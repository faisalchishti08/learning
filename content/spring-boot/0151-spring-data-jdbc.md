---
card: spring-boot
gi: 151
slug: spring-data-jdbc
title: Spring Data JDBC
---

## 1. What it is

**Spring Data JDBC** is a persistence framework that sits between raw `JdbcTemplate` and full JPA. It maps Java objects to tables and provides `CrudRepository`/`ListCrudRepository` interfaces with generated implementations — but without Hibernate, the JPA EntityManager, lazy loading, a first-level cache, or dirty tracking. Every database operation is explicit. Spring Boot auto-configures Spring Data JDBC when `spring-boot-starter-data-jdbc` is on the classpath.

## 2. Why & when

JPA (Hibernate) is powerful but brings hidden complexity: lazy loading, dirty tracking, first-level cache, proxy objects, `LazyInitializationException`, N+1 queries. Spring Data JDBC deliberately drops all of that in favour of simplicity:

- **No lazy loading** — you decide exactly what to load.
- **No dirty tracking** — a `save()` always issues an `UPDATE`; nothing is tracked automatically.
- **Aggregate-oriented** — models Domain-Driven Design aggregates cleanly.

Use Spring Data JDBC when:

- You want repository-style access without Hibernate's complexity.
- Your domain model maps to a DDD aggregate (root + children owned by root).
- You write custom SQL for complex queries anyway and just want simple CRUD abstraction.

## 3. Core concept

Spring Data JDBC uses the **aggregate root** model: a root entity owns its children. When you save a root, children are saved too. When you delete a root, children are deleted. No bidirectional relationships — children don't hold a reference back to the root.

Mapping rules:

- Class → table (name derived by `NamingStrategy`).
- Field → column (snake_case via default strategy).
- `@Id` → primary key.
- `List<Child>` embedded in root → child table with a foreign key back to the root.

`@Query` annotations let you write custom SQL, and `JdbcTemplate` is always available for anything outside the aggregate model.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="145" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="92" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Aggregate Root</text>
  <text x="92" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Order + items</text>
  <rect x="240" y="60" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="327" y="83" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">ListCrudRepository</text>
  <text x="327" y="99" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">save / findById / delete</text>
  <rect x="240" y="130" width="175" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="327" y="155" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">JdbcTemplate</text>
  <rect x="490" y="80" width="165" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="572" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <text x="572" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">explicit SQL</text>
  <line x1="167" y1="110" x2="236" y2="87" stroke="#6db33f" stroke-width="1.5" marker-end="url(#sj)"/>
  <line x1="417" y1="88" x2="486" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#sj2)"/>
  <line x1="417" y1="152" x2="486" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#sj3)"/>
  <defs>
    <marker id="sj" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="sj2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="sj3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Aggregate root passed to `ListCrudRepository`; Spring Data JDBC issues explicit SQL; `JdbcTemplate` available for custom queries.

## 5. Runnable example

```java
// SpringDataJdbcApp.java — Spring Boot project
// pom.xml: spring-boot-starter-data-jdbc, com.h2database:h2 (runtime)
// schema.sql:
//   CREATE TABLE purchase_order (id BIGINT AUTO_INCREMENT PRIMARY KEY, customer VARCHAR(100));
//   CREATE TABLE order_item (purchase_order INT NOT NULL, name VARCHAR(100), quantity INT);

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.data.annotation.Id;
import org.springframework.data.relational.core.mapping.MappedCollection;
import org.springframework.data.relational.core.mapping.Table;
import org.springframework.data.repository.ListCrudRepository;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

@SpringBootApplication
public class SpringDataJdbcApp {
    public static void main(String[] args) {
        SpringApplication.run(SpringDataJdbcApp.class, args);
    }

    @Bean
    CommandLineRunner demo(OrderRepository repo) {
        return args -> {
            PurchaseOrder order = new PurchaseOrder("Alice");
            order.items().add(new OrderItem("Widget", 3));
            order.items().add(new OrderItem("Gadget", 1));
            PurchaseOrder saved = repo.save(order);
            System.out.println("Saved order id=" + saved.id());
            System.out.println("All orders: " + repo.findAll());
        };
    }
}

@Table("purchase_order")
record PurchaseOrder(
    @Id Long id,
    String customer,
    @MappedCollection(idColumn = "purchase_order")
    List<OrderItem> items
) {
    PurchaseOrder(String customer) {
        this(null, customer, new ArrayList<>());
    }
}

record OrderItem(String name, int quantity) {}

interface OrderRepository extends ListCrudRepository<PurchaseOrder, Long> {
    List<PurchaseOrder> findByCustomer(String customer);
}
```

**How to run:** add `spring-boot-starter-data-jdbc` and H2, create the `schema.sql` shown in comments, start the app. The `CommandLineRunner` saves an order with items and prints the result.

## 6. Walkthrough

- `spring-boot-starter-data-jdbc` triggers `JdbcRepositoriesAutoConfiguration`. It creates a `JdbcMappingContext`, a `DataAccessStrategy`, and generates implementations for all `ListCrudRepository` interfaces found during scan.
- `@Table("purchase_order")` maps the aggregate root record to the `purchase_order` table. Without the annotation, Spring Data JDBC uses the class name converted to snake_case.
- `@Id Long id` marks the primary key. Spring Data JDBC sets it from the database's generated value after `INSERT`.
- `@MappedCollection(idColumn = "purchase_order")` tells Spring Data JDBC that `OrderItem` rows are owned by this root and have a `purchase_order` foreign-key column referencing the root's `id`.
- `repo.save(order)` issues `INSERT INTO purchase_order` followed by `INSERT INTO order_item` for each item — all in one transaction. **There is no dirty tracking**: calling `save()` again always issues an `UPDATE` + `DELETE`/`INSERT` for the collection.
- `findByCustomer(String)` is a derived query, exactly like Spring Data JPA — Spring Data JDBC generates `SELECT * FROM purchase_order WHERE customer = ?`.

## 7. Gotchas & takeaways

> Spring Data JDBC **always** deletes and re-inserts child rows when saving an aggregate root with a `List` collection. For large collections this is expensive. Consider explicit SQL via `@Query` or `JdbcTemplate` for bulk-update scenarios.

> There is **no lazy loading**. Calling `repo.findById(id)` loads the entire aggregate including all child collections eagerly. Design aggregates to be small and self-contained.

- Spring Data JDBC uses `@Id` from `org.springframework.data.annotation`, not JPA's `jakarta.persistence.Id` — they are not interchangeable.
- The schema must be created separately — Spring Data JDBC does not generate DDL. Use `schema.sql` or a migration tool.
- `@Query("SELECT * FROM purchase_order WHERE …")` writes plain SQL (not JPQL) — the result is mapped to the aggregate root record automatically.
- `@Transactional` on service methods works the same as with JPA — Spring's `JdbcTransactionManager` manages the transaction.
- Spring Data JDBC integrates with Spring Data's `Pageable`, `Sort`, and `Page` abstractions — pass `Pageable` to `findAll()` for pagination.
