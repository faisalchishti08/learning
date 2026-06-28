---
card: spring-boot
gi: 153
slug: jooq-support
title: jOOQ support
---

## 1. What it is

**jOOQ (Java Object Oriented Querying)** is a library that generates Java classes from your database schema and lets you write type-safe SQL as Java code. Instead of string SQL prone to typos and injection, you write `dsl.selectFrom(PRODUCT).where(PRODUCT.PRICE.lt(50.0)).fetch()`. Spring Boot auto-configures a `DSLContext` bean (jOOQ's main entry point) from the auto-configured `DataSource` when `spring-boot-starter-jooq` is on the classpath.

## 2. Why & when

JPA abstracts SQL away — good for simple CRUD, but you lose control over complex joins, window functions, and database-specific features. Raw SQL strings are flexible but brittle and injection-prone. jOOQ is the middle ground:

- **Type-safe SQL** — column references and values are typed; the compiler catches errors.
- **Full SQL coverage** — CTEs, window functions, `ON CONFLICT`, `UPSERT`, lateral joins — anything your database supports.
- **Auto-completion** — IDE gives you table and column names from generated classes.

Use jOOQ when you want SQL's full power but refuse to sacrifice type safety. Combine with Spring Data JPA for simple CRUD (let repositories handle it) and jOOQ for complex queries.

## 3. Core concept

jOOQ workflow:

1. **Code generation** — jOOQ reads your schema (from DB or Flyway migrations) and generates Java classes representing tables, records, and enums under `src/generated/`.
2. **`DSLContext`** — the query builder and executor. Auto-configured by Spring Boot from the `DataSource` and SQL dialect.
3. **Type-safe queries** — table and column references are generated constants (`Tables.PRODUCT`, `PRODUCT.NAME`).

Without code generation you can still use jOOQ in "plain SQL" mode — less type safety but useful for dynamic queries:

```java
dsl.fetch("SELECT * FROM product WHERE price < {0}", 50.0);
```

Spring Boot sets the SQL dialect from the `DataSource` URL automatically (`POSTGRES`, `MYSQL`, `H2`, etc.).

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="105" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your Java code</text>
  <text x="95" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">dsl.select(…)</text>
  <rect x="245" y="55" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="332" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">DSLContext</text>
  <text x="332" y="96" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">dialect-aware SQL builder</text>
  <rect x="245" y="130" width="175" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="332" y="152" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">Generated classes</text>
  <text x="332" y="169" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Tables.PRODUCT, etc.</text>
  <rect x="495" y="80" width="165" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="577" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">DataSource</text>
  <text x="577" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">→ Database</text>
  <line x1="172" y1="110" x2="241" y2="84" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jq)"/>
  <line x1="422" y1="82" x2="491" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jq2)"/>
  <line x1="172" y1="120" x2="241" y2="155" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#jq3)"/>
  <defs>
    <marker id="jq" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jq2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jq3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`DSLContext` (auto-configured) builds dialect-aware SQL from Java method chains; generated classes provide type-safe table/column references.

## 5. Runnable example

