---
card: spring-data
gi: 112
slug: change-streams-reactive
title: "Change streams (reactive)"
---

## 1. What it is

**Change streams** let an application subscribe to a live feed of changes happening in a MongoDB collection — inserts, updates, deletes — as they happen, instead of repeatedly polling with queries. Spring Data MongoDB exposes this through `ReactiveMongoTemplate.changeStream(...)`, which returns a `Flux<ChangeStreamEvent<T>>` that keeps emitting as long as something subscribes to it.

```java
Flux<ChangeStreamEvent<Order>> stream = reactiveMongoTemplate
    .changeStream(Order.class)
    .watchCollection("orders")
    .listen();

stream.subscribe(event -> System.out.println("Changed: " + event.getBody()));
```

## 2. Why & when

Earlier cards covered `find`/`query` operations that fetch a snapshot of data at one point in time. Change streams solve a different problem: **reacting to changes as they occur**, without the client having to ask "did anything change?" over and over. They are built on MongoDB's replication mechanism (the oplog), so every change to a watched collection is delivered in the order it happened, exactly once per event, to every active subscriber.

Reach for a reactive change stream when:

- You need to push live updates to clients — for example, notifying a dashboard the instant an order's status flips to `SHIPPED`, without the dashboard polling every few seconds.
- You're building an event-driven pipeline where one service needs to react to another service's writes to a shared collection, without direct coupling between them.
- You want to keep a secondary system (a search index, a cache, an analytics store) in sync with MongoDB writes in near real time.

Change streams require MongoDB to be running as a replica set (or sharded cluster) — they are not available against a single standalone `mongod`, because they depend on the oplog that replication produces.

## 3. Core concept

```
 App writes:  db.orders.updateOne({id: 1}, {$set: {status: "SHIPPED"}})
                                |
                                v
                   MongoDB oplog records the change
                                |
                                v
    changeStream().watchCollection("orders").listen()  -- Flux<ChangeStreamEvent<Order>>
                                |
                                v
          subscriber #1  <--  event  -->  subscriber #2  (both get every event)
```

A change stream is a live, ordered, at-least-once feed — every subscriber sees every matching change, in the order MongoDB applied it, for as long as the subscription stays open.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A write to MongoDB flows through the oplog into a change stream, which pushes an event to every subscriber">
  <rect x="20" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Write to</text>
  <text x="90" y="63" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">orders collection</text>

  <rect x="250" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">oplog entry</text>

  <rect x="480" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ChangeStreamEvent</text>

  <line x1="160" y1="45" x2="245" y2="45" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <line x1="390" y1="45" x2="475" y2="45" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>

  <rect x="380" y="120" width="120" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="440" y="147" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">subscriber #1</text>

  <rect x="530" y="120" width="120" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="580" y="147" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">subscriber #2</text>

  <line x1="550" y1="70" x2="440" y2="118" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>
  <line x1="550" y1="70" x2="580" y2="118" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

One write produces one oplog entry, which fans out as one event to every active subscriber of the change stream.

## 5. Runnable example

The scenario: an order-status dashboard that needs to react the instant an order's status changes, evolving from a basic in-memory event bus, to a `Flux`-style reactive publisher with multiple subscribers, to a resilient stream that filters events and survives a disconnect using a resume token.

### Level 1 — Basic

Model the core idea: a write to a "collection" produces a change event, delivered to whoever is listening.

```java
import java.util.*;
import java.util.function.*;

public class ChangeStreamsLevel1 {
    public static void main(String[] args) {
        OrdersCollection orders = new OrdersCollection();
        orders.watch(event -> System.out.println("Changed (" + event.operationType + "): order "
            + event.body.id + " -> " + event.body.status));

        orders.update(1, "SHIPPED");
        orders.update(1, "DELIVERED");
    }
}

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

class ChangeStreamEvent {
    String operationType; Order body;
    ChangeStreamEvent(String operationType, Order body) { this.operationType = operationType; this.body = body; }
}

// Stands in for org.springframework.data.mongodb.core.ReactiveMongoTemplate's changeStream() feed.
class OrdersCollection {
    private final Map<Long, Order> docs = new HashMap<>();
    private Consumer<ChangeStreamEvent> listener; // one subscriber, for simplicity at this level

    void watch(Consumer<ChangeStreamEvent> listener) { this.listener = listener; }

    void update(long id, String newStatus) {
        Order o = docs.computeIfAbsent(id, k -> new Order(id, "PENDING"));
        o.status = newStatus;
        if (listener != null) listener.accept(new ChangeStreamEvent("update", o)); // fires AFTER the write
    }
}
```

