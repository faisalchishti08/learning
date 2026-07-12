---
card: spring-authorization-server
gi: 31
slug: oauth2-authorization-server-metadata-endpoint
title: "OAuth2 authorization server metadata endpoint"
---

## 1. What it is

The OAuth2 authorization server metadata endpoint (`GET /.well-known/oauth-authorization-server`, RFC 8414) publishes a single JSON document describing the server's capabilities: its issuer, every protocol endpoint's full URL (authorization, token, introspection, revocation, JWK Set), which grant types and response types it supports, which client authentication methods it accepts, and more. It's generated directly from the `AuthorizationServerSettings` bean (card 0025), so it's always automatically consistent with however the server is actually configured — there's no separate document to keep in sync by hand.

## 2. Why & when

Without this endpoint, every client integrating with an authorization server would need its endpoint URLs and capabilities hardcoded or manually configured — brittle, and a real problem the moment any URL changes. RFC 8414 metadata exists so a client (or its OAuth2 library) can be configured with nothing more than the issuer URL and discover everything else automatically, which is exactly what libraries like Spring Security's own OAuth2/OIDC client support do.

Reach for understanding this endpoint (you rarely call it manually) whenever:

- Configuring any OAuth2 client library — most modern libraries accept just an issuer URL and perform this discovery themselves.
- Debugging why a client library "can't find" the token or authorization endpoint — fetching this URL directly is the fastest way to confirm what the server is actually advertising versus what the client expects.
- Auditing what an authorization server supports (which grant types, which client auth methods) without needing source-level access to its configuration.

## 3. Core concept

Think of this endpoint as a company's public "how to reach us" directory page — rather than every visitor needing separately-distributed instructions for where the front desk, the mailroom, and the loading dock are, they all just check the one published directory, which the company keeps automatically up to date as departments move. Any client that only knows the company's main address (the issuer) can find every other detail by checking this one page first.

```json
{
  "issuer": "https://auth.example.com",
  "authorization_endpoint": "https://auth.example.com/oauth2/authorize",
  "token_endpoint": "https://auth.example.com/oauth2/token",
  "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post", "private_key_jwt"],
  "jwks_uri": "https://auth.example.com/oauth2/jwks",
  "response_types_supported": ["code"],
  "grant_types_supported": ["authorization_code", "client_credentials", "refresh_token", "urn:ietf:params:oauth:grant-type:device_code"],
  "revocation_endpoint": "https://auth.example.com/oauth2/revoke",
  "introspection_endpoint": "https://auth.example.com/oauth2/introspect",
  "code_challenge_methods_supported": ["S256"]
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client discovers every endpoint and capability from one metadata document">
  <rect x="20" y="75" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client (issuer URL only)</text>

  <rect x="240" y="75" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GET /.well-known/oauth-authorization-server</text>

  <rect x="460" y="30" width="160" height="140" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="540" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">issuer</text>
  <text x="540" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">authorization_endpoint</text>
  <text x="540" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">token_endpoint</text>
  <text x="540" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">jwks_uri</text>
  <text x="540" y="135" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">grant_types_supported</text>
  <text x="540" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">...</text>

  <line x1="200" y1="100" x2="235" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="420" y1="100" x2="455" y2="100" stroke="#3fb950" stroke-width="2"/>
</svg>

One document, generated straight from `AuthorizationServerSettings`, is enough to fully configure a client.

## 5. Runnable example

The scenario: a client fetching metadata to self-configure, then checking supported capabilities before attempting a flow, and finally validating a server's metadata for internal consistency as part of a deployment health check.

### Level 1 — Basic

```java
// MetadataDemo.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class MetadataDemo {
    public static void main(String[] args) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(
                URI.create("https://auth.example.com/.well-known/oauth-authorization-server"))
                .GET().build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body (truncated): " + response.body().substring(0, Math.min(150, response.body().length())));
    }
}
```

**How to run:** requires a live authorization server; run via `java MetadataDemo.java`. Expected output (truncated):

```
Status: 200
Body (truncated): {"issuer":"https://auth.example.com","authorization_endpoint":"https://auth.example.com/oauth2/authorize","token_endpoint":"https://auth...
```

### Level 2 — Intermediate

A client library should check `grant_types_supported` and `code_challenge_methods_supported` *before* attempting a flow, so it can fail with a clear, actionable error instead of a confusing runtime rejection deep into the protocol exchange.

```java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class MetadataDemo {

    static void verifyServerSupportsDeviceFlow(String issuer) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(
                URI.create(issuer + "/.well-known/oauth-authorization-server")).GET().build();
        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        JsonNode metadata = new ObjectMapper().readTree(response.body());
        boolean supportsDeviceFlow = false;
        for (JsonNode grantType : metadata.path("grant_types_supported")) {
            if ("urn:ietf:params:oauth:grant-type:device_code".equals(grantType.asText())) {
                supportsDeviceFlow = true;
                break;
            }
        }

        if (!supportsDeviceFlow) {
            throw new IllegalStateException(
                    "This authorization server does not advertise device_code grant support; "
                    + "cannot proceed with device flow login.");
        }
        System.out.println("Server confirmed to support device authorization grant flow.");
    }

    public static void main(String[] args) throws Exception {
        verifyServerSupportsDeviceFlow("https://auth.example.com");
    }
}
```

**How to run:** same environment as Level 1, against a server with device flow enabled (card 0036). Expected output:

```
Server confirmed to support device authorization grant flow.
```

What changed: instead of blindly attempting `POST /oauth2/device_authorization` and getting a confusing generic error if the server doesn't actually support it, the client checks metadata first and fails with a clear, specific message naming exactly what's missing.

### Level 3 — Advanced

An operations team adds a deployment-time health check that validates the metadata document is internally consistent — every advertised endpoint URL actually starts with the advertised issuer, and required fields per RFC 8414 are present — catching configuration drift (e.g. a reverse-proxy change that only partially updated `AuthorizationServerSettings`) before it reaches production traffic.

```java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;

