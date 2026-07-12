---
card: spring-authorization-server
gi: 39
slug: client-credentials-grant
title: "Client credentials grant"
---

## 1. What it is

The client credentials grant (`grant_type=client_credentials` at `POST /oauth2/token`) is the OAuth2 flow for machine-to-machine authentication — there's no user involved at all. A client authenticates directly with its own `client_id`/`client_secret` and receives an access token representing *the client itself*, not any particular person.

## 2. Why & when

Every flow covered so far exists to get a token on behalf of a *user* — someone logs in, consents, and the resulting token represents them. But a nightly batch job, a backend service calling another backend service, or a CI pipeline hitting an internal API has no user to redirect to a login page; it needs to prove *its own* identity and be granted access based on what that service is allowed to do, independent of any human.

Reach for client credentials when:

- Building service-to-service calls inside a backend — a reporting service calling an inventory API on a schedule, with no user session involved.
- Authenticating a CI/CD pipeline or automation script that needs to call a protected API as itself.
- Deciding between this and authorization code — if there's a human whose data or consent matters, use authorization code with PKCE (card 0038); if the caller *is* the identity being authenticated, use client credentials.

## 3. Core concept

Think of authorization code (card 0038) as a guest checking into a hotel with their own ID, and client credentials as a delivery company's driver badging into a building's loading dock with the company's own corporate badge — no guest involved, just the company proving *it* is who it says it is, and getting access scoped to what that company (not any individual driver) is contracted to do. The badge reader (the token endpoint) doesn't care who's physically holding the badge; it only verifies the badge itself is valid and issues access accordingly.

```
POST /oauth2/token
    grant_type=client_credentials
    client_id=reporting-service
    client_secret=***
    scope=inventory.read
```

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client authenticates directly with the token endpoint using its own credentials and receives a token with no user involved">
  <rect x="20" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Service A</text>
  <text x="100" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(client_id + secret)</text>

  <rect x="240" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Token Endpoint</text>
  <text x="320" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no redirect, no login</text>

  <rect x="460" y="70" width="140" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="530" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Service B</text>
  <text x="530" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(protected API)</text>

  <line x1="180" y1="100" x2="235" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <text x="207" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. POST /token</text>

  <line x1="180" y1="115" x2="235" y2="115" stroke="#3fb950" stroke-width="1.5"/>
  <text x="207" y="127" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">2. access_token</text>

  <line x1="180" y1="60" x2="530" y2="60" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="530" y1="60" x2="530" y2="65" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arrow)"/>
  <text x="355" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">3. Bearer access_token -&gt; call Service B directly</text>
</svg>

The whole exchange is a single, direct request-response — there is no redirect, no browser, and no user session anywhere in the flow.

## 5. Runnable example

The scenario: a reporting service authenticating itself to call an inventory API, growing to cache the token instead of fetching a new one per call, and finally to handle token refresh and scope-based authorization on the receiving side.

### Level 1 — Basic

```java
// ClientCredentialsCaller.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class ClientCredentialsCaller {

    private final HttpClient client = HttpClient.newHttpClient();

    public String fetchToken(String clientId, String clientSecret, String scope) throws Exception {
        String credentials = Base64.getEncoder().encodeToString((clientId + ":" + clientSecret).getBytes());

        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString("grant_type=client_credentials&scope=" + scope))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }

    public static void main(String[] args) throws Exception {
        String tokenResponse = new ClientCredentialsCaller()
                .fetchToken("reporting-service", "secret", "inventory.read");
        System.out.println(tokenResponse);
    }
}
```

**How to run:** register a `RegisteredClient` named `reporting-service` with `authorizationGrantTypes(CLIENT_CREDENTIALS)` and scope `inventory.read`, run a Spring Authorization Server locally, then `java ClientCredentialsCaller.java`. Expected output: a JSON body with `access_token`, `token_type`, and `expires_in` — no `refresh_token`, since there's no user session to keep alive.

### Level 2 — Intermediate

Fetching a new token on every single outbound call is wasteful — access tokens are valid for a while (`expires_in`), so a real service caches the token and only re-fetches once it's actually expired.

```java
import java.time.Instant;

public class CachingTokenProvider {

    private final ClientCredentialsCaller caller = new ClientCredentialsCaller();
    private String cachedToken;
    private Instant expiresAt = Instant.EPOCH;

    public String getToken(String clientId, String clientSecret, String scope) throws Exception {
        if (Instant.now().isBefore(expiresAt.minusSeconds(30))) {
            return cachedToken; // reuse, with a 30s safety margin before real expiry
        }
        String responseBody = caller.fetchToken(clientId, clientSecret, scope);
        // In a real implementation, parse expires_in and access_token out of the JSON body here.
        cachedToken = extractAccessToken(responseBody);
        expiresAt = Instant.now().plusSeconds(extractExpiresIn(responseBody));
        return cachedToken;
    }

    private String extractAccessToken(String json) {
        int start = json.indexOf("\"access_token\":\"") + 17;
        int end = json.indexOf("\"", start);
        return json.substring(start, end);
    }

    private long extractExpiresIn(String json) {
        int start = json.indexOf("\"expires_in\":") + 13;
        int end = json.indexOf(",", start);
        return Long.parseLong(json.substring(start, end).trim());
    }
}
```

