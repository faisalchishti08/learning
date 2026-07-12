---
card: spring-authorization-server
gi: 27
slug: token-endpoint
title: "Token endpoint"
---

## 1. What it is

The token endpoint (`POST /oauth2/token` by default) is where a client actually obtains tokens — by exchanging an authorization code, presenting a refresh token, authenticating via `client_credentials`, or polling with a device code. Internally it's `OAuth2TokenEndpointFilter`, which delegates to a chain of `AuthenticationProvider` implementations, one per grant type (`OAuth2AuthorizationCodeAuthenticationProvider`, `OAuth2RefreshTokenAuthenticationProvider`, `OAuth2ClientCredentialsAuthenticationProvider`, `OAuth2DeviceCodeAuthenticationProvider`), each responsible for validating and fulfilling its specific grant.

## 2. Why & when

The authorization endpoint (card 0026) only ever produces a code — the actual tokens a client needs to call APIs are minted here, at the token endpoint, and only after the client itself authenticates (card 0012). Separating these two endpoints is what makes the authorization code flow secure against a code being intercepted in the browser's URL bar or referrer headers: a stolen code alone is useless without also passing the token endpoint's client authentication (and, for public clients, PKCE) check.

You interact with the token endpoint whenever:

- Completing any authorization code flow — this is always the second step, immediately following a successful redirect from the authorization endpoint.
- Implementing a service-to-service integration using `client_credentials` — this is the *only* endpoint such a client ever calls.
- Refreshing an expired access token (card 0023) — every refresh is a fresh call here with `grant_type=refresh_token`.
- Debugging `invalid_client`, `invalid_grant`, or `unauthorized_client` errors — all three come from this endpoint's validation logic, and the error code itself narrows down which check failed.

## 3. Core concept

If the authorization endpoint is the hotel check-in desk that hands out a room key voucher (the code), the token endpoint is the actual key-cutting counter downstairs — you bring your voucher *and* your own ID (client authentication) to this counter, and only then do you get the physical room key (the access token) plus a spare key for later (the refresh token). Different grant types are like different kinds of vouchers accepted at the same counter: a check-in voucher (authorization code), a returning-guest membership card (refresh token), or a staff badge that needs no guest voucher at all (client credentials).

```
POST /oauth2/token
Authorization: Basic dGFzay10cmFja2VyOnNlY3JldA==
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=SplxlOBeZQQYbYS6WxSbIA
&redirect_uri=https://task-tracker.example.com/callback
&code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Token endpoint routes each grant_type to its own authentication provider">
  <rect x="240" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="48" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OAuth2TokenEndpointFilter</text>

  <rect x="20" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">authorization_code provider</text>

  <rect x="185" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">refresh_token provider</text>

  <rect x="350" y="120" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="425" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">client_credentials provider</text>

  <rect x="515" y="120" width="105" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="567" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">device_code provider</text>

  <line x1="320" y1="66" x2="95" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="66" x2="260" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="66" x2="425" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="320" y1="66" x2="567" y2="118" stroke="#3fb950" stroke-width="2"/>

  <text x="320" y="210" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">routed by the request's grant_type parameter</text>
</svg>

One endpoint, one filter, dispatched to a dedicated provider per `grant_type`.

## 5. Runnable example

The scenario: exchanging task-tracker's authorization code for tokens, then handling a client_credentials service call, and finally adding defensive error-response shaping so clients get consistent, spec-compliant error bodies.

### Level 1 — Basic

```java
// TokenEndpointDemo.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class TokenEndpointDemo {
    public static void main(String[] args) throws Exception {
        String credentials = Base64.getEncoder().encodeToString("task-tracker:secret".getBytes());
        String body = "grant_type=authorization_code"
                + "&code=SplxlOBeZQQYbYS6WxSbIA"
                + "&redirect_uri=https://task-tracker.example.com/callback";

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/token"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body: " + response.body());
    }
}
```

**How to run:** requires a live, running authorization server with `task-tracker` registered and a real, unredeemed authorization code (obtained by first completing the browser flow from card 0026); run via `java TokenEndpointDemo.java` (uses only JDK built-ins, no extra dependencies). Expected output against a valid code:

```
Status: 200
Body: {"access_token":"eyJhbGciOi...","refresh_token":"8xL3k9...","token_type":"Bearer","expires_in":600,"scope":"tasks.read"}
```

### Level 2 — Intermediate

The nightly export job (card 0015) calls the same endpoint with `grant_type=client_credentials` — no user, no code, no redirect URI at all, just the client's own credentials.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

public class TokenEndpointDemo {

    static HttpResponse<String> requestClientCredentialsToken(String clientId, String clientSecret, String scope)
            throws Exception {
        String credentials = Base64.getEncoder().encodeToString((clientId + ":" + clientSecret).getBytes());
        String body = "grant_type=client_credentials&scope=" + scope;

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/token"))
                .header("Authorization", "Basic " + credentials)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build();

        return HttpClient.newHttpClient().send(request, HttpResponse.BodyHandlers.ofString());
    }

    public static void main(String[] args) throws Exception {
        HttpResponse<String> response = requestClientCredentialsToken(
                "task-tracker-export-job", "job-secret", "tasks.export");
        System.out.println("Status: " + response.statusCode());
        System.out.println("Body: " + response.body());
    }
}
```

