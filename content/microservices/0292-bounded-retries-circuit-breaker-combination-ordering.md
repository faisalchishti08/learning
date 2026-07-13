---
card: microservices
gi: 292
slug: bounded-retries-circuit-breaker-combination-ordering
title: "Bounded retries + circuit breaker combination ordering"
---

## 1. What it is

When both a [retry](0259-retry-pattern.md) mechanism and a [circuit breaker](0250-circuit-breaker-pattern.md) wrap the same call, the *order* in which they're layered changes their behavior substantially. Wrapping retry around the circuit breaker (retry is the outer layer, circuit breaker is inner) means each individual retry attempt passes through the circuit breaker's own logic and can itself trip or be blocked by it. Wrapping circuit breaker around retry (circuit breaker outer, retry inner) means the circuit breaker only sees the *final* outcome after all retries are exhausted, treating a "succeeded on the 3rd retry" the same as a first-attempt success.

## 2. Why & when

Resilience4j's own recommended and default ordering is retry as the outer layer, circuit breaker as the inner layer — meaning each retry attempt is itself subject to the circuit breaker. This matters because if the circuit breaker is inside, once it trips open, *further retry attempts immediately fail fast* against the open circuit instead of continuing to hammer an already-struggling dependency with retries. This is the composition that actually protects the failing dependency: retries stop dead the moment the circuit breaker (which is watching the aggregate failure rate across *all* callers, not just this one call site) opens.

Wrapping it the other way — circuit breaker outside, retry inside — is usually a mistake: a single logical call retries fully (e.g., 3 attempts with backoff) before the circuit breaker ever sees a single failure, since the circuit breaker only observes the retry group's final result. This means the circuit breaker's failure-rate calculation is based on a much smaller, delayed signal (whole retry-groups succeeding or failing) rather than individual call attempts, making it slower to detect and react to a struggling dependency, and it does nothing to stop each individual caller from still fully retrying against an already-known-bad dependency.

## 3. Core concept

Resilience4j's decorator composition order determines which one sees which events; the recommended order applies retry outermost so each attempt is individually gated by the circuit breaker.

```java
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.retry.Retry;
import io.vavr.control.Try;
import java.util.function.Supplier;

CircuitBreaker circuitBreaker = CircuitBreaker.ofDefaults("payments");
Retry retry = Retry.ofDefaults("payments");

Supplier<String> callDependency = () -> paymentClient.charge(request);

// CORRECT order: Retry.decorateSupplier WRAPS the circuit-breaker-decorated supplier.
// Each retry attempt individually passes through (and can be blocked by) the circuit breaker.
Supplier<String> decorated = Retry.decorateSupplier(retry,
        CircuitBreaker.decorateSupplier(circuitBreaker, callDependency));

String result = Try.ofSupplier(decorated).recover(t -> "fallback").get();
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Retry as the outer layer wraps circuit breaker as the inner layer; each individual retry attempt passes through the circuit breaker, so once the circuit breaker opens, subsequent retry attempts fail fast instead of continuing to call the struggling dependency">
  <rect x="30" y="20" width="560" height="140" rx="8" fill="none" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="40" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">RETRY (outer) -- attempt 1, 2, 3...</text>

  <rect x="60" y="55" width="520" height="90" rx="8" fill="none" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">CIRCUIT BREAKER (inner) -- gates EVERY attempt</text>

  <rect x="90" y="90" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="165" y="112" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 1: real call, fails</text>

  <rect x="260" y="90" width="150" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="335" y="112" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">attempt 2: real call, fails</text>

  <rect x="430" y="90" width="150" height="35" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="505" y="106" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">attempt 3: circuit</text>
  <text x="505" y="118" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">now OPEN, fails FAST</text>
</svg>

Retry wraps circuit breaker: later retry attempts get short-circuited fast once the breaker trips, sparing the dependency.

## 5. Runnable example

Scenario: circuit breaker wrapped around retry (the less effective order), showing the dependency still receives every retried call even after enough failures to justify tripping, extended to the recommended order — retry wrapped around circuit breaker — showing later retries short-circuit immediately once the breaker opens, and finally a full production-shaped composition adding a fallback so the caller still gets a usable result either way.

### Level 1 — Basic

```java
// File: CircuitBreakerOutsideRetry.java -- circuit breaker wraps retry:
// the breaker only sees the FINAL outcome of a whole retry group, so it
// reacts slowly, and every individual retry attempt still fully hits
// the struggling dependency.
public class CircuitBreakerOutsideRetry {
    enum State { CLOSED, OPEN }
    static State circuitState = State.CLOSED;
    static int consecutiveGroupFailures = 0;
    static int dependencyCallCount = 0;

    static String callDependency() {
        dependencyCallCount++;
        throw new RuntimeException("dependency down");
    }

