---
card: spring-data
gi: 80
slug: embedded-entities-embedded
title: "Embedded entities (@Embedded)"
---

## 1. What it is

`@Embedded` flattens a nested value object's fields directly into the *same* table as its containing entity, instead of creating a separate child table the way a `@MappedCollection` association would. It's for small, cohesive value objects (like an address or a money amount) that have no independent identity and never need their own table.

```java
class Order {
    @Id Long id;
    @Embedded(onEmpty = OnEmpty.USE_NULL) Address shippingAddress; // flattened into the SAME "order" table
}
class Address { String street; String city; String zip; } // no @Id -- not an aggregate/entity of its own
```

## 2. Why & when

The mapping and `@MappedCollection` cards both covered *one-to-many* relationships, always producing a separate child table. `@Embedded` is for the opposite case: a *single* nested value object that logically belongs entirely to one row and should live in that same row's columns — creating a separate one-row-per-parent table for something like an address would be unnecessary overhead and an awkward join for no benefit.

Reach for `@Embedded` specifically when:

- The nested object is a genuine value object — no identity of its own, never queried or referenced independently of its parent (an `Address`, a `Money` amount with currency, a `DateRange`).
- You want the nested object's fields to simply become extra columns on the parent's existing table, avoiding a join entirely for data that's always read/written together with the parent anyway.
- You need to distinguish "no address at all" (`null`) from "an address with all-blank fields" — `@Embedded(onEmpty = OnEmpty.USE_NULL)` controls exactly this behavior when every embedded column comes back empty from a query.

## 3. Core concept

```
 class Order {
     @Id Long id;
     String status;
     @Embedded(onEmpty = OnEmpty.USE_NULL) Address shippingAddress;
 }
 class Address { String street; String city; String zip; }

 Maps to ONE table, "order":
   id | status  | shipping_address_street | shipping_address_city | shipping_address_zip
   -- Address's fields become PREFIXED columns on the SAME row -- no separate "address" table at all
```

`@Embedded` fields are prefixed with the field's own name by default, flattening the nested object's fields directly into the parent's row.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="An embedded Address value object flattens its fields as prefixed columns on the same order row, no separate table">
  <rect x="20" y="20" width="240" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">class Order</text>
  <text x="140" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">id, status,</text>
  <text x="140" y="74" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">@Embedded Address shippingAddress</text>

  <rect x="340" y="10" width="280" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">table "order" (ONE table)</text>
  <text x="360" y="55" fill="#8b949e" font-size="8.5" font-family="monospace">id, status,</text>
  <text x="360" y="75" fill="#8b949e" font-size="8.5" font-family="monospace">shipping_address_street,</text>
  <text x="360" y="95" fill="#8b949e" font-size="8.5" font-family="monospace">shipping_address_city,</text>
  <text x="360" y="115" fill="#8b949e" font-size="8.5" font-family="monospace">shipping_address_zip</text>

  <line x1="260" y1="60" x2="335" y2="60" stroke="#8b949e" stroke-width="1.3" marker-end="url(#em)"/>
  <defs><marker id="em" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Unlike a `@MappedCollection` association, `@Embedded` never creates a second table — the nested object's fields simply become more columns on the parent's row.

## 5. Runnable example

The scenario: an order with a shipping address, evolving from a naive separate-table approach highlighting the unnecessary overhead, to a flattened embedded model, to handling the "address entirely absent" case with `onEmpty`.

### Level 1 — Basic

Show the alternative being avoided: modeling `Address` as its own separate table/entity, even though it never has independent identity or is ever queried on its own.

```java
import java.util.*;

// Modeled (incorrectly, for a pure value object) as its own separate "entity" with its own table.
class Address { long id; long orderId; String street; String city; Address(long id, long orderId, String street, String city) { this.id = id; this.orderId = orderId; this.street = street; this.city = city; } }
class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

public class EmbeddedLevel1 {
    public static void main(String[] args) {
        Map<Long, Order> orders = new HashMap<>();
        Map<Long, Address> addresses = new HashMap<>(); // a WHOLE separate table, just for one address per order

        Order order = new Order(1, "PENDING");
        orders.put(1L, order);
        addresses.put(1L, new Address(100, 1, "123 Main St", "Springfield")); // needs its own PK (100), own FK (orderId)

        // Reading the order's address requires a SEPARATE lookup/join, even though it's a 1-to-1, always-together relationship.
        Address addr = addresses.get(order.id);
        System.out.println("Order " + order.id + " ships to: " + addr.street + ", " + addr.city);
        System.out.println("(This required a whole separate table + join for data that's always read together.)");
    }
}
```

