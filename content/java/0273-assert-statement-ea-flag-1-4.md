---
card: java
gi: 273
slug: assert-statement-ea-flag-1-4
title: assert statement & -ea flag (1.4)
---

## 1. What it is

The `assert` statement, introduced in Java 1.4, checks that a boolean condition is true, and throws `AssertionError` if it is not. Critically, assertions are disabled by default at runtime — they only actually execute when the JVM is started with the `-ea` (enable assertions) flag; without it, every `assert` statement in the program is effectively skipped entirely, as if it were never there.

```java
public class AssertDemo {
    static int divide(int a, int b) {
        assert b != 0 : "divisor must not be zero"; // only checked if assertions are enabled
        return a / b;
    }

    public static void main(String[] args) {
        System.out.println(divide(10, 2)); // 5
        System.out.println(divide(10, 0)); // WITHOUT -ea: throws ArithmeticException (assert did nothing)
                                             // WITH -ea: throws AssertionError first, at the assert line
    }
}
```

Running `java AssertDemo` normally (without `-ea`) skips the `assert` statement entirely, so `divide(10, 0)` proceeds straight to `10 / 0`, throwing the ordinary `ArithmeticException`; running `java -ea AssertDemo` instead evaluates the assertion first, finds `b != 0` is `false`, and throws `AssertionError("divisor must not be zero")` immediately — a completely different exception, at a different point, purely because of the runtime flag.

## 2. Why & when

Assertions exist for verifying internal invariants and assumptions during development and testing — conditions that should always be true if the code is correct — without imposing the runtime cost of checking them in production, where they're typically disabled by default.

- **Documenting and verifying internal invariants** — an assertion states, in executable form, "at this point, this condition must hold if my code is correct"; unlike a comment, it's automatically checked whenever assertions are enabled, catching violated assumptions immediately during development or testing.
- **Zero cost in production by default** — because assertions are disabled unless `-ea` is explicitly passed, they add no runtime overhead to production deployments, which is precisely why they're appropriate for checks you want during development but don't want slowing down (or behaving differently in) a shipped application.
- **Never for validating external input** — since assertions can be silently disabled, they must never be used to validate anything genuinely important for correctness or security (like user input or method arguments from external callers) — if assertions are off, that validation would simply vanish; use ordinary exceptions (like `IllegalArgumentException`) for anything that must always be checked, regardless of runtime flags.

Use `assert` for internal sanity checks — verifying an invariant that should be impossible to violate if the rest of your code is correct (like "this private helper method's precondition, guaranteed by its only caller, definitely holds") — and never for validating anything coming from outside your own code's control, since that validation would then depend on a runtime flag most production deployments don't set.

## 3. Core concept

```java
public class AssertCore {
    static int factorial(int n) {
        assert n >= 0 : "factorial is undefined for negative numbers: " + n; // internal invariant check
        int result = 1;
        for (int i = 2; i <= n; i++) result *= i;

        assert result >= 1 : "factorial result should never be less than 1"; // a POST-condition check
        return result;
    }
}
```

Two assertions appear here: one checking a *precondition* (the input must be non-negative) and one checking a *post-condition* (the result should never be less than `1`) — both are internal sanity checks about the method's own correctness, not validation of untrusted external input, which is exactly the appropriate use case for `assert`.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without the minus ea flag assertions are entirely skipped at runtime, with the flag enabled a false assertion condition throws AssertionError immediately at that exact statement">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="230" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="155" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">java AssertDemo (no -ea)</text>
  <text x="155" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">assert statement SKIPPED entirely</text>

  <rect x="330" y="20" width="230" height="60" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="445" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">java -ea AssertDemo</text>
  <text x="445" y="60" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">condition checked, throws AssertionError if false</text>

  <text x="300" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same source code, completely different runtime behaviour, depending purely on the -ea flag.</text>
</svg>

The exact same `assert` statement is either entirely skipped or fully checked, depending solely on the `-ea` runtime flag.

## 5. Runnable example

Scenario: a small internal helper method verifying its own invariants with assertions, evolved from a single precondition check into a demonstration comparing behaviour with and without `-ea`, then hardened into a case showing why assertions are unsuitable for validating genuinely external input.

### Level 1 — Basic

```java
public class AssertBasic {
    static int square(int n) {
        assert n >= 0 : "expected non-negative input, got: " + n;
        return n * n;
    }

    public static void main(String[] args) {
        System.out.println(square(5));  // 25
        System.out.println(square(-3)); // 9 -- assertion (if enabled) would flag this as unexpected
    }
}
```

**How to run (assertions disabled, the default):** `java AssertBasic.java`
**How to run (assertions enabled):** `javac AssertBasic.java && java -ea AssertBasic`

Without `-ea`, both calls run normally, printing `25` and `9` — the assertion is entirely inert; with `-ea`, the second call throws `AssertionError: expected non-negative input, got: -3` at the `assert` line, before `n * n` is even computed.

### Level 2 — Intermediate

Same idea, now catching `AssertionError` explicitly to observe the difference directly within one program run — note that `AssertionError` extends `Error`, not `Exception` (as an earlier topic covered), so catching it is unusual but useful here purely for demonstration.

```java
public class AssertIntermediate {
    static int square(int n) {
        assert n >= 0 : "expected non-negative input, got: " + n;
        return n * n;
    }

    public static void main(String[] args) {
        try {
            System.out.println("Result: " + square(-3));
        } catch (AssertionError e) {
            System.out.println("Assertion failed (only visible with -ea): " + e.getMessage());
        }
    }
}
```

