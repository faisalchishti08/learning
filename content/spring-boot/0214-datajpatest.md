---
card: spring-boot
gi: 214
slug: datajpatest
title: "@DataJpaTest"
---

## 1. What it is

`@DataJpaTest` is a Spring Boot test slice that loads only the JPA layer. It configures an in-memory H2 database (by default), scans `@Repository` beans, configures `EntityManager` and `TestEntityManager`, and wraps each test in a transaction that is rolled back at the end. It does NOT load `@Service`, `@Controller`, or web auto-configuration. It is the standard tool for testing JPA repositories and custom JPQL/native queries.

## 2. Why & when

Use `@DataJpaTest` to test:
- Custom query methods (`@Query`, named queries, derived queries).
- Entity mappings — constraints, lazy loading, cascade rules.
- Repository finder methods you wrote manually.
- Pagination and sorting (`Pageable`, `Sort`).

Do NOT use it for testing service logic or controller behavior — those are separate concerns. Because each test rolls back its transaction, the database is always clean at the start of every test method without manual truncation.

## 3. Core concept

```java
@DataJpaTest
class OrderRepositoryTest {

    @Autowired OrderRepository repo;
    @Autowired TestEntityManager em;

    @Test
    void findByCustomer_returnsOrders() {
        // Arrange: persist test data directly via TestEntityManager
        em.persist(new Order("alice", 99.99));
        em.persist(new Order("alice", 149.00));
        em.persist(new Order("bob",   49.99));
        em.flush();

        // Act
        List<Order> aliceOrders = repo.findByCustomer("alice");

        // Assert
        assertThat(aliceOrders).hasSize(2);
        assertThat(aliceOrders).allMatch(o -> "alice".equals(o.getCustomer()));
    }

    @Test
    void findByTotalGreaterThan_returnsFiltered() {
        em.persist(new Order("carol", 200.00));
        em.persist(new Order("dave",  50.00));
        em.flush();

        var expensive = repo.findByTotalGreaterThan(100.0);
        assertThat(expensive).hasSize(1);
        assertThat(expensive.get(0).getCustomer()).isEqualTo("carol");
    }
}
```

**Using real database (Testcontainers):**
```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = Replace.NONE) // don't replace with H2
@Testcontainers
class OrderRepositoryPostgresTest {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");
    ...
}
```

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@DataJpaTest loads JPA repositories and TestEntityManager against an in-memory H2 database; each test runs in a transaction rolled back on completion; no web layer or service beans">
  <!-- Test -->
  <rect x="10" y="72" width="145" height="55" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="82" y="94" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataJpaTest</text>
  <text x="82" y="109" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">em.persist(entity)</text>
  <text x="82" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">repo.findByCustomer(..)</text>

  <!-- Arrow -->
  <line x1="157" y1="99" x2="205" y2="99" stroke="#6db33f" stroke-width="1.5" marker-end="url(#dja)"/>

  <!-- JPA slice -->
  <rect x="210" y="25" width="250" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataJpaTest Slice</text>
  <rect x="223" y="58" width="224" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="75" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@Repository beans + EntityManager</text>
  <rect x="223" y="91" width="224" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">TestEntityManager (test-only wrapper)</text>
  <rect x="223" y="124" width="224" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="335" y="141" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Flyway / Liquibase auto-run</text>

  <!-- Arrow to DB -->
  <line x1="462" y1="99" x2="520" y2="99" stroke="#6db33f" stroke-width="1.5" marker-end="url(#djb)"/>

  <!-- DB -->
  <rect x="525" y="55" width="145" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">H2 (in-memory)</text>
  <text x="597" y="95" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">auto-created schema</text>
  <text x="597" y="109" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Transactional test</text>
  <text x="597" y="123" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ROLLBACK after each</text>
  <text x="597" y="137" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Test method</text>

  <text x="335" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ Web, Security, Service, Kafka, Redis excluded; no HTTP layer</text>

  <defs>
    <marker id="dja" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="djb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`TestEntityManager` seeds test data; `OrderRepository` queries H2; each test rolls back — clean state for every test method.

## 5. Runnable example

