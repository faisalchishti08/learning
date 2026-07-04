---
card: spring-framework
gi: 261
slug: simplejdbcinsert-simplejdbccall
title: SimpleJdbcInsert / SimpleJdbcCall
---

## 1. What it is

`SimpleJdbcInsert` and `SimpleJdbcCall` are high-level helpers that read **database metadata** at startup to eliminate hand-written SQL for common operations:

- **`SimpleJdbcInsert`** — inserts a row and optionally retrieves the generated key, with no SQL string required.
- **`SimpleJdbcCall`** — calls a stored procedure or function, using metadata to discover IN/OUT parameters automatically.

```java
// SimpleJdbcInsert — no INSERT SQL needed
Number id = new SimpleJdbcInsert(ds)
    .withTableName("products")
    .usingGeneratedKeyColumns("id")
    .executeAndReturnKey(Map.of("name","Widget","price",9.99));

// SimpleJdbcCall — no CALL SQL needed
Map<String,Object> out = new SimpleJdbcCall(ds)
    .withProcedureName("get_product_stats")
    .execute(Map.of("p_id", 1));
```

Both classes live in `org.springframework.jdbc.core.simple`.

## 2. Why & when

`SimpleJdbcInsert` shines when you insert into the same table from many places and want to avoid writing repetitive `INSERT INTO t (col1,col2,...) VALUES (?,?,...)` SQL. The metadata read at startup means Spring knows the column list — you just pass a `Map` or bean.

`SimpleJdbcCall` is valuable when a DBA owns stored procedures and the Java side just needs to call them without hard-coding the procedure signature in a string.

**When to use:**
- Inserts where retrieving the auto-generated PK matters.
- Calling stored procedures when parameter names are known only at runtime or change across DB environments.
- Teams that want zero SQL strings in Java for CRUD operations.

**When to skip:**
- Complex multi-table INSERTs or INSERT…SELECT — use `JdbcTemplate`.
- When you want explicit SQL for auditability or performance tuning.

## 3. Core concept

**`SimpleJdbcInsert` lifecycle:**

1. Constructor takes a `DataSource` or `JdbcTemplate`.
2. First call to `execute` / `executeAndReturnKey` triggers metadata inspection (`DatabaseMetaData.getColumns(table)`) to discover column names and types.
3. Builds and caches an `INSERT INTO <table> (<cols>) VALUES (<placeholders>)` internally.
4. Delegates to `JdbcTemplate.update()` or `KeyHolder` path.

**`SimpleJdbcCall` lifecycle:**

1. Constructor takes a `DataSource`.
2. First call triggers `DatabaseMetaData.getProcedureColumns(proc)` to discover parameter names, modes (IN/OUT/INOUT), and types.
3. Builds and caches the `{call proc_name(?,?,?)}` escape syntax internally.
4. Calls `JdbcTemplate.call()` with a `CallableStatementCreator`.

Both classes are **not thread-safe after construction** — configure once, use as a singleton or configure in `@PostConstruct`.

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- SimpleJdbcInsert box -->
  <rect x="30" y="30" width="280" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SimpleJdbcInsert</text>
  <line x1="40" y1="58" x2="300" y2="58" stroke="#8b949e" stroke-width="0.5"/>
  <text x="170" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. read DatabaseMetaData.getColumns(table)</text>
  <text x="170" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. build INSERT SQL + placeholders</text>
  <text x="170" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. JdbcTemplate.update() / KeyHolder</text>

  <!-- SimpleJdbcCall box -->
  <rect x="30" y="145" width="280" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="170" y="167" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">SimpleJdbcCall</text>
  <line x1="40" y1="173" x2="300" y2="173" stroke="#8b949e" stroke-width="0.5"/>
  <text x="170" y="191" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. read DatabaseMetaData.getProcedureColumns</text>
  <text x="170" y="207" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. build {call proc(?,?)} escape</text>
  <text x="170" y="223" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. JdbcTemplate.call() + output binding</text>

  <!-- DB -->
  <rect x="500" y="85" width="140" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="570" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Database</text>
  <text x="570" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">H2 / PostgreSQL</text>

  <line x1="312" y1="80" x2="497" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="312" y1="185" x2="497" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
</svg>

Both helpers inspect database metadata once, then cache the generated SQL for all subsequent calls.

## 5. Runnable example

Scenario: a **product catalog** — insert products with auto-generated IDs using `SimpleJdbcInsert`, then call a stored function to compute average price using `SimpleJdbcCall`.

### Level 1 — Basic

`SimpleJdbcInsert` with `execute()` (no key retrieval).

