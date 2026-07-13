---
card: microservices
gi: 426
slug: data-layer-tests-datajpatest-etc
title: "Data layer tests (@DataJpaTest, etc.)"
---

## 1. What it is

`@DataJpaTest` is a Spring Boot test slice (see [@SpringBootTest slices & full-context tests](0424-springboottest-slices-full-context-tests.md)) that boots **only the persistence layer** — `@Entity` classes, Spring Data repositories, the `EntityManager`, and a `DataSource` — while excluding controllers, services, and most other application beans. Related slices exist for other persistence technologies: `@DataMongoTest` for MongoDB, `@DataRedisTest` for Redis, `@JdbcTest` for plain JDBC. Each one narrows the context to exactly the beans needed to exercise queries, mappings, and constraints against a real (or embedded) database, without paying to construct the rest of the application. By default `@DataJpaTest` wraps each test in a transaction that's rolled back afterward, so tests never leave data behind for the next test to trip over.

## 2. Why & when

You reach for a data-layer slice specifically to test the parts of your persistence code that a plain unit test, with a hand-rolled fake repository, cannot verify at all:

- **Query correctness is invisible to a fake.** A hand-written fake `Map`-backed repository always "finds" whatever you put into it; it can't tell you whether your real `@Query("SELECT o FROM Order o WHERE o.status = :status AND o.createdAt < :cutoff")` actually returns the right rows, has a typo, or silently returns nothing because of a mismatched parameter name.
- **Entity mapping bugs only surface against a real schema.** A missing `@Column` mapping, a wrong `@JoinColumn`, or an entity that doesn't match its migration script all pass a fake-repository unit test trivially and fail (sometimes silently, with wrong data) against a real database.
- **Constraint violations need a real database to enforce.** A unique-index violation, a foreign-key constraint, or a NOT NULL check only fires when a real (or embedded) database engine evaluates the insert — a fake never enforces any of that.
- **It's still fast**, because `@DataJpaTest` by default swaps in an embedded, in-memory database (like H2) unless you explicitly configure a real one — though see [Testcontainers integration](0428-testcontainers-integration-for-real-db-broker-in-tests.md) for why an embedded database is often the wrong trade-off in production-grade suites.

You reach for `@DataJpaTest` (or the sibling slices) specifically to verify repository queries, entity mappings, and database constraints — the layer directly touching persistence — leaving business logic to unit tests and full request/response behavior to [web layer tests](0425-web-layer-tests-webmvctest-webfluxtest.md).

## 3. Core concept

Picture a librarian's cataloging system being tested separately from the front desk. You don't need a patron at the counter to verify that a call number correctly retrieves the right shelf location, that two books can't be assigned the same barcode, or that a search by author actually returns every book by that author — you need the real card catalog (or its digital equivalent) running, with real rules enforced, but nothing else about the library needs to be operating. `@DataJpaTest` is that isolated cataloging rehearsal: real entities, real repository queries, a real (if substitute) database enforcing real constraints — no controllers, no services, no HTTP involved at all.

Concretely, a data-layer slice test has four ingredients:

1. **`@DataJpaTest`** (or `@DataMongoTest`, `@JdbcTest`, etc.) — scopes the context to `@Entity` classes, Spring Data repository interfaces, and the minimal infrastructure needed to run them against a database.
2. **A database** — by default an embedded, in-memory substitute (H2, for JPA); can be reconfigured to run against a real containerized database via `@AutoConfigureTestDatabase(replace = Replace.NONE)` combined with [Testcontainers](0428-testcontainers-integration-for-real-db-broker-in-tests.md), which is the more production-representative choice.
3. **`TestEntityManager`** — an autowired helper for setting up test data directly (bypassing the repository under test) and flushing changes to the database so queries actually hit real, persisted rows rather than an in-memory first-level cache.
4. **Automatic transaction rollback** — each test method runs inside a transaction that's rolled back when the test finishes, so tests don't need to manually clean up rows and can't leak state into the next test.

