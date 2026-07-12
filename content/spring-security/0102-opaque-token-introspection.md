---
card: spring-security
gi: 102
slug: opaque-token-introspection
title: "Opaque token introspection"
---

## 1. What it is

`oauth2ResourceServer(oauth2 -> oauth2.opaqueToken(...))` wires the opposite half of card 0099's contrast: instead of decoding and locally verifying a self-contained JWT, this configuration treats the bearer token as a meaningless string — genuinely "opaque" to the resource server — and asks the authorization server directly, via RFC 7662's **Token Introspection** endpoint, whether it's currently valid and what it represents. `OpaqueTokenIntrospector` is the interface behind this call; `SpringOpaqueTokenIntrospector` is the default implementation, configured with the introspection endpoint's URI plus credentials the resource server itself authenticates with (introspection is a protected endpoint — not just anyone can ask "is this token valid").

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .oauth2ResourceServer(oauth2 -> oauth2.opaqueToken(Customizer.withDefaults()));
    return http.build();
}
```
```yaml
spring:
  security:
    oauth2:
      resourceserver:
        opaquetoken:
          introspection-uri: https://auth.example.com/oauth2/introspect
          client-id: resource-server-1        # THIS resource server's own credentials
          client-secret: ${INTROSPECTION_SECRET}
```

## 2. Why & when

Card 0099 already named the core trade-off — JWTs are fast but can't be revoked before their natural expiry without extra machinery, opaque tokens are slower (a network call per request) but always reflect the authorization server's live state. This card exists to make that trade-off concrete: introspection is the *mechanism* by which "live state" is obtained, and understanding its request/response shape and failure modes is what turns "opaque tokens support instant revocation" from an abstract claim into something you can actually implement and debug.

Reach for opaque token introspection when:

- Revocation must take effect immediately — a user's session is force-logged-out from an admin panel, a compromised token must stop working the instant it's flagged, and waiting for a JWT's natural expiry (even a short one) isn't acceptable.
- The token format itself is controlled entirely by the authorization server and isn't necessarily even a JWT — introspection works for any opaque, server-issued string, since the resource server never needs to parse it, only ask about it.
- The extra per-request network latency is acceptable for the endpoints in question — often true for lower-traffic, higher-sensitivity operations (payments, account changes) even in a system that uses JWTs elsewhere for high-volume, latency-sensitive endpoints.
- Building a resource server against an authorization server you don't fully control the token format of — introspection decouples the resource server's implementation from ever needing to understand the authorization server's internal token representation.

## 3. Core concept

```
Incoming request:
    GET /api/orders
    Authorization: Bearer a1b2c3-opaque-token-xyz     <-- meaningless string to THIS server

OpaqueTokenIntrospector.introspect(token):
  1. build an introspection request, AUTHENTICATED as the resource server itself:
       POST introspection-uri
       Authorization: Basic <base64(client-id:client-secret)>
       Content-Type: application/x-www-form-urlencoded

       token=a1b2c3-opaque-token-xyz

  2. authorization server looks the token up in ITS OWN store (never decoded/verified locally)
  3. authorization server responds:
       {"active": true, "sub": "alice", "scope": "read:orders write:orders", "exp": 1735689600}
       -- or, if revoked/expired/unknown --
       {"active": false}

  4. active=false           -> reject: 401 invalid_token
     active=true            -> build an Authentication from the returned claims
     introspection call FAILS (network/timeout/5xx from auth server) -> reject: 401 (or 5xx, depending on config)
       -- a DIFFERENT failure category from "active=false": the CHECK couldn't be performed at all
