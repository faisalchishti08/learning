---
card: spring-security
gi: 121
slug: cas-authentication
title: "CAS authentication"
---

## 1. What it is

CAS (Central Authentication Service) is an older, ticket-based single sign-on protocol — predating both SAML and OAuth2/OIDC — still found in higher-education institutions and some legacy enterprise deployments where it was adopted early and never migrated away from. Spring Security's `CasAuthenticationFilter` implements the client (service) side: rather than exchanging a code for a token (OAuth2) or a signed XML assertion (SAML), CAS's flow centers on a short-lived, single-use **service ticket** — a simple opaque string — that the client application validates by calling back to the CAS server directly, over a server-to-server HTTP request, before trusting it.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http, ServiceProperties serviceProperties,
                                        TicketValidator ticketValidator) throws Exception {
    CasAuthenticationFilter casFilter = new CasAuthenticationFilter();
    casFilter.setAuthenticationManager(authenticationManager(ticketValidator, serviceProperties));

    http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .addFilter(casFilter)
        .exceptionHandling(exceptions -> exceptions
                .authenticationEntryPoint(casAuthenticationEntryPoint(serviceProperties)));
    return http.build();
}
```

## 2. Why & when

CAS predates the widespread adoption of cryptographically signed tokens (JWTs) or XML assertions (SAML) as the trust mechanism for federated login, so it takes a simpler — and in some ways more conservative — approach: rather than trusting a token because of a signature the client verifies itself, the client always calls back to the CAS server to ask "is this ticket genuinely one you issued, and for whom?" This server-to-server validation call is CAS's core trust mechanism, conceptually similar to card 0102's opaque-token introspection, but predating OAuth2 entirely — an organization that adopted CAS early (many universities did, in the 1990s and 2000s) often still runs it as their central SSO system today, simply because migrating every integrated application away is a large, multi-year undertaking rarely worth undertaking purely for its own sake.

Reach for `CasAuthenticationFilter`/CAS integration when:

- Integrating with an existing CAS server that an organization (frequently a university, or a long-established enterprise) already operates as its central SSO system, and building or maintaining a new SAML/OIDC front end for that same CAS deployment isn't planned or practical.
- The organization's other applications already speak CAS, and a new application needs single sign-on with them specifically — joining the existing ecosystem is simpler than asking the identity team to stand up a parallel OIDC-compatible path.
- Legacy compatibility during a longer migration — an application might support both CAS (for existing integrated systems) and a newer protocol (OIDC, SAML) simultaneously while a broader modernization effort is still in progress.

## 3. Core concept

```
CAS ticket-based flow:
  1. browser requests a protected resource -> CasAuthenticationEntryPoint redirects to the CAS server
       -> GET https://cas.example.edu/login?service=https://app.example.com/login/cas
  2. user authenticates AT the CAS server (outside the client application entirely)
  3. CAS server redirects back to the "service" URL, carrying a TICKET (a short opaque string):
       -> GET https://app.example.com/login/cas?ticket=ST-123456-abcXYZ
  4. CasAuthenticationFilter catches this callback and VALIDATES the ticket by calling BACK to CAS,
       server-to-server, over a SEPARATE HTTP request:
       -> GET https://cas.example.edu/serviceValidate?service=...&ticket=ST-123456-abcXYZ
  5. CAS server responds with an XML (or JSON) document confirming:
       - the ticket IS valid, was issued for THIS service, and hasn't been used before
       - the authenticated user's identity (and optionally additional attributes)
  6. CasAuthenticationFilter builds an Authentication from the validated response -> SecurityContextHolder

KEY property: the ticket ITSELF proves nothing on its own -- it is opaque and single-use,
              and its validity is established ONLY by that separate, server-to-server
              validation call back to the CAS server, exactly mirroring the trust model
              of OAuth2 opaque token introspection (card 0102), just under an older protocol.
