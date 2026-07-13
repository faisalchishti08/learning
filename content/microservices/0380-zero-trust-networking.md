---
card: microservices
gi: 380
slug: zero-trust-networking
title: "Zero-trust networking"
---

## 1. What it is

**Zero-trust networking** is a security model built on one blunt rule: *never trust a request just because of where it came from — verify it every time, on every hop.* The old "castle and moat" model trusted anything already inside the network perimeter; zero trust throws that assumption away and instead requires every caller, internal or external, to prove its identity and permissions on every single call, as if the network itself were hostile. In microservices, that means service A calling service B doesn't get a free pass just because both live inside the same cluster or VPC — B still checks who A is and what A is allowed to do.

## 2. Why & when

You need zero trust the moment your system has more than one trust boundary, which — as covered in [microservices security challenges](0378-microservices-security-challenges-larger-attack-surface.md) — is essentially every microservices system. The perimeter model breaks down for a few concrete reasons:

- **Internal networks get breached too.** A misconfigured container, a leaked credential, or a single vulnerable dependency can put an attacker *inside* your network just as easily as outside it.
- **Cloud environments blur "inside" and "outside."** Services scattered across regions, clusters, and third-party platforms don't share one clean physical boundary the way an on-premise data center once did.
- **Lateral movement is the real danger.** Once an attacker compromises one low-value service, an internal network that implicitly trusts "anything already inside" lets them call every other service unchecked — turning one small breach into a full compromise.
- **Compliance and auditability** increasingly require proof of *who* accessed *what*, which is only possible if every hop actually authenticates and logs identity, rather than assuming trust.

Adopt zero trust as a default posture from day one of a multi-service system, not as a retrofit after an incident — retrofitting means finding every unguarded internal endpoint, which is much harder than building them guarded from the start.

## 3. Core concept

Think of an airport instead of a castle. A castle checks you once at the gate, and afterward you can wander into the throne room unchallenged. An airport checks your ID at security, checks your boarding pass again at the gate, and checks it once more when you board the plane — at every transition, someone independently re-verifies who you are and what you're allowed to do, regardless of the fact that you already cleared an earlier checkpoint. Zero-trust networking applies that same "verify at every transition" discipline to service-to-service calls.

Concretely, zero trust rests on a few pillars:

1. **Explicit verification** — every request carries proof of identity (a certificate, a signed token) and that proof is checked on every hop, not just at the edge.
2. **Least-privilege access** — a service is granted only the specific calls it needs to make, nothing broader "just in case."
3. **Assume breach** — design as if an attacker is already inside the network, so damage is contained by per-hop checks rather than prevented solely by keeping attackers out.
4. **Micro-segmentation** — network policy restricts *which* services can even attempt to connect to *which* other services, shrinking the blast radius before identity checks even run.
5. **Strong transport identity** — [mutual TLS](0392-mutual-tls-mtls.md) lets the connection itself cryptographically prove both sides' identity, so trust isn't based on network location (like an IP address) at all.

This is the internal counterpart to [edge authentication at the gateway](0382-edge-authentication-at-the-gateway.md): the gateway verifies external callers, and zero trust extends that same discipline to every call *between* services once a request is already inside.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Perimeter trust model lets any internal caller reach any service unchecked once inside the network; zero trust re-verifies identity independently at every hop, containing a compromised service">
  <text x="150" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Perimeter trust</text>
  <rect x="40" y="40" width="220" height="170" rx="10" fill="#1c2430" stroke="#f85149" stroke-width="2" stroke-dasharray="4,3"/>
  <text x="150" y="58" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">one gate, then free roam</text>
  <rect x="60" y="75" width="60" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order</text>
  <rect x="150" y="75" width="60" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payment</text>
  <rect x="90" y="140" width="90" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="135" y="159" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">compromised svc</text>
  <line x1="150" y1="140" x2="90" y2="105" stroke="#f85149"/>
  <line x1="150" y1="140" x2="180" y2="105" stroke="#f85149"/>
  <text x="150" y="200" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">unchecked calls anywhere</text>

  <text x="470" y="24" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Zero trust</text>
  <rect x="360" y="40" width="220" height="170" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <rect x="380" y="75" width="60" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="410" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order</text>
  <rect x="470" y="75" width="60" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="500" y="94" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Payment</text>
  <rect x="410" y="140" width="90" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="455" y="159" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">compromised svc</text>
  <line x1="470" y1="140" x2="410" y2="105" stroke="#f85149" stroke-dasharray="2,2"/>
  <text x="440" y="130" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">x</text>
  <line x1="470" y1="140" x2="500" y2="105" stroke="#f85149" stroke-dasharray="2,2"/>
  <text x="490" y="130" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">x</text>
  <text x="470" y="200" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">every hop re-verified, blocked</text>
