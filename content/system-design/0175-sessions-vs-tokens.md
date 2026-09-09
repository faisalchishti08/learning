---
card: system-design
gi: 175
slug: sessions-vs-tokens
title: Sessions vs tokens
---

## 1. What it is

A **session** authenticates a user once, then stores their identity server-side (usually in memory or a shared store like Redis) under a session ID, which the client holds as a cookie and sends with every request — the server looks up the session ID to know who is making the request. A **token** (commonly a [JWT](0177-jwt-structure-validation.md)) instead encodes the user's identity and claims directly inside the token itself, cryptographically signed, so the server can verify it without looking anything up in shared storage — the server trusts the token's contents because the signature proves it has not been tampered with.

## 2. Why & when

A session-based approach is simple and lets the server immediately revoke access (just delete the session), but requires a shared session store that every server instance can reach — a real dependency and a point of coordination across a fleet of servers. A token-based approach lets any server instance verify a request on its own, with no shared store and no network round trip, since the token is self-contained and signed — but revoking a single token before it naturally expires is much harder, since no server is tracking it centrally. Use sessions when you need instant revocation and control a small, contained set of servers; use tokens for stateless, horizontally-scaled services, or when third parties (mobile apps, other companies' services) need to hold and present credentials your servers did not directly create.

## 3. Core concept

- **Session ID as a lookup key:** the cookie holds only an opaque, random ID; all real user data lives server-side, keyed by that ID.
- **Server-side revocation is instant for sessions:** deleting the session entry from the store immediately invalidates it — the next request with that session ID finds nothing and is rejected.
- **Token self-containment:** a signed token holds the actual claims (user ID, roles, expiry) inside it; any server holding the signing key's public counterpart can verify and read the token without asking anywhere else.
- **Token revocation is hard:** since no central store is checked by default, a compromised token remains valid until it expires, unless you add an extra mechanism (a blocklist of revoked token IDs, checked on every request) — which reintroduces some of the shared-lookup cost tokens were meant to avoid.
- **Statelessness and horizontal scaling:** because any server can verify a token independently, adding more server instances needs no coordination for authentication — this is the main operational advantage tokens have over sessions at scale.

## 4. Diagram

```
   SESSION-BASED:                              TOKEN-BASED:
   client -> cookie: session-id-xyz             client -> header: Authorization: Bearer <signed token>
                |                                             |
                v                                             v
   server: look up "xyz" in shared store        server: verify signature locally (no lookup)
           -> found: {userId: 17, role: ...}             -> decode claims: {userId: 17, role: ...}
                |                                             |
   revoke: DELETE session "xyz" from store      revoke: token still valid until it expires
           -> instantly invalid                          (unless a blocklist is checked too)
```
*Caption: a session needs a shared lookup on every request but revokes instantly; a token needs no lookup but is hard to revoke before it naturally expires.*

## 5. Runnable example

**Level 1 — Basic.** A session store: create a session, look it up by ID.

**Level 2 — A self-contained "token": encode claims and a signature, verify without any lookup.** Model signature verification with a simple checksum.

**Level 3 — Revocation comparison.** Show a session revoking instantly, versus a token remaining valid (unless checked against an explicit blocklist).

```java
// SessionsVsTokensDemo.java
import java.util.*;

public class SessionsVsTokensDemo {

    // Level 1: session store - server-side state, keyed by an opaque session ID.
    static Map<String, String> sessionStore = new HashMap<>(); // sessionId -> userId

    static String createSession(String userId) {
        String sessionId = "sess-" + UUID.randomUUID().toString().substring(0, 8);
        sessionStore.put(sessionId, userId);
        return sessionId;
    }

    static String lookupSession(String sessionId) {
        return sessionStore.get(sessionId); // returns null if revoked or never existed - a real lookup, every time
    }

    // Level 2: a simplified "token" - claims plus a signature (here, a simple checksum standing in for a real crypto signature).
    static String signToken(String claims, String secretKey) {
        return Integer.toHexString((claims + secretKey).hashCode());
    }

    static String issueToken(String userId, String secretKey) {
        String claims = "userId=" + userId;
        String signature = signToken(claims, secretKey);
        return claims + "." + signature; // "claims.signature" - self-contained, no server-side storage needed
    }

    static String verifyAndDecodeToken(String token, String secretKey) {
        String[] parts = token.split("\\.");
        String claims = parts[0], signature = parts[1];
        if (!signToken(claims, secretKey).equals(signature)) {
            throw new SecurityException("invalid signature - token was tampered with");
        }
        return claims; // no lookup anywhere - the signature alone proves authenticity
    }

    // Level 3: a token blocklist - the ONLY way to revoke a token early, and it reintroduces a lookup.
    static Set<String> revokedTokenSignatures = new HashSet<>();

    public static void main(String[] args) {
        String secretKey = "server-secret-key";

        // Level 1: session-based flow.
        String sessionId = createSession("user-17");
        System.out.println("session created: " + sessionId + " -> " + lookupSession(sessionId));
        sessionStore.remove(sessionId); // revoke by deleting the server-side entry
        System.out.println("after revocation, session lookup: " + lookupSession(sessionId) + " (instantly invalid)");

        // Level 2: token-based flow - no server-side storage needed to verify.
        String token = issueToken("user-17", secretKey);
        System.out.println("token issued: " + token);
        System.out.println("verified claims (no lookup): " + verifyAndDecodeToken(token, secretKey));

        // Level 3: "revoking" a token before its natural expiry requires an explicit blocklist check.
        String[] tokenParts = token.split("\\.");
        revokedTokenSignatures.add(tokenParts[1]);
        System.out.println("attempting to use the token after adding it to a blocklist...");
        if (revokedTokenSignatures.contains(tokenParts[1])) {
            System.out.println("rejected: token signature is on the revocation blocklist (this check itself needs a shared lookup)");
        } else {
            System.out.println("accepted: " + verifyAndDecodeToken(token, secretKey));
        }
    }
}
```

**How to run:** save as `SessionsVsTokensDemo.java`, then run `java SessionsVsTokensDemo.java`.

## 6. Walkthrough

1. `createSession("user-17")` generates a random `sessionId` and stores the mapping in `sessionStore`; `lookupSession(sessionId)` finds it and returns `"user-17"` — the identity lives entirely on the server, and the client only ever holds the opaque ID.
2. `sessionStore.remove(sessionId)` deletes the entry entirely; the next call to `lookupSession(sessionId)` finds nothing and returns `null` — revocation is instant and absolute, since the server is the sole source of truth.
3. `issueToken("user-17", secretKey)` builds a `claims` string and computes a `signature` over `claims + secretKey` via `signToken`, then returns them joined as `"claims.signature"` — this whole string is self-contained; nothing about it needs to be stored anywhere on the server.
4. `verifyAndDecodeToken(token, secretKey)` re-computes the expected signature from the token's own `claims` part and the server's `secretKey`, and compares it to the signature embedded in the token; since they match, verification succeeds and the claims are returned — critically, no `Map` lookup or database call happened anywhere in this step.
5. Adding the token's signature to `revokedTokenSignatures` and checking it before trusting the token models the *only* way to revoke a token before its natural expiry — and this check itself requires exactly the kind of shared, checked-on-every-request store that plain tokens were designed to avoid, showing that "instant revocation" and "no shared lookup" are fundamentally in tension for token-based auth.

## 7. Gotchas & takeaways

> Gotcha: choosing tokens purely for "statelessness" while also needing instant revocation (e.g. for a banned user, or a leaked token) means reimplementing much of a session store anyway, just as a blocklist instead of an allowlist — before committing to pure stateless tokens, be honest about whether your system actually needs instant revocation, since that need pulls hard back toward session-like server-side state.

- Sessions store identity server-side and revoke instantly, but need a shared store every server instance can reach.
- Tokens are self-contained and need no shared store to verify, but are hard to revoke before they naturally expire without adding one back.
- The choice is a real tradeoff between operational simplicity of scaling (tokens) and operational simplicity of revocation (sessions), not a strictly "better" option either way.
- Related concepts: [JWT structure & validation](0177-jwt-structure-validation.md) (the most common concrete token format), [Authentication vs authorization](0174-authentication-vs-authorization.md) (what both mechanisms exist to carry between requests), [Distributed locks (Redis Redlock / ZooKeeper)](0167-distributed-locks-redis-redlock-zookeeper.md) (the kind of shared store a session-based system typically relies on at scale).