public class MetadataHealthCheck {

    static List<String> validate(String issuer) throws Exception {
        List<String> problems = new ArrayList<>();
        HttpRequest request = HttpRequest.newBuilder(
                URI.create(issuer + "/.well-known/oauth-authorization-server")).GET().build();
        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            problems.add("metadata endpoint returned status " + response.statusCode());
            return problems;
        }

        JsonNode metadata = new ObjectMapper().readTree(response.body());
        String[] requiredFields = {"issuer", "authorization_endpoint", "token_endpoint", "jwks_uri"};
        for (String field : requiredFields) {
            if (!metadata.has(field)) {
                problems.add("missing required field: " + field);
            }
        }

        if (metadata.has("issuer") && !issuer.equals(metadata.get("issuer").asText())) {
            problems.add("issuer mismatch: expected " + issuer + " but got " + metadata.get("issuer").asText());
        }

        for (String endpointField : List.of("authorization_endpoint", "token_endpoint", "jwks_uri")) {
            if (metadata.has(endpointField) && !metadata.get(endpointField).asText().startsWith(issuer)) {
                problems.add(endpointField + " does not start with the advertised issuer -- possible proxy misconfiguration");
            }
        }

        return problems;
    }

    public static void main(String[] args) throws Exception {
        List<String> problems = validate("https://auth.example.com");
        System.out.println(problems.isEmpty() ? "Metadata consistent, all checks passed." : "Problems: " + problems);
    }
}
```

**How to run:** same environment as Level 1; run as part of a deployment smoke test or scheduled health check. Expected output against a correctly-configured server:

```
Metadata consistent, all checks passed.
```

What changed and why it's production-flavored: this is the same class of issuer-consistency check introduced in card 0025, applied here to the *entire* metadata document rather than just the issuer field alone — catching partial misconfigurations (e.g. a proxy that rewrites the issuer but not every individual endpoint URL) that would otherwise silently break specific flows while others kept working, making the bug much harder to spot.

## 6. Walkthrough

Tracing how a real OAuth2 client library uses this endpoint during its own setup, in execution order:

1. An application developer configures their client library with only `issuer: https://auth.example.com` — no endpoint URLs, no supported-methods lists.
2. On startup (or lazily, on first use), the library calls `GET https://auth.example.com/.well-known/oauth-authorization-server`.
3. Spring Authorization Server's metadata endpoint filter builds the response directly from the running `AuthorizationServerSettings` bean and each `RegisteredClient`-independent, server-wide capability list, returning `200 OK` with the JSON body shown in Part 3.
4. The client library parses this once, caches it, and from this point on uses `authorization_endpoint` for the login redirect, `token_endpoint` for code exchange, and `jwks_uri` (indirectly, via its own JWT decoder setup, card 0030) for signature verification — all derived, never hardcoded.
5. If the developer later points the same client at a different authorization server (e.g. switching from a staging to a production issuer), no client code changes are needed — the new issuer's metadata document is fetched and used instead, and every endpoint URL updates automatically.

```
Client configured with: issuer = https://auth.example.com
   |
GET /.well-known/oauth-authorization-server
   |
{issuer, authorization_endpoint, token_endpoint, jwks_uri, grant_types_supported, ...}
   |
client derives every URL and capability from this ONE document, caches it, never hardcodes endpoints
```

## 7. Gotchas & takeaways

> This metadata document is generated live from `AuthorizationServerSettings` — if that bean is misconfigured (wrong issuer, wrong endpoint paths), the metadata document faithfully reflects the *mistake*, not the intended configuration. Fixing a broken deployment means fixing the settings bean, not the metadata endpoint itself, which has no independent configuration of its own.

- This endpoint is unauthenticated and public by design, same as the JWK Set endpoint (card 0030) — it describes capabilities, not secrets, and gating it would break automatic client configuration for no security benefit.
- `grant_types_supported` and `token_endpoint_auth_methods_supported` describe what the *server* supports overall — they don't reflect what any particular `RegisteredClient` is individually configured for (card 0015); a client still gets `unauthorized_client` if it attempts a grant type the server supports in general but that specific client isn't registered for.
- RFC 8414's `.well-known/oauth-authorization-server` and OIDC's `.well-known/openid-configuration` (next card) are two related but distinct discovery documents — a server can support both, and OIDC clients specifically should be pointed at the OIDC-flavored document.
- Path placement of the well-known URI matters: for a non-root issuer, the well-known segment is inserted after the host but before the issuer's own path, per RFC 8414 — a common source of 404s when adopting a non-root issuer for the first time.
- Include a metadata consistency check (Level 3) in deployment health checks, not just manual, one-off debugging — configuration drift between an issuer setting and a reverse proxy's actual routing is exactly the kind of subtle bug that benefits from automated, repeated verification.
