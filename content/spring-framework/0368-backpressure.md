---
card: spring-framework
gi: 368
slug: backpressure
title: "Backpressure"
---

## 1. What it is

Backpressure is the mechanism by which a slow consumer (subscriber) tells a fast producer (publisher) to slow down, rather than being overwhelmed by data arriving faster than it can process — implemented in Reactive Streams via `Subscription.request(n)` (the previous card's specification). Without backpressure, a fast producer and a slow consumer would either force unbounded memory growth (buffering everything the consumer hasn't caught up on) or drop data silently — both dangerous failure modes reactive programming is specifically designed to avoid.

```java
Flux.range(1, 1_000_000)
    .onBackpressureBuffer(1000)   // explicit strategy: buffer up to 1000, then apply a fallback
    .subscribe(new BaseSubscriber<Integer>() {
        @Override
        protected void hookOnSubscribe(Subscription s) {
            request(10);   // only ask for 10 at a time
        }
        @Override
        protected void hookOnNext(Integer value) {
            process(value);
            request(1);   // ask for one more after processing each
        }
    });
```

## 2. Why & when

Imagine a fast producer (a database streaming millions of rows) feeding a slow consumer (writing each row to a rate-limited external API, one at a time). Without backpressure, the producer would keep emitting rows as fast as it can read them, and something has to give: either the consumer's input buffer grows unboundedly (eventually causing an `OutOfMemoryError`), or rows get silently dropped, or the whole system deadlocks trying to apply artificial blocking to prevent the first two outcomes.

Backpressure solves this at the protocol level: the *consumer* decides how much it can handle, and the producer is contractually obligated to respect that limit. This matters whenever:

