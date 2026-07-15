---
card: spring-integration
gi: 34
slug: inbound-outbound-gateways
title: "Inbound/outbound gateways"
---

## 1. What it is

Where a plain channel adapter (card 0033) is strictly one-way, an inbound gateway and an outbound gateway are the two-way counterparts: an inbound gateway receives a request from an external system, sends it into the flow, waits for the flow to produce a reply, and sends that reply back out to the external caller. An outbound gateway does the mirror: it takes a message from the flow, sends a request to an external system, waits for that system's response, and feeds the response back into the flow as a reply message. Both directions preserve the request/reply round trip that a plain adapter deliberately discards.

## 2. Why & when

You reach for a gateway (inbound or outbound) specifically when the external interaction genuinely has a two-way, request/reply shape:

- **An external caller expects a response** — an HTTP client waiting for a status code and body, an RPC caller waiting for a result — an inbound gateway is what lets the flow produce that response and have it actually delivered back to the original external caller, rather than vanishing the way a plain inbound adapter's "fire and forget" input would.
- **The flow needs data back from an external system before it can proceed** — calling another microservice's REST API and needing its response body, querying a database and needing the result rows — an outbound gateway performs that call and feeds the response back into the flow as a reply message, unlike a plain outbound adapter, which only performs a one-way side effect.
- **You want the request/reply contract to be explicit in the endpoint's configuration**, rather than discovering only at runtime that a "fire and forget" adapter silently dropped a response the flow actually needed.

## 3. Core concept

Think of an inbound gateway like a customer service phone line with a live representative, as opposed to a suggestion box (an inbound adapter): the caller stays on the line, their request goes to whoever handles it internally, and the representative comes back with an actual answer before the caller hangs up — the round trip is preserved end to end. An outbound gateway is the mirror: it's you, on hold, dialing another company's support line, waiting for their answer, and bringing that answer back to whoever asked you to make the call in the first place.

```java
// Inbound gateway (e.g., backing an HTTP endpoint): receives request, waits for flow's reply, sends it back
@Bean
public IntegrationFlow httpInboundFlow() {
    return IntegrationFlows.from(Http.inboundGateway("/orders")
            .requestMapping(m -> m.methods(HttpMethod.POST)))
        .handle((Order order, headers) -> orderService.process(order)) // this RETURN VALUE becomes the HTTP response
        .get();
}

// Outbound gateway: sends a request to another system, waits for and returns its response
@Bean
public IntegrationFlow httpOutboundFlow() {
    return IntegrationFlows.from("outboundRequests")
        .handle(Http.outboundGateway("https://payments.example.com/charge")
            .expectedResponseType(ChargeResult.class)) // WAITS for the external response
        .channel("chargeResults")
        .get();
}
```

Both gateways preserve a two-way exchange across the external boundary — one where the external caller is the initiator (inbound), one where the flow itself is the initiator (outbound).

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Inbound gateway: external caller's request flows in and a reply flows back out to them. Outbound gateway: the flow's request goes to an external system and its response flows back into the flow.">
  <text x="150" y="20" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Inbound gateway</text>
  <rect x="20" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">external caller</text>

  <line x1="130" y1="47" x2="190" y2="47" stroke="#6db33f" stroke-width="2" marker-end="url(#ig1)"/>
  <line x1="190" y1="65" x2="130" y2="65" stroke="#79c0ff" stroke-width="2" marker-end="url(#ig2)"/>

  <rect x="200" y="35" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="255" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow</text>

  <text x="490" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Outbound gateway</text>
  <rect x="360" y="135" width="110" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="415" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow</text>

  <line x1="470" y1="147" x2="530" y2="147" stroke="#6db33f" stroke-width="2" marker-end="url(#ig1)"/>
  <line x1="530" y1="165" x2="470" y2="165" stroke="#79c0ff" stroke-width="2" marker-end="url(#ig2)"/>

  <rect x="540" y="135" width="90" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="585" y="159" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">external API</text>

  <defs>
    <marker id="ig1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ig2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Both directions preserve the full round trip; who initiates the request (external caller vs. the flow itself) is what distinguishes inbound from outbound.

## 5. Runnable example

The scenario: an order-submission endpoint that itself needs to call a payment service, starting with a basic inbound gateway simulation, then an outbound gateway calling an external service, and finally both composed so an inbound request triggers an outbound call before replying.

### Level 1 — Basic