```

A ticket presented twice (a replay attempt) fails the validation call the second time, since CAS marks each ticket as consumed on its first successful validation.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence diagram of CAS login the browser is redirected to the CAS server to authenticate then redirected back to the client application carrying a ticket the client application validates that ticket by calling back to the CAS server directly over a server to server request before trusting the identity it confirms">
  <text x="90" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Client App</text>
  <text x="340" y="24" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="590" y="24" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">CAS Server</text>

  <line x1="90" y1="35" x2="90" y2="225" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="340" y1="35" x2="340" y2="225" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="590" y1="35" x2="590" y2="225" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <line x1="90" y1="55" x2="335" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cas121)"/>
  <text x="95" y="48" fill="#e6edf3" font-size="8.5" font-family="sans-serif">1. 302 -&gt; CAS login?service=...</text>

  <line x1="340" y1="85" x2="585" y2="85" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cas121)"/>
  <text x="345" y="78" fill="#e6edf3" font-size="8.5" font-family="sans-serif">2. GET CAS login (user authenticates)</text>

  <line x1="590" y1="115" x2="335" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cas121b)"/>
  <text x="585" y="108" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">3. 302 -&gt; service?ticket=ST-123..</text>

  <line x1="340" y1="145" x2="95" y2="145" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cas121c)"/>
  <text x="340" y="138" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">4. GET /login/cas?ticket=ST-123..</text>

  <line x1="90" y1="175" x2="585" y2="175" stroke="#6db33f" stroke-width="1.6" stroke-dasharray="6,3" marker-end="url(#cas121d)"/>
  <text x="95" y="168" fill="#6db33f" font-size="8.5" font-family="sans-serif">5. GET serviceValidate?ticket=.. -- server-to-server, NOT via browser</text>

  <line x1="590" y1="205" x2="95" y2="205" stroke="#8b949e" stroke-width="1.6" stroke-dasharray="6,3" marker-end="url(#cas121b)"/>
  <text x="585" y="198" fill="#e6edf3" font-size="8.5" text-anchor="end" font-family="sans-serif">6. XML: ticket valid, user=alice</text>

  <defs>
    <marker id="cas121" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="cas121b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="cas121c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="cas121d" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The ticket itself is meaningless without the server-to-server validation call that confirms it — the browser never carries anything that's independently verifiable.

## 5. Runnable example

The scenario: model CAS ticket issuance and server-to-server validation, growing from a bare valid/invalid check into single-use ticket consumption (a replay attempt failing), then into a full simulated redirect sequence contrasting CAS's callback-validation model with OAuth2's locally-verifiable JWTs.

### Level 1 — Basic

Issue a ticket, validate it via a callback.

```java
import java.util.*;

public class CasAuthLevel1 {
    static class CasServer {
        private final Map<String, String> issuedTickets = new HashMap<>(); // ticket -> username
        private int counter = 0;

        String issueTicket(String username) {
            String ticket = "ST-" + (++counter) + "-abcXYZ";
            issuedTickets.put(ticket, username);
            return ticket;
        }

        // the SERVER-TO-SERVER validation call -- the client NEVER trusts a ticket without this
        String validate(String ticket, String service) {
            String username = issuedTickets.get(ticket);
            if (username == null) throw new IllegalStateException("INVALID_TICKET");
            return username;
        }
    }

    public static void main(String[] args) {
        CasServer cas = new CasServer();

        String ticket = cas.issueTicket("alice");
        System.out.println("browser received ticket: " + ticket);

        String validatedUser = cas.validate(ticket, "https://app.example.com/login/cas");
        System.out.println("server-side validation confirms: " + validatedUser);
    }
}
```

**How to run:** save as `CasAuthLevel1.java`, run `java CasAuthLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
browser received ticket: ST-1-abcXYZ
server-side validation confirms: alice
```

`issueTicket` stands in for CAS's redirect-with-ticket response; `validate` stands in for the client application's separate, server-to-server call to `/serviceValidate` — the ticket alone (just a string the browser carries) proves nothing until this second call confirms it.

### Level 2 — Intermediate

Add single-use consumption: a ticket validated once cannot be validated again — a replay attempt must fail.

```java
import java.util.*;

public class CasAuthLevel2 {
    static class TicketValidationException extends RuntimeException {
        TicketValidationException(String message) { super(message); }
    }

    static class CasServer {
        private final Map<String, String> issuedTickets = new HashMap<>();
        private int counter = 0;

        String issueTicket(String username) {
            String ticket = "ST-" + (++counter) + "-abcXYZ";
            issuedTickets.put(ticket, username);
            return ticket;
        }

        String validate(String ticket, String service) {
            // remove() makes this SINGLE-USE -- a second validation attempt finds nothing
            String username = issuedTickets.remove(ticket);
            if (username == null) throw new TicketValidationException("INVALID_TICKET: unknown or already used");
            return username;
        }
    }

