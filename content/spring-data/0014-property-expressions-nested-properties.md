---
card: spring-data
gi: 14
slug: property-expressions-nested-properties
title: "Property expressions & nested properties"
---

## 1. What it is

Property expressions are the part of query derivation responsible for matching the property name segment of a method (like `LastName` in `findByLastName`) against the entity's actual fields — including traversing into a related, nested object's fields, like `findByAddressCity` matching a `Customer` entity's `address.city` property, where `address` is itself an embedded object or a related entity. Spring Data resolves these by walking the entity's property graph, preferring an exact top-level property match, then falling back to splitting the name at different points to find a valid nested path.

```java
public class Customer {
    private Address address; // has its own "city" field
}

List<Customer> findByAddressCity(String city); // "address" -> "city" -- a nested traversal
```

## 2. Why & when

Real domain models are rarely flat — a `Customer` has an `Address`, an `Order` has a `Customer`, a `Customer` has a `Department` — and query needs regularly cross those boundaries: "find customers in this city" needs to reach through `Customer.address.city`. Property expressions exist so that a derived query method name can express exactly that traversal without dropping to `@Query` and writing a join clause by hand.

Understanding property expressions matters specifically when:

- You're writing a derived-query method that needs to filter on a related entity's or embedded object's field — knowing the naming convention (`AddressCity` for `address.city`) is what makes this expressible via derivation at all.
- You're debugging a startup failure about an ambiguous or unresolvable property — this happens when a compound property name like `AddressCity` could theoretically split multiple ways (an `AddressCity` top-level field *and* a nested `address.city` path both existing would be ambiguous), and Spring Data's resolution algorithm needs disambiguating with an explicit underscore (`Address_City`).
- You're deciding how deep a derived query should traverse relationships before switching to `@Query` — very deep nesting (three or more levels) tends to produce long, hard-to-read method names, at which point an explicit JPQL join in `@Query` is usually clearer.

## 3. Core concept

```
 findByAddressCity(String city)
        |
        v
 Spring Data's property-path resolution algorithm:
   1. Try "addressCity" as a single top-level property on the entity -- not found
   2. Split at the last capital letter boundary: "address" + "City"
      -- "address" IS a property on the entity, AND it has a "city" property -- MATCH
        |
        v
 Resolves to the path: entity.address.city
        |
        v
 JPQL: SELECT c FROM Customer c WHERE c.address.city = ?1
       (Hibernate translates this into the appropriate JOIN automatically)

 AMBIGUOUS CASE: if the entity had BOTH a top-level "addressCity" field
 AND an "address" object with a "city" field, use an underscore to disambiguate:
   findByAddress_City(...)   -- forces the split at "Address" | "City"
```

The traversal algorithm greedily tries to match the longest possible top-level property name first, backing off segment by segment until it finds a valid path — the underscore is the explicit override when that automatic algorithm would otherwise be ambiguous.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="findByAddressCity resolves by splitting into address and city, traversing the nested Address object">
  <rect x="10" y="20" width="220" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">findByAddressCity(city)</text>

  <rect x="270" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Customer.address</text>

  <rect x="460" y="20" width="150" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Address.city</text>

  <rect x="150" y="110" width="340" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="137" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="monospace">WHERE c.address.city = ?1</text>

  <line x1="230" y1="42" x2="265" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="42" x2="455" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="320" y1="65" x2="320" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The compound property name is split and re-split until each segment matches a real property along the path.

## 5. Runnable example

The scenario: a `Customer` entity with an embedded `Address`, evolving from a basic nested traversal, to a two-level-deep traversal through a related entity, to resolving a genuinely ambiguous property name using the underscore disambiguation syntax.

### Level 1 — Basic

Query through an `@Embedded` `Address` object using `findByAddressCity`, the simplest nested-property case.

```java
import jakarta.persistence.Embeddable;
import jakarta.persistence.Embedded;
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
public class PropertyExprLevel1 {

    @Embeddable
    public static class Address {
        private String city;
        protected Address() {}
        public Address(String city) { this.city = city; }
        public String getCity() { return city; }
    }

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        @Embedded
        private Address address;
        protected Customer() {}
        public Customer(String name, Address address) { this.name = name; this.address = address; }
        public String getName() { return name; }
    }

    public interface CustomerRepository extends JpaRepository<Customer, Long> {
        List<Customer> findByAddressCity(String city); // nested: address.city
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PropertyExprLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:propexpr1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        CustomerRepository repo = ctx.getBean(CustomerRepository.class);
        repo.save(new Customer("Ada", new Address("London")));
        repo.save(new Customer("Grace", new Address("New York")));
        repo.save(new Customer("Katherine", new Address("London")));

        List<Customer> londoners = repo.findByAddressCity("London");
        System.out.println("customers in London = " + londoners.stream().map(Customer::getName).toList());

        if (londoners.size() != 2) throw new AssertionError("Expected 2 customers in London");
        System.out.println("findByAddressCity correctly traversed into the embedded Address -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java PropertyExprLevel1.java` on JDK 17+.

