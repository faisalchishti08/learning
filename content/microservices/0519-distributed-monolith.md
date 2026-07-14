---
card: microservices
gi: 519
slug: distributed-monolith
title: "Distributed monolith"
---

## 1. What it is

A **distributed monolith** is a system split into multiple deployed services that still behaves like a single tightly-coupled monolith underneath — services can't be deployed independently, can't fail independently, and can't be understood independently, because they're bound together by shared databases, synchronous call chains, or lockstep release schedules. It has all the operational cost of distribution (network calls, deployment complexity, service discovery) with none of the benefits (independent deployability, fault isolation, independent scaling) that were the entire reason to split the monolith in the first place.

## 2. Why & when

You need to recognize a distributed monolith because it's an easy trap to fall into gradually, and because it's strictly worse than either a real monolith or real microservices:

- **It happens through small, individually reasonable decisions** — one team adds "just this one" synchronous call to another service to save time, another shares a database table because standing up a new one feels like overhead, another couples two services' release versions because "they always change together anyway." None of these decisions looks wrong in isolation; together they recreate a monolith's coupling with a microservice's operational overhead.
- **The tell-tale symptom is that deploying one service requires deploying (or at least coordinating with) others** — if Service A's team can't ship a change without checking with Service B's team and lining up a joint release, the services are not actually independently deployable, regardless of how many separate repos or deployment pipelines exist.
- **Another tell is cascading failure**: if Service A being slow or down reliably takes Service B and C down with it (through synchronous call chains or shared resource exhaustion), the services don't actually fail independently — an outage in one is an outage in all, exactly like a monolith, just with extra network hops in between.
- **The fix is architectural, not organizational** — recognizing the coupling for what it is (shared data, synchronous chains, contract fragility) and addressing the specific cause, whether that's giving each service its own database, replacing a synchronous call with an async event, or hardening the API contract so callers don't break on unrelated changes.

## 3. Core concept

Think of a company that reorganizes one big open-plan office into separate private offices — but leaves every desk phone wired through party lines where every call gets picked up by three other offices, keeps one shared filing cabinet nobody has exclusive access to, and requires every department to submit their weekly report on the same Friday or none of them can leave for the weekend. Giving everyone separate offices didn't actually decouple anyone's work; it just added walls and travel time between people who still can't act independently. Real independence would mean each office has its own phone line, its own filing cabinet, and its own schedule — the distributed monolith is separate offices without separate anything else.

Concretely, the usual causes are:

1. **A shared database** that multiple services read and write directly — any service can be broken by another service's schema change, and no service can evolve its data model without coordinating with everyone else who touches that table.
2. **Long synchronous call chains** — Service A calls B calls C calls D synchronously to answer one request, so D being slow makes A slow, and D being down can make A fail entirely, collapsing the fault boundary between four supposedly independent services into one.
3. **Brittle, versioned-in-lockstep contracts** — if Service A's client code breaks whenever Service B changes its response shape even slightly, the two services can't actually release on independent schedules, no matter how separate their codebases and pipelines are.
4. **Shared, synchronized deployment schedules** — if two services must always be deployed together because their contracts are too tightly coupled to tolerate any version skew, they are, for deployment purposes, one system wearing two names.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Real microservices deploy and fail independently; a distributed monolith looks separated on a diagram but is coupled by a shared database and synchronous chains underneath">
  <text x="150" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Looks like microservices</text>
  <rect x="30" y="40" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="150" y="40" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="195" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service B</text>
  <rect x="270" y="40" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service C</text>

  <text x="195" y="112" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">but underneath...</text>
  <rect x="30" y="130" width="330" height="34" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="195" y="151" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ONE shared database, all three read/write directly</text>
  <line x1="75" y1="80" x2="150" y2="130" stroke="#f0883e" stroke-width="1"/>
  <line x1="195" y1="80" x2="195" y2="130" stroke="#f0883e" stroke-width="1"/>
  <line x1="315" y1="80" x2="240" y2="130" stroke="#f0883e" stroke-width="1"/>

  <text x="500" y="24" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Real microservices</text>
  <rect x="420" y="40" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="460" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service A</text>
  <rect x="420" y="90" width="80" height="26" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="460" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own DB</text>

  <rect x="540" y="40" width="80" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="580" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service B</text>
  <rect x="540" y="90" width="80" height="26" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="580" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own DB</text>
  <text x="530" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deploy, fail, and scale independently</text>
</svg>

Separate boxes on an architecture diagram don't guarantee independence — a shared database or synchronous chain underneath recreates monolith-style coupling.

## 5. Runnable example

