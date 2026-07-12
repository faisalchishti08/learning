---
card: spring-authorization-server
gi: 14
slug: redirect-uris-scopes
title: "Redirect URIs & scopes"
---

## 1. What it is

Redirect URIs and scopes are two of the permission fields on `RegisteredClient` (card 0010) that deserve their own deep dive because they're both frequent sources of security bugs and confusing errors. A **redirect URI** is one of the exact addresses the server is allowed to send the user's browser back to after login, carrying the authorization code. A **scope** is a named permission (like `read`, `write`, or the OIDC-standard `openid`, `profile`, `email`) that limits what an issued token can actually be used for. Both are declared as allow-lists on the client — anything not listed is rejected.

## 2. Why & when

Redirect URIs exist because the authorization code, once issued, is sent to *wherever the request says to send it* — without a strict allow-list, an attacker could register a malicious `redirect_uri` pointing at their own server and trick a user into authorizing a code that then lands in the attacker's hands instead of the legitimate app's. Scopes exist because a token that grants blanket access to everything is far more dangerous if leaked than one scoped to exactly what the requesting operation needed.

Reach for careful redirect URI and scope configuration whenever:

- Registering any new client — get the exact redirect URI right the first time, since a mismatch produces an opaque `invalid_request` rejected *before* the user even sees a login page (the server won't redirect to an unregistered address, even to show an error).
- Designing what a client can do — splitting permissions into granular scopes (`orders.read`, `orders.write`) rather than one broad scope lets you grant exactly what's needed per integration.
- Supporting mobile or desktop apps that use custom URI schemes (`myapp://callback`) or loopback addresses (`http://127.0.0.1:PORT/callback`) as their redirect target, both of which the server supports but validates differently from a normal HTTPS URL.

## 3. Core concept

A redirect URI is like a courier's *pre-approved delivery address* — the sender (authorization server) will only hand the package (authorization code) to the exact address on file, never wherever the recipient happens to claim they are at pickup time. A scope is like a *permission slip* attached to that package — even after delivery, the package (token) only unlocks the specific doors listed on the slip (specific API operations), not the whole building.

```java
RegisteredClient.withId(UUID.randomUUID().toString())
    .clientId("task-tracker")
    .redirectUri("https://task-tracker.example.com/login/oauth2/code/task-tracker")
    .scope("orders.read")
    .scope("orders.write")
    .build();
```

Spring Authorization Server matches redirect URIs by exact string equality by default (not prefix or wildcard matching), and validates that requested scopes are a subset of what the client is registered for — anything outside either allow-list is rejected before any code or token is issued.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Redirect URI allow-list and scope allow-list both gate what the server will do">
  <rect x="30" y="30" width="580" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="60" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Request: redirect_uri=... &amp; scope=read write admin</text>

  <rect x="30" y="110" width="270" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="135" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">redirectUris allow-list</text>
  <text x="165" y="155" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">exact match required</text>
  <text x="165" y="172" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">match -&gt; safe to redirect code</text>

  <rect x="340" y="110" width="270" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="135" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">scopes allow-list</text>
  <text x="475" y="155" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">"admin" not registered</text>
  <text x="475" y="172" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">-&gt; trimmed or rejected</text>

  <line x1="320" y1="80" x2="165" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="80" x2="475" y2="108" stroke="#3fb950" stroke-width="2"/>
</svg>

Both allow-lists are checked independently, and both must pass before anything is issued.

## 5. Runnable example

The scenario: registering task-tracker's redirect URI and scopes, then growing to handle a mobile app's loopback redirect and a granular scope model.

### Level 1 — Basic

```java
// RedirectScopeDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class RedirectScopeDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/login/oauth2/code/task-tracker")
                .scope("read")
                .build();

        System.out.println("Redirect URIs: " + client.getRedirectUris());
        System.out.println("Scopes: " + client.getScopes());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java RedirectScopeDemo.java`. Expected output:

```
Redirect URIs: [https://task-tracker.example.com/login/oauth2/code/task-tracker]
Scopes: [read]
```

A request whose `redirect_uri` or `scope` doesn't exactly match these values is rejected.

### Level 2 — Intermediate

The product now needs finer-grained permissions (separating reading tasks from writing them) and must support a second redirect target for a staging environment.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class RedirectScopeDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/login/oauth2/code/task-tracker")
                .redirectUri("https://staging.task-tracker.example.com/login/oauth2/code/task-tracker")
                .scope("tasks.read")
                .scope("tasks.write")
                .build();

        System.out.println("Redirect URIs: " + client.getRedirectUris());
        System.out.println("Scopes: " + client.getScopes());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Redirect URIs: [https://task-tracker.example.com/login/oauth2/code/task-tracker, https://staging.task-tracker.example.com/login/oauth2/code/task-tracker]
Scopes: [tasks.read, tasks.write]
```

What changed: the client can now redirect to either its production or staging URL (both must be listed explicitly — there's no wildcard subdomain matching), and permissions are split so a token requested with only `tasks.read` can never be used to modify data even if the client application has a bug that tries.

### Level 3 — Advanced

A companion mobile app needs to register too. Native apps can't receive an HTTPS redirect from an external browser back into the app directly in the same way, so it uses a loopback IP redirect URI with a dynamic port — a pattern Spring Authorization Server explicitly supports for public clients using PKCE.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

import java.util.UUID;

public class RedirectScopeDemo {
    public static void main(String[] args) {
        RegisteredClient mobileClient = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker-mobile")
                .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                // loopback redirect: the OS routes this back to the native app; port varies per launch
                .redirectUri("http://127.0.0.1:8000/callback")
                .scope("tasks.read")
                .clientSettings(ClientSettings.builder().requireProofKey(true).build())
                .build();

        System.out.println("Mobile redirect URIs: " + mobileClient.getRedirectUris());
        System.out.println("Auth method: " + mobileClient.getClientAuthenticationMethods());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Mobile redirect URIs: [http://127.0.0.1:8000/callback]
Auth method: [none]
```

What changed and why it's production-flavored: mobile apps are public clients, so `NONE` plus mandatory PKCE (card 0012) replaces the missing client secret, and the loopback redirect lets the native app spin up a temporary local HTTP listener to catch the browser's redirect — a well-established, RFC-documented pattern rather than a workaround.

## 6. Walkthrough

Tracing a redirect URI and scope mismatch through the authorization endpoint, in execution order:

1. A malicious actor crafts `GET /oauth2/authorize?client_id=task-tracker&redirect_uri=https://evil.example.com/steal&response_type=code&scope=tasks.read`, hoping to trick a logged-in user into approving a code that gets sent to `evil.example.com` instead.
2. The server loads `RegisteredClient` for `task-tracker` and compares `https://evil.example.com/steal` against the registered redirect URIs from Level 2 — it isn't an exact match for either.
3. Because redirect URI validation happens *before* any redirect occurs, the server does **not** redirect the browser anywhere at all — it renders an error directly, refusing to send anything (even an error) to an unregistered address, which is precisely what stops the attack: the code is never generated in the first place.
4. Contrast this with a legitimate request using the registered URI and a valid, in-scope `scope=tasks.read`: validation passes, the user authenticates and consents, and the server issues `302 Found` with `Location: https://task-tracker.example.com/login/oauth2/code/task-tracker?code=AbC123...`.
5. The client's backend then exchanges that code via `POST /oauth2/token`, and the resulting access token is scoped to exactly `tasks.read` — calling a hypothetical `DELETE /api/tasks/42` endpoint with this token is rejected by the resource server with `403 Forbidden` because `tasks.write` (or a delete-specific scope) was never granted.

```
Attacker's redirect_uri NOT in allow-list
   -> server refuses to redirect at all (fails closed, before code is issued)

Legitimate redirect_uri IS in allow-list, scope=tasks.read IS in allow-list
   -> 302 to registered URI with ?code=...
   -> token issued, scoped to tasks.read only
   -> write/delete calls with that token -> 403 Forbidden
```

## 7. Gotchas & takeaways

> Redirect URI matching is exact by default — a registered `https://task-tracker.example.com/callback` will **not** match an incoming `https://task-tracker.example.com/callback/` (trailing slash) or `http://` instead of `https://`. This trips up more integrations than any other single setting in this section.

- Register every environment's redirect URI explicitly (production, staging, local dev) — there's no built-in wildcard or pattern matching for security reasons.
- Loopback redirect URIs (`http://127.0.0.1:<port>/...`) are treated specially: the server allows the *port* to vary between requests for exactly this pattern, since native apps can't predict which port the OS will hand them.
- Scopes on the `RegisteredClient` are a ceiling; the actual token's scopes are the intersection of what's registered, what's requested, and (if consent is required) what the user approved.
- `openid`, `profile`, `email`, and other `OidcScopes` constants are just conventionally-named scopes from the OIDC spec — the server treats them like any other scope string except that `openid` also triggers OIDC-specific behavior (issuing an ID token).
- When debugging a rejected authorization request, check the redirect URI match *first* — if it fails, the server won't even display a helpful in-browser error, since it refuses to redirect anywhere at all.
