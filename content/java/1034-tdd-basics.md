---
card: java
gi: 1034
slug: tdd-basics
title: TDD basics
---

## 1. What it is

**Test-Driven Development (TDD)** is a discipline for writing code in a tight, repeating cycle known as **red-green-refactor**: first write a test for behavior that doesn't exist yet (it fails — **red**, since the code to satisfy it isn't written), then write the smallest amount of production code needed to make that test pass (**green**), then clean up the code while keeping the test passing (**refactor**), and repeat for the next small piece of behavior. The test is written *before* the implementation, not after — this ordering is the entire point of the discipline, not an incidental detail.

## 2. Why & when

Writing tests after the implementation tends to produce tests that simply confirm whatever the code already does — including any bugs already baked into it — because the author's mental model is anchored to the code they just wrote, not to what the behavior is actually supposed to be. Writing the test first forces you to think about the desired *behavior* and its observable contract before any implementation exists to bias that thinking, and watching the test genuinely fail first (red) confirms the test is actually capable of catching a missing or wrong implementation — a test that passes even before any code exists to satisfy it is testing nothing at all. The tight cycle also keeps each step small: implement just enough to pass the current test, not more, which naturally avoids speculative, untested code paths.

TDD suits situations where the desired behavior can be described concretely and incrementally — a calculation, a validation rule, a data transformation — and works less naturally for exploratory work where the shape of the solution itself is still being discovered (in that case, prototype first, then retrofit tests once the design settles, rather than forcing TDD onto pure exploration). It's a discipline, not a mandate for every single line of code — use judgment about when the red-green-refactor cycle's overhead pays for itself.

## 3. Core concept

```java
// STEP 1 (RED): write the test FIRST, for behavior that doesn't exist yet.
// This test currently fails to even compile, since PriceCalculator doesn't exist.
@Test
void tenPercentDiscountAppliesToMemberPurchase() {
    PriceCalculator calc = new PriceCalculator();
    assertEquals(90.0, calc.finalPrice(100.0, true));
}

// STEP 2 (GREEN): write the SMALLEST implementation that makes the test pass.
class PriceCalculator {
    double finalPrice(double price, boolean isMember) {
        return isMember ? price * 0.90 : price; // just enough to satisfy the one test above
    }
}

// STEP 3 (REFACTOR): clean up, if needed, with the test still passing throughout.
// (Here the implementation is already simple -- nothing to refactor yet.)
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The red-green-refactor cycle: write a failing test, write minimal code to pass it, refactor while staying green, then repeat for the next behavior">
  <rect x="20" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="95" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RED: write failing test</text>

  <rect x="245" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">GREEN: minimal code</text>

  <rect x="470" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">REFACTOR: clean up</text>

  <line x1="170" y1="85" x2="245" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="395" y1="85" x2="470" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <path d="M 545 110 Q 320 160 95 110" stroke="#8b949e" fill="none" marker-end="url(#a)"/>
  <text x="320" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">repeat for the next small behavior</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each cycle is small: one failing test, the minimal code to pass it, then cleanup — repeated for the next piece of behavior.

## 5. Runnable example

Scenario: building a `PriceCalculator` from scratch using strict TDD, showing the actual red-green-refactor cycle across three increasingly complete iterations.

### Level 1 — Basic

```java
// File: src/test/java/PriceCalculatorTddTest.java
// STEP 1 (RED): this test is written FIRST. PriceCalculator does not exist yet,
// so this file will not even compile -- that failure to compile IS the "red" state.
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class PriceCalculatorTddTest {
    @Test
    void memberGetsTenPercentDiscount() {
        PriceCalculator calc = new PriceCalculator();
        assertEquals(90.0, calc.finalPrice(100.0, true));
    }
}
```

```java
// File: src/main/java/PriceCalculator.java
// STEP 2 (GREEN): the SMALLEST implementation satisfying the ONE test above --
// no non-member branch, no validation, nothing beyond what's actually required yet.
public class PriceCalculator {
    public double finalPrice(double price, boolean isMember) {
        return price * 0.90;
    }
}
```

**How to run:** create both files in a Maven project, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

Notice `finalPrice` doesn't even check `isMember` — it always applies the discount. This is the correct TDD discipline at this stage: the test only ever calls `finalPrice(100.0, true)`, so nothing yet demands handling the non-member case. Writing more than this would be speculative, untested code.

### Level 2 — Intermediate

```java
// File: src/test/java/PriceCalculatorTddTest.java
// STEP 1 (RED) again: a NEW test describing the next piece of behavior --
// this test WILL fail against the Level 1 implementation, which ignores isMember.
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class PriceCalculatorTddTest {
    @Test
    void memberGetsTenPercentDiscount() {
        PriceCalculator calc = new PriceCalculator();
        assertEquals(90.0, calc.finalPrice(100.0, true));
    }

    @Test
    void nonMemberPaysFullPrice() {
        PriceCalculator calc = new PriceCalculator();
        assertEquals(100.0, calc.finalPrice(100.0, false)); // FAILS against Level 1's code: returns 90.0, not 100.0
    }
}
```

```java
// File: src/main/java/PriceCalculator.java
// STEP 2 (GREEN) again: extend the implementation JUST enough to make BOTH
// tests pass -- adding the isMember branch the new test actually demands.
public class PriceCalculator {
    public double finalPrice(double price, boolean isMember) {
        return isMember ? price * 0.90 : price;
    }
}
```

**How to run:** run `mvn test`. If you run the tests against the Level 1 implementation first (to see red), `nonMemberPaysFullPrice` fails with `expected: <100.0> but was: <90.0>`; after updating to the Level 2 implementation shown, both pass.

Expected output (after the Level 2 implementation):
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: the second test was written first, confirmed to fail against the existing implementation (proving it actually tests something meaningful), and only then was the implementation extended — by the smallest change that makes both tests pass, not a larger rewrite anticipating requirements that haven't been demanded by a test yet.

### Level 3 — Advanced

```java
// File: src/test/java/PriceCalculatorTddTest.java
// STEP 1 (RED): a test for a genuinely new requirement -- negative prices
// should be rejected. This fails against the Level 2 implementation, which
// has no validation at all and would just compute a negative "discount."
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class PriceCalculatorTddTest {
    @Test
    void memberGetsTenPercentDiscount() {
        PriceCalculator calc = new PriceCalculator();
        assertEquals(90.0, calc.finalPrice(100.0, true));
    }

    @Test
    void nonMemberPaysFullPrice() {
        PriceCalculator calc = new PriceCalculator();
        assertEquals(100.0, calc.finalPrice(100.0, false));
    }

    @Test
    void negativePriceThrows() {
        PriceCalculator calc = new PriceCalculator();
        assertThrows(IllegalArgumentException.class, () -> calc.finalPrice(-10.0, true));
    }
}
```

```java
// File: src/main/java/PriceCalculator.java
// STEP 2 (GREEN): the smallest addition satisfying the new test -- a guard clause,
// nothing more elaborate than what's actually demanded.
// STEP 3 (REFACTOR): the ternary is extracted into a named, self-documenting
// method -- purely a readability cleanup, with all three tests still green
// throughout this change, confirming the refactor didn't alter behavior.
public class PriceCalculator {
    public double finalPrice(double price, boolean isMember) {
        if (price < 0) {
            throw new IllegalArgumentException("price cannot be negative");
        }
        return applyMembershipDiscount(price, isMember);
    }

