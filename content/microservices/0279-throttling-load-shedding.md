---
card: microservices
gi: 279
slug: throttling-load-shedding
title: "Throttling & load shedding"
---

## 1. What it is

Throttling and load shedding are both responses to a service being asked to do more work than it can handle, but they act at different points and with different criteria. Throttling proactively slows or caps the *rate* of accepted work per caller (this is what rate limiters like [token bucket](0274-token-bucket-algorithm.md) do), usually applied per-client based on a configured quota. Load shedding is a reactive, whole-service decision: when the service's own health signals (queue depth, CPU, memory, latency) cross a danger threshold, it starts deliberately dropping or rejecting some requests — regardless of any individual client's quota — specifically to protect itself from falling over entirely.

## 2. Why & when

Throttling protects fairness and predictability: it stops any single client from monopolizing capacity or exceeding its agreed usage tier, and it kicks in based on *that client's* behavior, independent of whether the service overall is under stress. It is a per-caller contract.

Load shedding protects the service's own survival: even with perfect per-client throttling, aggregate legitimate traffic from *many* well-behaved clients can still exceed total capacity (e.g., a traffic spike, a downstream dependency slowing everyone down, a partial outage reducing available instances). Load shedding is the last line of defense — deliberately failing *some* requests fast, cheaply, and predictably (an immediate 503) so the service can keep serving the rest, rather than accepting everything, becoming overloaded, and failing unpredictably for *all* requests including in-flight ones.

Use throttling as the standing, per-client policy always in effect. Use load shedding as the emergency valve that engages only when the service's own health signals say it is in danger, typically shedding lower-priority traffic first (e.g., background jobs before user-facing requests) if priority information is available.

## 3. Core concept

Throttling checks a per-client budget before doing work. Load shedding checks a global health signal (often queue length or latency) before doing work, independent of which client is asking, and often applies differently by request priority.

```java
class LoadShedder {
    final int maxQueueDepth;
    final java.util.concurrent.atomic.AtomicInteger currentQueueDepth = new java.util.concurrent.atomic.AtomicInteger(0);

    boolean shouldShed(String priority) {
        int depth = currentQueueDepth.get();
        if ("low".equals(priority)) return depth > maxQueueDepth * 0.5;  // shed LOW priority EARLY
        return depth > maxQueueDepth;                                    // shed HIGH priority only when FULL
    }
    LoadShedder(int maxQueueDepth) { this.maxQueueDepth = maxQueueDepth; }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Throttling checks each individual client's own quota independent of overall system health; load shedding checks the service's own overall health signal and rejects some requests, often lower priority ones first, once that signal crosses a danger threshold, regardless of which client is asking">
  <text x="150" y="20" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Throttling (per-client quota)</text>
  <rect x="30" y="30" width="80" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="70" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Client A: 8/10</text>
  <rect x="120" y="30" width="80" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="160" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Client B: 11/10</text>
  <text x="160" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">only B is throttled</text>

  <text x="470" y="20" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Load shedding (whole-service health)</text>
  <rect x="380" y="30" width="180" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="49" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">queue depth: 95% FULL &#8594; DANGER</text>
  <text x="470" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">low-priority requests shed FIRST, from ALL clients</text>

  <line x1="220" y1="100" x2="420" y2="100" stroke="#8b949e" stroke-dasharray="2,2"/>
  <text x="320" y="115" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">independent mechanisms, often used together</text>
</svg>

Throttling is per-client and quota-based; load shedding is whole-service and health-based, often priority-aware.

## 5. Runnable example

Scenario: a service that throttles individual over-quota clients while still overloading overall because many well-behaved clients combine to exceed capacity, extended to add load shedding based on queue depth, and finally shedding low-priority work first to protect high-priority traffic under sustained overload.

### Level 1 — Basic

```java
// File: ThrottlingAloneIsNotEnough.java -- every client individually
// stays under its per-client quota, yet the SERVICE as a whole is still
// overloaded because there are many well-behaved clients.
import java.util.*;

public class ThrottlingAloneIsNotEnough {
    static class PerClientThrottle {
        final Map<String, Integer> counts = new HashMap<>();
        final int perClientLimit = 10;
        boolean allow(String clientId) {
            int c = counts.getOrDefault(clientId, 0);
            if (c < perClientLimit) { counts.put(clientId, c + 1); return true; }
            return false;
        }
    }

