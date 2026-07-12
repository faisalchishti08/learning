---
card: spring-security
gi: 105
slug: multi-tenancy-multiple-issuers
title: "Multi-tenancy (multiple issuers)"
---

## 1. What it is

Every resource server example so far has trusted exactly one issuer, configured via a single `issuer-uri`. A multi-tenant resource server — one that must accept tokens from *several* different, independent authorization servers (one per customer organization, for instance, each running its own Okta or Azure AD tenant) — needs a decoder that can resolve *which* issuer's keys to use *per request*, based on the incoming token's own `iss` claim, before any signature verification can even begin. `JwtIssuerAuthenticationManagerResolver` is Spring Security's built-in component for exactly this: given a set of trusted issuer URIs, it inspects each incoming token's unverified `iss` claim, looks up (and caches) the correct per-issuer `JwtDecoder`/`AuthenticationManager` pair, and only then proceeds with normal validation against that specific issuer's keys.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    JwtIssuerAuthenticationManagerResolver resolver = JwtIssuerAuthenticationManagerResolver.fromTrustedIssuers(
            "https://tenant-a.okta.com/oauth2/default",
            "https://tenant-b.okta.com/oauth2/default");

    http.oauth2ResourceServer(oauth2 -> oauth2.authenticationManagerResolver(resolver));
    return http.build();
}
```

## 2. Why & when

A single-issuer resource server can configure one `JwtDecoder` at startup because it knows, in advance, which authorization server it trusts — a fixed `issuer-uri` and a fixed JWK Set. A genuinely multi-tenant SaaS application breaks that assumption: tenant A's users authenticate against tenant A's own identity provider, tenant B's against tenant B's, and a single incoming request to the shared API could carry a token from either — the resource server cannot know in advance which JWK Set to fetch keys from until it has at least peeked at the token's claimed issuer.

Reach for `JwtIssuerAuthenticationManagerResolver` when:

- Building a resource server for a B2B SaaS product where each customer organization brings its own identity provider (a common enterprise requirement, sometimes called "bring your own IdP").
- Migrating between authorization servers — briefly trusting both an old and a new issuer during a cutover window, so tokens issued by either continue to work until the migration completes.
- A single logical service is deployed across regions, each with its own regional authorization server, but the resource server code itself is shared.
- You need per-tenant customization beyond just the signing keys — since the resolver returns a full `AuthenticationManager` per issuer, not just a `JwtDecoder`, different tenants can even have entirely different validation rules (a stricter audience check for a security-sensitive tenant, for instance).

## 3. Core concept

```
JwtIssuerAuthenticationManagerResolver.fromTrustedIssuers(issuer1, issuer2, ...):

  incoming request:
    Authorization: Bearer <token whose UNVERIFIED "iss" claim is "https://tenant-b.okta.com/oauth2/default">

  1. PEEK at the token's iss claim -- WITHOUT verifying the signature yet (can't -- don't know which key to use!)
  2. is this iss in the trusted set?
       NO  -> reject immediately: 401, untrusted issuer -- NEVER attempt to fetch keys from an unlisted issuer
       YES -> proceed
  3. look up (or lazily build + cache) the AuthenticationManager for THIS SPECIFIC issuer
       -- each one wraps its OWN JwtDecoder, built from ITS OWN issuer's JWK Set
  4. delegate to that issuer-specific AuthenticationManager for the REST of validation
       (signature via ITS keys, exp/nbf/iss/aud checks, authority mapping -- everything from cards 0101-0104)

CRITICAL: the trusted-issuer allowlist is checked FIRST, against the raw claim, before ANY
          cryptographic work happens -- an untrusted issuer is rejected without ever making
          a network call to fetch keys from wherever it claims to be.
