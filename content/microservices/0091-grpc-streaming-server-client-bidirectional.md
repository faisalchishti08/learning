---
card: microservices
gi: 91
slug: grpc-streaming-server-client-bidirectional
title: "gRPC streaming (server, client, bidirectional)"
---

## 1. What it is

gRPC supports four RPC shapes, building on the [HTTP/2 streaming](0089-grpc-and-http-2.md) foundation: **unary** (one request, one response — ordinary RPC), **server streaming** (one request, a sequence of responses over time), **client streaming** (a sequence of requests, one final response), and **bidirectional streaming** (both sides send a sequence of messages independently, over the same long-lived call, in either order).

## 2. Why & when

Unary calls cover most service-to-service interactions, but some genuinely don't fit that one-request-one-response shape. A client watching an order's status change over time is naturally server streaming — the server pushes updates as they happen, rather than the client polling repeatedly. A client uploading a large file in chunks is naturally client streaming — many small messages, one final confirmation. A live chat or a bidirectional sensor-data exchange is naturally bidirectional streaming — both sides send whenever they have something to say, independently of each other's timing.

Choose the streaming shape that matches the real interaction pattern: unary for "ask a question, get an answer," server streaming for "subscribe to a sequence of updates," client streaming for "send a sequence of data, get one final result," and bidirectional streaming for genuinely independent, ongoing exchange in both directions. Forcing a naturally-streaming interaction into repeated unary polling wastes both latency (waiting for each poll interval) and resources (unnecessary round trips) compared to a single, appropriately-shaped streaming call.

## 3. Core concept

Each RPC shape differs in how many messages flow in which direction over the single underlying call.

```
Unary:                request ---> <--- response                (1 in, 1 out)
Server streaming:     request ---> <--- response, response, ...  (1 in, N out)
Client streaming:     request, request, ... ---> <--- response   (N in, 1 out)
Bidirectional:        request <---> response, interleaved freely  (N in, N out, either order)
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four gRPC call shapes shown as arrows: unary with one request and one response, server streaming with one request and many responses, client streaming with many requests and one response, and bidirectional with interleaved messages in both directions">
  <text x="100" y="20" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Unary</text>
  <line x1="40" y1="35" x2="160" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="160" y1="50" x2="40" y2="50" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>

  <text x="320" y="20" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Server streaming</text>
  <line x1="260" y1="35" x2="380" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="380" y1="50" x2="260" y2="50" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="380" y1="62" x2="260" y2="62" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="380" y1="74" x2="260" y2="74" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>

  <text x="530" y="20" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Client streaming</text>
  <line x1="480" y1="35" x2="600" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="480" y1="47" x2="600" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="600" y1="62" x2="480" y2="62" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>

  <text x="320" y="130" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Bidirectional streaming</text>
  <line x1="260" y1="150" x2="380" y2="150" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="380" y1="162" x2="260" y2="162" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="260" y1="174" x2="380" y2="174" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a91)"/>
  <line x1="380" y1="186" x2="260" y2="186" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a91)"/>

  <defs><marker id="a91" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L7,3.5 L0,7 z" fill="#8b949e"/></marker></defs>
</svg>

Green arrows are client-sent messages; blue arrows are server-sent messages — each shape differs only in their count and interleaving.

## 5. Runnable example

Scenario: model the three streaming shapes beyond unary using the same `StreamObserver`-style interface gRPC's Java bindings use — first server streaming (already familiar from the previous topic, extended here), then client streaming (many client messages, one aggregated server response), then bidirectional streaming (both sides interleaved).

### Level 1 — Basic

```java
// File: ServerStreaming.java -- ONE request, a SEQUENCE of responses --
// the server pushes multiple order-status updates over one call.
import java.util.*;

public class ServerStreaming {
    interface StreamObserver<T> { void onNext(T value); void onCompleted(); }

    static void subscribeToOrderUpdates(String orderId, StreamObserver<String> responseObserver) {
        for (String status : List.of("PLACED", "PACKED", "SHIPPED")) {
            responseObserver.onNext(status); // server pushes each update as it happens
        }
        responseObserver.onCompleted();
    }

