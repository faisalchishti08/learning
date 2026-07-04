---
card: spring-framework
gi: 267
slug: initializing-a-datasource-schema-data-scripts
title: Initializing a DataSource (schema/data scripts)
---

## 1. What it is

**DataSource initialization** in Spring runs SQL scripts against a `DataSource` at startup — typically to create the schema and load seed data. Spring provides three mechanisms:

1. **`EmbeddedDatabaseBuilder.addScript()`** — for embedded (in-memory) databases.
2. **`DataSourceInitializer`** — programmatic, works with any `DataSource` (including external).
3. **`ResourceDatabasePopulator`** — low-level utility that runs scripts against any `Connection`.

In Spring Boot the equivalent is `spring.sql.init.schema-locations` / `spring.sql.init.data-locations` properties, but the underlying classes are the same.

```java
// Programmatic initialization of an external DataSource
ResourceDatabasePopulator populator = new ResourceDatabasePopulator();
populator.addScript(new ClassPathResource("schema.sql"));
populator.addScript(new ClassPathResource("data.sql"));
populator.execute(dataSource);
```

## 2. Why & when

SQL scripts for initialization are useful when:
- **Tests** need a fresh schema before each test class.
- **Local development** uses an external database (not embedded) and you want a reproducible schema.
- **CI/CD** spins up a database service (e.g., Docker PostgreSQL) and needs the schema applied before tests run.
- **Demo / documentation** datasets need to be repeatable.

Alternatives:
- **Flyway / Liquibase** — for production database migrations with version tracking and rollback. Prefer these for production schemas.
- **JPA `ddl-auto=create-drop`** — schema from entity annotations; useful for prototyping but loses control over the exact DDL.

## 3. Core concept

`ResourceDatabasePopulator` wraps `ScriptUtils.executeSqlScript()` — the core script runner:

1. Load each `Resource` (classpath, file, URL).
2. Split content by statement separator (default `;`).
3. Execute each statement with `Statement.execute()` or `PreparedStatement.execute()`.
4. On error: throw `ScriptStatementFailedException` by default; or continue with `setContinueOnError(true)`.

Key options:

| Option | Default | Effect |
|---|---|---|
| `setSeparator(str)` | `;` | Statement delimiter |
| `setCommentPrefixes(arr)` | `--`, `#` | Ignore comment lines |
| `setContinueOnError(bool)` | false | Log but don't throw on error |
| `setIgnoreFailedDrops(bool)` | false | Ignore `DROP TABLE` failures (useful when table may not exist) |
| `setSqlScriptEncoding(charset)` | UTF-8 | Script file encoding |

`DataSourceInitializer` wraps a `ResourceDatabasePopulator` with a Spring lifecycle hook — its `afterPropertiesSet()` method fires when the bean is created, which is guaranteed to happen before `JdbcTemplate` beans that depend on the schema.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Scripts -->
  <rect x="10" y="50" width="120" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="68" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">schema.sql</text>
  <rect x="10" y="95" width="120" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="113" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">data.sql</text>

  <line x1="132" y1="65" x2="195" y2="95" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="132" y1="110" x2="195" y2="110" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>

  <!-- ResourceDatabasePopulator -->
  <rect x="197" y="55" width="230" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="312" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ResourceDatabasePopulator</text>
  <line x1="207" y1="83" x2="417" y2="83" stroke="#8b949e" stroke-width="0.5"/>
  <text x="312" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">1. load + split by ";"</text>
  <text x="312" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">2. stmt.execute(sql) × N</text>
  <text x="312" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">3. error? throw / log&amp;continue</text>

  <line x1="429" y1="105" x2="480" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DataSource -->
  <rect x="482" y="80" width="160" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="562" y="101" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">DataSource</text>
  <text x="562" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">H2 / PostgreSQL</text>

  <!-- DataSourceInitializer wrapper -->
  <rect x="197" y="170" width="230" height="35" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="312" y="191" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">DataSourceInitializer (Spring bean wrapper)</text>
