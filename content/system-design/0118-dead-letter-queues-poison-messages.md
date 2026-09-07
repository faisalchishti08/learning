---
card: system-design
gi: 118
slug: dead-letter-queues-poison-messages
title: Dead-letter queues & poison messages
---

## 1. What it is

A **poison message** is a message that a consumer can never successfully process, no matter how many times it is retried — perhaps its data is malformed, or it triggers a bug every time. A **dead-letter queue (DLQ)** is a separate queue where such messages are moved after they exceed a maximum retry count, instead of being retried forever (which would block the queue) or silently discarded (which would lose the failure entirely).

## 2. Why & when

Under [at-least-once delivery](0114-delivery-semantics-at-most-at-least-exactly-once.md), a consumer that fails to process a message typically causes the broker to redeliver it. If the failure is permanent — not a transient blip like a brief database outage — the same message will fail forever, and if it sits at the front of an ordered queue, it can block every message behind it from ever being processed. A dead-letter queue solves this: after a bounded number of retries, the poison message is moved aside, letting the main queue continue processing everything else, while preserving the failed message for investigation instead of losing it. Use a DLQ any time a consumer's failure could plausibly be permanent (bad data, a bug), not just transient.

## 3. Core concept

- **Retry count tracking:** each message (or its processing attempt) tracks how many times it has been retried since it was first delivered.
- **Retry threshold:** after a configured maximum (e.g. 5 attempts), the message is considered poison rather than transiently failing.
- **Move to DLQ, not discard:** the poison message is moved to a separate DLQ, not deleted — this preserves it for manual inspection, alerting, or a fix-and-replay later, unlike simply dropping it.
- **The main queue keeps moving:** once a poison message is moved out, the consumer can proceed to the next message instead of being stuck retrying the same one forever.
- **Alerting on the DLQ:** since a poison message usually indicates a real bug or bad data upstream, systems typically alert an on-call engineer whenever a message lands in the DLQ, rather than letting it sit unnoticed.
- **Distinguishing transient from permanent failures:** a well-designed consumer should retry transient errors (a temporary network timeout) more times, or with backoff, before giving up, and fail fast to the DLQ for clearly permanent errors (malformed data that will never parse).

## 4. Diagram

```
Main queue: [msg1][msg2 (poison)][msg3][msg4]

  Consumer processes msg1: OK, acknowledged, removed.
  Consumer processes msg2: FAILS. Retry 1: FAILS. Retry 2: FAILS.
  ... Retry 5: FAILS (max retries reached)
      -> msg2 moved to Dead-Letter Queue, alert fired.

Main queue now: [msg3][msg4]   <- consumer can proceed immediately

Dead-Letter Queue: [msg2]   <- preserved for investigation, not lost
```
*Caption: a poison message is moved aside after exceeding its retry limit, so it cannot block the rest of the queue, and is preserved rather than discarded.*

## 5. Runnable example

**Level 1 — Basic.** A consumer retries a failing message up to a maximum count.

**Level 2 — Move to DLQ.** Once retries are exhausted, move the message to a dead-letter queue and continue processing the rest.

**Level 3 — Alerting and replay.** Fire an alert when a message lands in the DLQ, and show fixing the data and replaying it back into the main queue.

```java
// DeadLetterQueue.java
import java.util.*;

public class DeadLetterQueue {

    record Message(String id, String payload) {}

    static int maxRetries = 3;

    static boolean tryProcess(Message msg) {
        // simulates a permanently broken message: this specific payload always fails to parse.
        return !msg.payload().equals("CORRUPTED_DATA");
    }

    public static void main(String[] args) {
        Queue<Message> mainQueue = new LinkedList<>(List.of(
            new Message("msg1", "valid-order-1"),
            new Message("msg2", "CORRUPTED_DATA"), // this one will fail every time
            new Message("msg3", "valid-order-2")
        ));
        Queue<Message> deadLetterQueue = new LinkedList<>();

        // Level 1 & 2: process the queue; retry failures up to maxRetries, then move to DLQ.
        while (!mainQueue.isEmpty()) {
            Message msg = mainQueue.poll();
            int attempts = 0;
            boolean success = false;
            while (attempts < maxRetries && !success) {
                attempts++;
                success = tryProcess(msg);
                System.out.println("processing " + msg.id() + ", attempt " + attempts + ": " + (success ? "OK" : "FAILED"));
            }
            if (!success) {
                deadLetterQueue.add(msg);
                System.out.println("ALERT: " + msg.id() + " exceeded " + maxRetries + " retries -> moved to dead-letter queue");
            } else {
                System.out.println(msg.id() + " processed successfully, acknowledged");
            }
        }

        System.out.println("main queue processing complete. dead-letter queue contains: " + deadLetterQueue);
        System.out.println("-> msg3 was still processed normally, even though msg2 failed permanently");

        // Level 3: investigate, fix, and replay the poisoned message back into the main queue.
        Message poisoned = deadLetterQueue.poll();
        Message fixed = new Message(poisoned.id(), "valid-order-1-corrected"); // data corrected after investigation
        boolean replaySuccess = tryProcess(fixed);
        System.out.println("replaying fixed " + fixed.id() + ": " + (replaySuccess ? "OK, now processed" : "still failing"));
    }
}
```

**How to run:** save as `DeadLetterQueue.java`, then run `java DeadLetterQueue.java`.

## 6. Walkthrough

1. The main loop polls each message and calls `tryProcess` up to `maxRetries` times; for `msg1` and `msg3`, `tryProcess` returns `true` on the first attempt, since their payloads are not `"CORRUPTED_DATA"`.
2. For `msg2`, `tryProcess` always returns `false`, since its payload is exactly `"CORRUPTED_DATA"`; the inner `while` loop runs all 3 allowed attempts, each printed as `FAILED`.
3. After exhausting `maxRetries` with no success, the code adds `msg2` to `deadLetterQueue` and prints an alert — this is the moment a transient-looking retry loop gives up and treats the message as poison.
4. Crucially, the outer loop then continues to `msg3` and processes it normally — `msg2`'s permanent failure never blocked `msg3` from being handled, which is the entire point of moving it aside instead of retrying it forever in place.
5. Level 3 pulls `msg2` back out of the dead-letter queue, constructs a `fixed` version with corrected data, and calls `tryProcess` on it directly — since the corrected payload is no longer `"CORRUPTED_DATA"`, it succeeds, demonstrating the DLQ's role as a holding area for messages that can be inspected, fixed, and replayed rather than being lost forever.

## 7. Gotchas & takeaways

> Gotcha: a dead-letter queue is only useful if something actually looks at it. A DLQ that silently accumulates poison messages with no alerting or monitoring is barely better than discarding them outright — the entire value of a DLQ is that a human (or an automated process) eventually investigates and resolves what landed there.

- A dead-letter queue holds messages that exceeded their retry limit, preventing one permanently failing message from blocking every message behind it.
- Moving to a DLQ preserves the failed message for investigation and possible replay, rather than losing it via a silent discard.
- A DLQ needs active alerting or monitoring to be genuinely useful — messages should be investigated and either fixed-and-replayed or intentionally discarded, not left indefinitely.
- Related concepts: [Delivery semantics (at-most / at-least / exactly-once)](0114-delivery-semantics-at-most-at-least-exactly-once.md) (the retry behavior that leads a message toward a DLQ), [Idempotent consumers](0116-idempotent-consumers.md) (relevant when a replayed DLQ message might have partially succeeded before).
