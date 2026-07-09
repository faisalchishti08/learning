---
card: java
gi: 753
slug: scoped-values-preview
title: Scoped values (preview)
---

## 1. What it is

**Java 21** (JEP 446) moves [scoped values](0732-scoped-values-incubator.md) from **incubator** to **preview** status — a step closer to a permanent, standard API — after one incubator round in Java 20. The type moves from the incubator package `jdk.incubator.concurrent.ScopedValue` to `java.lang.ScopedValue`, signaling the JDK team's growing confidence in the design: immutable, block-scoped context sharing via `ScopedValue.where(...).run(...)`, automatically unbound when the block exits, designed to propagate cheaply and correctly into child tasks forked by [structured concurrency](0754-structured-concurrency-preview.md). As a preview feature (rather than an incubator module), it now requires only `--enable-preview`, not a separate `--add-modules` for an incubator module — a smaller, more standard-shaped adoption step for anyone testing it in Java 21.

## 2. Why & when

The move from incubator to preview is itself meaningful: incubator modules (under `jdk.incubator.*`) are explicitly for APIs still undergoing significant design changes, while preview features (under the eventual permanent package, gated only by `--enable-preview`) signal that the API's shape is close to final and the remaining open questions are about polish, not fundamentals. For scoped values specifically, the incubator round in Java 20 validated the core design against real structured-concurrency workloads; this preview round in Java 21 is where the API sees its first broad usage under something closer to its final name and package, ahead of eventual standardization. Practically, this is the point where scoped values become worth prototyping seriously against real request-scoped-context use cases (request IDs, auth principals, trace context) if you're evaluating whether to migrate off `ThreadLocal` — the risk of the API changing meaningfully out from under you is lower here than during incubation, though it's still a preview, so production adoption should wait for standardization.

## 3. Core concept

```java
// Now java.lang.ScopedValue — no incubator module needed, just --enable-preview.
static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

static void handleRequest(String id) {
    ScopedValue.where(REQUEST_ID, id).run(() -> {
        processRequest(); // REQUEST_ID.get() is visible anywhere in this call tree
    });
    // REQUEST_ID is automatically unbound here — no cleanup call needed
}

static void processRequest() {
    System.out.println("handling request " + REQUEST_ID.get());
}
```

The binding is visible to `processRequest` (and to any structured-concurrency subtasks forked within the `run` block) purely because they execute within its dynamic scope — no parameter threading required.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A scoped value is bound only for the duration of a run block, visible to every method and subtask called within it, and automatically unbound when the block exits">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">ScopedValue.where(REQUEST_ID, "req-42").run(() -&gt; { ... })</text>

  <rect x="80" y="80" width="480" height="70" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="320" y="105" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">bound for the lifetime of this block only</text>
  <text x="320" y="125" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">processRequest() -&gt; validate() -&gt; forked subtasks -&gt; all see REQUEST_ID</text>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Binding disappears the instant run() returns — no explicit unbind, no leak risk</text>
</svg>

*A scoped value's lifetime is tied exactly to one block's execution — nothing to remember to clean up.*

## 5. Runnable example

Scenario: a request handler that needs a request ID visible throughout its call tree for logging, growing from manual parameter threading to full scoped-value propagation.

### Level 1 — Basic

```java
public class RequestIdParam {
    static void handleRequest(String requestId) {
        validate(requestId);
        process(requestId);
    }

    static void validate(String requestId) {
        System.out.println("[" + requestId + "] validating");
    }

    static void process(String requestId) {
        System.out.println("[" + requestId + "] processing");
    }

    public static void main(String[] args) {
        handleRequest("req-1");
        handleRequest("req-2");
    }
}
```

**How to run:** `java RequestIdParam.java` (JDK 21+, no preview flag needed for this baseline version).

This is the manual-threading style: `requestId` gets passed as an explicit parameter through every method that needs it, even methods (like a deeper helper several calls down) that only pass it further along without using it themselves.

### Level 2 — Intermediate

```java
public class RequestIdScoped {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static void handleRequest(String requestId) {
        ScopedValue.where(REQUEST_ID, requestId).run(() -> {
            validate();
            process();
        });
    }

    static void validate() {
        System.out.println("[" + REQUEST_ID.get() + "] validating");
    }

    static void process() {
        System.out.println("[" + REQUEST_ID.get() + "] processing");
    }

    public static void main(String[] args) {
        handleRequest("req-1");
        handleRequest("req-2");
    }
}
```

**How to run:** `java --enable-preview --source 21 RequestIdScoped.java`.

