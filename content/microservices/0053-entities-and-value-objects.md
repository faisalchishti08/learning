---
card: microservices
gi: 53
slug: entities-and-value-objects
title: Entities and value objects
---

## 1. What it is

An **entity** is a domain object defined by its **identity** — a `Customer` with ID `cust-1` is still the same customer even if their name and email change; two `Customer` objects with different IDs are different customers even if every other field happens to match. A **value object** is a domain object defined entirely by its **attributes**, with no identity of its own — two `Money` objects representing `$9.99 USD` are simply equal, interchangeable, and typically **immutable**; there's no meaningful sense in which one is "the same $9.99" as another distinct from it. Getting this distinction right in your code's own types is a direct, concrete application of [ubiquitous language](0048-ubiquitous-language.md): the code should reflect which domain concepts genuinely have identity and which are just descriptive values.

## 2. Why & when

Modeling a value object as if it were an entity (giving `Money` its own database ID and mutable state) invites bugs: code might mutate a shared `Money` instance in place, silently corrupting every other object that happens to reference that same instance, when the correct behavior is to produce a brand-new `Money` value representing the result. Modeling an entity as if it were a value object (comparing two `Customer` objects purely by their current field values) breaks the moment a customer legitimately changes their name — two representations of the *same* customer, at different points in time, would incorrectly compare as "different."

Apply the distinction deliberately for every domain concept you model: does this thing have a continuous identity that persists as its attributes change over time (entity), or is it fully described by its current attributes with no independent identity of its own (value object)? Make value objects immutable by default — any "change" to a value object should produce a new instance, never mutate the existing one in place.

## 3. Core concept

The concrete test, and its consequence for equality and mutability:

| | Entity | Value Object |
|---|---|---|
| Defined by | Identity (an ID) | Attributes (its actual values) |
| Equality | Same ID = same entity, regardless of other field values | Same attribute values = equal, regardless of object reference |
| Mutability | Typically mutable — its attributes can change over its lifetime | Typically immutable — a "change" produces a new instance |
| Example | `Customer`, `Order` | `Money`, `Address`, `DateRange` |

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An entity is compared by identity even as its attributes change over time; a value object is compared by its attributes, with no identity of its own">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Entity (Customer)</text>
  <rect x="30" y="35" width="220" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">id=cust-1, name="Alice"</text>
  <rect x="30" y="90" width="220" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="115" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">id=cust-1, name="Alice Smith"</text>
  <text x="140" y="145" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">SAME entity (same id)</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Value Object (Money)</text>
  <rect x="390" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="445" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">$9.99 USD</text>
  <rect x="510" y="35" width="110" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="565" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">$9.99 USD</text>
  <text x="500" y="145" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">EQUAL (same attributes, no identity)</text>
</svg>

An entity's identity persists across attribute changes; a value object's identity is nothing more than its attributes.

## 5. Runnable example

Scenario: modeling a customer and a monetary amount, first with the entity/value-object distinction ignored (causing bugs), then modeled correctly with Java records and explicit identity handling.

### Level 1 — Basic

```java
// File: DistinctionIgnored.java -- Money modeled as MUTABLE, no immutability;
// Customer compared by FIELD VALUES instead of identity -- BOTH backwards.
import java.util.*;

public class DistinctionIgnored {
    static class Money { double amount; Money(double amount) { this.amount = amount; } } // MUTABLE -- should be a value object

    static class Customer { // compared by field equality below -- should be by IDENTITY
        String id; String name;
        Customer(String id, String name) { this.id = id; this.name = name; }
    }

    public static void main(String[] args) {
        Money price = new Money(9.99);
        Money discountedPrice = price; // aliasing, not a new value
        discountedPrice.amount -= 2.00; // MUTATES the SAME object -- price is corrupted too!
        System.out.println("original price is now (WRONG): " + price.amount);

        Customer alice = new Customer("cust-1", "Alice");
        Customer aliceRenamed = new Customer("cust-1", "Alice Smith"); // SAME customer, name changed
        System.out.println("same customer? " + (alice.name.equals(aliceRenamed.name))); // WRONG test -- compares names, not identity
    }
}
```

**How to run:** `javac DistinctionIgnored.java && java DistinctionIgnored` (JDK 17+).

Expected output:
```
original price is now (WRONG): 7.99
same customer? false
```

Two bugs from ignoring the distinction: `price` was silently corrupted because `Money` is mutable and `discountedPrice` was just an alias to the same object, not a new value. And comparing `alice` to `aliceRenamed` by name incorrectly concludes they're different customers, when they should be recognized as the same customer (`cust-1`) whose name simply changed.

### Level 2 — Intermediate

```java
// File: CorrectModeling.java -- Money as an IMMUTABLE value object;
// Customer compared by IDENTITY (its id), not its other fields.
import java.util.*;

public class CorrectModeling {
    record Money(double amount) { // IMMUTABLE by construction (Java records are final and immutable)
        Money minus(double reduction) { return new Money(amount - reduction); } // returns a NEW value, never mutates
    }

    static class Customer {
        final String id; // identity, NEVER changes for this customer's lifetime
        String name;      // attributes CAN change without affecting identity
        Customer(String id, String name) { this.id = id; this.name = name; }

        @Override
        public boolean equals(Object other) { // equality by IDENTITY, not by other fields
            return other instanceof Customer c && this.id.equals(c.id);
        }
        @Override
        public int hashCode() { return id.hashCode(); }
    }

    public static void main(String[] args) {
        Money price = new Money(9.99);
        Money discountedPrice = price.minus(2.00); // a NEW value, price is UNCHANGED
        System.out.println("original price (correctly unchanged): " + price.amount());
        System.out.println("discounted price (new value): " + discountedPrice.amount());

        Customer alice = new Customer("cust-1", "Alice");
        Customer aliceRenamed = new Customer("cust-1", "Alice Smith");
        System.out.println("same customer? " + alice.equals(aliceRenamed)); // correctly TRUE -- same id
    }
}
```

