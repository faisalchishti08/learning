---
card: microservices
gi: 298
slug: spring-retry-retryable-recover-retrytemplate
title: "Spring Retry (@Retryable, @Recover, RetryTemplate)"
---

## 1. What it is

Spring Retry is Spring's own, older retry library — predating Resilience4j's popularity in the Spring ecosystem — offering both an annotation-driven style (`@Retryable` on a method, `@Recover` for the method to call once retries are exhausted) and a programmatic style (`RetryTemplate`, used for retry logic that isn't tied to a Spring-managed bean method or that needs to be built dynamically). It remains widely used, particularly in Spring Batch and Spring Integration internals, and is a perfectly valid choice for straightforward retry-only needs in application code.

## 2. Why & when

`@Retryable` is the simplest way to add retry behavior to a Spring bean method — a single annotation, similar in spirit to Resilience4j's `@Retry` but with its own configuration attributes and its own `@Recover` mechanism for defining a fallback specifically for after-retries-are-exhausted, rather than for every possible failure the way a general fallback might. `RetryTemplate` covers the cases `@Retryable` can't: retrying logic inside a method that isn't a proxied Spring bean call, or retry behavior that needs to be constructed with parameters only known at runtime.

Choosing between Spring Retry and Resilience4j's retry module for new code is largely a matter of ecosystem fit: if a project is already using Resilience4j for circuit breaking, bulkheads, and rate limiting, using its `@Retry` module too keeps everything under one consistent API and one configuration model (`application.yml`). If only retry is needed, or the project already depends on Spring Batch/Integration (which use Spring Retry internally), Spring Retry is a lighter, equally capable choice. Use `@Retryable`/`@Recover` for simple, static, annotation-declared retry needs on Spring bean methods; use `RetryTemplate` for retry logic needed outside that context.

## 3. Core concept

`@Retryable` specifies which exceptions to retry on, how many attempts, and the backoff policy; `@Recover` methods (matched by return type and a leading exception parameter) run once all attempts are exhausted.

```java
import org.springframework.retry.annotation.Backoff;
import org.springframework.retry.annotation.Retryable;
import org.springframework.retry.annotation.Recover;
import org.springframework.stereotype.Service;

@Service
class InventoryService {
    @Retryable(retryFor = TransientDataAccessException.class,
               maxAttempts = 3,
               backoff = @Backoff(delay = 200, multiplier = 2))
    String checkStock(String sku) {
        return inventoryClient.checkStock(sku); // may throw TransientDataAccessException
    }

    @Recover // signature: matching return type, leading param = the exception type retried on
    String recover(TransientDataAccessException e, String sku) {
        return "UNKNOWN (exhausted retries for " + sku + ")";
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An @Retryable method is called through a Spring AOP proxy that retries the underlying call according to the configured attempts and backoff; once every attempt is exhausted, the proxy dispatches to the matching @Recover method instead of propagating the final exception">
  <rect x="20" y="50" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="74" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">caller</text>

  <line x1="140" y1="70" x2="220" y2="70" stroke="#8b949e" marker-end="url(#arr298)"/>
  <rect x="230" y="30" width="200" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="50" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Retryable proxy</text>
  <text x="330" y="65" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">attempt 1, 2, 3...</text>
  <text x="330" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exponential backoff</text>
  <text x="330" y="95" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">between attempts</text>

  <line x1="430" y1="70" x2="510" y2="70" stroke="#8b949e" marker-end="url(#arr298)"/>
  <text x="470" y="60" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">exhausted</text>
  <rect x="520" y="50" width="100" height="40" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="570" y="74" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Recover</text>

  <defs><marker id="arr298" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The proxy retries with backoff on the configured exception type; exhaustion routes to the matching @Recover method.

## 5. Runnable example

Scenario: a plain method with manually written retry logic mixed into the business code, extended to simulate the `@Retryable` + `@Recover` annotation-driven proxy behavior Spring generates, and finally using the actual programmatic `RetryTemplate` API (which requires no Spring context and runs directly) for a case where the retry logic can't be a simple annotated bean method — retrying a block of code with a runtime-determined policy.

### Level 1 — Basic

```java
// File: ManualRetryMixedIntoLogic.java -- retry logic is hand-written
// directly inside the business method, mixing the resilience concern
// with the actual work being done.
public class ManualRetryMixedIntoLogic {
    static int callCount = 0;
    static String checkStockRaw(String sku) {
        callCount++;
        if (callCount < 3) throw new RuntimeException("transient inventory error");
        return "IN_STOCK";
    }

    static String checkStock(String sku) {
        int maxAttempts = 3;
        long delay = 200;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return checkStockRaw(sku); // business call, TANGLED with retry bookkeeping below
            } catch (Exception e) {
                if (attempt == maxAttempts) return "UNKNOWN (exhausted retries)"; // recovery ALSO tangled in here
                try { Thread.sleep(delay); } catch (InterruptedException ignored) {}
                delay *= 2;
            }
        }
        throw new IllegalStateException("unreachable");
    }

    public static void main(String[] args) {
        System.out.println(checkStock("sku-123"));
        System.out.println("Calls made: " + callCount);
    }
}
```

How to run: `java ManualRetryMixedIntoLogic.java`

`checkStock` mixes retry attempt counting, backoff delay computation, and recovery logic directly inline with the business call — the method is doing two jobs at once, which is exactly what `@Retryable`/`@Recover` exist to separate.

### Level 2 — Intermediate

```java
// File: SimulatedRetryableAndRecover.java -- simulates what Spring AOP
// generates for @Retryable(maxAttempts=3, backoff=@Backoff(delay=200,
// multiplier=2)) plus a matching @Recover method: the business method
// body is now PLAIN, with the retry/recovery composed around it by a proxy.
public class SimulatedRetryableAndRecover {
    static int callCount = 0;

