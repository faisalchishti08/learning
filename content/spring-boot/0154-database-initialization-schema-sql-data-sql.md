---
card: spring-boot
gi: 154
slug: database-initialization-schema-sql-data-sql
title: Database initialization (schema.sql / data.sql)
---

## 1. What it is

Spring Boot can run SQL scripts automatically at startup to create tables (`schema.sql`) and seed data (`data.sql`). These scripts are detected on the classpath and executed against the configured `DataSource` — before the application handles any requests. The behaviour is controlled by `spring.sql.init.mode`: `embedded` (default — runs only for embedded DBs like H2), `always` (runs for any DataSource), or `never`.

## 2. Why & when

For development and tests you often need a fresh, predictable schema and seed data every run. `schema.sql` + `data.sql` are the simplest way to achieve this for embedded databases, without Flyway or Liquibase overhead.

Use them when:

- Running integration tests against H2 — simple schema setup, no migration tooling.
- Bootstrapping dev data (reference tables, test users) that should always exist.
- You are not yet using a migration tool and want minimal setup.

For production, prefer **Flyway** or **Liquibase** (versioned migrations, rollback support, execution history) over plain `schema.sql` which runs unconditionally and overwrites existing data.

## 3. Core concept

Execution order and precedence:

```
Embedded DB detected (or spring.sql.init.mode=always)
  1. schema.sql executed (DDL — CREATE TABLE, etc.)
  2. data.sql executed   (DML — INSERT, etc.)
  3. JPA / Hibernate runs (if present)
     → ddl-auto applies AFTER script init
```

With JPA, if you use `schema.sql` for DDL and `data.sql` for seed data, set `spring.jpa.defer-datasource-initialization=true` so Hibernate's `ddl-auto` runs *before* `data.sql` — otherwise `data.sql` may try to insert rows into tables that don't exist yet.

Location: `src/main/resources/schema.sql` and `src/main/resources/data.sql` (or `schema-<platform>.sql` for platform-specific files).

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring Boot starts</text>
  <rect x="235" y="55" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">1. schema.sql (DDL)</text>
  <rect x="235" y="110" width="160" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="315" y="134" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">2. data.sql (DML)</text>
  <rect x="475" y="80" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="108" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">App ready</text>
  <line x1="162" y1="105" x2="231" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sq)"/>
  <line x1="162" y1="105" x2="231" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sq)"/>
  <line x1="397" y1="105" x2="471" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sq2)"/>
  <defs>
    <marker id="sq" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sq2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`schema.sql` runs first (creates tables), then `data.sql` (inserts rows); app starts only after both succeed.

## 5. Runnable example

```java
// SqlInitApp.java — Spring Boot project
// pom.xml: spring-boot-starter-jdbc, com.h2database:h2 (runtime)
// application.properties:
//   spring.sql.init.mode=always
//   spring.sql.init.schema-locations=classpath:schema.sql
//   spring.sql.init.data-locations=classpath:data.sql
//
// src/main/resources/schema.sql:
//   DROP TABLE IF EXISTS category;
//   CREATE TABLE category (
//     id   INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
//     name VARCHAR(100) NOT NULL UNIQUE
//   );
//
// src/main/resources/data.sql:
//   INSERT INTO category (name) VALUES ('Electronics');
//   INSERT INTO category (name) VALUES ('Books');
//   INSERT INTO category (name) VALUES ('Tools');

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@SpringBootApplication
public class SqlInitApp {
    public static void main(String[] args) {
        SpringApplication.run(SqlInitApp.class, args);
    }
}

@RestController
class CategoryController {

    private final JdbcTemplate jdbc;

    CategoryController(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @GetMapping("/categories")
    public List<Map<String, Object>> categories() {
        return jdbc.queryForList("SELECT * FROM category ORDER BY id");
    }
}
```

**How to run:**
1. Create `schema.sql` and `data.sql` in `src/main/resources/` with the content shown in comments.
2. Start the app.
3. `curl http://localhost:8080/categories` → `[{"ID":1,"NAME":"Electronics"},…]`
4. Restart — data resets because `schema.sql` drops and recreates the table each time.

## 6. Walkthrough

- `spring.sql.init.mode=always` forces script execution even for a non-embedded DB (H2 file-based, PostgreSQL, etc.). Without it, execution only happens for embedded databases.
- `spring.sql.init.schema-locations=classpath:schema.sql` allows overriding the default location. Multiple files: `classpath:schema-1.sql,classpath:schema-2.sql`.
- `DROP TABLE IF EXISTS category` in `schema.sql` makes the script idempotent — each restart begins with a clean slate. On a real production database you'd omit the `DROP` and use migration tooling instead.
- `data.sql` runs after `schema.sql` in the same transaction (if the driver supports it). All three rows are inserted before the app accepts requests.
- `JdbcTemplate.queryForList("SELECT * FROM category")` returns each row as a `Map<String, Object>` — easy to serialise as JSON.
- If you add JPA (`spring-boot-starter-data-jpa`), set `spring.jpa.defer-datasource-initialization=true` so Hibernate validates/creates tables *before* `data.sql` inserts rows.

## 7. Gotchas & takeaways

> Running `schema.sql` with `DROP TABLE IF EXISTS` on a production database **destroys real data**. Use this pattern only for embedded DBs in dev/test; switch to Flyway or Liquibase for production schema management.

> `spring.sql.init.mode=always` silently overwrites existing tables on every restart. If you point a production DataSource at this config, you will lose data.

- `schema-h2.sql` and `data-h2.sql` (platform-specific) run only when the database platform matches — useful for multi-DB test suites.
- `spring.sql.init.encoding` sets the script file encoding (default: platform charset). Use `UTF-8` to be safe.
- `spring.sql.init.separator` is the statement separator (default: `;`). Change to `;;` for stored procedures that contain `;` internally.
- `@Sql` annotation on test classes loads per-test SQL scripts — more granular than global `data.sql`.
- Spring Boot 2.5+ moved from `spring.datasource.initialization-mode` to `spring.sql.init.mode` — old property is ignored in Boot 3.x.
