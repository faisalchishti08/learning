---
card: java
gi: 357
slug: lower-bounded-wildcard-super-t
title: Lower-bounded wildcard (? super T)
---

## 1. What it is

A lower-bounded wildcard, `? super T`, restricts an unknown type to "T or some supertype of T" — `List<? super Integer>` means "a list of some specific type that is `Integer` or a supertype of it (`Number`, `Object`)." Unlike an upper-bounded wildcard, this is the shape you want when you need to *write* values of a known type into a collection whose exact element type is broader than (or equal to) that known type, without knowing or needing to know exactly how much broader.

```java
import java.util.List;
import java.util.ArrayList;

public class LowerBoundedDemo {
    static void addNumbers(List<? super Integer> list) { // accepts List<Integer>, List<Number>, List<Object>
        list.add(1);
        list.add(2);
        list.add(3);
    }

    public static void main(String[] args) {
        List<Number> numbers = new ArrayList<>();
        addNumbers(numbers); // Integer values added into a List<Number>
        System.out.println(numbers);
    }
}
```

`addNumbers(List<? super Integer> list)` accepts a `List<Number>` (a genuine supertype of `Integer`), and safely adds `Integer` values into it — something a parameter typed `List<Integer>` could never accept, since `List<Number>` is not a subtype of `List<Integer>`.

## 2. Why & when

Lower-bounded wildcards exist for the mirror-image scenario of upper bounds: instead of "read elements of at least this type," it's "write elements of exactly this known type into a collection that might be typed even more broadly." This comes up whenever a method's job is to *supply* or *insert* values of a specific type into a caller-provided collection, without dictating exactly what that collection's declared element type must be.

- **Populating a caller-supplied collection with a specific known type** — a method that generates or adds `Integer` values doesn't need the caller's list to be `List<Integer>` specifically; `List<Number>` or `List<Object>` works equally well as a destination.
- **Following the standard "write into it" half of the PECS guideline** — Consumer Super: when a generic parameter is only ever written to (consumes values you supply), a lower-bounded wildcard is usually the right choice.
- **Maximizing flexibility for callers supplying the destination collection** — a caller with a `List<Object>` meant to hold mixed content can still pass it to a method that only adds `Integer`s, without needing to narrow their own collection's type.

Reading from a lower-bounded wildcard collection is restricted to `Object` — since the actual element type could be anything from `Integer` up to `Object` itself, the compiler can only guarantee that whatever comes out is *at least* an `Object`, which is the mirror image of an upper-bounded wildcard's write restriction.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class LowerBoundedCore {
    static void fillWithSquares(List<? super Integer> list, int upTo) {
        for (int i = 1; i <= upTo; i++) list.add(i * i); // writing Integers is safe
        // int first = list.get(0); // would NOT compile -- only known to be an Object
        Object first = list.get(0); // reading is only guaranteed to be Object
        System.out.println("First element (as Object): " + first);
    }

    public static void main(String[] args) {
        List<Object> destination = new ArrayList<>();
        fillWithSquares(destination, 5);
        System.out.println(destination);
    }
}
```

**How to run:** `java LowerBoundedCore.java`

`fillWithSquares` freely adds `Integer` values into `list` (safe, since `Integer` is guaranteed compatible with whatever supertype the list actually is), but reading an element back out only yields `Object`, since that's the only type the compiler can guarantee regardless of whether the real list is `List<Integer>`, `List<Number>`, or `List<Object>`.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a lower-bounded wildcard List<? super Integer> accepts a list of Integer or any of its supertypes, allowing Integer values to be safely written in">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="260" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">addNumbers(List&lt;? super Integer&gt;)</text>

  <text x="300" y="50" fill="#8b949e" font-size="10">accepts:</text>
  <rect x="360" y="15" width="110" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="415" y="32" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Integer&gt;</text>
  <rect x="360" y="45" width="110" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="415" y="62" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Number&gt;</text>
  <rect x="360" y="75" width="110" height="25" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="415" y="92" fill="#6db33f" font-size="9" text-anchor="middle">List&lt;Object&gt;</text>
</svg>

## 5. Runnable example

Scenario: a small number-generating utility that fills a caller-provided destination, evolved from one requiring an exact destination type, into one accepting any sufficiently-broad destination via a lower-bounded wildcard, into a production-style generator combining a producer source with a consumer destination in one method.

### Level 1 — Basic

```java
import java.util.List;
import java.util.ArrayList;

public class FillBasic {
    static void fillWithCounts(List<Integer> list, int upTo) { // requires the EXACT type List<Integer>
        for (int i = 1; i <= upTo; i++) list.add(i);
    }

    public static void main(String[] args) {
        List<Integer> destination = new ArrayList<>();
        fillWithCounts(destination, 5);
        System.out.println(destination);
        // List<Number> broader = new ArrayList<>();
        // fillWithCounts(broader, 5); // would NOT compile -- List<Number> isn't List<Integer>
    }
}
```

**How to run:** `java FillBasic.java`

This only accepts `List<Integer>` exactly — a caller with a `List<Number>` (a perfectly reasonable destination for `Integer` values conceptually) can't use this method at all, even though every `Integer` genuinely is a `Number`.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.ArrayList;

public class FillIntermediate {
    static void fillWithCounts(List<? super Integer> list, int upTo) { // lower-bounded wildcard
        for (int i = 1; i <= upTo; i++) list.add(i);
    }

    public static void main(String[] args) {
        List<Integer> exact = new ArrayList<>();
        fillWithCounts(exact, 3);
        System.out.println("Into List<Integer>: " + exact);

        List<Number> broader = new ArrayList<>();
        fillWithCounts(broader, 3);
        System.out.println("Into List<Number>: " + broader);

        List<Object> broadest = new ArrayList<>();
        fillWithCounts(broadest, 3);
        System.out.println("Into List<Object>: " + broadest);
    }
}
```

