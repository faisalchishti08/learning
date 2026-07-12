---
card: microservices
gi: 76
slug: restful-apis-over-http
title: "RESTful APIs over HTTP"
---

## 1. What it is

REST (Representational State Transfer) is an architectural style for designing network APIs around **resources** — nouns like `orders` or `customers` — manipulated through a small, fixed set of HTTP verbs (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`), each request carrying everything the server needs to process it (statelessness), and responses using standard HTTP status codes to communicate outcome. In microservices, a RESTful HTTP API is the most common concrete implementation of the [synchronous request/response model](0075-synchronous-request-response-model.md): Service A issues an HTTP request to Service B's REST endpoint and waits for the HTTP response.

## 2. Why & when

Before REST became the default, service-to-service APIs were often built around RPC-style method calls with custom protocols, each requiring bespoke client libraries and tooling to understand. REST's appeal is that it reuses HTTP itself — a protocol every language, every tool, and every piece of infrastructure (load balancers, caches, browsers, curl) already understands natively — as the entire contract. A resource's URL, the verb applied to it, and the status code returned are enough information for any HTTP-aware tool to reason about the interaction, without needing to understand your specific application's internal logic.

Use RESTful HTTP APIs as the default choice for synchronous service-to-service communication in a microservices system, particularly when broad tooling compatibility, human-readability of the API (during debugging, via curl or a browser), and straightforward caching (leveraging standard HTTP caching semantics) matter. Reach for other protocols (gRPC, GraphQL) when you specifically need stronger typed contracts, binary efficiency, or more flexible querying than REST's resource model comfortably provides.

## 3. Core concept

A resource, identified by a URL, is manipulated through HTTP verbs; the verb plus the URL plus the status code fully describes the interaction, without any custom protocol layered on top.

```
GET    /orders/42        -> 200 OK   { id: 42, status: "PLACED" }   (read one resource)
POST   /orders           -> 201 Created                              (create a new resource)
PUT    /orders/42        -> 200 OK                                   (replace a resource)
DELETE /orders/42        -> 204 No Content                           (remove a resource)
```

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client sends an HTTP GET request to the orders resource URL and receives a JSON response with a 200 status code">
  <rect x="20" y="60" width="140" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="250" y="20" width="340" height="130" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService (REST API)</text>
  <text x="420" y="65" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">GET /orders/42</text>
  <text x="420" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">200 OK</text>
  <text x="420" y="105" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">{"id":42,"status":"PLACED"}</text>

  <line x1="160" y1="75" x2="250" y2="60" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="250" y1="95" x2="160" y2="100" stroke="#79c0ff" stroke-width="1.5"/>
</svg>

The verb and URL express the request; the status code and body express the outcome.

## 5. Runnable example

Scenario: a small in-memory `OrderService` "REST API," first modeled as a single crude `handle` method, then refactored into a proper verb + resource-path router (matching REST conventions), then extended to return correct status codes for both success and not-found cases.

### Level 1 — Basic

```java
// File: CrudeHandler.java -- ONE method with a giant if-chain -- not
// organized around REST conventions at all, just ad-hoc dispatch.
import java.util.*;

public class CrudeHandler {
    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static String handle(String action, int id) {
        if (action.equals("read")) return orders.getOrDefault(id, "NOT FOUND");
        if (action.equals("delete")) { orders.remove(id); return "deleted"; }
        return "unknown action";
    }

    public static void main(String[] args) {
        System.out.println(handle("read", 42));
        System.out.println(handle("delete", 42));
        System.out.println(handle("read", 42));
    }
}
```

**How to run:** `javac CrudeHandler.java && java CrudeHandler` (JDK 17+).

Expected output:
```
PLACED
deleted
NOT FOUND
```

There's no notion of a URL, a verb, or a status code here — just an arbitrary action string, which every client of this API would need custom documentation to understand.

### Level 2 — Intermediate

```java
// File: RestfulRouter.java -- restructure around REST conventions:
// a resource PATH and an HTTP VERB, matched by a simple router --
// exactly the shape a real Spring @RestController maps for you.
import java.util.*;

public class RestfulRouter {
    record HttpRequest(String method, String path) {}
    record HttpResponse(int status, String body) {}

    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));

    static HttpResponse route(HttpRequest req) {
        if (req.method().equals("GET") && req.path().startsWith("/orders/")) {
            int id = Integer.parseInt(req.path().substring("/orders/".length()));
            String status = orders.get(id);
            return new HttpResponse(200, "{\"id\":" + id + ",\"status\":\"" + status + "\"}");
        }
        if (req.method().equals("DELETE") && req.path().startsWith("/orders/")) {
            int id = Integer.parseInt(req.path().substring("/orders/".length()));
            orders.remove(id);
            return new HttpResponse(204, "");
        }
        return new HttpResponse(404, "");
    }

    public static void main(String[] args) {
        HttpResponse r1 = route(new HttpRequest("GET", "/orders/42"));
        System.out.println(r1.status() + " " + r1.body());

        HttpResponse r2 = route(new HttpRequest("DELETE", "/orders/42"));
        System.out.println(r2.status() + " (no body)");
    }
}
```

**How to run:** `javac RestfulRouter.java && java RestfulRouter` (JDK 17+).

Expected output:
```
200 {"id":42,"status":"PLACED"}
204 (no body)
```

### Level 3 — Advanced

```java
// File: WithProperStatusCodes.java -- add correct status codes for the
// NOT FOUND case (404, not 200 with a null status), and for successful
// creation (201, with a Location-style identifier in the body) -- both
// standard REST conventions this version now honors.
import java.util.*;

