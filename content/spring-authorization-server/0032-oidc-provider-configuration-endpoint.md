---
card: spring-authorization-server
gi: 32
slug: oidc-provider-configuration-endpoint
title: "OIDC provider configuration endpoint"
---

## 1. What it is

The OIDC provider configuration endpoint (`GET /.well-known/openid-configuration`) is OpenID Connect's own discovery document, standardized separately from RFC 8414's OAuth2 metadata (card 0031) even though the two overlap heavily and Spring Authorization Server serves both from the same underlying settings. It's automatically enabled the moment OIDC support is turned on via `.oidc(Customizer.withDefaults())` on `OAuth2AuthorizationServerConfigurer`, and it adds OIDC-specific fields the plain OAuth2 metadata document doesn't have: `userinfo_endpoint`, `id_token_signing_alg_values_supported`, `subject_types_supported`, `scopes_supported` (including the standard OIDC scopes), and `claims_supported`.

## 2. Why & when

OIDC client libraries (as opposed to plain OAuth2 libraries) specifically look for `/.well-known/openid-configuration`, and they rely on OIDC-only fields like `userinfo_endpoint` and `id_token_signing_alg_values_supported` that don't exist in the plain OAuth2 metadata document — pointing an OIDC library at the OAuth2-only document would leave it unable to find the UserInfo endpoint or verify ID token signing algorithm support.

Reach for understanding (and enabling) this endpoint when:

- Building "Sign in with X" using an OIDC-aware client library (most modern ones are), which will specifically look for this document rather than the plain OAuth2 one.
- Adding user identity information (name, email, profile) to a login flow — this requires OIDC, not plain OAuth2, and this document is how compliant clients discover the associated `userinfo_endpoint` (card 0033).
- Debugging an OIDC client that reports it "can't discover the provider" — checking this exact URL directly is the fastest way to see whether OIDC support is even enabled on the server.

## 3. Core concept

If the OAuth2 metadata document (card 0031) is the general company directory, the OIDC provider configuration document is the specialized directory page for a particular department (identity and profile services) that only exists once that department (OIDC support) is actually staffed. It repeats some of the same general information (the issuer, the shared endpoints) but adds department-specific listings — where to fetch someone's profile (`userinfo_endpoint`), what identity-proof formats are accepted (`id_token_signing_alg_values_supported`), and what personal details can be requested (`claims_supported`).

