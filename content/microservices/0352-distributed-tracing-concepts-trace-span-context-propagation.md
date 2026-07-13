---
card: microservices
gi: 352
slug: distributed-tracing-concepts-trace-span-context-propagation
title: "Distributed tracing concepts (trace, span, context propagation)"
---

## 1. What it is

**Distributed tracing** formalizes and automates the [correlation ID](0351-correlation-ids-request-ids.md) idea into a structured model: a **trace** represents one end-to-end request across every service it touches, identified by a single trace ID; a **span** represents one unit of work within that trace (one service handling one operation), with its own span ID, a start time, a duration, and a reference to its **parent span** (forming a tree, since a service handling a request often calls other services, creating child spans); **context propagation** is the mechanism — headers on outbound calls — that carries the trace ID and the current span ID forward so the next service's spans correctly attach as children.

## 2. Why & when

A flat correlation ID tells you which log lines belong to the same request, but it doesn't capture the *structure* of that request — which service called which other service, in what order, nested how deeply, and how long each part took relative to the whole. Spans, organized into a parent/child tree under one trace, capture exactly this: a trace visualized as a waterfall or flame graph shows you, at a glance, which service's span accounts for most of the total time, and where in the call tree that slow span sits.

Use distributed tracing whenever a request's path through the system is complex enough that "which service called what, and how long did each part take" is itself useful information — which, in any microservices system beyond the simplest, is essentially always. This is the concept underlying tools like Zipkin, Jaeger, and OpenTelemetry's tracing API; you'll typically use a tracing library that implements this model for you rather than hand-building spans, but understanding the trace/span/propagation model is what makes those tools' output interpretable.

## 3. Core concept

A trace ID is generated once, at the root of a request. Each service, upon receiving a request, starts a new span as a child of whatever span ID it received in the incoming request's context; when that service calls another service, it propagates the trace ID and its *own* span ID (as the next span's parent) in the outbound request's headers. The result, when all spans for one trace ID are collected, is a tree: the root span (the entry point) has children (each downstream call), which may have their own children, and so on.

```java
record Span(String traceId, String spanId, String parentSpanId, String service, long startMs, long durationMs) {}
// A trace = every Span sharing one traceId, forming a tree via parentSpanId references.
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree of spans: root span in the gateway, with two children -- order-service and, nested under order-service, payment-service as a grandchild span">
  <rect x="230" y="15" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">gateway (root span)</text>

  <line x1="320" y1="49" x2="320" y2="80" stroke="#8b949e" marker-end="url(#a352)"/>
  <rect x="230" y="80" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="102" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">order-service (child)</text>

  <line x1="320" y1="114" x2="320" y2="145" stroke="#8b949e" marker-end="url(#a352)"/>
  <rect x="230" y="145" width="180" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="167" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">payment-service (grandchild)</text>

  <defs><marker id="a352" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Spans form a tree via parent references, all sharing one trace ID — the full structure of one request across every service it touched.

## 5. Runnable example

Scenario: a checkout request across three nested service calls, first with only a flat correlation ID (no structure), then rebuilt with proper trace/span/parent modeling capturing the call tree, and finally extended to render the trace as an indented, human-readable waterfall showing nesting depth and relative timing.

### Level 1 — Basic

```java
// File: FlatCorrelationIdNoStructure.java -- a single correlation ID
// links log lines, but captures NO structure -- no idea which service
// called which, or how deeply nested each call was.
import java.util.*;

public class FlatCorrelationIdNoStructure {
    static List<String> logs = new ArrayList<>();

    static void handle(String correlationId, String service) {
        logs.add("[" + correlationId + "] " + service + " handled something");
    }

    public static void main(String[] args) {
        String correlationId = "corr-abc";
        handle(correlationId, "gateway");
        handle(correlationId, "order-service");
        handle(correlationId, "payment-service");

        System.out.println(logs);
        System.out.println("All three lines share one ID -- but WHO called WHOM? Flat, no tree structure at all.");
    }
}
```

How to run: `java FlatCorrelationIdNoStructure.java`

All three log lines correctly share `"corr-abc"`, letting you find them together — but nothing here says `gateway` called `order-service` which called `payment-service`, as opposed to all three being called independently and in parallel by something else. The correlation ID links the *events*, not the *structure* of the call.

### Level 2 — Intermediate

```java
// File: SpansFormATree.java -- each service starts a SPAN referencing
// its PARENT span, building an explicit tree structure under one trace ID.
import java.util.*;

public class SpansFormATree {
    record Span(String traceId, String spanId, String parentSpanId, String service) {}
    static List<Span> spans = new ArrayList<>();
    static int nextSpanId = 1;

    static Span startSpan(String traceId, String parentSpanId, String service) {
        Span span = new Span(traceId, "span-" + (nextSpanId++), parentSpanId, service);
        spans.add(span);
        return span;
    }

    public static void main(String[] args) {
        String traceId = "trace-xyz";

        Span rootSpan = startSpan(traceId, null, "gateway"); // root: NO parent
        Span orderSpan = startSpan(traceId, rootSpan.spanId(), "order-service"); // child of gateway
        Span paymentSpan = startSpan(traceId, orderSpan.spanId(), "payment-service"); // child of order-service

        System.out.println("All spans for trace " + traceId + ":");
        spans.forEach(s -> System.out.println("  " + s.spanId() + " (" + s.service() + "), parent=" + s.parentSpanId()));
        System.out.println("NOW the call tree is explicit: gateway -> order-service -> payment-service, nested.");
    }
}
```

How to run: `java SpansFormATree.java`

`startSpan` records each span's `parentSpanId` explicitly: the root span (`gateway`) has `parentSpanId=null`; `order-service`'s span references the root's `spanId` as its parent; `payment-service`'s span references `order-service`'s span as *its* parent. Printing all three spans now reveals the exact call structure — not just that they're related, but precisely who called whom.

### Level 3 — Advanced

```java
// File: RenderTraceAsWaterfall.java -- reconstructs the span tree and
// renders it as an INDENTED waterfall (the standard tracing-UI view),
// showing nesting depth and each span's own duration.
import java.util.*;

