---
card: spring-security
gi: 20
slug: multiple-security-filter-chains
title: "Multiple security filter chains"
---

## 1. What it is

An application can register more than one `SecurityFilterChain` bean, each annotated with `@Order` to establish evaluation priority and each scoped to a distinct subset of request paths via `securityMatcher`/`securityMatchers` — Spring Security evaluates each chain's matcher in `@Order` sequence for every incoming request, and the *first* chain whose matcher accepts the request path is the only one applied to it, with all of that chain's own configuration (authentication mechanism, authorization rules, session policy) taking over completely for matching requests.

```java
@Bean
@Order(1)
public SecurityFilterChain apiFilterChain(HttpSecurity http) throws Exception {
    http.securityMatcher("/api/**")
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS));
    return http.build();
}

@Bean
@Order(2)
public SecurityFilterChain webFilterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .formLogin(Customizer.withDefaults());
    return http.build();
}
```

## 2. Why & when

A single `HttpSecurity` configuration inherently applies one uniform policy to every request it matches — but many real applications genuinely need *different* policies for different parts of the same application: a JSON REST API under `/api/**` that authenticates via a stateless bearer token and never redirects, alongside a traditional server-rendered UI under everything else that authenticates via session-cookie-backed form login and redirects to a login page on failure. Multiple `SecurityFilterChain` beans, each scoped with `securityMatcher` and ordered with `@Order`, is how Spring Security supports genuinely different security postures living side by side in the same application without either policy compromising the other.

Reach for multiple filter chains when:

- The application serves both a browser-facing UI (session-based, form login, redirect-on-failure) and a JSON API (stateless, token-based, `401`-on-failure) from the same server, and a single `AuthenticationEntryPoint`/session policy can't correctly serve both.
- Different subsets of paths need entirely different authentication mechanisms — internal admin endpoints authenticated via mutual TLS or IP allowlisting, customer-facing endpoints via OAuth2 login.
- A narrower, more specific matcher (like `/api/**`) needs a distinct, higher-priority policy that should not fall through to a broader, catch-all chain meant for everything else.

## 3. Core concept

```
 incoming request
        |
        v
 chain with @Order(1), securityMatcher("/api/**")   -- checked FIRST (lowest @Order value = highest priority)
   matches?  YES -> this chain's ENTIRE policy applies; no other chain is even consulted
             NO  -> fall through to the next chain
        |
        v
 chain with @Order(2), NO securityMatcher (defaults to "/**")   -- the catch-all
   matches?  YES (always, since it matches everything) -> this chain's policy applies
```

Exactly one chain ever applies to a given request — the first, in `@Order` sequence, whose matcher accepts it.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request is checked against an ordered list of security filter chains the first chain whose matcher accepts the request path is the only one applied requests to slash api go to a stateless API chain everything else falls through to a session based web chain">
  <rect x="15" y="65" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">incoming request</text>
  <text x="85" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">e.g. /api/orders</text>

  <rect x="215" y="20" width="200" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="315" y="40" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Order(1) chain</text>
  <text x="315" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">securityMatcher(/api/**)</text>

  <rect x="215" y="110" width="200" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="130" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Order(2) chain</text>
  <text x="315" y="143" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">catch-all (/**)</text>

  <rect x="470" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="545" y="94" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">that chain's full policy</text>

  <defs><marker id="a20" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="80" x2="215" y2="45" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a20)"/>
  <text x="185" y="55" fill="#8b949e" font-size="6.5" font-family="sans-serif">checked 1st</text>
  <line x1="155" y1="90" x2="215" y2="130" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a20)"/>
  <text x="185" y="150" fill="#8b949e" font-size="6.5" font-family="sans-serif">fallback</text>
  <line x1="415" y1="40" x2="470" y2="80" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a20)"/>
  <line x1="415" y1="130" x2="470" y2="95" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a20)"/>
</svg>

Priority order flows top to bottom; only the first matching chain's policy is ever applied to a given request.

## 5. Runnable example

The scenario: model an ordered list of `(matcher, policy)` pairs and route requests through it, showing the same server correctly applying two different policies to two different path prefixes. Start with two chains and simple routing, then add explicit `@Order` semantics with a specificity mistake and its consequence, then add a fully realistic three-chain setup (API, admin, web) with distinct authentication mechanisms each.

### Level 1 — Basic

Two chains — a stateless API chain and a session-based web chain — routed by path prefix.

