---
card: microservices
gi: 117
slug: message-acknowledgement-modes
title: "Message acknowledgement modes"
---

## 1. What it is

An acknowledgement (ack) is a consumer telling the broker "I have successfully finished processing this message, you can remove it" (or, for a negative acknowledgement, "I could not process this, do something else with it"). The acknowledgement mode is the policy that determines *when* that ack is considered given: automatically the instant a message is delivered, or only explicitly, after the consumer's processing logic actually completes.

## 2. Why & when

If a broker removes a message the instant it hands it to a consumer, a crash in that consumer between receipt and finishing the work means the message is gone forever, silently — no error, no retry, just lost work. Explicit acknowledgement exists specifically to close that gap: the broker holds the message as "delivered but unconfirmed" until the consumer explicitly says it is done, and redelivers it to another consumer if the original one disappears without acknowledging.

Use automatic (immediate) acknowledgement only when losing an occasional message is genuinely tolerable — a metrics ping, a non-critical log line. Use explicit, manual acknowledgement whenever the message represents something that must not be silently dropped — an order, a payment, an inventory change — which in practice is most business-critical messaging.

## 3. Core concept

With auto-ack, the broker marks a message as consumed the moment it is delivered, regardless of what happens next in the consumer. With manual ack, the broker keeps the message in an "in-flight" state until the consumer calls `ack()` (success) or `nack()`/`reject()` (failure), and redelivers it if the consumer disconnects while it is still in-flight.

```java
// auto-ack: the message is considered "done" the instant receive() returns --
// even if processMessage() below throws
Message msg = channel.receiveAutoAck();
processMessage(msg); // if this throws, the message is ALREADY gone from the broker

// manual ack: the message stays in-flight until explicitly confirmed
Message msg2 = channel.receiveManualAck();
try {
    processMessage(msg2);
    msg2.ack(); // only NOW does the broker consider it done
} catch (Exception e) {
    msg2.nack(); // tell the broker this failed -- it can redeliver
}
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Auto-ack marks a message consumed at delivery time regardless of processing outcome; manual ack keeps the message in-flight until the consumer explicitly confirms success or failure">
  <text x="160" y="30" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Auto-ack</text>
  <rect x="20" y="45" width="90" height="36" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="65" y="67" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">deliver</text>
  <rect x="130" y="45" width="90" height="36" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="175" y="67" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">removed</text>
  <rect x="240" y="45" width="90" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="285" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">process</text>
  <text x="285" y="72" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">(too late if it fails)</text>
  <line x1="110" y1="63" x2="128" y2="63" stroke="#8b949e" marker-end="url(#arr7)"/>

  <text x="450" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Manual ack</text>
  <rect x="340" y="120" width="90" height="36" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="385" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">deliver</text>
  <rect x="450" y="120" width="90" height="36" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="495" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">in-flight</text>
  <text x="495" y="147" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">(held)</text>
  <rect x="560" y="120" width="60" height="36" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="590" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ack()</text>
  <line x1="430" y1="138" x2="448" y2="138" stroke="#8b949e" marker-end="url(#arr7)"/>
  <line x1="540" y1="138" x2="558" y2="138" stroke="#8b949e" marker-end="url(#arr7)"/>

  <defs>
    <marker id="arr7" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Auto-ack removes the message before processing even begins; manual ack holds it until processing actually finishes.

## 5. Runnable example

Scenario: an order-processing consumer that starts with auto-ack and demonstrates the message-loss problem when processing fails, then switches to manual ack to fix that exact problem, and finally adds redelivery for a consumer that crashes mid-processing.

### Level 1 — Basic

```java
// File: AutoAckLossDemo.java -- auto-ack: a failure AFTER delivery still loses the message.
import java.util.*;
import java.util.concurrent.*;

public class AutoAckLossDemo {
    static class AutoAckBroker {
        private final BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        void send(String msg) { queue.offer(msg); }
        String receiveAutoAck() throws InterruptedException {
            String msg = queue.take(); // the broker considers this message GONE the instant it's handed over
            return msg;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        AutoAckBroker broker = new AutoAckBroker();
        broker.send("OrderPlaced:42");

        String msg = broker.receiveAutoAck(); // broker already removed it -- no going back from here
        try {
            processOrder(msg); // this will throw
        } catch (RuntimeException e) {
            System.out.println("Processing failed: " + e.getMessage());
            System.out.println("But the broker already discarded the message -- IT IS LOST, no retry possible.");
        }
    }

