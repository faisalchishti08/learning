---
card: microservices
gi: 485
slug: ingress-egress-gateways
title: "Ingress & egress gateways"
---

## 1. What it is

An **ingress gateway** is a dedicated entry point through which all traffic entering the mesh from outside must pass, applying the mesh's traffic management, security, and observability to external requests before they reach any internal service. An **egress gateway** is its mirror: a dedicated exit point through which the mesh routes all traffic leaving it toward external destinations, letting the mesh apply policy (which external hosts are even allowed, TLS origination, monitoring) to outbound calls as deliberately as it does to internal ones.

## 2. Why & when

You deploy dedicated gateways at the mesh's boundary because internal service-to-service traffic and boundary-crossing traffic have genuinely different concerns:

- **A single, well-defined entry point is easier to secure and monitor than every service exposing itself directly.** Rather than every service potentially being reachable from outside the cluster, only the ingress gateway is — internal services only ever need to trust traffic that's already passed through it.
- **Uncontrolled egress is a real security and cost risk.** Without an egress gateway, any compromised or misconfigured service inside the mesh could make arbitrary outbound calls to any external destination; routing all outbound traffic through a controlled gateway lets you enforce an allowlist of permitted external hosts.
- **Centralizing boundary-crossing traffic gives you one place to apply TLS origination, rate limiting, and detailed audit logging** for exactly the traffic that's most exposed to the outside world — rather than needing every individual service to implement these controls consistently on its own.
- **You deploy these gateways as part of the mesh's baseline architecture**, essentially from the start of any production mesh deployment — they're not an advanced afterthought, they're the standard, expected boundary control points.

## 3. Core concept

Think of a secure office building with exactly one staffed front entrance (ingress gateway) that every visitor must pass through — no side doors letting people walk directly into random offices — and exactly one loading dock (egress gateway) through which every outbound shipment must be logged and inspected, rather than employees being able to walk packages out through any random exit whenever they like.

Concretely:

1. **The ingress gateway is the only entry point exposed outside the mesh** — external clients connect to it, and it applies routing rules to direct requests to the correct internal service, along with TLS termination, authentication, and rate limiting at that single boundary point.
2. **Internal services never need to be individually exposed** to the outside world; they only receive traffic that's already been routed and validated by the ingress gateway.
3. **The egress gateway is the designated path for outbound calls to external destinations** — internal services route their calls to external systems through it rather than connecting directly.
4. **Egress policy (an allowlist of permitted external hosts, TLS origination for calls to external HTTPS services) is enforced centrally at the gateway**, rather than trusting every individual service to handle outbound security correctly on its own.
5. **Both gateways get the same observability benefits as internal mesh traffic** — since all boundary-crossing traffic passes through one well-defined point, monitoring exactly what's entering and leaving the mesh becomes straightforward.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="External clients enter through the ingress gateway to reach internal services; internal services exit through the egress gateway to reach external destinations" >
  <rect x="20" y="80" width="130" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">external client</text>

  <rect x="180" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="250" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ingress gateway</text>

  <rect x="360" y="20" width="120" height="160" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="420" y="105" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">internal services (mesh)</text>

  <rect x="510" y="80" width="140" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="580" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">egress gateway</text>

  <line x1="150" y1="105" x2="180" y2="105" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="320" y1="105" x2="360" y2="105" stroke="#6db33f" marker-end="url(#a1)"/>
  <line x1="480" y1="105" x2="510" y2="105" stroke="#f0883e" marker-end="url(#a1)"/>

  <text x="580" y="180" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-&gt; allowed external hosts only</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Inbound traffic funnels through the ingress gateway; outbound traffic funnels through the egress gateway — internal services never connect directly across the boundary.

## 5. Runnable example

Scenario: a gateway layer enforcing entry and exit rules for a mesh. We start with a basic ingress routing rule, extend it to egress with an allowlist of permitted external hosts, then handle the hard case: an internal service attempting to reach an external host not on the allowlist, which must be blocked at the egress gateway rather than silently allowed through.

### Level 1 — Basic

