---
card: spring-session
gi: 7
slug: session-expiration-cleanup
title: "Session expiration & cleanup"
---

## 1. What it is

Session expiration is the process of a session becoming invalid after a period of inactivity (`maxInactiveInterval`, defaulting to 30 minutes, same as most containers). Cleanup is the mechanism by which an *expired* session's data actually gets removed from the backing store — which, unlike a container's in-memory session, doesn't happen "for free" just because nobody's referencing it anymore; each store implementation has its own distinct cleanup strategy.

## 2. Why & when

A container's native in-memory session can rely on simple, local timers and garbage collection to reclaim expired sessions — everything lives in one process's memory, so cleanup is an internal implementation detail. An external store has no such luxury: Redis and a relational database don't inherently know a given row or key represents a "session" that should vanish after 30 minutes of inactivity — that has to be built. How this is built differs meaningfully by store: Redis uses native key TTL (expiring keys automatically), while JDBC-backed sessions rely on a scheduled cleanup task actively deleting expired rows, since relational databases have no native per-row expiration concept.

Reach for understanding expiration and cleanup mechanics when:

- Diagnosing "expired sessions are still showing up" — the answer depends heavily on which store is in use and whether its specific cleanup mechanism (TTL vs. scheduled task) is actually configured and running.
- Tuning `maxInactiveInterval` for a specific application's security and usability needs — shorter intervals reduce the window a stolen session cookie remains useful, at the cost of more frequent re-logins.
- Estimating storage growth for a session store under load — JDBC-backed sessions in particular can accumulate unboundedly if the cleanup task isn't running, since nothing else removes expired rows.

## 3. Core concept

Think of a container's in-memory session as food left out that simply evaporates once nobody's watching it — no active process is needed. A Redis-backed session is like food stored with a self-destructing timer built directly into the container itself (TTL) — set it once, and it's gone automatically at the set time, no external intervention required. A JDBC-backed session is like food stored in a plain box with an expiry date written on the label, but the box itself doesn't do anything about it — someone (a scheduled cleanup task) has to actively walk through the pantry, check every label, and physically throw out anything past its date; skip that chore, and expired food just accumulates indefinitely.

```
Redis:  SET session:abc123 <data> EX 1800   <- native, automatic expiration
JDBC:   INSERT INTO spring_session (...) VALUES (..., expiry_time)
        -- nothing deletes this row automatically; a scheduled task must
```

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Redis expires sessions automatically via native TTL; JDBC requires an explicit scheduled cleanup task to remove expired rows">
  <rect x="20" y="20" width="280" height="90" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Redis</text>
  <text x="160" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">key set with TTL</text>
  <text x="160" y="88" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">expires automatically, no task needed</text>

  <rect x="360" y="20" width="280" height="90" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="500" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">JDBC</text>
  <text x="500" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">row with expiry_time column</text>
  <text x="500" y="88" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">row persists until a task deletes it</text>

  <rect x="360" y="150" width="280" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="500" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SpringSessionBackedSessionRepository</text>
  <text x="500" y="192" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">cleanupExpiredSessions() (scheduled)</text>

  <line x1="500" y1="110" x2="500" y2="145" stroke="#f0883e" stroke-width="1.5"/>
</svg>

The two stores need fundamentally different cleanup strategies precisely because only one of them has a native concept of key expiration.

## 5. Runnable example

The scenario: setting a custom session timeout, growing to observe Redis's automatic TTL-based expiration directly, and finally to configure and verify the JDBC cleanup task actually running and removing expired rows.

### Level 1 — Basic

```properties
# application.properties
server.servlet.session.timeout=5m
```

```java
// TimeoutCheckController.java
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class TimeoutCheckController {

    @GetMapping("/demo/timeout")
    public String touch(HttpSession session) {
        return "Session " + session.getId() + " max inactive interval: "
                + session.getMaxInactiveInterval() + " seconds";
    }
}
```

**How to run:** set the timeout to 5 minutes, start the app with any Spring Session store configured, create a session, then wait 5+ minutes without touching it before making another request with the same cookie. Expected behavior: the session is treated as gone — a new session is created — since it exceeded `maxInactiveInterval` since its last access.

### Level 2 — Intermediate

With Redis, expiration is enforced natively — inspecting the key's TTL directly in Redis proves there's no separate cleanup process involved at all.

```bash
# After creating a session via a request, inspect it directly:
redis-cli KEYS "spring:session:sessions:*"
# spring:session:sessions:a1b2c3d4-...

redis-cli TTL "spring:session:sessions:a1b2c3d4-..."
# (integer) 298   <- seconds remaining, counting down natively inside Redis itself
```

```java
// Confirming programmatically that no scheduled Java task is doing this work:
import org.springframework.session.data.redis.RedisIndexedSessionRepository;

public class RedisExpirationNote {
    // RedisIndexedSessionRepository relies entirely on Redis's own EXPIRE mechanism
    // (plus a supporting sorted-set structure it maintains for expired-session cleanup events)
    // — there's no @Scheduled task in the application itself doing a periodic sweep.
}
```

**How to run:** run the `redis-cli TTL` command shown above repeatedly over a couple of minutes against a real session key. Expected output: the returned integer decreases steadily toward zero, entirely driven by Redis's own internal expiration clock — no application code triggered any of these decrements or the eventual key removal.

What changed: this makes visible what was previously invisible — Redis's TTL mechanism is doing all the expiration work at the storage layer itself, which is why Redis-backed Spring Session requires no explicit cleanup configuration to avoid unbounded growth.

### Level 3 — Advanced

JDBC-backed sessions need the opposite: an explicit, correctly scheduled cleanup task, since a relational database will happily keep expired session rows forever unless something deletes them.