```java
@DataJpaTest
class OrderRepositoryTest {
    @Autowired TestEntityManager entityManager;
    @Autowired OrderRepository orderRepository;

    @Test
    void findsOrdersByStatusExcludingOthers() {
        entityManager.persist(new Order("order-1", "SHIPPED"));
        entityManager.persist(new Order("order-2", "PENDING"));
        entityManager.flush();

        List<Order> shipped = orderRepository.findByStatus("SHIPPED");
        assertThat(shipped).hasSize(1).extracting(Order::getId).containsExactly("order-1");
    }
}
```

`entityManager.persist` and `flush` insert real rows into the (embedded) database; `orderRepository.findByStatus` then runs the *real* Spring Data query against those rows, proving the query itself is correct, not just that a fake would agree with itself.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A DataJpaTest slice loads entities, repositories, and a test database, wrapped in a transaction that rolls back after each test, leaving no data behind for the next test">
  <rect x="30" y="40" width="150" height="140" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="105" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@DataJpaTest</text>
  <rect x="45" y="80" width="120" height="28" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="98" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Entity classes</text>
  <rect x="45" y="115" width="120" height="28" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="133" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Repositories</text>
  <rect x="45" y="150" width="120" height="20" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="105" y="164" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no controllers/services</text>

  <line x1="180" y1="110" x2="250" y2="110" stroke="#79c0ff" stroke-width="2"/>

  <rect x="250" y="70" width="150" height="80" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="325" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Test database</text>
  <text x="325" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">embedded (H2) or</text>
  <text x="325" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Testcontainers-backed</text>

  <rect x="440" y="70" width="170" height="80" rx="10" fill="#1c2430" stroke="#f85149" stroke-dasharray="4,2"/>
  <text x="525" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">transaction per test</text>
  <text x="525" y="113" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rolled back automatically</text>
  <text x="525" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">after each test method</text>

  <line x1="400" y1="110" x2="440" y2="110" stroke="#f85149" stroke-width="2" stroke-dasharray="3,2"/>

  <text x="320" y="200" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">real queries run against a real database, but no test leaves data behind</text>
</svg>

Entities and repositories are real and run real queries against a real database, wrapped in a per-test transaction that rolls back so tests stay isolated.

## 5. Runnable example

Scenario: an `OrderRepository` with a status-filtering query and a uniqueness constraint on order id. We model the essential persistence behavior in plain Java first, then show the real `@DataJpaTest` shape, then handle a production-flavored constraint-violation case.

### Level 1 — Basic

```java
// File: OrderRepositoryLogicBasic.java -- the CORE query behavior, in
// plain Java with an in-memory list standing in for a real table, before
// wiring anything into Spring or a real database.
import java.util.*;
import java.util.stream.*;

public class OrderRepositoryLogicBasic {
    record Order(String id, String status) {}

    static class InMemoryOrderTable {
        final List<Order> rows = new ArrayList<>();
        void insert(Order o) { rows.add(o); }
        List<Order> findByStatus(String status) {
            return rows.stream().filter(o -> o.status().equals(status)).collect(Collectors.toList());
        }
    }

    public static void main(String[] args) {
        InMemoryOrderTable table = new InMemoryOrderTable();
        table.insert(new Order("order-1", "SHIPPED"));
        table.insert(new Order("order-2", "PENDING"));
        table.insert(new Order("order-3", "SHIPPED"));

        List<Order> shipped = table.findByStatus("SHIPPED");
        System.out.println("Shipped orders: " + shipped.stream().map(Order::id).collect(Collectors.toList()));
    }
}
```

How to run: `java OrderRepositoryLogicBasic.java`

This mirrors the *intent* of `orderRepository.findByStatus("SHIPPED")` with a plain in-memory list — useful for reasoning about what the query should return, but it proves nothing about whether a real `@Query` annotation, a real column mapping, or a real database engine would actually behave this way. That's exactly the gap `@DataJpaTest` closes.

### Level 2 — Intermediate

