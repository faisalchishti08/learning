---
card: spring-boot
gi: 204
slug: spring-boot-starter-test-contents-junit-5-assertj-hamcrest-m
title: spring-boot-starter-test contents (JUnit 5, AssertJ, Hamcrest, Mockito, JSONassert, JsonPath)
---

## 1. What it is

`spring-boot-starter-test` is an all-in-one test dependency that bundles the tools Spring Boot applications need for testing. Adding a single dependency gives you JUnit 5, AssertJ, Hamcrest, Mockito, JSONassert, JsonPath, and the Spring Test utilities — all at compatible versions, no manual version management.

## 2. Why & when

Before this starter, each project had to manually assemble JUnit, Hamcrest, Mockito, JSON assertion libraries, and ensure their versions didn't conflict. The starter solves that once and keeps versions in sync with each Spring Boot release. Add it to every Spring Boot project with `<scope>test</scope>` and immediately have access to the full testing toolkit.

## 3. Core concept

**Maven:**
```xml
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-test</artifactId>
    <scope>test</scope>
</dependency>
```

**Bundled libraries:**

| Library | Role | Key API |
|---|---|---|
| **JUnit 5 (Jupiter)** | Test framework | `@Test`, `@ExtendWith`, `@ParameterizedTest` |
| **AssertJ** | Fluent assertions | `assertThat(x).isEqualTo(y).isNotNull()` |
| **Hamcrest** | Matcher library | `assertThat(x, is(42))`, `hasItems(...)` |
| **Mockito** | Mocking framework | `@Mock`, `when().thenReturn()`, `verify()` |
| **Mockito JUnit 5 extension** | Mockito + JUnit 5 integration | `@ExtendWith(MockitoExtension.class)` |
| **JSONassert** | JSON equality testing | `JSONAssert.assertEquals(expected, actual, strict)` |
| **JsonPath** | JSON path assertions | `JsonPath.read(json, "$.name")` |
| **Spring Test** | Spring integration utilities | `MockMvc`, `TestRestTemplate`, `@SpringBootTest` |
| **Spring Boot Test** | Boot-specific test support | `@SpringBootTest`, test slices |
| **Awaitility** | Async test utilities | `await().until(condition)` |

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="spring-boot-starter-test aggregates JUnit 5, AssertJ, Hamcrest, Mockito, JSONassert, JsonPath, Spring Test, and Awaitility into one dependency">
  <!-- Central starter -->
  <rect x="230" y="85" width="220" height="42" rx="10" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="102" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">spring-boot-starter-test</text>
  <text x="340" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one dependency, all at compatible versions</text>

  <!-- Lib boxes -->
  <rect x="10"  y="20"  width="125" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="72"  y="40"  fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JUnit 5 (Jupiter)</text>

  <rect x="10"  y="62"  width="125" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="72"  y="82"  fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">AssertJ</text>

  <rect x="10"  y="104" width="125" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="72"  y="124" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Hamcrest</text>

  <rect x="10"  y="146" width="125" height="32" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="72"  y="166" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Mockito + JUnit5 ext</text>

  <rect x="545" y="20"  width="125" height="32" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="40"  fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Test</text>

  <rect x="545" y="62"  width="125" height="32" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="82"  fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Boot Test</text>

  <rect x="545" y="104" width="125" height="32" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="124" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSONassert</text>

  <rect x="545" y="146" width="125" height="32" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="166" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JsonPath + Awaitility</text>

  <!-- Arrows from libs to starter -->
  <line x1="137" y1="36"  x2="228" y2="95" stroke="#6db33f" stroke-width="1.2" marker-end="url(#sta)"/>
  <line x1="137" y1="78"  x2="228" y2="100" stroke="#6db33f" stroke-width="1.2" marker-end="url(#sta)"/>
  <line x1="137" y1="120" x2="228" y2="106" stroke="#6db33f" stroke-width="1.2" marker-end="url(#sta)"/>
  <line x1="137" y1="162" x2="228" y2="112" stroke="#6db33f" stroke-width="1.2" marker-end="url(#sta)"/>
  <line x1="543" y1="36"  x2="452" y2="95" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#stb)"/>
  <line x1="543" y1="78"  x2="452" y2="100" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#stb)"/>
  <line x1="543" y1="120" x2="452" y2="106" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#stb)"/>
  <line x1="543" y1="162" x2="452" y2="112" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#stb)"/>

  <text x="340" y="198" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">scope=test — never included in production JAR</text>

  <defs>
    <marker id="sta" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="stb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

