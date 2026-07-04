---
card: spring-framework
gi: 266
slug: embedded-database-support-h2-hsql-derby
title: Embedded database support (H2, HSQL, Derby)
---

## 1. What it is

Spring's **embedded database support** creates a fully functional, in-process SQL database for tests or local development — no external database server required. Spring ships a builder API that creates the database, runs schema/data scripts, and exposes a `DataSource`:

```java
DataSource ds = new EmbeddedDatabaseBuilder()
    .setType(EmbeddedDatabaseType.H2)
    .addScript("classpath:schema.sql")
    .addScript("classpath:test-data.sql")
    .build();
```

Supported databases:

| Type | Driver class | Notes |
|---|---|---|
| `H2` | `org.h2.Driver` | Most popular; wide SQL dialect support; excellent tooling |
| `HSQL` | `org.hsqldb.jdbcDriver` | Long history; lighter footprint |
| `DERBY` | `org.apache.derby.jdbc.EmbeddedDriver` | Apache Derby; more ANSI-SQL strict |

All three run in the same JVM process — no TCP sockets, no external service to start or stop.

## 2. Why & when

The main use case is **automated testing** — integration and repository tests that need a real database without:
- Installing and starting a database server.
- Keeping test data isolated between test runs.
- CI/CD pipelines that can't access a real database.

**When to use embedded databases:**
- Unit/integration tests for `@Repository` classes.
- Local development when the production database is remote or requires special setup.
- Fast prototyping and demos.

