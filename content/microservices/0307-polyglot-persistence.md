---
card: microservices
gi: 307
slug: polyglot-persistence
title: "Polyglot persistence"
---

## 1. What it is

Polyglot persistence is the practice of letting each service choose the database technology best suited to its own specific data and access patterns, rather than forcing every service in the system onto one single database engine. One service might use a relational database for strongly structured, transactional order data; another might use a document store for flexible, schema-varying product catalog data; another might use a graph database for a social/recommendation feature built on relationships; another might use a time-series database for metrics. [Database per service](0304-database-per-service-pattern.md) is what makes this possible at all — since each service's data is already private and isolated, nothing prevents different services from choosing entirely different storage technologies.

## 2. Why & when

A monolith with one shared database is typically forced to make every kind of data fit one engine's model, even when that model is a poor fit for some of it — storing deeply nested, frequently-changing product attributes in rigid relational tables, or trying to model highly connected social-graph data as SQL joins, both work, but often awkwardly and with real performance and development-velocity costs. Polyglot persistence removes this constraint: once a service's data is genuinely private, that service's team can pick storage technology purely based on what fits their data model and access patterns best, without needing agreement from every other team in the system.

Use polyglot persistence deliberately, driven by a genuine mismatch between a service's data shape/access pattern and its current database technology — not simply because a new technology is interesting to try. The cost is real: more different database technologies in production means more operational expertise required across the team, more tooling to maintain, and more moving pieces overall, so the benefit needs to clearly outweigh that added complexity for each specific case.

## 3. Core concept

Each service's repository/data-access layer targets whichever store fits it, entirely independent of what other services use — there is no shared data-access abstraction spanning services, because there is no shared data.

```java
// InventoryService: relational, strongly structured, transactional stock counts.
@Service
class InventoryService {
    private final JpaRepository<StockRecord, String> stockRepository; // relational (e.g. PostgreSQL)
}

// ProductCatalogService: flexible, varying attributes per product category.
@Service
class ProductCatalogService {
    private final MongoRepository<ProductDocument, String> productRepository; // document store (e.g. MongoDB)
}

// RecommendationService: highly connected "users who bought X also bought Y" data.
@Service
class RecommendationService {
    private final Neo4jRepository<ProductNode, String> graphRepository; // graph database (e.g. Neo4j)
}
// Each choice is made INDEPENDENTLY, driven by that service's OWN data shape.
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three services each independently choose the database technology best suited to their own data shape: a relational database for strongly structured transactional data, a document store for flexible varying attributes, and a graph database for highly connected relationship data, with no requirement that any two services agree on the same technology">
  <rect x="20" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Inventory Service</text>
  <text x="110" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Relational (structured, transactional)</text>

  <rect x="230" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Product Catalog Service</text>
  <text x="320" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Document store (flexible attributes)</text>

  <rect x="440" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Recommendation Service</text>
  <text x="530" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Graph database (connected data)</text>

  <text x="320" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">each choice made INDEPENDENTLY, driven by that service's own data shape</text>
</svg>

Each service's storage technology is chosen independently, based purely on the fit for its own data.

## 5. Runnable example

Scenario: one service awkwardly forcing flexible, varying product attributes into a rigid, fixed-column relational-style model, extended to the same data modeled naturally as a flexible document, and finally a small comparison harness quantifying the structural cost (wasted or missing fields) of the mismatched relational model versus the natural fit of the document model for the same realistic dataset.

### Level 1 — Basic

```java
// File: RigidRelationalModelForVaryingData.java -- product data has
// WILDLY different attributes per category (a book has an author and
// ISBN; a laptop has a CPU and RAM; a t-shirt has a size and color), but
// this service is forced to use a FIXED set of relational-style columns,
// leading to wasted null columns and awkward workarounds.
import java.util.*;

public class RigidRelationalModelForVaryingData {
    // A FIXED, one-size-fits-all "table" -- every product row has EVERY
    // possible column, even though most are irrelevant for any given product.
    record ProductRow(String sku, String category, String author, String isbn,
                       String cpu, String ramGb, String size, String color) {}

