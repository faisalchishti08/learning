---
card: spring-security
gi: 16
slug: securitycontextrepository-persistence
title: "SecurityContextRepository / persistence"
---

## 1. What it is

`SecurityContextRepository` is the interface (`loadContext`, `saveContext`, `containsContext`) responsible for persisting the `SecurityContext` between requests — since HTTP is stateless and a new `SecurityContext` is created fresh for every request, something has to save an authenticated context somewhere after login and reload it on every subsequent request, or the user would have to re-authenticate on every single call. `HttpSessionSecurityContextRepository` (session-backed, the default for form login) and `RequestAttributeSecurityContextRepository` (request-scoped only, typical for stateless APIs) are the two built-in implementations, and `SecurityContextHolderFilter` is the filter that invokes this repository at the start and end of every request.

```java
public interface SecurityContextRepository {
    SecurityContext loadContext(HttpRequestResponseHolder requestResponseHolder);
    void saveContext(SecurityContext context, HttpServletRequest request, HttpServletResponse response);
    boolean containsContext(HttpServletRequest request);
}
```

## 2. Why & when

Authenticating a user (validating credentials, building an `Authentication` with roles) is meaningful work that should not have to repeat on every single request a user makes — but `SecurityContextHolder` itself is only ever populated per-request, using a `ThreadLocal` by default, and is cleared once the request completes. `SecurityContextRepository` is the piece that bridges these two facts: it decides *where* the authenticated context is stored between requests (an `HttpSession`, nowhere at all) and reloads it at the start of each new request, so `SecurityContextHolder` appears to "remember" the login even though, mechanically, a brand new context object is populated fresh every time.

Reach for understanding (or explicitly configuring) `SecurityContextRepository` when:

- Building a stateless REST API where session-based persistence is explicitly unwanted — every request should be independently authenticated (via a bearer token, for instance), and no `SecurityContext` should ever be written to an `HttpSession`; this is exactly what `securityContext(context -> context.securityContextRepository(new RequestAttributeSecurityContextRepository()))` or `.sessionManagement(session -> session.sessionCreationPolicy(STATELESS))` configures.
- Debugging why a user appears to be logged out unexpectedly on a later request — the answer is usually that no context was actually persisted (or that the session backing it expired, or wasn't found), so `loadContext` returned an empty context for the new request.
- Implementing a custom persistence mechanism — for example, storing the context in a distributed cache shared across multiple application instances, rather than in a single server's in-memory `HttpSession`.

## 3. Core concept

```
 request 1 (login):
   SecurityContextHolderFilter.doFilter():
     context = repository.loadContext(...)          -- EMPTY, nothing persisted yet
     ... authentication happens, context now holds an Authentication ...
     repository.saveContext(context, request, response)   -- PERSISTED (e.g. into the HttpSession)

 request 2 (later, same session):
   SecurityContextHolderFilter.doFilter():
     context = repository.loadContext(...)          -- RELOADED from the HttpSession, already authenticated
     SecurityContextHolder.setContext(context)        -- available to the rest of THIS request's filters/controller
```

Without a repository actively saving and reloading, every request would see an empty `SecurityContext`, regardless of any earlier successful login.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Request one logs in and SecurityContextRepository saves the resulting SecurityContext into the HttpSession request two loads the same context back out of the session reproducing the authenticated state without re-authenticating">
  <rect x="10" y="30" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="100" y="50" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">request 1: login</text>
  <text x="100" y="63" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">saveContext(...)</text>

  <rect x="230" y="55" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">HttpSession</text>
  <text x="320" y="88" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">SecurityContext stored</text>

  <rect x="450" y="105" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="125" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">request 2: later call</text>
  <text x="540" y="138" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">loadContext(...) -&gt; authenticated</text>

  <defs><marker id="a16" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="190" y1="60" x2="230" y2="75" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a16)"/>
  <line x1="410" y1="90" x2="450" y2="120" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a16)"/>
</svg>

The `HttpSession` in the middle is what lets request 2's `SecurityContext` look identical to request 1's, without the user re-authenticating.

## 5. Runnable example

The scenario: model `SecurityContextRepository` backed by a simple in-memory session map, then show a second, stateless repository implementation for comparison, then wire in expiry so a stale session correctly reloads as unauthenticated.

### Level 1 — Basic

A minimal session-backed repository: save writes into a map, load reads back out of it.