    public static void main(String[] args) {
        subscribeToOrderUpdates("ORD-1", new StreamObserver<String>() {
            public void onNext(String status) { System.out.println("Update: " + status); }
            public void onCompleted() { System.out.println("Stream ended."); }
        });
    }
}
```

**How to run:** `javac ServerStreaming.java && java ServerStreaming` (JDK 17+).

Expected output:
```
Update: PLACED
Update: PACKED
Update: SHIPPED
Stream ended.
```

### Level 2 — Intermediate

```java
// File: ClientStreaming.java -- the CLIENT sends a SEQUENCE of messages
// (order line items, one at a time); the SERVER responds ONCE, after the
// client signals it's done, with an aggregated result.
import java.util.*;

public class ClientStreaming {
    interface StreamObserver<T> { void onNext(T value); void onCompleted(); }

    record LineItem(String sku, int quantity, double price) {}
    record OrderSummary(int itemCount, double total) {}

    static StreamObserver<LineItem> submitOrderItems(StreamObserver<OrderSummary> responseObserver) {
        List<LineItem> received = new ArrayList<>();
        return new StreamObserver<LineItem>() {
            public void onNext(LineItem item) {
                received.add(item); // server accumulates each client-sent item
                System.out.println("Server received item: " + item.sku());
            }
            public void onCompleted() { // client signaled it's done sending
                double total = received.stream().mapToDouble(i -> i.quantity() * i.price()).sum();
                responseObserver.onNext(new OrderSummary(received.size(), total)); // ONE final response
                responseObserver.onCompleted();
            }
        };
    }

    public static void main(String[] args) {
        StreamObserver<LineItem> clientStream = submitOrderItems(new StreamObserver<OrderSummary>() {
            public void onNext(OrderSummary summary) {
                System.out.println("Final summary: " + summary.itemCount() + " items, total=" + summary.total());
            }
            public void onCompleted() { System.out.println("Server response stream ended."); }
        });

        clientStream.onNext(new LineItem("widget", 2, 9.99));
        clientStream.onNext(new LineItem("gadget", 1, 19.99));
        clientStream.onCompleted(); // client finishes sending -- triggers the server's aggregated response
    }
}
```

**How to run:** `javac ClientStreaming.java && java ClientStreaming` (JDK 17+).

Expected output:
```
Server received item: widget
Server received item: gadget
Final summary: 2 items, total=39.97
Server response stream ended.
```

### Level 3 — Advanced

```java
// File: BidirectionalStreaming.java -- BOTH sides send a SEQUENCE of
// messages, INTERLEAVED, over the SAME call -- a live price-quote
// negotiation where the server can respond to each client message
// individually, in either order relative to further client messages.
import java.util.*;

public class BidirectionalStreaming {
    interface StreamObserver<T> { void onNext(T value); void onCompleted(); }

    record PriceQuery(String sku) {}
    record PriceQuote(String sku, double price) {}

    static Map<String, Double> prices = Map.of("widget", 9.99, "gadget", 19.99, "gizmo", 14.99);

    static StreamObserver<PriceQuery> negotiate(StreamObserver<PriceQuote> responseObserver) {
        return new StreamObserver<PriceQuery>() {
            public void onNext(PriceQuery query) { // server responds to EACH client message individually
                double price = prices.getOrDefault(query.sku(), 0.0);
                responseObserver.onNext(new PriceQuote(query.sku(), price)); // interleaved: respond immediately
            }
            public void onCompleted() { responseObserver.onCompleted(); }
        };
    }

