---
card: spring-authorization-server
gi: 23
slug: refresh-tokens
title: "Refresh tokens"
---

## 1. What it is

A refresh token is a long-lived, opaque credential a client exchanges for a new access token (and often a new refresh token) once the current access token expires, without requiring the user to log in again. Spring Authorization Server issues one whenever a `RegisteredClient` includes `AuthorizationGrantType.REFRESH_TOKEN` among its grant types (card 0015), generates it via `OAuth2RefreshTokenGenerator` (card 0019), and — critically — supports **refresh token rotation**, where each use of a refresh token can optionally invalidate it and issue a brand-new one in its place.

## 2. Why & when

Access tokens are deliberately short-lived (minutes to an hour) to limit the damage window if one leaks — but forcing a user to re-authenticate every time a short-lived token expires would make short lifetimes impractical. Refresh tokens solve this: they're presented only to the authorization server itself (never to a resource server), so they can be long-lived without the resource-server-exposure risk that makes long-lived *access* tokens dangerous.

Reach for understanding and tuning refresh token behavior when:

- Any client needs to stay logged in across sessions longer than a single access token's lifetime — nearly every real interactive application.
- Deciding between refresh token **reuse** (the same refresh token value works repeatedly until it expires) and **rotation** (each use invalidates the old one and issues a new one) — rotation is the stronger security posture and the current best practice (RFC 9700).
- Implementing "logout everywhere" or responding to a suspected credential leak — this means revoking the `OAuth2Authorization` that holds the refresh token, cutting off both it and any access tokens issued from the same grant.

## 3. Core concept

Think of an access token as a day pass and a refresh token as a season membership card. You show the day pass to get into individual events (resource server calls); when it expires, you don't need to buy a new membership — you show your membership card at the counter and get a fresh day pass. With **rotation** turned on, the counter also swaps your membership card for a brand-new one each time, and the old card is immediately deactivated — so if someone stole your card and used it once, using the same old card again fails, which is a strong tell that a theft occurred.

```java
TokenSettings.builder()
    .refreshTokenTimeToLive(Duration.ofDays(30))
    .reuseRefreshTokens(false) // rotate: issue a new refresh token on every use
    .build();
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Refresh token rotation issues a new refresh token on each use and invalidates the old one">
  <rect x="20" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">refresh_token_v1</text>

  <rect x="245" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">POST /oauth2/token</text>

  <rect x="470" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="545" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">new access_token +</text>
  <text x="545" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">refresh_token_v2</text>

  <line x1="170" y1="55" x2="240" y2="55" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="395" y1="55" x2="465" y2="55" stroke="#3fb950" stroke-width="2"/>

  <rect x="245" y="140" width="150" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="320" y="165" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">refresh_token_v1</text>
  <text x="320" y="183" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">reused -&gt; rejected</text>

  <line x1="320" y1="80" x2="320" y2="138" stroke="#f0883e" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="230" y="115" fill="#8b949e" font-size="10" font-family="sans-serif">replay attempt</text>
</svg>

Each refresh consumes the old token and mints a new one; reusing a consumed token is treated as suspicious.

## 5. Runnable example

The scenario: task-tracker refreshes its access token, first with reuse enabled, then with rotation enabled, and finally handling the reuse-detection response that signals possible token theft.

### Level 1 — Basic

```java
// RefreshTokenDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;

import java.time.Duration;
import java.util.UUID;

public class RefreshTokenDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .tokenSettings(TokenSettings.builder()
                        .refreshTokenTimeToLive(Duration.ofDays(30))
                        .build())
                .build();

        System.out.println("Refresh token TTL: " + client.getTokenSettings().getRefreshTokenTimeToLive());
        System.out.println("Reuse refresh tokens (default): " + client.getTokenSettings().isReuseRefreshTokens());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java RefreshTokenDemo.java`. Expected output:

```
Refresh token TTL: PT720H
Reuse refresh tokens (default): true
```

With the default `reuseRefreshTokens(true)`, the same refresh token value keeps working across many refresh calls until it hits its own 30-day expiry.

### Level 2 — Intermediate

The security team decides reuse is too permissive — a leaked refresh token would remain usable for its entire 30-day lifetime. Turning on rotation means each refresh call invalidates the token just used and returns a fresh one in the response.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;

import java.time.Duration;
import java.util.UUID;

public class RefreshTokenDemo {
    public static void main(String[] args) {
        RegisteredClient client = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .clientAuthenticationMethod(ClientAuthenticationMethod.CLIENT_SECRET_BASIC)
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("https://task-tracker.example.com/callback")
                .scope("tasks.read")
                .tokenSettings(TokenSettings.builder()
                        .refreshTokenTimeToLive(Duration.ofDays(30))
                        .reuseRefreshTokens(false) // rotate on every use
                        .build())
                .build();

        System.out.println("Reuse refresh tokens: " + client.getTokenSettings().isReuseRefreshTokens());
        System.out.println("Behavior: every refresh call now returns a NEW refresh token,");
        System.out.println("and the previous one is invalidated immediately.");
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Reuse refresh tokens: false
Behavior: every refresh call now returns a NEW refresh token,
and the previous one is invalidated immediately.
```

What changed: a leaked refresh token is now only usable exactly once before it stops working — if the legitimate client refreshes again with its (now-rotated) new token, and the leaked old one is tried afterward by an attacker, that attempt fails, which is a meaningfully smaller exposure window than reuse allows.

### Level 3 — Advanced

