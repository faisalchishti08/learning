---
card: spring-authorization-server
gi: 38
slug: authorization-code-grant-with-pkce
title: "Authorization code grant with PKCE"
---

## 1. What it is

The authorization code grant is the standard OAuth2 flow for clients that can interact with a browser: the client redirects the user to the authorization endpoint (card 0026), receives a short-lived code back, then exchanges that code for tokens at the token endpoint (card 0027). PKCE (Proof Key for Code Exchange, RFC 7636) is an extension that adds a cryptographic binding between the request that started the flow and the request that redeems the code, and is mandatory for all clients under OAuth 2.1, which Spring Authorization Server targets.

## 2. Why & when

Without PKCE, if an attacker can intercept the authorization code mid-flight (a real risk on mobile, where the redirect goes through a shared OS-level URL scheme handler that other installed apps might also register), they can redeem that code themselves at the token endpoint, since a public client (one with no secret) has nothing else to prove it's the legitimate requester. PKCE closes this by having the client generate a one-time secret (`code_verifier`) before starting the flow, sending only its hash (`code_challenge`) to the authorization endpoint, and later revealing the original secret when redeeming the code — the token endpoint checks the hash matches before it trusts the exchange.

Reach for PKCE-protected authorization code flow when:

- Building any client that involves a browser redirect — single-page apps, mobile apps, and traditional server-side web apps all use this flow, and OAuth 2.1 requires PKCE regardless of client type.
- Deciding how to protect a public client (no client secret, e.g. a SPA or native mobile app) — PKCE is specifically designed to secure exactly this case.
- Debugging an `invalid_grant` error at the token endpoint after an otherwise-successful authorization step — a `code_verifier` mismatch is one of the most common causes.

## 3. Core concept