```java
// SimpleJdbcDemo.java
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.Map;
import org.springframework.jdbc.core.JdbcTemplate;

public class SimpleJdbcDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:product-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();

        // Build once — configure table name
        SimpleJdbcInsert insert = new SimpleJdbcInsert(ds)
            .withTableName("products");

        // Insert rows — no SQL string, just a Map of column→value
        insert.execute(Map.of("name", "Widget",  "price", 9.99,  "category", "Tools"));
        insert.execute(Map.of("name", "Gadget",  "price", 24.99, "category", "Electronics"));
        insert.execute(Map.of("name", "Gizmo",   "price", 14.49, "category", "Electronics"));

        // Verify via plain JdbcTemplate
        JdbcTemplate jt = new JdbcTemplate(ds);
        Integer count = jt.queryForObject("SELECT COUNT(*) FROM products", Integer.class);
        System.out.println("Product count: " + count);   // 3
    }
}
```

`product-schema.sql`:
```sql
CREATE TABLE products (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100),
  price DOUBLE,
  category VARCHAR(80)
);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. SimpleJdbcDemo.java`

`SimpleJdbcInsert.execute(Map)` reads the table's column metadata once on the first call and constructs `INSERT INTO products (name,price,category) VALUES (?,?,?)`. The `Map` keys must match column names (case-insensitive for most databases).

---

### Level 2 — Intermediate

`executeAndReturnKey()` to capture the generated primary key.

```java
// SimpleJdbcDemo.java
import org.springframework.jdbc.core.simple.SimpleJdbcInsert;
import org.springframework.jdbc.core.namedparam.BeanPropertySqlParameterSource;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import org.springframework.jdbc.core.JdbcTemplate;
import java.util.*;

record Product(long id, String name, double price, String category) {}

public class SimpleJdbcDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:product-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();

        // usingGeneratedKeyColumns tells Spring which column holds the auto-generated key
        SimpleJdbcInsert insert = new SimpleJdbcInsert(ds)
            .withTableName("products")
            .usingGeneratedKeyColumns("id");

        // Insert via Map — returns generated key
        Number widgetId = insert.executeAndReturnKey(
            Map.of("name","Widget","price",9.99,"category","Tools"));
        System.out.println("Widget id=" + widgetId.longValue());

        // Insert via BeanPropertySqlParameterSource — reads product.name(), .price(), .category()
        Product gadget = new Product(0, "Gadget", 24.99, "Electronics");
        Number gadgetId = insert.executeAndReturnKey(new BeanPropertySqlParameterSource(gadget));
        System.out.println("Gadget id=" + gadgetId.longValue());

        // Batch insert — executeBatch returns int[]
        List<Map<String,Object>> batch = List.of(
            Map.of("name","Gizmo","price",14.49,"category","Electronics"),
            Map.of("name","Relay","price",4.99,"category","Tools")
        );
        int[] batchCounts = insert.executeBatch(batch.toArray(Map[]::new));
        System.out.println("Batch inserted: " + batchCounts.length + " rows");

        JdbcTemplate jt = new JdbcTemplate(ds);
        jt.queryForList("SELECT id,name,price FROM products ORDER BY id", Map.class)
            .forEach(r -> System.out.printf("  [%s] %-10s $%.2f%n",
                r.get("ID"), r.get("NAME"), r.get("PRICE")));
    }
}
```

How to run: same classpath

`usingGeneratedKeyColumns("id")` adds `RETURNING id` / uses `Statement.RETURN_GENERATED_KEYS` depending on the driver. `executeAndReturnKey()` returns a `Number` — call `.longValue()` or `.intValue()` to get the typed key.

---

### Level 3 — Advanced

`SimpleJdbcCall` to invoke an H2 stored function that returns product count per category.

```java
// SimpleJdbcDemo.java
import org.springframework.jdbc.core.simple.*;
import org.springframework.jdbc.core.namedparam.BeanPropertySqlParameterSource;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.core.JdbcTemplate;
import javax.sql.DataSource;
import java.util.*;

public class SimpleJdbcDemo {

    static DataSource buildDs() {
        // schema creates table + stored procedure
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:product-schema.sql")
            .addScript("classpath:product-proc.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();

        // Seed data
        SimpleJdbcInsert insert = new SimpleJdbcInsert(ds)
            .withTableName("products")
            .usingGeneratedKeyColumns("id");
        for (var row : List.of(
                Map.of("name","Widget","price",9.99,"category","Tools"),
                Map.of("name","Gadget","price",24.99,"category","Electronics"),
                Map.of("name","Gizmo","price",14.49,"category","Electronics"),
                Map.of("name","Relay","price",4.99,"category","Tools"),
                Map.of("name","Sensor","price",49.99,"category","Electronics"))) {
            insert.execute(row);
        }

        // SimpleJdbcCall — calls the stored procedure COUNT_BY_CATEGORY
        // H2 stored procs use CALL syntax; Spring detects IN/OUT params from metadata
        SimpleJdbcCall call = new SimpleJdbcCall(ds)
            .withProcedureName("COUNT_BY_CATEGORY");

        Map<String,Object> result = call.execute(Map.of("P_CATEGORY", "Electronics"));
        System.out.println("Electronics count: " + result.get("P_COUNT"));

        result = call.execute(Map.of("P_CATEGORY", "Tools"));
        System.out.println("Tools count: " + result.get("P_COUNT"));

        // Also demonstrate usingColumns — restrict which columns SimpleJdbcInsert uses
        SimpleJdbcInsert restrictedInsert = new SimpleJdbcInsert(ds)
            .withTableName("products")
            .usingColumns("name", "price", "category")
            .usingGeneratedKeyColumns("id");
        Number newId = restrictedInsert.executeAndReturnKey(
            Map.of("name","Timer","price",7.99,"category","Tools"));
        System.out.println("New product id: " + newId);
    }
}
```

