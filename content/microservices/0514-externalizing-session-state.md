---
card: microservices
gi: 514
slug: externalizing-session-state
title: "Externalizing session state"
---

## 1. What it is

**Externalizing session state** means moving user session data — login status, shopping cart contents, in-progress multi-step form data — out of a service instance's own in-process memory and into a shared, external store (typically a distributed cache like Redis, or a database) that every instance can access equally. It's the concrete, most common application of [statelessness](0513-stateless-services-for-scaling.md) — session data is usually the single biggest source of accidental in-memory state in a typical web application.

## 2. Why & when

You externalize session state specifically because in-memory HTTP sessions are the most common way a service accidentally becomes stateful without anyone deciding that on purpose:

- **Traditional web framework defaults often store sessions in server memory**, tied to a session cookie — this is a completely reasonable default for a single-server application, but it silently breaks the moment you run more than one instance behind a load balancer, since a session created on instance A is invisible to instance B.
- **Sticky sessions are a common but incomplete workaround.** Configuring the load balancer to always route a given client back to the same instance keeps in-memory sessions technically working, but reintroduces exactly the fragility [statelessness](0513-stateless-services-for-scaling.md) is meant to eliminate — that one instance restarting or scaling down loses every session stuck to it.
- **Externalizing to a shared store is what actually fixes the root cause**, rather than working around it — once session data lives in Redis (or similar), any instance can correctly serve any request for any session, with no dependency on which instance a client happened to hit previously.
- **You externalize session state as one of the very first steps when converting a service to run multiple horizontally-scaled instances** — it's usually the single highest-impact change, since session data is so commonly the source of a service's accidental statefulness.

## 3. Core concept

Think of a coat check at a large venue with multiple entrances: rather than each entrance's coat check having its own separate rack (meaning you'd have to exit through the same entrance you came in, or lose your coat), the venue uses one shared, centralized coat check that any entrance's staff can access — you can enter through any door and retrieve your coat through any door, because the actual storage is centralized and shared, not tied to wherever you happened to walk in.

Concretely:

1. **A session identifier travels with each request** — typically a cookie or a token — that any instance can use to look up the session's actual data.
2. **The session's actual data lives in a shared external store** (Redis is extremely common for this specific purpose, given its speed and native support for exactly this kind of key-value session data), not in any individual instance's memory.
3. **Reading session data on any request means looking it up from the shared store** using the session identifier — an instance that's never seen this specific client before can still correctly retrieve their session state.
4. **Writing to session data means updating the shared store**, not a local in-memory structure — so the update is immediately visible to whichever instance handles the client's *next* request, wherever that request happens to land.
5. **Session expiry is typically handled via the external store's own TTL mechanism** — Redis, for example, can automatically expire a session key after a period of inactivity, without any instance needing to run its own cleanup logic.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Instead of each instance holding its own private session store, all instances read from and write to one shared external session store, keyed by session ID">
  <rect x="20" y="20" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="45" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance A</text>

  <rect x="20" y="140" width="130" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="85" y="165" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">instance B</text>

  <rect x="420" y="70" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="520" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">shared session store</text>
  <text x="520" y="113" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">e.g. Redis, keyed by session ID</text>

  <line x1="150" y1="40" x2="420" y2="90" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="150" y1="160" x2="420" y2="110" stroke="#8b949e" marker-end="url(#a1)"/>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Every instance reads and writes the same shared session store, rather than keeping its own private copy.

## 5. Runnable example

Scenario: a login session tracked across requests. We start with a basic in-memory session store demonstrating the classic breakage, extend it to an externalized shared store fixing it, then handle the hard case: session expiry via TTL, correctly implemented so an idle session expires while an active one stays alive, matching a real Redis-backed session store's typical behavior.

### Level 1 — Basic

```java
// File: InMemorySessionBroken.java -- models the CLASSIC problem:
// session data stored in EACH instance's OWN memory, breaking the moment
// a client's requests land on a DIFFERENT instance.
import java.util.*;

public class InMemorySessionBroken {
    static class ServiceInstance {
        String name;
        Map<String, String> localSessions = new HashMap<>(); // sessionId -> username

        ServiceInstance(String name) { this.name = name; }

        void login(String sessionId, String username) {
            localSessions.put(sessionId, username);
            System.out.println("[" + name + "] logged in '" + username + "', session stored LOCALLY");
        }

        String getLoggedInUser(String sessionId) {
            return localSessions.get(sessionId);
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        String sessionId = "sess-abc123";
        instanceA.login(sessionId, "alice"); // login request -> instance A

        String user = instanceB.getLoggedInUser(sessionId); // a LATER request -> instance B
        System.out.println("[result] instance-B sees logged-in user: " + user + " -- alice appears LOGGED OUT, even though she just logged in!");
    }
}
```

