---
card: java
gi: 392
slug: varargs-ambiguity-array-passing
title: Varargs & ambiguity / array passing
---

## 1. What it is

A varargs parameter (`Type... name`) is, underneath, compiled as an ordinary array parameter (`Type[] name`) — this is why you can call a varargs method either with a comma-separated list of individual values *or* by passing an already-built array directly, and both compile to the exact same method call. This duality creates two specific, well-known trouble spots: **overload ambiguity**, when multiple overloads could plausibly match a given varargs call, and **generic varargs warnings**, which surface because arrays and generics interact unsafely (recall [[cannot-create-generic-arrays]]).

## 2. Why & when

Because a varargs parameter really is an array parameter in disguise, passing a single array argument directly (`sum(new int[]{1,2,3})`) and passing multiple individual values (`sum(1, 2, 3)`) both compile to the same underlying call — the compiler decides, based on the argument's actual type, whether to wrap loose values into a new array or pass an existing array as-is. This is usually invisible and convenient, but it becomes a genuine trap the moment overload resolution has to choose between a varargs method and a non-varargs method that could also match — Java's rules always prefer a more specific, non-varargs overload when one applies, which can produce a call resolving to a method other than the one you expected.

The second trouble spot, generic varargs, comes from combining `T...` with a generic type parameter: since varargs are arrays underneath, and arrays and generics don't mix safely (see [[cannot-create-generic-arrays]]), declaring `<T> void method(T... args)` produces a "heap pollution" warning — the compiler is telling you that, in principle, unsafe things could happen to that array behind the scenes, even though many uses are perfectly safe in practice.

## 3. Core concept

```java
import java.util.List;

public class VarargsAmbiguityDemo {
    static void print(Object... items) { // varargs overload
        System.out.println("varargs version, count=" + items.length);
    }

    static void print(Object[] items) { // non-varargs, explicit array overload -- can coexist!
        System.out.println("explicit array version, count=" + items.length);
    }

    public static void main(String[] args) {
        print("a", "b"); // only the varargs version can match multiple loose arguments
        print(new Object[]{"a", "b"}); // AMBIGUOUS in theory, but Java prefers the non-varargs match here
    }
}
```

**How to run:** `java VarargsAmbiguityDemo.java`

`print("a", "b")` can only match the varargs overload, since there's no non-varargs overload accepting two separate `Object` arguments. `print(new Object[]{"a", "b"})` passes an actual array directly — Java's overload resolution specifically prefers the non-varargs `print(Object[])` overload whenever an argument already matches it exactly, so this call resolves to the *second* method, not the varargs one, even though both could technically accept it.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="passing loose comma-separated values only matches a varargs overload, but passing an already-built array can match either overload, with Java preferring the non-varargs, more specific match">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">print("a", "b")  -&gt;  only matches print(Object... items)  -- varargs</text>

  <text x="20" y="65" fill="#e6edf3" font-size="11">print(new Object[]{"a","b"})  -&gt;  matches BOTH overloads --</text>
  <rect x="330" y="50" width="130" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="395" y="70" fill="#f85149" font-size="9" text-anchor="middle">varargs (loses)</text>
  <rect x="470" y="50" width="150" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="545" y="70" fill="#6db33f" font-size="9" text-anchor="middle">non-varargs (wins)</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">Java's overload resolution always prefers the more specific, non-varargs match when both are applicable.</text>
</svg>

## 5. Runnable example

Scenario: a generic "first non-null" utility, evolved from a version producing an unchecked "heap pollution" warning typical of generic varargs, through understanding exactly why, to a version using `@SafeVarargs` correctly to document that the specific usage is genuinely safe.

### Level 1 — Basic

```java
public class FirstNonNullWarning {
    static <T> T firstNonNull(T... candidates) { // generic varargs -- triggers an unchecked warning
        for (T c : candidates) {
            if (c != null) return c;
        }
        return null;
    }

    public static void main(String[] args) {
        System.out.println(firstNonNull(null, null, "found it"));
    }
}
```

**How to run:** `javac FirstNonNullWarning.java` (note the "unchecked generic array creation" warning) then `java FirstNonNullWarning`

`T... candidates` compiles and runs correctly, but produces a compiler warning: `warning: [unchecked] Possible heap pollution from parameterized vararg type T` — because underneath, the compiler must create a `T[]` array (recall this is normally illegal, see [[cannot-create-generic-arrays]]), and it can only do so by creating an `Object[]` and treating it as `T[]`, which is inherently a little unsafe if misused elsewhere.

### Level 2 — Intermediate

