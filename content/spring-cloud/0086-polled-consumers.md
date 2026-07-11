---
card: spring-cloud
gi: 86
slug: polled-consumers
title: "Polled consumers"
---

## 1. What it is

Most Spring Cloud Stream consumers are event-driven — the framework calls your `Function`/`Consumer` automatically whenever a message arrives. A `PollableMessageSource` inverts this: your code explicitly calls `.poll(...)` on a schedule or trigger of its own choosing, pulling one message at a time, rather than being invoked reactively by the framework the instant a message is available.

```java
@Bean
ApplicationRunner poller(PollableMessageSource source) {
    return args -> {
        while (true) {
            boolean received = source.poll(message -> {
                System.out.println("polled: " + message.getPayload());
            });
            if (!received) Thread.sleep(1000); // nothing was available -- wait before polling again
        }
    };
}
```

## 2. Why & when

Ordinary event-driven consumption assumes the consumer wants messages delivered as fast as they arrive, on the framework's own thread management. Polled consumption exists for the cases where that assumption doesn't fit: batch-oriented processing that should pull work only when a scheduled job actually runs, integration with external systems that themselves operate on a pull/poll model, or scenarios where precise, application-controlled control over consumption rate matters more than automatic, framework-driven delivery.

Reach for `PollableMessageSource` when:

- Consumption should happen on a schedule (a `@Scheduled` batch job pulling a bounded number of messages every few minutes) rather than continuously and reactively as messages arrive.
- The processing logic itself needs full control over exactly when it asks for the next message — for instance, throttling consumption based on some external condition the framework's automatic delivery model has no way to express.
- Integrating with a downstream system that's itself pull-based (writing to a batch file, calling an external API with its own rate limits) where matching the consumption rate to that downstream system's actual capacity matters more than raw throughput.

## 3. Core concept

```
 event-driven consumer (the default, ordinary case):
    framework calls your Function/Consumer AUTOMATICALLY, the instant a message is available
    you don't control the timing -- the framework does

 polled consumer:
    YOUR code calls source.poll(handler) explicitly, whenever it chooses to
    if a message is available, handler runs with it; if not, poll() returns false and your code decides what to do next
    you control the timing entirely -- the framework just makes messages available on request
```

The inversion of control is the entire distinction — who decides *when* the next message gets processed, the framework or your own code.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An event driven consumer is invoked automatically by the framework whenever a message arrives while a polled consumer explicitly calls poll on its own schedule to pull one message at a time">
  <rect x="20" y="20" width="280" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">event-driven (default)</text>
  <text x="160" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">framework calls your Function</text>
  <text x="160" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">the instant a message arrives</text>

  <rect x="330" y="20" width="290" height="70" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">polled consumer</text>
  <text x="475" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">your code calls source.poll(...)</text>
  <text x="475" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">on YOUR chosen schedule</text>

  <text x="320" y="130" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">same underlying broker and destination -- only who decides WHEN differs</text>

  <defs><marker id="a86" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Same messages, same destination — the only real difference is which side (framework or application code) controls the timing of consumption.

## 5. Runnable example

The scenario: consume `order-placed-events` on a controlled, application-driven schedule rather than reactively. Start with event-driven consumption (the default), then add explicit polling, then add a scheduled batch job pulling a bounded number of messages at a time.

### Level 1 — Basic

Event-driven consumption — messages processed automatically, the instant they're available.

```java
import java.util.*;
import java.util.function.Consumer;

public class PolledConsumersLevel1 {
    static List<String> messageQueue = new ArrayList<>(List.of("Order(1)", "Order(2)", "Order(3)"));

    static Consumer<String> handleOrder = message -> System.out.println("automatically handled: " + message);

    static void simulateFrameworkDelivery() {
        // the framework calls handleOrder AUTOMATICALLY for every message, no application control over timing
        for (String message : new ArrayList<>(messageQueue)) {
            handleOrder.accept(message);
            messageQueue.remove(message);
        }
    }

    public static void main(String[] args) {
        simulateFrameworkDelivery();
        System.out.println("remaining in queue: " + messageQueue);
    }
}
```

How to run: `java PolledConsumersLevel1.java`

`simulateFrameworkDelivery` processes every available message immediately and automatically — this is ordinary event-driven consumption, with the "framework" (this simulated loop) deciding entirely on its own when each message gets handled.

### Level 2 — Intermediate

Add explicit polling: application code calls `poll()` itself, on its own terms, pulling one message at a time only when it chooses to.

```java
import java.util.*;
import java.util.function.Consumer;

public class PolledConsumersLevel2 {
    static List<String> messageQueue = new ArrayList<>(List.of("Order(1)", "Order(2)", "Order(3)"));

    static boolean poll(Consumer<String> handler) {
        if (messageQueue.isEmpty()) return false; // nothing available right now
        String message = messageQueue.remove(0);
        handler.accept(message);
        return true;
    }

    public static void main(String[] args) {
        // application code EXPLICITLY decides to poll exactly 2 times, regardless of queue depth
        boolean got1 = poll(message -> System.out.println("explicitly polled: " + message));
        boolean got2 = poll(message -> System.out.println("explicitly polled: " + message));

        System.out.println("poll 1 got a message: " + got1);
        System.out.println("poll 2 got a message: " + got2);
        System.out.println("remaining in queue (untouched, application chose NOT to poll further): " + messageQueue);
    }
}
```

