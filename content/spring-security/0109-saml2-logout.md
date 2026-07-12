---
card: spring-security
gi: 109
slug: saml2-logout
title: "SAML2 logout"
---

## 1. What it is

SAML2 logout is the direct analogue of card 0097's OIDC RP-Initiated Logout, but built on SAML's **Single Logout (SLO)** profile: `Saml2LogoutRequestFilter` and `Saml2LogoutResponseFilter` implement the two-message exchange defined by the SAML spec — the service provider (or the identity provider) sends a signed `LogoutRequest` to the other party, which terminates its own session and replies with a signed `LogoutResponse`. Registered via `saml2Logout()`, this uses the same `RelyingPartyRegistration` (card 0108) as login, reading its `singleLogoutServiceLocation` and credentials to know where to send the request and how to sign it.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .saml2Login(Customizer.withDefaults())
        .saml2Logout(Customizer.withDefaults()); // adds SLO on top of an existing saml2Login() setup
    return http.build();
}
```

## 2. Why & when

Just as card 0097 established for OIDC, clearing your own application's session does nothing to end a user's session at the identity provider — and SAML's enterprise deployment context (shared workstations, corporate SSO expectations) makes this gap even more consequential than in a typical consumer OAuth2 app. SAML's Single Logout profile additionally supports **IdP-initiated logout**: the identity provider itself can push a `LogoutRequest` to every service provider a user is signed into, letting one action (an admin disabling an account, a user clicking "sign out everywhere" at the IdP) terminate sessions across every connected application — a capability plain session invalidation could never provide on its own.

Reach for `saml2Logout()` when:

- Enterprise policy requires "logout" to mean a full sign-out across every connected application, not just the one the user happened to click "logout" in.
- The identity provider needs to be able to push logout to your application — for instance, when an admin deactivates a user's account and every active session, in every SP, must end immediately.
- Building against an identity provider that mandates SLO support as part of its SAML integration requirements (common for enterprise and government identity providers).

## 3. Core concept

```
SP-INITIATED logout (user clicks "logout" in YOUR app):
  1. browser -> SP: POST /logout
  2. SP clears its OWN session, builds a signed LogoutRequest
  3. SP redirects browser -> IdP's singleLogoutServiceLocation, carrying the LogoutRequest
  4. IdP ends its own session, replies with a signed LogoutResponse
  5. IdP redirects browser back to the SP's logout response endpoint
  6. SP verifies the LogoutResponse's signature, considers logout complete

IDP-INITIATED logout (something at the IdP triggers logout, e.g. admin action):
  1. IdP sends a signed LogoutRequest to the SP (may hit MULTIPLE SPs if the user was signed into several)
  2. Saml2LogoutRequestFilter verifies ITS signature, then clears the SP's own session
  3. SP replies with a signed LogoutResponse back to the IdP

BOTH directions require signature verification on every inbound Logout message --
an unsigned or badly-signed LogoutRequest must NEVER be allowed to end a session,
or it becomes a trivial denial-of-service against any user whose session id an attacker can guess.
```

The two flows are mirror images of each other — which party initiates determines which message type (`LogoutRequest` vs. `LogoutResponse`) each side sends first.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting sp initiated logout where the browser tells the service provider to log out which then notifies the identity provider against idp initiated logout where the identity provider pushes a logout request directly to the service provider">
  <rect x="20" y="20" width="290" height="180" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="165" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SP-initiated</text>
  <text x="165" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">browser -&gt; SP: POST /logout</text>
  <text x="165" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">SP clears session, signs LogoutRequest</text>
  <text x="165" y="98" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">browser -&gt; IdP (carries LogoutRequest)</text>
  <text x="165" y="116" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">IdP ends session, signs LogoutResponse</text>
  <text x="165" y="134" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">browser -&gt; SP (carries LogoutResponse)</text>
  <text x="165" y="152" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">SP verifies signature -&gt; done</text>

  <rect x="330" y="20" width="290" height="180" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="475" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">IdP-initiated</text>
  <text x="475" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">admin deactivates user AT the IdP</text>
  <text x="475" y="80" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">IdP signs + sends LogoutRequest to SP</text>
  <text x="475" y="98" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">SP MUST verify signature first</text>
  <text x="475" y="116" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">SP clears its own session</text>
  <text x="475" y="134" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">SP replies with signed LogoutResponse</text>
  <text x="475" y="152" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">may repeat for EVERY SP the user was in</text>
</svg>

Either party can initiate, but both directions demand signature verification before a session is ever cleared.

## 5. Runnable example

The scenario: model SP-initiated logout, add IdP-initiated logout as a symmetric alternative path, then add the mandatory signature check that must gate any inbound `LogoutRequest` regardless of which direction initiated it.

### Level 1 — Basic

SP-initiated: clear the local session, build a signed logout request.

```java
import java.util.*;

public class Saml2LogoutLevel1 {
    static class Session {
        String principal;
        boolean active = true;
    }
    record LogoutRequest(String signature, String sessionIndex) {}