```java
public class FirstNonNullUnsafeUsage {
    static <T> T[] toArray(T... items) { // returns the backing array directly -- this is the actual danger
        return items; // exposes the compiler's internal Object[]-as-T[] array to the caller
    }

    public static void main(String[] args) {
        Object[] leaked = toArray("a", "b", "c"); // works, but silently exposes an Object[] disguised as String[]
        leaked[0] = 42; // corrupts the array with a non-String value -- compiles fine, no warning here!

        String[] strings = toArray("x", "y"); // this line would throw ClassCastException in some cases
        System.out.println(strings[0]);
    }
}
```

**How to run:** `java FirstNonNullUnsafeUsage.java`

This demonstrates the actual danger the warning is about: `toArray` returns its own varargs array directly, and because that array is really an `Object[]` underneath erasure, treating it as `T[]` and handing it back to callers can let mismatched types slip in without any compile-time check catching it — exactly the kind of "heap pollution" the compiler's warning is trying to flag.

### Level 3 — Advanced

```java
import java.util.Arrays;
import java.util.List;

public class FirstNonNullSafeVarargs {
    @SafeVarargs // asserts: this method genuinely does NOT leak or misuse the varargs array
    static <T> T firstNonNull(T... candidates) {
        for (T c : candidates) { // only ever READS from the array -- never stores it, never returns it directly
            if (c != null) return c;
        }
        throw new IllegalArgumentException("All candidates were null");
    }

    public static void main(String[] args) {
        String result = firstNonNull(null, null, "found it");
        System.out.println("Result: " + result);

        List<String> names = firstNonNull(null, List.of("Alice", "Bob"), List.of("fallback"));
        System.out.println("Names: " + names);
    }
}
```

**How to run:** `javac FirstNonNullSafeVarargs.java` (no warning now) then `java FirstNonNullSafeVarargs`

`@SafeVarargs`, placed on `firstNonNull`, suppresses the unchecked warning — it is a promise from the method's author to callers and the compiler that this specific method never does anything unsafe with its varargs array (like `toArray` in Level 2 did): it only reads elements out of the array, never stores the array itself somewhere it could later be misused, and never returns the array directly. `@SafeVarargs` can only legally be applied to `static`, `final`, `private`, or constructor methods — ones that can't be overridden — since an override could break the safety promise the original method made.

## 6. Walkthrough

Execution starts in `main`. `firstNonNull(null, null, "found it")` is called with three loose `String` (or `null`) arguments. Because `firstNonNull` is varargs, the compiler collects these three values into a new array — here genuinely a `String[]` at the call site, since all three arguments are `String`-compatible, though internally treated through the erased `T[]` (really `Object[]`) mechanism.

Inside `firstNonNull`, the `for (T c : candidates)` loop iterates: first `c = null` (skip, since `c != null` is `false`), then `c = null` again (skip), then `c = "found it"` — `c != null` is `true`, so the method returns `"found it"` immediately, without reaching the `throw` statement. `main` prints `Result: found it`.

`firstNonNull(null, List.of("Alice", "Bob"), List.of("fallback"))` is called next, with `T` inferred as `List<String>` this time (a completely different type parameter binding than the previous call — generic methods can be called with different type arguments on each invocation). The compiler collects the three arguments (`null`, one `List`, another `List`) into an array. The loop skips the first `null`, then finds `List.of("Alice", "Bob")` is non-null, and returns it immediately.

`names` is assigned this returned `List<String>`, and `main` prints `Names: [Alice, Bob]`.

Because `firstNonNull` only ever reads elements from `candidates` via the for-each loop and never stores the array reference anywhere or returns it directly (unlike `toArray` in Level 2), the `@SafeVarargs` promise genuinely holds — there is no way for this method to leak an unsafely-typed array back to a caller.

Expected output:
```
Result: found it
Names: [Alice, Bob]
```

## 7. Gotchas & takeaways

> `@SafeVarargs` is a promise, not a proof — the compiler does not verify that a method annotated with it is actually safe; it simply trusts the annotation and suppresses the warning. Only apply it to a method you've personally confirmed never stores or returns its varargs array directly (only reads from it), and only to `static`, `final`, `private`, or constructor methods, since those can never be overridden in a way that would break the safety promise.

- A varargs parameter is an array parameter underneath — this lets it be called with either loose comma-separated values or an already-built array, but also means array-related generics limitations apply to it.
- When both a varargs and a non-varargs overload could match a call, Java's overload resolution always prefers the more specific, non-varargs match.
- Generic varargs (`T... args`) always produce an "unchecked generic array creation" warning, since the compiler must build a `T[]` internally, which erasure makes fundamentally unsafe in the general case (recall [[cannot-create-generic-arrays]]).
- The real danger generic varargs warnings are about: a method that stores its varargs array somewhere persistent, or returns it directly to a caller, can let mismatched-type values corrupt that array without any compile-time check catching it.
- `@SafeVarargs` suppresses the warning for methods that provably only read from their varargs array — never store or return it directly — and is restricted to `static`, `final`, `private` methods and constructors for exactly this reason.
