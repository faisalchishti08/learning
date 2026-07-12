---
card: spring-security
gi: 127
slug: withmockuser
title: "@WithMockUser"
---

## 1. What it is

`@WithMockUser` is the single most commonly used Spring Security testing annotation: placed on a test method (or test class, applying to every method within it), it causes a `SecurityContext` containing a mock, framework-constructed `Authentication` — carrying a specified username, password, and roles/authorities — to be populated *before* that test method runs, and cleared automatically afterward. No real authentication (no password check, no database lookup, no `AuthenticationManager` invocation at all) ever happens; the `Authentication` object is simply constructed directly and dropped into `SecurityContextHolder`.

```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {

    @Test
    @WithMockUser(username = "alice", roles = {"USER", "ADMIN"})
    void adminCanDeleteOrder() throws Exception {
        mockMvc.perform(delete("/api/orders/123"))
               .andExpect(status().isNoContent());
    }
}
```

## 2. Why & when

Testing an `@PreAuthorize`-annotated method or an `authorizeHttpRequests` rule genuinely requires *some* authenticated principal to be present when the test executes — but re-running a full login flow (submitting credentials, following redirects, handling CSRF tokens) in every single test that merely wants to verify "does an ADMIN get past this check" would be enormous, unnecessary overhead, and would couple every authorization test to the specific mechanics of however the application authenticates in production. `@WithMockUser` decouples "testing that authorization rules behave correctly given a certain principal" from "testing that the login mechanism itself works" — the latter is a separate, narrower concern (covered in card 0133's `MockMvc` form-login testing), letting the vast majority of authorization-focused tests skip login entirely and simply declare the principal they want to test against.

Reach for `@WithMockUser` when:

- Testing `authorizeHttpRequests` rules or `@PreAuthorize`/`@PostAuthorize`-annotated methods against a specific role or authority combination — this is the primary, most common use case for this annotation.
- The exact identity of the principal (a real username tied to a real database record) doesn't matter for what the test is verifying — only that *some* authenticated user with certain authorities is present.
- Writing many similar tests each verifying a different role/authority combination against the same endpoint — `@WithMockUser`'s attributes make this a one-line declaration per test case rather than a repeated setup block.

Reach instead for `@WithUserDetails` (card 0129) when the test needs the *actual* `UserDetails` your application's own `UserDetailsService` would produce (custom fields beyond the default mock's shape), since `@WithMockUser` always constructs a generic, framework-default principal.

## 3. Core concept

```
@WithMockUser(username = "alice", roles = {"USER", "ADMIN"}, password = "password")
    DEFAULT username: "user"     (if not specified)
    DEFAULT password: "password" (if not specified)
    DEFAULT roles:    {"USER"}   (if neither roles NOR authorities specified)

    roles = {"USER", "ADMIN"}  -->  automatically becomes authorities: ROLE_USER, ROLE_ADMIN
                                     (the "ROLE_" prefix is added FOR you)
    authorities = {"SCOPE_read"} --> used VERBATIM, NO prefix added
                                     (use "authorities" instead of "roles" when you need
                                      an authority WITHOUT the ROLE_ prefix)

TEST LIFECYCLE:
  1. BEFORE the test method runs: a TestSecurityContextHolderPostProcessor-driven mechanism
     builds a mock Authentication from the annotation's attributes and sets it in SecurityContextHolder
  2. the TEST METHOD runs -- any code checking SecurityContextHolder (or MockMvc requests
     going through the security filter chain) sees this mock Authentication as already-authenticated
  3. AFTER the test method: the context is CLEARED automatically, so the next test starts clean
```

No real credential validation, no database lookup, no `AuthenticationProvider` invocation happens at any point — the `Authentication` object is manufactured directly from the annotation's own attributes.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a test method annotated with WithMockUser having a mock Authentication constructed directly from the annotations attributes and placed into SecurityContextHolder before the test runs then cleared automatically afterward with no real authentication mechanism ever invoked">
  <rect x="20" y="20" width="220" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="130" y="42" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">@WithMockUser(roles="ADMIN")</text>
  <text x="130" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">on a @Test method</text>

  <line x1="240" y1="50" x2="285" y2="50" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#wmu127)"/>

  <rect x="290" y="20" width="150" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="365" y="42" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">mock Authentication</text>
  <text x="365" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">NO real auth check</text>

  <line x1="365" y1="80" x2="365" y2="110" stroke="#6db33f" stroke-width="1.6" marker-end="url(#wmu127b)"/>

  <rect x="290" y="112" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="365" y="136" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">SecurityContextHolder</text>

  <line x1="440" y1="132" x2="490" y2="132" stroke="#8b949e" stroke-width="1.5" marker-end="url(#wmu127c)"/>

  <rect x="495" y="112" width="120" height="40" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.3"/>
  <text x="555" y="136" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">test method runs</text>

  <text x="365" y="170" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">context CLEARED automatically after the test method returns</text>

  <defs>
    <marker id="wmu127" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wmu127b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wmu127c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

No login flow, no credential check — a fully-formed `Authentication` is manufactured directly, purely to exercise authorization logic.

