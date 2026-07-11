---
card: spring-security
gi: 19
slug: httpsecurity-dsl
title: "HttpSecurity DSL"
---

## 1. What it is

`HttpSecurity` is the single builder object passed into every `SecurityFilterChain` bean method, exposing one configuration method per security concern — `authorizeHttpRequests` (access rules), `formLogin`/`httpBasic`/`oauth2Login` (authentication mechanisms), `csrf`/`cors` (cross-request protections), `sessionManagement` (statefulness policy), `exceptionHandling` (entry point and access-denied handler), and `headers` (security response headers) among others — each independently configurable, and each ultimately contributing one or more servlet filters to the final chain produced by `http.build()`.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .formLogin(Customizer.withDefaults())
        .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED))
        .csrf(Customizer.withDefaults())
        .headers(headers -> headers.frameOptions(frame -> frame.sameOrigin()));
    return http.build();
}
```

## 2. Why & when

A web application's full security posture spans many independent, largely orthogonal concerns — who can access what, how identity is established, whether state persists between requests, what happens on rejection, what protective headers are sent — and bundling all of that into one monolithic configuration object would make each concern hard to reason about in isolation. `HttpSecurity` is deliberately structured as one builder with many independently configurable facets, so that a change to (for instance) session management policy is visibly and mechanically separate from a change to authorization rules, even though both eventually assemble into the same single filter chain.

Reach for a specific `HttpSecurity` method when:

- `authorizeHttpRequests` for *any* access-control rule — this is almost always present in a custom chain, since it's how "who can reach this path" is expressed.
- `sessionManagement(session -> session.sessionCreationPolicy(...))` when building a stateless API (`STATELESS`) as opposed to a traditional session-backed application (`IF_REQUIRED`, the default) — this directly determines which `SecurityContextRepository` (the earlier card) is used.
- `exceptionHandling` when the default `401`/`403` response shape needs customizing (registering a custom `AuthenticationEntryPoint` or `AccessDeniedHandler`, both covered earlier in this section).
- `csrf(csrf -> csrf.disable())` specifically and only for genuinely stateless, non-browser-form-based APIs — disabling CSRF for a session-cookie-authenticated browser app reintroduces a real vulnerability.

## 3. Core concept

```
 HttpSecurity http = ...;

 http
   .authorizeHttpRequests(...)   -- WHO can access WHAT       -> contributes AuthorizationFilter
   .formLogin(...)               -- HOW identity is established -> contributes UsernamePasswordAuthenticationFilter
   .httpBasic(...)               -- an ALTERNATIVE auth mechanism -> contributes BasicAuthenticationFilter
   .sessionManagement(...)       -- statefulness policy          -> affects SecurityContextRepository choice
   .csrf(...)                    -- cross-site request forgery   -> contributes (or omits) CsrfFilter
   .cors(...)                    -- cross-origin resource sharing -> contributes CorsFilter
   .exceptionHandling(...)       -- 401/403 response shape        -> configures ExceptionTranslationFilter's handlers
   .headers(...)                 -- security response headers     -> contributes HeaderWriterFilter
   .build();                      -- ASSEMBLES every configured concern into ONE SecurityFilterChain
```

Each method configures one independent concern; `build()` is the single point where all of them are assembled together.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HttpSecurity exposes independent configuration methods for authorization form login session management csrf and exception handling each contributing a distinct filter or handler to the single SecurityFilterChain produced by build">
  <rect x="15" y="15" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="39" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">authorizeHttpRequests</text>

  <rect x="15" y="65" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="89" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">formLogin / httpBasic</text>

  <rect x="15" y="115" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="139" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">sessionManagement</text>

  <rect x="15" y="165" width="150" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="90" y="189" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">csrf / cors / headers</text>

  <rect x="420" y="90" width="200" height="60" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="520" y="115" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">http.build()</text>
  <text x="520" y="130" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">one assembled</text>
  <text x="520" y="143" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">SecurityFilterChain</text>

  <defs><marker id="a19" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="35" x2="420" y2="105" stroke="#8b949e" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="165" y1="85" x2="420" y2="112" stroke="#8b949e" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="165" y1="135" x2="420" y2="128" stroke="#8b949e" stroke-width="1" marker-end="url(#a19)"/>
  <line x1="165" y1="185" x2="420" y2="135" stroke="#8b949e" stroke-width="1" marker-end="url(#a19)"/>
</svg>

Four (of many) independent configuration methods, all funneling into the one chain `build()` produces.

## 5. Runnable example

The scenario: model `HttpSecurity` as a builder accumulating independent configuration state across several method calls, then use that accumulated state to answer realistic requests. Start with two concerns (authorization and session policy), then add exception handling with a custom entry point, then add a stateless-API-flavored configuration (no session, no CSRF, header-based auth only) as a genuinely different, production-flavored profile from the first two levels.

### Level 1 — Basic

Two independent concerns — authorization rules and session policy — configured on the same builder.

```java
import java.util.*;

