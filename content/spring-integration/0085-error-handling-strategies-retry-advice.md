---
card: spring-integration
gi: 85
slug: error-handling-strategies-retry-advice
title: "Error handling strategies & retry advice"
---

## 1. What it is

Error handling strategies bring together the different ways a flow can react when a step fails: routing the failure to an error channel for centralized handling, catching and recovering inline, or attaching retry advice (`RequestHandlerRetryAdvice`, built on Spring Retry) to an endpoint so a transient failure is retried automatically before it's ever treated as a true failure. This card covers the overall strategic picture — which approach fits which kind of failure — with `RequestHandlerRetryAdvice` and circuit-breaker advice covered in more depth in the next card (0086).

## 2. Why & when

You reach for a deliberate error-handling strategy because different failures call for genuinely different responses, and treating them all the same way is a common source of both silent data loss and unnecessary alarm:

- **Transient failures should be retried automatically, not surfaced as errors** — a downstream service returning a momentary timeout is often successful on a second attempt moments later; retry advice handles this without ever routing the message to an error channel or bothering a human.
- **Permanent failures need a different destination than transient ones** — a message that will never succeed no matter how many times it's retried (malformed data, a business rule violation) belongs on an error channel or a dead-letter destination for inspection, not stuck in a retry loop that will exhaust itself and still fail.
- **The error channel needs to distinguish "give up cleanly" from "corrupt the flow"** — an unhandled exception with nowhere routed to catch it can, depending on configuration, silently swallow a message or crash a poller thread; an explicit error-handling strategy makes what happens to a failed message a deliberate decision, not an accident of default behavior.

## 3. Core concept

Think of error handling like a hospital's triage system: not every patient (failure) needs the same response. Some just need to wait a few minutes and try walking again (transient failure, handled by a quick retry). Some need to be sent to a specialist for review (permanent failure, routed to an error channel for a human or a separate process to examine). Treating every patient identically — either "send everyone home to rest" or "escalate everyone to the ICU" — would be either dangerously under-responsive or wastefully over-responsive; a good triage strategy matches the response to the actual nature of the problem.

```java
@Bean
public IntegrationFlow orderProcessingFlow() {
    return IntegrationFlow.from("orderChannel")
        .handle(orderService::process,
            e -> e.advice(retryAdvice())) // retries transient failures automatically
        .get();
}

@Bean
public RequestHandlerRetryAdvice retryAdvice() {
    RequestHandlerRetryAdvice advice = new RequestHandlerRetryAdvice();
    advice.setRecoveryCallback(context -> {
        // exhausted all retries -- this is where a permanent-looking failure gets routed onward
        errorChannel().send(new ErrorMessage(context.getLastThrowable()));
        return null;
    });
    return advice;
}
```

Transient failures get quietly retried; only once retries are exhausted does the failure become visible on the error channel.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A failure first goes through retry advice; if a retry succeeds, processing continues normally; if retries are exhausted, the failure routes to an error channel for separate handling rather than being silently lost" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Message processing</text>

  <line x1="110" y1="65" x2="110" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a4)"/>
  <rect x="20" y="90" width="180" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="117" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Fails -&gt; retry advice</text>

  <line x1="200" y1="112" x2="290" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a4)"/>
  <text x="270" y="45" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">retry succeeds</text>
  <rect x="290" y="20" width="180" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Continue normally</text>

  <line x1="200" y1="118" x2="290" y2="145" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a4)"/>
  <text x="270" y="150" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">retries exhausted</text>
  <rect x="290" y="115" width="180" height="45" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="380" y="142" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Route to error channel</text>

  <defs><marker id="a4" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#79c0ff"/></marker></defs>
</svg>

Retry first, absorb transient blips silently; only a genuinely exhausted retry becomes a visible, routed error.

## 5. Runnable example

The scenario: processing an order against a flaky downstream service, simulated with a service that fails a configurable number of times before succeeding (no real Spring Retry dependency needed to demonstrate the retry-then-escalate strategy), starting with a basic retry loop, then adding a distinction between transient and permanent failures, then adding error-channel routing once retries are genuinely exhausted.

### Level 1 — Basic

