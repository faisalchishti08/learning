---
card: spring-security
gi: 13
slug: authenticationentrypoint
title: "AuthenticationEntryPoint"
---

## 1. What it is

`AuthenticationEntryPoint` is the single-method interface (`commence(HttpServletRequest, HttpServletResponse, AuthenticationException)`) that decides what response an unauthenticated request receives when it is denied access — for a browser-facing app it typically redirects to a login page (`LoginUrlAuthenticationEntryPoint`), while for an API it typically writes a bare `401 Unauthorized` status with no body (`Http403ForbiddenEntryPoint`-style, or a custom JSON error). It is invoked by `ExceptionTranslationFilter` (the next card) whenever an `AuthenticationException` reaches it, and never runs for requests that are already authenticated but merely lack permission — that case is handled by `AccessDeniedHandler` instead.

```java
public interface AuthenticationEntryPoint {
    void commence(HttpServletRequest request, HttpServletResponse response,
                  AuthenticationException authException) throws IOException, ServletException;
}
```

```java
@Component
class JsonAuthenticationEntryPoint implements AuthenticationEntryPoint {
    public void commence(HttpServletRequest req, HttpServletResponse res, AuthenticationException ex) throws IOException {
        res.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        res.setContentType("application/json");
        res.getWriter().write("{\"error\":\"unauthenticated\",\"message\":\"" + ex.getMessage() + "\"}");
    }
}
```

## 2. Why & when

Different clients expect completely different things when authentication fails: a browser expects a redirect to a login form so a human can type credentials; a JavaScript single-page app or a mobile client expects a machine-readable `401` with a JSON body it can react to (show a login modal, refresh a token); a server-to-server API client expects a plain `401` status and nothing more. `AuthenticationEntryPoint` exists as its own pluggable interface precisely so this "what should the *unauthenticated* rejection look like" decision is entirely separate from the authentication logic itself — the same `AuthenticationProvider` and filter chain can serve both a browser UI and a JSON API by simply wiring in a different entry point per request path.

Reach for a custom `AuthenticationEntryPoint` when:

- Building a REST API where the default redirect-to-login behavior is wrong — clients need a `401` status with a JSON error body they can parse, not an HTML redirect they can't follow.
- Supporting multiple client types (a browser UI and a JSON API) from the same application, where each needs a different entry point registered against a different request matcher (see the multiple-filter-chains card later in this section).
- Adding custom headers or a specific error payload shape (matching an existing API error convention) to the `401` response, beyond what any built-in entry point provides.

## 3. Core concept

```
 unauthenticated request reaches a protected resource
        |
        v
 AuthenticationException thrown (e.g. by AuthorizationFilter, or an auth filter itself)
        |
        v
 ExceptionTranslationFilter catches it
        |
        v
 AuthenticationEntryPoint.commence(request, response, exception)
        |
        +--> LoginUrlAuthenticationEntryPoint    -- redirects browser to /login
        +--> a custom JSON entry point           -- writes 401 + JSON body
        +--> Http403ForbiddenEntryPoint           -- writes bare 403 (legacy REST convention)
```

Exactly one `AuthenticationEntryPoint` is invoked per rejected request — which one is chosen is a matter of configuration, not of the exception itself.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An AuthenticationException caught by ExceptionTranslationFilter is handed to one of two different AuthenticationEntryPoint implementations depending on client type a browser entry point redirects to a login page while a JSON entry point for an API client writes a 401 status with a JSON body">
  <rect x="15" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationException</text>
  <text x="90" y="103" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">caught by filter</text>

  <rect x="220" y="70" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="90" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationEntryPoint</text>
  <text x="310" y="103" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">.commence(...)</text>

  <rect x="460" y="20" width="165" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="542" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">browser client</text>
  <text x="542" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">302 redirect -&gt; /login</text>

  <rect x="460" y="118" width="165" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="542" y="138" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">API client</text>
  <text x="542" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">401 + JSON body</text>

  <defs><marker id="a13" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="93" x2="220" y2="93" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a13)"/>
  <line x1="400" y1="85" x2="460" y2="45" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a13)"/>
  <line x1="400" y1="100" x2="460" y2="140" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a13)"/>
</svg>

One `AuthenticationException`, one `commence` call, but a different response shape depending on which entry point is configured for the request.

