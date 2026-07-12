---
card: spring-security
gi: 133
slug: mockmvc-form-login-logout
title: "MockMvc form login / logout"
---

## 1. What it is

`SecurityMockMvcRequestBuilders.formLogin()` and `.logout()` are purpose-built `RequestBuilder`s that construct the exact `POST` request Spring Security's `UsernamePasswordAuthenticationFilter` and `LogoutFilter` expect — correct URL (`/login` by default), correct parameter names (`username`/`password` by default, both configurable if the application customizes them), and, critically, a valid CSRF token automatically included — letting a test exercise the *real* login/logout mechanism end to end, in contrast to card 0127's `@WithMockUser`, which bypasses it entirely.

```java
@Test
void loginWithValidCredentialsSucceeds() throws Exception {
    mockMvc.perform(formLogin().user("alice").password("secret123"))
           .andExpect(authenticated().withUsername("alice"));
}

@Test
void logoutClearsAuthentication() throws Exception {
    mockMvc.perform(formLogin().user("alice").password("secret123"));
    mockMvc.perform(logout())
           .andExpect(unauthenticated());
}
```

## 2. Why & when

Every earlier testing card in this section (`@WithMockUser`, `@WithUserDetails`) exists specifically to *skip* the login mechanism, letting a test focus on authorization logic without re-testing authentication machinery repeatedly. But that machinery — the login form's exact field names, the CSRF token requirement, the success/failure redirect behavior, the logout endpoint's session invalidation — is exactly what a *dedicated* test of the login/logout flow itself needs to exercise directly, and hand-building that `POST` request (correct path, correct parameter names, a manually-fetched CSRF token) in every such test would be tedious and easy to get subtly wrong. `formLogin()`/`logout()` exist to make testing the actual authentication mechanism itself as convenient as `@WithMockUser` makes bypassing it.

Reach for `formLogin()`/`logout()` when:

- Specifically testing the login endpoint's behavior — correct credentials succeed, incorrect ones fail with the expected response, account-status exceptions (card 0054) produce their specific failure paths.
- Verifying custom `AuthenticationSuccessHandler`/`AuthenticationFailureHandler` behavior (redirect URLs, response bodies) configured for a `formLogin()` DSL setup — this requires exercising the real filter, not a mock principal.
- Testing that logout genuinely clears authentication state (`SecurityContextHolder`, the session) and produces the expected post-logout behavior (redirect to a login page, session invalidation).
- The application customizes `formLogin()`'s default paths or parameter names (`.loginProcessingUrl(...)`, `.usernameParameter(...)`) — `formLogin()`'s own builder methods (`.loginProcessingUrl(...)`, `.user(paramName, value)`) mirror these customizations directly.

## 3. Core concept

```
formLogin() builds a request equivalent to:
    POST /login
    Content-Type: application/x-www-form-urlencoded

    username=alice&password=secret123&_csrf=<a VALID token, added AUTOMATICALLY>

Customization mirrors the application's own formLogin() DSL configuration:
    formLogin().loginProcessingUrl("/perform_login")   -- if the app customized this path
    formLogin().user("email", "alice@example.com")      -- if the app uses a different parameter name

logout() builds a request equivalent to:
    POST /logout
    Content-Type: application/x-www-form-urlencoded

    _csrf=<a VALID token>

BOTH builders exercise the REAL UsernamePasswordAuthenticationFilter / LogoutFilter --
this is genuinely DIFFERENT from @WithMockUser, which never invokes either filter at all.

Typical test flow for verifying logout:
  1. formLogin() first -- establishes a REAL authenticated session
  2. logout() next -- using the SAME MockMvc session, clears it
  3. assert unauthenticated() -- confirms the session's authentication state is genuinely gone
```

