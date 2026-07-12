---
card: microservices
gi: 104
slug: restclient-spring-6-1-synchronous-fluent-client
title: "RestClient (Spring 6.1 synchronous fluent client)"
---

## 1. What it is

`RestClient`, introduced in Spring Framework 6.1 (Spring Boot 3.2), is Spring's modern synchronous HTTP client — designed to combine [`RestTemplate`](0102-resttemplate-legacy-synchronous-client.md)'s straightforward blocking execution model with [`WebClient`](0103-webclient-reactive-synchronous-client.md)'s clean, fluent builder API, minus the reactive `Mono`/`Flux` wrapping that only matters if you're actually building a non-blocking pipeline. A single, consistent method chain — `.get().uri(...).retrieve().body(Order.class)` — replaces `RestTemplate`'s dozen separately-named convenience methods, while returning plain objects directly rather than requiring `.block()`.

## 2. Why & when

`RestTemplate`'s many similarly-named methods (`getForObject`, `getForEntity`, `postForObject`, `postForEntity`...) require memorizing which one fits your specific verb-and-shape combination. `WebClient`'s fluent chain is genuinely pleasant to use, but wraps every result in `Mono`/`Flux`, forcing every caller in a blocking codebase to append `.block()` — extra ceremony with no actual benefit if the calling code was never going to be reactive in the first place. `RestClient` was built specifically to close this gap: `WebClient`'s fluent chain style, without the reactive wrapper, returning results directly for genuinely synchronous callers.

Use `RestClient` as the default choice for new synchronous Spring service-to-service calls — Spring's own guidance is to prefer it over `RestTemplate` for new code, and over forcing `WebClient` with `.block()` when the calling code is fundamentally blocking anyway. Reach for `WebClient` specifically when the calling code is genuinely reactive throughout (see [Spring WebFlux](0101-spring-webflux-for-reactive-non-blocking-endpoints.md)).

## 3. Core concept

One consistent fluent chain — verb, URI, retrieve, body type — covers every call shape, returning the result directly, with no reactive wrapper and no separately-named method to look up.

```java
Order order = restClient.get()
    .uri("/orders/{id}", 42)
    .retrieve()
    .body(Order.class);              // returns Order DIRECTLY -- no .block() needed

ResponseEntity<Order> response = restClient.post()
    .uri("/orders")
    .body(createRequest)
    .retrieve()
    .toEntity(Order.class);          // full response, when you need status/headers too
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestClient combines WebClient's fluent chain syntax with RestTemplate's direct, blocking return values, avoiding both RestTemplate's many separately-named methods and WebClient's reactive Mono wrapper">
  <rect x="20" y="20" width="180" height="100" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">RestTemplate</text>
  <text x="110" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">many named methods</text>
  <text x="110" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">direct return, blocking</text>

  <rect x="230" y="20" width="180" height="100" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">WebClient</text>
  <text x="320" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">fluent chain</text>
  <text x="320" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Mono/Flux, needs .block()</text>

  <rect x="440" y="20" width="180" height="100" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">RestClient</text>
  <text x="530" y="65" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">fluent chain</text>
  <text x="530" y="82" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">direct return, blocking</text>
</svg>

`RestClient` takes the best trait from each of its two predecessors.

## 5. Runnable example

Scenario: an order-lookup-and-create client, first with `RestTemplate`-style separately-named methods for comparison, then rewritten with `RestClient`'s single consistent fluent chain covering both the GET and POST cases, then extended to add a custom error handler configured once on the client and applied consistently to every call made through it.

### Level 1 — Basic

```java
// File: RestTemplateForComparison.java -- TWO separately-named methods
// for GET vs POST -- the pattern RestClient's single chain replaces.
import java.util.*;

public class RestTemplateForComparison {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
    static int nextId = 43;

    static Order getForObject(int id) { return orders.get(id); }
    static Order postForObject(String sku) {
        Order created = new Order(nextId++, "PLACED");
        orders.put(created.id(), created);
        return created;
    }

