---
card: system-design
gi: 176
slug: oauth2-openid-connect
title: OAuth2 & OpenID Connect
---

## 1. What it is

**OAuth2** is a protocol for *delegated authorization* — letting a user grant a third-party application limited access to their data on another service, without ever sharing their password with that third party (e.g. "let this photo-printing app access your Google Photos"). **OpenID Connect (OIDC)** is a thin layer built on top of OAuth2 that adds *authentication* — a standard way for that third-party application to also learn who the user actually is, via a signed identity token, not just what data it can access.

## 2. Why & when

Before OAuth2, the only way for a third-party app to access your data on another service was for you to hand over your actual password to that app — a serious security risk, since the app could then do anything your account could do, forever, with no easy way to revoke just that one app's access. OAuth2 solves this by having the user grant a scoped, revocable permission directly through the service they already trust (Google, GitHub), which then issues the third-party app a limited access token, never the user's real credentials. OpenID Connect solves the closely related but distinct problem of "how does this third-party app know who just logged in" — the classic "Sign in with Google" button is OIDC, not plain OAuth2. Use OAuth2 when an app needs limited access to a user's data on another service; use OIDC (built on OAuth2) when an app needs to authenticate the user at all, typically via a "Sign in with X" flow.

## 3. Core concept

- **Authorization Code flow:** the user is redirected to the authorization server (e.g. Google) to log in and approve the requested access; the authorization server redirects back to the app with a short-lived authorization code, which the app exchanges (server-to-server, using its own client secret) for an access token — the code itself is useless if intercepted, since exchanging it also requires the app's secret.
- **Access token:** what the third-party app actually uses to call the resource server's (e.g. Google Photos') API on the user's behalf; it is scoped to specific permissions (e.g. "read-only photo access") and typically short-lived.
- **Refresh token:** a longer-lived credential the app can use to get a new access token once the current one expires, without requiring the user to log in again.
- **ID token (OIDC only):** a signed [JWT](0177-jwt-structure-validation.md) containing the user's verified identity claims (their user ID, email, name) — this is what actually answers "who logged in," and is separate from the access token, which only grants API access.
- **Scopes:** the specific, named permissions the user is asked to grant (`photos.read`, `email`, `profile`) — the app should request only the scopes it actually needs, and the user sees exactly what they are approving.

## 4. Diagram

```
   user                  third-party app              authorization server (e.g. Google)
    |                          |                                  |
    |-- clicks "Sign in" ----->|                                  |
    |<----------------- redirect to authorization server ---------|
    |-- logs in + approves scopes -------------------------------->|
    |<----------------- redirect back WITH authorization code -----|
    |                          |-- exchange code + client secret ->|
    |                          |<---- access token + ID token ------|
    |                          |
    |                          |-- call resource server API with access token -->|
    |                          |<------------------------- user's data ----------|
```
*Caption: the user never gives their password to the third-party app; the authorization server mediates the whole exchange and issues scoped, revocable tokens instead.*

## 5. Runnable example

**Level 1 — Basic.** Generate a short-lived authorization code after simulated user approval.

**Level 2 — Exchange the code for an access token, requiring the app's own secret.** Model the server-to-server exchange step.

**Level 3 — Issue an OIDC ID token alongside the access token, and use the access token to call a resource server.** Distinguish "who logged in" (ID token) from "what the app can do" (access token).

