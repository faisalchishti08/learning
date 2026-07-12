---
card: microservices
gi: 4
slug: componentization-via-services
title: Componentization via services
---

## 1. What it is

**Componentization via services** is the first Lewis & Fowler characteristic: a microservices system builds its "components" — its independently replaceable units of software — as **services** communicating over the network, rather than as **libraries** linked into a shared process at compile time. A library is a component you upgrade by recompiling and redeploying everything that depends on it. A service is a component you upgrade by deploying a new version of it alone; every caller keeps working against the same network interface, unaware anything changed underneath.

## 2. Why & when

Libraries are the natural first choice for splitting up code, and they work well within a single deployable process: fast, in-process calls, and the compiler catches interface mismatches immediately. Their weakness shows up at release time: changing a library means every consumer of it must be recompiled and, in most environments, redeployed together, whether or not their own code actually changed. That's fine for a handful of internal utility classes. It becomes a real bottleneck when a "component" is something a whole team owns and wants to release on their own schedule.

Choose service-based componentization when you specifically need that independent release cadence — a pricing engine a pricing team wants to update weekly without coordinating with every consumer. Keep using plain libraries for genuinely internal, stable pieces of logic that don't need their own release schedule; wrapping every small utility class in an HTTP service adds real latency and operational cost for no benefit.

## 3. Core concept

The mechanical difference is where the "seam" between components sits:

- **Library componentization:** the seam is a Java interface or class boundary, resolved at **compile time**. Upgrading it requires a new build of every consumer.
- **Service componentization:** the seam is a network API, resolved at **run time**. Upgrading it requires only redeploying the service; consumers keep calling the same address with the same contract.

The tradeoff is real, not free: a network call can fail, time out, or add latency that a method call never would — service componentization buys independent deployability at the cost of that added complexity.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Library componentization resolves at compile time; service componentization resolves at run time over the network">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Library seam</text>
  <rect x="30" y="40" width="240" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller.class + PricingLib.class</text>
  <text x="150" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">seam resolved at COMPILE TIME</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Service seam</text>
  <rect x="360" y="40" width="110" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="415" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Caller</text>
  <rect x="500" y="40" width="120" height="55" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PricingService</text>
  <line x1="470" y1="67" x2="500" y2="67" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a4)"/>
  <text x="490" y="115" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">seam resolved at RUN TIME (HTTP)</text>
  <defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same pricing logic, different seam: compile-time linkage versus a run-time network contract.

## 5. Runnable example

Scenario: a pricing component upgraded from v1 to v2 pricing logic, first as a library (forcing a caller rebuild), then as a service (upgraded with zero changes to the caller).

### Level 1 — Basic

```java
// File: LibraryComponent.java -- PricingLib compiled directly into the caller
public class LibraryComponent {
    static class PricingLib {
        double priceFor(String item) {
            return switch (item) { case "widget" -> 9.99; default -> 0.0; }; // v1 pricing
        }
    }

    public static void main(String[] args) {
        PricingLib pricing = new PricingLib(); // caller is bound to THIS exact class at compile time
        System.out.println("widget: $" + pricing.priceFor("widget"));
    }
}
```

**How to run:** `javac LibraryComponent.java && java LibraryComponent` (JDK 17+).

Expected output:
```
widget: $9.99
```

To release v2 pricing (say, `8.49`), you edit `PricingLib`, then must recompile `LibraryComponent.java` as a whole — the caller and the component are one compiled unit, so there is no way to ship one without the other.

### Level 2 — Intermediate

```java
// File: ServiceComponent.java -- PricingService as a separately runnable process;
// the caller only knows an HTTP contract, not a Java class.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class ServiceComponent {
    static HttpServer startPricingV1() throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(8093), 0);
        s.createContext("/price", ex -> {
            String item = ex.getRequestURI().getQuery().replace("item=", "");
            String body = item.equals("widget") ? "9.99" : "0.0";
            ex.sendResponseHeaders(200, body.length());
            ex.getResponseBody().write(body.getBytes());
            ex.close();
        });
        s.start();
        return s;
    }

    static String callPricing(HttpClient client, String item) throws Exception {
        var req = HttpRequest.newBuilder(URI.create("http://localhost:8093/price?item=" + item)).build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception {
        HttpServer pricing = startPricingV1();
        HttpClient client = HttpClient.newHttpClient();
        System.out.println("widget: $" + callPricing(client, "widget")); // caller ONLY knows the HTTP contract
        pricing.stop(0);
    }
}
```

