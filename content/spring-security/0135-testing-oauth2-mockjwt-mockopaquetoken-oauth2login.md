---
card: spring-security
gi: 135
slug: testing-oauth2-mockjwt-mockopaquetoken-oauth2login
title: "Testing OAuth2 (mockJwt, mockOpaqueToken, oauth2Login)"
---

## 1. What it is

Cards 0100–0106 covered how a resource server validates JWTs and opaque tokens in production, and card 0088 covered the full `oauth2Login()` browser redirect flow — testing either without dedicated support would mean either standing up a real (or embedded) authorization server for every test, or manually constructing signed JWTs and wiring a fake `JwtDecoder`. `SecurityMockMvcRequestPostProcessors.jwt()`/`.opaqueToken()` (for resource server tests) and `.oauth2Login()` (for client-side login tests) exist specifically to skip that infrastructure: they let a test declare "this request carries a JWT/opaque token/OAuth2 login with these specific claims and authorities" directly, producing a request the security filter chain processes exactly as if a real, fully-validated token or completed login had arrived.

```java
@Test
void resourceServerAcceptsValidJwt() throws Exception {
    mockMvc.perform(get("/api/orders")
            .with(jwt().jwt(builder -> builder.claim("scope", "read:orders"))
                       .authorities(new SimpleGrantedAuthority("SCOPE_read:orders"))))
           .andExpect(status().isOk());
}

@Test
void resourceServerAcceptsValidOpaqueToken() throws Exception {
    mockMvc.perform(get("/api/orders").with(opaqueToken().authorities(new SimpleGrantedAuthority("SCOPE_read:orders"))))
           .andExpect(status().isOk());
}

@Test
void clientEndpointWorksForLoggedInUser() throws Exception {
    mockMvc.perform(get("/profile").with(oauth2Login().attributes(attrs -> attrs.put("email", "alice@example.com"))))
           .andExpect(status().isOk());
}
```

## 2. Why & when

A genuine JWT requires a real signature from a real (or embedded) authorization server's private key, and a real opaque token requires a live introspection endpoint to call — reproducing either faithfully in every resource-server test would mean standing up substantial test infrastructure just to verify a controller correctly reads `scope` claims or handles a missing authority. `jwt()`/`opaqueToken()` sidestep this entirely by constructing the *post-validation* result directly — a `Jwt` object or an introspection-equivalent principal, exactly as `JwtAuthenticationConverter`/`OpaqueTokenAuthenticationConverter` would have produced from a genuinely validated token — letting a test focus on what the application does with an authenticated OAuth2 principal, not on re-verifying that JWT signature validation itself works (which is Spring Security's own, already-tested responsibility, not the application's).

Reach for these testing utilities when:

- Testing a resource server endpoint's authorization logic against specific scopes/claims (cards 0100, 0104) — `jwt()`'s `.jwt(builder -> ...)` and `.authorities(...)` let a test specify exactly the claims and resulting authorities it needs, without any real token or key material.
- Testing an opaque-token-secured endpoint (card 0102) similarly, via `opaqueToken()`, without needing a live introspection endpoint.
- Testing a controller or view that reads from an `OAuth2User`/`OidcUser` principal after `oauth2Login()` (card 0088) — `.oauth2Login().attributes(...)` lets a test populate exactly the claims a real login would have produced, without any real redirect-and-exchange flow.
- Verifying `@PreAuthorize("hasAuthority('SCOPE_...')")`-style checks (card 0104) against an OAuth2-secured endpoint specifically, as opposed to a session-based one.

## 3. Core concept

```
jwt() (for resource server tests):
    builds a Jwt object DIRECTLY from specified claims -- NO real signing, NO real JwtDecoder call
    .jwt(builder -> builder.claim("scope", "read:orders").subject("alice"))
    .authorities(...)  -- explicitly specify the RESULTING authorities (bypassing the
                          real JwtAuthenticationConverter's claim-to-authority mapping,
                          UNLESS you want to test that mapping specifically)

opaqueToken() (for resource server tests):
    builds an authenticated principal DIRECTLY -- NO real introspection call is made
    .attributes(attrs -> attrs.put("scope", "read:orders"))
    .authorities(...)

oauth2Login() (for CLIENT tests -- the oauth2Login() DSL from card 0088):
    builds an OAuth2User/OidcUser DIRECTLY -- NO real redirect, NO real code exchange
    .attributes(attrs -> attrs.put("email", "alice@example.com"))
    .authorities(...)

ALL THREE skip real token validation/exchange machinery ENTIRELY -- they construct the
POST-VALIDATION result directly, exactly as if a real, successful validation/login had
already occurred. This tests "what does my application do with this principal," NOT
"does JWT signature verification / OAuth2 code exchange work" (Spring Security's own
responsibility, already covered by the framework's own test suite).
```

