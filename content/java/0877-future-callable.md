---
card: java
gi: 877
slug: future-callable
title: Future & Callable
---

## 1. What it is

`Callable<T>` is the result-bearing counterpart to `Runnable`: instead of `void run()`, it declares `T call() throws Exception`, meaning it can both return a value *and* throw a checked exception — something `Runnable` cannot do. `Future<T>` is the handle you get back when you submit a `Callable<T>` (or `Runnable`) to an `ExecutorService`: it represents a computation that may not have finished yet, offering `get()` (block until the result is ready, or rethrow the task's exception wrapped in `ExecutionException`), `isDone()`, and `cancel(boolean mayInterruptIfRunning)`.

## 2. Why & when

Use `Callable<T>` instead of `Runnable` whenever the asynchronous task needs to produce a result or might throw a checked exception that the caller needs to observe — computing a value, fetching data, running a query. `Future<T>` is what lets the submitting thread decide *when* to wait for that result: it can submit several tasks and only call `get()` on each when it actually needs the answer, letting them run concurrently in the meantime, rather than blocking immediately after each submission. `Future.get()` with a timeout (`get(long, TimeUnit)`) is the tool for bounding how long you're willing to wait, since an unbounded `get()` blocks forever if the task never completes; `cancel()` lets you give up on a task you no longer need, though it can only actually stop a running task if the task's code cooperates by checking `Thread.interrupted()` periodically.

## 3. Core concept

```java
ExecutorService pool = Executors.newFixedThreadPool(2);
Callable<Integer> task = () -> {
    if (Math.random() < 0.01) throw new IllegalStateException("rare failure");
    return 42;
};
Future<Integer> future = pool.submit(task);

try {
    Integer result = future.get(2, TimeUnit.SECONDS); // blocks up to 2s, or throws
} catch (ExecutionException e) {
    Throwable actualCause = e.getCause(); // the task's own thrown exception, unwrapped
} catch (TimeoutException e) {
    future.cancel(true); // give up -- interrupt if it's still running
}
```

`ExecutionException` wraps whatever the `Callable` actually threw — you must call `getCause()` to get at the real exception, since `Future.get()` itself only ever throws `ExecutionException`, `InterruptedException`, `CancellationException`, or `TimeoutException`.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Callable submitted to a pool returns a Future immediately; the caller continues other work, then later calls get, which either returns the result, times out, or rethrows the task's exception">
  <rect x="20" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">submit(Callable) -&gt; Future</text>

  <rect x="260" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">caller does OTHER work</text>

  <rect x="500" y="20" width="120" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="560" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">future.get()</text>

  <rect x="440" y="100" width="80" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="122" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">result</text>
  <rect x="530" y="100" width="80" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="570" y="122" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Execution-Exception</text>
  <rect x="350" y="100" width="80" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="390" y="122" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Timeout-Exception</text>

  <line x1="220" y1="40" x2="256" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a14)"/>
  <line x1="460" y1="40" x2="496" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a14)"/>
  <line x1="560" y1="60" x2="480" y2="98" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a14)"/>
  <line x1="560" y1="60" x2="570" y2="98" stroke="#f85149" stroke-width="1.5" marker-end="url(#a14)"/>
  <line x1="560" y1="60" x2="390" y2="98" stroke="#f0883e" stroke-width="1.5" marker-end="url(#a14)"/>
  <defs><marker id="a14" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Submitting returns immediately; `get()` is where the caller actually waits and finds out whether the task succeeded, failed, or is taking too long.*

## 5. Runnable example

Scenario: fetching a batch of "remote" prices (simulated), growing from a basic `Callable`/`Future` pair, to submitting several concurrently and collecting results, to handling both timeouts and task-thrown exceptions correctly with proper cancellation.

### Level 1 — Basic

