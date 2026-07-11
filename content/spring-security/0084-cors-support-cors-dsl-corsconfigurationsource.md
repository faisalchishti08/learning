---
card: spring-security
gi: 84
slug: cors-support-cors-dsl-corsconfigurationsource
title: "CORS support (cors DSL & CorsConfigurationSource)"
---

## 1. What it is

The **Same-Origin Policy (SOP)** is the browser's default rule that JavaScript running on one origin (scheme + host + port) cannot read responses from a different origin — `https://app.example.com` cannot, by default, read the body of a response from `https://api.example.com`, even if the request itself succeeds at the network level. **CORS (Cross-Origin Resource Sharing)** is the standardized, opt-in mechanism by which a server tells browsers "it's fine for *this specific origin* to read *this specific response*," via headers like `Access-Control-Allow-Origin`. Spring Security's `.cors()` DSL wires a `CorsConfigurationSource` bean — allowed origins, methods, headers, and whether credentials are permitted — into the security filter chain, so cross-origin requests are evaluated consistently with the rest of the application's security rules, typically working alongside Spring MVC's own `@CrossOrigin` annotation or `WebMvcConfigurer`-based CORS configuration.

## 2. Why & when

Before CORS existed, cross-origin `XMLHttpRequest`s were simply blocked outright by SOP with no opt-in mechanism at all — safe, but it also meant a JavaScript app hosted on one domain genuinely could not call an API hosted on another, even when both were owned by the same company and the call was entirely legitimate. This became common once single-page apps and separately deployed APIs became standard practice. CORS relaxes SOP in a controlled, server-declared way instead of abandoning it.

For requests beyond a simple `GET` or a plain form-encoded `POST` — anything using `PUT`/`DELETE`, a `Content-Type` of `application/json`, or custom headers such as an `Authorization` bearer token — the browser first sends a **preflight** `OPTIONS` request carrying `Access-Control-Request-Method` and `Access-Control-Request-Headers`, asking the server's permission *before* sending the real request at all. Only if the preflight response grants that method and those headers does the browser proceed to send the actual request.

Reach for `.cors()` and a `CorsConfigurationSource` when:

- Your frontend and API are served from different origins — different subdomains (`app.` vs `api.`), different ports during local development, or entirely different domains.
- You need fine control over exactly which origins, methods, and headers are permitted, rather than a blanket allow-everything policy that would defeat the purpose of having an origin check at all.
- Cookies or other credentials need to travel with the cross-origin request — this requires `allowCredentials(true)` on the server and `credentials: "include"` on the client, and specifically forbids using a wildcard origin, covered below.

## 3. Core concept

```
 Same-Origin Policy (default): scripts on origin A cannot read responses from origin B.

 CorsConfigurationSource (the policy the server declares):
   allowedOrigins:   which origins may read responses           e.g. https://app.example.com
   allowedMethods:   which HTTP methods are permitted            e.g. GET, POST, PUT
   allowedHeaders:   which request headers are permitted         e.g. Content-Type, Authorization
   allowCredentials: whether cookies/credentials may be included -- NEVER combine with "*" origin

 Preflight (only for "non-simple" requests -- custom headers, JSON bodies, PUT/DELETE/etc.):
   1. Browser sends OPTIONS with Access-Control-Request-Method / -Headers
   2. Server answers with Access-Control-Allow-Origin / -Methods / -Headers
   3. ONLY if that's granted does the browser send the actual request
```

The security filter chain's `.cors()` DSL is where this policy plugs into request processing — it runs early enough to answer preflight `OPTIONS` requests itself, before they ever reach a controller.

## 4. Diagram

