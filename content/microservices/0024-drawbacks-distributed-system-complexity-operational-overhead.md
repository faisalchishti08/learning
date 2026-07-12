---
card: microservices
gi: 24
slug: drawbacks-distributed-system-complexity-operational-overhead
title: "Drawbacks: distributed-system complexity, operational overhead"
---

## 1. What it is

Microservices trade a monolith's simplicity for two categories of real, ongoing cost. **Distributed-system complexity** covers everything that becomes hard the moment logic crosses a network boundary instead of staying in-process: calls can fail partially, latency is added to every hop, and keeping data consistent across services requires deliberate design instead of one database transaction. **Operational overhead** covers the sheer number of moving parts a microservices system introduces: many more processes to deploy, monitor, log, alert on, and keep available than a single monolith would ever require, each one a genuine, ongoing maintenance burden.

These aren't hypothetical or avoidable through better tooling alone — they are the direct, structural cost of the same properties (independent processes, independent data, independent deploys) that produce microservices' benefits.

## 2. Why & when

Knowing these drawbacks precisely matters because they're what should be weighed, honestly, against the four benefits in the previous tutorial before choosing microservices at all. A team of five engineers running a system with modest, uniform traffic will likely find that ten independently deployed services multiply their operational burden (ten things to monitor, ten deploy pipelines to maintain, ten sets of logs to correlate) far more than they multiply any genuine benefit — the same five engineers might ship faster and more reliably with a well-structured monolith.

Weigh these costs explicitly, service by service, not just once at the system level: is *this specific* split's added latency, added failure mode, and added operational surface actually justified by *this specific* boundary's independent-deployability or scalability need? A system doesn't need to be "all microservices" or "all monolith" — most real systems benefit from splitting only where the tradeoff clearly favors it.

## 3. Core concept

Concrete manifestations of each category:

- **Distributed-system complexity:** a call that used to be a guaranteed, instant, all-or-nothing method call can now fail partway through, time out, or succeed on the far side while the caller never receives confirmation — situations a monolith's in-process calls structurally cannot produce.
- **Operational overhead:** N services means N deploy pipelines, N sets of logs to search across for one user-facing request, N health checks to monitor, and N opportunities for any one of them to be the thing that's down at 3 a.m.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A monolith has one process to monitor and one guaranteed in-process call; microservices multiply both the number of processes to operate and the ways a single call can fail">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Monolith</text>
  <rect x="60" y="35" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">1 process to operate</text>
  <text x="150" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">in-process call: always completes</text>

  <text x="480" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Microservices</text>
  <rect x="360" y="35" width="240" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="480" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">N processes to operate</text>
  <text x="480" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">network call: can time out, fail partially</text>
</svg>

Splitting one process into many multiplies both the operational surface and the ways a single call can go wrong.

## 5. Runnable example

Scenario: a checkout operation, first as a guaranteed in-process call, then split across a network with a genuinely new partial-failure mode, then with the operational overhead of correlating logs across services made explicit.

### Level 1 — Basic

```java
// File: MonolithGuaranteedCall.java -- an in-process call ALWAYS completes atomically
public class MonolithGuaranteedCall {
    static boolean inventoryReserved = false;
    static boolean paymentCharged = false;

    static void checkout() {
        inventoryReserved = true; // in-process -- either this whole method completes, or an exception unwinds it all
        paymentCharged = true;
        System.out.println("checkout complete -- reserved=" + inventoryReserved + ", charged=" + paymentCharged);
    }

    public static void main(String[] args) {
        checkout();
    }
}
```

**How to run:** `javac MonolithGuaranteedCall.java && java MonolithGuaranteedCall` (JDK 17+).

Expected output:
```
checkout complete -- reserved=true, charged=true
```

Both steps happen as guaranteed, sequential, in-process operations. There's no possibility of "inventory was reserved but we never found out whether payment succeeded" — that state simply cannot occur within one process's normal control flow.

### Level 2 — Intermediate

```java
// File: DistributedPartialFailure.java -- the SAME operation, over a network,
// can now land in a state a monolith could never produce: PARTIAL success.
public class DistributedPartialFailure {
    static boolean callInventoryService() { return true; } // succeeds

    static boolean callPaymentService() {
        throw new RuntimeException("payment service timed out"); // the RESPONSE is lost, but the charge may have ALREADY happened server-side
    }

    static void checkout() {
        boolean reserved = callInventoryService();
        System.out.println("inventory reserved: " + reserved);
        try {
            boolean charged = callPaymentService();
            System.out.println("payment charged: " + charged);
        } catch (RuntimeException e) {
            // THE HARD PART: we genuinely don't know if the charge happened or not --
            // a timeout means "no response," not "no effect." A monolith's method call has no equivalent ambiguity.
            System.out.println("payment call failed: " + e.getMessage() + " -- UNKNOWN whether the customer was actually charged");
        }
    }

    public static void main(String[] args) {
        checkout();
    }
}
```

**How to run:** `javac DistributedPartialFailure.java && java DistributedPartialFailure` (JDK 17+).

Expected output:
```
inventory reserved: true
payment call failed: payment service timed out -- UNKNOWN whether the customer was actually charged
```

This is distributed-system complexity in its sharpest form: `inventory reserved: true` is certain, but the payment outcome is genuinely ambiguous — the timeout means the caller never received a response, not that nothing happened on the payment service's side. A monolith's in-process call from Level 1 has no equivalent state; either the whole method completed or it threw before completing anything.

