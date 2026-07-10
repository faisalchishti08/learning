---
card: java
gi: 1029
slug: nested-dynamic-tests
title: Nested & dynamic tests
---

## 1. What it is

**Nested tests** (`@Nested`) group related test methods into inner classes, letting you organize tests hierarchically — "when the cart is empty," "when the cart has items," each with its own related tests and even its own `@BeforeEach` setup — instead of one long, flat list of test methods with descriptive-but-repetitive names. **Dynamic tests** (`@TestFactory`) generate test cases at runtime from a `Stream` (or `Collection`) of `DynamicTest` objects, useful when the exact set of test cases can't be known until the test actually runs — for example, one test per file found in a directory, or one test per row loaded from an external data source.

## 2. Why & when

A flat list of test methods with names like `emptyCartAddItemIncreasesCount`, `emptyCartRemoveItemThrows`, `cartWithItemsAddItemIncreasesCount`, `cartWithItemsRemoveItemDecreasesCount` repeats the "context" (empty cart vs. cart with items) in every method name, and duplicates whatever setup differs between those two contexts across every relevant test. `@Nested` classes let each context become its own inner class with its own `@BeforeEach`, so the setup for "cart with items" lives in exactly one place, and the test names inside that nested class no longer need to restate the context — `JUnit`'s test report naturally shows the hierarchy (`CartWithItems > addItemIncreasesCount`).

`@TestFactory` and `DynamicTest` solve a different problem: sometimes the number and content of test cases genuinely isn't known at compile time — it depends on runtime data (files on disk, rows from a database, an external specification). `@ParameterizedTest`'s sources are still resolved at test-*discovery* time, before the run truly starts; `@TestFactory` methods run as regular code and can build the list of test cases dynamically, from any computation, at test-execution time.

Use `@Nested` whenever a test class has natural sub-contexts (different starting states, different configurations) with genuinely different, related test groups and setups. Use `@TestFactory`/`DynamicTest` specifically when the *set* of test cases itself needs to be computed at runtime — not merely a convenient alternative to `@ParameterizedTest`, which should still be preferred for a known, fixed set of input values.

## 3. Core concept

```java
import org.junit.jupiter.api.*;
import java.util.stream.Stream;
import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.DynamicTest.dynamicTest;

class ShoppingCartTest {

    @Nested
    class WhenCartIsEmpty {
        ShoppingCart cart = new ShoppingCart();

        @Test void hasZeroItems() { assertTrue(cart.isEmpty()); }
        @Test void addingItemMakesItNonEmpty() {
            cart.add("apple");
            assertFalse(cart.isEmpty());
        }
    }

    @Nested
    class WhenCartHasItems {
        ShoppingCart cart = new ShoppingCart();
        @BeforeEach void seedCart() { cart.add("apple"); cart.add("bread"); }

        @Test void hasCorrectCount() { assertEquals(2, cart.itemCount()); }
    }

    @TestFactory
    Stream<DynamicTest> oneTestPerKnownItem() {
        return Stream.of("apple", "bread", "milk")
            .map(item -> dynamicTest("cart accepts " + item, () -> {
                ShoppingCart cart = new ShoppingCart();
                cart.add(item);
                assertEquals(1, cart.itemCount());
            }));
    }
}
class ShoppingCart {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    void add(String item) { items.add(item); }
    boolean isEmpty() { return items.isEmpty(); }
    int itemCount() { return items.size(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ShoppingCartTest containing two Nested inner classes each with their own related tests, plus a TestFactory generating one dynamic test per item in a runtime-computed list">
  <rect x="20" y="10" width="600" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="30" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ShoppingCartTest</text>

  <rect x="30" y="60" width="270" height="70" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Nested WhenCartIsEmpty</text>
  <text x="165" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hasZeroItems()</text>
  <text x="165" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">addingItemMakesItNonEmpty()</text>

  <rect x="330" y="60" width="270" height="70" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Nested WhenCartHasItems</text>
  <text x="465" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hasCorrectCount()</text>

  <rect x="30" y="150" width="570" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="315" y="170" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@TestFactory oneTestPerKnownItem() -&gt; 3 dynamic tests generated at runtime</text>
</svg>

Two `@Nested` groups organize related tests by context; `@TestFactory` generates tests dynamically rather than declaring them statically.

## 5. Runnable example

Scenario: testing a shopping cart's behavior in different starting states, evolving from a flat list of repetitively-named test methods into organized `@Nested` groups plus a `@TestFactory` for runtime-generated cases.

### Level 1 — Basic

```java
// File: src/test/java/CartBasicTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CartBasicTest {
    @Test
    void emptyCartHasZeroItems() {
        ShoppingCart cart = new ShoppingCart();
        assertTrue(cart.isEmpty());
    }

    @Test
    void emptyCartAddingItemMakesItNonEmpty() {
        ShoppingCart cart = new ShoppingCart();
        cart.add("apple");
        assertFalse(cart.isEmpty());
    }

    @Test
    void cartWithItemsHasCorrectCount() {
        ShoppingCart cart = new ShoppingCart();
        cart.add("apple");
        cart.add("bread");
        assertEquals(2, cart.itemCount());
    }
}

