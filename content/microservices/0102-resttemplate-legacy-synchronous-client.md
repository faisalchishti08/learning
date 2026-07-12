---
card: microservices
gi: 102
slug: resttemplate-legacy-synchronous-client
title: "RestTemplate (legacy synchronous client)"
---

## 1. What it is

`RestTemplate` was Spring's original synchronous HTTP client, built around methods like `getForObject`, `postForEntity`, and the more general `exchange`, each taking a URI, an HTTP method, and the expected response type. It has been in Spring's maintenance mode since Spring 5 — no new features are being added — with Spring's own documentation directing new development toward [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md) instead. It remains fully supported for existing code, but understanding *why* it was superseded clarifies what `RestClient` actually improved on.

## 2. Why & when

`RestTemplate`'s API grew a large surface area over time — separate methods for different combinations of "give me the object" vs. "give me the full `ResponseEntity`" vs. "give me control over the method" (`getForObject`, `getForEntity`, `postForObject`, `postForEntity`, `exchange`, `execute`), each with multiple overloads for URI templates, variables, and headers. This breadth makes the class powerful but not especially discoverable or pleasant to chain fluently — you often need to already know which of a dozen similarly-named methods fits your specific case.

You'll most often encounter `RestTemplate` maintaining existing Spring codebases that predate `RestClient` (introduced in Spring Framework 6.1 / Spring Boot 3.2). For new code, prefer `RestClient`'s more modern fluent builder API, which achieves the same synchronous, blocking behavior with a cleaner, more consistently chainable interface. This topic exists to help you read and maintain `RestTemplate`-based code you'll still encounter, not to recommend starting new code with it.

## 3. Core concept

`RestTemplate`'s method name itself encodes both the HTTP verb and the shape of what you want back — a naming convention that's precise but requires memorizing which combination you need.

```java
Order order = restTemplate.getForObject("/orders/{id}", Order.class, 42);          // GET, just the body
ResponseEntity<Order> resp = restTemplate.getForEntity("/orders/{id}", Order.class, 42); // GET, full response incl. headers/status
ResponseEntity<Order> created = restTemplate.postForEntity("/orders", request, Order.class); // POST
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestTemplate offers separate, specifically-named methods for each combination of HTTP verb and desired response shape, unlike a single fluent builder chain">
  <rect x="20" y="20" width="180" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getForObject(...)</text>
  <rect x="230" y="20" width="180" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">getForEntity(...)</text>
  <rect x="440" y="20" width="180" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">postForEntity(...)</text>
  <rect x="20" y="85" width="600" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="112" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">exchange(uri, method, request, responseType) -- ONE general-purpose method covering everything</text>
</svg>

Several specifically-named convenience methods, plus one general-purpose `exchange` covering everything they don't.

## 5. Runnable example

Scenario: an order client, first modeled with `RestTemplate`-style separately-named convenience methods to make its API surface concrete, then using its general-purpose `exchange`-style method for a case the convenience methods don't directly cover, then extended to show handling an error response, which requires checking `ResponseEntity`'s status explicitly rather than getting an object directly.

### Level 1 — Basic

```java
// File: RestTemplateConvenienceMethods.java -- model RestTemplate's
// SEPARATELY NAMED convenience methods for different verb/shape combos.
import java.util.*;

public class RestTemplateConvenienceMethods {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class SimulatedRestTemplate {
        Order getForObject(String uri, int id) { // just the body
            return orders.get(id);
        }
        Map<String, Object> getForEntity(String uri, int id) { // full "response entity": status + body
            Order body = orders.get(id);
            return Map.of("status", 200, "body", body);
        }
    }

    public static void main(String[] args) {
        SimulatedRestTemplate restTemplate = new SimulatedRestTemplate();
        Order order = restTemplate.getForObject("/orders/{id}", 42);
        System.out.println("getForObject result: " + order);

        Map<String, Object> entity = restTemplate.getForEntity("/orders/{id}", 42);
        System.out.println("getForEntity result: status=" + entity.get("status") + ", body=" + entity.get("body"));
    }
}
```

**How to run:** `javac RestTemplateConvenienceMethods.java && java RestTemplateConvenienceMethods` (JDK 17+).

Expected output:
```
getForObject result: Order[id=42, status=PLACED]
getForEntity result: status=200, body=Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: RestTemplateExchange.java -- use the GENERAL-PURPOSE exchange
// method for a case the named convenience methods don't cover directly:
// a DELETE that also needs to read the response body.
import java.util.*;

public class RestTemplateExchange {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class SimulatedRestTemplate {
        Map<String, Object> exchange(String uri, String method, int id) { // the general-purpose escape hatch
            if (method.equals("DELETE")) {
                Order removed = orders.remove(id);
                return Map.of("status", removed != null ? 200 : 404, "body", removed);
            }
            throw new UnsupportedOperationException();
        }
    }

