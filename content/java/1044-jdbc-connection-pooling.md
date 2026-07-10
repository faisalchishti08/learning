---
card: java
gi: 1044
slug: jdbc-connection-pooling
title: JDBC & connection pooling
---

## 1. What it is

**JDBC** (Java Database Connectivity) is the standard API for talking to a relational database from Java: obtain a `Connection`, create a `Statement` or `PreparedStatement`, execute SQL, and read results from a `ResultSet`. Opening a database connection is genuinely expensive — a TCP handshake, authentication, session setup on the database server — expensive enough that opening a fresh one for every single query would dominate an application's response time. A **connection pool** (HikariCP being the current de facto standard) solves this by opening a fixed number of connections once, up front, and handing them out to application code on request, taking each one back into the pool (not actually closing it) when the code calls `.close()`.

## 2. Why & when

Opening a raw JDBC connection for every database operation means paying that connection-establishment cost — often tens of milliseconds — on every single request, which for a web application handling many requests per second turns "wait for the database" into "wait for the database *and* a fresh connection setup" every time. A connection pool amortizes that cost: connections are established once, at startup (or lazily on first use), and reused across thousands of subsequent operations — calling `.close()` on a pooled connection doesn't tear down the underlying TCP connection at all, it just returns the connection object to the pool so the next caller can reuse it immediately.

Always use a connection pool in any real application talking to a relational database — the cost of connection establishment is high enough, and the pooling mechanism transparent enough (code still calls `.close()` exactly as with a raw connection), that there's essentially no reason to manage raw JDBC connections directly outside of the simplest throwaway scripts. Configure the pool's size based on the actual concurrency your database and application can sustain — too small a pool serializes requests waiting for a free connection; too large a pool can overwhelm the database with more concurrent connections than it can efficiently handle.

## 3. Core concept

```java
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

// Raw JDBC: a NEW physical connection is opened and closed for every single call --
// expensive if this method is called frequently.
String findUserName(String jdbcUrl, String id) throws Exception {
    try (Connection conn = DriverManager.getConnection(jdbcUrl);
         PreparedStatement stmt = conn.prepareStatement("SELECT name FROM users WHERE id = ?")) {
        stmt.setString(1, id);
        try (ResultSet rs = stmt.executeQuery()) {
            return rs.next() ? rs.getString("name") : null;
        }
    } // conn.close() here tears down the ACTUAL physical connection
}

// With a connection pool (HikariCP): conn.close() returns the connection to
// the POOL for reuse -- the underlying physical connection stays open.
import com.zaxxer.hikari.HikariDataSource;

HikariDataSource dataSource = new HikariDataSource(); // configured once, at startup
String findUserNamePooled(HikariDataSource dataSource, String id) throws Exception {
    try (Connection conn = dataSource.getConnection(); // borrowed from the pool, not opened fresh
         PreparedStatement stmt = conn.prepareStatement("SELECT name FROM users WHERE id = ?")) {
        stmt.setString(1, id);
        try (ResultSet rs = stmt.executeQuery()) {
            return rs.next() ? rs.getString("name") : null;
        }
    } // conn.close() here just returns it to the pool -- the physical connection stays open
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Raw JDBC opening and tearing down a new physical connection for every call versus a connection pool borrowing and returning connections from a fixed set of already-open physical connections">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Raw JDBC: open + close every call</text>
  <rect x="30" y="40" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">handshake + auth EVERY call</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Pooled: borrow + return</text>
  <rect x="360" y="40" width="90" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="405" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">conn A</text>
  <text x="405" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">conn B</text>
  <text x="405" y="95" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">conn C</text>
  <text x="405" y="30" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">pool (pre-opened)</text>
  <rect x="490" y="60" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">borrow / return</text>
  <line x1="450" y1="77" x2="490" y2="77" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Raw JDBC pays connection-setup cost on every call; a pool pays it once and reuses already-open connections.

## 5. Runnable example

Scenario: querying an in-memory H2 database repeatedly, evolving from raw per-call connections into a HikariCP-pooled data source, with measured timing showing the actual difference.

### Level 1 — Basic

```java
// File: RawJdbcBasic.java
// Requires the H2 database driver on the classpath (see Level 3's pom.xml
// snippet -- for this single-file example, download h2-2.2.224.jar and run:
// java -cp .:h2-2.2.224.jar RawJdbcBasic
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

public class RawJdbcBasic {
    static final String URL = "jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1";

    static void setup() throws Exception {
        try (Connection conn = DriverManager.getConnection(URL);
             Statement stmt = conn.createStatement()) {
            stmt.execute("CREATE TABLE users (id VARCHAR(20), name VARCHAR(50))");
            stmt.execute("INSERT INTO users VALUES ('u1', 'Ana')");
        }
    }

