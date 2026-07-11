---
card: spring-data
gi: 99
slug: connection-factories-pooling
title: "Connection factories & pooling"
---

## 1. What it is

`ConnectionFactory` is R2DBC's core abstraction for obtaining database connections — the reactive counterpart to JDBC's `DataSource` — and `r2dbc-pool` provides `ConnectionPool`, a `ConnectionFactory` implementation that reuses a bounded set of connections instead of opening a new one for every operation, mirroring what HikariCP (or similar) does for blocking JDBC connections.

```java
ConnectionFactory connectionFactory = ConnectionFactories.get("r2dbc:postgresql://localhost:5432/mydb");

ConnectionPoolConfiguration poolConfig = ConnectionPoolConfiguration.builder(connectionFactory)
    .maxSize(20)
    .initialSize(5)
    .build();
ConnectionPool pool = new ConnectionPool(poolConfig);
```

## 2. Why & when

The R2DBC reactive-overview card established that R2DBC's whole point is avoiding blocked threads waiting on I/O — but opening a brand-new database connection for every single operation is itself expensive (a real network round trip, authentication handshake, and resource allocation on the database server), reactive or not. Connection pooling closes that gap by reusing a fixed set of already-open connections, the same rationale that makes connection pooling standard practice for blocking JDBC applications too.

Reach for explicit `ConnectionPool` configuration specifically when:

- You're tuning an R2DBC application's connection behavior for production load — pool size, initial size, and idle/lifetime settings all directly affect how many concurrent database operations the application can sustain.
- You're seeing connection-exhaustion errors under load (requests waiting for a connection, or outright failures) — this is almost always a pool-sizing problem, either too small a max pool size or connections being held longer than necessary.
- You're setting up automated tests and want a small, fast, ephemeral pool (or a direct, unpooled `ConnectionFactory`) rather than a production-sized one.

## 3. Core concept

```
 Without pooling:
   every repository operation -> open NEW connection -> use it -> close it
   -- real network handshake + auth on EVERY single operation, even simple ones

 With ConnectionPool:
   pool pre-opens (or lazily opens up to) N connections
   operation -> BORROW a connection from the pool -> use it -> RETURN it to the pool (not closed)
   -- handshake/auth cost paid ONCE per connection, reused across MANY operations
```

Pooling amortizes the expensive part (opening a connection) across many operations, instead of paying that cost on every single one.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Without pooling every operation opens and closes a new connection; with a pool, connections are borrowed and returned from a reusable set">
  <text x="20" y="20" fill="#e6edf3" font-size="10" font-family="sans-serif">Without pooling</text>
  <rect x="20" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="95" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">open new connection</text>
  <rect x="190" y="30" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="265" y="52" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">use, then CLOSE</text>
  <text x="360" y="52" fill="#8b949e" font-size="8" font-family="sans-serif">-- repeated EVERY operation</text>

  <text x="20" y="105" fill="#e6edf3" font-size="10" font-family="sans-serif">With ConnectionPool</text>
  <rect x="20" y="115" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="95" y="139" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">borrow from pool</text>
  <rect x="190" y="115" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="265" y="139" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">use, then RETURN</text>
  <text x="360" y="139" fill="#8b949e" font-size="8" font-family="sans-serif">-- connection stays open, reused</text>
</svg>

Pooled connections are borrowed and returned, staying open across many operations; unpooled connections pay the full open/close cost every time.

## 5. Runnable example

The scenario: executing several database operations, evolving from an unpooled baseline paying full connection cost every time, to a pooled model reusing connections, to a bounded pool demonstrating what happens when demand exceeds pool capacity.

### Level 1 — Basic

Model the unpooled baseline: every operation opens a brand-new connection and closes it afterward.

```java
import java.util.concurrent.atomic.AtomicInteger;

class Connection {
    private static final AtomicInteger totalOpened = new AtomicInteger(0);
    final int id;
    Connection() {
        id = totalOpened.incrementAndGet();
        System.out.println("  Connection #" + id + " OPENED (simulated handshake + auth cost)");
    }
    void close() { System.out.println("  Connection #" + id + " CLOSED"); }
    static int totalOpened() { return totalOpened.get(); }
}

public class PoolingLevel1 {
    static void performOperation(String description) {
        Connection conn = new Connection(); // NEW connection every single time
        System.out.println("Executing: " + description);
        conn.close();
    }

    public static void main(String[] args) {
        performOperation("SELECT * FROM orders WHERE id = 1");
        performOperation("SELECT * FROM orders WHERE id = 2");
        performOperation("SELECT * FROM orders WHERE id = 3");
        System.out.println("Total connections opened: " + Connection.totalOpened());
    }
}
```

