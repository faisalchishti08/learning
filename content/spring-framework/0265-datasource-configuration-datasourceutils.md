---
card: spring-framework
gi: 265
slug: datasource-configuration-datasourceutils
title: DataSource configuration & DataSourceUtils
---

## 1. What it is

**`DataSource`** is the standard Java interface (`javax.sql.DataSource`) for acquiring database connections — a connection pool that lends connections to callers and returns them to the pool. Spring integrates with any `DataSource` implementation but ships helpers for the most common:

| DataSource | Source | Typical use |
|---|---|---|
| `HikariDataSource` | HikariCP | Production — fastest pool |
| `DriverManagerDataSource` | Spring JDBC | Tests / quick demos — no pooling |
| `EmbeddedDatabase` | Spring JDBC | Tests — H2/HSQL/Derby in-memory |

**`DataSourceUtils`** is Spring's low-level utility class that acquires and releases connections in a way that participates in the active **Spring transaction**. `JdbcTemplate` calls `DataSourceUtils` internally — you rarely call it directly unless you write your own JDBC code outside of `JdbcTemplate`.

## 2. Why & when

A bare `DriverManager.getConnection()` opens a new TCP connection to the database every time — expensive (~5–50 ms). A connection pool maintains open connections and lends them to threads — typical lend/return is microseconds.

`DataSourceUtils.getConnection(dataSource)` is important because:
- It returns the **transaction-bound connection** if a Spring transaction is active on the current thread — so all SQL within one `@Transactional` method shares the same connection and runs in the same transaction.
- It handles `DataSourceTransactionManager`'s bind/unbind lifecycle correctly.

Use `DataSourceUtils` when you write JDBC code that must participate in Spring transactions but cannot use `JdbcTemplate`.

## 3. Core concept

Connection pool lifecycle:

```
Application start:
  DataSource created → pool initialises N connections (min-pool-size)

Request thread:
  DataSourceUtils.getConnection(ds)
    → active transaction? yes → return bound connection
    → no → ds.getConnection() from pool

  ... execute SQL ...

  DataSourceUtils.releaseConnection(con, ds)
    → active transaction? yes → do nothing (TX owns it)
    → no → con.close() (returns to pool)

Application stop:
  HikariDataSource.close() → all connections closed
```

Key `HikariCP` settings:

| Property | Effect |
|---|---|
| `maximumPoolSize` | Max connections in pool (default 10) |
| `minimumIdle` | Min idle connections maintained |
| `connectionTimeout` | Throw `SQLTransientConnectionException` after N ms |
| `idleTimeout` | Return idle connections to pool |
| `maxLifetime` | Max lifetime of a connection (recycle before DB kills it) |

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Thread 1 -->
  <rect x="10" y="40" width="90" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="58" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Thread 1</text>

  <!-- Thread 2 -->
  <rect x="10" y="90" width="90" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="108" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Thread 2</text>

  <!-- DataSourceUtils -->
  <rect x="150" y="35" width="180" height="95" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="240" y="57" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DataSourceUtils</text>
  <line x1="160" y1="62" x2="320" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="240" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">TX active? → bound connection</text>
  <text x="240" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">No TX? → ds.getConnection()</text>
  <text x="240" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">release → return to pool or TX</text>

  <line x1="102" y1="55" x2="148" y2="70" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>
  <line x1="102" y1="105" x2="148" y2="100" stroke="#6db33f" stroke-width="1" marker-end="url(#arr)"/>

  <!-- Connection pool -->
  <rect x="390" y="35" width="200" height="95" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="490" y="57" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">HikariCP Pool</text>
  <line x1="400" y1="62" x2="580" y2="62" stroke="#8b949e" stroke-width="0.5"/>
  <text x="490" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Con1 ████  [lent to Thread 1]</text>
  <text x="490" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Con2 ████  [lent to Thread 2]</text>
  <text x="490" y="110" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">Con3 ░░░░  [idle, ready]</text>

  <line x1="332" y1="82" x2="388" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- DB -->
  <rect x="270" y="170" width="160" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="194" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Database (TCP)</text>

  <line x1="490" y1="132" x2="410" y2="170" stroke="#79c0ff" stroke-width="1" marker-end="url(#arr2)"/>
</svg>

Threads share the pool; `DataSourceUtils` ensures TX-bound connections flow correctly.

## 5. Runnable example

Scenario: a **customer registry** — configure a `DriverManagerDataSource` for tests, show `DataSourceUtils` connection binding within a transaction, and then demonstrate production-style `HikariCP` configuration.

### Level 1 — Basic

`DriverManagerDataSource` — simple, no pooling, good for tests.

