---
card: spring-security
gi: 128
slug: withanonymoususer
title: "@WithAnonymousUser"
---

## 1. What it is

`@WithAnonymousUser` is the deliberate opposite of card 0127's `@WithMockUser`: rather than populating `SecurityContextHolder` with an authenticated principal, it explicitly sets an `AnonymousAuthenticationToken` — the same object `AnonymousAuthenticationFilter` (card 0007's territory) installs for any real, unauthenticated request — ensuring a test method runs under precisely the "not logged in" state, regardless of what class-level `@WithMockUser` annotation might otherwise apply.

```java
@WebMvcTest(OrderController.class)
@WithMockUser  // applies to EVERY test method in this class by default
class OrderControllerTest {

    @Test
    void authenticatedUserCanViewOrders() throws Exception {
        mockMvc.perform(get("/api/orders")).andExpect(status().isOk()); // uses the class-level @WithMockUser
    }

    @Test
    @WithAnonymousUser  // OVERRIDES the class-level annotation for just this one method
    void anonymousUserIsRedirectedToLogin() throws Exception {
        mockMvc.perform(get("/api/orders")).andExpect(status().is3xxRedirection());
    }
}
```

## 2. Why & when

A test class commonly wants most of its test methods to run as some authenticated user — placing `@WithMockUser` at the class level is the natural way to express that default. But a handful of tests specifically need to verify the *unauthenticated* path — confirming an endpoint correctly rejects or redirects a request with no credentials at all — and without a way to override the class-level default for just those methods, a developer would be forced to either move those specific tests to a separate class (fragmenting related tests unnecessarily) or manually clear `SecurityContextHolder` inside the test body (easy to forget, and bypasses the declarative style every other test in the class uses). `@WithAnonymousUser` exists specifically to let one method deliberately opt out of a class-wide authenticated default.

Reach for `@WithAnonymousUser` when:

- A test class uses a class-level `@WithMockUser` (or similar) as its default, but a specific test method needs to verify behavior for a genuinely unauthenticated request instead.
- Testing that a protected endpoint correctly rejects (401) or redirects (302 to a login page) an anonymous request — the negative-path counterpart to the many `@WithMockUser`-annotated tests verifying the authenticated, authorized path.
- Verifying that a `permitAll()`-configured endpoint remains reachable without authentication — confirming the *absence* of an authentication requirement is just as important to test as the presence of an authorization rule.

## 3. Core concept

```
Class-level @WithMockUser applies to EVERY @Test method in the class BY DEFAULT.

@WithAnonymousUser, placed on a SPECIFIC method:
    OVERRIDES the class-level annotation for THAT method only
    installs an AnonymousAuthenticationToken instead --
        principal: "anonymousUser" (the framework's fixed anonymous key)
        authorities: {ROLE_ANONYMOUS} (or whatever the anonymous() DSL configured)

This is functionally IDENTICAL to what a real, un-authenticated request would see --
AnonymousAuthenticationFilter installs the SAME kind of token for any request that reaches it
without prior authentication, so a test using @WithAnonymousUser exercises the EXACT SAME
code path an anonymous internet visitor's request would.

Precedence (method-level annotations win over class-level ones) is standard JUnit/Spring
Test behavior, not something specific to security testing -- @WithAnonymousUser simply
takes advantage of that existing override mechanism.
```

The anonymous token is not "no authentication at all" — it's a specific, real `Authentication` implementation representing exactly that state, which is precisely why `authorizeHttpRequests`/`@PreAuthorize` checks can reason about it consistently.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a test class with a class level WithMockUser default applying to most test methods while one specific method annotated WithAnonymousUser overrides that default to install an AnonymousAuthenticationToken instead exercising the same code path a real unauthenticated request would">
  <rect x="20" y="20" width="600" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@WithMockUser (class-level default)</text>

  <line x1="150" y1="70" x2="150" y2="100" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wau128)"/>
  <line x1="490" y1="70" x2="490" y2="100" stroke="#f0883e" stroke-width="1.5" marker-end="url(#wau128b)"/>

  <rect x="40" y="102" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="150" y="126" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">test 1: uses class-level default</text>

  <rect x="380" y="102" width="220" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.4"/>
  <text x="490" y="120" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">test 2: @WithAnonymousUser</text>
  <text x="490" y="134" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OVERRIDES the class default</text>

  <text x="150" y="170" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">runs as mock authenticated user</text>
  <text x="490" y="170" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">runs as AnonymousAuthenticationToken</text>

  <defs>
    <marker id="wau128" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wau128b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