- You're processing a genuinely large or unbounded stream (a live event feed, a huge database export, an infinite `Flux.interval`) where the consumer's processing rate is a real constraint.
- Downstream systems have rate limits (an external API you shouldn't hammer) and you want the reactive pipeline to naturally throttle to match.
- You want explicit, deliberate control over buffering behavior (how much to buffer, and what to do when the buffer fills) rather than accepting an implicit, potentially unsafe default.

## 3. Core concept

```
Unbounded request (Flux operators mostly do this by default):

  subscription.request(Long.MAX_VALUE)   <- "send me everything, as fast as you can"
  This effectively DISABLES backpressure for that subscription — fine when
  the consumer genuinely can keep up (most in-memory transformation pipelines).

Explicit, bounded request (backpressure IN EFFECT):

  subscription.request(10)   <- "send me AT MOST 10, then wait for more requests"
  publisher MUST NOT send an 11th item until MORE demand is requested

When the producer is faster than the consumer's requested rate, overflow
strategies decide what happens to the EXCESS:

  onBackpressureBuffer(n)   — queue up to n excess items (THEN error/drop/block, configurable)
  onBackpressureDrop()      — silently DISCARD items the consumer hasn't requested yet
  onBackpressureLatest()    — keep only the MOST RECENT unconsumed item, drop older ones
  onBackpressureError()     — signal an ERROR if demand is exceeded (fail loudly, don't buffer)

Choosing a strategy is a real design decision, not a technicality:
  a live stock ticker -> onBackpressureLatest() makes sense (old prices are stale anyway)
  a financial transaction log -> onBackpressureError() or careful buffering (can't lose data)
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Backpressure: consumer-controlled demand vs producer speed</text>

  <rect x="20" y="50" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="72" text-anchor="middle" fill="#6db33f" font-size="10">Fast Producer</text>
  <text x="120" y="90" text-anchor="middle" fill="#8b949e" font-size="9">can emit 10,000/sec</text>

  <line x1="220" y1="80" x2="520" y2="80" stroke="#8b949e" marker-end="url(#a44)"/>
  <text x="370" y="72" text-anchor="middle" fill="#8b949e" font-size="9">request(10) -&gt; onNext × 10 -&gt; wait</text>

  <rect x="520" y="50" width="200" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="620" y="72" text-anchor="middle" fill="#79c0ff" font-size="10">Slow Consumer</text>
  <text x="620" y="90" text-anchor="middle" fill="#8b949e" font-size="9">processes 100/sec</text>

  <rect x="220" y="140" width="300" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="370" y="170" text-anchor="middle" fill="#8b949e" font-size="10">producer PAUSES until more demand requested</text>

  <defs>
    <marker id="a44" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*The consumer's `request(n)` calls throttle the producer to a pace it can actually sustain.*

## 5. Runnable example

### Level 1 — Basic

A custom `BaseSubscriber` explicitly controlling demand, one item at a time, to observe backpressure directly:

```java
// ManualDemandDemo.java
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Flux;

public class ManualDemandDemo {

    public static void main(String[] args) throws InterruptedException {
        Flux<Integer> source = Flux.range(1, 10)
            .doOnRequest(n -> System.out.println("Producer: received request for " + n));

        source.subscribe(new BaseSubscriber<Integer>() {
            @Override
            protected void hookOnSubscribe(Subscription subscription) {
                System.out.println("Subscriber: requesting 1 item");
                request(1);
            }

            @Override
            protected void hookOnNext(Integer value) {
                System.out.println("Subscriber: processing " + value);
                try { Thread.sleep(100); } catch (InterruptedException ignored) {}
                System.out.println("Subscriber: requesting 1 more");
                request(1);
            }

            @Override
            protected void hookOnComplete() {
                System.out.println("Subscriber: complete");
            }
        });

        Thread.sleep(1500);
    }
}
```

**How to run:**
```bash
java ManualDemandDemo.java
# Subscriber: requesting 1 item
# Producer: received request for 1
# Subscriber: processing 1
# Subscriber: requesting 1 more
# Producer: received request for 1
# Subscriber: processing 2
# ... (repeats for 3 through 10, one at a time)
# Subscriber: complete
```

The producer only ever emits **one** item per `request(1)` call — even though `Flux.range(1, 10)` could produce all ten values instantly, the subscriber's deliberate one-at-a-time demand strictly paces the flow, and `doOnRequest` makes each individual request call visible in the log.

### Level 2 — Intermediate

Comparing overflow strategies (`onBackpressureDrop` vs `onBackpressureLatest`) when a producer genuinely outpaces a slow consumer, using `Flux.interval` (a real, time-driven, potentially-infinite source):

```java
// OverflowStrategyDemo.java
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;

public class OverflowStrategyDemo {

    public static void main(String[] args) throws InterruptedException {
        System.out.println("--- onBackpressureDrop ---");
        Flux.interval(Duration.ofMillis(10))               // producer: 100 items/sec
            .onBackpressureDrop(dropped -> System.out.println("  dropped: " + dropped))
            .publishOn(Schedulers.boundedElastic(), 1)      // downstream processes ONE at a time
            .subscribe(value -> {
                slowlyProcess(value, 100);                  // consumer: only ~10 items/sec
            });

        Thread.sleep(500);

        System.out.println("--- onBackpressureLatest ---");
        Flux.interval(Duration.ofMillis(10))
            .onBackpressureLatest()
            .publishOn(Schedulers.boundedElastic(), 1)
            .subscribe(value -> {
                slowlyProcess(value, 100);
            });

        Thread.sleep(500);
    }

    static void slowlyProcess(Long value, long delayMs) {
        System.out.println("  processing: " + value);
        try { Thread.sleep(delayMs); } catch (InterruptedException ignored) {}
    }
}
```

**How to run:**
```bash
java OverflowStrategyDemo.java
# --- onBackpressureDrop ---
#   processing: 0
#   dropped: 1
#   dropped: 2
#   ... (many drops while item 0 is being slowly processed)
#   processing: 3
#   dropped: 4
# ... (roughly every ~10th interval item actually gets processed; the rest are dropped)
#
# --- onBackpressureLatest ---
#   processing: 0
#   processing: N   (whichever value was MOST RECENT when the consumer became ready again)
# ... (similar pacing, but ALWAYS the freshest available value, never an arbitrarily old dropped one)
```

**What changed:** `onBackpressureDrop` discards *any* item the slow consumer isn't ready for the instant it arrives — including potentially the very next, most-relevant one. `onBackpressureLatest` instead always keeps the *most recent* unconsumed item, discarding only older ones as newer ones arrive — appropriate for something like a live sensor reading or stock price, where an old, stale value is actively worse than no value at all, and only the freshest matters once the consumer catches up.

### Level 3 — Advanced

Production concern: bounded buffering with an explicit overflow strategy and monitoring — the realistic middle ground between "unlimited buffer" (risks OOM) and "drop everything the consumer can't immediately handle" (risks silent data loss for cases where every item matters):

```java
// BoundedBufferDemo.java
import reactor.core.publisher.Flux;
import reactor.core.publisher.FluxSink;
import reactor.core.scheduler.Schedulers;
import reactor.util.concurrent.Queues;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicLong;

public class BoundedBufferDemo {

    record Order(long id, double amount) {}

    public static void main(String[] args) throws InterruptedException {
        AtomicLong processedCount = new AtomicLong(0);
        AtomicLong errorCount = new AtomicLong(0);

        // Simulates a BURSTY producer — orders arriving faster than they can be
        // written to a (simulated) slow downstream payment-processing system.
        Flux<Order> orderStream = Flux.create(sink -> {
            for (long i = 1; i <= 50; i++) {
                sink.next(new Order(i, 19.99 * i));
            }
            sink.complete();
        }, FluxSink.OverflowStrategy.BUFFER);

        orderStream
            // Bounded buffer: hold up to 20 unconsumed orders; if that fills,
            // signal an ERROR rather than growing unboundedly or silently
            // dropping a financial transaction (data loss is NOT acceptable here).
            .onBackpressureBuffer(
                20,
                dropped -> System.out.println("BUFFER FULL — rejected order: " + dropped),
                reactor.util.concurrent.Queues.SMALL_BUFFER_SIZE > 0
                    ? reactor.core.publisher.BufferOverflowStrategy.ERROR
                    : reactor.core.publisher.BufferOverflowStrategy.ERROR)
            .publishOn(Schedulers.boundedElastic(), 1)
            .doOnError(ex -> System.out.println("Pipeline failed: " + ex.getMessage()))
            .doOnNext(order -> {
                processSlowly(order);
                processedCount.incrementAndGet();
            })
            .onErrorResume(ex -> {
                errorCount.incrementAndGet();
                return Flux.empty();
            })
            .blockLast();   // ONLY acceptable here because main() needs to wait — never in a real handler

        System.out.println("Processed: " + processedCount.get() + ", Errors: " + errorCount.get());
    }

    static void processSlowly(Order order) {
        try { Thread.sleep(20); } catch (InterruptedException ignored) {}   // simulated slow downstream call
    }
}
```

**How to run:**
```bash
java BoundedBufferDemo.java
# processing continues until the buffer of 20 fills faster than the consumer drains it
# BUFFER FULL — rejected order: Order[id=..., amount=...]
# Pipeline failed: ... (Queue is full / overflow)
# Processed: <some number less than 50>, Errors: 1
```

**What changed and why:**
- `onBackpressureBuffer(20, droppedHandler, BufferOverflowStrategy.ERROR)` establishes an explicit, bounded buffer size (`20`) rather than either extreme — this genuinely protects memory from unbounded growth while still absorbing reasonable, short-lived bursts that a fully synchronous, un-buffered approach would reject immediately.
- Choosing `BufferOverflowStrategy.ERROR` (rather than silently dropping) reflects a deliberate business decision: for financial `Order` data, silently losing a transaction is unacceptable, so exceeding the buffer's capacity should be a loud, observable failure (logged, alerted on, and handled explicitly via `onErrorResume`) rather than quietly discarding customer orders.
- `doOnNext`/`onErrorResume` together demonstrate handling the two possible outcomes for each item explicitly: successful processing increments a counter, while the buffer-overflow error path is caught, logged as a metric (`errorCount`), and the pipeline recovers with `Flux.empty()` rather than crashing the entire stream over what might be a transient burst.

## 6. Walkthrough

**Execution: `ManualDemandDemo.main()` (Level 1 code), tracing the request/emit cycle precisely.**

1. `source.subscribe(new BaseSubscriber<Integer>() {...})` triggers the subscription. Per the Reactive Streams protocol, this causes `hookOnSubscribe(subscription)` to be called first, before any data flows.
2. Inside `hookOnSubscribe`: the subscriber prints its intent and calls `request(1)` — explicitly telling the upstream `Flux.range(1, 10)` (wrapped with `doOnRequest` for visibility) "you may emit exactly one item right now."
3. `doOnRequest`'s callback fires, printing `"Producer: received request for 1"` — confirming the request signal reached the source.
4. `Flux.range` emits its first value, `1`, triggering `hookOnNext(1)` on the subscriber.
5. Inside `hookOnNext`: the subscriber prints `"processing 1"`, sleeps 100ms (simulating real work), then calls `request(1)` **again** — this is the critical step that keeps the flow going. Without this second `request(1)` call, the producer would never emit a second item; the flow would simply stop after the first, since no further demand was ever signaled.
6. This triggers another `doOnRequest` log line, then `Flux.range` emits `2`, triggering another `hookOnNext(2)` call.
7. This cycle (process, sleep, request one more) repeats for values `3` through `10` — each iteration strictly gated by the subscriber's own `request(1)` call, never running ahead of the consumer's actual processing pace.
8. After emitting `10` (the range's last value) and receiving the corresponding acknowledgment via the next `hookOnNext` completing its cycle, `Flux.range` has no more values to emit — it signals completion, triggering `hookOnComplete()`, which prints `"Subscriber: complete"`.

The key insight demonstrated end-to-end: at no point does the producer emit an item the subscriber hasn't explicitly asked for — the entire ten-item sequence is paced exactly to the subscriber's own processing rate (roughly one item per 100ms, matching the `Thread.sleep(100)` in `hookOnNext`), even though `Flux.range` itself is fully capable of producing all ten values essentially instantaneously.

## 7. Gotchas & takeaways

> **Most everyday Reactor operator chains use *unbounded* request internally (`request(Long.MAX_VALUE)`) unless you explicitly customize demand** — backpressure exists and is available, but for typical in-memory transformation pipelines where the consumer can easily keep pace, you generally don't need to manage it manually. Reach for explicit demand control (as in these examples) specifically when a genuine speed mismatch between producer and consumer exists.

> **Choosing `onBackpressureDrop`/`onBackpressureLatest` for data where every item matters (financial transactions, audit logs) is a serious correctness bug, not just a performance tuning choice** — these strategies are explicitly designed to lose data under pressure. Reserve them for genuinely "only the latest matters" scenarios (live prices, sensor readings, UI state updates); use `onBackpressureBuffer` with an error/block strategy for anything where data loss is unacceptable.

> **An unbounded `onBackpressureBuffer()` (no capacity argument) can still cause an `OutOfMemoryError` under sustained producer/consumer speed mismatch** — always specify an explicit, reasoned capacity and overflow strategy rather than relying on the no-argument default, which effectively just delays the same unbounded-growth problem backpressure exists to prevent.

- Backpressure lets a slow consumer explicitly control how much data a fast producer sends, via `Subscription.request(n)`, preventing unbounded buffering or silent data loss.
- Overflow strategies (`buffer`, `drop`, `latest`, `error`) represent real, deliberate business tradeoffs about what should happen when a producer genuinely outpaces a consumer — choose based on whether losing individual items is acceptable for the data in question.
- Most everyday reactive pipelines use unbounded (effectively backpressure-free) demand implicitly — explicit demand management matters specifically for genuine, sustained speed mismatches between producer and consumer.
- For data where loss is unacceptable, use a bounded buffer with an `ERROR` (or blocking) overflow strategy, paired with explicit error handling — never rely on unbounded buffering as a substitute for genuine capacity planning.