### Level 3 — Advanced

```java
// File: OperationalOverhead.java -- ONE user-facing request now requires
// correlating logs across MULTIPLE separate services to diagnose an issue.
import java.util.*;

public class OperationalOverhead {
    static List<String> ordersServiceLogs = new ArrayList<>();
    static List<String> inventoryServiceLogs = new ArrayList<>();
    static List<String> paymentServiceLogs = new ArrayList<>();

    static void checkout(String requestId) {
        // each service logs INDEPENDENTLY, into its OWN log stream -- a genuine operational cost
        ordersServiceLogs.add("[" + requestId + "] received checkout request");
        inventoryServiceLogs.add("[" + requestId + "] reserved 1x widget");
        paymentServiceLogs.add("[" + requestId + "] charge FAILED: card declined");
        ordersServiceLogs.add("[" + requestId + "] checkout FAILED (payment declined)");
    }

    // diagnosing ONE request now means searching THREE separate log streams and correlating by requestId
    static List<String> diagnose(String requestId) {
        List<String> combined = new ArrayList<>();
        for (String log : ordersServiceLogs) if (log.startsWith("[" + requestId + "]")) combined.add("[orders] " + log);
        for (String log : inventoryServiceLogs) if (log.startsWith("[" + requestId + "]")) combined.add("[inventory] " + log);
        for (String log : paymentServiceLogs) if (log.startsWith("[" + requestId + "]")) combined.add("[payment] " + log);
        return combined;
    }

    public static void main(String[] args) {
        checkout("req-42");
        System.out.println("A support engineer investigating req-42 must correlate logs from " + 3 + " separate services:");
        for (String line : diagnose("req-42")) System.out.println("  " + line);
    }
}
```

**How to run:** `javac OperationalOverhead.java && java OperationalOverhead` (JDK 17+).

Expected output:
```
A support engineer investigating req-42 must correlate logs from 3 separate services:
  [orders] [req-42] received checkout request
  [orders] [req-42] checkout FAILED (payment declined)
  [inventory] [req-42] reserved 1x widget
  [payment] [req-42] charge FAILED: card declined
```

The production-flavored cost: understanding what happened to one user's request means searching across three separate log streams and manually correlating them by `requestId` — a task a monolith's single log stream would never require. Notice the merged output isn't even in chronological order (both `orders` lines appear together, even though the `payment` failure that caused the second one happened in between) — `diagnose` merges service-by-service, not by real timestamp, which is exactly why real distributed tracing tools sort by timestamp and span relationships instead. This kind of infrastructure (log aggregation, distributed tracing) is exactly what a real microservices system must invest in operationally, on top of the business logic itself.

## 6. Walkthrough

1. `checkout("req-42")` runs, and each line appends a log entry to a *different* list — `ordersServiceLogs`, `inventoryServiceLogs`, or `paymentServiceLogs` — each one standing in for a separate service's own, independently managed log output in a real deployment.
2. No single list contains the full story of what happened to `req-42` — `ordersServiceLogs` alone shows only that the request was received and that checkout ultimately failed, without showing *why* (the payment decline reason lives only in `paymentServiceLogs`).
3. `diagnose("req-42")` is called to answer "what actually happened to this request." It loops over all three lists separately, filtering each for lines tagged with `req-42`, and merges the results, prefixing each with which service it came from.
4. The final printed output reconstructs the full picture — request received, inventory reserved, payment declined, checkout ultimately failed — but only because `diagnose` did the cross-service correlation work explicitly. In a monolith, this entire sequence would appear as consecutive lines in one single log file, needing no correlation logic at all.
5. This function is a simplified stand-in for real infrastructure microservices systems need to invest in — centralized log aggregation and distributed tracing (propagating a shared request ID, exactly like `requestId` here, across every service a request touches) — which is itself a genuine, ongoing piece of operational overhead a monolith never needs.

```
Monolith:        ONE log stream, chronological, no correlation needed

Microservices:   ordersServiceLogs:     [req-42] received, [req-42] FAILED
                  inventoryServiceLogs:  [req-42] reserved
                  paymentServiceLogs:    [req-42] charge FAILED
                        |
                  diagnose(req-42) -- manual/automated correlation REQUIRED to see the full picture
```

## 7. Gotchas & takeaways

> **Gotcha:** distributed-system complexity doesn't announce itself loudly during development or in a demo — `DistributedPartialFailure`'s ambiguous payment state, and the log-correlation burden in `OperationalOverhead`, both tend to surface only under real production conditions (genuine network instability, genuine concurrent load, genuine on-call incidents at 3 a.m.) — meaning these costs are easy to underestimate until a system has been running in production for a while.

- Distributed-system complexity means calls that were once guaranteed, atomic, in-process operations can now fail partially, time out ambiguously, or leave the system in a state a monolith could never produce.
- Operational overhead means every additional independently deployed service adds its own deploy pipeline, its own logs, its own health checks, and its own way of being the thing that's broken — multiplying, not just adding to, the system's total operational surface.
- Weigh these costs against the [benefits](0023-benefits-scalability-agility-fault-isolation-tech-diversity.md) explicitly, per service boundary — a split that doesn't clearly justify its added complexity and overhead against a concrete benefit likely isn't worth making yet.
- Investing in infrastructure to manage these costs — centralized logging, distributed tracing, [design for failure](0011-design-for-failure.md) patterns like timeouts and circuit breakers — is not optional polish on top of microservices; it's a required, ongoing part of operating them safely.
