---
card: microservices
gi: 180
slug: gateway-security-with-spring-security-oauth2
title: "Gateway security with Spring Security / OAuth2"
---

## 1. What it is

Gateway security with Spring Security and OAuth2 centralizes token validation and authentication at the gateway, using Spring Security's OAuth2 resource server support to validate an incoming request's bearer token (typically a JWT) before the request is ever forwarded to a backend — a concrete Spring implementation of the general [cross-cutting concerns at the gateway](0163-cross-cutting-concerns-at-the-gateway-auth-logging-metrics.md) principle applied specifically to authentication.

## 2. Why & when

Validating a JWT — checking its signature against the issuer's public key, verifying it hasn't expired, confirming required claims are present — is genuinely non-trivial logic that shouldn't be reimplemented, and potentially get subtly wrong, inside every single backend service. Doing it once at the gateway, using Spring Security's well-tested OAuth2 resource server support, means every backend can trust that any request reaching it has already been through this validation, needing at most to trust a simpler, gateway-injected signal (like the authenticated user's identity in a forwarded header) rather than independently re-validating the original token.

Centralize OAuth2 token validation at the gateway whenever the gateway is genuinely the sole entry point for external traffic — the same condition that generally justifies pushing any cross-cutting concern to the edge. For internal service-to-service calls behind the gateway, a different, typically lighter-weight trust mechanism (mutual TLS, a service mesh's own identity system) is usually more appropriate than re-validating the original external token at every hop.

## 3. Core concept

Spring Security's OAuth2 resource server support, configured on the gateway, automatically validates an incoming request's bearer token against the configured identity provider's public key before the request reaches any route's filter chain; a request with a missing, malformed, or expired token is rejected at this stage, before ever being routed to a backend.

```java
// application.yml -- Spring Security automatically validates EVERY request's JWT
spring.security.oauth2.resourceserver.jwt.issuer-uri: https://auth.example.com

@Bean
public SecurityWebFilterChain securityWebFilterChain(ServerHttpSecurity http) {
    return http
        .authorizeExchange(exchanges -> exchanges.anyExchange().authenticated()) // EVERY request requires a valid token
        .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults())) // validated AUTOMATICALLY, before routing
        .build();
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A request with a bearer token is validated by Spring Security's OAuth2 resource server support before it ever reaches the gateway's routing logic; an invalid token is rejected immediately with a 401, while a valid one proceeds to routing and is forwarded to the backend with the authenticated user's identity attached" >
  <rect x="20" y="70" width="120" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="97" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Request + JWT</text>

  <rect x="220" y="60" width="180" height="65" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="82" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Spring Security</text>
  <text x="310" y="98" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">validate signature,</text>
  <text x="310" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">expiry, claims</text>

  <rect x="480" y="20" width="140" height="35" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Route -&gt; backend</text>

  <rect x="480" y="130" width="140" height="35" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="550" y="152" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">401 Unauthorized</text>

  <line x1="140" y1="92" x2="218" y2="92" stroke="#8b949e" marker-end="url(#arr61)"/>
  <line x1="400" y1="80" x2="478" y2="40" stroke="#8b949e" marker-end="url(#arr61)"/>
  <line x1="400" y1="105" x2="478" y2="140" stroke="#8b949e" marker-end="url(#arr61)"/>

  <defs>
    <marker id="arr61" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Token validation happens once, before routing; an invalid token never reaches any backend at all.

## 5. Runnable example

Scenario: an order-gateway that starts with each backend independently and inconsistently validating tokens (showing the duplication risk), centralizes JWT validation at the gateway before any routing occurs, and finally propagates the authenticated user's identity to backends via a trusted header, letting backends make authorization decisions without re-validating the original token themselves.

### Level 1 — Basic

```java
// File: DuplicatedBackendValidation.java -- EACH backend validates tokens
// independently, with subtly inconsistent logic -- the drift risk revisited.
import java.util.*;

public class DuplicatedBackendValidation {
    record Token(String subject, long expiresAtEpochSeconds, String signature) {}

    static boolean orderServiceValidate(Token token) {
        return token.signature().equals("valid-sig") && token.expiresAtEpochSeconds() > System.currentTimeMillis() / 1000; // copy #1
    }
    static boolean customerServiceValidate(Token token) {
        return token.signature().equals("valid-sig"); // copy #2 -- FORGOT to check expiry! Already drifted.
    }

    public static void main(String[] args) {
        Token expiredToken = new Token("user-1", System.currentTimeMillis() / 1000 - 3600, "valid-sig"); // expired an hour ago

        System.out.println("order-service accepts expired token: " + orderServiceValidate(expiredToken));
        System.out.println("customer-service accepts expired token: " + customerServiceValidate(expiredToken) + " (BUG: missing expiry check)");
    }
}
```

**How to run:** `javac DuplicatedBackendValidation.java && java DuplicatedBackendValidation` (JDK 17+).

### Level 2 — Intermediate

```java
// File: CentralizedGatewayValidation.java -- token validation happens ONCE, at
// the gateway, BEFORE routing to ANY backend -- neither backend validates anything itself.
import java.util.*;
import java.util.function.*;

public class CentralizedGatewayValidation {
    record Token(String subject, long expiresAtEpochSeconds, String signature) {}

    static class OAuth2ResourceServerFilter { // mirrors Spring Security's automatic validation
        boolean validate(Token token) {
            boolean signatureValid = token.signature().equals("valid-sig");
            boolean notExpired = token.expiresAtEpochSeconds() > System.currentTimeMillis() / 1000;
            System.out.println("  [gateway security] signature valid=" + signatureValid + ", not expired=" + notExpired);
            return signatureValid && notExpired;
        }
    }

    static class Gateway {
        OAuth2ResourceServerFilter securityFilter = new OAuth2ResourceServerFilter();

        String handleRequest(Token token, String path, Supplier<String> backendCall) {
            if (!securityFilter.validate(token)) {
                return "401 Unauthorized -- rejected BEFORE reaching any backend";
            }
            return backendCall.get(); // backends NEVER see an invalid token -- they don't even need their OWN validation
        }
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();
        Token validToken = new Token("user-1", System.currentTimeMillis() / 1000 + 3600, "valid-sig");
        Token expiredToken = new Token("user-1", System.currentTimeMillis() / 1000 - 3600, "valid-sig");

        System.out.println(gateway.handleRequest(validToken, "/orders/42", () -> "200 OK, order data"));
        System.out.println(gateway.handleRequest(expiredToken, "/orders/42", () -> "200 OK, order data"));
        System.out.println("BOTH order-service AND customer-service now trust the GATEWAY's single validation -- no per-backend drift possible.");
    }
}
```

**How to run:** `javac CentralizedGatewayValidation.java && java CentralizedGatewayValidation` (JDK 17+).

Expected output:
```
  [gateway security] signature valid=true, not expired=true
200 OK, order data
  [gateway security] signature valid=true, not expired=false
401 Unauthorized -- rejected BEFORE reaching any backend
BOTH order-service AND customer-service now trust the GATEWAY's single validation -- no per-backend drift possible.
```

### Level 3 — Advanced

```java
// File: IdentityPropagationViaTrustedHeader.java -- the gateway EXTRACTS the
// authenticated identity from the validated token and forwards it as a TRUSTED
// header; backends make AUTHORIZATION decisions using it, WITHOUT re-validating the original token.
import java.util.*;
import java.util.function.*;

public class IdentityPropagationViaTrustedHeader {
    record Token(String subject, List<String> roles, long expiresAtEpochSeconds, String signature) {}
    record ForwardedRequest(String userIdHeader, List<String> rolesHeader, String path) {} // what the BACKEND actually receives

    static class Gateway {
        boolean validate(Token token) {
            return token.signature().equals("valid-sig") && token.expiresAtEpochSeconds() > System.currentTimeMillis() / 1000;
        }

        String handleRequest(Token token, String path, Function<ForwardedRequest, String> backendHandler) {
            if (!validate(token)) return "401 Unauthorized";

            // extract identity from the VALIDATED token, forward it as TRUSTED headers -- the backend never sees the raw token
            ForwardedRequest forwarded = new ForwardedRequest(token.subject(), token.roles(), path);
            System.out.println("  [gateway] forwarding with X-User-Id=" + forwarded.userIdHeader() + ", X-User-Roles=" + forwarded.rolesHeader());
            return backendHandler.apply(forwarded);
        }
    }

    // BACKEND: makes an AUTHORIZATION decision using the TRUSTED header -- never re-validates a JWT itself
    static String orderServiceHandler(ForwardedRequest request) {
        if (!request.rolesHeader().contains("ORDER_ADMIN")) {
            return "403 Forbidden -- " + request.userIdHeader() + " lacks ORDER_ADMIN role";
        }
        return "200 OK, order data for " + request.userIdHeader();
    }

    public static void main(String[] args) {
        Gateway gateway = new Gateway();
        Token adminToken = new Token("user-1", List.of("ORDER_ADMIN"), System.currentTimeMillis() / 1000 + 3600, "valid-sig");
        Token regularToken = new Token("user-2", List.of("BASIC_USER"), System.currentTimeMillis() / 1000 + 3600, "valid-sig");

        System.out.println(gateway.handleRequest(adminToken, "/orders/42", IdentityPropagationViaTrustedHeader::orderServiceHandler));
        System.out.println(gateway.handleRequest(regularToken, "/orders/42", IdentityPropagationViaTrustedHeader::orderServiceHandler));
        System.out.println("order-service made an AUTHORIZATION decision using ONLY the forwarded, trusted headers -- it never saw or validated a raw JWT.");
    }
}
```

**How to run:** `javac IdentityPropagationViaTrustedHeader.java && java IdentityPropagationViaTrustedHeader` (JDK 17+).

Expected output:
```
  [gateway] forwarding with X-User-Id=user-1, X-User-Roles=[ORDER_ADMIN]
200 OK, order data for user-1
  [gateway] forwarding with X-User-Id=user-2, X-User-Roles=[BASIC_USER]
403 Forbidden -- user-2 lacks ORDER_ADMIN role
order-service made an AUTHORIZATION decision using ONLY the forwarded, trusted headers -- it never saw or validated a raw JWT.
```

## 6. Walkthrough

1. **Level 1** — `orderServiceValidate` checks both signature and expiry, while `customerServiceValidate` checks only signature — a real, demonstrated inconsistency between two independently written validation implementations, and the printed output shows `customer-service` incorrectly accepting an expired token.
2. **Level 2, one validation implementation** — `OAuth2ResourceServerFilter.validate` is the *only* place token validation logic exists; `Gateway.handleRequest` calls it before invoking `backendCall` at all, meaning a failed validation never even reaches the point of attempting a backend call.
3. **Level 2, the observable rejection** — the expired token's request is stopped with `"401 Unauthorized -- rejected BEFORE reaching any backend"`, printed *without* ever calling the `backendCall` supplier — confirmed by the fact that no `"200 OK"` line appears for that request.
4. **Level 2, both backends implicitly protected** — the final printed statement makes explicit that this single gateway-level check now protects every backend uniformly, eliminating the Level 1 drift risk entirely, since no backend performs its own validation anymore.
5. **Level 3, extracting identity from the validated token** — `handleRequest` calls `token.subject()` and `token.roles()` only *after* `validate(token)` has already returned `true`, constructing a `ForwardedRequest` that carries the authenticated identity as plain data (`userIdHeader`, `rolesHeader`) rather than the original token itself.
6. **Level 3, the backend trusting forwarded headers** — `orderServiceHandler` receives a `ForwardedRequest`, not a `Token`; it checks `request.rolesHeader().contains("ORDER_ADMIN")` directly, making an authorization decision using data the gateway has already vouched for, with no JWT signature verification or expiry check happening inside the backend at all.
7. **Level 3, two different authorization outcomes from identical validation** — both `adminToken` and `regularToken` pass the *same* gateway-level `validate` check (both have valid signatures and haven't expired), but `orderServiceHandler` makes two different authorization decisions based on the *forwarded roles* — `user-1`'s `ORDER_ADMIN` role grants access, `user-2`'s `BASIC_USER` role does not — demonstrating the clean separation this pattern establishes: the gateway's job is authentication (is this token genuinely valid, and who does it represent), while each backend's job, using the gateway's trusted output, is its own business-specific authorization (does this specific, now-trusted identity have permission for this specific operation).

## 7. Gotchas & takeaways

> **Gotcha:** forwarding identity via a plain header (`X-User-Id`, `X-User-Roles`) is only safe if backends are absolutely unreachable except through the gateway — if a backend is directly reachable on the internal network by anything other than the gateway, that "trusted" header becomes trivially forgeable by anyone who can reach the backend directly, completely bypassing the gateway's authentication entirely; this pattern requires network-level enforcement (firewall rules, a service mesh's mutual TLS) ensuring backends genuinely cannot be reached except via the gateway, not just an assumption that they won't be.

- Centralizing OAuth2/JWT token validation at the gateway, using Spring Security's resource server support, avoids the inconsistency and duplication risk of every backend implementing its own token validation logic.
- A request with an invalid, expired, or malformed token is rejected at the gateway before it ever reaches any backend service.
- Propagating the authenticated user's identity via trusted, gateway-injected headers lets backends make their own business-specific authorization decisions without needing to re-validate the original token themselves.
- This establishes a clean separation of concerns: the gateway handles authentication (is this token valid, who does it represent), and each backend handles its own authorization (does this identity have permission for this specific operation).
- This trust model is only sound if backends are genuinely unreachable except through the gateway — network-level enforcement of that boundary is required, not just an assumption that no one will bypass it.