```java
// JooqApp.java — Spring Boot project using jOOQ in plain-SQL mode (no code generation)
// pom.xml: spring-boot-starter-jooq, com.h2database:h2 (runtime), spring-boot-starter-jdbc
// schema.sql:
//   CREATE TABLE product (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), price DOUBLE);
// data.sql:
//   INSERT INTO product (name, price) VALUES ('Widget', 9.99), ('Gadget', 24.99), ('Sprocket', 4.49);

import org.jooq.DSLContext;
import org.jooq.Field;
import org.jooq.Record;
import org.jooq.impl.DSL;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@SpringBootApplication
public class JooqApp {
    public static void main(String[] args) {
        SpringApplication.run(JooqApp.class, args);
    }
}

@RestController
@RequestMapping("/products")
class ProductController {

    private final DSLContext dsl;

    ProductController(DSLContext dsl) { this.dsl = dsl; }

    // Plain SQL — no generated classes needed
    @GetMapping
    public List<Map<String, Object>> all() {
        return dsl.fetch("SELECT id, name, price FROM product ORDER BY id")
                  .intoMaps();
    }

    // Type-safe DSL with inline table/field definitions
    @GetMapping("/cheap")
    public List<Map<String, Object>> cheap(@RequestParam(defaultValue = "10") double max) {
        var product = DSL.table("product");
        Field<Double> price = DSL.field("price", Double.class);

        return dsl.selectFrom(product)
                  .where(price.lt(max))
                  .orderBy(price)
                  .fetch()
                  .intoMaps();
    }

    // Aggregation — sum of all prices per first-letter group
    @GetMapping("/stats")
    public List<Map<String, Object>> stats() {
        return dsl.fetch(
            "SELECT SUBSTRING(name, 1, 1) AS prefix, COUNT(*) AS cnt, SUM(price) AS total " +
            "FROM product GROUP BY prefix ORDER BY prefix"
        ).intoMaps();
    }

    @PostMapping
    public String add(@RequestParam String name, @RequestParam double price) {
        int rows = dsl.execute(
            "INSERT INTO product (name, price) VALUES (?, ?)", name, price);
        return rows + " row(s) inserted";
    }
}
```

**How to run:** add `spring-boot-starter-jooq` and H2, create `schema.sql` and `data.sql`, start the app, then:
- `curl http://localhost:8080/products` → all products
- `curl "http://localhost:8080/products/cheap?max=10"` → products under £10
- `curl http://localhost:8080/products/stats` → group stats

## 6. Walkthrough

- `spring-boot-starter-jooq` triggers `JooqAutoConfiguration`. It detects the `DataSource` and the SQL dialect (H2 from the URL) and creates a `DSLContext` bean configured with the H2 dialect.
- `dsl.fetch("SELECT …")` executes plain SQL and returns a jOOQ `Result<Record>`. `.intoMaps()` converts each `Record` to a `Map<String,Object>` — convenient for REST responses without extra mapping code.
- `DSL.table("product")` and `DSL.field("price", Double.class)` create inline table/field references without generated classes. This is the "plain mode" — less type safety but no code generation required.
- `price.lt(max)` builds a `WHERE price < ?` condition; jOOQ handles parameter binding safely — no SQL injection possible because the value is bound as a prepared statement parameter.
- `.fetch().intoMaps()` is a short chain; for typed POJOs use `.fetchInto(Product.class)` (jOOQ maps column names to fields by convention).
- `dsl.execute("INSERT …", name, price)` uses positional `?` placeholders — also parameterised and safe.

## 7. Gotchas & takeaways

> jOOQ's free open-source edition supports only `H2`, `HSQLDB`, `Derby`, `SQLite`, and a few others. **PostgreSQL, MySQL, Oracle, SQL Server require the commercial edition.** For open-source production use, the generated-code API still works but without some advanced dialect features.

> Plain string SQL in jOOQ (`dsl.fetch("...")`) looks like raw JDBC but jOOQ still routes it through its `Connection` pool handling and `ExecuteListener` chain — logging, transaction participation, and metrics work automatically.

- The jOOQ code generator is configured via `pom.xml` plugin or Gradle task; it connects to a DB (or uses Flyway migration files) and writes Java classes to `target/generated-sources/`.
- `JooqExceptionTranslator` (auto-configured) translates jOOQ's `DataAccessException` into Spring's `DataAccessException` hierarchy — consistent with JPA and JdbcTemplate error handling.
- `@Transactional` works: jOOQ's `DSLContext` participates in Spring-managed transactions automatically.
- Combining jOOQ for complex queries with Spring Data JPA for simple CRUD is a common and recommended pattern.
- jOOQ supports reactive execution via `DSLContext.reactive()` (requires R2DBC driver) — fully compatible with WebFlux.
