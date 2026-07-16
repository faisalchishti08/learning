---
card: spring-amqp
gi: 16
slug: rabbittemplate-retry-recovery
title: "RabbitTemplate retry & recovery"
---

## 1. What it is

`RabbitTemplate` supports wrapping its publish operations with a `RetryTemplate` (from Spring Retry, the same library underlying Spring Integration's retry advice) via `setRetryTemplate(...)`, so a transient failure while attempting to publish — a momentary connection issue, a channel error — is retried automatically according to a configured policy, before the publish is considered truly failed. This is distinct from publisher confirms (card 0014): confirms tell you whether the broker accepted an already-successfully-sent message, while publish retry handles failures in the act of sending itself, before the message even reaches the broker successfully once.

## 2. Why & when

You configure publish-side retry when the act of publishing itself can fail transiently and recovering automatically is worth the added complexity:

- **A connection or channel-level failure occurs right as a publish is attempted** — a brief network blip or a broker temporarily unavailable during a rolling restart can cause a publish attempt to throw, and a second attempt moments later often succeeds without any application-level intervention needed.
- **Publishing happens on a critical path where losing a message to a transient failure is unacceptable** — critical business events (an order placed, a payment initiated) benefit from automatic retry at the publish level so a momentary blip doesn't silently drop the attempt.
- **A recovery strategy is needed for when retries are ultimately exhausted** — pairing retry with a `RecoveryCallback` means a publish that fails even after retrying has a defined fallback (logging, an alternate persistence path, an alert) rather than the exception simply propagating up uncaught.

## 3. Core concept

Think of publish-side retry like redialing a phone number that gave a busy signal — the busy signal (a transient connection issue) often clears within a few seconds, and simply trying again shortly after is far more practical than immediately giving up and reporting the call as permanently failed. But if the line stays busy after several redial attempts, continuing to redial indefinitely wastes time; at some point, switching to a fallback plan (leaving a voicemail via a different channel, in this analogy — the recovery callback) is the sensible move.

```java
@Bean
public RabbitTemplate rabbitTemplate(ConnectionFactory connectionFactory) {
    RabbitTemplate template = new RabbitTemplate(connectionFactory);

    RetryTemplate retryTemplate = RetryTemplate.builder()
        .maxAttempts(3)
        .fixedBackoff(500)
        .retryOn(AmqpConnectException.class)
        .build();
    template.setRetryTemplate(retryTemplate);

    template.setRecoveryCallback(context -> {
        System.out.println("Publish retries exhausted: " + context.getLastThrowable());
        return null; // or route to a fallback persistence mechanism
    });

    return template;
}
```

A transient connection exception triggers up to 3 attempts with a 500ms pause between them; if all attempts fail, the recovery callback runs instead of letting the exception propagate.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A publish attempt that fails transiently is retried automatically per the configured retry policy; if every attempt fails, the recovery callback runs instead of the exception propagating uncaught" >
  <rect x="20" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Publish attempt 1</text>

  <line x1="170" y1="42" x2="240" y2="42" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a17)"/>
  <text x="205" y="32" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">fails</text>

  <rect x="240" y="20" width="150" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="315" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Attempt 2 (backoff)</text>

  <line x1="315" y1="65" x2="150" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a17)"/>
  <text x="200" y="90" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">succeeds -&gt; done</text>

  <line x1="390" y1="42" x2="460" y2="42" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a17)"/>
  <text x="425" y="32" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">also fails</text>

  <rect x="460" y="20" width="150" height="45" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="535" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Retries exhausted</text>

  <line x1="535" y1="65" x2="400" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a17)"/>
  <text x="470" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">RecoveryCallback runs</text>
</svg>

Retry absorbs transient publish failures; the recovery callback catches what retry couldn't fix.

## 5. Runnable example

The scenario: publishing critical order events with automatic retry on transient connection failures, simulated with a plain in-memory retry loop standing in for `RetryTemplate` (no real Spring Retry dependency or RabbitMQ broker needed to demonstrate the retry-then-recover pattern), starting with a basic retry loop, then adding a recovery callback for exhausted retries, then adding backoff between attempts to model realistic transient-failure recovery timing.

