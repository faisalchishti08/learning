---
card: microservices
gi: 119
slug: message-ordering-guarantees
title: "Message ordering guarantees"
---

## 1. What it is

Message ordering guarantees describe whether, and under what conditions, a messaging system promises to deliver messages to a consumer in the same order they were produced. Plain queues generally guarantee nothing about order once more than one consumer is involved; systems that need order use a technique like partitioning by key to get "ordered within a partition, unordered across partitions."

## 2. Why & when

Some events only make sense in order: `OrderCreated` before `OrderShipped` before `OrderDelivered` for the *same* order, or `AccountDebited` before `AccountCredited` for the *same* transfer. If a consumer sees `OrderShipped` before `OrderCreated` because two different workers happened to process them out of turn, the consumer's logic can easily end up in an invalid state (shipping an order that, as far as it knows, doesn't exist yet).

Ordering only matters, and needs to be designed for, *within* a related sequence of events — order between *unrelated* events (an event for order 42 versus an event for order 99) is almost never something any consumer actually needs. Recognizing that distinction is what makes ordering practical to guarantee: instead of ordering an entire firehose of unrelated events (expensive, often impossible at scale), a system only needs to order events that share a key.

## 3. Core concept

Partitioning by key routes every message with the same key (e.g., the same `orderId`) to the same partition, and within a single partition, delivery order matches send order; across different partitions (different keys), no ordering relationship is promised or needed.

```java
// same orderId -> same partition -> guaranteed order for THIS order's events
broker.send("order-events", key = "order-42", event = "OrderCreated");
broker.send("order-events", key = "order-42", event = "OrderShipped");
// a DIFFERENT orderId can land on a different partition, processed independently, in parallel
broker.send("order-events", key = "order-99", event = "OrderCreated");
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Messages with the same key are routed to the same partition and stay in order within it; messages with different keys land on different partitions with no ordering relationship between them">
  <rect x="20" y="20" width="180" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="40" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Partition 0 (key: order-42)</text>
  <rect x="35" y="50" width="60" height="24" fill="#79c0ff" opacity="0.5"/><text x="65" y="66" font-size="7" text-anchor="middle" fill="#0d1117" font-family="sans-serif">Created</text>
  <rect x="100" y="50" width="60" height="24" fill="#79c0ff" opacity="0.5"/><text x="130" y="66" font-size="7" text-anchor="middle" fill="#0d1117" font-family="sans-serif">Shipped</text>

  <rect x="20" y="120" width="180" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="140" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Partition 1 (key: order-99)</text>
  <rect x="35" y="150" width="60" height="24" fill="#79c0ff" opacity="0.5"/><text x="65" y="166" font-size="7" text-anchor="middle" fill="#0d1117" font-family="sans-serif">Created</text>

  <text x="380" y="60" fill="#8b949e" font-size="8.5" font-family="sans-serif">order-42's events always arrive Created -&gt; Shipped</text>
  <text x="380" y="160" fill="#8b949e" font-size="8.5" font-family="sans-serif">order-99's events have no ordering vs. order-42's</text>
</svg>

Ordering is guaranteed within a partition (same key); there is no ordering promise across different partitions.

## 5. Runnable example

Scenario: an order lifecycle consumer that starts with a single unordered queue (showing out-of-order delivery corrupting state), then adds key-based partitioning so same-order events stay ordered, and finally runs multiple partitions concurrently to show ordering holds within each while different orders process independently in parallel.

### Level 1 — Basic

```java
// File: UnorderedQueueBug.java -- a single queue with concurrent workers gives NO ordering guarantee.
import java.util.*;
import java.util.concurrent.*;

public class UnorderedQueueBug {
    record Event(String orderId, String type) {}

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<Event> queue = new LinkedBlockingQueue<>();
        // two workers pulling from ONE shared queue -- delivery order to each worker isn't guaranteed
        // relative to the OTHER worker's processing time
        queue.put(new Event("order-42", "OrderCreated"));
        queue.put(new Event("order-42", "OrderShipped"));