How to run: `java ChangeStreamsLevel1.java`

`orders.watch(...)` registers a listener, standing in for `changeStream(Order.class).listen().subscribe(...)`. Every call to `update` performs the write and then, immediately, notifies the listener with a `ChangeStreamEvent` describing what changed — the same push model a real change stream uses, just without the network and the oplog in between.

### Level 2 — Intermediate

Support **multiple** subscribers, matching a real `Flux` — every subscriber to the same change stream receives every event, independently.

```java
import java.util.*;
import java.util.function.*;

public class ChangeStreamsLevel2 {
    public static void main(String[] args) {
        OrdersCollection orders = new OrdersCollection();

        orders.subscribe(e -> System.out.println("Dashboard sees: " + e.body.id + " -> " + e.body.status));
        orders.subscribe(e -> System.out.println("Audit log sees: " + e.body.id + " -> " + e.body.status));

        orders.update(1, "SHIPPED"); // BOTH subscribers fire for this one write
    }
}

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

class ChangeStreamEvent {
    String operationType; Order body;
    ChangeStreamEvent(String operationType, Order body) { this.operationType = operationType; this.body = body; }
}

// Stands in for Flux<ChangeStreamEvent<Order>> -- supports multiple independent subscribers.
class OrdersCollection {
    private final Map<Long, Order> docs = new HashMap<>();
    private final List<Consumer<ChangeStreamEvent>> subscribers = new ArrayList<>();

    void subscribe(Consumer<ChangeStreamEvent> subscriber) { subscribers.add(subscriber); }

    void update(long id, String newStatus) {
        Order o = docs.computeIfAbsent(id, k -> new Order(id, "PENDING"));
        o.status = newStatus;
        ChangeStreamEvent event = new ChangeStreamEvent("update", o);
        for (Consumer<ChangeStreamEvent> sub : subscribers) sub.accept(event); // EVERY subscriber sees EVERY event
    }
}
```

How to run: `java ChangeStreamsLevel2.java`

Two independent subscribers — a "dashboard" and an "audit log" — both register on the same stream, exactly like two separate `Flux<ChangeStreamEvent<Order>>.subscribe(...)` calls against the same `changeStream(...)` publisher. A single `update` call fans out to both, in registration order, each getting its own copy of the event.

### Level 3 — Advanced

Add a **filter** (only watch `status` changes, mirroring `.filter(where("updateDescription.updatedFields.status").exists(true))`) and a **resume token** so a subscriber that disconnects can resume from where it left off instead of missing events or re-processing everything.

```java
import java.util.*;
import java.util.function.*;

public class ChangeStreamsLevel3 {
    public static void main(String[] args) {
        OrdersCollection orders = new OrdersCollection();
        long lastSeenToken = 0;

        orders.update(1, "status", "SHIPPED");
        orders.update(1, "total", 150.0 + "");   // NOT a status change -- filtered out below
        orders.update(1, "status", "DELIVERED");

        List<Long> processed = new ArrayList<>();
        orders.listenFrom(lastSeenToken, "status", event -> {
            System.out.println("Processing: order " + event.orderId + " status -> " + event.statusAtEventTime
                + " (token " + event.resumeToken + ")");
            processed.add(event.resumeToken);
        });
        lastSeenToken = processed.get(processed.size() - 1); // save the last token -- this is what survives a disconnect

        System.out.println("--- subscriber disconnects, then reconnects, resuming from token " + lastSeenToken + " ---");
        orders.update(1, "status", "RETURNED"); // happens WHILE the subscriber was disconnected
        orders.listenFrom(lastSeenToken, "status", event ->
            System.out.println("Processing: order " + event.orderId + " status -> " + event.statusAtEventTime
                + " (token " + event.resumeToken + ")"));
    }
}

class Order { long id; String status; Order(long id, String status) { this.id = id; this.status = status; } }

class ChangeStreamEvent {
    long resumeToken; String operationType; String changedField; long orderId; String statusAtEventTime;
    ChangeStreamEvent(long resumeToken, String operationType, String changedField, long orderId, String statusAtEventTime) {
        this.resumeToken = resumeToken; this.operationType = operationType; this.changedField = changedField;
        this.orderId = orderId; this.statusAtEventTime = statusAtEventTime; // a SNAPSHOT, not a live reference to the document
    }
}

class OrdersCollection {
    private final Map<Long, Order> docs = new HashMap<>();
    private final List<ChangeStreamEvent> oplog = new ArrayList<>(); // stands in for MongoDB's oplog
    private long nextToken = 1;

    void update(long id, String field, String newValue) {
        Order o = docs.computeIfAbsent(id, k -> new Order(id, "PENDING"));
        if (field.equals("status")) o.status = newValue;
        // Snapshot o.status NOW -- a real oplog entry captures the document's state at write time, not a live pointer to it.
        oplog.add(new ChangeStreamEvent(nextToken++, "update", field, o.id, o.status));
    }

    // watchCollection("orders").filter(where(...updatedFields.status...).exists()).resumeAt(token).listen()
    void listenFrom(long resumeToken, String onlyField, Consumer<ChangeStreamEvent> subscriber) {
        for (ChangeStreamEvent event : oplog) {
            if (event.resumeToken <= resumeToken) continue;      // skip events already seen before the resume point
            if (!event.changedField.equals(onlyField)) continue; // filter: only care about this field
            subscriber.accept(event);
        }
    }
}
```

