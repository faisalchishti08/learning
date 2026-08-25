# Java CompletableFuture

## Overview

`CompletableFuture<T>` (Java 8+) is a promise-based async computation model. Unlike plain `Future`, it supports non-blocking chaining, composition, exception handling, and manual completion. It implements both `Future<T>` and `CompletionStage<T>`.

---

## 1. Creation

### Visual Diagram — Creation Methods

```
CompletableFuture.supplyAsync(() -> value)   ← runs in ForkJoinPool.commonPool(), returns T
CompletableFuture.runAsync(() -> sideEffect) ← runs in pool, returns Void
CompletableFuture.completedFuture(value)     ← already done, no async
CompletableFuture.failedFuture(ex)           ← [Java 9+] already failed
CompletableFuture.supplyAsync(supplier, executor) ← custom thread pool

Timeline:
  supplyAsync:  [thread pool]--[compute]--[complete]
  completedFuture: [already complete] ← no thread spawned
```

### Example 1 — All Creation Forms

```java
import java.util.concurrent.*;

public class CFCreation {
    public static void main(String[] args) throws Exception {
        // supplyAsync — async, returns a value
        CompletableFuture<String> cf1 = CompletableFuture.supplyAsync(() -> {
            // runs in ForkJoinPool.commonPool()
            return "Hello from async";
        });
        System.out.println(cf1.get()); // Hello from async

        // runAsync — async, no return value
        CompletableFuture<Void> cf2 = CompletableFuture.runAsync(() ->
            System.out.println("Side effect in pool")
        );
        cf2.get(); // wait for completion

        // completedFuture — already done, no thread spawned
        CompletableFuture<Integer> cf3 = CompletableFuture.completedFuture(42);
        System.out.println(cf3.get()); // 42 — returns immediately

        // failedFuture [Java 9+] — already failed
        CompletableFuture<String> cf4 = CompletableFuture.failedFuture(
            new RuntimeException("already failed")
        );
        // cf4.get() would throw ExecutionException

        // Custom executor
        ExecutorService pool = Executors.newFixedThreadPool(4);
        CompletableFuture<String> cf5 = CompletableFuture.supplyAsync(
            () -> "Custom pool result",
            pool
        );
        System.out.println(cf5.get()); // Custom pool result
        pool.shutdown();
    }
}
```

**What this does:** `supplyAsync` is the workhorse — spawns computation in a thread pool. `completedFuture` is for wrapping already-known values (useful in tests and fallbacks). Custom executor gives control over thread count and lifecycle.

### Example 2 — Manual Completion

```java
import java.util.concurrent.*;

public class ManualCompletion {
    public static void main(String[] args) throws Exception {
        CompletableFuture<String> cf = new CompletableFuture<>();

        // Simulate external callback completing the future
        new Thread(() -> {
            try {
                Thread.sleep(100);
                cf.complete("done by callback");    // signals completion
            } catch (InterruptedException e) {
                cf.completeExceptionally(e);         // signals failure
            }
        }).start();

        System.out.println(cf.get()); // blocks until complete → "done by callback"

        // completeOnTimeout [Java 9+]
        CompletableFuture<String> withTimeout = CompletableFuture
            .supplyAsync(() -> {
                try { Thread.sleep(5000); } catch (InterruptedException e) {}
                return "too slow";
            })
            .completeOnTimeout("default", 200, TimeUnit.MILLISECONDS);

        System.out.println(withTimeout.get()); // "default" (timeout fires first)
    }
}
```

**What this does:** Manual completion bridges callback-based APIs into CompletableFuture. `completeOnTimeout` [Java 9+] provides a fallback value when computation takes too long.

---

## 2. Chaining — thenApply / thenAccept / thenRun

### Visual Diagram — Chain Types

```
thenApply(fn):   T → U     — transform result, returns CompletableFuture<U>
thenAccept(fn):  T → void  — consume result, returns CompletableFuture<Void>
thenRun(fn):     void      — run after done (no access to result), Void

Async variants (run the fn in a thread pool):
  thenApplyAsync(fn)
  thenAcceptAsync(fn)
  thenRunAsync(fn)

Without Async: the fn runs in the completing thread (may be caller's thread).
With Async:    the fn runs in ForkJoinPool.commonPool() or specified executor.

Chain:
  CF<String> ──thenApply(len)──▶ CF<Integer> ──thenAccept(print)──▶ CF<Void>
```

