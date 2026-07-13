---
card: microservices
gi: 125
slug: message-ttl-expiration
title: "Message TTL & expiration"
---

## 1. What it is

Message time-to-live (TTL) is an expiration deadline attached to a message: if the broker cannot deliver (or the consumer cannot successfully process) the message before that deadline, it is discarded, or routed elsewhere (often a [dead letter queue](0123-dead-letter-queue-dlq.md)), rather than staying in the queue indefinitely, growing staler and less useful with every passing moment.

## 2. Why & when

Some data has a genuine shelf life: a "price updated" event is only useful if applied before the price changes again; a "user is typing" indicator is meaningless a minute later; a one-time authentication code must not be honored after its validity window closes. Delivering — or worse, having a consumer act on — a message well past the point where its information was accurate can be actively harmful, not just wasteful. TTL makes that shelf life explicit and enforced by the broker itself, instead of relying on every consumer to independently remember to check a timestamp buried in the payload.

Set a TTL whenever a message's usefulness or correctness genuinely degrades with age — real-time UI updates, time-sensitive pricing, short-lived tokens, cache invalidation events. Skip it for messages that remain fully valid no matter how long they wait (most durable business events, like "an order was placed," don't become wrong just because they took an extra hour to process).

## 3. Core concept

A TTL is set at send time (or as a default policy on the whole channel); the broker tracks each message's expiration and, independently of the consumer, removes anything that ages past that point before it is successfully consumed.

```java
// this price update is only useful for the next 5 seconds -- after that, a fresher one will exist anyway
channel.send("price-updates", priceUpdate, ttlMillis = 5000);

// a consumer that's badly backed up might never even see an expired message --
// the broker discards it before delivery, which is the point
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A message sent with a 5 second TTL is delivered and processed successfully within that window; a second message with the same TTL sits unconsumed past its deadline and is discarded by the broker before a slow consumer ever reaches it">
  <text x="160" y="25" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Within TTL</text>
  <rect x="30" y="40" width="260" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <rect x="30" y="40" width="90" height="30" fill="#6db33f" opacity="0.4"/>
  <text x="75" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">delivered &amp; processed</text>
  <text x="160" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">consumed before the 5s deadline</text>

  <text x="480" y="25" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Past TTL</text>
  <rect x="360" y="40" width="260" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="490" y="60" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">discarded by broker, never delivered</text>
  <text x="490" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">consumer was too slow -- deadline passed first</text>
</svg>

Same TTL, different outcomes: whether a message beats the deadline depends purely on consumer speed relative to the expiration.

## 5. Runnable example

Scenario: a real-time price-update channel that starts with no TTL (showing a stale price silently applied by a slow consumer), adds TTL enforcement so expired updates are discarded before reaching that same slow consumer, and finally routes expired messages to a dead-letter-style channel instead of silently dropping them, for visibility.

### Level 1 — Basic

```java
// File: NoTtlStaleData.java -- no expiration: a slow consumer applies a hopelessly stale price.
import java.util.concurrent.*;

public class NoTtlStaleData {
    record PriceUpdate(String sku, double price, long sentAtMillis) {}

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<PriceUpdate> channel = new LinkedBlockingQueue<>();
        channel.put(new PriceUpdate("SKU-1", 19.99, System.currentTimeMillis()));

        Thread.sleep(8000); // consumer is badly backed up -- 8 SECONDS pass before it even looks

        PriceUpdate update = channel.take();
        long ageMillis = System.currentTimeMillis() - update.sentAtMillis();
        System.out.println("Applying price " + update.price() + " for " + update.sku() + " -- but it is " + ageMillis + "ms stale!");
        System.out.println("The real price has almost certainly changed multiple times since this was sent.");
    }
}
```

**How to run:** `javac NoTtlStaleData.java && java NoTtlStaleData` (JDK 17+).

With no expiration mechanism, the consumer applies whatever it eventually finds, no matter how stale — an 8-second-old price update is treated exactly the same as a fresh one.

### Level 2 — Intermediate

```java
// File: TtlEnforced.java -- the broker itself checks TTL at delivery time and discards expired messages.
import java.util.concurrent.*;

