---
card: spring-cloud
gi: 51
slug: cors-configuration
title: "CORS configuration"
---

## 1. What it is

Cross-Origin Resource Sharing (CORS) configuration tells browsers which external origins (a web app served from a different domain) are allowed to call the gateway's APIs directly from JavaScript. Since the gateway is a single entry point for potentially many backend services, configuring CORS once at the gateway means individual backends never need their own CORS setup at all.

```yaml
spring:
  cloud:
    gateway:
      globalcors:
        cors-configurations:
          '[/**]':
            allowedOrigins: "https://app.example.com"
            allowedMethods: GET,POST,PUT,DELETE
            allowedHeaders: "*"
            allowCredentials: true
            maxAge: 3600
```

## 2. Why & when

Browsers enforce the same-origin policy by default: JavaScript running on `https://app.example.com` can't call `https://api.example.com` unless the server explicitly says it's allowed to, via CORS response headers — and for anything beyond a simple `GET`, the browser first sends a "preflight" `OPTIONS` request asking permission before sending the real one. Configuring this at the gateway, once, in one place, means every backend service benefits without each one separately implementing CORS handling (and potentially getting it subtly wrong, or inconsistent, across services).

Configure CORS deliberately when:

- A browser-based frontend (a single-page app, a separately-hosted marketing site making API calls) is served from a different origin than the gateway's own domain.
- Multiple frontends with different trust levels need different CORS policies — a public marketing site might get a narrower policy than an authenticated internal admin dashboard.
- `allowCredentials: true` is needed (cookies, `Authorization` headers sent cross-origin) — this specifically requires `allowedOrigins` to list exact origins, since browsers reject the wildcard `"*"` combined with credentials for security reasons.

## 3. Core concept

```
 browser preflight (for non-simple requests):
   OPTIONS /orders/42
     Origin: https://app.example.com
     Access-Control-Request-Method: POST
         |
         v
   gateway checks its CORS config for this origin/method/path
         |
   ALLOWED -> 200 with Access-Control-Allow-* headers -> browser proceeds with the real request
   DENIED  -> browser blocks the real request from ever being sent
```

CORS is enforced by the *browser*, based on headers the server returns — the gateway's job is to return the right headers for origins it actually trusts.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A browser sends a preflight OPTIONS request before the real POST request, and only proceeds with the real request if the gateway's CORS response headers explicitly allow the calling origin">
  <rect x="20" y="20" width="150" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">browser (app.example.com)</text>

  <rect x="470" y="20" width="150" height="40" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="45" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Gateway</text>

  <line x1="170" y1="40" x2="468" y2="40" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a51)"/>
  <text x="320" y="30" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">1. OPTIONS preflight (Origin header)</text>

  <line x1="468" y1="65" x2="170" y2="65" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a51)"/>
  <text x="320" y="80" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">2. Access-Control-Allow-Origin: app.example.com</text>

  <line x1="170" y1="100" x2="468" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a51)"/>
  <text x="320" y="115" fill="#6db33f" font-size="6.5" text-anchor="middle" font-family="sans-serif">3. real POST request (allowed to proceed)</text>

  <rect x="200" y="140" width="240" height="40" rx="8" fill="#e6494930" stroke="#e64949" stroke-width="1.3"/>
  <text x="320" y="164" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">origin not in allowedOrigins -&gt; browser blocks the real request entirely</text>

  <defs><marker id="a51" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The browser gates the real request on the preflight response; a denied preflight means the real request is never even sent.

## 5. Runnable example

The scenario: enforce CORS for `orders-service` traffic through the gateway. Start with a naive allow-everything policy, then add real per-origin checking, then add credentialed-request handling with its stricter same-origin-list requirement.

### Level 1 — Basic

Naive allow-everything — the insecure baseline this feature must move past.