### Example 1 — Chaining Transformations

```java
import java.util.concurrent.*;

public class Chaining {
    public static void main(String[] args) throws Exception {
        CompletableFuture<String> pipeline = CompletableFuture
            .supplyAsync(() -> "  hello world  ")      // CF<String>
            .thenApply(String::trim)                    // CF<String>
            .thenApply(String::toUpperCase)             // CF<String>
            .thenApply(s -> "Result: " + s);            // CF<String>

        System.out.println(pipeline.get()); // Result: HELLO WORLD

        // thenAccept — consume the result
        CompletableFuture<Void> sink = CompletableFuture
            .supplyAsync(() -> 42)
            .thenAccept(n -> System.out.println("Got: " + n)); // Got: 42

        sink.get();

        // thenRun — run after, no access to result
        CompletableFuture<Void> after = CompletableFuture
            .supplyAsync(() -> "ignored result")
            .thenRun(() -> System.out.println("Computation done"));

        after.get();
    }
}
```

**What this does:** `thenApply` chains transform like `Stream.map`. `thenAccept` is a terminal consumer. `thenRun` fires a cleanup/notification action without caring about the value.

### Dry Run — Chain Execution

```
CompletableFuture
  .supplyAsync(() -> "hello")    // Stage 1: thread pool → produces "hello"
  .thenApply(String::toUpperCase) // Stage 2: same or completing thread → "HELLO"
  .thenApply(s -> s + "!")        // Stage 3: → "HELLO!"
  .thenAccept(System.out::println) // Stage 4: prints "HELLO!", returns CF<Void>

Step | Stage        | Input     | Output     | Thread
  1  | supplyAsync  | —         | "hello"    | ForkJoinPool worker
  2  | thenApply    | "hello"   | "HELLO"    | completing thread (worker)
  3  | thenApply    | "HELLO"   | "HELLO!"   | completing thread
  4  | thenAccept   | "HELLO!"  | void       | completing thread
```

### Example 2 — Async vs Non-Async

```java
import java.util.concurrent.*;

public class AsyncVsSync {
    public static void main(String[] args) throws Exception {
        // thenApply — continuation runs in completing thread
        CompletableFuture<String> sync = CompletableFuture
            .supplyAsync(() -> {
                System.out.println("supply: " + Thread.currentThread().getName());
                return "value";
            })
            .thenApply(v -> {
                System.out.println("apply: " + Thread.currentThread().getName());
                return v.toUpperCase();
            });
        sync.get();
        // Both lines likely print same ForkJoinPool thread

        System.out.println("---");

        // thenApplyAsync — continuation runs in different pool thread
        CompletableFuture<String> async = CompletableFuture
            .supplyAsync(() -> {
                System.out.println("supply: " + Thread.currentThread().getName());
                return "value";
            })
            .thenApplyAsync(v -> {
                System.out.println("applyAsync: " + Thread.currentThread().getName());
                return v.toUpperCase();
            });
        async.get();
        // May print different pool threads
    }
}
```

**What this does:** `thenApplyAsync` guarantees the continuation is submitted to the thread pool, preventing stack overflow in long chains and avoiding blocking the completing thread. Prefer `Async` variants in production for long chains or I/O-heavy continuations.

---

## 3. thenCompose — Flat Mapping Futures

### What is it

`thenCompose` is like `flatMap` for streams — it chains futures that themselves return futures, avoiding `CompletableFuture<CompletableFuture<T>>`.

### Visual Diagram

```
thenApply(fn: T → CF<U>):
  CF<T> → CF<CF<U>>   ← WRONG — nested future, needs .get().get()

thenCompose(fn: T → CF<U>):
  CF<T> → CF<U>       ← CORRECT — flat, single .get()

Stream analogy:
  map    → thenApply
  flatMap → thenCompose
```

### Example 1 — thenCompose for Sequential Async Calls

