---
card: spring-cloud
gi: 85
slug: error-handling-dead-letter-queues
title: "Error handling & dead-letter queues"
---

## 1. What it is

When a consumer function throws an exception processing a message, Spring Cloud Stream can retry the delivery a configured number of times, and if it still fails, route the "poison" message to a dead-letter queue (DLQ) — a separate destination holding messages that couldn't be processed, so the main consumer isn't stuck retrying the same bad message forever, and no data is silently lost.

```properties
spring.cloud.stream.bindings.handleOrder-in-0.destination=order-placed-events
spring.cloud.stream.bindings.handleOrder-in-0.group=billing-service-group

spring.cloud.stream.rabbit.bindings.handleOrder-in-0.consumer.max-attempts=3
spring.cloud.stream.rabbit.bindings.handleOrder-in-0.consumer.dlq-name=order-placed-events.billing-service-group.dlq
spring.cloud.stream.rabbit.bindings.handleOrder-in-0.consumer.auto-bind-dlq=true
```

## 2. Why & when

Without dead-letter handling, a message that consistently fails to process (a malformed payload, a business rule that always rejects it, a bug triggered by that specific data) either gets retried forever — blocking every message behind it in the same partition/queue — or gets silently dropped, losing data with no trace. A DLQ solves both: the retry loop eventually gives up on that one message specifically, routes it aside for manual inspection or reprocessing, and lets the consumer move on to the next message rather than getting permanently stuck.

Reach for dead-letter queue configuration when:

- Consuming any destination where a malformed or unprocessable message is a realistic possibility — which is essentially every real production messaging integration, since upstream bugs, schema drift, and unexpected edge cases do happen.
- A message failing to process shouldn't block the entire queue/partition behind it — without a DLQ, ordered consumption (from the previous card's partitioning) means one poison message can permanently stall every subsequent message for that same partition key.
- Operational visibility into failures matters — a DLQ gives a concrete, inspectable place to see exactly which messages failed and why, rather than failures disappearing into logs that may or may not be monitored closely.

## 3. Core concept

```
 message arrives -> handleOrder(message) throws an exception
        |
        v
 retry attempt 2 -> throws again
        |
        v
 retry attempt 3 (max-attempts reached) -> STILL throws
        |
        v
 route to DLQ (order-placed-events.billing-service-group.dlq) instead of retrying forever
        |
        v
 consumer moves on to the NEXT message -- not stuck on this one indefinitely
```

The DLQ is the escape valve that turns "this one bad message blocks everything behind it forever" into "this one bad message is set aside, and everything else keeps flowing."

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A message that fails processing is retried up to the configured maximum attempts, and if it still fails it is routed to a dead letter queue instead of blocking the consumer, which then continues processing subsequent messages normally">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">message arrives</text>

  <line x1="200" y1="40" x2="250" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a85)"/>

  <rect x="255" y="20" width="180" height="40" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.3"/>
  <text x="345" y="40" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">processing fails</text>
  <text x="345" y="53" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">retried up to max-attempts</text>

  <line x1="345" y1="60" x2="345" y2="95" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a85)"/>

  <rect x="255" y="100" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="345" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">still failing after max-attempts</text>

  <line x1="345" y1="140" x2="345" y2="165" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a85)"/>

  <rect x="255" y="170" width="180" height="30" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="345" y="190" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">routed to DLQ</text>

  <rect x="480" y="20" width="140" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.3"/>
  <text x="550" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">next message processed normally</text>

  <line x1="435" y1="185" x2="500" y2="60" stroke="#8b949e" stroke-width="1.1" stroke-dasharray="3,3" marker-end="url(#a85)"/>

  <defs><marker id="a85" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A message failing repeatedly is set aside into the DLQ, freeing the main consumer to keep processing everything after it without indefinite blocking.

## 5. Runnable example

The scenario: process `order-placed-events` with error handling for consistently malformed messages. Start with no error handling (a poison message blocks everything), then add retry with a limit, then add dead-lettering once retries are exhausted.

