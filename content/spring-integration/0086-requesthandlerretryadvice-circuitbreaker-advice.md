---
card: spring-integration
gi: 86
slug: requesthandlerretryadvice-circuitbreaker-advice
title: "RequestHandlerRetryAdvice / CircuitBreaker advice"
---

## 1. What it is

`RequestHandlerRetryAdvice` and `RequestHandlerCircuitBreakerAdvice` are two concrete, attachable advices (both built on Spring Retry) that wrap a message handler with resilience behavior: the retry advice re-attempts a failed call a configured number of times with optional backoff, while the circuit-breaker advice tracks failure counts and, once a threshold is crossed, stops attempting the call at all for a cooldown period — failing fast instead of continuing to hammer a service that's clearly already struggling.

## 2. Why & when

You reach for these specific advices to attach concrete, off-the-shelf resilience behavior to an endpoint without hand-writing retry or circuit-breaking logic:

- **A downstream call fails occasionally and a second attempt usually succeeds** — `RequestHandlerRetryAdvice` handles this directly, configured with a maximum attempt count and a backoff policy, without the flow's own handler code needing any retry logic embedded in it.
- **A downstream service is having a sustained outage, and continuing to retry every message only adds load to an already-failing system** — `RequestHandlerCircuitBreakerAdvice` detects the sustained failure pattern and stops attempting calls for a cooldown period, letting the struggling service recover instead of being bombarded by a stream of retried requests from every failing message.
- **Both advices are meant to compose** — a handler can be wrapped with retry advice (to absorb brief blips) and circuit-breaker advice (to detect a sustained outage and stop hammering it) at the same time, each addressing a different failure timescale.

## 3. Core concept

Think of `RequestHandlerRetryAdvice` as knocking on a door a few more times if there's no answer — reasonable when someone might just be a moment away from answering. Think of `RequestHandlerCircuitBreakerAdvice` as recognizing, after enough consecutive no-answers, that continuing to knock is pointless and possibly rude — so it stops knocking altogether for a while, coming back to try again only after a cooldown period has passed, rather than knocking incessantly the whole time no one's answering.

```java
@Bean
public IntegrationFlow resilientCallFlow() {
    return IntegrationFlow.from("paymentRequests")
        .handle(paymentGateway::charge, e -> e.advice(retryAdvice(), circuitBreakerAdvice()))
        .get();
}

@Bean
public RequestHandlerRetryAdvice retryAdvice() {
    RequestHandlerRetryAdvice advice = new RequestHandlerRetryAdvice();
    advice.setRetryTemplate(RetryTemplate.builder().maxAttempts(3).fixedBackoff(500).build());
    return advice;
}

@Bean
public RequestHandlerCircuitBreakerAdvice circuitBreakerAdvice() {
    RequestHandlerCircuitBreakerAdvice advice = new RequestHandlerCircuitBreakerAdvice();
    advice.setThreshold(5);       // open the circuit after 5 consecutive failures
    advice.setHalfOpenAfter(30_000); // try again after 30 seconds
    return advice;
}
```

Each individual call gets up to 3 quick retry attempts; if the gateway has been failing consistently across many messages, the circuit breaker stops even attempting calls for 30 seconds at a time.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A circuit breaker moves through CLOSED (calls go through), OPEN (calls fail fast without attempting the downstream service), and HALF-OPEN (a trial call decides whether to close again or reopen)" >
  <rect x="20" y="20" width="170" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">CLOSED</text>
  <text x="105" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">calls go through normally</text>

  <line x1="190" y1="47" x2="270" y2="47" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a5)"/>
  <text x="230" y="38" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">threshold failures</text>

  <rect x="270" y="20" width="170" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="355" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OPEN</text>
  <text x="355" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fail fast, no call attempted</text>

  <line x1="440" y1="47" x2="520" y2="47" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a5)"/>
  <text x="480" y="38" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">cooldown elapses</text>

  <rect x="520" y="20" width="100" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">HALF-OPEN</text>
  <text x="570" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">one trial call</text>

  <path d="M 520 65 Q 300 130 105 75" stroke="#6db33f" stroke-width="1.5" fill="none" marker-end="url(#a5)"/>
  <text x="320" y="130" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">trial succeeds -&gt; back to CLOSED</text>

  <path d="M 520 78 Q 400 150 190 78" stroke="#8b949e" stroke-width="1.5" fill="none" marker-end="url(#a5)"/>
  <text x="330" y="160" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">trial fails -&gt; back to OPEN, cooldown restarts</text>

  <defs><marker id="a5" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker></defs>
