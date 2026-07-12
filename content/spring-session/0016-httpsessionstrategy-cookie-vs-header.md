---
card: spring-session
gi: 16
slug: httpsessionstrategy-cookie-vs-header
title: "HttpSessionStrategy (cookie vs header)"
---

## 1. What it is

`HttpSessionIdResolver` (the modern name; older Spring Session versions called this `HttpSessionStrategy`) is the strategy interface controlling how a session's ID travels between client and server on each request — read from and written to either a cookie (`CookieHttpSessionIdResolver`, the default) or an HTTP header (`HeaderHttpSessionIdResolver`).

## 2. Why & when

A browser-based web application naturally wants cookies — the browser handles storing and automatically resending them, with no client-side code needed. But not every client is a browser: a mobile app, a single-page application's API client, or a service-to-service caller often doesn't want (or can't easily use) cookie-based session handling, and prefers to receive a session ID explicitly and send it back as a plain header, giving the client full, explicit control over exactly when and how the session ID is stored and transmitted.

Reach for choosing an `HttpSessionIdResolver` deliberately when:

- Building a REST API primarily consumed by non-browser clients (mobile apps, other services) where header-based session propagation is simpler for those clients to implement than cookie jar management.
- A single application serves both a browser-based frontend and a separate API surface with different session-propagation needs — this may call for different resolvers per path, or picking whichever single mechanism best serves the primary audience.
- Debugging "the session isn't being found on the next request" for a non-browser client — often traced back to the client not correctly resending whichever mechanism (cookie or header) the server is actually configured to expect.

## 3. Core concept

Think of the session ID as a claim ticket handed to a customer picking up a custom order. A cookie is like the shop automatically stapling that ticket inside the customer's own coat pocket (the browser's cookie jar) — the customer doesn't have to think about it; next time they walk in wearing that coat, the shop just checks the pocket. A header is like handing the customer the ticket directly and telling them "bring this back with you next time" — no automatic mechanism does it for them; the customer (client code) must explicitly hold onto it and explicitly present it again on every subsequent visit.

```java
// Cookie (default): browser handles storage and resend automatically
Set-Cookie: SESSION=MTZmYzA0...

// Header: client must explicitly read this and resend it on every subsequent request
X-Auth-Token: MTZmYzA0...
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Cookie-based resolution is handled automatically by the browser; header-based resolution requires explicit client code to store and resend the value">
  <rect x="20" y="20" width="290" height="80" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="165" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">CookieHttpSessionIdResolver</text>
  <text x="165" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Set-Cookie response header</text>
  <text x="165" y="86" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">browser auto-resends — zero client code</text>

  <rect x="350" y="20" width="290" height="80" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">HeaderHttpSessionIdResolver</text>
  <text x="495" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">custom response header (e.g. X-Auth-Token)</text>
  <text x="495" y="86" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">client must explicitly store + resend</text>
</svg>

Both ultimately carry the same session ID value — the difference is entirely in the transport mechanism and who's responsible for handling it.

## 5. Runnable example

The scenario: configuring the default cookie-based resolver explicitly, growing to switch a REST API to header-based resolution for mobile clients, and finally to support both simultaneously for an app serving both a browser frontend and a mobile API from the same backend.

### Level 1 — Basic

```java
// CookieResolverConfig.java (explicit, though this matches the library's own default)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.web.http.CookieHttpSessionIdResolver;
import org.springframework.session.web.http.HttpSessionIdResolver;

@Configuration
public class CookieResolverConfig {

    @Bean
    public HttpSessionIdResolver httpSessionIdResolver() {
        return new CookieHttpSessionIdResolver();
    }
}
```

**How to run:** with any Spring Session store configured plus this bean, make a request and inspect response headers. Expected output: `Set-Cookie: SESSION=<id>; Path=/; HttpOnly; SameSite=Lax` — the browser (or `curl -c`) handles resending it automatically on subsequent requests with no client code needed.

### Level 2 — Intermediate

Switching to header-based resolution for a REST API means the client — a mobile app in this example — must explicitly read the response header and resend it as a request header on every subsequent call.

```java
// HeaderResolverConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.web.http.HeaderHttpSessionIdResolver;
import org.springframework.session.web.http.HttpSessionIdResolver;

@Configuration
public class HeaderResolverConfig {

    @Bean
    public HttpSessionIdResolver httpSessionIdResolver() {
        return HeaderHttpSessionIdResolver.xAuthToken(); // uses "X-Auth-Token" header
    }
}
```

```java
// MobileApiClient.java (a stand-in for real mobile client logic)
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class MobileApiClient {

    private final HttpClient client = HttpClient.newHttpClient();
    private String sessionToken;

    public void login() throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/login"))
                .POST(HttpRequest.BodyPublishers.noBody())
                .build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        this.sessionToken = response.headers().firstValue("X-Auth-Token").orElseThrow();
    }

    public String callProtectedApi() throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/api/data"))
                .header("X-Auth-Token", sessionToken) // client explicitly resends what it stored
                .GET().build();
        return client.send(request, HttpResponse.BodyHandlers.ofString()).body();
    }
}
```

**How to run:** with `HeaderHttpSessionIdResolver` configured server-side, call `login()` then `callProtectedApi()`. Expected behavior: `login()` captures the `X-Auth-Token` response header into `sessionToken`, and `callProtectedApi()` succeeds only because it explicitly resends that stored value — omitting the header entirely (simulating a client bug) results in a fresh, unauthenticated session being treated as the request's identity instead.

What changed: session propagation responsibility moved from the browser (implicit, automatic) to the client's own code (explicit, must be correctly implemented) — appropriate for a mobile client that manages its own token storage anyway (often alongside other credentials) rather than relying on cookie-jar semantics it may not naturally have.

### Level 3 — Advanced

An application serving both a browser-based frontend (wanting cookies) and a separate mobile/API surface (wanting headers) from the same backend needs a resolver that picks the right mechanism per request — a custom `HttpSessionIdResolver` composing both, checking for one first and falling back to the other.

```java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.session.web.http.CookieHttpSessionIdResolver;
import org.springframework.session.web.http.HeaderHttpSessionIdResolver;
import org.springframework.session.web.http.HttpSessionIdResolver;

