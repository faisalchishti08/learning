---
card: microservices
gi: 2
slug: microservice-architecture-vs-monolithic-architecture
title: Microservice architecture vs monolithic architecture
---

## 1. What it is

A **monolithic architecture** packages an entire application — every feature, every module — into one deployable unit that runs as a single process and usually talks to one shared database. A **microservice architecture** splits that same application into several small, independently deployable services, each owning one business capability and, typically, its own private data.

The distinction isn't about how many source files or classes exist — a well-organized monolith can have many internal modules. The distinction is about the **deployment boundary**: in a monolith, everything ships together, as one artifact, on one schedule. In microservices, each service ships on its own artifact, on its own schedule.

## 2. Why & when

A monolith is genuinely simpler at small scale: one build, one deployment pipeline, in-process method calls with no network latency, and a single database transaction can keep everything consistent. As the codebase and the team grow, though, those same properties start to hurt: any team's change goes through the same build and the same deploy, so a risky change from one team can block or break everyone else; the whole application must scale as one unit even when only one feature is actually the bottleneck; and a single unhandled bug can take the entire system down instead of being contained.

Microservices trade that simplicity for independent deployability and scalability, at the real cost of distributed-systems complexity: network calls can fail in ways in-process calls cannot, and keeping data consistent across services requires deliberate design instead of one shared transaction. Reach for microservices once a monolith's deployment coupling is measurably costing velocity or reliability — not as the default starting point for a new, small application, where a well-structured monolith is usually the wiser first step.

## 3. Core concept

The clean test: pick any one feature and ask "can I ship a change to just this, alone, right now?"

- **Monolith:** no — shipping any change means rebuilding and redeploying the entire application, because everything lives in one process and one artifact.
- **Microservices:** yes — each service has its own build, its own artifact, its own deploy pipeline, so a change to one service's code never forces a rebuild of any other.

The same logical features exist in both architectures; what changes is purely how they are packaged, deployed, and scaled.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A monolith bundles Cart, Inventory and Shipping into one deployable process with one shared database; microservices split them into three independently deployable services each with their own data">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <rect x="30" y="35" width="240" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Cart | Inventory | Shipping</text>
  <text x="150" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one process</text>
  <text x="150" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one shared database</text>
  <text x="150" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one deploy pipeline</text>

  <text x="480" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Microservices</text>
  <rect x="350" y="35" width="90" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="395" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Cart</text>
  <rect x="455" y="35" width="90" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Inventory</text>
  <rect x="560" y="35" width="70" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="595" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Shipping</text>
  <text x="490" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">each: own process, own data, own deploy</text>
</svg>

Same three capabilities, different packaging: one deployable box versus three independently deployable ones.

## 5. Runnable example

Scenario: an order-placement flow spanning Cart, Inventory, and Shipping, first as a monolith, then split into microservices, then hardened to show what independent failure isolation actually buys you.

### Level 1 — Basic

```java
// File: ShopMonolith.java -- Cart, Inventory, Shipping as one process, one deploy unit
public class ShopMonolith {
    static java.util.Map<String, Integer> inventory = new java.util.HashMap<>(java.util.Map.of("widget", 3));

    static boolean reserve(String item) {
        Integer count = inventory.get(item);
        if (count != null && count > 0) { inventory.put(item, count - 1); return true; }
        return false;
    }

    static void scheduleShipping(String item) {
        System.out.println("Shipping scheduled for " + item);
    }

    static void checkout(String item) {
        if (reserve(item)) {
            scheduleShipping(item);
            System.out.println("Order placed for " + item);
        } else {
            System.out.println("Out of stock: " + item);
        }
    }

    public static void main(String[] args) {
        checkout("widget");
        checkout("gadget");
    }
}
```

**How to run:** `javac ShopMonolith.java && java ShopMonolith` (JDK 17+).

Expected output:
```
Shipping scheduled for widget
Order placed for widget
Out of stock: gadget
```

All three capabilities are plain methods in one class, in one process. Deploying a fix to `scheduleShipping` means rebuilding and redeploying this entire file — there's no way to touch just the shipping logic.

### Level 2 — Intermediate

