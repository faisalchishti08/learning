---
card: microservices
gi: 525
slug: lack-of-observability
title: "Lack of observability"
---

## 1. What it is

**Lack of observability** is the anti-pattern where a distributed system is deployed without the logging, metrics, and distributed tracing needed to understand what's actually happening inside it — especially across service boundaries. In a monolith, a debugger and a single log file can often answer "why did this fail"; in a microservices system, one logical request might touch a dozen services, and without correlated logs, metrics, and traces tying those dozen services' activity back to that one request, the honest answer to "why did this fail" becomes "we don't know," even though every individual service's own logs look fine in isolation.

## 2. Why & when

You invest in observability deliberately, and treat it as a first-class requirement rather than an afterthought, because distributed systems fail in ways that are invisible without it:

- **A failure in a distributed system is often not localized to one service.** A slow response might originate in a downstream dependency three hops away; a wrong result might stem from a stale cache in a service the caller doesn't even know exists. Without a way to trace one request's path across service boundaries, diagnosing this requires guesswork or, worse, painstakingly cross-referencing separate logs by timestamp and hoping they line up.
- **Individual service logs, viewed separately, tell you almost nothing about cross-service problems.** Service A's log shows "request received, response sent, 200 OK" — perfectly healthy from A's own perspective — while the actual problem was that A's response was wrong because of bad data three services upstream. No single service's logs reveal that; only a correlated view across all of them does.
- **The three foundational pillars are logs, metrics, and traces, and each answers a different question**: logs answer "what exactly happened at this point in time," metrics answer "how is the system behaving in aggregate, over time" (error rates, latency percentiles, throughput), and traces answer "what path did this one request take, and where did the time or the failure actually happen along that path."
- **Retrofitting observability after an incident is far more expensive than building it in from the start** — during an actual outage is the worst possible time to discover you have no way to see what's happening, and "we'll add tracing later, once we need it" usually means adding it in a panic, mid-incident, when it's too late to help with the incident already happening.

## 3. Core concept

Think of a package shipped through three different couriers before reaching its destination — the first courier's paperwork says "picked up, handed off," the second's says "received, handed off," the third's says "received, delivered late." Each courier's own records look complete and correct in isolation; none of them alone explains *why* the whole journey took three extra days. A single tracking number that follows the package through all three couriers' systems — a correlation ID — is the only thing that lets you reconstruct the actual end-to-end journey and pinpoint exactly which handoff caused the delay, rather than three separate, locally-correct-looking stories that don't add up to an answer.

Concretely:

1. **A correlation ID (or trace ID) is generated at the start of a request** and propagated through every downstream call the request triggers — every service that touches this request includes that same ID in its logs, letting anyone later reconstruct the request's full path across every service it touched.
2. **Structured logs** (not just free-text strings) let the correlation ID, and other key fields (service name, duration, outcome), be reliably searched and joined across services, instead of relying on fragile text-matching or manual timestamp correlation.
3. **Metrics aggregate behavior over time and across many requests** — error rate, request rate, latency percentiles per service — surfacing systemic problems (a slow creeping degradation, an error rate climbing) that would be invisible looking at any single request's logs alone.
4. **Distributed tracing stitches together the individual "spans"** (one span per service hop) that share a trace ID into a single timeline, showing exactly how long each hop took and where a failure actually originated, turning "we think it might be Service D" into "the trace shows Service D took 2.8 of the request's 3.0 total seconds."

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without a shared correlation ID, each service's logs look fine in isolation; with a correlation ID propagated through every hop, a single trace reconstructs the whole request across all services">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">No correlation</text>
  <rect x="20" y="35" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">A: OK, 200</text>
  <rect x="120" y="35" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">B: OK, 200</text>
  <rect x="220" y="35" width="80" height="30" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="260" y="54" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">C: slow, 200</text>
  <text x="160" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">three separate logs, no shared ID -- nobody sees the whole story</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Correlated trace</text>
  <rect x="380" y="35" width="260" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="53" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">trace-id=abc123, span A: 50ms</text>
  <rect x="380" y="65" width="260" height="26" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="510" y="83" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">trace-id=abc123, span B: 40ms</text>
  <rect x="380" y="95" width="260" height="26" rx="4" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="510" y="113" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">trace-id=abc123, span C: 2800ms -- HERE</text>
  <text x="510" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one trace ID reconstructs the whole path, pinpoints C</text>
</svg>

A shared correlation ID propagated through every hop turns isolated, locally-fine-looking logs into one reconstructable end-to-end story.

