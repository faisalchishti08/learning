---
card: microservices
gi: 148
slug: spring-cloud-stream-dead-letter-retry-config
title: "Spring Cloud Stream dead-letter & retry config"
---

## 1. What it is

Spring Cloud Stream provides declarative, configuration-driven [retry](0123-dead-letter-queue-dlq.md) and [dead-letter queue](0123-dead-letter-queue-dlq.md) support for consumer bindings — properties like `consumer.max-attempts`, `consumer.back-off-initial-interval`, and `consumer.dlq-name` (or the Kafka/RabbitMQ binder-specific equivalents) let a function bean's failure-handling policy be expressed entirely in `application.yml`, without any retry loop, exception classification, or DLQ-publishing code written by hand.

## 2. Why & when

Writing [poison message handling](0124-poison-message-handling.md) and [DLQ routing](0123-dead-letter-queue-dlq.md) by hand, as earlier sections in this course demonstrated, means every consumer bean re-implements the same retry-count tracking, backoff logic, and DLQ-publishing boilerplate — repetitive, easy to get subtly wrong, and disconnected from the actual business logic it surrounds. Spring Cloud Stream's declarative configuration handles this uniformly across every binding: the retry policy (how many attempts, what backoff), and what happens after retries are exhausted (route to a DLQ, discard, or fail the whole application), are expressed as properties the framework enforces automatically around any function bean.

Use this declarative configuration as the default for any Spring Cloud Stream consumer where transient failures are plausible (which is nearly always, for anything calling a downstream dependency) — it is dramatically less code and less error-prone than hand-rolled retry logic. Reach for a custom, hand-written retry/DLQ implementation only when the built-in policy genuinely cannot express a specific requirement, such as classifying retryable versus non-retryable exceptions with logic more nuanced than the framework's built-in exception-type matching supports.

## 3. Core concept

The function bean contains only business logic and can throw exceptions freely; retry attempts, backoff timing, and DLQ routing after retries are exhausted are all handled by the framework around that bean, driven entirely by configuration properties bound to the consumer's binding name.

```java
@Bean
public Consumer<OrderPlaced> processOrder() {
    return order -> {
        if (!inventoryAvailable(order)) throw new RuntimeException("inventory check failed"); // just THROW
        applyOrder(order);
    }; // NO retry loop, NO DLQ-publishing code anywhere in this method
}
```
```yaml
spring.cloud.stream.bindings.processOrder-in-0.consumer.max-attempts: 3
spring.cloud.stream.bindings.processOrder-in-0.consumer.back-off-initial-interval: 1000
spring.cloud.stream.kafka.bindings.processOrder-in-0.consumer.enableDlq: true  # after 3 failed attempts, auto-route to DLQ
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A consumer bean throws an exception; the framework, driven by configuration, automatically retries with backoff up to max-attempts, then routes the message to a dead-letter topic once retries are exhausted -- none of this logic is written in the bean itself" >
  <rect x="20" y="60" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="87" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Consumer bean (throws)</text>

  <rect x="230" y="30" width="200" height="105" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Framework retry policy</text>
  <text x="330" y="70" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 1 -&gt; fail, backoff</text>
  <text x="330" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 2 -&gt; fail, backoff</text>
  <text x="330" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 3 -&gt; fail, exhausted</text>
  <text x="330" y="118" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">config-driven, no code</text>

  <rect x="470" y="60" width="150" height="45" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="545" y="87" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">DLQ topic</text>

  <line x1="170" y1="82" x2="228" y2="82" stroke="#8b949e" marker-end="url(#arr29)"/>
  <line x1="430" y1="82" x2="468" y2="82" stroke="#8b949e" marker-end="url(#arr29)"/>

  <defs>
    <marker id="arr29" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Retry and DLQ behavior are entirely framework-managed, driven by configuration surrounding an ordinary, exception-throwing function bean.

## 5. Runnable example

Scenario: an order-processing consumer that starts with hand-written retry and DLQ logic tangled into the business method (the boilerplate this configuration eliminates), then simulates the framework's declarative retry-and-DLQ behavior wrapping a pure, exception-throwing bean, and finally adds configurable backoff timing between attempts to mirror the real `back-off-initial-interval` and `back-off-multiplier` properties.

### Level 1 — Basic

```java
// File: HandWrittenRetryBoilerplate.java -- retry and DLQ logic hand-rolled,
// tangled directly into the business method.
import java.util.*;

