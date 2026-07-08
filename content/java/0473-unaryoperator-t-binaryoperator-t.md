---
card: java
gi: 473
slug: unaryoperator-t-binaryoperator-t
title: UnaryOperator<T> / BinaryOperator<T>
---

## 1. What it is

`UnaryOperator<T>` is a specialized `Function<T, T>` — one input and one output of the **exact same type**. `BinaryOperator<T>` is likewise a specialized `BiFunction<T, T, T>` — two inputs and one output, all the same type. Both interfaces exist purely to express "the input type and output type are identical" directly in the type signature, rather than repeating the same type parameter twice on a general `Function` or `BiFunction`.

## 2. Why & when

`Function<String, String>` and `UnaryOperator<String>` are behaviorally identical — `UnaryOperator<T>` literally extends `Function<T, T>` with no new methods. The reason it exists at all is readability and intent: `UnaryOperator<T>` at a glance tells a reader "this transforms a `T` into another `T`, same type both ends" without them needing to check whether the two type parameters on a `Function<T, R>` happen to match. The JDK itself uses this distinction: `List.replaceAll(UnaryOperator<E>)` requires same-type-in-same-type-out by its very signature, which a plain `Function` couldn't enforce as cleanly.

You reach for `UnaryOperator<T>` whenever a transformation genuinely keeps the same type — normalizing a `String` into another `String`, incrementing an `Integer` into another `Integer`. You reach for `BinaryOperator<T>` for the two-argument, same-type case — most commonly, **reducing** or **combining** two values of one type into a single value of that same type, exactly the shape `Stream.reduce(BinaryOperator<T>)` needs. `BinaryOperator` also adds two useful `static` factory methods, `minBy` and `maxBy`, for building a `BinaryOperator` from a `Comparator`.

## 3. Core concept

```java
import java.util.function.*;

UnaryOperator<String> trim = String::trim; // String -> String, same type
String trimmed = trim.apply("  hi  "); // "hi"

BinaryOperator<Integer> add = (a, b) -> a + b; // (Integer, Integer) -> Integer, all same type
int sum = add.apply(3, 4); // 7

// BinaryOperator.maxBy: builds a BinaryOperator<T> from a Comparator<T>
BinaryOperator<Integer> max = BinaryOperator.maxBy(Integer::compareTo);
System.out.println(max.apply(3, 7)); // 7
```

`UnaryOperator<T>` is exactly `Function<T, T>`; `BinaryOperator<T>` is exactly `BiFunction<T, T, T>` — narrower type signatures for the specific, common case where every type involved is the same.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="UnaryOperator narrows Function to same-type in and out; BinaryOperator narrows BiFunction to two same-type inputs and a same-type output">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">Function&lt;T,R&gt;  narrows to  UnaryOperator&lt;T&gt;  when R = T</text>
  <rect x="20" y="40" width="280" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">UnaryOperator&lt;String&gt; = Function&lt;String,String&gt;</text>

  <text x="20" y="95" fill="#8b949e" font-size="11" font-family="sans-serif">BiFunction&lt;T,U,R&gt;  narrows to  BinaryOperator&lt;T&gt;  when T=U=R</text>
  <rect x="20" y="105" width="380" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="210" y="125" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">BinaryOperator&lt;Integer&gt; = BiFunction&lt;Integer,Integer,Integer&gt;</text>
</svg>

Same underlying shape, narrower and more descriptive type — exactly when every type involved matches.

## 5. Runnable example

Scenario: normalizing and combining a list of raw scores — evolved from a `UnaryOperator` normalizing individual values in place, through `Stream.reduce` using a `BinaryOperator` to combine values into a running total, to `BinaryOperator.maxBy` finding the largest value from a `Comparator`.

### Level 1 — Basic

```java
import java.util.function.*;
import java.util.*;

public class UnaryOperatorBasic {
    public static void main(String[] args) {
        List<Integer> scores = new ArrayList<>(List.of(-5, 110, 42, 150, 0));

        UnaryOperator<Integer> clamp = score -> Math.max(0, Math.min(100, score));

        // List.replaceAll takes a UnaryOperator<E> specifically -- same type in, same type out.
        scores.replaceAll(clamp);

        System.out.println(scores);
    }
}
```

**How to run:** `java UnaryOperatorBasic.java`

Expected output:
```
[0, 100, 42, 100, 0]
```

`List.replaceAll(UnaryOperator<E>)` calls `clamp.apply(score)` on every element, replacing each in place with the result — its parameter type is specifically `UnaryOperator<E>`, not a general `Function`, because replacing an element in a `List<Integer>` requires the replacement to also be an `Integer`.

### Level 2 — Intermediate

```java
import java.util.function.*;
import java.util.*;

public class BinaryOperatorReduce {
    public static void main(String[] args) {
        List<Integer> scores = List.of(70, 85, 42, 91, 60);

        BinaryOperator<Integer> sum = (a, b) -> a + b;

        // Stream.reduce combines all elements pairwise into ONE final value, using a BinaryOperator<T>.
        int total = scores.stream().reduce(0, sum);

        System.out.println("Total: " + total);
        System.out.println("Average: " + (total / (double) scores.size()));
    }
}
```