Scenario: an order-processing setup with an Order service and an Inventory service. We start with the distributed-monolith version, where both services read and write the same shared table directly, extend it to show the cascading-failure symptom of a synchronous call chain, then handle the fix: each service owns its own data and communicates only through a well-defined API, decoupling their deployments and failure modes.

### Level 1 — Basic

```java
// File: SharedDatabaseAntiPattern.java -- simulates the DISTRIBUTED
// MONOLITH symptom: Order and Inventory "services" both read/write
// the SAME shared table directly, with no owning service in between.
import java.util.*;

public class SharedDatabaseAntiPattern {
    // one shared table both "services" reach into directly
    static Map<String, Integer> sharedInventoryTable = new HashMap<>(Map.of("widget", 10));

    static class OrderService {
        void placeOrder(String item, int qty) {
            int current = sharedInventoryTable.get(item); // reaches directly into Inventory's table
            sharedInventoryTable.put(item, current - qty); // writes it directly too
            System.out.println("[OrderService] placed order, decremented shared table directly");
        }
    }

    static class InventoryService {
        void restock(String item, int qty) {
            int current = sharedInventoryTable.get(item);
            sharedInventoryTable.put(item, current + qty);
            System.out.println("[InventoryService] restocked, wrote shared table directly");
        }
    }

    public static void main(String[] args) {
        new OrderService().placeOrder("widget", 3);
        new InventoryService().restock("widget", 5);
        System.out.println("Final shared table state: " + sharedInventoryTable);
        System.out.println("Problem: if Inventory changes this table's schema, OrderService breaks with NO warning -- they're coupled at the data layer.");
    }
}
```

How to run: `java SharedDatabaseAntiPattern.java`

Both "services" reach directly into `sharedInventoryTable` — there's no encapsulation, no owning service, and no API between them. This compiles and runs fine today, but it means `InventoryService`'s team cannot change the table's shape (rename a field, split a column, add a constraint) without breaking `OrderService`, even though they're nominally separate services with separate teams and separate deploy pipelines.

### Level 2 — Intermediate

```java
// File: SynchronousChainAntiPattern.java -- shows the CASCADING FAILURE
// symptom: Order calls Inventory calls Pricing synchronously, so a slow
// or failing Pricing service takes down the entire chain above it.
public class SynchronousChainAntiPattern {
    static class PricingService {
        double getPrice(String item) throws InterruptedException {
            Thread.sleep(3000); // simulates Pricing being unhealthy/slow right now
            return 9.99;
        }
    }

    static class InventoryService {
        PricingService pricing = new PricingService();
        String checkAndPrice(String item) throws InterruptedException {
            double price = pricing.getPrice(item); // BLOCKS on Pricing synchronously
            return item + " priced at $" + price;
        }
    }

    static class OrderService {
        InventoryService inventory = new InventoryService();
        String placeOrder(String item) throws InterruptedException {
            return inventory.checkAndPrice(item); // BLOCKS on Inventory, which blocks on Pricing
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        String result = new OrderService().placeOrder("widget");
        System.out.println(result + " (took " + (System.currentTimeMillis() - start) + "ms)");
        System.out.println("Problem: OrderService's response time is now HOSTAGE to Pricing's -- three 'independent' services, one failure domain.");
    }
}
```

How to run: `java SynchronousChainAntiPattern.java`

`OrderService.placeOrder` calls `InventoryService.checkAndPrice`, which calls `PricingService.getPrice` — all synchronously, all on the same call stack. Pricing's simulated 3-second slowness propagates unchanged all the way up to Order's response time. If Pricing were down entirely rather than just slow, Order would fail entirely too — three services deployed and scaled separately, but sharing one failure domain end to end.

### Level 3 — Advanced

