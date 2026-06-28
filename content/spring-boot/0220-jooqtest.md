---
card: spring-boot
gi: 220
slug: jooqtest
title: "@JooqTest"
---

## 1. What it is

`@JooqTest` is a Spring Boot test slice that loads the jOOQ `DSLContext` and an in-memory H2 database. It does NOT load Spring Data JPA repositories, web layers, or services. Use it to test jOOQ-based data access classes — the SQL queries your `DSLContext` generates and the result mapping — in isolation.

## 2. Why & when

Use `@JooqTest` when your application uses jOOQ for SQL query building and you want to test:
- Type-safe SQL queries written with jOOQ's fluent DSL.
- `ResultQuery` → record mapping (jOOQ's `Record` types or your own POJOs via `.into(MyClass.class)`).
- `DSLContext.fetchOne`, `fetchMany`, `fetch` behavior against real SQL.
- Batch insert/update statements.

jOOQ queries can't be meaningfully unit-tested without a real SQL engine because the SQL dialect, type coercions, and result sets are dialect-specific. `@JooqTest` provides a real JDBC connection to H2 without requiring a full application context.

## 3. Core concept

```java
@JooqTest
class OrderDslRepositoryTest {

    @Autowired DSLContext dsl;

    @BeforeEach
    void setup() {
        // Schema must exist (from schema.sql or created in @BeforeEach)
        dsl.execute("CREATE TABLE IF NOT EXISTS orders (" +
                    "id INT PRIMARY KEY AUTO_INCREMENT, customer VARCHAR(255), total DECIMAL)");
    }

    @Test
    void insertAndQuery_returnsCorrectRecords() {
        dsl.execute("INSERT INTO orders (customer, total) VALUES ('alice', 99.99)");
        dsl.execute("INSERT INTO orders (customer, total) VALUES ('alice', 49.99)");

        // jOOQ DSL query (type-safe in real projects using generated classes)
        var records = dsl.fetch("SELECT * FROM orders WHERE customer = ?", "alice");

        assertThat(records).hasSize(2);
        assertThat(records.get(0).get("CUSTOMER", String.class)).isEqualTo("alice");
    }

    @AfterEach
    void teardown() {
        dsl.execute("DROP TABLE IF EXISTS orders");
    }
}
```

In a real project with jOOQ code generation, you'd use type-safe DSL: `dsl.select(ORDERS.CUSTOMER).from(ORDERS).where(ORDERS.CUSTOMER.eq("alice")).fetch()`.

## 4. Diagram

<svg viewBox="0 0 680 175" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@JooqTest loads DSLContext and H2 database; test code calls DSL type-safe queries; H2 executes SQL and returns results; web layer and JPA are excluded">
  <!-- Test -->
  <rect x="10" y="55" width="140" height="70" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JooqTest</text>
  <text x="75" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">dsl.select(ORDERS.ID)</text>
  <text x="75" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  .from(ORDERS)</text>
  <text x="75" y="119" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  .where(CUSTOMER.eq("x"))</text>

  <!-- Arrow -->
  <line x1="152" y1="90" x2="200" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jqa)"/>

  <!-- DSLContext slice -->
  <rect x="205" y="30" width="235" height="120" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="322" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JooqTest Slice</text>
  <rect x="218" y="63" width="210" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="322" y="80" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DSLContext (H2 SQL dialect)</text>
  <rect x="218" y="96" width="210" height="26" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="322" y="113" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">DataSource (H2 in-memory)</text>
  <rect x="218" y="129" width="210" height="16" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="322" y="141" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">schema.sql auto-run</text>

  <!-- Arrow to H2 -->
  <line x1="442" y1="90" x2="495" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jqb)"/>

  <!-- H2 -->
  <rect x="500" y="55" width="170" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="78" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">H2 In-Memory</text>
  <text x="585" y="95" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">H2 SQL dialect</text>
  <text x="585" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Transactional rollback</text>

  <text x="340" y="167" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ JPA, web, security, services excluded — pure SQL testing</text>

  <defs>
    <marker id="jqa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jqb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`DSLContext` translates type-safe DSL to SQL; H2 executes it; results are mapped back — same pipeline as production, faster than a full context.

## 5. Runnable example