**When NOT to use:**
- Production data (data vanishes on JVM shutdown for `mem:` URLs).
- Testing database-specific features (H2 doesn't support all PostgreSQL-specific SQL).
- Concurrency testing at scale (in-process databases share the JVM heap and GC).

## 3. Core concept

`EmbeddedDatabaseBuilder` lifecycle:

1. **`build()`** calls `EmbeddedDatabaseFactory.initDatabase()`.
2. The factory looks up the JDBC driver from the classpath, generates a unique database name (unless you set one), and opens the first connection — this initialises the database.
3. Script resources are executed in the order they are added via `addScript()`.
4. Returns an `EmbeddedDatabase` — which extends `DataSource` and adds `shutdown()`.

**Unique naming**: by default each `EmbeddedDatabaseBuilder.build()` call generates a fresh name, so each test gets its own isolated database even if tests run in parallel. Set `setName("myDb")` when you want a shared database.

**Spring XML bean** (for legacy XML configs):
```xml
<jdbc:embedded-database id="dataSource" type="H2">
    <jdbc:script location="classpath:schema.sql"/>
</jdbc:embedded-database>
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Builder -->
  <rect x="10" y="70" width="190" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="92" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EmbeddedDatabaseBuilder</text>
  <line x1="20" y1="98" x2="190" y2="98" stroke="#8b949e" stroke-width="0.5"/>
  <text x="105" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">setType(H2)</text>
  <text x="105" y="130" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">addScript(schema.sql)</text>
  <text x="105" y="142" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">addScript(data.sql)</text>

  <line x1="202" y1="110" x2="255" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="229" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">build()</text>

  <!-- Embedded DB factory -->
  <rect x="257" y="60" width="200" height="100" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="357" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">EmbeddedDatabaseFactory</text>
  <line x1="267" y1="88" x2="447" y2="88" stroke="#8b949e" stroke-width="0.5"/>
  <text x="357" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. generate unique DB name</text>
  <text x="357" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. open in-process H2 DB</text>
  <text x="357" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. run schema + data scripts</text>

  <line x1="459" y1="110" x2="510" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DataSource -->
  <rect x="512" y="85" width="170" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="597" y="106" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">EmbeddedDatabase</text>
  <text x="597" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">implements DataSource</text>

  <!-- In-memory -->
  <rect x="257" y="175" width="200" height="28" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="357" y="192" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">In-process JVM memory (no TCP)</text>
</svg>

The embedded database runs entirely inside the JVM — no port, no external server, no data on disk (for `mem:` URLs).

## 5. Runnable example

Scenario: a **user registry** — set up an H2 embedded database for integration tests, run schema and seed scripts, query data, and test in-process isolation.

### Level 1 — Basic

`EmbeddedDatabaseBuilder` for test schema setup.

```java
// EmbeddedDbDemo.java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import java.util.List;
import java.util.Map;

public class EmbeddedDbDemo {

    public static void main(String[] args) {
        // Build an H2 in-memory database and run setup scripts
        EmbeddedDatabase db = new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .addScript("classpath:user-schema.sql")
            .addScript("classpath:user-data.sql")
            .build();

        JdbcTemplate jdbc = new JdbcTemplate(db);

        // Query the seeded data
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM users", Integer.class);
        System.out.println("Users loaded: " + count);

        List<Map<String,Object>> users = jdbc.queryForList(
            "SELECT name, role FROM users ORDER BY name");
        users.forEach(u -> System.out.printf("  %-10s → %s%n", u.get("NAME"), u.get("ROLE")));

        // Embedded database is destroyed on shutdown
        db.shutdown();
        System.out.println("Database shut down — all data gone");
    }
}
```

`user-schema.sql`:
```sql
CREATE TABLE users (
  id   BIGINT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  email VARCHAR(200) UNIQUE,
  role VARCHAR(50)
);
```

`user-data.sql`:
```sql
INSERT INTO users(name,email,role) VALUES('Alice','alice@example.com','ADMIN');
INSERT INTO users(name,email,role) VALUES('Bob','bob@example.com','USER');
INSERT INTO users(name,email,role) VALUES('Carol','carol@example.com','USER');
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. EmbeddedDbDemo.java`

`EmbeddedDatabaseBuilder.build()` opens an H2 in-memory database, runs `user-schema.sql` to create the table, then `user-data.sql` to seed data — both via a `ScriptUtils.executeSqlScript()` call internally. `db.shutdown()` drops all tables and closes all connections; on the next `build()` the database starts fresh.

---

### Level 2 — Intermediate

Named database + `setGenerateUniqueName(false)` for shared test state + H2 console URL.

```java
// EmbeddedDbDemo.java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

public class EmbeddedDbDemo {

    static EmbeddedDatabase buildNamedDb(String name) {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .setName(name)                        // fixed name — same DB for multiple builders
            .setGenerateUniqueName(false)
            .addScript("classpath:user-schema.sql")
            .build();
    }

    public static void main(String[] args) {
        EmbeddedDatabase db1 = buildNamedDb("registry");
        JdbcTemplate jdbc = new JdbcTemplate(db1);

        jdbc.update("INSERT INTO users(name,email,role) VALUES(?,?,?)",
            "Alice","alice@example.com","ADMIN");
        jdbc.update("INSERT INTO users(name,email,role) VALUES(?,?,?)",
            "Bob","bob@example.com","USER");

        // Two different DataSource handles, same in-process DB
        EmbeddedDatabase db2 = buildNamedDb("registry");
        JdbcTemplate jdbc2 = new JdbcTemplate(db2);
        Integer seen = jdbc2.queryForObject("SELECT COUNT(*) FROM users", Integer.class);
        System.out.println("Seen via second handle: " + seen); // 2

        // H2 INFORMATION_SCHEMA — inspect the live database metadata
        List<String> tables = jdbc.queryForList(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA='PUBLIC'",
            String.class);
        System.out.println("Tables: " + tables);

        // H2 web console URL (useful during dev — prints to stdout when H2Server started)
        try {
            var meta = db1.getConnection().getMetaData();
            System.out.println("JDBC URL: " + meta.getURL());
            System.out.println("DB product: " + meta.getDatabaseProductName()
                + " " + meta.getDatabaseProductVersion());
        } catch (Exception e) { e.printStackTrace(); }

        db1.shutdown();
    }
}
```

How to run: same classpath

With `setName("registry")` and `setGenerateUniqueName(false)`, both `buildNamedDb("registry")` calls open the **same** H2 in-memory database. Data inserted through `db1` is immediately visible through `db2`. This simulates shared state — useful when your test context wires multiple beans that all need the same database handle.

---

### Level 3 — Advanced

H2 file-backed database + multiple script directories + programmatic Spring `@Configuration` for test context.

```java
// EmbeddedDbDemo.java
import org.springframework.context.annotation.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.embedded.*;
import javax.sql.DataSource;
import java.util.*;

@Configuration
class TestConfig {
    @Bean
    public DataSource dataSource() {
        return new EmbeddedDatabaseBuilder()
            .setType(EmbeddedDatabaseType.H2)
            .setName("testDb")
            // Script in classpath root
            .addScript("classpath:user-schema.sql")
            // Inline SQL (useful in tests when you don't want a separate file)
            .addScripts(
                "classpath:user-data.sql"
            )
            // H2 compatibility mode — run in MySQL compatibility for dialect testing
            // (add SET MODE=MySQL at top of schema.sql for this to take effect)
            .build();
    }

    @Bean
    public JdbcTemplate jdbcTemplate(DataSource ds) {
        return new JdbcTemplate(ds);
    }
}

public class EmbeddedDbDemo {

    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TestConfig.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // Insert extra rows
        jdbc.batchUpdate("INSERT INTO users(name,email,role) VALUES(?,?,?)",
            List.of(
                new Object[]{"Dave","dave@example.com","USER"},
                new Object[]{"Eve","eve@example.com","MODERATOR"},
                new Object[]{"Frank","frank@example.com","ADMIN"}
            ));

        // Group by role
        Map<String,Integer> byRole = new LinkedHashMap<>();
        jdbc.query("SELECT role, COUNT(*) cnt FROM users GROUP BY role ORDER BY role",
            rs -> { byRole.put(rs.getString("role"), rs.getInt("cnt")); });
        System.out.println("Users by role: " + byRole);

        // H2 EXPLAIN PLAN — check index usage
        String plan = jdbc.queryForObject(
            "EXPLAIN SELECT * FROM users WHERE email=?",
            String.class, "alice@example.com");
        System.out.println("Query plan:\n  " + plan);

        // Spring manages DataSource lifecycle — shutdown closes embedded DB
        ctx.close();
        System.out.println("Context closed — embedded DB destroyed");
    }
}
```

How to run: same classpath

Wiring `EmbeddedDatabase` as a `@Bean` means Spring's `ApplicationContext.close()` calls `db.shutdown()` automatically via the `DisposableBean` interface — no manual `shutdown()` needed. `EXPLAIN` in H2 shows the query plan — useful for verifying that UNIQUE indices are used as expected during test runs.

## 6. Walkthrough

**Level 1 — `EmbeddedDatabaseBuilder.build()` execution order:**

1. **`new EmbeddedDatabaseBuilder().setType(H2).addScript("user-schema.sql").addScript("user-data.sql").build()`**: `EmbeddedDatabaseFactory.initDatabase()` is called.
2. **Database name**: `generateUniqueName=true` by default → UUID-based name, e.g. `testdb_a3f7c9d2`. H2 in-memory URL becomes `jdbc:h2:mem:testdb_a3f7c9d2`.
3. **Driver registration**: H2's `Driver.class` is loaded from classpath and registered with `DriverManager`.
4. **First connection**: `DriverManager.getConnection("jdbc:h2:mem:testdb_a3f7c9d2","sa","")` — this creates the in-memory database (it didn't exist before the first connection).
5. **Script execution — `user-schema.sql`**: `ScriptUtils.executeSqlScript(con, resource)` reads the file, splits by `;`, calls `stmt.execute("CREATE TABLE users (...)")` — table created.
6. **Script execution — `user-data.sql`**: same mechanism — 3 INSERT statements run on the same connection.
7. **`build()` returns** `SimpleDriverDataSource`-backed `EmbeddedDatabase` object.
8. **`db.shutdown()`**: closes all open connections → H2 drops the in-memory database (all data gone).

```
Embedded DB lifecycle:
  build()     → CREATE DATABASE in JVM memory
  addScript() → CREATE TABLE + INSERT (in script order)
  getConnection() → returns connection from simple single-connection source
  shutdown()  → DROP DATABASE (data gone from JVM memory)
```

## 7. Gotchas & takeaways

> **H2 defaults to H2-dialect SQL, not MySQL or PostgreSQL.** If your production schema uses MySQL-specific syntax (e.g., backtick identifiers, `TINYINT(1)` for boolean), H2 will reject it. Fix: add `SET MODE=MySQL` as the first statement in your schema script, or use `COMPATIBILITY_MODE=MySQL` in the JDBC URL.

> **Unique name generation is on by default.** Each `build()` creates a new isolated database. When you want tests to share a database (e.g., a `@TestConfiguration` bean), use `setName("fixed")` + `setGenerateUniqueName(false)`.

> **`EmbeddedDatabase` extends `DataSource` and `DisposableBean`.** When registered as a Spring bean, it is shut down automatically on `ApplicationContext.close()` — no manual cleanup needed. Outside of Spring, always call `db.shutdown()`.

- `EmbeddedDatabaseType.H2` — most common; `HSQL` and `DERBY` are alternatives.
- Scripts run in the order added — schema before data.
- Unique name by default → isolated per `build()` call → safe for parallel tests.
- `setName("x") + setGenerateUniqueName(false)` — share state across beans in one test context.
- In a Spring `@Bean`, lifecycle is managed automatically — `close()` on the context shuts down the DB.
