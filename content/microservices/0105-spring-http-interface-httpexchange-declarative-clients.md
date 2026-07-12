---
card: microservices
gi: 105
slug: spring-http-interface-httpexchange-declarative-clients
title: "Spring HTTP Interface (@HttpExchange declarative clients)"
---

## 1. What it is

Spring's HTTP Interface support lets you declare a REST client as a plain Java interface annotated with `@HttpExchange` (and its verb-specific shortcuts `@GetExchange`, `@PostExchange`, `@PutExchange`, `@DeleteExchange`), then hand that interface to an `HttpServiceProxyFactory`, which generates a working implementation backed by an actual HTTP client — either [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md) for blocking use or [`WebClient`](0103-webclient-reactive-synchronous-client.md) for reactive use. This is Spring's own, built-in implementation of the general [declarative REST client](0094-declarative-rest-clients.md) pattern.

## 2. Why & when

Even with [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md)'s clean fluent API, a service calling several endpoints on the same downstream dependency still needs a builder-chain call written out at every call site. `@HttpExchange` interfaces collapse this further: define the downstream API's shape once, as an interface, and every call site becomes a plain method call on that interface — `orderClient.getOrder(42)` — with `HttpServiceProxyFactory` generating the actual `RestClient`/`WebClient` calls underneath, entirely hidden from calling code.

Use `@HttpExchange` interfaces whenever a service makes multiple calls to the same downstream API — the interface becomes a single, self-documenting definition of that dependency's entire surface as seen from your service, and it composes naturally with either `RestClient` (blocking) or `WebClient` (reactive) as the underlying transport, letting you pick the execution model separately from the interface's declaration.

## 3. Core concept

The interface declares each call's shape via annotations; `HttpServiceProxyFactory`, configured once with a concrete client (`RestClient` or `WebClient`) and a base URL, generates the implementation at application startup.

```java
interface OrderClient {
    @GetExchange("/orders/{id}")
    Order getOrder(@PathVariable int id);

    @PostExchange("/orders")
    Order createOrder(@RequestBody CreateOrderRequest request);
}

// wiring (typically in a @Configuration class):
RestClient restClient = RestClient.builder().baseUrl("http://order-service").build();
HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(RestClientAdapter.create(restClient)).build();
OrderClient orderClient = factory.createClient(OrderClient.class);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An annotated OrderClient interface is combined with a configured RestClient by HttpServiceProxyFactory to produce a working proxy implementation">
  <rect x="20" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderClient interface</text>
  <text x="110" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@GetExchange, @PostExchange</text>

  <rect x="20" y="100" width="180" height="50" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="110" y="122" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">RestClient / WebClient</text>
  <text x="110" y="138" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">the actual transport</text>

  <rect x="260" y="55" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">HttpServiceProxyFactory</text>
  <text x="350" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">combines both</text>

  <rect x="500" y="55" width="120" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="560" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Generated proxy</text>
  <text x="560" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">implements OrderClient</text>

  <line x1="200" y1="50" x2="260" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="200" y1="125" x2="260" y2="95" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="440" y1="85" x2="500" y2="85" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The factory needs both the interface's shape and a concrete transport to produce a working client.

## 5. Runnable example

Scenario: an `OrderClient` interface, first defined and manually implemented against a hard-coded transport (to show what the proxy factory would otherwise need to be written by hand), then generated dynamically via a reflection-based factory taking a transport as a parameter, then extended to show the SAME interface working against two different underlying transports (a "RestClient-style" blocking one and a "WebClient-style" one wrapped to behave synchronously), demonstrating the interface's decoupling from its transport.

### Level 1 — Basic

```java
// File: ManuallyImplementedClient.java -- hand-write an implementation
// of the OrderClient interface -- the boilerplate the proxy factory exists
// to eliminate.
import java.util.*;

public class ManuallyImplementedClient {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    interface OrderClient {
        Order getOrder(int id);
    }

    static class ManualOrderClient implements OrderClient { // hand-written -- exactly what we want to avoid writing
        public Order getOrder(int id) {
            System.out.println("  [manual impl: GET /orders/" + id + "]");
            return orders.get(id);
        }
    }

