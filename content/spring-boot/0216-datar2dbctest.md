---
card: spring-boot
gi: 216
slug: datar2dbctest
title: "@DataR2dbcTest"
---

## 1. What it is

`@DataR2dbcTest` is the reactive database test slice for Spring Data R2DBC. It loads R2DBC repositories, `R2dbcEntityTemplate`, the R2DBC connection factory, and configures an in-memory H2 (or R2DBC-compatible) database. It does NOT load JPA, web, or service beans. Because R2DBC is fully non-blocking, test methods return reactive types (`Mono<Void>`, `Flux<T>`) and use reactor-test's `StepVerifier` for assertions.

## 2. Why & when

Use `@DataR2dbcTest` when your application uses Spring Data R2DBC (reactive relational data access):
- Testing reactive repository methods (`ReactiveCrudRepository`).
- Testing custom `@Query` SQL in reactive repositories.
- Testing `R2dbcEntityTemplate` queries.
- Verifying that streaming queries emit the correct number of elements.

Not for JPA (use `@DataJpaTest`) or non-reactive JDBC (use `@DataJdbcTest`). The key distinction from `@DataJpaTest`: all database operations return `Mono`/`Flux` and are non-blocking.

## 3. Core concept

```java
@DataR2dbcTest
class OrderR2dbcRepositoryTest {

    @Autowired OrderR2dbcRepository repo;
    @Autowired R2dbcEntityTemplate template;

    @Test
    void findByCustomer_returnsOrders() {
        // Insert test data via template (reactive)
        template.insert(new Order("alice", 99.99))
                .then(template.insert(new Order("alice", 149.00)))
                .block(); // block in test setup only

        StepVerifier.create(repo.findByCustomer("alice"))
                    .expectNextMatches(o -> "alice".equals(o.getCustomer()))
                    .expectNextMatches(o -> "alice".equals(o.getCustomer()))
                    .verifyComplete();
    }

    @Test
    void findById_notExisting_returnsEmpty() {
        StepVerifier.create(repo.findById(999L))
                    .verifyComplete(); // empty Mono completes without emitting
    }
}
```

