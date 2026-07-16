---
card: spring-amqp
gi: 19
slug: rpc-pattern-sendandreceive
title: "RPC pattern (sendAndReceive)"
---

## 1. What it is

`RabbitTemplate.sendAndReceive` (and its object-converting counterpart `convertSendAndReceive`, already introduced briefly in card 0007) implements a full request/reply RPC pattern over AMQP: the template publishes a request message with a `replyTo` property set and a correlation ID attached, then blocks the calling thread until a reply carrying that same correlation ID arrives on the specified reply destination, or until a configured timeout elapses. This card looks at the pattern in more depth — what actually has to happen on the responding side for this to work, and the trade-offs of layering synchronous RPC semantics onto an inherently asynchronous protocol.

## 2. Why & when

You reach for the RPC pattern specifically when a caller genuinely cannot proceed without a response, and a synchronous call is the natural fit for the interaction:

- **A calculation or lookup needs to happen in a separate service, and the caller has no useful work to do until the answer arrives** — a price quote calculation, an inventory check — these are naturally synchronous interactions even though the underlying transport is a message broker rather than a direct HTTP call.
- **The responding side is decoupled from the caller by design (different team, different deployment, different scaling profile), but the interaction itself is still fundamentally synchronous** — using AMQP as the transport rather than HTTP might be chosen for its existing infrastructure, but the request/reply *shape* of the interaction doesn't change based on the transport.
- **Avoid this pattern when a response isn't actually needed before the caller can proceed** — for pure fire-and-forget events (an order was created, a status changed), a plain `convertAndSend` with no expectation of a reply is simpler, faster, and doesn't tie up a thread waiting.

## 3. Core concept

Think of `sendAndReceive` like making a phone call and staying on hold rather than sending a message and going about your day — you (the caller) can't do anything else productive until the person on the other end (the responder) picks up and gives you an answer, and you'll eventually hang up in frustration (timeout) if no one answers within a reasonable time. This is meaningfully different from dropping a note in someone's mailbox and continuing with your day regardless of when (or whether) they eventually reply — that's what plain, non-blocking publishing looks like instead.

```java
// Caller side: blocks until a reply arrives or the timeout elapses.
public PriceQuote getQuote(QuoteRequest request) {
    return (PriceQuote) rabbitTemplate.convertSendAndReceive(
        "pricing.exchange", "quote.request", request);
}

// Responder side: a listener that returns a value is automatically treated as the reply.
@RabbitListener(queues = "quoteRequestQueue")
public PriceQuote handleQuoteRequest(QuoteRequest request) {
    double price = pricingEngine.calculate(request);
    return new PriceQuote(request.getItemId(), price); // this return value becomes the RPC reply
}
```

The responder's `@RabbitListener` method simply returns a value; Spring AMQP's listener infrastructure handles publishing that return value back to the caller's `replyTo` destination with the matching correlation ID automatically.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="sendAndReceive publishes a request with replyTo and a correlation ID, blocks the calling thread, and a responder's listener method's return value is automatically published back to that reply destination with the matching correlation ID" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Caller (blocks)</text>

  <line x1="200" y1="42" x2="270" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a18)"/>
  <text x="235" y="32" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">request + replyTo + corrId</text>

  <rect x="270" y="20" width="180" height="45" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">@RabbitListener</text>

  <line x1="270" y1="60" x2="200" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a18)"/>
  <text x="235" y="90" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">return value auto-published</text>
  <text x="235" y="105" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">to replyTo, with corrId</text>

  <rect x="20" y="105" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="130" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">reply arrives -&gt; unblocks</text>
</svg>

The listener's plain return value becomes the RPC reply automatically — no manual reply-publishing code needed.

## 5. Runnable example

The scenario: a price-quote RPC where the caller blocks for the responder's answer, simulated with a `CompletableFuture` standing in for the blocking request/reply round trip (no real RabbitMQ broker needed to demonstrate the synchronous-call-over-async-transport pattern), starting with a basic successful round trip, then adding a timeout for when no reply arrives in time, then adding a scenario with a responder that itself needs to call a slow downstream dependency, showing how that latency directly becomes the caller's own wait time.

### Level 1 — Basic

