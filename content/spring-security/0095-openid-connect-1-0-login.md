---
card: spring-security
gi: 95
slug: openid-connect-1-0-login
title: "OpenID Connect 1.0 login"
---

## 1. What it is

OpenID Connect (OIDC) is a thin identity layer built on top of the exact OAuth2 Authorization Code grant covered in card 0090: it adds one crucial new artifact to the token response — the **ID token**, a signed JWT that asserts *who authenticated and when*, distinct from the access token, which only asserts *what this bearer is allowed to call*. Practically, enabling OIDC for a provider is often just adding `openid` to the requested `scope`; Spring Security detects that scope, recognizes the provider is OIDC-compliant, validates the returned ID token's signature and claims automatically, and produces an `OidcUser` (a subtype of `OAuth2User`) instead of a plain `OAuth2User`. The same `oauth2Login()` DSL from card 0088 handles both cases — OIDC support isn't a separate method, it's the same filter chain recognizing a richer response.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .oauth2Login(Customizer.withDefaults()); // works for OIDC providers exactly like OAuth2-only ones
    return http.build();
}
```
```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          google:
            client-id: abc123
            client-secret: ${GOOGLE_CLIENT_SECRET}
            scope: openid,profile,email   # "openid" is what makes this an OIDC login, not just OAuth2
