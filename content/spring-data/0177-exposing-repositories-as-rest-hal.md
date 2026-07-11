---
card: spring-data
gi: 177
slug: exposing-repositories-as-rest-hal
title: "Exposing repositories as REST (HAL)"
---

## 1. What it is

Spring Data REST automatically exposes Spring Data repository interfaces as hypermedia-driven REST endpoints — no controller code written by hand. Add the `spring-boot-starter-data-rest` dependency, and every public `JpaRepository`/`MongoRepository`/etc. in the application gets a full set of HTTP endpoints, serialized as HAL (Hypertext Application Language) JSON with `_links` for navigation.

```java
interface CustomerRepository extends JpaRepository<Customer, String> { }
// That's it. GET /customers, GET /customers/{id}, POST /customers, etc. now exist automatically.
```

## 2. Why & when

Every module so far in this course covered how to *store and query* data. Spring Data REST answers a different question: given a repository already written, how much of a REST API can be generated automatically, with no controller boilerplate? For straightforward CRUD-over-an-entity APIs — internal admin tools, quick prototypes, or APIs where the resource model maps directly onto the persistence model — Spring Data REST can eliminate an entire layer of repetitive controller code.

Reach for Spring Data REST when:

- The API's resource shape closely matches the entity/repository shape — a `Customer` repository really should expose `Customer` resources with standard CRUD.
- Hypermedia-driven navigation (following `_links` rather than hardcoding URLs) fits the client's needs, or the client is another service that can follow HAL links.
- You want a working REST API immediately from existing repositories, with customization (the next several cards) layered in only where the defaults don't fit.

## 3. Core concept

```
 interface CustomerRepository extends JpaRepository<Customer, String> { }

 Spring Data REST scans for repository interfaces at startup and generates:

 GET    /customers            -> list all customers (HAL collection resource)
 GET    /customers/{id}       -> a single customer (HAL item resource)
 POST   /customers            -> create
 PUT    /customers/{id}       -> full update
 PATCH  /customers/{id}       -> partial update
 DELETE /customers/{id}       -> delete

 Response body includes "_links": { "self": {...}, ... } -- HAL hypermedia navigation
```

The repository interface is the entire specification — Spring Data REST derives the resource path, the HTTP verbs, and the response shape from it automatically.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A repository interface is scanned at startup and exposed automatically as a set of HAL REST endpoints">
  <rect x="30" y="45" width="220" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="140" y="68" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">CustomerRepository</text>
  <text x="140" y="84" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">extends JpaRepository</text>

  <line x1="250" y1="72" x2="320" y2="72" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a12)"/>
  <text x="285" y="62" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">scanned</text>

  <rect x="330" y="20" width="280" height="110" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="40" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Generated HAL REST endpoints</text>
  <text x="470" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">GET/POST /customers</text>
  <text x="470" y="76" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">GET/PUT/PATCH/DELETE /customers/{id}</text>
  <text x="470" y="96" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="monospace">{ "_links": {...} }</text>

  <defs><marker id="a12" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A repository interface alone is enough for Spring Data REST to generate a full set of HAL endpoints.

## 5. Runnable example

The scenario: exposing a `Customer` repository as REST, evolving from a hand-written controller doing what Spring Data REST would generate automatically, to a simulated auto-generated HAL endpoint, to HAL responses including `_links` for related resources — demonstrating what hypermedia navigation actually looks like on the wire.

### Level 1 — Basic

Show the hand-written controller baseline — the boilerplate Spring Data REST exists to eliminate.

```java
import java.util.*;

public class RestExposureLevel1 {
    public static void main(String[] args) {
        CustomerController controller = new CustomerController();
        controller.create(new Customer("c1", "Amara"));
        controller.create(new Customer("c2", "Bilal"));

        System.out.println("GET /customers -> " + controller.list().size() + " customers");
        System.out.println("GET /customers/c1 -> " + controller.getById("c1").name);
    }
}

class Customer { String id, name; Customer(String id, String name) { this.id = id; this.name = name; } }

// A HAND-WRITTEN controller doing exactly what Spring Data REST would generate automatically.
class CustomerController {
    private final Map<String, Customer> store = new HashMap<>();
    Customer create(Customer c) { store.put(c.id, c); return c; }         // handles POST /customers
    List<Customer> list() { return new ArrayList<>(store.values()); }     // handles GET /customers
    Customer getById(String id) { return store.get(id); }                 // handles GET /customers/{id}
}
```

How to run: `java RestExposureLevel1.java`

Every method here — `create`, `list`, `getById` — is exactly what a `@RestController` would need to hand-write to expose `Customer` as REST; Spring Data REST generates all of it from the repository interface alone.

### Level 2 — Intermediate

Simulate what Spring Data REST auto-generates: HAL-shaped JSON responses with a `_links.self` entry, derived automatically from the repository and entity.

