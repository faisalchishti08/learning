---
card: microservices
gi: 400
slug: spring-security-core-filters-authentication-authorization
title: "Spring Security core (filters, authentication, authorization)"
---

## 1. What it is

**Spring Security** is the standard framework for implementing authentication and authorization in a Spring Boot service, built around a chain of **servlet filters** that each inspect or act on a request before it reaches your controller code. Rather than hand-rolling the concepts covered throughout this section — [authentication vs authorization](0381-authentication-vs-authorization.md), token validation, scope and role checks — Spring Security gives you a well-tested, declarative way to wire them into a real application: a `SecurityFilterChain` bean that declares *which* requests need authentication and *what* they're authorized to do, backed by pluggable authentication and authorization machinery.

## 2. Why & when

You reach for Spring Security's core building blocks any time a Spring Boot service needs to authenticate requests and enforce authorization rules, which in a microservices system is nearly every service that accepts external or even internal HTTP traffic:

- **It centralizes cross-cutting request handling** — authentication, session management (or its deliberate absence in a stateless API), CSRF protection, CORS, and authorization — in one declarative configuration rather than scattered `if` checks in every controller method.
- **The filter chain runs before your controllers**, so unauthenticated or unauthorized requests are rejected early, consistent with the "fail fast, fail cheap" layering discussed in [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md).
- **It's the foundation the more specialized Spring Security modules build on** — [Spring Security's OAuth2 Resource Server support](0401-spring-security-oauth2-resource-server-jwt-opaque.md) is itself implemented as filters plugged into this same chain, so understanding the core filter model is what makes the OAuth2-specific configuration make sense rather than feel like magic.
- **Method-level security** (`@PreAuthorize`, checked elsewhere in this curriculum) builds on the same `Authentication` object this filter chain establishes, so getting the core model right pays off at every layer above it.

You need this the moment you're building any Spring Boot service that isn't purely internal and fully network-isolated — and even then, per [zero-trust networking](0380-zero-trust-networking.md), internal services usually want it too.

## 3. Core concept

Think of the Spring Security filter chain as a sequence of checkpoints at an airport, each checking one specific thing in a fixed order: boarding-pass scan, ID check, security screening, gate boarding — and if you fail any checkpoint, you don't proceed to the next one, you're routed to a rejection path instead. Spring Security's filter chain works the same way: a request passes through an ordered list of `Filter` instances, each responsible for one concern (extracting credentials, establishing the authenticated identity, checking authorization), and only a request that clears every filter reaches your `@RestController`.

The essential pieces:

1. **`SecurityFilterChain` bean** — the declarative entry point. It configures which URL patterns require authentication, which are public, and which authentication mechanism(s) apply.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())                       // stateless APIs typically don't need CSRF protection
            .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health", "/public/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/orders/**").hasAuthority("SCOPE_orders:read")
                .requestMatchers(HttpMethod.POST, "/orders/**").hasAuthority("SCOPE_orders:write")
                .anyRequest().authenticated())
            .build();
    }
}
```

2. **`Authentication`** — an object representing "who is making this request," populated by an `AuthenticationProvider` after credentials are verified, and stored in the `SecurityContext` for the duration of the request (or the session, in a stateful app).
3. **`UserDetailsService` and `PasswordEncoder`** — for form-login or basic-auth style setups, `UserDetailsService` loads a user's stored credentials, and `PasswordEncoder` (e.g., `BCryptPasswordEncoder`) verifies a presented password against the stored hash without ever comparing plaintext directly.
4. **Authorization rules** — expressed declaratively via `authorizeHttpRequests` (URL-pattern-based, evaluated in the filter chain) or via `@PreAuthorize`/`@PostAuthorize` annotations (method-level, evaluated via AOP just before/after a method runs) — both ultimately consult the same `Authentication` object's granted authorities.

Custom filters can be inserted at a specific position in the chain — `http.addFilterBefore(myCustomFilter, UsernamePasswordAuthenticationFilter.class)` — when you need logic that doesn't fit a built-in filter, such as a bespoke internal-service-authentication header check.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming request passes through Spring Security's ordered filter chain: authentication filter, then exception translation, then the authorization filter, before finally reaching the DispatcherServlet and controller; a failure at any stage short-circuits to a 401 or 403 response" font-family="sans-serif">
  <rect x="10" y="80" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="55" y="105" fill="#e6edf3" font-size="9" text-anchor="middle">Request</text>

  <rect x="130" y="80" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="190" y="98" fill="#e6edf3" font-size="9" text-anchor="middle">Authentication</text>
  <text x="190" y="112" fill="#8b949e" font-size="8" text-anchor="middle">filter(s)</text>

  <rect x="280" y="80" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="340" y="98" fill="#e6edf3" font-size="9" text-anchor="middle">Authorization</text>
  <text x="340" y="112" fill="#8b949e" font-size="8" text-anchor="middle">filter (authorizeHttpRequests)</text>

  <rect x="430" y="80" width="120" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="98" fill="#e6edf3" font-size="9" text-anchor="middle">DispatcherServlet</text>
  <text x="490" y="112" fill="#8b949e" font-size="8" text-anchor="middle">-&gt; @RestController</text>

  <rect x="190" y="150" width="120" height="35" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="250" y="172" fill="#f85149" font-size="9" text-anchor="middle">401 Unauthorized</text>
  <rect x="340" y="150" width="120" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="400" y="172" fill="#f0883e" font-size="9" text-anchor="middle">403 Forbidden</text>

  <line x1="100" y1="100" x2="130" y2="100" stroke="#8b949e" marker-end="url(#sf)"/>
  <line x1="250" y1="100" x2="280" y2="100" stroke="#8b949e" marker-end="url(#sf)"/>
  <line x1="400" y1="100" x2="430" y2="100" stroke="#8b949e" marker-end="url(#sf)"/>
  <line x1="190" y1="120" x2="250" y2="150" stroke="#f85149" stroke-dasharray="3,2" marker-end="url(#sf)"/>
  <line x1="340" y1="120" x2="400" y2="150" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#sf)"/>
  <defs>
    <marker id="sf" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Each filter in the chain either passes the request forward or short-circuits it to an error response; only a request that clears every filter reaches the controller.

## 5. Runnable example

Scenario: an orders endpoint. We simulate Spring Security's filter-chain model directly in plain Java — first with no chain at all, then an ordered chain that mirrors authentication-then-authorization, then a chain with a custom filter inserted at a specific position, matching how `addFilterBefore` works in real Spring Security.

### Level 1 — Basic

```java
// File: NoFilterChain.java -- authentication and authorization logic is
// tangled directly into the "controller" method, with no clear separation
// or reusable structure -- exactly what Spring Security's filter chain exists to avoid.
public class NoFilterChain {
    static String handleGetOrders(String presentedToken) {
        // authentication AND authorization, both inline, both ad hoc
        if (!"valid-token".equals(presentedToken)) {
            return "401 Unauthorized";
        }
        // pretend this token implies a role, checked inline too
        boolean hasReadScope = true; // no real structure for where this comes from
        if (!hasReadScope) {
            return "403 Forbidden";
        }
        return "200 OK -- order list";
    }

    public static void main(String[] args) {
        System.out.println(handleGetOrders("valid-token"));
        System.out.println(handleGetOrders("bad-token"));
    }
}
```

How to run: `java NoFilterChain.java`

`handleGetOrders` mixes credential checking and permission checking directly into what stands in for controller logic — there's no reusable place to add a third check (rate limiting, CORS, CSRF) without further tangling this one method. This is the shape of code Spring Security's filter chain exists to replace with a declarative, ordered, reusable pipeline.

### Level 2 — Intermediate

```java
// File: OrderedFilterChain.java -- an explicit, ORDERED chain of filters, each
// with ONE responsibility, mirroring Spring Security's real filter-chain model:
// authentication runs first and establishes an Authentication object; authorization
// runs second and consults ONLY that object, never the raw request again.
import java.util.*;
import java.util.function.*;

public class OrderedFilterChain {
    record Authentication(String principal, Set<String> authorities) {}

    interface SecurityFilter {
        // returns null to allow the chain to continue; a non-null String short-circuits with that response.
        String apply(String presentedToken, Authentication[] authHolder);
    }

    static class AuthenticationFilter implements SecurityFilter {
        public String apply(String presentedToken, Authentication[] authHolder) {
            if (!"valid-token".equals(presentedToken)) return "401 Unauthorized";
            authHolder[0] = new Authentication("alice", Set.of("SCOPE_orders:read"));
            return null; // continue down the chain
        }
    }

    static class AuthorizationFilter implements SecurityFilter {
        final String requiredAuthority;
        AuthorizationFilter(String requiredAuthority) { this.requiredAuthority = requiredAuthority; }
        public String apply(String presentedToken, Authentication[] authHolder) {
            Authentication auth = authHolder[0];
            if (auth == null || !auth.authorities().contains(requiredAuthority)) return "403 Forbidden";
            return null;
        }
    }

    static String runChain(List<SecurityFilter> chain, String presentedToken, Supplier<String> controller) {
        Authentication[] authHolder = new Authentication[1];
        for (SecurityFilter filter : chain) {
            String rejection = filter.apply(presentedToken, authHolder);
            if (rejection != null) return rejection; // short-circuit, controller never runs
        }
        return controller.get();
    }

    public static void main(String[] args) {
        List<SecurityFilter> chain = List.of(new AuthenticationFilter(), new AuthorizationFilter("SCOPE_orders:read"));
        System.out.println(runChain(chain, "valid-token", () -> "200 OK -- order list"));
        System.out.println(runChain(chain, "bad-token", () -> "200 OK -- order list"));
    }
}
```

How to run: `java OrderedFilterChain.java`

`AuthenticationFilter` and `AuthorizationFilter` each implement `SecurityFilter` and handle exactly one concern, exactly mirroring how Spring Security separates authentication filters from the authorization filter driven by `authorizeHttpRequests`. `runChain` walks the list in order, stopping at the first filter that returns a non-null rejection — the controller supplier is never invoked for a rejected request, just as a real controller method is never entered for a request Spring Security rejects. The `Authentication` object is populated once by the authentication filter and consumed, unchanged, by the authorization filter — mirroring the real `SecurityContext`.

### Level 3 — Advanced

```java
// File: CustomFilterInsertedAtPosition.java -- adds a CUSTOM filter for
// internal-service callers, inserted BEFORE the standard authentication
// filter (mirroring http.addFilterBefore(...)), so trusted internal callers
// authenticate via a service header while external callers still go through
// normal token authentication -- both converging on the SAME Authentication
// object and the SAME downstream authorization filter.
import java.util.*;
import java.util.function.*;

public class CustomFilterInsertedAtPosition {
    record Authentication(String principal, Set<String> authorities) {}

    interface SecurityFilter {
        String apply(Map<String, String> headers, Authentication[] authHolder);
    }

    // Custom filter: trusts an internal service header IF it carries a recognized service identity,
    // WITHOUT touching the normal token-based path at all.
    static class InternalServiceAuthFilter implements SecurityFilter {
        static final Set<String> TRUSTED_INTERNAL_SERVICES = Set.of("payment-service");
        public String apply(Map<String, String> headers, Authentication[] authHolder) {
            String serviceHeader = headers.get("X-Internal-Service");
            if (serviceHeader != null) {
                if (!TRUSTED_INTERNAL_SERVICES.contains(serviceHeader)) return "401 Unauthorized -- unrecognized internal service";
                authHolder[0] = new Authentication(serviceHeader, Set.of("SCOPE_orders:read", "SCOPE_orders:write"));
            }
            return null; // no service header present -- fall through to the NEXT filter (token auth)
        }
    }

    static class TokenAuthenticationFilter implements SecurityFilter {
        public String apply(Map<String, String> headers, Authentication[] authHolder) {
            if (authHolder[0] != null) return null; // already authenticated by an earlier filter -- skip
            String token = headers.get("Authorization");
            if (!"Bearer valid-token".equals(token)) return "401 Unauthorized -- missing or invalid token";
            authHolder[0] = new Authentication("alice", Set.of("SCOPE_orders:read"));
            return null;
        }
    }

    static class AuthorizationFilter implements SecurityFilter {
        final String requiredAuthority;
        AuthorizationFilter(String requiredAuthority) { this.requiredAuthority = requiredAuthority; }
        public String apply(Map<String, String> headers, Authentication[] authHolder) {
            Authentication auth = authHolder[0];
            if (auth == null || !auth.authorities().contains(requiredAuthority)) {
                return "403 Forbidden -- " + (auth == null ? "unauthenticated" : auth.principal() + " lacks " + requiredAuthority);
            }
            return null;
        }
    }

    static String runChain(List<SecurityFilter> chain, Map<String, String> headers, Supplier<String> controller) {
        Authentication[] authHolder = new Authentication[1];
        for (SecurityFilter filter : chain) {
            String rejection = filter.apply(headers, authHolder);
            if (rejection != null) return rejection;
        }
        return "200 OK -- authenticated as '" + authHolder[0].principal() + "': " + controller.get();
    }

    public static void main(String[] args) {
        // addFilterBefore(InternalServiceAuthFilter, TokenAuthenticationFilter) -- custom filter runs FIRST.
        List<SecurityFilter> chain = List.of(
                new InternalServiceAuthFilter(),
                new TokenAuthenticationFilter(),
                new AuthorizationFilter("SCOPE_orders:write"));

        // A trusted internal service, authenticated via header, never touches token logic at all.
        System.out.println(runChain(chain, Map.of("X-Internal-Service", "payment-service"), () -> "order write processed"));

        // A normal external caller, authenticated via bearer token, has read-only scope -- denied write.
        System.out.println(runChain(chain, Map.of("Authorization", "Bearer valid-token"), () -> "order write processed"));

        // An untrusted internal-header claim is rejected immediately, before token auth is even attempted.
        System.out.println(runChain(chain, Map.of("X-Internal-Service", "unknown-service"), () -> "order write processed"));
    }
}
```

How to run: `java CustomFilterInsertedAtPosition.java`

`InternalServiceAuthFilter` is inserted first in the chain — mirroring `http.addFilterBefore(internalServiceAuthFilter, UsernamePasswordAuthenticationFilter.class)` in real Spring Security configuration. If an `X-Internal-Service` header is present and recognized, it populates `Authentication` immediately with broad service-level scopes, and `TokenAuthenticationFilter` short-circuits its own check (seeing `authHolder[0]` already set) rather than duplicating work. A normal external request with no such header falls through to `TokenAuthenticationFilter` exactly as before. Both paths converge on the same `AuthorizationFilter`, which doesn't know or care *how* the `Authentication` object was populated — only what authorities it carries, exactly like Spring Security's authorization filter being agnostic to which `AuthenticationProvider` produced the current `Authentication`.

## 6. Walkthrough

Trace `CustomFilterInsertedAtPosition.main`'s second call: `runChain(chain, Map.of("Authorization", "Bearer valid-token"), ...)`. **First**, `InternalServiceAuthFilter.apply` runs. `headers.get("X-Internal-Service")` returns `null` (no such header in this request), so the `if (serviceHeader != null)` branch is skipped entirely, and the method returns `null` — meaning "no opinion, continue to the next filter."

**Next**, `TokenAuthenticationFilter.apply` runs. `authHolder[0]` is still `null` (the previous filter never set it), so its own early-return guard doesn't fire. `headers.get("Authorization")` returns `"Bearer valid-token"`, which matches the expected value, so `authHolder[0]` is set to `new Authentication("alice", Set.of("SCOPE_orders:read"))`, and the method returns `null` to continue.

**Then**, `AuthorizationFilter.apply` runs, configured with `requiredAuthority = "SCOPE_orders:write"`. `auth` is the `Authentication` just set for alice, whose `authorities()` is `{"SCOPE_orders:read"}` — it does not contain `"SCOPE_orders:write"`. The condition `auth == null || !auth.authorities().contains(requiredAuthority)` evaluates to `true` (the second half), so this filter returns `"403 Forbidden -- alice lacks SCOPE_orders:write"`.

**Finally**, `runChain`'s loop sees this non-null rejection and returns it immediately — the `controller` supplier (`() -> "order write processed"`) is never invoked, exactly as a real `@RestController` method would never execute for a request Spring Security's authorization filter rejects.

```
200 OK -- authenticated as 'payment-service': order write processed
403 Forbidden -- alice lacks SCOPE_orders:write
401 Unauthorized -- unrecognized internal service
```

Compare this to a real Spring Security HTTP exchange for the second case:

```
POST /orders HTTP/1.1
Authorization: Bearer valid-token

HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "access_denied", "message": "insufficient_scope"}
```

## 7. Gotchas & takeaways

> A common mistake is forgetting that filter *order* is load-bearing: inserting a custom filter with `addFilterAfter` instead of `addFilterBefore` (or targeting the wrong reference filter class) can silently place it after Spring Security has already made its authentication decision, meaning the custom logic never actually influences the outcome. Always verify a custom filter's position by checking `http.build()`'s resulting chain order in tests, not just by assuming the configuration reads correctly.

- Spring Security's `SecurityFilterChain` is a declarative, ordered pipeline — authentication filters establish an `Authentication`, and a later authorization filter consults it, mirroring the general layered pattern from [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md).
- Custom filters can be inserted at a specific position (`addFilterBefore`/`addFilterAfter`) to handle authentication mechanisms Spring Security doesn't support out of the box, such as a bespoke internal-service header scheme.
- Authorization checks should depend only on the established `Authentication` object, never on re-parsing raw request data — this keeps authorization logic uniform regardless of which authentication mechanism produced the identity.
- A rejected request short-circuits the chain entirely — the controller method is never invoked, which is why Spring Security-level testing (not just controller unit tests) matters for verifying security behavior.
- This core filter model is what [Spring Security's OAuth2 Resource Server support](0401-spring-security-oauth2-resource-server-jwt-opaque.md) builds on — that topic covers the specific authentication filter Spring Security provides for validating JWTs and opaque tokens automatically, instead of writing `TokenAuthenticationFilter` by hand as we did here.