```java
// DataJpaTestDemo.java — simulates @DataJpaTest patterns with in-memory storage
// How to run: java DataJpaTestDemo.java  (JDK 17+, no dependencies)
// Real use: @DataJpaTest with @Autowired OrderRepository + TestEntityManager

import java.util.*;
import java.util.stream.Collectors;

public class DataJpaTestDemo {

    record Order(Long id, String customer, double total, String status) {
        Order(String customer, double total) { this(null, customer, total, "NEW"); }
        Order withId(long id) { return new Order(id, customer, total, status); }
    }

    // Simulates TestEntityManager + JPA repository
    static class TestEntityManager {
        private long seq = 1;
        private final List<Order> db = new ArrayList<>();

        Order persist(Order order) {
            Order saved = order.withId(seq++);
            db.add(saved);
            System.out.println("  [em.persist] " + saved);
            return saved;
        }

        void flush() { System.out.println("  [em.flush] SQL INSERT executed"); }

        void clear() { // simulate em.clear() to evict 1st-level cache
            System.out.println("  [em.clear] L1 cache evicted");
        }

        Order find(long id) { return db.stream().filter(o -> o.id() == id).findFirst().orElse(null); }
        List<Order> all() { return List.copyOf(db); }

        // Simulates transaction rollback at end of @Test
        void rollback() {
            db.clear();
            seq = 1;
            System.out.println("  [ROLLBACK] transaction rolled back — DB clean");
        }
    }

    // Simulates JPA Repository with custom query methods
    static class OrderRepository {
        private final TestEntityManager em;
        OrderRepository(TestEntityManager em) { this.em = em; }

        List<Order> findByCustomer(String customer) {
            return em.all().stream().filter(o -> customer.equals(o.customer())).collect(Collectors.toList());
        }

        List<Order> findByTotalGreaterThan(double threshold) {
            return em.all().stream().filter(o -> o.total() > threshold).collect(Collectors.toList());
        }

        List<Order> findByStatus(String status) {
            return em.all().stream().filter(o -> status.equals(o.status())).collect(Collectors.toList());
        }

        Optional<Order> findById(long id) {
            return Optional.ofNullable(em.find(id));
        }

        long countByCustomer(String customer) {
            return em.all().stream().filter(o -> customer.equals(o.customer())).count();
        }
    }

    static void expect(boolean cond, String msg) {
        if (!cond) throw new AssertionError("FAIL: " + msg);
        System.out.println("  ✓ " + msg);
    }

    static void runTest(String name, TestEntityManager em, Runnable test) {
        System.out.println("\n--- " + name + " ---");
        test.run();
        em.rollback(); // @Transactional rollback after each @Test
    }

    public static void main(String[] args) {
        System.out.println("=== @DataJpaTest Demo ===\n");

        TestEntityManager em = new TestEntityManager();
        OrderRepository repo = new OrderRepository(em);

        // Test 1: findByCustomer
        runTest("findByCustomer", em, () -> {
            em.persist(new Order("alice", 99.99));
            em.persist(new Order("alice", 149.00));
            em.persist(new Order("bob",   49.99));
            em.flush();

            List<Order> aliceOrders = repo.findByCustomer("alice");
            expect(aliceOrders.size() == 2,        "alice has 2 orders");
            expect(aliceOrders.stream().allMatch(o -> "alice".equals(o.customer())),
                   "all orders belong to alice");
            expect(repo.findByCustomer("carol").isEmpty(), "carol has no orders");
        });

        // Test 2: findByTotalGreaterThan (DB is clean after rollback)
        runTest("findByTotalGreaterThan", em, () -> {
            em.persist(new Order("carol", 200.00));
            em.persist(new Order("dave",   50.00));
            em.flush();

            var expensive = repo.findByTotalGreaterThan(100.0);
            expect(expensive.size() == 1,                          "one expensive order");
            expect("carol".equals(expensive.get(0).customer()),    "expensive order is carol's");
        });

        // Test 3: findById + TestEntityManager.find
        runTest("findById", em, () -> {
            Order saved = em.persist(new Order("eve", 75.00));
            em.flush();
            em.clear(); // evict L1 cache — forces real DB load

            Optional<Order> found = repo.findById(saved.id());
            expect(found.isPresent(),                   "order found by id");
            expect(found.get().customer().equals("eve"), "correct customer");
        });

        // Test 4: count
        runTest("countByCustomer", em, () -> {
            em.persist(new Order("frank", 10.00));
            em.persist(new Order("frank", 20.00));
            em.persist(new Order("frank", 30.00));
            em.flush();

            expect(repo.countByCustomer("frank") == 3, "frank has 3 orders");
        });

        System.out.println("\n--- Key @DataJpaTest patterns ---");
        System.out.println("""
@DataJpaTest
class OrderRepositoryTest {
    @Autowired OrderRepository repo;
    @Autowired TestEntityManager em;

    @Test void findByCustomer() {
        em.persist(new Order("alice", 99.99));
        em.flush();
        assertThat(repo.findByCustomer("alice")).hasSize(1);
    }  // transaction rolled back here — H2 is clean for next test

    // Use real DB instead of H2:
    @DataJpaTest
    @AutoConfigureTestDatabase(replace = Replace.NONE)
    class RealDbTest { ... }
}""");
    }
}
```

**How to run:** `java DataJpaTestDemo.java`

## 6. Walkthrough

- **`TestEntityManager.persist` + `flush`**: `persist` adds the entity to the persistence context; `flush` sends the SQL `INSERT` to the database (but within the still-open transaction). In real `@DataJpaTest`, `em.persistFlushFind(entity)` is a convenience method that does all three steps.
- **Rollback between tests** (`em.rollback()`): simulates Spring's `@Transactional` test rollback. After each `@Test` method, Spring rolls back the transaction — the H2 database returns to its pre-test state. No `@AfterEach` cleanup needed.
- **`em.clear()`**: evicts the first-level (session) cache. Without this, `findById` might return the cached entity without hitting the database. `clear()` forces a real SQL `SELECT`.
- **Test isolation**: test 2 starts with an empty database even though test 1 inserted 3 rows — because rollback happens between tests.

## 7. Gotchas & takeaways

> `@DataJpaTest` replaces your configured datasource with H2 by default (`replace=REPLACE_AUTO_CONFIGURED`). If your entities use PostgreSQL-specific types (JSONB, arrays, custom enums) that H2 doesn't support, tests will fail. Add `@AutoConfigureTestDatabase(replace = Replace.NONE)` and provide a real DB via Testcontainers.

> The `@Transactional` rollback only works when the test method and the repository call share the same transaction. If your repository method uses `@Transactional(propagation = REQUIRES_NEW)`, it commits its own transaction and the data IS visible to other tests — rollback won't clean it up.

- `TestEntityManager.persistAndFlush(entity)` is shorthand for `persist` + `flush`.
- `TestEntityManager.persistAndGetId(entity)` persists and returns the generated ID.
- Flyway / Liquibase migrations run automatically if on the classpath — test against the real schema.
- `@Sql("/test-data.sql")` inserts test data from a SQL file before a test method — an alternative to `TestEntityManager`.
- Use `@DataJpaTest` for repository query tests; use `@SpringBootTest` only when you need the full stack (service + repository + controller) integrated.