**Schema:** loaded from `schema.sql` in `src/test/resources` (same as `@DataJdbcTest`).

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@DataR2dbcTest loads reactive R2DBC repositories and R2dbcEntityTemplate against H2 R2DBC; StepVerifier asserts on Mono/Flux emissions; no blocking IO, no JPA, no web">
  <!-- StepVerifier (test) -->
  <rect x="10" y="70" width="140" height="58" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="75" y="91" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">StepVerifier</text>
  <text x="75" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.create(flux)</text>
  <text x="75" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.expectNext()</text>
  <text x="75" y="131" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.verifyComplete()</text>

  <!-- Arrow -->
  <line x1="152" y1="99" x2="200" y2="99" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#r2a)"/>

  <!-- R2DBC slice -->
  <rect x="205" y="25" width="270" height="140" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="340" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataR2dbcTest Slice</text>
  <rect x="218" y="58" width="244" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="75" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">R2DBC Repositories (ReactiveCrudRepository)</text>
  <rect x="218" y="91" width="244" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">R2dbcEntityTemplate (reactive queries)</text>
  <rect x="218" y="124" width="244" height="26" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">R2DBC ConnectionFactory (H2 R2DBC driver)</text>

  <!-- Arrow to DB -->
  <line x1="477" y1="99" x2="535" y2="99" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#r2b)"/>

  <!-- DB -->
  <rect x="540" y="65" width="130" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="605" y="86" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">H2 R2DBC</text>
  <text x="605" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">reactive SQL ops</text>
  <text x="605" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">schema.sql loaded</text>
  <text x="605" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(no ROLLBACK — R2DBC</text>
  <text x="605" y="142" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">has no TX rollback default)</text>

  <text x="340" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ JPA, Servlet, blocking DataSource, Kafka, web layer excluded</text>

  <defs>
    <marker id="r2a" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="r2b" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`StepVerifier` subscribes to reactive repository results; `R2dbcEntityTemplate` seeds test data; H2 R2DBC provides a non-blocking in-memory database.

## 5. Runnable example

```java
// DataR2dbcTestDemo.java — simulates @DataR2dbcTest reactive repository testing with StepVerifier
// How to run: java DataR2dbcTestDemo.java  (JDK 17+, no dependencies)
// Real use: @DataR2dbcTest + @Autowired OrderR2dbcRepository + StepVerifier

import java.util.*;
import java.util.concurrent.*;
import java.util.stream.Collectors;

public class DataR2dbcTestDemo {

    record Order(Long id, String customer, double total) {
        Order(String customer, double total) { this(null, customer, total); }
        Order withId(long id) { return new Order(id, customer, total); }
    }

    // Simulate Mono/Flux (minimal reactive types)
    static class Mono<T> {
        final T value;
        Mono(T value) { this.value = value; }
        static <T> Mono<T> just(T v)  { return new Mono<>(v); }
        static <T> Mono<T> empty()    { return new Mono<>(null); }
        T block() { return value; }
        boolean hasValue() { return value != null; }
    }

    static class Flux<T> {
        final List<T> items;
        Flux(List<T> items) { this.items = items; }
        @SafeVarargs static <T> Flux<T> just(T... items) { return new Flux<>(List.of(items)); }
        static <T> Flux<T> fromList(List<T> list) { return new Flux<>(list); }
        List<T> collectList() { return items; }
        int count() { return items.size(); }
    }

    // Simulates R2DBC in-memory repository (non-blocking reads from in-memory map)
    static class InMemoryR2dbcDb {
        private long seq = 1;
        final List<Order> store = new ArrayList<>();

        Mono<Order> insert(Order o) {
            Order saved = o.withId(seq++);
            store.add(saved);
            System.out.println("  [R2DBC INSERT] " + saved);
            return Mono.just(saved);
        }

        Flux<Order> findByCustomer(String customer) {
            System.out.println("  [R2DBC SELECT] WHERE customer='" + customer + "'");
            return Flux.fromList(store.stream().filter(o -> customer.equals(o.customer())).collect(Collectors.toList()));
        }

        Mono<Order> findById(long id) {
            System.out.println("  [R2DBC SELECT] WHERE id=" + id);
            return store.stream().filter(o -> o.id() == id).findFirst()
                        .map(Mono::just).orElse(Mono.empty());
        }

        Flux<Order> findAll() {
            System.out.println("  [R2DBC SELECT] SELECT * FROM orders");
            return Flux.fromList(List.copyOf(store));
        }

        void clean() { store.clear(); seq = 1; System.out.println("  [CLEANUP] store cleared"); }
    }

    // Simulates StepVerifier
    static class StepVerifier<T> {
        private final List<T> actual;
        private int expectCount = 0;
        private final List<String> failures = new ArrayList<>();

        StepVerifier(Flux<T> flux) { this.actual = flux.collectList(); }
        StepVerifier(Mono<T> mono) { this.actual = mono.hasValue() ? List.of(mono.block()) : List.of(); }

        StepVerifier<T> expectNext(T expected) {
            if (expectCount < actual.size() && actual.get(expectCount).equals(expected)) {
                System.out.println("  ✓ expectNext: " + expected);
            } else {
                String got = expectCount < actual.size() ? actual.get(expectCount).toString() : "<none>";
                failures.add("expected " + expected + " got " + got);
            }
            expectCount++;
            return this;
        }

        StepVerifier<T> expectNextMatches(java.util.function.Predicate<T> pred, String desc) {
            if (expectCount < actual.size() && pred.test(actual.get(expectCount))) {
                System.out.println("  ✓ expectNextMatches: " + desc);
            } else {
                failures.add("predicate failed at index " + expectCount + ": " + desc);
            }
            expectCount++;
            return this;
        }

        StepVerifier<T> expectNextCount(int n) {
            if (actual.size() >= expectCount + n) {
                System.out.println("  ✓ expectNextCount(" + n + ")");
                expectCount += n;
            } else {
                failures.add("expected " + n + " more but only " + (actual.size() - expectCount) + " left");
            }
            return this;
        }

        void verifyComplete() {
            if (!failures.isEmpty()) throw new AssertionError("StepVerifier failed:\n  " + String.join("\n  ", failures));
            if (expectCount != actual.size())
                throw new AssertionError("Expected stream to complete after " + expectCount + " elements but had " + actual.size());
            System.out.println("  ✓ verifyComplete()");
        }

        static <T> StepVerifier<T> create(Flux<T> flux) { return new StepVerifier<>(flux); }
        static <T> StepVerifier<T> create(Mono<T> mono) { return new StepVerifier<>(mono); }
    }

    public static void main(String[] args) {
        System.out.println("=== @DataR2dbcTest Demo ===\n");

        InMemoryR2dbcDb db = new InMemoryR2dbcDb();

        // Test 1: findByCustomer
        System.out.println("--- Test 1: findByCustomer (Flux) ---");
        db.insert(new Order("alice", 99.99)).block();
        db.insert(new Order("alice", 149.00)).block();
        db.insert(new Order("bob",   49.99)).block();

        StepVerifier.create(db.findByCustomer("alice"))
            .expectNextMatches(o -> "alice".equals(o.customer()) && o.total() == 99.99, "first alice order")
            .expectNextMatches(o -> "alice".equals(o.customer()) && o.total() == 149.00,"second alice order")
            .verifyComplete();

        db.clean();

        // Test 2: findById found
        System.out.println("\n--- Test 2: findById (Mono — found) ---");
        Order saved = db.insert(new Order("carol", 75.00)).block();

        StepVerifier.create(db.findById(saved.id()))
            .expectNextMatches(o -> "carol".equals(o.customer()), "carol's order by id")
            .verifyComplete();

        db.clean();

        // Test 3: findById not found (empty Mono)
        System.out.println("\n--- Test 3: findById (Mono — empty) ---");
        StepVerifier.create(db.findById(999L))
            .verifyComplete(); // no elements emitted — verifyComplete with expectCount=0 and actual=[]

        db.clean();

        // Test 4: findAll count
        System.out.println("\n--- Test 4: findAll (Flux count) ---");
        db.insert(new Order("dave",  10.0)).block();
        db.insert(new Order("eve",   20.0)).block();
        db.insert(new Order("frank", 30.0)).block();

        StepVerifier.create(db.findAll())
            .expectNextCount(3)
            .verifyComplete();

        System.out.println("\n--- Key @DataR2dbcTest notes ---");
        System.out.println("• No automatic @Transactional rollback — clean DB manually or use @Sql");
        System.out.println("• StepVerifier (from reactor-test) is the standard reactive assertion tool");
        System.out.println("• template.insert(entity).block() for setup is acceptable in test code");
        System.out.println("• Add io.r2dbc:r2dbc-h2 to test classpath for H2 R2DBC support");
        System.out.println("• @AutoConfigureTestDatabase(replace=NONE) + Testcontainers for real DB");
    }
}
```

**How to run:** `java DataR2dbcTestDemo.java`

## 6. Walkthrough

- **`StepVerifier.create(flux)`**: subscribes to the reactive pipeline and records all emitted elements. `.expectNextMatches(predicate)` asserts on each element in order. `.verifyComplete()` asserts there are no more elements and the stream completed without error.
- **`findByCustomer` (Flux)**: emits two Alice orders in insertion order. `StepVerifier` asserts on each one individually. If the order or count is wrong, the step fails with a clear message.
- **`findById` found (Mono)**: a `Mono<Order>` that emits exactly one element. `StepVerifier` expects one matching element then `onComplete`.
- **`findById` not found (empty Mono)**: `Mono.empty()` emits nothing and completes. `StepVerifier` with no `.expectNext()` before `.verifyComplete()` asserts the empty case.
- **No rollback note**: unlike `@DataJpaTest`, `@DataR2dbcTest` does not have automatic transaction rollback in earlier Spring Boot versions. You must clean the database manually (e.g., `repo.deleteAll().block()` in `@AfterEach`).

## 7. Gotchas & takeaways

> `@DataR2dbcTest` does **not** add `@Transactional` to test methods by default — there is no automatic rollback. Clean your database in `@BeforeEach` or `@AfterEach` using `repo.deleteAll().block()` or `@Sql` to avoid test pollution.

> H2 R2DBC requires the `io.r2dbc:r2dbc-h2` driver on the test classpath. Without it, `@DataR2dbcTest` will fail to configure the connection factory. Add it as a test dependency separately from the production R2DBC driver.

- `StepVerifier` is from `io.projectreactor:reactor-test` — a separate dependency included in `spring-boot-starter-test`.
- `StepVerifier.create(flux).expectNextCount(n).verifyComplete()` is the most concise way to assert count.
- `R2dbcEntityTemplate` supports fluent reactive queries: `template.select(Order.class).from("orders").matching(where("customer").is("alice")).all()`.
- `@AutoConfigureTestDatabase(replace = Replace.NONE)` + `@Testcontainers` for PostgreSQL R2DBC tests.
