---
card: microservices
gi: 13
slug: independent-deployability
title: Independent deployability
---

## 1. What it is

**Independent deployability** is the ability to release a new version of one service into production without requiring any other service to be rebuilt, retested, or redeployed at the same time. It is arguably the single most load-bearing property in the entire microservices idea — nearly every other characteristic (componentization via services, decentralized data, infrastructure automation) exists in service of making this one property true and safe.

A system can look like microservices — many small processes, separate repositories, separate databases — and still fail this test, if in practice a release always bundles several services together. That's a "distributed monolith": all the network overhead of microservices, none of the deployment independence.

## 2. Why & when

The whole appeal of splitting a system into services is that different teams can move at different speeds, on different schedules, without blocking each other. If deploying `OrdersService` still requires simultaneously deploying `PaymentsService` because their contracts, database schema, or release process are entangled, you've lost that benefit entirely — you've just added network latency and operational complexity to what is still, functionally, one release unit.

Verify independent deployability continuously, not just at design time: the moment two services' releases need to be coordinated for any reason — a shared migration, a breaking API change, a shared config file both must update together — that's a signal the boundary between them, or the discipline enforcing it, has slipped.

## 3. Core concept

The operational test: pick any one service, and ask two questions.

1. Can I build and test just this service's code, in isolation, without checking out any other service's repository?
2. Can I deploy a new version of just this service, right now, with every other service's currently-running version untouched, and have the system keep working correctly?

If both answers are genuinely "yes," the service is independently deployable. If either is "no" — you need another service's code to build or test yours, or deploying yours breaks something else unless it's redeployed too — independent deployability has been violated somewhere.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Independently deployable services each have their own pipeline; a coupled release forces two services through one shared pipeline together">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Coupled release</text>
  <rect x="30" y="35" width="240" height="35" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="57" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ONE pipeline deploys A + B together</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Independent</text>
  <rect x="380" y="35" width="110" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="435" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Pipeline A</text>
  <rect x="510" y="35" width="110" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="565" y="57" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Pipeline B</text>
  <text x="500" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">each deploys on its own schedule</text>
</svg>

One shared pipeline forces synchronized releases; separate pipelines let each service ship on its own clock.

## 5. Runnable example

Scenario: two services, `OrdersService` and `PaymentsService`, verified for independent deployability by upgrading one while confirming the other's currently-running version and behavior are completely untouched.

### Level 1 — Basic

```java
// File: TwoServices.java -- baseline: two services running, each answering its own version
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class TwoServices {
    static HttpServer versionedService(int port, String version) throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(port), 0);
        s.createContext("/version", ex -> {
            ex.sendResponseHeaders(200, version.length());
            ex.getResponseBody().write(version.getBytes());
            ex.close();
        });
        s.start();
        return s;
    }

    public static void main(String[] args) throws Exception {
        HttpServer orders = versionedService(8095, "orders-v1.0");
        HttpServer payments = versionedService(8096, "payments-v1.0");

        var client = java.net.http.HttpClient.newHttpClient();
        for (int port : new int[]{8095, 8096}) {
            var req = java.net.http.HttpRequest.newBuilder(java.net.URI.create("http://localhost:" + port + "/version")).build();
            System.out.println("port " + port + ": " + client.send(req, java.net.http.HttpResponse.BodyHandlers.ofString()).body());
        }
        orders.stop(0); payments.stop(0);
    }
}
```

**How to run:** `javac TwoServices.java && java TwoServices` (JDK 17+).

Expected output:
```
port 8095: orders-v1.0
port 8096: payments-v1.0
```

Two independently versioned services, each answering its own `/version` endpoint — the baseline before any deploy happens.

### Level 2 — Intermediate

```java
// File: DeployOneService.java -- upgrade ONLY OrdersService; PaymentsService
// stays running, untouched, on its original version throughout.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class DeployOneService {
    static HttpServer versionedService(int port, String version) throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(port), 0);
        s.createContext("/version", ex -> {
            ex.sendResponseHeaders(200, version.length());
            ex.getResponseBody().write(version.getBytes());
            ex.close();
        });
        s.start();
        return s;
    }

    static String checkVersion(HttpClient client, int port) throws Exception {
        var req = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/version")).build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception {
        HttpServer orders = versionedService(8095, "orders-v1.0");
        HttpServer payments = versionedService(8096, "payments-v1.0"); // never touched below

        HttpClient client = HttpClient.newHttpClient();
        System.out.println("before deploy -- orders: " + checkVersion(client, 8095) + ", payments: " + checkVersion(client, 8096));

        orders.stop(0); // deploy pipeline for OrdersService ONLY
        orders = versionedService(8095, "orders-v1.1");

        System.out.println("after deploy  -- orders: " + checkVersion(client, 8095) + ", payments: " + checkVersion(client, 8096));
        orders.stop(0); payments.stop(0);
    }
}
```

**How to run:** `javac DeployOneService.java && java DeployOneService` (JDK 17+).

Expected output:
```
before deploy -- orders: orders-v1.0, payments: payments-v1.0
after deploy  -- orders: orders-v1.1, payments: payments-v1.0
```

`payments`'s process is never stopped or restarted during this whole example. `orders` moves from `v1.0` to `v1.1`, and `checkVersion(client, 8096)` returns exactly the same value both times — proof the deploy of one service had zero observable effect on the other.

