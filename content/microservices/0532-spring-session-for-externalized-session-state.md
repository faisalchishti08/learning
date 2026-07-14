---
card: microservices
gi: 532
slug: spring-session-for-externalized-session-state
title: "Spring Session for externalized session state"
---

## 1. What it is

**Spring Session** transparently replaces a servlet container's default in-memory `HttpSession` storage with an external store (Redis, JDBC, Hazelcast, MongoDB) — so session data survives an individual instance restarting, and, critically, is visible to every instance in a horizontally-scaled fleet rather than being pinned to whichever single instance originally created it. Application code keeps calling the same familiar `HttpSession` API (`session.setAttribute(...)`, `session.getAttribute(...)`); Spring Session intercepts the underlying storage transparently, so [externalizing session state](0514-externalizing-session-state.md) requires essentially no code changes, only a dependency and a configuration.

## 2. Why & when

You reach for Spring Session whenever a service needs to keep any per-user session state and is (or will be) deployed as more than one instance behind a load balancer:

- **A default `HttpSession` lives in one instance's memory.** If a user's first request lands on instance A and A stores something in the session, a subsequent request landing on instance B (a different, unrelated JVM) has no way to see it — B has its own, entirely separate in-memory session store. Without [sticky sessions](0514-externalizing-session-state.md) pinning a user to one instance for their whole session's duration, this breaks outright; even with sticky sessions, it means an instance being replaced (a deploy, a crash, an autoscale-down event) destroys every session pinned to it.
- **Spring Session moves the actual session data to a shared, external store**, so any instance in the fleet can serve any request for any user's session correctly — this removes the need for sticky sessions entirely (any instance can transparently pick up any session), and means an individual instance's restart or replacement no longer destroys the sessions that happened to be pinned there.
- **It requires essentially no application code changes** — the servlet container's own `HttpSession` interface is what application code already uses; Spring Session's `SessionRepositoryFilter` intercepts requests transparently and backs the same interface with the external store instead of the container's default in-memory implementation.
- **The right moment to add it is before horizontally scaling any service that uses sessions at all** — retrofitting it later usually means untangling assumptions ("this instance's session state will always be here") that quietly crept into application or infrastructure configuration (sticky-session load balancer rules, for instance) once the service was already scaled without it.

## 3. Core concept

Think of a hotel where each floor's front desk keeps its own private ledger of guest preferences, so a guest checking in on floor 3 whose preferences are noted there gets a completely different (blank) experience if they later interact with floor 5's front desk, which has never heard of them. Moving that ledger to one shared, central reception system that every floor's desk can read and write means any floor can serve that guest correctly, using the exact same guest-facing interaction (the guest never has to know or care which floor's desk they happened to reach) — and if floor 3's desk is ever closed for renovation, the guest's preferences aren't lost, because they were never actually stored on floor 3 to begin with.

Concretely:

1. **`HttpSession` is a standard servlet API** that application code already uses (`request.getSession()`, `session.setAttribute(key, value)`) regardless of what's actually storing the data underneath.
2. **Spring Session's `SessionRepositoryFilter` intercepts every incoming request** before it reaches application code, wrapping the request so that any call to `request.getSession()` returns a Spring Session-backed session object instead of the container's default one — this happens transparently, with the application never directly interacting with the external store.
3. **The actual storage backend (Redis being the most common choice) is configured separately**, via a dependency (`spring-session-data-redis`) and minimal configuration — application code that calls `session.setAttribute(...)` has no idea, and doesn't need to know, that the value is actually being serialized and written to Redis rather than kept in local JVM memory.
4. **Because the session now lives externally, any instance can serve any request for any session** — a load balancer no longer needs sticky-session affinity for correctness (though it may still be used for other reasons, like cache locality), and replacing or restarting any single instance has zero effect on session data, since none of it ever lived there.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without Spring Session, each instance's HttpSession is private and pinned by sticky sessions; with Spring Session, session data lives in a shared external store any instance can read and write">
  <text x="150" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Default (in-memory)</text>
  <rect x="20" y="35" width="110" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="75" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance A</text>
  <text x="75" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">session in JVM memory</text>
  <rect x="150" y="35" width="110" height="50" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="205" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance B</text>
  <text x="205" y="78" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">CANNOT see A's session</text>
  <text x="140" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">requires sticky sessions; instance A restart = sessions lost</text>

  <text x="510" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring Session (Redis)</text>
  <rect x="400" y="35" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance A</text>
  <rect x="500" y="35" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="59" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">instance B</text>
  <rect x="440" y="90" width="110" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="495" y="109" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Redis: shared sessions</text>
  <line x1="445" y1="75" x2="480" y2="90" stroke="#8b949e"/>
  <line x1="545" y1="75" x2="510" y2="90" stroke="#8b949e"/>
  <text x="495" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">any instance serves any session; instance restart loses nothing</text>
