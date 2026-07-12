---
card: spring-authorization-server
gi: 40
slug: refresh-token-grant
title: "Refresh token grant"
---

## 1. What it is

The refresh token grant (`grant_type=refresh_token` at `POST /oauth2/token`) lets a client obtain a new access token using a previously issued refresh token, without the user re-authenticating. It's how a client stays logged in across an access token's short lifetime (card 0024) without repeatedly bouncing the user back through the authorization endpoint (card 0026).

## 2. Why & when

Access tokens are deliberately short-lived (often minutes to an hour) to limit the damage if one leaks — but forcing a user to log in again every time that short window elapses would make for an unusable app. Refresh tokens resolve this tension: they're longer-lived and, critically, only ever presented directly to the token endpoint over a trusted backend channel, never attached to ordinary API calls the way access tokens are — so they're both the mechanism that keeps sessions long-lived *and* a smaller, better-protected attack surface than making access tokens themselves long-lived.

Reach for the refresh token grant when:

- Building any client that needs a session to outlast a single access token's short lifetime — most authorization-code clients need this.
- Deciding token lifetimes (card 0024) — the standard pattern is a short-lived access token paired with a longer-lived refresh token, rather than one long-lived token doing both jobs.
- Debugging "the user got silently logged out after N minutes" — usually means the client isn't using its refresh token to get a new access token before the old one expires.

## 3. Core concept

Think of the access token as a same-day visitor badge and the refresh token as your building membership card. The visitor badge (access token) gets you through doors *today*, but expires at midnight — you can't reuse it tomorrow. Your membership card (refresh token) doesn't get you through doors directly; instead, you show it at the front desk each morning to get a *new* visitor badge for that day, without having to re-verify your full identity from scratch (no re-login) every single day. If your membership card itself is lost or revoked, though, no more badges get issued until you re-register in person (full re-authentication).

```
POST /oauth2/token
    grant_type=refresh_token
    refresh_token=tGzv3JOkF0XG5Qx2TlKWIA
    client_id=task-tracker
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client uses refresh token to get a new access token, and optionally a new refresh token, without user interaction">
  <rect x="20" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="250" y="80" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="103" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Token Endpoint</text>
  <text x="330" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no user, no redirect</text>

  <rect x="480" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="103" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">New tokens</text>
  <text x="550" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">access (+ refresh)</text>

  <line x1="170" y1="95" x2="245" y2="95" stroke="#8b949e" stroke-width="1.5"/>
  <text x="207" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">old refresh_token</text>

  <line x1="410" y1="105" x2="475" y2="105" stroke="#3fb950" stroke-width="1.5"/>

  <line x1="330" y1="130" x2="330" y2="170" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="330" y="185" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">revoked/reused refresh_token -&gt; 400 invalid_grant, no tokens issued</text>
</svg>

Refreshing happens entirely between the client and the token endpoint — no browser redirect, no login page, no user interaction of any kind.

## 5. Runnable example

The scenario: a client using a refresh token to silently renew an expiring access token, growing to run this proactively in the background before expiry, and finally to handle refresh token rotation, where the server issues a brand-new refresh token on every use.

### Level 1 — Basic

```java
// RefreshTokenClient.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class RefreshTokenClient {

    private final HttpClient client = HttpClient.newHttpClient();

    public String refresh(String refreshToken, String clientId) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(
                        "grant_type=refresh_token"
                                + "&refresh_token=" + refreshToken
                                + "&client_id=" + clientId))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }

    public static void main(String[] args) throws Exception {
        String result = new RefreshTokenClient().refresh("tGzv3JOkF0XG5Qx2TlKWIA", "task-tracker");
        System.out.println(result);
    }
}
```

**How to run:** obtain an initial `refresh_token` via the authorization code flow (card 0038), then `java RefreshTokenClient.java` with that token. Expected output: a new JSON body with a fresh `access_token` and `expires_in`, without any browser interaction.

### Level 2 — Intermediate

Waiting for a `401` from an API call before refreshing adds latency and a failed request to every cycle — a better client tracks the access token's expiry and refreshes proactively just before it runs out.

```java
import java.time.Instant;

public class ProactiveTokenManager {

    private final RefreshTokenClient refreshClient = new RefreshTokenClient();
    private String accessToken;
    private String refreshToken;
    private Instant accessTokenExpiresAt;

    public String getValidAccessToken(String clientId) throws Exception {
        if (accessToken != null && Instant.now().isBefore(accessTokenExpiresAt.minusSeconds(60))) {
            return accessToken; // still good for at least another minute
        }
        String responseBody = refreshClient.refresh(refreshToken, clientId);
        applyTokenResponse(responseBody);
        return accessToken;
    }

    private void applyTokenResponse(String json) {
        this.accessToken = extract(json, "access_token");
        long expiresIn = Long.parseLong(extract(json, "expires_in"));
        this.accessTokenExpiresAt = Instant.now().plusSeconds(expiresIn);
        // A new refresh_token may or may not be present depending on rotation (Level 3).
        String newRefreshToken = extract(json, "refresh_token");
        if (newRefreshToken != null) {
            this.refreshToken = newRefreshToken;
        }
    }

