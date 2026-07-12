---
card: spring-session
gi: 10
slug: redis-indexed-session-repository
title: "Redis indexed session repository"
---

## 1. What it is

`RedisIndexedSessionRepository` is the concrete Redis-backed implementation of `FindByIndexNameSessionRepository` (card 0003) — it stores session data as a Redis hash per session, and separately maintains Redis sets acting as secondary indexes (most notably, an index from principal name to session IDs) so that queries like "all sessions for user X" are efficient direct lookups rather than a full key scan.

## 2. Why & when

Storing session data alone in Redis (a hash per session key) satisfies the base `SessionRepository` contract, but answering "which sessions belong to user X" against raw Redis hashes would require scanning every session key and inspecting its contents — expensive and something Redis's `KEYS`/`SCAN` commands are explicitly discouraged from being used for at scale. `RedisIndexedSessionRepository` solves this the same way a database adds a secondary index: it maintains an additional Redis data structure (a set, keyed by principal name) that's updated in lockstep with every session write, turning an expensive scan into a fast, direct set lookup.

Reach for understanding `RedisIndexedSessionRepository` specifically (rather than the generic Redis session support) when:

- Building any feature that needs `findByPrincipalName` (card 0003) — active-sessions lists, force-logout-everywhere, concurrent session limits — since this is the concrete class that actually implements that capability for Redis.
- Debugging Redis session data structure directly — knowing that sessions aren't just simple key-value pairs, but a hash plus supporting index sets, is essential for correctly interpreting what's seen when inspecting Redis directly with `redis-cli`.
- Understanding the difference from the simpler `RedisSessionRepository` (card 0011), which trades away the indexing capability for a leaner storage footprint and less write overhead.

## 3. Core concept

Think of a plain Redis hash-per-session as a filing cabinet where each folder (session) is labeled only with its own unique tracking number — fine if a clerk always knows exactly which tracking number to pull, hopeless if asked "pull every folder belonging to this specific client" without checking every folder by hand. `RedisIndexedSessionRepository` adds a card-catalog drawer next to the cabinet — every time a folder is filed or refiled, a card is also updated in the catalog under that client's name, cross-referencing which tracking numbers belong to them. Looking up "everything for this client" now means checking one card in the catalog instead of opening every drawer in the cabinet.

```
Redis structures maintained per session:
  spring:session:sessions:<sessionId>                 <- hash: the actual session data
  spring:session:index:PRINCIPAL_NAME_INDEX_NAME:<user> <- set: session IDs for this user
  spring:session:sessions:expirations:<bucket>          <- supporting structure for expiration
```

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Each session write updates both the session hash and the principal-name index set in Redis together">
  <rect x="20" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sessions:a1b2c3 (hash)</text>
  <text x="160" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">principal=alice, attr:cart=...</text>

  <rect x="20" y="120" width="280" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">index:PRINCIPAL:alice (set)</text>
  <text x="160" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">{a1b2c3, d4e5f6}</text>

  <text x="450" y="55" fill="#e6edf3" font-size="11" font-family="sans-serif">save(session)</text>
  <line x1="380" y1="70" x2="300" y2="50" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="380" y1="70" x2="300" y2="150" stroke="#3fb950" stroke-width="1.5"/>
  <text x="450" y="90" fill="#8b949e" font-size="9" font-family="sans-serif">both updated together</text>
</svg>

Both structures are kept consistent by the same `save()` call — the repository, not the application, guarantees they stay in sync.

## 5. Runnable example

The scenario: inspecting the actual Redis structures `RedisIndexedSessionRepository` creates, growing to build a monitoring tool that reports index-to-session consistency, and finally to handle the edge case where a session's principal changes mid-session (re-authentication) and the index must be correctly updated, not just added to.

### Level 1 — Basic

