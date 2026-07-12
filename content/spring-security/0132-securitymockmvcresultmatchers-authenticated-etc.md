---
card: spring-security
gi: 132
slug: securitymockmvcresultmatchers-authenticated-etc
title: "SecurityMockMvcResultMatchers (authenticated, etc.)"
---

## 1. What it is

`SecurityMockMvcResultMatchers` is the assertion-side counterpart to card 0131's request-building post-processors: rather than asserting only on the HTTP response (`status()`, `content()`, `header()`, all of which `MockMvc` already supports natively), its `authenticated()` matcher inspects the `SecurityContext` that ended up populated *as a result of* processing the request — verifying not just that a response looked correct, but that the actual authentication outcome was what the test expected: who got authenticated, with which authorities, or that authentication was correctly denied.

```java
@Test
void formLoginWithCorrectCredentialsAuthenticatesAsAlice() throws Exception {
    mockMvc.perform(formLogin().user("alice").password("secret123"))
           .andExpect(authenticated().withUsername("alice").withRoles("USER"));
}

@Test
void formLoginWithWrongPasswordIsNotAuthenticated() throws Exception {
    mockMvc.perform(formLogin().user("alice").password("WRONG"))
           .andExpect(unauthenticated());
}
```

## 2. Why & when

A response's HTTP status alone can be an incomplete signal for security-related behavior — a `302 Found` redirect after a login attempt could mean "login succeeded, redirecting to the dashboard" or "login failed, redirecting back to the login page with an error," and asserting only on the status code (or even the redirect URL) leaves a test unable to distinguish these clearly, or to verify *which* principal actually ended up authenticated. `authenticated()`/`unauthenticated()` matchers give a test direct access to the actual post-request `SecurityContext`, letting assertions target the authentication *outcome* itself rather than inferring it indirectly from response artifacts that might coincidentally look similar across both success and failure.

Reach for `SecurityMockMvcResultMatchers` when:

- Testing a login endpoint (form-based, or any custom authentication filter) and needing to verify not just "the response looked like success" but specifically who got authenticated and with what authorities.
- Distinguishing a legitimate authentication failure from some other unrelated failure that happens to produce a similar-looking response — asserting `unauthenticated()` is a direct, unambiguous check rather than an inference from a status code or redirect location.
- Verifying that a specific authentication mechanism (OAuth2 login, SAML, LDAP bind) resulted in the expected principal type and attributes, as a more precise complement to checking the eventual HTTP response.

## 3. Core concept

```
mockMvc.perform(...) executes a simulated request through the REAL security filter chain --
the SAME chain a genuine request would traverse.

authenticated() (a ResultMatcher):
    inspects SecurityContextHolder AFTER the request has been processed
    verifies an Authentication IS present and IS authenticated
    .withUsername("alice")   -- further asserts the principal's name specifically
    .withRoles("USER")       -- further asserts the authorities granted
    .withAuthentication(matcher) -- fully custom assertion against the Authentication object

unauthenticated() (a ResultMatcher):
    verifies NO valid Authentication resulted from processing this request --
    either SecurityContextHolder is empty, or holds an anonymous/unauthenticated token

This differs from asserting purely on the HTTP RESPONSE:
    status()/header()/redirectedUrl() -- describe what the CLIENT would observe
    authenticated()/unauthenticated() -- describe the SERVER-SIDE security OUTCOME directly,
                                          which may be a more precise or unambiguous signal
                                          for exactly what a given test cares about verifying
```

