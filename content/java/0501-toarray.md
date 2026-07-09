---
card: java
gi: 501
slug: toarray
title: toArray()
---

## 1. What it is

`Stream.toArray()` is a terminal operation that collects a stream's elements into a plain Java array. The no-argument form, `toArray()`, returns an `Object[]` — even for a `Stream<String>`, you get back `Object[]`, not `String[]`, because of how generics and arrays interact in Java. The overload `toArray(generator)` takes an `IntFunction<T[]>` (typically `String[]::new`) and returns a properly-typed `T[]` array instead.

## 2. Why & when

Most of the time, `.toList()` or `.collect(Collectors.toList())` is what you want from a stream — a `List<T>` is more flexible than an array. But some APIs, especially older ones or those interfacing with array-based code (varargs methods, low-level performance-sensitive code, serialization formats), specifically require a real array rather than a `List`. `toArray()` is how you get there directly from a stream, without an intermediate `List` and a separate `.toArray()` call on it.

You reach for the no-argument `toArray()` only when `Object[]` is genuinely fine (rare — usually you'd cast each element back out, which is awkward). You reach for `toArray(generator)` when you need a properly-typed array, which is the far more common case in practice.

## 3. Core concept

```java
import java.util.stream.*;

Object[] objs = Stream.of("a", "b", "c").toArray(); // Object[], not String[]

String[] strs = Stream.of("a", "b", "c").toArray(String[]::new); // properly typed String[]

int[] ints = IntStream.of(1, 2, 3).toArray(); // primitive int[] -- IntStream's toArray needs no generator
```

`Stream<T>.toArray()` needs a generator to produce a typed `T[]`; primitive streams (`IntStream`, etc.) have their own `toArray()` that returns a primitive array directly, with no generator needed.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="toArray with a generator produces a properly-typed array instead of Object[]">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="60" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"a"</text>
  <rect x="95" y="20" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="125" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"b"</text>
  <rect x="160" y="20" width="60" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="190" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">"c"</text>
  <text x="120" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">toArray(String[]::new)</text>
  <line x1="120" y1="52" x2="120" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowTA)"/>
  <rect x="30" y="90" width="190" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="125" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">String[]{"a","b","c"}</text>
  <defs><marker id="arrowTA" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Passing `String[]::new` as the generator tells `toArray` exactly what array type to build, avoiding the untyped `Object[]` result.

## 5. Runnable example

Scenario: preparing data for a legacy API that requires plain arrays — evolved from a basic typed-array conversion, through building a primitive `int[]` for a numeric API, to a version that converts a stream of custom objects into a correctly-sized, correctly-typed array using a method reference generator.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ToArrayBasic {
    public static void main(String[] args) {
        List<String> names = List.of("Alice", "Bob", "Carol");

        String[] namesArray = names.stream()
                .filter(name -> name.length() > 3)
                .toArray(String[]::new);

        System.out.println("Array length: " + namesArray.length);
        System.out.println("Contents: " + Arrays.toString(namesArray));
    }
}
```

**How to run:** `java ToArrayBasic.java`

Expected output:
```
Array length: 2
Contents: [Alice, Carol]
```

`.filter(name -> name.length() > 3)` keeps `"Alice"` and `"Carol"` (both longer than three characters), dropping `"Bob"`. `.toArray(String[]::new)` then collects the two survivors into a properly-typed `String[]` — `String[]::new` is a constructor reference that `toArray` calls internally with the correct size to allocate the array.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ToArrayPrimitive {
    public static void main(String[] args) {
        List<Integer> scores = List.of(42, 17, 99, 3, 56, 88);

        // IntStream's toArray() returns a primitive int[] directly -- no generator needed.
        int[] highScores = scores.stream()
                .mapToInt(Integer::intValue)
                .filter(score -> score >= 50)
                .toArray();

        System.out.println("High scores array: " + Arrays.toString(highScores));
        System.out.println("Sum via Arrays.stream: " + Arrays.stream(highScores).sum());
    }
}
```

**How to run:** `java ToArrayPrimitive.java`

Expected output:
```
High scores array: [99, 56, 88]
Sum via Arrays.stream: 243
```

