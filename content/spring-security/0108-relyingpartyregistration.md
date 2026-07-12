---
card: spring-security
gi: 108
slug: relyingpartyregistration
title: "RelyingPartyRegistration"
---

## 1. What it is

`RelyingPartyRegistration` is SAML2's equivalent of card 0089's `ClientRegistration`: the immutable, per-identity-provider configuration object holding everything the SP needs to complete a login against one specific IdP — its own entity id, its ACS (Assertion Consumer Service) location, its own signing/decryption credentials, and the IdP's SSO endpoint URL plus trusted verification certificate. `RelyingPartyRegistrationRepository` is the lookup interface, resolved by `registrationId` (the segment that appears in `/saml2/authenticate/{registrationId}` and `/login/saml2/sso/{registrationId}`), exactly mirroring `ClientRegistrationRepository`'s role for OAuth2.

```java
@Bean
public RelyingPartyRegistrationRepository relyingPartyRegistrationRepository() {
    RelyingPartyRegistration okta = RelyingPartyRegistration.withRegistrationId("okta")
            .entityId("https://app.example.com/saml2/service-provider-metadata/okta")
            .assertingPartyDetails(party -> party
                    .entityId("https://idp.okta.com/exk1a2b3c4d5e")
                    .singleSignOnServiceLocation("https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml")
                    .verificationX509Credentials(c -> c.add(oktaSigningCertificate())))
            .build();
    return new InMemoryRelyingPartyRegistrationRepository(okta);
}
```

## 2. Why & when

