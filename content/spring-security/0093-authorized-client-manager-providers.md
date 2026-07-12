---
card: spring-security
gi: 93
slug: authorized-client-manager-providers
title: "Authorized client manager & providers"
---

## 1. What it is

`OAuth2AuthorizedClientManager` is the central coordinator both the previous two cards' repository/service and exchange-filter integration ultimately delegate to: given a registration id and the current principal, it decides whether an existing `OAuth2AuthorizedClient`'s token is still valid, whether it needs to be **refreshed**, or whether one needs to be **obtained from scratch** — and it does the actual obtaining/refreshing itself by delegating to an `OAuth2AuthorizedClientProvider`. A provider is a pluggable strategy for exactly one grant type: there is one for `authorization_code` (completing the flow started by the login redirect, card 0090), one for `refresh_token` (silently exchanging a refresh token for a new access token), and one for `client_credentials` (obtaining an app-to-app token with no end user involved at all). In practice these are composed together via `OAuth2AuthorizedClientProviderBuilder`, which chains several strategies and tries them in order.

```java
@Bean
public OAuth2AuthorizedClientManager authorizedClientManager(
        ClientRegistrationRepository clientRegistrationRepository,
        OAuth2AuthorizedClientRepository authorizedClientRepository) {

    OAuth2AuthorizedClientProvider provider = OAuth2AuthorizedClientProviderBuilder.builder()
            .authorizationCode()   // completes the code-for-token exchange (card 0090)
            .refreshToken()        // silently refreshes an expired-but-refreshable token
            .clientCredentials()   // obtains an app-to-app token, no end user needed
            .build();

    DefaultOAuth2AuthorizedClientManager manager =
            new DefaultOAuth2AuthorizedClientManager(clientRegistrationRepository, authorizedClientRepository);
    manager.setAuthorizedClientProvider(provider);
    return manager;
}
```

## 2. Why & when

The manager/provider split exists because "which token-acquisition strategy applies right now" is a decision with several genuinely different possible answers depending on grant type, token state, and whether an end user is even involved — and each answer requires talking to a different endpoint with a different request shape. Rather than one monolithic method with a sprawling `if/else` over every case, the manager owns only the *decision* (valid? refresh? obtain?) and delegates the actual grant-specific work to whichever `OAuth2AuthorizedClientProvider` in its chain reports that it supports the current situation. This is the same "chain of pluggable strategies, first-match-wins" shape as `AuthenticationManager`'s list of `AuthenticationProvider`s, deliberately.

Reach for understanding this layer when:

- Wiring up a `client_credentials` registration for server-to-server calls that have no logged-in user at all — the `.clientCredentials()` provider is what makes `OAuth2AuthorizedClientManager.authorize(...)` work for a registration where there is no `principalName` tied to a human, and you'll typically use `AuthorizedClientServiceOAuth2AuthorizedClientManager` (service-based, not request-based) since there's no `HttpServletRequest` to anchor a client-credentials token to.
- Explaining why an expired token gets silently refreshed on the next call instead of forcing re-login — that's precisely the `.refreshToken()` provider being tried by the manager before falling through to "obtain a brand-new one."
- Customizing refresh behavior — for example, adding a clock-skew buffer so tokens are refreshed a little before they actually expire, or supplying a custom `OAuth2AuthorizedClientProvider` for a provider whose refresh semantics differ from the standard.
- Deciding between `DefaultOAuth2AuthorizedClientManager` (request-based, used by the servlet exchange filter integration from the previous card) and `AuthorizedClientServiceOAuth2AuthorizedClientManager` (service-based, no request required) — the latter is what background jobs and client-credentials-only setups need, since it never assumes an `HttpServletRequest` is available.

## 3. Core concept