```bash
# After logging in as "alice" through a Redis-backed session app:
redis-cli KEYS "spring:session:*"
# spring:session:sessions:a1b2c3d4-...
# spring:session:index:org.springframework.session.FindByIndexNameSessionRepository.PRINCIPAL_NAME_INDEX_NAME:alice
# spring:session:sessions:expirations:1234567890

redis-cli HGETALL "spring:session:sessions:a1b2c3d4-..."
# principalName -> "alice"
# sessionAttr:cart -> (serialized data)

redis-cli SMEMBERS "spring:session:index:...PRINCIPAL_NAME_INDEX_NAME:alice"
# "a1b2c3d4-..."
```

**How to run:** log in as a user through an app with `@EnableRedisHttpSession` (card 0009), then run these `redis-cli` commands directly. Expected output: the hash structure holding the actual session data, plus a separate set structure under the principal-name index key containing the same session's ID — direct, visible confirmation of the two-structure design.

### Level 2 — Intermediate

Since these two structures are meant to always stay consistent, a monitoring tool that periodically cross-checks them can catch a real class of bug (a botched manual Redis operation, a partial write from an interrupted process) before it causes confusing application-level symptoms.

```java
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Set;

@Component
public class SessionIndexConsistencyChecker {

    private final StringRedisTemplate redisTemplate;

    public SessionIndexConsistencyChecker(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public void checkConsistency(String principalName) {
        String indexKey = "spring:session:index:org.springframework.session.FindByIndexNameSessionRepository.PRINCIPAL_NAME_INDEX_NAME:"
                + principalName;
        Set<String> indexedSessionIds = redisTemplate.opsForSet().members(indexKey);

        if (indexedSessionIds == null) return;

        for (String sessionId : indexedSessionIds) {
            String sessionKey = "spring:session:sessions:" + sessionId;
            Boolean exists = redisTemplate.hasKey(sessionKey);
            if (Boolean.FALSE.equals(exists)) {
                System.out.println("INCONSISTENCY: index references session " + sessionId
                        + " for " + principalName + ", but the session hash no longer exists");
            }
        }
    }
}
```

**How to run:** call `checkConsistency("alice")` after alice's sessions have expired naturally (letting Redis's own TTL remove the hash, card 0007) but *before* the repository's own index cleanup would run. Expected output in that narrow timing window: potentially an `INCONSISTENCY` line — this is usually transient and self-heals as the repository's own expiration handling catches up, but persistent inconsistencies (found repeatedly across runs) point to a real bug worth investigating.

What changed: this makes the two-structure design's consistency guarantee (normally an invisible implementation detail) directly observable and testable, useful both for building confidence in the mechanism and for catching genuine drift if something outside the library ever manipulates these keys directly.

### Level 3 — Advanced

A session's principal can legitimately change mid-session — a common example is an anonymous session (with no principal indexed) becoming an authenticated one the moment the user logs in partway through — and `RedisIndexedSessionRepository` must correctly add the new index entry and (if a session ever changes from one principal to another entirely, less common but possible) remove any stale one, rather than accumulating incorrect index entries over time.

```java
import jakarta.servlet.http.HttpSession;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class LoginTransitionController {

    @PostMapping("/demo/login-transition")
    public String simulateLoginMidSession(HttpSession session) {
        // Before login: this session has no principal, so it's not in ANY principal-name index yet.
        Object existingContext = session.getAttribute("SPRING_SECURITY_CONTEXT");
        String beforePrincipal = existingContext != null
                ? ((SecurityContext) existingContext).getAuthentication().getName()
                : "none";

        // Simulate authentication completing mid-session, the same way a real login flow
        // (via Spring Security's SecurityContextHolderFilter) would populate this attribute.
        SecurityContext newContext = SecurityContextHolder.createEmptyContext();
        newContext.setAuthentication(new UsernamePasswordAuthenticationToken("alice", null, java.util.List.of()));
        session.setAttribute("SPRING_SECURITY_CONTEXT", newContext);

        return "Before: principal=" + beforePrincipal
                + ". After a real login, RedisIndexedSessionRepository detects the "
                + "principal attribute change on save() and adds this session ID to "
                + "the new principal's index set automatically.";
    }
}
```

