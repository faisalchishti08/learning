---
card: spring-session
gi: 2
slug: session-sessionrepository-abstractions
title: "Session & SessionRepository abstractions"
---

## 1. What it is

`Session` and `SessionRepository<S extends Session>` are Spring Session's two core interfaces. `Session` represents one session's data — an ID, attributes, creation and last-accessed timestamps, a max-inactive-interval — independent of any storage technology. `SessionRepository` is the CRUD contract for loading, saving, and deleting `Session` objects, with a different implementation per backing store (`RedisIndexedSessionRepository`, `JdbcIndexedSessionRepository`, `MapSessionRepository`, and others).

## 2. Why & when

Every store-specific piece of Spring Session (Redis, JDBC, MongoDB) needs to expose the same fundamental operations — get a session by ID, save it, delete it, and manage its attributes — but each store has a wildly different native API for doing so (Redis commands versus SQL versus a MongoDB driver). `Session` and `SessionRepository` are the abstraction layer that lets everything above them — the servlet filter, `HttpSession` adaptation, application code — work identically regardless of which concrete store is plugged in underneath.

Reach for understanding this abstraction when:

- Writing code that needs to interact with sessions programmatically outside of a normal request — e.g. an admin tool that looks up and modifies a specific user's session directly via `SessionRepository`, not through `HttpServletRequest`.
- Deciding between storage backends — knowing the shape of `Session`/`SessionRepository` clarifies that switching from Redis to JDBC (cards 0009-0012) is a matter of swapping the repository implementation, not rewriting application logic.
- Debugging a custom `SessionRepository` implementation, or understanding what a store-specific implementation like `RedisIndexedSessionRepository` is actually required to do to satisfy the contract.

## 3. Core concept

Think of `Session` as a standardized shipping manifest form — every shipment (session), regardless of which carrier handles it, gets described using the same fields: contents (attributes), origin/destination timestamps, and an ID. `SessionRepository` is the interface every carrier (storage backend) must implement to accept, store, retrieve, and dispose of shipments described on that standard form. A shipping clerk (application code, or the servlet filter) doesn't need to know whether the manifest ends up on a truck (Redis), a train (JDBC), or a plane (MongoDB) — they just fill out the standard form and hand it to whichever carrier is configured, and get back manifests in that same standard shape regardless of carrier.

```java
public interface SessionRepository<S extends Session> {
    S createSession();
    void save(S session);
    S findById(String id);
    void deleteById(String id);
}
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code depends only on the SessionRepository interface, with different concrete implementations swappable underneath">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SessionRepository</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(interface)</text>

  <rect x="30" y="140" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="162" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RedisIndexed</text>
  <text x="105" y="176" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SessionRepository</text>

  <rect x="245" y="140" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="162" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JdbcIndexed</text>
  <text x="320" y="176" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SessionRepository</text>

  <rect x="460" y="140" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="535" y="162" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MapSession</text>
  <text x="535" y="176" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Repository</text>

  <line x1="105" y1="140" x2="290" y2="70" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="320" y1="140" x2="320" y2="70" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="535" y1="140" x2="350" y2="70" stroke="#8b949e" stroke-width="1.5"/>

  <text x="320" y="230" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SessionRepositoryFilter and application code depend only on the interface at the top</text>
</svg>

Swapping the concrete implementation (Redis to JDBC, say) requires no change above the interface line.

## 5. Runnable example

The scenario: interacting with `SessionRepository` directly and programmatically (outside a normal HTTP request), growing to build a small admin tool that lists and inspects active sessions, and finally to safely modify another user's session attribute from that tool — a realistic "force logout" or "update user preference remotely" feature.

### Level 1 — Basic

```java
// SessionInspector.java
import org.springframework.session.MapSession;
import org.springframework.session.SessionRepository;
import org.springframework.stereotype.Component;

@Component
public class SessionInspector {

    private final SessionRepository<? extends org.springframework.session.Session> sessionRepository;

    public SessionInspector(SessionRepository<? extends org.springframework.session.Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    public String describe(String sessionId) {
        org.springframework.session.Session session = sessionRepository.findById(sessionId);
        if (session == null) {
            return "No session found for ID: " + sessionId;
        }
        return "Session " + session.getId()
                + " created at " + session.getCreationTime()
                + ", last accessed " + session.getLastAccessedTime()
                + ", expires in " + session.getMaxInactiveInterval();
    }
}
```

**How to run:** with any `SessionRepository` bean configured (e.g. Redis, card 0009), inject `SessionInspector` and call `describe(sessionId)` with a real session ID captured from a browser's cookie. Expected output: a description string with the session's real timestamps, fetched directly from the store — not from an active HTTP request.

### Level 2 — Intermediate

Beyond a single lookup, an admin tool typically needs to list *all* sessions for a specific user — this requires the indexed variant of the repository (`FindByIndexNameSessionRepository`, card 0003), which supports lookup by a secondary index like the principal's username.

```java
import org.springframework.session.FindByIndexNameSessionRepository;
import org.springframework.session.Session;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
public class UserSessionLister {

    private final FindByIndexNameSessionRepository<? extends Session> indexedRepository;

    public UserSessionLister(FindByIndexNameSessionRepository<? extends Session> indexedRepository) {
        this.indexedRepository = indexedRepository;
    }

