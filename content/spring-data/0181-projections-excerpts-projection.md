---
card: spring-data
gi: 181
slug: projections-excerpts-projection
title: "Projections & excerpts (@Projection)"
---

## 1. What it is

`@Projection` defines a named, alternate JSON shape for a Spring Data REST resource, selectable per-request via a `projection` query parameter (`GET /customers/c1?projection=summary`). An "excerpt projection" is a special case: a projection automatically applied to an entity whenever it appears *embedded* inside another resource's collection, without the client asking for it explicitly.

```java
@Projection(name = "summary", types = Customer.class)
interface CustomerSummary {
    String getName();
}
// GET /customers/c1?projection=summary -> { "name": "Amara", "_links": {...} }
```

## 2. Why & when

This closes out Spring Data REST's resource-shaping toolbox: the previous card's `@JsonIgnore` hides a field for *every* client, permanently. `@Projection` is different — it defines *multiple* named shapes for the same resource, and lets each request choose which one it wants, rather than committing to one fixed public shape.

Reach for `@Projection` when:

- Different clients of the same API legitimately need different amounts of detail from the same resource — a mobile client wanting a lean summary, an admin dashboard wanting the full picture.
- A collection endpoint embeds related entities (e.g. `GET /orders` embedding each order's customer) and the embedded shape should be lean by default — that's exactly what an excerpt projection is for.
- The shaping needs to be selectable at request time, not fixed once at the entity/repository level.

## 3. Core concept

```
 @Projection(name = "summary", types = Customer.class)
 interface CustomerSummary { String getName(); }

 @Projection(name = "detailed", types = Customer.class)
 interface CustomerDetailed { String getName(); String getEmail(); String getCity(); }

 GET /customers/c1                     -> full default entity shape
 GET /customers/c1?projection=summary   -> { "name": "Amara" }
 GET /customers/c1?projection=detailed  -> { "name": "Amara", "email": "...", "city": "..." }

 @RepositoryRestResource(excerptProjection = CustomerSummary.class)
 interface CustomerRepository extends JpaRepository<Customer, String> { }
   -> whenever a Customer is EMBEDDED inside another resource, it automatically uses "summary" shape
```

Named projections are opt-in per request via a query parameter; an excerpt projection is opt-out — it's the automatic default whenever the entity appears nested inside something else.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same Customer resource can be rendered in different shapes depending on the requested projection or its embedding context">
  <rect x="230" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Customer entity</text>

  <line x1="280" y1="60" x2="150" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a14)"/>
  <line x1="320" y1="60" x2="320" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a14)"/>
  <line x1="360" y1="60" x2="500" y2="100" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a14)"/>

  <rect x="50" y="105" width="200" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="150" y="130" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">default: full shape</text>

  <rect x="220" y="105" width="200" height="40" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="130" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">?projection=summary</text>

  <rect x="400" y="105" width="200" height="40" rx="6" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="130" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">embedded: excerpt</text>

  <defs><marker id="a14" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The same entity, three different rendered shapes: full default, an explicitly requested named projection, and the automatic excerpt shown when embedded.

## 5. Runnable example

The scenario: shaping how `Customer` data appears in different contexts, evolving from a single fixed shape, to multiple named projections selectable by request parameter, to an excerpt projection automatically applied when a customer is embedded inside an order's response.

### Level 1 — Basic

Model the fixed, single-shape baseline — the problem multiple projections solve.

```java
public class ProjectionExcerptLevel1 {
    public static void main(String[] args) {
        Customer amara = new Customer("c1", "Amara", "amara@example.com", "Lagos");
        System.out.println("GET /customers/c1 -> " + toFullJson(amara)); // always the same, full shape
    }

    static String toFullJson(Customer c) {
        return "{ \"name\": \"" + c.name + "\", \"email\": \"" + c.email + "\", \"city\": \"" + c.city + "\" }";
    }
}

class Customer {
    String id, name, email, city;
    Customer(String id, String name, String email, String city) { this.id = id; this.name = name; this.email = email; this.city = city; }
}
```

How to run: `java ProjectionExcerptLevel1.java`

Every consumer of `/customers/c1` gets the exact same full shape — fine for one client, wasteful for a mobile client that only wants the name, and insufficient for a dashboard that might want even more.

### Level 2 — Intermediate

Add named projections, selected via a simulated query parameter, mirroring `?projection=summary` / `?projection=detailed`.

```java
import java.util.*;

public class ProjectionExcerptLevel2 {
    public static void main(String[] args) {
        Customer amara = new Customer("c1", "Amara", "amara@example.com", "Lagos");

        System.out.println("GET /customers/c1 -> " + render(amara, null));               // default: full shape
        System.out.println("GET /customers/c1?projection=summary -> " + render(amara, "summary"));
        System.out.println("GET /customers/c1?projection=detailed -> " + render(amara, "detailed"));
    }

    // Stands in for Spring Data REST resolving the ?projection= query parameter to a registered @Projection.
    static String render(Customer c, String projection) {
        if ("summary".equals(projection)) {
            return "{ \"name\": \"" + c.name + "\" }"; // @Projection(name="summary") { String getName(); }
        }
        if ("detailed".equals(projection)) {
            return "{ \"name\": \"" + c.name + "\", \"email\": \"" + c.email + "\" }"; // @Projection(name="detailed")
        }
        return "{ \"name\": \"" + c.name + "\", \"email\": \"" + c.email + "\", \"city\": \"" + c.city + "\" }"; // default full shape
    }
}

class Customer {
    String id, name, email, city;
    Customer(String id, String name, String email, String city) { this.id = id; this.name = name; this.email = email; this.city = city; }
}
```