```java
// OAuth2OidcDemo.java
import java.util.*;

public class OAuth2OidcDemo {

    static final String CLIENT_SECRET = "app-secret-xyz"; // only the app and the auth server know this
    static Map<String, String> issuedCodes = new HashMap<>(); // code -> userId (short-lived, single-use)

    // Level 1: user approves the requested scopes; the authorization server issues a short-lived code.
    static String authorizationServerIssueCode(String userId, List<String> approvedScopes) {
        String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
        issuedCodes.put(code, userId);
        System.out.println("user " + userId + " approved scopes " + approvedScopes + " -> authorization code issued");
        return code;
    }

    // Level 2: exchange the code for tokens - only succeeds with the correct client secret.
    static Map<String, String> authorizationServerExchangeCode(String code, String clientSecret) {
        if (!clientSecret.equals(CLIENT_SECRET)) {
            throw new SecurityException("invalid client secret - exchange rejected");
        }
        String userId = issuedCodes.remove(code); // single-use: the code is consumed here
        if (userId == null) throw new SecurityException("code invalid, expired, or already used");

        String accessToken = "access-" + UUID.randomUUID().toString().substring(0, 8);
        String idToken = "idtoken.{userId=" + userId + ",name=Alice}.signed"; // Level 3: OIDC identity claims
        Map<String, String> tokens = new HashMap<>();
        tokens.put("access_token", accessToken);
        tokens.put("id_token", idToken);
        return tokens;
    }

    // Level 3: the resource server accepts the access token for API calls - it doesn't care about identity, only scope.
    static String resourceServerGetPhotos(String accessToken) {
        return "photos for token " + accessToken + ": [photo1.jpg, photo2.jpg]";
    }

    public static void main(String[] args) {
        // Level 1: user logs in at the authorization server and approves the app's requested scopes.
        String code = authorizationServerIssueCode("user-17", List.of("photos.read", "email"));

        // Level 2: the app (server-side) exchanges the code, proving its identity with the client secret.
        Map<String, String> tokens = authorizationServerExchangeCode(code, CLIENT_SECRET);
        System.out.println("received access_token: " + tokens.get("access_token"));
        System.out.println("received id_token (OIDC - proves WHO logged in): " + tokens.get("id_token"));

        // Level 3: the access token is used to call the resource server - separate from knowing WHO the user is.
        System.out.println(resourceServerGetPhotos(tokens.get("access_token")));

        // Reusing the SAME code again fails - it was already consumed (single-use).
        try {
            authorizationServerExchangeCode(code, CLIENT_SECRET);
        } catch (SecurityException e) {
            System.out.println("reusing the code failed: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `OAuth2OidcDemo.java`, then run `java OAuth2OidcDemo.java`.

## 6. Walkthrough

1. `authorizationServerIssueCode("user-17", [...])` models the user approving the requested scopes at the authorization server's login page; it generates a random, short-lived `code` and stores `code -> userId` in `issuedCodes`, then returns the code to (conceptually) redirect back to the app.
2. `authorizationServerExchangeCode(code, CLIENT_SECRET)` first checks the supplied `clientSecret` against the real `CLIENT_SECRET`; since it matches, the check passes, and `issuedCodes.remove(code)` both retrieves the associated `userId` and deletes the entry — making the code single-use from this point on.
3. The method builds and returns a map containing a fresh `access_token` (a random, opaque string standing in for a real bearer token) and an `id_token` (here, a simplified structure showing the OIDC identity claims it would really carry, as a signed JWT).
4. `resourceServerGetPhotos(tokens.get("access_token"))` uses only the access token, calling a completely separate resource server API — this deliberately shows that the resource server only ever needs to validate the access token's scope and validity; it never needs to know or care about the user's actual identity, which is what the (separate) ID token is for.
5. The final call attempts to exchange the exact same `code` a second time; since it was already removed from `issuedCodes` in step 2, `issuedCodes.remove(code)` now returns `null`, and the method throws a `SecurityException` — correctly enforcing that an authorization code can only ever be exchanged once, closing off a class of replay attacks where an intercepted code might otherwise be reused.

## 7. Gotchas & takeaways

> Gotcha: treating the *access token* as proof of the user's identity (instead of using the *ID token*) is a common and serious mistake — an access token only proves "this bearer may call this API with these scopes," and says nothing verified about who the user actually is; only the signed ID token, specific to OpenID Connect, is meant to be parsed for identity claims.

- OAuth2 solves delegated, scoped, revocable access to a user's data on another service, without ever exposing the user's real password.
- OpenID Connect adds a standard, verifiable way to authenticate the user (via the ID token), which plain OAuth2 does not provide on its own.
- An authorization code is short-lived and single-use specifically to limit the damage if it is ever intercepted in transit.
- Related concepts: [JWT structure & validation](0177-jwt-structure-validation.md) (the format the ID token, and often the access token, actually use), [Authentication vs authorization](0174-authentication-vs-authorization.md) (the two concerns OIDC and OAuth2 respectively address), [Spring Authorization Server (OAuth2 provider)](0184-spring-authorization-server-oauth2-provider.md) (a concrete Java implementation of the authorization server role shown here).