## 5. Runnable example

The scenario: model `@WithMockUser`'s attribute-to-authority translation and lifecycle, growing from a bare default-attribute case into the `roles` versus `authorities` distinction, then into a small suite exercising several role combinations against a simulated `@PreAuthorize` check.

### Level 1 — Basic

Default attributes, and the automatic `ROLE_` prefixing.

```java
import java.util.*;

public class WithMockUserLevel1 {
    record MockUserAttributes(String username, String password, List<String> roles) {}
    record Authentication(String principalName, Set<String> authorities) {}

    // mirrors WithMockUserSecurityContextFactory's core translation logic
    static Authentication buildMockAuthentication(MockUserAttributes attrs) {
        Set<String> authorities = new LinkedHashSet<>();
        for (String role : attrs.roles()) authorities.add("ROLE_" + role);
        return new Authentication(attrs.username(), authorities);
    }

    public static void main(String[] args) {
        // mirrors: @WithMockUser  (no attributes at all -- every default applies)
        MockUserAttributes defaults = new MockUserAttributes("user", "password", List.of("USER"));
        Authentication auth = buildMockAuthentication(defaults);

        System.out.println("principal: " + auth.principalName());
        System.out.println("authorities: " + auth.authorities());
    }
}
```

**How to run:** save as `WithMockUserLevel1.java`, run `java WithMockUserLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
principal: user
authorities: [ROLE_USER]
```

`buildMockAuthentication` mirrors exactly what `@WithMockUser`'s bare, no-attribute form produces: username `"user"`, one authority `ROLE_USER` — the framework's stated defaults, with the `ROLE_` prefix applied automatically from the bare role name `"USER"`.

### Level 2 — Intermediate

The `roles` vs. `authorities` distinction — `roles` gets prefixed automatically, `authorities` is used verbatim.

```java
import java.util.*;

public class WithMockUserLevel2 {
    record MockUserAttributes(String username, List<String> roles, List<String> authorities) {}
    record Authentication(String principalName, Set<String> grantedAuthorities) {}

    static Authentication buildMockAuthentication(MockUserAttributes attrs) {
        Set<String> resolved = new LinkedHashSet<>();
        for (String role : attrs.roles()) resolved.add("ROLE_" + role); // AUTOMATIC prefix
        for (String authority : attrs.authorities()) resolved.add(authority); // VERBATIM, no prefix added
        return new Authentication(attrs.username(), resolved);
    }

    public static void main(String[] args) {
        // mirrors: @WithMockUser(username = "alice", roles = {"USER", "ADMIN"})
        Authentication viaRoles = buildMockAuthentication(
                new MockUserAttributes("alice", List.of("USER", "ADMIN"), List.of()));
        System.out.println("via roles: " + viaRoles.grantedAuthorities());

        // mirrors: @WithMockUser(username = "bob", authorities = {"SCOPE_read", "SCOPE_write"})
        Authentication viaAuthorities = buildMockAuthentication(
                new MockUserAttributes("bob", List.of(), List.of("SCOPE_read", "SCOPE_write")));
        System.out.println("via authorities: " + viaAuthorities.grantedAuthorities());
    }
}
```

**How to run:** save as `WithMockUserLevel2.java`, run `java WithMockUserLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
via roles: [ROLE_USER, ROLE_ADMIN]
via authorities: [SCOPE_read, SCOPE_write]
```

What changed: `roles` entries always gain the `"ROLE_"` prefix automatically, while `authorities` entries are used exactly as written — this distinction matters because a `@PreAuthorize("hasAuthority('SCOPE_read')")` check needs a test using `authorities = {"SCOPE_read"}`, not `roles = {"SCOPE_read"}` (which would incorrectly produce `ROLE_SCOPE_read`, matching nothing).

### Level 3 — Advanced

A small suite of test-style cases exercising several role combinations against a simulated `@PreAuthorize("hasRole('ADMIN')")` check, mirroring exactly the kind of table of test methods `@WithMockUser` makes concise to write.

```java
import java.util.*;

public class WithMockUserLevel3 {
    record MockUserAttributes(String username, List<String> roles, List<String> authorities) {}
    record Authentication(String principalName, Set<String> grantedAuthorities) {}

    static Authentication buildMockAuthentication(MockUserAttributes attrs) {
        Set<String> resolved = new LinkedHashSet<>();
        for (String role : attrs.roles()) resolved.add("ROLE_" + role);
        for (String authority : attrs.authorities()) resolved.add(authority);
        return new Authentication(attrs.username(), resolved);
    }

    // the "controller/service" under test -- mirrors @PreAuthorize("hasRole('ADMIN')")
    static String deleteOrder(Authentication auth, String orderId) {
        if (!auth.grantedAuthorities().contains("ROLE_ADMIN")) {
            throw new SecurityException("Access Denied");
        }
        return "order " + orderId + " deleted";
    }

    static void runTest(String testName, MockUserAttributes mockUser, String orderId) {
        Authentication auth = buildMockAuthentication(mockUser);
        try {
            String result = deleteOrder(auth, orderId);
            System.out.println("PASS-EXPECTED-ALLOWED: " + testName + " -> " + result);
        } catch (SecurityException e) {
            System.out.println("PASS-EXPECTED-DENIED: " + testName + " -> " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        // mirrors: @Test @WithMockUser(roles = "ADMIN") void adminCanDelete()
        runTest("admin deletes order", new MockUserAttributes("admin-user", List.of("ADMIN"), List.of()), "123");

        // mirrors: @Test @WithMockUser void regularUserCannotDelete()  (default roles = {"USER"})
        runTest("regular user attempts delete", new MockUserAttributes("user", List.of("USER"), List.of()), "123");

        // mirrors: @Test @WithMockUser(roles = {"USER", "ADMIN"}) void userWithBothRolesCanDelete()
        runTest("user with BOTH roles deletes order", new MockUserAttributes("alice", List.of("USER", "ADMIN"), List.of()), "456");
    }
}
```

