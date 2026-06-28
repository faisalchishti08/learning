---
card: spring-boot
gi: 147
slug: jpa-spring-data-jpa-auto-config
title: JPA & Spring Data JPA auto-config
---

## 1. What it is

**JPA (Jakarta Persistence API)** is the standard Java specification for object-relational mapping — annotating Java classes to represent database tables and querying them through an `EntityManager`. **Spring Data JPA** builds on JPA, eliminating repetitive repository code: you declare an interface extending `JpaRepository<T, ID>` and Spring generates the implementation. Spring Boot auto-configures Hibernate (the default JPA provider), an `EntityManagerFactory`, `JpaTransactionManager`, and Spring Data repository scanning when `spring-boot-starter-data-jpa` is on the classpath.

## 2. Why & when

Raw JDBC is powerful but verbose: SQL strings everywhere, manual `ResultSet` mapping, no object graph traversal. JPA maps tables to objects so you can work with Java types directly; Spring Data JPA reduces repository code to interface declarations.

Use Spring Data JPA when:

- Entities have straightforward CRUD operations — repositories handle them for free.
- You want type-safe derived queries from method names (`findByEmailAndActive`).
- Domain model relationships (one-to-many, many-to-many) are central to your design.

Consider plain `JdbcTemplate` / `JdbcClient` for complex reporting queries, bulk operations, or when you want explicit SQL.

## 3. Core concept

Auto-configuration chain:

```
spring-boot-starter-data-jpa
  → HibernateJpaAutoConfiguration
      → EntityManagerFactory (wraps Hibernate SessionFactory)
      → JpaTransactionManager
  → JpaRepositoriesAutoConfiguration
      → @EnableJpaRepositories (scans for JpaRepository interfaces)
      → Generates runtime implementations
```

You declare entities (`@Entity`, `@Id`) and repositories (`interface FooRepository extends JpaRepository<Foo, Long>`). Spring Data JPA generates SQL at startup by inspecting method names: `findByName(String name)` → `SELECT * FROM foo WHERE name = ?`.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your Service</text>
  <text x="90" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">calls repository</text>
  <rect x="235" y="60" width="170" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="82" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">JpaRepository</text>
  <text x="320" y="99" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">generated impl</text>
  <rect x="235" y="130" width="170" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="152" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">EntityManager</text>
  <text x="320" y="169" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(Hibernate)</text>
  <rect x="480" y="80" width="175" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <text x="567" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">via HikariCP</text>
  <line x1="162" y1="110" x2="231" y2="87" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jpa)"/>
  <line x1="320" y1="112" x2="320" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jpa2)"/>
  <line x1="407" y1="155" x2="476" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#jpa3)"/>
  <defs>
    <marker id="jpa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jpa2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jpa3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Service calls the generated `JpaRepository` impl → delegates to `EntityManager` (Hibernate) → executes SQL via HikariCP.

## 5. Runnable example

```java
// JpaApp.java — Spring Boot project
// pom.xml: spring-boot-starter-data-jpa, com.h2database:h2 (runtime)
// application.properties:
//   spring.jpa.hibernate.ddl-auto=create-drop
//   spring.jpa.show-sql=true

import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@SpringBootApplication
public class JpaApp {
    public static void main(String[] args) {
        SpringApplication.run(JpaApp.class, args);
    }
}

@Entity
@Table(name = "book")
class Book {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String title;
    private String author;

    protected Book() {}
    Book(String title, String author) { this.title = title; this.author = author; }

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public String getAuthor() { return author; }
}

// No implementation needed — Spring Data generates it
interface BookRepository extends JpaRepository<Book, Long> {
    List<Book> findByAuthor(String author);            // derived query
    List<Book> findByTitleContainingIgnoreCase(String keyword);
}

@RestController
@RequestMapping("/books")
class BookController {

    private final BookRepository repo;

    BookController(BookRepository repo) { this.repo = repo; }

    @GetMapping
    public List<Book> all() { return repo.findAll(); }

    @GetMapping("/author/{name}")
    public List<Book> byAuthor(@PathVariable String name) {
        return repo.findByAuthor(name);
    }

    @PostMapping
    public Book create(@RequestParam String title, @RequestParam String author) {
        return repo.save(new Book(title, author));
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) { repo.deleteById(id); }
}
```

**How to run:** add `spring-boot-starter-data-jpa` and H2 to `pom.xml`, set properties, start the app, then:
- `curl -X POST "http://localhost:8080/books?title=Effective+Java&author=Bloch"`
- `curl http://localhost:8080/books`
- `curl http://localhost:8080/books/author/Bloch`

## 6. Walkthrough

- `spring-boot-starter-data-jpa` triggers `HibernateJpaAutoConfiguration`. It creates an `EntityManagerFactory` (Hibernate `SessionFactory`) pointing at the auto-configured `DataSource`, then wraps it in a `JpaTransactionManager`.
- `spring.jpa.hibernate.ddl-auto=create-drop` instructs Hibernate to create tables from `@Entity` classes at startup and drop them at shutdown — suitable for demos/tests. Use `validate` in production.
- `@Entity` marks `Book` as a JPA entity. `@GeneratedValue(strategy = GenerationType.IDENTITY)` delegates ID generation to the database (auto-increment).
- `BookRepository extends JpaRepository<Book, Long>` gives free implementations of `findAll()`, `findById()`, `save()`, `deleteById()`, and more.
- `findByAuthor(String author)` is a **derived query** — Spring Data JPA parses the method name and generates `SELECT b FROM Book b WHERE b.author = ?1`. No SQL written.
- `spring.jpa.show-sql=true` prints generated SQL to the console — invaluable during development to catch N+1 queries and missing indexes.

## 7. Gotchas & takeaways

> **N+1 select problem**: fetching a `List<Order>` where each `Order` has a `@OneToMany List<Item>` causes 1 query for orders + N queries for items. Fix with `@EntityGraph`, `JOIN FETCH` JPQL, or `@BatchSize`.

> `spring.jpa.hibernate.ddl-auto=create-drop` **deletes your data** on every restart. Never use it in production. Use `validate` (fails fast on schema mismatch) or Flyway/Liquibase for migrations.

- `@Transactional` on service methods is essential — without it, lazy loading outside the persistence context throws `LazyInitializationException`.
- `JpaRepository.save(entity)` performs `persist` for new entities and `merge` for detached ones — check the entity's `@Id` field to understand which path runs.
- `spring.jpa.open-in-view=false` (recommended) disables the OpenEntityManager-in-View interceptor — see the dedicated tutorial for details.
- Spring Data's `@Query("SELECT b FROM Book b WHERE ...")` lets you write explicit JPQL or native SQL when derived queries are insufficient.
