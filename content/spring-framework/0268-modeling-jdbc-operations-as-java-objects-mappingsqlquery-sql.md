---
card: spring-framework
gi: 268
slug: modeling-jdbc-operations-as-java-objects-mappingsqlquery-sql
title: Modeling JDBC operations as Java objects (MappingSqlQuery, SqlUpdate)
---

## 1. What it is

Spring JDBC provides an **object-oriented model** for JDBC operations via classes in `org.springframework.jdbc.object`. Instead of calling `JdbcTemplate` methods inline, you subclass reusable objects:

| Class | Purpose |
|---|---|
| `MappingSqlQuery<T>` | Compiled, parameterised SELECT → `List<T>` |
| `SqlUpdate` | Compiled, parameterised INSERT/UPDATE/DELETE |
| `SqlCall` | Compiled, parameterised stored procedure call |
| `StoredProcedure` | Full stored-procedure wrapper (with OUT params) |
| `SqlFunction<T>` | Compiled scalar-returning SQL function call |

All inherit from `RdbmsOperation` which compiles the SQL and registers parameters at creation time — similar to how JDBC `PreparedStatement` is compiled once.

## 2. Why & when

These classes predate Spring's fluent `JdbcTemplate` style. They shine when:
- **A query is called from many places** — define it once as a named class and share the instance.
- **SQL is complex enough to deserve its own class** with clear parameter documentation.
- **Type safety matters** — parameters are declared with `SqlParameter` objects that carry JDBC type info, preventing bind-type mismatches.
- You want **test doubles** — the operation class can be subclassed or mocked easily.

For simple one-off queries, `JdbcTemplate` inline is shorter. Use object-model classes for frequently called, documented, domain-meaningful queries.

## 3. Core concept

`RdbmsOperation` subclass lifecycle:

1. Constructor calls `declareParameter(new SqlParameter("name", Types.VARCHAR))` for each param.
2. Constructor calls `compile()` — validates SQL and parameter list; stores compiled state.
3. Each `execute(args...)` call binds the declared parameters and delegates to the internal `JdbcTemplate`.

`MappingSqlQuery<T>` requires one abstract method:
```java
@Override
protected T mapRow(ResultSet rs, int rowNumber) throws SQLException { ... }
```

`SqlUpdate` exposes `update(Object... args)` returning `int` (affected rows).

Both accept a `DataSource` in the constructor — they create their own internal `JdbcTemplate`.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- RdbmsOperation hierarchy -->
  <rect x="240" y="10" width="220" height="36" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="32" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RdbmsOperation (abstract)</text>

  <!-- MappingSqlQuery -->
  <rect x="60" y="80" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="102" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">MappingSqlQuery&lt;T&gt;</text>
  <text x="160" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">abstract mapRow(rs, n) → T</text>

  <!-- SqlUpdate -->
  <rect x="440" y="80" width="200" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">SqlUpdate</text>
  <text x="540" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">update(Object... args) → int</text>

  <!-- Arrows from RdbmsOperation -->
  <line x1="350" y1="48" x2="200" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="350" y1="48" x2="500" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Your subclass -->
  <rect x="60" y="165" width="200" height="38" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="160" y="181" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">class ItemsBySkuQuery</text>
  <text x="160" y="196" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">extends MappingSqlQuery&lt;Item&gt;</text>
  <line x1="160" y1="133" x2="160" y2="163" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>

  <!-- SqlUpdate subclass -->
  <rect x="440" y="165" width="200" height="38" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="540" y="181" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">class UpdateItemQty</text>
  <text x="540" y="196" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">extends SqlUpdate</text>
  <line x1="540" y1="133" x2="540" y2="163" stroke="#79c0ff" stroke-width="1" marker-end="url(#arr)"/>
</svg>

`MappingSqlQuery` and `SqlUpdate` compile once at construction, then accept parameter values at each call.

## 5. Runnable example

Scenario: an **inventory system** — create `MappingSqlQuery` and `SqlUpdate` objects to query and update stock items, progressing from basic subclassing to full parameterised object usage.

