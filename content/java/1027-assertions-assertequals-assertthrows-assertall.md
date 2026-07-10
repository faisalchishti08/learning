---
card: java
gi: 1027
slug: assertions-assertequals-assertthrows-assertall
title: "Assertions (assertEquals, assertThrows, assertAll)"
---

## 1. What it is

JUnit 5's `Assertions` class provides the static methods that actually check whether a test passed or failed. `assertEquals(expected, actual)` checks that two values match, failing with a clear message showing both if they don't. `assertThrows(ExceptionType.class, () -> ...)` verifies that a specific block of code throws a specific exception type — the correct way to test that failure paths behave as designed. `assertAll(...)` groups several independent assertions together so that **all** of them run and report their failures, instead of a test method stopping at the very first failed assertion and hiding every other check that would have followed it.

## 2. Why & when

A test with several separate `assertEquals` calls in a row has a hidden weakness: the moment the *first* one fails, JUnit throws an `AssertionError` immediately, and every assertion after it in that method simply never runs — so a test failure report showing "assertion 1 failed" tells you nothing about whether assertions 2, 3, and 4 would have also failed, forcing a slow fix-one-rerun-see-the-next-failure cycle. `assertAll` groups related assertions so every one of them executes regardless of whether an earlier one failed, and the failure report lists *all* of the failures from that group in one shot. `assertThrows` exists because testing "this throws an exception" by wrapping code in a manual `try`/`catch` and manually failing if no exception was thrown is verbose and easy to get subtly wrong (forgetting to fail the test if the code *doesn't* throw).

Use plain `assertEquals`/`assertTrue`/`assertNotNull` for straightforward single checks. Reach for `assertAll` whenever a test checks several independent properties of the same result — several fields of a returned object, several elements of a returned list — so a single test run reveals every failing property at once. Reach for `assertThrows` whenever a test's whole purpose is verifying that invalid input or an invalid operation correctly triggers a specific exception, rather than silently succeeding or throwing the wrong kind of failure.

## 3. Core concept

```java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {

    @Test
    void divisionByZeroThrows() {
        Calculator calc = new Calculator();
        ArithmeticException ex = assertThrows(ArithmeticException.class, () -> calc.divide(10, 0));
        assertEquals("/ by zero", ex.getMessage());
    }

    @Test
    void divisionResultHasMultipleProperties() {
        Calculator calc = new Calculator();
        Fraction result = calc.divideAsFraction(7, 2);

        // assertAll: EVERY check below runs and reports, even if one fails
        assertAll("fraction result",
            () -> assertEquals(7, result.numerator()),
            () -> assertEquals(2, result.denominator()),
            () -> assertEquals(3.5, result.toDouble(), 0.0001)
        );
    }
}
record Fraction(int numerator, int denominator) {
    double toDouble() { return (double) numerator / denominator; }
}
class Calculator {
    int divide(int a, int b) { return a / b; }
    Fraction divideAsFraction(int a, int b) { return new Fraction(a, b); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three sequential assertEquals calls where the first failure stops the test immediately, versus assertAll running and reporting all three checks regardless of individual failures">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Sequential asserts: stops at first failure</text>
  <rect x="30" y="40" width="70" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="65" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check 1 ✓</text>
  <rect x="110" y="40" width="70" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check 2 ✗</text>
  <rect x="190" y="40" width="70" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="4"/>
  <text x="225" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">check 3 ?</text>
  <text x="145" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">test stops here -- check 3 never runs</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">assertAll: all run, all reported</text>
  <rect x="380" y="70" width="70" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="415" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check 1 ✓</text>
  <rect x="460" y="70" width="70" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="495" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check 2 ✗</text>
  <rect x="540" y="70" width="70" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="575" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check 3 ✗</text>
  <text x="480" y="120" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">BOTH failures reported together</text>
</svg>

Sequential assertions hide every failure after the first; `assertAll` surfaces every failure in the group at once.

## 5. Runnable example

Scenario: testing a calculator's division behavior, evolving from a single narrow assertion into a full suite using `assertThrows` and `assertAll` correctly.

### Level 1 — Basic

```java
// File: src/test/java/CalculatorBasicTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class CalculatorBasicTest {
    @Test
    void dividesTwoNumbers() {
        Calculator calc = new Calculator();
        assertEquals(5, calc.divide(10, 2));
    }
}

