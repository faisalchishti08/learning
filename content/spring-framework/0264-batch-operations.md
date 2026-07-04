---
card: spring-framework
gi: 264
slug: batch-operations
title: Batch operations
---

## 1. What it is

**Batch operations** in Spring JDBC send multiple SQL statements to the database in a single network round-trip, instead of one round-trip per statement. Spring provides batch support through:

- `JdbcTemplate.batchUpdate(String sql, List<Object[]>)` — positional parameters, fixed SQL
- `NamedParameterJdbcTemplate.batchUpdate(String sql, SqlParameterSource[])` — named parameters
- `JdbcTemplate.batchUpdate(String... sqls)` — multiple different SQL statements in one batch
- `BatchPreparedStatementSetter` — full control over each row's binding

```java
// Single update: one round-trip per row — 1000 rows = 1000 round-trips
for (Product p : products) jdbc.update("INSERT INTO products ... VALUES(?,?)", p.name(), p.price());

// Batch update: all rows in ONE round-trip
jdbc.batchUpdate("INSERT INTO products(name,price) VALUES(?,?)",
    products.stream().map(p -> new Object[]{p.name(), p.price()}).toList());
```

## 2. Why & when

**Performance**: network latency is the bottleneck for bulk inserts. A round-trip to a local database takes ~0.1 ms; to a remote database 1-10 ms. 10,000 rows × 1 ms = 10 seconds. Batched: one round-trip ≈ 10 ms. That's a 1000× speedup.

**Use batch operations when:**
- Inserting/updating hundreds or thousands of rows at once (data import, bulk processing).
- Running repeated updates with different parameters (price updates, status changes).
- ETL pipelines where throughput matters.

**Limits:**
- Not all JDBC drivers truly batch — MySQL needs `rewriteBatchedStatements=true`.
- Very large batches may exceed driver/server limits — chunk into sub-batches of 500–2000 rows.
- Batch updates don't return per-row generated keys in all drivers (use `executeAndReturnKeys()` via `SimpleJdbcInsert` for key retrieval).

## 3. Core concept

JDBC batch API under the hood:

```
PreparedStatement ps = con.prepareStatement(sql);
for (row : rows) {
    ps.setString(1, row.name());
    ps.setDouble(2, row.price());
    ps.addBatch();          ← queue
}
int[] counts = ps.executeBatch();   ← one round-trip: sends queued rows to DB
```

Spring's `batchUpdate` wrappers handle the open/close lifecycle and exception translation. `BatchPreparedStatementSetter` lets you bind each row's params and declare the batch size — useful when the data comes from a source without a known size upfront.

`int[]` return: each element is the row count for one statement in the batch. JDBC defines two special values:
- `Statement.SUCCESS_NO_INFO` (-2) — statement succeeded but affected row count unknown.
- `Statement.EXECUTE_FAILED` (-3) — statement failed (only in continue-on-error mode).

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Non-batched -->
  <text x="175" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Without batching (3 round-trips)</text>
  <rect x="10" y="30" width="70" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="45" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">App</text>
  <line x1="82" y1="43" x2="126" y2="43" stroke="#8b949e" stroke-width="1" marker-end="url(#arr2)"/>
  <rect x="128" y="30" width="60" height="26" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="158" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">DB ×3</text>
  <text x="104" y="38" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">row1</text>
  <text x="104" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">row2…</text>

  <!-- Batched -->
  <text x="500" y="22" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">With batching (1 round-trip)</text>
  <rect x="360" y="30" width="70" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">App</text>

  <!-- Buffer -->
  <rect x="448" y="30" width="80" height="26" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="488" y="40" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="monospace">PS buffer</text>
  <text x="488" y="52" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">addBatch()×N</text>

  <line x1="433" y1="43" x2="446" y2="43" stroke="#79c0ff" stroke-width="1" marker-end="url(#arr2)"/>
  <line x1="530" y1="43" x2="574" y2="43" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="576" y="30" width="90" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="621" y="40" fill="#6db33f" font-size="7" text-anchor="middle" font-family="monospace">DB (1 call)</text>
  <text x="621" y="52" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">executeBatch()</text>

  <!-- Spring batchUpdate flow -->
  <rect x="30" y="100" width="640" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="122" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JdbcTemplate.batchUpdate(sql, List&lt;Object[]&gt;)</text>
  <line x1="40" y1="128" x2="660" y2="128" stroke="#8b949e" stroke-width="0.5"/>
  <text x="350" y="145" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. prepareStatement(sql)  →  2. for each row: bind params + addBatch()</text>
  <text x="350" y="161" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. executeBatch() → int[]  →  4. close PS  →  5. translate exceptions</text>
  <text x="350" y="177" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">chunked batches: call batchUpdate() multiple times with slices of the list</text>
</svg>

All rows queued via `addBatch()`, then sent with one `executeBatch()` call — one network round-trip.

