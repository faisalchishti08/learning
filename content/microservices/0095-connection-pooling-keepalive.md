---
card: microservices
gi: 95
slug: connection-pooling-keep-alive
title: "Connection pooling & keep-alive"
---

## 1. What it is

Establishing a new TCP connection (and, for HTTPS, completing a TLS handshake on top of it) has real, measurable cost — multiple network round trips before a single byte of actual request data is even sent. Connection pooling reuses a small set of already-established connections across many requests to the same downstream service, rather than opening and closing a fresh connection per request. HTTP keep-alive is the underlying protocol feature that makes this possible: it tells the server "don't close this connection after responding — I intend to send another request on it soon."

## 2. Why & when

A service calling the same downstream dependency repeatedly — which is the normal case in a microservices system — pays the full connection-setup cost (TCP handshake, TLS handshake) on *every single call* if connections aren't reused, even though the destination never changes between calls. This overhead is often larger than the actual request processing time for a fast downstream call, meaning most of the latency budget on every request would be spent purely on connection setup rather than useful work. Connection pooling amortizes that setup cost across many requests, keeping a bounded set of connections open and warm, ready to be reused immediately.

Configure connection pooling for any HTTP client making repeated calls to the same downstream service — essentially every [service-to-service HTTP client](0093-service-to-service-http-clients.md) in a microservices system benefits from this, and most modern HTTP client libraries (Java's `HttpClient`, Spring's `RestClient`/`WebClient` underlying connection managers) pool connections by default, though the pool's size and per-route limits are worth tuning deliberately rather than leaving at arbitrary defaults.

## 3. Core concept

Without pooling, connection setup cost is paid on every single call; with pooling, it's paid once per connection, then amortized across every request that reuses it.

```
WITHOUT pooling:  [TCP+TLS setup][request][response] [TCP+TLS setup][request][response] ...
                   ~~~~~~~~~~~~~~ repeated on EVERY call ~~~~~~~~~~~~~~

WITH pooling:      [TCP+TLS setup][request][response][request][response][request][response] ...
                   ~~~~~~~~~~~~~~ paid ONCE, then reused ~~~~~~~~~~~~~~
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without pooling each request pays a full connection setup cost; with pooling one connection is established once and reused across many subsequent requests">
  <text x="160" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Without pooling</text>
  <rect x="20" y="30" width="80" height="25" rx="3" fill="#1c2430" stroke="#79c0ff"/><text x="60" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">setup+req</text>
  <rect x="110" y="30" width="80" height="25" rx="3" fill="#1c2430" stroke="#79c0ff"/><text x="150" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">setup+req</text>
  <rect x="200" y="30" width="80" height="25" rx="3" fill="#1c2430" stroke="#79c0ff"/><text x="240" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">setup+req</text>

  <text x="480" y="18" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">With pooling</text>
  <rect x="360" y="30" width="70" height="25" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="395" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">setup</text>
  <rect x="435" y="30" width="55" height="25" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="462" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">req</text>
  <rect x="495" y="30" width="55" height="25" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="522" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">req</text>
  <rect x="555" y="30" width="55" height="25" rx="3" fill="#1c2430" stroke="#6db33f"/><text x="582" y="47" fill="#e6edf3" font-size="6.5" text-anchor="middle" font-family="sans-serif">req</text>
</svg>

Pooling pays the setup cost once, then reuses the warm connection for many subsequent requests.

## 5. Runnable example

Scenario: a client making repeated calls to a downstream service, first with a new connection established on every call, then fixed with a pooled connection reused across calls, then extended to a bounded pool serving multiple concurrent callers, demonstrating both the reuse benefit and what happens when demand exceeds the pool's size.

### Level 1 — Basic

```java
// File: NewConnectionEveryCall.java -- pay the connection SETUP cost on
// EVERY single call -- no reuse at all.
public class NewConnectionEveryCall {
    static int connectionsEstablished = 0;