Think of PKCE like a claim-check ticket torn in half at coat check. Before handing your coat over (starting the authorization request), you tear a ticket in two, keeping one half in your pocket (`code_verifier`) and handing coat check a photograph of the *other* half (`code_challenge`, a hash — not the raw half itself, so a shoulder-surfer photographing the exchange still can't derive your half). Later, when you come to reclaim your coat (redeeming the code), you must show the actual torn half from your pocket, and coat check verifies it matches the photograph they filed. Anyone who *only* stole the claim ticket number (the authorization code) but doesn't have your literal torn-off half (`code_verifier`) can't collect the coat.

```
1) client generates: code_verifier = random 43-128 char string
2) client computes:  code_challenge = BASE64URL(SHA256(code_verifier))
3) /oauth2/authorize?...&code_challenge=E9Melhoa2Ow...&code_challenge_method=S256
4) /oauth2/token with code=... AND code_verifier=<original secret>
```

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client sends a hashed code challenge at authorization time and the raw verifier at token exchange time, server checks they match">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. Generate verifier,</text>
  <text x="110" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">hash to challenge</text>

  <rect x="250" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. /authorize with</text>
  <text x="340" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">code_challenge (hash)</text>

  <rect x="480" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="570" y="43" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. server stores hash,</text>
  <text x="570" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">returns code</text>

  <line x1="200" y1="45" x2="245" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="430" y1="45" x2="475" y2="45" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="250" y="150" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="173" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">4. /token with code +</text>
  <text x="340" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">code_verifier (raw secret)</text>

  <rect x="480" y="150" width="180" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="570" y="173" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">5. hash(verifier) ==</text>
  <text x="570" y="188" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">stored challenge? -&gt; tokens</text>

  <line x1="340" y1="70" x2="340" y2="145" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4"/>
  <line x1="430" y1="175" x2="475" y2="175" stroke="#3fb950" stroke-width="1.5"/>
</svg>

Only the hash ever travels on step 2's request; the raw secret is revealed only once, directly to the server, at the final step.

## 5. Runnable example

The scenario: a Java client implementing the full authorization code + PKCE round trip against a local Spring Authorization Server, growing from generating the PKCE pair, to actually driving the authorize/token exchange over HTTP, to handling token refresh once the access token expires.

### Level 1 — Basic

```java
// PkceGenerator.java
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;

public class PkceGenerator {

    public record PkcePair(String verifier, String challenge) {}

    public PkcePair generate() throws Exception {
        SecureRandom random = new SecureRandom();
        byte[] verifierBytes = new byte[32];
        random.nextBytes(verifierBytes);
        String verifier = Base64.getUrlEncoder().withoutPadding().encodeToString(verifierBytes);

        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        byte[] hash = digest.digest(verifier.getBytes("UTF-8"));
        String challenge = Base64.getUrlEncoder().withoutPadding().encodeToString(hash);

        return new PkcePair(verifier, challenge);
    }

    public static void main(String[] args) throws Exception {
        PkcePair pair = new PkceGenerator().generate();
        System.out.println("code_verifier:  " + pair.verifier());
        System.out.println("code_challenge: " + pair.challenge());
    }
}
```

**How to run:** `java PkceGenerator.java`. Expected output: two related but visually unrelated strings, e.g. `code_verifier: dGhpcyBpcyBhIHRlc3Qgdm...` and `code_challenge: E9Melhoa2OwvFrEMTJguCH...` — the challenge is what gets sent first; the verifier is kept secret until the token exchange.

### Level 2 — Intermediate

A real client drives the full round trip: build the authorize URL with the challenge, capture the redirected-back code (simulated here by printing the URL to visit manually, since a full browser isn't scriptable in this snippet), then exchange the code plus the original verifier for tokens.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;

public class AuthCodeExchange {

    private final HttpClient client = HttpClient.newHttpClient();

    public String buildAuthorizeUrl(String challenge) {
        return "http://localhost:8080/oauth2/authorize"
                + "?response_type=code"
                + "&client_id=task-tracker"
                + "&redirect_uri=" + URLEncoder.encode("https://task-tracker.example.com/callback", StandardCharsets.UTF_8)
                + "&scope=tasks.read"
                + "&code_challenge=" + challenge
                + "&code_challenge_method=S256";
    }

    public String exchangeCodeForToken(String code, String verifier) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(
                        "grant_type=authorization_code"
                                + "&code=" + code
                                + "&redirect_uri=" + URLEncoder.encode("https://task-tracker.example.com/callback", StandardCharsets.UTF_8)
                                + "&client_id=task-tracker"
                                + "&code_verifier=" + verifier))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        return response.body();
    }
}
```

**How to run:** call `buildAuthorizeUrl(challenge)` from Level 1's generated challenge, open the printed URL in a browser, log in and approve, copy the `code` query parameter from the redirected URL, then call `exchangeCodeForToken(code, verifier)` with the *original* verifier. Expected output: a JSON body containing `access_token` and (if configured) `refresh_token`.

What changed: this now performs the actual two-legged exchange against a running server, proving the challenge/verifier pair really does gate token issuance — swapping in a different (wrong) verifier at this step causes the server to reject the exchange.

### Level 3 — Advanced

Production clients need to handle the access token expiring and use the refresh token (card 0040) to get a new one without forcing the user through the browser flow again — and must securely persist the verifier only for the brief window between redirect and exchange, never longer.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Instant;

public class TokenLifecycleClient {

    private final HttpClient client = HttpClient.newHttpClient();
    private String accessToken;
    private String refreshToken;
    private Instant expiresAt;

    public void handleTokenResponse(String jsonBody, long expiresInSeconds, String accessTok, String refreshTok) {
        this.accessToken = accessTok;
        this.refreshToken = refreshTok;
        this.expiresAt = Instant.now().plusSeconds(expiresInSeconds);
    }

    public String getValidAccessToken() throws Exception {
        if (Instant.now().isBefore(expiresAt.minusSeconds(30))) {
            return accessToken; // still valid with a 30s safety margin
        }
        // Expired or about to expire: use the refresh token, no browser interaction needed.
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://localhost:8080/oauth2/token"))
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(
                        "grant_type=refresh_token"
                                + "&refresh_token=" + refreshToken
                                + "&client_id=task-tracker"))
                .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        if (response.statusCode() != 200) {
            throw new IllegalStateException("Refresh failed, user must re-authenticate: " + response.body());
        }
        // In a real client, parse the JSON body here to update accessToken/refreshToken/expiresAt.
        return response.body();
    }
}
```

**How to run:** after the Level 2 exchange, call `handleTokenResponse(...)` with the parsed response, then call `getValidAccessToken()` repeatedly — before expiry it returns the cached token instantly with no network call; after expiry it silently refreshes. Force an expired `refreshToken` too (e.g. one already revoked, card 0029): expect an `IllegalStateException` signaling the app must fall back to a full browser-based re-authentication.

