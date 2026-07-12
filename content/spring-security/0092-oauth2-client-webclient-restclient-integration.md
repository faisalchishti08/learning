---
card: spring-security
gi: 92
slug: oauth2-client-webclient-restclient-integration
title: "OAuth2 client (WebClient/RestClient integration)"
---

## 1. What it is

Once a user has an `OAuth2AuthorizedClient` (previous card), the whole point is usually to *use* that token to call a downstream API on the user's behalf. Spring Security wires this in automatically for the two standard HTTP clients: `ServletOAuth2AuthorizedClientExchangeFilterFunction` for the reactive `WebClient` (used even in ordinary servlet applications, not just WebFlux), and an equivalent `OAuth2ClientHttpRequestInterceptor` for the newer synchronous `RestClient`. Both do the same job at their respective integration point: given an outbound request tagged with a registration id (or the currently authenticated principal), look up — or transparently obtain, or transparently refresh — a valid `OAuth2AuthorizedClient`, and attach its access token as an `Authorization: Bearer <token>` header before the request is actually sent. Application code never manually reads a token off the `SecurityContext` and sets the header itself; it just tags the request with which registration to use, and the filter/interceptor does the rest.

```java
@Bean
public WebClient webClient(OAuth2AuthorizedClientManager manager) {
    ServletOAuth2AuthorizedClientExchangeFilterFunction oauth2 =
            new ServletOAuth2AuthorizedClientExchangeFilterFunction(manager);
    return WebClient.builder().apply(oauth2.oauth2Configuration()).build();
}

// per-call: tag which registration (and/or which principal) this request should authenticate as
Mono<String> body = webClient.get()
        .uri("https://api.github.com/user/repos")
        .attributes(oauth2AuthorizedClient(authorizedClient)) // or clientRegistrationId("github")
        .retrieve()
        .bodyToMono(String.class);
```

## 2. Why & when

Before this integration existed, every controller that needed to call a downstream API on a user's behalf had to manually resolve the `OAuth2AuthorizedClient`, check expiry, refresh if needed, and set the `Authorization` header by hand — repeated, easy-to-get-wrong boilerplate in every call site. Centralizing it in a filter function (or interceptor) means that concern is handled exactly once, consistently, regardless of how many places in the codebase make outbound calls. It also means the *refresh* logic (card 0093's `OAuth2AuthorizedClientProvider` chain) is invoked transparently at the moment a request is about to go out, rather than requiring every call site to remember to check token freshness first.

Reach for this integration when:

- Building any feature where the application calls a third-party API using the logged-in user's own OAuth2 token (fetching the user's GitHub repos, their Google Drive files, their Slack workspaces) — this is the standard mechanism, not a hand-rolled `HttpHeaders.setBearerAuth(...)`.
- Deciding between `WebClient` and `RestClient` integration: `RestClient` (Spring Framework 6.1+) is the synchronous, blocking-style client most new servlet applications should prefer for simplicity; `WebClient` remains the choice for reactive stacks or when non-blocking I/O genuinely matters. Both get equivalent OAuth2 support via their respective filter/interceptor.
- Debugging a downstream call that unexpectedly succeeds with an old, expired-looking token, or unexpectedly 401s — the filter function's job is precisely to prevent the former by refreshing before attaching, and the latter is almost always a sign the authorized client couldn't be resolved (wrong registration id, no authenticated principal in scope) or a refresh attempt failed.
- Calling a downstream API using **client-credentials** (an app-to-app token, not tied to any end user) rather than a user's own token — the same filter/interceptor mechanism applies; only the underlying grant type used to obtain the token differs (card 0093).

## 3. Core concept

