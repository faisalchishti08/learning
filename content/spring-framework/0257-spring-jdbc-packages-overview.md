---
card: spring-framework
gi: 257
slug: spring-jdbc-packages-overview
title: Spring JDBC packages overview
---

## 1. What it is

Spring JDBC (`spring-jdbc` artifact) is a thin layer over JDBC that eliminates boilerplate (`Connection`, `PreparedStatement`, `ResultSet` lifecycle management, exception translation) while staying close to raw SQL. It is organized into five primary packages, each serving a distinct role in the data-access layer.

```
org.springframework.jdbc
├── core              — JdbcTemplate, NamedParameterJdbcTemplate, SimpleJdbcInsert, etc.
├── datasource        — DataSource utilities, embedded databases, connection routing
├── object            — SQL-as-object model (MappingSqlQuery, SqlUpdate, StoredProcedure)
├── support           — SQLExceptionTranslator, JdbcDaoSupport, JdbcAccessor
└── (root)            — JdbcOperations interface, UncategorizedSQLException
```

Each package is independently usable — you can use `core` without `object`, or `datasource` without `core`.

## 2. Why & when

Raw JDBC requires ten or more lines for a simple query — `getConnection()`, `prepareStatement()`, `executeQuery()`, `close()` in finally blocks, `catch (SQLException)` everywhere, and vendor-specific error code handling. Spring JDBC reduces this to a single method call:

```java
// Raw JDBC: ~15 lines, 3 try-finally, vendor-specific exception handling
// Spring JDBC: 1 line
List<String> names = jdbc.queryForList("SELECT name FROM products", String.class);
```

Use Spring JDBC when:
- You need SQL control (complex queries, stored procedures, bulk operations).
- You're not using a full ORM (JPA/Hibernate).
- You need maximum performance — no entity lifecycle overhead.

## 3. Core concept

The five packages and their key classes:

**`org.springframework.jdbc.core`** — the main API:
- `JdbcTemplate` — central class; all CRUD operations as typed Java calls.
- `NamedParameterJdbcTemplate` — wraps `JdbcTemplate`; supports `:name` placeholders instead of `?`.
- `SimpleJdbcInsert` — configures INSERT from a table name + column map; handles key generation.
- `SimpleJdbcCall` — wraps stored procedure / function calls.
- `JdbcOperations` / `NamedParameterJdbcOperations` — interfaces for the templates (useful for mocking).

**`org.springframework.jdbc.datasource`** — connection and DataSource management:
- `DataSourceUtils` — `getConnection()`/`releaseConnection()` that participate in Spring transactions.
- `TransactionAwareDataSourceProxy` — wraps a DataSource so direct `getConnection()` calls join the active Spring transaction.
- `EmbeddedDatabaseBuilder` — builds in-memory H2/HSQL/Derby databases for tests.
- `LazyConnectionDataSourceProxy` — defers connection acquisition until first statement.
- `AbstractRoutingDataSource` — delegates to different DataSource implementations based on lookup key (tenant routing, read/write splitting).

**`org.springframework.jdbc.object`** — SQL-as-reusable-object:
- `MappingSqlQuery<T>` — a compiled parameterized SELECT that returns a `List<T>`.
- `SqlUpdate` — a compiled INSERT/UPDATE/DELETE.
- `StoredProcedure` — wraps stored procedure execution including IN/OUT parameters.
- (Less commonly used today — `JdbcTemplate` is usually preferred.)

