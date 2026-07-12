---
card: spring-authorization-server
gi: 15
slug: grant-types-per-client
title: "Grant types per client"
---

## 1. What it is

A grant type (`AuthorizationGrantType`) is a named OAuth2 flow for obtaining a token — `authorization_code`, `refresh_token`, `client_credentials`, and Spring Authorization Server's own `urn:ietf:params:oauth:grant-type:device_code` for device flow. Each `RegisteredClient` declares which grant types it's permitted to use via `.authorizationGrantType(...)`, and the server enforces this as a hard allow-list: a request using any grant type not listed for that client is rejected with `unauthorized_client`, regardless of how correct everything else about the request is.

## 2. Why & when

Different applications fundamentally interact with users differently, and the grant type is what matches the OAuth2 flow to that interaction pattern. A browser-based app has a user present to log in interactively. A backend service running a nightly batch job has no user at all. A smart TV or CLI tool has no convenient browser to redirect through. Locking each client to only the grant types its actual use case needs isn't a formality — it's what prevents, say, a batch job's credentials from being usable to silently impersonate a user via a code flow they were never meant to support.

Reach for each grant type when:

- **`authorization_code`** — any client with a real user present who can log in through a browser (web apps, mobile apps, SPAs); this is the default, most common flow, always paired with a redirect URI.
- **`refresh_token`** — added alongside `authorization_code` (or `client_credentials`) whenever a client should be able to get new access tokens without forcing the user to log in again every time the token expires.
- **`client_credentials`** — service-to-service calls with no user involved at all; the client authenticates as itself and receives a token representing the *application*, not a person.
- **Device code (`urn:ietf:params:oauth:grant-type:device_code`)** — input-constrained devices (smart TVs, IoT devices, CLI tools) that show the user a code to enter on a separate device with a proper browser.

## 3. Core concept

Think of grant types as different keys cut for different doors, all issued by the same locksmith (the authorization server). `authorization_code` is the key cut after checking someone's ID in person (the user logs in and consents). `client_credentials` is a key cut for the building's own maintenance staff — no tenant ID is checked, because the staff isn't acting on behalf of any particular tenant, only on behalf of the building itself. `refresh_token` isn't a separate door at all — it's a keycard the locksmith will exchange for a *fresh* key without re-checking ID, as long as the keycard itself is still valid. A `RegisteredClient`'s grant type list is simply which of these keys the locksmith is willing to cut for that particular applicant.

