---
card: spring-authorization-server
gi: 34
slug: oidc-client-registration-endpoint
title: "OIDC client registration endpoint"
---

## 1. What it is

The OIDC Dynamic Client Registration endpoint (`POST /connect/register` to create, `GET /connect/register?client_id=...` to read) lets a client register itself with the authorization server at runtime by sending an HTTP request, instead of an administrator manually inserting a `RegisteredClient` (card 0010) ahead of time. It's implemented internally as `OidcClientRegistrationEndpointFilter`, and — unlike most other endpoints in this section — it is disabled by default and must be explicitly enabled.

## 2. Why & when

Every endpoint covered so far assumes a `RegisteredClient` already exists in the repository (card 0011). That works fine for a fixed set of first-party clients, but breaks down for platforms where third-party developers need to self-service register their own OAuth2 client — think "developer portal, click a button, get a `client_id` and `client_secret` instantly" rather than filing a ticket with an administrator.

Reach for it when:

- Building a public API platform where external developers register their own integrations (a common pattern for SaaS platforms with an app marketplace).
- Implementing automated provisioning — a CI/CD pipeline or infrastructure-as-code tool that needs to create OAuth2 clients programmatically as part of deployment.
- Deciding whether to expose this endpoint at all — for a closed system with a small, known set of internal clients, manual `RegisteredClient` administration (card 0011) is usually simpler and safer than dynamic self-registration.

## 3. Core concept

Think of manual client registration (card 0011) as a bank requiring an in-person branch visit to open an account, versus this endpoint being the bank's self-service online sign-up form. Anyone who fills out the form correctly (a JSON body describing the desired client) walks away with a working account (`client_id` and `client_secret`) immediately — no human in the loop. That convenience is also the risk: an unauthenticated registration endpoint means *anyone* can open an account, which is why production deployments almost always require an initial access token or additional authorization before allowing registration.

```
POST /connect/register
Content-Type: application/json

{
  "client_name": "Weather Widget",
  "redirect_uris": ["https://widget.example.com/callback"],
  "grant_types": ["authorization_code", "refresh_token"],
  "scope": "openid profile weather.read"
}
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A third-party developer posts a registration request and receives client credentials plus a registration access token">
  <rect x="20" y="90" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="120" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Developer / Client</text>

  <rect x="250" y="90" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OidcClientRegistration</text>
  <text x="330" y="128" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">EndpointFilter</text>

  <rect x="480" y="90" width="140" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="113" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">RegisteredClient</text>
  <text x="550" y="128" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">saved</text>

  <line x1="170" y1="105" x2="245" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <text x="205" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">POST registration</text>

  <line x1="410" y1="115" x2="475" y2="115" stroke="#3fb950" stroke-width="1.5"/>

  <line x1="330" y1="140" x2="330" y2="180" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="330" y="195" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">201 Created: client_id, client_secret, registration_access_token</text>
</svg>

The response includes both the new client's credentials and a separate registration access token used to manage that client registration later.

## 5. Runnable example

The scenario: enabling dynamic client registration for a developer portal, growing to restrict who can register clients, and finally to constrain what redirect URIs and scopes self-registered clients are allowed to request.

### Level 1 — Basic

```java
// DynamicRegistrationConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class DynamicRegistrationConfig {

    @Bean
    @Order(1)
    public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
        OAuth2AuthorizationServerConfigurer configurer =
                OAuth2AuthorizationServerConfigurer.authorizationServer();

        http.securityMatcher(configurer.getEndpointsMatcher())
                .with(configurer, authorizationServer -> authorizationServer
                        .oidc(oidc -> oidc.clientRegistrationEndpoint(reg -> {}))); // enables /connect/register

        return http.build();
    }
}
```

**How to run:** add this to a Spring Boot project, then `curl -X POST http://localhost:8080/connect/register -H "Content-Type: application/json" -d '{"client_name":"Weather Widget","redirect_uris":["https://widget.example.com/callback"],"grant_types":["authorization_code"],"scope":"openid weather.read"}'`. Expected output: a `201 Created` JSON body containing a generated `client_id`, `client_secret`, and `registration_access_token`.

### Level 2 — Intermediate

Leaving registration wide open lets anyone create clients, so production requires callers to already hold a valid *initial access token* before they can register — issued out-of-band to trusted developers, not something the registration endpoint itself hands out.

```java
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

public class DynamicRegistrationConfig {

    public SecurityFilterChain configure(HttpSecurity http,
            OAuth2AuthorizationServerConfigurer configurer) throws Exception {

        http.securityMatcher(configurer.getEndpointsMatcher())
                .with(configurer, authorizationServer -> authorizationServer
                        .oidc(oidc -> oidc.clientRegistrationEndpoint(reg -> {})))
                // Require a Bearer token (an initial access token) on the registration endpoint itself.
                .oauth2ResourceServer(resourceServer -> resourceServer.jwt(Customizer.withDefaults()))
                .authorizeHttpRequests(authorize -> authorize
                        .requestMatchers("/connect/register").authenticated()
                        .anyRequest().permitAll());

        return http.build();
    }
}
```

**How to run:** issue an initial access token to a trusted developer out-of-band (e.g. a pre-registered service client using client-credentials grant, card on grant types), then repeat the `curl` call from Level 1 with `-H "Authorization: Bearer <initial-access-token>"`. Expected behavior: requests without a valid bearer token now receive `401 Unauthorized`; requests with one succeed as before.

What changed: registration is no longer anonymous — only holders of a pre-issued initial access token can create new clients, closing off the open-registration abuse vector.

### Level 3 — Advanced

