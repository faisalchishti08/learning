---
card: system-design
gi: 30
slug: spring-websocket-stomp-messaging
title: Spring WebSocket & STOMP messaging
---

## 1. What it is

**Spring WebSocket** is Spring's support for handling raw WebSocket connections (covered earlier in this section) within a Spring application. **Simple Text Oriented Messaging Protocol (STOMP)** is a lightweight messaging protocol that runs *on top of* WebSocket, adding structure — named destinations (like `/topic/prices`), a familiar publish/subscribe pattern, and message headers — so you are not left parsing raw text frames yourself.

## 2. Why & when

Raw WebSocket gives you a full-duplex connection, but no built-in concept of "send this message to everyone subscribed to this specific topic" — you would have to build that routing yourself. STOMP over Spring's WebSocket support adds exactly that: named destinations and a broker-style publish/subscribe model, so building something like a chat room or a live-updating dashboard with multiple topics becomes far simpler. You reach for this whenever your WebSocket use case needs to route different messages to different groups of interested clients, not just a single raw stream.

## 3. Core concept

**How Spring wires it together:**
- A `@Configuration` class implementing `WebSocketMessageBrokerConfigurer` registers a STOMP endpoint (the URL clients connect to) and enables a **message broker** — either a simple in-memory one Spring provides, or a full external broker like RabbitMQ for production scale.
- Clients **subscribe** to destinations, like `/topic/prices`, to receive messages published there.
- A `@Controller` method annotated `@MessageMapping("/send")` handles messages a client sends *to* the server; a method can use `@SendTo("/topic/prices")` to broadcast its return value to every subscriber of that destination.

**The message flow:**
1. Client connects to the STOMP endpoint (which itself is a WebSocket connection under the hood).
2. Client subscribes to a destination, e.g. `/topic/prices`.
3. Some event happens (an order fills, a price changes) and the server publishes a message to `/topic/prices`.
4. The message broker delivers that message to every client currently subscribed to `/topic/prices` — the server does not need to track individual connections itself; the broker handles fan-out.

**Why this scales better than tracking raw connections manually:** with raw WebSocket, your own code has to remember which specific connection belongs to which topic and loop over them to broadcast. STOMP's broker abstraction handles this subscription tracking and message routing for you, and swapping the simple in-memory broker for an external one (like RabbitMQ) lets this scale across multiple server instances without you rewriting your message-sending code.

## 4. Diagram

```
 Client A --subscribe /topic/prices-->|
 Client B --subscribe /topic/prices-->|  Message Broker (in-memory or RabbitMQ)
 Client C --subscribe /topic/orders-->|
                                       |
 Server: @MessageMapping("/updatePrice")
         @SendTo("/topic/prices")
         publishes new price ------------------->|
                                       |
                     broker fans out to A and B (not C, wrong topic)
```
*Caption: clients subscribe to named destinations; the broker fans out published messages only to the matching subscribers.*

## 5. Runnable example

### Artifact: a minimal Java sketch of a STOMP-style publish/subscribe broker, illustrating the routing Spring's broker performs

```java
import java.util.*;

public class StompBrokerSim {

    // Maps a destination to the set of subscribed client names.
    static final Map<String, Set<String>> subscriptions = new HashMap<>();

    static void subscribe(String client, String destination) {
        subscriptions.computeIfAbsent(destination, d -> new LinkedHashSet<>()).add(client);
        System.out.println(client + " subscribed to " + destination);
    }

    // Simulates a @MessageMapping handler using @SendTo to broadcast.
    static void publish(String destination, String message) {
        Set<String> subscribers = subscriptions.getOrDefault(destination, Set.of());
        System.out.println("Publishing to " + destination + ": \"" + message + "\"");
        for (String client : subscribers) {
            System.out.println("  -> delivered to " + client);
        }
    }

    public static void main(String[] args) {
        subscribe("ClientA", "/topic/prices");
        subscribe("ClientB", "/topic/prices");
        subscribe("ClientC", "/topic/orders");

        publish("/topic/prices", "AAPL now $101.50");
        publish("/topic/orders", "Order #99 filled");
    }
}
```

**How to run:** save as `StompBrokerSim.java`, run `java StompBrokerSim.java` (JDK 17+). A real Spring app uses the `spring-boot-starter-websocket` dependency and `@MessageMapping`/`@SendTo` annotations; this example models the broker's core routing behavior directly, without requiring a running server.

## 6. Walkthrough

1. `subscriptions` models the broker's internal state: which clients are listening to which destination — exactly what Spring's message broker tracks for you automatically when a client sends a STOMP `SUBSCRIBE` frame.
2. `subscribe` registers a client under a destination, printing confirmation, mirroring a client's subscription being acknowledged.
3. `publish` models a `@MessageMapping` handler's `@SendTo` broadcast: it looks up every client subscribed to the given destination and delivers the message to each one, and only those.
4. `main` sets up three clients: two subscribed to `/topic/prices`, one subscribed to `/topic/orders`, then publishes one message to each destination.
5. Output:
```
ClientA subscribed to /topic/prices
ClientB subscribed to /topic/prices
ClientC subscribed to /topic/orders
Publishing to /topic/prices: "AAPL now $101.50"
  -> delivered to ClientA
  -> delivered to ClientB
Publishing to /topic/orders: "Order #99 filled"
  -> delivered to ClientC
```
6. Notice `ClientC` never receives the price update, and `ClientA`/`ClientB` never receive the order update — the broker routes strictly by destination, which is exactly the structure STOMP adds on top of raw WebSocket's single, undifferentiated stream.

## 7. Gotchas & takeaways

> **Gotcha:** using Spring's simple, built-in in-memory broker in a multi-instance production deployment. Because it only tracks subscriptions within its own single server process, a message published on one instance never reaches a client whose WebSocket connection is held by a *different* instance — switch to an external broker (like RabbitMQ) once you run more than one server instance.

- STOMP adds named destinations and publish/subscribe routing on top of raw WebSocket, removing the need to manually track which connection wants which messages.
- `@MessageMapping` handles incoming client messages; `@SendTo` broadcasts a handler's return value to a destination's subscribers.
- The built-in in-memory broker is fine for a single instance or local development; use an external broker for multi-instance production scale.
