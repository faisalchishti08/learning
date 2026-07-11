---
card: spring-security
gi: 26
slug: form-login
title: "Form login"
---

## 1. What it is

Form login is Spring Security's built-in username/password authentication mechanism for browser-based applications: `http.formLogin(Customizer.withDefaults())` auto-generates a login page at `/login`, registers `UsernamePasswordAuthenticationFilter` to intercept `POST /login` submissions (reading `username`/`password` request parameters by default), and wires up redirect-based success and failure handling — a successful login redirects to the originally requested page (or a configured default), and a failed attempt redirects back to `/login?error`.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth.anyRequest().authenticated())
        .formLogin(form -> form
            .loginPage("/custom-login")
            .defaultSuccessUrl("/dashboard", true)
            .failureUrl("/custom-login?error"));
    return http.build();
}
```

## 2. Why & when

Nearly every server-rendered web application needs the same login mechanics — an HTML form, a `POST` handler that reads submitted credentials, a redirect on success back to where the user was headed, a redirect on failure back to the form with an error indicator — and reimplementing this from scratch for every application would be pure repetition of well-understood, security-sensitive logic. `formLogin` provides this entire mechanism out of the box, built on `UsernamePasswordAuthenticationFilter` (itself an `AbstractAuthenticationProcessingFilter` subclass, from the earlier card), configurable enough to swap in a custom login page, custom success/failure destinations, or custom parameter names without needing to write a new filter at all.

Reach for `formLogin` when:

- Building a traditional server-rendered application where a human enters credentials through an HTML form — this is the most natural fit and requires the least configuration.
- A custom login page template is needed (`loginPage("/custom-login")`) — note that when a custom login page is configured, the application itself is responsible for rendering it and must also `permitAll()` that path, since a login page must be reachable by definition-unauthenticated users.
- `defaultSuccessUrl(url, alwaysUse)` when the redirect-to-originally-requested-page behavior isn't wanted — passing `true` for `alwaysUse` forces every successful login to that URL, ignoring whatever page originally triggered the redirect to login.

## 3. Core concept

```
 unauthenticated GET /account
        |
        v
 redirected to GET /login (the login page, rendered)
        |
        v
 user submits POST /login  (username=alice&password=hunter2)
        |
        v
 UsernamePasswordAuthenticationFilter.attemptAuthentication()
   reads "username"/"password" request parameters
   builds UsernamePasswordAuthenticationToken(unverified)
   delegates to AuthenticationManager (-> ProviderManager -> DaoAuthenticationProvider)
        |
        +-- SUCCESS --> AuthenticationSuccessHandler
        |                 redirect to /account (the ORIGINALLY requested page, saved earlier)
        +-- FAILURE --> AuthenticationFailureHandler
                          redirect to /login?error
```

The original destination (`/account`) is remembered across the redirect-to-login round trip via a saved request (the final card in this section).

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unauthenticated request to a protected page redirects to the login page the user submits credentials via POST to slash login UsernamePasswordAuthenticationFilter verifies them and either redirects to the originally requested page on success or back to the login page with an error on failure">
  <rect x="15" y="65" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="85" y="85" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">GET /account</text>
  <text x="85" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(unauthenticated)</text>

  <rect x="220" y="65" width="140" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="290" y="85" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">POST /login</text>
  <text x="290" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">username + password</text>

  <rect x="440" y="20" width="170" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="44" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">success -&gt; /account</text>

  <rect x="440" y="120" width="170" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="525" y="144" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">failure -&gt; /login?error</text>

  <defs><marker id="a26" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="85" x2="220" y2="85" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a26)"/>
  <line x1="360" y1="78" x2="440" y2="42" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a26)"/>
  <line x1="360" y1="95" x2="440" y2="135" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a26)"/>
</svg>

The saved original destination (`/account`) is what makes the success redirect land back where the user actually intended to go.

## 5. Runnable example

The scenario: model form login's request-handling logic end to end — deciding whether a request is the login POST, verifying credentials, and picking a redirect target. Start with a bare success/failure decision, then add the saved-request redirect behavior, then add `defaultSuccessUrl(url, alwaysUse=true)` as a genuinely different redirect policy.

### Level 1 — Basic

A minimal form login handler: verify submitted credentials, redirect on success or failure.

```java
import java.util.*;

