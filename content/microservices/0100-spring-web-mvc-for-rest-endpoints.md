---
card: microservices
gi: 100
slug: spring-web-mvc-for-rest-endpoints
title: "Spring Web MVC for REST endpoints"
---

## 1. What it is

Spring Web MVC (often just "Spring MVC") is Spring's original, [blocking](0087-blocking-vs-non-blocking-i-o.md), servlet-based web framework for building REST endpoints — the default choice when you add the `spring-boot-starter-web` dependency. A `@RestController` class with methods annotated `@GetMapping`, `@PostMapping`, and so on declares your API's routes; Spring handles matching an incoming HTTP request to the right method, converting its body into your method's parameter types, and converting your method's return value back into the HTTP response body.

## 2. Why & when

Building a REST endpoint by hand — parsing the raw HTTP request, matching the URL against your own routing logic, manually deserializing the body, manually serializing the response — is exactly the kind of repetitive boilerplate every one of your API's endpoints would otherwise need to duplicate. Spring MVC's annotation-driven routing collapses this to a method signature and a few annotations: the framework's `DispatcherServlet` handles request matching, and Spring's `HttpMessageConverter`s (JSON by default, via Jackson) handle serialization in both directions automatically.

Use Spring Web MVC as the default choice for any traditional, thread-per-request, blocking Spring Boot service — the vast majority of microservices don't need [Spring WebFlux](0101-spring-webflux-for-reactive-non-blocking-endpoints.md)'s reactive, non-blocking model, and Spring MVC's simpler, imperative programming style (plain method calls, ordinary stack traces, no reactive operator chains to learn) is easier to write and debug for most teams and most workloads.

## 3. Core concept

A `@RestController` method's signature, combined with its mapping annotation, fully declares one route; Spring wires incoming requests to the matching method and handles the data conversion on both ends automatically.

```java
@RestController
@RequestMapping("/orders")
class OrderController {

    @GetMapping("/{id}")
    Order getOrder(@PathVariable int id) { ... }     // GET /orders/{id}

    @PostMapping
    Order createOrder(@RequestBody CreateOrderRequest request) { ... }  // POST /orders
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming HTTP request is routed by DispatcherServlet to the matching annotated controller method, whose return value is converted back into the HTTP response body">
  <rect x="20" y="60" width="120" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="80" y="88" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET /orders/42</text>

  <rect x="200" y="40" width="180" height="90" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">DispatcherServlet</text>
  <text x="290" y="82" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">matches route, converts</text>
  <text x="290" y="97" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">body, calls method</text>

  <rect x="440" y="55" width="180" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderController</text>
  <text x="530" y="97" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">.getOrder(42)</text>

  <line x1="140" y1="85" x2="200" y2="85" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="380" y1="85" x2="440" y2="85" stroke="#8b949e" stroke-width="1.5"/>
</svg>

`DispatcherServlet` is the single entry point that routes every request to its matching annotated method.

## 5. Runnable example

Scenario: an order-lookup endpoint, first with hand-written routing logic (the boilerplate Spring MVC eliminates), then refactored to an annotation-style declaration with a simulated dispatcher that reads those annotations via reflection to route requests automatically, then extended to also handle request body deserialization for a POST endpoint, completing the picture of what `@RestController` provides.

### Level 1 — Basic

```java
// File: HandWrittenRouting.java -- manual routing logic: match the path
// and method YOURSELF, call the right handler YOURSELF.
import java.util.*;

public class HandWrittenRouting {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    static Order getOrder(int id) { return orders.get(id); }

    static Object dispatch(String method, String path) {
        if (method.equals("GET") && path.startsWith("/orders/")) {
            int id = Integer.parseInt(path.substring("/orders/".length()));
            return getOrder(id); // hand-wired: YOU have to know which method serves which route
        }
        return "404 Not Found";
    }

