---
card: spring-security
gi: 90
slug: authorization-code-grant-flow
title: "Authorization Code grant flow"
---

## 1. What it is

The Authorization Code grant is the specific OAuth2 protocol — defined by RFC 6749 — that cards 0088 and 0089 have been building toward: the exact sequence of redirects and parameters that lets a browser prove a user authenticated with a provider, without the provider's password ever passing through the client application or being visible in a URL that could be logged or leaked. Its defining feature is that the **code** obtained via the browser is short-lived and single-use, and the **exchange** of that code for an actual access token happens over a direct, authenticated, server-to-server channel — a `client_secret` proves it's really the registered application asking, not just anyone who intercepted the code. Spring Security implements the two halves as two separate filters: `OAuth2AuthorizationRequestRedirectFilter` builds and sends the initial redirect (and remembers the request it sent, including a `state` value, for later verification), and `OAuth2LoginAuthenticationFilter` (already introduced in card 0088) handles the callback and drives the code-for-token exchange via a `OAuth2AccessTokenResponseClient`.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.oauth2Login(oauth2 -> oauth2
        .authorizationEndpoint(auth -> auth.baseUri("/oauth2/authorization"))
        .redirectionEndpoint(redir -> redir.baseUri("/login/oauth2/code/*")));
    return http.build();
}
```

The defaults shown here (`/oauth2/authorization/{registrationId}` to start, `/login/oauth2/code/{registrationId}` to receive the callback) are rarely overridden — they exist mostly to show that these are configurable paths, not magic strings baked into the protocol itself.

## 2. Why & when

Earlier OAuth2 grant types (the deprecated Implicit grant, Resource Owner Password Credentials) either exposed tokens directly in a browser-visible URL fragment or required the client application to collect the user's password itself — both defeat the entire point of delegating authentication. The Authorization Code grant's two-hop design (browser gets a code, server exchanges it for a token) exists specifically so that the only thing ever visible to the browser, and therefore to browser history, referrer headers, or a shoulder-surfing observer, is a single-use code that is useless without also knowing the client's secret. This is why it remains the recommended grant for any application with a confidential backend server — which is the overwhelming majority of what `oauth2Login()` is used for.

Reach for understanding this flow in detail when:

- Debugging a login that fails partway through — nearly every failure (`redirect_uri_mismatch`, `invalid_grant`, a `state` mismatch) corresponds to exactly one step below going wrong, and knowing which step lets you read the error correctly.
- Explaining to a security reviewer why access tokens never appear in browser-accessible logs — the code-for-token exchange is the one hop in the entire flow that never touches the browser.
- Deciding whether PKCE (Proof Key for Code Exchange) is needed — required for public clients (mobile apps, single-page apps with no confidential backend) that can't safely hold a `client_secret`, and Spring Security's `authorization_code` support enables it automatically for such clients.
- Implementing `client_credentials` or `refresh_token` grants (card 0094) — understanding what makes the authorization code grant distinct (a code obtained via user interaction) clarifies why those other grants skip the browser redirect entirely.

## 3. Core concept

```
Authorization Code grant, in order:

  1. Client app redirects browser to authorization endpoint, with:
       response_type=code, client_id, redirect_uri, scope, state (CSRF nonce)
  2. User authenticates + consents AT the provider (invisible to the client app)
  3. Provider redirects browser back to redirect_uri, with:
       code (short-lived, single-use), state (echoed back UNCHANGED)
  4. Client app verifies the echoed `state` matches what it sent in step 1
       -- MISMATCH means this callback wasn't triggered by THIS app's own redirect: reject it (CSRF protection)
  5. Client app's SERVER exchanges the code, server-to-server:
       POST token endpoint: grant_type=authorization_code, code, redirect_uri, client_id, client_secret
  6. Provider validates the code (unused? not expired? redirect_uri matches step 1?) and returns:
       access_token, (refresh_token), (id_token if OIDC), expires_in
  7. Client app now has a token it can use to call APIs -- and card 0088's userinfo fetch can proceed
