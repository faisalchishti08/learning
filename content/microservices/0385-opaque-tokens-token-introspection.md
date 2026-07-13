---
card: microservices
gi: 385
slug: opaque-tokens-token-introspection
title: "Opaque tokens & token introspection"
---

## 1. What it is

An **opaque token** is a [token](0383-token-based-security.md) that means nothing on its own — typically just a random string like `a8f3-92cb-...` — with no embedded, readable claims. Unlike a [JWT](0384-json-web-token-jwt-structure-validation.md), you cannot decode an opaque token to learn who it belongs to or what it authorizes; the token is just a reference, a lookup key. **Token introspection** is the mechanism that makes opaque tokens usable: a receiving service calls back to the authorization server with the token and asks, "is this still valid, and if so, who does it belong to and what can it do?" The authorization server holds the real state and answers on demand.

## 2. Why & when

Opaque tokens trade away the "verify locally, no network call" convenience of JWTs in exchange for something JWTs structurally can't offer: **immediate, guaranteed revocation**. You reach for opaque tokens (or a hybrid where a JWT's claims are minimal and the real state lives server-side) when:

- **Instant revocation matters.** If a user's session must be killed *right now* — they logged out, their account was compromised, an admin revoked access — a JWT stays valid until it naturally expires, because verification never consults the issuer again. An opaque token's validity is checked live on every introspection call, so revoking it takes effect on the very next request.
- **Claims shouldn't be visible to the bearer or intermediaries.** A JWT's payload is base64url-encoded, not encrypted — anyone holding the token can read its claims. An opaque token reveals nothing by itself; only the authorization server (via introspection) knows what it means.
- **The token's scope or role needs to reflect live, frequently-changing state.** If permissions can change mid-session (a role downgrade, a suspended account), an opaque token's introspection response reflects that instantly, whereas a JWT's embedded claims are frozen at issuance until it expires.

The cost is the one JWTs were designed to avoid: **every use requires a network call** to the authorization server's introspection endpoint (or a call to a shared cache that mirrors it), which adds latency and a new runtime dependency every resource server now shares — echoing the same shared-store cost discussed in [token-based security](0383-token-based-security.md).

## 3. Core concept

Think of the difference between a stamped, signed letter of introduction (a JWT) and a coat-check ticket (an opaque token). The letter tells the reader everything on its own — name, credentials, what they're authorized for — the moment they open it. The coat-check ticket tells the attendant nothing by itself; it's just a number. The attendant has to look up that number in their own records to find out whose coat it is and whether it's even still valid — and crucially, if the coat's owner reports it stolen, the attendant can immediately mark that ticket number invalid in their own records, something a self-contained letter has no equivalent for once it's already been handed out.