    public static void main(String[] args) {
        CasServer cas = new CasServer();
        String ticket = cas.issueTicket("alice");

        String firstValidation = cas.validate(ticket, "https://app.example.com/login/cas");
        System.out.println("first validation: " + firstValidation);

        try {
            cas.validate(ticket, "https://app.example.com/login/cas"); // REPLAY attempt
        } catch (TicketValidationException e) {
            System.out.println("replay attempt: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `CasAuthLevel2.java`, run `java CasAuthLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
first validation: alice
replay attempt: INVALID_TICKET: unknown or already used
```

What changed: `validate` now consumes the ticket (`issuedTickets.remove`) rather than merely reading it — a second validation attempt with the same ticket, whether from an accidental retry or an attacker who intercepted it in transit, finds nothing left to validate, mirroring the single-use property real CAS service tickets carry, conceptually identical to card 0090's single-use OAuth2 authorization codes.

### Level 3 — Advanced

A full simulated flow: redirect to CAS, ticket issuance, callback, server-to-server validation — contrasted explicitly with what a JWT-based approach would look like, to highlight CAS's defining trust mechanism (always call back, never verify locally).

```java
import java.util.*;

public class CasAuthLevel3 {
    static class TicketValidationException extends RuntimeException {
        TicketValidationException(String message) { super(message); }
    }

    static class CasServer {
        private final Map<String, String> issuedTickets = new HashMap<>();
        private int counter = 0;
        private int validationCallCount = 0;

        String issueTicket(String username) {
            String ticket = "ST-" + (++counter) + "-abcXYZ";
            issuedTickets.put(ticket, username);
            return ticket;
        }

        String validate(String ticket, String service) {
            validationCallCount++; // tracks how many times the client had to call BACK to CAS
            String username = issuedTickets.remove(ticket);
            if (username == null) throw new TicketValidationException("INVALID_TICKET");
            return username;
        }

        int getValidationCallCount() { return validationCallCount; }
    }

    static class ClientApplication {
        private final CasServer cas;
        private final String serviceUrl;

        ClientApplication(CasServer cas, String serviceUrl) { this.cas = cas; this.serviceUrl = serviceUrl; }

        // step 1: redirect the browser to CAS
        String buildLoginRedirect() {
            return "https://cas.example.edu/login?service=" + serviceUrl;
        }

        // step 4: the callback arrives carrying a ticket -- this app does NOT trust it yet
        String handleCallback(String ticket) {
            System.out.println("  received ticket via browser redirect: " + ticket + " (NOT YET trusted)");
            // step 5: MUST call back to CAS, server-to-server, before trusting anything
            String username = cas.validate(ticket, serviceUrl);
            System.out.println("  server-to-server validation confirms: " + username + " (NOW trusted)");
            return username;
        }
    }

    public static void main(String[] args) {
        CasServer cas = new CasServer();
        ClientApplication app = new ClientApplication(cas, "https://app.example.com/login/cas");

        System.out.println("step 1: " + app.buildLoginRedirect());
        System.out.println("step 2-3: user authenticates at CAS, gets redirected back with a ticket");

        String ticket = cas.issueTicket("alice"); // CAS issues the ticket, corresponding to steps 2-3
        System.out.println("step 4-5:");
        String authenticatedUser = app.handleCallback(ticket);

        System.out.println("authenticated as: " + authenticatedUser);
        System.out.println("total server-to-server validation calls made: " + cas.getValidationCallCount());

        System.out.println();
        System.out.println("CONTRAST: a JWT-based approach would need ZERO server-to-server calls here --");
        System.out.println("the client would verify the JWT's signature LOCALLY (card 0101), no callback required.");
        System.out.println("CAS's ticket model trades that round trip for a simpler, pre-cryptographic trust mechanism.");
    }
}
```

**How to run:** save as `CasAuthLevel3.java`, run `java CasAuthLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
step 1: https://cas.example.edu/login?service=https://app.example.com/login/cas
step 2-3: user authenticates at CAS, gets redirected back with a ticket
step 4-5:
  received ticket via browser redirect: ST-1-abcXYZ (NOT YET trusted)
  server-to-server validation confirms: alice (NOW trusted)
authenticated as: alice
total server-to-server validation calls made: 1
```
(plus the closing contrast lines printed as-is)

What changed: `ClientApplication.handleCallback` explicitly marks the ticket as untrusted the instant it arrives via the browser, and only becomes trusted after the separate `cas.validate(...)` call succeeds — `getValidationCallCount()` confirms exactly one server-to-server round trip was needed for this one login, which is the structural cost CAS's ticket model always pays, in contrast to a JWT-based approach that could skip this callback entirely by verifying a signature locally instead.

## 6. Walkthrough

Trace alice's full login from Level 3, tying each step back to the diagram's sequence.

**Step 1 — the browser requests a protected resource, gets redirected to CAS:**
```
GET /dashboard HTTP/1.1
Host: app.example.com
```
```
HTTP/1.1 302 Found
Location: https://cas.example.edu/login?service=https://app.example.com/login/cas
```
This corresponds to `app.buildLoginRedirect()`.

**Step 2 — the browser follows the redirect and authenticates at CAS** — entirely outside the client application's code, exactly like every other federated login flow this course has covered.

**Step 3 — CAS redirects back with a ticket:**
```
HTTP/1.1 302 Found
Location: https://app.example.com/login/cas?ticket=ST-1-abcXYZ
```
This corresponds to `cas.issueTicket("alice")` having produced `"ST-1-abcXYZ"`.

**Step 4 — the callback arrives at the client application:**
```
GET /login/cas?ticket=ST-1-abcXYZ HTTP/1.1
Host: app.example.com
```
`CasAuthenticationFilter` catches this — corresponding to `app.handleCallback("ST-1-abcXYZ")` being invoked. The ticket is logged as received but explicitly *not yet trusted*.

**Step 5 — the mandatory server-to-server validation call, never seen by the browser:**
```
GET /serviceValidate?service=https://app.example.com/login/cas&ticket=ST-1-abcXYZ HTTP/1.1
Host: cas.example.edu
```
This corresponds to `cas.validate("ST-1-abcXYZ", serviceUrl)` — inside, `issuedTickets.remove(...)` both retrieves and consumes the ticket in one step, returning `"alice"`.

**Step 6 — CAS's validation response, in a real deployment, would look like:**
```
HTTP/1.1 200 OK
Content-Type: text/xml

<cas:serviceResponse>
  <cas:authenticationSuccess>
    <cas:user>alice</cas:user>
  </cas:authenticationSuccess>
</cas:serviceResponse>
```

**Step 7 — only now is alice trusted.** `handleCallback` returns `"alice"`, and `CasAuthenticationFilter` builds an `Authentication`, populating `SecurityContextHolder` — precisely mirroring how every earlier federated login mechanism in this course (OAuth2, SAML) eventually arrives at the same kind of object, regardless of the very different protocol details that got there.

```
browser: gets ticket from CAS (untrusted string)
        |
        v (client app receives it via browser redirect)
client app: MUST call back to CAS server-to-server -- this is the ONLY way to establish trust
        |
        v
CAS: consumes the ticket, confirms identity -- SINGLE round trip, SINGLE use
        |
        v
client app: NOW trusts "alice" -- SecurityContext populated
```

## 7. Gotchas & takeaways

> **Gotcha:** never treat a CAS ticket as trustworthy simply because it arrived via an HTTPS redirect from what looks like the right URL — the entire point of CAS's design is that the ticket proves nothing on its own; skipping (or caching results of) the server-to-server validation call to save a round trip reintroduces exactly the vulnerability that call exists to close, since an attacker who can trick a browser into visiting a crafted callback URL with a guessed or intercepted ticket string would otherwise be trusted without ever having actually authenticated.

- CAS is an older, ticket-based SSO protocol still found in legacy deployments (especially higher education) where migrating away from it is a larger undertaking than continuing to support it.
- A CAS service ticket is an opaque, meaningless string on its own — trust is established entirely by a mandatory, server-to-server validation call back to the CAS server, conceptually similar to OAuth2's opaque token introspection (card 0102) but predating it as a protocol.
- Tickets are single-use — CAS consumes a ticket on its first successful validation, so a replayed or intercepted ticket fails on any subsequent validation attempt.
- The resulting `Authentication`/`SecurityContext` populated after a successful CAS validation behaves identically to one produced by any other authentication mechanism in this course — CAS's distinctiveness is entirely in *how* trust gets established, not in what the rest of the application does with the result afterward.
- Supporting CAS alongside a newer protocol (OIDC, SAML) simultaneously is a common, legitimate pattern during a longer-term migration away from it, rather than an all-or-nothing switch.
