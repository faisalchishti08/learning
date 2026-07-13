---
card: microservices
gi: 124
slug: poison-message-handling
title: "Poison message handling"
---

## 1. What it is

A poison message is one that cannot be successfully processed no matter how many times it's retried — malformed JSON, a reference to data that was deleted, a value that violates a business invariant the consumer enforces. Poison message handling is the set of practices for detecting that a message is poison (rather than just transiently unlucky) and isolating it before it disrupts everything else moving through the same consumer.

## 2. Why & when

Not every failure is the same kind of failure: a downstream database being briefly unreachable is transient and worth retrying; a message whose `orderId` field is literally the string `"null"` because of an upstream serialization bug will fail identically on every retry, forever. Treating both kinds of failure the same way — blind retry — wastes resources on the second kind and, worse, can create a "poison pill" that consumes 100% of a worker's capacity in an infinite retry loop while every other, perfectly healthy message sits waiting behind it.

Build explicit poison message handling into any consumer where malformed or unprocessable input is plausible — in practice, this is essentially all consumers accepting data that ultimately originated from outside the immediate boundary of trusted, validated internal state. A [dead letter queue](0123-dead-letter-queue-dlq.md) is the destination poison messages are typically routed to once identified; poison message handling is the detection and isolation logic that decides *when* to route there.

## 3. Core concept

The consumer distinguishes error types (or, lacking that, tracks a retry count per message) and short-circuits the retry loop for a message that has either failed a threshold number of times or triggered an error category known to be non-retryable (deserialization failures, schema validation errors), isolating just that one message without slowing down or blocking the processing of any other message.

```java
try {
    Order order = deserialize(rawMessage); // a malformed payload throws HERE, before any business logic even runs
    processOrder(order);
    message.ack();
} catch (DeserializationException e) {
    // this category of error will NEVER succeed on retry -- skip straight to quarantine
    quarantine(rawMessage, e);
    message.ack();
} catch (TransientException e) {
    message.nack(); // worth retrying
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A consumer classifies a failure as transient (worth retrying) or poison (never worth retrying); poison messages are quarantined immediately instead of entering the retry loop">
  <rect x="20" y="80" width="140" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="109" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Failure occurs</text>

  <rect x="220" y="20" width="170" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="305" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Transient?</text>
  <text x="305" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; retry (nack)</text>

  <rect x="220" y="140" width="170" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="305" y="162" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Poison?</text>
  <text x="305" y="178" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-&gt; quarantine immediately</text>

  <line x1="160" y1="95" x2="218" y2="50" stroke="#8b949e" marker-end="url(#arr11)"/>
  <line x1="160" y1="105" x2="218" y2="160" stroke="#8b949e" marker-end="url(#arr11)"/>

  <defs>
    <marker id="arr11" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Classifying the failure type lets a poison message skip the retry loop entirely, instead of burning through retries it will never pass.

## 5. Runnable example

Scenario: an order consumer that starts by retrying every failure identically (wasting effort on unrecoverable ones), then adds error-type classification so deserialization failures are quarantined immediately instead of retried, and finally adds a "quarantine after N *identical* failures" heuristic for cases where the error type alone can't tell you it's poison.

### Level 1 — Basic

```java
// File: BlindRetryAll.java -- every failure is retried identically, wasting effort on unrecoverable ones.
import java.util.*;

public class BlindRetryAll {
    public static void main(String[] args) {
        List<String> messages = List.of("{malformed json", "{\"orderId\":42,\"total\":99.9}");
        int maxRetries = 3;

        for (String msg : messages) {
            int attempt = 0;
            boolean succeeded = false;
            while (attempt < maxRetries && !succeeded) {
                attempt++;
                try {
                    processMessage(msg);
                    succeeded = true;
                    System.out.println("Processed: " + msg);
                } catch (RuntimeException e) {
                    System.out.println("Attempt " + attempt + " failed for '" + msg + "': " + e.getMessage());
                }
            }
            if (!succeeded) System.out.println(msg + " exhausted all retries -- but a MALFORMED message was NEVER going to succeed; those 3 attempts were wasted.");
        }
    }