Both kinds of assertions can (and often should) be combined on the same test — response-shape assertions for what a real client would see, authentication-outcome assertions for what actually happened server-side.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a mock request processed through the real security filter chain producing both an http response that ordinary result matchers check and a resulting security context that the authenticated and unauthenticated matchers check directly">
  <rect x="20" y="70" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="90" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">mockMvc.perform(formLogin())</text>
  <text x="110" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">real security filter chain</text>

  <line x1="200" y1="80" x2="250" y2="45" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rm132)"/>
  <line x1="200" y1="100" x2="250" y2="135" stroke="#f0883e" stroke-width="1.5" marker-end="url(#rm132b)"/>

  <rect x="255" y="18" width="200" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="355" y="38" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">HTTP response</text>
  <text x="355" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">status(), header(), redirectedUrl()</text>

  <rect x="255" y="112" width="200" height="60" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.4"/>
  <text x="355" y="132" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">resulting SecurityContext</text>
  <text x="355" y="148" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">authenticated().withUsername(...)</text>
  <text x="355" y="162" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">unauthenticated()</text>

  <defs>
    <marker id="rm132" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rm132b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

One processed request, two independently checkable outcomes: what the client would see, and what actually got authenticated server-side.

## 5. Runnable example

The scenario: model a simulated login attempt producing both an HTTP-response-like result and a resulting security context, growing from a single successful-login assertion into a failed-login case, then into a scenario demonstrating why checking the authentication outcome directly catches a bug a response-only assertion would miss.

### Level 1 — Basic

A successful login, asserting on the resulting authentication directly.

```java
import java.util.*;

public class ResultMatchersLevel1 {
    record Authentication(String username, Set<String> authorities, boolean authenticated) {}
    record MockResult(int status, Authentication resultingAuthentication) {}

    static MockResult performFormLogin(String username, String password, Map<String, String> validCredentials) {
        boolean valid = password.equals(validCredentials.get(username));
        if (valid) {
            return new MockResult(302, new Authentication(username, Set.of("ROLE_USER"), true));
        }
        return new MockResult(302, null); // ALSO a 302 -- but NO resulting authentication
    }

    // mirrors authenticated().withUsername(...).withRoles(...)
    static void assertAuthenticated(MockResult result, String expectedUsername, String expectedRole) {
        if (result.resultingAuthentication() == null || !result.resultingAuthentication().authenticated()) {
            throw new AssertionError("expected an authenticated result, but none was present");
        }
        if (!expectedUsername.equals(result.resultingAuthentication().username())) {
            throw new AssertionError("expected username " + expectedUsername + " but got " + result.resultingAuthentication().username());
        }
        if (!result.resultingAuthentication().authorities().contains("ROLE_" + expectedRole)) {
            throw new AssertionError("expected role " + expectedRole + " but authorities were " + result.resultingAuthentication().authorities());
        }
    }

    public static void main(String[] args) {
        Map<String, String> validCredentials = Map.of("alice", "secret123");

        MockResult result = performFormLogin("alice", "secret123", validCredentials);
        assertAuthenticated(result, "alice", "USER");
        System.out.println("assertion passed: authenticated as alice with ROLE_USER");
    }
}
```

**How to run:** save as `ResultMatchersLevel1.java`, run `java ResultMatchersLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
assertion passed: authenticated as alice with ROLE_USER
```

`assertAuthenticated` mirrors `authenticated().withUsername(...).withRoles(...)`: rather than inferring success from the `302` status alone (which both the success and failure paths in `performFormLogin` produce), it directly inspects the resulting `Authentication` object for the specific username and role expected.

### Level 2 — Intermediate

A failed login, asserting `unauthenticated()`, and demonstrating that both outcomes share the same HTTP status.

