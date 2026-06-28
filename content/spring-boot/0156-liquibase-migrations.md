---
card: spring-boot
gi: 156
slug: liquibase-migrations
title: Liquibase migrations
---

## 1. What it is

**Liquibase** is a database schema migration tool that tracks and applies changes through a **changelog** — a structured file (XML, YAML, JSON, or SQL) containing ordered *changesets*. Spring Boot auto-configures Liquibase when `liquibase-core` is on the classpath, running the changelog at startup against the configured `DataSource`. Unlike plain SQL scripts, Liquibase changesets are database-agnostic: the same changelog can generate correct DDL for PostgreSQL, MySQL, and H2.

## 2. Why & when

Liquibase and Flyway solve the same problem (versioned schema migrations). Key differences that favour Liquibase:

- **Format flexibility** — YAML, XML, JSON, or SQL changelogs vs. SQL-only for Flyway.
- **Database portability** — Liquibase generates dialect-specific DDL from abstract operations (`createTable`, `addColumn`).
- **Rollback support** — changesets can define `rollback` blocks; Liquibase can reverse them.
- **Preconditions** — skip a changeset if a table already exists; useful when migrating existing databases.

Use Liquibase when portability across databases matters, or your team prefers a structured XML/YAML format over raw SQL.

## 3. Core concept

A **changelog** is a file that lists **changesets**. Each changeset has an `id` and `author`; together they form a unique key. Liquibase records applied changesets in `DATABASECHANGELOG` and never re-runs them.

```yaml
# db/changelog/db.changelog-master.yaml
databaseChangeLog:
  - changeSet:
      id: 1
      author: alice
      changes:
        - createTable:
            tableName: customer
            columns:
              - column: { name: id, type: BIGINT, autoIncrement: true, constraints: { primaryKey: true } }
              - column: { name: email, type: VARCHAR(200), constraints: { nullable: false } }
  - changeSet:
      id: 2
      author: alice
      changes:
        - addColumn:
            tableName: customer
            columns:
              - column: { name: created_at, type: TIMESTAMP, defaultValueComputed: CURRENT_TIMESTAMP }
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">App startup</text>
  <text x="90" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Liquibase runs</text>
  <rect x="235" y="55" width="185" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">DATABASECHANGELOG</text>
  <text x="327" y="96" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">id:1 alice — applied</text>
  <rect x="235" y="125" width="185" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="327" y="147" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">changeset id:2</text>
  <text x="327" y="164" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">addColumn → applied now</text>
  <rect x="490" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <text x="575" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">schema up to date</text>
  <line x1="162" y1="110" x2="231" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lq)"/>
  <line x1="162" y1="110" x2="231" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#lq)"/>
  <line x1="422" y1="152" x2="486" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#lq2)"/>
  <defs>
    <marker id="lq" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="lq2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Liquibase checks `DATABASECHANGELOG`, finds changeset id:2 unapplied, executes `addColumn`, records the result; database is now current.

## 5. Runnable example

```java
// LiquibaseApp.java — Spring Boot project
// pom.xml: spring-boot-starter-data-jpa, org.liquibase:liquibase-core, com.h2database:h2 (runtime)
// application.properties:
//   spring.jpa.hibernate.ddl-auto=validate
//   spring.liquibase.change-log=classpath:db/changelog/db.changelog-master.yaml
//
// src/main/resources/db/changelog/db.changelog-master.yaml:
//   databaseChangeLog:
//     - changeSet:
//         id: 1
//         author: dev
//         changes:
//           - createTable:
//               tableName: product
//               columns:
//                 - column:
//                     name: id
//                     type: BIGINT
//                     autoIncrement: true
//                     constraints:
//                       primaryKey: true
//                 - column:
//                     name: name
//                     type: VARCHAR(100)
//                     constraints:
//                       nullable: false
//                 - column:
//                     name: price
//                     type: DOUBLE
//     - changeSet:
//         id: 2
//         author: dev
//         changes:
//           - insert:
//               tableName: product
//               columns:
//                 - column: { name: name, value: Widget }
//                 - column: { name: price, valueNumeric: 9.99 }

import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@SpringBootApplication
public class LiquibaseApp {
    public static void main(String[] args) {
        SpringApplication.run(LiquibaseApp.class, args);
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
1. Create `src/main/resources/db/changelog/db.changelog-master.yaml` with the YAML shown in comments.
2. Add `liquibase-core` to `pom.xml`.
3. Start the app — Liquibase applies changesets 1 and 2.
4. `curl http://localhost:8080/products` → `[{"id":1,"name":"Widget","price":9.99}]`

## 6. Walkthrough

- `org.liquibase:liquibase-core` triggers `LiquibaseAutoConfiguration`. It creates a `SpringLiquibase` bean that calls `liquibase.update()` at startup.
- `spring.liquibase.change-log` points at the master changelog. The master file can include other files with `- include: { file: … }` for modular changelog organisation.
- Changeset `id:1 author:dev` creates the `product` table with `createTable`. The abstract operation generates correct DDL for whatever database dialect is in use — the same YAML works against H2 in tests and PostgreSQL in production.
- Changeset `id:2` inserts a seed row using Liquibase's abstract `insert` operation.
- `spring.jpa.hibernate.ddl-auto=validate` makes Hibernate verify that the JPA entity `Product` matches the table Liquibase created, but does not generate DDL itself.
- On the second startup, both changesets are in `DATABASECHANGELOG` — Liquibase skips them. Any new changeset added to the YAML runs on the next deploy.

## 7. Gotchas & takeaways

> **Never change a changeset that has been applied.** Liquibase stores a checksum; a modified changeset causes `ValidationFailedException`. Fix: always add new changesets; never edit committed ones.

> Changeset `id` + `author` must be **globally unique** within a changelog. Duplicate identifiers cause Liquibase to throw at startup. Adopt a naming convention: `{ticket-number}` or `{YYYYMMdd-N}`.

- `spring.liquibase.enabled=false` disables Liquibase — useful in tests with `@DataJpaTest`.
- `spring.liquibase.contexts=dev,test` lets you tag changesets with contexts; only changesets matching the active context run.
- SQL-format changesets (`--changeset author:id`) are an alternative to YAML if you prefer raw SQL with Liquibase tracking.
- `liquibase:rollback` Maven goal or `SpringLiquibase.setRollbackFile()` generates a rollback script if your changesets define `rollback` blocks.
- `spring.liquibase.drop-first=true` drops the entire database before migrating — useful for a clean dev environment, dangerous in production.
