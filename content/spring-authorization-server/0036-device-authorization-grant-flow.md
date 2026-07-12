---
card: spring-authorization-server
gi: 36
slug: device-authorization-grant-flow
title: "Device authorization grant flow"
---

## 1. What it is

The device authorization grant (OAuth2 Device Authorization Grant, RFC 8628) is a flow for input-constrained devices — smart TVs, CLI tools, IoT hardware — that can't easily open a browser or accept a typed password. The device requests a code from `POST /oauth2/device_authorization`, shows a short user code on its own screen, and polls `POST /oauth2/token` (with `grant_type=urn:ietf:params:oauth:grant-type:device_code`) until the user approves it on a *separate* device with a real browser.

## 2. Why & when

Every flow covered so far — authorization code (card 0026), client credentials — assumes the client itself can either open a browser or securely hold a client secret. A smart TV has neither a keyboard for typing a password comfortably nor, often, a client secret it can protect (it's a shared hardware SKU, not a per-install secret). The device flow sidesteps both problems: the TV shows a short code and a URL, the *user* completes authentication and consent on their phone or laptop, and the TV just polls in the background until that's done.

Reach for it when:

- Building login for a device with limited or no text input (smart TVs, streaming boxes, game consoles).
- Building CLI tools that need to authenticate a user without embedding a client secret or spinning up a local redirect listener.
- Deciding between this and the authorization code flow — if the client can open a browser and receive a redirect, prefer authorization code with PKCE; reserve device flow for genuinely input-constrained clients.

## 3. Core concept

Think of the device flow like checking into a hotel by phone before you arrive. You call the front desk (the device requests a code) and get a short confirmation number (the user code) read back to you. You then separately go to the hotel's app on your phone (the user's browser), enter that confirmation number, and finish check-in there — providing ID and a signature. Meanwhile, the original phone call is put on hold, periodically asking "are we done yet?" (the device polling the token endpoint) until the front desk confirms your check-in is complete and hands over the room key (the access token) over that same call.

```
POST /oauth2/device_authorization
    client_id=smart-tv-app
    scope=videos.read
```

## 4. Diagram

<svg viewBox="0 0 700 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Device requests a code, user approves on a separate browser, device polls until approved">
  <rect x="20" y="20" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Device (TV)</text>

  <rect x="280" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Authorization</text>
  <text x="350" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Server</text>

  <rect x="540" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="610" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">User's phone</text>

  <line x1="150" y1="45" x2="275" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <text x="212" y="35" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">1. request device code</text>

  <line x1="280" y1="60" x2="155" y2="60" stroke="#3fb950" stroke-width="1.5"/>
  <text x="212" y="75" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">2. device_code + user_code</text>

  <text x="85" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. shows: "Go to</text>
  <text x="85" y="124" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">example.com/device,</text>
  <text x="85" y="138" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">enter WDJB-MJHT"</text>

  <line x1="610" y1="70" x2="610" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <text x="610" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4. user visits URL,</text>
  <text x="610" y="139" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">enters code, logs in,</text>
  <text x="610" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">approves</text>

  <rect x="20" y="200" width="660" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="350" y="225" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">5. Device polls POST /oauth2/token every `interval` seconds</text>
  <text x="350" y="245" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">authorization_pending -&gt; keep polling</text>
  <text x="350" y="262" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">approved -&gt; access_token returned, polling stops</text>
</svg>

The device never sees the user's credentials — approval happens entirely on the separate, trusted browser.

## 5. Runnable example

The scenario: a CLI tool authenticating a user via device flow, growing to handle the polling loop's `slow_down` and `expired_token` responses correctly, and finally to add a real terminal progress display with cancellation.

### Level 1 — Basic

```java
// DeviceFlowConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
public class DeviceFlowConfig {

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

**How to run:** add to a Boot project with a `RegisteredClient` whose `authorizationGrantTypes` includes `DEVICE_CODE`, then `curl -X POST http://localhost:8080/oauth2/device_authorization -d "client_id=cli-tool"`. Expected output: a JSON body with `device_code`, `user_code`, `verification_uri`, and `expires_in`.