Because these builders exercise the genuine filters, a bug in a custom `AuthenticationSuccessHandler` or an incorrectly configured login URL will surface as a real test failure here — exactly the coverage `@WithMockUser`-based tests cannot provide, since they never touch this code path at all.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing formLogin building a real POST to slash login with username password and a valid csrf token dispatched through the actual UsernamePasswordAuthenticationFilter followed by logout building a real POST to slash logout through the actual LogoutFilter clearing the same session's authentication">
  <rect x="20" y="20" width="280" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="160" y="42" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">formLogin().user("alice").password(...)</text>
  <text x="160" y="60" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">POST /login, username, password, _csrf</text>
  <text x="160" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; REAL UsernamePasswordAuthenticationFilter</text>

  <line x1="300" y1="55" x2="340" y2="55" stroke="#6db33f" stroke-width="1.6" marker-end="url(#fl133)"/>

  <rect x="345" y="20" width="270" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="480" y="42" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SAME MockMvc session, now authenticated</text>
  <text x="480" y="60" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">logout() -&gt; POST /logout, _csrf</text>
  <text x="480" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">-&gt; REAL LogoutFilter</text>

  <line x1="480" y1="90" x2="480" y2="120" stroke="#f0883e" stroke-width="1.6" marker-end="url(#fl133b)"/>

  <rect x="345" y="122" width="270" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="480" y="146" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">unauthenticated() -- session cleared</text>

  <defs>
    <marker id="fl133" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="fl133b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

A real login establishes a real session state; a real logout, against that same session, is what genuinely proves it gets cleared.

## 5. Runnable example

The scenario: model `formLogin()`/`logout()` as request builders producing the exact request shape the real filters expect, growing from a single successful login into a failed-login case, then into a full login-then-logout sequence sharing session state, verifying logout genuinely clears what login established.

### Level 1 — Basic

Build and process a form-login request, mirroring `formLogin().user(...).password(...)`.

```java
import java.util.*;

public class FormLoginLevel1 {
    record LoginRequest(String path, String username, String password, boolean hasCsrfToken) {}
    record Authentication(String username, boolean authenticated) {}

    // mirrors SecurityMockMvcRequestBuilders.formLogin()
    static LoginRequest formLogin(String username, String password) {
        return new LoginRequest("/login", username, password, true); // CSRF token added automatically
    }

    // mirrors the REAL UsernamePasswordAuthenticationFilter
    static Authentication processLogin(LoginRequest request, Map<String, String> validCredentials) {
        if (!request.hasCsrfToken()) throw new IllegalStateException("Invalid CSRF Token");
        boolean valid = request.password().equals(validCredentials.get(request.username()));
        return valid ? new Authentication(request.username(), true) : new Authentication(null, false);
    }

    public static void main(String[] args) {
        Map<String, String> validCredentials = Map.of("alice", "secret123");

        LoginRequest request = formLogin("alice", "secret123");
        Authentication result = processLogin(request, validCredentials);

        System.out.println("authenticated: " + result.authenticated() + ", username: " + result.username());
    }
}
```

**How to run:** save as `FormLoginLevel1.java`, run `java FormLoginLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated: true, username: alice
```

`formLogin` mirrors `SecurityMockMvcRequestBuilders.formLogin()`: it builds a request targeting `/login` with the correct field names, and (unlike hand-rolling a request manually) always includes a valid CSRF token — `processLogin` mirrors the real filter checking credentials against the actual authentication mechanism.

### Level 2 — Intermediate

A failed login attempt, and verifying the CSRF requirement is genuinely enforced even for this builder-produced request.

