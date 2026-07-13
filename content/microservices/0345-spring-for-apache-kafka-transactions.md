---
card: microservices
gi: 345
slug: spring-for-apache-kafka-transactions
title: "Spring for Apache Kafka transactions"
---

## 1. What it is

**Spring for Apache Kafka's transaction support** (`KafkaTransactionManager`, `@Transactional` on a method using a transactional `KafkaTemplate`) lets a service atomically produce multiple Kafka messages — or, with the right configuration, coordinate a Kafka publish with a database write via `ChainedTransactionManager` — so that either all the messages in a logical batch are committed to Kafka or none are, and consumers reading with `read_committed` isolation never see a partial, uncommitted batch.

## 2. Why & when

A service that needs to publish several related messages together — say, an `OrderPlaced` event and a `StockReservationRequested` command, produced from the same business operation — normally has no guarantee that both actually land: a crash between the two `send()` calls leaves one published and the other not, an instance of the [dual-write problem](0338-dual-write-problem.md) but purely within Kafka itself (multiple topics or partitions, not a database and a broker). Kafka transactions solve this specifically for multi-message and multi-partition atomicity: every message sent within the transaction is committed together, and importantly, `read_committed` consumers won't see *any* of them until the whole transaction commits, so no consumer ever observes a half-published batch.

Use Kafka transactions when a single logical operation must produce more than one related message atomically, particularly in **consume-transform-produce** pipelines — a service reads from one topic, transforms the data, and produces to another topic, wanting the "mark input as consumed" and "produce the output" to happen atomically together (this is what `KafkaTemplate.executeInTransaction` and `@Transactional` combined with a transactional producer achieve). It does not, by itself, make a Kafka publish and a *separate database write* atomic — that still requires either the [transactional outbox pattern](0331-transactional-outbox-pattern.md) or a `ChainedTransactionManager` coordinating both, which has its own tradeoffs.

## 3. Core concept

A Kafka producer configured as transactional (`transactional.id` set) can begin a transaction, send any number of messages across any number of topics/partitions, and either commit (all messages become visible to `read_committed` consumers atomically) or abort (none of them ever become visible). Spring wires this into the familiar `@Transactional` programming model via `KafkaTransactionManager`, so the same annotation style used for database transactions applies to Kafka producer operations.

```java
@Transactional("kafkaTransactionManager")
public void placeOrder(Order order) {
    kafkaTemplate.send("orders", order.getId(), toJson(order));
    kafkaTemplate.send("stock-requests", order.getId(), toStockRequestJson(order));
} // both messages commit together, or neither does
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A transactional producer sends two messages to two different topics inside one Kafka transaction; a read_committed consumer sees both messages together only after the transaction commits, never a partial view">
  <rect x="30" y="20" width="580" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Kafka transaction: send(orders) + send(stock-requests)</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">both PENDING until commit</text>

  <line x1="320" y1="70" x2="320" y2="110" stroke="#3fb950" marker-end="url(#a345)"/>
  <rect x="180" y="110" width="280" height="40" rx="6" fill="#1c2430" stroke="#3fb950"/>
  <text x="320" y="135" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">COMMIT -&gt; read_committed consumers see BOTH together</text>

  <defs><marker id="a345" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Multiple sends inside one Kafka transaction become visible to read_committed consumers together, atomically, or not at all.

## 5. Runnable example

Scenario: a service producing two related messages, first shown with independent, non-transactional sends where a crash leaves one message published and one lost, then fixed with a simulated Kafka transaction that commits or aborts both together, and finally extended to show a `read_committed`-style consumer that correctly never observes a partially-committed transaction.

### Level 1 — Basic

```java
// File: NonTransactionalSends.java -- two related messages sent
// INDEPENDENTLY; a failure after the FIRST send leaves it published with
// no corresponding second message.
import java.util.*;

public class NonTransactionalSends {
    static Map<String, List<String>> topics = new HashMap<>();

    static void send(String topic, String message) {
        topics.computeIfAbsent(topic, k -> new ArrayList<>()).add(message);
        System.out.println("sent to " + topic + ": " + message);
    }

