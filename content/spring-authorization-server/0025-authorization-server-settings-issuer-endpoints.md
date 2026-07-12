---
card: spring-authorization-server
gi: 25
slug: authorization-server-settings-issuer-endpoints
title: "Authorization server settings (issuer, endpoints)"
---

## 1. What it is

`AuthorizationServerSettings` is the server-wide (not per-client) configuration bean that defines the authorization server's own identity and the URL paths of its protocol endpoints: `issuer`, `authorizationEndpoint` (default `/oauth2/authorize`), `tokenEndpoint` (`/oauth2/token`), `jwkSetEndpoint` (`/oauth2/jwks`), `tokenRevocationEndpoint`, `tokenIntrospectionEndpoint`, `oidcClientRegistrationEndpoint`, and `oidcUserInfoEndpoint`. Where every other card in this section configures *a client*, `AuthorizationServerSettings` configures *the server itself*, exactly once, as a single `@Bean`.

## 2. Why & when

Every OAuth2 and OIDC client needs to discover where to send requests, and the `issuer` value is embedded inside every token this server issues (as the `iss` claim) — it's the server's self-declared identity that resource servers check against when validating tokens. `AuthorizationServerSettings` exists as the one place this identity and these endpoint paths are declared, so the rest of the server's components (metadata endpoints, token generation, filter chains) all read from a single, consistent source of truth rather than hardcoding paths independently.

Reach for configuring `AuthorizationServerSettings` when:

- Standing up a new authorization server — `issuer` must be set correctly (matching the externally-reachable base URL) before anything else works correctly, since it's baked into every token.
- Deploying behind a reverse proxy or load balancer where the externally-visible URL differs from what the application sees internally — a mismatched issuer causes resource servers to reject otherwise-valid tokens.
- Customizing endpoint paths to avoid collisions with existing routes in an application that also serves other content at `/oauth2/*`.
- Enabling OIDC-specific endpoints (`oidcClientRegistrationEndpoint`, `oidcUserInfoEndpoint`) that aren't active by default.

## 3. Core concept

Think of `AuthorizationServerSettings` as the letterhead and office directory for the entire authorization server — the letterhead (`issuer`) is the name the server signs onto every letter (token) it sends out, and the directory lists exactly which room number (endpoint path) handles which kind of request. Every visitor (client or resource server) that wants to interact with this server correctly relies on this one directory being accurate — get the letterhead wrong, and every letter the server has ever sent becomes suspect the moment someone checks the return address against what they expect.

```java
@Bean
public AuthorizationServerSettings authorizationServerSettings() {
    return AuthorizationServerSettings.builder()
            .issuer("https://auth.example.com")
            .authorizationEndpoint("/oauth2/authorize")
            .tokenEndpoint("/oauth2/token")
            .jwkSetEndpoint("/oauth2/jwks")
            .tokenRevocationEndpoint("/oauth2/revoke")
            .tokenIntrospectionEndpoint("/oauth2/introspect")
            .build();
}
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AuthorizationServerSettings defines the issuer and every protocol endpoint path">
  <rect x="220" y="20" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">issuer: https://auth.example.com</text>

  <rect x="20" y="110" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">/oauth2/authorize</text>

  <rect x="175" y="110" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="245" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">/oauth2/token</text>

  <rect x="330" y="110" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="400" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">/oauth2/jwks</text>

  <rect x="485" y="110" width="135" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="552" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">/oauth2/introspect</text>

  <line x1="290" y1="70" x2="90" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="310" y1="70" x2="245" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="330" y1="70" x2="400" y2="108" stroke="#3fb950" stroke-width="2"/>
  <line x1="360" y1="70" x2="552" y2="108" stroke="#3fb950" stroke-width="2"/>

  <rect x="220" y="190" width="200" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="215" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">discoverable at /.well-known/oauth-authorization-server</text>
</svg>

One settings bean anchors the server's identity and every relative endpoint path clients and metadata discovery rely on.

## 5. Runnable example

The scenario: configuring task-tracker's authorization server with a correct issuer, then handling a reverse-proxy deployment where the internal and external URLs differ, and finally validating the settings are consistent before startup.

### Level 1 — Basic

```java
// AuthServerSettingsDemo.java
import org.springframework.security.oauth2.server.authorization.settings.AuthorizationServerSettings;