```java
import java.util.*;

public class FormLoginLevel2 {
    record LoginRequest(String path, String username, String password, boolean hasCsrfToken) {}
    record Authentication(String username, boolean authenticated) {}

    static LoginRequest formLogin(String username, String password) {
        return new LoginRequest("/login", username, password, true);
    }

    static Authentication processLogin(LoginRequest request, Map<String, String> validCredentials) {
        if (!request.hasCsrfToken()) throw new IllegalStateException("Invalid CSRF Token");
        boolean valid = request.password().equals(validCredentials.get(request.username()));
        return valid ? new Authentication(request.username(), true) : new Authentication(null, false);
    }

    public static void main(String[] args) {
        Map<String, String> validCredentials = Map.of("alice", "secret123");

        LoginRequest wrongPasswordRequest = formLogin("alice", "WRONG-password");
        Authentication result = processLogin(wrongPasswordRequest, validCredentials);
        System.out.println("wrong password -> authenticated: " + result.authenticated());

        // simulate a request WITHOUT a csrf token (as if built by hand, incorrectly)
        LoginRequest noCsrfRequest = new LoginRequest("/login", "alice", "secret123", false);
        try {
            processLogin(noCsrfRequest, validCredentials);
        } catch (IllegalStateException e) {
            System.out.println("no csrf token -> REJECTED: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `FormLoginLevel2.java`, run `java FormLoginLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
wrong password -> authenticated: false
no csrf token -> REJECTED: Invalid CSRF Token
```

What changed: a wrong password correctly fails authentication (but doesn't throw — mirroring the real filter's graceful failure handling), while a request deliberately missing the CSRF token (as a hand-built request might, if a developer forgot to add one manually) is rejected outright — this is precisely why `formLogin()`'s automatic CSRF inclusion is valuable: it removes an entire category of test-authoring mistakes that would otherwise produce confusing `403`s unrelated to the actual authentication logic under test.

### Level 3 — Advanced

A full login-then-logout sequence sharing session state, verifying logout genuinely clears what a real login established — the scenario card 0133's core concept section describes as the typical test flow.

```java
import java.util.*;

public class FormLoginLevel3 {
    record LoginRequest(String path, String username, String password, boolean hasCsrfToken) {}
    record LogoutRequest(String path, boolean hasCsrfToken) {}
    record Authentication(String username, boolean authenticated) {}

    // stands in for MockMvc's session-carrying behavior across multiple .perform(...) calls
    static class MockMvcSession {
        Authentication currentAuthentication;
    }

    static LoginRequest formLogin(String username, String password) {
        return new LoginRequest("/login", username, password, true);
    }
    static LogoutRequest logout() { return new LogoutRequest("/logout", true); }

    static void processLogin(MockMvcSession session, LoginRequest request, Map<String, String> validCredentials) {
        if (!request.hasCsrfToken()) throw new IllegalStateException("Invalid CSRF Token");
        boolean valid = request.password().equals(validCredentials.get(request.username()));
        session.currentAuthentication = valid ? new Authentication(request.username(), true) : null;
    }

    // mirrors the REAL LogoutFilter -- clears the session's authentication entirely
    static void processLogout(MockMvcSession session, LogoutRequest request) {
        if (!request.hasCsrfToken()) throw new IllegalStateException("Invalid CSRF Token");
        session.currentAuthentication = null;
    }

    static boolean isAuthenticated(MockMvcSession session) {
        return session.currentAuthentication != null && session.currentAuthentication.authenticated();
    }