```

The two-phase design (untrusted allowlist check first, full per-issuer validation second) is what prevents a malicious token from claiming an arbitrary `iss` and tricking the resource server into fetching keys from an attacker-controlled URL.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a request with a jwt the issuer resolver peeks at the unverified iss claim checks it against a trusted allowlist and if trusted delegates to a per issuer authentication manager cached per issuer that performs full validation using that issuers own keys if not trusted the request is rejected immediately without any key fetch">
  <rect x="20" y="90" width="160" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="100" y="110" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">incoming JWT</text>
  <text x="100" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">iss="tenant-b..." (unverified)</text>

  <line x1="180" y1="115" x2="220" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#mt105)"/>

  <rect x="225" y="90" width="180" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.4"/>
  <text x="315" y="110" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">trusted issuer allowlist?</text>
  <text x="315" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">checked BEFORE any key fetch</text>

  <line x1="315" y1="140" x2="180" y2="185" stroke="#f85149" stroke-width="1.5" marker-end="url(#mt105b)"/>
  <text x="220" y="175" fill="#f85149" font-size="8.5" font-family="sans-serif">NOT trusted</text>

  <rect x="40" y="188" width="180" height="40" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.3"/>
  <text x="130" y="212" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">401 -- rejected immediately</text>

  <line x1="405" y1="115" x2="450" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#mt105c)"/>
  <text x="425" y="107" fill="#6db33f" font-size="8" font-family="sans-serif">trusted</text>

  <rect x="455" y="60" width="185" height="110" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="547" y="82" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">per-issuer AuthenticationManager</text>
  <text x="547" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">cached per iss value</text>
  <text x="547" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">own JwtDecoder, own JWK Set</text>
  <text x="547" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">full validation (cards 0101-0104)</text>
  <text x="547" y="154" fill="#3fb950" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; JwtAuthenticationToken</text>

  <defs>
    <marker id="mt105" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="mt105b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="mt105c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The allowlist check happens before any cryptographic work — an untrusted `iss` never triggers a key fetch at all.

## 5. Runnable example

The scenario: build a from-scratch issuer resolver that routes requests to the right per-issuer decoder, growing from a single trusted issuer into multiple, then into lazy per-issuer manager caching, and finally into rejecting an untrusted issuer *before* any key-fetching work would occur.

### Level 1 — Basic

Two trusted issuers, each with its own decoder; route by the token's claimed `iss`.

```java
import java.util.*;

public class MultiTenantLevel1 {
    record Jwt(String issuer, String subject) {}
    record AuthenticationResult(String issuer, String subject) {}

    static class PerIssuerDecoder {
        private final String issuer;
        PerIssuerDecoder(String issuer) { this.issuer = issuer; }
        AuthenticationResult decode(Jwt jwt) {
            if (!issuer.equals(jwt.issuer())) throw new IllegalStateException("iss mismatch inside per-issuer decoder");
            return new AuthenticationResult(jwt.issuer(), jwt.subject());
        }
    }

    static class IssuerResolver {
        private final Map<String, PerIssuerDecoder> decodersByIssuer = new HashMap<>();
        void trust(String issuer) { decodersByIssuer.put(issuer, new PerIssuerDecoder(issuer)); }

        AuthenticationResult authenticate(Jwt jwt) {
            PerIssuerDecoder decoder = decodersByIssuer.get(jwt.issuer());
            if (decoder == null) throw new IllegalStateException("untrusted issuer: " + jwt.issuer());
            return decoder.decode(jwt);
        }
    }

