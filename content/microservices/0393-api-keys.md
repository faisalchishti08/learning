---
card: microservices
gi: 393
slug: api-keys
title: "API keys"
---

## 1. What it is

An **API key** is a single, static, opaque credential — usually a long random string — that a caller includes with every request to prove it's an authorized client. Unlike a JWT, an API key carries no built-in structure or claims of its own; it's just a lookup value the server checks against a stored list of known, valid keys. It's one of the simplest possible forms of [service-to-service authentication](0391-service-to-service-authentication.md), and the most common way third-party developers and external partners authenticate against a public or partner-facing API.

## 2. Why & when

API keys earn their place specifically because they're simple, not because they're the strongest option:

- **Third-party and partner integrations.** When an external company's system needs to call your API, issuing them an OAuth2 client-credentials setup is often more machinery than the relationship needs; a single API key, generated in a developer portal, is quick to issue, quick to revoke, and easy for the partner's engineers to use.
- **Public APIs with usage-based billing or quotas.** An API key doubles as a simple, stable identifier for attributing usage to a specific customer or application — useful for [rate limiting](0397-rate-limiting-throttling-as-security-control.md) and billing, even independent of its security role.
- **Low-stakes, read-only, or already-low-privilege endpoints**, where the operational simplicity of "check a key against a list" outweighs the security gap versus a full token-based scheme.

API keys are a poor fit when you need per-user context (an API key identifies an *application* or *account*, not an individual user session), fine-grained, frequently-changing permissions (a JWT's scopes can vary token to token; an API key's permissions are usually static until someone edits the key's record), or short credential lifetimes (API keys are commonly long-lived by default, unlike a JWT's built-in expiry) — for internal service calls, prefer [mutual TLS](0392-mutual-tls-mtls.md) or signed tokens, which we cover in [service-to-service authentication](0391-service-to-service-authentication.md).

## 3. Core concept

Think of an API key like a numbered gym membership card: it doesn't say anything about who's holding it, just "this number is a valid, active membership" — the front desk looks the number up in a list and lets the holder in if it's found and not expired or suspended. If someone photocopies the card, the copy works exactly as well as the original; there's no way to tell them apart. That's the core trade-off of API keys: they're simple bearer credentials — whoever *presents* the valid key *is* the authenticated party, with no further proof required.

Handled well, an API key system has a few non-negotiable pieces:

1. **The key itself is high-entropy** (long, random, unguessable) — never a predictable value like a sequential ID.
2. **The server stores a hash of the key, not the plaintext** — exactly like a password, so a database leak doesn't hand out usable keys directly (see [secrets management & rotation](0394-secrets-management-rotation.md)).
3. **Keys are scoped and revocable independently.** A well-designed system lets you issue a key with specific permissions (e.g., read-only) and revoke *that one key* without affecting others issued to the same account.
4. **Keys travel over TLS, never in a URL query string** — a key in a URL ends up in server access logs, browser history, and proxy logs, all of which are far more exposed than a request header.
5. **Keys are rotatable and ideally short-to-medium-lived**, with the old key still working during a grace period so the caller can switch over without downtime.

An API key answers "is this a recognized caller?" — it says nothing on its own about *what* that caller is allowed to do beyond whatever permissions were attached to the key at issuance, which is why scopes still matter even in an API-key world.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A client sends its API key in a request header; the server hashes the incoming key and looks it up against stored key hashes, checking scope and revocation before processing the request" font-family="sans-serif">
  <rect x="20" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="90" y="100" fill="#e6edf3" font-size="10" text-anchor="middle">Partner client</text>
  <text x="90" y="115" fill="#8b949e" font-size="9" text-anchor="middle">X-API-Key: sk_live_...</text>

  <rect x="240" y="20" width="180" height="170" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="42" fill="#e6edf3" font-size="11" text-anchor="middle">API server</text>
  <text x="330" y="65" fill="#8b949e" font-size="9" text-anchor="middle">1. hash incoming key</text>
  <text x="330" y="85" fill="#8b949e" font-size="9" text-anchor="middle">2. lookup hash in store</text>
  <text x="330" y="105" fill="#8b949e" font-size="9" text-anchor="middle">3. check revoked?</text>
  <text x="330" y="125" fill="#8b949e" font-size="9" text-anchor="middle">4. check scope</text>
  <text x="330" y="145" fill="#6db33f" font-size="9" text-anchor="middle">-&gt; allow / reject</text>

  <rect x="470" y="80" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="100" fill="#e6edf3" font-size="10" text-anchor="middle">Key store</text>
  <text x="545" y="115" fill="#8b949e" font-size="9" text-anchor="middle">hash -&gt; owner, scope, status</text>

  <line x1="160" y1="105" x2="240" y2="105" stroke="#8b949e" marker-end="url(#ak)"/>
  <line x1="330" y1="90" x2="470" y2="100" stroke="#79c0ff" stroke-dasharray="2,2" marker-end="url(#ak)"/>
  <defs>
    <marker id="ak" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

