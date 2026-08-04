---
card: system-design
gi: 20
slug: keep-alive-connection-pooling
title: Keep-alive & connection pooling
---

## 1. What it is

**Keep-alive** is a setting that lets a single TCP connection stay open and be reused for multiple requests, instead of opening and closing a new connection for every single request. **Connection pooling** takes this further: a client (or a service) keeps a small collection — a **pool** — of already-open connections ready to reuse, so any new request can grab an idle one immediately instead of paying for a new connection setup.

## 2. Why & when

Opening a new TCP connection costs a round trip (the TCP handshake), and if TLS is involved, another round trip on top of that (the TLS handshake). Paying this cost on every single request is wasteful when the same client talks to the same server repeatedly, which is extremely common: a web page loading many resources, or a backend service calling the same database or downstream service on every user request. You bring this up whenever a design involves frequent, repeated calls between the same two components — it is a near-universal, low-cost latency win.

## 3. Core concept

**Without keep-alive:** every request pays the full connection-setup cost (TCP handshake, plus TLS handshake if applicable) before any actual data moves, then the connection closes, discarding that setup work.

**With keep-alive:** the connection is marked to stay open after a response is returned. The *next* request to the same server reuses the same already-open connection, skipping the handshake entirely.

**Connection pooling goes one step further, for a client that makes many concurrent requests (like a backend service calling a database):** instead of relying on one connection being kept alive, the client maintains a **pool** of several open connections. When a request needs to make a call, it borrows an idle connection from the pool, uses it, and returns it — rather than opening a fresh one. Key pool settings you tune in real systems:

- **Pool size (min/max):** how many connections to keep open at once. Too small, and requests queue waiting for a free connection under load. Too large, and you waste resources (and can overwhelm the downstream server) with idle connections.
- **Idle timeout:** how long an unused connection stays in the pool before being closed, to avoid holding resources that are never used again.
- **Connection validation:** checking a pooled connection is still alive before handing it out, since the other end may have silently closed it.

**Why this matters for throughput, not just single-request latency:** a database connection pool that is too small becomes a bottleneck under load — requests queue up waiting for a free connection, even if the database itself could handle more traffic.

## 4. Diagram

```
 WITHOUT keep-alive               WITH connection pooling
 req1: [handshake][data]           pool: [conn1][conn2][conn3] (idle, ready)
 req2: [handshake][data]           req1: borrow conn1 -> use -> return to pool
 req3: [handshake][data]           req2: borrow conn2 -> use -> return to pool
   (handshake cost paid EVERY      req3: borrow conn1 (reused!) -> use -> return
    single request)                  (handshake cost paid ONCE per connection,
                                       reused across many requests)
```
*Caption: pooling pays the connection-setup cost once per connection, then amortizes it across many reused requests.*

## 5. Runnable example

### Artifact: a Java simulation of a simple connection pool, comparing total setup cost with and without reuse

```java
import java.util.*;

public class ConnectionPoolSim {

    static final int HANDSHAKE_COST_MS = 50; // TCP + TLS handshake cost, simulated
    static final int REQUEST_COST_MS = 5;    // actual request/response work

    static int withoutKeepAlive(int requestCount) {
        // Every request opens a brand-new connection.
        return requestCount * (HANDSHAKE_COST_MS + REQUEST_COST_MS);
    }

    static int withPool(int requestCount, int poolSize) {
        // Each pooled connection pays its handshake cost exactly once, then is reused.
        int handshakeTotal = poolSize * HANDSHAKE_COST_MS;
        int requestTotal = requestCount * REQUEST_COST_MS;
        return handshakeTotal + requestTotal;
    }

    public static void main(String[] args) {
        int requestCount = 1000;
        int poolSize = 10;

        int noPoolTime = withoutKeepAlive(requestCount);
        int pooledTime = withPool(requestCount, poolSize);

        System.out.println("Without keep-alive, " + requestCount + " requests: " + noPoolTime + " ms");
        System.out.println("With a pool of " + poolSize + " connections: " + pooledTime + " ms");
        System.out.printf("Speedup: %.1fx%n", (double) noPoolTime / pooledTime);
    }
}
```

**How to run:** save as `ConnectionPoolSim.java`, run `java ConnectionPoolSim.java` (JDK 17+).

## 6. Walkthrough

1. `HANDSHAKE_COST_MS` and `REQUEST_COST_MS` model the fixed cost of opening a connection versus the cost of doing one request's actual work over an already-open connection.
2. `withoutKeepAlive` pays the full handshake cost on every single request, since each one opens and closes its own connection.
3. `withPool` pays the handshake cost only once per pooled connection (`poolSize` times total), because every request after that reuses an already-open connection from the pool; only the per-request work cost is paid every time.
4. `main` runs both scenarios for 1,000 requests against a pool of 10 connections, and prints the resulting speedup.
5. Output:
```
Without keep-alive, 1000 requests: 55000 ms
With a pool of 10 connections: 5500 ms
Speedup: 10.0x
```
6. The 10x speedup directly mirrors the 10x fewer handshakes paid: 1,000 handshakes without pooling versus 10 with pooling. This is the concrete number behind the standard advice to always enable keep-alive and use connection pooling for any client that talks to the same server repeatedly.

## 7. Gotchas & takeaways

> **Gotcha:** setting a connection pool's maximum size too small for the actual concurrent load. Requests then queue waiting for a free connection, adding latency that looks like a downstream slowdown but is actually a pool-sizing bug in your own client.

- Keep-alive avoids repeating the connection-setup cost across sequential requests to the same server.
- Connection pooling extends this for concurrent traffic, maintaining several ready-to-use connections instead of one.
- Size your pool to your real concurrent request volume; too small causes queuing, too large wastes resources and can overload the downstream service.