```java
import java.util.concurrent.*;

public class ThenCompose {
    static CompletableFuture<String> fetchUser(int id) {
        return CompletableFuture.supplyAsync(() -> "User-" + id);
    }

    static CompletableFuture<String> fetchOrders(String user) {
        return CompletableFuture.supplyAsync(() -> "Orders for " + user);
    }

    public static void main(String[] args) throws Exception {
        // WRONG: thenApply produces CF<CF<String>>
        CompletableFuture<CompletableFuture<String>> nested =
            fetchUser(1).thenApply(user -> fetchOrders(user));
        // nested.get().get() — double get needed, ugly

        // CORRECT: thenCompose flattens to CF<String>
        CompletableFuture<String> flat =
            fetchUser(1).thenCompose(user -> fetchOrders(user));

        System.out.println(flat.get()); // Orders for User-1

        // Chain multiple async operations
        CompletableFuture<String> pipeline =
            fetchUser(42)
                .thenCompose(user -> fetchOrders(user))
                .thenCompose(orders -> CompletableFuture.supplyAsync(
                    () -> orders + " [processed]"
                ));

        System.out.println(pipeline.get()); // Orders for User-42 [processed]
    }
}
```

**What this does:** `thenCompose` enables sequential async pipelines where each step depends on the previous. Common pattern: authenticate → fetch resource → process resource, each step being an async call.

---

## 4. Combining Futures

### Visual Diagram — Combination Methods

```
thenCombine(cf2, fn):   CF<A> + CF<B> → CF<C>    — both must complete, combine results
thenAcceptBoth(cf2,fn): CF<A> + CF<B> → CF<Void> — both must complete, consume both
runAfterBoth(cf2, fn):  CF<A> + CF<B> → CF<Void> — both must complete, run action

applyToEither(cf2, fn): CF<A> | CF<A> → CF<B>    — first to complete wins
acceptEither(cf2, fn):  CF<A> | CF<A> → CF<Void> — first to complete consumed
runAfterEither(cf2, fn):CF<A> | CF<A> → CF<Void> — first to complete triggers

allOf(cf1, cf2, ...):   all must complete → CF<Void>
anyOf(cf1, cf2, ...):   first to complete → CF<Object>
```

### Example 1 — thenCombine and allOf

```java
import java.util.concurrent.*;
import java.util.*;
import java.util.stream.*;

public class Combining {
    public static void main(String[] args) throws Exception {
        // thenCombine — combine two independent results
        CompletableFuture<Integer> priceF = CompletableFuture.supplyAsync(() -> 100);
        CompletableFuture<Integer> taxF   = CompletableFuture.supplyAsync(() -> 15);

        CompletableFuture<Integer> totalF = priceF.thenCombine(taxF, Integer::sum);
        System.out.println("Total: " + totalF.get()); // Total: 115

        // allOf — wait for all, then collect results
        CompletableFuture<String> f1 = CompletableFuture.supplyAsync(() -> "Alpha");
        CompletableFuture<String> f2 = CompletableFuture.supplyAsync(() -> "Beta");
        CompletableFuture<String> f3 = CompletableFuture.supplyAsync(() -> "Gamma");

        CompletableFuture<Void> all = CompletableFuture.allOf(f1, f2, f3);
        all.get(); // wait for all

        List<String> results = Stream.of(f1, f2, f3)
            .map(CompletableFuture::join) // join() = get() without checked exception
            .collect(Collectors.toList());
        System.out.println(results); // [Alpha, Beta, Gamma]
    }
}
```

**What this does:** `thenCombine` waits for both futures independently then merges. `allOf` fires multiple computations in parallel then collects. Pattern: fan-out (start many) → fan-in (collect all).

### Example 2 — anyOf and applyToEither

```java
import java.util.concurrent.*;

public class AnyOf {
    public static void main(String[] args) throws Exception {
        // anyOf — returns first to complete (racing)
        CompletableFuture<String> fast = CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(50); } catch (InterruptedException e) {}
            return "fast";
        });
        CompletableFuture<String> slow = CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(500); } catch (InterruptedException e) {}
            return "slow";
        });

        // anyOf returns CF<Object> — need to cast
        CompletableFuture<Object> first = CompletableFuture.anyOf(fast, slow);
        System.out.println("First: " + first.get()); // First: fast

        // applyToEither — same type, apply function to winner
        CompletableFuture<String> primaryServer = CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(100); } catch (InterruptedException e) {}
            return "primary result";
        });
        CompletableFuture<String> backupServer = CompletableFuture.supplyAsync(() -> {
            try { Thread.sleep(50); } catch (InterruptedException e) {}
            return "backup result";
        });

        CompletableFuture<String> fastest = primaryServer.applyToEither(
            backupServer, result -> result.toUpperCase()
        );
        System.out.println(fastest.get()); // BACKUP RESULT
    }
}
```