    static void processOrder(String msg) {
        throw new RuntimeException("inventory service unavailable");
    }
}
```

**How to run:** `javac AutoAckLossDemo.java && java AutoAckLossDemo` (JDK 17+).

The exception happens *after* the broker already considered the message delivered and done, so there is nothing left to retry — the order is silently lost.

### Level 2 — Intermediate

```java
// File: ManualAckFix.java -- manual ack: the message only leaves the broker's
// "in-flight" set after processing genuinely succeeds.
import java.util.*;
import java.util.concurrent.*;

public class ManualAckFix {
    static class ManualAckBroker {
        private final BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        private final Set<String> inFlight = ConcurrentHashMap.newKeySet();
        void send(String msg) { queue.offer(msg); }

        String receiveManualAck() throws InterruptedException {
            String msg = queue.take();
            inFlight.add(msg); // held here, NOT yet considered done
            return msg;
        }
        void ack(String msg) { inFlight.remove(msg); System.out.println("  ACKed: " + msg); }
        void nack(String msg) { inFlight.remove(msg); queue.offer(msg); System.out.println("  NACKed, requeued: " + msg); }
    }

    public static void main(String[] args) throws InterruptedException {
        ManualAckBroker broker = new ManualAckBroker();
        broker.send("OrderPlaced:42");

        String msg = broker.receiveManualAck();
        try {
            processOrder(msg); // still throws
            broker.ack(msg);
        } catch (RuntimeException e) {
            System.out.println("Processing failed: " + e.getMessage());
            broker.nack(msg); // tell the broker explicitly -- it goes back on the queue
        }

        // prove it's recoverable: receive it again and succeed this time
        String retried = broker.receiveManualAck();
        System.out.println("Retrying: " + retried);
        broker.ack(retried); // succeeds on retry
    }

    static void processOrder(String msg) {
        throw new RuntimeException("inventory service unavailable");
    }
}
```

**How to run:** `javac ManualAckFix.java && java ManualAckFix` (JDK 17+).

Expected output:
```
Processing failed: inventory service unavailable
  NACKed, requeued: OrderPlaced:42
Retrying: OrderPlaced:42
  ACKed: OrderPlaced:42
```

Unlike Level 1, the failed message is not lost — `nack` puts it back on the queue, and a subsequent `receiveManualAck` picks it up for a genuine retry.

### Level 3 — Advanced

```java
// File: RedeliveryOnCrash.java -- adds automatic redelivery when a consumer
// disappears WITHOUT ever calling ack or nack (simulating a crash mid-processing).
import java.util.*;
import java.util.concurrent.*;

public class RedeliveryOnCrash {
    static class ManualAckBroker {
        private final BlockingQueue<String> queue = new LinkedBlockingQueue<>();
        private final Map<String, Long> inFlight = new ConcurrentHashMap<>(); // msg -> delivery timestamp
        private final long visibilityTimeoutMs;

        ManualAckBroker(long visibilityTimeoutMs) { this.visibilityTimeoutMs = visibilityTimeoutMs; }
        void send(String msg) { queue.offer(msg); }

        String receiveManualAck() throws InterruptedException {
            String msg = queue.poll(500, TimeUnit.MILLISECONDS);
            if (msg != null) inFlight.put(msg, System.currentTimeMillis());
            return msg;
        }
        void ack(String msg) { inFlight.remove(msg); }

