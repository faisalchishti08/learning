---
card: microservices
gi: 1
slug: definition-of-a-microservice
title: Definition of a microservice
---

## 1. What it is

A **microservice** is a small, independently deployable software service that owns one specific piece of business functionality — placing orders, sending notifications, calculating prices — end to end, including its own data if it needs any. "Independently deployable" is the load-bearing phrase: you can build, test, and ship a new version of that one service without recompiling, retesting, or redeploying anything else in the system. It runs as its own process, listens on its own network address, and talks to other services only through a well-defined interface such as an HTTP API.

Contrast this with a **module** or **library** inside a larger application: a module is a piece of code compiled and deployed *together* with everything else, sharing the same process and the same release cycle. A microservice is a module that has been given its own process, its own deployment pipeline, and its own lifecycle.

## 2. Why & when

Splitting an application into independently deployable units matters once a single team, a single build, or a single deploy becomes a bottleneck for everyone touching the codebase. If a "notifications" feature can be built, tested, and released on its own schedule — by a small team, without waiting for or risking the rest of the system — that is a real, measurable win in a growing organization.

Reach for this definition as your working test whenever someone claims to have "a microservice": ask whether it can actually be deployed on its own, right now, without also redeploying something else. If the answer is no — if it still ships bundled with other components, or shares a process with them — it's a module with a services badge on it, not a microservice yet.

## 3. Core concept

Three properties, together, are what make something a microservice rather than just "a class" or "a package":

1. **Single responsibility** — it owns one cohesive piece of business capability, not a grab-bag of unrelated features.
2. **Own process, own address** — it runs independently of every other service, reachable over the network at its own host and port.
3. **Independent deployability** — a new version can go live without coordinating a release with any other service.

Drop any one of these three and you no longer have a microservice: drop (1) and you have a monolith; drop (2) and you have a library; drop (3) and you have a "distributed monolith" — separate processes that must still be deployed together.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A library is compiled into the caller's process; a microservice runs as its own separate process reachable over the network">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Library / module</text>
  <rect x="40" y="40" width="220" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller code</text>
  <text x="150" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ PricingLib.class</text>
  <text x="150" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">one process, one deploy</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Microservice</text>
  <rect x="360" y="40" width="120" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="420" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller</text>
  <text x="420" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own process</text>

  <rect x="500" y="40" width="120" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PricingService</text>
  <text x="560" y="82" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own process, own deploy</text>

  <line x1="480" y1="70" x2="500" y2="70" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a1)"/>
  <text x="490" y="130" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">network call, deployed independently</text>
  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A library ships bundled with its caller; a microservice ships on its own — the network boundary is what makes independent deployment possible.

## 5. Runnable example

Scenario: a pricing calculation, first as a plain library call, then promoted step by step into a real microservice you can redeploy on its own.

### Level 1 — Basic

```java
// File: PricingLibrary.java -- pricing logic as an ordinary library class
public class PricingLibrary {
    static class PricingLib {
        double priceFor(String item) {
            return switch (item) {
                case "widget" -> 9.99;
                case "gadget" -> 19.99;
                default -> 0.0;
            };
        }
    }

    public static void main(String[] args) {
        PricingLib pricing = new PricingLib();
        System.out.println("widget: $" + pricing.priceFor("widget"));
        System.out.println("gadget: $" + pricing.priceFor("gadget"));
    }
}
```

**How to run:** `javac PricingLibrary.java && java PricingLibrary` (JDK 17+).

Expected output:
```
widget: $9.99
gadget: $19.99
```

`PricingLib` is just a class in the same file, compiled and run together with its caller. To change the pricing logic, you must recompile and redeploy this entire program — there's no way to update pricing without touching everything else.

### Level 2 — Intermediate

```java
// File: PricingService.java -- the SAME pricing logic, now its own process
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class PricingService {
    static double priceFor(String item) {
        return switch (item) {
            case "widget" -> 9.99;
            case "gadget" -> 19.99;
            default -> 0.0;
        };
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(8082), 0);
        server.createContext("/price", exchange -> {
            String item = exchange.getRequestURI().getQuery().replace("item=", "");
            String body = String.valueOf(priceFor(item));
            exchange.sendResponseHeaders(200, body.length());
            exchange.getResponseBody().write(body.getBytes());
            exchange.close();
        });
        server.start();
        System.out.println("PricingService listening on :8082");

        // simulate a caller, in a real system this would be a separate process
        var client = java.net.http.HttpClient.newHttpClient();
        var request = java.net.http.HttpRequest.newBuilder(java.net.URI.create("http://localhost:8082/price?item=widget")).build();
        var response = client.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
        System.out.println("caller received price: $" + response.body());
        server.stop(0);
    }
}
```

**How to run:** `javac PricingService.java && java PricingService` (JDK 17+).

Expected output:
```
PricingService listening on :8082
caller received price: $9.99
```