This division of testing responsibility — framework tests its own protocol mechanics, application tests its own business logic given a validated principal — is exactly the same principle underlying every testing utility in this section.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing jwt opaqueToken and oauth2Login test utilities each skipping real token validation or oauth exchange machinery and instead directly constructing the post validation principal that a real successful flow would have produced">
  <rect x="20" y="20" width="180" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="42" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">jwt()</text>
  <text x="110" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NO real signature check</text>
  <text x="110" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">builds Jwt directly</text>
  <text x="110" y="92" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">for RESOURCE SERVER tests</text>

  <rect x="230" y="20" width="180" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="320" y="42" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">opaqueToken()</text>
  <text x="320" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NO real introspection call</text>
  <text x="320" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">builds principal directly</text>
  <text x="320" y="92" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">for RESOURCE SERVER tests</text>

  <rect x="440" y="20" width="180" height="80" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="530" y="42" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">oauth2Login()</text>
  <text x="530" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NO real redirect/exchange</text>
  <text x="530" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">builds OAuth2User directly</text>
  <text x="530" y="92" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">for CLIENT (login) tests</text>

  <text x="320" y="130" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">ALL skip protocol mechanics -- test application logic against an already-valid principal</text>
</svg>

Each utility skips its respective protocol's validation machinery, focusing tests entirely on how the application reacts to an already-authenticated principal.

## 5. Runnable example

The scenario: model the three testing utilities as builders producing already-authenticated principals directly, growing from a single JWT-based authorization check into an opaque-token equivalent, then into an OAuth2 login test verifying attribute-based application logic.

### Level 1 — Basic

Build a `Jwt`-equivalent test principal directly, mirroring `jwt().jwt(...).authorities(...)`.

```java
import java.util.*;

public class TestingOAuth2Level1 {
    record Jwt(String subject, Map<String, Object> claims) {}
    record JwtAuthenticationToken(Jwt jwt, Set<String> authorities) {}

    // mirrors SecurityMockMvcRequestPostProcessors.jwt() -- NO real signature verification happens
    static JwtAuthenticationToken jwt(Map<String, Object> claims, Set<String> authorities) {
        return new JwtAuthenticationToken(new Jwt((String) claims.get("sub"), claims), authorities);
    }

    // the endpoint under test -- mirrors @PreAuthorize("hasAuthority('SCOPE_read:orders')")
    static int handleRequest(JwtAuthenticationToken auth) {
        return auth.authorities().contains("SCOPE_read:orders") ? 200 : 403;
    }

    public static void main(String[] args) {
        JwtAuthenticationToken auth = jwt(Map.of("sub", "alice", "scope", "read:orders"), Set.of("SCOPE_read:orders"));

        System.out.println("status: " + handleRequest(auth));
    }
}
```

**How to run:** save as `TestingOAuth2Level1.java`, run `java TestingOAuth2Level1.java` (JDK 17+ runs single files directly).

Expected output:
```
status: 200
```

`jwt(...)` mirrors `.with(jwt().jwt(...).authorities(...))`: it constructs an already-authenticated `JwtAuthenticationToken` directly, with no real signature check or `JwtDecoder` call involved — the test exercises exactly the authorization logic (`handleRequest`) that matters, given an already-valid token.

### Level 2 — Intermediate

The opaque-token equivalent, and both mechanisms compared side by side against the same endpoint.

