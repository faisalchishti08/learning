---
card: spring-cloud
gi: 77
slug: spring-retry-retryable-recover
title: "Spring Retry (@Retryable, @Recover)"
---

## 1. What it is

Spring Retry is an older, separate retry library (predating Resilience4j's Spring Cloud integration) offering an annotation-driven style: `@Retryable` marks a method as automatically retried on failure, and a matching `@Recover` method supplies the fallback logic, invoked once retries are exhausted — declarative retry configuration without manually wrapping call sites in retry logic.

```java
@Service
class BillingService {
    @Retryable(
        retryFor = { TransientNetworkException.class },
        maxAttempts = 3,
        backoff = @Backoff(delay = 200, multiplier = 2)
    )
    Invoice getInvoice(String id) {
        return billingClient.getInvoice(id); // retried automatically on TransientNetworkException
    }

    @Recover
    Invoice recover(TransientNetworkException e, String id) {
        return new Invoice(id, 0.0); // called once maxAttempts is exhausted
    }
}
```

## 2. Why & when

Resilience4j's `Retry` (an earlier card) is the modern, actively-developed choice and generally preferred for new work, especially in applications already using other Resilience4j patterns. Spring Retry remains relevant because it's still widely used in existing codebases, it's simpler to reach for when retry is the *only* resilience concern needed (no circuit breaker, bulkhead, or rate limiter involved), and its `@Recover` method signature matching (by exception type and parameter list) is a distinctive, genuinely convenient style some teams prefer.

Reach for Spring Retry when:

- Working in an existing codebase that already uses it — consistency with surrounding code often outweighs a marginal preference for a different library.
- Retry is the only resilience concern for a given method — no need to pull in circuit breaker or bulkhead configuration alongside it, where Spring Retry's simpler, single-purpose annotation style is a lighter-weight fit.
- The `@Recover` method's automatic parameter/exception-type matching is genuinely useful — Spring Retry can select among multiple `@Recover` methods based on which exception type was actually thrown, letting different failure modes recover differently without manual `instanceof` branching (unlike the fallback-differentiation pattern from the previous card, which required explicit type checks).

## 3. Core concept

```
 @Retryable(retryFor = {...}, maxAttempts = N, backoff = @Backoff(...))
 Invoice getInvoice(String id) { ... }

 call getInvoice("42")
    attempt 1 fails (matching exception) -> wait (backoff) -> attempt 2
    attempt 2 fails -> wait -> attempt 3
    attempt 3 fails -> maxAttempts exhausted -> look for a matching @Recover method
        @Recover method's exception parameter type must match what was thrown
        @Recover method's OTHER parameters must match the original method's parameters (by type, in order)
    matching @Recover method found -> its return value becomes the overall result
```

Spring's AOP proxy machinery intercepts the annotated method call, handles the retry loop, and dispatches to the right `@Recover` method automatically — none of this is hand-written by the calling code.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling a Retryable annotated method transparently goes through a proxy that retries on matching failures up to max attempts, then dispatches to a matching Recover method once retries are exhausted">
  <rect x="30" y="70" width="160" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="110" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billingService.getInvoice(id)</text>

  <rect x="240" y="30" width="180" height="120" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="50" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">@Retryable proxy</text>
  <text x="330" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 1 -&gt; fail -&gt; wait</text>
  <text x="330" y="93" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 2 -&gt; fail -&gt; wait</text>
  <text x="330" y="111" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 3 -&gt; still fails</text>
  <text x="330" y="135" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">maxAttempts exhausted</text>

  <rect x="460" y="70" width="150" height="40" rx="8" fill="#79c0ff30" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="535" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Recover method dispatched</text>

  <line x1="190" y1="90" x2="238" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a77)"/>
  <line x1="420" y1="90" x2="458" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a77)"/>

  <defs><marker id="a77" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The calling code just calls the method — the annotation-driven proxy handles the entire retry-then-recover lifecycle invisibly.

## 5. Runnable example

The scenario: model Spring Retry's `@Retryable`/`@Recover` mechanism for `getInvoice`. Start with the manual retry-and-recover logic it replaces, then model the annotation-driven dispatch, then add multiple `@Recover` methods matched by exception type.

### Level 1 — Basic

Manual retry-and-recover logic — what `@Retryable`/`@Recover` replaces with a declarative style.