class ShoppingCart {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    void add(String item) { items.add(item); }
    boolean isEmpty() { return items.isEmpty(); }
    int itemCount() { return items.size(); }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

Every test name has to restate its context (`emptyCart...`, `cartWithItems...`), and the "cart with items" setup (`cart.add("apple"); cart.add("bread");`) would need to be repeated in every additional test that shares that same starting state.

### Level 2 — Intermediate

```java
// File: src/test/java/CartIntermediateTest.java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class CartIntermediateTest {

    @Nested
    class WhenCartIsEmpty {
        ShoppingCart cart = new ShoppingCart();

        @Test void hasZeroItems() {
            assertTrue(cart.isEmpty());
        }

        @Test void addingItemMakesItNonEmpty() {
            cart.add("apple");
            assertFalse(cart.isEmpty());
        }
    }

    @Nested
    class WhenCartHasItems {
        ShoppingCart cart = new ShoppingCart();

        @BeforeEach
        void seedCart() {
            cart.add("apple");
            cart.add("bread");
        }

        @Test void hasCorrectCount() {
            assertEquals(2, cart.itemCount());
        }
    }
}

class ShoppingCart {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    void add(String item) { items.add(item); }
    boolean isEmpty() { return items.isEmpty(); }
    int itemCount() { return items.size(); }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 3, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: `WhenCartIsEmpty` and `WhenCartHasItems` each group their related tests and own the setup specific to that context — `WhenCartHasItems`'s `@BeforeEach` seeding logic lives in exactly one place, and test names inside each nested class (`hasZeroItems`, `hasCorrectCount`) no longer need to restate the surrounding context.

### Level 3 — Advanced

```java
// File: src/test/java/CartAdvancedTest.java
import org.junit.jupiter.api.*;
import java.util.List;
import java.util.stream.Stream;
import static org.junit.jupiter.api.Assertions.*;
import static org.junit.jupiter.api.DynamicTest.dynamicTest;

class CartAdvancedTest {

    @Nested
    class WhenCartIsEmpty {
        ShoppingCart cart = new ShoppingCart();
        @Test void hasZeroItems() { assertTrue(cart.isEmpty()); }
    }

    @Nested
    class WhenCartHasItems {
        ShoppingCart cart = new ShoppingCart();
        @BeforeEach void seedCart() { cart.add("apple"); cart.add("bread"); }
        @Test void hasCorrectCount() { assertEquals(2, cart.itemCount()); }
    }

    // Simulates a runtime-provided catalog -- the set of test cases isn't known
    // until this method actually runs, unlike @ParameterizedTest's static sources.
    static List<String> loadCatalogItems() {
        return List.of("apple", "bread", "milk", "eggs");
    }

