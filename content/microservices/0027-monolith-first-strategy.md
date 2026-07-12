---
card: microservices
gi: 27
slug: monolith-first-strategy
title: Monolith-first strategy
---

## 1. What it is

**Monolith-first**, a term popularized by Martin Fowler, is the strategy of deliberately starting a new system as a single, well-structured monolith, and only extracting services out of it later, once real service boundaries have emerged from genuine usage and the team has a concrete, evidence-based reason to split. It's a direct answer to the temptation to start a brand-new system already split into microservices: you almost never understand a new domain's true boundaries well enough on day one to draw good service lines, and a monolith is far cheaper to refactor internally than a wrong service split is to undo across a network boundary.

## 2. Why & when

Early in a new system's life, the domain model is still being discovered — what looked like two separate concerns on day one often turns out to be one tightly related concept by month three, or vice versa. Drawing a hard service boundary (with its own deploy pipeline, its own data store, its own network contract) around a guess is expensive to undo: merging two wrongly-split services back together, or re-splitting one wrongly-merged service, both require far more coordinated work than moving a class between two packages in one codebase ever would.

Start monolith-first for any genuinely new system or product, and revisit the decision to split once you can point to concrete evidence — a part of the domain whose boundary has stopped shifting, a real, measured difference in load or release cadence between two parts of the codebase, or a team that has grown large enough to genuinely benefit from independent deployability. Skip monolith-first only when you're extending an already-well-understood domain (a second implementation of a pattern your organization has built several times before) where the boundaries are already known with real confidence.

## 3. Core concept

The practical technique for making a later extraction painless: keep the monolith's internal module boundaries clean from day one, even though everything ships together. A well-structured monolith with clear internal module boundaries — even while physically deployed as one process — can have one of its modules extracted into its own service later with comparatively little rework, because the *logical* seam (a clean interface between modules) already existed; only the *physical* seam (a network boundary) needs to be added.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A well-structured monolith with clean internal module boundaries can later have one module extracted into its own service with comparatively little rework">
  <rect x="30" y="35" width="260" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Monolith, one process</text>
  <rect x="45" y="70" width="100" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Orders module</text>
  <rect x="165" y="70" width="110" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="220" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Payments module</text>

  <line x1="300" y1="80" x2="380" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a27)"/>
  <text x="340" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">extract later</text>

  <rect x="390" y="35" width="100" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Orders module</text>
  <text x="440" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(stays in monolith)</text>

  <rect x="510" y="35" width="110" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="565" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">PaymentsService</text>
  <text x="565" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(extracted, own process)</text>
  <defs><marker id="a27" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A clean internal module boundary, kept from day one, becomes the seam a later extraction can follow with minimal rework.

## 5. Runnable example

Scenario: a new system started as a monolith with clean internal module boundaries, evolved to show that boundary being cheap to change internally, then actually extracted into a separate service once real evidence justifies it.

### Level 1 — Basic

```java
// File: MonolithWithCleanModules.java -- ONE process, but a CLEAN internal
// interface between Orders and Payments -- the seam a future extraction will follow.
public class MonolithWithCleanModules {
    interface PaymentsModule { String charge(double amount); } // the clean seam

    static class PaymentsModuleImpl implements PaymentsModule {
        public String charge(double amount) { return "charged $" + amount; }
    }

    static class OrdersModule {
        PaymentsModule payments; // depends on the INTERFACE, not a concrete class
        OrdersModule(PaymentsModule payments) { this.payments = payments; }
        String placeOrder(double total) { return "order placed, " + payments.charge(total); }
    }

    public static void main(String[] args) {
        OrdersModule orders = new OrdersModule(new PaymentsModuleImpl());
        System.out.println(orders.placeOrder(9.99));
    }
}
```

**How to run:** `javac MonolithWithCleanModules.java && java MonolithWithCleanModules` (JDK 17+).

Expected output:
```
order placed, charged $9.99
```

`OrdersModule` depends only on the `PaymentsModule` interface, never on `PaymentsModuleImpl` directly — even though everything runs in one process today, this is the exact seam a real service extraction would follow later.

### Level 2 — Intermediate

```java
// File: DomainUnderstandingShifts.java -- the domain model CHANGES during
// early development -- cheap to fix, because it's still all in one process.
public class DomainUnderstandingShifts {
    interface PaymentsModule { String charge(double amount, String currency); } // requirement CHANGED: now needs currency

    static class PaymentsModuleImpl implements PaymentsModule {
        public String charge(double amount, String currency) { return "charged " + amount + " " + currency; }
    }

    static class OrdersModule {
        PaymentsModule payments;
        OrdersModule(PaymentsModule payments) { this.payments = payments; }
        String placeOrder(double total, String currency) { return "order placed, " + payments.charge(total, currency); }
    }

    public static void main(String[] args) {
        // this change (adding a currency parameter) touched ONE interface and its ONE implementation --
        // a straightforward, local, same-process refactor, NOT a coordinated cross-service API migration.
        OrdersModule orders = new OrdersModule(new PaymentsModuleImpl());
        System.out.println(orders.placeOrder(9.99, "USD"));
    }
}
```

**How to run:** `javac DomainUnderstandingShifts.java && java DomainUnderstandingShifts` (JDK 17+).

Expected output:
```
order placed, charged 9.99 USD
```