`Address` is `@Embeddable`, meaning its fields (`city`) are stored as columns directly on the `Customer` table, not a separate joined table — `findByAddressCity(String city)` resolves the compound name by splitting `AddressCity` into `address` (a property on `Customer`) and `city` (a property on `Address`), producing `WHERE address.city = ?1`.

### Level 2 — Intermediate

Traverse through a genuine `@ManyToOne` relationship (a separate related entity, not an embedded value object) two levels deep — `findByCustomerAddressCity`, reaching from `Order` through `Customer` through `Address`.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class PropertyExprLevel2 {

    @Embeddable
    public static class Address {
        private String city;
        protected Address() {}
        public Address(String city) { this.city = city; }
    }

    @Entity
    public static class Customer {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        @Embedded
        private Address address;
        protected Customer() {}
        public Customer(String name, Address address) { this.name = name; this.address = address; }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        @ManyToOne
        private Customer customer;
        private double total;
        protected Order() {}
        public Order(Customer customer, double total) { this.customer = customer; this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // Two-level traversal: Order -> customer (Customer) -> address (Address) -> city
        List<Order> findByCustomerAddressCity(String city);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PropertyExprLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:propexpr2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        var customerCtx = ctx.getBean(org.springframework.data.jpa.repository.JpaRepository.class); // not used directly
        OrderRepository orderRepo = ctx.getBean(OrderRepository.class);

        // Use an EntityManager directly to persist related entities together for this example.
        jakarta.persistence.EntityManager em = ctx.getBean(jakarta.persistence.EntityManagerFactory.class).createEntityManager();
        em.getTransaction().begin();
        Customer ada = new Customer("Ada", new Address("London"));
        Customer grace = new Customer("Grace", new Address("New York"));
        em.persist(ada);
        em.persist(grace);
        em.persist(new Order(ada, 100.0));
        em.persist(new Order(ada, 50.0));
        em.persist(new Order(grace, 200.0));
        em.getTransaction().commit();
        em.close();

        List<Order> londonOrders = orderRepo.findByCustomerAddressCity("London");
        System.out.println("orders from London customers = " + londonOrders.stream().map(Order::getTotal).toList());

        if (londonOrders.size() != 2) throw new AssertionError("Expected 2 orders from London-based customers (Ada)");
        System.out.println("findByCustomerAddressCity traversed Order -> Customer -> Address -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java PropertyExprLevel2.java`.

`findByCustomerAddressCity(String city)` resolves through two hops: `customer` (a `@ManyToOne` property on `Order`), then `address` (an embedded property on `Customer`), then `city` (a field on `Address`) — Spring Data's resolution algorithm handles multi-level traversal exactly the same way it handles a single level, just continuing the split-and-match process further along the compound name. Hibernate translates this into the appropriate SQL `JOIN` between the `order` and `customer` tables automatically.

### Level 3 — Advanced

Create a genuinely ambiguous situation — an entity with both a top-level property whose name matches a possible split point *and* a nested property reachable the same way — and resolve it using the underscore-disambiguation syntax (`_`) to force the intended split.

```java
import jakarta.persistence.*;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class PropertyExprLevel3 {

    @Embeddable
    public static class ShippingDetails {
        private String status;
        protected ShippingDetails() {}
        public ShippingDetails(String status) { this.status = status; }
    }

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;

        // A top-level field whose name COULD collide with a naive split of "ShippingStatus".
        private String shippingStatus;

        // A nested object that ALSO has a "status" field, reachable as "shipping.status".
        @Embedded
        @AttributeOverride(name = "status", column = @Column(name = "shipping_details_status"))
        private ShippingDetails shipping;

        protected Order() {}
        public Order(String shippingStatus, ShippingDetails shipping) {
            this.shippingStatus = shippingStatus; this.shipping = shipping;
        }
        public String getShippingStatus() { return shippingStatus; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // Unambiguous: matches the TOP-LEVEL "shippingStatus" field directly (greedy match wins).
        List<Order> findByShippingStatus(String status);

        // Explicit underscore: FORCES the split at "shipping" | "status",
        // reaching into the embedded ShippingDetails.status field instead.
        List<Order> findByShipping_Status(String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(PropertyExprLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:propexpr3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("PENDING", new ShippingDetails("PACKED")));
        repo.save(new Order("PENDING", new ShippingDetails("SHIPPED")));
        repo.save(new Order("SHIPPED", new ShippingDetails("PACKED")));

        List<Order> byTopLevelField = repo.findByShippingStatus("PENDING");
        List<Order> byNestedField = repo.findByShipping_Status("PACKED");

        System.out.println("orders with top-level shippingStatus=PENDING: " + byTopLevelField.size());
        System.out.println("orders with nested shipping.status=PACKED: " + byNestedField.size());

        if (byTopLevelField.size() != 2) throw new AssertionError("Expected 2 orders with top-level shippingStatus=PENDING");
        if (byNestedField.size() != 2) throw new AssertionError("Expected 2 orders with nested shipping.status=PACKED");
        System.out.println("Top-level match and underscore-disambiguated nested match both resolved correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java PropertyExprLevel3.java`.

`findByShippingStatus` matches the top-level `shippingStatus` field directly — Spring Data's algorithm greedily tries the longest possible top-level property name first, and `shippingStatus` exists exactly as named, so no splitting is needed. `findByShipping_Status`, with an explicit underscore, forces the split at `shipping` | `Status`, deliberately reaching into the embedded `ShippingDetails.status` field instead — the two queries target entirely different columns despite very similar method names, and the underscore is what makes the second interpretation unambiguous and intentional rather than accidental.

## 6. Walkthrough

Trace Level 3's property resolution for both methods.

1. **Startup — `findByShippingStatus` resolution**: `PartTree` extracts the property segment `ShippingStatus`. The resolution algorithm first tries the full string, lowercased, as a single top-level property: `shippingStatus`. `Order` genuinely has a field named exactly `shippingStatus` — match found immediately, no traversal needed, no splitting attempted.
2. **Startup — `findByShipping_Status` resolution**: `PartTree` sees the explicit underscore in the method name, which is a direct instruction: split exactly here, into `Shipping` and `Status`, rather than running the automatic greedy-match algorithm. It checks `Order` for a property named `shipping` — found (the `@Embedded ShippingDetails shipping` field) — then checks `ShippingDetails` for a property named `status` — found. The path `shipping.status` is confirmed valid.
3. **Both methods' query templates are built** at this point (startup), each targeting a different column: `WHERE o.shippingStatus = ?1` for the first, `WHERE o.shipping.status = ?1` for the second (the latter resolving, at the JPA/Hibernate level, to the embedded column `shipping_details_status`, per the `@AttributeOverride`).
4. **`repo.findByShippingStatus("PENDING")`** executes its query, matching the two orders whose top-level `shippingStatus` field is `"PENDING"`.
5. **`repo.findByShipping_Status("PACKED")`** executes its separate query, matching the two orders whose embedded `shipping.status` field is `"PACKED"` — a completely different filter, on a completely different column, despite the very similar-looking method name.
6. **Verification**: the program checks both result counts independently, confirming the underscore genuinely selected a different resolution path than the plain, unambiguous method name did.

```
 findByShippingStatus(status)
        |
        v
 greedy match: "shippingStatus" IS a real top-level field -- MATCH, no split
        |
        v
 WHERE o.shippingStatus = ?1

 findByShipping_Status(status)      <- explicit underscore forces the split
        |
        v
 split forced at "Shipping" | "Status"
 "shipping" is a property -> "status" is a property ON shipping -- MATCH
        |
        v
 WHERE o.shipping.status = ?1   (different column entirely)
```

## 7. Gotchas & takeaways

> **Gotcha:** without the underscore, an ambiguous compound property name doesn't necessarily fail at startup — Spring Data's algorithm picks *a* valid interpretation (typically preferring the longest top-level match it can find first) and silently uses it, which may not be the interpretation you intended. The failure mode here isn't a loud startup error; it's a query that quietly does something other than what you meant. When a property name could plausibly resolve two different ways, use the underscore explicitly rather than relying on the automatic algorithm's default preference.

- Property expressions let a derived-query method name traverse into embedded objects and related entities, not just top-level fields — `findByAddressCity` reaching `Customer.address.city` is the simplest example, and multi-level traversal (`findByCustomerAddressCity`) works the same way, just continuing further.
- The resolution algorithm greedily prefers the longest top-level property match before attempting any split — this is why a genuinely top-level field named `shippingStatus` is matched directly, without ever considering a `shipping.status` interpretation.
- The underscore (`_`) is the explicit, unambiguous way to force a specific split point in a compound property name — reach for it whenever a name could plausibly resolve more than one way, or simply to make the intended traversal path self-documenting in the method name itself.
- Very deep nested traversal (three or more levels) tends to produce long, hard-to-parse-by-eye method names — at that point, an explicit `@Query` with a JPQL join is usually more maintainable than pushing property-expression derivation further.
