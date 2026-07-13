---
card: microservices
gi: 391
slug: service-to-service-authentication
title: "Service-to-service authentication"
---

## 1. What it is

**Service-to-service authentication** is how one service proves *its own identity* to another service, independent of any end user involved in the request. It answers a different question than [token relay](0389-token-relay-propagation-between-services.md) or [token exchange](0390-token-exchange.md): those are about carrying a *user's* identity through a call chain, while this is about the *calling service itself* proving "I really am order-service, not an impostor" before the callee does any work at all — including for purely internal, user-agnostic calls like a nightly batch job or a health check between services.

## 2. Why & when

You need service-to-service authentication for exactly the reason laid out in [microservices security challenges](0378-microservices-security-challenges-larger-attack-surface.md): once a call crosses the network, "it came from inside our cluster" is not proof of anything. You need it whenever:

- **A service accepts calls from other services**, whether or not those calls carry a user token — a background reconciliation job, a metrics scraper, or an internal admin tool calling a service directly all still need to prove *who* they are.
- **You want least-privilege internal access.** Even if service B trusts *some* callers, it shouldn't automatically trust *every* service in the mesh; service-to-service authentication is what lets B check "is this specific caller, `payment-service`, actually allowed to call me?"
- **You're building any zero-trust internal network** (see [zero-trust networking](0380-zero-trust-networking.md)) — the whole premise of zero trust is that network location proves nothing, so every hop needs its own credential check.

The main options in practice, roughly from simplest to most robust:

1. **Shared static secrets** — a pre-shared API key or password every service knows. Simple, but a single leak compromises every caller using it, and rotation means touching every service simultaneously.
2. **Signed JWTs (client credentials)** — each service authenticates to an authorization server using the [OAuth2 client-credentials grant](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md) and receives a short-lived JWT identifying itself as the subject, which it presents on every call.
3. **Mutual TLS (mTLS)** — both sides present X.509 certificates during the TLS handshake itself, so identity is verified at the transport layer before any application data is even exchanged; covered in depth in [mutual TLS (mTLS)](0392-mutual-tls-mtls.md).
4. **API keys** — a simpler, often less secure relative of shared secrets, more common for third-party integrations than internal service calls; see [API keys](0393-api-keys.md).

## 3. Core concept

Picture a building where employees badge into every internal room, not just the front door — the building doesn't ask "are you inside the building?" (network location), it asks "does *your specific badge* open *this specific door*?" every single time. Service-to-service authentication is the internal badge system: every service carries a credential that identifies it specifically, and every service that receives a call checks that credential before doing anything, regardless of which network segment the call arrived from.

Two properties separate a good service-to-service auth scheme from a weak one:

1. **Verifiable identity, not just a shared password.** A JWT signed by a trusted authorization server, or an mTLS certificate signed by a trusted CA, lets the callee cryptographically verify *which* service is calling — a shared static secret only proves "someone who knows the secret" is calling, which is much weaker once that secret inevitably ends up in more places than intended (config files, logs, a compromised service).
2. **Short-lived, rotatable credentials.** A JWT from client-credentials typically expires in minutes; an mTLS certificate can be rotated on a schedule. A leaked long-lived shared secret stays dangerous until someone notices and manually rotates it everywhere it's used — see [secrets management & rotation](0394-secrets-management-rotation.md).

Crucially, service-to-service authentication and [token relay](0389-token-relay-propagation-between-services.md) are complementary, not competing: a call can (and often should) carry *both* — a service identity token proving "this call really came from order-service" *and* a relayed or exchanged user token proving "and it's acting on behalf of alice." Losing either one loses real information: without the service identity, you can't enforce which services may call which; without the user identity, you can't enforce per-user rules downstream.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Payment service presents its own client-credentials JWT to inventory service, which verifies the signature and checks the caller identity against an allow-list before processing the call" font-family="sans-serif">
  <rect x="20" y="30" width="140" height="50" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="90" y="50" fill="#e6edf3" font-size="10" text-anchor="middle">payment-service</text>
  <text x="90" y="65" fill="#8b949e" font-size="9" text-anchor="middle">holds its own client id/secret</text>

  <rect x="230" y="30" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="310" y="50" fill="#e6edf3" font-size="10" text-anchor="middle">Authorization Server</text>
  <text x="310" y="65" fill="#8b949e" font-size="9" text-anchor="middle">client_credentials grant</text>

  <rect x="450" y="30" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="50" fill="#e6edf3" font-size="10" text-anchor="middle">service JWT</text>
  <text x="525" y="65" fill="#8b949e" font-size="9" text-anchor="middle">sub=payment-service</text>

  <rect x="230" y="150" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="172" fill="#e6edf3" font-size="10" text-anchor="middle">inventory-service</text>
  <text x="330" y="188" fill="#8b949e" font-size="9" text-anchor="middle">verifies signature +</text>
  <text x="330" y="200" fill="#8b949e" font-size="9" text-anchor="middle">checks allow-list</text>

  <line x1="160" y1="55" x2="230" y2="55" stroke="#8b949e" marker-end="url(#s2s)"/>
  <line x1="390" y1="55" x2="450" y2="55" stroke="#8b949e" marker-end="url(#s2s)"/>
  <line x1="90" y1="80" x2="330" y2="150" stroke="#f0883e" stroke-dasharray="3,2" marker-end="url(#s2s)"/>
  <text x="180" y="120" fill="#f0883e" font-size="9">call + service JWT</text>
  <defs>
    <marker id="s2s" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

