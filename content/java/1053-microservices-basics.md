---
card: java
gi: 1053
slug: microservices-basics
title: Microservices basics
---

## 1. What it is

A microservices architecture splits an application into several small, independently deployable services, each owning its own specific piece of business capability (an `OrderService`, an `InventoryService`, a `PaymentService`) and typically its own dedicated database — as opposed to a **monolith**, where all of that functionality and data lives in one single deployable application sharing one database. Services communicate over the network, most commonly via REST APIs (see [REST APIs (JAX-RS, Spring MVC)](1051-rest-apis-jax-rs-spring-mvc.md)) or asynchronous messaging, rather than through in-process method calls the way different modules within a monolith would.

## 2. Why & when

A monolith is simpler to develop, test, and deploy for a small team and a small codebase — one build, one deployment, in-process method calls with no network latency or partial-failure concerns. As an application and organization grow, though, a monolith's downsides compound: every team's changes go through the same build and deployment pipeline (a slow or risky deploy for one team's feature blocks everyone), the whole application must scale together even if only one specific piece (say, image processing) is actually the bottleneck, and a bug in one module can bring down the entire application rather than being contained to just that concern. Microservices trade the monolith's simplicity for independent deployability and scalability: each service can be built, tested, deployed, and scaled on its own schedule, by its own team, using whatever technology fits its specific needs — at the cost of introducing genuine distributed-systems complexity (network calls can fail or time out in ways in-process calls never do, data consistency across services requires deliberate design instead of a single database transaction, and the system as a whole becomes harder to reason about and observe).

Consider microservices when an application and its engineering organization have grown to the point where a monolith's deployment coupling and shared-scaling limitations are genuinely costing significant velocity or reliability — not as a default starting architecture for a new, small application. Starting with a well-structured monolith and extracting services later, once real boundaries and pain points have emerged, is a common and often wiser path than beginning with a distributed system's complexity before it's actually needed.

## 3. Core concept

```java
// MONOLITH: OrderService and InventoryService are just Java classes,
// called via a normal, in-process method call -- no network involved.
class OrderService {
    private final InventoryService inventory; // direct object reference
    OrderService(InventoryService inventory) { this.inventory = inventory; }

    void placeOrder(String item) {
        if (inventory.reserve(item)) { // a plain, in-process method call
            System.out.println("Order placed for " + item);
        }
    }
}

// MICROSERVICES: OrderService calls InventoryService over the NETWORK instead --
// via a REST call, since they're now separate, independently-deployed processes.
class OrderServiceClient {
    private final java.net.http.HttpClient httpClient = java.net.http.HttpClient.newHttpClient();

    boolean reserveViaNetwork(String item) throws Exception {
        var request = java.net.http.HttpRequest.newBuilder()
            .uri(java.net.URI.create("http://inventory-service/reserve?item=" + item))
            .POST(java.net.http.HttpRequest.BodyPublishers.noBody())
            .build();
        var response = httpClient.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
        return response.statusCode() == 200; // could ALSO fail with a timeout, a 500, a connection refusal...
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A monolith with OrderService and InventoryService as two classes sharing one database, calling each other in-process, versus a microservices architecture with OrderService and InventoryService as separate deployed services each with their own database, communicating over a network">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <rect x="30" y="40" width="240" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService  |  InventoryService</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one shared database</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Microservices</text>
  <rect x="360" y="30" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="420" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="420" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own DB</text>

  <rect x="500" y="30" width="120" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">InventoryService</text>
  <text x="560" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own DB</text>

  <line x1="480" y1="55" x2="500" y2="55" stroke="#f0883e" marker-end="url(#a)"/>
  <text x="490" y="100" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">network call (can fail/time out)</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A monolith's in-process call becomes a network call between independently-deployed services, each owning its own data.

## 5. Runnable example

Scenario: an order-placement flow depending on inventory availability, evolving from a monolithic in-process design into a microservices-style network call, showing exactly what new failure handling that transition demands.

### Level 1 — Basic

```java
// File: MonolithBasic.java
public class MonolithBasic {
    static class InventoryService {
        private final java.util.Map<String, Integer> stock = new java.util.HashMap<>();
        InventoryService() { stock.put("widget", 5); }

        boolean reserve(String item) {
            Integer count = stock.get(item);
            if (count != null && count > 0) {
                stock.put(item, count - 1);
                return true;
            }
            return false;
        }
    }

    static class OrderService {
        private final InventoryService inventory;
        OrderService(InventoryService inventory) { this.inventory = inventory; }

        void placeOrder(String item) {
            if (inventory.reserve(item)) { // a plain, in-process, ALWAYS-RELIABLE method call
                System.out.println("Order placed for " + item);
            } else {
                System.out.println("Out of stock: " + item);
            }
        }
    }

    public static void main(String[] args) {
        InventoryService inventory = new InventoryService();
        OrderService orders = new OrderService(inventory);
        orders.placeOrder("widget");
        orders.placeOrder("gadget"); // never stocked at all
    }
}
```

**How to run:** save as `MonolithBasic.java`, then `javac MonolithBasic.java && java MonolithBasic` (JDK 17+).

Expected output:
```
Order placed for widget
Out of stock: gadget
```

`OrderService.placeOrder` calls `inventory.reserve(item)` as a plain, in-process method call — this call cannot time out, cannot fail due to a network partition, and cannot receive a malformed response, since both classes run in the same JVM process sharing the same memory.

### Level 2 — Intermediate

```java
// File: OrderServiceHttp.java -- simulates OrderService calling InventoryService
// over a NETWORK boundary (represented here by a simple embedded HTTP server
// standing in for a genuinely separate InventoryService process).
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class OrderServiceHttp {
    public static void main(String[] args) throws Exception {
        // A minimal stand-in "InventoryService" running as its own HTTP server,
        // representing a genuinely separate process/deployment.
        Map<String, Integer> stock = new ConcurrentHashMap<>(Map.of("widget", 5));
        HttpServer inventoryServer = HttpServer.create(new InetSocketAddress(8081), 0);
        inventoryServer.createContext("/reserve", exchange -> {
            String item = exchange.getRequestURI().getQuery().replace("item=", "");
            int count = stock.getOrDefault(item, 0);
            int status = count > 0 ? 200 : 409; // 200 = reserved, 409 = out of stock
            if (count > 0) stock.put(item, count - 1);
            exchange.sendResponseHeaders(status, -1);
            exchange.close();
        });
        inventoryServer.start();

        // OrderService now calls InventoryService over an ACTUAL network request.
        HttpClient client = HttpClient.newHttpClient();
        for (String item : new String[]{"widget", "gadget"}) {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:8081/reserve?item=" + item))
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
            HttpResponse<Void> response = client.send(request, HttpResponse.BodyHandlers.discarding());
            if (response.statusCode() == 200) {
                System.out.println("Order placed for " + item);
            } else {
                System.out.println("Out of stock: " + item + " (status " + response.statusCode() + ")");
            }
        }
        inventoryServer.stop(0);
    }
}
```

**How to run:** save as `OrderServiceHttp.java`, then `javac OrderServiceHttp.java && java OrderServiceHttp` (JDK 17+).

Expected output:
```
Order placed for widget
Out of stock: gadget (status 409)
```

The real-world concern added: `OrderService` and `InventoryService` are now genuinely separate — communicating over an actual HTTP request/response cycle on `localhost:8081`, rather than a plain method call. The result looks the same, but the mechanism underneath has changed fundamentally: this call could, in a real deployment, also fail due to a network timeout, a connection refusal, or the inventory service being temporarily down — none of which a monolith's in-process call could ever experience.

### Level 3 — Advanced

```java
// File: OrderServiceResilient.java -- handles the NEW failure modes a network
// call introduces: connection failures and timeouts, neither of which an
// in-process method call in a monolith would ever need to consider.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.net.http.HttpConnectTimeoutException;
import java.time.Duration;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class OrderServiceResilient {
    static boolean reserveWithFallback(HttpClient client, String item) {
        try {
            HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://localhost:8081/reserve?item=" + item))
                .timeout(Duration.ofSeconds(2)) // NEW concern: bound how long we'll wait
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
            HttpResponse<Void> response = client.send(request, HttpResponse.BodyHandlers.discarding());
            return response.statusCode() == 200;
        } catch (java.net.ConnectException e) {
            // NEW concern: the inventory service might simply be DOWN.
            System.out.println("  [fallback] inventory service unreachable for " + item + " -- assuming out of stock");
            return false;
        } catch (Exception e) {
            System.out.println("  [fallback] unexpected error reserving " + item + ": " + e.getClass().getSimpleName());
            return false;
        }
    }

    public static void main(String[] args) throws Exception {
        Map<String, Integer> stock = new ConcurrentHashMap<>(Map.of("widget", 5));
        HttpServer inventoryServer = HttpServer.create(new InetSocketAddress(8081), 0);
        inventoryServer.createContext("/reserve", exchange -> {
            String item = exchange.getRequestURI().getQuery().replace("item=", "");
            int count = stock.getOrDefault(item, 0);
            int status = count > 0 ? 200 : 409;
            if (count > 0) stock.put(item, count - 1);
            exchange.sendResponseHeaders(status, -1);
            exchange.close();
        });
        inventoryServer.start();

        HttpClient client = HttpClient.newHttpClient();
        System.out.println("widget: " + (reserveWithFallback(client, "widget") ? "placed" : "failed"));

        // Simulate the inventory service going down entirely.
        inventoryServer.stop(0);
        System.out.println("gadget: " + (reserveWithFallback(client, "gadget") ? "placed" : "failed"));
    }
}
```

**How to run:** save as `OrderServiceResilient.java`, then `javac OrderServiceResilient.java && java OrderServiceResilient` (JDK 17+).

Expected output:
```
widget: placed
  [fallback] inventory service unreachable for gadget -- assuming out of stock
gadget: failed
```

The production-flavored hard case: after `inventoryServer.stop(0)` simulates the inventory service being genuinely unreachable, the second call to `reserveWithFallback` catches a `ConnectException` and falls back gracefully (treating it as "out of stock" rather than crashing the whole order flow) — this exact failure mode, an entire dependency becoming unreachable mid-operation, is unique to a distributed, network-based architecture and has no equivalent in a monolith's in-process method calls.

## 6. Walkthrough

Tracing the second call, `reserveWithFallback(client, "gadget")`, after `inventoryServer.stop(0)`:

1. `inventoryServer.stop(0)` shuts down the embedded HTTP server immediately, meaning nothing is listening on `localhost:8081` anymore — simulating a real scenario where the `InventoryService` process has crashed, is being redeployed, or is otherwise unreachable.
2. `reserveWithFallback(client, "gadget")` builds an `HttpRequest` targeting `http://localhost:8081/reserve?item=gadget`, with a `2`-second timeout configured.
3. `client.send(request, ...)` attempts to establish a TCP connection to `localhost:8081` — since nothing is listening there anymore, the operating system immediately refuses the connection attempt, and the JDK's HTTP client throws a `java.net.ConnectException` rather than returning any HTTP response at all.
4. The `catch (java.net.ConnectException e)` block catches this specific exception, printing `"  [fallback] inventory service unreachable for gadget -- assuming out of stock"` and returning `false` — the calling code treats this as equivalent to a genuine "out of stock" business outcome, a deliberate fallback decision made by the application, not something the network layer decided on its own.
5. Back in `main`, `reserveWithFallback` returned `false`, so `"gadget: failed"` is printed.
6. Contrast this with the monolith version (Level 1): there, `inventory.reserve("gadget")` returning `false` meant "genuinely out of stock" — a real business fact. Here, in the microservices version, the *exact same textual outcome* (`"failed"`) could mean either "genuinely out of stock" (a `409` response) or "we have no idea, because the inventory service is unreachable" (a `ConnectException`) — a distinction a monolith's design never needs to make, but that a resilient microservices design must handle deliberately, since the two situations may call for very different responses in a real production system (retrying, alerting, or genuinely rejecting the order).

## 7. Gotchas & takeaways

> **Gotcha:** treating "the network call failed" as identical to "the answer is no" (as the fallback above does, for simplicity) can silently produce wrong business outcomes — a customer might be told an item is "out of stock" when the truth is simply "we couldn't ask in time," which is a meaningfully different situation that a mature system would often handle differently (retry, queue for later, or surface a clear "temporarily unavailable" message rather than a false "out of stock").

- Microservices split an application into independently deployable services, each typically owning its own data, communicating over the network rather than through in-process method calls.
- The core tradeoff: independent deployability and scalability per service, at the cost of genuine distributed-systems complexity — network calls can fail, time out, or partially succeed in ways in-process calls never do.
- A network call requires explicit handling for failure modes a monolith never needs to consider: connection failures, timeouts, and partial or malformed responses.
- Don't collapse "the dependency said no" and "we couldn't reach the dependency at all" into the same fallback behavior without considering whether the business situation genuinely calls for the same response in both cases.
- Microservices are a response to organizational and scaling pain a monolith is genuinely experiencing — not a default starting architecture for a new, small application, where a monolith's simplicity is usually the better starting point.
- See [REST APIs (JAX-RS, Spring MVC)](1051-rest-apis-jax-rs-spring-mvc.md) for the most common protocol microservices use to communicate, and [JDBC & connection pooling](1044-jdbc-connection-pooling.md) for how each service typically manages its own dedicated database connections independently of any other service's data store.
