---
card: spring-security
gi: 120
slug: rsocket-security
title: "RSocket security"
---

## 1. What it is

RSocket is a binary, reactive-streams-native protocol supporting four distinct interaction models over one persistent connection — request-response, fire-and-forget, request-stream, and channel (bidirectional streaming) — and Spring Security's RSocket support secures it with a design that mirrors card 0119's WebSocket story but adapted to RSocket's own request/route model. `PayloadSocketAcceptorInterceptor`, configured via an `RSocketSecurity` bean, authorizes each inbound RSocket request by its **route** (RSocket's equivalent of a destination/path), while authentication for the connection itself is typically established once via a `setup` payload — most commonly carrying a bearer token — rather than re-authenticating per individual request.

```java
@Bean
public PayloadSocketAcceptorInterceptor rsocketInterceptor(RSocketSecurity security) {
    security
        .authorizePayload(authorize -> authorize
            .route("public.**").permitAll()
            .route("admin.**").hasRole("ADMIN")
            .anyRequest().authenticated())
        .simpleAuthentication(Customizer.withDefaults());
    return security.build();
}
```

## 2. Why & when

RSocket's interaction models (particularly request-stream and channel) share the same fundamental challenge card 0119 identified for WebSockets — a single connection carries many logical requests or an ongoing stream of data over time, so a single connection-level authorization check is insufficient. RSocket security exists to authorize each route independently, similarly to how WebSocket security authorizes each STOMP destination independently, but shaped around RSocket's own primitives: routes instead of STOMP destinations, and a `setup` frame (carrying authentication metadata once, at connection establishment) instead of a separate HTTP-upgrade handshake.

Reach for RSocket security when:

- Building a Spring application using RSocket as its primary inter-service or client-service communication protocol — common in reactive, high-throughput microservice architectures wanting bidirectional streaming without the connection-per-request overhead of HTTP.
- Different RSocket routes need different authorization levels — a metrics-streaming route open to any authenticated client, an admin-command route restricted to a specific role, exactly mirroring the WebSocket destination-pattern story.
- The interaction model is request-stream or channel (an ongoing flow of data, potentially over a long period) rather than simple request-response — per-route authorization at request time doesn't automatically re-check authorization continuously throughout a long-lived stream, which is a design consideration worth understanding explicitly.

## 3. Core concept

```
RSocket connection lifecycle:
  1. SETUP frame -- establishes the connection, typically carries authentication metadata
       (e.g. a bearer token via SimpleAuthenticationEncoder / a custom MimeType)
  2. connection established -- the PRINCIPAL from setup is associated with this connection
  3. any number of subsequent REQUESTS over the same connection, each targeting a ROUTE:
       REQUEST_RESPONSE  -- one request, one response
       REQUEST_FIRE_AND_FORGET -- one request, no response expected
       REQUEST_STREAM    -- one request, a STREAM of responses over time
       REQUEST_CHANNEL   -- bidirectional STREAMS in both directions

PayloadSocketAcceptorInterceptor, per REQUEST:
  1. read the request's ROUTE (e.g. "admin.broadcast")
  2. find the FIRST matching authorizePayload rule, in order
  3. evaluate against the principal established at SETUP time
  4. passes -> request proceeds to its handler
     fails  -> request REJECTED (typically as an error signal on the response, mirroring
               card 0118's reactive method security error-signal behavior)

For REQUEST_STREAM / REQUEST_CHANNEL: authorization is checked ONCE, when the stream is
INITIATED -- it does not automatically re-check on every individual element flowing
through an already-established, already-authorized stream.
```

The initiation-time-only check for streaming interactions is a deliberate design trade-off, not an oversight — but it's worth knowing explicitly, since it differs from WebSocket security's genuinely per-message checking.

## 4. Diagram