```java
import java.util.function.Supplier;

public class SpringRetryLevel1 {
    record Invoice(String id, double amount) {}
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    static Invoice getInvoiceManually(String id, Supplier<Invoice> call, int maxAttempts) {
        RuntimeException last = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return call.get();
            } catch (TransientNetworkException e) {
                last = e;
                System.out.println("attempt " + attempt + " failed, retrying");
            }
        }
        return recover(id); // manually calling the "recovery" logic once attempts are exhausted
    }

    static Invoice recover(String id) {
        return new Invoice(id, 0.0);
    }

    public static void main(String[] args) {
        Invoice result = getInvoiceManually("42", () -> { throw new TransientNetworkException(); }, 3);
        System.out.println("result: " + result);
    }
}
```

How to run: `java SpringRetryLevel1.java`

The retry loop and the "give up, use a fallback" logic are both hand-written and interleaved with the calling code — functionally correct, but exactly the boilerplate `@Retryable`/`@Recover` exists to eliminate through declarative configuration instead.

### Level 2 — Intermediate

Model the annotation-driven dispatch: a simplified proxy that reads simulated `@Retryable`/`@Recover` metadata and handles the retry-then-recover flow automatically, without the calling code writing any retry logic itself.

```java
import java.util.function.Supplier;

public class SpringRetryLevel2 {
    record Invoice(String id, double amount) {}
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    interface RetryableOperation { Invoice call(String id); }
    interface RecoverOperation { Invoice recover(String id); }

    // simulates what Spring's AOP proxy does: wraps the retryable operation with retry-then-recover behavior
    static Invoice invokeWithRetrySupport(RetryableOperation operation, RecoverOperation recovery,
                                           String id, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.call(id);
            } catch (TransientNetworkException e) {
                System.out.println("[proxy] attempt " + attempt + " failed");
                if (attempt == maxAttempts) {
                    System.out.println("[proxy] max attempts reached -- dispatching to @Recover");
                    return recovery.recover(id);
                }
            }
        }
        throw new IllegalStateException("unreachable");
    }

    // application code just declares WHAT to do -- no retry loop written here at all
    static Invoice billingCall(String id) { throw new TransientNetworkException(); }
    static Invoice billingRecover(String id) { return new Invoice(id, 0.0); }

    public static void main(String[] args) {
        Invoice result = invokeWithRetrySupport(SpringRetryLevel2::billingCall, SpringRetryLevel2::billingRecover, "42", 3);
        System.out.println("result: " + result);
    }
}
```

How to run: `java SpringRetryLevel2.java`