</svg>

Moving session storage to a shared external store removes both the need for sticky sessions and the risk of losing session data when an instance restarts.

## 5. Runnable example

Scenario: a shopping cart stored in a user's session. We start with a plain Java model showing the per-instance session gap, extend it to a shared store closing that gap, then handle the real Spring Session configuration backed by Redis, requiring no changes to the application's session-using code.

### Level 1 — Basic

```java
// File: PerInstanceSessionGap.java -- models the DEFAULT servlet
// container behavior: each "instance" has its OWN private session store,
// so a session created on one instance is INVISIBLE to another.
import java.util.*;

public class PerInstanceSessionGap {
    static class ServiceInstance {
        String name;
        Map<String, Map<String, Object>> sessionsById = new HashMap<>(); // this instance's OWN sessions
        ServiceInstance(String name) { this.name = name; }

        void setSessionAttribute(String sessionId, String key, Object value) {
            sessionsById.computeIfAbsent(sessionId, k -> new HashMap<>()).put(key, value);
        }
        Object getSessionAttribute(String sessionId, String key) {
            Map<String, Object> session = sessionsById.get(sessionId);
            return session == null ? null : session.get(key);
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        instanceA.setSessionAttribute("sess-1", "cart", List.of("widget", "gadget"));
        System.out.println("instance-A sees cart: " + instanceA.getSessionAttribute("sess-1", "cart"));
        System.out.println("instance-B sees cart: " + instanceB.getSessionAttribute("sess-1", "cart") + " (null! same session ID, different instance)");
    }
}
```

How to run: `java PerInstanceSessionGap.java`

`instanceA` and `instanceB` each maintain their own private `sessionsById` map. A cart added to session `"sess-1"` on `instanceA` is completely invisible on `instanceB`, even though it's the same session ID — a request for `"sess-1"` that happens to land on `instanceB` (say, because a load balancer routed it there without sticky-session affinity) would see an empty cart, a real and confusing bug for the user.

### Level 2 — Intermediate

```java
// File: SharedSessionStore.java -- models moving session storage to a
// SHARED external store, so every instance sees the SAME session data
// regardless of which instance a request happens to land on.
import java.util.*;

public class SharedSessionStore {
    // ONE shared store, modeling a separate Redis deployment every instance connects to
    static Map<String, Map<String, Object>> sharedSessions = new HashMap<>();

    static class ServiceInstance {
        String name;
        ServiceInstance(String name) { this.name = name; }

        void setSessionAttribute(String sessionId, String key, Object value) {
            sharedSessions.computeIfAbsent(sessionId, k -> new HashMap<>()).put(key, value); // writes to the SHARED store
        }
        Object getSessionAttribute(String sessionId, String key) {
            Map<String, Object> session = sharedSessions.get(sessionId);
            return session == null ? null : session.get(key);
        }
    }

    public static void main(String[] args) {
        ServiceInstance instanceA = new ServiceInstance("instance-A");
        ServiceInstance instanceB = new ServiceInstance("instance-B");

        instanceA.setSessionAttribute("sess-1", "cart", List.of("widget", "gadget"));
        System.out.println("instance-A sees cart: " + instanceA.getSessionAttribute("sess-1", "cart"));
        System.out.println("instance-B sees cart: " + instanceB.getSessionAttribute("sess-1", "cart") + " (correct! shared store closes the gap)");
    }
}
```

How to run: `java SharedSessionStore.java`

`sharedSessions` is one map both instances write to and read from, modeling Spring Session backed by Redis. `instanceB` now correctly sees the cart `instanceA` added to `"sess-1"`, because both instances are reading from and writing to the same underlying store — exactly the fix Spring Session provides transparently for real `HttpSession` usage.

### Level 3 — Advanced