    public Map<String, ? extends Session> listSessionsForUser(String username) {
        return indexedRepository.findByPrincipalName(username);
    }
}
```

**How to run:** log in as the same user from two different browsers (or a browser and an incognito window), then call `listSessionsForUser(username)`. Expected output: a `Map` with two entries, one per active session, keyed by session ID — the first tangible evidence of a user's multiple concurrent sessions, useful for a "your active devices" account settings page.

What changed: the repository abstraction now supports a query pattern (lookup by user, not just by session ID) that a bare `SessionRepository` couldn't express — this is why the indexed variant exists as a distinct, richer interface (card 0003).

### Level 3 — Advanced

A real "force logout this device" or "update a remote session's preference" admin feature must load, mutate, and save a session correctly and atomically enough to avoid clobbering a concurrent write from the session's actual owner — and must handle the session having expired between lookup and save.

```java
import org.springframework.session.Session;
import org.springframework.session.SessionRepository;
import org.springframework.stereotype.Component;

@Component
public class SessionMutator<S extends Session> {

    private final SessionRepository<S> sessionRepository;

    public SessionMutator(SessionRepository<S> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    public boolean forceLogout(String sessionId) {
        S session = sessionRepository.findById(sessionId);
        if (session == null) {
            return false; // already expired or never existed — nothing to do
        }
        sessionRepository.deleteById(session.getId());
        return true;
    }

    public boolean updatePreference(String sessionId, String key, Object value) {
        S session = sessionRepository.findById(sessionId);
        if (session == null) {
            return false; // session expired between the admin's lookup and this action
        }
        session.setAttribute(key, value);
        sessionRepository.save(session); // save() re-persists, extending last-accessed time too
        return true;
    }
}
```

**How to run:** call `forceLogout(sessionId)` for a session belonging to a logged-in test user, then have that user make another request with their existing cookie. Expected behavior: the store no longer has that session ID, so the container treats them as unauthenticated — a real, working "remote sign-out" feature. Then test `updatePreference` against an intentionally expired session ID: expect `false` returned rather than an exception, since `findById` correctly returns `null` for anything the store has already evicted.

What changed and why it's production-flavored: both operations check for `null` before acting, since the session being mutated might expire (or be deleted by its owner logging out) at any moment between the admin action being triggered and it actually executing — a real-world race condition any session-mutating admin feature must handle rather than assume away.

## 6. Walkthrough

Tracing a `SessionRepository`-based lookup and mutation, in execution order:

1. An admin tool calls `sessionMutator.updatePreference(sessionId, "theme", "dark")` for a specific user's session ID, obtained from `UserSessionLister.listSessionsForUser(...)` (Level 2) moments earlier.
2. `SessionMutator` calls `sessionRepository.findById(sessionId)` — for a Redis-backed repository, this issues actual Redis commands (`HGETALL` against the session's hash key, roughly) to reconstruct a `Session` object from the stored data.
3. If the store returns nothing (the session expired in the interval between listing and this call), `findById` returns `null`, and the mutator returns `false` without attempting further action.
4. Assuming the session is found, `session.setAttribute("theme", "dark")` mutates the in-memory `Session` object — at this point, nothing has been written back to the store yet; the change exists only in this local Java object.
5. `sessionRepository.save(session)` is called explicitly (since this isn't happening inside a normal request cycle where `SessionRepositoryFilter` would do this automatically at the end of processing) — this writes the updated attribute back to the store and, depending on implementation, also refreshes the session's expiration timer.
6. The next time the actual user (in their own browser, in a real request) loads their session, `SessionRepositoryFilter` calls the same `findById` internally and the controller sees `theme=dark` via the ordinary `HttpSession` API — the admin-side mutation and the user-side read go through the identical repository contract, just triggered from different code paths.

```
Admin tool: sessionMutator.updatePreference(id, "theme", "dark")
   |
sessionRepository.findById(id)  -- real store round-trip
   |   null (expired) --> return false
   |   found
session.setAttribute("theme", "dark")   -- in-memory only, not yet persisted
   |
sessionRepository.save(session)   -- writes to store
   |
(later) real user's request -> SessionRepositoryFilter -> findById(id) -> sees theme=dark
```

## 7. Gotchas & takeaways

> `Session` objects returned by `findById` are snapshots, not live references — mutating one and forgetting to call `save(...)` afterward silently discards the change, since nothing was ever written back to the store. This is a common mistake when adapting code that's used to `HttpSession`'s implicit auto-save behavior inside `SessionRepositoryFilter`, which doesn't apply when calling the repository directly.

- `SessionRepository<S extends Session>` is generically typed to the concrete `Session` implementation each store uses (`MapSession` for the in-memory variant, a Redis-specific type for Redis) — code written against the generic interface stays portable across stores; code that casts to a store-specific `Session` subtype loses that portability.
- Calling `save(...)` on a session typically refreshes its last-accessed time and, by extension, when it will expire — an admin tool that reads and re-saves sessions purely for inspection (without intending to extend their lifetime) should be aware this side effect exists.
- `findById` returning `null` is the normal, expected outcome for an expired or nonexistent session ID — always check for it explicitly rather than assuming a session found in a prior step (like a listing) is still present moments later.
- The base `SessionRepository` interface alone cannot answer "which sessions belong to user X" — that capability requires the specific `FindByIndexNameSessionRepository` extension (card 0003), which not every store implementation necessarily provides.
- When building tooling that mutates sessions outside a normal request lifecycle, treat it with the same care as any other shared mutable state — a poorly synchronized admin tool can race with, and silently lose to, a legitimate concurrent write from the session's actual owner mid-request.
