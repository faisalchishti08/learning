---
card: spring-security
gi: 101
slug: jwtdecoder-jwk-set
title: "JwtDecoder & JWK set"
---

## 1. What it is

`JwtDecoder` is the interface behind card 0100's `decode(token)` call — the component that actually parses a JWT's compact string form, verifies its signature, and (by default, via `JwtValidators.createDefault()`) checks its `exp`, `iat`, and `nbf` claims. The most common implementation, `NimbusJwtDecoder`, verifies signatures using public keys it fetches from the issuer's **JWK Set** (JSON Web Key Set) — a JSON document, conventionally served at `/.well-known/jwks.json`, listing every public key the issuer currently uses to sign tokens, each tagged with a `kid` (key id) so a decoder can pick the exact key that matches a given token's header. Spring Boot autoconfigures a `NimbusJwtDecoder` automatically from `spring.security.oauth2.resourceserver.jwt.issuer-uri` (fetching the JWK Set URI via OIDC discovery) or from an explicit `jwk-set-uri` if the issuer doesn't support discovery.

```java
@Bean
public JwtDecoder jwtDecoder() {
    return NimbusJwtDecoder.withJwkSetUri("https://auth.example.com/.well-known/jwks.json").build();
}
```
```json
{
  "keys": [
    {"kty": "RSA", "kid": "2024-key-1", "use": "sig", "n": "...", "e": "AQAB"},
    {"kty": "RSA", "kid": "2024-key-2", "use": "sig", "n": "...", "e": "AQAB"}
  ]
}
```

## 2. Why & when

A JWT's signature can only be verified with the *correct* public key, and issuers rotate their signing keys periodically for security hygiene — an old key that's been in use for a year is a bigger target than one rotated every few months. If a resource server hard-coded a single public key, every rotation would require a coordinated deployment across every service that validates that issuer's tokens — completely impractical at any real scale. The JWK Set with a `kid` per key solves this: the issuer can publish a *new* signing key alongside the old one (so tokens signed with either still validate), start signing new tokens with the new key, and eventually drop the old key from the set once every previously-issued token using it has expired — all without any resource server being redeployed, because `NimbusJwtDecoder` fetches (and caches, with automatic refresh) the JWK Set rather than embedding keys statically.

Reach for understanding the JWK Set mechanism specifically when:

- Debugging a sudden wave of `invalid_token` errors after an issuer rotates keys — almost always caused by a resource server's cached JWK Set being stale and not yet refreshed, or a firewall/network policy blocking the resource server from reaching the issuer's JWKS endpoint at all.
- Deciding between `issuer-uri` (lets Spring Boot discover the JWKS endpoint automatically via OIDC discovery metadata) and `jwk-set-uri` (an explicit URL, needed when the issuer doesn't publish discovery metadata, or you want to pin the exact JWKS endpoint).
- Working with an issuer that supports key rotation without downtime — understanding that multiple valid keys can coexist in one JWK Set, distinguished only by `kid`, is what makes zero-downtime rotation possible at all.
- Building or testing against a local/offline JWT issuer (common in tests) — `NimbusJwtDecoder.withPublicKey(...)` or `withSecretKey(...)` bypass the JWK Set fetch entirely for a single, statically-known key, appropriate for test fixtures but not production issuers that rotate keys.

## 3. Core concept

```
JWT header (base64, decoded):
    {"alg": "RS256", "kid": "2024-key-2", "typ": "JWT"}

JwtDecoder.decode(tokenString):
  1. parse the compact JWT string into header + claims + signature
  2. read "kid" from the header
  3. look up that "kid" in the CACHED JWK Set
       cache MISS (new/rotated key) -> re-fetch the JWK Set from jwk-set-uri, try again
       still not found -> fail: unknown signing key
  4. use the matched key's public material to verify the signature
       mismatch -> fail: signature invalid
  5. run configured validators against claims (exp, iat, nbf by default; iss/aud if configured, card 0103)
  6. SUCCESS -> return a Jwt object

Key ROTATION, safely, without downtime:
    issuer publishes NEW key (kid="2024-key-3") ALONGSIDE the old ones in the JWK Set
    issuer starts signing NEW tokens with "2024-key-3"
    resource servers: OLD tokens (kid="2024-key-2") still verify fine -- that key is still IN the set
    once every old token has naturally expired, issuer can safely REMOVE "2024-key-2" from the set
```

The cache-miss-triggers-refetch behavior in step 3 is precisely what lets a resource server pick up a brand-new key without any restart or redeploy.

## 4. Diagram

<svg viewBox="0 0 660 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a jwt with a kid in its header being matched against a cached jwk set on a cache miss the decoder refetches the jwk set from the issuer before retrying the match then uses the matched keys public material to verify the token signature">
  <rect x="20" y="30" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JWT header</text>
  <text x="110" y="65" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">kid=2024-key-3</text>

  <line x1="200" y1="55" x2="245" y2="55" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#jk101)"/>

  <rect x="250" y="20" width="200" height="70" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="350" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">cached JWK Set</text>
  <text x="350" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">key-1, key-2</text>
  <text x="350" y="72" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">key-3 NOT present -&gt; MISS</text>

  <line x1="350" y1="90" x2="350" y2="120" stroke="#f0883e" stroke-width="1.6" marker-end="url(#jk101b)"/>
  <text x="440" y="110" fill="#f0883e" font-size="8.5" font-family="sans-serif">re-fetch on miss</text>

  <rect x="460" y="20" width="180" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="550" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">issuer's JWKS endpoint</text>
  <text x="550" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">/.well-known/jwks.json</text>
  <text x="550" y="74" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">now includes key-3</text>

  <line x1="460" y1="55" x2="355" y2="90" stroke="#f0883e" stroke-width="1.4" stroke-dasharray="4,3" marker-end="url(#jk101b)"/>

  <rect x="250" y="130" width="200" height="46" rx="7" fill="#1c2430" stroke="#3fb950" stroke-width="1.4"/>
  <text x="350" y="150" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">key-3 found after refetch</text>
  <text x="350" y="165" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">verify signature -&gt; match</text>

  <defs>
    <marker id="jk101" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jk101b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

A `kid` not found in the cached JWK Set triggers a live re-fetch before the token is rejected — the mechanism that lets rotation happen without any resource server redeploy.

## 5. Runnable example

The scenario: a from-scratch `JwkSetCache` and `JwtDecoder` pair, growing from a single trusted key into multiple coexisting keys (rotation in progress), then into cache-miss-triggers-refetch behavior that picks up a brand-new key without a restart.

### Level 1 — Basic

One key, one token, verify by matching `kid`.

```java
import java.util.*;

public class JwkSetLevel1 {
    record JwtHeader(String kid) {}
    record Token(JwtHeader header, String signature) {}
    record Jwk(String kid, String publicKeyMaterial) {}

    static class JwtDecoder {
        private final Map<String, Jwk> keysByKid;
        JwtDecoder(List<Jwk> keys) {
            keysByKid = new HashMap<>();
            for (Jwk k : keys) keysByKid.put(k.kid(), k);
        }

        boolean verify(Token token) {
            Jwk matched = keysByKid.get(token.header().kid());
            if (matched == null) throw new IllegalStateException("unknown signing key: " + token.header().kid());
            // stands in for real cryptographic verification against matched.publicKeyMaterial()
            return token.signature().equals("signed-with-" + matched.kid());
        }
    }

    public static void main(String[] args) {
        JwtDecoder decoder = new JwtDecoder(List.of(new Jwk("2024-key-1", "public-material-1")));

        Token token = new Token(new JwtHeader("2024-key-1"), "signed-with-2024-key-1");
        System.out.println("signature valid: " + decoder.verify(token));
    }
}
```

**How to run:** save as `JwkSetLevel1.java`, run `java JwkSetLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
signature valid: true
```

`verify` matches the token's `kid` against the decoder's known keys and checks the signature against that specific key — mirroring `NimbusJwtDecoder`'s core job, just without real RSA/EC cryptography standing in for `"signed-with-..."`.

### Level 2 — Intermediate

Multiple keys coexist in the JWK Set — a rotation in progress — so tokens signed with either the old or the new key must still verify.

```java
import java.util.*;

public class JwkSetLevel2 {
    record JwtHeader(String kid) {}
    record Token(JwtHeader header, String signature) {}
    record Jwk(String kid, String publicKeyMaterial) {}

    static class JwtDecoder {
        private final Map<String, Jwk> keysByKid;
        JwtDecoder(List<Jwk> keys) {
            keysByKid = new LinkedHashMap<>();
            for (Jwk k : keys) keysByKid.put(k.kid(), k);
        }

        boolean verify(Token token) {
            Jwk matched = keysByKid.get(token.header().kid());
            if (matched == null) throw new IllegalStateException("unknown signing key: " + token.header().kid());
            return token.signature().equals("signed-with-" + matched.kid());
        }
    }

    public static void main(String[] args) {
        // rotation in progress: BOTH the old and the new key are published together
        JwtDecoder decoder = new JwtDecoder(List.of(
                new Jwk("2024-key-1", "public-material-1"), // old key, still valid for OLD tokens
                new Jwk("2024-key-2", "public-material-2"))); // new key, used for NEW tokens

        Token oldToken = new Token(new JwtHeader("2024-key-1"), "signed-with-2024-key-1");
        Token newToken = new Token(new JwtHeader("2024-key-2"), "signed-with-2024-key-2");

        System.out.println("old token (pre-rotation) still valid: " + decoder.verify(oldToken));
        System.out.println("new token (post-rotation) valid: " + decoder.verify(newToken));
    }
}
```

**How to run:** save as `JwkSetLevel2.java`, run `java JwkSetLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
old token (pre-rotation) still valid: true
new token (post-rotation) valid: true
```

What changed: the decoder now holds *two* keys simultaneously — this is exactly what a JWK Set looks like mid-rotation, and it's why rotation causes zero downtime: tokens issued before the rotation (signed with `2024-key-1`) keep verifying successfully right alongside brand-new tokens (signed with `2024-key-2`), for as long as the issuer keeps publishing both.

### Level 3 — Advanced

A resource server's decoder caches the JWK Set rather than fetching it on every single request (that would be far too slow) — but a cache miss (an unrecognized `kid`, meaning the key was likely rotated in *after* the cache was last populated) must trigger a live re-fetch before giving up, not an immediate rejection.

```java
import java.util.*;

public class JwkSetLevel3 {
    record JwtHeader(String kid) {}
    record Token(JwtHeader header, String signature) {}
    record Jwk(String kid, String publicKeyMaterial) {}

    // stands in for the issuer's live JWKS endpoint -- the SOURCE of truth, which can change over time
    static class JwksEndpoint {
        private List<Jwk> currentKeys;
        private int fetchCount = 0;

        JwksEndpoint(List<Jwk> initialKeys) { this.currentKeys = new ArrayList<>(initialKeys); }

        void rotateInNewKey(Jwk newKey) { currentKeys.add(newKey); } // issuer publishes a new key, live

        List<Jwk> fetch() {
            fetchCount++;
            return List.copyOf(currentKeys);
        }

        int getFetchCount() { return fetchCount; }
    }

    static class JwtDecoder {
        private final JwksEndpoint endpoint;
        private Map<String, Jwk> cache;

        JwtDecoder(JwksEndpoint endpoint) {
            this.endpoint = endpoint;
            refreshCache();
        }

        private void refreshCache() {
            cache = new LinkedHashMap<>();
            for (Jwk k : endpoint.fetch()) cache.put(k.kid(), k);
        }

        boolean verify(Token token) {
            Jwk matched = cache.get(token.header().kid());
            if (matched == null) {
                // CACHE MISS: the key might have been rotated in since we last fetched -- try ONE live refresh
                refreshCache();
                matched = cache.get(token.header().kid());
                if (matched == null) {
                    throw new IllegalStateException("unknown signing key even after refresh: " + token.header().kid());
                }
            }
            return token.signature().equals("signed-with-" + matched.kid());
        }
    }

    public static void main(String[] args) {
        JwksEndpoint endpoint = new JwksEndpoint(List.of(new Jwk("2024-key-1", "public-material-1")));
        JwtDecoder decoder = new JwtDecoder(endpoint); // 1st fetch happens here, at construction

        Token oldToken = new Token(new JwtHeader("2024-key-1"), "signed-with-2024-key-1");
        System.out.println("old token verifies (cache hit): " + decoder.verify(oldToken));
        System.out.println("fetch count so far: " + endpoint.getFetchCount());

        // the issuer rotates in a brand-new key WHILE our decoder's cache is still the old one
        endpoint.rotateInNewKey(new Jwk("2024-key-2", "public-material-2"));

        // a token signed with the new key arrives -- our cache doesn't know about "2024-key-2" YET
        Token newToken = new Token(new JwtHeader("2024-key-2"), "signed-with-2024-key-2");
        System.out.println("new token verifies (triggers refresh): " + decoder.verify(newToken));
        System.out.println("fetch count after refresh: " + endpoint.getFetchCount());

        // a token with a kid that never existed at all -- refresh happens, but it's STILL not found
        Token bogusToken = new Token(new JwtHeader("never-existed-key"), "signed-with-nothing");
        try {
            decoder.verify(bogusToken);
        } catch (IllegalStateException e) {
            System.out.println("bogus key rejected: " + e.getMessage());
        }
        System.out.println("total fetch count: " + endpoint.getFetchCount());
    }
}
```

**How to run:** save as `JwkSetLevel3.java`, run `java JwkSetLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
old token verifies (cache hit): true
fetch count so far: 1
new token verifies (triggers refresh): true
fetch count after refresh: 2
bogus key rejected: unknown signing key even after refresh: never-existed-key
total fetch count: 3
```

What changed: `verify` now distinguishes a cache hit (no re-fetch needed, `fetchCount` stays put) from a cache miss (triggers exactly one live `refreshCache()` call before giving up) — the new key rotated in mid-run is found on the *second* fetch, while a genuinely bogus `kid` still fails even after a fresh fetch, correctly distinguishing "we just hadn't seen this key yet" from "this key doesn't exist at the issuer at all."

## 6. Walkthrough

Trace the new-token verification from Level 3 — the case demonstrating zero-downtime rotation — end to end.

**Step 1 — decoder construction, at application startup.** `new JwtDecoder(endpoint)` calls `refreshCache()`, which calls `endpoint.fetch()` — corresponding to a real `NimbusJwtDecoder`'s first request to `jwk-set-uri` when it's first needed. `fetchCount` becomes `1`; the cache now holds only `2024-key-1`.

**Step 2 — the issuer rotates in a new key, independently, on its own schedule.** `endpoint.rotateInNewKey(new Jwk("2024-key-2", ...))` — this models the issuer's operations team publishing a new signing key to its live JWKS endpoint; our decoder's in-memory cache has no way to know this happened yet, since nothing has told it to re-fetch.

**Step 3 — a request arrives carrying a token signed with the new key:**
```
GET /api/orders HTTP/1.1
Authorization: Bearer <JWT with header {"kid":"2024-key-2", "alg":"RS256"}>
```
`decoder.verify(newToken)` is called; `cache.get("2024-key-2")` returns `null` because the cache still only holds `2024-key-1` from step 1's fetch.

**Step 4 — the cache miss triggers a live refresh.** `refreshCache()` is called a second time, calling `endpoint.fetch()` again — `fetchCount` becomes `2`, and this fetch reflects the issuer's *current* state, which now includes `2024-key-2` (added in step 2).

**Step 5 — the retry succeeds.** `cache.get("2024-key-2")` now returns the newly-fetched `Jwk`, and `token.signature().equals("signed-with-2024-key-2")` is `true`, so `verify` returns `true` without ever throwing.

**Step 6 — the response.** A real resource server would proceed exactly as in card 0100: build a `Jwt`, populate the `SecurityContext` for this request, and let the request through to the controller — all without a single restart, redeploy, or manual intervention on the resource server's part.

```
t=0   decoder starts, fetch #1 -> {key-1}
t=1   issuer rotates in key-2 (decoder's cache still only knows key-1)
t=2   request with kid=key-2 arrives -> cache MISS -> fetch #2 -> {key-1, key-2} -> HIT -> verified
t=3   request with kid=never-existed arrives -> cache MISS -> fetch #3 -> STILL not found -> rejected
```

**Contrast with the bogus-key case:** step 3's cache miss for `"never-existed-key"` also triggers `refreshCache()` (`fetchCount` reaches `3`), but even the freshest possible fetch doesn't contain that `kid`, since the issuer never published it — `verify` correctly distinguishes "not yet cached" (recoverable via refresh) from "does not exist" (still rejected after refresh) by simply checking the *result* of that same refresh, not by special-casing the two situations up front.

## 7. Gotchas & takeaways

> **Gotcha:** refetching the entire JWK Set on *every single request's* cache miss (rather than the bounded, single-retry pattern shown here) opens a denial-of-service vector — an attacker who floods a resource server with tokens carrying random, nonexistent `kid` values could force unbounded live fetches against the issuer. Production `JwtDecoder` implementations rate-limit or otherwise bound how often a genuine re-fetch is attempted; never assume "cache miss triggers refetch" means "refetch unconditionally, every time, forever."

- `JwtDecoder` verifies a JWT's signature using public keys drawn from the issuer's JWK Set, matched by the `kid` in the token's header — it never trusts a key it hasn't fetched from a configured, trusted source.
- Key rotation works without downtime because multiple keys can coexist in one JWK Set: an issuer publishes a new key alongside the old one, switches to signing with the new one, and only removes the old one once every token it ever signed has naturally expired.
- A cache miss on an unrecognized `kid` should trigger a bounded, one-time live re-fetch before rejecting the token — this is what lets a resource server pick up newly-rotated keys automatically, without a restart.
- `issuer-uri` (OIDC discovery) and `jwk-set-uri` (explicit) are two ways to point a `NimbusJwtDecoder` at the same underlying JWKS endpoint — prefer `issuer-uri` when the issuer supports discovery, since it also picks up other metadata (like the introspection endpoint) automatically.
- Static, hard-coded public keys (`withPublicKey`, `withSecretKey`) skip the JWK Set entirely and are appropriate for tests or issuers with genuinely fixed keys, but they defeat rotation entirely and should not be used against a production issuer that rotates.
