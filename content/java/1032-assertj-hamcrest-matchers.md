---
card: java
gi: 1032
slug: assertj-hamcrest-matchers
title: "AssertJ / Hamcrest matchers"
---

## 1. What it is

AssertJ and Hamcrest are two popular libraries offering **fluent, readable assertions** as an alternative to JUnit's plain `assertEquals`/`assertTrue` style. AssertJ's signature style is a fluent chain starting with `assertThat(actual)` followed by readable method calls describing the expectation: `assertThat(list).hasSize(3).contains("apple")`. Hamcrest instead uses composable "matcher" objects passed to a single `assertThat(actual, matcher)` call: `assertThat(list, hasSize(3))`. Both aim at the same goal — assertions that read close to natural language and produce far more informative failure messages than a bare `assertEquals` ever could.

## 2. Why & when

Plain JUnit assertions work but produce failure messages that are only as good as the assertion itself allows — `assertTrue(list.size() == 3 && list.contains("apple"))` failing tells you only that "the expression was false," with no indication of which half failed or what the actual list contained. AssertJ's `assertThat(list).hasSize(3).contains("apple")` reports precisely which check failed and shows the actual list content in the failure message automatically. Both libraries also provide rich, purpose-built assertions for collections, exceptions, and strings that would otherwise require several lines of manual checking with plain JUnit assertions — checking that a collection contains items in any order, ignoring case in a string comparison, or checking several properties of an object at once, all in one fluent, readable line.

Reach for AssertJ (the more actively developed and broadly favored of the two in modern Java projects) whenever a test's assertions would otherwise require several lines of manual JUnit checks, or when a richer failure message would meaningfully speed up debugging a failing test. Plain JUnit assertions remain perfectly fine for simple, single-value checks where the extra fluency wouldn't add clarity.

## 3. Core concept