Concretely, the introspection flow (standardized as [RFC 7662](https://www.rfc-editor.org/rfc/rfc7662) in the OAuth2 ecosystem) works like this:

1. **A client presents an opaque token** in the `Authorization: Bearer <token>` header, exactly as with a JWT — the token *format* is invisible to the client either way.
2. **The resource server cannot verify the token itself** — there's no signature to check, no embedded claims to read. It must call the authorization server's `/introspect` endpoint, passing the token.
3. **The authorization server looks up the token** in its own store and responds with a JSON body: `{"active": true, "sub": "alice", "scope": "orders:read", "exp": ...}` if valid, or `{"active": false}` if the token is expired, revoked, or simply unknown.
4. **The resource server trusts that response** (it authenticated to the introspection endpoint itself, typically with client credentials) and proceeds — or rejects the request if `active` is `false`.
5. **Caching** is common in practice: introspecting on literally every request is expensive, so resource servers often cache a positive introspection result for a short time (seconds, not minutes) — trading a little revocation latency for much lower load on the authorization server, a middle ground between pure JWTs and pure per-request introspection.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An opaque token carries no claims; a resource server must call the authorization server's introspection endpoint on every use to learn whether the token is active and what it authorizes" font-family="sans-serif">
  <rect x="20" y="90" width="90" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="65" y="119" fill="#e6edf3" font-size="10" text-anchor="middle">Client</text>

  <rect x="200" y="30" width="90" height="60" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="245" y="55" fill="#f0883e" font-size="10" text-anchor="middle">Opaque</text>
  <text x="245" y="70" fill="#f0883e" font-size="10" text-anchor="middle">token</text>
  <text x="245" y="83" fill="#8b949e" font-size="8" text-anchor="middle">"a8f3-92cb..."</text>

  <rect x="200" y="130" width="140" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="270" y="150" fill="#79c0ff" font-size="10" text-anchor="middle">Resource server</text>
  <text x="270" y="166" fill="#8b949e" font-size="9" text-anchor="middle">cannot read token</text>
  <text x="270" y="180" fill="#8b949e" font-size="9" text-anchor="middle">must ask auth server</text>

  <rect x="440" y="130" width="160" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="520" y="152" fill="#6db33f" font-size="10" text-anchor="middle">Authorization server</text>
  <text x="520" y="170" fill="#8b949e" font-size="9" text-anchor="middle">POST /introspect</text>
  <text x="520" y="184" fill="#8b949e" font-size="9" text-anchor="middle">{"active":true,"sub":"alice",</text>
  <text x="520" y="197" fill="#8b949e" font-size="9" text-anchor="middle">"scope":"orders:read"}</text>

  <line x1="110" y1="115" x2="200" y2="165" stroke="#8b949e" marker-end="url(#a4)"/>
  <line x1="340" y1="165" x2="440" y2="165" stroke="#6db33f" marker-end="url(#a4)"/>
  <text x="390" y="220" fill="#6db33f" font-size="9" text-anchor="middle">live lookup, every use</text>
  <defs>
    <marker id="a4" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Unlike a JWT, an opaque token means nothing until the resource server asks the authorization server what it means — enabling instant revocation at the cost of a network call per use.

## 5. Runnable example

Scenario: a resource server protecting an "orders" endpoint using opaque tokens. We start with a naive local lookup (showing why that doesn't scale to multiple services), move to a real introspection call against a simulated authorization server, then add caching plus instant revocation to show the key trade-off opaque tokens exist for.

### Level 1 — Basic

```java
// File: NaiveLocalLookup.java -- an opaque token checked against a map the
// RESOURCE SERVER itself owns. Works for one service, but doesn't scale: every
// service needing to check tokens would need its OWN copy of this state.
import java.util.*;

public class NaiveLocalLookup {
    // Anti-pattern: the resource server owns the token state directly.
    static final Map<String, String> LOCAL_TOKEN_OWNERS = new HashMap<>();
    static { LOCAL_TOKEN_OWNERS.put("opaque-abc123", "alice"); }

    static String checkOrder(String token) {
        String owner = LOCAL_TOKEN_OWNERS.get(token);
        return owner == null ? "401: token unknown to THIS service" : "Orders returned for '" + owner + "'";
    }

    public static void main(String[] args) {
        System.out.println(checkOrder("opaque-abc123"));
        System.out.println(checkOrder("some-other-services-token")); // this service never heard of it
        System.out.println("A second resource server would need its OWN copy of this map -- doesn't scale.");
    }
}
```

How to run: `java NaiveLocalLookup.java`

Each service maintaining its own token table is the naive extreme: it avoids a network call, but now every service needs to somehow stay in sync with every token ever issued — which is exactly the shared-state coupling opaque tokens are meant to centralize into one authoritative place instead of duplicating everywhere.

### Level 2 — Intermediate

```java
// File: RealIntrospection.java -- a resource server that has NO local token state
// at all, and instead calls a (simulated) authorization server's introspection
// endpoint on every request to learn whether the token is active.
import java.util.*;

public class RealIntrospection {
    // Simulates the AUTHORIZATION SERVER's own private state -- the resource server never sees this directly.
    static class AuthServer {
        static final Map<String, Map<String, Object>> TOKENS = new HashMap<>();
        static { TOKENS.put("opaque-abc123", Map.of("active", true, "sub", "alice", "scope", "orders:read")); }

        // The introspection endpoint: given a token, tell the caller what it means.
        static Map<String, Object> introspect(String token) {
            return TOKENS.getOrDefault(token, Map.of("active", false));
        }
    }

    static String checkOrder(String token) {
        Map<String, Object> result = AuthServer.introspect(token); // NETWORK CALL in a real system
        if (!Boolean.TRUE.equals(result.get("active"))) {
            return "401: introspection says token is not active";
        }
        return "Orders returned for '" + result.get("sub") + "' with scope '" + result.get("scope") + "'";
    }

    public static void main(String[] args) {
        System.out.println(checkOrder("opaque-abc123")); // valid, active
        System.out.println(checkOrder("never-issued-token")); // unknown to the auth server
    }
}
```

How to run: `java RealIntrospection.java`

The resource server (`checkOrder`) holds no token knowledge of its own — every fact it learns about the token comes from `AuthServer.introspect`, standing in for an HTTP call to a real `/introspect` endpoint. An unknown token returns `{"active": false}` by default rather than throwing an error, matching the real RFC 7662 introspection response shape. This is the core opaque-token property: the resource server is stateless regarding tokens; all authority lives at the auth server.

### Level 3 — Advanced

```java
// File: IntrospectionWithCachingAndRevocation.java -- adds short-lived CACHING of
// introspection results (to avoid a network call on every single request) while
// still demonstrating that REVOCATION at the auth server takes effect almost
// immediately, once the cache entry expires -- the key trade-off opaque tokens make.
import java.util.*;

public class IntrospectionWithCachingAndRevocation {
    static class AuthServer {
        static final Map<String, Map<String, Object>> TOKENS = new HashMap<>();
        static { TOKENS.put("opaque-abc123", new HashMap<>(Map.of("active", true, "sub", "alice", "scope", "orders:read"))); }

        static Map<String, Object> introspect(String token) {
            return TOKENS.getOrDefault(token, Map.of("active", false));
        }
        // Simulates an admin revoking the token RIGHT NOW.
        static void revoke(String token) {
            TOKENS.computeIfPresent(token, (k, v) -> { v.put("active", false); return v; });
        }
    }

    // Resource-server-side cache: token -> (result, cachedAtMillis)
    static final Map<String, Object[]> CACHE = new HashMap<>();
    static final long CACHE_TTL_MILLIS = 200; // short-lived on purpose: bounds revocation latency

    static String checkOrder(String token) {
        Object[] cached = CACHE.get(token);
        long now = System.currentTimeMillis();
        Map<String, Object> result;
        if (cached != null && (now - (long) cached[1]) < CACHE_TTL_MILLIS) {
            result = (Map<String, Object>) cached[0];
            System.out.println("  (served from cache, age " + (now - (long) cached[1]) + "ms)");
        } else {
            result = AuthServer.introspect(token); // real network call, cache miss or expired
            CACHE.put(token, new Object[]{result, now});
            System.out.println("  (fresh introspection call made)");
        }
        if (!Boolean.TRUE.equals(result.get("active"))) {
            return "401: token not active";
        }
        return "Orders returned for '" + result.get("sub") + "'";
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println(checkOrder("opaque-abc123")); // cache miss -- real introspection
        System.out.println(checkOrder("opaque-abc123")); // cache hit -- no network call

        AuthServer.revoke("opaque-abc123"); // admin revokes RIGHT NOW
        System.out.println(checkOrder("opaque-abc123")); // STILL cached -- stale "active" result briefly persists

        Thread.sleep(220); // wait for the cache entry to expire
        System.out.println(checkOrder("opaque-abc123")); // cache expired -- fresh call sees the revocation
    }
}
```

How to run: `java IntrospectionWithCachingAndRevocation.java`

This models the realistic middle ground: caching introspection results avoids a network call on every single request, but the cache TTL directly bounds how long a revoked token can still be accepted. The hard case is the third call: the token was revoked at the authorization server, but the resource server's cache entry is still within its TTL, so it briefly still reports the token as active — a deliberate, *bounded* trade-off, not a bug. Only after the cache entry naturally expires does the next introspection call reveal the revocation.

## 6. Walkthrough

Trace `IntrospectionWithCachingAndRevocation.main` in order. **First**, `checkOrder("opaque-abc123")` runs. `CACHE.get(token)` returns `null` (nothing cached yet), so it's a cache miss: `AuthServer.introspect` is called for real, returns `{"active": true, "sub": "alice", ...}`, and the result is stored in `CACHE` with the current timestamp. The method prints "fresh introspection call made" and returns the orders response.

**Next**, `checkOrder("opaque-abc123")` runs again immediately. `CACHE.get(token)` now returns the entry from a moment ago, and `now - cachedAtMillis` is well under `CACHE_TTL_MILLIS` (200ms) — a cache hit. No call to `AuthServer.introspect` happens at all; the cached, still-active result is reused directly.

**Then**, `AuthServer.revoke("opaque-abc123")` runs, flipping that token's `"active"` field to `false` in the authorization server's own state — simulating an admin action or a user logging out. Immediately after, `checkOrder("opaque-abc123")` runs again: the cache entry is still fresh (well under 200ms old), so it's *still* a cache hit, and the stale, pre-revocation `"active": true` result is served — the resource server has no way to know revocation just happened, because it hasn't asked again yet.

**Finally**, after `Thread.sleep(220)` — past the 200ms TTL — `checkOrder("opaque-abc123")` runs one more time. The cached entry is now older than `CACHE_TTL_MILLIS`, forcing a fresh introspection call. This time `AuthServer.introspect` returns the post-revocation state, `{"active": false}`, and the method correctly returns `"401: token not active"`.

```
call 1: fresh introspection call made   -> Orders returned for 'alice'
call 2: served from cache (age ~0ms)    -> Orders returned for 'alice'
[token revoked at auth server]
call 3: served from cache (still <200ms)-> Orders returned for 'alice'  (stale, expected)
[sleep 220ms]
call 4: fresh introspection call made   -> 401: token not active
```

Sample introspection request/response shape this models, per RFC 7662:

```
POST /introspect HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <resource-server-credentials>

token=opaque-abc123

--> response after revocation:
{"active": false}
```

## 7. Gotchas & takeaways

> The cache TTL in Level 3 is not a bug to be minimized to zero — it's a deliberate dial. Setting it to `0` means every single request pays a network round-trip to the authorization server, which can become a real bottleneck and a single point of failure under load. Setting it too high (minutes) defeats the entire reason to choose opaque tokens over JWTs in the first place — revocation would take just as long to propagate as a JWT's natural expiry might. The right TTL is a few seconds, chosen deliberately against how urgently your system needs revocation to take effect.

- Opaque tokens carry no readable claims; only the authorization server, via introspection, knows what a given token means.
- The core trade-off versus [JWTs](0384-json-web-token-jwt-structure-validation.md): opaque tokens enable instant (or near-instant, with caching) revocation at the cost of a network dependency on every use; JWTs avoid that network call at the cost of staying valid until natural expiry, revocation-resistant by design.
- Introspection responses should themselves be authenticated (the resource server proves its own identity to the introspection endpoint) so that an attacker can't query arbitrary tokens' details.
- Caching introspection results is standard practice in production systems, but the cache TTL is a direct, tunable trade-off between load on the authorization server and revocation latency.
- Some systems use a hybrid: a JWT whose claims are intentionally minimal (just enough for coarse routing) alongside a reference that still requires introspection for anything sensitive — getting some of each approach's benefits.