<svg viewBox="0 0 700 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A cross origin browser first sends an OPTIONS preflight request carrying the Origin and Access-Control-Request-Method headers the server's CorsConfigurationSource checks whether that origin method and headers are allowed and answers with Access-Control-Allow-Origin Allow-Methods and Allow-Headers only after that succeeds does the browser send the actual PUT request which receives its own Access-Control-Allow-Origin header in the real response">
  <rect x="20" y="20" width="150" height="260" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="95" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">app.example.com</text>

  <rect x="530" y="20" width="150" height="260" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="605" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">CorsConfigurationSource</text>

  <line x1="170" y1="95" x2="530" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#c1)"/>
  <text x="350" y="83" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">1. OPTIONS preflight</text>
  <text x="350" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Origin, Access-Control-Request-Method</text>

  <line x1="530" y1="145" x2="170" y2="145" stroke="#3fb950" stroke-width="2" marker-end="url(#c2)"/>
  <text x="350" y="133" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">2. 200, preflight allowed</text>
  <text x="350" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Allow-Origin, Allow-Methods, Allow-Headers</text>

  <line x1="170" y1="200" x2="530" y2="200" stroke="#79c0ff" stroke-width="2" marker-end="url(#c1)"/>
  <text x="350" y="188" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">3. actual PUT /account</text>

  <line x1="530" y1="250" x2="170" y2="250" stroke="#3fb950" stroke-width="2" marker-end="url(#c2)"/>
  <text x="350" y="238" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">4. 200 OK + body</text>
  <text x="350" y="265" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Access-Control-Allow-Origin echoed</text>

  <defs>
    <marker id="c1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The preflight is a separate round trip that must succeed before the browser will even attempt the real request — the actual request then repeats the origin check independently and gets its own CORS headers.

## 5. Runnable example

The scenario: a JavaScript app on `https://app.example.com` calls a JSON API on `https://api.example.com`. Level 1 shows the browser blocking the response outright under the plain Same-Origin Policy, with no CORS support at all. Level 2 adds a `CorsConfigurationSource` and a preflight handler, so a non-simple `PUT` request is first approved via `OPTIONS` and then allowed through. Level 3 adds credentialed requests across multiple allowed origins, and enforces the rule that a wildcard origin can never be combined with `allowCredentials(true)`.

### Level 1 — Basic

```java
import java.util.*;

public class CorsLevel1 {

    record HttpRequest(String method, String url, String origin, Map<String, String> headers) {}
    record HttpResponse(int status, Map<String, String> headers, String body) {}

    // A minimal server with NO CORS support at all yet -- it just answers the request.
    static HttpResponse handle(HttpRequest request) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", "application/json");
        return new HttpResponse(200, headers, "{\"balance\": 42}");
    }

    // Simulates the BROWSER's enforcement of the Same-Origin Policy: even though the
    // server answered with a perfectly good response, the browser refuses to hand the
    // body to the calling JavaScript unless the response explicitly allows the caller's origin.
    static String browserDeliverToScript(HttpRequest request, HttpResponse response) {
        String allowOrigin = response.headers().get("Access-Control-Allow-Origin");
        boolean sameOrigin = request.origin().equals("https://api.example.com");

        if (sameOrigin) return "Delivered to script (same-origin, CORS not involved): " + response.body();
        if (allowOrigin != null && (allowOrigin.equals("*") || allowOrigin.equals(request.origin()))) {
            return "Delivered to script (cross-origin, allowed): " + response.body();
        }
        return "BLOCKED by browser: no Access-Control-Allow-Origin permitting " + request.origin();
    }

    public static void main(String[] args) {
        HttpRequest fromDashboard = new HttpRequest("GET", "https://api.example.com/account",
                "https://app.example.com", Map.of());

        HttpResponse response = handle(fromDashboard);
        System.out.println(browserDeliverToScript(fromDashboard, response));
    }
}
```

**How to run:** save as `CorsLevel1.java`, run `java CorsLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
BLOCKED by browser: no Access-Control-Allow-Origin permitting https://app.example.com
```

The server responded successfully, but with no CORS support the response carries no `Access-Control-Allow-Origin` header at all, so the browser refuses to hand the body to the calling script — exactly what SOP does by default for any cross-origin request.

### Level 2 — Intermediate