    public static void main(String[] args) {
        PerClientThrottle throttle = new PerClientThrottle();
        int totalAccepted = 0;
        // 50 DIFFERENT clients, each sending exactly its allowed 10 requests.
        for (int client = 1; client <= 50; client++) {
            for (int req = 1; req <= 10; req++) {
                if (throttle.allow("client-" + client)) totalAccepted++;
            }
        }
        System.out.println("Every individual client stayed within its quota of 10.");
        System.out.println("But total accepted work across the service: " + totalAccepted
                + " (service capacity is only ~200 -- this is 2.5x overloaded)");
    }
}
```

How to run: `java ThrottlingAloneIsNotEnough.java`

Fifty clients each send exactly 10 requests — their individually allowed quota — so per-client throttling never rejects a single one of them. But the total work accepted is 500, well beyond a hypothetical service capacity of 200. This demonstrates why throttling alone cannot protect the service itself: it is a fairness mechanism between clients, not a capacity mechanism for the service as a whole.

### Level 2 — Intermediate

```java
// File: AddLoadShedding.java -- same throttled clients, but now the
// service also tracks its own queue depth and sheds (rejects) requests
// once that depth crosses a danger threshold, independent of any
// individual client's quota status.
import java.util.*;

public class AddLoadShedding {
    static class PerClientThrottle {
        final Map<String, Integer> counts = new HashMap<>();
        final int perClientLimit = 10;
        boolean allow(String clientId) {
            int c = counts.getOrDefault(clientId, 0);
            if (c < perClientLimit) { counts.put(clientId, c + 1); return true; }
            return false;
        }
    }

    static class LoadShedder {
        int currentQueueDepth = 0;
        final int capacity = 200;
        boolean shouldShed() { return currentQueueDepth >= capacity; }
        void enqueue() { currentQueueDepth++; }
        void complete() { currentQueueDepth = Math.max(0, currentQueueDepth - 1); } // work finishes, frees capacity
    }

    public static void main(String[] args) {
        PerClientThrottle throttle = new PerClientThrottle();
        LoadShedder shedder = new LoadShedder();
        int accepted = 0, throttled = 0, shed = 0;

        for (int client = 1; client <= 50; client++) {
            for (int req = 1; req <= 10; req++) {
                String clientId = "client-" + client;
                if (!throttle.allow(clientId)) { throttled++; continue; }
                if (shedder.shouldShed()) { shed++; continue; } // service protects ITSELF here
                shedder.enqueue();
                accepted++;
            }
        }
        System.out.println("Throttled (individual over-quota): " + throttled);
        System.out.println("Shed (service self-protection once full): " + shed);
        System.out.println("Accepted: " + accepted + " (capped at service capacity, not client count)");
    }
}
```

How to run: `java AddLoadShedding.java`

Same 50 well-behaved clients, each within their individual quota (so `throttled` stays 0), but now a `LoadShedder` tracks the service's own queue depth against a capacity of 200. Once 200 requests have been accepted, every subsequent request — no matter which client, no matter that the client is still under its own quota — is shed. The accepted total now caps at exactly 200, protecting the service, while `shed` accounts for the remaining 300 requests that were within their per-client quota but still had to be rejected for the service's own survival.

### Level 3 — Advanced

```java
// File: PriorityAwareLoadShedding.java -- under sustained overload, shed
// LOW-priority requests first (e.g., background sync jobs) while still
// serving HIGH-priority requests (e.g., user-facing checkout) as long as
// there is any capacity left, instead of shedding indiscriminately.
import java.util.*;

public class PriorityAwareLoadShedding {
    enum Priority { HIGH, LOW }

    static class PriorityAwareShedder {
        int currentQueueDepth = 0;
        final int capacity = 200;
        final double lowPriorityShedThreshold = 0.5; // shed LOW priority once 50% full

        boolean shouldShed(Priority priority) {
            double utilization = (double) currentQueueDepth / capacity;
            if (priority == Priority.LOW) return utilization >= lowPriorityShedThreshold;
            return utilization >= 1.0; // HIGH priority sheds only once truly full
        }
        void enqueue() { currentQueueDepth++; }
    }