    static void processMessage(String raw) {
        if (raw.startsWith("{malformed")) throw new RuntimeException("JSON parse error");
        System.out.println("  parsed and applied: " + raw);
    }
}
```

**How to run:** `javac BlindRetryAll.java && java BlindRetryAll` (JDK 17+).

The malformed message burns through all three retries identically to how a transient failure would, even though a parse error on attempt 1 already tells us with certainty that attempts 2 and 3 will fail exactly the same way.

### Level 2 — Intermediate

```java
// File: ClassifiedFailures.java -- distinguishing error TYPES to skip pointless retries for poison messages.
import java.util.*;

public class ClassifiedFailures {
    static class DeserializationException extends RuntimeException { DeserializationException(String m) { super(m); } }
    static class TransientException extends RuntimeException { TransientException(String m) { super(m); } }

    public static void main(String[] args) {
        List<String> messages = List.of("{malformed json", "{\"orderId\":42,\"total\":99.9}", "{\"orderId\":43,\"total\":10.0}");
        List<String> quarantined = new ArrayList<>();
        int maxRetriesForTransient = 3;

        for (String msg : messages) {
            try {
                processMessage(msg);
                System.out.println("Processed: " + msg);
            } catch (DeserializationException e) {
                // NEVER retryable -- go straight to quarantine, don't waste a single extra attempt
                quarantined.add(msg);
                System.out.println(msg + " is malformed (" + e.getMessage() + ") -- quarantined immediately, 0 wasted retries.");
            } catch (TransientException e) {
                System.out.println(msg + " hit a transient error, would retry up to " + maxRetriesForTransient + " times: " + e.getMessage());
            }
        }
        System.out.println("Quarantined without wasting retries: " + quarantined);
    }

