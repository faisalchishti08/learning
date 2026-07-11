---
card: spring-cloud
gi: 87
slug: reactive-functions
title: "Reactive functions"
---

## 1. What it is

Beyond the plain `Supplier<T>`/`Function<T, R>`/`Consumer<T>` shapes covered earlier, Spring Cloud Stream also supports reactive variants — `Function<Flux<T>, Flux<R>>`, `Supplier<Flux<T>>`, `Consumer<Flux<T>>` — operating on entire reactive streams of messages rather than one message at a time, letting Project Reactor operators (buffering, windowing, rate-limiting, backpressure handling) apply directly to the message flow itself.

```java
@Bean
Function<Flux<OrderPlaced>, Flux<InvoiceRequested>> handleOrders() {
    return orderFlux -> orderFlux
            .buffer(Duration.ofSeconds(5))          // group orders arriving within 5-second windows
            .flatMap(batch -> Flux.fromIterable(batch))
            .map(order -> new InvoiceRequested(order.orderId(), order.amount()));
}
```

## 2. Why & when

An imperative `Function<OrderPlaced, InvoiceRequested>` processes exactly one message per invocation — for logic that genuinely needs to reason across *multiple* messages together (batching a window of events, deduplicating within a time period, rate-limiting the effective processing speed), reactive stream operators express that far more naturally than manually accumulating state across separate imperative function calls.

Reach for reactive function signatures when:

- Processing genuinely needs to operate on windows or batches of messages together, not one at a time — `Flux.buffer`, `Flux.window`, and similar operators express this declaratively, where the imperative model would require hand-rolled accumulation state.
- Backpressure matters — a slow downstream consumer (a database write, a third-party API call) shouldn't be overwhelmed by an unbounded rate of incoming messages; reactive streams' backpressure protocol is a first-class part of the model, not something bolted on afterward.
- The rest of the application is already built reactively (WebFlux controllers, reactive repositories) — keeping the messaging layer reactive too avoids an awkward blocking/non-blocking boundary inside the same request-processing pipeline.

## 3. Core concept

```
 imperative:  Function<OrderPlaced, InvoiceRequested>
     called ONCE per message, no visibility into surrounding messages

 reactive:    Function<Flux<OrderPlaced>, Flux<InvoiceRequested>>
     called ONCE at startup, returns a PIPELINE that processes the entire ongoing stream
     Reactor operators (buffer, window, filter, flatMap, ...) apply to the stream itself
```

The reactive shape isn't "the same function, called differently" — it's a fundamentally different unit of composition: a pipeline definition over an entire stream, not a per-message handler.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An imperative function is invoked once per incoming message with no visibility into neighboring messages, while a reactive function defines one pipeline over the entire stream, letting operators like buffer group multiple messages together">
  <rect x="20" y="20" width="280" height="70" rx="10" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">imperative Function&lt;T, R&gt;</text>
  <text x="160" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">called once PER message</text>
  <text x="160" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">no visibility across messages</text>

  <rect x="330" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">reactive Function&lt;Flux&lt;T&gt;, Flux&lt;R&gt;&gt;</text>
  <text x="475" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">defined ONCE over the whole stream</text>
  <text x="475" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">buffer/window/filter across many messages</text>

  <defs><marker id="a87" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

An imperative function processes messages one at a time in isolation; a reactive function shapes the entire flow of messages as one continuous pipeline.

## 5. Runnable example

The scenario: batch and process `OrderPlaced` events in time windows. Start with imperative per-message processing (no batching possible), then add a simplified reactive-style buffering pipeline, then add backpressure-aware rate limiting on top.

### Level 1 — Basic

Imperative, per-message processing — no way to group related messages together.

```java
import java.util.function.Function;

public class ReactiveFunctionsLevel1 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceRequested(String orderId, double amount) {}

    static Function<OrderPlaced, InvoiceRequested> handleOrder =
            order -> new InvoiceRequested(order.orderId(), order.amount());

    public static void main(String[] args) {
        // each call is completely independent -- no way to, say, batch these three into one downstream call
        System.out.println(handleOrder.apply(new OrderPlaced("1", 10.0)));
        System.out.println(handleOrder.apply(new OrderPlaced("2", 20.0)));
        System.out.println(handleOrder.apply(new OrderPlaced("3", 30.0)));
    }
}
```