**How to run:** start a session anonymously (no login), confirm via `redis-cli` that no principal-name index set yet contains this session's ID. Then complete a real login using that same session (not a fresh one — e.g. add items to a cart anonymously, then log in). Expected behavior: after login, the *same* session ID now appears under the newly authenticated user's principal-name index set — `RedisIndexedSessionRepository` detected the principal attribute being set during `save()` and updated the index accordingly, without the session ID changing and without any manual index management from application code.

What changed and why it's production-flavored: this is exactly the real-world "add to cart anonymously, then log in" flow — the repository's automatic index maintenance is what makes `findByPrincipalName` correctly find this session immediately after login, even though the session itself existed and was already storing data before the user was ever authenticated.

## 6. Walkthrough

Tracing index maintenance across a login transition, in execution order:

1. An anonymous visitor's session is created; `RedisIndexedSessionRepository.save(...)` writes the session hash, but since no `principalName` attribute exists yet, no principal-name index set is touched for this session.
2. The visitor logs in. Spring Security establishes an `Authentication` and stores the resulting `SecurityContext` as a session attribute — a standard part of how Spring Security integrates with `HttpSession`.
3. At the end of this request, `SessionRepositoryFilter` calls `save(...)` again. `RedisIndexedSessionRepository`'s implementation specifically inspects the session for a principal name (by resolving it from the stored `SecurityContext` attribute, following Spring Session's documented convention for this) and, finding one now present where there wasn't before, adds this session's ID to `index:...PRINCIPAL_NAME_INDEX_NAME:<username>`.
4. From this point forward, `findByPrincipalName(username)` (card 0003) correctly includes this session — even though the session's own ID never changed and it existed, with real data, before the user ever authenticated.
5. If the user later logs out (`session.invalidate()`), the repository's deletion path removes both the session hash *and* the corresponding entry from the principal-name index set, keeping the two structures consistent in the other direction too.

```
Anonymous session created -> save() -> hash written, no principal index entry (no principal yet)
   |
user logs in -> SecurityContext attribute set on session
   |
save() called again -> repository detects principal now present
   |
   -> SADD index:PRINCIPAL_NAME_INDEX_NAME:alice <sessionId>
   |
findByPrincipalName("alice") now includes this session
   |
(later) logout -> session.invalidate() -> hash deleted AND index entry removed together
```

## 7. Gotchas & takeaways

> Never manipulate the Redis index sets directly (via raw `SADD`/`SREM` outside the library's own code path) — doing so risks the two structures (session hash and index set) drifting out of sync, since only `RedisIndexedSessionRepository`'s own save/delete logic knows how to keep them consistent together; Level 2's consistency checker exists precisely to catch this kind of drift, not to be a substitute for it.

- The principal-name index is populated based on a specific, documented session attribute convention (tied to how the `Authentication`'s name is stored) — a custom authentication mechanism that stores the user's identity under a different, non-standard attribute name won't be picked up by the index automatically without extra configuration.
- `RedisIndexedSessionRepository` does more writes per session save than the simpler `RedisSessionRepository` (card 0011), since it maintains index structures in addition to the raw session hash — this is a deliberate, worthwhile trade for indexed-lookup capability, but it's not free, and matters when comparing write-throughput benchmarks between the two.
- Index sets are cleaned up as part of the same expiration/deletion handling that removes the session hash itself — a correctly functioning setup shouldn't accumulate stale index entries for genuinely expired sessions over time; persistent staleness is a sign something (a misconfiguration, a manual Redis intervention) is interfering with the repository's normal lifecycle handling.
- When debugging "findByPrincipalName returns nothing for a user I know is logged in," check first whether the session's principal was actually established through the mechanism the index expects (usually via Spring Security's standard `SecurityContext` session attribute) before assuming the indexing itself is broken.
- Redis key naming for these structures follows a documented, stable convention (`spring:session:sessions:*`, `spring:session:index:*`) — useful to know when writing monitoring, debugging, or migration tooling that needs to interact with the raw Redis keyspace directly rather than through the repository API.
