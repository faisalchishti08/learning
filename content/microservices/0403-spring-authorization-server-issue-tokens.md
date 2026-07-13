---
card: microservices
gi: 403
slug: spring-authorization-server-issue-tokens
title: "Spring Authorization Server (issue tokens)"
---

## 1. What it is

**Spring Authorization Server** is Spring's own OAuth2 / OIDC-compliant identity provider implementation — the piece that plays the *issuer* role in the flows this section has spent many topics validating and relaying. Where [Spring Security's OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md) module *validates* tokens, and [Spring Security OAuth2 Client](0402-spring-security-oauth2-client-login-token-relay.md) *obtains* tokens from someone else's identity provider, Spring Authorization Server lets you *run your own* identity provider inside a Spring Boot application — authenticating users or client applications and minting the JWTs or opaque tokens that every other service in the system then trusts.

## 2. Why & when

You reach for Spring Authorization Server when a system needs its own OAuth2/OIDC issuer rather than depending entirely on an external identity provider such as Okta or Auth0:

- **Internal or hybrid identity needs** — a company running many internal microservices sometimes wants a self-hosted authorization server for internal client-credentials tokens (service-to-service auth) even while using an external IdP for human login, or wants full control over token claims, lifetimes, and revocation behavior.
- **It's the reference implementation of the [grant types](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md) covered earlier** — authorization code, client credentials, refresh token — built and maintained by the Spring Security team, so its behavior is exactly what a Spring resource server expects without integration surprises.
- **It closes the loop for this whole section.** Every topic about validating a JWT, checking a scope, or trusting an issuer assumed *something* mints those tokens correctly in the first place; this is that something, made concrete.
- **You need this specifically when building or testing an internal OAuth2 ecosystem** — for example, a client-credentials-only authorization server issuing scoped service tokens for [service-to-service authentication](0391-service-to-service-authentication.md), or a full OIDC provider for a company's own login page.

## 3. Core concept

Think of Spring Authorization Server as a passport office rather than a border checkpoint: the border checkpoints (resource servers) never issue passports themselves, they only check the ones presented to them against a public list of what a *real* passport looks like. The passport office is the one place authorized to actually mint new passports (tokens) after verifying who's asking — a human presenting credentials, or a registered client application presenting its own client ID and secret.

The essential pieces, configured as Spring beans:

1. **`RegisteredClientRepository`** — the office's client registry: which client applications exist, what grant types they're allowed to use, what scopes they can request, and what their redirect URIs are.

```java
@Bean
public RegisteredClientRepository registeredClientRepository() {
    RegisteredClient orderService = RegisteredClient.withId(UUID.randomUUID().toString())
            .clientId("order-service")
            .clientSecret("{noop}order-service-secret")
            .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
            .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
            .scope("inventory:read")
            .tokenSettings(TokenSettings.builder().accessTokenTimeToLive(Duration.ofMinutes(10)).build())
            .build();
    return new InMemoryRegisteredClientRepository(orderService);
}
```

2. **`SecurityFilterChain` for the authorization server endpoints** — `spring-security-oauth2-authorization-server` provides `OAuth2AuthorizationServerConfigurer`, which wires up `/oauth2/authorize`, `/oauth2/token`, `/oauth2/introspect`, `/oauth2/revoke`, `/.well-known/oauth-authorization-server`, and (for OIDC) `/.well-known/openid-configuration` automatically.
3. **`JWKSource`** — the signing key material used to sign issued JWTs; resource servers fetch the corresponding public keys from the JWK Set endpoint the authorization server exposes, closing the trust loop described in [JWT structure & validation](0384-json-web-token-jwt-structure-validation.md).
4. **Token customization** — an `OAuth2TokenCustomizer<JwtEncodingContext>` bean lets you add custom claims (roles, tenant ID, internal identifiers) to issued tokens before they're signed, which is exactly the mechanism that determines what a resource server's `hasAuthority(...)` checks will see downstream.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client requests a token from the authorization server's token endpoint, the authorization server checks its registered client repository, signs a JWT using its private key, and the resource server later validates that JWT using the corresponding public key fetched from the JWK Set endpoint" font-family="sans-serif">
  <rect x="10" y="90" width="120" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="70" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">Client app</text>
  <text x="70" y="127" fill="#8b949e" font-size="8" text-anchor="middle">order-service</text>

  <rect x="250" y="30" width="180" height="110" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="340" y="50" fill="#e6edf3" font-size="10" text-anchor="middle">Spring Authorization Server</text>
  <text x="340" y="68" fill="#8b949e" font-size="8" text-anchor="middle">RegisteredClientRepository</text>
  <text x="340" y="82" fill="#8b949e" font-size="8" text-anchor="middle">/oauth2/token</text>
  <text x="340" y="96" fill="#8b949e" font-size="8" text-anchor="middle">signs with private key</text>
  <text x="340" y="110" fill="#8b949e" font-size="8" text-anchor="middle">/oauth2/jwks (public keys)</text>

  <rect x="500" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="575" y="112" fill="#e6edf3" font-size="10" text-anchor="middle">Resource server</text>
  <text x="575" y="127" fill="#8b949e" font-size="8" text-anchor="middle">validates via JWK Set</text>

  <line x1="130" y1="105" x2="250" y2="90" stroke="#8b949e" marker-end="url(#as)"/>
  <text x="190" y="80" fill="#8b949e" font-size="8" text-anchor="middle">client_credentials</text>
  <line x1="250" y1="115" x2="130" y2="130" stroke="#6db33f" marker-end="url(#as)"/>
  <text x="190" y="150" fill="#6db33f" font-size="8" text-anchor="middle">signed JWT</text>

  <line x1="130" y1="120" x2="500" y2="115" stroke="#79c0ff" stroke-dasharray="3,2" marker-end="url(#as)"/>
  <text x="330" y="175" fill="#79c0ff" font-size="8" text-anchor="middle">bearer token presented downstream</text>
  <line x1="430" y1="90" x2="500" y2="115" stroke="#8b949e" stroke-dasharray="2,2" marker-end="url(#as)"/>
  <text x="480" y="70" fill="#8b949e" font-size="8" text-anchor="middle">fetches JWK Set once, caches</text>

  <defs>
    <marker id="as" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