    public static void main(String[] args) {
        List<ProductRow> products = List.of(
                new ProductRow("bk-1", "book", "Jane Doe", "978-0-000", null, null, null, null),
                new ProductRow("lt-1", "laptop", null, null, "M3", "16", null, null),
                new ProductRow("ts-1", "tshirt", null, null, null, null, "L", "blue")
        );

        int totalCells = 0, wastedNullCells = 0;
        for (ProductRow p : products) {
            for (Object field : List.of(p.author(), p.isbn(), p.cpu(), p.ramGb(), p.size(), p.color())) {
                totalCells++;
                if (field == null) wastedNullCells++;
            }
        }
        System.out.println("Total attribute cells: " + totalCells + ", wasted/null cells: " + wastedNullCells
                + " (" + (100 * wastedNullCells / totalCells) + "% waste -- most columns are irrelevant for any given product)");
    }
}
```

How to run: `java RigidRelationalModelForVaryingData.java`

Every product row carries all six category-specific columns regardless of its actual category, so a book's row has four `null` columns (cpu, ram, size, color), a laptop's has four different `null` columns, and so on. The printed waste percentage — most of the cells across this small dataset are unused — illustrates the structural mismatch: a fixed, uniform schema forced onto data whose actual shape genuinely varies by category, a common source of awkward, `NULL`-heavy relational designs, or an ever-growing number of increasingly sparse columns as new product categories are added.

### Level 2 — Intermediate

```java
// File: FlexibleDocumentModel.java -- the SAME product data modeled
// naturally as a document with only the attributes RELEVANT to that
// product's category, matching how a document store (e.g., MongoDB)
// represents genuinely variable-shape data without wasted columns.
import java.util.*;

public class FlexibleDocumentModel {
    record ProductDocument(String sku, String category, Map<String, Object> attributes) {}

    public static void main(String[] args) {
        List<ProductDocument> products = List.of(
                new ProductDocument("bk-1", "book", Map.of("author", "Jane Doe", "isbn", "978-0-000")),
                new ProductDocument("lt-1", "laptop", Map.of("cpu", "M3", "ramGb", "16")),
                new ProductDocument("ts-1", "tshirt", Map.of("size", "L", "color", "blue"))
        );

        int totalCells = 0;
        for (ProductDocument p : products) totalCells += p.attributes().size(); // ONLY relevant attributes counted

        System.out.println("Total attribute entries across all products: " + totalCells + " (zero wasted/null entries -- "
                + "each document holds ONLY the attributes relevant to its own category)");
        for (ProductDocument p : products) {
            System.out.println("  " + p.sku() + " (" + p.category() + "): " + p.attributes());
        }
    }
}
```

How to run: `java FlexibleDocumentModel.java`

Each `ProductDocument` carries only the attributes actually relevant to its category — a book's document has exactly `author` and `isbn`, nothing else, no wasted columns at all. The total attribute-entry count across all three products is exactly the number of *meaningful* attributes (6, matching the non-null count from Level 1), with zero waste — this is the natural fit a document store provides for genuinely variable-shape data, which is exactly why a real product catalog service, needing to support arbitrarily different attribute sets per category without constant schema migrations, is a strong candidate for this kind of storage technology.

### Level 3 — Advanced

```java
// File: PolyglotServicesComparison.java -- simulates THREE services each
// choosing their OWN storage shape independently, matching THEIR OWN
// data's actual access patterns, and demonstrates why forcing all three
// onto ONE shared model (e.g., relational-only) would be a poor fit for
// at least one of them, justifying the polyglot approach.
import java.util.*;

public class PolyglotServicesComparison {
    // Service 1: InventoryService -- strongly structured, needs TRANSACTIONAL
    // consistency across a few fixed fields. Relational fits naturally.
    record StockRecord(String sku, int quantity, int reservedQuantity) {}

    // Service 2: ProductCatalogService -- variable attributes per category.
    // Document model fits naturally (see Level 2).
    record ProductDocument(String sku, Map<String, Object> attributes) {}

    // Service 3: RecommendationService -- "customers who bought X also
    // bought Y" is fundamentally a GRAPH traversal problem: find all
    // products connected to a given product through purchase co-occurrence.
    static Map<String, Set<String>> purchaseGraph = Map.of(
            "bk-1", Set.of("bk-2", "bk-3"),
            "bk-2", Set.of("bk-1", "bk-4"),
            "bk-3", Set.of("bk-1")
    );
    static Set<String> recommendationsFor(String sku) { return purchaseGraph.getOrDefault(sku, Set.of()); }