<svg viewBox="0 0 660 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing an rsocket connection established via a setup frame carrying authentication then multiple requests over that connection each targeting a different route being authorized independently against the principal from setup">
  <rect x="20" y="20" width="200" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="42" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">SETUP frame</text>
  <text x="120" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">bearer token -&gt; principal established</text>

  <line x1="120" y1="66" x2="120" y2="95" stroke="#6db33f" stroke-width="1.6" marker-end="url(#rs120)"/>

  <rect x="20" y="98" width="600" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="118" fill="#8b949e" font-size="9.5" text-anchor="middle" font-family="sans-serif">ONE persistent RSocket connection, principal fixed for its lifetime</text>

  <rect x="40" y="140" width="150" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="115" y="160" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">REQUEST_RESPONSE</text>
  <text x="115" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">route: public.ping</text>

  <rect x="255" y="140" width="150" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="330" y="160" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">REQUEST_STREAM</text>
  <text x="330" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">route: admin.metrics</text>

  <rect x="470" y="140" width="150" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="545" y="160" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">FIRE_AND_FORGET</text>
  <text x="545" y="175" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">route: public.log-event</text>

  <defs><marker id="rs120" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Authentication is established once, at setup; each subsequent request is authorized independently by its own route.

## 5. Runnable example

The scenario: model route-based RSocket request authorization, growing from a single request check into an ordered rule set covering multiple interaction types, then into the stream-initiation-only checking behavior that distinguishes request-stream authorization from per-element checking.

### Level 1 — Basic

Authorize a single request by route.

```java
import java.util.*;

public class RSocketSecurityLevel1 {
    record RSocketRequest(String route, String interactionType, Set<String> principalAuthorities) {}

    static boolean isAuthorized(RSocketRequest request, String requiredAuthority) {
        return request.principalAuthorities().contains(requiredAuthority);
    }

    public static void main(String[] args) {
        RSocketRequest adminRequest = new RSocketRequest("admin.broadcast", "REQUEST_RESPONSE", Set.of("ROLE_USER"));

        System.out.println("authorized: " + isAuthorized(adminRequest, "ROLE_ADMIN"));
    }
}
```

**How to run:** save as `RSocketSecurityLevel1.java`, run `java RSocketSecurityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
authorized: false
```

The minimal shape of `PayloadSocketAcceptorInterceptor`'s core job: given a request and a required authority, does the connection's established principal have it?

### Level 2 — Intermediate

An ordered rule set covering multiple routes and interaction types, mirroring `authorizePayload`'s builder DSL.

```java
import java.util.*;
import java.util.function.*;

public class RSocketSecurityLevel2 {
    record RSocketRequest(String route, String interactionType, Set<String> principalAuthorities) {}
    record Rule(Predicate<RSocketRequest> matcher, String requirement) {}

    static class AuthorizePayloadSpec {
        private final List<Rule> rules = new ArrayList<>();

        AuthorizePayloadSpec route(String pattern, String requirement) {
            rules.add(new Rule(r -> matches(r.route(), pattern), requirement));
            return this;
        }
        AuthorizePayloadSpec anyRequest(String requirement) {
            rules.add(new Rule(r -> true, requirement));
            return this;
        }

        boolean authorize(RSocketRequest request) {
            for (Rule rule : rules) {
                if (rule.matcher().test(request)) {
                    return switch (rule.requirement()) {
                        case "permitAll" -> true;
                        case "authenticated" -> !request.principalAuthorities().isEmpty();
                        default -> request.principalAuthorities().contains(rule.requirement());
                    };
                }
            }
            return false;
        }

        private static boolean matches(String route, String pattern) {
            return route.matches(pattern.replace("**", ".*").replace(".", "\\."));
        }
    }

    public static void main(String[] args) {
        AuthorizePayloadSpec spec = new AuthorizePayloadSpec()
                .route("public.**", "permitAll")
                .route("admin.**", "ROLE_ADMIN")
                .anyRequest("authenticated");

        RSocketRequest publicPing = new RSocketRequest("public.ping", "REQUEST_RESPONSE", Set.of());
        RSocketRequest adminBroadcast = new RSocketRequest("admin.broadcast", "REQUEST_RESPONSE", Set.of("ROLE_USER"));
        RSocketRequest chatMessage = new RSocketRequest("chat.send", "FIRE_AND_FORGET", Set.of("ROLE_USER"));

        System.out.println("anonymous ping to public route: " + spec.authorize(publicPing));
        System.out.println("regular user to admin route: " + spec.authorize(adminBroadcast));
        System.out.println("authenticated user to unlisted route: " + spec.authorize(chatMessage));
    }
}
```