### Level 1 — Basic

No error handling — a consistently failing message blocks the consumer indefinitely.

```java
import java.util.*;

public class DlqLevel1 {
    static void processMessage(String message) {
        if (message.contains("MALFORMED")) throw new RuntimeException("cannot parse: " + message);
        System.out.println("processed: " + message);
    }

    public static void main(String[] args) {
        List<String> queue = List.of("OrderPlaced(1)", "MALFORMED-DATA", "OrderPlaced(3)", "OrderPlaced(4)");

        for (String message : queue) {
            processMessage(message); // no protection at all -- the second message crashes the whole loop
        }
        System.out.println("this line is never reached");
    }
}
```

How to run: `java DlqLevel1.java`

The single malformed message at index 1 throws an uncaught exception, crashing the entire loop — `OrderPlaced(3)` and `OrderPlaced(4)`, both perfectly valid, are never processed at all, purely because they happened to be queued behind one bad message.

### Level 2 — Intermediate

Add retry with a limit — the malformed message gets a few chances (useful if the failure might genuinely be transient) before giving up, without crashing the whole consumer.

```java
import java.util.*;

public class DlqLevel2 {
    static void processMessage(String message) {
        if (message.contains("MALFORMED")) throw new RuntimeException("cannot parse: " + message);
        System.out.println("processed: " + message);
    }

    static void processWithRetry(String message, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                processMessage(message);
                return; // success -- stop retrying
            } catch (RuntimeException e) {
                System.out.println("attempt " + attempt + " failed for '" + message + "': " + e.getMessage());
            }
        }
        System.out.println("gave up on '" + message + "' after " + maxAttempts + " attempts -- but consumer KEEPS RUNNING");
    }

    public static void main(String[] args) {
        List<String> queue = List.of("OrderPlaced(1)", "MALFORMED-DATA", "OrderPlaced(3)", "OrderPlaced(4)");

        for (String message : queue) {
            processWithRetry(message, 3); // consumer never crashes -- moves on after exhausting retries
        }
        System.out.println("all messages processed (or given up on) -- consumer completed normally");
    }
}
```

How to run: `java DlqLevel2.java`

`processWithRetry` catches the exception, retries up to `maxAttempts`, and — critically — the surrounding `for` loop in `main` continues to the next message regardless of whether the current one ultimately succeeded or exhausted its retries. `OrderPlaced(3)` and `OrderPlaced(4)` are correctly processed this time, no longer blocked by the malformed message ahead of them, though the malformed message itself is simply given up on with no record kept of it beyond the console output.

### Level 3 — Advanced

Add a real dead-letter queue: instead of just giving up silently, route the exhausted message into a separate DLQ list for later inspection or manual reprocessing.

```java
import java.util.*;

public class DlqLevel3 {
    static List<String> deadLetterQueue = new ArrayList<>();

    static void processMessage(String message) {
        if (message.contains("MALFORMED")) throw new RuntimeException("cannot parse: " + message);
        System.out.println("processed: " + message);
    }

    static void processWithRetryAndDlq(String message, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                processMessage(message);
                return;
            } catch (RuntimeException e) {
                System.out.println("attempt " + attempt + " failed for '" + message + "': " + e.getMessage());
            }
        }
        deadLetterQueue.add(message); // routed aside, not lost, not blocking anything else
        System.out.println("routed to DLQ: '" + message + "'");
    }

    public static void main(String[] args) {
        List<String> queue = List.of("OrderPlaced(1)", "MALFORMED-DATA", "OrderPlaced(3)", "MALFORMED-DATA-2", "OrderPlaced(5)");

        for (String message : queue) {
            processWithRetryAndDlq(message, 2);
        }

        System.out.println("-- main queue processing complete --");
        System.out.println("messages requiring manual attention: " + deadLetterQueue);
        // an operator (or an automated tool) can now inspect and decide: fix and replay, or discard
    }
}
```