```

Steps 1–4 are entirely visible to (and partly protected by) the browser; steps 5–6 are the one hop that never is.

## 4. Diagram

<svg viewBox="0 0 660 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence diagram showing the client app redirecting the browser to the authorization endpoint with a state value the browser authenticating at the provider and being redirected back with a code and the same state which the client app verifies matches before exchanging the code for a token directly with the provider over a server to server channel">
  <text x="90" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Client Server</text>
  <text x="330" y="24" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="580" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Provider</text>

  <line x1="90" y1="35" x2="90" y2="285" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="330" y1="35" x2="330" y2="285" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="580" y1="35" x2="580" y2="285" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <rect x="40" y="50" width="220" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="150" y="69" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">1. generate state=xyz, store it</text>

  <line x1="90" y1="100" x2="325" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#g90)"/>
  <text x="95" y="93" fill="#e6edf3" font-size="8.5" font-family="sans-serif">2. 302 -> authorize?...&amp;state=xyz</text>

  <line x1="330" y1="128" x2="575" y2="128" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#g90)"/>
  <text x="335" y="121" fill="#e6edf3" font-size="8.5" font-family="sans-serif">3. GET /authorize (login + consent)</text>

  <line x1="580" y1="156" x2="335" y2="156" stroke="#8b949e" stroke-width="1.5" marker-end="url(#g90c)"/>
  <text x="575" y="149" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">4. 302 -> redirect_uri?code=..&amp;state=xyz</text>

  <line x1="330" y1="184" x2="95" y2="184" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#g90)"/>
  <text x="330" y="177" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">5. GET callback?code=..&amp;state=xyz</text>

  <rect x="40" y="196" width="220" height="26" rx="5" fill="#1c2430" stroke="#f85149" stroke-width="1.2"/>
  <text x="150" y="213" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="sans-serif">6. state=xyz == stored xyz ? else REJECT</text>

  <line x1="90" y1="240" x2="575" y2="240" stroke="#6db33f" stroke-width="1.6" stroke-dasharray="6,3" marker-end="url(#g90b)"/>
  <text x="95" y="233" fill="#6db33f" font-size="8.5" font-family="sans-serif">7. POST /token (code, client_secret) -- browser NOT involved</text>

  <line x1="580" y1="266" x2="95" y2="266" stroke="#8b949e" stroke-width="1.6" stroke-dasharray="6,3" marker-end="url(#g90c)"/>
  <text x="575" y="259" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">8. access_token (+ refresh_token, id_token)</text>

  <defs>
    <marker id="g90" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="g90b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="g90c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`state` is generated before the redirect and verified after the callback; only a matching pair lets the exchange in step 7 proceed.

## 5. Runnable example

The scenario: a from-scratch simulation of the grant's mechanics — a `Client` that starts the flow and holds pending `state` values, an `AuthorizationServer` that issues codes and later tokens — grown from a bare happy path into `state` verification, then into single-use/expiring codes.

### Level 1 — Basic

The bare happy path: request a code, exchange it for a token.

```java
import java.util.*;

public class AuthCodeGrantLevel1 {
    static class AuthorizationServer {
        private final Map<String, String> issuedCodes = new HashMap<>(); // code -> username
        private int counter = 0;

        String authorize(String username) {
            String code = "code-" + (++counter); // provider mints a fresh, unpredictable code
            issuedCodes.put(code, username);
            return code;
        }

        String exchange(String code, String clientSecret) {
            if (!"correct-secret".equals(clientSecret)) throw new IllegalStateException("invalid_client");
            String username = issuedCodes.get(code);
            if (username == null) throw new IllegalStateException("invalid_grant: unknown code");
            return "access-token-for-" + username;
        }
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();

        // step 1-4 collapsed: user authenticates at the provider, browser comes back with a code
        String code = server.authorize("alice");
        System.out.println("received code: " + code);

        // step 5-6: server-to-server exchange
        String accessToken = server.exchange(code, "correct-secret");
        System.out.println("access token: " + accessToken);
    }
}
```

**How to run:** save as `AuthCodeGrantLevel1.java`, run `java AuthCodeGrantLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
received code: code-1
access token: access-token-for-alice
```

`authorize` stands in for the entire browser round trip (steps 1–4 of the core concept); `exchange` stands in for the server-to-server hop (steps 5–6) and requires the correct `client_secret`, mirroring how the provider authenticates the *client application itself*, separately from the end user.

### Level 2 — Intermediate

Add `state` generation and verification — the CSRF defense that step 4 of the core concept depends on — modeled as a `Client` that tracks its own pending states.

```java
import java.util.*;

public class AuthCodeGrantLevel2 {
    static class AuthorizationServer {
        private final Map<String, String> issuedCodes = new HashMap<>();
        private int counter = 0;

        String authorize(String username) {
            String code = "code-" + (++counter);
            issuedCodes.put(code, username);
            return code;
        }

        String exchange(String code, String clientSecret) {
            if (!"correct-secret".equals(clientSecret)) throw new IllegalStateException("invalid_client");
            String username = issuedCodes.remove(code); // consumed here in Level 3, tracked from Level 2 on
            if (username == null) throw new IllegalStateException("invalid_grant: unknown code");
            return "access-token-for-" + username;
        }
    }