    public static void main(String[] args) {
        System.out.println(dispatch("GET", "/orders/42"));
    }
}
```

**How to run:** `javac HandWrittenRouting.java && java HandWrittenRouting` (JDK 17+).

Expected output:
```
Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: AnnotationStyleDispatch.java -- declare routes via ANNOTATIONS
// on a controller class; a simulated dispatcher reads them via
// reflection and routes automatically -- no hand-wired if-chain.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class AnnotationStyleDispatch {
    @Retention(RetentionPolicy.RUNTIME)
    @interface GetMapping { String value(); } // stands in for Spring's @GetMapping

    record Order(int id, String status) {}

    static class OrderController {
        Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

        @GetMapping("/orders/{id}")
        Order getOrder(int id) { return orders.get(id); }
    }

    static Object dispatch(Object controller, String method, String path) throws Exception {
        for (Method m : controller.getClass().getDeclaredMethods()) {
            GetMapping mapping = m.getAnnotation(GetMapping.class);
            if (mapping == null || !method.equals("GET")) continue;
            String template = mapping.value(); // e.g. "/orders/{id}"
            String prefix = template.substring(0, template.indexOf("{"));
            if (path.startsWith(prefix)) {
                int id = Integer.parseInt(path.substring(prefix.length()));
                return m.invoke(controller, id); // Spring's DispatcherServlet does exactly this kind of dispatch
            }
        }
        return "404 Not Found";
    }

    public static void main(String[] args) throws Exception {
        OrderController controller = new OrderController();
        System.out.println(dispatch(controller, "GET", "/orders/42"));
    }
}
```

**How to run:** `javac AnnotationStyleDispatch.java && java AnnotationStyleDispatch` (JDK 17+).

Expected output:
```
Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: WithRequestBodyDeserialization.java -- add a POST endpoint that
// deserializes a request BODY (simplified JSON parsing) into a method
// parameter -- completing what @RestController + @RequestBody provides.
import java.lang.annotation.*;
import java.lang.reflect.*;
import java.util.*;

public class WithRequestBodyDeserialization {
    @Retention(RetentionPolicy.RUNTIME) @interface GetMapping { String value(); }
    @Retention(RetentionPolicy.RUNTIME) @interface PostMapping { String value(); }

    record Order(int id, String status) {}
    record CreateOrderRequest(String sku) {}

    static class OrderController {
        Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
        int nextId = 43;

        @GetMapping("/orders/{id}")
        Order getOrder(int id) { return orders.get(id); }

        @PostMapping("/orders")
        Order createOrder(CreateOrderRequest request) { // deserialized from the request BODY
            Order created = new Order(nextId++, "PLACED");
            orders.put(created.id(), created);
            System.out.println("  [created order from sku=" + request.sku() + "]");
            return created;
        }
    }

    static CreateOrderRequest parseBody(String json) { // SIMPLIFIED JSON parsing -- Jackson does this for real
        String sku = json.replaceAll(".*\"sku\"\\s*:\\s*\"([^\"]+)\".*", "$1");
        return new CreateOrderRequest(sku);
    }

    static Object dispatch(Object controller, String method, String path, String body) throws Exception {
        for (Method m : controller.getClass().getDeclaredMethods()) {
            if (method.equals("GET") && m.isAnnotationPresent(GetMapping.class)) {
                String template = m.getAnnotation(GetMapping.class).value();
                String prefix = template.substring(0, template.indexOf("{"));
                if (path.startsWith(prefix)) {
                    int id = Integer.parseInt(path.substring(prefix.length()));
                    return m.invoke(controller, id);
                }
            }
            if (method.equals("POST") && m.isAnnotationPresent(PostMapping.class)) {
                String template = m.getAnnotation(PostMapping.class).value();
                if (path.equals(template)) {
                    CreateOrderRequest request = parseBody(body);
                    return m.invoke(controller, request);
                }
            }
        }
        return "404 Not Found";
    }

    public static void main(String[] args) throws Exception {
        OrderController controller = new OrderController();
        Object created = dispatch(controller, "POST", "/orders", "{\"sku\":\"widget\"}");
        System.out.println("Response: " + created);
    }
}
```

**How to run:** `javac WithRequestBodyDeserialization.java && java WithRequestBodyDeserialization` (JDK 17+).

Expected output:
```
  [created order from sku=widget]
