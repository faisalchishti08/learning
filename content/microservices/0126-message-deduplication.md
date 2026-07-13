---
card: microservices
gi: 126
slug: message-deduplication
title: "Message deduplication"
---

## 1. What it is

Message deduplication is detecting and discarding a message that has already been processed before, using a stable identifier attached to the message. It is the mechanism, sitting on the broker or producer side, that reduces the number of duplicate deliveries a consumer actually has to deal with — a companion to, not a replacement for, [idempotent consumers](0127-idempotent-consumers.md), which handle whatever duplicates get through anyway.

## 2. Why & when

[At-least-once delivery](0118-at-most-once-at-least-once-exactly-once-delivery.md) guarantees a message won't be lost, at the cost of occasionally delivering it more than once — a network blip between a producer sending and receiving its own send confirmation is enough to trigger an accidental resend of the exact same logical message. Deduplication catches these at the earliest reasonable point (ideally the broker, sometimes the producer itself) so that fewer duplicate messages ever reach a consumer in the first place, reducing the burden on downstream idempotency logic and cutting wasted processing.

Deduplicate whenever producers might resend (retry logic on the producer side after an ambiguous failure — did the send succeed or not?) or when the broker itself might redeliver due to acknowledgement timing. It is cheap insurance layered in front of consumer-side idempotency, not a substitute for it — a consumer should still be built to tolerate an occasional duplicate slipping through.

## 3. Core concept

Every message carries a stable, producer-assigned deduplication id (often called an idempotency key or message id); the broker (or an intermediate deduplication component) tracks recently-seen ids within a bounded window and silently drops any message whose id it has already seen, before it ever reaches a consumer.

```java
String dedupId = UUID.randomUUID().toString(); // generated ONCE, reused across retries of the SAME logical send
for (int attempt = 1; attempt <= 3; attempt++) {
    boolean sent = producer.sendWithDedup(dedupId, orderPlacedEvent); // broker drops it if dedupId was seen before
    if (sent) break;
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A producer resends the same logical message twice with the same deduplication id due to an ambiguous network failure; the broker delivers the first copy to the consumer and silently drops the second, identical-id copy">
  <rect x="20" y="30" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Producer</text>

  <rect x="220" y="20" width="180" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Broker</text>
  <text x="310" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">seen ids: {id-1}</text>

  <rect x="460" y="30" width="150" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Consumer</text>

  <line x1="170" y1="40" x2="218" y2="35" stroke="#8b949e" marker-end="url(#arr12)"/>
  <text x="195" y="20" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">send #1 (id-1)</text>
  <line x1="170" y1="55" x2="218" y2="60" stroke="#8b949e" marker-end="url(#arr12)"/>
  <text x="195" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">retry: send #2 (id-1, same)</text>
  <line x1="400" y1="40" x2="458" y2="40" stroke="#8b949e" marker-end="url(#arr12)"/>
  <text x="430" y="20" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">delivered once</text>

  <text x="310" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">second send with id-1 recognized &amp; dropped</text>

  <defs>
    <marker id="arr12" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The broker's own memory of recently-seen ids is what stops a producer's retry from becoming a second delivery.

## 5. Runnable example

Scenario: an order-submission flow that starts with a producer's ambiguous-failure retry causing a genuine duplicate delivery, then adds broker-side deduplication keyed by a stable id to suppress it, and finally adds a bounded time window for the dedup memory, showing why "seen before" can't be tracked forever.

### Level 1 — Basic

```java
// File: DuplicateFromRetry.java -- an ambiguous send failure causes a genuine, harmful duplicate.
import java.util.*;

public class DuplicateFromRetry {
    static List<String> delivered = new ArrayList<>();

    public static void main(String[] args) {
        String orderPayload = "OrderPlaced:42";

        // attempt 1: the send actually succeeds, but the confirmation is lost on the way back
        boolean confirmationReceived = sendToBroker(orderPayload);
        if (!confirmationReceived) {
            System.out.println("No confirmation received -- was it really not delivered, or just the ACK lost? Retrying to be safe...");
            sendToBroker(orderPayload); // retry: sends the SAME logical order again
        }

        System.out.println("Broker actually delivered: " + delivered);
        System.out.println("BUG: the consumer will process this order TWICE.");
    }

