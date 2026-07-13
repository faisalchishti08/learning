---
card: microservices
gi: 370
slug: context-propagation-across-threads-reactive-micrometer-conte
title: "Context propagation across threads & reactive (Micrometer Context Propagation)"
---

## 1. What it is

**Micrometer Context Propagation** is a library that solves a specific, tricky problem: tracing and logging context (the current span, the [correlation ID](0351-correlation-ids-request-ids.md)) is typically stored in a thread-local variable, but modern Java code frequently hops across threads — a reactive pipeline (WebFlux, Project Reactor) processes a request across a chain of different worker threads, and a `@Async` method or a thread pool submission runs on an entirely different thread than the one that started the request. Thread-local context doesn't automatically follow the logical request as it moves between threads; Micrometer Context Propagation exists to carry it along explicitly.

## 2. Why & when

A thread-local variable, by definition, is only visible to the thread that set it. In traditional blocking, one-thread-per-request code, that's fine — the same thread handles the request start to finish, so a tracing span or correlation ID stored in a thread-local stays available the whole time. But a reactive pipeline deliberately hops across a small pool of worker threads as different stages of the pipeline execute (this is the whole point of reactive programming's efficiency), and each hop would otherwise "lose" whatever was in the previous thread's thread-local storage — a span started on thread A becomes invisible the moment processing continues on thread B, breaking tracing and correlated logging exactly where they matter most.