**How to run:** save as `WithMockUserLevel3.java`, run `java WithMockUserLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
PASS-EXPECTED-ALLOWED: admin deletes order -> order 123 deleted
PASS-EXPECTED-DENIED: regular user attempts delete -> Access Denied
PASS-EXPECTED-ALLOWED: user with BOTH roles deletes order -> order 456 deleted
```

What changed: `runTest` now exercises three distinct `@WithMockUser`-equivalent configurations against the same guarded operation — this mirrors precisely how a real test class using `@WithMockUser` would structure three separate `@Test` methods, each with a different annotation attribute, to cover the "authorized," "denied," and "authorized via a different role combination" cases without writing any custom `Authentication`-building code per test.

## 6. Walkthrough

Trace the "regular user attempts delete" case from Level 3, mapping it directly to a real annotated test method.

**Step 1 — the real test method:**
```java
@Test
@WithMockUser  // defaults: username="user", roles={"USER"}
void regularUserCannotDeleteOrder() {
    assertThrows(AccessDeniedException.class, () -> orderService.deleteOrder("123"));
}
```

**Step 2 — before the test method body runs**, Spring Security's test infrastructure reads the annotation's attributes (all defaults here, since none were specified) and constructs a mock `Authentication` — corresponding to `buildMockAuthentication(new MockUserAttributes("user", List.of("USER"), List.of()))`, yielding `authorities = {"ROLE_USER"}`.

**Step 3 — this `Authentication` is placed into `SecurityContextHolder`**, made available to any code the test method invokes — including, if this were a real `@PreAuthorize`-annotated service method being called directly (card 0136 covers this specific case), the method security interceptor that checks it.

**Step 4 — the test body calls the guarded operation.** `orderService.deleteOrder("123")` — corresponding to `deleteOrder(auth, "123")` in Level 3's code — checks `auth.grantedAuthorities().contains("ROLE_ADMIN")`, which is `false` for this mock user (`{"ROLE_USER"}` only), so `SecurityException("Access Denied")` is thrown.

**Step 5 — the test assertion passes**, since the real test expected exactly this exception. In Level 3's simplified simulation, this corresponds to the `catch` block printing the "expected denied" message rather than failing.

**Step 6 — after the test method returns, the mock `SecurityContext` is cleared automatically**, ensuring the next test method (which might use a different `@WithMockUser` configuration, or none at all) starts with a completely clean slate — no leftover authentication state can leak between tests.

```
@WithMockUser (defaults: user, ROLE_USER)
        |
        v  (before test method body runs)
mock Authentication built, placed in SecurityContextHolder
        |
        v
test body: orderService.deleteOrder("123")
        |
        v
@PreAuthorize("hasRole('ADMIN')") check: ROLE_USER present? NO -> AccessDeniedException
        |
        v (test asserts this exception WAS thrown -- test PASSES)
        |
        v  (after test method returns)
SecurityContext cleared -- next test starts clean
```

## 7. Gotchas & takeaways

> **Gotcha:** `roles` and `authorities` are not interchangeable — a `@PreAuthorize("hasAuthority('SCOPE_admin')")` check will never pass under `@WithMockUser(roles = "SCOPE_admin")`, since that produces the authority `"ROLE_SCOPE_admin"` (the prefix is *always* added for `roles`), not `"SCOPE_admin"` itself. When a check uses `hasAuthority(...)` rather than `hasRole(...)`, use the `authorities` attribute, which is applied verbatim.

- `@WithMockUser` constructs a fully mock `Authentication` directly, with zero real authentication (no credential check, no database lookup) — it exists purely to let authorization-focused tests skip the login mechanism entirely.
- Its default username is `"user"`, default password is `"password"`, and default role is `{"USER"}` when no attributes are specified at all.
- The `roles` attribute automatically prefixes each entry with `"ROLE_"`; the `authorities` attribute uses each entry exactly as written — mixing these up is one of the most common mistakes when writing Spring Security tests.
- The mock security context is populated before the annotated test method runs and cleared automatically afterward, so no state leaks between test methods regardless of test execution order.
- For tests needing the application's actual, custom `UserDetails` implementation (rather than a generic mock principal), `@WithUserDetails` (card 0129) is the more appropriate annotation.