```java
// BasicInboundGatewayDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicInboundGatewayDemo {
    record OrderRequest(String id) {}
    record OrderResponse(String id, String status) {}

    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();

        // the FLOW behind the inbound gateway: processes the request, produces a reply
        Thread flow = new Thread(() -> {
            Message<?> request = requestChannel.receive();
            OrderRequest order = (OrderRequest) request.getPayload();
            var replyChannel = request.getHeaders().getReplyChannel();
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new OrderResponse(order.id(), "ACCEPTED")).build());
        });
        flow.start();

        // the INBOUND GATEWAY: receives an "external" request, waits for the flow's reply, hands it back
        MessagingTemplate inboundGateway = new MessagingTemplate();
        inboundGateway.setDefaultChannel(requestChannel);

        System.out.println("External caller sending request...");
        OrderResponse response = (OrderResponse) inboundGateway.sendAndReceive(
            MessageBuilder.withPayload(new OrderRequest("ORD-1")).build()).getPayload();
        System.out.println("External caller received reply: " + response);
    }
}
```

How to run: `java BasicInboundGatewayDemo.java`. Expected output: `External caller sending request...` then `External caller received reply: OrderResponse[id=ORD-1, status=ACCEPTED]` — an external-style caller sent a request and genuinely received a reply back, the full round trip an inbound gateway (unlike a plain inbound adapter) preserves.

### Level 2 — Intermediate

An outbound gateway is the flow initiating a request to an external system and waiting for its response — modeled here with a simulated external payment service that takes some time to respond, blocking the outbound gateway's caller until the response arrives.

```java
// BasicOutboundGatewayDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicOutboundGatewayDemo {
    record ChargeRequest(String orderId, double amount) {}
    record ChargeResult(String orderId, boolean approved) {}

    public static void main(String[] args) {
        QueueChannel externalPaymentServiceChannel = new QueueChannel();

        // stands in for an EXTERNAL payment service (outside our own flow entirely)
        Thread externalPaymentService = new Thread(() -> {
            Message<?> request = externalPaymentServiceChannel.receive();
            ChargeRequest charge = (ChargeRequest) request.getPayload();
            try { Thread.sleep(200); } catch (InterruptedException ignored) {} // simulated network latency
            var replyChannel = request.getHeaders().getReplyChannel();
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new ChargeResult(charge.orderId(), true)).build());
        });
        externalPaymentService.start();

        // the OUTBOUND GATEWAY: the flow's own code, calling OUT to the external system and awaiting its response
        MessagingTemplate outboundGateway = new MessagingTemplate();
        outboundGateway.setDefaultChannel(externalPaymentServiceChannel);
        outboundGateway.setReceiveTimeout(2000);

        System.out.println("Flow calling external payment service...");
        ChargeResult result = (ChargeResult) outboundGateway.sendAndReceive(
            MessageBuilder.withPayload(new ChargeRequest("ORD-1", 199.99)).build()).getPayload();
        System.out.println("Flow received external response: " + result);
    }
}
```

How to run: `java BasicOutboundGatewayDemo.java`. Expected output: `Flow calling external payment service...` immediately, then (after ~200ms, simulating real network latency) `Flow received external response: ChargeResult[orderId=ORD-1, approved=true]` — the flow's own code blocked waiting for the external system's genuine response, exactly the round trip a plain outbound adapter would never provide.

### Level 3 — Advanced

Composing both: an inbound gateway receives an external order-submission request, and *before* replying to that external caller, the flow itself makes an outbound gateway call to a payment service — the external caller's reply only goes out once the internal outbound round trip has completed, chaining two independent request/reply exchanges together.

```java
// ComposedInboundOutboundGatewayDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class ComposedInboundOutboundGatewayDemo {
    record OrderRequest(String id, double amount) {}
    record ChargeRequest(String orderId, double amount) {}
    record ChargeResult(String orderId, boolean approved) {}
    record OrderResponse(String id, String status) {}

    public static void main(String[] args) {
        QueueChannel inboundRequestChannel = new QueueChannel();
        QueueChannel paymentServiceChannel = new QueueChannel();

        // external payment service (called via OUTBOUND gateway, from within our flow)
        Thread paymentService = new Thread(() -> {
            Message<?> req = paymentServiceChannel.receive();
            ChargeRequest charge = (ChargeRequest) req.getPayload();
            var replyChannel = req.getHeaders().getReplyChannel();
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new ChargeResult(charge.orderId(), true)).build());
        });
        paymentService.start();

        MessagingTemplate outboundGateway = new MessagingTemplate();
        outboundGateway.setDefaultChannel(paymentServiceChannel);

        // our FLOW: receives via inbound gateway, calls OUT via outbound gateway, THEN replies to the original caller
        Thread flow = new Thread(() -> {
            Message<?> req = inboundRequestChannel.receive();
            OrderRequest order = (OrderRequest) req.getPayload();

            ChargeResult chargeResult = (ChargeResult) outboundGateway.sendAndReceive(
                MessageBuilder.withPayload(new ChargeRequest(order.id(), order.amount())).build()).getPayload();

            var replyChannel = req.getHeaders().getReplyChannel();
            String status = chargeResult.approved() ? "CONFIRMED" : "PAYMENT_FAILED";
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new OrderResponse(order.id(), status)).build());
        });
        flow.start();

        MessagingTemplate inboundGateway = new MessagingTemplate();
        inboundGateway.setDefaultChannel(inboundRequestChannel);

        OrderResponse response = (OrderResponse) inboundGateway.sendAndReceive(
            MessageBuilder.withPayload(new OrderRequest("ORD-1", 199.99)).build()).getPayload();
        System.out.println("External caller finally received: " + response);
    }
}
```

