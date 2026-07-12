---
card: spring-authorization-server
gi: 45
slug: extending-grant-types
title: "Extending grant types"
---

## 1. What it is

Extending grant types means adding an entirely new `grant_type` value the token endpoint understands, beyond the standard ones (authorization code, client credentials, refresh token, device code, token exchange) covered so far. It's done by implementing a custom `AuthenticationConverter` (parses the request into an `Authentication` object), a custom `AuthenticationProvider` (validates it and produces a token), and registering both via `.tokenEndpoint(tokenEndpoint -> tokenEndpoint.accessTokenRequestConverter(...).authenticationProvider(...))`.

## 2. Why & when

Every grant type covered so far maps to a standard, widely-understood OAuth2 use case. But some systems have an authentication mechanism that doesn't fit any of them — a legacy system migrating users off an old proprietary token format, an IoT fleet that authenticates via a pre-shared hardware certificate rather than any of the standard credential types, or a partner integration that needs to exchange a SAML assertion for an OAuth2 token in a way the standard token-exchange grant (card 0041) doesn't quite model. Spring Authorization Server's token endpoint is deliberately extensible for exactly these cases, rather than forcing every possible authentication scheme into the existing standard grants.

Reach for a custom grant type when:

- Migrating a legacy authentication system where users hold a pre-existing credential (a signed legacy token, an API key from an old system) that needs to become a first-class, short-lived OAuth2 access token.
- Building non-standard machine authentication (hardware-backed certificates, custom pre-shared keys) that doesn't map cleanly onto client credentials.
- Deciding whether a custom grant is actually warranted — first check if token exchange (card 0041) or client credentials (card 0039) with a custom `AuthenticationProvider` behind them can express the need; a genuinely new `grant_type` value is a bigger commitment (clients need to know about it explicitly) and should be reserved for cases the standard grants truly can't express.

## 3. Core concept

Think of the token endpoint as a single reception desk that already has forms for several standard requests (passport renewal, ID replacement, address change — the standard grant types). Extending grant types is like adding an entirely new form to that same desk for a request type unique to this particular office (say, "legacy card exchange" for people still holding an old-format ID from a discontinued system). The desk clerk (the token endpoint) needs a new intake form (the `AuthenticationConverter`, which parses the raw request into a structured object) and a new procedure manual for validating and processing that specific request type (the `AuthenticationProvider`) — but everything downstream (issuing the actual token, recording it, signing it) reuses all the same machinery every other grant type already relies on.

```
POST /oauth2/token
    grant_type=urn:example:params:oauth:grant-type:legacy-token
    legacy_token=LGCY-9F8E7D6C
    client_id=migration-service
```

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom converter parses the request, custom provider validates it, and standard token generation machinery produces the final token">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Custom</text>
  <text x="110" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AuthenticationConverter</text>

  <rect x="260" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Custom</text>
  <text x="350" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AuthenticationProvider</text>

  <rect x="500" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="580" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Standard token</text>
  <text x="580" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">generation (card 0019)</text>

  <line x1="200" y1="45" x2="255" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="440" y1="45" x2="495" y2="45" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="150" y="150" width="400" height="80" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="350" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Reused unchanged: RegisteredClient lookup,</text>
  <text x="350" y="193" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth2AuthorizationService persistence, JWK signing,</text>
  <text x="350" y="211" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">token customizers (card 0044) — same as every other grant</text>
</svg>

Only the initial parsing and validation logic is new — everything from token construction onward is the exact same machinery every standard grant type shares.

## 5. Runnable example

The scenario: building a custom grant that exchanges a legacy system's proprietary token for a new OAuth2 access token, growing to validate the legacy token's signature properly, and finally to mark issued tokens so downstream systems can distinguish "migrated via legacy grant" from normal logins for auditing.

### Level 1 — Basic

```java
// LegacyTokenAuthenticationToken.java
import org.springframework.security.authentication.AbstractAuthenticationToken;
import org.springframework.security.oauth2.core.AuthorizationGrantType;

import java.util.Collections;
import java.util.Set;

public class LegacyTokenAuthenticationToken extends AbstractAuthenticationToken {

    public static final AuthorizationGrantType LEGACY_TOKEN_GRANT_TYPE =
            new AuthorizationGrantType("urn:example:params:oauth:grant-type:legacy-token");

    private final String legacyToken;
    private final org.springframework.security.core.Authentication clientPrincipal;
    private final Set<String> scopes;

    public LegacyTokenAuthenticationToken(String legacyToken,
            org.springframework.security.core.Authentication clientPrincipal, Set<String> scopes) {
        super(Collections.emptyList());
        this.legacyToken = legacyToken;
        this.clientPrincipal = clientPrincipal;
        this.scopes = scopes;
        setAuthenticated(false);
    }

    public String getLegacyToken() { return legacyToken; }
    public Set<String> getScopes() { return scopes; }

    @Override
    public Object getCredentials() { return legacyToken; }

    @Override
    public Object getPrincipal() { return clientPrincipal; }
}
```

