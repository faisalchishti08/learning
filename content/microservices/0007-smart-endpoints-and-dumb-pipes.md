---
card: microservices
gi: 7
slug: smart-endpoints-and-dumb-pipes
title: Smart endpoints and dumb pipes
---

## 1. What it is

**Smart endpoints and dumb pipes** is the Lewis & Fowler characteristic that says business logic — routing decisions, transformation, validation — should live inside the services (the **endpoints**) that send and receive messages, not inside the messaging infrastructure (the **pipe**) that carries those messages between them. The pipe's only job is to move bytes from one place to another as reliably as the situation requires; it shouldn't know or care what those bytes mean.

This is a direct reaction against older **Enterprise Service Bus (ESB)** architectures, where a central piece of middleware performed message routing, format transformation, and even business rule orchestration. Microservices push that intelligence back out to the edges: to the services themselves.

## 2. Why & when

Centralizing business logic in the pipe (a smart ESB) seems efficient at first — one place to change a routing rule instead of touching every service. In practice it creates a different bottleneck: the ESB becomes a shared piece of infrastructure that every team's feature work has to go through, owned by a specialized team that must understand every service's business rules, and it becomes a single point where a change for one service's needs can break routing for every other service sharing that bus.

Choose smart endpoints and dumb pipes as your default: give each service its own logic for interpreting, validating, and reacting to messages, and use the simplest transport that reliably moves bytes — plain HTTP or a basic message queue — without embedding business rules in that transport layer. Reserve any transformation or orchestration logic for the endpoints, even if that means the same validation rule is implemented independently in more than one place; that duplication is a smaller cost than a central bottleneck every team must coordinate through.

## 3. Core concept

The test is: when a business rule changes, what has to be edited?

