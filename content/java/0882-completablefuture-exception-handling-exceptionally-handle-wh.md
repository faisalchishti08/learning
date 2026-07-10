---
card: java
gi: 882
slug: completablefuture-exception-handling-exceptionally-handle-wh
title: CompletableFuture exception handling (exceptionally/handle/whenComplete)
---

## 1. What it is

When a stage in a `CompletableFuture` chain throws, the exception propagates down the chain as a **completion exception**, skipping every subsequent `thenApply`/`thenAccept`/`thenCompose` stage until it reaches a stage designed to handle failure. `exceptionally(Function<Throwable,T>)` supplies a fallback value only if the future completed exceptionally, letting the chain recover and continue as if nothing went wrong. `handle(BiFunction<T,Throwable,R>)` runs regardless of success or failure, receiving *both* the result (or `null`) and the exception (or `null`), and lets you produce a new value either way. `whenComplete(BiConsumer<T,Throwable>)` also runs regardless of outcome, but is for a side effect (logging, cleanup) — it doesn't change the result and re-throws the original exception (if any) onward down the chain.

## 2. Why & when

Use `exceptionally` when you have one specific fallback value or behavior to substitute in on failure — a cached or default result if a live fetch fails — and don't need to know anything else. Use `handle` when you need to inspect *both* the success and failure paths in one place to decide what to produce — for example, wrapping either outcome into a uniform `Result` object. Use `whenComplete` purely for side effects that should happen regardless of outcome without altering the chain's actual result or exception — logging that a stage finished, releasing a resource, updating a metric — since unlike `handle`, it lets the original success value or exception propagate onward unchanged. Getting these three right prevents two common failure modes: an unhandled exception silently propagating all the way to a final `get()`/`join()` call and surfacing as a generic wrapped exception with no earlier context, or a `handle` accidentally swallowing a real error by not checking whether the `Throwable` argument was non-null.

## 3. Core concept

```java
CompletableFuture<Integer> result = CompletableFuture
    .supplyAsync(() -> riskyFetch())
    .exceptionally(ex -> {
        System.out.println("fetch failed: " + ex.getMessage());
        return -1; // fallback value -- chain continues as if this had been the success value
    });

CompletableFuture<String> handled = CompletableFuture
    .supplyAsync(() -> riskyFetch())
    .handle((value, ex) -> ex != null ? "error: " + ex.getMessage() : "value: " + value);

CompletableFuture<Integer> logged = CompletableFuture
    .supplyAsync(() -> riskyFetch())
    .whenComplete((value, ex) -> {
        if (ex != null) System.out.println("logging failure: " + ex);
        else System.out.println("logging success: " + value);
    }); // does NOT change the outcome -- exception (if any) still propagates onward
```

`exceptionally` only fires on failure and supplies a replacement value; `handle` always fires and lets you inspect both outcomes; `whenComplete` always fires but is purely observational — it can't turn a failure into a success.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A CompletableFuture chain where a stage throws; exceptionally supplies a fallback and the chain recovers; handle always runs on either path; whenComplete observes without altering the outcome">
  <rect x="20" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="100" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">stage throws</text>

  <rect x="220" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="300" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">exceptionally -&gt; fallback</text>

  <rect x="420" y="20" width="160" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">chain continues normally</text>

  <line x1="180" y1="37" x2="216" y2="37" stroke="#8b949e" stroke-width="2" marker-end="url(#a18)"/>
  <line x1="380" y1="37" x2="416" y2="37" stroke="#8b949e" stroke-width="2" marker-end="url(#a18)"/>

  <rect x="20" y="90" width="560" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="300" y="113" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">handle(value, ex) -- ALWAYS runs, on success OR failure, produces new result</text>

  <rect x="20" y="145" width="560" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="300" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">whenComplete(value, ex) -- ALWAYS runs, side effect only, outcome unchanged</text>

  <defs><marker id="a18" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*`exceptionally` recovers from failure only; `handle` runs either way and can change the result; `whenComplete` runs either way and only observes.*