### Level 1 — Basic

`MappingSqlQuery<Item>` subclass — compiled SELECT.

```java
// ObjectJdbcDemo.java
import org.springframework.jdbc.core.SqlParameter;
import org.springframework.jdbc.object.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

record Item(long id, String sku, String name, int qty) {}

// Subclass MappingSqlQuery — compiled once, reused many times
class ItemsBySkuQuery extends MappingSqlQuery<Item> {
    ItemsBySkuQuery(DataSource ds) {
        super(ds, "SELECT * FROM inventory WHERE sku LIKE :sku ORDER BY sku");
        declareParameter(new SqlParameter("sku", Types.VARCHAR));
        compile();
    }

    @Override
    protected Item mapRow(ResultSet rs, int rowNumber) throws SQLException {
        return new Item(rs.getLong("id"), rs.getString("sku"),
            rs.getString("name"), rs.getInt("qty"));
    }
}

public class ObjectJdbcDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:inventory-schema.sql")
            .addScript("classpath:inventory-data.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        ItemsBySkuQuery query = new ItemsBySkuQuery(ds);

        // Execute with named param
        List<Item> widgetItems = query.executeByNamedParam(Map.of("sku", "WID%"));
        System.out.println("WID items: " + widgetItems.size());
        widgetItems.forEach(i -> System.out.printf("  %s %-15s qty=%d%n",
            i.sku(), i.name(), i.qty()));

        List<Item> all = query.executeByNamedParam(Map.of("sku", "%"));
        System.out.println("All items: " + all.size());
    }
}
```

`inventory-schema.sql`: `CREATE TABLE inventory (id BIGINT AUTO_INCREMENT PRIMARY KEY, sku VARCHAR(20) NOT NULL UNIQUE, name VARCHAR(100), qty INT DEFAULT 0);`

`inventory-data.sql`:
```sql
INSERT INTO inventory(sku,name,qty) VALUES('WID-001','Widget',150);
INSERT INTO inventory(sku,name,qty) VALUES('GAD-002','Gadget',75);
INSERT INTO inventory(sku,name,qty) VALUES('SEN-003','Sensor',200);
INSERT INTO inventory(sku,name,qty) VALUES('WID-004','Wide Widget',80);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. ObjectJdbcDemo.java`

`MappingSqlQuery` must declare all parameters before `compile()`. `executeByNamedParam(Map)` binds named params and returns `List<Item>`. The `mapRow()` implementation is exactly a `RowMapper` lambda but structured as an overridable method for clarity.

---

### Level 2 — Intermediate

`SqlUpdate` for INSERT and UPDATE operations.

```java
// ObjectJdbcDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.object.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.*;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

record Item(long id, String sku, String name, int qty) {}

class ItemsBySkuQuery extends MappingSqlQuery<Item> {
    ItemsBySkuQuery(DataSource ds) {
        super(ds, "SELECT * FROM inventory WHERE sku LIKE :sku ORDER BY sku");
        declareParameter(new SqlParameter("sku", Types.VARCHAR));
        compile();
    }
    @Override
    protected Item mapRow(ResultSet rs, int n) throws SQLException {
        return new Item(rs.getLong("id"), rs.getString("sku"),
            rs.getString("name"), rs.getInt("qty"));
    }
}

// SqlUpdate for INSERT
class InsertItem extends SqlUpdate {
    InsertItem(DataSource ds) {
        super(ds, "INSERT INTO inventory(sku,name,qty) VALUES(?,?,?)");
        declareParameter(new SqlParameter("sku",  Types.VARCHAR));
        declareParameter(new SqlParameter("name", Types.VARCHAR));
        declareParameter(new SqlParameter("qty",  Types.INTEGER));
        setReturnGeneratedKeys(true);
        compile();
    }
}

// SqlUpdate for stock adjustment
class AdjustQty extends SqlUpdate {
    AdjustQty(DataSource ds) {
        super(ds, "UPDATE inventory SET qty = qty + ? WHERE sku = ?");
        declareParameter(new SqlParameter("delta", Types.INTEGER));
        declareParameter(new SqlParameter("sku",   Types.VARCHAR));
        compile();
    }
}

public class ObjectJdbcDemo {

    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:inventory-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        InsertItem insert  = new InsertItem(ds);
        AdjustQty  adjust  = new AdjustQty(ds);
        ItemsBySkuQuery q  = new ItemsBySkuQuery(ds);

        // Insert items — returns affected row count
        KeyHolder kh = new GeneratedKeyHolder();
        insert.update(new Object[]{"WID-001","Widget",150}, kh);
        System.out.println("Inserted Widget with key: " + kh.getKey());

        insert.update("GAD-002", "Gadget", 75);
        insert.update("SEN-003", "Sensor", 200);

        // Adjust stock
        int updated = adjust.update(+50, "WID-001");  // receive 50 more Widgets
        System.out.println("Adjusted: " + updated + " row(s)");
        updated = adjust.update(-30, "GAD-002");       // ship 30 Gadgets
        System.out.println("Adjusted: " + updated + " row(s)");

        // Query result
        List<Item> all = q.executeByNamedParam(Map.of("sku", "%"));
        all.forEach(i -> System.out.printf("  %-10s %-15s qty=%d%n",
            i.sku(), i.name(), i.qty()));
    }
}
```