```
Application code builds an outbound request, tagging it with a registration id (and/or principal):
    webClient.get().uri(...).attributes(clientRegistrationId("github"))...

ServletOAuth2AuthorizedClientExchangeFilterFunction / OAuth2ClientHttpRequestInterceptor intercepts BEFORE send:
    1. resolve WHICH OAuth2AuthorizedClient applies (registration id + current principal, from the request attributes)
    2. ask the OAuth2AuthorizedClientManager (card 0093): is this client's token STILL VALID?
         valid       -> use it as-is
         expired,
         refreshable -> silently REFRESH via the refresh_token provider, then use the NEW token
         missing     -> OBTAIN a new one (e.g. client_credentials grant needs no end user at all)
    3. set  Authorization: Bearer <access-token-value>  on the outbound request
    4. hand the now-authenticated request to the underlying HTTP client to actually send

Downstream API sees ONLY a normal request with a Bearer header -- it has no idea a refresh may have just happened
```

The filter/interceptor is a single choke point: every outbound call routed through it gets a fresh, valid token attached, without the calling code ever touching a token directly.

## 4. Diagram

<svg viewBox="0 0 640 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code builds a request tagged with a registration id the OAuth2 filter function asks the authorized client manager to resolve a valid token if the stored token is expired but refreshable the manager refreshes it first the filter attaches the resulting token as a bearer authorization header and the request is sent to the downstream api which returns a normal json response">
  <rect x="15" y="15" width="610" height="205" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="34" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Outbound call through WebClient / RestClient</text>

  <rect x="30" y="55" width="140" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="100" y="75" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">App code</text>
  <text x="100" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">tags registrationId</text>

  <rect x="205" y="55" width="180" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="295" y="75" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">OAuth2 filter /</text>
  <text x="295" y="89" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">interceptor</text>

  <line x1="170" y1="78" x2="200" y2="78" stroke="#79c0ff" stroke-width="2" marker-end="url(#a92)"/>

  <rect x="205" y="130" width="180" height="46" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="295" y="150" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">AuthorizedClientManager</text>
  <text x="295" y="164" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">refresh if expired</text>

  <line x1="295" y1="101" x2="295" y2="125" stroke="#8b949e" stroke-width="1.6" marker-end="url(#a92)"/>
  <line x1="295" y1="125" x2="295" y2="101" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="3,2"/>

  <rect x="430" y="55" width="170" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="515" y="75" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">Downstream API</text>
  <text x="515" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Authorization: Bearer ...</text>

  <line x1="385" y1="78" x2="425" y2="78" stroke="#3fb950" stroke-width="2" marker-end="url(#a92g)"/>

  <defs>
    <marker id="a92" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a92g" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The filter/interceptor sits between application code and the downstream call, consulting the authorized client manager before every request goes out.

## 5. Runnable example

The scenario: a fake outbound HTTP client that requires a bearer token, an `OAuth2AuthorizedClient` store (from the previous card), and an exchange-filter-style wrapper that resolves, refreshes if needed, and attaches the token before "calling" a downstream API — grown from a single successful call into one that transparently refreshes an expired token mid-flight.

### Level 1 — Basic

A fake downstream API that requires a bearer token, and a filter that attaches a known-good token.

```java
import java.util.*;

public class OAuth2ClientIntegrationLevel1 {
    record AuthorizedClient(String registrationId, String principal, String accessToken) {}

    // stands in for the real downstream HTTP endpoint -- rejects anything without a matching bearer token
    static class FakeDownstreamApi {
        static String call(String authorizationHeader) {
            if (authorizationHeader == null || !authorizationHeader.equals("Bearer tok-abc123")) {
                return "401 Unauthorized";
            }
            return "200 OK: [{\"name\":\"my-repo\"}]";
        }
    }

    // stands in for ServletOAuth2AuthorizedClientExchangeFilterFunction -- attaches the token before sending
    static String callWithBearerToken(AuthorizedClient client) {
        String header = "Bearer " + client.accessToken();
        return FakeDownstreamApi.call(header);
    }

    public static void main(String[] args) {
        AuthorizedClient alice = new AuthorizedClient("github", "alice", "tok-abc123");
        System.out.println("alice's call -> " + callWithBearerToken(alice));
    }
}
```

**How to run:** save as `OAuth2ClientIntegrationLevel1.java`, run `java OAuth2ClientIntegrationLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's call -> 200 OK: [{"name":"my-repo"}]
```