public class FormLoginLevel1 {
    record LoginAttempt(String username, String password) {}
    static Map<String, String> validCredentials = Map.of("alice", "hunter2");

    static String handleLoginSubmission(LoginAttempt attempt) {
        String storedPassword = validCredentials.get(attempt.username());
        if (storedPassword != null && storedPassword.equals(attempt.password())) {
            return "302 Found -> Location: /"; // default success destination
        }
        return "302 Found -> Location: /login?error";
    }

    public static void main(String[] args) {
        System.out.println(handleLoginSubmission(new LoginAttempt("alice", "hunter2")));
        System.out.println(handleLoginSubmission(new LoginAttempt("alice", "wrongpass")));
    }
}
```

How to run: `java FormLoginLevel1.java`

A correct username/password pair redirects to `/`; any mismatch redirects back to `/login?error` — the simplest possible model of `UsernamePasswordAuthenticationFilter`'s success/failure branching.

### Level 2 — Intermediate

Add saved-request tracking, so a successful login redirects back to whatever page originally triggered the login flow, not always to `/`.

```java
import java.util.*;

public class FormLoginLevel2 {
    record LoginAttempt(String username, String password, String sessionId) {}
    static Map<String, String> validCredentials = Map.of("alice", "hunter2");
    static Map<String, String> savedRequests = new HashMap<>(); // sessionId -> originally requested URL

    static String requestProtectedPage(String sessionId, String path) {
        savedRequests.put(sessionId, path); // remember where the user was headed
        return "302 Found -> Location: /login (redirect to login, original destination saved)";
    }

    static String handleLoginSubmission(LoginAttempt attempt) {
        String storedPassword = validCredentials.get(attempt.username());
        if (storedPassword != null && storedPassword.equals(attempt.password())) {
            String originalDestination = savedRequests.remove(attempt.sessionId());
            String target = (originalDestination != null) ? originalDestination : "/"; // fall back if nothing was saved
            return "302 Found -> Location: " + target;
        }
        return "302 Found -> Location: /login?error";
    }

    public static void main(String[] args) {
        String sessionId = "JSESSIONID-abc123";
        System.out.println(requestProtectedPage(sessionId, "/account/settings"));
        System.out.println(handleLoginSubmission(new LoginAttempt("alice", "hunter2", sessionId)));

        // a second login, with NOTHING saved for this session -- falls back to "/"
        System.out.println(handleLoginSubmission(new LoginAttempt("alice", "hunter2", "brand-new-session")));
    }
}
```

How to run: `java FormLoginLevel2.java`

`requestProtectedPage` records `"/account/settings"` under the session ID before redirecting to login; the subsequent successful login for that *same* session correctly redirects back to `/account/settings`, while a login for a session with no saved request falls back to the default `/`.

### Level 3 — Advanced

Add `defaultSuccessUrl(url, alwaysUse=true)`-style behavior: a configured flag that, when set, *always* redirects to a fixed URL after login, deliberately ignoring any saved request — a genuinely different policy from Level 2's behavior.

```java
import java.util.*;

public class FormLoginLevel3 {
    record LoginAttempt(String username, String password, String sessionId) {}

    static class FormLoginConfig {
        Map<String, String> validCredentials = Map.of("alice", "hunter2", "bob", "letmein");
        Map<String, String> savedRequests = new HashMap<>();
        String defaultSuccessUrl = "/";
        boolean alwaysUseDefaultSuccessUrl = false;

        String requestProtectedPage(String sessionId, String path) {
            savedRequests.put(sessionId, path);
            return "302 Found -> Location: /login";
        }

        String handleLoginSubmission(LoginAttempt attempt) {
            String storedPassword = validCredentials.get(attempt.username());
            if (storedPassword == null || !storedPassword.equals(attempt.password())) {
                return "302 Found -> Location: /login?error";
            }
            String originalDestination = savedRequests.remove(attempt.sessionId());
            String target;
            if (alwaysUseDefaultSuccessUrl) {
                target = defaultSuccessUrl; // IGNORES originalDestination entirely, even if one was saved
            } else {
                target = (originalDestination != null) ? originalDestination : defaultSuccessUrl;
            }
            return "302 Found -> Location: " + target;
        }
    }

