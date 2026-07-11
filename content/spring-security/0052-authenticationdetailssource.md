---
card: spring-security
gi: 52
slug: authenticationdetailssource
title: "AuthenticationDetailsSource"
---

## 1. What it is

`AuthenticationDetailsSource` is the single-method interface (`buildDetails(context)`) that captures request-context information — the source IP address, the session ID, or anything else worth recording — into an `Authentication` object's `details` property at the moment authentication is attempted, separate from the actual `principal`/`credentials` being verified. `WebAuthenticationDetailsSource` (building `WebAuthenticationDetails`, holding the remote address and session ID) is the default for web-based authentication filters, and it's straightforward to supply a custom implementation capturing additional context.

```java
public class CustomAuthenticationDetails extends WebAuthenticationDetails {
    private final String userAgent;
    public CustomAuthenticationDetails(HttpServletRequest request) {
        super(request);
        this.userAgent = request.getHeader("User-Agent");
    }
    public String getUserAgent() { return userAgent; }
}

@Component
public class CustomAuthenticationDetailsSource
        implements AuthenticationDetailsSource<HttpServletRequest, CustomAuthenticationDetails> {
    public CustomAuthenticationDetails buildDetails(HttpServletRequest request) {
        return new CustomAuthenticationDetails(request);
    }
}
```

## 2. Why & when

An `Authentication` object's `principal` and `credentials` answer "who is this and what did they present as proof," but a complete picture of an authentication attempt — for security auditing, anomaly detection, or a policy that behaves differently based on request context — often needs more: where did this request originate, what session was it tied to, what client made it. `AuthenticationDetailsSource` exists specifically to capture *this* contextual information at the moment authentication happens, keeping it cleanly separate from the identity-verification concern (`principal`/`credentials`) that `AuthenticationProvider` is responsible for — the details object flows alongside the `Authentication` but is never itself checked or verified by the provider.

Reach for a custom `AuthenticationDetailsSource` when:

- Building a security audit trail or event listener (from the previous card) that needs contextual information beyond just the username — the source IP, User-Agent, or a custom header identifying an internal calling service.
- Implementing risk-based authentication logic (like the earlier custom-`AuthenticationProvider` example checking whether a login came from a known IP) — a custom `AuthenticationDetailsSource` is exactly where that source IP capture belongs, kept separate from the credential-verification logic itself.
- The default `WebAuthenticationDetails` (remote address and session ID only) doesn't capture everything a specific application's authentication events or providers need — extending it (as shown above) is the standard pattern, rather than replacing it entirely.

## 3. Core concept

```
 AbstractAuthenticationProcessingFilter.attemptAuthentication(request, response):
   1. Authentication unverified = ... build from request (username, password, etc.) ...
   2. unverified.setDetails(authenticationDetailsSource.buildDetails(request))
        -- CAPTURES request context HERE, at the moment of the attempt
        -- this happens BEFORE authenticationManager.authenticate() is even called
   3. return authenticationManager.authenticate(unverified)

 the AuthenticationProvider NEVER inspects "details" for its OWN verification decision --
   principal/credentials verification and "details" capture are DELIBERATELY separate concerns

 "details" DOES flow through to the FINAL, verified Authentication --
   available afterward to event listeners, audit logs, or authorization logic that wants it
```

Details capture happens once, up front, alongside credential extraction — never as part of the verification decision itself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="At the moment an authentication attempt is built AuthenticationDetailsSource captures request context like source IP and session ID into a details object attached to the Authentication this details object flows through unchanged by the AuthenticationProvider's verification logic and remains available afterward to listeners and audit logs">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">HttpServletRequest</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(source IP, session)</text>

  <rect x="215" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="305" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationDetailsSource</text>
  <text x="305" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.buildDetails(request)</text>

  <rect x="450" y="20" width="170" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="535" y="42" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthenticationProvider</text>
  <text x="535" y="55" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">verifies principal/credentials only</text>

  <rect x="450" y="105" width="170" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="127" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">verified Authentication</text>
  <text x="535" y="140" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.getDetails() still available</text>

  <defs><marker id="a52" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="88" x2="215" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a52)"/>
  <line x1="395" y1="80" x2="450" y2="45" stroke="#8b949e" stroke-width="1" marker-end="url(#a52)"/>
  <line x1="395" y1="95" x2="450" y2="122" stroke="#8b949e" stroke-width="1" marker-end="url(#a52)"/>
</svg>

Details flow around, not through, the verification decision — captured up front, still attached afterward.

## 5. Runnable example

