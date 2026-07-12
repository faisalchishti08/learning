---
card: spring-session
gi: 3
slug: findbyindexnamesessionrepository
title: "FindByIndexNameSessionRepository"
---

## 1. What it is

`FindByIndexNameSessionRepository<S extends Session>` extends the base `SessionRepository` with `findByIndexNameAndIndexValue(indexName, indexValue)` (and the convenience method `findByPrincipalName(principalName)`), letting sessions be looked up by an arbitrary secondary attribute — most commonly, the authenticated user's name — instead of only by session ID.

## 2. Why & when

The base `SessionRepository` (card 0002) only supports lookup by session ID, which is fine for the normal request path (the cookie always carries the ID), but useless for the very common real-world need: "find every active session belonging to user X." A base repository would require scanning every session in the store and checking each one's attributes — expensive and not something most stores support efficiently anyway. `FindByIndexNameSessionRepository` solves this by maintaining a proper secondary index at write time, so lookups by principal name are a direct, efficient query rather than a full scan.

Reach for this interface when:

- Building an "active sessions" or "manage your devices" account settings page, where a user needs to see and selectively revoke their own concurrent sessions.
- Implementing "force logout everywhere" after a password change or a suspected account compromise — this requires finding *all* sessions for a user, not just the one making the current request.
- Enforcing a maximum concurrent session limit per user — checking how many sessions already exist for a principal before allowing a new login.

## 3. Core concept

Think of the base `SessionRepository` as a library where books (sessions) are shelved only by their unique catalog number (session ID) — fast if you already know the number, but hopeless if you only know "find me every book checked out by this specific patron." `FindByIndexNameSessionRepository` is the library adding a second card catalog, cross-referenced by patron name, maintained automatically every time a book is checked in or out — so "show me everything patron X currently has" becomes a direct catalog lookup instead of walking every shelf in the building.

```java
Map<String, ? extends Session> sessions =
    indexedRepository.findByPrincipalName("alice");
// {"a1b2c3...": Session, "d4e5f6...": Session}  <- two devices, both logged in as alice
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sessions are indexed both by their own ID and by principal name, allowing lookup either way">
  <rect x="20" y="30" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Session ID index</text>

  <rect x="20" y="140" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Principal name index</text>

  <rect x="330" y="30" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="400" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Session a1b2c3</text>

  <rect x="330" y="140" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="400" y="168" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Session d4e5f6</text>

  <line x1="200" y1="53" x2="325" y2="53" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="200" y1="163" x2="325" y2="53" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="200" y1="163" x2="325" y2="163" stroke="#3fb950" stroke-width="1.5"/>

  <text x="400" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">both sessions belong to the same principal "alice"</text>
</svg>

Both indexes point at the same underlying session records — the index type used just determines the query pattern available.

## 5. Runnable example

The scenario: building an "active sessions" list for a logged-in user, growing to add a "force logout everywhere else" button, and finally to enforce a maximum concurrent session limit per user at login time.

### Level 1 — Basic

```java
// ActiveSessionsController.java
import org.springframework.security.core.Authentication;
import org.springframework.session.FindByIndexNameSessionRepository;
import org.springframework.session.Session;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
public class ActiveSessionsController {

    private final FindByIndexNameSessionRepository<? extends Session> sessionRepository;

    public ActiveSessionsController(FindByIndexNameSessionRepository<? extends Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @GetMapping("/account/sessions")
    public Map<String, ? extends Session> listMySessions(Authentication authentication) {
        return sessionRepository.findByPrincipalName(authentication.getName());
    }
}
```

**How to run:** with a Redis- or JDBC-backed indexed session repository (card 0010 or 0013) and Spring Security wired so authenticated sessions register the principal name index, log in from two different browsers as the same user, then `curl` `/account/sessions` with either session's cookie. Expected output: a JSON map with two entries — one per active login — both keyed by their respective session IDs.

### Level 2 — Intermediate

A real settings page lets a user revoke every session *except* the one they're currently using — deleting the current session out from under the active request would immediately log them out too, which is rarely the intended behavior for this specific button.

```java
import org.springframework.security.core.Authentication;
import org.springframework.session.FindByIndexNameSessionRepository;
import org.springframework.session.Session;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import jakarta.servlet.http.HttpServletRequest;

@RestController
public class LogoutOthersController {

    private final FindByIndexNameSessionRepository<? extends Session> sessionRepository;

    public LogoutOthersController(FindByIndexNameSessionRepository<? extends Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    @PostMapping("/account/sessions/logout-others")
    public String logoutOtherSessions(Authentication authentication, HttpServletRequest request) {
        String currentSessionId = request.getSession(false).getId();
        var sessions = sessionRepository.findByPrincipalName(authentication.getName());

        int revoked = 0;
        for (String sessionId : sessions.keySet()) {
            if (!sessionId.equals(currentSessionId)) {
                sessionRepository.deleteById(sessionId);
                revoked++;
            }
        }
        return "Revoked " + revoked + " other session(s).";
    }
}
```

**How to run:** log in as the same user from three browsers, note which one issues the request, then call `/account/sessions/logout-others` from that browser. Expected behavior: the calling browser stays logged in; the other two are immediately signed out on their next request (their session ID no longer resolves in the store).

What changed: the current session is deliberately excluded from the revocation set — a small but important detail, since indiscriminately deleting every session for the principal (including the current one) would log the user out of the very page they just used to trigger the action.

### Level 3 — Advanced

Production systems often cap concurrent sessions per user (e.g. "maximum 5 active devices") — this requires checking the index *before* allowing a new session to be fully established, and deciding a policy for what happens when the limit is exceeded (reject the new login, or evict the oldest session).

```java
import org.springframework.session.FindByIndexNameSessionRepository;
import org.springframework.session.Session;

import java.util.Comparator;
import java.util.Map;

public class ConcurrentSessionLimiter {

