---
card: java
gi: 474
slug: primitive-specializations-intfunction-tointfunction-intpredi
title: Primitive specializations (IntFunction, ToIntFunction, IntPredicate, etc.)
---

## 1. What it is

`java.util.function` includes dozens of **primitive-specialized** variants of `Function`, `Predicate`, `Consumer`, `Supplier`, and the operator interfaces — `IntFunction<R>`, `ToIntFunction<T>`, `IntPredicate`, `IntConsumer`, `IntSupplier`, `IntUnaryOperator`, `IntBinaryOperator`, and the same set again for `long` and `double`. Each one works with a primitive type (`int`, `long`, or `double`) directly at one or more positions in its signature, instead of the corresponding boxed wrapper type (`Integer`, `Long`, `Double`).

## 2. Why & when

`Function<Integer, Integer>` works, but every call **boxes** its `int` argument into an `Integer` object and **unboxes** the `Integer` result back into an `int` — extra object allocation and indirection on every single call. In a tight loop processing millions of numbers, that boxing overhead adds up to real, measurable cost, both in CPU time and in extra garbage for the collector to clean up. The primitive specializations exist purely to eliminate that overhead: `IntUnaryOperator.applyAsInt(int)` takes and returns raw `int` the whole way through, no boxing at any point.

You reach for a primitive specialization whenever you're working with primitives at meaningful volume — `IntStream`/`LongStream`/`DoubleStream` (the primitive stream types) are built entirely around these interfaces, so `IntStream.map` expects an `IntUnaryOperator`, not a `Function<Integer, Integer>`. For everyday, low-volume code, the boxing overhead of the generic interfaces is irrelevant and not worth thinking about — reach for the primitive-specialized version specifically when profiling or stream-heavy numeric code shows it matters, or when an API (like the primitive streams) requires it directly.

## 3. Core concept

```java
import java.util.function.*;

IntUnaryOperator square = n -> n * n;        // int -> int, no boxing
int result = square.applyAsInt(5);            // 25

ToIntFunction<String> length = String::length; // T -> int (result is primitive, input is not)
int len = length.applyAsInt("hello");          // 5

IntFunction<String> repeat = n -> "x".repeat(n); // int -> R (input is primitive, result is not)
String repeated = repeat.apply(3);               // "xxx"

IntPredicate isEven = n -> n % 2 == 0;         // int -> boolean, no boxing
boolean even = isEven.test(4);                  // true
```

Each specialization uses a differently-named method (`applyAsInt`, `test`, `getAsInt`, and so on, depending on which interface) instead of the generic `apply`/`test`/`get`, but the underlying idea is identical — only the boxing is removed.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Generic Function boxes int into Integer at every call; IntUnaryOperator works with raw int the whole way through, avoiding that overhead">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="28" fill="#8b949e" font-size="11" font-family="sans-serif">Function&lt;Integer,Integer&gt; -- boxes on every call</text>
  <rect x="20" y="38" width="180" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="110" y="58" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">int -&gt; box -&gt; Integer</text>
  <rect x="220" y="38" width="180" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="310" y="58" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">apply(Integer)</text>
  <rect x="420" y="38" width="180" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="510" y="58" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">Integer -&gt; unbox -&gt; int</text>

  <text x="20" y="105" fill="#8b949e" font-size="11" font-family="sans-serif">IntUnaryOperator -- raw int the whole way through</text>
  <rect x="20" y="115" width="580" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="310" y="135" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">int -&gt; applyAsInt(int) -&gt; int  -- no boxing at all</text>
</svg>

Same idea, but the primitive-specialized version skips the box/unbox round trip entirely.

## 5. Runnable example

Scenario: processing a large array of measurements — evolved from `IntUnaryOperator` transforming values with no boxing, through `ToIntFunction` and `IntPredicate` used together to extract and filter primitive data from objects, to `IntStream` built entirely around these primitive-specialized interfaces for a full numeric pipeline.

### Level 1 — Basic

```java
import java.util.function.*;

public class PrimitiveSpecializationBasic {
    public static void main(String[] args) {
        IntUnaryOperator celsiusToFahrenheit = celsius -> celsius * 9 / 5 + 32;

        int[] readings = { 0, 20, 37, 100 };
        for (int celsius : readings) {
            System.out.println(celsius + "C -> " + celsiusToFahrenheit.applyAsInt(celsius) + "F");
        }
    }
}
```

**How to run:** `java PrimitiveSpecializationBasic.java`

Expected output:
```
0C -> 32F
20C -> 68F
37C -> 98F
100C -> 212F
```

`celsiusToFahrenheit.applyAsInt(celsius)` takes and returns a raw `int` throughout — no `Integer` object is ever created for any of these calls, unlike an equivalent `Function<Integer, Integer>` would silently create on every single invocation.

### Level 2 — Intermediate

```java
import java.util.function.*;
import java.util.*;

public class PrimitiveSpecializationExtractFilter {
    record Sensor(String name, int reading) {}

    public static void main(String[] args) {
        List<Sensor> sensors = List.of(
                new Sensor("A", 15),
                new Sensor("B", 92),
                new Sensor("C", 45),
                new Sensor("D", 3)
        );

        // ToIntFunction<T>: extracts a primitive int FROM an object -- avoids boxing the extracted value.
        ToIntFunction<Sensor> extractReading = Sensor::reading;
        // IntPredicate: tests a primitive int directly -- avoids boxing to check the condition.
        IntPredicate isAlert = reading -> reading > 50;

        for (Sensor sensor : sensors) {
            int reading = extractReading.applyAsInt(sensor);
            boolean alert = isAlert.test(reading);
            System.out.println(sensor.name() + ": " + reading + (alert ? " ALERT" : ""));
        }
    }
}
```

