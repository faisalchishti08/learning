---
card: spring-session
gi: 23
slug: rest-api-session-via-header
title: "REST API session via header"
---

## 1. What it is

This is the practical application of `HeaderHttpSessionIdResolver` (introduced in card 0016) as a complete pattern for REST APIs: a stateless-looking API (no cookies, no server-rendered redirects) that still benefits from server-side session state — shopping carts, multi-step wizards, rate-limiting counters — by having the client explicitly manage a session token as a bearer-style header, the same way many APIs already handle authentication tokens.

## 2. Why & when

REST APIs consumed by mobile apps, single-page applications, or other services often avoid cookies deliberately — cookies carry browser-specific semantics (automatic sending, `SameSite` policies, CORS complications) that don't map cleanly onto non-browser clients or cross-origin API architectures. But "stateless API" doesn't have to mean "no server-side session state at all" — it's entirely reasonable to want session-backed features (a server-tracked shopping cart, a partially-completed multi-step form) while still using a token-based, header-driven propagation mechanism that fits more naturally into how API clients already handle other tokens (like OAuth2 bearer tokens).

Reach for header-based REST session handling when:

- Building an API primarily consumed by mobile apps or other non-browser clients, where header-based token handling is the client's natural, expected convention already used for authentication.
- Needing session-backed state (a cart, a wizard's progress, request-scoped caching) in an API that deliberately avoids cookies for architectural or cross-origin reasons.
- Deciding whether session state is the right tool at all for a given API — for genuinely stateless, single-request operations, this pattern adds unneeded complexity; it earns its place specifically when multi-request, server-tracked state is a real requirement.

## 3. Core concept

Think of a cookie-based web session as a hotel automatically re-recognizing a guest by their room key card every time they badge through a door — no conscious effort from the guest. A header-based REST session is more like a coat-check ticket: the API hands the client an explicit token on first contact, and the client is responsible for presenting that exact ticket on every subsequent related request — natural and expected for an API client, which already manages other tokens (API keys, OAuth2 bearer tokens) the exact same explicit way, rather than relying on any browser-specific automatic mechanism.

```http
POST /api/cart/create
< 201 Created
< X-Auth-Token: 9f8e7d6c5b4a...

POST /api/cart/add-item
> X-Auth-Token: 9f8e7d6c5b4a...
< 200 OK
```

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client receives a session token on first response and explicitly attaches it to every subsequent related request">
  <rect x="20" y="30" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">API client</text>

  <rect x="250" y="30" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">REST API server</text>

  <line x1="170" y1="45" x2="245" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <text x="207" y="35" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1. first request</text>

  <line x1="250" y1="60" x2="175" y2="60" stroke="#3fb950" stroke-width="1.5"/>
  <text x="207" y="75" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">2. X-Auth-Token: abc</text>

  <rect x="20" y="120" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="148" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">same client</text>

  <line x1="170" y1="135" x2="245" y2="135" stroke="#8b949e" stroke-width="1.5"/>
  <text x="207" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">3. X-Auth-Token: abc (explicit)</text>
</svg>

Nothing automatic happens between step 2 and step 3 — the client's own code must carry that value forward.

## 5. Runnable example

The scenario: building a header-based session API for a server-tracked shopping cart, growing to handle the common client-side mistake of a missing or expired token gracefully, and finally to correctly support CORS for a browser-based single-page application consuming this same header-based API cross-origin.

### Level 1 — Basic

```java
// HeaderCartApiController.java
import jakarta.servlet.http.HttpSession;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/cart")
public class HeaderCartApiController {

    @PostMapping("/create")
    public String create(HttpSession session) {
        session.setAttribute("items", new java.util.ArrayList<String>());
        return "Cart created. Session ID: " + session.getId();
    }

    @PostMapping("/add")
    @SuppressWarnings("unchecked")
    public String addItem(HttpSession session, @RequestParam String item) {
        var items = (java.util.List<String>) session.getAttribute("items");
        if (items == null) {
            return "No cart found for this session — call /create first.";
        }
        items.add(item);
        return "Cart now has " + items.size() + " item(s): " + items;
    }
}
```

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
        return HeaderHttpSessionIdResolver.xAuthToken();
    }
}
```

**How to run:** `curl -i -X POST http://localhost:8080/api/cart/create` and capture the `X-Auth-Token` response header. Then `curl -X POST "http://localhost:8080/api/cart/add?item=book" -H "X-Auth-Token: <captured-value>"`. Expected output: `Cart now has 1 item(s): [book]` — the cart's state was correctly tracked server-side across two separate, cookie-free requests purely via the explicitly resent header.