**How to run:** save as `RSocketSecurityLevel2.java`, run `java RSocketSecurityLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
anonymous ping to public route: true
regular user to admin route: false
authenticated user to unlisted route: true
```

What changed: routes are matched in declared order against a pattern-to-requirement rule set — a public route needs nothing, an admin route needs a specific role a regular user lacks, and an unlisted route falls through to the catch-all requiring only authentication, exactly mirroring `authorizePayload`'s real configuration shape.

### Level 3 — Advanced

Model the request-stream initiation-only check: authorization runs once, when the stream begins, and is not re-evaluated for every subsequent element the stream emits — contrasted with what *would* happen if authorization state changed mid-stream (it has no effect on an already-authorized, in-progress stream).

```java
import java.util.*;
import java.util.function.*;

public class RSocketSecurityLevel3 {
    record RSocketRequest(String route, String interactionType, Set<String> principalAuthorities) {}
    record Rule(Predicate<RSocketRequest> matcher, String requirement) {}

    static class RequestDeniedException extends RuntimeException { RequestDeniedException(String m) { super(m); } }

    static class AuthorizePayloadSpec {
        private final List<Rule> rules = new ArrayList<>();
        AuthorizePayloadSpec route(String pattern, String requirement) {
            rules.add(new Rule(r -> matches(r.route(), pattern), requirement)); return this;
        }
        AuthorizePayloadSpec anyRequest(String requirement) { rules.add(new Rule(r -> true, requirement)); return this; }

        boolean authorize(RSocketRequest request) {
            for (Rule rule : rules) {
                if (rule.matcher().test(request)) {
                    return switch (rule.requirement()) {
                        case "permitAll" -> true;
                        case "authenticated" -> !request.principalAuthorities().isEmpty();
                        default -> request.principalAuthorities().contains(rule.requirement());
                    };
                }
            }
            return false;
        }
        private static boolean matches(String route, String pattern) { return route.matches(pattern.replace("**", ".*").replace(".", "\\.")); }
    }

    // simulates a REQUEST_STREAM: authorization checked ONCE, at initiation, then elements flow freely
    static class MetricsStream {
        private final boolean authorizedAtInitiation;
        private final List<String> elements = new ArrayList<>();

        MetricsStream(RSocketRequest initiationRequest, AuthorizePayloadSpec spec) {
            this.authorizedAtInitiation = spec.authorize(initiationRequest); // the ONLY authorization check for this whole stream
            if (!authorizedAtInitiation) throw new RequestDeniedException("stream initiation denied for route " + initiationRequest.route());
        }

        // elements after initiation are NOT re-checked against authorization -- they simply flow
        void emit(String element) {
            elements.add(element);
            System.out.println("  stream element emitted (no re-authorization check): " + element);
        }

        List<String> getElements() { return elements; }
    }

    public static void main(String[] args) {
        AuthorizePayloadSpec spec = new AuthorizePayloadSpec()
                .route("admin.**", "ROLE_ADMIN")
                .anyRequest("authenticated");

        RSocketRequest adminInitiation = new RSocketRequest("admin.metrics", "REQUEST_STREAM", Set.of("ROLE_ADMIN"));

        System.out.println("--- admin's metrics stream, authorized once at initiation ---");
        MetricsStream stream = new MetricsStream(adminInitiation, spec);
        stream.emit("cpu=45%");
        stream.emit("memory=60%");
        stream.emit("cpu=47%");
        System.out.println("total elements streamed, all under ONE initiation-time check: " + stream.getElements().size());

        System.out.println("--- a non-admin ATTEMPTING to initiate the same stream ---");
        RSocketRequest regularUserInitiation = new RSocketRequest("admin.metrics", "REQUEST_STREAM", Set.of("ROLE_USER"));
        try {
            new MetricsStream(regularUserInitiation, spec);
        } catch (RequestDeniedException e) {
            System.out.println("  DENIED before the stream ever starts: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `RSocketSecurityLevel3.java`, run `java RSocketSecurityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- admin's metrics stream, authorized once at initiation ---
  stream element emitted (no re-authorization check): cpu=45%
  stream element emitted (no re-authorization check): memory=60%
  stream element emitted (no re-authorization check): cpu=47%