    static class Client {
        private final Set<String> pendingStates = new HashSet<>();
        private int stateCounter = 0;

        // step 1: build the redirect, remembering the state we sent
        String startLogin() {
            String state = "state-" + (++stateCounter);
            pendingStates.add(state);
            System.out.println("redirecting browser with state=" + state);
            return state;
        }

        // step 6: verify the callback's state matches something WE generated
        void verifyState(String returnedState) {
            if (!pendingStates.remove(returnedState)) {
                throw new IllegalStateException("state mismatch -- possible CSRF, rejecting callback");
            }
        }
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();
        Client client = new Client();

        String state = client.startLogin();
        String code = server.authorize("alice");

        // callback arrives carrying the SAME state the provider echoed back
        client.verifyState(state);
        System.out.println("state verified, proceeding with exchange");

        String accessToken = server.exchange(code, "correct-secret");
        System.out.println("access token: " + accessToken);

        // an attacker's forged callback, with a state the client never generated
        try {
            client.verifyState("state-forged-by-attacker");
        } catch (IllegalStateException e) {
            System.out.println("forged callback rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `AuthCodeGrantLevel2.java`, run `java AuthCodeGrantLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
redirecting browser with state=state-1
state verified, proceeding with exchange
access token: access-token-for-alice
forged callback rejected: state mismatch -- possible CSRF, rejecting callback
```

What changed: `Client` now tracks every `state` it generates and requires the callback to present one of them before continuing — a forged callback (one an attacker tricked a victim's browser into visiting, carrying the attacker's own code) is rejected here because its `state` was never issued by *this* client's own `startLogin` call, which is precisely the cross-site request forgery this parameter defends against.

### Level 3 — Advanced

Real codes are single-use and expire quickly. Level 3 adds both: exchanging the same code twice fails, and a code presented after its short lifetime has elapsed fails too, mirroring the two most common `invalid_grant` causes in production.

```java
import java.time.*;
import java.util.*;

public class AuthCodeGrantLevel3 {
    record IssuedCode(String username, Instant expiresAt) {}

    static class AuthorizationServer {
        private final Map<String, IssuedCode> issuedCodes = new HashMap<>();
        private int counter = 0;
        private final Duration codeLifetime;

        AuthorizationServer(Duration codeLifetime) { this.codeLifetime = codeLifetime; }

        String authorize(String username) {
            String code = "code-" + (++counter);
            issuedCodes.put(code, new IssuedCode(username, Instant.now().plus(codeLifetime)));
            return code;
        }

        String exchange(String code, String clientSecret) {
            if (!"correct-secret".equals(clientSecret)) throw new IllegalStateException("invalid_client");
            // remove() makes the code single-use: a second exchange attempt finds nothing
            IssuedCode issued = issuedCodes.remove(code);
            if (issued == null) throw new IllegalStateException("invalid_grant: code unknown or already used");
            if (Instant.now().isAfter(issued.expiresAt())) throw new IllegalStateException("invalid_grant: code expired");
            return "access-token-for-" + issued.username();
        }
    }

    static class Client {
        private final Set<String> pendingStates = new HashSet<>();
        private int stateCounter = 0;

        String startLogin() {
            String state = "state-" + (++stateCounter);
            pendingStates.add(state);
            return state;
        }

        void verifyState(String returnedState) {
            if (!pendingStates.remove(returnedState)) throw new IllegalStateException("state mismatch");
        }
    }

    public static void main(String[] args) throws InterruptedException {
        AuthorizationServer server = new AuthorizationServer(Duration.ofMillis(50)); // deliberately short, for this demo
        Client client = new Client();

        String state = client.startLogin();
        String code = server.authorize("alice");
        client.verifyState(state);

        // FIRST exchange: succeeds
        String accessToken = server.exchange(code, "correct-secret");
        System.out.println("first exchange: " + accessToken);

        // REPLAY: same code, exchanged a second time -- must fail, codes are single-use
        try {
            server.exchange(code, "correct-secret");
        } catch (IllegalStateException e) {
            System.out.println("replay rejected: " + e.getMessage());
        }

        // a SECOND, fresh code that is allowed to expire before it's ever exchanged
        String state2 = client.startLogin();
        String slowCode = server.authorize("bob");
        client.verifyState(state2);
        Thread.sleep(100); // simulate a slow network / user delay past the code's short lifetime

        try {
            server.exchange(slowCode, "correct-secret");
        } catch (IllegalStateException e) {
            System.out.println("expired code rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `AuthCodeGrantLevel3.java`, run `java AuthCodeGrantLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
first exchange: access-token-for-alice
replay rejected: invalid_grant: code unknown or already used
expired code rejected: invalid_grant: code expired
```

What changed: `issuedCodes.remove(code)` (rather than a non-destructive `get`) makes every code single-use — a second exchange attempt with the same code, whether from a genuine retry or an attacker who intercepted it in transit, finds nothing left to consume; and each code now carries its own `expiresAt`, rejecting an exchange that arrives too late even if the code was never used, mirroring a provider's typical code lifetime of well under a minute.

## 6. Walkthrough

Trace Level 3's full happy path — `client.startLogin()` through `server.exchange(code, "correct-secret")` for alice — as a concrete HTTP exchange, then show why the replay fails.

**Step 1 — the client builds and remembers a `state`, then redirects:**
```
GET /oauth2/authorization/github HTTP/1.1
Host: app.example.com
```
```
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?response_type=code&client_id=abc123&redirect_uri=https%3A%2F%2Fapp.example.com%2Flogin%2Foauth2%2Fcode%2Fgithub&scope=read:user&state=state-1
```
This corresponds to `client.startLogin()` returning `"state-1"` and the client remembering it in `pendingStates`.

**Step 2 — the user authenticates and consents at the provider** (outside the code entirely — `server.authorize("alice")` is the point where the provider has already decided to let this login proceed and is about to hand back a code).

**Step 3 — the provider redirects back, echoing `state` unchanged:**
```
HTTP/1.1 302 Found
Location: https://app.example.com/login/oauth2/code/github?code=code-1&state=state-1
```

**Step 4 — the callback request arrives:**
```
GET /login/oauth2/code/github?code=code-1&state=state-1 HTTP/1.1
Host: app.example.com
```
`client.verifyState("state-1")` removes `"state-1"` from `pendingStates` and finds it present — the callback is accepted as genuinely originating from this client's own redirect, not a forged one.

**Step 5 — the server-to-server exchange, never touching the browser:**
```
POST /login/oauth/access_token HTTP/1.1
Host: github.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=code-1&redirect_uri=https%3A%2F%2Fapp.example.com%2Flogin%2Foauth2%2Fcode%2Fgithub&client_id=abc123&client_secret=correct-secret
```
This corresponds to `server.exchange("code-1", "correct-secret")`: inside, `issuedCodes.remove("code-1")` both retrieves and deletes the entry in one step, returning `IssuedCode("alice", expiresAt)`; the expiry check passes (only a few milliseconds have elapsed); the method returns `"access-token-for-alice"`.

**Step 6 — the provider's real response would look like:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"access-token-for-alice","token_type":"Bearer","expires_in":3600}
```

**Step 7 — the replay.** A second `server.exchange("code-1", "correct-secret")` call re-runs `issuedCodes.remove("code-1")` — but the entry was already deleted in step 5, so `remove` returns `null`, and the method throws `invalid_grant: code unknown or already used` immediately, before the expiry check is even reached.

```
first call:  remove("code-1") -> IssuedCode(alice, ...)   [found + deleted together]
second call: remove("code-1") -> null                      [nothing left to find]
             -> invalid_grant
```

## 7. Gotchas & takeaways

> **Gotcha:** a mismatched or missing `state` on the callback should always be treated as a hard failure, never logged-and-ignored — it is the one check standing between "this callback genuinely followed from a redirect this application itself issued" and a cross-site request forgery where an attacker tricks a victim's browser into completing a login (or account-linking flow) the attacker initiated, potentially binding the victim's session to the attacker's provider account.

- The Authorization Code grant's two-hop shape — browser gets a code, server exchanges it for a token — exists so the actual access token never appears anywhere the browser (or its history, or a referrer header) can see it.
- `state` is generated before the redirect and must be verified after the callback; a mismatch means the callback did not originate from this application's own redirect and must be rejected.
- Authorization codes are single-use and short-lived by design — `invalid_grant` on exchange almost always means one of those two properties was violated (a retry reused an already-consumed code, or too much time elapsed between redirect and exchange).
- The exchange step requires a `client_secret`, authenticating the *application*, not the user — this is why public clients that cannot safely hold a secret (mobile apps, SPAs) need PKCE as an additional layer rather than relying on the secret alone.
- Everything covered here is the mechanics `oauth2Login()` (card 0088) drives automatically and `ClientRegistration` (card 0089) configures — application code essentially never implements this exchange by hand.
