---
card: spring-session
gi: 5
slug: enablespringhttpsession
title: "@EnableSpringHttpSession"
---

## 1. What it is

`@EnableSpringHttpSession` is the base configuration annotation that wires up `SessionRepositoryFilter` (card 0004) and the servlet-specific plumbing needed for Spring Session to intercept `HttpSession` — but, notably, it does *not* configure which `SessionRepository` backs it. It's the generic foundation that store-specific annotations like `@EnableRedisHttpSession` (card 0009) and `@EnableJdbcHttpSession` (card 0012) build on top of.

## 2. Why & when

Every Spring Session setup needs the same servlet-layer wiring (the filter, request wrapping, cookie handling) regardless of which store backs it — but the store itself is a separate, pluggable decision. `@EnableSpringHttpSession` separates these two concerns: it handles the "make `HttpSession` work through Spring Session" part universally, while expecting the application to separately provide a `SessionRepository` bean of its own choosing. This is the annotation to reach for when using a store that doesn't have (or doesn't need) its own dedicated `@Enable*HttpSession` annotation — most commonly, a custom or non-standard `SessionRepository` implementation.

Reach for `@EnableSpringHttpSession` directly (rather than a store-specific variant) when:

- Building a custom `SessionRepository` implementation for a store Spring Session doesn't ship first-class support for, and needing the generic servlet wiring without any store-specific assumptions baked in.
- Understanding what the store-specific annotations (`@EnableRedisHttpSession`, `@EnableJdbcHttpSession`) are actually doing underneath — they all compose this same base configuration plus a store-specific `SessionRepository` bean definition.
- Testing or prototyping with a simple in-memory `SessionRepository` (like `MapSessionRepository`) before committing to a specific production store, using the generic annotation with a manually defined repository bean.

## 3. Core concept

Think of `@EnableSpringHttpSession` as installing a universal electrical outlet standard in a building — it defines the socket shape, voltage, and wiring conventions (the servlet filter, request wrapping, cookie handling) that any compliant appliance (any `SessionRepository` implementation) can be plugged into. `@EnableRedisHttpSession` and `@EnableJdbcHttpSession` are pre-wired appliances that come with both the plug *and* the specific device already built in — convenient defaults for the common cases — but nothing stops someone from wiring in their own custom appliance (a hand-built `SessionRepository`) directly into the same standard outlet.

```java
@Configuration
@EnableSpringHttpSession
public class SessionConfig {

    @Bean
    public SessionRepository<?> sessionRepository() {
        return new MapSessionRepository(new ConcurrentHashMap<>()); // any implementation works here
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnableSpringHttpSession provides the generic servlet wiring that any SessionRepository bean plugs into">
  <rect x="30" y="80" width="220" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@EnableSpringHttpSession</text>
  <text x="140" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">generic filter + wiring</text>

  <rect x="380" y="20" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MapSessionRepository</text>

  <rect x="380" y="90" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Custom SessionRepository</text>

  <rect x="380" y="160" width="220" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Any other implementation</text>

  <line x1="250" y1="110" x2="375" y2="43" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="250" y1="110" x2="375" y2="113" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="250" y1="110" x2="375" y2="183" stroke="#8b949e" stroke-width="1.5"/>
</svg>

The annotation itself is store-agnostic — it composes with whatever `SessionRepository` bean the application declares.

## 5. Runnable example

The scenario: building a minimal working Spring Session setup with an in-memory `MapSessionRepository` using the generic annotation, growing to add a scheduled cleanup task since the in-memory store has no automatic expiration sweep, and finally to swap in a genuinely custom `SessionRepository` implementation to see the annotation's store-agnostic design in practice.

### Level 1 — Basic

```java
// InMemorySessionConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.MapSessionRepository;
import org.springframework.session.SessionRepository;
import org.springframework.session.config.annotation.web.http.EnableSpringHttpSession;

import java.util.concurrent.ConcurrentHashMap;

@Configuration
@EnableSpringHttpSession
public class InMemorySessionConfig {

    @Bean
    public SessionRepository<?> sessionRepository() {
        return new MapSessionRepository(new ConcurrentHashMap<>());
    }
}
```

**How to run:** add this configuration class to a Spring Boot web app with no other session-related dependencies (no Redis, no database needed). Make a request that sets a session attribute, then a second request with the same cookie reading it back. Expected output: the attribute persists across requests within the same JVM — functionally similar to a container's default session, but now flowing through Spring Session's own filter and repository abstraction.

### Level 2 — Intermediate

`MapSessionRepository` alone doesn't proactively expire old sessions the way Redis (via TTL) or JDBC (via a cleanup job, card 0007) does — without help, it accumulates every session ever created for the life of the JVM, a real memory leak in a long-running process.

```java
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.session.MapSessionRepository;
import org.springframework.session.Session;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class InMemorySessionCleanup {

    private final Map<String, Session> sessionStore;
    private final MapSessionRepository repository;

    public InMemorySessionCleanup(ConcurrentHashMap<String, Session> sessionStore) {
        this.sessionStore = sessionStore;
        this.repository = new MapSessionRepository(sessionStore);
    }

    @Scheduled(fixedRate = 60_000) // run every minute
    public void evictExpired() {
        Instant now = Instant.now();
        sessionStore.entrySet().removeIf(entry -> {
            Session session = entry.getValue();
            Instant expiry = session.getLastAccessedTime().plus(session.getMaxInactiveInterval());
            return now.isAfter(expiry);
        });
    }
}
```

**How to run:** wire the same `ConcurrentHashMap` bean used by `sessionRepository()` into this cleanup component (sharing the exact map instance), enable `@EnableScheduling`, then create several sessions with a short `maxInactiveInterval` for testing. Expected behavior: sessions past their expiry are removed from the map within a minute of the scheduled check, keeping memory bounded — verify by checking the map's size before and after the interval elapses.

What changed: the in-memory store now has explicit, active expiration handling, something Redis-backed and JDBC-backed repositories provide more automatically (via native TTL or a maintained cleanup job) but a bare `MapSessionRepository` requires the application to build itself.

### Level 3 — Advanced

Demonstrating the annotation's true store-agnostic design: swap in a completely custom `SessionRepository` — here, one that layers a simple write-through audit log on top of the in-memory map — without touching `@EnableSpringHttpSession` or anything else in the servlet-layer wiring.

```java
import org.springframework.session.MapSession;
import org.springframework.session.SessionRepository;

