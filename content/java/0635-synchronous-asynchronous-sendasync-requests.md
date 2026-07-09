---
card: java
gi: 635
slug: synchronous-asynchronous-sendasync-requests
title: Synchronous & asynchronous (sendAsync) requests
---

## 1. What it is

`HttpClient` provides two modes for sending requests: **synchronous** via `send()` and **asynchronous** via `sendAsync()`. `send(request, handler)` blocks the calling thread until the response is fully received and returns `HttpResponse<T>` directly. `sendAsync(request, handler)` returns immediately with a `CompletableFuture<HttpResponse<T>>` — the request is processed in a background thread pool, and the result is available via the future when it completes. Both modes use the same `HttpRequest` and `BodyHandler` types; the only difference is whether the calling thread waits. This dual API lets you choose blocking or non-blocking behaviour based on your application's threading model.

## 2. Why & when

In traditional servlet-based applications, synchronous I/O is fine — each request has its own thread, and blocking that thread for 100 ms is acceptable. In reactive or high-concurrency applications (thousands of concurrent operations), blocking threads wastes resources — async I/O lets one thread manage many inflight requests. Use `send()` for simple scripts, command-line tools, and traditional server-side code where blocking is expected. Use `sendAsync()` for GUI applications (don't freeze the UI thread), microservices that make multiple downstream calls in parallel, and any scenario where you want to fire off several HTTP requests concurrently and combine their results.

## 3. Core concept

```java
HttpClient client = HttpClient.newHttpClient();
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://httpbin.org/delay/2"))
    .GET().build();

// Synchronous: blocks until response arrives
HttpResponse<String> syncResp = client.send(request,
    HttpResponse.BodyHandlers.ofString());
System.out.println(syncResp.statusCode());  // prints after ~2 seconds

// Asynchronous: returns immediately
CompletableFuture<HttpResponse<String>> future =
    client.sendAsync(request, HttpResponse.BodyHandlers.ofString());

// Do other work while waiting...
System.out.println("Request sent, doing other things...");

// Get result (blocks if not ready)
HttpResponse<String> asyncResp = future.get();
System.out.println(asyncResp.statusCode());  // prints after ~2 seconds
```

The key difference: `send()` blocks the caller; `sendAsync()` returns a future that completes later. The underlying HTTP I/O is identical; only the threading model differs.

## 4. Diagram

<svg viewBox="0 0 560 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="send() blocks the calling thread; sendAsync() returns a CompletableFuture immediately">
  <rect x="10" y="10" width="540" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="240" height="70" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="140" y="40" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">client.send()</text>
  <text x="140" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Send ── wait ── get response</text>
  <text x="140" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Blocks calling thread</text>
  <text x="140" y="81" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Returns HttpResponse&lt;T&gt; directly</text>

  <rect x="280" y="20" width="260" height="70" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="410" y="40" fill="#3fb950" font-size="11" text-anchor="middle" font-family="monospace">client.sendAsync()</text>
  <text x="410" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Send ── return future ── (background)</text>
  <text x="410" y="68" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Returns CompletableFuture immediately</text>
  <text x="410" y="81" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Caller thread is free</text>

  <line x1="260" y1="55" x2="280" y2="55" stroke="#8b949e" stroke-width="1" stroke-dasharray="4"/>

  <text x="20" y="115" fill="#8b949e" font-size="9" font-family="sans-serif">Use send(): simple scripts, CLI tools, traditional blocking server code</text>
  <text x="20" y="133" fill="#8b949e" font-size="9" font-family="sans-serif">Use sendAsync(): GUIs (don't freeze), microservices (parallel calls), reactive apps</text>
  <text x="20" y="151" fill="#3fb950" font-size="9" font-family="sans-serif">Both use the same HttpRequest and BodyHandler — only the return type differs</text>
  <text x="20" y="169" fill="#f85149" font-size="9" font-family="sans-serif">send() throws IOException/InterruptedException directly; sendAsync() completes exceptionally</text>
</svg>

`send()` is the simpler API — call and get the result. `sendAsync()` is the scalable API — fire and handle the result later, via `thenApply`, `thenAccept`, or `join()`.

## 5. Runnable example

Scenario: building a weather dashboard that fetches data from multiple API endpoints — starting with basic sync vs async, extending to parallel async calls, and finally handling timeouts, errors, and composition.

### Level 1 — Basic

```java
// File: SyncVsAsync.java
import java.net.*;
import java.net.http.*;
import java.time.*;
import java.util.concurrent.*;

public class SyncVsAsync {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/delay/1"))
            .GET().build();

        // --- Synchronous ---
        System.out.println("=== Synchronous (send) ===");
        long start = System.currentTimeMillis();
        HttpResponse<String> syncResp = client.send(request,
            HttpResponse.BodyHandlers.ofString());
        long syncTime = System.currentTimeMillis() - start;
        System.out.println("Status: " + syncResp.statusCode());
        System.out.println("Time:   " + syncTime + " ms (thread was blocked)");

        // --- Asynchronous ---
        System.out.println("\n=== Asynchronous (sendAsync) ===");
        start = System.currentTimeMillis();
        CompletableFuture<HttpResponse<String>> future =
            client.sendAsync(request, HttpResponse.BodyHandlers.ofString());
        System.out.println("Future returned immediately (after " +
            (System.currentTimeMillis() - start) + " ms)");
        System.out.println("Main thread is free — doing other work...");

        // Now wait for result
        HttpResponse<String> asyncResp = future.get();
        long asyncTime = System.currentTimeMillis() - start;
        System.out.println("Status: " + asyncResp.statusCode());
        System.out.println("Total time: " + asyncTime + " ms");
    }
}
```

**How to run:** `java SyncVsAsync.java`

Expected output:
```
=== Synchronous (send) ===
Status: 200
Time:   ~1100 ms (thread was blocked)

=== Asynchronous (sendAsync) ===
Future returned immediately (after ~5 ms)
Main thread is free — doing other work...
Status: 200
Total time: ~1100 ms
```

The simplest comparison: `send()` blocks for the full request duration; `sendAsync()` returns a future in milliseconds and completes in the background. Total wall-clock time is similar, but the calling thread is free with `sendAsync()`.

### Level 2 — Intermediate

```java
// File: ParallelAsyncRequests.java
import java.net.*;
import java.net.http.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class ParallelAsyncRequests {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        // Three API endpoints to call
        List<String> urls = List.of(
            "https://httpbin.org/delay/1",   // 1 second
            "https://httpbin.org/delay/2",   // 2 seconds
            "https://httpbin.org/delay/1"    // 1 second
        );

        // ---- Sequential (sync) ----
        System.out.println("=== Sequential (sync) ===");
        long start = System.currentTimeMillis();
        for (String url : urls) {
            HttpRequest req = HttpRequest.newBuilder()
                .uri(URI.create(url)).GET().build();
            HttpResponse<String> resp = client.send(req,
                HttpResponse.BodyHandlers.ofString());
            System.out.println("  Done: " + url + " → " + resp.statusCode());
        }
        long seqTime = System.currentTimeMillis() - start;
        System.out.println("Total: " + seqTime + " ms (~1+2+1 = 4 sec)");

        // ---- Parallel (async) ----
        System.out.println("\n=== Parallel (async) ===");
        start = System.currentTimeMillis();

        List<CompletableFuture<HttpResponse<String>>> futures = urls.stream()
            .map(url -> HttpRequest.newBuilder().uri(URI.create(url)).GET().build())
            .map(req -> client.sendAsync(req, HttpResponse.BodyHandlers.ofString()))
            .toList();

        // Wait for all to complete
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0])).join();

        futures.forEach(f -> {
            HttpResponse<String> resp = f.join();
            System.out.println("  Done: " + resp.uri() + " → " + resp.statusCode());
        });

        long parTime = System.currentTimeMillis() - start;
        System.out.println("Total: " + parTime + " ms (~max(1,2,1) = 2 sec)");
    }
}
```

**How to run:** `java ParallelAsyncRequests.java`

Expected output:
```
=== Sequential (sync) ===
  Done: https://httpbin.org/delay/1 → 200
  Done: https://httpbin.org/delay/2 → 200
  Done: https://httpbin.org/delay/1 → 200
Total: ~4000 ms (~1+2+1 = 4 sec)

=== Parallel (async) ===
  Done: https://httpbin.org/delay/1 → 200
  Done: https://httpbin.org/delay/1 → 200
  Done: https://httpbin.org/delay/2 → 200
Total: ~2000 ms (~max(1,2,1) = 2 sec)
```

The real-world concern: parallel API calls. Sequential `send()` takes sum of durations; parallel `sendAsync()` takes max duration. For microservices that fan out to 10 downstream services, async saves up to 90% of total latency.

### Level 3 — Advanced

```java
// File: AsyncAdvanced.java
import java.net.*;
import java.net.http.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.*;

public class AsyncAdvanced {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

        System.out.println("=== Timeout handling ===");

        HttpRequest slowRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/delay/10"))  // 10 sec delay
            .timeout(Duration.ofSeconds(2))                    // 2 sec timeout
            .GET().build();

        CompletableFuture<HttpResponse<String>> timeoutFuture =
            client.sendAsync(slowRequest, HttpResponse.BodyHandlers.ofString());

        try {
            timeoutFuture.get(3, TimeUnit.SECONDS);  // wait max 3 sec
        } catch (TimeoutException e) {
            System.out.println("Request timed out (as expected)");
        }

        System.out.println("\n=== Error handling with exceptionally() ===");

        HttpRequest badUri = HttpRequest.newBuilder()
            .uri(URI.create("https://invalid.domain.zzz"))
            .GET().build();

        client.sendAsync(badUri, HttpResponse.BodyHandlers.ofString())
            .thenApply(HttpResponse::statusCode)
            .exceptionally(ex -> {
                System.out.println("Error: " + ex.getCause().getMessage());
                return -1;
            })
            .join();

        System.out.println("\n=== Composing results ===");

        // Fetch two endpoints and combine results
        HttpRequest req1 = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/get?item=first"))
            .GET().build();
        HttpRequest req2 = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/get?item=second"))
            .GET().build();

        CompletableFuture<String> combined = client.sendAsync(req1,
                HttpResponse.BodyHandlers.ofString())
            .thenCombine(
                client.sendAsync(req2, HttpResponse.BodyHandlers.ofString()),
                (resp1, resp2) -> "Combined: [" +
                    resp1.statusCode() + ", " + resp2.statusCode() + "]"
            );

        System.out.println("Combined result: " + combined.join());

        System.out.println("\n=== Custom executor ===");

        // Use a custom thread pool
        ExecutorService customPool = Executors.newFixedThreadPool(4);
        HttpClient customClient = HttpClient.newBuilder()
            .executor(customPool)
            .build();

        HttpRequest req = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/get"))
            .GET().build();

        customClient.sendAsync(req, HttpResponse.BodyHandlers.ofString())
            .thenAccept(resp -> System.out.println(
                "Custom pool response: " + resp.statusCode()))
            .join();

        customPool.shutdown();
    }
}
```

**How to run:** `java AsyncAdvanced.java`

Expected output:
```
=== Timeout handling ===
Request timed out (as expected)

=== Error handling with exceptionally() ===
Error: ...

=== Composing results ===
Combined result: [200, 200]

=== Custom executor ===
Custom pool response: 200
```

The production-flavoured hard cases: (1) **Timeouts** — set `.timeout()` on the `HttpRequest` and/or use `future.get(timeout, unit)` to bound wait time. (2) **Error handling** — `sendAsync()` failures complete the future exceptionally; use `.exceptionally()` or try-catch on `.get()`. (3) **Composition** — `thenCombine()`, `thenCompose()`, `allOf()` enable complex async workflows. (4) **Custom executor** — `HttpClient.newBuilder().executor(pool)` controls which threads handle async work, important for server environments with managed thread pools.

## 6. Walkthrough

Tracing parallel async requests: `client.sendAsync(req1, handler).thenCombine(client.sendAsync(req2, handler), combiner)`:

1. `client.sendAsync(req1, handler)` is called. The `HttpClient` submits the request to its internal (or custom) executor. A `CompletableFuture<HttpResponse<String>>` is returned immediately. The calling thread proceeds without blocking.

2. `client.sendAsync(req2, handler)` is called similarly. A second `CompletableFuture` is returned. Both requests are now in-flight concurrently.

3. `.thenCombine(future2, (resp1, resp2) -> ...)` registers a callback that fires when BOTH futures complete. The combiner lambda receives both `HttpResponse<String>` objects.

4. The calling thread now waits on `.join()` (or continues doing other work).

5. When request 1 completes: its HTTP response bytes arrive, `BodyHandlers.ofString()` decodes them, and the first future completes with an `HttpResponse<String>`. The `thenCombine` callback is NOT yet triggered (future 2 is still pending).

6. When request 2 completes: the second future completes. NOW the `thenCombine` callback fires. It extracts both status codes and returns a combined string.

7. The combined result is available via the outer `CompletableFuture`, which `.join()` unblocks on.

Data flow: two independent HTTP request/response cycles run concurrently. Their results are merged at the composition point. No thread was blocked waiting for either individual response — only the final `.join()` (if called) blocks until the combined result is ready.

## 7. Gotchas & takeaways

> `sendAsync()` returns a `CompletableFuture` that completes **on an internal or custom executor thread**. Never call `.get()` or `.join()` on the future from a UI thread without a timeout — it can freeze the UI indefinitely. Always use `.thenAccept()` or `.whenComplete()` for non-blocking result handling in GUI applications.

- `send()` and `sendAsync()` use the same underlying HTTP engine — the only difference is thread management. An async request is not faster than a sync one; it just doesn't tie up the calling thread.
- The default executor for `sendAsync()` is a cached thread pool internal to the `HttpClient`. For server applications, provide a custom `ExecutorService` via `HttpClient.newBuilder().executor(pool)` to integrate with your managed thread pool.
- `sendAsync()` + `thenApply`/`thenAccept` enables reactive-style composition without switching to a full reactive framework. For simple workflows, `CompletableFuture` chains are often sufficient.
- Error handling differs: `send()` throws checked exceptions (`IOException`, `InterruptedException`); `sendAsync()` completes the future exceptionally. Use `.exceptionally()` or try-catch on `.get()` accordingly.
- Multiple `sendAsync()` calls on the same `HttpClient` are safe and efficient — the client manages an internal connection pool and multiplexes requests over shared connections (especially with HTTP/2).
