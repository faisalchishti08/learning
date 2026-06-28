---
card: spring-boot
gi: 215
slug: datajdbctest-jdbctest
title: "@DataJdbcTest / @JdbcTest"
---

## 1. What it is

`@DataJdbcTest` loads the Spring Data JDBC layer: JDBC repositories, `JdbcTemplate`, `NamedParameterJdbcTemplate`, and an in-memory H2 database. It does NOT load JPA, web, or services. `@JdbcTest` is the lighter sibling — it loads only `JdbcTemplate` / `NamedParameterJdbcTemplate` (no Spring Data JDBC repositories), useful when testing raw SQL queries via `JdbcTemplate` directly. Both roll back transactions after each test.

## 2. Why & when

Use `@DataJdbcTest` when you use Spring Data JDBC (`CrudRepository`, `PagingAndSortingRepository`) and want to test:
- Derived query methods.
- Custom `@Query` SQL in repositories.
- Entity mapping (aggregates, embedded objects).

Use `@JdbcTest` when you use raw `JdbcTemplate` (no Spring Data) and want to test:
- `JdbcTemplate.queryForObject(sql, type)` calls.
- `NamedParameterJdbcTemplate` queries.
- `RowMapper` implementations.

Neither tests JPA — use `@DataJpaTest` for Hibernate/JPA.

## 3. Core concept

**`@DataJdbcTest`:**
```java
@DataJdbcTest
class OrderJdbcRepositoryTest {

    @Autowired OrderJdbcRepository repo;
    @Autowired JdbcTemplate jdbc;

    @Test
    void findByCustomer_returnsRows() {
        // Seed data using JdbcTemplate (Spring Data JDBC has no TestEntityManager)
        jdbc.update("INSERT INTO orders (customer, total) VALUES (?, ?)", "alice", 99.99);
        jdbc.update("INSERT INTO orders (customer, total) VALUES (?, ?)", "alice", 49.99);

        List<Order> orders = repo.findByCustomer("alice");
        assertThat(orders).hasSize(2);
    }
}
```

**`@JdbcTest` (raw JdbcTemplate):**
```java
@JdbcTest
class OrderDaoTest {

    @Autowired JdbcTemplate jdbc;

    @Test
    void countOrders_returnsCorrectCount() {
        jdbc.update("INSERT INTO orders (customer, total) VALUES (?,?)", "bob", 100.0);
        int count = jdbc.queryForObject("SELECT COUNT(*) FROM orders WHERE customer=?",
                                        Integer.class, "bob");
        assertThat(count).isEqualTo(1);
    }
}
```

Schema is loaded from `schema.sql` / `data.sql` in `src/test/resources` or `src/main/resources` by default.

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@DataJdbcTest loads Spring Data JDBC repositories and JdbcTemplate against H2; @JdbcTest loads only JdbcTemplate; both roll back each test transaction">
  <!-- Left: DataJdbcTest -->
  <rect x="10" y="30" width="295" height="135" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="157" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataJdbcTest</text>
  <rect x="23" y="63" width="270" height="24" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="157" y="79" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Spring Data JDBC repositories (@CrudRepository)</text>
  <rect x="23" y="94" width="270" height="24" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="157" y="110" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JdbcTemplate + NamedParameterJdbcTemplate</text>
  <rect x="23" y="125" width="270" height="24" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="157" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">H2 (in-memory) — schema.sql auto-loaded</text>
  <text x="157" y="160" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">No JPA / Hibernate, no web layer, no services</text>

  <!-- Arrow to H2 -->
  <line x1="307" y1="98" x2="355" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#dda)"/>

  <!-- H2 -->
  <rect x="360" y="68" width="145" height="62" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="432" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">H2 In-Memory</text>
  <text x="432" y="104" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@Transactional test</text>
  <text x="432" y="119" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ROLLBACK after each @Test</text>

  <!-- Right: JdbcTest -->
  <rect x="520" y="30" width="150" height="135" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="595" y="52" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JdbcTest</text>
  <rect x="532" y="63" width="126" height="24" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="595" y="79" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JdbcTemplate only</text>
  <rect x="532" y="94" width="126" height="24" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="595" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">No Spring Data repositories</text>
  <text x="595" y="135" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Raw SQL via JdbcTemplate</text>
  <text x="595" y="148" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">useful for DAO / RowMapper tests</text>

  <line x1="520" y1="98" x2="507" y2="98" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ddb)"/>

  <defs>
    <marker id="dda" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ddb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`@DataJdbcTest` tests JDBC repositories; `@JdbcTest` tests raw `JdbcTemplate` — both use H2 with automatic transaction rollback.

