---
card: spring-authorization-server
gi: 12
slug: client-authentication-methods-basic-post-jwt-none-pkce
title: "Client authentication methods (basic, post, JWT, none/PKCE)"
---

## 1. What it is

A client authentication method is *how* a client proves to the token endpoint that it's really the client it claims to be. Spring Authorization Server supports the standard OAuth2 methods, each represented by a `ClientAuthenticationMethod` constant: `CLIENT_SECRET_BASIC` (secret in an HTTP Basic auth header), `CLIENT_SECRET_POST` (secret as a form parameter in the request body), `PRIVATE_KEY_JWT` / `CLIENT_SECRET_JWT` (a signed JWT assertion instead of a raw secret), and `NONE` (no client secret at all, relying on PKCE instead). A `RegisteredClient` declares which of these it's allowed to use, and the server rejects any token request that authenticates a different way.

## 2. Why & when

Not every client can safely hold a secret. A server-side web application can — its source code and configuration live on a machine only the operator controls. A single-page app running in a browser, or a native mobile app, cannot — anyone can decompile the app or read its network traffic and extract a baked-in secret. These different levels of trust are exactly why multiple authentication methods exist, and picking the right one per client is a real security decision, not a formality.

Reach for:

- **`CLIENT_SECRET_BASIC`** — the default choice for confidential clients (backend servers) that can keep a secret; simplest to configure and widely supported.
- **`CLIENT_SECRET_POST`** — when a client library or legacy system can't send Basic auth headers but can send form parameters; functionally equivalent, slightly less common.
- **`PRIVATE_KEY_JWT` / `CLIENT_SECRET_JWT`** — for high-security integrations (e.g. banking, or clients that are themselves other backend services) where a signed, time-bound assertion is stronger than a long-lived static secret that could leak once and be reused forever.
- **`NONE` + PKCE** — mandatory for public clients: single-page apps, mobile apps, CLI tools — anything that can't keep a secret confidential. PKCE (Proof Key for Code Exchange) replaces the secret with a per-request, one-time cryptographic challenge.

## 3. Core concept

Think of these as different ways to prove your identity at a locked door. `CLIENT_SECRET_BASIC` and `CLIENT_SECRET_POST` are like showing a physical key — anyone holding the key gets in, and if the key is copied, the copy works just as well. `PRIVATE_KEY_JWT` is like signing a note with your own private signature stamp each time — the door checks the signature against a public record of what your stamp looks like, but never sees or stores the stamp itself, so nothing reusable is transmitted. `NONE` with PKCE is for someone who has no key at all — instead, right before knocking, they generate a random word, tell the door a scrambled (hashed) version of it, and then when they return moments later to actually open the door, they reveal the original word — proving they're the same person who started the process, without ever needing a secret to steal.

```java
RegisteredClient.withId(UUID.randomUUID().toString())
    .clientId("public-spa")
    .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)
    .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
    .clientSettings(ClientSettings.builder().requireProofKey(true).build())
    .build();
```

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four client authentication methods ranging from shared secret to no secret with PKCE">
  <rect x="20" y="20" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="46" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">CLIENT_SECRET</text>
  <text x="90" y="62" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">_BASIC</text>

  <rect x="180" y="20" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="250" y="46" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">CLIENT_SECRET</text>
  <text x="250" y="62" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">_POST</text>

  <rect x="340" y="20" width="140" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="410" y="46" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">PRIVATE_KEY_JWT /</text>
  <text x="410" y="62" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">CLIENT_SECRET_JWT</text>

  <rect x="500" y="20" width="120" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="560" y="46" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">NONE</text>
  <text x="560" y="62" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">+ PKCE</text>

  <line x1="20" y1="110" x2="620" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <text x="20" y="130" fill="#8b949e" font-size="11" font-family="sans-serif">confidential clients (server can keep a secret)</text>
  <text x="500" y="130" fill="#8b949e" font-size="11" text-anchor="end" font-family="sans-serif">public clients (SPA, mobile)</text>

  <text x="90" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">secret in header</text>
  <text x="250" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">secret in body</text>
  <text x="410" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">signed assertion</text>
  <text x="560" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no secret at all</text>
</svg>

The methods form a spectrum from "shares a durable secret" to "proves possession without any secret."

## 5. Runnable example

The scenario: the same "task-tracker" client authenticating with the token endpoint, evolving from a shared-secret method to a JWT assertion and finally to PKCE for a public front-end.

### Level 1 — Basic

```java
// AuthMethodDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class AuthMethodDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("http://127.0.0.1:8080/login/oauth2/code/task-tracker")
                .build();

        System.out.println("Auth methods: " + client.getClientAuthenticationMethods());
    }
}
```

**How to run:** run within a Spring Boot project with `spring-security-oauth2-authorization-server`, via `java AuthMethodDemo.java` through a build tool. Expected output:

```
Auth methods: [client_secret_basic]
```

The client authenticates by sending `Authorization: Basic base64("task-tracker:secret")` on every token request.

### Level 2 — Intermediate