    static String findUserName(String id) throws Exception {
        // A NEW raw connection opened (and torn down) for EVERY call.
        try (Connection conn = DriverManager.getConnection(URL);
             PreparedStatement stmt = conn.prepareStatement("SELECT name FROM users WHERE id = ?")) {
            stmt.setString(1, id);
            try (ResultSet rs = stmt.executeQuery()) {
                return rs.next() ? rs.getString("name") : null;
            }
        }
    }

    public static void main(String[] args) throws Exception {
        setup();
        long start = System.nanoTime();
        for (int i = 0; i < 100; i++) {
            findUserName("u1");
        }
        long elapsed = (System.nanoTime() - start) / 1_000_000;
        System.out.println("100 raw-connection lookups took " + elapsed + " ms");
    }
}
```

**How to run:** download `h2-2.2.224.jar`, then `javac -cp h2-2.2.224.jar RawJdbcBasic.java && java -cp .:h2-2.2.224.jar RawJdbcBasic` (JDK 17+; on Windows use `;` instead of `:` in the classpath).

Expected output (exact timing varies by machine, but is noticeably slower than the pooled version below):
```
100 raw-connection lookups took <some number, generally the slowest of the three levels> ms
```

Every one of the 100 lookups opens and tears down a brand-new connection — for a real network-based database (unlike this in-memory H2 example, which is unusually fast to "connect" to), this cost would be dramatically higher and would dominate total response time under any real load.

### Level 2 — Intermediate

```java
// File: PooledBasic.java
// Requires HikariCP and the H2 driver on the classpath.
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;

public class PooledBasic {
    public static void main(String[] args) throws Exception {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1");
        config.setMaximumPoolSize(5); // up to 5 connections kept ready in the pool

        try (HikariDataSource dataSource = new HikariDataSource(config)) {
            try (Connection conn = dataSource.getConnection();
                 Statement stmt = conn.createStatement()) {
                stmt.execute("CREATE TABLE users (id VARCHAR(20), name VARCHAR(50))");
                stmt.execute("INSERT INTO users VALUES ('u1', 'Ana')");
            }

            long start = System.nanoTime();
            for (int i = 0; i < 100; i++) {
                try (Connection conn = dataSource.getConnection(); // BORROWED from the pool, not opened fresh
                     PreparedStatement stmt = conn.prepareStatement("SELECT name FROM users WHERE id = ?")) {
                    stmt.setString(1, "u1");
                    try (ResultSet rs = stmt.executeQuery()) {
                        rs.next();
                    }
                } // conn.close() here returns it to the pool -- doesn't tear it down
            }
            long elapsed = (System.nanoTime() - start) / 1_000_000;
            System.out.println("100 pooled lookups took " + elapsed + " ms");
        }
    }
}
```

**How to run:** with HikariCP and H2 JARs on the classpath, `javac -cp HikariCP-5.1.0.jar:h2-2.2.224.jar PooledBasic.java && java -cp .:HikariCP-5.1.0.jar:h2-2.2.224.jar:slf4j-api-2.0.13.jar PooledBasic` (JDK 17+; HikariCP requires an SLF4J API JAR on the classpath even without a logging backend configured).

Expected output (noticeably faster than Level 1, especially pronounced against a real network database rather than in-memory H2):
```
100 pooled lookups took <some number, generally faster than Level 1> ms
```

The real-world concern added: `dataSource.getConnection()` borrows an already-established connection from the pool rather than opening a fresh one — `conn.close()` returns it for the next iteration to reuse, meaning the actual expensive connection-establishment work happens only up to `maximumPoolSize` times total, not once per loop iteration.

### Level 3 — Advanced

```xml
<!-- Minimal pom.xml for the pooled example -->
<dependencies>
    <dependency>
        <groupId>com.zaxxer</groupId>
        <artifactId>HikariCP</artifactId>
        <version>5.1.0</version>
    </dependency>
    <dependency>
        <groupId>com.h2database</groupId>
        <artifactId>h2</artifactId>
        <version>2.2.224</version>
        <scope>runtime</scope>
    </dependency>
