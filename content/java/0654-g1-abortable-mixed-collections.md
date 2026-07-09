---
card: java
gi: 654
slug: g1-abortable-mixed-collections
title: G1 abortable mixed collections
---

## 1. What it is

**G1 abortable mixed collections**, added in **Java 12** (JEP 344), lets G1's "mixed" garbage collection pauses **stop early** if they're about to exceed the pause-time goal you set with `-XX:MaxGCPauseMillis`. G1 works by collecting the heap in regions, and a "mixed collection" pause processes both young-generation regions and a batch of old-generation regions in the same pause. Before Java 12, once G1 committed to collecting a set of old regions in a mixed pause, it collected *all* of them, even if that meant blowing well past the target pause time — the collection wasn't checkable or interruptible mid-flight. From Java 12 onward, G1 checks its progress periodically during a mixed collection and can abort — stopping after the current region — if it's already run long enough, deferring the remaining old regions to a future pause.

## 2. Why & when

`-XX:MaxGCPauseMillis` is meant to be a *soft goal* the collector tries to honor, but before this change, mixed collections could silently and significantly overshoot it — an application configured for, say, 200 ms pauses might occasionally see 500+ ms pauses simply because the collector had already picked a batch of old regions and had no way to bail out partway through. This is exactly the kind of latency spike that erodes trust in a pause-time goal and makes G1 harder to tune predictably. Abortable mixed collections make the goal genuinely closer to real for the mixed-collection phase (young-only pauses were already more predictable). You benefit automatically just by running on Java 12+ with G1 (the default collector) — there's no new flag to opt in, it's a scheduling improvement to how G1 respects the pause-time goal you already configure.

## 3. Core concept

```bash
# Set a pause-time goal — G1 tries to keep pauses under this target
java -XX:MaxGCPauseMillis=200 -Xlog:gc MyApp

# Before Java 12: a mixed collection pause might commit to N old regions
# and finish ALL of them even if the pause blows past 200ms.
#
# Java 12+: G1 checks elapsed time between old regions during the pause
# and can stop early ("abort"), leaving the rest for a later mixed collection.
```

No API or flag changes — this is purely internal scheduling logic inside G1's mixed collection algorithm, making the existing `MaxGCPauseMillis` goal more reliably honored.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 12 a mixed collection processes all committed old regions even past the pause goal; from Java 12 it can abort early and defer remaining regions">
  <rect x="10" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="42" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">Before Java 12</text>
  <rect x="25" y="55" width="40" height="24" fill="#79c0ff"/><text x="45" y="72" fill="#0d1117" font-size="9" text-anchor="middle">Y</text>
  <rect x="70" y="55" width="40" height="24" fill="#6db33f"/><text x="90" y="72" fill="#0d1117" font-size="9" text-anchor="middle">O1</text>
  <rect x="115" y="55" width="40" height="24" fill="#6db33f"/><text x="135" y="72" fill="#0d1117" font-size="9" text-anchor="middle">O2</text>
  <rect x="160" y="55" width="40" height="24" fill="#f85149"/><text x="180" y="72" fill="#0d1117" font-size="9" text-anchor="middle">O3</text>
  <text x="20" y="105" fill="#f85149" font-size="10" font-family="sans-serif">Goal: 200ms — pause runs</text>
  <text x="20" y="120" fill="#f85149" font-size="10" font-family="sans-serif">to 480ms finishing ALL</text>
  <text x="20" y="135" fill="#f85149" font-size="10" font-family="sans-serif">committed old regions.</text>
  <text x="20" y="155" fill="#8b949e" font-size="9" font-family="sans-serif">No way to bail out mid-pause.</text>

  <rect x="320" y="20" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 12+</text>
  <rect x="335" y="55" width="40" height="24" fill="#79c0ff"/><text x="355" y="72" fill="#0d1117" font-size="9" text-anchor="middle">Y</text>
  <rect x="380" y="55" width="40" height="24" fill="#6db33f"/><text x="400" y="72" fill="#0d1117" font-size="9" text-anchor="middle">O1</text>
  <rect x="425" y="55" width="40" height="24" fill="#6db33f"/><text x="445" y="72" fill="#0d1117" font-size="9" text-anchor="middle">O2</text>
  <rect x="470" y="55" width="40" height="24" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="490" y="72" fill="#8b949e" font-size="9" text-anchor="middle">O3</text>
  <text x="335" y="105" fill="#6db33f" font-size="10" font-family="sans-serif">Goal: 200ms — pause checks</text>
  <text x="335" y="120" fill="#6db33f" font-size="10" font-family="sans-serif">time after O2, aborts before</text>
  <text x="335" y="135" fill="#6db33f" font-size="10" font-family="sans-serif">O3, stays near 200ms.</text>
  <text x="335" y="155" fill="#8b949e" font-size="9" font-family="sans-serif">O3 deferred to next mixed pause.</text>
