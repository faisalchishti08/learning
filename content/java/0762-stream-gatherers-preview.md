---
card: java
gi: 762
slug: stream-gatherers-preview
title: Stream gatherers (preview)
---

## 1. What it is

**Java 22** (JEP 461) previews `Stream.gather(Gatherer)`, a new intermediate stream operation that lets you write **custom** intermediate operations — the same category as `map`, `filter`, and `distinct` — without needing the JDK to add a built-in method for every possible transformation. A `Gatherer` can do things the existing fixed set of intermediate operations cannot express cleanly: producing a different number of output elements than input elements based on running state (sliding windows, deduplication with a custom rule), looking at multiple elements together, or short-circuiting based on accumulated context. Being a preview feature, it requires `--enable-preview` to compile and run.

## 2. Why & when

The `Stream` API's intermediate operations (`map`, `filter`, `sorted`, `distinct`, `limit`, and others) cover an enormous range of common transformations, but they're a **fixed, closed set** — if you need something not on that list (grouping consecutive elements into fixed-size windows, computing a running average, deduplicating based on a custom equivalence rule not expressible via `distinct()`'s `equals()`-based semantics), you're stuck either dropping out of the stream pipeline into imperative code, or collecting to an intermediate `List` and post-processing it manually, both of which break the fluent, lazy, potentially-parallel nature of a stream pipeline. `Gatherer` opens that closed set: it's an interface with a small, well-defined contract (an initializer for internal state, an integrator function processing one element at a time and optionally emitting zero or more output elements, and a finisher for any trailing output), and once implemented, a `Gatherer` composes into `.gather(...)` exactly like any built-in intermediate operation — including working correctly with sequential and parallel streams. This matters whenever a data-processing pipeline needs a transformation genuinely outside the built-in vocabulary, without abandoning the stream style entirely.

## 3. Core concept

```java
import java.util.stream.*;

List<Integer> numbers = List.of(1, 2, 3, 4, 5);

// Gatherers.windowFixed is a built-in gatherer: groups elements into fixed-size lists
List<List<Integer>> windows = numbers.stream()
    .gather(Gatherers.windowFixed(2))
    .toList();
// [[1, 2], [3, 4], [5]]
```

`Gatherers.windowFixed(2)` is a JDK-provided `Gatherer` demonstrating the pattern; custom gatherers implement the same `Gatherer` interface to express transformations the JDK doesn't ship a built-in for.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Gatherer sits in a stream pipeline like map or filter, but can maintain running state across elements and emit a different number of outputs than inputs">
  <rect x="20" y="20" width="120" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="80" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">.filter(...)</text>

  <line x1="140" y1="40" x2="190" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#arrow762)"/>
  <defs><marker id="arrow762" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>

  <rect x="200" y="15" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">.gather(myGatherer)</text>
  <text x="290" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">custom stateful logic</text>

  <line x1="380" y1="40" x2="430" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#arrow762)"/>

  <rect x="440" y="20" width="120" height="40" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="500" y="45" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">.toList()</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A gatherer is a first-class intermediate operation you define yourself</text>
</svg>

*Custom stateful transformations slot into a stream pipeline exactly where `map`/`filter` would go.*

## 5. Runnable example

Scenario: computing a running average over a stream of sensor readings, growing from a built-in windowing gatherer into a fully custom gatherer with its own accumulated state.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class GathererBuiltin {
    public static void main(String[] args) {
        List<Double> readings = List.of(10.0, 12.0, 11.0, 15.0, 13.0, 14.0);

        List<List<Double>> pairs = readings.stream()
            .gather(Gatherers.windowFixed(2))
            .toList();

        System.out.println(pairs);
    }
}
```

**How to run:** `java --enable-preview --source 22 GathererBuiltin.java` (JDK 22+).

This uses the JDK-provided `Gatherers.windowFixed(2)` to group readings into fixed-size pairs — demonstrating the `.gather(...)` pipeline shape before writing a custom gatherer.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class GathererSlidingAverage {
    public static void main(String[] args) {
        List<Double> readings = List.of(10.0, 12.0, 11.0, 15.0, 13.0, 14.0);

        List<Double> movingAverages = readings.stream()
            .gather(Gatherers.windowSliding(3))
            .map(window -> window.stream().mapToDouble(Double::doubleValue).average().orElseThrow())
            .toList();

        System.out.println(movingAverages);
    }
}
```

**How to run:** `java --enable-preview --source 22 GathererSlidingAverage.java`.

The real-world concern added: `Gatherers.windowSliding(3)` produces **overlapping** windows of 3 consecutive readings (unlike `windowFixed`'s non-overlapping groups), and each window is immediately reduced to its average via `map` — a realistic "3-point moving average" computation built entirely out of composed stream operations, no manual index-based loop needed.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

public class GathererCustom {
    // A custom gatherer: emits a reading only if it differs from the
    // previous emitted reading by more than a threshold — a "significant
    // change" filter that stateless map/filter cannot express, since it
    // needs to remember the last emitted value across elements.
    static Gatherer<Double, double[], Double> significantChange(double threshold) {
        return Gatherer.ofSequential(
            () -> new double[]{Double.NaN}, // state: last emitted value (NaN = none yet)
            Gatherer.Integrator.ofGreedy((state, element, downstream) -> {
                if (Double.isNaN(state[0]) || Math.abs(element - state[0]) > threshold) {
                    state[0] = element;
                    return downstream.push(element);
                }
                return true; // skip this element, keep processing
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

**How to run:** `java --enable-preview --source 22 GathererCustom.java`.

This adds the production-flavored hard case: a **fully custom `Gatherer`** built from scratch with `Gatherer.ofSequential`, carrying its own running state (`double[] state`, holding the last emitted value) across the integrator's calls — expressing "emit this reading only if it's a significant jump from the last one I emitted" — a transformation that depends on history across elements, something no combination of stateless built-in operations like `map`/`filter` could express directly.

## 6. Walkthrough

Tracing `GathererCustom.main`:

1. `main` builds `readings`, a list of eight sensor values with a few small fluctuations and a few larger jumps, then applies `.gather(significantChange(2.0))`.
2. `significantChange(2.0)` returns a `Gatherer` whose state is a one-element `double[]` initialized to `{NaN}` (meaning "nothing emitted yet") and whose integrator runs once per input element.
3. For the first element, `10.0`: `state[0]` is `NaN`, so the `Double.isNaN(state[0])` branch is true — this element is always emitted as the first one. `state[0]` becomes `10.0`, and `downstream.push(10.0)` sends it to the result.
4. For `10.2`: `Math.abs(10.2 - 10.0) = 0.2`, not greater than the `2.0` threshold, so this element is skipped (the integrator returns `true` without pushing, and `state[0]` stays `10.0`).
5. For `10.1`: `Math.abs(10.1 - 10.0) = 0.1`, also skipped, state unchanged.
6. For `15.0`: `Math.abs(15.0 - 10.0) = 5.0`, greater than `2.0` — this is a significant change. It's pushed, and `state[0]` updates to `15.0`.
7. For `15.3`: `Math.abs(15.3 - 15.0) = 0.3`, skipped.
8. For `9.0`: `Math.abs(9.0 - 15.0) = 6.0`, significant — pushed, `state[0]` becomes `9.0`.
9. For `9.1`: `Math.abs(9.1 - 9.0) = 0.1`, skipped.
10. For `20.0`: `Math.abs(20.0 - 9.0) = 11.0`, significant — pushed, `state[0]` becomes `20.0`.

The final result collects every pushed element, in order: `10.0, 15.0, 9.0, 20.0`.

Expected output:
```
significant changes: [10.0, 15.0, 9.0, 20.0]
```

## 7. Gotchas & takeaways

> **Gotcha:** `Gatherer.ofSequential` deliberately restricts a stateful gatherer to sequential processing even if the surrounding stream is parallel — running state that depends on element order (like "the last emitted value") cannot be safely shared across parallel threads without extra synchronization the simple API doesn't provide. If you need a gatherer to work correctly with a parallel stream, you need the more advanced combiner-aware construction, not the sequential-only convenience factory.

- Preview feature in Java 22 — requires `--enable-preview` at compile and run time.
- `Stream.gather(Gatherer)` is a new general-purpose intermediate operation, composing with `map`/`filter`/`sorted` exactly like any built-in stream operation.
- The JDK ships several built-in gatherers (`Gatherers.windowFixed`, `Gatherers.windowSliding`, `Gatherers.fold`, and others) covering common cases before you need to write your own.
- Write a custom `Gatherer` when a transformation genuinely needs running state across elements, or needs to emit a different number of outputs than inputs, which stateless `map`/`filter` cannot express.
- `Gatherer.ofSequential` is the simpler entry point for stateful gatherers that don't need to support parallel execution; a full parallel-safe gatherer requires additional combiner logic.