</svg>

The circuit breaker's three states cycle based on observed failures and a trial call, not a fixed schedule.

## 5. Runnable example

The scenario: calling a payment gateway that fails for a sustained period, simulated with a plain state machine standing in for `RequestHandlerCircuitBreakerAdvice` combined with a simple retry loop (no real Spring Retry dependency needed to demonstrate the retry-plus-circuit-breaker composition), starting with basic retry only, then adding a circuit breaker that opens after repeated failures across multiple messages, then adding the half-open trial recovery behavior.

### Level 1 — Basic

```java
// ResilienceAdviceDemo.java
public class ResilienceAdviceDemo {
    static int callCount = 0;

    static String chargeCard(String orderId) {
        callCount++;
        throw new RuntimeException("gateway down, attempt " + callCount);
    }

    static String withRetry(String orderId, int maxAttempts) {
        for (int i = 0; i < maxAttempts; i++) {
            try {
                return chargeCard(orderId);
            } catch (RuntimeException ex) {
                System.out.println("Retry failed: " + ex.getMessage());
            }
        }
        return "FAILED after retries";
    }

    public static void main(String[] args) {
        System.out.println(withRetry("ORD-1", 3));
    }
}
```

How to run: `java ResilienceAdviceDemo.java`. Expected output: three "Retry failed: ..." lines then `FAILED after retries` — retry alone keeps attempting the call for every message with no memory of past failures across calls.

### Level 2 — Intermediate

```java
// ResilienceAdviceDemo.java
public class ResilienceAdviceDemo {
    // Real-world concern: retrying each message independently means a sustained outage still
    // gets hammered by every incoming message's own retry attempts. A circuit breaker tracks
    // failures ACROSS messages and stops attempting calls once a threshold is crossed.
    static class CircuitBreaker {
        private int consecutiveFailures = 0;
        private final int threshold;
        private boolean open = false;

        CircuitBreaker(int threshold) { this.threshold = threshold; }

        boolean isOpen() { return open; }

        void recordFailure() {
            consecutiveFailures++;
            if (consecutiveFailures >= threshold) {
                open = true;
                System.out.println("Circuit OPENED after " + consecutiveFailures + " consecutive failures");
            }
        }

        void recordSuccess() { consecutiveFailures = 0; }
    }

    static String chargeCard(String orderId) {
        throw new RuntimeException("gateway down");
    }

    public static void main(String[] args) {
        CircuitBreaker breaker = new CircuitBreaker(3);

        for (int i = 1; i <= 5; i++) {
            if (breaker.isOpen()) {
                System.out.println("Message " + i + ": circuit open, failing fast (no call attempted)");
                continue;
            }
            try {
                chargeCard("ORD-" + i);
            } catch (RuntimeException ex) {
                System.out.println("Message " + i + " failed: " + ex.getMessage());
                breaker.recordFailure();
            }
        }
    }
}
```

How to run: `java ResilienceAdviceDemo.java`. Expected output: messages 1-3 each fail and are logged, with the circuit opening after the third; messages 4 and 5 print "circuit open, failing fast (no call attempted)" — no further calls to the already-struggling gateway are made, sparing it additional load while it's clearly down.

### Level 3 — Advanced

```java
// ResilienceAdviceDemo.java
public class ResilienceAdviceDemo {
    static class CircuitBreaker {
        private int consecutiveFailures = 0;
        private final int threshold;
        private final long cooldownMillis;
        private boolean open = false;
        private long openedAtMillis = 0;

        CircuitBreaker(int threshold, long cooldownMillis) {
            this.threshold = threshold;
            this.cooldownMillis = cooldownMillis;
        }

        // Production concern: after the cooldown, allow exactly ONE trial call through
        // (half-open) rather than either staying permanently open or fully reopening the
        // floodgates -- the trial's outcome decides whether service has actually recovered.
        boolean allowCall(long nowMillis) {
            if (!open) return true;
            if (nowMillis - openedAtMillis >= cooldownMillis) {
                System.out.println("Cooldown elapsed, allowing one HALF-OPEN trial call");
                return true;
            }
            return false;
        }

        void recordFailure(long nowMillis) {
            consecutiveFailures++;
            if (consecutiveFailures >= threshold) {
                if (!open) System.out.println("Circuit OPENED after " + consecutiveFailures + " consecutive failures");
                open = true;
                openedAtMillis = nowMillis; // reopening also restarts the cooldown clock
            }
        }

        void recordSuccess() {
            if (open) System.out.println("Trial call succeeded, circuit CLOSED");
            consecutiveFailures = 0;
            open = false;
        }
    }

    public static void main(String[] args) {
        CircuitBreaker breaker = new CircuitBreaker(2, 1000);
        boolean[] gatewayIsDown = { true, true, true, true, false }; // recovers on message 5

        long now = 0;
        for (int i = 0; i < gatewayIsDown.length; i++) {
            if (!breaker.allowCall(now)) {
                System.out.println("Message " + (i + 1) + ": circuit open, failing fast");
            } else if (gatewayIsDown[i]) {
                System.out.println("Message " + (i + 1) + ": call failed");
                breaker.recordFailure(now);
            } else {
                System.out.println("Message " + (i + 1) + ": call succeeded");
                breaker.recordSuccess();
            }
            now += 600; // messages arrive every 600ms; cooldown is 1000ms
        }
    }
}
```