</svg>

Scripts are loaded from classpath or filesystem, split by `;`, executed statement-by-statement against the `DataSource`.

## 5. Runnable example

Scenario: an **inventory system** — initialize an H2 database with schema and seed scripts, then demonstrate `DataSourceInitializer` with `setIgnoreFailedDrops`, and finally show conditional initialization.

### Level 1 — Basic

`ResourceDatabasePopulator.execute(dataSource)` to apply schema and seed data.

```java
// DataSourceInitDemo.java
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import javax.sql.DataSource;
import java.util.List;
import java.util.Map;

public class DataSourceInitDemo {

    static DataSource buildDs() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setDriverClassName("org.h2.Driver");
        ds.setUrl("jdbc:h2:mem:inventory;DB_CLOSE_DELAY=-1");
        ds.setUsername("sa"); ds.setPassword("");
        return ds;
    }

    public static void main(String[] args) {
        DataSource ds = buildDs();

        // Apply schema and seed scripts manually
        ResourceDatabasePopulator populator = new ResourceDatabasePopulator();
        populator.addScript(new ClassPathResource("inventory-schema.sql"));
        populator.addScript(new ClassPathResource("inventory-data.sql"));
        populator.execute(ds);   // runs both scripts against the DataSource

        JdbcTemplate jdbc = new JdbcTemplate(ds);
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM inventory", Integer.class);
        System.out.println("Inventory items loaded: " + count);

        List<Map<String,Object>> items = jdbc.queryForList(
            "SELECT sku, name, qty FROM inventory ORDER BY sku");
        items.forEach(i -> System.out.printf("  %-10s %-20s qty=%s%n",
            i.get("SKU"), i.get("NAME"), i.get("QTY")));
    }
}
```

`inventory-schema.sql`:
```sql
CREATE TABLE inventory (
  id  BIGINT AUTO_INCREMENT PRIMARY KEY,
  sku VARCHAR(20) NOT NULL UNIQUE,
  name VARCHAR(100),
  qty INT DEFAULT 0
);
```

`inventory-data.sql`:
```sql
INSERT INTO inventory(sku,name,qty) VALUES('WID-001','Widget',150);
INSERT INTO inventory(sku,name,qty) VALUES('GAD-002','Gadget',75);
INSERT INTO inventory(sku,name,qty) VALUES('SEN-003','Sensor',200);
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. DataSourceInitDemo.java`

`ResourceDatabasePopulator.execute(ds)` acquires a connection from `ds`, iterates each script resource, splits on `;`, and calls `stmt.execute(sql)` for each statement. If any statement fails, it throws `ScriptStatementFailedException` immediately.

---

### Level 2 — Intermediate

`DataSourceInitializer` as a Spring bean + `setIgnoreFailedDrops(true)` for idempotent schema scripts.

```java
// DataSourceInitDemo.java
import org.springframework.context.annotation.*;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.init.*;
import javax.sql.DataSource;
import java.util.*;

@Configuration
class DbConfig {
    @Bean
    public DataSource dataSource() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setDriverClassName("org.h2.Driver");
        ds.setUrl("jdbc:h2:mem:inventory;DB_CLOSE_DELAY=-1");
        ds.setUsername("sa"); ds.setPassword("");
        return ds;
    }

    @Bean
    public DataSourceInitializer dataSourceInitializer(DataSource ds) {
        ResourceDatabasePopulator pop = new ResourceDatabasePopulator();
        pop.addScript(new ClassPathResource("inventory-schema.sql"));
        pop.addScript(new ClassPathResource("inventory-data.sql"));
        // Ignore "table not found" on DROP TABLE IF EXISTS statements
        pop.setIgnoreFailedDrops(true);
        // Continue on errors (useful when some CREATE statements may already exist)
        // pop.setContinueOnError(true);

        DataSourceInitializer init = new DataSourceInitializer();
        init.setDataSource(ds);
        init.setDatabasePopulator(pop);
        init.setEnabled(true);   // flip to false to skip init (e.g., prod profile)
        return init;
    }

    @Bean
    public JdbcTemplate jdbcTemplate(DataSource ds) {
        return new JdbcTemplate(ds);
    }
}

public class DataSourceInitDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DbConfig.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // Schema + data already applied by DataSourceInitializer before this bean was created
        List<String> skus = jdbc.queryForList("SELECT sku FROM inventory ORDER BY sku", String.class);
        System.out.println("SKUs after init: " + skus);

        // Add more items at runtime
        jdbc.update("INSERT INTO inventory(sku,name,qty) VALUES(?,?,?)", "REL-004","Relay",90);
        Integer total = jdbc.queryForObject("SELECT SUM(qty) FROM inventory", Integer.class);
        System.out.println("Total qty: " + total);

        ctx.close();
    }
}
```

