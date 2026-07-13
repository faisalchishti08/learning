---
card: microservices
gi: 123
slug: dead-letter-queue-dlq
title: "Dead letter queue (DLQ)"
---

## 1. What it is

A dead letter queue is a separate, dedicated queue where messages get routed after they fail processing too many times to be worth retrying automatically — instead of being retried forever or silently discarded, they land somewhere visible where a human or a separate recovery process can inspect and decide what to do with them.

## 2. Why & when

[At-least-once delivery](0118-at-most-once-at-least-once-exactly-once-delivery.md) with redelivery is great for transient failures (a downstream service was briefly down), but a message that fails for a *permanent* reason — malformed data, a bug in the consumer, a business rule that will never be satisfied — will simply be redelivered and fail again forever, endlessly consuming consumer capacity and cluttering logs without ever making progress. A DLQ breaks that infinite loop: after a bounded number of failed attempts, the message is moved out of the main queue entirely, so the main pipeline keeps flowing and the stuck message is parked somewhere for deliberate follow-up.

Configure a DLQ (or the closest equivalent your broker offers) for any queue processing messages where a permanent failure is plausible — which is nearly always, since bad data or unexpected edge cases eventually reach every consumer in production. Skip it only for messages so low-stakes that losing them after retries is an acceptable, deliberate trade-off.

## 3. Core concept

Every failed processing attempt increments a retry counter attached to the message; once that counter crosses a configured threshold, instead of requeueing the message onto the original queue, the consumer (or the broker itself, in brokers with native DLQ support) routes it to the DLQ, tagged with the failure reason, leaving the main queue free to keep processing everything else.

```java
try {
    processOrder(message);
    message.ack();
} catch (Exception e) {
    if (message.deliveryCount() >= maxRetries) {
        deadLetterQueue.send(message, reason = e.getMessage()); // stop retrying, park it
        message.ack(); // acknowledge on the ORIGINAL queue -- it's handled, just handled elsewhere
    } else {
        message.nack(); // still within retry budget -- try again
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A message failing repeatedly is retried up to a limit on the main queue; once the limit is exceeded it is routed to a dead letter queue instead of retried forever, keeping the main queue flowing" >
  <rect x="20" y="70" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="95" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Main queue</text>
  <text x="110" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">retry 1, 2, 3...</text>

  <rect x="250" y="70" width="140" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Consumer</text>
  <text x="320" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">keeps failing</text>

  <rect x="440" y="70" width="170" height="60" rx="6" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="525" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Dead letter queue</text>
  <text x="525" y="112" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">parked for review</text>

  <line x1="200" y1="100" x2="248" y2="100" stroke="#8b949e" marker-end="url(#arr10)"/>
  <path d="M320,70 Q320,20 200,20 Q120,20 120,68" fill="none" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#arr10)"/>
  <text x="220" y="15" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">retry loop (bounded)</text>
  <line x1="390" y1="100" x2="438" y2="100" stroke="#8b949e" marker-end="url(#arr10)"/>
  <text x="415" y="90" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">limit hit</text>

  <defs>
    <marker id="arr10" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Retries loop back to the main queue up to a limit; crossing that limit diverts the message to the DLQ instead of looping forever.

## 5. Runnable example

Scenario: an order-processing consumer that starts with unbounded retries getting stuck forever on a permanently-bad message, then adds a bounded retry count with DLQ routing to unblock the queue, and finally adds a DLQ inspection tool that reports why each parked message failed.

### Level 1 — Basic

```java
// File: InfiniteRetryStuck.java -- no retry limit: a permanently bad message loops forever,
// blocking everything behind it (loop capped here only so the demo terminates).
import java.util.*;
import java.util.concurrent.*;

public class InfiniteRetryStuck {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        queue.put("OrderPlaced:BAD-DATA"); // this one will NEVER succeed, no matter how many times retried
        queue.put("OrderPlaced:42");        // stuck behind it, never gets a chance

