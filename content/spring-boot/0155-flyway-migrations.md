---
card: spring-boot
gi: 155
slug: flyway-migrations
title: Flyway migrations
---

## 1. What it is

**Flyway** is a database migration tool that applies versioned SQL scripts to a database in a defined, tracked order. Each script runs exactly once; Flyway records execution in a `flyway_schema_history` table. Spring Boot auto-configures Flyway when `flyway-core` (via `spring-boot-starter-data-jpa` or an explicit dependency) is on the classpath — migrations in `classpath:db/migration/` run automatically at startup before the application accepts traffic.

## 2. Why & when

`schema.sql` runs every restart and can't track which changes have already been applied. Flyway solves this with **versioned migrations**: each SQL file has a version number (`V1__`, `V2__`, …). Flyway checks the database's history table and runs only the scripts not yet applied. This is safe for production — tables are never dropped accidentally.

Use Flyway when:

- Your database persists between restarts (any production database).
- Multiple developers add schema changes independently.
- You need an audit trail of what was applied and when.
- You want automatic schema updates on deployment (no manual `ALTER TABLE` steps).

## 3. Core concept

Migration file naming convention:

```
V{version}__{description}.sql
 ↑            ↑
 Version num  Two underscores + description (no spaces; use underscores)

Examples:
  V1__create_users_table.sql
  V2__add_email_index.sql
  V3__add_orders_table.sql
```

Flyway reads every `V*.sql` file in `classpath:db/migration/`, compares with `flyway_schema_history`, and runs missing ones in version order. Files already applied are never re-run. Checksum validation detects edits to applied migrations and fails fast.

`R__*.sql` repeatable migrations (no version number) run every time their checksum changes — useful for views and stored procedures.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">App startup</text>
  <text x="90" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Flyway runs</text>
  <rect x="235" y="55" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">flyway_schema_history</text>
  <text x="325" y="96" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">V1, V2 already applied</text>
  <rect x="235" y="125" width="180" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="325" y="147" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">V3__add_orders.sql</text>
  <text x="325" y="164" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">→ applied now</text>
  <rect x="490" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <text x="575" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">schema up to date</text>
  <line x1="162" y1="110" x2="231" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fw)"/>
  <line x1="162" y1="110" x2="231" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#fw)"/>
  <line x1="417" y1="150" x2="486" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#fw2)"/>
  <defs>
    <marker id="fw" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fw2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Flyway checks the history table, identifies unapplied migrations (V3 here), applies them to the database, and records the result.

## 5. Runnable example

```java
// FlywayApp.java — Spring Boot project
// pom.xml: spring-boot-starter-data-jpa, org.flywaydb:flyway-core, com.h2database:h2 (runtime)
// application.properties:
//   spring.jpa.hibernate.ddl-auto=validate
//   spring.flyway.locations=classpath:db/migration
//
// src/main/resources/db/migration/V1__create_product.sql:
//   CREATE TABLE product (
//     id    BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
//     name  VARCHAR(100) NOT NULL,
//     price DOUBLE NOT NULL
//   );
//
// src/main/resources/db/migration/V2__seed_products.sql:
//   INSERT INTO product (name, price) VALUES ('Widget', 9.99);
//   INSERT INTO product (name, price) VALUES ('Gadget', 24.99);

import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@SpringBootApplication
public class FlywayApp {
    public static void main(String[] args) {
        SpringApplication.run(FlywayApp.class, args);
    }
}

@Entity
class Product {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    private double price;
    protected Product() {}
    public Long getId() { return id; }
    public String getName() { return name; }
    public double getPrice() { return price; }
}

interface ProductRepo extends JpaRepository<Product, Long> {}

@RestController
class ProductController {
    private final ProductRepo repo;
    ProductController(ProductRepo repo) { this.repo = repo; }

    @GetMapping("/products")
    public List<Product> all() { return repo.findAll(); }
}
```

**How to run:**
1. Create migration files at `src/main/resources/db/migration/V1__create_product.sql` and `V2__seed_products.sql` with the SQL shown in comments.
2. Start the app — Flyway applies V1 then V2, then JPA validates the schema.
3. `curl http://localhost:8080/products` → the two seeded products.
4. Start again — Flyway sees V1 and V2 already applied and skips them.

## 6. Walkthrough

- `org.flywaydb:flyway-core` on the classpath triggers `FlywayAutoConfiguration`. It creates a `Flyway` bean, calls `flyway.migrate()` before the application context finishes starting, and blocks until all pending migrations complete.
- `spring.jpa.hibernate.ddl-auto=validate` tells Hibernate to check that entity definitions match the database schema (created by Flyway) but make no changes. This is the correct production combination.
- `spring.flyway.locations=classpath:db/migration` (this is the default) tells Flyway where to look. Point it at multiple locations for environment-specific scripts: `classpath:db/migration,classpath:db/migration-dev`.
- At startup, Flyway reads the `flyway_schema_history` table (creates it on first run), finds V1 and V2 not yet applied, executes them in order, and records success rows in the history table.
- On the second startup, both versions are in the history table — Flyway does nothing. Schema changes are cumulative and never destructive without an explicit `DROP`.
- Adding a new developer migration: create `V3__add_stock_column.sql` with `ALTER TABLE product ADD COLUMN stock INT DEFAULT 0`. Next deployment applies it automatically.

## 7. Gotchas & takeaways

> **Never edit a migration file after it has been applied.** Flyway stores a checksum; a modified applied file causes `FlywayException: Validate failed: Migration checksum mismatch`. Fix: if you need to alter applied SQL, create a new migration version.

> Flyway runs migrations in a **single thread at startup**. In multi-instance deployments, all instances try to migrate simultaneously. Flyway uses a database lock (`flyway_schema_history` lock row) so only one instance runs migrations — the others wait. Ensure your database allows this or use Flyway's baseline migration strategy.

- `spring.flyway.enabled=false` disables Flyway entirely — useful in tests that use `@DataJpaTest` with `ddl-auto=create-drop`.
- `spring.flyway.baseline-on-migrate=true` marks an existing database as already at a baseline version — use when adopting Flyway on a pre-existing schema.
- `spring.flyway.out-of-order=true` allows applying a lower-version migration found after a higher one has run — useful during parallel development on feature branches.
- Flyway Community supports H2, PostgreSQL, MySQL, MariaDB; Oracle and SQL Server require the Teams/Enterprise edition.
