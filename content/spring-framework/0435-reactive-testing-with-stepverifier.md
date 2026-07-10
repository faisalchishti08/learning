---
card: spring-framework
gi: 435
slug: reactive-testing-with-stepverifier
title: "Reactive testing with StepVerifier"
---

## 1. What it is

`StepVerifier` (from Project Reactor's `reactor-test` module, not Spring itself, but the standard companion for testing any `Mono`/`Flux`-returning Spring code) is a fluent assertion API for verifying exactly what a reactive stream emits, in what order, over what timing — including errors, completion, and, critically, virtual time control for testing time-based operators (delays, timeouts, intervals) without a real test actually waiting for real wall-clock time to pass.

```java
StepVerifier.create(productService.findDiscounted())
        .expectNext(new Product(1, "Laptop", 899.99))
        .expectNext(new Product(2, "Mouse", 19.99))
        .verifyComplete();
```

## 2. Why & when

A `Mono`/`Flux` is a *description* of an asynchronous computation, not a value — asserting on it with plain JUnit assertions means either blocking (defeating the point of testing reactive code, and unable to express multi-item or timing-sensitive behavior) or writing manual subscriber/callback boilerplate for every test. `StepVerifier` exists to make testing a reactive stream's exact behavior — every emitted item, in order, plus how it terminates (completion, error, or never) — as natural as testing a synchronous return value, while also solving the harder problem of testing operators that depend on time passing (`delayElement`, `timeout`, `Flux.interval`) via virtual time, so a test verifying a 10-second delay doesn't actually take 10 real seconds to run.

Reach for `StepVerifier` when:

- Testing any service method or component that returns `Mono`/`Flux`, to verify its exact emission sequence, not just "did it eventually produce something."
- Verifying error-handling behavior in a reactive pipeline — that a specific error type propagates, or that a fallback correctly recovers from one.
- Testing time-dependent reactive operators (retries with backoff, timeouts, scheduled emissions) using `StepVerifier.withVirtualTime(...)`, without a slow, real-time-dependent test suite.

## 3. Core concept

```
 StepVerifier.create(publisher)
        |
        v
   .expectNext(item1)          <- assert the next emitted item equals this
   .expectNext(item2)
   .expectNextCount(n)          <- assert n more items arrive, without checking each one
   .expectError(SomeException.class)   <- assert the stream terminates with this error type
   .expectComplete()             <- assert the stream terminates normally (no error)
        |
        v
   .verify()  /  .verifyComplete()  /  .verifyError(...)
        |
        | SUBSCRIBES to the publisher NOW, and blocks the test thread
        | until the expected sequence of events has been observed
        | (or a default timeout elapses, failing the test)
        v
   pass or fail, with a precise description of what diverged from expectations
```

Nothing in the chain before `.verify()`/its variants actually subscribes — exactly like building a `Mono`/`Flux` pipeline itself, the verification steps are assembled lazily and only executed when the terminal `verify*()` call runs.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="StepVerifier subscribes to a publisher and checks each emitted signal against expectations in order">
  <rect x="10" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Flux/Mono</text>

  <rect x="240" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">StepVerifier</text>
  <text x="330" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">expectNext / expectError</text>

  <rect x="480" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">verify()</text>

  <line x1="160" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="95" x2="475" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each emitted signal is checked in order against the expectation chain, terminating in a pass/fail verdict.

## 5. Runnable example

### Level 1 — Basic

Verify a simple `Flux`'s exact emitted sequence and normal completion — the most fundamental `StepVerifier` usage.

```java
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

public class StepVerifierBasic {

    record Product(long id, String name) {}

    static Flux<Product> findAll() {
        return Flux.just(
                new Product(1, "Laptop"),
                new Product(2, "Mouse"),
                new Product(3, "Keyboard")
        );
    }

    public static void main(String[] args) {
        StepVerifier.create(findAll())
                .expectNext(new Product(1, "Laptop"))
                .expectNext(new Product(2, "Mouse"))
                .expectNext(new Product(3, "Keyboard"))
                .verifyComplete();

        System.out.println("Exact emission sequence and completion verified -- PASS");
    }
}
```

How to run: add `reactor-core` and `io.projectreactor:reactor-test` to the classpath, then `java StepVerifierBasic.java`.

`StepVerifier.create(findAll())` builds the verification chain without subscribing yet; three `.expectNext(...)` calls describe the exact sequence expected, in order; `.verifyComplete()` is the terminal call — it subscribes, collects and checks each signal against the corresponding expectation, and additionally asserts the stream completes normally (not with an error) after exactly those three items. Any deviation — a missing item, an extra item, a different value, an error instead of completion — produces a clear, specific failure message identifying exactly what diverged.

### Level 2 — Intermediate

Verify error-handling behavior in a reactive pipeline, plus `expectNextCount(...)` for asserting "N more items arrive" without checking each one individually — useful for larger sequences where checking every value would be tedious and not add much confidence.

```java
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

public class StepVerifierIntermediate {

    record Order(long id, double amount) {}

    static class InsufficientFundsException extends RuntimeException {
        InsufficientFundsException(String message) { super(message); }
    }

    static Mono<String> processPayment(Order order, double availableFunds) {
        if (order.amount() > availableFunds) {
            return Mono.error(new InsufficientFundsException(
                    "Order " + order.id() + " needs " + order.amount() + " but only " + availableFunds + " available"));
        }
        return Mono.just("payment-confirmed-" + order.id());
    }

    static Flux<Integer> generateSequence(int count) {
        return Flux.range(1, count);
    }

    public static void main(String[] args) {
        // Verify a successful payment
        StepVerifier.create(processPayment(new Order(1, 50.0), 100.0))
                .expectNext("payment-confirmed-1")
                .verifyComplete();
        System.out.println("Successful payment verified -- PASS");

        // Verify the error path -- checking BOTH the exception type and its message
        StepVerifier.create(processPayment(new Order(2, 500.0), 100.0))
                .expectErrorMatches(error ->
                        error instanceof InsufficientFundsException
                                && error.getMessage().contains("needs 500.0"))
                .verify();
        System.out.println("Insufficient-funds error correctly propagated -- PASS");

        // expectNextCount: verify 100 items arrive without checking each one
        StepVerifier.create(generateSequence(100))
                .expectNextCount(100)
                .verifyComplete();
        System.out.println("Large sequence count verified without per-item checks -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java StepVerifierIntermediate.java`.

`expectErrorMatches(predicate)` verifies both the error's type *and* its content via a lambda, more flexible than `expectError(SomeException.class)` alone when the message or other error details matter to the test. `expectNextCount(100)` asserts exactly 100 more items arrive before whatever comes next in the chain, without requiring 100 individual `expectNext(...)` calls — useful when a sequence's *count* matters more than each individual value for a given test's purpose.

### Level 3 — Advanced

`StepVerifier.withVirtualTime(...)` to test a time-dependent reactive pipeline (a retry with exponential backoff) without the test actually waiting in real time for the delays involved — advancing a virtual clock instead, verifying both the retry behavior and that it doesn't slow down the test suite.

```java
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.util.retry.Retry;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

public class StepVerifierAdvanced {

    static class TransientFailureException extends RuntimeException {
        TransientFailureException(String message) { super(message); }
    }

    static Mono<String> callFlakyService(AtomicInteger attemptCounter) {
        return Mono.defer(() -> {
            int attempt = attemptCounter.incrementAndGet();
            if (attempt < 3) {
                return Mono.error(new TransientFailureException("Attempt " + attempt + " failed"));
            }
            return Mono.just("success-on-attempt-" + attempt);
        });
    }

    public static void main(String[] args) {
        AtomicInteger attemptCounter = new AtomicInteger(0);

        Mono<String> withRetry = callFlakyService(attemptCounter)
                .retryWhen(Retry.backoff(3, Duration.ofSeconds(1))); // real backoff: 1s, 2s, 4s between attempts

        // Without virtual time, this test would take several REAL seconds (1s + 2s of backoff) to run.
        // withVirtualTime lets us verify the same retry behavior in near-zero wall-clock time.
        StepVerifier.withVirtualTime(() -> {
                    attemptCounter.set(0); // reset for this verification run
                    return callFlakyService(attemptCounter)
                            .retryWhen(Retry.backoff(3, Duration.ofSeconds(1)));
                })
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(1))   // advance virtual clock past the FIRST backoff delay
                .thenAwait(Duration.ofSeconds(2))   // advance past the SECOND (doubled) backoff delay
                .expectNext("success-on-attempt-3")
                .verifyComplete();

        System.out.println("Retry-with-backoff behavior verified using virtual time (no real waiting) -- PASS");
        System.out.println("Total attempts made: " + attemptCounter.get());
    }
}
```

How to run: add `reactor-core`, `io.projectreactor:reactor-test`, and `io.projectreactor.addons:reactor-extra` (for `Retry.backoff`, sometimes bundled directly in `reactor-core` depending on version) to the classpath, then `java StepVerifierAdvanced.java`. This runs in milliseconds despite testing multi-second backoff behavior.

`StepVerifier.withVirtualTime(() -> ...)` requires the publisher to be constructed *inside* the supplied lambda (not built beforehand and passed to `create(...)`) — this lets Reactor substitute a virtual `Scheduler` before any time-based operator (like the `retryWhen` backoff delays) is created, so those delays run against virtual, instantly-advanceable time rather than real `Thread.sleep`-backed waiting. `.thenAwait(Duration.ofSeconds(1))` advances the virtual clock by exactly that much, letting the test assert on behavior that would only happen after real time had passed — without the test actually taking that long to execute.

## 6. Walkthrough

Trace `StepVerifierAdvanced.main`'s virtual-time verification:

1. **Verifier construction with deferred publisher.** `StepVerifier.withVirtualTime(() -> { ... })` doesn't build the `Mono` immediately — it first sets up a virtual `Scheduler` as Reactor's default, then invokes the lambda to actually construct `callFlakyService(...).retryWhen(...)`, ensuring the `retryWhen` operator's internal delay scheduling uses that virtual scheduler.
2. **Subscription.** `.expectSubscription()` asserts a subscription occurred (the verification chain's way of saying "and now we've started observing"), then the underlying `Mono` is subscribed to.
3. **First attempt.** `callFlakyService` runs, `attemptCounter` increments to `1`, which is less than `3`, so it emits an error (`TransientFailureException`).
4. **Retry scheduling (virtual).** `retryWhen(Retry.backoff(3, Duration.ofSeconds(1)))` catches this error and schedules a retry after a 1-second backoff — but because the virtual scheduler is active, this "1 second" is a virtual-time marker, not a real `Thread.sleep`.
5. **`thenAwait(Duration.ofSeconds(1))` advances virtual time.** The test explicitly advances the virtual clock by exactly 1 second, which is enough to trigger the pending retry — the second attempt fires immediately (in real wall-clock terms), incrementing `attemptCounter` to `2`, which again is less than `3`, producing another error and scheduling the next backoff (doubled, to 2 seconds, per exponential backoff).
6. **`thenAwait(Duration.ofSeconds(2))` advances virtual time again.** This triggers the third attempt — `attemptCounter` becomes `3`, which is no longer less than `3`, so `callFlakyService` emits `"success-on-attempt-3"` instead of an error.
7. **Final expectations.** `.expectNext("success-on-attempt-3")` confirms that value was emitted, and `.verifyComplete()` confirms the stream then completed normally — all of this happens in milliseconds of real test execution time, because every delay was virtual, not real.

```
withVirtualTime: publisher built with virtual scheduler active

subscribe
   attempt 1 -> error -> schedule retry after 1s (virtual)
thenAwait(1s) -> virtual clock advances -> retry fires
   attempt 2 -> error -> schedule retry after 2s (virtual, doubled backoff)
thenAwait(2s) -> virtual clock advances -> retry fires
   attempt 3 -> success -> emit "success-on-attempt-3"

expectNext("success-on-attempt-3") -- check
verifyComplete() -- check
(all of this: milliseconds of REAL test time, despite 3s of "elapsed" backoff)
```

## 7. Gotchas & takeaways

> Gotcha: `StepVerifier.withVirtualTime(...)` only works correctly if the publisher (including any time-based operators inside it) is constructed *inside* the supplied lambda — constructing it beforehand and passing an already-built `Mono`/`Flux` to a variant expecting a supplier means the time-based operators inside it were already wired to the *real* default scheduler before the virtual one was ever installed, silently defeating virtual time and reverting to genuinely slow, real-time-waiting test behavior with no obvious error explaining why.

- `StepVerifier` is the standard way to assert on a reactive stream's exact emission sequence, error behavior, and completion — the reactive equivalent of asserting on a plain return value, without needing to block or write manual subscriber code.
- `expectNext(...)` checks exact values in order; `expectNextCount(...)` checks quantity without per-item verification; `expectErrorMatches(...)` verifies both error type and content via a predicate.
- Nothing in the verification chain subscribes until the terminal `verify()`/`verifyComplete()`/`verifyError()` call — consistent with the general laziness principle of reactive pipelines covered elsewhere in this content.
- `withVirtualTime(...)` is essential for testing time-dependent operators (delays, timeouts, backoff, intervals) without a test suite that takes real minutes to run — but requires the publisher to be built inside the supplied lambda for the virtual scheduler substitution to actually take effect.