    public static void main(String[] args) {
        FormLoginConfig config = new FormLoginConfig();
        config.defaultSuccessUrl = "/dashboard";
        config.alwaysUseDefaultSuccessUrl = true; // models defaultSuccessUrl("/dashboard", true)

        String sessionId = "JSESSIONID-xyz789";
        System.out.println(config.requestProtectedPage(sessionId, "/account/settings"));
        System.out.println("login (alwaysUse=true, saved request IGNORED): "
                + config.handleLoginSubmission(new LoginAttempt("alice", "hunter2", sessionId)));

        config.alwaysUseDefaultSuccessUrl = false; // models defaultSuccessUrl("/dashboard", false) -- the default
        config.requestProtectedPage("session2", "/orders/42");
        System.out.println("login (alwaysUse=false, saved request HONORED): "
                + config.handleLoginSubmission(new LoginAttempt("bob", "letmein", "session2")));
    }
}
```

How to run: `java FormLoginLevel3.java`

With `alwaysUseDefaultSuccessUrl = true`, alice's login redirects to `/dashboard` even though `/account/settings` was saved for her session — the saved request is discarded (via `.remove`) but never consulted; with the flag `false`, bob's login correctly honors his saved `/orders/42` destination instead, exactly matching the real difference between `defaultSuccessUrl("/dashboard")` (honors saved requests) and `defaultSuccessUrl("/dashboard", true)` (always overrides them).

## 6. Walkthrough

Trace the full sequence for alice in Level 3.

1. `config.requestProtectedPage(sessionId, "/account/settings")` runs first, storing `savedRequests.put("JSESSIONID-xyz789", "/account/settings")` and returning the redirect-to-login message — this models a request to a protected page triggering `ExceptionTranslationFilter`'s `AuthenticationEntryPoint` (from two cards back in this section), which saves the request before redirecting.
2. `config.handleLoginSubmission(new LoginAttempt("alice", "hunter2", sessionId))` runs next: `validCredentials.get("alice")` returns `"hunter2"`, which equals `attempt.password()`, so the credential check passes.
3. `savedRequests.remove(attempt.sessionId())` is called, retrieving *and deleting* the entry for `"JSESSIONID-xyz789"` — it returns `"/account/settings"`, assigned to `originalDestination`.
4. Because `config.alwaysUseDefaultSuccessUrl` is `true`, the `if` branch runs regardless of what `originalDestination` holds: `target` is set to `config.defaultSuccessUrl`, which is `"/dashboard"` — `originalDestination`'s value is computed and then never used.
5. The method returns `"302 Found -> Location: /dashboard"` — even though the user's actual intent was to reach `/account/settings`, the configured `alwaysUse=true` policy takes precedence, which is precisely the documented, deliberate behavior of `defaultSuccessUrl(url, true)` in real Spring Security applications, typically chosen when every login should land on a consistent landing page (like a dashboard) regardless of what triggered it.

```
requestProtectedPage(session, "/account/settings")  -> saved, redirect to /login
handleLoginSubmission(alice, correct password)        -> credentials OK
  originalDestination = "/account/settings" (retrieved, but...)
  alwaysUseDefaultSuccessUrl = true -> IGNORE originalDestination -> target = "/dashboard"
-> 302 Found -> Location: /dashboard
```

## 7. Gotchas & takeaways

> **Gotcha:** configuring a custom `loginPage(...)` without also explicitly `permitAll()`-ing that same path is a common mistake — the custom login page itself becomes a protected resource requiring authentication, producing an infinite redirect loop (redirected to the login page, which itself redirects back to the login page, since it too now requires authentication).

- Form login's default behavior (no custom `loginPage`) is convenient for prototyping, but production applications typically configure a custom login page matching the application's own look and templates.
- The saved-request mechanism (remembering the originally requested URL across the redirect-to-login round trip) is what makes a successful login feel seamless — landing the user back where they meant to go, not always at a fixed default page.
- `defaultSuccessUrl(url, true)` deliberately overrides this saved-request behavior, always redirecting to the same fixed URL after any successful login — useful when a consistent post-login landing page matters more than preserving the original destination.
- `failureUrl` (or the default `/login?error`) is where a failed attempt redirects to; the application's login page template is responsible for checking for the `error` query parameter and displaying an appropriate message.