public class AuthServerSettingsDemo {
    public static void main(String[] args) {
        AuthorizationServerSettings settings = AuthorizationServerSettings.builder()
                .issuer("https://auth.example.com")
                .build();

        System.out.println("Issuer: " + settings.getIssuer());
        System.out.println("Token endpoint: " + settings.getTokenEndpoint());
        System.out.println("JWK Set endpoint: " + settings.getJwkSetEndpoint());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java AuthServerSettingsDemo.java`. Expected output:

```
Issuer: https://auth.example.com
Token endpoint: /oauth2/token
JWK Set endpoint: /oauth2/jwks
```

Endpoint paths default to sensible values; only `issuer` is normally mandatory to set explicitly.

### Level 2 — Intermediate

Task-tracker's authorization server runs behind a reverse proxy that terminates TLS and rewrites the internal application port — a common deployment where the app itself doesn't know its own externally-visible hostname. `issuer` must reflect the *external* address that clients and resource servers actually use, not the internal one.

```java
import org.springframework.security.oauth2.server.authorization.settings.AuthorizationServerSettings;

public class AuthServerSettingsDemo {
    public static void main(String[] args) {
        // The app itself binds to http://internal-host:8080, but the reverse proxy
        // exposes it publicly at https://auth.example.com -- issuer must match the PUBLIC address.
        AuthorizationServerSettings settings = AuthorizationServerSettings.builder()
                .issuer("https://auth.example.com") // NOT "http://internal-host:8080"
                .authorizationEndpoint("/oauth2/authorize")
                .tokenEndpoint("/oauth2/token")
                .tokenRevocationEndpoint("/oauth2/revoke")
                .tokenIntrospectionEndpoint("/oauth2/introspect")
                .oidcUserInfoEndpoint("/userinfo")
                .build();

        System.out.println("Issuer (external, public): " + settings.getIssuer());
        System.out.println("UserInfo endpoint: " + settings.getOidcUserInfoEndpoint());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Issuer (external, public): https://auth.example.com
UserInfo endpoint: /userinfo
```

What changed: `issuer` is now the address the outside world actually reaches this server at, which matters because it's embedded as the `iss` claim in every issued token — a resource server validating a JWT checks that its `iss` claim matches the issuer it expects, and a mismatch (internal vs. external hostname) causes every single token to fail validation.

### Level 3 — Advanced

Production adds a startup-time sanity check confirming the configured issuer is actually reachable and serves valid OIDC discovery metadata at `/.well-known/openid-configuration` — catching a misconfigured reverse proxy or DNS issue before it causes every client in production to fail.

```java
import org.springframework.security.oauth2.server.authorization.settings.AuthorizationServerSettings;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class AuthServerSettingsDemo {

    static void verifyIssuerReachable(AuthorizationServerSettings settings) throws Exception {
        String discoveryUrl = settings.getIssuer() + "/.well-known/openid-configuration";
        HttpClient client = HttpClient.newBuilder().connectTimeout(Duration.ofSeconds(5)).build();
        HttpRequest request = HttpRequest.newBuilder(URI.create(discoveryUrl))
                .timeout(Duration.ofSeconds(5))
                .GET()
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new IllegalStateException(
                    "Issuer misconfigured: " + discoveryUrl + " returned " + response.statusCode()
                    + " -- check reverse proxy / DNS / issuer value before accepting traffic");
        }
        if (!response.body().contains("\"issuer\":\"" + settings.getIssuer() + "\"")) {
            throw new IllegalStateException(
                    "Issuer mismatch: discovery document does not self-report the configured issuer");
        }
    }

    public static void main(String[] args) {
        AuthorizationServerSettings settings = AuthorizationServerSettings.builder()
                .issuer("https://auth.example.com")
                .build();
        System.out.println("In a real deployment, verifyIssuerReachable(settings) would be called");
        System.out.println("during application startup (e.g. an ApplicationRunner bean) to fail fast");
        System.out.println("if the externally-configured issuer doesn't actually resolve correctly.");
    }
}
```

**How to run:** same environment as Level 1; `verifyIssuerReachable` requires network access to a live, deployed authorization server to actually exercise the HTTP call. Expected output:

```
In a real deployment, verifyIssuerReachable(settings) would be called
during application startup (e.g. an ApplicationRunner bean) to fail fast
if the externally-configured issuer doesn't actually resolve correctly.
```

What changed and why it's production-flavored: an issuer misconfiguration is one of the most disruptive possible mistakes for an authorization server — it silently breaks every resource server's token validation at once — so failing fast at startup with a clear error, rather than discovering it via a flood of confused `401` reports after deployment, is a meaningful operational safeguard.

## 6. Walkthrough

Tracing how `issuer` and endpoint paths get used across a full request lifecycle, in execution order:

1. A client application, configured only with the issuer URL `https://auth.example.com`, performs OIDC discovery: `GET https://auth.example.com/.well-known/openid-configuration`.
2. Spring Authorization Server's auto-registered metadata endpoint responds with a JSON document built directly from `AuthorizationServerSettings`: `{"issuer": "https://auth.example.com", "authorization_endpoint": "https://auth.example.com/oauth2/authorize", "token_endpoint": "https://auth.example.com/oauth2/token", "jwks_uri": "https://auth.example.com/oauth2/jwks", ...}`.
3. The client reads this document and now knows exactly where to send the user for login (`authorization_endpoint`) and where to later exchange a code for tokens (`token_endpoint`) — it never needed these paths hardcoded.
4. After a successful grant, the server issues a JWT access token whose payload includes `"iss": "https://auth.example.com"` — the exact `issuer` value from `AuthorizationServerSettings`.
5. A resource server, itself configured (via Spring Security's OAuth2 resource server support) with `issuer-uri: https://auth.example.com`, fetches the same discovery document, extracts `jwks_uri`, downloads the public signing key, and validates the token's signature.
6. As part of validation, the resource server also checks the token's `iss` claim equals its own configured issuer-uri — if the authorization server had been misconfigured with the internal hostname instead of the public one (the mistake Level 2 avoids), this check would fail for every single token, since the value baked into the token wouldn't match what any correctly-configured resource server expects.

```
Client: GET /.well-known/openid-configuration
   |
Server: {issuer, authorization_endpoint, token_endpoint, jwks_uri, ...}  (from AuthorizationServerSettings)
   |
Client uses discovered endpoints for the full authorization code flow
   |
Server issues JWT with "iss": <issuer>
   |
Resource server: fetch jwks_uri -> verify signature -> check iss claim matches its own configured issuer-uri
```

## 7. Gotchas & takeaways

> `issuer` must be the exact, fully-qualified external URL that both clients and resource servers use to reach this server — including scheme (`https://`), with no trailing slash unless every consumer is configured to expect one. A mismatch here, however small, causes silent, total token-validation failure everywhere, since it's embedded into every single token issued.

- Set `issuer` explicitly rather than relying on auto-detection from the current request — auto-detection can easily disagree with the address behind a reverse proxy or CDN, which is exactly the failure mode Level 2 and 3 guard against.
- Endpoint path customization (`authorizationEndpoint`, `tokenEndpoint`, etc.) is mostly useful for avoiding collisions with an existing application's own routes — most deployments never need to change these from their sensible defaults.
- `AuthorizationServerSettings` is a single, server-wide `@Bean` — unlike `RegisteredClient` or `ClientSettings`, there's exactly one of these per running authorization server instance, not one per client.
- OIDC-specific endpoints (`oidcUserInfoEndpoint`, `oidcClientRegistrationEndpoint`) aren't automatically active just because they're configured here — they also require the corresponding OIDC configurer to be enabled in the security filter chain.
- Verify the issuer is reachable and self-consistent (Level 3's pattern) as part of deployment health checks, not just at first setup — DNS, load balancer, or certificate changes down the line can silently break this without any code change at all.