### Level 1 — Basic

```java
// RabbitTemplateRetryDemo.java
public class RabbitTemplateRetryDemo {
    static int attemptCount = 0;

    static void publishOrderEvent(String payload) {
        attemptCount++;
        if (attemptCount < 2) throw new RuntimeException("transient connection issue, attempt " + attemptCount);
        System.out.println("Published successfully on attempt " + attemptCount + ": " + payload);
    }

    static void publishWithRetry(String payload, int maxAttempts) {
        for (int i = 1; i <= maxAttempts; i++) {
            try {
                publishOrderEvent(payload);
                return;
            } catch (RuntimeException ex) {
                System.out.println("Attempt " + i + " failed: " + ex.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        publishWithRetry("{\"orderId\":\"ORD-1\"}", 3);
    }
}
```

How to run: `java RabbitTemplateRetryDemo.java`. Expected output: `Attempt 1 failed: ...` then `Published successfully on attempt 2: {"orderId":"ORD-1"}` — a transient publish failure recovered automatically on the second try.

### Level 2 — Intermediate

```java
// RabbitTemplateRetryDemo.java
public class RabbitTemplateRetryDemo {
    static int attemptCount = 0;

    static void publishOrderEvent(String payload, int failUntilAttempt) {
        attemptCount++;
        if (attemptCount < failUntilAttempt) throw new RuntimeException("transient connection issue, attempt " + attemptCount);
        System.out.println("Published successfully on attempt " + attemptCount + ": " + payload);
    }

    // Real-world concern: retries can be exhausted without ever succeeding -- a recovery
    // callback defines what happens then, rather than letting the failure propagate uncaught.
    static void publishWithRetryAndRecovery(String payload, int maxAttempts, int failUntilAttempt) {
        for (int i = 1; i <= maxAttempts; i++) {
            try {
                publishOrderEvent(payload, failUntilAttempt);
                return;
            } catch (RuntimeException ex) {
                System.out.println("Attempt " + i + " failed: " + ex.getMessage());
                if (i == maxAttempts) {
                    System.out.println("Retries exhausted, running recovery callback for: " + payload);
                    // recovery: log, persist to a fallback store, alert -- whatever the app decides
                }
            }
        }
    }

    public static void main(String[] args) {
        publishWithRetryAndRecovery("{\"orderId\":\"ORD-2\"}", 3, 100); // never succeeds within budget
    }
}
```

How to run: `java RabbitTemplateRetryDemo.java`. Expected output: three "Attempt N failed" lines followed by `Retries exhausted, running recovery callback for: {"orderId":"ORD-2"}` — the message never actually gets published within the retry budget, but the failure is handled deliberately by the recovery callback rather than crashing whatever code initiated the publish.

### Level 3 — Advanced

```java
// RabbitTemplateRetryDemo.java
public class RabbitTemplateRetryDemo {
    static int attemptCount = 0;

    static void publishOrderEvent(String payload, int failUntilAttempt) {
        attemptCount++;
        if (attemptCount < failUntilAttempt) throw new RuntimeException("transient connection issue, attempt " + attemptCount);
        System.out.println("Published successfully on attempt " + attemptCount + ": " + payload);
    }

    // Production concern: retrying instantly, back to back, against a struggling broker can
    // make things worse -- a backoff delay between attempts gives the broker (or network) time
    // to actually recover before the next attempt, rather than hammering it continuously.
    static void publishWithBackoffRetry(String payload, int maxAttempts, int failUntilAttempt, long backoffMillis)
            throws InterruptedException {
        for (int i = 1; i <= maxAttempts; i++) {
            try {
                publishOrderEvent(payload, failUntilAttempt);
                return;
            } catch (RuntimeException ex) {
                System.out.println("Attempt " + i + " failed: " + ex.getMessage());
                if (i == maxAttempts) {
                    System.out.println("Retries exhausted, running recovery callback for: " + payload);
                    return;
                }
                System.out.println("Backing off for " + backoffMillis + "ms before next attempt");
                Thread.sleep(backoffMillis);
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        publishWithBackoffRetry("{\"orderId\":\"ORD-3\"}", 3, 3, 200);
        System.out.println("Total elapsed: ~" + (System.currentTimeMillis() - start) + "ms");
    }
}
```

