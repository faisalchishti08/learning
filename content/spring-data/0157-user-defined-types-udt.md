---
card: spring-data
gi: 157
slug: user-defined-types-udt
title: "User-defined types (UDT)"
---

## 1. What it is

A Cassandra **user-defined type (UDT)** lets you group several related fields into a reusable, named structure — like a `address` type with `street`/`city`/`zip` fields — that can be embedded directly into a table's column, similar in spirit to embedding a sub-object in a MongoDB document, but as an explicitly declared type in Cassandra's schema. Spring Data Cassandra maps this with `@UserDefinedType`.

```java
@UserDefinedType("address")
class Address {
    String street;
    String city;
    String zipCode;
}

@Table("orders")
class Order {
    @PrimaryKey String orderId;
    Address deliveryAddress; // an entire UDT stored as ONE column
}
```

## 2. Why & when

Cassandra tables are otherwise "flat" — every column holds a scalar value (or a simple collection like a list/set/map). Without UDTs, a structured value like an address would have to be flattened into several separate columns (`street`, `city`, `zip_code`) directly on the parent table, which becomes unwieldy once you have several structured sub-objects, or need the same structure reused across multiple tables. A UDT groups related fields into one named, reusable, typed unit.

Reach for a UDT when:

- A group of fields naturally belongs together and is always read/written as a unit — an address, a monetary amount with a currency, a geographic coordinate.
- The same structure is reused across multiple tables — defining it once as a UDT avoids repeating the same set of flattened columns everywhere it's needed.
- You want the structure to be explicit and self-documenting in the schema, rather than implicit through a naming convention across several flat columns (`shipping_street`, `shipping_city`, `billing_street`, `billing_city`, ...).

## 3. Core concept

```
 CREATE TYPE address (
     street  text,
     city    text,
     zip_code text
 );

 CREATE TABLE orders (
     order_id          text PRIMARY KEY,
     delivery_address  address    -- the ENTIRE UDT stored as one column's value
 );

 -- Java side:
 Order order = new Order("1");
 order.deliveryAddress = new Address("123 Main St", "Springfield", "12345");
 -- ONE field on Order, holding a structured, multi-part value
```

A UDT column holds one structured value, read and written as a whole — not several independent flat columns bolted onto the parent table.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An orders table has a delivery_address column whose value is a structured address UDT rather than several flat columns">
  <rect x="20" y="20" width="280" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">table orders</text>
  <text x="160" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">order_id (PRIMARY KEY)</text>
  <text x="160" y="82" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">delivery_address: address</text>
  <text x="160" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(a UDT, one column)</text>

  <rect x="360" y="20" width="260" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">type address</text>
  <text x="490" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">street</text>
  <text x="490" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">city</text>
  <text x="490" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">zip_code</text>

  <line x1="300" y1="82" x2="355" y2="82" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

The `delivery_address` column's type is itself a structured type with its own named fields, not a scalar.

## 5. Runnable example

The scenario: modeling delivery addresses on orders, evolving from a basic UDT embedded in a table, to a UDT reused across two different tables (delivery and billing addresses), to a collection of UDTs — a list of addresses, matching Cassandra's support for collections of user-defined types.

### Level 1 — Basic

Model a UDT embedded as a single structured column on a table.

```java
import java.util.*;

public class UdtLevel1 {
    public static void main(String[] args) {
        Order order = new Order("1", new Address("123 Main St", "Springfield", "12345"));

        System.out.println("Order " + order.orderId + " delivers to: " + order.deliveryAddress);
        System.out.println("Accessing just the city: " + order.deliveryAddress.city);
    }
}

// Mirrors: @UserDefinedType("address") class Address { String street; String city; String zipCode; }
class Address {
    String street; String city; String zipCode;
    Address(String street, String city, String zipCode) { this.street = street; this.city = city; this.zipCode = zipCode; }
    public String toString() { return street + ", " + city + " " + zipCode; }
}

// Mirrors: @Table("orders") class Order { @PrimaryKey String orderId; Address deliveryAddress; }
class Order {
    String orderId;
    Address deliveryAddress; // the ENTIRE UDT as one field
    Order(String orderId, Address deliveryAddress) { this.orderId = orderId; this.deliveryAddress = deliveryAddress; }
}
```

How to run: `java UdtLevel1.java`

`Order.deliveryAddress` holds an entire `Address` object as one field, mirroring how a UDT column stores a structured value as a single unit in Cassandra — `order.deliveryAddress.city` accesses one part of that structure, just as CQL supports dotted access into a UDT column's fields (`SELECT delivery_address.city FROM orders ...`).

### Level 2 — Intermediate

Reuse the same UDT across two different fields (and conceptually, two different tables), matching a UDT's purpose as a shareable, reusable structure.

```java
import java.util.*;

public class UdtLevel2 {
    public static void main(String[] args) {
        Address home = new Address("123 Main St", "Springfield", "12345");
        Address office = new Address("456 Business Ave", "Metropolis", "67890");

        Order order = new Order("1", home, office); // delivered home, billed to the office

        System.out.println("Delivery address: " + order.deliveryAddress);
        System.out.println("Billing address:  " + order.billingAddress);
        System.out.println("Both use the SAME Address type -- no duplicated flat columns needed for each.");
    }
}

class Address {
    String street; String city; String zipCode;
    Address(String street, String city, String zipCode) { this.street = street; this.city = city; this.zipCode = zipCode; }
    public String toString() { return street + ", " + city + " " + zipCode; }
}

// The SAME Address UDT reused for two different purposes on the same entity.
class Order {
    String orderId;
    Address deliveryAddress;
    Address billingAddress;
    Order(String orderId, Address deliveryAddress, Address billingAddress) {
        this.orderId = orderId; this.deliveryAddress = deliveryAddress; this.billingAddress = billingAddress;
    }
}
```

