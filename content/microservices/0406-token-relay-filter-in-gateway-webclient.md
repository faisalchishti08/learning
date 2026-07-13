---
card: microservices
gi: 406
slug: token-relay-filter-in-gateway-webclient
title: "Token relay filter in gateway / WebClient"
---

## 1. What it is

The **token relay filter** is the concrete Spring mechanism that forwards a caller's access token from the gateway (or any Spring service acting as an OAuth2 client) onward to downstream services, so those services can validate the *original* caller's identity rather than treating every gateway-forwarded request as coming from the gateway itself. In [Spring Cloud Gateway](0405-spring-cloud-gateway-spring-security-at-the-edge.md), this is the `TokenRelay=` route filter; in a general Spring service making outbound calls with `WebClient`, it's an `ExchangeFilterFunction` (`ServletBearerExchangeFilterFunction` or its reactive equivalent) that attaches the stored access token automatically to every outgoing request.

## 2. Why & when

You reach for token relay specifically to avoid two bad alternatives: forcing every downstream service to re-authenticate the user from scratch (impossible for a machine-to-machine hop with no login UI), or having the gateway silently act as an anonymous, unauthenticated proxy once past the edge (losing all caller-identity information downstream services need for authorization decisions):

- **Downstream authorization needs the original caller's identity and scopes**, not just "a request arrived from the trusted gateway" — [`@PreAuthorize`](0404-method-security-preauthorize-postauthorize.md)-style ownership checks and [scoped authorization](0395-scopes-roles-fine-grained-authorization.md) both depend on knowing *who* is actually asking.
- **It avoids re-implementing authentication at every hop.** The gateway (or an upstream client) already did the work of validating who the caller is via [OAuth2 login](0402-spring-security-oauth2-client-login-token-relay.md); relaying that proof forward means downstream services can validate the same token as a plain [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md) call, no special-casing required.
- **It preserves audit trails.** Logs and traces downstream can attribute an action to the actual end user, not an anonymized "the gateway did it," which matters for compliance and incident investigation.
- **You need this any time a request crosses a service boundary and the receiving service needs to make its own authorization decision** based on who originally made the call — this connects directly to [token relay / propagation](0389-token-relay-propagation-between-services.md), the conceptual version of this exact mechanism.

## 3. Core concept

Think of the token relay filter as a relay race baton handoff: the gateway (first runner) already proved it's in the race by presenting its own credentials to start, but the baton it's carrying — the caller's access token — is what actually gets checked at each subsequent leg. The gateway doesn't run the whole race pretending to *be* the original caller; it hands off the exact same baton, unmodified, so every downstream checkpoint sees precisely who started the race.

The essential pieces:

1. **`TokenRelay=` gateway filter** — a built-in Spring Cloud Gateway `GatewayFilter` that reads the current request's access token (obtained via `oauth2Login` or already present as a bearer token) and attaches it as the `Authorization` header on the outbound, routed request.

```yaml
spring:
  cloud:
    gateway:
      routes:
        - id: orders-route
          uri: lb://order-service
          predicates:
            - Path=/orders/**
          filters:
            - TokenRelay=
```

```java
// Programmatic equivalent, via a RouteLocator bean:
@Bean
public RouteLocator routes(RouteLocatorBuilder builder) {
    return builder.routes()
        .route("orders", r -> r.path("/orders/**")
            .filters(f -> f.tokenRelay())
            .uri("lb://order-service"))
        .build();
}
```

2. **`ServletOAuth2AuthorizedClientExchangeFilterFunction`** — the servlet-side equivalent for a plain Spring service (not a gateway) making outbound `WebClient` calls; it retrieves the caller's stored access token from the `OAuth2AuthorizedClientRepository` (see [Spring Security OAuth2 Client](0402-spring-security-oauth2-client-login-token-relay.md)) and attaches it automatically.

```java
@Bean
public WebClient webClient(OAuth2AuthorizedClientManager manager) {
    ServletOAuth2AuthorizedClientExchangeFilterFunction oauth2 =
            new ServletOAuth2AuthorizedClientExchangeFilterFunction(manager);
    return WebClient.builder().apply(oauth2.oauth2Configuration()).build();
}
```

