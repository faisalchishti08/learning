---
card: spring-authorization-server
gi: 33
slug: oidc-userinfo-endpoint
title: "OIDC UserInfo endpoint"
---

## 1. What it is

The OIDC UserInfo endpoint (`GET/POST /userinfo` by default) is a protected resource endpoint that returns claims about the currently authenticated user, given a valid access token. It's implemented internally as `OidcUserInfoEndpointFilter`, and is only registered on the filter chain when OIDC support is enabled via `.oidc(Customizer.withDefaults())` on `OAuth2AuthorizationServerConfigurer`.

## 2. Why & when

An ID token (issued at the token endpoint, card 0027) is a signed, self-contained snapshot of the user taken at authentication time — it doesn't change if the user's profile is updated afterward, and clients are told not to treat it as a general-purpose "who is this user" API. The UserInfo endpoint solves that: it's a live, callable endpoint a client hits *after* token issuance, using the `openid` access token it already holds, to get fresh, up-to-date claims about the user without needing a new authentication round-trip.

Reach for it when:

- Building a "login with X" client that needs to display the user's current name, email, or profile picture — call UserInfo rather than trusting a possibly-stale ID token for display data.
- Debugging "why does my client see different data than the ID token claimed" — UserInfo is a live read, so account changes made after login show up here first.
- Deciding what data belongs in the ID token (issued once) versus UserInfo (fetched fresh) — heavier or more sensitive claims are usually only exposed via UserInfo, gated by scope.

## 3. Core concept

Think of the ID token as a passport photo taken at the border crossing (authentication) — accurate at that moment, but not updated if you change your appearance later. The UserInfo endpoint is like calling the passport office directly: present your travel document (the access token) and they read you back your *current* file. The office only tells you what your visa (the granted scopes) entitles you to see — a `tasks.read`-only visa gets nothing from this office, since it never asked for `openid` or profile claims in the first place.

```
GET /userinfo
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9...
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client presents access token to UserInfo endpoint, which returns claims scoped to the token's granted scopes">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Client</text>

  <rect x="250" y="80" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="103" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OidcUserInfo</text>
  <text x="330" y="118" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">EndpointFilter</text>

  <rect x="480" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Claims JSON</text>

  <line x1="160" y1="95" x2="245" y2="95" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Bearer token</text>

  <line x1="410" y1="105" x2="475" y2="105" stroke="#3fb950" stroke-width="1.5"/>
  <text x="440" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scoped claims</text>

  <line x1="330" y1="130" x2="330" y2="170" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="330" y="185" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">no openid scope -&gt; 401</text>
</svg>

The endpoint validates the bearer token first, then filters returned claims down to what the token's granted scopes actually cover.

## 5. Runnable example

The scenario: a minimal OIDC-enabled authorization server, growing to customize which claims UserInfo returns, and finally to add scope-based claim filtering explicitly.

### Level 1 — Basic

```java
// OidcConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
public class OidcConfig {

    @Bean
    @Order(1)
    public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
        OAuth2AuthorizationServerConfigurer configurer =
                OAuth2AuthorizationServerConfigurer.authorizationServer();

        http.securityMatcher(configurer.getEndpointsMatcher())
                .with(configurer, authorizationServer -> authorizationServer.oidc(withDefaults()));

        return http.build();
    }
}
```

**How to run:** add this to a Spring Boot project with `spring-security-oauth2-authorization-server`, obtain an access token via the authorization code flow with `openid profile` scope, then run `curl -H "Authorization: Bearer <token>" http://localhost:8080/userinfo`. Expected output: a JSON object with `sub` and any profile claims the default `OidcUserInfoService` can derive from the authentication.

### Level 2 — Intermediate

Real applications back UserInfo claims with actual user data (e.g. a database), not just the authentication principal's username, so a custom `OidcUserInfoService`-equivalent mapper is needed.

```java
import org.springframework.security.oauth2.core.oidc.OidcUserInfo;
import org.springframework.security.oauth2.server.authorization.oidc.authentication.OidcUserInfoAuthenticationContext;
import org.springframework.security.oauth2.server.authorization.oidc.authentication.OidcUserInfoAuthenticationToken;

import java.util.Map;
import java.util.function.Function;

public class UserInfoMapper implements Function<OidcUserInfoAuthenticationContext, OidcUserInfo> {

    @Override
    public OidcUserInfo apply(OidcUserInfoAuthenticationContext context) {
        OidcUserInfoAuthenticationToken authentication = context.getAuthentication();
        String username = authentication.getPrincipal().getName();

        // In production, look up the real profile from a UserRepository by username.
        Map<String, Object> claims = Map.of(
                "sub", username,
                "name", "Ada Lovelace",
                "email", username + "@example.com",
                "email_verified", true);

        return new OidcUserInfo(claims);
    }
}
```

**How to run:** register via `.oidc(oidc -> oidc.userInfoEndpoint(userInfo -> userInfo.userInfoMapper(new UserInfoMapper())))` on the configurer from Level 1, then repeat the `curl` call. Expected output: the JSON response now includes `name` and `email` sourced from the mapper instead of only `sub`.

What changed: claims are now derived from real application data via a lookup instead of the bare authentication principal, which is what production systems actually need.

