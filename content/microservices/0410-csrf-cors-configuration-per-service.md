---
card: microservices
gi: 410
slug: csrf-cors-configuration-per-service
title: "CSRF / CORS configuration per service"
---

## 1. What it is

**CSRF** (Cross-Site Request Forgery) protection and **CORS** (Cross-Origin Resource Sharing) configuration are two distinct browser-security mechanisms that every browser-facing microservice must configure deliberately, not just accept the framework defaults blindly. CSRF protection stops a malicious site from tricking a logged-in user's browser into submitting an unwanted request to your service using the user's own cookies. CORS configuration controls which *other* origins (websites) are allowed to make cross-origin requests to your service from JavaScript at all. They solve different, easily confused problems, and getting either one wrong either blocks legitimate traffic or, worse, opens a real vulnerability.

## 2. Why & when

You configure these per service because each microservice may have a different exposure profile: a public API meant to be called from a partner's web app needs permissive CORS but not necessarily CSRF protection; an internal admin service using cookie-based sessions needs CSRF protection but should have CORS locked down to nothing at all.

- **CSRF matters specifically for cookie-based, browser session authentication.** If a service uses cookies to identify a logged-in user, a malicious page can make the browser send a request with those cookies attached automatically — CSRF protection (a per-session token the attacker's page can't read) stops the forged request from being accepted.
- **CSRF does *not* matter for pure token-based APIs** where the client must explicitly attach an `Authorization: Bearer <token>` header — a malicious page can't make the browser attach a header it doesn't already know, so there's nothing to forge. This is why a stateless [JWT-based resource server](0401-spring-security-oauth2-resource-server-jwt-opaque.md) commonly disables CSRF protection entirely.
- **CORS matters whenever a browser-based frontend on one origin calls an API on a different origin** (different scheme, host, or port) — without CORS headers, the browser blocks the response from ever reaching the frontend's JavaScript, regardless of whether the server would have answered.
- **Misconfiguring either is a real vulnerability, not just an inconvenience:** disabling CSRF on a cookie-based service opens it to forged state-changing requests; setting CORS to allow any origin (`*`) *combined with* allowing credentials opens the door for any website to make authenticated calls on a logged-in user's behalf.

## 3. Core concept

Think of CORS as a bouncer at your API's front door checking a guest list of *which websites' JavaScript* is allowed to read the response — it's the *browser* enforcing this, on behalf of the user, based on headers your server sends. Think of CSRF protection as a wristband stamped at check-in: even someone already inside (a request carrying valid session cookies) must also present the matching wristband (an unpredictable CSRF token) proving the request actually originated from your own page, not from some other page that merely borrowed the visitor's cookies.

```java
@Configuration
@EnableWebSecurity
public class WebSecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
                // CSRF: keep enabled for a cookie/session-based browser app, using the
                // cookie-based token repository so a JS frontend can read it and echo it back.
                .csrf(csrf -> csrf.csrfTokenRepository(CookieCsrfTokenRepository.withHttpOnlyFalse()))
                // CORS: only this specific frontend origin may call this API from a browser.
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                .authorizeHttpRequests(authz -> authz.anyRequest().authenticated())
                .build();
    }

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration config = new CorsConfiguration();
        config.setAllowedOrigins(List.of("https://app.example.com")); // NOT "*" -- credentials require an explicit origin
        config.setAllowedMethods(List.of("GET", "POST", "PUT", "DELETE"));
        config.setAllowCredentials(true); // cookies are sent cross-origin
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
```

Key distinctions to hold onto:

1. **CORS is a browser-enforced allowlist for cross-origin *reads*** — it never protects a server from a request actually arriving; it only controls whether the browser lets the calling page's JavaScript *see the response*. A non-browser client (curl, another service) ignores CORS entirely.
2. **CSRF is server-enforced protection against forged *state-changing* requests** riding on ambient credentials (cookies) the browser attaches automatically, regardless of which page initiated the request.
3. **`allowCredentials(true)` combined with a wildcard origin (`*`) is invalid and dangerous** — browsers actively reject this combination, and frameworks should too, because it would let any website make authenticated, cookie-carrying requests to your API.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="CORS is checked by the browser before it lets JavaScript on one origin read a response from another origin; CSRF protection is checked by the server to confirm a state-changing request carrying session cookies actually originated from its own page, not a forged cross-site request" font-family="sans-serif">
  <text x="165" y="20" fill="#e6edf3" font-size="11" text-anchor="middle">CORS (browser-enforced)</text>
  <rect x="30" y="35" width="120" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="56" fill="#e6edf3" font-size="9" text-anchor="middle">app.example.com JS</text>
  <rect x="210" y="35" width="120" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="270" y="56" fill="#e6edf3" font-size="9" text-anchor="middle">api.example.com</text>
  <line x1="150" y1="52" x2="205" y2="52" stroke="#8b949e" marker-end="url(#c410)"/>
  <text x="180" y="45" fill="#8b949e" font-size="7" text-anchor="middle">fetch()</text>
  <line x1="205" y1="66" x2="150" y2="66" stroke="#6db33f" marker-end="url(#c410)"/>
  <text x="180" y="80" fill="#6db33f" font-size="7" text-anchor="middle">response + Access-Control-Allow-Origin</text>
  <text x="90" y="95" fill="#79c0ff" font-size="8" text-anchor="middle">browser blocks JS from</text>
  <text x="90" y="107" fill="#79c0ff" font-size="8" text-anchor="middle">reading it if origin not allowed</text>

  <text x="500" y="20" fill="#e6edf3" font-size="11" text-anchor="middle">CSRF (server-enforced)</text>
  <rect x="400" y="35" width="120" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="460" y="56" fill="#e6edf3" font-size="9" text-anchor="middle">evil-site.com page</text>
  <rect x="580" y="35" width="60" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="610" y="56" fill="#e6edf3" font-size="9" text-anchor="middle">API</text>
  <line x1="520" y1="52" x2="575" y2="52" stroke="#f85149" marker-end="url(#c410)"/>
  <text x="548" y="45" fill="#f85149" font-size="7" text-anchor="middle">forged POST + cookies</text>
  <text x="548" y="95" fill="#f0883e" font-size="8" text-anchor="middle">server REJECTS: missing/invalid</text>
  <text x="548" y="107" fill="#f0883e" font-size="8" text-anchor="middle">CSRF token the forged page can't supply</text>

  <defs>
    <marker id="c410" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

CORS controls whether a browser lets JavaScript on one origin read a response from another; CSRF protection stops a forged request from a different page succeeding even though it carries valid session cookies.

## 5. Runnable example

Scenario: a cookie-based "transfer funds" endpoint. We model it first with no protections at all (a forged cross-site request succeeds), then add CSRF token verification (the forged request is rejected), then add CORS origin checking on top so only an approved frontend origin's browser JavaScript can even read a legitimate response.

### Level 1 — Basic

```java
// File: UnprotectedCookieEndpoint.java -- a cookie-authenticated endpoint
// with NO CSRF protection: any request carrying a valid session cookie is
// accepted, regardless of what page actually caused the browser to send it.
import java.util.*;

public class UnprotectedCookieEndpoint {
    static final Map<String, String> ACTIVE_SESSIONS = Map.of("session-abc", "user-42");

    static String transferFunds(String sessionCookie, String toAccount, double amount) {
        String userId = ACTIVE_SESSIONS.get(sessionCookie);
        if (userId == null) return "401 Unauthorized";
        return "200 OK -- transferred $" + amount + " to " + toAccount + " for " + userId;
    }

    public static void main(String[] args) {
        // A legitimate request from the real app...
        System.out.println("Legit request:  " + transferFunds("session-abc", "user-42-savings", 50));
        // ...and a request the browser sent because evil-site.com's hidden form auto-submitted,
        // carrying the SAME cookie automatically -- indistinguishable to this endpoint.
        System.out.println("Forged request: " + transferFunds("session-abc", "attacker-account", 5000));
    }
}
```

How to run: `java UnprotectedCookieEndpoint.java`

`transferFunds` only checks whether `sessionCookie` maps to a valid, logged-in user — it has no way to tell whether the request was intentionally submitted by the user on the real site, or auto-submitted by a hidden form on `evil-site.com` that the user's browser attached the session cookie to automatically (browsers attach cookies to *any* request to a domain, regardless of which page triggered it). Both requests succeed identically, meaning a forged transfer to `attacker-account` goes through exactly like a legitimate one.

### Level 2 — Intermediate