How to run: `java PoolingLevel1.java`

`Connection.totalOpened()` reaches `3` — one brand-new connection per operation, each paying the full simulated handshake/auth cost, even though all three operations are simple, quick queries that could easily have shared one connection.

### Level 2 — Intermediate

Introduce a simple `ConnectionPool` that reuses a small set of already-open connections, borrowing and returning them instead of opening a new one every time.

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

class Connection {
    private static final AtomicInteger totalOpened = new AtomicInteger(0);
    final int id;
    Connection() { id = totalOpened.incrementAndGet(); System.out.println("  Connection #" + id + " OPENED"); }
    static int totalOpened() { return totalOpened.get(); }
}

// Stands in for io.r2dbc.pool.ConnectionPool.
class ConnectionPool {
    private final Deque<Connection> available = new ArrayDeque<>();
    ConnectionPool(int initialSize) {
        for (int i = 0; i < initialSize; i++) available.push(new Connection()); // pre-open a few connections
    }

    Connection borrow() {
        if (available.isEmpty()) throw new IllegalStateException("Pool exhausted"); // simplified: no growth/waiting here
        Connection c = available.pop();
        System.out.println("  Borrowed connection #" + c.id + " from pool");
        return c;
    }
    void giveBack(Connection c) { available.push(c); System.out.println("  Returned connection #" + c.id + " to pool"); }
}

public class PoolingLevel2 {
    static void performOperation(ConnectionPool pool, String description) {
        Connection conn = pool.borrow(); // REUSED, not newly opened
        System.out.println("Executing: " + description);
        pool.giveBack(conn);
    }

    public static void main(String[] args) {
        ConnectionPool pool = new ConnectionPool(2); // pre-open just 2 connections

        performOperation(pool, "SELECT * FROM orders WHERE id = 1");
        performOperation(pool, "SELECT * FROM orders WHERE id = 2");
        performOperation(pool, "SELECT * FROM orders WHERE id = 3");

        System.out.println("Total connections opened: " + Connection.totalOpened()); // still just 2!
    }
}
```

How to run: `java PoolingLevel2.java`

`Connection.totalOpened()` stays at `2` even after three operations — the pool pre-opened two connections once, and each `performOperation` call borrows one, uses it, and returns it, so the third operation reuses whichever connection the first one returned, rather than paying the open cost a third time.

### Level 3 — Advanced

Demonstrate what happens under load exceeding the pool's capacity — one operation holding a connection while another tries to borrow, and how a bounded pool must handle that (here, by failing fast; a real pool typically queues the request instead).

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

class Connection {
    private static final AtomicInteger totalOpened = new AtomicInteger(0);
    final int id;
    Connection() { id = totalOpened.incrementAndGet(); }
    static int totalOpened() { return totalOpened.get(); }
}

class ConnectionPool {
    private final Deque<Connection> available = new ArrayDeque<>();
    private final int maxSize;
    private int borrowedCount = 0;

    ConnectionPool(int maxSize) {
        this.maxSize = maxSize;
        for (int i = 0; i < maxSize; i++) available.push(new Connection());
    }

    Optional<Connection> tryBorrow() {
        if (available.isEmpty()) {
            System.out.println("  Pool EXHAUSTED (all " + maxSize + " connections in use) -- cannot borrow right now");
            return Optional.empty(); // a real pool would typically QUEUE this request instead of failing immediately
        }
        Connection c = available.pop();
        borrowedCount++;
        System.out.println("  Borrowed connection #" + c.id + " (" + borrowedCount + "/" + maxSize + " in use)");
        return Optional.of(c);
    }

    void giveBack(Connection c) {
        available.push(c);
        borrowedCount--;
        System.out.println("  Returned connection #" + c.id + " (" + borrowedCount + "/" + maxSize + " in use)");
    }
}

public class PoolingLevel3 {
    public static void main(String[] args) {
        ConnectionPool pool = new ConnectionPool(2); // max pool size: 2

        // Two long-running operations BOTH borrow a connection and hold it (not yet returned).
        Connection connA = pool.tryBorrow().orElseThrow();
        Connection connB = pool.tryBorrow().orElseThrow();

        // A THIRD operation tries to borrow while both existing connections are still in use.
        Optional<Connection> connC = pool.tryBorrow();
        System.out.println("Third borrow succeeded? " + connC.isPresent());

        // Operation A finishes and returns its connection...
        pool.giveBack(connA);

        // ...NOW a fourth borrow attempt succeeds, reusing the connection A just returned.
        Connection connD = pool.tryBorrow().orElseThrow();
        System.out.println("Fourth borrow succeeded (after A returned its connection): #" + connD.id);

        System.out.println("Total connections ever opened: " + Connection.totalOpened()); // still just 2
    }
}
```

