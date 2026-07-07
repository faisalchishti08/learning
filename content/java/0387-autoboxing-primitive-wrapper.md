---
card: java
gi: 387
slug: autoboxing-primitive-wrapper
title: 'Autoboxing (primitive → wrapper)'
---

## 1. What it is

**Autoboxing** is the compiler's automatic conversion of a primitive value (`int`, `double`, `boolean`, etc.) into its corresponding wrapper object (`Integer`, `Double`, `Boolean`) whenever a wrapper type is required but a primitive is supplied. Before Java 5, this conversion had to be written out by hand (`Integer.valueOf(5)`); since Java 5, the compiler inserts it automatically wherever needed — assigning an `int` to an `Integer` variable, passing an `int` where an `Object` or `Integer` parameter is expected, or adding an `int` into a `List<Integer>`.

## 2. Why & when

Generics (introduced in the same Java 5 release) can only work with reference types, never primitives directly (see [[cannot-use-primitives-as-type-args]]) — `List<int>` is illegal, only `List<Integer>` compiles. Without autoboxing, every single interaction between primitive values and generic collections, or any API expecting `Object`, would require manually writing `Integer.valueOf(n)` everywhere, cluttering ordinary code with conversions that add no real information. Autoboxing makes primitives and their wrapper classes interoperate almost seamlessly at the source level, even though they remain genuinely different things underneath — a primitive `int` is a raw stack value, an `Integer` is a full heap-allocated object with identity and methods.

You benefit from autoboxing constantly, usually without noticing: putting an `int` literal into a `List<Integer>`, returning an `int` from a method declared to return `Integer`, or passing a `double` where a method expects `Double`. It's most visible (and most worth understanding precisely) when things go subtly wrong — covered in [[autoboxing-pitfalls-npe-identity-caching-128-127]].

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class AutoboxingDemo {
    public static void main(String[] args) {
        Integer boxed = 5; // autoboxing: int 5 -> Integer.valueOf(5), inserted by the compiler
        System.out.println(boxed.getClass().getSimpleName()); // Integer -- a real object now

        List<Integer> numbers = new ArrayList<>();
        numbers.add(10); // autoboxing again: the int literal 10 becomes an Integer before storage
        System.out.println(numbers.get(0).getClass().getSimpleName());
    }
}
```

**How to run:** `java AutoboxingDemo.java`

`Integer boxed = 5` looks like assigning a primitive directly, but the compiler actually generates `Integer boxed = Integer.valueOf(5)` — `boxed` genuinely holds a real `Integer` object, confirmed by `boxed.getClass().getSimpleName()` printing `Integer`. `numbers.add(10)` similarly boxes the literal `int 10` before it's stored, since `List<Integer>` can only ever hold `Integer` objects, never raw primitives.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="autoboxing inserts an automatic conversion from a raw primitive value to a heap-allocated wrapper object whenever a reference type context requires it">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="40" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="63" fill="#79c0ff" font-size="11" text-anchor="middle">int 5</text>
  <text x="120" y="78" fill="#8b949e" font-size="9" text-anchor="middle">raw stack value</text>

  <text x="240" y="65" fill="#e6edf3" font-size="11">Integer.valueOf(5)</text>
  <text x="240" y="80" fill="#8b949e" font-size="9">compiler-inserted call</text>

  <rect x="410" y="40" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="510" y="63" fill="#6db33f" font-size="11" text-anchor="middle">Integer object</text>
  <text x="510" y="78" fill="#8b949e" font-size="9" text-anchor="middle">heap-allocated, has identity</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">Every place a primitive meets a reference-type context (generics, Object params) triggers this conversion.</text>
</svg>

## 5. Runnable example

Scenario: computing a running total from user-entered scores, evolved from a purely primitive version, through storing scores in a generic collection (forcing autoboxing), to a version showing autoboxing happening across a method boundary and inside a data structure at once.

### Level 1 — Basic

```java
public class ScoresPrimitiveOnly {
    public static void main(String[] args) {
        int a = 90, b = 85, c = 78; // pure primitives, no boxing anywhere
        int total = a + b + c;
        System.out.println("Total: " + total);
    }
}
```

**How to run:** `java ScoresPrimitiveOnly.java`

No generics, no `Object` parameters — everything stays as raw `int` values, so no autoboxing happens at all. This is the baseline the next levels build on.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.ArrayList;

public class ScoresBoxedList {
    public static void main(String[] args) {
        List<Integer> scores = new ArrayList<>(); // must be Integer -- generics forbid int directly
        scores.add(90); // autobox: int 90 -> Integer.valueOf(90)
        scores.add(85); // autobox: int 85 -> Integer.valueOf(85)
        scores.add(78); // autobox: int 78 -> Integer.valueOf(78)

        int total = 0;
        for (int score : scores) { // auto-unboxing happens here, the reverse conversion (see next topic)
            total += score;
        }
        System.out.println("Total: " + total);
    }
}
```