```java
// DataSourceDemo.java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.datasource.DriverManagerDataSource;
import javax.sql.DataSource;

public class DataSourceDemo {

    public static void main(String[] args) {
        // DriverManagerDataSource: opens a new connection per getConnection() call
        // No pooling — fine for tests and demos, never for production
        DriverManagerDataSource ds = new DriverManagerDataSource();
        ds.setDriverClassName("org.h2.Driver");
        ds.setUrl("jdbc:h2:mem:customers;DB_CLOSE_DELAY=-1");
        ds.setUsername("sa");
        ds.setPassword("");

        JdbcTemplate jdbc = new JdbcTemplate(ds);
        jdbc.execute("CREATE TABLE customers (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(200))");

        jdbc.update("INSERT INTO customers(name,email) VALUES(?,?)", "Alice", "alice@example.com");
        jdbc.update("INSERT INTO customers(name,email) VALUES(?,?)", "Bob",   "bob@example.com");

        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM customers", Integer.class);
        System.out.println("Customers: " + count);

        // DataSource reports connection info
        try {
            var con = ds.getConnection();
            System.out.println("URL: " + con.getMetaData().getURL());
            System.out.println("DB: " + con.getMetaData().getDatabaseProductName());
            con.close();
        } catch (Exception e) { e.printStackTrace(); }
    }
}
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:. DataSourceDemo.java`

`DriverManagerDataSource` calls `DriverManager.getConnection(url, user, password)` on every `getConnection()` call — each call opens a new TCP connection to the database. For H2 in-memory mode `DB_CLOSE_DELAY=-1` keeps the database open even after all connections close (default is to drop data when the last connection closes).

---

### Level 2 — Intermediate

`DataSourceUtils` — acquiring and releasing connections manually within a transaction.

```java
// DataSourceDemo.java
import org.springframework.jdbc.datasource.*;
import org.springframework.jdbc.support.JdbcUtils;
import org.springframework.transaction.*;
import org.springframework.transaction.support.*;
import javax.sql.DataSource;
import java.sql.*;

public class DataSourceDemo {

    public static void main(String[] args) throws Exception {
        // SingleConnectionDataSource: always returns the SAME connection — useful for unit tests
        SingleConnectionDataSource ds = new SingleConnectionDataSource(
            "jdbc:h2:mem:customers;DB_CLOSE_DELAY=-1", "sa", "", true);

        ds.getConnection().createStatement().execute(
            "CREATE TABLE IF NOT EXISTS customers " +
            "(id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(200))");

        // DataSourceTransactionManager — drives DataSourceUtils' TX binding
        DataSourceTransactionManager txManager = new DataSourceTransactionManager(ds);
        TransactionTemplate txTemplate = new TransactionTemplate(txManager);

        txTemplate.execute(status -> {
            // Inside TX: DataSourceUtils returns the SAME TX-bound connection
            try {
                Connection con1 = DataSourceUtils.getConnection(ds);
                Connection con2 = DataSourceUtils.getConnection(ds);
                System.out.println("Same connection inside TX: " + (con1 == con2)); // true

                PreparedStatement ps = con1.prepareStatement(
                    "INSERT INTO customers(name,email) VALUES(?,?)");
                ps.setString(1, "Carol"); ps.setString(2, "carol@example.com");
                ps.executeUpdate();

                // releaseConnection is a no-op inside an active TX — connection stays bound
                DataSourceUtils.releaseConnection(con1, ds);
                System.out.println("Connection still open (TX active): " + !con1.isClosed());
                return null;
            } catch (SQLException e) { throw new RuntimeException(e); }
        });

        // After TX commits, connection is returned/released
        Connection postTx = DataSourceUtils.getConnection(ds);
        System.out.println("Got connection after TX: " + !postTx.isClosed());
        DataSourceUtils.releaseConnection(postTx, ds);
        ds.destroy();
    }
}
```

How to run: same classpath

`DataSourceUtils.getConnection(ds)` checks `TransactionSynchronizationManager` for a connection bound to the current thread's transaction. If a TX is active, it returns the bound connection — all JDBC code within `@Transactional` (or `TransactionTemplate`) automatically shares one connection and one transaction.

---

### Level 3 — Advanced

`HikariCP` configuration for production + pool health monitoring.

