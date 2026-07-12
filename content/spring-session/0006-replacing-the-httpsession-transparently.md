---
card: spring-session
gi: 6
slug: replacing-the-httpsession-transparently
title: "Replacing the HttpSession transparently"
---

## 1. What it is

"Transparent replacement" is Spring Session's central design promise: once configured, existing code written against the standard Servlet `HttpSession` API — `request.getSession()`, `session.getAttribute(...)`, `session.setAttribute(...)`, `session.invalidate()` — keeps working completely unmodified, while actually being backed by whichever external store is configured. No application code needs to know Spring Session is involved at all.

## 2. Why & when

Migrating a real application to clustered sessions would be a nonstarter if it meant rewriting every place that touches `HttpSession` — controllers, filters, and every third-party library (Spring Security very much included) that assumes the standard API. Transparent replacement is what makes adopting Spring Session in an existing codebase a configuration change rather than a rewrite: add the dependency, add one annotation, and every existing `getSession()` call site keeps compiling and behaving identically, just now backed by Redis or JDBC instead of the container.

Reach for this understanding when:

- Migrating an existing single-instance application to a clustered deployment — knowing that `HttpSession` usage doesn't need to change is what makes the migration path low-risk.
- Explaining to a team why third-party libraries (Spring Security, any framework calling `getSession()` internally) "just work" once Spring Session is configured, with no library-specific integration code needed.
- Verifying the boundary of transparency — code that casts `HttpSession` to a container-specific type, or that relies on container-specific behavior beyond the standard API, is where transparency can actually break down.

## 3. Core concept

Think of transparent replacement like swapping a building's phone system from an old on-premise PBX to a modern cloud-hosted VoIP provider. Every employee keeps using the exact same handset, dialing the exact same extensions, in the exact same way — nothing about their day-to-day experience changes. What changed is entirely behind the wall jack: calls now route through the cloud instead of a closet full of on-site hardware. `HttpSession` is the handset and dialing convention (the stable, unchanged API); Spring Session is the new routing infrastructure behind it, invisible to anyone just making calls.

```java
// This code is completely unaware of Spring Session:
HttpSession session = request.getSession();
session.setAttribute("cart", cart);
Object cart = session.getAttribute("cart");
session.invalidate();
// Whether this reads/writes local JVM memory or Redis is decided entirely by configuration, not this code.
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application and library code call the standard HttpSession API unchanged; only the configuration layer determines the real backing store">
  <rect x="30" y="30" width="260" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Application code, Spring Security,</text>
  <text x="160" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">any library calling getSession()</text>

  <rect x="30" y="130" width="260" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="158" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Standard HttpSession API</text>

  <line x1="160" y1="90" x2="160" y2="125" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="380" y="130" width="260" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="510" y="158" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Container native OR Spring Session</text>

  <line x1="290" y1="153" x2="375" y2="153" stroke="#3fb950" stroke-width="1.5"/>
  <text x="330" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">config decides</text>
</svg>

Everything above the standard API line is identical either way — only what's plugged in below it changes.

## 5. Runnable example

The scenario: proving transparency by running the exact same controller and Spring Security configuration first against the container's native session, then against Spring Session with zero code changes, growing to show a third-party-style component (a request-scoped bean depending on `HttpSession`) also working unmodified, and finally identifying and testing the one real edge case where transparency can break — a container-specific cast.

### Level 1 — Basic

```java
// SameControllerBothWays.java — this file never changes across the whole example
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class SameControllerBothWays {

    @GetMapping("/visit")
    public String recordVisit(HttpSession session) {
        Integer visits = (Integer) session.getAttribute("visits");
        visits = (visits == null ? 0 : visits) + 1;
        session.setAttribute("visits", visits);
        return "Visit #" + visits + " (session: " + session.getId() + ")";
    }
}
```

**How to run:** run this app with no Spring Session dependency at all — a plain Boot web app. `curl -c c.txt http://localhost:8080/visit` a few times with `-b c.txt`. Expected output: `Visit #1`, `Visit #2`, `Visit #3` — ordinary container-session behavior.

### Level 2 — Intermediate

Now add Spring Session (Redis-backed, card 0009) and re-run the *exact same* `curl` sequence against the *exact same, completely unmodified* controller class.

```java
// RedisConfig.java — the ONLY new file; SameControllerBothWays.java is untouched
import org.springframework.context.annotation.Configuration;
import org.springframework.session.data.redis.config.annotation.web.http.EnableRedisHttpSession;

@Configuration
@EnableRedisHttpSession
public class RedisConfig {
}
```

**How to run:** add this config class and the Redis dependency, restart, run the identical `curl -c c.txt http://localhost:8080/visit` sequence. Expected output: identical `Visit #1`, `Visit #2`, `Visit #3` responses — but now `redis-cli KEYS "spring:session:*"` shows the session actually stored in Redis, and — the real proof of transparency — restarting the application mid-sequence and continuing with the same cookie still correctly returns `Visit #4`, something Level 1's setup could never do.

What changed: literally nothing in `SameControllerBothWays.java`. The only difference between "session lost on restart" and "session survives restart" was the addition of one configuration class — exactly the transparency this card is about.

### Level 3 — Advanced