How to run: `java EmbeddedLevel1.java`

`Address` needed its own primary key (`id=100`) and its own foreign key (`orderId`) despite never being queried independently of its `Order` — a full second table exists purely to hold three columns that are always read and written together with the order. This is the overhead `@Embedded` avoids.

### Level 2 — Intermediate

Replace the separate table with a flattened, embedded representation — `Address`'s fields become prefixed columns directly on the `Order`'s own row.

```java
import java.util.*;

class Address { String street; String city; Address(String street, String city) { this.street = street; this.city = city; } }

class Order {
    long id; String status;
    Address shippingAddress; // @Embedded -- NOT a separate table, just nested fields
    Order(long id, String status, Address shippingAddress) { this.id = id; this.status = status; this.shippingAddress = shippingAddress; }
}

public class EmbeddedLevel2 {
    // Simulates the flattened row Spring Data JDBC would actually store/query.
    static Map<String, Object> toFlattenedRow(Order order) {
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", order.id);
        row.put("status", order.status);
        row.put("shipping_address_street", order.shippingAddress.street); // prefixed with the field name
        row.put("shipping_address_city", order.shippingAddress.city);
        return row;
    }

    public static void main(String[] args) {
        Order order = new Order(1, "PENDING", new Address("123 Main St", "Springfield"));
        Map<String, Object> row = toFlattenedRow(order);

        System.out.println("Single 'order' table row: " + row);
        System.out.println("No separate address table, no join needed to read the address.");
    }
}
```

How to run: `java EmbeddedLevel2.java`

`toFlattenedRow` produces a single map representing one database row — `shippingAddress`'s two fields appear as `shipping_address_street` and `shipping_address_city`, prefixed with the embedded field's own name (`shippingAddress` → `shipping_address_`), exactly matching Spring Data JDBC's default `@Embedded` column-naming behavior. There is no second table, no join, no separate primary/foreign key pair.

### Level 3 — Advanced

Handle the "address entirely absent" case with `onEmpty` semantics: when every embedded column comes back empty/null from a query, decide whether to reconstruct `null` or an object with all-null fields.

```java
import java.util.*;

class Address { String street; String city; Address(String street, String city) { this.street = street; this.city = city; }
    public String toString() { return street == null && city == null ? "Address{all null}" : "Address{" + street + ", " + city + "}"; } }

enum OnEmpty { USE_NULL, USE_EMPTY }

public class EmbeddedLevel3 {
    // Simulates reconstructing an @Embedded field from a flattened row, honoring the onEmpty strategy.
    static Address reconstructAddress(Map<String, Object> row, OnEmpty onEmpty) {
        String street = (String) row.get("shipping_address_street");
        String city = (String) row.get("shipping_address_city");

        boolean allNull = street == null && city == null;
        if (allNull && onEmpty == OnEmpty.USE_NULL) {
            return null; // @Embedded(onEmpty = OnEmpty.USE_NULL): no address at all
        }
        return new Address(street, city); // USE_EMPTY (or partially-populated): construct the object regardless
    }

    public static void main(String[] args) {
        // Row representing an order that was NEVER given a shipping address -- both columns are null.
        Map<String, Object> rowWithNoAddress = new HashMap<>();
        rowWithNoAddress.put("id", 1L);
        rowWithNoAddress.put("shipping_address_street", null);
        rowWithNoAddress.put("shipping_address_city", null);

        Address withUseNull = reconstructAddress(rowWithNoAddress, OnEmpty.USE_NULL);
        Address withUseEmpty = reconstructAddress(rowWithNoAddress, OnEmpty.USE_EMPTY);

        System.out.println("onEmpty=USE_NULL:  shippingAddress = " + withUseNull);   // null -- correctly "no address"
        System.out.println("onEmpty=USE_EMPTY: shippingAddress = " + withUseEmpty);  // Address{all null} -- an object still gets created

        // Row representing an order WITH a real address.
        Map<String, Object> rowWithAddress = Map.of(
            "id", 2L, "shipping_address_street", "456 Oak Ave", "shipping_address_city", "Metropolis");
        System.out.println("Order with a real address: " + reconstructAddress(rowWithAddress, OnEmpty.USE_NULL));
    }
}
```

