---
card: spring-data
gi: 139
slug: index-mapping-management
title: "Index & mapping management"
---

## 1. What it is

`IndexOperations` (obtained via `elasticsearchOperations.indexOps(Order.class)`) manages the lifecycle of an Elasticsearch index itself — creating it, applying a mapping derived from `@Field` annotations, checking whether it exists, and deleting it — separate from `ElasticsearchOperations`'s document-level `save`/`get`/`search` operations covered in earlier cards.

```java
IndexOperations indexOps = elasticsearchOperations.indexOps(Order.class);
if (!indexOps.exists()) {
    indexOps.create();
    indexOps.putMapping(indexOps.createMapping()); // derives the mapping from Order's @Field annotations
}
```

## 2. Why & when

Every earlier card in this section assumed the `orders` index already existed with a correct mapping. In practice, someone (or something) has to actually create that index and apply that mapping before any document can be indexed into it — and, per the previous card's gotcha, get the mapping right *before* significant data goes in, since changing it later requires a full reindex. `IndexOperations` is that lifecycle management layer.

Reach for `IndexOperations` when:

- Setting up a new index for the first time — application startup, a test's `@BeforeEach`, or a deployment migration script that provisions infrastructure before the application starts handling traffic.
- Checking whether an index already exists before conditionally creating it, to make setup logic idempotent and safe to run repeatedly.
- Managing index lifecycle as part of a reindexing migration — creating a new index with a corrected mapping, then (via `_reindex`, invoked outside Spring Data's direct API) copying data from the old index into the new one.

## 3. Core concept

```
 indexOps.exists()          -- does the "orders" index exist right now?
 indexOps.create()           -- creates it (empty, no documents, no mapping applied yet)
 indexOps.createMapping()    -- DERIVES a mapping definition from Order's @Field annotations
 indexOps.putMapping(...)    -- APPLIES that mapping to the (now-created) index
 indexOps.delete()           -- destroys the index and every document in it

 Typical startup sequence:
   if (!exists()) { create(); putMapping(createMapping()); }
```

Index creation and mapping application are two separate steps — an index can exist with no mapping applied, or with an incomplete/incorrect one, if this sequence isn't followed carefully.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Index setup proceeds through exists check, create, derive mapping from annotations, and apply mapping, in order">
  <rect x="20" y="20" width="140" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">exists()?</text>

  <rect x="190" y="20" width="120" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="250" y="47" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">create()</text>

  <rect x="340" y="20" width="140" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="410" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">createMapping()</text>

  <rect x="510" y="20" width="120" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="570" y="47" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">putMapping(...)</text>

  <line x1="160" y1="42" x2="185" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="310" y1="42" x2="335" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="480" y1="42" x2="505" y2="42" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <text x="320" y="110" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">only if the index does NOT already exist -- an idempotent startup sequence</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

An idempotent setup sequence: check first, then create and map only if necessary, so it's safe to run on every startup.

## 5. Runnable example

The scenario: provisioning an `orders` index correctly, evolving from a basic exists-check-then-create sequence, to deriving a mapping from field annotations, to a safe reindex migration when a field's mapping needs to change after data already exists.

### Level 1 — Basic

Model the idempotent exists-check-then-create pattern.

```java
import java.util.*;

public class IndexMappingLevel1 {
    public static void main(String[] args) {
        ElasticsearchIndexManager indexOps = new ElasticsearchIndexManager("orders");

        setupIndexIfNeeded(indexOps); // first run -- index doesn't exist yet
        setupIndexIfNeeded(indexOps); // second run -- SAFE, does nothing since it already exists
    }

    // Mirrors: if (!indexOps.exists()) { indexOps.create(); }
    static void setupIndexIfNeeded(ElasticsearchIndexManager indexOps) {
        if (indexOps.exists()) {
            System.out.println("Index '" + indexOps.name + "' already exists -- skipping creation.");
            return;
        }
        indexOps.create();
        System.out.println("Index '" + indexOps.name + "' created.");
    }
}

// Stands in for elasticsearchOperations.indexOps(Order.class).
class ElasticsearchIndexManager {
    final String name;
    private boolean created = false;
    ElasticsearchIndexManager(String name) { this.name = name; }
    boolean exists() { return created; }
    void create() { created = true; }
}
```

How to run: `java IndexMappingLevel1.java`

`setupIndexIfNeeded` checks `exists()` before calling `create()`, making it safe to call on every application startup — the first call actually creates the index, the second call recognizes it already exists and does nothing, avoiding a duplicate-creation error a naive unconditional `create()` would throw against an already-existing index.

### Level 2 — Intermediate

Derive a mapping definition from field annotations and apply it, matching `indexOps.createMapping()` + `indexOps.putMapping(...)`.

```java
import java.util.*;

public class IndexMappingLevel2 {
    public static void main(String[] args) {
        ElasticsearchIndexManager indexOps = new ElasticsearchIndexManager("orders");
        indexOps.create();

        // Mirrors indexOps.createMapping() -- reflects over @Field annotations to BUILD the mapping definition.
        List<FieldMapping> mapping = List.of(
            new FieldMapping("status", FieldType.KEYWORD),
            new FieldMapping("description", FieldType.TEXT),
            new FieldMapping("createdAt", FieldType.DATE)
        );

        indexOps.putMapping(mapping); // APPLIES the derived mapping to the created index
        System.out.println("Applied mapping to '" + indexOps.name + "':");
        for (FieldMapping fm : indexOps.currentMapping) System.out.println("  " + fm.name + " -> " + fm.type);
    }
}

// Mirrors @Field(type = FieldType.Keyword/Text/Date) annotations on an Order class.
enum FieldType { KEYWORD, TEXT, DATE }

class FieldMapping { String name; FieldType type; FieldMapping(String name, FieldType type) { this.name = name; this.type = type; } }

class ElasticsearchIndexManager {
    final String name;
    private boolean created = false;
    List<FieldMapping> currentMapping = new ArrayList<>();
    ElasticsearchIndexManager(String name) { this.name = name; }
    boolean exists() { return created; }
    void create() { created = true; }
    void putMapping(List<FieldMapping> mapping) { this.currentMapping = new ArrayList<>(mapping); }
}
```

How to run: `java IndexMappingLevel2.java`

`mapping` stands in for what `indexOps.createMapping()` derives automatically by reflecting over an entity class's `@Field` annotations — `status` as `KEYWORD` (exact match), `description` as `TEXT` (analyzed), `createdAt` as `DATE`. `putMapping` applies that definition to the index, matching the two-step "derive, then apply" sequence from the intro snippet.

### Level 3 — Advanced

Perform a safe reindex migration: create a *new* index with a corrected mapping, copy existing documents across, then swap which index the application actually uses — matching the standard, safe way to change a field's mapping on data that already exists.

```java
import java.util.*;

public class IndexMappingLevel3 {
    public static void main(String[] args) {
        ElasticsearchIndexManager oldIndex = new ElasticsearchIndexManager("orders_v1");
        oldIndex.create();
        oldIndex.putMapping(List.of(new FieldMapping("category", FieldType.TEXT))); // ORIGINAL mapping -- no keyword sub-field
        oldIndex.documents.put("1", new Order("1", "Electronics"));
        oldIndex.documents.put("2", new Order("2", "Books"));

        System.out.println("Discovered we need to SORT by category -- but it's mapped as TEXT, unsortable (previous card).");
        System.out.println("Creating a new index with a corrected mapping instead of altering the existing one...");

        // Create a NEW index with the CORRECTED mapping -- the existing index is never modified in place.
        ElasticsearchIndexManager newIndex = new ElasticsearchIndexManager("orders_v2");
        newIndex.create();
        newIndex.putMapping(List.of(new FieldMapping("category", FieldType.KEYWORD))); // CORRECTED

        // Reindex: copy every existing document from the old index into the new one.
        for (var entry : oldIndex.documents.entrySet()) newIndex.documents.put(entry.getKey(), entry.getValue());
        System.out.println("Reindexed " + newIndex.documents.size() + " document(s) from '" + oldIndex.name + "' to '" + newIndex.name + "'.");

        // Only AFTER the reindex succeeds does the application switch to using the new index.
        String activeIndex = newIndex.name;
        System.out.println("Application now points at: " + activeIndex);
        System.out.println("Old index '" + oldIndex.name + "' can be safely deleted once confirmed working.");
    }
}

class Order { String id; String category; Order(String id, String category) { this.id = id; this.category = category; } }

enum FieldType { KEYWORD, TEXT, DATE }

class FieldMapping { String name; FieldType type; FieldMapping(String name, FieldType type) { this.name = name; this.type = type; } }

class ElasticsearchIndexManager {
    final String name;
    private boolean created = false;
    List<FieldMapping> currentMapping = new ArrayList<>();
    Map<String, Order> documents = new HashMap<>();
    ElasticsearchIndexManager(String name) { this.name = name; }
    boolean exists() { return created; }
    void create() { created = true; }
    void putMapping(List<FieldMapping> mapping) { this.currentMapping = new ArrayList<>(mapping); }
}
```

How to run: `java IndexMappingLevel3.java`

Rather than trying to change `orders_v1`'s existing `category` mapping in place (which real Elasticsearch does not allow), a brand-new index `orders_v2` is created with the corrected `KEYWORD` mapping, every existing document is copied across, and only afterward does `activeIndex` switch to point at the new index — the old index is left intact and can be deleted once the new one is confirmed working, giving a safe rollback path if something goes wrong.

## 6. Walkthrough

Execution starts in `main` for Level 3. `oldIndex` ("orders_v1") is created and given a `TEXT` mapping for `category` — matching the mistake identified in the previous card, where a `text`-mapped field can't be sorted. Two documents are added directly to `oldIndex.documents`.

A message is printed acknowledging the mapping problem, then `newIndex` ("orders_v2") is created fresh, with `category` mapped as `KEYWORD` this time — the corrected mapping. Critically, `oldIndex` itself is never modified; a wholly separate index object is created instead.

The `for` loop iterates every entry in `oldIndex.documents` and inserts each one into `newIndex.documents` — this is the reindex step, standing in for Elasticsearch's real `_reindex` API, which copies documents from a source index into a destination index server-side. After the loop, `newIndex.documents.size()` is `2`, matching the count copied from `oldIndex`.

`activeIndex` is then set to `newIndex.name`, representing the application's configuration being updated to query the new index going forward, and a final message notes that the old index remains available for deletion once the switch is verified safe.

```
Discovered we need to SORT by category -- but it's mapped as TEXT, unsortable (previous card).
Creating a new index with a corrected mapping instead of altering the existing one...
Reindexed 2 document(s) from 'orders_v1' to 'orders_v2'.
Application now points at: orders_v2
Old index 'orders_v1' can be safely deleted once confirmed working.
```

In a real Elasticsearch deployment, this exact reindex-then-swap pattern is usually fronted by an **alias** — the application always queries `orders` (an alias), which initially points at `orders_v1`; after the reindex into `orders_v2` completes and is verified, the alias is atomically repointed to `orders_v2` with a single `_aliases` API call, so the application's configuration never needs to change at all, and the cutover is instantaneous with no window where the application points at a partially-migrated index.

## 7. Gotchas & takeaways

> Gotcha: `indexOps.create()` on an index that already exists throws an error in real Elasticsearch — always check `exists()` first (or use `createWithMapping()`, which some versions handle more gracefully), especially in code that runs on every application startup.

> Gotcha: reindexing copies documents but does **not** automatically update application configuration to point at the new index — without an alias layer, every place in the application that references the index name by string needs to be updated in lockstep with the reindex, which is exactly the coordination problem index aliases exist to remove.

- `IndexOperations` (via `elasticsearchOperations.indexOps(Type.class)`) manages index lifecycle — existence checks, creation, mapping application, deletion — separately from document-level operations.
- A mapping is normally derived automatically from an entity's `@Field` annotations via `createMapping()`, then applied with `putMapping(...)`.
- Because Elasticsearch mappings can't be altered in place once documents exist, fixing an incorrect mapping requires creating a new index with the corrected mapping and reindexing existing documents into it.
- Fronting an index with an **alias** lets a reindex-and-swap migration happen without any application configuration change or downtime window.