    public static void main(String[] args) {
        PriorityAwareShedder shedder = new PriorityAwareShedder();
        Random random = new Random(42);
        int highAccepted = 0, highShed = 0, lowAccepted = 0, lowShed = 0;

        // 400 requests total, 30% HIGH priority (checkout-like), 70% LOW priority (background jobs).
        for (int i = 0; i < 400; i++) {
            Priority p = random.nextDouble() < 0.3 ? Priority.HIGH : Priority.LOW;
            if (shedder.shouldShed(p)) {
                if (p == Priority.HIGH) highShed++; else lowShed++;
                continue;
            }
            shedder.enqueue();
            if (p == Priority.HIGH) highAccepted++; else lowAccepted++;
        }

        System.out.println("HIGH priority: accepted=" + highAccepted + " shed=" + highShed);
        System.out.println("LOW  priority: accepted=" + lowAccepted + " shed=" + lowShed);
        System.out.printf("HIGH priority success rate: %.0f%%  LOW priority success rate: %.0f%%%n",
                100.0 * highAccepted / (highAccepted + highShed),
                100.0 * lowAccepted / (lowAccepted + lowShed));
    }
}
```

How to run: `java PriorityAwareLoadShedding.java`

Four hundred requests arrive, roughly 30% high-priority and 70% low-priority, all against a service with capacity 200. Because `shouldShed` uses a lower utilization threshold (50%) for low-priority requests but only sheds high-priority requests once the queue is completely full, low-priority traffic starts getting rejected early while capacity is preserved for high-priority traffic. The printed success rates show high-priority requests succeeding at a much higher rate than low-priority ones — exactly the intended outcome: under overload, the service degrades gracefully by sacrificing less-important work first rather than treating all 400 requests identically and failing them proportionally.

## 6. Walkthrough

Trace `PriorityAwareLoadShedding.main` in order. **First**, a `PriorityAwareShedder` is created with `capacity=200` and a `lowPriorityShedThreshold=0.5`, and `currentQueueDepth` starts at 0.

**For each of the 400 requests**, a priority is assigned randomly (30% HIGH, 70% LOW), simulating a realistic mixed workload — think user checkout calls (HIGH) interleaved with background inventory sync calls (LOW).

**Each request then calls `shouldShed(priority)`.** Inside, `utilization` is computed as `currentQueueDepth / capacity`. For a LOW-priority request, the check is `utilization >= 0.5` — so once the queue is half full, every subsequent LOW request is shed immediately, before any enqueue happens. For a HIGH-priority request, the check is `utilization >= 1.0` — HIGH requests keep flowing until the queue is completely full.

**Early in the run** (queue depth low), both priorities are accepted and `enqueue()` increments `currentQueueDepth`, so utilization climbs steadily as more requests are processed.

**Once utilization crosses 50%** (roughly the 100th accepted request, since capacity is 200), the branch for LOW-priority requests starts returning `true` from `shouldShed`, and those calls now hit the `continue` in the `if (shedder.shouldShed(p))` block — incrementing `lowShed` and never reaching `enqueue()`. HIGH-priority requests keep sailing through this same check because their threshold is 1.0, not 0.5.

**As the run continues** past that point, only HIGH-priority requests continue to be enqueued, so `currentQueueDepth` keeps climbing but now almost entirely from HIGH-priority traffic, until it too eventually approaches capacity (200) and even HIGH-priority requests start being shed.

**At the end**, the program computes each priority's success rate by dividing accepted by (accepted + shed). Because LOW-priority requests started being shed at 50% utilization while HIGH-priority requests kept flowing until 100%, HIGH priority's success rate is substantially higher than LOW's — the deliberate, designed outcome of priority-aware load shedding.

```
request arrives -> priority assigned -> shouldShed(priority)?
                                            |
                    LOW: shed once queue >= 50% full
                    HIGH: shed only once queue >= 100% full
                                            |
                                  accepted -> enqueue() -> queue depth++
```

## 7. Gotchas & takeaways

> Throttling every individual client fairly does not guarantee the service survives — many well-behaved clients, each within quota, can still sum to more load than the service can handle. Load shedding is what actually protects the service itself.

- Throttling is a per-client fairness/quota mechanism; load shedding is a whole-service self-protection mechanism — they answer different questions and both are usually needed.
- Load shedding should reject fast and cheap (an immediate `503 Service Unavailable`), not after doing partial, wasted work — the whole point is to avoid spending scarce resources on requests that won't be served anyway.
- Priority-aware shedding (shedding low-value traffic first) produces much better outcomes under overload than shedding indiscriminately, but it requires the system to actually carry and trust priority information on each request.
- Load shedding thresholds should be based on real health signals (queue depth, latency, resource saturation), not just a static request count, so the service adapts to its actual current capacity rather than an assumed fixed one.
