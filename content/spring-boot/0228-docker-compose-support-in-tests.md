---
card: spring-boot
gi: 228
slug: docker-compose-support-in-tests
title: Docker Compose support in tests
---

## 1. What it is

Spring Boot 3.1 introduced first-class Docker Compose support. Drop a `compose.yaml` file into your project root and Boot's `DockerComposeLifecycleManager` automatically starts it before the application context and stops it after — both in regular runs and in tests. No shell scripts, no manual `docker compose up` before running tests.

## 2. Why & when

Teams already have Docker Compose files describing their local dev stack. Testcontainers is more powerful but requires code changes. Docker Compose support is ideal when you want to reuse your existing `compose.yaml` for integration tests without adding Testcontainers dependencies or writing container-management code.

## 3. Core concept

Add `spring-boot-docker-compose` on the classpath. Boot detects `compose.yaml` (or `compose.yml`, `docker-compose.yaml`, `docker-compose.yml`) at the project root. At startup it runs `docker compose up` and waits for health checks. On shutdown it runs `docker compose down`. In tests you annotate with `@SpringBootTest` as usual — the Compose lifecycle is transparent.

Two key properties control behaviour:
- `spring.docker.compose.enabled` — toggle the feature.
- `spring.docker.compose.lifecycle-management` — `start-and-stop` (default), `start-only`, or `none`.

`@ServiceConnection` works with Docker Compose too: Boot reads the service's exposed port and credentials from Compose and wires `DataSource` / broker beans without extra configuration.

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="300" fill="#1c2430" rx="10"/>
  <!-- compose.yaml -->
  <rect x="20" y="60" width="150" height="60" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="86" text-anchor="middle" fill="#e6edf3">compose.yaml</text>
  <text x="95" y="106" text-anchor="middle" fill="#8b949e" font-size="11">project root</text>
  <!-- DockerComposeLifecycleManager -->
  <rect x="220" y="50" width="200" height="80" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="320" y="78" text-anchor="middle" fill="#6db33f" font-size="12">DockerCompose</text>
  <text x="320" y="96" text-anchor="middle" fill="#6db33f" font-size="12">LifecycleManager</text>
  <text x="320" y="116" text-anchor="middle" fill="#8b949e" font-size="11">docker compose up/down</text>
  <!-- Docker -->
  <rect x="480" y="50" width="140" height="140" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="2"/>
  <text x="550" y="80" text-anchor="middle" fill="#79c0ff">Docker</text>
  <rect x="493" y="92" width="114" height="36" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="550" y="116" text-anchor="middle" fill="#6db33f" font-size="12">postgres service</text>
  <rect x="493" y="136" width="114" height="36" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="550" y="160" text-anchor="middle" fill="#8b949e" font-size="12">redis service</text>
  <!-- Spring Boot context -->
  <rect x="220" y="180" width="200" height="60" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="206" text-anchor="middle" fill="#79c0ff">Spring Boot Context</text>
  <text x="320" y="224" text-anchor="middle" fill="#8b949e" font-size="11">DataSource wired via @ServiceConnection</text>
  <!-- arrows -->
  <line x1="170" y1="90" x2="218" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a3)"/>
  <line x1="420" y1="90" x2="478" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a3)"/>
  <line x1="320" y1="132" x2="320" y2="178" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a3)"/>
  <defs>
    <marker id="a3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_Boot reads `compose.yaml`, manages `docker compose up/down`, and wires connection details automatically._

## 5. Runnable example

```java
// File: DockerComposeDemoTest.java
// How to run:
//   1. Add spring-boot-docker-compose to pom.xml (test scope)
//   2. Create compose.yaml in project root (see comment below)
//   3. Run: ./mvnw test -Dtest=DockerComposeDemoTest
//   Docker must be running.

// compose.yaml (place at project root):
// -------------------------------------------
// services:
//   postgres:
//     image: postgres:16-alpine
//     environment:
//       POSTGRES_DB: testdb
//       POSTGRES_USER: test
//       POSTGRES_PASSWORD: test
//     ports:
//       - "5432"
// -------------------------------------------

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;

import static org.assertj.core.api.Assertions.assertThat;

@SpringBootTest
// Docker Compose is started automatically by Boot when
// spring-boot-docker-compose is on the classpath.
// No @Testcontainers, no @DynamicPropertySource needed.
class DockerComposeDemoTest {

    @Autowired
    JdbcTemplate jdbcTemplate;

    @Test
    void dockerComposeStartedAutomatically() {
        // If we reach here, Boot started the Compose stack and wired DataSource
        Integer result = jdbcTemplate.queryForObject("SELECT 42", Integer.class);
        assertThat(result).isEqualTo(42);
    }
}
```

**How to run:** Ensure Docker is running, create `compose.yaml` at the project root (see comment), add `spring-boot-docker-compose` to `pom.xml` test scope, then `./mvnw test -Dtest=DockerComposeDemoTest`.

## 6. Walkthrough

1. `spring-boot-docker-compose` on the classpath activates `DockerComposeLifecycleManager` via auto-configuration.
2. At application startup, Boot looks for `compose.yaml` (and its variants) in the working directory and project root.
3. It executes `docker compose up --wait` — the `--wait` flag blocks until all service health checks pass.
4. `@ServiceConnection` reads the exposed port and environment variables from the running Compose services and synthesises a `JdbcConnectionDetails` bean, which auto-configures `DataSource`.
5. `@SpringBootTest` starts the full context — `DataSource` is backed by the real Postgres container.
6. After the last test, Boot calls `docker compose down` (configurable via `lifecycle-management`).

## 7. Gotchas & takeaways

> Docker Compose support runs `docker compose up` on **every** application startup — including production. In non-test profiles, disable it with `spring.docker.compose.enabled=false` or scope the dependency to `test`.

> The `compose.yaml` file is discovered relative to the **working directory**, not the module root in a multi-module build. Set `spring.docker.compose.file` explicitly if your Compose file lives elsewhere.

> Docker Compose support and Testcontainers are **complementary, not competing**. Use Compose when you already have `compose.yaml` and want zero code changes. Use Testcontainers for programmatic control, dynamic images, or per-test container isolation.

- Add `spring-boot-docker-compose` with `<scope>test</scope>` to avoid activating it in production builds.
- Use `spring.docker.compose.lifecycle-management=start-only` in CI to skip `docker compose down` (let the CI runner clean up).
- Combine with `@ActiveProfiles("test")` and a test-specific `compose.yaml` for full environment isolation.
- Health checks in `compose.yaml` are critical — without them Boot may connect before Postgres is ready.
