---
card: spring-data
gi: 26
slug: dynamic-projections
title: "Dynamic projections"
---

## 1. What it is

A dynamic projection is a repository method whose result *type* is a generic type parameter, resolved not at compile time but at each call site via a trailing `Class<T>` argument — the previous card's final example used one briefly; this card goes deeper into how the mechanism actually works, including combining it with `@Query`, and the constraints Spring Data places on what `T` can legitimately be.

```java
interface CustomerRepository extends Repository<Customer, Long> {
    <T> Optional<T> findByEmail(String email, Class<T> type);
}

Optional<Customer> full = repo.findByEmail("ada@example.com", Customer.class);
Optional<CustomerSummary> summary = repo.findByEmail("ada@example.com", CustomerSummary.class);
```

## 2. Why & when

Without dynamic projections, supporting both "give me the full entity" and "give me a summary view" for the same underlying query would require two separate repository methods with different names but identical filtering logic — real duplication for what's conceptually one query with two possible output shapes. Dynamic projections collapse that into one method, letting the *caller* decide the shape per call, while the repository author writes the filtering logic exactly once.

Reach for dynamic projections specifically when:

- The same filter/query logic legitimately needs to serve more than one output shape across different call sites in your codebase — a full-detail admin view and a lightweight public API response, both filtered the same way.
- You're building a generic, reusable search or lookup utility method that different callers should be able to adapt to their own DTO/view needs, without you needing to anticipate every possible projection shape in advance.
- You want to avoid maintaining near-duplicate repository methods that differ only in return type, keeping the actual query-filtering logic defined exactly once.

## 3. Core concept

```
 <T> Optional<T> findByEmail(String email, Class<T> type);
        |
        v
 Spring Data recognizes:
   - "email" is a regular filter parameter, matched against the entity property
   - "type" (a Class<T> parameter) is the SPECIAL dynamic-projection marker,
     NOT matched against any entity property -- it selects the RESULT SHAPE

 At CALL TIME (not proxy-generation time), Spring Data inspects the actual
 Class<T> argument passed:
   Customer.class          --> return the full managed entity
   CustomerSummary.class   --> return an interface projection proxy
   CustomerDto.class       --> return a class-based DTO (if a matching
                                constructor/mapping strategy is resolvable)

 Works with BOTH derived-query methods AND @Query-annotated methods --
 the dynamic Class<T> parameter mechanism is independent of how the
 underlying query itself is determined.
```

The `Class<T>` parameter's position (trailing, after regular filter parameters) and type are what Spring Data uses to recognize it as a dynamic-projection marker, exactly the same way it recognizes `Sort`/`Pageable`/`Limit` by type in an earlier card.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One repository method resolves to different return shapes at each call site based on the Class argument passed">
  <rect x="180" y="20" width="280" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">findByEmail(email, type)</text>

  <rect x="10" y="110" width="270" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="137" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">type=Customer.class -&gt; full entity</text>

  <rect x="360" y="110" width="270" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="137" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">type=CustomerSummary.class -&gt; projection</text>

  <line x1="270" y1="65" x2="150" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="370" y1="65" x2="490" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Identical filtering logic, resolved to two different result shapes purely by which `Class` was passed.

## 5. Runnable example

The scenario: an order-lookup repository, evolving from a basic dynamic projection on a derived query, to combining dynamic projection with `@Query`, to a realistic service layer exposing both shapes to different callers through the same underlying repository method.

### Level 1 — Basic

