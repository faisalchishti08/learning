---
card: java
gi: 1026
slug: junit-5-lifecycle-beforeeach-aftereach-beforeall-afterall
title: "JUnit 5 lifecycle (@BeforeEach/@AfterEach/@BeforeAll/@AfterAll)"
---

## 1. What it is

JUnit 5's lifecycle annotations control code that runs automatically **around** your test methods: `@BeforeEach` runs before every single test method, `@AfterEach` runs after every single test method, and `@BeforeAll`/`@AfterAll` run exactly **once**, before the first test and after the last test in the class, respectively. JUnit creates a **fresh instance of the test class for every test method** by default — so `@BeforeEach`/`@AfterEach` methods are regular (non-static) instance methods that can freely use instance fields, while `@BeforeAll`/`@AfterAll` must be `static`, since they run before any test instance exists at all (or after every instance has already been used).

## 2. Why & when

Repeating the same setup code (creating a fresh object under test, clearing a shared collection) at the top of every single test method is both tedious and risky — it's easy for one test to forget a reset step and silently leak state into the next test that runs, making test *order* accidentally matter, which is exactly the kind of flakiness a good test suite should never have. `@BeforeEach` guarantees that setup runs identically before every test, with no test able to forget it. `@BeforeAll`/`@AfterAll` exist for the opposite case: work that's genuinely expensive and shareable across all tests in the class — starting a test container, opening one shared expensive connection — where doing it once, rather than before every single test, is the whole point.

Use `@BeforeEach`/`@AfterEach` for anything that must be fresh per test — a new instance of the class under test, a cleared mutable collection — to guarantee tests never leak state into each other regardless of execution order. Reserve `@BeforeAll`/`@AfterAll` specifically for expensive, safely-shareable setup with no per-test state — since it runs only once, any state it sets up is implicitly shared (and potentially mutated) across every test in the class, which is only safe if every test either doesn't mutate it or is fine sharing that mutation.

## 3. Core concept

```java
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class ShoppingCartTest {

    @BeforeAll
    static void setUpClass() {
        System.out.println("Runs ONCE, before any test in this class");
    }

    @BeforeEach
    void setUp() {
        System.out.println("Runs before EVERY test -- fresh state each time");
        // e.g.: cart = new ShoppingCart();
    }

    @Test
    void emptyCartHasZeroItems() {
        System.out.println("  test 1 runs");
    }

    @Test
    void addingItemIncreasesCount() {
        System.out.println("  test 2 runs");
    }

    @AfterEach
    void tearDown() {
        System.out.println("Runs after EVERY test");
    }

    @AfterAll
    static void tearDownClass() {
        System.out.println("Runs ONCE, after all tests in this class");
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="beforeAll running once, then beforeEach and afterEach wrapping each individual test method, then afterAll running once at the very end">
  <rect x="20" y="10" width="600" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="30" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@BeforeAll -- once</text>

  <rect x="20" y="60" width="280" height="90" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@BeforeEach</text>
  <text x="160" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">test 1</text>
  <text x="160" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@AfterEach</text>

  <rect x="340" y="60" width="280" height="90" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@BeforeEach</text>
  <text x="480" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">test 2</text>
  <text x="480" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@AfterEach</text>

  <rect x="20" y="170" width="600" height="26" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@AfterAll -- once</text>
</svg>

`@BeforeAll`/`@AfterAll` wrap the whole class exactly once; `@BeforeEach`/`@AfterEach` wrap each individual test method.

## 5. Runnable example

Scenario: a `ShoppingCart` test suite, evolving from manual per-test setup repeated by hand into the full JUnit 5 lifecycle used correctly.

### Level 1 — Basic

```java
// File: src/test/java/ShoppingCartBasicTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ShoppingCartBasicTest {

    @Test
    void emptyCartHasZeroItems() {
        ShoppingCart cart = new ShoppingCart(); // manually repeated in EVERY test method
        assertTrue(cart.isEmpty());
    }

    @Test
    void addingItemIncreasesCount() {
        ShoppingCart cart = new ShoppingCart(); // duplicated setup, easy to forget or drift
        cart.add("apple");
        assertEquals(1, cart.itemCount());
    }
}

