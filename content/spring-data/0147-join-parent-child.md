---
card: spring-data
gi: 147
slug: join-parent-child
title: "Join/parent-child"
---

## 1. What it is

Elasticsearch's **join** field type models a parent-child relationship *within a single index* — documents are tagged as either a `parent` (say, a `product`) or a `child` (say, an `order` for that product) of a named relation, and both live in the same index and, crucially, the same shard, which is what makes efficient parent-child queries possible at all.

```java
@Document(indexName = "products_and_orders")
class ProductOrRelated {
    @Id String id;
    @JoinTypeRelations(relations = {
        @JoinTypeRelation(parent = "product", children = "order")
    })
    JoinField<String> relation; // holds either "product" or {"order", parentId}
}
```

## 2. Why & when

Elasticsearch has no native `JOIN` the way a relational database does — every document is independent, and a search can't reach across two unrelated documents to combine their fields the way a SQL join can. The `join` field type is the (deliberately limited) mechanism Elasticsearch offers instead: it lets you query for parents based on conditions on their children, or children based on conditions on their parent, as long as both are declared as part of the same join relation and live in the same index.

Reach for `join`/parent-child modeling specifically when:

- You have a genuine one-to-many relationship where the "many" side is updated far more frequently than the "one" side (comments on a post, orders for a product) — updating a child document doesn't require reindexing the parent or any sibling children, unlike a nested object (a later, related concept) where the whole parent document must be reindexed for any change to a nested item.
- You need to query "find parents that have at least one child matching X" or "find children whose parent matches Y" — `has_child`/`has_parent` queries express exactly this.
- You've confirmed embedding the related data directly into one document (Elasticsearch's usual preferred approach, mirroring the "prefer embedding" guidance from the earlier MongoDB cards) doesn't fit your update pattern.

This is a specialized, relatively heavyweight feature — reach for it only after confirming a simpler denormalized or nested-object model doesn't fit, since parent-child queries carry real performance overhead compared to a search against a single flat document.

## 3. Core concept

```
 Same index, same shard (required for join queries to work at all):

   { "id": "product-1", "relation": "product" }                              <- PARENT document
   { "id": "order-1",   "relation": {"name": "order", "parent": "product-1"} } <- CHILD document
   { "id": "order-2",   "relation": {"name": "order", "parent": "product-1"} } <- CHILD document

 has_child query: "find products that have at least one order with status=SHIPPED"
        -> Elasticsearch checks child documents, returns their PARENT products

 has_parent query: "find orders whose product is in category=Electronics"
        -> Elasticsearch checks parent documents, returns their matching CHILD orders
```

Parent and child documents are ordinary documents in the same index, linked only by the `join` field's explicit parent reference — there's no separate relationship table or foreign key the way a relational database would model this.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A has_child query examines child order documents and returns the matching parent product documents">
  <rect x="20" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">product-1 (PARENT)</text>

  <rect x="240" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">order-1 (CHILD, status=PENDING)</text>

  <rect x="440" y="20" width="180" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">order-2 (CHILD, status=SHIPPED)</text>

  <line x1="200" y1="42" x2="235" y2="42" stroke="#8b949e" stroke-width="1.3"/>
  <line x1="200" y1="42" x2="435" y2="42" stroke="#8b949e" stroke-width="1.3"/>

  <text x="320" y="110" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">has_child(status=SHIPPED) matches order-2, so it returns product-1</text>
  <line x1="530" y1="65" x2="130" y2="105" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a1)"/>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

A `has_child` query examines the child documents but returns their matching parents — the query traverses the relationship in the opposite direction from what it filters on.

## 5. Runnable example

The scenario: modeling products and their orders as parent-child documents in one index, evolving from a basic parent-child data model, to a `has_child`-style query finding parents with a matching child, to a `has_parent`-style query finding children whose parent matches a condition.

### Level 1 — Basic

Model parent and child documents co-located in one index, linked by an explicit parent reference — the `join` field's core structure.

