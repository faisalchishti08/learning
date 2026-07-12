---
card: spring-security
gi: 106
slug: bearer-token-resolution
title: "Bearer token resolution"
---

## 1. What it is

Every card in this section has assumed the bearer token arrives in an `Authorization: Bearer <token>` header — that's `DefaultBearerTokenResolver`'s behavior, and it's what `oauth2ResourceServer()` wires up automatically. `BearerTokenResolver` is the actual extension point behind that assumption: a single-method interface (`String resolve(HttpServletRequest request)`) responsible only for locating the raw token string somewhere in the incoming request, before any decoding or introspection (cards 0100–0105) ever begins. Its default implementation also optionally accepts the token as a form parameter or query parameter (both disabled by default, since both leak tokens into server logs and browser history far more easily than a header does), and a fully custom `BearerTokenResolver` can look anywhere else entirely — a cookie, a custom header, a WebSocket handshake parameter.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    DefaultBearerTokenResolver resolver = new DefaultBearerTokenResolver();
    resolver.setAllowFormEncodedBodyParameter(false); // default; explicit here for clarity
    resolver.setAllowUriQueryParameter(false);        // default; explicit here for clarity

    http.oauth2ResourceServer(oauth2 -> oauth2.bearerTokenResolver(resolver));
    return http.build();
}
```

## 2. Why & when

Cards 0100–0105 all start from "a bearer token arrived" without ever asking *how* it arrived — this card exists because that question has a real, security-relevant answer, and because not every client can put a token in an `Authorization` header at all. Browser-based EventSource/SSE connections and some WebSocket clients historically couldn't set custom headers, forcing tokens into query strings as the only option — but a token in a URL ends up in access logs, proxy logs, browser history, and `Referer` headers sent to third-party resources, any of which can leak it. Understanding `BearerTokenResolver` as a distinct, replaceable component is what lets an application make a deliberate, informed choice about where it will and won't accept a token from, rather than inheriting whatever the framework happens to check by default.

Reach for a custom `BearerTokenResolver` when:

- A specific legacy or constrained client genuinely cannot set an `Authorization` header (some browser `EventSource` APIs, certain embedded devices) — a custom resolver checking a specific alternative location can be scoped narrowly, rather than globally enabling the built-in (and broadly discouraged) query-parameter support.
- Tokens need to be read from a cookie instead of a header — for a browser-based single-page application that wants the resource-server benefits of statelessness without manually attaching an `Authorization` header to every request, at the cost of needing separate CSRF protection, since cookies are sent automatically by the browser.
- Debugging why a request that "should" be authenticated is coming back `401` — verifying that the token is actually where the configured resolver expects to find it is one of the first things to check, since a resolver that finds nothing behaves identically (from the resource server's point of view) to no token having been sent at all.
- Auditing whether query-parameter or form-parameter token support is enabled in an existing application — since both are security-relevant defaults-off features, finding either explicitly turned on is worth scrutinizing for exactly why.

## 3. Core concept

```
BearerTokenResolver.resolve(request) -> String (the raw token) or null

