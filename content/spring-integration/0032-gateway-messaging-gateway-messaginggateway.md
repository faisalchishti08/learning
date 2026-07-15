---
card: spring-integration
gi: 32
slug: gateway-messaging-gateway-messaginggateway
title: "Gateway (messaging gateway, @MessagingGateway)"
---

## 1. What it is

A messaging gateway (`@MessagingGateway`) is an interface-based entry point into a message flow: you declare a plain Java interface with ordinary method signatures, and Spring Integration generates a runtime implementation that translates each method call into a message send (and, for non-void methods, a `sendAndReceive`-style exchange, using the same mechanics `MessagingTemplate`, card 0016, wraps manually). Calling code never touches `Message`, `MessageChannel`, or any Spring Integration type at all — it just calls a method on an interface, exactly like calling any other service.

## 2. Why & when

You reach for a messaging gateway specifically when you want the *entry point* into a flow to look like a completely ordinary method call, with zero messaging-aware code at the call site:

- **Application code (a `@Controller`, another service) needs to trigger a flow without depending on Spring Integration at all** — a `@MessagingGateway` interface is the cleanest possible seam: the caller sees `orderGateway.submit(order)`, nothing about channels, messages, or headers leaks into the caller's code.
- **You want the flow's entry contract to be a strongly-typed interface** rather than "send an arbitrarily-shaped payload to a named channel string," catching type mismatches at compile time instead of at runtime.
- **You're testing calling code in isolation** — a mocked or stubbed gateway interface is trivial to substitute in unit tests, exactly like mocking any other injected service dependency, with no need to spin up real channels for a caller-side test.

## 3. Core concept

Think of a messaging gateway like a hotel's front desk: a guest (calling code) walks up and asks for something in plain language ("I'd like a wake-up call at 7am") — they never see the hotel's internal phone switchboard, routing logic, or staff communication system that actually makes the wake-up call happen. The front desk (the gateway) translates the guest's plain request into whatever internal messaging the hotel actually uses, and later translates any internal response back into plain language for the guest.

```java
@MessagingGateway
public interface OrderGateway {
    @Gateway(requestChannel = "orderRequests", replyChannel = "orderReplies")
    OrderConfirmation submit(Order order);
}

// calling code, anywhere in the application:
@Autowired OrderGateway orderGateway;
OrderConfirmation confirmation = orderGateway.submit(new Order("ORD-1", 199.99));
// this looks EXACTLY like calling any plain service method — no Message, no MessageChannel in sight
```

