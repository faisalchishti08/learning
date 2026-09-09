---
card: system-design
gi: 144
slug: leaky-bucket
title: Leaky bucket
---

## 1. What it is

The **leaky bucket** algorithm smooths out bursty traffic into a steady, fixed-rate stream. Requests arrive and fill a bucket (really a queue); the bucket "leaks" — that is, it processes — requests at a constant rate, no matter how fast they arrived. If the bucket overflows because requests arrive faster than it can leak, the excess requests are dropped. Picture an actual bucket with a small hole in the bottom: water can be poured in fast or slow, but it always drips out at the same steady rate.

## 2. Why & when

A downstream system, such as a database or a legacy service, sometimes needs a perfectly steady request rate and cannot tolerate any burst at all, even a short one that a [token bucket](0143-token-bucket.md) would allow. The leaky bucket enforces this by queuing incoming requests and releasing them strictly at a fixed rate, fully absorbing any burst into the queue (up to its size) instead of letting it through. Use it when you must protect a rate-sensitive downstream dependency, or when you need to shape traffic into a smooth outbound stream, such as sending events to a partner API with a strict per-second limit.

## 3. Core concept

- **Queue with fixed capacity:** incoming requests are placed into a queue; if the queue is full, new requests are rejected outright (bucket overflow).
- **Fixed leak (processing) rate:** the bucket processes queued requests at a constant rate, regardless of how many are waiting or how fast they arrived.
- **No bursts allowed downstream:** unlike a token bucket, a leaky bucket never releases more than one leak-interval's worth of requests at once — the output rate is always smooth, even if the input was bursty.
- **Difference from token bucket:** a token bucket allows the *client* to burst (through accumulated tokens); a leaky bucket absorbs the client's burst into a queue and only lets a smooth stream reach the *downstream* system.
- **Overflow policy:** when the queue is full, you must decide whether to reject the new request immediately, or drop the oldest queued request to make room — this choice depends on whether older or newer requests matter more for your use case.

## 4. Diagram

```
   bursty arrivals            fixed-capacity queue         steady leak rate
   (fast, uneven)             (the "bucket")                (1 request / 200ms)

   req req req req    -->   [ req | req | req ]   -->   drip -> downstream
     |                             |
   arrives faster              full? reject the
   than leak rate               newest incoming request
```
*Caption: requests queue up in the bucket no matter how fast they arrive, but they leak out to the downstream system at one fixed, steady rate.*

## 5. Runnable example

**Level 1 — Basic.** A bounded queue that accepts requests and processes them one at a time.

**Level 2 — Fixed leak rate.** Process queued requests only when enough time has passed since the last one leaked out.

**Level 3 — Overflow rejection.** Reject new requests outright once the queue is full, instead of growing it unbounded.

```java
// LeakyBucketDemo.java
import java.util.*;

public class LeakyBucketDemo {

    static class LeakyBucket {
        final int capacity;
        final long leakIntervalMillis;
        final Deque<String> queue = new ArrayDeque<>();
        long lastLeakTimeMillis;

        LeakyBucket(int capacity, long leakIntervalMillis) {
            this.capacity = capacity;
            this.leakIntervalMillis = leakIntervalMillis;
            this.lastLeakTimeMillis = System.currentTimeMillis();
        }

        // Level 3: reject outright if the queue is already full.
        boolean offer(String requestId) {
            leakIfDue();
            if (queue.size() >= capacity) {
                return false; // overflow - reject the new request
            }
            queue.addLast(requestId);
            return true;
        }

        // Level 2: only leak (process) one request per fixed interval.
        private void leakIfDue() {
            long now = System.currentTimeMillis();
            while (!queue.isEmpty() && now - lastLeakTimeMillis >= leakIntervalMillis) {
                String processed = queue.removeFirst();
                System.out.println("  leaked -> processing " + processed);
                lastLeakTimeMillis += leakIntervalMillis;
            }
        }

        int queued() {
            return queue.size();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        // capacity 3, leaks one request every 200ms
        LeakyBucket bucket = new LeakyBucket(3, 200);

        // Level 1: a burst of 5 requests arrives almost instantly.
        for (int i = 1; i <= 5; i++) {
            boolean accepted = bucket.offer("req-" + i);
            System.out.println("req-" + i + ": " + (accepted ? "queued (queue size=" + bucket.queued() + ")" : "REJECTED (bucket full)"));
        }

        // Let the bucket leak the queued requests at its fixed rate.
        System.out.println("waiting for the bucket to leak...");
        Thread.sleep(700);
        bucket.leakIfDue();
        System.out.println("final queue size: " + bucket.queued());
    }
}
```

**How to run:** save as `LeakyBucketDemo.java`, then run `java LeakyBucketDemo.java`.

## 6. Walkthrough

1. `req-1` through `req-3` arrive almost instantly; each call to `offer` first runs `leakIfDue`, which does nothing since no interval has elapsed, then finds `queue.size() < capacity` and queues the request, so all three are accepted.
2. `req-4` arrives with the queue already at `capacity` (3); `offer` finds `queue.size() >= capacity` and returns `false` before ever touching the queue, so the demo prints "REJECTED (bucket full)".
3. `req-5` arrives immediately after and is rejected the same way, since no time has passed for anything to leak yet.
4. After the `Thread.sleep(700)`, the explicit call to `bucket.leakIfDue()` finds enough elapsed time has passed for multiple 200ms intervals, so its `while` loop removes and "processes" requests one at a time, each iteration advancing `lastLeakTimeMillis` by exactly one `leakIntervalMillis` rather than jumping straight to `now`.
5. The final `queued()` call confirms the queue has drained down as the requests leaked out at the fixed rate, even though they all arrived in a single burst — the defining behavior of a leaky bucket.

## 7. Gotchas & takeaways

> Gotcha: advancing `lastLeakTimeMillis` by setting it to `now` instead of incrementing it by exactly `leakIntervalMillis` per leaked item silently changes the algorithm from "leak at a fixed rate" into "leak in bursts after a delay" — always advance the leak clock by whole intervals, as this example's `while` loop does, to keep the output rate genuinely smooth.

- A leaky bucket smooths bursty input into a strictly steady output rate; a token bucket instead allows the client itself to burst.
- The queue capacity, not a token count, is what bounds how much burst the bucket can absorb before it starts rejecting requests.
- Choosing what to do on overflow (reject the newest vs. drop the oldest) is a real design decision, not an afterthought.
- Related concepts: [Token bucket](0143-token-bucket.md) (the burst-allowing alternative), [Fixed-window counter](0145-fixed-window-counter.md) (a simpler, cruder rate limiter), [Rate-limit response headers & 429 handling](0149-rate-limit-response-headers-429-handling.md) (how to respond to a rejected request).