```java
// ErrorStrategyDemo.java
public class ErrorStrategyDemo {
    static int attemptCount = 0;

    // A service that fails the first two times, then succeeds -- simulating a transient blip.
    static String callFlakyService(String orderId) {
        attemptCount++;
        if (attemptCount < 3) throw new RuntimeException("timeout on attempt " + attemptCount);
        return "confirmed:" + orderId;
    }

    static String withRetry(String orderId, int maxAttempts) {
        for (int i = 0; i < maxAttempts; i++) {
            try {
                return callFlakyService(orderId);
            } catch (RuntimeException ex) {
                System.out.println("Attempt failed: " + ex.getMessage() + ", retrying...");
            }
        }
        throw new RuntimeException("all retries exhausted");
    }

    public static void main(String[] args) {
        String result = withRetry("ORD-1", 5);
        System.out.println("Result: " + result);
    }
}
```

How to run: `java ErrorStrategyDemo.java`. Expected output: two "Attempt failed: ... retrying..." lines followed by `Result: confirmed:ORD-1` — the transient failures absorbed silently by the retry loop until the underlying issue resolves itself.

### Level 2 — Intermediate

```java
// ErrorStrategyDemo.java
public class ErrorStrategyDemo {
    static class TransientException extends RuntimeException {
        TransientException(String msg) { super(msg); }
    }
    static class PermanentException extends RuntimeException {
        PermanentException(String msg) { super(msg); }
    }

    // Real-world concern: not every failure should be retried -- a malformed order will fail
    // identically every time, and retrying it just wastes time before the inevitable failure.
    static String callService(String orderId, boolean malformed, int attemptNumber) {
        if (malformed) throw new PermanentException("invalid order data, will never succeed");
        if (attemptNumber < 3) throw new TransientException("timeout on attempt " + attemptNumber);
        return "confirmed:" + orderId;
    }

    static String withSelectiveRetry(String orderId, boolean malformed, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return callService(orderId, malformed, attempt);
            } catch (TransientException ex) {
                System.out.println("Transient failure, retrying: " + ex.getMessage());
            } catch (PermanentException ex) {
                System.out.println("Permanent failure detected, not retrying: " + ex.getMessage());
                throw ex; // no point retrying, fail fast instead
            }
        }
        throw new RuntimeException("retries exhausted for " + orderId);
    }

    public static void main(String[] args) {
        System.out.println("-- transient failure scenario --");
        System.out.println(withSelectiveRetry("ORD-1", false, 5));

        System.out.println("-- permanent failure scenario --");
        try {
            withSelectiveRetry("ORD-2", true, 5);
        } catch (PermanentException ex) {
            System.out.println("Caught permanent failure at top level, not retried further");
        }
    }
}
```

How to run: `java ErrorStrategyDemo.java`. Expected output: the transient scenario retries twice then succeeds; the permanent scenario fails on the very first attempt with no retry at all, since retrying a malformed order would only waste time reproducing the same guaranteed failure.

### Level 3 — Advanced

```java
// ErrorStrategyDemo.java
import java.util.*;

public class ErrorStrategyDemo {
    static class TransientException extends RuntimeException {
        TransientException(String msg) { super(msg); }
    }
    static class PermanentException extends RuntimeException {
        PermanentException(String msg) { super(msg); }
    }

    static String callService(String orderId, boolean malformed, int attemptNumber, int failUntilAttempt) {
        if (malformed) throw new PermanentException("invalid order data, will never succeed");
        if (attemptNumber < failUntilAttempt) throw new TransientException("timeout on attempt " + attemptNumber);
        return "confirmed:" + orderId;
    }

    // Production concern: once retries are truly exhausted (not just one failure), route to an
    // error channel for separate handling -- a dead-letter queue, an alert, a manual review
    // queue -- rather than losing the message or crashing the calling thread.
    static class ErrorChannel {
        List<String> routedFailures = new ArrayList<>();
        void send(String orderId, String reason) {
            routedFailures.add(orderId + ": " + reason);
            System.out.println("Routed to error channel: " + orderId + " (" + reason + ")");
        }
    }

    static void processWithStrategy(String orderId, boolean malformed, int failUntilAttempt,
                                     int maxAttempts, ErrorChannel errorChannel) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                String result = callService(orderId, malformed, attempt, failUntilAttempt);
                System.out.println("Success: " + result);
                return;
            } catch (PermanentException ex) {
                errorChannel.send(orderId, "permanent: " + ex.getMessage());
                return;
            } catch (TransientException ex) {
                if (attempt == maxAttempts) {
                    errorChannel.send(orderId, "transient retries exhausted: " + ex.getMessage());
                    return;
                }
                System.out.println("Retrying " + orderId + " after: " + ex.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        ErrorChannel errorChannel = new ErrorChannel();

        processWithStrategy("ORD-1", false, 2, 5, errorChannel);       // succeeds after retries
        processWithStrategy("ORD-2", true, 0, 5, errorChannel);        // permanent, no retry
        processWithStrategy("ORD-3", false, 100, 3, errorChannel);     // transient, never recovers within budget

        System.out.println("Total errors routed: " + errorChannel.routedFailures.size());
    }
}
```