public class HandWrittenRetryBoilerplate {
    record OrderPlaced(int orderId) {}
    static List<OrderPlaced> deadLetterQueue = new ArrayList<>();

    static void processOrderWithManualRetry(OrderPlaced order) {
        int maxAttempts = 3;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                applyOrder(order); // the ACTUAL business logic, buried inside retry boilerplate
                System.out.println("Order " + order.orderId() + " processed on attempt " + attempt);
                return;
            } catch (RuntimeException e) {
                System.out.println("Attempt " + attempt + " failed: " + e.getMessage());
                if (attempt == maxAttempts) {
                    deadLetterQueue.add(order); // hand-rolled DLQ routing
                    System.out.println("Max attempts reached -- routed to hand-rolled DLQ.");
                }
            }
        }
    }

    static void applyOrder(OrderPlaced order) { throw new RuntimeException("inventory service unavailable"); }

    public static void main(String[] args) {
        processOrderWithManualRetry(new OrderPlaced(42));
        System.out.println("DLQ contents: " + deadLetterQueue);
        System.out.println("This retry+DLQ boilerplate would need to be COPIED into every single consumer method.");
    }
}
```

**How to run:** `javac HandWrittenRetryBoilerplate.java && java HandWrittenRetryBoilerplate` (JDK 17+).

The retry loop, attempt counting, and DLQ routing are all mixed directly into `processOrderWithManualRetry`, meaning every new consumer needing this same policy would duplicate this entire structure.

### Level 2 — Intermediate

```java
// File: FrameworkManagedRetryDlq.java -- the consumer bean is PURE business logic;
// a simulated framework wrapper applies retry + DLQ policy entirely from configuration.
import java.util.*;
import java.util.function.*;

public class FrameworkManagedRetryDlq {
    record OrderPlaced(int orderId) {}
    record RetryDlqConfig(int maxAttempts) {}

    // simulates Spring Cloud Stream's own binding machinery wrapping a Consumer bean
    static class SimulatedBindingFramework {
        List<OrderPlaced> dlqTopic = new ArrayList<>();

        void bindWithRetryAndDlq(Consumer<OrderPlaced> businessLogic, RetryDlqConfig config, OrderPlaced message) {
            for (int attempt = 1; attempt <= config.maxAttempts(); attempt++) {
                try {
                    businessLogic.accept(message); // the bean itself has NO knowledge of attempt counting
                    System.out.println("[framework] processed on attempt " + attempt);
                    return;
                } catch (RuntimeException e) {
                    System.out.println("[framework] attempt " + attempt + " failed: " + e.getMessage());
                    if (attempt == config.maxAttempts()) {
                        dlqTopic.add(message); // FRAMEWORK handles DLQ routing, driven by config alone
                        System.out.println("[framework] max-attempts (" + config.maxAttempts() + ") reached -- auto-routed to DLQ topic.");
                    }
                }
            }
        }
    }

    // THIS is what application code actually writes -- pure business logic, no retry/DLQ awareness
    static Consumer<OrderPlaced> processOrder() {
        return order -> { throw new RuntimeException("inventory service unavailable"); };
    }

