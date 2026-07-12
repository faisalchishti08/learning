---
card: spring-security
gi: 103
slug: validating-audience-issuer-claims
title: "Validating audience/issuer/claims"
---

## 1. What it is

`JwtDecoder` validates a fixed set of claims by default via `JwtValidators.createDefault()` — `exp` (not expired) and `nbf` (not used before its valid time) — but notably **not** `aud` (audience), because audience requirements vary per application and Spring Security cannot guess what value to expect. `JwtValidator`/`OAuth2TokenValidator<Jwt>` is the extension point for adding exactly this kind of custom check: a `DelegatingOAuth2TokenValidator` runs an ordered list of validators, and any application with more than one resource server sharing an issuer (a very common setup) needs to add an explicit audience check, or risk one resource server accepting a token that was actually issued for a *different* resource server.

```java
@Bean
public JwtDecoder jwtDecoder() {
    NimbusJwtDecoder decoder = NimbusJwtDecoder.withJwkSetUri("https://auth.example.com/.well-known/jwks.json").build();

    OAuth2TokenValidator<Jwt> defaults = JwtValidators.createDefaultWithIssuer("https://auth.example.com");
    OAuth2TokenValidator<Jwt> audience = jwt -> {
        if (jwt.getAudience().contains("orders-api")) return OAuth2TokenValidatorResult.success();
        return OAuth2TokenValidatorResult.failure(new OAuth2Error("invalid_token", "required audience is missing", null));
    };
    decoder.setJwtValidator(new DelegatingOAuth2TokenValidator<>(defaults, audience));
    return decoder;
}
```

## 2. Why & when

Card 0101 covered how a signature gets verified; this card covers what happens *after* a signature checks out, because a validly-signed token is not automatically an *appropriate* one. The audience gap is the sharpest example: imagine one authorization server issuing tokens for both an `orders-api` and a `billing-api` resource server — a token correctly signed by that shared issuer, intended only for `billing-api`, is still a perfectly valid JWT by signature alone. Without an explicit audience check, `orders-api` would happily accept it too, letting a token leaked or replayed from one service authenticate against a completely different one it was never meant to reach.

Reach for custom claim validation when:

