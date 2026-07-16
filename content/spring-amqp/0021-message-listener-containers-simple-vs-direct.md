---
card: spring-amqp
gi: 21
slug: message-listener-containers-simple-vs-direct
title: "Message listener containers (Simple vs Direct)"
---

## 1. What it is

A message listener container is the infrastructure that manages the actual consuming of messages from a queue and dispatching them to application listener code — handling connection/channel management, concurrency, and acknowledgment on the consumer's behalf, so application code just supplies the "what to do with each message" logic. Spring AMQP provides two implementations: `SimpleMessageListenerContainer`, the older, more mature implementation using a fixed or dynamically-scaling pool of internal threads each looping on `basicConsume`, and `DirectMessageListenerContainer`, a newer implementation that creates one consumer per configured concurrency level directly on separate connections/channels, offering somewhat better behavior when consumer count changes dynamically at runtime.

## 2. Why & when

Understanding the distinction matters for tuning consumer behavior, even though most applications never construct either container directly, relying instead on `@RabbitListener`'s (card 0022) auto-configured default:

- **`SimpleMessageListenerContainer` is the long-standing, well-understood default** — it's been in Spring AMQP the longest, has the most operational track record, and its behavior under various failure and scaling scenarios is thoroughly documented and battle-tested.
- **`DirectMessageListenerContainer` handles dynamic concurrency changes more gracefully** — if an application needs to change its consumer concurrency at runtime (scaling up or down in response to queue depth, for instance) without a full container restart, `DirectMessageListenerContainer`'s per-consumer-thread model adapts to that more cleanly than `SimpleMessageListenerContainer`'s internal pooling model.
- **Most applications never choose between them explicitly** — `@RabbitListener`'s auto-configuration picks a sensible default (`SimpleMessageListenerContainer`, historically), and only applications with specific scaling or concurrency-management needs typically reach for `DirectMessageListenerContainer` explicitly.

## 3. Core concept

Think of `SimpleMessageListenerContainer` as a fixed team of workers each independently looping through a shared task list, checking back for more work as soon as they finish their current item — reliable and well-understood, but resizing the team (adding or removing workers) means carefully coordinating a change to that whole pool. `DirectMessageListenerContainer` is more like assigning one dedicated worker per active work line, where adding or removing a work line (changing concurrency) is a more localized, individually-manageable operation, since each worker's line of work isn't entangled with a shared internal pool the way the first model's workers are.

```java
// SimpleMessageListenerContainer: the traditional, well-established default.
@Bean
public SimpleMessageListenerContainer simpleContainer(ConnectionFactory connectionFactory) {
    SimpleMessageListenerContainer container = new SimpleMessageListenerContainer(connectionFactory);
    container.setQueueNames("orderProcessingQueue");
    container.setConcurrentConsumers(5);
    container.setMaxConcurrentConsumers(20); // can scale within this range
    container.setMessageListener(message -> orderService.process(message));
    return container;
}

// DirectMessageListenerContainer: newer, better dynamic-concurrency behavior.
@Bean
public DirectMessageListenerContainer directContainer(ConnectionFactory connectionFactory) {
    DirectMessageListenerContainer container = new DirectMessageListenerContainer(connectionFactory);
    container.setQueueNames("orderProcessingQueue");
    container.setConsumersPerQueue(5); // adjustable more cleanly at runtime
    container.setMessageListener(message -> orderService.process(message));
    return container;
}
```

Both containers ultimately deliver messages to the same kind of listener callback; the difference lies in internal concurrency management, not in the application-facing programming model.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SimpleMessageListenerContainer manages an internal pool of consumer threads that can grow and shrink within it; DirectMessageListenerContainer creates one consumer per concurrency slot directly, making individual consumers easier to add or remove independently" >
  <text x="160" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SimpleMessageListenerContainer</text>
  <rect x="20" y="30" width="280" height="100" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="35" y="55" fill="#e6edf3" font-size="7" font-family="sans-serif">internal thread pool (shared management)</text>
  <rect x="35" y="70" width="60" height="20" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="65" y="84" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">consumer</text>
  <rect x="105" y="70" width="60" height="20" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="135" y="84" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">consumer</text>
  <rect x="175" y="70" width="60" height="20" rx="3" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="205" y="84" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">consumer</text>
  <text x="160" y="115" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">resizing pool: coordinated internally</text>

  <text x="480" y="14" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DirectMessageListenerContainer</text>
  <rect x="340" y="30" width="280" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="355" y="50" width="60" height="20" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="385" y="64" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">consumer 1</text>
  <rect x="425" y="50" width="60" height="20" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="455" y="64" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">consumer 2</text>
  <rect x="495" y="50" width="60" height="20" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="525" y="64" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">consumer 3</text>
  <text x="480" y="115" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">each independent -- add/remove individually, cleanly</text>
