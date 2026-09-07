---
card: system-design
gi: 110
slug: message-queues-point-to-point
title: Message queues (point-to-point)
---

## 1. What it is

A **message queue** is a buffer that holds messages between a producer (who sends them) and a consumer (who processes them), so the two do not need to interact directly or at the same time. **Point-to-point** means each message is delivered to and processed by exactly one consumer, even if several consumers are listening on the same queue — like a single ticket at a deli counter that only one server can pick up and handle, even though several servers are waiting.

## 2. Why & when

Without a queue, a producer calling a consumer's service directly must wait for that call to finish, and both services must be available at the same instant. A queue removes that coupling: the producer drops a message and moves on immediately, and the consumer picks it up whenever it is ready, even if it was down a moment ago. Use a point-to-point queue when each unit of work (an order to process, an email to send) should be handled exactly once by exactly one worker, and you want to add more worker instances later purely to process the backlog faster.

## 3. Core concept

- **Producer:** the service that creates and sends a message onto the queue, without knowing or caring which consumer will handle it.
- **Queue:** an ordered (usually FIFO) buffer holding messages until a consumer takes one.
- **Consumer:** a service that pulls a message off the queue, processes it, and acknowledges completion.
- **Competing consumers:** multiple consumer instances can listen on the same queue, but the queue hands each individual message to only one of them — this is what "point-to-point" means, and it is how you scale processing throughput by adding more consumer instances.
- **Acknowledgment:** a consumer tells the queue "I finished this message" only after processing succeeds; if a consumer crashes before acknowledging, the queue makes the message available again for another consumer to pick up.
- **Decoupling in time and space:** the producer does not need the consumer to be running at the same moment, and does not need to know how many consumers exist or where they run.

## 4. Diagram

```
  Producer ---> [ Queue: msg1, msg2, msg3, msg4 ] <--- competing consumers
                        |    |
                 msg1 goes to Consumer A only
                 msg2 goes to Consumer B only
                 (never both - point-to-point delivery)

        Consumer A            Consumer B
        (processing msg1)     (processing msg2)
```
*Caption: multiple consumers can listen on one queue, but each individual message is delivered to and processed by only one of them.*

## 5. Runnable example

**Level 1 — Basic.** A producer enqueues messages; a single consumer dequeues and processes them one at a time.

**Level 2 — Competing consumers.** Two consumer threads pull from the same queue; each message goes to only one.

**Level 3 — Acknowledgment and requeue on failure.** A consumer that fails to process a message puts it back on the queue for another consumer to retry.

```java
// PointToPointQueue.java
import java.util.concurrent.*;
import java.util.*;

public class PointToPointQueue {

    public static void main(String[] args) throws InterruptedException {
        BlockingQueue<String> queue = new LinkedBlockingQueue<>();

        // Level 1: producer enqueues messages.
        for (int i = 1; i <= 4; i++) queue.put("order-" + i);
        System.out.println("queue after producing: " + queue);

        // Level 2: two competing consumers, each pulling whatever is next - never the same message twice.
        List<String> processedByA = Collections.synchronizedList(new ArrayList<>());
        List<String> processedByB = Collections.synchronizedList(new ArrayList<>());

        Runnable consumerA = () -> {
            String msg;
            while ((msg = queue.poll()) != null) processedByA.add(msg);
        };
        Runnable consumerB = () -> {
            String msg;
            while ((msg = queue.poll()) != null) processedByB.add(msg);
        };

        Thread tA = new Thread(consumerA);
        Thread tB = new Thread(consumerB);
        tA.start(); tB.start();
        tA.join(); tB.join();

        System.out.println("processed by consumer A: " + processedByA);
        System.out.println("processed by consumer B: " + processedByB);
        System.out.println("total unique messages processed: " + (processedByA.size() + processedByB.size()) + " (each message handled exactly once)");

        // Level 3: acknowledgment - a message that fails processing is requeued for another consumer.
        BlockingQueue<String> retryQueue = new LinkedBlockingQueue<>();
        retryQueue.put("payment-1");

        String msg = retryQueue.poll();
        boolean processingSucceeded = false; // simulate this consumer failing to process the message
        if (!processingSucceeded) {
            System.out.println("consumer failed to process '" + msg + "', NOT acknowledging - requeueing");
            retryQueue.put(msg); // message goes back on the queue instead of being lost
        }
        System.out.println("queue after failed processing: " + retryQueue + " (available for another consumer to retry)");
    }
}
```

**How to run:** save as `PointToPointQueue.java`, then run `java PointToPointQueue.java`.

## 6. Walkthrough

1. Level 1 fills a `BlockingQueue` with four order messages, modeling a producer that does not know or care who will handle them.
2. Level 2 starts two consumer threads, each looping on `queue.poll()` until the queue is empty. Because `poll()` atomically removes and returns one item, no two threads can ever receive the same message — this is the point-to-point guarantee enforced at the data-structure level.
3. The printed `processedByA` and `processedByB` lists, added together, account for all four original messages, with zero overlap and zero duplication between the two consumers.
4. Level 3 models a single message being pulled off `retryQueue`, then a processing failure (`processingSucceeded = false`). Because the consumer never acknowledges success, the code explicitly puts the message back with `retryQueue.put(msg)`.
5. The final print confirms the message is back in the queue, available for any consumer (this one retrying, or a different instance) to pick up again — this is what prevents work from silently disappearing when a consumer crashes mid-processing.

## 7. Gotchas & takeaways

> Gotcha: if a consumer crashes *after* finishing the real work but *before* sending the acknowledgment, the queue will redeliver the message to another consumer, causing it to be processed twice. Point-to-point queues alone do not prevent this — the consumer's processing logic must be safe to run more than once for the same message; see [idempotent consumers](0116-idempotent-consumers.md).

- A point-to-point queue delivers each individual message to exactly one consumer, even when multiple consumers listen on the same queue.
- Competing consumers let you scale processing throughput horizontally by adding more consumer instances, with no change to the producer.
- Acknowledgment (or its absence) is what lets a queue safely redeliver a message whose consumer failed or crashed mid-processing.
- Related concepts: [Publish/subscribe](0111-publish-subscribe.md) (the opposite delivery model, where every subscriber gets a copy), [Idempotent consumers](0116-idempotent-consumers.md) (needed to handle the redelivery this scheme can cause).