The authorization server signs tokens with a private key it alone holds; resource servers verify with the matching public key it publishes, so trust flows one direction without either side sharing secrets.

## 5. Runnable example

Scenario: a small internal authorization server issuing client-credentials tokens for `inventory-service`. We build client-credential validation and token minting first, then add scope enforcement per registered client, then add signed-JWT issuance with a JWK-style key pair so a downstream resource server can verify authenticity without ever talking to the authorization server directly.

### Level 1 — Basic

```java
// File: ClientCredentialsTokenEndpoint.java -- the simplest possible token
// endpoint: verify a registered client's id/secret, then issue an opaque
// access token. Mirrors POST /oauth2/token with grant_type=client_credentials.
import java.util.*;

public class ClientCredentialsTokenEndpoint {
    record RegisteredClient(String clientId, String clientSecret, Set<String> allowedScopes) {}

    static final Map<String, RegisteredClient> REGISTERED_CLIENTS = Map.of(
            "inventory-service", new RegisteredClient("inventory-service", "secret-1", Set.of("orders:read"))
    );

    static String issueToken(String clientId, String clientSecret) {
        RegisteredClient client = REGISTERED_CLIENTS.get(clientId);
        if (client == null || !client.clientSecret().equals(clientSecret)) {
            return "401 Unauthorized -- invalid_client";
        }
        String token = "token-for-" + clientId + "-" + UUID.randomUUID().toString().substring(0, 8);
        System.out.println("[AuthServer] issued token '" + token + "' to '" + clientId + "'");
        return token;
    }

    public static void main(String[] args) {
        System.out.println(issueToken("inventory-service", "secret-1"));
        System.out.println(issueToken("inventory-service", "wrong-secret"));
    }
}
```

How to run: `java ClientCredentialsTokenEndpoint.java`

`issueToken` mirrors the minimum a token endpoint must do: authenticate the *client* (not a human — client credentials is a machine-to-machine grant) against the `RegisteredClientRepository`, then mint a token. A wrong secret is rejected with `invalid_client`, exactly the error code the real OAuth2 spec (and Spring Authorization Server) returns for a failed client authentication attempt.

### Level 2 — Intermediate

```java
// File: TokenEndpointWithScopeEnforcement.java -- the SAME token endpoint,
// now enforcing that a client can only be issued scopes it's registered
// for -- mirroring RegisteredClient.scope(...) constraining what a real
// Spring Authorization Server will ever put in an access token.
import java.util.*;

public class TokenEndpointWithScopeEnforcement {
    record RegisteredClient(String clientId, String clientSecret, Set<String> allowedScopes) {}
    record TokenResponse(String accessToken, Set<String> grantedScopes) {}

    static final Map<String, RegisteredClient> REGISTERED_CLIENTS = Map.of(
            "inventory-service", new RegisteredClient("inventory-service", "secret-1", Set.of("orders:read")),
            "billing-service", new RegisteredClient("billing-service", "secret-2", Set.of("orders:read", "orders:write"))
    );

    static Object issueToken(String clientId, String clientSecret, Set<String> requestedScopes) {
        RegisteredClient client = REGISTERED_CLIENTS.get(clientId);
        if (client == null || !client.clientSecret().equals(clientSecret)) {
            return "401 Unauthorized -- invalid_client";
        }
        // Never grant more than the client is registered for, even if it asks.
        Set<String> grantedScopes = new HashSet<>(requestedScopes);
        grantedScopes.retainAll(client.allowedScopes());
        if (grantedScopes.isEmpty()) {
            return "400 Bad Request -- invalid_scope, none of " + requestedScopes + " are permitted for " + clientId;
        }
        String token = "token-for-" + clientId;
        System.out.println("[AuthServer] '" + clientId + "' requested " + requestedScopes + ", granted " + grantedScopes);
        return new TokenResponse(token, grantedScopes);
    }

    public static void main(String[] args) {
        System.out.println(issueToken("inventory-service", "secret-1", Set.of("orders:read", "orders:write")));
        System.out.println(issueToken("inventory-service", "secret-1", Set.of("orders:write")));
    }
}
```

