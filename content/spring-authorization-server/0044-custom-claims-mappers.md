---
card: spring-authorization-server
gi: 44
slug: custom-claims-mappers
title: "Custom claims & mappers"
---

## 1. What it is

Custom claims and mappers is the general mechanism for putting application-specific data into issued tokens — beyond the standard claims (`sub`, `scope`, `exp`, and similar) that the library adds automatically. It's implemented via the `OAuth2TokenCustomizer<JwtEncodingContext>` bean (card 0022 introduced this for a single claim; this card generalizes it across access tokens, ID tokens, and multiple claim sources at once).

## 2. Why & when

A token's standard claims tell a resource server *who* is calling and *what* they're allowed to do in OAuth2 terms, but real applications frequently need more — a tenant ID for multi-tenant systems, a user's role or department for authorization decisions, an internal employee ID distinct from the login identifier. Rather than having every resource server make a separate database call to look this up on every request, embedding it directly in the token (when it's not overly sensitive and changes infrequently) lets resource servers make authorization decisions from the token alone.

Reach for custom claims when:

- A resource server needs data about the user or client that isn't naturally part of the OAuth2/OIDC standard claim set (tenant ID, department, feature flags, internal role names).
- Different claims are needed on different token types — an access token consumed by APIs might need different information than an ID token consumed by the client's UI.
- Deciding what belongs in a token versus what belongs behind a UserInfo/API lookup (card 0033) — data needed on nearly every request and safe to be moderately public belongs in the token; sensitive or frequently-changing data belongs behind a live lookup.

## 3. Core concept

Think of the standard OAuth2/OIDC claims as the printed, fixed fields on a passport — name, passport number, nationality, expiry date — the same fields on every passport, everywhere. Custom claims are like a country adding its own supplementary visa stamps and endorsement pages: still part of the same document, still checked at the border, but specific to that country's own needs and not part of the universal passport standard. A `JwtEncodingContext` gives the customizer access to everything about the request — who's authenticating, which client, what grant type — the same way a passport office has access to your full application file when deciding what extra endorsements to stamp.

```java
context.getClaims().claim("tenant_id", resolveTenantFor(context.getPrincipal()));
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Token customizer inspects the encoding context and adds application-specific claims before the token is signed">
  <rect x="20" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JwtEncodingContext</text>
  <text x="100" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">principal, client, type</text>

  <rect x="250" y="80" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OAuth2TokenCustomizer</text>
  <text x="330" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">add claims to builder</text>

  <rect x="480" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Signed JWT</text>
  <text x="550" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">standard + custom claims</text>

  <line x1="180" y1="110" x2="245" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="410" y1="110" x2="475" y2="110" stroke="#3fb950" stroke-width="1.5"/>
</svg>

The customizer runs once per token being built, with full context about which kind of token (access vs. ID) and which grant produced it.

## 5. Runnable example

The scenario: adding a tenant ID claim to access tokens for a multi-tenant SaaS, growing to vary claims by token type (access token vs. ID token get different data), and finally to make claim resolution resilient to a failing downstream lookup so a database blip doesn't break every token issuance.

### Level 1 — Basic

```java
// TenantClaimCustomizer.java
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;

import java.util.function.Function;

public class TenantClaimCustomizer implements OAuth2TokenCustomizer<JwtEncodingContext> {

    private final Function<String, String> tenantLookup; // username -> tenantId

    public TenantClaimCustomizer(Function<String, String> tenantLookup) {
        this.tenantLookup = tenantLookup;
    }

    @Override
    public void customize(JwtEncodingContext context) {
        String username = context.getPrincipal().getName();
        String tenantId = tenantLookup.apply(username);
        context.getClaims().claim("tenant_id", tenantId);
    }
}
```

**How to run:** register as a `@Bean` implementing `OAuth2TokenCustomizer<JwtEncodingContext>` with a real `Function` backed by a `UserRepository` lookup, then complete an authorization code flow. Decode the resulting access token (e.g. at jwt.io, for a non-production token) — expect `tenant_id` present as a top-level claim.

### Level 2 — Intermediate

Access tokens and ID tokens serve different audiences (resource servers versus the client's own UI) — the customizer checks `context.getTokenType()` to add different claims to each, avoiding leaking API-internal data (like a tenant's internal database shard ID) into the ID token a browser can freely decode and display.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2TokenType;
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;

public class TypeAwareClaimCustomizer implements OAuth2TokenCustomizer<JwtEncodingContext> {

    @Override
    public void customize(JwtEncodingContext context) {
        String username = context.getPrincipal().getName();
        String tenantId = resolveTenant(username);

        if (OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
            context.getClaims().claim("tenant_id", tenantId);
            context.getClaims().claim("tenant_shard", resolveShard(tenantId)); // internal routing detail
        } else if ("id_token".equals(context.getTokenType().getValue())) {
            context.getClaims().claim("tenant_name", resolveDisplayName(tenantId)); // user-facing only
        }
    }

    private String resolveTenant(String username) { return "tenant-42"; }
    private String resolveShard(String tenantId) { return "shard-3"; }
    private String resolveDisplayName(String tenantId) { return "Acme Corp"; }
}
```

**How to run:** complete an OIDC login (`scope=openid`) and inspect both tokens. Expected: the access token contains `tenant_id` and `tenant_shard`; the ID token contains only `tenant_name` — the internal shard routing detail never appears in a token the browser can inspect.

What changed: claims are now scoped to their appropriate audience, following the principle that internal routing/infrastructure details belong only in tokens resource servers see, never in tokens exposed to client-side JavaScript.

