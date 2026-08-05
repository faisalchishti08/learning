---
card: system-design
gi: 63
slug: normalization-1nf3nf-bcnf
title: "Normalization (1NF–3NF, BCNF)"
---

## 1. What it is

**Normalization** is a set of rules for organizing tables so that each fact is stored exactly once, avoiding duplication and the inconsistency it causes. It is applied as a series of increasingly strict forms: **1NF** (First Normal Form), **2NF**, **3NF**, and **BCNF** (Boyce-Codd Normal Form), each fixing a specific kind of redundancy the previous form still allows.

## 2. Why & when

An unnormalized table that repeats the same fact in many rows (a customer's address copied into every one of their orders) risks **update anomalies**: change the address in one row and forget another, and the data now contradicts itself with no way to tell which copy is correct. Normalization removes this risk by storing each fact in exactly one place. Apply it when designing a schema for data you will update; some denormalization (the opposite trade, covered next) is later applied deliberately for read performance once the normalized design is understood.

## 3. Core concept

**1NF — atomic values, no repeating groups:** every column holds a single, indivisible value; a column like `phone_numbers = "555-1111, 555-2222"` violates 1NF because it packs multiple values into one field, making them impossible to query or update individually. The fix is a separate table, one row per phone number.

**2NF — no partial dependency on a composite key:** applies to tables with a multi-column primary key. If a column depends on only *part* of that composite key rather than the whole thing, it violates 2NF. Example: an `order_items` table keyed on `(order_id, product_id)` should not also store `product_name`, because `product_name` depends only on `product_id`, not on the full key — it belongs in a separate `products` table.

**3NF — no transitive dependency:** a non-key column should not depend on another non-key column. Example: if `orders` stores both `customer_id` and `customer_city`, and `customer_city` really depends on `customer_id` (not on the order itself), that is a transitive dependency — `customer_city` belongs in the `customers` table, reached via `customer_id`.

**BCNF — a stricter version of 3NF:** every determinant (a column, or set of columns, that determines another column's value) must be a candidate key. BCNF catches a narrow class of anomalies 3NF can still miss, mainly in tables with multiple overlapping candidate keys — rare in practice, but the logical end of this progression.

## 4. Diagram

```
UNNORMALIZED (violates 1NF - repeating group):
  orders: | id | customer | phones              |
          | 1  | Alice    | 555-1111, 555-2222  |   <- multiple values in one column

1NF fix (atomic values, separate table):
  orders: | id | customer_id |      customer_phones: | customer_id | phone     |
          | 1  | 1           |                        | 1           | 555-1111  |
                                                        | 1           | 555-2222  |

3NF fix (remove transitive dependency: customer_city depends on customer, not the order):
  orders: | id | customer_id |     customers: | id | name  | city    |
          | 1  | 1           |                 | 1  | Alice | Chicago |
  (customer_city REMOVED from orders - looked up via customer_id instead)
```
*Caption: each normal form removes one specific way the same fact could end up stored, and later contradict itself, in more than one place.*

## 5. Runnable example

**Level 1 — Basic.** Model an unnormalized table (repeating group) and show the update-anomaly risk directly.

**Level 2 — 1NF fix.** Split the repeating group into a separate table.

**Level 3 — 3NF fix.** Remove a transitive dependency (customer city stored redundantly on every order) into its own table, and show updating it once fixes every order at once.

```java
// Normalization.java
import java.util.*;

public class Normalization {

    // Level 1: UNNORMALIZED - city is duplicated on every order (transitive dependency),
    // and it is easy to update one row but forget another.
    record UnnormalizedOrder(int id, String customerName, String customerCity) {}

    // Level 3: NORMALIZED (3NF) - city lives in exactly one place: the customers table.
    record Customer(int id, String name, String city) {}
    record NormalizedOrder(int id, int customerId) {}

    public static void main(String[] args) {
        // Level 1: unnormalized data, city repeated across two orders for the same customer.
        List<UnnormalizedOrder> unnormalized = new ArrayList<>(List.of(
            new UnnormalizedOrder(1, "Alice", "Chicago"),
            new UnnormalizedOrder(2, "Alice", "Chicago") // same fact, stored a second time
        ));

        // Simulate an update anomaly: Alice moves to Denver, but only order 1 gets updated.
        unnormalized.set(0, new UnnormalizedOrder(1, "Alice", "Denver"));
        System.out.println("UNNORMALIZED after updating only order 1:");
        for (UnnormalizedOrder o : unnormalized) {
            System.out.println("  order " + o.id() + ": " + o.customerName() + " in " + o.customerCity());
        }
        System.out.println("  -> contradiction: same customer, two different cities on file");

        // Level 3: normalized - city stored once, on the customer, referenced by orders.
        Map<Integer, Customer> customers = new HashMap<>();
        customers.put(1, new Customer(1, "Alice", "Chicago"));
        List<NormalizedOrder> orders = List.of(
            new NormalizedOrder(1, 1),
            new NormalizedOrder(2, 1)
        );

        // Update the city ONCE, on the customer record.
        customers.put(1, new Customer(1, "Alice", "Denver"));

        System.out.println("NORMALIZED after updating the customer once:");
        for (NormalizedOrder o : orders) {
            Customer c = customers.get(o.customerId());
            System.out.println("  order " + o.id() + ": " + c.name() + " in " + c.city());
        }
        System.out.println("  -> both orders agree automatically: the fact only exists in one place");
    }
}
```

**How to run:** save as `Normalization.java`, then run `java Normalization.java`.

## 6. Walkthrough

1. `unnormalized` stores `customerCity` directly on each order — the same fact ("Alice lives in Chicago") duplicated across both of her orders.
2. Updating only `unnormalized.get(0)` to `"Denver"` leaves order 2 still saying `"Chicago"` — printing both rows shows a direct contradiction: the same customer now has two different cities on file, purely because the fact was stored in two places.
3. In the normalized version, `customers` holds the city exactly once, keyed by `customerId`; `orders` only stores a reference (`customerId`), never the city itself.
4. Updating `customers.put(1, new Customer(1, "Alice", "Denver"))` changes the fact in its one location.
5. Looking up the city through `customers.get(o.customerId())` for both orders now yields `"Denver"` for both — consistency is automatic because there was never a second copy that could disagree.

## 7. Gotchas & takeaways

> Gotcha: over-normalizing (splitting data into many small tables even when it is rarely updated and always read together) can hurt read performance, since every query now needs more joins to reassemble the full picture — this is exactly the tension denormalization, covered next, deliberately trades back.

- Every normal form fixes one specific kind of duplication: 1NF fixes multi-valued columns, 2NF fixes partial key dependencies, 3NF and BCNF fix transitive and near-transitive dependencies.
- Normalization protects update consistency; it does not, by itself, optimize read speed — that is a separate, sometimes opposing, design goal.
- Related concepts: [Denormalization for read performance](0064-denormalization-for-read-performance.md) (the deliberate, informed trade-off in the other direction), [Tables, rows, keys & relationships](0062-tables-rows-keys-relationships.md) (the foundational structure normalization organizes).