```

## 2. Why & when

Plain OAuth2 was never designed as an authentication protocol — it was designed for *authorization* (letting an app act on a user's behalf against an API), and using an access token as a proxy for "the user is authenticated" is a well-documented anti-pattern (the access token's audience, issuer, and expiry aren't guaranteed to say anything about identity at all, and different providers structure them inconsistently). OIDC exists specifically to close that gap: the ID token is a standardized, signed, verifiable statement — "issuer X asserts subject Y authenticated at time Z for audience W" — with a fixed claim shape (`iss`, `sub`, `aud`, `exp`, `iat`) that every compliant provider produces the same way.

Reach for OIDC (rather than plain OAuth2 login) when:

- The provider supports it — Google, Microsoft/Azure AD, Okta, Auth0, and most modern identity providers are OIDC-compliant; GitHub, notably, is not (it's OAuth2-only), which is exactly why card 0088's examples used GitHub as the plain-`OAuth2User` case.
- You need a verifiable, cryptographically signed statement of *when* authentication happened and *by whom* — useful for step-up authentication or audit logging, where trusting an access token's mere presence isn't enough.
- You want a standardized userinfo shape — OIDC's `/userinfo` endpoint and standard claims (`email`, `email_verified`, `name`, `picture`) are far more consistent across providers than each provider's bespoke OAuth2 profile endpoint.
- Building single sign-out across multiple applications sharing one identity provider — OIDC's RP-initiated logout (card 0097) depends on the ID token issued during this login.

## 3. Core concept

```
oauth2Login() ALREADY handles OIDC -- no separate DSL method. What differs from plain OAuth2:

  Plain OAuth2 (e.g. GitHub):
    scope does NOT include "openid"
    token response: access_token (+ refresh_token)
    profile comes from: userInfoUri (provider-specific shape)
    principal produced: OAuth2User

  OIDC (e.g. Google, Okta):
    scope INCLUDES "openid" (usually alongside "profile", "email")
    token response: access_token + id_token (a signed JWT) (+ refresh_token)
    id_token is VALIDATED: signature (against provider's public keys), iss, aud, exp, nonce
    profile comes from: BOTH the id_token's claims AND (optionally) the userInfoUri
    principal produced: OidcUser (extends OAuth2User, adds getIdToken(), getClaims())

Spring Security decides which path to take based on whether "openid" scope was requested/granted --
it is the presence of that ONE scope value that turns an OAuth2 login into an OIDC login.
```

The ID token's validation (signature, `iss`, `aud`, `exp`) happens automatically inside `OidcAuthorizationCodeAuthenticationProvider` — application code never re-implements JWT verification for this.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram comparing plain oauth2 login producing an OAuth2User from a provider specific profile endpoint against OIDC login where the openid scope triggers an id token being issued alongside the access token the id token is validated and merged with optional userinfo data to produce an OidcUser">
  <rect x="20" y="20" width="280" height="210" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="160" y="42" fill="#8b949e" font-size="10.5" text-anchor="middle" font-family="sans-serif">Plain OAuth2 (no "openid" scope)</text>
  <rect x="40" y="60" width="240" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="79" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">token response: access_token only</text>
  <line x1="160" y1="90" x2="160" y2="115" stroke="#8b949e" stroke-width="1.4" marker-end="url(#d95)"/>
  <rect x="40" y="117" width="240" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="160" y="136" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">GET userInfoUri (provider-specific)</text>
  <line x1="160" y1="147" x2="160" y2="172" stroke="#8b949e" stroke-width="1.4" marker-end="url(#d95)"/>
  <rect x="40" y="174" width="240" height="34" rx="5" fill="#161b22" stroke="#6db33f" stroke-width="1.4"/>
  <text x="160" y="195" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth2User</text>

  <rect x="330" y="20" width="290" height="210" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="475" y="42" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">OIDC ("openid" IN scope)</text>
  <rect x="350" y="60" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="79" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">token response: access_token + id_token</text>
  <line x1="475" y1="90" x2="475" y2="112" stroke="#6db33f" stroke-width="1.4" marker-end="url(#d95b)"/>
  <rect x="350" y="114" width="250" height="30" rx="5" fill="#161b22" stroke="#f85149" stroke-width="1"/>
  <text x="475" y="133" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">validate id_token: sig, iss, aud, exp, nonce</text>
  <line x1="475" y1="144" x2="475" y2="166" stroke="#6db33f" stroke-width="1.4" marker-end="url(#d95b)"/>
  <rect x="350" y="168" width="250" height="30" rx="5" fill="#161b22" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="187" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">(optional) GET standardized /userinfo</text>
  <line x1="475" y1="198" x2="475" y2="210" stroke="#6db33f" stroke-width="1.4" marker-end="url(#d95b)"/>
  <text x="475" y="222" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">OidcUser (extends OAuth2User)</text>

  <defs>
    <marker id="d95" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="d95b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The `openid` scope is the single switch that adds an extra, cryptographically-validated identity artifact to the same underlying flow.

## 5. Runnable example

The scenario: simulate a token response that may or may not include an `id_token` depending on requested scope, build the right principal type for each case, then add ID token claim validation (`iss`, `aud`, `exp`) that must pass before an `OidcUser` can be trusted.

### Level 1 — Basic

Requesting `openid` scope changes what the token response contains, and therefore which principal type gets built.

```java
import java.util.*;

public class OidcLoginLevel1 {
    record TokenResponse(String accessToken, String idToken) {} // idToken is null for plain OAuth2

    static class AuthorizationServer {
        TokenResponse issueTokens(List<String> requestedScopes) {
            String accessToken = "access-tok-abc";
            String idToken = requestedScopes.contains("openid") ? "id-tok-signed-jwt" : null;
            return new TokenResponse(accessToken, idToken);
        }
    }

    interface Principal { String describe(); }
    record OAuth2User(String accessToken) implements Principal {
        public String describe() { return "OAuth2User(accessToken=" + accessToken + ")"; }
    }
    record OidcUser(String accessToken, String idToken) implements Principal {
        public String describe() { return "OidcUser(accessToken=" + accessToken + ", idToken=" + idToken + ")"; }
    }

    static Principal buildPrincipal(TokenResponse tokens) {
        return tokens.idToken() != null
                ? new OidcUser(tokens.accessToken(), tokens.idToken())
                : new OAuth2User(tokens.accessToken());
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();

        Principal githubLogin = buildPrincipal(server.issueTokens(List.of("read:user")));
        Principal googleLogin = buildPrincipal(server.issueTokens(List.of("openid", "profile", "email")));

        System.out.println("github: " + githubLogin.describe());
        System.out.println("google: " + googleLogin.describe());
    }
}
```

**How to run:** save as `OidcLoginLevel1.java`, run `java OidcLoginLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
github: OAuth2User(accessToken=access-tok-abc)
google: OidcUser(accessToken=access-tok-abc, idToken=id-tok-signed-jwt)
```

`buildPrincipal` is the decision Spring Security makes internally: the *presence of an `id_token`* in the response (itself a consequence of requesting the `openid` scope) is what determines whether an `OidcUser` or a plain `OAuth2User` gets built.

### Level 2 — Intermediate

Model the ID token as a claims map rather than an opaque string, and extract standard claims from it.

```java
import java.util.*;

public class OidcLoginLevel2 {
    record IdToken(Map<String, Object> claims) {
        Object claim(String name) { return claims.get(name); }
    }
    record TokenResponse(String accessToken, IdToken idToken) {}

    static class AuthorizationServer {
        TokenResponse issueTokens(List<String> requestedScopes, String subject, String email) {
            String accessToken = "access-tok-abc";
            IdToken idToken = null;
            if (requestedScopes.contains("openid")) {
                Map<String, Object> claims = new LinkedHashMap<>();
                claims.put("iss", "https://accounts.google.com");
                claims.put("sub", subject);
                claims.put("aud", "abc123"); // this app's own client_id
                claims.put("exp", System.currentTimeMillis() / 1000 + 3600);
                claims.put("email", email);
                idToken = new IdToken(claims);
            }
            return new TokenResponse(accessToken, idToken);
        }
    }

    record OidcUser(String accessToken, IdToken idToken) {
        String getSubject() { return String.valueOf(idToken.claim("sub")); }
        String getEmail() { return String.valueOf(idToken.claim("email")); }
    }

    public static void main(String[] args) {
        AuthorizationServer server = new AuthorizationServer();

        TokenResponse tokens = server.issueTokens(List.of("openid", "email"), "109283746", "alice@example.com");
        OidcUser user = new OidcUser(tokens.accessToken(), tokens.idToken());

        System.out.println("subject: " + user.getSubject());
        System.out.println("email: " + user.getEmail());
        System.out.println("issuer: " + user.idToken().claim("iss"));
    }
}
```

**How to run:** save as `OidcLoginLevel2.java`, run `java OidcLoginLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
subject: 109283746
email: alice@example.com
issuer: https://accounts.google.com
```

What changed: the ID token is now a real claims map (`iss`, `sub`, `aud`, `exp`, plus whatever standard or custom claims the provider includes), and `OidcUser` exposes typed accessors over it — mirroring the real `OidcUser.getSubject()` / `.getEmail()` methods, which are just convenient lookups into this same claims map.

### Level 3 — Advanced

A real ID token must be validated before it's trusted — a wrong `aud` (issued for a different application), an `iss` that doesn't match the expected provider, or an expired `exp` must all be rejected. Level 3 adds that validation as a mandatory gate before an `OidcUser` can be constructed.

```java
import java.util.*;

public class OidcLoginLevel3 {
    record IdToken(Map<String, Object> claims) {
        Object claim(String name) { return claims.get(name); }
    }
    record TokenResponse(String accessToken, IdToken idToken) {}

    static class OidcValidationException extends RuntimeException {
        OidcValidationException(String message) { super(message); }
    }

    // mirrors the mandatory checks OidcIdTokenValidator performs before an OidcUser is ever built
    static void validate(IdToken idToken, String expectedIssuer, String expectedAudience) {
        String iss = String.valueOf(idToken.claim("iss"));
        if (!expectedIssuer.equals(iss)) {
            throw new OidcValidationException("iss mismatch: expected " + expectedIssuer + " but got " + iss);
        }
        Object aud = idToken.claim("aud");
        if (!expectedAudience.equals(aud)) {
            throw new OidcValidationException("aud mismatch: this id_token was not issued for this client");
        }
        long exp = ((Number) idToken.claim("exp")).longValue();
        long now = System.currentTimeMillis() / 1000;
        if (now >= exp) {
            throw new OidcValidationException("id_token expired at " + exp + " (now=" + now + ")");
        }
    }

    record OidcUser(String accessToken, IdToken idToken) {
        String getSubject() { return String.valueOf(idToken.claim("sub")); }
    }

    static OidcUser buildOidcUser(TokenResponse tokens, String expectedIssuer, String expectedAudience) {
        validate(tokens.idToken(), expectedIssuer, expectedAudience); // gate -- throws before construction on failure
        return new OidcUser(tokens.accessToken(), tokens.idToken());
    }

    public static void main(String[] args) {
        String ourClientId = "abc123";
        String trustedIssuer = "https://accounts.google.com";

        Map<String, Object> validClaims = new LinkedHashMap<>();
        validClaims.put("iss", trustedIssuer);
        validClaims.put("sub", "109283746");
        validClaims.put("aud", ourClientId);
        validClaims.put("exp", System.currentTimeMillis() / 1000 + 3600);
        TokenResponse validTokens = new TokenResponse("access-tok", new IdToken(validClaims));

        Map<String, Object> wrongAudienceClaims = new LinkedHashMap<>(validClaims);
        wrongAudienceClaims.put("aud", "some-OTHER-app-client-id"); // token was meant for a different app
        TokenResponse wrongAudienceTokens = new TokenResponse("access-tok", new IdToken(wrongAudienceClaims));

        Map<String, Object> expiredClaims = new LinkedHashMap<>(validClaims);
        expiredClaims.put("exp", System.currentTimeMillis() / 1000 - 60); // expired one minute ago
        TokenResponse expiredTokens = new TokenResponse("access-tok", new IdToken(expiredClaims));

        for (var entry : Map.of(
                "valid id_token", validTokens,
                "wrong audience", wrongAudienceTokens,
                "expired id_token", expiredTokens).entrySet()) {
            try {
                OidcUser user = buildOidcUser(entry.getValue(), trustedIssuer, ourClientId);
                System.out.println(entry.getKey() + ": ACCEPTED, subject=" + user.getSubject());
            } catch (OidcValidationException e) {
                System.out.println(entry.getKey() + ": REJECTED -- " + e.getMessage());
            }
        }
    }
}
```

**How to run:** save as `OidcLoginLevel3.java`, run `java OidcLoginLevel3.java` (JDK 17+ runs single files directly).

Expected output (order may vary since `Map.of` does not guarantee iteration order):
```
valid id_token: ACCEPTED, subject=109283746
wrong audience: REJECTED -- aud mismatch: this id_token was not issued for this client
expired id_token: REJECTED -- id_token expired at ... (now=...)
```

What changed: `buildOidcUser` now calls `validate` as a mandatory gate before constructing anything — an `id_token` whose `aud` doesn't match this application's own client id (meaning it was issued for a *different* application and should never be trusted here, even if otherwise well-formed) or whose `exp` has passed is rejected outright, exactly mirroring the checks `OidcIdTokenValidator` performs automatically inside Spring Security's OIDC support.

## 6. Walkthrough

Trace the "valid id_token" case from Level 3 as a full request/response sequence, picking up where card 0090's Authorization Code grant leaves off.

**Step 1 — the code-for-token exchange (identical to card 0090, but now requesting `openid` scope):**
```
POST /token HTTP/1.1
Host: accounts.google.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=SplxlOBeZQQYbYS6WxSbIA&redirect_uri=https%3A%2F%2Fapp.example.com%2Flogin%2Foauth2%2Fcode%2Fgoogle&client_id=abc123&client_secret=***
```

**Step 2 — because `openid` was in the originally requested scope, the response now includes `id_token` alongside `access_token`:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"access-tok","id_token":"eyJhbGciOi...(a signed JWT)...","token_type":"Bearer","expires_in":3600}
```
This corresponds to `server.issueTokens(...)` in Level 1/2 returning a non-null `idToken` because `"openid"` was present in the requested scopes.

**Step 3 — the ID token's signature is verified** against the provider's published public keys (fetched from its JWKS endpoint, cached by Spring Security) — this step is assumed to have already passed by the time Level 3's code runs, since `validate` only checks the *claims*, not the signature; a real deployment validates both, in that order, with signature verification first.

**Step 4 — claim validation runs**, corresponding to `validate(tokens.idToken(), trustedIssuer, ourClientId)`:
- `iss` (`"https://accounts.google.com"`) is compared against the issuer this application expects for the `google` registration — matches, so no exception yet.
- `aud` (`"abc123"`) is compared against this application's own `client_id` — matches, so no exception yet.
- `exp` is compared against the current time — still in the future, so no exception.

**Step 5 — construction.** Since `validate` returned without throwing, `buildOidcUser` proceeds to `new OidcUser(tokens.accessToken(), tokens.idToken())`.

**Step 6 — the principal is available to application code.** A controller parameter typed `@AuthenticationPrincipal OidcUser` now resolves to this object; `user.getSubject()` returns `"109283746"`, the stable, provider-issued identifier for this end user.

```
token response arrives
   -> signature check (against provider's public keys)      [assumed passed before Level 3's code runs]
   -> iss check      : "https://accounts.google.com" == expected  -> OK
   -> aud check      : "abc123" == this app's client_id           -> OK
   -> exp check      : exp > now                                  -> OK
   -> OidcUser constructed, subject = "109283746"
```

**Step 7 — the wrong-audience case, for contrast.** If a malicious or misconfigured party presented an ID token whose `aud` were `"some-OTHER-app-client-id"`, the `aud` check in step 4 would fail immediately — `validate` throws `OidcValidationException`, `buildOidcUser` never reaches the `new OidcUser(...)` line, and no principal is ever placed in the `SecurityContext` for that request, exactly as `OidcIdTokenValidator` would reject it before `OidcLoginAuthenticationProvider` builds anything.

## 7. Gotchas & takeaways

> **Gotcha:** an `id_token`'s `aud` claim must match *this specific application's* `client_id`, not just "some client_id belonging to the same provider." An ID token issued by Google for a *different* application, if somehow presented to this one, is cryptographically valid (correctly signed by Google) but must still be rejected — signature validity proves who issued the token, not that it was issued *for you*, which is exactly what the `aud` check exists to establish.

- OIDC is not a separate protocol from OAuth2 — it is the same Authorization Code grant with one additional artifact (a signed ID token) triggered by requesting the `openid` scope.
- The single distinguishing signal Spring Security uses is the presence of `openid` in the granted scopes: that alone decides whether an `OAuth2User` or the richer `OidcUser` gets built.
- An `OidcUser`'s ID token must pass signature verification (against the provider's published keys) and claim validation (`iss`, `aud`, `exp`, and `nonce` when applicable) before it is trusted — Spring Security performs both automatically, and application code should never need to re-implement this.
- Not every provider supports OIDC — GitHub is a common example of an OAuth2-only provider, which is why it produces a plain `OAuth2User` rather than an `OidcUser` even though the login DSL is identical.
- `OidcUser` extends `OAuth2User`, so code written against the more general type still works, but only `OidcUser` exposes ID-token-specific data (`getIdToken()`, `getClaims()`) — the next card covers exactly what's available there and how it differs from the OAuth2 userinfo response.
