---
card: spring-security
gi: 129
slug: withuserdetails
title: "@WithUserDetails"
---

## 1. What it is

`@WithUserDetails` addresses the one gap card 0127's `@WithMockUser` deliberately leaves open: it doesn't construct a generic mock principal from annotation attributes — instead, it looks up a real `UserDetails` object by calling the application's *actual*, configured `UserDetailsService` bean with a given username, and builds the test's `Authentication` from whatever that real service returns. This means a test using `@WithUserDetails` exercises the application's genuine user-loading logic (custom fields, computed authorities, whatever a real `UserDetailsService` implementation does) rather than a framework-manufactured stand-in.

```java
@SpringBootTest
@AutoConfigureMockMvc
class OrderControllerTest {

    @Test
    @WithUserDetails("alice@example.com")  // looks up "alice@example.com" via the REAL UserDetailsService bean
    void aliceSeesHerOwnOrders() throws Exception {
        mockMvc.perform(get("/api/my-orders")).andExpect(status().isOk());
    }
}
```

## 2. Why & when

`@WithMockUser`'s convenience comes at a real cost: it builds a generic `org.springframework.security.core.userdetails.User` (or a bare `Authentication` with whatever authorities were specified), which is fine when a test only cares about role/authority checks, but falls short the moment application logic depends on something a custom `UserDetails` implementation carries — a database-backed user id used to scope a query (`WHERE user_id = ?`), a tenant identifier, or any field beyond username/authorities. `@WithUserDetails` closes that gap by routing through the real `UserDetailsService` — the exact same bean production code uses — so the resulting principal is genuinely indistinguishable from what a real login would have produced.

Reach for `@WithUserDetails` over `@WithMockUser` when:

- The application's `UserDetailsService` returns a custom implementation carrying fields (a database id, a tenant id, a display name) that the controller or service logic under test actually reads.
- Testing that a query correctly scopes results to "the current user" — this requires the test's principal to carry the *actual* database identifier the query filters by, not a synthetic mock value.
- A test needs to verify behavior that depends on account-status flags (locked, expired, disabled — card 0054's territory) as they're actually computed by the real `UserDetailsService`/`UserDetails` implementation, rather than a mock that always reports "enabled."
- The test setup already has a known, seeded user (via a test fixture, an `@Sql` script, or an in-memory test database) whose username can simply be referenced by string.

## 3. Core concept

```
@WithMockUser:
    builds a GENERIC mock UserDetails/Authentication directly from the annotation's OWN attributes
    NEVER calls any application bean at all

@WithUserDetails("alice@example.com"):
  1. locates the UserDetailsService BEAN from the test's Spring application context
       (by default, the bean named "userDetailsService"; configurable via userDetailsServiceBeanName)
  2. calls userDetailsService.loadUserByUsername("alice@example.com")  <-- the REAL implementation runs
  3. wraps the RETURNED UserDetails in an Authentication, placed into SecurityContextHolder
  4. this is the EXACT SAME UserDetails a real login for alice would have produced

Consequence: @WithUserDetails REQUIRES a Spring application context to be loaded
             (it's a bean lookup) -- it does NOT work in a pure unit test with no
             Spring context at all, unlike @WithMockUser, which needs nothing but
             the annotation itself.
```

The trade-off is explicit: `@WithMockUser` is faster and context-independent but generic; `@WithUserDetails` is slower (a real service call, possibly hitting a real or test database) but produces a genuinely authentic principal.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram contrasting WithMockUser which builds a generic principal directly from annotation attributes with no bean lookup against WithUserDetails which calls the applications real UserDetailsService bean to load an actual UserDetails object producing a genuinely authentic principal">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="160" y="42" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@WithMockUser</text>
  <text x="160" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">annotation attributes</text>
  <line x1="160" y1="72" x2="160" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wud129)"/>
  <text x="160" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">generic mock UserDetails</text>
  <text x="160" y="140" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">NO application bean called</text>
  <text x="160" y="158" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">works with NO Spring context</text>

  <rect x="330" y="20" width="290" height="160" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@WithUserDetails("alice@example.com")</text>
  <text x="475" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">real UserDetailsService BEAN</text>
  <line x1="475" y1="72" x2="475" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wud129b)"/>
  <text x="475" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.loadUserByUsername("alice@example.com")</text>
  <text x="475" y="140" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">REAL, custom UserDetails returned</text>
  <text x="475" y="158" fill="#f0883e" font-size="8.5" text-anchor="middle" font-family="sans-serif">requires a loaded Spring context</text>

  <defs>
    <marker id="wud129" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wud129b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

