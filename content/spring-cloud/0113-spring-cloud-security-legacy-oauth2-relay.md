---
card: spring-cloud
gi: 113
slug: spring-cloud-security-legacy-oauth2-relay
title: "Spring Cloud Security (legacy, OAuth2 relay)"
---

## 1. What it is

Spring Cloud Security was an early (now largely superseded and legacy) project providing OAuth2 SSO helpers and, notably, "token relay" — automatically forwarding the currently-authenticated user's OAuth2 access token from an incoming request onto any outbound calls a service makes to downstream services, so a chain of microservices could each independently verify the same end-user's identity and permissions without the caller manually copying the token onto every outbound request itself.

```java
// legacy Spring Cloud Security relay -- largely superseded by Spring Cloud Gateway's TokenRelay filter
// and Spring Security's own OAuth2 client support in current applications
@Bean
public OAuth2FeignRequestInterceptor oauth2FeignRequestInterceptor(OAuth2ClientContext context, OAuth2ProtectedResourceDetails resource) {
    return new OAuth2FeignRequestInterceptor(context, resource);
}
```

```yaml
# modern equivalent: Spring Cloud Gateway's built-in TokenRelay filter
spring:
  cloud:
    gateway:
      default-filters:
        - TokenRelay
```

## 2. Why & when

In a microservices chain fronted by an API gateway, an end user authenticates once at the gateway, but every downstream service the gateway routes to may also need to know who that user is and what they're authorized to do — re-authenticating at every hop is both redundant and awkward, since downstream services don't necessarily have direct access to the user's original credentials. Token relay solves this by propagating the *same* validated OAuth2 access token from the original request onto every outbound call the gateway (or an intermediate service) makes on the user's behalf, letting each downstream service independently validate that same token against the authorization server and extract the same user identity and scopes from it, without needing a separate authentication step or a shared session.

Reach for understanding token relay (via its modern equivalent) when:

- Building an API-gateway-fronted microservices architecture where downstream services need to know the authenticated end user's identity — relaying the original access token is the standard mechanism for this, rather than each service performing its own separate authentication flow.
- Working with an existing, older Spring Cloud application still using `spring-cloud-starter-security`'s legacy relay mechanisms — recognizing this as legacy and understanding what it's being replaced by (Spring Cloud Gateway's `TokenRelay` filter, or direct use of Spring Security's OAuth2 client support) informs any modernization effort.
- Debugging a downstream service that unexpectedly can't determine which user made a request — confirming the token relay mechanism (old or new) is actually configured and forwarding the token correctly is a standard first diagnostic step.

## 3. Core concept

```
 user authenticates ONCE at the gateway, receives an OAuth2 access token

 gateway routes request downstream:
   WITHOUT relay: downstream service receives the request with NO token -- doesn't know who the user is
   WITH relay:    the SAME access token is forwarded as an Authorization header on the outbound call
                  downstream service independently validates the SAME token, extracts the SAME user identity

 legacy Spring Cloud Security:  manual OAuth2 interceptors on RestTemplate/Feign clients
 modern equivalent:              Spring Cloud Gateway's TokenRelay filter (automatic, declarative)
```

The relayed token is identical, bit for bit, to the one the original caller presented — relay is purely a forwarding mechanism, not a token-transformation or re-issuance step.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A user presents an access token to the gateway which relays the identical token onward to a downstream service allowing that service to independently validate the same token and identify the same user">
  <rect x="20" y="20" width="130" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="48" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">user + token</text>

  <rect x="250" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">gateway</text>
  <text x="320" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">relays SAME token</text>

  <rect x="480" y="20" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="550" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">downstream service</text>
  <text x="550" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">validates independently</text>

  <defs><marker id="a113" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="150" y1="43" x2="250" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a113)"/>
  <line x1="390" y1="43" x2="480" y2="43" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a113)"/>
</svg>

The token travels unchanged across both hops — the gateway forwards, it doesn't reissue.

## 5. Runnable example