How to run: `java TokenEndpointWithScopeEnforcement.java`

`issueToken` now intersects the *requested* scopes against the client's *registered* `allowedScopes`, so `inventory-service` asking for `orders:write` (which it was never registered for) is silently narrowed down to just `orders:read` in the first call, and rejected outright in the second call where nothing overlaps. This mirrors how Spring Authorization Server treats `RegisteredClient.scope(...)` as a hard ceiling — a compromised or misconfigured client can never talk its way into a broader scope than an administrator registered for it, regardless of what it requests.

### Level 3 — Advanced

```java
// File: JwtIssuingAuthorizationServer.java -- issues a SIGNED JWT (not an
// opaque string) using a simulated private-key signature, and exposes a
// JWK-style public key lookup so a downstream resource server can verify
// the token WITHOUT calling back to the authorization server -- mirroring
// Spring Authorization Server's JWKSource and the real /oauth2/jwks endpoint.
import java.time.*;
import java.util.*;

public class JwtIssuingAuthorizationServer {
    record RegisteredClient(String clientId, String clientSecret, Set<String> allowedScopes) {}
    record Jwt(String issuer, String subject, Set<String> scopes, Instant issuedAt, Instant expiresAt, String signature) {}

    static final String ISSUER = "https://auth.internal.example.com";
    static final String SIGNING_KEY_ID = "key-2026-a"; // private key held ONLY by the authorization server
    static final Map<String, RegisteredClient> REGISTERED_CLIENTS = Map.of(
            "inventory-service", new RegisteredClient("inventory-service", "secret-1", Set.of("orders:read"))
    );

    // Stand-in for signing with the authorization server's private key.
    static String sign(String clientId, Set<String> scopes, Instant issuedAt) {
        return "sig(" + SIGNING_KEY_ID + ":" + clientId + ":" + scopes + ":" + issuedAt + ")";
    }

    static Object issueJwt(String clientId, String clientSecret, Set<String> requestedScopes, Instant now) {
        RegisteredClient client = REGISTERED_CLIENTS.get(clientId);
        if (client == null || !client.clientSecret().equals(clientSecret)) return "401 Unauthorized -- invalid_client";

        Set<String> grantedScopes = new HashSet<>(requestedScopes);
        grantedScopes.retainAll(client.allowedScopes());
        if (grantedScopes.isEmpty()) return "400 Bad Request -- invalid_scope";

        Instant expiresAt = now.plusSeconds(600);
        String signature = sign(clientId, grantedScopes, now);
        Jwt jwt = new Jwt(ISSUER, clientId, grantedScopes, now, expiresAt, signature);
        System.out.println("[AuthServer] issued JWT for '" + clientId + "': " + jwt);
        return jwt;
    }

    // Stand-in for the /oauth2/jwks endpoint: a resource server fetches THIS, once, and caches it.
    static boolean verifySignatureUsingPublicKey(Jwt jwt) {
        // Re-derive what a valid signature for these exact claims would look like, using the
        // PUBLIC half of the key pair -- the resource server never sees the private key itself.
        String expected = sign(jwt.subject(), jwt.scopes(), jwt.issuedAt());
        return expected.equals(jwt.signature());
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-07-13T12:00:00Z");
        Object result = issueJwt("inventory-service", "secret-1", Set.of("orders:read"), now);
        System.out.println("Issued: " + result);

        if (result instanceof Jwt jwt) {
            boolean valid = verifySignatureUsingPublicKey(jwt);
            System.out.println("[ResourceServer] signature valid (via public key, no callback to AuthServer): " + valid);

            // Tamper with the token in transit -- a resource server must catch this.
            Jwt tampered = new Jwt(jwt.issuer(), jwt.subject(), Set.of("orders:write"), jwt.issuedAt(), jwt.expiresAt(), jwt.signature());
            System.out.println("[ResourceServer] tampered-scope token signature valid: " + verifySignatureUsingPublicKey(tampered));
        }
    }
}
```

