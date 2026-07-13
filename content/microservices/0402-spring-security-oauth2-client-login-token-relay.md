---
card: microservices
gi: 402
slug: spring-security-oauth2-client-login-token-relay
title: "Spring Security OAuth2 Client (login & token relay)"
---

## 1. What it is

Spring Security's **OAuth2 Client** module (`spring-boot-starter-oauth2-client`) is the Spring implementation of the *client* side of OAuth2: a service that lets a human log in via an external identity provider (Google, Okta, an internal Spring Authorization Server) using the [authorization code grant](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md), then stores the resulting access token so it can be forwarded — "relayed" — on outbound calls to downstream APIs. This is distinct from the [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md) module covered previously: a resource server *validates* incoming tokens; an OAuth2 client *obtains* tokens by driving a login flow and then *uses* them when calling someone else.

## 2. Why & when

You reach for `spring-boot-starter-oauth2-client` specifically when a Spring Boot application sits at the front of a user-facing flow and needs to authenticate a human, not just validate a token that already arrived:

- **A browser-facing gateway or BFF (backend-for-frontend)** needs to redirect an unauthenticated user to an identity provider's login page, handle the callback, and establish a session — exactly the "login" half of this module.
- **After login, downstream calls still need proof of identity.** A gateway that authenticated the user via OAuth2 login usually still needs to call `order-service` or `payment-service` on the user's behalf, which means forwarding — relaying — an access token rather than making those services re-authenticate the user from scratch.
- **It centralizes provider-specific quirks** (authorization endpoints, token endpoints, JWK URIs, scope names) behind a single `ClientRegistration` abstraction, so switching identity providers is a configuration change, not a code rewrite.
- **It's the natural complement to [Spring Cloud Gateway + Spring Security at the edge](0405-spring-cloud-gateway-spring-security-at-the-edge.md)**, where the gateway is frequently the one component doing OAuth2 login on behalf of the whole system, then relaying tokens inward — see [token relay filter in gateway / WebClient](0406-token-relay-filter-in-gateway-webclient.md) for the mechanics of that forwarding step.

You need this the moment a Spring Boot service is the first hop a browser talks to and must establish who the user is, rather than simply trusting a token some other component already validated.

## 3. Core concept

Think of OAuth2 Client as a hotel concierge who doesn't have the keys to every room in the city, but knows exactly which building (identity provider) to walk a guest to, how to introduce them, and how to carry back a signed voucher (the access token) once the guest has proven who they are. The concierge doesn't issue the voucher — the identity provider does — but the concierge is responsible for driving the guest there, handling the paperwork, and then presenting that voucher on the guest's behalf at every other desk (downstream service) the guest needs to visit.

The essential pieces:

1. **`ClientRegistration`** — describes one OAuth2 provider: authorization URI, token URI, client ID/secret, and scopes. Usually configured declaratively in `application.yml`.

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          okta:
            client-id: order-ui
            client-secret: ${OKTA_CLIENT_SECRET}
            scope: openid, profile, orders:read
            authorization-grant-type: authorization_code
            redirect-uri: "{baseUrl}/login/oauth2/code/{registrationId}"
        provider:
          okta:
            issuer-uri: https://dev-1234.okta.com/oauth2/default
```

2. **`OAuth2LoginConfigurer`** — wired via `.oauth2Login(...)` in a `SecurityFilterChain`, this triggers the redirect-to-provider, handles the callback, and produces an authenticated `Authentication` whose principal is an `OidcUser` or `OAuth2User`.

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/", "/public/**").permitAll()
            .anyRequest().authenticated())
        .oauth2Login(Customizer.withDefaults())   // enables the login redirect + callback handling
        .build();
}
```

