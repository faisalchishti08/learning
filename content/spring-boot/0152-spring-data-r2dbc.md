---
card: spring-boot
gi: 152
slug: spring-data-r2dbc
title: Spring Data R2DBC
---

## 1. What it is

**R2DBC (Reactive Relational Database Connectivity)** is a non-blocking database driver specification — the reactive counterpart of JDBC. **Spring Data R2DBC** provides repository support (`R2dbcRepository`) and a `DatabaseClient` on top of R2DBC drivers, enabling fully reactive database access without blocking a thread. Spring Boot auto-configures the `ConnectionFactory`, `DatabaseClient`, and repository scanning when `spring-boot-starter-data-r2dbc` is on the classpath alongside an R2DBC driver.

## 2. Why & when

JDBC blocks the calling thread while the database responds. In a Spring WebFlux app with Reactor Netty, a JDBC call would block an event-loop thread and stall the entire server. R2DBC sends the query to the database and emits results through a `Flux<Row>` stream when they arrive — no thread blocked.

Use Spring Data R2DBC when:

- Your app is fully reactive (Spring WebFlux + Reactor Netty).
- You need maximum concurrent database connections with minimal thread overhead.
- You're building streaming APIs that process large result sets row by row.

Do not use R2DBC if your app is Spring MVC (Servlet-based) — in that context, JDBC with HikariCP is simpler and just as fast.

## 3. Core concept

