---
card: microservices
gi: 15
slug: polyglot-programming-polyglot-persistence
title: Polyglot programming & polyglot persistence
---

## 1. What it is

**Polyglot programming** means different services in the same system can be written in whichever language best suits their specific job — one service in Java for heavy business logic, another in Python for a machine-learning model, another in Go for a low-latency proxy — because the only thing that actually connects them is a network contract, not a shared compiled artifact. **Polyglot persistence** is the same idea applied to storage: each service picks the data store that fits its access pattern — a relational database for `OrdersService`'s transactional data, a document store for `CatalogService`'s flexible product attributes, a key-value cache for `SessionService`'s ephemeral state — rather than every service being forced onto one company-wide database technology.

## 2. Why & when

Both forms of "polyglot" are a direct consequence of [decentralized governance](0008-decentralized-governance.md): once only the contract is centrally agreed and the implementation is a team's own choice, that choice naturally extends to language and storage technology, not just internal code structure. A relational database is excellent for `OrdersService`'s need for strict transactional consistency across an order's line items; that same relational rigidity is often a poor fit for `CatalogService`'s wildly varying, frequently-changing product attribute sets, where a schema-flexible document store fits better.

Adopt polyglot choices deliberately, service by service, based on that service's actual access pattern and team expertise — not reflexively, for variety's own sake. Every additional language or storage technology in active use is a genuine operational cost: one more thing to monitor, back up, patch, and staff for. A small organization is often better served by two or three well-understood technologies applied consistently than by ten different ones chosen for marginal per-service fit.

## 3. Core concept

Polyglot works because of the same principle as decentralized governance: what's shared is the **contract**, not the **implementation**. This example demonstrates the concept entirely in Java (the storage *shape* differs — relational-style versus document-style — even though the demonstration language stays fixed), but the underlying idea generalizes directly to genuinely different languages and database engines behind the same kind of network contract.

- A relational-style model: fixed columns, strict types, values referenced by strongly-typed fields.
- A document-style model: a flexible, nested map where different records can have entirely different sets of fields.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OrdersService uses a relational-style store while CatalogService uses a document-style store, each independently chosen to fit its own access pattern, connected only through their respective APIs">
  <rect x="40" y="40" width="200" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrdersService</text>
  <text x="140" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">relational-style store</text>
  <text x="140" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fixed columns, strict types</text>

  <rect x="400" y="40" width="200" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">CatalogService</text>
  <text x="500" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">document-style store</text>
  <text x="500" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">flexible, per-record fields</text>
</svg>

Each service's storage shape is chosen to fit its own access pattern — connected to the rest of the system only through its API.

## 5. Runnable example

Scenario: `OrdersService` and `CatalogService` each modeling their data the way that suits them best, first as fixed relational-style records, then contrasted with a flexible document-style catalog, then combined into one system where each service's storage choice is entirely invisible to the other.

### Level 1 — Basic

```java
// File: RelationalStyleOrders.java -- OrdersService: FIXED columns, strict types
public class RelationalStyleOrders {
    record Order(int orderId, String customerId, double total, String status) { } // every order has EXACTLY these fields

    public static void main(String[] args) {
        Order order = new Order(1001, "cust-1", 29.98, "PLACED");
        System.out.println("Order " + order.orderId() + ": customer=" + order.customerId() + ", total=$" + order.total() + ", status=" + order.status());
    }
}
```

**How to run:** `javac RelationalStyleOrders.java && java RelationalStyleOrders` (JDK 17+).

Expected output:
```
Order 1001: customer=cust-1, total=$29.98, status=PLACED
```

Every `Order` has exactly the same fixed shape — `orderId`, `customerId`, `total`, `status` — which is exactly what a relational table's fixed columns and an order's need for strict transactional consistency call for.

### Level 2 — Intermediate

```java
// File: DocumentStyleCatalog.java -- CatalogService: FLEXIBLE, per-record fields,
// since different product categories genuinely need different attributes.
import java.util.*;

public class DocumentStyleCatalog {
    public static void main(String[] args) {
        // a document store lets EACH record carry its own distinct set of fields
        Map<String, Object> widget = new LinkedHashMap<>();
        widget.put("name", "Widget");
        widget.put("price", 9.99);
        widget.put("weightGrams", 150); // physical product: has weight

        Map<String, Object> ebook = new LinkedHashMap<>();
        ebook.put("name", "Learning Microservices");
        ebook.put("price", 19.99);
        ebook.put("fileSizeMb", 4.2); // digital product: has file size, NOT weight -- a genuinely different shape

        for (Map<String, Object> product : List.of(widget, ebook)) {
            System.out.println(product.get("name") + ": $" + product.get("price") + " -- fields: " + product.keySet());
        }
    }
}
```

**How to run:** `javac DocumentStyleCatalog.java && java DocumentStyleCatalog` (JDK 17+).

Expected output:
```
Widget: $9.99 -- fields: [name, price, weightGrams]
Learning Microservices: $19.99 -- fields: [name, price, fileSizeMb]
```

Unlike `OrdersService`'s `Order` record, `widget` and `ebook` have genuinely different sets of fields — `weightGrams` versus `fileSizeMb` — with no shared, fixed schema forcing every product into the same shape. This is exactly the kind of variability a document store handles naturally and a rigid relational table would need awkward nullable columns or extra tables to express.