    static boolean sendToBroker(String payload) {
        delivered.add(payload); // the broker DID receive and queue it...
        return false; // ...but we simulate the confirmation getting lost, so the producer thinks it failed
    }
}
```

**How to run:** `javac DuplicateFromRetry.java && java DuplicateFromRetry` (JDK 17+).

Expected output:
```
No confirmation received -- was it really not delivered, or just the ACK lost? Retrying to be safe...
Broker actually delivered: [OrderPlaced:42, OrderPlaced:42]
BUG: the consumer will process this order TWICE.
```

The producer did the right thing by retrying on an ambiguous failure (better than risking silent loss), but without deduplication, that safety-first retry became a real duplicate delivery.

### Level 2 — Intermediate

```java
// File: BrokerSideDedup.java -- same retry behavior, but the broker recognizes the
// repeated deduplication id and drops the second copy before it's ever queued for delivery.
import java.util.*;

public class BrokerSideDedup {
    static class DedupBroker {
        private final Set<String> seenIds = new HashSet<>();
        private final List<String> delivered = new ArrayList<>();

        boolean send(String dedupId, String payload) {
            if (seenIds.contains(dedupId)) {
                System.out.println("Broker recognized duplicate dedupId=" + dedupId + " -- DROPPED, not queued for delivery.");
                return true; // still report success -- the ORIGINAL send already succeeded
            }
            seenIds.add(dedupId);
            delivered.add(payload);
            return true;
        }
    }

    public static void main(String[] args) {
        DedupBroker broker = new DedupBroker();
        String dedupId = "order-42-submission"; // stable id, reused across retries of the SAME logical send
        String orderPayload = "OrderPlaced:42";

        boolean confirmationReceived = false; // simulate the same lost-confirmation scenario as Level 1
        broker.send(dedupId, orderPayload); // attempt 1: succeeds at the broker
        if (!confirmationReceived) {
            System.out.println("No confirmation received -- retrying with the SAME dedupId...");
            broker.send(dedupId, orderPayload); // attempt 2: same id, broker catches it
        }

        System.out.println("Broker actually delivered: " + broker.delivered);
    }
}
```

**How to run:** `javac BrokerSideDedup.java && java BrokerSideDedup` (JDK 17+).

Expected output:
```
No confirmation received -- retrying with the SAME dedupId...
Broker recognized duplicate dedupId=order-42-submission -- DROPPED, not queued for delivery.
Broker actually delivered: [OrderPlaced:42]
```

The exact same ambiguous-failure retry from Level 1 now results in only one genuine delivery, because the broker's `seenIds` check catches the repeated `dedupId` before queuing it again.

### Level 3 — Advanced

```java
// File: BoundedDedupWindow.java -- deduplication memory can't grow forever, so it's
// bounded by a time window; shows both a caught duplicate and one that falls outside the window.
import java.util.*;

public class BoundedDedupWindow {
    static class BoundedDedupBroker {
        record SeenEntry(String dedupId, long seenAtMillis) {}
        private final Deque<SeenEntry> seenWindow = new ArrayDeque<>();
        private final long windowMillis;
        private final List<String> delivered = new ArrayList<>();

        BoundedDedupBroker(long windowMillis) { this.windowMillis = windowMillis; }

        private void evictExpired(long now) {
            while (!seenWindow.isEmpty() && (now - seenWindow.peekFirst().seenAtMillis()) > windowMillis) {
                seenWindow.pollFirst(); // drop entries older than the window -- memory can't grow unbounded
            }
        }

        boolean send(String dedupId, String payload, long nowMillis) {
            evictExpired(nowMillis);
            boolean isDuplicate = seenWindow.stream().anyMatch(e -> e.dedupId().equals(dedupId));
            if (isDuplicate) {
                System.out.println("[t=" + nowMillis + "] duplicate dedupId=" + dedupId + " within window -- DROPPED.");
                return true;
            }
            seenWindow.addLast(new SeenEntry(dedupId, nowMillis));
            delivered.add(payload);
            System.out.println("[t=" + nowMillis + "] dedupId=" + dedupId + " delivered.");
            return true;
        }
    }