Method-level `@WithAnonymousUser` overrides a class-level authenticated default for exactly the one test that needs it.

## 5. Runnable example

The scenario: model the class-level-default-with-method-override pattern directly, growing from a single override case into a small suite mixing authenticated and anonymous tests, then into verifying the anonymous token behaves identically to a genuinely unauthenticated request against an authorization rule.

### Level 1 — Basic

A class-level default, overridden by one method.

```java
import java.util.*;

public class WithAnonymousUserLevel1 {
    record Authentication(String principalName, Set<String> authorities, boolean isAnonymous) {}

    static final Authentication CLASS_DEFAULT = new Authentication("user", Set.of("ROLE_USER"), false);
    static final Authentication ANONYMOUS = new Authentication("anonymousUser", Set.of("ROLE_ANONYMOUS"), true);

    // mirrors resolving which Authentication applies to a GIVEN test method,
    // given an optional method-level override
    static Authentication resolveForMethod(boolean hasAnonymousOverride) {
        return hasAnonymousOverride ? ANONYMOUS : CLASS_DEFAULT;
    }

    public static void main(String[] args) {
        Authentication testWithoutOverride = resolveForMethod(false);
        Authentication testWithOverride = resolveForMethod(true);

        System.out.println("test without @WithAnonymousUser: " + testWithoutOverride);
        System.out.println("test WITH @WithAnonymousUser: " + testWithOverride);
    }
}
```

**How to run:** save as `WithAnonymousUserLevel1.java`, run `java WithAnonymousUserLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
test without @WithAnonymousUser: Authentication[principalName=user, authorities=[ROLE_USER], isAnonymous=false]
test WITH @WithAnonymousUser: Authentication[principalName=anonymousUser, authorities=[ROLE_ANONYMOUS], isAnonymous=true]
```

`resolveForMethod` mirrors exactly how the test infrastructure decides which `Authentication` to install for a given method: absent an override, the class-level `@WithMockUser` default applies; with `@WithAnonymousUser` present, the anonymous token replaces it entirely for that one method.

### Level 2 — Intermediate

A small suite mixing default (authenticated) and overridden (anonymous) test methods.

```java
import java.util.*;

public class WithAnonymousUserLevel2 {
    record Authentication(String principalName, Set<String> authorities) {}

    static final Authentication CLASS_DEFAULT = new Authentication("user", Set.of("ROLE_USER"));
    static final Authentication ANONYMOUS = new Authentication("anonymousUser", Set.of("ROLE_ANONYMOUS"));

    // the "endpoint" under test -- mirrors authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
    static int handleRequest(Authentication auth) {
        boolean isAuthenticated = !auth.authorities().contains("ROLE_ANONYMOUS");
        return isAuthenticated ? 200 : 302; // 302 = redirect to login, mirroring an unauthenticated request
    }

    static void runTest(String testName, Authentication authForThisTest, int expectedStatus) {
        int actualStatus = handleRequest(authForThisTest);
        System.out.println(testName + ": expected=" + expectedStatus + " actual=" + actualStatus
                + (actualStatus == expectedStatus ? " PASS" : " FAIL"));
    }

    public static void main(String[] args) {
        // mirrors: @Test void authenticatedUserCanViewOrders() -- uses class-level default
        runTest("authenticatedUserCanViewOrders (class default)", CLASS_DEFAULT, 200);

        // mirrors: @Test @WithAnonymousUser void anonymousUserIsRedirected() -- method override
        runTest("anonymousUserIsRedirected (@WithAnonymousUser)", ANONYMOUS, 302);
    }
}
```