How to run: same classpath

`DataSourceInitializer` implements `InitializingBean` — `afterPropertiesSet()` fires when Spring builds the bean, which is before any bean that declares a dependency on `DataSource`. `setEnabled(false)` is handy for production profiles where you want Flyway to manage the schema instead.

---

### Level 3 — Advanced

Multi-script initialization with separator and encoding config + a cleanup script wired as `DataSourceDestroyer`.

```java
// DataSourceInitDemo.java
import org.springframework.context.annotation.*;
import org.springframework.core.io.*;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import org.springframework.jdbc.datasource.init.*;
import javax.sql.DataSource;
import java.nio.charset.StandardCharsets;
import java.util.*;

@Configuration
class DbConfig {
    @Bean
    public DataSource dataSource() {
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setDriverClassName("org.h2.Driver");
        ds.setUrl("jdbc:h2:mem:inventory;DB_CLOSE_DELAY=-1");
        ds.setUsername("sa"); ds.setPassword("");
        return ds;
    }

    @Bean
    public DataSourceInitializer dataSourceInitializer(DataSource ds) {
        ResourceDatabasePopulator pop = new ResourceDatabasePopulator();
        // Multiple scripts in order
        pop.addScripts(
            new ClassPathResource("inventory-schema.sql"),
            new ClassPathResource("inventory-data.sql"),
            new ClassPathResource("inventory-indexes.sql")
        );
        pop.setSqlScriptEncoding(StandardCharsets.UTF_8.name());
        pop.setSeparator(";");         // explicit (default); use "//" for PL/SQL-style
        pop.setCommentPrefixes("--", "#");  // both ANSI and shell-style comments ignored
        pop.setIgnoreFailedDrops(true);

        DataSourceInitializer init = new DataSourceInitializer();
        init.setDataSource(ds);
        init.setDatabasePopulator(pop);

        // Destroy script — runs on ApplicationContext.close()
        ResourceDatabasePopulator cleaner = new ResourceDatabasePopulator();
        cleaner.addScript(new ClassPathResource("inventory-cleanup.sql"));
        init.setDatabaseCleaner(cleaner);

        return init;
    }

    @Bean
    public JdbcTemplate jdbcTemplate(DataSource ds) { return new JdbcTemplate(ds); }
}

public class DataSourceInitDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DbConfig.class);
        JdbcTemplate jdbc = ctx.getBean(JdbcTemplate.class);

        // Verify schema + indexes
        List<String> indexes = jdbc.queryForList(
            "SELECT INDEX_NAME FROM INFORMATION_SCHEMA.INDEXES WHERE TABLE_NAME='INVENTORY'",
            String.class);
        System.out.println("Indexes: " + indexes);

        // Insert and query
        jdbc.update("INSERT INTO inventory(sku,name,qty) VALUES(?,?,?)", "TIM-005","Timer",50);
        jdbc.queryForList("SELECT sku,name,qty FROM inventory ORDER BY sku", Map.class)
            .forEach(r -> System.out.printf("  %-10s %-15s %s%n",
                r.get("SKU"), r.get("NAME"), r.get("QTY")));

        // ctx.close() fires DataSourceDestroyer → runs inventory-cleanup.sql
        ctx.close();
        System.out.println("Context closed — cleanup script ran");
    }
}
```