How to run: `java UdtLevel2.java`

`Order` has two independent `Address` fields, both using the exact same UDT structure — this is the reuse benefit a UDT provides over flattening: without it, this table would need six separate columns (`delivery_street`, `delivery_city`, `delivery_zip`, `billing_street`, `billing_city`, `billing_zip`) instead of two clean, self-documenting UDT columns.

### Level 3 — Advanced

Model a collection of UDTs — a list of addresses on one entity, matching Cassandra's support for `list<frozen<address>>`-style columns.

```java
import java.util.*;
import java.util.stream.*;

public class UdtLevel3 {
    public static void main(String[] args) {
        Customer customer = new Customer("customer-A", List.of(
            new Address("Home", "123 Main St", "Springfield", "12345"),
            new Address("Work", "456 Business Ave", "Metropolis", "67890"),
            new Address("Parents", "789 Old Rd", "Smallville", "54321")
        ));

        System.out.println("customer-A's saved addresses (" + customer.savedAddresses.size() + "):");
        for (Address a : customer.savedAddresses) System.out.println("  " + a);

        // Find the "Work" address specifically -- application-side filtering over the embedded collection.
        Address work = customer.savedAddresses.stream().filter(a -> a.label.equals("Work")).findFirst().orElse(null);
        System.out.println("Work address specifically: " + work);
    }
}

class Address {
    String label; String street; String city; String zipCode;
    Address(String label, String street, String city, String zipCode) { this.label = label; this.street = street; this.city = city; this.zipCode = zipCode; }
    public String toString() { return "[" + label + "] " + street + ", " + city + " " + zipCode; }
}

// Mirrors: @Column("saved_addresses") List<Address> savedAddresses; -- a LIST of a UDT, e.g. list<frozen<address>>.
class Customer {
    String customerId;
    List<Address> savedAddresses;
    Customer(String customerId, List<Address> savedAddresses) { this.customerId = customerId; this.savedAddresses = savedAddresses; }
}
```

How to run: `java UdtLevel3.java`

`Customer.savedAddresses` is a `List<Address>`, mirroring a Cassandra column typed `list<frozen<address>>` — a collection where each element is itself a full UDT instance. Filtering for the `"Work"` address happens in application code after reading the whole list back, since Cassandra collections (including collections of UDTs) are generally read and written as a whole value, not queried element-by-element the way a relational join table might be.

## 6. Walkthrough

Execution starts in `main` for Level 3. `customer` is constructed with `savedAddresses` set to a `List.of(...)` containing three `Address` instances, each with a distinct `label` (`"Home"`, `"Work"`, `"Parents"`).

The first loop iterates `customer.savedAddresses` in list order and prints each address's `toString()` representation, showing all three entries exactly as stored.

`customer.savedAddresses.stream().filter(a -> a.label.equals("Work")).findFirst().orElse(null)` then filters the same list down to the one entry whose `label` equals `"Work"` — the second element in the list — and retrieves it via `findFirst()`. Since exactly one match exists, `work` ends up holding that specific `Address` object.

```
customer-A's saved addresses (3):
  [Home] 123 Main St, Springfield 12345
  [Work] 456 Business Ave, Metropolis 67890
  [Parents] 789 Old Rd, Smallville 54321
Work address specifically: [Work] 456 Business Ave, Metropolis 67890
```

In real Cassandra, `savedAddresses` mapped as `list<frozen<address>>` is written and read as one complete collection value per row — updating a single address within the list (say, changing the `"Work"` address's zip code) generally requires reading the whole list, modifying the relevant element in application code, and writing the entire list back, since Cassandra's frozen collections don't support in-place element updates the way individual columns do. This is an important practical constraint: UDT collections are great for values that are read and written together as a unit, but awkward for values that need frequent, independent per-element updates.

## 7. Gotchas & takeaways

> Gotcha: a UDT used inside a collection (like `list<frozen<address>>`) must be declared `frozen` — a frozen UDT is serialized and stored as a single opaque blob, which means it can't be updated field-by-field in place; the entire value must be read, modified, and rewritten. Non-frozen (individually updatable) UDTs are only supported as a single top-level column, not inside a collection.

> Gotcha: adding a new field to an existing UDT definition (`ALTER TYPE address ADD country text`) is supported and applies to future writes, but doesn't retroactively populate the new field on rows written before the change — exactly the same "schema evolution doesn't rewrite existing data" caveat that applies to adding a new field to any entity in a schema-flexible or evolving-schema store.

- A user-defined type (UDT) groups related fields into a reusable, named structure that can be embedded as a single column's value, avoiding the need to flatten structured data into many separate top-level columns.
- The same UDT can be reused across multiple fields or tables — an address type used for both delivery and billing addresses, for instance.
- Collections of UDTs (`list<frozen<address>>`, `set<frozen<address>>`, `map<text, frozen<address>>`) require the UDT to be `frozen`, meaning the whole value is treated as one opaque unit for read/write purposes.
- Frozen collections and frozen UDTs can't be updated field-by-field or element-by-element in place — updating one part requires reading, modifying, and rewriting the entire value.