The real-world concern added: `validate()` and `process()` no longer take `requestId` as a parameter at all — they read `REQUEST_ID.get()` directly, and the binding is scoped exactly to the `run(...)` block in `handleRequest`, disappearing automatically once it returns.

### Level 3 — Advanced

```java
import java.util.concurrent.*;

public class RequestIdStructured {
    static final ScopedValue<String> REQUEST_ID = ScopedValue.newInstance();

    static void handleRequest(String requestId) throws Exception {
        ScopedValue.where(REQUEST_ID, requestId).run(() -> {
            try {
                fanOutToServices();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
    }

    static void fanOutToServices() throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            var inventory = scope.fork(() -> callService("inventory"));
            var pricing = scope.fork(() -> callService("pricing"));
            scope.join().throwIfFailed();
            System.out.println("results: " + inventory.get() + ", " + pricing.get());
        }
    }

    static String callService(String name) {
        // each forked subtask sees the SAME REQUEST_ID bound by the parent
        return "[" + REQUEST_ID.get() + "] " + name + " ok";
    }

    public static void main(String[] args) throws Exception {
        handleRequest("req-1");
        handleRequest("req-2");
    }
}
```

**How to run:** `java --enable-preview --source 21 --add-modules jdk.incubator.concurrent RequestIdStructured.java` (structured concurrency is still incubating separately in Java 21 — see [structured concurrency (preview)](0754-structured-concurrency-preview.md) for the exact flags needed on this JDK version).

This adds the production-flavored hard case: `REQUEST_ID` bound once in `handleRequest`, then read from **two concurrently forked subtasks** inside a `StructuredTaskScope` — demonstrating the exact scenario scoped values were designed for: context that needs to be visible not just down a sequential call chain, but across fan-out into concurrent child tasks, without any explicit parameter passed into `callService`.

## 6. Walkthrough

Tracing `RequestIdStructured.handleRequest("req-1")`:

1. `ScopedValue.where(REQUEST_ID, "req-1").run(...)` binds `REQUEST_ID` to `"req-1"` for the dynamic extent of the lambda passed to `run`.
2. Inside that lambda, `fanOutToServices()` is called. Because it executes within the `run` block's dynamic scope, `REQUEST_ID.get()` would already return `"req-1"` here, though `fanOutToServices` itself doesn't call it directly.
3. `fanOutToServices` opens a `StructuredTaskScope.ShutdownOnFailure` and forks two subtasks: one calling `callService("inventory")`, one calling `callService("pricing")`. Each `fork` call starts a new virtual thread running that lambda.
4. Crucially, **both forked subtasks** run within the scoped value's binding, because structured concurrency's subtasks are considered part of the same logical "thread of execution" as their parent for scoped-value purposes — so each subtask's call to `REQUEST_ID.get()` inside `callService` returns `"req-1"`, without `"req-1"` ever being passed as an explicit argument to `callService`.
5. `scope.join()` blocks until both subtasks finish (or one fails); `throwIfFailed()` re-throws any subtask's exception if one occurred. Here both succeed.
6. `fanOutToServices` reads both subtasks' results via `.get()` and prints them.
7. The `run` block returns, and `REQUEST_ID`'s binding to `"req-1"` is automatically discarded — the next call, `handleRequest("req-2")`, establishes a completely fresh binding with no possibility of the previous request's ID leaking through.

Expected output:
```
results: [req-1] inventory ok, [req-1] pricing ok
results: [req-2] inventory ok, [req-2] pricing ok
```

## 7. Gotchas & takeaways

> **Gotcha:** in Java 21, scoped values are a **preview** feature while structured concurrency is still a **separate incubator** module — the two features are designed to work together, but check the exact flag combination your JDK build requires (`--enable-preview` for scoped values, plus `--add-modules jdk.incubator.concurrent` for structured concurrency) rather than assuming one flag covers both.

- Preview in Java 21 (up from incubator in Java 20) — package moved to `java.lang.ScopedValue`, only `--enable-preview` needed for the scoped-value part itself.
- Bindings are immutable and exist only for the duration of the enclosing `run`/`call` block — no `.remove()` to forget, unlike `ThreadLocal`.
- Designed specifically to propagate correctly and cheaply into subtasks forked by structured concurrency — see [structured concurrency (preview)](0754-structured-concurrency-preview.md).
- Prefer scoped values over `ThreadLocal` for request-scoped context (IDs, auth principals, trace data), especially in code using virtual threads or structured concurrency.
- Still a preview: expect possible refinements before eventual standardization, and avoid depending on this exact API shape in production code until it's finalized.