    // The PLAIN business-logic method, as the developer writes it --
    // in real Spring code, @Retryable would be the only thing added here.
    static String checkStock(String sku) {
        callCount++;
        if (callCount < 3) throw new RuntimeException("transient inventory error");
        return "IN_STOCK";
    }

    // The @Recover method -- also plain, matched by Spring at runtime
    // based on its parameter/return types.
    static String recover(Exception e, String sku) {
        return "UNKNOWN (exhausted retries for " + sku + ": " + e.getMessage() + ")";
    }

    // Simulates the AOP proxy Spring generates from @Retryable + @Recover.
    static String retryableProxy(String sku) throws InterruptedException {
        int maxAttempts = 3; long delay = 200;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                return checkStock(sku); // delegates to the PLAIN method
            } catch (Exception e) {
                if (attempt == maxAttempts) return recover(e, sku); // dispatches to @Recover
                Thread.sleep(delay);
                delay *= 2; // multiplier=2
            }
        }
        throw new IllegalStateException("unreachable");
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println(retryableProxy("sku-123"));
        System.out.println("Calls made: " + callCount);
    }
}
```

How to run: `java SimulatedRetryableAndRecover.java`

`checkStock` and `recover` are both plain methods with no retry logic of their own — everything about attempt counting, backoff, and dispatching to recovery lives in `retryableProxy`, standing in for the AOP proxy Spring generates automatically from the `@Retryable`/`@Recover` annotations. Since the underlying call succeeds on its 3rd attempt (before recovery would even be needed), the method returns `"IN_STOCK"` directly — but if it kept failing past `maxAttempts`, the proxy would dispatch to `recover` instead, exactly as shown in Level 3's compositional walkthrough.

### Level 3 — Advanced

```java
// File: RetryTemplateProgrammatic.java -- the REAL Spring Retry
// org.springframework.retry.support.RetryTemplate API, used
// programmatically for a case @Retryable can't cover directly: the
// retry policy (max attempts) is determined at RUNTIME (e.g., from a
// per-tenant configuration value), not fixed at compile time by an
// annotation. (Requires spring-retry on the classpath.)
import org.springframework.retry.RetryCallback;
import org.springframework.retry.RecoveryCallback;
import org.springframework.retry.backoff.ExponentialBackOffPolicy;
import org.springframework.retry.policy.SimpleRetryPolicy;
import org.springframework.retry.support.RetryTemplate;

public class RetryTemplateProgrammatic {
    static int callCount = 0;
    static String checkStockRaw(String sku) {
        callCount++;
        if (callCount < 3) throw new RuntimeException("transient inventory error");
        return "IN_STOCK";
    }

    static String checkStockWithDynamicRetry(String sku, int maxAttemptsForThisTenant) {
        RetryTemplate retryTemplate = new RetryTemplate();

        SimpleRetryPolicy retryPolicy = new SimpleRetryPolicy();
        retryPolicy.setMaxAttempts(maxAttemptsForThisTenant); // RUNTIME-determined, not a compile-time annotation attribute
        retryTemplate.setRetryPolicy(retryPolicy);

        ExponentialBackOffPolicy backOffPolicy = new ExponentialBackOffPolicy();
        backOffPolicy.setInitialInterval(200);
        backOffPolicy.setMultiplier(2.0);
        retryTemplate.setBackOffPolicy(backOffPolicy);

        RetryCallback<String, RuntimeException> retryCallback = context -> checkStockRaw(sku);
        RecoveryCallback<String> recoveryCallback = context -> "UNKNOWN (exhausted " + maxAttemptsForThisTenant + " retries for " + sku + ")";

        return retryTemplate.execute(retryCallback, recoveryCallback);
    }