Card 0107 described the login flow in the abstract, treating "the SP knows the IdP's SSO endpoint and trusted certificate" as a given — but every one of those specific details differs completely between identity providers, and an application supporting more than one IdP (different customer organizations, each running their own SAML setup) needs a typed container for exactly that per-relationship configuration, plus a way to look one up by `registrationId` from an incoming request path. That's precisely `RelyingPartyRegistration`'s job, decoupling the generic SAML protocol machinery (card 0107's filters) from any one IdP's specific endpoints and keys.

Reach for this pair when:

- Onboarding a new enterprise customer's identity provider — this typically means building a new `RelyingPartyRegistration` from the metadata the customer's IT team provides (either a metadata XML document, or individually as SSO URL + certificate).
- Deciding between building a registration manually (`RelyingPartyRegistration.withRegistrationId(...)`) versus from asserting-party metadata (`RelyingPartyRegistrations.fromMetadataLocation(...)`, card 0110) — metadata-driven construction is preferred whenever the IdP publishes a metadata document, since it avoids hand-transcribing URLs and certificates that are easy to get subtly wrong.
- Debugging a login that fails at the "wrong audience" or "signature verification failed" stage — nearly every such failure traces back to exactly one field in the resolved `RelyingPartyRegistration` (a stale certificate, a mismatched entity id) being incorrect.
- Supporting multiple IdPs simultaneously (multi-tenant SAML, similar to card 0105's multi-issuer OAuth2 pattern) — each customer organization gets its own `RelyingPartyRegistration`, looked up by a `registrationId` unique to that tenant.

## 3. Core concept

```
RelyingPartyRegistration (ONE per identity provider relationship, immutable):
    registrationId              -- "okta" -- appears in /saml2/authenticate/{registrationId}
    entityId                    -- THIS service provider's own identifier for this relationship
    assertionConsumerServiceLocation -- where THIS SP expects the IdP to POST assertions back to
    signingX509Credentials      -- THIS SP's own key pair, for signing outbound AuthnRequests (optional)
    decryptionX509Credentials   -- THIS SP's own key pair, for decrypting encrypted assertions (optional)

    assertingPartyDetails (the IDP's side, from THIS SP's point of view):
        entityId                        -- the IdP's own identifier
        singleSignOnServiceLocation     -- where to send the browser to start login
        verificationX509Credentials     -- the IdP's PUBLIC certificate(s), used to verify assertion signatures
        singleLogoutServiceLocation     -- where to send logout requests (card 0109)

RelyingPartyRegistrationRepository:
    findByRegistrationId(String registrationId) -> RelyingPartyRegistration

InMemoryRelyingPartyRegistrationRepository -- default; built from configuration/code at startup
```

Every field used across card 0107's entire login flow — both directions — traces back to exactly one `RelyingPartyRegistration`, resolved once by `registrationId` and never mutated afterward.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a RelyingPartyRegistration holding this service providers own entity id and ACS location alongside the asserting party details for one identity provider including its sso location and verification certificate all resolved together by registration id">
  <rect x="20" y="20" width="600" height="200" rx="9" fill="#1c2430" stroke="#8b949e" stroke-width="1.2" stroke-dasharray="4,3"/>
  <text x="320" y="42" fill="#8b949e" font-size="10.5" text-anchor="middle" font-family="sans-serif">RelyingPartyRegistration (registrationId="okta")</text>

  <rect x="40" y="58" width="270" height="140" rx="7" fill="#161b22" stroke="#6db33f" stroke-width="1.4"/>
  <text x="175" y="80" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">THIS service provider's own config</text>
  <text x="175" y="100" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">entityId</text>
  <text x="175" y="118" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">assertionConsumerServiceLocation</text>
  <text x="175" y="136" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">signingX509Credentials (optional)</text>
  <text x="175" y="154" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">decryptionX509Credentials (optional)</text>

  <rect x="330" y="58" width="270" height="140" rx="7" fill="#161b22" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="465" y="80" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">assertingPartyDetails (the IdP)</text>
  <text x="465" y="100" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">entityId</text>
  <text x="465" y="118" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">singleSignOnServiceLocation</text>
  <text x="465" y="136" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">verificationX509Credentials</text>
  <text x="465" y="154" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">singleLogoutServiceLocation</text>

  <defs></defs>
</svg>

Both halves — the SP's own identity and the trusted IdP's endpoints/certificate — live in one immutable object, resolved together by `registrationId`.

## 5. Runnable example

The scenario: model a `RelyingPartyRegistration` and repository, grow it from one IdP into several, then add validation that catches a misconfigured registration (a missing verification certificate) before it can cause confusing runtime signature failures.

### Level 1 — Basic

One registration, resolved by id.

```java
import java.util.*;

public class RelyingPartyLevel1 {
    record AssertingPartyDetails(String entityId, String ssoLocation, String verificationCert) {}
    record RelyingPartyRegistration(String registrationId, String ownEntityId, String acsLocation,
                                     AssertingPartyDetails assertingParty) {}

    static class InMemoryRelyingPartyRegistrationRepository {
        private final Map<String, RelyingPartyRegistration> registrations = new LinkedHashMap<>();
        InMemoryRelyingPartyRegistrationRepository(RelyingPartyRegistration... regs) {
            for (var r : regs) registrations.put(r.registrationId(), r);
        }
        RelyingPartyRegistration findByRegistrationId(String id) { return registrations.get(id); }
    }

    public static void main(String[] args) {
        RelyingPartyRegistration okta = new RelyingPartyRegistration("okta",
                "https://app.example.com/saml2/service-provider-metadata/okta",
                "https://app.example.com/login/saml2/sso/okta",
                new AssertingPartyDetails("https://idp.okta.com/exk1a2b3c4d5e",
                        "https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml", "okta-cert-abc"));

        InMemoryRelyingPartyRegistrationRepository repository = new InMemoryRelyingPartyRegistrationRepository(okta);

        RelyingPartyRegistration resolved = repository.findByRegistrationId("okta");
        System.out.println("resolved: " + resolved.registrationId() + " sso=" + resolved.assertingParty().ssoLocation());
        System.out.println("unknown: " + repository.findByRegistrationId("adfs"));
    }
}
```

**How to run:** save as `RelyingPartyLevel1.java`, run `java RelyingPartyLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
resolved: okta sso=https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml
unknown: null
```

The repository is a simple map from `registrationId` to a `RelyingPartyRegistration`, exactly mirroring `ClientRegistrationRepository`'s structure for OAuth2 — a lookup for an unconfigured IdP yields `null` rather than throwing.

### Level 2 — Intermediate

Add a second identity provider, and build the ACS URL from a per-registration template, mirroring card 0089's redirect-URI templating.

```java
import java.util.*;

public class RelyingPartyLevel2 {
    record AssertingPartyDetails(String entityId, String ssoLocation, String verificationCert) {}
    record RelyingPartyRegistration(String registrationId, String ownEntityIdTemplate, String acsLocationTemplate,
                                     AssertingPartyDetails assertingParty) {
        String buildAcsLocation(String baseUrl) {
            return acsLocationTemplate.replace("{baseUrl}", baseUrl).replace("{registrationId}", registrationId);
        }
    }

    static class InMemoryRelyingPartyRegistrationRepository {
        private final Map<String, RelyingPartyRegistration> registrations = new LinkedHashMap<>();
        InMemoryRelyingPartyRegistrationRepository(RelyingPartyRegistration... regs) {
            for (var r : regs) registrations.put(r.registrationId(), r);
        }
        RelyingPartyRegistration findByRegistrationId(String id) { return registrations.get(id); }
    }

    public static void main(String[] args) {
        RelyingPartyRegistration okta = new RelyingPartyRegistration("okta", "{baseUrl}/saml2/service-provider-metadata/{registrationId}",
                "{baseUrl}/login/saml2/sso/{registrationId}",
                new AssertingPartyDetails("https://idp.okta.com/exk1a2b3", "https://idp.okta.com/sso/saml", "okta-cert"));

        RelyingPartyRegistration adfs = new RelyingPartyRegistration("adfs", "{baseUrl}/saml2/service-provider-metadata/{registrationId}",
                "{baseUrl}/login/saml2/sso/{registrationId}",
                new AssertingPartyDetails("https://adfs.corp.example.com/adfs/services/trust",
                        "https://adfs.corp.example.com/adfs/ls/", "adfs-cert"));

        InMemoryRelyingPartyRegistrationRepository repository =
                new InMemoryRelyingPartyRegistrationRepository(okta, adfs);

        for (String id : List.of("okta", "adfs")) {
            RelyingPartyRegistration reg = repository.findByRegistrationId(id);
            System.out.println(id + " -> ACS=" + reg.buildAcsLocation("https://app.example.com")
                    + " SSO=" + reg.assertingParty().ssoLocation());
        }
    }
}
```

**How to run:** save as `RelyingPartyLevel2.java`, run `java RelyingPartyLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
okta -> ACS=https://app.example.com/login/saml2/sso/okta SSO=https://idp.okta.com/sso/saml
adfs -> ACS=https://app.example.com/login/saml2/sso/adfs SSO=https://adfs.corp.example.com/adfs/ls/
```

What changed: two independent identity providers now coexist in one repository, each with its own `assertingParty` details and its own templated ACS URL — an incoming assertion for `okta` is validated against Okta's SSO location and certificate, while one for `adfs` is validated against ADFS's, with neither registration's configuration ever leaking into the other's validation.

### Level 3 — Advanced

Real registrations can be misconfigured — a missing verification certificate, a duplicate registration id. Level 3 adds validation mirroring the fail-fast checks a real `RelyingPartyRegistration.Builder.build()` performs.

```java
import java.util.*;

public class RelyingPartyLevel3 {
    record AssertingPartyDetails(String entityId, String ssoLocation, String verificationCert) {}
    record RelyingPartyRegistration(String registrationId, String ownEntityIdTemplate, String acsLocationTemplate,
                                     AssertingPartyDetails assertingParty) {}

    static class RelyingPartyValidationException extends RuntimeException {
        RelyingPartyValidationException(String message) { super(message); }
    }

    static void validate(RelyingPartyRegistration reg) {
        List<String> problems = new ArrayList<>();
        if (reg.assertingParty() == null) {
            problems.add("assertingPartyDetails is required");
        } else {
            if (reg.assertingParty().ssoLocation() == null || reg.assertingParty().ssoLocation().isBlank())
                problems.add("singleSignOnServiceLocation is required");
            if (reg.assertingParty().verificationCert() == null || reg.assertingParty().verificationCert().isBlank())
                problems.add("verificationX509Credentials is required -- without it, NO assertion can ever be trusted");
        }
        if (!problems.isEmpty()) {
            throw new RelyingPartyValidationException(
                    "invalid registration \"" + reg.registrationId() + "\": " + String.join("; ", problems));
        }
    }

    static class InMemoryRelyingPartyRegistrationRepository {
        private final Map<String, RelyingPartyRegistration> registrations = new LinkedHashMap<>();

        InMemoryRelyingPartyRegistrationRepository(RelyingPartyRegistration... regs) {
            for (var r : regs) {
                if (registrations.containsKey(r.registrationId())) {
                    throw new RelyingPartyValidationException("duplicate registrationId \"" + r.registrationId() + "\"");
                }
                validate(r);
                registrations.put(r.registrationId(), r);
            }
        }
        RelyingPartyRegistration findByRegistrationId(String id) { return registrations.get(id); }
    }

    static void tryBuild(String label, RelyingPartyRegistration... regs) {
        try {
            new InMemoryRelyingPartyRegistrationRepository(regs);
            System.out.println(label + ": OK");
        } catch (RelyingPartyValidationException e) {
            System.out.println(label + ": REJECTED -- " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        RelyingPartyRegistration valid = new RelyingPartyRegistration("okta", "{baseUrl}/saml2/metadata/{registrationId}",
                "{baseUrl}/login/saml2/sso/{registrationId}",
                new AssertingPartyDetails("https://idp.okta.com/exk1", "https://idp.okta.com/sso", "okta-cert-abc"));

        RelyingPartyRegistration missingCert = new RelyingPartyRegistration("misconfigured-idp",
                "{baseUrl}/saml2/metadata/{registrationId}", "{baseUrl}/login/saml2/sso/{registrationId}",
                new AssertingPartyDetails("https://idp.example.com", "https://idp.example.com/sso", null));

        tryBuild("single valid registration", valid);
        tryBuild("missing verification certificate", missingCert);
    }
}
```

**How to run:** save as `RelyingPartyLevel3.java`, run `java RelyingPartyLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
single valid registration: OK
missing verification certificate: REJECTED -- invalid registration "misconfigured-idp": verificationX509Credentials is required -- without it, NO assertion can ever be trusted
```

What changed: `validate` catches a missing verification certificate at registration-build time — a startup-time failure — rather than letting the application boot successfully and only discover the problem the first time a real user's assertion arrives and can't be verified against anything.

## 6. Walkthrough

Trace what happens between application startup and a successful `okta`-registration login, tying it directly to card 0107's flow.

**Step 1 — startup.** `new RelyingPartyRegistration("okta", ...)` is constructed (in a real application, often from a metadata document via card 0110's `RelyingPartyRegistrations.fromMetadataLocation(...)`, rather than by hand as shown here), then validated and stored in the repository — once, at startup.

**Step 2 — inbound request to start login:**
```
GET /saml2/authenticate/okta HTTP/1.1
```
The filter extracts `"okta"` and calls `repository.findByRegistrationId("okta")`, resolving the same object built in step 1.

**Step 3 — building the redirect to the IdP.** The filter reads `assertingParty().ssoLocation()` to know where to send the browser, and `ownEntityIdTemplate`/`acsLocationTemplate` (filled in via `buildAcsLocation`) to construct the `AuthnRequest`'s own identifying fields.

**Step 4 — the IdP's callback, later, arrives at the templated ACS URL** (`/login/saml2/sso/okta`), and the *same* resolved registration's `assertingParty().verificationCert()` is what the assertion's signature gets checked against.

Every field used across both directions of card 0107's flow traces back to this one object, resolved once by `registrationId` and never mutated in between.

## 7. Gotchas & takeaways

> **Gotcha:** `verificationX509Credentials` must be the IdP's own **public** certificate — a common configuration mistake is pasting in the wrong certificate (an old one after IdP-side rotation, or the SP's own certificate by mistake) which causes every single login attempt to fail signature verification with an error that gives no hint the certificate itself is the problem. When *every* login fails at the signature-check stage, verifying this one field first is almost always the fastest path to a fix.

- `RelyingPartyRegistration` is SAML2's equivalent of `ClientRegistration`: immutable, per-IdP configuration, resolved by `registrationId` from `RelyingPartyRegistrationRepository`.
- It holds two distinct halves — this service provider's own identity/keys, and the trusted IdP's endpoints and verification certificate — both needed together to complete a login.
- Building registrations from IdP-published metadata (card 0110) is generally preferable to hand-transcribing URLs and certificates, since metadata-driven construction eliminates an entire class of copy-paste configuration errors.
- A missing or stale verification certificate is the single most common cause of "every SAML login fails" — validating this at startup, rather than discovering it on the first real login attempt, turns a confusing runtime failure into a clear boot-time error.
- Supporting multiple identity providers (multi-tenant SAML) is exactly the same pattern as multiple OAuth2 registrations or multiple trusted JWT issuers (card 0105): one immutable configuration object per relationship, resolved by a stable id.
