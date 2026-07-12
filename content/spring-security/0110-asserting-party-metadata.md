---
card: spring-security
gi: 110
slug: asserting-party-metadata
title: "Asserting party metadata"
---

## 1. What it is

Rather than hand-transcribing an identity provider's SSO endpoint URL, entity id, and signing certificate into code field-by-field (as cards 0107–0108's examples did for clarity), every real SAML identity provider publishes a **metadata document** — an XML file at a well-known URL containing exactly that information in a standardized, machine-readable format. `RelyingPartyRegistrations.fromMetadataLocation(metadataUrl)` is Spring Security's built-in metadata parser: given that one URL, it builds a `RelyingPartyRegistration.Builder` already populated with the IdP's entity id, SSO location, logout location, and verification certificate(s) — eliminating an entire class of copy-paste transcription errors.

```java
@Bean
public RelyingPartyRegistrationRepository relyingPartyRegistrationRepository() {
    RelyingPartyRegistration okta = RelyingPartyRegistrations
            .fromMetadataLocation("https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml/metadata")
            .registrationId("okta")
            .build();
    return new InMemoryRelyingPartyRegistrationRepository(okta);
}
```
```xml
<EntityDescriptor entityID="https://idp.okta.com/exk1a2b3c4d5e">
  <IDPSSODescriptor>
    <KeyDescriptor use="signing">
      <KeyInfo><X509Data><X509Certificate>MIIDpDCCAoygAwIBAgIGA...</X509Certificate></X509Data></KeyInfo>
    </KeyDescriptor>
    <SingleSignOnService Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-Redirect"
                          Location="https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml"/>
  </IDPSSODescriptor>
</EntityDescriptor>
```

## 2. Why & when

Card 0108's `RelyingPartyRegistration` examples built every field by hand for pedagogical clarity, but doing that against a real IdP is exactly the kind of error-prone, manual transcription this card exists to eliminate — a single mistyped character in a base64-encoded certificate, or a URL copied from the wrong environment (staging instead of production), silently breaks every login until someone painstakingly diffs the configuration against the IdP's own published values. Metadata-driven registration treats the IdP's own published document as the single source of truth, fetched (and in production, periodically refreshed) directly from the IdP rather than re-typed by a human.

Reach for metadata-driven registration when:

- Onboarding any real, production identity provider — this should be the default approach, not the exception; hand-built registrations (card 0108's style) are appropriate mainly for tests, documentation, or IdPs that genuinely don't publish metadata.
- The IdP rotates its signing certificate — a resource server (or SP) that refreshes its cached metadata periodically picks up the new certificate automatically, exactly mirroring card 0101's JWK Set rotation story for JWTs, rather than requiring a manual reconfiguration and redeploy.
- Debugging "why doesn't my SP trust this IdP's assertions" — comparing the *actual* fetched metadata document against what's configured is almost always the fastest way to spot a stale or mistyped value.
- Generating your *own* SP's metadata document for the IdP's administrators to consume — `RelyingPartyRegistration` can be rendered back out as metadata XML (via `Saml2MetadataFilter`) for exactly the same reason: giving the other party a machine-readable, unambiguous source of truth rather than a manually-assembled email of URLs and certificates.

## 3. Core concept

```
Metadata document (published by the IdP, at a well-known URL):
    EntityDescriptor
        entityID                          -- the IdP's own identifier
        IDPSSODescriptor
            KeyDescriptor (use="signing")  -- the IdP's PUBLIC certificate(s) for verifying assertions
            SingleSignOnService            -- WHERE to redirect the browser to start login
            SingleLogoutService             -- WHERE to send logout requests (card 0109)

RelyingPartyRegistrations.fromMetadataLocation(url):
  1. fetch the metadata XML from `url`  (a network call, at application startup or on-demand)
  2. parse EntityDescriptor / IDPSSODescriptor
  3. extract entityID, SSO location, logout location, verification certificate(s)
  4. return a Builder ALREADY populated with all of that -- you only need to add YOUR OWN
     SP-side details (registrationId, and optionally your own signing/decryption credentials)

CACHING & rotation:
    a metadata-backed RelyingPartyRegistrationRepository CAN be built to periodically
    re-fetch the metadata document, picking up IdP certificate rotation automatically
    -- exactly the JWK Set rotation story (card 0101), applied to SAML
```

Metadata parsing turns "trust whatever this document currently says" into the operative security model — which is precisely why fetching it only from a URL you actually trust (typically HTTPS, from the IdP's own verified domain) matters as much as anything else in this flow.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing an identity providers published metadata xml document being fetched and parsed into a RelyingPartyRegistration builder populated with entity id sso location and verification certificate which the application then completes with its own registration id">
  <rect x="20" y="30" width="220" height="90" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="130" y="52" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">IdP metadata XML</text>
  <text x="130" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">entityID, SSO location,</text>
  <text x="130" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">signing certificate</text>
  <text x="130" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">published at a well-known URL</text>

  <line x1="240" y1="75" x2="285" y2="75" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#am110)"/>
  <text x="262" y="65" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">fetch + parse</text>

  <rect x="290" y="30" width="220" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="400" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">RelyingPartyRegistration.Builder</text>
  <text x="400" y="72" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">assertingPartyDetails ALREADY set</text>
  <text x="400" y="86" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">from the fetched metadata</text>
  <text x="400" y="104" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">.registrationId("okta") -- YOU add this</text>

  <line x1="400" y1="120" x2="400" y2="150" stroke="#6db33f" stroke-width="1.6" marker-end="url(#am110b)"/>

  <rect x="290" y="152" width="220" height="46" rx="7" fill="#1c2430" stroke="#3fb950" stroke-width="1.4"/>
  <text x="400" y="172" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">complete RelyingPartyRegistration</text>
  <text x="400" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ready to register in the repository</text>

  <defs>
    <marker id="am110" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="am110b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The metadata document supplies everything about the IdP; the application only adds its own registration id and, optionally, its own SP-side credentials.

## 5. Runnable example

The scenario: a from-scratch metadata parser and registration builder, growing from a bare parse-and-build into handling a metadata document with multiple signing certificates (rotation in progress), then into detecting a metadata fetch failure and falling back safely rather than building a broken, half-populated registration.

### Level 1 — Basic

Parse a metadata document into a registration.

```java
import java.util.*;

public class MetadataLevel1 {
    record MetadataDocument(String entityId, String ssoLocation, String signingCertificate) {}
    record RelyingPartyRegistration(String registrationId, String idpEntityId, String ssoLocation, String verificationCert) {}

    static RelyingPartyRegistration fromMetadata(MetadataDocument metadata, String registrationId) {
        return new RelyingPartyRegistration(registrationId, metadata.entityId(), metadata.ssoLocation(), metadata.signingCertificate());
    }

    public static void main(String[] args) {
        MetadataDocument oktaMetadata = new MetadataDocument(
                "https://idp.okta.com/exk1a2b3c4d5e", "https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml", "okta-cert-abc");

        RelyingPartyRegistration registration = fromMetadata(oktaMetadata, "okta");
        System.out.println(registration);
    }
}
```

**How to run:** save as `MetadataLevel1.java`, run `java MetadataLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
RelyingPartyRegistration[registrationId=okta, idpEntityId=https://idp.okta.com/exk1a2b3c4d5e, ssoLocation=https://idp.okta.com/app/exk1a2b3c4d5e/sso/saml, verificationCert=okta-cert-abc]
```

`fromMetadata` is exactly what `RelyingPartyRegistrations.fromMetadataLocation(...).registrationId(...).build()` does: take everything the metadata document supplies, add the one thing it can't supply (your own chosen `registrationId`), and produce a complete registration.

### Level 2 — Intermediate

Handle a metadata document listing multiple signing certificates — the IdP mid-rotation — carrying all of them forward so either currently-valid key is trusted.

```java
import java.util.*;

public class MetadataLevel2 {
    record MetadataDocument(String entityId, String ssoLocation, List<String> signingCertificates) {}
    record RelyingPartyRegistration(String registrationId, String idpEntityId, String ssoLocation, List<String> verificationCerts) {
        boolean trustsSignature(String signature) {
            return verificationCerts.stream().anyMatch(cert -> signature.startsWith(cert + "-signed-"));
        }
    }

    static RelyingPartyRegistration fromMetadata(MetadataDocument metadata, String registrationId) {
        return new RelyingPartyRegistration(registrationId, metadata.entityId(), metadata.ssoLocation(),
                List.copyOf(metadata.signingCertificates()));
    }

    public static void main(String[] args) {
        // the IdP's metadata NOW lists TWO certificates -- old key still present during rotation
        MetadataDocument oktaMetadata = new MetadataDocument("https://idp.okta.com/exk1", "https://idp.okta.com/sso",
                List.of("okta-key-1", "okta-key-2"));

        RelyingPartyRegistration registration = fromMetadata(oktaMetadata, "okta");

        System.out.println("trusts old key: " + registration.trustsSignature("okta-key-1-signed-alice"));
        System.out.println("trusts new key: " + registration.trustsSignature("okta-key-2-signed-alice"));
        System.out.println("trusts unknown key: " + registration.trustsSignature("okta-key-3-signed-alice"));
    }
}
```

**How to run:** save as `MetadataLevel2.java`, run `java MetadataLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
trusts old key: true
trusts new key: true
trusts unknown key: false
```

What changed: `signingCertificates` is now a list rather than a single value, and `trustsSignature` checks against all of them — this mirrors real metadata documents that list every currently-valid signing certificate, letting an SP built from freshly-fetched metadata trust assertions signed with either the old or new key during an IdP-side rotation window, without any manual reconfiguration.

### Level 3 — Advanced

A metadata fetch can fail (network error, IdP outage, malformed document) — building a registration from a failed fetch must fail loudly at startup rather than silently producing a broken, half-populated registration that fails every login later with a confusing error.

```java
import java.util.*;

public class MetadataLevel3 {
    record MetadataDocument(String entityId, String ssoLocation, List<String> signingCertificates) {}
    record RelyingPartyRegistration(String registrationId, String idpEntityId, String ssoLocation, List<String> verificationCerts) {}

    static class MetadataFetchException extends RuntimeException {
        MetadataFetchException(String message) { super(message); }
    }
    static class MetadataParseException extends RuntimeException {
        MetadataParseException(String message) { super(message); }
    }

    static class MetadataEndpoint {
        private final Map<String, MetadataDocument> documents = new HashMap<>();
        private final Set<String> unreachableUrls = new HashSet<>();
        private final Set<String> malformedUrls = new HashSet<>();

        void publish(String url, MetadataDocument doc) { documents.put(url, doc); }
        void simulateOutage(String url) { unreachableUrls.add(url); }
        void simulateMalformed(String url) { malformedUrls.add(url); }

        MetadataDocument fetch(String url) {
            if (unreachableUrls.contains(url)) throw new MetadataFetchException("connection timed out fetching " + url);
            if (malformedUrls.contains(url)) throw new MetadataParseException("metadata at " + url + " is not valid XML / missing required elements");
            MetadataDocument doc = documents.get(url);
            if (doc == null) throw new MetadataFetchException("no metadata document found at " + url);
            return doc;
        }
    }

    // mirrors RelyingPartyRegistrations.fromMetadataLocation(...).registrationId(...).build()
    static RelyingPartyRegistration fromMetadataLocation(String url, String registrationId, MetadataEndpoint endpoint) {
        MetadataDocument metadata = endpoint.fetch(url); // let ANY failure here propagate -- never build a partial registration
        if (metadata.signingCertificates().isEmpty()) {
            throw new MetadataParseException("metadata at " + url + " lists NO signing certificates -- cannot trust any assertion");
        }
        return new RelyingPartyRegistration(registrationId, metadata.entityId(), metadata.ssoLocation(),
                List.copyOf(metadata.signingCertificates()));
    }

    public static void main(String[] args) {
        MetadataEndpoint endpoint = new MetadataEndpoint();
        endpoint.publish("https://idp.okta.com/metadata",
                new MetadataDocument("https://idp.okta.com/exk1", "https://idp.okta.com/sso", List.of("okta-key-1")));
        endpoint.simulateOutage("https://idp.down.example/metadata");
        endpoint.simulateMalformed("https://idp.broken.example/metadata");

        try {
            RelyingPartyRegistration ok = fromMetadataLocation("https://idp.okta.com/metadata", "okta", endpoint);
            System.out.println("okta: OK -- " + ok);
        } catch (RuntimeException e) {
            System.out.println("okta: FAILED -- " + e.getMessage());
        }

        try {
            fromMetadataLocation("https://idp.down.example/metadata", "down-idp", endpoint);
        } catch (RuntimeException e) {
            System.out.println("down-idp: FAILED at startup -- " + e.getMessage());
        }

        try {
            fromMetadataLocation("https://idp.broken.example/metadata", "broken-idp", endpoint);
        } catch (RuntimeException e) {
            System.out.println("broken-idp: FAILED at startup -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `MetadataLevel3.java`, run `java MetadataLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
okta: OK -- RelyingPartyRegistration[registrationId=okta, idpEntityId=https://idp.okta.com/exk1, ssoLocation=https://idp.okta.com/sso, verificationCerts=[okta-key-1]]
down-idp: FAILED at startup -- connection timed out fetching https://idp.down.example/metadata
broken-idp: FAILED at startup -- metadata at https://idp.broken.example/metadata is not valid XML / missing required elements
```

What changed: `fromMetadataLocation` now lets *any* fetch or parse failure propagate immediately, rather than catching it and returning a partially-built registration — an application configured against an unreachable or malformed metadata URL fails at startup with a clear, actionable message, instead of booting successfully and only discovering the problem when the first real user's login attempt mysteriously fails.

## 6. Walkthrough

Trace the `down-idp` startup failure from Level 3, then contrast it with `okta`'s successful path.

**Step 1 — application startup, bean creation.** The `relyingPartyRegistrationRepository()` bean method runs, calling (conceptually) `RelyingPartyRegistrations.fromMetadataLocation("https://idp.down.example/metadata").registrationId("down-idp").build()` — corresponding to `fromMetadataLocation("https://idp.down.example/metadata", "down-idp", endpoint)`.

**Step 2 — the metadata fetch is attempted.** `endpoint.fetch("https://idp.down.example/metadata")` checks `unreachableUrls.contains(url)`, which is `true` (this URL was registered via `simulateOutage`), so it throws `MetadataFetchException("connection timed out fetching ...")` immediately.

**Step 3 — the exception propagates out of `fromMetadataLocation`**, since there is no `try`/`catch` around the fetch call — it continues propagating out of the bean method, which in a real Spring Boot application causes application context startup to fail entirely.

**Step 4 — the application never starts.** Rather than an application that boots successfully but has a broken `down-idp` registration silently sitting in its repository (which would only surface as a confusing failure the first time a user tried to log in via that registration), the failure is visible immediately, at deploy time, with a message pointing directly at the cause.

**Contrast — `okta`'s successful path.** `endpoint.fetch("https://idp.okta.com/metadata")` finds a registered `MetadataDocument`, returns it without incident; `metadata.signingCertificates()` is non-empty (`["okta-key-1"]`), so the additional "no signing certificates" check also passes, and a complete `RelyingPartyRegistration` is returned and (in a real application) registered in the repository, ready to serve real login attempts from card 0107's flow.

```
okta:      fetch succeeds -> certs present -> registration BUILT -> application starts normally
down-idp:  fetch throws (timeout)          -> exception propagates -> STARTUP FAILS, loudly, immediately
broken-idp: fetch throws (malformed XML)   -> exception propagates -> STARTUP FAILS, loudly, immediately
```

## 7. Gotchas & takeaways

> **Gotcha:** always fetch metadata over HTTPS from a URL you've verified belongs to the actual identity provider — metadata is the mechanism by which trust (which certificate to verify assertion signatures against) gets established in the first place, so a metadata document fetched from a spoofed or compromised URL would cause the SP to trust an attacker's signing key without any other check ever catching the substitution.

- Metadata-driven registration (`RelyingPartyRegistrations.fromMetadataLocation`) should be the default way to configure a production SAML integration — hand-built registrations invite transcription errors that metadata parsing eliminates entirely.
- A metadata document can list multiple valid signing certificates simultaneously, which is exactly how an IdP rotates its signing key without any coordinated SP-side redeploy — the same rotation story as JWK Sets (card 0101), applied to SAML.
- A failed or malformed metadata fetch should fail application startup loudly, not silently produce a partially-configured registration that only breaks later, confusingly, on the first real login attempt.
- The trust model rests on fetching metadata from a URL that genuinely belongs to the intended identity provider — an attacker-controlled or spoofed metadata source would let a malicious signing certificate get trusted from the very start.
- The same mechanism runs in reverse: your own application's `RelyingPartyRegistration` can be rendered as metadata XML for the IdP's administrators, giving them the same error-eliminating, machine-readable source of truth about your SP.