### Level 3 — Advanced

A tenant lookup backed by a database call happening synchronously during every single token issuance is a new failure point — if that lookup times out or the database has a blip, production shouldn't fail the entire login; it should degrade gracefully (or fail the specific request clearly) rather than letting one flaky dependency break authentication server-wide.

```java
import org.springframework.security.oauth2.server.authorization.OAuth2TokenType;
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;

import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class ResilientTenantClaimCustomizer implements OAuth2TokenCustomizer<JwtEncodingContext> {

    @Override
    public void customize(JwtEncodingContext context) {
        if (!OAuth2TokenType.ACCESS_TOKEN.equals(context.getTokenType())) {
            return;
        }
        String username = context.getPrincipal().getName();
        try {
            String tenantId = CompletableFuture.supplyAsync(() -> lookupTenantSlow(username))
                    .get(500, TimeUnit.MILLISECONDS);
            context.getClaims().claim("tenant_id", tenantId);
        } catch (TimeoutException | InterruptedException | java.util.concurrent.ExecutionException e) {
            // Fail loudly rather than issuing a token silently missing tenant scoping —
            // a resource server that trusts tenant_id for isolation must never receive
            // a token where that claim was silently dropped due to an infrastructure hiccup.
            throw new IllegalStateException("Unable to resolve tenant for token issuance", e);
        }
    }

    private String lookupTenantSlow(String username) {
        return "tenant-42"; // stands in for a real, possibly slow, database call
    }
}
```

**How to run:** simulate a slow lookup (e.g. `Thread.sleep(1000)` inside `lookupTenantSlow`) and attempt a token issuance. Expected behavior: the customizer times out at 500ms and throws, which the token endpoint surfaces as a `500`-class failure rather than silently issuing a token with no `tenant_id` — a resource server relying on that claim for tenant isolation must never see a token where it's simply absent due to a timing issue.

What changed and why it's production-flavored: this trades "always issue *a* token, even if wrong" for "fail the specific request clearly when a required claim can't be resolved" — the right trade-off whenever a downstream system uses that claim for a security boundary (tenant isolation) rather than a purely cosmetic display value.

## 6. Walkthrough

Tracing claim customization during a token issuance, in execution order:

1. A client completes the authorization code exchange (card 0027), and the token endpoint begins building the access token (and, for an OIDC request, the ID token too).
2. For each token being built, the endpoint constructs a `JwtEncodingContext` carrying the authenticated principal, the requesting client, the grant type, and the token type currently being produced.
3. The registered `OAuth2TokenCustomizer` bean's `customize(context)` method runs — `ResilientTenantClaimCustomizer` (Level 3) first checks `context.getTokenType()` to decide whether this invocation is for the access token (where it should act) or the ID token (where it returns immediately, doing nothing).
4. For an access token, it kicks off a bounded, time-limited tenant lookup; on success, it adds `tenant_id` to `context.getClaims()` — a mutable builder the library uses to assemble the final claim set.
5. If the lookup exceeds its timeout, the customizer throws, aborting this token's issuance entirely rather than producing a token silently missing a claim a resource server will later trust for tenant isolation.
6. Assuming success, the library finishes assembling all claims (standard plus custom), signs the JWT (card 0021), and the token endpoint returns it in the normal `200 OK` response (card 0027).
7. A resource server later receiving this token decodes it and reads `tenant_id` directly from the claims — no additional database round-trip needed for that specific piece of authorization context.

```
Token endpoint building access token
   |
build JwtEncodingContext (principal, client, grant, tokenType=ACCESS_TOKEN)
   |
customizer.customize(context)
   |    tokenType == ACCESS_TOKEN? --no (it's ID token)--> return, no-op
   |    yes
   |    lookup tenant (bounded to 500ms) --timeout--> throw, abort issuance
   |    success
   |    claims.claim("tenant_id", ...)
   |
sign JWT with full claim set -> 200 OK {access_token: "...tenant_id embedded..."}
```

## 7. Gotchas & takeaways

> A token customizer that silently swallows a lookup failure and just omits the claim is more dangerous than one that fails loudly — a resource server that trusts `tenant_id` for data isolation and receives a token where that claim is simply missing might fall back to some default or unscoped behavior, effectively bypassing tenant isolation rather than obviously failing.

- Only one `OAuth2TokenCustomizer<JwtEncodingContext>` bean is honored per token type context — if multiple customization concerns exist (tenant claims, role claims, feature flags), combine them inside a single customizer implementation, or explicitly chain multiple `Consumer`-style helpers within it, rather than registering several competing beans.
- Distinguish claims meant for resource servers (access token) from claims meant for the client's own UI (ID token) — Level 2's type check exists precisely because these two tokens have different audiences and different sensitivity tolerances.
- Keep customizer logic fast and bounded (Level 3) — it runs synchronously on every single token issuance, including every refresh (card 0040); a slow customizer directly slows down every login and every silent refresh across the whole system.
- Custom claims increase token size — for a resource-constrained client (mobile, embedded device) or a system issuing very large numbers of tokens, weigh whether a claim genuinely needs to be embedded versus fetched on demand via UserInfo (card 0033) or a dedicated API call.
- If a downstream resource server reports "claim X is missing," check first whether the customizer bean is even being picked up (a common cause is defining it as a plain `@Component` instead of exposing it correctly as the specific `OAuth2TokenCustomizer<JwtEncodingContext>` bean type the token generator looks for) before assuming the lookup logic itself is broken.
