---
card: system-design
gi: 128
slug: connection-reuse-pooling
title: Connection reuse & pooling
---

## 1. What it is

Establishing a network connection (a TCP handshake, and for HTTPS, a TLS handshake on top) has a real, fixed cost before any actual data is exchanged. **Connection reuse** means keeping a connection open and sending multiple requests over it, instead of opening a fresh one for every request. **Connection pooling** manages a set of pre-established, reusable connections (to a database, or an HTTP server), handing one out to a caller when needed and returning it to the pool afterward instead of closing it.

## 2. Why & when

Opening a new connection for every single request pays that connection-setup cost every single time, even when talking to the same server repeatedly. This overhead can dwarf the actual work being done for small, frequent requests. Reuse and pooling amortize that setup cost across many requests. Use connection reuse (like HTTP keep-alive) whenever a client makes repeated requests to the same server. Use a connection pool specifically for expensive-to-establish, stateful connections — most notably database connections — where you want to bound the maximum number of concurrent connections while still avoiding the cost of establishing a fresh one per request.

## 3. Core concept

- **Connection setup cost:** a TCP handshake takes at least one round trip; adding TLS on top adds more round trips for the cryptographic handshake — all before a single byte of your actual request is sent.
- **HTTP keep-alive:** modern HTTP defaults to keeping a TCP connection open after a response, so the *next* request to the same server can reuse it directly, skipping the handshake entirely for that request.
- **Connection pool:** a fixed-size (or bounded) set of already-open connections; a caller "borrows" one, uses it, and returns it to the pool rather than closing it — the next caller reuses that same, already-established connection.
- **Pool size as a resource limit:** the pool's maximum size also caps how many concurrent operations can happen against that resource (e.g. a database), which protects the resource from being overwhelmed by too many simultaneous connections — see [connection pooling and HikariCP defaults](0074-hikaricp-connection-pool-defaults-in-spring-boot.md) for a concrete example.
- **Borrow/return discipline:** a connection must always be returned (even if the operation using it failed), or the pool slowly runs out of available connections — a common resource leak.

## 4. Diagram

```
WITHOUT REUSE (new connection every request):

  Request 1: [TCP handshake][TLS handshake][actual request/response][close]
  Request 2: [TCP handshake][TLS handshake][actual request/response][close]
  -> handshake cost paid on EVERY request

WITH POOLING/REUSE:

  Pool: [conn1][conn2][conn3]  (established once, up front)

  Request 1: borrow conn1 -> [actual request/response] -> return conn1
  Request 2: borrow conn1 (reused!) -> [actual request/response] -> return conn1
  -> handshake cost paid ONCE per connection, amortized across many requests
```
*Caption: a pool pays the connection-setup cost once per connection, then that connection serves many requests before ever needing to be re-established.*

## 5. Runnable example

**Level 1 — Basic.** Compare total cost of establishing a new connection per request versus reusing one connection.

**Level 2 — Connection pool.** Model borrowing and returning connections from a fixed-size pool across concurrent callers.

**Level 3 — Pool exhaustion.** Show what happens when more callers need a connection than the pool has available.