**What this does:** `anyOf` implements the "racing" pattern — fire N requests to redundant services, take the first response. `applyToEither` is the typed version for same-type futures.

### Dry Run — allOf Fan-Out Pattern

```
CompletableFuture.allOf(f1, f2, f3).thenRun(collect)

Timeline:
  t=0ms:  f1 starts (FJP worker 1), f2 starts (FJP worker 2), f3 starts (FJP worker 3)
  t=10ms: f1 completes → "Alpha"
  t=20ms: f3 completes → "Gamma"
  t=30ms: f2 completes → "Beta"  ← allOf triggers now (all done)
  t=30ms: collect runs → [Alpha, Beta, Gamma]

Total time: ~30ms (max of individual times), not 60ms (sum)
This is the whole point: parallelism.
```

---

## 5. Exception Handling

### Visual Diagram — Exception Handling Methods

```
exceptionally(fn: Throwable → T):
  — if failed: apply fn, recover with T
  — if success: skip fn, pass T through
  → CF<T>

handle(fn: (T, Throwable) → U):
  — always called: T is result (or null if failed), Throwable is error (or null if success)
  → CF<U>

whenComplete(fn: (T, Throwable) → void):
  — always called (like handle but can't transform)
  — side-effect only, preserves original result/exception
  → CF<T>
```

### Example 1 — exceptionally and handle

```java
import java.util.concurrent.*;

public class ExceptionHandling {
    public static void main(String[] args) throws Exception {
        // exceptionally — recover from failure
        CompletableFuture<String> cf1 = CompletableFuture
            .<String>supplyAsync(() -> { throw new RuntimeException("fetch failed"); })
            .exceptionally(ex -> "fallback: " + ex.getMessage());

        System.out.println(cf1.get()); // fallback: fetch failed

        // Success path: exceptionally is skipped
        CompletableFuture<String> cf2 = CompletableFuture
            .supplyAsync(() -> "real result")
            .exceptionally(ex -> "fallback");

        System.out.println(cf2.get()); // real result

        // handle — always called, can transform both paths
        CompletableFuture<String> cf3 = CompletableFuture
            .<Integer>supplyAsync(() -> { throw new RuntimeException("oops"); })
            .handle((result, ex) -> {
                if (ex != null) return "Error: " + ex.getMessage();
                return "Value: " + result;
            });

        System.out.println(cf3.get()); // Error: oops

        // handle on success path
        CompletableFuture<String> cf4 = CompletableFuture
            .supplyAsync(() -> 42)
            .handle((result, ex) -> {
                if (ex != null) return "Error: " + ex.getMessage();
                return "Value: " + result;
            });

        System.out.println(cf4.get()); // Value: 42
    }
}
```

**What this does:** `exceptionally` is for recovery — provide a default value when the computation fails. `handle` is more powerful: it always runs and can inspect both success and failure, transforming either into a new type.

### Example 2 — whenComplete and Re-throwing

```java
import java.util.concurrent.*;

public class WhenComplete {
    public static void main(String[] args) throws Exception {
        // whenComplete — side effects on both success and failure
        CompletableFuture<Integer> cf = CompletableFuture
            .supplyAsync(() -> 42)
            .whenComplete((result, ex) -> {
                if (ex != null) {
                    System.out.println("Failed: " + ex.getMessage());
                } else {
                    System.out.println("Succeeded: " + result);
                }
            });

        System.out.println("Final: " + cf.get()); // Succeeded: 42 \n Final: 42

        // Chain: exceptionally → thenApply (recovery then transform)
        CompletableFuture<String> pipeline = CompletableFuture
            .<Integer>supplyAsync(() -> { throw new ArithmeticException("div/0"); })
            .exceptionally(ex -> -1)       // recover with -1
            .thenApply(n -> "Value: " + n); // transform recovered value

        System.out.println(pipeline.get()); // Value: -1
    }
}
```

**What this does:** `whenComplete` is the logging/auditing hook — doesn't change the result, just observes it. Chaining `exceptionally` then `thenApply` creates a recovery-then-transform pattern.

### Dry Run — Exception Propagation Through Chain