**`org.springframework.jdbc.support`** — infrastructure:
- `SQLExceptionTranslator` / `SQLErrorCodeSQLExceptionTranslator` — converts `SQLException` to `DataAccessException`.
- `JdbcDaoSupport` — base class for DAOs; provides `setDataSource()` and `getJdbcTemplate()`.
- `KeyHolder` / `GeneratedKeyHolder` — captures auto-generated primary keys after INSERT.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <!-- core -->
  <rect x="10" y="10" width="200" height="110" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">jdbc.core</text>
  <line x1="20" y1="38" x2="200" y2="38" stroke="#8b949e" stroke-width="0.5"/>
  <text x="110" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">JdbcTemplate</text>
  <text x="110" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">NamedParameterJdbcTemplate</text>
  <text x="110" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">SimpleJdbcInsert</text>
  <text x="110" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">SimpleJdbcCall</text>
  <text x="110" y="110" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">main API — use this daily</text>

  <!-- datasource -->
  <rect x="220" y="10" width="200" height="110" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="30" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">jdbc.datasource</text>
  <line x1="230" y1="38" x2="410" y2="38" stroke="#8b949e" stroke-width="0.5"/>
  <text x="320" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">DataSourceUtils</text>
  <text x="320" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">EmbeddedDatabaseBuilder</text>
  <text x="320" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">AbstractRoutingDataSource</text>
  <text x="320" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">LazyConnectionDataSourceProxy</text>
  <text x="320" y="110" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">connection + routing</text>

  <!-- object -->
  <rect x="430" y="10" width="260" height="110" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="560" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">jdbc.object</text>
  <line x1="440" y1="38" x2="680" y2="38" stroke="#8b949e" stroke-width="0.5"/>
  <text x="560" y="54" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">MappingSqlQuery&lt;T&gt;</text>
  <text x="560" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">SqlUpdate</text>
  <text x="560" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">StoredProcedure</text>
  <text x="560" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(compiled SQL objects)</text>
  <text x="560" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">less common; JdbcTemplate preferred</text>

  <!-- support -->
  <rect x="10" y="140" width="420" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="220" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">jdbc.support</text>
  <line x1="20" y1="165" x2="420" y2="165" stroke="#8b949e" stroke-width="0.5"/>
  <text x="220" y="180" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">SQLErrorCodeSQLExceptionTranslator  |  JdbcDaoSupport  |  GeneratedKeyHolder</text>
  <text x="220" y="198" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">infrastructure — exception translation, key capture, DAO base class</text>

  <!-- DataSource label -->
  <rect x="448" y="140" width="242" height="80" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="569" y="158" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Root: JdbcOperations</text>
  <line x1="458" y1="165" x2="680" y2="165" stroke="#8b949e" stroke-width="0.5"/>
  <text x="569" y="183" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">JdbcOperations (interface for JdbcTemplate)</text>
  <text x="569" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">UncategorizedSQLException</text>
</svg>

Five packages, each independently usable; `jdbc.core` is the daily-use API, `jdbc.support` is the infrastructure layer.

## 5. Runnable example

Scenario: a **`ProductCatalog`** service — basic `JdbcTemplate` queries (core), `EmbeddedDatabaseBuilder` (datasource), `GeneratedKeyHolder` (support), and `SimpleJdbcInsert` (core advanced).

### Level 1 — Basic

Core and datasource packages: `JdbcTemplate` + `EmbeddedDatabaseBuilder`.

```java
// SpringJdbcPackagesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.List;

@Configuration
public class SpringJdbcPackagesDemo {
    @Bean public DataSource dataSource() {
        // jdbc.datasource: EmbeddedDatabaseBuilder
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("catalog-schema.sql")
            .build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) {
        // jdbc.core: JdbcTemplate
        return new JdbcTemplate(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpringJdbcPackagesDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // INSERT
        jdbc.update("INSERT INTO products(name, price) VALUES(?,?)", "Widget", 9.99);
        jdbc.update("INSERT INTO products(name, price) VALUES(?,?)", "Gadget", 19.99);

        // SELECT list — queryForList
        List<String> names = jdbc.queryForList("SELECT name FROM products", String.class);
        System.out.println("Names: " + names);   // [Widget, Gadget]

        // COUNT — queryForObject
        int count = jdbc.queryForObject("SELECT COUNT(*) FROM products", Integer.class);
        System.out.println("Count: " + count);   // 2
        ctx.close();
    }
}
```

`catalog-schema.sql`: `CREATE TABLE products (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price DOUBLE);`

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. SpringJdbcPackagesDemo.java`

`EmbeddedDatabaseBuilder` (from `jdbc.datasource`) creates and initializes the H2 in-memory database. `JdbcTemplate` (from `jdbc.core`) eliminates all JDBC boilerplate — no `Connection`, no `PreparedStatement`, no `ResultSet` lifecycle code needed.

---

### Level 2 — Intermediate

Support package: `GeneratedKeyHolder` captures the auto-generated primary key after INSERT.

```java
// SpringJdbcPackagesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.datasource.embedded.*;
import org.springframework.jdbc.support.*;
import javax.sql.DataSource;
import java.sql.*;

@Configuration
public class SpringJdbcPackagesDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("catalog-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpringJdbcPackagesDemo.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // jdbc.support: GeneratedKeyHolder captures auto-generated key
        KeyHolder holder = new GeneratedKeyHolder();
        jdbc.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                "INSERT INTO products(name, price) VALUES(?,?)",
                Statement.RETURN_GENERATED_KEYS);
            ps.setString(1, "Sensor");
            ps.setDouble(2, 49.99);
            return ps;
        }, holder);

        long generatedId = holder.getKey().longValue();
        System.out.println("Generated ID: " + generatedId);

        // Verify
        String name = jdbc.queryForObject("SELECT name FROM products WHERE id=?", String.class, generatedId);
        System.out.println("Found: " + name + " (id=" + generatedId + ")");
        ctx.close();
    }
}
```

How to run: same classpath

`GeneratedKeyHolder` (from `jdbc.support`) is passed to the `update()` call. After execution, `holder.getKey()` contains the database-generated primary key. This is the Spring JDBC way to get back the key from an auto-increment column without a separate SELECT.

---

### Level 3 — Advanced

`SimpleJdbcInsert` (core) + `NamedParameterJdbcTemplate` (core) + `AbstractRoutingDataSource` (datasource) pattern sketch.

```java
// SpringJdbcPackagesDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.*;
import org.springframework.jdbc.core.namedparam.*;
import org.springframework.jdbc.core.simple.*;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