Use Micrometer Context Propagation (already wired in automatically by Spring Boot's WebFlux and tracing auto-configuration in recent versions) whenever your code uses reactive types (`Mono`, `Flux`) or hops threads via `@Async`, `CompletableFuture`, or a custom executor, and you need tracing/logging context to correctly follow the logical request across those hops. Without it, you'll see broken traces (spans that don't correctly nest under their parent) or missing correlation IDs in log lines emitted from a different thread than where the request began.

## 3. Core concept

Rather than relying on a plain thread-local, context propagation captures the current context explicitly at each hop boundary and reinstates it on the new thread before the next piece of work runs — for reactive pipelines, this is done automatically via hooks Reactor calls at each operator boundary; for manual thread hops (`@Async`, executors), it typically requires wrapping the submitted task so the context capture-and-restore happens around it.

```java
// Reactive: context propagation is largely automatic once wired in.
Mono.just(orderId).map(this::validate).flatMap(this::chargePayment); // span/correlationId correctly follow across hops

// Manual thread hop: context must be EXPLICITLY captured and restored.
ContextSnapshot snapshot = ContextSnapshotFactory.builder().build().captureAll();
executor.submit(() -> { try (var scope = snapshot.setThreadLocals()) { doWork(); } });
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request's span starts on Thread A; without context propagation, the span is lost when processing hops to Thread B; with context propagation, the span context is captured and restored on Thread B, correctly continuing">
  <rect x="20" y="20" width="270" height="60" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Without propagation</text>
  <text x="155" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Thread A span -&gt; Thread B: LOST</text>

  <rect x="340" y="20" width="270" height="60" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="475" y="42" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">With propagation</text>
  <text x="475" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Thread A span -&gt; captured -&gt; restored on Thread B</text>
</svg>

Without explicit propagation, thread-local context is lost at each thread hop; with it, context is captured and restored, following the logical request across threads.

## 5. Runnable example

Scenario: a checkout request processed across two simulated thread hops, first losing its correlation ID at each hop (naive thread-local), then fixed with explicit context capture-and-restore, and finally extended to a chain of hops mimicking a reactive pipeline's multiple operator boundaries.

### Level 1 — Basic

```java
// File: ThreadLocalLostAcrossHops.java -- a correlation ID is set in a
// thread-local on the FIRST thread; when work continues on a DIFFERENT
// thread, the thread-local is simply EMPTY there -- context is LOST.
public class ThreadLocalLostAcrossHops {
    static ThreadLocal<String> correlationIdContext = new ThreadLocal<>();

    public static void main(String[] args) throws InterruptedException {
        correlationIdContext.set("corr-42"); // set on the MAIN thread
        System.out.println("On main thread: correlationId = " + correlationIdContext.get());

        Thread workerThread = new Thread(() -> {
            System.out.println("On worker thread: correlationId = " + correlationIdContext.get()
                    + " -- LOST! Thread-locals do NOT automatically cross threads.");
        });
        workerThread.start();
        workerThread.join();
    }
}
```

How to run: `java ThreadLocalLostAcrossHops.java`

`correlationIdContext.set("corr-42")` only affects the `ThreadLocal`'s value as seen from the main thread. `workerThread` is a genuinely different thread, and `correlationIdContext.get()` from inside it returns `null` — the context was never automatically carried across, exactly the problem that breaks tracing and correlated logging in reactive or thread-hopping code without explicit propagation.

### Level 2 — Intermediate

```java
// File: ExplicitCaptureAndRestore.java -- the context is EXPLICITLY
// captured on the originating thread and RESTORED on the new thread
// before running the next piece of work, mirroring what Micrometer
// Context Propagation automates.
public class ExplicitCaptureAndRestore {
    static ThreadLocal<String> correlationIdContext = new ThreadLocal<>();

    interface Snapshot { void restore(); } // mirrors ContextSnapshot's role

    static Snapshot captureContext() {
        String captured = correlationIdContext.get(); // capture the CURRENT thread's value
        return () -> correlationIdContext.set(captured); // returns a function that RESTORES it elsewhere
    }

    public static void main(String[] args) throws InterruptedException {
        correlationIdContext.set("corr-42");
        Snapshot snapshot = captureContext(); // capture BEFORE hopping threads

        Thread workerThread = new Thread(() -> {
            snapshot.restore(); // RESTORE the captured context on the NEW thread, explicitly
            System.out.println("On worker thread (after restore): correlationId = " + correlationIdContext.get()
                    + " -- CORRECTLY propagated across the thread hop!");
        });
        workerThread.start();
        workerThread.join();
    }
}
```

How to run: `java ExplicitCaptureAndRestore.java`

`captureContext` reads the current thread's `correlationIdContext` value and returns a `Snapshot` whose `restore` method sets that same value on whatever thread calls it. Inside `workerThread`'s body, `snapshot.restore()` runs first, explicitly setting `correlationIdContext` on this new thread to the captured value — so the subsequent `correlationIdContext.get()` correctly returns `"corr-42"`, unlike Level 1's naive approach, demonstrating the explicit capture-and-restore mechanism that context propagation libraries automate.

### Level 3 — Advanced

```java
// File: ChainOfHopsMimicsReactivePipeline.java -- context is captured
// and restored across MULTIPLE sequential thread hops, mimicking a
// reactive pipeline's chain of operators, each potentially running on a
// DIFFERENT worker thread.
import java.util.concurrent.*;
import java.util.function.*;

public class ChainOfHopsMimicsReactivePipeline {
    static ThreadLocal<String> correlationIdContext = new ThreadLocal<>();

    static Supplier<String> withPropagatedContext(Supplier<String> task) { // wraps a task, capturing context AROUND it
        String captured = correlationIdContext.get();
        return () -> {
            String previous = correlationIdContext.get();
            correlationIdContext.set(captured); // restore BEFORE running
            try {
                return task.get();
            } finally {
                correlationIdContext.set(previous); // clean up AFTER, restoring whatever was there before
            }
        };
    }

    public static void main(String[] args) throws Exception {
        correlationIdContext.set("corr-42");
        ExecutorService pool = Executors.newFixedThreadPool(3); // simulates a reactive pipeline's small worker pool

        // Simulates THREE sequential pipeline stages, each potentially on a DIFFERENT thread from the pool.
        Callable<String> stage1 = withPropagatedContext(() -> {
            System.out.println("stage1 [" + Thread.currentThread().getName() + "]: correlationId = " + correlationIdContext.get());
            return "validated";
        })::get;
        Callable<String> stage2 = withPropagatedContext(() -> {
            System.out.println("stage2 [" + Thread.currentThread().getName() + "]: correlationId = " + correlationIdContext.get());
            return "charged";
        })::get;
        Callable<String> stage3 = withPropagatedContext(() -> {
            System.out.println("stage3 [" + Thread.currentThread().getName() + "]: correlationId = " + correlationIdContext.get());
            return "shipped";
        })::get;

        pool.submit(stage1).get();
        pool.submit(stage2).get();
        pool.submit(stage3).get();

        pool.shutdown();
        System.out.println("Every stage saw the CORRECT correlationId, even though each may have run on a DIFFERENT pool thread.");
    }
}
```

How to run: `java ChainOfHopsMimicsReactivePipeline.java`

Each stage is wrapped by `withPropagatedContext`, which captures `correlationIdContext`'s value on the *main* thread (where all three wrapped suppliers are constructed) at the moment of wrapping, and restores that captured value on whatever thread the pool actually runs the task on, regardless of which of the three pool threads is assigned. Submitting all three stages to the pool — potentially each landing on a different worker thread — still results in every stage correctly seeing `"corr-42"`, exactly mirroring how Micrometer Context Propagation ensures tracing and logging context correctly follows a request through a reactive pipeline's chain of operator hops.

## 6. Walkthrough

Trace `ChainOfHopsMimicsReactivePipeline.main` in order. **First**, `correlationIdContext.set("corr-42")` runs on the main thread, and `stage1`, `stage2`, and `stage3` are each constructed by calling `withPropagatedContext` — critically, each of these three calls happens on the main thread, so each captures `"corr-42"` as its `captured` value at construction time, before any thread hop occurs.

**Next**, `pool.submit(stage1).get()` runs: the pool assigns `stage1`'s wrapped lambda to one of its worker threads. Inside that lambda, `correlationIdContext.set(captured)` runs first, setting this worker thread's own thread-local to `"corr-42"` (since that thread's thread-local was previously unset, `previous` is `null`); then the actual task body runs, printing the worker thread's name and the now-correctly-set `correlationId`; finally, the `finally` block restores `correlationIdContext` back to `previous` (`null`) on that worker thread, cleaning up after itself.

**The same pattern repeats for `stage2` and `stage3`**, each potentially running on a different one of the pool's three worker threads (or possibly a reused one, depending on the pool's scheduling), but each independently capturing `"corr-42"` at construction time and correctly restoring it on whichever thread actually executes it.

**Finally**, `main` shuts down the pool and prints a closing confirmation that every stage correctly saw `"corr-42"`, regardless of which specific worker thread it happened to execute on — demonstrating that context propagation makes the *logical* continuity of the request's correlation ID independent of the *physical* thread it happens to run on at each step.

```
main thread: correlationIdContext = corr-42
stage1 wrapped (captures corr-42) -> submitted -> runs on pool-thread-X -> restores corr-42 -> sees corr-42 correctly
stage2 wrapped (captures corr-42) -> submitted -> runs on pool-thread-Y -> restores corr-42 -> sees corr-42 correctly
stage3 wrapped (captures corr-42) -> submitted -> runs on pool-thread-Z -> restores corr-42 -> sees corr-42 correctly
```

## 7. Gotchas & takeaways

> Forgetting to restore the *previous* thread-local value after a task completes (skipping the `finally` cleanup) can leak context between unrelated tasks that happen to reuse the same pooled thread later — a subsequent, completely unrelated task might incorrectly see a stale correlation ID left behind by an earlier one. Always capture and restore the previous value symmetrically, not just set-and-forget the new one.

- Thread-local context (tracing spans, correlation IDs) does not automatically follow a logical request across thread hops — reactive pipelines and manual thread submissions (`@Async`, executors) all introduce this risk.
- Micrometer Context Propagation solves this by explicitly capturing context at the point of a hop and restoring it on the new thread before work continues, automated for reactive pipelines and available for manual use elsewhere.
- Always restore the *previous* value (not just clear it) after a task completes, to avoid leaking context into unrelated work that later reuses the same pooled thread.
- This mechanism is what keeps [distributed tracing](0352-distributed-tracing-concepts-trace-span-context-propagation.md) and correlated [structured logging](0360-structured-logging.md) working correctly in reactive Spring WebFlux applications, not just traditional blocking ones.
