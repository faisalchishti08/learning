---
card: spring-cloud
gi: 102
slug: brave-zipkin-integration
title: "Brave / Zipkin integration"
---

## 1. What it is

`micrometer-tracing-bridge-brave` plugs Brave (a lightweight, mature Java tracer library) in as the concrete implementation underneath Micrometer Tracing's neutral API, and `zipkin-reporter-brave` batches the spans Brave produces and ships them to a Zipkin server over HTTP, where Zipkin's own UI renders the reconstructed trace tree — this is the traditional, Sleuth-era tracing stack, still fully supported and often the simplest path when Zipkin is the desired trace-viewing backend.

```xml
<dependency>
    <groupId>io.micrometer</groupId>
    <artifactId>micrometer-tracing-bridge-brave</artifactId>
</dependency>
<dependency>
    <groupId>io.zipkin.reporter2</groupId>
    <artifactId>zipkin-reporter-brave</artifactId>
</dependency>
```

```properties
management.zipkin.tracing.endpoint=http://localhost:9411/api/v2/spans
management.tracing.sampling.probability=1.0
```

## 2. Why & when

Choosing a tracing bridge means choosing which ecosystem of tools and export formats an application plugs into — Brave, paired with Zipkin as the backend, is a well-established, low-overhead combination with a long production track record, a straightforward HTTP-based span-reporting protocol, and a lightweight self-hostable server (or hosted equivalents) for viewing traces. It remains a strong default choice specifically when Zipkin (rather than Jaeger or a vendor OpenTelemetry-native backend) is the target trace store, or when migrating an existing Sleuth-based application that already used Brave/Zipkin and has no immediate need to switch ecosystems.

Reach for the Brave/Zipkin combination when:

- Zipkin is the chosen (or already-deployed) trace-viewing backend — Brave's reporter integrates with Zipkin's ingest API directly, with minimal configuration beyond the endpoint URL.
- Migrating an existing Spring Cloud Sleuth application forward — Sleuth itself was built on Brave, so keeping Brave as the bridge underneath Micrometer Tracing minimizes behavioral differences during that migration (the dedicated Sleuth-migration card covers this specifically).
- Low tracer overhead matters and the broader observability stack doesn't already mandate OpenTelemetry specifically — Brave is a mature, minimal-dependency tracer, and pairing it with Zipkin avoids pulling in the somewhat heavier OpenTelemetry SDK when nothing else in the stack requires it.

## 3. Core concept

```
 application span creation (via the neutral Tracer API)
        |
        v
 Brave tracer implementation
   -- creates/manages spans, propagates context, applies sampling decision
        |
        v
 zipkin-reporter-brave
   -- batches finished spans, POSTs them as JSON to Zipkin's HTTP ingest endpoint
        |
        v
 Zipkin server
   -- stores spans, groups by traceId, renders the reconstructed trace tree in its UI
```

The reporter batches and sends asynchronously — application request-handling threads are not blocked waiting for the Zipkin server to acknowledge receipt of a span.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An application using the Brave bridge creates spans that are batched by the Zipkin reporter and sent over HTTP to a Zipkin server which stores and renders the reconstructed trace">
  <rect x="20" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="48" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">app + Brave bridge</text>

  <rect x="230" y="20" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="315" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">zipkin-reporter-brave</text>
  <text x="315" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">batches + POSTs spans</text>

  <rect x="460" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="535" y="48" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Zipkin server + UI</text>

  <defs><marker id="a102" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="43" x2="230" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a102)"/>
  <line x1="400" y1="43" x2="460" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a102)"/>
  <text x="315" y="110" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">reporting is asynchronous and batched — request threads are not blocked</text>
</svg>

Three distinct stages, each independently swappable — Brave for a different tracer, the reporter for a different transport, Zipkin for a different backend — without the other two needing to change.

## 5. Runnable example

The scenario: model span creation, batched asynchronous reporting, and a receiving backend that groups spans by trace — mirroring the real Brave + Zipkin reporter pipeline without a live server. Start with unbatched, synchronous reporting of one span, then add batching, then add asynchronous flushing on a size/time threshold, mirroring how a real reporter avoids blocking the application on every single span.

### Level 1 — Basic

One span, reported synchronously and individually — the simplest possible version, before batching is introduced.

