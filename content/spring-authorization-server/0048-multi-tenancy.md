---
card: spring-authorization-server
gi: 48
slug: multi-tenancy
title: "Multi-tenancy"
---

## 1. What it is

Multi-tenancy in Spring Authorization Server means running a single authorization server deployment that serves multiple distinct tenants (separate customer organizations, separate brands, or separate environments), each with its own issuer identity, its own registered clients, and often its own branding — rather than deploying an entirely separate server instance per tenant. It's built by combining path- or host-based issuer resolution with tenant-scoped lookups across the repositories already covered (cards 0011, 0017, 0018).

## 2. Why & when

Running one full authorization server per customer is operationally expensive — every tenant needs its own deployment, monitoring, and patching, and that cost scales linearly with customer count. Multi-tenancy inverts this: one running deployment, one codebase, one set of infrastructure, but tenant-scoped data and tenant-specific issuer identities baked into every issued token, so tenants remain cryptographically and logically isolated from each other despite sharing infrastructure.

Reach for multi-tenancy when:

- Building a SaaS product where each customer organization needs its own OAuth2/OIDC issuer identity (their own `iss` claim, sometimes their own JWK signing keys) without provisioning separate infrastructure per customer.
- Supporting multiple brands or products under one company that each need visually and technically distinct authorization experiences (different login pages, different registered client pools) from shared infrastructure.
- Deciding whether multi-tenancy is warranted at all — for a small, fixed number of large enterprise customers, separate deployments per tenant might actually be simpler and offer stronger isolation guarantees; multi-tenancy earns its complexity at meaningfully larger tenant counts.

## 3. Core concept