**How to run (assertions disabled):** `java AssertIntermediate.java` — prints `"Result: 9"`, since the assertion never ran.
**How to run (assertions enabled):** `javac AssertIntermediate.java && java -ea AssertIntermediate` — prints `"Assertion failed (only visible with -ea): expected non-negative input, got: -3"`, since the assertion threw before `square` could return normally.

This demonstrates directly, within one file, exactly how much runtime behaviour hinges on the `-ea` flag — the same source code produces genuinely different observable output depending purely on how the JVM was launched.

### Level 3 — Advanced

Same idea, now demonstrating the correct, important distinction: an internal invariant checked with `assert` (fine to disable in production) versus genuine input validation that must always run, using a real exception instead — showing why mixing these two up would be a serious mistake.

```java
public class AssertAdvanced {
    // GOOD internal invariant: an assumption this private helper's caller is expected to already guarantee
    private static int computeAverage(int[] validatedNonEmptyArray) {
        assert validatedNonEmptyArray.length > 0 : "internal contract violated: array should never be empty here";
        int sum = 0;
        for (int v : validatedNonEmptyArray) sum += v;
        return sum / validatedNonEmptyArray.length;
    }

    // Public entry point: genuine external input validation -- must ALWAYS run, assertions or not
    public static int publicAverage(int[] input) {
        if (input == null || input.length == 0) {
            throw new IllegalArgumentException("input must be a non-empty array"); // NOT an assert!
        }
        return computeAverage(input); // by the time we reach here, the invariant is truly guaranteed
    }

    public static void main(String[] args) {
        System.out.println("Average: " + publicAverage(new int[]{2, 4, 6}));

        try {
            publicAverage(new int[]{});
        } catch (IllegalArgumentException e) {
            System.out.println("Correctly rejected, regardless of -ea: " + e.getMessage());
        }
    }
}
```

**How to run (with or without `-ea` — behaves identically either way):** `java AssertAdvanced.java` or `java -ea AssertAdvanced`

`publicAverage` uses a genuine `IllegalArgumentException` to validate its externally-provided `input` parameter — this check runs *unconditionally*, regardless of the `-ea` flag, exactly as required for real input validation; `computeAverage`'s internal `assert`, by contrast, only ever double-checks an invariant that `publicAverage` has *already* guaranteed by the time it's called, so it's purely a development-time sanity check, safe to have disabled in production without affecting correctness at all.

## 6. Walkthrough

Trace `main` in `AssertAdvanced.main` under both possible `-ea` settings.

**`publicAverage(new int[]{2, 4, 6})`.** `input == null` is `false`; `input.length == 0` is `false` (length is `3`). The `IllegalArgumentException` guard does not fire. `computeAverage(new int[]{2, 4, 6})` runs: the `assert` checks `validatedNonEmptyArray.length > 0` — `3 > 0` is `true`, so (whether or not assertions are enabled) this holds and no `AssertionError` occurs either way. `sum` accumulates `2 + 4 + 6 = 12`. Returns `12 / 3 = 4`. Prints `"Average: 4"`.

**`publicAverage(new int[]{})`.** `input == null` is `false`, but `input.length == 0` is `true` (an empty array). `IllegalArgumentException("input must be a non-empty array")` is thrown immediately — `computeAverage` is never even called, so its internal `assert` is never reached at all. This happens identically whether or not `-ea` is set, since it's an ordinary exception, not an assertion. Caught by `main`'s `catch` clause. Prints `"Correctly rejected, regardless of -ea: input must be a non-empty array"`.

```
publicAverage([2,4,6]):
  null/empty check -> false -> proceeds
  computeAverage([2,4,6]): assert length>0 -> 3>0 true (holds regardless of -ea) -> sum=12 -> returns 4
  prints "Average: 4"

publicAverage([]):
  null/empty check -> true -> throws IllegalArgumentException (ALWAYS, -ea irrelevant here)
  computeAverage never even called
  caught -> prints "Correctly rejected, regardless of -ea: input must be a non-empty array"
```

**Final output (identical with or without `-ea`).**
```
Average: 4
Correctly rejected, regardless of -ea: input must be a non-empty array
```
This program's observable behaviour is completely unaffected by the `-ea` flag, which is exactly the point: the genuinely important validation uses a real exception that always runs, while the `assert` only ever double-checks a condition that was already guaranteed true by the time it's reached — so whether it's actually checked or silently skipped makes no difference to correct program behaviour.

## 7. Gotchas & takeaways

> **Assertions are disabled by default — running `java YourProgram` without `-ea` silently skips every `assert` statement in the entire program**, which means code relying on assertions for anything that actually matters for correctness will behave completely differently (and, for genuine bugs, far more dangerously) in a typical production deployment than during development or testing where `-ea` might be enabled. Never assume assertions are running unless you have explicitly confirmed the `-ea` flag is set.

> **Never use `assert` to validate external input, user data, or anything a method's caller (outside your own trusted code) provides** — since assertions can be silently disabled, any validation expressed only through `assert` effectively vanishes in a typical production run, potentially letting invalid data flow deep into the program undetected. Use ordinary exceptions (`IllegalArgumentException`, custom exceptions) for anything that must always be validated, and reserve `assert` strictly for internal invariants your own code should be able to guarantee are always true if it's implemented correctly.

- `assert condition : message;` throws `AssertionError(message)` if `condition` is `false`, but only when the JVM is launched with the `-ea` flag — without it, every assertion is silently skipped entirely.
- Use assertions for internal sanity checks and invariants your own code is responsible for guaranteeing, verified during development and testing at essentially zero cost in production.
- Never use assertions to validate external input or anything a caller outside your trusted code provides, since that validation could simply disappear if `-ea` isn't set.
- `AssertionError` extends `Error`, not `Exception`, reflecting that a failed assertion signals a genuine bug in the program's own logic, not a normal, expected failure condition.
