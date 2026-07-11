---
card: spring-data
gi: 77
slug: aggregate-roots-references
title: "Aggregate roots & references"
---

## 1. What it is

When one aggregate needs to point at *another*, separate aggregate (rather than containing it as a member), Spring Data JDBC represents that link with a plain identifier field (an `AggregateReference<T, ID>` or simply a foreign-key-typed field) instead of embedding or eagerly loading the other aggregate's object graph. This is the mechanism for keeping two aggregates genuinely independent while still relating them.

```java
class Order {
    @Id Long id;
    AggregateReference<Customer, Long> customer; // reference to a SEPARATE aggregate, not a member
    List<LineItem> lineItems;                     // members of THIS aggregate
}
```

## 2. Why & when

The philosophy card explained that members of one aggregate are always loaded/saved together with their root — but real domains have relationships that cross aggregate boundaries entirely, like an order referencing the customer who placed it. A `Customer` is its own aggregate (with its own repository, its own independent lifecycle) — `Order` should not load, save, or delete `Customer` as a side effect of doing so for itself.

Reach for an aggregate reference (rather than nesting the related object as a member) specifically when:

- The related object has its own independent lifecycle and repository — a `Customer` exists and is managed independently of any particular `Order`, unlike a `LineItem`, which has no meaning outside its `Order`.
- You want to avoid accidentally eager-loading (or worse, accidentally re-saving/re-deleting) a large, unrelated aggregate just because it's referenced by ID from another one.
- You need to model a genuine many-to-one or many-to-many relationship *between* aggregates, as opposed to a one-to-many composition *within* a single aggregate.

## 3. Core concept

```
 Order aggregate:                          Customer aggregate (SEPARATE, independent):
   Order (root)                              Customer (root)
     |-- LineItem (member, same aggregate)     -- own repository: CustomerRepository
     |-- customer: AggregateReference<Customer,Long>  -- just an ID, NOT a loaded object

 orderRepository.save(order)
   -> saves Order + its LineItems TOGETHER (same aggregate)
   -> does NOT save/touch Customer at all -- only its ID is stored as a foreign key

 To get the actual Customer: customerRepository.findById(order.customer.getId())
   -- an EXPLICIT, separate call -- never implicit/automatic
```

An aggregate reference is just an ID, deliberately not an object graph — fetching the referenced aggregate is always a separate, explicit repository call.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="An Order aggregate holds only a Customer's ID as a reference, requiring a separate explicit call to load the actual Customer">
  <rect x="20" y="15" width="260" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Order aggregate</text>
  <text x="150" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">lineItems: [LineItem, LineItem]</text>
  <text x="150" y="75" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">customer: AggregateReference(id=42)</text>
  <text x="150" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-- just an ID, not loaded</text>

  <rect x="380" y="15" width="240" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Customer aggregate (id=42)</text>
  <text x="500" y="58" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">own repository, own lifecycle</text>
  <text x="500" y="75" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">NOT loaded/saved by OrderRepository</text>

  <line x1="280" y1="70" x2="375" y2="60" stroke="#8b949e" stroke-width="1.3" stroke-dasharray="4,3" marker-end="url(#ar)"/>
  <text x="330" y="55" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reference only</text>

  <rect x="30" y="130" width="580" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="149" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">customerRepository.findById(order.customer.getId()) -- an explicit, SEPARATE call</text>
  <defs><marker id="ar" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The reference is a dotted line (just an ID), not a solid containment relationship — loading the actual `Customer` always requires a deliberate, separate call.

## 5. Runnable example

The scenario: orders that reference customers, evolving from a naive embedded-object approach showing the problem it causes, to an ID-based `AggregateReference` model, to a full two-repository setup with explicit cross-aggregate loading.

### Level 1 — Basic

Show the problem with naively embedding a full `Customer` object inside `Order`: saving an order risks unintentionally also carrying (and potentially overwriting) unrelated customer data.

