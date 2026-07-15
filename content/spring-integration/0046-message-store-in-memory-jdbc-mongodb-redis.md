---
card: spring-integration
gi: 46
slug: message-store-in-memory-jdbc-mongodb-redis
title: "Message store (in-memory, JDBC, MongoDB, Redis)"
---

## 1. What it is

A `MessageStore` is the pluggable persistence abstraction behind every stateful Spring Integration component that needs to hold onto messages across time — `QueueChannel` (card 0010), `Aggregator` (card 0025), `Resequencer` (card 0026), and `Delayer` (card 0028) all buffer messages internally using a `MessageStore` rather than an ad hoc in-memory collection. The default implementation, `SimpleMessageStore`, keeps everything in-memory (fast, but lost on restart); production-grade alternatives (`JdbcMessageStore`, `MongoDbMessageStore`, `RedisMessageStore`) persist that same buffered state to an external, durable store instead.

## 2. Why & when

You reach for a persistent `MessageStore` implementation specifically when a stateful component's buffered messages need to survive beyond the application's own in-memory lifetime:

- **An `Aggregator` (card 0025) is buffering a partial group when the application restarts or crashes** — with `SimpleMessageStore`, that partial group is gone forever; with `JdbcMessageStore` (or another persistent option), the buffered messages are recovered from the database and the aggregation can continue once the application comes back up.
- **A `Delayer` (card 0028) has scheduled messages waiting for their delay to elapse, and the application needs to restart during that window** — a persistent message store means those pending delayed messages survive the restart and still fire once their delay is up, rather than silently vanishing.
- **Multiple application instances need to share the same buffered state** — a `RedisMessageStore` or `JdbcMessageStore` backed by a shared database lets several instances of a clustered application coordinate around the same aggregation groups or delayed messages, something purely in-memory storage on one instance could never support.

## 3. Core concept

Think of `SimpleMessageStore` like keeping meeting notes on a whiteboard — fast to read and write, but the moment the room is cleared (the application restarts), everything on it is gone. A persistent `MessageStore` (JDBC, MongoDB, Redis) is like keeping those same notes in a shared, durable notebook instead — slightly slower to read and write than a whiteboard, but the notes survive the room being cleared, and anyone with access to the notebook (another application instance) can pick up exactly where the notes left off.

```java
@Bean
public MessageStore messageStore(DataSource dataSource) {
    return new JdbcMessageStore(dataSource); // persists to a real database table
}

@Bean
@ServiceActivator(inputChannel = "orderItems")
public AggregatingMessageHandler aggregator(MessageStore messageStore) {
    AggregatingMessageHandler handler = new AggregatingMessageHandler(
        new DefaultAggregatingMessageGroupProcessor(), messageStore);
    handler.setOutputChannelName("orderSummaries");
    return handler;
}
```

The `Aggregator`'s buffering behavior (from card 0025) is otherwise unchanged — what differs is purely *where* the buffered group's messages physically live while waiting to be released: in-process memory (`SimpleMessageStore`) versus a durable, external store.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stateful components like Aggregator delegate their buffering to a pluggable MessageStore, which can be in-memory (lost on restart) or a persistent backend (survives restarts and can be shared across instances)">
  <rect x="20" y="70" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="100" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Aggregator / Delayer</text>

  <line x1="180" y1="92" x2="230" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#ms1)"/>

  <rect x="240" y="70" width="150" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="97" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">MessageStore</text>

  <line x1="315" y1="70" x2="200" y2="30" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ms2)"/>
  <rect x="120" y="10" width="160" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="30" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">SimpleMessageStore (in-memory)</text>

  <line x1="315" y1="115" x2="440" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ms2)"/>
  <rect x="400" y="150" width="200" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="500" y="170" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">JdbcMessageStore / MongoDb / Redis</text>

  <defs>
    <marker id="ms1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ms2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The same stateful component's behavior stays identical regardless of which `MessageStore` implementation backs it — only durability and shareability change.

## 5. Runnable example

The scenario: an order aggregation flow needing durable buffering, starting with a basic in-memory-only demonstration of what's lost on restart, then a simulated persistent store surviving a restart, and finally comparing behavior when multiple "instances" share the same persistent store.

### Level 1 — Basic