- More than one resource server trusts the same issuer — audience validation is the single most important addition in this scenario, and its absence is a genuinely common, easy-to-miss vulnerability.
- The issuer embeds custom, application-specific claims that must meet some invariant before a token should be trusted (a `tenant_id` claim that must match this deployment's own tenant, for instance).
- Debugging a token that's rejected despite having a seemingly-valid signature — the failure almost always traces to one specific validator in the chain, and knowing the chain's order (and that `DelegatingOAuth2TokenValidator` runs every validator and aggregates failures) narrows the search immediately.
- Layering `iss` validation explicitly even when `issuer-uri` is already configured — `JwtValidators.createDefaultWithIssuer(...)` bakes this in, but a custom `JwtDecoder` built without it needs the check added back manually or the issuer claim goes unchecked.

## 3. Core concept

```
JwtValidators.createDefault():
    exp check   -- token not expired
    nbf check   -- token not used before its "not before" time
    (NO issuer, NO audience check by default)

JwtValidators.createDefaultWithIssuer(issuer):
    exp, nbf checks (as above)
    + iss check  -- jwt.getIssuer() must equal the configured issuer

DelegatingOAuth2TokenValidator<Jwt>(v1, v2, v3, ...):
    runs EVERY validator, even after one fails (so ALL problems can be reported together)
    aggregates failures into ONE OAuth2TokenValidatorResult
    ANY failure -> the whole validation fails

Custom validator (lambda or class implementing OAuth2TokenValidator<Jwt>):
    OAuth2TokenValidatorResult validate(Jwt token) {
        return CONDITION_MET ? OAuth2TokenValidatorResult.success()
                              : OAuth2TokenValidatorResult.failure(new OAuth2Error(...));
    }

TYPICAL production chain:
    createDefaultWithIssuer(trustedIssuer)  +  custom audience validator  +  any other app-specific checks
```

Every validator in the chain gets a chance to run; a token must pass all of them, not just the first one that happens to check.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a decoded jwt passing through a chain of validators for expiry not before issuer and audience each validator runs independently and any failure causes the overall validation to fail with an aggregated error">
  <rect x="20" y="80" width="140" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="90" y="100" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">decoded Jwt</text>
  <text x="90" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(signature OK)</text>

  <line x1="160" y1="105" x2="195" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#va103)"/>

  <rect x="200" y="20" width="100" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="250" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">exp check</text>

  <rect x="200" y="62" width="100" height="36" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="250" y="84" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">nbf check</text>

  <rect x="200" y="104" width="100" height="36" rx="6" fill="#6db33f" stroke="#6db33f" stroke-width="1.3"/>
  <text x="250" y="126" fill="#0d1117" font-size="9" text-anchor="middle" font-family="sans-serif">iss check</text>

  <rect x="200" y="146" width="100" height="36" rx="6" fill="#79c0ff" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="250" y="168" fill="#0d1117" font-size="9" text-anchor="middle" font-family="sans-serif">aud check (custom)</text>

  <line x1="300" y1="38" x2="345" y2="105" stroke="#6db33f" stroke-width="1.2" marker-end="url(#va103b)"/>
  <line x1="300" y1="80" x2="345" y2="105" stroke="#6db33f" stroke-width="1.2" marker-end="url(#va103b)"/>
  <line x1="300" y1="122" x2="345" y2="105" stroke="#6db33f" stroke-width="1.2" marker-end="url(#va103b)"/>
  <line x1="300" y1="164" x2="345" y2="105" stroke="#79c0ff" stroke-width="1.2" marker-end="url(#va103c)"/>

  <rect x="350" y="80" width="270" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="485" y="100" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">DelegatingOAuth2TokenValidator</text>
  <text x="485" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ALL must pass -&gt; success, else aggregated failure</text>

  <defs>
    <marker id="va103" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="va103b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="va103c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each validator answers a narrow question independently; the delegating validator only reports overall success once every one of them agrees.

## 5. Runnable example

The scenario: build a validator chain from scratch — issuer check, then audience check added on top — and demonstrate the exact vulnerability audience validation closes: a token correctly signed and correctly issued, but meant for a different resource server, being wrongly accepted without it.

### Level 1 — Basic

An issuer-only validator: signature (assumed already checked) plus one claim check.

```java
import java.util.*;

public class ClaimValidationLevel1 {
    record Jwt(String issuer, List<String> audience, Map<String, Object> claims) {}
    record ValidationResult(boolean valid, String errorDescription) {
        static ValidationResult success() { return new ValidationResult(true, null); }
        static ValidationResult failure(String description) { return new ValidationResult(false, description); }
    }

    interface TokenValidator { ValidationResult validate(Jwt jwt); }

    static TokenValidator issuerValidator(String expectedIssuer) {
        return jwt -> expectedIssuer.equals(jwt.issuer())
                ? ValidationResult.success()
                : ValidationResult.failure("iss mismatch: expected " + expectedIssuer + " but got " + jwt.issuer());
    }

    public static void main(String[] args) {
        TokenValidator validator = issuerValidator("https://auth.example.com");

        Jwt correctIssuer = new Jwt("https://auth.example.com", List.of("orders-api"), Map.of());
        Jwt wrongIssuer = new Jwt("https://attacker-controlled.example", List.of("orders-api"), Map.of());

        System.out.println("correct issuer: " + validator.validate(correctIssuer));
        System.out.println("wrong issuer: " + validator.validate(wrongIssuer));
    }
}
```

**How to run:** save as `ClaimValidationLevel1.java`, run `java ClaimValidationLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
correct issuer: ValidationResult[valid=true, errorDescription=null]
wrong issuer: ValidationResult[valid=false, errorDescription=iss mismatch: expected https://auth.example.com but got https://attacker-controlled.example]
```

`issuerValidator` is a minimal `OAuth2TokenValidator<Jwt>`-equivalent: one focused check, returning either success or a specific, actionable failure description — exactly the shape every validator in a real `DelegatingOAuth2TokenValidator` chain follows.

### Level 2 — Intermediate

Combine issuer and audience checks via a delegating validator that runs every check and aggregates failures.

```java
import java.util.*;

public class ClaimValidationLevel2 {
    record Jwt(String issuer, List<String> audience, Map<String, Object> claims) {}
    record ValidationResult(boolean valid, List<String> errors) {
        static ValidationResult success() { return new ValidationResult(true, List.of()); }
        static ValidationResult failure(String description) { return new ValidationResult(false, List.of(description)); }
    }

    interface TokenValidator { ValidationResult validate(Jwt jwt); }

    static TokenValidator issuerValidator(String expectedIssuer) {
        return jwt -> expectedIssuer.equals(jwt.issuer())
                ? ValidationResult.success()
                : ValidationResult.failure("iss mismatch: expected " + expectedIssuer);
    }

    static TokenValidator audienceValidator(String requiredAudience) {
        return jwt -> jwt.audience().contains(requiredAudience)
                ? ValidationResult.success()
                : ValidationResult.failure("required audience \"" + requiredAudience + "\" not present in " + jwt.audience());
    }

    // mirrors DelegatingOAuth2TokenValidator: run EVERY validator, aggregate ALL failures
    static ValidationResult validateAll(Jwt jwt, List<TokenValidator> validators) {
        List<String> allErrors = new ArrayList<>();
        for (TokenValidator v : validators) {
            ValidationResult result = v.validate(jwt);
            if (!result.valid()) allErrors.addAll(result.errors());
        }
        return allErrors.isEmpty() ? ValidationResult.success() : new ValidationResult(false, allErrors);
    }

    public static void main(String[] args) {
        List<TokenValidator> chain = List.of(
                issuerValidator("https://auth.example.com"),
                audienceValidator("orders-api"));

        Jwt validForOrders = new Jwt("https://auth.example.com", List.of("orders-api"), Map.of());
        Jwt validForBillingOnly = new Jwt("https://auth.example.com", List.of("billing-api"), Map.of());
        Jwt wrongEverything = new Jwt("https://attacker.example", List.of("billing-api"), Map.of());

        System.out.println("token for orders-api: " + validateAll(validForOrders, chain));
        System.out.println("token for billing-api only: " + validateAll(validForBillingOnly, chain));
        System.out.println("wrong issuer AND audience: " + validateAll(wrongEverything, chain));
    }
}
```

**How to run:** save as `ClaimValidationLevel2.java`, run `java ClaimValidationLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
token for orders-api: ValidationResult[valid=true, errors=[]]
token for billing-api only: ValidationResult[valid=false, errors=[required audience "orders-api" not present in [billing-api]]]
token for wrong issuer AND audience: ValidationResult[valid=false, errors=[iss mismatch: expected https://auth.example.com, required audience "orders-api" not present in [billing-api]]]
```

What changed: `validateAll` runs *every* validator regardless of earlier failures and collects *all* of their errors — the third case demonstrates this clearly: both the issuer check and the audience check fail, and both error messages appear together, rather than the chain stopping at the first problem, which would hide the second one from whoever is debugging the rejection.

### Level 3 — Advanced

Simulate the exact cross-service vulnerability audience validation prevents: a shared issuer serving tokens to two different resource servers, and a token meant for one being replayed against the other — first without an audience check (succeeds, wrongly), then with one added (correctly rejected).

```java
import java.util.*;

public class ClaimValidationLevel3 {
    record Jwt(String issuer, List<String> audience, String subject, Map<String, Object> claims) {}
    record ValidationResult(boolean valid, List<String> errors) {
        static ValidationResult success() { return new ValidationResult(true, List.of()); }
        static ValidationResult failure(String description) { return new ValidationResult(false, List.of(description)); }
    }

    interface TokenValidator { ValidationResult validate(Jwt jwt); }

    static TokenValidator issuerValidator(String expectedIssuer) {
        return jwt -> expectedIssuer.equals(jwt.issuer()) ? ValidationResult.success()
                : ValidationResult.failure("iss mismatch");
    }

    static TokenValidator audienceValidator(String requiredAudience) {
        return jwt -> jwt.audience().contains(requiredAudience) ? ValidationResult.success()
                : ValidationResult.failure("token was not issued for audience \"" + requiredAudience + "\"");
    }

    static ValidationResult validateAll(Jwt jwt, List<TokenValidator> validators) {
        List<String> errors = new ArrayList<>();
        for (TokenValidator v : validators) {
            ValidationResult r = v.validate(jwt);
            if (!r.valid()) errors.addAll(r.errors());
        }
        return errors.isEmpty() ? ValidationResult.success() : new ValidationResult(false, errors);
    }

    // simulates a resource server's own decoder configuration
    static ValidationResult resourceServerAccepts(Jwt jwt, String thisServersAudience, boolean enforceAudience) {
        List<TokenValidator> chain = new ArrayList<>();
        chain.add(issuerValidator("https://shared-auth.example.com"));
        if (enforceAudience) chain.add(audienceValidator(thisServersAudience));
        return validateAll(jwt, chain);
    }

    public static void main(String[] args) {
        // a token the shared authorization server issued SPECIFICALLY for billing-api, requested via client_credentials
        Jwt tokenForBilling = new Jwt("https://shared-auth.example.com", List.of("billing-api"),
                "service-account-billing-worker", Map.of());

        System.out.println("=== orders-api WITHOUT audience validation ===");
        ValidationResult withoutAudienceCheck = resourceServerAccepts(tokenForBilling, "orders-api", false);
        System.out.println("billing-only token accepted by orders-api: " + withoutAudienceCheck.valid()
                + (withoutAudienceCheck.valid() ? "  <-- WRONG: this token was never meant for orders-api!" : ""));

        System.out.println("=== orders-api WITH audience validation ===");
        ValidationResult withAudienceCheck = resourceServerAccepts(tokenForBilling, "orders-api", true);
        System.out.println("billing-only token accepted by orders-api: " + withAudienceCheck.valid()
                + (!withAudienceCheck.valid() ? "  <-- correctly rejected: " + withAudienceCheck.errors() : ""));

        // for contrast: billing-api itself, which SHOULD and DOES accept this token
        ValidationResult billingApiAccepts = resourceServerAccepts(tokenForBilling, "billing-api", true);
        System.out.println("same token accepted by billing-api (its intended audience): " + billingApiAccepts.valid());
    }
}
```

**How to run:** save as `ClaimValidationLevel3.java`, run `java ClaimValidationLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
=== orders-api WITHOUT audience validation ===
billing-only token accepted by orders-api: true  <-- WRONG: this token was never meant for orders-api!
=== orders-api WITH audience validation ===
billing-only token accepted by orders-api: false  <-- correctly rejected: [token was not issued for audience "orders-api"]
same token accepted by billing-api (its intended audience): true
```

What changed: `resourceServerAccepts` now takes an `enforceAudience` flag demonstrating both configurations side by side — the *same* validly-signed, validly-issued token is wrongly accepted by a resource server it was never intended for when audience validation is absent, and correctly rejected once it's added, while the resource server it *was* actually issued for continues to accept it either way. This is the exact vulnerability class audience validation closes: a token's validity (signature, issuer) says nothing about which specific resource server it's authorized to reach.

## 6. Walkthrough

Trace the vulnerable case (`withoutAudienceCheck`) and its fix side by side, as if `tokenForBilling` had genuinely leaked or been replayed from the billing service to the orders service.

**Step 1 — the token is legitimately issued, for billing only:**
```
POST /token HTTP/1.1
Host: shared-auth.example.com

grant_type=client_credentials&client_id=billing-worker&client_secret=***&scope=process:payments
```
```
HTTP/1.1 200 OK
{"access_token":"eyJhbGci...","aud":["billing-api"],"iss":"https://shared-auth.example.com"}
```
This corresponds to `tokenForBilling`'s construction: `audience=["billing-api"]`, correctly signed by the shared issuer.

**Step 2 — that token is presented to `orders-api` instead** (through misconfiguration, a compromised billing worker, or a deliberate replay attack):
```
GET /api/orders HTTP/1.1
Host: orders-api.internal
Authorization: Bearer eyJhbGci...
```

**Step 3a — WITHOUT audience validation.** `resourceServerAccepts(tokenForBilling, "orders-api", false)` builds a chain containing only `issuerValidator("https://shared-auth.example.com")`. That check passes — the token really was issued by the trusted shared issuer — and since no audience validator is in the chain at all, `validateAll` returns `success()`. The request is authenticated as `service-account-billing-worker` against `orders-api`, an endpoint it was never authorized to reach.

**Step 3b — WITH audience validation.** `resourceServerAccepts(tokenForBilling, "orders-api", true)` adds `audienceValidator("orders-api")` to the chain. `issuerValidator` still passes, but `audienceValidator("orders-api").validate(tokenForBilling)` checks `jwt.audience().contains("orders-api")` — `audience` is `["billing-api"]`, so this returns a failure, and `validateAll` aggregates it into an overall rejection.

**Step 4 — the correctly-configured `orders-api`'s response:**
```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token", error_description="token was not issued for audience \"orders-api\""
```

**Step 5 — for contrast, the same token presented to `billing-api` itself:** `resourceServerAccepts(tokenForBilling, "billing-api", true)` — `audienceValidator("billing-api").validate(tokenForBilling)` checks `audience.contains("billing-api")`, which is `true`, so this leg of the chain passes, and (assuming the issuer check also passes, which it does) the token is correctly accepted exactly where it was meant to be used.

```
same signed token, same issuer, TWO different resource servers:

  orders-api  (no audience check): ACCEPTS  <-- security gap
  orders-api  (audience check)   : REJECTS  <-- correct
  billing-api (audience check)   : ACCEPTS  <-- correct, this IS its intended audience
```

## 7. Gotchas & takeaways

> **Gotcha:** `JwtValidators.createDefault()` (and even `createDefaultWithIssuer(...)`) never validates audience — this is a deliberate design choice (Spring Security cannot guess what audience value your application expects), not an oversight, but it means every application with more than one resource server sharing an issuer must add an explicit audience validator itself, or silently inherit exactly the cross-service token acceptance shown above.

- `JwtDecoder`'s default validation covers `exp` and `nbf`; issuer validation is added by `createDefaultWithIssuer`, but audience validation is never automatic and must always be added explicitly by application code.
- `DelegatingOAuth2TokenValidator` runs every configured validator and aggregates all failures — a token can fail multiple checks at once, and a good error message should reflect that rather than reporting only the first problem encountered.
- Audience validation exists specifically to prevent a token correctly issued by a trusted shared issuer, but intended for a *different* resource server, from being accepted somewhere it was never authorized to reach.
- A validator only needs to implement one method (`validate(Jwt) -> OAuth2TokenValidatorResult`) and can check anything expressible from the token's claims — custom tenant checks, required scopes, or any other application-specific invariant follow the exact same pattern as the built-in checks.
- Any deployment where multiple resource servers trust the same authorization server should treat an explicit audience check as a required addition, not an optional hardening step.