## 5. Runnable example

The scenario: model `commence` being invoked with different registered entry points, showing how the exact same exception produces a browser redirect in one configuration and a JSON `401` in another. Start with a single entry point writing a fixed response, then add a second entry point and a router that picks between them by request path, then add a real error payload shape with the original exception's message embedded.

### Level 1 — Basic

A single `AuthenticationEntryPoint`-style handler, invoked when an exception is "caught".

```java
import java.util.*;

public class EntryPointLevel1 {
    interface AuthenticationEntryPoint {
        String commence(String path, String exceptionMessage);
    }

    static class LoginRedirectEntryPoint implements AuthenticationEntryPoint {
        public String commence(String path, String exceptionMessage) {
            return "302 Found -> Location: /login";
        }
    }

    public static void main(String[] args) {
        AuthenticationEntryPoint entryPoint = new LoginRedirectEntryPoint();
        String response = entryPoint.commence("/account", "Full authentication is required");
        System.out.println("response: " + response);
    }
}
```

How to run: `java EntryPointLevel1.java`

`commence` is called with the request path and the exception's message, and this single implementation always produces the same redirect response, regardless of either argument — a reasonable default for a browser-only application.

### Level 2 — Intermediate

Two entry points registered, with a router choosing between them by request path — modeling an app that serves both a browser UI and a JSON API.

```java
import java.util.*;
import java.util.function.BiFunction;

public class EntryPointLevel2 {
    interface AuthenticationEntryPoint {
        String commence(String path, String exceptionMessage);
    }

    static class LoginRedirectEntryPoint implements AuthenticationEntryPoint {
        public String commence(String path, String exceptionMessage) { return "302 Found -> Location: /login"; }
    }

    static class JsonEntryPoint implements AuthenticationEntryPoint {
        public String commence(String path, String exceptionMessage) {
            return "401 Unauthorized, body: {\"error\":\"" + exceptionMessage + "\"}";
        }
    }

    static AuthenticationEntryPoint route(String path) {
        return path.startsWith("/api/") ? new JsonEntryPoint() : new LoginRedirectEntryPoint();
    }

    public static void main(String[] args) {
        for (String path : List.of("/account", "/api/orders")) {
            AuthenticationEntryPoint entryPoint = route(path);
            String response = entryPoint.commence(path, "Full authentication is required");
            System.out.println(path + " -> " + response);
        }
    }
}
```

How to run: `java EntryPointLevel2.java`

`route` inspects the request path and picks `JsonEntryPoint` for anything under `/api/`, falling back to `LoginRedirectEntryPoint` otherwise — the exact same exception now produces two entirely different response shapes depending purely on which path was requested, mirroring `HttpSecurity`'s ability to register a different `AuthenticationEntryPoint` per matched request pattern.

### Level 3 — Advanced

A production-flavored JSON entry point that embeds a request ID and timestamp, plus a fallback entry point chosen when no more specific matcher applies, modeling `DelegatingAuthenticationEntryPoint`'s real behavior.

```java
import java.util.*;
import java.util.function.Predicate;

public class EntryPointLevel3 {
    interface AuthenticationEntryPoint {
        String commence(String path, String exceptionMessage);
    }

    record Registration(Predicate<String> matcher, AuthenticationEntryPoint entryPoint) {}

    static class JsonEntryPoint implements AuthenticationEntryPoint {
        public String commence(String path, String exceptionMessage) {
            String requestId = UUID.randomUUID().toString().substring(0, 8);
            return "401 Unauthorized, body: {\"error\":\"" + exceptionMessage + "\",\"requestId\":\"" + requestId + "\"}";
        }
    }

    static class LoginRedirectEntryPoint implements AuthenticationEntryPoint {
        public String commence(String path, String exceptionMessage) { return "302 Found -> Location: /login"; }
    }

    // models DelegatingAuthenticationEntryPoint: an ORDERED list of (matcher, entryPoint) pairs, plus a default
    static class DelegatingEntryPoint implements AuthenticationEntryPoint {
        private final List<Registration> registrations;
        private final AuthenticationEntryPoint fallback;

        DelegatingEntryPoint(List<Registration> registrations, AuthenticationEntryPoint fallback) {
            this.registrations = registrations;
            this.fallback = fallback;
        }

        public String commence(String path, String exceptionMessage) {
            for (Registration reg : registrations) {
                if (reg.matcher().test(path)) return reg.entryPoint().commence(path, exceptionMessage);
            }
            return fallback.commence(path, exceptionMessage);
        }
    }

    public static void main(String[] args) {
        DelegatingEntryPoint delegating = new DelegatingEntryPoint(
                List.of(new Registration(p -> p.startsWith("/api/"), new JsonEntryPoint())),
                new LoginRedirectEntryPoint()
        );

        for (String path : List.of("/api/orders", "/account", "/api/users/42")) {
            System.out.println(path + " -> " + delegating.commence(path, "Full authentication is required"));
        }
    }
}
```