    static String withRetry() {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try { return callDependency(); }
            catch (Exception e) { if (attempt == 3) throw e; }
        }
        throw new IllegalStateException("unreachable");
    }

    static String withCircuitBreakerOutside() {
        if (circuitState == State.OPEN) throw new RuntimeException("circuit OPEN");
        try {
            return withRetry(); // retry group runs COMPLETELY before the breaker sees anything
        } catch (Exception e) {
            consecutiveGroupFailures++;
            if (consecutiveGroupFailures >= 2) circuitState = State.OPEN;
            throw e;
        }
    }

    public static void main(String[] args) {
        for (int call = 1; call <= 3; call++) {
            try { withCircuitBreakerOutside(); }
            catch (Exception e) { System.out.println("Logical call " + call + " failed after its retries."); }
        }
        System.out.println("Total REAL dependency calls made: " + dependencyCallCount
                + " (every retry within every logical call hit the dependency, breaker reacted only AFTER whole groups failed)");
    }
}
```

How to run: `java CircuitBreakerOutsideRetry.java`

Each "logical call" retries 3 times internally before the circuit breaker (wrapping the whole retry group) ever records a failure. Three logical calls each retry 3 times, so `dependencyCallCount` reaches 9 — every single retry attempt across all three logical calls hit the real (failing) dependency, even though after the second logical call's total failure, the circuit breaker did open. The third logical call's *first* attempt is blocked by the now-open circuit, but its would-be retries never even get the chance to be gated individually — because retry doesn't wrap the breaker, once inside a `withRetry()` call the breaker isn't consulted again until that whole group finishes.

### Level 2 — Intermediate

```java
// File: RetryOutsideCircuitBreaker.java -- the RECOMMENDED order: retry
// wraps circuit breaker, so EACH individual retry attempt is gated by
// the breaker. Once the breaker opens mid-retry-sequence, later attempts
// within the SAME logical call fail fast instead of hitting the dependency.
public class RetryOutsideCircuitBreaker {
    enum State { CLOSED, OPEN }
    static State circuitState = State.CLOSED;
    static int consecutiveFailures = 0;
    static int dependencyCallCount = 0;

    static String callDependency() {
        dependencyCallCount++;
        throw new RuntimeException("dependency down");
    }

    static String callThroughCircuitBreaker() {
        if (circuitState == State.OPEN) throw new RuntimeException("circuit OPEN, not calling dependency");
        try {
            String result = callDependency();
            consecutiveFailures = 0;
            return result;
        } catch (Exception e) {
            consecutiveFailures++;
            if (consecutiveFailures >= 2) circuitState = State.OPEN; // trips after just 2 REAL failures
            throw e;
        }
    }

    static String withRetryOutside() {
        for (int attempt = 1; attempt <= 3; attempt++) {
            try { return callThroughCircuitBreaker(); } // EACH attempt individually gated by the breaker
            catch (Exception e) { if (attempt == 3) throw e; }
        }
        throw new IllegalStateException("unreachable");
    }

    public static void main(String[] args) {
        for (int call = 1; call <= 3; call++) {
            try { withRetryOutside(); }
            catch (Exception e) { System.out.println("Logical call " + call + " failed after its retries."); }
        }
        System.out.println("Total REAL dependency calls made: " + dependencyCallCount
                + " (far fewer -- the breaker started short-circuiting retries as soon as it opened, mid-sequence)");
    }
}
```

How to run: `java RetryOutsideCircuitBreaker.java`

With retry as the outer layer, the very first logical call's attempts 1 and 2 hit the real dependency and fail, tripping the breaker open after just 2 real failures. Attempt 3 of that *same* logical call already gets short-circuited by the now-open breaker instead of hitting the dependency a third time. Logical calls 2 and 3 never reach the dependency at all — every attempt within them is immediately blocked by the open circuit. The total dependency call count comes out to just 2 (versus 9 in Level 1) for the identical three logical calls, because each retry attempt was individually protected by the breaker rather than the breaker only reacting after whole retry groups completed.

### Level 3 — Advanced

```java
// File: FullCompositionWithFallback.java -- the complete, realistic
// production shape: retry (outer) wraps circuit breaker (inner), and the
// whole thing is wrapped in a fallback so the caller always gets a
// usable result regardless of which layer ultimately gave up.
import io.github.resilience4j.circuitbreaker.CircuitBreaker;
import io.github.resilience4j.circuitbreaker.CircuitBreakerConfig;
import io.github.resilience4j.retry.Retry;
import io.github.resilience4j.retry.RetryConfig;
import io.vavr.control.Try;
import java.time.Duration;
import java.util.function.Supplier;

public class FullCompositionWithFallback {
    static int dependencyCallCount = 0;

    static String callDependency() {
        dependencyCallCount++;
        throw new RuntimeException("dependency down");
    }