`callWithBearerToken` mirrors the filter function's core job: take an `AuthorizedClient`'s token and set it as the `Authorization` header before the call reaches the downstream API, which only accepts requests carrying the exact expected bearer value.

### Level 2 — Intermediate

Real applications don't have the token handed to them directly — they tag the request with a registration id and let the filter *resolve* the current authorized client from a store, exactly as `clientRegistrationId("github")` does.

```java
import java.util.*;

public class OAuth2ClientIntegrationLevel2 {
    record AuthorizedClient(String registrationId, String principal, String accessToken) {}

    static class AuthorizedClientStore {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient c) { store.put(key(c.registrationId(), c.principal()), c); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    static class FakeDownstreamApi {
        static String call(String authorizationHeader) {
            if (authorizationHeader == null || !authorizationHeader.equals("Bearer tok-abc123")) {
                return "401 Unauthorized";
            }
            return "200 OK: [{\"name\":\"my-repo\"}]";
        }
    }

    // mirrors the exchange filter function: RESOLVES the authorized client from the store, THEN attaches it
    static class OAuth2ExchangeFilter {
        private final AuthorizedClientStore store;
        OAuth2ExchangeFilter(AuthorizedClientStore store) { this.store = store; }

        String send(String registrationId, String principal) {
            AuthorizedClient client = store.load(registrationId, principal);
            if (client == null) {
                return "ERROR: no authorized client for " + registrationId + "/" + principal;
            }
            return FakeDownstreamApi.call("Bearer " + client.accessToken());
        }
    }

    public static void main(String[] args) {
        AuthorizedClientStore store = new AuthorizedClientStore();
        store.save(new AuthorizedClient("github", "alice", "tok-abc123"));

        OAuth2ExchangeFilter filter = new OAuth2ExchangeFilter(store);

        System.out.println("alice/github -> " + filter.send("github", "alice"));
        System.out.println("bob/github (never authorized) -> " + filter.send("github", "bob"));
    }
}
```

**How to run:** save as `OAuth2ClientIntegrationLevel2.java`, run `java OAuth2ClientIntegrationLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
alice/github -> 200 OK: [{"name":"my-repo"}]
bob/github (never authorized) -> ERROR: no authorized client for github/bob
```

What changed: application code no longer holds the token at all — it only supplies `(registrationId, principal)`, exactly like tagging a `WebClient` call with `clientRegistrationId("github")`. `OAuth2ExchangeFilter.send` does the resolution step the real filter function performs internally, and correctly reports an error rather than crashing when no authorized client exists for the given pair.

### Level 3 — Advanced

Handle the case that actually justifies this whole mechanism: the stored token is expired, but a refresh token exists, so the filter transparently refreshes it, saves the refreshed client back to the store, and *then* attaches the new token — all before the downstream call happens, with application code none the wiser.