```
OAuth2AuthorizedClientManager.authorize(request):     <-- the SINGLE entry point every integration calls
    1. load existing OAuth2AuthorizedClient (via the Repository/Service, cards 0091-0092)
    2. ask the PROVIDER CHAIN: "does any of you apply to this situation, and if so, what's the result?"
    3. return either: the EXISTING valid client, a REFRESHED client, or a NEWLY OBTAINED client

OAuth2AuthorizedClientProviderBuilder.builder()
    .authorizationCode()  -- APPLIES WHEN: no authorized client yet exists, but an authorization_code exchange
                              just completed (the login redirect flow, card 0090) -- finishes that handshake
    .refreshToken()       -- APPLIES WHEN: an authorized client exists, its access token IS expired,
                              AND a refresh token is present -- exchanges it for a fresh access token
    .clientCredentials()  -- APPLIES WHEN: registration's grant type is client_credentials -- no end user,
                              no refresh token even needed; simply re-requests a new app-to-app token
    .build()              -- returns ONE composite OAuth2AuthorizedClientProvider trying each in order

Each individual provider's contract: authorize(context) -> OAuth2AuthorizedClient, or null if it doesn't apply
    -- the manager tries providers in chain order, using the FIRST non-null result
```

The manager owns the decision of *which* strategy applies right now; each provider owns exactly one grant type's mechanics.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The authorized client manager receives an authorize request and consults a chain of three providers in order authorization code refresh token and client credentials each provider either declares it does not apply and passes to the next or handles the request and returns an authorized client the first provider that produces a non null result wins">
  <rect x="15" y="15" width="610" height="230" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="34" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizedClientManager.authorize(...)</text>

  <rect x="30" y="55" width="140" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="100" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">authorize request</text>

  <rect x="205" y="55" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="280" y="79" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">authorizationCode()</text>

  <rect x="205" y="103" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="280" y="127" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">refreshToken()</text>

  <rect x="205" y="151" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="280" y="175" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">clientCredentials()</text>

  <line x1="170" y1="78" x2="200" y2="75" stroke="#79c0ff" stroke-width="2" marker-end="url(#a93)"/>
  <line x1="280" y1="95" x2="280" y2="100" stroke="#8b949e" stroke-width="1.4" marker-end="url(#a93)"/>
  <line x1="280" y1="143" x2="280" y2="148" stroke="#8b949e" stroke-width="1.4" marker-end="url(#a93)"/>
  <text x="290" y="99" fill="#8b949e" font-size="7.5" font-family="sans-serif">doesn't apply</text>
  <text x="290" y="147" fill="#8b949e" font-size="7.5" font-family="sans-serif">doesn't apply</text>

  <rect x="440" y="103" width="160" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.6"/>
  <text x="520" y="127" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizedClient</text>

  <line x1="355" y1="123" x2="435" y2="123" stroke="#3fb950" stroke-width="2" marker-end="url(#a93g)"/>
  <text x="395" y="115" fill="#3fb950" font-size="7.5" text-anchor="middle" font-family="sans-serif">applies -&gt; result</text>

  <defs>
    <marker id="a93" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a93g" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The manager tries each provider in chain order; the first one that declares it applies produces the result, and the rest are never consulted.

## 5. Runnable example

The scenario: a fake `OAuth2AuthorizedClientProvider` chain modeling `authorization_code`, `refresh_token`, and `client_credentials`, composed by a fake `OAuth2AuthorizedClientProviderBuilder`, coordinated by a fake `OAuth2AuthorizedClientManager` — grown from a single provider into a full chain that correctly picks the right strategy for three different real-world situations.

### Level 1 — Basic

A single `refresh_token`-only provider and a manager that uses it when a stored token has expired.

```java
import java.time.Instant;
import java.util.*;

public class AuthorizedClientManagerLevel1 {
    record AuthorizedClient(String registrationId, String principal, String accessToken,
                             Instant expiresAt, String refreshToken) {
        boolean isExpired() { return Instant.now().isAfter(expiresAt); }
    }

    static class ClientStore {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient c) { store.put(key(c.registrationId(), c.principal()), c); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    // mirrors ONE OAuth2AuthorizedClientProvider strategy: refresh_token
    interface Provider {
        AuthorizedClient authorize(AuthorizedClient existing); // returns null if this provider doesn't apply
    }

    static class RefreshTokenProvider implements Provider {
        public AuthorizedClient authorize(AuthorizedClient existing) {
            if (existing == null || !existing.isExpired() || existing.refreshToken() == null) {
                return null; // doesn't apply: nothing to refresh, or not expired, or no refresh token
            }
            return new AuthorizedClient(existing.registrationId(), existing.principal(),
                    "tok-refreshed-" + existing.refreshToken(), Instant.now().plusSeconds(3600), existing.refreshToken());
        }
    }

    static class Manager {
        private final ClientStore store;
        private final Provider provider;
        Manager(ClientStore store, Provider provider) { this.store = store; this.provider = provider; }

        AuthorizedClient authorize(String registrationId, String principal) {
            AuthorizedClient existing = store.load(registrationId, principal);
            AuthorizedClient result = provider.authorize(existing);
            if (result != null) {
                store.save(result);
                return result;
            }
            return existing; // provider didn't apply -- return whatever was already stored (possibly null)
        }
    }

    public static void main(String[] args) {
        ClientStore store = new ClientStore();
        store.save(new AuthorizedClient("github", "bob", "tok-old", Instant.now().minusSeconds(60), "refresh-bob"));

        Manager manager = new Manager(store, new RefreshTokenProvider());
        AuthorizedClient result = manager.authorize("github", "bob");

        System.out.println("bob's token after authorize(): " + result.accessToken());
    }
}
```