- **Smart pipe:** a central mediator/bus class contains an `if` statement deciding how to route or transform each message type. Adding a new business rule means editing that shared, central class.
- **Smart endpoints, dumb pipe:** the pipe (however simple) just forwards messages as-is. Each endpoint decides for itself what to do with a message it receives. Adding a new business rule means editing only the one endpoint that cares about it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A smart pipe centralizes routing and transformation logic in a mediator; smart endpoints keep that logic in the services themselves, with a dumb pipe just forwarding messages">
  <text x="150" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Smart pipe (ESB-style)</text>
  <rect x="30" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Producer</text>
  <rect x="150" y="60" width="120" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="210" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Bus (routing +</text>
  <text x="210" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">business logic)</text>
  <rect x="300" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="345" y="94" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Consumer</text>

  <text x="500" y="20" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Smart endpoints</text>
  <rect x="430" y="60" width="100" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Producer</text>
  <text x="480" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">owns its logic</text>
  <line x1="530" y1="90" x2="555" y2="90" stroke="#8b949e" marker-end="url(#a7)"/>
  <text x="542" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">dumb pipe</text>
  <rect x="560" y="60" width="100" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Consumer</text>
  <text x="610" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">owns its logic</text>
  <defs><marker id="a7" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Logic sits either in a central bus everyone shares, or distributed at the edges where each endpoint owns its own rules.

## 5. Runnable example

Scenario: routing an order event to the right handler, first through a central smart-bus mediator, then refactored so the pipe carries messages blindly and each endpoint decides for itself.

### Level 1 — Basic

```java
// File: SmartBus.java -- a central mediator holding ALL the routing
// and business logic; endpoints are passive, dumb recipients.
import java.util.*;

public class SmartBus {
    static class Bus {
        void publish(String eventType, String payload) {
            // the BUS decides what each event type means and who should get it -- SMART PIPE
            if (eventType.equals("order.placed")) {
                if (payload.startsWith("premium-")) {
                    System.out.println("[bus] routing premium order to PriorityHandler: " + payload);
                } else {
                    System.out.println("[bus] routing standard order to StandardHandler: " + payload);
                }
            } else if (eventType.equals("order.cancelled")) {
                System.out.println("[bus] routing cancellation to RefundHandler: " + payload);
            }
        }
    }

    public static void main(String[] args) {
        Bus bus = new Bus();
        bus.publish("order.placed", "premium-widget");
        bus.publish("order.placed", "widget");
        bus.publish("order.cancelled", "widget");
    }
}
```

**How to run:** `javac SmartBus.java && java SmartBus` (JDK 17+).

Expected output:
```
[bus] routing premium order to PriorityHandler: premium-widget
[bus] routing standard order to StandardHandler: widget
[bus] routing cancellation to RefundHandler: widget
```

Every routing decision — what "premium" means, which handler owns cancellations — lives inside `Bus.publish`. Adding a new event type or a new routing rule means editing this one shared, central class, no matter which team's feature it's for.

### Level 2 — Intermediate

```java
// File: DumbPipeSmartEndpoints.java -- the pipe just forwards messages;
// each endpoint decides for itself what to do with what it receives.
import java.util.*;
import java.util.function.Consumer;

public class DumbPipeSmartEndpoints {
    // DUMB PIPE: knows nothing about "premium" or "cancellations" -- just fans out to subscribers.
    static class DumbPipe {
        List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void send(String message) { subscribers.forEach(h -> h.accept(message)); }
    }

    public static void main(String[] args) {
        DumbPipe pipe = new DumbPipe();

        // SMART ENDPOINT #1: decides for ITSELF what counts as "premium"
        pipe.subscribe(message -> {
            if (message.startsWith("order.placed:premium-")) {
                System.out.println("[PriorityHandler] handling: " + message);
            }
        });

        // SMART ENDPOINT #2: decides for ITSELF what counts as "standard"
        pipe.subscribe(message -> {
            if (message.startsWith("order.placed:") && !message.contains("premium-")) {
                System.out.println("[StandardHandler] handling: " + message);
            }
        });

        pipe.send("order.placed:premium-widget");
        pipe.send("order.placed:widget");
    }
}
```

**How to run:** `javac DumbPipeSmartEndpoints.java && java DumbPipeSmartEndpoints` (JDK 17+).

Expected output:
```
[PriorityHandler] handling: order.placed:premium-widget
[StandardHandler] handling: order.placed:widget
```

`DumbPipe.send` does nothing but call every subscriber with the raw message — it has no `if (eventType.equals(...))` logic at all. Each handler inspects the message itself and decides, independently, whether it cares. Adding a third handler means adding a new `subscribe` call; the pipe's code never changes.

### Level 3 — Advanced

```java
// File: DumbPipeNewEndpoint.java -- add a BRAND-NEW endpoint (RefundHandler)
// to an already-running pipe, with ZERO changes to the pipe or any existing endpoint.
import java.util.*;
import java.util.function.Consumer;

public class DumbPipeNewEndpoint {
    static class DumbPipe { // IDENTICAL to Level 2 -- unchanged
        List<Consumer<String>> subscribers = new ArrayList<>();
        void subscribe(Consumer<String> handler) { subscribers.add(handler); }
        void send(String message) { subscribers.forEach(h -> h.accept(message)); }
    }

    public static void main(String[] args) {
        DumbPipe pipe = new DumbPipe();

        pipe.subscribe(message -> { // PriorityHandler, unchanged from Level 2
            if (message.startsWith("order.placed:premium-")) System.out.println("[PriorityHandler] handling: " + message);
        });
        pipe.subscribe(message -> { // StandardHandler, unchanged from Level 2
            if (message.startsWith("order.placed:") && !message.contains("premium-")) System.out.println("[StandardHandler] handling: " + message);
        });

        // NEW endpoint, added independently -- no other endpoint or the pipe itself needed editing
        pipe.subscribe(message -> {
            if (message.startsWith("order.cancelled:")) System.out.println("[RefundHandler] handling: " + message);
        });

        pipe.send("order.placed:premium-widget");
        pipe.send("order.cancelled:widget"); // only RefundHandler reacts; the other two silently ignore it
    }
}
```

**How to run:** `javac DumbPipeNewEndpoint.java && java DumbPipeNewEndpoint` (JDK 17+).

Expected output:
```
[PriorityHandler] handling: order.placed:premium-widget
[RefundHandler] handling: order.cancelled:widget
```

The production-flavored case: a whole new capability (`RefundHandler`) was added by writing one new `subscribe` call — `DumbPipe` itself, `PriorityHandler`, and `StandardHandler` are byte-for-byte unchanged from Level 2. When `pipe.send("order.cancelled:widget")` runs, `PriorityHandler` and `StandardHandler` both receive it too (the pipe fans out to everyone, blindly) but their own `if` conditions silently reject it — exactly the decentralized decision-making smart endpoints are meant to provide.

## 6. Walkthrough

1. `pipe.subscribe(...)` is called three times, registering `PriorityHandler`, `StandardHandler`, and `RefundHandler` as independent `Consumer<String>` lambdas in the pipe's `subscribers` list. The pipe has no idea what any of them do.
2. `pipe.send("order.placed:premium-widget")` runs `subscribers.forEach(h -> h.accept(message))` — the exact same raw string is handed to all three subscribers, unmodified and uninterpreted by the pipe.
3. Inside `PriorityHandler`'s lambda, its own `if (message.startsWith("order.placed:premium-"))` check passes, so it prints the handling line. `StandardHandler`'s check fails (the message does contain `"premium-"`), so it does nothing. `RefundHandler`'s check also fails (wrong prefix), so it does nothing either.
4. `pipe.send("order.cancelled:widget")` runs the same fan-out. This time `PriorityHandler` and `StandardHandler`'s checks both fail silently, and only `RefundHandler`'s check passes, printing its handling line.
5. At no point does `DumbPipe.send` branch on message content — every routing decision happened inside the endpoint that received the message, exactly matching the "smart endpoints, dumb pipes" principle.

```
send("order.placed:premium-widget") -> fan out to ALL subscribers
    PriorityHandler: matches  -> handles
    StandardHandler: no match -> silent
    RefundHandler:   no match -> silent

send("order.cancelled:widget") -> fan out to ALL subscribers
    PriorityHandler: no match -> silent
    StandardHandler: no match -> silent
    RefundHandler:   matches  -> handles
```

## 7. Gotchas & takeaways

> **Gotcha:** "dumb pipe" doesn't mean "no infrastructure investment at all" — a real dumb pipe (a message broker, an HTTP gateway) still needs to be reliable, observable, and capable of retries or dead-lettering. "Dumb" refers specifically to a lack of *business* logic in the transport layer, not a lack of engineering effort in building a solid transport layer.

- Smart endpoints, dumb pipes keeps routing and business logic inside the services sending and receiving messages, not inside the messaging middleware connecting them.
- The concrete test: when a business rule changes, do you edit a central mediator/bus class, or only the one endpoint that owns that rule?
- Adding a new consumer of an event stream should require zero changes to the pipe and zero changes to any existing consumer — only new code for the new consumer.
- This characteristic is a direct rejection of older centralized ESB architectures, where routing and transformation logic piled up in a shared piece of middleware every team had to coordinate through.