**How to run:** `java PrimitiveSpecializationExtractFilter.java`

Expected output:
```
A: 15
B: 92 ALERT
C: 45
D: 3
```

The real-world concern this adds: `extractReading` pulls a raw `int` field out of each `Sensor` object without boxing it, and `isAlert` checks that raw `int` directly against a threshold, again without boxing — the entire per-sensor check runs on primitive `int` values from extraction through comparison, exactly the kind of tight, numeric-heavy loop where avoiding boxing matters most.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class PrimitiveSpecializationIntStream {
    record Sensor(String name, int reading) {}

    public static void main(String[] args) {
        List<Sensor> sensors = List.of(
                new Sensor("A", 15),
                new Sensor("B", 92),
                new Sensor("C", 45),
                new Sensor("D", 3),
                new Sensor("E", 70)
        );

        // IntStream is built entirely on primitive-specialized interfaces:
        // mapToInt takes a ToIntFunction<T>, filter takes an IntPredicate, map takes an IntUnaryOperator.
        IntSummaryStatistics stats = sensors.stream()
                .mapToInt(Sensor::reading)      // ToIntFunction<Sensor> -- extract int, no boxing
                .filter(reading -> reading > 10) // IntPredicate -- test int, no boxing
                .map(reading -> reading * 2)     // IntUnaryOperator -- transform int, no boxing
                .summaryStatistics();

        System.out.println("Count: " + stats.getCount());
        System.out.println("Sum: " + stats.getSum());
        System.out.println("Max: " + stats.getMax());
        System.out.println("Average: " + stats.getAverage());
    }
}
```

**How to run:** `java PrimitiveSpecializationIntStream.java`

Expected output:
```
Count: 4
Sum: 444
Max: 184
Average: 111.0
```

`IntStream` is the natural home for primitive specializations at scale: `mapToInt` extracts a raw `int` per element (skipping `D`'s reading of `3` after the filter, since it's the only reading `<= 10`), `filter` and `map` continue operating on raw `int`s throughout, and `summaryStatistics()` computes count/sum/min/max/average over the primitive stream — the entire pipeline, from object extraction through transformation to aggregation, never boxes a single value.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `sensors` holds five `Sensor` records with readings `15, 92, 45, 3, 70`.

`sensors.stream()` produces a `Stream<Sensor>`. `.mapToInt(Sensor::reading)` converts it to an `IntStream`, calling the `ToIntFunction<Sensor>` `Sensor::reading` on each element to extract its raw `int` reading — producing the primitive sequence `15, 92, 45, 3, 70`, with no `Integer` boxing anywhere in this step.

`.filter(reading -> reading > 10)` applies an `IntPredicate` to each value: `15 > 10` true (kept), `92 > 10` true (kept), `45 > 10` true (kept), `3 > 10` false (dropped), `70 > 10` true (kept). The stream is now `15, 92, 45, 70`.

`.map(reading -> reading * 2)` applies an `IntUnaryOperator`, doubling each surviving value: `15 -> 30`, `92 -> 184`, `45 -> 90`, `70 -> 140`. The stream is now `30, 184, 90, 140`.

```
extract: 15, 92, 45, 3, 70
filter (>10): 15, 92, 45, 70      (3 dropped)
map (*2): 30, 184, 90, 140
```

`.summaryStatistics()` consumes this final `IntStream` and computes aggregates in one pass: `getCount()` returns `4` (four values remain); `getSum()` returns `30 + 184 + 90 + 140 = 444`; `getMax()` returns `184` (the largest of the four); `getAverage()` returns `444 / 4.0 = 111.0`. Each of these is printed in turn by `main`.

## 7. Gotchas & takeaways

> Not every primitive-specialized combination exists in the JDK — there's no `IntToLongFunction` covering every conceivable primitive-to-primitive pairing, though the most common ones (`IntToLongFunction`, `IntToDoubleFunction`, and their `long`/`double` counterparts) do exist. For an unusual combination the JDK doesn't provide, you fall back to the boxed generic interfaces, accepting the boxing cost, or define your own specialized interface if the volume genuinely warrants it.

- Primitive specializations (`IntFunction`, `ToIntFunction`, `IntPredicate`, `IntSupplier`, `IntConsumer`, `IntUnaryOperator`, `IntBinaryOperator`, and their `Long`/`Double` counterparts) exist purely to avoid the boxing overhead of using `Integer`/`Long`/`Double` with the generic functional interfaces.
- The method names differ from the generic interfaces' `apply`/`test`/`get` — typically `applyAsInt`, `getAsInt`, `test` (unchanged for predicates), or similar — because a primitive-specialized interface can't use the same generic method signature as its boxed counterpart.
- `IntStream`, `LongStream`, and `DoubleStream` are built entirely around these primitive-specialized interfaces — `mapToInt`, `filter`, `map`, and similar methods on them expect the primitive-specialized functional interfaces, not the boxed generic ones.
- For everyday, low-volume code, boxing overhead is not worth worrying about — reach for primitive specializations specifically for numeric-heavy loops, large streams, or when profiling shows boxing is a real cost.
- Only `int`, `long`, and `double` get this treatment in the JDK (no `byte`, `short`, `float`, `char`, or `boolean` specializations exist) — these three are the primitives the JDK's designers judged most likely to appear in performance-sensitive numeric code.