payment-service obtains a short-lived JWT identifying itself from the authorization server, then presents that JWT on its call to inventory-service, which verifies both the signature and that this specific caller is allowed to call it.

## 5. Runnable example

Scenario: inventory-service is being called by other internal services to reserve stock. We start with a wide-open endpoint (no caller verification at all), add a shared-secret check, then move to per-service signed credentials verified against an explicit allow-list of which callers may call which operations.

### Level 1 — Basic

```java
// File: NoServiceAuth.java -- inventory-service accepts calls from ANY caller,
// trusting network location alone. Any process that can reach it can reserve stock.
public class NoServiceAuth {
    static String reserveStock(String sku, int qty, String callerName) {
        return "Reserved " + qty + " of " + sku + " -- call accepted from '" + callerName
                + "' with NO verification of that identity";
    }

    public static void main(String[] args) {
        System.out.println(reserveStock("sku-42", 5, "payment-service"));
        // An attacker who compromised an unrelated, low-value service gets identical access.
        System.out.println(reserveStock("sku-42", 999, "compromised-newsletter-service"));
    }
}
```

How to run: `java NoServiceAuth.java`

`reserveStock` takes `callerName` purely as a label to print — it never checks whether the caller actually *is* who it claims. The forged call from `compromised-newsletter-service` succeeds identically to the legitimate one, reserving an arbitrary quantity of stock.

### Level 2 — Intermediate

```java
// File: SharedSecretAuth.java -- every internal service now presents a
// SHARED secret on every call. Better than nothing, but every caller uses
// the SAME credential, so it doesn't distinguish WHICH service is calling,
// and a single leak compromises every legitimate caller at once.
import java.util.*;

public class SharedSecretAuth {
    static final String SHARED_INTERNAL_SECRET = "internal-network-secret-2024";

    static String reserveStock(String sku, int qty, String callerName, String presentedSecret) {
        if (!SHARED_INTERNAL_SECRET.equals(presentedSecret)) {
            return "REJECTED: invalid shared secret from '" + callerName + "'";
        }
        return "Reserved " + qty + " of " + sku + " -- accepted from '" + callerName + "' (shared secret matched)";
    }

    public static void main(String[] args) {
        System.out.println(reserveStock("sku-42", 5, "payment-service", "internal-network-secret-2024"));
        // If the secret ever leaks (logged, checked into a repo, found in a compromised container),
        // ANY caller who has it -- legitimate or not -- passes this exact same check.
        System.out.println(reserveStock("sku-42", 999, "compromised-newsletter-service", "internal-network-secret-2024"));
    }
}
```

How to run: `java SharedSecretAuth.java`

`reserveStock` now rejects any call missing the correct secret — a real improvement over Level 1. But notice both calls present the *same* secret and both succeed: the check can't tell `payment-service` apart from `compromised-newsletter-service` if both happen to know the shared value, and there's no way to revoke just one caller's access without rotating the secret for every legitimate caller too.

### Level 3 — Advanced

```java
// File: PerServiceCredentialAuth.java -- each service authenticates with its
// OWN client-credentials-issued token (simulated), and inventory-service checks
// BOTH that the token is validly signed AND that this specific caller is on the
// allow-list for the operation being requested -- least-privilege, per-caller access.
import java.util.*;

public class PerServiceCredentialAuth {
    record ServiceToken(String issuer, String subject, String signature) {
        boolean signatureValid() {
            // Stand-in for real signature verification (e.g. RSA/EC signature check against the AS's public key).
            return signature.equals("valid-sig-for-" + subject);
        }
    }

    // Authorization server (simulated): issues a token identifying the calling service.
    static ServiceToken authServerIssuesToken(String clientId, String clientSecret) {
        if (!("secret-for-" + clientId).equals(clientSecret)) {
            throw new SecurityException("invalid client credentials for " + clientId);
        }
        return new ServiceToken("auth-server", clientId, "valid-sig-for-" + clientId);
    }

    // Per-operation allow-list: which service identities may call reserveStock.
    static final Set<String> ALLOWED_TO_RESERVE = Set.of("payment-service", "order-service");

    static String reserveStock(String sku, int qty, ServiceToken token) {
        if (!token.signatureValid()) {
            return "REJECTED: invalid or forged token signature";
        }
        if (!ALLOWED_TO_RESERVE.contains(token.subject())) {
            return "REJECTED: '" + token.subject() + "' is not authorized to reserve stock";
        }
        return "Reserved " + qty + " of " + sku + " -- verified caller '" + token.subject() + "', authorized for this operation";
    }

    public static void main(String[] args) {
        // Legitimate: payment-service authenticates and gets its own signed token.
        ServiceToken paymentToken = authServerIssuesToken("payment-service", "secret-for-payment-service");
        System.out.println(reserveStock("sku-42", 5, paymentToken));

        // A DIFFERENT legitimate service, but one never granted reserveStock access.
        ServiceToken newsletterToken = authServerIssuesToken("newsletter-service", "secret-for-newsletter-service");
        System.out.println(reserveStock("sku-42", 5, newsletterToken));

        // An attacker who forges a token claiming to be payment-service, but without the real signature.
        ServiceToken forged = new ServiceToken("auth-server", "payment-service", "forged-signature");
        System.out.println(reserveStock("sku-42", 999, forged));
    }
}
```

