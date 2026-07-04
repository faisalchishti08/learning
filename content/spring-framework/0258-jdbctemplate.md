---
card: spring-framework
gi: 258
slug: jdbctemplate
title: JdbcTemplate
---

## 1. What it is

`JdbcTemplate` is the central class in Spring JDBC. It wraps the entire JDBC `Connection` / `PreparedStatement` / `ResultSet` lifecycle — open, execute, close, translate exceptions — into a set of typed Java method calls. The caller provides only the SQL and the data; `JdbcTemplate` handles everything else.

```java
// One-line query — no Connection, no PreparedStatement, no ResultSet, no try-finally
List<String> names = jdbc.queryForList("SELECT name FROM products", String.class);

// One-line insert
jdbc.update("INSERT INTO products(name, price) VALUES(?,?)", "Widget", 9.99);
```

`JdbcTemplate` is thread-safe — configure it once as a singleton `@Bean` and share it across all service classes.

## 2. Why & when

Raw JDBC requires five steps for even the simplest query: acquire connection, prepare statement, bind parameters, iterate result set, close everything in a finally block. That's roughly 15 lines of boilerplate per query — plus `catch (SQLException)` with vendor-specific error codes. `JdbcTemplate` collapses this to one line.

Use `JdbcTemplate` when:
- You want SQL control (specific queries, bulk INSERT, stored procedures).
- You need maximum performance — no JPA entity lifecycle overhead.
- You're using a schema that doesn't map neatly to JPA entities (views, reporting queries, multi-table joins).

Use `NamedParameterJdbcTemplate` when your SQL has more than 2-3 parameters (`:name` vs `?` is much clearer at scale).

## 3. Core concept

`JdbcTemplate` is built around three callback interfaces:

| Callback | Use | Lambda shape |
|----------|-----|-------------|
| `PreparedStatementCreator` | Create the `PreparedStatement` | `con -> con.prepareStatement(sql)` |
| `PreparedStatementSetter` | Bind parameters | `ps -> { ps.setString(1, x); ... }` |
| `RowMapper<T>` | Map each result row to a Java object | `(rs, n) -> new Product(rs.getLong(1), rs.getString(2))` |

The method families:

```java
// Queries
jdbc.queryForObject(sql, RowMapper, args...)  → T           // single row
jdbc.queryForList(sql, Class<T>, args...)     → List<T>     // scalar column list
jdbc.query(sql, RowMapper, args...)          → List<T>      // full object list
jdbc.queryForMap(sql, args...)               → Map<String,Object>  // single row

// Updates
jdbc.update(sql, args...)                    → int          // rows affected
jdbc.batchUpdate(sql, List<Object[]>)        → int[]        // batch

// DDL / arbitrary SQL
jdbc.execute(sql)                            → void
```

`JdbcTemplate` internally calls `DataSourceUtils.getConnection(dataSource)` — the connection participates in any active Spring transaction automatically.

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

  <!-- Caller -->
  <rect x="10" y="80" width="110" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="65" y="108" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Your Code</text>
  <line x1="122" y1="105" x2="178" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="150" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">sql + args</text>

  <!-- JdbcTemplate -->
  <rect x="178" y="40" width="200" height="130" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="278" y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">JdbcTemplate</text>
  <line x1="188" y1="70" x2="368" y2="70" stroke="#8b949e" stroke-width="0.5"/>
  <text x="278" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">getConnection (DataSourceUtils)</text>
  <text x="278" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">prepareStatement / bind params</text>
  <text x="278" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">execute</text>
  <text x="278" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">map ResultSet → Java objects</text>
  <text x="278" y="152" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">close / translate exceptions</text>

  <line x1="380" y1="105" x2="435" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DataSource -->
  <rect x="435" y="80" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">DataSource</text>
  <text x="495" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">HikariCP / H2</text>

  <!-- Exception path -->
  <line x1="278" y1="172" x2="278" y2="200" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <rect x="168" y="198" width="220" height="14" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="278" y="209" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">SQLExceptionTranslator → DataAccessException</text>
</svg>

`JdbcTemplate` sits between your code and JDBC — handles all lifecycle and translates exceptions.

## 5. Runnable example

Scenario: an **`OrderService`** managing orders — inserting, querying by field, mapping to a domain object, and running a batch.

### Level 1 — Basic

`JdbcTemplate.update()` for INSERT and `queryForObject()` / `queryForList()` for SELECT.

