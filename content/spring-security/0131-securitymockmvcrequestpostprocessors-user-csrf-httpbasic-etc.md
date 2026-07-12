---
card: spring-security
gi: 131
slug: securitymockmvcrequestpostprocessors-user-csrf-httpbasic-etc
title: "SecurityMockMvcRequestPostProcessors (user, csrf, httpBasic, etc.)"
---

## 1. What it is

While `@WithMockUser` (card 0127) populates `SecurityContextHolder` *before* a test method runs, `SecurityMockMvcRequestPostProcessors` takes a different, per-request approach: its static factory methods (`user(...)`, `csrf()`, `httpBasic(...)`, `jwt()`, `authentication(...)`) return `RequestPostProcessor` objects passed directly into a specific `MockMvc.perform(...)` call, modifying *that one simulated request* — adding an authenticated principal, a valid CSRF token, or an `Authorization` header — rather than the whole test method's ambient security state.

```java
@Test
void adminCanDeleteOrder() throws Exception {
    mockMvc.perform(delete("/api/orders/123")
            .with(user("admin").roles("ADMIN"))  // THIS request only
            .with(csrf()))                        // a valid CSRF token, THIS request only
           .andExpect(status().isNoContent());
}
```

## 2. Why & when

`@WithMockUser` is ideal when an entire test method should run as one consistent principal — but some tests genuinely need finer, per-request control: simulating multiple different requests with different principals within the *same* test method, testing CSRF protection itself (which requires a request that specifically *lacks* a valid token, something `@WithMockUser` alone says nothing about), or testing HTTP Basic or JWT bearer authentication mechanics directly rather than skipping past them. `RequestPostProcessor`s exist as a request-scoped alternative precisely for these cases, composing naturally with `.perform(...)`'s existing builder-style API rather than requiring a separate annotation per test method.

Reach for `SecurityMockMvcRequestPostProcessors` over `@WithMockUser` when:

- A single test method needs to issue multiple `mockMvc.perform(...)` calls as *different* principals — `user("alice")` on one call, `user("bob")` on another, within the same test.
- Testing CSRF protection specifically — `csrf()` supplies a valid token for a state-changing request that should succeed; *omitting* it deliberately tests that the same request is correctly rejected without one.
- Testing an endpoint secured by `httpBasic()` or a bearer-token mechanism directly, exercising the actual authentication filter (`httpBasic(...)`, `jwt()`) rather than bypassing it the way `@WithMockUser` does.
- Composing several post-processors on one request — `user(...)` combined with `csrf()` is an extremely common pairing for testing a state-changing endpoint (`POST`/`PUT`/`DELETE`) that both requires authentication and enforces CSRF protection.

## 3. Core concept

```
mockMvc.perform(REQUEST_BUILDER.with(POST_PROCESSOR_1).with(POST_PROCESSOR_2)...)

Each RequestPostProcessor MODIFIES the MockHttpServletRequest being built, BEFORE
it's dispatched through the actual SecurityFilterChain -- this is genuinely
DIFFERENT from @WithMockUser, which pre-populates SecurityContextHolder and never
touches the request itself at all.

Common post-processors:
    user("alice").roles("ADMIN")   -- adds a mock authenticated principal, THIS request only
    csrf()                          -- adds a valid CSRF token matching what the app expects
    httpBasic("alice", "password")  -- adds a real Authorization: Basic header, EXERCISES the actual filter
    jwt().jwt(builder -> ...)       -- simulates a Bearer JWT, for testing resource server endpoints
    authentication(someAuthObject)  -- installs a SPECIFIC, already-built Authentication object directly
    anonymous()                     -- explicitly marks the request as UNAUTHENTICATED (like @WithAnonymousUser, per-request)

KEY DIFFERENCE from @WithMockUser:
    @WithMockUser:        sets SecurityContextHolder ONCE, before the test method; EVERY
                           mockMvc call in that method sees the SAME principal
    RequestPostProcessor: applies to ONE specific .perform(...) call; different calls in
                           the SAME test method can use DIFFERENT post-processors entirely
```

