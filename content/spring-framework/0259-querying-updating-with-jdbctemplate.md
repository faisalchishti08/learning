---
card: spring-framework
gi: 259
slug: querying-updating-with-jdbctemplate
title: Querying & updating with JdbcTemplate
---

## 1. What it is

`JdbcTemplate` provides two families of operations: **querying** (SELECT) and **updating** (INSERT / UPDATE / DELETE / DDL). Each family has overloads for common use cases — scalar results, typed object lists, row mapping, batch processing, and key capture. `NamedParameterJdbcTemplate` adds `:name` named-parameter syntax on top of the same operations.

```java
// Querying
List<Order> orders = jdbc.query("SELECT * FROM orders WHERE status=?", ORDER_MAPPER, "OPEN");
Order order   = jdbc.queryForObject("SELECT * FROM orders WHERE id=?", ORDER_MAPPER, 42L);
int count     = jdbc.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);

// Updating
int rows = jdbc.update("UPDATE orders SET status=? WHERE id=?", "SHIPPED", 42L);
int[] results = jdbc.batchUpdate("INSERT INTO orders(product,qty) VALUES(?,?)", batchArgs);
```

## 2. Why & when

Raw JDBC parameter binding with `?` is error-prone at scale — the 5th positional `?` in a 10-parameter query is impossible to audit without counting characters. Named parameters fix this. `batchUpdate()` sends bulk operations in a single round-trip. `ResultSetExtractor` gives full control over the cursor for complex multi-row mappings.

Know which method to reach for:

| Goal | Method |
|------|--------|
| Scalar result (COUNT, SUM) | `queryForObject(sql, Class<T>)` |
| Single domain object | `queryForObject(sql, RowMapper, args)` |
| List of domain objects | `query(sql, RowMapper, args)` |
| Single row as Map | `queryForMap(sql, args)` |
| Column list | `queryForList(sql, Class<T>, args)` |
| INSERT/UPDATE/DELETE | `update(sql, args)` |
| INSERT + capture key | `update(PreparedStatementCreator, KeyHolder)` |
| Bulk insert | `batchUpdate(sql, List<Object[]>)` |
| Named parameters | All of the above via `NamedParameterJdbcTemplate` |

## 3. Core concept

**Query operations** use `RowMapper<T>` (one row → one object) or `ResultSetExtractor<T>` (full cursor → one result). `RowMapper` is the common case; `ResultSetExtractor` is for parent-child joins where multiple rows map to one object.

```java
// RowMapper — called for every row
RowMapper<Order> mapper = (rs, n) -> new Order(rs.getLong("id"), rs.getString("product"));

// ResultSetExtractor — controls entire cursor
ResultSetExtractor<Map<Long, List<String>>> extractor = rs -> {
    Map<Long, List<String>> map = new LinkedHashMap<>();
    while (rs.next()) {
        map.computeIfAbsent(rs.getLong("order_id"), k -> new ArrayList<>())
           .add(rs.getString("item_name"));
    }
    return map;
};
```

**Update operations** bind parameters positionally with `Object...` varargs or via `PreparedStatementSetter`. For bulk operations, `batchUpdate(String, List<Object[]>)` submits all rows in one prepared-statement batch. For key capture after INSERT, pass a `GeneratedKeyHolder`.