```java
import java.util.*;

public class CorsLevel2 {

    record HttpRequest(String method, String url, String origin, Map<String, String> headers) {}
    record HttpResponse(int status, Map<String, String> headers, String body) {}

    // Mirrors Spring's CorsConfigurationSource: a per-path policy describing exactly which
    // origins, methods, and headers are allowed for cross-origin requests.
    static class CorsConfigurationSource {
        final List<String> allowedOrigins = new ArrayList<>();
        final List<String> allowedMethods = new ArrayList<>();
        final List<String> allowedHeaders = new ArrayList<>();

        boolean originAllowed(String origin) { return allowedOrigins.contains(origin); }
        boolean methodAllowed(String method) { return allowedMethods.contains(method); }
        boolean headersAllowed(List<String> requested) { return allowedHeaders.containsAll(requested); }
    }

    // The security filter chain's .cors() DSL: intercepts BEFORE the request reaches a
    // controller and answers preflight OPTIONS requests itself.
    static HttpResponse handlePreflight(CorsConfigurationSource cors, HttpRequest preflight) {
        String origin = preflight.origin();
        String requestedMethod = preflight.headers().get("Access-Control-Request-Method");
        List<String> requestedHeaders = Arrays.asList(preflight.headers()
                .getOrDefault("Access-Control-Request-Headers", "").split(",\\s*"));

        Map<String, String> headers = new LinkedHashMap<>();
        if (cors.originAllowed(origin) && cors.methodAllowed(requestedMethod) && cors.headersAllowed(requestedHeaders)) {
            headers.put("Access-Control-Allow-Origin", origin);
            headers.put("Access-Control-Allow-Methods", String.join(", ", cors.allowedMethods));
            headers.put("Access-Control-Allow-Headers", String.join(", ", cors.allowedHeaders));
            headers.put("Access-Control-Max-Age", "3600");
            return new HttpResponse(200, headers, "");
        }
        return new HttpResponse(403, headers, "");
    }

    static HttpResponse handleActualRequest(CorsConfigurationSource cors, HttpRequest request) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", "application/json");
        if (cors.originAllowed(request.origin())) {
            headers.put("Access-Control-Allow-Origin", request.origin());
        }
        return new HttpResponse(200, headers, "{\"updated\": true}");
    }

    public static void main(String[] args) {
        CorsConfigurationSource cors = new CorsConfigurationSource();
        cors.allowedOrigins.add("https://app.example.com");
        cors.allowedMethods.addAll(List.of("GET", "PUT", "POST"));
        cors.allowedHeaders.addAll(List.of("Content-Type", "X-Requested-With"));

        // PUT with a JSON body is a "non-simple" request -- the browser sends a preflight FIRST
        HttpRequest preflight = new HttpRequest("OPTIONS", "https://api.example.com/account",
                "https://app.example.com",
                Map.of("Access-Control-Request-Method", "PUT",
                        "Access-Control-Request-Headers", "Content-Type"));

        HttpResponse preflightResponse = handlePreflight(cors, preflight);
        System.out.println("Preflight status: " + preflightResponse.status());
        preflightResponse.headers().forEach((k, v) -> System.out.println("  " + k + ": " + v));

        HttpRequest actual = new HttpRequest("PUT", "https://api.example.com/account",
                "https://app.example.com", Map.of("Content-Type", "application/json"));
        HttpResponse actualResponse = handleActualRequest(cors, actual);
        System.out.println("Actual request status: " + actualResponse.status()
                + ", Allow-Origin: " + actualResponse.headers().get("Access-Control-Allow-Origin"));
    }
}
```

**How to run:** save as `CorsLevel2.java`, run `java CorsLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
Preflight status: 200
  Access-Control-Allow-Origin: https://app.example.com
  Access-Control-Allow-Methods: GET, PUT, POST
  Access-Control-Allow-Headers: Content-Type, X-Requested-With
  Access-Control-Max-Age: 3600
Actual request status: 200, Allow-Origin: https://app.example.com
```

