---
card: spring-session
gi: 15
slug: in-memory-map-session-repository
title: "In-memory map session repository"
---

## 1. What it is

`MapSessionRepository` is Spring Session's simplest `SessionRepository` implementation — it stores sessions in a plain `Map<String, Session>` (typically a `ConcurrentHashMap`), entirely within the JVM's own memory, with no external store, no network round-trips, and no clustering. It's the repository briefly introduced alongside `@EnableSpringHttpSession` (card 0005) as the minimal, generic-annotation companion, revisited here in its own right as a legitimate tool for specific situations, not just a stepping stone to a "real" store.

## 2. Why & when

Every other repository covered so far exists specifically to solve the clustering problem (card 0001) — multiple instances sharing session state. `MapSessionRepository` doesn't solve that problem at all; it's functionally similar to what a container's own native session already provides. Its value lies elsewhere: it makes Spring Session's abstractions (the `Session`/`SessionRepository` interfaces, `SessionRepositoryFilter`'s transparent wrapping, session events) usable and testable without needing any external infrastructure running — genuinely useful for local development, unit and integration testing, and any single-instance deployment that has no clustering need at all.

Reach for `MapSessionRepository` when:

- Writing integration tests for session-dependent behavior — spinning up Redis or a database purely to test session logic is often unnecessary overhead; an in-memory repository gives fast, isolated, dependency-free tests.
- Local development — running Redis or a database locally just to develop and test features that happen to touch the session adds friction that `MapSessionRepository` avoids entirely.
- A genuinely single-instance deployment with no plans to scale horizontally — though even then, worth pausing on: if there's any reasonable chance the deployment grows to multiple instances later, starting with a real clustered store from day one avoids a migration later.

## 3. Core concept

Think of `MapSessionRepository` as a sticky note on your own desk versus the shared filing cabinet down the hall that every other store (Redis, JDBC, MongoDB, Hazelcast) represents. A sticky note is instant, requires no walk to the filing room, and is perfectly fine for a note only you will ever need — but the moment a colleague at a different desk needs to read or update that same note, the sticky-note approach breaks down completely, which is exactly the clustering problem every other repository in this card exists to solve and `MapSessionRepository` deliberately does not.

```java
@Bean
public SessionRepository<?> sessionRepository() {
    return new MapSessionRepository(new ConcurrentHashMap<>());
}
// Fast, zero infrastructure, but data lives only in this one JVM's memory.
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MapSessionRepository stores data purely inside the single JVM's own memory, with no path to any other instance">
  <rect x="200" y="30" width="240" height="90" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Single JVM instance</text>
  <rect x="230" y="70" width="180" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ConcurrentHashMap</text>

  <text x="320" y="160" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">no network path to any other instance — by design</text>
</svg>

There is deliberately nothing outside this one box — that's both the entire appeal (simplicity, speed) and the entire limitation (no clustering) of this repository.

## 5. Runnable example

The scenario: writing a fast integration test for session-dependent controller logic using `MapSessionRepository`, growing to test session expiration behavior deterministically without waiting real wall-clock minutes, and finally to explicitly document and enforce (via a startup check) that this repository never accidentally ships to a multi-instance production deployment.

### Level 1 — Basic

```java
// CartSessionIntegrationTest.java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.ResponseEntity;
import org.springframework.session.MapSessionRepository;
import org.springframework.session.SessionRepository;
import org.springframework.session.config.annotation.web.http.EnableSpringHttpSession;

import java.util.concurrent.ConcurrentHashMap;

import static org.junit.jupiter.api.Assertions.assertTrue;

@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class CartSessionIntegrationTest {

    @Configuration
    @EnableSpringHttpSession
    static class TestSessionConfig {
        @Bean
        public SessionRepository<?> sessionRepository() {
            return new MapSessionRepository(new ConcurrentHashMap<>()); // no Redis/DB needed for this test
        }
    }

    @Autowired
    private TestRestTemplate restTemplate;

    @Test
    void cartCountIncrementsAcrossRequestsWithSameSession() {
        ResponseEntity<String> first = restTemplate.postForEntity("/cart/add?item=book", null, String.class);
        String cookie = first.getHeaders().getFirst(HttpHeaders.SET_COOKIE);

        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.COOKIE, cookie);
        ResponseEntity<String> second = restTemplate.exchange(
                "/cart/add?item=pen", org.springframework.http.HttpMethod.POST,
                new HttpEntity<>(headers), String.class);

        assertTrue(second.getBody().contains("Cart has 2 item"));
    }
}
```

**How to run:** `mvn test` (or the equivalent Gradle task) — no Redis, no database, no Docker container needed for this test to run. Expected result: the test passes quickly (typically well under a second), verifying real `HttpSession`-based cart logic end-to-end through actual HTTP requests, entirely in-process.

### Level 2 — Intermediate

Testing session *expiration* behavior against a real store means either waiting real wall-clock time (slow, flaky) or manipulating the store's clock — `MapSessionRepository`, being a plain in-memory structure the test fully controls, makes it straightforward to simulate expiration deterministically by directly manipulating a session's state.

```java
import org.junit.jupiter.api.Test;
import org.springframework.session.MapSession;
import org.springframework.session.MapSessionRepository;