</dependencies>
```

```java
// File: src/main/java/PooledAdvanced.java
import com.zaxxer.hikari.HikariConfig;
import com.zaxxer.hikari.HikariDataSource;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class PooledAdvanced {
    public static void main(String[] args) throws Exception {
        HikariConfig config = new HikariConfig();
        config.setJdbcUrl("jdbc:h2:mem:testdb;DB_CLOSE_DELAY=-1");
        // A DELIBERATELY small pool -- only 2 connections -- to observe what
        // happens when concurrent demand exceeds the pool's capacity.
        config.setMaximumPoolSize(2);
        config.setConnectionTimeout(3000); // fail fast if no connection frees up in time

        try (HikariDataSource dataSource = new HikariDataSource(config)) {
            try (Connection conn = dataSource.getConnection();
                 Statement stmt = conn.createStatement()) {
                stmt.execute("CREATE TABLE users (id VARCHAR(20), name VARCHAR(50))");
                stmt.execute("INSERT INTO users VALUES ('u1', 'Ana')");
            }

            // Simulate 5 CONCURRENT requests competing for only 2 pooled connections.
            ExecutorService executor = Executors.newFixedThreadPool(5);
            for (int i = 0; i < 5; i++) {
                int requestId = i;
                executor.submit(() -> {
                    try (Connection conn = dataSource.getConnection();
                         PreparedStatement stmt = conn.prepareStatement("SELECT name FROM users WHERE id = ?")) {
                        stmt.setString(1, "u1");
                        try (ResultSet rs = stmt.executeQuery()) {
                            rs.next();
                            Thread.sleep(200); // hold the connection briefly, simulating real work
                            System.out.println("request " + requestId + " completed, active connections: "
                                + dataSource.getHikariPoolMXBean().getActiveConnections());
                        }
                    } catch (SQLException | InterruptedException e) {
                        System.out.println("request " + requestId + " failed: " + e.getMessage());
                    }
                });
            }
            executor.shutdown();
            executor.awaitTermination(10, TimeUnit.SECONDS);
        }
    }
}
```

**How to run:** with the dependencies above, `mvn compile exec:java -Dexec.mainClass=PooledAdvanced`.

Expected output (exact request completion order may vary, but never more than 2 requests report active simultaneously):
```
request 0 completed, active connections: <at most 2 at any point in time>
request 1 completed, active connections: <at most 2 at any point in time>
request 2 completed, active connections: <at most 2 at any point in time>
request 3 completed, active connections: <at most 2 at any point in time>
request 4 completed, active connections: <at most 2 at any point in time>
```

The production-flavored hard case: with `maximumPoolSize` deliberately set to `2` and 5 concurrent requests submitted, HikariCP naturally serializes access — only 2 requests can hold a connection at any instant, and the remaining 3 wait (up to `connectionTimeout`) until one is returned to the pool. This demonstrates the real tradeoff of pool sizing: too small, and concurrent demand queues up waiting for a free connection.

## 6. Walkthrough

Tracing what happens as the 5 submitted tasks compete for the pool of 2 connections:

1. `dataSource.getConnection()` is called by the first two submitted tasks (say, request 0 and request 1, though actual scheduling order isn't guaranteed) — since the pool has 2 available connections and neither is currently borrowed, both calls succeed immediately, each receiving one of the pool's two physical connections.
2. A third task (say, request 2) calls `dataSource.getConnection()` while both pooled connections are still held by requests 0 and 1 — since `maximumPoolSize` is `2` and neither existing connection has been returned yet, this call **blocks**, waiting for one to become available, up to the configured `connectionTimeout` of 3000ms.
3. Request 0 finishes its query, executes `Thread.sleep(200)` (simulating real work being done while holding the connection), then reaches the end of its `try-with-resources` block — `conn.close()` runs, which (because `conn` is a pooled connection, not a raw JDBC one) returns it to the pool rather than tearing it down.
4. The moment that connection is returned, the blocked `getConnection()` call from step 2 (request 2) unblocks and receives that now-available connection, proceeding with its own query.
5. This same borrow-block-return cycle repeats for the remaining requests (3 and 4), each waiting for whichever of the two connections is returned soonest, until all 5 requests have eventually completed.
6. At any given instant during this whole process, `dataSource.getHikariPoolMXBean().getActiveConnections()` never reports more than `2` — confirming the pool genuinely enforced its configured maximum size, serializing excess concurrent demand rather than allowing more physical connections to be opened than configured.

## 7. Gotchas & takeaways

> **Gotcha:** forgetting to call `.close()` on a pooled connection (or letting an exception skip it, without using `try-with-resources`) doesn't just leak that one connection for the current request — it permanently shrinks the pool's effective capacity for every future request, since that connection is never returned and the pool has no way to reclaim it automatically until the pool itself times it out or the application restarts.

- Opening a raw JDBC connection is expensive; a connection pool amortizes that cost by opening a fixed set of connections once and reusing them across many subsequent operations.
- Calling `.close()` on a pooled connection returns it to the pool for reuse — it does not tear down the underlying physical database connection, unlike closing a raw JDBC connection.
- HikariCP is the current de facto standard connection pool for Java, known for its performance and being the default choice in frameworks like Spring Boot.
- Pool size is a genuine tradeoff: too small serializes concurrent requests waiting for a free connection (as demonstrated above); too large risks overwhelming the database server with more concurrent connections than it can handle efficiently.
- Always use `try-with-resources` (or equivalent guaranteed cleanup) for pooled connections — a connection that's never returned to the pool permanently reduces its effective capacity, a subtle and cumulative resource leak.
- See [JPA / Hibernate ORM](1045-jpa-hibernate-orm.md) for the higher-level abstraction typically built on top of a pooled `DataSource` in real applications, sparing most application code from writing raw JDBC directly.