**How to run:** `java ScoresBoxedList.java`

Storing scores in a `List<Integer>` (necessary because generics can't hold primitives) triggers autoboxing on every `add` call — each `int` literal is silently converted to an `Integer` object before being stored, invisible in the source but a real conversion happening underneath.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.ArrayList;

public class ScoresBoxingAcrossBoundary {
    static void recordScore(List<Integer> scores, int newScore) { // int parameter
        Integer boxed = newScore; // autobox happens explicitly here, assigning int to Integer
        scores.add(boxed);        // no additional boxing needed -- boxed is already an Integer
    }

    static double average(List<Integer> scores) {
        int sum = 0;
        for (Integer s : scores) { // s is Integer; used in an int context below, auto-unboxed per iteration
            sum += s;
        }
        return (double) sum / scores.size();
    }

    public static void main(String[] args) {
        List<Integer> scores = new ArrayList<>();
        recordScore(scores, 90); // int argument autoboxed inside recordScore
        recordScore(scores, 85);
        recordScore(scores, 78);

        System.out.printf("Average: %.2f%n", average(scores));
    }
}
```

**How to run:** `java ScoresBoxingAcrossBoundary.java`

`recordScore` accepts a plain `int`, then explicitly autoboxes it into an `Integer` before storing it in the list — demonstrating that boxing can happen at any point where a primitive meets a reference-type context, not just directly at a collection's `add` call. `average` then unboxes each stored `Integer` back to `int` for the summation (the reverse process, covered next).

## 6. Walkthrough

Execution starts in `main`. `recordScore(scores, 90)` is called, passing the primitive `int` literal `90`. Inside `recordScore`, `Integer boxed = newScore` triggers autoboxing: the compiler generates `Integer boxed = Integer.valueOf(newScore)`, creating (or reusing, for small values — see [[autoboxing-pitfalls-npe-identity-caching-128-127]]) an `Integer` object wrapping `90`. `scores.add(boxed)` stores this `Integer` object directly into the list — no further boxing needed, since `boxed` is already the right type.

The same happens for `recordScore(scores, 85)` and `recordScore(scores, 78)`, appending two more boxed `Integer` objects to `scores`.

`average(scores)` is called next. Inside, `for (Integer s : scores)` iterates the list, binding `s` to each `Integer` object in turn: first `90`, then `85`, then `78`. `sum += s` requires an `int` operand for the addition, so each `s` is auto-unboxed back to a primitive `int` before the addition executes — `sum` accumulates `90`, then `175`, then `253`.

After the loop, `(double) sum / scores.size()` computes `253 / 3` as a floating-point division (since `sum` is cast to `double` first, avoiding integer division truncation), giving `84.333...`. This value is returned from `average` and formatted by `System.out.printf("Average: %.2f%n", ...)` to two decimal places.

Expected output:
```
Average: 84.33
```

## 7. Gotchas & takeaways

> Autoboxing happens automatically and silently, which is convenient but hides real object allocation — in a performance-sensitive loop that boxes millions of primitive values (for example, repeatedly adding to a `List<Integer>`), this invisible allocation cost can be a genuine, hard-to-spot bottleneck; prefer primitive arrays or primitive-specialized collections when that matters.

- Autoboxing is the compiler-inserted conversion from a primitive value to its corresponding wrapper object, triggered wherever a reference type is required but a primitive value is supplied.
- It exists primarily to bridge primitives with generics (which cannot hold primitive type arguments directly) and with any API expecting `Object`.
- The conversion is invisible in source code — `Integer x = 5` reads like a direct primitive assignment but is actually `Integer x = Integer.valueOf(5)` under the hood.
- Autoboxing and auto-unboxing (the reverse, see [[auto-unboxing-wrapper-primitive]]) work together to make primitive and boxed code interoperate almost seamlessly — almost, because subtle differences remain (identity, `null`-ability) that occasionally surface as real bugs.
- Be mindful of autoboxing's real allocation cost in performance-sensitive code operating on large volumes of primitive data — it is not free, even though it's syntactically invisible.