        int attempts = 0;
        int demoCap = 5; // in reality this would be unbounded and truly infinite
        while (attempts < demoCap) {
            String msg = queue.peek();
            attempts++;
            try {
                processOrder(msg);
                queue.take();
            } catch (RuntimeException e) {
                System.out.println("Attempt " + attempts + " failed for '" + msg + "': " + e.getMessage() + " -- retrying forever, nothing else gets processed");
            }
        }
        System.out.println("Demo capped at " + demoCap + " attempts; in production this never stops, and OrderPlaced:42 is NEVER reached.");
    }

    static void processOrder(String msg) {
        if (msg.contains("BAD-DATA")) throw new RuntimeException("cannot parse order payload");
    }
}
```

**How to run:** `javac InfiniteRetryStuck.java && java InfiniteRetryStuck` (JDK 17+).

The malformed message is retried without limit and the healthy `OrderPlaced:42` behind it never even gets attempted — a single bad message can stall an entire queue.

### Level 2 — Intermediate

```java
// File: BoundedRetryWithDlq.java -- a retry limit plus a DLQ unblocks the main queue.
import java.util.*;
import java.util.concurrent.*;

public class BoundedRetryWithDlq {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        BlockingQueue<String> deadLetterQueue = new LinkedBlockingQueue<>();
        queue.put("OrderPlaced:BAD-DATA");
        queue.put("OrderPlaced:42");

        Map<String, Integer> attemptCounts = new HashMap<>();
        int maxRetries = 3;

        while (!queue.isEmpty()) {
            String msg = queue.take();
            try {
                processOrder(msg);
                System.out.println("Processed successfully: " + msg);
            } catch (RuntimeException e) {
                int attempts = attemptCounts.merge(msg, 1, Integer::sum);
                if (attempts >= maxRetries) {
                    deadLetterQueue.offer(msg); // give up on the main queue, park it instead
                    System.out.println(msg + " exceeded " + maxRetries + " retries -- moved to DLQ: " + e.getMessage());
                } else {
                    queue.offer(msg); // still within budget -- requeue for another attempt
                    System.out.println(msg + " failed attempt " + attempts + "/" + maxRetries + ", requeued");
                }
            }
        }
        System.out.println("Main queue drained. DLQ contains: " + deadLetterQueue.size() + " message(s).");
    }

    static void processOrder(String msg) {
        if (msg.contains("BAD-DATA")) throw new RuntimeException("cannot parse order payload");
    }
}
```

**How to run:** `javac BoundedRetryWithDlq.java && java BoundedRetryWithDlq` (JDK 17+).

Expected output (order of retries vs. the healthy message may interleave differently, but the shape is the same):
```
Processed successfully: OrderPlaced:42
OrderPlaced:BAD-DATA failed attempt 1/3, requeued
OrderPlaced:BAD-DATA failed attempt 2/3, requeued
OrderPlaced:BAD-DATA exceeded 3 retries -- moved to DLQ: cannot parse order payload
Main queue drained. DLQ contains: 1 message(s).
```

Crucially, `OrderPlaced:42` gets processed successfully without waiting for the bad message to be resolved — the queue as a whole keeps flowing.

### Level 3 — Advanced

```java
// File: DlqInspection.java -- a DLQ that records failure metadata, plus a
// simple inspection tool an operator would use to triage parked messages.
import java.util.*;
import java.util.concurrent.*;

public class DlqInspection {
    record DeadLetter(String originalMessage, String failureReason, int attemptsMade, long parkedAtMillis) {}

    static class BrokerWithDlq {
        private final BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        private final List<DeadLetter> deadLetterQueue = new ArrayList<>();
        private final Map<String, Integer> attemptCounts = new HashMap<>();
        private final int maxRetries;

        BrokerWithDlq(int maxRetries) { this.maxRetries = maxRetries; }
        void send(String msg) { queue.offer(msg); }

        void processAll() {
            while (!queue.isEmpty()) {
                String msg = queue.poll();
                try {
                    processOrder(msg);
                    System.out.println("Processed successfully: " + msg);
                } catch (RuntimeException e) {
                    int attempts = attemptCounts.merge(msg, 1, Integer::sum);
                    if (attempts >= maxRetries) {
                        deadLetterQueue.add(new DeadLetter(msg, e.getMessage(), attempts, System.currentTimeMillis()));
                    } else {
                        queue.offer(msg);
                    }
                }
            }
        }