```java
import java.util.*;
import java.util.function.Predicate;

public class MultiChainLevel1 {
    record Request(String path, String bearerToken, String sessionUser) {}
    record FilterChain(Predicate<String> matcher, java.util.function.Function<Request, String> handle) {}

    public static void main(String[] args) {
        FilterChain apiChain = new FilterChain(
                path -> path.startsWith("/api/"),
                req -> req.bearerToken() != null ? "200 OK (API, token=" + req.bearerToken() + ")" : "401 Unauthorized (API)"
        );
        FilterChain webChain = new FilterChain(
                path -> true, // catch-all
                req -> req.sessionUser() != null ? "200 OK (web, user=" + req.sessionUser() + ")" : "302 Found -> /login"
        );

        List<FilterChain> chains = List.of(apiChain, webChain); // ORDER matters: apiChain checked first

        for (Request req : List.of(
                new Request("/api/orders", "tok-123", null),
                new Request("/account", null, "alice"))) {
            for (FilterChain chain : chains) {
                if (chain.matcher().test(req.path())) {
                    System.out.println(req.path() + " -> " + chain.handle().apply(req));
                    break;
                }
            }
        }
    }
}
```

How to run: `java MultiChainLevel1.java`

`/api/orders` matches `apiChain`'s matcher first and is evaluated entirely by its token-based policy; `/account` fails that matcher and falls through to `webChain`'s catch-all, which applies its own, entirely different session-based policy — the same list, two genuinely different security postures.

### Level 2 — Intermediate

Demonstrate the consequence of getting matcher specificity/order wrong: a broad catch-all placed *before* a specific matcher silently shadows it.

```java
import java.util.*;
import java.util.function.Predicate;
import java.util.function.Function;

public class MultiChainLevel2 {
    record Request(String path, String bearerToken, String sessionUser) {}
    record FilterChain(String name, Predicate<String> matcher, Function<Request, String> handle) {}

    static String route(List<FilterChain> chains, Request req) {
        for (FilterChain chain : chains) {
            if (chain.matcher().test(req.path())) return chain.name() + ": " + chain.handle().apply(req);
        }
        return "no chain matched (should never happen with a catch-all present)";
    }

    public static void main(String[] args) {
        FilterChain apiChain = new FilterChain("apiChain", path -> path.startsWith("/api/"),
                req -> req.bearerToken() != null ? "200 OK (token)" : "401 Unauthorized");
        FilterChain webChain = new FilterChain("webChain", path -> true,
                req -> req.sessionUser() != null ? "200 OK (session)" : "302 Found -> /login");

        Request apiRequest = new Request("/api/orders", "tok-123", null);

        System.out.println("CORRECT order (specific first):");
        System.out.println("  " + route(List.of(apiChain, webChain), apiRequest));

        System.out.println("WRONG order (catch-all first, shadows apiChain):");
        System.out.println("  " + route(List.of(webChain, apiChain), apiRequest));
    }
}
```

How to run: `java MultiChainLevel2.java`

With `apiChain` first, `/api/orders` correctly gets the token-based `200 OK`; with `webChain` first (a mistaken `@Order` assignment), the *same* request instead matches `webChain`'s catch-all matcher immediately, applying the session-based policy to a request that was never meant to be checked that way — since `req.sessionUser()` is `null`, it incorrectly returns a login redirect for what should have been a token-authenticated API call.

### Level 3 — Advanced

Three chains — API (stateless token), admin (IP allowlist), and web (session/form login) — each with a genuinely distinct authentication mechanism, ordered correctly by specificity.