```java
// File: OrderRepositorySpringShapeIntermediate.java -- the SAME query, now
// in its REAL Spring Data JPA form using @DataJpaTest, TestEntityManager,
// and a real (embedded) database -- as it would really be written and run
// under Maven/Gradle with spring-boot-starter-data-jpa and H2 on the classpath.
import jakarta.persistence.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

public class OrderRepositorySpringShapeIntermediate {

    @Entity
    static class Order {
        @Id String id;
        String status;
        protected Order() {}
        Order(String id, String status) { this.id = id; this.status = status; }
        String getId() { return id; }
        String getStatus() { return status; }
    }

    interface OrderRepository extends JpaRepository<Order, String> {
        List<Order> findByStatus(String status);
    }

    @DataJpaTest
    static class OrderRepositoryTest {
        @Autowired TestEntityManager entityManager;
        @Autowired OrderRepository orderRepository;

        @Test
        void findsOrdersByStatusExcludingOthers() {
            entityManager.persist(new Order("order-1", "SHIPPED"));
            entityManager.persist(new Order("order-2", "PENDING"));
            entityManager.persist(new Order("order-3", "SHIPPED"));
            entityManager.flush();

            List<Order> shipped = orderRepository.findByStatus("SHIPPED");

            assertThat(shipped).hasSize(2);
            assertThat(shipped).extracting(Order::getId).containsExactlyInAnyOrder("order-1", "order-3");
        }
    }
}
```

How to run: this file requires `spring-boot-starter-data-jpa`, an embedded database driver (e.g. H2), and JUnit 5 on the classpath; run it as a JUnit 5 test via `mvn test` or your IDE's test runner, not with plain `java`.

`entityManager.persist` and `flush` write real rows to the embedded database via a real `EntityManager` — no faking involved. `orderRepository.findByStatus` then runs the query Spring Data generates from the method name (`findBy` + `Status`) against those actual persisted rows, proving both the entity mapping and the derived query are correct together, which a hand-rolled fake could never verify.

### Level 3 — Advanced

```java
// File: OrderRepositoryConstraintAdvanced.java -- the SAME repository, now
// handling a PRODUCTION-FLAVORED hard case: a UNIQUE constraint violation
// that only a real database engine can enforce, verified with @DataJpaTest
// so the actual constraint (not an assumption about it) is exercised.
import jakarta.persistence.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.boot.test.autoconfigure.orm.jpa.TestEntityManager;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.data.jpa.repository.JpaRepository;

import static org.assertj.core.api.Assertions.assertThatThrownBy;

public class OrderRepositoryConstraintAdvanced {

    @Entity
    @Table(name = "orders", uniqueConstraints = @UniqueConstraint(columnNames = "orderNumber"))
    static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY) Long id;
        @Column(nullable = false, unique = true) String orderNumber;
        String status;
        protected Order() {}
        Order(String orderNumber, String status) { this.orderNumber = orderNumber; this.status = status; }
    }

    interface OrderRepository extends JpaRepository<Order, Long> {}

    @DataJpaTest
    static class OrderRepositoryConstraintTest {
        @Autowired TestEntityManager entityManager;
        @Autowired OrderRepository orderRepository;

        @Test
        void rejectsDuplicateOrderNumberAtTheDatabaseLevel() {
            entityManager.persistAndFlush(new Order("ON-1001", "PENDING"));

            // A second order re-using the SAME orderNumber -- application code
            // might forget to check this itself, but the DATABASE constraint
            // must still catch it. This is precisely what a fake repository,
            // which just appends to a list, would silently allow through.
            Order duplicate = new Order("ON-1001", "PENDING");

            assertThatThrownBy(() -> entityManager.persistAndFlush(duplicate))
                    .isInstanceOf(jakarta.persistence.PersistenceException.class);
        }

        @Test
        void allowsDistinctOrderNumbers() {
            entityManager.persistAndFlush(new Order("ON-2001", "PENDING"));
            entityManager.persistAndFlush(new Order("ON-2002", "PENDING"));
            // No exception -- distinct orderNumbers are perfectly fine.
            assertThat(orderRepository.findAll()).hasSize(2);
        }

        private static <T> org.assertj.core.api.ListAssert<T> assertThat(java.util.List<T> list) {
            return org.assertj.core.api.Assertions.assertThat(list);
        }
    }
}
```