The pricing logic now lives behind an HTTP endpoint in its own runnable `main`. It has its own process, its own port, and can be started, stopped, and redeployed without touching whatever code calls it — the defining trait of a microservice.

### Level 3 — Advanced

```java
// File: PricingServiceVersions.java -- v1 and v2 running SIDE BY SIDE,
// proving each can be deployed and retired independently of the other.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class PricingServiceVersions {
    static double priceForV1(String item) {
        return switch (item) { case "widget" -> 9.99; case "gadget" -> 19.99; default -> 0.0; };
    }

    static double priceForV2(String item) {
        // v2 changed the pricing model -- deployed without touching v1 at all
        return switch (item) { case "widget" -> 8.49; case "gadget" -> 17.49; default -> 0.0; };
    }

    static HttpServer startService(int port, java.util.function.Function<String, Double> priceFn) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        server.createContext("/price", exchange -> {
            String item = exchange.getRequestURI().getQuery().replace("item=", "");
            String body = String.valueOf(priceFn.apply(item));
            exchange.sendResponseHeaders(200, body.length());
            exchange.getResponseBody().write(body.getBytes());
            exchange.close();
        });
        server.start();
        return server;
    }

    public static void main(String[] args) throws Exception {
        HttpServer v1 = startService(8082, PricingServiceVersions::priceForV1);
        HttpServer v2 = startService(8083, PricingServiceVersions::priceForV2);
        System.out.println("v1 on :8082, v2 on :8083 -- both running independently");

        var client = java.net.http.HttpClient.newHttpClient();
        for (int port : new int[]{8082, 8083}) {
            var request = java.net.http.HttpRequest.newBuilder(java.net.URI.create("http://localhost:" + port + "/price?item=widget")).build();
            var response = client.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
            System.out.println("port " + port + " widget price: $" + response.body());
        }

        // retire v1 WITHOUT touching v2 at all -- independent deployability in action
        v1.stop(0);
        System.out.println("v1 retired; v2 keeps serving traffic unaffected");
        var request = java.net.http.HttpRequest.newBuilder(java.net.URI.create("http://localhost:8083/price?item=widget")).build();
        var response = client.send(request, java.net.http.HttpResponse.BodyHandlers.ofString());
        System.out.println("v2 still serving widget price: $" + response.body());
        v2.stop(0);
    }
}
```

**How to run:** `javac PricingServiceVersions.java && java PricingServiceVersions` (JDK 17+).

Expected output:
```
v1 on :8082, v2 on :8083 -- both running independently
port 8082 widget price: $9.99
port 8083 widget price: $8.49
v1 retired; v2 keeps serving traffic unaffected
v2 still serving widget price: $8.49
```

The production-flavored hard case: two versions of the *same* service run concurrently, on different ports, and one can be stopped (`v1.stop(0)`) without any effect on the other. This is what "independently deployable" means in practice — not just "runs in its own process," but "its lifecycle (start, upgrade, retire) is entirely decoupled from every other service's lifecycle."

## 6. Walkthrough

1. `startService(8082, ...)` and `startService(8083, ...)` each build their own `HttpServer`, bind it to a distinct port, and start it — two fully independent processes-in-miniature, sharing nothing but the JVM they happen to run in for this demo (in production they would be two entirely separate machines or containers).
2. The client sends a `GET /price?item=widget` request to port `8082` first. The request travels over a real TCP connection to `PricingServiceVersions::priceForV1`, which returns `9.99`; the server writes that into the HTTP response body and the client prints `port 8082 widget price: $9.99`.
3. The same request goes to port `8083` next, hitting `priceForV2`, which returns a different number (`8.49`) — proof the two versions have genuinely independent logic, not just independent ports.
4. `v1.stop(0)` shuts down only the `v1` server. Nothing about `v2`'s process, port, or state is touched.
5. A final request to port `8083` succeeds exactly as before, printing `$8.49` — `v2` never noticed `v1` was retired, because the two were never coupled to begin with.

```
client -> GET /price?item=widget -> :8082 (v1) -> 9.99
client -> GET /price?item=widget -> :8083 (v2) -> 8.49
                    v1.stop(0)
client -> GET /price?item=widget -> :8083 (v2) -> 8.49  (unaffected)
```

## 7. Gotchas & takeaways

> **Gotcha:** running code in a separate process is *necessary* but not *sufficient* to call it a microservice. If deploying `v2` always requires redeploying some other service in lockstep (a shared database schema migration, a shared config file, a coordinated release), you have a "distributed monolith" — extra network hops with none of the independent-deployability benefit.

- A microservice = single responsibility + own process/address + independent deployability. All three, together.
- The test for "is this really a microservice" is operational, not architectural: can you ship a new version of it, alone, right now, without anyone else's code changing?
- A library becomes a microservice the moment you give it its own process and its own deployable release — the logic itself doesn't need to change at all.
- Two versions of a service can coexist and be retired independently, which is exactly what lets teams migrate consumers gradually instead of a risky, coordinated big-bang cutover.
