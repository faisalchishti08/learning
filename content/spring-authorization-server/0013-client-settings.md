---
card: spring-authorization-server
gi: 13
slug: client-settings
title: "Client settings"
---

## 1. What it is

`ClientSettings` is a small, extensible configuration object attached to every `RegisteredClient` that controls *how the server behaves toward that specific client*, as opposed to *what the client is allowed to request* (which is `RegisteredClient`'s other fields). It currently exposes `requireAuthorizationConsent` (should the user see a consent screen), `requireProofKey` (is PKCE mandatory), `jwkSetUrl` (where to fetch the client's public keys for `PRIVATE_KEY_JWT`), and `tokenEndpointAuthenticationSigningAlgorithm`, plus a general-purpose settings map for custom, non-standard extensions.

## 2. Why & when

Two clients can have identical grant types and scopes yet need to be treated very differently by the server — one is a trusted internal admin tool that shouldn't nag its one operator with a consent screen every login, another is a third-party integration that absolutely must show users what data it's requesting before anything is granted. `ClientSettings` exists to carry these *behavioral* decisions separately from the *permission* decisions, so they can be tuned per client without touching grant types or scopes at all.

Reach for adjusting `ClientSettings` when:

- Onboarding a third-party client that must show an explicit consent screen (regulatory or trust requirement) versus a first-party client that shouldn't.
- Hardening a confidential client with mandatory PKCE as defense in depth, or configuring a public client where PKCE is required by protocol.
- Wiring up `PRIVATE_KEY_JWT` authentication, which needs `jwkSetUrl` to know where to verify the client's signed assertions.
- Extending the server with a custom, application-specific per-client flag that doesn't have a first-class field — the settings map accepts arbitrary key/value pairs.

## 3. Core concept

If `RegisteredClient`'s grant types and scopes are the *rules of what's allowed*, `ClientSettings` is the *house rules for how this particular guest is treated* — does this guest need to sign a visitor's log every time (consent), does this guest need to show ID even though they have a key (PKCE), and where can staff verify this particular guest's credentials (JWK Set URI). It's built the same fluent way as `RegisteredClient` itself:

```java
ClientSettings settings = ClientSettings.builder()
        .requireAuthorizationConsent(true)
        .requireProofKey(true)
        .jwkSetUrl("https://backend-integration.example.com/.well-known/jwks.json")
        .build();
```

Because `ClientSettings` is backed by a generic settings map internally, custom values can also be stashed and retrieved with `.setting(key, value)` and `.getSetting(key)`, which is the officially supported way to extend it without subclassing.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ClientSettings holds behavioral flags separate from RegisteredClient permissions">
  <rect x="30" y="30" width="220" height="160" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="140" y="55" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">RegisteredClient</text>
  <text x="140" y="80" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">grantTypes</text>
  <text x="140" y="100" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">redirectUris</text>
  <text x="140" y="120" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">scopes</text>
  <text x="140" y="150" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">clientSettings -&gt;</text>

  <rect x="380" y="30" width="230" height="160" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="55" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">ClientSettings</text>
  <text x="495" y="80" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">requireAuthorizationConsent</text>
  <text x="495" y="100" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">requireProofKey</text>
  <text x="495" y="120" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">jwkSetUrl</text>
  <text x="495" y="140" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">tokenEndpointAuth...</text>
  <text x="495" y="160" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">custom settings map</text>

  <line x1="250" y1="150" x2="378" y2="80" stroke="#3fb950" stroke-width="2"/>
</svg>

Permissions live on the `RegisteredClient`; behavioral toggles live in its nested `ClientSettings`.

## 5. Runnable example

The scenario: onboarding "task-tracker" as a client and tuning how the server treats it, growing from defaults to a fully hardened configuration.

### Level 1 — Basic

```java
// ClientSettingsDemo.java
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

public class ClientSettingsDemo {
    public static void main(String[] args) {
        ClientSettings settings = ClientSettings.builder().build();

        System.out.println("Requires consent: " + settings.isRequireAuthorizationConsent());
        System.out.println("Requires PKCE: " + settings.isRequireProofKey());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` on the classpath via `java ClientSettingsDemo.java`. Expected output:

```
Requires consent: false
Requires PKCE: false
```

Defaults are permissive — no consent screen, no mandatory PKCE — suitable only for a trusted first-party client during early development.

### Level 2 — Intermediate

Task-tracker is now being opened up to third-party scopes, so consent must be shown, and the team decides to require PKCE for every client regardless of type, as a blanket policy.