How to run: `java JwtIssuingAuthorizationServer.java`

`issueJwt` performs the same client authentication and scope-narrowing as Level 2, but now produces a structured `Jwt` record with a `signature` computed from the token's own claims using the (simulated) authorization server's private key. `verifySignatureUsingPublicKey` stands in for what a resource server does after fetching the authorization server's JWK Set once at startup: it recomputes what a valid signature *should* look like for the claims actually present in the token, using only public key material, and compares. The legitimate token verifies successfully. The tampered token — where `scopes` was changed from `orders:read` to `orders:write` after signing — fails verification, because the recomputed signature no longer matches, demonstrating exactly why a resource server can trust a JWT's claims without a network round-trip: any tampering breaks the signature check.

## 6. Walkthrough

Trace `JwtIssuingAuthorizationServer.main`. **First**, `issueJwt("inventory-service", "secret-1", Set.of("orders:read"), now)` runs. `REGISTERED_CLIENTS.get("inventory-service")` finds the client, and its secret matches, so authentication passes. `grantedScopes` intersects `{"orders:read"}` with the client's `allowedScopes` (`{"orders:read"}`), leaving `{"orders:read"}` — non-empty, so scope validation passes too. `expiresAt` is set to `now + 600s`, and `sign("inventory-service", {"orders:read"}, now)` produces a signature string encoding exactly those claims. A `Jwt` record is built and printed.

**Next**, back in `main`, the result is confirmed to be a `Jwt` via pattern matching (`result instanceof Jwt jwt`), and `verifySignatureUsingPublicKey(jwt)` is called. Inside, `sign(jwt.subject(), jwt.scopes(), jwt.issuedAt())` recomputes the expected signature using the *same* claims the token currently carries — `"inventory-service"`, `{"orders:read"}`, and the original `issuedAt`. Since nothing has changed, this recomputed value equals `jwt.signature()` exactly, so verification returns `true`.

**Then**, `tampered` is constructed by copying `jwt` but swapping `scopes` from `{"orders:read"}` to `{"orders:write"}` — simulating an attacker intercepting the token and rewriting its claims, while leaving the original `signature` field untouched (an attacker without the private key cannot produce a new valid signature for the new claims).

**Finally**, `verifySignatureUsingPublicKey(tampered)` recomputes the expected signature using the *tampered* scopes (`{"orders:write"}`), which produces a different string than the original `signature` still attached to the token — so the comparison fails and verification correctly returns `false`, exactly the protection a real JWT signature check provides.

```
[AuthServer] issued JWT for 'inventory-service': Jwt[issuer=https://auth.internal.example.com, subject=inventory-service, scopes=[orders:read], issuedAt=2026-07-13T12:00:00Z, expiresAt=2026-07-13T12:10:00Z, signature=sig(key-2026-a:inventory-service:[orders:read]:2026-07-13T12:00:00Z)]
Issued: Jwt[...]
[ResourceServer] signature valid (via public key, no callback to AuthServer): true
[ResourceServer] tampered-scope token signature valid: false
```

Sample HTTP shape for the real `client_credentials` exchange against Spring Authorization Server:

```
POST /oauth2/token HTTP/1.1
Authorization: Basic aW52ZW50b3J5LXNlcnZpY2U6c2VjcmV0LTE=
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&scope=orders:read

HTTP/1.1 200 OK
{"access_token": "eyJhbGciOiJSUzI1NiJ9...", "token_type": "Bearer", "expires_in": 600, "scope": "orders:read"}
```

## 7. Gotchas & takeaways

> Rotating the authorization server's signing key without a transition period breaks every resource server that cached the old JWK Set — Spring Authorization Server (and any well-behaved resource server) supports publishing multiple active keys with `kid` (key ID) claims specifically to allow overlapping rotation, but this only works if resource servers actually refresh their cached key set periodically rather than fetching it once at startup and never again.

- Spring Authorization Server plays the *issuer* role: it authenticates clients or users and mints tokens, the exact counterpart to the *validating* role covered in [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md).
- `RegisteredClient.scope(...)` is a hard ceiling on what a client can ever be granted, regardless of what it requests — always narrow requested scopes to the registered allow-list, never trust the request alone.
- Signed JWTs let resource servers verify tokens using only public key material, with no network call back to the authorization server on every request — this is the mechanism [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md)'s JWT mode relies on.
- Client-credentials grants (machine-to-machine) authenticate the *client application*, not a human — don't confuse this with the authorization-code login flow covered in [Spring Security OAuth2 Client](0402-spring-security-oauth2-client-login-token-relay.md), which authenticates a user.
- Running your own authorization server means you own key rotation, client registration, and token revocation policy — decide deliberately whether that operational burden is worth it versus using an established external identity provider.
