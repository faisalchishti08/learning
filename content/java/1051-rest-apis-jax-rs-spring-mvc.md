---
card: java
gi: 1051
slug: rest-apis-jax-rs-spring-mvc
title: "REST APIs (JAX-RS, Spring MVC)"
---

## 1. What it is

A REST API exposes application functionality over HTTP using resource-oriented URLs and standard HTTP methods — `GET /orders/42` to retrieve, `POST /orders` to create, `PUT`/`PATCH` to update, `DELETE` to remove — with request and response bodies typically encoded as JSON. Spring MVC (`@RestController`, `@GetMapping`, etc., covered briefly in [Spring Boot](1047-spring-boot.md)) and JAX-RS (`@Path`, `@GET`, covered in [Jakarta EE overview](1048-jakarta-ee-overview.md)) are the two dominant Java frameworks for building these endpoints, each providing annotations that map incoming HTTP requests to Java methods and automatically convert Java objects to/from JSON for the request and response bodies.

## 2. Why & when

Handling raw HTTP requests directly — parsing the URL path, reading headers, manually reading and parsing a request body's bytes, manually writing a correctly-formatted response — is a substantial amount of repetitive infrastructure work that has nothing to do with an application's actual business logic. Both Spring MVC and JAX-RS exist to eliminate that boilerplate: annotate a method with the HTTP method and path it should handle, declare its parameters (path variables, query parameters, the deserialized request body), and the framework handles routing the incoming request to that method, converting its return value into a properly-formatted HTTP response — including automatic JSON conversion via Jackson (see [JSON (Jackson, Gson)](1050-json-jackson-gson.md)), correct status codes, and content-type headers.

Design REST endpoints around **resources** (nouns: `/orders`, `/orders/{id}`) rather than actions (verbs: `/getOrder`, `/createOrder`) — the HTTP method itself expresses the action (`GET` for retrieval, `POST` for creation), which is what makes REST APIs predictable and consistent across different endpoints. Use appropriate HTTP status codes to communicate outcomes precisely: `200 OK` for a successful retrieval, `201 Created` for a successful creation, `404 Not Found` for a missing resource, `400 Bad Request` for invalid input — rather than always returning `200` with an error described only in the response body.

## 3. Core concept

```java
import org.springframework.web.bind.annotation.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;

record Order(String id, double total) {}

@RestController
@RequestMapping("/orders")
class OrderController {
    @GetMapping("/{id}")
    ResponseEntity<Order> getOrder(@PathVariable String id) {
        Order order = findOrder(id); // hypothetical lookup
        if (order == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).build(); // 404, precise and explicit
        }
        return ResponseEntity.ok(order); // 200 OK, with the Order serialized to JSON automatically
    }

    @PostMapping
    ResponseEntity<Order> createOrder(@RequestBody Order newOrder) {
        Order saved = save(newOrder); // hypothetical persistence
        return ResponseEntity.status(HttpStatus.CREATED).body(saved); // 201 Created
    }

    Order findOrder(String id) { return null; } // stub
    Order save(Order order) { return order; }   // stub
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A GET request to /orders/42 routed to getOrder, returning 200 with a JSON body if found or 404 if not found, and a POST request to /orders routed to createOrder returning 201 Created">
  <rect x="20" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GET /orders/42</text>

  <rect x="250" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">getOrder("42")</text>

  <rect x="450" y="5" width="160" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="25" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">200 OK + JSON body</text>
  <rect x="450" y="45" width="160" height="30" rx="5" fill="#1c2430" stroke="#f0883e"/>
  <text x="530" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">404 Not Found</text>

  <rect x="20" y="120" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="141" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">POST /orders</text>
  <rect x="250" y="120" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="141" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">createOrder(body)</text>
  <rect x="450" y="120" width="160" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="530" y="141" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">201 Created + JSON body</text>

  <line x1="200" y1="37" x2="250" y2="37" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="390" y1="30" x2="450" y2="20" stroke="#6db33f" marker-end="url(#a)"/>
  <line x1="390" y1="45" x2="450" y2="60" stroke="#f0883e" marker-end="url(#a)"/>
  <line x1="200" y1="137" x2="250" y2="137" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="390" y1="137" x2="450" y2="137" stroke="#6db33f" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The HTTP method and path route to a specific handler method, whose response is translated into a precise status code and JSON body.

## 5. Runnable example

Scenario: an order-lookup and creation API, evolving from a status-code-blind design into a properly resource-oriented, status-precise Spring MVC REST controller.

### Level 1 — Basic

```java
// File: src/main/java/com/example/OrderControllerBasic.java
package com.example;