    public static void main(String[] args) {
        StreamObserver<PriceQuery> clientStream = negotiate(new StreamObserver<PriceQuote>() {
            public void onNext(PriceQuote quote) {
                System.out.println("Received quote: " + quote.sku() + " -> $" + quote.price());
            }
            public void onCompleted() { System.out.println("Negotiation stream ended."); }
        });

        clientStream.onNext(new PriceQuery("widget")); // client sends, server responds IMMEDIATELY -- interleaved
        clientStream.onNext(new PriceQuery("gizmo"));
        clientStream.onNext(new PriceQuery("gadget"));
        clientStream.onCompleted();
    }
}
```

**How to run:** `javac BidirectionalStreaming.java && java BidirectionalStreaming` (JDK 17+).

Expected output:
```
Received quote: widget -> $9.99
Received quote: gizmo -> $14.99
Received quote: gadget -> $19.99
Negotiation stream ended.
```

## 6. Walkthrough

1. **Level 1 (server streaming)** — `subscribeToOrderUpdates` takes one `orderId` argument (the single request) and calls `responseObserver.onNext` three times in sequence, followed by `onCompleted()`. `main`'s anonymous `StreamObserver` prints each update as `onNext` is called, then the "Stream ended" line when `onCompleted` fires — one request in, a sequence of responses out, exactly matching server streaming's shape.
2. **Level 2 (client streaming)** — `submitOrderItems` returns a `StreamObserver<LineItem>` for the *client* to push messages into, rather than taking a single argument. `main` obtains this observer, then calls `onNext` on it twice (once per line item) — each call triggers the server-side `onNext` implementation, which accumulates the item into `received` and prints a confirmation. Only when `main` calls `clientStream.onCompleted()` does the server-side `onCompleted` implementation run: it computes `total` by summing `quantity * price` across all accumulated items, constructs one `OrderSummary`, and pushes it through `responseObserver.onNext` — triggering `main`'s response-side `onNext`, which prints the final summary — followed by `responseObserver.onCompleted()`, printing the closing line.
3. **Tracing the aggregation math** — `received` ends up holding `LineItem("widget", 2, 9.99)` and `LineItem("gadget", 1, 19.99)`; the stream sum computes `2 * 9.99 + 1 * 19.99 = 19.98 + 19.99 = 39.97`, matching the printed `total=39.97` — confirming the server genuinely waited for *all* client messages before computing and sending its one final response, the defining shape of client streaming.
4. **Level 3 (bidirectional streaming)** — `negotiate` also returns a `StreamObserver<PriceQuery>` for the client to send into, but unlike client streaming's `submitOrderItems`, its `onNext` implementation responds to *each individual* client message immediately, rather than waiting for `onCompleted`. `main` calls `clientStream.onNext` three times, for `"widget"`, `"gizmo"`, and `"gadget"` in that order — and each call synchronously triggers a lookup in `prices` and an immediate `responseObserver.onNext` call, printing that specific quote before the next client message is even sent.
5. **Why the printed order confirms bidirectional behavior** — the three "Received quote" lines print in the *same order* as the three client queries were sent (widget, gizmo, gadget) — because each response is generated and delivered immediately upon receiving its corresponding request, rather than being batched and delivered only after all requests finish (as client streaming would do) or all delivered up front before any request (as server streaming would do). This immediate, per-message, interleaved exchange in both directions over one ongoing call is exactly what distinguishes bidirectional streaming from the other two streaming shapes.

## 7. Gotchas & takeaways

> **Gotcha:** in a real bidirectional streaming call, the client and server run on genuinely independent threads/timing — a server implementation that assumes responses arrive in the same order requests were sent (as this simplified, synchronous simulation does) can break under real concurrent conditions, where responses to later requests might complete before responses to earlier ones. Design bidirectional streaming logic to correlate requests and responses explicitly (e.g., via an id in each message) rather than relying on ordering alone.

- Choose the RPC shape that matches the real interaction pattern: unary for simple request/response, server streaming for a subscription-like sequence of updates, client streaming for uploading many pieces before getting one result, bidirectional for genuinely independent, ongoing exchange.
- All four shapes are built on the same underlying [HTTP/2 multiplexed stream](0089-grpc-and-http-2.md) — the difference is purely in how many messages flow in which direction and when.
- Client streaming's server-side logic only produces its final response once the client signals completion (`onCompleted`) — don't confuse this with bidirectional streaming, where responses can be sent per-message, immediately.
- Forcing a naturally-streaming interaction into repeated unary polling wastes both round trips and latency compared to a properly-shaped streaming call.
- Real bidirectional streaming needs explicit request/response correlation for production robustness — don't rely on message ordering alone, since it may not hold under real network and concurrency conditions.
