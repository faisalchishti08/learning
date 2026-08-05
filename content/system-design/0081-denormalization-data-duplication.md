---
card: system-design
gi: 81
slug: denormalization-data-duplication
title: "Denormalization & data duplication"
---

## 1. What it is

In NoSQL databases, **denormalization** is not an occasional optimization applied on top of a normalized design (as it is relationally) — it is often the default, expected way to model data. **Data duplication** — copying the same fact into multiple documents or rows so each one can be read independently, without a join — is the normal cost of designing for a NoSQL database's specific access patterns.

## 2. Why & when

Most NoSQL databases either cannot join across documents/rows efficiently (document stores) or cannot join across partitions at all (wide-column stores). Given that constraint, the only way to answer a query in one fast operation is to have already put every piece of data that query needs into one place — which usually means duplicating some of it. This is not a shortcut or a compromise the way relational denormalization can feel; it is the standard, correct way to model data once you accept the store's constraints. Apply it deliberately, guided by exactly which queries you need to serve fast (the access-pattern-first approach, covered next).

## 3. Core concept

**Why relational denormalization and NoSQL denormalization differ in spirit:** relationally, you start normalized (the "correct," minimal-duplication baseline) and denormalize specific hot paths as a deliberate, measured trade-off. In a document or wide-column store, there often is no efficient join to fall back on at all — so a "normalized" design (splitting an order and its customer into two separate documents that must be joined by two round trips) may not just be slower, it may not be a realistically supported query shape at the store's designed scale.

**Duplicating for read speed, accepting the write cost:** if a product's name is duplicated into every order document that references it (so viewing an order needs zero extra lookups), a later product rename must explicitly update every order document that duplicated the old name — or, often, the duplication is deliberately treated as a historical snapshot (the name *as it was* at order time), which sidesteps the sync problem entirely by redefining what "correct" means for that copy.

