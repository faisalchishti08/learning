---
card: java
gi: 937
slug: gc-tuning-flags-ergonomics
title: GC tuning flags & ergonomics
---

## 1. What it is

GC ergonomics is the JVM's built-in ability to automatically pick sensible defaults for collector selection, heap sizing, and generation ratios based on the machine it's running on (available memory, detected core count) and the running application's observed behavior — without any explicit flags at all. GC tuning flags are the escape hatch for when those automatic choices aren't right for a specific workload: flags like `-XX:MaxGCPauseMillis` (a soft pause-time target, primarily meaningful to [G1](0932-g1-gc.md)), `-XX:NewRatio` and `-XX:SurvivorRatio` (controlling how heap space is divided between young and old generations, and between Eden and Survivor spaces within the young generation), `-XX:InitiatingHeapOccupancyPercent` (how full the old generation must get before a concurrent marking cycle begins), and `-XX:ParallelGCThreads` / `-XX:ConcGCThreads` (worker thread counts for parallel and concurrent phases respectively). Together, ergonomics-plus-overrides let the JVM make good default decisions out of the box, while still giving operators a way to correct for a workload's specific, atypical allocation and retention pattern.

## 2. Why & when

Ergonomics exists because most applications don't need hand-tuning — modern collectors (especially [G1](0932-g1-gc.md), the current default) already adapt generation sizing and pause behavior reasonably well to observed allocation rates and promotion patterns automatically, and reaching for tuning flags before actually profiling a real pause problem is a common and wasteful anti-pattern. Explicit tuning becomes worthwhile once you have concrete evidence from GC logs (`-Xlog:gc`) that a specific default is wrong for your workload: for example, if mixed collections in G1 are triggering too late and causing a full GC fallback, `-XX:InitiatingHeapOccupancyPercent` lowered from its default (45%) starts concurrent marking earlier, giving G1 more time to reclaim garbage before old-generation pressure becomes critical; if pauses are consistently and comfortably under the target with room to spare, raising `-XX:MaxGCPauseMillis` can let G1 batch more region evacuation per pause and improve throughput; and if young-generation collections are too frequent because Eden is undersized relative to the application's allocation rate, `-XX:NewRatio` (or explicitly sizing the young generation) can rebalance that. The unifying principle: tune based on what the GC log actually shows happening, not based on a plausible-sounding flag copied from an unrelated workload's blog post.

## 3. Core concept

```
Ergonomics (automatic, no flags needed):
  - Detects available memory  -> chooses default -Xmx (typically 1/4 of physical RAM)
  - Detects core count        -> chooses default GC worker thread counts
  - Observes allocation/promotion rate at runtime -> adapts generation sizing (G1 does this continuously)

Tuning flags (manual override, evidence-driven):
  -XX:MaxGCPauseMillis=N              soft pause-time target (mainly G1)
  -XX:NewRatio=N                      old-gen : young-gen size ratio
  -XX:SurvivorRatio=N                 Eden : (one) Survivor space size ratio
  -XX:InitiatingHeapOccupancyPercent=N  occupancy % that starts concurrent marking (G1)
  -XX:ParallelGCThreads=N             worker threads for STW parallel phases
  -XX:ConcGCThreads=N                 worker threads for concurrent phases

Workflow: observe (-Xlog:gc) -> identify specific problem -> apply ONE targeted flag -> re-observe
```

Tuning is an iterative, evidence-driven loop, not a one-shot flag dump — each change should be justified by something specific seen in the GC log, and re-verified afterward.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A feedback loop: observe GC log, identify a specific problem, apply one targeted tuning flag, re-observe to confirm improvement">
  <rect x="20" y="30" width="140" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="54" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Observe -Xlog:gc</text>

  <rect x="200" y="30" width="140" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="270" y="54" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Identify specific issue</text>

  <rect x="380" y="30" width="140" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="450" y="49" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Apply ONE targeted</text>
  <text x="450" y="62" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">tuning flag</text>

  <rect x="560" y="30" width="60" height="40" fill="none" stroke="#8b949e" stroke-dasharray="2"/>

  <line x1="160" y1="50" x2="200" y2="50" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="340" y1="50" x2="380" y2="50" stroke="#8b949e" marker-end="url(#a)"/>
  <path d="M 450 70 Q 450 130 90 130 Q 90 130 90 70" fill="none" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="270" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">re-observe: confirm improvement, or revert and try a different flag</text>
