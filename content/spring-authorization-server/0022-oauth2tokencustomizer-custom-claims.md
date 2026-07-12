---
card: spring-authorization-server
gi: 22
slug: oauth2tokencustomizer-custom-claims
title: "OAuth2TokenCustomizer (custom claims)"
---

## 1. What it is

`OAuth2TokenCustomizer<T extends OAuth2TokenContext>` is the general-purpose customization interface behind the `JwtGenerator` customizer seen in card 0019 — it's actually the same mechanism, generalized. It's a single-method functional interface, `void customize(T context)`, and Spring Authorization Server wires it into token generation at three distinct points: `OAuth2TokenCustomizer<JwtEncodingContext>` for access tokens and ID tokens formatted as JWTs, and `OAuth2TokenCustomizer<OAuth2TokenClaimsContext>` for opaque access tokens (whose claims still exist internally, for introspection responses, even though the token string itself carries none of them).

## 2. Why & when

Card 0019 showed customizing JWT access token claims. This card is about the fuller picture: the *same* customization pattern applies to opaque tokens (via `OAuth2TokenClaimsContext`, which backs what `/oauth2/introspect` returns) and to OIDC ID tokens specifically — and knowing which context type you're customizing, and when it runs, is what determines whether your custom logic actually takes effect where you expect it to.

Reach for a dedicated `OAuth2TokenCustomizer` bean when:

- Adding claims that must appear in introspection responses for opaque tokens, not just in JWT payloads — this requires customizing `OAuth2TokenClaimsContext`, a different context type than the JWT one.
- Adding claims to the OIDC ID token specifically (e.g. a custom `tenant` claim visible to the client itself, as opposed to the access token, which the resource server sees) — the context's `getTokenType()` distinguishes `ID_TOKEN` from `ACCESS_TOKEN` so one customizer can branch on which token it's currently building.
- Centralizing all custom-claim logic in one bean rather than scattering `set*Customizer` calls across multiple manually-constructed generators.

## 3. Core concept

Picture a form-processing office with multiple different form types moving through it (an access-token form, an ID-token form, an opaque-token summary form) — `OAuth2TokenCustomizer` is a rubber stamp process that gets applied to whichever form passes through, and it can check "what kind of form is this, and for whom" before deciding what to stamp on it. The same stamp station handles every form type; it just checks the form's `getTokenType()` and `getPrincipal()` before acting.

```java
public interface OAuth2TokenCustomizer<T extends OAuth2TokenContext> {
    void customize(T context);
}

@Bean
public OAuth2TokenCustomizer<JwtEncodingContext> jwtTokenCustomizer() {
    return context -> {
        if (context.getTokenType().equals(OAuth2TokenType.ACCESS_TOKEN)) {
            context.getClaims().claim("roles", rolesFor(context.getPrincipal().getName()));
        } else if ("id_token".equals(context.getTokenType().getValue())) {
            context.getClaims().claim("tenant", tenantFor(context.getPrincipal().getName()));
        }
    };
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One customizer interface branches by token type across access tokens, ID tokens, and opaque token claims">
  <rect x="240" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OAuth2TokenCustomizer</text>

  <rect x="20" y="120" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JwtEncodingContext</text>
  <text x="110" y="163" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">access token or ID token</text>

  <rect x="230" y="120" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OAuth2TokenClaimsContext</text>
  <text x="320" y="163" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">opaque token (for introspection)</text>

  <rect x="440" y="120" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="530" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">getTokenType()</text>
  <text x="530" y="163" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">branch per call</text>

  <line x1="280" y1="70" x2="110" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="330" y1="70" x2="320" y2="118" stroke="#3fb950" stroke-width="2"/>
  <line x1="370" y1="70" x2="530" y2="118" stroke="#3fb950" stroke-width="2"/>
</svg>

The same interface, applied across three distinct context flavors, each carrying different claim destinations.

## 5. Runnable example

The scenario: task-tracker needs a `roles` claim on access tokens, a `tenant` claim on ID tokens, and — for a payments client using opaque tokens — the same `roles` data visible via introspection, so all three destinations must be handled correctly.

### Level 1 — Basic

```java
// TokenCustomizerDemo.java
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;
import org.springframework.security.oauth2.core.OAuth2TokenType;