```java
import java.util.*;

public class ContextRepoLevel1 {
    record SecurityContext(String principal, Set<String> roles) {
        static final SecurityContext EMPTY = new SecurityContext(null, Set.of());
    }

    static class HttpSessionSecurityContextRepository {
        private final Map<String, SecurityContext> sessions = new HashMap<>();

        SecurityContext loadContext(String sessionId) {
            return sessions.getOrDefault(sessionId, SecurityContext.EMPTY);
        }

        void saveContext(String sessionId, SecurityContext context) {
            sessions.put(sessionId, context);
        }
    }

    public static void main(String[] args) {
        HttpSessionSecurityContextRepository repository = new HttpSessionSecurityContextRepository();
        String sessionId = "JSESSIONID-abc123";

        System.out.println("request 1, before login: " + repository.loadContext(sessionId));

        SecurityContext afterLogin = new SecurityContext("alice", Set.of("ROLE_USER"));
        repository.saveContext(sessionId, afterLogin);

        System.out.println("request 2, same session: " + repository.loadContext(sessionId));
    }
}
```

How to run: `java ContextRepoLevel1.java`

The first `loadContext` call returns `SecurityContext.EMPTY` since nothing has been saved for this `sessionId` yet; after `saveContext` runs (simulating a successful login), the second `loadContext` call for the *same* `sessionId` returns the authenticated context — the map is standing in for the servlet container's real `HttpSession` store.

### Level 2 — Intermediate

Add a second, stateless repository implementation, and a switch showing both plugged in behind the same interface — mirroring the real choice between session-based and request-attribute-based persistence.

```java
import java.util.*;

public class ContextRepoLevel2 {
    record SecurityContext(String principal, Set<String> roles) {
        static final SecurityContext EMPTY = new SecurityContext(null, Set.of());
    }

    interface SecurityContextRepository {
        SecurityContext loadContext(String requestId);
        void saveContext(String requestId, SecurityContext context);
    }

    static class HttpSessionSecurityContextRepository implements SecurityContextRepository {
        private final Map<String, SecurityContext> sessions = new HashMap<>();
        public SecurityContext loadContext(String sessionId) { return sessions.getOrDefault(sessionId, SecurityContext.EMPTY); }
        public void saveContext(String sessionId, SecurityContext context) { sessions.put(sessionId, context); }
    }

    // stateless: NOTHING persists between requests -- every call must re-authenticate (e.g. via a bearer token, checked elsewhere)
    static class RequestAttributeSecurityContextRepository implements SecurityContextRepository {
        public SecurityContext loadContext(String requestId) { return SecurityContext.EMPTY; }
        public void saveContext(String requestId, SecurityContext context) { /* intentionally a no-op across requests */ }
    }

    static void simulateTwoRequests(SecurityContextRepository repository, String id) {
        System.out.println("  before login: " + repository.loadContext(id));
        repository.saveContext(id, new SecurityContext("alice", Set.of("ROLE_USER")));
        System.out.println("  next request: " + repository.loadContext(id));
    }

    public static void main(String[] args) {
        System.out.println("session-backed repository:");
        simulateTwoRequests(new HttpSessionSecurityContextRepository(), "JSESSIONID-abc123");

        System.out.println("stateless repository:");
        simulateTwoRequests(new RequestAttributeSecurityContextRepository(), "req-xyz");
    }
}
```

How to run: `java ContextRepoLevel2.java`

Both repositories implement the identical `SecurityContextRepository` interface, but `RequestAttributeSecurityContextRepository`'s `loadContext` always returns `EMPTY` regardless of any prior `saveContext` call — a deliberate design for stateless APIs, where every request is expected to carry its own independent proof of identity (a token) rather than relying on server-side persisted state.

### Level 3 — Advanced

Add session expiry to the session-backed repository, so a context saved too long ago correctly reloads as unauthenticated — modeling real `HttpSession` timeout behavior.

