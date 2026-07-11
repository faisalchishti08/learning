---
card: spring-security
gi: 31
slug: pre-authentication-scenarios-x-509-siteminder-j2ee
title: "Pre-authentication scenarios (X.509, SiteMinder, J2EE)"
---

## 1. What it is

Pre-authentication is the model for scenarios where identity has *already* been established by something outside Spring Security entirely — a client TLS certificate verified during the TLS handshake itself (X.509), an external single-sign-on proxy like SiteMinder that authenticates the user and forwards identity via a trusted header, or a servlet container's own authentication mechanism (J2EE/servlet container auth) — and Spring Security's job is reduced to *extracting* that already-established identity and *loading* the corresponding user's authorities, never verifying a password itself. `AbstractPreAuthenticatedProcessingFilter` is the shared base class for all such filters, and `PreAuthenticatedAuthenticationProvider` (paired with a `UserDetailsService`) is the corresponding provider that loads authorities without ever checking a credential.

```java
// X.509: the filter extracts the principal directly from the already-verified client certificate
public class X509AuthenticationFilter extends AbstractPreAuthenticatedProcessingFilter {
    protected Object getPreAuthenticatedPrincipal(HttpServletRequest request) {
        X509Certificate cert = extractClientCertificate(request);
        return cert.getSubjectX500Principal().getName(); // e.g. "CN=alice,OU=Engineering,..."
    }
    protected Object getPreAuthenticatedCredentials(HttpServletRequest request) {
        return "N/A"; // no credential to check -- the CERTIFICATE ITSELF was already verified by TLS
    }
}
```

## 2. Why & when

Spring Security's default authentication model assumes *it* is the component responsible for verifying a credential — but in these scenarios, a far more privileged and trusted layer (the TLS handshake itself, a dedicated enterprise SSO gateway, the servlet container/application server) has already done that verification, often using mechanisms Spring Security has no direct visibility into (certificate chain validation, an external identity provider's own login flow). Re-verifying anything at the Spring Security layer would be redundant at best and impossible at worst (Spring Security cannot re-validate a TLS certificate chain that the container already terminated), so pre-authentication filters exist specifically to *trust* that external verification and focus only on the remaining necessary step: mapping the externally-established identity to the application's own notion of authorities/roles.

Reach for a pre-authentication filter when:

- Client-certificate (mutual TLS) authentication is required, where the container or a load balancer terminates TLS and Spring Security's job is only to read the already-validated certificate's subject and load corresponding authorities.
- An external SSO/reverse-proxy system (SiteMinder, an enterprise identity gateway) authenticates the user and forwards identity via a trusted, proxy-injected HTTP header (`SM_USER` or similar) that only the trusted proxy can set, never the end client directly.
- Deploying inside a servlet container or application server that already performs its own authentication (J2EE container-managed security) and Spring Security should simply adopt that already-established `Principal` rather than duplicating the check.

## 3. Core concept

```
 AbstractPreAuthenticatedProcessingFilter.doFilter(request):
   1. principal = getPreAuthenticatedPrincipal(request)   -- SUBCLASS extracts from cert/header/container
   2. credentials = getPreAuthenticatedCredentials(request) -- usually a meaningless filler value ("N/A")
   3. PreAuthenticatedAuthenticationToken unverified = new PreAuthenticatedAuthenticationToken(principal, credentials)
   4. authenticationManager.authenticate(unverified)
        -> PreAuthenticatedAuthenticationProvider:
             userDetailsService.loadUserByUsername(principal)  -- LOADS AUTHORITIES ONLY
             ( NEVER compares any password -- the identity is ALREADY TRUSTED )
   5. SecurityContextHolder populated with the resulting, now-authorized Authentication
```