```java
// JooqTestDemo.java — simulates @JooqTest DSLContext query patterns
// How to run: java JooqTestDemo.java  (JDK 17+, no dependencies)
// Real use: @JooqTest + @Autowired DSLContext; uses jOOQ generated code for type safety

import java.util.*;
import java.util.stream.Collectors;

public class JooqTestDemo {

    record OrderRow(int id, String customer, double total) {}

    // Simulates DSLContext backed by H2 (all queries go to in-memory store)
    static class DSLContext {
        private int seq = 1;
        private final List<OrderRow> db = new ArrayList<>();

        // Simulates dsl.execute(sql, params)
        int execute(String sql, Object... params) {
            System.out.println("  [SQL] " + sql.trim() + " " + Arrays.toString(params));
            if (sql.startsWith("CREATE TABLE")) return 0;
            if (sql.startsWith("DROP TABLE"))   { db.clear(); seq = 1; return 0; }
            if (sql.toUpperCase().startsWith("INSERT")) {
                String customer = (String) params[0];
                double total    = ((Number) params[1]).doubleValue();
                db.add(new OrderRow(seq++, customer, total));
                return 1;
            }
            return 0;
        }

        // Simulates dsl.fetch(sql, params) → List of records
        List<OrderRow> fetch(String sql, Object... params) {
            System.out.println("  [SQL] " + sql.trim() + " " + Arrays.toString(params));
            String upper = sql.toUpperCase();
            if (upper.contains("WHERE CUSTOMER = ?")) {
                String customer = (String) params[0];
                return db.stream().filter(r -> customer.equals(r.customer())).collect(Collectors.toList());
            }
            if (upper.contains("WHERE TOTAL >")) {
                double threshold = ((Number) params[0]).doubleValue();
                return db.stream().filter(r -> r.total() > threshold).collect(Collectors.toList());
            }
            return List.copyOf(db);
        }

        // Simulates dsl.fetchOne(sql, params)
        Optional<OrderRow> fetchOne(String sql, Object... params) {
            return fetch(sql, params).stream().findFirst();
        }

        // Simulates type-safe jOOQ DSL (simplified representation)
        SelectBuilder select(String... cols) { return new SelectBuilder(this, cols); }

        int count(String table, String whereClause, Object param) {
            System.out.println("  [SQL] SELECT COUNT(*) FROM " + table + " WHERE " + whereClause + " " + param);
            String customer = (String) param;
            return (int) db.stream().filter(r -> customer.equals(r.customer())).count();
        }

        void rollback() { db.clear(); seq = 1; System.out.println("  [ROLLBACK]"); }
    }

    // Simulates jOOQ fluent DSL builder
    static class SelectBuilder {
        private final DSLContext ctx;
        private final String[] cols;
        private String whereCustomer;
        private Double whereTotal;

        SelectBuilder(DSLContext ctx, String[] cols) { this.ctx = ctx; this.cols = cols; }
        SelectBuilder from(String table) { return this; }
        SelectBuilder where(String col, String val) { this.whereCustomer = val; return this; }
        SelectBuilder whereGreaterThan(double t)    { this.whereTotal = t; return this; }

        List<OrderRow> fetch() {
            if (whereCustomer != null) return ctx.fetch("SELECT FROM orders WHERE CUSTOMER = ?", whereCustomer);
            if (whereTotal    != null) return ctx.fetch("SELECT FROM orders WHERE TOTAL > ?", whereTotal);
            return ctx.fetch("SELECT FROM orders");
        }
        Optional<OrderRow> fetchOne() { return fetch().stream().findFirst(); }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    static void runTest(String name, DSLContext dsl, Runnable test) {
        System.out.println("\n--- " + name + " ---");
        test.run();
        dsl.rollback();
    }

    public static void main(String[] args) {
        System.out.println("=== @JooqTest / DSLContext Demo ===\n");

        DSLContext dsl = new DSLContext();

        runTest("Basic INSERT and SELECT", dsl, () -> {
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "alice", 99.99);
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "alice", 49.99);
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "bob",   200.00);

            List<OrderRow> aliceOrders = dsl.fetch("SELECT * FROM orders WHERE CUSTOMER = ?", "alice");
            expect(aliceOrders.size() == 2,                    "alice has 2 orders");
            expect(aliceOrders.stream().allMatch(r -> "alice".equals(r.customer())), "all are alice's");
        });

        runTest("fetchOne returns single result", dsl, () -> {
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "carol", 150.00);
            Optional<OrderRow> row = dsl.fetchOne("SELECT * FROM orders WHERE CUSTOMER = ?", "carol");
            expect(row.isPresent(),                            "carol's order found");
            expect(row.get().total() == 150.00,               "correct total");
        });

        runTest("Type-safe DSL builder (jOOQ style)", dsl, () -> {
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "dave", 500.00);
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "eve",   30.00);

            // Simulates: dsl.select(ORDERS.asterisk()).from(ORDERS).where(ORDERS.TOTAL.gt(100.0)).fetch()
            List<OrderRow> expensive = dsl.select("*").from("orders").whereGreaterThan(100.0).fetch();
            expect(expensive.size() == 1,                      "one expensive order");
            expect("dave".equals(expensive.get(0).customer()), "dave's order is expensive");
        });

        runTest("COUNT query", dsl, () -> {
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "frank", 10.0);
            dsl.execute("INSERT INTO orders (customer, total) VALUES (?, ?)", "frank", 20.0);

            int count = dsl.count("orders", "CUSTOMER = ?", "frank");
            expect(count == 2, "frank has 2 orders");
        });

        System.out.println("\n--- Real @JooqTest setup ---");
        System.out.println("""
@JooqTest
class OrderDslRepositoryTest {
    @Autowired DSLContext dsl;

    @Test
    void findByCustomer() {
        // H2 — schema.sql creates the table
        dsl.insertInto(ORDERS)
           .set(ORDERS.CUSTOMER, "alice")
           .set(ORDERS.TOTAL, BigDecimal.valueOf(99.99))
           .execute();

        // Type-safe jOOQ query:
        var records = dsl.selectFrom(ORDERS)
                         .where(ORDERS.CUSTOMER.eq("alice"))
                         .fetch();

        assertThat(records).hasSize(1);
        assertThat(records.get(0).getCustomer()).isEqualTo("alice");
    }   // @Transactional rollback after test
}""");
    }
}
```