    public static void main(String[] args) {
        CircuitBreakerConfig cbConfig = CircuitBreakerConfig.custom()
                .failureRateThreshold(50)
                .minimumNumberOfCalls(2)
                .slidingWindowSize(2)
                .waitDurationInOpenState(Duration.ofSeconds(10))
                .build();
        CircuitBreaker circuitBreaker = CircuitBreaker.of("payments", cbConfig);

        RetryConfig retryConfig = RetryConfig.custom().maxAttempts(3).waitDuration(Duration.ofMillis(10)).build();
        Retry retry = Retry.of("payments", retryConfig);

        Supplier<String> decorated = Retry.decorateSupplier(retry, // RETRY OUTER
                CircuitBreaker.decorateSupplier(circuitBreaker, FullCompositionWithFallback::callDependency)); // CIRCUIT BREAKER INNER

        for (int call = 1; call <= 3; call++) {
            String result = Try.ofSupplier(decorated)
                    .recover(t -> "FALLBACK: showing cached/default result")
                    .get();
            System.out.println("Logical call " + call + " -> " + result);
        }
        System.out.println("Total REAL dependency calls made: " + dependencyCallCount);
    }
}
```

How to run: `java -cp .:resilience4j-retry-2.2.0.jar:resilience4j-circuitbreaker-2.2.0.jar:resilience4j-core-2.2.0.jar:vavr-0.10.4.jar FullCompositionWithFallback.java` (with the Resilience4j and Vavr jars on the classpath; typically pulled in transitively via `spring-cloud-starter-circuitbreaker-resilience4j` in a Spring Boot project).

This wires the actual Resilience4j library with the recommended composition order — `Retry.decorateSupplier` wrapping a `CircuitBreaker.decorateSupplier`-wrapped call — and adds a `Try...recover` fallback around the whole thing. Every attempt, whether it's an initial call or a retry, passes through the circuit breaker, so the breaker opens quickly (after just 2 calls per the configured `slidingWindowSize`) and subsequent attempts across all three logical calls fail fast. Regardless of whether a given logical call succeeds, exhausts retries, or gets short-circuited by an open breaker, `recover` catches whatever exception surfaces and returns a usable fallback string — the caller of `main`'s loop never sees a raw exception, only a graceful degraded result, demonstrating the full production-shaped stack of resilience patterns working together.

## 6. Walkthrough

Trace `RetryOutsideCircuitBreaker.main`'s first logical call (`call=1`) in order. **First**, `withRetryOutside()` begins its loop at `attempt=1` and calls `callThroughCircuitBreaker()`.

**Inside**, `circuitState` is still `CLOSED`, so the guard passes; `callDependency()` is invoked, incrementing `dependencyCallCount` to 1 and throwing. The `catch` block increments `consecutiveFailures` to 1, which is `< 2` (the threshold), so the circuit stays `CLOSED`, and the exception is re-thrown up to `withRetryOutside`.

**Back in `withRetryOutside`**, `attempt=1`'s failure is caught; since `attempt != 3`, the loop continues to `attempt=2`, calling `callThroughCircuitBreaker()` again. The circuit is still `CLOSED`, so `callDependency()` runs again — `dependencyCallCount` reaches 2, `consecutiveFailures` reaches 2, which now meets the threshold, so `circuitState` flips to `OPEN`. The exception still propagates back to `withRetryOutside` as a normal retry-attempt failure.

**`attempt=3`** now calls `callThroughCircuitBreaker()` a third time — but this time, the very first line, `if (circuitState == State.OPEN)`, is true, so the method throws immediately without ever calling `callDependency()`. `dependencyCallCount` stays at 2. Since `attempt == 3`, this final failure is re-thrown out of `withRetryOutside`, and `main`'s `catch` block prints "Logical call 1 failed after its retries."

**For logical call 2**, `withRetryOutside` again starts at `attempt=1`, calling `callThroughCircuitBreaker()` — but `circuitState` is *still* `OPEN` from the previous logical call (state persists across calls, as a real circuit breaker's does), so all three of this call's attempts are immediately short-circuited without ever touching `dependencyCallCount`. The same happens for logical call 3.

**Final state**: `dependencyCallCount` is 2 total across all three logical calls (9 attempts), because the breaker — being consulted on *every individual attempt*, not just once per logical call — stopped nearly all of them from ever reaching the failing dependency.

```
call 1: attempt1(real,fail,count=1) -> attempt2(real,fail,count=2,BREAKER OPENS) -> attempt3(short-circuited)
call 2: attempt1(short-circuited) -> attempt2(short-circuited) -> attempt3(short-circuited)
call 3: attempt1(short-circuited) -> attempt2(short-circuited) -> attempt3(short-circuited)
                                    total real dependency calls: 2
```

## 7. Gotchas & takeaways

> Wrapping a circuit breaker *outside* a retry loop means the breaker only ever observes whole-retry-group outcomes, reacting far more slowly and doing nothing to stop individual retry attempts within an already-doomed call from still hammering a struggling dependency.

- The recommended composition is retry as the outer decorator and circuit breaker as the inner one, so every individual attempt — original call and every retry — is gated by the breaker.
- This ordering makes the breaker's failure-rate calculation far more responsive, since it's based on individual call attempts rather than delayed whole-group outcomes.
- Always add a fallback around the entire composed stack (as in Level 3) so the caller receives a usable result regardless of which specific layer — retry exhaustion or an open circuit — ultimately caused the failure.
- When composing multiple resilience decorators, always verify the actual order empirically (as this topic's runnable example does) rather than assuming — decorator composition order is easy to get backward, and the resulting behavior difference is significant but not obviously reflected by superficially similar-looking code.
