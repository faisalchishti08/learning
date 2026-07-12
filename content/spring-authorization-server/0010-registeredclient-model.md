---
card: spring-authorization-server
gi: 10
slug: registeredclient-model
title: "RegisteredClient model"
---

## 1. What it is

`RegisteredClient` is the class that represents one OAuth2 client application registered with the authorization server — the digital equivalent of a row in a "who's allowed to ask us for tokens" table. It bundles everything the server needs to know about a client: its identifier, its secret (if it has one), which authentication methods it may use, which grant types it's allowed to request, which redirect URIs it may send users back to, which scopes it may ask for, and a set of fine-grained settings that tune its behavior.

Every other core component in this section — the repository that stores clients, the authorization that gets issued, the tokens that get generated — ultimately reads from a `RegisteredClient` instance to decide what is and isn't permitted for a given request.

## 2. Why & when

An authorization server can never simply trust that whoever is asking for a token is who they claim to be, or that they're allowed to do what they're asking. `RegisteredClient` exists so that trust is established once, up front, during registration, rather than improvised on every request. It's the single source of truth the server consults before issuing any authorization code or token.

Reach for `RegisteredClient` (by building one, in code or via a repository) whenever:

- You're standing up a new authorization server and need to declare which applications may talk to it.
- You're onboarding a new client application (a web app, a mobile app, a backend service) and need to decide its grant types, redirect URIs, and secret.
- You're debugging "invalid_client" or "unauthorized_client" errors — the answer almost always traces back to a mismatch between what the request asked for and what the matching `RegisteredClient` permits.

## 3. Core concept

Think of `RegisteredClient` as a passport application on file at an embassy. The embassy (authorization server) doesn't just take your word for who you are — it keeps a record: your name (`clientId`), your photo-matching secret (`clientSecret`), which border crossings you're allowed to use (`redirectUris`), which types of visas you can request (`authorizationGrantTypes`), and which countries you're permitted to visit (`scopes`). When you show up at a border (an OAuth2 request), the guard checks the request against the file on record — not against whatever you happen to claim in the moment.

A `RegisteredClient` is built with a fluent builder and is intentionally **immutable** once constructed — settings can't drift mid-request, which keeps authorization decisions predictable and auditable. Its key building blocks are:

- **Identity**: `id` (an internal UUID) and `clientId` (the public identifier sent in requests).
- **Credentials**: `clientSecret` and `clientAuthenticationMethods` (how the client proves the secret is really its own — see the next card).
- **Permissions**: `authorizationGrantTypes`, `redirectUris`, `scopes`.
- **Tuning**: `clientSettings` and `tokenSettings`, covering things like consent requirements and token lifetimes.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RegisteredClient bundles identity, credentials, permissions and settings">
  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#e6edf3" font-size="15" text-anchor="middle" font-family="sans-serif">RegisteredClient</text>

  <rect x="30" y="120" width="150" height="56" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Identity</text>
  <text x="105" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">id, clientId</text>

  <rect x="200" y="120" width="150" height="56" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="275" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Credentials</text>
  <text x="275" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">secret, auth methods</text>

  <rect x="370" y="120" width="150" height="56" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="144" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Permissions</text>
  <text x="445" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">grants, redirects, scopes</text>

  <rect x="480" y="200" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="228" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Settings</text>

  <line x1="290" y1="66" x2="105" y2="118" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="310" y1="66" x2="275" y2="118" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="340" y1="66" x2="445" y2="118" stroke="#6db33f" stroke-width="1.5"/>
  <line x1="380" y1="66" x2="550" y2="198" stroke="#6db33f" stroke-width="1.5"/>
</svg>

One `RegisteredClient` object holds four groups of facts the server consults on every request.

## 5. Runnable example

The scenario: a small "task-tracker" web app needs to register itself with an authorization server so it can request tokens on behalf of its users. We'll build the same `RegisteredClient` and grow it from a bare-bones registration into one hardened for production use.

### Level 1 — Basic

```java
// RegisteredClientDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class RegisteredClientDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("http://127.0.0.1:8080/login/oauth2/code/task-tracker")
                .scope("read")
                .build();

        System.out.println("Registered client: " + client.getClientId());
        System.out.println("Grant types: " + client.getAuthorizationGrantTypes());
        System.out.println("Redirect URIs: " + client.getRedirectUris());
    }
}
```

**How to run:** requires the `spring-security-oauth2-authorization-server` jar (and its transitive dependencies) on the classpath; simplest is to drop this class into a Spring Boot project with that starter and run `java RegisteredClientDemo.java` via a build tool, or run it as a JUnit-less `main` inside the project. Expected output:

```
Registered client: task-tracker
Grant types: [authorization_code]
Redirect URIs: [http://127.0.0.1:8080/login/oauth2/code/task-tracker]
```

This is the minimum: an id, a secret, one authentication method, one grant type, one redirect URI, one scope.

### Level 2 — Intermediate

Real applications need a refresh token so users aren't forced to re-authenticate constantly, and they need `ClientSettings` to require explicit user consent before scopes are granted.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.core.oidc.OidcScopes;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

import java.util.UUID;

public class RegisteredClientDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("http://127.0.0.1:8080/login/oauth2/code/task-tracker")
                .scope(OidcScopes.OPENID)
                .scope("read")
                .scope("write")
                .clientSettings(ClientSettings.builder()
                        .requireAuthorizationConsent(true)
                        .build())
                .build();

        System.out.println("Scopes: " + client.getScopes());
        System.out.println("Requires consent: "
                + client.getClientSettings().isRequireAuthorizationConsent());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Scopes: [openid, read, write]