```java
import java.util.*;

public class BraveZipkinLevel1 {
    record Span(String traceId, String spanId, String name, long durationMs) {}

    // stands in for a Zipkin server's ingest endpoint
    static class ZipkinServer {
        List<Span> stored = new ArrayList<>();
        void receive(Span span) {
            stored.add(span);
            System.out.println("Zipkin received: " + span.name() + " (trace " + span.traceId() + ")");
        }
    }

    public static void main(String[] args) {
        ZipkinServer zipkin = new ZipkinServer();
        Span span = new Span("trace-1", "span-1", "GET /orders", 45);

        zipkin.receive(span); // synchronous, one-at-a-time -- NOT how the real reporter behaves
    }
}
```

How to run: `java BraveZipkinLevel1.java`

Reporting synchronously and per-span is simple but doesn't scale — a high-throughput service producing hundreds of spans per second would overwhelm a naive one-HTTP-call-per-span reporter, which is exactly the problem batching (the next level) solves.

### Level 2 — Intermediate

Add batching: spans accumulate locally and are flushed to "Zipkin" together, once a batch size threshold is reached, mirroring `zipkin-reporter-brave`'s own buffering behavior.

```java
import java.util.*;

public class BraveZipkinLevel2 {
    record Span(String traceId, String spanId, String name, long durationMs) {}

    static class ZipkinServer {
        List<Span> stored = new ArrayList<>();
        void receiveBatch(List<Span> batch) {
            stored.addAll(batch);
            System.out.println("Zipkin received batch of " + batch.size() + " spans");
        }
    }

    // stands in for zipkin-reporter-brave's own local buffering
    static class BatchingReporter {
        ZipkinServer zipkin;
        List<Span> buffer = new ArrayList<>();
        int batchSize;
        BatchingReporter(ZipkinServer zipkin, int batchSize) { this.zipkin = zipkin; this.batchSize = batchSize; }

        void report(Span span) {
            buffer.add(span);
            if (buffer.size() >= batchSize) flush(); // send once the buffer fills, not per-span
        }
        void flush() {
            if (buffer.isEmpty()) return;
            zipkin.receiveBatch(new ArrayList<>(buffer));
            buffer.clear();
        }
    }

    public static void main(String[] args) {
        ZipkinServer zipkin = new ZipkinServer();
        BatchingReporter reporter = new BatchingReporter(zipkin, 3);

        reporter.report(new Span("trace-1", "span-1", "GET /orders", 45));
        reporter.report(new Span("trace-1", "span-2", "order-service", 30));
        System.out.println("2 spans reported so far, buffer not yet flushed (batchSize=3)");
        reporter.report(new Span("trace-1", "span-3", "db-query", 12)); // THIS one triggers the flush

        System.out.println("total stored at Zipkin: " + zipkin.stored.size());
    }
}
```

How to run: `java BraveZipkinLevel2.java`

The first two `report` calls only add to `buffer` — no HTTP-equivalent call to `zipkin` happens until the third call brings `buffer.size()` to `3`, matching `batchSize`, at which point `flush` sends all three at once, dramatically reducing the number of reporting round-trips compared to Level 1's one-call-per-span approach.

### Level 3 — Advanced