How to run: `java ResilienceAdviceDemo.java`. Expected output: messages 1-2 fail and open the circuit; message 3 (at t=1200ms, past the 1000ms cooldown) gets a half-open trial that also fails, reopening the circuit and restarting the cooldown; message 4 fails fast since the new cooldown hasn't elapsed; message 5's trial (gateway now recovered) succeeds and closes the circuit — demonstrating the full open/half-open/closed cycle reacting to real recovery rather than just a fixed timer.

## 6. Walkthrough

Trace a sequence of payment attempts through both advices working together.

1. **Normal operation (circuit CLOSED)**: each message's `.handle(...)` call goes through, wrapped first by retry advice (a few quick attempts on failure) and then by the circuit breaker's failure tracking, which increments its consecutive-failure count on each retry-exhausted failure.
2. **Threshold crossed (circuit OPENS)**: once enough messages in a row have exhausted their retries and failed, the circuit breaker flips to OPEN — from this point, incoming messages don't even attempt the downstream call; they fail fast immediately, and the circuit-open state itself becomes the "error" the flow reacts to (routing to an error channel, for instance).
3. **Cooldown period**: while OPEN, every message fails immediately without touching the actual downstream service — this is the entire point, sparing an already-overloaded or down service from being hit by a continuous stream of retried requests it cannot currently handle anyway.
4. **Cooldown elapses (circuit HALF-OPEN)**: once the configured cooldown has passed, the next incoming message is allowed through as a trial call, to test whether the downstream service has actually recovered.
5. **Trial succeeds (circuit CLOSES)**: if the trial call succeeds, the circuit breaker resets its failure count and returns to CLOSED, resuming normal call-through behavior for all subsequent messages.
6. **Trial fails (circuit reopens)**: if the trial call also fails, the circuit breaker immediately reopens and restarts its cooldown timer, deferring the next trial attempt further into the future rather than repeatedly hammering a service that clearly hasn't recovered yet.

```
message arrives -> circuit state?
  CLOSED    -> attempt call (with retry advice) -> success: continue, stay CLOSED
                                                 -> failure: increment count -> threshold? -> OPEN
  OPEN      -> fail fast, no call attempted -> cooldown elapsed? -> HALF-OPEN trial
  HALF-OPEN -> one trial call -> succeeds: CLOSED
                              -> fails: OPEN again, cooldown restarts
```

## 7. Gotchas & takeaways

> **Gotcha:** retry advice and circuit-breaker advice operate on different timescales and can interact in a surprising way if misconfigured — if the retry advice's own attempts (with backoff) take longer than the circuit breaker's failure-counting window expects, the circuit may open more slowly (or quickly) than intended; tune the retry attempt count/backoff and the circuit breaker's threshold together, not independently.

- Retry advice absorbs brief, per-call blips; circuit-breaker advice protects against sustained, cross-message outages — they solve different problems on different timescales, and using only one leaves the other gap uncovered.
- A circuit breaker's failing-fast behavior during the OPEN state is a feature, not a bug to work around — it protects the downstream service from pointless additional load and gives the calling flow a fast, predictable failure to route elsewhere (a fallback, a queued retry for later, a user-facing "try again shortly" message) instead of a slow timeout on every attempt.
- Tune the failure threshold and cooldown duration to the actual failure and recovery characteristics of the downstream service — a threshold too low trips the circuit on ordinary noise; a cooldown too short sends trial calls at a struggling service faster than it can possibly stabilize.
- Composing both advices on the same handler is a common and sensible pattern: let retry handle the small stuff, let the circuit breaker handle the big stuff, and route to an error channel or fallback specifically when the circuit is open, since that state itself signals "don't even bother trying right now."