Requires consent: true
```

What changed: adding `REFRESH_TOKEN` as a second grant type lets the client exchange a refresh token for a new access token later without a fresh login. Adding `openid` opts the client into OIDC. Turning on `requireAuthorizationConsent` means the server will show the user a consent screen listing `read` and `write` before granting them — the client can no longer silently accumulate scopes.

### Level 3 — Advanced

Production hardens this further: a hashed secret instead of plaintext `{noop}`, PKCE required even for a confidential client (defense in depth), a tighter redirect URI, and explicit token lifetime settings so access tokens expire quickly while refresh tokens are rotated.

```java
import org.springframework.security.crypto.factory.PasswordEncoderFactories;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.core.oidc.OidcScopes;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;

import java.time.Duration;
import java.util.UUID;

public class RegisteredClientDemo {
    public static void main(String[] args) {
        PasswordEncoder encoder = PasswordEncoderFactories.createDelegatingPasswordEncoder();

        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret(encoder.encode("s3cr3t-from-vault"))
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("https://task-tracker.example.com/login/oauth2/code/task-tracker")
                .scope(OidcScopes.OPENID)
                .scope("read")
                .scope("write")
                .clientSettings(ClientSettings.builder()
                        .requireAuthorizationConsent(true)
                        .requireProofKey(true) // require PKCE even though the client has a secret
                        .build())
                .tokenSettings(TokenSettings.builder()
                        .accessTokenTimeToLive(Duration.ofMinutes(10))
                        .refreshTokenTimeToLive(Duration.ofDays(7))
                        .reuseRefreshTokens(false) // rotate refresh tokens on each use
                        .build())
                .build();

        System.out.println("Access token TTL: " + client.getTokenSettings().getAccessTokenTimeToLive());
        System.out.println("Requires PKCE: " + client.getClientSettings().isRequireProofKey());
        System.out.println("Refresh token reuse: " + client.getTokenSettings().isReuseRefreshTokens());
    }
}
```

**How to run:** same as Level 1, run as a `main` method inside a Spring Boot project that has `spring-security-oauth2-authorization-server` and `spring-security-crypto` on the classpath. Expected output:

```
Access token TTL: PT10M
Requires PKCE: true
Refresh token reuse: false
```

What changed and why it's production-flavored: the secret is now hashed (never store plaintext), `requireProofKey(true)` demands a PKCE code challenge even from a client that already authenticates with a secret — closing the door on authorization code interception — and short access-token lifetimes plus refresh token rotation limit the damage window if either token ever leaks.

## 6. Walkthrough

Tracing Level 3 in execution order, from construction to how the server later uses it:

1. `RegisteredClient.withId(...)` starts the builder with a fresh internal UUID — this is the primary key the server's storage layer uses, distinct from the human-readable `clientId`.
2. `.clientId("task-tracker")` sets the identifier the client will send in the `client_id` request parameter (or embed in its Basic auth header).
3. `.clientSecret(encoder.encode(...))` stores a bcrypt (or similar) hash, never the raw secret — so a database leak doesn't hand over usable credentials.
4. `.clientAuthenticationMethod(CLIENT_SECRET_BASIC)` declares the client will authenticate via HTTP Basic auth (`Authorization: Basic base64(clientId:secret)`), which the token endpoint filter checks against the stored hash.
5. The two `.authorizationGrantType(...)` calls declare which OAuth2 grants this client may use — the authorization endpoint and token endpoint both reject any grant not in this set with an `unauthorized_client` error.
6. `.redirectUri(...)` locks down exactly where the server is allowed to send the browser back to after login — any other `redirect_uri` on an incoming request is rejected up front, which is what prevents an attacker from redirecting a stolen code to their own server.
7. The `.scope(...)` calls declare the maximum scopes this client may ever be granted — a request asking for a scope not listed here is trimmed or rejected.
8. `.clientSettings(...)` turns on mandatory consent and mandatory PKCE; `.tokenSettings(...)` sets short-lived access tokens with rotating refresh tokens.
9. `.build()` produces an **immutable** `RegisteredClient` object — from this point on, nothing in the running server can silently change what this client is allowed to do.
10. Later, when a real HTTP request like `GET /oauth2/authorize?client_id=task-tracker&redirect_uri=https://task-tracker.example.com/login/oauth2/code/task-tracker&response_type=code&scope=read` arrives, the server looks up the `RegisteredClient` for `task-tracker` and checks the request's `redirect_uri`, `scope`, and grant type against exactly the fields we just set — a mismatch on any of them produces an OAuth2 error response instead of a code.

```
Incoming request  --lookup by client_id-->  RegisteredClient  --validate-->  allow / reject
```

## 7. Gotchas & takeaways

> `RegisteredClient` is immutable by design. If you need to change a client's settings at runtime, you build a *new* `RegisteredClient` (usually via `RegisteredClient.from(existing)...build()`) and save it back through the repository — you don't mutate the object in place.

- `clientId` is public and appears in URLs and Basic auth headers; `id` is the internal primary key and should never be exposed to callers.
- Forgetting to add `AuthorizationGrantType.REFRESH_TOKEN` is a common mistake — without it, the client gets an access token but can never renew it without a fresh login.
- `redirectUri` matching is exact-string by default; a trailing slash mismatch between what's registered and what's sent is a frequent source of `invalid_request` errors.
- Never leave `{noop}` (plaintext) secrets outside local demos — always hash with `PasswordEncoderFactories.createDelegatingPasswordEncoder()` or equivalent.
- Scopes listed on `RegisteredClient` are a ceiling, not a guarantee — the actual grant still depends on user consent and the specific request.