How to run: `java RabbitTemplateRetryDemo.java`. Expected output: two failed-attempt lines each followed by a "Backing off for 200ms" message, then `Published successfully on attempt 3: {"orderId":"ORD-3"}`, and a total elapsed time reflecting the roughly 400ms of accumulated backoff delay — demonstrating the deliberate pacing between attempts that keeps automatic retry from hammering a struggling connection continuously.

## 6. Walkthrough

Trace a publish operation through retry, backoff, and eventual recovery.

1. **Initial publish attempt**: application code calls `convertAndSend(...)` on a `RabbitTemplate` configured with a `RetryTemplate`; internally, the retry template wraps the actual publish operation.
2. **Transient failure**: the underlying publish throws an exception matching the retry policy's configured retryable exception types (a connection-related exception, typically) — this happens before any publisher confirm would even be relevant, since the message never successfully reached the broker at all on this attempt.
3. **Backoff and retry**: per the configured backoff policy, the retry template waits (fixed or exponentially increasing delay) before attempting the publish again — giving whatever caused the transient failure (a brief network blip, a broker restart) time to resolve.
4. **Success on a later attempt**: if a subsequent attempt succeeds, the retry template returns normally, and from the calling code's perspective, `convertAndSend` simply succeeded — the retries that happened underneath are invisible to the caller except for the added latency.
5. **Exhaustion and recovery**: if every configured attempt fails, the retry template's `RecoveryCallback` runs instead of letting the final exception propagate — this is where the application defines what "truly failed to publish, even after retrying" actually means for this particular publish operation: log it, persist to a fallback store for later reprocessing, or alert an operator.
6. **Downstream unaffected either way**: whether the message ultimately got published on the first attempt or only after several retries, everything downstream (the broker's routing, delivery to consumers) proceeds identically — the retry mechanism is entirely about the reliability of the act of publishing itself, not anything that happens after a successful publish.

```
convertAndSend(...) wrapped by RetryTemplate
  attempt 1 -> transient failure -> backoff
    attempt 2 -> transient failure -> backoff
      attempt 3 -> succeeds -> return normally (retries invisible to caller)
                -> OR also fails -> RecoveryCallback runs (log/fallback/alert)
```

## 7. Gotchas & takeaways

> **Gotcha:** publish-side retry is entirely separate from publisher confirms (card 0014) — retry handles failures in the act of sending (before the broker has accepted anything), while confirms tell you whether an already-successfully-sent message was actually accepted; conflating the two, or assuming retry alone provides delivery assurance, misses that a "successfully sent" (no exception, no retry needed) message can still be NACKed or unroutable at the confirm/return level afterward.

- Configure retry specifically for transient, likely-to-resolve-quickly failure types (connection issues) — retrying a failure caused by a genuine, permanent misconfiguration (an authentication failure, a malformed exchange name) just wastes time reproducing the same guaranteed failure repeatedly.
- Always pair retry with a defined recovery strategy — retry with no recovery callback and retries eventually exhausted simply lets the original exception propagate, which may or may not be handled sensibly by whatever code called the publish in the first place.
- Backoff between attempts (rather than retrying instantly, back to back) is important specifically because instant retries against a struggling connection or broker can compound the underlying problem rather than giving it room to recover.
- Retry, confirms, and returns are three distinct but complementary reliability mechanisms in Spring AMQP's publishing story — retry handles send-time failures, confirms verify broker acceptance, and returns catch unroutable messages; a genuinely reliable critical-path publish operation often uses all three together.