```java
// InMemoryLossOnRestartDemo.java
import java.util.*;

public class InMemoryLossOnRestartDemo {
    record LineItemResult(String sku, boolean inStock) {}

    // SimpleMessageStore-equivalent: plain in-memory map, exists only as long as the JVM does
    static class InMemoryStore {
        Map<String, List<LineItemResult>> groups = new HashMap<>();
        void add(String correlationId, LineItemResult item) {
            groups.computeIfAbsent(correlationId, k -> new ArrayList<>()).add(item);
        }
    }

    public static void main(String[] args) {
        InMemoryStore store = new InMemoryStore();
        store.add("order-42", new LineItemResult("SKU-A", true));
        store.add("order-42", new LineItemResult("SKU-B", true));
        System.out.println("Before 'restart': buffered group has " + store.groups.get("order-42").size() + " items");

        // simulate an application restart: a BRAND NEW store instance, nothing carried over
        store = new InMemoryStore();
        System.out.println("After 'restart' (new InMemoryStore instance): buffered group = "
            + store.groups.getOrDefault("order-42", List.of()) + " — EVERYTHING LOST");
    }
}
```

How to run: `java InMemoryLossOnRestartDemo.java`. Expected output: `Before 'restart': buffered group has 2 items` then `After 'restart' (new InMemoryStore instance): buffered group = [] — EVERYTHING LOST` — exactly the risk `SimpleMessageStore` carries in production: any buffered-but-incomplete aggregation group is gone the moment the application process restarts.

### Level 2 — Intermediate

Simulating a persistent store (standing in for `JdbcMessageStore`) with data written to a file, showing that a buffered group genuinely survives a "restart" — represented here as re-reading from the persisted file into a fresh in-memory structure, rather than relying on anything carried over in the JVM's own memory.

```java
// PersistentStoreSurvivesRestartDemo.java
import java.io.*;
import java.util.*;

public class PersistentStoreSurvivesRestartDemo {
    record LineItemResult(String sku, boolean inStock) implements Serializable {}

    // stands in for JdbcMessageStore: writes to DURABLE storage (here, a file) instead of a JVM-only map
    static void persistToStore(File storeFile, String correlationId, LineItemResult item) throws IOException {
        List<Object[]> existing = readAllFromStore(storeFile);
        existing.add(new Object[]{correlationId, item});
        try (ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream(storeFile))) {
            out.writeObject(existing);
        }
    }

    @SuppressWarnings("unchecked")
    static List<Object[]> readAllFromStore(File storeFile) throws IOException {
        if (!storeFile.exists()) return new ArrayList<>();
        try (ObjectInputStream in = new ObjectInputStream(new FileInputStream(storeFile))) {
            return (List<Object[]>) in.readObject();
        } catch (ClassNotFoundException | EOFException e) { return new ArrayList<>(); }
    }

    public static void main(String[] args) throws Exception {
        File storeFile = File.createTempFile("message-store-demo", ".dat");
        storeFile.deleteOnExit();

        persistToStore(storeFile, "order-42", new LineItemResult("SKU-A", true));
        persistToStore(storeFile, "order-42", new LineItemResult("SKU-B", true));
        System.out.println("Before 'restart': " + readAllFromStore(storeFile).size() + " items persisted to durable storage");

        // simulate a full application restart: nothing but the FILE survives; re-read from it fresh
        List<Object[]> recovered = readAllFromStore(storeFile);
        System.out.println("After 'restart' (re-read from persistent store): " + recovered.size()
            + " items RECOVERED — nothing was lost");
    }
}
```

How to run: `java PersistentStoreSurvivesRestartDemo.java`. Expected output: `Before 'restart': 2 items persisted to durable storage` then `After 'restart' (re-read from persistent store): 2 items RECOVERED — nothing was lost` — unlike Level 1's in-memory store, the durable file-backed store's contents were fully intact after the simulated restart, exactly the guarantee `JdbcMessageStore`/`MongoDbMessageStore`/`RedisMessageStore` provide in a real application.

### Level 3 — Advanced

Two separate "application instances" (represented as two independent code paths that never share Java-level memory) both writing to and reading from the *same* persistent store file, showing that a shared durable `MessageStore` is what makes multi-instance aggregation coordination possible at all — something no in-memory store could ever support across separate processes.