## 5. Runnable example

Scenario: a request flowing through three services (Gateway, Inventory, Pricing) where Pricing is unexpectedly slow. We start with uncorrelated logging that hides the problem, extend it to structured logs with a shared correlation ID, then handle the hard case: assembling those correlated logs into a simple trace that pinpoints exactly where the time went.

### Level 1 — Basic

```java
// File: UncorrelatedLogging.java -- each service logs INDEPENDENTLY,
// with no shared identifier tying their log lines to the same request.
public class UncorrelatedLogging {
    static void gatewayHandle() throws InterruptedException {
        System.out.println("[Gateway] request received");
        inventoryCheck();
        System.out.println("[Gateway] request completed, 200 OK");
    }
    static void inventoryCheck() throws InterruptedException {
        System.out.println("[Inventory] checking stock");
        Thread.sleep(40);
        pricingLookup();
        System.out.println("[Inventory] stock check done");
    }
    static void pricingLookup() throws InterruptedException {
        System.out.println("[Pricing] looking up price");
        Thread.sleep(2800); // Pricing is unexpectedly slow today
        System.out.println("[Pricing] price found");
    }

    public static void main(String[] args) throws InterruptedException {
        gatewayHandle();
        System.out.println("Problem: with concurrent traffic, these log lines interleave with OTHER requests' lines -- no way to tell which lines belong together.");
    }
}
```

How to run: `java UncorrelatedLogging.java`

Each service prints plain, unstructured log lines with no shared identifier. In isolation, running one request at a time, this looks readable — but under real concurrent traffic, Gateway, Inventory, and Pricing are each handling many requests simultaneously, and their log lines interleave in the actual log stream with no way to tell which "checking stock" line belongs to which "request received" line.

### Level 2 — Intermediate

```java
// File: CorrelatedStructuredLogging.java -- adds a CORRELATION ID,
// generated once at the entry point and PROPAGATED through every call,
// plus STRUCTURED fields instead of free-text log lines.
import java.util.*;

public class CorrelatedStructuredLogging {
    record LogEntry(String traceId, String service, String message, long timestampMs) {
        public String toString() { return "trace=" + traceId + " service=" + service + " ts=" + timestampMs + " msg=\"" + message + "\""; }
    }

    static void log(String traceId, String service, String message) {
        System.out.println(new LogEntry(traceId, service, message, System.currentTimeMillis()));
    }

    static void gatewayHandle(String traceId) throws InterruptedException {
        log(traceId, "Gateway", "request received");
        inventoryCheck(traceId); // traceId is PASSED DOWN through every call
        log(traceId, "Gateway", "request completed, 200 OK");
    }
    static void inventoryCheck(String traceId) throws InterruptedException {
        log(traceId, "Inventory", "checking stock");
        Thread.sleep(40);
        pricingLookup(traceId);
        log(traceId, "Inventory", "stock check done");
    }
    static void pricingLookup(String traceId) throws InterruptedException {
        log(traceId, "Pricing", "looking up price");
        Thread.sleep(2800);
        log(traceId, "Pricing", "price found");
    }

    public static void main(String[] args) throws InterruptedException {
        String traceId = UUID.randomUUID().toString().substring(0, 8); // generated ONCE, at the entry point
        gatewayHandle(traceId);
        System.out.println("Fix: every line above shares trace=" + traceId + " -- filterable/joinable across ALL three services, even under concurrent traffic.");
    }
}
```

How to run: `java CorrelatedStructuredLogging.java`

`traceId` is generated exactly once, at `main`, and threaded through every subsequent call as an explicit parameter, appearing in every log line via the structured `LogEntry`. Now, even with many concurrent requests interleaving in the real log stream, filtering for one `trace=` value reconstructs exactly this request's path across all three services — something the free-text version in Level 1 had no way to do.

### Level 3 — Advanced