```java
import java.util.*;

public class JoinParentChildLevel1 {
    public static void main(String[] args) {
        List<IndexedDocument> index = List.of(
            IndexedDocument.product("product-1", "Electronics"),
            IndexedDocument.order("order-1", "product-1", "PENDING"),
            IndexedDocument.order("order-2", "product-1", "SHIPPED")
        );

        for (IndexedDocument d : index) {
            if (d.relationType.equals("product")) System.out.println(d.id + ": PARENT (product, category=" + d.category + ")");
            else System.out.println(d.id + ": CHILD (order, parent=" + d.parentId + ", status=" + d.status + ")");
        }
    }
}

// Stands in for a document with a @JoinTypeRelations join field -- "relation" is either "product" (a parent)
// or {"order", parentId} (a child), all stored in the SAME index.
class IndexedDocument {
    String id;
    String relationType; // "product" or "order"
    String parentId;     // null for a parent document, set for a child
    String status;        // only meaningful for "order" documents
    String category;      // only meaningful for "product" documents

    static IndexedDocument product(String id, String category) {
        IndexedDocument d = new IndexedDocument(); d.id = id; d.relationType = "product"; d.category = category; return d;
    }
    static IndexedDocument order(String id, String parentId, String status) {
        IndexedDocument d = new IndexedDocument(); d.id = id; d.relationType = "order"; d.parentId = parentId; d.status = status; return d;
    }
}
```

How to run: `java JoinParentChildLevel1.java`

`index` models all three documents living in the *same* logical index, distinguished only by their `relationType` and (for children) a `parentId` field — exactly what a real `join` field encodes internally: `"relation": "product"` for a parent, `"relation": {"name": "order", "parent": "product-1"}` for a child.

### Level 2 — Intermediate

Implement a `has_child`-style query: find parent documents that have at least one child matching a condition.

```java
import java.util.*;
import java.util.stream.*;

public class JoinParentChildLevel2 {
    public static void main(String[] args) {
        List<IndexedDocument> index = List.of(
            IndexedDocument.product("product-1", "Electronics"),
            IndexedDocument.product("product-2", "Books"),
            IndexedDocument.order("order-1", "product-1", "PENDING"),
            IndexedDocument.order("order-2", "product-1", "SHIPPED"),
            IndexedDocument.order("order-3", "product-2", "PENDING") // product-2 has NO shipped orders
        );

        // Mirrors: hasChildQuery("order", termQuery("status", "SHIPPED"))
        List<IndexedDocument> productsWithShippedOrders = hasChild(index, "SHIPPED");
        System.out.println("Products with at least one SHIPPED order: "
            + productsWithShippedOrders.stream().map(d -> d.id).collect(Collectors.toList()));
    }

    static List<IndexedDocument> hasChild(List<IndexedDocument> index, String childStatus) {
        Set<String> parentIdsWithMatchingChild = index.stream()
            .filter(d -> "order".equals(d.relationType) && childStatus.equals(d.status))
            .map(d -> d.parentId)
            .collect(Collectors.toSet());
        return index.stream()
            .filter(d -> "product".equals(d.relationType) && parentIdsWithMatchingChild.contains(d.id))
            .collect(Collectors.toList());
    }
}

class IndexedDocument {
    String id; String relationType; String parentId; String status; String category;
    static IndexedDocument product(String id, String category) { IndexedDocument d = new IndexedDocument(); d.id = id; d.relationType = "product"; d.category = category; return d; }
    static IndexedDocument order(String id, String parentId, String status) { IndexedDocument d = new IndexedDocument(); d.id = id; d.relationType = "order"; d.parentId = parentId; d.status = status; return d; }
}
```

How to run: `java JoinParentChildLevel2.java`

`hasChild` first finds every distinct `parentId` belonging to a matching child (`status = "SHIPPED"`), then returns the parent documents whose id is in that set — mirroring `QueryBuilders.hasChildQuery("order", termQuery("status", "SHIPPED"), ScoreMode.None)`. `product-1` (which has a `SHIPPED` order) is returned; `product-2` (whose only order is `PENDING`) is correctly excluded, even though it's also a valid parent document.

### Level 3 — Advanced

Implement a `has_parent`-style query: find child documents whose parent matches a condition — the reverse direction from `has_child`.

