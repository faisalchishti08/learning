---
card: spring-security
gi: 136
slug: testing-method-security
title: "Testing method security"
---

## 1. What it is

Testing `@PreAuthorize`/`@PostAuthorize`-annotated methods (card 0062) directly — calling a service method in a test and verifying it's correctly allowed or denied based on the caller's authorities — requires the method security interceptor to actually be active during the test, which in turn requires both `@EnableMethodSecurity` to be picked up (typically via loading enough Spring context for it to apply) and a populated `SecurityContext` for the interceptor to check against. This is where every earlier card in this Testing section converges: `@WithMockUser`, `@WithUserDetails`, or a custom `@WithSecurityContext`-based annotation (cards 0127–0130) can all be applied directly to a test method exercising a plain service call — no `MockMvc`, no HTTP layer, no web-specific test utilities required at all.

```java
@SpringBootTest
class OrderServiceSecurityTest {

    @Autowired OrderService orderService;

    @Test
    @WithMockUser(roles = "ADMIN")
    void adminCanDeleteOrder() {
        assertDoesNotThrow(() -> orderService.deleteOrder("123"));
    }

    @Test
    @WithMockUser  // default roles = {"USER"}
    void regularUserCannotDeleteOrder() {
        assertThrows(AccessDeniedException.class, () -> orderService.deleteOrder("123"));
    }
}
```

## 2. Why & when

Every earlier testing card in this section happened to demonstrate its concepts primarily through `MockMvc`-based web-layer tests, but method security itself is a genuinely separate concern from the web layer — a `@PreAuthorize`-annotated service method is checked by the *same* interceptor whether it's invoked from a REST controller, a scheduled job, a message listener, or directly from a test, and testing it doesn't require simulating an HTTP request at all. Recognizing this decoupling matters because it means method-security-focused tests can (and generally should) be narrower, faster unit/slice tests targeting the service layer directly, reserving full `MockMvc`-based tests for verifying the web layer's own behavior (routing, serialization, status codes) — a cleaner separation of what each test is actually responsible for verifying.

Reach for direct method-security testing (without `MockMvc`) when:

- Verifying a specific `@PreAuthorize`/`@PostAuthorize` expression's logic — testing the security rule itself, independent of whatever web endpoint happens to expose that service method.
- The service method being tested has no corresponding web endpoint at all (an internal service called only by other services, or by a scheduled job) — there's no `MockMvc` request to simulate in the first place.
- Faster test execution matters — a narrower test loading less of the web infrastructure (or none at all, for a pure unit test using a manually-constructed `AuthorizationManager`) than a full `MockMvc`-based integration test.
- Testing `@PostAuthorize` expressions specifically, which depend on the method's *return value* — this is naturally verified by calling the method directly and inspecting what comes back (or that an exception is thrown), with no HTTP response layer involved at all.

## 3. Core concept

```
Method security interceptor DOES NOT CARE how a method was invoked:
    directly from a test                    -> interceptor runs
    from a MockMvc-simulated HTTP request     -> interceptor runs
    from a real production HTTP request       -> interceptor runs
    from a scheduled job / message listener   -> interceptor runs

ALL of these paths go through the SAME AuthorizationManager-based check (card 0062),
reading SecurityContextHolder the SAME way, regardless of what triggered the call.

Testing method security DIRECTLY:
    @SpringBootTest (or a narrower @DataJpaTest/@Import(...)-based slice, as long as
    @EnableMethodSecurity's infrastructure and the target bean are both present)
    + @WithMockUser / @WithUserDetails / custom @WithSecurityContext annotation
    + a plain @Test method calling the service directly
    + assertThrows(AccessDeniedException.class, () -> service.method(...))
        or assertDoesNotThrow(...) / asserting the returned value, for the allowed case

NO MockMvc, NO HTTP simulation, NO web layer at all is required for this kind of test --
it is testing the AUTHORIZATION RULE, independent of whatever exposes the method.
```

