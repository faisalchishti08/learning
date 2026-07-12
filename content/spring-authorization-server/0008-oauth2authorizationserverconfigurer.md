---
card: spring-authorization-server
gi: 8
slug: oauth2authorizationserverconfigurer
title: "OAuth2AuthorizationServerConfigurer"
---

## 1. What it is

`OAuth2AuthorizationServerConfigurer` is the single configurer class behind everything cards 0006 and 0007 introduced — a Spring Security `SecurityConfigurer` (the same extension pattern every DSL method like `.formLogin(...)` or `.oauth2Login(...)` uses) that exposes a family of per-endpoint sub-configurers, each individually customizable: `.authorizationEndpoint(...)`, `.tokenEndpoint(...)`, `.tokenIntrospectionEndpoint(...)`, `.tokenRevocationEndpoint(...)`, `.oidc(...)`, and `.clientAuthentication(...)`. Understanding it as one configurer exposing many focused sub-configurers — rather than one monolithic settings object — is what makes its customization surface tractable.

```java
http.with(OAuth2AuthorizationServerConfigurer.authorizationServer(), authorizationServer -> authorizationServer
        .authorizationEndpoint(authorization -> authorization
                .consentPage("/oauth2/custom-consent"))  // customize JUST the authorization endpoint
        .tokenEndpoint(token -> token
                .accessTokenResponseHandler(customTokenResponseHandler()))  // customize JUST token issuance
        .oidc(oidc -> oidc
                .userInfoEndpoint(userInfo -> userInfo
                        .userInfoMapper(customUserInfoMapper())))  // customize JUST the /userinfo response
);
```

## 2. Why & when

A monolithic "authorization server settings" object would force every customization through one giant, unfocused configuration surface; `OAuth2AuthorizationServerConfigurer`'s per-endpoint sub-configurer design instead lets an application customize exactly the one endpoint it needs to change — a custom consent page, custom token response fields, a custom `/userinfo` claim mapping — without needing to understand or touch configuration for every other endpoint the server also exposes. This mirrors exactly the pattern `HttpSecurity` itself uses (`.formLogin(...)`, `.csrf(...)`, `.oauth2Login(...)` are all independent, composable sub-configurers on the same parent DSL), so recognizing the pattern here means applying already-familiar knowledge.

Reach for a specific sub-configurer when:

- `.authorizationEndpoint(...)` — customizing the consent page, or how authorization requests are validated/converted, beyond the framework's defaults.
- `.tokenEndpoint(...)` — customizing the token response itself (adding custom fields beyond the standard OAuth2 response shape) or how token requests are authenticated.
- `.oidc(...)` — enabling and customizing OpenID Connect-specific behavior: the `/userinfo` endpoint's claim mapping, ID token customization, RP-Initiated Logout (card 0097's issuing side).
- `.tokenIntrospectionEndpoint(...)`/`.tokenRevocationEndpoint(...)` — customizing how introspection (card 0102's issuing side) or revocation requests are processed.
- `.clientAuthentication(...)` — customizing how a client itself authenticates when calling the token endpoint (client secret, private key JWT, mutual TLS).

## 3. Core concept

```
OAuth2AuthorizationServerConfigurer (the PARENT configurer, card 0006/0007's entry point)
    .authorizationEndpoint(consumer)          -- customize /oauth2/authorize
    .deviceAuthorizationEndpoint(consumer)     -- customize /oauth2/device_authorization
    .deviceVerificationEndpoint(consumer)      -- customize the device flow's user-facing verification page
    .tokenEndpoint(consumer)                   -- customize /oauth2/token
    .tokenIntrospectionEndpoint(consumer)      -- customize /oauth2/introspect
    .tokenRevocationEndpoint(consumer)         -- customize /oauth2/revoke
    .clientAuthentication(consumer)            -- customize how CLIENTS authenticate to the token endpoint
    .authorizationServerMetadataEndpoint(...)  -- customize /.well-known/oauth-authorization-server
    .oidc(consumer)                            -- ENABLE + customize OpenID Connect: /userinfo, ID tokens, RP-init logout

EACH sub-configurer accepts a Consumer<XxxConfigurer>, following the EXACT SAME
lambda-based customization pattern every OTHER Spring Security DSL method uses
(.formLogin(form -> form.loginPage(...)), .csrf(csrf -> csrf.disable()), etc.)

DEFAULT behavior (Customizer.withDefaults() at the TOP level) applies sensible
defaults to EVERY sub-configurer at once -- customizing ONE sub-configurer doesn't
require touching or even knowing about the others.
```

Each sub-configurer is independently optional — an application customizes only the specific endpoints it needs to change, leaving every other endpoint at its spec-conformant default.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing OAuth2AuthorizationServerConfigurer as a parent with several independent sub configurers each targeting one specific endpoint authorizationEndpoint tokenEndpoint oidc tokenIntrospectionEndpoint each customizable without touching the others">
  <rect x="240" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="330" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizationServerConfigurer</text>

  <line x1="330" y1="60" x2="150" y2="100" stroke="#79c0ff" stroke-width="1.4" marker-end="url(#oasc8)"/>
  <line x1="330" y1="60" x2="330" y2="100" stroke="#f0883e" stroke-width="1.4" marker-end="url(#oasc8b)"/>
  <line x1="330" y1="60" x2="510" y2="100" stroke="#8b949e" stroke-width="1.4" marker-end="url(#oasc8c)"/>

  <rect x="60" y="102" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="150" y="127" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">.authorizationEndpoint(...)</text>

  <rect x="240" y="102" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="330" y="127" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">.tokenEndpoint(...)</text>

  <rect x="420" y="102" width="180" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="510" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.oidc(...)</text>

  <rect x="150" y="160" width="180" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.3"/>
  <text x="240" y="185" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">.tokenIntrospectionEndpoint(...)</text>

  <line x1="330" y1="60" x2="240" y2="160" stroke="#3fb950" stroke-width="1.4" marker-end="url(#oasc8d)" stroke-dasharray="3,3"/>

  <defs>
    <marker id="oasc8" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="oasc8b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="oasc8c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="oasc8d" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

One parent configurer, several independent sub-configurers — each targets exactly one endpoint's behavior.

## 5. Runnable example

The scenario: model the sub-configurer pattern directly — a parent configurer holding several independently-customizable endpoint behaviors, growing from a single customized sub-configurer into multiple ones applied together, then into demonstrating that customizing one endpoint's behavior leaves every other endpoint's defaults completely untouched.

### Level 1 — Basic

A single sub-configurer, customized independently.

```java
import java.util.*;
import java.util.function.*;

public class AuthServerConfigurerLevel1 {
    static class TokenEndpointConfigurer {
        Map<String, Object> extraResponseFields = new LinkedHashMap<>();
        TokenEndpointConfigurer addExtraField(String key, Object value) {
            extraResponseFields.put(key, value);
            return this;
        }
    }

    static class AuthorizationServerConfigurer {
        private final TokenEndpointConfigurer tokenEndpointConfigurer = new TokenEndpointConfigurer();

        AuthorizationServerConfigurer tokenEndpoint(Consumer<TokenEndpointConfigurer> customizer) {
            customizer.accept(tokenEndpointConfigurer);
            return this;
        }

        Map<String, Object> buildTokenResponse(String accessToken) {
            Map<String, Object> response = new LinkedHashMap<>();
            response.put("access_token", accessToken);
            response.put("token_type", "Bearer");
            response.putAll(tokenEndpointConfigurer.extraResponseFields);
            return response;
        }
    }

    public static void main(String[] args) {
        AuthorizationServerConfigurer configurer = new AuthorizationServerConfigurer()
                .tokenEndpoint(token -> token.addExtraField("issued_by", "my-company-auth-server"));

        Map<String, Object> response = configurer.buildTokenResponse("token-abc123");
        System.out.println("token response: " + response);
    }
}
```

**How to run:** save as `AuthServerConfigurerLevel1.java`, run `java AuthServerConfigurerLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
token response: {access_token=token-abc123, token_type=Bearer, issued_by=my-company-auth-server}
```

`.tokenEndpoint(customizer)` mirrors the exact lambda-based customization pattern `OAuth2AuthorizationServerConfigurer`'s real sub-configurers use — a custom field is added to the token response without touching anything about how any other endpoint behaves.

### Level 2 — Intermediate

Two independent sub-configurers, both customized, demonstrating they don't interfere with each other.

```java
import java.util.*;
import java.util.function.*;

public class AuthServerConfigurerLevel2 {
    static class TokenEndpointConfigurer {
        Map<String, Object> extraFields = new LinkedHashMap<>();
        TokenEndpointConfigurer addExtraField(String key, Object value) { extraFields.put(key, value); return this; }
    }

    static class OidcConfigurer {
        Function<String, Map<String, Object>> userInfoMapper = username -> Map.of("sub", username);
        OidcConfigurer userInfoMapper(Function<String, Map<String, Object>> mapper) { this.userInfoMapper = mapper; return this; }
    }

    static class AuthorizationServerConfigurer {
        private final TokenEndpointConfigurer tokenEndpointConfigurer = new TokenEndpointConfigurer();
        private final OidcConfigurer oidcConfigurer = new OidcConfigurer();

        AuthorizationServerConfigurer tokenEndpoint(Consumer<TokenEndpointConfigurer> customizer) {
            customizer.accept(tokenEndpointConfigurer); return this;
        }
        AuthorizationServerConfigurer oidc(Consumer<OidcConfigurer> customizer) {
            customizer.accept(oidcConfigurer); return this;
        }

        Map<String, Object> buildTokenResponse(String accessToken) {
            Map<String, Object> response = new LinkedHashMap<>();
            response.put("access_token", accessToken);
            response.putAll(tokenEndpointConfigurer.extraFields);
            return response;
        }
        Map<String, Object> buildUserInfoResponse(String username) {
            return oidcConfigurer.userInfoMapper.apply(username);
        }
    }

    public static void main(String[] args) {
        AuthorizationServerConfigurer configurer = new AuthorizationServerConfigurer()
                .tokenEndpoint(token -> token.addExtraField("issued_by", "my-company"))
                .oidc(oidc -> oidc.userInfoMapper(username -> Map.of(
                        "sub", username, "email", username + "@example.com", "email_verified", true)));

        System.out.println("token response: " + configurer.buildTokenResponse("token-abc"));
        System.out.println("userinfo response: " + configurer.buildUserInfoResponse("alice"));
    }
}
```

**How to run:** save as `AuthServerConfigurerLevel2.java`, run `java AuthServerConfigurerLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
token response: {access_token=token-abc, issued_by=my-company}
userinfo response: {sub=alice, email=alice@example.com, email_verified=true}
```

What changed: both `.tokenEndpoint(...)` and `.oidc(...)` are customized independently within the same overall configuration — `buildTokenResponse` reflects only the token endpoint's customization, and `buildUserInfoResponse` reflects only the OIDC customization, confirming that each sub-configurer's changes are genuinely scoped to its own endpoint, with zero cross-contamination.

### Level 3 — Advanced

Demonstrate that customizing one sub-configurer leaves every *un*customized endpoint at its framework default — verifying the independence property more rigorously by comparing a fully-default configuration against one with a single targeted customization.

```java
import java.util.*;
import java.util.function.*;

public class AuthServerConfigurerLevel3 {
    static class TokenEndpointConfigurer {
        Map<String, Object> extraFields = new LinkedHashMap<>();
        TokenEndpointConfigurer addExtraField(String key, Object value) { extraFields.put(key, value); return this; }
    }
    static class IntrospectionEndpointConfigurer {
        boolean includeTokenType = true; // the DEFAULT
        IntrospectionEndpointConfigurer suppressTokenType() { this.includeTokenType = false; return this; }
    }
    static class OidcConfigurer {
        Function<String, Map<String, Object>> userInfoMapper = username -> Map.of("sub", username); // the DEFAULT
        OidcConfigurer userInfoMapper(Function<String, Map<String, Object>> mapper) { this.userInfoMapper = mapper; return this; }
    }

    static class AuthorizationServerConfigurer {
        private final TokenEndpointConfigurer tokenEndpointConfigurer = new TokenEndpointConfigurer();
        private final IntrospectionEndpointConfigurer introspectionConfigurer = new IntrospectionEndpointConfigurer();
        private final OidcConfigurer oidcConfigurer = new OidcConfigurer();

        AuthorizationServerConfigurer tokenEndpoint(Consumer<TokenEndpointConfigurer> c) { c.accept(tokenEndpointConfigurer); return this; }
        AuthorizationServerConfigurer tokenIntrospectionEndpoint(Consumer<IntrospectionEndpointConfigurer> c) { c.accept(introspectionConfigurer); return this; }
        AuthorizationServerConfigurer oidc(Consumer<OidcConfigurer> c) { c.accept(oidcConfigurer); return this; }

        Map<String, Object> buildTokenResponse(String token) {
            Map<String, Object> r = new LinkedHashMap<>(); r.put("access_token", token); r.putAll(tokenEndpointConfigurer.extraFields); return r;
        }
        Map<String, Object> buildIntrospectionResponse(boolean active) {
            Map<String, Object> r = new LinkedHashMap<>(); r.put("active", active);
            if (introspectionConfigurer.includeTokenType) r.put("token_type", "Bearer");
            return r;
        }
        Map<String, Object> buildUserInfoResponse(String username) { return oidcConfigurer.userInfoMapper.apply(username); }
    }

    public static void main(String[] args) {
        // configuration A: EVERYTHING at defaults, no customization at all
        AuthorizationServerConfigurer defaultsOnly = new AuthorizationServerConfigurer();

        // configuration B: ONLY the token endpoint is customized -- everything ELSE should remain default
        AuthorizationServerConfigurer onlyTokenCustomized = new AuthorizationServerConfigurer()
                .tokenEndpoint(token -> token.addExtraField("issued_by", "my-company"));

        System.out.println("=== defaults-only configuration ===");
        System.out.println("introspection response: " + defaultsOnly.buildIntrospectionResponse(true));
        System.out.println("userinfo response: " + defaultsOnly.buildUserInfoResponse("bob"));

        System.out.println("=== only-token-customized configuration ===");
        System.out.println("token response (CUSTOMIZED): " + onlyTokenCustomized.buildTokenResponse("token-xyz"));
        System.out.println("introspection response (UNCHANGED, still default): " + onlyTokenCustomized.buildIntrospectionResponse(true));
        System.out.println("userinfo response (UNCHANGED, still default): " + onlyTokenCustomized.buildUserInfoResponse("bob"));
    }
}
```

**How to run:** save as `AuthServerConfigurerLevel3.java`, run `java AuthServerConfigurerLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
=== defaults-only configuration ===
introspection response: {active=true, token_type=Bearer}
userinfo response: {sub=bob}
=== only-token-customized configuration ===
token response (CUSTOMIZED): {access_token=token-xyz, issued_by=my-company}
introspection response (UNCHANGED, still default): {active=true, token_type=Bearer}
userinfo response (UNCHANGED, still default): {sub=bob}
```

What changed: `onlyTokenCustomized`'s introspection and userinfo responses are byte-for-byte identical to `defaultsOnly`'s — proving that customizing the token endpoint via `.tokenEndpoint(...)` had absolutely zero effect on the introspection or OIDC sub-configurers, since each maintains its own, entirely independent configuration state, exactly the isolation property that makes `OAuth2AuthorizationServerConfigurer`'s per-endpoint design tractable for real applications that only ever need to customize a small number of specific endpoints.

## 6. Walkthrough

Trace how a real application would incrementally customize just the OIDC UserInfo endpoint, leaving everything else at its default, tying it back to card 0006's minimal starting configuration.

**Step 1 — the application starts from card 0006's minimal, all-defaults configuration:**
```java
http.with(OAuth2AuthorizationServerConfigurer.authorizationServer(), Customizer.withDefaults());
```
Corresponding to Level 3's `defaultsOnly` — every endpoint (token, introspection, UserInfo) behaves according to the framework's spec-conformant defaults.

**Step 2 — a requirement emerges: the `/userinfo` endpoint needs to include a custom `department` claim** that this application's user records carry, but the default UserInfo mapping has no concept of.

**Step 3 — only the `.oidc(...)` sub-configurer is touched:**
```java
http.with(OAuth2AuthorizationServerConfigurer.authorizationServer(), authorizationServer -> authorizationServer
        .oidc(oidc -> oidc.userInfoEndpoint(userInfo -> userInfo
                .userInfoMapper(context -> {
                    // build claims INCLUDING the custom "department" field
                }))));
```
Corresponding to `.oidc(oidc -> oidc.userInfoMapper(...))` in Level 2/3's model — only the OIDC sub-configurer's state changes.

**Step 4 — every other endpoint remains entirely unaffected.** The token endpoint still issues standard responses, introspection still behaves exactly as before, the authorization endpoint's consent flow is untouched — corresponding to Level 3's demonstration that `onlyTokenCustomized`'s introspection and userinfo responses matched `defaultsOnly`'s exactly, just with the roles reversed (here, only UserInfo changes, everything else stays default).

**Step 5 — the application deploys with exactly one, precisely-scoped customization**, rather than needing to reconstruct or re-verify the entire authorization server's configuration surface for a change that conceptually only concerns one endpoint.

```
default configuration: EVERY endpoint at framework defaults
        |
        v (touch ONLY .oidc(...))
customized configuration: UserInfo endpoint includes "department" claim
                            EVERY OTHER endpoint: STILL at framework defaults, UNCHANGED
```

## 7. Gotchas & takeaways

> **Gotcha:** because each sub-configurer maintains independent state, forgetting to call `.oidc(Customizer.withDefaults())` (or any customized variant) at all means OpenID Connect support is never enabled — plain OAuth2 endpoints work, but `/userinfo` and ID token issuance simply don't exist. This is easy to miss when starting from a bare `OAuth2AuthorizationServerConfigurer.authorizationServer()` call without the `.oidc(...)` clause, producing an OAuth2-only server when OIDC support was actually intended.

- `OAuth2AuthorizationServerConfigurer` exposes a family of independent, per-endpoint sub-configurers (`.authorizationEndpoint(...)`, `.tokenEndpoint(...)`, `.oidc(...)`, and others), each customizable via the same lambda-based pattern every other Spring Security DSL method uses.
- Customizing one sub-configurer has zero effect on any other — this independence is what makes incremental, targeted customization of a real authorization server tractable, rather than requiring a monolithic reconfiguration for every change.
- `.oidc(...)` must be explicitly included (even with just `Customizer.withDefaults()`) to enable OpenID Connect-specific behavior at all — its absence limits the server to plain OAuth2, which may not be the intended outcome.
- Reach for the specific sub-configurer matching whatever endpoint's behavior actually needs to change — there's no need to understand or touch the others.
- This per-endpoint design mirrors `HttpSecurity`'s own composable sub-configurer pattern (`.formLogin(...)`, `.csrf(...)`, `.oauth2Login(...)`), meaning familiarity with that broader pattern transfers directly to understanding this one.
