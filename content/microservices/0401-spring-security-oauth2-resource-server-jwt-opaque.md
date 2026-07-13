---
card: microservices
gi: 401
slug: spring-security-oauth2-resource-server-jwt-opaque
title: "Spring Security OAuth2 Resource Server (JWT & opaque)"
---

## 1. What it is

Spring Security's **OAuth2 Resource Server** module is the concrete Spring implementation of validating incoming bearer tokens, plugging directly into the [Spring Security core filter chain](0400-spring-security-core-filters-authentication-authorization.md) as a specialized authentication filter. It supports both major token styles covered earlier in this section: **JWTs**, verified locally via signature checking against the issuer's public key (see [JWT structure & validation](0384-json-web-token-jwt-structure-validation.md)), and **opaque tokens**, verified remotely via a call to the authorization server's introspection endpoint (see [opaque tokens & token introspection](0385-opaque-tokens-token-introspection.md)) — with Spring Security handling the mechanics of either approach once you declare which one you're using.

## 2. Why & when

You reach for this module specifically when a Spring Boot service needs to accept bearer tokens issued by an external or shared authorization server, rather than managing its own authentication:

- **Every resource server behind an [OAuth2](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md) setup needs this** — the gateway validating a user's token, or an internal service validating a [service-to-service](0391-service-to-service-authentication.md) client-credentials token, both use the same resource-server machinery.
- **JWT and opaque tokens trade off differently**, and Spring Security lets you configure either with a few lines, rather than hand-rolling signature verification or introspection HTTP calls yourself: JWTs validate locally and fast but can't be revoked before expiry without extra machinery; opaque tokens require a network round-trip per validation but can be revoked instantly, since the authorization server is consulted on every check.
- **Getting the configuration wrong is a common, high-impact mistake** — misconfiguring the issuer URI, skipping audience validation, or trusting a token without checking its signature algorithm are exactly the kinds of subtle bugs a well-tested library like Spring Security exists to prevent, if configured correctly.

## 3. Core concept

Think of the resource server as a bouncer with two different ways of checking a wristband: for a **JWT**, the bouncer holds the venue's own UV light and checks the wristband's hologram directly, on the spot, with no phone call needed — fast, but only as trustworthy as the light being genuine and up to date. For an **opaque token**, the wristband has no visible markings at all; the bouncer has to call the wristband office and ask "is `#4471` still valid right now?" — slower, but the office can say "no, that one was cancelled five minutes ago" even if the physical wristband looks fine.

Spring Security configures each style declaratively:

```java
// application.yml -- JWT resource server: validated LOCALLY against the issuer's public keys
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://auth.example.com   # Spring auto-discovers the JWK set from here

// application.yml -- OPAQUE token resource server: validated REMOTELY via introspection
spring:
  security:
    oauth2:
      resourceserver:
        opaquetoken:
          introspection-uri: https://auth.example.com/oauth2/introspect
          client-id: order-service
          client-secret: ${INTROSPECTION_CLIENT_SECRET}
```

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers(HttpMethod.GET, "/orders/**").hasAuthority("SCOPE_orders:read")
            .anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2
            .jwt(jwt -> jwt.jwtAuthenticationConverter(customAuthoritiesConverter())))
        // .opaqueToken(Customizer.withDefaults())  -- mutually exclusive alternative to .jwt(...) above
        .build();
}
```

Two details matter beyond just picking JWT or opaque:

1. **Scope-to-authority mapping.** Spring Security prefixes OAuth2 scopes with `SCOPE_` by default when building granted authorities (a token scope `orders:read` becomes the authority `SCOPE_orders:read`), which is what `hasAuthority("SCOPE_orders:read")` in `authorizeHttpRequests` checks against — a custom `JwtAuthenticationConverter` lets you map claims differently if your authorization server structures roles or scopes another way.
2. **Audience validation isn't automatic by default.** Spring Security validates the signature, issuer, and expiry out of the box, but checking the `aud` claim against this specific service's identity requires adding a custom `OAuth2TokenValidator` — skipping this is exactly the audience-confusion gap flagged in [token relay / propagation](0389-token-relay-propagation-between-services.md).

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Security's OAuth2 resource server branches on token style: a JWT is validated locally against cached public keys, while an opaque token triggers a remote introspection call to the authorization server before the request proceeds" font-family="sans-serif">
  <rect x="20" y="90" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">Incoming request</text>
  <text x="80" y="127" fill="#8b949e" font-size="8" text-anchor="middle">Authorization: Bearer ...</text>

  <rect x="230" y="30" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="52" fill="#e6edf3" font-size="10" text-anchor="middle">JWT path</text>
  <text x="310" y="68" fill="#8b949e" font-size="8" text-anchor="middle">local signature check</text>
  <text x="310" y="82" fill="#8b949e" font-size="8" text-anchor="middle">against cached JWK set</text>

  <rect x="230" y="150" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="310" y="172" fill="#e6edf3" font-size="10" text-anchor="middle">Opaque token path</text>
  <text x="310" y="188" fill="#8b949e" font-size="8" text-anchor="middle">remote call to</text>
  <text x="310" y="202" fill="#8b949e" font-size="8" text-anchor="middle">/oauth2/introspect</text>

  <rect x="460" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">authorizeHttpRequests</text>
  <text x="535" y="127" fill="#8b949e" font-size="8" text-anchor="middle">hasAuthority(SCOPE_...)</text>

  <line x1="140" y1="105" x2="230" y2="60" stroke="#6db33f" marker-end="url(#os)"/>
  <line x1="140" y1="125" x2="230" y2="180" stroke="#f0883e" marker-end="url(#os)"/>
  <line x1="390" y1="60" x2="460" y2="105" stroke="#6db33f" marker-end="url(#os)"/>
  <line x1="390" y1="180" x2="460" y2="125" stroke="#f0883e" marker-end="url(#os)"/>
  <defs>
    <marker id="os" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Both token styles converge on the same authorization step once validated — the difference is entirely in how the resource server establishes trust in the token before that point.

## 5. Runnable example

Scenario: an order-service resource server accepting either token style. We build a JWT-only validator first, add opaque-token support with simulated introspection, then combine both with an introspection-result cache so opaque validation doesn't pay a network round-trip on every single request — a real, production-relevant performance concern for opaque tokens.

### Level 1 — Basic

```java
// File: JwtOnlyResourceServer.java -- validates a JWT LOCALLY: signature,
// issuer, and expiry, with NO network call needed. Mirrors
// spring.security.oauth2.resourceserver.jwt.issuer-uri configuration.
import java.time.*;
import java.util.*;

public class JwtOnlyResourceServer {
    record Jwt(String issuer, String subject, Set<String> scopes, Instant expiresAt, String signature) {}

    static final String TRUSTED_ISSUER = "https://auth.example.com";
    static final String EXPECTED_SIGNING_KEY_FINGERPRINT = "key-2026-a";

    static boolean signatureValid(Jwt jwt) {
        // Stand-in for real JWK-based signature verification.
        return jwt.signature().equals("signed-with-" + EXPECTED_SIGNING_KEY_FINGERPRINT);
    }

    static String validateAndHandle(Jwt jwt, Instant now, String requiredScope) {
        if (!TRUSTED_ISSUER.equals(jwt.issuer())) return "401 Unauthorized -- unknown issuer";
        if (!signatureValid(jwt)) return "401 Unauthorized -- invalid signature";
        if (now.isAfter(jwt.expiresAt())) return "401 Unauthorized -- token expired";
        if (!jwt.scopes().contains(requiredScope)) return "403 Forbidden -- missing scope " + requiredScope;
        return "200 OK -- authenticated as '" + jwt.subject() + "' (validated locally, no network call)";
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-07-13T12:00:00Z");
        Jwt validJwt = new Jwt(TRUSTED_ISSUER, "alice", Set.of("orders:read"), now.plusSeconds(300), "signed-with-key-2026-a");
        System.out.println(validateAndHandle(validJwt, now, "orders:read"));
    }
}
```

How to run: `java JwtOnlyResourceServer.java`

`validateAndHandle` performs every check locally — issuer comparison, signature verification, expiry, and scope — with no external call at any point. This models exactly what `spring.security.oauth2.resourceserver.jwt.issuer-uri` configures Spring Security to do automatically: it fetches and caches the issuer's public keys once, then verifies every subsequent JWT's signature against that cached key set without a per-request network round-trip.

### Level 2 — Intermediate

```java
// File: OpaqueTokenResourceServer.java -- validates an OPAQUE token via a
// simulated call to the authorization server's introspection endpoint.
// Unlike Level 1, there is NO local signature to check -- the token is a
// meaningless string until the authorization server says otherwise, on EVERY call.
import java.time.*;
import java.util.*;

