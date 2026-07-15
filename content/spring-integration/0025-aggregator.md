---
card: spring-integration
gi: 25
slug: aggregator
title: "Aggregator"
---

## 1. What it is

`@Aggregator` is the endpoint archetype that reverses what `Splitter` (card 0024) does: it collects multiple related messages and combines them into a single outgoing message. It groups incoming messages by a correlation strategy (by default, the `correlationId` header a `Splitter` automatically stamps), holds them in a buffer until a release condition is satisfied (by default, once `sequenceSize` messages with a given `correlationId` have arrived), and then invokes an aggregation method with the full group, sending its single return value onward.

## 2. Why & when

You reach for `Aggregator` specifically when a flow split work into pieces upstream and now needs to recombine the results before proceeding:

- **A `Splitter` broke an order into individual line items for independent processing, and now the flow needs one confirmation message once every line item has been checked** — an `Aggregator` waits for all of them (matched by the correlation ID the splitter stamped) and combines their individual results into one summary.
- **Multiple independent requests need to be joined into a single response** — a scatter-gather pattern, where the same request goes out to several services and the flow needs to wait for all (or some) replies before proceeding — `Aggregator` is the "gather" half of that pattern.
- **You want group-completion logic isolated from the actual per-item processing** — the aggregation method only deals with "here's the full collected group, produce one result," entirely separate from whatever logic produced each individual message in the first place.

## 3. Core concept

Think of `Aggregator` like a warehouse dock waiting for every box of a multi-box shipment to arrive before assembling the final product — each box (an individual message) is checked in and set aside, tagged with the shipment's ID (the correlation ID), and only once every expected box has actually arrived does assembly begin. A box arriving alone doesn't get combined into anything by itself; it waits in the staging area until its siblings show up.

```java
@Aggregator(inputChannel = "lineItemResults", outputChannel = "orderSummary")
public OrderSummary combine(List<LineItemResult> results) {
    boolean allInStock = results.stream().allMatch(LineItemResult::inStock);
    return new OrderSummary(results.size(), allInStock);
}
```

Messages sent to `lineItemResults` are buffered by correlation ID; once a full group (by default, matching `sequenceSize`) has arrived, `combine` is invoked once with the whole `List<LineItemResult>`, and its single return value is sent to `orderSummary`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Aggregator buffers messages sharing a correlation ID until the full group arrives, then invokes the aggregation method once with the whole group, producing one outgoing message">
  <rect x="20" y="15" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="35" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">item 1/3 (corr=X)</text>
  <rect x="20" y="75" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">item 2/3 (corr=X)</text>
  <rect x="20" y="135" width="120" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="155" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">item 3/3 (corr=X)</text>

  <line x1="140" y1="30" x2="220" y2="80" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="140" y1="90" x2="220" y2="90" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="140" y1="150" x2="220" y2="100" stroke="#6db33f" stroke-width="1.5"/>

  <rect x="230" y="55" width="150" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="305" y="80" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Aggregator</text>
  <text x="305" y="97" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">buffer by correlationId</text>
  <text x="305" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">release when group full</text>

  <line x1="380" y1="90" x2="440" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#ag1)"/>

  <rect x="450" y="65" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="85" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">1 combined message</text>
  <text x="525" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">OrderSummary</text>

  <defs>
    <marker id="ag1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Three messages sharing correlation ID X are buffered until all three arrive, then combined into exactly one outgoing message — the reverse of `Splitter`'s (card 0024) one-to-many.

## 5. Runnable example

The scenario: line-item check results from a split order needing recombination into one summary, starting with a basic aggregator, then a partial-group timeout release, and finally a full split-then-aggregate round trip mirroring `Splitter`'s example.

### Level 1 — Basic

```java
// BasicAggregatorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class BasicAggregatorDemo {
    record LineItemResult(String sku, boolean inStock) {}
    record OrderSummary(int itemCount, boolean allInStock) {}

    public static void main(String[] args) {
        DirectChannel results = new DirectChannel();
        DirectChannel summary = new DirectChannel();
        summary.subscribe(m -> System.out.println("Combined summary: " + m.getPayload()));

        // what @Aggregator does for you: buffer by correlationId until sequenceSize is reached
        Map<String, List<Message<?>>> buffer = new ConcurrentHashMap<>();
        results.subscribe(m -> {
            String correlationId = (String) m.getHeaders().get("correlationId");
            int sequenceSize = (Integer) m.getHeaders().get("sequenceSize");
            List<Message<?>> group = buffer.computeIfAbsent(correlationId, k -> new ArrayList<>());
            group.add(m);
            if (group.size() == sequenceSize) { // full group arrived — release
                List<LineItemResult> items = group.stream().map(gm -> (LineItemResult) gm.getPayload()).toList();
                boolean allInStock = items.stream().allMatch(LineItemResult::inStock);
                summary.send(MessageBuilder.withPayload(new OrderSummary(items.size(), allInStock)).build());
                buffer.remove(correlationId);
            }
        });

        String corr = "order-42";
        results.send(MessageBuilder.withPayload(new LineItemResult("SKU-A", true))
            .setHeader("correlationId", corr).setHeader("sequenceSize", 2).build());
        results.send(MessageBuilder.withPayload(new LineItemResult("SKU-B", true))
            .setHeader("correlationId", corr).setHeader("sequenceSize", 2).build());
    }
}
```