`@WithMockUser` builds a stand-in with no application involvement; `@WithUserDetails` calls the real bean, producing an authentic result at the cost of requiring a loaded context.

## 5. Runnable example

The scenario: a from-scratch `UserDetailsService`-style lookup, growing from a single custom-field lookup into showing what `@WithMockUser` alone would have missed, then into a scoped-query test that only works correctly with the real, custom principal.

### Level 1 — Basic

A custom `UserDetails` implementation with a field `@WithMockUser` could never provide, looked up via a real service.

```java
import java.util.*;

public class WithUserDetailsLevel1 {
    // a CUSTOM UserDetails implementation, carrying a field @WithMockUser's generic mock has no concept of
    record AppUserDetails(String username, Long databaseUserId, Set<String> authorities) {}

    static class RealUserDetailsService {
        private final Map<String, AppUserDetails> usersByUsername = new HashMap<>();
        void register(AppUserDetails user) { usersByUsername.put(user.username(), user); }

        // mirrors the REAL UserDetailsService bean's loadUserByUsername
        AppUserDetails loadUserByUsername(String username) {
            AppUserDetails user = usersByUsername.get(username);
            if (user == null) throw new NoSuchElementException("UsernameNotFoundException: " + username);
            return user;
        }
    }

    public static void main(String[] args) {
        RealUserDetailsService service = new RealUserDetailsService();
        service.register(new AppUserDetails("alice@example.com", 42L, Set.of("ROLE_USER")));

        // mirrors: @WithUserDetails("alice@example.com")
        AppUserDetails resolved = service.loadUserByUsername("alice@example.com");
        System.out.println("resolved via REAL service: " + resolved);
        System.out.println("database user id (unavailable via @WithMockUser alone): " + resolved.databaseUserId());
    }
}
```

**How to run:** save as `WithUserDetailsLevel1.java`, run `java WithUserDetailsLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
resolved via REAL service: AppUserDetails[username=alice@example.com, databaseUserId=42, authorities=[ROLE_USER]]
database user id (unavailable via @WithMockUser alone): 42
```

`loadUserByUsername` mirrors calling the application's real `UserDetailsService` bean — the returned object carries `databaseUserId`, a field that has no equivalent in `@WithMockUser`'s generic, framework-built principal.

### Level 2 — Intermediate

Contrast what a test using `@WithMockUser` versus `@WithUserDetails` would actually have access to, when the controller/service logic under test needs that custom field.

```java
import java.util.*;

public class WithUserDetailsLevel2 {
    record AppUserDetails(String username, Long databaseUserId, Set<String> authorities) {}
    record GenericMockPrincipal(String username, Set<String> authorities) {} // what @WithMockUser produces

    static class RealUserDetailsService {
        private final Map<String, AppUserDetails> usersByUsername = new HashMap<>();
        void register(AppUserDetails user) { usersByUsername.put(user.username(), user); }
        AppUserDetails loadUserByUsername(String username) { return usersByUsername.get(username); }
    }

    // the SERVICE UNDER TEST -- needs the database user id, not just a username
    static List<String> findMyOrders(Long databaseUserId, Map<Long, List<String>> ordersByUserId) {
        return ordersByUserId.getOrDefault(databaseUserId, List.of());
    }

    public static void main(String[] args) {
        RealUserDetailsService service = new RealUserDetailsService();
        service.register(new AppUserDetails("alice@example.com", 42L, Set.of("ROLE_USER")));

        Map<Long, List<String>> ordersByUserId = Map.of(42L, List.of("order-101", "order-102"));

        // WITH @WithUserDetails: the REAL databaseUserId is available
        AppUserDetails realPrincipal = service.loadUserByUsername("alice@example.com");
        List<String> orders = findMyOrders(realPrincipal.databaseUserId(), ordersByUserId);
        System.out.println("using @WithUserDetails, alice's orders: " + orders);

        // WITH @WithMockUser alone: there is NO databaseUserId to use at all --
        // the test would have to either skip this check or somehow guess/hardcode an id
        GenericMockPrincipal mockPrincipal = new GenericMockPrincipal("alice", Set.of("ROLE_USER"));
        System.out.println("using @WithMockUser, no databaseUserId field exists on the principal at all -- "
                + "findMyOrders(?, ...) has no real id to call with");
    }
}
```