    static void placeOrder(String orderId, boolean simulateFailureBeforeSecondSend) {
        send("orders", "OrderPlaced:" + orderId); // message 1: SUCCEEDS
        if (simulateFailureBeforeSecondSend) {
            System.out.println("CRASH before sending to stock-requests -- message 1 is ALREADY published, unpaired!");
            return;
        }
        send("stock-requests", "ReserveStock:" + orderId); // message 2: never sent in this run
    }

    public static void main(String[] args) {
        placeOrder("order-1", true);
        System.out.println("orders topic: " + topics.get("orders"));
        System.out.println("stock-requests topic: " + topics.getOrDefault("stock-requests", List.of())
                + " -- inventory service will NEVER see a stock request for this order!");
    }
}
```

How to run: `java NonTransactionalSends.java`

The two `send` calls are entirely independent. The simulated crash after the first prevents the second from ever running, leaving `"orders"` with a message that has no corresponding `"stock-requests"` message — any consumer relying on both existing together is left in an inconsistent view.

### Level 2 — Intermediate

```java
// File: TransactionalSendsCommitTogether.java -- both sends are wrapped
// in a SIMULATED Kafka transaction: messages are buffered as PENDING and
// only become "visible" (moved to the real topic) together, on commit;
// a failure discards BOTH.
import java.util.*;

public class TransactionalSendsCommitTogether {
    static Map<String, List<String>> committedTopics = new HashMap<>(); // what consumers can actually see
    static Map<String, List<String>> pendingInTransaction = new HashMap<>(); // buffered, not yet visible

    static void sendInTransaction(String topic, String message) {
        pendingInTransaction.computeIfAbsent(topic, k -> new ArrayList<>()).add(message);
        System.out.println("buffered (PENDING, not yet visible) to " + topic + ": " + message);
    }

    static void runKafkaTransaction(Runnable body) {
        pendingInTransaction.clear();
        boolean committed = false;
        try {
            body.run();
            committed = true;
        } finally {
            if (committed) {
                pendingInTransaction.forEach((topic, messages) ->
                        committedTopics.computeIfAbsent(topic, k -> new ArrayList<>()).addAll(messages));
                System.out.println("Kafka transaction COMMITTED -- all buffered messages now visible together");
            } else {
                System.out.println("Kafka transaction ABORTED -- all buffered messages DISCARDED, nothing becomes visible");
            }
        }
    }

    static void placeOrder(String orderId, boolean simulateFailure) {
        sendInTransaction("orders", "OrderPlaced:" + orderId);
        if (simulateFailure) throw new RuntimeException("failed before second send");
        sendInTransaction("stock-requests", "ReserveStock:" + orderId);
    }

    public static void main(String[] args) {
        try { runKafkaTransaction(() -> placeOrder("order-1", true)); } catch (RuntimeException ignored) {}
        System.out.println("orders (committed, visible): " + committedTopics.getOrDefault("orders", List.of())
                + " -- correctly EMPTY, the whole transaction aborted.");
    }
}
```

How to run: `java TransactionalSendsCommitTogether.java`

`sendInTransaction` only buffers messages into `pendingInTransaction`; nothing lands in `committedTopics` (what a consumer would actually see) until `runKafkaTransaction`'s `finally` block runs the commit path. Because `placeOrder` throws before its second send, `committed` stays `false`, so the abort branch discards the entire buffer — `committedTopics` correctly ends up with no `"orders"` entry at all, avoiding the unpaired-message problem Level 1 had.

### Level 3 — Advanced

```java
// File: ReadCommittedConsumerNeverSeesPartial.java -- simulates a
// read_committed CONSUMER: even if it polls WHILE a transaction is still
// open (messages buffered but not yet committed), it sees NOTHING from
// that in-flight transaction until commit -- never a partial view.
import java.util.*;

public class ReadCommittedConsumerNeverSeesPartial {
    static Map<String, List<String>> committedTopics = new HashMap<>();
    static Map<String, List<String>> pendingInTransaction = new HashMap<>();

    static void sendInTransaction(String topic, String message) {
        pendingInTransaction.computeIfAbsent(topic, k -> new ArrayList<>()).add(message);
    }

    static List<String> readCommittedConsumerPoll(String topic) { // ONLY ever reads committedTopics -- NEVER pendingInTransaction
        return committedTopics.getOrDefault(topic, List.of());
    }

