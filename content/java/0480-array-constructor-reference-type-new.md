---
card: java
gi: 480
slug: array-constructor-reference-type-new
title: 'Array constructor reference (Type[]::new)'
---

## 1. What it is

An **array constructor reference**, written `Type[]::new`, is shorthand for a lambda that creates a new array of that type with a given length. `String[]::new` means the same thing as `size -> new String[size]` — its single `int` parameter becomes the array's length. This is a special case of the constructor reference syntax, specifically for arrays, since arrays in Java don't have ordinary constructors the way classes do.

## 2. Why & when

`Stream<T>.toArray()` has two forms: a no-argument version that always returns an `Object[]` (losing your specific element type), and a version taking an `IntFunction<T[]>` that lets you specify exactly what array type you want back. Writing `size -> new String[size]` works for that second form, but `String[]::new` says the same thing more directly — "here's how to make an array of the right size and the right type" is exactly what an array constructor reference expresses.

You reach for `Type[]::new` almost exclusively with `Stream.toArray(IntFunction<T[]>)`, where you want a correctly-typed array (`String[]`, `Point[]`) rather than the generic, type-erased `Object[]` the no-argument overload returns. It's a narrow, specific tool for a narrow, specific problem — you won't use it nearly as often as the other method/constructor reference forms, but where it applies, it's the clean, idiomatic way to specify the array type.

## 3. Core concept

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

// String[]::new means: size -> new String[size]
IntFunction<String[]> makeStringArray = String[]::new;
String[] arr = makeStringArray.apply(3); // new String[3] -- {null, null, null}

List<String> names = List.of("Alice", "Bob", "Carol");

// The correctly-typed way to get a String[] back from a stream, instead of Object[]
String[] namesArray = names.stream().toArray(String[]::new);
```

`toArray(IntFunction<T[]>)` calls the supplied function exactly once, with the stream's final known size, to allocate an array of the right type and length before filling it with the stream's elements.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array constructor reference is shorthand for a lambda that allocates a new array of a given type and length">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="34" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="150" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">size -&gt; new String[size]</text>

  <text x="300" y="52" fill="#8b949e" font-size="14" font-family="sans-serif">==</text>

  <rect x="340" y="30" width="240" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">String[]::new</text>

  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Used almost exclusively with Stream.toArray(IntFunction&lt;T[]&gt;) to keep the correct element type.</text>
</svg>

The `int` length flows in; a correctly-typed, correctly-sized array flows out.

## 5. Runnable example

Scenario: converting stream results into arrays — evolved from the no-argument `toArray()` losing the specific element type, through `String[]::new` fixing that with a correctly-typed array, to using the same pattern with a custom record type to build a strongly-typed array of domain objects.

### Level 1 — Basic

```java
import java.util.*;

public class ArrayConstructorRefProblem {
    public static void main(String[] args) {
        List<String> names = List.of("Alice", "Bob", "Carol");

        // The no-argument toArray() ALWAYS returns Object[], regardless of the actual element type.
        Object[] objectArray = names.stream().toArray();

        System.out.println(objectArray.length);
        System.out.println(objectArray.getClass().getSimpleName());
        // objectArray[0] IS a String at runtime, but the ARRAY'S TYPE is Object[], not String[] --
        // trying to treat it as a String[] (e.g. String[] wrong = (String[]) objectArray;)
        // would throw ClassCastException, since the array itself was never created as a String[].
    }
}
```

**How to run:** `java ArrayConstructorRefProblem.java`

Expected output:
```
3
Object[]
```

`Stream.toArray()` (no arguments) always produces an `Object[]` — even though every element is genuinely a `String`, the array container itself is typed as `Object[]`, which loses information a caller might need (like being able to pass it to an API expecting `String[]` specifically).

### Level 2 — Intermediate

```java
import java.util.*;

