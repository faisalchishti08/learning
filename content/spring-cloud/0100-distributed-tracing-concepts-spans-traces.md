---
card: spring-cloud
gi: 100
slug: distributed-tracing-concepts-spans-traces
title: "Distributed tracing concepts (spans, traces)"
---

## 1. What it is

A trace is the complete record of one logical operation as it flows through a distributed system — an incoming HTTP request that touches an API gateway, an order service, a payment service, and a database — and a span is one timed unit of work within that trace (one HTTP call, one database query, one message handler invocation), each span carrying a start time, an end time, a name, and a reference to its parent span, so the full set of spans for one trace reconstructs the entire causal, timed call tree of that operation across every service it touched.

```
traceId=abc123
  span 1: gateway        [0ms  -------- 120ms]
    span 2: order-service   [10ms -- 90ms]
      span 3: payment-service   [20ms - 60ms]
      span 4: db query           [65ms - 85ms]
```

## 2. Why & when

A single request in a microservices architecture might touch a dozen services before a response is returned — when that request is slow, or fails, figuring out *which* of those dozen services caused it, from each service's own isolated logs alone, means manually correlating timestamps across a dozen separate log streams with no shared identifier connecting them. Distributed tracing solves this by assigning one `traceId` to the entire request at its origin, propagating that same `traceId` (plus each span's own `spanId` and its parent's `spanId`) across every network hop the request makes, so that a single query against a tracing backend (Zipkin, Jaeger, or any OpenTelemetry-compatible store) reconstructs the entire request's path, timing, and hierarchy across every service instantly.

Reach for distributed tracing when:

- Diagnosing latency in a multi-service call chain — a trace's span tree immediately shows which specific span (which specific service call) consumed the bulk of the total request time, rather than requiring a guess-and-check tour through each service's own logs.
- Diagnosing a failure that occurred somewhere in a multi-hop chain — the trace shows exactly which span failed and what its immediate parent and children were doing at the time, giving precise fault localization instead of only "the overall request failed."
- Building any meaningful observability into a microservices system at all — tracing, alongside metrics and logs, is one of the three pillars of observability, and it's specifically the one that answers "how did this one request's work get distributed across my services," which neither metrics nor logs alone can answer as directly.

## 3. Core concept

```
 ONE trace = the whole request's journey, identified by ONE traceId shared across every span

 span:
   traceId    -- shared by every span in this trace
   spanId     -- unique to THIS span
   parentId   -- the spanId of the span that CALLED this one (absent for the root span)
   name       -- what this span represents (e.g. "GET /orders", "payment-service call")
   startTime, endTime -- this span's own duration

 the span tree is reconstructed AFTER the fact, purely from parentId references:
   root span (parentId=none)
     -> child span (parentId=root's spanId)
          -> grandchild span (parentId=child's spanId)
```

No single service ever sees the whole trace directly — each service only creates and reports its own span(s), and the tracing backend assembles the full tree by matching `traceId`s and `parentId`/`spanId` references across everything reported.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single trace contains a root span for the gateway with a child span for the order service which itself has two child spans for the payment service call and a database query each with its own start and end time within the parents time range">
  <rect x="20" y="20" width="600" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="30" y="44" fill="#6db33f" font-size="8" font-family="sans-serif">gateway (root span) — 0ms to 120ms</text>

  <rect x="60" y="80" width="440" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="70" y="101" fill="#79c0ff" font-size="7.5" font-family="sans-serif">order-service — 10ms to 90ms</text>

  <rect x="100" y="140" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="110" y="159" fill="#e6edf3" font-size="7" font-family="sans-serif">payment-service — 20ms to 60ms</text>

  <rect x="330" y="140" width="150" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="340" y="159" fill="#e6edf3" font-size="7" font-family="sans-serif">db query — 65ms to 85ms</text>

  <text x="30" y="195" fill="#8b949e" font-size="7.5" font-family="sans-serif">all four spans share ONE traceId; each child's parentId points to the span that called it</text>
</svg>

Nested boxes model nested timing: every child span's time range falls inside its parent's, and every span shares one `traceId`.

## 5. Runnable example