## 5. Runnable example

Scenario: fetching a configuration value with a flaky remote source, growing from an unhandled-exception version that fails loudly at the end, to using `exceptionally` for a graceful fallback, to a version combining `handle` and `whenComplete` for both proper recovery and unconditional logging.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class UnhandledException {
    static int riskyFetch() {
        if (Math.random() < 1.0) throw new IllegalStateException("remote source unavailable"); // always fails, for the demo
        return 42;
    }

    public static void main(String[] args) {
        CompletableFuture<Integer> future = CompletableFuture.supplyAsync(UnhandledException::riskyFetch);
        try {
            Integer value = future.join(); // throws CompletionException wrapping the original
            System.out.println("value = " + value);
        } catch (CompletionException e) {
            System.out.println("chain failed with no recovery: " + e.getCause().getMessage());
        }
    }
}
```

**How to run:** `java UnhandledException.java` (JDK 17+).

Expected output:
```
chain failed with no recovery: remote source unavailable
```

The exception is only ever observed at the very end, by whichever code called `join()` — there's no opportunity to substitute a fallback value or continue the pipeline with any subsequent `thenApply` stages, since they'd all be skipped.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;

public class ExceptionallyFallback {
    static int riskyFetch() {
        throw new IllegalStateException("remote source unavailable"); // always fails, for the demo
    }

    public static void main(String[] args) {
        CompletableFuture<Integer> future = CompletableFuture
            .supplyAsync(ExceptionallyFallback::riskyFetch)
            .exceptionally(ex -> {
                System.out.println("caught failure: " + ex.getMessage() + " -- using fallback");
                return -1; // fallback value -- the chain "recovers" as if this had succeeded
            })
            .thenApply(value -> value * 100); // this DOES run, since exceptionally recovered

        System.out.println("final value = " + future.join());
    }
}
```

**How to run:** `java ExceptionallyFallback.java`.

Expected output:
```
caught failure: remote source unavailable -- using fallback
final value = -100
```