The provider's job shrinks from "verify AND authorize" (the normal case) to just "authorize" — verification already happened outside Spring Security.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An externally verified identity from a client certificate an SSO proxy header or a servlet container is extracted by a pre authentication filter and passed to PreAuthenticatedAuthenticationProvider which loads authorities via UserDetailsService without ever checking a password since verification already happened outside Spring Security">
  <rect x="15" y="20" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="105" y="45" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">X.509 client certificate</text>

  <rect x="15" y="70" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="105" y="95" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">SiteMinder header (SM_USER)</text>

  <rect x="15" y="120" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="105" y="145" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">J2EE container Principal</text>

  <rect x="250" y="70" width="180" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="340" y="87" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">AbstractPreAuthenticated</text>
  <text x="340" y="100" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ProcessingFilter</text>

  <rect x="470" y="70" width="150" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="545" y="87" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">load authorities</text>
  <text x="545" y="100" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(NO password check)</text>

  <defs><marker id="a31" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="41" x2="250" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a31)"/>
  <line x1="195" y1="91" x2="250" y2="91" stroke="#8b949e" stroke-width="1" marker-end="url(#a31)"/>
  <line x1="195" y1="141" x2="250" y2="102" stroke="#8b949e" stroke-width="1" marker-end="url(#a31)"/>
  <line x1="430" y1="91" x2="470" y2="91" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a31)"/>
</svg>

Three different external sources of already-verified identity, all converging into the same "load authorities only" pattern.

## 5. Runnable example

The scenario: model a SiteMinder-style header-based pre-authentication filter, then add trust boundary validation (only accept the header from a genuinely trusted proxy IP), then add X.509 alongside it behind a shared abstraction, proving both mechanisms fit the identical pattern.

### Level 1 — Basic

A minimal pre-authentication filter reading a trusted proxy header and loading authorities without any password check.

```java
import java.util.*;

public class PreAuthLevel1 {
    record Request(Map<String, String> headers) {}
    record UserAuthorities(String username, Set<String> roles) {}

    static Map<String, UserAuthorities> userDirectory = Map.of(
            "alice", new UserAuthorities("alice", Set.of("ROLE_USER", "ROLE_ADMIN"))
    );

    // models getPreAuthenticatedPrincipal(request) -- reads the identity a TRUSTED proxy already established
    static String extractPrincipal(Request request) {
        return request.headers().get("SM_USER"); // set ONLY by the trusted SiteMinder proxy, never by the end client
    }

    static UserAuthorities authenticate(Request request) {
        String principal = extractPrincipal(request);
        if (principal == null) throw new RuntimeException("no SM_USER header -- request did not come through SSO proxy");
        UserAuthorities authorities = userDirectory.get(principal);
        if (authorities == null) throw new RuntimeException("no such user in local directory: " + principal);
        return authorities; // NOTE: no password was ever checked -- identity was already trusted
    }

    public static void main(String[] args) {
        Request request = new Request(Map.of("SM_USER", "alice"));
        System.out.println("authenticated: " + authenticate(request));
    }
}
```

How to run: `java PreAuthLevel1.java`

`authenticate` never asks for or checks any password — it trusts that the presence of `SM_USER` in the request already represents a verified identity from the SSO proxy, and its only remaining job is to look up `alice`'s authorities in the local `userDirectory`.

### Level 2 — Intermediate

Add a trust boundary check: the `SM_USER` header must only be honored when it genuinely came from the trusted proxy's IP, since an end client could otherwise simply forge the header directly.