`billingCall` and `billingRecover` are now just plain methods with no retry logic of their own — `invokeWithRetrySupport` (standing in for Spring's real AOP proxy generated from `@Retryable`/`@Recover` annotations) handles the entire retry-then-recover cycle around them, exactly mirroring how a real `@Retryable`-annotated Spring bean method is transparently wrapped without the method's own body containing any retry code at all.

### Level 3 — Advanced

Add multiple `@Recover`-style methods, dispatched based on which exception type was actually thrown — modeling Spring Retry's real exception-type-based `@Recover` method selection.

```java
import java.util.function.Supplier;

public class SpringRetryLevel3 {
    record Invoice(String id, double amount, String status) {}
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }
    static class InvoiceNotFoundException extends RuntimeException { InvoiceNotFoundException() { super("not found"); } }

    interface RetryableOperation { Invoice call(String id); }

    static Invoice invokeWithRetrySupport(RetryableOperation operation, String id, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return operation.call(id);
            } catch (TransientNetworkException e) {
                System.out.println("[proxy] attempt " + attempt + " failed with retryable exception");
                if (attempt == maxAttempts) return dispatchToRecover(e, id);
            } catch (InvoiceNotFoundException e) {
                // NOT in retryFor -- Spring Retry would not retry this at all, dispatches to @Recover immediately
                System.out.println("[proxy] non-retryable exception -- dispatching to @Recover immediately");
                return dispatchToRecover(e, id);
            }
        }
        throw new IllegalStateException("unreachable");
    }

    // simulates Spring's @Recover method SELECTION based on exception type -- multiple candidates, best match wins
    static Invoice dispatchToRecover(RuntimeException e, String id) {
        if (e instanceof InvoiceNotFoundException) return recoverFromNotFound((InvoiceNotFoundException) e, id);
        if (e instanceof TransientNetworkException) return recoverFromNetworkFailure((TransientNetworkException) e, id);
        throw e;
    }

    static Invoice recoverFromNotFound(InvoiceNotFoundException e, String id) {
        return new Invoice(id, 0.0, "NOT_FOUND");
    }

    static Invoice recoverFromNetworkFailure(TransientNetworkException e, String id) {
        return new Invoice(id, -1.0, "TEMPORARILY_UNAVAILABLE");
    }

    public static void main(String[] args) {
        System.out.println(invokeWithRetrySupport(id -> { throw new TransientNetworkException(); }, "42", 3));
        System.out.println(invokeWithRetrySupport(id -> { throw new InvoiceNotFoundException(); }, "999", 3));
    }
}
```

How to run: `java SpringRetryLevel3.java`

`dispatchToRecover` models Spring Retry's real behavior of selecting among multiple `@Recover` methods based on the actual exception type thrown — a `TransientNetworkException` (retried three times first, since it's the configured retryable type) ends up at `recoverFromNetworkFailure`, while an `InvoiceNotFoundException` (never retried at all, since it's not in the configured retryable set) is dispatched immediately to `recoverFromNotFound`. Two different failure modes, two different, appropriately-matched recovery methods — with the dispatch logic driven entirely by exception type, not manual `instanceof` checks scattered through calling code.

## 6. Walkthrough

Trace both calls in Level 3.

1. The first call, `invokeWithRetrySupport(id -> { throw new TransientNetworkException(); }, "42", 3)`, enters the loop. Attempt 1 throws `TransientNetworkException`, caught by the matching `catch` clause, printing the retry message; since `attempt (1) != maxAttempts (3)`, the loop continues. Attempts 2 and 3 repeat identically, and on attempt 3 (`attempt == maxAttempts`), `dispatchToRecover(e, "42")` is called instead of retrying further.
2. `dispatchToRecover` checks `e instanceof InvoiceNotFoundException` (false, it's a `TransientNetworkException`), then checks `e instanceof TransientNetworkException` (true), and calls `recoverFromNetworkFailure(e, "42")`, returning `Invoice("42", -1.0, "TEMPORARILY_UNAVAILABLE")`.
3. The second call, `invokeWithRetrySupport(id -> { throw new InvoiceNotFoundException(); }, "999", 3)`, enters the loop at attempt 1. This time the operation throws `InvoiceNotFoundException`, which matches the *second* `catch` clause (not the retryable one) — this models Spring Retry recognizing that this exception type isn't in the method's configured `retryFor` list, so it doesn't retry at all, dispatching to recovery immediately on the very first failure.
4. `dispatchToRecover(e, "999")` is called — this time `e instanceof InvoiceNotFoundException` is `true`, so `recoverFromNotFound(e, "999")` runs, returning `Invoice("999", 0.0, "NOT_FOUND")`.
5. The two printed results show genuinely different outcomes correctly matched to genuinely different failure causes: three retry attempts followed by a "temporarily unavailable" recovery for the transient network failure, versus zero retry attempts and an immediate, accurate "not found" recovery for the business-level failure.

```
TransientNetworkException:  attempt1 fail -> attempt2 fail -> attempt3 fail -> recoverFromNetworkFailure()
InvoiceNotFoundException:   NOT in retryFor -> dispatched to recover IMMEDIATELY -> recoverFromNotFound()
```

## 7. Gotchas & takeaways

> **Gotcha:** a `@Recover` method's non-exception parameters must match the original `@Retryable` method's parameters by type and order for Spring to correctly select it — a mismatched signature means Spring either can't find a matching `@Recover` method at all (the original exception propagates instead) or picks an unintended one if multiple candidates loosely match. Keep `@Recover` method signatures deliberately aligned with their corresponding `@Retryable` method.

- Spring Retry's declarative `@Retryable`/`@Recover` style removes retry-loop boilerplate from calling code, similar in spirit to Resilience4j's properties-driven configuration, but expressed through annotations directly on the protected method rather than external configuration plus a wrapping call.
- `retryFor` (or the older `value` attribute) scopes which exception types actually trigger retry — exactly like Resilience4j's `retry-exceptions`, a non-matching exception skips retry entirely and goes straight to recovery (or propagates, if no `@Recover` matches).
- Multiple `@Recover` methods can coexist on the same class, each handling a different exception type for the same `@Retryable` method — Spring selects the best match automatically, removing the need for manual `instanceof` branching inside one large recovery method.
- Choosing between Spring Retry and Resilience4j's `Retry` is largely about ecosystem fit — existing codebase conventions, whether other Resilience4j patterns are already in use, and whether the annotation-driven or properties-driven configuration style is preferred — both are legitimate, functioning choices for the retry concern specifically.
