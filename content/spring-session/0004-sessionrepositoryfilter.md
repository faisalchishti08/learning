---
card: spring-session
gi: 4
slug: sessionrepositoryfilter
title: "SessionRepositoryFilter"
---

## 1. What it is

`SessionRepositoryFilter` is the servlet filter at the heart of Spring Session — it intercepts every incoming request, wraps the `HttpServletRequest` so that any call to `getSession()` transparently uses Spring Session's `SessionRepository` instead of the container's native session mechanism, and, after the response is generated, persists any session changes back to the store.

## 2. Why & when

Application code, and most libraries built on the Servlet API (Spring Security included), call `request.getSession()` expecting the container's built-in `HttpSession`. For Spring Session to work transparently — without rewriting every call site across the whole application and every third-party library it depends on — it needs to intercept that exact call and redirect it, invisibly, to its own store-backed implementation. `SessionRepositoryFilter` is what makes that interception possible, sitting as early as possible in the filter chain so that every other filter and the controller layer see a `HttpServletRequest` already wired for Spring Session.

Reach for understanding this filter when:

- Debugging filter-ordering issues — since Spring Session must wrap the request before anything else touches `getSession()`, misconfigured filter ordering (especially with Spring Security, which also needs early access) is a common source of "sessions aren't persisting to Redis" bugs.
- Understanding *when* session writes actually happen — attribute changes made mid-request aren't written to the store instantly; they're flushed by this filter at the end of the request.
- Customizing session cookie behavior (name, path, same-site attributes) — these are configured on the component this filter uses to read and write the session cookie, not scattered across application code.

## 3. Core concept

Think of `SessionRepositoryFilter` as airport security at the very first checkpoint every traveler (request) passes through before reaching any gate (controller) or connecting service (other filters, Spring Security). It doesn't just check credentials once — it issues each traveler a special badge (the wrapped request) that, for the rest of their time in the airport, makes every "which gate am I flying from" lookup (`getSession()`) automatically route through the airport's own centralized system (Spring Session), regardless of which specific staff member (filter or controller) asks. On the way out, the same checkpoint reconciles anything that changed during the visit (session attribute writes) back into that central system before the traveler leaves.

```
Request -> SessionRepositoryFilter (wraps request) -> [other filters] -> Controller
                                                                              |
Response <- SessionRepositoryFilter (flushes session changes) <-------------|
```

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="SessionRepositoryFilter wraps the request early in the chain and flushes session changes late, on the way out">
  <rect x="20" y="80" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SessionRepository</text>
  <text x="80" y="116" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Filter (wrap)</text>

  <rect x="180" y="80" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="240" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Security Filter</text>

  <rect x="340" y="80" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="400" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Controller</text>

  <rect x="500" y="80" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SessionRepository</text>
  <text x="580" y="116" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Filter (flush on exit)</text>

  <line x1="140" y1="105" x2="175" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="300" y1="105" x2="335" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="460" y1="105" x2="495" y2="105" stroke="#8b949e" stroke-width="1.5"/>

  <text x="340" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">every getSession() call between entry and exit is redirected to the store</text>
</svg>

The same filter instance handles both the wrap-on-entry and flush-on-exit halves of the request, since a servlet filter naturally wraps around the rest of the chain.

## 5. Runnable example

The scenario: observing the filter's wrap-and-flush behavior directly with a debug filter placed around it, growing to demonstrate that attribute writes are batched and only flushed once at the end (not on every `setAttribute` call), and finally to handle the specific ordering requirement with Spring Security correctly.

### Level 1 — Basic

```java
// TimingFilter.java (registered explicitly before SessionRepositoryFilter to observe its effect)
import jakarta.servlet.*;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.io.IOException;

@Component
@Order(0) // runs before SessionRepositoryFilter, which Spring Session registers early too
public class TimingFilter implements Filter {

    @Override
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest request = (HttpServletRequest) req;
        System.out.println("Before chain: request class = " + request.getClass().getSimpleName());
        chain.doFilter(req, res);
        System.out.println("After chain: response committed = " + ((jakarta.servlet.http.HttpServletResponse) res).isCommitted());
    }
}
```

**How to run:** add this filter to a Spring Session-enabled app and make a request. Expected console output: the request class name printed *before* the chain proceeds is already Spring Session's wrapper type (confirming `SessionRepositoryFilter` wrapped it before this filter even ran, since Spring Session registers itself very early by default), demonstrating the wrap-first ordering.

### Level 2 — Intermediate

Attribute writes aren't flushed to the store on every individual `setAttribute` call — they accumulate on the wrapped session object during the request and are written once, at the very end, when `SessionRepositoryFilter` detects the request completing.

```java
// BatchedWriteController.java
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class BatchedWriteController {

    @GetMapping("/demo/batched-writes")
    public String demonstrate(HttpSession session) {
        session.setAttribute("step1", "a");
        session.setAttribute("step2", "b");
        session.setAttribute("step3", "c");
        // At this point in a Redis-backed setup, none of these three writes
        // have necessarily reached Redis yet — they're accumulated locally
        // on the wrapped session and flushed once, after this method returns,
        // by SessionRepositoryFilter.
        return "Set three attributes in one request.";
    }
}
```

**How to run:** call `GET /demo/batched-writes` while a separate process runs `redis-cli MONITOR` to watch commands in real time. Expected observation: rather than three separate write operations interleaved with the request handling, the actual persistence commands appear together, right around when the HTTP response is being finalized — confirming the filter batches and flushes once per request rather than on every attribute mutation.