How to run: `java InMemorySessionBroken.java`

`localSessions` is a plain field on each `ServiceInstance` object, entirely private to it — `instanceA.login` writes only into `instanceA`'s own map, so when `instanceB.getLoggedInUser` is called for the same session ID, it finds nothing at all, since `instanceB` never received or shares `instanceA`'s in-memory data.

### Level 2 — Intermediate

```java
// File: ExternalizedSessionFixed.java -- the SAME login flow, now with
// session data EXTERNALIZED to a SHARED store -- ANY instance can
// correctly see ANY other instance's session writes.
import java.util.*;

public class ExternalizedSessionFixed {
    // The SHARED, external session store -- not owned by any single instance.
    static Map<String, String> sharedSessionStore = new HashMap<>();

    static class ServiceInstance {
        String name;
        ServiceInstance(String name) { this.name = name; }

        void login(String sessionId, String username) {
            sharedSessionStore.put(sessionId, username);
            System.out.println("[" + name + "] logged in '" + username + "', session stored in SHARED store");
        }

        String getLoggedInUser(String sessionId) {
            return sharedSessionStore.get(sessionId);
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        String sessionId = "sess-abc123";
        instanceA.login(sessionId, "alice");

        String user = instanceB.getLoggedInUser(sessionId);
        System.out.println("[result] instance-B sees logged-in user: " + user + " -- CORRECT, alice stays logged in regardless of routing");
    }
}
```

How to run: `java ExternalizedSessionFixed.java`

`sharedSessionStore` is accessible identically to both `instanceA` and `instanceB` — neither one privately owns it. `instanceB.getLoggedInUser` correctly retrieves `"alice"`, since it's reading from the same underlying store `instanceA.login` wrote into, entirely independent of which instance handled which request.

### Level 3 — Advanced

```java
// File: ExternalizedSessionWithTtl.java -- the SAME externalized session
// store, now handling the PRODUCTION-FLAVORED hard case: SESSION EXPIRY.
// An IDLE session (no activity for a while) must EXPIRE automatically,
// while an ACTIVE session (recently used) must STAY alive -- matching how
// a real Redis-backed session store with a sliding TTL actually behaves.
import java.util.*;

public class ExternalizedSessionWithTtl {
    record SessionData(String username, long expiresAtMs) {}
    static Map<String, SessionData> sharedSessionStore = new HashMap<>();
    static long sessionTtlMs = 100;

    static void login(String sessionId, String username) {
        long expiresAt = System.currentTimeMillis() + sessionTtlMs;
        sharedSessionStore.put(sessionId, new SessionData(username, expiresAt));
        System.out.println("[login] session '" + sessionId + "' created, expires in " + sessionTtlMs + "ms unless refreshed");
    }

    // Reading a session ALSO refreshes its TTL -- a "sliding" expiry, exactly like typical
    // real session stores: activity keeps a session alive, inactivity lets it expire.
    static String getLoggedInUserAndRefresh(String sessionId) {
        SessionData data = sharedSessionStore.get(sessionId);
        long now = System.currentTimeMillis();
        if (data == null || now >= data.expiresAtMs()) {
            System.out.println("[session check] '" + sessionId + "' is EXPIRED or absent -- treated as logged out");
            sharedSessionStore.remove(sessionId);
            return null;
        }
        // Activity detected -- REFRESH (slide forward) the expiry.
        sharedSessionStore.put(sessionId, new SessionData(data.username(), now + sessionTtlMs));
        System.out.println("[session check] '" + sessionId + "' active -- user=" + data.username() + ", TTL refreshed");
        return data.username();
    }

    public static void main(String[] args) throws InterruptedException {
        login("sess-active", "alice");
        login("sess-idle", "bob");

        System.out.println();
        System.out.println("--- 'alice' stays ACTIVE, making requests every 40ms, well within the 100ms TTL ---");
        for (int i = 0; i < 3; i++) {
            Thread.sleep(40);
            getLoggedInUserAndRefresh("sess-active"); // keeps refreshing, staying alive
        }

        System.out.println();
        System.out.println("--- 'bob' goes IDLE for 150ms, exceeding the 100ms TTL with no activity ---");
        Thread.sleep(150);

        System.out.println();
        System.out.println("--- final check on BOTH sessions ---");
        String aliceStatus = getLoggedInUserAndRefresh("sess-active");
        String bobStatus = getLoggedInUserAndRefresh("sess-idle");
        System.out.println("[result] alice: " + aliceStatus + " (still logged in, was active) | bob: " + bobStatus + " (expired, was idle)");
    }
}
```