import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;

record Order(String id, double total) {}

@RestController
public class OrderControllerBasic {
    private final Map<String, Order> orders = new HashMap<>();

    // Action-style endpoint (a verb in the URL) rather than resource-oriented,
    // and always returns 200 regardless of whether the order was actually found.
    @GetMapping("/getOrder")
    Order getOrder(@RequestParam String id) {
        return orders.get(id); // returns null (as an empty JSON body) if not found -- no clear signal
    }

    @PostMapping("/createOrder")
    Order createOrder(@RequestBody Order newOrder) {
        orders.put(newOrder.id(), newOrder);
        return newOrder; // always 200, even though a resource was just CREATED
    }
}
```

**How to run:** place in a Spring Boot project (see [Spring Boot](1047-spring-boot.md) for setup), run `mvn spring-boot:run`, then `curl -X POST http://localhost:8080/createOrder -H "Content-Type: application/json" -d '{"id":"o1","total":19.99}'` followed by `curl "http://localhost:8080/getOrder?id=missing"`.

Expected output (from the `POST`, HTTP status `200`):
```
{"id":"o1","total":19.99}
```

Expected output (from the `GET` with a missing id, HTTP status still `200`, empty body):
```

```

The URL uses verbs (`/getOrder`, `/createOrder`) instead of resource nouns, and — more importantly — looking up a non-existent order returns an HTTP `200` with an empty body rather than a clear `404`, forcing any client to inspect the (empty) body content just to determine whether the lookup actually succeeded.

### Level 2 — Intermediate

```java
// File: src/main/java/com/example/OrderControllerIntermediate.java
package com.example;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;

record Order(String id, double total) {}

@RestController
@RequestMapping("/orders") // resource-oriented base path
public class OrderControllerIntermediate {
    private final Map<String, Order> orders = new HashMap<>();

    @GetMapping("/{id}")
    ResponseEntity<Order> getOrder(@PathVariable String id) {
        Order order = orders.get(id);
        if (order == null) {
            return ResponseEntity.notFound().build(); // explicit 404
        }
        return ResponseEntity.ok(order); // explicit 200
    }

    @PostMapping
    ResponseEntity<Order> createOrder(@RequestBody Order newOrder) {
        orders.put(newOrder.id(), newOrder);
        return ResponseEntity.status(HttpStatus.CREATED).body(newOrder); // explicit 201
    }
}
```

**How to run:** run `mvn spring-boot:run`, then `curl -i -X POST http://localhost:8080/orders -H "Content-Type: application/json" -d '{"id":"o1","total":19.99}'` followed by `curl -i http://localhost:8080/orders/missing`.

Expected output (from the `POST`, relevant headers and body):
```
HTTP/1.1 201
Content-Type: application/json
{"id":"o1","total":19.99}
```

Expected output (from the `GET` on a missing id):
```
HTTP/1.1 404
```

The real-world concern added: the URL is now resource-oriented (`/orders`, `/orders/{id}`), and the status codes precisely communicate outcomes — `201 Created` for a successful creation and `404 Not Found` for a genuinely missing resource — letting a client determine the outcome from the status code alone, without needing to inspect the response body.

### Level 3 — Advanced

```java
// File: src/main/java/com/example/OrderControllerAdvanced.java
package com.example;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

record Order(String id, double total) {}
record ErrorResponse(String message) {}

@RestController
@RequestMapping("/orders")
public class OrderControllerAdvanced {
    private final Map<String, Order> orders = new HashMap<>();

    @GetMapping("/{id}")
    ResponseEntity<?> getOrder(@PathVariable String id) {
        Order order = orders.get(id);
        if (order == null) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                .body(new ErrorResponse("no order found with id: " + id));
        }
        return ResponseEntity.ok(order);
    }

    @PostMapping
    ResponseEntity<?> createOrder(@RequestBody Order newOrderRequest) {
        if (newOrderRequest.total() <= 0) {
            // 400 Bad Request: the request itself is invalid, distinct from a
            // missing resource (404) or a server-side failure (500).
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(new ErrorResponse("total must be positive"));
        }
        String generatedId = UUID.randomUUID().toString();
        Order saved = new Order(generatedId, newOrderRequest.total());
        orders.put(generatedId, saved);

        // Location header: standard REST practice pointing the client at the
        // newly-created resource's own URL, alongside the 201 status.
        return ResponseEntity
            .created(java.net.URI.create("/orders/" + generatedId))
            .body(saved);
    }
}
```