```java
// RpcPatternDemo.java
import java.util.concurrent.*;

public class RpcPatternDemo {
    record QuoteRequest(String itemId, int quantity) {}
    record PriceQuote(String itemId, double totalPrice) {}

    // Stand-in for the responder: a listener method whose return value becomes the reply.
    static PriceQuote handleQuoteRequest(QuoteRequest request) {
        return new PriceQuote(request.itemId(), request.quantity() * 9.99);
    }

    // Stand-in for RabbitTemplate.convertSendAndReceive: blocks until the "reply" is available.
    static PriceQuote sendAndReceive(QuoteRequest request) throws Exception {
        CompletableFuture<PriceQuote> future = CompletableFuture.supplyAsync(() -> handleQuoteRequest(request));
        return future.get(1, TimeUnit.SECONDS);
    }

    public static void main(String[] args) throws Exception {
        PriceQuote quote = sendAndReceive(new QuoteRequest("WIDGET-1", 3));
        System.out.println("Received quote: " + quote);
    }
}
```

How to run: `java RpcPatternDemo.java`. Expected output: `Received quote: PriceQuote[itemId=WIDGET-1, totalPrice=29.97]` — the caller blocks briefly and receives the responder's return value as its RPC reply.

### Level 2 — Intermediate

```java
// RpcPatternDemo.java
import java.util.concurrent.*;

public class RpcPatternDemo {
    record QuoteRequest(String itemId, int quantity) {}
    record PriceQuote(String itemId, double totalPrice) {}

    static PriceQuote handleQuoteRequest(QuoteRequest request, long simulatedDelayMillis) throws InterruptedException {
        Thread.sleep(simulatedDelayMillis);
        return new PriceQuote(request.itemId(), request.quantity() * 9.99);
    }

    // Real-world concern: the responder can be slow, unreachable, or the reply lost -- the
    // caller must not block forever; a configured timeout is essential for RPC-style calls.
    static PriceQuote sendAndReceiveWithTimeout(QuoteRequest request, long responderDelayMillis, long timeoutMillis)
            throws Exception {
        CompletableFuture<PriceQuote> future = CompletableFuture.supplyAsync(() -> {
            try {
                return handleQuoteRequest(request, responderDelayMillis);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });
        try {
            return future.get(timeoutMillis, TimeUnit.MILLISECONDS);
        } catch (TimeoutException ex) {
            System.out.println("RPC call timed out after " + timeoutMillis + "ms, no reply received");
            return null;
        }
    }

    public static void main(String[] args) throws Exception {
        PriceQuote fastQuote = sendAndReceiveWithTimeout(new QuoteRequest("WIDGET-1", 3), 100, 500);
        System.out.println("Fast responder result: " + fastQuote);

        PriceQuote slowQuote = sendAndReceiveWithTimeout(new QuoteRequest("WIDGET-2", 1), 800, 300);
        System.out.println("Slow responder result: " + slowQuote);
    }
}
```

How to run: `java RpcPatternDemo.java`. Expected output: the fast responder returns its quote well within the timeout, printing `Fast responder result: PriceQuote[...]`; the slow responder (800ms delay against a 300ms timeout) triggers the timeout message and `Slow responder result: null` — the caller correctly giving up rather than waiting indefinitely for a reply that's taking too long.

### Level 3 — Advanced

```java
// RpcPatternDemo.java
import java.util.concurrent.*;

public class RpcPatternDemo {
    record QuoteRequest(String itemId, int quantity) {}
    record PriceQuote(String itemId, double totalPrice) {}

    // Production concern: a responder's own latency (calling a slow downstream inventory or
    // tax-calculation service) becomes DIRECTLY the caller's wait time in an RPC pattern --
    // there is no way to decouple the two once synchronous request/reply is chosen.
    static PriceQuote handleQuoteRequest(QuoteRequest request, long downstreamCallDelayMillis) throws InterruptedException {
        System.out.println("  Responder calling downstream pricing engine (will take " + downstreamCallDelayMillis + "ms)...");
        Thread.sleep(downstreamCallDelayMillis);
        return new PriceQuote(request.itemId(), request.quantity() * 9.99);
    }

    static PriceQuote sendAndReceiveWithTimeout(QuoteRequest request, long downstreamDelayMillis, long timeoutMillis)
            throws Exception {
        long start = System.currentTimeMillis();
        CompletableFuture<PriceQuote> future = CompletableFuture.supplyAsync(() -> {
            try {
                return handleQuoteRequest(request, downstreamDelayMillis);
            } catch (InterruptedException e) {
                throw new RuntimeException(e);
            }
        });
        try {
            PriceQuote result = future.get(timeoutMillis, TimeUnit.MILLISECONDS);
            System.out.println("Caller waited " + (System.currentTimeMillis() - start) + "ms for the reply");
            return result;
        } catch (TimeoutException ex) {
            System.out.println("Caller gave up after " + timeoutMillis + "ms timeout");
            return null;
        }
    }

    public static void main(String[] args) throws Exception {
        // If the responder's downstream dependency (a tax/inventory service) is itself slow,
        // that latency is transmitted directly to the RPC caller -- no amount of caller-side
        // configuration changes that fundamental coupling, only the timeout used to bound it.
        sendAndReceiveWithTimeout(new QuoteRequest("WIDGET-1", 3), 250, 1000);
    }
}
```