</svg>

Both consume messages the same way; the difference is how cleanly concurrency can change at runtime.

## 5. Runnable example

The scenario: adjusting consumer concurrency at runtime in response to changing queue depth, simulated with a plain in-memory model standing in for both container types' concurrency-management approach (no real RabbitMQ broker needed to demonstrate the structural difference in how each handles dynamic scaling), starting with a basic fixed-concurrency consumer setup, then adding a pool-based scaling model resembling `SimpleMessageListenerContainer`, then adding an independent-consumer model resembling `DirectMessageListenerContainer` to contrast how cleanly each adapts to a concurrency change.

### Level 1 — Basic

```java
// ListenerContainerDemo.java
import java.util.*;

public class ListenerContainerDemo {
    static class FixedConcurrencyContainer {
        int consumerCount;
        FixedConcurrencyContainer(int consumerCount) { this.consumerCount = consumerCount; }
        void start() { System.out.println("Started " + consumerCount + " consumers"); }
    }

    public static void main(String[] args) {
        FixedConcurrencyContainer container = new FixedConcurrencyContainer(5);
        container.start();
    }
}
```

How to run: `java ListenerContainerDemo.java`. Expected output: `Started 5 consumers` — a basic, fixed-concurrency container with no scaling behavior yet.

### Level 2 — Intermediate

```java
// ListenerContainerDemo.java
import java.util.*;

public class ListenerContainerDemo {
    // Real-world concern: SimpleMessageListenerContainer manages an internal pool that can
    // grow/shrink between a min and max, but resizing involves coordinating the whole pool's
    // internal state together, rather than adding/removing one independent consumer at a time.
    static class PoolBasedContainer {
        int minConsumers, maxConsumers, currentConsumers;

        PoolBasedContainer(int minConsumers, int maxConsumers) {
            this.minConsumers = minConsumers;
            this.maxConsumers = maxConsumers;
            this.currentConsumers = minConsumers;
        }

        void adjustForQueueDepth(int queueDepth) {
            int target = Math.min(maxConsumers, Math.max(minConsumers, queueDepth / 100));
            if (target != currentConsumers) {
                System.out.println("Resizing pool from " + currentConsumers + " to " + target
                    + " consumers (coordinated pool-wide adjustment)");
                currentConsumers = target;
            }
        }
    }

    public static void main(String[] args) {
        PoolBasedContainer container = new PoolBasedContainer(2, 10);
        container.adjustForQueueDepth(50);   // low depth, stays at minimum
        container.adjustForQueueDepth(650);  // high depth, scales up
        container.adjustForQueueDepth(30);   // depth drops, scales back down
    }
}
```

How to run: `java ListenerContainerDemo.java`. Expected output: no resize message for the first call (already at minimum), then `Resizing pool from 2 to 6 consumers ...` for the depth spike, then `Resizing pool from 6 to 2 consumers ...` as depth drops — the pool-based model adjusting as a coordinated whole each time.

### Level 3 — Advanced