public class OpaqueTokenResourceServer {
    record IntrospectionResponse(boolean active, String subject, Set<String> scopes, Instant expiresAt) {}

    // Simulated authorization server introspection endpoint -- a REAL network call in production.
    static final Map<String, IntrospectionResponse> AUTH_SERVER_STATE = new HashMap<>();
    static {
        AUTH_SERVER_STATE.put("opaque-abc123",
                new IntrospectionResponse(true, "alice", Set.of("orders:read"), Instant.parse("2026-07-13T13:00:00Z")));
        // This one was issued but has since been REVOKED -- introspection reflects that immediately.
        AUTH_SERVER_STATE.put("opaque-revoked999",
                new IntrospectionResponse(false, "mallory", Set.of("orders:write"), Instant.parse("2026-07-13T13:00:00Z")));
    }

    static int introspectionCallCount = 0;

    static IntrospectionResponse introspect(String token) {
        introspectionCallCount++; // simulates the cost of a real network round-trip, made EVERY time
        return AUTH_SERVER_STATE.getOrDefault(token, new IntrospectionResponse(false, null, Set.of(), Instant.EPOCH));
    }

    static String validateAndHandle(String token, Instant now, String requiredScope) {
        IntrospectionResponse resp = introspect(token);
        if (!resp.active()) return "401 Unauthorized -- token inactive or unknown per authorization server";
        if (now.isAfter(resp.expiresAt())) return "401 Unauthorized -- token expired";
        if (!resp.scopes().contains(requiredScope)) return "403 Forbidden -- missing scope " + requiredScope;
        return "200 OK -- authenticated as '" + resp.subject() + "' (validated via remote introspection call #" + introspectionCallCount + ")";
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-07-13T12:30:00Z");
        System.out.println(validateAndHandle("opaque-abc123", now, "orders:read"));
        // The SAME valid token, requested again, STILL triggers a fresh network call -- no caching yet.
        System.out.println(validateAndHandle("opaque-abc123", now, "orders:read"));
        System.out.println(validateAndHandle("opaque-revoked999", now, "orders:write"));
        System.out.println("Total introspection calls made: " + introspectionCallCount);
    }
}
```

How to run: `java OpaqueTokenResourceServer.java`

`introspect` stands in for the real HTTP call Spring Security's `OpaqueTokenIntrospector` makes to `introspection-uri` on every request bearing an opaque token. There's no signature to check locally, because opaque tokens carry no verifiable structure of their own — the authorization server's answer *is* the source of truth. Notice the revoked token is rejected immediately, something a pure JWT approach cannot do before its `exp` claim naturally passes — this is opaque tokens' key advantage. But also notice `introspectionCallCount` increments on *every* call, including two calls for the identical, still-valid `opaque-abc123` token — a real production cost that Level 3 addresses.

### Level 3 — Advanced

```java
// File: DualModeResourceServerWithCache.java -- supports BOTH token styles
// (detecting which one was presented, mirroring how a real gateway might
// accept either), and adds a SHORT-LIVED cache for opaque token introspection
// results -- reducing network round-trips while still respecting a maximum
// cache TTL so revocation is noticed within a bounded, acceptable delay.
import java.time.*;
import java.util.*;

public class DualModeResourceServerWithCache {
    record Jwt(String issuer, String subject, Set<String> scopes, Instant expiresAt, String signature) {}
    record IntrospectionResponse(boolean active, String subject, Set<String> scopes, Instant expiresAt) {}
    record CachedIntrospection(IntrospectionResponse response, Instant cachedAt) {}

