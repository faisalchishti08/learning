---
card: spring-security
gi: 134
slug: webtestclient-security-mutatewith
title: "WebTestClient security (mutateWith)"
---

## 1. What it is

`WebTestClient` is Spring WebFlux's testing counterpart to `MockMvc`, and `SecurityMockServerConfigurers` provides its equivalent of card 0131's request post-processors — but wired through `mutateWith(...)` rather than `.with(...)`, matching `WebTestClient`'s own reactive, builder-style API. `mutateWith(mockUser())`, `mutateWith(mockJwt())`, and similar configurers customize the security context a given `WebTestClient` request (or every request from a client instance configured once via `.mutateWith(...)` before any requests are made) will be processed under.

```java
@Test
void adminCanDeleteOrder() {
    webTestClient
        .mutateWith(mockUser("admin").roles("ADMIN"))
        .mutateWith(csrf())
        .delete().uri("/api/orders/123")
        .exchange()
        .expectStatus().isNoContent();
}
```

## 2. Why & when

Every earlier testing card in this section — `@WithMockUser`, `RequestPostProcessor`s, `ResultMatcher`s — was built around `MockMvc`, the Servlet-stack's test client; card 0115's reactive stack needs the exact same testing capabilities, but `WebTestClient` is a genuinely different client with its own API shape (a fluent, `exchange()`-terminated builder rather than `MockMvc.perform(...)`), so Spring Security provides a parallel set of configurers specifically designed to compose with it. `mutateWith(...)` exists because `WebTestClient`'s own extension mechanism is exactly this "mutate" pattern — configurers that adjust the client (or an individual request) before it actually executes.

Reach for `WebTestClient` security configurers when:

- Testing a WebFlux application (`@WebFluxTest`, or a full reactive `@SpringBootTest`) — this is the direct reactive-stack equivalent of using `MockMvc` post-processors in a Servlet-stack test.
- Testing a reactive resource server's JWT or opaque-token authentication (card 0100/0102's reactive equivalents) — `mockJwt()`/`mockOpaqueToken()` simulate these directly, mirroring card 0135's `MockMvc`-side equivalents but for `WebTestClient`.
- Applying a security configuration to *every* request a given `WebTestClient` instance issues — calling `.mutateWith(...)` on the client itself (rather than per-request) establishes a reusable, pre-configured client for a whole test class or test method's several requests.

## 3. Core concept

```
MockMvc (Servlet stack)                       WebTestClient (Reactive stack)
------------------------------------------    ------------------------------------------
mockMvc.perform(get(...).with(user(...)))     webTestClient.mutateWith(mockUser(...)).get().uri(...)
.with(csrf())                                 .mutateWith(csrf())
.with(jwt())                                  .mutateWith(mockJwt())
.with(authentication(auth))                   .mutateWith(mockAuthentication(auth))

mutateWith(configurer) can be applied:
    PER-REQUEST:   webTestClient.mutateWith(mockUser()).get().uri("/one").exchange();
                   webTestClient.get().uri("/two").exchange();  <-- this one is UNAFFECTED
    OR PRE-CONFIGURED on the client itself:
                   WebTestClient securedClient = webTestClient.mutateWith(mockUser());
                   securedClient.get().uri("/one").exchange();  <-- both requests from
                   securedClient.get().uri("/two").exchange();  <-- THIS client share it

Underlying mechanism: mirrors how Reactor Context (card 0116) carries the mock
SecurityContext through the reactive request-processing chain, exactly as a real
authenticated request's context would propagate.
```

The choice between per-request and pre-configured-client application is purely a convenience decision about how many requests in a given test need the same security setup.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing WebTestClient mutateWith mockUser applied either per request affecting only that one exchange or applied once to the client itself producing a reusable pre configured client whose every subsequent request shares the same mock security context">
  <rect x="20" y="20" width="290" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="165" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">PER-REQUEST application</text>
  <text x="165" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">.mutateWith(mockUser()).get().uri("/one")</text>
  <text x="165" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">only THIS exchange is affected</text>

  <rect x="330" y="20" width="290" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">CLIENT-level application</text>
  <text x="475" y="62" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">client = webTestClient.mutateWith(mockUser())</text>
  <text x="475" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">EVERY request from "client" shares it</text>

  <text x="320" y="130" fill="#8b949e" font-size="1"> </text>
</svg>

Two application points, same underlying configurer — per-request scoping or a reusable, pre-configured client instance.

## 5. Runnable example

The scenario: model `mutateWith`-style client mutation as an immutable builder pattern, growing from a single per-request configurer into distinguishing per-request from client-level scoping, then into composing multiple configurers on the same reactive-style request.

### Level 1 — Basic

A single configurer applied to one request.