DefaultBearerTokenResolver, in order of what it checks:
  1. Authorization: Bearer <token> header               -- ALWAYS checked, this is the standard, safest path
  2. form-encoded body parameter "access_token"          -- ONLY if allowFormEncodedBodyParameter(true)
  3. URI query parameter "access_token"                  -- ONLY if allowUriQueryParameter(true)

  -- finding a token in MORE THAN ONE of these places on the SAME request is a hard error
     (ambiguous credential presentation -> reject, don't guess which one to trust)

Registration point:
    http.oauth2ResourceServer(oauth2 -> oauth2.bearerTokenResolver(myResolver))

CUSTOM resolver -- implement the interface directly:
    class CookieBearerTokenResolver implements BearerTokenResolver {
        public String resolve(HttpServletRequest request) {
            Cookie cookie = findCookie(request, "access_token");
            return cookie != null ? cookie.getValue() : null;
        }
    }
```

The resolver's only job is finding the raw string; everything about validating it (cards 0100–0105) happens entirely afterward, unaffected by where the token came from.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing the default bearer token resolver checking the authorization header first then optionally a form parameter then optionally a query parameter finding a token in more than one location is treated as an error rather than an arbitrary choice">
  <rect x="20" y="20" width="240" height="170" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="140" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DefaultBearerTokenResolver</text>

  <rect x="40" y="55" width="200" height="34" rx="6" fill="#161b22" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="76" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">1. Authorization: Bearer ... (ALWAYS)</text>

  <rect x="40" y="98" width="200" height="34" rx="6" fill="#161b22" stroke="#f0883e" stroke-width="1.2"/>
  <text x="140" y="119" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">2. form param (opt-in, default OFF)</text>

  <rect x="40" y="141" width="200" height="34" rx="6" fill="#161b22" stroke="#f85149" stroke-width="1.2"/>
  <text x="140" y="162" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">3. query param (opt-in, default OFF)</text>

  <line x1="270" y1="105" x2="330" y2="105" stroke="#6db33f" stroke-width="1.6" marker-end="url(#bt106)"/>

  <rect x="335" y="80" width="290" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="480" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">raw token string</text>
  <text x="480" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">passed on to JwtDecoder / introspector</text>

  <rect x="335" y="145" width="290" height="46" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="480" y="164" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">found in MULTIPLE locations at once</text>
  <text x="480" y="180" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; hard error, NOT an arbitrary pick</text>

  <defs><marker id="bt106" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Only the header is checked by default; the two alternative locations are opt-in precisely because they're more prone to leaking the token.

## 5. Runnable example

The scenario: a from-scratch `BearerTokenResolver` implementing the header-first default behavior, growing to add opt-in query-parameter support with its ambiguity check, then to a fully custom cookie-based resolver for a browser client that never sets the header at all.

### Level 1 — Basic

Header-only resolution — the always-on, safest path.

```java
import java.util.*;

public class BearerResolutionLevel1 {
    record Request(Map<String, String> headers) {
        String header(String name) { return headers.get(name); }
    }

    static String resolve(Request request) {
        String authHeader = request.header("Authorization");
        if (authHeader != null && authHeader.startsWith("Bearer ")) {
            return authHeader.substring("Bearer ".length());
        }
        return null; // no token found -- NOT an error by itself, just "unauthenticated so far"
    }

    public static void main(String[] args) {
        Request withToken = new Request(Map.of("Authorization", "Bearer abc123"));
        Request withoutToken = new Request(Map.of());

        System.out.println("resolved: " + resolve(withToken));
        System.out.println("resolved: " + resolve(withoutToken));
    }
}
```

**How to run:** save as `BearerResolutionLevel1.java`, run `java BearerResolutionLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
resolved: abc123
resolved: null
```

`resolve` mirrors `DefaultBearerTokenResolver`'s always-on first check — the `Authorization` header, checked for the exact `"Bearer "` prefix. A request without one simply resolves to `null`, which downstream code (card 0100) correctly treats as "no credential presented," not a malformed one.

### Level 2 — Intermediate

Add opt-in query-parameter support, plus the ambiguity check: a token present in *both* locations at once must be rejected outright, not silently resolved to one or the other.

```java
import java.util.*;

public class BearerResolutionLevel2 {
    record Request(Map<String, String> headers, Map<String, String> queryParams) {
        String header(String name) { return headers.get(name); }
        String queryParam(String name) { return queryParams.get(name); }
    }

    static class BearerTokenResolutionException extends RuntimeException {
        BearerTokenResolutionException(String message) { super(message); }
    }

    static class ConfigurableBearerTokenResolver {
        private boolean allowUriQueryParameter = false;

        void setAllowUriQueryParameter(boolean allow) { this.allowUriQueryParameter = allow; }

        String resolve(Request request) {
            String fromHeader = null;
            String authHeader = request.header("Authorization");
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                fromHeader = authHeader.substring("Bearer ".length());
            }

            String fromQuery = allowUriQueryParameter ? request.queryParam("access_token") : null;

            if (fromHeader != null && fromQuery != null) {
                // ambiguous: a token in TWO places at once is a hard error, never an arbitrary pick
                throw new BearerTokenResolutionException("token found in both the header AND the query parameter");
            }
            return fromHeader != null ? fromHeader : fromQuery;
        }
    }

    public static void main(String[] args) {
        ConfigurableBearerTokenResolver resolver = new ConfigurableBearerTokenResolver();
        resolver.setAllowUriQueryParameter(true);

        Request headerOnly = new Request(Map.of("Authorization", "Bearer abc123"), Map.of());
        Request queryOnly = new Request(Map.of(), Map.of("access_token", "xyz789"));
        Request both = new Request(Map.of("Authorization", "Bearer abc123"), Map.of("access_token", "xyz789"));

        System.out.println("header only: " + resolver.resolve(headerOnly));
        System.out.println("query only: " + resolver.resolve(queryOnly));

        try {
            resolver.resolve(both);
        } catch (BearerTokenResolutionException e) {
            System.out.println("ambiguous request rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `BearerResolutionLevel2.java`, run `java BearerResolutionLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
header only: abc123
query only: xyz789
ambiguous request rejected: token found in both the header AND the query parameter
```

What changed: with `allowUriQueryParameter(true)`, a token in the query string is now accepted as an alternative to the header — but a request presenting *both* is rejected outright rather than the resolver silently picking one, mirroring `DefaultBearerTokenResolver`'s actual behavior: ambiguity in how a credential is presented is treated as suspicious, not as a minor inconsistency to paper over.

### Level 3 — Advanced

A fully custom resolver reading from a cookie instead — for a browser client that never sets an `Authorization` header at all — combined with the header path still available for non-browser clients, and both paths subject to the same ambiguity rule.

```java
import java.util.*;

public class BearerResolutionLevel3 {
    record Request(Map<String, String> headers, Map<String, String> cookies) {
        String header(String name) { return headers.get(name); }
        String cookie(String name) { return cookies.get(name); }
    }

    static class BearerTokenResolutionException extends RuntimeException {
        BearerTokenResolutionException(String message) { super(message); }
    }

    interface BearerTokenResolver { String resolve(Request request); }

    static class HeaderBearerTokenResolver implements BearerTokenResolver {
        public String resolve(Request request) {
            String authHeader = request.header("Authorization");
            return (authHeader != null && authHeader.startsWith("Bearer "))
                    ? authHeader.substring("Bearer ".length()) : null;
        }
    }

    // a CUSTOM resolver -- reads from a cookie instead, for a browser client that can't set the header
    static class CookieBearerTokenResolver implements BearerTokenResolver {
        private final String cookieName;
        CookieBearerTokenResolver(String cookieName) { this.cookieName = cookieName; }
        public String resolve(Request request) { return request.cookie(cookieName); }
    }

    // COMPOSES both resolvers, applying the same ambiguity rule across ALL sources, not just two hardcoded ones
    static class CompositeBearerTokenResolver implements BearerTokenResolver {
        private final List<BearerTokenResolver> delegates;
        CompositeBearerTokenResolver(List<BearerTokenResolver> delegates) { this.delegates = delegates; }

        public String resolve(Request request) {
            List<String> found = new ArrayList<>();
            for (BearerTokenResolver delegate : delegates) {
                String token = delegate.resolve(request);
                if (token != null) found.add(token);
            }
            if (found.size() > 1) {
                throw new BearerTokenResolutionException("token found via " + found.size() + " different resolvers -- ambiguous");
            }
            return found.isEmpty() ? null : found.get(0);
        }
    }

    public static void main(String[] args) {
        CompositeBearerTokenResolver resolver = new CompositeBearerTokenResolver(List.of(
                new HeaderBearerTokenResolver(),
                new CookieBearerTokenResolver("access_token")));

        // a non-browser API client, using the standard header
        Request apiClientRequest = new Request(Map.of("Authorization", "Bearer abc123"), Map.of());
        System.out.println("API client (header): " + resolver.resolve(apiClientRequest));

        // a browser client that never sets the header, relying on the cookie instead
        Request browserRequest = new Request(Map.of(), Map.of("access_token", "cookie-token-xyz"));
        System.out.println("browser client (cookie): " + resolver.resolve(browserRequest));

        // neither present -- genuinely unauthenticated
        Request anonymousRequest = new Request(Map.of(), Map.of());
        System.out.println("anonymous request: " + resolver.resolve(anonymousRequest));

        // BOTH present at once -- still ambiguous, regardless of WHICH two sources are involved
        Request suspiciousRequest = new Request(Map.of("Authorization", "Bearer abc123"), Map.of("access_token", "cookie-token-xyz"));
        try {
            resolver.resolve(suspiciousRequest);
        } catch (BearerTokenResolutionException e) {
            System.out.println("suspicious request rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `BearerResolutionLevel3.java`, run `java BearerResolutionLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
API client (header): abc123
browser client (cookie): cookie-token-xyz
anonymous request: null
suspicious request rejected: token found via 2 different resolvers -- ambiguous
```

What changed: `CompositeBearerTokenResolver` generalizes the ambiguity rule to work across *any* number and combination of underlying resolvers, not just a fixed header-versus-query pair — a header-based API client and a cookie-based browser client are both served by the same composed resolver, each getting its token from its own natural source, while a request presenting credentials via more than one path at once is rejected identically to Level 2's case, regardless of which specific two sources happened to collide.

## 6. Walkthrough

Trace the browser client's cookie-based request from Level 3 end to end, then contrast it with the ambiguous rejection.

**Step 1 — the inbound request, from a browser that stores its token in a cookie rather than setting an `Authorization` header:**
```
GET /api/orders HTTP/1.1
Host: api.example.com
Cookie: access_token=cookie-token-xyz
```

**Step 2 — the composite resolver is invoked** (this is `oauth2ResourceServer(oauth2 -> oauth2.bearerTokenResolver(resolver))`'s registered resolver, running before `JwtDecoder`/introspection ever sees anything). It iterates its `delegates` list.

**Step 3 — the header resolver runs first and finds nothing.** `HeaderBearerTokenResolver.resolve(browserRequest)` checks `request.header("Authorization")`, which is `null` for this request (the browser never set it) — this delegate contributes nothing to `found`.

**Step 4 — the cookie resolver runs next and finds the token.** `CookieBearerTokenResolver.resolve(browserRequest)` checks `request.cookie("access_token")`, which is `"cookie-token-xyz"` — this delegate contributes exactly one value to `found`.

**Step 5 — exactly one token was found, so no ambiguity.** `found.size()` is `1`, so `CompositeBearerTokenResolver` does not throw; it returns `found.get(0)`, `"cookie-token-xyz"`.

**Step 6 — resolution's result feeds directly into card 0100's flow.** The resolved string is handed to `JwtDecoder.decode(...)` (or the opaque-token introspector) exactly as if it had arrived via the standard header — resolution and validation are fully decoupled; nothing downstream needs to know or care which source the token came from.

**Contrast — the suspicious, dual-source request.** For `suspiciousRequest`, step 3's header resolver *does* find `"abc123"`, and step 4's cookie resolver *also* finds `"cookie-token-xyz"` — `found` now has two entries. `found.size() > 1` is `true`, so `CompositeBearerTokenResolver` throws `BearerTokenResolutionException` before any decoding is attempted at all; a real resource server would respond:
```
HTTP/1.1 400 Bad Request
```
(Spring Security's real `DefaultBearerTokenResolver` responds with an `OAuth2AuthenticationException` mapped to a `400`, distinct from the `401`s seen throughout this section for invalid-but-unambiguous tokens — a genuinely malformed *request*, not merely an unauthenticated or badly-authenticated one.)

```
browser request:  header=null, cookie="cookie-token-xyz"  -> found=[cookie-token-xyz] -> resolved, proceeds to decode
suspicious request: header="abc123", cookie="cookie-token-xyz" -> found=[abc123, cookie-token-xyz] -> AMBIGUOUS -> 400, rejected before decode
```

## 7. Gotchas & takeaways

> **Gotcha:** enabling `allowUriQueryParameter` (or building a custom resolver that reads tokens from a URL) reintroduces every problem that design choice is disabled by default to avoid — the token ends up in web server access logs, proxy logs, browser history, and any `Referer` header sent when the page links to a third-party resource. Only enable it for a specific, well-understood legacy constraint, never as a general convenience.

- `BearerTokenResolver` is the extension point for *where* a token is found in a request — entirely separate from *how* it's validated once found (cards 0100–0105), and can be swapped independently.
- `DefaultBearerTokenResolver` checks the `Authorization` header always, and a form-body or query parameter only if explicitly enabled — both alternatives are off by default because they're more prone to leaking the token than a header is.
- A token found in more than one location on the same request is treated as an error, not resolved by picking one arbitrarily — ambiguous credential presentation is itself a signal worth rejecting outright.
- A custom resolver (reading a cookie, a custom header, a WebSocket handshake parameter) is a legitimate way to support clients that cannot use the standard `Authorization` header, as long as the same care around leakage and ambiguity is preserved.
- Resolution failing (returning `null`) is not itself an authentication failure — it simply means no credential was presented, which `authorizeHttpRequests` then evaluates like any other unauthenticated request.