    public static void main(String[] args) {
        SimulatedBindingFramework framework = new SimulatedBindingFramework();
        RetryDlqConfig config = new RetryDlqConfig(3); // simulates spring.cloud.stream.bindings.processOrder-in-0.consumer.max-attempts: 3

        framework.bindWithRetryAndDlq(processOrder(), config, new OrderPlaced(42));
        System.out.println("DLQ topic contents: " + framework.dlqTopic);
        System.out.println("processOrder() itself contains ZERO retry or DLQ code -- all of it lives in framework + config.");
    }
}
```

**How to run:** `javac FrameworkManagedRetryDlq.java && java FrameworkManagedRetryDlq` (JDK 17+).

Expected output:
```
[framework] attempt 1 failed: inventory service unavailable
[framework] attempt 2 failed: inventory service unavailable
[framework] attempt 3 failed: inventory service unavailable
[framework] max-attempts (3) reached -- auto-routed to DLQ topic.
DLQ topic contents: [OrderPlaced[orderId=42]]
```

`processOrder()` is identical in shape to any other pure `Consumer` bean — the retry counting and DLQ routing live entirely in `SimulatedBindingFramework`, driven only by the `RetryDlqConfig` passed alongside it.

### Level 3 — Advanced

```java
// File: ConfigurableBackoff.java -- adds backoff TIMING between attempts, mirroring
// back-off-initial-interval and back-off-multiplier, still entirely framework-managed.
import java.util.*;
import java.util.function.*;

public class ConfigurableBackoff {
    record OrderPlaced(int orderId) {}
    record RetryDlqConfig(int maxAttempts, long backOffInitialIntervalMillis, double backOffMultiplier) {}

    static class SimulatedBindingFramework {
        List<OrderPlaced> dlqTopic = new ArrayList<>();

        void bindWithRetryAndDlq(Consumer<OrderPlaced> businessLogic, RetryDlqConfig config, OrderPlaced message) throws InterruptedException {
            long currentBackoff = config.backOffInitialIntervalMillis();
            for (int attempt = 1; attempt <= config.maxAttempts(); attempt++) {
                try {
                    businessLogic.accept(message);
                    System.out.println("[framework] processed on attempt " + attempt);
                    return;
                } catch (RuntimeException e) {
                    System.out.println("[framework] attempt " + attempt + " failed: " + e.getMessage());
                    if (attempt == config.maxAttempts()) {
                        dlqTopic.add(message);
                        System.out.println("[framework] max-attempts reached -- routed to DLQ.");
                    } else {
                        System.out.println("[framework] backing off " + currentBackoff + "ms before next attempt (config-driven)");
                        Thread.sleep(currentBackoff); // real backoff wait, entirely framework-managed
                        currentBackoff = (long) (currentBackoff * config.backOffMultiplier()); // EXPONENTIAL backoff
                    }
                }
            }
        }
    }

    static Consumer<OrderPlaced> processOrder() {
        return order -> { throw new RuntimeException("inventory service unavailable"); };
    }