## 5. Runnable example

Scenario: **bulk product import** — insert a catalogue of products in bulk, update prices in batch, and handle very large sets with chunking.

### Level 1 — Basic

`batchUpdate(String, List<Object[]>)` for bulk INSERT.

```java
// BatchDemo.java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

public class BatchDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:product-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // Build list of Object[] — each array maps to one row's ? placeholders
        List<Object[]> rows = List.of(
            new Object[]{"Widget",  9.99,  "Tools"},
            new Object[]{"Gadget",  24.99, "Electronics"},
            new Object[]{"Gizmo",   14.49, "Electronics"},
            new Object[]{"Relay",   4.99,  "Tools"},
            new Object[]{"Sensor",  49.99, "Electronics"}
        );

        int[] counts = jdbc.batchUpdate(
            "INSERT INTO products(name,price,category) VALUES(?,?,?)", rows);

        System.out.println("Rows inserted: " + counts.length);
        System.out.println("Each row count: " + Arrays.toString(counts));  // [1,1,1,1,1]

        // Verify
        Integer total = jdbc.queryForObject("SELECT COUNT(*) FROM products", Integer.class);
        System.out.println("Total in DB: " + total);
    }
}
```

`product-schema.sql`: `CREATE TABLE products (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price DOUBLE, category VARCHAR(80));`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. BatchDemo.java`

`batchUpdate` returns `int[]` where each element is the affected-row count for that position. All 5 INSERTs are queued with `addBatch()` and sent to H2 in a single `executeBatch()` call.

---

### Level 2 — Intermediate

`BatchPreparedStatementSetter` for full control + batch UPDATE.

```java
// BatchDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import java.util.*;

record Product(String name, double price, String category) {}

public class BatchDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:product-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        List<Product> products = List.of(
            new Product("Widget",  9.99,  "Tools"),
            new Product("Gadget",  24.99, "Electronics"),
            new Product("Gizmo",   14.49, "Electronics"),
            new Product("Relay",   4.99,  "Tools"),
            new Product("Sensor",  49.99, "Electronics")
        );

        // BatchPreparedStatementSetter — full type control, no Object[] boxing
        int[] inserts = jdbc.batchUpdate(
            "INSERT INTO products(name,price,category) VALUES(?,?,?)",
            new BatchPreparedStatementSetter() {
                @Override
                public void setValues(PreparedStatement ps, int i) throws SQLException {
                    Product p = products.get(i);
                    ps.setString(1, p.name());
                    ps.setDouble(2, p.price());
                    ps.setString(3, p.category());
                }
                @Override public int getBatchSize() { return products.size(); }
            });
        System.out.println("Inserted: " + inserts.length + " rows");

        // Batch UPDATE — raise prices 10% for Electronics
        List<Object[]> updates = jdbc.queryForList(
                "SELECT id FROM products WHERE category=?", "Electronics")
            .stream()
            .map(r -> new Object[]{r.get("ID")})
            .toList();

        int[] updated = jdbc.batchUpdate(
            "UPDATE products SET price = ROUND(price*1.10,2) WHERE id=?", updates);
        System.out.println("Updated Electronics prices: " + updated.length + " rows");

        jdbc.queryForList("SELECT name,price,category FROM products ORDER BY name", Map.class)
            .forEach(r -> System.out.printf("  %-10s $%.2f  %s%n",
                r.get("NAME"), r.get("PRICE"), r.get("CATEGORY")));
    }
}
```

How to run: same classpath

`BatchPreparedStatementSetter` uses typed `ps.setString/setDouble` instead of `Object[]` — avoids boxing and works cleanly with `null` values (use `ps.setNull(i, Types.DOUBLE)`). `getBatchSize()` tells Spring how many rows to process.

---

### Level 3 — Advanced

Chunked batch insert for very large datasets + `InterruptibleBatchPreparedStatementSetter`.

```java
// BatchDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;
import java.util.stream.*;

record Product(String name, double price, String category) {}

public class BatchDemo {

