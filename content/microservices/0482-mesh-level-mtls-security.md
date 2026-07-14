---
card: microservices
gi: 482
slug: mesh-level-mtls-security
title: "Mesh-level mTLS & security"
---

## 1. What it is

**Mesh-level mTLS (mutual TLS)** means every service-to-service connection in the mesh is automatically encrypted and mutually authenticated — both sides present a certificate proving their identity, not just the server side as in ordinary TLS — with certificate issuance, rotation, and verification handled entirely by the mesh's [sidecar proxies](0479-sidecar-proxy-envoy.md) and [control plane](0478-data-plane-vs-control-plane.md). No application ever writes TLS-handling code; the encryption and identity verification happen transparently at the proxy layer.

## 2. Why & when

You enable mesh-level mTLS whenever you need strong, consistent service-to-service security without relying on every team to implement it correctly themselves:

- **Ordinary TLS only authenticates the server; mTLS authenticates both sides.** In a microservices system, you often need to know not just "is this really `inventory-service`'s server" but also "is this caller really `order-service`, and not something else that got network access" — mTLS proves both identities cryptographically.
- **Manually configuring TLS correctly, consistently, everywhere is error-prone at scale.** Certificate generation, distribution, rotation before expiry, and verification logic implemented separately in every service is a lot of surface area for something to be misconfigured — a mesh centralizes this into one correctly-implemented mechanism applied uniformly.
- **Zero-trust network architectures require verified identity on every connection, not just perimeter security.** A mesh with mTLS enforced means even traffic *inside* the cluster, between services that might have once been trusted implicitly, is authenticated on every single hop.
- **You want this enabled by default across the mesh**, essentially without exception in any production deployment — the operational cost of running it is largely absorbed by the mesh's automation, while the security benefit applies uniformly to every service.

## 3. Core concept

Think of a high-security building where every door checks not just that whoever's entering has a badge (like ordinary TLS checking a server has a certificate) but also that the badge holder is who they claim to be via a second verification step (mTLS's mutual check) — and where the building's own security office (the control plane) issues, tracks, and periodically reissues everyone's badges automatically, rather than each department managing its own employees' badges independently.

Concretely:

1. **The control plane acts as a certificate authority**, issuing a unique identity certificate to every service (or every proxy, representing a service) in the mesh.
2. **When one proxy initiates a connection to another, both sides present their certificates during the TLS handshake** — the initiating proxy verifies the destination's identity, and the destination verifies the initiator's identity, both directions checked before any application data flows.
3. **Certificates are short-lived and automatically rotated** by the control plane, well before expiry — reducing the blast radius of a leaked certificate, since it becomes useless soon regardless.
4. **The entire process is invisible to application code** — an application makes a plain, unencrypted-looking call to its local sidecar; the sidecar-to-sidecar hop is where the actual mTLS handshake and encryption happens.
5. **Authorization policies can build on top of verified identity** — "only `order-service` may call `payment-service`'s `/charge` endpoint," enforced because the mesh knows, cryptographically, exactly which service is making each call.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two sidecar proxies perform a mutual TLS handshake, each presenting and verifying a certificate, before encrypted application traffic flows between them" >
  <rect x="20" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">order-service</text>
  <text x="100" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">sidecar (cert: order-svc)</text>

  <rect x="460" y="70" width="160" height="60" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="540" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">payment-service</text>
  <text x="540" y="112" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">sidecar (cert: payment-svc)</text>

  <line x1="180" y1="90" x2="460" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <text x="320" y="80" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">presents cert -&gt;</text>
  <line x1="460" y1="110" x2="180" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#a1)"/>
  <text x="320" y="128" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">&lt;- presents cert, both verified</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#6db33f"/></marker>
  </defs>
</svg>

Both proxies present certificates and verify each other's identity before any application data flows between them.

## 5. Runnable example

Scenario: a proxy-to-proxy mTLS handshake and identity-based authorization check. We start with a basic one-directional certificate check, extend it to true mutual verification (both sides checked), then handle the hard case: an authorization policy that allows a verified identity to call one endpoint but denies it for another, enforced only after mTLS identity has already been established.

### Level 1 — Basic

