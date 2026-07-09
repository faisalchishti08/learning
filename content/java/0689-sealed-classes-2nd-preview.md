---
card: java
gi: 689
slug: sealed-classes-2nd-preview
title: Sealed classes (2nd preview)
---

## 1. What it is

**Sealed classes**, first previewed in Java 15, returned for a **second preview** in **Java 16** (JEP 397) with refinements based on feedback from the first round. The core syntax is unchanged: `sealed class Shape permits Circle, Square {}` restricts which classes may extend or implement `Shape`, and every permitted subtype must itself be `final`, `sealed`, or `non-sealed`. The second preview refined details around how sealed types interact with records (which are implicitly `final`, satisfying the permitted-subtype rule automatically) and clarified reflection APIs like `Class.getPermittedSubclasses()` for introspecting a sealed hierarchy at runtime.

## 2. Why & when

The first preview (Java 15) established the core mechanism; the second preview existed to validate that sealed types composed cleanly with the language's other closed-data-modeling feature, records, and to settle the exact reflection surface (`Class.isSealed()`, `Class.getPermittedSubclasses()`) that tools, frameworks, and serialization libraries would need to introspect a sealed hierarchy programmatically. This mattered because sealed types and records were designed to be used together constantly — a sealed interface whose permitted subtypes are all records is the idiomatic way to model a closed set of data variants in Java — so getting the interaction right across two preview rounds, rather than rushing standardization, reduced the risk of needing a breaking change later. Reach for sealed types (still requiring `--enable-preview` on Java 16) whenever modeling a fixed, closed set of alternatives — an AST node, a result type, a state-machine state — especially when each variant is naturally expressed as a record.

## 3. Core concept

```java
// Java 16 (2nd preview) — requires --enable-preview --release 16
sealed interface Result<T> permits Success, Failure {}
record Success<T>(T value) implements Result<T> {}
record Failure<T>(String error) implements Result<T> {}
```

Because `record` types are implicitly `final`, `Success` and `Failure` automatically satisfy sealed's requirement that every permitted subtype be `final`, `sealed`, or `non-sealed` — no extra modifier needed on the records themselves.

## 4. Diagram

<svg viewBox="0 0 600 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sealed Result interface permits exactly Success and Failure, both implemented as implicitly final records">
  <rect x="210" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">sealed Result&lt;T&gt;</text>
  <text x="300" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">permits Success, Failure</text>

  <line x1="260" y1="70" x2="150" y2="130" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="340" y1="70" x2="450" y2="130" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="70" y="130" width="160" height="50" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="150" y="150" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">record Success&lt;T&gt;</text>
  <text x="150" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implicitly final</text>

  <rect x="370" y="130" width="160" height="50" rx="6" fill="#161b22" stroke="#79c0ff"/>
  <text x="450" y="150" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">record Failure&lt;T&gt;</text>
  <text x="450" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implicitly final</text>
</svg>

Records automatically satisfy sealed's "must be final, sealed, or non-sealed" rule, making the two features a natural pair.

## 5. Runnable example

Scenario: a `Result<T>` type modeling success-or-failure — first the basic sealed-plus-record hierarchy with exhaustive handling, then adding a third variant to show the compiler-enforced update ripple, then using reflection (`Class.getPermittedSubclasses()`, refined in this second preview) to introspect the hierarchy at runtime.

### Level 1 — Basic

```java
// File: ResultBasic.java
// compile & run with: --enable-preview --release 16
public class ResultBasic {
    sealed interface Result<T> permits Success, Failure {}
    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}

    static <T> String describe(Result<T> result) {
        if (result instanceof Success<T> s) return "Success: " + s.value();
        if (result instanceof Failure<T> f) return "Failure: " + f.error();
        throw new IllegalStateException("unreachable: sealed to Success, Failure");
    }

    public static void main(String[] args) {
        Result<Integer> ok = new Success<>(42);
        Result<Integer> bad = new Failure<>("division by zero");

        System.out.println(describe(ok));
        System.out.println(describe(bad));
    }
}
```

**How to run:**
```
javac --enable-preview --release 16 ResultBasic.java
java --enable-preview ResultBasic
```

Expected output:
```
Success: 42
Failure: division by zero
```

### Level 2 — Intermediate

```java
// File: ResultWithPending.java
// compile & run with: --enable-preview --release 16
public class ResultWithPending {
    sealed interface Result<T> permits Success, Failure, Pending {}
    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}
    record Pending<T>() implements Result<T> {}

    static <T> String describe(Result<T> result) {
        if (result instanceof Success<T> s) return "Success: " + s.value();
        if (result instanceof Failure<T> f) return "Failure: " + f.error();
        if (result instanceof Pending<T>) return "Pending: no result yet";
        throw new IllegalStateException("unreachable: sealed to Success, Failure, Pending");
    }

    public static void main(String[] args) {
        Result<Integer> ok = new Success<>(42);
        Result<Integer> bad = new Failure<>("timeout");
        Result<Integer> waiting = new Pending<>();

        for (Result<Integer> r : new Result[]{ ok, bad, waiting }) {
            System.out.println(describe(r));
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 16 ResultWithPending.java
java --enable-preview ResultWithPending
```

