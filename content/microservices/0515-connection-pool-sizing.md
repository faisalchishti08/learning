---
card: microservices
gi: 515
slug: connection-pool-sizing
title: "Connection pool sizing"
---

## 1. What it is

**Connection pool sizing** is choosing how many reusable database (or other backend) connections a service instance keeps open and ready, rather than opening a brand-new connection for every single request. A pool that's too small forces requests to queue and wait for a connection to free up, adding latency under load; a pool that's too large can overwhelm the backend, or waste resources that would have been better spent elsewhere — and critically, when a service is horizontally scaled to many instances, each instance's own pool size multiplies across the whole fleet, meaning the backend's actual connection limit becomes a fleet-wide sizing constraint, not a per-instance one.

## 2. Why & when

You size connection pools deliberately, and revisit that sizing whenever the service's scale changes, because getting it wrong causes real, sometimes surprising problems in either direction:

- **Opening a new database connection per request is expensive** — the TCP handshake, authentication, and connection setup overhead is significant compared to just reusing an already-established connection, which is the entire reason connection pools exist in the first place.
- **A pool that's too small under real concurrent load means requests queue waiting for a free connection**, adding latency that has nothing to do with the actual query taking long — the bottleneck is purely pool contention, not the database itself.
- **A pool that's too large, especially multiplied across many horizontally-scaled instances, can exceed what the backend database can actually handle.** A database with a hard connection limit of 500 gets a very different outcome from 10 instances each configured for a pool of 20 (200 total, safely under the limit) versus 10 instances each configured for a pool of 100 (1000 total, wildly over the limit) — the *same* per-instance pool size decision produces wildly different fleet-wide outcomes depending purely on how many instances exist.
- **You size pools with the whole fleet's total connection count in mind, not just one instance in isolation** — and you revisit that sizing any time your horizontal scaling (the number of instances) changes meaningfully, since the safe per-instance number changes inversely with instance count.

## 3. Core concept

Think of a small business with a shared fleet of company cars: giving each of 5 employees their own dedicated car (a small pool per person) makes sense when there are only 5 employees and 20 available parking spots — but if the company grows to 50 employees, giving each one their own dedicated car the same way would need 50 spots, potentially far more than the lot actually has. The *total* number of cars needed to keep everyone reasonably unblocked has to account for how many employees there now are — sizing "per employee" without considering the total headcount is exactly the mistake connection pool sizing needs to avoid.

Concretely:

1. **A pool holds a fixed maximum number of open connections**, reused across requests — a request needing a connection borrows one from the pool, uses it, and returns it for the next request to reuse, rather than opening and closing a fresh connection each time.
2. **Pool size should reflect actual concurrent database usage need**, which is often much smaller than naive intuition suggests — a well-tuned pool of even a modest size can serve a surprisingly high request rate, since most queries complete quickly and connections are returned rapidly for reuse.
3. **Total fleet-wide connections = per-instance pool size × number of instances** — this is the number that actually matters against the database's connection limit, not any single instance's pool size viewed in isolation.
4. **Autoscaling interacts directly with this math** — if an autoscaler can scale a service from 5 to 50 instances under load, the pool size per instance needs to be chosen so that even the maximum expected instance count times the per-instance pool size stays safely under the database's actual connection limit.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Per-instance pool size multiplied by instance count gives total connections against the database, which must stay under its connection limit" >
  <rect x="20" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">pool size: 20 per instance</text>

  <rect x="240" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">x 10 instances = 200 total</text>

  <rect x="460" y="20" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="550" y="50" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">database limit: 500 -- SAFE</text>

  <line x1="200" y1="45" x2="240" y2="45" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="420" y1="45" x2="460" y2="45" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="330" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the SAME per-instance pool size at 30 instances would be 600 total -- OVER the limit</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Per-instance pool size times instance count is the number that matters against the database's actual connection limit.

## 5. Runnable example

Scenario: a fleet-aware connection pool sizing calculator. We start with a basic single-instance pool simulation showing reuse benefits, extend it to computing fleet-wide totals across multiple instances, then handle the hard case: an autoscaler scaling up under load, where the naive per-instance pool size that was safe at low instance counts becomes unsafe at high instance counts, requiring a dynamically-aware sizing decision.

### Level 1 — Basic