```java
import java.util.*;

public class PreAuthLevel2 {
    record Request(Map<String, String> headers, String sourceIp) {}
    record UserAuthorities(String username, Set<String> roles) {}

    static Map<String, UserAuthorities> userDirectory = Map.of(
            "alice", new UserAuthorities("alice", Set.of("ROLE_USER", "ROLE_ADMIN"))
    );
    static Set<String> trustedProxyIps = Set.of("10.0.0.1"); // ONLY this IP may set SM_USER meaningfully

    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }

    static UserAuthorities authenticate(Request request) {
        if (!trustedProxyIps.contains(request.sourceIp())) {
            // CRITICAL: reject the header ENTIRELY if it didn't arrive via the trusted proxy,
            // regardless of what value it claims -- otherwise ANY client could forge SM_USER: admin
            throw new AuthenticationException("SM_USER header ignored -- request did not originate from a trusted proxy IP ("
                    + request.sourceIp() + ")");
        }
        String principal = request.headers().get("SM_USER");
        if (principal == null) throw new AuthenticationException("trusted proxy request missing SM_USER header");
        UserAuthorities authorities = userDirectory.get(principal);
        if (authorities == null) throw new AuthenticationException("no such user in local directory: " + principal);
        return authorities;
    }

    public static void main(String[] args) {
        Request viaTrustedProxy = new Request(Map.of("SM_USER", "alice"), "10.0.0.1");
        System.out.println("via trusted proxy: " + authenticate(viaTrustedProxy));

        Request forgedDirectly = new Request(Map.of("SM_USER", "alice"), "203.0.113.50"); // attacker, NOT the proxy
        try {
            authenticate(forgedDirectly);
        } catch (AuthenticationException ex) {
            System.out.println("forged header attempt: " + ex.getMessage());
        }
    }
}
```

How to run: `java PreAuthLevel2.java`

The exact same `SM_USER: alice` header value is honored when it arrives from `10.0.0.1` (the trusted proxy) but rejected when it arrives from any other IP — this trust-boundary enforcement is essential and non-optional for header-based pre-authentication, since without it any client could simply set the header themselves and impersonate any user.

### Level 3 — Advanced

Unify header-based (SiteMinder-style) and certificate-based (X.509) pre-authentication behind a shared abstraction, proving both are the same pattern with a different "already-verified identity extraction" step.

```java
import java.util.*;
import java.util.function.Function;

public class PreAuthLevel3 {
    record Request(Map<String, String> headers, String sourceIp, String clientCertSubjectDN) {}
    record UserAuthorities(String username, Set<String> roles) {}

    static Map<String, UserAuthorities> userDirectory = Map.of(
            "alice", new UserAuthorities("alice", Set.of("ROLE_USER", "ROLE_ADMIN")),
            "bob", new UserAuthorities("bob", Set.of("ROLE_USER"))
    );
    static Set<String> trustedProxyIps = Set.of("10.0.0.1");

    static class AuthenticationException extends RuntimeException {
        AuthenticationException(String msg) { super(msg); }
    }

    interface PreAuthenticatedPrincipalExtractor extends Function<Request, String> {}

    static PreAuthenticatedPrincipalExtractor siteMinderExtractor = request -> {
        if (!trustedProxyIps.contains(request.sourceIp())) {
            throw new AuthenticationException("SM_USER ignored -- untrusted source IP " + request.sourceIp());
        }
        return request.headers().get("SM_USER");
    };

    static PreAuthenticatedPrincipalExtractor x509Extractor = request -> {
        if (request.clientCertSubjectDN() == null) throw new AuthenticationException("no client certificate presented");
        // parse "CN=alice,OU=Engineering,O=Example" -> "alice"
        for (String part : request.clientCertSubjectDN().split(",")) {
            if (part.trim().startsWith("CN=")) return part.trim().substring(3);
        }
        throw new AuthenticationException("certificate subject DN missing CN");
    };

    // the SHARED provider logic: identical regardless of which extractor supplied the principal
    static UserAuthorities authenticate(Request request, PreAuthenticatedPrincipalExtractor extractor) {
        String principal = extractor.apply(request); // the ONLY part that differs between mechanisms
        UserAuthorities authorities = userDirectory.get(principal);
        if (authorities == null) throw new AuthenticationException("no such user in local directory: " + principal);
        return authorities;
    }

    public static void main(String[] args) {
        Request siteMinderRequest = new Request(Map.of("SM_USER", "alice"), "10.0.0.1", null);
        System.out.println("via SiteMinder: " + authenticate(siteMinderRequest, siteMinderExtractor));

        Request x509Request = new Request(Map.of(), null, "CN=bob,OU=Engineering,O=Example");
        System.out.println("via X.509 cert: " + authenticate(x509Request, x509Extractor));
    }
}
```

