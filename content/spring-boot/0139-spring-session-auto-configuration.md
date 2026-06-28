---
card: spring-boot
gi: 139
slug: spring-session-auto-configuration
title: Spring Session auto-configuration
---

## 1. What it is

**Spring Session** replaces the default Servlet `HttpSession` with an implementation that stores session data in an external store — Redis, JDBC, Hazelcast, or MongoDB — instead of in-memory inside the JVM. Spring Boot auto-configures Spring Session when `spring-session-data-redis` (or another session starter) is on the classpath, wiring up the `SessionRepository`, the `HttpSessionIdResolver`, and a `SessionRepositoryFilter` that transparently intercepts every request.

## 2. Why & when

The standard `HttpSession` is stored in the JVM heap. If you run multiple app instances behind a load balancer, sessions are tied to the instance that created them — a user routed to a different instance loses their session. Spring Session fixes this by moving sessions to a shared store.

Use it when:

- Running more than one app instance (horizontal scaling, rolling deployments).
- You need sessions to survive an app restart.
- You want to inspect, invalidate, or share sessions from outside the app (e.g. admin tooling).

Common choice: **Redis** for speed; **JDBC** for simplicity when you already have a relational database.

## 3. Core concept

Spring Session inserts a `SessionRepositoryFilter` at the top of the Servlet filter chain. This filter wraps the `HttpServletRequest` and `HttpServletResponse` in a decorator that redirects all `request.getSession()` calls to a `SessionRepository` backed by the chosen store. From the application's perspective, `HttpSession` works exactly as before — the persistence is transparent.

Session ID is read from (and written to) a cookie (`SESSION` by default) or an HTTP header (`X-Auth-Token` for stateless clients). Spring Boot auto-configures the right `HttpSessionIdResolver` based on the store type and properties.

```
Request → SessionRepositoryFilter
             ↓ getSession()
         SessionRepository (Redis / JDBC / …)
             ↓ load/save session attributes
         Application code (unchanged)
```

## 4. Diagram

<svg viewBox="0 0 680 210" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="110" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">HTTP Request</text>
  <rect x="225" y="80" width="175" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="312" y="103" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">SessionRepository</text>
  <text x="312" y="120" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Filter (transparent)</text>
  <rect x="475" y="55" width="175" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="562" y="79" text-anchor="middle" fill="#8b949e" font-size="12" font-family="sans-serif">Redis / JDBC / Mongo</text>
  <rect x="475" y="115" width="175" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="562" y="139" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Your Controller</text>
  <line x1="152" y1="105" x2="221" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ss)"/>
  <line x1="402" y1="95" x2="471" y2="75" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ss2)"/>
  <line x1="402" y1="115" x2="471" y2="135" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ss2)"/>
  <defs>
    <marker id="ss" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ss2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`SessionRepositoryFilter` intercepts every request, loading and saving session data from the external store; your controller calls `HttpSession` normally.

## 5. Runnable example

```java
// SessionApp.java  —  Spring Boot project
// pom.xml dependencies needed:
//   spring-boot-starter-web
//   spring-session-data-redis
//   spring-boot-starter-data-redis
// application.properties:
//   spring.session.store-type=redis
//   spring.data.redis.host=localhost
//   spring.data.redis.port=6379

import jakarta.servlet.http.HttpSession;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.web.bind.annotation.*;

@SpringBootApplication
public class SessionApp {
    public static void main(String[] args) {
        SpringApplication.run(SessionApp.class, args);
    }
}

@RestController
@RequestMapping("/session")
class SessionController {

    // Store a value in the distributed session
    @PostMapping("/set")
    public String set(@RequestParam String key,
                      @RequestParam String value,
                      HttpSession session) {
        session.setAttribute(key, value);
        return "Stored in session " + session.getId();
    }

    // Read it back — works even after a restart or on a different instance
    @GetMapping("/get")
    public String get(@RequestParam String key, HttpSession session) {
        Object val = session.getAttribute(key);
        return val != null ? val.toString() : "not found";
    }

    @DeleteMapping("/invalidate")
    public String invalidate(HttpSession session) {
        session.invalidate();
        return "Session invalidated";
    }
}
```

**How to run:**
1. Start Redis locally: `docker run -p 6379:6379 redis:7`
2. Start the app.
3. `curl -c cookies.txt -X POST "http://localhost:8080/session/set?key=user&value=alice"`
4. `curl -b cookies.txt "http://localhost:8080/session/get?key=user"` → `alice`
5. Restart the app and repeat step 4 — value persists in Redis.

## 6. Walkthrough

- `spring-session-data-redis` on the classpath triggers `RedisSessionAutoConfiguration`. It creates a `RedisSessionRepository` (or `RedisIndexedSessionRepository` for findByIndex queries) and registers the `SessionRepositoryFilter`.
- `spring.session.store-type=redis` makes the store choice explicit (auto-detected when only one store starter is present).
- `SessionRepositoryFilter` wraps `HttpServletRequest` in a `SessionRepositoryRequestWrapper`. When your controller calls `session.setAttribute(key, value)`, the wrapper writes the attribute to the Redis hash for that session ID.
- The session ID is written to a `SESSION` cookie. On subsequent requests, the filter reads the cookie, loads the session from Redis, and your code sees the same attributes regardless of which app instance handles the request.
- `session.invalidate()` deletes the session entry from Redis and clears the cookie.
- For JDBC-backed sessions, swap the dependency for `spring-session-jdbc` and set `spring.session.store-type=jdbc`. The DDL for the session table is auto-applied via `spring.session.jdbc.initialize-schema=always` in dev.

## 7. Gotchas & takeaways

> All objects stored as session attributes must be **`Serializable`**. Redis serialises them with Java serialisation by default. Non-serializable objects cause `SerializationException` at runtime. Prefer JSON serialisation (`spring.session.redis.repository-type=indexed` + custom `RedisSerializer`).

> Session fixation: Spring Session regenerates the session ID on login (when using Spring Security). Without Spring Security, call `session.invalidate()` then create a new session after authentication to prevent session fixation attacks.

- `spring.session.timeout` sets session lifetime (e.g. `30m`); overrides the container's default.
- `SessionRepository.findById(id)` lets you look up any session programmatically — useful for admin dashboards.
- Spring Session integrates transparently with Spring Security's `SecurityContextRepository`.
- With JDBC store, enable `spring.session.jdbc.initialize-schema=always` in dev to auto-create the `SPRING_SESSION` table.
- `spring.session.redis.flush-mode=on-save` (default) writes to Redis only when the response commits; `immediate` writes on every `setAttribute` call.
