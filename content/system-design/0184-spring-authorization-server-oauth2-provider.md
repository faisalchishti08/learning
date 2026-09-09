---
card: system-design
gi: 184
slug: spring-authorization-server-oauth2-provider
title: Spring Authorization Server (OAuth2 provider)
---

## 1. What it is

**Spring Authorization Server** is a framework for building your own [OAuth2](0176-oauth2-openid-connect.md) authorization server in Java — the role played by services like Google or GitHub in a "Sign in with X" flow — issuing access tokens, ID tokens, and refresh tokens to registered client applications after a user authenticates and approves the requested scopes. Instead of your organization depending on a third-party identity provider, this lets you run that same protocol yourself, for your own users and your own client applications.

## 2. Why & when

An organization with its own user base, needing to let multiple internal or partner applications authenticate users and access APIs on their behalf, needs something playing the authorization server role in the OAuth2 flow: issuing authorization codes, exchanging them for tokens, and validating client credentials. Building this correctly from scratch means implementing the authorization code flow, token issuance and signing, and client registration securely — Spring Authorization Server provides all of this as a configurable, standards-compliant framework. Use it when you need to be your own OAuth2/OIDC provider, rather than delegating identity to an external provider (Google, Okta, Auth0) or building JWT issuance and validation by hand.

## 3. Core concept

- **`RegisteredClient`:** configuration for each client application allowed to request tokens — its client ID, secret, allowed grant types (authorization code, client credentials), redirect URIs, and allowed scopes.
- **Authorization endpoint (`/oauth2/authorize`):** where the user is redirected to log in and approve the requested scopes; on approval, the server issues a short-lived authorization code and redirects back to the client's registered redirect URI.
- **Token endpoint (`/oauth2/token`):** where the client exchanges an authorization code (plus its client secret) for an access token, refresh token, and (for OIDC) an ID token.
- **JWK (JSON Web Key) endpoint (`/oauth2/jwks`):** exposes the server's public signing keys, so any resource server can independently verify tokens' signatures without contacting the authorization server on every request — exactly what a [resource server](0183-spring-security-resource-server-jwt.md) configuration points at.
- **Grant types beyond authorization code:** `client_credentials` (for pure service-to-service authentication, with no user involved at all) is also commonly configured for machine-to-machine API access.

## 4. Diagram

```
   Spring Authorization Server (your own OAuth2 provider)

   RegisteredClient: {id: "mobile-app", secret: "...", redirectUris: [...], scopes: [read, write]}

   user -> /oauth2/authorize (login + consent screen, served by YOUR authorization server)
                |
                v
   authorization code issued -> redirected back to client's redirect URI
                |
                v
   client -> POST /oauth2/token (code + client_id + client_secret)
                |
                v
   access_token + id_token + refresh_token issued, signed with YOUR server's private key
                |
                v
   any resource server -> GET /oauth2/jwks -> fetches YOUR public key -> verifies tokens independently
```
*Caption: your own server plays every role a third-party provider normally would — issuing, signing, and exposing the public key needed to verify its own tokens.*

## 5. Runnable example

This models the client registration, authorization-code, and token-issuance flow in-process; the "How to run" note shows the real Spring configuration.

**Level 1 — Basic.** Register a client and validate its credentials at the token endpoint.

**Level 2 — Issue an authorization code, then exchange it for tokens.** Model the full authorization-code grant.

**Level 3 — Support a second grant type, `client_credentials`, for pure service-to-service auth with no user involved.**