public class HttpSecurityDslLevel1 {
    enum SessionCreationPolicy { ALWAYS, IF_REQUIRED, STATELESS }
    record Request(String path, String principal) {}

    static class HttpSecurity {
        List<String> authenticatedPaths = new ArrayList<>();
        SessionCreationPolicy sessionPolicy = SessionCreationPolicy.IF_REQUIRED; // Spring Security's real default

        HttpSecurity authorizeHttpRequests(String requireAuthPathPrefix) {
            authenticatedPaths.add(requireAuthPathPrefix);
            return this;
        }

        HttpSecurity sessionManagement(SessionCreationPolicy policy) {
            this.sessionPolicy = policy;
            return this;
        }
    }

    public static void main(String[] args) {
        HttpSecurity http = new HttpSecurity()
                .authorizeHttpRequests("/account")
                .sessionManagement(SessionCreationPolicy.IF_REQUIRED);

        System.out.println("protected paths: " + http.authenticatedPaths);
        System.out.println("session policy: " + http.sessionPolicy);
    }
}
```

How to run: `java HttpSecurityDslLevel1.java`

Both `authorizeHttpRequests` and `sessionManagement` mutate independent fields on the same `HttpSecurity` instance and both return `this`, letting the two calls chain fluently while affecting entirely separate concerns.

### Level 2 — Intermediate

Add `exceptionHandling` with a custom entry point, and use the accumulated configuration to actually answer a request end to end.

```java
import java.util.*;
import java.util.function.Function;

public class HttpSecurityDslLevel2 {
    record Request(String path, String principal) {}
    interface AuthenticationEntryPoint { String commence(Request request); }

    static class HttpSecurity {
        List<String> authenticatedPaths = new ArrayList<>();
        AuthenticationEntryPoint entryPoint = req -> "302 Found -> Location: /login"; // Spring's default for form login

        HttpSecurity authorizeHttpRequests(String requireAuthPathPrefix) {
            authenticatedPaths.add(requireAuthPathPrefix);
            return this;
        }

        HttpSecurity exceptionHandling(AuthenticationEntryPoint customEntryPoint) {
            this.entryPoint = customEntryPoint;
            return this;
        }

        String handle(Request request) {
            boolean requiresAuth = authenticatedPaths.stream().anyMatch(request.path()::startsWith);
            if (requiresAuth && request.principal() == null) return entryPoint.commence(request);
            return "200 OK";
        }
    }

    public static void main(String[] args) {
        HttpSecurity http = new HttpSecurity()
                .authorizeHttpRequests("/api")
                .exceptionHandling(req -> "401 Unauthorized, body: {\"path\":\"" + req.path() + "\"}");

        System.out.println(http.handle(new Request("/api/orders", null)));
        System.out.println(http.handle(new Request("/api/orders", "alice")));
    }
}
```

How to run: `java HttpSecurityDslLevel2.java`

`exceptionHandling` overrides the default redirect-based `entryPoint` with a JSON-producing one; `handle` then uses both `authenticatedPaths` and `entryPoint` together to decide the response — an unauthenticated request to a protected path now gets the *custom* JSON response, not the default redirect, showing how one concern (`exceptionHandling`) changes the observable behavior configured by another (`authorizeHttpRequests`).

### Level 3 — Advanced

A stateless-API profile: `sessionManagement(STATELESS)`, `csrf` disabled, and a header-based authentication check replacing form login entirely — a genuinely different, production-flavored configuration from the first two levels' session-based assumptions.

```java
import java.util.*;

public class HttpSecurityDslLevel3 {
    enum SessionCreationPolicy { ALWAYS, IF_REQUIRED, STATELESS }
    record Request(String path, Map<String, String> headers) {}

    static class HttpSecurity {
        List<String> authenticatedPaths = new ArrayList<>();
        SessionCreationPolicy sessionPolicy = SessionCreationPolicy.IF_REQUIRED;
        boolean csrfEnabled = true;
        Map<String, String> validApiKeys = Map.of("secret-key-123", "service-account");

        HttpSecurity authorizeHttpRequests(String requireAuthPathPrefix) { authenticatedPaths.add(requireAuthPathPrefix); return this; }
        HttpSecurity sessionManagement(SessionCreationPolicy policy) { this.sessionPolicy = policy; return this; }
        HttpSecurity csrfDisable() { this.csrfEnabled = false; return this; }