```java
import java.util.concurrent.*;

public class BasicCallableFuture {
    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newSingleThreadExecutor();

        Callable<Integer> task = () -> {
            Thread.sleep(50);
            return 6 * 7;
        };

        Future<Integer> future = pool.submit(task);
        System.out.println("submitted -- doing other work while it runs...");
        Integer result = future.get(); // blocks until the task completes
        System.out.println("result = " + result);

        pool.shutdown();
    }
}
```

**How to run:** `java BasicCallableFuture.java` (JDK 17+).

Expected output:
```
submitted -- doing other work while it runs...
result = 42
```

`submit()` returns immediately with a `Future`; the actual blocking only happens at `future.get()`, when the caller genuinely needs the result.

### Level 2 — Intermediate

```java
import java.util.concurrent.*;
import java.util.*;

public class MultipleConcurrentFutures {
    static int fetchPrice(String symbol) throws InterruptedException {
        Thread.sleep(100); // simulate a network call
        return Math.abs(symbol.hashCode() % 1000);
    }

    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        List<String> symbols = List.of("AAPL", "GOOG", "MSFT", "AMZN");
        List<Future<Integer>> futures = new ArrayList<>();

        long start = System.currentTimeMillis();
        for (String symbol : symbols) {
            futures.add(pool.submit(() -> fetchPrice(symbol))); // all 4 submitted before any get() is called
        }

        Map<String, Integer> prices = new LinkedHashMap<>();
        for (int i = 0; i < symbols.size(); i++) {
            prices.put(symbols.get(i), futures.get(i).get()); // collect results one by one
        }

        System.out.println("prices = " + prices);
        System.out.println("elapsed ~" + (System.currentTimeMillis() - start) + "ms (ran concurrently, not 4x100ms)");
        pool.shutdown();
    }
}
```

**How to run:** `java MultipleConcurrentFutures.java`.

Expected output shape (exact price values are deterministic given the hash, elapsed time confirms concurrency):
```
prices = {AAPL=... , GOOG=..., MSFT=..., AMZN=...}
elapsed ~105ms (ran concurrently, not 4x100ms)
```

The real-world concern added: submitting all four `Callable`s *before* calling `get()` on any of them, so they run concurrently on the 4-thread pool — total elapsed time is close to one call's 100ms, not the 400ms it would take if each fetch were awaited immediately after submission.

### Level 3 — Advanced

```java
import java.util.concurrent.*;
import java.util.*;

public class TimeoutAndExceptionHandling {
    static int riskyFetch(String symbol) throws Exception {
        if (symbol.equals("BADCO")) throw new IllegalStateException("symbol not found: " + symbol);
        if (symbol.equals("SLOWCO")) Thread.sleep(5000); // deliberately too slow
        Thread.sleep(50);
        return Math.abs(symbol.hashCode() % 1000);
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        List<String> symbols = List.of("AAPL", "BADCO", "SLOWCO", "MSFT");
        List<Future<Integer>> futures = new ArrayList<>();

        for (String symbol : symbols) {
            futures.add(pool.submit(() -> riskyFetch(symbol)));
        }

        Map<String, String> outcomes = new LinkedHashMap<>();
        for (int i = 0; i < symbols.size(); i++) {
            String symbol = symbols.get(i);
            Future<Integer> f = futures.get(i);
            try {
                Integer price = f.get(500, TimeUnit.MILLISECONDS); // bounded wait per task
                outcomes.put(symbol, "price=" + price);
            } catch (ExecutionException e) {
                outcomes.put(symbol, "FAILED: " + e.getCause().getMessage()); // unwrap the real cause
            } catch (TimeoutException e) {
                f.cancel(true); // give up on the slow task -- interrupt it
                outcomes.put(symbol, "TIMED OUT, cancelled");
            }
        }

        pool.shutdownNow(); // in case a cancelled task is still lingering
        System.out.println(outcomes);
    }
}
```

**How to run:** `java TimeoutAndExceptionHandling.java`.

