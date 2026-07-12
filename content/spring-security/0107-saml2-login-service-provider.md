---
card: spring-security
gi: 107
slug: saml2-login-service-provider
title: "SAML2 login (service provider)"
---

## 1. What it is

`saml2Login()` is the `HttpSecurity` DSL method that plays the same role for SAML 2.0 that `oauth2Login()` (card 0088) plays for OAuth2/OIDC: it wires a complete "log in via your corporate identity provider" flow into a `SecurityFilterChain`, but using SAML's XML-based assertion exchange instead of OAuth2's token exchange. In SAML terminology, your application is the **Service Provider** (SP) — the thing a user wants to access — and the identity system (Okta, ADFS, Azure AD, PingFederate) is the **Identity Provider** (IdP) — the thing that actually authenticates the user and vouches for their identity via a signed XML document called an **assertion**. Under the hood, `saml2Login()` registers `Saml2WebSsoAuthenticationFilter`, which handles the IdP's POST-back (by default at `/login/saml2/sso/{registrationId}`), validates the assertion's signature and conditions, and builds a `Saml2AuthenticatedPrincipal` from it.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/", "/error", "/saml2/**", "/login/**").permitAll()
            .anyRequest().authenticated())
        .saml2Login(Customizer.withDefaults());
    return http.build();
}
```

## 2. Why & when

SAML predates OAuth2/OIDC by roughly a decade and remains the entrenched standard inside large enterprises — many corporate identity providers (particularly older or more conservative IT deployments, universities, government systems) support SAML as their primary or only federated login protocol, sometimes without OIDC support at all. An application that needs to be adopted inside such organizations has no choice but to speak SAML, regardless of how much simpler OAuth2/OIDC's JSON-over-HTTPS exchange is by comparison — SAML's XML, digital signatures, and multi-step metadata exchange are the price of admission to that ecosystem.

Reach for `saml2Login()` when:

- Integrating with an enterprise customer's existing identity infrastructure where SAML is the supported (or only) federation protocol — common with Active Directory Federation Services (ADFS), many Okta/Azure AD configurations in "classic" mode, and higher-education Shibboleth deployments.
- Building a B2B SaaS product where large customers require Single Sign-On via their own identity provider as a contractual or compliance requirement, and that customer's identity team hands you a SAML metadata document rather than an OIDC discovery URL.
- The identity provider itself only exposes a SAML endpoint — some legacy or specialized identity systems never adopted OIDC and SAML is the only federation option available.

It's not mutually exclusive with `oauth2Login()` or `formLogin()` — a single application can offer several login paths side by side, letting different users (or different customer organizations) authenticate however their own environment supports.

## 3. Core concept

```
saml2Login() registers Saml2WebSsoAuthenticationFilter against every configured RelyingPartyRegistration (card 0108).

High-level steps for ONE identity provider:
  1. Browser asks the SP to start login          -> GET /saml2/authenticate/{registrationId}
  2. SP redirects (or auto-submits a form) to the IdP's SSO endpoint,
       carrying a SAML AuthnRequest (optionally signed)
  3. User authenticates AT THE IDP                -> entirely outside Spring Security's code
  4. IdP POSTs an XML SAMLResponse (containing a signed Assertion) back to the SP's ACS endpoint
       -> POST /login/saml2/sso/{registrationId}
  5. Saml2WebSsoAuthenticationFilter catches that POST and:
       a. verifies the Assertion's XML signature against the IdP's trusted certificate
       b. checks conditions: NotBefore/NotOnOrAfter (a validity window), the intended Audience
       c. extracts the NameID and any additional Attributes (email, groups, department, ...)
  6. Filter wraps the result as a Saml2AuthenticatedPrincipal -> AuthenticationManager -> SecurityContextHolder

Steps 1-4's exact metadata (SSO endpoint, certificates, entity IDs) is RelyingPartyRegistration's job (card 0108).
```

Everything downstream of step 6 — `@AuthenticationPrincipal`, authorization checks — behaves exactly as it would for `formLogin()` or `oauth2Login()`, since the resulting `Authentication` is the same kind of object regardless of which protocol produced it.

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence diagram of SAML2 login the browser asks the service provider to start login the service provider redirects the browser to the identity provider with an AuthnRequest the browser authenticates there and the identity provider posts back a signed SAMLResponse to the service providers assertion consumer service endpoint which validates the signature and builds an authenticated principal">
  <text x="90" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Service Provider</text>
  <text x="340" y="24" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="590" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Identity Provider</text>

  <line x1="90" y1="35" x2="90" y2="245" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="340" y1="35" x2="340" y2="245" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="590" y1="35" x2="590" y2="245" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <line x1="340" y1="55" x2="95" y2="55" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#s107)"/>
  <text x="340" y="48" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">1. GET /saml2/authenticate/okta</text>

  <line x1="90" y1="85" x2="335" y2="85" stroke="#6db33f" stroke-width="1.5" marker-end="url(#s107b)"/>
  <text x="95" y="78" fill="#e6edf3" font-size="8.5" font-family="sans-serif">2. redirect + AuthnRequest</text>

  <line x1="340" y1="115" x2="585" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#s107)"/>
  <text x="345" y="108" fill="#e6edf3" font-size="8.5" font-family="sans-serif">3. GET SSO endpoint (user logs in)</text>

  <line x1="590" y1="145" x2="335" y2="145" stroke="#8b949e" stroke-width="1.5" marker-end="url(#s107c)"/>
  <text x="585" y="138" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">4. POST SAMLResponse (signed Assertion)</text>

  <line x1="340" y1="175" x2="95" y2="175" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#s107b)"/>
  <text x="340" y="168" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">5. POST /login/saml2/sso/okta (ACS)</text>

  <rect x="40" y="188" width="260" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="170" y="204" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">6. verify signature, check conditions</text>
  <text x="170" y="218" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">   -&gt; Saml2AuthenticatedPrincipal</text>

  <defs>
    <marker id="s107" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="s107b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="s107c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

The assertion arrives via a browser-mediated POST, but its trustworthiness rests entirely on the XML signature the SP verifies in step 6 — there is no separate server-to-server exchange like OAuth2's code-for-token hop.

## 5. Runnable example

The scenario: model a signed SAML assertion and the SP's validation of it, growing from a bare signature-and-identity check into full condition validation (validity window, audience), then into extracting attributes and rejecting a forged assertion.

### Level 1 — Basic

A minimal assertion with a signature check.

```java
import java.util.*;

public class Saml2LoginLevel1 {
    record Assertion(String nameId, String signature, String issuer) {}

    static class IdentityProvider {
        private final String trustedSignaturePrefix;
        IdentityProvider(String trustedSignaturePrefix) { this.trustedSignaturePrefix = trustedSignaturePrefix; }

        // simulates signing an assertion with the IdP's own private key
        Assertion issueAssertion(String nameId) {
            return new Assertion(nameId, trustedSignaturePrefix + "-signed-" + nameId, "https://idp.example.com");
        }
    }

    static class ServiceProvider {
        private final String trustedSignaturePrefix; // stands in for the IdP's trusted public certificate

        ServiceProvider(String trustedSignaturePrefix) { this.trustedSignaturePrefix = trustedSignaturePrefix; }

        String authenticate(Assertion assertion) {
            if (!assertion.signature().startsWith(trustedSignaturePrefix + "-signed-")) {
                throw new IllegalStateException("signature verification failed");
            }
            return assertion.nameId();
        }
    }

    public static void main(String[] args) {
        IdentityProvider idp = new IdentityProvider("okta-key-1");
        ServiceProvider sp = new ServiceProvider("okta-key-1");

        Assertion assertion = idp.issueAssertion("alice@example.com");
        String authenticatedName = sp.authenticate(assertion);

        System.out.println("authenticated: " + authenticatedName);
    }
}
```

**How to run:** save as `Saml2LoginLevel1.java`, run `java Saml2LoginLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated: alice@example.com
```

`ServiceProvider.authenticate` mirrors the core of `Saml2WebSsoAuthenticationFilter`'s job: verify the assertion was really signed by the trusted IdP before trusting anything else about it — here, a shared "key prefix" stands in for real XML digital signature verification.

### Level 2 — Intermediate

Add the validity window (`NotBefore`/`NotOnOrAfter`) and audience checks — an assertion valid by signature alone is not automatically usable right now, or for this application.

```java
import java.time.*;
import java.util.*;

public class Saml2LoginLevel2 {
    record Assertion(String nameId, String signature, String issuer,
                      Instant notBefore, Instant notOnOrAfter, String audience) {}

    static class Saml2ValidationException extends RuntimeException {
        Saml2ValidationException(String message) { super(message); }
    }

    static class ServiceProvider {
        private final String trustedSignaturePrefix;
        private final String ownEntityId; // THIS service provider's own identifier

        ServiceProvider(String trustedSignaturePrefix, String ownEntityId) {
            this.trustedSignaturePrefix = trustedSignaturePrefix;
            this.ownEntityId = ownEntityId;
        }

        String authenticate(Assertion assertion) {
            if (!assertion.signature().startsWith(trustedSignaturePrefix + "-signed-")) {
                throw new Saml2ValidationException("signature verification failed");
            }
            Instant now = Instant.now();
            if (now.isBefore(assertion.notBefore())) {
                throw new Saml2ValidationException("assertion not yet valid (NotBefore in the future)");
            }
            if (!now.isBefore(assertion.notOnOrAfter())) {
                throw new Saml2ValidationException("assertion expired (NotOnOrAfter has passed)");
            }
            if (!ownEntityId.equals(assertion.audience())) {
                throw new Saml2ValidationException("audience mismatch: assertion was not issued for " + ownEntityId);
            }
            return assertion.nameId();
        }
    }

    public static void main(String[] args) {
        ServiceProvider sp = new ServiceProvider("okta-key-1", "https://app.example.com/saml2/service-provider-metadata/okta");

        Assertion valid = new Assertion("alice@example.com", "okta-key-1-signed-alice@example.com",
                "https://idp.example.com", Instant.now().minusSeconds(10), Instant.now().plusSeconds(300),
                "https://app.example.com/saml2/service-provider-metadata/okta");

        Assertion wrongAudience = new Assertion("alice@example.com", "okta-key-1-signed-alice@example.com",
                "https://idp.example.com", Instant.now().minusSeconds(10), Instant.now().plusSeconds(300),
                "https://a-DIFFERENT-app.example.com/saml2/service-provider-metadata/okta");

        System.out.println("valid assertion: " + sp.authenticate(valid));
        try {
            sp.authenticate(wrongAudience);
        } catch (Saml2ValidationException e) {
            System.out.println("wrong audience rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `Saml2LoginLevel2.java`, run `java Saml2LoginLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
valid assertion: alice@example.com
wrong audience rejected: audience mismatch: assertion was not issued for https://app.example.com/saml2/service-provider-metadata/okta
```

What changed: `authenticate` now checks the assertion's validity window and audience in addition to its signature — an assertion genuinely signed by the trusted IdP but intended for a *different* service provider's own entity id is rejected, exactly like OAuth2's audience check (card 0103) prevents a token issued for one resource server from being accepted by another.

### Level 3 — Advanced

Extract attributes (email, groups) alongside the `NameID`, and demonstrate a forged assertion — one whose signature doesn't match any trusted key at all — being rejected before any of its claimed attributes are ever trusted.

```java
import java.time.*;
import java.util.*;

public class Saml2LoginLevel3 {
    record Assertion(String nameId, String signature, String issuer,
                      Instant notBefore, Instant notOnOrAfter, String audience,
                      Map<String, List<String>> attributes) {}

    record Saml2AuthenticatedPrincipal(String name, Map<String, List<String>> attributes) {
        List<String> getAttribute(String name) { return attributes.getOrDefault(name, List.of()); }
    }

    static class Saml2ValidationException extends RuntimeException {
        Saml2ValidationException(String message) { super(message); }
    }

    static class ServiceProvider {
        private final Set<String> trustedSignaturePrefixes; // could trust MULTIPLE IdP certs during rotation
        private final String ownEntityId;

        ServiceProvider(Set<String> trustedSignaturePrefixes, String ownEntityId) {
            this.trustedSignaturePrefixes = trustedSignaturePrefixes;
            this.ownEntityId = ownEntityId;
        }

        Saml2AuthenticatedPrincipal authenticate(Assertion assertion) {
            boolean signatureTrusted = trustedSignaturePrefixes.stream()
                    .anyMatch(prefix -> assertion.signature().startsWith(prefix + "-signed-"));
            if (!signatureTrusted) {
                throw new Saml2ValidationException("signature verification failed -- not signed by any trusted IdP certificate");
            }
            Instant now = Instant.now();
            if (now.isBefore(assertion.notBefore()) || !now.isBefore(assertion.notOnOrAfter())) {
                throw new Saml2ValidationException("assertion outside its validity window");
            }
            if (!ownEntityId.equals(assertion.audience())) {
                throw new Saml2ValidationException("audience mismatch");
            }
            return new Saml2AuthenticatedPrincipal(assertion.nameId(), assertion.attributes());
        }
    }

    public static void main(String[] args) {
        ServiceProvider sp = new ServiceProvider(Set.of("okta-key-1", "okta-key-2"), // TWO trusted keys, mid-rotation
                "https://app.example.com/saml2/service-provider-metadata/okta");

        Assertion genuine = new Assertion("alice@example.com", "okta-key-2-signed-alice@example.com",
                "https://idp.example.com", Instant.now().minusSeconds(5), Instant.now().plusSeconds(300),
                "https://app.example.com/saml2/service-provider-metadata/okta",
                Map.of("email", List.of("alice@example.com"), "groups", List.of("engineering", "managers")));

        // an attacker attempting to forge an assertion, signed with a key the SP does NOT trust
        Assertion forged = new Assertion("admin@example.com", "attacker-controlled-key-signed-admin@example.com",
                "https://idp.example.com", Instant.now().minusSeconds(5), Instant.now().plusSeconds(300),
                "https://app.example.com/saml2/service-provider-metadata/okta",
                Map.of("groups", List.of("super-admins")));

        Saml2AuthenticatedPrincipal principal = sp.authenticate(genuine);
        System.out.println("authenticated: " + principal.name() + " groups=" + principal.getAttribute("groups"));

        try {
            sp.authenticate(forged);
        } catch (Saml2ValidationException e) {
            System.out.println("forged assertion rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `Saml2LoginLevel3.java`, run `java Saml2LoginLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated: alice@example.com groups=[engineering, managers]
forged assertion rejected: signature verification failed -- not signed by any trusted IdP certificate
```

What changed: `trustedSignaturePrefixes` is now a set (supporting key rotation, mirroring card 0101's JWK Set discussion for JWTs), and attributes (`groups`, `email`) are extracted alongside the `NameID` into the returned principal — but critically, the forged assertion's claimed `groups=["super-admins"]` is never even inspected, because the signature check fails and throws before attribute extraction is ever reached, regardless of how convincing the forged claims might look.

## 6. Walkthrough

Trace alice's successful login from Level 3 end to end.

**Step 1 — the browser starts the login:**
```
GET /saml2/authenticate/okta HTTP/1.1
Host: app.example.com
```
The SP redirects (or auto-submits a self-posting HTML form, common for larger `AuthnRequest`s) to the IdP's SSO endpoint.

**Step 2 — the user authenticates at the IdP** — outside Spring Security's code entirely, exactly as with OAuth2's redirect step.

**Step 3 — the IdP posts the SAMLResponse back to the SP's Assertion Consumer Service (ACS) endpoint:**
```
POST /login/saml2/sso/okta HTTP/1.1
Host: app.example.com
Content-Type: application/x-www-form-urlencoded

SAMLResponse=PHNhbWxwOlJlc3BvbnNlIC4uLg%3D%3D
```
The base64-encoded value decodes to an XML `Response` document containing the signed `Assertion` — corresponding to `genuine` in Level 3's code.

**Step 4 — signature verification.** `authenticate` checks `assertion.signature()` against every prefix in `trustedSignaturePrefixes`; `"okta-key-2-signed-alice@example.com"` matches the `"okta-key-2"` entry (the IdP's *second*, newer signing key — the SP trusts both during a rotation window, exactly mirroring card 0101's JWK Set rotation pattern for JWTs).

**Step 5 — validity window and audience checks.** `notBefore`/`notOnOrAfter` bound a narrow window (a few minutes, typically) around when the assertion was issued; `now` falls inside it. `audience` matches the SP's own configured entity id.

**Step 6 — attribute extraction.** `assertion.attributes()` — `{"email": ["alice@example.com"], "groups": ["engineering", "managers"]}` — is carried straight into the returned `Saml2AuthenticatedPrincipal`, alongside `nameId`.

**Step 7 — the SP's response to the browser, completing the flow:**
```
HTTP/1.1 302 Found
Location: https://app.example.com/
Set-Cookie: JSESSIONID=...; HttpOnly; Secure
```
A controller's `@AuthenticationPrincipal Saml2AuthenticatedPrincipal principal` now resolves to this object; `principal.getAttribute("groups")` returns `["engineering", "managers"]`.

**Contrast — the forged assertion.** Its `signature`, `"attacker-controlled-key-signed-admin@example.com"`, matches none of `{"okta-key-1", "okta-key-2"}`'s expected prefixes — `signatureTrusted` is `false`, and `authenticate` throws immediately. The forged assertion's `groups=["super-admins"]` claim is never read at all; no principal is ever built from it.

```
genuine assertion: signature matches "okta-key-2" (trusted, mid-rotation) -> validity OK -> audience OK -> AUTHENTICATED
forged assertion:  signature matches NEITHER trusted key                 -> REJECTED before attributes ever inspected
```

## 7. Gotchas & takeaways

> **Gotcha:** an assertion's attributes (email, groups, department) are only as trustworthy as the signature that covers them — never read or act on an attribute from an `Assertion` object before the signature check has passed. A forged or tampered assertion can claim anything in its attribute set; the signature is what proves those claims actually came from the trusted IdP.

- SAML2 login plays the OIDC role for enterprise identity federation, using signed XML assertions delivered via a browser-mediated POST rather than a server-to-server token exchange.
- The Service Provider (your application) never talks to the Identity Provider directly during login — it only ever receives and verifies what the browser POSTs back, making the assertion's digital signature the entire basis of trust.
- Validity window (`NotBefore`/`NotOnOrAfter`) and audience checks are just as necessary for SAML assertions as `exp`/`aud` checks are for JWTs — a validly-signed assertion can still be expired, not-yet-valid, or intended for a different service provider.
- Trusting multiple IdP signing certificates simultaneously (as in Level 3) is how key rotation happens without downtime — the same pattern as a JWK Set holding multiple valid keys during a JWT issuer's rotation.
- The next three cards unpack what this card treats as configuration: `RelyingPartyRegistration` (the SP-side metadata, card 0108), SAML2 logout (card 0109), and where the IdP's trusted certificates and endpoints actually come from (card 0110).