    public static void main(String[] args) {
        OrderClient orderClient = new ManualOrderClient();
        System.out.println(orderClient.getOrder(42));
    }
}
```

**How to run:** `javac ManuallyImplementedClient.java && java ManuallyImplementedClient` (JDK 17+).

Expected output:
```
  [manual impl: GET /orders/42]
Order[id=42, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: GeneratedViaProxyFactory.java -- a REFLECTION-BASED factory
// takes the interface AND a transport, generating the implementation --
// standing in for HttpServiceProxyFactory.createClient(OrderClient.class).
import java.util.*;
import java.lang.reflect.*;
import java.lang.annotation.*;
import java.util.function.*;

public class GeneratedViaProxyFactory {
    @Retention(RetentionPolicy.RUNTIME) @interface GetExchange { String value(); }

    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    interface OrderClient {
        @GetExchange("/orders/{id}")
        Order getOrder(int id);
    }

    interface Transport { // stands in for RestClient/WebClient
        Object call(String path);
    }

    static <T> T createClient(Class<T> iface, Transport transport) { // stands in for HttpServiceProxyFactory
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, (proxy, method, args) -> {
            GetExchange exchange = method.getAnnotation(GetExchange.class);
            String path = exchange.value().replace("{id}", String.valueOf(args[0]));
            return transport.call(path);
        });
    }

    public static void main(String[] args) {
        Transport transport = path -> {
            int id = Integer.parseInt(path.substring(path.lastIndexOf('/') + 1));
            System.out.println("  [proxy factory generated call: GET " + path + "]");
            return orders.get(id);
        };
        OrderClient orderClient = createClient(OrderClient.class, transport); // NO manual implementation written
        System.out.println(orderClient.getOrder(42));
    }
}
```

**How to run:** `javac GeneratedViaProxyFactory.java && java GeneratedViaProxyFactory` (JDK 17+).

Expected output:
```
  [proxy factory generated call: GET /orders/42]
Order[id=42, status=PLACED]
```

### Level 3 — Advanced

```java
// File: SameInterfaceDifferentTransports.java -- the SAME OrderClient
// interface, generated against TWO DIFFERENT transports -- proving the
// interface's shape is fully decoupled from which underlying client
// (RestClient-style vs WebClient-style) actually executes the calls.
import java.util.*;
import java.lang.reflect.*;
import java.lang.annotation.*;

