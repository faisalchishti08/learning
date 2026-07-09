---
card: java
gi: 734
slug: pattern-matching-for-switch-4th-preview
title: Pattern matching for switch (4th preview)
---

## 1. What it is

**Java 20** (JEP 433) is the **fourth preview** of pattern matching for `switch`, continuing directly from the [third preview in Java 19](0728-pattern-matching-for-switch-3rd-preview.md). The type patterns, `case null`, `when` guards, and combination with record patterns all carry forward. The headline refinement in this round is stricter, clearer **exhaustiveness checking** for `switch` expressions over `sealed` type hierarchies involving generics, plus continued grammar polishing around record patterns nested inside `switch` cases. Like every round before it, this remains a preview feature requiring `--enable-preview`, and continued to be refined based on feedback before final standardization.

## 2. Why & when

Exhaustiveness — the compiler's ability to prove a `switch` expression handles every possible input without needing a `default` branch — is one of pattern-matching `switch`'s most valuable guarantees, but it gets genuinely harder to verify correctly once generics and nested record patterns are combined. Consider a `sealed interface Box<T> permits Full, Empty` used with record patterns: the compiler must reason not just about which subtypes exist, but about which *type parameter instantiations* combined with which *nested destructuring patterns* actually cover every case, without either wrongly rejecting a `switch` that genuinely is exhaustive (forcing developers to add a needless, dead `default` branch) or wrongly accepting one that secretly isn't (a real correctness gap). Each preview round refined this checking based on real cases the community found where the compiler's exhaustiveness analysis was too conservative or, occasionally, subtly wrong. This round's improvements matter specifically to code combining `sealed` generic hierarchies with nested record-pattern `switch` expressions — exactly the kind of code that benefits most from provable exhaustiveness, since it's also the kind of code where manually verifying "did I handle every case?" by eye is hardest.

## 3. Core concept

```java
sealed interface Result<T> permits Success, Failure {}
record Success<T>(T value) implements Result<T> {}
record Failure<T>(String error) implements Result<T> {}

// Exhaustive without a default — the compiler proves every Result<T> case,
// across both sealed permits AND the generic type parameter, is covered.
static <T> String describe(Result<T> result) {
    return switch (result) {
        case Success<T>(var value) -> "ok: " + value;
        case Failure<T>(var error) -> "error: " + error;
    };
}
```

The fourth preview refined exactly this kind of generic-plus-sealed-plus-record-pattern exhaustiveness check to work reliably.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Exhaustiveness checking for a generic sealed interface must verify every permitted subtype is covered by a case, regardless of the type parameter instantiation, before the compiler allows omitting a default branch">
  <rect x="200" y="20" width="240" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">sealed interface Result&lt;T&gt;</text>

  <line x1="270" y1="70" x2="150" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a11)"/>
  <line x1="370" y1="70" x2="490" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a11)"/>

  <rect x="40" y="110" width="220" height="50" rx="8" fill="#0f1620" stroke="#3fb950"/>
  <text x="150" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">case Success&lt;T&gt;(var v) -&gt; ...</text>

  <rect x="380" y="110" width="220" height="50" rx="8" fill="#0f1620" stroke="#3fb950"/>
  <text x="490" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">case Failure&lt;T&gt;(var e) -&gt; ...</text>

  <text x="320" y="185" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">both cases covered for EVERY T -&gt; no default needed</text>

  <defs><marker id="a11" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

The compiler verifies coverage across both the sealed hierarchy's permitted subtypes and the generic parameter, together.

## 5. Runnable example

Scenario: a generic `Result<T>` type representing success or failure, used to model a small validation pipeline. It grows from a basic exhaustive switch over `Result<T>`, to a version nesting record patterns to unwrap validated values with guards for specific error categories, to a generic pipeline processing a list of heterogeneous `Result<T>` values and aggregating outcomes — exercising exhaustiveness checking against real generic, nested, guarded patterns.

### Level 1 — Basic