3. **`OAuth2AuthorizedClientService` / `OAuth2AuthorizedClientRepository`** — stores the access token (and refresh token, if issued) obtained during login, keyed by the user's principal and the `registrationId`, so it can be retrieved later for outbound calls.
4. **Token relay** — the act of retrieving that stored access token and attaching it as an `Authorization: Bearer <token>` header on a call to a downstream resource server, so the downstream service can validate it exactly as covered in [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md), and so the original scopes/identity survive the hop, consistent with [token relay / propagation](0389-token-relay-propagation-between-services.md).

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A browser is redirected to an identity provider for login, the client exchanges the authorization code for an access token, stores it in the authorized client repository, and later relays that token as a bearer header on a call to a downstream service" font-family="sans-serif">
  <rect x="10" y="20" width="110" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="65" y="45" fill="#e6edf3" font-size="10" text-anchor="middle">Browser</text>

  <rect x="170" y="20" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="240" y="38" fill="#e6edf3" font-size="9" text-anchor="middle">OAuth2 Client</text>
  <text x="240" y="52" fill="#8b949e" font-size="8" text-anchor="middle">(Spring Boot app)</text>

  <rect x="360" y="20" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="435" y="38" fill="#e6edf3" font-size="9" text-anchor="middle">Identity Provider</text>
  <text x="435" y="52" fill="#8b949e" font-size="8" text-anchor="middle">login + token endpoint</text>

  <line x1="120" y1="40" x2="170" y2="40" stroke="#8b949e" marker-end="url(#oc)"/>
  <line x1="310" y1="35" x2="360" y2="35" stroke="#6db33f" marker-end="url(#oc)"/>
  <text x="335" y="27" fill="#6db33f" font-size="8" text-anchor="middle">redirect + code</text>
  <line x1="360" y1="50" x2="310" y2="50" stroke="#79c0ff" marker-end="url(#oc)"/>
  <text x="335" y="66" fill="#79c0ff" font-size="8" text-anchor="middle">access token</text>

  <rect x="170" y="110" width="140" height="44" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="240" y="128" fill="#e6edf3" font-size="9" text-anchor="middle">Authorized Client</text>
  <text x="240" y="142" fill="#8b949e" font-size="8" text-anchor="middle">Repository (stores token)</text>
  <line x1="240" y1="60" x2="240" y2="110" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#oc)"/>

  <rect x="170" y="200" width="140" height="44" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="240" y="218" fill="#e6edf3" font-size="9" text-anchor="middle">Outbound call</text>
  <text x="240" y="232" fill="#8b949e" font-size="8" text-anchor="middle">Authorization: Bearer ...</text>
  <line x1="240" y1="154" x2="240" y2="200" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#oc)"/>

  <rect x="440" y="200" width="150" height="44" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="515" y="218" fill="#e6edf3" font-size="9" text-anchor="middle">Downstream</text>
  <text x="515" y="232" fill="#8b949e" font-size="8" text-anchor="middle">Resource Server (0401)</text>
  <line x1="310" y1="222" x2="440" y2="222" stroke="#6db33f" marker-end="url(#oc)"/>

  <defs>
    <marker id="oc" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Login obtains the token once and stores it; every subsequent outbound call retrieves and relays that same stored token rather than re-authenticating.

## 5. Runnable example

Scenario: a Spring Boot "order-ui" client that logs a user in via an identity provider and then relays the obtained token to `order-service`. We model the login exchange and token storage first, then relaying the token on one outbound call, then handling an expired access token by transparently using a stored refresh token before relaying.

### Level 1 — Basic