```java
// File: SpringSessionRealShape.java -- the REAL Spring Session shape:
// ordinary HttpSession usage in a controller, with Redis-backed storage
// configured SEPARATELY -- the controller code never changes.
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.bind.annotation.*;

import java.util.ArrayList;
import java.util.List;

public class SpringSessionRealShape {

    // ONE annotation on a configuration class is what redirects HttpSession storage to Redis
    @Configuration
    @EnableRedisHttpSession
    static class SessionConfig {}

    @RestController
    static class CartController {

        // ordinary HttpSession usage -- IDENTICAL to what it would be with the
        // servlet container's default in-memory session; no Redis-specific code here at all
        @PostMapping("/cart/add")
        public String addToCart(HttpServletRequest request, @RequestParam String item) {
            HttpSession session = request.getSession();
            @SuppressWarnings("unchecked")
            List<String> cart = (List<String>) session.getAttribute("cart");
            if (cart == null) { cart = new ArrayList<>(); }
            cart.add(item);
            session.setAttribute("cart", cart); // transparently serialized and written to Redis by Spring Session
            return "Cart now: " + cart;
        }

        @GetMapping("/cart")
        public String viewCart(HttpServletRequest request) {
            HttpSession session = request.getSession();
            List<String> cart = (List<String>) session.getAttribute("cart");
            return "Cart: " + (cart == null ? "[]" : cart);
        }
    }
}
```

How to run: requires `spring-session-data-redis` and `spring-boot-starter-data-redis` on the classpath, a running Redis instance, and `spring-boot-starter-web`; run via `mvn spring-boot:run`, then `POST /cart/add?item=widget` against instance A and `GET /cart` against instance B (a second instance of the same application, pointed at the same Redis) to see B correctly return the cart A added.

`CartController` contains ordinary `HttpServletRequest`/`HttpSession` code with zero mention of Redis — `@EnableRedisHttpSession` on `SessionConfig` is the only thing that redirects where `request.getSession()` actually stores its data. This is the entire value proposition: application code that already correctly uses `HttpSession` gets fleet-wide session sharing for free, purely through configuration.

## 6. Walkthrough

Trace what happens when a request hits `POST /cart/add?item=widget` on Instance A, followed by `GET /cart` on Instance B, both configured with `@EnableRedisHttpSession` pointed at the same Redis deployment:

1. **The request arrives at Instance A.** Spring Session's `SessionRepositoryFilter`, registered automatically by `@EnableRedisHttpSession`, intercepts it before it reaches `CartController`. It checks for a session cookie (`SESSION`, by default) in the request; finding none (first request), it will create a new session ID once one is requested.
2. **`addToCart` calls `request.getSession()`.** Because of the filter's interception, this returns a Spring Session-backed `HttpSession` implementation, not the servlet container's default. A new session ID is generated (say, `a1b2c3`) and a corresponding Redis key is prepared, though nothing is written to Redis yet at this point.
3. **`session.getAttribute("cart")` returns `null`** (nothing stored yet for this brand-new session), so `addToCart` initializes an empty `cart` list, adds `"widget"`, and calls `session.setAttribute("cart", cart)`. Spring Session serializes the `cart` list and writes it into Redis under a key derived from the session ID `a1b2c3`.
4. **The HTTP response includes a `Set-Cookie: SESSION=a1b2c3` header**, so the client's subsequent requests carry this same session ID.
5. **A second request, `GET /cart`, is sent with cookie `SESSION=a1b2c3`, but happens to land on Instance B** (a different, unrelated JVM, perhaps due to load-balancing with no sticky affinity). Instance B's own `SessionRepositoryFilter` reads the `SESSION` cookie, and because it's configured against the *same* Redis deployment, looks up session `a1b2c3` there directly.
6. **Redis returns the serialized `cart` data written in step 3**, and Instance B's `HttpSession.getAttribute("cart")` deserializes it back into the same `List<String>` containing `"widget"` — `viewCart` returns `"Cart: [widget]"`, correctly reflecting the item added on a completely different instance.

Without Spring Session, step 5 would instead hit Instance B's own empty, private in-memory session store (as in Level 1), and the response would incorrectly show an empty cart — exactly the bug Spring Session's Redis-backed, shared storage eliminates.

## 7. Gotchas & takeaways

> **Gotcha:** every object stored in the session via `setAttribute` must be serializable (by default, Java serialization, though this can be configured to use JSON) once Spring Session is backed by an external store like Redis — an object that worked fine in a purely in-memory session (never actually serialized) can fail unexpectedly the moment it's moved to Spring Session if it isn't properly serializable or contains non-serializable fields.

- Spring Session requires essentially no changes to application code that already correctly uses the standard `HttpSession` API — the storage swap happens transparently via a servlet filter.
- Externalizing session storage removes the *need* for sticky sessions for correctness, since any instance can serve any session — though a load balancer might still use sticky routing for other reasons (like colocating with a local cache).
- An instance restarting, being replaced, or being scaled down no longer destroys any session data, since none of it lives in that instance's own memory to begin with.
- Session objects must be properly serializable once backed by an external store — verify this explicitly, since a purely in-memory session never exercises this requirement and a serialization failure may only surface after moving to Spring Session in production.
