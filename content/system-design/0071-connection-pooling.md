---
card: system-design
gi: 71
slug: connection-pooling
title: Connection pooling
---

## 1. What it is

A **connection pool** is a fixed set of already-open database connections that an application reuses across requests, instead of opening a brand-new connection for every single database operation and closing it afterward.

## 2. Why & when

Opening a database connection is expensive — it involves a network handshake, authentication, and setting up session state — expensive enough that doing it fresh for every query would dominate a request's total time. A pool pays that connection-setup cost once, up front, for a batch of connections, and every request thereafter just borrows one for the duration of its query and returns it. Use a connection pool in essentially every production application that talks to a database; it is the default in frameworks like Spring Boot (via HikariCP) rather than an optional extra.

## 3. Core concept

**Borrow and return, not open and close:** application code asks the pool for a connection (`pool.getConnection()`), uses it to run one or more queries, and then returns it to the pool (`connection.close()` — which, with pooling, does not actually close the underlying network connection, only marks it available again).

**Pool size — a fixed, bounded resource:** a pool is configured with a maximum size (say, 20 connections). If all 20 are currently borrowed and a 21st request needs one, that request waits until a connection is returned to the pool, up to a configurable timeout. This bounds how many concurrent database connections your application can ever open, protecting the database from being overwhelmed by connection count alone.

**Why unbounded connections hurt the database, not just the application:** a database server has its own limit on how many concurrent connections it can handle efficiently; each open connection consumes the database's own memory. An application opening a fresh connection per request, under load, can exhaust the database's connection limit even if each individual query is fast.

**Sizing the pool:** too small a pool means requests queue up waiting for a connection even when the database itself has spare capacity; too large a pool can overwhelm the database or waste memory on idle connections. Pool size is typically tuned based on measured concurrent query load, not guessed.

## 4. Diagram

```
WITHOUT pooling (a new connection per request):
  Request 1 -> open connection (slow handshake) -> query -> close connection
  Request 2 -> open connection (slow handshake) -> query -> close connection
  ... repeated handshake cost on every single request

WITH pooling (connections opened once, reused):
  Startup: pool opens 20 connections up front (handshake cost paid once, in a batch)
  Request 1 -> borrow connection #3 -> query -> return connection #3 to pool
  Request 2 -> borrow connection #3 (reused!) -> query -> return connection #3 to pool
  Request 21 (pool full, all 20 borrowed) -> WAITS until one is returned
```
*Caption: pooling pays the expensive connection-setup cost once per connection, then reuses each connection across many requests.*

## 5. Runnable example

**Level 1 — Basic.** A pool of pre-created "connections," borrowed and returned, compared against a naive open-per-request approach.

**Level 2 — Bounded pool, waiting.** A pool with a fixed maximum size that forces a caller to wait when it is exhausted.

**Level 3 — Cost comparison.** Count simulated "handshakes" under both approaches across many requests.

```java
// ConnectionPooling.java
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class ConnectionPooling {

    static final AtomicInteger handshakesWithoutPooling = new AtomicInteger();
    static final AtomicInteger handshakesWithPooling = new AtomicInteger();

    static class FakeConnection {
        final int id;
        FakeConnection(int id, AtomicInteger handshakeCounter) {
            this.id = id;
            handshakeCounter.incrementAndGet(); // models the expensive handshake, paid on CREATION
        }
    }

    // Level 1 (no pool): every request opens and "closes" (discards) its own connection.
    static void requestWithoutPooling(int requestNum) {
        FakeConnection conn = new FakeConnection(requestNum, handshakesWithoutPooling); // handshake EVERY time
        // ... use conn for a query ...
        // connection is discarded here, not reused
    }

    // Level 2 & 3: a bounded pool, connections created once, borrowed and returned via a BlockingQueue.
    static class ConnectionPool {
        private final BlockingQueue<FakeConnection> available;

        ConnectionPool(int size) {
            available = new ArrayBlockingQueue<>(size);
            for (int i = 0; i < size; i++) {
                available.add(new FakeConnection(i, handshakesWithPooling)); // handshake ONCE per connection, at startup
            }
        }

        FakeConnection borrow() throws InterruptedException {
            return available.take(); // waits here if the pool is currently exhausted
        }
        void giveBack(FakeConnection conn) {
            available.offer(conn); // returned to the pool, ready for the NEXT request to reuse
        }
    }

    static void requestWithPooling(ConnectionPool pool, int requestNum) throws InterruptedException {
        FakeConnection conn = pool.borrow(); // reuses an existing connection, NO new handshake
        // ... use conn for a query ...
        pool.giveBack(conn);
    }

    public static void main(String[] args) throws InterruptedException {
        int totalRequests = 50;

        for (int i = 0; i < totalRequests; i++) {
            requestWithoutPooling(i);
        }
        System.out.println("WITHOUT pooling: " + totalRequests + " requests -> " + handshakesWithoutPooling.get() + " handshakes");

        ConnectionPool pool = new ConnectionPool(5); // pool of 5 reusable connections
        for (int i = 0; i < totalRequests; i++) {
            requestWithPooling(pool, i);
        }
        System.out.println("WITH pooling (size 5): " + totalRequests + " requests -> " + handshakesWithPooling.get() + " handshakes");
    }
}
```

**How to run:** save as `ConnectionPooling.java`, then run `java ConnectionPooling.java`.

## 6. Walkthrough

1. Each call to `requestWithoutPooling` constructs a brand-new `FakeConnection`, and the `FakeConnection` constructor itself increments `handshakesWithoutPooling` — so 50 calls produce exactly 50 handshakes.
2. `new ConnectionPool(5)` constructs exactly five `FakeConnection` objects up front, incrementing `handshakesWithPooling` five times total, during pool creation — before any request has even happened.
3. Each `requestWithPooling` call borrows an existing connection via `pool.borrow()` (which blocks if none are currently available, then returns immediately once one is available) and returns it via `pool.giveBack()` — no new `FakeConnection` is ever created during these calls.
4. After 50 requests through the pool, `handshakesWithPooling` is still `5` — the same five connections were reused across all 50 requests, each one borrowed and returned many times.
5. The final comparison — 50 handshakes without pooling versus 5 with pooling — is the direct, measurable saving pooling provides, and the gap widens further as request volume grows, since the pooled cost stays fixed at the pool size while the unpooled cost scales linearly with request count.

## 7. Gotchas & takeaways

> Gotcha: forgetting to return a borrowed connection (a "connection leak," often from a missing `finally` block or `try-with-resources`) slowly shrinks the pool's available connections until every request starts blocking indefinitely, even though the database itself may be completely healthy — this is a common, hard-to-diagnose production issue.

- Connection pooling amortizes the expensive connection-setup cost across many requests, and bounds how many concurrent connections your application ever opens against the database.
- Pool size is a real capacity limit: too small causes requests to wait unnecessarily, too large risks overwhelming the database — size it from measured concurrent query load.
- Always release a borrowed connection in a `finally` block (or use try-with-resources), since a leaked connection is a slow, silent failure.
- Related concepts: [Spring Data JPA & repositories](0072-spring-data-jpa-repositories.md) (Spring Boot configures a connection pool, HikariCP, automatically behind every JPA repository).