@Configuration
public class SpringJdbcPackagesDemo {
    @Bean public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder().setType(EmbeddedDatabaseType.H2)
            .addScript("catalog-schema.sql").build();
    }
    @Bean public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
    @Bean public NamedParameterJdbcTemplate namedJdbc(DataSource ds) {
        return new NamedParameterJdbcTemplate(ds);
    }

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpringJdbcPackagesDemo.class);
        DataSource ds = ctx.getBean(DataSource.class);
        NamedParameterJdbcTemplate named = ctx.getBean(NamedParameterJdbcTemplate.class);

        // SimpleJdbcInsert — table-aware insert with key generation
        SimpleJdbcInsert insertProduct = new SimpleJdbcInsert(ds)
            .withTableName("products")
            .usingGeneratedKeyColumns("id");

        Number id1 = insertProduct.executeAndReturnKey(Map.of("name","Router","price",129.99));
        Number id2 = insertProduct.executeAndReturnKey(Map.of("name","Switch","price",89.99));
        System.out.println("Inserted IDs: " + id1 + ", " + id2);

        // NamedParameterJdbcTemplate — :name placeholders (clearer than ?)
        var params = Map.of("minPrice", 90.0, "maxPrice", 200.0);
        List<Map<String,Object>> rows = named.queryForList(
            "SELECT id, name, price FROM products WHERE price BETWEEN :minPrice AND :maxPrice",
            params);
        rows.forEach(r -> System.out.printf("  id=%s name=%s price=%s%n", r.get("ID"), r.get("NAME"), r.get("PRICE")));

        ctx.close();
    }
}
```

How to run: same classpath

`SimpleJdbcInsert` (core) derives the column list from database metadata and handles key generation automatically — no hand-written INSERT SQL needed. `NamedParameterJdbcTemplate` (core) uses `:minPrice`/`:maxPrice` named parameters from a `Map`, eliminating positional `?` numbering mistakes in complex queries.

## 6. Walkthrough

**Level 2 — `GeneratedKeyHolder` flow:**

```
jdbc.update(psc, holder)
  → JdbcTemplate.execute(PreparedStatementCreator, PreparedStatementCallback):
      con = DataSourceUtils.getConnection(dataSource)
      ps = psc.createPreparedStatement(con)
         → "INSERT INTO products..." with RETURN_GENERATED_KEYS flag
      ps.executeUpdate()
         → H2: INSERT succeeds, generates id=1
      rs = ps.getGeneratedKeys()  ← H2 returns ResultSet with id=1
      KeyHolder.addValue("ID", 1, Types.BIGINT)  ← captured
      ps.close()
      DataSourceUtils.releaseConnection(con, dataSource)

holder.getKey() → 1L
```

**Package dependency view:**

```
Application code
  → jdbc.core (JdbcTemplate, SimpleJdbcInsert)
       → jdbc.support (SQLExceptionTranslator, KeyHolder)
       → jdbc.datasource (DataSourceUtils.getConnection)
            → your DataSource (HikariCP, EmbeddedDatabase, etc.)
```

## 7. Gotchas & takeaways

> **`JdbcTemplate` is thread-safe after construction.** Create one instance per `DataSource` and share it as a singleton `@Bean`. Do NOT create a new `JdbcTemplate` per request — each construction loads metadata and caches it.

> **`SimpleJdbcInsert` reads table metadata on first use.** If the database is not yet initialized when `SimpleJdbcInsert` is constructed, `usingGeneratedKeyColumns()` will fail. Construct `SimpleJdbcInsert` lazily or after schema initialization.

> **`DataSourceUtils.getConnection()` vs `dataSource.getConnection()`.** Always use `DataSourceUtils` (or `JdbcTemplate`) to get a connection inside a Spring-managed transaction — it returns the transaction-bound connection. `dataSource.getConnection()` always returns a fresh connection, bypassing the transaction.

- `jdbc.core` — daily use: `JdbcTemplate`, `NamedParameterJdbcTemplate`, `SimpleJdbcInsert`, `SimpleJdbcCall`.
- `jdbc.datasource` — connection management: `DataSourceUtils`, `EmbeddedDatabaseBuilder`, `AbstractRoutingDataSource`.
- `jdbc.support` — infrastructure: `SQLExceptionTranslator`, `GeneratedKeyHolder`, `JdbcDaoSupport`.
- `jdbc.object` — compiled SQL objects: `MappingSqlQuery`, `SqlUpdate`, `StoredProcedure` (rare today).
- `JdbcTemplate` is thread-safe — one instance per DataSource, shared as a `@Bean` singleton.