</svg>

*Effective GC tuning is a loop: observe, diagnose a specific cause, apply one flag, then re-verify — never a one-shot bundle of unverified flags.*

## 5. Runnable example

Scenario: tune a single, identifiable GC problem on one workload — starting with a baseline showing default ergonomics behavior, then diagnosing and fixing an observed issue (concurrent marking starting too late) with one targeted flag, then verifying the fix's actual effect with a controlled before/after comparison.

### Level 1 — Basic

```java
import java.util.*;

public class GcTuningBaseline {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 400_000; i++) {
            retained.add(new byte[300]);
        }
        System.out.println("retained: " + retained.size());
        System.out.println("check the log for when 'Concurrent Start' and 'Pause Full' events occur");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx150m -XX:+UseG1GC GcTuningBaseline.java` (JDK 17+).

Expected output shape (illustrative — under default ergonomics, concurrent marking may start late enough to risk a full GC fallback under this specific retention pattern):
```
[0.10s][info][gc] GC(5) Pause Young (Normal) (G1 Evacuation Pause) ... 20M->8M(150M) 1.8ms
...
[0.60s][info][gc] GC(30) Pause Young (Concurrent Start) (G1 Evacuation Pause) ... 130M->95M(150M) 5.1ms
[0.75s][info][gc] GC(33) Pause Full (G1 Compaction Pause) ... 148M->60M(150M) 210ms
retained: 400000
check the log for when 'Concurrent Start' and 'Pause Full' events occur
```

The default `InitiatingHeapOccupancyPercent` (45%) triggers concurrent marking reasonably late relative to this workload's fast, sustained retention rate — leaving G1 too little time to finish reclaiming garbage-rich regions before old-generation occupancy becomes critical, forcing an expensive full GC fallback.

### Level 2 — Intermediate

```java
import java.util.*;

public class GcTuningEarlierMarking {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        for (int i = 0; i < 400_000; i++) {
            retained.add(new byte[300]);
        }
        System.out.println("retained: " + retained.size());
        System.out.println("with earlier IHOP, concurrent marking should have time to complete before old gen is critical");
    }
}
```

**How to run:** `java -Xlog:gc -Xmx150m -XX:+UseG1GC -XX:InitiatingHeapOccupancyPercent=25 GcTuningEarlierMarking.java` (JDK 17+; identical code, only the tuning flag changes, lowering the occupancy threshold that starts concurrent marking).

Expected output shape:
```
[0.08s][info][gc] GC(4) Pause Young (Normal) (G1 Evacuation Pause) ... 18M->8M(150M) 1.7ms
...
[0.35s][info][gc] GC(20) Pause Young (Concurrent Start) (G1 Evacuation Pause) ... 78M->50M(150M) 3.9ms
[0.55s][info][gc] GC(28) Pause Young (Mixed) (G1 Evacuation Pause) ... 100M->55M(150M) 4.2ms
retained: 400000
with earlier IHOP, concurrent marking should have time to complete before old gen is critical
```

The real-world concern added: with the same identical retention workload, lowering `InitiatingHeapOccupancyPercent` starts concurrent marking earlier (at 25% old-gen occupancy instead of 45%), giving G1 enough lead time to identify and reclaim garbage-rich regions via ordinary mixed collections — the previously-observed "Pause Full" fallback no longer appears at all, confirming the targeted flag actually fixed the specific, previously-diagnosed problem.

### Level 3 — Advanced

```java
import java.util.*;

public class GcTuningVerifiedComparison {
    public static void main(String[] args) {
        List<byte[]> retained = new ArrayList<>();
        long start = System.nanoTime();
        for (int i = 0; i < 600_000; i++) {
            retained.add(new byte[300]);
            if (i % 5 == 0 && retained.size() > 10) {
                retained.remove(retained.size() / 3);
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("retained: " + retained.size() + ", elapsed: " + elapsedMs + "ms");
    }
}
```