public class SameInterfaceDifferentTransports {
    @Retention(RetentionPolicy.RUNTIME) @interface GetExchange { String value(); }

    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));

    interface OrderClient {
        @GetExchange("/orders/{id}")
        Order getOrder(int id);
    }

    interface Transport { Object call(String path); }

    static <T> T createClient(Class<T> iface, Transport transport) {
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, (proxy, method, args) -> {
            GetExchange exchange = method.getAnnotation(GetExchange.class);
            String path = exchange.value().replace("{id}", String.valueOf(args[0]));
            return transport.call(path);
        });
    }

    public static void main(String[] args) {
        Transport restClientStyleTransport = path -> { // "RestClient" backend
            int id = Integer.parseInt(path.substring(path.lastIndexOf('/') + 1));
            System.out.println("  [RestClient-backed transport: GET " + path + "]");
            return orders.get(id);
        };
        Transport webClientStyleTransport = path -> { // "WebClient" backend (forced synchronous via .block())
            int id = Integer.parseInt(path.substring(path.lastIndexOf('/') + 1));
            System.out.println("  [WebClient-backed transport (blocked): GET " + path + "]");
            return orders.get(id);
        };

        OrderClient restBackedClient = createClient(OrderClient.class, restClientStyleTransport);
        OrderClient webBackedClient = createClient(OrderClient.class, webClientStyleTransport);

        System.out.println("Via RestClient-backed proxy: " + restBackedClient.getOrder(42));
        System.out.println("Via WebClient-backed proxy: " + webBackedClient.getOrder(42));
        System.out.println("(same OrderClient interface, same call site shape, different transport underneath)");
    }
}
```

**How to run:** `javac SameInterfaceDifferentTransports.java && java SameInterfaceDifferentTransports` (JDK 17+).

Expected output:
```
Via RestClient-backed proxy:   [RestClient-backed transport: GET /orders/42]
Order[id=42, status=PLACED]
Via WebClient-backed proxy:   [WebClient-backed transport (blocked): GET /orders/42]
Order[id=42, status=PLACED]
(same OrderClient interface, same call site shape, different transport underneath)
```

## 6. Walkthrough

1. **Level 1** — `ManualOrderClient` hand-implements the `OrderClient` interface's single method directly, printing a diagnostic and looking up the order. `main` calls `orderClient.getOrder(42)` through the interface reference and prints the result — functionally correct, but every new method added to `OrderClient` requires hand-writing its own implementation logic inside `ManualOrderClient`, exactly the repetition `@HttpExchange`-based generation exists to eliminate.
2. **Level 2 — generating the implementation from the interface's annotations** — `createClient` uses `java.lang.reflect.Proxy` to build a runtime implementation of any interface passed to it, reading each invoked method's `@GetExchange` annotation to determine the request path template, substituting in the method argument, and delegating the actual call to a `Transport` (standing in for a configured `RestClient`/`WebClient`). `main` builds a `Transport` lambda and calls `createClient(OrderClient.class, transport)` to get a working `OrderClient` — with *zero* hand-written implementation code for `getOrder` anywhere.
3. **Level 3 — proving transport independence** — two different `Transport` implementations are constructed: `restClientStyleTransport` and `webClientStyleTransport`, each printing a different diagnostic label but performing the identical underlying lookup. `createClient(OrderClient.class, ...)` is called twice, once with each transport, producing two separate `OrderClient` proxy instances.
4. **Tracing both calls** — `restBackedClient.getOrder(42)` invokes the proxy's handler, which reads `getOrder`'s `@GetExchange` annotation, builds the path `/orders/42`, and delegates to `restClientStyleTransport.call(...)`, printing its "RestClient-backed" diagnostic before returning the found order. `webBackedClient.getOrder(42)` performs the *identical* proxy dispatch logic — same annotation reading, same path construction — but delegates to `webClientStyleTransport.call(...)` instead, printing the "WebClient-backed (blocked)" diagnostic. Both ultimately return the same `Order[id=42, status=PLACED]`.
5. **What this demonstrates about real Spring `@HttpExchange` usage** — the `OrderClient` interface's declaration never changed between the two calls; only the underlying transport wired into `HttpServiceProxyFactory` differed. In a real Spring application, this is exactly how the same `@HttpExchange` interface can be backed by either `RestClientAdapter.create(restClient)` (blocking) or `WebClientAdapter.create(webClient)` (reactive) — the interface declares *what* the API looks like, entirely independent of *how* the underlying calls actually execute, letting you change the execution model (or swap in a test double for the transport) without touching a single call site that uses the interface.

## 7. Gotchas & takeaways

> **Gotcha:** `@HttpExchange` interfaces are resolved and validated by `HttpServiceProxyFactory` at application startup, not lazily — a malformed annotation (a path template referencing a parameter that doesn't exist on the method, for instance) typically surfaces as a startup failure rather than a runtime surprise on first call, which is a real benefit (fail fast) but means startup itself can fail for reasons unrelated to any actual downstream service being unavailable.

- `@HttpExchange` (and its verb shortcuts `@GetExchange`/`@PostExchange`/etc.) is Spring's own built-in implementation of the [declarative REST client](0094-declarative-rest-clients.md) pattern.
- `HttpServiceProxyFactory` generates a working implementation from the annotated interface, combined with a configured underlying transport (`RestClient` for blocking, `WebClient` for reactive).
- The interface's shape is fully decoupled from its transport — the same interface can be backed by either a blocking or reactive client without any change to call sites using the interface.
- This pairs naturally with [`RestClient`](0104-restclient-spring-6-1-synchronous-fluent-client.md) for the common case of blocking, synchronous service-to-service calls in a Spring MVC application.
- See [Spring Cloud OpenFeign](0106-spring-cloud-openfeign-declarative-rest-clients.md) for an alternative, older declarative client approach with a different (though conceptually similar) annotation style and additional Spring Cloud integration.