    private double applyMembershipDiscount(double price, boolean isMember) {
        return isMember ? price * 0.90 : price;
    }
}
```

**How to run:** run `mvn test`.

Expected output:
```
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: the refactor step (extracting `applyMembershipDiscount`) happened *after* all three tests were green, and the tests themselves were never touched during the refactor — they're what gives confidence that extracting the method didn't silently change any behavior, which is the entire purpose of having the tests run again immediately after any refactor.

## 6. Walkthrough

Tracing the discipline across the three iterations shown:

1. Level 1 begins with `memberGetsTenPercentDiscount` written *before* `PriceCalculator` exists at all — attempting to compile this test alone fails (red), which is expected and correct: there's genuinely nothing yet to make it pass.
2. The minimal `PriceCalculator` from Level 1 is written specifically to make that one test pass — nothing more. Running `mvn test` at this point shows one passing test (green).
3. Level 2 adds `nonMemberPaysFullPrice`. Run against the Level 1 code, `calc.finalPrice(100.0, false)` returns `100.0 * 0.90 = 90.0` (since Level 1's implementation ignores `isMember` entirely), which doesn't match the expected `100.0` — this test genuinely fails (red), confirming it exercises real, currently-missing behavior.
4. The implementation is extended to `isMember ? price * 0.90 : price` — the smallest change that makes both the new test and the still-existing first test pass together. Running `mvn test` now shows both green.
5. Level 3 adds `negativePriceThrows`. Run against the Level 2 code, `calc.finalPrice(-10.0, true)` would simply compute `-10.0 * 0.90 = -9.0` and return it normally, with no exception thrown at all — `assertThrows` fails because no exception occurred (red), confirming a genuine, currently-missing validation requirement.
6. A guard clause is added (`if (price < 0) throw ...`), making all three tests pass (green). Only then does the refactor happen: the ternary is pulled into `applyMembershipDiscount`, a named private method — and because all three tests still pass immediately afterward with zero test-code changes, the refactor is confirmed to be a pure structural cleanup, not an accidental behavior change.

## 7. Gotchas & takeaways

> **Gotcha:** skipping the "confirm it's actually red first" step is the most common way TDD breaks down in practice — a test that was never observed failing might be broken in a way that makes it *always* pass (a typo in the assertion, testing the wrong method), silently providing false confidence for the rest of the codebase's lifetime.

- Red-green-refactor: write a failing test first (red), write the minimal code to pass it (green), then clean up while staying green (refactor) — repeated in small cycles.
- Writing the test first, and confirming it genuinely fails before writing the implementation, is what proves the test is actually capable of catching a bug — a test that never failed once might not be testing anything real.
- "Minimal code to pass" deliberately avoids speculative, untested behavior — extending the implementation only happens in response to a new failing test demanding that specific behavior.
- The refactor step relies entirely on the existing tests staying green throughout — that's what gives confidence a structural cleanup didn't silently change behavior.
- TDD suits behavior that can be described concretely and incrementally; it fits less naturally onto pure design exploration, where prototyping first and adding tests once the shape settles is often more practical.
- See [JUnit 5 lifecycle](1026-junit-5-lifecycle-beforeeach-aftereach-beforeall-afterall.md) and [assertions (assertEquals, assertThrows, assertAll)](1027-assertions-assertequals-assertthrows-assertall.md) for the mechanical tools TDD's tests are built from, and [test coverage (JaCoCo)](1033-test-coverage-jacoco.md) for how coverage naturally tends to stay high as a side effect of writing tests first, rather than as a separately chased goal.