**How to run:** `javac CorrectModeling.java && java CorrectModeling` (JDK 17+).

Expected output:
```
original price (correctly unchanged): 9.99
discounted price (new value): 7.99
same customer? true
```

`Money.minus` returns a brand-new `Money` instance, leaving `price` completely unaffected — the immutability bug from Level 1 is structurally impossible now. `Customer.equals` compares only `id`, correctly recognizing `alice` and `aliceRenamed` as the same entity despite their differing `name` field.

### Level 3 — Advanced

```java
// File: ValueObjectInAggregate.java -- use a value object (Money) INSIDE
// an entity/aggregate (Order), demonstrating how the two concepts compose.
import java.util.*;

public class ValueObjectInAggregate {
    record Money(double amount) {
        Money plus(Money other) { return new Money(this.amount + other.amount); } // combining VALUES produces a NEW value
    }

    record OrderLineItem(String item, Money price) { } // a value object itself -- no independent identity, just describes a line

    static class Order { // the ENTITY / aggregate root -- has identity (orderId)
        final String orderId;
        private final List<OrderLineItem> lineItems = new ArrayList<>();
        private Money total = new Money(0);

        Order(String orderId) { this.orderId = orderId; }

        void addLineItem(String item, Money price) {
            lineItems.add(new OrderLineItem(item, price)); // storing a VALUE object inside the ENTITY
            total = total.plus(price); // combining Money VALUES produces a fresh total, never mutating in place
        }

        Money getTotal() { return total; }

        @Override
        public boolean equals(Object other) { return other instanceof Order o && this.orderId.equals(o.orderId); } // identity-based
    }

    public static void main(String[] args) {
        Order order = new Order("ord-1");
        order.addLineItem("widget", new Money(9.99));
        order.addLineItem("gadget", new Money(19.99));

        System.out.println("Order " + order.orderId + " total: $" + order.getTotal().amount());

        Order sameOrderDifferentInstance = new Order("ord-1"); // a DIFFERENT object, but SAME identity
        System.out.println("Same order (by identity)? " + order.equals(sameOrderDifferentInstance));
    }
}
```

**How to run:** `javac ValueObjectInAggregate.java && java ValueObjectInAggregate` (JDK 17+).

Expected output:
```
Order ord-1 total: $29.98
Same order (by identity)? true
```

The production-flavored composition: `Order` is an entity (identity-based equality via `orderId`), while `Money` and `OrderLineItem` are value objects (immutable, defined purely by their content) living *inside* that entity. `addLineItem` never mutates an existing `Money` in place — `total.plus(price)` always produces a fresh `Money` value, reassigned to `total` — exactly the immutability discipline value objects require, composed correctly inside an aggregate that itself has genuine identity.

## 6. Walkthrough

1. `order.addLineItem("widget", new Money(9.99))` runs first: it constructs a new `OrderLineItem` value object and appends it to `lineItems`, then computes `total = total.plus(new Money(9.99))`. Since `total` started as `new Money(0)`, `plus` returns `new Money(0 + 9.99) = Money(9.99)`, and this new instance replaces `total`.
2. `order.addLineItem("gadget", new Money(19.99))` runs next: `total.plus(new Money(19.99))` computes `new Money(9.99 + 19.99) = Money(29.98)`, again replacing `total` with a fresh instance rather than mutating the previous one.
3. `order.getTotal().amount()` reads the final `total`'s `amount` field, `29.98`, confirming both line items were correctly accumulated.
4. `new Order("ord-1")` constructs `sameOrderDifferentInstance` — a genuinely different Java object in memory, with its own empty `lineItems` list and its own `total` starting at `Money(0)`.
5. `order.equals(sameOrderDifferentInstance)` calls the overridden `equals`, which checks only `this.orderId.equals(o.orderId)` — since both are `"ord-1"`, this returns `true`, correctly recognizing them as the same entity by identity, even though their other state (line items, total) currently differs completely — exactly matching how a real `Order` entity's identity persists independently of its current field values.

```
Order (entity, identity = orderId):
   addLineItem -> total = total.plus(newMoney)  <- Money (value object) recombined, never mutated in place
   addLineItem -> total = total.plus(newMoney)
        |
equals() compares ONLY orderId -- two Order instances with the SAME id are the SAME entity, regardless of their other state
```

## 7. Gotchas & takeaways

> **Gotcha:** Java's default `equals` (inherited from `Object`) compares object references, not field values — without explicitly overriding `equals` and `hashCode` on an entity class (as `Customer` and `Order` do above), two objects representing the same logical entity but stored in different variables will incorrectly compare as unequal, even if you intended identity-based equality. Records get sensible value-based equality automatically, which is exactly right for value objects but would be wrong to rely on, unmodified, for an entity.

- An entity is defined by identity (an ID) that persists as its other attributes change; a value object is defined entirely by its current attributes, with no identity of its own.
- Value objects should be immutable — any "change" produces a new instance rather than mutating the existing one, preventing a whole class of aliasing bugs where an unintended shared reference gets silently corrupted.
- Entities need explicit identity-based `equals`/`hashCode` (comparing only the ID), since a language's default object equality won't automatically match this domain concept.
- The two concepts compose naturally: an aggregate root (an entity) commonly contains and manages several value objects internally, exactly as `Order` manages its `Money` total and `OrderLineItem` values above.