`handlePreflight` checks the requested origin, method, and headers against the `CorsConfigurationSource` before the browser ever sends the real `PUT` — only once that passes does `handleActualRequest` get a chance to run at all, mirroring how `.cors()` intercepts `OPTIONS` requests ahead of the rest of the filter chain.

### Level 3 — Advanced

```java
import java.util.*;

public class CorsLevel3 {

    record HttpRequest(String method, String url, String origin, Map<String, String> headers, boolean hasCredentialedCookie) {}
    record HttpResponse(int status, Map<String, String> headers, String body) {}

    static class CorsConfigurationSource {
        final Set<String> allowedOrigins = new LinkedHashSet<>();
        final List<String> allowedMethods = new ArrayList<>();
        boolean allowCredentials = false;

        // enforces the spec rule: a wildcard origin can NEVER be combined with credentials
        void validate() {
            if (allowCredentials && allowedOrigins.contains("*")) {
                throw new IllegalStateException(
                        "Invalid CORS config: allowCredentials(true) cannot be combined with a wildcard origin -- "
                        + "this would let ANY site read authenticated responses using the victim's cookies");
            }
        }

        boolean originAllowed(String origin) {
            return allowedOrigins.contains("*") || allowedOrigins.contains(origin);
        }
    }

    static HttpResponse handleActualRequest(CorsConfigurationSource cors, HttpRequest request) {
        cors.validate();
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", "application/json");

        if (!cors.originAllowed(request.origin())) {
            return new HttpResponse(403, headers, "");
        }

        // credentialed responses must echo the EXACT origin, never "*" -- browsers reject
        // Access-Control-Allow-Origin: * outright when the request carried credentials
        if (request.hasCredentialedCookie() && cors.allowCredentials) {
            headers.put("Access-Control-Allow-Origin", request.origin());
            headers.put("Access-Control-Allow-Credentials", "true");
        } else if (!request.hasCredentialedCookie()) {
            headers.put("Access-Control-Allow-Origin", cors.allowedOrigins.contains("*") ? "*" : request.origin());
        } else {
            return new HttpResponse(403, headers, ""); // credentialed request but server doesn't allow credentials
        }
        return new HttpResponse(200, headers, "{\"balance\": 42}");
    }

    public static void main(String[] args) {
        CorsConfigurationSource safeConfig = new CorsConfigurationSource();
        safeConfig.allowedOrigins.addAll(List.of("https://app.example.com", "https://admin.example.com"));
        safeConfig.allowedMethods.addAll(List.of("GET", "POST"));
        safeConfig.allowCredentials = true;

        HttpRequest credentialedRequest = new HttpRequest("GET", "https://api.example.com/account",
                "https://app.example.com", Map.of("Cookie", "SESSION=abc123"), true);

        HttpResponse response = handleActualRequest(safeConfig, credentialedRequest);
        System.out.println("Safe config -> status " + response.status()
                + ", Allow-Origin: " + response.headers().get("Access-Control-Allow-Origin")
                + ", Allow-Credentials: " + response.headers().get("Access-Control-Allow-Credentials"));

        CorsConfigurationSource dangerousConfig = new CorsConfigurationSource();
        dangerousConfig.allowedOrigins.add("*");
        dangerousConfig.allowCredentials = true;

        try {
            handleActualRequest(dangerousConfig, credentialedRequest);
        } catch (IllegalStateException e) {
            System.out.println("Dangerous config rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `CorsLevel3.java`, run `java CorsLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