```java
// File: OAuth2LoginExchange.java -- simulates the authorization_code grant:
// the browser is redirected, comes back with a code, and the client exchanges
// that code for an access token at the provider's token endpoint. Mirrors
// what Spring Security's OAuth2LoginConfigurer does automatically on
// /login/oauth2/code/{registrationId}.
import java.util.*;

public class OAuth2LoginExchange {
    record TokenResponse(String accessToken, String refreshToken, int expiresInSeconds) {}

    // Stand-in for the identity provider's /oauth2/token endpoint.
    static TokenResponse exchangeCodeForToken(String authorizationCode, String clientId, String clientSecret) {
        if (!"valid-auth-code".equals(authorizationCode)) {
            throw new IllegalStateException("invalid_grant -- authorization code rejected");
        }
        System.out.println("[IdentityProvider] verified client '" + clientId + "' and code, issuing tokens");
        return new TokenResponse("access-token-abc", "refresh-token-xyz", 300);
    }

    public static void main(String[] args) {
        // The browser was redirected to the provider, logged in, and came back with this code.
        String code = "valid-auth-code";
        TokenResponse tokens = exchangeCodeForToken(code, "order-ui", "order-ui-secret");
        System.out.println("Login complete. Access token: " + tokens.accessToken()
                + ", expires in " + tokens.expiresInSeconds() + "s, refresh token: " + tokens.refreshToken());
    }
}
```

How to run: `java OAuth2LoginExchange.java`