### Level 2 — Intermediate

Real API clients sometimes forget to resend the token, or resend an expired one — a well-designed API returns a clear, structured error rather than silently creating an unexpected fresh session (which, from a shopping cart's perspective, looks like "my cart randomly emptied").

```java
import jakarta.servlet.http.HttpSession;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/cart")
public class RobustHeaderCartApiController {

    @PostMapping("/add")
    @SuppressWarnings("unchecked")
    public ResponseEntity<?> addItem(HttpSession session, @RequestParam String item,
                                      @RequestHeader(value = "X-Auth-Token", required = false) String providedToken) {

        boolean isFreshSession = session.isNew();

        if (isFreshSession && providedToken != null) {
            // The client SENT a token, but it didn't resolve to any existing session —
            // it expired or was never valid. This is meaningfully different from
            // "no token provided at all," and deserves a distinct, clear error.
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(java.util.Map.of("error", "session_expired",
                            "message", "Your session has expired. Please create a new cart."));
        }

        var items = (java.util.List<String>) session.getAttribute("items");
        if (items == null) {
            items = new java.util.ArrayList<>();
            session.setAttribute("items", items);
        }
        items.add(item);
        return ResponseEntity.ok(java.util.Map.of("items", items, "sessionId", session.getId()));
    }
}
```

**How to run:** call `/api/cart/add` with a deliberately invalid or expired `X-Auth-Token` value. Expected response: `401 Unauthorized` with a clear `session_expired` error body, rather than a silent `200 OK` with a freshly emptied cart that gives the client no signal anything unexpected happened.

What changed: the API now clearly distinguishes "you never had a session" from "your session token was presented but no longer resolves to anything," letting client code handle each case appropriately (prompt for a fresh cart versus surface a specific "your session expired" message to the end user) instead of silently and confusingly starting over.

### Level 3 — Advanced

A browser-based single-page application consuming this header-based API cross-origin needs correct CORS configuration — specifically, the custom `X-Auth-Token` header must be explicitly allowed in both the request (`Access-Control-Allow-Headers`) and, critically, exposed in the response (`Access-Control-Expose-Headers`), since custom response headers aren't visible to browser JavaScript by default under CORS.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

@Configuration
public class CorsForHeaderSessionConfig {

    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(java.util.List.of("https://spa.example.com"));
        config.setAllowedMethods(java.util.List.of("GET", "POST", "DELETE"));
        config.setAllowedHeaders(java.util.List.of("X-Auth-Token", "Content-Type"));

        // Without this, the browser's fetch() API cannot read the X-Auth-Token
        // response header at all, even though it's present on the wire —
        // custom response headers are hidden from JavaScript by default under CORS.
        config.setExposedHeaders(java.util.List.of("X-Auth-Token"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/api/**", config);
        return new CorsFilter(source);
    }
}
```

**How to run:** serve a test single-page application from `https://spa.example.com` (or an equivalent local setup) making `fetch()` calls to `/api/cart/create` on a different origin. Without `setExposedHeaders`, log `response.headers.get('X-Auth-Token')` in browser JavaScript: expect `null`, even though the browser's network tab clearly shows the header was sent. With `setExposedHeaders` correctly configured: expect the JavaScript code to successfully read the actual token value, letting it store and resend it on subsequent calls.

What changed and why it's production-flavored: this closes a specific, easy-to-miss CORS gap that has nothing to do with Spring Session itself and everything to do with browser security defaults — a header-based session API consumed by browser-based client code is silently broken without this exact configuration, and the failure mode (the header is visibly sent, but invisible to the client's own JavaScript) is confusing enough that it commonly costs real debugging time before the root cause is identified.

## 6. Walkthrough

Tracing a header-based session interaction from a browser-based SPA client, in execution order:

1. The SPA calls `fetch('/api/cart/create', { method: 'POST' })` from `https://spa.example.com`, targeting a different-origin API server.
2. The browser first checks CORS: since this is a simple enough request in this example (though a real app's headers might trigger a preflight `OPTIONS` check first), it proceeds, and `CorsFilter` (Level 3) confirms `https://spa.example.com` is an allowed origin before the request reaches the controller.
3. `HeaderCartApiController.create(...)` runs, creating a session and — via `HeaderHttpSessionIdResolver` — including `X-Auth-Token: <new session id>` in the response.
4. The response returns to the browser; because `Access-Control-Expose-Headers` includes `X-Auth-Token` (Level 3), the browser's CORS enforcement permits the SPA's JavaScript to actually read that header's value from the `fetch` response object — without this, the header would be present on the wire but invisible to the calling code.
5. The SPA's JavaScript stores this token (in memory, or another storage mechanism it manages itself) and includes it as `X-Auth-Token` on the next call, `fetch('/api/cart/add?item=book', { headers: { 'X-Auth-Token': token } })`.
6. `RobustHeaderCartApiController.addItem(...)` (Level 2) receives this request; `session.isNew()` returns `false` (the token correctly resolved to the existing session), so the item is added to the already-existing cart rather than a fresh one.
7. If, instead, the stored token had expired server-side by this point, `session.isNew()` would return `true` despite a token being present — triggering the explicit `session_expired` response instead, giving the SPA's error-handling code a clear, actionable signal to show the user rather than silently and confusingly starting a new, empty cart.

```
SPA (different origin) -> POST /api/cart/create
   |
CorsFilter: origin allowed? --> proceed
   |
controller creates session -> X-Auth-Token: abc123 in response
   |
Access-Control-Expose-Headers includes X-Auth-Token --> browser JS CAN read it
   |
SPA stores token, includes on next call: X-Auth-Token: abc123
   |
controller: session.isNew()? --false (token resolved)--> add to existing cart
                              --true (token expired/invalid)--> 401 session_expired
```

## 7. Gotchas & takeaways

> `Access-Control-Expose-Headers` is required for any custom response header (like `X-Auth-Token`) to be readable by browser JavaScript under CORS — this is a browser security default, not a Spring Session limitation, and its absence produces one of the most confusing classes of bugs in this pattern: the header is visibly present in the browser's network inspector tab, yet completely inaccessible to the application's own `fetch`/`XMLHttpRequest` code.

- Distinguish "no token was ever sent" from "a token was sent but doesn't resolve to a valid session" (Level 2) in API error responses — client applications need to react differently to each case (prompt fresh setup versus surface a clear "your session expired" message), and collapsing both into the same generic behavior makes debugging client-side issues harder for API consumers.
- Header-based session tokens carry the same general security considerations as any bearer-style token — client-side storage choice matters (an in-memory JavaScript variable is safer against certain attack classes than `localStorage`), and the token should always be transmitted over HTTPS only, exactly as any authentication bearer token would be.
- This pattern is genuinely optional complexity — plenty of REST APIs are, and should remain, fully stateless with no server-side session concept at all; reach for header-based sessions specifically when there's a real multi-request, server-tracked state requirement (a cart, a wizard), not merely because "the API doesn't use cookies."
- CORS preflight requests (`OPTIONS`) for any request including custom headers like `X-Auth-Token` need the server's CORS configuration to correctly handle and respond to them — a CORS setup that only accounts for the "simple" request case will fail once a client sends a custom header that triggers browser preflight behavior.
- Test this pattern with an actual cross-origin browser client at least once before considering it complete — `curl`-based testing (as shown in Levels 1 and 2) never exercises CORS at all, since CORS is a browser-enforced mechanism, not a server-side behavior that non-browser HTTP clients respect or even notice.