```java
// File: CsrfProtectedEndpoint.java -- adds a CSRF TOKEN check: a
// state-changing request must now present a token that only the real page
// (which fetched it from the server first) could know, closing the Level 1 gap.
import java.util.*;

public class CsrfProtectedEndpoint {
    static final Map<String, String> ACTIVE_SESSIONS = Map.of("session-abc", "user-42");
    static final Map<String, String> CSRF_TOKENS = Map.of("session-abc", "csrf-token-xyz789"); // issued per session

    static String transferFunds(String sessionCookie, String presentedCsrfToken, String toAccount, double amount) {
        String userId = ACTIVE_SESSIONS.get(sessionCookie);
        if (userId == null) return "401 Unauthorized";
        String expectedToken = CSRF_TOKENS.get(sessionCookie);
        if (!Objects.equals(expectedToken, presentedCsrfToken)) {
            return "403 Forbidden -- missing or invalid CSRF token";
        }
        return "200 OK -- transferred $" + amount + " to " + toAccount + " for " + userId;
    }

    public static void main(String[] args) {
        // Legit request: the real page fetched the CSRF token from the server first and echoes it back.
        System.out.println("Legit request:  " + transferFunds("session-abc", "csrf-token-xyz789", "user-42-savings", 50));
        // Forged request: evil-site.com's hidden form has the session cookie (browser attaches it automatically),
        // but has NO WAY to know the CSRF token, because cross-origin JavaScript can't read it.
        System.out.println("Forged request: " + transferFunds("session-abc", null, "attacker-account", 5000));
    }
}
```

How to run: `java CsrfProtectedEndpoint.java`

