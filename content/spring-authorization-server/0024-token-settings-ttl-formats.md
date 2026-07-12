---
card: spring-authorization-server
gi: 24
slug: token-settings-ttl-formats
title: "Token settings (TTL, formats)"
---

## 1. What it is

`TokenSettings` is the nested configuration object on `RegisteredClient` (card 0010) that governs everything about how long tokens live and what format they take: `authorizationCodeTimeToLive`, `accessTokenTimeToLive`, `accessTokenFormat` (JWT vs opaque, card 0020), `deviceCodeTimeToLive`, `refreshTokenTimeToLive`, `reuseRefreshTokens` (card 0023), and `idTokenSignatureAlgorithm`. Cards 0020 and 0023 already showed pieces of this in isolation; this card is the full picture of `TokenSettings` as one coherent, per-client tuning surface.

## 2. Why & when

Every one of these lifetimes and formats represents a real tradeoff between security and usability, and different clients legitimately need different answers. A banking client might want a 2-minute access token and a 1-hour refresh token with mandatory rotation. An internal admin tool trusted implicitly might tolerate a 1-hour access token and a 90-day refresh token. `TokenSettings` exists so each client gets its own tuned answer, all expressed through one consistent builder.

Reach for adjusting `TokenSettings` when:

- Onboarding a new client and deciding its risk profile — the security-sensitivity of what it can do should drive how long its tokens live.
- Debugging "my authorization code expired before I could redeem it" — the default authorization code lifetime is intentionally very short (minutes), and slow client-side processing (or a user idling on a consent screen) can genuinely run past it.
- Tuning for high-security integrations (short access token TTL, opaque format, mandatory rotation) versus low-friction internal tools (longer TTLs, JWT format for local validation speed).

## 3. Core concept

`TokenSettings` is like the full set of dials on a single control panel for one client's tokens — how long each type of pass is valid, whether the pass carries its own information or needs a phone call to verify (format), and whether a used season pass gets swapped for a new one (rotation). Every dial defaults to a sane, moderately-conservative value, but every dial is independently tunable per client.

```java
TokenSettings settings = TokenSettings.builder()
        .authorizationCodeTimeToLive(Duration.ofMinutes(5))   // default
        .accessTokenTimeToLive(Duration.ofMinutes(10))
        .accessTokenFormat(OAuth2TokenFormat.SELF_CONTAINED)   // JWT
        .refreshTokenTimeToLive(Duration.ofDays(30))
        .reuseRefreshTokens(false)
        .build();
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TokenSettings dials for different token lifetimes ordered from shortest to longest lived">
  <line x1="40" y1="120" x2="600" y2="120" stroke="#8b949e" stroke-width="2"/>
  <text x="320" y="145" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">shorter-lived -------------------------------------&gt; longer-lived</text>

  <circle cx="80" cy="120" r="8" fill="#6db33f"/>
  <text x="80" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">auth code</text>
  <text x="80" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">~5 min</text>

  <circle cx="250" cy="120" r="8" fill="#79c0ff"/>
  <text x="250" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">access token</text>
  <text x="250" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">minutes-1hr</text>

  <circle cx="420" cy="120" r="8" fill="#79c0ff"/>
  <text x="420" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">device code</text>
  <text x="420" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">~5-15 min</text>

  <circle cx="570" cy="120" r="8" fill="#f0883e"/>
  <text x="570" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">refresh token</text>
  <text x="570" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">days-weeks</text>
</svg>

Each token type has an independently configurable lifetime, ordered here shortest to longest by convention.

## 5. Runnable example

The scenario: configuring task-tracker's full `TokenSettings`, then differentiating a high-security payments client, then validating the settings are internally consistent before deployment.

### Level 1 — Basic

```java
// TokenSettingsDemo.java
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;

import java.time.Duration;

