---
card: java
gi: 378
slug: suppresswarnings
title: '@SuppressWarnings'
---

## 1. What it is

`@SuppressWarnings("category")` is a built-in annotation that tells the compiler to hide specific categories of warning for the annotated element (a class, method, field, or local variable) and everything nested inside it. Common categories include `"unchecked"` (unsafe generic casts or conversions), `"deprecation"` (calls to `@Deprecated` code), and `"rawtypes"` (use of a raw generic type). It never changes what the code actually does — it only silences the compiler's warning output about it.

## 2. Why & when

Some warnings are genuinely unavoidable — type erasure sometimes forces an unchecked cast that's actually safe given the surrounding logic (see [[cannot-create-generic-arrays]]), or a small, deliberate piece of code needs to call a deprecated method during a migration (see [[deprecated]]). Left unsuppressed, these warnings clutter the build output, making it harder to spot *new*, unintentional warnings among the noise of ones the team has already reviewed and accepted.

`@SuppressWarnings` lets you acknowledge a specific warning at the smallest possible scope — ideally one method or even one local variable, not an entire class — with an implicit "we've reviewed this, it's safe" statement, while leaving every other warning in the codebase fully visible. This targeted acknowledgement is very different from disabling a whole category of warning project-wide (via a build tool flag), which would hide both the reviewed cases and any brand-new, unreviewed ones equally.

## 3. Core concept

```java
import java.util.List;
import java.util.ArrayList;

public class SuppressWarningsDemo {
    @SuppressWarnings("unchecked") // scoped to just this one method
    static <T> T[] toArrayUnsafe(List<T> list, T[] template) {
        return (T[]) list.toArray(); // unchecked cast -- but genuinely safe given the caller's contract
    }

    public static void main(String[] args) {
        List<String> names = new ArrayList<>(List.of("Alice", "Bob"));
        String[] array = toArrayUnsafe(names, new String[0]);
        System.out.println(array.length + " names: " + array[0] + ", " + array[1]);
    }
}
```

**How to run:** `java SuppressWarningsDemo.java`

`(T[]) list.toArray()` would normally trigger an "unchecked cast" compiler warning, since erasure means the compiler cannot actually verify the cast is safe at compile time. `@SuppressWarnings("unchecked")`, placed directly on `toArrayUnsafe`, silences just that warning for this one method — the rest of the file (and program) is unaffected, and any *other* unchecked warning elsewhere would still show up normally.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SuppressWarnings scoped to one method hides only that method's warnings, leaving warnings in the rest of the file fully visible">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="580" height="90" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="45" y="50" fill="#8b949e" font-size="10">class SuppressWarningsDemo {</text>

  <rect x="55" y="60" width="540" height="30" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="65" y="80" fill="#f85149" font-size="10">@SuppressWarnings("unchecked")  toArrayUnsafe(...) -- warning hidden here</text>

  <text x="45" y="105" fill="#6db33f" font-size="10">main(...) -- any warning HERE would still show normally</text>
</svg>

## 5. Runnable example

Scenario: a small generic cache backed by a raw array (recall [[cannot-create-generic-arrays]]), evolved from unsuppressed, noisy warnings, through scoping suppression tightly to just the unavoidable cast, to a version demonstrating why suppressing at too broad a scope is a real risk.

### Level 1 — Basic

```java
public class CacheNoisyWarnings {
    static class Cache<T> {
        private final Object[] slots; // backing array must be Object[], see cannot-create-generic-arrays

        Cache(int size) {
            slots = new Object[size];
        }

        void put(int index, T value) {
            slots[index] = value;
        }

        T get(int index) { // unchecked cast here -- compiler warns every time this file is built
            return (T) slots[index];
        }
    }

    public static void main(String[] args) {
        Cache<String> cache = new Cache<>(2);
        cache.put(0, "hello");
        System.out.println(cache.get(0));
    }
}
```

**How to run:** `javac CacheNoisyWarnings.java` (note the unchecked warning) then `java CacheNoisyWarnings`

`(T) slots[index]` is an unavoidable unchecked cast, given that arrays can't hold a generic type directly. Compiling prints `warning: [unchecked] unchecked cast` — accurate, but noisy if this pattern repeats across many similar generic classes in a real codebase, since every one of them will report the same unavoidable warning.

### Level 2 — Intermediate

```java
public class CacheScopedSuppression {
    static class Cache<T> {
        private final Object[] slots;

        Cache(int size) {
            slots = new Object[size];
        }

        void put(int index, T value) {
            slots[index] = value;
        }

        @SuppressWarnings("unchecked") // acknowledges exactly this one unavoidable cast
        T get(int index) {
            return (T) slots[index];
        }
    }

    public static void main(String[] args) {
        Cache<String> cache = new Cache<>(2);
        cache.put(0, "hello");
        System.out.println(cache.get(0));
    }
}
```

**How to run:** `javac CacheScopedSuppression.java` (no warning now) then `java CacheScopedSuppression`

