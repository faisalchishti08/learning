---
card: microservices
gi: 94
slug: declarative-rest-clients
title: "Declarative REST clients"
---

## 1. What it is

A declarative REST client lets you define an HTTP API call as a plain Java interface method, annotated with the URL, verb, and parameters — `@GetExchange("/orders/{id}") Order getOrder(@PathVariable int id)` — and the framework generates a working implementation at runtime, handling the actual request construction, serialization, and response parsing behind the scenes. Spring's modern approach is `@HttpExchange` (with `@GetExchange`, `@PostExchange`, etc.) backed by an `HttpServiceProxyFactory`, generating a proxy implementation of your interface at startup — no hand-written client code at all.

## 2. Why & when

Writing an HTTP client call imperatively, as covered in [service-to-service HTTP clients](0093-service-to-service-http-clients.md), still requires hand-writing the same repetitive request-building code for every single endpoint a service calls — building the URI, setting headers, calling `.retrieve()`, specifying the response type — even with a clean fluent builder like `RestClient`. A declarative client removes that repetition entirely: the interface method's signature *is* the contract, and the generated implementation handles every call the exact same, consistent way, with far less code to write and far less room for a copy-paste mistake (like forgetting to set a header on one of several similar calls).

Use a declarative client whenever a service makes multiple calls to the same downstream service — the interface becomes a single, cohesive, self-documenting definition of everything that downstream service's API surface looks like from this caller's perspective. For a single, one-off outbound call, the imperative `RestClient` builder approach may be simpler and not worth the extra interface-definition ceremony.

## 3. Core concept

The interface declares *what* each call looks like; the framework generates the *how* — the actual HTTP request construction and response parsing — as a runtime proxy implementing that interface.

```java
interface OrderClient {
    @GetExchange("/orders/{id}")
    Order getOrder(@PathVariable int id);

    @PostExchange("/orders")
    Order createOrder(@RequestBody CreateOrderRequest request);
}

// usage: looks exactly like calling a local interface method
Order order = orderClient.getOrder(42);
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An annotated interface is handed to HttpServiceProxyFactory, which generates a runtime proxy implementing that interface, translating each annotated method call into an actual HTTP request">
  <rect x="20" y="30" width="200" height="110" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="120" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">OrderClient interface</text>
  <text x="120" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@GetExchange("/orders/{id}")</text>
  <text x="120" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Order getOrder(int id);</text>

  <rect x="260" y="55" width="150" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">HttpServiceProxyFactory</text>
  <text x="335" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">generates proxy</text>

  <rect x="450" y="30" width="170" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Runtime proxy</text>
  <text x="535" y="75" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">getOrder(42) -&gt;</text>
  <text x="535" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">real GET /orders/42</text>

  <line x1="220" y1="85" x2="260" y2="85" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="410" y1="85" x2="450" y2="85" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The interface method's annotations describe the request; the generated proxy performs it.

## 5. Runnable example

Scenario: an `OrderClient` used to call a downstream order service, first written imperatively (repeating the request-building boilerplate for each of two similar calls), then refactored to a declarative interface with a hand-written proxy standing in for what `HttpServiceProxyFactory` generates automatically, then extended to add a third method to the interface, showing how little new code a new declarative call requires compared to the imperative equivalent.

### Level 1 — Basic

```java
// File: ImperativeCalls.java -- TWO similar downstream calls, each with
// its OWN hand-written request-building boilerplate.
import java.util.*;

public class ImperativeCalls {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
    static int nextId = 43;

    static Order getOrder(int id) { // hand-written call #1
        System.out.println("  [building GET /orders/" + id + "]");
        return orders.get(id);
    }

    static Order createOrder(String sku) { // hand-written call #2 -- similar shape, DUPLICATED structure
        System.out.println("  [building POST /orders with body sku=" + sku + "]");
        Order created = new Order(nextId++, "PLACED");
        orders.put(created.id(), created);
        return created;
    }

    public static void main(String[] args) {
        Order found = getOrder(42);
        System.out.println("Found: " + found);
        Order created = createOrder("widget");
        System.out.println("Created: " + created);
    }
}
```

**How to run:** `javac ImperativeCalls.java && java ImperativeCalls` (JDK 17+).

Expected output:
```
  [building GET /orders/42]