        String handle(Request request) {
            boolean requiresAuth = authenticatedPaths.stream().anyMatch(request.path()::startsWith);
            if (!requiresAuth) return "200 OK (public)";

            // STATELESS: no session lookup at all -- every request must independently supply its own credential
            String apiKey = request.headers().get("X-API-Key");
            String principal = validApiKeys.get(apiKey);
            if (principal == null) return "401 Unauthorized (no valid X-API-Key, and no session to fall back on -- STATELESS)";
            return "200 OK, authenticated as " + principal + " (sessionPolicy=" + sessionPolicy + ", csrfEnabled=" + csrfEnabled + ")";
        }
    }

    public static void main(String[] args) {
        HttpSecurity http = new HttpSecurity()
                .authorizeHttpRequests("/api")
                .sessionManagement(SessionCreationPolicy.STATELESS)
                .csrfDisable();

        System.out.println(http.handle(new Request("/api/orders", Map.of())));
        System.out.println(http.handle(new Request("/api/orders", Map.of("X-API-Key", "secret-key-123"))));
        System.out.println(http.handle(new Request("/public/info", Map.of())));
    }
}
```

How to run: `java HttpSecurityDslLevel3.java`

With `sessionPolicy = STATELESS`, `handle` never consults any session-backed state at all — a request with no `X-API-Key` header is rejected outright, and even a request with a valid key must present it fresh on *every* call, since nothing is persisted between requests, matching the earlier `SecurityContextRepository` card's stateless profile and correctly pairing it with `csrfDisable()`, since CSRF protection is meaningless without session-based cookie authentication to protect in the first place.

## 6. Walkthrough

Trace Level 3's three `handle` calls in order.

1. `http.handle(new Request("/api/orders", Map.of()))` runs first — `authenticatedPaths.stream().anyMatch(...)` checks `"/api/orders".startsWith("/api")`, which is `true`, so `requiresAuth` is `true`; `request.headers().get("X-API-Key")` returns `null` since the map is empty, so `validApiKeys.get(null)` also returns `null`, and the method returns the `401` message.
2. `http.handle(new Request("/api/orders", Map.of("X-API-Key", "secret-key-123")))` runs next — the same path check makes `requiresAuth` true; this time `request.headers().get("X-API-Key")` returns `"secret-key-123"`, and `validApiKeys.get("secret-key-123")` resolves to `"service-account"`, so `principal` is non-null and the method returns the `200 OK` success message, embedding the current `sessionPolicy` and `csrfEnabled` values for visibility.
3. `http.handle(new Request("/public/info", Map.of()))` runs last — `"/public/info".startsWith("/api")` is `false`, so `requiresAuth` is `false`, and the method short-circuits immediately to `"200 OK (public)"`, never even checking for an API key.
4. In a real stateless Spring Security application, step 2's success path is exactly where a custom `OncePerRequestFilter` (built on the `AbstractAuthenticationProcessingFilter` pattern from two cards back, or a simpler always-on filter) would populate `SecurityContextHolder` for the duration of this one request only, since `RequestAttributeSecurityContextRepository` never persists it anywhere for the *next* request to find.

```
GET /api/orders   (no X-API-Key)        -> requiresAuth=true, no key found -> 401
GET /api/orders   (X-API-Key valid)     -> requiresAuth=true, key resolves -> 200 (fresh check, no session used)
GET /public/info  (no X-API-Key)        -> requiresAuth=false              -> 200 (public, no check needed)
```

## 7. Gotchas & takeaways

> **Gotcha:** disabling CSRF (`csrf(csrf -> csrf.disable())`) is only safe for genuinely stateless, non-cookie-authenticated APIs — disabling it on a traditional session-cookie-based browser application removes real protection against cross-site request forgery, since the vulnerability CSRF protection defends against specifically exploits the browser's automatic cookie-attaching behavior on cross-site requests, which stateless header/token-based APIs are not subject to in the same way.

- `HttpSecurity` is a single builder exposing many independent configuration methods, each affecting a distinct concern, all funneled into one `SecurityFilterChain` by the final `build()` call.
- `sessionManagement`'s policy (`IF_REQUIRED` by default, `STATELESS` for APIs) determines whether a `SecurityContextRepository` persists anything between requests at all — pairing `STATELESS` with an appropriate authentication mechanism (a token or API key checked on every request) is essential, since there's no session to fall back on.
- `exceptionHandling` is where a custom `AuthenticationEntryPoint`/`AccessDeniedHandler` (from earlier cards in this section) gets registered onto the chain being built.
- CSRF protection and session-based (cookie) authentication are conceptually paired — disabling one without considering the other is a common, security-relevant misconfiguration.