import java.time.Instant;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

public class AuditingSessionRepository implements SessionRepository<MapSession> {

    private final Map<String, MapSession> store = new ConcurrentHashMap<>();

    @Override
    public MapSession createSession() {
        MapSession session = new MapSession();
        System.out.printf("[%s] session CREATED: %s%n", Instant.now(), session.getId());
        return session;
    }

    @Override
    public void save(MapSession session) {
        store.put(session.getId(), session);
        System.out.printf("[%s] session SAVED: %s%n", Instant.now(), session.getId());
    }

    @Override
    public MapSession findById(String id) {
        return store.get(id);
    }

    @Override
    public void deleteById(String id) {
        store.remove(id);
        System.out.printf("[%s] session DELETED: %s%n", Instant.now(), id);
    }
}
```

**How to run:** replace the `sessionRepository()` bean from Level 1 with `new AuditingSessionRepository()`, leaving `@EnableSpringHttpSession` completely untouched. Make requests that create, modify, and let a session expire (or explicitly invalidate it). Expected console output: `CREATED`, `SAVED`, and `DELETED` log lines tracing every session lifecycle event, proving the generic annotation required zero changes to accept an entirely custom, hand-written repository implementation.

What changed and why it's production-flavored: this is the exact mechanism a team would use to build support for a store Spring Session doesn't ship out of the box (a proprietary internal cache, an unusual database) — the generic annotation's contract with `SessionRepository` is the extension point, and this example proves it holds even for a repository implementation the library's authors never anticipated.

## 6. Walkthrough

Tracing what `@EnableSpringHttpSession` actually wires up, and how it interacts with the application-supplied repository, in execution order:

1. On application startup, Spring processes the `@EnableSpringHttpSession` annotation, which imports a configuration class registering `SessionRepositoryFilter` (card 0004) as a servlet filter bean, along with the default `HttpSessionIdResolver` (responsible for reading/writing the session ID cookie).
2. This registered filter has a dependency on a `SessionRepository` bean — but `@EnableSpringHttpSession` itself declares no opinion about which implementation satisfies that dependency; it's simply autowired from whatever bean the application context provides.
3. Spring's dependency injection resolves that dependency against `InMemorySessionConfig.sessionRepository()` (Level 1) or, once swapped, `AuditingSessionRepository` (Level 3) — the filter's own code never changes based on which one is present.
4. At request time, `SessionRepositoryFilter` behaves exactly as described in card 0004 — wrap the request, lazily resolve `getSession()` against whichever repository was injected, flush changes at the end — completely unaware of which concrete implementation it's actually talking to.
5. For `AuditingSessionRepository` specifically, each of the repository's own methods (`createSession`, `save`, `findById`, `deleteById`) logs its own audit line — behavior entirely private to that implementation, invisible to and unaffected by the generic filter machinery calling it.

```
@EnableSpringHttpSession
   |
registers SessionRepositoryFilter (generic, store-agnostic)
   |
filter depends on: SessionRepository<?> bean  <- resolved via normal Spring DI
   |
   +-- MapSessionRepository (Level 1)
   +-- AuditingSessionRepository (Level 3)
   +-- (any other implementation)
   |
at request time: filter calls repository.findById/save/createSession
   |             — identical calls regardless of which implementation is wired in
```

## 7. Gotchas & takeaways

> `@EnableSpringHttpSession` alone, with no `SessionRepository` bean defined anywhere in the application context, fails at startup with a clear dependency-injection error — it's deliberately incomplete by itself, since the whole point of separating it from the store-specific annotations is that it has no default store to fall back on.

- Prefer the store-specific annotations (`@EnableRedisHttpSession`, `@EnableJdbcHttpSession`) for standard production use — they handle store-specific configuration details (serialization, table/index setup) that would otherwise need to be replicated manually alongside a bare `@EnableSpringHttpSession` plus a hand-wired repository.
- `MapSessionRepository` is appropriate for local testing and single-instance scenarios only — it provides none of the clustering benefits (card 0001) that are the entire reason to reach for Spring Session in the first place, since its data still lives in one JVM's memory.
- A custom `SessionRepository` (Level 3) is a legitimate, supported extension point, not a workaround — Spring Session's design explicitly anticipates stores beyond the ones it ships built-in support for.
- Expiration handling is *not* automatically provided by `@EnableSpringHttpSession` itself — it's the responsibility of whichever `SessionRepository` implementation is plugged in; a naive custom implementation (or bare `MapSessionRepository`, per Level 2) needs its own explicit cleanup strategy.
- When debugging "which annotation is actually configuring my sessions," remember that store-specific annotations like `@EnableRedisHttpSession` internally compose `@EnableSpringHttpSession`'s generic behavior plus their own `SessionRepository` bean — so the servlet-layer behavior described in this card applies universally, even when using a more specific annotation.
