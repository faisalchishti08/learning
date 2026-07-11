---
card: spring-security
gi: 5
slug: securityfilterchain
title: "SecurityFilterChain"
---

## 1. What it is

`SecurityFilterChain` is the Spring bean that actually defines one specific chain of security filters together with a `RequestMatcher` describing which requests that chain applies to, built declaratively through the `HttpSecurity` DSL and registered as an ordinary `@Bean` — modern Spring Security applications express essentially all of their configuration (which paths require authentication, which roles can access what, CSRF settings, session policy) through one or more of these beans, rather than the older, now-deprecated `WebSecurityConfigurerAdapter` subclassing approach.

```java
@Bean
SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/public/**").permitAll()
            .requestMatchers("/admin/**").hasRole("ADMIN")
            .anyRequest().authenticated())
        .formLogin(Customizer.withDefaults())
        .csrf(Customizer.withDefaults());
    return http.build();
}
```

```java
// MULTIPLE SecurityFilterChain beans can coexist, each scoped to different paths
@Bean
@Order(1)
SecurityFilterChain apiFilterChain(HttpSecurity http) throws Exception {
    http.securityMatcher("/api/**").authorizeHttpRequests(auth -> auth.anyRequest().authenticated());
    return http.build();
}
```

## 2. Why & when

Earlier versions of Spring Security configured security by subclassing `WebSecurityConfigurerAdapter` and overriding its `configure` methods — a pattern that worked, but coupled configuration to inheritance and made it awkward to define genuinely separate, independently-scoped security rules for different parts of a large application (an API surface with one security policy, an admin UI with a different one) within the same application. `SecurityFilterChain` beans replace this with a plain, composable, `@Bean`-based approach: any number of `SecurityFilterChain` beans can be defined, each scoped to a specific set of request paths via `securityMatcher`, each independently configured with its own authentication and authorization rules, letting a single application cleanly host multiple, genuinely different security configurations for different parts of its URL space.

Reach for `SecurityFilterChain` beans when:

- Configuring Spring Security for any modern (Spring Security 5.4+) application — this is the current, recommended configuration mechanism, replacing the deprecated `WebSecurityConfigurerAdapter` subclassing approach entirely.
- A single application genuinely needs multiple, independently-scoped security configurations — a stateless, token-authenticated API section alongside a stateful, session-based, form-login-authenticated admin UI section, for instance, each defined as its own separate `SecurityFilterChain` bean with its own `securityMatcher`.
- Composing security configuration declaratively, in a way that's testable and reviewable as ordinary Spring configuration code, rather than through inheritance-based method overrides that can be harder to trace and reason about, especially as a configuration class grows.

## 3. Core concept

```
 ONE SecurityFilterChain bean = ONE RequestMatcher (which requests this chain applies to)
                                + ONE ordered list of filters (built via the HttpSecurity DSL)

 multiple SecurityFilterChain beans can coexist:
   chain A: securityMatcher("/api/**")   -> stateless, token-based auth
   chain B: securityMatcher("/admin/**") -> stateful, session-based, form login
   chain C: (no matcher -- catches EVERYTHING else)  -> some default policy

 FilterChainProxy (the previous card) tries EACH registered SecurityFilterChain's matcher,
 IN ORDER, and uses the FIRST one whose matcher matches the incoming request's path
```

Multiple chains, each independently configured, let genuinely different parts of one application enforce genuinely different security rules — a capability that was awkward to express cleanly under the older subclassing model.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming request is matched against multiple registered SecurityFilterChain beans in order with the first matching chains own independently configured filters applying to that request">
  <rect x="20" y="70" width="130" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="98" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">request /api/orders</text>

  <rect x="220" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="38" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">chain A: /api/**</text>
  <text x="310" y="52" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">MATCHES -- applies</text>

  <rect x="220" y="70" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="310" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">chain B: /admin/**</text>
  <text x="310" y="102" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">not tried (already matched)</text>

  <rect x="220" y="120" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="310" y="138" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">chain C: catch-all</text>
  <text x="310" y="152" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">not tried</text>

  <defs><marker id="a5" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="150" y1="93" x2="220" y2="40" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a5)"/>
</svg>

The first matching chain wins, and its own independently-configured filters are what apply to that request.

## 5. Runnable example

The scenario: model multiple `SecurityFilterChain`-style beans, each with its own matcher and rules, and a dispatcher trying them in order to find the first match. Start with a single chain applying to all requests, then add multiple chains with distinct matchers, then add a case where request path ordering across chains actually matters, demonstrating why chain registration order is significant.

### Level 1 — Basic

A single security filter chain applying to all requests — the simplest possible configuration.