What changed: this reveals a meaningful performance characteristic — setting many attributes in a single request costs roughly one round-trip to the store, not one round-trip per `setAttribute` call, because `SessionRepositoryFilter` defers persistence to request completion.

### Level 3 — Advanced

Spring Security also needs very early access to the request (to establish the `SecurityContext` before authorization decisions are made), which creates a real ordering dependency — `SessionRepositoryFilter` must wrap the request *before* Spring Security's filter chain runs, or Spring Security ends up reading/writing the container's native session instead of Spring Session's store-backed one, silently breaking clustering for authenticated sessions specifically.

```java
// SessionFilterOrderConfig.java
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.Ordered;
import org.springframework.session.web.http.SessionRepositoryFilter;

@Configuration
public class SessionFilterOrderConfig {

    @Bean
    public FilterRegistrationBean<SessionRepositoryFilter<?>> sessionRepositoryFilterRegistration(
            SessionRepositoryFilter<?> filter) {

        FilterRegistrationBean<SessionRepositoryFilter<?>> registration = new FilterRegistrationBean<>(filter);
        registration.setOrder(Ordered.HIGHEST_PRECEDENCE); // guarantee it runs before Spring Security's chain
        return registration;
    }
}
```

**How to run:** in a Spring Boot app combining Spring Security and Spring Session, deliberately misconfigure ordering first (e.g. a custom filter with `Ordered.HIGHEST_PRECEDENCE` competing for the same slot) and observe login sessions failing to appear in Redis. Apply the explicit ordering shown above: log in, then check `redis-cli KEYS "spring:session:*"` — expect the authenticated session to now genuinely appear in Redis, confirming Spring Security's `SecurityContext` persistence is going through Spring Session, not the container's native session.

What changed and why it's production-flavored: Spring Boot's autoconfiguration usually gets this ordering right automatically when both Spring Session and Spring Security starters are present, but understanding *why* the ordering matters — and how to fix it explicitly — is essential when custom filter configuration or unusual starter combinations disturb the default ordering Boot would otherwise provide.

## 6. Walkthrough

Tracing a full request through `SessionRepositoryFilter`, in execution order:

1. A request arrives carrying a `SESSION` cookie. `SessionRepositoryFilter`, registered to run extremely early in the filter chain (Level 3), intercepts it before any other filter (including Spring Security's) gets a chance to call `getSession()`.
2. The filter wraps the raw `HttpServletRequest` in its own implementation, which overrides `getSession()` to lazily load from the configured `SessionRepository` (card 0002) — "lazily" meaning the actual store round-trip only happens the first time something calls `getSession()`, not unconditionally on every request.
3. The wrapped request proceeds through the rest of the filter chain — Spring Security's authentication filters, any custom filters, and finally the controller — every one of which calls the ordinary `HttpServletRequest.getSession()` API, unaware it's been redirected.
4. Any code along the way that calls `session.setAttribute(...)` mutates the wrapped session's local state; per Level 2, this doesn't hit the store immediately.
5. Once the controller returns and the response is being finalized, `SessionRepositoryFilter` checks whether the session was created, accessed, or modified during this request.
6. If so, it calls `sessionRepository.save(session)` exactly once, persisting the accumulated changes to the store in a single operation, and — if this was a brand-new session — writes the `SESSION` cookie onto the response so the client can present it on the next request.
7. The response is sent to the client; the store now holds the session state exactly as it stood at the end of request processing.

```
Request (SESSION cookie)
   |
SessionRepositoryFilter: wrap request (lazy getSession())
   |
[Security filters, custom filters, ...] -> getSession() -> lazily load from store on first call
   |
Controller: session.setAttribute(...) x N   (accumulated locally, not yet persisted)
   |
response being finalized
   |
SessionRepositoryFilter: session modified? --yes--> repository.save(session) (single write)
   |                                        --no--> skip, nothing to persist
   |
response sent (with SESSION cookie if new)
```

## 7. Gotchas & takeaways

> If `SessionRepositoryFilter` runs *after* Spring Security's own filters in the chain (a misordering, Level 3), Spring Security establishes its `SecurityContext` against the container's native session before Spring Session ever gets a chance to intercept `getSession()` — the application appears to work in every manual test, but authenticated sessions silently never make it into the shared store, and clustering breaks specifically for logged-in users while anonymous session behavior might look fine.

- Session writes are flushed once per request, at the end — code that reads a session attribute back from a *separate* concurrent request in the same instant it was written elsewhere may not see it yet if that other request's flush hasn't completed; don't assume same-instant cross-request visibility.
- `getSession()` is lazy — calling it triggers the actual store lookup; a request that never touches the session at all (a pure static-asset request, for instance) never makes a Redis or database call for session data, which matters for load characteristics under Spring Session versus a container's eagerly-initialized native session in some configurations.
- Spring Boot's autoconfiguration handles filter ordering automatically for the common case (Spring Session plus Spring Security both present as starters) — Level 3's manual configuration is a fallback for custom setups, not something most applications need to write themselves.
- A session that's accessed (read) but never modified during a request may still trigger a write, depending on configuration, since accessing it updates the last-accessed timestamp used for expiration tracking (card 0007) — this is expected, not a bug, but worth knowing when reasoning about write volume.
- When debugging "my session changes aren't showing up in the store," check filter ordering first, then confirm the request actually reached a point where the response wasn't already committed before the filter's flush logic ran (writing directly to the response stream and flushing it manually, bypassing normal completion, can in rare cases interfere with this).