public class TokenCustomizerDemo {

    static OAuth2TokenCustomizer<JwtEncodingContext> accessTokenRolesCustomizer() {
        return context -> {
            if (OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
                context.getClaims().claim("roles", rolesFor(context.getPrincipal().getName()));
            }
        };
    }

    static java.util.List<String> rolesFor(String principal) {
        return "alice".equals(principal) ? java.util.List.of("ADMIN") : java.util.List.of("USER");
    }

    public static void main(String[] args) {
        System.out.println("Customizer built. Roles for alice: " + rolesFor("alice"));
    }
}
```

**How to run:** run inside a project with `spring-security-oauth2-authorization-server` via `java TokenCustomizerDemo.java`. Expected output:

```
Customizer built. Roles for alice: [ADMIN]
```

### Level 2 — Intermediate

The same bean now also handles ID tokens, adding a `tenant` claim there — and correctly does *not* leak that claim into the access token, since access tokens and ID tokens have different intended audiences (the resource server versus the client application itself).

```java
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;
import org.springframework.security.oauth2.core.OAuth2TokenType;
import org.springframework.security.oauth2.core.oidc.endpoint.OidcParameterNames;

public class TokenCustomizerDemo {

    static OAuth2TokenCustomizer<JwtEncodingContext> combinedCustomizer() {
        return context -> {
            String principal = context.getPrincipal().getName();
            if (OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
                context.getClaims().claim("roles", rolesFor(principal));
            } else if ("id_token".equals(context.getTokenType().getValue())) {
                context.getClaims().claim("tenant", tenantFor(principal));
            }
        };
    }

    static java.util.List<String> rolesFor(String principal) {
        return "alice".equals(principal) ? java.util.List.of("ADMIN") : java.util.List.of("USER");
    }

    static String tenantFor(String principal) {
        return "acme-corp";
    }

    public static void main(String[] args) {
        System.out.println("Access token would carry: roles=" + rolesFor("alice"));
        System.out.println("ID token would carry: tenant=" + tenantFor("alice") + " (no roles claim here)");
    }
}
```

**How to run:** same as Level 1. Expected output:

```
Access token would carry: roles=[ADMIN]
ID token would carry: tenant=acme-corp (no roles claim here)
```

What changed: one bean now branches correctly across two token types sharing the same context class (`JwtEncodingContext`) — the `getTokenType()` check is what keeps `roles` off the ID token and `tenant` off the access token, matching the principle that each token type should only carry claims relevant to its actual audience.

### Level 3 — Advanced

The payments client uses opaque access tokens (card 0020), so its "claims" only ever surface through introspection — this requires a *separate* customizer bean typed to `OAuth2TokenClaimsContext`, since opaque tokens never go through `JwtEncodingContext` at all.

```java
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenClaimsContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;
import org.springframework.security.oauth2.core.OAuth2TokenType;

public class TokenCustomizerDemo {

    static OAuth2TokenCustomizer<OAuth2TokenClaimsContext> opaqueTokenClaimsCustomizer() {
        return context -> {
            if (OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
                String principal = context.getAuthorization().getPrincipalName();
                context.getClaims().claim("roles", rolesFor(principal));
            }
        };
    }

    static java.util.List<String> rolesFor(String principal) {
        return "alice".equals(principal) ? java.util.List.of("ADMIN") : java.util.List.of("USER");
    }

