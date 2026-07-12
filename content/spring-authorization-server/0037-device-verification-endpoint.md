---
card: spring-authorization-server
gi: 37
slug: device-verification-endpoint
title: "Device verification endpoint"
---

## 1. What it is

The device verification endpoint (`GET/POST /oauth2/device_verification` by default) is the human-facing half of the device authorization grant (card 0036) — it's the page a user visits on their phone or laptop to type in the short `user_code` shown on their TV or CLI, authenticate, and approve or deny the device's request. It's implemented internally as `OAuth2DeviceVerificationEndpointFilter`.

## 2. Why & when

The device authorization endpoint (card 0036) generates a `user_code`, but by itself that code does nothing — something has to let a human actually redeem it. This endpoint is that something: it's a regular, browser-facing, authenticated page, functionally similar to the authorization endpoint's consent step (card 0026), except it starts from a typed code instead of a `client_id` in the query string.

Reach for this endpoint (or its concept) when:

- Implementing the phone/laptop side of a device-flow login — this is the URL you tell the device to display to the user (`verification_uri`).
- Customizing the code-entry or consent UI a user sees when approving a TV or CLI login — the default page can be overridden the same way the standard consent page can (card 0026).
- Debugging "my device flow polls forever and never resolves" — check whether the user actually reached and completed this page; an abandoned or mistyped code leaves the device polling with `authorization_pending` indefinitely until it expires.

## 3. Core concept

Think of the device authorization endpoint (card 0036) as a vending machine that prints a claim ticket, and this verification endpoint as the staffed counter where you hand that ticket to an attendant to actually collect your item. The vending machine (the TV) can print tickets all day, but nothing happens until a person walks the ticket over to the counter (this endpoint), proves who they are (login), and says "yes, give it to that machine" (consent) — only then does the original machine's request get fulfilled.

```
GET /oauth2/device_verification?user_code=WDJB-MJHT
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="User visits verification page, enters code, authenticates, approves, which unblocks the waiting device">
  <rect x="20" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. Enter user_code</text>

  <rect x="200" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="275" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. Authenticate</text>

  <rect x="380" y="20" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="455" y="48" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. Approve / Deny</text>

  <line x1="170" y1="43" x2="195" y2="43" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="350" y1="43" x2="375" y2="43" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="230" y="130" width="200" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="330" y="155" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OAuth2Authorization</text>
  <text x="330" y="172" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">status: approved</text>

  <line x1="455" y1="66" x2="330" y2="125" stroke="#3fb950" stroke-width="1.5"/>

  <text x="330" y="220" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">device's next poll now returns an access token</text>
</svg>

Approval here is what flips the shared `OAuth2Authorization` record the device is polling against — the two flows communicate through that stored state, not a direct connection.

## 5. Runnable example

The scenario: exposing the default device verification page, growing to pre-fill the `user_code` when the device provides a `verification_uri_complete`, and finally to add rate-limiting on code entry to resist brute-forcing short codes.

### Level 1 — Basic

```java
// DeviceVerificationConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
public class DeviceVerificationConfig {

    @Bean
    @Order(1)
    public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
        OAuth2AuthorizationServerConfigurer configurer =
                OAuth2AuthorizationServerConfigurer.authorizationServer();

        http.securityMatcher(configurer.getEndpointsMatcher())
                .with(configurer, authorizationServer -> authorizationServer
                        .deviceAuthorizationEndpoint(withDefaults())
                        .deviceVerificationEndpoint(withDefaults()));

        return http.build();
    }
}
```

**How to run:** with a device_code request already made (card 0036), visit `http://localhost:8080/oauth2/device_verification` in a browser, log in if prompted, then type the `user_code` shown by the device into the form. Expected behavior: after submission, a consent-style page lists the requested scopes; approving it marks the underlying authorization as approved.

### Level 2 — Intermediate

Typing an 8-character code by hand is friction real products avoid — the device authorization response also includes `verification_uri_complete`, a URL with the code already embedded, often shown as a QR code so the user just scans and confirms.

```java
public class VerificationUriBuilder {

    public String buildCompleteUri(String verificationUri, String userCode) {
        return verificationUri + "?user_code=" + userCode.replace("-", "");
    }
}
```

**How to run:** call `buildCompleteUri("https://auth.example.com/oauth2/device_verification", "WDJB-MJHT")`, render the result as a QR code on the TV screen alongside the manually-typed fallback. Expected output: `https://auth.example.com/oauth2/device_verification?user_code=WDJBMJHT`; scanning it on a phone opens the verification page with the code field already filled in via the `user_code` query parameter, skipping straight to the login/consent step.

What changed: the user no longer has to type an 8-character code by hand on a phone keyboard — scanning a QR code (built from `verification_uri_complete`) pre-fills it, which is the flow most real device-flow UIs (streaming apps, smart TVs) actually use.

### Level 3 — Advanced

Because `user_code` is short and human-typeable, it's also brute-forceable — production rate-limits code-entry attempts per session/IP so an attacker can't script guesses against the pool of currently-pending codes.