public class TtlEnforced {
    record PriceUpdate(String sku, double price, long sentAtMillis, long ttlMillis) {
        boolean isExpired(long nowMillis) { return (nowMillis - sentAtMillis) > ttlMillis; }
    }

    static class TtlAwareChannel {
        private final BlockingQueue<PriceUpdate> queue = new LinkedBlockingQueue<>();
        void send(PriceUpdate update) { queue.offer(update); }

        PriceUpdate receiveNonExpired() throws InterruptedException {
            while (true) {
                PriceUpdate update = queue.poll(1, TimeUnit.SECONDS);
                if (update == null) return null; // nothing waiting
                if (update.isExpired(System.currentTimeMillis())) {
                    System.out.println("DISCARDED expired update for " + update.sku() + " (age exceeded TTL of " + update.ttlMillis() + "ms) -- never delivered to consumer");
                    continue; // skip it, check the next one
                }
                return update; // fresh enough -- deliver it
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        TtlAwareChannel channel = new TtlAwareChannel();
        channel.send(new PriceUpdate("SKU-1", 19.99, System.currentTimeMillis(), 5000)); // valid for only 5s

        Thread.sleep(8000); // same slow consumer as Level 1 -- 8 seconds pass

        PriceUpdate result = channel.receiveNonExpired();
        System.out.println("Consumer received: " + result + " (null means: correctly nothing usable was delivered)");
    }
}
```

**How to run:** `javac TtlEnforced.java && java TtlEnforced` (JDK 17+).

Expected output:
```
DISCARDED expired update for SKU-1 (age exceeded TTL of 5000ms) -- never delivered to consumer
Consumer received: null (null means: correctly nothing usable was delivered)
```

Unlike Level 1, the stale price is never handed to the consumer at all — the broker enforces the deadline on the message's behalf, regardless of how slow the consumer turned out to be.

### Level 3 — Advanced

```java
// File: ExpiredToDeadLetterChannel.java -- instead of silently discarding, route
// expired messages to a visible channel, so staleness is tracked, not just hidden.
import java.util.*;
import java.util.concurrent.*;

public class ExpiredToDeadLetterChannel {
    record PriceUpdate(String sku, double price, long sentAtMillis, long ttlMillis) {
        boolean isExpired(long nowMillis) { return (nowMillis - sentAtMillis) > ttlMillis; }
    }
    record ExpiredRecord(PriceUpdate update, long expiredAtMillis, long overdueByMillis) {}

    static class TtlAwareChannel {
        private final BlockingQueue<PriceUpdate> queue = new LinkedBlockingQueue<>();
        private final List<ExpiredRecord> expiredChannel = new ArrayList<>(); // visible instead of silently dropped
        void send(PriceUpdate update) { queue.offer(update); }

        PriceUpdate receiveNonExpired() throws InterruptedException {
            while (true) {
                PriceUpdate update = queue.poll(1, TimeUnit.SECONDS);
                if (update == null) return null;
                long now = System.currentTimeMillis();
                if (update.isExpired(now)) {
                    long overdueBy = (now - update.sentAtMillis()) - update.ttlMillis();
                    expiredChannel.add(new ExpiredRecord(update, now, overdueBy));
                    continue;
                }
                return update;
            }
        }