Safe config -> status 200, Allow-Origin: https://app.example.com, Allow-Credentials: true
Dangerous config rejected: Invalid CORS config: allowCredentials(true) cannot be combined with a wildcard origin -- this would let ANY site read authenticated responses using the victim's cookies
```

`safeConfig` lists explicit origins and never uses `"*"`, so `validate()` passes and the credentialed request gets back its own exact origin plus `Allow-Credentials: true`. `dangerousConfig` combines a wildcard origin with `allowCredentials(true)`, and `validate()` rejects that combination immediately, before any response is even built — catching in configuration exactly the combination browsers would refuse to honor at runtime anyway.

## 6. Walkthrough

Trace the Level 3 example's two calls to `handleActualRequest`, from the raw HTTP request through to the concrete response each configuration produces.

**Request (credentialed cross-origin GET):**
```
GET /account HTTP/1.1
Host: api.example.com
Origin: https://app.example.com
Cookie: SESSION=abc123
```

**Response (safe config):**
```
HTTP/1.1 200 OK
Content-Type: application/json
Access-Control-Allow-Origin: https://app.example.com
Access-Control-Allow-Credentials: true

{"balance": 42}
```

1. `handleActualRequest(safeConfig, credentialedRequest)` first calls `cors.validate()`. Because `safeConfig.allowCredentials` is `true` but `allowedOrigins` contains only the two explicit hostnames, never `"*"`, the condition `allowCredentials && allowedOrigins.contains("*")` is `false`, so `validate()` returns normally without throwing.
2. `cors.originAllowed(request.origin())` checks whether `allowedOrigins` contains `"*"` (it doesn't) or contains `"https://app.example.com"` (it does), so it returns `true` and the request is not rejected with a `403`.
3. `request.hasCredentialedCookie()` is `true` and `cors.allowCredentials` is `true`, so the first branch of the `if`/`else if`/`else` executes: it sets `Access-Control-Allow-Origin` to the request's exact origin string, never `"*"`, and adds `Access-Control-Allow-Credentials: true`.
4. The method returns a `200` with the JSON body — the browser, seeing its own exact origin echoed back alongside `Allow-Credentials: true`, permits the calling script to read the response.
5. Now the dangerous config: `handleActualRequest(dangerousConfig, credentialedRequest)` calls `cors.validate()` again, but this time `dangerousConfig.allowCredentials` is `true` *and* `allowedOrigins.contains("*")` is also `true`, so the condition is `true` and `validate()` immediately throws an `IllegalStateException` before any origin check, header assembly, or response is attempted.
6. The `try`/`catch` in `main` catches that exception and prints its message — modeling that a real `CorsConfigurationSource` should reject this combination at configuration time, rather than silently producing a response that browsers would refuse to honor anyway (browsers independently reject `Access-Control-Allow-Origin: *` on any response answering a credentialed request, so this misconfiguration would fail at runtime regardless — catching it during configuration is strictly better than discovering it via a confusing CORS error in the browser console).

## 7. Gotchas & takeaways

> **Gotcha:** `Access-Control-Allow-Origin: *` combined with `Access-Control-Allow-Credentials: true` is not just bad practice — browsers refuse to honor it outright. If a response sends both, the browser blocks the credentialed request regardless of server intent, because a wildcard origin combined with credentials would let literally any website read another user's authenticated data using their own ambient cookies.

- CORS is enforced by the **browser**, not the server — a non-browser client (`curl`, a server-to-server call) ignores `Access-Control-Allow-Origin` entirely and reads the response regardless; CORS is not an authorization mechanism, it only controls what browser-hosted JavaScript is allowed to read.
- Preflight only happens for "non-simple" requests — a plain `GET` or a form-encoded `POST` with no custom headers skips the preflight round trip entirely and goes straight to the actual request.
- `Access-Control-Allow-Origin` must echo the exact requesting origin, never `"*"`, whenever the request carries credentials — Spring's `CorsConfigurationSource` enforces this at the framework level when `allowCredentials(true)` is set.
- Spring Security's `.cors()` DSL and Spring MVC's `@CrossOrigin`/`WebMvcConfigurer` CORS support should agree with each other — an inconsistency between the two is a frequent source of confusing "works from Postman but not the browser" bugs, since Postman doesn't enforce CORS at all.
- A `CorsConfigurationSource` scoped too broadly, matching every path with a wildcard origin, defeats the purpose of having origin restrictions in the first place — scope it as narrowly as the application's actual cross-origin needs require.
