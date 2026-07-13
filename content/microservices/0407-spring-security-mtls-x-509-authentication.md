---
card: microservices
gi: 407
slug: spring-security-mtls-x-509-authentication
title: "Spring Security mTLS / X.509 authentication"
---

## 1. What it is

Spring Security's **X.509 authentication** support is the concrete Spring implementation of authenticating a caller from their **TLS client certificate**, the mechanism underlying [mutual TLS](0392-mutual-tls-mtls.md): instead of extracting an `Authentication` from a bearer token or a login form, Spring Security's `x509()` configuration extracts it directly from the client certificate the TLS handshake already verified, using a certificate field (usually the Subject's Common Name) as the caller's identity.

## 2. Why & when

You reach for X.509 authentication specifically in service-to-service scenarios where mutual TLS is already the transport-level security mechanism, and it would be redundant to layer a *second*, separate authentication scheme (like a bearer token) on top:

- **The TLS handshake already proved identity cryptographically** — if a client presented a valid certificate signed by a trusted CA during the handshake, requiring it to *also* present a bearer token to prove the same identity again is duplicated work, not extra security.
- **Service meshes and internal service-to-service calls** commonly use mTLS as the baseline transport security (see [mutual TLS](0392-mutual-tls-mtls.md) and [service-to-service authentication](0391-service-to-service-authentication.md)), and X.509 authentication is what turns "TLS handshake succeeded" into a Spring Security `Authentication` object your authorization rules can actually check.
- **It avoids issuing and rotating a separate credential** for machine-to-machine calls that already rotate TLS certificates through their own PKI lifecycle — one fewer secret type to manage, connecting to [secrets management & rotation](0394-secrets-management-rotation.md).
- **You need this when a Spring Boot service sits behind (or terminates) mTLS** and needs its authorization logic (`hasAuthority`, `@PreAuthorize`) to reference the calling service's identity, not just "TLS succeeded, so allow everything."

## 3. Core concept

Think of a bearer token as a visitor badge you show at every door, and a client certificate as a tattoo verified once at the building's mTLS-secured entrance — the badge (token) is checked repeatedly and can be lost or stolen; the tattoo (certificate identity, bound to the TLS session itself) was already cryptographically verified as part of *establishing the connection*, so Spring Security's job is simply to read who that verified identity belongs to and turn it into an `Authentication`.

The essential pieces:

1. **TLS-level mutual authentication** happens *before* Spring Security sees the request at all — it's configured at the servlet container or reverse-proxy level (`server.ssl.client-auth=need` in Spring Boot, or a proxy/mesh terminating mTLS and forwarding a verified identity).

```yaml
server:
  ssl:
    client-auth: need                 # REQUIRE a valid client certificate, or reject the TLS handshake
    trust-store: classpath:truststore.p12
    trust-store-password: ${TRUSTSTORE_PASSWORD}
    key-store: classpath:keystore.p12
    key-store-password: ${KEYSTORE_PASSWORD}
```

2. **`x509()` in the `SecurityFilterChain`** — extracts the principal from the certificate already present on the request (via `X509Certificate` attached by the servlet container after a successful handshake).

```java
@Bean
public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
    return http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/internal/**").hasAuthority("SERVICE_payment-service")
            .anyRequest().authenticated())
        .x509(x509 -> x509
            .subjectPrincipalRegex("CN=(.*?)(?:,|$)")          // extract Common Name as the principal
            .userDetailsService(x509UserDetailsService()))      // map that CN to authorities
        .build();
}
```

3. **A `UserDetailsService` for X.509** — maps the extracted Common Name (e.g., `payment-service`) to a `UserDetails` carrying the authorities that identity should have, exactly analogous to mapping a JWT subject claim to authorities in [OAuth2 Resource Server](0401-spring-security-oauth2-resource-server-jwt-opaque.md).
4. **Certificate validation itself (chain of trust, expiry, revocation)** is handled by the TLS layer via the configured trust store, not by Spring Security's `x509()` filter — that filter only runs *after* TLS has already accepted the certificate as valid, so getting the trust store and revocation checking right is as load-bearing here as getting JWT signature verification right in a token-based scheme.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During the TLS handshake the server verifies the client certificate against a trust store before any HTTP request is processed; once the handshake succeeds, Spring Security's X509 filter extracts the certificate's Common Name and turns it into an Authentication object consulted by the same authorization rules used elsewhere" font-family="sans-serif">
  <rect x="10" y="30" width="140" height="160" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="80" y="50" fill="#e6edf3" font-size="10" text-anchor="middle">TLS handshake</text>
  <text x="80" y="70" fill="#8b949e" font-size="8" text-anchor="middle">client presents cert</text>
  <text x="80" y="86" fill="#8b949e" font-size="8" text-anchor="middle">server checks trust store</text>
  <text x="80" y="102" fill="#8b949e" font-size="8" text-anchor="middle">chain + expiry + revocation</text>
  <rect x="30" y="120" width="100" height="30" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="80" y="139" fill="#f85149" font-size="9" text-anchor="middle">reject handshake</text>
  <text x="80" y="168" fill="#6db33f" font-size="9" text-anchor="middle">verified -&gt;</text>

  <rect x="220" y="30" width="180" height="160" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="50" fill="#e6edf3" font-size="10" text-anchor="middle">Spring Security x509()</text>
  <text x="310" y="72" fill="#8b949e" font-size="8" text-anchor="middle">reads X509Certificate</text>
  <text x="310" y="88" fill="#8b949e" font-size="8" text-anchor="middle">subjectPrincipalRegex</text>
  <text x="310" y="104" fill="#8b949e" font-size="8" text-anchor="middle">extracts CN=payment-service</text>
  <text x="310" y="126" fill="#8b949e" font-size="8" text-anchor="middle">UserDetailsService maps</text>
  <text x="310" y="142" fill="#8b949e" font-size="8" text-anchor="middle">CN -&gt; authorities</text>

  <rect x="450" y="80" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="540" y="100" fill="#e6edf3" font-size="9" text-anchor="middle">Authentication</text>
  <text x="540" y="116" fill="#8b949e" font-size="8" text-anchor="middle">consumed by authorizeHttpRequests</text>

  <line x1="150" y1="100" x2="220" y2="100" stroke="#6db33f" marker-end="url(#x5)"/>
  <line x1="400" y1="100" x2="450" y2="100" stroke="#6db33f" marker-end="url(#x5)"/>

  <defs>
    <marker id="x5" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto">
      <path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

TLS establishes cryptographic proof of identity during the handshake; Spring Security's X.509 filter simply reads that already-verified identity and turns it into an Authentication.

## 5. Runnable example

Scenario: `payment-service` accepting internal calls authenticated purely via client certificate. We simulate certificate-to-principal extraction first, then map extracted identities to authorities, then add expiry and trust-chain checks that mirror what the TLS layer itself must get right before Spring Security ever runs.

### Level 1 — Basic

```java
// File: ExtractPrincipalFromCertificate.java -- simulates x509()'s core job:
// pull the Common Name out of an ALREADY-VERIFIED client certificate and
// use it as the caller's principal. No token, no password -- the cert IS the credential.
import java.util.regex.*;

public class ExtractPrincipalFromCertificate {
    // Stand-in for a java.security.cert.X509Certificate's subject DN string.
    record ClientCertificate(String subjectDn) {}

    static final Pattern CN_PATTERN = Pattern.compile("CN=([^,]+)"); // mirrors subjectPrincipalRegex

    static String extractPrincipal(ClientCertificate cert) {
        Matcher m = CN_PATTERN.matcher(cert.subjectDn());
        if (!m.find()) throw new IllegalStateException("no CN found in certificate subject");
        return m.group(1);
    }

    public static void main(String[] args) {
        ClientCertificate cert = new ClientCertificate("CN=payment-service,OU=platform,O=example-corp,C=US");
        String principal = extractPrincipal(cert);
        System.out.println("Extracted principal from certificate: '" + principal + "'");
    }
}
```

How to run: `java ExtractPrincipalFromCertificate.java`

`extractPrincipal` applies the same regex logic as `x509().subjectPrincipalRegex("CN=(.*?)(?:,|$)")` to a certificate's subject distinguished name, pulling out `"payment-service"` as the caller's principal. Note this method assumes the certificate has *already* been cryptographically verified by the TLS layer — extraction is purely a string operation on a field the handshake already trusts.

### Level 2 — Intermediate

```java
// File: MapPrincipalToAuthorities.java -- the SAME extraction, now mapping
// the extracted principal to AUTHORITIES via a lookup, mirroring x509()'s
// userDetailsService(...) turning a bare Common Name into a real
// Authentication with granted authorities, consumed by authorizeHttpRequests.
import java.util.*;
import java.util.regex.*;

public class MapPrincipalToAuthorities {
    record ClientCertificate(String subjectDn) {}
    record Authentication(String principal, Set<String> authorities) {}

    static final Pattern CN_PATTERN = Pattern.compile("CN=([^,]+)");

    // Mirrors a UserDetailsService mapping known service identities to authorities.
    static final Map<String, Set<String>> KNOWN_SERVICE_IDENTITIES = Map.of(
            "payment-service", Set.of("SERVICE_payment-service", "SCOPE_internal:call"),
            "order-service", Set.of("SERVICE_order-service", "SCOPE_internal:call")
    );

    static String extractPrincipal(ClientCertificate cert) {
        Matcher m = CN_PATTERN.matcher(cert.subjectDn());
        if (!m.find()) throw new IllegalStateException("no CN found");
        return m.group(1);
    }

    static Authentication authenticate(ClientCertificate cert) {
        String principal = extractPrincipal(cert);
        Set<String> authorities = KNOWN_SERVICE_IDENTITIES.get(principal);
        if (authorities == null) {
            throw new SecurityException("401 Unauthorized -- '" + principal + "' has a valid cert but is not a known service identity");
        }
        return new Authentication(principal, authorities);
    }

    public static void main(String[] args) {
        Authentication auth = authenticate(new ClientCertificate("CN=payment-service,OU=platform,O=example-corp,C=US"));
        System.out.println("Authenticated: " + auth);

        try {
            authenticate(new ClientCertificate("CN=unknown-rogue-client,O=example-corp,C=US"));
        } catch (SecurityException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

How to run: `java MapPrincipalToAuthorities.java`

`authenticate` extracts the principal exactly as in Level 1, then looks it up in `KNOWN_SERVICE_IDENTITIES` — mirroring how a real `UserDetailsService` for X.509 rejects a certificate whose Common Name, while cryptographically valid (correctly signed, unexpired), doesn't correspond to any *known, authorized* service identity. This distinguishes "the certificate is genuine" (a TLS-layer fact) from "this identity is allowed to call us" (an application-layer authorization decision) — a valid certificate for an unrecognized identity is still rejected.

### Level 3 — Advanced

```java
// File: MtlsWithExpiryAndTrustChain.java -- adds what the TLS layer is
// actually responsible for validating BEFORE Spring Security's x509() filter
// ever runs: certificate expiry and issuer trust. Models the full picture --
// a certificate can have a perfectly well-formed CN and still be rejected
// for being expired or signed by an untrusted issuer.
import java.time.*;
import java.util.*;
import java.util.regex.*;

public class MtlsWithExpiryAndTrustChain {
    record ClientCertificate(String subjectDn, String issuerDn, Instant notAfter) {}
    record Authentication(String principal, Set<String> authorities) {}

    static final Pattern CN_PATTERN = Pattern.compile("CN=([^,]+)");
    static final Set<String> TRUSTED_ISSUERS = Set.of("CN=internal-ca,O=example-corp"); // the configured trust store
    static final Map<String, Set<String>> KNOWN_SERVICE_IDENTITIES = Map.of(
            "payment-service", Set.of("SERVICE_payment-service", "SCOPE_internal:call")
    );

    static String extractCn(String dn) {
        Matcher m = CN_PATTERN.matcher(dn);
        if (!m.find()) throw new IllegalStateException("no CN found");
        return m.group(1);
    }

    // Mirrors what the TLS handshake itself checks BEFORE any HTTP request is even processed.
    static void verifyTlsLevelTrust(ClientCertificate cert, Instant now) {
        if (!TRUSTED_ISSUERS.contains(cert.issuerDn())) {
            throw new SecurityException("TLS handshake rejected -- issuer '" + cert.issuerDn() + "' not in trust store");
        }
        if (now.isAfter(cert.notAfter())) {
            throw new SecurityException("TLS handshake rejected -- certificate expired at " + cert.notAfter());
        }
    }

    static Authentication authenticate(ClientCertificate cert, Instant now) {
        verifyTlsLevelTrust(cert, now); // would happen during the handshake, before Spring Security runs at all
        String principal = extractCn(cert.subjectDn());
        Set<String> authorities = KNOWN_SERVICE_IDENTITIES.get(principal);
        if (authorities == null) {
            throw new SecurityException("401 Unauthorized -- '" + principal + "' not a known service identity");
        }
        return new Authentication(principal, authorities);
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-07-13T12:00:00Z");
        String trustedIssuer = "CN=internal-ca,O=example-corp";

        ClientCertificate valid = new ClientCertificate(
                "CN=payment-service,O=example-corp", trustedIssuer, now.plusSeconds(86400));
        System.out.println("Valid cert: " + authenticate(valid, now));

        ClientCertificate expired = new ClientCertificate(
                "CN=payment-service,O=example-corp", trustedIssuer, now.minusSeconds(3600));
        try {
            authenticate(expired, now);
        } catch (SecurityException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        ClientCertificate untrustedIssuer = new ClientCertificate(
                "CN=payment-service,O=example-corp", "CN=self-signed-attacker-ca", now.plusSeconds(86400));
        try {
            authenticate(untrustedIssuer, now);
        } catch (SecurityException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

How to run: `java MtlsWithExpiryAndTrustChain.java`

`verifyTlsLevelTrust` checks the two things the TLS handshake itself is responsible for before any HTTP request is even routed to a controller: is the certificate's issuer in the configured trust store, and has the certificate expired. `authenticate` calls this first, then falls through to the same CN-extraction and authority-mapping logic from Level 2. The valid certificate, signed by the trusted internal CA and not yet expired, authenticates successfully. The expired certificate is rejected even though its Common Name and issuer are otherwise perfectly legitimate. The certificate with an untrusted issuer — modeling an attacker who generated their own self-signed certificate claiming to be `payment-service` — is rejected regardless of what Common Name it claims, because trust in mTLS flows from the issuing CA, not from anything the certificate's subject says about itself.

## 6. Walkthrough

Trace `MtlsWithExpiryAndTrustChain.main`'s third case: `authenticate(untrustedIssuer, now)`. **First**, `verifyTlsLevelTrust(untrustedIssuer, now)` runs. `TRUSTED_ISSUERS.contains("CN=self-signed-attacker-ca")` is checked — this issuer was never added to the trust store, so the condition `!TRUSTED_ISSUERS.contains(...)` is `true`, and a `SecurityException` is thrown immediately, citing the untrusted issuer.

**Next**, because `verifyTlsLevelTrust` threw, execution never reaches the `extractCn` call at all — the certificate's Common Name (`"payment-service"`, which *looks* legitimate) is never even inspected. This mirrors a real TLS handshake: an untrusted-issuer certificate causes the handshake itself to fail before any HTTP request — let alone Spring Security's `x509()` filter — is ever reached.

**Then**, back in `main`, the `catch` block prints the rejection message, confirming the attacker's self-signed certificate was stopped purely on trust-chain grounds, independent of anything it claimed in its subject.

**Finally**, compare this against the second case (`expired`): there, `TRUSTED_ISSUERS.contains(trustedIssuer)` succeeds (a legitimately-issued certificate), so the method proceeds to the expiry check, which is where *that* certificate is caught — demonstrating the two checks are independent and both must pass before extraction and authority-mapping are even attempted.

```
Valid cert: Authentication[principal=payment-service, authorities=[SERVICE_payment-service, SCOPE_internal:call]]
Rejected: TLS handshake rejected -- certificate expired at 2026-07-13T11:00:00Z
Rejected: TLS handshake rejected -- issuer 'CN=self-signed-attacker-ca' not in trust store
```

Sample TLS handshake failure as seen by a client (before any HTTP response is even possible):

```
TLS handshake initiated
-> client presents certificate: CN=payment-service, issuer=CN=self-signed-attacker-ca
-> server checks issuer against configured trust store: NOT FOUND
<- TLS alert: unknown_ca (handshake_failure)
   (connection closed -- no HTTP request/response ever exchanged)
```

## 7. Gotchas & takeaways

> A subtle and dangerous misconfiguration is setting `server.ssl.client-auth: want` instead of `need`. `want` makes the client certificate *optional* — a caller presenting no certificate at all still completes the TLS handshake and reaches Spring Security, where `x509()` simply finds no certificate to extract a principal from. Depending on the rest of the security configuration, this can silently fall through to an unauthenticated or anonymous request path instead of being rejected outright. Use `need` whenever client certificates should be mandatory.

- X.509 authentication turns an already-verified TLS client certificate into a Spring Security `Authentication`, avoiding a redundant second authentication scheme layered on top of mTLS.
- Certificate validity (trust chain, expiry, revocation) is enforced by the TLS layer itself, before Spring Security's `x509()` filter ever runs — misconfiguring the trust store is as serious a bug as misconfiguring JWT signature verification.
- A cryptographically valid certificate does not automatically imply authorization — mapping the extracted Common Name to a known, allow-listed service identity (via a `UserDetailsService`) is still a required application-layer step.
- `server.ssl.client-auth: need` makes client certificates mandatory; `want` makes them optional and can silently admit unauthenticated connections if the rest of the chain isn't configured to reject them.
- This topic is the Spring-specific mechanics behind [mutual TLS](0392-mutual-tls-mtls.md) and complements token-based [service-to-service authentication](0391-service-to-service-authentication.md) — many systems use mTLS for transport-level trust and reserve tokens for finer-grained, per-call scopes.