`csrf()` and `user(...)` are frequently combined precisely because most real applications require both a valid principal *and* CSRF protection for the same state-changing endpoints.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a mockMvc perform call being built up with a request post processor for user and another for csrf both modifying the request object itself before it is dispatched through the real security filter chain unlike WithMockUser which pre populates the security context ahead of the whole test method">
  <rect x="20" y="30" width="220" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="130" y="52" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">delete("/api/orders/123")</text>
  <text x="130" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">MockHttpServletRequestBuilder</text>

  <line x1="240" y1="60" x2="280" y2="60" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#pp131)"/>

  <rect x="285" y="20" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="355" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">.with(user("admin")...)</text>

  <rect x="285" y="66" width="140" height="34" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="355" y="88" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">.with(csrf())</text>

  <line x1="425" y1="37" x2="470" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#pp131b)"/>
  <line x1="425" y1="83" x2="470" y2="60" stroke="#f0883e" stroke-width="1.5" marker-end="url(#pp131c)"/>

  <rect x="475" y="35" width="160" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="555" y="55" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">fully-built request</text>
  <text x="555" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; through REAL filter chain</text>

  <text x="330" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a DIFFERENT .perform(...) call in the same test method could use ENTIRELY different post-processors</text>

  <defs>
    <marker id="pp131" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="pp131b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="pp131c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

Post-processors modify one request being built, letting a single test method exercise several different security scenarios across multiple `.perform(...)` calls.

## 5. Runnable example

The scenario: model request post-processors as functions modifying a `MockRequest`-equivalent object, growing from a single `user()` post-processor into combined `user()` + `csrf()`, then into one test method issuing multiple requests with different post-processors, verifying each behaves independently.

### Level 1 — Basic

A single post-processor adding an authenticated principal to one request.

```java
import java.util.*;
import java.util.function.*;

public class RequestPostProcessorsLevel1 {
    static class MockRequest {
        String method; String path;
        String principalName; Set<String> authorities = Set.of();
        boolean hasCsrfToken = false;
    }

    // mirrors SecurityMockMvcRequestPostProcessors.user(...)
    static UnaryOperator<MockRequest> user(String username, String... roles) {
        return request -> {
            request.principalName = username;
            Set<String> auths = new LinkedHashSet<>();
            for (String role : roles) auths.add("ROLE_" + role);
            request.authorities = auths;
            return request;
        };
    }

    static MockRequest perform(String method, String path, UnaryOperator<MockRequest>... postProcessors) {
        MockRequest request = new MockRequest();
        request.method = method; request.path = path;
        for (var pp : postProcessors) pp.apply(request);
        return request;
    }

    public static void main(String[] args) {
        MockRequest request = perform("DELETE", "/api/orders/123", user("admin", "ADMIN"));

        System.out.println("principal: " + request.principalName + ", authorities: " + request.authorities);
    }
}
```

**How to run:** save as `RequestPostProcessorsLevel1.java`, run `java RequestPostProcessorsLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
principal: admin, authorities: [ROLE_ADMIN]
```

`user(...)` mirrors `SecurityMockMvcRequestPostProcessors.user(...)`: it modifies the request object being built, attaching an authenticated principal that only applies to *this* simulated request — nothing about `SecurityContextHolder` globally is touched.

### Level 2 — Intermediate

Combine `user()` with `csrf()`, and show a request without CSRF failing a simulated CSRF check.

```java
import java.util.*;
import java.util.function.*;

public class RequestPostProcessorsLevel2 {
    static class MockRequest {
        String method; String path;
        String principalName; Set<String> authorities = Set.of();
        boolean hasCsrfToken = false;
    }

    static class CsrfException extends RuntimeException { CsrfException(String m) { super(m); } }

    static UnaryOperator<MockRequest> user(String username, String... roles) {
        return request -> {
            request.principalName = username;
            Set<String> auths = new LinkedHashSet<>();
            for (String role : roles) auths.add("ROLE_" + role);
            request.authorities = auths;
            return request;
        };
    }

    static UnaryOperator<MockRequest> csrf() {
        return request -> { request.hasCsrfToken = true; return request; };
    }

    @SafeVarargs
    static MockRequest perform(String method, String path, UnaryOperator<MockRequest>... postProcessors) {
        MockRequest request = new MockRequest();
        request.method = method; request.path = path;
        for (var pp : postProcessors) pp.apply(request);
        return request;
    }

    // mirrors the security filter chain's CSRF check for state-changing methods
    static int handleRequest(MockRequest request) {
        boolean isStateChanging = Set.of("POST", "PUT", "DELETE", "PATCH").contains(request.method);
        if (isStateChanging && !request.hasCsrfToken) throw new CsrfException("Invalid CSRF Token");
        if (request.principalName == null) return 401;
        return 204;
    }

    public static void main(String[] args) {
        MockRequest withBoth = perform("DELETE", "/api/orders/123", user("admin", "ADMIN"), csrf());
        System.out.println("with user + csrf: " + handleRequest(withBoth));

        MockRequest withoutCsrf = perform("DELETE", "/api/orders/123", user("admin", "ADMIN"));
        try {
            handleRequest(withoutCsrf);
        } catch (CsrfException e) {
            System.out.println("without csrf: REJECTED -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `RequestPostProcessorsLevel2.java`, run `java RequestPostProcessorsLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