**How to run:** save as `AuthorizedClientManagerLevel1.java`, run `java AuthorizedClientManagerLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
bob's token after authorize(): tok-refreshed-refresh-bob
```

`Manager.authorize` loads bob's stored client, hands it to the single `RefreshTokenProvider`, which detects it is expired and carries a refresh token, and returns a refreshed client that the manager then persists and hands back — the same shape as the real `DefaultOAuth2AuthorizedClientManager` delegating to a `refreshToken()` provider.

### Level 2 — Intermediate

Add a second provider, `client_credentials`, and chain them via a builder-style composite that tries each provider in order — mirroring `OAuth2AuthorizedClientProviderBuilder`.

```java
import java.time.Instant;
import java.util.*;

public class AuthorizedClientManagerLevel2 {
    record AuthorizedClient(String registrationId, String principal, String accessToken,
                             Instant expiresAt, String refreshToken, String grantType) {
        boolean isExpired() { return Instant.now().isAfter(expiresAt); }
    }

    static class ClientStore {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient c) { store.put(key(c.registrationId(), c.principal()), c); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    interface Provider {
        AuthorizedClient authorize(String registrationId, String principal, String grantType, AuthorizedClient existing);
    }

    static class RefreshTokenProvider implements Provider {
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing) {
            if (existing == null || !existing.isExpired() || existing.refreshToken() == null) return null;
            return new AuthorizedClient(rid, principal, "tok-refreshed-" + existing.refreshToken(),
                    Instant.now().plusSeconds(3600), existing.refreshToken(), existing.grantType());
        }
    }

    // APPLIES WHEN: the registration's grant type is client_credentials -- no end user, no refresh token needed
    static class ClientCredentialsProvider implements Provider {
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing) {
            if (!"client_credentials".equals(grantType)) return null; // doesn't apply to other grant types
            return new AuthorizedClient(rid, principal, "tok-app-" + rid, Instant.now().plusSeconds(3600), null, grantType);
        }
    }

    // mirrors OAuth2AuthorizedClientProviderBuilder -- tries each provider IN ORDER, first non-null result wins
    static class CompositeProvider implements Provider {
        private final List<Provider> chain;
        CompositeProvider(List<Provider> chain) { this.chain = chain; }
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing) {
            for (Provider p : chain) {
                AuthorizedClient result = p.authorize(rid, principal, grantType, existing);
                if (result != null) return result;
            }
            return null;
        }
    }

    static class Manager {
        private final ClientStore store;
        private final Provider provider;
        Manager(ClientStore store, Provider provider) { this.store = store; this.provider = provider; }

        AuthorizedClient authorize(String registrationId, String principal, String grantType) {
            AuthorizedClient existing = store.load(registrationId, principal);
            AuthorizedClient result = provider.authorize(registrationId, principal, grantType, existing);
            if (result != null) { store.save(result); return result; }
            return existing;
        }
    }

    public static void main(String[] args) {
        ClientStore store = new ClientStore();
        store.save(new AuthorizedClient("github", "bob", "tok-old", Instant.now().minusSeconds(60), "refresh-bob", "authorization_code"));

        CompositeProvider chain = new CompositeProvider(List.of(new RefreshTokenProvider(), new ClientCredentialsProvider()));
        Manager manager = new Manager(store, chain);

        AuthorizedClient bobResult = manager.authorize("github", "bob", "authorization_code");
        AuthorizedClient serviceResult = manager.authorize("internal-billing-service", "system", "client_credentials");

        System.out.println("bob (refreshed via chain) -> " + bobResult.accessToken());
        System.out.println("billing-service (client_credentials via chain) -> " + serviceResult.accessToken());
    }
}
```

