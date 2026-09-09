---
card: system-design
gi: 183
slug: spring-security-resource-server-jwt
title: Spring Security resource server (JWT)
---

## 1. What it is

Spring Security's **OAuth2 Resource Server** support lets a Spring Boot application validate incoming [JWT](0177-jwt-structure-validation.md) access tokens on every request automatically, without you hand-writing signature verification, expiry checking, or claims parsing. Configuring `spring-boot-starter-oauth2-resource-server` and pointing it at the issuer's public key (or JWKS endpoint) is enough for Spring Security to reject invalid or expired tokens before your controller code ever runs, and to expose the token's claims (like the user's roles) to your authorization logic.

## 2. Why & when

Hand-implementing JWT validation correctly — checking the signature against the right key, verifying `exp`, `iss`, and `aud` claims, and rejecting a token signed with an unexpected algorithm — is easy to get subtly wrong, and every mistake is a real security hole. Spring Security's resource server support centralizes this into well-tested, declarative configuration, so every protected endpoint automatically benefits from correct validation. Use it in any Spring Boot service that accepts bearer tokens (typically issued by an [OAuth2/OIDC](0176-oauth2-openid-connect.md) authorization server) and needs to authorize requests based on the validated token's claims.

## 3. Core concept

- **`spring-boot-starter-oauth2-resource-server`:** the dependency that adds a security filter validating the `Authorization: Bearer <token>` header on every incoming request.
- **`spring.security.oauth2.resourceserver.jwt.issuer-uri` (or `jwk-set-uri`):** configuration pointing Spring Security at the authorization server's public signing keys, so it can verify token signatures without a hardcoded secret.
- **Automatic validation:** signature verification, expiry (`exp`), and (if configured) issuer (`iss`) and audience (`aud`) checks all happen automatically in the security filter chain, before any controller method runs.
- **`@PreAuthorize` and `SecurityContext`:** once a token is validated, its claims (e.g. `scope` or a custom `roles` claim) are available for method-level authorization checks, such as `@PreAuthorize("hasAuthority('SCOPE_read')")`.
- **Custom claim-to-authority mapping:** by default Spring maps a JWT's `scope`/`scp` claim to Spring Security authorities prefixed with `SCOPE_`; a `JwtAuthenticationConverter` bean lets you customize this mapping for custom claims (like a `roles` array).

## 4. Diagram

```
   request: GET /api/orders
   Authorization: Bearer eyJhbGciOiJSUzI1NiJ9...

        |
        v
   Spring Security filter chain
        |
        |-- fetch issuer's public keys (cached) from jwk-set-uri
        |-- verify signature against public key
        |-- check exp, iss, aud claims
        |-- FAIL any check -> 401 Unauthorized, controller never runs
        |
        v (all checks pass)
   SecurityContext populated with validated claims (scope, sub, etc.)
        |
        v
   @PreAuthorize("hasAuthority('SCOPE_read')") checked against the token's scope
        |
        v
   controller method runs, with access to the authenticated principal
```
*Caption: validation happens entirely in the security filter chain, before the controller; only a token that passes every check ever reaches your business logic.*

## 5. Runnable example

This models the resource-server validation and scope-based authorization pipeline in-process; the "How to run" note shows the real Spring configuration.

**Level 1 — Basic.** Validate a JWT's signature and expiry, modeling the automatic filter-chain checks.

**Level 2 — Extract and map claims to authorities.** Convert a `scope` claim into Spring-Security-style authorities.

**Level 3 — Method-level authorization via `@PreAuthorize`-style scope checking.** Reject a request whose token lacks the required scope, before the "controller" logic runs.