`inventory-indexes.sql`: `CREATE INDEX IF NOT EXISTS idx_inventory_sku ON inventory(sku);`

`inventory-cleanup.sql`: `DROP TABLE IF EXISTS inventory;`

How to run: same classpath

`setDatabaseCleaner(populator)` runs the cleaner scripts when the `ApplicationContext` closes via `DataSourceInitializer.destroy()`. This is ideal for test teardown — the test context creates the schema, tests run, then cleanup scripts restore the database to a known state for the next test class.

## 6. Walkthrough

**Level 2 — `DataSourceInitializer` bean lifecycle (execution order):**

1. **`AnnotationConfigApplicationContext(DbConfig.class)`** starts. Spring discovers `@Bean` methods: `dataSource`, `dataSourceInitializer`, `jdbcTemplate`.
2. **`dataSource()` bean created first** — `DriverManagerDataSource` constructed. No DB connection yet.
3. **`dataSourceInitializer(ds)` bean created** — `DataSourceInitializer` constructed with populator and DataSource reference. Spring calls `afterPropertiesSet()`:
   - `ResourceDatabasePopulator.populate(con)` called with a connection from `ds`.
   - `ScriptUtils.executeSqlScript(con, inventory-schema.sql)` — splits on `;`, executes `CREATE TABLE inventory (...)`.
   - `ScriptUtils.executeSqlScript(con, inventory-data.sql)` — executes 3 INSERT statements.
   - Connection closed/returned.
4. **`jdbcTemplate(ds)` bean created** — `JdbcTemplate` wrapping the same `DataSource`.
5. **`main()` executes** — `jdbc.queryForList("SELECT sku FROM inventory...")` — schema and data already present from step 3.

```
Bean creation order:
  dataSource → dataSourceInitializer (runs scripts) → jdbcTemplate

Scripts run during dataSourceInitializer.afterPropertiesSet():
  inventory-schema.sql:
    stmt.execute("CREATE TABLE inventory (id BIGINT AUTO_INCREMENT PRIMARY KEY, ...)")
  inventory-data.sql:
    stmt.execute("INSERT INTO inventory(sku,name,qty) VALUES('WID-001','Widget',150)")
    stmt.execute("INSERT INTO inventory(sku,name,qty) VALUES('GAD-002','Gadget',75)")
    stmt.execute("INSERT INTO inventory(sku,name,qty) VALUES('SEN-003','Sensor',200)")
```

## 7. Gotchas & takeaways

> **Script execution order matters.** Spring executes scripts exactly in the order they are added via `addScript()` / `addScripts()`. Always add `schema.sql` before `data.sql` — data inserts will fail if the table doesn't exist yet.

> **`setContinueOnError(true)` silently swallows errors.** Only use it when you know some statements may fail (e.g., `CREATE INDEX IF NOT EXISTS` on a DB that doesn't support `IF NOT EXISTS`). Leaving it on in normal operation hides real bugs.

> **`DataSourceInitializer` runs once per `ApplicationContext` creation.** In tests using `@SpringBootTest` with `@DirtiesContext`, the context is rebuilt for each test class — schema + data scripts run again. Without `@DirtiesContext`, scripts run once and state accumulates across tests, causing unique-constraint failures on second runs.

- `ResourceDatabasePopulator.execute(ds)` — simplest: runs scripts on demand.
- `DataSourceInitializer` — Spring bean; scripts run during `afterPropertiesSet()`, before any dependent beans.
- `setIgnoreFailedDrops(true)` — safe for idempotent scripts with `DROP TABLE IF EXISTS`.
- `setDatabaseCleaner(populator)` — teardown scripts run on `ApplicationContext.close()`.
- For production schema evolution, use Flyway or Liquibase instead of static scripts.