`product-proc.sql`:
```sql
CREATE ALIAS COUNT_BY_CATEGORY AS $$
int countByCategory(Connection conn, String p_category) throws SQLException {
    PreparedStatement ps = conn.prepareStatement(
        "SELECT COUNT(*) FROM products WHERE category=?");
    ps.setString(1, p_category);
    ResultSet rs = ps.executeQuery();
    rs.next();
    return rs.getInt(1);
}
$$;
```

How to run: same classpath (H2 supports Java-based aliases as stored procedures)

`SimpleJdbcCall` reads `DatabaseMetaData.getProcedureColumns("COUNT_BY_CATEGORY")` to discover the parameter list. `execute(Map)` binds the input params, calls `{call COUNT_BY_CATEGORY(?)}`, and returns a `Map<String,Object>` containing the output parameters and result sets by name.

## 6. Walkthrough

**Level 2 — `executeAndReturnKey` execution order:**

1. **`new SimpleJdbcInsert(ds).withTableName("products").usingGeneratedKeyColumns("id")`**: configures the helper. No DB call yet — metadata is lazy.
2. **First `executeAndReturnKey(Map.of(...))` call**: `SimpleJdbcInsert.doExecute()` runs metadata inspection — `DatabaseMetaData.getColumns(null, null, "PRODUCTS", null)` returns columns: `ID`, `NAME`, `PRICE`, `CATEGORY`. Builds SQL: `INSERT INTO products (NAME,PRICE,CATEGORY) VALUES (?,?,?)`. Caches it.
3. **Key generation**: `JdbcTemplate.update(PreparedStatementCreator, KeyHolder)` with `Statement.RETURN_GENERATED_KEYS`. JDBC executes the INSERT, driver places the generated key in `KeyHolder`.
4. **`executeAndReturnKey` returns** `KeyHolder.getKey()` as `Number`. Caller calls `.longValue()` → `1L`.
5. **`BeanPropertySqlParameterSource(gadget)`**: Spring reads `gadget.name()` → `"Gadget"`, `gadget.price()` → `24.99`, `gadget.category()` → `"Electronics"` by calling accessor methods matching the cached column list.
6. **Subsequent inserts** reuse the cached SQL — no metadata round-trip.

**Request/response trace (Level 2):**

```
Metadata query (first call only):
  JDBC: DatabaseMetaData.getColumns(null, null, "PRODUCTS", null)
  Result: [ID BIGINT AUTO_INCREMENT, NAME VARCHAR, PRICE DOUBLE, CATEGORY VARCHAR]

INSERT (Widget):
  SQL:    INSERT INTO products (NAME,PRICE,CATEGORY) VALUES (?,?,?)
  Params: ["Widget", 9.99, "Tools"]
  Keys:   Statement.RETURN_GENERATED_KEYS=true
  Result: generated key=1

INSERT (Gadget via BeanPropertySqlParameterSource):
  SQL:    INSERT INTO products (NAME,PRICE,CATEGORY) VALUES (?,?,?)  [cached]
  Params: ["Gadget", 24.99, "Electronics"]
  Result: generated key=2
```

## 7. Gotchas & takeaways

> **`SimpleJdbcInsert` reads metadata at first use.** If the table doesn't exist yet when the first `execute()` is called, it will throw a `MetaDataAccessException`. Create tables before using the helper — typically in a `@PostConstruct` method that checks schema readiness first.

> **`usingColumns(...)` is required when the Map contains extra keys** that don't correspond to table columns, or when you want to insert into only a subset of columns explicitly. Without it, Spring may try to bind a Map key to a non-existent column and throw.

> **`SimpleJdbcCall` is not thread-safe during configuration.** Build and configure it once (usually `@PostConstruct`) — calling `withProcedureName()` after concurrent use can corrupt internal state.

- `SimpleJdbcInsert` eliminates `INSERT` SQL by reading column metadata at startup.
- `executeAndReturnKey()` captures auto-generated PKs — returns `Number`, cast to `long` or `int`.
- `executeBatch(Map[])` inserts multiple rows in one batch.
- `usingColumns(...)` restricts which columns are included — use when your Map has extra keys.
- `SimpleJdbcCall` discovers stored-procedure parameters from metadata; returns `Map<String,Object>` of output params.