```java
// SharedStoreAcrossInstancesDemo.java
import java.io.*;
import java.util.*;

public class SharedStoreAcrossInstancesDemo {
    record LineItemResult(String sku, boolean inStock) implements Serializable {}

    static void persistToStore(File storeFile, LineItemResult item) throws IOException {
        List<LineItemResult> existing = readAllFromStore(storeFile);
        existing.add(item);
        try (ObjectOutputStream out = new ObjectOutputStream(new FileOutputStream(storeFile))) {
            out.writeObject(existing);
        }
    }

    @SuppressWarnings("unchecked")
    static List<LineItemResult> readAllFromStore(File storeFile) throws IOException {
        if (!storeFile.exists()) return new ArrayList<>();
        try (ObjectInputStream in = new ObjectInputStream(new FileInputStream(storeFile))) {
            return (List<LineItemResult>) in.readObject();
        } catch (ClassNotFoundException | EOFException e) { return new ArrayList<>(); }
    }

    public static void main(String[] args) throws Exception {
        File sharedStoreFile = File.createTempFile("shared-message-store-demo", ".dat");
        sharedStoreFile.deleteOnExit();

        // "Instance A" processes and persists SKU-A's result
        System.out.println("[Instance A] persisting SKU-A result");
        persistToStore(sharedStoreFile, new LineItemResult("SKU-A", true));

        // "Instance B" — a COMPLETELY separate code path, sharing NOTHING but the store file — persists SKU-B
        System.out.println("[Instance B] persisting SKU-B result");
        persistToStore(sharedStoreFile, new LineItemResult("SKU-B", true));

        // either instance reading the shared store now sees BOTH results — coordination via the shared store
        List<LineItemResult> combined = readAllFromStore(sharedStoreFile);
        System.out.println("Either instance reading the SHARED store sees: " + combined);
    }
}
```

How to run: `java SharedStoreAcrossInstancesDemo.java`. Expected output: `[Instance A] persisting SKU-A result`, `[Instance B] persisting SKU-B result`, then `Either instance reading the SHARED store sees: [LineItemResult[sku=SKU-A, inStock=true], LineItemResult[sku=SKU-B, inStock=true]]` — even though "Instance A" and "Instance B" never shared any in-process Java state, both results ended up visible through the shared durable store, exactly the coordination mechanism that lets a real clustered application's multiple instances jointly build up one aggregation group.

## 6. Walkthrough

Tracing `SharedStoreAcrossInstancesDemo` in execution order:

1. "Instance A"'s code calls `persistToStore(sharedStoreFile, SKU-A result)` — this reads whatever's currently in the store file (nothing yet, on the first call), appends the new `LineItemResult`, and writes the updated list back to the same file.
2. "Instance B"'s code — represented as a separate call with no shared Java objects, standing in for a genuinely separate application process — calls the same `persistToStore` function with its own result, `SKU-B`.
3. Crucially, this second call *re-reads* the store file first (via `readAllFromStore` inside `persistToStore`), picking up the `SKU-A` entry that "Instance A" already wrote, before appending its own `SKU-B` entry and writing the combined list back.
4. The final `readAllFromStore(sharedStoreFile)` call, representing either instance checking the store's current state, reads back both entries — `SKU-A` and `SKU-B` — even though neither "instance" ever directly communicated with the other.
5. This is exactly the mechanism a real `JdbcMessageStore` (or `MongoDbMessageStore`/`RedisMessageStore`) provides for a genuinely clustered `Aggregator`: multiple application instances, each handling different pieces of a split order's line items, all read and write to the same shared database-backed store, letting the aggregation group accumulate correctly regardless of which instance processed which individual item.
6. Without a shared persistent store — if each instance used its own `SimpleMessageStore` — "Instance A" and "Instance B" would each believe they had an incomplete group of just one item, and the aggregation would never actually complete, since no single instance's in-memory state ever contained both results.

```
Instance A: persist(SKU-A) -> store file now contains: [SKU-A]
Instance B: persist(SKU-B) -> reads store file (sees SKU-A) -> appends SKU-B -> store file now contains: [SKU-A, SKU-B]
Either instance reading the store: sees the FULL combined group
```

## 7. Gotchas & takeaways

> Switching from `SimpleMessageStore` to a persistent implementation is not a purely additive change — persistent stores add real I/O latency to every buffering operation (an `Aggregator`'s group update, a `Delayer`'s scheduled message), and require the underlying database/store schema to actually be provisioned and migrated correctly. A common mistake is assuming a persistent `MessageStore` is a drop-in performance-equivalent swap; benchmark and provision accordingly, especially for high-throughput aggregation or delay use cases.

- `MessageStore` is the pluggable persistence abstraction behind stateful components like `Aggregator` (card 0025), `Resequencer` (card 0026), `Delayer` (card 0028), and `QueueChannel` (card 0010) — it's where their buffered/pending messages actually live.
- `SimpleMessageStore` (the default) keeps everything in-memory: fast, but all buffered state is lost if the application restarts.
- Persistent implementations (`JdbcMessageStore`, `MongoDbMessageStore`, `RedisMessageStore`) durably store the same buffered state, surviving application restarts and enabling recovery of in-flight aggregation groups or delayed messages.
- A shared persistent store is what makes multi-instance coordination possible — several clustered application instances can jointly build up the same buffered aggregation group by reading and writing to the same durable backend.
- Persistent stores trade some latency and operational complexity (schema provisioning, network calls) for durability and shareability — choose based on whether the specific stateful component's buffered data genuinely needs to survive restarts or be shared across instances.
