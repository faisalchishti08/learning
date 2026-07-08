---
card: java
gi: 401
slug: blockingqueue-arrayblockingqueue-linkedblockingqueue
title: BlockingQueue (ArrayBlockingQueue, LinkedBlockingQueue)
---

## 1. What it is

`BlockingQueue<E>` is a queue interface built for the **producer-consumer** pattern: it adds blocking versions of add/remove — `put(e)` waits if the queue is full instead of failing, and `take()` waits if the queue is empty instead of returning `null` or throwing. `ArrayBlockingQueue` is a **fixed-capacity**, array-backed implementation you must size up front; `LinkedBlockingQueue` is backed by a linked-node structure and can be created either bounded or (by default) effectively unbounded.

## 2. Why & when

Coordinating producer and consumer threads by hand — a shared `ArrayList` guarded by manual `synchronized`/`wait`/`notify` calls — is tedious and easy to get subtly wrong (missed notifications, spurious wakeups, forgetting to check the condition in a loop). `BlockingQueue` packages all of that correctly-implemented coordination behind a simple queue API: producers call `put()` and don't need to know or care whether any consumer is currently waiting; consumers call `take()` and automatically block until something arrives.

`ArrayBlockingQueue`'s fixed capacity is a feature, not a limitation — it gives you built-in **backpressure**: if consumers can't keep up, producers calling `put()` simply block (slow down) instead of memory ballooning unboundedly. `LinkedBlockingQueue` (unbounded) trades that safety for throughput when you're confident producers won't outpace consumers by much, or you explicitly want a large but still-bounded buffer by passing a capacity to its constructor.

## 3. Core concept

Think of `BlockingQueue` as a **conveyor belt with a maximum length** (for `ArrayBlockingQueue`) between a kitchen (producer) and a cashier (consumer). If the belt is full, the kitchen must pause — it can't just keep stacking dishes on the floor. If the belt is empty, the cashier waits rather than repeatedly checking an empty belt (busy-waiting). This waiting is handled *inside* the queue itself:

```java
BlockingQueue<String> queue = new ArrayBlockingQueue<>(5); // capacity: exactly 5 slots

queue.put("order-1"); // blocks HERE if the queue already has 5 items waiting
String order = queue.take(); // blocks HERE if the queue is currently empty
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Producer threads put items into a bounded queue; consumer threads take items out; put blocks when full, take blocks when empty">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="20" y="60" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="80" y="85" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Producer</text>

  <rect x="220" y="50" width="200" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ArrayBlockingQueue(5)</text>
  <rect x="235" y="80" width="20" height="18" fill="#6db33f"/><rect x="260" y="80" width="20" height="18" fill="#6db33f"/><rect x="285" y="80" width="20" height="18" fill="#6db33f"/><rect x="310" y="80" width="20" height="18" fill="#1c2430" stroke="#8b949e"/><rect x="335" y="80" width="20" height="18" fill="#1c2430" stroke="#8b949e"/>

  <rect x="500" y="60" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Consumer</text>

  <line x1="140" y1="80" x2="215" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a4)"/>
  <text x="177" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">put()</text>
  <line x1="425" y1="80" x2="495" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a5)"/>
  <text x="460" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">take()</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">put() blocks if all 5 slots full; take() blocks if 0 items present</text>

  <defs><marker id="a4" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker><marker id="a5" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

A bounded queue naturally paces a fast producer against a slower consumer, and vice versa.

## 5. Runnable example

Scenario: an order-processing pipeline where a kitchen (producer) puts finished orders on a belt and a cashier (consumer) takes them off — the same belt, evolved from one producer/one consumer, through multiple of each, to a clean shutdown using a "poison pill" and timeout-based polling.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class OrderBeltBasic {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> belt = new ArrayBlockingQueue<>(3);

        Thread kitchen = new Thread(() -> {
            for (int i = 1; i <= 5; i++) {
                try {
                    belt.put("order-" + i); // blocks if the belt (capacity 3) is full
                    System.out.println("Kitchen made order-" + i);
                } catch (InterruptedException ignored) { }
            }
        });

        Thread cashier = new Thread(() -> {
            for (int i = 1; i <= 5; i++) {
                try {
                    String order = belt.take(); // blocks if the belt is empty
                    System.out.println("Cashier served " + order);
                } catch (InterruptedException ignored) { }
            }
        });

        kitchen.start();
        cashier.start();
        kitchen.join();
        cashier.join();
    }
}
```

**How to run:** `java OrderBeltBasic.java`