    static LogoutRequest spInitiatedLogout(Session session, String signingKeyId) {
        String sessionIndex = session.principal; // stands in for a real SAML session index
        session.principal = null;
        session.active = false;
        return new LogoutRequest(signingKeyId + "-signed-" + sessionIndex, sessionIndex);
    }

    public static void main(String[] args) {
        Session session = new Session();
        session.principal = "alice";

        LogoutRequest request = spInitiatedLogout(session, "sp-key-1");
        System.out.println("session active: " + session.active);
        System.out.println("sending signed LogoutRequest to IdP: " + request);
    }
}
```

**How to run:** save as `Saml2LogoutLevel1.java`, run `java Saml2LogoutLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
session active: false
sending signed LogoutRequest to IdP: LogoutRequest[signature=sp-key-1-signed-alice, sessionIndex=alice]
```

`spInitiatedLogout` clears the local session first, then builds a signed request identifying which session is ending — mirroring `Saml2LogoutRequestResolver`'s job of producing an outbound, SP-signed `LogoutRequest`.

### Level 2 — Intermediate

Add IdP-initiated logout as the symmetric alternative — the IdP sends the first message instead of the SP.

```java
import java.util.*;

public class Saml2LogoutLevel2 {
    static class Session {
        String principal;
        boolean active = true;
    }
    record LogoutRequest(String signature, String sessionIndex) {}
    record LogoutResponse(String signature, String status) {}

    // SP-initiated: the browser told US to log out
    static LogoutRequest spInitiatedLogout(Session session, String signingKeyId) {
        String sessionIndex = session.principal;
        session.principal = null;
        session.active = false;
        return new LogoutRequest(signingKeyId + "-signed-" + sessionIndex, sessionIndex);
    }

    // IdP-initiated: the IdP told US to log out (e.g. an admin deactivated this user elsewhere)
    static LogoutResponse idpInitiatedLogout(Session session, LogoutRequest incoming, String spSigningKeyId) {
        session.principal = null;
        session.active = false;
        return new LogoutResponse(spSigningKeyId + "-signed-response-to-" + incoming.sessionIndex(), "success");
    }

    public static void main(String[] args) {
        Session aliceSession = new Session();
        aliceSession.principal = "alice";
        LogoutRequest outgoing = spInitiatedLogout(aliceSession, "sp-key-1");
        System.out.println("SP-initiated: session active=" + aliceSession.active + ", sent " + outgoing);

        Session bobSession = new Session();
        bobSession.principal = "bob";
        LogoutRequest incomingFromIdp = new LogoutRequest("idp-key-1-signed-bob", "bob");
        LogoutResponse response = idpInitiatedLogout(bobSession, incomingFromIdp, "sp-key-1");
        System.out.println("IdP-initiated: session active=" + bobSession.active + ", replied " + response);
    }
}
```

**How to run:** save as `Saml2LogoutLevel2.java`, run `java Saml2LogoutLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
SP-initiated: session active=false, sent LogoutRequest[signature=sp-key-1-signed-alice, sessionIndex=alice]
IdP-initiated: session active=false, replied LogoutResponse[signature=sp-key-1-signed-response-to-bob, status=success]
```

What changed: `idpInitiatedLogout` handles the mirror-image flow — an inbound `LogoutRequest` triggers local session clearing and a reply, rather than the SP originating the first message — both paths converge on the same outcome (the local session ends), just triggered from opposite directions.

### Level 3 — Advanced

Add the mandatory signature check every inbound `LogoutRequest`/`LogoutResponse` must pass before any session is touched — without it, an attacker could forge a `LogoutRequest` for an arbitrary session index and force-logout any user.

```java
import java.util.*;

public class Saml2LogoutLevel3 {
    static class Session {
        String principal;
        boolean active = true;
    }
    record LogoutRequest(String signature, String sessionIndex) {}
    record LogoutResponse(String signature, String status) {}

    static class Saml2LogoutValidationException extends RuntimeException {
        Saml2LogoutValidationException(String message) { super(message); }
    }

    static class ServiceProvider {
        private final String trustedIdpSignaturePrefix;
        private final Map<String, Session> sessionsBySessionIndex = new HashMap<>();

        ServiceProvider(String trustedIdpSignaturePrefix) { this.trustedIdpSignaturePrefix = trustedIdpSignaturePrefix; }

        void registerActiveSession(String sessionIndex, Session session) { sessionsBySessionIndex.put(sessionIndex, session); }

        // handles an INBOUND LogoutRequest -- from the IdP, or forged by an attacker
        LogoutResponse handleIncomingLogoutRequest(LogoutRequest request, String spSigningKeyId) {
            if (!request.signature().startsWith(trustedIdpSignaturePrefix + "-signed-")) {
                throw new Saml2LogoutValidationException(
                        "LogoutRequest signature verification failed -- REFUSING to end any session");
            }
            Session session = sessionsBySessionIndex.get(request.sessionIndex());
            if (session != null) {
                session.principal = null;
                session.active = false;
            }
            return new LogoutResponse(spSigningKeyId + "-signed-response-to-" + request.sessionIndex(), "success");
        }
    }

