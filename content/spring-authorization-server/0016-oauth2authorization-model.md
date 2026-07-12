---
card: spring-authorization-server
gi: 16
slug: oauth2authorization-model
title: "OAuth2Authorization model"
---

## 1. What it is

`OAuth2Authorization` is the class that represents one in-progress-or-completed grant — a single "authorization session" tying together the client, the resource owner (user), the requested scopes, and every token issued as part of that grant: the authorization code itself, the access token, the refresh token, and (for OIDC) the ID token. Where `RegisteredClient` answers "what is this client allowed to do in general," `OAuth2Authorization` answers "what actually happened in *this specific* grant, right now."

## 2. Why & when

A single OAuth2 flow produces multiple, related artifacts over time — first a short-lived authorization code, then an access token, then possibly a refresh token, and each of those needs to be looked up later (to redeem the code, to validate the access token, to use the refresh token) in a way that remembers they all belong together. `OAuth2Authorization` exists so the server has one consistent record per grant that every one of those lookups reads from and writes to, rather than scattered, disconnected token records.

You interact with `OAuth2Authorization` (usually indirectly, through the service that stores it) whenever:

- Debugging why a token introspection or revocation call can't find a token — the answer lives in how it's stored inside an `OAuth2Authorization`.
- Building a custom token-issuing extension that needs to inspect what's already been granted in this session (e.g. checking which scopes were already consented to).
- Implementing a custom `OAuth2AuthorizationService` and needing to understand exactly what an implementation must store and retrieve.

## 3. Core concept

Think of `OAuth2Authorization` as a single case file opened at the start of a grant and updated as the grant progresses. The file starts with the basics — which client, which user, which scopes were requested — and as the flow proceeds, new documents get stapled into the same file: first the authorization code, then (once redeemed) the access token, then the refresh token. Anyone needing to check something about this specific grant — "is this access token still valid," "which authorization code did this access token come from" — pulls the one case file rather than searching disconnected records.

```java
public class OAuth2Authorization implements Serializable {
    String getId();
    String getRegisteredClientId();
    String getPrincipalName();
    AuthorizationGrantType getAuthorizationGrantType();
    Set<String> getAuthorizedScopes();
    <T extends OAuth2Token> Token<T> getToken(Class<T> tokenType);
    Map<String, Object> getAttributes();
}
```

Internally, each token type (authorization code, access token, refresh token, OIDC ID token) is stored as a generic `OAuth2Authorization.Token<T>` wrapper that pairs the token value with metadata — issued time, expiry, and whether it's already been invalidated.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One OAuth2Authorization ties together a client, a user, and several tokens issued over time">
  <rect x="220" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">OAuth2Authorization</text>

  <rect x="20" y="110" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">authorization code</text>

  <rect x="185" y="110" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">access token</text>

  <rect x="350" y="110" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="425" y="140" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">refresh token</text>

  <rect x="470" y="180" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="210" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OIDC ID token</text>

  <line x1="320" y1="70" x2="95" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="260" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="425" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="545" y2="178" stroke="#3fb950" stroke-width="2"/>
</svg>

Time flows left to right, top to bottom — one authorization record accumulates tokens as the grant proceeds.

## 5. Runnable example

The scenario: constructing an `OAuth2Authorization` step by step as a grant progresses, from just the initial request context to a fully populated record with an access and refresh token.

### Level 1 — Basic

```java
// AuthorizationModelDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.Set;
import java.util.UUID;

public class AuthorizationModelDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .build();

        OAuth2Authorization authorization = OAuth2Authorization.withRegisteredClient(client)
                .principalName("alice")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizedScopes(Set.of("tasks.read"))
                .build();

        System.out.println("Principal: " + authorization.getPrincipalName());
        System.out.println("Scopes: " + authorization.getAuthorizedScopes());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java AuthorizationModelDemo.java`. Expected output:

```
Principal: alice
Scopes: [tasks.read]
```

This is the record at the very start of the grant — before any actual token exists yet.

### Level 2 — Intermediate

As the authorization code flow proceeds, the authorization code itself gets attached to this same record — this is what lets the server later look up "who was this code issued to" when the client redeems it.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationCode;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;