public class ArrayConstructorRefBasic {
    public static void main(String[] args) {
        List<String> names = List.of("Alice", "Bob", "Carol");

        // toArray(IntFunction<T[]>) with String[]::new produces a genuinely typed String[].
        String[] namesArray = names.stream().toArray(String[]::new);

        System.out.println(namesArray.length);
        System.out.println(namesArray.getClass().getSimpleName());
        System.out.println(Arrays.toString(namesArray));
    }
}
```

**How to run:** `java ArrayConstructorRefBasic.java`

Expected output:
```
3
String[]
[Alice, Bob, Carol]
```

The real-world concern this fixes: `String[]::new` is called once, internally, with the stream's final size (`3`), producing an actual `String[3]` array, which the stream then fills with its elements — `namesArray.getClass().getSimpleName()` now correctly reports `"String[]"`, and the array can be passed anywhere a genuine `String[]` is required, unlike the `Object[]` from Level 1.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ArrayConstructorRefRecords {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        List<int[]> rawCoordinates = List.of(
                new int[]{0, 0},
                new int[]{3, 4},
                new int[]{-2, 5}
        );

        // Build Point objects, then collect them into a genuinely typed Point[] array,
        // not just an Object[] or a List<Point>.
        Point[] points = rawCoordinates.stream()
                .map(coords -> new Point(coords[0], coords[1]))
                .toArray(Point[]::new);

        System.out.println(points.length);
        System.out.println(points.getClass().getSimpleName());
        for (Point p : points) {
            System.out.println(p);
        }
    }
}
```

**How to run:** `java ArrayConstructorRefRecords.java`

Expected output:
```
3
Point[]
Point[x=0, y=0]
Point[x=3, y=4]
Point[x=-2, y=5]
```

This applies the same pattern to a custom `record` type rather than a built-in class like `String`: `Point[]::new` produces a genuinely typed `Point[]` array, filled with the `Point` instances the earlier `.map(...)` stage constructed — the array constructor reference works identically regardless of whether the element type is a built-in class or a type you defined yourself, since it only needs a matching array-creation expression to exist for that type (which is true for any reference type in Java).

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `rawCoordinates` holds three `int[]` arrays, each representing a raw `(x, y)` pair.

`rawCoordinates.stream()` produces a `Stream<int[]>`. `.map(coords -> new Point(coords[0], coords[1]))` transforms each raw `int[]` into a `Point`: for `{0, 0}`, `new Point(0, 0)`; for `{3, 4}`, `new Point(3, 4)`; for `{-2, 5}`, `new Point(-2, 5)`. The stream is now conceptually a `Stream<Point>` holding these three constructed records.

`.toArray(Point[]::new)` finalizes the stream into an array. Internally, this calls `Point[]::new` (the array constructor reference) exactly once, with the stream's known final size — `3` — producing a fresh `Point[3]` array (initially holding three `null` references). The stream implementation then fills that array's slots with the three `Point` instances, in stream order: index `0` gets `Point[x=0, y=0]`, index `1` gets `Point[x=3, y=4]`, index `2` gets `Point[x=-2, y=5]`.

```
{0,0}  --map--> Point(0,0)   --\
{3,4}  --map--> Point(3,4)   ---+--> Point[]::new(3) --> fill --> points[0..2]
{-2,5} --map--> Point(-2,5)  --/
```

`points.length` reports `3`, matching the array size allocated. `points.getClass().getSimpleName()` reports `"Point[]"` — confirming this is a genuinely typed `Point` array, not a generic `Object[]`. The `for` loop then iterates `points` and prints each `Point`'s auto-generated record `toString()`, in the same order they were placed into the array.

## 7. Gotchas & takeaways

> `Stream.toArray()` with no arguments is a legitimate, common choice when you genuinely don't care about the specific array type and are happy working with `Object[]` — but the moment you need to pass the result to code expecting a specific array type, or need to use the array with reflection/`instanceof` checks relying on its exact runtime type, `Type[]::new` is required; you cannot fix an already-created `Object[]`'s type after the fact by casting it.

- `Type[]::new` is shorthand for `size -> new Type[size]` — its single `int` parameter becomes the length of a newly allocated array of that type.
- Its primary, near-exclusive use is with `Stream.toArray(IntFunction<T[]>)`, producing a correctly-typed array instead of the generic `Object[]` the no-argument `toArray()` overload returns.
- The array constructor reference is called exactly once per `toArray` call, with the stream's final known size — not once per element.
- This pattern works identically for built-in types (`String[]::new`) and custom types (`Point[]::new`, for any class or record you define) — any reference type in Java supports array creation.
- If you never need the array's specific runtime type — only its elements — `Collectors.toList()` or the no-argument `toArray()` is simpler and avoids the extra ceremony of specifying an array constructor reference at all.