## 5. Runnable example

```java
// DataJdbcTestDemo.java — simulates @DataJdbcTest and @JdbcTest patterns
// How to run: java DataJdbcTestDemo.java  (JDK 17+, no dependencies)
// Real use: @DataJdbcTest + @Autowired OrderRepository + JdbcTemplate

import java.util.*;
import java.util.stream.Collectors;

public class DataJdbcTestDemo {

    record Order(Long id, String customer, double total) {
        Order(String customer, double total) { this(null, customer, total); }
    }

    // Simulates H2 in-memory DB (schema pre-loaded)
    static class InMemoryDb {
        private long seq = 1;
        final List<Order> orders = new ArrayList<>();

        long insert(String customer, double total) {
            long id = seq++;
            orders.add(new Order(id, customer, total));
            System.out.println("  [SQL] INSERT INTO orders (customer,total) VALUES ('" + customer + "'," + total + ") → id=" + id);
            return id;
        }

        List<Map<String, Object>> query(String sql, Object... params) {
            System.out.println("  [SQL] " + sql + " params=" + Arrays.toString(params));
            // Simplified SQL parsing for demo
            if (sql.contains("customer=?") || sql.contains("customer = ?")) {
                String cust = (String) params[0];
                return orders.stream()
                    .filter(o -> cust.equals(o.customer()))
                    .map(o -> Map.of("id", o.id(), "customer", o.customer(), "total", o.total()))
                    .collect(Collectors.toList());
            }
            if (sql.contains("COUNT(*)") && sql.contains("customer=?")) {
                String cust = (String) params[0];
                long cnt = orders.stream().filter(o -> cust.equals(o.customer())).count();
                return List.of(Map.of("count", cnt));
            }
            if (sql.contains("total >") || sql.contains("total>")) {
                double threshold = (double) params[0];
                return orders.stream()
                    .filter(o -> o.total() > threshold)
                    .map(o -> Map.of("id", o.id(), "customer", o.customer(), "total", o.total()))
                    .collect(Collectors.toList());
            }
            return orders.stream()
                .map(o -> Map.of("id", o.id(), "customer", o.customer(), "total", o.total()))
                .collect(Collectors.toList());
        }

        void rollback() {
            orders.clear(); seq = 1;
            System.out.println("  [ROLLBACK] transaction rolled back");
        }
    }

    // Spring Data JDBC repository simulation
    static class OrderJdbcRepository {
        private final InMemoryDb db;
        OrderJdbcRepository(InMemoryDb db) { this.db = db; }

        List<Map<String, Object>> findByCustomer(String customer) {
            return db.query("SELECT * FROM orders WHERE customer=?", customer);
        }

        List<Map<String, Object>> findByTotalGreaterThan(double t) {
            return db.query("SELECT * FROM orders WHERE total > ?", t);
        }
    }

    static void expect(boolean cond, String msg) {
        if (!cond) throw new AssertionError("FAIL: " + msg);
        System.out.println("  ✓ " + msg);
    }

    static void runTest(String name, InMemoryDb db, Runnable test) {
        System.out.println("\n--- " + name + " ---");
        test.run();
        db.rollback();
    }

    public static void main(String[] args) {
        System.out.println("=== @DataJdbcTest / @JdbcTest Demo ===\n");

        InMemoryDb db = new InMemoryDb();
        OrderJdbcRepository repo = new OrderJdbcRepository(db);

        // === @DataJdbcTest scenarios ===
        System.out.println("=== @DataJdbcTest ===");

        runTest("findByCustomer", db, () -> {
            db.insert("alice", 99.99);
            db.insert("alice", 49.99);
            db.insert("bob",   200.00);

            var aliceOrders = repo.findByCustomer("alice");
            expect(aliceOrders.size() == 2, "alice has 2 orders");
            expect(aliceOrders.stream().allMatch(r -> "alice".equals(r.get("customer"))),
                   "all are alice's");
        });

        runTest("findByTotalGreaterThan", db, () -> {
            db.insert("carol", 500.00);
            db.insert("dave",   30.00);
            db.insert("eve",   150.00);

            var expensive = repo.findByTotalGreaterThan(100.0);
            expect(expensive.size() == 2, "2 orders above 100");
        });

        // === @JdbcTest: raw JdbcTemplate ===
        System.out.println("\n=== @JdbcTest (raw JdbcTemplate) ===");

        runTest("JdbcTemplate INSERT and COUNT", db, () -> {
            db.insert("frank", 75.00);
            db.insert("frank", 25.00);

            // Simulate jdbc.queryForObject("SELECT COUNT(*) FROM orders WHERE customer=?", Integer.class, "frank")
            var result = db.query("SELECT COUNT(*) FROM orders WHERE customer=?", "frank");
            long count = (long) result.get(0).get("count");
            expect(count == 2, "frank has 2 orders");
        });

        runTest("RowMapper simulation", db, () -> {
            db.insert("grace", 88.88);
            var rows = db.query("SELECT * FROM orders WHERE customer=?", "grace");
            // Simulate a RowMapper mapping row → Order
            Order mapped = new Order(
                (Long)  rows.get(0).get("id"),
                (String)rows.get(0).get("customer"),
                (double)rows.get(0).get("total"));
            expect("grace".equals(mapped.customer()), "RowMapper maps customer");
            expect(mapped.total() == 88.88,           "RowMapper maps total");
        });

        System.out.println("\n--- Schema setup (schema.sql) ---");
        System.out.println("-- src/test/resources/schema.sql");
        System.out.println("CREATE TABLE orders (");
        System.out.println("  id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,");
        System.out.println("  customer VARCHAR(255) NOT NULL,");
        System.out.println("  total    DECIMAL(10,2) NOT NULL");
        System.out.println(");");
    }
}
```