Response: Order[id=43, status=PLACED]
```

## 6. Walkthrough

1. **Level 1** — `dispatch` contains a hand-written `if` chain checking method and path prefix directly, calling `getOrder` explicitly when they match. `main` calls `dispatch("GET", "/orders/42")` and gets back the matching order — but every new route would need its own hand-added branch in this same `if` chain, growing unboundedly as the API grows.
2. **Level 2 — annotation-driven dispatch** — `OrderController.getOrder` is now marked with a custom `@GetMapping("/orders/{id}")` annotation, and `dispatch` uses reflection (`controller.getClass().getDeclaredMethods()`) to *discover* which method handles which route, rather than having that mapping hard-coded into the dispatch logic itself. `main` calls `dispatch(controller, "GET", "/orders/42")`, and the loop finds `getOrder`'s `@GetMapping` annotation, extracts the path prefix, matches it against the incoming path, parses out the `id`, and invokes the method via `m.invoke(controller, id)` — this is structurally exactly what Spring's real `DispatcherServlet` does, just simplified.
3. **Level 3 — adding request body deserialization** — `createOrder` is added with a `@PostMapping("/orders")` annotation and takes a `CreateOrderRequest` parameter instead of a path variable. `parseBody` performs a simplified regex-based extraction of the `sku` field from a raw JSON string, standing in for what Spring's real Jackson-based `HttpMessageConverter` does automatically and much more robustly. `dispatch` now has two branches — one for `GET` methods with `@GetMapping` (as in Level 2), and a new one for `POST` methods with `@PostMapping`, which calls `parseBody` on the incoming request body before invoking the target method.
4. **Tracing `main`'s call** — `dispatch(controller, "POST", "/orders", "{\"sku\":\"widget\"}")` matches the second branch: `template` is `"/orders"`, which equals `path`, so `parseBody("{\"sku\":\"widget\"}")` runs, extracting `"widget"` via the regex and constructing a `CreateOrderRequest("widget")`. `m.invoke(controller, request)` then calls `createOrder` with that parsed request object — `createOrder` prints its diagnostic line, constructs a new `Order` with `id=43` (from `nextId`, incrementing it), stores it, and returns it. `main` prints the final response.
5. **What this models about real Spring MVC** — in a real Spring Boot application, none of this reflection-based dispatch logic or manual JSON regex-parsing would be hand-written at all — `@RestController`, `@GetMapping`, `@PostMapping`, and `@RequestBody` are processed by Spring's own `DispatcherServlet` and `HttpMessageConverter` infrastructure automatically, at startup and per-request respectively. This example's simplified reflection-based dispatcher exists purely to make visible the *mechanism* Spring is actually performing under the hood, which is otherwise entirely hidden behind the annotations.

## 7. Gotchas & takeaways

> **Gotcha:** Spring MVC's blocking, thread-per-request model (see [blocking vs non-blocking I/O](0087-blocking-vs-non-blocking-i-o.md)) means each in-flight request occupies a thread from the servlet container's thread pool for its full duration — under very high concurrency with slow downstream calls, this is exactly the resource-exhaustion risk covered in [cascading failures from synchronous coupling](0099-cascading-failures-from-synchronous-coupling.md). Spring MVC is the right default for most services, but it isn't immune to that failure mode.

- `@RestController` combined with `@GetMapping`/`@PostMapping`/etc. declares routes as annotated method signatures; Spring's `DispatcherServlet` handles matching incoming requests to the right method automatically.
- `@RequestBody` and `@PathVariable` (along with Spring's `HttpMessageConverter`s) handle deserializing incoming data and serializing outgoing responses, eliminating manual JSON parsing/building entirely in real code.
- Spring MVC's blocking, imperative model is simpler to write and debug than [Spring WebFlux](0101-spring-webflux-for-reactive-non-blocking-endpoints.md)'s reactive model, and is the right default for most services that don't specifically need very high I/O-bound concurrency.
- The annotation-driven approach shown here is the same underlying pattern as [declarative REST clients](0094-declarative-rest-clients.md) — annotations declare *what*, and generated/reflective machinery handles *how* — just applied to the server side instead of the client side.
- Spring MVC still runs on a bounded thread pool underneath — it doesn't eliminate the resource-exhaustion risks covered in [backpressure](0086-backpressure-in-synchronous-calls.md) and [cascading failures](0099-cascading-failures-from-synchronous-coupling.md); those concerns still need addressing explicitly.