Expected output:
```
{AAPL=price=..., BADCO=FAILED: symbol not found: BADCO, SLOWCO=TIMED OUT, cancelled, MSFT=price=...}
```

This adds the production-flavored hard case: three distinct failure modes handled correctly in one loop — a task that threw a checked-then-wrapped exception (`BADCO`, caught via `ExecutionException.getCause()`), a task that ran too long (`SLOWCO`, caught via `TimeoutException` and explicitly cancelled so it doesn't keep consuming a pool thread), and ordinary successful completions (`AAPL`, `MSFT`) — each handled distinctly rather than one blanket `catch (Exception e)` that would obscure which failure mode actually occurred.

## 6. Walkthrough

Tracing `TimeoutAndExceptionHandling.main` processing all four symbols:

1. All four `Callable`s are submitted up front, so they begin running concurrently across the 4-thread pool — `AAPL` and `MSFT` will finish quickly (~50ms), `BADCO` will throw almost immediately, and `SLOWCO` will still be sleeping 5 seconds after everything else is long done.
2. For `AAPL`, `future.get(500, TimeUnit.MILLISECONDS)` returns the computed price well within the timeout — the `try` block's happy path stores `"price=..."`.
3. For `BADCO`, the task itself threw `IllegalStateException` inside `call()`. `Future.get()` detects the task completed abnormally and rethrows it wrapped as `ExecutionException` — the `catch (ExecutionException e)` block calls `e.getCause()` to retrieve the *original* `IllegalStateException` and reads its message, storing `"FAILED: symbol not found: BADCO"`.
4. For `SLOWCO`, `future.get(500, TimeUnit.MILLISECONDS)` blocks for the full 500ms and then throws `TimeoutException`, since the task is still sleeping (it needs 5000ms total). The `catch (TimeoutException e)` block calls `f.cancel(true)` — the `true` means "interrupt the thread if it's currently running," which will cause the sleeping task's `Thread.sleep` to throw `InterruptedException` internally and abandon the task, freeing that pool thread back up sooner rather than later.
5. For `MSFT`, processed last in the loop, enough time has already passed that its result (computed concurrently, in the background, this whole time) is likely already available — `get()` returns immediately.
6. `pool.shutdownNow()` is called instead of a plain `shutdown()`, since a cancelled-but-not-yet-fully-terminated task (`SLOWCO`) might still be unwinding from its interruption — `shutdownNow()` more aggressively attempts to stop all remaining tasks.
7. The final `outcomes` map, printed in insertion order (`LinkedHashMap`), shows each symbol's distinct, correctly-diagnosed result: a real price, a specific failure message, or an explicit timeout/cancellation notice.

## 7. Gotchas & takeaways

> **Gotcha:** `Future.get()`'s checked exceptions (`ExecutionException`, `TimeoutException`) are easy to conflate — `ExecutionException` wraps whatever the task itself threw (via `getCause()`), while `TimeoutException` means the task simply hasn't finished within your specified wait window and tells you nothing about whether it will eventually succeed or fail. Handle them as the distinct signals they are, not with a single catch-all.

- `Callable<T>` is `Runnable`'s result-bearing, checked-exception-throwing cousin — use it whenever the async task needs to hand back a value or a checked exception.
- Submit all the `Callable`s you need concurrently *before* calling `get()` on any of them — calling `submit().get()` immediately, one at a time, serializes work that could otherwise run in parallel.
- Always unwrap `ExecutionException.getCause()` to get at the task's real thrown exception — the `ExecutionException` itself is just a wrapper.
- Use `get(timeout, unit)` rather than the unbounded `get()` whenever a hung or slow task shouldn't be allowed to block the caller forever; follow a timeout with `cancel(true)` to actually stop the task rather than leaving it running unattended.
- `cancel()` only reliably stops a running task if that task's own code periodically checks for interruption (e.g., `Thread.sleep`, blocking I/O, or an explicit `Thread.currentThread().isInterrupted()` check) — cancellation is cooperative, not forceful.