How to run: `java ComposedInboundOutboundGatewayDemo.java`. Expected output: `External caller finally received: OrderResponse[id=ORD-1, status=CONFIRMED]` — the external caller's `sendAndReceive` call didn't unblock until the flow had completed its own nested outbound round trip to the payment service and used that result to decide the final status.

## 6. Walkthrough

Tracing `ComposedInboundOutboundGatewayDemo` in execution order:

1. The main thread (standing in for an external caller) calls `inboundGateway.sendAndReceive(...)`, which builds a request message with a temporary reply channel and sends it to `inboundRequestChannel`, then blocks waiting for a reply.
2. The `flow` thread's `inboundRequestChannel.receive()` unblocks, receiving the order request — this is the inbound gateway's request arriving at the flow.
3. Instead of replying immediately, the flow itself now acts as a *caller*: it invokes `outboundGateway.sendAndReceive(...)` with a `ChargeRequest`, which builds its own separate request message with its own separate temporary reply channel, sent to `paymentServiceChannel` — the flow is now blocked, waiting on this second, independent round trip.
4. The `paymentService` thread's `paymentServiceChannel.receive()` unblocks, processes the charge request, and sends a `ChargeResult` back to the reply channel the outbound gateway attached.
5. The flow's blocked `outboundGateway.sendAndReceive(...)` call unblocks with the `ChargeResult`; the flow uses `chargeResult.approved()` to decide the final status (`"CONFIRMED"`), then sends an `OrderResponse` to the *original* reply channel from step 1 — the one the external caller is actually waiting on.
6. The main thread's original `inboundGateway.sendAndReceive(...)` call (blocked since step 1) finally unblocks with that `OrderResponse`, and the external caller's reply is printed — the entire chain took two nested request/reply round trips before the outermost one could complete.

```
external caller: sendAndReceive(OrderRequest) [BLOCKS on inboundRequestChannel's reply]
  flow: receives OrderRequest
  flow: sendAndReceive(ChargeRequest) [BLOCKS on paymentServiceChannel's reply]
    paymentService: receives ChargeRequest, replies with ChargeResult
  flow: unblocks with ChargeResult, decides status
  flow: replies to ORIGINAL external caller's reply channel with OrderResponse
external caller: unblocks with OrderResponse
```

## 7. Gotchas & takeaways

> Chaining gateways (an inbound gateway's flow making an outbound gateway call before replying) means the *external* caller's wait time now includes the *internal* outbound call's full latency, plus both gateways' own overhead — a slow or hanging external payment service directly makes the original external caller wait longer, or time out. Always set a receive timeout on every gateway in a chain, not just the outermost one, so a stuck internal call fails fast rather than silently propagating its hang all the way out to the original external caller.

- An inbound gateway receives an external request, waits for the flow's reply, and delivers that reply back to the external caller — the two-way counterpart of a plain inbound adapter (card 0033).
- An outbound gateway is the flow itself initiating a request to an external system and waiting for that system's response before continuing — the two-way counterpart of a plain outbound adapter.
- Use a gateway (either direction) whenever the external interaction genuinely has a request/reply shape; a plain adapter would silently discard the response side of that exchange.
- Gateways can be chained: an inbound gateway's own flow can make outbound gateway calls before producing its own reply, composing multiple independent request/reply round trips into one overall exchange.
- Every gateway in a chain needs its own explicit timeout — a hang anywhere in a chained sequence of gateways propagates its latency (or its indefinite block) all the way out to whoever is waiting at the very front of the chain.