### Level 3 — Advanced

```java
// File: PolyglotSystem.java -- OrdersService and CatalogService, each using
// its OWN storage shape, wired together ONLY through their public APIs.
import java.util.*;

public class PolyglotSystem {
    // OrdersService: relational-style, fixed shape -- completely private to this service
    record Order(int orderId, String productName, double total) { }
    static List<Order> orderStore = new ArrayList<>();

    static void placeOrder(int orderId, String productName, double total) {
        orderStore.add(new Order(orderId, productName, total));
    }

    // CatalogService: document-style, flexible shape -- completely private to this service
    static List<Map<String, Object>> catalogStore = new ArrayList<>();

    static void addProduct(Map<String, Object> product) { catalogStore.add(product); }

    static Optional<Map<String, Object>> lookupProduct(String name) {
        return catalogStore.stream().filter(p -> p.get("name").equals(name)).findFirst();
    }

    // the ONLY connection between the two services: a lookup by NAME, a plain String contract
    static void placeOrderForProduct(int orderId, String productName) {
        Optional<Map<String, Object>> product = lookupProduct(productName);
        if (product.isEmpty()) { System.out.println("Cannot order unknown product: " + productName); return; }
        double price = (double) product.get().get("price");
        placeOrder(orderId, productName, price);
        System.out.println("Order " + orderId + " placed for " + productName + " at $" + price);
    }

    public static void main(String[] args) {
        Map<String, Object> widget = new LinkedHashMap<>();
        widget.put("name", "Widget");
        widget.put("price", 9.99);
        widget.put("weightGrams", 150);
        addProduct(widget);

        placeOrderForProduct(1001, "Widget");
        System.out.println("orderStore (relational-style): " + orderStore);
        System.out.println("catalogStore (document-style, untouched by OrdersService's shape): " + catalogStore);
    }
}
```

**How to run:** `javac PolyglotSystem.java && java PolyglotSystem` (JDK 17+).

Expected output:
```
Order 1001 placed for Widget at $9.99
orderStore (relational-style): [Order[orderId=1001, productName=Widget, total=9.99]]
catalogStore (document-style, untouched by OrdersService's shape): [{name=Widget, price=9.99, weightGrams=150}]
```

The production-flavored case: `placeOrderForProduct` bridges the two services, but only through `lookupProduct`'s return value — a `price` it reads out and stores in its own, entirely different shape (`Order`, a fixed record). `orderStore` never sees `weightGrams`, and `catalogStore` never sees `orderId` or `total` — each service's internal storage shape stays completely private, exactly as it would if `OrdersService` ran on a real relational database and `CatalogService` on a real document database, possibly written in two entirely different languages.

## 6. Walkthrough

1. `addProduct(widget)` inserts a document-shaped record — a `LinkedHashMap` with `name`, `price`, and `weightGrams` — into `catalogStore`, which is entirely private to `CatalogService`'s side of the code.
2. `placeOrderForProduct(1001, "Widget")` runs next. It calls `lookupProduct("Widget")`, which searches `catalogStore` for a matching `name` and returns the whole document, wrapped in an `Optional`.
3. Since the product is found, `placeOrderForProduct` extracts just one field it actually needs — `price`, cast from `Object` to `double` — completely ignoring `weightGrams` and any other fields the document might carry. This is the network-contract-style boundary in action: only what's needed crosses from one service's data shape into the other's.
4. `placeOrder(1001, "Widget", 9.99)` constructs a brand-new `Order` record — the relational-style shape `OrdersService` actually uses — and appends it to `orderStore`, which is entirely separate storage from `catalogStore`.
5. The two final printouts show `orderStore` holding a strongly-typed `Order` record with exactly three fixed fields, and `catalogStore` still holding its original flexible document with `weightGrams` — proof that `OrdersService`'s fixed relational shape and `CatalogService`'s flexible document shape coexisted throughout, each private to its own service, joined only by the single `price` value that crossed the boundary.

```
CatalogService (document-style):  {name, price, weightGrams}
        |
   lookupProduct("Widget") -> returns the WHOLE document
        |
   placeOrderForProduct extracts ONLY "price"
        |
OrdersService (relational-style): Order(orderId, productName, total)
```

## 7. Gotchas & takeaways

> **Gotcha:** polyglot persistence multiplies operational cost, not just design flexibility — every additional storage technology in production needs its own backup strategy, its own monitoring, its own on-call expertise, and its own upgrade path. Choosing five different databases across five services because each is "technically the best fit" can leave a small team unable to properly operate any of them.

- Polyglot programming and persistence mean each service can choose the language and storage technology that fits its own access pattern, connected to other services only through a network contract.
- The concrete proof that polyglot choices are safe: can one service's internal storage shape change completely, without any other service's code needing to change, because only a narrow, specific value crosses the boundary?
- This is decentralized governance applied specifically to language and data technology — the same "own the implementation, share only the contract" principle.
- Weigh every additional technology's real operational cost against its per-service fit — a small number of well-understood, consistently-applied technologies often beats a large number of individually optimal ones.
