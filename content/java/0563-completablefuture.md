---
card: java
gi: 563
slug: completablefuture
title: CompletableFuture
---

## 1. What it is

`CompletableFuture<T>` is Java 8's improved asynchronous computation type: a `Future<T>` (a stand-in for a result that isn't ready yet) that you can also **chain** — attach callbacks that run when the result arrives, combine multiple futures together, and complete manually from outside. It replaces the old `Future`, which only let you *block* (`get()`) waiting for a result, with a composable pipeline for building async workflows.

## 2. Why & when

The original `Future` interface (Java 5) had one fatal limitation: the only way to react to its completion was to call `get()`, which blocks the calling thread until the result is ready — there was no way to say "when this finishes, then do X" without blocking a thread just to wait. That made chaining multiple async steps, running several tasks in parallel and combining results, or handling errors without blocking, all awkward or impossible. `CompletableFuture` fixes this: `.thenApply(...)`, `.thenCompose(...)`, `.thenCombine(...)`, `.exceptionally(...)` let you build a pipeline of async steps that only "wake up" and run when their input is ready, with no thread sitting idle in `get()`. Use it whenever you have I/O-bound or otherwise async work (HTTP calls, database queries) that you want to run concurrently and combine without manually managing threads.

## 3. Core concept

```java
CompletableFuture<String> future = CompletableFuture
    .supplyAsync(() -> fetchUserName(42))       // runs on a background thread
    .thenApply(name -> name.toUpperCase())       // transforms the result when ready
    .exceptionally(ex -> "UNKNOWN");             // fallback if any prior step threw

String result = future.join(); // blocks only here, at the very end, if needed
```

`supplyAsync` starts async work and returns immediately with an incomplete future. `thenApply` registers a transformation that runs automatically once the previous stage completes — no explicit blocking or callback registration boilerplate. `join()` (or `get()`) blocks only when you actually need the final value, ideally as late as possible in the program.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CompletableFuture chains stages that fire automatically as each previous stage completes">
  <rect x="10" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">supplyAsync</text>

  <line x1="160" y1="40" x2="210" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#c1)"/>

  <rect x="210" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="285" y="45" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">thenApply</text>

  <line x1="360" y1="40" x2="410" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#c2)"/>

  <rect x="410" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#d2a8ff"/>
  <text x="485" y="45" fill="#d2a8ff" font-size="11" text-anchor="middle" font-family="monospace">exceptionally</text>

  <text x="10" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">Calling thread never blocks between stages — each stage's callback</text>
  <text x="10" y="105" fill="#8b949e" font-size="10" font-family="sans-serif">runs (on a pool thread) automatically once its input is ready.</text>
  <text x="10" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">Only .join() / .get() actually blocks — and only if called.</text>

  <defs>
    <marker id="c1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="c2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each stage is wired to fire off of the previous one; nothing here forces a thread to sit and wait.

## 5. Runnable example

Scenario: fetching a user's profile and their order history from two separate (simulated) services and combining them into a summary — starting with a single async call, then chaining a transformation and error handling, then running two independent calls in parallel and combining their results.

### Level 1 — Basic

```java
import java.util.concurrent.CompletableFuture;

public class FutureBasic {
    static String fetchUserName(int userId) {
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
        return "user-" + userId;
    }

    public static void main(String[] args) {
        CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> fetchUserName(42));

        System.out.println("Request sent, doing other work while we wait...");
        String name = future.join();
        System.out.println("Got name: " + name);
    }
}
```

**How to run:** `java FutureBasic.java`

Expected output:
```
Request sent, doing other work while we wait...
Got name: user-42
```

`CompletableFuture.supplyAsync(() -> fetchUserName(42))` starts `fetchUserName` on a background thread (from `ForkJoinPool.commonPool()` by default) and returns immediately — `main` continues on to print `"Request sent..."` while the 100ms `fetchUserName` call is still running elsewhere. `future.join()` is where `main` finally waits, blocking until the background computation finishes, then returning its result.

### Level 2 — Intermediate

```java
import java.util.concurrent.CompletableFuture;

public class FutureChained {
    static String fetchUserName(int userId) {
        if (userId < 0) throw new IllegalArgumentException("Invalid user id: " + userId);
        try { Thread.sleep(100); } catch (InterruptedException ignored) {}
        return "user-" + userId;
    }

    static CompletableFuture<String> greet(int userId) {
        return CompletableFuture
            .supplyAsync(() -> fetchUserName(userId))
            .thenApply(name -> "Hello, " + name.toUpperCase() + "!")
            .exceptionally(ex -> "Hello, guest! (lookup failed: " + ex.getCause().getMessage() + ")");
    }

    public static void main(String[] args) {
        System.out.println(greet(42).join());
        System.out.println(greet(-1).join());
    }
}
```

**How to run:** `java FutureChained.java`

Expected output:
```
Hello, USER-42!
Hello, guest! (lookup failed: Invalid user id: -1)
```