    static final String TRUSTED_ISSUER = "https://auth.example.com";
    static final Duration CACHE_TTL = Duration.ofSeconds(30); // bounds how stale a revocation check can be

    static final Map<String, IntrospectionResponse> AUTH_SERVER_STATE = Map.of(
            "opaque-abc123", new IntrospectionResponse(true, "alice", Set.of("orders:read"), Instant.parse("2026-07-13T13:00:00Z"))
    );
    static final Map<String, CachedIntrospection> introspectionCache = new HashMap<>();
    static int realIntrospectionCalls = 0;

    static boolean looksLikeJwt(String token) { return token.startsWith("jwt-"); }

    static boolean signatureValid(Jwt jwt) { return jwt.signature().equals("signed-with-key-2026-a"); }

    static IntrospectionResponse introspectWithCache(String token, Instant now) {
        CachedIntrospection cached = introspectionCache.get(token);
        if (cached != null && Duration.between(cached.cachedAt(), now).compareTo(CACHE_TTL) < 0) {
            return cached.response(); // fresh enough -- skip the network call entirely
        }
        realIntrospectionCalls++;
        IntrospectionResponse fresh = AUTH_SERVER_STATE.getOrDefault(token, new IntrospectionResponse(false, null, Set.of(), Instant.EPOCH));
        introspectionCache.put(token, new CachedIntrospection(fresh, now));
        return fresh;
    }

    static String validateAndHandle(Object token, Instant now, String requiredScope) {
        String subject; Set<String> scopes; Instant expiresAt; String mode;

        if (token instanceof Jwt jwt) {
            mode = "JWT (local)";
            if (!TRUSTED_ISSUER.equals(jwt.issuer()) || !signatureValid(jwt)) return "401 Unauthorized -- invalid JWT";
            subject = jwt.subject(); scopes = jwt.scopes(); expiresAt = jwt.expiresAt();
        } else {
            String opaque = (String) token;
            mode = "opaque (introspection, possibly cached)";
            IntrospectionResponse resp = introspectWithCache(opaque, now);
            if (!resp.active()) return "401 Unauthorized -- opaque token inactive";
            subject = resp.subject(); scopes = resp.scopes(); expiresAt = resp.expiresAt();
        }

        if (now.isAfter(expiresAt)) return "401 Unauthorized -- token expired";
        if (!scopes.contains(requiredScope)) return "403 Forbidden -- missing scope " + requiredScope;
        return "200 OK -- '" + subject + "' via " + mode;
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-07-13T12:00:00Z");
        Jwt jwt = new Jwt(TRUSTED_ISSUER, "bob", Set.of("orders:write"), t0.plusSeconds(300), "signed-with-key-2026-a");

        System.out.println(validateAndHandle(jwt, t0, "orders:write"));
        System.out.println(validateAndHandle("opaque-abc123", t0, "orders:read"));                       // first call: real introspection
        System.out.println(validateAndHandle("opaque-abc123", t0.plusSeconds(5), "orders:read"));         // within TTL: cache hit
        System.out.println(validateAndHandle("opaque-abc123", t0.plusSeconds(45), "orders:read"));        // past TTL: real introspection again
        System.out.println("Total REAL introspection calls: " + realIntrospectionCalls + " (out of 3 opaque validations)");
    }
}
```

How to run: `java DualModeResourceServerWithCache.java`

`validateAndHandle` accepts an `Object` and branches on whether it's a `Jwt` or a raw opaque string — a simplified stand-in for how a real Spring Security configuration picks between `.jwt(...)` and `.opaqueToken(...)` resource server modes (in practice you configure one or the other per service, or per request path, rather than truly mixing per-call, but modeling both here makes the structural contrast clear). `introspectWithCache` only calls the real introspection logic when no cached result exists or the cached result has exceeded `CACHE_TTL` — trading a bounded window of potential staleness (at most 30 seconds before a revocation is noticed) for a large reduction in network calls under sustained traffic from the same caller.

## 6. Walkthrough

Trace the three opaque-token calls in `DualModeResourceServerWithCache.main`. **First**, `validateAndHandle("opaque-abc123", t0, "orders:read")` runs. The `token instanceof Jwt` check is `false` (it's a `String`), so the opaque branch executes. `introspectWithCache("opaque-abc123", t0)` checks `introspectionCache.get("opaque-abc123")`, which is `null` (nothing cached yet) — so it proceeds to the real lookup: `realIntrospectionCalls` becomes `1`, `AUTH_SERVER_STATE.getOrDefault(...)` returns the active response for alice, and this result is stored in `introspectionCache` with `cachedAt = t0`. Back in `validateAndHandle`, `resp.active()` is `true`, `now.isAfter(expiresAt)` is `false`, and `scopes.contains("orders:read")` is `true`, so it returns success.

**Next**, `validateAndHandle("opaque-abc123", t0.plusSeconds(5), "orders:read")` runs. `introspectWithCache` now finds a cached entry with `cachedAt = t0`. `Duration.between(t0, t0+5s)` is `5` seconds, and `5s.compareTo(30s) < 0` is `true` — the cache is still fresh, so the cached `response()` is returned directly, and `realIntrospectionCalls` stays at `1`. The rest of the validation proceeds identically and succeeds.

**Then**, `validateAndHandle("opaque-abc123", t0.plusSeconds(45), "orders:read")` runs. The cached entry is still `cachedAt = t0` (nothing has refreshed it). `Duration.between(t0, t0+45s)` is `45` seconds, and `45s.compareTo(30s) < 0` is `false` — the cache has expired, so `introspectWithCache` performs a fresh lookup, incrementing `realIntrospectionCalls` to `2`, and overwrites the cache entry with `cachedAt = t0+45s`.

**Finally**, the summary line prints `realIntrospectionCalls`, showing `2` real network calls served `3` total validation requests — the cache absorbed exactly the one request that arrived well within the TTL window.

```
200 OK -- 'bob' via JWT (local)
200 OK -- 'alice' via opaque (introspection, possibly cached)
200 OK -- 'alice' via opaque (introspection, possibly cached)
200 OK -- 'alice' via opaque (introspection, possibly cached)
Total REAL introspection calls: 2 (out of 3 opaque validations)
```

Sample HTTP shape for the real introspection call Spring Security's `OpaqueTokenIntrospector` makes:

```
POST /oauth2/introspect HTTP/1.1
Authorization: Basic <order-service-client-credentials>
Content-Type: application/x-www-form-urlencoded