```java
import java.util.*;

public class TestingOAuth2Level2 {
    record Jwt(String subject, Map<String, Object> claims) {}
    record JwtAuthenticationToken(Jwt jwt, Set<String> authorities) {}
    record OpaqueTokenAuthentication(Map<String, Object> attributes, Set<String> authorities) {}

    static JwtAuthenticationToken jwt(Map<String, Object> claims, Set<String> authorities) {
        return new JwtAuthenticationToken(new Jwt((String) claims.get("sub"), claims), authorities);
    }

    // mirrors SecurityMockMvcRequestPostProcessors.opaqueToken() -- NO real introspection call happens
    static OpaqueTokenAuthentication opaqueToken(Map<String, Object> attributes, Set<String> authorities) {
        return new OpaqueTokenAuthentication(attributes, authorities);
    }

    static int handleRequestForJwt(JwtAuthenticationToken auth) {
        return auth.authorities().contains("SCOPE_read:orders") ? 200 : 403;
    }
    static int handleRequestForOpaqueToken(OpaqueTokenAuthentication auth) {
        return auth.authorities().contains("SCOPE_read:orders") ? 200 : 403;
    }

    public static void main(String[] args) {
        JwtAuthenticationToken jwtAuth = jwt(Map.of("sub", "alice"), Set.of("SCOPE_read:orders"));
        OpaqueTokenAuthentication opaqueAuth = opaqueToken(Map.of("sub", "bob"), Set.of("SCOPE_write:orders")); // wrong scope

        System.out.println("jwt-based request status: " + handleRequestForJwt(jwtAuth));
        System.out.println("opaque-token-based request status (wrong scope): " + handleRequestForOpaqueToken(opaqueAuth));
    }
}
```

**How to run:** save as `TestingOAuth2Level2.java`, run `java TestingOAuth2Level2.java` (JDK 17+ runs single files directly).

Expected output:
```
jwt-based request status: 200
opaque-token-based request status (wrong scope): 403
```

What changed: `opaqueToken(...)` mirrors `.with(opaqueToken().authorities(...))` — no live introspection endpoint is ever called, yet the resulting principal behaves exactly like a genuinely introspected one from the endpoint's point of view; bob's request, carrying the wrong scope, is correctly denied, verifying the same authorization logic works consistently regardless of which token validation mechanism (JWT or opaque) actually produced the authenticated principal.

### Level 3 — Advanced

`oauth2Login()`-style testing of a client endpoint that reads attributes from the logged-in `OAuth2User`, contrasted with the resource-server tests to reinforce the client-versus-resource-server distinction this card's core concept establishes.

```java
import java.util.*;

public class TestingOAuth2Level3 {
    record OAuth2User(Map<String, Object> attributes, Set<String> authorities) {
        Object getAttribute(String name) { return attributes.get(name); }
    }

    // mirrors SecurityMockMvcRequestPostProcessors.oauth2Login() -- NO real redirect or code exchange happens
    static OAuth2User oauth2Login(Map<String, Object> attributes) {
        return new OAuth2User(attributes, Set.of("OAUTH2_USER"));
    }

    // the CLIENT endpoint under test -- reads a claim from the authenticated OAuth2User
    static String renderProfilePage(OAuth2User user) {
        String email = (String) user.getAttribute("email");
        String name = (String) user.getAttribute("name");
        return "Welcome, " + (name != null ? name : email);
    }

    public static void main(String[] args) {
        // mirrors: .with(oauth2Login().attributes(attrs -> { attrs.put("email", "alice@example.com"); attrs.put("name", "Alice Example"); }))
        OAuth2User withName = oauth2Login(Map.of("email", "alice@example.com", "name", "Alice Example"));
        System.out.println(renderProfilePage(withName));

        // a provider that only supplies "email", no "name" attribute at all -- e.g. some OAuth2-only providers
        OAuth2User emailOnly = oauth2Login(Map.of("email", "bob@example.com"));
        System.out.println(renderProfilePage(emailOnly));
    }
}
```

**How to run:** save as `TestingOAuth2Level3.java`, run `java TestingOAuth2Level3.java` (JDK 17+ runs single files directly).

Expected output:
```
Welcome, Alice Example
Welcome, bob@example.com
```

