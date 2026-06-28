---
card: spring-boot
gi: 142
slug: datasource-configuration-connection-pools-hikaricp-tomcat-db
title: DataSource configuration & connection pools (HikariCP, Tomcat, DBCP2)
---

## 1. What it is

A **DataSource** is the factory that produces JDBC database connections. Spring Boot auto-configures one from `spring.datasource.*` properties. Rather than creating a raw connection each time, Spring Boot wraps it in a **connection pool** — a cache of reusable open connections. The default pool is **HikariCP**, the fastest and most widely used Java connection pool. Fallbacks in priority order are Tomcat's pool, then Apache DBCP2.

## 2. Why & when

Opening a TCP connection to a database is expensive — typically 50–200 ms. A connection pool keeps a set of pre-opened connections ready; requests borrow one, use it, and return it in milliseconds. Without pooling every SQL call would pay the full connection-setup cost.

You configure the pool when you need to tune:

- **Pool size** — minimum and maximum open connections.
- **Timeout** — how long a thread waits for a connection before throwing.
- **Validation** — a query run to check if a borrowed connection is still alive.
- **Leaks** — detect connections borrowed but not returned.

## 3. Core concept

Spring Boot selects the pool implementation by scanning the classpath:

1. **HikariCP** — `com.zaxxer.hikari.HikariDataSource` (included in `spring-boot-starter-data-jpa` and `spring-boot-starter-jdbc`).
2. **Tomcat pool** — `org.apache.tomcat.jdbc.pool.DataSource` (present when `spring-boot-starter-web` with Tomcat is used and Hikari is excluded).
3. **DBCP2** — `org.apache.commons.dbcp2.BasicDataSource` (explicit dependency).

Configure via `spring.datasource.hikari.*` (or `.tomcat.*` / `.dbcp2.*`) for pool-specific settings.

```
application.properties
  spring.datasource.url=jdbc:postgresql://localhost/mydb
  spring.datasource.username=user
  spring.datasource.password=secret
  spring.datasource.hikari.maximum-pool-size=20
         ↓
DataSourceAutoConfiguration → HikariDataSource
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">App Thread</text>
  <rect x="240" y="60" width="180" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="83" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">HikariCP Pool</text>
  <text x="330" y="100" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">conn1 (idle)</text>
  <text x="330" y="115" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">conn2 (in use)</text>
  <text x="330" y="130" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">conn3 (idle)</text>
  <rect x="500" y="80" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="110" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Database</text>
  <line x1="162" y1="105" x2="236" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ds)"/>
  <text x="199" y="99" fill="#8b949e" font-size="10" font-family="sans-serif">borrow</text>
  <line x1="422" y1="105" x2="496" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ds2)"/>
  <text x="459" y="99" fill="#8b949e" font-size="10" font-family="sans-serif">TCP conn</text>
  <defs>
    <marker id="ds" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ds2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

App threads borrow connections from HikariCP's pool; the pool maintains a fixed set of real TCP connections to the database.

## 5. Runnable example

```java
// DataSourceApp.java — Spring Boot project with spring-boot-starter-jdbc + H2 for demo
// application.properties:
//   spring.datasource.url=jdbc:h2:mem:testdb
//   spring.datasource.driver-class-name=org.h2.Driver
//   spring.datasource.hikari.maximum-pool-size=5
//   spring.datasource.hikari.minimum-idle=2
//   spring.datasource.hikari.connection-timeout=3000
//   spring.datasource.hikari.idle-timeout=30000

import com.zaxxer.hikari.HikariDataSource;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.sql.DataSource;

@SpringBootApplication
public class DataSourceApp {
    public static void main(String[] args) {
        SpringApplication.run(DataSourceApp.class, args);
    }
}

@RestController
class PoolInfoController {

    private final DataSource dataSource;
    private final JdbcTemplate jdbc;

    PoolInfoController(DataSource dataSource, JdbcTemplate jdbc) {
        this.dataSource = dataSource;
        this.jdbc = jdbc;
    }

    @GetMapping("/pool-info")
    public String poolInfo() {
        HikariDataSource hikari = (HikariDataSource) dataSource;
        return String.format(
            "Pool: %s | maxPoolSize: %d | activeConnections: %d | idleConnections: %d",
            hikari.getPoolName(),
            hikari.getMaximumPoolSize(),
            hikari.getHikariPoolMXBean().getActiveConnections(),
            hikari.getHikariPoolMXBean().getIdleConnections()
        );
    }

    @GetMapping("/query")
    public String query() {
        return "DB time: " + jdbc.queryForObject("SELECT CURRENT_TIMESTAMP", String.class);
    }
}
```

**How to run:** add `spring-boot-starter-jdbc` and `com.h2database:h2` to `pom.xml`, start the app, then:
- `curl http://localhost:8080/pool-info` → Hikari pool stats
- `curl http://localhost:8080/query` → current timestamp from H2

## 6. Walkthrough

- `spring-boot-starter-jdbc` pulls in HikariCP. `DataSourceAutoConfiguration` detects the Hikari class on the classpath and creates a `HikariDataSource` bean from `spring.datasource.*` properties.
- `spring.datasource.hikari.maximum-pool-size=5` caps the pool at 5 open connections. Under high load, threads queue waiting for a free connection up to `connection-timeout` (3 s here).
- `spring.datasource.hikari.minimum-idle=2` keeps at least 2 connections warm even when idle, avoiding cold-start latency on the first requests after quiet periods.
- `JdbcTemplate` is auto-configured alongside the `DataSource`. It uses the pool transparently — each `jdbc.queryForObject(...)` call borrows a connection, executes, and returns it automatically.
- `hikari.getHikariPoolMXBean()` exposes runtime pool metrics: active (in use), idle (available), and pending (waiting) connection counts — useful for capacity planning.
- For a real PostgreSQL database, replace the H2 URL with `jdbc:postgresql://host/db` and add the PostgreSQL JDBC driver dependency.

## 7. Gotchas & takeaways

> **Pool size ≠ more throughput.** Each connection occupies a database server thread. A pool of 100 on a 4-core database server creates severe context-switching overhead. The HikariCP wiki's formula: `pool_size = (core_count × 2) + effective_disk_spindles` — typically 10-20 is plenty.

> `spring.datasource.hikari.connection-timeout` is in **milliseconds** (default 30 000 ms = 30 s). A caller waiting longer than this gets `SQLTimeoutException`. Tune it to fail fast rather than hanging indefinitely.

- Spring Boot does not auto-configure a `DataSource` if you provide your own `DataSource` `@Bean`.
- Switch to Tomcat pool: exclude HikariCP (`<exclusions>`) and add `org.apache.tomcat:tomcat-jdbc`.
- `spring.datasource.hikari.pool-name` sets a human-readable name visible in JMX and logs.
- Hikari validates connections using `isValid()` by default; set `spring.datasource.hikari.connection-test-query=SELECT 1` for older drivers that don't implement `isValid()`.
- For multiple DataSources (multi-tenancy), declare each as a `@Bean` with `@Primary` on the default one; auto-configuration backs off.