**How to run:** call `getToken(...)` repeatedly in a loop — the first call hits the network, subsequent calls within the token's lifetime return instantly from the cache. Expected behavior: only one `POST /oauth2/token` request fires per token lifetime, no matter how many times `getToken` is called in that window.

What changed: the service now avoids unnecessary token endpoint traffic entirely, which matters at scale — a service calling downstream APIs thousands of times per minute must not re-authenticate on every single call.

### Level 3 — Advanced

Production also needs the *receiving* service to enforce scopes correctly — `reporting-service` having a valid token doesn't mean it's allowed to do everything; the resource server must check the token's granted scope matches what the specific endpoint requires.

```java
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

public class InventoryApiSecurityConfig {

    public SecurityFilterChain resourceServerFilterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(authorize -> authorize
                        .requestMatchers("GET", "/inventory/**").hasAuthority("SCOPE_inventory.read")
                        .requestMatchers("POST", "/inventory/**").hasAuthority("SCOPE_inventory.write")
                        .anyRequest().denyAll())
                .oauth2ResourceServer(resourceServer -> resourceServer.jwt(Customizer.withDefaults()));

        return http.build();
    }
}
```

**How to run:** wire this into the inventory API's own Spring Boot app (a resource server, separate from the authorization server). Call `GET /inventory/items` with a token carrying only `inventory.read`: expect `200 OK`. Call `POST /inventory/items` with that same token: expect `403 Forbidden`, since it lacks `inventory.write`.

```
HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error":"insufficient_scope","error_description":"The request requires higher privileges than provided by the access token."}
```

What changed and why it's production-flavored: authenticating as a valid client is necessary but not sufficient — real authorization also depends on which scopes were actually granted, and the resource server, not the authorization server, is what enforces that boundary on each individual call.

## 6. Walkthrough

Tracing a complete client credentials exchange and its downstream use, in execution order:

1. `reporting-service` needs to call the inventory API and has no cached, unexpired token (Level 2's cache check fails).
2. It sends `POST /oauth2/token` with `grant_type=client_credentials`, its own `client_id`/`client_secret` (via HTTP Basic auth, card 0012), and the `scope` it wants (`inventory.read`).
3. The token endpoint (card 0027) authenticates the client credentials themselves — this *is* the entire authentication step; there's no separate user login anywhere in this flow, unlike authorization code (card 0038).
4. The server checks the requested scope against what `reporting-service`'s `RegisteredClient` is allowed to request (card 0014) — narrowing or rejecting anything outside that list.
5. The server generates an access token whose subject *is* the client itself (`sub=reporting-service`, not any user), saves it via `OAuth2AuthorizationService` (card 0017), and responds `200 OK` with the token — critically, no `refresh_token` is issued, since the client can simply request a fresh token again using the same credentials whenever it needs one.
6. `reporting-service` caches this token (Level 2) and attaches it as `Authorization: Bearer <token>` on its call to the inventory API.
7. The inventory API, acting as a resource server (Level 3), validates the token's signature and checks its `scope` claim contains `inventory.read` before serving the request; a request to a `write` endpoint with only `read` scope is rejected with `403`.

```
reporting-service                Authorization Server              Inventory API
     | 1. cached token expired?
     | 2. POST /token (client creds)  |
     |--------------------------------->
     |                                 | 3-5. authenticate client,
     |                                 |      check scope, issue token
     | 6. 200 OK {access_token}        |
     <---------------------------------|
     | 7. GET /inventory/items                                |
     |    Authorization: Bearer <token>                       |
     |---------------------------------------------------------->
     |                                                          | validate token, check scope
     |                                          200 OK / 403    |
     <----------------------------------------------------------|
```

Concrete request and response for the token exchange:

```
POST /oauth2/token HTTP/1.1
Authorization: Basic cmVwb3J0aW5nLXNlcnZpY2U6c2VjcmV0
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&scope=inventory.read

HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"eyJhbGciOiJSUzI1NiJ9...","token_type":"Bearer","expires_in":3600,"scope":"inventory.read"}
```

## 7. Gotchas & takeaways

> There is no user consent step anywhere in client credentials — whatever scopes the client is permitted to request (card 0014), it gets automatically, with no human review at request time. This means the `RegisteredClient` configuration itself *is* the security boundary; misconfiguring a service's allowed scopes too broadly is immediately exploitable, with no consent screen acting as a second line of defense.

- No `refresh_token` is issued for this grant, and that's intentional — since the client already holds its own long-lived secret, it can simply request a brand-new access token the same way at any time, making a separate refresh token redundant.
- The access token's subject represents the *client*, not a user — don't design downstream authorization logic that assumes `sub` is always a human username; for client-credentials tokens it's a `client_id`.
- Client credentials should only ever be used over a secure, non-browser channel (backend-to-backend) — never embed a client secret in a mobile app, SPA, or any client a user could extract by inspecting the app's binary or network traffic.
- Cache tokens (Level 2) rather than fetching a new one per call, but always honor `expires_in` with a safety margin — using a token past its actual expiry produces a hard failure on the resource server, which is worse than fetching slightly early.
- Scope enforcement is the resource server's job (Level 3), not the authorization server's — issuing a token with `inventory.read` doesn't automatically restrict what the client can technically attempt; the receiving API must actively check `SCOPE_inventory.read` on every relevant endpoint.