```java
// JdbcTemplateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;

@Configuration
public class JdbcTemplateDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JdbcTemplateDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // INSERT — args bound positionally to ?
        int rows = jdbc.update("INSERT INTO orders(product, quantity, total) VALUES(?,?,?)",
            "Widget", 3, 29.97);
        System.out.println("Inserted: " + rows + " row(s)");

        jdbc.update("INSERT INTO orders(product, quantity, total) VALUES(?,?,?)", "Gadget", 1, 19.99);
        jdbc.update("INSERT INTO orders(product, quantity, total) VALUES(?,?,?)", "Widget", 5, 49.95);

        // SELECT scalar — queryForObject
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
        System.out.println("Total orders: " + count);

        // SELECT list of one column
        List<String> products = jdbc.queryForList("SELECT DISTINCT product FROM orders ORDER BY product", String.class);
        System.out.println("Products: " + products);

        // SELECT single row by id
        String name = jdbc.queryForObject("SELECT product FROM orders WHERE id=?", String.class, 1);
        System.out.println("Order 1 product: " + name);
        ctx.close();
    }
}
```

`orders-schema.sql`: `CREATE TABLE orders (id BIGINT AUTO_INCREMENT PRIMARY KEY, product VARCHAR(100), quantity INT, total DOUBLE);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. JdbcTemplateDemo.java`

`jdbc.update()` handles parameter binding and returns the row count. `queryForObject()` requires exactly one result row — it throws `EmptyResultDataAccessException` if zero rows match and `IncorrectResultSizeDataAccessException` if more than one. `queryForList()` returns a `List` of the single specified column type.

---

### Level 2 — Intermediate

`RowMapper<T>` — mapping result rows to a domain object `Order`.

```java
// JdbcTemplateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;

record Order(long id, String product, int quantity, double total) {}

@Configuration
public class JdbcTemplateDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }

    // RowMapper as a reusable constant
    static final RowMapper<Order> ORDER_MAPPER = (rs, rowNum) -> new Order(
        rs.getLong("id"),
        rs.getString("product"),
        rs.getInt("quantity"),
        rs.getDouble("total")
    );

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JdbcTemplateDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        jdbc.update("INSERT INTO orders(product,quantity,total) VALUES(?,?,?)", "Sensor", 2, 99.98);
        jdbc.update("INSERT INTO orders(product,quantity,total) VALUES(?,?,?)", "Router", 1, 129.99);
        jdbc.update("INSERT INTO orders(product,quantity,total) VALUES(?,?,?)", "Sensor", 3, 149.97);

        // Map all rows → List<Order>
        List<Order> all = jdbc.query("SELECT * FROM orders ORDER BY id", ORDER_MAPPER);
        all.forEach(o -> System.out.printf("  Order[%d] %s x%d = $%.2f%n", o.id(), o.product(), o.quantity(), o.total()));

        // Map single row → Order (by id)
        Order first = jdbc.queryForObject("SELECT * FROM orders WHERE id=?", ORDER_MAPPER, 1);
        System.out.println("First: " + first);

        // Aggregate — total revenue per product
        List<String> summary = jdbc.queryForList(
            "SELECT product || ': $' || CAST(SUM(total) AS VARCHAR) FROM orders GROUP BY product",
            String.class);
        System.out.println("Revenue: " + summary);
        ctx.close();
    }
}
```

How to run: same classpath

`RowMapper<Order>` is a functional interface — a lambda that receives `ResultSet` and row number, returns a typed object. `jdbc.query()` applies it to every row and returns `List<Order>`. Defining it as a `static final` constant avoids instantiating a new lambda object per call.

---

### Level 3 — Advanced

`batchUpdate()` for bulk inserts + `BeanPropertyRowMapper` for convention-based mapping.