```java
// File: ResultSwitchBasic.java
// Run with --enable-preview: pattern matching for switch is a 4th preview
// feature in Java 20.
public class ResultSwitchBasic {
    sealed interface Result<T> permits Success, Failure {}
    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}

    static <T> String describe(Result<T> result) {
        return switch (result) {
            case Success<T>(var value) -> "ok: " + value;
            case Failure<T>(var error) -> "error: " + error;
        };
    }

    public static void main(String[] args) {
        Result<Integer> ok = new Success<>(42);
        Result<Integer> bad = new Failure<>("not found");

        System.out.println(describe(ok));
        System.out.println(describe(bad));
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview ResultSwitchBasic.java
java --enable-preview ResultSwitchBasic
```

Expected output:
```
ok: 42
error: not found
```

### Level 2 — Intermediate

```java
// File: ResultSwitchGuardedIntermediate.java
// Adds guarded cases classifying specific error categories and validating
// success values, combining record patterns with `when` guards on a
// generic sealed hierarchy.
public class ResultSwitchGuardedIntermediate {
    sealed interface Result<T> permits Success, Failure {}
    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}

    static String classify(Result<Integer> result) {
        return switch (result) {
            case Success<Integer>(var value) when value < 0 -> "invalid: negative value " + value;
            case Success<Integer>(var value) when value > 1000 -> "invalid: value too large " + value;
            case Success<Integer>(var value) -> "valid: " + value;
            case Failure<Integer>(var error) when error.contains("timeout") -> "retryable error: " + error;
            case Failure<Integer>(var error) -> "fatal error: " + error;
        };
    }

    public static void main(String[] args) {
        System.out.println(classify(new Success<>(50)));
        System.out.println(classify(new Success<>(-5)));
        System.out.println(classify(new Success<>(5000)));
        System.out.println(classify(new Failure<>("connection timeout")));
        System.out.println(classify(new Failure<>("permission denied")));
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview ResultSwitchGuardedIntermediate.java
java --enable-preview ResultSwitchGuardedIntermediate
```

Expected output:
```
valid: 50
invalid: negative value -5
invalid: value too large 5000
retryable error: connection timeout
fatal error: permission denied
```

### Level 3 — Advanced

```java
// File: ResultPipelineAdvanced.java
// Processes a batch of generic Results, aggregating outcomes and separating
// retryable from fatal failures — the production-flavored shape of a
// validation/ingestion pipeline report, exercising exhaustiveness over a
// generic sealed hierarchy across many values.
import java.util.List;

public class ResultPipelineAdvanced {
    sealed interface Result<T> permits Success, Failure {}
    record Success<T>(T value) implements Result<T> {}
    record Failure<T>(String error) implements Result<T> {}

    record Report(int valid, int invalid, int retryable, int fatal) {}

    static Report process(List<Result<Integer>> results) {
        int valid = 0, invalid = 0, retryable = 0, fatal = 0;

        for (Result<Integer> result : results) {
            String outcome = switch (result) {
                case Success<Integer>(var v) when v >= 0 && v <= 1000 -> "valid";
                case Success<Integer> s -> "invalid";
                case Failure<Integer>(var error) when error.contains("timeout") -> "retryable";
                case Failure<Integer> f -> "fatal";
            };
            switch (outcome) {
                case "valid" -> valid++;
                case "invalid" -> invalid++;
                case "retryable" -> retryable++;
                case "fatal" -> fatal++;
            }
        }
        return new Report(valid, invalid, retryable, fatal);
    }

    public static void main(String[] args) {
        List<Result<Integer>> batch = List.of(
                new Success<>(10),
                new Success<>(-1),
                new Failure<>("read timeout"),
                new Failure<>("access denied"),
                new Success<>(999),
                new Failure<>("timeout while connecting"));

        Report report = process(batch);
        System.out.println("valid=" + report.valid() + " invalid=" + report.invalid()
                + " retryable=" + report.retryable() + " fatal=" + report.fatal());
    }
}
```

**How to run:**
```
javac --release 20 --enable-preview ResultPipelineAdvanced.java
java --enable-preview ResultPipelineAdvanced
```

Expected output:
```
valid=2 invalid=1 retryable=2 fatal=1
```

## 6. Walkthrough