```

Every single request pays this network round trip — there is no local caching of introspection results by default, since caching would reintroduce exactly the revocation-latency problem this mechanism exists to avoid.

## 4. Diagram

<svg viewBox="0 0 660 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence diagram showing a request with an opaque bearer token being introspected by posting to the authorization servers introspection endpoint authenticated as the resource server itself and receiving back an active true or false response used to build or reject authentication">
  <text x="90" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="330" y="24" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Resource Server</text>
  <text x="580" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Authorization Server</text>

  <line x1="90" y1="35" x2="90" y2="215" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="330" y1="35" x2="330" y2="215" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="580" y1="35" x2="580" y2="215" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <line x1="90" y1="55" x2="325" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#it102)"/>
  <text x="95" y="48" fill="#e6edf3" font-size="8.5" font-family="sans-serif">1. GET /api/orders, Authorization: Bearer opaque-xyz</text>

  <line x1="330" y1="90" x2="575" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#it102)"/>
  <text x="335" y="83" fill="#e6edf3" font-size="8.5" font-family="sans-serif">2. POST /introspect (Basic auth AS resource server)</text>

  <rect x="480" y="100" width="140" height="26" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="550" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">lookup in own store</text>

  <line x1="580" y1="140" x2="335" y2="140" stroke="#8b949e" stroke-width="1.5" marker-end="url(#it102b)"/>
  <text x="575" y="133" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">3. {"active":true,"sub":"alice","scope":"..."}</text>

  <rect x="260" y="150" width="140" height="26" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="330" y="167" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">build Authentication</text>

  <line x1="330" y1="190" x2="95" y2="190" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#it102c)"/>
  <text x="330" y="203" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">4. 200 OK (or 401 if active=false)</text>

  <defs>
    <marker id="it102" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="it102b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="it102c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Introspection is itself an authenticated call — the resource server proves its own identity to the authorization server before asking about someone else's token.

## 5. Runnable example

The scenario: a from-scratch introspection client and authorization server pair, growing from a bare active/inactive check into resource-server self-authentication, then into distinguishing an inactive-token rejection from an introspection-call failure — two categories that must be handled differently.

### Level 1 — Basic

Ask the authorization server whether a token is active; build a principal if so.

```java
import java.util.*;

public class IntrospectionLevel1 {
    record IntrospectionResponse(boolean active, String subject, String scope) {}
    record Authentication(String subject, Set<String> authorities) {}

    static class AuthorizationServer {
        private final Map<String, IntrospectionResponse> tokens = new HashMap<>();
        void register(String token, IntrospectionResponse response) { tokens.put(token, response); }

        IntrospectionResponse introspect(String token) {
            return tokens.getOrDefault(token, new IntrospectionResponse(false, null, null));
        }
    }

    static Authentication authenticate(String token, AuthorizationServer authServer) {
        IntrospectionResponse response = authServer.introspect(token);
        if (!response.active()) throw new IllegalStateException("token is not active");
        Set<String> authorities = new LinkedHashSet<>();
        for (String s : response.scope().split(" ")) authorities.add("SCOPE_" + s);
        return new Authentication(response.subject(), authorities);
    }

    public static void main(String[] args) {
        AuthorizationServer authServer = new AuthorizationServer();
        authServer.register("opaque-abc123", new IntrospectionResponse(true, "alice", "read:orders"));

        Authentication authentication = authenticate("opaque-abc123", authServer);
        System.out.println("subject: " + authentication.subject());
        System.out.println("authorities: " + authentication.authorities());
    }
}
```

**How to run:** save as `IntrospectionLevel1.java`, run `java IntrospectionLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
subject: alice
authorities: [SCOPE_read:orders]
```

`authenticate` mirrors `SpringOpaqueTokenIntrospector.introspect`'s happy path: ask, check `active`, build authorities from the returned `scope` — the resource server never inspects the token's own structure at all, only trusts what the authorization server reports about it.

### Level 2 — Intermediate

Add resource-server self-authentication to the introspection call — the authorization server must be able to trust that *this specific resource server* is the one asking, not an arbitrary caller.

```java
import java.util.*;

public class IntrospectionLevel2 {
    record IntrospectionResponse(boolean active, String subject, String scope) {}
    record Authentication(String subject, Set<String> authorities) {}

    static class AuthorizationServer {
        private final Map<String, IntrospectionResponse> tokens = new HashMap<>();
        private final Map<String, String> registeredResourceServers = new HashMap<>(); // clientId -> clientSecret

        void register(String token, IntrospectionResponse response) { tokens.put(token, response); }
        void registerResourceServer(String clientId, String clientSecret) { registeredResourceServers.put(clientId, clientSecret); }

        IntrospectionResponse introspect(String token, String callerClientId, String callerClientSecret) {
            String expectedSecret = registeredResourceServers.get(callerClientId);
            if (expectedSecret == null || !expectedSecret.equals(callerClientSecret)) {
                throw new SecurityException("introspection caller not authenticated -- unknown or wrong credentials");
            }
            return tokens.getOrDefault(token, new IntrospectionResponse(false, null, null));
        }
    }

    static Authentication authenticate(String token, AuthorizationServer authServer, String clientId, String clientSecret) {
        IntrospectionResponse response = authServer.introspect(token, clientId, clientSecret);
        if (!response.active()) throw new IllegalStateException("token is not active");
        Set<String> authorities = new LinkedHashSet<>();
        for (String s : response.scope().split(" ")) authorities.add("SCOPE_" + s);
        return new Authentication(response.subject(), authorities);
    }