**How to run:** `java DataJdbcTestDemo.java`

## 6. Walkthrough

- **`@DataJdbcTest` findByCustomer**: seeds two Alice orders and one Bob order using `db.insert()` (simulates `JdbcTemplate.update(sql,...)`). Then calls the Spring Data repository's derived `findByCustomer` — executed as a SQL `SELECT WHERE customer=?`. Verifies count and that all results belong to Alice.
- **`findByTotalGreaterThan`**: demonstrates a numeric threshold query. `@DataJdbcTest` supports `@Query("SELECT * FROM orders WHERE total > :threshold")` annotations on repository interfaces.
- **`@JdbcTest` + COUNT**: raw `JdbcTemplate.queryForObject(sql, Integer.class, params)`. This is the preferred way to test DAOs that don't use Spring Data repository interfaces.
- **RowMapper simulation**: `JdbcTemplate.query(sql, rowMapper, params)` maps each `ResultSet` row to a domain object. Testing the `RowMapper` logic is the key use case for `@JdbcTest`.
- **Rollback**: each `runTest` calls `db.rollback()` — analogous to Spring's automatic `@Transactional` rollback after each test.

## 7. Gotchas & takeaways

> `@DataJdbcTest` does **not** support JPA annotations (`@Entity`, `@Column`). Spring Data JDBC uses its own aggregate mapping conventions. If your code uses `@Entity`, use `@DataJpaTest` instead.

> Schema must be set up manually. Unlike `@DataJpaTest` which generates DDL from JPA entities, `@DataJdbcTest` and `@JdbcTest` expect `schema.sql` (or `data.sql`) in `src/test/resources`. If the schema file is missing, `INSERT` statements in tests will fail with "Table not found."

- `@DataJdbcTest` uses H2 by default; override with `@AutoConfigureTestDatabase(replace = Replace.NONE)` + Testcontainers for real-DB tests.
- `@Sql("/test-data.sql")` on a test method executes a SQL file before the test — useful for loading a large seed dataset.
- `NamedParameterJdbcTemplate` is available in both slice types for `:named` parameter queries.
- Both slices are `@Transactional` by default; rollback is automatic — no need for `@AfterEach` cleanup.
