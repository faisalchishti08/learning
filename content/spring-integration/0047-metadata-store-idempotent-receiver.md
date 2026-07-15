---
card: spring-integration
gi: 47
slug: metadata-store-idempotent-receiver
title: "Metadata store / idempotent receiver"
---

## 1. What it is

A `MetadataStore` is a simple, pluggable key-value persistence abstraction (`ConcurrentMetadataStore`/`SimpleMetadataStore` in-memory by default, with JDBC, MongoDB, Redis, and Zookeeper-backed alternatives) used to remember small facts across restarts — most commonly, which message IDs (or business keys) have already been processed. An idempotent receiver is the pattern built on top of it: an endpoint (often implemented as a `Filter`, card 0022, or an `IdempotentReceiverInterceptor`) that checks a `MetadataStore` before processing a message, skipping anything it recognizes as already handled, so that a message delivered more than once (a common reality with many messaging transports' at-least-once delivery guarantees) is only ever *processed* once.

## 2. Why & when

You reach for a `MetadataStore`-backed idempotent receiver specifically when duplicate message delivery is a real possibility and processing the same message twice would be harmful:

- **The messaging transport only guarantees at-least-once delivery** (many JMS, Kafka, and cloud queue configurations) — a network hiccup or consumer restart can cause the same message to be redelivered; without an idempotency check, "charge the customer's card" or "ship the order" could happen twice for what was logically one event.
- **You want that de-duplication to survive application restarts**, not just catch duplicates arriving within one process's uptime — a purely in-memory "have I seen this ID" set would forget everything on restart, exactly the same durability gap `SimpleMessageStore` has (card 0046); a persistent `MetadataStore` avoids that.
- **The idempotency check needs to be a lightweight, dedicated lookup** — a `MetadataStore` is intentionally a much simpler abstraction than a full `MessageStore`: it stores small key-value facts (has this ID been seen?), not entire buffered message bodies, making it cheap to check on every single incoming message.

## 3. Core concept

Think of a `MetadataStore`-backed idempotent receiver like a wedding's guest check-in table with a physical guest list. Each arriving guest's name is checked against the list before they're let in; if their name is already checked off, they're recognized as having already been let in (perhaps they walked out and came back in through a different door) and aren't seated a second time, taking up a duplicate seat. The guest list itself is small — just names and a checkbox, not each guest's entire life story — which is exactly why checking it at the door is fast enough to do for every single arrival.

```java
@Bean
public MetadataStore metadataStore() {
    return new SimpleMetadataStore(); // or JdbcMetadataStore for a durable, restart-surviving version
}

@Filter(inputChannel = "orders", outputChannel = "newOrders")
public boolean isNewOrder(Message<Order> message) {
    String messageId = message.getHeaders().getId().toString();
    if (metadataStore.get(messageId) != null) {
        return false; // ALREADY seen this exact message — skip it, don't process twice
    }
    metadataStore.put(messageId, Instant.now().toString());
    return true;
}
```

The filter's condition is a single fast lookup against the metadata store — messages recognized as already-processed are simply dropped, exactly like any other `Filter` (card 0022) rejection, just based on "have I seen this before" rather than a business-rule condition.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Idempotent receiver checks each incoming message's ID against a MetadataStore; a new ID is recorded and forwarded, a duplicate ID is recognized and dropped" >
  <rect x="20" y="60" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="85" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">incoming message</text>

  <line x1="150" y1="85" x2="210" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#mdc1)"/>

  <rect x="220" y="60" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="310" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check MetadataStore</text>
  <text x="310" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">has this ID been seen?</text>

  <line x1="400" y1="75" x2="460" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#mdc2)"/>
  <text x="440" y="25" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">new -&gt; record + forward</text>

  <line x1="400" y1="95" x2="460" y2="140" stroke="#8b949e" stroke-width="1.5" marker-end="url(#mdc2)"/>
  <text x="440" y="155" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">duplicate -&gt; DROP</text>

  <rect x="470" y="10" width="140" height="35" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="32" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">newOrders channel</text>

  <defs>
    <marker id="mdc1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="mdc2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

A single fast key lookup decides, per message, whether it's genuinely new or a duplicate already handled.

## 5. Runnable example

The scenario: an order-processing endpoint receiving occasionally-duplicated messages from an at-least-once transport, starting with a basic idempotent filter, then persisting that check across a simulated restart, and finally a business-key-based (not just message-ID-based) idempotency check for a more realistic duplicate scenario.

### Level 1 — Basic

```java
// BasicIdempotentReceiverDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

public class BasicIdempotentReceiverDemo {
    record Order(String id) {}

    public static void main(String[] args) {
        Map<String, String> metadataStore = new ConcurrentHashMap<>(); // stand-in for SimpleMetadataStore
        DirectChannel orders = new DirectChannel();
        DirectChannel newOrders = new DirectChannel();
        newOrders.subscribe(m -> System.out.println("Processing (genuinely new): " + m.getPayload()));

        // what an idempotent-receiver Filter does for you:
        orders.subscribe(m -> {
            String messageId = m.getHeaders().getId().toString();
            if (metadataStore.putIfAbsent(messageId, "seen") != null) {
                System.out.println("DUPLICATE detected, skipping: " + m.getPayload());
            } else {
                newOrders.send(m);
            }
        });

        var duplicateMessage = MessageBuilder.withPayload(new Order("ORD-1")).build();
        orders.send(duplicateMessage);        // first delivery
        orders.send(duplicateMessage);        // SAME message object redelivered (simulating at-least-once)
    }
}
```

How to run: `java BasicIdempotentReceiverDemo.java`. Expected output: `Processing (genuinely new): Order[id=ORD-1]` then `DUPLICATE detected, skipping: Order[id=ORD-1]` — the exact same message, redelivered a second time (its ID unchanged, since it's literally the same `Message` object), was recognized and skipped rather than processed twice.

### Level 2 — Intermediate

Using a file-backed metadata store (standing in for a real `JdbcMetadataStore`) shows the check surviving a simulated application restart — a message redelivered *after* the restart is still correctly recognized as a duplicate, something a purely in-memory metadata store could never do.

```java
// PersistentMetadataStoreDemo.java
import java.io.*;
import java.util.*;

public class PersistentMetadataStoreDemo {
    static boolean checkAndRecord(File storeFile, String messageId) throws IOException {
        Set<String> seen = readSeenIds(storeFile);
        boolean isDuplicate = seen.contains(messageId);
        if (!isDuplicate) {
            seen.add(messageId);
            try (PrintWriter out = new PrintWriter(new FileWriter(storeFile))) {
                seen.forEach(out::println);
            }
        }
        return isDuplicate;
    }

    static Set<String> readSeenIds(File storeFile) throws IOException {
        if (!storeFile.exists()) return new HashSet<>();
        Set<String> ids = new HashSet<>();
        try (BufferedReader in = new BufferedReader(new FileReader(storeFile))) {
            String line;
            while ((line = in.readLine()) != null) ids.add(line);
        }
        return ids;
    }

    public static void main(String[] args) throws IOException {
        File storeFile = File.createTempFile("metadata-store-demo", ".dat");
        storeFile.deleteOnExit();

        System.out.println("First delivery, duplicate=" + checkAndRecord(storeFile, "msg-ORD-1"));

        // simulate a full application restart: nothing but the file survives
        System.out.println("--- simulated restart ---");
        System.out.println("Redelivery AFTER restart, duplicate=" + checkAndRecord(storeFile, "msg-ORD-1"));
    }
}
```

How to run: `java PersistentMetadataStoreDemo.java`. Expected output: `First delivery, duplicate=false`, `--- simulated restart ---`, then `Redelivery AFTER restart, duplicate=true` — even across the simulated restart (a fresh read from the durable file, with no in-memory state carried over), the second delivery of the same message ID was still correctly recognized as a duplicate.

### Level 3 — Advanced

A more realistic idempotency check often uses a stable *business key* (an order ID from the payload) rather than the transport-generated message ID, since two genuinely distinct message deliveries (different message IDs) can still represent the same logical business event — shown here alongside a TTL-style cleanup to prevent the metadata store from growing forever.

```java
// BusinessKeyIdempotencyDemo.java
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;
import java.time.Instant;
import java.time.Duration;

public class BusinessKeyIdempotencyDemo {
    record Order(String id, double amount) {}

    static Map<String, Instant> metadataStore = new ConcurrentHashMap<>();
    static Duration retentionWindow = Duration.ofMinutes(30); // don't keep entries forever

    static boolean isDuplicateByBusinessKey(Order order) {
        String businessKey = "order-" + order.id(); // the STABLE business identity, not a transport message ID
        Instant now = Instant.now();
        Instant existing = metadataStore.get(businessKey);
        if (existing != null && Duration.between(existing, now).compareTo(retentionWindow) < 0) {
            return true; // seen recently — genuine duplicate by business meaning
        }
        metadataStore.put(businessKey, now);
        return false;
    }

    public static void main(String[] args) {
        // two DIFFERENT transport-level messages (different message IDs, if this were real),
        // but the SAME business order — e.g. delivered via two different retries with new envelope IDs
        Order delivery1 = new Order("ORD-1", 199.99);
        Order delivery2 = new Order("ORD-1", 199.99); // same order ID, a genuinely separate delivery/message

        System.out.println("Delivery 1, duplicate by business key=" + isDuplicateByBusinessKey(delivery1));
        System.out.println("Delivery 2, duplicate by business key=" + isDuplicateByBusinessKey(delivery2));

        Order differentOrder = new Order("ORD-2", 50.0);
        System.out.println("A genuinely different order, duplicate=" + isDuplicateByBusinessKey(differentOrder));
    }
}
```

How to run: `java BusinessKeyIdempotencyDemo.java`. Expected output: `Delivery 1, duplicate by business key=false`, `Delivery 2, duplicate by business key=true`, then `A genuinely different order, duplicate=false` — even though `delivery1` and `delivery2` would be entirely separate `Message` objects with separate transport-level IDs in a real system, the business-key check correctly recognized them as the same logical order, while a genuinely different order was correctly treated as new.

## 6. Walkthrough

Tracing `BusinessKeyIdempotencyDemo` in execution order:

1. `isDuplicateByBusinessKey(delivery1)` computes `businessKey = "order-ORD-1"`, checks `metadataStore.get(...)` — nothing is present yet, so `existing` is `null`, and the method records the current timestamp under that key before returning `false` (not a duplicate).
2. `isDuplicateByBusinessKey(delivery2)` computes the *same* `businessKey`, `"order-ORD-1"`, since `delivery2` carries the same order ID — even though, in a real system, `delivery2` would have arrived as a completely separate message with its own distinct transport-level ID.
3. This time, `metadataStore.get("order-ORD-1")` finds the timestamp recorded in step 1; `Duration.between(existing, now)` is well within the 30-minute retention window, so the method returns `true` — correctly identifying this as a duplicate by business meaning, regardless of transport-level message identity.
4. `isDuplicateByBusinessKey(differentOrder)` computes `businessKey = "order-ORD-2"` — a key that has never been seen before — so `existing` is `null`, and this order is correctly recognized as genuinely new.
5. The `retentionWindow` check (`Duration.between(...).compareTo(retentionWindow) < 0`) is what prevents the metadata store from growing forever with permanently-retained entries: an entry older than 30 minutes would no longer count as "recently seen," allowing (in a real system with cleanup) that key to eventually be evicted or reused.
6. This business-key approach is strictly more robust for real-world idempotency than a pure message-ID check (as in Level 1) precisely because message IDs are transport-level identifiers that change on every redelivery attempt, while a business key (an order ID, a payment reference) represents the actual logical event the system cares about not processing twice.

```
delivery1 (order-ORD-1) -> businessKey lookup: not found -> record timestamp -> NOT duplicate
delivery2 (order-ORD-1) -> businessKey lookup: FOUND (within retention window) -> DUPLICATE
differentOrder (order-ORD-2) -> businessKey lookup: not found -> record timestamp -> NOT duplicate
```

## 7. Gotchas & takeaways

> A metadata store with no retention/eviction policy grows without bound as long as the application keeps receiving new unique keys — exactly the same unbounded-growth risk `QueueChannel` (card 0010) and `Aggregator` (card 0025) carry without their own bounds or timeouts. Always pair an idempotent receiver's metadata store with either a TTL-based eviction policy (as shown in Level 3) or periodic cleanup, especially for high-volume systems where the set of distinct business keys grows continuously over the application's lifetime.

- A `MetadataStore` is a lightweight, pluggable key-value persistence abstraction, most commonly used to remember which messages (or business events) have already been processed.
- An idempotent receiver checks a `MetadataStore` before processing each incoming message, skipping anything already recognized — protecting against duplicate processing from at-least-once delivery transports.
- A persistent `MetadataStore` implementation (JDBC, MongoDB, Redis, Zookeeper) makes that de-duplication survive application restarts, unlike a purely in-memory check that would forget everything on restart.
- Prefer checking a stable business key (an order ID, a payment reference) over a raw transport-level message ID when possible — the same logical event can arrive as genuinely different messages with different transport IDs across retries.
- Always pair a metadata store with a retention/eviction policy (TTL-based or otherwise) to prevent unbounded growth as the set of distinct keys accumulates over the application's lifetime.