The real-world concern this adds: numeric APIs (like `Arrays.stream(int[])`, or legacy math libraries) often expect a primitive `int[]`, not `Integer[]`. `.mapToInt(Integer::intValue)` converts the boxed `Stream<Integer>` into an `IntStream` first, so its `.toArray()` — a distinct method from `Stream<T>.toArray()` — directly returns a primitive `int[]`, with no generator argument needed at all, since primitive arrays don't have the generics erasure problem object arrays do.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ToArrayCustomObjects {
    record Point(int x, int y) {
        static Point[] arrayOf(int size) {
            return new Point[size];
        }
    }

    public static void main(String[] args) {
        List<Point> points = List.of(new Point(0, 0), new Point(1, 2), new Point(3, 4), new Point(-1, -1));

        // Only keep points in the "first quadrant" (both coordinates non-negative, excluding the origin).
        Point[] firstQuadrant = points.stream()
                .filter(p -> p.x() >= 0 && p.y() >= 0 && !(p.x() == 0 && p.y() == 0))
                .toArray(Point[]::new);

        System.out.println("Count: " + firstQuadrant.length);
        for (Point p : firstQuadrant) {
            System.out.println("(" + p.x() + ", " + p.y() + ")");
        }
    }
}
```

**How to run:** `java ToArrayCustomObjects.java`

Expected output:
```
Count: 2
(1, 2)
(3, 4)
```

This shows `toArray(generator)` working with a custom `record` type rather than a built-in one: `Point[]::new` is a constructor reference to `Point`'s implicitly-available array constructor, and `toArray` calls it with the correct final size (`2`, after filtering) to allocate exactly the right array — `(0, 0)` is excluded by the origin check, and `(-1, -1)` is excluded by the non-negative check, leaving only `(1, 2)` and `(3, 4)`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `points` holds four `Point` records: `(0,0)`, `(1,2)`, `(3,4)`, `(-1,-1)`.

`points.stream().filter(p -> p.x() >= 0 && p.y() >= 0 && !(p.x() == 0 && p.y() == 0))` evaluates the predicate on each point. For `(0,0)`: `0 >= 0` true, `0 >= 0` true, but `!(0 == 0 && 0 == 0)` is `!(true)` = `false` — the whole predicate is `false` (excluded, since the origin is deliberately not counted as being "in" a quadrant). For `(1,2)`: `1 >= 0` true, `2 >= 0` true, `!(1==0 && 2==0)` is `!(false)` = `true` — predicate is `true` (kept). For `(3,4)`: same reasoning as `(1,2)` — kept. For `(-1,-1)`: `-1 >= 0` is `false` — predicate is `false` (excluded).

```
(0,0)   -> x>=0 T, y>=0 T, not-origin F -> overall FALSE -> excluded
(1,2)   -> x>=0 T, y>=0 T, not-origin T -> overall TRUE  -> kept
(3,4)   -> x>=0 T, y>=0 T, not-origin T -> overall TRUE  -> kept
(-1,-1) -> x>=0 F (short-circuits)      -> overall FALSE -> excluded
```

After filtering, two points remain: `(1,2)` and `(3,4)`, in their original relative order. `.toArray(Point[]::new)` is called: internally, the stream machinery already knows the final count is `2` (having consumed the whole filtered stream), so it invokes `Point[]::new` with `2`, producing a fresh, correctly-sized `Point[2]` array, then copies the two surviving `Point` references into it.

`firstQuadrant.length` is `2`, printed as `"Count: 2"`. The `for` loop then iterates the array in order, printing `"(1, 2)"` and `"(3, 4)"` — the two points that survived the quadrant-and-not-origin check.

## 7. Gotchas & takeaways

> The no-argument `Stream<T>.toArray()` always returns `Object[]`, **never** `T[]`, even when `T` is known at compile time — this is a consequence of Java generics being erased at runtime, so the stream has no way to know what concrete array type to allocate without being told explicitly via a generator. Casting the `Object[]` result to `T[]` at the call site throws `ClassCastException` at runtime — always use `toArray(generator)` when a typed array is needed.

- `Stream<T>.toArray()` (no arguments) returns `Object[]`; use `toArray(generator)` (e.g. `String[]::new`) to get a properly-typed `T[]`.
- Primitive streams (`IntStream`, `LongStream`, `DoubleStream`) have their own `toArray()` that returns a primitive array directly (`int[]`, etc.) with no generator needed, since primitive arrays don't suffer from generics erasure.
- The generator function (`T[]::new`) is called once, internally, with the correct final size — you don't need to pre-size or pre-allocate anything yourself.
- For most code, `.toList()` (returning an immutable `List<T>`) is simpler and more idiomatic than `.toArray(...)`; reach for `toArray` specifically when an array is required by the API you're calling into.
- `Arrays.stream(array)` is the reverse direction — going from an existing array back into a stream — useful when you need to round-trip between array-based and stream-based APIs.