```java
// File: MtlsBasic.java -- models a ONE-DIRECTIONAL certificate check --
// the caller verifying the destination's identity, like ordinary TLS.
public class MtlsBasic {
    record Certificate(String serviceName, boolean validAndTrusted) {}

    static boolean verifyServerCertificate(Certificate serverCert) {
        if (!serverCert.validAndTrusted()) {
            System.out.println("[order-service sidecar] REJECTED: server certificate for '" + serverCert.serviceName() + "' is not trusted");
            return false;
        }
        System.out.println("[order-service sidecar] server identity verified: " + serverCert.serviceName());
        return true;
    }

    public static void main(String[] args) {
        Certificate paymentServiceCert = new Certificate("payment-service", true);
        boolean trusted = verifyServerCertificate(paymentServiceCert);
        System.out.println("[order-service sidecar] connection allowed: " + trusted);
    }
}
```

How to run: `java MtlsBasic.java`

`verifyServerCertificate` models the caller's side checking the destination's certificate — a single-direction check, exactly what ordinary (non-mutual) TLS provides, before extending to true mutual verification in the next level.

### Level 2 — Intermediate

```java
// File: MtlsMutual.java -- the SAME certificate check, now applied
// MUTUALLY -- both the caller's AND the destination's identities are
// verified before the connection is allowed, matching real mTLS.
public class MtlsMutual {
    record Certificate(String serviceName, boolean validAndTrusted) {}

    static boolean verifyCertificate(String verifierName, Certificate presentedCert) {
        if (!presentedCert.validAndTrusted()) {
            System.out.println("[" + verifierName + "] REJECTED: certificate for '" + presentedCert.serviceName() + "' is not trusted");
            return false;
        }
        System.out.println("[" + verifierName + "] verified identity: " + presentedCert.serviceName());
        return true;
    }

    static boolean establishMtlsConnection(Certificate callerCert, Certificate serverCert) {
        boolean serverVerifiedByCaller = verifyCertificate("order-service sidecar", serverCert);
        boolean callerVerifiedByServer = verifyCertificate("payment-service sidecar", callerCert);
        return serverVerifiedByCaller && callerVerifiedByServer;
    }

    public static void main(String[] args) {
        Certificate orderServiceCert = new Certificate("order-service", true);
        Certificate paymentServiceCert = new Certificate("payment-service", true);

        boolean established = establishMtlsConnection(orderServiceCert, paymentServiceCert);
        System.out.println("[mesh] mTLS connection established: " + established);
    }
}
```

How to run: `java MtlsMutual.java`

`establishMtlsConnection` calls `verifyCertificate` twice, once from each side's perspective — `serverVerifiedByCaller` checks the destination's certificate the way Level 1 did, and `callerVerifiedByServer` additionally checks the *caller's* certificate from the destination's point of view. The connection is only established if `&&` of both checks is `true` — either side alone failing would block the connection entirely.

### Level 3 — Advanced

```java
// File: MtlsAuthorizationPolicy.java -- the SAME mutual verification, now
// handling the PRODUCTION-FLAVORED hard case: a VERIFIED identity is
// still subject to an AUTHORIZATION POLICY. order-service's identity is
// legitimately verified via mTLS, but the mesh's policy only allows it to
// call payment-service's /charge endpoint, NOT its /refund endpoint --
// identity verification and authorization are TWO SEPARATE checks.
import java.util.*;

public class MtlsAuthorizationPolicy {
    record Certificate(String serviceName, boolean validAndTrusted) {}

    static boolean verifyCertificate(String verifierName, Certificate presentedCert) {
        if (!presentedCert.validAndTrusted()) {
            System.out.println("[" + verifierName + "] REJECTED: untrusted certificate for '" + presentedCert.serviceName() + "'");
            return false;
        }
        return true;
    }

    // The mesh's authorization policy: which verified identities may call which endpoints.
    static Map<String, Set<String>> authorizationPolicy = Map.of(
        "/charge", Set.of("order-service"),
        "/refund", Set.of("support-service") // order-service is NOT authorized for refunds
    );

    static String handleIncomingCall(Certificate callerCert, String endpoint) {
        // Step 1: mTLS identity verification.
        if (!verifyCertificate("payment-service sidecar", callerCert)) {
            return "REJECTED: mTLS identity verification failed";
        }
        System.out.println("[payment-service sidecar] mTLS verified caller identity: " + callerCert.serviceName());

        // Step 2: authorization check -- a COMPLETELY SEPARATE decision from identity verification.
        Set<String> allowedCallers = authorizationPolicy.getOrDefault(endpoint, Set.of());
        if (!allowedCallers.contains(callerCert.serviceName())) {
            System.out.println("[payment-service sidecar] AUTHORIZATION DENIED: " + callerCert.serviceName()
                    + " is verified but not authorized to call " + endpoint);
            return "REJECTED: authorization denied";
        }

        System.out.println("[payment-service sidecar] authorization granted for " + callerCert.serviceName() + " -> " + endpoint);
        return "ALLOWED: request forwarded to application";
    }

    public static void main(String[] args) {
        Certificate orderServiceCert = new Certificate("order-service", true);

        System.out.println("--- order-service calls /charge (authorized) ---");
        System.out.println(handleIncomingCall(orderServiceCert, "/charge"));

        System.out.println();
        System.out.println("--- order-service calls /refund (verified identity, but NOT authorized) ---");
        System.out.println(handleIncomingCall(orderServiceCert, "/refund"));
    }
}
```