**How to run:** run three configurations to isolate the effect of each individual flag: default, `-XX:InitiatingHeapOccupancyPercent=25` alone, and that flag combined with a tighter `-XX:MaxGCPauseMillis=50` — all with `java -Xlog:gc -Xmx200m -XX:+UseG1GC ...` and the respective additional flags (JDK 17+).

Expected output shape (illustrative):
```
(default):                          1 'Pause Full' event, elapsed: 780ms
(+IHOP=25):                          0 'Pause Full' events, elapsed: 640ms  -- fallback eliminated
(+IHOP=25 +MaxGCPauseMillis=50):     0 'Pause Full' events, more frequent smaller pauses, elapsed: 690ms
```

The production-flavored hard case: layering a second flag (`MaxGCPauseMillis=50`) on top of the already-fixed IHOP setting shows the next-order tradeoff — tightening the pause target further eliminates the fallback just as well, but trades a modest amount of total throughput for smaller individual pauses, which is exactly the kind of second, independent tuning decision that should only be made after confirming the first fix actually worked, and only if the workload's latency requirements justify it.

## 6. Walkthrough

Tracing the diagnosis-and-fix process across the three examples above, in the order a real tuning session would follow:

1. `GcTuningBaseline` runs first under default ergonomics — the GC log reveals a `Pause Full` event, which is the specific, concrete signal that something about this workload's allocation/retention pattern is outrunning G1's default assumptions; this is the "observe" step, and it must come before touching any flag.
2. The full GC's presence, combined with a "Concurrent Start" event that fired only shortly before it, narrows the diagnosis: concurrent marking did not have enough lead time to finish identifying and reclaiming garbage-rich old regions before old-generation occupancy became critical — this points specifically at `InitiatingHeapOccupancyPercent`, the flag controlling exactly when concurrent marking begins, rather than at, say, thread counts or pause-time targets.
3. `GcTuningEarlierMarking` applies exactly one change — lowering `InitiatingHeapOccupancyPercent` from its default 45% to 25% — keeping every other variable (heap size, workload, collector) identical, which is what makes the resulting log a valid before/after comparison rather than a confounded one.
4. Re-running with the new flag and re-observing the log confirms the fix: concurrent marking now starts earlier (at lower old-gen occupancy), giving it enough time to complete and feed properly-identified garbage-rich regions into ordinary "Mixed" collections — and critically, the previously-seen "Pause Full" event no longer appears anywhere in the log.
5. `GcTuningVerifiedComparison` then runs a controlled three-way comparison — default, single-flag fix, and single-flag fix plus a second, independent tuning knob — specifically to demonstrate that each additional flag's effect should be verified in isolation, on top of an already-confirmed baseline, rather than bundling multiple untested changes together and hoping the net effect is positive.
6. The final elapsed-time and full-GC-count numbers across all three runs give a complete, evidence-based picture: the first flag fixed a genuine problem (eliminating an expensive fallback), and the second flag made an additional, smaller, and separately justified latency/throughput tradeoff — exactly the disciplined, log-driven loop the "Core concept" section describes.

## 7. Gotchas & takeaways

> **Gotcha:** applying several tuning flags at once, without observing their effect individually, makes it impossible to tell which flag actually helped, which had no effect, and which made things worse — always change one flag at a time and re-run with `-Xlog:gc` to confirm the specific, expected effect before adding another.

- GC ergonomics automatically adapts heap sizing, generation ratios, and worker-thread counts to the running machine and observed workload — most applications never need explicit tuning flags at all.
- Reach for tuning flags only after GC logs show a specific, concrete problem (e.g., an unexpected full GC fallback, pauses consistently far under or over budget) — never as a speculative first step.
- `InitiatingHeapOccupancyPercent` controls when G1's concurrent marking begins; too high a threshold risks marking not finishing before old-generation pressure becomes critical, forcing an expensive full-GC fallback.
- `MaxGCPauseMillis` is a soft target G1 uses to decide how many regions to evacuate per pause — tightening it favors latency, loosening it favors throughput.
- Always tune one flag at a time and re-verify against the GC log — bundling untested flags together makes it impossible to attribute cause and effect.
- See [G1 GC](0932-g1-gc.md) for the collector most of these flags target directly, and [stop-the-world pauses](0936-stop-the-world-pauses.md) for what's actually being measured in the logs these tuning decisions are based on.
