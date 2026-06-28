---
card: spring-boot
gi: 150
slug: open-entitymanager-in-view
title: Open EntityManager in View
---

## 1. What it is

**Open EntityManager in View (OEMIV)** is a Spring MVC interceptor pattern that keeps the JPA `EntityManager` (Hibernate Session) open from the start of an HTTP request until the HTTP response is fully written — including the view rendering phase. Spring Boot enables it by default via `OpenEntityManagerInViewInterceptor`. It is controlled with `spring.jpa.open-in-view=true|false` (default: `true`).

## 2. Why & when

JPA lazy loading works only inside an active persistence context. Without OEMIV, the `EntityManager` closes after the service method returns — any attempt to access a lazily-loaded collection in a view template (Thymeleaf, Freemarker) throws `LazyInitializationException`.

OEMIV fixes this by extending the EntityManager's lifetime to cover view rendering. But it has a cost: database connections may be held open while view templates render, reducing pool throughput under load.

**When to disable it (`spring.jpa.open-in-view=false`):**

- You prefer explicit fetch strategies (eager loading or `JOIN FETCH` in JPQL).
- Your architecture is REST/JSON — no view rendering, so lazy loading in the view is impossible anyway.
- You want to catch `LazyInitializationException` early rather than masking it.

## 3. Core concept

`OpenEntityManagerInViewInterceptor` wraps every HTTP request in an `EntityManager` lifecycle:

```
HTTP request arrives
  ↓ preHandle: EntityManager bound to thread
  ↓ Controller → Service → Repository (JPA calls here)
  ↓ afterCompletion: EntityManager closed
  ↑ Response written (view or JSON)
```

Without OEMIV, the EntityManager closes after the service layer. Any `@OneToMany` list accessed in the view template would require a new session — which doesn't exist, hence the exception.

With OEMIV, the same session is available in the view. But the connection may be held in the Hikari pool during slow template rendering — a hidden scalability cost.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="40" width="620" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="62" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">EntityManager open (OEMIV = true)</text>
  <rect x="20" y="100" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="127" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Controller</text>
  <rect x="175" y="100" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="127" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Service</text>
  <rect x="330" y="100" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="395" y="127" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Repository</text>
  <rect x="485" y="100" width="155" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="562" y="120" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">View render</text>
  <text x="562" y="137" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">(lazy OK)</text>
  <line x1="152" y1="122" x2="172" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#oe)"/>
  <line x1="307" y1="122" x2="327" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#oe)"/>
  <line x1="462" y1="122" x2="482" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#oe)"/>
  <rect x="20" y="165" width="620" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="184" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">EntityManager closed — DB connection returned to pool</text>
  <defs>
    <marker id="oe" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

With OEMIV enabled, the EntityManager spans the entire request including view rendering; it closes (and releases the connection) only after the response is committed.

## 5. Runnable example

```java
// OemivApp.java — Spring Boot project showing both behaviors
// pom.xml: spring-boot-starter-data-jpa, spring-boot-starter-web, com.h2database:h2 (runtime)
// application.properties:
//   spring.jpa.hibernate.ddl-auto=create-drop
//   spring.jpa.open-in-view=false   ← recommended for REST APIs
//   spring.jpa.show-sql=true

import jakarta.persistence.*;
import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@SpringBootApplication
public class OemivApp {
    public static void main(String[] args) {
        SpringApplication.run(OemivApp.class, args);
    }

    @Bean
    CommandLineRunner seed(AuthorRepository repo) {
        return args -> {
            Author a = new Author("Joshua Bloch");
            a.getBooks().add("Effective Java");
            a.getBooks().add("Java Puzzlers");
            repo.save(a);
        };
    }
}

@Entity
class Author {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;

    @ElementCollection(fetch = FetchType.LAZY)   // lazy by default
    private List<String> books = new java.util.ArrayList<>();

    protected Author() {}
    Author(String name) { this.name = name; }
    public Long getId() { return id; }
    public String getName() { return name; }
    public List<String> getBooks() { return books; }
}

interface AuthorRepository extends JpaRepository<Author, Long> {}

@RestController
class AuthorController {

    private final AuthorRepository repo;
    AuthorController(AuthorRepository repo) { this.repo = repo; }

    // Safe: load books eagerly inside the transaction
    @GetMapping("/authors/{id}")
    @Transactional(readOnly = true)
    public String author(@PathVariable Long id) {
        Author a = repo.findById(id).orElseThrow();
        // Accessing books HERE (inside @Transactional) is safe regardless of OEMIV
        return a.getName() + " wrote: " + a.getBooks();
    }
}
```

**How to run:** set `spring.jpa.open-in-view=false`, start the app, then `curl http://localhost:8080/authors/1` → `Joshua Bloch wrote: [Effective Java, Java Puzzlers]`. The `@Transactional` on the controller method keeps the persistence context open during `getBooks()`.

## 6. Walkthrough

- `spring.jpa.open-in-view=false` disables `OpenEntityManagerInViewInterceptor`. The EntityManager closes when the `@Transactional` method exits.
- `@ElementCollection(fetch = FetchType.LAZY)` makes `books` lazy. Without `@Transactional` on the controller, accessing `a.getBooks()` after the service call would throw `LazyInitializationException`.
- `@Transactional(readOnly = true)` on the controller method opens a persistence context for the duration of the method — books can be safely loaded because the EntityManager is still active.
- With `spring.jpa.open-in-view=true` (default), the interceptor would keep the EntityManager open even after the transaction ends — lazily loaded collections work, but the database connection stays borrowed until the JSON serializer finishes writing the response.
- Spring Boot logs a warning at startup when OEMIV is enabled: `"spring.jpa.open-in-view is enabled by default. Therefore, database queries may be performed during view rendering."` — treat this as a reminder to review your fetch strategy.

## 7. Gotchas & takeaways

> With `open-in-view=true`, a slow JSON serialiser or template engine can hold a Hikari connection for the entire render duration. Under high concurrency this exhausts the pool. **Disable OEMIV and use `@Transactional` + eager fetching or `JOIN FETCH` instead.**

> Disabling OEMIV reveals latent `LazyInitializationException` bugs — consider this a feature, not a problem. It forces you to be intentional about what data is loaded.

- Spring Boot 2.x defaults to `open-in-view=true` and logs a startup warning. Spring Boot 3.x preserves this default but the warning is still present.
- For REST APIs returning JSON there is no view rendering phase — OEMIV provides no benefit and only costs connection hold time.
- `@Transactional(readOnly = true)` on query methods gives Hibernate optimisation hints (no dirty checking) and informs the transaction manager to use a read replica.
- `FetchType.EAGER` avoids lazy loading entirely but can cause Cartesian product explosions with multiple `@OneToMany` collections — profile before using.