The scenario: model a trace as a small object graph — a root span with nested child spans — build it up as if reporting from three separate services, then reconstruct the parent/child tree purely from `parentId` references, and finally compute per-span duration and total request latency breakdown. Start with a single span, then a nested trace built from independently-created spans, then full tree reconstruction and latency analysis.

### Level 1 — Basic

A single span: an id, a name, a start and end time — the fundamental unit tracing is built from.

```java
import java.util.*;

public class TracingConceptsLevel1 {
    record Span(String spanId, String traceId, String parentId, String name, long startMs, long endMs) {
        long durationMs() { return endMs - startMs; }
    }

    public static void main(String[] args) {
        Span rootSpan = new Span("span-1", "trace-abc", null, "GET /orders", 0, 120);

        System.out.println("span: " + rootSpan.name() + " duration=" + rootSpan.durationMs() + "ms");
    }
}
```

How to run: `java TracingConceptsLevel1.java`

One `Span` record captures everything a tracing backend needs about one unit of work: which trace it belongs to (`traceId`), what called it (`parentId`, `null` here because this is the root), and how long it took (`endMs - startMs`).

### Level 2 — Intermediate

Build a small nested trace: four spans, created as if reported independently by four different services, all sharing one `traceId` and linked by `parentId`.

```java
import java.util.*;

public class TracingConceptsLevel2 {
    record Span(String spanId, String traceId, String parentId, String name, long startMs, long endMs) {
        long durationMs() { return endMs - startMs; }
    }

    public static void main(String[] args) {
        String traceId = "trace-abc"; // ONE traceId, generated once at the request's origin, propagated to every hop

        List<Span> spans = new ArrayList<>();
        spans.add(new Span("span-1", traceId, null, "gateway", 0, 120));
        spans.add(new Span("span-2", traceId, "span-1", "order-service", 10, 90));
        spans.add(new Span("span-3", traceId, "span-2", "payment-service", 20, 60));
        spans.add(new Span("span-4", traceId, "span-2", "db-query", 65, 85));

        // these four spans were "reported" by four DIFFERENT services -- yet they all share traceId
        for (Span s : spans) {
            System.out.println(s.name() + ": traceId=" + s.traceId() + " parentId=" + s.parentId() + " duration=" + s.durationMs() + "ms");
        }
    }
}
```

How to run: `java TracingConceptsLevel2.java`

Every span shares `traceId = "trace-abc"`, but each was independently created (by gateway, order-service, payment-service, and the database-query code respectively) — nothing here required a single service to know about the others directly; only the shared `traceId` and each span's own `parentId` reference connect them.

### Level 3 — Advanced

Reconstruct the full span tree purely from `parentId` references (as a tracing backend does when a trace is queried), and compute a latency breakdown showing which span consumed the largest share of total request time.

```java
import java.util.*;

public class TracingConceptsLevel3 {
    record Span(String spanId, String traceId, String parentId, String name, long startMs, long endMs) {
        long durationMs() { return endMs - startMs; }
    }

    static void printTree(Span span, Map<String, List<Span>> childrenByParent, int depth) {
        System.out.println("  ".repeat(depth) + span.name() + " (" + span.durationMs() + "ms)");
        for (Span child : childrenByParent.getOrDefault(span.spanId(), List.of())) {
            printTree(child, childrenByParent, depth + 1);
        }
    }

    public static void main(String[] args) {
        String traceId = "trace-abc";
        List<Span> spans = List.of(
                new Span("span-1", traceId, null, "gateway", 0, 120),
                new Span("span-2", traceId, "span-1", "order-service", 10, 90),
                new Span("span-3", traceId, "span-2", "payment-service", 20, 60),
                new Span("span-4", traceId, "span-2", "db-query", 65, 85)
        );

        // reconstruct the tree: group every span by its parentId
        Map<String, List<Span>> childrenByParent = new HashMap<>();
        Span root = null;
        for (Span s : spans) {
            if (s.parentId() == null) root = s;
            else childrenByParent.computeIfAbsent(s.parentId(), k -> new ArrayList<>()).add(s);
        }

        System.out.println("-- reconstructed span tree --");
        printTree(root, childrenByParent, 0);

        // latency breakdown: which span's OWN work (excluding known children) took the longest
        System.out.println("-- durations, longest first --");
        spans.stream()
             .sorted((a, b) -> Long.compare(b.durationMs(), a.durationMs()))
             .forEach(s -> System.out.println(s.name() + ": " + s.durationMs() + "ms"));
    }
}
```