with user + csrf: 204
without csrf: REJECTED -- Invalid CSRF Token
```

What changed: `handleRequest` now simulates the actual CSRF check the security filter chain performs on state-changing methods — a request built with both `user()` and `csrf()` succeeds, while omitting `csrf()` (even with a valid authenticated principal) is correctly rejected, demonstrating that authentication and CSRF protection are genuinely independent checks, both needing their own explicit post-processor to satisfy in a test.

### Level 3 — Advanced

One test method issuing multiple requests as different principals, each with independently correct post-processors — demonstrating the per-request flexibility `@WithMockUser` alone cannot provide within a single test method.

```java
import java.util.*;
import java.util.function.*;

public class RequestPostProcessorsLevel3 {
    static class MockRequest {
        String method; String path;
        String principalName; Set<String> authorities = Set.of();
        boolean hasCsrfToken = false;
        boolean isAnonymous = false;
    }
    static class CsrfException extends RuntimeException { CsrfException(String m) { super(m); } }

    static UnaryOperator<MockRequest> user(String username, String... roles) {
        return request -> {
            request.principalName = username;
            Set<String> auths = new LinkedHashSet<>();
            for (String role : roles) auths.add("ROLE_" + role);
            request.authorities = auths;
            return request;
        };
    }
    static UnaryOperator<MockRequest> csrf() { return request -> { request.hasCsrfToken = true; return request; }; }
    static UnaryOperator<MockRequest> anonymous() { return request -> { request.isAnonymous = true; return request; }; }

    @SafeVarargs
    static MockRequest perform(String method, String path, UnaryOperator<MockRequest>... postProcessors) {
        MockRequest request = new MockRequest();
        request.method = method; request.path = path;
        for (var pp : postProcessors) pp.apply(request);
        return request;
    }

    static int handleRequest(MockRequest request, Set<String> requiredAuthorityForPath) {
        boolean isStateChanging = Set.of("POST", "PUT", "DELETE", "PATCH").contains(request.method);
        if (isStateChanging && !request.hasCsrfToken) throw new CsrfException("Invalid CSRF Token");
        if (request.isAnonymous || request.principalName == null) return 302; // redirect to login
        if (!requiredAuthorityForPath.isEmpty() && Collections.disjoint(request.authorities, requiredAuthorityForPath)) return 403;
        return isStateChanging ? 204 : 200;
    }