```java
import java.time.Instant;
import java.util.*;

public class OAuth2ClientIntegrationLevel3 {
    record AuthorizedClient(String registrationId, String principal, String accessToken,
                             Instant expiresAt, String refreshToken) {
        boolean isExpired() { return Instant.now().isAfter(expiresAt); }
    }

    static class AuthorizedClientStore {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient c) { store.put(key(c.registrationId(), c.principal()), c); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    static class FakeDownstreamApi {
        static String call(String authorizationHeader, String expectedToken) {
            if (authorizationHeader == null || !authorizationHeader.equals("Bearer " + expectedToken)) {
                return "401 Unauthorized";
            }
            return "200 OK: [{\"name\":\"my-repo\"}]";
        }
    }

    // stands in for the refresh_token OAuth2AuthorizedClientProvider (full detail in the next card)
    static class FakeTokenRefresher {
        static AuthorizedClient refresh(AuthorizedClient stale) {
            String newAccessToken = "tok-refreshed-" + stale.refreshToken();
            return new AuthorizedClient(stale.registrationId(), stale.principal(), newAccessToken,
                    Instant.now().plusSeconds(3600), stale.refreshToken());
        }
    }

    // mirrors the exchange filter function's full responsibility: resolve, refresh-if-needed, attach, send
    static class OAuth2ExchangeFilter {
        private final AuthorizedClientStore store;
        OAuth2ExchangeFilter(AuthorizedClientStore store) { this.store = store; }

        String send(String registrationId, String principal, String expectedLiveToken) {
            AuthorizedClient client = store.load(registrationId, principal);
            if (client == null) {
                return "ERROR: no authorized client for " + registrationId + "/" + principal;
            }

            if (client.isExpired()) {
                if (client.refreshToken() == null) {
                    return "ERROR: token expired and no refresh token -- re-login required";
                }
                client = FakeTokenRefresher.refresh(client);
                store.save(client); // persist the refreshed client BEFORE using it, same as the real manager
            }

            return FakeDownstreamApi.call("Bearer " + client.accessToken(), expectedLiveToken);
        }
    }

    public static void main(String[] args) {
        AuthorizedClientStore store = new AuthorizedClientStore();

        // bob's stored token already expired 60 seconds ago, but a refresh token IS present
        store.save(new AuthorizedClient("github", "bob", "tok-bob-old",
                Instant.now().minusSeconds(60), "refresh-bob"));

        OAuth2ExchangeFilter filter = new OAuth2ExchangeFilter(store);

        // the downstream API will only accept the FRESHLY refreshed token -- proving a refresh actually happened
        String result = filter.send("github", "bob", "tok-refreshed-refresh-bob");
        System.out.println("bob's call (auto-refreshed) -> " + result);

        AuthorizedClient afterCall = store.load("github", "bob");
        System.out.println("bob's stored token after call -> " + afterCall.accessToken());
        System.out.println("bob's stored token still expired? -> " + afterCall.isExpired());
    }
}
```

**How to run:** save as `OAuth2ClientIntegrationLevel3.java`, run `java OAuth2ClientIntegrationLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
bob's call (auto-refreshed) -> 200 OK: [{"name":"my-repo"}]
bob's stored token after call -> tok-refreshed-refresh-bob
bob's stored token still expired? -> false
```

The key result: `filter.send` detects bob's expired token, calls `FakeTokenRefresher.refresh` to obtain a new one, **saves it back to the store** before proceeding, and only then attaches it to the outbound call — the downstream API, which only accepts the freshly minted token value, succeeds, proving the refresh genuinely happened rather than reusing the stale token. The store reflects the refreshed client afterward, so the *next* call for bob reuses the still-valid refreshed token instead of refreshing again.

## 6. Walkthrough

Trace `filter.send("github", "bob", "tok-refreshed-refresh-bob")` from Level 3, step by step, from the call site to the final downstream response.

**The concrete outbound HTTP request this ultimately produces (after the token is resolved and possibly refreshed):**
```
GET /user/repos HTTP/1.1
Host: api.github.com
Authorization: Bearer tok-refreshed-refresh-bob
Accept: application/vnd.github+json
```