```java
import java.util.*;
import java.util.function.Predicate;

public class SecurityFilterChainLevel1 {
    record Request(String path, boolean authenticated) {}

    static class SecurityFilterChain {
        Predicate<String> matcher;
        java.util.function.Function<Request, Boolean> rule;
        SecurityFilterChain(Predicate<String> matcher, java.util.function.Function<Request, Boolean> rule) {
            this.matcher = matcher; this.rule = rule;
        }
    }

    public static void main(String[] args) {
        SecurityFilterChain chain = new SecurityFilterChain(
                path -> true, // matches EVERYTHING
                request -> request.authenticated() // require authentication for everything
        );

        Request r1 = new Request("/orders", true);
        Request r2 = new Request("/orders", false);

        System.out.println("authenticated request allowed? " + chain.rule.apply(r1));
        System.out.println("unauthenticated request allowed? " + chain.rule.apply(r2));
    }
}
```

How to run: `java SecurityFilterChainLevel1.java`

One chain, one matcher (matching everything), one rule — this models the simplest possible `SecurityFilterChain` bean, equivalent to a single `.anyRequest().authenticated()` configuration with no path-based differentiation at all.

### Level 2 — Intermediate

Add multiple chains with distinct matchers, and a dispatcher selecting the first matching chain for a given request, mirroring how `FilterChainProxy` selects among multiple registered `SecurityFilterChain` beans.

```java
import java.util.*;
import java.util.function.Predicate;
import java.util.function.Function;

public class SecurityFilterChainLevel2 {
    record Request(String path, boolean authenticated, boolean hasApiToken) {}

    record NamedChain(String name, Predicate<String> matcher, Function<Request, Boolean> rule) {}

    static Optional<NamedChain> selectChain(List<NamedChain> chains, String path) {
        for (NamedChain chain : chains) {
            if (chain.matcher().test(path)) return Optional.of(chain); // FIRST matching chain wins
        }
        return Optional.empty();
    }

    public static void main(String[] args) {
        List<NamedChain> chains = List.of(
                new NamedChain("api-chain", path -> path.startsWith("/api/"), request -> request.hasApiToken()),
                new NamedChain("default-chain", path -> true, request -> request.authenticated())
        );

        Request apiRequest = new Request("/api/orders", false, true); // NOT session-authenticated, but HAS an api token
        Request webRequest = new Request("/orders", true, false); // session-authenticated, no api token

        NamedChain selectedForApi = selectChain(chains, apiRequest.path()).orElseThrow();
        System.out.println("API request matched: " + selectedForApi.name() + ", allowed? " + selectedForApi.rule().apply(apiRequest));

        NamedChain selectedForWeb = selectChain(chains, webRequest.path()).orElseThrow();
        System.out.println("web request matched: " + selectedForWeb.name() + ", allowed? " + selectedForWeb.rule().apply(webRequest));
    }
}
```

How to run: `java SecurityFilterChainLevel2.java`

The API request matches `"api-chain"` (its path starts with `/api/`) and is evaluated against that chain's own rule (`hasApiToken`, which is `true`, so it's allowed) — the web request falls through to `"default-chain"` (matching everything) and is evaluated against session authentication instead — two structurally different requests, correctly routed to two structurally different, independently-configured security rules.

### Level 3 — Advanced

Add a case demonstrating why chain registration *order* matters — a more specific matcher registered after a broader, catch-all matcher would never actually be reached, since the broader one matches first.

```java
import java.util.*;
import java.util.function.Predicate;
import java.util.function.Function;

public class SecurityFilterChainLevel3 {
    record Request(String path, boolean authenticated, boolean hasApiToken) {}
    record NamedChain(String name, Predicate<String> matcher, Function<Request, Boolean> rule) {}

    static Optional<NamedChain> selectChain(List<NamedChain> chains, String path) {
        for (NamedChain chain : chains) {
            if (chain.matcher().test(path)) return Optional.of(chain);
        }
        return Optional.empty();
    }

    public static void main(String[] args) {
        // MISCONFIGURED order: the catch-all chain is registered FIRST -- api-chain becomes UNREACHABLE
        List<NamedChain> misconfigured = List.of(
                new NamedChain("default-chain", path -> true, request -> request.authenticated()),
                new NamedChain("api-chain", path -> path.startsWith("/api/"), request -> request.hasApiToken())
        );

        Request apiRequest = new Request("/api/orders", false, true);

        NamedChain matched = selectChain(misconfigured, apiRequest.path()).orElseThrow();
        System.out.println("MISCONFIGURED order -- API request matched: " + matched.name()
                + " (should have been 'api-chain', but the catch-all matched FIRST)");
        System.out.println("evaluated against WRONG rule (authenticated): " + matched.rule().apply(apiRequest));

        // CORRECTED order: the MORE SPECIFIC matcher (api-chain) must come FIRST
        List<NamedChain> corrected = List.of(
                new NamedChain("api-chain", path -> path.startsWith("/api/"), request -> request.hasApiToken()),
                new NamedChain("default-chain", path -> true, request -> request.authenticated())
        );

        NamedChain matchedCorrectly = selectChain(corrected, apiRequest.path()).orElseThrow();
        System.out.println("CORRECTED order -- API request matched: " + matchedCorrectly.name());
        System.out.println("evaluated against CORRECT rule (hasApiToken): " + matchedCorrectly.rule().apply(apiRequest));
    }
}
```

