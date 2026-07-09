---
card: java
gi: 776
slug: stream-gatherers-2nd-preview
title: Stream gatherers (2nd preview)
---

## 1. What it is

**Java 23** (JEP 473) is the **second preview** of [stream gatherers](0762-stream-gatherers-preview.md), carried forward from Java 22 **with no functional changes** to the `Gatherer` interface, `Stream.gather(...)`, or the built-in `Gatherers` factory methods (`windowFixed`, `windowSliding`, `fold`, `scan`, `mapConcurrent`). A second, unchanged preview round exists so the JDK can gather more real-world usage feedback before committing the API's shape permanently — the same reason many JEPs spend two or more rounds in preview even when a round introduces no new capability. It still requires `--enable-preview` to compile and run.

## 2. Why & when

Finalizing a general-purpose API like `Gatherer` — one meant to be implemented by arbitrary third-party code, not just called — carries more risk than finalizing a single new method: once it's standard, every custom `Gatherer` implementation written against it becomes something the JDK has to support compatibly forever. The JDK team's practice for API-shaped previews is to hold the design steady for a second round specifically to see whether real usage (library authors writing custom gatherers for pipelines the first round's examples didn't anticipate) turns up an awkward edge in the `Integrator`/state/finisher contract before it's locked in. If you used `Gatherer` under Java 22's preview, your code keeps working unchanged under Java 23's preview — the only difference is which `--source`/`--release` value enables it, and the API is one preview round closer to becoming a stable, permanent part of the `java.util.stream` package.

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> numbers = List.of(1, 1, 2, 2, 2, 3, 1, 1);

// Gatherers.fold: a running accumulation, like reduce but as an intermediate op
List<Integer> runningTotal = numbers.stream()
    .gather(Gatherers.fold(() -> 0, (total, n) -> total + n))
    .toList();
// [1, 2, 4, 6, 8, 11, 12, 13]
```

`Gatherers.fold` — unchanged from the first preview — turns a running accumulation into an intermediate operation that emits the accumulator's value after every element, rather than only its final value.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Gatherer API carries forward unchanged from the first preview to the second, gathering more usage feedback before eventual standardization">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="110" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 22: 1st preview</text>

  <line x1="200" y1="45" x2="250" y2="45" stroke="#6db33f" stroke-width="2" marker-end="url(#a776)"/>
  <text x="225" y="35" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">no API change</text>
  <defs><marker id="a776" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker></defs>

  <rect x="260" y="20" width="180" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="350" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Java 23: 2nd preview</text>

  <line x1="440" y1="45" x2="490" y2="45" stroke="#8b949e" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#a776)"/>

  <rect x="500" y="20" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">eventual standard</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A second unchanged preview collects feedback before the API is locked in permanently</text>
</svg>

*The same `Gatherer` contract from Java 22, given a second release cycle for feedback before standardization.*

## 5. Runnable example

Scenario: deduplicating consecutive log-severity spikes in a stream of readings, growing from a built-in `Gatherers.fold` running total into a custom stateful gatherer — the same kind of pipeline the first preview supports, unchanged under the second.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class GathererFoldBasic {
    public static void main(String[] args) {
        List<Integer> visitors = List.of(3, 5, 2, 8, 1, 4);

        List<Integer> runningTotal = visitors.stream()
            .gather(Gatherers.fold(() -> 0, (total, n) -> total + n))
            .toList();

        System.out.println(runningTotal);
    }
}
```

**How to run:** `java --enable-preview --source 23 GathererFoldBasic.java` (JDK 23+).