Under the hood, calling `submit(order)` builds a `Message<Order>`, sends it to `orderRequests`, blocks for a correlated reply on `orderReplies` (the same request/reply mechanics as `MessagingTemplate.sendAndReceive`, card 0016), and unwraps the reply's payload back into a plain `OrderConfirmation` — none of which the caller's code expresses directly.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling code invokes a plain interface method; the gateway translates it into a message send and reply, hiding all messaging types from the caller">
  <rect x="20" y="60" width="130" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">calling code</text>
  <text x="85" y="100" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">plain method call</text>

  <line x1="150" y1="85" x2="210" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#gw1)"/>

  <rect x="220" y="45" width="180" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="70" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@MessagingGateway</text>
  <text x="310" y="87" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">builds Message, sends,</text>
  <text x="310" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">waits for reply, unwraps</text>

  <line x1="400" y1="70" x2="460" y2="70" stroke="#79c0ff" stroke-width="2" marker-end="url(#gw2)"/>
  <text x="430" y="58" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">request</text>

  <line x1="460" y1="105" x2="400" y2="105" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3,2" marker-end="url(#gw3)"/>
  <text x="430" y="120" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">reply</text>

  <rect x="470" y="55" width="130" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">flow (channels,</text>
  <text x="535" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">endpoints)</text>

  <defs>
    <marker id="gw1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="gw2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="gw3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The gateway is the entire messaging boundary — everything to its left is plain Java; everything to its right is Spring Integration's world.

## 5. Runnable example

The scenario: an order-submission entry point for application code, starting with a manually-simulated gateway showing exactly what it does internally, then a void "fire and forget" gateway variant, and finally a gateway used from what stands in for a REST controller, fully decoupled from the flow's implementation.

### Level 1 — Basic

```java
// BasicGatewayConceptDemo.java
// Simulates what a generated @MessagingGateway proxy does internally, since a full annotation-driven
// proxy requires a Spring ApplicationContext; the logic shown here is exactly what gets generated.
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class BasicGatewayConceptDemo {
    record Order(String id, double amount) {}
    record OrderConfirmation(String orderId, String status) {}

    // this class IS the gateway: plain method in, plain method out, no messaging types visible to CALLERS
    static class OrderGateway {
        private final MessagingTemplate template;
        OrderGateway(MessagingTemplate template) { this.template = template; }

        OrderConfirmation submit(Order order) { // <- this is the plain interface method a caller sees
            OrderConfirmation confirmation =
                (OrderConfirmation) template.convertSendAndReceive(order, OrderConfirmation.class);
            return confirmation;
        }
    }

    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();

        Thread flowProcessing = new Thread(() -> { // stands in for the actual flow behind the gateway
            Message<?> request = requestChannel.receive();
            Order order = (Order) request.getPayload();
            var replyChannel = request.getHeaders().getReplyChannel();
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new OrderConfirmation(order.id(), "CONFIRMED")).build());
        });
        flowProcessing.start();

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(requestChannel);
        OrderGateway orderGateway = new OrderGateway(template);

        // calling code — completely plain, no Message/MessageChannel anywhere:
        OrderConfirmation result = orderGateway.submit(new Order("ORD-1", 199.99));
        System.out.println("Caller received: " + result);
    }
}
```

How to run: `java BasicGatewayConceptDemo.java`. Expected output: `Caller received: OrderConfirmation[orderId=ORD-1, status=CONFIRMED]` — the calling code at the bottom of `main` never referenced a `Message` or `MessageChannel`; only `OrderGateway`'s internals did.

### Level 2 — Intermediate

A gateway method can also be `void`, representing "fire and forget" — the method returns as soon as the message is sent, with no reply expected at all, useful for notifications or commands where the caller doesn't need (or want to wait for) a response.

```java
// FireAndForgetGatewayDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;

public class FireAndForgetGatewayDemo {
    record AuditEvent(String action, String details) {}

    static class AuditGateway {
        private final MessagingTemplate template;
        AuditGateway(MessagingTemplate template) { this.template = template; }

        void record(AuditEvent event) { // void return -> fire and forget, no reply expected
            template.convertAndSend(event);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        QueueChannel auditChannel = new QueueChannel();

        Thread auditProcessor = new Thread(() -> {
            while (true) {
                Message<?> m = auditChannel.receive();
                if (m == null) continue;
                System.out.println("Audit log processed asynchronously: " + m.getPayload());
            }
        });
        auditProcessor.setDaemon(true);
        auditProcessor.start();

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(auditChannel);
        AuditGateway auditGateway = new AuditGateway(template);

        System.out.println("Calling record()...");
        auditGateway.record(new AuditEvent("ORDER_SUBMITTED", "ORD-1"));
        System.out.println("record() returned IMMEDIATELY — caller never waited for processing");

        Thread.sleep(100); // let the async processor catch up before the program exits
    }
}
```

How to run: `java FireAndForgetGatewayDemo.java`. Expected output: `Calling record()...`, `record() returned IMMEDIATELY...`, then `Audit log processed asynchronously: AuditEvent[...]` — the caller's method call returned before (or regardless of when) the actual processing happened, exactly the "fire and forget" contract a `void` gateway method signature implies.

### Level 3 — Advanced

Using the gateway from what stands in for a REST controller shows full decoupling: the controller code depends only on the plain `OrderGateway` interface/class, with zero awareness of channels, and the underlying flow implementation could be swapped entirely (a different channel type, an added transformer, a completely different transport) without the controller code changing at all.

```java
// ControllerUsingGatewayDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.integration.core.MessagingTemplate;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

public class ControllerUsingGatewayDemo {
    record OrderRequest(String customerId, double amount) {}
    record OrderConfirmation(String orderId, String status) {}

    static class OrderGateway {
        private final MessagingTemplate template;
        OrderGateway(MessagingTemplate template) { this.template = template; }
        OrderConfirmation submit(OrderRequest request) {
            return (OrderConfirmation) template.convertSendAndReceive(request, OrderConfirmation.class);
        }
    }

    // stands in for a @RestController — depends ONLY on OrderGateway, nothing messaging-specific
    static class OrderController {
        private final OrderGateway gateway;
        OrderController(OrderGateway gateway) { this.gateway = gateway; }
        String handlePost(OrderRequest request) { // stands in for a @PostMapping handler
            OrderConfirmation confirmation = gateway.submit(request);
            return "HTTP 201 Created: " + confirmation;
        }
    }

    public static void main(String[] args) {
        QueueChannel requestChannel = new QueueChannel();
        Thread flow = new Thread(() -> {
            Message<?> req = requestChannel.receive();
            OrderRequest r = (OrderRequest) req.getPayload();
            var replyChannel = req.getHeaders().getReplyChannel();
            ((org.springframework.messaging.MessageChannel) replyChannel).send(
                MessageBuilder.withPayload(new OrderConfirmation("ORD-" + r.customerId(), "CONFIRMED")).build());
        });
        flow.start();

        MessagingTemplate template = new MessagingTemplate();
        template.setDefaultChannel(requestChannel);
        OrderController controller = new OrderController(new OrderGateway(template));

        String response = controller.handlePost(new OrderRequest("CUST-42", 199.99));
        System.out.println(response);
    }
}
```

How to run: `java ControllerUsingGatewayDemo.java`. Expected output: `HTTP 201 Created: OrderConfirmation[orderId=ORD-CUST-42, status=CONFIRMED]` — the controller's `handlePost` method reads like any ordinary web handler calling a service; nothing about `Message`, channels, or Spring Integration is visible in `OrderController`'s code at all.

## 6. Walkthrough

Tracing `ControllerUsingGatewayDemo` in execution order:

1. `controller.handlePost(new OrderRequest("CUST-42", 199.99))` is called, exactly as a real `@PostMapping` handler would be invoked by Spring MVC for an incoming HTTP request.
2. Inside `handlePost`, `gateway.submit(request)` is called — from the controller's perspective, this is just another method call on a collaborator object; there's no messaging vocabulary anywhere in this line.
3. Inside `OrderGateway.submit`, `template.convertSendAndReceive(request, OrderConfirmation.class)` is invoked — this is where the plain `OrderRequest` object actually gets wrapped into a `Message`, given a temporary reply channel, and sent (exactly as detailed in `MessagingTemplate`'s walkthrough, card 0016).
4. The background `flow` thread's `requestChannel.receive()` unblocks, receives the message, extracts the `OrderRequest` payload, builds an `OrderConfirmation`, and sends it to the reply channel the gateway automatically attached.
5. Back inside `convertSendAndReceive`, the reply arrives, is unwrapped from its `Message` envelope back into a plain `OrderConfirmation` object, and is returned from `submit`.
6. `handlePost` receives that plain `OrderConfirmation`, formats a response string, and returns it — from HTTP request in to HTTP-response-shaped string out, the entire journey through the messaging system happened invisibly, behind the `OrderGateway` interface's single method call.

```
controller.handlePost(request)
  -> gateway.submit(request)
       -> template.convertSendAndReceive(request)
            -> Message built, sent, replyChannel attached
            -> [flow processes, replies]
            -> reply unwrapped back to OrderConfirmation
       -> returns OrderConfirmation
  -> controller formats "HTTP 201 Created: ..."
```

## 7. Gotchas & takeaways

> A non-void gateway method backed by a `requestChannel`/`replyChannel` exchange inherits the same untimed-block hazard as `MessagingTemplate.sendAndReceive` (card 0016) — if nothing ever replies, the caller's method call hangs indefinitely unless a timeout is explicitly configured on the gateway. Because a gateway makes the messaging machinery invisible to the caller, it's especially easy to forget this risk exists at all; always configure a sensible reply timeout on any gateway method that isn't intentionally fire-and-forget.

- A `@MessagingGateway` interface is a plain-method entry point into a message flow — calling code invokes ordinary methods, with the framework generating an implementation that handles message building, sending, and (for non-void methods) reply correlation entirely internally.
- Use it to keep application code (controllers, other services) completely decoupled from messaging types, and to give a flow's entry point a strongly-typed, compile-time-checked contract.
- A `void` gateway method is fire-and-forget: it returns as soon as the message is sent, with no reply wait at all.
- A non-void gateway method blocks (like `MessagingTemplate.sendAndReceive`) waiting for a correlated reply — always configure a timeout to avoid an indefinite hang if nothing ever replies.
- Because callers depend only on the gateway's plain interface, the flow implementation behind it can be changed freely (different channels, added steps, a different transport) without any change to calling code — the gateway is the stable seam that makes that decoupling possible.
