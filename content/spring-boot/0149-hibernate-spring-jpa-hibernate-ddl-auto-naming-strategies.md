---
card: spring-boot
gi: 149
slug: hibernate-spring-jpa-hibernate-ddl-auto-naming-strategies
title: Hibernate (spring.jpa.hibernate.ddl-auto, naming strategies)
---

## 1. What it is

**Hibernate** is the default JPA provider in Spring Boot. Beyond the JPA spec, Spring Boot exposes Hibernate-specific configuration through `spring.jpa.hibernate.*` properties. The two most commonly tuned settings are:

- **`ddl-auto`** — controls whether Hibernate creates, updates, or validates the database schema from your entity classes.
- **Naming strategies** — control how Java field names (`firstName`) are translated to SQL column names (`first_name`). Spring Boot sets an opinionated default that applies Snake Case naming.

## 2. Why & when

`ddl-auto` lets Hibernate own schema changes during early development (no migration scripts needed), while `validate` or `none` keeps Hibernate out of the way when you use Flyway or Liquibase in production. Understanding naming strategies prevents silent mismatches between your Java model and the database column names your DBA created.

Tune these settings when:

- Moving from dev (H2 + `create-drop`) to production (external DB + `none` or `validate`).
- Your database columns use naming conventions that don't match Hibernate's defaults.
- You're taking over schema management with a migration tool and want Hibernate to stay hands-off.

## 3. Core concept

**`spring.jpa.hibernate.ddl-auto` values:**

| Value | Effect |
|---|---|
| `none` | Hibernate does nothing to the schema |
| `validate` | Checks entity ↔ table match; fails if mismatched |
| `update` | Alters tables to match entities (additive only — never drops columns) |
| `create` | Drops and recreates schema on every startup |
| `create-drop` | Like `create` but also drops on shutdown |

Spring Boot defaults: `create-drop` for embedded DBs; `none` for all others.

**Naming strategies:** Spring Boot configures two layers:

1. `SpringPhysicalNamingStrategy` — converts camelCase to snake_case at the physical level: `firstName` → `first_name`.
2. `SpringImplicitNamingStrategy` — determines names for join tables and foreign key columns when not explicitly specified.

Override with `spring.jpa.hibernate.naming.physical-strategy` and `spring.jpa.hibernate.naming.implicit-strategy`.

## 4. Diagram

<svg viewBox="0 0 680 215" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">@Entity class</text>
  <text x="95" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">firstName (Java)</text>
  <rect x="250" y="55" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">SpringPhysical</text>
  <text x="340" y="96" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">NamingStrategy</text>
  <rect x="250" y="125" width="180" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="145" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">ddl-auto</text>
  <text x="340" y="162" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">none/validate/update/create</text>
  <rect x="505" y="80" width="155" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="582" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">first_name (SQL)</text>
  <text x="582" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">table structure</text>
  <line x1="172" y1="110" x2="246" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hs)"/>
  <line x1="172" y1="110" x2="246" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#hs)"/>
  <line x1="432" y1="82" x2="501" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#hs2)"/>
  <line x1="432" y1="148" x2="501" y2="122" stroke="#8b949e" stroke-width="1.5" marker-end="url(#hs3)"/>
  <defs>
    <marker id="hs" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="hs2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="hs3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`SpringPhysicalNamingStrategy` converts `firstName` → `first_name`; `ddl-auto` controls whether Hibernate creates or just validates the matching table.

## 5. Runnable example