class Calculator {
    int divide(int a, int b) { return a / b; }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

This test covers the happy path only — there's no test at all confirming what happens for division by zero, and no test checking more than the single division result.

### Level 2 — Intermediate

```java
// File: src/test/java/CalculatorIntermediateTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CalculatorIntermediateTest {
    @Test
    void dividesTwoNumbers() {
        Calculator calc = new Calculator();
        assertEquals(5, calc.divide(10, 2));
    }

    @Test
    void divisionByZeroThrowsArithmeticException() {
        Calculator calc = new Calculator();
        ArithmeticException ex = assertThrows(ArithmeticException.class, () -> calc.divide(10, 0));
        assertEquals("/ by zero", ex.getMessage());
    }
}

class Calculator {
    int divide(int a, int b) { return a / b; }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: `assertThrows` verifies both that the exception type is correct (`ArithmeticException`) and — by capturing its return value — that the exception's message is exactly what's expected, in one readable, purpose-built assertion instead of a manual `try`/`catch`.

### Level 3 — Advanced

```java
// File: src/test/java/CalculatorAdvancedTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

record Fraction(int numerator, int denominator) {
    double toDouble() { return (double) numerator / denominator; }
}

class Calculator {
    int divide(int a, int b) { return a / b; }
    Fraction divideAsFraction(int a, int b) {
        if (b == 0) throw new ArithmeticException("/ by zero");
        return new Fraction(a, b);
    }
}

class CalculatorAdvancedTest {
    @Test
    void divisionByZeroThrowsArithmeticException() {
        Calculator calc = new Calculator();
        ArithmeticException ex = assertThrows(ArithmeticException.class, () -> calc.divideAsFraction(10, 0));
        assertEquals("/ by zero", ex.getMessage());
    }

    @Test
    void fractionResultHasCorrectNumeratorDenominatorAndValue() {
        Calculator calc = new Calculator();
        Fraction result = calc.divideAsFraction(7, 2);

        // assertAll: ALL three checks run and report, even if one of them fails --
        // essential when checking multiple independent properties of one result.
        assertAll("fraction result for 7/2",
            () -> assertEquals(7, result.numerator(), "numerator should be unchanged"),
            () -> assertEquals(2, result.denominator(), "denominator should be unchanged"),
            () -> assertEquals(3.5, result.toDouble(), 0.0001, "decimal value should be 3.5")
        );
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=CalculatorAdvancedTest`.

Expected output:
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

To see `assertAll`'s failure-reporting behavior directly, temporarily change the expected numerator to a wrong value (e.g. `assertEquals(99, result.numerator(), ...)`) and rerun — the failure report will show that specific assertion failed *while the other two in the same group still ran and are confirmed passing*, rather than the test simply stopping after the first check.

The production-flavored hard case: `divideAsFraction` now throws explicitly rather than relying on integer-division's implicit `ArithmeticException`, and its result is checked across three genuinely independent properties (numerator, denominator, decimal value) using `assertAll` so a single failing property never hides information about the other two.

## 6. Walkthrough

Tracing `fractionResultHasCorrectNumeratorDenominatorAndValue` in `CalculatorAdvancedTest`:

1. `calc.divideAsFraction(7, 2)` runs: `b == 0` is `false` (since `b` is `2`), so it skips the exception path and returns `new Fraction(7, 2)`.
2. `assertAll("fraction result for 7/2", executable1, executable2, executable3)` is called with three lambda "executables" and a group label.
3. Internally, `assertAll` invokes each of the three lambdas in turn, but wraps each invocation so that if one throws an `AssertionError` (meaning that particular assertion failed), the error is *collected* rather than immediately propagated — allowing the next lambda in the list to still run.
4. The first lambda, `() -> assertEquals(7, result.numerator(), ...)`, calls `result.numerator()`, which returns `7` — matching the expected `7`, so this assertion passes with no error collected.
5. The second lambda checks `result.denominator()` (`2`, matching), and the third checks `result.toDouble()` (`7.0 / 2.0 = 3.5`, matching `3.5` within the `0.0001` tolerance) — both pass as well.
6. Since all three collected zero failures, `assertAll` itself completes normally without throwing anything, and the test method as a whole passes. Had any of the three actually failed (say, `numerator()` unexpectedly returned `70`), `assertAll` would have thrown a single `AssertionError` combining the message from every failed assertion in the group — but crucially, all three lambdas would still have been *executed* first, so the failure report would show exactly which of the three properties were wrong, together, in one test run, rather than requiring three separate failing test runs to discover.

## 7. Gotchas & takeaways

> **Gotcha:** the lambdas passed to `assertAll` must be genuinely independent of each other's outcome — if the second assertion's *code* depends on a side effect that only happens if the first assertion's code ran successfully (rather than just checking an independent property of an already-computed result), a failure in the first could leave the object under test in a state that makes the second lambda's own assertion misleading, since `assertAll` still runs every lambda regardless of earlier failures.

- `assertEquals`, `assertTrue`, `assertNotNull`, and similar single-purpose assertions are the right choice for one straightforward check.
- `assertThrows(ExceptionType.class, executable)` is the correct, JUnit-idiomatic way to verify a specific exception type is thrown — it also returns the caught exception, letting you make further assertions about its message or state.
- `assertAll` groups several independent assertions so that all of them run and report their failures together, instead of a test stopping silently at the first failure and hiding the rest.
- Reach for `assertAll` specifically when checking multiple independent properties of the same result — several fields of an object, several elements of a collection.
- A descriptive message (either as `assertAll`'s first argument, or as the optional final argument to most single assertions) makes a failure report far easier to diagnose without needing to open the test source code first.
- See [JUnit 5 lifecycle](1026-junit-5-lifecycle-beforeeach-aftereach-beforeall-afterall.md) for how the setup surrounding these assertions is structured, and [parameterized tests](1028-parameterized-tests.md) for running the same assertions across many different inputs without duplicating the test method.