    static void processMessage(String raw) {
        if (raw.startsWith("{malformed")) throw new DeserializationException("JSON parse error");
        if (raw.contains("\"orderId\":43")) throw new TransientException("inventory service timeout");
        System.out.println("  parsed and applied: " + raw);
    }
}
```

**How to run:** `javac ClassifiedFailures.java && java ClassifiedFailures` (JDK 17+).

Expected output:
```
{malformed json is malformed (JSON parse error) -- quarantined immediately, 0 wasted retries.
Processed: {"orderId":42,"total":99.9}
{"orderId":43,"total":10.0} hit a transient error, would retry up to 3 times: inventory service timeout
Quarantined without wasting retries: [{malformed json]
```

Recognizing `DeserializationException` as a category that can never succeed on retry avoids the wasted attempts from Level 1 entirely, while a genuinely transient error still gets its retry budget.

### Level 3 — Advanced

```java
// File: RepeatedIdenticalFailureHeuristic.java -- for errors that AREN'T obviously
// permanent by type alone, quarantine after N attempts fail with the SAME error signature.
import java.util.*;

public class RepeatedIdenticalFailureHeuristic {
    static class ProcessingException extends RuntimeException {
        final String errorCode;
        ProcessingException(String errorCode, String message) { super(message); this.errorCode = errorCode; }
    }

    static class PoisonDetector {
        private final Map<String, String> lastErrorCodeByMessage = new HashMap<>();
        private final Map<String, Integer> repeatCountByMessage = new HashMap<>();
        private final int suspicionThreshold;
        PoisonDetector(int suspicionThreshold) { this.suspicionThreshold = suspicionThreshold; }

        // returns true if this message should now be quarantined as (probable) poison
        boolean recordFailureAndCheckPoison(String msg, String errorCode) {
            String lastCode = lastErrorCodeByMessage.get(msg);
            if (errorCode.equals(lastCode)) {
                int repeats = repeatCountByMessage.merge(msg, 1, Integer::sum);
                return repeats >= suspicionThreshold; // same exact error, repeatedly -- looks permanent, not transient
            } else {
                lastErrorCodeByMessage.put(msg, errorCode);
                repeatCountByMessage.put(msg, 1);
                return false; // a NEW error type after a different one isn't yet suspicious
            }
        }
    }

    public static void main(String[] args) {
        PoisonDetector detector = new PoisonDetector(3);
        String msg = "{\"orderId\":99,\"customerRef\":\"cust-DELETED\"}"; // references a customer that was deleted
        List<String> quarantined = new ArrayList<>();

        for (int attempt = 1; attempt <= 5 && !quarantined.contains(msg); attempt++) {
            try {
                processMessage(msg);
            } catch (ProcessingException e) {
                System.out.println("Attempt " + attempt + " failed with [" + e.errorCode + "]: " + e.getMessage());
                if (detector.recordFailureAndCheckPoison(msg, e.errorCode)) {
                    quarantined.add(msg);
                    System.out.println("  -> same error repeated " + detector.suspicionThreshold + "x in a row -- quarantining as probable poison after attempt " + attempt);
                }
            }
        }
        System.out.println("Final quarantined set: " + quarantined);
    }

    static void processMessage(String raw) {
        // this failure is not a deserialization error -- it PARSES fine, but the referenced
        // customer genuinely doesn't exist, so it will keep failing identically every time
        throw new ProcessingException("CUSTOMER_NOT_FOUND", "customer cust-DELETED does not exist");
    }
}
```

**How to run:** `javac RepeatedIdenticalFailureHeuristic.java && java RepeatedIdenticalFailureHeuristic` (JDK 17+).

Expected output:
```
Attempt 1 failed with [CUSTOMER_NOT_FOUND]: customer cust-DELETED does not exist
Attempt 2 failed with [CUSTOMER_NOT_FOUND]: customer cust-DELETED does not exist
Attempt 3 failed with [CUSTOMER_NOT_FOUND]: customer cust-DELETED does not exist
  -> same error repeated 3x in a row -- quarantining as probable poison after attempt 3
Final quarantined set: [{"orderId":99,"customerRef":"cust-DELETED"}]
```

## 6. Walkthrough

1. **Level 1** — the retry loop treats a JSON parse failure identically to a transient database hiccup: three identical attempts, three identical failures, with no mechanism recognizing the first failure already proved the outcome of the next two.
2. **Level 2, error type as the classifier** — `DeserializationException` and `TransientException` are distinct exception types; the `catch` blocks handle each differently, and `DeserializationException` skips straight to `quarantined.add(msg)` with zero additional retry attempts, because parse errors are known by their *category* to be permanent.
3. **Level 2, the healthy and transient messages unaffected** — the well-formed message processes immediately, and the "transient" one is logged as eligible for its normal retry budget — classification only changes behavior for the specific category known to be unrecoverable.
4. **Level 3, when the type alone isn't enough** — `ProcessingException` here represents a category of failure (`CUSTOMER_NOT_FOUND`) that *isn't* obviously permanent just from its exception type the way a parse error is — a customer lookup failure could in principle be transient (a replica lag issue) or permanent (the customer really was deleted); the code can't know which just from the type.
5. **Level 3, tracking repeated identical failures** — `PoisonDetector.recordFailureAndCheckPoison` compares each new failure's `errorCode` against the *last* one recorded for that specific message; as long as the exact same `errorCode` keeps recurring, `repeatCountByMessage` climbs.
6. **Level 3, crossing the suspicion threshold** — once the same error code has repeated `suspicionThreshold` (3) times in a row for the same message, `recordFailureAndCheckPoison` returns `true`, and the loop adds the message to `quarantined`, stopping further attempts — the heuristic infers "probably permanent" from the pattern of repeated identical failures rather than from the error type alone.
7. **Level 3, why this is a heuristic, not a certainty** — three identical failures strongly suggest a permanent condition, but it's not proof; a sufficiently long-lived transient outage (a downstream service down for several minutes) could produce the same identical-error pattern — this is why poison detection thresholds are tunable trade-offs, not absolute guarantees, and why quarantined messages still deserve human review rather than automatic deletion.

## 7. Gotchas & takeaways

> **Gotcha:** classifying by error type is only as reliable as the exceptions actually thrown — a poorly designed system that wraps every failure (network timeout, validation error, bug) in the same generic exception type gives poison detection nothing to distinguish on, forcing a fallback to the cruder repeated-failure heuristic, or worse, blind retries; deliberately typed exceptions are what make sharp poison detection possible.

- A poison message is one that will never succeed no matter how many times it's retried, as opposed to a transiently failing message that will likely succeed on a later attempt.
- Classifying failures by type (deserialization errors, validation errors, versus network/timeout errors) is the sharpest and cheapest way to detect poison messages, when the exception types are specific enough to support it.
- When error type alone can't distinguish permanent from transient, a repeated-identical-failure heuristic (same error code, N times in a row) is a reasonable, tunable fallback.
- Quarantining poison messages immediately, rather than exhausting a full retry budget on them, protects the healthy majority of messages from being slowed down or starved by consumer capacity wasted on unrecoverable ones.
- Poison message detection and [dead letter queues](0123-dead-letter-queue-dlq.md) work together: detection decides *when* to give up, the DLQ is *where* the message goes once given up on.