`Gatherers.fold` emits the running total **after each element**, unlike `Stream.reduce`, which only ever produces the final accumulated value — the API and behavior are identical to what the first preview shipped in Java 22.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class GathererDedupe {
    public static void main(String[] args) {
        List<String> statuses = List.of("ok", "ok", "warn", "warn", "warn", "ok", "error", "error");

        List<String> collapsed = statuses.stream()
            .gather(Gatherers.<String, String>fold(
                () -> null,
                (last, current) -> current))
            .distinct()
            .toList();

        System.out.println(collapsed);
    }
}
```

**How to run:** `java --enable-preview --source 23 GathererDedupe.java`.

The real-world concern added: composing a gatherer with an ordinary intermediate operation (`.distinct()`) afterward — `fold` here just tracks "the current value," but the point is showing that a gathered stream keeps behaving like any other stream pipeline: further intermediate operations chain normally, no special-casing required.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class GathererCollapseRuns {
    // Custom gatherer: collapses consecutive equal elements into one,
    // paired with a count — e.g. "ok, ok, warn, warn, warn" -> [(ok,2), (warn,3)].
    static Gatherer<String, Object, Map.Entry<String, Integer>> collapseRuns() {
        return Gatherer.ofSequential(
            () -> new Object[]{null, 0}, // [currentValue, currentCount]
            Gatherer.Integrator.ofGreedy((state, element, downstream) -> {
                Object[] s = (Object[]) state;
                if (element.equals(s[0])) {
                    s[1] = (int) s[1] + 1;
                    return true;
                }
                boolean keepGoing = true;
                if (s[0] != null) {
                    keepGoing = downstream.push(Map.entry((String) s[0], (int) s[1]));
                }
                s[0] = element;
                s[1] = 1;
                return keepGoing;
            }),
            (state, downstream) -> {
                Object[] s = (Object[]) state;
                if (s[0] != null) {
                    downstream.push(Map.entry((String) s[0], (int) s[1]));
                }
            }
        );
    }

    public static void main(String[] args) {
        List<String> statuses = List.of("ok", "ok", "warn", "warn", "warn", "ok", "error", "error");

        List<Map.Entry<String, Integer>> runs = statuses.stream()
            .gather(collapseRuns())
            .toList();

        System.out.println(runs);
    }
}
```

**How to run:** `java --enable-preview --source 23 GathererCollapseRuns.java`.

This adds the production-flavored hard case: a **custom gatherer with a finisher** — `collapseRuns()` tracks both a current run's value and its count in a two-slot state array, pushing a completed `(value, count)` pair only when a *different* value arrives, and using the **finisher** callback (the third argument to `Gatherer.ofSequential`) to flush the final in-progress run once the input stream ends, since that last run would otherwise never get pushed by the integrator alone.

## 6. Walkthrough

Tracing `GathererCollapseRuns.main`:

1. `main` builds `statuses`, a list of eight strings with runs of consecutive repeats (`"ok","ok"`, then `"warn","warn","warn"`, then `"ok"`, then `"error","error"`), and applies `.gather(collapseRuns())`.
2. The integrator processes elements one at a time, starting from state `[null, 0]`. For `"ok"` (first element), `s[0]` is `null` (no current run yet), so the "different value" branch runs but skips pushing (since `s[0] == null`), then sets `s[0] = "ok"`, `s[1] = 1`.
3. The second `"ok"` matches the current run's value, so `s[1]` increments to `2` — no push yet, the run is just getting longer.
4. `"warn"` differs from the current run (`"ok"`), so the integrator pushes the completed run `("ok", 2)` downstream, then starts a new run: `s[0] = "warn"`, `s[1] = 1`.
5. The next two `"warn"`s each match, incrementing the count to `3`.
6. `"ok"` differs again, pushing `("warn", 3)` and starting a new run `s[0] = "ok"`, `s[1] = 1`.
7. `"error"` differs, pushing `("ok", 1)` and starting `s[0] = "error"`, `s[1] = 1`.
8. The final `"error"` matches, incrementing to `s[1] = 2` — but no more elements follow, so this run is never pushed by the integrator itself.
9. Once the source stream is exhausted, the **finisher** runs: it sees `s[0] = "error"` is non-null, so it pushes the trailing run `("error", 2)` — without this finisher call, the last run would be silently lost.
10. `.toList()` collects every pushed entry in order.

Expected output:
```
[ok=2, warn=3, ok=1, error=2]
```

## 7. Gotchas & takeaways

> **Gotcha:** a stateful gatherer's **finisher** is easy to forget, and its absence fails silently, not loudly — without it, `collapseRuns()` would simply drop the last run from the output with no error, since the integrator only pushes a run when a *different* element arrives to trigger it. Any gatherer that accumulates state across elements needs to ask "what happens to whatever's left in my state when the input ends?" and handle it in the finisher.

- Second preview in Java 23 (JEP 473) — **no API changes** from Java 22's [first preview](0762-stream-gatherers-preview.md); still requires `--enable-preview`.
- `Gatherer.ofSequential` takes three pieces: an initializer (starting state), an integrator (per-element logic), and optionally a finisher (flushes any trailing state once input ends).
- Gathered streams compose normally with further intermediate operations (`.distinct()`, `.map()`, and so on) — `.gather(...)` is a first-class citizen of the pipeline, not a special terminal step.
- A second, functionally identical preview round is the JDK's way of gathering more real-world feedback before an API-shaped feature is locked in permanently.
- Custom gatherers with state should almost always implement a finisher unless it's certain no state can be left unpushed when the stream ends.
