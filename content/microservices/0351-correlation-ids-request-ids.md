---
card: microservices
gi: 351
slug: correlation-ids-request-ids
title: "Correlation IDs / request IDs"
---

## 1. What it is

A **correlation ID** (or request ID) is a unique identifier generated once, at the entry point of a request, and passed along — in headers, in message metadata, in every log line — through every service that request touches, so that anyone reading logs, metrics, or traces from any of those services can find every piece of data related to that one specific request by searching for a single shared value.

## 2. Why & when

Without a correlation ID, connecting a log line in `payment-service` to the specific `order-service` request that triggered it (the exact problem shown in [three pillars](0349-three-pillars-logs-metrics-traces.md)'s Level 1 example) is guesswork at best — timestamps are close but not exact, and under concurrent load, many requests are in flight across many services simultaneously with no way to tell which log lines belong together. A correlation ID solves this directly: generate it once at the edge (the API gateway, or the first service that receives the request), and every downstream service includes it in its own logs and passes it along to whatever it calls next.

Generate a correlation ID for every incoming request at your system's entry point, and propagate it through every downstream call — HTTP header, message header, whatever the communication mechanism is — as an unconditional, baseline requirement for any request that might touch more than one service. This is foundational infrastructure that [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) builds on and formalizes (a trace ID *is* a correlation ID, with additional structure), so most modern systems get this for free from a tracing library rather than needing to hand-roll it — but understanding the underlying need is what makes tracing infrastructure make sense.

## 3. Core concept

A correlation ID is generated once (typically a UUID) at the request's entry point, stored somewhere accessible to all logging within that request's handling (commonly a thread-local or a framework-provided "MDC" — Mapped Diagnostic Context), included in every log line automatically, and explicitly forwarded as a header on every outbound call so the next service can do the same.

```java
String correlationId = UUID.randomUUID().toString(); // generated ONCE, at the entry point
MDC.put("correlationId", correlationId); // every subsequent log line in this request includes it automatically
httpClient.send(request.header("X-Correlation-Id", correlationId)); // propagated to the NEXT service
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request enters the gateway which generates a correlation ID; the ID is passed as a header to order-service, then to payment-service; every log line in every service includes the same correlation ID">
  <rect x="20" y="60" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Gateway: generates ID</text>

  <line x1="140" y1="77" x2="210" y2="77" stroke="#8b949e" marker-end="url(#a351)"/>
  <text x="175" y="67" fill="#8b949e" font-size="8" font-family="sans-serif">X-Correlation-Id</text>
  <rect x="220" y="60" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="290" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">order-service</text>

  <line x1="360" y1="77" x2="430" y2="77" stroke="#8b949e" marker-end="url(#a351)"/>
  <text x="395" y="67" fill="#8b949e" font-size="8" font-family="sans-serif">same ID</text>
  <rect x="440" y="60" width="160" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="520" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">payment-service</text>

  <text x="320" y="140" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Every log line in EVERY service includes the SAME correlation ID -- searchable as one unit.</text>

  <defs><marker id="a351" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Generated once at the entry point, the correlation ID is forwarded unchanged to every downstream service and stamped on every log line.

## 5. Runnable example

Scenario: a checkout request across three services, first shown with no correlation ID (logs impossible to reliably connect under concurrent load), then fixed with a correlation ID generated at the gateway and threaded through explicitly, and finally extended to show it surviving an asynchronous hop (a message queue), where it must be carried in message metadata rather than an HTTP header.

### Level 1 — Basic

```java
// File: NoCorrelationIdAmbiguous.java -- TWO concurrent checkouts produce
// logs with NOTHING linking each service's lines back to the right request.
import java.util.*;

public class NoCorrelationIdAmbiguous {
    static List<String> orderServiceLogs = new ArrayList<>();
    static List<String> paymentServiceLogs = new ArrayList<>();

    static void checkout(String orderId) {
        orderServiceLogs.add("order-service: processing checkout");
        paymentServiceLogs.add("payment-service: charging card"); // WHICH checkout is this for?? No way to tell from the log alone.
    }

    public static void main(String[] args) {
        checkout("order-1"); // concurrent request 1
        checkout("order-2"); // concurrent request 2 (interleaved in a real system)

        System.out.println("order-service logs: " + orderServiceLogs);
        System.out.println("payment-service logs: " + paymentServiceLogs);
        System.out.println("With TWO concurrent checkouts, which payment-service line belongs to which order?? AMBIGUOUS.");
    }
}
```

How to run: `java NoCorrelationIdAmbiguous.java`

Both `paymentServiceLogs` entries are identical strings with no reference back to `"order-1"` or `"order-2"` — under real concurrent load, with interleaved log output from many simultaneous requests, there is no reliable way to determine which `payment-service` log line corresponds to which `order-service` request.

### Level 2 — Intermediate

```java
// File: CorrelationIdThreadedThrough.java -- a correlation ID is
// generated ONCE at the entry point and explicitly passed to every
// downstream call; every log line includes it.
import java.util.*;

public class CorrelationIdThreadedThrough {
    static List<String> orderServiceLogs = new ArrayList<>();
    static List<String> paymentServiceLogs = new ArrayList<>();

    static void checkout(String orderId, String correlationId) { // generated ONCE by the caller (simulating the gateway)
        orderServiceLogs.add("[" + correlationId + "] order-service: processing checkout for " + orderId);
        chargePayment(orderId, correlationId); // PROPAGATED to the next service explicitly
    }

    static void chargePayment(String orderId, String correlationId) {
        paymentServiceLogs.add("[" + correlationId + "] payment-service: charging card for " + orderId);
    }

    public static void main(String[] args) {
        String correlationId1 = "corr-" + UUID.randomUUID();
        String correlationId2 = "corr-" + UUID.randomUUID();

        checkout("order-1", correlationId1);
        checkout("order-2", correlationId2);

        System.out.println("order-service logs: " + orderServiceLogs);
        System.out.println("payment-service logs: " + paymentServiceLogs);
        System.out.println("Now each payment-service line's correlation ID EXACTLY matches its corresponding order-service line -- unambiguous, even under concurrency.");
    }
}
```

How to run: `java CorrelationIdThreadedThrough.java`

Each `checkout` call generates (or, in a real system, receives from the gateway) its own unique `correlationId` and passes it explicitly into `chargePayment`. Every log line, in both services, is prefixed with that ID — searching logs for `correlationId1` reliably returns exactly the lines belonging to `"order-1"`'s request, across both services, no matter how many other requests were happening concurrently.

### Level 3 — Advanced

```java
// File: CorrelationIdSurvivesAsyncHop.java -- the correlation ID must
// also survive an ASYNCHRONOUS hop through a message queue, where there
// is no HTTP header to carry it -- it must be placed in the message's
// own metadata instead.
import java.util.*;

public class CorrelationIdSurvivesAsyncHop {
    record Message(String correlationId, String payload) {} // correlationId travels IN the message itself
    static Queue<Message> stockReservationQueue = new LinkedList<>();
    static List<String> orderServiceLogs = new ArrayList<>();
    static List<String> inventoryServiceLogs = new ArrayList<>();

    static void checkout(String orderId, String correlationId) {
        orderServiceLogs.add("[" + correlationId + "] order-service: publishing stock reservation request for " + orderId);
        // ASYNC hop: no HTTP header here -- the correlation ID must ride along IN the message.
        stockReservationQueue.add(new Message(correlationId, "ReserveStock:" + orderId));
    }

    static void inventoryServiceConsumesQueue() { // runs LATER, in a completely different process
        Message message = stockReservationQueue.poll();
        // The correlation ID is extracted from the MESSAGE, not from any HTTP context (there isn't one here).
        inventoryServiceLogs.add("[" + message.correlationId() + "] inventory-service: processing " + message.payload());
    }

    public static void main(String[] args) {
        String correlationId = "corr-" + UUID.randomUUID();
        checkout("order-1", correlationId);

        System.out.println("--- some time passes; inventory-service consumes the queue in a SEPARATE process ---");
        inventoryServiceConsumesQueue();

        System.out.println("order-service logs: " + orderServiceLogs);
        System.out.println("inventory-service logs: " + inventoryServiceLogs);
        System.out.println("The SAME correlation ID appears in BOTH, even across the async, queue-based hop.");
    }
}
```

How to run: `java CorrelationIdSurvivesAsyncHop.java`

`checkout` builds a `Message` that carries `correlationId` as one of its own fields — since there's no HTTP request/response here to attach a header to, the message itself is the only vehicle available for propagating the ID across this asynchronous boundary. When `inventoryServiceConsumesQueue` runs, potentially much later and in an entirely separate process, it reads `message.correlationId()` directly from the message and includes it in its own log line — the same correlation ID that started in `order-service` now appears in `inventory-service`'s logs too, even though no synchronous call chain connects them.

## 6. Walkthrough

Trace `CorrelationIdSurvivesAsyncHop.main` in order. **First**, a single `correlationId` is generated. **Then**, `checkout("order-1", correlationId)` runs: it appends a log line to `orderServiceLogs` including that ID, and constructs a `Message` record with `correlationId` as one of its fields, adding it to `stockReservationQueue`.

**Next**, `main` prints a line marking the passage of time, representing the asynchronous gap between the message being queued and being consumed — in a real system, this could be milliseconds or much longer, and would very likely happen in an entirely different process or even a different machine.

**Then**, `inventoryServiceConsumesQueue()` runs: it polls the one message off `stockReservationQueue`, and — critically — extracts `message.correlationId()` directly from the message's own data, since there is no ambient request context (like an HTTP header) available in this asynchronous, queue-consuming code path. It appends a log line to `inventoryServiceLogs` using that extracted ID.

**Finally**, `main` prints both services' logs, showing that the identical correlation ID string appears in both `orderServiceLogs` and `inventoryServiceLogs` — proving the identifier survived the transition from a synchronous request-handling context into an asynchronous, message-driven one, by being carried explicitly as data within the message rather than relying on any transport-specific mechanism like an HTTP header.

```
checkout(order-1, corrId)  -> orderServiceLogs += "[corrId] ..." ; queue += Message(corrId, "ReserveStock:order-1")
[async gap -- different process, different time]
inventoryServiceConsumesQueue() -> polls Message -> extracts corrId FROM the message -> inventoryServiceLogs += "[corrId] ..."
Both logs share the SAME corrId, despite no synchronous call connecting them.
```

## 7. Gotchas & takeaways

> A correlation ID that's only propagated through synchronous HTTP headers silently breaks the moment a request's processing crosses into an asynchronous hop (a message queue, a scheduled job triggered by an earlier event) — the ID must be explicitly carried as part of the message or event payload/metadata for the chain to survive that transition, exactly as shown in Level 3.

- A correlation ID is generated once at a request's entry point and must be explicitly propagated through every subsequent call — synchronous (HTTP headers) or asynchronous (message metadata) — for logs across services to be reliably connectable.
- Without one, connecting related log lines across services under real concurrent load is effectively guesswork.
- This concept is the foundation that [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) formalizes and typically automates — a trace ID is a correlation ID with additional structure (parent/child span relationships) layered on top.
- Standardized propagation formats like [W3C Trace Context or B3 headers](0353-trace-context-w3c-trace-context-b3-headers.md) exist so different services and libraries can interoperate on correlation without each team inventing its own header scheme.