The server never trusts the raw key comparison alone: it hashes the incoming key, looks it up, and checks both revocation status and scope before allowing the request through.

## 5. Runnable example

Scenario: a partner-facing orders API authenticated with API keys. We start with a naive plaintext key comparison, add proper hashed storage, then add scoping and revocation so a leaked or over-privileged key can be constrained and shut off independently.

### Level 1 — Basic

```java
// File: PlaintextApiKeyCheck.java -- keys are stored and compared in PLAINTEXT.
// Works, but anyone who reads the key store (a backup, a misconfigured admin
// panel, a database dump) gets every partner's usable key directly.
import java.util.*;

public class PlaintextApiKeyCheck {
    static final Map<String, String> KEY_STORE = Map.of(
            "sk_live_abc123", "acme-partner"
    );

    static String handleRequest(String presentedKey) {
        String owner = KEY_STORE.get(presentedKey);
        if (owner == null) return "REJECTED: unknown API key";
        return "Request accepted for '" + owner + "'";
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("sk_live_abc123"));
        System.out.println(handleRequest("sk_live_guessed"));
    }
}
```

How to run: `java PlaintextApiKeyCheck.java`

`KEY_STORE` maps the raw key directly to its owner, and `handleRequest` does a plain map lookup. This works functionally, but `KEY_STORE` holding plaintext keys means anything that can read that data structure (a log statement, a memory dump, a database export) hands an attacker every live key at once — the same weakness plaintext passwords have.

### Level 2 — Intermediate

```java
// File: HashedApiKeyCheck.java -- the store now holds a HASH of each key, never
// the raw value. Incoming keys are hashed before lookup, so a leaked store
// doesn't hand out usable keys directly.
import java.security.*;
import java.util.*;

public class HashedApiKeyCheck {
    // Store: hash(key) -> owner. The real key never lives here.
    static final Map<String, String> KEY_HASH_STORE = new HashMap<>();
    static {
        KEY_HASH_STORE.put(sha256("sk_live_abc123"), "acme-partner");
    }

    static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(input.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    static String handleRequest(String presentedKey) {
        String owner = KEY_HASH_STORE.get(sha256(presentedKey));
        if (owner == null) return "REJECTED: unknown API key";
        return "Request accepted for '" + owner + "'";
    }

    public static void main(String[] args) {
        System.out.println(handleRequest("sk_live_abc123"));
        System.out.println("Stored value is a hash, not the key: " + sha256("sk_live_abc123"));
        System.out.println(handleRequest("sk_live_guessed"));
    }
}
```

How to run: `java HashedApiKeyCheck.java`

`KEY_HASH_STORE` now holds `sha256("sk_live_abc123")` rather than the key itself. `handleRequest` hashes whatever key the caller presents and looks *that* up. Functionally identical results to Level 1, but a leak of `KEY_HASH_STORE` no longer hands out working keys — an attacker would need to reverse a SHA-256 hash of a high-entropy random string, which is computationally infeasible. This mirrors how passwords should be stored, and it's the same principle behind why token signatures matter for JWTs.

### Level 3 — Advanced

```java
// File: ScopedRevocableApiKeys.java -- keys now carry a SCOPE (what they're
// allowed to do) and a REVOKED flag, checked on every request, and a leaked
// key can be revoked independently without touching any other partner's key.
import java.security.*;
import java.time.*;
import java.util.*;

public class ScopedRevocableApiKeys {
    record KeyRecord(String owner, Set<String> scopes, boolean revoked, Instant expiresAt) {}

    static final Map<String, KeyRecord> KEY_HASH_STORE = new HashMap<>();
    static {
        KEY_HASH_STORE.put(sha256("sk_live_abc123"),
                new KeyRecord("acme-partner", Set.of("orders:read"), false, Instant.parse("2026-12-31T00:00:00Z")));
        // A second key for the same partner, leaked and since revoked -- independent of the key above.
        KEY_HASH_STORE.put(sha256("sk_live_leaked999"),
                new KeyRecord("acme-partner", Set.of("orders:read", "orders:write"), true, Instant.parse("2026-12-31T00:00:00Z")));
    }

    static String sha256(String input) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(input.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) sb.append(String.format("%02x", b));
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new RuntimeException(e);
        }
    }

    static String handleRequest(String presentedKey, String requiredScope, Instant now) {
        KeyRecord record = KEY_HASH_STORE.get(sha256(presentedKey));
        if (record == null) return "REJECTED: unknown API key";
        if (record.revoked()) return "REJECTED: key has been revoked (owner='" + record.owner() + "')";
        if (now.isAfter(record.expiresAt())) return "REJECTED: key expired";
        if (!record.scopes().contains(requiredScope)) {
            return "REJECTED: key for '" + record.owner() + "' lacks scope '" + requiredScope + "'";
        }
        return "Request accepted for '" + record.owner() + "' with scope '" + requiredScope + "'";
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-07-13T00:00:00Z");
        System.out.println(handleRequest("sk_live_abc123", "orders:read", now));
        System.out.println(handleRequest("sk_live_abc123", "orders:write", now));       // valid key, WRONG scope
        System.out.println(handleRequest("sk_live_leaked999", "orders:read", now));      // revoked key
    }
}
```