**How to run:** save as `WithUserDetailsLevel2.java`, run `java WithUserDetailsLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
using @WithUserDetails, alice's orders: [order-101, order-102]
using @WithMockUser, no databaseUserId field exists on the principal at all -- findMyOrders(?, ...) has no real id to call with
```

What changed: the `findMyOrders` service method genuinely needs `databaseUserId` — a field only the real `UserDetailsService`-produced `AppUserDetails` carries — demonstrating concretely why `@WithMockUser`'s generic principal is insufficient here: there simply is no equivalent field to call `findMyOrders` with, whereas `@WithUserDetails` provides exactly the value production code would have.

### Level 3 — Advanced

A full scoped-query test verifying alice cannot see bob's orders — this genuinely requires each test to authenticate as a *distinct*, real principal with its own database id, something `@WithMockUser`'s generic, interchangeable mock principal cannot provide.

```java
import java.util.*;

public class WithUserDetailsLevel3 {
    record AppUserDetails(String username, Long databaseUserId, Set<String> authorities) {}
    record Order(String id, Long ownerId) {}

    static class RealUserDetailsService {
        private final Map<String, AppUserDetails> usersByUsername = new HashMap<>();
        void register(AppUserDetails user) { usersByUsername.put(user.username(), user); }
        AppUserDetails loadUserByUsername(String username) {
            AppUserDetails user = usersByUsername.get(username);
            if (user == null) throw new NoSuchElementException("UsernameNotFoundException: " + username);
            return user;
        }
    }

    // the ACTUAL production logic under test -- must NEVER leak another user's orders
    static List<Order> findOrdersForCurrentUser(Long currentUserId, List<Order> allOrders) {
        return allOrders.stream().filter(o -> o.ownerId().equals(currentUserId)).toList();
    }

    static void runTest(String testName, RealUserDetailsService service, String usernameToAuthenticateAs,
                         List<Order> allOrders, List<String> expectedOrderIds) {
        AppUserDetails principal = service.loadUserByUsername(usernameToAuthenticateAs); // mirrors @WithUserDetails
        List<Order> result = findOrdersForCurrentUser(principal.databaseUserId(), allOrders);
        List<String> actualIds = result.stream().map(Order::id).toList();
        boolean pass = actualIds.equals(expectedOrderIds);
        System.out.println(testName + ": " + (pass ? "PASS" : "FAIL")
                + " (expected=" + expectedOrderIds + ", actual=" + actualIds + ")");
    }

    public static void main(String[] args) {
        RealUserDetailsService service = new RealUserDetailsService();
        service.register(new AppUserDetails("alice@example.com", 42L, Set.of("ROLE_USER")));
        service.register(new AppUserDetails("bob@example.com", 99L, Set.of("ROLE_USER")));

        List<Order> allOrders = List.of(
                new Order("order-101", 42L), new Order("order-102", 42L), // alice's
                new Order("order-201", 99L));                              // bob's

        // mirrors: @Test @WithUserDetails("alice@example.com") void aliceSeesOnlyHerOwnOrders()
        runTest("aliceSeesOnlyHerOwnOrders", service, "alice@example.com", allOrders, List.of("order-101", "order-102"));

        // mirrors: @Test @WithUserDetails("bob@example.com") void bobSeesOnlyHisOwnOrders()
        runTest("bobSeesOnlyHisOwnOrders", service, "bob@example.com", allOrders, List.of("order-201"));
    }
}
```

**How to run:** save as `WithUserDetailsLevel3.java`, run `java WithUserDetailsLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
aliceSeesOnlyHerOwnOrders: PASS (expected=[order-101, order-102], actual=[order-101, order-102])
bobSeesOnlyHisOwnOrders: PASS (expected=[order-201], actual=[order-201])
```