```java
// File: AssembledTrace.java -- assembles the correlated log entries
// into a proper TRACE: a timeline of spans (one per service hop) with
// durations, making it possible to see EXACTLY where time was spent.
import java.util.*;

public class AssembledTrace {
    record Span(String traceId, String service, long startMs, long endMs) {
        long durationMs() { return endMs - startMs; }
    }

    static List<Span> spans = new ArrayList<>();

    static void gatewayHandle(String traceId) throws InterruptedException {
        long start = System.currentTimeMillis();
        inventoryCheck(traceId);
        spans.add(new Span(traceId, "Gateway", start, System.currentTimeMillis()));
    }
    static void inventoryCheck(String traceId) throws InterruptedException {
        long start = System.currentTimeMillis();
        Thread.sleep(40);
        pricingLookup(traceId);
        spans.add(new Span(traceId, "Inventory", start, System.currentTimeMillis()));
    }
    static void pricingLookup(String traceId) throws InterruptedException {
        long start = System.currentTimeMillis();
        Thread.sleep(2800);
        spans.add(new Span(traceId, "Pricing", start, System.currentTimeMillis()));
    }

    public static void main(String[] args) throws InterruptedException {
        String traceId = "abc123";
        gatewayHandle(traceId);

        spans.sort(Comparator.comparingLong(Span::startMs));
        long totalMs = spans.stream().mapToLong(Span::durationMs).max().getAsLong(); // Gateway's span spans the whole request
        System.out.println("--- Trace " + traceId + " (total ~" + totalMs + "ms) ---");
        for (Span s : spans) {
            double pct = 100.0 * s.durationMs() / totalMs;
            System.out.printf("  %-10s %5dms (%.0f%% of total)%s%n", s.service(), s.durationMs(), pct, pct > 50 ? "  <-- BOTTLENECK" : "");
        }
    }
}
```

How to run: `java AssembledTrace.java`

Each service records its own `Span` (start time, end time), all tagged with the same `traceId` and collected into one list — exactly what a real tracing system (Zipkin, Jaeger, OpenTelemetry) does automatically across service boundaries. Sorting and printing the spans together produces a clear breakdown of where the request's ~2.8+ seconds actually went, flagging Pricing as the bottleneck by percentage of total time — a conclusion that was completely invisible from Level 1's disconnected log lines, and only reachable in Level 2 by manually cross-referencing timestamps.

## 6. Walkthrough

Trace `AssembledTrace.main` end to end:

1. **`gatewayHandle("abc123")` records `start` and calls `inventoryCheck("abc123")`.**
2. **`inventoryCheck` records its own `start`, sleeps 40ms, then calls `pricingLookup("abc123")`** before recording its own span — note the recording happens *after* the nested call returns, so `Inventory`'s span duration includes all of Pricing's time nested inside it (mirroring how a real parent span includes its children's time).
3. **`pricingLookup` records `start`, sleeps 2800ms, then adds its own `Span("Pricing", start, now)`** to the shared `spans` list — this is the innermost, and slowest, hop.
4. **Control returns to `inventoryCheck`, which now adds its own `Span("Inventory", ...)`** — its recorded duration is roughly 40 + 2800 = 2840ms, since it includes the nested Pricing call's time.
5. **Control returns to `gatewayHandle`, which adds its own `Span("Gateway", ...)`** — its duration is the full end-to-end request time, roughly 2840ms, encompassing everything nested beneath it.
6. **`main` sorts the spans by start time and computes `totalMs`** as the largest single duration (Gateway's, since it spans the whole request), then prints each span with its percentage of that total.
7. **The printed trace shows Pricing consuming roughly 98% of total request time**, flagged explicitly as the bottleneck — directly answering "where did the time go" in a way that reading three separate services' logs, even with a shared trace ID but no assembled timeline, would still require manual arithmetic to figure out.

This mirrors exactly what a distributed tracing system does in production: each service emits spans tagged with a shared trace ID, a collector assembles them into one timeline, and a trace viewer (like Jaeger's waterfall view) renders precisely this kind of "which hop took how long" breakdown — turning "the request was slow somewhere" into "Pricing's span was 2800ms out of 2840ms total."

## 7. Gotchas & takeaways

> **Gotcha:** adding logging to every service without a shared correlation ID gives a false sense of having observability — plenty of log volume exists, but none of it can be tied together across service boundaries, so during an actual incident, someone still has to manually guess which log lines from which services belong to the same failing request, exactly the problem observability was supposed to solve.

- A correlation/trace ID must be generated once at the request's entry point and explicitly propagated through every downstream call — it doesn't happen automatically, and a single hop that forgets to pass it along breaks the chain for everything beneath it.
- Logs, metrics, and traces answer different questions — logs for "what happened at this exact point," metrics for "how is the system behaving in aggregate," traces for "where did this one request's time actually go" — a mature observability setup needs all three, not just one.
- Structured logging (explicit fields, not free-text strings) is what makes correlation IDs actually searchable and joinable at scale — free-text logs with an ID buried in a sentence are far harder to query reliably than a structured field.
- Build observability in from the start, not during an incident — the value of tracing and correlation is realized exactly when things are already going wrong, which is the worst possible time to discover it was never wired up.