Production also constrains *what* a self-registering client can request — an unconstrained registration lets a malicious caller register a client with an overly broad scope or an attacker-controlled redirect URI, so a `RegisteredClientRepository.save` hook validates and narrows the incoming registration before persisting it.

```java
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;

import java.util.Set;

public class ConstrainedClientRepository implements RegisteredClientRepository {

    private static final Set<String> ALLOWED_SCOPES = Set.of("openid", "profile", "weather.read");
    private final RegisteredClientRepository delegate;

    public ConstrainedClientRepository(RegisteredClientRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public void save(RegisteredClient registeredClient) {
        Set<String> requested = registeredClient.getScopes();
        if (!ALLOWED_SCOPES.containsAll(requested)) {
            throw new IllegalArgumentException("Requested scope exceeds what self-registration allows: " + requested);
        }
        boolean anyInsecureRedirect = registeredClient.getRedirectUris().stream()
                .anyMatch(uri -> !uri.startsWith("https://"));
        if (anyInsecureRedirect) {
            throw new IllegalArgumentException("Self-registered clients must use https redirect URIs");
        }
        delegate.save(registeredClient);
    }

    @Override
    public RegisteredClient findById(String id) { return delegate.findById(id); }

    @Override
    public RegisteredClient findByClientId(String clientId) { return delegate.findByClientId(clientId); }
}
```

**How to run:** wrap the application's real `RegisteredClientRepository` bean with `ConstrainedClientRepository`. Re-run the Level 2 registration request but with `"scope":"openid profile admin.write"`: expect `400 Bad Request` (the exception is translated to an OIDC `invalid_client_metadata` error by the endpoint filter). Re-run with an `http://` redirect URI: same rejection.

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"error":"invalid_client_metadata","error_description":"Requested scope exceeds what self-registration allows: [openid, profile, admin.write]"}
```

What changed and why it's production-flavored: self-service registration now enforces the same security posture (scope allow-listing, HTTPS-only redirects) that a human administrator would apply manually — necessary because dynamic registration removes the human review step entirely.

## 6. Walkthrough

Tracing a client registration request, in execution order:

1. A trusted developer, already holding an initial access token issued out-of-band, sends `POST /connect/register` with a JSON body describing the desired client.
2. `OidcClientRegistrationEndpointFilter` first authenticates the request as a resource-server request (Level 2's bearer check) — if the initial access token is missing or invalid, it responds `401 Unauthorized` immediately, before any client is created.
3. The filter parses the JSON body into an `OidcClientRegistration` object, mapping fields like `redirect_uris`, `grant_types`, and `scope` onto a candidate `RegisteredClient`.
4. It calls `RegisteredClientRepository.save(...)` — in this example, `ConstrainedClientRepository.save` (Level 3) — which validates the requested scopes and redirect URIs before delegating to the real repository.
5. If validation fails, the save throws, and the filter translates that into a `400 Bad Request` with an `invalid_client_metadata` OIDC error body — no client is persisted.
6. If validation passes, the client is saved (persisted the same way as a manually created `RegisteredClient`, card 0011), and the filter generates a `registration_access_token` — a separate, long-lived credential scoped only to managing *this* client's registration (not for obtaining user access tokens).
7. The filter responds `201 Created` with the full client metadata, including the generated `client_id`, `client_secret`, and `registration_access_token`, plus a `registration_client_uri` the developer can later `GET` to read back the current registration.

```
POST /connect/register  (Bearer: initial access token)
   |
authenticate bearer token --fail--> 401 Unauthorized
   |  pass
parse JSON -> candidate RegisteredClient
   |
repository.save(...) --validation fails--> 400 invalid_client_metadata
   |  pass
persist client, generate registration_access_token
   |
201 Created  {client_id, client_secret, registration_access_token, registration_client_uri}
```

Concrete request and response:

```
POST /connect/register HTTP/1.1
Authorization: Bearer <initial-access-token>
Content-Type: application/json

{"client_name":"Weather Widget","redirect_uris":["https://widget.example.com/callback"],"grant_types":["authorization_code"],"scope":"openid weather.read"}

HTTP/1.1 201 Created
Content-Type: application/json

{"client_id":"a1b2c3d4","client_secret":"e5f6g7h8","client_id_issued_at":1752300000,"redirect_uris":["https://widget.example.com/callback"],"grant_types":["authorization_code"],"scope":"openid weather.read","registration_access_token":"reg-9f8e...","registration_client_uri":"https://auth.example.com/connect/register?client_id=a1b2c3d4"}
```

## 7. Gotchas & takeaways

> Leaving `/connect/register` reachable without any authentication requirement (skipping Level 2) means anyone on the internet can mint themselves a valid `client_id`/`client_secret` pair against the authorization server — this endpoint is disabled by default precisely because enabling it carelessly is a common and serious misconfiguration.

- The `registration_access_token` returned in the response is not an access token for user resources — it's a management credential for reading and updating that one client's own registration via `GET`/`PUT` on `registration_client_uri`. Losing it means losing the ability to self-manage that client.
- Always pair dynamic registration with scope and redirect-URI constraints (Level 3) — without them, self-registration is equivalent to letting external parties define their own trust boundaries.
- `client_secret` is only returned once, in the registration response itself — exactly like a manually created client (card 0010), it isn't retrievable again afterward.
- If a registration request is rejected with `invalid_client_metadata`, check the response body's `error_description` first — it's the fastest way to see which specific constraint (scope, redirect URI, grant type) failed.
- For internal-only systems with a small, fixed set of clients, prefer manual `RegisteredClient` administration (card 0011) over enabling this endpoint at all — the operational simplicity of "no dynamic registration surface to secure" often outweighs the convenience.