**How to run:** `java JooqTestDemo.java`

## 6. Walkthrough

- **INSERT and SELECT** (test 1): `dsl.execute(sql, params)` inserts rows. `dsl.fetch(sql, params)` returns all matching rows. In real jOOQ: `dsl.insertInto(ORDERS).set(ORDERS.CUSTOMER,"alice").execute()` and `dsl.selectFrom(ORDERS).where(ORDERS.CUSTOMER.eq("alice")).fetch()` — fully type-safe, checked at compile time.
- **`fetchOne`** (test 2): expects zero or one row. In jOOQ, `fetchOne()` throws if more than one row is returned — `fetchOptional()` is safer for nullable single-row queries.
- **Type-safe DSL builder** (test 3): demonstrates the jOOQ fluent API pattern. Real jOOQ generates `ORDERS.TOTAL` as a typed `Field<BigDecimal>`, making `ORDERS.TOTAL.gt(100.0)` compile-time safe.
- **COUNT** (test 4): `dsl.count(...)` is a convenience but in real jOOQ: `dsl.fetchCount(ORDERS, ORDERS.CUSTOMER.eq("frank"))` returns an `int`.
- **Rollback**: `@JooqTest` wraps each test in a `@Transactional` transaction that rolls back — clean DB for each test.

## 7. Gotchas & takeaways

> `@JooqTest` uses H2's SQL dialect, which may differ from your production database (PostgreSQL, MySQL). jOOQ SQL dialect is configured per database; H2 may accept SQL that your production DB rejects, or vice versa. Use `@AutoConfigureTestDatabase(replace = Replace.NONE)` + Testcontainers with the real DB for full confidence.

> jOOQ code generation produces classes like `ORDERS`, `ORDERS.ID`, `ORDERS.CUSTOMER` that won't exist in a plain JUnit test. `@JooqTest` loads the application context where these generated DSL classes are on the classpath and the `DSLContext` is configured with the correct dialect.

- `@Transactional` rollback is automatic — each `@Test` method runs in a transaction that rolls back.
- `dsl.fetchExists(ORDERS, ORDERS.CUSTOMER.eq("alice"))` — convenient boolean existence check.
- `dsl.batch(...)` for batch inserts — `@JooqTest` supports testing batch operations.
- For `@JooqTest` with PostgreSQL-specific SQL (RETURNING clause, JSONB, etc.), replace H2 with a Testcontainers `PostgreSQLContainer`.
