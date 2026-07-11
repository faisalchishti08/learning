---
card: spring-cloud
gi: 90
slug: batch-consumers
title: "Batch consumers"
---

## 1. What it is

A batch consumer is a `Function`/`Consumer` bean that receives a `List<T>` of multiple messages in one invocation, rather than one message at a time — configured via `spring.cloud.stream.bindings.<binding>.consumer.batch-mode=true` — trading per-message invocation overhead for the efficiency of processing many messages together in a single call (one database batch insert instead of many individual ones, for instance).

```properties
spring.cloud.stream.bindings.handleOrderBatch-in-0.consumer.batch-mode=true
```

```java
@Bean
Function<List<OrderPlaced>, List<InvoiceRequested>> handleOrderBatch() {
    return orders -> {
        // one call handles the WHOLE batch -- e.g. one bulk database insert instead of N individual ones
        return orders.stream()
                .map(o -> new InvoiceRequested(o.orderId(), o.amount()))
                .toList();
    };
}
```

## 2. Why & when

Processing messages strictly one at a time means every downstream operation (a database write, an external API call) happens once per message — for a workload with real per-call overhead (database round-trip latency, API rate limits counted per call, transaction commit cost), batching many messages into fewer, larger downstream operations can be dramatically more efficient. Batch consumers deliver exactly the underlying batch the broker already groups messages into (Kafka polls return batches internally, for instance) directly to application code, rather than the framework artificially splitting that batch into individual calls.

Reach for batch consumers when:

- The downstream operation has meaningful per-call overhead that batching genuinely amortizes — a bulk database insert of 100 rows is typically far faster than 100 individual inserts, each paying its own round-trip and transaction cost.
- Throughput matters more than per-message processing latency — batch consumption trades "each message processed the instant it's ready" for "messages processed together, once enough have accumulated (or a timeout elapses)."
- The underlying broker already delivers messages in batches internally (true of Kafka's consumer poll model) — batch consumption avoids the overhead of the framework splitting an already-batched delivery into individual function invocations, only to potentially need to re-batch it downstream anyway.

## 3. Core concept

```
 per-message consumer (default):
   Function<OrderPlaced, InvoiceRequested>
   invoked ONCE per message -- N messages = N invocations = N downstream operations

 batch consumer:
   Function<List<OrderPlaced>, List<InvoiceRequested>>
   invoked ONCE per BATCH -- N messages, batched into groups of size B, = N/B invocations
   each invocation can perform ONE downstream operation covering the whole batch
```

The function signature itself changes from a single value to a `List` of values — the framework hands over however many messages the broker delivered together in one poll/fetch, rather than iterating and calling the function once per element.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A per message consumer makes one downstream database call per message while a batch consumer receives a whole group of messages at once and makes a single downstream call covering the entire batch">
  <rect x="20" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="165" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">per-message consumer</text>
  <text x="165" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">msg1-&gt;DB call, msg2-&gt;DB call, msg3-&gt;DB call</text>
  <text x="165" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3 messages = 3 downstream calls</text>

  <rect x="330" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">batch consumer</text>
  <text x="475" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">[msg1,msg2,msg3] -&gt; ONE bulk DB call</text>
  <text x="475" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3 messages = 1 downstream call</text>

  <defs><marker id="a90" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same three messages, dramatically different downstream call volume depending purely on which consumption mode is configured.

## 5. Runnable example

The scenario: persist `OrderPlaced` events to a database, measuring the difference batch consumption makes. Start with per-message consumption (many individual downstream calls), then add batch consumption, then measure the actual call-count difference across a realistic message volume.

### Level 1 — Basic

Per-message consumption — one downstream database call for every single message.

```java
import java.util.*;
import java.util.function.Function;

public class BatchConsumersLevel1 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static int databaseCallCount = 0;

    static void insertOne(InvoiceRequested invoice) {
        databaseCallCount++; // one call per message
    }

    static Function<OrderPlaced, InvoiceRequested> handleOrder =
            order -> new InvoiceRequested(order.orderId(), order.amount());

    public static void main(String[] args) {
        List<OrderPlaced> incoming = new ArrayList<>();
        for (int i = 1; i <= 100; i++) incoming.add(new OrderPlaced(String.valueOf(i), i * 1.0));

        for (OrderPlaced order : incoming) {
            InvoiceRequested invoice = handleOrder.apply(order);
            insertOne(invoice); // ONE database round-trip PER message
        }

        System.out.println("100 messages processed via " + databaseCallCount + " individual database calls");
    }
}
```

How to run: `java BatchConsumersLevel1.java`

100 messages produce 100 separate database calls — each one paying its own connection/transaction/network round-trip cost, even though a single bulk insert covering all 100 rows would very likely be dramatically faster overall.

### Level 2 — Intermediate

Add batch consumption: the function receives a `List<OrderPlaced>` and performs one bulk database call per batch instead of per message.

```java
import java.util.*;
import java.util.function.Function;

public class BatchConsumersLevel2 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static int databaseCallCount = 0;

    static void bulkInsert(List<InvoiceRequested> invoices) {
        databaseCallCount++; // ONE call for the WHOLE batch, regardless of batch size
    }

    // batch-mode signature: List<T> in, List<R> out
    static Function<List<OrderPlaced>, List<InvoiceRequested>> handleOrderBatch =
            orders -> orders.stream().map(o -> new InvoiceRequested(o.orderId(), o.amount())).toList();

    // models how the broker delivers messages already grouped into batches (e.g. one Kafka poll's worth)
    static List<List<OrderPlaced>> deliverInBatches(List<OrderPlaced> messages, int batchSize) {
        List<List<OrderPlaced>> batches = new ArrayList<>();
        for (int i = 0; i < messages.size(); i += batchSize) {
            batches.add(messages.subList(i, Math.min(i + batchSize, messages.size())));
        }
        return batches;
    }

    public static void main(String[] args) {
        List<OrderPlaced> incoming = new ArrayList<>();
        for (int i = 1; i <= 100; i++) incoming.add(new OrderPlaced(String.valueOf(i), i * 1.0));

        List<List<OrderPlaced>> batches = deliverInBatches(incoming, 20); // e.g. Kafka poll returns 20 at a time

        for (List<OrderPlaced> batch : batches) {
            List<InvoiceRequested> invoices = handleOrderBatch.apply(batch); // ONE call for 20 messages
            bulkInsert(invoices);
        }

        System.out.println("100 messages (in batches of 20) processed via " + databaseCallCount + " database calls");
    }
}
```

How to run: `java BatchConsumersLevel2.java`

`handleOrderBatch` is invoked once per batch of 20 messages, and `bulkInsert` is called once per batch too — 100 messages, delivered in batches of 20, produce just 5 database calls instead of 100, a 20x reduction in downstream call volume purely from restructuring how many messages are handled per invocation.

### Level 3 — Advanced

Measure the actual difference more explicitly across varying batch sizes, and handle a partial-batch failure — one bad message within a batch shouldn't necessarily need to fail the entire batch's downstream operation, depending on how the batch-level logic is written.

```java
import java.util.*;
import java.util.function.Function;

public class BatchConsumersLevel3 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static int databaseCallCount = 0;
    static List<String> failedOrderIds = new ArrayList<>();

    static void bulkInsert(List<InvoiceRequested> invoices) { databaseCallCount++; }

    static Function<List<OrderPlaced>, List<InvoiceRequested>> handleOrderBatch = orders -> {
        List<InvoiceRequested> results = new ArrayList<>();
        for (OrderPlaced order : orders) {
            if (order.amount() < 0) {
                // one malformed message within the batch -- handle it individually, don't fail the WHOLE batch
                failedOrderIds.add(order.orderId());
                continue;
            }
            results.add(new InvoiceRequested(order.orderId(), order.amount()));
        }
        return results;
    };

    static List<List<OrderPlaced>> deliverInBatches(List<OrderPlaced> messages, int batchSize) {
        List<List<OrderPlaced>> batches = new ArrayList<>();
        for (int i = 0; i < messages.size(); i += batchSize) {
            batches.add(messages.subList(i, Math.min(i + batchSize, messages.size())));
        }
        return batches;
    }

    public static void main(String[] args) {
        List<OrderPlaced> incoming = new ArrayList<>();
        for (int i = 1; i <= 50; i++) {
            double amount = (i == 27) ? -10.0 : i * 1.0; // one deliberately malformed message in the middle
            incoming.add(new OrderPlaced(String.valueOf(i), amount));
        }

        List<List<OrderPlaced>> batches = deliverInBatches(incoming, 10);
        for (List<OrderPlaced> batch : batches) {
            List<InvoiceRequested> invoices = handleOrderBatch.apply(batch);
            bulkInsert(invoices); // the batch containing the bad message still inserts its 9 GOOD messages
        }

        System.out.println("50 messages in batches of 10 -> " + databaseCallCount + " database calls");
        System.out.println("individually failed messages (not blocking their batch): " + failedOrderIds);
    }
}
```

How to run: `java BatchConsumersLevel3.java`

`handleOrderBatch` filters out the one malformed message (order `"27"`, with a negative amount) within its batch, adding it to `failedOrderIds` for separate handling, while still returning the other nine valid `InvoiceRequested` results from that same batch — `bulkInsert` still runs once for that batch, correctly persisting the nine good records rather than either silently including the bad one or failing the entire batch of ten over one bad message.

## 6. Walkthrough

Trace the batch containing the malformed message in Level 3.

1. `deliverInBatches` groups the 50 orders into 5 batches of 10 — the batch containing order `"27"` is the third batch (orders `21` through `30`, zero-indexed as `incoming.subList(20, 30)`).
2. When `handleOrderBatch.apply(batch)` is called on that specific batch, the `for` loop iterates all 10 orders within it. For order `"27"`, `order.amount() < 0` evaluates `true` (it was deliberately set to `-10.0`), so `failedOrderIds.add("27")` runs and `continue` skips adding anything to `results` for this one order.
3. The other nine orders in that same batch all have positive amounts, so each produces a normal `InvoiceRequested` added to `results`.
4. `handleOrderBatch` returns `results`, now containing 9 elements (not 10) for this particular batch — the malformed message was excluded, but the batch-level operation as a whole still completed successfully.
5. `bulkInsert(invoices)` runs for this batch exactly as it does for every other batch, inserting the 9 valid records — the one malformed message didn't need to fail or block the other nine perfectly good ones within the same batch.
6. The final `println` calls report `databaseCallCount` at `5` (still one call per batch, unaffected by the partial failure within one of them) and `failedOrderIds` containing exactly `["27"]` — a clean, auditable record of the one message needing individual attention, without it having compromised the batch efficiency for the other 49 messages.

```
batch 3 (orders 21-30): order 27 has amount=-10.0 (invalid)
   -> excluded from results, added to failedOrderIds
   -> other 9 orders in the SAME batch still processed normally
   -> bulkInsert still runs ONCE for this batch, persisting the 9 valid records

total: 5 database calls (one per batch of 10), 1 message flagged individually, 49 successfully persisted
```

## 7. Gotchas & takeaways

> **Gotcha:** batch consumption changes acknowledgment/commit semantics — depending on the broker and configuration, a failure partway through processing a batch can mean the *entire batch* is redelivered on retry (including messages that were already successfully processed before the failure), unlike per-message consumption where each message's success/failure is typically tracked independently. Understanding a specific broker's exact batch-acknowledgment behavior is essential before relying on batch consumption for genuinely critical data, and handling partial failures gracefully *within* the batch function itself (as Level 3 demonstrated) is often necessary to avoid reprocessing already-successful work.

- Batch consumption trades per-message processing simplicity for genuinely significant downstream efficiency gains, when the downstream operation has real per-call overhead that batching amortizes effectively.
- The function signature itself changes to `List<T>` in, `List<R>` out — this is a structurally different contract from the per-message `Function<T, R>` shape, not merely a configuration toggle on an otherwise-identical function.
- Handling a malformed or invalid message *within* a batch requires deliberate logic inside the batch function (filtering it out, as Level 3 did) — the framework doesn't automatically isolate individual bad messages within an otherwise-successful batch the way per-message dead-lettering (an earlier card) does for a single message's own delivery.
- Choose batch consumption specifically when downstream call overhead genuinely dominates — for lightweight, low-latency-per-message processing with no meaningful per-call cost to amortize, per-message consumption remains simpler and equally effective.