**How to run:** save as `WithAnonymousUserLevel2.java`, run `java WithAnonymousUserLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticatedUserCanViewOrders (class default): expected=200 actual=200 PASS
anonymousUserIsRedirected (@WithAnonymousUser): expected=302 actual=302 PASS
```

What changed: `handleRequest` now models the actual authorization decision an `anyRequest().authenticated()` rule would make — the class-default authenticated user passes, while the `@WithAnonymousUser`-overridden test correctly exercises the redirect path a real anonymous visitor would hit, both verified within the same simulated test class.

### Level 3 — Advanced

Verify the anonymous token behaves identically to a genuinely unauthenticated request across multiple authorization rule types (`permitAll`, `authenticated`, a specific role requirement) — confirming `@WithAnonymousUser` is a faithful stand-in for "no real login occurred," not merely a different label for the same thing.

```java
import java.util.*;
import java.util.function.*;

public class WithAnonymousUserLevel3 {
    record Authentication(String principalName, Set<String> authorities) {}

    static final Authentication ANONYMOUS = new Authentication("anonymousUser", Set.of("ROLE_ANONYMOUS"));
    static final Authentication REGULAR_USER = new Authentication("alice", Set.of("ROLE_USER"));
    static final Authentication ADMIN_USER = new Authentication("admin", Set.of("ROLE_USER", "ROLE_ADMIN"));

    static boolean isAnonymous(Authentication auth) { return auth.authorities().contains("ROLE_ANONYMOUS"); }

    static class AuthorizationRule {
        final String description;
        final Function<Authentication, Boolean> check;
        AuthorizationRule(String description, Function<Authentication, Boolean> check) {
            this.description = description; this.check = check;
        }
    }

    public static void main(String[] args) {
        List<AuthorizationRule> rules = List.of(
                new AuthorizationRule("permitAll", auth -> true),
                new AuthorizationRule("authenticated()", auth -> !isAnonymous(auth)),
                new AuthorizationRule("hasRole('ADMIN')", auth -> !isAnonymous(auth) && auth.authorities().contains("ROLE_ADMIN")));

        List<Map.Entry<String, Authentication>> testPrincipals = List.of(
                Map.entry("@WithAnonymousUser", ANONYMOUS),
                Map.entry("@WithMockUser (default)", REGULAR_USER),
                Map.entry("@WithMockUser(roles=\"ADMIN\")", ADMIN_USER));

        for (AuthorizationRule rule : rules) {
            System.out.println("--- rule: " + rule.description + " ---");
            for (var entry : testPrincipals) {
                boolean allowed = rule.check.apply(entry.getValue());
                System.out.println("  " + entry.getKey() + ": " + (allowed ? "ALLOWED" : "DENIED/REDIRECTED"));
            }
        }
    }
}
```

**How to run:** save as `WithAnonymousUserLevel3.java`, run `java WithAnonymousUserLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
--- rule: permitAll ---
  @WithAnonymousUser: ALLOWED
  @WithMockUser (default): ALLOWED
  @WithMockUser(roles="ADMIN"): ALLOWED
--- rule: authenticated() ---
  @WithAnonymousUser: DENIED/REDIRECTED
  @WithMockUser (default): ALLOWED
  @WithMockUser(roles="ADMIN"): ALLOWED
--- rule: hasRole('ADMIN') ---
  @WithAnonymousUser: DENIED/REDIRECTED
  @WithMockUser (default): DENIED/REDIRECTED
  @WithMockUser(roles="ADMIN"): ALLOWED
```

What changed: the same three simulated principals are now checked against three different rule types — `@WithAnonymousUser`'s token correctly passes a `permitAll` rule (anyone can reach it) but fails both `authenticated()` and `hasRole('ADMIN')` exactly as a genuinely unauthenticated real request would, confirming the annotation is a faithful, complete stand-in for "no login happened" across every authorization rule shape this course has covered, not merely for one specific case.