    static void commitTransaction() {
        pendingInTransaction.forEach((topic, messages) ->
                committedTopics.computeIfAbsent(topic, k -> new ArrayList<>()).addAll(messages));
        pendingInTransaction.clear();
    }

    public static void main(String[] args) {
        sendInTransaction("orders", "OrderPlaced:order-1");
        sendInTransaction("stock-requests", "ReserveStock:order-1");

        System.out.println("--- transaction still OPEN, not yet committed ---");
        System.out.println("read_committed consumer polls 'orders': " + readCommittedConsumerPoll("orders")
                + " -- sees NOTHING yet, even though the message was already SENT (just not committed).");

        commitTransaction();

        System.out.println("--- transaction COMMITTED ---");
        System.out.println("read_committed consumer polls 'orders': " + readCommittedConsumerPoll("orders"));
        System.out.println("read_committed consumer polls 'stock-requests': " + readCommittedConsumerPoll("stock-requests")
                + " -- BOTH now visible together, atomically.");
    }
}
```

How to run: `java ReadCommittedConsumerNeverSeesPartial.java`

Both `sendInTransaction` calls only populate `pendingInTransaction`. `readCommittedConsumerPoll` is written to only ever read from `committedTopics`, modeling the real behavior of a Kafka consumer configured with `isolation.level=read_committed`: even though both messages have technically been sent to the broker at this point, a `read_committed` consumer's poll returns nothing for either topic, because the transaction hasn't committed yet. Only after `commitTransaction()` moves both buffered messages into `committedTopics` does the consumer's poll return them — and it returns both together, never one without the other.

## 6. Walkthrough

Trace `ReadCommittedConsumerNeverSeesPartial.main` in order. **First**, both `sendInTransaction` calls append their respective messages to `pendingInTransaction`, keyed by topic — `committedTopics` remains completely untouched at this point.

**Next**, `readCommittedConsumerPoll("orders")` is called while the transaction is still conceptually open. It reads `committedTopics.getOrDefault("orders", List.of())`, which returns an empty list, since nothing has been moved into `committedTopics` yet — this models the real guarantee that a `read_committed` consumer cannot see messages from a transaction that hasn't committed, even though those messages already exist in Kafka's internal, uncommitted state.

**Then**, `commitTransaction()` runs: it iterates `pendingInTransaction` and, for each topic, appends its buffered messages into the corresponding list in `committedTopics`, then clears `pendingInTransaction`.

**Finally**, `readCommittedConsumerPoll` is called for both `"orders"` and `"stock-requests"`. Both calls now read from `committedTopics`, which has been populated by the commit step — both return their respective messages, demonstrating that both became visible at the same moment, as a single atomic unit, rather than one appearing before the other.

```
sendInTransaction(orders)         -> pendingInTransaction={orders: [...]}          | committedTopics={} (consumer sees NOTHING)
sendInTransaction(stock-requests) -> pendingInTransaction={orders:[...], stock:[...]} | committedTopics={} (still nothing)
commitTransaction()                -> committedTopics gets BOTH topics' messages, atomically
consumer poll(orders)         -> now visible
consumer poll(stock-requests) -> now visible, together with orders
```

## 7. Gotchas & takeaways

> A Kafka transaction makes multiple produced messages atomic *within Kafka*, but does not, by itself, make a Kafka send and a separate database write atomic together — that still requires either a [transactional outbox pattern](0331-transactional-outbox-pattern.md) or a `ChainedTransactionManager`, each with real tradeoffs and added complexity. Don't assume `@Transactional` alone spanning a database call and a `kafkaTemplate.send` gives full atomicity without verifying the actual transaction manager configuration.

- Kafka transactions let a producer send multiple messages across topics/partitions atomically — all become visible together, or none do.
- Consumers must be configured with `isolation.level=read_committed` to get this guarantee; the default `read_uncommitted` would let a consumer see messages from a transaction that later aborts.
- This is especially valuable in consume-transform-produce pipelines, atomically coupling "mark input consumed" with "produce transformed output."
- Combining a Kafka transaction with a separate database transaction (via `ChainedTransactionManager`) is possible but adds real complexity — the [transactional outbox pattern](0331-transactional-outbox-pattern.md) remains the simpler, more common choice for that specific need.