3. **Token relay is transparent to calling code.** Once configured, a controller or service method calling `webClient.get().uri("http://inventory-service/items").retrieve()` doesn't manually attach any header — the filter function intercepts the outbound exchange and adds `Authorization: Bearer <token>` automatically.
4. **Relay is not the same as re-issuing a new, narrower token.** A raw token relay forwards the *exact* token the caller presented, scopes and all — which is simple but means every downstream hop implicitly trusts the same broad token. More advanced setups use token exchange to mint a narrower, service-specific token per hop, but that's a deliberate extra step beyond plain relay.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caller presents a bearer token to the gateway; the gateway's TokenRelay filter reattaches the same token unmodified to the outbound request to order-service, which then relays it again via WebClient to inventory-service, so every hop sees the same original caller identity" font-family="sans-serif">
  <rect x="10" y="80" width="90" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="55" y="100" fill="#e6edf3" font-size="9" text-anchor="middle">Caller</text>
  <text x="55" y="115" fill="#8b949e" font-size="8" text-anchor="middle">Bearer tok-A</text>

  <rect x="150" y="80" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="210" y="100" fill="#e6edf3" font-size="9" text-anchor="middle">Gateway</text>
  <text x="210" y="115" fill="#8b949e" font-size="8" text-anchor="middle">TokenRelay=</text>

  <rect x="320" y="80" width="120" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="380" y="100" fill="#e6edf3" font-size="9" text-anchor="middle">order-service</text>
  <text x="380" y="115" fill="#8b949e" font-size="8" text-anchor="middle">WebClient relay</text>

  <rect x="490" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="560" y="100" fill="#e6edf3" font-size="9" text-anchor="middle">inventory-service</text>
  <text x="560" y="115" fill="#8b949e" font-size="8" text-anchor="middle">validates tok-A directly</text>

  <line x1="100" y1="105" x2="150" y2="105" stroke="#8b949e" marker-end="url(#tr)"/>
  <line x1="270" y1="105" x2="320" y2="105" stroke="#6db33f" marker-end="url(#tr)"/>
  <line x1="440" y1="105" x2="490" y2="105" stroke="#6db33f" marker-end="url(#tr)"/>
  <text x="380" y="60" fill="#6db33f" font-size="9" text-anchor="middle">same Bearer tok-A relayed unmodified at every hop</text>

  <defs>
    <marker id="tr" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Plain token relay forwards the same bearer token unchanged at every hop, so every downstream service sees the same original caller identity without re-authentication.

## 5. Runnable example

Scenario: a gateway relaying a caller's token through `order-service` to `inventory-service`. We model manual, ad hoc header forwarding first (showing what's easy to get wrong), then a proper token-relay filter abstraction, then a chain of relays across two hops with a check that catches a token accidentally being dropped mid-chain.

### Level 1 — Basic

```java
// File: ManualHeaderForwarding.java -- forwarding the token by hand, ad hoc,
// with no dedicated abstraction -- easy to forget on any new outbound call.
import java.util.*;

public class ManualHeaderForwarding {
    static Map<String, String> callDownstream(String path, Map<String, String> incomingHeaders) {
        Map<String, String> outgoingHeaders = new HashMap<>();
        // Someone has to REMEMBER to copy this header on every single outbound call.
        if (incomingHeaders.containsKey("Authorization")) {
            outgoingHeaders.put("Authorization", incomingHeaders.get("Authorization"));
        }
        System.out.println("Calling " + path + " with headers: " + outgoingHeaders);
        return outgoingHeaders;
    }

    public static void main(String[] args) {
        Map<String, String> incoming = Map.of("Authorization", "Bearer tok-A");
        callDownstream("http://order-service/orders", incoming);

        // A DIFFERENT call site, written by someone else, FORGOT to forward the header:
        Map<String, String> forgotten = new HashMap<>();
        System.out.println("Second call (bug): " + callDownstream("http://inventory-service/items", forgotten));
    }
}
```

How to run: `java ManualHeaderForwarding.java`

`callDownstream` only forwards `Authorization` because this particular implementation remembered to copy it — but the second, independent call site never received the header at all, silently making an unauthenticated (or effectively anonymous) call. This is exactly the class of bug a dedicated `TokenRelay=` filter or `ExchangeFilterFunction` exists to eliminate: relay becomes automatic infrastructure instead of something every developer must remember at every call site.

### Level 2 — Intermediate