```java
import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class VerificationRateLimiter {

    private static final int MAX_ATTEMPTS = 5;
    private static final Duration WINDOW = Duration.ofMinutes(10);

    private final Map<String, AttemptWindow> attemptsByClientIp = new ConcurrentHashMap<>();

    public boolean allow(String clientIp) {
        AttemptWindow window = attemptsByClientIp.computeIfAbsent(clientIp, ip -> new AttemptWindow());
        synchronized (window) {
            if (Instant.now().isAfter(window.windowStart.plus(WINDOW))) {
                window.windowStart = Instant.now();
                window.count = 0;
            }
            if (window.count >= MAX_ATTEMPTS) {
                return false;
            }
            window.count++;
            return true;
        }
    }

    private static class AttemptWindow {
        Instant windowStart = Instant.now();
        int count = 0;
    }
}
```

**How to run:** call `allow(request.getRemoteAddr())` before processing each submitted `user_code`, rejecting with `429 Too Many Requests` when it returns `false`. Simulate 6 rapid submissions of wrong codes from the same IP within 10 minutes: expect the first 5 to be processed (and rejected as invalid codes), and the 6th to be blocked by the rate limiter itself before code lookup even runs.

What changed and why it's production-flavored: an unthrottled verification form lets an attacker script through the entire keyspace of short `user_code`s (deliberately kept small for human typing) hoping to hijack someone else's pending device login — rate-limiting by IP/session closes that brute-force window.

## 6. Walkthrough

Tracing a complete verification interaction, in execution order:

1. The user, prompted by their TV, scans a QR code (Level 2) or manually navigates to `https://auth.example.com/oauth2/device_verification`.
2. If the URL included `user_code` as a query parameter (from `verification_uri_complete`), the form is pre-filled; otherwise the user types the code shown on the TV.
3. On submission, `VerificationRateLimiter.allow(...)` (Level 3) checks the submitting IP hasn't exceeded its attempt budget — if it has, `429` is returned immediately and no code lookup happens.
4. `OAuth2DeviceVerificationEndpointFilter` looks up the pending `OAuth2Authorization` (card 0016) matching the submitted `user_code`. An unknown or already-expired code returns an error page — deliberately generic, so it doesn't reveal whether the code simply expired or never existed.
5. If the user isn't authenticated yet, they're redirected to log in first, then returned to the verification flow with the code still attached.
6. Once authenticated, the endpoint renders a consent-style screen listing exactly what the *device's* client requested (scopes, client name) — the same trust decision as the authorization endpoint's consent step (card 0026), just reached via a typed code instead of a redirect chain.
7. The user approves (or denies). On approval, the endpoint updates the stored `OAuth2Authorization` for that `device_code` to an approved state, associated with this now-known user.
8. Control returns to the device flow (card 0036): the TV's next poll to `POST /oauth2/token` finds the authorization approved and receives a real access token in response.

```
GET /oauth2/device_verification?user_code=WDJBMJHT
   |
rate limit check --exceeded--> 429 Too Many Requests
   |  ok
lookup OAuth2Authorization by user_code --not found/expired--> generic error page
   |  found
authenticated? --no--> login --> return here
   |  yes
render consent screen (client name, requested scopes)
   |
user approves --------------------------> update OAuth2Authorization: status = approved
   |
render "you may now return to your device" confirmation page
```

Concrete interaction (as HTTP, from the browser's perspective):

```
GET /oauth2/device_verification?user_code=WDJBMJHT HTTP/1.1

HTTP/1.1 200 OK
Content-Type: text/html
(renders login form, or consent form if already authenticated)

POST /oauth2/device_verification HTTP/1.1
Content-Type: application/x-www-form-urlencoded

user_code=WDJBMJHT&scope=videos.read&approve=true

HTTP/1.1 200 OK
(renders "Device authorized — you may return to your TV")
```

## 7. Gotchas & takeaways

> Returning a *specific* error ("this code has expired" vs. "this code doesn't exist" vs. "this code was already used") leaks information useful for brute-forcing the active code pool — production verification pages should return a single generic failure message for all three cases, exactly like login forms avoid confirming which half of a username/password pair was wrong.

- The device never talks to this endpoint directly — communication between the TV and the phone happens entirely through the shared `OAuth2Authorization` record's status, updated here and read by the token endpoint's polling handler (card 0036).
- `user_code`s are short by design for human typing, which means the space of valid codes at any moment is small — combine short expiry (`expires_in` from card 0036) with rate-limiting (Level 3) rather than relying on code length alone for security.
- If a user reports "I approved on my phone but the TV never logged in," check first whether the TV's polling actually reached this specific `device_code`'s authorization (a stale or already-expired device_code on the TV side won't reflect the phone's approval).
- Denying the request (rather than abandoning the page) should promptly mark the `OAuth2Authorization` as denied so the device's next poll gets a definitive `access_denied` (card 0036) instead of waiting out the full expiry window unnecessarily.
- Because this page performs a real login and consent decision, treat it with the same UI/security scrutiny as the primary authorization endpoint's consent screen (card 0026) — it's a full trust boundary, not a lightweight utility form.