How to run: `java PreAuthLevel3.java`

`authenticate` itself is completely mechanism-agnostic — it never inspects headers or certificates directly, only calls whichever `PreAuthenticatedPrincipalExtractor` it's given and looks up the resulting `principal` in `userDirectory`; `siteMinderExtractor` and `x509Extractor` are the only mechanism-specific pieces, exactly mirroring how `AbstractPreAuthenticatedProcessingFilter` factors out the shared authentication lifecycle while leaving `getPreAuthenticatedPrincipal` as the one method each concrete subclass implements differently.

## 6. Walkthrough

Trace `authenticate(x509Request, x509Extractor)` from Level 3.

1. `authenticate` first calls `extractor.apply(request)`, which for this call is `x509Extractor` — inside, `request.clientCertSubjectDN()` is `"CN=bob,OU=Engineering,O=Example"`, not `null`, so the method proceeds past the initial guard.
2. `x509Extractor` splits the subject DN string on commas, producing `["CN=bob", "OU=Engineering", "O=Example"]`, then iterates looking for the part starting with `"CN="` — the first element matches, so it returns `"CN=bob".substring(3)`, which is `"bob"`.
3. Back in `authenticate`, `principal` is now `"bob"`; `userDirectory.get("bob")` finds `new UserAuthorities("bob", Set.of("ROLE_USER"))`, which is non-null, so the final `if` guard is skipped.
4. The method returns this `UserAuthorities` object directly — note that at no point in this entire trace was any password, secret, or credential ever compared; the client's certificate was already verified during the TLS handshake, well before this code ever ran, and this code's entire job was extracting the already-trusted identity (`bob`) and looking up his authorities.
5. Contrast this with the `siteMinderRequest` call just above it: `siteMinderExtractor` instead checks `request.sourceIp()` against `trustedProxyIps` before trusting the `SM_USER` header at all — a different verification-of-trust step specific to that mechanism, but the shared `authenticate` function downstream is identical for both.

```
x509Request  -> x509Extractor: parse "CN=bob,..." -> principal="bob" -> lookup -> UserAuthorities(bob, {ROLE_USER})
siteMinderRequest -> siteMinderExtractor: check trusted IP, then read SM_USER header -> principal="alice" -> lookup -> UserAuthorities(alice, {ROLE_USER, ROLE_ADMIN})
(the SAME authenticate() function handles both, differing only in how principal is extracted)
```

## 7. Gotchas & takeaways

> **Gotcha:** header-based pre-authentication (SiteMinder-style) is only as secure as the guarantee that the trusted header can *never* reach the application directly from an end client — if the application server is ever reachable other than through the trusted proxy (a misconfigured load balancer, a direct network path bypassing the proxy), an attacker can simply set `SM_USER: admin` themselves and impersonate any user. This trust boundary must be enforced at the network/infrastructure level, not just checked opportunistically in application code.

- Pre-authentication scenarios (X.509, SiteMinder-style proxies, J2EE container auth) shift Spring Security's role from "verify and authorize" to "trust and authorize only" — the actual credential verification happened in a different, already-trusted layer.
- `AbstractPreAuthenticatedProcessingFilter` factors out the shared lifecycle; a concrete subclass only supplies `getPreAuthenticatedPrincipal` (and typically a filler value for `getPreAuthenticatedCredentials`, since there's no real credential to extract).
- Header-based mechanisms absolutely require verifying the request's origin (source IP, mutual TLS between proxy and application) before trusting the header at all — the header itself carries no inherent proof of authenticity.
- `PreAuthenticatedAuthenticationProvider` pairs with a `UserDetailsService` purely to load authorities for the already-trusted principal — it is fundamentally different from `DaoAuthenticationProvider`, which additionally verifies a password.