```java
import java.util.*;

class Customer { long id; String name; Customer(long id, String name) { this.id = id; this.name = name; } }

// PROBLEMATIC: Order embeds a full Customer object, blurring the aggregate boundary.
class Order {
    long id; String status;
    Customer customer; // the WHOLE customer object, not just a reference
    Order(long id, String status, Customer customer) { this.id = id; this.status = status; this.customer = customer; }
}

public class AggregateRefLevel1 {
    public static void main(String[] args) {
        Customer customer = new Customer(42, "Ada Lovelace");
        Order order = new Order(1, "PENDING", customer);

        // Later, some other part of the app updates the customer's name via their OWN aggregate...
        customer.name = "Ada King"; // she used both surnames at different times

        // ...but `order.customer` is the SAME object reference -- it "sees" the change even though
        // Order was never re-saved. This blurs exactly where the Order aggregate's boundary is.
        System.out.println("Order's view of the customer: " + order.customer.name);
        System.out.println("This changed even though nobody touched the Order at all!");
    }
}
```

How to run: `java AggregateRefLevel1.java`

`order.customer.name` reflects the mutation made through the *separate* `customer` variable, even though nothing about `order` itself was ever re-saved — embedding the full object blurs the aggregate boundary between `Order` and `Customer`, exactly the ambiguity `AggregateReference` is designed to eliminate by holding only an ID.

### Level 2 — Intermediate

Replace the embedded `Customer` object with an ID-based reference, matching `AggregateReference<Customer, Long>`.

```java
import java.util.*;

class Customer { long id; String name; Customer(long id, String name) { this.id = id; this.name = name; } }

// Stands in for org.springframework.data.jdbc.core.mapping.AggregateReference<Customer, Long>
class AggregateReference {
    private final long id;
    AggregateReference(long id) { this.id = id; }
    long getId() { return id; }
}

class Order {
    long id; String status;
    AggregateReference customer; // JUST an ID -- no object graph, no shared mutable state
    Order(long id, String status, AggregateReference customer) { this.id = id; this.status = status; this.customer = customer; }
}

public class AggregateRefLevel2 {
    public static void main(String[] args) {
        Customer customer = new Customer(42, "Ada Lovelace");
        Order order = new Order(1, "PENDING", new AggregateReference(customer.id));

        customer.name = "Ada King"; // mutate the customer independently

        // order.customer only ever held an ID -- it cannot "see" the name change at all.
        System.out.println("Order's reference: id=" + order.customer.getId());
        System.out.println("The Order aggregate has NO visibility into the Customer's fields.");
    }
}
```

How to run: `java AggregateRefLevel2.java`

`order.customer` only ever exposes `getId()` — there is no `.name` to accidentally observe or mutate through it. Changing `customer.name` independently has zero effect on `order`, because `order` never held a reference to the `Customer` object at all, only to its identifier — this is the whole point of `AggregateReference`.

### Level 3 — Advanced

Add both repositories (`OrderRepository`, `CustomerRepository`) and show the explicit, separate call required to actually resolve a reference into the real `Customer` object — plus confirm that saving an order never touches the customer's own data.

```java
import java.util.*;

class Customer { long id; String name; Customer(long id, String name) { this.id = id; this.name = name; } }

class AggregateReference {
    private final long id;
    AggregateReference(long id) { this.id = id; }
    long getId() { return id; }
}

class Order {
    long id; String status;
    AggregateReference customer;
    Order(long id, String status, AggregateReference customer) { this.id = id; this.status = status; this.customer = customer; }
}

class CustomerRepository {
    Map<Long, Customer> db = new HashMap<>();
    Customer save(Customer c) { db.put(c.id, c); return c; }
    Optional<Customer> findById(long id) { return Optional.ofNullable(db.get(id)); }
}

class OrderRepository {
    Map<Long, Order> db = new HashMap<>();
    Order save(Order o) {
        System.out.println("  SQL: INSERT/UPDATE orders (customer_id=" + o.customer.getId() + ") -- only the FK, not customer data");
        db.put(o.id, o);
        return o;
    }
    Optional<Order> findById(long id) { return Optional.ofNullable(db.get(id)); }
}

public class AggregateRefLevel3 {
    public static void main(String[] args) {
        CustomerRepository customerRepo = new CustomerRepository();
        OrderRepository orderRepo = new OrderRepository();

        Customer ada = customerRepo.save(new Customer(42, "Ada Lovelace")); // independent save, own aggregate
        Order order = orderRepo.save(new Order(1, "PENDING", new AggregateReference(ada.id))); // only stores the FK

        // To get the ACTUAL customer, an explicit, separate lookup is required:
        Order found = orderRepo.findById(1L).orElseThrow();
        Customer resolvedCustomer = customerRepo.findById(found.customer.getId())
            .orElseThrow(() -> new NoSuchElementException("Customer not found"));

        System.out.println("Order " + found.id + " belongs to: " + resolvedCustomer.name);

        // Mutating the customer independently never requires touching the order at all.
        ada.name = "Ada King";
        customerRepo.save(ada); // saved through its OWN repository -- orderRepo is never involved
        System.out.println("Order still references the same customer ID: " + found.customer.getId());
    }
}
```