`exchangeCodeForToken` stands in for the real HTTPS POST Spring Security's `OAuth2LoginAuthenticationFilter` makes to the provider's token endpoint once the browser returns from login with an authorization code in the query string. The client authenticates itself with its own `clientId`/`clientSecret` (proving it's really `order-ui` making the request, not an attacker who intercepted the code), and receives back an access token plus a refresh token — exactly the shape Spring Security stores in an `OAuth2AuthorizedClient`.

### Level 2 — Intermediate

```java
// File: TokenRelayToDownstream.java -- the SAME login flow, now storing the
// token in a simulated AuthorizedClientRepository and RELAYING it on an
// outbound call to a downstream service, mirroring how a gateway or BFF
// attaches Authorization: Bearer <token> when calling order-service.
import java.util.*;

public class TokenRelayToDownstream {
    record TokenResponse(String accessToken, String refreshToken, int expiresInSeconds) {}
    record AuthorizedClient(String principalName, String registrationId, TokenResponse tokens) {}

    static final Map<String, AuthorizedClient> AUTHORIZED_CLIENT_REPOSITORY = new HashMap<>();

    static TokenResponse exchangeCodeForToken(String authorizationCode) {
        if (!"valid-auth-code".equals(authorizationCode)) throw new IllegalStateException("invalid_grant");
        return new TokenResponse("access-token-abc", "refresh-token-xyz", 300);
    }

    static void login(String principal, String registrationId, String authorizationCode) {
        TokenResponse tokens = exchangeCodeForToken(authorizationCode);
        AUTHORIZED_CLIENT_REPOSITORY.put(principal, new AuthorizedClient(principal, registrationId, tokens));
        System.out.println("[Client] stored authorized client for '" + principal + "' (" + registrationId + ")");
    }

    // Simulates a downstream call carrying the relayed token.
    static String callDownstream(String principal, String path) {
        AuthorizedClient client = AUTHORIZED_CLIENT_REPOSITORY.get(principal);
        if (client == null) return "401 Unauthorized -- no authorized client for this principal";
        String header = "Authorization: Bearer " + client.tokens().accessToken();
        System.out.println("[order-ui] GET " + path + " with " + header);
        return "[order-service] 200 OK -- request accepted for principal relayed via token";
    }

    public static void main(String[] args) {
        login("alice", "okta", "valid-auth-code");
        System.out.println(callDownstream("alice", "/orders/42"));
        System.out.println(callDownstream("bob", "/orders/42")); // never logged in
    }
}
```

How to run: `java TokenRelayToDownstream.java`

`login` performs the same code-for-token exchange as Level 1, but now stores the result in `AUTHORIZED_CLIENT_REPOSITORY` keyed by principal — mirroring Spring Security's `OAuth2AuthorizedClientRepository`. `callDownstream` retrieves that stored client and attaches its access token as a bearer header, exactly what an `ExchangeFilterFunction` or `RequestInterceptor` does automatically when you inject `OAuth2AuthorizedClientManager` into a `WebClient` or `RestClient` — the calling code never handles the raw token string itself. Bob's call fails because no login ever happened for him, demonstrating that relay only works after the login step populated the repository.

### Level 3 — Advanced

```java
// File: TokenRelayWithRefresh.java -- adds token EXPIRY and transparent
// REFRESH: relaying an expired access token would just get 401'd by the
// downstream service, so the client checks expiry first and uses the stored
// refresh token to get a new access token before relaying -- mirroring
// Spring Security's OAuth2AuthorizedClientManager refresh-on-demand behavior.
import java.time.*;
import java.util.*;

public class TokenRelayWithRefresh {
    record TokenResponse(String accessToken, String refreshToken, Instant expiresAt) {}
    record AuthorizedClient(String principalName, TokenResponse tokens) {}

    static final Map<String, AuthorizedClient> AUTHORIZED_CLIENT_REPOSITORY = new HashMap<>();
    static int tokenEndpointCalls = 0;

    static TokenResponse exchangeCodeForToken(String code, Instant now) {
        if (!"valid-auth-code".equals(code)) throw new IllegalStateException("invalid_grant");
        tokenEndpointCalls++;
        return new TokenResponse("access-token-v1", "refresh-token-xyz", now.plusSeconds(300));
    }

    // A refresh call gets a NEW access token but the SAME (or provider-rotated) refresh token.
    static TokenResponse refresh(String refreshToken, Instant now) {
        if (!"refresh-token-xyz".equals(refreshToken)) throw new IllegalStateException("invalid_grant -- bad refresh token");
        tokenEndpointCalls++;
        System.out.println("[IdentityProvider] refresh token accepted, issuing NEW access token");
        return new TokenResponse("access-token-v2", refreshToken, now.plusSeconds(300));
    }

    static void login(String principal, String code, Instant now) {
        AUTHORIZED_CLIENT_REPOSITORY.put(principal, new AuthorizedClient(principal, exchangeCodeForToken(code, now)));
    }

    static String callDownstream(String principal, Instant now) {
        AuthorizedClient client = AUTHORIZED_CLIENT_REPOSITORY.get(principal);
        if (client == null) return "401 Unauthorized -- no authorized client";

        TokenResponse tokens = client.tokens();
        if (now.isAfter(tokens.expiresAt())) {
            System.out.println("[order-ui] access token expired at " + tokens.expiresAt() + ", refreshing before relay");
            tokens = refresh(tokens.refreshToken(), now);
            AUTHORIZED_CLIENT_REPOSITORY.put(principal, new AuthorizedClient(principal, tokens));
        }
        System.out.println("[order-ui] relaying Authorization: Bearer " + tokens.accessToken());
        return "[order-service] 200 OK";
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-07-13T12:00:00Z");
        login("alice", "valid-auth-code", t0);

        System.out.println(callDownstream("alice", t0.plusSeconds(60)));   // still fresh, no refresh
        System.out.println(callDownstream("alice", t0.plusSeconds(600)));  // expired, transparent refresh
        System.out.println("Total token-endpoint calls: " + tokenEndpointCalls + " (1 login + 1 refresh)");
    }
}
```

How to run: `java TokenRelayWithRefresh.java`

`callDownstream` now checks `tokens.expiresAt()` before relaying anything. The first call at `t0 + 60s` is well within the 300-second lifetime, so it relays `access-token-v1` directly with zero extra network cost. The second call at `t0 + 600s` finds the token expired, calls `refresh` to obtain `access-token-v2` using the stored refresh token (never touching the user or requiring them to log in again), stores the refreshed client back in the repository, and only then relays the new token. This mirrors exactly what `OAuth2AuthorizedClientManager.authorize(...)` does under the hood in real Spring Security: it transparently refreshes an expired access token using a stored refresh token before handing the token back to the caller, so downstream calls almost never see a stale token.

## 6. Walkthrough

Trace `TokenRelayWithRefresh.main` in order. **First**, `login("alice", "valid-auth-code", t0)` runs `exchangeCodeForToken`, which validates the code and returns a `TokenResponse` with `accessToken = "access-token-v1"` and `expiresAt = t0 + 300s`. This is stored in `AUTHORIZED_CLIENT_REPOSITORY` under `"alice"`. `tokenEndpointCalls` is now `1`.

**Next**, `callDownstream("alice", t0.plusSeconds(60))` runs. `client` is found. `now` (`t0+60s`) is compared against `tokens.expiresAt()` (`t0+300s`) — `now.isAfter(expiresAt)` is `false`, so the refresh branch is skipped entirely. The method logs and relays `access-token-v1` directly, and prints `200 OK`.

**Then**, `callDownstream("alice", t0.plusSeconds(600))` runs. This time `now` (`t0+600s`) *is* after `expiresAt` (`t0+300s`), so the expiry branch fires: it prints the expiry notice, then calls `refresh("refresh-token-xyz", t0+600s)`. Inside `refresh`, the refresh token matches, `tokenEndpointCalls` becomes `2`, and a new `TokenResponse` with `accessToken = "access-token-v2"` and a new `expiresAt` of `t0+900s` is returned. `callDownstream` overwrites the repository entry with this fresh client, then relays `access-token-v2`.

**Finally**, `main` prints `tokenEndpointCalls`, which is `2` — one for the original login exchange, one for the mid-flight refresh — confirming the refresh happened exactly once, only when actually needed.

```
[order-ui] relaying Authorization: Bearer access-token-v1
[order-service] 200 OK
[order-ui] access token expired at 2026-07-13T12:05:00Z, refreshing before relay
[IdentityProvider] refresh token accepted, issuing NEW access token
[order-ui] relaying Authorization: Bearer access-token-v2
[order-service] 200 OK
Total token-endpoint calls: 2 (1 login + 1 refresh)
```

Sample HTTP shapes for the real exchange:

```
GET /oauth2/authorization/okta HTTP/1.1
-> 302 Found, Location: https://idp.example.com/authorize?client_id=order-ui&response_type=code&...

GET /login/oauth2/code/okta?code=valid-auth-code&state=... HTTP/1.1

POST /oauth2/token HTTP/1.1
grant_type=authorization_code&code=valid-auth-code&client_id=order-ui&client_secret=...

HTTP/1.1 200 OK
{"access_token": "access-token-v1", "refresh_token": "refresh-token-xyz", "expires_in": 300}
```

## 7. Gotchas & takeaways

> A common mistake is relaying the *ID token* instead of the *access token* to downstream services. The ID token (an OIDC-specific JWT proving the user logged in) is meant for the client application itself, often has a different audience, and many resource servers will correctly reject it. Always relay the `access_token`, never the `id_token`, when calling downstream APIs.

- OAuth2 Client and OAuth2 Resource Server are complementary, not competing: one obtains tokens via login, the other validates tokens on the way in — a gateway commonly runs both, using the client side for the human's session and the resource-server side to protect its own endpoints.
- Access tokens obtained via login are short-lived by design; always plan for transparent refresh using the stored refresh token rather than forcing the user to re-authenticate on every expiry.
- Storing tokens server-side in an `OAuth2AuthorizedClientRepository` (rather than pushing raw tokens into the browser) keeps the access token out of client-side JavaScript, reducing the blast radius of an XSS vulnerability.
- Relaying the wrong token, or relaying it to a service that never expected to receive user-scoped credentials, can silently widen privilege — always confirm the downstream service actually validates the audience and scope of what it receives, per [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md).
- This login-and-relay pattern is exactly what [token relay filter in gateway / WebClient](0406-token-relay-filter-in-gateway-webclient.md) automates at the infrastructure level, and what [token relay / propagation](0389-token-relay-propagation-between-services.md) covers conceptually — this topic is where it becomes concrete Spring configuration.