This is precisely why cards 0127–0130's testing annotations were introduced generically, not as `MockMvc`-specific tools — they apply identically whether or not a web layer is involved at all.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing the same PreAuthorize annotated service method being called from a MockMvc simulated http request a direct test method call and a scheduled job all passing through the identical method security interceptor which checks the same SecurityContextHolder regardless of the caller">
  <rect x="20" y="20" width="160" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="100" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">MockMvc request</text>
  <text x="100" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(card 0131 style)</text>

  <rect x="240" y="20" width="160" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="320" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">direct test call</text>
  <text x="320" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(THIS card)</text>

  <rect x="460" y="20" width="160" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="540" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">scheduled job / listener</text>
  <text x="540" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(production)</text>

  <line x1="100" y1="70" x2="290" y2="120" stroke="#79c0ff" stroke-width="1.4" marker-end="url(#tms136)"/>
  <line x1="320" y1="70" x2="320" y2="120" stroke="#6db33f" stroke-width="1.4" marker-end="url(#tms136b)"/>
  <line x1="540" y1="70" x2="350" y2="120" stroke="#8b949e" stroke-width="1.4" marker-end="url(#tms136c)"/>

  <rect x="220" y="122" width="200" height="50" rx="7" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="320" y="142" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">SAME method security interceptor</text>
  <text x="320" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">checks the SAME SecurityContextHolder</text>

  <defs>
    <marker id="tms136" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="tms136b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="tms136c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Three entirely different callers, one identical interceptor — testing it directly needs none of the surrounding infrastructure.

## 5. Runnable example

The scenario: model a `@PreAuthorize`/`@PostAuthorize`-equivalent service being tested directly, growing from a single allowed/denied case into a small suite covering both annotation types, then into verifying that the exact same annotated method behaves identically whether called "directly" or via a simulated web-layer caller, proving the decoupling this card's core concept describes.

### Level 1 — Basic

A `@PreAuthorize`-equivalent service method, tested directly with no web layer at all.

```java
import java.util.*;

public class MethodSecurityTestLevel1 {
    record Authentication(String username, Set<String> authorities) {}
    static Authentication currentAuth; // stands in for SecurityContextHolder

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    // mirrors: @PreAuthorize("hasRole('ADMIN')") public void deleteOrder(String orderId)
    static void deleteOrder(String orderId) {
        if (!currentAuth.authorities().contains("ROLE_ADMIN")) throw new AccessDeniedException("Access Denied");
        System.out.println("order " + orderId + " deleted");
    }

    public static void main(String[] args) {
        // mirrors: @Test @WithMockUser(roles = "ADMIN") void adminCanDelete()
        currentAuth = new Authentication("admin", Set.of("ROLE_ADMIN"));
        try {
            deleteOrder("123");
            System.out.println("adminCanDelete: PASSED");
        } catch (AccessDeniedException e) {
            System.out.println("adminCanDelete: FAILED unexpectedly -- " + e.getMessage());
        }

        // mirrors: @Test @WithMockUser void regularUserCannotDelete()
        currentAuth = new Authentication("user", Set.of("ROLE_USER"));
        try {
            deleteOrder("123");
            System.out.println("regularUserCannotDelete: FAILED (should have thrown)");
        } catch (AccessDeniedException e) {
            System.out.println("regularUserCannotDelete: PASSED (correctly denied) -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `MethodSecurityTestLevel1.java`, run `java MethodSecurityTestLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
order 123 deleted
adminCanDelete: PASSED
regularUserCannotDelete: PASSED (correctly denied) -- Access Denied
```

No `MockMvc`, no HTTP simulation, no web layer at all — `deleteOrder` is called directly, exactly mirroring how a real `@SpringBootTest` with `@WithMockUser` would exercise the same `@PreAuthorize`-annotated service method, with the interceptor's check running purely against whatever `SecurityContextHolder` currently holds.

### Level 2 — Intermediate

Add a `@PostAuthorize`-equivalent method, whose check depends on the *return value* — naturally verified by inspecting what the method actually returns or whether it throws.

```java
import java.util.*;