```java
// File: TokenRelayFilterAbstraction.java -- a dedicated, REUSABLE relay
// filter function, applied automatically to every outbound call -- mirroring
// how ServletOAuth2AuthorizedClientExchangeFilterFunction or Spring Cloud
// Gateway's TokenRelay= filter attach the header without per-call-site code.
import java.util.*;
import java.util.function.*;

public class TokenRelayFilterAbstraction {
    interface OutboundCall { Map<String, String> apply(String path, Map<String, String> headers); }

    // The relay filter: wraps ANY outbound call and guarantees the token is attached.
    static OutboundCall withTokenRelay(OutboundCall inner, Supplier<String> currentCallerToken) {
        return (path, baseHeaders) -> {
            Map<String, String> headers = new HashMap<>(baseHeaders);
            String token = currentCallerToken.get();
            if (token != null) {
                headers.put("Authorization", "Bearer " + token);
            }
            return inner.apply(path, headers);
        };
    }

    static Map<String, String> rawCall(String path, Map<String, String> headers) {
        System.out.println("Calling " + path + " with headers: " + headers);
        return headers;
    }

    public static void main(String[] args) {
        String requestScopedToken = "tok-A"; // stands in for the ThreadLocal / reactive context holding the current request's token
        OutboundCall call = withTokenRelay(TokenRelayFilterAbstraction::rawCall, () -> requestScopedToken);

        // EVERY call site automatically gets the token relayed -- no per-call-site code needed.
        call.apply("http://order-service/orders", Map.of());
        call.apply("http://inventory-service/items", Map.of());
    }
}
```

How to run: `java TokenRelayFilterAbstraction.java`

`withTokenRelay` wraps any `OutboundCall` and injects the current request's token via `currentCallerToken`, a stand-in for how real Spring Security stores the current request's authentication in a thread-local (servlet) or reactive context (WebFlux) that the filter function reads automatically. Both `call.apply(...)` invocations now carry `Authorization: Bearer tok-A` without either call site writing any header-copying code — exactly the guarantee `TokenRelay=` and `ServletOAuth2AuthorizedClientExchangeFilterFunction` provide in a real Spring application: relay is infrastructure, not per-developer discipline.

### Level 3 — Advanced

```java
// File: ChainedRelayWithDropDetection.java -- relays the SAME token across
// TWO hops (gateway -> order-service -> inventory-service), and adds
// verification that the token survives the whole chain intact -- catching
// the real production bug of an intermediate service accidentally
// stripping or replacing the Authorization header (e.g. its own outbound
// WebClient config overwrote it instead of relaying).
import java.util.*;
import java.util.function.*;

public class ChainedRelayWithDropDetection {
    record Hop(String serviceName, Map<String, String> receivedHeaders) {}

    static final List<Hop> TRACE = new ArrayList<>();

    interface OutboundCall { Map<String, String> apply(String serviceName, Map<String, String> headers); }

    static OutboundCall withTokenRelay(OutboundCall inner) {
        return (serviceName, incomingHeaders) -> {
            Map<String, String> outgoing = new HashMap<>(incomingHeaders); // relay EXACTLY what arrived
            return inner.apply(serviceName, outgoing);
        };
    }

    // A BUGGY hop that builds a fresh header map instead of relaying -- simulates a
    // misconfigured WebClient bean that doesn't apply the relay filter function.
    static OutboundCall brokenHop(OutboundCall inner) {
        return (serviceName, incomingHeaders) -> inner.apply(serviceName, new HashMap<>()); // drops everything!
    }

    static Map<String, String> receive(String serviceName, Map<String, String> headers) {
        TRACE.add(new Hop(serviceName, headers));
        System.out.println("[" + serviceName + "] received headers: " + headers);
        return headers;
    }

    static void verifyChainIntegrity(String expectedToken) {
        for (Hop hop : TRACE) {
            String header = hop.receivedHeaders().get("Authorization");
            boolean intact = ("Bearer " + expectedToken).equals(header);
            System.out.println("  " + hop.serviceName() + ": token intact = " + intact
                    + (intact ? "" : " <-- RELAY BROKEN HERE"));
        }
    }

    public static void main(String[] args) {
        Map<String, String> callerHeaders = Map.of("Authorization", "Bearer tok-A");

        // Healthy chain: gateway -> order-service, relay works correctly.
        OutboundCall gatewayToOrders = withTokenRelay(h -> receive("order-service", h));
        Map<String, String> atOrderService = gatewayToOrders.apply("order-service", callerHeaders);

        // Broken chain: order-service -> inventory-service, relay filter misconfigured.
        OutboundCall ordersToInventoryBroken = brokenHop(h -> receive("inventory-service", h));
        ordersToInventoryBroken.apply("inventory-service", atOrderService);

        System.out.println("Verifying chain integrity:");
        verifyChainIntegrity("tok-A");
    }
}
```

How to run: `java ChainedRelayWithDropDetection.java`