    private String extract(String json, String field) {
        String marker = "\"" + field + "\":\"";
        int start = json.indexOf(marker);
        if (start == -1) return null;
        start += marker.length();
        int end = json.indexOf("\"", start);
        return json.substring(start, end);
    }
}
```

**How to run:** call `getValidAccessToken(clientId)` before every outbound API call in the app. Expected behavior: refresh happens automatically and transparently in the 60-second window before expiry, so outbound API calls never hit a token that's about to lapse mid-request.

What changed: the client now refreshes ahead of expiry rather than reactively after a failure, eliminating a class of intermittent `401` errors that would otherwise appear right at the boundary of each access token's lifetime.

### Level 3 — Advanced

Production systems often enable refresh token rotation — a new refresh token is issued on every use, and the *old* one is immediately invalidated, so a stolen-but-unused refresh token becomes worthless the moment the legitimate client uses its copy, and reuse of an already-rotated token is a strong signal of theft.

```java
public class RotationAwareTokenManager extends ProactiveTokenManager {

    public String getValidAccessTokenWithRotationHandling(String clientId) throws Exception {
        try {
            return getValidAccessToken(clientId);
        } catch (RuntimeException refreshFailure) {
            // A rejected refresh (invalid_grant) after rotation usually means either:
            // (a) this refresh token was already rotated by a prior, successful use, or
            // (b) it was explicitly revoked (card 0029).
            // Either way, the safe response is to force a full re-authentication,
            // never to retry with the same stale token.
            throw new IllegalStateException(
                    "Refresh token rejected — forcing full re-authentication via authorization code flow.",
                    refreshFailure);
        }
    }
}
```

**How to run:** configure the `RegisteredClient`'s `TokenSettings` to enable refresh token reuse detection (rotation), then deliberately call `refresh(...)` twice with the *same* original refresh token. Expected behavior: the first call succeeds and returns a new refresh token; the second call with the now-stale original token fails with `400 invalid_grant`, and `RotationAwareTokenManager` converts that into a clear signal to restart the login flow rather than retrying blindly.

```
HTTP/1.1 400 Bad Request
Content-Type: application/json

{"error":"invalid_grant","error_description":"Refresh token has already been used or is invalid."}
```

What changed and why it's production-flavored: rotation turns "the refresh token was stolen and I don't know it" into "the refresh token was reused and now everyone's session is force-logged-out" — a much safer failure mode, and the client-side handling above is what makes that failure mode actually resolve cleanly for the user (a fresh login) instead of a silent, confusing broken state.

## 6. Walkthrough

Tracing a refresh token exchange, in execution order:

1. The client detects its access token is expired or about to expire (Level 2's proactive check) and has a stored, previously issued refresh token.
2. It sends `POST /oauth2/token` with `grant_type=refresh_token`, the `refresh_token` value, and its `client_id` — client authentication is still required here (via secret or PKCE-equivalent, depending on client type), since a refresh token alone shouldn't be usable by just anyone who intercepts it in transit.
3. The token endpoint (card 0027) looks up the stored `OAuth2Authorization` (card 0016) associated with this refresh token value and checks it hasn't expired or been revoked (card 0029).
4. If rotation is enabled (Level 3), the server also checks this exact refresh token value hasn't already been consumed by a prior refresh — if it has, this is treated as a reuse/theft signal, and the server invalidates *all* tokens tied to this authorization as a precaution, not just rejecting this one request.
5. Assuming validation passes, the server issues a new access token (and, under rotation, a new refresh token too, invalidating the old one), saves the updated authorization state, and responds `200 OK`.
6. The client updates its stored tokens (Level 2's `applyTokenResponse`) and resumes making API calls with the fresh access token — the user never saw a login screen or any indication this happened.

```
Client                              Token Endpoint
  | 1. access token expiring soon
  | 2. POST /token grant_type=refresh_token
  |------------------------------------------>
  |                                    3. look up authorization by refresh_token
  |                                    4. rotation: already used? --yes--> revoke all, reject
  |                                                              --no--> continue
  |                                    5. issue new access_token (+ new refresh_token)
  | 6. 200 OK {access_token, refresh_token, expires_in}
  <------------------------------------------|
```

Concrete request and response:

```
POST /oauth2/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=tGzv3JOkF0XG5Qx2TlKWIA&client_id=task-tracker

HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"MApWNRGaqXk1IziW2ZLU","token_type":"Bearer","expires_in":3600,"refresh_token":"8xLOxBtZp8","scope":"tasks.read"}
```

## 7. Gotchas & takeaways

> Under rotation, once a refresh token has been successfully used, that *exact* token value becomes permanently invalid — retrying with it (even accidentally, due to a race between two concurrent refresh attempts in the same client) triggers reuse detection and can invalidate the entire session, not just fail the redundant request. Client code must serialize refresh attempts so two threads never race to use the same refresh token simultaneously.

- A refresh token being rejected doesn't always mean theft — it's equally often just an app bug (a race condition triggering rotation reuse, or a refresh token that legitimately expired from long inactivity); don't over-alarm users on every `invalid_grant`, but do always force a fresh login rather than retrying blindly.
- Refresh tokens should never be sent on ordinary API calls the way access tokens are — they belong exclusively in requests to the token endpoint, and treating them like a bearer credential for arbitrary APIs defeats their entire security purpose.
- Client credentials grant (card 0039) never issues a refresh token — there's nothing to "keep alive," since the client can simply request a fresh access token with its own long-lived secret at any time.
- Rotation (Level 3) trades a small amount of complexity (clients must correctly replace their stored refresh token on every use) for a real security benefit (stolen-but-unused tokens become useless); enable it unless a specific client architecture makes tracking the "latest" refresh token genuinely difficult.
- If refresh keeps failing right after working fine, check the refresh token's own expiry and idle-timeout settings (card 0024) before assuming a code bug — long-lived doesn't mean infinite, and a refresh token unused for too long can lapse on its own.