How to run: `java AggregateRefLevel3.java`

`orderRepo.save(order)` only ever prints `customer_id=42` — it never touches `Customer`'s own fields. Resolving the actual customer name requires the explicit two-step `orderRepo.findById(...)` followed by `customerRepo.findById(found.customer.getId())` — there is no automatic join or lazy load bridging the two aggregates, matching how Spring Data JDBC deliberately keeps aggregate boundaries hard and explicit.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `customerRepo.save(new Customer(42, "Ada Lovelace"))` runs — this is a save on `Customer`'s own, independent repository, entirely unrelated to any `Order`.

Next, `orderRepo.save(new Order(1, "PENDING", new AggregateReference(42)))` runs. Inside `OrderRepository.save`, only `o.customer.getId()` (`42`) is used to build the simulated SQL — the `Customer` object itself is never touched, printed, or referenced by this method at all, matching how the real `orders` table would only ever gain a `customer_id` foreign-key column, not a copy of customer data.

Then `orderRepo.findById(1L)` retrieves the order back, and `customerRepo.findById(found.customer.getId())` performs a *second*, entirely separate repository call to resolve the actual `Customer` object — this is the explicit "join" application code must perform itself; nothing automatic happened when `found` was retrieved. The printed line correctly shows "Order 1 belongs to: Ada Lovelace".

Finally, `ada.name` is mutated to `"Ada King"` and saved through `customerRepo` alone — `orderRepo` is never called during this step. The final printed line confirms `found.customer.getId()` is still `42`, completely unaffected by the customer's name change, because the `Order` aggregate never held anything about the customer beyond that one ID.

```
customerRepo.save(Customer{id=42, name="Ada Lovelace"})      -- independent aggregate
orderRepo.save(Order{id=1, customer=ref(42)})                -- stores customer_id=42 only

orderRepo.findById(1) -> order{customer=ref(42)}
customerRepo.findById(42) -> Customer{name="Ada Lovelace"}    -- SEPARATE explicit call
"Order 1 belongs to: Ada Lovelace"

ada.name = "Ada King"; customerRepo.save(ada)                 -- orderRepo untouched
order.customer.getId() still == 42                            -- unaffected
```

In a real Spring Data JDBC application, `Order.customer` typed as `AggregateReference<Customer, Long>` maps to a plain `customer_id BIGINT` foreign-key column in the `orders` table — nothing more. `orderRepository.save(order)` writes only that ID; retrieving the actual `Customer` entity always requires an explicit `customerRepository.findById(order.customer().getId())` call in application code (often inside a service method that composes both repositories), because Spring Data JDBC deliberately never performs implicit joins or lazy loading across aggregate boundaries — that boundary is exactly where JPA's rich object graph and Spring Data JDBC's plain-ID reference model diverge.

## 7. Gotchas & takeaways

> Gotcha: embedding a full related object (as in Level 1) instead of an `AggregateReference` doesn't just blur modeling intent — practically, it can also cause Spring Data JDBC to try to treat the embedded object as a *member* of the same aggregate, attempting to insert/update/delete it alongside the root, which is almost never the intended behavior for a genuinely separate aggregate like `Customer`.

- `AggregateReference<T, ID>` represents a link to a *different, independent* aggregate as a plain ID — never as a loaded object graph.
- Saving an aggregate never touches (reads, writes, or cascades to) any aggregate it merely references — only aggregates it actually *contains* as members are affected.
- Resolving a reference into the real object always requires an explicit, separate repository call — there is no automatic join, no lazy loading, ever.
- Use references between independently-managed aggregates (like `Order` → `Customer`); use plain member fields/collections (like `Order` → `LineItem`) within a single aggregate.