How to run: `java EmbeddedLevel3.java`

For `rowWithNoAddress` (both embedded columns `null`), `OnEmpty.USE_NULL` correctly reconstructs `shippingAddress` as `null` — matching the intent "this order simply has no shipping address" — while `OnEmpty.USE_EMPTY` would instead construct an `Address` object whose fields are all `null`, a subtly different (and usually less useful) outcome. For `rowWithAddress`, both strategies behave identically since the columns aren't actually empty.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `rowWithNoAddress` is built representing a database row where `shipping_address_street` and `shipping_address_city` are both `null` — standing in for an order that was created without ever specifying a shipping address.

`reconstructAddress(rowWithNoAddress, OnEmpty.USE_NULL)` runs: it reads both columns (both `null`), computes `allNull = true`, and since `onEmpty == OnEmpty.USE_NULL`, returns `null` directly — `shippingAddress` on the reconstructed `Order` would correctly be `null`, matching the semantic "no address was ever given."

`reconstructAddress(rowWithNoAddress, OnEmpty.USE_EMPTY)` runs next on the *same* row: `allNull` is still `true`, but since `onEmpty` is `USE_EMPTY` this time, the early-return branch is skipped, and `new Address(null, null)` is constructed and returned instead — a non-null `Address` object exists, but all of its fields are `null`, a meaningfully different outcome than the `USE_NULL` case.

Finally, `rowWithAddress` (a row with real, non-null values) is reconstructed with `OnEmpty.USE_NULL` — since `allNull` is `false` in this case, the early-return branch never triggers regardless of the `onEmpty` setting, and a proper `Address{456 Oak Ave, Metropolis}` is returned.

```
rowWithNoAddress (street=null, city=null):
   USE_NULL  -> allNull=true  -> return null                    (no address object at all)
   USE_EMPTY -> allNull=true  -> return Address(null, null)      (an object, but empty)

rowWithAddress (street="456 Oak Ave", city="Metropolis"):
   USE_NULL  -> allNull=false -> return Address("456 Oak Ave", "Metropolis")  (onEmpty irrelevant here)
```

In a real Spring Data JDBC application, `@Embedded(onEmpty = OnEmpty.USE_NULL) Address shippingAddress` on `Order` causes exactly this logic to run every time a row is mapped back into an `Order` object: Spring Data JDBC checks whether *every* column prefixed `shipping_address_` came back `null` from the query, and if so (with `USE_NULL` configured), sets `shippingAddress` itself to `null` rather than constructing an `Address` with all-null fields — sparing calling code from having to separately check "is this address actually populated" versus "is this address object present at all."

## 7. Gotchas & takeaways

> Gotcha: `@Embedded`'s default `onEmpty` behavior constructs the nested object even when every one of its columns is `null` (equivalent to `USE_EMPTY`) — forgetting to set `onEmpty = OnEmpty.USE_NULL` on an optional embedded value object means code has to separately check every one of its fields for `null` to determine "is this actually present," rather than doing one `shippingAddress == null` check.

- `@Embedded` flattens a value object's fields directly into the parent's own table row — no separate table, no join, unlike a `@MappedCollection` association.
- Reach for it for small, identity-less value objects (addresses, money amounts, date ranges) that always belong entirely to one parent row.
- Embedded fields are column-prefixed with the field's own name by default (`shippingAddress.street` → `shipping_address_street`).
- `onEmpty = OnEmpty.USE_NULL` reconstructs the whole nested object as `null` when every embedded column is empty, rather than an object with all-null fields — usually the more useful default for genuinely optional embedded objects.