What changed: each test now authenticates as a genuinely *distinct* real user, each carrying their own real `databaseUserId` from the real service — this is exactly the scenario `@WithMockUser` cannot express well, since its generic mock principal has no natural way to represent "a different, specific real user with their own real id" across multiple test methods without significant custom setup, whereas `@WithUserDetails("alice@example.com")` and `@WithUserDetails("bob@example.com")` express this directly and legibly.

## 6. Walkthrough

Trace alice's test from Level 3, mapping each step to the real annotation's behavior.

**Step 1 — the real test method:**
```java
@Test
@WithUserDetails("alice@example.com")
void aliceSeesOnlyHerOwnOrders() throws Exception {
    mockMvc.perform(get("/api/my-orders"))
           .andExpect(jsonPath("$[*].id", containsInAnyOrder("order-101", "order-102")));
}
```

**Step 2 — before the test body runs**, Spring Security's test infrastructure locates the `UserDetailsService` bean in the test's Spring application context (this is precisely why `@WithUserDetails` requires a context with such a bean registered — a `@WebMvcTest` slice test would need to explicitly provide or mock one, while a full `@SpringBootTest` typically has the real one already wired) and calls `loadUserByUsername("alice@example.com")` on it.

**Step 3 — the real lookup runs**, corresponding to `service.loadUserByUsername("alice@example.com")` in Level 3's code — returning `AppUserDetails("alice@example.com", 42L, {"ROLE_USER"})`, the exact object the application's real logic would use for any genuine login by alice.

**Step 4 — this real `UserDetails` is wrapped into an `Authentication` and placed into `SecurityContextHolder`**, available to the controller invoked by `mockMvc.perform(...)`.

**Step 5 — the controller (or the service it delegates to) reads the principal's `databaseUserId`.** In a real controller, this might look like `@AuthenticationPrincipal AppUserDetails principal` followed by `orderService.findOrdersForCurrentUser(principal.getDatabaseUserId())` — corresponding to `findOrdersForCurrentUser(principal.databaseUserId(), allOrders)`.

**Step 6 — the query correctly scopes to alice's own orders only.** `allOrders.stream().filter(o -> o.ownerId().equals(42L))` returns exactly `order-101` and `order-102` — bob's `order-201` (owned by user id `99L`) is correctly excluded, verifying the scoping logic genuinely works, using alice's *real* id rather than a value a mock principal could never have provided.

```
@WithUserDetails("alice@example.com")
        |
        v (before test body runs)
UserDetailsService.loadUserByUsername("alice@example.com") -- REAL bean, REAL lookup
        |
        v
AppUserDetails(username=alice@example.com, databaseUserId=42, ...) -- REAL object
        |
        v
placed in SecurityContextHolder -> available to controller/service under test
        |
        v
findOrdersForCurrentUser(42L, allOrders) -> [order-101, order-102]  (bob's order-201 correctly excluded)
```

## 7. Gotchas & takeaways

> **Gotcha:** `@WithUserDetails` fails immediately (typically with a `UsernameNotFoundException` surfaced as a test setup failure, not a normal test assertion failure) if the given username doesn't exist according to the real `UserDetailsService` — this means the referenced user must genuinely be present in whatever backing store or in-memory user store the test's Spring context is configured against, via a seeded fixture, an `@Sql` script, or a pre-populated `InMemoryUserDetailsManager`, before the annotated test method ever runs.

- `@WithUserDetails` calls the application's real `UserDetailsService` bean to build the test's principal, in contrast to `@WithMockUser`'s framework-manufactured generic mock — the trade-off is authenticity versus speed and context-independence.
- Reach for it specifically when test logic depends on custom `UserDetails` fields (a database id, a tenant id) that a generic mock principal simply has no way to represent.
- It requires a loaded Spring application context containing a `UserDetailsService` bean — it cannot be used in a context-free unit test the way `@WithMockUser` can.
- Testing per-user data scoping (verifying alice cannot see bob's data) is a natural fit for `@WithUserDetails`, since each test method can authenticate as a genuinely distinct, real user with their own real identifying data.
- A username referenced by `@WithUserDetails` that doesn't exist in the configured `UserDetailsService` fails the test at setup time, before the test body even runs — this is a signal to check test fixture/seed data, not the test's own assertions.