```java
import java.util.*;
import java.util.function.Predicate;
import java.util.function.Function;

public class MultiChainLevel3 {
    record Request(String path, String bearerToken, String sourceIp, String sessionUser) {}
    record FilterChain(String name, Predicate<String> matcher, Function<Request, String> handle) {}

    static final Set<String> ADMIN_ALLOWLIST = Set.of("10.0.0.5", "10.0.0.6");

    public static void main(String[] args) {
        FilterChain adminChain = new FilterChain("adminChain", path -> path.startsWith("/admin/"),
                req -> ADMIN_ALLOWLIST.contains(req.sourceIp())
                        ? "200 OK (admin, IP-allowlisted)"
                        : "403 Forbidden (admin, IP not allowlisted: " + req.sourceIp() + ")");

        FilterChain apiChain = new FilterChain("apiChain", path -> path.startsWith("/api/"),
                req -> req.bearerToken() != null ? "200 OK (API, token verified)" : "401 Unauthorized (API, no token)");

        FilterChain webChain = new FilterChain("webChain", path -> true,
                req -> req.sessionUser() != null ? "200 OK (web, session=" + req.sessionUser() + ")" : "302 Found -> /login");

        // most-specific matchers FIRST: admin, then api, then the catch-all web chain last
        List<FilterChain> chains = List.of(adminChain, apiChain, webChain);

        List<Request> requests = List.of(
                new Request("/admin/reports", null, "203.0.113.9", null),
                new Request("/admin/reports", null, "10.0.0.5", null),
                new Request("/api/orders", "tok-abc", null, null),
                new Request("/account", null, null, "alice")
        );

        for (Request req : requests) {
            for (FilterChain chain : chains) {
                if (chain.matcher().test(req.path())) {
                    System.out.println(req.path() + " (" + chain.name() + ") -> " + chain.handle().apply(req));
                    break;
                }
            }
        }
    }
}
```

How to run: `java MultiChainLevel3.java`

Each request is checked against `adminChain` first, then `apiChain`, then `webChain`'s catch-all — an `/admin/reports` request from a non-allowlisted IP is correctly rejected by `adminChain` itself (never falling through to the other two chains, since its path already matched), while an `/admin/reports` request from an allowlisted IP succeeds; `/api/orders` skips `adminChain` (path mismatch) and is handled entirely by `apiChain`'s token check; `/account` skips both specific chains and is handled by `webChain`'s session check.

## 6. Walkthrough

Trace the request `new Request("/admin/reports", null, "203.0.113.9", null)` from Level 3.

1. The outer loop begins iterating `chains` in order: `adminChain` first. Its matcher, `path -> path.startsWith("/admin/")`, is tested against `"/admin/reports"` and returns `true`, since the path does begin with `/admin/`.
2. Because the matcher matched, the inner `if` block runs `chain.handle().apply(req)`, and the loop's `break` ensures neither `apiChain` nor `webChain` is ever consulted for this request — `adminChain`'s policy is the *only* one applied.
3. Inside `adminChain`'s handler, `ADMIN_ALLOWLIST.contains(req.sourceIp())` checks `"203.0.113.9"` against the set `{"10.0.0.5", "10.0.0.6"}`, which returns `false`, so the handler returns `"403 Forbidden (admin, IP not allowlisted: 203.0.113.9)"`.
4. The next request, `new Request("/admin/reports", null, "10.0.0.5", null)`, goes through the identical matching path — `adminChain` matches on path again — but this time `ADMIN_ALLOWLIST.contains("10.0.0.5")` returns `true`, so the handler returns the `200 OK` success message instead.
5. Note that both admin requests were decided entirely within `adminChain` and never touched `apiChain`'s token logic or `webChain`'s session logic at all — this is the core guarantee multiple ordered filter chains provide: complete policy isolation per matched path prefix.

```
/admin/reports (IP 203.0.113.9) -> adminChain matches path -> IP not allowlisted -> 403
/admin/reports (IP 10.0.0.5)    -> adminChain matches path -> IP allowlisted     -> 200
(neither request ever reaches apiChain or webChain)
```

## 7. Gotchas & takeaways

> **Gotcha:** every `SecurityFilterChain` bean beyond the first one *must* have a `securityMatcher` narrowing which paths it applies to — a second bean with no matcher (or an overly broad one) placed at a lower `@Order` value than intended will silently swallow requests meant for a more specific chain, exactly as demonstrated in Level 2's reversed-order example. Always order chains from most specific matcher to the broadest catch-all.

- Multiple `SecurityFilterChain` beans, each with `@Order` and `securityMatcher`, let genuinely different security postures (stateless API, IP-restricted admin, session-based web UI) coexist in one application, each fully isolated from the others.
- Exactly one chain applies per request — the first, in ascending `@Order` sequence, whose matcher accepts the request path; no partial merging of two chains' policies ever happens for a single request.
- Order chains from most specific matcher to least specific, ending with one broad catch-all chain — reversing this ordering silently shadows the more specific chains.
- Debugging "why is this endpoint being authenticated the wrong way" for an application with multiple chains should start by identifying exactly which chain's `securityMatcher` actually claimed the request.