    @TestFactory
    Stream<DynamicTest> cartAcceptsEveryCatalogItem() {
        return loadCatalogItems().stream()
            .map(item -> dynamicTest("cart accepts '" + item + "'", () -> {
                ShoppingCart cart = new ShoppingCart();
                cart.add(item);
                assertEquals(1, cart.itemCount());
                assertFalse(cart.isEmpty());
            }));
    }
}

class ShoppingCart {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    void add(String item) { items.add(item); }
    boolean isEmpty() { return items.isEmpty(); }
    int itemCount() { return items.size(); }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=CartAdvancedTest`.

Expected output:
```
[INFO] Tests run: 6, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: `6` total tests reflects `1` from `WhenCartIsEmpty` plus `1` from `WhenCartHasItems` plus `4` dynamically generated from `loadCatalogItems()` — one per catalog item — demonstrating both organizational tools together: `@Nested` for structuring related, fixed test groups, and `@TestFactory` for a genuinely runtime-computed set of cases.

## 6. Walkthrough

Tracing how JUnit discovers and executes `cartAcceptsEveryCatalogItem`:

1. JUnit recognizes `cartAcceptsEveryCatalogItem` as a `@TestFactory` method (not a `@Test`), so instead of running it as a single pass/fail test, it *invokes* the method once to obtain its return value — a `Stream<DynamicTest>`.
2. Inside the method, `loadCatalogItems()` is called, returning `["apple", "bread", "milk", "eggs"]` — this is the point where the actual set of test cases becomes known; nothing about this list was baked into the test class at compile time.
3. `.stream().map(item -> dynamicTest(...))` transforms each catalog item into a `DynamicTest` object — each one pairs a descriptive display name (`"cart accepts 'apple'"`, etc.) with an executable block of test code (the lambda).
4. JUnit consumes this stream of four `DynamicTest` objects and executes each one's lambda in turn, reporting each as its own separate test result in the output, under the display name given at creation.
5. For the first, `"cart accepts 'apple'"`, the lambda runs: a fresh `ShoppingCart` is constructed, `"apple"` is added, and both `assertEquals(1, cart.itemCount())` and `assertFalse(cart.isEmpty())` are checked — both pass.
6. This repeats for `"bread"`, `"milk"`, and `"eggs"`, each getting its own fresh `ShoppingCart` and its own pass/fail result in the test report — if `loadCatalogItems()` returned a fifth item tomorrow (say, from an actual runtime data source instead of the hardcoded `List.of(...)` here), a fifth dynamic test would simply appear in the next run, with zero changes needed to `cartAcceptsEveryCatalogItem`'s own code.

## 7. Gotchas & takeaways

> **Gotcha:** `@Nested` classes must be **non-static** inner classes — a `static` nested class is a completely different, top-level-like class from JUnit's perspective and won't be picked up as a nested test group; this is also what allows a nested class's instance fields (like `cart` here) to be freshly initialized per test, following the same fresh-instance-per-test rule as the outer class.

- `@Nested` groups related test methods (and their own setup) into inner classes, letting different starting contexts each own their own tests and `@BeforeEach` logic without repeating context in every test name.
- `@TestFactory` methods return a `Stream` (or `Collection`) of `DynamicTest` objects, generating the actual set of test cases at runtime rather than declaring them statically — essential when the cases depend on data not known until the test executes.
- Prefer `@ParameterizedTest` (see [parameterized tests](1028-parameterized-tests.md)) over `@TestFactory` whenever the set of input values is genuinely known and fixed — `@TestFactory` is specifically for cases where the *set itself* must be computed at runtime.
- Each `DynamicTest` needs a descriptive display name, since JUnit's test report shows these names individually — a generic or repeated name across dynamic tests makes failures much harder to identify.
- `@Nested` classes are `non-static`, meaning each gets its own fresh instance (and fresh instance fields) per test, consistent with JUnit's default per-test-instance lifecycle described in [JUnit 5 lifecycle](1026-junit-5-lifecycle-beforeeach-aftereach-beforeall-afterall.md).
- Don't over-nest — a few natural levels of context (empty vs. populated, valid vs. invalid input) improve readability, but deeply nested test hierarchies mirror the same over-engineering risk any deep class hierarchy carries.