```java
// File: DecoupledFix.java -- the FIX: each service owns its OWN data
// exclusively, exposes a narrow API instead of shared tables, and uses
// a timeout + fallback instead of an unbounded synchronous chain.
import java.util.*;
import java.util.concurrent.*;

public class DecoupledFix {
    static class InventoryService {
        private Map<String, Integer> ownInventory = new HashMap<>(Map.of("widget", 10)); // owned exclusively

        // the ONLY way anyone touches this data: through this method, never direct table access
        synchronized boolean reserve(String item, int qty) {
            int current = ownInventory.getOrDefault(item, 0);
            if (current < qty) return false;
            ownInventory.put(item, current - qty);
            return true;
        }
    }

    static class PricingService {
        CompletableFuture<Double> getPriceAsync(String item, boolean simulateSlow) {
            return CompletableFuture.supplyAsync(() -> {
                try { Thread.sleep(simulateSlow ? 3000 : 50); } catch (InterruptedException e) { throw new RuntimeException(e); }
                return 9.99;
            }).orTimeout(500, TimeUnit.MILLISECONDS)
              .exceptionally(ex -> -1.0); // fallback price when Pricing is slow/down
        }
    }

    static class OrderService {
        InventoryService inventory = new InventoryService();
        PricingService pricing = new PricingService();

        String placeOrder(String item, int qty) throws Exception {
            boolean reserved = inventory.reserve(item, qty); // through InventoryService's API, not its table
            if (!reserved) return "Order REJECTED: insufficient inventory";
            double price = pricing.getPriceAsync(item, true).get(); // bounded wait, degrades gracefully
            String priceText = price < 0 ? "price pending (will confirm async)" : "$" + price;
            return "Order ACCEPTED for " + qty + "x " + item + ", " + priceText;
        }
    }

    public static void main(String[] args) throws Exception {
        long start = System.currentTimeMillis();
        String result = new OrderService().placeOrder("widget", 3);
        System.out.println(result + " (took " + (System.currentTimeMillis() - start) + "ms)");
        System.out.println("Fix: Inventory's data is private to it; Pricing's slowness is bounded and degrades instead of cascading.");
    }
}
```

How to run: `java DecoupledFix.java`

`InventoryService.ownInventory` is a private field accessed only through `reserve(...)` — no other service can touch it directly, so `InventoryService`'s team can change its internal representation freely as long as `reserve`'s contract holds. `PricingService.getPriceAsync` bounds the wait to 500ms with a fallback, so Order's response time is capped regardless of how slow Pricing actually is (here, simulated at 3000ms) — the order still completes in roughly 500ms with a "price pending" stand-in value instead of hanging for 3 seconds or failing outright.

## 6. Walkthrough

Trace `DecoupledFix.main` end to end, contrasting it with the Level 2 anti-pattern:

1. **`OrderService.placeOrder("widget", 3)` is called.** First it calls `inventory.reserve("widget", 3)` — not a direct table write, but a call through `InventoryService`'s own API.
2. **Inside `reserve`, `InventoryService` checks its private `ownInventory` map**, finds `10 >= 3`, decrements to `7`, and returns `true`. No other service could have performed this check-and-decrement directly; it's entirely encapsulated.
3. **Back in `placeOrder`, since reservation succeeded, it calls `pricing.getPriceAsync("widget", true)`**, which immediately returns a `CompletableFuture` (not blocking yet) with `.orTimeout(500ms)` and `.exceptionally(...)` already chained on.
4. **`.get()` is called on that future, which is where `placeOrder` actually waits** — but only up to the 500ms timeout, not the full 3000ms the simulated Pricing call would otherwise take.
5. **At the 500ms mark, `orTimeout` fires** (since the underlying sleep needs 3000ms), converting the future to a `TimeoutException`, which `.exceptionally(...)` catches and replaces with the fallback value `-1.0`.
6. **`placeOrder` receives `price = -1.0`, recognizes it as the fallback sentinel**, and builds the response text `"price pending (will confirm async)"` instead of propagating a failure or hanging.
7. **`main` prints the final order confirmation and the elapsed time** — roughly 500ms, not 3000ms, demonstrating the bounded, degraded response instead of the Level 2 chain's full cascading delay.

Contrast directly with Level 2: there, `OrderService.placeOrder` took the *full* 3000ms because every call in the chain was a plain, unbounded synchronous call — Order's fate was entirely tied to Pricing's. Here, the same three-service shape survives Pricing being slow because the coupling was replaced with an owned API (for data) and a bounded, gracefully-degrading call (for cross-service communication) — the two specific fixes that turn a distributed monolith back into real microservices.

## 7. Gotchas & takeaways

> **Gotcha:** splitting a monolith into separate deployables without addressing shared databases or synchronous call chains doesn't eliminate the coupling — it just adds network latency and operational complexity on top of exactly the same monolith you started with, making it strictly worse than not splitting at all.

- The tell-tale sign of a distributed monolith is that services can't be deployed, scaled, or fail independently — count the number of teams you'd need to coordinate with to ship one change safely; more than one team means real coupling still exists underneath.
- Give each service exclusive ownership of its own data — no other service should read or write another's tables directly, even if it's technically reachable.
- Replace unbounded synchronous call chains with either asynchronous messaging or bounded, fallback-equipped calls, so one service's slowness doesn't become every upstream caller's slowness too.
- A distributed monolith is usually the result of many individually reasonable shortcuts, not one bad decision — watch for "just this once" shared-table access or "just this one synchronous call" creeping in during normal feature work.