How to run: `java SecurityFilterChainLevel3.java`

In `misconfigured` order, `"default-chain"`'s catch-all matcher (`path -> true`) matches every request first, including `/api/orders`, so `"api-chain"` is never even reached, and the API request is incorrectly evaluated against session-based `authenticated` (which is `false` for this token-authenticated request, producing a wrong, overly-restrictive result); in `corrected` order, the more specific `"api-chain"` matcher is tried first, correctly matches, and the request is evaluated against the appropriate `hasApiToken` rule instead — this is precisely why Spring Security's real `SecurityFilterChain` beans use `@Order` (or declaration order) to ensure more specific matchers are evaluated before broader, catch-all ones.

## 6. Walkthrough

Trace `selectChain(misconfigured, "/api/orders")` in Level 3.

1. `selectChain` iterates `misconfigured` in list order — the first element is `"default-chain"`, whose `matcher` is `path -> true`.
2. `chain.matcher().test("/api/orders")` evaluates the lambda `path -> true`, which returns `true` unconditionally, regardless of what `path` actually is.
3. Because this matches, `selectChain` immediately returns `Optional.of("default-chain")` — the loop never even reaches the second element, `"api-chain"`, despite it being the more specific, more appropriate match for this particular request's path.
4. Back in `main`, `matched.rule().apply(apiRequest)` evaluates `"default-chain"`'s rule, `request -> request.authenticated()`, against `apiRequest`, whose `authenticated` field is `false` (this request relies on an API token, not session authentication) — the result is `false`, incorrectly rejecting a request that should have been allowed under the API token rule.
5. In the `corrected` list, `"api-chain"` is listed first — `chain.matcher().test("/api/orders")` for `"api-chain"`'s matcher (`path -> path.startsWith("/api/")`) evaluates `true`, so it matches immediately, and `selectChain` returns it without ever considering `"default-chain"` — `matchedCorrectly.rule().apply(apiRequest)` now correctly evaluates `hasApiToken`, which is `true`, producing the correct, intended result.

```
misconfigured = [default-chain(matches EVERYTHING), api-chain(matches /api/**)]
  selectChain("/api/orders"): default-chain.matcher matches FIRST -> api-chain NEVER REACHED
  wrong rule applied (authenticated=false) -> INCORRECTLY rejected

corrected = [api-chain(matches /api/**), default-chain(matches EVERYTHING)]
  selectChain("/api/orders"): api-chain.matcher matches FIRST (more specific, listed first)
  correct rule applied (hasApiToken=true) -> CORRECTLY allowed
```

## 7. Gotchas & takeaways

> **Gotcha:** when multiple `SecurityFilterChain` beans are registered, their relative order (controlled via `@Order` or declaration order) is not a minor detail — a broader or catch-all matcher registered before a more specific one will silently make the more specific chain completely unreachable, exactly as `misconfigured` demonstrated, with no compile-time or obvious runtime error indicating the mistake; the more specific chain's rules simply never apply, which can be a subtle and dangerous security misconfiguration if not caught during review or testing.

- `SecurityFilterChain` beans are the current, recommended way to configure Spring Security, replacing the deprecated `WebSecurityConfigurerAdapter` subclassing approach with plain, composable `@Bean` definitions built through the `HttpSecurity` DSL.
- Multiple `SecurityFilterChain` beans, each scoped via `securityMatcher` to a specific set of paths, let a single application cleanly host genuinely different security configurations for different parts of its URL space — an API section with stateless token auth, an admin UI with stateful session auth, and so on.
- The order in which multiple chains are registered is significant — more specific matchers must be ordered before broader ones, or the broader matcher will shadow the more specific chain entirely, silently applying the wrong security rules to requests that should have matched the more specific configuration.
- The next card covers the full, detailed default ordering of Spring Security's individual built-in filters *within* a single chain — this card's ordering concern (which whole chain applies to a request) is a distinct, higher-level concern from that filter-level ordering within one already-selected chain.