How to run: `java PoolingLevel3.java`

With a max pool size of `2`, the first two borrows succeed immediately, but the third fails outright (`connC.isPresent()` is `false`) because both connections are still held — only after `pool.giveBack(connA)` runs does a connection become available again, letting the fourth borrow succeed. `Connection.totalOpened()` stays at `2` throughout, confirming no new connections were ever created beyond the pool's original allocation — a real `r2dbc-pool` `ConnectionPool` would typically queue (rather than immediately fail) a borrow request when the pool is exhausted, up to a configurable acquire timeout, but the underlying capacity constraint is the same.

## 6. Walkthrough

Execution starts in `main` for Level 3. First, `pool = new ConnectionPool(2)` pre-opens exactly two connections (`#1` and `#2`), both initially available.

`pool.tryBorrow()` is called twice in succession: the first call pops connection `#1` off `available`, increments `borrowedCount` to `1`, and returns it as `connA`; the second call pops connection `#2`, increments `borrowedCount` to `2`, and returns it as `connB`. At this point, `available` is empty and both connections are in use.

A third `pool.tryBorrow()` is attempted for `connC`: `available.isEmpty()` is now `true`, so the method prints "Pool EXHAUSTED" and returns `Optional.empty()` — `connC.isPresent()` prints `false`, confirming no third connection was created or made available, since the pool's maximum size (`2`) has been reached and neither existing connection has been returned yet.

`pool.giveBack(connA)` is then called: connection `#1` is pushed back onto `available`, and `borrowedCount` decrements to `1` — a connection is now available again.

A fourth `pool.tryBorrow()` succeeds this time: `available` now contains connection `#1` (the one just returned), so it's popped again and returned as `connD` — the printed line confirms "Fourth borrow succeeded ... #1", showing the *same* physical connection object being reused, not a newly-opened one. `Connection.totalOpened()` is checked one final time and confirmed to still be `2`, proving that across all four borrow attempts, only the two connections created at pool construction time were ever used.

```
pool = ConnectionPool(maxSize=2)  -- opens connections #1, #2 (totalOpened=2)

borrow() -> connA=#1 (1/2 in use)
borrow() -> connB=#2 (2/2 in use)
borrow() -> EXHAUSTED, connC=empty (still 2/2 in use)

giveBack(connA)  -> #1 returned (1/2 in use)
borrow() -> connD=#1 (REUSED, 2/2 in use again)

totalOpened() still == 2  -- no new connections ever created
```

In a real Spring Data R2DBC application, `ConnectionPoolConfiguration.builder(connectionFactory).maxSize(20).initialSize(5).build()` configures exactly this behavior at production scale: up to 20 connections can be borrowed concurrently, 5 are pre-opened at startup, and a request arriving when all 20 are in use typically waits (up to a configurable timeout) for one to be returned rather than failing immediately — sized correctly, this lets a modest, fixed number of real database connections serve a much larger number of concurrent reactive operations, each holding a connection only for the brief duration it's actually needed.

## 7. Gotchas & takeaways

> Gotcha: a pool sized too small for actual concurrent demand causes operations to queue (or, as this simplified example shows, fail) waiting for a connection — but a pool sized too large can overwhelm the database server itself, since every pooled connection consumes real server-side resources (memory, connection slots) whether it's actively being used or not; pool sizing is a genuine tuning exercise, not a "bigger is always better" setting.

- `ConnectionFactory` is R2DBC's core connection abstraction, mirroring JDBC's `DataSource`; `ConnectionPool` (from `r2dbc-pool`) is a pooling `ConnectionFactory` implementation, mirroring HikariCP's role for blocking JDBC.
- Pooling amortizes the real cost of opening a database connection (network handshake, authentication) across many operations, instead of paying it on every single one.
- A pool's maximum size is a hard capacity limit — operations attempting to borrow beyond it must wait (or, in a naively-implemented pool, fail) until an in-use connection is returned.
- Pool sizing is a genuine tradeoff: too small causes contention/waiting under load; too large risks overwhelming the database server's own connection capacity — size it based on actual measured concurrency, not by default habit.