The scenario: implement a details capture mechanism, build a custom details subtype adding extra context, then use the captured details in an event listener (tying together with the previous card) without the authentication decision itself ever depending on it.

### Level 1 — Basic

A minimal `AuthenticationDetailsSource` capturing the default fields (remote address, session ID) into a details object.

```java
import java.util.*;

public class AuthDetailsLevel1 {
    record Request(String remoteAddress, String sessionId) {}
    record WebAuthenticationDetails(String remoteAddress, String sessionId) {}

    interface AuthenticationDetailsSource { WebAuthenticationDetails buildDetails(Request request); }

    static AuthenticationDetailsSource defaultSource = request ->
            new WebAuthenticationDetails(request.remoteAddress(), request.sessionId());

    record Authentication(String username, String password, WebAuthenticationDetails details) {}

    public static void main(String[] args) {
        Request incoming = new Request("203.0.113.42", "JSESSIONID-abc123");

        WebAuthenticationDetails details = defaultSource.buildDetails(incoming);
        Authentication unverified = new Authentication("alice", "hunter2", details);

        System.out.println("unverified authentication's details: " + unverified.details());
    }
}
```

How to run: `java AuthDetailsLevel1.java`

`buildDetails` reads only `remoteAddress` and `sessionId` off the incoming request, entirely independent of the `username`/`password` fields also present on `unverified` — the details object is attached alongside, not derived from, the credentials being authenticated.

### Level 2 — Intermediate

Extend the default details with additional application-specific context (a User-Agent header), following the standard extension pattern.

```java
import java.util.*;

public class AuthDetailsLevel2 {
    record Request(String remoteAddress, String sessionId, Map<String, String> headers) {}

    // EXTENDS the default shape with one additional field, following the real WebAuthenticationDetails pattern
    record CustomAuthenticationDetails(String remoteAddress, String sessionId, String userAgent) {}

    interface AuthenticationDetailsSource { CustomAuthenticationDetails buildDetails(Request request); }

    static AuthenticationDetailsSource customSource = request ->
            new CustomAuthenticationDetails(request.remoteAddress(), request.sessionId(), request.headers().get("User-Agent"));

    record Authentication(String username, String password, CustomAuthenticationDetails details) {}

    public static void main(String[] args) {
        Request incoming = new Request("203.0.113.42", "JSESSIONID-abc123", Map.of("User-Agent", "Mozilla/5.0 (curl-like-client)"));

        CustomAuthenticationDetails details = customSource.buildDetails(incoming);
        Authentication unverified = new Authentication("alice", "hunter2", details);

        System.out.println("captured details: " + unverified.details());
    }
}
```

How to run: `java AuthDetailsLevel2.java`

`CustomAuthenticationDetails` carries everything `WebAuthenticationDetails` would, plus a `userAgent` field populated from the request's `User-Agent` header — the shape of what's captured is fully under the application's control, since `AuthenticationDetailsSource` is a plain interface with no fixed schema beyond what a given implementation chooses to build.

### Level 3 — Advanced

Tie the captured details into an event listener (from the previous card) for a suspicious-User-Agent detection use case, and confirm the authentication decision itself never depends on the details object at all.

```java
import java.util.*;
import java.util.function.Consumer;

public class AuthDetailsLevel3 {
    record Request(String remoteAddress, Map<String, String> headers) {}
    record CustomAuthenticationDetails(String remoteAddress, String userAgent) {}
    record Authentication(String username, String password, CustomAuthenticationDetails details) {}

    interface AuthenticationDetailsSource { CustomAuthenticationDetails buildDetails(Request request); }
    static AuthenticationDetailsSource source = request ->
            new CustomAuthenticationDetails(request.remoteAddress(), request.headers().getOrDefault("User-Agent", "unknown"));

    static Map<String, String> validCredentials = Map.of("alice", "hunter2");

    // the AUTHENTICATION DECISION itself -- uses ONLY username/password, NEVER touches "details"
    static boolean verifyCredentials(Authentication auth) {
        String stored = validCredentials.get(auth.username());
        return stored != null && stored.equals(auth.password());
    }

    interface AuthEvent {}
    record SuccessEvent(Authentication auth) implements AuthEvent {}
    record FailureEvent(Authentication auth) implements AuthEvent {}

    static List<Consumer<AuthEvent>> listeners = new ArrayList<>();

    static void authenticate(Request request, String username, String password) {
        CustomAuthenticationDetails details = source.buildDetails(request);
        Authentication attempt = new Authentication(username, password, details);

        boolean success = verifyCredentials(attempt); // decision made WITHOUT consulting "details" at all
        AuthEvent event = success ? new SuccessEvent(attempt) : new FailureEvent(attempt);
        listeners.forEach(l -> l.accept(event));
    }

    public static void main(String[] args) {
        // a listener using DETAILS (captured earlier, but never part of the verification decision) for its OWN purpose
        listeners.add(event -> {
            CustomAuthenticationDetails details = (event instanceof SuccessEvent s) ? s.auth().details()
                    : ((FailureEvent) event).auth().details();
            if (details.userAgent().contains("curl") || details.userAgent().equals("unknown")) {
                System.out.println("[SECURITY] non-browser or missing User-Agent from " + details.remoteAddress()
                        + ": '" + details.userAgent() + "' -- flagged for review");
            } else {
                System.out.println("[AUDIT] normal browser login attempt from " + details.remoteAddress());
            }
        });

        authenticate(new Request("198.51.100.1", Map.of("User-Agent", "Mozilla/5.0 (Windows NT 10.0)")), "alice", "hunter2");
        authenticate(new Request("203.0.113.99", Map.of("User-Agent", "curl/8.4.0")), "alice", "hunter2");
    }
}
```

