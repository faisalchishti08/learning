---
card: java
gi: 479
slug: constructor-reference-class-new
title: 'Constructor reference (Class::new)'
---

## 1. What it is

A **constructor reference**, written `ClassName::new`, is shorthand for a lambda that constructs a new instance of that class, forwarding the lambda's parameters as the constructor's arguments. `Point::new` means the same thing as `(x, y) -> new Point(x, y)` (assuming a matching two-argument constructor exists) — it's the same family of shorthand as method references, applied to object creation instead of an existing method call.

## 2. Why & when

Just as a static or instance method reference removes the ceremony from a lambda that only forwards to an existing method, a constructor reference removes the ceremony from a lambda whose only job is calling `new`. `Supplier<ArrayList<String>> factory = ArrayList::new` reads as directly as "a supplier that makes new array lists" — clearer than the equivalent `() -> new ArrayList<String>()`, and just as functionally identical.

You reach for a constructor reference whenever an API wants "a way to create new instances" — `Stream.collect` with a custom `Supplier` for the container, `Collectors.toCollection(TreeSet::new)` to control which collection type a stream collects into, or `Map.computeIfAbsent(key, k -> new ArrayList<>())`-style code, more idiomatically written `Map.computeIfAbsent(key, k -> ArrayList::new)`-shaped constructs, or simply any of your own code accepting a `Supplier<T>` or `Function<Args, T>` where the caller should be able to supply "how to build one of these."

## 3. Core concept

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

record Point(int x, int y) {}

// Constructor reference matching a two-argument constructor:
BiFunction<Integer, Integer, Point> makePoint = Point::new;
Point p = makePoint.apply(3, 4); // Point[x=3, y=4]

// Constructor reference matching a no-argument constructor:
Supplier<ArrayList<String>> newList = ArrayList::new;
ArrayList<String> list = newList.get(); // a fresh, empty ArrayList

// Common in stream collection: control WHICH concrete type to collect into
TreeSet<String> sorted = Stream.of("banana", "apple", "cherry")
        .collect(Collectors.toCollection(TreeSet::new));
```

Just like a method reference, the constructor reference is resolved against a target functional interface — its parameter count and types must match a constructor that actually exists on the class.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A constructor reference is shorthand for a lambda that calls new with the lambda's parameters forwarded as constructor arguments">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="280" height="34" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">(x, y) -&gt; new Point(x, y)</text>

  <text x="320" y="52" fill="#8b949e" font-size="14" font-family="sans-serif">==</text>

  <rect x="360" y="30" width="260" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Point::new</text>

  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Parameter count/types must match an actual constructor on the class.</text>
</svg>

Same shorthand principle as a method reference, but pointing at construction instead of an existing method.

## 5. Runnable example

Scenario: building `Point` objects from raw coordinate data — evolved from a `BiFunction`-typed constructor reference used directly, through using a constructor reference as a `Stream.map` transformation to build objects from raw data pairs, to `Collectors.toCollection` using a constructor reference to control the exact collection type a stream is gathered into.

### Level 1 — Basic

```java
import java.util.function.*;

public class ConstructorRefBasic {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        BiFunction<Integer, Integer, Point> makePoint = Point::new;

        Point origin = makePoint.apply(0, 0);
        Point somewhere = makePoint.apply(3, 4);

        System.out.println(origin);
        System.out.println(somewhere);
    }
}
```

**How to run:** `java ConstructorRefBasic.java`

Expected output:
```
Point[x=0, y=0]
Point[x=3, y=4]
```

`Point::new` matches `Point`'s canonical two-argument constructor (auto-generated for the record, taking `int x, int y`), so it satisfies `BiFunction<Integer, Integer, Point>.apply(Integer, Integer)` — each call constructs a genuinely new `Point` instance from its two arguments.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class ConstructorRefMapping {
    record Point(int x, int y) {}

    public static void main(String[] args) {
        List<int[]> rawCoordinates = List.of(
                new int[]{0, 0},
                new int[]{3, 4},
                new int[]{-2, 5}
        );

        // A constructor reference doesn't directly fit int[] -> Point, so an intermediate
        // lambda unpacks the array first -- this shows the limit of what a bare reference can express.
        List<Point> points = rawCoordinates.stream()
                .map(coords -> new Point(coords[0], coords[1]))
                .collect(Collectors.toList());

        System.out.println(points);
    }
}
```

**How to run:** `java ConstructorRefMapping.java`