Found: Order[id=42, status=PLACED]
  [building POST /orders with body sku=widget]
Created: Order[id=43, status=PLACED]
```

### Level 2 — Intermediate

```java
// File: DeclarativeInterface.java -- declare the SAME two calls as a
// plain interface; a HAND-WRITTEN proxy (standing in for what
// HttpServiceProxyFactory generates automatically) implements them.
import java.util.*;
import java.lang.reflect.*;

public class DeclarativeInterface {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
    static int nextId = 43;

    interface OrderClient { // the DECLARATION -- just method signatures, no implementation
        Order getOrder(int id);
        Order createOrder(String sku);
    }

    // stands in for HttpServiceProxyFactory's generated implementation
    static OrderClient buildProxy() {
        return (OrderClient) Proxy.newProxyInstance(
            OrderClient.class.getClassLoader(),
            new Class<?>[]{OrderClient.class},
            (proxy, method, args) -> { // ONE generic handler serves EVERY interface method
                if (method.getName().equals("getOrder")) {
                    int id = (int) args[0];
                    System.out.println("  [proxy: GET /orders/" + id + "]");
                    return orders.get(id);
                }
                if (method.getName().equals("createOrder")) {
                    String sku = (String) args[0];
                    System.out.println("  [proxy: POST /orders with body sku=" + sku + "]");
                    Order created = new Order(nextId++, "PLACED");
                    orders.put(created.id(), created);
                    return created;
                }
                throw new UnsupportedOperationException();
            }
        );
    }

    public static void main(String[] args) {
        OrderClient orderClient = buildProxy(); // ONE proxy handles BOTH declared methods
        Order found = orderClient.getOrder(42); // reads like a plain interface call
        System.out.println("Found: " + found);
        Order created = orderClient.createOrder("widget");
        System.out.println("Created: " + created);
    }
}
```

**How to run:** `javac DeclarativeInterface.java && java DeclarativeInterface` (JDK 17+).

Expected output:
```
  [proxy: GET /orders/42]
Found: Order[id=42, status=PLACED]
  [proxy: POST /orders with body sku=widget]
Created: Order[id=43, status=PLACED]
```

### Level 3 — Advanced

```java
// File: AddingAThirdMethod.java -- add a THIRD declared method
// (cancelOrder) -- notice how little new code this needs, because the
// generic proxy handler already exists and just needs one more case.
import java.util.*;
import java.lang.reflect.*;

public class AddingAThirdMethod {
    record Order(int id, String status) {}
    static Map<Integer, Order> orders = new HashMap<>(Map.of(42, new Order(42, "PLACED")));
    static int nextId = 43;

    interface OrderClient {
        Order getOrder(int id);
        Order createOrder(String sku);
        Order cancelOrder(int id); // NEW -- just one more line in the interface
    }

    static OrderClient buildProxy() {
        return (OrderClient) Proxy.newProxyInstance(
            OrderClient.class.getClassLoader(),
            new Class<?>[]{OrderClient.class},
            (proxy, method, args) -> {
                if (method.getName().equals("getOrder")) {
                    int id = (int) args[0];
                    return orders.get(id);
                }
                if (method.getName().equals("createOrder")) {
                    String sku = (String) args[0];
                    Order created = new Order(nextId++, "PLACED");
                    orders.put(created.id(), created);
                    return created;
                }
                if (method.getName().equals("cancelOrder")) { // NEW case -- one small addition
                    int id = (int) args[0];
                    Order cancelled = new Order(id, "CANCELLED");
                    orders.put(id, cancelled);
                    System.out.println("  [proxy: POST /orders/" + id + "/cancel]");
                    return cancelled;
                }
                throw new UnsupportedOperationException();
            }
        );
    }

    public static void main(String[] args) {
        OrderClient orderClient = buildProxy();
        Order cancelled = orderClient.cancelOrder(42); // the caller's code is JUST as simple as the other two calls
        System.out.println("Cancelled: " + cancelled);
    }
}
```

**How to run:** `javac AddingAThirdMethod.java && java AddingAThirdMethod` (JDK 17+).

Expected output:
```
  [proxy: POST /orders/42/cancel]
