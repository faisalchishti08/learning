---
card: java
gi: 1033
slug: test-coverage-jacoco
title: Test coverage (JaCoCo)
---

## 1. What it is

JaCoCo (Java Code Coverage) is a Maven/Gradle plugin that instruments your code while tests run, tracking exactly which lines and branches actually executed, and produces a report showing coverage as a percentage per class, package, and project overall. "100% line coverage" means every line ran at least once during the test suite — it says nothing about whether the *assertions* checking that execution were meaningful. Coverage is a **diagnostic tool for finding untested code**, not a quality score to maximize for its own sake.

## 2. Why & when

Without a coverage report, it's easy to believe a class is well-tested simply because *some* tests exist for it, while an entire error-handling branch, an edge case, or a rarely-hit `else` clause never actually executes during any test run — a bug hiding in that exact untested branch will slip through every test run until it surfaces in production. JaCoCo's report makes untested code *visible*: a red (uncovered) line or branch in the report is a direct pointer to exactly where a test is missing, turning "we should probably have more tests" into "this specific branch, right here, has never been executed by any test."

Use JaCoCo's coverage report as a targeted tool for finding *specific, concretely* untested branches worth writing a test for — not as a target percentage to chase for its own sake. A build gate that fails when coverage drops below a threshold is a reasonable guard against accidentally shipping large untested additions, but treating "100% coverage" as the goal encourages writing tests that execute code without meaningfully asserting on its behavior, which inflates the number while adding little real safety.

## 3. Core concept