How to run: `java ExternalizedSessionWithTtl.java`

`getLoggedInUserAndRefresh` both checks expiry *and* refreshes the TTL on every successful access — this is a sliding-window expiry, matching how many real session stores behave. `"sess-active"` is accessed three times, each roughly `40ms` apart, and each access refreshes its expiry before the previous window would have run out, so it never actually expires. `"sess-idle"` is never accessed at all during a `150ms` gap, exceeding its `100ms` TTL with no refreshing activity, so it correctly expires by the time it's finally checked.

## 6. Walkthrough

Trace `ExternalizedSessionWithTtl.main` in order. **First**, both `login` calls create sessions, each with `expiresAtMs` set to `100ms` from their respective creation times.

**Next**, the loop runs three iterations for `"sess-active"`, each preceded by a `40ms` sleep. On each call, `getLoggedInUserAndRefresh` finds the session present and not yet expired (since each check happens well within the most recently refreshed `100ms` window), so it takes the refresh branch: a new `SessionData` is stored with `expiresAtMs` pushed forward to `now + sessionTtlMs` — meaning `"sess-active"`'s deadline keeps sliding forward with each access, never actually reaching zero remaining time.

**Then**, `Thread.sleep(150)` runs, representing `"sess-idle"` going completely untouched for `150ms` — well past its original, never-refreshed `100ms` TTL, since `login("sess-idle", "bob")` was never followed by any access at all during this window.

**After that**, the final check calls `getLoggedInUserAndRefresh("sess-active")` first: its most recent refresh (from the third loop iteration) is well within its own `100ms` window relative to now, so it's found active, refreshed again, and returns `"alice"`.

**Finally**, `getLoggedInUserAndRefresh("sess-idle")` runs: `data.expiresAtMs()` reflects the original login time plus `100ms`, and `now` is well past that, since `150ms` of pure idle time has elapsed with zero refreshing activity — the `now >= data.expiresAtMs()` check is `true`, so the expired branch runs, removing the entry and returning `null`. The final printed comparison shows `alice` still logged in and `bob` expired, purely as a function of activity pattern against the shared TTL mechanism, exactly mirroring how a real Redis-backed sliding-expiry session store behaves.

```
[login] session 'sess-active' created, expires in 100ms unless refreshed
[login] session 'sess-idle' created, expires in 100ms unless refreshed

--- 'alice' stays ACTIVE, making requests every 40ms, well within the 100ms TTL ---
[session check] 'sess-active' active -- user=alice, TTL refreshed
[session check] 'sess-active' active -- user=alice, TTL refreshed
[session check] 'sess-active' active -- user=alice, TTL refreshed

--- 'bob' goes IDLE for 150ms, exceeding the 100ms TTL with no activity ---

--- final check on BOTH sessions ---
[session check] 'sess-active' active -- user=alice, TTL refreshed
[session check] 'sess-idle' is EXPIRED or absent -- treated as logged out
[result] alice: alice (still logged in, was active) | bob: bob (expired, was idle)
```

## 7. Gotchas & takeaways

> A sliding TTL, where every access refreshes the expiry, is usually the right default for user-facing sessions (an active user shouldn't be logged out mid-use), but be deliberate about it — for session types where you specifically want a hard absolute expiry regardless of activity (a time-limited authorization token, for instance), you need a fixed expiry that doesn't refresh, a different mechanism than what's shown here.
- Redis is a common choice for externalized session storage specifically because of its speed (sessions are read on nearly every request, so latency matters) and its native TTL support, which handles exactly this expiry behavior without custom cleanup logic.
- This is the single most common, highest-impact instance of the broader [statelessness](0513-stateless-services-for-scaling.md) principle — most services that "aren't stateless yet" are usually specifically failing on session data, making this the natural first fix.
- Externalizing session data doesn't mean giving up all local optimization — a service can still keep a short-lived [near cache](0506-near-cache.md) of session data for performance, as long as correctness always falls back to the shared, authoritative external store, exactly like any other two-tier caching setup.
- Test this specifically by simulating cross-instance routing in a staging environment — a session bug caused by in-memory storage often doesn't surface in local development (where there's only ever one instance) and only appears once real horizontal scaling and load balancing are in play in a genuine multi-instance deployment.