    static String call(String path) throws InterruptedException {
        connectionsEstablished++;
        Thread.sleep(30); // simulated TCP+TLS handshake cost
        Thread.sleep(5);  // simulated actual request/response time
        return "response for " + path;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        for (int i = 0; i < 3; i++) {
            System.out.println(call("/orders/" + i));
        }
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Connections established: " + connectionsEstablished + ", total time: ~" + elapsed + "ms");
    }
}
```

**How to run:** `javac NewConnectionEveryCall.java && java NewConnectionEveryCall` (JDK 17+).

Expected output (elapsed time will vary slightly, always at least 105):
```
response for /orders/0
response for /orders/1
response for /orders/2
Connections established: 3, total time: ~105ms
```

### Level 2 — Intermediate

```java
// File: PooledConnection.java -- establish ONE connection, REUSE it
// across all three calls -- the setup cost is paid only once.
public class PooledConnection {
    static int connectionsEstablished = 0;
    static boolean connectionOpen = false;

    static void ensureConnection() throws InterruptedException {
        if (!connectionOpen) {
            connectionsEstablished++;
            Thread.sleep(30); // setup cost paid ONLY when no connection exists yet
            connectionOpen = true;
        }
    }

    static String call(String path) throws InterruptedException {
        ensureConnection(); // reuses the existing connection if already open
        Thread.sleep(5); // just the request/response time -- no setup cost on reuse
        return "response for " + path;
    }

    public static void main(String[] args) throws InterruptedException {
        long start = System.currentTimeMillis();
        for (int i = 0; i < 3; i++) {
            System.out.println(call("/orders/" + i));
        }
        long elapsed = System.currentTimeMillis() - start;
        System.out.println("Connections established: " + connectionsEstablished + ", total time: ~" + elapsed + "ms");
    }
}
```

**How to run:** `javac PooledConnection.java && java PooledConnection` (JDK 17+).

Expected output (elapsed time will vary slightly, always at least 45):
```
response for /orders/0
response for /orders/1
response for /orders/2
Connections established: 1, total time: ~45ms
```

Only 1 connection was established (versus Level 1's 3), and total time dropped from ~105ms to ~45ms — the setup cost was paid exactly once and amortized across all three calls.

### Level 3 — Advanced

```java
// File: BoundedPoolMultipleCallers.java -- a BOUNDED pool of 2
// connections serves MULTIPLE concurrent callers -- reuse happens across
// different threads too, and a 3rd concurrent caller must wait for a
// connection to free up rather than opening an unbounded new one.
import java.util.concurrent.*;
import java.util.concurrent.atomic.*;

public class BoundedPoolMultipleCallers {
    static AtomicInteger connectionsEstablished = new AtomicInteger(0);
    static Semaphore pool = new Semaphore(2); // bounded pool: max 2 connections