The real-world concern added: `exceptionally` intercepts the failure and supplies `-1` as a substitute result, letting the chain continue normally into the subsequent `thenApply` stage (`value * 100`), which would otherwise have been skipped entirely had the exception been left unhandled.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class HandleAndWhenCompleteTogether {
    static AtomicInteger callCount = new AtomicInteger(0);

    static int riskyFetch() {
        int attempt = callCount.incrementAndGet();
        if (attempt == 1) throw new IllegalStateException("first attempt failed");
        return 42; // succeeds on subsequent calls, simulating a flaky-then-recovering source
    }

    public static void main(String[] args) {
        // First call: fails. whenComplete logs it (without altering the outcome), handle then
        // converts the failure into a typed, uniform result rather than propagating the exception.
        CompletableFuture<String> firstResult = CompletableFuture
            .supplyAsync(HandleAndWhenCompleteTogether::riskyFetch)
            .whenComplete((value, ex) -> {
                if (ex != null) System.out.println("[log] attempt failed: " + ex.getCause().getMessage());
                else System.out.println("[log] attempt succeeded: " + value);
            })
            .handle((value, ex) -> ex != null ? "DEGRADED(default)" : "OK(" + value + ")");

        System.out.println("first result: " + firstResult.join());

        // Second call: succeeds outright. Same chain, same logging and handling logic, but
        // now on the success path -- demonstrating both branches are correctly exercised.
        CompletableFuture<String> secondResult = CompletableFuture
            .supplyAsync(HandleAndWhenCompleteTogether::riskyFetch)
            .whenComplete((value, ex) -> {
                if (ex != null) System.out.println("[log] attempt failed: " + ex.getCause().getMessage());
                else System.out.println("[log] attempt succeeded: " + value);
            })
            .handle((value, ex) -> ex != null ? "DEGRADED(default)" : "OK(" + value + ")");

        System.out.println("second result: " + secondResult.join());
    }
}
```

**How to run:** `java HandleAndWhenCompleteTogether.java`.

Expected output:
```
[log] attempt failed: first attempt failed
first result: DEGRADED(default)
[log] attempt succeeded: 42
second result: OK(42)
```

This adds the production-flavored hard case: `whenComplete` runs on *both* paths purely to log what happened, without changing the eventual result — note that inside `whenComplete`, the exception argument (when the async stage threw) is wrapped as a `CompletionException`, so `ex.getCause()` retrieves the original `IllegalStateException`. Immediately after, `handle` runs on both paths too, this time actually producing a new, uniform `String` result (`"DEGRADED(default)"` or `"OK(42)"`) regardless of whether the underlying fetch succeeded or failed — demonstrating the clean separation of concerns: `whenComplete` for observation, `handle` for recovery/transformation.

## 6. Walkthrough

Tracing the `firstResult` chain in `HandleAndWhenCompleteTogether.main`:

1. `CompletableFuture.supplyAsync(...)` runs `riskyFetch()` on a common-pool thread. Since this is the first call, `callCount.incrementAndGet()` returns `1`, and the method throws `IllegalStateException("first attempt failed")`.
2. The framework catches this and marks the future as completed exceptionally, wrapping the thrown exception in a `CompletionException` internally for propagation purposes.
3. `.whenComplete((value, ex) -> {...})` runs next regardless of outcome — since this stage failed, `value` is `null` and `ex` is non-null (the wrapping `CompletionException`). The lambda checks `ex != null`, calls `ex.getCause()` to retrieve the original `IllegalStateException`, and logs its message. Critically, `whenComplete` does not swallow or alter the exception — it re-propagates the same failure to the next stage in the chain.
4. `.handle((value, ex) -> ...)` runs next, also regardless of outcome — again `ex` is non-null here, so the ternary evaluates to `"DEGRADED(default)"`. Unlike `whenComplete`, `handle`'s return value *becomes* the new result of the chain — the future is now considered successfully completed with the string `"DEGRADED(default)"`, and the original exception is fully absorbed and does not propagate any further.
5. `firstResult.join()` therefore returns `"DEGRADED(default)"` without throwing, and `main` prints it.
6. For `secondResult`, `riskyFetch()` runs again — `callCount` is now `2`, so the method returns `42` successfully. `whenComplete` still runs, but this time `ex` is `null` and `value` is `42`, so it logs the success branch. `handle` also still runs, and since `ex` is `null`, evaluates to `"OK(42)"`, which becomes `secondResult`'s final value.
7. This demonstrates that `whenComplete` and `handle` both execute unconditionally on *every* completion, successful or not — the difference is purely in what each is meant to do with that information: observe versus transform.

## 7. Gotchas & takeaways

> **Gotcha:** inside `whenComplete` or `handle`, an exception from an async stage arrives wrapped in a `CompletionException` (not the original exception type directly) — always call `.getCause()` to retrieve the actual underlying exception your code threw, or your failure-detection logic (like checking `instanceof SomeSpecificException`) will silently never match.

- `exceptionally` supplies a fallback value only on failure — the chain "recovers" and any subsequent stages run normally, as if the fallback had been the original successful result.
- `handle` always runs, on success or failure, and lets you produce a new result either way — useful for normalizing both outcomes into one uniform shape.
- `whenComplete` always runs but is purely observational — it can't change the result or swallow an exception; the original outcome (success value or exception) propagates onward unchanged after it runs.
- Unhandled exceptions in a `CompletableFuture` chain skip every subsequent `thenApply`/`thenAccept`/`thenCompose` stage and only surface at a terminal `get()`/`join()` call, wrapped in `ExecutionException` or `CompletionException` respectively — always add explicit exception handling (`exceptionally` or `handle`) at the point where failure should actually be dealt with, not just at the very end.
- Place `whenComplete` for logging *before* a `handle` that transforms failure into a fallback, if you want the log to still reflect the original failure rather than the already-recovered value.