```java
// DataSourceDemo.java
import com.zaxxer.hikari.*;
import org.springframework.jdbc.core.JdbcTemplate;
import javax.sql.DataSource;
import java.util.*;
import java.util.concurrent.*;

public class DataSourceDemo {

    static DataSource buildHikariDs() {
        HikariConfig cfg = new HikariConfig();
        cfg.setJdbcUrl("jdbc:h2:mem:customers;DB_CLOSE_DELAY=-1");
        cfg.setUsername("sa");
        cfg.setPassword("");
        cfg.setDriverClassName("org.h2.Driver");

        // Pool sizing
        cfg.setMaximumPoolSize(10);         // max concurrent connections
        cfg.setMinimumIdle(2);              // keep 2 idle connections ready
        cfg.setConnectionTimeout(3000);     // throw after 3 s if no conn available
        cfg.setIdleTimeout(600_000);        // return idle conn after 10 min
        cfg.setMaxLifetime(1_800_000);      // recycle connection after 30 min

        // Validation
        cfg.setConnectionTestQuery("SELECT 1");
        cfg.setPoolName("CustomerPool");

        return new HikariDataSource(cfg);
    }

    public static void main(String[] args) throws Exception {
        HikariDataSource ds = (HikariDataSource) buildHikariDs();
        JdbcTemplate jdbc = new JdbcTemplate(ds);

        jdbc.execute("CREATE TABLE customers (id BIGINT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), email VARCHAR(200))");

        // Seed data via batch
        List<Object[]> batch = List.of(
            new Object[]{"Alice","alice@example.com"},
            new Object[]{"Bob","bob@example.com"},
            new Object[]{"Carol","carol@example.com"}
        );
        jdbc.batchUpdate("INSERT INTO customers(name,email) VALUES(?,?)", batch);

        // Pool metrics (before concurrent load)
        HikariPoolMXBean pool = ds.getHikariPoolMXBean();
        System.out.printf("Pool: total=%d  idle=%d  active=%d  waiting=%d%n",
            pool.getTotalConnections(), pool.getIdleConnections(),
            pool.getActiveConnections(), pool.getThreadsAwaitingConnection());

        // Simulate concurrent load — 5 threads each run a query
        ExecutorService exec = Executors.newFixedThreadPool(5);
        CountDownLatch latch = new CountDownLatch(5);
        for (int i = 0; i < 5; i++) {
            exec.submit(() -> {
                Integer n = jdbc.queryForObject("SELECT COUNT(*) FROM customers", Integer.class);
                System.out.println("Thread " + Thread.currentThread().getName() + " count=" + n);
                latch.countDown();
            });
        }
        latch.await(5, TimeUnit.SECONDS);
        exec.shutdown();

        System.out.printf("After load: active=%d  idle=%d%n",
            pool.getActiveConnections(), pool.getIdleConnections());

        ds.close();  // gracefully closes all connections
    }
}
```

How to run: `java -cp spring-context.jar:spring-jdbc.jar:h2.jar:hikaricp.jar:. DataSourceDemo.java`

`HikariCP` is the default pool in Spring Boot. `maximumPoolSize` is the most important setting — too small and threads wait; too large and the database is overloaded. Rule of thumb: `poolSize = (cpuCores × 2) + effectiveSpindleCount`. The pool MXBean exposes live metrics: use these in production monitoring to detect pool exhaustion.

## 6. Walkthrough

**Level 2 — `DataSourceUtils` inside `TransactionTemplate` (execution order):**

1. **`txTemplate.execute(callback)`**: calls `DataSourceTransactionManager.getTransaction()`.
2. **Transaction starts**: `txManager` calls `DataSourceUtils.getConnection(ds)` to acquire a connection, calls `con.setAutoCommit(false)`, then binds the connection to the current thread via `TransactionSynchronizationManager.bindResource(ds, conHolder)`.
3. **Inside callback — `DataSourceUtils.getConnection(ds)` call 1**: `TransactionSynchronizationManager.getResource(ds)` returns the bound `ConnectionHolder` → returns the same connection. No new connection opened.
4. **`DataSourceUtils.getConnection(ds)` call 2**: same lookup → same connection returned again. `con1 == con2` → true.
5. **INSERT executes** on that connection (auto-commit is false — row is visible only within this TX).
6. **`DataSourceUtils.releaseConnection(con1, ds)`**: checks `TransactionSynchronizationManager` → TX is active → no-op. Connection stays bound.
7. **Callback returns `null`** → `TransactionTemplate` treats as success → calls `txManager.commit(status)`.
8. **Commit**: `con.commit()` → row persisted to DB → `con.setAutoCommit(true)` → `TransactionSynchronizationManager.unbindResource(ds)` → `DataSourceUtils.releaseConnection(con, ds)` (now no TX) → connection returned to pool / closed.

```
Thread TX state:
  Before TX:  TransactionSynchronizationManager has no binding for ds
  TX starts:  binds con1
  Inside TX:  all getConnection(ds) calls → con1
  releaseConnection inside TX: no-op
  After commit: unbind + close/return con1
```

## 7. Gotchas & takeaways

> **Never call `con.close()` directly when using `DataSourceUtils`.** Always use `DataSourceUtils.releaseConnection(con, ds)` — `close()` inside a TX would return the connection to the pool prematurely, causing the TX to run on an already-closed connection.

> **`DriverManagerDataSource` in production is a common mistake.** It opens a new TCP connection per query — under load this exhausts the OS connection limit and causes connection-refused errors. Use HikariCP in any environment that will see more than one concurrent request.

> **`maxLifetime` must be shorter than the database's `wait_timeout`** (MySQL default: 8 hours). If HikariCP holds a connection longer than the DB's idle timeout, the DB closes it server-side; HikariCP then hands out a "dead" connection and the first query fails. Set `maxLifetime` to ~5 minutes less than the DB timeout.

- `DriverManagerDataSource` — no pooling; tests only.
- `HikariDataSource` — production pool; tune `maximumPoolSize` to CPU × 2 + spindles.
- `DataSourceUtils.getConnection(ds)` — returns TX-bound connection when inside a TX.
- `DataSourceUtils.releaseConnection(con, ds)` — no-op inside TX; returns to pool outside.
- Never `con.close()` directly with Spring — always `DataSourceUtils.releaseConnection`.