public class TokenSettingsDemo {
    public static void main(String[] args) {
        TokenSettings settings = TokenSettings.builder().build(); // all defaults

        System.out.println("Auth code TTL: " + settings.getAuthorizationCodeTimeToLive());
        System.out.println("Access token TTL: " + settings.getAccessTokenTimeToLive());
        System.out.println("Refresh token TTL: " + settings.getRefreshTokenTimeToLive());
        System.out.println("Reuse refresh tokens: " + settings.isReuseRefreshTokens());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java TokenSettingsDemo.java`. Expected output:

```
Auth code TTL: PT5M
Access token TTL: PT5M
Refresh token TTL: PT720H
Reuse refresh tokens: true
```

These are the library's built-in defaults — reasonable for a demo, but worth deliberately reviewing before production.

### Level 2 — Intermediate

Task-tracker's team decides on their actual tuning: a slightly longer access token (10 minutes, since their API calls can be chatty) and rotation enabled for refresh tokens (card 0023).

```java
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;
import org.springframework.security.oauth2.server.authorization.settings.OAuth2TokenFormat;

import java.time.Duration;

public class TokenSettingsDemo {
    public static void main(String[] args) {
        TokenSettings settings = TokenSettings.builder()
                .accessTokenTimeToLive(Duration.ofMinutes(10))
                .accessTokenFormat(OAuth2TokenFormat.SELF_CONTAINED)
                .refreshTokenTimeToLive(Duration.ofDays(30))
                .reuseRefreshTokens(false)
                .build();

        System.out.println("Access token TTL: " + settings.getAccessTokenTimeToLive());
        System.out.println("Access token format: " + settings.getAccessTokenFormat().getValue());
        System.out.println("Refresh rotation enabled: " + !settings.isReuseRefreshTokens());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Access token TTL: PT10M
Access token format: self-contained
Refresh rotation enabled: true
```

What changed: the client now has an explicit, deliberately-chosen tuning instead of library defaults, combining a JWT access token (fast local validation, card 0020) with rotating refresh tokens (limited leak exposure, card 0023).

### Level 3 — Advanced

The payments client needs a stricter profile, and production adds a validation helper that checks a `TokenSettings` configuration for internally-inconsistent or risky combinations before it's ever saved — catching, for example, a dangerously long access token TTL paired with the opaque format's revocation benefits being undermined by an equally long refresh TTL with reuse enabled.

```java
import org.springframework.security.oauth2.server.authorization.settings.TokenSettings;
import org.springframework.security.oauth2.server.authorization.settings.OAuth2TokenFormat;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;

public class TokenSettingsDemo {

    static List<String> validate(TokenSettings settings) {
        List<String> warnings = new ArrayList<>();

        if (settings.getAccessTokenTimeToLive().toMinutes() > 60) {
            warnings.add("access token TTL over 1 hour is unusually long; consider shortening it");
        }
        if (settings.getAccessTokenFormat().equals(OAuth2TokenFormat.SELF_CONTAINED)
                && settings.getAccessTokenTimeToLive().toMinutes() > 15) {
            warnings.add("JWT (self-contained) access tokens over 15 minutes reduce the value "
                    + "of short-lived tokens, since JWTs can't be revoked before expiry");
        }
        if (settings.isReuseRefreshTokens()) {
            warnings.add("refresh token reuse is enabled; rotation (reuseRefreshTokens=false) "
                    + "is the stronger, currently recommended default (RFC 9700)");
        }
        return warnings;
    }

    public static void main(String[] args) {
        TokenSettings paymentsSettings = TokenSettings.builder()
                .accessTokenTimeToLive(Duration.ofMinutes(5))
                .accessTokenFormat(OAuth2TokenFormat.REFERENCE) // opaque, instantly revocable
                .refreshTokenTimeToLive(Duration.ofHours(1))
                .reuseRefreshTokens(false)
                .build();

        List<String> warnings = validate(paymentsSettings);
        System.out.println("Payments client warnings: " + (warnings.isEmpty() ? "none" : warnings));

        TokenSettings riskySettings = TokenSettings.builder()
                .accessTokenTimeToLive(Duration.ofHours(2))
                .accessTokenFormat(OAuth2TokenFormat.SELF_CONTAINED)
                .build();
        System.out.println("Risky client warnings: " + validate(riskySettings));
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Payments client warnings: none
Risky client warnings: [access token TTL over 1 hour is unusually long; consider shortening it, JWT (self-contained) access tokens over 15 minutes reduce the value of short-lived tokens, since JWTs can't be revoked before expiry]
```

What changed and why it's production-flavored: a small validation pass like this, run at client-registration time (e.g. inside the admin API that calls `RegisteredClientRepository.save`), catches misconfigurations before they ship rather than discovering them during a security review or, worse, an incident — the payments client's tight, opaque, rotating configuration passes cleanly, while a careless long-lived JWT configuration is flagged immediately.

## 6. Walkthrough

Tracing how `TokenSettings` values get consulted at each stage of a grant, in execution order:

1. `GET /oauth2/authorize?...` succeeds; the server generates an authorization code and sets its expiry using `client.getTokenSettings().getAuthorizationCodeTimeToLive()` — 5 minutes by default (Level 1), giving the user a real but bounded window to complete login and consent.
2. `POST /oauth2/token` redeems the code before it expires; the server reads `getAccessTokenFormat()` to decide whether `JwtGenerator` or `OAuth2AccessTokenGenerator` produces the access token (card 0019), and stamps its `exp` claim (or its stored expiry, for opaque tokens) using `getAccessTokenTimeToLive()`.
3. If `REFRESH_TOKEN` is among the client's grant types, the server also generates a refresh token, expiring after `getRefreshTokenTimeToLive()`.
4. Minutes later, the access token expires; the client calls `POST /oauth2/token` with `grant_type=refresh_token`. The server checks `isReuseRefreshTokens()` — if false (rotation), it invalidates the presented refresh token and issues a new one with a **fresh** `getRefreshTokenTimeToLive()` window starting now (not counted down from the original grant), extending the effective session as long as refreshes keep happening within that window.
5. If the refresh token itself eventually expires (the user hasn't used the app in over `getRefreshTokenTimeToLive()`), the next refresh attempt fails with `invalid_grant`, and the client must send the user through a fresh `authorization_code` flow, back to step 1.

```
authorize -> code (TTL: authorizationCodeTimeToLive)
   |
redeem code -> access_token (TTL: accessTokenTimeToLive) + refresh_token (TTL: refreshTokenTimeToLive)
   |
   ... access token expires ...
   |
refresh -> new access_token + (if rotating) new refresh_token, TTL window restarts
   |
   ... eventually refresh token itself expires ...
   |
back to authorize (full login required again)
```

## 7. Gotchas & takeaways

> `accessTokenTimeToLive` for a **JWT-format** access token is a hard ceiling on how long a leaked token remains dangerous, since JWTs can't be revoked before expiry (card 0020) — treat this setting as a security control, not just a convenience knob, and keep it short for any client whose tokens might reach less-trusted environments (browsers, mobile devices).

- `authorizationCodeTimeToLive` is intentionally short by default (5 minutes) — if legitimate users are hitting expired-code errors, the fix is almost always a slow redirect chain or a user idling on a login screen, not a reason to casually extend this window.
- `refreshTokenTimeToLive` resets on each successful rotation (Level 3's walkthrough) — a refresh token's *effective* session length, for an actively-used client, is unbounded as long as refreshes keep happening more often than the TTL, which is the intended "stay logged in while active" behavior.
- Setting `accessTokenFormat` to opaque doesn't make `accessTokenTimeToLive` irrelevant — introspection still checks expiry, it's just that revocation additionally works before that expiry for opaque tokens.
- There's no single "correct" TTL for every client — the right values depend on the sensitivity of what the client can do and the acceptable blast radius of a leaked token; the validation pattern in Level 3 is a good way to encode your organization's specific policy.
- `TokenSettings` is per-client, not global — different clients on the same authorization server can (and often should) have very different tunings, as shown by contrasting task-tracker's and the payments client's settings throughout this card.