**How to run:** `java BinaryOperatorReduce.java`

Expected output:
```
Total: 348
Average: 69.6
```

The real-world concern here: `Stream.reduce(identity, BinaryOperator<T>)` needs its combining function to take two `T`s and produce another `T`, since the running accumulated result and each new element must be the same type to keep combining — exactly `BinaryOperator<Integer>`'s shape. `reduce` starts with `0` (the identity value) and repeatedly applies `sum` to combine the running total with each element in turn.

### Level 3 — Advanced

```java
import java.util.function.*;
import java.util.*;

public class BinaryOperatorMaxBy {
    record Student(String name, int score) {}

    public static void main(String[] args) {
        List<Student> students = List.of(
                new Student("Alice", 85),
                new Student("Bob", 92),
                new Student("Carol", 78)
        );

        // BinaryOperator.maxBy builds a BinaryOperator<Student> from a Comparator<Student> --
        // "given two students, return whichever has the higher score."
        BinaryOperator<Student> higherScore = BinaryOperator.maxBy(Comparator.comparingInt(Student::score));

        Optional<Student> topStudent = students.stream().reduce(higherScore);

        topStudent.ifPresent(student ->
                System.out.println("Top student: " + student.name() + " with score " + student.score()));
    }
}
```

**How to run:** `java BinaryOperatorMaxBy.java`

Expected output:
```
Top student: Bob with score 92
```

`BinaryOperator.maxBy(comparator)` builds a `BinaryOperator<Student>` from a `Comparator<Student>`: given any two `Student`s, it returns whichever one the comparator ranks higher. `stream().reduce(higherScore)` (the overload with no identity value, returning `Optional<T>`) then repeatedly applies this `BinaryOperator` to whittle the whole stream down to a single "winner" — exactly the same reduction shape `BinaryOperatorReduce` used for summing, but combining by "pick the bigger one" instead of "add them together."

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `students` holds three `Student` records: Alice (85), Bob (92), Carol (78). `higherScore` is built from `BinaryOperator.maxBy(Comparator.comparingInt(Student::score))` — a `BinaryOperator<Student>` that, given two students, returns whichever has the higher `score()`.

`students.stream().reduce(higherScore)` processes the stream by repeatedly combining pairs, left to right, using `higherScore`. With three elements, `reduce` (no-identity form) effectively computes `higherScore.apply(higherScore.apply(Alice, Bob), Carol)`.

First, `higherScore.apply(Alice, Bob)` compares their scores: `85` versus `92`. Since Bob's score is higher, `higherScore` returns `Bob`. This intermediate result, `Bob`, becomes the running accumulated value.

Next, `higherScore.apply(Bob, Carol)` compares `92` versus `78`. Since Bob's score is still higher, `higherScore` returns `Bob` again.

```
apply(Alice(85), Bob(92))  --> 85 < 92 --> Bob wins
apply(Bob(92), Carol(78))  --> 92 > 78 --> Bob wins again
```

With no more elements left to combine, `reduce` wraps the final result, `Bob`, in an `Optional<Student>` (the no-identity `reduce` overload returns empty only if the stream itself was empty — here it isn't, so the `Optional` is present). `topStudent.ifPresent(...)` runs its `Consumer` lambda since the `Optional` holds a value, printing `"Top student: Bob with score 92"`.

## 7. Gotchas & takeaways

> `UnaryOperator<T>` and `BinaryOperator<T>` are purely type-signature specializations — they add no new methods beyond what `Function`/`BiFunction` already provide (aside from `BinaryOperator`'s two `static` factories, `minBy`/`maxBy`). Don't expect any behavioral difference from using one over the general form; the only benefit is that the type itself documents "same type in, same type out," which the compiler can then also enforce at call sites like `List.replaceAll`.

- `UnaryOperator<T>` is `Function<T, T>` with a name that documents the same-type constraint; `BinaryOperator<T>` is `BiFunction<T, T, T>` likewise.
- `List.replaceAll(UnaryOperator<E>)` is a common place `UnaryOperator` appears, replacing every element in place with a transformed version of the same type.
- `Stream.reduce` is the classic home for `BinaryOperator<T>` — combining a stream's elements pairwise into a single final value of the same type, whether by summing, finding a max/min, or any other same-type combination.
- `BinaryOperator.minBy(Comparator<T>)` and `BinaryOperator.maxBy(Comparator<T>)` are convenient `static` factories for building a "pick the smaller/larger" `BinaryOperator` directly from an existing `Comparator`, without writing the comparison logic by hand.
- Reach for these narrower interfaces over the general `Function`/`BiFunction` whenever the same-type constraint genuinely applies — it's a small but meaningful readability signal to anyone reading the type signature later.