import java.util.List;

public class DualModeSessionIdResolver implements HttpSessionIdResolver {

    private final HttpSessionIdResolver headerResolver = HeaderHttpSessionIdResolver.xAuthToken();
    private final HttpSessionIdResolver cookieResolver = new CookieHttpSessionIdResolver();

    @Override
    public List<String> resolveSessionIds(HttpServletRequest request) {
        List<String> headerIds = headerResolver.resolveSessionIds(request);
        return !headerIds.isEmpty() ? headerIds : cookieResolver.resolveSessionIds(request);
    }

    @Override
    public void setSessionId(HttpServletRequest request, HttpServletResponse response, String sessionId) {
        boolean isApiClient = request.getRequestURI().startsWith("/api/");
        if (isApiClient) {
            headerResolver.setSessionId(request, response, sessionId);
        } else {
            cookieResolver.setSessionId(request, response, sessionId);
        }
    }

    @Override
    public void expireSession(HttpServletRequest request, HttpServletResponse response) {
        headerResolver.expireSession(request, response);
        cookieResolver.expireSession(request, response);
    }
}
```

**How to run:** register `DualModeSessionIdResolver` as the `HttpSessionIdResolver` bean. Test a browser-style request to `/dashboard` (expect `Set-Cookie` in the response) and a mobile-style request to `/api/data` (expect `X-Auth-Token` in the response instead). Expected behavior: each request type receives the propagation mechanism appropriate to it, and `resolveSessionIds` correctly checks for a header first (mobile/API clients), falling back to cookies (browser clients) when no header is present.

What changed and why it's production-flavored: a single backend now correctly serves two genuinely different client populations with their own natural session-propagation conventions, without forcing either one into an awkward mechanism that doesn't fit how that client type actually operates.

## 6. Walkthrough

Tracing session ID resolution for both client types against the dual-mode resolver, in execution order:

1. A browser makes its first request to `/dashboard` with no existing session cookie.
2. `SessionRepositoryFilter` (card 0004) needs to resolve any existing session ID; it calls `DualModeSessionIdResolver.resolveSessionIds(request)`, which checks for an `X-Auth-Token` header (none present for a browser request), falls back to checking cookies (also none, first visit), and returns an empty list — no existing session found.
3. A new session is created; at response time, `setSessionId(...)` is called. Since the request path doesn't start with `/api/`, it delegates to the cookie resolver, and the response includes `Set-Cookie: SESSION=...`.
4. Separately, a mobile client calls `POST /api/login`. The same resolution process runs; this time, `setSessionId(...)` sees the `/api/` prefix and delegates to the header resolver instead, returning `X-Auth-Token: ...` in the response.
5. The mobile client (per Level 2's `MobileApiClient`) explicitly captures and resends that header on its next call to `/api/data`; `resolveSessionIds` finds it in the header check first (since header resolution is checked before falling back to cookies) and correctly resolves the existing session.
6. Both client types, despite using entirely different transport mechanisms for the session ID, end up with `SessionRepositoryFilter` resolving to the correct, existing session on subsequent requests — the dual-mode resolver made the mechanism choice transparent to everything downstream of it.

```
Browser -> GET /dashboard (no cookie yet)
   resolveSessionIds: no header, no cookie -> [] (new session)
   setSessionId: path doesn't start with /api/ -> Set-Cookie response

Mobile  -> POST /api/login
   resolveSessionIds: no header yet -> [] (new session)
   setSessionId: path starts with /api/ -> X-Auth-Token response

Mobile  -> GET /api/data (X-Auth-Token: <stored value>)
   resolveSessionIds: header present -> [<value>] -> existing session found
```

## 7. Gotchas & takeaways

> Header-based session propagation (Level 2, Level 3) means the client is fully responsible for secure storage and transmission of the session identifier — unlike a cookie with `HttpOnly` (inaccessible to JavaScript, mitigating XSS token theft) and `Secure` (HTTPS-only transmission) flags handled automatically, a header-based token stored carelessly by client code (e.g. in `localStorage`, readable by any injected script) can be more exposed to certain attack classes; client-side storage choices matter as much as the server-side resolver choice.

- The default `CookieHttpSessionIdResolver` is the right choice for the overwhelming majority of browser-facing applications — reach for header-based resolution deliberately, for a specific non-browser client need, not as a default.
- A client that receives a header-based session token but fails to resend it on subsequent requests doesn't produce an error — it simply results in a fresh, unauthenticated session being treated as the request's identity, which can look confusingly like "random logouts" if the client-side bug is intermittent (e.g. only some request paths correctly attach the header).
- Cookie-based and header-based resolution can coexist in one application (Level 3), but the composition logic (which mechanism applies to which requests) needs to be deliberate and well-tested — an incorrectly composed resolver can silently resolve session IDs from the wrong mechanism for a given client type.
- `expireSession(...)` (used on logout) should clear *all* mechanisms a dual-mode resolver might have set, not just one — otherwise a stale cookie or header value could linger client-side and cause confusing partial-logout behavior.
- When debugging cross-client session issues, first confirm which resolver is actually active for the specific request path in question — assuming cookie behavior while the server is actually configured for header-based resolution (or vice versa) is a common source of "sessions aren't working" confusion when testing with a tool like `curl` that doesn't automatically manage cookies the way a browser does.