</svg>

Under perimeter trust a compromised service can call anything inside; under zero trust every hop is independently re-verified, so the same compromised service is blocked.

## 5. Runnable example

Scenario: an internal call from an "inventory-check" component to a "payment" component. We start with pure perimeter trust (IP/network membership only), then add per-hop identity verification, then add least-privilege scoping so even a verified caller can't exceed the specific action it's allowed.

### Level 1 — Basic

```java
// File: PerimeterTrustOnly.java -- trusts ANY caller that is "inside the network"
// (simulated by a boolean), regardless of who it actually is.
public class PerimeterTrustOnly {
    static String chargeCard(String callerNetwork, String orderId) {
        // The ONLY check: is the caller somewhere inside our network?
        if (!"internal".equals(callerNetwork)) {
            return "DENIED: not on internal network";
        }
        return "CHARGED order " + orderId + " -- caller network was 'internal', that's all that was checked";
    }

    public static void main(String[] args) {
        // A legitimate service call.
        System.out.println(chargeCard("internal", "order-1"));
        // A compromised, low-value service is ALSO "internal" -- and gets through identically.
        System.out.println(chargeCard("internal", "order-2"));
    }
}
```

How to run: `java PerimeterTrustOnly.java`

`chargeCard` only checks whether the caller is on the internal network — a stand-in for "did this request come from inside our VPC/cluster." Both the legitimate order service and a compromised, unrelated service satisfy that one check identically, because network location says nothing about *which* service is actually calling or whether it should be allowed to charge a card at all.

### Level 2 — Intermediate

```java
// File: ZeroTrustIdentityCheck.java -- the SAME call, now requiring a verified,
// per-hop identity (like an mTLS certificate subject) instead of just network location.
import java.util.*;

public class ZeroTrustIdentityCheck {
    static final Set<String> KNOWN_SERVICE_IDENTITIES = Set.of("order-service", "inventory-service");

    static String chargeCard(String callerIdentity, String certificateValid, String orderId) {
        if (!KNOWN_SERVICE_IDENTITIES.contains(callerIdentity)) {
            return "DENIED: '" + callerIdentity + "' is not a recognized service identity";
        }
        if (!"true".equals(certificateValid)) {
            return "DENIED: identity claimed but certificate/token did not verify";
        }
        return "CHARGED order " + orderId + " -- verified identity '" + callerIdentity + "' with a valid credential";
    }

    public static void main(String[] args) {
        System.out.println(chargeCard("order-service", "true", "order-1"));       // legitimate, verified
        System.out.println(chargeCard("compromised-service", "true", "order-2")); // network-internal, but unrecognized identity
        System.out.println(chargeCard("order-service", "false", "order-3"));      // right name, but credential fails to verify
    }
}
```

How to run: `java ZeroTrustIdentityCheck.java`

Now network location is irrelevant — `chargeCard` requires a recognized identity *and* a credential (simulating a certificate or signed token) that actually verifies. `"compromised-service"` is rejected outright because it isn't on the known-identity list, no matter how it reached the call. A caller claiming to be `"order-service"` with an invalid credential is also rejected, modeling a stolen or spoofed identity claim without the matching private key or signature.

### Level 3 — Advanced