How to run: requires the same Spring Boot Data JPA test dependencies as Level 2; run as a JUnit 5 test via `mvn test` or your IDE.

The hard case here only exists because a real database engine enforces `unique = true` on the `orderNumber` column — attempting to `persistAndFlush` a second `Order` with the same `orderNumber` throws a `PersistenceException` (wrapping the database's unique-constraint violation) at flush time, not before. A hand-rolled fake repository backed by a `List` would happily accept both rows, silently hiding a defect that would only surface in production when the real database rejects the duplicate insert — exactly the class of bug `@DataJpaTest` exists to catch early.

## 6. Walkthrough

Trace `rejectsDuplicateOrderNumberAtTheDatabaseLevel` in order. **First**, the `@DataJpaTest`-scoped context boots (or reuses a cached one) with the `Order` entity, `OrderRepository`, and an embedded database configured from the entity's schema, including the `unique = true` constraint on `orderNumber`.

**Next**, `entityManager.persistAndFlush(new Order("ON-1001", "PENDING"))` runs. `persist` stages the entity, and `flush` forces Hibernate to immediately issue the real `INSERT` statement against the embedded database — this succeeds because no row with `orderNumber = "ON-1001"` exists yet.

**Then**, a second `Order` is constructed with the identical `orderNumber`, `"ON-1001"`. Calling `entityManager.persistAndFlush(duplicate)` forces another real `INSERT`. The database engine evaluates the unique constraint on the `orderNumber` column at insert time and rejects the row, because a row with that value already exists.

**Finally**, that rejection propagates up through Hibernate as a constraint-violation error, which JPA wraps in a `jakarta.persistence.PersistenceException`. `assertThatThrownBy` catches exactly this exception type, and the test passes — confirming the *database itself*, not application code, is what stopped the duplicate.

```
persistAndFlush(Order[orderNumber=ON-1001]) -> INSERT succeeds (first row)
persistAndFlush(Order[orderNumber=ON-1001]) -> INSERT rejected: unique constraint violation on 'orderNumber'
  -> wrapped as jakarta.persistence.PersistenceException

Test result: rejectsDuplicateOrderNumberAtTheDatabaseLevel PASSED
  assertThatThrownBy(...).isInstanceOf(PersistenceException.class) -- OK
```

## 7. Gotchas & takeaways

> `@DataJpaTest`'s default embedded database (H2) doesn't always enforce constraints, dialect quirks, or query behavior identically to your real production database (PostgreSQL, MySQL, and so on) — a query that works against H2 can fail, or a constraint that H2 enforces loosely can behave differently, against the real engine. For anything beyond simple mapping and constraint checks, prefer running the same slice against a real, containerized database with [Testcontainers](0428-testcontainers-integration-for-real-db-broker-in-tests.md) instead of trusting the embedded substitute.

- `@DataJpaTest` (and its siblings `@DataMongoTest`, `@JdbcTest`, `@DataRedisTest`) load only persistence-layer beans, giving fast, focused tests that a hand-rolled fake repository structurally cannot replicate — query correctness and constraint enforcement need a real engine.
- Each test method runs in a transaction that's automatically rolled back, so tests never need manual cleanup and can't leak state to the next test — but this also means autocommit-dependent behavior won't be exercised unless you explicitly disable that default.
- Use `TestEntityManager` to set up test data directly, bypassing the repository under test, so you're never testing a method using data inserted by that same method.
- Pair data-layer tests with [web layer tests](0425-web-layer-tests-webmvctest-webfluxtest.md) to cover both ends of the stack cheaply, and reserve full [`@SpringBootTest`](0424-springboottest-slices-full-context-tests.md) for verifying the layers actually wire together end-to-end.
- See [Testcontainers integration](0428-testcontainers-integration-for-real-db-broker-in-tests.md) for replacing the embedded database with a real, production-matching one when embedded-database quirks become a real risk.