How to run: `java ProjectionExcerptLevel2.java`

`render` picks a different JSON shape entirely based on the `projection` parameter — the same underlying `Customer` object produces three genuinely different response bodies, and the client decides which one it wants per request, without the server needing separate endpoints for each.

### Level 3 — Advanced

Add an excerpt projection: automatically applied to `Customer` whenever it's embedded inside an `Order`'s response, without the client requesting it — the "opt-out by default when nested" behavior distinct from named projections' "opt-in by request" behavior.

```java
import java.util.*;

public class ProjectionExcerptLevel3 {
    public static void main(String[] args) {
        Customer amara = new Customer("c1", "Amara", "amara@example.com", "Lagos");
        Order order = new Order("o1", amara, "PENDING");

        System.out.println("GET /customers/c1 -> " + renderCustomer(amara, null)); // full shape, top-level request
        System.out.println("GET /orders/o1 -> " + renderOrder(order)); // customer EMBEDDED -> excerpt shape automatically
    }

    static String renderCustomer(Customer c, String projection) {
        if ("summary".equals(projection)) return "{ \"name\": \"" + c.name + "\" }";
        return "{ \"name\": \"" + c.name + "\", \"email\": \"" + c.email + "\", \"city\": \"" + c.city + "\" }";
    }

    // @RepositoryRestResource(excerptProjection = CustomerSummary.class) applied to CustomerRepository
    // means the FULL shape is never used here -- the excerpt kicks in automatically for embedding.
    static String renderOrder(Order o) {
        String embeddedCustomer = renderCustomer(o.customer, "summary"); // excerpt projection, not caller-selected
        return "{ \"status\": \"" + o.status + "\", \"customer\": " + embeddedCustomer + " }";
    }
}

class Customer {
    String id, name, email, city;
    Customer(String id, String name, String email, String city) { this.id = id; this.name = name; this.email = email; this.city = city; }
}
class Order {
    String id; Customer customer; String status;
    Order(String id, Customer customer, String status) { this.id = id; this.customer = customer; this.status = status; }
}
```

How to run: `java ProjectionExcerptLevel3.java`

`renderCustomer(amara, null)` at the top level renders the full shape, since it was requested directly with no projection specified. `renderOrder` calls `renderCustomer(o.customer, "summary")` — the caller of `renderOrder` never asked for a summary; it was applied automatically because `Customer` is *embedded* inside the `Order` response, which is exactly what an excerpt projection configured via `excerptProjection = CustomerSummary.class` does in a real Spring Data REST application.

## 6. Walkthrough

Execution starts in `main` for Level 3. A `Customer` and an `Order` referencing that customer are built. Two conceptual requests run.

`GET /customers/c1` calls `renderCustomer(amara, null)` — no projection specified, so the full default shape is used, matching the entity's own top-level resource behavior from Level 1:

```
GET /customers/c1 -> { "name": "Amara", "email": "amara@example.com", "city": "Lagos" }
```

`GET /orders/o1` calls `renderOrder(order)`, which internally renders the embedded `customer` field using the `"summary"` shape — automatically, with no `?projection=summary` anywhere in the conceptual request:

```
GET /orders/o1 -> { "status": "PENDING", "customer": { "name": "Amara" } }
```

The distinction that matters here: requesting `/customers/c1` directly and requesting `/orders/o1` (which embeds that same customer) produce *different* representations of the identical underlying `Customer` entity — the full shape when it's the primary resource being requested, the lean excerpt shape when it's just supporting context for another resource. This keeps collection and nested responses from ballooning with full entity payloads for every embedded reference.

## 7. Gotchas & takeaways

> Gotcha: an excerpt projection applies *automatically* to every embedding of that entity across the whole API — if one particular embedding context actually needs more detail than the excerpt provides, there's no per-embedding override; the caller would need to follow the entity's own `_links.self` and fetch it directly at full detail instead.

> Gotcha: `@Projection` interfaces are matched to a domain type via their `types` attribute — a projection interface with a typo in its target type, or applied to the wrong entity, fails silently at the "projection not found" level rather than a compile error, since the matching happens at runtime via reflection.

- Named `@Projection`s give clients a choice of response shape per request, via the `projection` query parameter — opt-in, resource by resource.
- An excerpt projection (`excerptProjection = ...` on `@RepositoryRestResource`) is the automatic, opt-out shape used whenever that entity is embedded inside another resource's response.
- The same entity can render differently depending on whether it's the primary resource being requested or just embedded context for something else.
- Both mechanisms complete the resource-shaping toolbox started with `@JsonIgnore` and verb restrictions — together they let one entity serve many different API-facing shapes without duplicating the underlying data model.