    public static void main(String[] args) {
        // OAuth2TokenClaimsContext.getPrincipal() isn't available pre-issuance the same way;
        // claims here populate the internal OAuth2Authorization used later by introspection.
        System.out.println("Opaque token introspection response would include: roles="
                + rolesFor("alice"));
    }
}
```

**How to run:** same as Level 1; both customizer beans (Level 2's `JwtEncodingContext` one and this `OAuth2TokenClaimsContext` one) are registered together in a real application, and Spring Authorization Server invokes whichever matches the token being generated. Expected output:

```
Opaque token introspection response would include: roles=[ADMIN]
```

What changed and why it's production-flavored: without this second, separately-typed customizer, the payments client's opaque tokens would carry no custom claims at all — the JWT customizer from Level 2 simply never runs for opaque tokens, since they're generated through an entirely different code path (`OAuth2AccessTokenGenerator`, not `JwtGenerator`). Registering both customizer types is what makes custom claims consistently available regardless of which token format a given client uses.

## 6. Walkthrough

Tracing how both customizers get invoked for two different clients requesting tokens around the same time, in execution order:

1. Task-tracker (JWT-format client) redeems an authorization code; `DelegatingOAuth2TokenGenerator` (card 0019) reaches `JwtGenerator`, which builds a `JwtEncodingContext` for the access token and invokes the registered `OAuth2TokenCustomizer<JwtEncodingContext>` bean — the Level 2 branch fires, adding `roles`.
2. Because task-tracker is also an OIDC client, the same request also triggers ID token generation — a **second**, separate `JwtEncodingContext` is built with `getTokenType()` reporting `id_token`, and the same customizer bean runs again, this time taking the `tenant` branch instead.
3. Meanwhile, the payments client (opaque-format client) makes a `client_credentials` request; `DelegatingOAuth2TokenGenerator` reaches `OAuth2AccessTokenGenerator` instead, which builds an `OAuth2TokenClaimsContext` and invokes the registered `OAuth2TokenCustomizer<OAuth2TokenClaimsContext>` bean from Level 3 — adding `roles` to the claims that back this opaque token's `OAuth2Authorization` record.
4. Later, when the payments resource server calls `POST /oauth2/introspect` with that opaque token, the introspection endpoint reads the claims stored on the matching `OAuth2Authorization` (the very claims the Level 3 customizer added) and returns them in the JSON response: `{"active": true, "sub": "alice", "roles": ["ADMIN"], "scope": "payments.charge"}`.
5. Task-tracker's resource server, in contrast, decodes its JWT access token locally and finds `roles: ["ADMIN"]` directly inside the token payload — same underlying data, delivered through two structurally different mechanisms depending on the token format each client was configured for (card 0020).

```
task-tracker (JWT):      JwtEncodingContext(access_token) -> customizer -> roles claim in JWT payload
                          JwtEncodingContext(id_token)     -> customizer -> tenant claim in ID token payload

payments-service (opaque): OAuth2TokenClaimsContext -> customizer -> roles claim stored on OAuth2Authorization
                                                                    -> surfaced later via /oauth2/introspect
```

## 7. Gotchas & takeaways

> A single `OAuth2TokenCustomizer<JwtEncodingContext>` bean handles *both* access tokens and ID tokens — forgetting to check `getTokenType()` before adding a claim means it silently ends up on both, which for a sensitive internal claim (like fine-grained permissions) can leak information to the client application via the ID token that was only ever meant for the resource server via the access token.

- `OAuth2TokenCustomizer<JwtEncodingContext>` and `OAuth2TokenCustomizer<OAuth2TokenClaimsContext>` are two **separate** bean types — registering only one leaves the other token format's claims uncustomized; check both are wired if the deployment mixes JWT and opaque clients.
- ID token claims are visible to the client application itself (it's the audience) — never put resource-server-only, sensitive authorization data there; that belongs on the access token instead.
- `OAuth2TokenClaimsContext` doesn't offer `getPrincipal()` the same way `JwtEncodingContext` does — use `context.getAuthorization().getPrincipalName()` to get the acting user or service instead.
- Because introspection responses are only as rich as what was stored via this customizer at issuance time, changing a user's roles after a token was issued has no effect on that token's already-cached claims until it's reissued or refreshed.
- Keep customizer logic fast and side-effect-light — it runs synchronously on the hot path of every token issuance, and a slow external lookup here (e.g. an uncached database call) becomes a slow token endpoint for every client.