How to run: `java DlqLevel3.java`

`deadLetterQueue` accumulates every message that exhausted its retry attempts — both `"MALFORMED-DATA"` and `"MALFORMED-DATA-2"` end up there — while every valid message (`OrderPlaced(1)`, `OrderPlaced(3)`, `OrderPlaced(5)`) is processed normally and promptly, unblocked by the bad messages ahead of or between them. The final printed `deadLetterQueue` gives an operator (or an automated reprocessing tool) a concrete, complete record of exactly which messages need attention, rather than that information being lost or scattered only through transient log lines.

## 6. Walkthrough

Trace the full run in Level 3.

1. `"OrderPlaced(1)"` is processed first — `processWithRetryAndDlq` calls `processMessage`, which succeeds immediately (no `MALFORMED` substring), so the method returns on attempt 1, printing the success message.
2. `"MALFORMED-DATA"` is processed next — `processMessage` throws on attempt 1, caught and logged; attempt 2 also throws, caught and logged. Since `maxAttempts (2)` is now exhausted, the loop ends without returning, falling through to `deadLetterQueue.add(message)`, adding this message to the DLQ and printing the routing confirmation.
3. `"OrderPlaced(3)"` is processed — succeeds immediately on attempt 1, exactly like the first message, completely unaffected by the malformed message that came before it in the queue.
4. `"MALFORMED-DATA-2"` is processed — fails both attempts identically to the first malformed message, and is also routed to `deadLetterQueue`.
5. `"OrderPlaced(5)"` is processed — succeeds immediately, again unaffected by either preceding failure.
6. After the loop, `deadLetterQueue` contains exactly the two messages that genuinely couldn't be processed: `["MALFORMED-DATA", "MALFORMED-DATA-2"]` — printed clearly at the end, giving a complete, actionable record separate from the successfully-processed messages.

```
queue: [OrderPlaced(1), MALFORMED-DATA, OrderPlaced(3), MALFORMED-DATA-2, OrderPlaced(5)]

OrderPlaced(1)      -> success on attempt 1
MALFORMED-DATA      -> fails x2 -> DLQ
OrderPlaced(3)      -> success on attempt 1 (unblocked, despite the failure right before it)
MALFORMED-DATA-2    -> fails x2 -> DLQ
OrderPlaced(5)      -> success on attempt 1

final DLQ: [MALFORMED-DATA, MALFORMED-DATA-2]   <- nothing lost, nothing silently dropped
```

## 7. Gotchas & takeaways

> **Gotcha:** a DLQ is only useful if something actually monitors it — messages routed to a DLQ that nobody ever looks at are functionally equivalent to silently dropped messages, just with an extra step. Pair DLQ configuration with real alerting (a monitoring check on DLQ depth, a scheduled job that reviews and reports on DLQ contents) so dead-lettered messages actually get investigated rather than accumulating unnoticed indefinitely.

- Dead-letter queues turn "one bad message blocks the whole consumer forever" or "failures are silently lost" into "bad messages are set aside for inspection, and everything else keeps flowing" — a real, necessary safety net for any production messaging consumer.
- `max-attempts` should reflect how likely the failure is to be transient versus permanent — a genuinely malformed message will never succeed no matter how many times it's retried, so excessive retry attempts on it just delay (without preventing) the eventual dead-lettering, wasting processing cycles.
- Retrying too aggressively before dead-lettering can also amplify load if the failure is actually caused by a downstream dependency being unhealthy (rather than the message itself being malformed) — the resilience patterns from the previous section (circuit breaker, especially) are worth combining with retry-then-DLQ handling for that specific failure mode.
- A DLQ preserves the *message*, but recovering from a dead-lettered message (fixing the underlying bug, then replaying it back into the main queue) is a manual or semi-automated process that needs its own deliberate design — the DLQ itself doesn't automatically resolve or retry the underlying problem.
