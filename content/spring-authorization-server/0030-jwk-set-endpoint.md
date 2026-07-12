---
card: spring-authorization-server
gi: 30
slug: jwk-set-endpoint
title: "JWK Set endpoint"
---

## 1. What it is

The JWK Set endpoint (`GET /oauth2/jwks` by default) publicly exposes the authorization server's current signing key(s) in JWK (JSON Web Key) format — specifically, only the *public* components, never private key material. It's implemented as `NimbusJwkSetEndpointFilter`, reading directly from the same `JWKSource<SecurityContext>` bean (card 0021) that `JwtEncoder` uses to sign tokens. Resource servers fetch this endpoint (usually once, then cache it) to obtain the key needed to verify JWT signatures.

## 2. Why & when

A resource server validating a JWT access token needs the public key that corresponds to whatever private key signed it — and it needs a reliable, standard way to fetch that key without the authorization server operator having to manually distribute it. The JWK Set endpoint exists so this is entirely self-service and automatic: any resource server, given just the authorization server's issuer URL, can discover this endpoint (via metadata, card 0031/0032) and fetch exactly the keys it needs.

You interact with this endpoint (almost always indirectly, via a resource server's auto-configuration) whenever:

- Setting up any resource server that validates JWT access tokens — `spring-security-oauth2-resource-server`'s `issuer-uri` property triggers automatic discovery and fetching of this endpoint.
- Debugging "invalid signature" JWT validation errors on the resource server side — confirming this endpoint returns the *currently expected* key (matching the `kid` in the token being rejected) is the first diagnostic step.
- Implementing key rotation (card 0021) — this endpoint is where the overlap window of old-and-new keys actually gets served to resource servers during a rotation.

## 3. Core concept

Think of this endpoint as a public noticeboard outside the notary's office (card 0021) — anyone can walk up and copy down the current official seal pattern(s) without needing an appointment or credentials. The noticeboard only ever displays the *pattern* used to verify a seal, never the private stamp itself; that stays locked in the notary's office at all times.

```json
{
  "keys": [
    {
      "kty": "RSA",
      "e": "AQAB",
      "use": "sig",
      "kid": "a1b2c3d4-...",
      "alg": "RS256",
      "n": "sXchAo8...(long base64url-encoded modulus)"
    }
  ]
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Resource server fetches and caches the public JWK Set, then verifies incoming JWTs locally">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">GET /oauth2/jwks</text>
  <text x="110" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(once, then cached)</text>

  <rect x="240" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Resource server</text>
  <text x="330" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">caches keys by kid</text>

  <rect x="460" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="540" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Verify JWT locally</text>
  <text x="540" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no per-request call</text>

  <line x1="200" y1="100" x2="235" y2="100" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="420" y1="100" x2="455" y2="100" stroke="#3fb950" stroke-width="2"/>
</svg>

Fetched once and cached — this is what makes JWT validation not require a network call on every request (card 0020's key tradeoff).

## 5. Runnable example

The scenario: a resource server fetching and using the JWK Set to verify a JWT, then adding caching with respect for the endpoint's own cache headers, and finally handling a key rotation event gracefully by refreshing the cache when an unknown `kid` is encountered.

### Level 1 — Basic

```java
// JwkSetFetchDemo.java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public class JwkSetFetchDemo {
    public static void main(String[] args) throws Exception {
        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/jwks"))
                .GET()
                .build();

        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body (truncated): " + response.body().substring(0, Math.min(120, response.body().length())));
    }
}
```

**How to run:** requires a live, running authorization server; run via `java JwkSetFetchDemo.java` (no extra dependencies, no authentication needed — this endpoint is intentionally public). Expected output (truncated, key material varies):

```
Status: 200
Body (truncated): {"keys":[{"kty":"RSA","e":"AQAB","use":"sig","kid":"a1b2c3d4-5678-90ab-cdef-1234567890ab","alg":"RS256","n":"sXchAo8...
```

### Level 2 — Intermediate

A real resource server (usually via Spring Security's built-in `JwtDecoder` auto-configuration) caches the fetched keys rather than fetching on every single token verification — the endpoint itself is cheap to call, but per-request network calls would still add unnecessary latency to every API request.

```java
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;

public class CachingJwkSetFetcher {

    private String cachedBody;
    private Instant cachedAt = Instant.EPOCH;
    private final Duration cacheTtl = Duration.ofMinutes(15); // typical default in real JwtDecoder setups

    public String getJwkSet() throws Exception {
        if (cachedBody != null && Instant.now().isBefore(cachedAt.plus(cacheTtl))) {
            return cachedBody; // fresh enough, skip the network call
        }

        HttpRequest request = HttpRequest.newBuilder(URI.create("https://auth.example.com/oauth2/jwks"))
                .GET().build();
        HttpResponse<String> response = HttpClient.newHttpClient()
                .send(request, HttpResponse.BodyHandlers.ofString());

        cachedBody = response.body();
        cachedAt = Instant.now();
        return cachedBody;
    }

    public static void main(String[] args) {
        System.out.println("getJwkSet() fetches once, then serves from an in-memory cache for 15 minutes,");
        System.out.println("matching the typical caching window used by Spring Security's own JwtDecoder.");
    }
}
```

**How to run:** run inside a project targeting a live server; calling `getJwkSet()` repeatedly within the TTL window issues only one real HTTP request. Expected output:

```
getJwkSet() fetches once, then serves from an in-memory cache for 15 minutes,
matching the typical caching window used by Spring Security's own JwtDecoder.
```

What changed: keys are now fetched once and reused across many token verifications, instead of one network round trip per incoming request — this is the mechanism that lets JWT validation stay fast (card 0020's whole point) despite the key ultimately coming from a remote endpoint.

### Level 3 — Advanced

Production handles key rotation gracefully: if an incoming token's `kid` isn't found in the cached key set (because the authorization server rotated to a new key since the last fetch, card 0021), the resource server should refresh its cache **once** and retry, rather than either failing immediately or refetching on every single request regardless of whether the cache actually looks stale.

```java
import java.util.Optional;
import java.util.function.Function;

public class RotationAwareKeyLookup {

    private final CachingJwkSetFetcher fetcher;
    private final Function<String, Optional<String>> extractKeyForKid; // parses JWK Set JSON for a given kid

    public RotationAwareKeyLookup(CachingJwkSetFetcher fetcher, Function<String, Optional<String>> extractKeyForKid) {
        this.fetcher = fetcher;
        this.extractKeyForKid = extractKeyForKid;
    }

    public Optional<String> findKeyForKid(String kid) throws Exception {
        String jwkSet = fetcher.getJwkSet();
        Optional<String> key = extractKeyForKid.apply(jwkSet);

        if (key.isPresent()) {
            return key;
        }

        // kid not found in cached set -- possibly a recent rotation; force ONE refresh and retry
        System.out.println("kid '" + kid + "' not found in cached JWK Set; forcing a refresh...");
        fetcher.forceRefresh();
        String freshJwkSet = fetcher.getJwkSet();
        return extractKeyForKid.apply(freshJwkSet);
    }
}
```

**How to run:** requires a `forceRefresh()` method added to `CachingJwkSetFetcher` from Level 2 (simply resetting `cachedAt` to `Instant.EPOCH`) and a real JSON-parsing `extractKeyForKid` function; wire this as part of the resource server's token verification path. Expected behavior when tested against a server that has just rotated keys: the first lookup for a token signed with the new key misses the stale cache, triggers exactly one forced refresh, and succeeds on retry — without falling back to refetching on every subsequent request.

What changed and why it's production-flavored: without this "refresh once on a cache miss" behavior, a resource server holding a stale, pre-rotation cache would reject every token signed with the new key until its normal TTL-based refresh eventually happens (Level 2's 15-minute window) — a real, if temporary, outage for legitimate clients right after every key rotation. Refreshing exactly once on an unknown `kid`, rather than on every miss, also protects against a flood of forced refreshes from a client presenting a token with a genuinely bogus `kid`.

## 6. Walkthrough

Tracing how the JWK Set endpoint gets used across a token's full lifecycle, in execution order:

1. At server startup (or on first request), a resource server's `JwtDecoder` performs OIDC/OAuth2 discovery (card 0031/0032) using the configured `issuer-uri`, learns the `jwks_uri` points at `/oauth2/jwks`, and fetches it.
2. The authorization server's `NimbusJwkSetEndpointFilter` reads the current `JWKSource<SecurityContext>` bean (card 0021), serializes only the public key components, and responds `200 OK` with the JSON body shown in Part 3.
3. The resource server parses this into a set of keys, indexed by `kid`, and caches it (Level 2).
4. A JWT access token arrives as `Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6ImExYjJjM2Q0...`; the resource server decodes the JWT header (not yet verifying anything) to read its `kid` claim.
5. It looks up that `kid` in its cached key set (Level 3's `findKeyForKid`) — found, so it uses the matching public key to verify the JWT's signature locally, no network call needed for this specific request.
6. If the signature and standard claims (`exp`, `iss`, `aud`) all check out, the resource server treats the request as authenticated and proceeds to authorize and serve it.
7. Sometime later, the authorization server rotates its signing key (card 0021's `rotate()`); the next JWT it issues carries a new `kid`. The resource server's next request bearing this new-`kid` token misses its stale cache, triggers exactly one forced refresh (Level 3), picks up the newly-published key (which the rotation deliberately still publishes alongside the retiring one), and verification succeeds.

```
Resource server startup: discover jwks_uri -> GET /oauth2/jwks -> cache keys by kid
   |
incoming JWT: read kid from header
   |
kid found in cache? --yes--> verify signature locally --> proceed
   |  no (e.g. after rotation)
force ONE cache refresh --> re-check --> found (rotation publishes both old+new) --> verify --> proceed
```

## 7. Gotchas & takeaways

> The JWK Set endpoint is deliberately public and unauthenticated — this is correct and by design, since it only ever exposes public key material, which is meant to be freely distributed. Never attempt to gate this endpoint behind authentication; doing so would break automatic key discovery for every resource server without adding any real security benefit.

- Confirm the resource server is actually caching the JWK Set (Level 2) rather than fetching it on every request — an unnecessarily short or absent cache turns supposedly-fast local JWT validation back into a network-bound operation, defeating the format's main advantage.
- After a key rotation, don't rely solely on time-based cache expiry to pick up the new key — handling a `kid` cache miss with a bounded, single forced refresh (Level 3) avoids a real availability gap for legitimate clients using freshly-issued tokens.
- The `kid` in a JWT header is what makes multi-key JWK Sets (during rotation overlap, card 0021) actually work — a resource server that ignores `kid` and just tries the "first" key in the set will fail intermittently during any rotation window.
- If a resource server reports it can never find a valid key at all, check that its configured `issuer-uri` or `jwkSetUri` actually matches the authorization server's real, reachable address — this is the same class of misconfiguration discussed for `issuer` in card 0025.
- Never attempt to construct or mock a `JWKSet` containing private key material for any purpose resembling this public endpoint — the entire security model depends on only public components ever being exposed here.