**Named parameters**: `NamedParameterJdbcTemplate` wraps `JdbcTemplate` and replaces `?` with `:name`. Parameters are passed as `Map<String,Object>` or a `SqlParameterSource` (e.g., `BeanPropertySqlParameterSource` — derives parameter values from Java bean properties).

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Query side -->
  <rect x="10" y="10" width="330" height="195" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="175" y="32" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Query Operations</text>
  <line x1="20" y1="40" x2="330" y2="40" stroke="#8b949e" stroke-width="0.5"/>
  <text x="175" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">queryForObject(sql, Class&lt;T&gt;)  → scalar</text>
  <text x="175" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">queryForObject(sql, RowMapper, args) → T</text>
  <text x="175" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">query(sql, RowMapper, args)  → List&lt;T&gt;</text>
  <text x="175" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">queryForMap(sql, args)  → Map&lt;String,Object&gt;</text>
  <text x="175" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">queryForList(sql, Class&lt;T&gt;, args)  → List&lt;T&gt;</text>
  <text x="175" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">query(sql, ResultSetExtractor, args) → T</text>
  <text x="175" y="176" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">RowMapper: 1 row → 1 object</text>
  <text x="175" y="192" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">ResultSetExtractor: full cursor → result</text>

  <!-- Update side -->
  <rect x="360" y="10" width="330" height="195" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="525" y="32" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Update Operations</text>
  <line x1="370" y1="40" x2="680" y2="40" stroke="#8b949e" stroke-width="0.5"/>
  <text x="525" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">update(sql, args...)  → int (rows affected)</text>
  <text x="525" y="76" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">update(PreparedStatementCreator, KeyHolder)</text>
  <text x="525" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">batchUpdate(sql, List&lt;Object[]&gt;)  → int[]</text>
  <text x="525" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">batchUpdate(sql, SqlParameterSource[])</text>
  <text x="525" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">execute(sql)  → void  (DDL)</text>
  <text x="525" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">execute(CallableStatementCreator, action)</text>
  <text x="525" y="176" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">NamedParameterJdbcTemplate: :name params</text>
  <text x="525" y="192" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">BeanPropertySqlParameterSource: bean → params</text>
</svg>

Query operations return typed results via `RowMapper` or `ResultSetExtractor`; update operations return row counts or generated keys.

## 5. Runnable example

Scenario: an **`InventoryService`** — building up from basic queries and updates, to named parameters with complex filtering, to a parent-child join with `ResultSetExtractor`.

### Level 1 — Basic

`update()` + `queryForObject()` + `query()` with a `RowMapper`.

```java
// JdbcQueryUpdateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;

record Item(long id, String name, int stock, double price) {}

@Configuration
public class JdbcQueryUpdateDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("inventory-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }

    static final RowMapper<Item> ITEM_MAPPER = (rs, n) -> new Item(
        rs.getLong("id"), rs.getString("name"), rs.getInt("stock"), rs.getDouble("price"));

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JdbcQueryUpdateDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // update() — INSERT rows
        jdbc.update("INSERT INTO items(name, stock, price) VALUES(?,?,?)", "Cable",  100, 4.99);
        jdbc.update("INSERT INTO items(name, stock, price) VALUES(?,?,?)", "Relay",   50, 24.95);
        jdbc.update("INSERT INTO items(name, stock, price) VALUES(?,?,?)", "Sensor",  20, 49.99);
        System.out.println("Inserted 3 items");

        // queryForObject — scalar
        int total = jdbc.queryForObject("SELECT SUM(stock) FROM items", Integer.class);
        System.out.println("Total stock: " + total);   // 170

        // query — list of domain objects
        List<Item> lowStock = jdbc.query(
            "SELECT * FROM items WHERE stock < ? ORDER BY stock",
            ITEM_MAPPER, 60);
        System.out.println("Low stock items:");
        lowStock.forEach(i -> System.out.printf("  %s: %d units%n", i.name(), i.stock()));

        // update() — UPDATE rows
        int updated = jdbc.update("UPDATE items SET stock=stock-? WHERE name=?", 5, "Sensor");
        System.out.println("Updated " + updated + " rows");
        System.out.println("Sensor stock: " +
            jdbc.queryForObject("SELECT stock FROM items WHERE name='Sensor'", Integer.class));
        ctx.close();
    }
}
```

`inventory-schema.sql`: `CREATE TABLE items (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), stock INT, price DOUBLE);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. JdbcQueryUpdateDemo.java`

`jdbc.update("UPDATE ...")` returns the count of affected rows — useful for verifying that the update matched expected records. `jdbc.query()` with a `RowMapper` collects every result row into `List<Item>`. `SUM()` via `queryForObject` with `Integer.class` performs aggregate queries cleanly.

---

### Level 2 — Intermediate

`NamedParameterJdbcTemplate` + `BeanPropertySqlParameterSource` for INSERT from a domain object.