The real-world concern this adds: **transforming** a successful result (`thenApply`) and **recovering** from a failure (`exceptionally`) without ever calling `get()`/`join()` in the middle of the pipeline. For `userId=42`, `fetchUserName` succeeds, `thenApply` uppercases the name, and `exceptionally` is skipped entirely (no exception occurred). For `userId=-1`, `fetchUserName` throws; the exception propagates through the pipeline (skipping `thenApply`, since there's no successful value to transform) straight to `exceptionally`, which supplies a fallback string instead of letting the exception escape to the caller.

### Level 3 — Advanced

```java
import java.util.concurrent.CompletableFuture;

public class FutureCombined {
    record Profile(String name, String email) {}
    record OrderHistory(int orderCount) {}
    record Summary(String name, String email, int orderCount) {}

    static CompletableFuture<Profile> fetchProfile(int userId) {
        return CompletableFuture.supplyAsync(() -> {
            sleep(150);
            return new Profile("user-" + userId, "user" + userId + "@example.com");
        });
    }

    static CompletableFuture<OrderHistory> fetchOrders(int userId) {
        return CompletableFuture.supplyAsync(() -> {
            sleep(100);
            return new OrderHistory(userId % 5); // pretend order count
        });
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }

    public static void main(String[] args) {
        long start = System.currentTimeMillis();

        CompletableFuture<Profile> profileFuture = fetchProfile(42);
        CompletableFuture<OrderHistory> ordersFuture = fetchOrders(42);

        CompletableFuture<Summary> summaryFuture = profileFuture.thenCombine(ordersFuture,
            (profile, orders) -> new Summary(profile.name(), profile.email(), orders.orderCount()));

        Summary summary = summaryFuture.join();
        long elapsedMs = System.currentTimeMillis() - start;

        System.out.println(summary);
        System.out.println("Elapsed: ~" + (elapsedMs / 50 * 50) + " ms (roughly the SLOWER call, not the sum)");
    }
}
```

**How to run:** `java FutureCombined.java`

Expected output (elapsed time is approximate, rounded for stable output; genuinely close to 150ms, not 250ms):
```
Summary[name=user-42, email=user42@example.com, orderCount=2]
Elapsed: ~150 ms (roughly the SLOWER call, not the sum)
```

This handles the production-flavoured case of **running two independent async calls concurrently and merging their results** — exactly like fetching a user profile from one service and their order history from another, in parallel, rather than one after another. `fetchProfile` (150ms) and `fetchOrders` (100ms) both start immediately and run on separate background threads at the same time; `thenCombine` registers a callback that fires only once *both* futures have completed, combining their two results into one `Summary`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `start` records the current time.

`fetchProfile(42)` is called, which immediately calls `CompletableFuture.supplyAsync(...)` — this schedules the profile-fetching lambda onto a background thread and returns a `CompletableFuture<Profile>` right away, *not yet complete*. `main` does not block here. Likewise, `fetchOrders(42)` schedules its own lambda onto another background thread and returns immediately.

At this point, both background threads are running concurrently: one sleeping 150ms before building a `Profile`, the other sleeping 100ms before building an `OrderHistory`. Because both were started before either was waited on, their execution overlaps in wall-clock time rather than happening one after another.

```
t=0ms    : fetchProfile starts (needs 150ms) | fetchOrders starts (needs 100ms)
t=100ms  : fetchOrders completes -> OrderHistory(orderCount=2) ready, profileFuture still pending
t=150ms  : fetchProfile completes -> Profile(name=user-42, email=user42@example.com) ready
t=150ms  : BOTH futures now complete -> thenCombine's callback fires
```

`profileFuture.thenCombine(ordersFuture, (profile, orders) -> new Summary(...))` registers a callback that Java only invokes once *both* `profileFuture` and `ordersFuture` have completed — it doesn't matter which one finishes first; the combining function waits for the slower of the two. Since `fetchOrders` finishes at ~100ms but `fetchProfile` doesn't finish until ~150ms, the combined `Summary` isn't ready until ~150ms — the *maximum* of the two durations, not their sum (~250ms), because they ran in parallel rather than sequentially.

`summaryFuture.join()` blocks `main` until that combined result is ready, returning `Summary[name=user-42, email=user42@example.com, orderCount=2]`. `elapsedMs` measures roughly 150ms (rounded down to the nearest 50ms in the printed output to keep it deterministic across runs, since exact timing varies slightly machine to machine), confirming the two calls really did run concurrently rather than one after another.

## 7. Gotchas & takeaways

> `get()` and `join()` do the same thing (block until the result is ready) but differ in exception handling: `get()` throws a **checked** `InterruptedException`/`ExecutionException`, forcing a try/catch; `join()` throws an **unchecked** `CompletionException` wrapping the original cause instead, which is why chained pipelines (like `exceptionally` in the Level 2 example) usually access the real cause via `ex.getCause()`. Prefer `join()` inside code that's already lambda-heavy to avoid checked-exception boilerplate.

- `supplyAsync`/`runAsync` default to `ForkJoinPool.commonPool()` — the same shared pool used by parallel streams. For CPU-bound or long-running blocking work, pass an explicit `Executor` (e.g., `supplyAsync(task, myExecutor)`) to avoid starving that shared pool.
- `thenApply` transforms a value synchronously on whichever thread completes the previous stage; `thenApplyAsync` instead schedules the transformation on the async executor — matters if the transformation itself is expensive or blocking.
- `thenCompose` (not shown above) is for chaining a step that *itself* returns a `CompletableFuture` — flattening nested futures, analogous to `Optional.flatMap`. Using `thenApply` for that instead produces a `CompletableFuture<CompletableFuture<T>>`, which is almost never what's wanted.
- `thenCombine` waits for **both** futures involved; `CompletableFuture.allOf(...)` waits for an arbitrary number of futures to all complete (returning `Void`, so results must be pulled individually afterward); `CompletableFuture.anyOf(...)` completes as soon as **any one** of several futures completes.
- An uncaught exception inside `supplyAsync`'s lambda doesn't crash the calling thread — it's captured and stored in the future, only surfacing when something calls `join()`/`get()` (as a wrapped exception) or when an `exceptionally`/`handle` stage is attached to recover from it.