`transferFunds` now requires a second, independent piece of proof: a CSRF token that matches the one issued for this session. The real frontend obtains this token from the server (typically via a cookie or a response header the page's own JavaScript can read) and includes it explicitly in the request. `evil-site.com`'s forged form submission still carries the session cookie automatically — cookies aren't protected by same-origin policy — but it has no legitimate way to read or guess the CSRF token, so it's rejected with `403 Forbidden`, closing exactly the gap Level 1 left open.

### Level 3 — Advanced

```java
// File: CsrfAndCorsProtectedEndpoint.java -- adds CORS origin checking on
// TOP of CSRF protection, modeling the browser-side enforcement: even a
// request that COULD pass CSRF is only useful to an attacker if the
// browser also lets their page's JS read the response -- CORS blocks that
// for any origin not on the explicit allowlist.
import java.util.*;

public class CsrfAndCorsProtectedEndpoint {
    static final Set<String> ALLOWED_ORIGINS = Set.of("https://app.example.com");
    static final Map<String, String> ACTIVE_SESSIONS = Map.of("session-abc", "user-42");
    static final Map<String, String> CSRF_TOKENS = Map.of("session-abc", "csrf-token-xyz789");

    record Response(int status, String body, boolean browserWouldExposeToJs) {}

    static Response transferFunds(String requestOrigin, String sessionCookie, String presentedCsrfToken,
                                   String toAccount, double amount) {
        String userId = ACTIVE_SESSIONS.get(sessionCookie);
        if (userId == null) return new Response(401, "Unauthorized", false);

        String expectedToken = CSRF_TOKENS.get(sessionCookie);
        if (!Objects.equals(expectedToken, presentedCsrfToken)) {
            return new Response(403, "Forbidden -- invalid CSRF token", false);
        }

        // The SERVER still processes the request and sets CORS response headers --
        // but whether the CALLING PAGE'S JS can actually read the response is decided by the BROWSER,
        // based on whether requestOrigin is on the allowlist.
        boolean corsAllowed = ALLOWED_ORIGINS.contains(requestOrigin);
        String body = "Transferred $" + amount + " to " + toAccount + " for " + userId;
        return new Response(200, body, corsAllowed); // browser hides the body from JS if corsAllowed is false
    }

    public static void main(String[] args) {
        Response fromRealApp = transferFunds("https://app.example.com", "session-abc", "csrf-token-xyz789", "user-42-savings", 50);
        System.out.println("From real app origin: status=" + fromRealApp.status()
                + ", JS on that page CAN read response: " + fromRealApp.browserWouldExposeToJs());

        // Suppose an attacker somehow obtained a valid CSRF token too (e.g. via a separate flaw) --
        // CORS is still a SEPARATE, independent layer that stops their page's JS from reading the result.
        Response fromEvilOrigin = transferFunds("https://evil-site.com", "session-abc", "csrf-token-xyz789", "attacker-account", 5000);
        System.out.println("From evil-site.com origin: status=" + fromEvilOrigin.status()
                + ", JS on that page CAN read response: " + fromEvilOrigin.browserWouldExposeToJs()
                + " -- server processed it, but the BROWSER hides the response from evil-site.com's JavaScript");
    }
}
```

How to run: `java CsrfAndCorsProtectedEndpoint.java`

This models an important subtlety: CORS doesn't stop the server from *processing* a request (that's CSRF's job) — it stops the *browser* from letting the calling page's JavaScript *read the response*. The `browserWouldExposeToJs` flag is `true` only when `requestOrigin` is on `ALLOWED_ORIGINS`. The real app's origin gets both a successful transfer and the ability to read the confirmation. The simulated `evil-site.com` case shows that even with a hypothetically-leaked CSRF token, its own JavaScript still can't read the response — because CORS is enforced independently by the browser based on origin, not on whether the request was otherwise "valid." In practice, `evil-site.com` couldn't have gotten the CSRF token either (Level 2), so real attacks are stopped twice over — this layer illustrates why the two protections are complementary rather than redundant.

## 6. Walkthrough

Trace `CsrfAndCorsProtectedEndpoint.main` in order. **First**, `transferFunds("https://app.example.com", "session-abc", "csrf-token-xyz789", ...)` runs. `ACTIVE_SESSIONS.get("session-abc")` resolves to `"user-42"`, so authentication passes. `CSRF_TOKENS.get("session-abc")` is `"csrf-token-xyz789"`, matching the presented token, so CSRF passes. `ALLOWED_ORIGINS.contains("https://app.example.com")` is `true`, so `corsAllowed` is `true`. The method returns `Response(200, "Transferred $50...", true)`.

**Next**, `main` prints that response: status `200`, and `browserWouldExposeToJs = true` — the real app's page can both trigger the transfer and read back confirmation of it.

**Then**, `transferFunds("https://evil-site.com", "session-abc", "csrf-token-xyz789", ...)` runs, using the *same* valid CSRF token to model a hypothetical worst case. Authentication and CSRF checks both pass identically to the first call (the server has no origin-based logic in its CSRF check). But `ALLOWED_ORIGINS.contains("https://evil-site.com")` is `false`, so `corsAllowed` is `false`. The method still returns `200` with the transfer body — the server-side operation happened — but with `browserWouldExposeToJs = false`.

**Finally**, `main` prints this second response: status `200`, but `browserWouldExposeToJs = false` — in a real browser, this means `evil-site.com`'s JavaScript would receive a network error trying to read the response body, even though (in this artificial scenario) the transfer itself occurred server-side. This is precisely why CORS alone never substitutes for CSRF protection: CORS can't stop the request from being processed, only from being *read back* by unauthorized JavaScript.

```
transferFunds(app.example.com, valid session, valid csrf) -> 200, JS CAN read response
transferFunds(evil-site.com,  valid session, valid csrf) -> 200 (processed!), JS CANNOT read response
```

## 7. Gotchas & takeaways

> CORS is not a request-blocking mechanism — it is a *response-reading* permission enforced entirely by the browser. A same-origin tool like `curl`, a mobile app, or a server-to-server call completely ignores CORS headers and will happily receive the full response regardless of what `Access-Control-Allow-Origin` says. Relying on CORS as your only protection for a state-changing endpoint is a mistake: CSRF protection is what actually stops the forged request from being *processed* in the first place.

- CSRF protection defends against forged state-changing requests riding on cookies the browser attaches automatically; it matters most for cookie/session-based authentication.
- CORS controls whether a browser lets cross-origin JavaScript read a response at all; it's irrelevant to non-browser clients and doesn't stop a request from being processed server-side.
- Pure token-based APIs (`Authorization: Bearer <token>`, as in a [JWT resource server](0401-spring-security-oauth2-resource-server-jwt-opaque.md)) commonly disable CSRF protection, because there's no ambient credential for a forged page to exploit — the attacker's page can't attach a header it doesn't know.
- Never combine `allowCredentials(true)` with a wildcard CORS origin (`*`) — browsers reject it, and frameworks should be configured to reject it too, since it would let any site make authenticated, cookie-carrying calls.
- Configure both per service based on its actual exposure: a public token-based API might need permissive CORS and no CSRF; an internal cookie-based admin panel needs the opposite emphasis.