</svg>

Java 12's G1 checks its elapsed time between old regions and can stop the pause early, deferring leftover regions instead of always finishing the whole batch.

## 5. Runnable example

Scenario: an application that generates enough old-generation garbage to trigger G1 mixed collections — first running with a default pause goal, then tightening the goal to make mixed-collection behavior visible, then using GC logging to observe the abort behavior across multiple mixed-collection pauses.

### Level 1 — Basic

```java
// File: OldGenChurn.java
import java.util.ArrayList;
import java.util.List;

public class OldGenChurn {
    static List<byte[]> survivors = new ArrayList<>();

    public static void main(String[] args) {
        // Promote enough objects to old generation to eventually trigger mixed GCs.
        for (int i = 0; i < 2_000_000; i++) {
            byte[] chunk = new byte[256];
            survivors.add(chunk);
            if (survivors.size() > 100_000) {
                survivors.subList(0, 20_000).clear(); // free some, keep churn going
            }
        }
        System.out.println("Done. Survivor list size: " + survivors.size());
    }
}
```

**How to run:** `java -Xmx256m -Xlog:gc OldGenChurn.java`

Expected output includes program output plus interleaved GC log lines:
```
[0.812s][info][gc] GC(12) Pause Young (Normal) (G1 Evacuation Pause) 45M->20M(256M) 12.345ms
[1.203s][info][gc] GC(15) Pause Young (Mixed) (G1 Evacuation Pause) 60M->25M(256M) 18.901ms
...
Done. Survivor list size: 100000
```

### Level 2 — Intermediate

**How to run with a tight pause goal**, making G1 work harder to stay within budget:
```
java -Xmx256m -XX:MaxGCPauseMillis=50 -Xlog:gc OldGenChurn.java
```

Expected output shows more frequent, shorter mixed-collection pauses as G1 tries to respect the tighter 50 ms goal:
```
[0.734s][info][gc] GC(10) Pause Young (Mixed) (G1 Evacuation Pause) 58M->24M(256M) 22.145ms
[0.798s][info][gc] GC(11) Pause Young (Mixed) (G1 Evacuation Pause) 61M->26M(256M) 19.882ms
Done. Survivor list size: 100000
```

Tightening `MaxGCPauseMillis` doesn't change the program's output, but it changes how G1 paces mixed collections — with abortable mixed collections (Java 12+), G1 is far less likely to produce a rogue pause that badly overshoots the 50 ms target, instead spreading old-region reclamation across more, shorter pauses.

### Level 3 — Advanced

```java
// File: OldGenChurnTimed.java
import java.util.ArrayList;
import java.util.List;

public class OldGenChurnTimed {
    static List<byte[]> survivors = new ArrayList<>();

    public static void main(String[] args) {
        long worstGapMs = 0;
        long last = System.nanoTime();

        for (int i = 0; i < 5_000_000; i++) {
            byte[] chunk = new byte[256];
            survivors.add(chunk);
            if (survivors.size() > 150_000) {
                survivors.subList(0, 30_000).clear();
            }
            if (i % 100_000 == 0) {
                long now = System.nanoTime();
                long gapMs = (now - last) / 1_000_000;
                if (gapMs > worstGapMs) worstGapMs = gapMs;
                last = now;
            }
        }
        System.out.println("Worst observed gap between checkpoints: " + worstGapMs + " ms");
        System.out.println("Final survivor list size: " + survivors.size());
    }
}
```

