---
card: spring-authorization-server
gi: 20
slug: jwt-vs-opaque-access-tokens
title: "JWT vs opaque access tokens"
---

## 1. What it is

An access token can be issued in one of two formats. A **JWT access token** is a self-contained, signed JSON payload — the resource server can verify its signature and read its claims (`scope`, `exp`, `sub`, custom claims) directly, without calling back to the authorization server. An **opaque access token** is just a random string with no embedded meaning — the resource server must call the authorization server's introspection endpoint (`POST /oauth2/introspect`) to find out anything about it (whether it's valid, who it belongs to, what scopes it carries). Spring Authorization Server supports both, chosen per `RegisteredClient` via `TokenSettings.builder().accessTokenFormat(...)`.

## 2. Why & when

This is a genuine architectural tradeoff, not a matter of taste. Reach for:

- **JWT access tokens** when resource servers need to validate tokens fast and locally — microservices architectures with many resource servers and high request volume benefit enormously from not needing a network round trip to the authorization server on every single API call.
- **Opaque access tokens** when you need the ability to instantly revoke a token and have that revocation take effect everywhere immediately. A JWT is valid until it expires, full stop — there's no way to "unsign" one that's already out in the wild, so revoking it before expiry requires additional infrastructure (a deny-list) that opaque tokens get for free, since introspection simply stops returning "active" once the authorization server's own record is revoked.
- **Opaque tokens** also when the claims a resource server needs are sensitive or change too frequently to bake into a token that might live for many minutes — introspection always reflects current, live state.

Many real systems use both: JWTs for internal service-to-service calls where low-latency local validation matters most, and opaque tokens (or short-lived JWTs) for anything facing a less trusted or higher-risk audience.

## 3. Core concept

A JWT access token is like a **notarized, tamper-evident letter of introduction** you carry with you — anyone who receives it can check the notary's seal (signature) themselves and trust what it says, without phoning the notary. An opaque access token is like a **coat-check ticket** — the ticket itself means nothing; the coat-check counter (introspection endpoint) is the only place that can tell you what it corresponds to, and if the counter later decides to void a ticket, it stops honoring it instantly, no matter who's holding it.

```java
TokenSettings jwtTokens = TokenSettings.builder()
        .accessTokenFormat(OAuth2TokenFormat.SELF_CONTAINED) // JWT
        .build();

TokenSettings opaqueTokens = TokenSettings.builder()
        .accessTokenFormat(OAuth2TokenFormat.REFERENCE) // opaque
        .build();
```

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JWT access tokens are validated locally; opaque tokens require an introspection call">
  <rect x="20" y="20" width="280" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">JWT access token</text>
  <text x="160" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Resource server verifies</text>
  <text x="160" y="88" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">signature + reads claims locally</text>
  <text x="160" y="106" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">no network call needed</text>

  <rect x="340" y="20" width="280" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="45" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Opaque access token</text>
  <text x="480" y="70" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Resource server calls</text>
  <text x="480" y="88" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">POST /oauth2/introspect</text>
  <text x="480" y="106" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">network call every time</text>

  <rect x="180" y="170" width="280" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="195" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Instant revocation before expiry?</text>
  <text x="320" y="215" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">JWT: hard (needs deny-list)</text>
  <text x="320" y="230" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">Opaque: yes, built in</text>
</svg>

The tradeoff is speed-and-independence versus instant, centralized control.

## 5. Runnable example

The scenario: configuring task-tracker's access token format, starting with JWT for speed, then showing the introspection alternative, then combining both formats for different clients in the same server.

### Level 1 — Basic

```java
// TokenFormatDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.OAuth2TokenFormat;
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;

import java.util.UUID;

public class TokenFormatDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .tokenSettings(TokenSettings.builder()
                        .accessTokenFormat(OAuth2TokenFormat.SELF_CONTAINED)
                        .build())
                .build();

        System.out.println("Access token format: " + client.getTokenSettings().getAccessTokenFormat().getValue());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java TokenFormatDemo.java`. Expected output:

```
Access token format: self-contained
```

`task-tracker`'s resource server can now decode and verify tokens locally, without calling back to the authorization server.

### Level 2 — Intermediate

A second, more sensitive integration — a payments microservice — chooses opaque tokens instead, so access can be revoked instantly (e.g. the moment a suspicious transaction is detected) rather than waiting out a token's remaining lifetime.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.OAuth2TokenFormat;
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;

import java.time.Duration;
import java.util.UUID;