total elements streamed, all under ONE initiation-time check: 3
--- a non-admin ATTEMPTING to initiate the same stream ---
  DENIED before the stream ever starts: stream initiation denied for route "admin.metrics"
```

What changed: `MetricsStream`'s constructor performs the *only* authorization check for the entire stream's lifetime — `emit` never re-checks anything, mirroring how a real RSocket request-stream's authorization is evaluated once, when the stream is initiated, not per-element as data continues flowing; a non-admin's attempt is rejected before the stream begins at all, but once admin's stream is running, no further authorization overhead is incurred per element.

## 6. Walkthrough

Trace the denied non-admin initiation attempt from Level 3, then contrast with admin's successful, ongoing stream.

**Step 1 — a regular user's client attempts to initiate a metrics stream:**
```
REQUEST_STREAM
route: admin.metrics
```
This corresponds to constructing `new MetricsStream(regularUserInitiation, spec)`.

**Step 2 — the authorization check runs, inside the constructor.** `spec.authorize(regularUserInitiation)` checks rules in order: `route("admin.**", "ROLE_ADMIN")` matches this route, and its requirement checks `principalAuthorities.contains("ROLE_ADMIN")` — the regular user's authorities are `{"ROLE_USER"}`, so this is `false`.

**Step 3 — the stream never initiates.** `authorizedAtInitiation` is `false`, so the constructor throws `RequestDeniedException` immediately — no `MetricsStream` object is ever successfully constructed, and no elements are ever emitted for this attempt.

**Step 4 — contrast: admin's successful initiation.** `new MetricsStream(adminInitiation, spec)` — the same route, same rule, but admin's authorities are `{"ROLE_ADMIN"}`, so `authorize` returns `true`, `authorizedAtInitiation` is `true`, and construction succeeds.

**Step 5 — subsequent elements flow with no further check.** Each `stream.emit(...)` call simply appends to `elements` and prints — there is no call back into `spec.authorize(...)` anywhere in `emit`'s body. This is the critical distinction: authorization for a request-stream interaction is a *gate at initiation*, not a *continuous filter* applied to every element.

```
regular user: REQUEST_STREAM admin.metrics -> authorize() at initiation -> FALSE -> stream NEVER starts
admin:        REQUEST_STREAM admin.metrics -> authorize() at initiation -> TRUE  -> stream starts
                  -> element 1 (NO check)
                  -> element 2 (NO check)
                  -> element 3 (NO check)
```

## 7. Gotchas & takeaways

> **Gotcha:** because request-stream and request-channel authorization is checked only at initiation, a long-lived stream established while a principal legitimately had the required authority continues delivering data even if that authority is later revoked mid-stream — there is no automatic re-check as the stream continues. If a use case genuinely requires revocation to take effect on an already-open stream, that logic must be built explicitly (for instance, by having the stream's own data source periodically re-verify authorization or by closing streams proactively when a relevant permission changes), rather than assumed to be handled by `authorizePayload` alone.

- RSocket security authorizes each request independently by its route, using the principal established once at connection setup — mirroring WebSocket security's per-message model but adapted to RSocket's own route/interaction-type primitives.
- `authorizePayload`'s rule matching (ordered, first-match-wins, route patterns mapped to authority requirements) follows the same shape as `authorizeHttpRequests`/`authorizeExchange`/WebSocket's `simpDestMatchers` — the underlying authorization-rule concept is consistent across every transport this course has covered.
- Request-response and fire-and-forget interactions are authorized per individual request, matching the simplest mental model; request-stream and request-channel interactions are authorized once, at initiation, not per streamed element.
- This initiation-only check for streaming interactions is a deliberate design trade-off worth knowing explicitly — an application needing revocation to take effect mid-stream must implement that behavior itself, since the framework does not re-check automatically.
- Authentication (establishing who the connection belongs to) happens once, via the `setup` frame; authorization (deciding what a given request on that connection may do) happens per request thereafter — the same authentication/authorization separation this entire course has emphasized, just expressed in RSocket's own vocabulary.
