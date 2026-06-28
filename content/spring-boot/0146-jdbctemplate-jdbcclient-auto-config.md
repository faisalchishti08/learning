---
card: spring-boot
gi: 146
slug: jdbctemplate-jdbcclient-auto-config
title: JdbcTemplate / JdbcClient auto-config
---

## 1. What it is

`JdbcTemplate` is Spring's primary JDBC helper — it handles connection borrowing, statement creation, exception translation, and resource cleanup so your code only writes the SQL and maps the results. `JdbcClient` (Spring 6.1 / Spring Boot 3.2) is a newer, fluent-API wrapper around `JdbcTemplate` that chains query/update calls in a single expression. Spring Boot auto-configures both from the auto-configured `DataSource` — no `@Bean` declarations needed.

## 2. Why & when

Raw JDBC is verbose and error-prone: opening connections, handling `SQLException`, closing `ResultSet`, `Statement`, and `Connection` in every `finally` block. `JdbcTemplate` removes all that boilerplate. Use it when:

- You want to write SQL directly (more control than JPA).
- Your queries are complex, dynamic, or use database-specific features that JPA struggles with.
- You want lightweight data access without Hibernate's overhead.

`JdbcClient` (introduced in Spring 6.1) simplifies `JdbcTemplate` further with a fluent, readable API for the common case: `client.sql("SELECT …").query(…).list()`.

## 3. Core concept

`JdbcTemplate` wraps a `DataSource`. Every method:
1. Borrows a connection from the pool.
2. Creates a `PreparedStatement`.
3. Executes it.
4. Maps the `ResultSet` using a callback (`RowMapper<T>`).
5. Returns the connection to the pool.

`JdbcClient` wraps `JdbcTemplate` and provides a builder-style API:
```java
// JdbcTemplate style
List<Product> ps = jdbc.query("SELECT * FROM product WHERE price < ?",
    (rs, i) -> new Product(rs.getInt("id"), rs.getString("name")), 50.0);

// JdbcClient style (Spring 6.1+)
List<Product> ps = client.sql("SELECT * FROM product WHERE price < :max")
    .param("max", 50.0)
    .query(Product.class)   // maps to record/bean via column name
    .list();
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your Code</text>
  <rect x="235" y="55" width="165" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="317" y="79" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">JdbcClient (fluent)</text>
  <rect x="235" y="115" width="165" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="317" y="139" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">JdbcTemplate</text>
  <rect x="480" y="80" width="175" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="110" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">DataSource (pool)</text>
  <line x1="162" y1="100" x2="231" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jt)"/>
  <line x1="162" y1="110" x2="231" y2="135" stroke="#6db33f" stroke-width="1.5" marker-end="url(#jt)"/>
  <line x1="402" y1="95" x2="476" y2="103" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#jt2)"/>
  <line x1="402" y1="135" x2="476" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#jt3)"/>
  <defs>
    <marker id="jt" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="jt2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jt3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`JdbcClient` wraps `JdbcTemplate`; both delegate to the auto-configured `DataSource` pool for connections.

## 5. Runnable example

```java
// JdbcClientApp.java  —  Spring Boot 3.2+ project
// pom.xml: spring-boot-starter-jdbc, com.h2database:h2 (runtime)
// schema.sql: CREATE TABLE product (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100), price DOUBLE);
// data.sql:   INSERT INTO product (name, price) VALUES ('Widget', 9.99), ('Gadget', 24.99);

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@SpringBootApplication
public class JdbcClientApp {
    public static void main(String[] args) {
        SpringApplication.run(JdbcClientApp.class, args);
    }
}

record Product(int id, String name, double price) {}

@RestController
@RequestMapping("/products")
class ProductController {

    private final JdbcClient client;

    ProductController(JdbcClient client) { this.client = client; }

    @GetMapping
    public List<Product> all() {
        return client.sql("SELECT id, name, price FROM product ORDER BY id")
                     .query(Product.class)   // maps columns to record components by name
                     .list();
    }

    @GetMapping("/{id}")
    public Product byId(@PathVariable int id) {
        return client.sql("SELECT id, name, price FROM product WHERE id = :id")
                     .param("id", id)
                     .query(Product.class)
                     .single();             // throws if 0 or >1 rows
    }

    @PostMapping
    public String add(@RequestParam String name, @RequestParam double price) {
        int rows = client.sql("INSERT INTO product (name, price) VALUES (:name, :price)")
                         .param("name", name)
                         .param("price", price)
                         .update();
        return rows + " row(s) inserted";
    }

    @DeleteMapping("/{id}")
    public String delete(@PathVariable int id) {
        int rows = client.sql("DELETE FROM product WHERE id = :id")
                         .param("id", id)
                         .update();
        return rows + " row(s) deleted";
    }
}
```

**How to run:** create `schema.sql` and `data.sql` in `src/main/resources/`, start the app, then:
- `curl http://localhost:8080/products` → list
- `curl http://localhost:8080/products/1` → single product
- `curl -X POST "http://localhost:8080/products?name=Sprocket&price=4.99"`

## 6. Walkthrough

- `JdbcClientAutoConfiguration` creates a `JdbcClient` bean backed by the auto-configured `JdbcTemplate` (which itself uses the `DataSource`). No extra configuration needed.
- `client.sql("SELECT … FROM product ORDER BY id")` starts a fluent chain. `.query(Product.class)` tells `JdbcClient` to map each row to a `Product` record using column-name-to-field-name matching (case-insensitive). `.list()` executes and returns all rows.
- Named parameters (`:id`, `:name`) are set with `.param(name, value)`. Positional `?` parameters also work with `.params(value1, value2, ...)`.
- `.single()` asserts exactly one row — throws `IncorrectResultSizeDataAccessException` if the result is empty or has multiple rows. Use `.optional()` when absence is expected.
- `.update()` returns the number of rows affected — useful to verify that a `DELETE` or `UPDATE` found the target row.
- All Spring JDBC exceptions are unchecked `DataAccessException` subclasses — no `try/catch` boilerplate needed.

## 7. Gotchas & takeaways

> `JdbcClient.query(SomeClass.class)` uses `BeanPropertyRowMapper` or `DataClassRowMapper` — column names must match field/property names (with underscore-to-camelCase conversion). Mismatches silently produce `null` fields.

> Named parameters use `:name` syntax. **Do not mix** named and positional parameters in the same SQL string — the parser handles only one style per query.

- `JdbcTemplate.queryForObject` throws `EmptyResultDataAccessException` (not null) when no row is found. Catch it or use `JdbcClient.query().optional()` instead.
- `JdbcTemplate` is still available alongside `JdbcClient` — use it directly for batch operations, stored procedures, or `CallableStatement` which `JdbcClient` doesn't wrap.
- `NamedParameterJdbcTemplate` is the predecessor to `JdbcClient`'s named-parameter feature — `JdbcClient` is the modern replacement.
- For `@Transactional` support, annotate service methods — both `JdbcTemplate` and `JdbcClient` participate in Spring-managed transactions automatically.