public class TokenFormatDemo {
    public static void main(String[] args) {
        RegisteredClient paymentsClient = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("payments-service")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
                .scope("payments.charge")
                .tokenSettings(TokenSettings.builder()
                        .accessTokenFormat(OAuth2TokenFormat.REFERENCE) // opaque
                        .accessTokenTimeToLive(Duration.ofMinutes(5))    // short-lived, on top of revocability
                        .build())
                .build();

        System.out.println("Payments token format: " + paymentsClient.getTokenSettings().getAccessTokenFormat().getValue());
        System.out.println("Payments token TTL: " + paymentsClient.getTokenSettings().getAccessTokenTimeToLive());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Payments token format: reference
Payments token TTL: PT5M
```

What changed: this client's tokens now carry no information at all by themselves — every use requires the payments microservice to call the authorization server's introspection endpoint, which means an operator can revoke the underlying `OAuth2Authorization` (card 0016/0017) and every future introspection call immediately reports the token as inactive, even though its stated expiry hasn't arrived yet.

### Level 3 — Advanced

Production runs both formats side by side on the same authorization server, and the resource server for the opaque-token client is configured with `OpaqueTokenIntrospector` to make the introspection call correctly, including handling the case where introspection reports the token as inactive.

```java
import org.springframework.security.oauth2.server.resource.introspection.NimbusOpaqueTokenIntrospector;
import org.springframework.security.oauth2.server.resource.introspection.OAuth2IntrospectionAuthenticatedPrincipal;
import org.springframework.security.oauth2.server.resource.introspection.OpaqueTokenIntrospector;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;

public class ResourceServerIntrospectionDemo {

    public static void main(String[] args) {
        // In a real Spring Boot resource server this is normally auto-configured from
        // spring.security.oauth2.resourceserver.opaquetoken.* properties; shown explicitly here.
        OpaqueTokenIntrospector introspector = new NimbusOpaqueTokenIntrospector(
                "https://auth.example.com/oauth2/introspect",
                "payments-service", // the resource server's own client credentials for introspection
                "resource-server-secret");

        String incomingToken = "8xL3k9-opaque-token-value";
        try {
            OAuth2IntrospectionAuthenticatedPrincipal principal =
                    (OAuth2IntrospectionAuthenticatedPrincipal) introspector.introspect(incomingToken);
            System.out.println("Token active for: " + principal.getName()
                    + ", scopes=" + principal.getAttributes().get("scope"));
        } catch (OAuth2AuthenticationException ex) {
            OAuth2Error error = ex.getError();
            System.out.println("Token rejected: " + error.getErrorCode() + " - " + error.getDescription());
        }
    }
}
```

**How to run:** this requires a live authorization server reachable at the introspection URL; in a real Spring Boot resource server it's wired automatically from configuration properties rather than constructed by hand. Expected behavior: a valid, active token prints the principal name and scopes; an expired or revoked token causes `introspect` to throw `OAuth2AuthenticationException`, which the resource server's security filter chain turns into a `401 Unauthorized` response.

What changed and why it's production-flavored: this is the actual mechanism that makes opaque tokens' instant-revocation property real — the resource server doesn't just trust a locally-cached decision, it asks the authorization server fresh on (essentially) every request, and correctly propagates a revoked/expired result as an authentication failure rather than silently allowing the request through.

## 6. Walkthrough

Tracing a request through each format side by side, in execution order:

**JWT path (task-tracker, from Level 1):**
1. Task-tracker's resource server receives `GET /api/tasks` with `Authorization: Bearer eyJhbGciOi...`.
2. It decodes the JWT locally using a `JwtDecoder` configured with the authorization server's public key (fetched once and cached from its JWK Set endpoint — no request-time network call).
3. It checks the signature, `exp`, and `scope` claims, all from the token itself, and — if valid — proceeds to serve the request. Total added latency: local CPU only.

**Opaque path (payments-service, from Level 2/3):**
1. The payments resource server receives `POST /api/charge` with `Authorization: Bearer 8xL3k9-opaque-token-value`.
2. It calls `introspector.introspect(token)`, which sends `POST /oauth2/introspect` with `token=8xL3k9-opaque-token-value` to the authorization server, authenticating itself as a registered introspection client.
3. The authorization server looks up the `OAuth2Authorization` by this token value (card 0017's `findByToken`), checks `isActive()`, and responds with a JSON body: `{"active": true, "scope": "payments.charge", "sub": "alice", "exp": 1752312345}` — or, if the token has been revoked or expired, simply `{"active": false}`.
4. The resource server treats an `active: false` response identically to an invalid token — `401 Unauthorized` — regardless of what the token's stated expiry claims.

```
JWT path:   Bearer <jwt>  --local signature+claims check-->  allow/deny  (no network call)
Opaque path: Bearer <opaque> --POST /oauth2/introspect--> {"active": true/false, ...} --> allow/deny
```

## 7. Gotchas & takeaways

> Revoking a JWT access token before its stated `exp` is not something the token format supports on its own — if instant revocation is a hard requirement (e.g. for a compromised-account response), either use opaque tokens for that client, or layer a separate revocation deny-list that every resource server checks in addition to the JWT's own validity.

- Introspection calls add real latency and load to the authorization server — for high-traffic resource servers, opaque tokens trade per-request cost for revocation control; this is a genuine capacity-planning consideration, not a minor detail.
- JWT access tokens are larger than opaque tokens (they carry their claims in plaintext, base64-encoded) — this matters if tokens are passed through systems with header size limits.
- Mixing formats per client (as in Level 3) is entirely normal — there's no requirement that every client on one authorization server use the same format.
- Introspection endpoint access itself must be authenticated (the resource server needs its own client credentials to call `/oauth2/introspect`) — don't leave it open, since it can reveal information about arbitrary tokens to whoever can call it.
- A short `accessTokenTimeToLive` (Level 2) partially compensates for a JWT's lack of instant revocability — it's common to pair self-contained JWTs with shorter lifetimes than opaque tokens, specifically to shrink the exposure window.