public class RenderTraceAsWaterfall {
    record Span(String traceId, String spanId, String parentSpanId, String service, long startMs, long durationMs) {}
    static List<Span> spans = new ArrayList<>();

    static void printWaterfall(String traceId) {
        Map<String, List<Span>> childrenByParent = new HashMap<>();
        Span root = null;
        for (Span s : spans) {
            if (!s.traceId().equals(traceId)) continue;
            if (s.parentSpanId() == null) root = s;
            else childrenByParent.computeIfAbsent(s.parentSpanId(), k -> new ArrayList<>()).add(s);
        }
        System.out.println("Trace " + traceId + " waterfall:");
        printSpanRecursive(root, childrenByParent, 0);
    }

    static void printSpanRecursive(Span span, Map<String, List<Span>> childrenByParent, int depth) {
        String indent = "  ".repeat(depth);
        System.out.println(indent + span.service() + " [" + span.spanId() + "] -- " + span.durationMs() + "ms (starts at t=" + span.startMs() + "ms)");
        for (Span child : childrenByParent.getOrDefault(span.spanId(), List.of())) {
            printSpanRecursive(child, childrenByParent, depth + 1); // RECURSE, one level DEEPER for each child
        }
    }

    public static void main(String[] args) {
        String traceId = "trace-xyz";
        spans.add(new Span(traceId, "span-1", null, "gateway", 0, 4000));
        spans.add(new Span(traceId, "span-2", "span-1", "order-service", 10, 3950));
        spans.add(new Span(traceId, "span-3", "span-2", "payment-service", 20, 3900));

        printWaterfall(traceId);
        System.out.println("The INDENTATION shows nesting depth; comparing durations shows payment-service accounts for nearly ALL the total time.");
    }
}
```

How to run: `java RenderTraceAsWaterfall.java`

`printWaterfall` first builds a `childrenByParent` map by grouping every span (except the root) under its `parentSpanId`, then finds the root span (the one with `parentSpanId=null`). `printSpanRecursive` prints each span indented by its depth in the tree and then recurses into its children, each one level deeper — reconstructing the exact nested call structure visually, along with each span's own duration, so a reader can immediately see both *how deep* the call chain went and *which* span dominates the overall time.

## 6. Walkthrough

Trace `RenderTraceAsWaterfall.main` in order. **First**, three spans are added: `span-1` (`gateway`, no parent, `4000ms`), `span-2` (`order-service`, parent `span-1`, `3950ms`), and `span-3` (`payment-service`, parent `span-2`, `3900ms`).

**Next**, `printWaterfall("trace-xyz")` runs. It iterates all spans, and for each one either identifies it as the `root` (if `parentSpanId` is `null` — this is `span-1`) or adds it to `childrenByParent` keyed by its parent's ID (`span-2` goes under `"span-1"`, `span-3` goes under `"span-2"`).

**Then**, `printSpanRecursive(root, childrenByParent, 0)` is called with `depth=0`. It prints `span-1`'s line with no indentation, then looks up `childrenByParent.get("span-1")`, finding `[span-2]`, and recurses into it with `depth=1`.

**Inside that recursive call**, `span-2`'s line prints with one level of indentation (`"  "`), and then `childrenByParent.get("span-2")` is looked up, finding `[span-3]`; the method recurses again, this time with `depth=2`.

**Inside the innermost call**, `span-3`'s line prints with two levels of indentation, and `childrenByParent.get("span-3")` returns nothing (no children), so the recursion ends there and unwinds back up through the two outer calls, which have nothing left to do.

**Finally**, `main` prints a closing observation: comparing the durations (`4000ms` total, `3950ms` inside `order-service`, `3900ms` inside `payment-service`) shows that nearly all of the total time is attributable to the innermost, most deeply nested span — exactly the kind of insight a waterfall visualization is designed to surface at a glance.

```
gateway [span-1] -- 4000ms
  order-service [span-2] -- 3950ms
    payment-service [span-3] -- 3900ms
```

## 7. Gotchas & takeaways

> A span's own duration typically includes the time spent waiting on its children — `order-service`'s `3950ms` includes the `3900ms` spent inside `payment-service`'s call. Reading a waterfall correctly means understanding that outer spans' durations overlap with their children's, not that they're additional, separate time on top of them.

- A trace is the full set of spans sharing one trace ID; a span is one unit of work with its own ID, timing, and a reference to its parent span, forming a tree.
- Context propagation — carrying the trace ID and current span ID forward on every outbound call — is what lets each downstream service's spans correctly attach as children in that tree.
- Rendering a trace as a waterfall (indented by nesting depth) is the standard way tracing tools visualize this structure, immediately revealing which nested call dominates the overall latency.
- Standardized header formats for propagating this context across service and even vendor boundaries are covered next, in [trace context (W3C Trace Context, B3 headers)](0353-trace-context-w3c-trace-context-b3-headers.md).