public class AuthorizationModelDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .build();

        Instant now = Instant.now();
        OAuth2AuthorizationCode code = new OAuth2AuthorizationCode(
                "abc123code", now, now.plusSeconds(300)); // codes are short-lived, ~5 minutes

        OAuth2Authorization authorization = OAuth2Authorization.withRegisteredClient(client)
                .principalName("alice")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizedScopes(Set.of("tasks.read"))
                .token(code)
                .build();

        System.out.println("Code value: " + authorization.getToken(OAuth2AuthorizationCode.class).getToken().getTokenValue());
        System.out.println("Code expires at: " + authorization.getToken(OAuth2AuthorizationCode.class).getToken().getExpiresAt());
    }
}
```

**How to run:** same as Level 1. Expected output (timestamp will vary):

```
Code value: abc123code
Code expires at: 2026-07-12T10:05:00Z
```

What changed: the authorization now carries an actual token artifact (`OAuth2AuthorizationCode`) with its own value and expiry, wrapped so the server can later find this whole authorization by searching for that code value — which is exactly how the token endpoint validates a code redemption.

### Level 3 — Advanced

Once the client redeems the code, the server issues an access token and a refresh token, replacing the (now consumed) code — production code checks each token's validity via the wrapper's `isActive()`/`isExpired()` helpers, not just its presence, since an authorization can hold a token record that has since expired or been marked invalidated.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.core.OAuth2AccessToken;
import org.springframework.security.oauth2.core.OAuth2RefreshToken;
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.time.Instant;
import java.util.Set;
import java.util.UUID;

public class AuthorizationModelDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .build();

        Instant now = Instant.now();
        OAuth2AccessToken accessToken = new OAuth2AccessToken(
                OAuth2AccessToken.TokenType.BEARER, "access-xyz", now, now.plusSeconds(600), Set.of("tasks.read"));
        OAuth2RefreshToken refreshToken = new OAuth2RefreshToken(
                "refresh-abc", now, now.plus(java.time.Duration.ofDays(7)));

        OAuth2Authorization authorization = OAuth2Authorization.withRegisteredClient(client)
                .principalName("alice")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizedScopes(Set.of("tasks.read"))
                .token(accessToken)
                .token(refreshToken)
                .build();

        OAuth2Authorization.Token<OAuth2AccessToken> at = authorization.getToken(OAuth2AccessToken.class);
        System.out.println("Access token active: " + at.isActive());
        System.out.println("Access token expired: " + at.isExpired());
        System.out.println("Refresh token present: " + (authorization.getRefreshToken() != null));
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Access token active: true
Access token expired: false
Refresh token present: true
```

What changed and why it's production-flavored: real resource-server and revocation logic never just checks "does a token value exist" — it checks `isActive()` (not expired *and* not invalidated), since an `OAuth2Authorization` persists in storage even after its tokens have expired or been explicitly revoked, and treating an inactive token as valid would be a serious authorization bug.

## 6. Walkthrough

Tracing how one `OAuth2Authorization` record evolves across an entire authorization code grant, in execution order:

1. `GET /oauth2/authorize?client_id=task-tracker&...` arrives; after login and consent, the server creates a **new** `OAuth2Authorization` (Level 1's shape: client, principal, requested scopes, no tokens yet).
2. The server generates an authorization code, attaches it via `.token(code)` (Level 2), and **saves** this authorization through the `OAuth2AuthorizationService` (next card), keyed so it can be found later by the code's value.
3. The server responds `302 Found` with `Location: https://task-tracker.example.com/callback?code=abc123code`.
4. The client calls `POST /oauth2/token` with `grant_type=authorization_code&code=abc123code&redirect_uri=...`.
5. The token endpoint looks up the `OAuth2Authorization` **by that code value**, confirms the code's `isActive()` is true (not expired, not already used), and — critically — marks the code as invalidated so it can never be redeemed a second time.
6. The server generates the access token and refresh token, attaches both to the **same** authorization record (Level 3's shape), and saves the updated record.
7. The response body is `{"access_token": "access-xyz", "refresh_token": "refresh-abc", "token_type": "Bearer", "expires_in": 600, "scope": "tasks.read"}`.
8. Later, when a resource server validates `access-xyz`, it (indirectly, via introspection or JWT decoding) is confirming facts that all trace back to this one `OAuth2Authorization` record: which client it was issued to, which user it represents, and which scopes it carries.

```
authorize -> [Authorization: client+principal+scopes, no tokens]
   |  save
   v
issue code -> [Authorization: + authorization_code]
   |  save
   v
POST /token (code) -> lookup by code -> mark code invalidated
   |
   v
issue tokens -> [Authorization: + access_token + refresh_token]
   |  save
   v
resource server validates access_token against this same record
```

## 7. Gotchas & takeaways

> An authorization code must be marked invalidated the instant it's redeemed — if a stolen, already-used code is presented again to the token endpoint, the correct behavior per the OAuth2 spec is not just to reject it but to treat it as a signal that all tokens issued from that authorization may be compromised and should be revoked too.

- `OAuth2Authorization` is looked up by different keys depending on context — by authorization code value during code redemption, by access token value during introspection, by refresh token value during a refresh — a well-implemented `OAuth2AuthorizationService` (next card) must support all of these lookups.
- Checking a token's mere *presence* on the authorization isn't enough — always check `isActive()`, which accounts for both expiry and explicit invalidation.
- `getAttributes()` is where request-scoped extras get stashed (like the original `code_challenge` for PKCE verification) — it's a general-purpose map, not just for the well-known fields.
- One `OAuth2Authorization` corresponds to one grant — a second login by the same user, even for the same client, creates a distinct new authorization record, not an update to the old one.
- This model is what the in-memory and JDBC `OAuth2AuthorizationService` implementations (next card) actually persist — understanding its shape makes debugging storage-related issues far more tractable.