A backend-to-backend integration wants stronger authentication than a static secret, so it switches to `PRIVATE_KEY_JWT`: the client signs a short-lived JWT assertion with its own private key instead of sending a shared secret at all.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class AuthMethodDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("backend-integration")
                // no clientSecret at all — the client proves itself with a signed JWT instead
                .clientAuthenticationMethod(ClientAuthenticationMethod.PRIVATE_KEY_JWT)
                .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
                .scope("orders.read")
                .build();

        System.out.println("Auth methods: " + client.getClientAuthenticationMethods());
        System.out.println("Grant type: " + client.getAuthorizationGrantTypes());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Auth methods: [private_key_jwt]
Grant type: [client_credentials]
```

What changed: instead of a shared secret, the client now signs a JWT assertion (containing its `client_id` as both issuer and subject, a short expiry, and a unique `jti`) with its own RSA private key. The server verifies the signature using the client's *public* key, which it looks up via a configured JWK Set URI — nothing secret ever crosses the wire, and a captured assertion is useless after it expires.

### Level 3 — Advanced

The front-end for task-tracker is actually a single-page app running entirely in the browser — it cannot hold any secret at all. Production configures it as a public client with `NONE` and mandatory PKCE, and the server additionally restricts it to HTTPS-only, exact-match redirect URIs to compensate for having no client secret.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

import java.util.UUID;

public class AuthMethodDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker-spa")
                .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("read")
                .clientSettings(ClientSettings.builder()
                        .requireProofKey(true) // PKCE is mandatory since there is no secret
                        .requireAuthorizationConsent(true)
                        .build())
                .build();

        System.out.println("Auth method: " + client.getClientAuthenticationMethods());
        System.out.println("PKCE required: " + client.getClientSettings().isRequireProofKey());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Auth method: [none]
PKCE required: true
```

What changed and why it's production-flavored: with `NONE`, anyone who learns `client_id` (public knowledge, visible in the browser) could otherwise submit an authorization code for exchange — PKCE closes this gap by requiring the *same browser session* that started the flow to supply a secret, one-time `code_verifier` at the token-exchange step, which the server checks against the `code_challenge` it recorded at the start.

## 6. Walkthrough

Tracing the Level 3 flow end to end, in execution order:

1. The SPA generates a random `code_verifier` (e.g. a 64-character random string) and computes `code_challenge = BASE64URL(SHA256(code_verifier))`.
2. The browser navigates to `GET /oauth2/authorize?client_id=task-tracker-spa&response_type=code&redirect_uri=https://task-tracker.example.com/callback&scope=read&code_challenge=<challenge>&code_challenge_method=S256`.
3. The server looks up `RegisteredClient` for `task-tracker-spa`, confirms `requireProofKey` is true, and — because a public client with `NONE` *must* supply a `code_challenge` — rejects the request with `invalid_request` if it's missing.
4. After login and consent, the server redirects to `https://task-tracker.example.com/callback?code=<auth-code>`, internally storing the `code_challenge` alongside that authorization code.
5. The SPA calls `POST /oauth2/token` with `grant_type=authorization_code&code=<auth-code>&redirect_uri=...&client_id=task-tracker-spa&code_verifier=<original-verifier>` — critically, **no** `Authorization` header and no client secret, since the client authentication method is `NONE`.
6. The token endpoint recomputes `SHA256(code_verifier)` from the request and compares it, byte for byte, against the `code_challenge` stored in step 4.
7. If they match, the server proceeds to issue tokens; if they don't — meaning whoever is presenting this code doesn't have the original `code_verifier` — the request is rejected with `invalid_grant`, even though the `client_id` alone was correct and public.

```
Browser: verifier -> SHA256 -> challenge
   |
   |  /authorize?...&code_challenge=<challenge>   (challenge only, verifier stays local)
   v
Server stores challenge with the issued code
   |
   |  /token grant_type=authorization_code&code=...&code_verifier=<verifier>
   v
Server: SHA256(verifier) == stored challenge? --yes--> issue tokens
                                              --no---> invalid_grant
```

## 7. Gotchas & takeaways

> A public client (`NONE`) without `requireProofKey(true)` is a real vulnerability, not a theoretical one — anyone who intercepts or guesses an authorization code (e.g. via a misconfigured redirect or browser history) can redeem it for tokens with nothing more than the publicly-known `client_id`. Always pair `NONE` with mandatory PKCE.

- `CLIENT_SECRET_BASIC` and `CLIENT_SECRET_POST` are functionally interchangeable in security terms — the choice is usually dictated by what the client library supports, not a security preference between them.
- `PRIVATE_KEY_JWT` requires the server to have a way to verify the client's signature — typically a `jwkSetUrl` configured on the `RegisteredClient` pointing at the client's own published public keys.
- PKCE can also be required for *confidential* clients as defense in depth (as shown in the previous card) — it isn't exclusive to public clients, even though it's mandatory for them.
- A `RegisteredClient` can list more than one authentication method if it needs to support multiple client library versions during a migration — the server accepts whichever the incoming request actually used.
- Mixing up which method a `RegisteredClient` is configured for versus what the client actually sends produces a generic `invalid_client` error — check the method list first when debugging authentication failures.
