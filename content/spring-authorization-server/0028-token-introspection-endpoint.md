---
card: spring-authorization-server
gi: 28
slug: token-introspection-endpoint
title: "Token introspection endpoint"
---

## 1. What it is

The token introspection endpoint (`POST /oauth2/introspect`, RFC 7662) lets a resource server ask the authorization server "is this token still valid, and what does it represent?" It's the mechanism that makes opaque access tokens usable (card 0020) — since an opaque token carries no information of its own, this endpoint is the only way to learn anything about it. Internally it's `OAuth2TokenIntrospectionEndpointFilter`, backed by `OAuth2TokenIntrospectionAuthenticationProvider`.

## 2. Why & when

A resource server checking a JWT never needs to ask the authorization server anything — it verifies the signature locally. But a resource server checking an opaque token has no other option: the token string alone means nothing. Introspection exists to fill exactly that gap, and it doubles as a way to check live revocation status even for tokens that *could* otherwise be checked another way, since it always reflects the authorization server's current, authoritative state.

Reach for the introspection endpoint (usually via `spring-security-oauth2-resource-server`'s built-in opaque token support rather than calling it manually) when:

- Your resource server is configured for opaque access tokens (card 0020) and needs to validate incoming bearer tokens.
- Building any tool or dashboard that needs to check "is this specific token currently valid" without decoding it — support tooling, an admin panel showing active sessions.
- Debugging a resource server rejecting a token it should accept — calling introspection directly with the same token value shows exactly what the authorization server currently believes about it.

## 3. Core concept

Introspection is like calling the issuing bank to check if a specific check (an opaque token) is still good before cashing it — you don't try to read anything meaningful off the check itself (there's nothing to read), you call the bank, hand over the check number, and they tell you definitively: valid or not, and if valid, whose account it draws from and what it's authorized for.

```
POST /oauth2/introspect
Authorization: Basic cGF5bWVudHMtc2VydmljZTpyZXNvdXJjZS1zZWNyZXQ=
Content-Type: application/x-www-form-urlencoded

token=8xL3k9-opaque-token-value
```

Response for an active token:
```json
{"active": true, "scope": "payments.charge", "client_id": "task-tracker", "sub": "alice", "exp": 1752312345, "token_type": "Bearer"}
```

Response for an invalid, expired, or revoked token:
```json
{"active": false}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Resource server calls introspection to check token validity, authenticating itself first">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Resource server</text>

  <rect x="240" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">POST /oauth2/introspect</text>
  <text x="330" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">token=...</text>

  <rect x="460" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="540" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">{"active": true/false,</text>
  <text x="540" y="113" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">scope, sub, exp, ...}</text>

  <line x1="200" y1="100" x2="235" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="420" y1="100" x2="455" y2="100" stroke="#3fb950" stroke-width="2"/>

  <text x="330" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Resource server must authenticate itself with its OWN client credentials first</text>
</svg>

The resource server is itself a client of this endpoint, authenticating separately from the token it's asking about.

## 5. Runnable example

The scenario: the payments resource server introspecting an incoming token, then handling both the active and inactive responses correctly, and finally caching introspection results briefly to reduce load without undermining revocation speed too much.

### Level 1 — Basic

```java
// IntrospectionDemo.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class IntrospectionDemo {
    public static void main(String[] args) throws Exception {
        String credentials = Base64.getEncoder().encodeToString("payments-service:resource-secret".getBytes());
        String body = "token=8xL3k9-opaque-token-value";

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/introspect"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body: " + response.body());
    }
}
```

**How to run:** requires a live authorization server with the `payments-service` resource-server client registered for introspection access, and a real opaque token value; run via `java IntrospectionDemo.java`. Expected output for a valid, active token:

```
Status: 200
Body: {"active":true,"scope":"payments.charge","client_id":"payments-service","sub":"alice","exp":1752312345,"token_type":"Bearer"}
```

### Level 2 — Intermediate

The resource server needs to correctly branch on `active` — treating `active: false` (or an unparseable response) as "reject the request," never as "allow by default."

```java
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class IntrospectionDemo {

    static boolean isTokenActive(String token) throws Exception {
        String credentials = Base64.getEncoder().encodeToString("payments-service:resource-secret".getBytes());
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/introspect"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString("token=" + token))
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        if (response.statusCode() != 200) {
            return false; // fail closed: any non-200 means "treat as invalid"
        }
        JsonNode json = new ObjectMapper().readTree(response.body());
        return json.path("active").asBoolean(false); // default false if the field is missing
    }

    public static void main(String[] args) throws Exception {
        System.out.println("This helper fails CLOSED: any error, missing field, or");
        System.out.println("active=false all resolve to 'reject the request'.");
    }
}
```

**How to run:** requires `jackson-databind` on the classpath (already a transitive dependency in most Spring Boot projects) and a live server; run the same way. Expected output:

```
This helper fails CLOSED: any error, missing field, or
active=false all resolve to 'reject the request'.
```

What changed: `isTokenActive` treats the *absence* of a clear "yes, active" signal as a rejection, not an approval — a network hiccup, a malformed JSON body, or a missing `active` field all correctly deny the request rather than accidentally letting it through, which is the safe default for any authorization check.

### Level 3 — Advanced

Production adds a short-lived cache for introspection results to reduce load on the authorization server, deliberately keeping the cache TTL well under the access token's own lifetime so revocation still takes effect quickly — trading a small, bounded delay for a large reduction in introspection traffic.

```java
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