One starter brings all test libraries at compatible versions; they're all `scope=test` and excluded from the production JAR.

## 5. Runnable example

```java
// StarterTestDemo.java — demonstrates assertion styles from each bundled library
// How to run: java StarterTestDemo.java  (JDK 17+, no dependencies)
// Real tests: use @Test + @SpringBootTest; this file shows the API patterns

import java.util.*;

public class StarterTestDemo {

    record Order(String id, String customer, double total, List<String> items) {}

    // --- Mini assertion helpers (simulating JUnit/AssertJ/Hamcrest) ---
    static <T> void assertEquals(T expected, T actual, String label) {
        if (!Objects.equals(expected, actual))
            throw new AssertionError(label + ": expected " + expected + " but was " + actual);
        System.out.println("  ✓ " + label);
    }

    static <T> void assertNotNull(T value, String label) {
        if (value == null) throw new AssertionError(label + ": expected non-null");
        System.out.println("  ✓ " + label + " [not null]");
    }

    static <T extends Comparable<T>> void assertGreaterThan(T actual, T threshold, String label) {
        if (actual.compareTo(threshold) <= 0)
            throw new AssertionError(label + ": " + actual + " is not > " + threshold);
        System.out.println("  ✓ " + label + " [" + actual + " > " + threshold + "]");
    }

    static <T> void assertContains(Collection<T> collection, T item, String label) {
        if (!collection.contains(item))
            throw new AssertionError(label + ": " + collection + " does not contain " + item);
        System.out.println("  ✓ " + label + " [contains " + item + "]");
    }

    // Simulated JSON assertion
    static void assertJsonPath(String json, String path, String expected, String label) {
        // Very simplified JsonPath simulation
        boolean found = json.contains("\"" + path.replace("$.", "") + "\": \"" + expected + "\"")
                     || json.contains("\"" + path.replace("$.", "") + "\":\"" + expected + "\"");
        if (!found) throw new AssertionError(label + ": path " + path + " != " + expected + " in " + json);
        System.out.println("  ✓ " + label + " [" + path + " = " + expected + "]");
    }

    // Simulated Mockito stub
    static class MockOrderRepository {
        private final Map<String, Order> data = new HashMap<>();
        boolean findByIdCalled = false;

        void stub(Order order) { data.put(order.id(), order); }

        Order findById(String id) {
            findByIdCalled = true;
            return data.get(id);
        }

        void verify(String id) {
            if (!findByIdCalled)
                throw new AssertionError("findById was never called!");
            System.out.println("  ✓ verify: findById called");
        }
    }

    public static void main(String[] args) {
        System.out.println("=== spring-boot-starter-test API Patterns ===\n");

        Order order = new Order("ORD-001", "alice", 149.99,
                List.of("Widget A", "Gadget B", "Donut C"));

        // JUnit 5 style assertions
        System.out.println("--- JUnit 5 Assertions ---");
        assertEquals("ORD-001", order.id(),       "order.id()");
        assertEquals("alice",   order.customer(), "order.customer()");
        assertNotNull(order.items(),              "order.items()");

        // AssertJ style (fluent chaining)
        System.out.println("\n--- AssertJ style (fluent) ---");
        // assertThat(order.total()).isGreaterThan(0.0).isLessThan(200.0)
        assertGreaterThan(order.total(), 0.0, "total > 0");
        assertContains(order.items(), "Widget A", "items contains Widget A");
        assertEquals(3, order.items().size(), "3 items");

        // Hamcrest style (matcher-based)
        System.out.println("\n--- Hamcrest style (matchers) ---");
        // assertThat(order.items(), hasItems("Widget A", "Gadget B"))
        assertContains(order.items(), "Gadget B", "hasItem Gadget B");
        assertGreaterThan(order.items().size(), 0, "hasSize > 0");

        // Mockito style
        System.out.println("\n--- Mockito style ---");
        MockOrderRepository mockRepo = new MockOrderRepository();
        mockRepo.stub(order);
        Order found = mockRepo.findById("ORD-001");
        assertEquals("ORD-001", found.id(), "mock returns stubbed order");
        mockRepo.verify("ORD-001");

        // JSONassert / JsonPath style
        System.out.println("\n--- JSONassert / JsonPath style ---");
        String json = "{\"id\": \"ORD-001\", \"customer\": \"alice\", \"total\": 149.99}";
        assertJsonPath(json, "$.id",       "ORD-001", "JsonPath $.id");
        assertJsonPath(json, "$.customer", "alice",   "JsonPath $.customer");

        System.out.println("\n--- Real test class structure ---");
        System.out.println("""
@SpringBootTest
class OrderServiceTest {

    @MockitoBean OrderRepository repo;       // Mockito mock
    @Autowired   OrderService    service;

    @Test void createOrder_returnsOrderWithId() {
        when(repo.save(any())).thenReturn(new Order("ORD-1"));
        Order o = service.create(new OrderRequest("alice", 99.99));

        assertThat(o.id()).isNotNull();          // AssertJ
        assertThat(o.total()).isEqualTo(99.99);
        verify(repo).save(any());               // Mockito verify
    }
}""");

        System.out.println("\nAll assertion patterns passed.");
    }
}
```