        // a background sweep a real broker runs: anything in-flight past its
        // visibility timeout with no ack is assumed abandoned (consumer crashed) and requeued
        void sweepExpiredDeliveries() {
            long now = System.currentTimeMillis();
            Iterator<Map.Entry<String, Long>> it = inFlight.entrySet().iterator();
            while (it.hasNext()) {
                Map.Entry<String, Long> entry = it.next();
                if (now - entry.getValue() > visibilityTimeoutMs) {
                    System.out.println("  [broker] visibility timeout expired, redelivering: " + entry.getKey());
                    queue.offer(entry.getKey());
                    it.remove();
                }
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ManualAckBroker broker = new ManualAckBroker(300); // 300ms visibility timeout
        broker.send("OrderPlaced:42");

        String msg = broker.receiveManualAck();
        System.out.println("Consumer A received: " + msg + " -- then CRASHES before calling ack()");
        // note: no ack() call here -- simulates a consumer that died mid-processing

        Thread.sleep(400); // longer than the visibility timeout
        broker.sweepExpiredDeliveries(); // broker notices the abandoned in-flight message

        String redelivered = broker.receiveManualAck();
        System.out.println("Consumer B received (redelivered): " + redelivered);
        broker.ack(redelivered); // this time it completes successfully
        System.out.println("Consumer B: ACKed successfully.");
    }
}
```

**How to run:** `javac RedeliveryOnCrash.java && java RedeliveryOnCrash` (JDK 17+).

Expected output:
```
Consumer A received: OrderPlaced:42 -- then CRASHES before calling ack()
  [broker] visibility timeout expired, redelivering: OrderPlaced:42
Consumer B received (redelivered): OrderPlaced:42
Consumer B: ACKed successfully.
```

## 6. Walkthrough

1. **Level 1** — `receiveAutoAck` returns the message and, by design, the broker has *already* removed it from its bookkeeping the instant `take()` returned; the subsequent `processOrder` call throwing has no way to inform the broker of anything, because as far as the broker is concerned the transaction already completed successfully.
2. **Level 2, delivery without completion** — `receiveManualAck` moves the message into `inFlight` but does *not* remove it from the broker's responsibility; only an explicit `ack` call does that.
3. **Level 2, the failure path** — when `processOrder` throws, the `catch` block calls `broker.nack(msg)`, which removes it from `inFlight` and puts it back on `queue` — the broker now has a second, independent chance to deliver this exact message.
4. **Level 2, the successful retry** — `main` calls `receiveManualAck` a second time, gets the same `"OrderPlaced:42"` message back (this time processing succeeds off-screen), and calls `ack`, which finally, genuinely removes it from `inFlight` — completing the delivery.
5. **Level 3, tracking delivery time** — `inFlight` now maps each message to the timestamp it was delivered, giving the broker a way to notice messages that have been in-flight suspiciously long.
6. **Level 3, "Consumer A" never acking** — `main` calls `receiveManualAck` and deliberately never calls `ack` or `nack` afterward, modeling a consumer process that crashed after receiving the message but before finishing (or even starting) its work.
7. **Level 3, the sweep** — after sleeping past the 300ms `visibilityTimeoutMs`, `sweepExpiredDeliveries` iterates `inFlight`, finds the abandoned entry, and calls `queue.offer` to put it back on the main queue — this mirrors how real brokers (e.g., SQS's visibility timeout, or a JMS redelivery policy) recover from a consumer that disappears without any explicit failure signal at all.
8. **Level 3, "Consumer B" picking it up** — the second `receiveManualAck` call retrieves the redelivered message, processes it (successfully, this time), and calls `ack`, finally completing a delivery that survived a simulated consumer crash with zero message loss.

## 7. Gotchas & takeaways

> **Gotcha:** manual acknowledgement combined with automatic redelivery means a consumer might process the *same* message twice — once by the crashed consumer (which may have partially completed work before dying) and once by the consumer that received the redelivery — so manual-ack processing logic needs to be safe to run more than once on the same message; see [at-most-once / at-least-once / exactly-once delivery](0118-at-most-once-at-least-once-exactly-once-delivery.md).

- Auto-ack marks a message as done at delivery time, before processing even runs — a failure after delivery silently loses the message.
- Manual ack keeps a message "in-flight" until the consumer explicitly confirms success (`ack`) or failure (`nack`/`reject`), closing the silent-loss gap.
- A consumer that disappears entirely, without calling either `ack` or `nack`, is handled by a visibility timeout (or equivalent) that redelivers the message after it has been in-flight too long.
- Business-critical messages should almost always use manual acknowledgement; auto-ack is only appropriate where occasional silent loss is genuinely acceptable.
- Manual ack plus redelivery means consumer logic must tolerate being run more than once on the same message — acknowledgement modes solve message loss, not duplicate delivery.