```java
// File: ShopMicroservices.java -- Cart, Inventory and Shipping as THREE
// separate HTTP services, each independently startable and stoppable.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class ShopMicroservices {
    static HttpServer inventoryService() throws Exception {
        java.util.Map<String, Integer> stock = new java.util.concurrent.ConcurrentHashMap<>(java.util.Map.of("widget", 3));
        HttpServer s = HttpServer.create(new InetSocketAddress(8091), 0);
        s.createContext("/reserve", ex -> {
            String item = ex.getRequestURI().getQuery().replace("item=", "");
            int count = stock.getOrDefault(item, 0);
            int status = count > 0 ? 200 : 409;
            if (count > 0) stock.put(item, count - 1);
            ex.sendResponseHeaders(status, -1); ex.close();
        });
        s.start();
        return s;
    }

    static HttpServer shippingService() throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(8092), 0);
        s.createContext("/schedule", ex -> { ex.sendResponseHeaders(200, -1); ex.close(); });
        s.start();
        return s;
    }

    static void checkout(HttpClient client, String item) throws Exception {
        var reserve = HttpRequest.newBuilder(URI.create("http://localhost:8091/reserve?item=" + item)).POST(HttpRequest.BodyPublishers.noBody()).build();
        var reserveResp = client.send(reserve, HttpResponse.BodyHandlers.discarding());
        if (reserveResp.statusCode() != 200) { System.out.println("Out of stock: " + item); return; }
        var ship = HttpRequest.newBuilder(URI.create("http://localhost:8092/schedule?item=" + item)).POST(HttpRequest.BodyPublishers.noBody()).build();
        client.send(ship, HttpResponse.BodyHandlers.discarding());
        System.out.println("Order placed for " + item);
    }

    public static void main(String[] args) throws Exception {
        HttpServer inv = inventoryService();
        HttpServer ship = shippingService();
        HttpClient client = HttpClient.newHttpClient();
        checkout(client, "widget");
        checkout(client, "gadget");
        inv.stop(0); ship.stop(0);
    }
}
```

**How to run:** `javac ShopMicroservices.java && java ShopMicroservices` (JDK 17+).

Expected output:
```
Order placed for widget
Out of stock: gadget
```

Same behavior, but `InventoryService` and `ShippingService` are now separate processes on separate ports; `checkout` coordinates them over HTTP. Either one can now be rebuilt and redeployed without touching the other or the caller's code.

### Level 3 — Advanced

```java
// File: ShopMicroservicesResilient.java -- ShippingService goes DOWN mid-run;
// with independent services, Cart+Inventory keep working -- the failure is
// contained instead of taking the whole system down, as a monolith would.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class ShopMicroservicesResilient {
    static HttpServer inventoryService() throws Exception {
        java.util.Map<String, Integer> stock = new java.util.concurrent.ConcurrentHashMap<>(java.util.Map.of("widget", 3, "gadget", 2));
        HttpServer s = HttpServer.create(new InetSocketAddress(8091), 0);
        s.createContext("/reserve", ex -> {
            String item = ex.getRequestURI().getQuery().replace("item=", "");
            int count = stock.getOrDefault(item, 0);
            int status = count > 0 ? 200 : 409;
            if (count > 0) stock.put(item, count - 1);
            ex.sendResponseHeaders(status, -1); ex.close();
        });
        s.start();
        return s;
    }

    static HttpServer shippingService() throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(8092), 0);
        s.createContext("/schedule", ex -> { ex.sendResponseHeaders(200, -1); ex.close(); });
        s.start();
        return s;
    }

    static void checkout(HttpClient client, String item) {
        try {
            var reserve = HttpRequest.newBuilder(URI.create("http://localhost:8091/reserve?item=" + item)).timeout(java.time.Duration.ofSeconds(2)).POST(HttpRequest.BodyPublishers.noBody()).build();
            var reserveResp = client.send(reserve, HttpResponse.BodyHandlers.discarding());
            if (reserveResp.statusCode() != 200) { System.out.println("Out of stock: " + item); return; }

            var ship = HttpRequest.newBuilder(URI.create("http://localhost:8092/schedule?item=" + item)).timeout(java.time.Duration.ofSeconds(2)).POST(HttpRequest.BodyPublishers.noBody()).build();
            client.send(ship, HttpResponse.BodyHandlers.discarding());
            System.out.println("Order placed and shipping scheduled for " + item);
        } catch (java.net.ConnectException e) {
            // Shipping is down, but the item WAS reserved -- order is placed, shipping is queued for later.
            System.out.println("Order placed for " + item + " but shipping scheduling failed -- will retry later");
        } catch (Exception e) {
            System.out.println("Unexpected failure for " + item + ": " + e.getClass().getSimpleName());
        }
    }

    public static void main(String[] args) throws Exception {
        HttpServer inv = inventoryService();
        HttpServer ship = shippingService();
        HttpClient client = HttpClient.newHttpClient();

        checkout(client, "widget"); // both services healthy

        ship.stop(0); // ShippingService crashes / is being redeployed
        checkout(client, "gadget"); // Cart+Inventory still work; only shipping is affected

        inv.stop(0);
    }
}
```