The scenario: model a gateway forwarding an incoming request's access token onto a downstream call, contrasted against a request with no relay where the downstream service can't identify the user. Start with no relay (the broken baseline), then add relay, then add token validation on the downstream side rejecting an expired relayed token, showing relay alone doesn't skip proper validation at each hop.

### Level 1 — Basic

No relay — the downstream service receives the request with no token at all, and can't identify the user.

```java
import java.util.*;

public class TokenRelayLevel1 {
    record Request(Map<String, String> headers) {}

    static String identifyUser(Request req) {
        String token = req.headers().get("Authorization");
        if (token == null) return "UNKNOWN (no token present)";
        return "user identified from token: " + token;
    }

    public static void main(String[] args) {
        Request incomingAtGateway = new Request(Map.of("Authorization", "Bearer abc123"));

        // gateway calls downstream WITHOUT forwarding the token -- the mistake this card addresses
        Request forwardedToDownstream = new Request(Map.of());

        System.out.println("downstream sees: " + identifyUser(forwardedToDownstream));
    }
}
```

How to run: `java TokenRelayLevel1.java`

`forwardedToDownstream` was constructed with an empty headers map, so `identifyUser` reports `"UNKNOWN"` — the downstream service has no way to know who made the original request, even though the original request was perfectly well authenticated at the gateway.

### Level 2 — Intermediate

Add relay: the gateway forwards the exact same token onto its downstream call, letting the downstream service identify the user correctly.

```java
import java.util.*;

public class TokenRelayLevel2 {
    record Request(Map<String, String> headers) {}

    static String identifyUser(Request req) {
        String token = req.headers().get("Authorization");
        if (token == null) return "UNKNOWN (no token present)";
        return "user identified from token: " + token;
    }

    // models the TokenRelay filter -- forwards the SAME Authorization header onto the outbound call
    static Request relayToken(Request incoming) {
        String token = incoming.headers().get("Authorization");
        Map<String, String> outboundHeaders = new HashMap<>();
        if (token != null) outboundHeaders.put("Authorization", token); // IDENTICAL token, forwarded unchanged
        return new Request(outboundHeaders);
    }

    public static void main(String[] args) {
        Request incomingAtGateway = new Request(Map.of("Authorization", "Bearer abc123"));

        Request forwardedToDownstream = relayToken(incomingAtGateway); // relay applied THIS time

        System.out.println("downstream sees: " + identifyUser(forwardedToDownstream));
    }
}
```

How to run: `java TokenRelayLevel2.java`

`relayToken` copies the exact `Authorization` header value from the incoming request onto the outbound request, so `identifyUser` on the downstream side now correctly reports the same token — the token itself was never transformed, decoded, or reissued, purely forwarded byte-for-byte.

### Level 3 — Advanced

Add downstream token validation, including a case where the relayed token has since expired — demonstrating that relay alone doesn't bypass proper validation at each hop; the downstream service still independently checks the token it received.

```java
import java.util.*;

public class TokenRelayLevel3 {
    record Request(Map<String, String> headers) {}
    record Token(String value, long issuedAtMs, long ttlMs) {
        boolean isExpired(long nowMs) { return (nowMs - issuedAtMs) > ttlMs; }
    }

    static Request relayToken(Request incoming) {
        String token = incoming.headers().get("Authorization");
        Map<String, String> outboundHeaders = new HashMap<>();
        if (token != null) outboundHeaders.put("Authorization", token);
        return new Request(outboundHeaders);
    }

    // downstream service independently validates -- relay does NOT exempt it from this
    static String identifyUserWithValidation(Request req, Map<String, Token> tokenStore) {
        String tokenValue = req.headers().get("Authorization");
        if (tokenValue == null) return "REJECTED: no token present";

        Token token = tokenStore.get(tokenValue);
        if (token == null) return "REJECTED: token not recognized";
        if (token.isExpired(System.currentTimeMillis())) return "REJECTED: token EXPIRED";

        return "ACCEPTED: user identified from valid token";
    }

    public static void main(String[] args) throws InterruptedException {
        Map<String, Token> tokenStore = new HashMap<>();
        tokenStore.put("Bearer abc123", new Token("Bearer abc123", System.currentTimeMillis(), 50)); // 50ms TTL

        Request incomingAtGateway = new Request(Map.of("Authorization", "Bearer abc123"));
        Request forwardedToDownstream = relayToken(incomingAtGateway);

        System.out.println("immediately: " + identifyUserWithValidation(forwardedToDownstream, tokenStore));

        Thread.sleep(100); // token's TTL elapses before the downstream call is actually processed

        System.out.println("after delay: " + identifyUserWithValidation(forwardedToDownstream, tokenStore));
    }
}
```