A request-scoped bean depending on `HttpSession` (a common pattern in larger applications, and a stand-in for how third-party libraries like Spring Security consume sessions internally) also needs zero changes — but demonstrating the one real limit of transparency: code that casts to a container-specific session type breaks, since Spring Session's wrapped session is a different concrete class.

```java
// VisitTracker.java — a request-scoped bean, unchanged across both configurations
import jakarta.servlet.http.HttpSession;
import org.springframework.context.annotation.RequestScope;
import org.springframework.stereotype.Component;

@Component
@RequestScope
public class VisitTracker {

    private final HttpSession session;

    public VisitTracker(HttpSession session) { // injected via the servlet-scope proxy, unaware of Spring Session
        this.session = session;
    }

    public String currentSessionSummary() {
        return "id=" + session.getId() + ", attrs=" + java.util.Collections.list(session.getAttributeNames());
    }
}
```

```java
// BrokenTransparencyExample.java — demonstrates the ONE thing that does NOT transparently work
public class BrokenTransparencyExample {
    public String demonstrateBreakage(jakarta.servlet.http.HttpSession session) {
        // This line compiles and works fine against a container-native session,
        // but throws ClassCastException once Spring Session is enabled, because
        // the session object is no longer the container's own implementation class.
        // org.apache.catalina.session.StandardSessionFacade tomcatSession =
        //     (org.apache.catalina.session.StandardSessionFacade) session;
        return "Never cast HttpSession to a container-specific implementation type.";
    }
}
```

**How to run:** inject `VisitTracker` into a controller and call `currentSessionSummary()` under both Level 1 and Level 2 configurations — expect it to work identically in both, proving even injected, request-scoped session-dependent beans transparently follow whichever backing store is configured. Then attempt the commented-out container-specific cast under the Spring Session configuration: expect a `ClassCastException`, since Spring Session's wrapped session object is its own type, not the container's.

What changed and why it's production-flavored: this demonstrates both the strength (99% of real code, including request-scoped beans and framework internals, transparently works) and the one genuine limit (container-specific casts) of the transparency guarantee — knowing exactly where that line sits prevents a confusing runtime surprise in the rare codebase that has such a cast lurking in it.

## 6. Walkthrough

Tracing why transparency actually holds, in execution order:

1. `SessionRepositoryFilter` (card 0004) wraps the incoming `HttpServletRequest` before any other code — including Spring Security's filters, `VisitTracker`'s construction, and the controller — gets a chance to call `getSession()`.
2. Every subsequent `getSession()` call anywhere in the request's processing — whether from `SameControllerBothWays`, from `VisitTracker`'s constructor injection, or from deep inside Spring Security's session-management filters — resolves against this same wrapped request, transparently redirected to Spring Session's `SessionRepository`.
3. Because the wrapped session object still fully implements the standard `jakarta.servlet.http.HttpSession` interface, every standard method call (`getAttribute`, `setAttribute`, `getId`, `invalidate`) behaves exactly per the Servlet spec's contract — callers relying only on that interface, not a specific implementation class, see no difference at all.
4. Attribute writes accumulate on this wrapped object during the request (as covered in card 0004) and are flushed to the actual store once, at request completion.
5. The one place transparency breaks is precisely where code steps outside the standard interface contract — casting to a concrete implementation class assumes a specific object identity that Spring Session, by design, doesn't preserve, since it supplies its own wrapper implementation instead of the container's.

```
Request -> SessionRepositoryFilter wraps HttpServletRequest
   |
ALL code (controllers, Security filters, request-scoped beans) calls
standard HttpSession interface methods only
   |
   -> works identically regardless of backing store (interface-based, transparent)
   |
CODE THAT CASTS to a container-specific class
   |
   -> breaks under Spring Session (ClassCastException) — the one non-transparent case
```

## 7. Gotchas & takeaways

> Transparency is guaranteed at the level of the standard `HttpSession` interface, not at the level of any container-specific implementation class — code (rare, but it exists in some older codebases) that casts an injected `HttpSession` to a Tomcat- or Jetty-specific type will compile fine and work under a container's native session, then fail with `ClassCastException` the moment Spring Session is introduced. Audit for this pattern before migrating an existing application.

- Third-party libraries that depend only on the standard Servlet API (Spring Security's session-management filters among them) genuinely require zero Spring Session-specific integration code — this is precisely why Spring Session can slot underneath an existing Spring Security setup with just configuration changes.
- The transparency promise extends to request-scoped beans and any dependency-injected `HttpSession` — Spring's proxying mechanism for request scope works through the standard interface just as controllers do, so no special handling is needed there either.
- Verifying transparency in practice (Level 2's approach: run the identical code against both configurations) is a genuinely useful pre-migration test for any real application — if behavior diverges between container-native and Spring Session configurations for the same code, that divergence is exactly what needs investigating before shipping the migration.
- Session *identity* (the actual session ID value, its format) may differ between a container's native session and Spring Session's own ID generation — application code should never parse or make assumptions about session ID format or structure, treating it purely as an opaque identifier, which the standard API has always implied anyway.
- When migrating a large legacy codebase, grep specifically for casts involving session types (`StandardSession`, `StandardSessionFacade`, or other container-specific class names) as a pre-migration sanity check — this is a small, mechanical, high-value check given how rare but how disruptive that one non-transparent case can be.