```java
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

// Fluent chain: reads close to a sentence, and reports EXACTLY which check failed
assertThat(shoppingCart.items())
    .hasSize(2)
    .contains("apple", "bread")
    .doesNotContain("milk");

// Rich exception assertions -- richer failure detail than assertThrows alone
assertThatThrownBy(() -> calculator.divide(10, 0))
    .isInstanceOf(ArithmeticException.class)
    .hasMessage("/ by zero");

// Object assertions checking several properties in one fluent, readable chain
assertThat(order)
    .extracting(Order::status, Order::total)
    .containsExactly(OrderStatus.CONFIRMED, 42.50);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A plain assertTrue combining two conditions with no indication of which failed, versus an AssertJ fluent chain reporting the exact failing check with the actual value shown">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Plain assertTrue: opaque failure</text>
  <rect x="30" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="61" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">assertTrue(size==3 &amp;&amp; contains("apple"))</text>
  <text x="145" y="100" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">"expected true, was false" -- which half?</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">AssertJ: precise failure</text>
  <rect x="380" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="61" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">assertThat(list).hasSize(3).contains("apple")</text>
  <text x="495" y="100" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">"expected size 3 but was 2, actual: [bread]"</text>
</svg>

AssertJ's fluent chain reports exactly which specific check failed and what the actual value was.

## 5. Runnable example

Scenario: testing a shopping cart's contents and a calculator's exception behavior, evolving from plain JUnit assertions into AssertJ's fluent, richly-reporting style.

### Level 1 — Basic

```java
// File: src/test/java/CartPlainAssertionsTest.java
import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class CartPlainAssertionsTest {
    @Test
    void cartContainsExpectedItems() {
        List<String> items = List.of("apple", "bread");
        assertEquals(2, items.size());
        assertTrue(items.contains("apple"));
        assertTrue(items.contains("bread"));
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

Three separate assertions are needed to check size and contents, and if any one of them fails, the failure message only reports that specific line's basic mismatch — there's no single, readable statement of everything being checked about `items` at once.

### Level 2 — Intermediate

```java
// File: src/test/java/CartAssertJTest.java
import org.junit.jupiter.api.Test;
import java.util.List;
import static org.assertj.core.api.Assertions.assertThat;

class CartAssertJTest {
    @Test
    void cartContainsExpectedItems() {
        List<String> items = List.of("apple", "bread");

        assertThat(items)
            .hasSize(2)
            .contains("apple", "bread")
            .doesNotContain("milk");
    }
}
```

**How to run:** place in a Maven project's test source root (with `assertj-core` on the test classpath — see [Maven dependencies & scopes](1036-maven-dependencies-scopes.md)), then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: one fluent, readable chain expresses everything being checked about `items` — size, expected contents, and an explicit negative check — and if any single link in the chain fails, AssertJ's failure message shows exactly which check failed along with the actual list content, without needing to add a custom message manually.

### Level 3 — Advanced

```java
// File: src/test/java/OrderAssertJAdvancedTest.java
import org.junit.jupiter.api.Test;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

enum OrderStatus { PENDING, CONFIRMED, CANCELLED }
record Order(String id, OrderStatus status, double total) {}

class Calculator {
    int divide(int a, int b) { return a / b; }
}

class OrderProcessor {
    Order confirm(Order order) {
        if (order.total() <= 0) throw new IllegalArgumentException("total must be positive");
        return new Order(order.id(), OrderStatus.CONFIRMED, order.total());
    }
}

class OrderAssertJAdvancedTest {
    @Test
    void confirmingOrderUpdatesStatusAndKeepsTotal() {
        OrderProcessor processor = new OrderProcessor();
        Order confirmed = processor.confirm(new Order("o1", OrderStatus.PENDING, 42.50));

        // extracting + containsExactly: checks MULTIPLE properties of the result
        // in one fluent, readable statement instead of separate assertEquals calls.
        assertThat(confirmed)
            .extracting(Order::status, Order::total)
            .containsExactly(OrderStatus.CONFIRMED, 42.50);
    }

    @Test
    void confirmingInvalidOrderThrowsWithClearMessage() {
        OrderProcessor processor = new OrderProcessor();

        assertThatThrownBy(() -> processor.confirm(new Order("o2", OrderStatus.PENDING, -5.0)))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessage("total must be positive");
    }

    @Test
    void divisionByZeroThrowsArithmeticException() {
        Calculator calc = new Calculator();

        assertThatThrownBy(() -> calc.divide(10, 0))
            .isInstanceOf(ArithmeticException.class)
            .hasMessageContaining("zero");
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=OrderAssertJAdvancedTest`.

Expected output:
```
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: `assertThatThrownBy` chains `isInstanceOf` and `hasMessage`/`hasMessageContaining` to check both the exception's type and its message content in one fluent statement, while `extracting(...).containsExactly(...)` checks two independent properties of a returned `Order` object without needing two separate `assertEquals` calls or an `assertAll` grouping.

## 6. Walkthrough

Tracing `confirmingOrderUpdatesStatusAndKeepsTotal` in `OrderAssertJAdvancedTest`:

1. `processor.confirm(new Order("o1", OrderStatus.PENDING, 42.50))` runs `OrderProcessor.confirm`: `order.total() <= 0` evaluates `42.50 <= 0`, which is `false`, so the exception path is skipped, and a new `Order("o1", OrderStatus.CONFIRMED, 42.50)` is returned, assigned to `confirmed`.
2. `assertThat(confirmed)` wraps `confirmed` in an AssertJ assertion object, ready for fluent chaining.
3. `.extracting(Order::status, Order::total)` calls both method references on `confirmed`, producing a tuple of `(OrderStatus.CONFIRMED, 42.50)` — AssertJ packages these two extracted values together for the next assertion in the chain.
4. `.containsExactly(OrderStatus.CONFIRMED, 42.50)` compares that extracted tuple against the expected values, in the given order — `OrderStatus.CONFIRMED` matches `confirmed.status()`, and `42.50` matches `confirmed.total()`, so this assertion passes.
5. Had either property been wrong (say, the processor forgot to update `status`), AssertJ's failure message would show precisely which extracted value(s) didn't match, including both the expected and actual tuples printed clearly — much more informative than two separate `assertEquals` failures reported independently across separate test runs.
6. In `divisionByZeroThrowsArithmeticException`, `assertThatThrownBy(() -> calc.divide(10, 0))` executes the lambda, catches the thrown `ArithmeticException` internally, and returns an assertion object wrapping it — `.isInstanceOf(ArithmeticException.class)` checks its exact type, and `.hasMessageContaining("zero")` checks that its message contains that substring (rather than requiring an exact string match), both chained fluently on the single caught exception.

## 7. Gotchas & takeaways

> **Gotcha:** AssertJ's `assertThat` and JUnit's `assertThat`-style equivalents (or Hamcrest's) can collide on the same static import if a test file imports both loosely (`import static org.assertj.core.api.Assertions.*;` alongside a Hamcrest equivalent) — pick one assertion library consistently per test class (or per project) to avoid ambiguous method resolution and inconsistent failure-message styles.

- AssertJ's fluent `assertThat(actual).method1().method2()...` chain reads close to natural language and produces detailed, specific failure messages automatically.
- Hamcrest achieves a similar goal through composable matcher objects passed to `assertThat(actual, matcher)` — both libraries aim at the same readability and failure-message quality improvements over plain JUnit assertions.
- `assertThatThrownBy` chains exception-type and message checks fluently, often replacing a `assertThrows` call followed by separate assertions on the caught exception.
- `extracting(...).containsExactly(...)` checks several properties of one object in a single fluent statement, similar in spirit to [assertAll](1027-assertions-assertequals-assertthrows-assertall.md) but expressed as one chained call rather than several grouped lambdas.
- Reach for these richer assertion libraries specifically when plain JUnit assertions would require several lines to express one logical check, or when a more detailed failure message would meaningfully speed up debugging.
- Don't mix assertion library styles inconsistently within the same test class — pick AssertJ (the more broadly favored modern choice) or Hamcrest and use it consistently for clarity and to avoid import collisions.