How to run: `java MtlsAuthorizationPolicy.java`

`handleIncomingCall` runs two genuinely separate checks in sequence: `verifyCertificate` (identity — is this really `order-service`) and then a lookup into `authorizationPolicy` (authorization — is `order-service` allowed to call *this specific endpoint*). For `/charge`, `order-service` appears in the allowed set, so both checks pass. For `/refund`, `order-service`'s certificate is identically valid and passes identity verification exactly as before — but it's absent from `/refund`'s allowed set, so the authorization check fails independently, even though nothing about the caller's identity verification changed at all between the two calls.

## 6. Walkthrough

Trace `MtlsAuthorizationPolicy.main` in order. **First**, the `/charge` call runs `handleIncomingCall(orderServiceCert, "/charge")`. Inside it, `verifyCertificate` checks `orderServiceCert.validAndTrusted()`, which is `true`, so identity verification passes and the confirmation prints.

**Next**, still within that same call, `authorizationPolicy.getOrDefault("/charge", Set.of())` returns `Set.of("order-service")`. The check `allowedCallers.contains("order-service")` is `true`, so the authorization-denied branch is skipped, the grant message prints, and `"ALLOWED: request forwarded to application"` is returned.

**Then**, the `/refund` call runs `handleIncomingCall(orderServiceCert, "/refund")` — the exact same `orderServiceCert` object as before. `verifyCertificate` runs the identical check on the identical certificate and passes identically — identity verification has nothing to do with which endpoint is being called, so this step behaves exactly as it did for `/charge`.

**After that**, `authorizationPolicy.getOrDefault("/refund", Set.of())` returns `Set.of("support-service")` this time — a completely different set that does not contain `"order-service"`. The check `allowedCallers.contains("order-service")` is `false`, so the authorization-denied branch runs, printing the denial message that explicitly notes the caller *is* verified but simply isn't authorized for this particular endpoint.

**Finally**, `handleIncomingCall` returns `"REJECTED: authorization denied"` for the `/refund` case — demonstrating concretely that identity verification (mTLS) and authorization (policy) are two independent gates, and passing the first is necessary but not sufficient to pass the second.

```
--- order-service calls /charge (authorized) ---
[payment-service sidecar] mTLS verified caller identity: order-service
[payment-service sidecar] authorization granted for order-service -> /charge
ALLOWED: request forwarded to application

--- order-service calls /refund (verified identity, but NOT authorized) ---
[payment-service sidecar] mTLS verified caller identity: order-service
[payment-service sidecar] AUTHORIZATION DENIED: order-service is verified but not authorized to call /refund
REJECTED: authorization denied
```

## 7. Gotchas & takeaways

> Confusing "mTLS verified" with "authorized" is a real security gap — a service can have a perfectly legitimate, cryptographically verified identity and still need to be denied access to a specific sensitive operation. Always treat identity verification and authorization as two separate, both-required checks, never assume passing one implies the other.
- Mesh-managed certificate rotation (short-lived certificates, automatically reissued) meaningfully reduces the risk of a leaked or stolen certificate, since it becomes invalid on its own relatively soon regardless of whether the leak is ever detected.
- Because mTLS happens entirely at the proxy layer, application code never needs its own TLS library, certificate management, or key handling for service-to-service calls — a substantial reduction in security-sensitive code every team would otherwise need to get right independently.
- Authorization policies (as in Level 3) let you express precise, least-privilege rules — "only these specific services may call this specific sensitive endpoint" — enforced consistently by the mesh rather than scattered across ad hoc checks in application code.
- Enabling mTLS mesh-wide, rather than only for specific "sensitive" services, is the stronger security posture — a zero-trust model treats every internal connection as needing verification, not just the ones that seem obviously sensitive today.