        void inspectDlq() { // what an operator's triage tool would show
            System.out.println("=== DLQ inspection: " + deadLetterQueue.size() + " message(s) parked ===");
            for (DeadLetter dl : deadLetterQueue) {
                System.out.println("  message: " + dl.originalMessage());
                System.out.println("    reason: " + dl.failureReason());
                System.out.println("    attempts made before parking: " + dl.attemptsMade());
            }
        }
    }

    static void processOrder(String msg) {
        if (msg.contains("BAD-DATA")) throw new RuntimeException("cannot parse order payload");
        if (msg.contains("MISSING-CUSTOMER")) throw new RuntimeException("referenced customer no longer exists");
    }

    public static void main(String[] args) {
        BrokerWithDlq broker = new BrokerWithDlq(3);
        broker.send("OrderPlaced:BAD-DATA");
        broker.send("OrderPlaced:MISSING-CUSTOMER");
        broker.send("OrderPlaced:42");

        broker.processAll();
        broker.inspectDlq();
    }
}
```

**How to run:** `javac DlqInspection.java && java DlqInspection` (JDK 17+).

Expected output:
```
Processed successfully: OrderPlaced:42
=== DLQ inspection: 2 message(s) parked ===
  message: OrderPlaced:BAD-DATA
    reason: cannot parse order payload
    attempts made before parking: 3
  message: OrderPlaced:MISSING-CUSTOMER
    reason: referenced customer no longer exists
    attempts made before parking: 3
```

## 6. Walkthrough

1. **Level 1** — `processOrder` throws every single time for `"OrderPlaced:BAD-DATA"`, and the loop's only response is to log and try again, indefinitely; because `queue.peek()` (not `take()`) is used until success, the bad message is never removed and `"OrderPlaced:42"` behind it is never even looked at.
2. **Level 2, tracking attempts per message** — `attemptCounts.merge(msg, 1, Integer::sum)` increments a counter keyed by the message content each time processing fails, giving each message its own retry budget instead of one global retry state.
3. **Level 2, the branch at the retry limit** — once `attempts >= maxRetries`, the message goes to `deadLetterQueue.offer(msg)` instead of back onto `queue`; critically, it is *not* requeued onto the main `queue` anymore, so the main processing loop's `while (!queue.isEmpty())` condition can actually become true and terminate.
4. **Level 2, the healthy message gets through** — because `"OrderPlaced:42"` was queued right behind the bad message but doesn't throw, it is processed and removed the very first time it's tried, independent of how many retries the bad message is still working through — the queue's overall progress is no longer blocked by one stuck message.
5. **Level 3, richer failure metadata** — `DeadLetter` captures not just the original message but the specific `failureReason` (the exception's message), `attemptsMade`, and a timestamp, giving an operator enough context to diagnose the failure without needing to reproduce it from scratch.
6. **Level 3, two different permanent failures** — `"BAD-DATA"` and `"MISSING-CUSTOMER"` fail for two distinct reasons; both exhaust their retry budgets and land in `deadLetterQueue`, each tagged with its *own* specific `failureReason`, while `"OrderPlaced:42"` again sails through untouched.
7. **Level 3, the inspection tool** — `inspectDlq()` iterates the parked messages and prints each one's original content, failure reason, and attempt count — this is the shape of tooling a real operator or automated alerting system would build on top of a broker's native DLQ feature (most production brokers expose exactly this kind of metadata automatically).

## 7. Gotchas & takeaways

> **Gotcha:** a DLQ that nobody monitors is just a slower, quieter way to lose data — messages that land there still represent real failed work (a customer's order, a payment that didn't process) and need an actual operational process (alerting, a dashboard, a scheduled review) to act on them, or the DLQ becomes a graveyard instead of a safety net.

- A dead letter queue breaks the infinite-retry loop that a permanently-failing message would otherwise cause, keeping the main queue's healthy messages flowing.
- The retry limit that triggers DLQ routing is a deliberate trade-off: too low risks giving up on transient failures too early, too high delays unblocking the queue.
- DLQ entries should carry enough context (original payload, failure reason, attempt count) to let a human or automated process actually diagnose and act on the failure.
- Acknowledging the message on the *original* queue after routing it to the DLQ is essential — otherwise the broker will keep redelivering it there too, defeating the point.
- A DLQ without monitoring or an operational review process is not actually solving the problem, just moving and hiding it.