## 6. Walkthrough

Trace the `authenticated()`-rule check for `@WithAnonymousUser` from Level 3, then contrast with `permitAll`.

**Step 1 — a test method is annotated:**
```java
@Test
@WithAnonymousUser
void anonymousRequestToProtectedEndpointRedirects() throws Exception {
    mockMvc.perform(get("/api/orders")).andExpect(status().is3xxRedirection());
}
```

**Step 2 — before this method runs**, Spring Security's test infrastructure installs an `AnonymousAuthenticationToken` into `SecurityContextHolder` — corresponding to `ANONYMOUS` in Level 3's model, with `authorities = {"ROLE_ANONYMOUS"}`.

**Step 3 — the simulated request hits the security filter chain's authorization check.** For an endpoint configured `anyRequest().authenticated()`, this corresponds to evaluating `rule.check.apply(ANONYMOUS)` for the `"authenticated()"` rule — `isAnonymous(ANONYMOUS)` is `true` (it *is* the anonymous token), so `!isAnonymous(auth)` evaluates `false`.

**Step 4 — the rule denies the request**, and in a real Spring Security application, this triggers the configured `AuthenticationEntryPoint` — typically a redirect to a login page for a browser-facing application, or a `401` for an API — corresponding to the `"DENIED/REDIRECTED"` output.

**Step 5 — the test assertion passes**, since `status().is3xxRedirection()` matches the actual outcome — the test successfully verified the negative path without ever needing a genuinely unauthenticated HTTP client or a real, unauthenticated request to exercise it.

**Contrast — the same anonymous token against a `permitAll` rule.** `rule.check.apply(ANONYMOUS)` for `"permitAll"` is the constant function `auth -> true`, which never even inspects the principal — every principal, anonymous or not, passes, correctly reflecting that a `permitAll()`-configured endpoint must remain reachable by literally anyone, including someone who never logged in at all.

```
@WithAnonymousUser -> AnonymousAuthenticationToken installed
        |
        v
authorizeHttpRequests rule evaluated:
   permitAll()          -> ALLOWED (anonymous token doesn't matter, everyone passes)
   authenticated()       -> DENIED (anonymous token explicitly fails this check)
   hasRole('ADMIN')      -> DENIED (fails both the authentication AND role requirement)
```

## 7. Gotchas & takeaways

> **Gotcha:** forgetting that a class-level `@WithMockUser` silently applies to *every* test method in the class means a test intended to verify anonymous-access behavior, if written without `@WithAnonymousUser`, will actually run as the class-default authenticated user — silently testing the wrong thing and potentially passing for the wrong reason (or worse, appearing to test the anonymous path while actually never exercising it at all). Always double-check that a test verifying unauthenticated behavior actually carries `@WithAnonymousUser` when a class-level default is in play.

- `@WithAnonymousUser` installs the exact same `AnonymousAuthenticationToken` a real, unauthenticated request would receive from `AnonymousAuthenticationFilter` — it is a faithful stand-in for "no login occurred," not a separate or approximate concept.
- It exists primarily to override a class-level `@WithMockUser` (or similar) default for the specific handful of test methods that need to verify unauthenticated behavior.
- The anonymous token correctly passes `permitAll()`-style rules while failing `authenticated()` and any role/authority-based rule — this consistency across rule types is what makes it a reliable tool for negative-path testing.
- Testing both the authenticated *and* anonymous paths for a protected endpoint (using `@WithMockUser` and `@WithAnonymousUser` respectively, often within the same test class) gives meaningfully more confidence than only ever testing the happy, authenticated path.
- Method-level annotation overriding a class-level one is standard JUnit/Spring Test precedence behavior — `@WithAnonymousUser` simply relies on that existing mechanism rather than introducing any special-case override logic of its own.