```java
import java.util.*;

public class ResultMatchersLevel2 {
    record Authentication(String username, Set<String> authorities, boolean authenticated) {}
    record MockResult(int status, Authentication resultingAuthentication) {}

    static MockResult performFormLogin(String username, String password, Map<String, String> validCredentials) {
        boolean valid = password.equals(validCredentials.get(username));
        if (valid) return new MockResult(302, new Authentication(username, Set.of("ROLE_USER"), true));
        return new MockResult(302, null); // SAME status as success
    }

    static void assertAuthenticated(MockResult result, String expectedUsername) {
        if (result.resultingAuthentication() == null) throw new AssertionError("expected authenticated, was not");
        if (!expectedUsername.equals(result.resultingAuthentication().username())) throw new AssertionError("wrong username");
    }

    static void assertUnauthenticated(MockResult result) {
        if (result.resultingAuthentication() != null && result.resultingAuthentication().authenticated()) {
            throw new AssertionError("expected unauthenticated, but a valid Authentication was present");
        }
    }

    public static void main(String[] args) {
        Map<String, String> validCredentials = Map.of("alice", "secret123");

        MockResult successResult = performFormLogin("alice", "secret123", validCredentials);
        MockResult failureResult = performFormLogin("alice", "WRONG-password", validCredentials);

        System.out.println("success case status: " + successResult.status() + " (identical to failure case's status)");
        System.out.println("failure case status: " + failureResult.status());

        assertAuthenticated(successResult, "alice");
        System.out.println("success case: correctly asserted authenticated");

        assertUnauthenticated(failureResult);
        System.out.println("failure case: correctly asserted UNauthenticated, DESPITE the identical status code");
    }
}
```

**How to run:** save as `ResultMatchersLevel2.java`, run `java ResultMatchersLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
success case status: 302 (identical to failure case's status)
failure case status: 302
success case: correctly asserted authenticated
failure case: correctly asserted UNauthenticated, DESPITE the identical status code
```

What changed: both the successful and failed login attempts produce the exact same `302` status, yet `assertAuthenticated`/`assertUnauthenticated` correctly distinguish the two by inspecting the resulting `Authentication` object directly — proving that the HTTP status alone is an ambiguous signal here, while the security-context-based assertion is not.

### Level 3 — Advanced

A scenario demonstrating why checking the resulting authentication directly matters: a buggy custom authentication filter that redirects to the success URL (a `302`) even when authentication actually failed — a response-only assertion would be fooled, while `unauthenticated()` catches it.

```java
import java.util.*;

public class ResultMatchersLevel3 {
    record Authentication(String username, Set<String> authorities, boolean authenticated) {}
    record MockResult(int status, String redirectLocation, Authentication resultingAuthentication) {}

    // a DELIBERATELY BUGGY filter: redirects to "success" REGARDLESS of whether auth actually succeeded
    static MockResult performBuggyLogin(String username, String password, Map<String, String> validCredentials) {
        boolean valid = password.equals(validCredentials.get(username));
        Authentication resultingAuth = valid ? new Authentication(username, Set.of("ROLE_USER"), true) : null;
        // BUG: always redirects to "/dashboard" regardless of `valid`
        return new MockResult(302, "/dashboard", resultingAuth);
    }

    static void assertRedirectedTo(MockResult result, String expectedLocation) {
        if (!expectedLocation.equals(result.redirectLocation())) {
            throw new AssertionError("wrong redirect location");
        }
    }

    static void assertAuthenticated(MockResult result) {
        if (result.resultingAuthentication() == null || !result.resultingAuthentication().authenticated()) {
            throw new AssertionError("expected authenticated, but no valid Authentication resulted from this request");
        }
    }

    public static void main(String[] args) {
        Map<String, String> validCredentials = Map.of("alice", "secret123");

        MockResult wrongPasswordResult = performBuggyLogin("alice", "WRONG-password", validCredentials);

        // a WEAK test, checking ONLY the response shape -- this test would INCORRECTLY PASS
        try {
            assertRedirectedTo(wrongPasswordResult, "/dashboard");
            System.out.println("response-only assertion: PASSED (misleadingly -- the bug went undetected)");
        } catch (AssertionError e) {
            System.out.println("response-only assertion: FAILED -- " + e.getMessage());
        }

        // a STRONGER test, checking the actual authentication outcome -- this CORRECTLY catches the bug
        try {
            assertAuthenticated(wrongPasswordResult);
            System.out.println("authenticated() assertion: PASSED (should not happen)");
        } catch (AssertionError e) {
            System.out.println("authenticated() assertion: FAILED (correctly) -- " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ResultMatchersLevel3.java`, run `java ResultMatchersLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
response-only assertion: PASSED (misleadingly -- the bug went undetected)
authenticated() assertion: FAILED (correctly) -- expected authenticated, but no valid Authentication resulted from this request
```

