---
card: java
gi: 274
slug: wrapper-classes-integer-long-double-boolean-character-etc
title: Wrapper classes (Integer, Long, Double, Boolean, Character, etc.)
---

## 1. What it is

Every primitive type in Java has a corresponding wrapper class: `int` has `Integer`, `long` has `Long`, `double` has `Double`, `boolean` has `Boolean`, `char` has `Character`, and so on for `byte`, `short`, and `float`. A wrapper class holds a primitive value inside an actual object, giving it everything a primitive lacks: the ability to be `null`, to be stored in generic collections (which only accept reference types), and access to useful static utility methods.

```java
public class WrapperDemo {
    public static void main(String[] args) {
        int primitive = 42;
        Integer wrapped = 42; // autoboxing: primitive int automatically wrapped into an Integer object

        System.out.println(wrapped.intValue());       // 42 — unwrap back to a primitive
        System.out.println(Integer.MAX_VALUE);          // 2147483647 — a static constant on the wrapper class
        System.out.println(Integer.toBinaryString(42)); // "101010" — a static utility method

        Integer nullable = null; // only possible with the WRAPPER class, never with a plain int
        System.out.println(nullable);
    }
}
```

`wrapped` holds the value `42` inside an actual `Integer` object (not just a raw primitive slot in memory), giving it access to instance methods like `intValue()` and letting the variable itself potentially be `null` — something a plain `int` variable could never be, since a primitive always has some concrete numeric value.

## 2. Why & when

Wrapper classes exist to bridge the gap between Java's primitive types (fast, memory-efficient, but limited) and its fully object-oriented type system (generics, collections, and anything requiring a reference type).

- **Enabling primitives in generic collections** — `List<int>` is not valid Java syntax; generics work only with reference types, so `List<Integer>` is used instead, with each `int` value automatically wrapped into an `Integer` object to be stored.
- **Representing "no value" with `null`** — a primitive `int` field defaults to `0` and can never distinguish "the value is zero" from "no value was ever provided"; an `Integer` field can be `null`, explicitly representing the absence of a value, which matters for things like optional configuration values or database columns that can be `NULL`.
- **Useful static utility methods and constants** — wrapper classes provide parsing methods (`Integer.parseInt`, covered in the next topic), formatting methods (`Integer.toBinaryString`, `Integer.toHexString`), comparison utilities (`Integer.compare`), and named constants (`Integer.MAX_VALUE`, `Integer.MIN_VALUE`) that a bare primitive type has no way to offer, since primitives aren't objects and can't have methods called on them directly.

Use plain primitives for ordinary local variables, loop counters, and calculations where performance matters and `null` is never a meaningful value; reach for wrapper classes specifically when you need to store values in generic collections, need to represent "no value" with `null`, or need one of the many useful static methods and constants each wrapper class provides.

## 3. Core concept

```java
public class WrapperCore {
    public static void main(String[] args) {
        Integer a = 100;
        Integer b = 100;
        Integer c = 200;
        Integer d = 200;

        System.out.println(a == b); // true — small Integer values are cached and shared
        System.out.println(c == d); // false — larger values are NOT cached, these are distinct objects
        System.out.println(c.equals(d)); // true — equals() correctly compares VALUE, regardless of caching
    }
}
```

Java caches `Integer` objects for small values (by default, `-128` to `127`), so `a == b` is `true` purely because both reference the *same* cached object; `c` and `d` fall outside that cached range, so they are genuinely distinct objects, making `c == d` `false` — but `c.equals(d)` correctly returns `true` in both cases, since `equals()` compares the actual wrapped value, not object identity, which is exactly why `equals()`, not `==`, should always be used to compare wrapper objects for value equality.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Small Integer values within the cached range share the same object so double equals works by coincidence, larger values outside the cache are distinct objects, equals always correctly compares the actual wrapped value">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="240" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Integer a=100, b=100</text>
  <text x="160" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cached range -- SAME object -- a==b true</text>

  <rect x="330" y="20" width="240" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="450" y="40" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">Integer c=200, d=200</text>
  <text x="450" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">outside cache -- DIFFERENT objects -- c==d false</text>

  <rect x="160" y="100" width="280" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="300" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">c.equals(d) -&gt; true, always correct</text>

  <text x="300" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Never rely on == for wrapper value comparison — always use equals().</text>