```java
import java.util.*;

public class ContextRepoLevel3 {
    record SecurityContext(String principal, Set<String> roles) {
        static final SecurityContext EMPTY = new SecurityContext(null, Set.of());
    }
    record SessionEntry(SecurityContext context, long savedAtMillis) {}

    static class ExpiringSessionRepository {
        private final Map<String, SessionEntry> sessions = new HashMap<>();
        private final long maxAgeMillis;

        ExpiringSessionRepository(long maxAgeMillis) { this.maxAgeMillis = maxAgeMillis; }

        SecurityContext loadContext(String sessionId, long nowMillis) {
            SessionEntry entry = sessions.get(sessionId);
            if (entry == null) return SecurityContext.EMPTY;
            if (nowMillis - entry.savedAtMillis() > maxAgeMillis) {
                sessions.remove(sessionId); // expired session is discarded, not just ignored
                return SecurityContext.EMPTY;
            }
            return entry.context();
        }

        void saveContext(String sessionId, SecurityContext context, long nowMillis) {
            sessions.put(sessionId, new SessionEntry(context, nowMillis));
        }
    }

    public static void main(String[] args) {
        ExpiringSessionRepository repository = new ExpiringSessionRepository(30 * 60 * 1000L); // 30 minutes
        String sessionId = "JSESSIONID-abc123";
        long loginTime = 0L;

        repository.saveContext(sessionId, new SecurityContext("alice", Set.of("ROLE_USER")), loginTime);

        long fiveMinutesLater = loginTime + 5 * 60 * 1000L;
        System.out.println("5 min later: " + repository.loadContext(sessionId, fiveMinutesLater));

        long fortyMinutesLater = loginTime + 40 * 60 * 1000L;
        System.out.println("40 min later: " + repository.loadContext(sessionId, fortyMinutesLater));
    }
}
```

How to run: `java ContextRepoLevel3.java`

`loadContext` now compares the current time against `savedAtMillis`; five minutes after login it correctly returns the still-valid authenticated context, but forty minutes later — past the configured thirty-minute `maxAgeMillis` — it removes the stale entry and returns `SecurityContext.EMPTY`, exactly reproducing the observable effect of an `HttpSession` timing out and forcing the user to log in again.

## 6. Walkthrough

Trace Level 3's two `loadContext` calls in order.

1. `repository.saveContext(sessionId, ..., loginTime)` runs first, storing a `SessionEntry` with `savedAtMillis = 0` for `"JSESSIONID-abc123"` in the `sessions` map — this models the moment `SecurityContextHolderFilter` persists the context after a successful login.
2. `repository.loadContext(sessionId, fiveMinutesLater)` runs next, with `fiveMinutesLater = 300000`; it finds the entry, computes `nowMillis - entry.savedAtMillis() = 300000 - 0 = 300000`, compares it against `maxAgeMillis = 1800000`, finds it well under the limit, and returns `entry.context()` unchanged — the authenticated `SecurityContext` for alice.
3. `repository.loadContext(sessionId, fortyMinutesLater)` runs last, with `fortyMinutesLater = 2400000`; it finds the same entry, computes `2400000 - 0 = 2400000`, compares it against `1800000`, finds it *exceeds* the limit, calls `sessions.remove(sessionId)` to discard the now-expired entry, and returns `SecurityContext.EMPTY`.
4. In a real application, this final case is exactly what causes `SecurityContextHolderFilter` to populate `SecurityContextHolder` with an empty context for that request — any subsequent `AuthorizationFilter` check then sees no principal and throws `AuthenticationException`, which `ExceptionTranslationFilter` (the previous card) routes to the configured `AuthenticationEntryPoint`, typically redirecting the user back to a login page.

```
t=0min:   saveContext -> session stores {alice, ROLE_USER} at t=0
t=5min:   loadContext -> age=5min  < 30min limit -> returns {alice, ROLE_USER}
t=40min:  loadContext -> age=40min > 30min limit -> entry removed, returns EMPTY
```

## 7. Gotchas & takeaways

> **Gotcha:** setting `sessionCreationPolicy(STATELESS)` (which effectively swaps in a no-op repository like `RequestAttributeSecurityContextRepository`) while still relying on form-login's default session-based persistence elsewhere in the same configuration is a common misconfiguration — the user appears to authenticate successfully, but every subsequent request reloads an empty context, since nothing was actually persisted anywhere durable.

- `SecurityContextRepository` bridges the gap between HTTP's inherent statelessness and an application's need to "remember" an authenticated user across multiple requests, by explicitly saving and reloading the `SecurityContext`.
- `HttpSessionSecurityContextRepository` (session-backed) is the right choice for traditional server-rendered, cookie-based applications; a stateless repository (or `sessionCreationPolicy(STATELESS)`) is the right choice for token-authenticated APIs where every request should independently prove its own identity.
- `SecurityContextHolderFilter` is the filter that actually invokes `loadContext` at the start of a request and (depending on configuration) `saveContext` at the end — this repository is not consulted anywhere else in the chain.
- Session or context expiry is handled entirely inside the repository implementation — understanding *where* and *how* expiry is checked is essential for correctly debugging an unexpected forced re-login.