import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.ConcurrentHashMap;

import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertNotNull;

class SessionExpirationDeterministicTest {

    @Test
    void expiredSessionIsNotReturnedByFindById() {
        var store = new ConcurrentHashMap<String, MapSession>();
        var repository = new MapSessionRepository(store);

        MapSession session = repository.createSession();
        session.setMaxInactiveInterval(Duration.ofSeconds(1));
        repository.save(session);

        assertNotNull(repository.findById(session.getId()), "session should exist immediately after save");

        // Instead of Thread.sleep(1100) (slow, flaky under load), directly manipulate
        // the session's last-accessed time to simulate the passage of time deterministically.
        session.setLastAccessedTime(Instant.now().minus(Duration.ofSeconds(5)));
        store.put(session.getId(), session);

        assertNull(repository.findById(session.getId()), "session past its interval should be treated as expired");
    }
}
```

**How to run:** run this test directly — no `Thread.sleep`, no real waiting. Expected result: it passes near-instantly, deterministically proving `MapSessionRepository.findById(...)` correctly treats a session with a last-accessed time older than its `maxInactiveInterval` as expired, without the test suite ever pausing for real elapsed time.

What changed: expiration logic — normally awkward and slow to test against real wall-clock time — becomes a fast, deterministic, reliable unit test by directly manipulating the in-memory structure's session state, a testing convenience genuinely specific to having full, direct control over the store.

### Level 3 — Advanced

Because `MapSessionRepository` has no clustering capability at all, accidentally shipping it to a multi-instance production deployment (say, a developer's test configuration class getting picked up by component scanning in production by mistake) silently breaks session sharing across instances — a startup-time guard catches this class of configuration mistake before it causes confusing production symptoms.

```java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.session.MapSessionRepository;
import org.springframework.session.SessionRepository;
import org.springframework.stereotype.Component;

@Component
public class NoInMemorySessionsInProductionGuard {

    private final SessionRepository<?> sessionRepository;
    private final String activeProfile;

    public NoInMemorySessionsInProductionGuard(SessionRepository<?> sessionRepository,
            @Value("${spring.profiles.active:}") String activeProfile) {
        this.sessionRepository = sessionRepository;
        this.activeProfile = activeProfile;
    }