`gatewayToOrders` uses the correct `withTokenRelay` wrapper, so `order-service` receives the full `Authorization` header intact — recorded as a `Hop` in `TRACE`. `ordersToInventoryBroken` uses `brokenHop`, which deliberately builds a fresh, empty header map instead of relaying the incoming one, simulating a real bug: a `WebClient` bean at `order-service` that wasn't configured with the token-relay `ExchangeFilterFunction`, so it silently makes an unauthenticated call to `inventory-service`. `verifyChainIntegrity` walks the recorded `TRACE` and checks, hop by hop, whether the expected token survived — flagging exactly where the chain broke, which is the kind of check worth building into contract or integration tests for a multi-hop relay chain.

## 6. Walkthrough

Trace `ChainedRelayWithDropDetection.main`. **First**, `callerHeaders` is set up with `Authorization: Bearer tok-A`, representing what the original caller presented to the gateway. `gatewayToOrders.apply("order-service", callerHeaders)` runs: inside `withTokenRelay`'s lambda, `outgoing` is built as a copy of `incomingHeaders` — still containing `Authorization: Bearer tok-A` — and passed to `inner.apply(...)`, which is `receive("order-service", h)`. `receive` records a `Hop("order-service", {Authorization: Bearer tok-A})` in `TRACE` and prints it. The return value, `atOrderService`, still carries the token.

**Next**, `ordersToInventoryBroken.apply("inventory-service", atOrderService)` runs. Inside `brokenHop`'s lambda, `incomingHeaders` (which is `atOrderService`, carrying the token) is **ignored** — a fresh, empty `HashMap` is passed to `inner.apply(...)` instead. `receive("inventory-service", {})` records a `Hop("inventory-service", {})` with no `Authorization` header at all, and prints an empty header map.

**Then**, `main` prints "Verifying chain integrity:" and calls `verifyChainIntegrity("tok-A")`, which iterates `TRACE`. For the `"order-service"` hop, `hop.receivedHeaders().get("Authorization")` is `"Bearer tok-A"`, matching `"Bearer " + "tok-A"` exactly — `intact` is `true`.

**Finally**, for the `"inventory-service"` hop, `hop.receivedHeaders().get("Authorization")` is `null` (the map was empty), which does not equal `"Bearer tok-A"` — `intact` is `false`, and the output flags `"<-- RELAY BROKEN HERE"`, pinpointing exactly which hop in the chain dropped the token.

```
[order-service] received headers: {Authorization=Bearer tok-A}
[inventory-service] received headers: {}
Verifying chain integrity:
  order-service: token intact = true
  inventory-service: token intact = false <-- RELAY BROKEN HERE
```

Sample HTTP shapes across the healthy vs. broken hop:

```
GET /orders/42 HTTP/1.1
Authorization: Bearer tok-A          <- gateway relayed this to order-service correctly

GET /items/7 HTTP/1.1
(no Authorization header at all)     <- order-service's broken WebClient dropped it before calling inventory-service

HTTP/1.1 401 Unauthorized             <- inventory-service correctly rejects the now-anonymous call
```

## 7. Gotchas & takeaways

> `TokenRelay=` and `ServletOAuth2AuthorizedClientExchangeFilterFunction` only work automatically when the outbound call actually goes through the configured `WebClient`/`RouteLocator` — a service that builds its own raw `HttpClient` or a second, unconfigured `WebClient` bean for "just this one call" silently bypasses relay entirely, producing exactly the broken-chain scenario in Level 3, often discovered only when a downstream service starts logging unexpected `401`s.

- Token relay forwards the *same* bearer token unmodified at every hop — simple and effective, but every downstream service that receives it implicitly trusts the same scopes the original caller had, which is worth reviewing for services that shouldn't see the caller's full privilege set.
- Centralizing relay in a filter function (`TokenRelay=`, `ExchangeFilterFunction`) removes the "did every developer remember to forward the header" risk that plain manual forwarding carries.
- A dropped or overwritten `Authorization` header mid-chain is a real, common production bug — usually caused by a misconfigured or bypassed `WebClient` bean — and is worth explicit integration-test coverage, not just assumed to work because it worked once.
- This mechanism is the concrete implementation of [token relay / propagation](0389-token-relay-propagation-between-services.md), building on the login/token-acquisition side covered in [Spring Security OAuth2 Client](0402-spring-security-oauth2-client-login-token-relay.md) and the edge routing covered in [Spring Cloud Gateway + Spring Security at the edge](0405-spring-cloud-gateway-spring-security-at-the-edge.md).
- Downstream services still validate the relayed token independently as resource servers (see [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md)) — relay forwards the credential, it does not itself grant trust; the receiving service's own signature/audience checks are still what matters.