```java
import java.util.*;

public class CorsConfigLevel1 {
    static Map<String, String> preflightResponse(String requestOrigin) {
        return Map.of("Access-Control-Allow-Origin", "*"); // allows literally any origin -- dangerous for anything sensitive
    }

    public static void main(String[] args) {
        System.out.println(preflightResponse("https://app.example.com"));
        System.out.println(preflightResponse("https://totally-untrusted-site.evil"));
    }
}
```

How to run: `java CorsConfigLevel1.java`

`Access-Control-Allow-Origin: *` grants every origin equal access, including ones that were never meant to call this API at all — fine for a genuinely public, unauthenticated API, but wrong the moment cookies, tokens, or any sensitive data are involved.

### Level 2 — Intermediate

Check the requesting origin against a real configured allowlist, modeling `allowedOrigins` from the gateway's actual configuration.

```java
import java.util.*;

public class CorsConfigLevel2 {
    static Set<String> allowedOrigins = Set.of("https://app.example.com", "https://admin.example.com");
    static Set<String> allowedMethods = Set.of("GET", "POST", "PUT", "DELETE");

    static Optional<Map<String, String>> preflightResponse(String requestOrigin, String requestedMethod) {
        if (!allowedOrigins.contains(requestOrigin)) return Optional.empty(); // no matching Access-Control headers at all
        if (!allowedMethods.contains(requestedMethod)) return Optional.empty();
        return Optional.of(Map.of(
                "Access-Control-Allow-Origin", requestOrigin, // echo back the SPECIFIC origin, not a wildcard
                "Access-Control-Allow-Methods", String.join(",", allowedMethods)
        ));
    }

    public static void main(String[] args) {
        System.out.println("app.example.com POST -> " + preflightResponse("https://app.example.com", "POST"));
        System.out.println("evil.example POST -> " + preflightResponse("https://evil.example", "POST"));
    }
}
```

How to run: `java CorsConfigLevel2.java`

`preflightResponse` now checks the real origin against `allowedOrigins` and returns `Optional.empty()` (modeling no CORS headers at all in the response) for anything not on the list — a browser receiving a response with no `Access-Control-Allow-Origin` header refuses to let the calling JavaScript read the response or send the real follow-up request, effectively blocking the untrusted origin.

### Level 3 — Advanced

Add credentialed-request handling: when `allowCredentials` is required, the origin must be echoed back exactly (never a wildcard), and the response must include `Access-Control-Allow-Credentials: true`.

```java
import java.util.*;

public class CorsConfigLevel3 {
    record CorsPolicy(Set<String> allowedOrigins, Set<String> allowedMethods, boolean allowCredentials) {}

    static CorsPolicy publicApiPolicy = new CorsPolicy(Set.of("*"), Set.of("GET"), false);
    static CorsPolicy authenticatedApiPolicy = new CorsPolicy(
            Set.of("https://app.example.com", "https://admin.example.com"),
            Set.of("GET", "POST", "PUT", "DELETE"),
            true // this API accepts cookies/auth headers cross-origin -- wildcard origin is NOT allowed here
    );

    static Optional<Map<String, String>> preflightResponse(CorsPolicy policy, String requestOrigin, String method) {
        boolean originAllowed = policy.allowedOrigins().contains("*") || policy.allowedOrigins().contains(requestOrigin);
        if (!originAllowed || !policy.allowedMethods().contains(method)) return Optional.empty();

        if (policy.allowCredentials() && policy.allowedOrigins().contains("*")) {
            // this combination is invalid per the CORS spec -- browsers reject wildcard + credentials outright
            throw new IllegalStateException("cannot combine allowCredentials=true with a wildcard origin");
        }

        Map<String, String> headers = new LinkedHashMap<>();
        // with credentials, MUST echo the specific origin -- never "*", even if "*" is technically in the allowlist
        headers.put("Access-Control-Allow-Origin", policy.allowCredentials() ? requestOrigin : "*");
        headers.put("Access-Control-Allow-Methods", String.join(",", policy.allowedMethods()));
        if (policy.allowCredentials()) headers.put("Access-Control-Allow-Credentials", "true");
        return Optional.of(headers);
    }

    public static void main(String[] args) {
        System.out.println("public API, any origin, GET -> "
                + preflightResponse(publicApiPolicy, "https://random-site.com", "GET"));

        System.out.println("authenticated API, trusted origin, POST -> "
                + preflightResponse(authenticatedApiPolicy, "https://app.example.com", "POST"));

        System.out.println("authenticated API, untrusted origin, POST -> "
                + preflightResponse(authenticatedApiPolicy, "https://untrusted.example", "POST"));
    }
}
```