```java
import java.util.*;

public class RestExposureLevel2 {
    public static void main(String[] args) {
        HalRepositoryExporter<Customer> exporter = new HalRepositoryExporter<>("customers", Customer::id);
        exporter.save(new Customer("c1", "Amara"));
        exporter.save(new Customer("c2", "Bilal"));

        System.out.println("GET /customers/c1 ->");
        System.out.println(exporter.toHalJson(exporter.findById("c1")));
    }
}

record Customer(String id, String name) {}

// Stands in for what Spring Data REST's HAL serialization generates automatically per repository.
class HalRepositoryExporter<T> {
    private final Map<String, T> store = new HashMap<>();
    private final String resourcePath;
    private final java.util.function.Function<T, String> idExtractor;

    HalRepositoryExporter(String resourcePath, java.util.function.Function<T, String> idExtractor) {
        this.resourcePath = resourcePath; this.idExtractor = idExtractor;
    }
    void save(T entity) { store.put(idExtractor.apply(entity), entity); }
    T findById(String id) { return store.get(id); }

    String toHalJson(T entity) {
        String id = idExtractor.apply(entity);
        Customer c = (Customer) entity;
        return "{ \"name\": \"" + c.name() + "\", \"_links\": { \"self\": { \"href\": \"/"
            + resourcePath + "/" + id + "\" } } }";
    }
}
```

How to run: `java RestExposureLevel2.java`

`toHalJson` mirrors what Spring Data REST's HAL serializer produces automatically: the entity's own fields, plus a `_links.self.href` pointing back at the resource's own URL — every generated resource is self-describing with its own retrievable link, with no controller code writing that link by hand.

### Level 3 — Advanced

Add `_links` for related resources — a customer's HAL representation linking out to its orders — showing hypermedia navigation across an entity relationship, the payoff of the HAL format over plain JSON.

```java
import java.util.*;

public class RestExposureLevel3 {
    public static void main(String[] args) {
        HalExporter exporter = new HalExporter();
        exporter.saveCustomer(new Customer("c1", "Amara"));
        exporter.saveOrder(new Order("o1", "c1", "PENDING"));
        exporter.saveOrder(new Order("o2", "c1", "SHIPPED"));

        System.out.println("GET /customers/c1 ->");
        System.out.println(exporter.customerToHalJson("c1"));
    }
}

record Customer(String id, String name) {}
record Order(String id, String customerId, String status) {}

// Stands in for Spring Data REST generating _links.orders for an @RepositoryRestResource-exposed association.
class HalExporter {
    private final Map<String, Customer> customers = new HashMap<>();
    private final List<Order> orders = new ArrayList<>();

    void saveCustomer(Customer c) { customers.put(c.id(), c); }
    void saveOrder(Order o) { orders.add(o); }

    String customerToHalJson(String customerId) {
        Customer c = customers.get(customerId);
        long orderCount = orders.stream().filter(o -> o.customerId().equals(customerId)).count();
        return "{ \"name\": \"" + c.name() + "\", \"_links\": { "
            + "\"self\": { \"href\": \"/customers/" + c.id() + "\" }, "
            + "\"orders\": { \"href\": \"/customers/" + c.id() + "/orders\" } }, "
            + "\"orderCount\": " + orderCount + " }";
    }
}
```

How to run: `java RestExposureLevel3.java`

The generated HAL body includes both `_links.self` (this resource's own URL) and `_links.orders` (the URL a client would `GET` next to fetch this customer's orders) — a client can navigate from customer to orders purely by following the `href` in the response, without hardcoding `/customers/{id}/orders` anywhere in its own code.

## 6. Walkthrough

Execution starts in `main` for Level 3. One customer and two orders are saved, both referencing `c1`. `exporter.customerToHalJson("c1")` builds the HAL representation.

The conceptual HTTP request is `GET /customers/c1`, and the response is:

```json
{
  "name": "Amara",
  "_links": {
    "self":   { "href": "/customers/c1" },
    "orders": { "href": "/customers/c1/orders" }
  },
  "orderCount": 2
}
```

A client consuming this response doesn't need to know the URL pattern `/customers/{id}/orders` in advance — it reads `_links.orders.href` from the response it already has, and issues its next request against that URL. This is the core hypermedia principle HAL embodies: the API tells the client what it can do next, rather than the client needing out-of-band knowledge of the URL structure.

## 7. Gotchas & takeaways

> Gotcha: exposing *every* public repository automatically means accidentally exposing repositories never meant to be public REST endpoints — an internal `AuditLogRepository`, say — is a real risk unless exposure is deliberately scoped (the next few cards cover exactly how).

> Gotcha: the default generated REST representation mirrors the JPA/Mongo entity shape closely, including fields that may not be appropriate to expose externally (internal flags, sensitive data) — Spring Data REST's convenience can leak persistence-layer details into a public API surface if left entirely on defaults.

- Spring Data REST generates a full HAL REST API directly from repository interfaces, eliminating hand-written CRUD controller boilerplate for straightforward cases.
- HAL responses are self-describing via `_links` — a `self` link plus links to related resources, letting clients navigate without hardcoding URL patterns.
- The convenience trades off control: every public repository is exposed by default, and the generated resource shape mirrors the entity shape unless customized.
- The next several cards cover exactly that customization — `@RepositoryRestResource`, exposure strategies, and shaping the generated resources.