```java
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

public class ClientSettingsDemo {
    public static void main(String[] args) {
        ClientSettings settings = ClientSettings.builder()
                .requireAuthorizationConsent(true)
                .requireProofKey(true)
                .build();

        System.out.println("Requires consent: " + settings.isRequireAuthorizationConsent());
        System.out.println("Requires PKCE: " + settings.isRequireProofKey());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Requires consent: true
Requires PKCE: true
```

What changed: users will now see an explicit consent screen listing exactly which scopes task-tracker is requesting before any token is issued, and every authorization code flow — confidential or public — must include a PKCE `code_challenge`/`code_verifier` pair.

### Level 3 — Advanced

A second client, "backend-integration," authenticates via `PRIVATE_KEY_JWT` (card 0012) — this needs `jwkSetUrl` so the server can fetch its public key to verify signed assertions — plus a custom setting flagging it as "internal" so a downstream audit-logging filter can skip verbose logging for trusted internal callers.

```java
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

public class ClientSettingsDemo {
    public static void main(String[] args) {
        ClientSettings settings = ClientSettings.builder()
                .requireAuthorizationConsent(false) // internal client, no user-facing consent needed
                .requireProofKey(false)              // uses PRIVATE_KEY_JWT instead, not PKCE
                .jwkSetUrl("https://backend-integration.example.com/.well-known/jwks.json")
                .setting("com.example.internalClient", true) // custom extension
                .build();

        System.out.println("JWK Set URL: " + settings.getJwkSetUrl());
        System.out.println("Internal flag: " + settings.getSetting("com.example.internalClient"));
    }
}
```

**How to run:** same as Level 1. Expected output:

```
JWK Set URL: https://backend-integration.example.com/.well-known/jwks.json
Internal flag: true
```

What changed and why it's production-flavored: `jwkSetUrl` is what makes `PRIVATE_KEY_JWT` authentication (card 0012) actually verifiable — without it, the server has no way to fetch the public key needed to check the client's signed assertion. The custom setting demonstrates the officially supported escape hatch for application-specific per-client flags that don't have a dedicated field, avoiding the need to subclass or fork `ClientSettings`.

## 6. Walkthrough

Tracing how `ClientSettings` gets consulted during a real authorization request, in execution order:

1. A user's browser hits `GET /oauth2/authorize?client_id=task-tracker&response_type=code&redirect_uri=...&scope=read&code_challenge=...&code_challenge_method=S256`.
2. The server loads the matching `RegisteredClient` (card 0010) via the repository (card 0011), then reads its nested `ClientSettings`.
3. It checks `isRequireProofKey()` — true — and confirms the request included a `code_challenge`; if this were false and the request omitted it, PKCE would simply be skipped rather than enforced.
4. After the user authenticates, the server checks `isRequireAuthorizationConsent()` — true — so instead of immediately issuing an authorization code, it renders a consent page listing the requested scope (`read`) and waits for the user to approve.
5. Once the user approves, the server issues the authorization code and redirects back to the client's `redirect_uri` with `?code=...`.
6. Later, for the separate `backend-integration` client authenticating via `PRIVATE_KEY_JWT`, the token endpoint reads that client's `jwkSetUrl` from its `ClientSettings`, fetches the public JWK Set from that URL (typically caching it), and verifies the signature on the client's JWT assertion against the matching key.

```
GET /oauth2/authorize ...
     |
     v
RegisteredClient -> ClientSettings.isRequireProofKey()? --true--> enforce code_challenge
     |
     v
ClientSettings.isRequireAuthorizationConsent()? --true--> show consent page --approve--> issue code
```

## 7. Gotchas & takeaways

> `requireAuthorizationConsent(false)` is appropriate only for clients you fully trust (typically first-party apps you also operate) — turning it off for a third-party integration means users never see what scopes they're granting, which is both a poor practice and, in many jurisdictions, a compliance problem.

- `ClientSettings` controls *behavior*, `RegisteredClient`'s other fields control *permission* — mixing these up when debugging leads to looking in the wrong place (e.g. a missing consent screen is a `ClientSettings` issue, not a scopes issue).
- `jwkSetUrl` only matters for `PRIVATE_KEY_JWT` client authentication; setting it for a client using `CLIENT_SECRET_BASIC` has no effect.
- The custom settings map (`.setting(key, value)`) is the sanctioned extension point — don't try to smuggle custom data into unrelated fields like scopes.
- `requireProofKey` can be turned on for confidential clients too, as extra defense in depth, not just for public clients that are required to use it.
- Changing `ClientSettings` on an existing `RegisteredClient` requires rebuilding the client object (via `RegisteredClient.from(existing)`) and saving it back through the repository — settings aren't mutable in place.