**How to run:** save as `AuthorizedClientManagerLevel2.java`, run `java AuthorizedClientManagerLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
bob (refreshed via chain) -> tok-refreshed-refresh-bob
billing-service (client_credentials via chain) -> tok-app-internal-billing-service
```

What changed: `CompositeProvider` now tries `RefreshTokenProvider` first, falling through to `ClientCredentialsProvider` only if the first declines — bob's expired-with-refresh-token client is handled entirely by the first provider, while the `internal-billing-service` registration (no existing client, `client_credentials` grant type) is declined by the refresh provider (nothing to refresh) and correctly picked up by the second.

### Level 3 — Advanced

Add the third provider, `authorization_code`, and a case the chain must get right: a *brand-new* registration with no stored client and no refresh token at all, immediately following a login redirect — which only the `authorization_code` provider (last in the chain here, deliberately, to prove ordering doesn't quietly break a differently-shaped case) can satisfy, while also confirming a genuinely unsupported combination correctly falls through to `null`.

```java
import java.time.Instant;
import java.util.*;

public class AuthorizedClientManagerLevel3 {
    record AuthorizedClient(String registrationId, String principal, String accessToken,
                             Instant expiresAt, String refreshToken, String grantType) {
        boolean isExpired() { return Instant.now().isAfter(expiresAt); }
    }

    static class ClientStore {
        private final Map<String, AuthorizedClient> store = new HashMap<>();
        private String key(String rid, String p) { return rid + "::" + p; }
        void save(AuthorizedClient c) { store.put(key(c.registrationId(), c.principal()), c); }
        AuthorizedClient load(String rid, String p) { return store.get(key(rid, p)); }
    }

    interface Provider {
        AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing, String freshAuthCode);
    }

    static class RefreshTokenProvider implements Provider {
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing, String freshAuthCode) {
            if (existing == null || !existing.isExpired() || existing.refreshToken() == null) return null;
            return new AuthorizedClient(rid, principal, "tok-refreshed-" + existing.refreshToken(),
                    Instant.now().plusSeconds(3600), existing.refreshToken(), existing.grantType());
        }
    }

    static class ClientCredentialsProvider implements Provider {
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing, String freshAuthCode) {
            if (!"client_credentials".equals(grantType)) return null;
            return new AuthorizedClient(rid, principal, "tok-app-" + rid, Instant.now().plusSeconds(3600), null, grantType);
        }
    }

    // APPLIES WHEN: no existing client yet AND a fresh authorization code just arrived from the redirect (card 0090)
    static class AuthorizationCodeProvider implements Provider {
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing, String freshAuthCode) {
            if (existing != null || freshAuthCode == null || !"authorization_code".equals(grantType)) return null;
            // simulates exchanging the code at the provider's token endpoint for a brand-new access + refresh token
            return new AuthorizedClient(rid, principal, "tok-new-from-" + freshAuthCode,
                    Instant.now().plusSeconds(3600), "refresh-new-" + freshAuthCode, grantType);
        }
    }

    static class CompositeProvider implements Provider {
        private final List<Provider> chain;
        CompositeProvider(List<Provider> chain) { this.chain = chain; }
        public AuthorizedClient authorize(String rid, String principal, String grantType, AuthorizedClient existing, String freshAuthCode) {
            for (Provider p : chain) {
                AuthorizedClient result = p.authorize(rid, principal, grantType, existing, freshAuthCode);
                if (result != null) return result;
            }
            return null; // NO provider in the chain applies -- caller must handle this (e.g. redirect to login)
        }
    }

    static class Manager {
        private final ClientStore store;
        private final Provider provider;
        Manager(ClientStore store, Provider provider) { this.store = store; this.provider = provider; }

        AuthorizedClient authorize(String registrationId, String principal, String grantType, String freshAuthCode) {
            AuthorizedClient existing = store.load(registrationId, principal);
            AuthorizedClient result = provider.authorize(registrationId, principal, grantType, existing, freshAuthCode);
            if (result != null) { store.save(result); return result; }
            return existing;
        }
    }

    public static void main(String[] args) {
        ClientStore store = new ClientStore();
        // note: RefreshTokenProvider is FIRST in the chain, AuthorizationCodeProvider LAST -- order must not matter
        // for cases that don't overlap, which this run proves
        CompositeProvider chain = new CompositeProvider(List.of(
                new RefreshTokenProvider(), new ClientCredentialsProvider(), new AuthorizationCodeProvider()));
        Manager manager = new Manager(store, chain);

        // case 1: bob has NO existing client, but a login redirect just delivered a fresh authorization code
        AuthorizedClient freshLogin = manager.authorize("github", "bob", "authorization_code", "code-xyz789");
        System.out.println("bob (fresh authorization_code) -> " + freshLogin.accessToken());

        // case 2: bob calls again shortly after -- now HAS an authorized client, still valid, no code this time
        AuthorizedClient secondCall = manager.authorize("github", "bob", "authorization_code", null);
        System.out.println("bob (second call, reuses stored client) -> " + secondCall.accessToken());

        // case 3: an unsupported combination -- no existing client, no fresh code, not client_credentials either
        AuthorizedClient unsupported = manager.authorize("github", "carol", "authorization_code", null);
        System.out.println("carol (no client, no code -- unsupported) -> " + unsupported);
    }
}
```

**How to run:** save as `AuthorizedClientManagerLevel3.java`, run `java AuthorizedClientManagerLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
bob (fresh authorization_code) -> tok-new-from-code-xyz789
bob (second call, reuses stored client) -> tok-new-from-code-xyz789
carol (no client, no code -- unsupported) -> null
```

The key result: case 1 shows `AuthorizationCodeProvider`, though last in the chain, is still reached correctly because `RefreshTokenProvider` and `ClientCredentialsProvider` both decline (no existing client to refresh, wrong grant type) — chain order only matters when multiple providers *could* apply to the same situation, not when their applicability conditions are disjoint. Case 2 shows the manager returning the now-stored, still-valid client without invoking any provider's actual work again. Case 3 shows a genuinely unsupported combination correctly falling through the entire chain to `null`, exactly as the real `OAuth2AuthorizedClientProvider` chain would — at which point real application code must redirect the user to authenticate rather than treat `null` as a token.

## 6. Walkthrough

Trace `manager.authorize("github", "bob", "authorization_code", "code-xyz789")` from Level 3, from the call to the final resolved client.

**Context: this authorize call typically fires right after the browser follows the authorization server's redirect back to the application, e.g.:**
```
GET /login/oauth2/code/github?code=code-xyz789&state=af0ifjsldkj HTTP/1.1
Host: myapp.example.com
```

1. `main` calls `manager.authorize("github", "bob", "authorization_code", "code-xyz789")` — in the real filter (`Filter` processing the redirect, card 0090), this corresponds to the authorization code and state being validated, then the manager being asked to complete the exchange for the now-authenticated principal `bob`.
2. Inside `Manager.authorize`, `store.load("github", "bob")` is called first — the store is empty for this key (nothing was ever saved for bob under `"github"` in this run), so `existing` is `null`.
3. `provider.authorize("github", "bob", "authorization_code", null, "code-xyz789")` is called on the `CompositeProvider` chain, which iterates its three providers in the order they were listed: `RefreshTokenProvider`, `ClientCredentialsProvider`, `AuthorizationCodeProvider`.
4. `RefreshTokenProvider.authorize` is tried first: `existing == null` is `true`, so its `if` condition short-circuits to `true` immediately, and it returns `null` — this provider declines because there is nothing to refresh.
5. Back in `CompositeProvider`, since the result was `null`, the loop continues to `ClientCredentialsProvider.authorize`: `!"client_credentials".equals("authorization_code")` is `true` (the grant types don't match), so it also returns `null` and declines.
6. The loop reaches `AuthorizationCodeProvider.authorize`: its condition is `existing != null || freshAuthCode == null || !"authorization_code".equals(grantType)` — `existing` is `null` (first clause false), `freshAuthCode` is `"code-xyz789"`, not `null` (second clause false), and `grantType` is exactly `"authorization_code"` (third clause false) — since none of the three disqualifying conditions is `true`, the overall `if` is `false`, so this provider does **not** decline; it proceeds to construct and return a brand-new `AuthorizedClient`.
7. That new client has `accessToken = "tok-new-from-code-xyz789"` (built from the fresh code, standing in for a real exchange with the provider's token endpoint) and `refreshToken = "refresh-new-code-xyz789"`, with `expiresAt` one hour out — this is the object `CompositeProvider.authorize` returns, since it was the first non-null result in the chain.
8. Back in `Manager.authorize`, `result` is this non-null new client, so `store.save(result)` persists it under the `"github"::"bob"` key, and `authorize` returns it.
9. `main` prints `bob (fresh authorization_code) -> tok-new-from-code-xyz789`, confirming the chain correctly reached the third provider after the first two properly declined.

**The eventual outbound call this newly obtained token enables (made via the WebClient/RestClient integration from the previous card):**
```
GET /user/repos HTTP/1.1
Host: api.github.com
Authorization: Bearer tok-new-from-code-xyz789
Accept: application/vnd.github+json
```
```
HTTP/1.1 200 OK
Content-Type: application/json

[{"name":"my-repo","private":false}]
```

10. When `main` next calls `manager.authorize("github", "bob", "authorization_code", null)` (case 2), `store.load("github", "bob")` now finds the client saved in step 8 — `existing` is non-null this time. `RefreshTokenProvider` declines because `existing.isExpired()` is `false` (only seconds have passed since `expiresAt` was set an hour out). `ClientCredentialsProvider` declines on grant type mismatch as before. `AuthorizationCodeProvider` declines too, since `existing != null` is now `true`, immediately short-circuiting its `if` to `true`. All three decline, `CompositeProvider` returns `null`, and `Manager.authorize` falls through to `return existing` — handing back the same stored client without any provider doing new work.

```
case 1 (no client, fresh code):        RefreshToken:no -> ClientCredentials:no -> AuthCode:YES  -> new client saved
case 2 (client exists, valid, no code): RefreshToken:no -> ClientCredentials:no -> AuthCode:no   -> return existing as-is
case 3 (no client, no code, carol):     RefreshToken:no -> ClientCredentials:no -> AuthCode:no   -> null, caller must handle
```

## 7. Gotchas & takeaways

> **Gotcha:** `OAuth2AuthorizedClientProviderBuilder`'s chain order is only load-bearing when two providers' applicability conditions could genuinely overlap for the same situation — for the three standard grant-type providers their conditions are disjoint by design (no client versus expired client versus no-end-user grant type), so reordering `.authorizationCode().refreshToken().clientCredentials()` typically doesn't change outcomes; a **custom** provider added to the chain that overlaps an existing one's conditions, however, absolutely does depend on where it's placed, and a careless custom provider inserted before `.refreshToken()` can silently prevent refreshes from ever being attempted.

- `OAuth2AuthorizedClientManager` is the single coordinator every integration (the repository/service pair, the WebClient/RestClient exchange filter) ultimately calls; it owns the decision of whether an existing client is valid, needs refreshing, or needs to be obtained fresh.
- `OAuth2AuthorizedClientProvider` is a pluggable, single-grant-type strategy; `OAuth2AuthorizedClientProviderBuilder.builder().authorizationCode().refreshToken().clientCredentials().build()` composes the three standard ones into one chain, tried in order, first non-null result wins.
- `DefaultOAuth2AuthorizedClientManager` is request-based (used where an `HttpServletRequest` is naturally available, like the exchange filter integration); `AuthorizedClientServiceOAuth2AuthorizedClientManager` is service-based and has no request dependency, making it the right choice for background jobs and pure client-credentials setups.
- A provider that doesn't apply to the current situation returns `null` rather than throwing — this lets the chain fall through cleanly to the next candidate, and a fully-declined chain (nothing applies) also returns `null`, which calling code must handle explicitly (typically by redirecting an end user to authenticate).
- The manager persists a refreshed or newly obtained client back through the `OAuth2AuthorizedClientService` (card 0091) before returning it, so the very next `authorize` call for the same registration and principal reuses that result instead of triggering the provider chain's work all over again.