    public static void main(String[] args) {
        IssuerResolver resolver = new IssuerResolver();
        resolver.trust("https://tenant-a.okta.com/oauth2/default");
        resolver.trust("https://tenant-b.okta.com/oauth2/default");

        Jwt fromTenantA = new Jwt("https://tenant-a.okta.com/oauth2/default", "alice");
        Jwt fromTenantB = new Jwt("https://tenant-b.okta.com/oauth2/default", "bob");

        System.out.println(resolver.authenticate(fromTenantA));
        System.out.println(resolver.authenticate(fromTenantB));
    }
}
```

**How to run:** save as `MultiTenantLevel1.java`, run `java MultiTenantLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
AuthenticationResult[issuer=https://tenant-a.okta.com/oauth2/default, subject=alice]
AuthenticationResult[issuer=https://tenant-b.okta.com/oauth2/default, subject=bob]
```

`IssuerResolver.authenticate` picks the right `PerIssuerDecoder` based on the token's own `issuer` field, mirroring `JwtIssuerAuthenticationManagerResolver`'s core job: route each request to the correct issuer-specific validation logic, rather than assuming a single fixed issuer for the whole application.

### Level 2 — Intermediate

Make per-issuer manager construction lazy and cached — building a decoder for an issuer only the first time it's actually needed, mirroring how key material shouldn't be fetched for a tenant that has never sent a request.

```java
import java.util.*;
import java.util.function.*;

public class MultiTenantLevel2 {
    record Jwt(String issuer, String subject) {}
    record AuthenticationResult(String issuer, String subject) {}

    static class PerIssuerDecoder {
        private final String issuer;
        PerIssuerDecoder(String issuer) {
            this.issuer = issuer;
            System.out.println("BUILDING decoder (fetching JWK Set) for issuer: " + issuer);
        }
        AuthenticationResult decode(Jwt jwt) { return new AuthenticationResult(jwt.issuer(), jwt.subject()); }
    }

    static class IssuerResolver {
        private final Set<String> trustedIssuers;
        private final Map<String, PerIssuerDecoder> cache = new HashMap<>(); // built LAZILY, per issuer

        IssuerResolver(Set<String> trustedIssuers) { this.trustedIssuers = trustedIssuers; }

        AuthenticationResult authenticate(Jwt jwt) {
            if (!trustedIssuers.contains(jwt.issuer())) {
                throw new IllegalStateException("untrusted issuer: " + jwt.issuer());
            }
            // computeIfAbsent -- build the decoder ONLY on first use for this issuer, then reuse it
            PerIssuerDecoder decoder = cache.computeIfAbsent(jwt.issuer(), PerIssuerDecoder::new);
            return decoder.decode(jwt);
        }
    }

    public static void main(String[] args) {
        IssuerResolver resolver = new IssuerResolver(Set.of(
                "https://tenant-a.okta.com/oauth2/default",
                "https://tenant-b.okta.com/oauth2/default"));

        System.out.println("--- first request from tenant A ---");
        resolver.authenticate(new Jwt("https://tenant-a.okta.com/oauth2/default", "alice"));

        System.out.println("--- second request from tenant A (should reuse cached decoder) ---");
        resolver.authenticate(new Jwt("https://tenant-a.okta.com/oauth2/default", "alice2"));

        System.out.println("--- first request from tenant B ---");
        resolver.authenticate(new Jwt("https://tenant-b.okta.com/oauth2/default", "bob"));
    }
}
```

**How to run:** save as `MultiTenantLevel2.java`, run `java MultiTenantLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
--- first request from tenant A ---
BUILDING decoder (fetching JWK Set) for issuer: https://tenant-a.okta.com/oauth2/default
--- second request from tenant A (should reuse cached decoder) ---
--- first request from tenant B ---
BUILDING decoder (fetching JWK Set) for issuer: https://tenant-b.okta.com/oauth2/default
```

What changed: `cache.computeIfAbsent` only triggers the (simulated) expensive JWK Set fetch the *first* time a given issuer is seen — tenant A's second request reuses the already-built decoder silently, with no "BUILDING" message printed again — this is exactly the caching behavior that keeps a multi-tenant resource server from re-fetching keys on every single request, even across dozens of tenants.

### Level 3 — Advanced

Reject an untrusted issuer *before* any decoder-building work would occur — the security-critical ordering — and show the contrast against a tenant whose decoder was never built at all versus one whose token is simply rejected outright.

```java
import java.util.*;

public class MultiTenantLevel3 {
    record Jwt(String issuer, String subject) {}
    record AuthenticationResult(String issuer, String subject) {}

    static class UntrustedIssuerException extends RuntimeException {
        UntrustedIssuerException(String message) { super(message); }
    }

    static class PerIssuerDecoder {
        private final String issuer;
        PerIssuerDecoder(String issuer) {
            this.issuer = issuer;
            System.out.println("BUILDING decoder (fetching JWK Set) for issuer: " + issuer);
        }
        AuthenticationResult decode(Jwt jwt) { return new AuthenticationResult(jwt.issuer(), jwt.subject()); }
    }

    static class IssuerResolver {
        private final Set<String> trustedIssuers;
        private final Map<String, PerIssuerDecoder> cache = new HashMap<>();
        private int untrustedRejectionCount = 0;

        IssuerResolver(Set<String> trustedIssuers) { this.trustedIssuers = trustedIssuers; }

        AuthenticationResult authenticate(Jwt jwt) {
            // STEP 1: allowlist check FIRST -- against the raw, UNVERIFIED claim -- before touching the cache at all
            if (!trustedIssuers.contains(jwt.issuer())) {
                untrustedRejectionCount++;
                throw new UntrustedIssuerException(
                        "issuer \"" + jwt.issuer() + "\" is not in the trusted allowlist -- rejecting WITHOUT fetching any keys");
            }
            // STEP 2: only NOW do we build/reuse a decoder, and only for a KNOWN-TRUSTED issuer
            PerIssuerDecoder decoder = cache.computeIfAbsent(jwt.issuer(), PerIssuerDecoder::new);
            return decoder.decode(jwt);
        }

        int getUntrustedRejectionCount() { return untrustedRejectionCount; }
        int getCachedDecoderCount() { return cache.size(); }
    }

    public static void main(String[] args) {
        IssuerResolver resolver = new IssuerResolver(Set.of("https://tenant-a.okta.com/oauth2/default"));

        System.out.println("--- legitimate request from the ONE trusted tenant ---");
        AuthenticationResult ok = resolver.authenticate(new Jwt("https://tenant-a.okta.com/oauth2/default", "alice"));
        System.out.println("authenticated: " + ok);

        System.out.println("--- forged token claiming an arbitrary, attacker-controlled issuer ---");
        try {
            resolver.authenticate(new Jwt("https://attacker-controlled.example/fake-idp", "anyone"));
        } catch (UntrustedIssuerException e) {
            System.out.println("REJECTED: " + e.getMessage());
        }

        System.out.println("decoders actually built: " + resolver.getCachedDecoderCount()
                + " (the attacker's fake issuer NEVER triggered a key fetch)");
        System.out.println("untrusted rejections so far: " + resolver.getUntrustedRejectionCount());
    }
}
```

**How to run:** save as `MultiTenantLevel3.java`, run `java MultiTenantLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- legitimate request from the ONE trusted tenant ---
BUILDING decoder (fetching JWK Set) for issuer: https://tenant-a.okta.com/oauth2/default
authenticated: AuthenticationResult[issuer=https://tenant-a.okta.com/oauth2/default, subject=alice]
--- forged token claiming an arbitrary, attacker-controlled issuer ---
REJECTED: issuer "https://attacker-controlled.example/fake-idp" is not in the trusted allowlist -- rejecting WITHOUT fetching any keys
decoders actually built: 1 (the attacker's fake issuer NEVER triggered a key fetch)
untrusted rejections so far: 1
```

What changed: `authenticate` now performs the allowlist check as an unconditional first step, before `cache.computeIfAbsent` is ever reached — the forged token's claimed issuer never causes a `PerIssuerDecoder` to be constructed at all (`getCachedDecoderCount()` stays at `1`, only the legitimate tenant), demonstrating precisely why this ordering matters: an attacker cannot use a forged `iss` claim to trick the resource server into making an outbound network call to an arbitrary URL, since that call would only ever happen *after* the allowlist has already confirmed the issuer is one this application explicitly chose to trust.

## 6. Walkthrough

Trace the forged-token rejection from Level 3 as a concrete request, then contrast it with the legitimate tenant A request.

**Step 1 — an attacker (or a misconfigured client) sends a request with a token claiming an arbitrary issuer:**
```
GET /api/orders HTTP/1.1
Host: api.example.com
Authorization: Bearer <JWT with unverified claim {"iss":"https://attacker-controlled.example/fake-idp", ...}>
```

**Step 2 — the resolver peeks at the claim, unverified.** This corresponds to reading `jwt.issuer()` in `authenticate` — at this point, nothing about the token has been cryptographically checked yet; only the *claimed* value has been read, exactly as `JwtIssuerAuthenticationManagerResolver` must do, since it doesn't yet know which key would even be needed to verify anything.

**Step 3 — the allowlist check runs, and fails.** `trustedIssuers.contains("https://attacker-controlled.example/fake-idp")` is `false`, since `trustedIssuers` only contains `"https://tenant-a.okta.com/oauth2/default"`. The `if` branch throws `UntrustedIssuerException` immediately.

**Step 4 — critically, no further work happens.** `cache.computeIfAbsent` is never reached for this request — no `PerIssuerDecoder` is constructed, meaning no outbound HTTP call to fetch a JWK Set from `https://attacker-controlled.example/fake-idp` (or anywhere else) is ever made. This is the security property the ordering guarantees: an attacker cannot use this endpoint as a vector to make the resource server issue arbitrary outbound requests based on claims in an untrusted token.

**Step 5 — the resource server's response:**
```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token", error_description="untrusted issuer"
```

**Contrast — tenant A's legitimate request.** `authenticate(new Jwt("https://tenant-a.okta.com/oauth2/default", "alice"))` passes the allowlist check on step 3's equivalent line (`trustedIssuers.contains(...)` is `true` here), and *only then* does `cache.computeIfAbsent` run — the first time for this issuer, triggering the "BUILDING decoder" fetch; on any subsequent request from tenant A, the same cache entry is reused with no further fetch.

```
forged token,   iss="attacker-controlled...":
   allowlist check -> NOT trusted -> REJECT -- zero key-fetch attempts, zero cache entries created

legitimate token, iss="tenant-a.okta.com...":
   allowlist check -> trusted -> proceed
   cache miss (first time) -> BUILD decoder (fetch tenant-a's OWN keys) -> cache it -> validate -> AUTHENTICATED
```

## 7. Gotchas & takeaways

> **Gotcha:** never build a resource server's issuer trust logic the other way around — accepting *any* `iss` value and fetching keys from wherever it points, then validating the signature against whatever comes back. That inverted order lets a forged token direct the resource server to fetch keys from an attacker-controlled URL, and depending on what that URL serves, could be leveraged for server-side request forgery or a spoofed signature check. The allowlist must be checked against the raw claim before any network activity is triggered by it.

- A multi-tenant resource server cannot fix a single issuer at startup — it must inspect each token's claimed (still-unverified) `iss` to know which issuer-specific decoder to use.
- `JwtIssuerAuthenticationManagerResolver` (and the pattern this card models) checks the incoming issuer against a fixed, trusted allowlist *before* any key-fetching or signature work occurs — an untrusted issuer is rejected with zero network activity.
- Per-issuer `AuthenticationManager`/`JwtDecoder` instances are built lazily and cached, so a tenant's keys are only ever fetched once its first request arrives, and never re-fetched needlessly for every subsequent request from the same tenant.
- This same mechanism supports a temporary multi-issuer window during an authorization-server migration — trust both the old and new issuer simultaneously until every client has cut over, then shrink the allowlist back down to one.
- Because each issuer gets its own `AuthenticationManager`, per-tenant validation rules (a stricter audience check, different claim-mapping logic) can differ tenant to tenant, not just the signing keys.
