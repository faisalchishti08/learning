---
card: java
gi: 837
slug: concurrentlinkedqueue-deque
title: ConcurrentLinkedQueue / Deque
---

## 1. What it is

`ConcurrentLinkedQueue` and `ConcurrentLinkedDeque` are thread-safe, **non-blocking** implementations of [`Queue`](0805-queue.md) and [`Deque`](0806-deque.md), built on lock-free algorithms using atomic compare-and-swap (CAS) operations rather than locks. Unlike [`BlockingQueue`](0836-blockingqueue-family-array-linked-priority-delay-synchronous.md) implementations, neither ever blocks a calling thread — `poll()` on an empty queue returns `null` immediately rather than waiting, and `offer()` always succeeds immediately (both are unbounded). Iterators are **weakly consistent**: they never throw `ConcurrentModificationException`, may or may not reflect modifications made during iteration, and are guaranteed to traverse each element that was present at construction time (and not removed) at most once.

## 2. Why & when

`BlockingQueue`'s `put`/`take` are exactly right when a thread genuinely should pause and wait for capacity or for an element to appear — but plenty of concurrent producer-consumer scenarios instead want a thread that, upon finding the queue empty, should do something else entirely (check another data source, perform other work, retry later) rather than block. `ConcurrentLinkedQueue`/`Deque` exist for that non-blocking style: `poll()` returning `null` immediately when empty lets a consumer thread decide for itself how to react, without ever parking. Because they're lock-free rather than lock-based, they also tend to scale better under very high contention from many threads than a lock-based alternative would, at the cost of being unbounded (no built-in backpressure mechanism the way a bounded `ArrayBlockingQueue` provides). Reach for these when the workload needs a genuinely non-blocking, high-throughput concurrent queue/deque and doesn't need bounded capacity or blocking semantics.

## 3. Core concept

```java
ConcurrentLinkedQueue<String> events = new ConcurrentLinkedQueue<>();
events.offer("event-1"); // always succeeds immediately -- unbounded, never blocks

String next = events.poll(); // "event-1" -- removed and returned
String empty = events.poll(); // null -- queue is empty, returns immediately, does NOT block

// A consumer loop reacting to emptiness instead of blocking:
while (true) {
    String event = events.poll();
    if (event == null) {
        break; // or do other work, or retry after a short pause -- the thread's choice, not forced to wait
    }
    // process event
}
```

Both `poll()` calls above return instantly regardless of the queue's state — there is no variant of this class that ever pauses a calling thread, which is the defining difference from the `BlockingQueue` family.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="poll on an empty BlockingQueue's take() blocks the calling thread, while poll on a ConcurrentLinkedQueue returns null immediately without blocking">
  <rect x="40" y="30" width="260" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="170" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">BlockingQueue.take() on empty queue</text>
  <text x="170" y="75" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">thread BLOCKS until an element arrives</text>

  <rect x="340" y="30" width="260" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="470" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ConcurrentLinkedQueue.poll() on empty</text>
  <text x="470" y="75" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">returns null IMMEDIATELY, never blocks</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Same logical situation (queue is empty), fundamentally different thread behavior by design</text>
</svg>

*The defining difference: blocking implementations pause the caller; `ConcurrentLinkedQueue`/`Deque` never do.*

## 5. Runnable example

Scenario: a high-throughput event log consumed by a background worker that should never block, growing from basic non-blocking offer/poll, to a polling consumer loop that gracefully handles emptiness, to demonstrating the weakly-consistent iterator guarantee under concurrent modification.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class EventQueueBasic {
    public static void main(String[] args) {
        ConcurrentLinkedQueue<String> events = new ConcurrentLinkedQueue<>();
        events.offer("login");
        events.offer("click");
        events.offer("logout");

        System.out.println("processing all events:");
        String event;
        while ((event = events.poll()) != null) {
            System.out.println("  " + event);
        }
        System.out.println("poll() on now-empty queue: " + events.poll()); // null, no blocking, no exception
    }
}
```

**How to run:** `java EventQueueBasic.java` (JDK 17+).

Expected output:
```
processing all events:
  login
  click
  logout
poll() on now-empty queue: null
```

The `while ((event = events.poll()) != null)` idiom is the standard non-blocking drain pattern — the loop naturally exits the instant the queue is empty, with no thread ever pausing.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class NonBlockingConsumer {
    public static void main(String[] args) throws InterruptedException {
        ConcurrentLinkedQueue<String> events = new ConcurrentLinkedQueue<>();
        AtomicInteger processedCount = new AtomicInteger();
        AtomicBoolean producingDone = new AtomicBoolean(false);

        Thread producer = new Thread(() -> {
            for (int i = 1; i <= 5; i++) {
                events.offer("event-" + i);
                try { Thread.sleep(20); } catch (InterruptedException ignored) {}
            }
            producingDone.set(true);
        });

        Thread consumer = new Thread(() -> {
            while (!producingDone.get() || !events.isEmpty()) {
                String event = events.poll();
                if (event != null) {
                    processedCount.incrementAndGet();
                } else {
                    // Queue was empty at this instant -- do something else instead of blocking.
                    Thread.onSpinWait(); // hint to the JVM/CPU that this is a brief busy-wait
                }
            }
        });

        producer.start();
        consumer.start();
        producer.join();
        consumer.join();

        System.out.println("total events processed: " + processedCount.get());
    }
}
```