```java
// JdbcTemplateDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

public class Order {
    private long id; private String product; private int quantity; private double total;
    public Order() {} public Order(long id, String p, int q, double t){this.id=id;product=p;quantity=q;total=t;}
    public long getId(){return id;} public String getProduct(){return product;}
    public int getQuantity(){return quantity;} public double getTotal(){return total;}
    public String toString(){return "Order["+id+","+product+","+quantity+","+(int)total+"]";}
}

@Configuration
public class JdbcTemplateDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("orders-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(JdbcTemplateDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // batchUpdate — one PreparedStatement, many executions, one round-trip to the DB
        List<Object[]> batchArgs = List.of(
            new Object[]{"Cable",  10,  49.90},
            new Object[]{"Relay",   5, 124.75},
            new Object[]{"Sensor",  7, 349.65},
            new Object[]{"Timer",   3,  89.97},
            new Object[]{"Module",  2,  59.98}
        );
        int[] counts = jdbc.batchUpdate(
            "INSERT INTO orders(product,quantity,total) VALUES(?,?,?)", batchArgs);
        System.out.println("Batch inserted: " + counts.length + " rows, each count=" + Arrays.stream(counts).sum());

        // BeanPropertyRowMapper — maps column names to property names by convention
        List<Order> orders = jdbc.query(
            "SELECT * FROM orders WHERE total > ? ORDER BY total DESC",
            BeanPropertyRowMapper.newInstance(Order.class),
            100.0);
        System.out.println("Orders > $100:");
        orders.forEach(o -> System.out.println("  " + o));

        // queryForMap — one row as Map (useful for dynamic schemas)
        Map<String,Object> row = jdbc.queryForMap("SELECT * FROM orders WHERE id=?", 1);
        System.out.println("Row map: " + row);
        ctx.close();
    }
}
```

How to run: same classpath

`batchUpdate(sql, List<Object[]>)` sends all rows in a single prepared-statement batch — typically 10-100× faster than individual `update()` calls for bulk operations. `BeanPropertyRowMapper.newInstance(Order.class)` maps column names to property names by convention (`PRODUCT` column → `setProduct()` method), eliminating hand-written `RowMapper` code for simple cases.

## 6. Walkthrough

**Level 2 — `jdbc.query()` with `RowMapper` (execution trace):**

```
jdbc.query("SELECT * FROM orders ORDER BY id", ORDER_MAPPER)
  → JdbcTemplate.query(String sql, RowMapper<T> rowMapper):
      execute(new SimplePreparedStatementCreator(sql),
              new RowMapperResultSetExtractor<>(rowMapper)):

  → JdbcTemplate.execute(PreparedStatementCreator, PreparedStatementCallback):
      con = DataSourceUtils.getConnection(dataSource)
             ← transaction-bound connection if inside @Transactional
      ps = con.prepareStatement("SELECT * FROM orders ORDER BY id")
      rs = ps.executeQuery()
             ← H2 executes; ResultSet with 3 rows

  → RowMapperResultSetExtractor.extractData(rs):
      results = new ArrayList<>()
      while (rs.next()):
        rowNum=1: ORDER_MAPPER.mapRow(rs, 1) → Order(1,"Sensor",2,99.98) → results.add()
        rowNum=2: ORDER_MAPPER.mapRow(rs, 2) → Order(2,"Router",1,129.99) → results.add()
        rowNum=3: ORDER_MAPPER.mapRow(rs, 3) → Order(3,"Sensor",3,149.97) → results.add()
      return results  ← List<Order> of 3 elements

  → rs.close(); ps.close()
  → DataSourceUtils.releaseConnection(con, dataSource)
  → return List<Order>
```

**Exception translation path:**

```
ps.executeQuery() → H2 throws SQLException(errorCode=42102: "TABLE NOT FOUND")
  → JdbcTemplate catches SQLException
  → SQLErrorCodeSQLExceptionTranslator.translate("PreparedStatementCallback", sql, ex)
       H2 section in sql-error-codes.xml: 42102 → BadSqlGrammarException
  → throw BadSqlGrammarException
```

## 7. Gotchas & takeaways

> **`queryForObject()` throws `EmptyResultDataAccessException` on zero rows.** Do not use it for "find by id" queries unless you're certain the row exists. Use `query()` and check if the returned `List` is empty, or wrap in `try/catch`.

> **`BeanPropertyRowMapper` uses reflection and converts column names to camelCase.** Column `ORDER_DATE` maps to `setOrderDate()`. It's convenient but slower than a hand-written `RowMapper` for high-throughput paths. Also: it does NOT validate that all result columns map to properties — extra columns are silently ignored.

> **`batchUpdate()` performance depends on the JDBC driver.** H2 and PostgreSQL support true server-side batching. MySQL requires `rewriteBatchedStatements=true` in the connection URL. Without it, the driver sends statements one by one despite the batch API.

- `JdbcTemplate` is thread-safe — create one per `DataSource`, share as `@Bean` singleton.
- `queryForObject()` — exactly one row; throws on 0 or 2+ results.
- `RowMapper<T>` — functional interface; maps one `ResultSet` row to a Java object.
- `BeanPropertyRowMapper` — convention-based mapping by property name; fine for low-traffic paths.
- `batchUpdate()` — bulk inserts in one round-trip; check driver configuration for true batching.