token=opaque-abc123

HTTP/1.1 200 OK
{"active": true, "sub": "alice", "scope": "orders:read", "exp": 1752411600}
```

## 7. Gotchas & takeaways

> Caching introspection results (Level 3) trades instant revocation for reduced load — during the cache window, a token that was just revoked by an administrator can still be accepted. This is a deliberate, bounded trade-off (choose the TTL based on how quickly your system needs to notice a revocation), not an oversight, but it's worth stating explicitly in a design review rather than discovering it during an incident postmortem, since it partially erodes the "instant revocation" property that's the whole reason opaque tokens were chosen over JWTs in the first place.

- Spring Security's OAuth2 Resource Server support handles JWT signature verification or opaque token introspection declaratively — configure `issuer-uri` for JWT or `introspection-uri` for opaque, rather than implementing either by hand.
- JWTs validate locally and fast but can't be instantly revoked; opaque tokens can be revoked instantly but require a network round-trip (optionally cached, with a bounded staleness trade-off) on every validation.
- Audience validation is not automatic in Spring Security's default JWT configuration — add a custom `OAuth2TokenValidator` if your service must reject tokens not specifically issued for it.
- Both token styles ultimately populate the same `Authentication` object consumed by `authorizeHttpRequests`, which is why they plug into the same [Spring Security core filter chain](0400-spring-security-core-filters-authentication-authorization.md) rather than requiring entirely separate authorization logic.
- The choice between JWT and opaque tokens connects directly back to [JWT structure & validation](0384-json-web-token-jwt-structure-validation.md) and [opaque tokens & token introspection](0385-opaque-tokens-token-introspection.md) — this topic is where that architectural decision becomes concrete Spring Boot configuration.