What changed: `performBuggyLogin` models a genuinely buggy authentication filter that redirects to the success page regardless of whether the password actually matched — a test asserting only on the redirect location would pass despite the bug, while `assertAuthenticated` (mirroring `authenticated()`) correctly fails, since it inspects the actual `Authentication` outcome rather than trusting the response shape as a proxy for it. This is the concrete argument for preferring `authenticated()`/`unauthenticated()` assertions specifically for verifying authentication behavior, rather than relying solely on HTTP response characteristics that a bug could coincidentally still produce correctly.

## 6. Walkthrough

Trace the buggy-login scenario from Level 3 end to end, contrasting both assertion styles.

**Step 1 — a request with a wrong password is submitted:**
```
POST /login HTTP/1.1

username=alice&password=WRONG-password
```

**Step 2 — the (buggy) authentication filter processes it.** It correctly determines the password is wrong (`valid = false`), correctly leaves `resultingAuth` as `null` — but then, due to the bug, always redirects to `/dashboard` regardless: `return new MockResult(302, "/dashboard", null)`.

**Step 3 — a response-only test assertion runs.** `assertRedirectedTo(wrongPasswordResult, "/dashboard")` checks only `redirectLocation`, which is indeed `/dashboard` — the assertion passes, giving false confidence that the login behaved correctly.

**Step 4 — an `authenticated()`-style assertion runs on the *same* result.** `assertAuthenticated(wrongPasswordResult)` checks `resultingAuthentication()`, which is `null` — the assertion correctly throws, revealing that despite the response looking like a success, no valid authentication actually resulted from this request.

**Step 5 — in a real Spring Security test**, this corresponds precisely to:
```java
mockMvc.perform(formLogin().user("alice").password("WRONG-password"))
       .andExpect(redirectedUrl("/dashboard"))  // would PASS despite the bug
       .andExpect(unauthenticated());            // would FAIL, correctly catching the bug
```
The second expectation is what actually catches a defect the first alone would miss entirely.

```
buggy filter: wrong password -> resultingAuth = null, BUT redirect = "/dashboard" (BUG: should redirect elsewhere)
        |
        +-- redirectedUrl("/dashboard") check -> PASSES (misleading)
        |
        +-- unauthenticated() check            -> FAILS (correctly exposes the bug)
```

## 7. Gotchas & takeaways

> **Gotcha:** relying solely on HTTP response characteristics (status code, redirect location) to verify authentication success or failure assumes the application's response-generation logic and its actual authentication decision are always consistent with each other — a bug that decouples the two (as in Level 3) will not be caught by response-only assertions. Pairing response assertions with `authenticated()`/`unauthenticated()` closes this gap by checking the authoritative source (the resulting `SecurityContext`) directly.

- `authenticated()`/`unauthenticated()` inspect the actual post-request `SecurityContext`, giving a direct, unambiguous signal about authentication outcome rather than inferring it from response shape.
- `authenticated().withUsername(...).withRoles(...)` lets a test assert precisely which principal and authorities resulted from processing a request, useful for verifying complex authentication flows produce exactly the expected identity.
- A response that "looks like" success (a redirect to a dashboard, a `200 OK`) can, in the presence of a bug, occur even when authentication genuinely failed — response-only assertions cannot distinguish this from a correct success.
- Combining response-shape assertions (what a real client observes) with authentication-outcome assertions (what the server actually decided) gives meaningfully stronger test coverage than either alone.
- This matcher operates on the real `SecurityContext` produced by dispatching the request through the actual security filter chain — it is not a mock or stand-in, but a genuine inspection of what really happened during that simulated request's processing.