**How to run:** `javac ServiceComponent.java && java ServiceComponent` (JDK 17+).

Expected output:
```
widget: $9.99
```

The caller (`callPricing`) has no compile-time dependency on any pricing class at all — just a URL and a string contract. The pricing team can now change `startPricingV1`'s internals freely without the caller's source ever needing to change.

### Level 3 — Advanced

```java
// File: ServiceComponentUpgrade.java -- upgrade pricing to v2 WITHOUT
// recompiling or even restarting the caller's code.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class ServiceComponentUpgrade {
    static HttpServer startPricing(int port, String widgetPrice) throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(port), 0);
        s.createContext("/price", ex -> {
            String item = ex.getRequestURI().getQuery().replace("item=", "");
            String body = item.equals("widget") ? widgetPrice : "0.0";
            ex.sendResponseHeaders(200, body.length());
            ex.getResponseBody().write(body.getBytes());
            ex.close();
        });
        s.start();
        return s;
    }

    static String callPricing(HttpClient client, int port, String item) throws Exception {
        var req = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/price?item=" + item)).build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        // v1 deployed on port 8093 -- caller code below NEVER references PricingLib or any version-specific class
        HttpServer v1 = startPricing(8093, "9.99");
        System.out.println("before upgrade, widget: $" + callPricing(client, 8093, "widget"));
        v1.stop(0);

        // v1 retired, v2 deployed on the SAME contract, SAME port -- a real deploy, not a caller change
        HttpServer v2 = startPricing(8093, "8.49");
        System.out.println("after upgrade,  widget: $" + callPricing(client, 8093, "widget"));
        v2.stop(0);
    }
}
```

**How to run:** `javac ServiceComponentUpgrade.java && java ServiceComponentUpgrade` (JDK 17+).

Expected output:
```
before upgrade, widget: $9.99
after upgrade,  widget: $8.49
```

The production-flavored hard case: `callPricing` is called twice with **identical code**, yet returns two different prices, because the *service* behind port `8093` was swapped out between calls — exactly what a real deploy of a new `PricingService` version looks like from a consumer's perspective. No caller recompilation, no caller redeploy, just a new response from the same contract.

## 6. Walkthrough

1. `startPricing(8093, "9.99")` boots the v1 pricing service and starts listening on port `8093` — this models the pricing team's currently-deployed release.
2. `callPricing(client, 8093, "widget")` sends `GET /price?item=widget` to that port; v1's handler reads the query string, matches `"widget"`, and writes back the string `"9.99"` as the full response body.
3. `v1.stop(0)` retires the v1 process — this models the pricing team beginning a deploy of a new version.
4. `startPricing(8093, "8.49")` starts v2 on the exact same port `8093`, with the same `/price` contract but different internal pricing data — this models the new version going live.
5. The second `callPricing` call is byte-for-byte the same Java call as the first one. It sends the same request to the same port, and the JDK's `HttpClient` has no idea the process behind that port has changed — it just gets back a different response body, `"8.49"`.
6. This is componentization via services in action: the "component" (`PricingService`) was upgraded, but the caller's compiled code, `.class` files, and running process needed zero changes.

```
Library:  caller.class depends on PricingLib.class at COMPILE TIME -> upgrade PricingLib -> must rebuild caller
Service:  caller depends on "GET /price?item=X" CONTRACT at RUN TIME -> redeploy PricingService -> caller untouched
```

## 7. Gotchas & takeaways

> **Gotcha:** service componentization only delivers this benefit if the network **contract** (the URL, request shape, response shape) stays stable across the upgrade. If v2 had changed the response format — say, from a plain number to JSON — the caller's parsing code would break even though it was "just" a service upgrade. The contract, not just the process boundary, is what must stay compatible.

- Library componentization resolves its seam at compile time: upgrading forces a rebuild of every consumer.
- Service componentization resolves its seam at run time over a network contract: upgrading only requires redeploying the service, as long as the contract stays compatible.
- Not every component needs to be a service — wrapping small, stable, internal utility code in HTTP adds real latency and operational overhead for no independent-deployability benefit.
- Choose service componentization specifically where independent release cadence for that component is a real requirement, not a default for every class in the system.