**How to run:** this class alone doesn't run standalone — it's the request model consumed by the converter and provider below. It compiles as a plain POJO extending Spring Security's `AbstractAuthenticationToken`, ready to be wired into the token endpoint next.

### Level 2 — Intermediate

The converter parses the raw HTTP request into this object, and the provider validates the legacy token, resolving it to a real user before issuing a standard access token.

```java
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.server.authorization.authentication.OAuth2ClientAuthenticationToken;
import org.springframework.security.web.authentication.AuthenticationConverter;

public class LegacyTokenAuthenticationConverter implements AuthenticationConverter {

    @Override
    public Authentication convert(HttpServletRequest request) {
        String grantType = request.getParameter("grant_type");
        if (!LegacyTokenAuthenticationToken.LEGACY_TOKEN_GRANT_TYPE.getValue().equals(grantType)) {
            return null; // not our grant type; let other converters handle it
        }
        String legacyToken = request.getParameter("legacy_token");
        Authentication clientPrincipal = org.springframework.security.core.context.SecurityContextHolder
                .getContext().getAuthentication(); // client already authenticated by earlier filters
        return new LegacyTokenAuthenticationToken(legacyToken, clientPrincipal, java.util.Set.of("legacy.migrated"));
    }
}

public class LegacyTokenAuthenticationProvider implements AuthenticationProvider {

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        LegacyTokenAuthenticationToken legacyAuth = (LegacyTokenAuthenticationToken) authentication;

        String resolvedUsername = validateAndResolveLegacyToken(legacyAuth.getLegacyToken());
        if (resolvedUsername == null) {
            throw new org.springframework.security.oauth2.core.OAuth2AuthenticationException("invalid_grant");
        }

        // In a real implementation: build and return an OAuth2AccessTokenAuthenticationToken here,
        // reusing the standard token generator (card 0019) with resolvedUsername as the subject.
        throw new UnsupportedOperationException("wire to OAuth2TokenGenerator, see Level 3");
    }

    private String validateAndResolveLegacyToken(String legacyToken) {
        return legacyToken != null && legacyToken.startsWith("LGCY-") ? "migrated-user-42" : null;
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return LegacyTokenAuthenticationToken.class.isAssignableFrom(authentication);
    }
}
```

**How to run:** register both via `.tokenEndpoint(te -> te.accessTokenRequestConverter(new LegacyTokenAuthenticationConverter()).authenticationProvider(new LegacyTokenAuthenticationProvider()))`. Call `POST /oauth2/token` with `grant_type=urn:example:params:oauth:grant-type:legacy-token&legacy_token=LGCY-9F8E7D6C`. Expected behavior at this stage: the converter correctly routes the request to the custom provider, which validates the format and resolves a username (full token issuance completed in Level 3).

### Level 3 — Advanced

Production wires the provider through to actual token generation, and tags issued tokens with a claim identifying they came from the legacy migration path, so auditing and gradual sunset of the old system are both possible.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2Authorization;
import org.springframework.security.oauth2.server.authorization.OAuth2TokenType;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.token.DefaultOAuth2TokenContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2AccessTokenGenerator;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenContext;

public class WiredLegacyTokenAuthenticationProvider {

    private final OAuth2AccessTokenGenerator tokenGenerator;

    public WiredLegacyTokenAuthenticationProvider(OAuth2AccessTokenGenerator tokenGenerator) {
        this.tokenGenerator = tokenGenerator;
    }