public class MethodSecurityTestLevel2 {
    record Authentication(String username, Set<String> authorities) {}
    static Authentication currentAuth;

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }
    record Order(String id, String ownerUsername) {}

    static final Map<String, Order> orders = Map.of(
            "123", new Order("123", "alice"),
            "456", new Order("456", "bob"));

    // mirrors: @PostAuthorize("returnObject.ownerUsername == authentication.name")
    static Order findOrder(String orderId) {
        Order order = orders.get(orderId);
        if (!order.ownerUsername().equals(currentAuth.username())) {
            throw new AccessDeniedException("Access Denied -- this order does not belong to you");
        }
        return order;
    }

    public static void main(String[] args) {
        // mirrors: @Test @WithMockUser(username = "alice") void aliceCanSeeHerOwnOrder()
        currentAuth = new Authentication("alice", Set.of("ROLE_USER"));
        Order aliceOrder = findOrder("123");
        System.out.println("aliceCanSeeHerOwnOrder: PASSED, returned " + aliceOrder);

        // mirrors: @Test @WithMockUser(username = "alice") void aliceCannotSeeBobsOrder()
        try {
            findOrder("456");
            System.out.println("aliceCannotSeeBobsOrder: FAILED (should have thrown)");
        } catch (AccessDeniedException e) {
            System.out.println("aliceCannotSeeBobsOrder: PASSED (correctly denied) -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `MethodSecurityTestLevel2.java`, run `java MethodSecurityTestLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
aliceCanSeeHerOwnOrder: PASSED, returned Order[id=123, ownerUsername=alice]
aliceCannotSeeBobsOrder: PASSED (correctly denied) -- Access Denied -- this order does not belong to you
```

What changed: `findOrder`'s check depends on comparing the *returned* order's owner against the current principal's name, exactly mirroring a `@PostAuthorize` expression referencing `returnObject` — testing this naturally means calling the method and inspecting the outcome (the returned value, or the thrown exception), with no separate mechanism needed to verify a post-return check versus a pre-invocation one.

### Level 3 — Advanced

Verify the same annotated method behaves identically whether invoked "directly" (as in Levels 1–2) or through a simulated web-layer caller — proving the decoupling this card's core concept describes, and demonstrating why a narrower, direct test is a legitimate, sufficient way to verify the authorization rule itself.

```java
import java.util.*;

public class MethodSecurityTestLevel3 {
    record Authentication(String username, Set<String> authorities) {}
    static Authentication currentAuth;

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    // the SAME @PreAuthorize-annotated service method, called from TWO different "layers"
    static void deleteOrder(String orderId) {
        if (!currentAuth.authorities().contains("ROLE_ADMIN")) throw new AccessDeniedException("Access Denied");
        System.out.println("  order " + orderId + " deleted");
    }

    // simulates a "controller" -- the web layer -- that simply DELEGATES to the service
    static int controllerHandleDelete(String orderId) {
        try {
            deleteOrder(orderId); // the SAME interceptor runs, regardless of this being called from a "controller"
            return 204;
        } catch (AccessDeniedException e) {
            return 403;
        }
    }

    public static void main(String[] args) {
        System.out.println("--- DIRECT service call (no web layer) ---");
        currentAuth = new Authentication("admin", Set.of("ROLE_ADMIN"));
        try {
            deleteOrder("123");
            System.out.println("direct call, admin: PASSED");
        } catch (AccessDeniedException e) {
            System.out.println("direct call, admin: unexpectedly denied");
        }

        System.out.println("--- THROUGH a simulated web-layer controller ---");
        currentAuth = new Authentication("admin", Set.of("ROLE_ADMIN"));
        int adminStatus = controllerHandleDelete("456");
        System.out.println("via controller, admin: status=" + adminStatus);

        currentAuth = new Authentication("user", Set.of("ROLE_USER"));
        int userStatus = controllerHandleDelete("456");
        System.out.println("via controller, regular user: status=" + userStatus);

        System.out.println("--- CONCLUSION: the interceptor's decision was IDENTICAL either way -- ");
        System.out.println("    testing the service method DIRECTLY is a sufficient, valid way to verify the rule");
    }
}
```

**How to run:** save as `MethodSecurityTestLevel3.java`, run `java MethodSecurityTestLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- DIRECT service call (no web layer) ---
  order 123 deleted
direct call, admin: PASSED
--- THROUGH a simulated web-layer controller ---
  order 456 deleted
via controller, admin: status=204
via controller, regular user: status=403
--- CONCLUSION: the interceptor's decision was IDENTICAL either way --
    testing the service method DIRECTLY is a sufficient, valid way to verify the rule
```

What changed: the *exact same* `deleteOrder` method is invoked both directly and through a simulated `controllerHandleDelete` wrapper — in both paths, the same authorization decision is reached (admin succeeds, regular user is denied) — proving that a direct, `MockMvc`-free test of `deleteOrder` genuinely verifies the same authorization behavior a full web-layer test would, just without the overhead of simulating HTTP at all.

## 6. Walkthrough

Trace the regular-user denial from Level 3's "through a controller" section, then contrast with the direct-call path.

**Step 1 — a real test method, calling the service directly (no web layer):**
```java
@Test
@WithMockUser  // default: username="user", roles={"USER"}
void regularUserCannotDeleteOrder() {
    assertThrows(AccessDeniedException.class, () -> orderService.deleteOrder("456"));
}
```
This corresponds to the "DIRECT service call" section: `currentAuth` is set to a regular user, and `deleteOrder("456")` is called — the interceptor's check (`authorities.contains("ROLE_ADMIN")`) fails, throwing `AccessDeniedException`, and the test's `assertThrows` correctly captures this.

**Step 2 — the equivalent verification through a full web-layer test:**
```java
@Test
@WithMockUser
void regularUserGetsForbiddenViaController() throws Exception {
    mockMvc.perform(delete("/api/orders/456").with(csrf())).andExpect(status().isForbidden());
}
```
This corresponds to `controllerHandleDelete("456")` with `currentAuth` set to the regular user — internally, `controllerHandleDelete` calls the *identical* `deleteOrder` method, which throws the *identical* `AccessDeniedException`, caught and translated into a `403` status by the (simulated) controller's error handling.

**Step 3 — both tests verify the same underlying fact: `deleteOrder` correctly requires `ROLE_ADMIN`.** The direct test does so more narrowly and quickly (no HTTP simulation, no controller involved at all); the web-layer test additionally verifies that a genuine `403` HTTP response results, which is a legitimate, additional thing to check, but not a *different* verification of the authorization rule itself — both paths hit the identical interceptor logic.

**Step 4 — the practical takeaway.** A test suite reasonably uses *both* kinds of tests for different purposes: many narrow, fast, direct method-security tests covering every `@PreAuthorize`/`@PostAuthorize` expression's edge cases (multiple roles, ownership checks, combinations), plus a smaller number of full web-layer tests confirming the HTTP-facing behavior (status codes, response bodies) for the endpoints that matter most, rather than duplicating exhaustive authorization-rule coverage at the (slower, heavier) web-testing layer.

```
Direct test:        @WithMockUser -> deleteOrder("456") directly -> AccessDeniedException -> assertThrows PASSES
Web-layer test:      @WithMockUser -> MockMvc DELETE /api/orders/456 -> controller -> deleteOrder("456") -> AccessDeniedException -> 403 -> status().isForbidden() PASSES

SAME interceptor, SAME decision, reached via two different paths -- direct testing is a valid, sufficient
way to verify the AUTHORIZATION RULE itself.
```

## 7. Gotchas & takeaways

> **Gotcha:** a direct method-security test (as in this card) requires enough of the Spring context to be loaded for `@EnableMethodSecurity`'s interceptor to actually be active — a pure, hand-constructed unit test that `new`s up a service object directly (bypassing Spring's proxy-based AOP entirely) will never invoke the method security interceptor at all, since that interceptor is woven in via a dynamic proxy Spring creates around the bean, not via any mechanism a manually-instantiated object participates in. The test must obtain the service bean *through* the Spring context (via `@Autowired` in a `@SpringBootTest`, for instance) for the annotation to have any effect.

- Method security is checked by the same interceptor regardless of what invokes the annotated method — a `MockMvc`-simulated HTTP request, a direct test call, or a real production caller (a scheduled job, a message listener) all pass through identical authorization logic.
- Testing method security directly — no `MockMvc`, no HTTP simulation — is a legitimate, often preferable way to verify `@PreAuthorize`/`@PostAuthorize` expressions specifically, since it's faster and more narrowly targeted than a full web-layer test.
- `@PostAuthorize` expressions, which depend on a method's return value, are naturally verified by inspecting what a direct call actually returns (or that it throws), with no separate mechanism needed beyond calling the method and checking the outcome.
- Every testing annotation from earlier cards in this section (`@WithMockUser`, `@WithUserDetails`, custom `@WithSecurityContext`-based ones) applies identically to a direct method-security test as it does to a `MockMvc`-based one — none of them are web-layer-specific.
- The test must obtain the annotated bean through Spring's application context (not a manually constructed instance) for the method security interceptor — which is woven in via a dynamic proxy — to actually be active during the test.