How to run: `java PerServiceCredentialAuth.java`

`authServerIssuesToken` models the [OAuth2 client-credentials grant](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md): each service authenticates with its *own* `clientId`/`clientSecret` pair and gets back a token whose `subject` is its own identity, signed in a way only the real authorization server can produce. `reserveStock` performs two independent checks: first, is the signature genuine (`signatureValid`), and second, is this specific subject on the `ALLOWED_TO_RESERVE` allow-list. `payment-service` passes both. `newsletter-service` authenticates successfully (it has valid credentials) but is still rejected because it was never granted this specific permission — a real caller with the wrong authorization, not a forgery. The forged token fails signature verification outright, regardless of which identity it claims.

## 6. Walkthrough

Trace `PerServiceCredentialAuth.main` in order. **First**, `authServerIssuesToken("payment-service", "secret-for-payment-service")` checks that the provided secret matches `"secret-for-payment-service"` — it does, so a `ServiceToken` is returned with `subject = "payment-service"` and `signature = "valid-sig-for-payment-service"`.

**Next**, `reserveStock("sku-42", 5, paymentToken)` runs. `token.signatureValid()` recomputes `"valid-sig-for-" + subject` and compares it to the stored signature — they match, so this check passes. `ALLOWED_TO_RESERVE.contains("payment-service")` is `true` — this check passes too. The reservation succeeds and is printed.

**Then**, `authServerIssuesToken("newsletter-service", "secret-for-newsletter-service")` succeeds identically at the authentication step — `newsletter-service` really does hold valid credentials for *itself*. But when `reserveStock` is called with this token, `signatureValid()` passes (it's a genuine token), while `ALLOWED_TO_RESERVE.contains("newsletter-service")` is `false` — this service was authenticated, but never *authorized* for this specific operation, so the call is rejected. This distinguishes [authentication from authorization](0381-authentication-vs-authorization.md): proving who you are is not the same as being allowed to do a given thing.

**Finally**, the forged token — claiming `subject = "payment-service"` but with `signature = "forged-signature"` — fails at `signatureValid()` immediately, before the allow-list is even consulted, because `"forged-signature"` does not equal `"valid-sig-for-payment-service"`.

```
Reserved 5 of sku-42 -- verified caller 'payment-service', authorized for this operation
REJECTED: 'newsletter-service' is not authorized to reserve stock
REJECTED: invalid or forged token signature
```

Sample HTTP shape for the real client-credentials exchange and the subsequent service call:

```
POST /token HTTP/1.1
Authorization: Basic cGF5bWVudC1zZXJ2aWNlOnNlY3JldA==
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&scope=inventory:reserve

HTTP/1.1 200 OK
{"access_token": "<JWT with sub=payment-service>", "expires_in": 300}

POST /inventory/reserve HTTP/1.1
Authorization: Bearer <JWT with sub=payment-service>

{"sku": "sku-42", "qty": 5}
```

## 7. Gotchas & takeaways

> A shared static secret (Level 2) is often adopted as a "quick win" and then never removed, because it works and rotating it means coordinating every service at once. The real cost shows up later: it can't express least privilege (every holder of the secret gets identical access), it can't be revoked for one caller without breaking all of them, and once it leaks — into a log line, a config dump, a compromised container's environment — every service using it is compromised simultaneously.

- Service-to-service authentication proves *which service* is calling, independent of any end-user token — necessary even for purely internal, user-agnostic calls.
- Prefer per-service, short-lived, verifiable credentials (signed JWTs from [client-credentials](0387-oauth2-grant-types-flows-auth-code-client-credentials-etc.md), or [mutual TLS](0392-mutual-tls-mtls.md) certificates) over shared static secrets — they support least privilege, revocation, and rotation without a fire drill.
- Authentication and authorization are separate checks: a service can genuinely prove its identity and still be denied a specific operation, exactly like `newsletter-service` in Level 3.
- Service identity and user identity are complementary, not competing — combine service-to-service authentication with [token relay / exchange](0389-token-relay-propagation-between-services.md) so downstream services know both *which service* and *on whose behalf* a call is being made.
- This whole approach only pays off within a broader [zero-trust networking](0380-zero-trust-networking.md) posture — verifying identity on every hop, not just at the network edge.