    public static void main(String[] args) {
        Map<String, String> validCredentials = Map.of("alice", "secret123");
        MockMvcSession session = new MockMvcSession();

        // step 1: formLogin() establishes a REAL authenticated session
        processLogin(session, formLogin("alice", "secret123"), validCredentials);
        System.out.println("after login, authenticated: " + isAuthenticated(session)
                + " as " + (session.currentAuthentication != null ? session.currentAuthentication.username() : "none"));

        // step 2: logout(), using the SAME session, clears it
        processLogout(session, logout());
        System.out.println("after logout, authenticated: " + isAuthenticated(session));
    }
}
```

**How to run:** save as `FormLoginLevel3.java`, run `java FormLoginLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
after login, authenticated: true as alice
after logout, authenticated: false
```

What changed: `MockMvcSession` now carries state across both the `formLogin()` and `logout()` calls, mirroring how a real `MockMvc` instance preserves session state between separate `.perform(...)` invocations within the same test — the login genuinely establishes an authenticated session (not a mocked one), and the subsequent logout genuinely clears it, giving real end-to-end confidence in both mechanisms working correctly together.

## 6. Walkthrough

Trace the full login-then-logout sequence from Level 3, mapped to a real MockMvc test.

**Step 1 — the real test code:**
```java
@Test
void logoutClearsRealSession() throws Exception {
    MvcResult loginResult = mockMvc.perform(formLogin().user("alice").password("secret123"))
                                   .andExpect(authenticated().withUsername("alice"))
                                   .andReturn();

    mockMvc.perform(logout().session((MockHttpSession) loginResult.getRequest().getSession()))
           .andExpect(unauthenticated());
}
```

**Step 2 — `formLogin()` builds the login request.** This corresponds to `formLogin("alice", "secret123")`, producing a `POST /login` request with `username`, `password`, and a valid, automatically-included CSRF token.

**Step 3 — the request is dispatched through the real `UsernamePasswordAuthenticationFilter`.** Corresponding to `processLogin(session, ..., validCredentials)`: the CSRF check passes, the credentials are checked and found valid, and `session.currentAuthentication` is set to `Authentication("alice", true)`.

**Step 4 — the first assertion passes.** `authenticated().withUsername("alice")` confirms the session is genuinely authenticated as alice — corresponding to `isAuthenticated(session)` returning `true` in Level 3's code.

**Step 5 — `logout()` builds the logout request, targeting the *same* session.** Corresponding to `logout()` producing a `POST /logout` request, and critically, being processed against the *same* `MockMvcSession` object that `formLogin()` had just authenticated.

**Step 6 — the request is dispatched through the real `LogoutFilter`.** Corresponding to `processLogout(session, ...)`: the CSRF check passes, and `session.currentAuthentication` is set to `null`, clearing the previously-established authentication entirely.

**Step 7 — the final assertion passes.** `unauthenticated()` confirms the session's authentication state is genuinely gone — corresponding to `isAuthenticated(session)` now returning `false`.

```
formLogin("alice", "secret123") -> POST /login, valid CSRF -> credentials checked -> session.auth = Authentication(alice, true)
        |
        v (assert authenticated().withUsername("alice") -- PASSES)
        |
        v
logout() -> POST /logout, valid CSRF, SAME session -> session.auth = null
        |
        v (assert unauthenticated() -- PASSES)
```

## 7. Gotchas & takeaways

> **Gotcha:** `logout()` must operate against the *same* session that `formLogin()` established for the test to meaningfully verify anything — issuing `logout()` against a fresh, never-authenticated `MockMvc` request would trivially "succeed" at being unauthenticated, since there was never anything to clear in the first place. Always carry the session (or use whatever session-continuity mechanism `MockMvc` provides) between the login and logout calls in the same test.

- `formLogin()`/`logout()` exercise the *real* `UsernamePasswordAuthenticationFilter`/`LogoutFilter`, in contrast to `@WithMockUser`'s complete bypass of both — this makes them the right tool specifically for testing the login/logout mechanism itself, not for testing authorization logic that merely needs *some* authenticated principal.
- These builders automatically include a valid CSRF token, removing an entire category of test-authoring mistakes a hand-built request would be prone to.
- A genuine end-to-end logout test requires first establishing a real, authenticated session via `formLogin()`, then issuing `logout()` against that *same* session — testing logout in isolation, without a prior real login, doesn't meaningfully verify the clearing behavior.
- `formLogin()`'s builder methods (`.loginProcessingUrl(...)`, custom parameter names) mirror whatever customizations the application's own `formLogin()` DSL configuration applies, keeping the test aligned with the actual production configuration.
- Combine these builders with `authenticated()`/`unauthenticated()` (card 0132) for the most precise assertions — verifying not just the HTTP response but the actual, resulting security state after each step.