```
CF<Integer> chain:
  supplyAsync(() -> throw RuntimeEx)   ← fails
  .thenApply(n -> n * 2)               ← SKIPPED (stage has exception)
  .thenApply(n -> n + 1)               ← SKIPPED
  .exceptionally(ex -> 0)              ← CATCHES, returns 0
  .thenApply(n -> "result: " + n)      ← runs with 0 → "result: 0"

Key: exceptions skip thenApply/thenAccept/thenRun stages until caught by
     exceptionally/handle. Chain "short-circuits" on exception.
```

---

## 6. Timeout [Java 9+]

### Example 1 — orTimeout and completeOnTimeout

```java
import java.util.concurrent.*;

public class Timeouts {
    public static void main(String[] args) throws Exception {
        // orTimeout [Java 9+] — fail with TimeoutException if too slow
        CompletableFuture<String> cf1 = CompletableFuture
            .supplyAsync(() -> {
                try { Thread.sleep(5000); } catch (InterruptedException e) {}
                return "too slow";
            })
            .orTimeout(200, TimeUnit.MILLISECONDS);

        try {
            cf1.get();
        } catch (ExecutionException e) {
            System.out.println("Timed out: " + e.getCause().getClass().getSimpleName());
            // Timed out: TimeoutException
        }

        // completeOnTimeout [Java 9+] — provide default if too slow
        CompletableFuture<String> cf2 = CompletableFuture
            .supplyAsync(() -> {
                try { Thread.sleep(5000); } catch (InterruptedException e) {}
                return "too slow";
            })
            .completeOnTimeout("cached default", 200, TimeUnit.MILLISECONDS);

        System.out.println(cf2.get()); // cached default

        // Combine with exceptionally for full resilience
        CompletableFuture<String> resilient = CompletableFuture
            .supplyAsync(() -> "fast result")
            .completeOnTimeout("fallback", 500, TimeUnit.MILLISECONDS)
            .exceptionally(ex -> "error fallback");

        System.out.println(resilient.get()); // fast result
    }
}
```

**What this does:** `orTimeout` is fail-fast (throw on timeout). `completeOnTimeout` is fail-safe (return default on timeout). In microservices, always add timeouts to prevent slow downstream services from blocking threads indefinitely.

---

## 7. Real-World Patterns

### Example 1 — Parallel API Calls with allOf

```java
import java.util.concurrent.*;
import java.util.*;
import java.util.stream.*;

public class ParallelAPICalls {
    record UserProfile(String name) {}
    record Order(String item) {}
    record Recommendation(String product) {}

    static CompletableFuture<UserProfile> fetchProfile(int userId) {
        return CompletableFuture.supplyAsync(() -> new UserProfile("User-" + userId));
    }

    static CompletableFuture<List<Order>> fetchOrders(int userId) {
        return CompletableFuture.supplyAsync(() ->
            List.of(new Order("item1"), new Order("item2"))
        );
    }

    static CompletableFuture<List<Recommendation>> fetchRecommendations(int userId) {
        return CompletableFuture.supplyAsync(() ->
            List.of(new Recommendation("prodA"))
        );
    }

    public static void main(String[] args) throws Exception {
        int userId = 123;

        // Fire all 3 calls in parallel
        CompletableFuture<UserProfile> profileF = fetchProfile(userId);
        CompletableFuture<List<Order>> ordersF = fetchOrders(userId);
        CompletableFuture<List<Recommendation>> recsF = fetchRecommendations(userId);

        // Wait for all
        CompletableFuture.allOf(profileF, ordersF, recsF).get();

        // Collect results (join() = non-checked-exception get())
        UserProfile profile = profileF.join();
        List<Order> orders = ordersF.join();
        List<Recommendation> recs = recsF.join();

        System.out.println(profile.name() + " | " + orders.size() + " orders | "
            + recs.size() + " recommendations");
        // User-123 | 2 orders | 1 recommendations
    }
}
```

**What this does:** Classic fan-out/fan-in. All three API calls start simultaneously and complete independently. Total latency = max(individual latencies) instead of sum.

### Example 2 — Pipeline with Fallback