```java
import java.util.*;
import java.util.stream.*;

public class JoinParentChildLevel3 {
    public static void main(String[] args) {
        List<IndexedDocument> index = List.of(
            IndexedDocument.product("product-1", "Electronics"),
            IndexedDocument.product("product-2", "Books"),
            IndexedDocument.order("order-1", "product-1", "PENDING"), // parent is Electronics
            IndexedDocument.order("order-2", "product-1", "SHIPPED"), // parent is Electronics
            IndexedDocument.order("order-3", "product-2", "PENDING")  // parent is Books
        );

        // Mirrors: hasParentQuery("product", termQuery("category", "Electronics"), false)
        List<IndexedDocument> ordersForElectronics = hasParent(index, "Electronics");
        System.out.println("Orders whose product is in category=Electronics: "
            + ordersForElectronics.stream().map(d -> d.id).collect(Collectors.toList()));
    }

    static List<IndexedDocument> hasParent(List<IndexedDocument> index, String parentCategory) {
        Set<String> matchingParentIds = index.stream()
            .filter(d -> "product".equals(d.relationType) && parentCategory.equals(d.category))
            .map(d -> d.id)
            .collect(Collectors.toSet());
        return index.stream()
            .filter(d -> "order".equals(d.relationType) && matchingParentIds.contains(d.parentId))
            .collect(Collectors.toList());
    }
}

class IndexedDocument {
    String id; String relationType; String parentId; String status; String category;
    static IndexedDocument product(String id, String category) { IndexedDocument d = new IndexedDocument(); d.id = id; d.relationType = "product"; d.category = category; return d; }
    static IndexedDocument order(String id, String parentId, String status) { IndexedDocument d = new IndexedDocument(); d.id = id; d.relationType = "order"; d.parentId = parentId; d.status = status; return d; }
}
```

How to run: `java JoinParentChildLevel3.java`

`hasParent` runs the opposite direction from `hasChild`: it first finds every parent id matching the condition (`category = "Electronics"`), then returns the child documents pointing at one of those parents — mirroring `QueryBuilders.hasParentQuery("product", termQuery("category", "Electronics"), false)`. Both `order-1` and `order-2` (children of `product-1`, which is `Electronics`) are returned; `order-3` (a child of `product-2`, which is `Books`) is excluded.

## 6. Walkthrough

Execution starts in `main` for Level 3. Five documents are defined: two products (`product-1` in `Electronics`, `product-2` in `Books`) and three orders, each pointing at one of those products via `parentId`.

`hasParent(index, "Electronics")` first filters `index` to documents where `relationType.equals("product")` and `category.equals("Electronics")` — only `product-1` matches, so `matchingParentIds` becomes `{"product-1"}`. It then filters `index` again, this time to documents where `relationType.equals("order")` and `parentId` is in `matchingParentIds` — `order-1` and `order-2` both have `parentId = "product-1"`, which is in the set, so both are included; `order-3` has `parentId = "product-2"`, which is not in the set, so it's excluded.

```
Orders whose product is in category=Electronics: [order-1, order-2]
```

In real Elasticsearch, `has_parent` and `has_child` queries execute this exact two-step logic entirely server-side, using the join field's internal indexing structure to make the lookup efficient — but only because parent and child documents are required to live on the *same shard* (guaranteed by routing children to their parent's shard automatically). This is precisely why `join` relationships are confined to a single index: the join can only be resolved efficiently when Elasticsearch can guarantee both sides of the relationship are co-located, unlike a relational database's `JOIN`, which can freely combine rows from anywhere in the database.

## 7. Gotchas & takeaways

> Gotcha: every child document must specify its parent's id at index time (used for routing, ensuring the child lands on the same shard as its parent) — and that parent-child link is effectively immutable; changing which parent a child belongs to requires deleting and re-indexing the child document, not an in-place update.

> Gotcha: `has_child`/`has_parent` queries are meaningfully more expensive than an equivalent query against a single flat (denormalized) document, because Elasticsearch has to perform the join-like traversal at query time — for read-heavy access patterns where the parent-child structure is mostly stable, denormalizing the needed parent fields directly onto each child document (accepting some duplication) is often faster in practice, even though it means updating multiple documents if a parent field changes.

- The `join` field type models one-to-many parent-child relationships within a single index, with parent and child documents required to live on the same shard.
- `has_child` queries filter on child document fields but return matching parent documents; `has_parent` queries filter on parent fields but return matching child documents — the two directions are not interchangeable.
- Parent-child modeling fits best when children are updated far more often than parents, since updating a child never requires reindexing the parent or sibling children.
- Parent-child queries carry real performance overhead compared to querying a single flat document — confirm a denormalized or nested-object model doesn't fit before reaching for this.