    static String call(String path) throws InterruptedException {
        boolean acquiredNewSlot = pool.tryAcquire(); // simplified: models "found or created a pooled connection"
        if (!acquiredNewSlot) {
            pool.acquire(); // no free slot -- WAIT for one to free up (bounded, not unbounded growth)
        }
        try {
            connectionsEstablished.incrementAndGet();
            Thread.sleep(20); // simulated request/response time using a pooled connection
            return "response for " + path;
        } finally {
            pool.release(); // connection returned to the pool, ready for reuse
        }
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService callers = Executors.newFixedThreadPool(3);
        for (int i = 0; i < 3; i++) {
            int id = i;
            callers.submit(() -> {
                try { System.out.println(call("/orders/" + id)); }
                catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
        }
        callers.shutdown();
        callers.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("Total connection uses across all calls: " + connectionsEstablished.get() + " (pool bounded at 2 concurrent)");
    }
}
```

**How to run:** `javac BoundedPoolMultipleCallers.java && java BoundedPoolMultipleCallers` (JDK 17+).

Expected output (line order may vary due to concurrency, but the summary count is always 3):
```
response for /orders/0
response for /orders/1
response for /orders/2
Total connection uses across all calls: 3 (pool bounded at 2 concurrent)
```

## 6. Walkthrough

1. **Level 1** — `call` increments `connectionsEstablished` and sleeps 30ms *every single time* it's invoked, simulating a fresh TCP+TLS handshake before each request's actual 5ms of work. `main` calls it three times in a loop; the printed summary shows `connectionsEstablished = 3` and a total elapsed time around 105ms (3 × (30+5)ms) — every call paid the full setup cost independently.
2. **Level 2 — reusing one connection** — `ensureConnection` only performs the 30ms setup simulation if `connectionOpen` is still `false`; once set to `true`, subsequent calls skip that cost entirely. `call` invokes `ensureConnection` before its own 5ms of simulated work. `main` runs the identical three-call loop, but the printed summary now shows `connectionsEstablished = 1` and a total time around 45ms (30ms setup once, plus 3 × 5ms) — the same three logical requests completed in less than half the time, purely by not re-paying the connection setup cost on calls 2 and 3.
3. **Level 3 — a bounded pool under concurrent load** — `pool`, a `Semaphore` with 2 permits, models a connection pool capped at 2 concurrent connections. `call` tries `pool.tryAcquire()` first (non-blocking); if no permit is immediately available, it falls back to `pool.acquire()`, which *waits* until one frees up — modeling how a real bounded pool makes a caller wait for a connection to become available, rather than opening an unbounded number of new ones.
4. **Tracing three concurrent callers against a pool of 2** — `main` submits three tasks to a 3-thread executor, each calling `call` with a different path, all launched at roughly the same time. Two of them acquire the pool's two available permits immediately and proceed with their simulated 20ms of work. The third finds both permits taken, blocks on `pool.acquire()` until one of the first two calls finishes its `finally` block (which calls `pool.release()`), and then proceeds itself. All three calls do eventually complete and print their response lines (order may vary slightly depending on which two win the initial race for permits), and `connectionsEstablished` (tracking total connection *uses*, not distinct connections) ends at `3`.
5. **What this demonstrates about pool sizing** — the bounded pool ensures that no matter how many concurrent callers arrive — three here, but the same logic would hold for hundreds — the number of simultaneously open connections to the downstream service never exceeds the configured limit (2). This protects the *downstream* service from being overwhelmed by an unbounded number of connections from just one caller, while still letting each individual caller's request eventually complete once a slot frees up — directly analogous to the [backpressure](0086-backpressure-in-synchronous-calls.md) principle applied specifically to outbound connection management.

## 7. Gotchas & takeaways

> **Gotcha:** a pooled connection can go stale — the server-side end may have silently closed it (idle timeout, server restart) without the client's pool knowing yet. A real HTTP client library validates or evicts stale pooled connections (often via a lightweight check or by simply retrying on a fresh connection if a reused one fails immediately), and pool configuration should account for this rather than assuming every pooled connection is always healthy.

- Connection setup (TCP handshake, plus TLS handshake for HTTPS) has real, often underestimated cost — reusing connections amortizes that cost across many requests instead of paying it on every single one.
- HTTP keep-alive is the protocol-level signal that makes connection reuse possible — most modern HTTP clients enable it and pool connections by default.
- A bounded pool size protects the downstream service from an unbounded number of simultaneous connections from one caller, at the cost of callers occasionally waiting for a connection to free up under high concurrency.
- Tune pool size deliberately for real production traffic patterns rather than leaving arbitrary defaults — too small a pool causes unnecessary waiting under load; too large a pool can overwhelm a downstream service or exhaust local resources.
- See [client-side timeouts](0096-client-side-timeouts-connect-read.md) for how connection-acquisition waits (like the third caller's wait in Level 3) should themselves be bounded by a timeout, rather than waiting indefinitely.