    static final int CHUNK_SIZE = 3;  // small for demo; use 500–2000 in production

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:product-schema.sql")
            .build();
    }

    // Chunk a list into sub-lists of maxSize
    static <T> List<List<T>> chunk(List<T> list, int size) {
        List<List<T>> result = new ArrayList<>();
        for (int i = 0; i < list.size(); i += size)
            result.add(list.subList(i, Math.min(i + size, list.size())));
        return result;
    }

    public static void main(String[] args) {
        JdbcTemplate jdbc = new JdbcTemplate(buildDs());

        // Simulate 10 products to import
        List<Product> catalogue = IntStream.rangeClosed(1, 10)
            .mapToObj(i -> new Product("Prod-" + i, 10.0 * i,
                i % 2 == 0 ? "Electronics" : "Tools"))
            .toList();

        int totalInserted = 0;
        for (List<Product> chunk : chunk(catalogue, CHUNK_SIZE)) {
            int[] counts = jdbc.batchUpdate(
                "INSERT INTO products(name,price,category) VALUES(?,?,?)",
                chunk.stream()
                    .map(p -> new Object[]{p.name(), p.price(), p.category()})
                    .toList());
            totalInserted += counts.length;
            System.out.println("Chunk inserted: " + counts.length + " rows");
        }
        System.out.println("Total inserted: " + totalInserted);

        // Multi-statement batch (different SQL in one batch)
        String[] ddlBatch = {
            "UPDATE products SET price = ROUND(price*0.9,2) WHERE category='Tools'",
            "UPDATE products SET price = ROUND(price*1.05,2) WHERE category='Electronics'"
        };
        int[] multiCounts = jdbc.batchUpdate(ddlBatch);
        System.out.println("Multi-statement batch: " + Arrays.toString(multiCounts));

        // Verify final state
        jdbc.queryForList(
            "SELECT category, COUNT(*) cnt, ROUND(AVG(price),2) avg_price FROM products GROUP BY category",
            Map.class)
        .forEach(r -> System.out.printf("  %-12s count=%-3s avg=$%s%n",
            r.get("CATEGORY"), r.get("CNT"), r.get("AVG_PRICE")));
    }
}
```

How to run: same classpath

Chunking keeps each batch within the JDBC driver's limit and prevents out-of-memory issues when the input is a database cursor or file stream. `batchUpdate(String... sqls)` sends multiple *different* SQL statements in one batch — no parameter binding — useful for running multiple DDL or admin statements atomically in one round-trip.

## 6. Walkthrough

**Level 3 — chunked batch insert (execution order):**

1. **`catalogue`**: 10 `Product` objects created by `IntStream`.
2. **`chunk(catalogue, 3)`**: produces `[[P1,P2,P3],[P4,P5,P6],[P7,P8,P9],[P10]]` — 4 sub-lists.
3. **First chunk `[P1,P2,P3]`**:
   - `jdbc.batchUpdate(sql, List<Object[]>)` called with 3 rows.
   - `JdbcTemplate` calls `con.prepareStatement("INSERT INTO products(name,price,category) VALUES(?,?,?)")`.
   - Iterates: `ps.setString(1,"Prod-1"); ps.setDouble(2,10.0); ps.setString(3,"Tools"); ps.addBatch()` — × 3 rows.
   - `ps.executeBatch()` → one network call → H2 inserts 3 rows → `int[]{1,1,1}`.
4. **Repeat for chunks 2, 3, 4** — total 4 `executeBatch()` calls (vs. 10 individual `executeUpdate()` calls without batching).
5. **Multi-statement batch `batchUpdate(String[])`**:
   - `con.createStatement()` (no PreparedStatement needed).
   - `stmt.addBatch("UPDATE products SET price = ROUND(price*0.9,2) WHERE category='Tools'")`.
   - `stmt.addBatch("UPDATE products SET price = ROUND(price*1.05,2) WHERE category='Electronics'")`.
   - `stmt.executeBatch()` — one call → returns `int[]{5, 5}` (5 Tools, 5 Electronics rows updated).

```
Chunk 1 — JDBC:
  prepareStatement("INSERT INTO products(name,price,category) VALUES(?,?,?)")
  addBatch() × 3
  executeBatch() → int[]{1,1,1}  [1 network call]

Multi-statement:
  addBatch("UPDATE ... WHERE category='Tools'")
  addBatch("UPDATE ... WHERE category='Electronics'")
  executeBatch() → int[]{5,5}  [1 network call, 2 SQL statements]
```

## 7. Gotchas & takeaways

> **MySQL requires `rewriteBatchedStatements=true`** in the JDBC connection URL for true server-side batching. Without it, the driver sends statements one-by-one despite the batch API — you get the bookkeeping overhead but none of the speed.

> **`int[]` may contain `Statement.SUCCESS_NO_INFO (-2)`** for drivers that don't report affected counts per statement (e.g., Oracle in some modes). Don't assume each element is 1 — check the JDBC driver docs for your database.

> **Error handling in batches**: by default, the first failing statement stops the batch and rolls back (if inside a transaction). Use `InterruptibleBatchPreparedStatementSetter` if you need early exit based on business logic during binding.

- Batch = queue rows with `addBatch()`, flush with `executeBatch()` — one round-trip regardless of row count.
- Chunk large datasets (500–2000 rows per call) to stay within driver/server limits.
- `BatchPreparedStatementSetter` gives type-safe binding; `List<Object[]>` is quicker for simple cases.
- `batchUpdate(String[])` batches different SQL statements in one call — no params.
- MySQL: add `rewriteBatchedStatements=true` to the JDBC URL or you won't get true batching.