```java
import java.util.*;

public class WebTestClientLevel1 {
    record MockRequest(String method, String path, String principalName, Set<String> authorities) {}

    // mirrors SecurityMockServerConfigurers.mockUser(...)
    static MockRequest mutateWithMockUser(MockRequest request, String username, String... roles) {
        Set<String> auths = new LinkedHashSet<>();
        for (String role : roles) auths.add("ROLE_" + role);
        return new MockRequest(request.method(), request.path(), username, auths);
    }

    public static void main(String[] args) {
        MockRequest base = new MockRequest("DELETE", "/api/orders/123", null, Set.of());
        MockRequest mutated = mutateWithMockUser(base, "admin", "ADMIN");

        System.out.println("principal: " + mutated.principalName() + ", authorities: " + mutated.authorities());
    }
}
```

**How to run:** save as `WebTestClientLevel1.java`, run `java WebTestClientLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
principal: admin, authorities: [ROLE_ADMIN]
```

`mutateWithMockUser` mirrors `mutateWith(mockUser("admin").roles("ADMIN"))`: it produces a *new*, mutated request configuration carrying the mock principal, exactly matching `WebTestClient`'s immutable, builder-style API design.

### Level 2 — Intermediate

Distinguish per-request scoping from client-level scoping — a client-level mutation affects every subsequent request built from it, a per-request one affects only that single request.

```java
import java.util.*;

public class WebTestClientLevel2 {
    record MockRequest(String method, String path, String principalName, Set<String> authorities) {}

    static class MockTestClient {
        private final String defaultPrincipal;
        private final Set<String> defaultAuthorities;

        MockTestClient() { this(null, Set.of()); }
        private MockTestClient(String principal, Set<String> authorities) {
            this.defaultPrincipal = principal; this.defaultAuthorities = authorities;
        }

        // mirrors webTestClient.mutateWith(mockUser(...)) applied to the CLIENT itself
        MockTestClient mutateWith(String username, String... roles) {
            Set<String> auths = new LinkedHashSet<>();
            for (String role : roles) auths.add("ROLE_" + role);
            return new MockTestClient(username, auths); // a NEW client instance, carrying this default
        }

        MockRequest buildRequest(String method, String path) {
            return new MockRequest(method, path, defaultPrincipal, defaultAuthorities);
        }
    }

    public static void main(String[] args) {
        MockTestClient plainClient = new MockTestClient();
        MockTestClient adminClient = plainClient.mutateWith("admin", "ADMIN"); // a SEPARATE, pre-configured client

        MockRequest fromPlainClient = plainClient.buildRequest("GET", "/api/public");
        MockRequest firstFromAdminClient = adminClient.buildRequest("GET", "/api/orders");
        MockRequest secondFromAdminClient = adminClient.buildRequest("DELETE", "/api/orders/123");

        System.out.println("plain client's request principal: " + fromPlainClient.principalName());
        System.out.println("admin client's FIRST request principal: " + firstFromAdminClient.principalName());
        System.out.println("admin client's SECOND request principal: " + secondFromAdminClient.principalName());
    }
}
```

**How to run:** save as `WebTestClientLevel2.java`, run `java WebTestClientLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
plain client's request principal: null
admin client's FIRST request principal: admin
admin client's SECOND request principal: admin
```

What changed: `adminClient`, once created via `mutateWith(...)`, carries its mock principal into *every* subsequent request built from it — both `firstFromAdminClient` and `secondFromAdminClient` share the same `"admin"` principal — while `plainClient`, never mutated, continues producing unauthenticated requests, exactly mirroring how `WebTestClient.mutateWith(...)` applied once to a client instance establishes a reusable, pre-configured client for however many requests a test needs to issue under that same identity.

### Level 3 — Advanced

Compose multiple configurers on the same request (`mockUser` plus a CSRF-equivalent), and model the underlying Reactor-Context-based propagation (card 0116) that makes the mock security context available correctly even through a simulated reactive chain hop.

```java
import java.util.*;
import java.util.function.*;

public class WebTestClientLevel3 {
    record MockRequest(String method, String path, String principalName, Set<String> authorities, boolean hasCsrfToken) {}

    interface Configurer extends UnaryOperator<MockRequest> {}

    static Configurer mockUser(String username, String... roles) {
        return request -> {
            Set<String> auths = new LinkedHashSet<>();
            for (String role : roles) auths.add("ROLE_" + role);
            return new MockRequest(request.method(), request.path(), username, auths, request.hasCsrfToken());
        };
    }

    static Configurer csrf() {
        return request -> new MockRequest(request.method(), request.path(),
                request.principalName(), request.authorities(), true);
    }

    static MockRequest applyAll(MockRequest base, Configurer... configurers) {
        MockRequest result = base;
        for (Configurer c : configurers) result = c.apply(result);
        return result;
    }

    // mirrors a reactive handler reading the mock context via ReactiveSecurityContextHolder (card 0116),
    // potentially after a simulated "thread hop" -- the context must STILL resolve correctly
    static String handleOnDifferentThread(MockRequest request) {
        // the context was carried EXPLICITLY in the request object, not via any thread-local mechanism,
        // so it resolves correctly regardless of which "thread" (conceptually) this runs on
        if (!request.hasCsrfToken()) throw new IllegalStateException("Invalid CSRF Token");
        if (!request.authorities().contains("ROLE_ADMIN")) throw new SecurityException("Access Denied");
        return "order deleted by " + request.principalName();
    }

    public static void main(String[] args) {
        MockRequest base = new MockRequest("DELETE", "/api/orders/123", null, Set.of(), false);

        MockRequest fullyConfigured = applyAll(base, mockUser("admin", "ADMIN"), csrf());

        String result = handleOnDifferentThread(fullyConfigured);
        System.out.println(result);

        // a request missing the csrf configurer -- still correctly rejected
        MockRequest missingCsrf = applyAll(base, mockUser("admin", "ADMIN"));
        try {
            handleOnDifferentThread(missingCsrf);
        } catch (IllegalStateException e) {
            System.out.println("missing csrf: REJECTED -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `WebTestClientLevel3.java`, run `java WebTestClientLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