    public static void main(String[] args) {
        SimulatedRestTemplate restTemplate = new SimulatedRestTemplate();
        Map<String, Object> response = restTemplate.exchange("/orders/{id}", "DELETE", 42);
        System.out.println("exchange (DELETE) result: status=" + response.get("status") + ", removed=" + response.get("body"));
    }
}
```

**How to run:** `javac RestTemplateExchange.java && java RestTemplateExchange` (JDK 17+).

Expected output:
```
exchange (DELETE) result: status=200, removed=Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: HandlingErrorResponses.java -- checking a ResponseEntity's
// STATUS explicitly, since RestTemplate's default behavior throws for
// 4xx/5xx responses -- here modeled as a status check the caller must
// perform, matching how getForEntity-style access works.
import java.util.*;

public class HandlingErrorResponses {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class RestClientResponseException extends RuntimeException {
        int statusCode;
        RestClientResponseException(int statusCode) { super("request failed with status " + statusCode); this.statusCode = statusCode; }
    }

    static class SimulatedRestTemplate {
        Map<String, Object> getForEntity(int id) {
            Order body = orders.get(id);
            if (body == null) {
                throw new RestClientResponseException(404); // RestTemplate throws by default on 4xx/5xx
            }
            return Map.of("status", 200, "body", body);
        }
    }

    public static void main(String[] args) {
        SimulatedRestTemplate restTemplate = new SimulatedRestTemplate();

        Map<String, Object> found = restTemplate.getForEntity(42);
        System.out.println("Found: status=" + found.get("status") + ", body=" + found.get("body"));

        try {
            restTemplate.getForEntity(999);
        } catch (RestClientResponseException e) {
            System.out.println("Caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `javac HandlingErrorResponses.java && java HandlingErrorResponses` (JDK 17+).

Expected output:
```
Found: status=200, body=Order[id=42, status=PLACED]
Caught: request failed with status 404
```

## 6. Walkthrough

1. **Level 1** — `getForObject` returns just the `Order` directly; `getForEntity` returns a map standing in for Spring's real `ResponseEntity<Order>`, carrying both the status and the body together. `main` calls both against the same order and prints the difference: `getForObject`'s result is the bare order, while `getForEntity`'s result exposes the status code alongside it — this is the core distinction `RestTemplate`'s naming convention encodes: do you want just the payload, or the full response context too?
2. **Level 2 — reaching for `exchange` when a convenience method doesn't fit** — `exchange` takes the URI, an explicit method string, and the id, and handles the `DELETE` case, which none of `RestTemplate`'s more specifically-named convenience methods cover directly (there's no `deleteForEntity` that also returns a body). `main` calls `exchange` with `"DELETE"`, which removes order 42 from `orders` and returns a status/body map reflecting the removal — demonstrating `exchange`'s role as the general-purpose fallback for any HTTP interaction the named convenience methods don't directly support.
3. **Level 3 — RestTemplate's default error-handling behavior** — `getForEntity` here explicitly throws `RestClientResponseException` when the requested order isn't found, mirroring `RestTemplate`'s real default behavior: by default, it throws an exception for any 4xx or 5xx response, rather than quietly returning a `ResponseEntity` with an error status for the caller to check — a meaningful difference from, say, `RestClient`'s more configurable default behavior.
4. **Tracing `main`'s two calls** — `restTemplate.getForEntity(42)` finds the order and returns normally, printing its status and body. `restTemplate.getForEntity(999)` finds nothing in `orders`, and the `if (body == null)` branch throws `RestClientResponseException(404)` — `main`'s `try`/`catch` catches it and prints the caught message. This is the behavior every `RestTemplate` caller needs to be aware of: a failed downstream call surfaces as a thrown exception by default, requiring a `try`/`catch` around the call site (or a custom `ResponseErrorHandler` configured on the `RestTemplate` instance) rather than an object you can inspect for a status code without exception handling.
5. **Why this matters when reading legacy code** — encountering a `try`/`catch RestClientResponseException` (or its subclasses like `HttpClientErrorException`/`HttpServerErrorException`) around a `RestTemplate` call is the normal, expected pattern in code written against this API — it's not an unusual defensive measure, but the standard way `RestTemplate`'s default error-handling model requires callers to handle non-2xx responses.

## 7. Gotchas & takeaways

> **Gotcha:** a single `RestTemplate` instance is thread-safe and meant to be shared and reused (typically as a single Spring bean) across your whole application — creating a new `RestTemplate` per request throws away connection pooling benefits (see [connection pooling & keep-alive](0095-connection-pooling-keep-alive.md)) entirely, since each new instance starts with a cold connection pool.

- `RestTemplate` is Spring's original synchronous HTTP client, in maintenance mode since Spring 5 — fully supported for existing code, but not recommended for new development.
- Its API surface is organized around separately-named methods per verb/response-shape combination (`getForObject`, `getForEntity`, `postForEntity`, etc.), plus a general-purpose `exchange` method for cases those don't cover.
- `RestTemplate` throws an exception by default for 4xx/5xx responses, requiring explicit `try`/`catch` handling at each call site (or a custom error handler configured centrally).
- Share and reuse a single `RestTemplate` instance (typically as a Spring bean) rather than constructing a new one per call, to preserve connection pooling benefits.
- See [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md) for the modern, fluent-builder synchronous client that Spring's documentation now recommends in `RestTemplate`'s place for new code.
