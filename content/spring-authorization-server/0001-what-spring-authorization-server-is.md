---
card: spring-authorization-server
gi: 1
slug: what-spring-authorization-server-is
title: "What Spring Authorization Server is"
---

## 1. What it is

Every earlier discussion of OAuth2/OIDC in this course (client login flows, resource server token validation) assumed an authorization server *already existed somewhere* — Google, Okta, a corporate identity provider — issuing the tokens being consumed. Spring Authorization Server is the framework for building *that* server yourself: a Spring Security extension implementing the OAuth2.1 and OpenID Connect 1.0 specifications on the *issuing* side — handling authorization requests, granting tokens, exposing metadata and JWK Set endpoints, and managing registered clients — rather than the client or resource-server role every prior card covered.

```java
@Bean
public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
    OAuth2AuthorizationServerConfigurer authorizationServerConfigurer =
            OAuth2AuthorizationServerConfigurer.authorizationServer();

    http
        .securityMatcher(authorizationServerConfigurer.getEndpointsMatcher())
        .with(authorizationServerConfigurer, Customizer.withDefaults())
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated());

    return http.build();
}
```

## 2. Why & when

Cards 0088–0110 covered building applications that *delegate* authentication to an external identity provider, and cards 0099–0106 covered building resource servers that *trust* tokens issued elsewhere — both roles assume the authorization server itself is someone else's infrastructure. Not every organization can rely purely on a third-party identity provider, though: an organization building its own internal platform, offering an API other companies' applications should be able to integrate with via OAuth2, or needing full control over token issuance, custom claims, and consent screens, needs to actually *run* an authorization server — and Spring Authorization Server exists specifically to make building one a matter of configuring Spring Security beans, rather than implementing the OAuth2/OIDC specifications' considerable protocol detail from scratch.

Reach for Spring Authorization Server when:

- Building a platform where multiple client applications (web apps, mobile apps, other services) need to obtain tokens through a standard OAuth2/OIDC flow, issued by *your own* infrastructure rather than a third party.
- Offering "Login with [Your Product]" to third-party integrators — becoming an identity provider *for other applications*, the mirror image of every earlier card's "Login with Google"-style client integration.
- Needing full control over the issued token's claims, lifetime, and the specific grant types supported — a third-party identity provider's token shape and policies are largely fixed; running your own server means you decide.
- Migrating off the older, now-archived Spring Security OAuth project (card 0004's territory) — Spring Authorization Server is its official, actively maintained successor.

It is not the right tool when an application merely needs to authenticate users via an *existing* provider (that's `oauth2Login()`, card 0088) or merely needs to validate tokens issued elsewhere (that's `oauth2ResourceServer()`, cards 0099–0106) — those roles need no authorization server of the application's own at all.

## 3. Core concept

```
The THREE roles in any OAuth2/OIDC relationship, and which cards cover which:

    Resource Owner   -- the end user, who owns the data/account
    Client           -- the application requesting access ON THE USER'S BEHALF
                         (cards 0088-0098: oauth2Login(), ClientRegistration, etc.)
    Authorization Server -- issues tokens, after authenticating the user and getting consent
                         (THIS project: Spring Authorization Server)
    Resource Server  -- hosts the protected data, VALIDATES tokens the Authorization Server issued
                         (cards 0099-0106: oauth2ResourceServer(), JwtDecoder, etc.)

Spring Authorization Server builds THIS piece specifically:
    /oauth2/authorize        -- the authorization endpoint (card 0090's redirect target)
    /oauth2/token             -- the token endpoint (card 0090's code-for-token exchange)
    /oauth2/jwks              -- the JWK Set endpoint (card 0101's key source)
    /.well-known/openid-configuration -- OIDC discovery metadata (card 0110's metadata source)
    /oauth2/introspect        -- token introspection (card 0102's validation target)
    /oauth2/revoke            -- token revocation

One application COULD, in principle, play multiple roles at once (be its own
authorization server AND a resource server validating its own tokens) -- but the
roles remain conceptually distinct regardless of how many run in the same process.
```

Every endpoint this project exposes is precisely the *other side* of an interaction some earlier card in this course already covered from the client or resource-server perspective.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing the four OAuth2 roles resource owner client authorization server and resource server with Spring Authorization Server building the authorization server piece specifically issuing tokens that a resource server built with oauth2ResourceServer then validates">
  <rect x="20" y="30" width="140" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="90" y="50" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Resource Owner</text>
  <text x="90" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(the end user)</text>

  <rect x="180" y="30" width="140" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="250" y="50" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="250" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">oauth2Login() (cards 88-98)</text>

  <rect x="340" y="30" width="160" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="420" y="50" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">Authorization Server</text>
  <text x="420" y="66" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">THIS project</text>

  <rect x="520" y="30" width="120" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="580" y="50" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">Resource Server</text>
  <text x="580" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cards 99-106</text>

  <line x1="320" y1="55" x2="335" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#asov1)"/>
  <text x="330" y="45" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">redirect</text>

  <line x1="420" y1="80" x2="420" y2="110" stroke="#6db33f" stroke-width="1.6" marker-end="url(#asov1b)"/>
  <text x="420" y="100" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">issues token</text>

  <rect x="340" y="112" width="160" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="420" y="132" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">access_token, id_token</text>

  <line x1="500" y1="132" x2="600" y2="80" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#asov1c)"/>
  <text x="560" y="105" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">token VALIDATED here</text>

  <defs>
    <marker id="asov1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="asov1b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="asov1c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

Spring Authorization Server builds exactly one of the four OAuth2 roles — the piece every earlier client/resource-server card assumed existed elsewhere.

## 5. Runnable example

The scenario: since this card introduces a concept rather than a single API, the example models the four-role relationship directly — a minimal in-memory authorization server issuing a token, a client redirecting to it, and a resource server validating what it issued — growing from a bare token issuance into the full round trip, then into demonstrating why running your own authorization server means controlling exactly what claims end up in the token.

### Level 1 — Basic

A minimal authorization server issuing a token for a registered client.

```java
import java.util.*;

public class AuthServerLevel1 {
    record RegisteredClient(String clientId, String clientSecret) {}
    record AccessToken(String value, String subject, Set<String> scopes) {}

    static class MinimalAuthorizationServer {
        private final Map<String, RegisteredClient> clients = new HashMap<>();
        void registerClient(RegisteredClient client) { clients.put(client.clientId(), client); }

        AccessToken issueToken(String clientId, String clientSecret, String subject, Set<String> scopes) {
            RegisteredClient client = clients.get(clientId);
            if (client == null || !client.clientSecret().equals(clientSecret)) {
                throw new IllegalStateException("invalid_client");
            }
            return new AccessToken("token-" + UUID.randomUUID().toString().substring(0, 8), subject, scopes);
        }
    }

    public static void main(String[] args) {
        MinimalAuthorizationServer authServer = new MinimalAuthorizationServer();
        authServer.registerClient(new RegisteredClient("my-app", "my-app-secret"));

        AccessToken token = authServer.issueToken("my-app", "my-app-secret", "alice", Set.of("read:orders"));
        System.out.println("issued token for subject=" + token.subject() + " scopes=" + token.scopes());
    }
}
```

**How to run:** save as `AuthServerLevel1.java`, run `java AuthServerLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
issued token for subject=alice scopes=[read:orders]
```

`MinimalAuthorizationServer.issueToken` mirrors, at the simplest possible level, what Spring Authorization Server's `/oauth2/token` endpoint does: verify the requesting client's identity, then issue a token — this is the *issuing* side every earlier client/resource-server card treated as an external black box.

### Level 2 — Intermediate

Add the client-redirect half (the authorization endpoint), completing the basic three-role relationship: resource owner, client, authorization server.

```java
import java.util.*;

public class AuthServerLevel2 {
    record RegisteredClient(String clientId, String clientSecret, String redirectUri) {}
    record AuthorizationCode(String value, String clientId, String subject) {}
    record AccessToken(String value, String subject, Set<String> scopes) {}

    static class MinimalAuthorizationServer {
        private final Map<String, RegisteredClient> clients = new HashMap<>();
        private final Map<String, AuthorizationCode> issuedCodes = new HashMap<>();

        void registerClient(RegisteredClient client) { clients.put(client.clientId(), client); }

        // mirrors GET /oauth2/authorize -- the user has already authenticated AT the auth server
        String authorize(String clientId, String subject) {
            RegisteredClient client = clients.get(clientId);
            String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
            issuedCodes.put(code, new AuthorizationCode(code, clientId, subject));
            return client.redirectUri() + "?code=" + code;
        }

        // mirrors POST /oauth2/token, exchanging the code
        AccessToken exchangeCodeForToken(String code, String clientId, String clientSecret) {
            RegisteredClient client = clients.get(clientId);
            if (client == null || !client.clientSecret().equals(clientSecret)) throw new IllegalStateException("invalid_client");
            AuthorizationCode authCode = issuedCodes.remove(code);
            if (authCode == null || !authCode.clientId().equals(clientId)) throw new IllegalStateException("invalid_grant");
            return new AccessToken("token-" + UUID.randomUUID().toString().substring(0, 8), authCode.subject(), Set.of("read:orders"));
        }
    }

    public static void main(String[] args) {
        MinimalAuthorizationServer authServer = new MinimalAuthorizationServer();
        authServer.registerClient(new RegisteredClient("my-app", "my-app-secret", "https://app.example.com/callback"));

        String redirect = authServer.authorize("my-app", "alice");
        System.out.println("browser redirected to: " + redirect);

        String code = redirect.substring(redirect.indexOf("code=") + 5);
        AccessToken token = authServer.exchangeCodeForToken(code, "my-app", "my-app-secret");
        System.out.println("client received token for: " + token.subject());
    }
}
```

**How to run:** save as `AuthServerLevel2.java`, run `java AuthServerLevel2.java` (JDK 17+ runs single files directly).

Expected output (the code value varies, since it's randomly generated):
```
browser redirected to: https://app.example.com/callback?code=code-a1b2c3d4
client received token for: alice
```

What changed: `authorize` and `exchangeCodeForToken` together mirror the exact Authorization Code grant flow from card 0090 — but now from the *issuing* side rather than the client side that card modeled. This is precisely the mirror-image relationship: card 0090 modeled a client receiving a redirect and exchanging a code; this level models the server producing that redirect and honoring that exchange.

### Level 3 — Advanced

Complete the four-role picture: a resource server validating a token this authorization server issued, using custom claims the authorization server controls entirely (something a third-party identity provider would never let an application customize this freely).

```java
import java.util.*;

public class AuthServerLevel3 {
    record RegisteredClient(String clientId, String clientSecret, String redirectUri) {}
    record AuthorizationCode(String value, String clientId, String subject) {}
    record AccessToken(String value, String subject, Set<String> scopes, Map<String, Object> customClaims) {}

    static class MinimalAuthorizationServer {
        private final Map<String, RegisteredClient> clients = new HashMap<>();
        private final Map<String, AuthorizationCode> issuedCodes = new HashMap<>();
        private final Map<String, AccessToken> issuedTokens = new HashMap<>(); // for the resource server to check

        void registerClient(RegisteredClient client) { clients.put(client.clientId(), client); }

        String authorize(String clientId, String subject) {
            RegisteredClient client = clients.get(clientId);
            String code = "code-" + UUID.randomUUID().toString().substring(0, 8);
            issuedCodes.put(code, new AuthorizationCode(code, clientId, subject));
            return client.redirectUri() + "?code=" + code;
        }

        AccessToken exchangeCodeForToken(String code, String clientId, String clientSecret) {
            RegisteredClient client = clients.get(clientId);
            if (client == null || !client.clientSecret().equals(clientSecret)) throw new IllegalStateException("invalid_client");
            AuthorizationCode authCode = issuedCodes.remove(code);
            if (authCode == null) throw new IllegalStateException("invalid_grant");

            // THIS IS WHAT RUNNING YOUR OWN AUTHORIZATION SERVER BUYS YOU:
            // full control over exactly what claims the token carries
            Map<String, Object> customClaims = Map.of(
                    "internal_tenant_id", "tenant-42",
                    "internal_account_tier", "premium");

            AccessToken token = new AccessToken("token-" + UUID.randomUUID().toString().substring(0, 8),
                    authCode.subject(), Set.of("read:orders"), customClaims);
            issuedTokens.put(token.value(), token);
            return token;
        }

        // mirrors what a resource server's introspection/JWT validation would confirm
        AccessToken validateToken(String tokenValue) {
            AccessToken token = issuedTokens.get(tokenValue);
            if (token == null) throw new IllegalStateException("invalid_token");
            return token;
        }
    }

    public static void main(String[] args) {
        MinimalAuthorizationServer authServer = new MinimalAuthorizationServer();
        authServer.registerClient(new RegisteredClient("my-app", "my-app-secret", "https://app.example.com/callback"));

        String redirect = authServer.authorize("my-app", "alice");
        String code = redirect.substring(redirect.indexOf("code=") + 5);
        AccessToken token = authServer.exchangeCodeForToken(code, "my-app", "my-app-secret");

        // the "resource server" -- a completely SEPARATE service, only trusting this auth server's tokens
        AccessToken validated = authServer.validateToken(token.value());
        System.out.println("resource server confirms subject: " + validated.subject());
        System.out.println("custom claim tenant_id: " + validated.customClaims().get("internal_tenant_id"));
        System.out.println("custom claim account_tier: " + validated.customClaims().get("internal_account_tier"));
    }
}
```

**How to run:** save as `AuthServerLevel3.java`, run `java AuthServerLevel3.java` (JDK 17+ runs single files directly).

Expected output (token/code values vary):
```
resource server confirms subject: alice
custom claim tenant_id: tenant-42
custom claim account_tier: premium
```

What changed: the token now carries `internal_tenant_id` and `internal_account_tier` — claims entirely specific to this application's own domain, added at the moment of issuance because *this* server controls token construction completely. A third-party identity provider's tokens carry whatever that provider decided to include; running your own authorization server means the issued token's shape is entirely under your own control, exactly as card 0104's custom `JwtAuthenticationConverter` discussion presupposed such claims existing *somewhere* — here is where they'd actually originate.

## 6. Walkthrough

Trace alice's full journey across all four roles, tying this card's example to the specific cards where each half was already covered.

**Step 1 — alice, the resource owner, wants to use `my-app` (the client).** `my-app`'s code, exactly matching card 0088's `oauth2Login()` pattern, redirects her browser to this authorization server's `/oauth2/authorize` endpoint — corresponding to `authServer.authorize("my-app", "alice")`.

**Step 2 — the authorization server issues a code**, corresponding to the returned redirect URL carrying `code=code-a1b2c3d4` — this is the exact code card 0090's Authorization Code grant flow described receiving on the client side.

**Step 3 — `my-app`'s backend exchanges that code**, corresponding to `authServer.exchangeCodeForToken(code, "my-app", "my-app-secret")` — the server-to-server hop card 0090 emphasized never touches the browser, verified here by client credentials (`clientId`/`clientSecret`) rather than anything the browser carried.

**Step 4 — the authorization server constructs the token**, including custom claims (`internal_tenant_id`, `internal_account_tier`) this application specifically wanted — this is the moment card 0104's custom claim-to-authority mapping discussion presupposed such claims existing; here is where an application actually decides what goes into them.

**Step 5 — the token is handed to a resource server** (a conceptually separate service, potentially a different application entirely) which validates it — corresponding to `authServer.validateToken(token.value())`, standing in for the real validation card 0100 (JWT) or card 0102 (opaque token introspection) covers from the *validating* side.

**Step 6 — the resource server trusts the custom claims because it trusts this authorization server specifically** — `validated.customClaims().get("internal_tenant_id")` returns `"tenant-42"`, a claim that only exists because this particular authorization server chose to include it, unlike a claim from a third-party provider whose contents are outside any one application's control.

```
alice (resource owner)
   -> my-app (client, card 0088's oauth2Login() side)
        -> redirect to /oauth2/authorize -- THIS PROJECT
             -> code issued -> exchanged at /oauth2/token -- THIS PROJECT
                  -> token constructed WITH CUSTOM CLAIMS -- THIS PROJECT'S unique value
                       -> resource server validates it (cards 0099-0106's side)
```

## 7. Gotchas & takeaways

> **Gotcha:** running your own authorization server means taking on responsibility for everything a third-party identity provider otherwise handles for you — key rotation (card 0101), token revocation, consent screen UX, security patching against emerging OAuth2 attack patterns, and ongoing conformance with evolving specifications. This is a genuine operational commitment, not a purely technical decision; many applications are better served by delegating to an established identity provider (cards 0088–0110) unless there's a concrete reason (custom claims, being an identity provider *for others*) that specifically requires running one's own.

- Spring Authorization Server builds the *authorization server* role in the OAuth2/OIDC relationship — the piece that issues tokens, which every earlier client and resource-server card in this course assumed already existed elsewhere.
- Reach for it specifically when an application needs to *be* an identity provider (for its own client applications, or for third-party integrators), not merely to authenticate against one or validate tokens from one.
- Every endpoint it exposes (`/oauth2/authorize`, `/oauth2/token`, `/oauth2/jwks`, OIDC discovery metadata) is the direct counterpart to something an earlier card covered from the consuming side.
- Running your own authorization server grants full control over issued token claims and structure — a capability third-party providers generally don't offer, since their token shape serves many unrelated applications simultaneously.
- This is a genuine operational responsibility, not just a code dependency — the next cards in this section cover its relationship to Spring Security, spec conformance, and getting a minimal instance running.