```java
// File: ConnectionPoolBasic.java -- models a BASIC connection pool:
// a FIXED number of reusable connections, borrowed and returned, rather
// than opening a fresh connection per request.
import java.util.concurrent.*;

public class ConnectionPoolBasic {
    static class ConnectionPool {
        Semaphore availableConnections;
        int poolSize;

        ConnectionPool(int poolSize) {
            this.poolSize = poolSize;
            this.availableConnections = new Semaphore(poolSize);
        }

        void handleRequest(String requestId) throws InterruptedException {
            availableConnections.acquire(); // borrow a connection, waiting if the pool is exhausted
            try {
                System.out.println("[pool] " + requestId + " borrowed a connection (available now: " + availableConnections.availablePermits() + "/" + poolSize + ")");
                Thread.sleep(10); // simulates a quick query
            } finally {
                availableConnections.release(); // return it for reuse
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ConnectionPool pool = new ConnectionPool(5);
        for (int i = 1; i <= 3; i++) {
            pool.handleRequest("request-" + i);
        }
    }
}
```

How to run: `java ConnectionPoolBasic.java`

`Semaphore(poolSize)` models the fixed-size pool — `acquire()` borrows a connection (blocking if none are available), and the `finally` block's `release()` guarantees the connection is always returned for reuse by a later request, even if the request handling itself were to throw an exception.

### Level 2 — Intermediate

```java
// File: FleetWideConnectionMath.java -- the SAME per-instance pool, now
// computing the FLEET-WIDE total across MULTIPLE instances, checked
// against the DATABASE's actual connection limit -- the number that
// actually matters.
public class FleetWideConnectionMath {
    static int databaseConnectionLimit = 500;

    static boolean isSafe(int perInstancePoolSize, int instanceCount) {
        int totalConnections = perInstancePoolSize * instanceCount;
        boolean safe = totalConnections <= databaseConnectionLimit;
        System.out.println("[fleet math] " + perInstancePoolSize + " per instance x " + instanceCount
                + " instances = " + totalConnections + " total -- " + (safe ? "SAFE" : "EXCEEDS LIMIT of " + databaseConnectionLimit));
        return safe;
    }

    public static void main(String[] args) {
        isSafe(20, 10);  // 200 total, well under 500
        isSafe(20, 30);  // 600 total -- SAME per-instance size, now unsafe at higher instance count
    }
}
```

How to run: `java FleetWideConnectionMath.java`

`isSafe` multiplies `perInstancePoolSize` by `instanceCount` to get the real number that matters — the *identical* `20`-per-instance pool size is perfectly safe at `10` instances (`200` total) but genuinely unsafe at `30` instances (`600` total, exceeding the `500` limit), demonstrating that a pool size decision can't be made correctly without knowing the actual or maximum expected instance count.

### Level 3 — Advanced

```java
// File: AutoscalingAwarePoolSizing.java -- the SAME fleet math, now
// handling the PRODUCTION-FLAVORED hard case: an AUTOSCALER scaling the
// fleet from a LOW instance count up to its CONFIGURED MAXIMUM under
// load. The per-instance pool size must be chosen so that even the
// autoscaler's MAXIMUM possible instance count stays SAFE -- not just
// whatever the CURRENT instance count happens to be.
public class AutoscalingAwarePoolSizing {
    static int databaseConnectionLimit = 500;
    static int autoscalerMaxInstances = 40; // the HIGHEST instance count the autoscaler could ever reach
    static double safetyMarginFraction = 0.8; // reserve some headroom, don't run right up to the hard limit

    static int computeSafePerInstancePoolSize() {
        int usableLimit = (int) (databaseConnectionLimit * safetyMarginFraction);
        int safePoolSize = usableLimit / autoscalerMaxInstances;
        System.out.println("[sizing] usable limit (with " + (int)(safetyMarginFraction * 100) + "% margin): " + usableLimit
                + ", divided across max " + autoscalerMaxInstances + " instances = " + safePoolSize + " per instance");
        return safePoolSize;
    }

    static boolean checkAtScale(int perInstancePoolSize, int currentInstanceCount) {
        int total = perInstancePoolSize * currentInstanceCount;
        boolean safe = total <= databaseConnectionLimit;
        System.out.println("[at scale] " + currentInstanceCount + " instances x " + perInstancePoolSize
                + " = " + total + " total -- " + (safe ? "safe" : "UNSAFE"));
        return safe;
    }

    public static void main(String[] args) {
        int safePoolSize = computeSafePerInstancePoolSize();

        System.out.println();
        System.out.println("--- verifying safety across the autoscaler's ENTIRE possible range ---");
        checkAtScale(safePoolSize, 5);   // low load, few instances
        checkAtScale(safePoolSize, 20);  // moderate load
        checkAtScale(safePoolSize, autoscalerMaxInstances); // PEAK load, the autoscaler's ceiling

        System.out.println();
        System.out.println("--- contrast: a NAIVELY chosen pool size, sized only for LOW instance counts ---");
        int naivePoolSize = 50; // "seemed fine" when tested with only a few instances
        checkAtScale(naivePoolSize, 5);   // looks fine at low scale...
        checkAtScale(naivePoolSize, autoscalerMaxInstances); // ...but catastrophically unsafe at peak autoscale
    }
}
```

