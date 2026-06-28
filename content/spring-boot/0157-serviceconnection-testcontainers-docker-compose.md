---
card: spring-boot
gi: 157
slug: serviceconnection-testcontainers-docker-compose
title: "@ServiceConnection & Testcontainers / Docker Compose"
---

## 1. What it is

**Testcontainers** launches real Docker containers (PostgreSQL, Redis, Kafka, etc.) during tests, giving you the actual database engine instead of H2 or mocks. **Docker Compose support** (Spring Boot 3.1+) starts a `compose.yaml` file automatically at application startup. **`@ServiceConnection`** (Spring Boot 3.1+) is a annotation that wires a container's host and port directly into Spring Boot's auto-configuration — no manual `spring.datasource.url` overrides needed.

## 2. Why & when

H2 differences from PostgreSQL (e.g. `SERIAL`, `RETURNING`, `ON CONFLICT`) cause tests that pass locally to fail in production. Testcontainers runs the exact same engine you use in production. `@ServiceConnection` removes the boilerplate of manually extracting a container's mapped port and setting `spring.datasource.url` in each test.

Use Testcontainers + `@ServiceConnection` when:

- Integration tests must run against the real database engine, not an in-memory substitute.
- You want zero-config Docker-backed tests with Spring Boot.
- CI already has Docker — Testcontainers works with Docker-in-Docker.

Use Docker Compose support for local development: define your infrastructure in `compose.yaml` and Spring Boot starts it before your app.

## 3. Core concept

With `@ServiceConnection`, you annotate a Testcontainers `@Container` field. Spring Boot's `ConnectionDetailsFactory` detects the annotation, reads the container's mapped connection details, and feeds them into the matching auto-configuration (DataSource, Redis, Kafka, etc.) — replacing any `spring.datasource.*` properties for the duration of the test.

```java
@SpringBootTest
class MyTest {
    @Container
    @ServiceConnection   // wires container URL → spring.datasource.*
    static PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16");
}
```

Docker Compose support: Spring Boot detects `compose.yaml` in the project root and calls `docker compose up` before starting — then `docker compose stop` on shutdown.

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="155" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="107" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">@SpringBootTest</text>
  <text x="97" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">@Container + @ServiceConnection</text>
  <rect x="255" y="60" width="170" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="83" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">Docker container</text>
  <text x="340" y="100" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">PostgreSQL:16 on random port</text>
  <rect x="255" y="130" width="170" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="340" y="152" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">DataSource</text>
  <text x="340" y="169" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">auto-wired connection</text>
  <rect x="500" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="107" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Test runs against</text>
  <text x="580" y="124" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">real PostgreSQL</text>
  <line x1="177" y1="110" x2="251" y2="87" stroke="#6db33f" stroke-width="1.5" marker-end="url(#tc)"/>
  <line x1="340" y1="112" x2="340" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#tc2)"/>
  <line x1="427" y1="155" x2="496" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#tc3)"/>
  <defs>
    <marker id="tc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="tc2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="tc3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`@ServiceConnection` extracts the container's mapped port and feeds it into the `DataSource` auto-configuration — the test sees a real PostgreSQL engine with no manual URL setup.

## 5. Runnable example

```java
// ServiceConnectionTest.java — Spring Boot 3.1+ test
// pom.xml (test scope):
//   org.springframework.boot:spring-boot-testcontainers
//   org.testcontainers:postgresql
//   org.testcontainers:junit-jupiter
//
// Also: spring-boot-starter-data-jpa, org.postgresql:postgresql (runtime)

import jakarta.persistence.*;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.data.jpa.repository.JpaRepository;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.assertj.core.api.Assertions.assertThat;

@Entity
class Note {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) Long id;
    String content;
    protected Note() {}
    Note(String content) { this.content = content; }
    public Long getId() { return id; }
    public String getContent() { return content; }
}

interface NoteRepo extends JpaRepository<Note, Long> {}

@SpringBootTest
@Testcontainers
class ServiceConnectionTest {

    // @ServiceConnection wires this container's URL into spring.datasource.*
    @Container
    @ServiceConnection
    static PostgreSQLContainer<?> postgres =
            new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired
    NoteRepo repo;

    @Test
    void savesAndFindsNote() {
        Note saved = repo.save(new Note("Hello PostgreSQL!"));
        assertThat(saved.getId()).isNotNull();

        Note found = repo.findById(saved.getId()).orElseThrow();
        assertThat(found.getContent()).isEqualTo("Hello PostgreSQL!");
    }
}
```

**How to run:** requires Docker running locally. Run `./mvnw test` — Testcontainers pulls `postgres:16-alpine`, starts it, `@ServiceConnection` wires the URL, Flyway or `ddl-auto=create-drop` creates the schema, and the test runs against real PostgreSQL.

## 6. Walkthrough

- `@Testcontainers` activates the JUnit 5 Testcontainers extension, which manages `@Container` lifecycle — starting the container before the test class and stopping it after.
- `@Container static PostgreSQLContainer<?> postgres` uses a static field so one container is shared across all test methods in the class (faster than per-method containers).
- `@ServiceConnection` tells Spring Boot to read `postgres.getJdbcUrl()`, `postgres.getUsername()`, and `postgres.getPassword()` from the running container and inject them into the `DataSource` auto-configuration — overriding any `spring.datasource.*` properties in `application.properties`.
- `@SpringBootTest` starts the full application context. Combined with `@ServiceConnection`, the `DataSource` bean points at the running PostgreSQL container, not H2.
- `repo.save(new Note(...))` issues a real PostgreSQL `INSERT`; `repo.findById(...)` issues a `SELECT`. The test validates real persistence semantics (auto-increment IDs, constraint enforcement, etc.).
- For **Docker Compose** support: add `spring-boot-docker-compose` dependency and create `compose.yaml`. Spring Boot calls `docker compose up` on start and `docker compose stop` on shutdown — useful for dev, not test.

## 7. Gotchas & takeaways

> Testcontainers requires Docker to be running. In CI, ensure the Docker daemon is available (standard on GitHub Actions, GitLab CI, CircleCI). Docker-in-Docker setups may need additional privileges (`--privileged`).

> Without `@ServiceConnection`, you must override properties manually in each test:
> ```java
> @DynamicPropertySource
> static void props(DynamicPropertyRegistry r) {
>     r.add("spring.datasource.url", postgres::getJdbcUrl);
> }
> ```
> `@ServiceConnection` replaces this boilerplate entirely for supported containers.

- `@ServiceConnection` supports PostgreSQL, MySQL, MariaDB, MongoDB, Redis, RabbitMQ, Kafka, Cassandra, Couchbase, and more.
- `@Container` without `static` creates a new container per test instance — slower but fully isolated.
- Docker Compose support: `spring.docker.compose.lifecycle-management=start-only` keeps containers running after the app stops (faster restarts in dev).
- Add `@Transactional` to test methods to auto-rollback after each test — keeps the database clean between tests.
- Testcontainers Cloud (paid) runs containers remotely — useful if your CI machines lack Docker.