</svg>

Small `Integer` values are cached (sharing objects); larger ones are not — `equals()`, not `==`, is always the correct comparison.

## 5. Runnable example

Scenario: a small statistics utility working with wrapped numeric data, evolved from basic wrapper usage into a demonstration of the caching pitfall, then hardened with proper `equals()`-based comparisons throughout.

### Level 1 — Basic

```java
import java.util.List;

public class WrapperBasic {
    public static void main(String[] args) {
        List<Integer> scores = List.of(85, 92, 78); // int values autoboxed into Integer objects
        int total = 0;
        for (Integer score : scores) {
            total += score; // auto-unboxed back to int for the addition
        }
        System.out.println("Total: " + total);
        System.out.println("Average: " + (total / scores.size()));
    }
}
```

**How to run:** `java WrapperBasic.java`

`List<Integer>` requires wrapper objects, since generics cannot hold primitives directly — each literal `85`, `92`, `78` is automatically autoboxed into an `Integer` when the list is built, and automatically unboxed back into an `int` inside the loop for the arithmetic.

### Level 2 — Intermediate

Same statistics idea, now demonstrating the `Integer` caching behaviour directly, and why comparing wrapper objects with `==` instead of `equals()` is a real, documented pitfall.

```java
import java.util.List;

public class WrapperIntermediate {
    public static void main(String[] args) {
        List<Integer> smallScores = List.of(50, 50);   // both within the cached range (-128 to 127)
        List<Integer> largeScores = List.of(1000, 1000); // both OUTSIDE the cached range

        Integer a = smallScores.get(0);
        Integer b = smallScores.get(1);
        System.out.println("Small values, == comparison: " + (a == b)); // true, by caching coincidence

        Integer c = largeScores.get(0);
        Integer d = largeScores.get(1);
        System.out.println("Large values, == comparison: " + (c == d)); // false! same numeric value, different objects

        System.out.println("Large values, equals() comparison: " + c.equals(d)); // true — always correct
    }
}
```

**How to run:** `java WrapperIntermediate.java`

`c == d` is `false` even though both hold the numeric value `1000`, because `1000` falls outside the default `Integer` cache range, so `List.of(1000, 1000)` produces two genuinely separate `Integer` objects — this exact kind of bug (code that happens to work for small test values but breaks for larger ones) is why `==` should never be used to compare wrapper objects for value equality.

### Level 3 — Advanced

Same statistics system, now handling optional (possibly missing) scores using `null` wrapper values — something impossible with plain primitives — and demonstrating the correct, safe pattern for comparing and unboxing nullable wrapper values without risking `NullPointerException`.

```java
import java.util.Arrays;
import java.util.List;
import java.util.Objects;

public class WrapperAdvanced {
    static double computeAverage(List<Integer> scores) {
        int sum = 0;
        int count = 0;
        for (Integer score : scores) {
            if (score != null) { // explicit null check -- required, since Integer CAN be null
                sum += score;      // safe: score is confirmed non-null here, auto-unboxes fine
                count++;
            }
        }
        if (count == 0) throw new IllegalStateException("no valid scores to average");
        return (double) sum / count;
    }

    public static void main(String[] args) {
        List<Integer> scores = Arrays.asList(85, null, 92, null, 78); // null represents a MISSING score

        System.out.println("Average of valid scores: " + computeAverage(scores));

        // Demonstrating safe equals()-based comparison, even with a possibly-null value
        Integer maybeNull = scores.get(1); // this is null
        System.out.println("Is missing score equal to 85? " + Objects.equals(maybeNull, 85)); // false, no NPE
    }
}
```

**How to run:** `java WrapperAdvanced.java`

`Arrays.asList(85, null, 92, null, 78)` is only possible because `Integer` (unlike `int`) can hold `null`, representing genuinely missing data; `computeAverage` explicitly checks `score != null` before unboxing (attempting `sum += score` on a `null` `Integer` would throw `NullPointerException` during auto-unboxing), and `Objects.equals(maybeNull, 85)` safely compares a potentially-`null` wrapper against a value without risking an NPE, unlike calling `maybeNull.equals(85)` directly, which would throw if `maybeNull` were `null`.