R2DBC uses a `ConnectionFactory` (analogous to JDBC's `DataSource`) that produces reactive `Connection` objects. `DatabaseClient` is the low-level reactive SQL client. `R2dbcRepository<T, ID>` provides reactive CRUD methods returning `Mono<T>` and `Flux<T>`.

```
application.properties
  spring.r2dbc.url=r2dbc:h2:mem:///testdb
         ↓
ConnectionFactoryAutoConfiguration → ConnectionFactory
R2dbcRepositoriesAutoConfiguration → R2dbcRepository impls
         ↓
Mono / Flux<T> — non-blocking database results
```

Entities use `@Table` and `@Id` from Spring Data (same as Spring Data JDBC, not JPA).

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">WebFlux handler</text>
  <text x="90" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">returns Flux&lt;T&gt;</text>
  <rect x="235" y="60" width="175" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="322" y="84" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">R2dbcRepository</text>
  <text x="322" y="100" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Flux / Mono results</text>
  <rect x="235" y="130" width="175" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="322" y="152" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">ConnectionFactory</text>
  <text x="322" y="168" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">non-blocking</text>
  <rect x="485" y="80" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <text x="570" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">H2 / PostgreSQL</text>
  <line x1="162" y1="110" x2="231" y2="87" stroke="#6db33f" stroke-width="1.5" marker-end="url(#r2)"/>
  <line x1="412" y1="87" x2="481" y2="108" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#r22)"/>
  <line x1="412" y1="152" x2="481" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#r23)"/>
  <defs>
    <marker id="r2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="r22" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="r23" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

WebFlux handler calls `R2dbcRepository`; `ConnectionFactory` opens a non-blocking connection; results flow back as `Flux<T>`.

## 5. Runnable example

```java
// R2dbcApp.java — Spring Boot project with spring-boot-starter-webflux + R2DBC
// pom.xml: spring-boot-starter-webflux, spring-boot-starter-data-r2dbc,
//          io.r2dbc:r2dbc-h2
// application.properties:
//   spring.r2dbc.url=r2dbc:h2:mem:///testdb;DB_CLOSE_DELAY=-1
//   spring.sql.init.mode=always
// schema.sql:
//   CREATE TABLE IF NOT EXISTS product (id BIGINT AUTO_INCREMENT PRIMARY KEY,
//     name VARCHAR(100), price DOUBLE);

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.annotation.Id;
import org.springframework.data.r2dbc.repository.R2dbcRepository;
import org.springframework.data.relational.core.mapping.Table;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

@SpringBootApplication
public class R2dbcApp {
    public static void main(String[] args) {
        SpringApplication.run(R2dbcApp.class, args);
    }
}

@Table("product")
record Product(@Id Long id, String name, double price) {
    Product(String name, double price) { this(null, name, price); }
}

interface ProductRepository extends R2dbcRepository<Product, Long> {
    Flux<Product> findByPriceLessThan(double max);
}

@RestController
@RequestMapping("/products")
class ProductController {

    private final ProductRepository repo;

    ProductController(ProductRepository repo) { this.repo = repo; }

    @GetMapping
    public Flux<Product> all() { return repo.findAll(); }

    @GetMapping("/cheap")
    public Flux<Product> cheap(@RequestParam(defaultValue = "20") double max) {
        return repo.findByPriceLessThan(max);
    }

    @PostMapping
    public Mono<Product> create(@RequestBody Product p) {
        return repo.save(new Product(p.name(), p.price()));
    }

    @DeleteMapping("/{id}")
    public Mono<Void> delete(@PathVariable Long id) {
        return repo.deleteById(id);
    }
}
```

**How to run:**
1. Add dependencies to `pom.xml` (`spring-boot-starter-webflux`, `spring-boot-starter-data-r2dbc`, `io.r2dbc:r2dbc-h2`).
2. Create `schema.sql` as shown in comments.
3. Start the app.
4. `curl -X POST http://localhost:8080/products -H "Content-Type: application/json" -d '{"name":"Widget","price":9.99}'`
5. `curl http://localhost:8080/products`

## 6. Walkthrough

- `spring-boot-starter-data-r2dbc` triggers `R2dbcAutoConfiguration` which creates a `ConnectionFactory` from `spring.r2dbc.url`. H2's R2DBC driver provides an in-memory database.
- `spring.sql.init.mode=always` runs `schema.sql` against the R2DBC `ConnectionFactory` at startup — creates the `product` table without Hibernate DDL.
- `R2dbcRepository<Product, Long>` generates reactive CRUD implementations. `findAll()` returns `Flux<Product>` — each row is emitted as it arrives from the database, not all at once.
- `findByPriceLessThan(double max)` is a derived query: Spring Data R2DBC generates `SELECT * FROM product WHERE price < $1` (parameterised, safe from injection).
- `repo.save(new Product(p.name(), p.price()))` — `id` is `null` so R2DBC issues an `INSERT` and the database-generated ID is populated in the returned `Mono<Product>`.
- The entire request pipeline is non-blocking: the WebFlux event loop thread handles the HTTP request, submits the SQL to R2DBC (which uses async I/O to the database), and subscribes to results — no thread waits.

## 7. Gotchas & takeaways

> R2DBC has **no JPA / Hibernate**. There is no lazy loading, no first-level cache, no JPQL — you write SQL or use derived queries. Import `@Id` and `@Table` from `org.springframework.data.*`, not `jakarta.persistence.*`.

> `@Transactional` works in a reactive context via `TransactionalOperator` or Spring's reactive `@Transactional` support (Reactor context-based). Mixing blocking JDBC and reactive R2DBC in the same transaction is not supported.

- R2DBC drivers exist for PostgreSQL (`r2dbc-postgresql`), MySQL (`r2dbc-mysql`), H2 (`r2dbc-h2`), SQL Server, and MariaDB.
- `DatabaseClient` (auto-configured) provides low-level SQL execution: `.sql("SELECT …").fetch().all()` returns `Flux<Map<String,Object>>`.
- `@Query("SELECT * FROM product WHERE …")` supports native SQL in `R2dbcRepository` methods.
- Schema initialisation with R2DBC uses `spring.sql.init.mode` and `schema.sql` — Flyway and Liquibase also have R2DBC-compatible modes.
- `r2dbc-pool` (auto-configured) provides connection pooling for R2DBC, similar to HikariCP for JDBC.
