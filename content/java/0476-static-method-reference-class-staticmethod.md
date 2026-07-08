---
card: java
gi: 476
slug: static-method-reference-class-staticmethod
title: 'Static method reference (Class::staticMethod)'
---

## 1. What it is

A **static method reference**, written `ClassName::staticMethodName`, is shorthand for a lambda whose entire body is just "call this static method with the arguments I was given." `Integer::parseInt` means exactly the same thing as `s -> Integer.parseInt(s)` — it's not a different mechanism, just a more compact way to write a lambda when the lambda's whole job is delegating straight to an existing static method.

## 2. Why & when

When a lambda's body is nothing more than forwarding its arguments to an existing method, writing out the lambda syntax (`s -> Integer.parseInt(s)`) adds ceremony — parameter names, an arrow — around an idea that's really just "use that method, right there." A method reference strips that ceremony away: `Integer::parseInt` says the same thing with less to read, and it directly names the method being reused, which can make intent clearer than a freshly-invented parameter name would.

You reach for a static method reference any time you'd otherwise write a lambda that does nothing but call one static method with the lambda's own parameters, in order, with no other logic. `Integer::parseInt`, `Math::max`, `String::valueOf` are common examples — passed directly to `Stream.map`, `Comparator.comparing`, or anywhere else a matching functional interface is expected. If the lambda would need to do anything else — transform an argument first, add a condition — a method reference can't express that; you'd need an actual lambda (or an intermediate method) instead.

## 3. Core concept

```java
import java.util.*;
import java.util.function.*;
import java.util.stream.*;

// These two lines are exactly equivalent:
Function<String, Integer> parseA = s -> Integer.parseInt(s);
Function<String, Integer> parseB = Integer::parseInt;

List<String> numbers = List.of("3", "1", "4", "1", "5");
List<Integer> parsed = numbers.stream()
        .map(Integer::parseInt)   // same as .map(s -> Integer.parseInt(s))
        .collect(Collectors.toList());
```