The `PaymentsModule` contract changed (added a `currency` parameter) as the team's domain understanding matured — this was a same-process refactor, touching one interface and one implementation, with the compiler catching every call site that needed updating. Had this already been a separately deployed `PaymentsService`, this same change would have needed a coordinated API version migration across every consumer.

### Level 3 — Advanced

```java
// File: ExtractOnceJustified.java -- NOW extract PaymentsModule into its
// OWN service, since real evidence (a measured load difference) justifies it.
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class ExtractOnceJustified {
    interface PaymentsModule { String charge(double amount, String currency); }

    // the SAME interface OrdersModule always depended on -- unchanged by the extraction
    static class OrdersModule {
        PaymentsModule payments;
        OrdersModule(PaymentsModule payments) { this.payments = payments; }
        String placeOrder(double total, String currency) { return "order placed, " + payments.charge(total, currency); }
    }

    // EXTRACTED: PaymentsModule's logic now lives behind a real network call,
    // because real evidence showed payments needed independent scaling.
    static class RemotePaymentsClient implements PaymentsModule {
        public String charge(double amount, String currency) {
            try {
                var client = java.net.http.HttpClient.newHttpClient();
                var request = java.net.http.HttpRequest.newBuilder(
                    java.net.URI.create("http://localhost:8097/charge?amount=" + amount + "&currency=" + currency)).build();
                return client.send(request, java.net.http.HttpResponse.BodyHandlers.ofString()).body();
            } catch (Exception e) { throw new RuntimeException(e); }
        }
    }

    public static void main(String[] args) throws Exception {
        HttpServer paymentsService = HttpServer.create(new InetSocketAddress(8097), 0);
        paymentsService.createContext("/charge", ex -> {
            var query = ex.getRequestURI().getQuery();
            String body = "charged " + query.replace("amount=", "").replace("&currency=", " ");
            ex.sendResponseHeaders(200, body.length());
            ex.getResponseBody().write(body.getBytes());
            ex.close();
        });
        paymentsService.start();

        // OrdersModule's OWN CODE never changed -- it still just calls payments.charge(...) through the SAME interface
        OrdersModule orders = new OrdersModule(new RemotePaymentsClient());
        System.out.println(orders.placeOrder(9.99, "USD"));
        paymentsService.stop(0);
    }
}
```

**How to run:** `javac ExtractOnceJustified.java && java ExtractOnceJustified` (JDK 17+).

Expected output:
```
order placed, charged 9.99 USD
```

The production-flavored payoff: `OrdersModule`'s source code — `placeOrder`, the field, the constructor — is completely unchanged from Level 2. Only a new implementation of `PaymentsModule`, `RemotePaymentsClient`, was introduced, making a real HTTP call to a genuinely separate `PaymentsService` process. This is exactly what monolith-first promises: because the interface boundary was kept clean from day one, extracting the implementation behind it into a real service required no changes to the calling code at all.

## 6. Walkthrough

1. `paymentsService` starts as a real, standalone `HttpServer` on port `8097` — this represents `PaymentsService` now running as its own genuinely separate process, the result of the extraction decision.
2. `new OrdersModule(new RemotePaymentsClient())` constructs `OrdersModule` exactly as before, except this time it's handed a `RemotePaymentsClient` instead of the old in-process `PaymentsModuleImpl` — both implement the same `PaymentsModule` interface, so `OrdersModule`'s constructor and field declaration required zero changes.
3. `orders.placeOrder(9.99, "USD")` calls `payments.charge(9.99, "USD")` exactly as it always has — but this time, because `payments` is a `RemotePaymentsClient`, that call sends a real HTTP `GET` request to `http://localhost:8097/charge?amount=9.99&currency=USD`.
4. `paymentsService`'s handler reads the query string, builds a response body like `"charged 9.99 USD"`, and sends it back over HTTP.
5. `RemotePaymentsClient.charge` receives that HTTP response and returns its body string, which flows back up through `OrdersModule.placeOrder` exactly as an in-process return value would have — `OrdersModule` has no way to tell, from its own code's perspective, that the implementation behind `PaymentsModule` is now a network call instead of a local object.

```
Monolith-first, Level 1-2: OrdersModule -> PaymentsModule (interface) -> PaymentsModuleImpl (in-process)
Extraction,     Level 3:   OrdersModule -> PaymentsModule (interface) -> RemotePaymentsClient -> HTTP -> PaymentsService (own process)
                                    ^ unchanged the whole way through ^
```

## 7. Gotchas & takeaways

> **Gotcha:** monolith-first only pays off if the internal module boundaries are kept genuinely clean throughout — a monolith where every module freely reaches into every other module's internals (no interfaces, shared mutable state everywhere) gives you none of this extraction benefit; you'd face the same painful, tangled untangling a poorly-organized monolith always requires, regardless of the "monolith-first" label.

- Monolith-first means starting a new system as a single, well-structured monolith and extracting services later, once real domain boundaries and genuine scaling needs have emerged from evidence, not guesses.
- The key technique that makes later extraction cheap: keep internal module boundaries clean (interfaces, not direct concrete-class coupling) from day one, even while everything ships as one deployable unit.
- A domain model refactor within a monolith (changing an interface and its one implementation) is a same-process, compiler-checked change; the same refactor after a premature service split becomes a coordinated, multi-team API migration.
- Extracting a service later, from a cleanly-bounded monolith module, should require changing only the implementation behind an existing interface — not the calling code that already depended on that interface.