**Accepting some staleness as a designed trade, not a bug:** many NoSQL systems accept that a duplicated copy may lag behind the source of truth for a short time (propagated via an event, a background job, or the application's own write path) — this is the same staleness trade-off covered earlier in this section, now applied by default rather than as a special case.

## 4. Diagram

```
"NORMALIZED" shape (requires 2 lookups, no efficient join available):
  orders/order-1: { customerId: "cust-42", items: [...] }
  customers/cust-42: { name: "Alice", tier: "gold" }
  displaying an order -> 2 separate reads, glued together by the APPLICATION

DENORMALIZED (duplicated) shape (1 lookup, the normal NoSQL default):
  orders/order-1: {
    customerId: "cust-42",
    customerName: "Alice",   <- DUPLICATED from the customer document
    customerTier: "gold",    <- DUPLICATED from the customer document
    items: [...]
  }
  displaying an order -> 1 read, everything needed is already there
```
*Caption: duplicating the customer's name and tier directly into every order removes a second lookup — the default NoSQL trade, not an unusual exception.*

## 5. Runnable example

**Level 1 — Basic.** A "normalized" two-document model requiring two lookups to display an order.

**Level 2 — Denormalized model.** The same data duplicated into the order document, answerable in one lookup.

**Level 3 — Keeping duplicates in sync.** Propagate a customer update to every order that duplicated their data.

```java
// DenormalizationDataDuplication.java
import java.util.*;

public class DenormalizationDataDuplication {

    record Customer(String id, String name, String tier) {}
    record NormalizedOrder(String id, String customerId, List<String> items) {}
    record DenormalizedOrder(String id, String customerId, String customerName, String customerTier, List<String> items) {}

    static final Map<String, Customer> customers = new HashMap<>();
    static final Map<String, NormalizedOrder> normalizedOrders = new HashMap<>();
    static final Map<String, DenormalizedOrder> denormalizedOrders = new HashMap<>();

    public static void main(String[] args) {
        customers.put("cust-42", new Customer("cust-42", "Alice", "gold"));

        // Level 1: "normalized" shape - the order only references the customer by ID.
        normalizedOrders.put("order-1", new NormalizedOrder("order-1", "cust-42", List.of("Pen", "Book")));

        System.out.println("displaying order-1, NORMALIZED shape (2 separate lookups needed):");
        NormalizedOrder nOrder = normalizedOrders.get("order-1"); // lookup 1
        Customer nCustomer = customers.get(nOrder.customerId());   // lookup 2, glued together by the application
        System.out.println("  " + nCustomer.name() + " (" + nCustomer.tier() + "): " + nOrder.items());

        // Level 2: denormalized shape - the customer's name and tier are duplicated directly into the order.
        denormalizedOrders.put("order-1", new DenormalizedOrder("order-1", "cust-42", "Alice", "gold", List.of("Pen", "Book")));

        System.out.println("displaying order-1, DENORMALIZED shape (1 lookup, everything already present):");
        DenormalizedOrder dOrder = denormalizedOrders.get("order-1"); // lookup 1, done
        System.out.println("  " + dOrder.customerName() + " (" + dOrder.customerTier() + "): " + dOrder.items());

        // Level 3: customer upgrades to "platinum" - every duplicated copy must be explicitly updated.
        customers.put("cust-42", new Customer("cust-42", "Alice", "platinum"));
        System.out.println("customer upgraded to platinum in the customers store.");
        System.out.println("denormalized order-1 tier BEFORE propagation (still stale): " + denormalizedOrders.get("order-1").customerTier());

        // Propagate the change to every order that duplicated this customer's data.
        for (Map.Entry<String, DenormalizedOrder> entry : denormalizedOrders.entrySet()) {
            DenormalizedOrder o = entry.getValue();
            if (o.customerId().equals("cust-42")) {
                entry.setValue(new DenormalizedOrder(o.id(), o.customerId(), o.customerName(), "platinum", o.items()));
            }
        }
        System.out.println("denormalized order-1 tier AFTER propagation: " + denormalizedOrders.get("order-1").customerTier());
    }
}
```

**How to run:** save as `DenormalizationDataDuplication.java`, then run `java DenormalizationDataDuplication.java`.

## 6. Walkthrough

1. Displaying the normalized order requires two separate lookups — `normalizedOrders.get("order-1")` for the order, then `customers.get(nOrder.customerId())` for the customer — with the application itself gluing the two results together.
2. Displaying the denormalized order requires just one lookup, `denormalizedOrders.get("order-1")`, which already carries `customerName` and `customerTier` duplicated directly into it.
3. `customers.put("cust-42", new Customer(..., "platinum"))` updates the one source-of-truth customer record.
4. The denormalized order's `customerTier` is checked immediately after and still prints `"gold"` — the duplicated copy has not been told about the change yet, exactly the staleness risk denormalization accepts.
5. The propagation loop explicitly finds every denormalized order referencing `"cust-42"` and updates its duplicated `customerTier` field; the final read confirms it now correctly shows `"platinum"` — demonstrating that keeping duplicated data correct requires an explicit, deliberate synchronization step, not something the store handles automatically.

## 7. Gotchas & takeaways

> Gotcha: forgetting to propagate an update to even one duplicated copy leaves that copy permanently stale until the next explicit sync — in a NoSQL system with many duplicated locations for the same fact, this risk multiplies with every extra place the data was copied into.

- In NoSQL modeling, denormalization is usually the default design, not an occasional optimization — driven directly by the store's lack of an efficient general-purpose join.
- Every duplicated field needs an explicit, deliberate update path; the store will not keep duplicates in sync automatically the way an ACID transaction keeps a normalized relational schema consistent.
- Related concepts: [Denormalization for read performance](0064-denormalization-for-read-performance.md) (the relational version of this same trade-off), [Access-pattern-first data modeling](0082-access-pattern-first-data-modeling.md) (the discipline that decides exactly what to duplicate and where).