How to run: `java TokenRelayLevel3.java`

The first `identifyUserWithValidation` call succeeds immediately (`"ACCEPTED"`), since the token is still within its `50ms` TTL; after `Thread.sleep(100)` pushes past that TTL, the second call — using the exact same relayed token, unchanged — now returns `"REJECTED: token EXPIRED"`, proving relay only forwards a token faithfully, it never bypasses or short-circuits the receiving service's own independent validation of that token's continued validity.

## 6. Walkthrough

Trace the second (post-delay) `identifyUserWithValidation` call in Level 3.

1. `forwardedToDownstream` still holds `Authorization: "Bearer abc123"`, unchanged since it was relayed — relay itself doesn't re-check or refresh anything, it's a pure forwarding step performed once, at the time of the outbound call.
2. `identifyUserWithValidation(forwardedToDownstream, tokenStore)` extracts `tokenValue = "Bearer abc123"` from the headers.
3. `tokenStore.get("Bearer abc123")` finds the corresponding `Token` object, which was created with `issuedAtMs` set to the time just before the first call and `ttlMs = 50`.
4. `token.isExpired(System.currentTimeMillis())` computes `(now - issuedAtMs) > 50` — because `Thread.sleep(100)` ran in between the two calls, `now - issuedAtMs` is approximately `100`, and `100 > 50` evaluates `true`.
5. Because `isExpired` returns `true`, the method returns `"REJECTED: token EXPIRED"` — this rejection happens entirely within the downstream service's own validation logic, using the token exactly as relayed; the gateway's earlier successful relay of the token had no bearing on this later, independent, time-sensitive validation outcome.

```
t=0ms:   relay forwards "Bearer abc123" unchanged
t=0ms:   downstream validates -> token TTL not yet exceeded -> ACCEPTED
   (100ms elapses)
t=100ms: downstream validates the SAME relayed token again -> TTL (50ms) now exceeded -> REJECTED (expired)
```

## 7. Gotchas & takeaways

> **Gotcha:** Spring Cloud Security's original OAuth2 relay mechanisms (manual `OAuth2FeignRequestInterceptor` beans, `OAuth2RestTemplate`) are legacy and largely superseded — new work should reach for Spring Cloud Gateway's built-in `TokenRelay` filter (for gateway-level relay) or Spring Security's own current OAuth2 resource server / client support (for service-to-service token handling) rather than the original Spring Cloud Security project's now-outdated APIs.

- Token relay's job is narrowly to forward an already-validated access token unchanged onto downstream calls — it is not a mechanism for re-authenticating, transforming, or extending that token's validity in any way.
- Every service receiving a relayed token is still responsible for independently validating it (checking signature, expiry, scope) exactly as if it had received the token directly from the original caller — relay never grants implicit trust that bypasses a downstream service's own validation.
- Modern Spring Cloud Gateway's declarative `TokenRelay` filter (a one-line configuration entry) replaces what used to require hand-written interceptor beans under the legacy Spring Cloud Security project, making relay both simpler to configure and less error-prone to get right.
- Recognizing legacy Spring Cloud Security usage in an existing codebase (imports from `org.springframework.cloud.security.oauth2`, manually-configured `OAuth2RestTemplate` beans) is a useful signal that a modernization pass toward Spring Cloud Gateway's or Spring Security's current OAuth2 support is worth prioritizing.