Production goes further: detecting reuse of an *already-rotated-away* refresh token is treated as a signal of token theft, and the correct response is to revoke every token descended from that authorization — not just reject the one bad request — so a stolen-and-later-used-twice refresh token can't be exploited even if the attacker gets one successful use in before the legitimate client's next refresh.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2AuthorizationService;
import org.springframework.security.oauth2.core.OAuth2RefreshToken;
import org.springframework.security.oauth2.core.OAuth2TokenType;

public class RefreshTokenReuseDetection {

    public static OAuth2Authorization handleRefresh(
            OAuth2AuthorizationService authorizationService, String presentedRefreshTokenValue) {

        OAuth2Authorization authorization = authorizationService.findByToken(
                presentedRefreshTokenValue, new OAuth2TokenType("refresh_token"));

        if (authorization == null) {
            throw new IllegalArgumentException("invalid_grant: unknown refresh token");
        }

        OAuth2Authorization.Token<OAuth2RefreshToken> refreshToken =
                authorization.getToken(OAuth2RefreshToken.class);

        if (!refreshToken.isActive()) {
            // this exact value was already rotated away -- someone is reusing a token
            // that should no longer exist. Treat the WHOLE authorization as compromised.
            authorizationService.remove(authorization);
            throw new SecurityException(
                    "invalid_grant: refresh token reuse detected, all tokens for this session revoked");
        }

        // legitimate: proceed to issue new access + refresh tokens, save updated authorization
        return authorization; // (token issuance omitted for brevity)
    }
}
```

**How to run:** call `handleRefresh` twice with the same, already-rotated-away token value against a real `JdbcOAuth2AuthorizationService`; the first legitimate refresh succeeds and rotates the token, and a later replay of the old value throws `SecurityException`, at which point `authorizationService.remove(authorization)` has already revoked the entire session — including any still-valid access token issued from it. Expected output on the replay attempt:

```
Exception in thread "main" java.lang.SecurityException: invalid_grant: refresh token reuse detected, all tokens for this session revoked
```

What changed and why it's production-flavored: this is the difference between "reject one bad request" and "shut down the whole compromised session" — per RFC 9700's guidance on refresh token rotation, detecting reuse of an already-consumed token is treated as strong evidence of theft, and the correct, defensible response is full revocation, not just declining that one call.

## 6. Walkthrough

Tracing a rotation-with-reuse-detection scenario end to end, in execution order:

1. Task-tracker's access token expires; the client calls `POST /oauth2/token` with `grant_type=refresh_token&refresh_token=RT-v1`.
2. The server finds the matching `OAuth2Authorization`, confirms `RT-v1.isActive()` is true, issues a new access token and a new refresh token `RT-v2`, marks `RT-v1` invalidated, and saves the updated authorization.
3. Response: `{"access_token": "AT-2", "refresh_token": "RT-v2", "token_type": "Bearer", "expires_in": 600}`.
4. Unbeknownst to the legitimate user, `RT-v1` had already leaked (e.g. via a compromised log file) before step 1 occurred, but the attacker hasn't used it yet.
5. The attacker now calls `POST /oauth2/token` with `grant_type=refresh_token&refresh_token=RT-v1` — the same token the legitimate client already rotated away in step 2.
6. The server finds the authorization (still locatable by `RT-v1`'s value, since the record persists even after invalidation), but `RT-v1.isActive()` is now false.
7. Per Level 3's logic, this isn't just a normal rejection — the server recognizes this as reuse of a superseded token and revokes the entire `OAuth2Authorization`, which immediately invalidates `RT-v2` and the still-live access token `AT-2` too.
8. The next legitimate request from task-tracker — even one using the valid, recently-issued `RT-v2` — now also fails, forcing the user to log in again. This is a deliberate, visible cost, but it's far preferable to letting the attacker's stolen token continue working.

```
Legitimate client:  RT-v1 --refresh--> RT-v2 (RT-v1 now invalidated)
Attacker (delayed):  RT-v1 --refresh--> REJECTED, RT-v1 already inactive
                                     -> reuse detected -> revoke entire authorization
                                     -> RT-v2 and AT-2 (legitimate!) also revoked
```

## 7. Gotchas & takeaways

> Reuse detection has a real cost: if the legitimate client and an attacker both end up trying the same superseded refresh token (e.g. due to a client bug that retries a request twice), the legitimate session gets revoked too, alongside the attacker's. This is an intentional, accepted tradeoff — err on the side of shutting down a possibly-compromised session rather than leaving a possibly-stolen token usable.

- `reuseRefreshTokens(false)` (rotation) is the current best-practice default recommended by RFC 9700 for public clients especially, where refresh tokens are more exposed to interception or local storage compromise.
- A refresh token should never be sent to, or accepted by, a resource server — it's presented only to the authorization server's token endpoint; code that treats it like a bearer credential for API calls is a serious misuse.
- Refresh token lifetime is independent of access token lifetime — a common pattern is a very short access token (minutes) alongside a much longer refresh token (days to weeks), refreshed transparently in the background by the client.
- Revoking an `OAuth2Authorization` (Level 3's `remove` call) cascades to every token issued from that same grant — access token, refresh token, and any OIDC ID token — because they're all attached to the one record (card 0016).
- Client-side, storing refresh tokens securely matters as much as server-side rotation logic — a rotation policy only limits the *damage window* of a leak; it doesn't prevent the leak itself, so secure storage (OS keychains, httpOnly cookies, secure enclaves) is still the client's responsibility.