public class WithProperStatusCodes {
    record HttpRequest(String method, String path, String body) {}
    record HttpResponse(int status, String body) {}

    static Map<Integer, String> orders = new HashMap<>(Map.of(42, "PLACED"));
    static int nextId = 43;

    static HttpResponse route(HttpRequest req) {
        if (req.method().equals("GET") && req.path().startsWith("/orders/")) {
            int id = Integer.parseInt(req.path().substring("/orders/".length()));
            if (!orders.containsKey(id)) {
                return new HttpResponse(404, "{\"error\":\"order " + id + " not found\"}");
            }
            return new HttpResponse(200, "{\"id\":" + id + ",\"status\":\"" + orders.get(id) + "\"}");
        }
        if (req.method().equals("POST") && req.path().equals("/orders")) {
            int id = nextId++;
            orders.put(id, "PLACED");
            return new HttpResponse(201, "{\"id\":" + id + ",\"status\":\"PLACED\"}"); // 201 Created
        }
        if (req.method().equals("DELETE") && req.path().startsWith("/orders/")) {
            int id = Integer.parseInt(req.path().substring("/orders/".length()));
            if (!orders.containsKey(id)) return new HttpResponse(404, "{\"error\":\"order " + id + " not found\"}");
            orders.remove(id);
            return new HttpResponse(204, "");
        }
        return new HttpResponse(404, "{\"error\":\"no matching route\"}");
    }

    public static void main(String[] args) {
        HttpResponse created = route(new HttpRequest("POST", "/orders", "{}"));
        System.out.println(created.status() + " " + created.body());

        HttpResponse found = route(new HttpRequest("GET", "/orders/43", null));
        System.out.println(found.status() + " " + found.body());

        HttpResponse missing = route(new HttpRequest("GET", "/orders/999", null));
        System.out.println(missing.status() + " " + missing.body());
    }
}
```

**How to run:** `javac WithProperStatusCodes.java && java WithProperStatusCodes` (JDK 17+).

Expected output:
```
201 {"id":43,"status":"PLACED"}
200 {"id":43,"status":"PLACED"}
404 {"error":"order 999 not found"}
```

## 6. Walkthrough

1. **Level 1** — `handle("read", 42)` and `handle("delete", 42)` dispatch on an arbitrary `action` string with no relationship to HTTP at all. Any client of this API needs custom, out-of-band documentation to know that `"read"` means read and `"delete"` means delete — none of that is expressed in a standard, tool-recognizable way.
2. **Level 2 — REST shape introduced** — `route` takes an `HttpRequest` carrying a `method` (the HTTP verb) and a `path` (the resource URL), matching the [core concept](#3-core-concept)'s convention: `GET /orders/{id}` reads, `DELETE /orders/{id}` removes. `main` calls `route` with a `GET` request for `/orders/42`, which finds the order and returns `200` with a JSON body; then a `DELETE` request for the same path, which removes the order and returns `204 No Content` — the standard REST status code for "succeeded, nothing to return."
3. **Level 3 — correct status codes for edge cases** — `WithProperStatusCodes.route` adds a `POST /orders` branch (create a new resource) and, critically, checks `orders.containsKey(id)` before treating a `GET` or `DELETE` as successful, returning `404` with an error body when the id doesn't exist, instead of silently proceeding with a `null` status as Level 2 implicitly would have if given a missing id.
4. **Tracing `main`'s three calls** — `route(POST /orders)` assigns `id = 43` (from `nextId`, then increments it), stores `"PLACED"`, and returns `201 Created` with the new resource's representation in the body — the standard REST convention for a successful creation, distinct from `200`, signaling specifically "a new resource now exists." The second call, `route(GET /orders/43)`, finds the just-created order and returns `200` with its current state — confirming the created resource is now retrievable exactly as REST's uniform interface promises. The third call, `route(GET /orders/999)`, finds no entry for `999` in `orders`, and returns `404` with a JSON error body — the correct way to signal "resource does not exist," rather than, say, returning `200` with an empty or null body, which would force every client to inspect the body just to detect an error that the status code alone should have communicated.
5. **Why the status code carries meaning independent of the body** — any HTTP-aware tool — a load balancer, a monitoring dashboard, `curl -w '%{http_code}'`, a browser's network tab — can immediately tell, from the status code alone and without parsing or understanding the JSON body, whether `POST /orders` succeeded (`201`), a lookup succeeded (`200`), or a lookup failed (`404`). This is the practical payoff of REST reusing HTTP's existing, universally understood vocabulary instead of inventing a bespoke one.

## 7. Gotchas & takeaways

> **Gotcha:** returning `200 OK` for an operation that actually failed (with the real error status embedded only inside the JSON body) defeats the entire point of using HTTP status codes — it forces every client, and every piece of standard HTTP tooling, to parse the body just to know whether the call succeeded. Return the status code that actually matches the outcome, as `WithProperStatusCodes` does for its `404` case.

- REST reuses HTTP's existing, universally understood vocabulary — verbs, URLs, and status codes — as the entire API contract, rather than inventing a custom protocol.
- A resource is identified by its URL; the verb applied to that URL expresses the intended action (read, create, replace, remove).
- Match status codes to real HTTP semantics: `200` for a successful read, `201` for a successful creation, `204` for a successful action with no body to return, `404` for a resource that doesn't exist.
- REST's [statelessness](0075-synchronous-request-response-model.md) principle means every request should carry everything the server needs — no server-side session state implicitly required between requests.
- See [HTTP verbs & status code semantics](0078-http-verbs-status-code-semantics.md) and the [Richardson Maturity Model](0079-richardson-maturity-model.md) for a deeper look at what distinguishes a truly RESTful API from one that merely uses HTTP as a transport.