### Level 2 — Intermediate

A real client must poll correctly — respecting the server's `interval`, handling `authorization_pending` by waiting and retrying, and backing off further on `slow_down`.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;

public class DevicePoller {

    private final HttpClient client = HttpClient.newHttpClient();

    public String pollForToken(String deviceCode, String clientId, int intervalSeconds) throws Exception {
        int interval = intervalSeconds;
        while (true) {
            Thread.sleep(Duration.ofSeconds(interval).toMillis());

            HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            "grant_type=urn:ietf:params:oauth:grant-type:device_code"
                                    + "&device_code=" + deviceCode
                                    + "&client_id=" + clientId))
                    .build();

            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            String body = response.body();

            if (response.statusCode() == 200) {
                return body; // contains access_token
            }
            if (body.contains("authorization_pending")) {
                continue; // keep polling at the same interval
            }
            if (body.contains("slow_down")) {
                interval += 5; // back off per RFC 8628
                continue;
            }
            throw new IllegalStateException("Device flow failed: " + body);
        }
    }
}
```

**How to run:** call `pollForToken(deviceCode, "cli-tool", 5)` right after obtaining `device_code` from Level 1, then approve the code in a browser at `verification_uri`. Expected behavior: the method returns immediately after approval with the token JSON; without approval, it keeps polling every 5 seconds (or more, if throttled) and never returns.

What changed: the client now handles the real polling protocol instead of a single request, correctly distinguishing "not yet approved, keep trying" from "the server wants you to slow down" from a genuine failure.

### Level 3 — Advanced

Production also handles `expired_token` (the user code timed out) and `access_denied` (the user explicitly declined), and gives the CLI user a way to cancel — polling forever on a dead code wastes the terminal session.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;

public class RobustDevicePoller {

    private final HttpClient client = HttpClient.newHttpClient();

    public String pollForToken(String deviceCode, String clientId, int intervalSeconds, int expiresInSeconds)
            throws Exception {
        int interval = intervalSeconds;
        Instant deadline = Instant.now().plusSeconds(expiresInSeconds);

        while (Instant.now().isBefore(deadline)) {
            Thread.sleep(Duration.ofSeconds(interval).toMillis());

            HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            "grant_type=urn:ietf:params:oauth:grant-type:device_code"
                                    + "&device_code=" + deviceCode
                                    + "&client_id=" + clientId))
                    .build();

            HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
            String body = response.body();

            if (response.statusCode() == 200) {
                return body;
            }
            if (body.contains("authorization_pending")) {
                System.out.print(".");
                continue;
            }
            if (body.contains("slow_down")) {
                interval += 5;
                continue;
            }
            if (body.contains("access_denied")) {
                throw new IllegalStateException("User declined the login request.");
            }
            if (body.contains("expired_token")) {
                throw new IllegalStateException("The device code expired before approval. Please retry.");
            }
            throw new IllegalStateException("Unexpected device flow error: " + body);
        }
        throw new IllegalStateException("Device code expired locally before the server reported it.");
    }
}
```

**How to run:** call with the `expires_in` value from Level 1's device_authorization response. Let the code sit unapproved past its `expires_in` window: expect an `expired_token` (or the local deadline) exception rather than an infinite loop. Approve immediately in another run: expect the same successful return as Level 2, with `.` characters printed to the terminal while waiting — real, visible feedback that the tool isn't hung.

What changed and why it's production-flavored: the poller now terminates deterministically on every outcome the RFC defines (approved, denied, expired, throttled) instead of only the happy path, which is what real CLI tools need to avoid leaving users staring at a frozen terminal.

## 6. Walkthrough

Tracing a complete device flow, in execution order:

1. The CLI tool sends `POST /oauth2/device_authorization` with `client_id=cli-tool` (and optionally `scope`).
2. The server generates a `device_code` (long, opaque, for the device's own polling use) and a short `user_code` (human-typeable, e.g. `WDJB-MJHT`), stores them linked together in an `OAuth2Authorization` (card 0016) with status pending, and responds with both codes plus `verification_uri` and `expires_in`.
3. The CLI displays: *"Go to `https://auth.example.com/activate` and enter code `WDJB-MJHT`"* — and starts polling (Level 3's `RobustDevicePoller`).
4. The user opens that URL on their phone, which hits the device verification endpoint (card 0037) — they authenticate normally (username/password or SSO) and type in `WDJB-MJHT`.
5. After the user reviews and approves the requested scopes, the server updates the stored `OAuth2Authorization` for that `device_code` from pending to approved, associating it with the now-authenticated user.
6. Meanwhile, the CLI's poll loop keeps sending `POST /oauth2/token` with `grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=...`. Each attempt before approval returns `400` with `{"error":"authorization_pending"}`, which the poller treats as "keep waiting."
7. The poll immediately after approval finds the `OAuth2Authorization` marked approved, and the token endpoint issues a normal access token (and refresh token, if configured) response — `200 OK` with the token JSON — exactly like the authorization code flow's final token exchange (card 0027).

```
Device                          Auth Server                      User's phone
  |--POST device_authorization-->|
  |<--device_code, user_code-----|
  | (shows user_code + URL)      |
  |                              |<--GET /activate, enter code---|
  |                              |<--login + consent-------------|
  |                              |  (marks device_code approved) |
  |--POST /token (device_code)-->| (still pending) 400 pending
  |--POST /token (device_code)-->| (still pending) 400 pending
  |--POST /token (device_code)-->| (approved!) 200 {access_token}
```

Concrete requests and responses:

```
POST /oauth2/device_authorization
client_id=cli-tool&scope=videos.read

HTTP/1.1 200 OK
{"device_code":"GmRhmhcxhwAzkoEqiMEg_DnyEysNkuNhszIySk9eS","user_code":"WDJB-MJHT","verification_uri":"https://auth.example.com/activate","expires_in":600,"interval":5}

POST /oauth2/token
grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=GmRhmhcxhwAzkoEqiMEg_DnyEysNkuNhszIySk9eS&client_id=cli-tool

HTTP/1.1 400 Bad Request
{"error":"authorization_pending"}

(... after user approves ...)

HTTP/1.1 200 OK
{"access_token":"2YotnFZFEjr1zCsicMWpAA","token_type":"Bearer","expires_in":3600,"scope":"videos.read"}
```

## 7. Gotchas & takeaways

> Polling too fast (ignoring `interval` and `slow_down`) is treated as abuse by a spec-compliant server — hammering `/oauth2/token` every second instead of every `interval` seconds risks the server rate-limiting or outright rejecting the client, so always respect the returned interval and honor `slow_down` by increasing it.

- `device_code` and `user_code` are two different values with two different audiences — `device_code` stays on the device and is used for polling; `user_code` is what gets displayed and typed by the human. Never confuse or swap them in logs or UI.
- The device never receives the user's password or any browser redirect — approval happens entirely out-of-band on a separate, trusted device, which is precisely what makes this flow safe for shared or unattended hardware.
- Always enforce a client-side deadline based on `expires_in` in addition to trusting server error codes (Level 3) — a network blip that drops the final `expired_token` response would otherwise leave a naive poller running forever.
- `user_code` values are deliberately short and often exclude ambiguous characters (like `0`/`O`, `1`/`I`) — don't "improve" this by generating your own opaque UUID-style code if implementing a custom device flow variant; short and typo-resistant is the whole point.
- Device flow is not a substitute for authorization code + PKCE on clients that *can* open a browser — it exists specifically for the input-constrained case and trades away some UX smoothness (a second device, manual code entry) that PKCE doesn't require.