How to run: `java AutoscalingAwarePoolSizing.java`

`computeSafePerInstancePoolSize` divides a safety-margined usable connection budget by `autoscalerMaxInstances` — the *maximum* the autoscaler could ever reach, not the current instance count — producing a per-instance pool size that stays safe across the *entire* autoscaling range. The contrast with `naivePoolSize` (chosen by testing only at low instance counts, where it "looked fine") makes the risk concrete: `checkAtScale(naivePoolSize, 5)` reports safe, but `checkAtScale(naivePoolSize, autoscalerMaxInstances)` reports genuinely unsafe, demonstrating exactly the trap of sizing a pool based on today's instance count rather than the autoscaler's actual ceiling.

## 6. Walkthrough

Trace `AutoscalingAwarePoolSizing.main` in order. **First**, `computeSafePerInstancePoolSize()` runs: `usableLimit` is computed as `500 * 0.8 = 400` (reserving a margin rather than running right up to the hard `500` limit), and `safePoolSize` is `400 / 40 = 10` — this `10`-per-instance figure is deliberately conservative enough to remain safe even if the autoscaler reaches its full `40`-instance ceiling.

**Next**, `checkAtScale(safePoolSize, 5)` computes `10 * 5 = 50` total connections, well under `500` — safe, as expected at low scale.

**Then**, `checkAtScale(safePoolSize, 20)` computes `10 * 20 = 200` — still comfortably safe at moderate scale.

**After that**, `checkAtScale(safePoolSize, autoscalerMaxInstances)` computes `10 * 40 = 400` — right at the intended usable limit, and still safely under the actual hard `500` connection limit, exactly as `computeSafePerInstancePoolSize` was designed to guarantee even at the autoscaler's absolute peak.

**Finally**, the contrast section runs `checkAtScale(naivePoolSize, 5)`, computing `50 * 5 = 250` — comfortably under `500`, which is exactly the kind of result that would make a `50`-per-instance pool size look perfectly reasonable if only tested at low instance counts. But `checkAtScale(naivePoolSize, autoscalerMaxInstances)` computes `50 * 40 = 2000` — wildly over the `500` hard limit, revealing that the naive sizing decision, which passed every test performed at low scale, would catastrophically overwhelm the database's actual connection limit the moment the autoscaler legitimately scaled up to handle real peak load.

```
[sizing] usable limit (with 80% margin): 400, divided across max 40 instances = 10 per instance

--- verifying safety across the autoscaler's ENTIRE possible range ---
[at scale] 5 instances x 10 = 50 total -- safe
[at scale] 20 instances x 10 = 200 total -- safe
[at scale] 40 instances x 10 = 400 total -- safe

--- contrast: a NAIVELY chosen pool size, sized only for LOW instance counts ---
[at scale] 5 instances x 50 = 250 total -- safe
[at scale] 40 instances x 50 = 2000 total -- UNSAFE
```

## 7. Gotchas & takeaways

> A connection pool size that "worked fine" during testing or in a low-traffic environment can be a ticking time bomb if that testing never exercised the fleet's actual maximum autoscaled instance count — the naive `50`-per-instance size above looked completely safe at 5 instances and only revealed its danger at the autoscaler's true ceiling, exactly the gap between "tested" and "production peak load" that causes real incidents.
- Always size per-instance connection pools against the *maximum* instance count your autoscaling configuration could ever reach, not the typical or current instance count — the whole point of an autoscaler is that instance count genuinely varies, often dramatically, under real load.
- Leave a safety margin below the database's hard connection limit (as the `safetyMarginFraction` does here) — other legitimate connections (admin tools, monitoring, batch jobs) also consume the database's connection budget, and running your service's pools right up against the absolute hard limit leaves no room for anything else.
- This constraint interacts directly with [horizontal vs vertical scaling](0512-horizontal-vs-vertical-scaling.md) decisions — a database connection limit is one of the concrete, practical ceilings that can make horizontal scaling of the application tier hit a real backend constraint, even though the application tier itself has no inherent scaling limit of its own.
- Consider a connection-pooling proxy (like PgBouncer for PostgreSQL) between your service fleet and the database for very large fleets — it can multiplex many application-level connections down to a smaller number of actual database connections, decoupling the fleet's instance count from the database's connection limit far more gracefully than per-instance pool math alone can achieve.