```java
// JdbcQueryUpdateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.core.namedparam.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.*;
import javax.sql.DataSource;
import java.util.*;

public class Item {
    private long id; private String name; private int stock; private double price;
    public Item() {} public Item(String n, int s, double p){name=n;stock=s;price=p;}
    public long getId(){return id;} public String getName(){return name;}
    public int getStock(){return stock;} public double getPrice(){return price;}
}

@Configuration
public class JdbcQueryUpdateDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("inventory-schema.sql").build();
    }
    @Bean public NamedParameterJdbcTemplate namedJdbc(DataSource ds) {
        return new NamedParameterJdbcTemplate(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JdbcQueryUpdateDemo.class);
        NamedParameterJdbcTemplate named = ctx.getBean(NamedParameterJdbcTemplate.class);

        // BeanPropertySqlParameterSource — derives :name, :stock, :price from Item getters
        Item widget = new Item("Widget", 200, 9.99);
        KeyHolder holder = new GeneratedKeyHolder();
        named.update(
            "INSERT INTO items(name, stock, price) VALUES(:name, :stock, :price)",
            new BeanPropertySqlParameterSource(widget), holder);
        System.out.println("Inserted Widget, id=" + holder.getKey().longValue());

        Item motor = new Item("Motor", 15, 149.95);
        named.update("INSERT INTO items(name, stock, price) VALUES(:name, :stock, :price)",
            new BeanPropertySqlParameterSource(motor));

        // Named parameters for complex filter
        var params = Map.of("minStock", 10, "maxPrice", 100.0);
        List<Map<String,Object>> results = named.queryForList(
            "SELECT name, stock, price FROM items WHERE stock >= :minStock AND price <= :maxPrice ORDER BY price",
            params);
        System.out.println("Items in range:");
        results.forEach(r -> System.out.printf("  %s: %d @ $%.2f%n", r.get("NAME"), r.get("STOCK"), r.get("PRICE")));
        ctx.close();
    }
}
```

How to run: same classpath + NamedParameterJdbcTemplate included in spring-jdbc.jar

`BeanPropertySqlParameterSource(widget)` reads `getName()` → `:name`, `getStock()` → `:stock`, `getPrice()` → `:price` automatically. Named parameters eliminate positional numbering bugs. The same `Item` object is the source for both the entity data and the SQL parameters — no manual `Map` construction needed.

---

### Level 3 — Advanced

`ResultSetExtractor` for a parent-child join — mapping `orders` + `order_items` into `Map<Long, List<String>>`.

```java
// JdbcQueryUpdateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

@Configuration
public class JdbcQueryUpdateDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScripts("order-tables.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }

    // ResultSetExtractor: receives the full cursor, builds parent-child map in one pass
    static final ResultSetExtractor<Map<Long, List<String>>> ORDER_ITEMS_EXTRACTOR = rs -> {
        Map<Long, List<String>> result = new LinkedHashMap<>();
        while (rs.next()) {
            long orderId = rs.getLong("order_id");
            String itemName = rs.getString("item_name");
            result.computeIfAbsent(orderId, k -> new ArrayList<>()).add(itemName);
        }
        return result;
    };

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JdbcQueryUpdateDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // Setup
        jdbc.update("INSERT INTO orders(description) VALUES(?)", "Office Supplies");
        jdbc.update("INSERT INTO orders(description) VALUES(?)", "Electronics");
        jdbc.update("INSERT INTO order_items(order_id, item_name) VALUES(1,'Stapler')");
        jdbc.update("INSERT INTO order_items(order_id, item_name) VALUES(1,'Paper')");
        jdbc.update("INSERT INTO order_items(order_id, item_name) VALUES(1,'Pens')");
        jdbc.update("INSERT INTO order_items(order_id, item_name) VALUES(2,'Keyboard')");
        jdbc.update("INSERT INTO order_items(order_id, item_name) VALUES(2,'Mouse')");

        // Single query — ResultSetExtractor maps parent-child join into grouped map
        Map<Long, List<String>> orderItems = jdbc.query(
            "SELECT o.id AS order_id, oi.item_name " +
            "FROM orders o JOIN order_items oi ON o.id = oi.order_id " +
            "ORDER BY o.id, oi.item_name",
            ORDER_ITEMS_EXTRACTOR);

        orderItems.forEach((orderId, items) ->
            System.out.printf("Order %d: %s%n", orderId, items));

        // batchUpdate with SqlParameterSource[] for NamedParameter batch insert
        var batchArgs = new org.springframework.jdbc.core.namedparam.SqlParameterSource[]{
            new org.springframework.jdbc.core.namedparam.MapSqlParameterSource("orderId",1).addValue("itemName","Clips"),
            new org.springframework.jdbc.core.namedparam.MapSqlParameterSource("orderId",2).addValue("itemName","Monitor"),
        };
        var namedJdbc = new org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate(
            ctx.getBean(DataSource.class));
        int[] added = namedJdbc.batchUpdate(
            "INSERT INTO order_items(order_id, item_name) VALUES(:orderId, :itemName)", batchArgs);
        System.out.println("Batch added: " + Arrays.stream(added).sum() + " items");

        // Verify updated grouping
        Map<Long, List<String>> updated = jdbc.query(
            "SELECT o.id AS order_id, oi.item_name FROM orders o JOIN order_items oi ON o.id=oi.order_id ORDER BY o.id",
            ORDER_ITEMS_EXTRACTOR);
        updated.forEach((oid, items) -> System.out.printf("Order %d (updated): %s%n", oid, items));
        ctx.close();
    }
}
```