```java
// ResourceServerDemo.java
import java.util.*;

public class ResourceServerDemo {

    static final String SIGNING_SECRET = "issuer-secret-key"; // stands in for the issuer's public key

    static class ValidatedJwt {
        final String subject;
        final Set<String> scopes;
        ValidatedJwt(String subject, Set<String> scopes) { this.subject = subject; this.scopes = scopes; }
    }

    // Level 1: the security filter chain's automatic validation - signature and expiry.
    static ValidatedJwt validateAndParse(String token, long nowEpochSeconds) {
        String[] parts = token.split("\\.");
        String claims = parts[0], signature = parts[1];
        String expectedSignature = Integer.toHexString((claims + SIGNING_SECRET).hashCode());
        if (!expectedSignature.equals(signature)) {
            throw new SecurityException("401 Unauthorized: invalid signature");
        }
        Map<String, String> parsedClaims = parseClaims(claims);
        long exp = Long.parseLong(parsedClaims.get("exp"));
        if (nowEpochSeconds >= exp) {
            throw new SecurityException("401 Unauthorized: token expired");
        }
        // Level 2: map the "scope" claim to a set of authorities, mirroring Spring's SCOPE_ prefix convention.
        Set<String> scopeAuthorities = new HashSet<>();
        for (String scope : parsedClaims.get("scope").split(" ")) scopeAuthorities.add("SCOPE_" + scope);
        return new ValidatedJwt(parsedClaims.get("sub"), scopeAuthorities);
    }

    static Map<String, String> parseClaims(String claimsJson) {
        Map<String, String> result = new HashMap<>();
        for (String field : claimsJson.replaceAll("[{}\"]", "").split(",")) {
            String[] kv = field.split(":", 2);
            result.put(kv[0], kv[1]);
        }
        return result;
    }

    static String issueToken(String subject, String scope, long expEpochSeconds) {
        String claims = "{sub:" + subject + ",scope:" + scope + ",exp:" + expEpochSeconds + "}";
        String signature = Integer.toHexString((claims + SIGNING_SECRET).hashCode());
        return claims + "." + signature;
    }

    // Level 3: @PreAuthorize("hasAuthority('SCOPE_read')")-style method-level check, BEFORE controller logic runs.
    static void requireAuthority(ValidatedJwt jwt, String requiredAuthority) {
        if (!jwt.scopes.contains(requiredAuthority)) {
            throw new SecurityException("403 Forbidden: missing authority " + requiredAuthority);
        }
    }

    static String getOrdersController(String token, long now) {
        ValidatedJwt jwt = validateAndParse(token, now); // Spring Security's filter chain, automatically
        requireAuthority(jwt, "SCOPE_orders.read");      // @PreAuthorize, checked before this line's "business logic"
        return "orders for " + jwt.subject + ": [order-1, order-2]";
    }

    public static void main(String[] args) {
        long now = 1_700_000_000L;
        String validToken = issueToken("user-17", "orders.read profile", now + 3600);
        String noScopeToken = issueToken("user-42", "profile", now + 3600);
        String expiredToken = issueToken("user-17", "orders.read", now - 10);

        System.out.println("valid token with correct scope: " + getOrdersController(validToken, now));

        try {
            getOrdersController(noScopeToken, now);
        } catch (SecurityException e) {
            System.out.println("token missing required scope: " + e.getMessage());
        }

        try {
            getOrdersController(expiredToken, now);
        } catch (SecurityException e) {
            System.out.println("expired token: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ResourceServerDemo.java`, then run `java ResourceServerDemo.java`. (Real Spring Boot: add `spring-boot-starter-oauth2-resource-server`, set `spring.security.oauth2.resourceserver.jwt.issuer-uri=https://your-auth-server`, and annotate a controller method with `@PreAuthorize("hasAuthority('SCOPE_orders.read')")` — Spring Security handles the signature/expiry validation and the scope check entirely through configuration.)

## 6. Walkthrough

1. `getOrdersController(validToken, now)` calls `validateAndParse`, which recomputes the expected signature from the token's claims and `SIGNING_SECRET`, finds it matches, checks `exp` against `now` (not yet expired), and returns a `ValidatedJwt` with `scopes = {"SCOPE_orders.read", "SCOPE_profile"}`.
2. `requireAuthority(jwt, "SCOPE_orders.read")` checks whether that set contains the required authority — it does, so no exception is thrown, and the method proceeds to return the "orders" result, modeling a controller method whose `@PreAuthorize` check passed.
3. `getOrdersController(noScopeToken, now)` validates successfully (signature and expiry both pass), producing a `ValidatedJwt` with `scopes = {"SCOPE_profile"}` only; `requireAuthority` then checks for `"SCOPE_orders.read"`, does not find it, and throws a `SecurityException` with a `403 Forbidden` message — critically, this happens *after* successful authentication but *before* any "business logic" runs, exactly modeling `@PreAuthorize`'s position in the request pipeline.
4. `getOrdersController(expiredToken, now)` calls `validateAndParse`, which finds the signature is valid but then checks `nowEpochSeconds (now) >= exp (now - 10)`, which is true, so it throws a `SecurityException` with a `401 Unauthorized` message — this failure happens even earlier, during what models the security filter chain itself, before the method-level authorization check is ever reached.
5. Both exceptions are caught in `main` and printed, showing the two distinct failure points a real Spring Security resource server enforces: token validity (filter chain, `401`) and sufficient authorization (`@PreAuthorize`, `403`) — exactly mirroring the [authentication vs authorization](0174-authentication-vs-authorization.md) distinction.

## 7. Gotchas & takeaways

> Gotcha: forgetting to configure `issuer-uri` or `jwk-set-uri` correctly (or pointing it at the wrong authorization server) means Spring Security cannot fetch the correct public keys to verify signatures, causing every legitimate token to fail validation — always verify this configuration matches the actual authorization server issuing your tokens, especially across different environments (dev, staging, production often use different issuers).

- Spring Security's resource server support centralizes JWT signature and expiry validation into tested, declarative configuration, run automatically in the filter chain.
- The `scope`/`scp` claim maps to `SCOPE_`-prefixed authorities by default, which `@PreAuthorize` expressions check against.
- Authentication (is the token valid) and authorization (does it have the right scope) fail with different status codes and at different points in the request pipeline.
- Related concepts: [JWT structure & validation](0177-jwt-structure-validation.md) (the format and checks this configuration automates), [OAuth2 & OpenID Connect](0176-oauth2-openid-connect.md) (the protocol issuing the tokens this resource server validates), [Spring Authorization Server (OAuth2 provider)](0184-spring-authorization-server-oauth2-provider.md) (the Spring component that would actually issue these tokens).
