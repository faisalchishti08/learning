---
card: spring-security
gi: 99
slug: oauth2-resource-server
title: "OAuth2 Resource Server"
---

## 1. What it is

Every card in this section so far has covered the **client** side of OAuth2 — an application that redirects users to log in elsewhere and obtains tokens on their behalf. `oauth2ResourceServer()` is the opposite role: it configures a `SecurityFilterChain` for an application that instead **receives** requests carrying a bearer token (typically in an `Authorization: Bearer <token>` header) issued by some other authorization server, validates that token, and — on success — treats it as proof of authentication, exactly like a session cookie would for `formLogin()`. Spring Security supports two token formats out of the box: **JWT** (`oauth2ResourceServer(oauth2 -> oauth2.jwt(...))`, validated locally using the issuer's public keys, no network call needed per-request) and **opaque tokens** (`oauth2ResourceServer(oauth2 -> oauth2.opaqueToken(...))`, validated by calling the authorization server's introspection endpoint on every request).

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/public/**").permitAll()
            .anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()));
    return http.build();
}
```
```yaml
spring:
  security:
    oauth2:
      resourceserver:
        jwt:
          issuer-uri: https://accounts.google.com   # Spring fetches signing keys from here automatically
```

## 2. Why & when

A typical microservice architecture has one service acting as an OAuth2/OIDC client (handling the user-facing login) and several other services that only ever receive already-issued tokens on incoming requests — a mobile app that got a token from your auth server calling a backend API directly, or one internal service calling another using a `client_credentials` token (card 0094). Those receiving services have no login flow of their own and no session to check; they need a fundamentally different piece of middleware whose entire job is "given a bearer token on this request, is it valid, and who/what does it represent?" That's precisely what `oauth2ResourceServer()` provides, and it's designed to compose independently of `oauth2Login()` — a single application can be a client for one flow and a resource server for its own API endpoints simultaneously.

Reach for `oauth2ResourceServer()` when:

- Building a stateless REST API that authenticates via `Authorization: Bearer <token>` rather than sessions or cookies — no `HttpSession` is created or consulted, matching typical `SessionCreationPolicy.STATELESS` configuration.
- The token was issued by a *separate* authorization server (a dedicated auth service, Okta, Auth0, Keycloak) rather than by this application itself.
- Choosing between JWT and opaque validation: JWT is self-contained and validated locally (fast, no per-request network call, but can't be revoked before its natural expiry without extra machinery), while opaque tokens require an introspection call per request (a network round trip, but supports immediate revocation since the authorization server is asked fresh each time).
- Extracting authorities from the token's claims — a `scope` or custom `roles` claim inside a JWT, mapped to Spring Security `GrantedAuthority` objects via a `JwtAuthenticationConverter`, so `@PreAuthorize` expressions can check them exactly like any other authority.

## 3. Core concept

```
Incoming request:
    GET /api/orders
    Authorization: Bearer eyJhbGciOiJSUzI1NiIs...

oauth2ResourceServer().jwt() path:
  1. extract the bearer token from the Authorization header
  2. decode the JWT's header to find which key signed it
  3. fetch (and cache) the issuer's public signing keys from its JWKS endpoint
  4. verify the SIGNATURE using the matching public key
  5. validate claims: iss (matches configured issuer-uri), exp (not expired), (aud, if configured)
  6. map claims (e.g. "scope") to GrantedAuthority objects via a JwtAuthenticationConverter
  7. build a JwtAuthenticationToken -- the Authentication for this request, held ONLY for its duration

oauth2ResourceServer().opaqueToken() path:
  1. extract the bearer token
  2. POST it to the authorization server's introspection endpoint (a NETWORK CALL, every request)
  3. authorization server responds: active=true/false, plus claims if active
  4. if active=false or the call fails -> reject with 401
  5. build an Authentication from the introspection response's claims

Both paths: NO HttpSession involved at all -- the token itself is presented on every single request.
```

Neither path is "the client side" from cards 0088–0098 — a resource server never redirects a browser anywhere; it only ever inspects a token that already arrived.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting JWT validation which decodes and verifies the token signature locally using cached public keys against opaque token validation which calls the authorization servers introspection endpoint on every request both producing an authentication object for that one request only">
  <rect x="20" y="20" width="280" height="215" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="42" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">JWT (local validation)</text>
  <rect x="40" y="58" width="240" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Bearer eyJhbGci... arrives</text>
  <line x1="160" y1="88" x2="160" y2="110" stroke="#8b949e" stroke-width="1.3" marker-end="url(#rs99)"/>
  <rect x="40" y="112" width="240" height="30" rx="5" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="131" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">verify sig w/ CACHED public key</text>
  <line x1="160" y1="142" x2="160" y2="164" stroke="#8b949e" stroke-width="1.3" marker-end="url(#rs99)"/>
  <rect x="40" y="166" width="240" height="30" rx="5" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="185" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">check iss / exp / aud</text>
  <text x="160" y="215" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">NO per-request network call</text>

  <rect x="330" y="20" width="290" height="215" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="475" y="42" fill="#79c0ff" font-size="10.5" text-anchor="middle" font-family="sans-serif">Opaque token (introspection)</text>
  <rect x="350" y="58" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="77" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Bearer opaque-abc123 arrives</text>
  <line x1="475" y1="88" x2="475" y2="110" stroke="#f0883e" stroke-width="1.3" marker-end="url(#rs99b)"/>
  <rect x="350" y="112" width="250" height="30" rx="5" fill="#161b22" stroke="#f0883e" stroke-width="1.3"/>
  <text x="475" y="131" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">POST /introspect (NETWORK CALL)</text>
  <line x1="475" y1="142" x2="475" y2="164" stroke="#8b949e" stroke-width="1.3" marker-end="url(#rs99)"/>
  <rect x="350" y="166" width="250" height="30" rx="5" fill="#161b22" stroke="#8b949e" stroke-width="1"/>
  <text x="475" y="185" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">active=true/false + claims</text>
  <text x="475" y="215" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">supports immediate revocation</text>

  <defs>
    <marker id="rs99" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="rs99b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

JWT trades a per-request network call for local, cached-key validation; opaque tokens trade that speed for revocability.

## 5. Runnable example

The scenario: model bearer-token extraction and JWT validation (signature, issuer, expiry), grow it to map a `scope` claim into `GrantedAuthority` objects, then add opaque-token introspection as an alternative path with its own network-failure handling.

### Level 1 — Basic

Extract a bearer token and validate a JWT's core claims (skipping real cryptographic signature verification for clarity — a `signature` field stands in for it).

```java
import java.util.*;

public class ResourceServerLevel1 {
    record Jwt(String signature, String issuer, long expiresAtEpochSeconds, String subject) {}

    static class JwtValidationException extends RuntimeException {
        JwtValidationException(String message) { super(message); }
    }

    static class JwtDecoder {
        private final String expectedIssuer;
        private final Set<String> trustedSignatures; // stands in for "signed by a key we trust"

        JwtDecoder(String expectedIssuer, Set<String> trustedSignatures) {
            this.expectedIssuer = expectedIssuer;
            this.trustedSignatures = trustedSignatures;
        }

        Jwt decode(Jwt token) {
            if (!trustedSignatures.contains(token.signature())) {
                throw new JwtValidationException("signature verification failed");
            }
            if (!expectedIssuer.equals(token.issuer())) {
                throw new JwtValidationException("iss mismatch: expected " + expectedIssuer + " but got " + token.issuer());
            }
            long now = System.currentTimeMillis() / 1000;
            if (now >= token.expiresAtEpochSeconds()) {
                throw new JwtValidationException("token expired");
            }
            return token; // valid -- caller can now trust its claims
        }
    }

    static String extractBearerToken(String authorizationHeader) {
        if (authorizationHeader == null || !authorizationHeader.startsWith("Bearer ")) {
            throw new JwtValidationException("missing or malformed Authorization header");
        }
        return authorizationHeader.substring("Bearer ".length());
    }

    public static void main(String[] args) {
        JwtDecoder decoder = new JwtDecoder("https://auth.example.com", Set.of("valid-sig-abc"));

        Jwt validToken = new Jwt("valid-sig-abc", "https://auth.example.com",
                System.currentTimeMillis() / 1000 + 3600, "alice");

        Jwt result = decoder.decode(validToken);
        System.out.println("validated JWT for subject: " + result.subject());
    }
}
```

**How to run:** save as `ResourceServerLevel1.java`, run `java ResourceServerLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
validated JWT for subject: alice
```

`JwtDecoder.decode` mirrors the real `NimbusJwtDecoder`'s core checks — signature trust, issuer match, expiry — in that order; here, signature verification is simulated by membership in a trusted set rather than real cryptography, but the validation *sequence* is the same one Spring Security's resource server support performs on every incoming request.

### Level 2 — Intermediate

Map a `scope` claim into `GrantedAuthority`-style strings, mirroring `JwtAuthenticationConverter`, and build the `Authentication`-equivalent object for the request.

```java
import java.util.*;

public class ResourceServerLevel2 {
    record Jwt(String signature, String issuer, long expiresAtEpochSeconds, String subject, String scope) {}
    record JwtAuthenticationToken(String subject, Set<String> authorities) {}

    static class JwtValidationException extends RuntimeException {
        JwtValidationException(String message) { super(message); }
    }

    static class JwtDecoder {
        private final String expectedIssuer;
        private final Set<String> trustedSignatures;
        JwtDecoder(String expectedIssuer, Set<String> trustedSignatures) {
            this.expectedIssuer = expectedIssuer;
            this.trustedSignatures = trustedSignatures;
        }
        Jwt decode(Jwt token) {
            if (!trustedSignatures.contains(token.signature())) throw new JwtValidationException("signature verification failed");
            if (!expectedIssuer.equals(token.issuer())) throw new JwtValidationException("iss mismatch");
            if (System.currentTimeMillis() / 1000 >= token.expiresAtEpochSeconds()) throw new JwtValidationException("token expired");
            return token;
        }
    }

    // mirrors JwtAuthenticationConverter's default behavior: split "scope" on whitespace, prefix each with SCOPE_
    static Set<String> convertScopeToAuthorities(Jwt jwt) {
        Set<String> authorities = new LinkedHashSet<>();
        if (jwt.scope() != null) {
            for (String scope : jwt.scope().split(" ")) {
                authorities.add("SCOPE_" + scope);
            }
        }
        return authorities;
    }

    static JwtAuthenticationToken authenticate(String authorizationHeader, JwtDecoder decoder) {
        String rawToken = authorizationHeader.substring("Bearer ".length());
        Jwt jwt = decoder.decode(new Jwt(rawToken, "https://auth.example.com",
                System.currentTimeMillis() / 1000 + 3600, "alice", "read:orders write:orders"));
        return new JwtAuthenticationToken(jwt.subject(), convertScopeToAuthorities(jwt));
    }

    public static void main(String[] args) {
        JwtDecoder decoder = new JwtDecoder("https://auth.example.com", Set.of("valid-sig-abc"));

        JwtAuthenticationToken authentication = authenticate("Bearer valid-sig-abc", decoder);

        System.out.println("subject: " + authentication.subject());
        System.out.println("authorities: " + new TreeSet<>(authentication.authorities()));
    }
}
```

**How to run:** save as `ResourceServerLevel2.java`, run `java ResourceServerLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
subject: alice
authorities: [SCOPE_read:orders, SCOPE_write:orders]
```

What changed: `convertScopeToAuthorities` splits the space-delimited `scope` claim and prefixes each value with `SCOPE_`, exactly mirroring `JwtAuthenticationConverter`'s default mapping — an endpoint guarded with `@PreAuthorize("hasAuthority('SCOPE_write:orders')")` would now correctly see this token as authorized, since the scope-to-authority mapping happened right here, once, at authentication time.

### Level 3 — Advanced

Add opaque-token introspection as a genuine alternative path, including its distinguishing property (revocation is checked fresh every request) and its distinguishing failure mode (the introspection call itself can fail, independent of the token's own validity).

```java
import java.util.*;

public class ResourceServerLevel3 {
    record Jwt(String signature, String issuer, long expiresAtEpochSeconds, String subject, String scope) {}
    record IntrospectionResult(boolean active, String subject, String scope) {}
    record Authentication(String subject, Set<String> authorities) {}

    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String message) { super(message); }
    }

    static class JwtDecoder {
        private final String expectedIssuer;
        private final Set<String> trustedSignatures;
        JwtDecoder(String expectedIssuer, Set<String> trustedSignatures) {
            this.expectedIssuer = expectedIssuer; this.trustedSignatures = trustedSignatures;
        }
        Jwt decode(Jwt token) {
            if (!trustedSignatures.contains(token.signature())) throw new AuthenticationException("signature verification failed");
            if (!expectedIssuer.equals(token.issuer())) throw new AuthenticationException("iss mismatch");
            if (System.currentTimeMillis() / 1000 >= token.expiresAtEpochSeconds()) throw new AuthenticationException("token expired");
            return token;
        }
    }

    // mirrors calling the authorization server's /introspect endpoint over the network, every request
    static class OpaqueTokenIntrospector {
        private final Map<String, IntrospectionResult> knownTokens = new HashMap<>();
        private final Set<String> revoked = new HashSet<>();
        private boolean simulateNetworkFailure = false;

        void register(String token, IntrospectionResult result) { knownTokens.put(token, result); }
        void revoke(String token) { revoked.add(token); }
        void simulateOutage(boolean outage) { this.simulateNetworkFailure = outage; }

        IntrospectionResult introspect(String token) {
            if (simulateNetworkFailure) throw new AuthenticationException("introspection endpoint unreachable");
            if (revoked.contains(token)) return new IntrospectionResult(false, null, null); // revoked -> inactive NOW
            return knownTokens.getOrDefault(token, new IntrospectionResult(false, null, null));
        }
    }

    static Set<String> scopeToAuthorities(String scope) {
        Set<String> authorities = new LinkedHashSet<>();
        if (scope != null) for (String s : scope.split(" ")) authorities.add("SCOPE_" + s);
        return authorities;
    }

    static Authentication authenticateWithJwt(String rawToken, JwtDecoder decoder, Jwt underlyingToken) {
        Jwt jwt = decoder.decode(underlyingToken);
        return new Authentication(jwt.subject(), scopeToAuthorities(jwt.scope()));
    }

    static Authentication authenticateWithOpaqueToken(String rawToken, OpaqueTokenIntrospector introspector) {
        IntrospectionResult result = introspector.introspect(rawToken); // NETWORK CALL, every single request
        if (!result.active()) throw new AuthenticationException("token is not active (expired, revoked, or unknown)");
        return new Authentication(result.subject(), scopeToAuthorities(result.scope()));
    }

    public static void main(String[] args) {
        OpaqueTokenIntrospector introspector = new OpaqueTokenIntrospector();
        introspector.register("opaque-bob-token", new IntrospectionResult(true, "bob", "read:orders"));

        // request #1: bob's opaque token is currently valid
        Authentication bobFirst = authenticateWithOpaqueToken("opaque-bob-token", introspector);
        System.out.println("bob request #1: " + bobFirst.subject() + " " + new TreeSet<>(bobFirst.authorities()));

        // an admin revokes bob's token -- this takes effect IMMEDIATELY, unlike a JWT which would
        // remain "valid" by signature until its own exp passes
        introspector.revoke("opaque-bob-token");

        try {
            authenticateWithOpaqueToken("opaque-bob-token", introspector);
        } catch (AuthenticationException e) {
            System.out.println("bob request #2 (after revocation): REJECTED -- " + e.getMessage());
        }

        // the introspection endpoint itself becomes unreachable -- a DIFFERENT failure mode from an inactive token
        introspector.simulateOutage(true);
        try {
            authenticateWithOpaqueToken("some-other-token", introspector);
        } catch (AuthenticationException e) {
            System.out.println("request during outage: REJECTED -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ResourceServerLevel3.java`, run `java ResourceServerLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
bob request #1: bob [SCOPE_read:orders]
bob request #2 (after revocation): REJECTED -- token is not active (expired, revoked, or unknown)
request during outage: REJECTED -- introspection endpoint unreachable
```

What changed: `authenticateWithOpaqueToken` now performs a genuine per-request lookup (`introspector.introspect`) rather than any local validation — bob's second request is rejected the instant the token is revoked, with no need to wait for a natural expiry (the property JWTs lack without extra machinery like a revocation list), while a third, unrelated request demonstrates the opaque path's distinct failure mode: if the introspection endpoint itself is unreachable, authentication fails not because the token is bad but because the *check* couldn't be performed at all — a failure category that has no equivalent in local JWT validation.

## 6. Walkthrough

Trace bob's revoked-token request (`bob request #2`) end to end, since it's the case that shows exactly why opaque tokens exist despite being slower than JWTs.

**Step 1 — the inbound request:**
```
GET /api/orders HTTP/1.1
Host: api.example.com
Authorization: Bearer opaque-bob-token
```

**Step 2 — the resource server extracts the bearer token.** `BearerTokenAuthenticationFilter` (registered by `oauth2ResourceServer().opaqueToken(...)`) pulls `"opaque-bob-token"` out of the `Authorization` header — corresponding to the literal string passed into `authenticateWithOpaqueToken`.

**Step 3 — the introspection call is made, over the network, on this specific request:**
```
POST /introspect HTTP/1.1
Host: auth.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <resource-server's own credentials>

token=opaque-bob-token
```
This corresponds to `introspector.introspect("opaque-bob-token")`. Because `revoke("opaque-bob-token")` was called between request #1 and request #2, `revoked.contains(token)` is now `true`, so the method returns `new IntrospectionResult(false, null, null)` immediately, without even checking `knownTokens`.

**Step 4 — what the real authorization server's introspection response would look like:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"active": false}
```
An inactive introspection result carries no other claims — the authorization server doesn't say *why* it's inactive (revoked vs. expired vs. never issued), only that it currently is.

**Step 5 — authentication fails.** Back in `authenticateWithOpaqueToken`, `result.active()` is `false`, so `if (!result.active())` throws `AuthenticationException("token is not active (expired, revoked, or unknown)")` before any `Authentication` object is ever constructed.

**Step 6 — the resource server responds to the original request:**
```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token", error_description="Token was not active"
```

```
JWT path (if bob had a JWT instead):
    signature check -> still passes (nothing about the KEY changed)
    iss/exp check    -> still passes (natural expiry hasn't arrived yet)
    RESULT: request would SUCCEED -- a revoked-but-unexpired JWT is, by itself, indistinguishable from a valid one

Opaque token path (what actually happened above):
    introspect() -> authorization server checked its OWN revocation state THIS INSTANT
    RESULT: request FAILS immediately, because the check happens fresh, every time
```

This contrast is precisely the trade-off from the core concept section made concrete: bob's revocation is enforced instantly only because the opaque path asks the authorization server fresh on every request — the same revocation against a JWT-based resource server would need an additional mechanism (a short token lifetime plus frequent refresh, or a distributed revocation/deny-list check) to achieve the same immediacy.

## 7. Gotchas & takeaways

> **Gotcha:** a JWT resource server validates the token entirely locally using cached public keys — it has no way to know a token was revoked before its `exp` unless additional infrastructure (a revocation list the resource server also checks, or deliberately short-lived tokens) is layered on top. Don't assume "the signature is valid" means "this token is still authorized right now" for a JWT the way it effectively does for a freshly-introspected opaque token.

- `oauth2ResourceServer()` is the opposite role from `oauth2Login()`: it receives and validates bearer tokens issued elsewhere, rather than driving a login flow — the two compose independently and can coexist in one application.
- JWT validation is local and fast (signature check against cached keys, then claim checks) with no per-request network call, but can't reflect revocation before natural expiry without extra machinery.
- Opaque token validation calls the authorization server's introspection endpoint on every single request — slower, but revocation takes effect immediately since the authorization server is asked fresh every time.
- `JwtAuthenticationConverter` (or its opaque-token equivalent) maps token claims (commonly `scope`) into `GrantedAuthority` objects at authentication time — this is what makes `@PreAuthorize("hasAuthority('SCOPE_...')")` checks work against bearer-token requests.
- Neither validation path creates or consults an `HttpSession` — the bearer token itself is the complete credential on every request, which is exactly what makes resource servers a natural fit for stateless REST APIs and inter-service calls.