How to run: `java ErrorStrategyDemo.java`. Expected output: `ORD-1` retries once and succeeds; `ORD-2` routes immediately to the error channel as a permanent failure with no retry attempted; `ORD-3` retries up to its budget (`3` attempts) and, still failing, routes to the error channel as exhausted transient retries — `Total errors routed: 2` confirming both distinct failure paths correctly reached the error channel while the genuinely recoverable case did not.

## 6. Walkthrough

Trace a message through the full error-handling decision tree.

1. **Processing attempt**: a message reaches a `.handle(...)` step wrapped with retry advice, and the underlying service call executes.
2. **Exception classification**: if the call throws, the flow (or the retry advice's configured recoverable-exception classification) determines whether this looks like a transient failure worth retrying or a permanent one that will never succeed no matter how many times it's attempted.
3. **Transient path — retry**: for a transient failure, the retry advice waits (often with a backoff delay) and attempts the call again, repeating up to a configured maximum number of attempts, with each attempt logged or tracked for visibility.
4. **Transient path — recovery**: if a retry succeeds, processing continues exactly as if the failure never happened — no error channel involvement, no alert, since the system genuinely recovered on its own.
5. **Transient path — exhaustion**: if every retry attempt fails, the retry advice's recovery callback fires, routing the message (typically wrapped as an `ErrorMessage`) to an error channel, since the transient issue has now proven not to be resolving within the retry budget.
6. **Permanent path**: for a failure classified as permanent (a validation error, a business rule violation), the flow skips retrying altogether and routes directly to the error channel — retrying a guaranteed failure only delays the inevitable and wastes resources.
7. **Error channel handling**: whatever consumes the error channel (a dead-letter store, an alerting system, a manual review queue) takes over from there, decoupled entirely from the original processing flow.

```
message -> handler attempt
  throws -> classify: transient or permanent?
    transient -> retry (up to N attempts, with backoff)
       succeeds  -> continue normally
       exhausted -> route to error channel
    permanent -> route to error channel immediately, no retry
```

## 7. Gotchas & takeaways

> **Gotcha:** retrying a failure that is actually permanent (misclassified as transient) doesn't just waste time — if the failed operation has a side effect that partially took hold before failing (a partial write, a message already sent to a third party), blindly retrying it can duplicate that side effect on every attempt; retry logic needs to pair with idempotency where the underlying operation isn't naturally safe to repeat.

- Draw an explicit line between transient and permanent failures in the exception hierarchy or classification logic — treating every exception as retriable, or every exception as immediately fatal, both lead to poor outcomes in different ways.
- Always configure a maximum retry count and a recovery callback — retry advice with no upper bound and no defined behavior on exhaustion can turn a transient failure into an effectively infinite retry loop that never surfaces the problem to anyone.
- Route genuinely failed messages somewhere inspectable (an error channel, a dead-letter store) rather than letting a caught exception simply be logged and discarded — a message an operator can never see again is effectively lost, even if the exception itself was "handled" in a narrow sense.
- Pair retry logic with backoff (increasing delay between attempts) for anything hitting a struggling downstream service — retrying instantly and repeatedly against a service that's already overloaded can make the underlying problem worse rather than helping it recover.