**How to run:** `java FillIntermediate.java`

The same `fillWithCounts` method now works for `List<Integer>`, `List<Number>`, and `List<Object>` destinations alike — each accepts `Integer` values being added, since `Integer` is compatible with all three as a supertype relationship.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;

public class FillAdvanced {
    // Combines an upper-bounded producer (source) with a lower-bounded consumer (destination) --
    // the classic PECS pattern in a single method.
    static void copyAtLeast(List<? extends Number> source, List<? super Number> destination) {
        for (Number n : source) { // reading from source: safe, guaranteed at least Number
            destination.add(n);   // writing into destination: safe, Number fits any supertype of Number
        }
    }

    public static void main(String[] args) {
        List<Integer> intSource = List.of(1, 2, 3);
        List<Object> objectDestination = new ArrayList<>();
        copyAtLeast(intSource, objectDestination);
        System.out.println("Copied into List<Object>: " + objectDestination);

        List<Double> doubleSource = List.of(1.1, 2.2);
        List<Number> numberDestination = new ArrayList<>();
        copyAtLeast(doubleSource, numberDestination);
        System.out.println("Copied into List<Number>: " + numberDestination);
    }
}
```

**How to run:** `java FillAdvanced.java`

`copyAtLeast` combines both wildcard forms at once: `source` is upper-bounded (`? extends Number`, a producer we only read from) and `destination` is lower-bounded (`? super Number`, a consumer we only write to) — this is the textbook shape for a generic copy operation, and it's exactly why the JDK's own `Collections.copy` method uses this same pattern.

## 6. Walkthrough

Execution starts in `main`, which creates `intSource` (a `List<Integer>`) and `objectDestination` (an empty `List<Object>`), then calls `copyAtLeast(intSource, objectDestination)`.

Inside `copyAtLeast`, the parameter types are checked: `List<Integer>` satisfies `List<? extends Number>` (`Integer` is a subtype of `Number`), and `List<Object>` satisfies `List<? super Number>` (`Object` is a supertype of `Number`) — both arguments are accepted.

The `for (Number n : source)` loop reads each element of `intSource` as a `Number` (the upper bound guarantees at least this much, even though the real elements are `Integer`s): first `1`, then `2`, then `3`. Each is passed to `destination.add(n)` — since `destination`'s real type (`List<Object>`) is guaranteed to be a supertype of `Number` (per the lower bound), adding a `Number` into it is always safe. After the loop, `objectDestination` contains `[1, 2, 3]` (as boxed `Integer` objects, stored as `Object` references).

`main` prints `Copied into List<Object>: [1, 2, 3]`.

`main` then creates `doubleSource` (a `List<Double>`) and `numberDestination` (an empty `List<Number>`), calling `copyAtLeast(doubleSource, numberDestination)`. The same logic applies: `List<Double>` satisfies `List<? extends Number>`, `List<Number>` satisfies `List<? super Number>` (since `Number` is trivially its own supertype). The loop reads `1.1` and `2.2` as `Number`, adding each into `numberDestination`. `main` prints `Copied into List<Number>: [1.1, 2.2]`.

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each element is read from the producer source as Number and written into the consumer destination, safe in both directions regardless of the destination's exact broader type">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">copyAtLeast(List&lt;Integer&gt; source, List&lt;Object&gt; destination):</text>
  <text x="20" y="52" fill="#79c0ff" font-size="10">  for each: read as Number (extends bound) -&gt; add into destination (super bound) -&gt; [1,2,3]</text>
  <text x="20" y="82" fill="#6db33f" font-size="10">copyAtLeast(List&lt;Double&gt; source, List&lt;Number&gt; destination):</text>
  <text x="20" y="104" fill="#6db33f" font-size="10">  for each: read as Number -&gt; add into destination -&gt; [1.1, 2.2]</text>
  <text x="20" y="134" fill="#8b949e" font-size="10">Same method body works for any valid producer/consumer pairing satisfying both wildcard bounds.</text>
</svg>

## 7. Gotchas & takeaways

> Reading an element out of a `List<? super Integer>` only yields `Object`, never `Integer` directly — the compiler only knows the list's real type is *at least as broad as* `Integer` going up toward `Object`, so it can't guarantee anything more specific comes back out, even though you know you only ever put `Integer`s in.

- `? super T` means "T or some unknown supertype of T" — you can safely write values of type `T` (or its subtypes) into such a collection.
- Writing into a lower-bounded wildcard collection is safe for the bound type (or its subtypes); reading from it only yields `Object`, since the real element type could be anywhere from `T` up to `Object`.
- Use a lower-bounded wildcard when a generic parameter is a "consumer" — something your method only writes values *into* — following the Consumer Super half of the PECS guideline.
- The classic combined pattern — an upper-bounded producer paired with a lower-bounded consumer in the same method (as in `copyAtLeast`) — is exactly how the JDK's own `Collections.copy(List<? super T> dest, List<? extends T> src)` is written.
- Lower-bounded wildcards are less common in everyday code than upper-bounded ones, precisely because "read from" scenarios are more frequent than "write a known type into a broader destination" scenarios — but when the latter comes up, `? super T` is the correct and often only clean solution.
