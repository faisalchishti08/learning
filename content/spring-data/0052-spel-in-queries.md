---
card: spring-data
gi: 52
slug: spel-in-queries
title: "SpEL in queries"
---

## 1. What it is

Beyond plain named/positional parameter binding, `@Query` strings support Spring Expression Language (SpEL) expressions wrapped in `#{...}` — most commonly `#{#entityName}` (the entity's JPQL name, useful for queries in reusable base repositories that don't know their concrete entity type at compile time) and `#{#paramName}` (referencing a method parameter, or a property of one, directly within the expression, rather than just binding it as a plain value).

```java
@Query("select e from #{#entityName} e where e.active = true")
List<T> findAllActive(); // #{#entityName} resolves to whatever concrete entity this repository manages
```

## 2. Why & when

An earlier card's custom-base-repository example defined a shared, generic base interface (`AuditableRepository<T, ID>`) meant to be extended by multiple concrete repositories — but any `@Query` declared on that shared base interface can't hardcode a specific entity name (`Order`, `Product`), since the base interface doesn't know which concrete entity a given extending repository actually manages. `#{#entityName}` solves exactly this: it's resolved, per repository, to the correct concrete entity's JPQL name at query-parsing time, letting one `@Query` string on a shared base interface work correctly for every entity type that extends it.

Reach for SpEL in queries specifically when:

- You're writing a `@Query` on a generic, reusable base repository interface (the pattern from the earlier custom-base-interface card) and need the query to reference "whatever entity this specific repository manages" rather than a hardcoded entity name.
- You need to reference a method parameter's *property* directly within the query expression, rather than just its plain value — `#{#user.id}` instead of requiring the caller to extract and pass `user.getId()` separately.
- You want to avoid duplicating a nearly-identical `@Query` string across several repository interfaces that differ only in which entity they target.

## 3. Core concept

```
 #{#entityName}
   -- resolves to the JPQL entity name of whatever concrete entity type
      THIS SPECIFIC repository manages -- critical for @Query declared on
      a shared, generic base repository interface (from an earlier card)

   @NoRepositoryBean
   interface AuditableRepository<T, ID> extends JpaRepository<T, ID> {
       @Query("select t from #{#entityName} t where t.createdAt > :since")
       List<T> findRecentlyCreated(@Param("since") Instant since);
   }
   -- works correctly whether extended by OrderRepository (entityName="Order")
      or ProductRepository (entityName="Product"), with ZERO query duplication

 #{#paramName} / #{#paramName.property}
   -- references a method parameter (or one of its properties) directly
      inside the SpEL expression, evaluated BEFORE the query is executed

   @Query("select o from Order o where o.customerId = :#{#customer.id}")
   List<Order> findByCustomer(@Param("customer") Customer customer);
```

SpEL expressions in `@Query` are resolved once per query execution, substituting the computed value into the final JPQL/SQL before it's sent to the database.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="entityName SpEL resolves to the concrete entity type per repository, letting one query on a shared base interface work for multiple entities">
  <rect x="180" y="15" width="280" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">select t from #{#entityName} t ...</text>

  <rect x="20" y="100" width="230" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="135" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderRepository -&gt; "Order"</text>

  <rect x="390" y="100" width="230" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="505" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ProductRepository -&gt; "Product"</text>

  <line x1="280" y1="60" x2="150" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <line x1="360" y1="60" x2="490" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same query text resolves differently per repository, based on which entity it actually manages.

## 5. Runnable example

The scenario: a shared auditing base repository, evolving from a basic `#{#entityName}`-based query working for one entity, to confirming it works identically for a second, unrelated entity with zero query duplication, to referencing a parameter's property directly via SpEL.

### Level 1 — Basic

Declare a `#{#entityName}`-based query on a shared base repository, and confirm it resolves correctly for one concrete entity.

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
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;

