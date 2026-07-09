---
card: java
gi: 783
slug: stream-gatherers-standardized
title: Stream gatherers — standardized
---

## 1. What it is

**Java 24** (JEP 485) makes `Stream.gather(Gatherer)` a **permanent, standard part** of the `java.util.stream` package — no `--enable-preview` flag required — after two preview rounds ([Java 22](0762-stream-gatherers-preview.md), [Java 23](0776-stream-gatherers-2nd-preview.md)). `Gatherer`, `Gatherer.Integrator`, and the built-in `Gatherers` factory methods (`windowFixed`, `windowSliding`, `fold`, `scan`, `mapConcurrent`) are all stable, production-ready API: writing custom intermediate stream operations — the same category as `map` and `filter` — is now something any code can rely on without a preview gate.

## 2. Why & when

Two preview rounds validated the `Gatherer` contract from both directions: the JDK's own built-in gatherers exercised the API's expressiveness for common cases, while real usage feedback (including the second preview's stateful-transform refinements that later shaped the [Class-File API's own stateful transforms](0779-class-file-api-2nd-preview.md)) confirmed the `Integrator`/state/finisher shape held up for less common, more demanding custom gatherers. Standardization means any codebase can now depend on `Stream.gather(...)` the same way it depends on `map` or `collect` — in a library published to Maven Central, in a framework's internal pipeline code, in application code processing data with genuinely custom windowing or stateful logic — without the caveat that the API might still change before the next release, and without needing `--enable-preview` to even compile.

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> readings = List.of(10, 12, 11, 15, 13, 14);

// No --enable-preview needed anymore — this is standard Java 24 API.
List<Integer> movingSums = readings.stream()
    .gather(Gatherers.windowSliding(3))
    .map(window -> window.stream().mapToInt(Integer::intValue).sum())
    .toList();
System.out.println(movingSums); // [33, 38, 39, 42]
```

The same `Gatherers.windowSliding` from the preview rounds, now callable with no flags at all.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream gatherers standardize after two preview rounds, becoming a permanent part of java.util.stream alongside map, filter, and collect">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 22 preview -&gt; Java 23 2nd preview -&gt; Java 24 standard</text>

  <rect x="60" y="90" width="220" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="170" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">.map / .filter / .sorted</text>
  <text x="170" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">built-in intermediate ops</text>

  <rect x="360" y="90" width="220" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="112" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">.gather(myGatherer)</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">standard as of Java 24</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Custom intermediate operations are now first-class, no preview flag required</text>
</svg>

*Two release cycles of preview converge on a permanent extension point for the `Stream` API.*

## 5. Runnable example

Scenario: detecting significant jumps in a stream of sensor readings, growing from a built-in windowing gatherer into a fully custom, stateful gatherer with a finisher — all running as standard Java 24 code with no preview flags.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class GathererStandardBasic {
    public static void main(String[] args) {
        List<Double> readings = List.of(10.0, 12.0, 11.0, 15.0, 13.0, 14.0);

        List<List<Double>> windows = readings.stream()
            .gather(Gatherers.windowFixed(2))
            .toList();

        System.out.println(windows);
    }
}
```

**How to run:** `java GathererStandardBasic.java` (JDK 24+, no `--enable-preview` needed).

`Gatherers.windowFixed(2)` groups the stream into non-overlapping pairs — the same behavior the preview rounds established, now compiled and run with zero special flags.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class GathererStandardScan {
    public static void main(String[] args) {
        List<Double> readings = List.of(10.0, 12.0, 11.0, 15.0, 13.0, 14.0);

        List<Double> runningMax = readings.stream()
            .gather(Gatherers.scan(() -> Double.NEGATIVE_INFINITY, Math::max))
            .toList();

        System.out.println("running max: " + runningMax);
    }
}
```

**How to run:** `java GathererStandardScan.java`.

The real-world concern added: `Gatherers.scan` (a running fold that emits the accumulator's value after every element, similar to `fold` but always starting from an explicit seed rather than the first element) — a standard, always-available way to compute a running maximum, no custom `Gatherer` implementation needed for this common case.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class GathererStandardCustom {
    static Gatherer<Double, double[], Double> significantChange(double threshold) {
        return Gatherer.ofSequential(
            () -> new double[]{Double.NaN},
            Gatherer.Integrator.ofGreedy((state, element, downstream) -> {
                if (Double.isNaN(state[0]) || Math.abs(element - state[0]) > threshold) {
                    state[0] = element;
                    return downstream.push(element);
                }
                return true;
            })
        );
    }

    public static void main(String[] args) {
        List<Double> readings = List.of(10.0, 10.2, 10.1, 15.0, 15.3, 9.0, 9.1, 20.0);

        List<Double> significant = readings.stream()
            .gather(significantChange(2.0))
            .toList();

        System.out.println("significant changes: " + significant);
    }
}
```

**How to run:** `java GathererStandardCustom.java`.

This adds the production-flavored hard case: a fully **custom** `Gatherer`, identical in shape and behavior to the one demonstrated during the preview rounds — proof that code written against the preview `Gatherer` API needs no source changes at all to run as standard Java 24, only the removal of `--enable-preview` from the run command.

## 6. Walkthrough

Tracing `GathererStandardCustom.main`:

1. `main` builds `readings`, a list of eight sensor values with a few small fluctuations and a few larger jumps, then applies `.gather(significantChange(2.0))`.
2. `significantChange(2.0)` returns a `Gatherer` with one-element `double[]` state, initialized to `{NaN}`, meaning "nothing emitted yet."
3. The first element, `10.0`, is always emitted (state is `NaN`), updating state to `10.0`.
4. `10.2` and `10.1` are each within `2.0` of the current state (`10.0`), so both are skipped.
5. `15.0` differs from `10.0` by `5.0`, exceeding the threshold — it's pushed, and state updates to `15.0`.
6. `15.3` is close to `15.0`, skipped.
7. `9.0` differs from `15.0` by `6.0`, pushed, state becomes `9.0`.
8. `9.1` is close to `9.0`, skipped.
9. `20.0` differs from `9.0` by `11.0`, pushed, state becomes `20.0`.

Expected output:
```
significant changes: [10.0, 15.0, 9.0, 20.0]
```

## 7. Gotchas & takeaways

> **Gotcha:** code migrating from a preview JDK to Java 24 needs to drop `--enable-preview` (and any matching `--source`/`--release` preview markers) from **both** compile and run commands — leaving a stale `--enable-preview` flag on a standard feature is harmless but pointless, while forgetting to remove a preview-specific `--release` pin that's now below 24 could otherwise prevent the code from picking up the standardized API at all.

- Standardized in Java 24 (JEP 485) — no `--enable-preview` flag needed; production-ready.
- The API is unchanged from the [second preview](0776-stream-gatherers-2nd-preview.md): `Gatherer.ofSequential`, an initializer/integrator/finisher, and the built-in `Gatherers` factory methods all carry forward exactly as they were.
- Custom gatherers remain the right tool when a transformation needs running state across elements or needs to emit a different number of outputs than inputs — something stateless `map`/`filter` cannot express.
- Preview-era code using `Stream.gather(...)` needs no source changes to run as standard Java 24; only the preview compiler/runtime flags need removing.
- This standardization, alongside [structured concurrency's continuing evolution](0777-structured-concurrency-3rd-preview.md), reflects the JDK's broader push to give stream and concurrency pipelines more expressive, first-class extension points.