class ShoppingCart {
    private final java.util.List<String> items = new java.util.ArrayList<>();
    void add(String item) { items.add(item); }
    boolean isEmpty() { return items.isEmpty(); }
    int itemCount() { return items.size(); }
}
```

**How to run:** place in a Maven project (`src/test/java/ShoppingCartBasicTest.java`) with `junit-jupiter` on the test classpath (see the `pom.xml` snippet in [Maven dependencies & scopes](1036-maven-dependencies-scopes.md)), then run `mvn test`.

Expected output (relevant excerpt from `mvn test`):
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

`new ShoppingCart()` is repeated identically at the top of every single test method — harmless here with only two tests, but every test author must remember to include it, and any test that forgets starts with `null` instead of a fresh cart.

### Level 2 — Intermediate

```java
// File: src/test/java/ShoppingCartIntermediateTest.java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ShoppingCartIntermediateTest {
    private ShoppingCart cart; // instance field -- fresh per test since JUnit creates a new instance per test

    @BeforeEach
    void setUp() {
        cart = new ShoppingCart(); // runs automatically before EVERY test method
    }

    @Test
    void emptyCartHasZeroItems() {
        assertTrue(cart.isEmpty());
    }

    @Test
    void addingItemIncreasesCount() {
        cart.add("apple");
        assertEquals(1, cart.itemCount());
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
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: `@BeforeEach` guarantees `cart` is freshly constructed before every test, with no test author able to forget it. Neither test method needs to repeat the construction line — and JUnit's default of a fresh test-class instance per test method means `cart` never leaks state between `emptyCartHasZeroItems` and `addingItemIncreasesCount`.

### Level 3 — Advanced

```java
// File: src/test/java/ShoppingCartAdvancedTest.java
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class ShoppingCartAdvancedTest {
    private static PricingService pricingService; // shared across ALL tests -- expensive to create
    private ShoppingCart cart; // fresh per test

    @BeforeAll
    static void startPricingService() {
        // Simulates something genuinely expensive to set up once (a shared connection,
        // a loaded reference dataset) -- deliberately done ONCE, not per test.
        pricingService = new PricingService();
        System.out.println("[once] pricing service started");
    }

    @BeforeEach
    void setUp() {
        cart = new ShoppingCart(pricingService);
    }

    @Test
    void emptyCartTotalsZero() {
        assertEquals(0.0, cart.total());
    }

    @Test
    void addingItemsAccumulatesTotal() {
        cart.add("apple", 1.50);
        cart.add("bread", 2.75);
        assertEquals(4.25, cart.total(), 0.0001);
    }

    @AfterEach
    void logCartState() {
        System.out.println("  after test: cart had " + cart.itemCount() + " item(s)");
    }

    @AfterAll
    static void stopPricingService() {
        pricingService.shutdown();
        System.out.println("[once] pricing service stopped");
    }
}

class PricingService {
    void shutdown() { /* release shared resources */ }
}

class ShoppingCart {
    private final PricingService pricingService;
    private final java.util.List<Double> prices = new java.util.ArrayList<>();
    ShoppingCart(PricingService pricingService) { this.pricingService = pricingService; }
    void add(String item, double price) { prices.add(price); }
    double total() { return prices.stream().mapToDouble(Double::doubleValue).sum(); }
    int itemCount() { return prices.size(); }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=ShoppingCartAdvancedTest`.

Expected output (relevant excerpt, order of the two `[once]` lines relative to the whole run confirmed by JUnit's console output):
```
[once] pricing service started
  after test: cart had 0 item(s)
  after test: cart had 2 item(s)
[once] pricing service stopped
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: `pricingService` (expensive, shared) is created exactly once via `@BeforeAll` and reused by both tests, while `cart` (needs to be fresh, since tests mutate it) is recreated per test via `@BeforeEach` — deliberately mixing "shared once" and "fresh per test" state within the same test class, based on which kind each piece of state actually needs to be.

## 6. Walkthrough

Tracing the full lifecycle for `ShoppingCartAdvancedTest`'s two tests, in the order JUnit executes them:

1. Before any test method runs, JUnit calls `startPricingService()` — being `static`, this runs without any test-class instance existing yet, printing `"[once] pricing service started"` and assigning the class-level `pricingService` field.
2. For the first test, JUnit creates a **new instance** of `ShoppingCartAdvancedTest` and calls `setUp()` on it, constructing `cart = new ShoppingCart(pricingService)` — note `pricingService` is the same shared instance from step 1, referenced (not recreated) here.
3. The test method itself runs — say `emptyCartTotalsZero`, calling `assertEquals(0.0, cart.total())`, which passes since a freshly-constructed `cart` has no prices added yet.
4. `logCartState()` runs next (on the same test-class instance), printing `"  after test: cart had 0 item(s)"`.
5. For the second test, JUnit creates **another new instance** of `ShoppingCartAdvancedTest` (a completely separate object from step 2's instance) and calls `setUp()` again on this new instance, constructing a brand-new `cart` — but `pricingService` is still the exact same static field value from step 1, shared across both instances.
6. `addingItemsAccumulatesTotal` runs on this fresh `cart`, adding two items and asserting the total; `logCartState()` runs again, printing `"  after test: cart had 2 item(s)"`. After both tests complete, JUnit calls the `static` `stopPricingService()` exactly once, printing `"[once] pricing service stopped"` — confirming `@BeforeAll`/`@AfterAll` ran exactly once each for the whole class, while `@BeforeEach`/`@AfterEach` ran once per test, on a fresh instance each time.

## 7. Gotchas & takeaways

> **Gotcha:** `@BeforeAll`/`@AfterAll` methods must be `static` by default, because JUnit creates a new test-class instance per test method — there's no single, shared instance for a non-static method to run on before the first test even exists. (JUnit's `@TestInstance(Lifecycle.PER_CLASS)` annotation can change this default and allow non-static `@BeforeAll`/`@AfterAll`, but that also changes other lifecycle behavior and should be a deliberate choice.)

- `@BeforeEach`/`@AfterEach` run before/after every individual test method, on a fresh test-class instance each time by default — ideal for state that must never leak between tests.
- `@BeforeAll`/`@AfterAll` run exactly once per test class, and must be `static` under JUnit's default per-method instance lifecycle.
- Reserve `@BeforeAll`/`@AfterAll` for genuinely expensive, safely-shareable setup — any state it creates is implicitly shared across every test in the class, so mutating it in one test can leak into another unless that's deliberately intended.
- JUnit's default of a fresh instance per test method is what makes instance fields set in `@BeforeEach` safe from cross-test contamination — you don't need to manually reset them at the end of each test.
- See [assertions (assertEquals, assertThrows, assertAll)](1027-assertions-assertequals-assertthrows-assertall.md) for what actually goes inside the `@Test` methods themselves.
- Don't put logic that only some tests need inside `@BeforeEach` — if setup diverges meaningfully between tests, that's often a sign the tests belong in separate `@Nested` classes with their own lifecycle, covered in [nested & dynamic tests](1029-nested-dynamic-tests.md).