How to run: `java ReactiveFunctionsLevel1.java`

Each call to `handleOrder.apply(...)` is entirely independent — there's no natural way, using this imperative shape alone, to group these three orders into a single batched downstream operation, even if that were genuinely more efficient.

### Level 2 — Intermediate

Add a simplified reactive-style pipeline, modeling `Flux.buffer` grouping messages before processing them as a batch.

```java
import java.util.*;
import java.util.function.Function;
import java.util.stream.*;

public class ReactiveFunctionsLevel2 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceBatch(List<String> orderIds, double totalAmount) {}

    // models Function<Flux<OrderPlaced>, Flux<InvoiceBatch>> using a plain List as a simplified stand-in for Flux
    static Function<List<OrderPlaced>, List<InvoiceBatch>> handleOrdersBatched = orders -> {
        // models .buffer(3) -- group every 3 incoming messages into one batch
        List<InvoiceBatch> batches = new ArrayList<>();
        for (int i = 0; i < orders.size(); i += 3) {
            List<OrderPlaced> chunk = orders.subList(i, Math.min(i + 3, orders.size()));
            double total = chunk.stream().mapToDouble(OrderPlaced::amount).sum();
            batches.add(new InvoiceBatch(chunk.stream().map(OrderPlaced::orderId).toList(), total));
        }
        return batches;
    };

    public static void main(String[] args) {
        List<OrderPlaced> incoming = List.of(
                new OrderPlaced("1", 10.0), new OrderPlaced("2", 20.0), new OrderPlaced("3", 30.0),
                new OrderPlaced("4", 15.0), new OrderPlaced("5", 25.0)
        );

        List<InvoiceBatch> result = handleOrdersBatched.apply(incoming);
        result.forEach(System.out::println);
    }
}
```

How to run: `java ReactiveFunctionsLevel2.java`

`handleOrdersBatched` processes the *entire* incoming collection as one unit, grouping every three orders into one `InvoiceBatch` — five orders produce two batches: one with three orders totaling `60.0`, and one with the remaining two totaling `40.0`. This is exactly the shape `.buffer(3)` provides on a real `Flux`: grouping a continuous stream of individual messages into batches for more efficient downstream processing (fewer, larger database writes or API calls instead of many small ones).

### Level 3 — Advanced

Add backpressure-aware rate limiting on top of batching, modeling how a slow downstream consumer's capacity constrains how fast batches are actually processed, rather than the pipeline blindly processing everything as fast as messages arrive.

```java
import java.util.*;
import java.util.function.Function;

public class ReactiveFunctionsLevel3 {
    record OrderPlaced(String orderId, double amount) {}
    record InvoiceBatch(List<String> orderIds, double totalAmount) {}

    static List<InvoiceBatch> processedBatches = new ArrayList<>();
    static int downstreamCapacityPerTick = 1; // models a slow downstream that can only absorb 1 batch per "tick"

    static List<InvoiceBatch> batch(List<OrderPlaced> orders, int batchSize) {
        List<InvoiceBatch> batches = new ArrayList<>();
        for (int i = 0; i < orders.size(); i += batchSize) {
            List<OrderPlaced> chunk = orders.subList(i, Math.min(i + batchSize, orders.size()));
            double total = chunk.stream().mapToDouble(OrderPlaced::amount).sum();
            batches.add(new InvoiceBatch(chunk.stream().map(OrderPlaced::orderId).toList(), total));
        }
        return batches;
    }

    // models backpressure: only pull as many batches as the downstream can currently absorb, per tick
    static void processWithBackpressure(List<InvoiceBatch> allBatches) {
        int tick = 0;
        int index = 0;
        while (index < allBatches.size()) {
            tick++;
            int end = Math.min(index + downstreamCapacityPerTick, allBatches.size());
            List<InvoiceBatch> thisTick = allBatches.subList(index, end);
            for (InvoiceBatch b : thisTick) {
                System.out.println("tick " + tick + ": downstream absorbs " + b);
                processedBatches.add(b);
            }
            index = end;
        }
    }

    public static void main(String[] args) {
        List<OrderPlaced> incoming = new ArrayList<>();
        for (int i = 1; i <= 9; i++) incoming.add(new OrderPlaced(String.valueOf(i), i * 10.0));

        List<InvoiceBatch> batches = batch(incoming, 3); // 9 orders -> 3 batches of 3
        System.out.println("total batches ready: " + batches.size());

        processWithBackpressure(batches); // downstream absorbs only 1 batch per tick, even though 3 are ready
        System.out.println("all " + processedBatches.size() + " batches eventually processed, at the downstream's own pace");
    }
}
```