How to run: `java AuthDetailsLevel3.java`

Both login attempts succeed identically (`verifyCredentials` only ever checks `username`/`password`, confirmed by both using alice's correct credentials), yet the listener reacts very differently based purely on the *captured details* — the first, from a normal browser User-Agent, is logged as routine; the second, from a `curl`-identified client, is flagged for review — demonstrating details flowing entirely alongside, never influencing, the actual authentication decision.

## 6. Walkthrough

Trace `authenticate(new Request("203.0.113.99", Map.of("User-Agent", "curl/8.4.0")), "alice", "hunter2")` from Level 3.

1. `source.buildDetails(request)` is called first, constructing `new CustomAuthenticationDetails("203.0.113.99", "curl/8.4.0")` — this reads directly off the incoming request, entirely before any credential verification happens.
2. `attempt = new Authentication("alice", "hunter2", details)` bundles the username, password, and the just-captured details together into one object.
3. `verifyCredentials(attempt)` runs next: it calls `validCredentials.get("alice")`, finds `"hunter2"`, and compares it against `auth.password()` (also `"hunter2"`) — this returns `true`. Critically, this method's body never references `auth.details()` at all; the User-Agent, however suspicious, plays no role whatsoever in whether this login succeeds.
4. Since `success` is `true`, `event = new SuccessEvent(attempt)` is constructed, and `listeners.forEach(l -> l.accept(event))` invokes the single registered listener with this event.
5. Inside the listener, `details.userAgent().contains("curl")` checks `"curl/8.4.0".contains("curl")`, which is `true`, so the security-flag branch fires, printing the review message — even though this was a completely successful, correctly-credentialed login, the listener's own separate logic flags it for review based purely on the details it inspects, entirely downstream of (and uninvolved in) the authentication decision itself.

```
authenticate(curl request, alice, hunter2):
  buildDetails -> CustomAuthenticationDetails(203.0.113.99, "curl/8.4.0")
  verifyCredentials -> checks ONLY username/password -> TRUE (never looks at details)
  -> SuccessEvent published
  -> listener inspects details SEPARATELY -> User-Agent contains "curl" -> flagged for review
     (the login itself already succeeded; this flag is purely informational, happening AFTER the fact)
```

## 7. Gotchas & takeaways

> **Gotcha:** because `AuthenticationDetailsSource` captures context at the moment of the *attempt*, not the moment of the *result*, a captured `remoteAddress` or session ID reflects where the request actually came from — this is exactly the reliable signal risk-based authentication logic (like the earlier custom-provider example) or audit trails depend on; conflating it with anything computed *after* verification (like the resulting authorities) would be a meaningful design mistake, since details are captured too early in the flow for that.

- `AuthenticationDetailsSource` captures request-context information (source IP, session ID, and any custom fields) into an `Authentication`'s `details` property, entirely separate from the `principal`/`credentials` an `AuthenticationProvider` actually verifies.
- The default `WebAuthenticationDetails` covers remote address and session ID; extending it with a custom subtype (adding a User-Agent, a custom header) is the standard pattern for capturing additional application-specific context.
- Details flow alongside the authentication decision, never influencing it — an `AuthenticationProvider`'s verification logic should never need to consult `details` to decide success or failure; that decision belongs entirely to `principal`/`credentials`.
- Event listeners (from the previous card) are a natural consumer of captured details, since they run after the decision is made and can use contextual information for logging, auditing, or anomaly detection without any risk of accidentally affecting the authentication outcome itself.