## 6. Walkthrough

Trace `main` in `WrapperAdvanced` from the list construction through the final comparison.

**`Arrays.asList(85, null, 92, null, 78)`.** Builds a `List<Integer>` with five elements: `85`, `null`, `92`, `null`, `78` — each non-null integer literal is autoboxed into an `Integer` object; the `null` entries remain genuinely `null` references, representing missing data points.

**`computeAverage(scores)`.** `sum` and `count` both start at `0`. The loop iterates over all five elements: for `85`, `score != null` is `true`, so `sum += 85` (auto-unboxing `85` safely, since it's confirmed non-null) makes `sum = 85`, `count = 1`. For `null` (second element), `score != null` is `false`, so the block is skipped entirely — no attempt is made to unbox it, avoiding a `NullPointerException`. For `92`, `sum = 85 + 92 = 177`, `count = 2`. For `null` (fourth element), skipped again. For `78`, `sum = 177 + 78 = 255`, `count = 3`. After the loop, `count == 0` is `false` (it's `3`), so no exception is thrown. Returns `(double) 255 / 3 = 85.0`.

**`main` prints the average.** `"Average of valid scores: 85.0"`.

**`Integer maybeNull = scores.get(1)`.** Retrieves the second element, which is `null`. `maybeNull` is now `null`.

**`Objects.equals(maybeNull, 85)`.** `Objects.equals` is specifically designed to handle `null` safely: it checks if both arguments are `null` (they're not — `85` is autoboxed to a non-null `Integer`), then if either is `null` alone (here, `maybeNull` is `null` and the second argument isn't), it returns `false` immediately, without ever calling `.equals()` on the `null` reference itself (which would otherwise throw `NullPointerException` if you had instead written `maybeNull.equals(85)` directly). Prints `"Is missing score equal to 85? false"`.

```
scores = [85, null, 92, null, 78]

computeAverage:
  85:   not null -> sum=85, count=1
  null: skipped (null check prevents NPE on unboxing)
  92:   not null -> sum=177, count=2
  null: skipped
  78:   not null -> sum=255, count=3
  count!=0 -> return 255/3 = 85.0

maybeNull = scores.get(1) = null
Objects.equals(null, 85) -> handles null safely -> false (no NPE)
```

**Final output.**
```
Average of valid scores: 85.0
Is missing score equal to 85? false
```

## 7. Gotchas & takeaways

> **`Integer` (and other wrapper classes) cache and share objects for small values (by default, `-128` to `127` for `Integer`), making `==` comparisons appear to work correctly by coincidence for small test values, but fail for larger ones** — as `WrapperIntermediate` demonstrated concretely, this is a well-known, real-world bug pattern: code tested only with small numbers can pass, then break in production with larger values. Always use `.equals()` (or `Objects.equals()` for potentially-`null` values) to compare wrapper objects for value equality, never `==`.

> **Auto-unboxing a `null` wrapper object throws `NullPointerException`** — any operation that implicitly converts a wrapper back to its primitive form (arithmetic, comparisons using primitive operators, passing it where a primitive is expected) will throw if the wrapper reference is `null`; always explicitly check for `null` before performing such an operation on a wrapper value that might legitimately be missing, exactly as `computeAverage`'s `if (score != null)` guard does.

- Every primitive type has a corresponding wrapper class (`int`/`Integer`, `long`/`Long`, `double`/`Double`, `boolean`/`Boolean`, `char`/`Character`, and more), enabling use in generics, `null` representation, and access to useful static utilities.
- Small wrapper values are cached and shared by the JVM, making `==` comparisons unreliable for wrapper objects — always use `.equals()` for value comparison instead.
- A `null` wrapper reference represents a genuinely missing value, something no primitive can express — but attempting to auto-unbox a `null` wrapper throws `NullPointerException`, so explicit `null` checks are required before using a potentially-null wrapper in a primitive context.
- `Objects.equals(a, b)` safely compares two potentially-`null` values without risking a `NullPointerException`, unlike calling `.equals()` directly on a reference that might be `null`.