```java
RegisteredClient.withId(UUID.randomUUID().toString())
    .clientId("nightly-report-job")
    .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
    .scope("reports.generate")
    .build();
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Different client types map to different allowed grant types">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Web app (user present)</text>

  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Batch job (no user)</text>

  <rect x="440" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Smart TV (no browser)</text>

  <rect x="20" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">authorization_code</text>
  <text x="110" y="162" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">+ refresh_token</text>

  <rect x="230" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">client_credentials</text>

  <rect x="440" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">device_code</text>

  <line x1="110" y1="70" x2="110" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="70" x2="320" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="530" y1="70" x2="530" y2="118" stroke="#3fb950" stroke-width="2"/>
</svg>

Each client's real-world shape determines which grant type actually fits its login capabilities.

## 5. Runnable example

The scenario: task-tracker starts as a plain web app using authorization code, then gains a companion nightly export job, then gains a CLI tool for developers without a full browser.

### Level 1 — Basic

```java
// GrantTypeDemo.java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class GrantTypeDemo {
    public static void main(String[] args) {
        RegisteredClient webApp = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .redirectUri("https://task-tracker.example.com/login/oauth2/code/task-tracker")
                .scope("tasks.read")
                .build();

        System.out.println("Grant types: " + webApp.getAuthorizationGrantTypes());
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java GrantTypeDemo.java`. Expected output:

```
Grant types: [authorization_code]
```

Without `refresh_token` added too, this client must send the user through a fresh login every time its access token expires.

### Level 2 — Intermediate

A separate nightly job needs to call the task-tracker API with no user involved, so it's registered as its own client using `client_credentials` — deliberately *not* sharing the web app's client ID, since they represent fundamentally different actors.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;

import java.util.UUID;

public class GrantTypeDemo {
    public static void main(String[] args) {
        RegisteredClient webApp = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker")
                .clientSecret("{noop}secret")
                .authorizationGrantType(AuthorizationGrantType.AUTHORIZATION_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .redirectUri("https://task-tracker.example.com/login/oauth2/code/task-tracker")
                .scope("tasks.read")
                .build();

        RegisteredClient nightlyJob = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker-export-job")
                .clientSecret("{noop}job-secret")
                .authorizationGrantType(AuthorizationGrantType.CLIENT_CREDENTIALS)
                .scope("tasks.export")
                .build();

        System.out.println("Web app grants: " + webApp.getAuthorizationGrantTypes());
        System.out.println("Job grants: " + nightlyJob.getAuthorizationGrantTypes());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Web app grants: [authorization_code, refresh_token]
Job grants: [client_credentials]
```

What changed: the web app can now silently refresh expired tokens without a re-login, and the nightly job gets its own, entirely separate client identity scoped only to `tasks.export` — even if the job's credentials leaked, they couldn't be used to impersonate any user, because `client_credentials` tokens never represent a user in the first place.

### Level 3 — Advanced

A CLI tool for developers can't easily open an embedded browser or receive a redirect on a fixed port in every environment (e.g. inside a remote SSH session), so it's registered for the device code grant — the user is shown a short code, visits a URL on a separate device with a real browser, and enters it there.

```java
import org.springframework.security.oauth2.core.AuthorizationGrantType;
import org.springframework.security.oauth2.core.ClientAuthenticationMethod;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.settings.ClientSettings;

import java.util.UUID;

public class GrantTypeDemo {
    public static void main(String[] args) {
        RegisteredClient cliTool = RegisteredClient.withId(UUID.randomUUID().toString())
                .clientId("task-tracker-cli")
                .clientAuthenticationMethod(ClientAuthenticationMethod.NONE)
                .authorizationGrantType(AuthorizationGrantType.DEVICE_CODE)
                .authorizationGrantType(AuthorizationGrantType.REFRESH_TOKEN)
                .scope("tasks.read")
                .clientSettings(ClientSettings.builder().requireAuthorizationConsent(true).build())
                .build();

        System.out.println("CLI grants: " + cliTool.getAuthorizationGrantTypes());
    }
}
```

**How to run:** same as Level 1. Expected output:

```
CLI grants: [urn:ietf:params:oauth:grant-type:device_code, refresh_token]
```

What changed and why it's production-flavored: the CLI tool never handles a redirect URI at all — it polls the token endpoint with a `device_code` while the human completes login on a phone or laptop, which is the only practical flow for a terminal-only environment, and pairing it with `refresh_token` avoids repeating that two-device dance every time the token expires.

## 6. Walkthrough

Tracing the device code flow end to end, in execution order, since it's the least familiar of the three:

1. The CLI tool sends `POST /oauth2/device_authorization` with `client_id=task-tracker-cli&scope=tasks.read`.
2. The server responds with a JSON body: `{"device_code": "...", "user_code": "WDJB-MJHT", "verification_uri": "https://auth.example.com/activate", "expires_in": 600, "interval": 5}`.
3. The CLI prints `Go to https://auth.example.com/activate and enter code WDJB-MJHT` and begins polling `POST /oauth2/token` with `grant_type=urn:ietf:params:oauth:grant-type:device_code&device_code=...` every 5 seconds (the `interval`).
4. Meanwhile, the user opens that URL on their phone, logs in, types in `WDJB-MJHT`, and approves the `tasks.read` scope on the consent screen.
5. On the CLI's *next* poll after approval, the token endpoint — having matched the `device_code` to the now-approved `user_code` internally — responds `200 OK` with a normal token response body: `{"access_token": "...", "refresh_token": "...", "token_type": "Bearer", "expires_in": 3600}`.
6. Before that approval happens, every poll instead receives `400 Bad Request` with `{"error": "authorization_pending"}`, telling the CLI to simply wait and retry rather than treat it as a failure.
7. The CLI tool stores the access and refresh tokens locally and uses them for subsequent API calls, refreshing via `grant_type=refresh_token` once the access token expires — never needing the two-device dance again until the refresh token itself expires.

```
CLI                                    Server                              User's phone
 |--POST /oauth2/device_authorization-->|
 |<--device_code, user_code, url---------|
 |  (prints code + URL to terminal)
 |                                       |<----- user visits url, enters code, logs in, approves
 |--POST /oauth2/token (device_code)---->|
 |<--400 authorization_pending-----------|   (before approval)
 |--POST /oauth2/token (device_code)---->|
 |<--200 access_token + refresh_token----|   (after approval)
```

## 7. Gotchas & takeaways

> Never register `client_credentials` alongside `authorization_code` on the *same* `RegisteredClient` unless you deliberately intend that client to be usable both as a user-facing app and as a service-to-service caller — mixing them muddies what a given token actually represents (a user, or the application itself), which downstream authorization logic often assumes is one or the other.

- A grant type not listed on the `RegisteredClient` is rejected with `unauthorized_client`, even if the request is otherwise perfectly formed — this is the first thing to check when a specific flow "just doesn't work" for one client but does for another.
- `client_credentials` tokens have no associated user — code on the resource server that assumes `Authentication.getName()` is always a real username will break when handling these tokens; check for this explicitly.
- Device code flow requires polling discipline: ignoring the returned `interval` and polling faster can get the client rate-limited or temporarily blocked (`slow_down` error).
- Always pair `refresh_token` with any interactive grant (`authorization_code`, `device_code`) unless there's a specific reason to force re-authentication on every expiry.
- Keep grant types minimal per client — a client that only ever needs `client_credentials` should not also be granted `authorization_code`, since every additional grant type is additional attack surface if that client's credentials are ever compromised.