How to run: `java CorsConfigLevel3.java`

For `authenticatedApiPolicy`, `preflightResponse` echoes back the *exact* requesting origin (`https://app.example.com`) rather than a wildcard, and adds `Access-Control-Allow-Credentials: true` — this is the specific, spec-mandated behavior needed for a browser to actually send cookies or `Authorization` headers along with a cross-origin request; a wildcard origin combined with credentials is rejected by browsers regardless of server intent, which is why the code explicitly guards against configuring that combination at all.

## 6. Walkthrough

Trace the three calls in Level 3.

1. `preflightResponse(publicApiPolicy, "https://random-site.com", "GET")` runs first — `publicApiPolicy.allowedOrigins()` contains `"*"`, so `originAllowed` is `true` regardless of the actual requesting origin; `GET` is in `allowedMethods`. Since `allowCredentials` is `false`, the credentials/wildcard conflict check is skipped, and the response echoes `Access-Control-Allow-Origin: *` — appropriate for a genuinely public, unauthenticated API where any site is welcome to read the response.
2. `preflightResponse(authenticatedApiPolicy, "https://app.example.com", "POST")` runs next — `authenticatedApiPolicy.allowedOrigins()` explicitly contains this exact origin, and `POST` is an allowed method. Because `allowCredentials` is `true`, the response echoes back the *specific* origin (`https://app.example.com`), not a wildcard, and adds `Access-Control-Allow-Credentials: true` — a browser receiving this response will now allow the app's JavaScript to send its follow-up `POST` request with cookies/auth headers included.
3. `preflightResponse(authenticatedApiPolicy, "https://untrusted.example", "POST")` runs last — `https://untrusted.example` is not in `authenticatedApiPolicy.allowedOrigins()`, so `originAllowed` is `false`, and the method returns `Optional.empty()` immediately, before even reaching the credentials logic. A browser seeing no CORS headers at all in this response blocks the calling JavaScript from proceeding with the real request entirely.

```
publicApiPolicy       + any origin        + GET  -> Allow-Origin: *
authenticatedApiPolicy + app.example.com  + POST -> Allow-Origin: app.example.com (echoed exactly) + Allow-Credentials: true
authenticatedApiPolicy + untrusted.example + POST -> no headers -> browser blocks the request
```

## 7. Gotchas & takeaways

> **Gotcha:** CORS is enforced entirely by the browser, based on server-supplied headers — it is not a server-side access control mechanism. A non-browser client (`curl`, a server-to-server call, a mobile app's native HTTP client) completely ignores CORS headers and can call the API regardless of `allowedOrigins`. CORS protects browser users from a malicious website silently calling an API on their behalf; it does nothing to stop a direct, deliberate API call from any other kind of client — real authorization still needs to happen server-side.

- Configuring CORS once at the gateway means individual backend services never need their own CORS handling, and policy stays consistent across the whole system.
- `allowCredentials: true` requires an exact origin list — never a wildcard — both because the CORS spec mandates it and because browsers actively reject the wildcard-plus-credentials combination for security.
- A denied preflight means the browser never sends the real request at all — from the frontend developer's perspective this often shows up as a confusing network-level CORS error with no server log entry, since the real request never reached the server to be logged.
- Different routes or path prefixes can have different CORS policies (a public marketing API more permissive than an authenticated admin API) — `globalcors` supports per-path configuration exactly for this kind of split.