How to run: `java BasicAggregatorDemo.java`. Expected output: `Combined summary: OrderSummary[itemCount=2, allInStock=true]` — printed only once, after both line-item messages arrived; the first message alone did not trigger any output.

### Level 2 — Intermediate

A group that never fully arrives (e.g., a service that never replies) would buffer forever without a release strategy beyond "wait for sequenceSize" — a `groupTimeout` releases whatever has arrived so far once a deadline passes, so a partial group can still be handled instead of leaking memory indefinitely.

```java
// TimeoutReleaseAggregatorDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;
import java.util.concurrent.*;

public class TimeoutReleaseAggregatorDemo {
    record LineItemResult(String sku, boolean inStock) {}

    public static void main(String[] args) throws InterruptedException {
        DirectChannel results = new DirectChannel();
        DirectChannel summary = new DirectChannel();
        summary.subscribe(m -> System.out.println("Released (possibly partial) group: " + m.getPayload()));

        Map<String, List<Message<?>>> buffer = new ConcurrentHashMap<>();
        int expectedSize = 3;
        String corr = "order-99";

        results.subscribe(m -> {
            List<Message<?>> group = buffer.computeIfAbsent(corr, k -> new ArrayList<>());
            group.add(m);
            System.out.println("Buffered " + group.size() + "/" + expectedSize + " for " + corr);
        });

        results.send(MessageBuilder.withPayload(new LineItemResult("SKU-A", true)).build());
        results.send(MessageBuilder.withPayload(new LineItemResult("SKU-B", false)).build());
        // SKU-C never arrives — simulating a service that never responded

        // groupTimeout equivalent: a scheduled release after waiting too long
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        scheduler.schedule(() -> {
            List<Message<?>> group = buffer.remove(corr);
            if (group != null) {
                List<LineItemResult> partial = group.stream().map(gm -> (LineItemResult) gm.getPayload()).toList();
                summary.send(MessageBuilder.withPayload(partial).build());
            }
            scheduler.shutdown();
        }, 500, TimeUnit.MILLISECONDS);

        Thread.sleep(700);
    }
}
```

How to run: `java TimeoutReleaseAggregatorDemo.java`. Expected output: two `Buffered N/3 for order-99` lines, then (after the 500ms timeout) `Released (possibly partial) group: [LineItemResult[sku=SKU-A, inStock=true], LineItemResult[sku=SKU-B, inStock=false]]` — the group was released with only 2 of the expected 3 items, since `SKU-C` never arrived and the timeout forced a decision rather than waiting forever.

### Level 3 — Advanced