What changed and why it's production-flavored: the `code_verifier` is discarded immediately after Level 2's single-use exchange (it's never needed again), while ongoing access is now sustained via the longer-lived refresh token — matching how real apps avoid re-prompting users for login on every token expiry, while still failing safely when the refresh token itself is no longer valid.

## 6. Walkthrough

Tracing the full PKCE-protected authorization code flow, in execution order:

1. The client generates `code_verifier` (a random string) and derives `code_challenge = BASE64URL(SHA256(code_verifier))` — this happens entirely client-side, before any network call.
2. The client redirects the browser to the authorization endpoint (card 0026) with `code_challenge` and `code_challenge_method=S256` in the query string — the verifier itself is never sent yet.
3. The server validates the request, authenticates the user, and (if needed) shows consent — exactly the flow traced in card 0026 — then stores the `code_challenge` alongside the newly issued authorization code in an `OAuth2Authorization` (card 0016).
4. The server redirects back to the client with `?code=SplxlOBeZQQYbYS6WxSbIA&state=...`.
5. The client immediately sends `POST /oauth2/token` with `grant_type=authorization_code`, the received `code`, and — critically — the original `code_verifier` it generated in step 1 and has been holding onto since.
6. The token endpoint (card 0027) looks up the stored authorization by `code`, recomputes `SHA256(code_verifier)` from the request, and compares it byte-for-byte against the `code_challenge` stored in step 3.
7. If they match, the server issues access and refresh tokens and responds `200 OK`; if they don't match (wrong or missing verifier), it responds `400 Bad Request` with `error=invalid_grant` and no tokens are issued — regardless of how correct everything else about the request was.

```
Client                                    Authorization Server
  | 1. generate verifier, hash -> challenge
  | 2. GET /authorize?code_challenge=...   |
  |----------------------------------------->
  |                                         | 3. validate, auth, consent
  |                                         |    store challenge with code
  | 4. 302 -> redirect_uri?code=...         |
  <-----------------------------------------|
  | 5. POST /token code=...&code_verifier=..|
  |----------------------------------------->
  |                                         | 6. hash(verifier) == stored challenge?
  | 7a. 200 OK {access_token, refresh_token}| (match)
  <-----------------------------------------|
  | 7b. 400 invalid_grant                   | (mismatch)
  <-----------------------------------------|
```

Concrete request and response for the final exchange:

```
POST /oauth2/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=SplxlOBeZQQYbYS6WxSbIA&redirect_uri=https%3A%2F%2Ftask-tracker.example.com%2Fcallback&client_id=task-tracker&code_verifier=dGhpcyBpcyBhIHRlc3Qgdm...

HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"2YotnFZFEjr1zCsicMWpAA","token_type":"Bearer","expires_in":3600,"refresh_token":"tGzv3JOkF0XG5Qx2TlKWIA","scope":"tasks.read"}
```

## 7. Gotchas & takeaways

> Never persist `code_verifier` anywhere durable (local storage, a database, disk) beyond the short window between the authorize redirect and the token exchange — it exists purely to be revealed once, and holding onto it any longer only recreates the same interception risk PKCE was designed to remove.

- `code_challenge_method=S256` (SHA-256 hash) should always be used over the deprecated `plain` method (where the challenge equals the verifier unhashed) — `plain` provides no protection at all if the challenge itself is intercepted, and OAuth 2.1 effectively mandates `S256`.
- A mismatched or missing `code_verifier` at the token endpoint produces `invalid_grant`, the same generic error used for several other authorization-code failures (expired code, reused code) — don't assume it's specifically a PKCE issue without checking the request body carefully.
- Authorization codes are single-use — reusing a code (even with the correct verifier) after it's already been exchanged once is treated as a replay and rejected, which is why the client must exchange it immediately rather than caching it.
- PKCE protects the code exchange step specifically; it does not replace `state` for CSRF protection (card 0026) — both should be present, since they defend against different attacks.
- For confidential clients (those with a real client secret, typically server-side web apps), PKCE is still required under OAuth 2.1 even though the client secret already provides some protection — defense in depth, not an either/or choice.