How to run: `java ScopedRevocableApiKeys.java`

`KeyRecord` now bundles an `owner`, a set of `scopes`, a `revoked` flag, and an `expiresAt`. `handleRequest` checks all four in order: the key must be known, not revoked, not expired, and its scopes must include whatever the endpoint requires. The first call succeeds — `sk_live_abc123` has `orders:read`. The second call fails on scope alone: the *same valid, non-revoked* key simply was never granted `orders:write`. The third call, using the second key belonging to the same partner, fails specifically because that key was independently revoked — demonstrating that per-key revocation doesn't have to touch `sk_live_abc123` at all.

## 6. Walkthrough

Trace `ScopedRevocableApiKeys.main` in order. **First**, `handleRequest("sk_live_abc123", "orders:read", now)` runs. `sha256("sk_live_abc123")` is computed and looked up in `KEY_HASH_STORE`, returning the first `KeyRecord`: `owner = "acme-partner"`, `scopes = {"orders:read"}`, `revoked = false`, `expiresAt` in late 2026. `record.revoked()` is `false` — passes. `now.isAfter(record.expiresAt())` is `false` — passes. `record.scopes().contains("orders:read")` is `true` — passes. All four checks clear, so the request is accepted.

**Next**, `handleRequest("sk_live_abc123", "orders:write", now)` runs with the *same* key. The lookup returns the identical `KeyRecord`, and the first three checks pass exactly as before. But `record.scopes().contains("orders:write")` is `false` — this key's scope set only ever contained `orders:read` — so the request is rejected purely on scope, even though the key itself is perfectly valid and unrevoked.

**Finally**, `handleRequest("sk_live_leaked999", "orders:read", now)` runs. The lookup returns the second `KeyRecord`, where `revoked` is `true`. This check fails immediately, before scope is even consulted, and the request is rejected with a message naming the same `owner` as the first key — showing that revoking this one leaked key had no effect on `sk_live_abc123`, which remains fully usable.

```
Request accepted for 'acme-partner' with scope 'orders:read'
REJECTED: key for 'acme-partner' lacks scope 'orders:write'
REJECTED: key has been revoked (owner='acme-partner')
```

Sample real HTTP request using an API key:

```
GET /v1/orders?status=pending HTTP/1.1
Host: api.example.com
X-API-Key: sk_live_abc123

HTTP/1.1 403 Forbidden
Content-Type: application/json

{"error": "insufficient_scope", "required_scope": "orders:write"}
```

## 7. Gotchas & takeaways

> API keys are bearer credentials: whoever presents a valid key is treated as authorized, with no further proof of possession required — unlike mTLS, where the private key backing a certificate never leaves the holder's machine. A leaked API key is instantly and fully usable by whoever finds it, which is why it must never appear in a URL query string, a public repository, client-side JavaScript, or an unencrypted log line; treat every API key exactly like a password.

- API keys are simple, static bearer credentials best suited to external, partner, or public API authentication — not a substitute for [mutual TLS](0392-mutual-tls-mtls.md) or signed tokens for internal service-to-service calls.
- Store only a hash of the key server-side, exactly like a password, so a data leak doesn't hand out working credentials.
- Scope each key to the minimum permissions it needs, and make revocation per-key, not per-partner, so one leaked key doesn't force rotating every credential a partner holds.
- Send keys only over TLS in a header (never a URL query string), and rotate them on a schedule — see [secrets management & rotation](0394-secrets-management-rotation.md) for the general pattern.
- An accepted API key answers "is this a known caller?" — it still says nothing about what that caller may do until scope and permission checks run, the same authentication-versus-authorization distinction covered in [authentication vs authorization](0381-authentication-vs-authorization.md).