How to run: `java EntryPointLevel3.java`

`DelegatingEntryPoint` walks its ordered `registrations` list looking for the first matcher that accepts the request path, falling back to `LoginRedirectEntryPoint` when nothing matches — `/api/orders` and `/api/users/42` both match the `/api/` predicate and get a `JsonEntryPoint` response (each carrying its own freshly generated request ID), while `/account` falls through to the redirect, exactly modeling how a real Spring Security app registers `exceptionHandling(ex -> ex.defaultAuthenticationEntryPointFor(jsonEntryPoint, new AntPathRequestMatcher("/api/**")))`.

## 6. Walkthrough

Trace Level 3 end to end for the request `GET /api/orders` with no `Authorization` header.

1. The request reaches `AuthorizationFilter` (from the filter-ordering card), which finds no authenticated principal and throws an `AuthenticationException` — conceptually `new AuthenticationCredentialsNotFoundException("Full authentication is required")`.
2. `ExceptionTranslationFilter` catches this exception (it wraps the rest of the chain in a try/catch) and calls `delegating.commence("/api/orders", "Full authentication is required")`.
3. Inside `commence`, the loop checks `registrations` in order: the single registered pair `(path -> path.startsWith("/api/"), JsonEntryPoint)` matches immediately, since `"/api/orders".startsWith("/api/")` is `true`.
4. `JsonEntryPoint.commence` runs, generates a fresh `requestId` via `UUID.randomUUID()`, and returns the string `"401 Unauthorized, body: {\"error\":\"Full authentication is required\",\"requestId\":\"<8 chars>\"}"`.
5. In a real application this is where the response would actually be written: `response.setStatus(401)` and `response.getWriter().write(jsonBody)` — the client receives a `401` status with a JSON payload it can parse to show an error message and correlate against server logs using the request ID.
6. For `GET /account` with the same missing credentials, step 3's loop finds no matching registration (`"/account".startsWith("/api/")` is `false`), so control falls through to `fallback.commence(...)`, which returns the plain redirect string — the client instead receives a `302` pointing at `/login`.

```
request                 registrations matched?      entry point invoked      response
/api/orders    -------->  YES (/api/** matcher) -->  JsonEntryPoint     -->  401 + JSON body
/account       -------->  NO                     -->  fallback (login)  -->  302 -> /login
```

## 7. Gotchas & takeaways

> **Gotcha:** `AuthenticationEntryPoint` only runs for `AuthenticationException` — a request from an *already-authenticated* user who simply lacks the required role throws `AccessDeniedException` instead, which is routed to a completely different interface, `AccessDeniedHandler`. Registering only an `AuthenticationEntryPoint` and expecting it to also handle "logged in but forbidden" responses is a common source of confusing `403`-vs-`401` bugs.

- `AuthenticationEntryPoint` decides the response shape for *unauthenticated* rejections; `AccessDeniedHandler` decides it for *authenticated-but-unauthorized* rejections — the two are invoked from the same `ExceptionTranslationFilter` but never for the same exception type.
- A single application can register different entry points for different request patterns (an API prefix versus everything else), via `exceptionHandling().defaultAuthenticationEntryPointFor(entryPoint, matcher)`, which is exactly what `DelegatingAuthenticationEntryPoint` implements internally.
- The default entry point when none is configured explicitly depends on what authentication mechanisms are active — form login auto-configures a redirect-based entry point, while HTTP Basic auto-configures a `WWW-Authenticate` header-based one; mixing mechanisms without an explicit entry point per path is a common source of an unexpected login-page redirect on what was meant to be a pure API endpoint.
