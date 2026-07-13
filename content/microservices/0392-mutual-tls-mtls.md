---
card: microservices
gi: 392
slug: mutual-tls-mtls
title: "Mutual TLS (mTLS)"
---

## 1. What it is

Ordinary TLS (the "S" in HTTPS) is **one-way**: the server proves its identity to the client with a certificate, but the client proves nothing back beyond "I can complete the handshake." **Mutual TLS (mTLS)** flips that into a two-way handshake: *both* sides present X.509 certificates, and both sides verify the other's certificate against a trusted certificate authority (CA) before any application data flows. In a microservices context, mTLS is one of the strongest forms of [service-to-service authentication](0391-service-to-service-authentication.md), because identity is verified at the transport layer, cryptographically, before a single byte of the HTTP request is even processed.

## 2. Why & when

Reach for mTLS when you want service identity verification that doesn't depend on the application layer getting anything right:

- **Defense that doesn't rely on every service correctly checking a token.** A JWT-based scheme still needs application code to validate the signature, audience, and expiry correctly on every endpoint; mTLS pushes identity verification into the TLS handshake itself, so a service that forgets to check something still can't complete a connection without a valid certificate.
- **Encryption and authentication in one mechanism.** mTLS gives you encrypted transport (nobody can eavesdrop) *and* mutual identity verification (nobody can impersonate either side) as a single package — directly closing the "data-in-transit surface" and part of the "internal surface" named in [microservices security challenges](0378-microservices-security-challenges-larger-attack-surface.md).
- **Service mesh environments.** Tools like Istio, Linkerd, and Consul Connect can enforce mTLS automatically between every pod, issuing and rotating short-lived certificates without application code changes — making mTLS the default, nearly invisible security layer for internal traffic in many Kubernetes-based systems.
- **Regulatory or compliance requirements** that specifically call for mutual authentication of internal traffic, not just encryption.

mTLS is less convenient when you need fine-grained, per-request, user-aware decisions (it authenticates the *service*, not an end user) or when you're calling across organizational boundaries where managing a shared CA trust relationship is impractical — that's usually where token-based schemes (JWTs, [API keys](0393-api-keys.md)) take over instead.

## 3. Core concept

Think of two embassies exchanging diplomatic credentials before any conversation happens: each side presents a sealed, government-issued ID, and each side checks the other's seal against a trusted registry — *before* either says a word about the actual business at hand. Neither embassy just takes the other's word for who they are. mTLS is that mutual credential check, built into the TLS handshake.

The handshake, at a level useful for understanding what's being verified:

1. **Client Hello / Server Hello** — the usual TLS negotiation of protocol version and cipher suites.
2. **Server presents its certificate.** The client verifies it was signed by a CA it trusts, and that the certificate's subject matches the hostname being connected to.
3. **Server requests a client certificate** (this is the "mutual" part — ordinary TLS stops after step 2). The client presents its own X.509 certificate.
4. **Server verifies the client's certificate** against a trusted CA, typically an internal CA the organization runs specifically for issuing service certificates.
5. Only after both verifications succeed does the encrypted session begin, and the server now knows the verified identity of the calling service (from the certificate's subject, e.g. a Subject Alternative Name like `spiffe://cluster.local/ns/orders/sa/order-service`).

Two operational pieces make mTLS work at scale in a microservices system, and both matter more than the handshake mechanics themselves:

- **A private, internal CA** issues short-lived certificates to each service — you're not using public CAs for internal traffic.
- **Automated certificate rotation.** Certificates for internal services are typically valid for hours, not months, and are reissued automatically (a service mesh sidecar commonly handles this transparently); see [secrets management & rotation](0394-secrets-management-rotation.md) for the general principle of why short-lived credentials beat long-lived ones.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Order service and inventory service exchange certificates during the TLS handshake: each verifies the other's certificate against a trusted internal CA before any application data is sent" font-family="sans-serif">
  <rect x="30" y="90" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="112" fill="#e6edf3" font-size="11" text-anchor="middle">order-service</text>
  <text x="105" y="128" fill="#8b949e" font-size="9" text-anchor="middle">cert signed by internal CA</text>

  <rect x="460" y="90" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="112" fill="#e6edf3" font-size="11" text-anchor="middle">inventory-service</text>
  <text x="535" y="128" fill="#8b949e" font-size="9" text-anchor="middle">cert signed by internal CA</text>

  <rect x="250" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="32" fill="#e6edf3" font-size="10" text-anchor="middle">Internal CA (trust root)</text>
  <line x1="320" y1="44" x2="105" y2="90" stroke="#6db33f" stroke-dasharray="2,2"/>
  <line x1="320" y1="44" x2="535" y2="90" stroke="#6db33f" stroke-dasharray="2,2"/>

  <line x1="180" y1="105" x2="460" y2="105" stroke="#79c0ff" marker-end="url(#mtls)"/>
  <text x="320" y="97" fill="#79c0ff" font-size="8" text-anchor="middle">1. server cert -&gt;</text>
  <line x1="460" y1="135" x2="180" y2="135" stroke="#79c0ff" marker-end="url(#mtls)"/>
  <text x="320" y="150" fill="#79c0ff" font-size="8" text-anchor="middle">&lt;- 2. client cert requested + presented</text>

  <rect x="200" y="200" width="240" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="222" fill="#6db33f" font-size="10" text-anchor="middle">3. both verified -&gt; encrypted session begins</text>
  <defs>
    <marker id="mtls" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

Both services present certificates signed by the same trusted internal CA; only once each side has verified the other's certificate does the encrypted, mutually-authenticated session begin.

## 5. Runnable example

Scenario: order-service calling inventory-service. We simulate the essential trust check mTLS performs — verifying a certificate's issuing CA and subject — starting from no verification at all, through one-way verification (ordinary TLS), to full mutual verification with certificate expiry checking.

### Level 1 — Basic

```java
// File: NoCertVerification.java -- a connection is "accepted" without checking
// ANY certificate at all -- the equivalent of plaintext HTTP between services.
public class NoCertVerification {
    record Connection(String fromService, String toService) {}

    static String connect(String fromService, String toService) {
        return "Connected " + fromService + " -> " + toService + " with NO certificate check -- identity of either side is unverified";
    }

    public static void main(String[] args) {
        System.out.println(connect("order-service", "inventory-service"));
        // An attacker's process can claim to be "order-service" -- nothing checks it.
        System.out.println(connect("attacker-process", "inventory-service"));
    }
}
```

How to run: `java NoCertVerification.java`

`connect` accepts any `fromService` string as-is, with no cryptographic proof behind it. This models plaintext, unauthenticated service calls: whoever can reach the network port can claim to be anyone.

### Level 2 — Intermediate

```java
// File: OneWayTLS.java -- ordinary (one-way) TLS: inventory-service proves ITS
// identity to order-service via a certificate, but order-service presents nothing
// back. inventory-service still has no idea WHO is calling it.
import java.util.*;

public class OneWayTLS {
    record Certificate(String subject, String issuer) {}

    static final Set<String> TRUSTED_CAS = Set.of("internal-ca");

    static boolean verifyServerCert(Certificate cert, String expectedSubject) {
        return TRUSTED_CAS.contains(cert.issuer()) && cert.subject().equals(expectedSubject);
    }

    public static void main(String[] args) {
        Certificate inventoryCert = new Certificate("inventory-service", "internal-ca");
        boolean serverVerified = verifyServerCert(inventoryCert, "inventory-service");
        System.out.println("order-service verifies inventory-service's cert: " + serverVerified);
        System.out.println("Encrypted channel established -- but inventory-service still has NO certificate from the caller.");
        System.out.println("inventory-service's view of the caller: unknown (only the network connection exists)");
    }
}
```

How to run: `java OneWayTLS.java`

`verifyServerCert` models what a normal HTTPS client does: check the server's certificate is issued by a trusted CA and matches the expected subject. `order-service` can now be sure it's really talking to `inventory-service`. But the check only runs in one direction — `inventory-service` never receives or verifies anything proving who called it, which is precisely the gap mTLS closes.

### Level 3 — Advanced

```java
// File: MutualTLS.java -- FULL mutual TLS: BOTH sides present certificates,
// BOTH are verified against the trusted CA, subject match, AND expiry --
// only if all checks pass on both sides does the connection succeed.
import java.time.*;
import java.util.*;

public class MutualTLS {
    record Certificate(String subject, String issuer, Instant expiresAt) {
        boolean isExpired(Instant now) { return now.isAfter(expiresAt); }
    }

    static final Set<String> TRUSTED_CAS = Set.of("internal-ca");

    static boolean verifyCert(Certificate cert, String expectedSubject, Instant now) {
        if (!TRUSTED_CAS.contains(cert.issuer())) return false;
        if (!cert.subject().equals(expectedSubject)) return false;
        if (cert.isExpired(now)) return false;
        return true;
    }

    // The full mutual handshake: server verifies client, client verifies server.
    static String handshake(Certificate clientCert, Certificate serverCert, String expectedClientSubject,
                             String expectedServerSubject, Instant now) {
        boolean clientVerifiedByServer = verifyCert(clientCert, expectedClientSubject, now);
        boolean serverVerifiedByClient = verifyCert(serverCert, expectedServerSubject, now);
        if (!clientVerifiedByServer) {
            return "HANDSHAKE FAILED: inventory-service rejected caller cert (subject='" + clientCert.subject()
                    + "', issuer='" + clientCert.issuer() + "', expired=" + clientCert.isExpired(now) + ")";
        }
        if (!serverVerifiedByClient) {
            return "HANDSHAKE FAILED: order-service rejected server cert";
        }
        return "MUTUAL TLS ESTABLISHED: inventory-service knows caller is verified '" + clientCert.subject()
                + "'; order-service knows server is verified '" + serverCert.subject() + "'";
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-07-13T12:00:00Z");
        Certificate orderCert = new Certificate("order-service", "internal-ca", now.plus(Duration.ofHours(8)));
        Certificate inventoryCert = new Certificate("inventory-service", "internal-ca", now.plus(Duration.ofHours(8)));

        System.out.println(handshake(orderCert, inventoryCert, "order-service", "inventory-service", now));

        // An attacker presents a self-signed certificate claiming to be order-service.
        Certificate forgedCert = new Certificate("order-service", "attacker-self-signed-ca", now.plus(Duration.ofHours(8)));
        System.out.println(handshake(forgedCert, inventoryCert, "order-service", "inventory-service", now));

        // A legitimate certificate that has simply expired (rotation missed its window).
        Certificate expiredCert = new Certificate("order-service", "internal-ca", now.minus(Duration.ofMinutes(5)));
        System.out.println(handshake(expiredCert, inventoryCert, "order-service", "inventory-service", now));
    }
}
```

How to run: `java MutualTLS.java`

`verifyCert` checks three independent conditions any real TLS stack checks during certificate validation: the issuing CA is trusted, the subject matches who we expect to be talking to, and the certificate hasn't expired. `handshake` runs this check in *both* directions before declaring success. The legitimate call, with two valid `internal-ca`-issued certificates, succeeds on both checks. The forged certificate — correct subject name, but signed by `attacker-self-signed-ca` rather than the trusted CA — fails the issuer check immediately, exactly the scenario mTLS is designed to catch: a spoofed identity claim without the matching trusted signature. The expired certificate fails the expiry check, modeling what happens when certificate rotation lags behind a certificate's validity window.

## 6. Walkthrough

Trace `MutualTLS.main` in order. **First**, `orderCert` and `inventoryCert` are built with `issuer = "internal-ca"` and an expiry eight hours in the future — both are valid, well-formed certificates from the trusted CA.

**Next**, `handshake(orderCert, inventoryCert, "order-service", "inventory-service", now)` runs. `verifyCert(orderCert, "order-service", now)` checks: is `"internal-ca"` in `TRUSTED_CAS`? Yes. Does `orderCert.subject()` equal `"order-service"`? Yes. Is it expired at `now`? No. All three pass, so `clientVerifiedByServer` is `true`. The same three checks run for `inventoryCert` against `"inventory-service"`, also all passing, so `serverVerifiedByClient` is `true`. Both directions verified, so the method returns the success message naming both verified identities.

**Then**, `handshake(forgedCert, inventoryCert, ...)` runs with `forgedCert.issuer() = "attacker-self-signed-ca"`. `verifyCert` immediately fails the very first check — `TRUSTED_CAS.contains("attacker-self-signed-ca")` is `false` — so `clientVerifiedByServer` is `false` regardless of the fact that the certificate's *subject* field claims `"order-service"`. The handshake fails with a message naming the actual issuer, which is exactly what a real TLS stack would report: a subject name means nothing without a trusted signature behind it.

**Finally**, `handshake(expiredCert, inventoryCert, ...)` runs with an expiry five minutes in the past. `verifyCert` passes the issuer and subject checks, but `expiredCert.isExpired(now)` is `true`, so the third check fails, and the handshake is rejected — a legitimate-but-stale credential, which is why automated rotation matters so much in practice.

```
MUTUAL TLS ESTABLISHED: inventory-service knows caller is verified 'order-service'; order-service knows server is verified 'inventory-service'
HANDSHAKE FAILED: inventory-service rejected caller cert (subject='order-service', issuer='attacker-self-signed-ca', expired=false)
HANDSHAKE FAILED: inventory-service rejected caller cert (subject='order-service', issuer='internal-ca', expired=true)
```

## 7. Gotchas & takeaways

> mTLS verifies *which service* is calling, cryptographically and at the transport layer — but it says nothing about *which end user* the call is on behalf of, or what that user is allowed to do. A common mistake is treating "the mTLS handshake succeeded" as equivalent to full authorization; in practice mTLS should sit alongside, not replace, [token relay](0389-token-relay-propagation-between-services.md) and [scopes, roles & fine-grained authorization](0395-scopes-roles-fine-grained-authorization.md) for anything that needs user-level decisions.

- mTLS authenticates both sides of a connection at the TLS handshake, before any application code runs — a strong complement to (not a replacement for) application-layer checks.
- It requires an internal CA and, at real scale, automated short-lived certificate issuance and rotation — manually managing long-lived certificates across many services doesn't scale and reintroduces the risks discussed in [secrets management & rotation](0394-secrets-management-rotation.md).
- Service meshes (Istio, Linkerd, Consul Connect) commonly automate mTLS transparently, so application code doesn't need to implement certificate handling itself.
- A certificate proves service identity, not user identity — combine it with token-based mechanisms when user-specific authorization decisions are needed downstream.
- mTLS is one concrete, robust option among several for [service-to-service authentication](0391-service-to-service-authentication.md); the right choice depends on whether you control both ends' infrastructure (favoring mTLS) or need lighter-weight, more portable credentials across trust boundaries (favoring JWTs or [API keys](0393-api-keys.md)).