`order-tables.sql`: `CREATE TABLE orders (id BIGINT AUTO_INCREMENT PRIMARY KEY, description VARCHAR(100)); CREATE TABLE order_items (id BIGINT AUTO_INCREMENT PRIMARY KEY, order_id BIGINT, item_name VARCHAR(100));`

How to run: same classpath

`ResultSetExtractor` gives full cursor control — the while-loop iterates all rows in one pass and groups order items by `order_id`. This is one DB round-trip for the whole parent-child tree instead of N+1 queries. `batchUpdate(sql, SqlParameterSource[])` on `NamedParameterJdbcTemplate` combines named parameters with batch execution.

## 6. Walkthrough

**Level 3 — `ResultSetExtractor` execution trace:**

```
jdbc.query(joinSql, ORDER_ITEMS_EXTRACTOR)
  → JdbcTemplate.query(String, ResultSetExtractor):
      execute(psc, new QueryStatementCallback(rse)):
        con = DataSourceUtils.getConnection(dataSource)
        stmt = con.createStatement()
        rs = stmt.executeQuery(joinSql)
          ← H2 returns 5 rows:
             (1, "Office Supplies", 1, "Paper")
             (1, "Office Supplies", 1, "Pens")
             (1, "Office Supplies", 1, "Stapler")
             (2, "Electronics",    2, "Keyboard")
             (2, "Electronics",    2, "Mouse")

  → ORDER_ITEMS_EXTRACTOR.extractData(rs):
      result = {}
      rs.next() → orderId=1, itemName="Paper"   → result={1:["Paper"]}
      rs.next() → orderId=1, itemName="Pens"    → result={1:["Paper","Pens"]}
      rs.next() → orderId=1, itemName="Stapler" → result={1:["Paper","Pens","Stapler"]}
      rs.next() → orderId=2, itemName="Keyboard"→ result={1:[...], 2:["Keyboard"]}
      rs.next() → orderId=2, itemName="Mouse"   → result={1:[...], 2:["Keyboard","Mouse"]}
      rs.next() → false
      return result

  → rs.close(); stmt.close()
  → DataSourceUtils.releaseConnection(con, dataSource)
  → return Map{1:["Paper","Pens","Stapler"], 2:["Keyboard","Mouse"]}
```

## 7. Gotchas & takeaways

> **`queryForObject()` throws on empty result — never use it for "find or null" lookups.** Use `query()` and check `list.isEmpty()` or use `Optional<T>` wrapping. Spring 5.3+ added `queryForObject()` overloads that return `null` on no result for scalar types, but the `RowMapper` variant still throws `EmptyResultDataAccessException`.

> **`batchUpdate()` reuses a single `PreparedStatement` — parameter types must be consistent.** Mixing `null` and non-null values for the same column position can cause type-inference errors on some JDBC drivers. Use `Types.NULL` explicit type or `SqlParameterSource` with typed nulls.

> **`NamedParameterJdbcTemplate` re-parses SQL for named placeholders on each call.** For performance-critical hot paths, use `ParsedSql` caching (via `NamedParameterUtils.parseSqlStatement`) or fall back to `JdbcTemplate` with positional parameters.

- `RowMapper<T>` — 1 row → 1 object; simpler and covers 90% of query cases.
- `ResultSetExtractor<T>` — full cursor control; use for parent-child joins or complex grouping.
- `BeanPropertySqlParameterSource` — bind INSERT/UPDATE params from a Java bean automatically.
- `batchUpdate()` — bulk operations; one round-trip for N rows; check driver batching config.
- `queryForObject()` with `RowMapper` throws `EmptyResultDataAccessException` on zero rows — don't use for nullable lookups.
