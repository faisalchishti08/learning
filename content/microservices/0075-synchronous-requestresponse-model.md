---
card: microservices
gi: 75
slug: synchronous-request-response-model
title: "Synchronous request/response model"
---

## 1. What it is

The synchronous request/response model is the simplest way one microservice can talk to another: Service A sends a request over the network to Service B and *blocks* — waits, holding the calling thread (or, in async I/O, the logical call) — until Service B sends back a response. Only once that response arrives does Service A continue executing. This is the same interaction shape as a normal function call, just carried out over the network instead of within one process, and it's the model underlying plain REST-over-HTTP calls between services.

## 2. Why & when

Synchronous calls are the natural first choice because they're the easiest to reason about: the caller's code reads top to bottom exactly like calling a local method, the response is immediately available for use, and errors surface directly as an exception or an error response the caller can handle right there. This simplicity is also the model's core limitation: while Service A is waiting on Service B, Service A's thread is tied up, and if Service B is slow or unresponsive, that slowness directly becomes Service A's slowness too — a chain of synchronous calls across several services means the total latency is (at least) the sum of every hop, and a failure anywhere in the chain can cascade back to the original caller.

Reach for synchronous request/response when the caller genuinely needs the result before it can proceed — checking current inventory before confirming an order, looking up a customer's details to render a page. Reach for an asynchronous, event-driven alternative instead when the caller doesn't need an immediate answer, or when tolerating the callee's slowness would otherwise leak straight back to the end user.

## 3. Core concept

The calling thread is occupied for the entire round trip; total latency for a chain of synchronous calls accumulates hop by hop.

```
OrderService --request--> InventoryService
     |  (BLOCKED, waiting)      |
     |                     does work...
     |  <--response--------------|
   continues
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A sequence diagram showing OrderService sending a request to InventoryService and blocking until the response returns, then continuing execution">
  <line x1="100" y1="20" x2="100" y2="170" stroke="#8b949e" stroke-width="1"/>
  <line x1="480" y1="20" x2="480" y2="170" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="15" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="480" y="15" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">InventoryService</text>

  <line x1="100" y1="55" x2="475" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a75)"/>
  <text x="290" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">GET /inventory/widget</text>

  <rect x="94" y="55" width="12" height="80" fill="#1c2430" stroke="#79c0ff"/>
  <text x="115" y="100" fill="#79c0ff" font-size="7.5" font-family="sans-serif">blocked, waiting</text>

  <line x1="480" y1="70" x2="480" y2="110" stroke="#8b949e" stroke-width="6"/>
  <text x="520" y="95" fill="#8b949e" font-size="7.5" font-family="sans-serif">doing work</text>

  <line x1="480" y1="135" x2="105" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a75)"/>
  <text x="290" y="128" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">200 OK { quantity: 5 }</text>

  <defs>
    <marker id="a75" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

OrderService's thread is occupied for the full round trip before it can continue.

## 5. Runnable example

Scenario: `OrderService` needs stock data from `InventoryService` before it can confirm an order, first modeled with a slow synchronous call blocking the caller for its full duration, then measured to show latency accumulates, then extended to a chain of two sequential synchronous calls to show the accumulation compounding across hops.

### Level 1 — Basic

```java
// File: SingleSynchronousCall.java -- OrderService BLOCKS while
// InventoryService "does work" (simulated with a sleep, standing in for
// network latency + processing time).
public class SingleSynchronousCall {
    static class InventoryService {
        int checkStock(String sku) throws InterruptedException {
            Thread.sleep(200); // simulates network + processing latency
            return 5;
        }
    }

    static class OrderService {
        InventoryService inventory = new InventoryService();
        void confirmOrder(String sku) throws InterruptedException {
            System.out.println("[Order] requesting stock for " + sku + "...");
            int stock = inventory.checkStock(sku); // BLOCKS here until InventoryService responds
            System.out.println("[Order] received stock=" + stock + ", continuing");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        new OrderService().confirmOrder("widget");
    }
}
```

**How to run:** `javac SingleSynchronousCall.java && java SingleSynchronousCall` (JDK 17+).

Expected output:
```
[Order] requesting stock for widget...
[Order] received stock=5, continuing
```

`OrderService.confirmOrder` genuinely pauses at `inventory.checkStock(sku)` for the full 200ms before the second line prints — nothing else in that thread runs during that wait.

### Level 2 — Intermediate

```java
// File: MeasuredLatency.java -- SAME call, now measuring elapsed time
// to make the blocking cost visible and concrete, not just implied.
public class MeasuredLatency {
    static class InventoryService {
        int checkStock(String sku) throws InterruptedException {
            Thread.sleep(200);
            return 5;
        }
    }