```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/oauth2/authorize",
  "token_endpoint": "https://auth.example.com/oauth2/token",
  "userinfo_endpoint": "https://auth.example.com/userinfo",
  "jwks_uri": "https://auth.example.com/oauth2/jwks",
  "scopes_supported": ["openid", "profile", "email", "tasks.read", "tasks.write"],
  "response_types_supported": ["code"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"],
  "claims_supported": ["sub", "iss", "aud", "exp", "iat", "name", "email"]
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OIDC provider configuration extends OAuth2 metadata with identity-specific fields">
  <rect x="20" y="60" width="260" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="85" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OAuth2 metadata (RFC 8414)</text>
  <text x="150" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">issuer, endpoints,</text>
  <text x="150" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">grant/response types</text>

  <rect x="330" y="30" width="290" height="150" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="475" y="55" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">+ OIDC-only fields</text>
  <text x="475" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">userinfo_endpoint</text>
  <text x="475" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">id_token_signing_alg_values_supported</text>
  <text x="475" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">subject_types_supported</text>
  <text x="475" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">claims_supported</text>
  <text x="475" y="160" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">scopes_supported (incl. openid)</text>

  <line x1="280" y1="105" x2="325" y2="105" stroke="#3fb950" stroke-width="2"/>
</svg>

The OIDC document is a superset — same shared foundation, plus identity-specific fields the plain OAuth2 document omits.

## 5. Runnable example

The scenario: an OIDC client discovering the provider, then using the discovered `userinfo_endpoint`, and finally verifying the server actually supports the specific scopes and signing algorithm the client requires before relying on them.

### Level 1 — Basic

```java
// OidcDiscoveryDemo.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class OidcDiscoveryDemo {
    public static void main(String[] args) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(
                URI.create("https://auth.example.com/.well-known/openid-configuration"))
                .GET().build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body (truncated): " + response.body().substring(0, Math.min(150, response.body().length())));
    }
}
```

**How to run:** requires a live authorization server with OIDC support enabled; run via `java OidcDiscoveryDemo.java`. Expected output (truncated):

```
Status: 200
Body (truncated): {"issuer":"https://auth.example.com","authorization_endpoint":"https://auth.example.com/oauth2/authorize","token_endpoint":"https:...
```

### Level 2 — Intermediate

The client extracts `userinfo_endpoint` from the discovery document and uses it to fetch the logged-in user's profile after obtaining an access token with the `openid` scope — the exact next step a "Sign in with X" integration takes right after login completes.

```java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class OidcDiscoveryDemo {

    static String discoverUserInfoEndpoint(String issuer) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(
                URI.create(issuer + "/.well-known/openid-configuration")).GET().build();
        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode metadata = new ObjectMapper().readTree(response.body());
        return metadata.get("userinfo_endpoint").asText();
    }

    static String fetchUserProfile(String userInfoEndpoint, String accessToken) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create(userInfoEndpoint))
                .header("Authorization", "Bearer " + accessToken)
                .GET().build();
        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception {
        String userInfoEndpoint = discoverUserInfoEndpoint("https://auth.example.com");
        System.out.println("Discovered userinfo_endpoint: " + userInfoEndpoint);
        // fetchUserProfile(userInfoEndpoint, accessToken) would be called next with a real access token
    }
}
```

**How to run:** same environment as Level 1. Expected output:

```
Discovered userinfo_endpoint: https://auth.example.com/userinfo
```

What changed: the client no longer needs `userinfo_endpoint` hardcoded anywhere — it's discovered fresh from the same document that already provided the authorization and token endpoints, keeping the entire OIDC integration configured from a single issuer URL.

### Level 3 — Advanced

Production verifies the server's advertised capabilities actually cover what the client relies on *before* attempting login — specifically, that `openid` is in `scopes_supported` and the client's expected signing algorithm is in `id_token_signing_alg_values_supported` — failing with a clear configuration error rather than a confusing runtime failure deep into token validation.

```java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class OidcCapabilityCheck {

    static void verifyOidcCapabilities(String issuer, String requiredAlg) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(
                URI.create(issuer + "/.well-known/openid-configuration")).GET().build();
        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode metadata = new ObjectMapper().readTree(response.body());

        boolean supportsOpenidScope = false;
        for (JsonNode scope : metadata.path("scopes_supported")) {
            if ("openid".equals(scope.asText())) { supportsOpenidScope = true; break; }
        }
        if (!supportsOpenidScope) {
            throw new IllegalStateException("Server does not advertise 'openid' scope support -- OIDC is not enabled");
        }

        boolean supportsRequiredAlg = false;
        for (JsonNode alg : metadata.path("id_token_signing_alg_values_supported")) {
            if (requiredAlg.equals(alg.asText())) { supportsRequiredAlg = true; break; }
        }
        if (!supportsRequiredAlg) {
            throw new IllegalStateException(
                    "Server does not support required ID token signing algorithm: " + requiredAlg);
        }

        System.out.println("OIDC capability check passed: openid scope and " + requiredAlg + " both supported.");
    }

    public static void main(String[] args) throws Exception {
        verifyOidcCapabilities("https://auth.example.com", "RS256");
    }
}
```

**How to run:** same environment as Level 1, against a properly OIDC-enabled server. Expected output:

```
OIDC capability check passed: openid scope and RS256 both supported.
```

What changed and why it's production-flavored: verifying capabilities up front turns a potential deep, confusing runtime failure (an ID token signature check silently failing because the algorithm was never actually supported) into an immediate, clear, actionable error at integration setup time — exactly the kind of check worth running once during deployment rather than discovering the hard way in production.

## 6. Walkthrough

Tracing an OIDC login flow's use of this document end to end, in execution order:

1. An OIDC client library is configured with `issuer: https://auth.example.com` and calls `GET /.well-known/openid-configuration` during setup.
2. It reads `authorization_endpoint`, `token_endpoint`, `jwks_uri`, and `userinfo_endpoint` from the response, and confirms (Level 3) that `openid` is supported and its expected `id_token_signing_alg_values_supported` entry is present.
3. The user completes a standard authorization code flow (card 0026/0027), requesting `scope=openid profile email` — because `openid` is present, the server additionally issues an ID token alongside the access token (card 0016).
4. The client verifies the ID token's signature using the key fetched from `jwks_uri` (card 0030) and checks its standard claims (`iss`, `aud`, `exp`) — this proves the user's identity as vouched for directly by the authorization server.
5. The client then calls the discovered `userinfo_endpoint` (Level 2) with `Authorization: Bearer <access_token>` to fetch additional profile claims beyond what's in the (deliberately compact) ID token — the next card covers exactly what that call and its response look like.
6. The client now has both a verified identity (from the ID token) and profile details (from UserInfo), completing the "Sign in with X" experience entirely from information first discovered via this one document.

```
GET /.well-known/openid-configuration
   |
{issuer, endpoints, userinfo_endpoint, scopes_supported, id_token_signing_alg_values_supported, ...}
   |
verify openid + signing alg supported (fail fast if not)
   |
authorization code flow with scope=openid ... --> ID token + access token issued
   |
verify ID token signature (via jwks_uri) --> call userinfo_endpoint (Bearer access_token) --> profile claims
```

## 7. Gotchas & takeaways

> `/.well-known/openid-configuration` only exists (returns something other than `404`) once OIDC support is explicitly enabled on the authorization server configurer — plain OAuth2-only servers correctly don't serve this document, since serving it without genuine OIDC support would mislead OIDC-aware client libraries about capabilities the server doesn't actually have.

- Point OIDC client libraries at `/.well-known/openid-configuration`, not the plain OAuth2 metadata document (card 0031) — libraries that specifically expect OIDC fields (`userinfo_endpoint`, `id_token_signing_alg_values_supported`) will fail to configure correctly against the wrong document.
- `scopes_supported` in this document should include `openid` and any additional standard OIDC scopes (`profile`, `email`) the server recognizes — but it's still each individual `RegisteredClient`'s own scope list (card 0014) that determines what that specific client can actually request.
- Don't skip capability verification (Level 3) for integrations you don't control end-to-end — a third-party or partner authorization server advertising incomplete or unexpected OIDC support is far better caught at setup time than during a live login attempt.
- The overlap between this document and the plain OAuth2 metadata document (card 0031) is intentional and specified — both exist because they're governed by separate specifications (OIDC Discovery vs. RFC 8414) with separate adoption timelines, not because one supersedes the other.
- When both are enabled, they must stay consistent (same issuer, same shared endpoints) — since both are generated from the same underlying `AuthorizationServerSettings` and OIDC configuration, Spring Authorization Server keeps this automatic, but a custom override of either document independently would be a correctness risk worth avoiding.