How to run: `java ChangeStreamsLevel3.java`

`listenFrom` only emits events past `resumeToken` and matching the `status` field, standing in for `.filter(...).resumeAt(token).listen()`. The "total" update is filtered out entirely. After the first batch, the resume token is saved; the subscriber then "reconnects" and picks up only the `RETURNED` change that happened during its downtime — nothing is missed and nothing already processed is repeated.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `orders.update(1, "status", "SHIPPED")` writes to the in-memory collection and appends a `ChangeStreamEvent` (token `1`) to the simulated oplog. `orders.update(1, "total", "150.0")` appends token `2`, but on a field the subscriber does not care about. `orders.update(1, "status", "DELIVERED")` appends token `3`.

`orders.listenFrom(0, "status", ...)` then walks the oplog from the beginning (`lastSeenToken = 0`), skipping any event whose `changedField` is not `"status"`. Token `1` (`SHIPPED`) is processed, token `2` is skipped because its field is `"total"`, and token `3` (`DELIVERED`) is processed. The last processed token, `3`, is saved as `lastSeenToken` — this is the value a real subscriber would persist alongside its resume token before disconnecting.

The subscriber then "disconnects" (nothing runs), and `orders.update(1, "status", "RETURNED")` happens while it is offline, appending token `4`. When `orders.listenFrom(3, "status", ...)` is called again, it skips every token `<= 3` — meaning it re-processes nothing — and delivers only token `4`, the change that happened during the outage.

```
Processing: order 1 status -> SHIPPED (token 1)
Processing: order 1 status -> DELIVERED (token 3)
--- subscriber disconnects, then reconnects, resuming from token 3 ---
Processing: order 1 status -> RETURNED (token 4)
```

In real MongoDB, the resume token is an opaque `BsonDocument` (not a simple counter), and `ReactiveMongoTemplate.changeStream(...).resumeAt(token)` (or `startAfter(token)`) passes it straight to the server, which replays the oplog from that exact position — this is why persisting the last-seen token before a subscriber shuts down is the standard way to make change-stream consumers resilient to restarts and network drops.

## 7. Gotchas & takeaways

> Gotcha: change streams require a **replica set** (even a single-node one for local development) — they will not work against a bare standalone `mongod`, because they are built on the oplog that only replication produces.

> Gotcha: a change stream is a live feed, not a query — a subscriber that starts listening *after* a write happened will never see that write unless it explicitly resumes from a token recorded before the write occurred.

- `ReactiveMongoTemplate.changeStream(Type.class).watchCollection(name).listen()` returns a `Flux<ChangeStreamEvent<Type>>` that keeps emitting until the subscription is cancelled.
- Every subscriber to the same stream sees every matching event, independently and in oplog order.
- `.filter(...)` narrows which change events are delivered (by operation type or changed fields), reducing noise for consumers that only care about specific writes.
- Persist the resume token from each processed event so a restarted or reconnected subscriber can pick up exactly where it left off, with no gaps and no duplicates.