```java
// ListenerContainerDemo.java
import java.util.*;

public class ListenerContainerDemo {
    // Production concern: DirectMessageListenerContainer manages consumers as independent
    // units -- adding or removing ONE consumer doesn't require touching or coordinating the
    // others at all, which is the specific advantage in scenarios needing frequent, fine-
    // grained runtime concurrency adjustments.
    static class IndependentConsumerContainer {
        List<String> activeConsumerIds = new ArrayList<>();
        int nextConsumerId = 1;

        void addConsumer() {
            String id = "consumer-" + nextConsumerId++;
            activeConsumerIds.add(id);
            System.out.println("Added " + id + " independently (others untouched): " + activeConsumerIds);
        }

        void removeConsumer(String id) {
            activeConsumerIds.remove(id);
            System.out.println("Removed " + id + " independently (others untouched): " + activeConsumerIds);
        }
    }

    public static void main(String[] args) {
        IndependentConsumerContainer container = new IndependentConsumerContainer();
        container.addConsumer();
        container.addConsumer();
        container.addConsumer();

        System.out.println("-- queue depth spikes, need one more consumer --");
        container.addConsumer(); // just adds one, doesn't touch the existing three

        System.out.println("-- queue depth drops, remove one specific consumer --");
        container.removeConsumer("consumer-2"); // removes just this one, others keep running
    }
}
```

How to run: `java ListenerContainerDemo.java`. Expected output: three consumers added one at a time, each addition shown as independent; a fourth added in response to a depth spike, again independently; then `consumer-2` specifically removed while `consumer-1`, `consumer-3`, and `consumer-4` remain listed as still active — demonstrating the fine-grained, individually-manageable concurrency adjustments `DirectMessageListenerContainer`'s model favors over `SimpleMessageListenerContainer`'s coordinated-pool-resize approach.

## 6. Walkthrough

Trace how each container type handles a concurrency change triggered by a queue-depth spike.

1. **Steady state**: both container types start with a configured baseline number of active consumers, each independently pulling and processing messages from the target queue(s).
2. **Depth spike detected**: some external signal (a monitoring system, an autoscaling controller, or the container's own built-in queue-depth-aware scaling logic) determines more consumer capacity is needed to keep up with an increased message arrival rate.
3. **SimpleMessageListenerContainer's response**: its internal pool-management logic recalculates a target consumer count within its configured min/max range and adjusts the shared internal pool to match — a coordinated, pool-wide operation, even though only the count actually changes.
4. **DirectMessageListenerContainer's response**: it can add (or remove) individual, independent consumer instances directly, without needing to coordinate against a shared internal pool structure — each consumer is a more self-contained unit whose addition or removal doesn't entangle with the others' state.
5. **Depth normalizes**: as the spike subsides, the same scaling-down decision plays out in reverse — `SimpleMessageListenerContainer` recalculates and adjusts its pool again, while `DirectMessageListenerContainer` can remove specific consumers individually.
6. **Application-facing behavior identical either way**: regardless of which container type is managing consumption, the actual message-processing code (a `MessageListener` implementation, or more commonly a `@RabbitListener`-annotated method) is completely unaware of which container delivered the message — the distinction is purely an internal consumption-management concern.

```
queue depth spikes -> more consumer capacity needed
  SimpleMessageListenerContainer: recalculate target -> resize shared internal pool (coordinated)
  DirectMessageListenerContainer: add individual consumer(s) directly (independent, localized)

queue depth normalizes -> less consumer capacity needed
  SimpleMessageListenerContainer: recalculate target -> resize shared internal pool again
  DirectMessageListenerContainer: remove individual consumer(s) directly
```

## 7. Gotchas & takeaways

> **Gotcha:** switching a running application's listener container type (from `SimpleMessageListenerContainer` to `DirectMessageListenerContainer`, or vice versa) is a configuration-level change, not something that happens automatically or gradually — an application relying on specific scaling behavior characteristics of one container type needs to explicitly configure that type rather than assuming Spring Boot's or `@RabbitListener`'s default will always match its expectations, especially across Spring AMQP version upgrades where defaults can shift.

- Most applications never need to choose explicitly between the two container types — `@RabbitListener`'s (card 0022) default configuration handles this transparently, and only applications with specific, demonstrated concurrency-scaling requirements typically need to reach for one explicitly.
- `SimpleMessageListenerContainer`'s longer track record and more thoroughly documented behavior across various operational scenarios makes it a reasonable default choice when there's no specific reason to prefer the alternative.
- `DirectMessageListenerContainer`'s advantage is specifically in scenarios needing frequent, fine-grained concurrency adjustments at runtime — if an application's consumer count is essentially static (set once at startup and rarely changed), this advantage doesn't meaningfully come into play.
- Both containers deliver messages to application code through the same programming model — the choice between them is purely an internal consumption-management and scaling-behavior decision, never something that changes how listener methods themselves are written.