@SpringBootApplication
public class SpelQueryLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private boolean active;
        protected Order() {}
        public Order(boolean active) { this.active = active; }
    }

    @NoRepositoryBean
    public interface AuditableRepository<T, ID> extends JpaRepository<T, ID> {
        @Query("select t from #{#entityName} t where t.active = true")
        List<T> findAllActive();
    }

    public interface OrderRepository extends AuditableRepository<Order, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpelQueryLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:spelquery1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(true));
        repo.save(new Order(false));

        List<Order> active = repo.findAllActive();
        System.out.println("active orders found via #{#entityName} query = " + active.size());

        if (active.size() != 1) throw new AssertionError("Expected exactly 1 active order");
        System.out.println("#{#entityName} resolved correctly to 'Order' on the generic base repository -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java SpelQueryLevel1.java` on JDK 17+.

`AuditableRepository<T, ID>`'s `@Query` never mentions `Order` by name — `#{#entityName}` resolves, at query-parsing time (when `OrderRepository`'s proxy is built), to `"Order"`, the JPQL entity name of the concrete type `OrderRepository` actually manages, producing the correct `select t from Order t where t.active = true`.

### Level 2 — Intermediate

Extend the same base repository with a second, unrelated entity, confirming the identical `@Query` string resolves correctly for both, with zero duplication.

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
import org.springframework.data.repository.NoRepositoryBean;

import java.util.List;