How to run: same classpath

`SqlUpdate.update(Object... args)` binds positionally and returns the affected-row count. `setReturnGeneratedKeys(true)` works with the `update(Object[], KeyHolder)` overload to capture auto-generated keys. Params are declared by position — `declareParameter` calls match the `?` order in the SQL.

---

### Level 3 — Advanced

`SqlFunction<Integer>` for scalar queries + `MappingSqlQuery` with multiple params.

```java
// ObjectJdbcDemo.java
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.object.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.sql.*;
import java.util.*;

record Item(long id, String sku, String name, int qty) {}

class ItemsBySkuQuery extends MappingSqlQuery<Item> {
    ItemsBySkuQuery(DataSource ds) {
        super(ds, "SELECT * FROM inventory WHERE sku LIKE :sku AND qty >= :minQty ORDER BY qty DESC");
        declareParameter(new SqlParameter("sku", Types.VARCHAR));
        declareParameter(new SqlParameter("minQty", Types.INTEGER));
        compile();
    }
    @Override
    protected Item mapRow(ResultSet rs, int n) throws SQLException {
        return new Item(rs.getLong("id"), rs.getString("sku"),
            rs.getString("name"), rs.getInt("qty"));
    }
}

// SqlFunction — scalar SELECT (COUNT, MAX, etc.)
class TotalQtyByCategory extends SqlFunction<Integer> {
    TotalQtyByCategory(DataSource ds) {
        super(ds, "SELECT SUM(qty) FROM inventory WHERE sku LIKE ?");
        declareParameter(new SqlParameter("prefix", Types.VARCHAR));
        compile();
    }
}

class InsertItem extends SqlUpdate {
    InsertItem(DataSource ds) {
        super(ds, "INSERT INTO inventory(sku,name,qty) VALUES(?,?,?)");
        declareParameter(new SqlParameter("sku", Types.VARCHAR));
        declareParameter(new SqlParameter("name", Types.VARCHAR));
        declareParameter(new SqlParameter("qty", Types.INTEGER));
        compile();
    }
}

public class ObjectJdbcDemo {
    static DataSource buildDs() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:inventory-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();
        InsertItem insert = new InsertItem(ds);
        insert.update("WID-001", "Widget",      150);
        insert.update("WID-004", "Wide Widget",   80);
        insert.update("GAD-002", "Gadget",        75);
        insert.update("SEN-003", "Sensor",       200);
        insert.update("SEN-007", "Smart Sensor",  45);

        // Multi-param MappingSqlQuery
        ItemsBySkuQuery q = new ItemsBySkuQuery(ds);
        List<Item> hiStockWidgets = q.executeByNamedParam(Map.of("sku","WID%","minQty",100));
        System.out.println("High-stock WID items:");
        hiStockWidgets.forEach(i -> System.out.printf("  %-12s qty=%d%n", i.name(), i.qty()));

        // SqlFunction — scalar result
        TotalQtyByCategory totalWidgets = new TotalQtyByCategory(ds);
        Integer widgetTotal = totalWidgets.run("WID%");
        System.out.println("Total WID qty: " + widgetTotal);

        Integer sensorTotal = totalWidgets.run("SEN%");
        System.out.println("Total SEN qty: " + sensorTotal);

        // Demonstrate compile() result — isCompiled()
        System.out.println("Query compiled: " + q.isCompiled());
        System.out.println("Update compiled: " + insert.isCompiled());
    }
}
```