1. `ResultPipelineAdvanced.main` builds a batch of six `Result<Integer>` values, a deliberate mix of valid successes, an out-of-range success, and failures with different error message content, then passes the whole batch to `process`.
2. `process` iterates the list, and for each element evaluates the inner `switch (result)` expression. Because `Result<T>` is `sealed` with exactly two permitted subtypes (`Success<T>`, `Failure<T>`), and every case in the `switch` is a record pattern over one of those two types with a guard, the compiler must verify — following this fourth preview's refined exhaustiveness rules — that between `Success<Integer>(var v) when v >= 0 && v <= 1000` and the unguarded `Success<Integer> s`, every possible `Success<Integer>` value is covered (the guarded case handles the valid range, the unguarded fallback catches everything else), and likewise for the two `Failure<Integer>` cases. No `default` branch is needed or would even be reachable.
3. For the first element, `Success(10)`, the guard `v >= 0 && v <= 1000` is `true`, so `outcome = "valid"`.
4. For `Success(-1)`, the same guard is `false` (since `-1 < 0`), so control falls through to the unguarded `case Success<Integer> s -> "invalid"` — note this fallback case doesn't need to destructure the value at all, since the classification here doesn't depend on it, demonstrating that a record pattern's components can be bound with `var` only where actually needed, or the whole record can be matched with a plain type pattern (`s`) when no components are needed.
5. For `Failure("read timeout")`, the guard `error.contains("timeout")` is `true`, giving `outcome = "retryable"`; for `Failure("access denied")`, the same guard is `false`, falling through to `outcome = "fatal"`.
6. The outer per-element `switch (outcome)` — an ordinary string `switch`, unrelated to pattern matching — then increments the matching counter in the `Report`. After all six elements are processed, `valid=2` (from `10` and `999`), `invalid=1` (from `-1`), `retryable=2` (from `"read timeout"` and `"timeout while connecting"`), `fatal=1` (from `"access denied"`) — matching the printed report.
7. This is the core benefit this preview round's exhaustiveness refinements protect: if a future maintainer added a third subtype permitted by `Result<T>` (say, `Pending<T>`), every `switch` like the one in `process` would fail to compile until a case for `Pending<T>` was added — the compiler catches the gap immediately, rather than the new case silently falling through to unexpected behavior or an unhandled runtime exception.

```
process(batch)
   |
   for each Result<Integer> in batch:
        switch (result)
            Success(v) when 0<=v<=1000?  -> "valid"
            Success(_)  (fallback)       -> "invalid"
            Failure(e) when contains("timeout")? -> "retryable"
            Failure(_)  (fallback)       -> "fatal"
   |
   v
tally into Report(valid, invalid, retryable, fatal)
```

## 7. Gotchas & takeaways

> This is a **preview feature in Java 20** (fourth preview of switch pattern matching) — both `javac` (`--release 20 --enable-preview`) and `java` (`--enable-preview`) require the flag; the exhaustiveness-checking refinements specific to this round targeted generic `sealed` hierarchies combined with nested record patterns, and continued to be adjusted before final standardization.
- Exhaustiveness checking considers the **sealed hierarchy's permitted subtypes**, not the specific generic type argument used at any one call site — `describe(Result<Integer> result)` and a hypothetical `describe(Result<String> result)` both benefit from the same two-case exhaustiveness proof, since the check operates on `Result<T>`'s structure generically.
- A record pattern in a `switch` case doesn't have to destructure every component down to a leaf variable — `case Success<Integer> s` (Level 3) matches and binds the whole record as `s` without unpacking its value, which is perfectly valid and appropriate when the case's logic doesn't need the inner value.
- As with earlier switch pattern-matching previews, guarded cases are still evaluated top to bottom, and the compiler's exhaustiveness proof depends on every *possible* value eventually being covered by some case — reordering an unguarded fallback case to appear before its guarded sibling for the same type would make the guarded case unreachable dead code, which the compiler also detects and rejects.
- The practical value of provable exhaustiveness compounds over a codebase's lifetime: it converts "did I forget a case?" from a runtime bug hunted down after the fact into a compile-time error caught the moment a new case is introduced — this is precisely why the pattern-matching `switch` design invested four preview rounds specifically into getting this guarantee right before finalizing it.