public class CachingIntrospector {

    record CachedResult(boolean active, Instant cachedAt) {}

    private final Map<String, CachedResult> cache = new ConcurrentHashMap<>();
    private final Duration cacheTtl; // deliberately short -- e.g. 10 seconds, NOT the token's own TTL
    private final Function<String, Boolean> realIntrospect;

    public CachingIntrospector(Duration cacheTtl, Function<String, Boolean> realIntrospect) {
        this.cacheTtl = cacheTtl;
        this.realIntrospect = realIntrospect;
    }

    public boolean isActive(String token) {
        CachedResult cached = cache.get(token);
        Instant now = Instant.now();

        if (cached != null && now.isBefore(cached.cachedAt().plus(cacheTtl))) {
            return cached.active(); // still fresh enough to trust
        }

        boolean freshResult = realIntrospect.apply(token);
        cache.put(token, new CachedResult(freshResult, now));
        return freshResult;
    }
}
```

**How to run:** wire `CachingIntrospector` with a real introspection call (Level 2's `isTokenActive`) as `realIntrospect`, and a TTL like `Duration.ofSeconds(10)`; a `main` method calling `isActive` repeatedly with the same token within 10 seconds hits the real endpoint only once, then serves from cache. Expected behavior when unit-tested with a counting stub: the underlying introspection function is called once per 10-second window per distinct token, regardless of how many `isActive` calls happen within that window.

What changed and why it's production-flavored: at real traffic volumes, introspecting on every single request would overwhelm the authorization server — a short cache (seconds, not minutes) cuts that load dramatically while keeping the worst-case revocation delay small and explicitly bounded, which is a deliberate, documented tradeoff rather than an accidental one.

## 6. Walkthrough

Tracing an introspection call through the endpoint, in execution order:

1. `POST /oauth2/introspect` arrives with the resource server's own Basic auth credentials and `token=8xL3k9-opaque-token-value`.
2. `OAuth2TokenIntrospectionEndpointFilter` first authenticates the *caller* (the resource server itself, registered as its own `RegisteredClient` with introspection access) — a completely separate authentication step from anything about the token being asked about.
3. `OAuth2TokenIntrospectionAuthenticationProvider` looks up the `OAuth2Authorization` by the token value (card 0017's `findByToken`), exactly as the token endpoint does when redeeming a code.
4. It checks the matching token's `isActive()` (card 0016) — not expired, not revoked.
5. If active, the provider builds a response body from the authorization's stored claims: `scope`, `client_id`, `sub` (principal name), `exp`, `token_type` — this is exactly the claims data added by any `OAuth2TokenCustomizer<OAuth2TokenClaimsContext>` (card 0022) at issuance time, resurfacing here.
6. The endpoint responds `200 OK` with `{"active": true, ...}`.
7. If the token is expired, doesn't exist, or was revoked, the endpoint responds `200 OK` with just `{"active": false}` — notably, still a `200`, not a `4xx`, since "the token is inactive" is itself a valid, successful introspection result, not a failure of the introspection request.
8. The resource server's security filter treats `active: false` (or any non-200/malformed response) as "reject this request," responding to its own original caller with `401 Unauthorized`.

```
Resource server: POST /oauth2/introspect (own credentials + token=...)
   |
authenticate resource server as a client
   |
findByToken(...) --not found/expired/revoked--> 200 {"active": false}
   |  found and active
build claims from OAuth2Authorization --> 200 {"active": true, scope, sub, exp, ...}
   |
Resource server: active=true? --> serve original request
                 active=false? --> 401 Unauthorized to original caller
```

## 7. Gotchas & takeaways

> `active: false` is returned with HTTP status `200`, not `401` or `404` — a resource server that checks only the HTTP status code and ignores the response body will incorrectly treat every introspection call as "successful," including ones describing an invalid token. Always parse and check the `active` field itself.

- Introspection requires the resource server to authenticate as its own registered client — this is a separate, additional credential from anything related to the token being checked, and a common setup mistake is forgetting to register a client specifically for introspection access.
- Caching introspection results (Level 3) is a legitimate, common optimization, but the cache TTL is a direct, explicit tradeoff against revocation speed — document it clearly, since "how fast does revocation actually take effect" is a real operational question someone will eventually ask.
- Never expose the introspection endpoint to untrusted callers without authentication — its response can reveal information about a token (scopes, subject) to whoever can call it, which is why it's itself gated by client authentication.
- JWT-format access tokens can technically also be introspected, but doing so defeats the entire point of using a self-contained format (card 0020) — if you find yourself introspecting JWTs routinely, reconsider whether opaque tokens would better fit that use case.
- Test the failure path explicitly — a resource server that's only ever been tested against active tokens can have a latent bug where a malformed or `active: false` response is accidentally treated as valid, which is a serious, easy-to-miss authorization hole.