**How to run:** `java NonBlockingConsumer.java`.

Expected output:
```
total events processed: 5
```

The real-world concern added: a consumer that reacts to an empty queue by briefly spinning (`Thread.onSpinWait()`, a JIT/CPU hint for exactly this kind of short busy-wait loop) instead of blocking — appropriate when the expected wait is very short and blocking overhead isn't worth paying, which is a legitimate use case `ConcurrentLinkedQueue` supports directly that `BlockingQueue`'s `take()` doesn't (since `take()` always blocks rather than letting the caller choose to spin).

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class WeaklyConsistentIterator {
    public static void main(String[] args) {
        ConcurrentLinkedQueue<Integer> queue = new ConcurrentLinkedQueue<>(List.of(1, 2, 3, 4, 5));

        Iterator<Integer> it = queue.iterator(); // weakly consistent -- never throws CME

        // Modify the queue WHILE iteration is in progress -- something that would throw
        // ConcurrentModificationException on an ArrayList's fail-fast iterator.
        queue.offer(6);
        queue.poll(); // removes 1 (the head), which the iterator may or may not have already passed

        System.out.println("iterating while concurrently modified (no exception thrown):");
        List<Integer> seen = new ArrayList<>();
        while (it.hasNext()) {
            seen.add(it.next());
        }
        System.out.println("elements observed by this iterator: " + seen);
        System.out.println("final queue contents: " + queue);
        System.out.println("-> weakly consistent: no CME, but the exact set/order seen isn't strictly guaranteed to match any single instant");
    }
}
```

**How to run:** `java WeaklyConsistentIterator.java`. The exact contents of `seen` can vary slightly depending on precise timing relative to the `offer`/`poll` calls, but no exception is ever thrown, and the program always completes normally.

Expected output shape:
```
iterating while concurrently modified (no exception thrown):
elements observed by this iterator: [1, 2, 3, 4, 5, 6]
final queue contents: [2, 3, 4, 5, 6]
-> weakly consistent: no CME, but the exact set/order seen isn't strictly guaranteed to match any single instant
```

This adds the production-flavored hard case: proving the **weakly consistent** iterator guarantee directly. Unlike `ArrayList`'s fail-fast iterator (which throws `ConcurrentModificationException` the moment it detects a concurrent structural change), this iterator simply continues, tolerating concurrent `offer`/`poll` calls without exception — at the cost of not guaranteeing the observed sequence corresponds exactly to the queue's state at any single specific instant. This tradeoff (never throwing, but weaker consistency guarantees) is deliberate and matches the class's overall lock-free design philosophy.

## 6. Walkthrough

Tracing `WeaklyConsistentIterator.main`:

1. `queue` starts with five elements, `1` through `5`. `it = queue.iterator()` obtains a weakly consistent iterator positioned at the current head.
2. `queue.offer(6)` appends a sixth element to the tail — this happens **after** the iterator was created, but because the iterator is weakly consistent (not a hard snapshot like [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)'s), it's permitted (though not guaranteed) to see this newly added element if iteration reaches that point in the underlying linked structure.
3. `queue.poll()` removes and discards the current head (`1`) — again, this happens concurrently with the iterator's existence, and depending on exactly where the iterator's internal cursor is at that moment, it may or may not have already yielded `1` via a prior `next()` call.
4. The `while (it.hasNext())` loop then walks whatever the iterator's internal traversal logic determines is "the remaining elements," collecting them into `seen`. Because both a concurrent addition and a concurrent removal happened, the exact contents of `seen` depend on subtle timing — but critically, no exception is ever thrown, and every element the iterator does report was genuinely present in the queue at some point during this sequence.
5. `queue`'s final printed contents reflect the net effect of all the operations performed (the original five elements, minus the one polled, plus the one offered) — independent of whatever the iterator itself happened to observe, since the iterator's traversal and the queue's actual current state are two different things once concurrent modification is in play.

## 7. Gotchas & takeaways

> **Gotcha:** "weakly consistent" is a **weaker** guarantee than a true snapshot — it promises no `ConcurrentModificationException` and that each element present throughout the iteration (and never removed) is seen at most once, but it does **not** promise the iteration reflects any single consistent point-in-time view of the collection, the way [`CopyOnWriteArrayList`](0815-copyonwritearraylist.md)'s snapshot iterator does. Code that needs a true frozen snapshot for correctness (not just "won't throw") needs a genuinely snapshot-based structure instead.

- `ConcurrentLinkedQueue`/`Deque` are lock-free, thread-safe, and **non-blocking** — `poll()` on an empty instance returns `null` immediately rather than waiting, unlike [`BlockingQueue`](0836-blockingqueue-family-array-linked-priority-delay-synchronous.md)'s `take()`.
- Both are unbounded — there's no built-in capacity limit or backpressure mechanism, unlike `ArrayBlockingQueue`.
- Iterators are weakly consistent: never throw `ConcurrentModificationException`, but don't guarantee reflecting any single consistent instant of the collection's state under concurrent modification.
- Choose these over `BlockingQueue` implementations when a consumer thread should never block on emptiness, instead deciding for itself how to react (spin briefly, do other work, retry later).
- Choose `BlockingQueue` instead when a thread genuinely should pause and wait — for coordination patterns where "wait until work is available" is the actual desired behavior.