Cancelled: Order[id=42, status=CANCELLED]
```

## 6. Walkthrough

1. **Level 1** — `getOrder` and `createOrder` each independently print a "building" diagnostic and then perform their own logic — two methods, two separately hand-written implementations, each responsible for its own request-construction boilerplate (here simplified to a print statement, but standing in for real header-setting, URI-building, serialization code). `main` calls both and prints their results.
2. **Level 2 — declaring the interface, generating the implementation** — `OrderClient` becomes a plain interface with *no* method bodies at all — just signatures. `buildProxy` uses `java.lang.reflect.Proxy` to construct a runtime implementation: a single `InvocationHandler` lambda inspects which method was called (`method.getName()`) and dispatches to the appropriate logic. This is a hand-rolled simulation of exactly what Spring's real `HttpServiceProxyFactory` does automatically from `@HttpExchange`-annotated interface methods — generate a working proxy implementation from the interface's declared shape.
3. **Tracing `main`'s calls** — `orderClient.getOrder(42)` invokes the proxy's `InvocationHandler`, which sees `method.getName()` equals `"getOrder"`, extracts `id = 42` from `args`, prints the "proxy: GET" diagnostic, and returns the matching `Order` from `orders`. `orderClient.createOrder("widget")` similarly dispatches to the `"createOrder"` branch, creating and storing a new order. Both calls, from `main`'s point of view, read exactly like calling ordinary methods on `orderClient` — no visible difference in calling syntax from Level 1's direct method calls, but the actual implementation logic now lives entirely inside one shared, generic proxy handler rather than two separately hand-written methods.
4. **Level 3 — adding a new call requires almost no new structure** — `cancelOrder` is added to the `OrderClient` interface as a single new line, and the proxy's `InvocationHandler` gains one more `if` branch handling `"cancelOrder"`. `main` calls `orderClient.cancelOrder(42)`, which dispatches to the new branch: it constructs a new `Order` with status `"CANCELLED"`, stores it back into `orders` (overwriting the old entry), prints the diagnostic, and returns the cancelled order — `main` prints the result.
5. **Why the contrast between Level 1 and Level 3 matters** — adding `cancelOrder` in the declarative model required exactly one interface line and one dispatch branch reusing the same generic proxy machinery already built. Adding an equivalent third method under Level 1's imperative approach would require writing an entirely new, independent method with its own full request-building logic, following (and hopefully correctly copying) whatever pattern the first two methods established. In a real Spring application using `@HttpExchange`, adding a new declarative call is even simpler still — just one new annotated interface method; `HttpServiceProxyFactory` generates the entire implementation automatically, with no hand-written `InvocationHandler` dispatch logic needed at all.

## 7. Gotchas & takeaways

> **Gotcha:** a declarative client interface hides the actual HTTP call happening behind an ordinary-looking method signature, which can make it easy to forget the [synchronous request/response model](0075-synchronous-request-response-model.md)'s real cost (network latency, potential failure) is still fully present — the same caution about RPC's "looks local, isn't local" illusion (see [RPC model](0088-remote-procedure-call-rpc-model.md)) applies directly here, since declarative HTTP clients are conceptually a lightweight form of RPC.

- A declarative client interface defines each call's shape (URL, verb, parameters) via annotations; the framework generates a working implementation as a runtime proxy — no hand-written request-building code per endpoint.
- Spring's modern approach is `@HttpExchange` (with `@GetExchange`, `@PostExchange`, etc.) backed by `HttpServiceProxyFactory`, generating the proxy from the annotated interface automatically.
- Adding a new declarative call is nearly free — a new interface method — because the framework's generic proxy-generation machinery already exists; adding a new imperative call means writing an entire new method's worth of request-building logic.
- Declarative clients earn their value most clearly when a service makes multiple calls to the same downstream API — the interface becomes a single, cohesive, self-documenting definition of that downstream service's surface from the caller's perspective.
- A declarative client is a thin layer over the same [imperative HTTP client](0093-service-to-service-http-clients.md) machinery underneath — it changes how the call is *declared*, not the network-level realities (latency, failure modes) of the call itself.