**How to run:** `javac ShopMicroservicesResilient.java && java ShopMicroservicesResilient` (JDK 17+).

Expected output:
```
Order placed and shipping scheduled for widget
Order placed for gadget but shipping scheduling failed -- will retry later
```

The production-flavored hard case: `ship.stop(0)` simulates `ShippingService` crashing mid-operation. `InventoryService` is completely unaffected — the `gadget` reservation still succeeds — and `checkout` catches the resulting `ConnectException`, degrading gracefully rather than losing the whole order. In `ShopMonolith` (Level 1), a bug or crash inside `scheduleShipping` would have thrown out of `checkout` entirely, losing the already-reserved inventory update along with it.

## 6. Walkthrough

1. `ship.stop(0)` shuts down only the `ShippingService` HTTP server; `InventoryService`, on a different port, keeps running untouched.
2. `checkout(client, "gadget")` first sends `POST /reserve?item=gadget` to port `8091`. `InventoryService` still has 2 gadgets, decrements to 1, returns `200`.
3. Because the reservation succeeded, `checkout` proceeds to send `POST /schedule?item=gadget` to port `8092` — but nothing is listening there anymore.
4. The JDK's `HttpClient` throws `java.net.ConnectException` on the connection attempt; the `catch` block treats this as "reserved, but shipping needs a retry" rather than failing the whole order.
5. The method prints `"Order placed for gadget but shipping scheduling failed -- will retry later"` — the inventory decrement from step 2 stands; only the shipping step is degraded.
6. Contrast with `ShopMonolith`: there, `scheduleShipping` runs as a plain method call inside the same `checkout` call stack. If it threw an exception, the whole `checkout` call would unwind, and depending on how the surrounding code was written, the earlier `reserve` mutation could be left in an inconsistent, half-applied state with no natural boundary to isolate the failure to "just shipping."

```
Monolith:      checkout -> reserve (in-process) -> scheduleShipping (in-process, SAME call stack)
                            a crash in shipping can unwind the whole checkout

Microservices: checkout -> POST /reserve (8091, succeeds)
                         -> POST /schedule (8092, DOWN -> ConnectException)
                            caught locally; reservation already committed and stands
```

## 7. Gotchas & takeaways

> **Gotcha:** splitting a monolith into services that still must be deployed together — because they share a database schema, or a release always bundles all of them — gives you all the network complexity of microservices with none of the independent-deployability benefit. Verify each service can actually ship alone before calling it "microservices."

- A monolith bundles every feature into one process, one deploy, and usually one database; microservices split those same features into independently deployable, independently owned units.
- The real dividing line is the deployment boundary, not the number of classes or files — a modular monolith can be well organized internally and still be one deployable unit.
- Independent services also give you independent *failure* boundaries: one service going down can degrade gracefully instead of taking the whole system down, provided calling code is written to expect and handle that.
- Don't adopt microservices by default for a new, small system — the distributed-systems complexity (partial failures, eventual consistency) is a real cost that only pays off once a monolith's coupling is genuinely limiting your team.