    public static void main(String[] args) throws InterruptedException {
        SimulatedBindingFramework framework = new SimulatedBindingFramework();
        // mirrors: back-off-initial-interval=200, back-off-multiplier=2.0, max-attempts=4
        RetryDlqConfig config = new RetryDlqConfig(4, 200, 2.0);

        long start = System.currentTimeMillis();
        framework.bindWithRetryAndDlq(processOrder(), config, new OrderPlaced(42));
        long elapsed = System.currentTimeMillis() - start;

        System.out.println("Total elapsed (includes exponential backoff waits): ~" + elapsed + "ms");
        System.out.println("Expected backoffs: 200ms, then 400ms, then 800ms between the 4 attempts (200 * 2^n).");
    }
}
```

**How to run:** `javac ConfigurableBackoff.java && java ConfigurableBackoff` (JDK 17+).

Expected output (elapsed time approximate, roughly 1400ms = 200+400+800):
```
[framework] attempt 1 failed: inventory service unavailable
[framework] backing off 200ms before next attempt (config-driven)
[framework] attempt 2 failed: inventory service unavailable
[framework] backing off 400ms before next attempt (config-driven)
[framework] attempt 3 failed: inventory service unavailable
[framework] backing off 800ms before next attempt (config-driven)
[framework] attempt 4 failed: inventory service unavailable
[framework] max-attempts reached -- routed to DLQ.
Total elapsed (includes exponential backoff waits): ~1400ms
Expected backoffs: 200ms, then 400ms, then 800ms between the 4 attempts (200 * 2^n).
```

## 6. Walkthrough

1. **Level 1** — `processOrderWithManualRetry` contains the `for` loop, the `try`/`catch`, the attempt counting, and the `deadLetterQueue.add(order)` call all directly inside the method that's supposed to represent order-processing business logic — the actual business rule (`applyOrder`) is a small fraction of this method's total code.
2. **Level 2, separating the bean from the policy** — `processOrder()` returns a `Consumer<OrderPlaced>` whose entire body is `order -> { throw new RuntimeException(...); }` — no loop, no attempt tracking, no DLQ reference anywhere.
3. **Level 2, the framework applying the policy externally** — `SimulatedBindingFramework.bindWithRetryAndDlq` takes the bean, a `RetryDlqConfig`, and a message, and is the *only* code responsible for calling the bean repeatedly, catching its exceptions, and deciding when to give up and route to `dlqTopic`.
4. **Level 2, the observable separation of concerns** — `main`'s final printed line makes explicit what the refactor achieved: `processOrder()`'s source is unaware that retries or a DLQ even exist, exactly mirroring how a real `@Bean Consumer<OrderPlaced>` method in a Spring Cloud Stream application contains no retry-related code, with `spring.cloud.stream.bindings.processOrder-in-0.consumer.max-attempts` and `enableDlq` doing that work instead.
5. **Level 3, adding backoff configuration** — `RetryDlqConfig` gains `backOffInitialIntervalMillis` and `backOffMultiplier`, mirroring the real `back-off-initial-interval` and `back-off-multiplier` properties; `bindWithRetryAndDlq` now calls `Thread.sleep(currentBackoff)` between failed attempts instead of retrying immediately.
6. **Level 3, exponential growth of the wait** — after each failed attempt (except the last), `currentBackoff` is multiplied by `config.backOffMultiplier()` (2.0), so the wait grows from 200ms to 400ms to 800ms across the three retry gaps between four total attempts — this is the same exponential backoff strategy the real framework applies automatically.
7. **Level 3, the measured total time** — the elapsed time printed at the end (roughly 1400ms, the sum of the three backoff waits) is directly observable proof that real time passed between attempts according to the configured multiplier, not that attempts happened back-to-back — confirming the backoff configuration genuinely governs timing, exactly as it would in a real Spring Cloud Stream deployment tuning `back-off-initial-interval` and `back-off-multiplier` to avoid hammering a struggling downstream dependency with immediate, rapid-fire retries.

## 7. Gotchas & takeaways

> **Gotcha:** `max-attempts` in Spring Cloud Stream counts the *total* number of attempts including the first one, not the number of *retries* after the first failure — a `max-attempts: 3` configuration means the message is tried up to three times total (one initial attempt plus two retries), a common off-by-one misunderstanding when tuning this value.

- Spring Cloud Stream's declarative retry and DLQ configuration handles attempt counting, backoff timing, and dead-letter routing entirely through `application.yml` properties, wrapping a consumer bean that contains only business logic.
- This eliminates the repetitive, error-prone boilerplate of hand-writing the same retry loop and DLQ-publishing code inside every consumer method.
- Exponential backoff (`back-off-initial-interval`, `back-off-multiplier`) is configured declaratively and applied automatically between failed attempts, without any timing code in the business logic.
- Reach for hand-written retry/DLQ logic only when the built-in exception classification or policy genuinely cannot express a specific, more nuanced requirement.
- `max-attempts` counts the total number of tries, including the first, which is a common source of off-by-one configuration mistakes.