A full split-then-aggregate round trip: an order is split into line items (as in card 0024's `Splitter`), each independently "checked" (simulating async, out-of-order completion), and the aggregator recombines them back into one summary — regardless of the order individual checks actually finish in.

```java
// SplitThenAggregateDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.*;
import java.util.concurrent.*;

public class SplitThenAggregateDemo {
    record LineItem(String sku, int quantity) {}
    record Order(String id, List<LineItem> lineItems) {}
    record LineItemResult(String sku, boolean inStock) {}
    record OrderSummary(String orderId, int itemCount, boolean allInStock) {}

    public static void main(String[] args) throws InterruptedException {
        DirectChannel orders = new DirectChannel();
        DirectChannel checkedItems = new DirectChannel();
        DirectChannel summary = new DirectChannel();
        CountDownLatch done = new CountDownLatch(1);

        summary.subscribe(m -> { System.out.println("Order summary: " + m.getPayload()); done.countDown(); });

        Map<String, List<Message<?>>> buffer = new ConcurrentHashMap<>();
        checkedItems.subscribe(m -> {
            String corr = (String) m.getHeaders().get("correlationId");
            int size = (Integer) m.getHeaders().get("sequenceSize");
            List<Message<?>> group = buffer.computeIfAbsent(corr, k -> new CopyOnWriteArrayList<>());
            group.add(m);
            if (group.size() == size) {
                List<LineItemResult> results = group.stream().map(gm -> (LineItemResult) gm.getPayload()).toList();
                boolean allInStock = results.stream().allMatch(LineItemResult::inStock);
                summary.send(MessageBuilder.withPayload(new OrderSummary("ORD-1", results.size(), allInStock)).build());
            }
        });

        ExecutorService pool = Executors.newFixedThreadPool(3);
        orders.subscribe(m -> {
            Order order = (Order) m.getPayload();
            String corr = "corr-" + order.id();
            for (LineItem item : order.lineItems()) {
                pool.submit(() -> { // simulate async, OUT-OF-ORDER completion
                    try { Thread.sleep((long) (Math.random() * 200)); } catch (InterruptedException ignored) {}
                    checkedItems.send(MessageBuilder.withPayload(new LineItemResult(item.sku(), true))
                        .setHeader("correlationId", corr).setHeader("sequenceSize", order.lineItems().size()).build());
                });
            }
        });

        orders.send(MessageBuilder.withPayload(new Order("ORD-1", List.of(
            new LineItem("SKU-A", 1), new LineItem("SKU-B", 2), new LineItem("SKU-C", 1)))).build());

        done.await();
        pool.shutdown();
    }
}
```

How to run: `java SplitThenAggregateDemo.java`. Expected output: exactly one `Order summary: OrderSummary[orderId=ORD-1, itemCount=3, allInStock=true]` line — even though the three line-item checks completed asynchronously and in a random, unpredictable order (due to the randomized sleep), the aggregator still correctly waited for all three before producing the single combined summary.

## 6. Walkthrough

Tracing `SplitThenAggregateDemo` in execution order:

1. `orders.send(...)` delivers the single `Order` to the splitter-shaped subscriber, which generates a shared correlation ID (`corr-ORD-1`) and submits three async tasks to a thread pool — one per line item — each of which will eventually send its own `LineItemResult` message.
2. Each pooled task sleeps a random duration (simulating variable-latency inventory checks) before sending its result to `checkedItems`, tagged with the shared correlation ID and `sequenceSize=3` — because the sleep durations differ, these three sends can complete in any order.
3. The aggregator's subscriber on `checkedItems` fires once per arriving result; each time, it adds the message to that correlation ID's buffered group and checks whether the group's size has reached the expected `sequenceSize`.
4. For the first two results to arrive (regardless of which SKUs they are), the group size is only 1 then 2 — below the threshold of 3 — so no summary is produced yet; the aggregator just keeps buffering.
5. Once the third and final result arrives, the group size reaches 3, matching `sequenceSize`; the aggregator now extracts all three buffered payloads, computes `allInStock` across the whole group, and sends exactly one `OrderSummary` message to `summary`.
6. The main thread, blocked on `done.await()`, unblocks once that single summary message is received and printed — regardless of the random completion order upstream, the aggregator guarantees exactly one combined result once the full group is present.

```
Order (1 message) --[Splitter-style]--> 3 async LineItemResult messages (arrive in RANDOM order)
                                              |
                                    [Aggregator buffers by correlationId]
                                              |
                              group size 1 -> 2 -> 3 (== sequenceSize) -> RELEASE
                                              |
                                    1 OrderSummary message
```

## 7. Gotchas & takeaways

> An `Aggregator` with no release strategy beyond "wait for the full group" will buffer indefinitely — and leak memory — if any expected message in a group never arrives (a downstream service that crashes, a split item that gets lost). Always configure either a `groupTimeout` (releasing whatever has arrived so far) or an explicit expiry/discard policy for incomplete groups in production; an unbounded wait is the aggregator-side equivalent of an unbounded `QueueChannel` (card 0010).

- `@Aggregator` buffers messages sharing a correlation strategy (by default, `correlationId`) until a release condition (by default, `sequenceSize`) is met, then invokes the aggregation method once with the full group, producing exactly one outgoing message.
- Use it to recombine results from a `Splitter` (card 0024), or to implement scatter-gather (multiple independent requests joined into one response).
- The order individual group members arrive in doesn't matter — the aggregator only cares that the expected group is eventually complete (or that a timeout forces a decision).
- Always configure a timeout or discard policy for incomplete groups; without one, a group missing even one expected message buffers forever.
- `Aggregator` and `Splitter` are natural pairs: split work out for independent/parallel processing, then aggregate results back into a single downstream message.