**How to run:** `java -Xmx256m -XX:MaxGCPauseMillis=50 -Xlog:gc:file=gc.log OldGenChurnTimed.java`

Expected output:
```
Worst observed gap between checkpoints: 41 ms
Final survivor list size: 150000
```
with `gc.log` containing many `Pause Young (Mixed)` entries, each staying reasonably close to the 50 ms target rather than occasionally spiking far past it.

Level 3 measures the worst gap between periodic checkpoints in application code — a crude proxy for "how bad did the worst pause feel from the application's perspective" — and redirects GC logs to a file (`-Xlog:gc:file=gc.log`) for later inspection, showing how abortable mixed collections keep even the worst-case pause closer to the configured goal instead of an unbounded overshoot.

## 6. Walkthrough

1. The JVM starts with `-Xmx256m` (small heap, to trigger GC activity quickly for the demo) and `-XX:MaxGCPauseMillis=50` (an aggressive pause-time goal).
2. `main` enters the loop and begins allocating `byte[256]` chunks, adding each to the static `survivors` list — this keeps objects reachable long enough that many get promoted from young generation into the old generation as G1's young collections run in the background.
3. Once old-generation occupancy crosses G1's internal threshold, G1 schedules a **mixed collection**: a pause that reclaims both young regions and a chosen batch of old regions together, since young-only collections alone can't reclaim old garbage.
4. During that mixed-collection pause, G1 processes old regions one at a time, and after each one, checks the elapsed pause time against the 50 ms goal (this is the Java 12 behavior from JEP 344). If it's already close to or over budget, it aborts — stopping before processing the remaining regions it had tentatively selected — rather than plowing through all of them regardless of cost.
5. Any old regions left unprocessed because of the abort are simply left for a **future** mixed-collection pause to pick up; nothing is lost, the reclamation work is just spread across more, smaller pauses.
6. Back in application code, every 100,000 iterations the loop records a timestamp and computes `gapMs`, the wall-clock time since the last checkpoint — this interval includes both normal allocation work and any GC pause that happened to occur during that stretch, so a bad GC pause shows up as an unusually large gap.
7. `worstGapMs` tracks the largest such gap seen across the whole run. After all 5,000,000 iterations complete, `main` prints that worst gap and the final `survivors` size — a small worst-gap value (well under, say, 100 ms even though the machine did substantial GC work) is the practical, application-visible evidence that abortable mixed collections kept pauses from spiraling.

```
allocate ──► old regions fill ──► mixed collection scheduled
    process O1 ──check time (ok)──► process O2 ──check time (near goal)──► ABORT
    remaining old regions (O3, O4...) deferred to NEXT mixed collection
```

## 7. Gotchas & takeaways

> `MaxGCPauseMillis` is, and remains, a **soft goal**, not a hard guarantee — abortable mixed collections make G1 much better at respecting it during the mixed-collection phase specifically, but extremely tight goals on heavily allocating workloads can still occasionally be missed. Don't treat the flag as a hard real-time bound; treat it as a strong hint G1 now honors more faithfully.

- This is an internal G1 scheduling improvement with no new public API or flag — it applies automatically once you're on Java 12+ using G1 (the default collector).
- It specifically improves *mixed* collections (young + a batch of old regions); plain young-only collections were already reasonably predictable before this change.
- Aborted (deferred) old regions aren't wasted work — they're simply picked up in a subsequent mixed-collection cycle.
- Tighter `MaxGCPauseMillis` values generally mean more, smaller mixed-collection pauses rather than fewer, larger ones — plan capacity accordingly.
- Always verify pause behavior with `-Xlog:gc` (or a GC visualization tool) rather than assuming a flag's effect — GC tuning is workload-specific.