    public static void main(String[] args) {
        AuthorizationServer authServer = new AuthorizationServer();
        authServer.registerResourceServer("resource-server-1", "correct-secret");
        authServer.register("opaque-abc123", new IntrospectionResponse(true, "alice", "read:orders write:orders"));

        Authentication authentication = authenticate("opaque-abc123", authServer, "resource-server-1", "correct-secret");
        System.out.println("authenticated: " + authentication.subject() + " " + authentication.authorities());

        try {
            authenticate("opaque-abc123", authServer, "resource-server-1", "WRONG-secret");
        } catch (SecurityException e) {
            System.out.println("introspection rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `IntrospectionLevel2.java`, run `java IntrospectionLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated: alice [SCOPE_read:orders, SCOPE_write:orders]
```
```
introspection rejected: introspection caller not authenticated -- unknown or wrong credentials
```

What changed: `introspect` now requires the *caller* (the resource server itself) to authenticate with its own `clientId`/`clientSecret` before it will answer anything about a user's token — a resource server with the wrong introspection credentials gets rejected regardless of whether the token being asked about is valid, exactly mirroring why the `client-id`/`client-secret` in the YAML configuration at the top of this card belong to the *resource server*, not the end user.

### Level 3 — Advanced

Distinguish two genuinely different failure categories that must be handled differently: a token the authorization server explicitly says is inactive, versus the introspection call itself failing (network error, authorization server down) — the latter says nothing about whether the token is actually good or bad.

```java
import java.util.*;

public class IntrospectionLevel3 {
    record IntrospectionResponse(boolean active, String subject, String scope) {}
    record Authentication(String subject, Set<String> authorities) {}

    static class IntrospectionCallFailedException extends RuntimeException {
        IntrospectionCallFailedException(String message) { super(message); }
    }
    static class InvalidTokenException extends RuntimeException {
        InvalidTokenException(String message) { super(message); }
    }

    static class AuthorizationServer {
        private final Map<String, IntrospectionResponse> tokens = new HashMap<>();
        private final Map<String, String> registeredResourceServers = new HashMap<>();
        private boolean simulateOutage = false;

        void register(String token, IntrospectionResponse response) { tokens.put(token, response); }
        void registerResourceServer(String clientId, String clientSecret) { registeredResourceServers.put(clientId, clientSecret); }
        void simulateOutage(boolean outage) { this.simulateOutage = outage; }

        IntrospectionResponse introspect(String token, String clientId, String clientSecret) {
            if (simulateOutage) throw new RuntimeException("connection refused"); // the AUTH SERVER itself is unreachable
            String expectedSecret = registeredResourceServers.get(clientId);
            if (expectedSecret == null || !expectedSecret.equals(clientSecret)) {
                throw new SecurityException("introspection caller not authenticated");
            }
            return tokens.getOrDefault(token, new IntrospectionResponse(false, null, null));
        }
    }

    enum FailureCategory { INTROSPECTION_UNAVAILABLE, TOKEN_INACTIVE, NONE }
    record AuthResult(FailureCategory failure, Authentication authentication) {}

    static AuthResult authenticate(String token, AuthorizationServer authServer, String clientId, String clientSecret) {
        IntrospectionResponse response;
        try {
            response = authServer.introspect(token, clientId, clientSecret);
        } catch (RuntimeException e) {
            // the CHECK could not be performed -- this is NOT the same as "the token is bad"
            return new AuthResult(FailureCategory.INTROSPECTION_UNAVAILABLE, null);
        }
        if (!response.active()) {
            return new AuthResult(FailureCategory.TOKEN_INACTIVE, null);
        }
        Set<String> authorities = new LinkedHashSet<>();
        for (String s : response.scope().split(" ")) authorities.add("SCOPE_" + s);
        return new AuthResult(FailureCategory.NONE, new Authentication(response.subject(), authorities));
    }

    public static void main(String[] args) {
        AuthorizationServer authServer = new AuthorizationServer();
        authServer.registerResourceServer("resource-server-1", "correct-secret");
        authServer.register("opaque-alice-token", new IntrospectionResponse(true, "alice", "read:orders"));
        // "opaque-revoked-token" is deliberately NOT registered -- the auth server has no record of it as active

        AuthResult success = authenticate("opaque-alice-token", authServer, "resource-server-1", "correct-secret");
        System.out.println("alice's token: " + success.failure()
                + (success.authentication() != null ? " subject=" + success.authentication().subject() : ""));

        AuthResult inactive = authenticate("opaque-revoked-token", authServer, "resource-server-1", "correct-secret");
        System.out.println("revoked token: " + inactive.failure());

        authServer.simulateOutage(true);
        AuthResult outage = authenticate("opaque-alice-token", authServer, "resource-server-1", "correct-secret");
        System.out.println("during outage: " + outage.failure());
    }
}
```

**How to run:** save as `IntrospectionLevel3.java`, run `java IntrospectionLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice's token: NONE subject=alice
revoked token: TOKEN_INACTIVE
during outage: INTROSPECTION_UNAVAILABLE
```

What changed: `authenticate` now separates a thrown-and-caught network failure (`INTROSPECTION_UNAVAILABLE`) from a normally-returned `active=false` response (`TOKEN_INACTIVE`) — both ultimately result in the request being denied, but they mean fundamentally different things operationally: one is "this specific credential is bad," the other is "we cannot currently tell if any credential is good," which should typically be logged, alerted on, and possibly retried very differently.

## 6. Walkthrough

Trace the revoked-token case from Level 3 as a concrete HTTP sequence, then contrast it with the outage case.

**Step 1 — the inbound request:**
```
GET /api/orders HTTP/1.1
Host: api.example.com
Authorization: Bearer opaque-revoked-token
```

**Step 2 — the resource server initiates introspection, authenticated as itself:**
```
POST /oauth2/introspect HTTP/1.1
Host: auth.example.com
Authorization: Basic cmVzb3VyY2Utc2VydmVyLTE6Y29ycmVjdC1zZWNyZXQ=
Content-Type: application/x-www-form-urlencoded

token=opaque-revoked-token
```
This corresponds to `authServer.introspect("opaque-revoked-token", "resource-server-1", "correct-secret")`. The `Authorization: Basic` header is `base64("resource-server-1:correct-secret")` — this is the resource server proving *its own* identity, entirely separate from whatever identity the token being asked about represents.

**Step 3 — client authentication check passes** (the resource server's own credentials are correct), so the authorization server proceeds to look up the token itself.

**Step 4 — the lookup finds nothing active.** `tokens.getOrDefault("opaque-revoked-token", new IntrospectionResponse(false, null, null))` returns the inactive default, since this token was never registered as active (standing in for a token that was genuinely revoked, or simply never existed).

**Step 5 — the authorization server's response:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"active": false}
```
Note the `200 OK` — introspection itself *succeeded* as an HTTP call; it's the *content* of the response that says the token is unusable. This is precisely why `IntrospectionLevel3`'s `authenticate` method distinguishes the two failure modes at different points: a thrown exception (call failed) versus a normally-returned `active: false` (call succeeded, answer was "no").

**Step 6 — the resource server's own response to the original caller:**
```
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token"
```

**Contrast — the outage case.** When `authServer.simulateOutage(true)` is active, step 2's `POST /oauth2/introspect` never gets a response at all — corresponding to `introspect` throwing `RuntimeException("connection refused")` before returning anything. `authenticate`'s `catch` block converts this into `INTROSPECTION_UNAVAILABLE` rather than `TOKEN_INACTIVE`; a well-behaved resource server would likely respond with a `503 Service Unavailable` (or retry with backoff) here rather than a flat `401`, since a `401` implies confidently "this credential is bad," which isn't actually known during an outage.

```
revoked token:  POST /introspect succeeds (200) -> body says active=false  -> TOKEN_INACTIVE  -> 401
outage:         POST /introspect never completes (connection refused)      -> INTROSPECTION_UNAVAILABLE -> 503 (or retry)
```

## 7. Gotchas & takeaways

> **Gotcha:** conflating "introspection call failed" with "token is inactive" both ends up denying the request, but treating them identically in logs and alerting hides a real operational distinction — a spike in `TOKEN_INACTIVE` might just mean users are logging out normally, while a spike in `INTROSPECTION_UNAVAILABLE` means the authorization server itself may be down, which is a very different (and more urgent) incident.

- Opaque token validation asks the authorization server directly, on every request, whether a token is currently active — the resource server never parses or verifies the token's own structure.
- Introspection is itself an authenticated call: the resource server proves its own identity (`client-id`/`client-secret`) to the authorization server before it will answer anything about someone else's token.
- `active: true`/`active: false` is a normal, successful HTTP response either way — a `false` result means "this token is not usable," not "the introspection call failed."
- A genuinely failed introspection call (network error, authorization server outage) is a distinct failure category from an inactive token, and the two should be logged, monitored, and responded to differently.
- Every request pays the network round trip cost of introspection with no local caching by default — this is precisely what makes revocation take effect immediately, in contrast to the local, cached-key validation JWTs use.
