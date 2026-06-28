---
card: spring-boot
gi: 143
slug: embedded-database-support
title: Embedded database support
---

## 1. What it is

An **embedded database** runs inside the JVM process — no separate server to install, start, or configure. Spring Boot auto-configures H2, HSQLDB, or Derby when their JAR is on the classpath and no explicit `spring.datasource.url` is set. The database starts automatically at application startup, is populated from `schema.sql` and `data.sql` if present, and is destroyed when the JVM exits. It is ideal for development, testing, and demos.

## 2. Why & when

Spinning up a PostgreSQL instance just to run unit tests or show a demo wastes time and creates environment dependencies. Embedded databases eliminate both: tests run anywhere the JAR runs, with a fresh, predictable dataset every time.

Use embedded databases for:

- **Unit/integration tests** — isolated, repeatable, no network required.
- **Local development** — zero-setup data layer while the real DB is being designed.
- **Demos and tutorials** — self-contained runnable examples.

Never use them for production — data is volatile (lost on restart), they are not clustered, and H2's SQL dialect differs from PostgreSQL/MySQL in edge cases.

## 3. Core concept

`EmbeddedDatabaseAutoConfiguration` detects H2, HSQLDB, or Derby on the classpath and creates an `EmbeddedDatabase` bean (a `DataSource` wrapper) when no `spring.datasource.url` is configured. The URL, username, and password are assigned automatically (`jdbc:h2:mem:<uuid>`, `sa`, empty).

Spring Boot also runs `src/main/resources/schema.sql` (DDL) and `data.sql` (DML) against the embedded database at startup if those files exist. In tests, use `@Sql` for per-test SQL or `spring.sql.init.mode=always` to control initialisation.

H2's in-memory mode (`mem:`) is the most common choice — data exists only in RAM and is isolated per connection pool. H2 also supports a file-based mode (`jdbc:h2:file:/path/db`) for persistence across restarts.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Spring Boot starts</text>
  <rect x="245" y="60" width="185" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="337" y="84" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">H2 DataSource (in-memory)</text>
  <rect x="245" y="115" width="185" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="337" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">schema.sql + data.sql</text>
  <rect x="505" y="80" width="155" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="582" y="108" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">JVM exits → gone</text>
  <line x1="172" y1="105" x2="241" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#em)"/>
  <line x1="172" y1="105" x2="241" y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#em)"/>
  <line x1="432" y1="100" x2="501" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#em2)"/>
  <defs>
    <marker id="em" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="em2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Spring Boot creates an H2 in-memory DataSource on startup, runs SQL init scripts, and destroys the database when the JVM exits.

## 5. Runnable example

```java
// EmbeddedDbApp.java — Spring Boot project
// pom.xml: spring-boot-starter-jdbc, com.h2database:h2 (scope: runtime)
//
// src/main/resources/schema.sql:
//   CREATE TABLE product (id INT PRIMARY KEY, name VARCHAR(100), price DECIMAL(10,2));
//
// src/main/resources/data.sql:
//   INSERT INTO product VALUES (1, 'Widget', 9.99);
//   INSERT INTO product VALUES (2, 'Gadget', 24.99);

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.Map;

@SpringBootApplication
public class EmbeddedDbApp {
    public static void main(String[] args) {
        SpringApplication.run(EmbeddedDbApp.class, args);
    }
}

@RestController
class ProductController {

    private final JdbcTemplate jdbc;

    ProductController(JdbcTemplate jdbc) { this.jdbc = jdbc; }

    @GetMapping("/products")
    public List<Map<String, Object>> products() {
        return jdbc.queryForList("SELECT * FROM product ORDER BY id");
    }

    @GetMapping("/products/count")
    public String count() {
        Long n = jdbc.queryForObject("SELECT COUNT(*) FROM product", Long.class);
        return "Total products: " + n;
    }
}
```

**How to run:**
1. Add `spring-boot-starter-jdbc` and H2 (`com.h2database:h2`) to `pom.xml`.
2. Create `schema.sql` and `data.sql` in `src/main/resources/` as shown in comments.
3. Start the app with `./mvnw spring-boot:run`.
4. `curl http://localhost:8080/products` → JSON list of products from H2.
5. Restart: products reset to initial `data.sql` seed — no persistence.

## 6. Walkthrough

- No `spring.datasource.url` is set → `EmbeddedDatabaseAutoConfiguration` detects H2 on the classpath and creates a `HikariDataSource` pointing at `jdbc:h2:mem:<generated-name>`.
- Spring Boot's `DataSourceInitializerInvoker` runs `schema.sql` (DDL) first, then `data.sql` (DML) against the fresh in-memory database at startup. This is controlled by `spring.sql.init.mode` (default: `embedded` — only runs for embedded DBs).
- `JdbcTemplate` is auto-configured from the same `DataSource` and injected into `ProductController`.
- `jdbc.queryForList("SELECT * FROM product")` returns each row as a `Map<String, Object>` — convenient for dynamic column sets. Jackson serialises the list to JSON automatically.
- H2's console UI is available at `http://localhost:8080/h2-console` when `spring.h2.console.enabled=true` — useful for inspecting data interactively during development.
- In test classes, `@DataJdbcTest` or `@DataJpaTest` automatically configure an embedded database without starting the full application context.

## 7. Gotchas & takeaways

> H2's SQL dialect differs from PostgreSQL and MySQL in edge cases (`SERIAL`, `ILIKE`, array types). Tests passing against H2 may fail against the real DB. Use Testcontainers to run tests against the actual database engine.

> With Spring Boot 2.5+, `data.sql` runs before Hibernate initialises the schema when `spring.jpa.defer-datasource-initialization=true` is not set. Set it to `true` if you use JPA and `data.sql` inserts rows that depend on JPA-created tables.

- H2 in-memory databases are **per connection pool** — all threads share one in-memory DB because Hikari's connections share the same `mem:` URL.
- `spring.h2.console.enabled=true` (dev only) opens a web UI at `/h2-console`.
- Add `spring.datasource.url=jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1` to prevent H2 from dropping the DB when the last connection closes.
- Use `@Sql("/test-data.sql")` in tests to load per-test fixtures without coupling to `data.sql`.
- Switching from H2 to PostgreSQL in prod: add the driver, set `spring.datasource.url`, done — the rest of your code is unchanged.