**How to run:** same environment as Level 1, against a live server with `task-tracker-export-job` registered for `client_credentials` (card 0015). Expected output:

```
Status: 200
Body: {"access_token":"eyJhbGciOi...","token_type":"Bearer","expires_in":3600,"scope":"tasks.export"}
```

What changed: notice there's no `refresh_token` in this response — `client_credentials` grants typically don't include one, since the client can simply request a fresh token by re-authenticating with its own credentials whenever needed; there's no user session to preserve across a token expiry.

### Level 3 — Advanced

Production adds a resilient client-side wrapper that correctly distinguishes retryable failures (network errors, `5xx`) from non-retryable OAuth2 errors (`400` with `invalid_grant`, `invalid_client`) — retrying a `400` blindly wastes time and can trip rate limiting, while retrying a transient `5xx` is exactly the right behavior.

```java
import java.time.Duration;
import java.util.function.Supplier;

public class TokenEndpointDemo {

    // A minimal stand-in for the fields of the real HTTP response that matter for retry logic.
    record TokenResponse(int statusCode, String body) {}

    static TokenResponse requestWithRetry(Supplier<TokenResponse> tokenRequest, int maxAttempts)
            throws InterruptedException {

        TokenResponse lastResponse = null;
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            lastResponse = tokenRequest.get();
            int status = lastResponse.statusCode();

            if (status == 200) {
                return lastResponse; // success
            }
            if (status >= 400 && status < 500) {
                // client error: invalid_grant, invalid_client, unauthorized_client, etc.
                // retrying with the SAME request will fail identically -- don't retry
                System.out.println("Non-retryable error (status " + status + "): " + lastResponse.body());
                return lastResponse;
            }
            // 5xx or network-level issue: worth a bounded retry with backoff
            System.out.println("Attempt " + attempt + " got status " + status + ", retrying...");
            Thread.sleep(Duration.ofMillis(200L * attempt).toMillis());
        }
        return lastResponse;
    }

    public static void main(String[] args) throws InterruptedException {
        int[] callCount = {0};
        Supplier<TokenResponse> flaky = () -> {
            callCount[0]++;
            // simulate: fails with 503 twice, then succeeds
            return callCount[0] < 3
                    ? new TokenResponse(503, "")
                    : new TokenResponse(200, "{\"access_token\":\"...\"}");
        };

        TokenResponse result = requestWithRetry(flaky, 5);
        System.out.println("Final status: " + result.statusCode() + " after " + callCount[0] + " attempt(s)");
    }
}
```

**How to run:** run via `java TokenEndpointDemo.java` (no network needed; the flaky supplier simulates responses locally so this runs standalone). Expected output:

```
Attempt 1 got status 503, retrying...
Attempt 2 got status 503, retrying...
Final status: 200 after 3 attempt(s)
```

What changed and why it's production-flavored: real client libraries calling the token endpoint over an unreliable network need exactly this distinction — a `5xx` from an overloaded or restarting authorization server is worth a bounded retry with backoff, but a `400 invalid_grant` (e.g. an already-used authorization code, card 0017) will never succeed on retry and should fail fast instead.

## 6. Walkthrough

Tracing an authorization code exchange through the token endpoint, in execution order:

1. `POST /oauth2/token` arrives with `Authorization: Basic ...` and form-encoded body containing `grant_type=authorization_code`.
2. `OAuth2TokenEndpointFilter` first authenticates the *client* itself, using the method declared on its `RegisteredClient` (card 0012) — here, checking the Basic auth credentials against the stored, hashed secret.
3. Based on `grant_type=authorization_code`, the filter dispatches to `OAuth2AuthorizationCodeAuthenticationProvider`.
4. That provider looks up the `OAuth2Authorization` by the code value (card 0017's `findByToken`), checks it's active and that the request's `redirect_uri` matches what was used at the authorization endpoint, and — if PKCE was required — verifies `code_verifier` against the stored `code_challenge` (card 0012's walkthrough).
5. All checks pass; the provider invokes the `OAuth2TokenGenerator` (card 0019) to produce an access token and, since `REFRESH_TOKEN` is among the client's grant types, a refresh token too.
6. The code is marked invalidated, the new tokens are attached to the same `OAuth2Authorization`, and the updated record is saved (card 0017's Level 3 pattern).
7. The filter builds the JSON response body and returns `200 OK` with `Content-Type: application/json`: `{"access_token": "eyJhbGciOi...", "refresh_token": "8xL3k9...", "token_type": "Bearer", "expires_in": 600, "scope": "tasks.read"}`.
8. If any check in steps 2–4 fails instead, the filter returns `400 Bad Request` with a JSON body naming the specific error: `{"error": "invalid_client"}` for a bad secret, `{"error": "invalid_grant"}` for an expired or already-used code or a PKCE mismatch, or `{"error": "unauthorized_client"}` if the client isn't registered for this grant type at all (card 0015).

```
POST /oauth2/token (grant_type=authorization_code)
   |
authenticate client (Basic auth vs stored hash) --fail--> 400 invalid_client
   |  pass
dispatch to authorization_code provider
   |
findByToken(code) + check active + check redirect_uri + check PKCE --fail--> 400 invalid_grant
   |  pass
generate access_token (+ refresh_token) --> invalidate code --> save authorization
   |
200 OK {access_token, refresh_token, token_type, expires_in, scope}
```

## 7. Gotchas & takeaways

> `invalid_client`, `invalid_grant`, and `unauthorized_client` mean three genuinely different things, and conflating them during debugging wastes time — `invalid_client` is an authentication problem (wrong secret or method), `invalid_grant` is a problem with the specific code/token presented (expired, already used, wrong redirect URI, failed PKCE), and `unauthorized_client` means this client was never registered for the grant type it's attempting at all.

- The token endpoint requires the *client* to authenticate on every single call, even for `refresh_token` and `client_credentials` grants — a common integration bug is sending the refresh token without the client's Basic auth header, expecting the refresh token alone to be sufficient.
- `client_credentials` responses typically omit `refresh_token` — this is expected, not a bug; the client simply calls the token endpoint again with its own credentials whenever it needs a fresh token.
- Retrying a `400`-level response without changing anything about the request will fail identically every time (Level 3) — only `5xx` or network-level failures are worth retrying.
- The token endpoint has no concept of a "logged in browser session" — every single call is a fresh, self-contained authenticated request; there's no cookie or session state carried over from the authorization endpoint.
- When building client libraries against this endpoint, always check the HTTP status code *and* parse the `error` field on non-200 responses — the body is spec-defined JSON, not free-form text, and contains exactly the information needed to distinguish retryable from non-retryable failures.