        Map<String, List<String>> stateByOrder = new ConcurrentHashMap<>();
        ExecutorService pool = Executors.newFixedThreadPool(2); // TWO workers racing on the same queue
        Runnable worker = () -> {
            Event e;
            try {
                while ((e = queue.poll(200, TimeUnit.MILLISECONDS)) != null) {
                    Thread.sleep((long) (Math.random() * 50)); // simulated variable processing time
                    stateByOrder.computeIfAbsent(e.orderId(), k -> new CopyOnWriteArrayList<>()).add(e.type());
                }
            } catch (InterruptedException ignored) { }
        };
        pool.submit(worker); pool.submit(worker);
        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println("order-42 saw events in this order: " + stateByOrder.get("order-42"));
        System.out.println("(run repeatedly -- this can print [OrderShipped, OrderCreated], which is nonsensical)");
    }
}
```

**How to run:** `javac UnorderedQueueBug.java && java UnorderedQueueBug` (JDK 17+).

Because two workers race to pull from the same queue and each has its own random processing delay, `OrderShipped` can finish being recorded before `OrderCreated` — the queue delivers messages, but nothing guarantees the *order in which processing completes*.

### Level 2 — Intermediate

```java
// File: PartitionedByKey.java -- routing same-orderId events to the SAME partition,
// each partition processed sequentially by a single worker, restoring order.
import java.util.*;
import java.util.concurrent.*;

public class PartitionedByKey {
    record Event(String orderId, String type) {}

    static class PartitionedBroker {
        private final List<BlockingQueue<Event>> partitions;
        PartitionedBroker(int numPartitions) {
            partitions = new ArrayList<>();
            for (int i = 0; i < numPartitions; i++) partitions.add(new LinkedBlockingQueue<>());
        }
        void send(Event e) {
            int partitionIndex = Math.floorMod(e.orderId().hashCode(), partitions.size()); // SAME key -> SAME partition, always
            partitions.get(partitionIndex).offer(e);
        }
        BlockingQueue<Event> partition(int i) { return partitions.get(i); }
        int numPartitions() { return partitions.size(); }
    }

    public static void main(String[] args) throws InterruptedException {
        PartitionedBroker broker = new PartitionedBroker(4);
        broker.send(new Event("order-42", "OrderCreated"));
        broker.send(new Event("order-42", "OrderShipped"));
        broker.send(new Event("order-42", "OrderDelivered"));

        Map<String, List<String>> stateByOrder = new ConcurrentHashMap<>();
        ExecutorService pool = Executors.newFixedThreadPool(broker.numPartitions());
        // ONE worker per partition -- a partition is only ever drained by a single sequential worker
        for (int i = 0; i < broker.numPartitions(); i++) {
            BlockingQueue<Event> p = broker.partition(i);
            pool.submit(() -> {
                Event e;
                try {
                    while ((e = p.poll(200, TimeUnit.MILLISECONDS)) != null) {
                        stateByOrder.computeIfAbsent(e.orderId(), k -> new CopyOnWriteArrayList<>()).add(e.type());
                    }
                } catch (InterruptedException ignored) { }
            });
        }
        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);

        System.out.println("order-42 saw events in this order: " + stateByOrder.get("order-42"));
    }
}
```

**How to run:** `javac PartitionedByKey.java && java PartitionedByKey` (JDK 17+).

Expected output (always, on every run):
```
order-42 saw events in this order: [OrderCreated, OrderShipped, OrderDelivered]
```

Every event for `"order-42"` hashes to the same partition index and is drained by that partition's single dedicated worker, so it is processed strictly in send order — no race is even possible.

### Level 3 — Advanced

```java
// File: OrderedWithinPartitionParallelAcross.java -- proves ordering holds per-order
// WHILE multiple different orders are processed genuinely concurrently across partitions.
import java.util.*;
import java.util.concurrent.*;

public class OrderedWithinPartitionParallelAcross {
    record Event(String orderId, String type, long sentAtNanos) {}

    static class PartitionedBroker {
        private final List<BlockingQueue<Event>> partitions;
        PartitionedBroker(int numPartitions) {
            partitions = new ArrayList<>();
            for (int i = 0; i < numPartitions; i++) partitions.add(new LinkedBlockingQueue<>());
        }
        void send(String orderId, String type) {
            int idx = Math.floorMod(orderId.hashCode(), partitions.size());
            partitions.get(idx).offer(new Event(orderId, type, System.nanoTime()));
        }
        BlockingQueue<Event> partition(int i) { return partitions.get(i); }
        int numPartitions() { return partitions.size(); }
    }