With belt capacity 3, the kitchen can get at most 3 orders ahead of the cashier before `put()` blocks — this naturally throttles a fast producer to match a slower consumer, with no manual `wait`/`notify` code required.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class OrderBeltMultiple {
    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> belt = new LinkedBlockingQueue<>(10); // bounded LinkedBlockingQueue

        Runnable kitchenWorker = () -> {
            String name = Thread.currentThread().getName();
            for (int i = 1; i <= 3; i++) {
                try {
                    belt.put(name + "-order-" + i);
                } catch (InterruptedException ignored) { }
            }
        };

        Runnable cashierWorker = () -> {
            String name = Thread.currentThread().getName();
            for (int i = 1; i <= 3; i++) {
                try {
                    String order = belt.take();
                    System.out.println(name + " served " + order);
                } catch (InterruptedException ignored) { }
            }
        };

        Thread k1 = new Thread(kitchenWorker, "kitchen-1");
        Thread k2 = new Thread(kitchenWorker, "kitchen-2");
        Thread c1 = new Thread(cashierWorker, "cashier-1");
        Thread c2 = new Thread(cashierWorker, "cashier-2");

        k1.start(); k2.start(); c1.start(); c2.start();
        k1.join(); k2.join(); c1.join(); c2.join();
    }
}
```

**How to run:** `java OrderBeltMultiple.java`

Two kitchen threads and two cashier threads now share the same belt safely — `BlockingQueue` handles all the internal locking, so multiple producers and consumers can `put()`/`take()` concurrently without any of them corrupting the queue's internal state or needing external synchronization.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class OrderBeltShutdown {
    static final String POISON_PILL = "__SHUTDOWN__";

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> belt = new ArrayBlockingQueue<>(5);

        Thread kitchen = new Thread(() -> {
            for (int i = 1; i <= 4; i++) {
                try { belt.put("order-" + i); } catch (InterruptedException ignored) { }
            }
            try { belt.put(POISON_PILL); } catch (InterruptedException ignored) { } // signal "no more orders"
        });

        Thread cashier = new Thread(() -> {
            while (true) {
                try {
                    String order = belt.poll(2, TimeUnit.SECONDS); // times out instead of waiting forever
                    if (order == null) {
                        System.out.println("No order for 2s, checking in...");
                        continue;
                    }
                    if (order.equals(POISON_PILL)) {
                        System.out.println("Cashier received shutdown signal, stopping.");
                        break;
                    }
                    System.out.println("Cashier served " + order);
                } catch (InterruptedException ignored) { }
            }
        });

        kitchen.start();
        cashier.start();
        kitchen.join();
        cashier.join();
    }
}
```

**How to run:** `java OrderBeltShutdown.java`

The **poison pill** pattern (a special sentinel value meaning "stop") lets the consumer know when to exit its loop cleanly, rather than looping forever; `poll(timeout, unit)` (instead of `take()`) additionally lets the consumer periodically check in even while waiting, useful for logging or health-check purposes during idle periods.

## 6. Walkthrough

Execution starts with `main` creating a capacity-5 `ArrayBlockingQueue<String>` and starting two threads: `kitchen` and `cashier`.

**Kitchen thread:** runs a loop from `i=1` to `4`, calling `belt.put("order-" + i)` each time. Since the belt has room for 5 and only 4 real orders plus 1 poison pill are ever produced, `put()` never actually blocks here — each call succeeds immediately. After the loop, the kitchen calls `belt.put(POISON_PILL)`, placing the sentinel string `"__SHUTDOWN__"` as the 5th and final item.

**Cashier thread:** runs an infinite `while (true)` loop. Each iteration calls `belt.poll(2, TimeUnit.SECONDS)` — this either returns an item immediately if one's available, waits up to 2 seconds for one to arrive, or returns `null` if the timeout elapses with nothing available. Since the kitchen is producing quickly, each `poll()` call here returns a real order almost instantly: `"order-1"`, `"order-2"`, `"order-3"`, `"order-4"` in turn, each printed as `"Cashier served order-N"`.

On the 5th call to `poll()`, the item returned is `POISON_PILL` (`"__SHUTDOWN__"`). The `if (order.equals(POISON_PILL))` check catches this, prints `"Cashier received shutdown signal, stopping."`, and `break`s out of the infinite loop — ending the cashier thread cleanly, rather than hanging forever waiting for a 6th item that will never come.

Both `kitchen.join()` and `cashier.join()` in `main` then return once their respective threads finish, and the program exits.

Expected output:
```
Cashier served order-1
Cashier served order-2
Cashier served order-3
Cashier served order-4
Cashier received shutdown signal, stopping.
```

## 7. Gotchas & takeaways

> `LinkedBlockingQueue`'s **no-argument constructor** creates an effectively unbounded queue (capacity `Integer.MAX_VALUE`). If you actually need backpressure (a producer that slows down when consumers fall behind), either use `ArrayBlockingQueue` or pass an explicit capacity to `LinkedBlockingQueue`'s constructor — don't assume "blocking queue" automatically means "bounded."

- `put()` blocks if the queue is full; `take()` blocks if the queue is empty — both handle the necessary waiting internally, no manual `wait`/`notify` needed.
- `ArrayBlockingQueue` is always fixed-capacity and array-backed; `LinkedBlockingQueue` can be bounded or (by default) unbounded, and is linked-node-backed.
- `poll(timeout, unit)` and `offer(item, timeout, unit)` are the timed, non-infinite-wait alternatives to `take()`/`put()` — use them when you need to periodically check in rather than block forever.
- The "poison pill" pattern (a special sentinel value signalling "stop") is a common, clean way to tell a consumer loop to exit once producers are done.
- Multiple producer and consumer threads can safely share one `BlockingQueue` concurrently — all the necessary internal locking is handled for you.