**How to run:** `java StarterTestDemo.java`

## 6. Walkthrough

- **JUnit 5 assertions** (`assertEquals`, `assertNotNull`): the foundational test assertions. `@Test` methods that throw `AssertionError` (or `AssertionFailedError`) are reported as failures.
- **AssertJ** (`assertThat(x).isGreaterThan(...).isLessThan(...)`): fluent chaining style. The chain reads like English and produces clear failure messages. Preferred over JUnit 5's `assertEquals` for complex assertions.
- **Hamcrest** (`hasItems`, `hasSize`, `is`): matcher-based assertions. Still widely used with `MockMvc` result matchers (`jsonPath("$.name", is("alice"))`).
- **Mockito** (`when(...).thenReturn(...)`, `verify(...)`): stubs return values and verifies calls. In Spring Boot 3, `@MockitoBean` (replaces `@MockBean`) injects a Mockito mock into the Spring context.
- **JSONassert/JsonPath**: assert on JSON response bodies — critical for `MockMvc` and `TestRestTemplate` tests.
- The real test class snippet shows how all these tools combine in a single `@SpringBootTest` test.

## 7. Gotchas & takeaways

> `spring-boot-starter-test` includes **JUnit 4 (Vintage)** transitively via Mockito in older Spring Boot versions. In Spring Boot 3, JUnit 4 is excluded by default. If you need JUnit 4, add `junit:junit` explicitly — but prefer migrating to JUnit 5.

> AssertJ is generally preferred over Hamcrest for new code — its error messages are clearer and IDE completion is better. Hamcrest remains useful with `MockMvc` result matchers where the API expects `Matcher<?>` types.

- Always declare `scope=test` — the starter must never reach the production JAR.
- `@ExtendWith(MockitoExtension.class)` initializes `@Mock` fields without a Spring context — fastest option for pure unit tests.
- Awaitility (`await().atMost(5, SECONDS).until(() -> ...))`) handles async tests without `Thread.sleep`.
- JSONassert `strict=false` (non-strict mode) allows extra fields in the actual JSON — use `strict=true` for exact equality.