```java
// File: ZeroTrustLeastPrivilege.java -- adds LEAST-PRIVILEGE scoping: even a fully
// verified, trusted identity is only allowed the specific actions it's been granted,
// not everything the target service exposes.
import java.util.*;

public class ZeroTrustLeastPrivilege {
    static final Set<String> KNOWN_SERVICE_IDENTITIES = Set.of("order-service", "inventory-service", "refund-admin-tool");
    // Least privilege: each identity is mapped to the SPECIFIC actions it may perform.
    static final Map<String, Set<String>> ALLOWED_ACTIONS = Map.of(
            "order-service", Set.of("charge"),
            "inventory-service", Set.of("reserve-stock"),
            "refund-admin-tool", Set.of("refund")
    );

    static String callPaymentService(String callerIdentity, boolean credentialValid, String action, String orderId) {
        if (!KNOWN_SERVICE_IDENTITIES.contains(callerIdentity)) {
            return "DENIED: unrecognized identity '" + callerIdentity + "'";
        }
        if (!credentialValid) {
            return "DENIED: credential for '" + callerIdentity + "' failed verification";
        }
        Set<String> allowed = ALLOWED_ACTIONS.getOrDefault(callerIdentity, Set.of());
        if (!allowed.contains(action)) {
            return "DENIED: '" + callerIdentity + "' is verified but NOT authorized for action '" + action + "' (allowed: " + allowed + ")";
        }
        return "OK: '" + callerIdentity + "' performed '" + action + "' on order " + orderId;
    }

    public static void main(String[] args) {
        System.out.println(callPaymentService("order-service", true, "charge", "order-1"));       // allowed action
        System.out.println(callPaymentService("order-service", true, "refund", "order-1"));       // verified identity, WRONG action
        System.out.println(callPaymentService("inventory-service", true, "charge", "order-1"));   // verified identity, never allowed to charge at all
        System.out.println(callPaymentService("refund-admin-tool", true, "refund", "order-1"));   // allowed action, different identity
    }
}
```

How to run: `java ZeroTrustLeastPrivilege.java`

This version adds a third check on top of identity and credential verification: even a fully trusted, verified `order-service` is only authorized for `"charge"` — asking it to perform `"refund"` is denied, because `order-service` was never granted that permission. `inventory-service` is fully verifiable but has no charge permission at all, modeling how a compromised-but-verified low-privilege service still can't reach high-privilege actions. This is zero trust combined with least privilege: identity alone isn't enough, the *specific action* must also be explicitly granted.

## 6. Walkthrough

Trace `ZeroTrustLeastPrivilege.main` in order. **First**, `callPaymentService("order-service", true, "charge", "order-1")` runs. Identity check passes (`"order-service"` is known). Credential check passes (`credentialValid` is `true`). Then `ALLOWED_ACTIONS.get("order-service")` returns `{"charge"}`, and `"charge"` is in that set — so the call succeeds and prints `OK`.

**Next**, `callPaymentService("order-service", true, "refund", "order-1")` runs with the same identity and valid credential, but this time the action is `"refund"`. Identity and credential checks pass exactly as before, but `{"charge"}.contains("refund")` is `false` — so this call is **denied at the authorization step**, even though the caller is fully verified. This models a compromised or buggy `order-service` trying to perform an action it was never granted, and least-privilege scoping stops it regardless of identity trust.

**Then**, `callPaymentService("inventory-service", true, "charge", "order-1")` runs. Identity and credential both pass, but `ALLOWED_ACTIONS.get("inventory-service")` is `{"reserve-stock"}`, which does not contain `"charge"` — denied again, showing a *different* service hitting the same kind of limit.

**Finally**, `callPaymentService("refund-admin-tool", true, "refund", "order-1")` runs and succeeds, because `"refund"` is exactly what that identity is scoped to perform.

```
order-service  + charge  -> OK
order-service  + refund  -> DENIED (verified identity, unauthorized action)
inventory-svc  + charge  -> DENIED (verified identity, unauthorized action)
refund-admin   + refund  -> OK
```

## 7. Gotchas & takeaways

> Zero trust is often reduced to "just add mTLS everywhere" — but a certificate only proves *identity*, not *permission*. A service with a perfectly valid certificate can still be over-privileged if authorization checks aren't layered on top, as Level 3 shows: `order-service` passes identity and credential checks yet is correctly denied a `refund` it was never granted.

- Zero trust replaces "is this caller inside our network?" with "who exactly is this caller, and is *this specific action* something they're allowed to do?" — verified on every hop, not just the first one.
- It pairs naturally with [defense in depth](0379-defense-in-depth.md): zero trust says verify every hop, defense in depth says layer independent checks so no single verification failure is catastrophic.
- [Mutual TLS](0392-mutual-tls-mtls.md) is the most common mechanism for strong per-hop identity in service meshes, because the transport connection itself proves both sides' identity cryptographically.
- Network-level micro-segmentation (restricting which services can even attempt a connection) is a cheap first layer that shrinks the blast radius before identity checks ever run.
- Zero trust adds real operational cost — every service needs identity material, and every call needs a verification step — so plan for credential issuance, rotation, and monitoring from the start rather than bolting it on later.