    public static void main(String[] args) {
        // ONE test method, THREE different requests, each with its own tailored post-processors
        System.out.println("--- request 1: admin deletes an order ---");
        MockRequest adminDelete = perform("DELETE", "/api/orders/123", user("admin", "ADMIN"), csrf());
        System.out.println("status: " + handleRequest(adminDelete, Set.of("ROLE_ADMIN")));

        System.out.println("--- request 2: regular user tries the SAME delete, in the SAME test method ---");
        MockRequest userDelete = perform("DELETE", "/api/orders/123", user("bob", "USER"), csrf());
        System.out.println("status: " + handleRequest(userDelete, Set.of("ROLE_ADMIN")));

        System.out.println("--- request 3: anonymous request to the SAME endpoint ---");
        MockRequest anonDelete = perform("DELETE", "/api/orders/123", anonymous(), csrf());
        System.out.println("status: " + handleRequest(anonDelete, Set.of("ROLE_ADMIN")));
    }
}
```

**How to run:** save as `RequestPostProcessorsLevel3.java`, run `java RequestPostProcessorsLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- request 1: admin deletes an order ---
status: 204
--- request 2: regular user tries the SAME delete, in the SAME test method ---
status: 403
--- request 3: anonymous request to the SAME endpoint ---
status: 302
```

What changed: three requests, each with an entirely different combination of post-processors, are all issued within what would be one single test method — this is precisely the flexibility `RequestPostProcessor`s provide over `@WithMockUser`: verifying an authorization boundary from three different angles (authorized, forbidden, unauthenticated) without needing three separate test methods each carrying its own class-level or method-level annotation.

## 6. Walkthrough

Trace request 2 (the forbidden case) from Level 3 end to end.

**Step 1 — the real test code:**
```java
@Test
void deleteEndpointRespectsAuthorization() throws Exception {
    mockMvc.perform(delete("/api/orders/123").with(user("admin").roles("ADMIN")).with(csrf()))
           .andExpect(status().isNoContent());

    mockMvc.perform(delete("/api/orders/123").with(user("bob").roles("USER")).with(csrf()))
           .andExpect(status().isForbidden());

    mockMvc.perform(delete("/api/orders/123").with(anonymous()).with(csrf()))
           .andExpect(status().is3xxRedirection());
}
```

**Step 2 — the second `.perform(...)` call is built.** `.with(user("bob").roles("USER"))` and `.with(csrf())` both modify the `MockHttpServletRequestBuilder` before it's dispatched — corresponding to `perform("DELETE", "/api/orders/123", user("bob", "USER"), csrf())` producing a `MockRequest` with `principalName="bob"`, `authorities={"ROLE_USER"}`, `hasCsrfToken=true`.

**Step 3 — the request is dispatched through the (simulated) filter chain.** `handleRequest(userDelete, Set.of("ROLE_ADMIN"))` first checks the CSRF condition — `hasCsrfToken` is `true`, so this passes without incident.

**Step 4 — the anonymous/authenticated check passes.** `request.isAnonymous` is `false` and `principalName` is `"bob"` (non-null), so this isn't treated as an unauthenticated request.

**Step 5 — the authorization check fails.** `requiredAuthorityForPath` is `{"ROLE_ADMIN"}`; `request.authorities` is `{"ROLE_USER"}`; `Collections.disjoint(...)` is `true` (no overlap), so the method returns `403`.

**Step 6 — the test assertion for this specific call passes**, since `status().isForbidden()` matches the actual `403` — bob, despite being a real, CSRF-protected, authenticated request, is correctly denied by the authorization rule specifically requiring `ROLE_ADMIN`.

```
request 1 (admin, csrf):     CSRF ok -> not anonymous -> ROLE_ADMIN present    -> 204
request 2 (bob/USER, csrf):  CSRF ok -> not anonymous -> ROLE_ADMIN ABSENT     -> 403
request 3 (anonymous, csrf): CSRF ok -> IS anonymous                          -> 302
```

## 7. Gotchas & takeaways

> **Gotcha:** testing a state-changing endpoint (`POST`/`PUT`/`DELETE`) with `user(...)` but *without* `csrf()` produces a `403` due to CSRF rejection, not because the authorization rule itself failed — a test asserting `status().isForbidden()` without understanding this distinction might pass for entirely the wrong reason, masking a genuine authorization bug that a correctly CSRF-token'd request would have revealed instead.

- `SecurityMockMvcRequestPostProcessors` modify one specific `.perform(...)` call's request, in contrast to `@WithMockUser`'s test-method-wide `SecurityContextHolder` population — this makes them the right tool when a single test method needs to exercise multiple, different security scenarios.
- `user(...)` and `csrf()` are commonly paired, since most real state-changing endpoints require both a valid authenticated principal and CSRF protection to succeed.
- `httpBasic(...)` and `jwt()` exercise the *actual* authentication filter for their respective mechanisms, rather than bypassing it the way `user(...)`/`@WithMockUser` do — useful specifically when the authentication mechanism's own mechanics are what's under test.
- `anonymous()` explicitly marks a request as unauthenticated, the per-request counterpart to `@WithAnonymousUser` — useful when a test needs both an authenticated and an anonymous request within the same method.
- Post-processors compose freely — multiple can be chained onto the same `.perform(...)` call via repeated `.with(...)` calls, each contributing its own modification to the request being built.