```java
// HibernateConfigApp.java — Spring Boot project
// pom.xml: spring-boot-starter-data-jpa, com.h2database:h2 (runtime)
// application.properties:
//   spring.jpa.hibernate.ddl-auto=create-drop
//   spring.jpa.show-sql=true
//   spring.jpa.properties.hibernate.format_sql=true
//   # Default naming is already snake_case via SpringPhysicalNamingStrategy
//   # Uncomment to switch to Hibernate's default (preserves camelCase):
//   # spring.jpa.hibernate.naming.physical-strategy=org.hibernate.boot.model.naming.PhysicalNamingStrategyStandardImpl

import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class HibernateConfigApp {
    public static void main(String[] args) {
        SpringApplication.run(HibernateConfigApp.class, args);
    }

    @Bean
    CommandLineRunner demo(PersonRepository repo) {
        return args -> {
            repo.save(new Person("Alice", "Smith"));
            repo.save(new Person("Bob", "Jones"));

            System.out.println("=== All persons ===");
            repo.findAll().forEach(p ->
                System.out.printf("id=%d  first_name=%s  last_name=%s%n",
                    p.getId(), p.getFirstName(), p.getLastName()));

            System.out.println("=== Smith family ===");
            repo.findByLastName("Smith")
                .forEach(p -> System.out.println(p.getFirstName()));
        };
    }
}

@Entity
class Person {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String firstName;   // → column: first_name (SpringPhysicalNamingStrategy)
    private String lastName;    // → column: last_name

    protected Person() {}
    Person(String firstName, String lastName) {
        this.firstName = firstName;
        this.lastName = lastName;
    }
    public Long getId() { return id; }
    public String getFirstName() { return firstName; }
    public String getLastName() { return lastName; }
}

interface PersonRepository extends JpaRepository<Person, Long> {
    List<Person> findByLastName(String lastName);
}
```

**How to run:** add `spring-boot-starter-data-jpa` and H2 to `pom.xml`, apply properties above, then `./mvnw spring-boot:run`. The console shows the formatted SQL Hibernate generates, including the snake_case column names.

## 6. Walkthrough

- `spring.jpa.hibernate.ddl-auto=create-drop` causes Hibernate to execute `CREATE TABLE person (id BIGINT AUTO_INCREMENT, first_name VARCHAR(255), last_name VARCHAR(255), PRIMARY KEY (id))` at startup and `DROP TABLE person` at shutdown.
- `spring.jpa.show-sql=true` prints every SQL statement. `hibernate.format_sql=true` pretty-prints them across multiple lines — makes complex JOINs readable.
- `firstName` in Java → `first_name` in SQL via `SpringPhysicalNamingStrategy`. Hibernate's own default `PhysicalNamingStrategyStandardImpl` would leave it as `firstName` — which fails on case-insensitive databases and is not idiomatic SQL.
- `CommandLineRunner` runs after the context starts — useful for demo data without needing a running server. `repo.save(new Person(...))` persists the entity inside a Hibernate transaction.
- `repo.findByLastName("Smith")` generates `SELECT * FROM person WHERE last_name = ?` — the naming strategy translates `lastName` to `last_name` automatically in the generated query.
- To use `validate` in production: set `spring.jpa.hibernate.ddl-auto=validate` and let Flyway or Liquibase manage schema changes. Hibernate compares entity metadata against live table metadata and throws `SchemaManagementException` on mismatch.

## 7. Gotchas & takeaways

> **Never use `ddl-auto=update` in production.** It adds columns but never removes them — schema drift accumulates silently, and it can lock tables on large databases during `ALTER TABLE`. Use Flyway or Liquibase for production schema changes.

> Spring Boot's `SpringPhysicalNamingStrategy` is applied *after* the logical naming strategy. If you add `@Column(name = "...")` on a field, the physical strategy is **not** applied to that explicit name — it's taken as-is.

- `spring.jpa.hibernate.ddl-auto` values are case-sensitive.
- `spring.jpa.properties.hibernate.*` passes arbitrary Hibernate properties not covered by Spring Boot's typed bindings.
- `spring.jpa.defer-datasource-initialization=true` ensures `schema.sql` runs after Hibernate creates tables — necessary when `data.sql` references JPA-created tables.
- In tests, `@DataJpaTest` sets `ddl-auto=create-drop` automatically, giving each test class a clean schema.
- Hibernate 6 (Spring Boot 3.x) changed some default SQL generation details — check generated SQL when upgrading from Hibernate 5.
