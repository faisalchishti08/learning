---
card: spring-authorization-server
gi: 19
slug: token-generation-oauth2tokengenerator
title: "Token generation (OAuth2TokenGenerator)"
---

## 1. What it is

`OAuth2TokenGenerator<T extends OAuth2Token>` is the pluggable interface responsible for actually producing a token's value and claims once the server has decided a grant should succeed. Spring Authorization Server ships `OAuth2AccessTokenGenerator`, `OAuth2RefreshTokenGenerator`, and `JwtGenerator` (for JWT-formatted access tokens and OIDC ID tokens), and combines them via `DelegatingOAuth2TokenGenerator`, which tries each delegate in turn until one produces a token for the requested `OAuth2TokenContext`. This is the extension point for customizing exactly what goes into a token — adding custom claims, choosing JWT versus opaque format, or changing how a token's value is generated.

## 2. Why & when

The server needs to generate several different kinds of tokens (opaque access tokens, JWT access tokens, refresh tokens, ID tokens), each with a different shape, and different deployments need to customize what's *inside* a token — a resource server might need a custom `roles` claim, an internal audit system might need a custom `request_id` claim threaded through. `OAuth2TokenGenerator` exists as the seam where all of that customization plugs in, without needing to override the entire token endpoint.

Reach for a custom `OAuth2TokenGenerator` (typically by customizing `JwtGenerator`'s claims customizer, or supplying your own generator in the `DelegatingOAuth2TokenGenerator` chain) whenever:

- A resource server needs claims in the access token that aren't part of any of the standard fields — e.g. a tenant ID, a set of application-specific roles, or a feature-flag snapshot.
- Deciding between JWT and opaque access tokens per client (see the next card) — this decision is implemented by which generator actually handles a given token request.
- Needing to inject a fully custom token format for a specialized use case beyond JWT and opaque strings.

## 3. Core concept

Think of `OAuth2TokenGenerator` as a set of specialized printing presses in the same print shop, each configured to produce one kind of document. When an order comes in ("I need an access token for this context"), the shop foreman (`DelegatingOAuth2TokenGenerator`) checks each press in order — "can you print this?" — and the first press that says yes does the printing. The JWT press additionally lets you attach a "watermark customizer" that runs on every document it prints, which is exactly how custom claims get added without touching the press itself.

```java
public interface OAuth2TokenGenerator<T extends OAuth2Token> {
    T generate(OAuth2TokenContext context);
}

OAuth2TokenGenerator<?> tokenGenerator = new DelegatingOAuth2TokenGenerator(
        new JwtGenerator(jwtEncoder),          // handles JWT access tokens + ID tokens
        new OAuth2AccessTokenGenerator(),      // handles opaque access tokens
        new OAuth2RefreshTokenGenerator());    // handles refresh tokens
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DelegatingOAuth2TokenGenerator tries each generator until one handles the context">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="90" y="106" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">TokenContext</text>
  <text x="90" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(what's requested)</text>

  <rect x="220" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JwtGenerator</text>

  <rect x="220" y="87" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OAuth2AccessTokenGenerator</text>

  <rect x="220" y="154" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="290" y="182" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OAuth2RefreshTokenGenerator</text>

  <rect x="440" y="87" width="170" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="525" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">generated token</text>

  <line x1="160" y1="105" x2="215" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="360" y1="110" x2="435" y2="110" stroke="#3fb950" stroke-width="2"/>
</svg>

The context flows to each generator in turn; the first one that recognizes it produces the token.

## 5. Runnable example

The scenario: generating a JWT access token for task-tracker, then customizing its claims, then handling multiple token types through one delegating generator.

### Level 1 — Basic

```java
// TokenGeneratorDemo.java
import com.nimbusds.jose.jwk.JWKSet;
import com.nimbusds.jose.jwk.RSAKey;
import com.nimbusds.jose.jwk.source.ImmutableJWKSet;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.jwt.NimbusJwtEncoder;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.token.JwtGenerator;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenContext;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.interfaces.RSAPrivateKey;
import java.security.interfaces.RSAPublicKey;
import java.util.UUID;

public class TokenGeneratorDemo {
    public static void main(String[] args) throws Exception {
        KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("RSA");
        keyPairGenerator.initialize(2048);
        KeyPair keyPair = keyPairGenerator.generateKeyPair();
        RSAKey rsaKey = new RSAKey.Builder((RSAPublicKey) keyPair.getPublic())
                .privateKey((RSAPrivateKey) keyPair.getPrivate())
                .keyID(UUID.randomUUID().toString())
                .build();
        JwtEncoder jwtEncoder = new NimbusJwtEncoder(new ImmutableJWKSet<>(new JWKSet(rsaKey)));

        JwtGenerator jwtGenerator = new JwtGenerator(jwtEncoder);

        System.out.println("JwtGenerator created, ready to handle JWT-format contexts.");
        // A full OAuth2TokenContext requires a live authorization request in progress;
        // downstream cards (JWT vs opaque, JwtEncoder) show it invoked end to end.
    }
}
```

**How to run:** requires `nimbus-jose-jwt` and `spring-security-oauth2-jose` on the classpath (both transitive deps of the authorization server starter); run via `java TokenGeneratorDemo.java` through a build tool. Expected output:

```
JwtGenerator created, ready to handle JWT-format contexts.
```

### Level 2 — Intermediate

Task-tracker's resource server needs a custom `roles` claim in every access token so it can make authorization decisions without a separate database lookup — this is added via `JwtGenerator`'s claims customizer, which runs for every token it produces.

```java
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.JwtGenerator;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenType;

import java.util.function.Consumer;

public class TokenGeneratorDemo {

    static JwtGenerator buildCustomizedGenerator(JwtEncoder jwtEncoder) {
        JwtGenerator jwtGenerator = new JwtGenerator(jwtEncoder);

        Consumer<JwtEncodingContext> customizer = context -> {
            if (OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
                String principal = context.getPrincipal().getName();
                // in a real app this would be a lookup against a roles service/database
                context.getClaims().claim("roles", lookupRoles(principal));
            }
        };
        jwtGenerator.setJwtCustomizer(customizer);
        return jwtGenerator;
    }

    static java.util.List<String> lookupRoles(String principal) {
        return "alice".equals(principal) ? java.util.List.of("ADMIN", "USER") : java.util.List.of("USER");
    }

    public static void main(String[] args) {
        System.out.println("Roles for alice: " + lookupRoles("alice"));
        System.out.println("Roles for bob: " + lookupRoles("bob"));
    }
}
```

**How to run:** same environment as Level 1. Expected output:

```
Roles for alice: [ADMIN, USER]
Roles for bob: [USER]
```

What changed: every JWT access token minted by this generator now carries a `roles` claim computed at token-issuance time, letting the resource server authorize requests by reading the JWT directly instead of calling back to the authorization server or a database on every API call.

### Level 3 — Advanced

Production combines generators for every token type the server issues (JWT access tokens, opaque refresh tokens) into one `DelegatingOAuth2TokenGenerator`, and adds a defensive customizer that only ever adds claims — never overwrites standard ones like `scope` or `exp` — to avoid a customization bug silently corrupting token semantics.

```java
import org.springframework.security.oauth2.jwt.JwtEncoder;
import org.springframework.security.oauth2.server.authorization.token.*;

import java.util.function.Consumer;
import java.util.Set;

public class TokenGeneratorDemo {

    static final Set<String> RESERVED_CLAIMS = Set.of(
            "iss", "sub", "aud", "exp", "iat", "nbf", "jti", "scope", "client_id");

    static OAuth2TokenGenerator<?> buildProductionGenerator(JwtEncoder jwtEncoder) {
        JwtGenerator jwtGenerator = new JwtGenerator(jwtEncoder);

        Consumer<JwtEncodingContext> safeCustomizer = context -> {
            if (OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
                addClaimSafely(context, "roles", lookupRoles(context.getPrincipal().getName()));
                addClaimSafely(context, "tenant_id", lookupTenant(context.getPrincipal().getName()));
            }
        };
        jwtGenerator.setJwtCustomizer(safeCustomizer);

        OAuth2AccessTokenGenerator accessTokenGenerator = new OAuth2AccessTokenGenerator();
        OAuth2RefreshTokenGenerator refreshTokenGenerator = new OAuth2RefreshTokenGenerator();

        return new DelegatingOAuth2TokenGenerator(jwtGenerator, accessTokenGenerator, refreshTokenGenerator);
    }

    static void addClaimSafely(JwtEncodingContext context, String name, Object value) {
        if (RESERVED_CLAIMS.contains(name)) {
            throw new IllegalArgumentException("refusing to overwrite reserved claim: " + name);
        }
        context.getClaims().claim(name, value);
    }

    static java.util.List<String> lookupRoles(String principal) {
        return "alice".equals(principal) ? java.util.List.of("ADMIN", "USER") : java.util.List.of("USER");
    }

    static String lookupTenant(String principal) {
        return "acme-corp";
    }

    public static void main(String[] args) {
        try {
            addClaimSafely(null, "scope", "should-not-be-allowed");
        } catch (IllegalArgumentException e) {
            System.out.println("Blocked unsafe customization: " + e.getMessage());
        }
    }
}
```

**How to run:** same environment as Level 1 (the `null` context in `main` only exercises the guard clause before the reserved-claim check, so it runs standalone). Expected output:

```
Blocked unsafe customization: refusing to overwrite reserved claim: scope
```

What changed and why it's production-flavored: `DelegatingOAuth2TokenGenerator` now handles every token type the server issues from one place, and the reserved-claims guard is exactly the kind of defensive check that prevents a future engineer's well-intentioned customizer from accidentally clobbering `scope` or `exp` and silently breaking every downstream authorization check.

## 6. Walkthrough

Tracing token generation during a real authorization code redemption, in execution order:

1. `POST /oauth2/token` with a valid, unredeemed authorization code arrives (as in card 0017's walkthrough), and the endpoint has already validated the client and the code.
2. The endpoint builds an `OAuth2TokenContext` describing what's needed: the `RegisteredClient`, the authenticated principal, the authorized scopes, and the token type (`ACCESS_TOKEN`).
3. It calls `tokenGenerator.generate(context)` on the `DelegatingOAuth2TokenGenerator` from Level 3.
4. The delegating generator tries `JwtGenerator` first; since this client is configured for JWT access tokens (next card), it accepts the context and produces a `Jwt` — internally building standard claims (`iss`, `sub`, `aud`, `exp`, `scope`) and then running the `safeCustomizer`, which adds `roles` and `tenant_id`.
5. The endpoint separately calls `generate` again with an `OAuth2TokenType(REFRESH_TOKEN)` context; this time `JwtGenerator` declines (refresh tokens aren't JWTs here), and `OAuth2RefreshTokenGenerator` produces a random opaque string instead.
6. Both generated tokens are attached to the `OAuth2Authorization` (card 0016) and saved via the `OAuth2AuthorizationService` (card 0017).
7. The response body is `{"access_token": "eyJhbGciOi...", "refresh_token": "8xL3k9...", "token_type": "Bearer", "expires_in": 600, "scope": "tasks.read"}` — decoding the access token's payload (it's a JWT, so this is just base64) reveals the standard claims plus the custom `roles: ["ADMIN", "USER"]` and `tenant_id: "acme-corp"` claims added by the customizer.

```
OAuth2TokenContext (ACCESS_TOKEN) --> DelegatingOAuth2TokenGenerator
        |
        try JwtGenerator --accepts--> build standard claims --> run customizer --> Jwt
        
OAuth2TokenContext (REFRESH_TOKEN) --> DelegatingOAuth2TokenGenerator
        |
        try JwtGenerator --declines--> try OAuth2RefreshTokenGenerator --accepts--> opaque string
```

## 7. Gotchas & takeaways

> A JWT customizer that overwrites a standard claim like `scope` or `exp` doesn't fail loudly — it silently produces a token whose stated permissions or expiry don't match what the server actually authorized, which is a security bug that may go unnoticed until an incident. Always guard custom claim names against the standard/reserved set, as shown in Level 3.

- `DelegatingOAuth2TokenGenerator` tries generators **in the order given** and uses the first one that returns non-null — order matters if you add a custom generator that might overlap with a built-in one.
- The claims customizer receives the *entire* `JwtEncodingContext`, including the principal, the authorized scopes, and the `RegisteredClient` — anything needed to compute a custom claim is available there, so avoid separate side-channel lookups where the context already has the data.
- Refresh tokens are opaque strings by default even when access tokens are JWTs — there's rarely a reason to make a refresh token a JWT, since it's only ever presented back to the authorization server itself, never parsed by a resource server.
- Custom claims added at generation time are baked into the token permanently — if the underlying data they reflect (like `roles`) changes before the token expires, the token still carries the old value until it's refreshed.
- Test custom customizers by decoding a real generated token and asserting on its claims map directly — a customizer that silently throws or gets skipped can be easy to miss otherwise.