Expected output:
```
[Point[x=0, y=0], Point[x=3, y=4], Point[x=-2, y=5]]
```

The real-world concern this shows: a constructor reference only works when the lambda's parameters map **directly** onto the constructor's parameters, in order, with no unpacking or transformation. Here, each element is an `int[]` that needs to be *unpacked* into two separate arguments — something a bare `Point::new` reference cannot express — so an explicit lambda is required instead, a useful reminder that method/constructor references are strictly narrower than full lambdas.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ConstructorRefCollector {
    public static void main(String[] args) {
        List<String> words = List.of("banana", "apple", "cherry", "apple", "banana");

        // Collectors.toCollection takes a Supplier<C> -- a constructor reference controls
        // EXACTLY which concrete collection type the stream is gathered into.
        TreeSet<String> sortedUnique = words.stream()
                .collect(Collectors.toCollection(TreeSet::new));

        LinkedList<String> asLinkedList = words.stream()
                .collect(Collectors.toCollection(LinkedList::new));

        System.out.println(sortedUnique);
        System.out.println(asLinkedList);
    }
}
```

**How to run:** `java ConstructorRefCollector.java`

Expected output:
```
[apple, banana, cherry]
[banana, apple, cherry, apple, banana]
```

`Collectors.toCollection(Supplier<C>)` needs to know exactly which collection implementation to build and fill — `TreeSet::new` (matching `TreeSet`'s no-argument constructor) produces a sorted, duplicate-free set; `LinkedList::new` produces an insertion-ordered list preserving every element including duplicates. The same stream of words, collected with two different constructor references, produces two structurally different results.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `words` holds five strings, including two duplicated values (`"apple"` appears twice, `"banana"` appears twice).

The first collection, `words.stream().collect(Collectors.toCollection(TreeSet::new))`, works as follows: `Collectors.toCollection` first calls `TreeSet::new` (matching `TreeSet`'s no-argument constructor) once, to create a single, empty `TreeSet<String>` to accumulate into. Then, for each element in the stream — `"banana"`, `"apple"`, `"cherry"`, `"apple"`, `"banana"`, in order — it calls `add` on that `TreeSet`. Because `TreeSet` maintains sorted order and rejects duplicates (`add` returns `false` for an element already present, and the set is unaffected), the final set contains each distinct word exactly once, in natural (alphabetical) order: `["apple", "banana", "cherry"]`.

The second collection, `words.stream().collect(Collectors.toCollection(LinkedList::new))`, follows the identical mechanism, but `LinkedList::new` creates an empty `LinkedList<String>` instead. `LinkedList` preserves insertion order and allows duplicates, so every one of the five stream elements is added in the exact order encountered: `["banana", "apple", "cherry", "apple", "banana"]`.

```
words: banana, apple, cherry, apple, banana

TreeSet::new    --> new TreeSet()    --> add each --> sorted, deduplicated  --> [apple, banana, cherry]
LinkedList::new --> new LinkedList() --> add each --> insertion order, all --> [banana, apple, cherry, apple, banana]
```

Both collections process the exact same source stream, in the exact same order — the only difference between the two final results is which constructor reference told `Collectors.toCollection` what kind of container to build and accumulate into.

## 7. Gotchas & takeaways

> A constructor reference only works when the lambda's needed parameters map **directly and in order** onto an actual constructor's parameter list — no unpacking, reordering, or extra logic is possible, exactly the same limitation method references have (see the `ConstructorRefMapping` example, where an `int[]` needed manual unpacking first). If the class has multiple overloaded constructors, the target functional interface's parameter types determine which specific constructor the reference resolves to — the same overload-resolution-by-target-type principle covered in the target typing topic.

- `ClassName::new` is shorthand for a lambda that calls `new ClassName(...)`, forwarding the lambda's own parameters as constructor arguments, in order.
- It's resolved against a target functional interface exactly like method references are — a no-argument constructor fits `Supplier<T>`, a two-argument constructor fits `BiFunction<A, B, T>`, and so on.
- `Collectors.toCollection(constructorRef)` is a common, practical use — controlling exactly which concrete collection type a stream's results are gathered into.
- If a class has several constructors, the specific one selected depends on the target type's parameter shape — the same resolution mechanism that lets overloaded methods work with lambdas.
- When the data available doesn't line up directly with a constructor's parameters (an array needing unpacking, a value needing transformation first), an explicit lambda is required instead — a constructor reference cannot add any logic beyond straight argument forwarding.
