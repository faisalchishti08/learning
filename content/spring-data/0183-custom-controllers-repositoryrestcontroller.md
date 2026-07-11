---
card: spring-data
gi: 183
slug: custom-controllers-repositoryrestcontroller
title: "Custom controllers (@RepositoryRestController)"
---

## 1. What it is

`@RepositoryRestController` marks a hand-written controller as living alongside Spring Data REST's auto-generated endpoints, sharing its base path, content negotiation, and HAL serialization conventions — rather than being a fully separate `@RestController` bolted on beside the generated API. This is the final card in this section, and the natural escape hatch once auto-generation and its configuration options (the previous several cards) aren't enough.

```java
@RepositoryRestController
class CustomerActivationController {
    private final CustomerRepository repository;
    CustomerActivationController(CustomerRepository repository) { this.repository = repository; }

    @PostMapping("/customers/{id}/activate")
    ResponseEntity<?> activate(@PathVariable String id) {
        // custom business logic that doesn't fit the generated CRUD shape
    }
}
```

## 2. Why & when

Every previous card in this section customized *generated* CRUD behavior. Some operations aren't CRUD at all — "activate this customer," "merge these two orders," "recalculate this customer's loyalty tier" — and forcing them through the generated endpoints (a `PATCH` with a magic field, say) is usually worse than just writing the endpoint.

Reach for `@RepositoryRestController` when:

- An operation is a genuine business action, not a create/read/update/delete on the entity's own fields.
- You want the custom endpoint to still return proper HAL responses (with `_links`) so it feels consistent with the rest of the generated API, rather than a plain, differently-shaped JSON response.
- The custom endpoint needs to live at (or near) the same base path as the generated resource, sharing its content negotiation setup, rather than being registered as a totally independent `@RestController`.

## 3. Core concept

```
 Generated (from the repository):
   GET/POST    /customers
   GET/PUT/PATCH/DELETE  /customers/{id}

 @RepositoryRestController
 class CustomerActivationController {
     @PostMapping("/customers/{id}/activate")
     ...
 }
   -> POST /customers/{id}/activate     -- hand-written, but shares HAL conventions with the rest

 Both respond with the SAME kind of HAL-shaped JSON, from the SAME effective base path.
```

`@RepositoryRestController` is a variant of `@RestController` scoped specifically to integrate with Spring Data REST's existing conventions, rather than a way to bypass them.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Generated CRUD endpoints and a hand-written custom controller share the same base path and HAL response conventions">
  <rect x="20" y="20" width="280" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Generated: GET/POST /customers</text>

  <rect x="340" y="20" width="280" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="47" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Custom: POST /customers/{id}/activate</text>

  <rect x="180" y="100" width="280" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="125" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Same HAL conventions, same base path</text>

  <line x1="160" y1="65" x2="280" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a16)"/>
  <line x1="480" y1="65" x2="360" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a16)"/>
  <defs><marker id="a16" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Generated CRUD and hand-written custom endpoints coexist, sharing the same HAL conventions and base path.

## 5. Runnable example

The scenario: adding a customer "activation" business action alongside the generated CRUD endpoints, evolving from forcing the action through a generic `PATCH` (the awkward workaround), to a proper custom endpoint returning a plain response, to a `@RepositoryRestController`-style endpoint that returns a full HAL response consistent with the rest of the generated API.

### Level 1 — Basic

Show the awkward workaround: forcing a business action through a generic field update, the anti-pattern this card's feature exists to avoid.

```java
import java.util.*;

public class CustomControllerLevel1 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        repo.save(new Customer("c1", "Amara", "PENDING"));

        // Forcing "activate this customer" through a generic PATCH-style field update.
        // Works, but the intent ("activate") is buried inside a generic status string mutation,
        // and any validation specific to activation has nowhere natural to live.
        Customer c = repo.findById("c1");
        c.status = "ACTIVE";
        repo.save(c);

        System.out.println("PATCH /customers/c1 { status: ACTIVE } -> status=" + repo.findById("c1").status);
    }
}

class Customer {
    String id, name, status;
    Customer(String id, String name, String status) { this.id = id; this.name = name; this.status = status; }
}

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    Customer save(Customer c) { store.put(c.id, c); return c; }
    Customer findById(String id) { return store.get(id); }
}
```

How to run: `java CustomControllerLevel1.java`

Nothing here validates that `PENDING -> ACTIVE` is a legal transition, or triggers whatever side effects "activation" should have (a welcome email, an audit entry) — the generic field-update endpoint has no natural place for that logic, which is exactly the gap a custom controller fills.

### Level 2 — Intermediate

Add a dedicated `activate` operation with its own validation and side effects, as a plain custom endpoint.

```java
import java.util.*;

public class CustomControllerLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        repo.save(new Customer("c1", "Amara", "PENDING"));

        CustomerActivationController controller = new CustomerActivationController(repo);
        System.out.println("POST /customers/c1/activate -> " + controller.activate("c1"));
        System.out.println("POST /customers/c1/activate -> " + controller.activate("c1")); // already active
    }
}

class Customer {
    String id, name, status;
    Customer(String id, String name, String status) { this.id = id; this.name = name; this.status = status; }
}

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    Customer save(Customer c) { store.put(c.id, c); return c; }
    Customer findById(String id) { return store.get(id); }
}

// @RestController-style custom endpoint -- not yet integrated with Spring Data REST's HAL conventions.
class CustomerActivationController {
    private final CustomerRepository repo;
    CustomerActivationController(CustomerRepository repo) { this.repo = repo; }

    // @PostMapping("/customers/{id}/activate")
    String activate(String id) {
        Customer c = repo.findById(id);
        if ("ACTIVE".equals(c.status)) return "409 Conflict: already active";
        c.status = "ACTIVE"; // the actual business action, with a real validation rule this time
        repo.save(c);
        return "200 OK: activated";
    }
}
```