Declare a dynamic-projection derived-query method and call it with two different `Class` arguments.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class DynamicProjectionLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private double total;
        protected Order() {}
        public Order(String status, double total) { this.status = status; this.total = total; }
        public String getStatus() { return status; }
        public double getTotal() { return total; }
    }

    public interface OrderSummary {
        double getTotal();
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        <T> List<T> findByStatus(String status, Class<T> type);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DynamicProjectionLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:dynproj1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("shipped", 150.0));
        repo.save(new Order("shipped", 75.0));
        repo.save(new Order("pending", 20.0));

        List<Order> fullOrders = repo.findByStatus("shipped", Order.class);
        List<OrderSummary> summaries = repo.findByStatus("shipped", OrderSummary.class);

        System.out.println("full orders: " + fullOrders.size() + " (has status: " + fullOrders.get(0).getStatus() + ")");
        System.out.println("summaries: " + summaries.size() + " (total only: " + summaries.get(0).getTotal() + ")");

        if (fullOrders.size() != 2 || summaries.size() != 2) throw new AssertionError("Expected 2 shipped orders in both shapes");
        System.out.println("Same method, two different Class<T> arguments, two different result shapes -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java DynamicProjectionLevel1.java` on JDK 17+.

`<T> List<T> findByStatus(String status, Class<T> type)` filters by `status` (a normal derived condition) exactly once, in exactly one method — calling it with `Order.class` returns full entities, calling it with `OrderSummary.class` returns projections exposing only `getTotal()`, all from the identical underlying filter logic.

### Level 2 — Intermediate

Combine dynamic projection with an explicit `@Query`, showing the mechanism works independently of whether the query itself is derived or declared.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

@SpringBootApplication
public class DynamicProjectionLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private double total;
        protected Order() {}
        public Order(String status, double total) { this.status = status; this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderSummary {
        double getTotal();
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        @Query("select o from Order o where o.status = :status and o.total > :minTotal")
        <T> List<T> findLargeOrders(@Param("status") String status, @Param("minTotal") double minTotal, Class<T> type);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DynamicProjectionLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:dynproj2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("shipped", 150.0));
        repo.save(new Order("shipped", 30.0));
        repo.save(new Order("pending", 200.0));

        List<Order> fullResults = repo.findLargeOrders("shipped", 50.0, Order.class);
        List<OrderSummary> summaryResults = repo.findLargeOrders("shipped", 50.0, OrderSummary.class);

        System.out.println("full: " + fullResults.size() + ", summary: " + summaryResults.size());

        if (fullResults.size() != 1 || summaryResults.size() != 1)
            throw new AssertionError("Expected exactly 1 large shipped order in both shapes");
        System.out.println("Dynamic projection worked with an explicit @Query too -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java DynamicProjectionLevel2.java`.

`@Query`'s JPQL string handles the filtering (`status` and `minTotal`), while the trailing `Class<T> type` parameter, exactly as in Level 1, independently controls the result shape — the two mechanisms (explicit query, dynamic projection) compose without any special interaction needed between them.

### Level 3 — Advanced

Build a small service layer exposing two differently-typed public methods, both backed internally by a single dynamic-projection repository method — the realistic shape of using dynamic projections to avoid duplicating query logic across a service's public API.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Optional;

@SpringBootApplication
public class DynamicProjectionLevel3 {

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        private String fullName;
        private String internalNotes; // NOT exposed via the public-facing projection
        protected Customer() {}
        public Customer(String email, String fullName, String internalNotes) {
            this.email = email; this.fullName = fullName; this.internalNotes = internalNotes;
        }
        public String getEmail() { return email; }
        public String getFullName() { return fullName; }
        public String getInternalNotes() { return internalNotes; }
    }

    public interface PublicCustomerView {
        String getEmail();
        String getFullName();
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        <T> Optional<T> findByEmail(String email, Class<T> type);
    }

    // Service layer: exposes two DIFFERENT public methods, both backed by ONE repository method.
    @Component
    public static class CustomerService {
        private final CustomerRepository repo;
        public CustomerService(CustomerRepository repo) { this.repo = repo; }

        // For internal/admin callers: full entity, including internal notes.
        public Optional<Customer> getFullCustomerForAdmin(String email) {
            return repo.findByEmail(email, Customer.class);
        }

        // For public API callers: narrowed view, no internal notes exposed at all.
        public Optional<PublicCustomerView> getPublicView(String email) {
            return repo.findByEmail(email, PublicCustomerView.class);
        }
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(DynamicProjectionLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:dynproj3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("ada@example.com", "Ada Lovelace", "VIP -- handle personally"));

        CustomerService service = ctx.getBean(CustomerService.class);

        Optional<Customer> adminView = service.getFullCustomerForAdmin("ada@example.com");
        Optional<PublicCustomerView> publicView = service.getPublicView("ada@example.com");

        System.out.println("admin sees internal notes: " + adminView.map(Customer::getInternalNotes).orElse(null));
        System.out.println("public view exposes: " + publicView.map(v -> v.getEmail() + "/" + v.getFullName()).orElse(null));

        if (adminView.isEmpty() || adminView.get().getInternalNotes() == null)
            throw new AssertionError("Expected the admin view to include internal notes");
        if (publicView.isEmpty()) throw new AssertionError("Expected the public view to find the customer too");

        System.out.println("One repository method backed two differently-scoped service methods -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java DynamicProjectionLevel3.java`.

`CustomerService` exposes `getFullCustomerForAdmin` and `getPublicView` as two distinct, independently-typed public methods — but both delegate to the exact same `repo.findByEmail(email, Class<T>)`, only varying the `Class` argument. `PublicCustomerView` has no `getInternalNotes()` at all, so code holding only a `PublicCustomerView` reference has no way to access that data — the API-level narrowing is enforced by the Java type system itself, exactly as the earlier repository-abstraction card demonstrated for read-only repositories.

## 6. Walkthrough

Trace `service.getPublicView("ada@example.com")`.

1. **`CustomerService.getPublicView(...)`** calls `repo.findByEmail("ada@example.com", PublicCustomerView.class)`.
2. **Inside the repository proxy**: the derived query part (`findByEmail` matching the `email` property) executes against the database exactly as it would for any single-result derived query, retrieving the matching `Customer` row.
3. **Dynamic projection resolution**: because a `Class<T>` argument was supplied and it's `PublicCustomerView.class` (an interface projection type, not the managed `Customer` entity type itself), Spring Data wraps the loaded `Customer` row in a generated proxy implementing `PublicCustomerView`, exposing only `getEmail()` and `getFullName()`.
4. **Return value**: `Optional<PublicCustomerView>`, populated with that proxy.
5. **Back in `CustomerService`**: `getPublicView` returns this `Optional<PublicCustomerView>` to its caller — nothing about `internalNotes` is present anywhere in this returned value, not because it was filtered out after the fact, but because `PublicCustomerView` never declared a getter for it in the first place.
6. **Separately, `getFullCustomerForAdmin(...)`** goes through the identical repository method, but passing `Customer.class` instead — this time Spring Data recognizes the requested type *is* the managed entity type, and returns the fully-loaded `Customer` object directly, including `internalNotes`.
7. **Verification**: the program confirms the admin path can read `internalNotes` while the public path's return type structurally cannot expose it, demonstrating the dynamic projection mechanism enforcing two different, legitimate view shapes from one underlying repository method.

```
 CustomerRepository.findByEmail(email, Class<T> type)
        |
        +-- type = Customer.class            --> full entity, includes internalNotes
        |
        +-- type = PublicCustomerView.class  --> proxy, NO internalNotes getter exists at all
        |
        v
 CustomerService exposes BOTH shapes as separate, independently-typed public methods,
 backed by this ONE repository method underneath
```

## 7. Gotchas & takeaways

> **Gotcha:** because dynamic projection resolution happens per call, based on a runtime `Class<T>` value, there's no compile-time guarantee that a given call site passes a type Spring Data can actually handle for that query — passing an arbitrary, unrelated class (one that isn't the managed entity type and doesn't look like a valid interface or DTO projection) typically fails at call time with a mapping error, not at compile time. Keep the set of types passed to a dynamic-projection method's `Class<T>` parameter limited to ones you've deliberately designed as valid projections (or the entity type itself).

- Dynamic projections let one repository method serve multiple return shapes, resolved per call site via a trailing `Class<T>` parameter — avoiding duplicate methods that differ only in return type.
- The mechanism works identically whether the underlying query is derived from the method name or declared explicitly via `@Query` — dynamic projection and query-source resolution are independent, composable features.
- A common, valuable pattern is exposing multiple differently-scoped public service methods, all backed by a single dynamic-projection repository method underneath — keeping the actual data-access/filtering logic defined exactly once.
- Because the `Class<T>` argument is resolved at runtime, dynamic projections trade some compile-time safety for flexibility — validate that any type passed is a class or interface Spring Data can genuinely map the query's results onto.