`Integer::parseInt` is resolved against the target type (here, `Function<String, Integer>`, inferred from `Stream.map`'s expected argument) exactly the way a lambda would be — this is target typing at work, just applied to a method reference instead of a lambda expression.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A static method reference is shorthand for a lambda that forwards its arguments directly to that static method">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="280" height="34" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="160" y="52" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">s -&gt; Integer.parseInt(s)</text>

  <text x="320" y="52" fill="#8b949e" font-size="14" font-family="sans-serif">==</text>

  <rect x="360" y="30" width="260" height="34" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="490" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">Integer::parseInt</text>

  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Same compiled behaviour -- the method reference is purely a shorter way to write the lambda.</text>
</svg>

Same behavior, shorter to write — a method reference is not a new capability, just a more compact spelling.

## 5. Runnable example

Scenario: parsing and formatting a list of raw numeric strings — evolved from a static method reference used directly with `Stream.map`, through combining several static method references into one pipeline, to using a static method reference as a `Comparator` factory for sorting.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class StaticMethodRefBasic {
    public static void main(String[] args) {
        List<String> rawNumbers = List.of("3", "1", "4", "1", "5", "9");

        List<Integer> parsed = rawNumbers.stream()
                .map(Integer::parseInt)
                .collect(Collectors.toList());

        System.out.println(parsed);
    }
}
```

**How to run:** `java StaticMethodRefBasic.java`

Expected output:
```
[3, 1, 4, 1, 5, 9]
```

`Integer::parseInt` is used directly as the `Function<String, Integer>` argument to `Stream.map` — no lambda syntax needed, since the whole operation is just "call this static method on each element."

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class StaticMethodRefPipeline {
    public static void main(String[] args) {
        List<String> rawNumbers = List.of("30", "-5", "12", "-8", "45");

        List<Integer> processed = rawNumbers.stream()
                .map(Integer::parseInt)      // String -> int
                .map(Math::abs)              // int -> int, absolute value
                .sorted()                     // natural order
                .collect(Collectors.toList());

        System.out.println(processed);
    }
}
```

**How to run:** `java StaticMethodRefPipeline.java`

Expected output:
```
[5, 8, 12, 30, 45]
```

The real-world concern this adds: multiple static method references chain together into a real pipeline, each doing exactly one well-defined step — parse, then take the absolute value — without any of them needing to be written as a full lambda. `sorted()` (no argument, natural ordering) then arranges the results ascending.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class StaticMethodRefComparator {
    public static void main(String[] args) {
        List<String> rawNumbers = List.of("30", "-5", "12", "-8", "45", "-100");

        // Comparator.comparing takes a key-extraction Function -- a static method reference
        // works perfectly here too, since Math::abs matches the needed shape.
        List<Integer> sortedByMagnitude = rawNumbers.stream()
                .map(Integer::parseInt)
                .sorted(Comparator.comparing(Math::abs))
                .collect(Collectors.toList());

        System.out.println(sortedByMagnitude);
    }
}
```

**How to run:** `java StaticMethodRefComparator.java`

Expected output:
```
[-5, -8, 12, 30, 45, -100]
```

`Comparator.comparing(Math::abs)` builds a `Comparator<Integer>` that orders elements by the result of `Math.abs(element)` rather than the element's own natural value — `Math::abs` here plays the role of a key-extraction function, and a static method reference fits that role just as naturally as it fit `Function` and the earlier `map` calls, since `Comparator.comparing` only needs *some* `Function<T, R>` producing a `Comparable` key.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `rawNumbers` holds six strings: `"30", "-5", "12", "-8", "45", "-100"`.

`rawNumbers.stream().map(Integer::parseInt)` converts each string to an `int` via `Integer.parseInt`, producing the sequence `30, -5, 12, -8, 45, -100` as a `Stream<Integer>`.

`.sorted(Comparator.comparing(Math::abs))` sorts this stream using a comparator built from `Math::abs`. For each pair the sort algorithm compares, it computes `Math.abs(...)` on both elements and compares those absolute values instead of the elements themselves: `abs(30)=30`, `abs(-5)=5`, `abs(12)=12`, `abs(-8)=8`, `abs(45)=45`, `abs(-100)=100`.

```
value:    30   -5   12   -8   45  -100
abs:      30    5   12    8   45   100
```

Sorting by these absolute values ascending gives the order `5, 8, 12, 30, 45, 100`, which correspond to the original elements `-5, -8, 12, 30, 45, -100` — each element keeps its original sign, since only the *comparison key* (the absolute value) changed, not the elements being sorted. `Collectors.toList()` gathers this order into the final list, which `main` prints: `[-5, -8, 12, 30, 45, -100]`.

## 7. Gotchas & takeaways

> A method reference must match the target functional interface's parameter *count and order* exactly, with no room to reorder, drop, or transform arguments along the way — `Integer::parseInt` works as a `Function<String, Integer>` because its one parameter and return type line up perfectly. The moment you need to reorder arguments, supply a constant alongside a parameter, or do anything beyond straight forwarding, a method reference can't express it and you need an actual lambda.

- `ClassName::staticMethodName` is shorthand for a lambda that calls that static method, forwarding the lambda's own parameters to it in order — nothing more.
- It's resolved against a target type exactly like a lambda expression would be — the same target-typing rules apply, including the arity/type matching that determines whether the reference is even valid at a given call site.
- Common examples: `Integer::parseInt`, `Math::abs`, `Math::max`, `String::valueOf` — any static method whose parameter list and return type happen to match a needed functional interface.
- `Comparator.comparing(keyExtractor)` frequently pairs with a static method reference as the key extractor, when the "key" is simply the result of calling some static method on each element.
- If the lambda you'd otherwise write needs any logic beyond pure forwarding — reordering arguments, adding a constant, branching — a method reference cannot express it; fall back to an explicit lambda.