```java
// JdbcSessionCleanupConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.springframework.session.jdbc.JdbcIndexedSessionRepository;

import java.time.Duration;

@Configuration
@EnableScheduling // required for the cleanup task's @Scheduled annotation to actually fire
public class JdbcSessionCleanupConfig {

    @Bean
    public JdbcSessionCleanupVerifier cleanupVerifier(JdbcIndexedSessionRepository repository) {
        return new JdbcSessionCleanupVerifier(repository);
    }
}
```

```java
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.scheduling.annotation.Scheduled;

public class JdbcSessionCleanupVerifier {

    private final org.springframework.session.jdbc.JdbcIndexedSessionRepository repository;

    public JdbcSessionCleanupVerifier(org.springframework.session.jdbc.JdbcIndexedSessionRepository repository) {
        this.repository = repository;
        // JdbcIndexedSessionRepository itself schedules its own cleanup via
        // its cleanupAfterMinutes / cleanupCron configuration — this class exists
        // purely to log observable proof that it ran.
    }

    @Scheduled(fixedRate = 70_000) // slightly offset from the library's own default cadence, for observation only
    public void logRowCount(JdbcTemplate jdbcTemplate) {
        Integer count = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM SPRING_SESSION WHERE EXPIRE_TIME < ?",
                Integer.class, System.currentTimeMillis());
        System.out.println("Expired-but-not-yet-cleaned rows: " + count);
    }
}
```

**How to run:** with a JDBC-backed session store (card 0012) and `@EnableScheduling` present, create sessions with a very short `maxInactiveInterval` for testing (e.g. 10 seconds), let them expire, and watch the logged row count. Expected behavior: the count of expired-but-uncleaned rows rises briefly right after expiry, then drops back toward zero as the library's own internal scheduled cleanup task runs and deletes them — proving the cleanup mechanism is active, not merely configured.

What changed and why it's production-flavored: without confirming this cleanup task is actually running (a misconfiguration, like forgetting `@EnableScheduling`, silently disables it), a JDBC-backed session table grows without bound in production — a slow, easy-to-miss storage leak that only becomes obvious weeks or months later when the table's size starts affecting query performance.

## 6. Walkthrough

Tracing the difference between Redis and JDBC expiration end-to-end, in execution order:

1. A session is created with `maxInactiveInterval=30m` (the default) and the user stops interacting with the application.
2. **Redis path:** at creation/save time, `RedisIndexedSessionRepository` issues a Redis `EXPIRE` command (or equivalent) setting a TTL matching the session's inactive interval directly on the underlying key. Redis's own internal expiration mechanism — no application code, no scheduled task — removes the key automatically once the TTL elapses; the next `findById` for that ID simply returns nothing, because the key genuinely no longer exists in Redis.
3. **JDBC path:** at creation/save time, `JdbcIndexedSessionRepository` writes a row with an `EXPIRE_TIME` column set to the computed expiry timestamp — but the row itself remains fully present in the table indefinitely; nothing about a relational database's row storage automatically removes it.
4. `JdbcIndexedSessionRepository` internally registers its own scheduled cleanup task (configurable via `cleanupCron`, defaulting to running roughly once a minute) that executes a `DELETE FROM SPRING_SESSION WHERE EXPIRE_TIME < :now` (approximately) against the table.
5. Until that scheduled task next runs, a JDBC-backed session past its expiry time is technically still present as a row — a subtlety Redis's native TTL doesn't have, since a Redis key past its TTL is gone essentially instantly, not "gone at the next cleanup pass."
6. Either way, once the session is actually gone from the store, the next request bearing that session's now-stale cookie finds nothing on `findById`, and `SessionRepositoryFilter` treats it as a fresh, unauthenticated request — from the application's perspective, expiration behaves identically regardless of which store is underneath.

```
Redis:  save() -> EXPIRE key 1800s -> [Redis internal timer] -> key auto-removed at T+1800s
                                                                       |
                                                          findById() returns null immediately after

JDBC:   save() -> INSERT row (expire_time = now + 1800s)
                                                                       |
                                          row still present until scheduled cleanup task runs
                                                                       |
                                          @Scheduled cleanup: DELETE WHERE expire_time < now
                                                                       |
                                                          findById() returns null only after cleanup runs
```

## 7. Gotchas & takeaways

> A JDBC-backed session repository's scheduled cleanup task requires `@EnableScheduling` (or an equivalent scheduling infrastructure) to actually fire — omitting it doesn't cause an error at startup, but silently means expired session rows are never removed, and the `SPRING_SESSION` table grows without bound until someone notices the storage or query-performance impact.

- With Redis, `findById` on an expired session correctly and immediately returns `null`, since the key is truly gone — application logic can rely on this without any awareness of a cleanup delay.
- With JDBC, there's a real (if usually short) window between a session technically expiring (past its `EXPIRE_TIME`) and the row actually being deleted — `findById` implementations typically still check the expiry timestamp explicitly and treat an expired-but-not-yet-deleted row as absent, so application-visible behavior matches Redis even though the physical row lingers slightly longer.
- Shortening `maxInactiveInterval` reduces the window a stolen or leaked session cookie remains exploitable, a genuine security lever — but weigh it against user experience, since it also means legitimate users get logged out from inactivity more aggressively.
- Monitor `SPRING_SESSION` table row counts (or Redis key counts under the session key prefix) in production as a basic health signal — a steadily growing count that never plateaus is a strong sign the cleanup mechanism (for JDBC) isn't actually running, or that sessions are being created far faster than expected.
- When migrating from Redis to JDBC (or vice versa) for session storage, explicitly verify the new store's expiration mechanics are correctly configured before relying on it in production — the two stores' expiration behavior looks identical from the application's perspective, but the underlying mechanism, and therefore what can go wrong, is completely different.