Think of a single-tenant authorization server as a standalone bank branch — one building, one set of vault combinations, serving one clientele. A multi-tenant authorization server is more like a shared office building with separate, independently-keyed suites for different tenant companies: the building's core infrastructure (elevators, power, security guards at the main entrance — the shared Spring Boot application and database) is one system, but each suite (tenant) has its own lock, its own list of who's allowed in, and its own nameplate on the door — while a visitor to Suite 4B (a request for `tenant-a`'s issuer path) can never accidentally end up in Suite 7A's (`tenant-b`'s) records.

```
https://auth.example.com/tenant-a/oauth2/authorize
https://auth.example.com/tenant-b/oauth2/authorize
   |
AuthorizationServerContext resolves issuer per-request based on the path segment
```

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Requests to different tenant path prefixes resolve to different issuers and are scoped to different tenant data via a shared repository layer">
  <rect x="20" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="48" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/tenant-a/oauth2/authorize</text>

  <rect x="20" y="90" width="160" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">/tenant-b/oauth2/authorize</text>

  <rect x="260" y="55" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TenantAware</text>
  <text x="350" y="96" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">IssuerResolver</text>

  <line x1="180" y1="43" x2="255" y2="75" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="180" y1="113" x2="255" y2="95" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="510" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="585" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">tenant-a clients only</text>

  <rect x="510" y="90" width="150" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="585" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">tenant-b clients only</text>

  <line x1="440" y1="75" x2="505" y2="43" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="440" y1="95" x2="505" y2="113" stroke="#3fb950" stroke-width="1.5"/>
</svg>

The issuer resolved per-request determines both what appears in the token's `iss` claim and which slice of tenant-scoped data the request is allowed to touch.

## 5. Runnable example

The scenario: building a path-based multi-tenant issuer resolver, growing to scope the `RegisteredClientRepository` lookup by resolved tenant so tenants can't see each other's clients, and finally to isolate JWK signing keys per tenant for stronger cryptographic separation.

### Level 1 — Basic

```java
// TenantIssuerResolver.java
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.oauth2.server.authorization.settings.AuthorizationServerSettings;

public class TenantIssuerResolver {

    public String resolveIssuer(HttpServletRequest request) {
        String path = request.getRequestURI(); // e.g. /tenant-a/oauth2/authorize
        String[] segments = path.split("/");
        String tenantId = segments.length > 1 ? segments[1] : "default";
        return "https://auth.example.com/" + tenantId;
    }
}
```

**How to run:** wire this into `AuthorizationServerSettings.Builder.issuer(...)` via a request-aware supplier (the library supports per-request issuer resolution when the authorization server is mounted under a path prefix). Call `GET /tenant-a/.well-known/openid-configuration` and `GET /tenant-b/.well-known/openid-configuration`: expect two different `issuer` values in the returned metadata, each matching the request's own tenant path.

### Level 2 — Intermediate

An issuer resolving correctly per tenant is only half the isolation story — client lookups must also be scoped, or a client registered for `tenant-a` could be looked up (and potentially authenticated against) under `tenant-b`'s issuer.

```java
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;
import org.springframework.security.oauth2.server.authorization.context.AuthorizationServerContextHolder;

public class TenantScopedRegisteredClientRepository implements RegisteredClientRepository {

    private final RegisteredClientRepository delegate; // e.g. JdbcRegisteredClientRepository (card 0047)

    public TenantScopedRegisteredClientRepository(RegisteredClientRepository delegate) {
        this.delegate = delegate;
    }

    @Override
    public void save(RegisteredClient registeredClient) {
        delegate.save(registeredClient);
    }

    @Override
    public RegisteredClient findById(String id) {
        RegisteredClient client = delegate.findById(id);
        return belongsToCurrentTenant(client) ? client : null;
    }

    @Override
    public RegisteredClient findByClientId(String clientId) {
        RegisteredClient client = delegate.findByClientId(clientId);
        return belongsToCurrentTenant(client) ? client : null;
    }

    private boolean belongsToCurrentTenant(RegisteredClient client) {
        if (client == null) return false;
        String currentIssuer = AuthorizationServerContextHolder.getContext().getIssuer();
        String clientTenantId = extractTenantFromClientMetadata(client); // e.g. a custom client setting
        return currentIssuer.endsWith("/" + clientTenantId);
    }

    private String extractTenantFromClientMetadata(RegisteredClient client) {
        return (String) client.getClientSettings().getSetting("tenant_id");
    }
}
```

**How to run:** register a client with `tenant_id=tenant-a` in its client settings, then attempt `findByClientId(...)` for it once under a request resolved to `tenant-a` (expect the client returned) and once under `tenant-b` (expect `null`, causing the authorization request to fail as if the client doesn't exist at all).

What changed: cross-tenant client visibility is now actively prevented at the repository layer — even a client ID guessed or leaked from another tenant is invisible when accessed through the wrong tenant's issuer path, rather than relying on obscurity alone.

### Level 3 — Advanced

For tenants with the strictest isolation requirements (e.g. regulated enterprise customers), even the JWK signing key (card 0021) should be tenant-specific — so a compromise of one tenant's signing key can't be used to forge tokens claiming to be from another tenant, and each tenant could even rotate or revoke their own key independently.

```java
import com.nimbusds.jose.jwk.JWKSet;
import org.springframework.security.oauth2.jwt.NimbusJwtEncoder;
import org.springframework.security.oauth2.server.authorization.context.AuthorizationServerContextHolder;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class TenantAwareJwkSource {

    // In production, load each tenant's key pair from a secrets manager, not memory.
    private final Map<String, JWKSet> tenantKeys = new ConcurrentHashMap<>();

    public void registerTenantKey(String tenantId, JWKSet jwkSet) {
        tenantKeys.put(tenantId, jwkSet);
    }

    public NimbusJwtEncoder encoderForCurrentTenant() {
        String issuer = AuthorizationServerContextHolder.getContext().getIssuer();
        String tenantId = issuer.substring(issuer.lastIndexOf('/') + 1);
        JWKSet jwkSet = tenantKeys.get(tenantId);
        if (jwkSet == null) {
            throw new IllegalStateException("No signing key configured for tenant: " + tenantId);
        }
        return new NimbusJwtEncoder((jwkSelector, context) -> jwkSelector.select(jwkSet));
    }
}
```

**How to run:** register distinct key pairs for `tenant-a` and `tenant-b`, issue a token under each tenant's issuer path, and verify each token's JWK `kid` (key ID, card 0021) differs and each token only validates against its own tenant's published JWK Set endpoint (`/tenant-a/oauth2/jwks` vs `/tenant-b/oauth2/jwks`, card 0030). Attempt to validate a `tenant-a`-issued token against `tenant-b`'s JWK Set: expect signature validation to fail outright.

What changed and why it's production-flavored: tenants are now cryptographically isolated, not just logically separated by database rows — the strongest isolation guarantee available short of fully separate infrastructure, appropriate for customers whose compliance requirements demand it.

## 6. Walkthrough

Tracing a multi-tenant authorization request, in execution order:

1. A client redirects to `GET /tenant-a/oauth2/authorize?client_id=task-tracker&...`.
2. `TenantIssuerResolver` (Level 1) parses the path, resolves the current `AuthorizationServerContext`'s issuer to `https://auth.example.com/tenant-a`, and this context is available to every downstream component processing this request.
3. `TenantScopedRegisteredClientRepository.findByClientId("task-tracker")` (Level 2) looks up the client, then checks `belongsToCurrentTenant(...)` — confirming the stored client's `tenant_id` setting matches `tenant-a`, the tenant resolved from this specific request's path.
4. If the client belongs to a *different* tenant (e.g. it was actually registered under `tenant-b`), the lookup returns `null`, and the authorization endpoint responds as if `client_id` simply doesn't exist — deliberately indistinguishable from a genuinely unregistered client, revealing nothing about cross-tenant existence.
5. Assuming the client resolves correctly for this tenant, the flow proceeds through authentication (potentially against a tenant-specific login page, an extension of card 0042) and consent as normal.
6. When the token is issued, `TenantAwareJwkSource.encoderForCurrentTenant()` (Level 3) selects `tenant-a`'s specific signing key — not a shared, global key — and the token's `iss` claim is set to `https://auth.example.com/tenant-a`.
7. A resource server validating this token later fetches `https://auth.example.com/tenant-a/oauth2/jwks` (card 0030) — tenant-a's own key set — to verify the signature; it can never accidentally validate against another tenant's keys.

```
GET /tenant-a/oauth2/authorize?client_id=task-tracker
   |
resolve issuer = https://auth.example.com/tenant-a
   |
findByClientId("task-tracker") -> belongs to tenant-a? --no--> treat as unknown client
   |  yes
authenticate, consent (tenant-a branded login, card 0042)
   |
issue token: sign with tenant-a's key, iss=".../tenant-a"
   |
resource server validates against https://auth.example.com/tenant-a/oauth2/jwks
```

## 7. Gotchas & takeaways

> A `RegisteredClientRepository.findByClientId` lookup that finds a client but doesn't check tenant ownership before returning it is a cross-tenant data leak — even if every other part of the system is correctly tenant-scoped, this single gap lets `tenant-a` potentially authenticate as or interact with `tenant-b`'s registered client. Always scope every repository lookup by the currently resolved tenant, not just writes.

- Returning `null` (indistinguishable from "client doesn't exist") for a cross-tenant lookup, rather than a distinct "found but wrong tenant" error, avoids leaking even the *existence* of another tenant's client IDs to someone probing the wrong tenant path.
- Multi-tenancy adds a new class of test to prioritize: explicitly verify that tenant A's requests, tokens, and lookups never succeed or leak data under tenant B's context — these tests catch isolation bugs that functional tests of a single tenant in isolation would never surface.
- Shared signing keys across tenants (skipping Level 3) is a legitimate, simpler choice for many products — reserve the added complexity of per-tenant keys for customers whose actual compliance or security requirements demand cryptographic separation, not by default.
- `AuthorizationServerContextHolder` carries the resolved issuer for the duration of the current request — any custom component needing tenant context (client lookups, key selection, claim customization, card 0044) should read it from there rather than re-deriving tenant identity independently, to guarantee consistency across the whole request.
- Path-based tenancy (`/tenant-a/...`) is simpler to operate than host-based tenancy (`tenant-a.auth.example.com`), but host-based tenancy allows each tenant a fully custom domain — choose based on whether tenants need their own branded domain or a shared one with a distinguishing path is acceptable.