What changed: `oauth2Login(...)` builds an already-logged-in `OAuth2User` directly, with no real browser redirect or authorization-code exchange (card 0090's protocol mechanics) ever simulated — the test focuses entirely on `renderProfilePage`'s own logic (preferring `name` when present, falling back to `email` otherwise), verifying application-level behavior against a realistic range of attribute combinations a real provider might supply, without any dependency on a real identity provider being reachable during the test run.

## 6. Walkthrough

Trace the resource-server JWT test from Level 1/2, then contrast with the client-side `oauth2Login()` test from Level 3, reinforcing which side of the OAuth2 relationship each utility is meant for.

**Step 1 — a resource server test, using `jwt()`:**
```java
@Test
void endpointRequiresReadScope() throws Exception {
    mockMvc.perform(get("/api/orders")
            .with(jwt().authorities(new SimpleGrantedAuthority("SCOPE_read:orders"))))
           .andExpect(status().isOk());
}
```
Here, the application under test *is* the resource server (cards 0099–0106) — `jwt()` stands in for a bearer token that would, in production, have been validated by `JwtDecoder` (card 0101) and converted to authorities by `JwtAuthenticationConverter` (card 0104). The test skips both of those steps and supplies their *result* directly.

**Step 2 — the request is dispatched, and `handleRequestForJwt`-equivalent logic runs.** Corresponding to `handleRequestForJwt(jwtAuth)` — the endpoint checks `auth.authorities().contains("SCOPE_read:orders")`, which is `true`, so the request succeeds.

**Step 3 — contrast: a client-side test, using `oauth2Login()`:**
```java
@Test
void profilePageShowsUsersName() throws Exception {
    mockMvc.perform(get("/profile")
            .with(oauth2Login().attributes(attrs -> attrs.put("name", "Alice Example"))))
           .andExpect(content().string(containsString("Welcome, Alice Example")));
}
```
Here, the application under test *is* the OAuth2 client (card 0088) — it's the one that would, in production, have redirected the browser to an identity provider, received a callback, and built an `OAuth2User` from the resulting profile response. `oauth2Login()` skips that entire flow, supplying the resulting `OAuth2User` directly, with whatever attributes the test wants to verify against.

**Step 4 — the profile page's rendering logic runs against this pre-built principal.** Corresponding to `renderProfilePage(withName)` — reading `"name"` from the attributes, producing `"Welcome, Alice Example"`.

**Step 5 — both tests are legitimate, targeted verifications, but of genuinely different application roles.** The resource-server test verifies "does my API correctly enforce scope requirements"; the client-side test verifies "does my UI correctly render a logged-in user's profile data" — neither test re-verifies Spring Security's own OAuth2 protocol implementation, which is exactly the intended division of testing responsibility.

```
Resource server test (jwt()):     bypasses JWT validation -> tests: does the ENDPOINT enforce scope correctly?
Client test (oauth2Login()):      bypasses the login flow  -> tests: does the APPLICATION handle the principal correctly?
```

## 7. Gotchas & takeaways

> **Gotcha:** none of `jwt()`, `opaqueToken()`, or `oauth2Login()` verify that the *real* validation/exchange machinery (signature checking, introspection calls, the actual redirect-and-code-exchange flow) works correctly — they deliberately bypass all of it. A misconfigured `JwtDecoder` (wrong issuer URI, unreachable JWKS endpoint) in production would never be caught by tests using `jwt()`, since those tests never touch a real `JwtDecoder` at all. These utilities test application logic *given* a valid principal, not whether the mechanism that produces one in production is correctly configured — a separate, narrower category of test (or careful manual/integration verification against a real or embedded authorization server) is needed for that.

- `jwt()` and `opaqueToken()` are for testing resource server (card 0099+) authorization logic — they construct an already-validated principal directly, skipping signature verification or introspection entirely.
- `oauth2Login()` is for testing OAuth2 client (card 0088) behavior — it constructs an already-logged-in `OAuth2User`/`OidcUser` directly, skipping the entire redirect-and-exchange flow.
- All three exist to let application-level tests focus on "what does my code do given a valid, authenticated OAuth2 principal," which is a genuinely different (and more appropriate) test target than re-verifying Spring Security's own, already-tested protocol implementation.
- Choosing the right utility depends on which side of the OAuth2 relationship the code under test plays — resource server code needs `jwt()`/`opaqueToken()`; client-side code needs `oauth2Login()`.
- Real end-to-end verification that the actual token validation or login flow is correctly configured (a real issuer URI, a genuinely reachable JWKS endpoint, a working redirect) requires separate integration testing against a real or embedded authorization server — these utilities are not a substitute for that.