@SpringBootApplication
public class SpelQueryLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private boolean active;
        protected Order() {}
        public Order(boolean active) { this.active = active; }
    }

    @Entity
    public static class Product {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private boolean active;
        protected Product() {}
        public Product(boolean active) { this.active = active; }
    }

    @NoRepositoryBean
    public interface AuditableRepository<T, ID> extends JpaRepository<T, ID> {
        @Query("select t from #{#entityName} t where t.active = true")
        List<T> findAllActive();
    }

    public interface OrderRepository extends AuditableRepository<Order, Long> {}
    public interface ProductRepository extends AuditableRepository<Product, Long> {}

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpelQueryLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:spelquery2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository orderRepo = ctx.getBean(OrderRepository.class);
        ProductRepository productRepo = ctx.getBean(ProductRepository.class);

        orderRepo.save(new Order(true));
        orderRepo.save(new Order(false));
        productRepo.save(new Product(true));
        productRepo.save(new Product(true));
        productRepo.save(new Product(false));

        int activeOrders = orderRepo.findAllActive().size();
        int activeProducts = productRepo.findAllActive().size();

        System.out.println("active orders = " + activeOrders + ", active products = " + activeProducts);

        if (activeOrders != 1) throw new AssertionError("Expected 1 active order");
        if (activeProducts != 2) throw new AssertionError("Expected 2 active products");

        System.out.println("The SAME query string correctly resolved for TWO different entity types -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java SpelQueryLevel2.java`.

`OrderRepository` and `ProductRepository` both extend `AuditableRepository`, inheriting the identical `@Query("select t from #{#entityName} t where t.active = true")` — but each resolves `#{#entityName}` differently (`"Order"` versus `"Product"`), producing two genuinely different generated queries from one shared query string, with zero duplication.

### Level 3 — Advanced

Reference a method parameter's property directly via `#{#paramName.property}`, letting a query use a computed or nested value from a complex parameter without the caller needing to extract it manually first.

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
public class SpelQueryLevel3 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private Long customerId;
        private double total;
        protected Order() {}
        public Order(Long customerId, double total) { this.customerId = customerId; this.total = total; }
        public double getTotal() { return total; }
    }

    public record CustomerRef(Long id) {}

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // References customerRef.id() DIRECTLY inside the SpEL expression --
        // the caller passes a CustomerRef object, not a raw Long, and the
        // query extracts the id itself via SpEL property access.
        @Query("select o from Order o where o.customerId = :#{#customerRef.id()}")
        List<Order> findByCustomerRef(@Param("customerRef") CustomerRef customerRef);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(SpelQueryLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:spelquery3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order(100L, 50.0));
        repo.save(new Order(100L, 75.0));
        repo.save(new Order(200L, 30.0));

        List<Order> forCustomer100 = repo.findByCustomerRef(new CustomerRef(100L));
        System.out.println("orders for customer 100 = " + forCustomer100.stream().map(Order::getTotal).toList());

        if (forCustomer100.size() != 2) throw new AssertionError("Expected 2 orders for customer 100");
        System.out.println("SpEL extracted a property directly from the parameter object -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java SpelQueryLevel3.java`.

`:#{#customerRef.id()}` combines named-parameter binding syntax (`:...`) with a SpEL expression (`#{...}`) — the caller passes a whole `CustomerRef` object, and the query itself extracts `.id()` via SpEL property/method access, rather than requiring the caller to call `customerRef.id()` and pass a plain `Long` as a separate argument. This is especially useful when a query needs a value nested inside a larger object the caller already has at hand.

## 6. Walkthrough

Trace `repo.findByCustomerRef(new CustomerRef(100L))`.

1. **Call**: `findByCustomerRef` is invoked with a `CustomerRef` object wrapping `id = 100L`.
2. **Query template resolution (done once, at startup)**: when the `OrderRepository` proxy is built, Spring Data parses `:#{#customerRef.id()}`, recognizing it as a SpEL expression tied to the `customerRef` parameter — this establishes *how* to compute the bound value at call time, but doesn't compute it yet.
3. **Call-time SpEL evaluation**: for this specific invocation, the SpEL expression `#customerRef.id()` is evaluated against the actual `customerRef` argument (the `CustomerRef(100L)` instance), invoking its `id()` accessor and producing the value `100L`.
4. **Query parameter binding**: this computed `100L` is bound to the query's actual JPQL parameter position, exactly as if the caller had passed a plain `Long customerId = 100L` argument directly.
5. **SQL execution**: `WHERE customer_id = 100` executes against the database, matching the two orders whose `customerId` is `100L`.
6. **Return value**: `List<Order>`, containing exactly those two matching orders.
7. **Verification**: the program checks the result count, confirming the SpEL property-extraction correctly computed the right filter value from the nested `CustomerRef` object, without the caller needing to manually unwrap it beforehand.

```
 findByCustomerRef(CustomerRef(id=100))
        |
        v
 SpEL: #customerRef.id()  evaluated against the actual argument  -->  100L
        |
        v
 bound as the query's actual parameter value
        |
        v
 WHERE customer_id = 100   -->  2 matching orders
```

## 7. Gotchas & takeaways

> **Gotcha:** SpEL expressions in `@Query` strings add real parsing and evaluation overhead compared to plain parameter binding, and — more importantly — because they're evaluated dynamically per call, they can obscure exactly what a query does at a glance, making the query harder to review for correctness or security (SpEL, like any expression language embedded in a query string, deserves the same caution around untrusted input as string-concatenated SQL would). Reach for it specifically for the genuine use cases (`#{#entityName}` on shared base repositories, extracting a nested property) rather than as a general-purpose scripting escape hatch inside queries.

- `#{#entityName}` resolves, per repository, to the concrete entity's JPQL name — essential for `@Query` declared on a shared, generic base repository interface (the pattern from the earlier custom-base-interface card) that needs to work correctly for multiple different concrete entity types.
- `#{#paramName.property}` lets a query extract a nested value directly from a method parameter object via SpEL, sparing the caller from having to manually unwrap it into a separate, flatter argument.
- SpEL expressions are resolved once at query-template-build time (determining *how* to compute a value) and evaluated per call (actually computing it for that specific invocation's arguments) — a two-phase process similar to how derived-query parsing works.
- SpEL in queries is a targeted tool for specific, real problems (entity-name genericity, nested-property extraction) — it shouldn't be reached for as a general substitute for well-structured, explicit query parameters.