```java
// ConnectionPooling.java
import java.util.*;
import java.util.concurrent.*;

public class ConnectionPooling {

    static int handshakeCostMs = 15;
    static int requestCostMs = 2;

    public static void main(String[] args) throws InterruptedException {
        // Level 1: cost of a new connection per request, vs reusing one connection for many requests.
        int numRequests = 10;
        int costWithoutReuse = numRequests * (handshakeCostMs + requestCostMs);
        int costWithReuse = handshakeCostMs + (numRequests * requestCostMs); // handshake paid ONCE
        System.out.println("without reuse: " + numRequests + " requests = " + costWithoutReuse + "ms total");
        System.out.println("with reuse: " + numRequests + " requests = " + costWithReuse + "ms total (handshake paid once)");

        // Level 2: a bounded connection pool, borrowed and returned by concurrent callers.
        BlockingQueue<String> pool = new LinkedBlockingQueue<>();
        int poolSize = 3;
        for (int i = 1; i <= poolSize; i++) pool.put("conn" + i); // pre-established connections

        ExecutorService callers = Executors.newFixedThreadPool(5);
        List<Future<String>> futures = new ArrayList<>();
        for (int i = 1; i <= 5; i++) {
            int callerId = i;
            futures.add(callers.submit(() -> {
                String conn = pool.poll(1, TimeUnit.SECONDS); // borrow (waits if none available)
                if (conn == null) return "caller-" + callerId + ": TIMED OUT waiting for a connection";
                String result = "caller-" + callerId + " used " + conn;
                pool.put(conn); // return the connection for reuse by someone else
                return result;
            }));
        }
        for (Future<String> f : futures) System.out.println(f.get());
        callers.shutdown();
        System.out.println("pool still has " + pool.size() + " connections available (all borrowed connections were returned)");

        // Level 3: pool exhaustion - callers exceed pool size AND hold connections without returning promptly.
        BlockingQueue<String> smallPool = new LinkedBlockingQueue<>();
        smallPool.put("conn1"); // pool of size 1
        String held = smallPool.poll(); // one caller borrows and does NOT return it yet
        System.out.println("pool size after one caller borrows without returning: " + smallPool.size());
        String secondBorrow = smallPool.poll(200, TimeUnit.MILLISECONDS); // a second caller tries to borrow
        System.out.println("second caller's borrow attempt result: " + (secondBorrow == null ? "TIMED OUT - pool exhausted" : secondBorrow));
    }
}
```

**How to run:** save as `ConnectionPooling.java`, then run `java ConnectionPooling.java`.

## 6. Walkthrough

1. Level 1 computes `costWithoutReuse` by multiplying the full per-request cost (handshake plus request) by `numRequests`, versus `costWithReuse`, which pays the handshake cost exactly once and only multiplies the smaller `requestCostMs` by `numRequests` — the reused total comes out far lower.
2. Level 2 pre-fills a `BlockingQueue`-based pool with 3 connection identifiers, then submits 5 concurrent callers, each of which polls a connection, "uses" it, and immediately returns it with `pool.put(conn)`.
3. Because each caller promptly returns its connection, later callers can successfully borrow one that an earlier caller already finished with — the pool never needs more than its original 3 connections to serve all 5 callers, just possibly with some callers waiting briefly.
4. The final `pool.size()` check confirms all 3 connections are back in the pool once every caller has finished — proper borrow/return discipline leaves the pool exactly as full as it started.
5. Level 3 sets up a pool of size 1, has one caller borrow it without ever calling `put` to return it, then has a second caller attempt `poll` with a timeout. Since the only connection is still held, the second `poll` call times out and returns `null`, printed as "TIMED OUT - pool exhausted" — this models exactly what happens in production when a connection leak (a borrowed connection never returned, often due to a missed `finally` block) slowly starves a pool of available connections.

## 7. Gotchas & takeaways

> Gotcha: a connection that is borrowed but never returned — commonly because an exception is thrown before the return call, and there was no `try`/`finally` (or try-with-resources) guarding it — slowly shrinks the pool's effective size over time, eventually starving every caller, even though the pool's configured maximum size never changed. Always return (or close) a pooled connection in a `finally` block.

- Connection reuse and pooling amortize the fixed cost of establishing a network connection across many requests, instead of paying it every time.
- A connection pool also serves as a concurrency limit on the resource it protects, bounding how many simultaneous connections a database or server must handle.
- Borrowed connections must always be returned, even on failure, or the pool slowly shrinks until callers start timing out waiting for one.
- Related concepts: [Connection pooling](0071-connection-pooling.md) and [HikariCP connection pool defaults in Spring Boot](0074-hikaricp-connection-pool-defaults-in-spring-boot.md) (a concrete, widely used implementation of this idea), [Batching & request coalescing](0127-batching-request-coalescing.md) (another technique for amortizing fixed per-operation overhead).