Scoping `@SuppressWarnings("unchecked")` to just the `get` method acknowledges precisely this one unavoidable cast — compiling now produces no warning for this class at all, while any *other* unrelated unchecked-cast mistake elsewhere in a real codebase would still be reported normally, since suppression here doesn't extend beyond `get`'s body.

### Level 3 — Advanced

```java
public class CacheOverSuppressionRisk {
    @SuppressWarnings("unchecked") // BAD: suppresses for the WHOLE CLASS, not just one method
    static class Cache<T> {
        private final Object[] slots;

        Cache(int size) {
            slots = new Object[size];
        }

        void put(int index, T value) {
            slots[index] = value;
        }

        T get(int index) {
            return (T) slots[index]; // the intended, unavoidable cast
        }

        T getBuggyDoubled(int index) {
            // A genuinely NEW mistake introduced later: casting the wrong thing entirely.
            // Because @SuppressWarnings is on the whole class, THIS warning is also hidden!
            Object[] doubled = new Object[]{ slots[index], slots[index] };
            return (T) doubled; // clearly wrong -- doubled is an Object[], not a T -- but no warning shown
        }
    }

    public static void main(String[] args) {
        Cache<String> cache = new Cache<>(2);
        cache.put(0, "hello");
        System.out.println(cache.get(0));
        try {
            cache.getBuggyDoubled(0); // throws at runtime -- the hidden warning would have flagged this
        } catch (ClassCastException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac CacheOverSuppressionRisk.java` (no warnings at all, even for the real bug) then `java CacheOverSuppressionRisk`

Placing `@SuppressWarnings("unchecked")` on the whole `Cache` class, rather than just `get`, hides warnings for *every* method inside it — including `getBuggyDoubled`'s genuinely broken cast, a real bug that a correctly-scoped suppression would have let the compiler flag. This demonstrates the core risk: over-broad suppression scope can hide brand-new mistakes right alongside the one warning you actually meant to acknowledge.

## 6. Walkthrough

Execution starts in `main`. `cache.put(0, "hello")` stores `"hello"` at `slots[0]`. `cache.get(0)` returns `(T) slots[0]`, which is `"hello"` cast to `T` (erased to `String` here) — this cast genuinely succeeds because `slots[0]` really does hold a `String`, so `System.out.println` prints `hello` without issue.

`cache.getBuggyDoubled(0)` is called next, inside a `try` block. Inside the method, `doubled` is built as a new two-element `Object[]` array containing `slots[0]` twice. The line `return (T) doubled` attempts to cast this `Object[]` array itself (not one of its elements) to `T` — since `T` is erased to `String` at the call site in `main` (because `cache` is a `Cache<String>`), the actual runtime cast attempted is `(String) doubled`, and `doubled` is an `Object[]`, not a `String` at all.

Because the cast target (`T`, erased to `String`) is a real, checkable type at the point where the value is *used* as a `String` — here, implicitly when the return value would need to be treated as one — the JVM inserts a genuine runtime check. `doubled` is not a `String`, so this throws `ClassCastException` the moment the value is used in a context requiring a `String`. The `catch (ClassCastException e)` block in `main` catches it and prints `Caught: ` followed by the exception's message.

Crucially, if `@SuppressWarnings("unchecked")` had been scoped correctly (only on `get`, as in Level 2), the compiler would have flagged `getBuggyDoubled`'s cast with its own unchecked warning during compilation — a chance to catch this mistake *before* running the program at all. Because the suppression was placed on the whole class instead, that warning was silently hidden along with the one warning that was actually meant to be suppressed.

Expected output:
```
hello
Caught: class [Ljava.lang.Object; cannot be cast to class java.lang.String
```

## 7. Gotchas & takeaways

> Scope `@SuppressWarnings` as narrowly as possible — a single method, or even a single local variable declaration, never a whole class — unless you have specifically reviewed every warning that scope could ever produce, now and in the future. Broad suppression silently hides new mistakes alongside the one you meant to acknowledge.

- `@SuppressWarnings("category")` hides compiler warnings of that category for the annotated element and everything nested inside it; it never changes actual program behaviour.
- Common categories: `"unchecked"` (unsafe generic casts/conversions), `"deprecation"` (calls to `@Deprecated` code, see [[deprecated]]), `"rawtypes"` (use of a raw generic type, see [[raw-types-warnings]]).
- Always prefer the smallest possible scope for a suppression — one method, ideally one line — over suppressing at the class level, to avoid hiding unrelated future warnings.
- A suppression should come with an implicit (or explicit, in a comment) justification for why the warning doesn't indicate a real problem — suppression is an acknowledgement, not a way to avoid thinking about the warning.
- Warnings suppressed at too broad a scope can hide genuinely new bugs introduced later in the same scope — always re-narrow a suppression's scope if the surrounding code grows to include logic the original suppression wasn't meant to cover.