### Level 3 — Advanced

```java
// File: VerifyIndependentDeployability.java -- an automated CHECK that fails
// loudly if deploying one service ever changes another's behavior.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;

public class VerifyIndependentDeployability {
    static HttpServer versionedService(int port, String version, java.util.concurrent.atomic.AtomicInteger callCount) throws Exception {
        HttpServer s = HttpServer.create(new InetSocketAddress(port), 0);
        s.createContext("/version", ex -> {
            callCount.incrementAndGet();
            ex.sendResponseHeaders(200, version.length());
            ex.getResponseBody().write(version.getBytes());
            ex.close();
        });
        s.start();
        return s;
    }

    static String checkVersion(HttpClient client, int port) throws Exception {
        var req = HttpRequest.newBuilder(URI.create("http://localhost:" + port + "/version")).build();
        return client.send(req, HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception {
        var paymentsCallCount = new java.util.concurrent.atomic.AtomicInteger(0);
        HttpServer orders = versionedService(8095, "orders-v1.0", new java.util.concurrent.atomic.AtomicInteger(0));
        HttpServer payments = versionedService(8096, "payments-v1.0", paymentsCallCount);
        HttpClient client = HttpClient.newHttpClient();

        String paymentsBefore = checkVersion(client, 8096);
        int callsBefore = paymentsCallCount.get();

        // simulate a full OrdersService deploy: stop, rebuild, restart -- PaymentsService untouched
        orders.stop(0);
        orders = versionedService(8095, "orders-v2.0", new java.util.concurrent.atomic.AtomicInteger(0));

        String paymentsAfter = checkVersion(client, 8096);
        int callsAfter = paymentsCallCount.get();

        boolean independentlyDeployable = paymentsBefore.equals(paymentsAfter) && (callsAfter - callsBefore == 1);
        System.out.println("payments version unchanged: " + paymentsBefore.equals(paymentsAfter));
        System.out.println("payments received exactly the expected traffic: " + (callsAfter - callsBefore == 1));
        System.out.println("VERDICT: independently deployable = " + independentlyDeployable);

        orders.stop(0); payments.stop(0);
    }
}
```

**How to run:** `javac VerifyIndependentDeployability.java && java VerifyIndependentDeployability` (JDK 17+).

Expected output:
```
payments version unchanged: true
payments received exactly the expected traffic: true
VERDICT: independently deployable = true
```

The production-flavored case: this isn't just a demonstration, it's a genuine automated check — it records `PaymentsService`'s version and call count *before* deploying `OrdersService`, deploys `OrdersService` (stop, rebuild, restart with a new version), then re-checks `PaymentsService` afterward. Only if both the version string and the call count are exactly what's expected does it print `independently deployable = true` — the kind of assertion a real deployment pipeline could run automatically after every release, as a regression check against accidental coupling.

## 6. Walkthrough

1. `versionedService(8096, "payments-v1.0", paymentsCallCount)` starts `PaymentsService`, wired to increment `paymentsCallCount` on every `/version` request it handles.
2. `checkVersion(client, 8096)` is called once, recording `paymentsBefore = "payments-v1.0"` and bumping `paymentsCallCount` to `1`; `callsBefore` captures that count.
3. `orders.stop(0)` followed by a fresh `versionedService(8095, "orders-v2.0", ...)` simulates a complete deploy of `OrdersService` — the old process is gone, a new one with a new version is running in its place. `PaymentsService`'s process is never referenced in this step at all.
4. `checkVersion(client, 8096)` runs a second time, hitting `PaymentsService` again, recording `paymentsAfter` and incrementing `paymentsCallCount` to `2`.
5. `independentlyDeployable` checks two things: that `paymentsBefore` and `paymentsAfter` are identical strings (the version never moved), and that `callsAfter - callsBefore == 1` (exactly one new, expected call reached `PaymentsService` — no unexpected extra traffic, no missed request, nothing coupled to the `OrdersService` deploy).
6. Both checks pass, so the final verdict prints `true` — a concrete, automated confirmation that deploying `OrdersService` had zero measurable effect on `PaymentsService`.

```
before: payments version = v1.0, calls = 1
        |
   deploy OrdersService (stop -> rebuild -> restart, v1.0 -> v2.0)
        |
after:  payments version = v1.0 (unchanged), calls = 2 (exactly +1, expected)
        |
   VERDICT: independently deployable
```

## 7. Gotchas & takeaways

> **Gotcha:** independent deployability is easy to lose silently through a shared database schema migration. Two services can have completely separate deploy pipelines and still be coupled if a schema change for one requires the other to deploy in lockstep to avoid breaking — this is exactly why [decentralized data management](0009-decentralized-data-management.md) matters: a service sharing a database with another service can never be fully independently deployable.

- Independent deployability means a new version of one service can go live with zero required changes to any other currently-running service.
- The operational test is two questions: can you build/test this service alone, and can you deploy it alone without breaking anything else?
- A system with many small services that must still be released together on a coordinated schedule is a distributed monolith, not genuinely independently-deployable microservices.
- Automating a check like the one in Level 3 — verifying a deploy of one service leaves another's behavior and traffic pattern unchanged — turns "we believe our services are decoupled" into a continuously verified fact.