    @EventListener(ApplicationReadyEvent.class)
    public void verify() {
        boolean isProduction = activeProfile.contains("production");
        boolean isInMemory = sessionRepository instanceof MapSessionRepository;

        if (isProduction && isInMemory) {
            throw new IllegalStateException(
                    "MapSessionRepository (in-memory, non-clustered) is active under the "
                            + "'production' profile — sessions will NOT be shared across instances. "
                            + "This is almost certainly a misconfiguration.");
        }
    }
}
```

**How to run:** deploy the application with the `production` profile active but a test configuration accidentally still providing `MapSessionRepository` (e.g. via an overly broad `@Profile`-less test config class left on the classpath). Expected behavior: the application fails to start with a clear, specific error naming the exact problem, rather than starting successfully and only surfacing the bug later as mysteriously inconsistent logins across load-balanced instances.

What changed and why it's production-flavored: this converts a subtle, easy-to-miss configuration mistake (one that would otherwise manifest as confusing, hard-to-diagnose "users randomly get logged out" reports from real users) into an immediate, loud startup failure with a message that names the exact cause — a legitimate tool given how easy it is for a convenient testing default to accidentally leak into a real deployment's active configuration.

## 6. Walkthrough

Tracing where `MapSessionRepository` fits across a project's lifecycle, in execution order:

1. During local development, a developer runs the application with `MapSessionRepository` configured (Level 1's `TestSessionConfig`, or an equivalent development-profile configuration) — no Redis or database container needs to be running locally just to iterate on session-touching features.
2. The team writes integration tests (Level 1) against this same in-memory repository — tests run fast, in isolation, with no shared external test infrastructure to coordinate or clean up between test runs.
3. Expiration-specific test cases (Level 2) manipulate the in-memory store's session objects directly, verifying expiration logic deterministically without real elapsed time, something meaningfully harder to do cleanly against a real external store's own clock.
4. As the application approaches production deployment, `NoInMemorySessionsInProductionGuard` (Level 3) runs automatically on every startup, regardless of environment — in development and test profiles, the check simply doesn't trigger (not "production"); the instant the `production` profile is active with an in-memory repository still wired in, the application refuses to start.
5. This guard is what actually enforces the boundary this card is about: `MapSessionRepository` is a legitimate, valuable tool for the first three steps, and a startup-time-caught mistake if it ever reaches the fourth.

```
Local dev: MapSessionRepository -> fast iteration, no infrastructure needed
   |
Integration tests: MapSessionRepository -> fast, isolated, deterministic (Level 1-2)
   |
Production deploy attempt: NoInMemorySessionsInProductionGuard checks active profile
   |    production + in-memory repository? --yes--> fail startup loudly
   |    otherwise --> proceed normally
```

## 7. Gotchas & takeaways

> `MapSessionRepository` provides zero clustering capability — using it in any deployment with more than one application instance silently reintroduces the exact problem (card 0001) Spring Session as a whole exists to solve, with the added confusion that the application otherwise looks and behaves like a fully working Spring Session setup right up until a second instance enters the picture.

- The value of `MapSessionRepository` is specifically in development and testing contexts, where its lack of clustering is irrelevant (a single test JVM, a single local development instance) — it is not a lightweight production alternative to Redis or JDBC for genuinely single-instance production deployments without also weighing the risk of that deployment growing to multiple instances later.
- Testing session logic against `MapSessionRepository` (Level 1) still exercises the real `SessionRepositoryFilter`, the real `HttpSession` API, and real session event publication (card 0008) — only the storage backend differs from production, which means these tests provide genuine confidence in session-dependent application logic, not merely a shallow stand-in.
- Direct manipulation of session state for deterministic expiration testing (Level 2) is a testing-only technique — it works because the test has direct, unsynchronized access to the same in-memory structure the repository uses; this specific technique doesn't translate to testing against a real external store, which would need its own store-appropriate testing approach (like manipulating a Redis TTL directly via `redis-cli` in a test, or a similar store-specific mechanism).
- A startup guard (Level 3) is a cheap, valuable safety net precisely because this specific mistake (a testing/development convenience leaking into a real environment) is easy to make and hard to notice quickly — the symptom (inconsistent session behavior across instances) doesn't point obviously back at the actual cause.
- If genuinely building a single-instance-forever application with no clustering need, still weigh whether `MapSessionRepository`'s complete lack of durability (a JVM restart during a deploy loses every active session, identical to a container's native session, card 0001) is acceptable — often, even a "single instance for now" deployment benefits from Redis or JDBC's durability across restarts, independent of the clustering question entirely.