    private static final int MAX_SESSIONS_PER_USER = 5;

    private final FindByIndexNameSessionRepository<? extends Session> sessionRepository;

    public ConcurrentSessionLimiter(FindByIndexNameSessionRepository<? extends Session> sessionRepository) {
        this.sessionRepository = sessionRepository;
    }

    public void enforceLimit(String principalName) {
        Map<String, ? extends Session> sessions = sessionRepository.findByPrincipalName(principalName);
        if (sessions.size() <= MAX_SESSIONS_PER_USER) {
            return;
        }

        // Policy: evict the oldest (least-recently-created) session(s) to make room,
        // rather than rejecting the new login outright.
        sessions.values().stream()
                .sorted(Comparator.comparing(Session::getCreationTime))
                .limit(sessions.size() - MAX_SESSIONS_PER_USER)
                .forEach(session -> sessionRepository.deleteById(session.getId()));
    }
}
```

**How to run:** call `enforceLimit(username)` immediately after a successful login completes (e.g. from an `AuthenticationSuccessHandler`). Simulate 6 logins for the same user across different simulated devices: expect exactly 5 sessions to remain after the 6th login, with the oldest one evicted — that device's next request finds its session gone and must re-authenticate.

What changed and why it's production-flavored: this is a real security control (limiting the blast radius of a leaked session by capping how many can exist simultaneously) built entirely on the indexed lookup this card introduces — without `findByPrincipalName`, computing "how many sessions does this user currently have" would require an expensive full scan of every session in the store.

## 6. Walkthrough

Tracing a new login against a session-limited system, in execution order:

1. A user successfully authenticates for the 6th time on a 6th device, while already having 5 active sessions elsewhere.
2. Spring Security's session creation, combined with Spring Session's index maintenance, registers this new session under the principal-name index alongside the existing 5.
3. `ConcurrentSessionLimiter.enforceLimit(...)` (Level 3) runs post-login, calling `findByPrincipalName(...)` — this hits the maintained secondary index directly (an efficient, targeted query for the backing store, not a scan) and returns all 6 sessions.
4. Since 6 exceeds the configured maximum of 5, the limiter sorts sessions by creation time and identifies the single oldest one for eviction.
5. `sessionRepository.deleteById(...)` removes that oldest session from the store entirely — both from the primary session-ID storage and from the principal-name index, since a correct indexed repository implementation keeps both in sync automatically.
6. The device that owned the now-deleted session makes its next request; `SessionRepositoryFilter` finds no session for its cookie's ID, treats the request as unauthenticated, and that device is forced to log in again — a real, observable consequence of the limit being enforced.

```
6th login succeeds -> session created, indexed under principal="alice"
   |
enforceLimit("alice")
   |
findByPrincipalName("alice") -> 6 sessions found (indexed lookup, not a scan)
   |
6 > MAX(5) -> sort by creation time -> evict oldest
   |
deleteById(oldestSessionId) -> removed from both ID index and principal index
   |
(later) oldest device's next request -> session not found -> forced re-login
```

## 7. Gotchas & takeaways

> `findByPrincipalName` only returns results for sessions that were actually indexed under a principal name in the first place — an anonymous, unauthenticated session (one that never had Spring Security establish a principal) simply won't appear in these results, which can look like "missing sessions" if the indexing mechanism isn't wired up correctly for the app's authentication flow.

- The principal name used for indexing typically comes from Spring Security's `Authentication.getName()` at the point a `SecurityContext` is established in the session — a custom authentication setup that doesn't populate this the standard way needs to explicitly register the index itself for `findByPrincipalName` to work.
- Not every `SessionRepository` implementation implements `FindByIndexNameSessionRepository` — check that the specific store's Spring Session module (Redis, JDBC) supports indexed lookups before designing a feature around it; a bare in-memory `MapSessionRepository` for local testing, for instance, may not.
- Deleting a session via `deleteById` from an admin or self-service tool takes effect on that session's *next* request, not instantly on any already-in-flight request that device might currently be processing — there's a small window where an in-progress request can still complete using the now-revoked session.
- When implementing a concurrent session limit (Level 3), decide the eviction policy deliberately — evicting the oldest session is one reasonable default, but some products prefer rejecting the new login outright, or notifying the user which device was signed out, rather than silently evicting in the background.
- Index maintenance has a cost at write time (every session save also updates the secondary index) — this is a reasonable trade for most applications, but it's worth knowing the mechanism exists if profiling ever points at unexpectedly heavy session-write latency in an indexed configuration.
