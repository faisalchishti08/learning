---
card: spring-framework
gi: 439
slug: testcontainers-integration-serviceconnection-via-boot
title: "Testcontainers integration (@ServiceConnection via Boot)"
---

## 1. What it is

Testcontainers is a Java library that runs real Docker containers (a real PostgreSQL, a real Kafka broker, a real Redis) for the duration of a test, giving integration tests a genuine instance of the actual technology instead of an in-memory approximation (like the H2 embedded database used throughout this section's earlier examples). Spring Boot's `@ServiceConnection` annotation (Boot 3.1+) automatically wires a started Testcontainers container's real, dynamically-assigned connection details (host, port, credentials) into Spring's configuration — no manual `@DynamicPropertySource` boilerplate required, building directly on the dynamic-property mechanism from an earlier card.

```java
@SpringBootTest
@Testcontainers
class OrderRepositoryIntegrationTest {
    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @Autowired OrderRepository orderRepository; // wired against the REAL containerized Postgres
}
```

## 2. Why & when

An embedded, in-memory database like H2 is fast and convenient, but it's never *exactly* the same database engine your production application actually uses — SQL dialect differences, specific functions, locking behavior, and edge-case type handling can all differ subtly, meaning a test passing against H2 doesn't fully guarantee the same code works against real PostgreSQL/MySQL/whatever production actually runs. Testcontainers closes that gap by running the *actual* production technology in a container, for the duration of the test — genuine confidence at the cost of needing Docker available and a slower container-startup time compared to an in-process embedded database.

`@ServiceConnection` specifically removes the boilerplate `@DynamicPropertySource` code that connecting a container to Spring configuration used to require manually — inspecting the container's type, reading its dynamically-assigned host/port, and registering the right Spring properties (`spring.datasource.url`, etc.) for that specific technology, all handled automatically based on the container's type.

Reach for Testcontainers (with `@ServiceConnection`) when:

- Your production application depends on a specific external technology (a particular database, message broker, cache) whose exact behavior matters and might differ from an in-memory substitute.
- You want integration tests that give genuine confidence your code works against the real thing, not an approximation — particularly valuable for database migrations, complex queries, or database-specific features.
- CI infrastructure has Docker available (a near-universal assumption for modern CI systems), making container startup cost an acceptable trade-off for the increased confidence.

## 3. Core concept

```
 @Container
 @ServiceConnection
 static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");
        |
        v
 @Testcontainers JUnit 5 extension starts the container
 BEFORE the Spring test context is built
        |
        v
 @ServiceConnection detects the container TYPE (PostgreSQLContainer)
 and automatically registers the matching Spring properties:
     spring.datasource.url = jdbc:postgresql://localhost:<random-port>/test
     spring.datasource.username = test
     spring.datasource.password = test
        |
        v
 Spring Boot auto-configuration builds a REAL DataSource
 pointed at the REAL, running PostgreSQL container
```

`@ServiceConnection` is essentially a pre-built, technology-aware `@DynamicPropertySource` — it knows, for a range of common Testcontainers types (Postgres, MySQL, Redis, Kafka, RabbitMQ, and more), exactly which Spring properties to set and how to derive their values from the started container.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ServiceConnection automatically wires a started Testcontainer's connection details into Spring Boot auto-configuration">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">PostgreSQLContainer</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real Docker container</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@ServiceConnection</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reads real host/port</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Boot auto-config</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">real DataSource bean</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

No manual property wiring — the container's type tells `@ServiceConnection` exactly what to configure.

## 5. Runnable example

### Level 1 — Basic

A repository test running against a genuine, containerized PostgreSQL instance, with `@ServiceConnection` handling all connection wiring automatically.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.jdbc.core.JdbcTemplate;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

public class TestcontainersBasic {

    @SpringBootApplication
    static class TestApp {}

    @SpringBootTest(classes = TestApp.class)
    @Testcontainers
    static class OrderRepositoryTest {

        @Container
        @ServiceConnection
        static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

        @Autowired
        JdbcTemplate jdbcTemplate; // wired against the REAL containerized Postgres, automatically

        @Test
        void canQueryRealPostgres() {
            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS orders (id BIGINT, status VARCHAR(20))");
            jdbcTemplate.update("INSERT INTO orders VALUES (1, 'PENDING')");

            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("Row count from REAL PostgreSQL container: " + count);
            if (count != 1) throw new AssertionError("Expected 1 row");
            System.out.println("canQueryRealPostgres -- PASS (against genuine Postgres, not an embedded substitute)");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderRepositoryTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: requires Docker running locally (or in CI); add `spring-boot-starter-test`, `spring-boot-testcontainers`, `org.testcontainers:junit-jupiter`, `org.testcontainers:postgresql`, and `spring-boot-starter-jdbc` (plus the PostgreSQL JDBC driver) to the classpath, then `java TestcontainersBasic.java`. Expect real container startup logs, followed by the test result.

`@Container` (Testcontainers' own JUnit 5 integration) starts the `PostgreSQLContainer` before the Spring context builds; `@ServiceConnection` detects it's a `PostgreSQLContainer` specifically and automatically configures `spring.datasource.*` properties pointing at that container's real, dynamically-assigned host and port — no `@DynamicPropertySource` method needed at all, in contrast to the manual pattern from the test-property-sources card.

### Level 2 — Intermediate

Two different container types (`PostgreSQLContainer` and `GenericContainer` for Redis) both wired via `@ServiceConnection` in the same test class, demonstrating that the annotation adapts its configuration strategy per container type automatically.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

public class TestcontainersIntermediate {

    @SpringBootApplication
    static class TestApp {}

    @SpringBootTest(classes = TestApp.class)
    @Testcontainers
    static class MultiContainerTest {

        @Container
        @ServiceConnection
        static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

        @Container
        @ServiceConnection(name = "redis") // explicit connection name for a technology needing it
        static GenericContainer<?> redis = new GenericContainer<>(DockerImageName.parse("redis:7-alpine"))
                .withExposedPorts(6379);

        @Autowired JdbcTemplate jdbcTemplate;      // wired against the Postgres container
        @Autowired StringRedisTemplate redisTemplate; // wired against the Redis container

        @Test
        void bothContainersAreIndependentlyWired() {
            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS orders (id BIGINT)");
            jdbcTemplate.update("INSERT INTO orders VALUES (1)");
            Integer pgCount = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);

            redisTemplate.opsForValue().set("order:1:status", "PENDING");
            String redisValue = redisTemplate.opsForValue().get("order:1:status");

            System.out.println("Postgres row count: " + pgCount + ", Redis value: " + redisValue);
            if (pgCount != 1) throw new AssertionError("Expected 1 row in Postgres");
            if (!"PENDING".equals(redisValue)) throw new AssertionError("Expected PENDING from Redis");
            System.out.println("bothContainersAreIndependentlyWired -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(MultiContainerTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: requires Docker; add the Level 1 dependencies plus `spring-boot-starter-data-redis` and `org.testcontainers:testcontainers` (generic support), then `java TestcontainersIntermediate.java`.

`@ServiceConnection` recognizes `PostgreSQLContainer` automatically (it's a well-known Testcontainers type with built-in support), while `GenericContainer` needs an explicit `name = "redis"` hint telling `@ServiceConnection` which connection-detail strategy to apply, since a generic container doesn't inherently declare what kind of service it represents. Both `JdbcTemplate` and `StringRedisTemplate` end up correctly wired to their respective real containers, entirely independently — Spring Boot's auto-configuration for each technology consumes the connection details `@ServiceConnection` registered for it.

### Level 3 — Advanced

Container reuse across multiple test classes via a shared base class and Testcontainers' singleton-container pattern, avoiding the cost of starting a fresh container per test class — a real production concern once a test suite has many container-dependent integration test classes.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.jdbc.core.JdbcTemplate;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Testcontainers;

public class TestcontainersAdvanced {

    @SpringBootApplication
    static class TestApp {}

    // Base class holding ONE shared, statically-started container -- every subclass reuses it,
    // instead of each test class paying its own container-startup cost independently.
    @SpringBootTest(classes = TestApp.class)
    @Testcontainers
    static abstract class AbstractContainerBaseTest {
        @org.testcontainers.junit.jupiter.Container
        @ServiceConnection
        static PostgreSQLContainer<?> sharedPostgres = new PostgreSQLContainer<>("postgres:16-alpine");
        // NOTE: no .withReuse(true) shown here for portability -- real projects often also
        // enable Testcontainers' reuse feature (via testcontainers.properties) to share
        // a container across SEPARATE JVM/test-suite runs, not just within one run.
    }

    static class OrderRepositoryTest extends AbstractContainerBaseTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        void ordersTableWorks() {
            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS orders (id BIGINT)");
            jdbcTemplate.update("INSERT INTO orders VALUES (1)");
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM orders", Integer.class);
            System.out.println("OrderRepositoryTest sees Postgres port: " + sharedPostgres.getMappedPort(5432));
            if (count != 1) throw new AssertionError("Expected 1 row");
            System.out.println("ordersTableWorks -- PASS");
        }
    }

    static class ProductRepositoryTest extends AbstractContainerBaseTest {
        @Autowired JdbcTemplate jdbcTemplate;

        @Test
        void productsTableWorks() {
            jdbcTemplate.execute("CREATE TABLE IF NOT EXISTS products (id BIGINT)");
            jdbcTemplate.update("INSERT INTO products VALUES (1)");
            Integer count = jdbcTemplate.queryForObject("SELECT COUNT(*) FROM products", Integer.class);
            // Same container instance/port as OrderRepositoryTest -- confirmed by comparing the mapped port.
            System.out.println("ProductRepositoryTest sees Postgres port: " + sharedPostgres.getMappedPort(5432));
            if (count != 1) throw new AssertionError("Expected 1 row");
            System.out.println("productsTableWorks -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(OrderRepositoryTest.class),
                        org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ProductRepositoryTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: requires Docker; same dependencies as Level 1, then `java TestcontainersAdvanced.java`. Expect the container startup log to appear only once, despite two test classes running.

`sharedPostgres` is declared `static` on the abstract base class, so both `OrderRepositoryTest` and `ProductRepositoryTest` reference the exact same container instance and its `@ServiceConnection`-registered connection details — Testcontainers starts it once, the first time any subclass's test lifecycle needs it, and both subclasses share it rather than each starting (and later stopping) their own separate container. Printing `sharedPostgres.getMappedPort(5432)` from both test classes and observing an identical value confirms this sharing directly.

## 6. Walkthrough

Trace `TestcontainersAdvanced.main`'s execution across both test classes:

1. **First test class initializes.** When `OrderRepositoryTest` (or whichever runs first) is prepared, `@Testcontainers`' JUnit 5 extension sees the `static` `sharedPostgres` field on the inherited `AbstractContainerBaseTest` and starts the container — real Docker container startup, taking a few real seconds.
2. **`@ServiceConnection` wires the context.** Once started, `@ServiceConnection` reads the container's actual mapped port (Docker assigns this dynamically) and registers the corresponding `spring.datasource.*` properties, exactly as in Level 1; Spring Boot's `SpringApplication` context then builds a real `DataSource`/`JdbcTemplate` against it.
3. **`OrderRepositoryTest.ordersTableWorks` runs.** It creates an `orders` table, inserts a row, and confirms the count — using the genuinely shared `sharedPostgres` container.
4. **Second test class initializes.** When `ProductRepositoryTest` is prepared, `@Testcontainers` checks the `static sharedPostgres` field again — since it's the *same static field*, inherited from the *same* base class, and it's already running (started in step 1), Testcontainers recognizes it's already active and does not start a second container.
5. **Context caching interacts here too.** Depending on whether `ProductRepositoryTest` and `OrderRepositoryTest` end up with an identical `MergedContextConfiguration` (they would, since both extend the same base class with the same `@ServiceConnection` setup), Spring's context-caching mechanism (from the earlier card) may also reuse the *same* `ApplicationContext`, not just the same container — both mechanisms (Testcontainers' static-field container reuse, and Spring's context cache) can compound to minimize redundant setup work across the suite.
6. **`ProductRepositoryTest.productsTableWorks` runs**, creating a *different* table (`products`) in the *same* shared Postgres database/container, and confirms its own row count independently — printing the same mapped port value as step 3 confirmed the container is genuinely shared, not a fresh instance.

```
OrderRepositoryTest starts first:
   @Testcontainers sees sharedPostgres not yet running -> starts it (real Docker startup)
   @ServiceConnection wires spring.datasource.* from the real container
   ordersTableWorks() -- creates 'orders' table, inserts, verifies

ProductRepositoryTest starts second:
   @Testcontainers sees sharedPostgres ALREADY running -> reuses it, no new container
   (context may also be cache-reused, since configuration is identical)
   productsTableWorks() -- creates 'products' table (SAME container/database), inserts, verifies

Both print the SAME mapped port -- confirms genuine container sharing
```

## 7. Gotchas & takeaways

> Gotcha: sharing one container across multiple test classes (Level 3's pattern) means database state genuinely persists between test classes unless each test wraps its own work in `@Transactional` rollback (from the transaction-management-in-tests card) or otherwise cleans up — two test classes sharing a container but creating tables with the same name, or relying on an assumption of a pristine database, can interfere with each other in ways a fresh-container-per-class approach would have prevented. Combine shared containers with `@Transactional` test rollback (or explicit `@Sql` cleanup) to get both fast container reuse and correct test isolation.

- Testcontainers runs the genuine production technology (a real Postgres, Redis, Kafka) in a container for the test's duration, giving stronger correctness confidence than an in-memory substitute like H2 at the cost of container-startup time and a Docker dependency.
- `@ServiceConnection` automates what used to require manual `@DynamicPropertySource` boilerplate, detecting a container's type and registering the matching Spring configuration properties automatically.
- Well-known Testcontainers types (Postgres, MySQL, Redis, Kafka, and more) are recognized automatically; a `GenericContainer` needs an explicit `name` hint telling `@ServiceConnection` which connection strategy applies.
- Sharing a container across multiple test classes (via a common base class with a `static` container field) avoids redundant startup cost, but requires deliberate test isolation (transactional rollback, explicit cleanup) since the underlying database state is genuinely shared, not reset between test classes automatically.