    static class OrderService {
        InventoryService inventory = new InventoryService();
        void confirmOrder(String sku) throws InterruptedException {
            long start = System.currentTimeMillis();
            int stock = inventory.checkStock(sku);
            long elapsed = System.currentTimeMillis() - start;
            System.out.println("[Order] stock=" + stock + ", caller was blocked for ~" + elapsed + "ms");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        new OrderService().confirmOrder("widget");
    }
}
```

**How to run:** `javac MeasuredLatency.java && java MeasuredLatency` (JDK 17+).

Expected output (elapsed time will vary slightly, always at least 200):
```
[Order] stock=5, caller was blocked for ~200ms
```

### Level 3 — Advanced

```java
// File: ChainedSynchronousCalls.java -- OrderService calls InventoryService,
// which ITSELF synchronously calls WarehouseService -- a two-hop chain.
// Total latency is the SUM of both hops, demonstrating how synchronous
// chains compound.
public class ChainedSynchronousCalls {
    static class WarehouseService {
        int checkPhysicalCount(String sku) throws InterruptedException {
            Thread.sleep(150);
            return 5;
        }
    }

    static class InventoryService {
        WarehouseService warehouse = new WarehouseService();
        int checkStock(String sku) throws InterruptedException {
            Thread.sleep(100); // InventoryService's OWN processing time
            return warehouse.checkPhysicalCount(sku); // BLOCKS on the next hop too
        }
    }

    static class OrderService {
        InventoryService inventory = new InventoryService();
        void confirmOrder(String sku) throws InterruptedException {
            long start = System.currentTimeMillis();
            int stock = inventory.checkStock(sku);
            long elapsed = System.currentTimeMillis() - start;
            System.out.println("[Order] stock=" + stock + " after a 2-hop chain, total wait ~" + elapsed + "ms");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        new OrderService().confirmOrder("widget");
    }
}
```

**How to run:** `javac ChainedSynchronousCalls.java && java ChainedSynchronousCalls` (JDK 17+).

Expected output (elapsed time will vary slightly, always at least 250):
```
[Order] stock=5 after a 2-hop chain, total wait ~250ms
```

## 6. Walkthrough

1. **Level 1** — `OrderService.confirmOrder` prints a "requesting" line, then calls `inventory.checkStock(sku)`, which internally sleeps 200ms before returning `5`. Only after that sleep completes does execution return to `confirmOrder`, which then prints the "received" line. The 200ms gap between the two printed lines, even though invisible in the text output itself, is exactly the blocking cost the synchronous model imposes on the caller.
2. **Level 2 — making the cost visible** — `MeasuredLatency` wraps the same call with `System.currentTimeMillis()` calls before and after, computing `elapsed`. Running it prints a single line reporting that the caller was blocked for roughly 200ms — turning the implicit wait from Level 1 into an explicit, measured number.
3. **Level 3 — chaining hops** — `InventoryService.checkStock` no longer just sleeps and returns; it sleeps 100ms for its own processing, then synchronously calls `warehouse.checkPhysicalCount`, which sleeps another 150ms before returning. `OrderService.confirmOrder` still just calls `inventory.checkStock` once — from `OrderService`'s point of view, nothing about the *shape* of the call changed. But tracing execution: `confirmOrder` calls `checkStock`, which blocks for 100ms, then calls `checkPhysicalCount`, which blocks for another 150ms, and only then does a value flow back up through both return statements to `confirmOrder`.
4. **Reading the elapsed time** — the printed `elapsed` value comes out around 250ms (100 + 150), demonstrating concretely that `OrderService` paid the *sum* of both downstream services' processing times, even though it only made one call in its own code. If `WarehouseService` had, in turn, synchronously called a fourth service, that service's latency would add to the chain too — this is the compounding effect referred to in Section 2: a synchronous chain's total latency is at least the sum of every hop, and every hop is also a place a failure could occur and propagate back up.
5. **What the diagram in Part 4 maps to in code** — the sequence diagram's "blocked, waiting" bar on `OrderService`'s lifeline corresponds exactly to the interval between calling `inventory.checkStock(sku)` and that call returning in the Java code — the thread genuinely cannot do anything else for `OrderService` during that span, matching the diagram's visual.

## 7. Gotchas & takeaways

> **Gotcha:** a chain of synchronous calls, each individually fast, can still add up to unacceptable end-to-end latency once enough hops are involved — 5 services each averaging 100ms in a synchronous chain means at least 500ms total, even though no single service looks slow in isolation. Measure and budget latency for the whole chain, not just each hop.

- The synchronous model's calling code reads and behaves like an ordinary function call — its simplicity is exactly why it's usually the first pattern reached for.
- The caller is blocked for the full round trip; a slow or failing downstream service directly becomes the caller's own slowness or failure.
- Latency compounds across a chain of synchronous calls — the total is at least the sum of every hop's own latency.
- Use synchronous calls when the caller genuinely needs the answer before proceeding; otherwise, an asynchronous, event-driven approach avoids tying up the caller's thread for work it doesn't need to wait on.
- This model is what [RESTful APIs over HTTP](0076-restful-apis-over-http.md) implement concretely — the request/response shape described here is exactly what an HTTP GET or POST call embodies between two services.