    public static void main(String[] args) {
        ServiceProvider sp = new ServiceProvider("idp-key-1");

        Session aliceSession = new Session();
        aliceSession.principal = "alice";
        sp.registerActiveSession("alice", aliceSession);

        Session bobSession = new Session();
        bobSession.principal = "bob";
        sp.registerActiveSession("bob", bobSession);

        // GENUINE IdP-initiated logout for alice
        LogoutRequest genuine = new LogoutRequest("idp-key-1-signed-alice", "alice");
        LogoutResponse response = sp.handleIncomingLogoutRequest(genuine, "sp-key-1");
        System.out.println("alice session active after genuine request: " + aliceSession.active + ", replied: " + response);

        // FORGED LogoutRequest attempting to force-logout bob, NOT signed by the trusted IdP
        LogoutRequest forged = new LogoutRequest("attacker-controlled-signed-bob", "bob");
        try {
            sp.handleIncomingLogoutRequest(forged, "sp-key-1");
        } catch (Saml2LogoutValidationException e) {
            System.out.println("forged request rejected: " + e.getMessage());
        }
        System.out.println("bob session STILL active (forged request had no effect): " + bobSession.active);
    }
}
```

**How to run:** save as `Saml2LogoutLevel3.java`, run `java Saml2LogoutLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
alice session active after genuine request: false, replied: LogoutResponse[signature=sp-key-1-signed-response-to-alice, status=success]
forged request rejected: LogoutRequest signature verification failed -- REFUSING to end any session
bob session STILL active (forged request had no effect): true
```

What changed: `handleIncomingLogoutRequest` now checks the inbound signature against the trusted IdP's key *before* touching `sessionsBySessionIndex` at all — the forged request, despite correctly naming bob's `sessionIndex`, is rejected outright and bob's session remains fully active, demonstrating exactly why every inbound Logout message, regardless of direction, must be signature-checked before it's allowed to have any effect.

## 6. Walkthrough

Trace the forged-request rejection from Level 3, contrasting it against the genuine case.

**Step 1 — an attacker sends a forged logout request, having guessed or observed bob's `sessionIndex`:**
```
POST /logout/saml2/slo HTTP/1.1
Host: app.example.com
Content-Type: application/x-www-form-urlencoded

SAMLRequest=<base64 XML LogoutRequest, sessionIndex="bob", signed with an UNTRUSTED key>
```

**Step 2 — signature verification runs first.** `handleIncomingLogoutRequest` checks `request.signature().startsWith("idp-key-1-signed-")` — the forged signature is `"attacker-controlled-signed-bob"`, which does not match, so `Saml2LogoutValidationException` is thrown immediately.

**Step 3 — bob's session lookup never happens.** `sessionsBySessionIndex.get("bob")` is never reached; bob's `Session` object is never touched.

**Step 4 — the SP's response to the forged request:**
```
HTTP/1.1 400 Bad Request
```

**Contrast — alice's genuine request.** `handleIncomingLogoutRequest(genuine, "sp-key-1")` passes the signature check (`"idp-key-1-signed-alice"` matches the trusted prefix), proceeds to look up and clear `aliceSession`, and returns a properly signed `LogoutResponse`.

```
genuine request (alice): signature TRUSTED -> session cleared -> signed LogoutResponse returned
forged request (bob):    signature UNTRUSTED -> REJECTED before session lookup -> bob's session UNCHANGED
```

## 7. Gotchas & takeaways

> **Gotcha:** IdP-initiated logout support means your application must accept unsolicited `LogoutRequest` messages arriving at any time, from a party your application didn't just redirect a user to — this is precisely why signature verification on every *inbound* Logout message (not just responses to requests your own application sent) is non-negotiable; without it, single logout becomes a trivial way for anyone who can guess or observe a session identifier to force-terminate another user's session.

- SAML2 logout mirrors OIDC's RP-Initiated Logout but adds a genuinely bidirectional profile: either the SP or the IdP can initiate, and the SP must be prepared to handle unsolicited inbound `LogoutRequest` messages.
- IdP-initiated logout is what makes "sign out everywhere" or "admin deactivates this account" actually terminate sessions across every connected service provider, not just the one the user happens to be looking at.
- Every inbound Logout message, regardless of which party initiated the exchange, must have its signature verified before any session state changes — an unverified `LogoutRequest` is a denial-of-service vector against any guessable session identifier.
- `saml2Logout()` reuses the same `RelyingPartyRegistration` (card 0108) as login — the IdP's `singleLogoutServiceLocation` and trusted certificate are configured once and used for both directions.
- A `LogoutResponse` back to the initiating party confirms the logout completed on this side — a real deployment with multiple connected service providers relies on every one of them completing this handshake for a true "signed out everywhere" guarantee.