    public static void main(String[] args) {
        // InventoryService: relational-style transactional update.
        StockRecord stock = new StockRecord("sku-1", 100, 5);
        System.out.println("InventoryService (relational fit): available = " + (stock.quantity() - stock.reservedQuantity()));

        // ProductCatalogService: document-style variable attributes.
        ProductDocument product = new ProductDocument("bk-1", Map.of("author", "Jane Doe", "isbn", "978-0-000"));
        System.out.println("ProductCatalogService (document fit): " + product.attributes());

        // RecommendationService: graph traversal -- awkward to express as
        // repeated SQL self-joins as the graph gets deeper, natural as a
        // graph query (e.g., Cypher: MATCH (p:Product)-[:BOUGHT_WITH]->(r) WHERE p.sku = 'bk-1' RETURN r).
        System.out.println("RecommendationService (graph fit): recommendations for bk-1 = " + recommendationsFor("bk-1"));

        System.out.println("\nEach service picked its storage technology INDEPENDENTLY, based on ITS OWN data shape --");
        System.out.println("forcing all three onto ONE shared relational schema would make at least two of them awkward to model and query efficiently.");
    }
}
```

How to run: `java PolyglotServicesComparison.java`

Three independent data shapes are modeled using the representation that fits each naturally: `InventoryService`'s stock levels as a simple structured record (a natural fit for relational tables with transactional guarantees), `ProductCatalogService`'s variable attributes as a flexible map (a natural fit for a document store), and `RecommendationService`'s "bought together" relationships as a graph adjacency structure (a natural fit for a graph database, where finding connected products is a direct traversal rather than a potentially expensive chain of self-joins). None of the three representations would serve the others well — modeling the purchase graph relationally would require join tables that grow awkward as relationship depth increases; modeling variable product attributes relationally reintroduces Level 1's wasted-column problem — which is the concrete justification for each service choosing independently.

## 6. Walkthrough

Trace `PolyglotServicesComparison.main`'s recommendation lookup. **First**, `purchaseGraph` is defined as a map from a SKU to the set of SKUs frequently purchased alongside it — `"bk-1"` maps to `{"bk-2", "bk-3"}`, `"bk-2"` maps to `{"bk-1", "bk-4"}`, and so on, representing a small purchase co-occurrence graph.

**`recommendationsFor("bk-1")` is called.** Inside, `purchaseGraph.getOrDefault("bk-1", Set.of())` performs a direct, single-hop lookup: since `"bk-1"` is a key in the map, it returns its associated set, `{"bk-2", "bk-3"}`, immediately — this is exactly the shape of query a graph database is optimized for: "find everything directly connected to this node," executed as a single traversal rather than a scan-and-join operation.

**Contrast with how this would need to be expressed relationally**: a relational schema for the same data would typically need a `purchase_pairs` table with columns like `sku_a`, `sku_b`, and a query like `SELECT sku_b FROM purchase_pairs WHERE sku_a = 'bk-1'` — functionally similar for this one-hop case, but as soon as the recommendation logic needs to go deeper ("also recommend books frequently bought with books that were bought with bk-1" — a two-hop traversal), the relational version requires a self-join per additional hop, growing more complex and often significantly slower with each level, while a graph database's traversal cost grows much more gracefully with path depth, since traversing relationships is its core, optimized operation rather than an emergent property of repeated joins.

**Back in `main`**, the returned set `{"bk-2", "bk-3"}` is printed directly as the recommendations for `"bk-1"` — a simple, natural result for what the data's underlying shape (a graph of relationships) makes a simple, natural query.

**The structural point across all three services in this example**: `InventoryService`'s transactional stock arithmetic, `ProductCatalogService`'s attribute lookup, and `RecommendationService`'s graph traversal are three genuinely different *kinds* of operations against three genuinely different *shapes* of data — polyglot persistence lets each be modeled and queried in the representation that fits it, rather than compromising all three to fit whichever single technology was chosen first.

```
InventoryService:      quantity - reservedQuantity           -> arithmetic on structured fields (relational fit)
ProductCatalogService: attributes.get(key)                   -> lookup in a variable-shape map (document fit)
RecommendationService: purchaseGraph.get(sku) -> connected set -> graph traversal (graph database fit)
```

## 7. Gotchas & takeaways

> Adopting a new database technology purely because it's interesting, without a genuine data-shape or access-pattern mismatch driving the decision, adds real operational cost (more expertise required, more tooling, more failure modes to understand) without a matching benefit — polyglot persistence should be a deliberate response to an actual mismatch, not a default preference for variety.

- Database-per-service is the prerequisite that makes polyglot persistence possible at all — without private, isolated data per service, no service could safely diverge from a shared technology choice.
- Choose a different storage technology per service based on a genuine mismatch between the current technology and that service's actual data shape or access pattern — structured/transactional data fits relational well, variable-shape data fits document stores well, highly connected relationship data fits graph databases well, high-volume sequential metrics fit time-series databases well.
- Each additional distinct database technology in production adds real operational cost (expertise, tooling, monitoring, backup/restore procedures) — weigh this cost against the fit benefit for each specific case rather than assuming more technologies is automatically better.
- Polyglot persistence is a per-service decision, made independently by each service's own team based on their own data — it does not require, and should not require, system-wide agreement or a shared technology roadmap across all services.