```java
// File: IngressGatewayBasic.java -- models the INGRESS gateway routing an
// EXTERNAL request to the correct INTERNAL service -- the only entry
// point exposed outside the mesh.
import java.util.*;

public class IngressGatewayBasic {
    static Map<String, String> routingRules = Map.of(
        "/api/orders", "order-service",
        "/api/inventory", "inventory-service"
    );

    static String ingressRoute(String path) {
        String target = routingRules.get(path);
        if (target == null) {
            System.out.println("[ingress gateway] no route for " + path + " -- REJECTED");
            return null;
        }
        System.out.println("[ingress gateway] routing external request " + path + " -> internal service: " + target);
        return target;
    }

    public static void main(String[] args) {
        ingressRoute("/api/orders");
    }
}
```

How to run: `java IngressGatewayBasic.java`

`ingressRoute` is the single point external traffic passes through — `routingRules` maps external-facing paths to internal service names, and any path not present is rejected outright rather than being forwarded blindly, modeling the ingress gateway as the sole, controlled entry point into the mesh.

### Level 2 — Intermediate

```java
// File: EgressGatewayAllowlist.java -- the SAME gateway concept, now for
// EGRESS: internal services route OUTBOUND calls through the egress
// gateway, which checks each destination against an ALLOWLIST of
// permitted external hosts.
import java.util.*;

public class EgressGatewayAllowlist {
    static Set<String> allowedExternalHosts = Set.of(
        "api.stripe.com",
        "api.shipping-partner.com"
    );

    static boolean egressAllow(String callingService, String externalHost) {
        boolean allowed = allowedExternalHosts.contains(externalHost);
        if (allowed) {
            System.out.println("[egress gateway] " + callingService + " -> " + externalHost + " ALLOWED (on allowlist)");
        } else {
            System.out.println("[egress gateway] " + callingService + " -> " + externalHost + " BLOCKED (not on allowlist)");
        }
        return allowed;
    }

    public static void main(String[] args) {
        egressAllow("payment-service", "api.stripe.com");
        egressAllow("order-service", "some-random-external-api.com");
    }
}
```

How to run: `java EgressGatewayAllowlist.java`

`egressAllow` checks every outbound destination against `allowedExternalHosts` before permitting the call — `api.stripe.com` is on the list and is allowed, while `some-random-external-api.com` isn't and is blocked, modeling how the egress gateway enforces a deliberate, centrally-managed boundary on what internal services are permitted to reach outside the mesh.

### Level 3 — Advanced

```java
// File: EgressGatewayBlockedAttempt.java -- the SAME allowlist
// enforcement, now handling the PRODUCTION-FLAVORED hard case: a service
// is COMPROMISED or MISCONFIGURED and attempts to exfiltrate data to an
// UNKNOWN external host. The egress gateway must BLOCK the call
// completely -- the call must never actually reach the network -- and
// log the attempt clearly for security review, rather than merely
// warning while still letting the call through.
import java.util.*;

public class EgressGatewayBlockedAttempt {
    static Set<String> allowedExternalHosts = Set.of(
        "api.stripe.com",
        "api.shipping-partner.com"
    );

    static List<String> securityAuditLog = new ArrayList<>();

    // Simulates the actual network call -- MUST NOT be reached for a blocked destination.
    static String makeActualNetworkCall(String host, String payload) {
        System.out.println("[network] ACTUALLY sent data to " + host + ": " + payload);
        return "external response from " + host;
    }

    static String egressGatewayHandle(String callingService, String externalHost, String payload) {
        if (!allowedExternalHosts.contains(externalHost)) {
            String auditEntry = "BLOCKED: " + callingService + " attempted to reach " + externalHost + " (not on allowlist)";
            securityAuditLog.add(auditEntry);
            System.out.println("[egress gateway] " + auditEntry);
            throw new SecurityException("egress blocked: " + externalHost + " is not an allowed external destination");
        }
        System.out.println("[egress gateway] " + callingService + " -> " + externalHost + " ALLOWED, forwarding");
        return makeActualNetworkCall(externalHost, payload);
    }

    public static void main(String[] args) {
        System.out.println("--- legitimate call: payment-service -> api.stripe.com ---");
        egressGatewayHandle("payment-service", "api.stripe.com", "charge-request");

        System.out.println();
        System.out.println("--- suspicious call: a misconfigured service tries to reach an unknown host ---");
        try {
            egressGatewayHandle("order-service", "unknown-exfiltration-target.evil.com", "customer-data-dump");
        } catch (SecurityException e) {
            System.out.println("[order-service] call failed: " + e.getMessage());
        }

        System.out.println();
        System.out.println("[security review] audit log: " + securityAuditLog);
    }
}
```