How to run: `java TracingConceptsLevel3.java`

`childrenByParent` is built purely by grouping the flat `spans` list on each span's `parentId` — no span object holds a direct reference to its children, exactly mirroring how a real tracing backend receives independent span reports from separate services and reconstructs the hierarchy afterward, purely from the `parentId` field each span carries.

## 6. Walkthrough

Trace the tree reconstruction in Level 3.

1. The `for` loop over `spans` runs once per span. For `"span-1"` (`parentId == null`), the `if` branch assigns `root = "span-1"`'s `Span` object.
2. For `"span-2"` (`parentId = "span-1"`), the `else` branch runs `childrenByParent.computeIfAbsent("span-1", ...)`, creating a new list under key `"span-1"` and adding `"span-2"`'s span to it.
3. For `"span-3"` (`parentId = "span-2"`) and `"span-4"` (`parentId = "span-2"`), both are added to a list under key `"span-2"` — after the loop, `childrenByParent` holds `{"span-1": ["span-2"], "span-2": ["span-3", "span-4"]}`.
4. `printTree(root, childrenByParent, 0)` is called with `root = "span-1"` (gateway) at `depth=0` — it prints `"gateway (120ms)"`, then looks up `childrenByParent.getOrDefault("span-1", ...)`, finding `["span-2"]`, and recurses into it at `depth=1`.
5. The recursive call for `"span-2"` (order-service) prints `"  order-service (80ms)"` (indented one level), then looks up `childrenByParent.getOrDefault("span-2", ...)`, finding `["span-3", "span-4"]`, and recurses into each at `depth=2`.
6. `"span-3"` (payment-service) and `"span-4"` (db-query) each print at two levels of indentation and have no entries in `childrenByParent` for their own `spanId`s, so `printTree`'s recursive call for each finds an empty list and simply returns after printing — they are leaves of the tree.
7. The final sorted-by-duration block reorders the flat `spans` list independent of the tree structure, printing `gateway (120ms)`, `order-service (80ms)`, `payment-service (40ms)`, `db-query (20ms)` — immediately surfacing that `order-service`'s own span accounts for the bulk of the total request time, and within it, `payment-service` is the single largest contributor.

```
tree (indentation = depth):
gateway (120ms)
  order-service (80ms)
    payment-service (40ms)
    db-query (20ms)

sorted by duration: gateway > order-service > payment-service > db-query
```

## 7. Gotchas & takeaways

> **Gotcha:** a child span's own reported duration is *not* automatically subtracted from its parent's — `order-service`'s `80ms` already *includes* the `40ms` spent inside `payment-service` and the `20ms` spent on the `db-query`, meaning only `20ms` (`80 - 40 - 20`) was order-service's own processing time outside of those two calls. Reading span durations as if they were mutually exclusive, rather than nested and overlapping with their children, is a common and misleading mistake when eyeballing a trace.

- A trace is the aggregate of every span sharing one `traceId`; a span is one timed, named unit of work with a reference to its parent — this parent/child linkage, not any single service's own knowledge of the whole call chain, is what lets the full tree be reconstructed after the fact.
- Because each service only ever creates and reports its own span(s), tracing scales naturally to any number of services in a call chain — no service needs to know the full topology of the system it's part of, only how to propagate the trace context (the `traceId` and its own span's id as the next hop's `parentId`) to whatever it calls next.
- Span duration includes all of that span's own child spans' time — computing a span's "self time" (time not attributable to any child) requires subtracting children's durations from the parent's, as the walkthrough above demonstrates.
- Later cards in this section cover exactly how this conceptual model gets implemented in Spring applications: Micrometer Tracing for instrumentation, Brave/Zipkin and OpenTelemetry for backend integration, and B3/W3C propagation formats for actually carrying `traceId`/`spanId` across network hops.