**How to run:** run `mvn spring-boot:run`, then `curl -i -X POST http://localhost:8080/orders -H "Content-Type: application/json" -d '{"id":"ignored","total":-5.0}'` followed by `curl -i -X POST http://localhost:8080/orders -H "Content-Type: application/json" -d '{"id":"ignored","total":19.99}'`.

Expected output (from the first `POST`, invalid total):
```
HTTP/1.1 400
{"message":"total must be positive"}
```

Expected output (from the second `POST`, valid total; the actual UUID will differ each run):
```
HTTP/1.1 201
Location: /orders/3fa85f64-5717-4562-b3fc-2c963f66afa6
{"id":"3fa85f64-5717-4562-b3fc-2c963f66afa6","total":19.99}
```

The production-flavored hard case: invalid input now produces a precise `400 Bad Request` with a descriptive error body, distinct from a `404` (missing resource) or a `500` (server failure) — and a successful creation includes a `Location` header pointing at the newly-created resource's own URL, a standard REST convention that lets a client immediately know where to `GET` the resource it just created.

## 6. Walkthrough

Tracing the second `POST /orders` request (with `total: 19.99`) in `OrderControllerAdvanced`:

1. Spring MVC's `DispatcherServlet` routes the incoming `POST /orders` request to `createOrder`, and deserializes the request body's JSON into a `newOrderRequest` object of type `Order` (via `@RequestBody`, using Jackson automatically — the `id` field from the request, `"ignored"`, is deserialized but will be discarded by the handler's own logic).
2. `newOrderRequest.total() <= 0` evaluates `19.99 <= 0`, which is `false`, so the validation-failure branch is skipped.
3. `UUID.randomUUID().toString()` generates a fresh, unique identifier for this new order — this is the *server's* chosen identifier, deliberately overriding whatever `id` value the client sent in the request body (which was `"ignored"`, reflecting that the client shouldn't be trusted to assign resource identifiers in this design).
4. `new Order(generatedId, newOrderRequest.total())` constructs the actual order to be saved, and `orders.put(generatedId, saved)` stores it in the in-memory map.
5. `ResponseEntity.created(URI.create("/orders/" + generatedId))` builds a response with status `201 Created` and a `Location` header set to the new resource's URL — this is what lets a client immediately know where to send a subsequent `GET` request to retrieve this exact order.
6. `.body(saved)` attaches the newly-created `Order` object as the response body, which Spring MVC's auto-configured Jackson integration serializes to JSON automatically. The complete response — status `201`, `Location` header, and JSON body — is sent back to the client in one coherent, standard-REST-practice response.

## 7. Gotchas & takeaways

> **Gotcha:** returning `200 OK` for every outcome (as in Level 1) forces every client to parse the response body just to determine success or failure — but the opposite extreme, inventing overly granular custom status codes for every possible situation, also hurts interoperability; stick to the well-established standard codes (`200`, `201`, `400`, `404`, `500`) whose meanings are already universally understood by HTTP clients and tooling.

- REST APIs organize around resources (nouns in the URL) with HTTP methods expressing the action, rather than encoding the action as a verb in the URL path itself.
- Spring MVC and JAX-RS both eliminate the boilerplate of manually parsing HTTP requests and building responses, automatically converting Java objects to/from JSON via an integrated library like Jackson (see [JSON (Jackson, Gson)](1050-json-jackson-gson.md)).
- Precise HTTP status codes (`200`, `201`, `400`, `404`) let a client determine the outcome without needing to inspect the response body's content — this is a core part of what makes an API genuinely RESTful rather than just "JSON over HTTP."
- A `Location` header on a `201 Created` response is a standard convention pointing the client at the newly-created resource's own URL.
- Server-generated identifiers (rather than trusting client-supplied ones) are a common and often necessary practice for resource creation, particularly when uniqueness or specific ID formats must be guaranteed.
- See [microservices basics](1053-microservices-basics.md) for how these same REST API design principles extend to communication *between* services in a distributed system, not just between a client and a single application.
