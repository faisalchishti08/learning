---
card: system-design
gi: 74
slug: hikaricp-connection-pool-defaults-in-spring-boot
title: "HikariCP connection pool defaults in Spring Boot"
---

## 1. What it is

**HikariCP** is the connection pooling library Spring Boot auto-configures by default whenever a `DataSource` is on the classpath — you get a working, tuned connection pool with zero explicit configuration, just by adding a JDBC driver dependency and a database URL.

## 2. Why & when

Every Spring Boot application talking to a relational database needs a connection pool (covered in the previous tutorial), and Spring Boot removes the need to choose and wire one up manually: it detects HikariCP on the classpath, creates a `DataSource` bean backed by it, and applies sensible defaults automatically. You only need to reach past the defaults when you have measured a real need — a specific concurrency level, a specific timeout requirement — that the defaults do not fit.

## 3. Core concept

**Zero-config startup:** with `spring-boot-starter-data-jpa` (which pulls in HikariCP transitively) and a datasource URL in `application.properties`, Spring Boot creates a fully working, pooled `DataSource` with no further code:

```properties
spring.datasource.url=jdbc:postgresql://localhost:5432/mydb
spring.datasource.username=app
spring.datasource.password=secret
# no pool configuration needed - HikariCP defaults apply automatically
```

**Key defaults and what they control:**
- `maximum-pool-size` (default `10`): the hard cap on concurrent connections this application will ever hold open against the database.
- `minimum-idle` (defaults to the pool size): how many idle connections HikariCP tries to keep ready, rather than fully shrinking the pool during low traffic.
- `connection-timeout` (default `30000` ms): how long a request waits for a connection to become available before giving up with an exception, if the pool is fully exhausted.
- `idle-timeout` (default `600000` ms, 10 minutes): how long an idle connection above `minimum-idle` is kept before being closed, to avoid holding unused connections forever.

**Overriding a default when you need to:**

```properties
spring.datasource.hikari.maximum-pool-size=30
spring.datasource.hikari.connection-timeout=5000
```

**Why the default pool size is often smaller than expected:** a common mistake is assuming a bigger pool always means better throughput. In practice, a database can only truly execute a limited number of queries concurrently (bounded by CPU cores and disk I/O), so a pool much larger than that just means more connections waiting in line at the database itself, not real added throughput — HikariCP's relatively conservative default of `10` reflects this.

## 4. Diagram

```
application.properties (minimal, no pool settings):
  spring.datasource.url=jdbc:postgresql://localhost:5432/mydb
  spring.datasource.username=app
  spring.datasource.password=secret
        |
        v
Spring Boot auto-configuration detects: HikariCP on classpath + a DataSource needed
        |
        v
Creates a HikariDataSource bean with DEFAULTS applied automatically:
  maximum-pool-size = 10
  minimum-idle      = 10
  connection-timeout = 30000 ms
  idle-timeout       = 600000 ms
        |
        v
@Autowired DataSource / JpaRepository beans use this pool transparently
```
*Caption: Spring Boot wires a fully configured HikariCP pool from nothing but a datasource URL — explicit `hikari.*` properties only override specific defaults you actually need to change.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling HikariCP's default-driven pool sizing and timeout behavior

```java
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class HikariDefaultsSim {

    // Models the key HikariCP defaults Spring Boot applies automatically.
    static class HikariDefaults {
        int maximumPoolSize = 10;
        long connectionTimeoutMs = 30_000;
    }

    static class SimulatedPool {
        private final Semaphore permits;
        private final long timeoutMs;
        private final AtomicInteger activeConnections = new AtomicInteger();

        SimulatedPool(HikariDefaults config) {
            this.permits = new Semaphore(config.maximumPoolSize); // the hard cap: maximum-pool-size
            this.timeoutMs = config.connectionTimeoutMs;
        }

        boolean tryBorrow() throws InterruptedException {
            boolean acquired = permits.tryAcquire(timeoutMs, TimeUnit.MILLISECONDS); // connection-timeout
            if (acquired) activeConnections.incrementAndGet();
            return acquired;
        }
        void giveBack() {
            activeConnections.decrementAndGet();
            permits.release();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        HikariDefaults defaults = new HikariDefaults();
        // Use a short timeout for this demo so it does not actually wait 30 real seconds.
        defaults.connectionTimeoutMs = 200;

        System.out.println("Spring Boot default maximum-pool-size: " + defaults.maximumPoolSize);
        System.out.println("Spring Boot default connection-timeout: 30000 ms (using 200ms here for a fast demo)");

        SimulatedPool pool = new SimulatedPool(defaults);

        // Borrow up to the maximum-pool-size, all successfully.
        for (int i = 0; i < defaults.maximumPoolSize; i++) {
            boolean ok = pool.tryBorrow();
            System.out.println("connection " + i + " borrowed: " + ok);
        }

        // The pool is now fully exhausted - the NEXT borrow must wait, then time out.
        long start = System.currentTimeMillis();
        boolean extraOk = pool.tryBorrow();
        long waited = System.currentTimeMillis() - start;
        System.out.println("11th connection borrowed? " + extraOk + " (waited ~" + waited + "ms before giving up)");

        // Returning one connection frees a permit for the next caller.
        pool.giveBack();
        boolean afterReturn = pool.tryBorrow();
        System.out.println("borrow after one connection was returned: " + afterReturn);
    }
}
```

**How to run:** save as `HikariDefaultsSim.java`, run `java HikariDefaultsSim.java` (JDK 17+). A real Spring Boot application needs no code at all for this — only a `DataSource` URL in `application.properties` and the `spring-boot-starter-data-jpa` dependency; override `spring.datasource.hikari.*` properties only for values measured to need changing.

## 6. Walkthrough

1. `SimulatedPool` is constructed with a `Semaphore` initialized to `maximumPoolSize` permits — mirroring HikariCP's hard cap on concurrent connections.
2. The loop borrows exactly `10` connections (the default `maximum-pool-size`), and every one succeeds immediately, since permits are available.
3. The 11th `tryBorrow()` call finds zero permits available, so it waits up to `connectionTimeoutMs` (shortened to `200` ms here for the demo, versus the real default of `30000` ms) before giving up — the printed output confirms it returns `false` after roughly that wait, mirroring what a real application sees as a connection-acquisition timeout exception when the pool is fully exhausted.
4. `pool.giveBack()` releases one permit back to the pool, mirroring a borrowed connection being returned (`connection.close()` under pooling).
5. The final `tryBorrow()` call succeeds immediately, because a permit is now available again — confirming that returning connections promptly is what keeps the pool usable under load.

## 7. Gotchas & takeaways

> **Gotcha:** raising `maximum-pool-size` well above what the database can actually execute concurrently does not increase real throughput — it just means more connections queued at the database's own admission control instead of at HikariCP's; size the pool from measured concurrent query load against the actual database, not by guessing higher is always better.

- Spring Boot's HikariCP auto-configuration means most applications need zero explicit pool configuration to get a working, reasonably tuned connection pool.
- The defaults (`maximum-pool-size=10`, `connection-timeout=30000`) are deliberately conservative; override them only for a specific, measured need.
- Related concepts: [Connection pooling](0071-connection-pooling.md) (the general concept HikariCP implements), [Spring Data JPA & repositories](0072-spring-data-jpa-repositories.md) (the layer that borrows connections from this pool on every query).
