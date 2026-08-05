---
card: system-design
gi: 76
slug: document-stores
title: Document stores
---

## 1. What it is

A **document store** is a NoSQL database that stores data as self-contained **documents** — usually JSON-like structures — instead of rows split across normalized tables. Unlike a plain key-value store, a document store understands the structure inside each document, so it can query and index on fields *within* it, not just on the top-level key. MongoDB is the most common example.

## 2. Why & when

A document store is a good fit when your data naturally forms a single, self-contained tree — a blog post with its comments, a product with its variants and reviews, a user profile with nested address and preference fields — and you usually read and write that whole tree together, as one unit. It removes the need for joins across tables for that common case, at the cost of the same duplication risk denormalization always carries. Use it when your access pattern is "fetch or update this one entity and everything nested inside it," and reach for a relational database instead when your data has many cross-cutting relationships that do not fit neatly inside one document.

## 3. Core concept

**Embedding vs referencing:** a document can **embed** related data directly inside it (a blog post document with its comments as a nested array), or **reference** another document by ID (a product document storing a `categoryId` rather than the full category). Embedding avoids a second lookup but duplicates data if the same information appears in many documents; referencing avoids duplication but requires a second query (an application-level join) to resolve.

**Querying inside the document:** unlike a key-value store, a document store can filter and index on nested fields — `db.orders.find({"items.productId": "sku42"})` finds every order document containing that product anywhere in its nested `items` array, something a plain key-value store cannot do without scanning every value manually.

**No fixed schema across documents:** two documents in the same collection do not need identical fields — one order might have a `discountCode` field and another might not. This offers flexibility during development, but it also means the database itself does not enforce that every document has the shape your application code expects — that discipline shifts to the application (or an optional schema-validation feature some document stores provide).

## 4. Diagram

```
DOCUMENT STORE - a self-contained tree per document:

  { "_id": "order-1",
    "customerName": "Alice",              <- embedded: no join needed to show the name
    "items": [
      { "productId": "sku1", "qty": 2 },
      { "productId": "sku2", "qty": 1 }
    ],
    "categoryId": "electronics"            <- referenced: a separate lookup resolves the full category
  }

  QUERY: find orders containing productId "sku1"
      -> db.orders.find({ "items.productId": "sku1" })
      -> the store can index and search INSIDE the nested items array directly
```
*Caption: a document store queries inside nested structure directly; embedding trades duplication for fewer lookups, referencing trades an extra lookup for less duplication.*

## 5. Runnable example

**Level 1 — Basic.** Model documents as nested Java records, stored by ID like a document collection.

**Level 2 — Querying nested fields.** Search inside every document's nested array, mirroring a query on a nested field.

**Level 3 — Embedding vs referencing.** Compare an embedded field (no extra lookup) against a referenced ID (needs a second lookup to resolve).

```java
// DocumentStores.java
import java.util.*;

public class DocumentStores {

    record Item(String productId, int qty) {}
    record Category(String id, String name) {}
    record Order(String id, String customerName, List<Item> items, String categoryId) {}

    static final Map<String, Order> orders = new HashMap<>(); // the "collection"
    static final Map<String, Category> categories = new HashMap<>(); // a separate, referenced collection

    public static void main(String[] args) {
        categories.put("electronics", new Category("electronics", "Electronics"));

        orders.put("order-1", new Order("order-1", "Alice",
            List.of(new Item("sku1", 2), new Item("sku2", 1)), "electronics"));
        orders.put("order-2", new Order("order-2", "Bob",
            List.of(new Item("sku3", 1)), "electronics"));

        // Level 1: fetch the whole self-contained document by its key.
        Order fetched = orders.get("order-1");
        System.out.println("fetched order-1 (embedded customerName, no join needed): " + fetched.customerName());

        // Level 2: query INSIDE the nested items array - something a plain key-value store cannot do.
        System.out.println("orders containing productId 'sku1' (nested-field query):");
        for (Order o : orders.values()) {
            boolean hasIt = o.items().stream().anyMatch(i -> i.productId().equals("sku1"));
            if (hasIt) System.out.println("  " + o.id() + " (customer: " + o.customerName() + ")");
        }

        // Level 3: embedding (customerName, no lookup) vs referencing (categoryId, needs a lookup).
        System.out.println("embedded field, no extra lookup: " + fetched.customerName());
        Category resolvedCategory = categories.get(fetched.categoryId()); // the "join" a reference requires
        System.out.println("referenced field, resolved via a second lookup: " + resolvedCategory.name());
    }
}
```

**How to run:** save as `DocumentStores.java`, then run `java DocumentStores.java`.

## 6. Walkthrough

1. `orders.get("order-1")` fetches the entire nested `Order` document — including its embedded `items` list — in one lookup, mirroring how a document store returns a whole document from one `findById`-style query.
2. `fetched.customerName()` reads directly, with no additional lookup, because `customerName` is embedded directly in the order document.
3. The loop over `orders.values()`, checking `o.items().stream().anyMatch(...)`, mirrors a document store's ability to query inside a nested array field — something the key-value store example in the previous tutorial had to do manually because its store gave no such support, but here it is the store's actual supported capability being modeled directly.
4. Only `order-1` contains `productId "sku1"`, so it is the sole match printed.
5. `categories.get(fetched.categoryId())` performs a second lookup to resolve the referenced category — modeling the application-level "join" a document store requires whenever data is referenced by ID instead of embedded directly.

## 7. Gotchas & takeaways

> Gotcha: because a document store enforces no schema across documents in the same collection, a bug that writes a document missing an expected field (or with the wrong type) does not fail at write time — it silently produces documents your application code may not handle correctly until it actually reads one and crashes or misbehaves.

- Document stores let you query inside nested structure directly, closing the biggest gap a plain key-value store has.
- The embed-vs-reference choice is the document-store version of denormalize-vs-normalize: embedding is faster to read but risks duplication, referencing avoids duplication but costs an extra lookup.
- Related concepts: [Key-value stores](0075-key-value-stores.md) (the simpler model this extends with nested-field querying), [Access-pattern-first data modeling](0082-access-pattern-first-data-modeling.md) (deciding what to embed versus reference, based on how the data is actually read).
