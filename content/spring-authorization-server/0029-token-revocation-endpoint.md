---
card: spring-authorization-server
gi: 29
slug: token-revocation-endpoint
title: "Token revocation endpoint"
---

## 1. What it is

The token revocation endpoint (`POST /oauth2/revoke`, RFC 7009) lets a client explicitly invalidate a token it holds — typically its refresh token — before that token's natural expiry. Internally it's `OAuth2TokenRevocationEndpointFilter`, backed by `OAuth2TokenRevocationAuthenticationProvider`, which finds the matching `OAuth2Authorization` and marks the relevant token invalidated, exactly the same underlying operation used internally during refresh token rotation (card 0023) — just triggered explicitly by client request instead of automatically on reuse.

## 2. Why & when

Tokens don't just expire on their own schedule — sometimes a client *knows* a token should stop working immediately: the user clicked "log out," the user uninstalled the app, or the client detected something suspicious about its own stored credentials. Revocation exists so this "I'm done with this token, invalidate it now" intent has a proper, standard mechanism, rather than the client just discarding its local copy and hoping the server independently expires it eventually.

Reach for the revocation endpoint when:

- Implementing "log out" for any client holding a refresh token — revoking the refresh token (and, per RFC 7009, typically its associated access token too) is the correct way to end a session server-side, not just deleting local storage.
- A client detects a compromised local token store (e.g. malware detection on a device) and needs to proactively invalidate every token it's holding.
- Implementing account-level "sign out everywhere" — which usually means iterating and revoking every `OAuth2Authorization` for a given user across all their sessions.

## 3. Core concept

Revocation is like returning a rented car key to the counter and saying "I'm done with this, deactivate it" — as opposed to just walking away and letting the rental agreement quietly expire on its own schedule days later. The counter (revocation endpoint) immediately deactivates the specific key handed over, and per the standard, deactivating certain keys (a refresh token) can cascade to deactivate related keys issued alongside it (its access token) too.

```
POST /oauth2/revoke
Authorization: Basic dGFzay10cmFja2VyOnNlY3JldA==
Content-Type: application/x-www-form-urlencoded

token=8xL3k9-refresh-token-value
&token_type_hint=refresh_token
```

Response: `200 OK` with an empty body — success is indicated simply by the absence of an error, per RFC 7009.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Revoking a refresh token cascades to invalidate its associated access token">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">POST /oauth2/revoke</text>
  <text x="110" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">token=refresh_token_value</text>

  <rect x="240" y="70" width="170" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="325" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OAuth2Authorization</text>
  <text x="325" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">found by token value</text>

  <rect x="450" y="30" width="160" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="530" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">refresh_token: invalidated</text>

  <rect x="450" y="100" width="160" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="530" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">access_token: invalidated too</text>

  <line x1="200" y1="100" x2="235" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="410" y1="90" x2="445" y2="60" stroke="#f0883e" stroke-width="1.5"/>
  <line x1="410" y1="110" x2="445" y2="125" stroke="#f0883e" stroke-width="1.5"/>
</svg>

Revoking one token in an authorization can, per RFC 7009, cascade to revoke its sibling token as well.

## 5. Runnable example

The scenario: task-tracker implements logout by revoking the user's refresh token, then handles revoking a specific access token directly, and finally implements "sign out everywhere" by revoking every authorization for a user across all their sessions.

### Level 1 — Basic

```java
// RevocationDemo.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class RevocationDemo {
    public static void main(String[] args) throws Exception {
        String credentials = Base64.getEncoder().encodeToString("task-tracker:secret".getBytes());
        String body = "token=8xL3k9-refresh-token-value&token_type_hint=refresh_token";

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/revoke"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
    }
}
```

**How to run:** requires a live authorization server with `task-tracker` registered and a real refresh token to revoke; run via `java RevocationDemo.java`. Expected output:

```
Status: 200
```

### Level 2 — Intermediate

Providing `token_type_hint` lets the server check the more likely token store first (an optimization, not a strict requirement — the server also checks the other store if the hint doesn't match), and a client should handle revoking either token type depending on what it locally holds.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class RevocationDemo {

    static int revokeToken(String clientId, String clientSecret, String token, String tokenTypeHint)
            throws Exception {
        String credentials = Base64.getEncoder().encodeToString((clientId + ":" + clientSecret).getBytes());
        String body = "token=" + token + "&token_type_hint=" + tokenTypeHint;

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/revoke"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString()).statusCode();
    }

    public static void main(String[] args) throws Exception {
        // Logout flow: revoke both tokens the client is holding, refresh token first
        int refreshResult = revokeToken("task-tracker", "secret", "8xL3k9-refresh-value", "refresh_token");
        int accessResult = revokeToken("task-tracker", "secret", "eyJhbGciOi-access-value", "access_token");

        System.out.println("Refresh token revocation: " + refreshResult);
        System.out.println("Access token revocation: " + accessResult);
    }
}
```

**How to run:** same environment as Level 1. Expected output:

```
Refresh token revocation: 200
Access token revocation: 200
```

What changed: this is a complete logout implementation — revoking the refresh token first (which per RFC 7009 typically cascades to the access token too on Spring Authorization Server) and then explicitly revoking the access token as well, covering both token types regardless of which one the cascade already handled.

### Level 3 — Advanced

"Sign out everywhere" needs to revoke every `OAuth2Authorization` for a given user, across every client and every device — this requires a custom admin-facing operation querying by principal name, since the standard `/oauth2/revoke` endpoint only ever handles one token at a time, presented by the client that holds it.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationService;

import java.util.List;

public class SignOutEverywhere {

    /**
     * Real deployments typically add a custom query method (e.g. on JdbcOAuth2AuthorizationService's
     * underlying table) to find all authorizations for a principal -- the base interface only
     * supports lookup by id or token value, not by principal name.
     */
    public static void revokeAllForUser(
            OAuth2AuthorizationService authorizationService,
            List<OAuth2Authorization> allAuthorizationsForPrincipal) {

        for (OAuth2Authorization authorization : allAuthorizationsForPrincipal) {
            authorizationService.remove(authorization);
            System.out.println("Revoked authorization " + authorization.getId()
                    + " for client " + authorization.getRegisteredClientId());
        }
    }

    public static void main(String[] args) {
        System.out.println("revokeAllForUser iterates every OAuth2Authorization belonging to a user");
        System.out.println("across every client and device, removing each one -- this is what a real");
        System.out.println("'sign out everywhere' account-settings action performs under the hood.");
    }
}
```

