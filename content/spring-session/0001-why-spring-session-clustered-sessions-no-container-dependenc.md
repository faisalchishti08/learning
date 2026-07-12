---
card: spring-session
gi: 1
slug: why-spring-session-clustered-sessions-no-container-dependenc
title: "Why Spring Session (clustered sessions, no container dependency)"
---

## 1. What it is

Spring Session is a library that replaces a servlet container's built-in `HttpSession` implementation with a pluggable, externally-stored one — backed by Redis, JDBC, MongoDB, or another store — so session data lives outside any single application server process. Application code keeps using the exact same `HttpServletRequest.getSession()` API it always has; only where the data actually lives changes.

## 2. Why & when

A container's default `HttpSession` lives entirely in that one JVM's memory. That's fine for a single instance, but breaks down the moment there's more than one: scale to two application instances behind a load balancer, and a user whose session was created on instance A gets logged out the instant a request lands on instance B, which has no idea that session exists. The traditional fix — sticky sessions, where the load balancer always routes a given user back to the same instance — works until that instance restarts (deploys, crashes, autoscaling events), at which point every session on it is simply gone. Spring Session removes this fragility by moving session storage to a shared, external store every instance can read and write identically.

Reach for Spring Session when:

- Running more than one instance of an application behind a load balancer and needing sessions to survive both scaling and individual instance restarts.
- Wanting session data to survive a rolling deployment — with container-native sessions, every deploy logs every user out; with Spring Session backed by Redis, it doesn't.
- Needing to inspect, query, or manage session data from outside the application itself (say, an admin tool listing a user's active sessions) — a container's in-memory session store offers no such access; an external Redis or database store does.

## 3. Core concept

Think of a container's default session storage as each waiter at a restaurant keeping customer orders scribbled on their own personal notepad — fine as long as the same waiter serves that table all night, but the moment a different waiter (a different server instance) picks up the table, they have no idea what was previously ordered. Spring Session is like replacing every waiter's personal notepad with a shared order board visible to the whole kitchen and every waiter on shift — any waiter serving any table at any moment sees the exact same, current order, regardless of who took it originally or whether the original waiter went home.

```
Without Spring Session:              With Spring Session:
Instance A [session data]            Instance A -----\
Instance B [different data!]         Instance B ------> Shared store (Redis/JDBC)
   (sticky routing required)         Instance C -----/
                                         (any instance, any request, same data)
```

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Multiple application instances all read and write session data from one shared external store instead of local memory">
  <rect x="30" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Instance A</text>

  <rect x="30" y="90" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="118" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Instance B</text>

  <rect x="30" y="160" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="188" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Instance C</text>

  <rect x="400" y="80" width="220" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="112" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Shared session store</text>
  <text x="510" y="132" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Redis / JDBC / MongoDB</text>

  <line x1="170" y1="43" x2="395" y2="105" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="170" y1="113" x2="395" y2="115" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="170" y1="183" x2="395" y2="130" stroke="#3fb950" stroke-width="1.5"/>

  <text x="330" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">any instance can serve any request for any session</text>
</svg>

No instance owns a session — every instance is an equally valid reader and writer of the same shared record.

## 5. Runnable example

The scenario: a simple shopping-cart web app storing item counts in the session, growing from a single-instance in-memory setup where a restart loses everything, to running two instances sharing state via Redis, to proving the cart genuinely survives an instance restart.

### Level 1 — Basic

```java
// CartController.java  (baseline: default container session, single instance)
import org.springframework.web.bind.annotation.*;
import jakarta.servlet.http.HttpSession;

@RestController
public class CartController {

    @PostMapping("/cart/add")
    public String addItem(HttpSession session, @RequestParam String item) {
        Integer count = (Integer) session.getAttribute("itemCount");
        count = (count == null ? 0 : count) + 1;
        session.setAttribute("itemCount", count);
        return "Cart has " + count + " item(s). Session ID: " + session.getId();
    }
}
```

**How to run:** a plain Spring Boot web app with this controller. `curl -c cookies.txt -X POST "http://localhost:8080/cart/add?item=book"` then repeat with `-b cookies.txt`. Expected output: `itemCount` increments across requests using the same session cookie — but restart the app, and it resets to zero, since the session lived only in that JVM's memory.

### Level 2 — Intermediate

Adding Spring Session backed by Redis makes the exact same controller code work identically, but now the session data lives outside the JVM.

```xml
<!-- pom.xml additions -->
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session-data-redis</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-data-redis</artifactId>
</dependency>
```

```java
// RedisSessionConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;

@Configuration
@EnableRedisHttpSession
public class RedisSessionConfig {
    // No other code needed — CartController above is completely unchanged.
}
```

**How to run:** start a local Redis (`docker run -p 6379:6379 redis`), add the dependency and config class, run the same app. `curl -c cookies.txt -X POST "http://localhost:8080/cart/add?item=book"` then `redis-cli KEYS "spring:session:*"`. Expected output: the same cart increment behavior as Level 1, but now `redis-cli` shows actual session keys stored in Redis — the data has physically left the JVM.

What changed: zero application code changed — only a dependency and one annotation were added — yet session storage moved from local JVM heap to an external, shared store, which is the entire point of Spring Session's design.

### Level 3 — Advanced

Proving the real payoff: run two instances of the same app on different ports sharing the same Redis, add items via instance A, read the cart via instance B, then kill and restart instance A entirely — the session survives because it was never inside instance A's memory to begin with.

```java
// Run identical jar twice with different ports, same Redis:
// java -Dserver.port=8081 -jar app.jar
// java -Dserver.port=8082 -jar app.jar
```

```bash
# Add two items via instance A (port 8081)
curl -c cookies.txt -X POST "http://localhost:8081/cart/add?item=book"
curl -b cookies.txt -c cookies.txt -X POST "http://localhost:8081/cart/add?item=pen"

# Read the cart via instance B (port 8082) — same cookie, different JVM
curl -b cookies.txt -X POST "http://localhost:8082/cart/add?item=notebook"
# Expected: "Cart has 3 item(s)." — instance B saw instance A's writes.

# Now kill instance A entirely (Ctrl+C or kill -9), then hit instance B again:
curl -b cookies.txt -X POST "http://localhost:8082/cart/add?item=eraser"
# Expected: "Cart has 4 item(s)." — the session survived instance A's death untouched.
```

**How to run:** as shown above — two JVM processes, same Redis instance, one shared session cookie. Expected behavior: the item count is consistent across both instances and survives one of them being killed entirely, since neither instance ever held the authoritative copy of the session data.

What changed and why it's production-flavored: this is exactly the scenario a rolling deployment or an autoscaling event creates in production — instances come and go continuously, and Spring Session is what keeps a user's session alive through all of it, which a container's default in-memory session fundamentally cannot do.

## 6. Walkthrough

Tracing what happens on a session-touching request with Spring Session enabled, in execution order:

1. A request arrives carrying a session cookie (`SESSION=<id>`, Spring Session's own cookie name, distinct from a container's default `JSESSIONID`).
2. Spring Session's servlet filter (`SessionRepositoryFilter`, card 0004) intercepts the request before it reaches the controller, and wraps the incoming `HttpServletRequest` so that any call to `getSession()` is redirected to Spring Session's machinery instead of the container's native implementation.
3. The filter asks the configured `SessionRepository` (card 0002) — here, a Redis-backed one — to load the session identified by the cookie's ID. This is a real network round-trip to Redis, not a local memory lookup.
4. The controller (`CartController`) calls `session.getAttribute(...)` and `session.setAttribute(...)` exactly as it always would against a normal `HttpSession` — it has no idea the data is coming from Redis.
5. After the controller finishes and the response is being written, the filter detects the session was modified and writes the updated attributes back to Redis before the response is sent to the client.
6. The next request — whether it lands on the same instance or a completely different one sharing the same Redis — repeats steps 1-3, loading the exact same, now-updated session data, regardless of which instance actually processed the previous request.

```
Request (SESSION cookie) -> SessionRepositoryFilter
   |
load session from Redis by ID  (network call, not memory read)
   |
controller: session.getAttribute/setAttribute (unaware of storage location)
   |
filter detects changes -> write back to Redis
   |
response sent
   |
(next request, any instance): load from Redis again -> sees the update
```

## 7. Gotchas & takeaways

> Enabling Spring Session changes the session cookie name from the container's default (`JSESSIONID`) to `SESSION` by default — if a load balancer, reverse proxy, or client-side code has hardcoded assumptions about the cookie name (for sticky-session routing, for instance), it needs to be updated, or that infrastructure silently stops recognizing sessions correctly.

- Every session read and write now involves a real network call to the external store — this trades away the near-zero latency of in-memory access for horizontal scalability and resilience; for most web apps this cost is negligible, but session-heavy hot paths should be measured, not assumed.
- Sticky sessions become unnecessary once Spring Session is in place — any instance can legitimately serve any request for any session, which simplifies load balancer configuration and removes the "one instance restart logs everyone off" failure mode entirely.
- Anything stored in the session must be serializable in whatever form the chosen store requires (JSON for Redis by default, or Java serialization depending on configuration) — storing a non-serializable object in the session, which worked fine with a container's in-memory session, fails loudly once Spring Session is enabled.
- The shared store itself becomes a new dependency the application needs to be available — if Redis (or whichever store is chosen) goes down, session access fails application-wide; plan for that store's own availability and monitoring just as carefully as the application servers themselves.
- Don't conflate "clustered sessions" with "distributed caching" as a general concept — Spring Session is specifically about `HttpSession` semantics (attributes, expiration, session IDs, cookies); a general-purpose cache for arbitrary application data is a separate concern, even if it happens to use the same underlying store.