How to run: `java ReactiveFunctionsLevel3.java`

`processWithBackpressure` only feeds `downstreamCapacityPerTick` batches per tick, regardless of how many are actually ready upstream — modeling how Reactor's backpressure protocol lets a slow subscriber (the downstream) signal how much it can currently handle, rather than the publisher pushing everything at once and overwhelming it. Three batches are ready immediately, but they're consumed one tick at a time, matching the downstream's own declared capacity — exactly the protection reactive streams provide against a fast producer overwhelming a slow consumer.

## 6. Walkthrough

Trace `processWithBackpressure`'s execution in Level 3.

1. `batch(incoming, 3)` runs first, grouping the 9 incoming orders into 3 batches of 3 orders each — this models a `.buffer(3)` operator having already run on the upstream `Flux<OrderPlaced>`, producing a `Flux<InvoiceBatch>` with 3 elements ready to flow downstream.
2. `processWithBackpressure(batches)` runs — `tick` starts at `0`, `index` at `0`. The `while` loop's first iteration increments `tick` to `1`, computes `end = min(0 + 1, 3) = 1` (since `downstreamCapacityPerTick = 1`), and takes `thisTick = batches.subList(0, 1)` — just the first batch.
3. The inner `for` loop processes that single batch, printing `"tick 1: downstream absorbs ..."` and adding it to `processedBatches`. `index` is updated to `1`.
4. The `while` loop's second iteration increments `tick` to `2`, computes `end = min(1 + 1, 3) = 2`, takes `thisTick = batches.subList(1, 2)` — the second batch, processed and printed as `"tick 2: ..."`. `index` becomes `2`.
5. The third iteration increments `tick` to `3`, computes `end = min(2 + 1, 3) = 3`, processes the third and final batch as `"tick 3: ..."`, `index` becomes `3`, and the `while` loop's condition (`index < allBatches.size()`, `3 < 3`) is now false, ending the loop.
6. Even though all 3 batches were ready and available from the very start, they were only ever processed one per tick, matching `downstreamCapacityPerTick` — this models exactly the effect Reactor's backpressure has on a real reactive pipeline: a fast producer's output rate is throttled to match what a slower consumer can actually absorb, rather than overwhelming it.

```
3 batches ready immediately (upstream production is fast)
downstream capacity: 1 batch per tick (downstream consumption is slow)

tick 1: absorb batch 1  (batches 2, 3 wait)
tick 2: absorb batch 2  (batch 3 waits)
tick 3: absorb batch 3  (done)

producer never overwhelmed the consumer -- consumption paced to the consumer's own declared capacity
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing reactive (`Flux`-based) and imperative (plain-object) function signatures within the same application is possible, but each individual binding must consistently use one style or the other — a `Function<Flux<T>, Flux<R>>` and a `Function<T, R>` are fundamentally different programming models, not interchangeable at the binding level, and accidentally mismatching the declared type against what the binder actually expects produces a startup or runtime type error rather than silently working either way.

- Reactive function signatures (`Function<Flux<T>, Flux<R>>`) shift the unit of composition from "one message at a time" to "the entire stream as a pipeline," unlocking Reactor operators like `buffer`, `window`, and rate-limiting that have no natural imperative equivalent without hand-rolled state.
- Backpressure is a first-class, built-in part of the reactive model — a slow downstream consumer can signal reduced capacity, and the pipeline respects it automatically, rather than needing manually-implemented throttling logic bolted on afterward.
- Reach for reactive functions specifically when cross-message logic (batching, windowing, deduplication over time) or genuine backpressure concerns are present — for straightforward one-message-in, one-message-out processing, the plain imperative `Function<T, R>` shape (from the earlier functional model card) remains simpler and equally valid.
- Keeping the messaging layer's programming style consistent with the rest of the application (fully reactive throughout, or fully imperative/blocking throughout) avoids an awkward, error-prone boundary where the two models have to interoperate within one request-processing pipeline.