    public static void main(String[] args) {
        BoundedDedupBroker broker = new BoundedDedupBroker(5000); // 5 second dedup window

        broker.send("order-42-submission", "OrderPlaced:42", 0);     // t=0: fresh, delivered
        broker.send("order-42-submission", "OrderPlaced:42", 2000);  // t=2000: within window, caught as duplicate
        broker.send("order-42-submission", "OrderPlaced:42", 9000);  // t=9000: OUTSIDE the 5s window, treated as fresh again

        System.out.println("Total delivered: " + broker.delivered.size() + " -- the t=9000 resend was NOT caught (outside dedup window, a real limitation).");
    }
}
```

**How to run:** `javac BoundedDedupWindow.java && java BoundedDedupWindow` (JDK 17+).

Expected output:
```
[t=0] dedupId=order-42-submission delivered.
[t=2000] duplicate dedupId=order-42-submission within window -- DROPPED.
[t=9000] dedupId=order-42-submission delivered.
Total delivered: 2 -- the t=9000 resend was NOT caught (outside dedup window, a real limitation).
```

## 6. Walkthrough

1. **Level 1** — `sendToBroker` genuinely enqueues the payload into `delivered` on the first call, but returns `false` to simulate the confirmation being lost; the producer, unable to distinguish "it failed" from "it succeeded but I didn't hear back," retries — the second call adds a second, identical entry to `delivered`, a real duplicate.
2. **Level 2, the stable id** — `dedupId` is generated once, before any retry logic runs, and is reused identically across both calls to `broker.send`; this is the essential property that makes deduplication possible — a fresh id per attempt would defeat it entirely.
3. **Level 2, the broker's check** — `send` looks up `dedupId` in `seenIds` *before* doing anything else; the first call finds nothing, adds the payload, and records the id; the second call, with the identical `dedupId`, finds it already present and returns without touching `delivered` again.
4. **Level 2, the corrected outcome** — `broker.delivered` ends with exactly one entry despite two send attempts, directly fixing the Level 1 bug, entirely on the broker side, with no change needed to how the consumer processes messages.
5. **Level 3, why an unbounded `seenIds` set is a problem** — a real broker handling millions of messages per day cannot keep every id it has ever seen in memory forever; `BoundedDedupBroker` instead keeps a `Deque` of `(dedupId, seenAtMillis)` pairs and calls `evictExpired` before every check, dropping entries older than `windowMillis`.
6. **Level 3, the two duplicates behaving differently** — the resend at `t=2000` is still within the 5000ms window of the original `t=0` entry, so `evictExpired` doesn't remove it, and the duplicate check correctly catches and drops it; the resend at `t=9000`, however, arrives after the `t=0` entry has aged out of the window (9000 − 0 > 5000), so `evictExpired` has already discarded it, and the check finds no matching id — the message is treated as brand new.
7. **Level 3, the honest limitation shown** — `Total delivered: 2` demonstrates, rather than merely asserts, that deduplication is bounded by its retention window; a genuinely delayed retry (a producer that waits an unusually long time before resending) can still slip through as an apparent duplicate delivery — which is exactly why deduplication is described as reducing, not eliminating, the duplicates a consumer must be prepared to handle.

## 7. Gotchas & takeaways

> **Gotcha:** deduplication is a probabilistic reduction, not an absolute guarantee, once a bounded retention window is involved (and an unbounded one is not practical in a real system) — a consumer still needs to be idempotent for correctness; deduplication is a performance and load-reduction optimization layered in front of that, never a substitute for it.

- Message deduplication uses a stable, producer-assigned id to recognize and drop a resend of the same logical message before it reaches the consumer.
- It exists because producers legitimately need to retry on ambiguous failures (was it delivered or not?), and that safety-first retrying is itself a source of duplicate deliveries.
- The deduplication id must be generated once and reused across retries of the same logical send — a freshly generated id per attempt makes deduplication impossible.
- Practical deduplication windows are bounded in time (or size) for memory reasons, which means a sufficiently delayed duplicate can still slip through undetected.
- Deduplication reduces the *frequency* of duplicates a consumer sees; it does not replace the need for [idempotent consumers](0127-idempotent-consumers.md), which remain the actual correctness guarantee.