**How to run:** in a real application, `allAuthorizationsForPrincipal` comes from a custom repository query (e.g. `SELECT * FROM oauth2_authorization WHERE principal_name = ?` against the JDBC schema, card 0017) rather than the standard `OAuth2AuthorizationService` interface, which doesn't expose a by-principal lookup; wire this into an account settings action. Expected output:

```
revokeAllForUser iterates every OAuth2Authorization belonging to a user
across every client and device, removing each one -- this is what a real
'sign out everywhere' account-settings action performs under the hood.
```

What changed and why it's production-flavored: single-token revocation (Level 1/2) only ever touches what one client presents about itself — a genuine "sign out everywhere" feature needs a broader, principal-scoped query that the standard interface doesn't provide out of the box, which is exactly the kind of extension a real account-security feature requires building on top of the base library.

## 6. Walkthrough

Tracing a logout flow through the revocation endpoint, in execution order:

1. The user clicks "Log out" in task-tracker; the client-side code retrieves its stored refresh token and calls `POST /oauth2/revoke` with `token=8xL3k9-refresh-value&token_type_hint=refresh_token`, authenticating with its own client credentials.
2. `OAuth2TokenRevocationEndpointFilter` authenticates the client, then `OAuth2TokenRevocationAuthenticationProvider` looks up the `OAuth2Authorization` by this token value (checking the refresh-token store first, per the hint).
3. It marks the refresh token's `OAuth2Authorization.Token` entry invalidated and — per the RFC 7009 semantics Spring Authorization Server implements — also invalidates the associated access token issued from the same authorization, since a client explicitly ending a session should end *all* access derived from it, not just the refresh capability.
4. The updated (now fully invalidated) authorization is saved, and the endpoint responds `200 OK` with an empty body.
5. The client discards its local copies of both tokens and redirects the user to a logged-out state.
6. If task-tracker's resource server later receives a request bearing the now-revoked access token: for a JWT-format token, the token itself is unaware anything happened and would still verify locally unless the resource server also checks revocation status somehow (card 0020's tradeoff) — but for an opaque-format token, the very next introspection call (card 0028) correctly reports `{"active": false}`, since introspection reads live authorization state, which now reflects the revocation.

```
User clicks logout
   |
POST /oauth2/revoke (refresh_token, client's own credentials)
   |
find OAuth2Authorization by refresh token value
   |
mark refresh_token invalidated + cascade: mark access_token invalidated too
   |
save authorization -> 200 OK (empty body)
   |
client discards local tokens
   |
next resource-server check: opaque token -> introspect reports active=false immediately
                             JWT token    -> still verifies locally until it naturally expires
```

## 7. Gotchas & takeaways

> Revocation only fully protects against reuse for opaque-format tokens, where the resource server checks live state via introspection on every request. A revoked JWT access token remains cryptographically valid and will pass local signature verification until its `exp` claim arrives — revoking it server-side doesn't retroactively un-sign it. If instant, guaranteed revocation matters for a given client, prefer opaque access tokens (card 0020) or a short access-token TTL alongside revocation.

- `token_type_hint` is an optimization, not a strict requirement — Spring Authorization Server will still find and revoke the token even with an incorrect or omitted hint, just potentially checking one store before the other.
- Revoking a refresh token cascades to its associated access token per RFC 7009's guidance, which Spring Authorization Server follows — don't assume you need to separately revoke both in every case, though doing so explicitly (Level 2) is harmless and can serve as defense in depth against implementation differences.
- The standard revocation endpoint operates on one token at a time, presented by a client that holds it — there's no built-in "revoke everything for user X" operation; that's a custom extension (Level 3) built against the underlying storage.
- Always implement logout by calling this endpoint, not merely by deleting the client's local token storage — a client-only "logout" leaves the tokens fully valid server-side, so anyone who captured them beforehand (e.g. via a prior network compromise) can keep using them indefinitely.
- Testing revocation is easy to get wrong silently — verify by attempting to *use* the revoked token afterward (a refresh attempt, or an introspection call) rather than just checking the revocation call itself returned `200`, since a `200` response doesn't by itself prove the token actually stopped working.