```xml
<!-- Minimal JaCoCo setup in pom.xml -->
<build>
  <plugins>
    <plugin>
      <groupId>org.jacoco</groupId>
      <artifactId>jacoco-maven-plugin</artifactId>
      <version>0.8.11</version>
      <executions>
        <execution>
          <goals><goal>prepare-agent</goal></goals> <!-- instruments code BEFORE tests run -->
        </execution>
        <execution>
          <id>report</id>
          <phase>test</phase>
          <goals><goal>report</goal></goals> <!-- generates the HTML report AFTER tests run -->
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

```java
class DiscountCalculator {
    double apply(double total, boolean isMember) {
        if (isMember) {
            return total * 0.90; // covered if a test exercises a member
        } else {
            return total;        // covered only if a SEPARATE test exercises a non-member
        }
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A test suite exercising the member branch of a discount calculator but never the non-member branch, shown as green covered and red uncovered lines in a JaCoCo report">
  <rect x="30" y="30" width="240" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">if (isMember) return total * 0.90;</text>
  <text x="150" y="20" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">covered -- test exercises this</text>

  <rect x="30" y="100" width="240" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">else return total;</text>
  <text x="150" y="90" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">UNcovered -- no test hits this line</text>
</svg>

The `else` branch shows red in JaCoCo's report — a direct, visible pointer to exactly which test is missing.

## 5. Runnable example

Scenario: a discount calculator with a partially-tested branch, evolving from an incomplete test suite (invisible without a coverage report) into a fully covered one guided directly by JaCoCo's output.

### Level 1 — Basic

```java
// File: src/main/java/DiscountCalculator.java
public class DiscountCalculator {
    public double apply(double total, boolean isMember) {
        if (isMember) {
            return total * 0.90;
        } else {
            return total;
        }
    }
}
```

```java
// File: src/test/java/DiscountCalculatorBasicTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class DiscountCalculatorBasicTest {
    @Test
    void memberGetsTenPercentOff() {
        DiscountCalculator calc = new DiscountCalculator();
        assertEquals(90.0, calc.apply(100.0, true));
    }
    // No test at all for isMember == false -- the else branch is never exercised.
}
```

**How to run:** place both files in a Maven project (`src/main/java/DiscountCalculator.java`, `src/test/java/DiscountCalculatorBasicTest.java`), add the JaCoCo plugin from Part 3 to `pom.xml`, then run `mvn test`. Open `target/site/jacoco/index.html` in a browser afterward.

Expected result: the test run itself passes —
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```
— but the JaCoCo HTML report for `DiscountCalculator` shows the `else return total;` line highlighted in **red** (0% covered), and the class's overall line coverage below 100%, even though the single existing test passed cleanly.

The test suite passing tells you nothing about the `else` branch — it's the coverage report, not the test result, that reveals this specific line has never run.

### Level 2 — Intermediate

```java
// File: src/test/java/DiscountCalculatorIntermediateTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

class DiscountCalculatorIntermediateTest {
    @Test
    void memberGetsTenPercentOff() {
        DiscountCalculator calc = new DiscountCalculator();
        assertEquals(90.0, calc.apply(100.0, true));
    }

    @Test
    void nonMemberGetsNoDiscount() {
        DiscountCalculator calc = new DiscountCalculator();
        assertEquals(100.0, calc.apply(100.0, false)); // now exercises the else branch directly
    }
}
```

**How to run:** run `mvn test`, then open `target/site/jacoco/index.html`.

Expected result:
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```
JaCoCo's report for `DiscountCalculator` now shows **100%** line and branch coverage — both the `if` and `else` branches are highlighted green, since `nonMemberGetsNoDiscount` exercises the previously-untested path.

The real-world concern added: the coverage report directly identified the missing test case (the `else` branch), and adding exactly one targeted test closed that specific gap — coverage went from partial to complete not by guessing, but by following what the report showed as red.

### Level 3 — Advanced

```java
// File: src/main/java/DiscountCalculator.java
public class DiscountCalculator {
    public double apply(double total, boolean isMember, boolean isFirstPurchase) {
        if (total < 0) {
            throw new IllegalArgumentException("total cannot be negative");
        }
        double discounted = isMember ? total * 0.90 : total;
        if (isFirstPurchase) {
            discounted -= 5.0; // an additional flat discount, easy to forget testing
        }
        return Math.max(discounted, 0.0); // floor at zero -- another easy-to-miss branch
    }
}
```

```java
// File: src/test/java/DiscountCalculatorAdvancedTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class DiscountCalculatorAdvancedTest {
    private final DiscountCalculator calc = new DiscountCalculator();

    @Test
    void memberFirstPurchaseGetsBothDiscounts() {
        assertEquals(85.0, calc.apply(100.0, true, true)); // 90 - 5
    }

    @Test
    void nonMemberReturningCustomerGetsNoDiscount() {
        assertEquals(100.0, calc.apply(100.0, false, false));
    }

    @Test
    void negativeTotalThrows() {
        assertThrows(IllegalArgumentException.class, () -> calc.apply(-10.0, false, false));
    }

    @Test
    void discountNeverGoesBelowZero() {
        // A small total with the flat $5 first-purchase discount would go negative
        // without the Math.max floor -- this test specifically exercises that floor.
        assertEquals(0.0, calc.apply(3.0, false, true));
    }
}
```

**How to run:** run `mvn test`, then open `target/site/jacoco/index.html`.

Expected result:
```
[INFO] Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
```
JaCoCo now reports 100% branch coverage across all four conditional paths: the negative-total guard, the membership discount, the first-purchase discount, and the zero-floor — each specifically targeted by one of the four tests above.

The production-flavored hard case: `discountNeverGoesBelowZero` exists specifically because JaCoCo's *branch* coverage (not just line coverage) would flag `Math.max(discounted, 0.0)` as only partially covered if no test ever drove `discounted` low enough to actually hit the "floor at zero" case — line coverage alone can be misleadingly high even when one side of a conditional expression never actually triggers.

## 6. Walkthrough

Tracing how coverage builds up across the four tests in `DiscountCalculatorAdvancedTest`:

1. `memberFirstPurchaseGetsBothDiscounts` calls `apply(100.0, true, true)`: `total < 0` is `false` (skips the exception branch), `discounted = 100.0 * 0.90 = 90.0` (exercises the `isMember == true` side of the ternary), `isFirstPurchase` is `true` so `discounted -= 5.0` runs, giving `85.0`, and `Math.max(85.0, 0.0)` returns `85.0` (exercises the "value already above zero" side of `Math.max`).
2. `nonMemberReturningCustomerGetsNoDiscount` calls `apply(100.0, false, false)`: this exercises the `isMember == false` side of the ternary (previously untested by test 1) and skips the first-purchase adjustment entirely, exercising the "skip" path of that `if`.
3. `negativeTotalThrows` calls `apply(-10.0, false, false)`: `total < 0` is now `true`, exercising the exception-throwing branch for the first time across all four tests — without this test, JaCoCo would show this line in red.
4. `discountNeverGoesBelowZero` calls `apply(3.0, false, true)`: `discounted` starts at `3.0` (non-member, no membership discount), then `isFirstPurchase` triggers `discounted -= 5.0`, making `discounted = -2.0` — this specifically drives `Math.max(-2.0, 0.0)` to actually return the second argument, `0.0`, exercising the branch of that expression where the floor genuinely takes effect (rather than just returning `discounted` unchanged, as happened in test 1).
5. After all four tests run, JaCoCo's instrumentation has recorded that every line executed at least once, and — critically for branch coverage — both sides of every conditional (`if`/`else`, the ternary, and `Math.max`'s effective branching) were each exercised by at least one test.
6. The JaCoCo report reflects this as 100% coverage for the class, but the real value wasn't the percentage itself — it was using the report, test by test, to identify exactly which specific branch (the exception guard, the zero-floor) still needed a targeted test, rather than writing tests speculatively and hoping they happened to cover everything.

## 7. Gotchas & takeaways

> **Gotcha:** 100% line coverage does not mean the code is well-tested — a test that calls a method and asserts nothing about its result (or asserts something trivially true) still "covers" every line the method executes, while verifying nothing meaningful about its actual behavior. Coverage measures *execution*, not *verification*.

- JaCoCo instruments code during the test run and reports exactly which lines and branches executed — a red line in the report is a direct, specific signal of where a test is missing.
- Line coverage and branch coverage are different metrics — a conditional expression's line can show as "covered" even if only one of its two possible outcomes was ever actually exercised; branch coverage catches this gap.
- Use coverage reports to find *specific* untested code worth writing a targeted test for, not as an abstract percentage target — chasing the number encourages tests that execute code without meaningfully asserting on its behavior.
- A coverage threshold as a build gate (failing the build if coverage drops below some percentage) is a reasonable guard against large, entirely untested additions slipping through, used as a floor rather than a goal to maximize.
- Coverage says nothing about whether the assertions in a passing test are actually correct or meaningful — see [assertions (assertEquals, assertThrows, assertAll)](1027-assertions-assertequals-assertthrows-assertall.md) and [TDD basics](1034-tdd-basics.md) for how to write tests that genuinely verify behavior, not just execute it.
- Don't treat an uncovered branch as automatically worth testing regardless of context — some code (generated boilerplate, defensive code for conditions that structurally cannot occur) may be reasonably excluded from coverage requirements rather than tested for its own sake.