How to run: `java PolledConsumersLevel2.java`

`poll()` returns `true`/`false` depending on whether a message was actually available, and — critically — `main` decides exactly how many times to call it. `"Order(3)"` remains in `messageQueue`, entirely untouched, purely because the application chose to stop polling after two calls — this is the essence of polled consumption: consumption rate and timing are entirely under application control, not automatically driven by message availability.

### Level 3 — Advanced

Add a scheduled batch job pulling a bounded number of messages at a time, on a timer, modeling a real `@Scheduled` method using `PollableMessageSource` for periodic, controlled batch processing.

```java
import java.util.*;
import java.util.function.Consumer;

public class PolledConsumersLevel3 {
    static List<String> messageQueue = new ArrayList<>(
            List.of("Order(1)", "Order(2)", "Order(3)", "Order(4)", "Order(5)", "Order(6)", "Order(7)")
    );

    static boolean poll(Consumer<String> handler) {
        if (messageQueue.isEmpty()) return false;
        String message = messageQueue.remove(0);
        handler.accept(message);
        return true;
    }

    // models a @Scheduled batch job: pulls up to batchSize messages each time it's invoked
    static void scheduledBatchPoll(int batchSize) {
        int processed = 0;
        while (processed < batchSize) {
            boolean got = poll(message -> System.out.println("batch processed: " + message));
            if (!got) break; // queue ran dry before filling the batch -- stop early, don't wait
            processed++;
        }
        System.out.println("this scheduled run processed " + processed + " message(s)");
    }

    public static void main(String[] args) {
        System.out.println("-- scheduled run 1 (simulated) --");
        scheduledBatchPoll(3); // e.g. a @Scheduled(fixedDelay = 60000) method, invoked once per minute, batch size 3

        System.out.println("-- scheduled run 2 (simulated, 1 minute later) --");
        scheduledBatchPoll(3);

        System.out.println("-- scheduled run 3 (simulated, 1 minute later) --");
        scheduledBatchPoll(3); // queue only has 1 left -- processes it, then stops early

        System.out.println("final remaining queue: " + messageQueue);
    }
}
```

How to run: `java PolledConsumersLevel3.java`

`scheduledBatchPoll` models a `@Scheduled` method invoked periodically, each run pulling up to `batchSize` messages via `poll()` and stopping early if the queue runs dry before the batch fills — this is exactly the shape of a real periodic batch consumer: bounded work per invocation, controlled entirely by the scheduling interval and batch size the application itself defines, rather than the framework pushing messages continuously as they arrive.

## 6. Walkthrough

Trace the three simulated scheduled runs in Level 3.

1. "Scheduled run 1" calls `scheduledBatchPoll(3)` — the `while` loop calls `poll(...)` up to three times. Each call finds a message (`messageQueue` starts with 7 entries), processes it, and increments `processed`. After three successful polls, `processed == batchSize (3)`, so the loop exits normally, having consumed `Order(1)`, `Order(2)`, `Order(3)`.
2. "Scheduled run 2" (modeling the same scheduled method invoked again, a simulated minute later) calls `scheduledBatchPoll(3)` again — the queue now has 4 messages remaining (`Order(4)` through `Order(7)`). The loop again successfully polls three times, consuming `Order(4)`, `Order(5)`, `Order(6)`.
3. "Scheduled run 3" calls `scheduledBatchPoll(3)` a third time — the queue now has only 1 message left (`Order(7)`). The first `poll()` call succeeds, processing it, `processed` becomes `1`. The second `poll()` call finds `messageQueue.isEmpty()` and returns `false`; the `if (!got) break` condition fires, ending the loop early with `processed == 1`, less than the requested `batchSize`.
4. The final `println` reports `messageQueue` as empty — all seven original messages were eventually processed across three separate, bounded, scheduled runs, each pulling only as many messages as were actually available up to its batch size, with the application entirely controlling the pacing rather than everything being consumed in one continuous, framework-driven rush.

```
run 1 (batchSize=3): polls Order(1), Order(2), Order(3) -> processed=3, batch full
run 2 (batchSize=3): polls Order(4), Order(5), Order(6) -> processed=3, batch full
run 3 (batchSize=3): polls Order(7) -> processed=1, queue empty -> stops EARLY, doesn't wait for more
```

## 7. Gotchas & takeaways

> **Gotcha:** a polled consumer that polls too infrequently (a long `@Scheduled` interval, or application logic that rarely calls `poll()`) can let messages accumulate on the broker for a long time before being consumed — unlike event-driven consumption, where messages are processed essentially as fast as they arrive, polled consumption's latency is directly bounded by however often the application chooses to poll, not by the broker's own delivery speed. Choose the polling interval deliberately based on how much consumption latency is actually acceptable for that particular workload.

- Polled consumption inverts control from the framework to the application — useful specifically when the application, not the framework's default "deliver as fast as possible" behavior, should decide the pace and timing of consumption.
- `PollableMessageSource.poll(...)` returns whether a message was actually available, letting application code cleanly handle "nothing to do right now" without blocking or erroring.
- A bounded, scheduled batch-polling pattern (as modeled in Level 3) is the most common real use case — periodic jobs that process a manageable chunk of work per run, rather than reacting instantly and continuously to every new message.
- Polled consumption trades event-driven's low latency (messages processed nearly instantly) for application-level control over pacing — appropriate specifically when that control is actually needed, not a general-purpose replacement for ordinary event-driven consumers.