How to run: `java EgressGatewayBlockedAttempt.java`

`egressGatewayHandle` checks `allowedExternalHosts` *before* ever calling `makeActualNetworkCall` — for the blocked destination, the `if` branch throws a `SecurityException` and returns immediately, meaning `makeActualNetworkCall` is never invoked at all for that attempt, so no data ever actually reaches the network. The blocked attempt is also recorded into `securityAuditLog`, giving a security team a clear, centralized record of exactly which service tried to reach exactly which unauthorized destination.

## 6. Walkthrough

Trace `EgressGatewayBlockedAttempt.main` in order. **First**, the legitimate call runs `egressGatewayHandle("payment-service", "api.stripe.com", "charge-request")`. The `if` check finds `"api.stripe.com"` present in `allowedExternalHosts`, so the condition is `false` and the block branch is skipped entirely — the allowed message prints, and `makeActualNetworkCall` runs, actually "sending" the payload and returning a response.

**Next**, the suspicious call runs `egressGatewayHandle("order-service", "unknown-exfiltration-target.evil.com", "customer-data-dump")`. The `if` check finds this host absent from `allowedExternalHosts`, so the condition is `true` — the block branch executes: it constructs an audit entry, appends it to `securityAuditLog`, prints the block message, and throws `SecurityException`.

**Then**, because that exception is thrown from inside the `if` block, execution never reaches the "ALLOWED, forwarding" line or the call to `makeActualNetworkCall` for this attempt — no data of any kind is sent anywhere, and no "network" output line appears for the blocked host anywhere in the transcript.

**After that**, back in `main`, the `try`/`catch` surrounding the suspicious call catches the `SecurityException` and prints the failure message from `order-service`'s point of view — the calling service receives a clear rejection rather than any indication of partial success.

**Finally**, `main` prints `securityAuditLog`, which contains exactly one entry — the blocked attempt — giving a security reviewer a precise, centralized record of the incident: which service attempted the call, which destination it tried to reach, and why it was blocked, all captured at the one chokepoint every outbound call is required to pass through.

```
--- legitimate call: payment-service -> api.stripe.com ---
[egress gateway] payment-service -> api.stripe.com ALLOWED, forwarding
[network] ACTUALLY sent data to api.stripe.com: charge-request

--- suspicious call: a misconfigured service tries to reach an unknown host ---
[egress gateway] BLOCKED: order-service attempted to reach unknown-exfiltration-target.evil.com (not on allowlist)
[order-service] call failed: egress blocked: unknown-exfiltration-target.evil.com is not an allowed external destination

[security review] audit log: [BLOCKED: order-service attempted to reach unknown-exfiltration-target.evil.com (not on allowlist)]
```

## 7. Gotchas & takeaways

> An egress "gateway" that merely logs a warning while still letting the outbound call proceed provides observability but no actual protection — a genuinely compromised service could still exfiltrate data to an attacker-controlled host, just with a log entry left behind after the fact. A real egress control must block the call outright, as demonstrated here, not just note that it happened.
- The ingress gateway being the *only* exposed entry point is what makes internal services safe to trust traffic from without each one re-implementing authentication and validation independently — that trust boundary only holds if there truly are no other paths in.
- An egress allowlist should be as narrow as the application's genuine needs — a service that only ever calls a payment processor and a shipping partner should never be permitted to reach arbitrary external hosts, regardless of what it might request.
- Both gateways get the same [mesh-level observability](0483-mesh-level-observability-telemetry.md) benefits as internal traffic — since every boundary-crossing request passes through one well-known point, monitoring exactly what enters and leaves the mesh becomes centralized rather than scattered.
- Gateways are a natural place to enforce mesh-wide policies that don't make sense to apply internally — rate limiting external clients, requiring API keys at the ingress boundary, or requiring TLS origination for calls to external HTTPS services at the egress boundary.