How to run: same classpath

`SqlFunction<Integer>` wraps a scalar-returning SELECT. `run(Object... args)` executes and returns the typed scalar. Multiple `declareParameter` calls with named params enable `executeByNamedParam(Map)`. Once compiled (`isCompiled()` returns true) the SQL is fixed — the class validates that all declared parameters are present on each call.

## 6. Walkthrough

**Level 2 — `insert.update()` then `adjust.update()` (execution order):**

1. **`InsertItem insert = new InsertItem(ds)`**: constructor runs:
   - `super(ds, "INSERT INTO inventory(sku,name,qty) VALUES(?,?,?)")` — stores SQL.
   - Three `declareParameter()` calls — registers sku (VARCHAR), name (VARCHAR), qty (INTEGER).
   - `compile()` — `RdbmsOperation.compile()` validates the parameter count matches `?` count (3 == 3), marks `compiled=true`.
2. **`insert.update("WID-001","Widget",150)`**: `SqlUpdate.update(Object...)` is called.
   - Checks `isCompiled()` → true.
   - Binds positionally: `ps.setString(1,"WID-001")`, `ps.setString(2,"Widget")`, `ps.setInt(3,150)`.
   - Calls internal `JdbcTemplate.update()` → `ps.executeUpdate()` → H2 inserts row → returns 1.
3. **`KeyHolder kh` variant**: same path but wrapped in `JdbcTemplate.update(psc, keyHolder)` — after `executeUpdate()`, `keyHolder.getKey()` returns the generated `BIGINT` primary key.
4. **`adjust.update(+50,"WID-001")`**: binds `ps.setInt(1,50)`, `ps.setString(2,"WID-001")` → `UPDATE inventory SET qty = qty + 50 WHERE sku = 'WID-001'` → H2 updates 1 row → returns 1.

```
insert.update("WID-001","Widget",150):
  SQL:    INSERT INTO inventory(sku,name,qty) VALUES(?,?,?)
  Params: ["WID-001","Widget",150]
  Result: 1 row inserted

adjust.update(+50,"WID-001"):
  SQL:    UPDATE inventory SET qty = qty + ? WHERE sku = ?
  Params: [50, "WID-001"]
  Result: 1 row updated  (qty: 150 → 200)
```

## 7. Gotchas & takeaways

> **`compile()` must be called in the constructor.** If you call `declareParameter()` after `compile()`, Spring throws `InvalidDataAccessApiUsageException`. Always declare all parameters before `compile()`.

> **`MappingSqlQuery` is thread-safe after `compile()`.** Create one instance per operation class and share it — do not create a new instance per request.

> **`executeByNamedParam()` requires the SQL to use `:name` placeholders**, not `?`. Plain `execute(Object...)` uses positional `?`. Mixing these causes a `BindException` at runtime.

- `MappingSqlQuery<T>` — compiled SELECT that maps rows; declare params then `compile()` in constructor.
- `SqlUpdate` — compiled INSERT/UPDATE/DELETE; `update(args...)` → affected row count.
- `SqlFunction<T>` — scalar-returning SELECT; `run(args...)` → typed scalar.
- All classes are thread-safe after `compile()` — create once, share as singletons.
- Prefer `JdbcTemplate` inline for simple one-off queries; use object classes for frequently called, documented domain operations.
