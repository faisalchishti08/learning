---
card: spring-data
gi: 103
slug: document-mapping-document-id-field-indexed
title: "Document mapping (@Document, @Id, @Field, @Indexed)"
---

## 1. What it is

`@Document` marks a class as mapping to a MongoDB collection (the document-store analogue of `@Table`), `@Id` marks the identifier field (mapped to MongoDB's special `_id` field), `@Field` overrides a single field's stored name (like `@Column`), and `@Indexed` declares that MongoDB should maintain an index on that field for faster queries.

```java
@Document("orders")
class Order {
    @Id String id;                       // maps to MongoDB's special _id field
    @Field("order_status") String status; // overrides the stored field name
    @Indexed String customerEmail;         // MongoDB maintains an index on this field
}
```

## 2. Why & when

Every relational card's mapping conventions (table/column naming, `@Id`/`@Table`/`@Column`) have a direct document-store counterpart here — but MongoDB's `_id` field is special (every document has exactly one, and it's the default query/sort key), and MongoDB's schemaless nature means indexes matter even more for query performance, since there's no query planner falling back on a fixed schema's assumptions the way a relational database's does.

Reach for these annotations specifically when:

- Declaring any MongoDB-backed entity at all — `@Document` is the minimum needed to tell Spring Data MongoDB which collection an entity maps to (though it can be inferred from the class name by convention, exactly like `@Table`).
- The MongoDB field name needs to differ from the Java field name (matching an existing collection's naming, or intentionally shortening a frequently-repeated field name to reduce document size) — `@Field` handles this per-field, like `@Column` for relational entities.
- A field is frequently queried or sorted on and doesn't already benefit from the automatic `_id` index — `@Indexed` tells MongoDB to build and maintain a real index, turning an O(n) collection scan into an O(log n) index lookup for queries filtering on that field.

## 3. Core concept

```
 @Document("orders")             -- maps this class to the "orders" collection
 class Order {
     @Id String id;                -- maps to MongoDB's built-in _id field, auto-indexed by default
     @Field("order_status") String status;  -- stored as "order_status" in the document, not "status"
     @Indexed String customerEmail;           -- MongoDB builds/maintains an index on this field
 }

 Resulting document shape:
   { "_id": "...", "order_status": "PENDING", "customerEmail": "ada@example.com" }
```

`@Id` always maps to MongoDB's special `_id` field regardless of the Java field's name; `@Field` controls every other field's stored name; `@Indexed` requests a real database index for query performance.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="An Order class maps its fields to a MongoDB document, with id going to the special underscore-id field and customerEmail gaining an index">
  <rect x="20" y="15" width="260" height="120" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Document("orders") class Order</text>
  <text x="35" y="60" fill="#8b949e" font-size="8.5" font-family="monospace">@Id String id</text>
  <text x="35" y="80" fill="#8b949e" font-size="8.5" font-family="monospace">@Field("order_status") status</text>
  <text x="35" y="100" fill="#8b949e" font-size="8.5" font-family="monospace">@Indexed customerEmail</text>

  <rect x="340" y="15" width="280" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="35" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">orders collection (document)</text>
  <text x="355" y="60" fill="#8b949e" font-size="8.5" font-family="monospace">_id: "..."</text>
  <text x="355" y="80" fill="#8b949e" font-size="8.5" font-family="monospace">order_status: "PENDING"</text>
  <text x="355" y="100" fill="#8b949e" font-size="8.5" font-family="monospace">customerEmail: "ada@..." (indexed)</text>

  <line x1="280" y1="65" x2="335" y2="65" stroke="#8b949e" stroke-width="1.3" marker-end="url(#dm)"/>
  <defs><marker id="dm" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`@Id` always becomes `_id`; other fields keep their name unless `@Field` overrides it; `@Indexed` fields get a real database index behind the scenes.

## 5. Runnable example

The scenario: mapping an order document, evolving from computing the default document shape, to overriding a field name and marking another as indexed, to demonstrating the query-performance difference an index makes at scale.

### Level 1 — Basic

Model the default document mapping: field names carry over unchanged except for the special `_id`.

```java
import java.util.*;

public class DocMappingLevel1 {
    // @Document("orders") class Order { @Id String id; String status; double total; }
    record FieldMapping(String javaField, boolean isId) {
        String documentFieldName() { return isId ? "_id" : javaField; }
    }

    public static void main(String[] args) {
        List<FieldMapping> fields = List.of(
            new FieldMapping("id", true),
            new FieldMapping("status", false),
            new FieldMapping("total", false)
        );
        for (FieldMapping f : fields) System.out.println(f.javaField() + " -> " + f.documentFieldName());
    }
}
```

How to run: `java DocMappingLevel1.java`

`id` maps to `_id` (MongoDB's special identifier field) while `status`/`total` keep their Java names unchanged — the simplest possible document mapping, requiring only `@Id` to be explicit about which field is the identifier.

### Level 2 — Intermediate

Add a `@Field` override and an `@Indexed` marker, and build the resulting document shape.

```java
import java.util.*;

public class DocMappingLevel2 {
    record FieldMapping(String javaField, boolean isId, String fieldOverride, boolean indexed) {
        String documentFieldName() {
            if (isId) return "_id";
            return fieldOverride != null ? fieldOverride : javaField;
        }
    }

    public static void main(String[] args) {
        // @Document("orders") class Order {
        //     @Id String id;
        //     @Field("order_status") String status;
        //     @Indexed String customerEmail;
        // }
        List<FieldMapping> fields = List.of(
            new FieldMapping("id", true, null, false),
            new FieldMapping("status", false, "order_status", false),
            new FieldMapping("customerEmail", false, null, true)
        );

        Map<String, Object> document = new LinkedHashMap<>();
        document.put(fields.get(0).documentFieldName(), "abc123");
        document.put(fields.get(1).documentFieldName(), "PENDING");
        document.put(fields.get(2).documentFieldName(), "ada@example.com");

        System.out.println("Document: " + document);
        for (FieldMapping f : fields) {
            if (f.indexed()) System.out.println("Index created on: " + f.documentFieldName());
        }
    }
}
```

How to run: `java DocMappingLevel2.java`

The resulting document uses `order_status` (not `status`) as its key, per the `@Field` override, and a separate index-creation message confirms `customerEmail` is flagged for indexing — both annotations act independently on their own field, composing into the final document shape and the collection's index set.

### Level 3 — Advanced

Demonstrate the query-performance difference an index makes: simulate a large "collection" and compare a full scan (unindexed field) against an index-assisted lookup (indexed field).

```java
import java.util.*;
import java.util.stream.*;

class OrderDoc { String id; String status; String customerEmail; OrderDoc(String id, String status, String email) { this.id = id; this.status = status; this.customerEmail = email; } }

public class DocMappingLevel3 {
    // Unindexed lookup: MongoDB must scan every document to find matches (a "collection scan").
    static List<OrderDoc> findByStatusUnindexed(List<OrderDoc> collection, String status) {
        int scanned = 0;
        List<OrderDoc> results = new ArrayList<>();
        for (OrderDoc doc : collection) {
            scanned++; // every single document is examined
            if (doc.status.equals(status)) results.add(doc);
        }
        System.out.println("  Unindexed scan: examined " + scanned + " documents");
        return results;
    }

    // Indexed lookup: simulates an index (a sorted map from value -> matching documents) letting
    // MongoDB jump straight to matches without scanning the whole collection.
    static List<OrderDoc> findByEmailIndexed(Map<String, List<OrderDoc>> emailIndex, String email) {
        List<OrderDoc> results = emailIndex.getOrDefault(email, List.of());
        System.out.println("  Indexed lookup: examined only the matching index bucket (" + results.size() + " document(s))");
        return results;
    }

    public static void main(String[] args) {
        List<OrderDoc> collection = IntStream.rangeClosed(1, 1000)
            .mapToObj(i -> new OrderDoc("id" + i, i % 2 == 0 ? "SHIPPED" : "PENDING", "customer" + i + "@example.com"))
            .collect(Collectors.toList());

        // Build the index MongoDB would maintain automatically for an @Indexed field.
        Map<String, List<OrderDoc>> emailIndex = collection.stream()
            .collect(Collectors.groupingBy(d -> d.customerEmail));

        List<OrderDoc> shipped = findByStatusUnindexed(collection, "SHIPPED"); // status has NO index
        System.out.println("Found " + shipped.size() + " shipped orders (had to scan everything)");

        List<OrderDoc> byEmail = findByEmailIndexed(emailIndex, "customer42@example.com"); // customerEmail IS indexed
        System.out.println("Found " + byEmail.size() + " order(s) by exact email (jumped straight there)");
    }
}
```

How to run: `java DocMappingLevel3.java`

`findByStatusUnindexed` examines all 1000 documents (`status` has no index in this model), while `findByEmailIndexed` goes directly to the matching bucket in a pre-built index structure — this mirrors the real difference between a MongoDB collection scan (linear in collection size) and an index-assisted query (roughly logarithmic, or a direct lookup for exact-match queries), which is exactly the performance benefit `@Indexed` provides for frequently-filtered fields.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `collection` is built with 1000 `OrderDoc` entries, alternating `SHIPPED`/`PENDING` status and each with a unique `customerEmail`. `emailIndex` is then built by grouping all 1000 documents by their `customerEmail` — since every email is unique in this dataset, this produces 1000 single-entry buckets, standing in for the sorted index structure MongoDB maintains internally for an `@Indexed` field.

`findByStatusUnindexed(collection, "SHIPPED")` runs next: the loop iterates over all 1000 documents one by one, incrementing `scanned` on every single one regardless of whether it matches, and only appending to `results` when `doc.status.equals("SHIPPED")` is true. After the loop, `scanned` is `1000` (every document was examined) and `results` contains the 500 `SHIPPED` orders (every even-indexed one). "Unindexed scan: examined 1000 documents" is printed.

`findByEmailIndexed(emailIndex, "customer42@example.com")` runs last: instead of iterating over the whole collection, it directly looks up `"customer42@example.com"` as a key in `emailIndex`, retrieving its single-entry bucket immediately — no scanning of the other 999 documents happens at all. "Indexed lookup: examined only the matching index bucket (1 document(s))" is printed.

```
findByStatusUnindexed("SHIPPED"):   scans all 1000 docs one by one -> finds 500 matches
findByEmailIndexed("customer42@..."):  direct lookup in pre-built index -> finds 1 match instantly
```

In a real MongoDB collection, a query like `db.orders.find({status: "SHIPPED"})` against an unindexed `status` field triggers a full collection scan — MongoDB examines every document to check the condition, an operation whose cost grows linearly with collection size. A query like `db.orders.find({customerEmail: "customer42@example.com"})` against an `@Indexed` `customerEmail` field instead uses the B-tree index MongoDB maintains automatically, letting the database jump nearly straight to matching documents regardless of how large the collection grows — the exact performance gap `findByStatusUnindexed`/`findByEmailIndexed` model here in simplified form.

## 7. Gotchas & takeaways

> Gotcha: every index MongoDB maintains adds write overhead (each insert/update must also update every affected index) and consumes additional storage — indexing every field "just in case" is a real cost, not a free performance win; `@Indexed` should be reserved for fields genuinely queried or sorted on frequently, not applied blanket across an entity.

- `@Document` maps a class to a MongoDB collection; `@Id` always maps to the special `_id` field regardless of the Java field's own name.
- `@Field` overrides a single field's stored document key, exactly like `@Column` does for relational columns.
- `@Indexed` requests a real database index on that field, turning a linear collection scan into a fast index-assisted lookup for queries filtering or sorting on it.
- Indexes have a real cost (write overhead, storage) — reserve `@Indexed` for fields genuinely queried frequently, not applied indiscriminately to every field.