        void reportExpirations() {
            System.out.println("=== " + expiredChannel.size() + " expired message(s) tracked ===");
            for (ExpiredRecord r : expiredChannel) {
                System.out.println("  " + r.update().sku() + ": expired, overdue by " + r.overdueByMillis() + "ms past its TTL");
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        TtlAwareChannel channel = new TtlAwareChannel();
        channel.send(new PriceUpdate("SKU-1", 19.99, System.currentTimeMillis(), 5000));
        channel.send(new PriceUpdate("SKU-2", 45.00, System.currentTimeMillis(), 20_000)); // longer TTL, should survive

        Thread.sleep(8000); // SKU-1 will have expired (TTL 5000ms); SKU-2 has not (TTL 20000ms)

        PriceUpdate delivered = channel.receiveNonExpired();
        System.out.println("Consumer received: " + delivered);
        channel.reportExpirations();
    }
}
```

**How to run:** `javac ExpiredToDeadLetterChannel.java && java ExpiredToDeadLetterChannel` (JDK 17+).

Expected output (timing approximate):
```
Consumer received: PriceUpdate[sku=SKU-2, price=45.0, sentAtMillis=..., ttlMillis=20000]
=== 1 expired message(s) tracked ===
  SKU-1: expired, overdue by 3000ms past its TTL
```

## 6. Walkthrough

1. **Level 1** — `Thread.sleep(8000)` simulates the consumer being backed up; when it finally calls `channel.take()`, the queue hands back the price update regardless of its age, and the consumer applies it as if it were current, with no mechanism even flagging that 8 seconds have elapsed.
2. **Level 2, expiration as part of the message** — `PriceUpdate` now carries `sentAtMillis` and `ttlMillis`, and `isExpired` computes whether `nowMillis - sentAtMillis` has exceeded `ttlMillis` — a self-contained check that doesn't depend on any external clock synchronization beyond the message's own recorded send time.
3. **Level 2, enforcement at receive time** — `receiveNonExpired` loops, polling the queue and checking `isExpired` on whatever it finds; an expired message is logged and the loop `continue`s to check the next one, rather than ever being returned to the caller.
4. **Level 2, the observable difference from Level 1** — after the same 8-second delay, `receiveNonExpired` returns `null` because the only message in the queue had a 5000ms TTL and was found expired; the consumer never sees or acts on stale data, in direct contrast to Level 1's silent staleness.
5. **Level 3, tracking instead of discarding** — `expiredChannel` is a second, visible list that expired messages are appended to (with `overdueByMillis` computed as exactly how far past the deadline the message was found), rather than the expired message simply vanishing with only a log line, as in Level 2.
6. **Level 3, two messages with different TTLs** — `SKU-1` is sent with a 5000ms TTL and `SKU-2` with a 20000ms TTL; after the same 8-second consumer delay, `SKU-1`'s deadline has passed (8000 > 5000) but `SKU-2`'s has not (8000 < 20000), so the two messages take genuinely different paths through `receiveNonExpired` despite being polled by the identical method at the identical wall-clock time.
7. **Level 3, the final state** — the consumer successfully receives `SKU-2` (still valid), while `reportExpirations()` shows exactly one tracked expiration for `SKU-1`, with its overdue amount computed precisely — this is the shape of the visibility a production system needs to notice, alert on, and eventually address *why* a consumer is running behind its message TTLs in the first place, rather than just quietly losing data.

## 7. Gotchas & takeaways

> **Gotcha:** TTL is measured from when the message was sent, not from when the consumer starts trying to process it — a consumer that has been backed up for a while can receive a message that is *already* expired the instant it arrives, meaning "received" and "still valid" are two separate checks a careful consumer needs to make, not one.

- Message TTL gives a message an explicit, broker-enforced expiration, so stale data is discarded (or diverted) instead of being delivered and acted on as if it were current.
- Set TTLs on data whose usefulness or correctness genuinely degrades with age; skip them for data that remains valid indefinitely.
- Silent discarding on expiration hides the underlying problem (a consumer running behind); routing expired messages to a visible channel or [dead letter queue](0123-dead-letter-queue-dlq.md) instead preserves the ability to notice and diagnose it.
- TTL is measured against the message's original send time, so an already-backed-up consumer can encounter already-expired messages the moment it looks, not just ones that expire while it's waiting.
- TTL and retry/DLQ mechanisms solve different problems and often combine: TTL handles "this data is too old to be useful," while DLQ routing handles "this data can never be processed successfully" — a message can be poison, expired, both, or neither.