Expected output:
```
Success: 42
Failure: timeout
Pending: no result yet
```

Adding `Pending` to `Result`'s `permits` list — a new record with no components at all, representing an in-flight, not-yet-resolved state — is the realistic evolution case sealing anticipates: the interface declaration change is small and explicit, and every exhaustive consumer (like `describe`) needs a matching update, which sealing surfaces clearly rather than letting a silently-unhandled case slip through.

### Level 3 — Advanced

```java
// File: SealedIntrospection.java
// compile & run with: --enable-preview --release 16
public class SealedIntrospection {
    sealed interface Result<T> permits Success, Failure, Pending {}
    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}
    record Pending<T>() implements Result<T> {}

    public static void main(String[] args) {
        Class<Result> resultClass = Result.class;

        System.out.println("Result.class.isSealed(): " + resultClass.isSealed());
        System.out.println("Permitted subclasses:");
        for (Class<?> permitted : resultClass.getPermittedSubclasses()) {
            System.out.println("  " + permitted.getSimpleName()
                    + " (final=" + java.lang.reflect.Modifier.isFinal(permitted.getModifiers()) + ")");
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 16 SealedIntrospection.java
java --enable-preview SealedIntrospection
```

Expected output:
```
Result.class.isSealed(): true
Permitted subclasses:
  Success (final=true)
  Failure (final=true)
  Pending (final=true)
```

Level 3 uses `Class.isSealed()` and `Class.getPermittedSubclasses()` — exactly the reflection APIs this second preview refined — to introspect `Result`'s hierarchy at runtime: confirming it's sealed, listing every permitted subclass, and verifying each is `final` (automatically true here since they're all records). This is the kind of introspection a serialization library or a framework generating exhaustive-switch-like dispatch code at runtime would rely on.

## 6. Walkthrough

1. `main` obtains `Result.class` (a raw `Class<Result>` reference, since generic type parameters aren't retained at the `Class`-object level) and calls `.isSealed()` — this returns `true` because `Result` was declared with the `sealed` modifier and a `permits` clause.
2. `.getPermittedSubclasses()` returns an array of `Class<?>` objects — one entry per name listed in `Result`'s `permits Success, Failure, Pending` clause — reflecting the interface's declared permitted-subtype list directly, without needing to scan the classpath or guess.
3. For each permitted `Class`, the loop prints its simple name (`Success`, `Failure`, `Pending`) and checks `Modifier.isFinal(permitted.getModifiers())` — since all three are declared as `record`s, and records are implicitly `final`, this check returns `true` for all of them without any of the three records needing an explicit `final` keyword.
4. This demonstrates concretely why records and sealed types compose so naturally: sealed's rule ("every permitted subtype must be `final`, `sealed`, or `non-sealed`") is satisfied automatically the moment you implement a sealed interface with records, since records already carry the required `final` modifier as part of their own definition — no extra ceremony needed to combine the two features.
5. In `ResultWithPending` (Level 2), the `describe` method's `instanceof` chain checks `Success`, then `Failure`, then `Pending` in turn — for `Pending<T>` (a record with **zero** components, `record Pending<T>() implements Result<T> {}`), the check `result instanceof Pending<T>` matches without needing to bind or use any component, since there are none; the method simply returns a fixed message once the type match succeeds.
6. Running `describe` across the three constructed instances (`ok`, `bad`, `waiting`) in Level 2 prints one line per instance, in the array's construction order, each reflecting which specific sealed variant it was and what data (or lack thereof) it carried.

```
Result<T> (sealed) ──permits──► Success<T> | Failure<T> | Pending<T>
                                   (all implicitly final, since all are records)
Class.isSealed() -> true
Class.getPermittedSubclasses() -> [Success, Failure, Pending]
```

## 7. Gotchas & takeaways

> Sealed classes were still a **preview feature in Java 16** (second preview, following Java 15's first) — `--enable-preview` was required on both `javac` and `java`, and the feature did not become permanent, standard syntax until Java 17. Reflection code written against this preview's `Class.isSealed()`/`getPermittedSubclasses()` should be re-verified against Java 17's finalized behavior before being relied upon in production.

- Records automatically satisfy sealed's "permitted subtype must be final/sealed/non-sealed" requirement, since records are always implicitly `final` — this is precisely the interaction this second preview round validated and refined.
- `Class.getPermittedSubclasses()` returns an empty array for a non-sealed class — always check `isSealed()` first, or be prepared for an empty (not null) array on ordinary classes.
- A `record` with zero components (like `Pending<T>()` here) is a perfectly valid, legitimate pattern for modeling a variant that carries no data — useful for states like "pending," "unknown," or "none" in a closed hierarchy.
- Sealed hierarchies whose permitted subtypes are all records are Java's closest built-in equivalent to what other languages call algebraic data types or tagged unions — a closed, exhaustively-checkable set of immutable data variants.
- As with the [first sealed-classes preview](0678-sealed-classes-preview.md), permitted subtypes generally must reside in the same module (or package, for the unnamed module) as the sealed type, unless all are declared together in one source file, in which case the `permits` clause can even be omitted entirely.