    public static void main(String[] args) {
        // Tenant A's SLA allows generous retries; tenant B's does not -- the
        // SAME code path, but the retry policy differs based on runtime data.
        callCount = 0;
        System.out.println("Tenant A (maxAttempts=5): " + checkStockWithDynamicRetry("sku-123", 5));
        System.out.println("  calls made: " + callCount);

        callCount = 0;
        System.out.println("Tenant B (maxAttempts=2): " + checkStockWithDynamicRetry("sku-123", 2));
        System.out.println("  calls made: " + callCount);
    }
}
```

How to run: `java -cp .:spring-retry-2.0.5.jar:spring-core-6.1.jar RetryTemplateProgrammatic.java` (with Spring Retry and Spring Core jars on the classpath; typically pulled in via the `spring-retry` dependency in a Spring Boot project alongside `spring-boot-starter-aop`).

The same underlying call (`checkStockRaw`, which needs exactly 3 attempts to succeed) is retried with two different, runtime-determined policies. Tenant A's policy allows up to 5 attempts, more than enough to reach the 3rd, successful attempt — `checkStockWithDynamicRetry` returns `"IN_STOCK"`. Tenant B's policy allows only 2 attempts, which is exhausted *before* reaching the 3rd, successful attempt — `retryTemplate.execute` invokes the `recoveryCallback` instead, returning the "exhausted retries" message. This is precisely the scenario `@Retryable`'s static, annotation-declared `maxAttempts` cannot express: the policy itself is built from data only available at runtime (here, a method parameter standing in for a per-tenant configuration lookup).

## 6. Walkthrough

Trace `RetryTemplateProgrammatic.main`'s call for Tenant B (`maxAttemptsForThisTenant=2`). **First**, `checkStockWithDynamicRetry("sku-123", 2)` builds a fresh `RetryTemplate`, configures a `SimpleRetryPolicy` with `maxAttempts=2`, and an `ExponentialBackOffPolicy` starting at 200ms with a 2x multiplier.

**`retryTemplate.execute(retryCallback, recoveryCallback)` is called.** Internally, `RetryTemplate` invokes `retryCallback.doWithRetry(context)` for attempt 1, which calls `checkStockRaw(sku)`. Since `callCount` was reset to 0 for this tenant's run, this is the method's 1st global call in this run; `callCount` becomes 1, and since `1 < 3`, it throws.

**`RetryTemplate` catches this exception internally**, consults the `SimpleRetryPolicy` to check whether another attempt is permitted — `maxAttempts=2` and only 1 attempt has been made, so retry is permitted. It waits according to the `ExponentialBackOffPolicy` (200ms for this first backoff), then invokes `retryCallback` again for attempt 2. `checkStockRaw` runs again, `callCount` becomes 2, and since `2 < 3`, it throws again.

**`RetryTemplate` consults the policy again**: 2 attempts have now been made, matching `maxAttempts=2` exactly — no further retry is permitted. Instead of attempting a 3rd time (which, notably, would have succeeded, since `checkStockRaw` requires `callCount >= 3`), `RetryTemplate` invokes `recoveryCallback.recover(context)`, which returns the "exhausted 2 retries" message. This becomes `execute`'s return value.

**Back in `main`**, this is printed, followed by `callCount`, which reads 2 — confirming exactly 2 real attempts were made before recovery kicked in, one short of what would have succeeded.

**Contrast with Tenant A's run** (traced identically but with `maxAttempts=5`): attempts 1 and 2 fail the same way, but since `2 < 5`, the policy permits a 3rd attempt; that 3rd call to `checkStockRaw` has `callCount` reach 3, satisfying `callCount >= 3`, so it succeeds and returns `"IN_STOCK"` directly — `recoveryCallback` is never invoked at all for this tenant.

```
Tenant A (maxAttempts=5): attempt1(fail) -> backoff200ms -> attempt2(fail) -> backoff400ms -> attempt3(SUCCESS) -> "IN_STOCK"
Tenant B (maxAttempts=2): attempt1(fail) -> backoff200ms -> attempt2(fail) -> policy EXHAUSTED -> recoveryCallback -> "UNKNOWN (exhausted...)"
```

## 7. Gotchas & takeaways

> A `@Recover` method's parameter list must start with the exact exception type declared (or a supertype of it) in the corresponding `@Retryable`'s `retryFor` attribute, followed by parameters matching the original method's signature in order — a mismatch means Spring silently fails to find a matching recovery method and the original exception propagates instead, often surprising developers who assumed their `@Recover` method would be used.

- `@Retryable`/`@Recover` are the right choice for static, per-method retry policies on Spring-managed beans; `RetryTemplate` is the right choice when the policy must be constructed dynamically or the retried code isn't a simple bean method call.
- Like Resilience4j's `@Retry`, `@Retryable` relies on a Spring AOP proxy — self-invocation (calling an `@Retryable` method from within the same class) bypasses the proxy and the retry behavior entirely.
- `RetryTemplate` requires no Spring context or bean proxying at all — it's a plain Java object that can be constructed and used anywhere, including outside Spring-managed code, which is why it's used directly (not via annotations) in this topic's examples.
- Spring Batch and Spring Integration use Spring Retry internally for their own built-in retry support, so a project already depending on either of those brings Spring Retry along transitively, often making it the path of least resistance even in a project otherwise using Resilience4j for other resilience patterns.