    public static void main(String[] args) throws InterruptedException {
        PartitionedBroker broker = new PartitionedBroker(4);
        String[] stages = {"Created", "Shipped", "Delivered"};
        String[] orderIds = {"order-42", "order-99", "order-7"}; // multiple INDEPENDENT orders

        for (String stage : stages) {
            for (String orderId : orderIds) broker.send(orderId, "Order" + stage);
        }

        Map<String, List<String>> stateByOrder = new ConcurrentHashMap<>();
        ExecutorService pool = Executors.newFixedThreadPool(broker.numPartitions());
        for (int i = 0; i < broker.numPartitions(); i++) {
            BlockingQueue<Event> p = broker.partition(i);
            pool.submit(() -> {
                Event e;
                try {
                    while ((e = p.poll(200, TimeUnit.MILLISECONDS)) != null) {
                        Thread.sleep((long) (Math.random() * 20)); // varying processing time PER PARTITION, still fine
                        stateByOrder.computeIfAbsent(e.orderId(), k -> new CopyOnWriteArrayList<>()).add(e.type());
                    }
                } catch (InterruptedException ignored) { }
            });
        }
        pool.shutdown();
        pool.awaitTermination(2, TimeUnit.SECONDS);

        for (String orderId : orderIds) {
            System.out.println(orderId + ": " + stateByOrder.get(orderId));
        }
    }
}
```

**How to run:** `javac OrderedWithinPartitionParallelAcross.java && java OrderedWithinPartitionParallelAcross` (JDK 17+).

Expected output (order of the three *lines* may vary between runs, but each individual order's list is always `[OrderCreated, OrderShipped, OrderDelivered]`):
```
order-42: [OrderCreated, OrderShipped, OrderDelivered]
order-99: [OrderCreated, OrderShipped, OrderDelivered]
order-7: [OrderCreated, OrderShipped, OrderDelivered]
```

## 6. Walkthrough

1. **Level 1** — both worker threads poll the *same* `queue`, so which worker gets `OrderCreated` versus `OrderShipped` is a race; combined with each worker sleeping a random amount before recording its result, the two events can finish being recorded in either order, corrupting the expected `order-42` lifecycle.
2. **Level 2, routing by key** — `send` computes `Math.floorMod(e.orderId().hashCode(), partitions.size())`, a deterministic function of `orderId` alone, so every event for `"order-42"` — regardless of when it was sent — always resolves to the identical partition index.
3. **Level 2, one worker per partition** — the `for` loop submits exactly one task per partition, and each task's `while` loop only ever pulls from *that* partition's queue; since a `BlockingQueue` preserves FIFO order and only one thread ever drains a given partition, everything sent to that partition is processed in the exact order it was sent.
4. **Level 2, the guaranteed result** — because all three `order-42` events land in the same partition and that partition has exactly one sequential consumer, `[OrderCreated, OrderShipped, OrderDelivered]` is not merely likely, it is structurally guaranteed by the code — there is no race to win or lose.
5. **Level 3, multiple orders interleaved at send time** — the nested loop sends `Created` for all three orders, then `Shipped` for all three, then `Delivered` for all three, deliberately interleaving different orders' events in send order to make sure partitioning, not send timing, is what produces the correct per-order sequence.
6. **Level 3, partitions running truly in parallel** — each of the four partition workers runs on its own thread with its own random `Thread.sleep`, so partitions genuinely process at different, unpredictable speeds relative to each other — this models real concurrent partition consumers.
7. **Level 3, the outcome per order** — despite that cross-partition unpredictability, every individual order's list still comes out as `[OrderCreated, OrderShipped, OrderDelivered]`, because each order's three events, however they were interleaved with other orders' events at send time, always ended up in the same partition and were drained by that partition's single worker in FIFO order — proving ordering is preserved *within* a key while different keys are processed with full parallelism.

## 7. Gotchas & takeaways

> **Gotcha:** picking a partition key that is too coarse (e.g., partitioning by a fixed small `region` value instead of by `orderId`) forces unrelated messages to share a partition and lose the parallelism partitioning was supposed to provide; picking a key that is too fine-grained (e.g., a fresh random value per message) gives up ordering entirely, since no two related messages would reliably land on the same partition — the key must exactly match "the set of events that actually need to stay in order relative to each other."

- Ordering guarantees are almost never "all messages system-wide, in order" — they are "messages that share a key, in order relative to each other."
- Partitioning by a stable, meaningful key (like `orderId`) routes related events to the same partition, where a single sequential consumer preserves send order.
- Unrelated messages (different keys, different partitions) have no ordering relationship, and that is fine — most consumers never actually need it.
- The choice of partition key is a real design decision: too coarse loses parallelism, too fine loses the ordering guarantee that was the whole point.
- Systems like Kafka expose this model directly (partitions with per-partition ordering); understanding it explains why "Kafka guarantees ordering" is only true within a partition, not across the whole topic.
