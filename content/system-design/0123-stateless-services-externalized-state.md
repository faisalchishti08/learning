---
card: system-design
gi: 123
slug: stateless-services-externalized-state
title: Stateless services & externalized state
---

## 1. What it is

A **stateless service** keeps no request-specific data in its own memory or local disk between requests — every request carries (or looks up) everything it needs, and any instance of the service can handle any request. **Externalized state** is where that data actually lives instead: a shared database, cache, or session store that every instance of the service can reach equally.

## 2. Why & when

[Horizontal scaling](0122-vertical-vs-horizontal-scaling.md) only works cleanly if any instance can handle any request — if instance A stored a user's shopping cart only in its own local memory, then a later request routed to instance B would not find that cart at all. Making services stateless removes this dependency on "which specific instance did I talk to last time", which is exactly what lets a load balancer route requests freely and lets instances be added, removed, or restarted without losing anything. Design for statelessness from the start of any service you expect to run as multiple instances behind a load balancer — which is most backend services today.

## 3. Core concept

- **No local session state:** a user's session data (logged-in user id, shopping cart contents) is stored in a shared store (Redis, a database) keyed by a session id, not in the memory of whichever instance first handled their login.
- **Any instance can serve any request:** since no instance holds unique, needed data locally, a load balancer can send a given user's requests to a different instance every time with no loss of correctness.
- **Externalized state stores:** a distributed cache (Redis) for session data, a shared database for persistent data, or a shared file store for uploaded files — all reachable by every instance identically.
- **Sticky sessions are a workaround, not a fix:** routing a user's requests to the same instance every time ("session affinity") can mask a stateful design, but it defeats even load distribution and breaks the moment that specific instance fails or is removed.
- **Instances become disposable:** because no instance holds anything unique, any instance can be killed and replaced (for a deploy, a crash, or scaling down) without losing any user's data or state.

## 4. Diagram

```
STATEFUL (broken under scaling):        STATELESS (externalized state):

  User logs in -> Instance A            User logs in -> Instance A writes
  stores session in A's own                session to shared Redis store
  local memory only.

  Next request routed to Instance B     Next request routed to Instance B ->
  by load balancer -> session NOT       B reads the SAME session from Redis
  FOUND -> user appears logged out.     -> works correctly, session found.

     [A: session data]  [B: nothing]        [A]        [B]
                                              \          /
                                          Shared Redis: session data
```
*Caption: a stateless instance keeps nothing unique locally, so any instance reading the shared store behaves identically to any other.*

## 5. Runnable example

**Level 1 — Basic.** A stateful service stores a session locally; a request to a different instance fails to find it.

**Level 2 — Externalize the state.** Both instances read and write to a shared store instead, fixing the problem.

**Level 3 — Disposability.** Kill one instance entirely and confirm the session is still available, served by the other.

```java
// StatelessServices.java
import java.util.*;

public class StatelessServices {

    static class StatefulInstance {
        String name;
        Map<String, String> localSessionStore = new HashMap<>(); // BAD: unique data lives only here
        StatefulInstance(String name) { this.name = name; }
        void login(String sessionId, String user) { localSessionStore.put(sessionId, user); }
        String getSession(String sessionId) { return localSessionStore.get(sessionId); }
    }

    static class StatelessInstance {
        String name;
        Map<String, String> sharedSessionStore; // GOOD: a reference to state shared by ALL instances
        StatelessInstance(String name, Map<String, String> sharedSessionStore) {
            this.name = name; this.sharedSessionStore = sharedSessionStore;
        }
        void login(String sessionId, String user) { sharedSessionStore.put(sessionId, user); }
        String getSession(String sessionId) { return sharedSessionStore.get(sessionId); }
    }

    public static void main(String[] args) {
        // Level 1: stateful design - session stored only on the instance that handled login.
        StatefulInstance instanceA = new StatefulInstance("A");
        StatefulInstance instanceB = new StatefulInstance("B");

        instanceA.login("session-1", "alice"); // user logs in, routed to instance A
        System.out.println("request to instance A for session-1: " + instanceA.getSession("session-1"));
        System.out.println("next request routed to instance B for session-1: " + instanceB.getSession("session-1") + " (BROKEN - appears logged out)");

        // Level 2: stateless design - session lives in a shared store both instances point to.
        Map<String, String> sharedStore = new HashMap<>(); // models Redis or a shared session database
        StatelessInstance statelessA = new StatelessInstance("A", sharedStore);
        StatelessInstance statelessB = new StatelessInstance("B", sharedStore);

        statelessA.login("session-2", "bob"); // login handled by instance A, written to the SHARED store
        System.out.println("request to instance A for session-2: " + statelessA.getSession("session-2"));
        System.out.println("next request routed to instance B for session-2: " + statelessB.getSession("session-2") + " (CORRECT - same shared store)");

        // Level 3: disposability - instance A can be discarded entirely; the session survives.
        statelessA = null; // instance A is "killed" (deploy, crash, scale-down)
        System.out.println("instance A destroyed. session-2 still readable via instance B: " + statelessB.getSession("session-2"));
    }
}
```

**How to run:** save as `StatelessServices.java`, then run `java StatelessServices.java`.

## 6. Walkthrough

1. `StatefulInstance` keeps its own private `localSessionStore`; `instanceA.login` writes only into `instanceA`'s own map.
2. Reading the session back from `instanceA` succeeds, but reading the same session id from `instanceB` returns `null` — `instanceB` never saw that write, since it has its own separate, empty map. This reproduces the exact bug a load balancer would trigger by routing a user's second request to a different instance.
3. `StatelessInstance` instead holds a reference to one `sharedStore` map, passed in at construction — both `statelessA` and `statelessB` point at the *same* underlying map object.
4. `statelessA.login` writes into `sharedStore`; reading it back via `statelessB.getSession` succeeds, because both instances are really just reading and writing the same shared data, not two separate private copies.
5. Setting `statelessA = null` models destroying that instance entirely; `statelessB.getSession("session-2")` still returns `"bob"` correctly, since the session was never tied to `statelessA`'s own existence — this is the disposability payoff: any instance can be added, removed, or replaced without losing state.

## 7. Gotchas & takeaways

> Gotcha: it is easy to accidentally reintroduce local state through caching — an in-memory cache inside a service instance, meant purely as a performance optimization, can silently become a source of the exact same bug if different instances end up disagreeing about a value because their local caches are out of sync. Any local cache in a horizontally-scaled service must either be safely stale-tolerant or itself backed by a shared, consistent store.

- A stateless service keeps no unique, request-relevant data in its own local memory or disk, letting any instance serve any request correctly.
- Externalizing state to a shared store (Redis, a database) is what actually enables horizontal scaling and safe instance disposability.
- Sticky sessions can mask a stateful design temporarily but reintroduce the single-point-of-failure problem horizontal scaling was meant to remove.
- Related concepts: [Vertical vs horizontal scaling](0122-vertical-vs-horizontal-scaling.md) (the scaling strategy this design enables), [Sticky sessions & session affinity](0040-sticky-sessions-session-affinity.md) (the common workaround, and why it does not remove the underlying dependency on one instance).