    public static void main(String[] args) {
        System.out.println("GET: " + getForObject(42));
        System.out.println("POST: " + postForObject("widget"));
    }
}
```

**How to run:** `javac RestTemplateForComparison.java && java RestTemplateForComparison` (JDK 17+).

Expected output:
```
GET: Order[id=42, status=PLACED]
POST: Order[id=43, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: RestClientFluentChain.java -- ONE consistent fluent chain shape
// covers BOTH the GET and the POST -- no separately-named methods, no
// Mono wrapper, direct return values.
import java.util.*;

public class RestClientFluentChain {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
    static int nextId = 43;

    static class SimulatedRestClient {
        RequestBuilder get() { return new RequestBuilder("GET"); }
        RequestBuilder post() { return new RequestBuilder("POST"); }

        class RequestBuilder {
            String verb; String uri; Object body;
            RequestBuilder(String verb) { this.verb = verb; }
            RequestBuilder uri(String template, Object... args) { uri = String.format(template.replace("{id}", "%s"), args); return this; }
            RequestBuilder body(Object body) { this.body = body; return this; }
            RequestBuilder retrieve() { return this; } // in real RestClient, a distinct step; simplified here
            Order bodyAsOrder() { // .body(Order.class) collapsed for brevity
                if (verb.equals("GET")) {
                    int id = Integer.parseInt(uri.substring(uri.lastIndexOf('/') + 1));
                    return orders.get(id);
                }
                Order created = new Order(nextId++, "PLACED");
                orders.put(created.id(), created);
                return created;
            }
        }
    }

    public static void main(String[] args) {
        SimulatedRestClient restClient = new SimulatedRestClient();

        Order found = restClient.get().uri("/orders/{id}", 42).retrieve().bodyAsOrder(); // SAME chain shape
        System.out.println("GET (fluent): " + found);

        Order created = restClient.post().uri("/orders").body("widget").retrieve().bodyAsOrder(); // SAME chain shape
        System.out.println("POST (fluent): " + created);
    }
}
```

**How to run:** `javac RestClientFluentChain.java && java RestClientFluentChain` (JDK 17+).

Expected output:
```
GET (fluent): Order[id=42, status=PLACED]
POST (fluent): Order[id=43, status=PLACED]
```

### Level 3 — Advanced

```java
// File: WithCentralizedErrorHandler.java -- configure ONE error handler
// ON THE CLIENT itself (not per call site) -- every call made through
// this client automatically applies the SAME error-handling policy.
import java.util.*;
import java.util.function.*;

public class WithCentralizedErrorHandler {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static class OrderNotFoundException extends RuntimeException {
        OrderNotFoundException(int id) { super("no order with id " + id); }
    }

    static class SimulatedRestClient {
        Function<Integer, RuntimeException> notFoundHandler; // configured ONCE, at client build time

        SimulatedRestClient(Function<Integer, RuntimeException> notFoundHandler) {
            this.notFoundHandler = notFoundHandler;
        }

        RequestBuilder get() { return new RequestBuilder(); }
        class RequestBuilder {
            String uri;
            RequestBuilder uri(String template, Object... args) { uri = String.format(template.replace("{id}", "%s"), args); return this; }
            Order retrieveBodyAsOrder() {
                int id = Integer.parseInt(uri.substring(uri.lastIndexOf('/') + 1));
                Order order = orders.get(id);
                if (order == null) throw notFoundHandler.apply(id); // the CENTRALIZED policy applied here
                return order;
            }
        }
    }

    public static void main(String[] args) {
        // ONE place configures how "not found" is handled for EVERY call through this client
        SimulatedRestClient restClient = new SimulatedRestClient(id -> new OrderNotFoundException(id));

        Order found = restClient.get().uri("/orders/{id}", 42).retrieveBodyAsOrder();
        System.out.println("Found: " + found);

        try {
            restClient.get().uri("/orders/{id}", 999).retrieveBodyAsOrder();
        } catch (OrderNotFoundException e) {
            System.out.println("Caught (via centralized handler): " + e.getMessage());
        }
    }
}
```

**How to run:** `javac WithCentralizedErrorHandler.java && java WithCentralizedErrorHandler` (JDK 17+).

Expected output:
```
Found: Order[id=42, status=PLACED]
Caught (via centralized handler): no order with id 999
```

## 6. Walkthrough

1. **Level 1** — `getForObject` and `postForObject` are two independently-named methods, each with its own implementation shape, standing in for `RestTemplate`'s convention of a separately-named method per verb. `main` calls both and prints their results — functionally correct, but requiring two entirely different method names for what are conceptually similar "make a call, get an object back" operations.
2. **Level 2 — one consistent chain for both verbs** — `SimulatedRestClient.get()` and `.post()` both return the *same* `RequestBuilder` type, and both are followed by the identical `.uri(...).retrieve().bodyAsOrder()` chain shape. `main` calls `restClient.get().uri(...).retrieve().bodyAsOrder()` for the GET case and `restClient.post().uri(...).body(...).retrieve().bodyAsOrder()` for the POST case — structurally the same pattern, just starting with a different verb method, and both return the resolved `Order` object *directly*, with no `.block()` or `Mono` wrapper anywhere.
3. **Level 3 — centralizing error-handling policy on the client** — `SimulatedRestClient`'s constructor now takes a `notFoundHandler` function, configured *once* when the client is built, rather than each call site independently deciding what to do when an order isn't found. `RequestBuilder.retrieveBodyAsOrder` checks if the looked-up order is `null` and, if so, calls `notFoundHandler.apply(id)` to construct the exception to throw — using whatever policy was configured on the client as a whole.
4. **Tracing `main`'s two calls** — `restClient.get().uri("/orders/{id}", 42).retrieveBodyAsOrder()` finds order 42 and returns it directly, printed as "Found." The second call, for id `999`, finds nothing in `orders`; `order == null` is true, so `notFoundHandler.apply(999)` is called, which (per the lambda passed into the constructor in `main`) constructs `new OrderNotFoundException(999)`, and that gets thrown — caught by `main`'s `try`/`catch` and printed.
5. **Why centralizing this on the client matters** — in a real Spring application, `RestClient`'s builder supports configuring a `defaultStatusHandler` (or similar) once, when the `RestClient` bean itself is constructed, so every call made through that one client instance automatically applies the same policy for translating specific HTTP status codes into specific, meaningful exceptions — rather than every individual call site needing to remember to check the status and throw the right thing itself. This centralization is exactly the kind of consistency-by-construction benefit a well-designed fluent client API provides over ad-hoc, per-call-site error handling.

## 7. Gotchas & takeaways

> **Gotcha:** despite `RestClient`'s fluent, chain-based syntax looking superficially similar to `WebClient`'s, mixing up which one you're holding matters — calling `.retrieve().body(Order.class)` on a `RestClient` blocks and returns an `Order` directly, while the equivalent on a `WebClient` returns `Mono<Order>`, requiring `.block()` or subscription. Know which client type a given variable actually is; the similar-looking chains can mask a real behavioral difference.

- `RestClient` (Spring 6.1+) combines `WebClient`'s clean fluent chain syntax with `RestTemplate`'s direct, synchronous return values — no reactive wrapper, no dozen separately-named convenience methods.
- Prefer `RestClient` over `RestTemplate` for new synchronous Spring service-to-service calls — it's Spring's current recommended default.
- A single, consistently-shaped chain (`.get()/.post()/...().uri(...).retrieve().body(Type.class)`) covers every call, rather than requiring a differently-named method per verb-and-shape combination.
- Configure error-handling policy once, on the client itself, rather than duplicating status-checking logic at every individual call site.
- See [`RestTemplate`](0102-resttemplate-legacy-synchronous-client.md) and [`WebClient`](0103-webclient-reactive-synchronous-client.md) for the two predecessor clients `RestClient` was designed to improve on.