How to run: `java RpcPatternDemo.java`. Expected output: `Responder calling downstream pricing engine (will take 250ms)...` followed by `Caller waited ~250ms for the reply` — demonstrating that the responder's own internal latency (its call to a further downstream dependency) is transmitted directly and unavoidably to the caller's wait time, since the entire point of the RPC pattern is that the caller blocks until the full round trip, including whatever the responder itself has to do, completes.

## 6. Walkthrough

Trace a full RPC round trip from caller to responder and back.

1. **Request published with reply metadata**: `convertSendAndReceive` publishes the request message with two crucial pieces of metadata attached: a `replyTo` property (naming the destination the reply should go to) and a correlation ID (uniquely identifying this specific request).
2. **Caller blocks**: the calling thread pauses, waiting for a reply message matching this correlation ID to arrive on the `replyTo` destination, up to the configured timeout.
3. **Responder receives the request**: a `@RabbitListener`-annotated method (or an equivalent listener) on the responding side receives the request message as it would any other message, with no special code needed to recognize it as an RPC request specifically.
4. **Responder computes and returns**: the listener method performs whatever work is needed (in the example, calling a pricing engine, possibly itself involving a call to a further downstream service) and returns a plain Java object — Spring AMQP's listener infrastructure recognizes this non-void return value and automatically publishes it as a reply to the `replyTo` destination named in the incoming request, tagged with the same correlation ID.
5. **Reply arrives, caller unblocks**: `RabbitTemplate`'s internal reply-listening mechanism recognizes the incoming reply's correlation ID, matches it to the waiting caller, and returns the deserialized reply object from the blocked `convertSendAndReceive` call.
6. **Timeout as the escape hatch**: if no reply arrives within the configured timeout — because the responder is down, overloaded, or the reply itself was lost — the call returns (typically `null`, or throws, depending on configuration) rather than blocking the caller's thread indefinitely.

```
caller: convertSendAndReceive(request)
  -> publish request [replyTo=tempQueue, correlationId=corr-X]
    -> caller BLOCKS, waiting on tempQueue for corr-X
      -> [responder] @RabbitListener receives request
        -> computes result (possibly calling further downstream services -- their latency adds directly here)
          -> return value auto-published to replyTo, tagged corr-X
            -> caller's wait matches corr-X -> unblocks, returns result
               (or: timeout elapses first -> caller gives up, returns null/throws)
```

## 7. Gotchas & takeaways

> **Gotcha:** because the RPC pattern's caller blocks for the full round trip, any latency anywhere in the responder's processing chain — including calls the responder itself makes to further downstream services — is transmitted directly and unavoidably to the caller's wait time; there is no way to "speed up" this coupling from the caller's side beyond configuring an appropriate timeout, since the fundamental trade-off of choosing synchronous RPC is accepting the full chain's latency as your own.

- Reach for `sendAndReceive`/`convertSendAndReceive` specifically when the interaction is genuinely synchronous in nature — the caller has no useful work to do until the answer arrives — not as a default way to communicate between services over AMQP.
- A responding `@RabbitListener` method's plain return value becoming the automatic RPC reply is a significant convenience — no manual `replyTo`/correlation-ID handling is needed on the responder's side at all, Spring AMQP's listener infrastructure manages the entire reply mechanism transparently.
- Always configure a sensible timeout on the caller's side — an RPC call with no timeout (or an unreasonably long one) risks tying up calling threads indefinitely if the responder becomes unavailable or overloaded.
- For high-throughput RPC scenarios, direct reply-to (card 0020) avoids the overhead of creating a dedicated temporary reply queue per request, making it the more efficient mechanism underlying `sendAndReceive` in modern Spring AMQP versions by default.