    public Object issueForLegacyUser(RegisteredClient client, String resolvedUsername) {
        OAuth2TokenContext context = DefaultOAuth2TokenContext.builder()
                .registeredClient(client)
                .principal(new org.springframework.security.authentication.UsernamePasswordAuthenticationToken(
                        resolvedUsername, null, java.util.List.of()))
                .authorizationGrantType(LegacyTokenAuthenticationToken.LEGACY_TOKEN_GRANT_TYPE)
                .tokenType(OAuth2TokenType.ACCESS_TOKEN)
                .authorizedScopes(java.util.Set.of("legacy.migrated"))
                .build();

        var generatedToken = tokenGenerator.generate(context);
        // A downstream OAuth2TokenCustomizer (card 0044) can inspect
        // context.getAuthorizationGrantType() to add a "migrated_from_legacy" claim,
        // giving auditors a durable, queryable trail of which tokens came through this path.
        return generatedToken;
    }
}
```

**How to run:** call `issueForLegacyUser(client, "migrated-user-42")` after the Level 2 provider successfully validates a legacy token, and register a token customizer that adds `"auth_method": "legacy_migration"` when `context.getAuthorizationGrantType()` equals the custom grant type. Decode a resulting token: expect a normal, fully-signed access token carrying the standard claims plus `auth_method: legacy_migration`, indistinguishable in structure from any other issued token except for that one traceable claim.

What changed and why it's production-flavored: the custom grant now produces a token that's a first-class citizen alongside every standard-grant token — same signing, same persistence, same customizer pipeline (card 0044) — while still carrying a durable marker that lets operators track migration progress and eventually retire the legacy path once its usage claim shows it's no longer needed.

## 6. Walkthrough

Tracing a custom grant request end-to-end, in execution order:

1. `migration-service` sends `POST /oauth2/token` with `grant_type=urn:example:params:oauth:grant-type:legacy-token`, its own client credentials, and `legacy_token=LGCY-9F8E7D6C`.
2. The token endpoint's registered `accessTokenRequestConverter` chain runs each converter in turn; `LegacyTokenAuthenticationConverter` (Level 2) recognizes the `grant_type` value and returns a populated `LegacyTokenAuthenticationToken` — every other standard converter would have returned `null` for this unrecognized grant type.
3. Standard client authentication still applies first (card 0012) — `migration-service` itself must be a valid, authenticated client before its request is even routed to grant-specific handling.
4. The token endpoint's `AuthenticationManager` dispatches to whichever registered `AuthenticationProvider` reports `supports(...)` true for `LegacyTokenAuthenticationToken` — `WiredLegacyTokenAuthenticationProvider` (Level 3).
5. The provider validates the legacy token's authenticity (in a real system: checking its signature or a legacy system database), resolves it to `resolvedUsername`, and builds an `OAuth2TokenContext` describing what kind of token to generate and for whom.
6. It calls the same `OAuth2AccessTokenGenerator` (card 0019) every standard grant type uses — this is the point where the custom logic ends and the shared, well-tested token machinery takes back over.
7. A registered `OAuth2TokenCustomizer` (card 0044) inspects the grant type on the context and adds `auth_method: legacy_migration` before the token is signed.
8. The token endpoint responds `200 OK` with a standard-shaped access token response — from `migration-service`'s perspective, this looked exactly like any other grant type call, just with different request parameters.

```
POST /oauth2/token (grant_type=urn:example:...:legacy-token, legacy_token=...)
   |
client authentication (card 0012) --fail--> 401
   |  pass
accessTokenRequestConverter chain: which converter recognizes this grant_type?
   |  LegacyTokenAuthenticationConverter matches
AuthenticationManager -> LegacyTokenAuthenticationProvider.authenticate(...)
   |  legacy token invalid --> 400 invalid_grant
   |  valid, resolved to user
OAuth2AccessTokenGenerator.generate(context)  <- same path every standard grant uses
   |
OAuth2TokenCustomizer adds auth_method=legacy_migration
   |
200 OK {access_token: "...", scope: "legacy.migrated"}
```

Concrete request and response:

```
POST /oauth2/token HTTP/1.1
Authorization: Basic bWlncmF0aW9uLXNlcnZpY2U6c2VjcmV0
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aexample%3Aparams%3Aoauth%3Agrant-type%3Alegacy-token&legacy_token=LGCY-9F8E7D6C

HTTP/1.1 200 OK
Content-Type: application/json

{"access_token":"eyJhbGciOiJSUzI1NiJ9...","token_type":"Bearer","expires_in":3600,"scope":"legacy.migrated"}
```

## 7. Gotchas & takeaways

> A custom `grant_type` value should always use a URN or fully-qualified URI, never a short bare word — this avoids ever colliding with a future officially registered OAuth2 grant type; `urn:example:params:oauth:grant-type:legacy-token` follows the same convention RFC 8628 (device code) and RFC 8693 (token exchange) themselves use for their own extension grant type identifiers.

- The converter must return `null` (not throw) for any request whose `grant_type` it doesn't recognize — the token endpoint tries each registered converter in sequence, and a converter that throws on non-matching input breaks every *other* grant type's requests too.
- Client authentication (card 0012) happens before grant-specific processing regardless of which grant type is used — a custom grant doesn't bypass or need to reimplement that layer.
- Reuse the standard `OAuth2AccessTokenGenerator` (card 0019) rather than hand-rolling token construction — doing so keeps custom-grant tokens consistent in structure, signing, and persistence with every standard-grant token, which matters enormously for downstream resource servers that shouldn't need to special-case how a token was originally obtained.
- Document and register custom grant type URIs clearly for any external client that needs to use them — unlike standard grants, there's no universal client library support for a bespoke `grant_type` value, so client-side implementation is entirely bespoke too.
- Treat a custom grant as a deliberate, load-bearing extension of the system's trust model — because it bypasses the well-trodden standard flows, give its `AuthenticationProvider` the same security scrutiny (input validation, error handling, no information leakage on failure) as any other authentication entry point in the system.