### Level 3 — Advanced

Production must respect the granted scopes — a client that only asked for `openid` (no `profile`, no `email`) must not receive name or email claims back, even if the mapper has that data available.

```java
import org.springframework.security.oauth2.core.oidc.OidcUserInfo;
import org.springframework.security.oauth2.core.oidc.OidcScopes;
import org.springframework.security.oauth2.server.authorization.oidc.authentication.OidcUserInfoAuthenticationContext;
import org.springframework.security.oauth2.server.authorization.oidc.authentication.OidcUserInfoAuthenticationToken;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;

public class ScopeAwareUserInfoMapper implements Function<OidcUserInfoAuthenticationContext, OidcUserInfo> {

    @Override
    public OidcUserInfo apply(OidcUserInfoAuthenticationContext context) {
        OidcUserInfoAuthenticationToken authentication = context.getAuthentication();
        Set<String> grantedScopes = authentication.getAccessToken().getScopes();
        String username = authentication.getPrincipal().getName();

        Map<String, Object> claims = new HashMap<>();
        claims.put("sub", username);

        if (grantedScopes.contains(OidcScopes.PROFILE)) {
            claims.put("name", "Ada Lovelace");
            claims.put("preferred_username", username);
        }
        if (grantedScopes.contains(OidcScopes.EMAIL)) {
            claims.put("email", username + "@example.com");
            claims.put("email_verified", true);
        }

        return new OidcUserInfo(claims);
    }
}
```

**How to run:** register `ScopeAwareUserInfoMapper` in place of the Level 2 mapper. Request a token with only `openid` scope and call `/userinfo`: expect `{"sub":"alice"}` with no other fields. Request again with `openid profile email`: expect the full claim set. Sample response:

```
HTTP/1.1 200 OK
Content-Type: application/json

{"sub":"alice","name":"Ada Lovelace","preferred_username":"alice","email":"alice@example.com","email_verified":true}
```

What changed and why it's production-flavored: claim exposure now tracks the OIDC scope contract precisely, which is required for spec compliance and prevents leaking profile data to clients that never asked for (and whose users never consented to) it.

## 6. Walkthrough

Tracing a UserInfo request end-to-end, in execution order:

1. The client already completed the authorization code flow and holds an access token whose scopes include `openid` (and, for this example, `profile` and `email`).
2. The client sends `GET /userinfo` with `Authorization: Bearer eyJhbGciOiJSUzI1NiJ9...`.
3. `OidcUserInfoEndpointFilter` intercepts the request. It first resolves the bearer token through Spring Security's standard OAuth2 resource server token validation — checking the signature, expiry, and that it's a genuinely issued access token (card 0021) — not a raw authorization step, but token *authentication* as a resource server would perform it.
4. If validation fails (expired, malformed, or missing token), the filter responds `401 Unauthorized` with a `WWW-Authenticate: Bearer error="invalid_token"` header — no claims are ever computed.
5. If validation succeeds, the filter builds an `OidcUserInfoAuthenticationToken` wrapping the resolved authentication and the access token's granted scopes, then passes it to the configured `userInfoMapper` (Level 3's `ScopeAwareUserInfoMapper`).
6. The mapper reads `grantedScopes` off the token, looks up the real user by `sub`, and returns only the claims the granted scopes permit.
7. The filter serializes the returned `OidcUserInfo` claims as a JSON object and responds `200 OK`.

```
GET /userinfo
Authorization: Bearer <access_token>
   |
validate bearer token --fail--> 401 Unauthorized (invalid_token)
   |  pass
resolve granted scopes from token
   |
userInfoMapper(context) --filters claims by scope-->
   |
200 OK  {"sub": "...", ...scope-permitted claims}
```

Concrete request and response:

```
GET /userinfo HTTP/1.1
Host: localhost:8080
Authorization: Bearer eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhbGljZSJ9...

HTTP/1.1 200 OK
Content-Type: application/json

{"sub":"alice","name":"Ada Lovelace","preferred_username":"alice","email":"alice@example.com","email_verified":true}
```

## 7. Gotchas & takeaways

> A UserInfo request with a token that lacks the `openid` scope entirely should be rejected — this endpoint is defined by the OIDC spec, and calling it with a plain OAuth2 access token that was never part of an OIDC flow is a misuse that a careful `userInfoMapper` (or an upstream check) should guard against, even though the library doesn't hard-block it by default.

- UserInfo claims are only as fresh as the mapper's data source — if the mapper just echoes stale principal data instead of doing a real lookup, the "live" promise of this endpoint is broken in practice.
- Always filter returned claims by the access token's granted scopes, not by what the client is capable of receiving — sending `email` to a client that never requested the `email` scope violates user consent, even if convenient.
- The default `OidcUserInfoService` derives claims only from the `Authentication` principal's name — anything beyond `sub` requires a custom mapper, as shown from Level 2 onward.
- UserInfo can be called with either `GET` or `POST`, and the access token can be presented as a bearer header or (less commonly) a form parameter — clients vary, so don't hardcode assumptions about which when writing test tooling.
- A `401` from this endpoint almost always means the access token itself is invalid, not that claims are missing — check token expiry and audience before assuming a mapper bug.