How to run: `java CustomControllerLevel2.java`

`activate` now owns its own validation (rejecting a redundant activation with a proper `409`) and is the single, obvious place any future activation-specific logic belongs — but its response is a plain string, disconnected from the HAL-shaped JSON the rest of the generated API returns.

### Level 3 — Advanced

Upgrade to a `@RepositoryRestController`-style endpoint returning a proper HAL response, consistent with the generated resources — including `_links` back to the customer resource itself.

```java
import java.util.*;

public class CustomControllerLevel3 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepository();
        repo.save(new Customer("c1", "Amara", "PENDING"));

        CustomerActivationController controller = new CustomerActivationController(repo);
        System.out.println("POST /customers/c1/activate ->");
        System.out.println(controller.activate("c1"));
    }
}

class Customer {
    String id, name, status;
    Customer(String id, String name, String status) { this.id = id; this.name = name; this.status = status; }
}

class CustomerRepository {
    private final Map<String, Customer> store = new HashMap<>();
    Customer save(Customer c) { store.put(c.id, c); return c; }
    Customer findById(String id) { return store.get(id); }
}

// @RepositoryRestController -- integrates with the same HAL conventions the generated endpoints use.
class CustomerActivationController {
    private final CustomerRepository repo;
    CustomerActivationController(CustomerRepository repo) { this.repo = repo; }

    // @PostMapping("/customers/{id}/activate")
    String activate(String id) {
        Customer c = repo.findById(id);
        if ("ACTIVE".equals(c.status)) {
            return "{ \"status\": 409, \"error\": \"already active\", \"_links\": { \"self\": { \"href\": \"/customers/"
                + id + "\" } } }";
        }
        c.status = "ACTIVE";
        repo.save(c);
        // Response matches the SAME HAL shape a generated GET/PATCH on /customers/{id} would produce.
        return "{ \"name\": \"" + c.name + "\", \"status\": \"" + c.status + "\", \"_links\": { "
            + "\"self\": { \"href\": \"/customers/" + id + "\" } } }";
    }
}
```

How to run: `java CustomControllerLevel3.java`

The response body from this hand-written `activate` endpoint is structurally identical to what a generated `GET /customers/{id}` would return — the same `_links.self` convention, the same field naming — so a client consuming this API can't tell, just from the response shape, whether an endpoint was generated automatically or written by hand, which is exactly the point of `@RepositoryRestController` over a plain, disconnected `@RestController`.

## 6. Walkthrough

Execution starts in `main` for Level 3. A `Customer` is saved with `status=PENDING`. `controller.activate("c1")` is called.

Conceptually, the request is `POST /customers/c1/activate` with an empty body. Inside `activate`, the customer is fetched, its current status checked (not yet active, so the happy path proceeds), the status is mutated to `ACTIVE`, and it's saved back through the same repository the generated endpoints also use:

```json
{
  "name": "Amara",
  "status": "ACTIVE",
  "_links": { "self": { "href": "/customers/c1" } }
}
```

This response is deliberately shaped the same way a generated `GET /customers/c1` response would be — a client following `_links.self` from this activation response lands right back on the standard customer resource, with no special-casing needed for "this response came from a custom endpoint." In a real Spring Data REST application, `@RepositoryRestController` also automatically participates in the same content negotiation (returning HAL, or plain JSON, based on the request's `Accept` header) that the generated endpoints use, without the custom controller needing to configure that itself.

## 7. Gotchas & takeaways

> Gotcha: `@RepositoryRestController` methods are responsible for their *own* response shape — unlike the fully generated endpoints, nothing automatically wraps a plain returned object in HAL format; the controller method has to build (or explicitly return) the `_links`-bearing representation itself, as shown here, or the response will look inconsistent with the rest of the API.

> Gotcha: a `@RepositoryRestController` mapped to a path that collides with a generated endpoint (e.g. accidentally mapping `GET /customers/{id}` instead of a distinct sub-path like `/customers/{id}/activate`) can silently shadow or conflict with the auto-generated handler for that same path — keep custom endpoints on paths the generator doesn't already own.

- `@RepositoryRestController` is for genuine business actions that don't fit create/read/update/delete on an entity's own fields — the natural escape hatch once the generated CRUD and its various customizations (earlier cards) aren't enough.
- Unlike a plain `@RestController`, it's designed to integrate with Spring Data REST's existing base path and content negotiation, keeping custom and generated endpoints feeling like one consistent API.
- The controller method is responsible for constructing its own HAL-consistent response shape — that consistency isn't automatic, it has to be built deliberately.
- This closes out the Spring Data REST toolbox: expose (this section's earlier cards) shapes *what's there*; `@RepositoryRestController` adds *what generated CRUD can't express* — together they cover the full range from "pure CRUD, fully automatic" to "custom business logic, manually written but API-consistent."