```java
// AuthorizationServerDemo.java
import java.util.*;

public class AuthorizationServerDemo {

    // Level 1: RegisteredClient - configuration for each allowed client application.
    static class RegisteredClient {
        final String clientId, clientSecret;
        final Set<String> allowedScopes;
        RegisteredClient(String clientId, String clientSecret, Set<String> allowedScopes) {
            this.clientId = clientId; this.clientSecret = clientSecret; this.allowedScopes = allowedScopes;
        }
    }

    static Map<String, RegisteredClient> registeredClients = Map.of(
        "mobile-app", new RegisteredClient("mobile-app", "mobile-secret", Set.of("orders.read", "orders.write")),
        "reporting-service", new RegisteredClient("reporting-service", "reporting-secret", Set.of("orders.read"))
    );

    static Map<String, String> issuedCodes = new HashMap<>(); // code -> username, single-use

    // Level 2: /oauth2/authorize - user approves, server issues a short-lived authorization code.
    static String authorize(String username, String clientId, Set<String> requestedScopes) {
        RegisteredClient client = registeredClients.get(clientId);
        if (!client.allowedScopes.containsAll(requestedScopes)) {
            throw new SecurityException("requested scopes exceed what this client is registered for");
        }
        String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
        issuedCodes.put(code, username);
        System.out.println("  user " + username + " approved " + requestedScopes + " for client " + clientId + " -> code issued");
        return code;
    }

    // Level 2: /oauth2/token - authorization_code grant.
    static String tokenEndpointAuthCodeGrant(String code, String clientId, String clientSecret) {
        RegisteredClient client = registeredClients.get(clientId);
        if (client == null || !client.clientSecret.equals(clientSecret)) {
            throw new SecurityException("invalid client credentials");
        }
        String username = issuedCodes.remove(code);
        if (username == null) throw new SecurityException("invalid or already-used authorization code");
        return "access-token-for-" + username + "-via-" + clientId;
    }

    // Level 3: /oauth2/token - client_credentials grant, NO user involved at all (pure service-to-service).
    static String tokenEndpointClientCredentialsGrant(String clientId, String clientSecret) {
        RegisteredClient client = registeredClients.get(clientId);
        if (client == null || !client.clientSecret.equals(clientSecret)) {
            throw new SecurityException("invalid client credentials");
        }
        return "access-token-for-service-" + clientId; // note: no username at all in this grant type
    }

    public static void main(String[] args) {
        // Level 1 & 2: authorization_code grant - a user-facing mobile app.
        String code = authorize("alice", "mobile-app", Set.of("orders.read"));
        String accessToken = tokenEndpointAuthCodeGrant(code, "mobile-app", "mobile-secret");
        System.out.println("issued access token: " + accessToken);

        // Reusing the same code fails - single-use, exactly as in a real authorization server.
        try {
            tokenEndpointAuthCodeGrant(code, "mobile-app", "mobile-secret");
        } catch (SecurityException e) {
            System.out.println("reuse rejected: " + e.getMessage());
        }

        // A client requesting a scope it is NOT registered for.
        try {
            authorize("alice", "reporting-service", Set.of("orders.write"));
        } catch (SecurityException e) {
            System.out.println("over-broad scope request rejected: " + e.getMessage());
        }

        // Level 3: client_credentials grant - pure service-to-service, no end user at all.
        String serviceToken = tokenEndpointClientCredentialsGrant("reporting-service", "reporting-secret");
        System.out.println("issued service-to-service token: " + serviceToken);
    }
}
```

**How to run:** save as `AuthorizationServerDemo.java`, then run `java AuthorizationServerDemo.java`. (Real Spring Authorization Server: add `spring-boot-starter-oauth2-authorization-server`, define `RegisteredClient` beans via `RegisteredClientRepository`, and Spring exposes the full `/oauth2/authorize`, `/oauth2/token`, and `/oauth2/jwks` endpoints automatically, following the actual OAuth2/OIDC specification.)

## 6. Walkthrough

1. `authorize("alice", "mobile-app", Set.of("orders.read"))` looks up `mobile-app`'s `RegisteredClient`, confirms `allowedScopes` (`{"orders.read", "orders.write"}`) contains the requested `{"orders.read"}`, then generates and stores a single-use code mapped to `"alice"`.
2. `tokenEndpointAuthCodeGrant(code, "mobile-app", "mobile-secret")` first validates the client's secret against the registered one (matches), then calls `issuedCodes.remove(code)`, which both retrieves `"alice"` and deletes the code entry, and returns a synthetic access token string incorporating both the username and the client ID.
3. The second call with the *same* code finds `issuedCodes.remove(code)` now returns `null` (already removed in step 2), so it throws a `SecurityException` for an invalid or already-used code — correctly enforcing single-use, exactly as in a real authorization server's code exchange.
4. `authorize("alice", "reporting-service", Set.of("orders.write"))` looks up `reporting-service`'s registered scopes, which are only `{"orders.read"}`; since this does not contain the requested `"orders.write"`, `allowedScopes.containsAll(requestedScopes)` is false, and the method throws before ever issuing a code — a client can never be granted a scope it was not explicitly registered for, regardless of what the user might try to approve.
5. `tokenEndpointClientCredentialsGrant("reporting-service", "reporting-secret")` validates the client's secret the same way as before, but note it never involves `issuedCodes` or any username at all — it returns a token directly from just the client's own credentials, modeling the `client_credentials` grant's defining property: it authenticates a *service*, not a *user*.

## 7. Gotchas & takeaways

> Gotcha: registering a client with an overly broad set of allowed scopes "just in case it needs them later" defeats the purpose of scope restriction entirely — if `reporting-service` were registered with `orders.write` even though it never legitimately needs to write orders, a compromise of that service's credentials would grant far more access than the service actually requires; register each client with only the scopes it genuinely needs.

- Spring Authorization Server lets an organization run its own OAuth2/OIDC provider, issuing tokens for its own registered client applications.
- Every client is registered with an explicit, limited set of allowed scopes, and a request for a broader scope than that is rejected before a code is even issued.
- The `client_credentials` grant authenticates a service directly, with no end user or authorization code involved at all, for machine-to-machine API access.
- Related concepts: [OAuth2 & OpenID Connect](0176-oauth2-openid-connect.md) (the protocol this framework implements the provider side of), [Spring Security resource server (JWT)](0183-spring-security-resource-server-jwt.md) (the service that validates the tokens this server issues), [JWT structure & validation](0177-jwt-structure-validation.md) (the format the issued tokens actually use).
