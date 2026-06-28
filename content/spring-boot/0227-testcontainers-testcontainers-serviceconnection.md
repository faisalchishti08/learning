---
card: spring-boot
gi: 227
slug: testcontainers-testcontainers-serviceconnection
title: "Testcontainers (@Testcontainers, @ServiceConnection)"
---

## 1. What it is

Testcontainers is a Java library that starts real Docker containers (PostgreSQL, Redis, Kafka, …) for the duration of your tests. Spring Boot 3.1 added `@ServiceConnection`: annotate a container field and Boot automatically wires the container's connection details (host, port, credentials) into your application context — no `@DynamicPropertySource` boilerplate required.

## 2. Why & when

In-memory databases (H2) and mocks hide real SQL dialect bugs, driver quirks, and migration failures. Use Testcontainers when you need confidence that your code works against the actual database engine, message broker, or cache that runs in production. `@ServiceConnection` is the modern, zero-boilerplate way to wire that container into Boot's auto-configuration.

## 3. Core concept

Three annotations drive the workflow:

| Annotation | Where | What it does |
|---|---|---|
| `@Testcontainers` | Test class | JUnit 5 extension — manages container lifecycle |
| `@Container` | Field | Marks a container for start/stop lifecycle management |
| `@ServiceConnection` | Field | Tells Boot to derive `DataSource` / broker URL directly from the container |

Boot's `@ServiceConnection` support works through `ConnectionDetailsFactory` implementations (one per technology). The factory calls `container.getJdbcUrl()`, `container.getUsername()` etc. and produces a `ConnectionDetails` bean that overrides auto-configured defaults — exactly what `@DynamicPropertySource` used to do manually.

## 4. Diagram

<svg viewBox="0 0 660 320" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="660" height="320" fill="#1c2430" rx="10"/>
  <!-- Docker -->
  <rect x="20" y="50" width="160" height="200" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="100" y="80" text-anchor="middle" fill="#79c0ff" font-weight="bold">Docker</text>
  <rect x="35" y="95" width="130" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="118" text-anchor="middle" fill="#6db33f" font-size="12">PostgreSQL</text>
  <text x="100" y="135" text-anchor="middle" fill="#8b949e" font-size="11">container</text>
  <rect x="35" y="160" width="130" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="100" y="183" text-anchor="middle" fill="#e6edf3" font-size="12">Redis</text>
  <text x="100" y="200" text-anchor="middle" fill="#8b949e" font-size="11">container</text>
  <!-- ServiceConnection bridge -->
  <rect x="240" y="110" width="170" height="80" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="138" text-anchor="middle" fill="#6db33f" font-size="12">@ServiceConnection</text>
  <text x="325" y="158" text-anchor="middle" fill="#8b949e" font-size="11">ConnectionDetailsFactory</text>
  <text x="325" y="175" text-anchor="middle" fill="#8b949e" font-size="11">auto-derives URL/creds</text>
  <!-- Spring Boot context -->
  <rect x="470" y="80" width="165" height="140" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="552" y="108" text-anchor="middle" fill="#79c0ff" font-size="12">Spring Boot</text>
  <text x="552" y="126" text-anchor="middle" fill="#8b949e" font-size="11">Application Context</text>
  <rect x="485" y="138" width="135" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="552" y="162" text-anchor="middle" fill="#6db33f" font-size="12">DataSource bean</text>
  <rect x="485" y="180" width="135" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="552" y="201" text-anchor="middle" fill="#8b949e" font-size="12">RedisTemplate bean</text>
  <!-- arrows -->
  <line x1="185" y1="140" x2="238" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr2)"/>
  <line x1="410" y1="150" x2="468" y2="155" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="325" y="255" text-anchor="middle" fill="#8b949e" font-size="12">No @DynamicPropertySource needed</text>
  <defs>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_`@ServiceConnection` reads the live container URL and injects it into Boot's auto-configuration transparently._

## 5. Runnable example

```java
// File: TestcontainersDemoTest.java
// How to run: place inside a Spring Boot 3.1+ project's test source root;
// Requires Docker running on the host.
// Dependencies in pom.xml:
//   spring-boot-starter-data-jpa, spring-boot-starter-test,
//   spring-boot-testcontainers, testcontainers:postgresql
// Run: ./mvnw test -Dtest=TestcontainersDemoTest

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.jdbc.core.JdbcTemplate;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
@Testcontainers   // JUnit 5 extension — manages container lifecycle
// Prevent Boot from replacing DataSource with H2
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
class TestcontainersDemoTest {

    // @Container — lifecycle tied to the test class
    // @ServiceConnection — Boot reads host/port/creds and wires DataSource automatically
    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    JdbcTemplate jdbcTemplate;

    @Test
    void containerIsRunning() {
        assertThat(postgres.isRunning()).isTrue();
    }

    @Test
    void canQueryRealPostgres() {
        // Execute a query against the real Postgres container
        Integer result = jdbcTemplate.queryForObject("SELECT 1 + 1", Integer.class);
        assertThat(result).isEqualTo(2);
    }
}
```

**How to run:** Ensure Docker is running, then `./mvnw test -Dtest=TestcontainersDemoTest`. The container starts, tests run, container stops.

## 6. Walkthrough

1. `@Testcontainers` — activates the JUnit 5 Testcontainers extension, which detects `@Container` fields and manages `start()` / `stop()` around the test class.
2. `static PostgreSQLContainer<?>` — declared `static` so one container is shared across all test methods in the class (faster than per-method). Testcontainers downloads the image on first run and caches it locally.
3. `@ServiceConnection` — Spring Boot's `PostgreSQLContainerConnectionDetailsFactory` reads `postgres.getJdbcUrl()`, `getUsername()`, `getPassword()` from the live container and creates a `JdbcConnectionDetails` bean. Boot's `DataSource` auto-configuration picks this bean up, overriding any `spring.datasource.*` properties.
4. `@AutoConfigureTestDatabase(replace = NONE)` — prevents Boot's test auto-configuration from replacing the real `DataSource` with an embedded H2.
5. `@Autowired JdbcTemplate` — receives a `JdbcTemplate` backed by the live Postgres container URL.
6. `canQueryRealPostgres()` — `SELECT 1 + 1` proves the real driver and engine are in use.

## 7. Gotchas & takeaways

> Without `@AutoConfigureTestDatabase(replace = NONE)`, Spring Boot test auto-configuration **replaces** your `DataSource` with H2 even when a container is running — the container starts but is never used.

> The container field must be `static` to share a single container across all test methods. A non-static field restarts the container per test, which is very slow.

> `@ServiceConnection` works out-of-the-box for PostgreSQL, MySQL, MariaDB, MongoDB, Redis, Kafka, RabbitMQ, and Elasticsearch in Boot 3.1+. For custom containers, implement `ConnectionDetailsFactory`.

- Always declare containers as `static` fields unless you specifically need per-test isolation.
- Use `@ServiceConnection` instead of `@DynamicPropertySource` for supported technologies — less code, same effect.
- Testcontainers image pulls are slow on first run; CI pipelines benefit from Docker layer caching.
- Combine with `@Sql` to seed test data before each test method.
- For large test suites, consider `TestcontainersConfiguration` in a shared base class to reuse containers across test classes.