order deleted by admin
missing csrf: REJECTED -- Invalid CSRF Token
```

What changed: `applyAll` composes both configurers onto the same request, and `handleOnDifferentThread` — standing in for a reactive handler that might genuinely execute on a different underlying thread than the one that built the request (exactly card 0116's concern) — still resolves the mock principal and CSRF status correctly, since both were carried explicitly as part of the request/context object rather than depending on any thread-local mechanism that a reactive thread hop could break.

## 6. Walkthrough

Trace the fully-configured admin delete request from Level 3, mapping it to a real `WebTestClient` test.

**Step 1 — the real test code:**
```java
@Test
void adminCanDeleteOrder() {
    webTestClient
        .mutateWith(mockUser("admin").roles("ADMIN"))
        .mutateWith(csrf())
        .delete().uri("/api/orders/123")
        .exchange()
        .expectStatus().isNoContent();
}
```

**Step 2 — both configurers are applied, building up the request's mock security context.** This corresponds to `applyAll(base, mockUser("admin", "ADMIN"), csrf())`, producing a `MockRequest` with `principalName="admin"`, `authorities={"ROLE_ADMIN"}`, `hasCsrfToken=true`.

**Step 3 — `.exchange()` dispatches the request through the reactive security filter chain** — corresponding to `handleOnDifferentThread(fullyConfigured)`, standing in for the fact that a real WebFlux request's processing may genuinely execute across multiple threads via Reactor's scheduling.

**Step 4 — the CSRF check passes**, since `hasCsrfToken` is `true` — corresponding to the `if (!request.hasCsrfToken())` check in `handleOnDifferentThread` not triggering.

**Step 5 — the authorization check passes.** `request.authorities().contains("ROLE_ADMIN")` is `true`, so the delete operation proceeds, returning `"order deleted by admin"`.

**Step 6 — the test assertion passes.** `.expectStatus().isNoContent()` matches the real `204` a successful deletion would produce.

```
mutateWith(mockUser("admin").roles("ADMIN")) -> principal=admin, authorities={ROLE_ADMIN}
mutateWith(csrf())                            -> hasCsrfToken=true
        |
        v (composed onto ONE request)
.delete().uri("/api/orders/123").exchange()
        |
        v (dispatched through the reactive security filter chain -- context resolves correctly regardless of thread)
CSRF check: PASS -> authorization check: PASS -> 204 No Content
```

## 7. Gotchas & takeaways

> **Gotcha:** applying `mutateWith(mockUser(...))` to the `WebTestClient` instance itself (rather than per-request) means *every* request issued from that specific client instance shares the same mock principal — if a test needs different principals for different requests within the same test method, use per-request `.mutateWith(...)` calls (or separate, independently-mutated client instances) rather than mutating one shared client and expecting different requests from it to somehow diverge.

- `WebTestClient` security configurers (`mutateWith(mockUser(...))`, `mutateWith(csrf())`, `mutateWith(mockJwt())`) are the reactive-stack equivalent of `MockMvc`'s `RequestPostProcessor`s (card 0131), adapted to `WebTestClient`'s own fluent, `mutateWith`-based API.
- A configurer can be applied per-request (affecting only that one `.exchange()` call) or to the client instance itself (producing a reusable, pre-configured client every subsequent request from it shares) — the choice is purely about convenience for a given test's structure.
- Multiple configurers compose freely on the same request, exactly like `MockMvc`'s post-processors — a mock user and CSRF token are commonly combined for testing state-changing reactive endpoints.
- The underlying mock security context propagates correctly through Reactor Context (card 0116), meaning it resolves correctly even if the actual request processing genuinely executes across multiple threads, which is routine in a real reactive server.
- Mixing up client-level and per-request mutation scope is a common source of confusion — always be explicit about which scope a given `mutateWith(...)` call is meant to apply to, especially in a test issuing several requests with different intended identities.
