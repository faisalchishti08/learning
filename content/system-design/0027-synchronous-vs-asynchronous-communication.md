---
card: system-design
gi: 27
slug: synchronous-vs-asynchronous-communication
title: Synchronous vs asynchronous communication
---

## 1. What it is

**Synchronous communication** means the caller sends a request and waits, blocked, until it receives a response before doing anything else. **Asynchronous communication** means the caller sends a request (often to a queue) and continues immediately with other work, without waiting for the request to finish — the result, if any, arrives later, separately.

Think of the difference between a phone call (synchronous — you wait on the line for an answer) and sending a letter (asynchronous — you drop it in the mailbox and go about your day, and a reply arrives later, if at all).

## 2. Why & when

This is one of the most consequential choices in a multi-service design, because it decides how failures and slowness in one service affect the rest of the system. You bring this up whenever a design involves one service calling another, especially for actions where the caller does not strictly need an immediate result to keep working (like "send a confirmation email after checkout" versus "check if this item is in stock before completing checkout").

## 3. Core concept

**Synchronous communication (e.g. a direct REST or gRPC call):**
- Simple to reason about: the caller gets an immediate result or an immediate error.
- The caller is **blocked** for the entire duration of the call, including however long the callee takes.
- **Failure and slowness propagate directly:** if the called service is slow or down, the caller is slow or stuck too — this can cascade across a whole chain of synchronous calls, sometimes called a "cascading failure".
- Good fit when the caller genuinely cannot proceed without the answer (e.g. "is this item in stock?" before allowing checkout to continue).

**Asynchronous communication (e.g. publishing a message to a queue):**
- The caller submits work and moves on immediately; it does not wait for the work to finish.
- **Decouples the two services in time:** the receiving service can be temporarily down or slow, and the message simply waits in the queue until it recovers — the caller was never blocked on it.
- Adds complexity: the caller usually cannot get an immediate result back this way, so the design needs another mechanism if the caller ever needs to know the outcome (like a follow-up notification, a webhook, or the caller polling for status later).
- Good fit for work that can happen "eventually" without blocking the user (sending an email, generating a thumbnail, logging an analytics event, processing a payment in the background after confirming the order was received).

**The core design tradeoff:** synchronous calls are simpler but couple services tightly, so one slow or failing service can drag down everything that calls it. Asynchronous calls decouple services and improve resilience to partial failure, at the cost of design complexity (you need a queue, and a way to eventually deliver results back if needed).

## 4. Diagram

```
 SYNCHRONOUS                              ASYNCHRONOUS
 Caller  -->  Service B                   Caller --> [queue] --> Service B
   |  (blocked, waiting)  |                  |  (continues immediately)
   |<---- response -------|                  |
                                            (if B is slow/down, message just
 if B is slow/down, CALLER                   waits in the queue; caller was
 is slow/stuck too                           never blocked on it)
```
*Caption: synchronous calls block the caller on the callee's speed and health; asynchronous calls decouple the two through a queue.*

## 5. Runnable example

### Artifact: a Java simulation contrasting a blocked synchronous call against a non-blocking asynchronous, queue-based call

```java
import java.util.concurrent.*;

public class SyncVsAsyncSim {

    // Simulates a slow downstream service call, taking 200ms.
    static String slowDownstreamCall() throws InterruptedException {
        Thread.sleep(200);
        return "order confirmed";
    }

    static void synchronousCall() throws InterruptedException {
        long start = System.currentTimeMillis();
        String result = slowDownstreamCall(); // caller is BLOCKED here for 200ms
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Synchronous: caller blocked for " + elapsed + "ms, got: " + result);
        System.out.println("Synchronous: caller can now do its NEXT task, only after waiting.");
    }

    static void asynchronousCall() throws InterruptedException {
        long start = System.currentTimeMillis();
        ExecutorService queueWorker = Executors.newSingleThreadExecutor();

        queueWorker.submit(() -> {
            try {
                String result = slowDownstreamCall(); // happens in the background
                System.out.println("Async: background work finished, result: " + result);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });

        long elapsedBeforeContinuing = System.currentTimeMillis() - start;
        System.out.println("Asynchronous: caller submitted work and moved on after " + elapsedBeforeContinuing + "ms");
        System.out.println("Asynchronous: caller is now free to do its NEXT task immediately.");

        queueWorker.shutdown();
        queueWorker.awaitTermination(1, TimeUnit.SECONDS); // just so main() waits to print the background result
    }

    public static void main(String[] args) throws InterruptedException {
        synchronousCall();
        System.out.println("---");
        asynchronousCall();
    }
}
```

**How to run:** save as `SyncVsAsyncSim.java`, run `java SyncVsAsyncSim.java` (JDK 17+).

## 6. Walkthrough

1. `slowDownstreamCall` simulates a downstream service that takes 200 milliseconds to respond, standing in for a real network call to another service.
2. `synchronousCall` calls it directly and waits: `Thread.sleep(200)` inside the call blocks the calling thread for the full 200ms before any further code in this method can run.
3. `asynchronousCall` instead submits the same slow work to a background worker (`ExecutorService`, standing in for a message queue and its worker) and immediately continues to its own next line of code, without waiting for the background work to finish.
4. Output (approximate, since real timing varies slightly):
```
Synchronous: caller blocked for 201ms, got: order confirmed
Synchronous: caller can now do its NEXT task, only after waiting.
---
Asynchronous: caller submitted work and moved on after 1ms
Asynchronous: caller is now free to do its NEXT task immediately.
Async: background work finished, result: order confirmed
```
5. Notice the asynchronous caller printed "moved on" almost instantly (1ms), while the background result only appeared afterward, once the slow call actually finished. The synchronous caller, by contrast, could not print anything else until the full 201ms had passed. This is the entire tradeoff in one run: synchronous ties your progress to the callee's speed; asynchronous does not.

## 7. Gotchas & takeaways

> **Gotcha:** using asynchronous communication for something the user is actively waiting to see the result of, like "did my payment succeed?" on a checkout page. Async fits work that can happen in the background; it is the wrong choice when the caller genuinely needs an answer before it can proceed or respond to the user.

- Synchronous: simple, immediate result, but couples the caller's speed and health to the callee's.
- Asynchronous: decouples services in time and improves resilience to a slow or failing downstream service, at the cost of added design complexity.
- Choose based on whether the caller can genuinely proceed without an immediate answer — if yes, prefer async for better resilience; if no, synchronous is the right, simpler choice.