```java
import java.util.concurrent.*;

public class PipelineWithFallback {
    static CompletableFuture<String> fetchFromCache(String key) {
        return CompletableFuture.supplyAsync(() -> {
            if (key.equals("missing")) throw new RuntimeException("cache miss");
            return "cached: " + key;
        });
    }

    static CompletableFuture<String> fetchFromDB(String key) {
        return CompletableFuture.supplyAsync(() -> "db: " + key);
    }

    static CompletableFuture<String> getWithFallback(String key) {
        return fetchFromCache(key)
            .exceptionallyCompose(ex -> fetchFromDB(key)); // [Java 12+]
    }

    public static void main(String[] args) throws Exception {
        System.out.println(getWithFallback("user:1").get());    // cached: user:1
        System.out.println(getWithFallback("missing").get());   // db: missing
    }
}
```

**What this does:** Cache-aside pattern. Try cache first; on failure, fall back to DB. `exceptionallyCompose` [Java 12+] handles async fallback (like `thenCompose` but for the exception path). Pre-12: chain `exceptionally` + `thenCompose`.

---

## 8. get() vs join()

### Comparison

```
get():
  — throws checked: InterruptedException, ExecutionException
  — must be in try-catch or declare throws
  — preferred in main/test code where checked handling matters

join():
  — throws unchecked: CompletionException (wraps the cause)
  — no try-catch required
  — preferred inside stream pipelines and lambda chains

get(timeout, unit):
  — same as get() but throws TimeoutException after timeout
  — always prefer this over unbounded get() in production

getNow(defaultValue):
  — returns immediately: result if done, defaultValue if not done yet
  — never blocks
```

### Example 1 — get() vs join() in Streams

```java
import java.util.concurrent.*;
import java.util.*;
import java.util.stream.*;

public class GetVsJoin {
    public static void main(String[] args) {
        List<CompletableFuture<String>> futures = List.of(
            CompletableFuture.supplyAsync(() -> "A"),
            CompletableFuture.supplyAsync(() -> "B"),
            CompletableFuture.supplyAsync(() -> "C")
        );

        // join() works cleanly in stream lambdas (no checked exception)
        List<String> results = futures.stream()
            .map(CompletableFuture::join)  // join(), not get()
            .collect(Collectors.toList());

        System.out.println(results); // [A, B, C]

        // get() in stream lambda requires try-catch — ugly
        List<String> results2 = futures.stream()
            .map(f -> {
                try { return f.get(); }
                catch (Exception e) { throw new RuntimeException(e); }
            })
            .collect(Collectors.toList());
    }
}
```

**What this does:** `join()` is the idiomatic choice inside lambdas/streams because it avoids checked exception boilerplate. Use `get(timeout, unit)` for external-facing code where you want explicit timeout control.

---

## 9. CompletableFuture vs ExecutorService Future

### Comparison Table

```
Feature                     | Future<T>          | CompletableFuture<T>
----------------------------|--------------------|--------------------------
Non-blocking chain          | NO                 | YES (thenApply etc.)
Exception handling          | via get() catch    | exceptionally/handle
Combine multiple            | manual             | allOf/anyOf/thenCombine
Manual completion           | NO                 | YES (complete())
Timeout in chain            | NO                 | orTimeout [Java 9+]
Cancel                      | YES (limited)      | YES (cancel())
Reactive composition        | NO                 | YES (full pipeline)
```

---

## Quick Reference

```
Creation:
  supplyAsync(supplier)          async, returns T
  runAsync(runnable)             async, returns Void
  completedFuture(value)         already done
  failedFuture(ex)               [Java 9+] already failed

Chaining (transform):
  thenApply(T→U)                 map
  thenCompose(T→CF<U>)           flatMap (for async steps)
  thenAccept(T→void)             consume
  thenRun(→void)                 run after (no access to result)
  *Async variants                run continuation in pool

Combining:
  thenCombine(cf, (a,b)→c)       combine two CFs
  allOf(cf1,cf2,...)             wait for all → CF<Void>
  anyOf(cf1,cf2,...)             first to complete → CF<Object>
  applyToEither(cf, fn)          first of two, typed

Exception handling:
  exceptionally(ex→T)            recover from failure
  handle((T,ex)→U)               always called, transform both
  whenComplete((T,ex)→void)      side effect, preserves result

Timeout [Java 9+]:
  orTimeout(n, unit)             fail with TimeoutException
  completeOnTimeout(val, n, unit) complete with default value

Getting result:
  get()                          blocks, checked exceptions
  join()                         blocks, unchecked (stream-friendly)
  get(timeout, unit)             bounded wait
  getNow(default)                immediate, no block
```