1. `main` calls `filter.send("github", "bob", "tok-refreshed-refresh-bob")` — in a real application this corresponds to a controller invoking `webClient.get().uri(...).attributes(clientRegistrationId("github"))...` on behalf of the currently authenticated user, `bob`.
2. Inside `send`, `store.load("github", "bob")` retrieves bob's previously saved `AuthorizedClient` — the one constructed in `main` with `accessToken = "tok-bob-old"` and `expiresAt` sixty seconds in the past.
3. `client == null` is `false` (bob has a stored client), so execution proceeds past the "no authorized client" error case.
4. `client.isExpired()` is evaluated: `Instant.now().isAfter(expiresAt)` compares now against bob's `expiresAt`, which is in the past, so this returns `true` — the stored token is stale.
5. Since expired, `client.refreshToken() == null` is checked next — bob's client carries `"refresh-bob"`, a non-null value, so the "re-login required" error path is skipped.
6. `FakeTokenRefresher.refresh(client)` is called, standing in for the real `refresh_token` `OAuth2AuthorizedClientProvider` (fully detailed in card 0093) actually exchanging the refresh token with the provider's token endpoint. It constructs a **new** `AuthorizedClient` with `accessToken = "tok-refreshed-refresh-bob"` (built here from the refresh token value, purely so the example can verify the right value flows through) and a fresh `expiresAt` one hour out, keeping the same `refreshToken`.
7. `store.save(client)` persists this refreshed client, **overwriting** bob's stale entry in the map — this mirrors the real manager saving the refreshed client back through the `OAuth2AuthorizedClientService` (previous card) before the request proceeds, so the refreshed token is available for reuse on the *next* call without refreshing again.
8. `client` (the local variable) now references the refreshed object, so `FakeDownstreamApi.call("Bearer " + client.accessToken(), expectedLiveToken)` is invoked with `"Bearer tok-refreshed-refresh-bob"`.
9. Inside `FakeDownstreamApi.call`, the header is compared against `"Bearer " + expectedLiveToken`, which is also `"Bearer tok-refreshed-refresh-bob"` — they match, so the method returns `"200 OK: [{\"name\":\"my-repo\"}]"`, standing in for the real downstream API accepting the fresh bearer token.
10. `send` returns that string, which `main` prints as `bob's call (auto-refreshed) -> 200 OK: [{"name":"my-repo"}]`.
11. `main` then calls `store.load("github", "bob")` again — since step 7 overwrote the map entry, this returns the refreshed client, whose `accessToken()` is `"tok-refreshed-refresh-bob"` and whose `isExpired()` is now `false` (its `expiresAt` is an hour in the future), confirming the store's state genuinely changed as a side effect of making the call.

**The downstream response corresponding to step 9:**
```
HTTP/1.1 200 OK
Content-Type: application/json

[{"name":"my-repo","private":false}]
```

```
call arrives -> store.load(bob) -> expired? yes -> refreshToken present? yes
   -> refresh() -> NEW AuthorizedClient -> store.save() overwrites stale entry
   -> attach NEW token -> downstream call -> 200 OK
```

12. Contrast this with what would happen if bob's client had no refresh token at all: step 5's check would be `true`, and `send` would return the `"ERROR: token expired and no refresh token -- re-login required"` string immediately, at step 5 — the downstream API would never be called, and no `Authorization` header would ever be constructed for this request.

## 7. Gotchas & takeaways

> **Gotcha:** the exchange filter function/interceptor only refreshes and attaches a token for requests that are actually tagged with a registration id (or an explicit `OAuth2AuthorizedClient`) via request attributes — a `WebClient`/`RestClient` call built without `clientRegistrationId(...)` or `oauth2AuthorizedClient(...)` simply goes out with no `Authorization` header at all, silently, rather than failing loudly; a downstream `401` from an otherwise-correct-looking call is very often this missing attribute, not a broken token.

- `ServletOAuth2AuthorizedClientExchangeFilterFunction` (for `WebClient`) and the `RestClient` equivalent (`OAuth2ClientHttpRequestInterceptor`) do the same job at their respective client's integration point: resolve the current authorized client, refresh it if expired and refreshable, and attach it as `Authorization: Bearer <token>` before the request is sent.
- Application code tags outbound requests with a registration id (or a specific `OAuth2AuthorizedClient`) rather than ever touching a token value directly — this is what makes the refresh-before-send behavior automatic and consistent across every call site.
- `RestClient` is generally the simpler choice for new synchronous servlet applications; `WebClient` remains relevant for reactive stacks, but both get equivalent OAuth2 client support.
- A refreshed token is persisted back through the `OAuth2AuthorizedClientService` (previous card) before the request proceeds, so subsequent calls reuse the refreshed token rather than triggering a refresh on every single request.
- The same filter/interceptor mechanism works for client-credentials tokens (app-to-app, no end user) just as it does for a user's own delegated token — only the grant type resolved by the `OAuth2AuthorizedClientManager` differs, which the next card covers in depth.