Add a time-based flush alongside the size-based one (mirroring the real reporter's dual size/interval trigger), so spans aren't held indefinitely waiting for a batch to fill during a quiet period, plus handle a reporting failure without losing already-buffered spans.

```java
import java.util.*;

public class BraveZipkinLevel3 {
    record Span(String traceId, String spanId, String name, long durationMs) {}

    static class ZipkinServer {
        List<Span> stored = new ArrayList<>();
        boolean simulateFailureOnce = false;
        void receiveBatch(List<Span> batch) {
            if (simulateFailureOnce) {
                simulateFailureOnce = false;
                throw new RuntimeException("Zipkin server temporarily unreachable");
            }
            stored.addAll(batch);
            System.out.println("Zipkin received batch of " + batch.size() + " spans");
        }
    }

    static class BatchingReporter {
        ZipkinServer zipkin;
        List<Span> buffer = new ArrayList<>();
        int batchSize;
        BatchingReporter(ZipkinServer zipkin, int batchSize) { this.zipkin = zipkin; this.batchSize = batchSize; }

        void report(Span span) {
            buffer.add(span);
            if (buffer.size() >= batchSize) flush();
        }

        // models the reporter's periodic timer-triggered flush, for when traffic is too low to fill a batch quickly
        void flushOnTimer() {
            if (!buffer.isEmpty()) {
                System.out.println("timer-triggered flush (buffer not full, but interval elapsed)");
                flush();
            }
        }

        void flush() {
            List<Span> toSend = new ArrayList<>(buffer);
            try {
                zipkin.receiveBatch(toSend);
                buffer.clear(); // only clear on SUCCESSFUL send -- keep spans buffered if the call failed
            } catch (RuntimeException e) {
                System.out.println("flush failed, spans remain buffered for retry: " + e.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        ZipkinServer zipkin = new ZipkinServer();
        BatchingReporter reporter = new BatchingReporter(zipkin, 5);

        reporter.report(new Span("trace-1", "span-1", "GET /orders", 45));
        reporter.report(new Span("trace-1", "span-2", "order-service", 30));

        zipkin.simulateFailureOnce = true;
        reporter.flushOnTimer(); // timer fires before batchSize is reached; the send itself fails
        System.out.println("buffer size after failed flush: " + reporter.buffer.size());

        reporter.flushOnTimer(); // retry succeeds this time
        System.out.println("buffer size after successful retry: " + reporter.buffer.size());
    }
}
```

How to run: `java BraveZipkinLevel3.java`

The first `flushOnTimer` call attempts to send both buffered spans, but `zipkin.receiveBatch` throws because `simulateFailureOnce` was set — the `catch` block prevents `buffer.clear()` from running, so both spans remain in `reporter.buffer` (confirmed by the size printout still showing `2`); the second `flushOnTimer` call retries with the same buffered spans and succeeds this time, correctly clearing the buffer — no spans were silently lost to the earlier failed send.

## 6. Walkthrough

Trace the failed-then-retried flush sequence in Level 3.

1. Two `report` calls add two spans to `reporter.buffer`, and since `batchSize` is `5`, neither call triggers an automatic flush.
2. `zipkin.simulateFailureOnce = true` arms the server to throw on its very next `receiveBatch` call.
3. `reporter.flushOnTimer()` finds `buffer` non-empty, prints the timer-triggered-flush message, and calls `flush()`.
4. Inside `flush`, `toSend` is a *copy* of the current buffer (two spans), and `zipkin.receiveBatch(toSend)` is called — this hits the armed failure, throwing `RuntimeException("Zipkin server temporarily unreachable")`, caught by the surrounding `try`/`catch`.
5. Because the exception was thrown before `buffer.clear()` could run, `reporter.buffer` still holds both original spans — the `println` right after confirms `buffer size after failed flush: 2`.
6. `reporter.flushOnTimer()` is called a second time — `buffer` is still non-empty (the same two spans), so it again calls `flush()`; this time `zipkin.simulateFailureOnce` is `false` (it was reset to `false` inside the first, failed call, right before the throw), so `receiveBatch` succeeds, printing the received-batch message and allowing `buffer.clear()` to run.
7. The final `println` confirms `buffer size after successful retry: 0` — the two spans that survived the earlier failure were successfully delivered on retry, with no data loss across the failure.

```
report(span1), report(span2)          -> buffer = [span1, span2], batchSize=5 not reached
simulateFailureOnce = true
flushOnTimer() -> flush() -> receiveBatch THROWS -> catch prevents buffer.clear() -> buffer still = [span1, span2]
flushOnTimer() -> flush() -> receiveBatch SUCCEEDS -> buffer.clear() -> buffer = []
```

## 7. Gotchas & takeaways

> **Gotcha:** a reporter that clears its buffer unconditionally, regardless of whether the send actually succeeded, silently loses spans on every transient network failure or Zipkin server outage — as Level 3 demonstrates, `buffer.clear()` must run only after a confirmed-successful send, never inside a `finally` block or before the send is attempted, or trace data quietly goes missing exactly when the observability system is most needed (during an incident that's also causing connectivity issues).

- Brave handles span creation, context propagation, and sampling; `zipkin-reporter-brave` handles the separate concern of getting finished spans to a Zipkin server efficiently, via batching — these are two distinct responsibilities, cleanly separated, matching the two-dependency setup shown in Part 1.
- Batching (by size, by time interval, or both, as Level 3 modeled) trades a small amount of reporting latency for a large reduction in the number of network calls made purely for span export — essential for any service producing meaningful trace volume.
- A reporter must handle transient failures to the tracing backend without losing buffered spans or, worse, blocking the application's own request-handling threads — reporting is inherently a best-effort, asynchronous side channel, and should never become a source of application-request latency or failure itself.
- Zipkin's own UI is what actually reconstructs and displays the trace tree from the `traceId`/`parentId` relationships across every span it receives — the application and reporter's job ends at successfully delivering spans; querying and visualizing them is Zipkin's responsibility entirely.
