---
card: spring-security
gi: 24
slug: default-security-auto-config-behavior
title: "Default security (auto-config) behavior"
---

## 1. What it is

With `spring-boot-starter-security` on the classpath and no custom `SecurityFilterChain` bean defined, Spring Boot's `SecurityAutoConfiguration` applies a deliberately strict default: every endpoint requires authentication, a form login page is auto-generated at `/login`, HTTP Basic authentication is also available, an in-memory `user` account is created with a randomly generated password (printed once to the application log at startup), and CSRF protection is enabled — a secure-by-default posture specifically designed so a freshly generated project is never accidentally left wide open.

```
Using generated security password: 8e557245-73e2-4286-969a-ff57fe326336

This generated password is for development use only. Your security configuration must be updated before running your application in production.
```

```java
// the moment ANY custom SecurityFilterChain bean is defined anywhere in the application,
// this entire default is stepped aside for -- there is no partial merge
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http.authorizeHttpRequests(auth -> auth.anyRequest().permitAll()); // now explicit, and intentional
    return http.build();
}
```

## 2. Why & when

Adding a security dependency to a project is a strong enough signal of intent that Boot treats "secure everything, generate a throwaway credential, print it loudly" as the only responsible default — the alternative (leaving new endpoints open until a developer remembers to configure security) would silently expose a real application in the common case where security configuration is added later than the dependency itself, or forgotten entirely during early development. The loud, one-time-generated password and its accompanying warning exist specifically to make the *default* state impossible to mistake for a *finished* configuration.

Reach for understanding this default when:

- A new Spring Boot project unexpectedly returns `401`/a login page for every endpoint immediately after adding the security starter — this is the default working exactly as designed, not a bug, and the fix is to define an explicit `SecurityFilterChain` bean matching the application's actual needs.
- Debugging "where did this password come from" — the generated password changes on every application restart (it is never persisted), so it cannot be relied upon beyond a single run and is never meant for anything beyond brief local testing.
- Understanding exactly what triggers the default to be replaced: any single `SecurityFilterChain` bean anywhere in the application context, even one configuring just a single path, causes the *entire* Boot default to step aside — there is no way to keep only part of the default while customizing the rest; the default is all-or-nothing.

## 3. Core concept

```
 spring-boot-starter-security on classpath?
   NO  -> no security auto-configuration at all
   YES -> continue

 does the application define its OWN SecurityFilterChain bean (anywhere)?
   NO  -> Boot's SecurityAutoConfiguration applies:
            - EVERY endpoint requires authentication
            - form login auto-configured at /login
            - HTTP Basic also available
            - one in-memory "user" account, RANDOM password printed to the log at startup
            - CSRF protection enabled
   YES -> Boot's default steps ASIDE ENTIRELY -- the application's own bean(s) are the ONLY configuration in effect
```

The default is a single, indivisible package — it cannot be selectively kept in part while a custom chain is added for the rest.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot checks whether a custom SecurityFilterChain bean is present if absent the fully strict auto configured default applies requiring authentication everywhere with a generated password if present the default steps aside entirely and only the custom bean's configuration is in effect">
  <rect x="15" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">custom SecurityFilterChain</text>
  <text x="100" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">bean defined?</text>

  <rect x="250" y="15" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="35" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">NO -&gt; Boot default applies</text>
  <text x="350" y="48" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">auth required everywhere</text>
  <text x="350" y="61" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">generated password, form login</text>

  <rect x="250" y="105" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="125" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">YES -&gt; default steps aside</text>
  <text x="350" y="138" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ONLY the custom bean's</text>
  <text x="350" y="151" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">configuration is in effect</text>

  <defs><marker id="a24" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="185" y1="80" x2="250" y2="45" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a24)"/>
  <line x1="185" y1="100" x2="250" y2="135" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a24)"/>
</svg>

The presence of a single custom bean is a hard, binary switch — there is no gradual dial between the default and a custom configuration.

## 5. Runnable example

The scenario: model Boot's bean-presence check and its all-or-nothing consequence directly. Start with the default applied when no custom bean exists, then add a custom bean and show the default disappearing entirely (including its generated-password behavior), then add a realistic startup log message generator matching Boot's real, distinctive console output.

### Level 1 — Basic

The default behavior: no custom bean present, so every request requires authentication against a randomly generated credential.

```java
import java.util.*;

public class DefaultSecurityLevel1 {
    record Request(String path, String username, String password) {}

    static String generatedPassword = UUID.randomUUID().toString(); // regenerated every "startup"

    static String bootDefaultChain(Request request) {
        if (request.username() == null) return "401 Unauthorized (default: authentication required)";
        if ("user".equals(request.username()) && generatedPassword.equals(request.password())) {
            return "200 OK, authenticated as 'user'";
        }
        return "401 Unauthorized (bad credentials)";
    }

    public static void main(String[] args) {
        System.out.println("Using generated security password: " + generatedPassword);
        System.out.println(bootDefaultChain(new Request("/anything", null, null)));
        System.out.println(bootDefaultChain(new Request("/anything", "user", generatedPassword)));
    }
}
```

How to run: `java DefaultSecurityLevel1.java`

`generatedPassword` is freshly created every run via `UUID.randomUUID()`, exactly mirroring Boot's real behavior of generating and logging a new password on every application startup; a request with no username is rejected outright, while one supplying `"user"` and the exact printed password succeeds.

### Level 2 — Intermediate

Add a custom `SecurityFilterChain`-style bean and show it fully replacing the default, including the generated-password mechanism disappearing entirely.

```java
import java.util.*;

public class DefaultSecurityLevel2 {
    record Request(String path, String username, String password) {}

    static String generatedPassword = UUID.randomUUID().toString();

    static String bootDefaultChain(Request request) {
        if (request.username() == null) return "401 Unauthorized (default: authentication required)";
        if ("user".equals(request.username()) && generatedPassword.equals(request.password())) return "200 OK (default user)";
        return "401 Unauthorized (bad credentials)";
    }

    // an application-defined bean; ITS PRESENCE ALONE disables bootDefaultChain entirely
    static String customChain(Request request) {
        if (request.path().equals("/public")) return "200 OK (public, no auth needed)";
        if (request.username() == null) return "401 Unauthorized (custom chain)";
        return "200 OK (custom chain), authenticated as " + request.username();
    }

    static String applicationHandle(Request request, boolean customBeanPresent) {
        // models Boot's actual bean-presence check
        return customBeanPresent ? customChain(request) : bootDefaultChain(request);
    }

    public static void main(String[] args) {
        Request publicRequest = new Request("/public", null, null);

        System.out.println("no custom bean: " + applicationHandle(publicRequest, false));
        System.out.println("with custom bean: " + applicationHandle(publicRequest, true));
        System.out.println("generated password still relevant with custom bean? "
                + "no -- bootDefaultChain (and generatedPassword) is never even consulted once a custom bean exists");
    }
}
```

How to run: `java DefaultSecurityLevel2.java`

With no custom bean, `/public` is rejected with `401` since `bootDefaultChain` has no concept of a public path at all; with a custom bean present, the exact same request succeeds, because `applicationHandle` routes to `customChain` instead — `bootDefaultChain` (and by extension, the generated password mechanism) is entirely bypassed, not merely overridden for this one path.

### Level 3 — Advanced

A realistic startup sequence: check for the security starter and a custom bean, generate and log the password only when actually needed, and produce Boot's real, distinctively worded console warning.

```java
import java.util.*;

public class DefaultSecurityLevel3 {
    record ApplicationContext(boolean securityStarterOnClasspath, boolean customFilterChainBeanDefined) {}

    static Optional<String> startUp(ApplicationContext context) {
        if (!context.securityStarterOnClasspath()) {
            System.out.println("(no security starter present -- no auto-configuration applied at all)");
            return Optional.empty();
        }
        if (context.customFilterChainBeanDefined()) {
            System.out.println("(custom SecurityFilterChain bean found -- Boot default security auto-configuration skipped)");
            return Optional.empty();
        }
        String generatedPassword = UUID.randomUUID().toString();
        System.out.println();
        System.out.println("Using generated security password: " + generatedPassword);
        System.out.println();
        System.out.println("This generated password is for development use only. "
                + "Your security configuration must be updated before running your application in production.");
        return Optional.of(generatedPassword);
    }

    public static void main(String[] args) {
        System.out.println("-- scenario 1: fresh project, no custom config --");
        Optional<String> password1 = startUp(new ApplicationContext(true, false));
        System.out.println("credential required for every request: " + password1.isPresent());

        System.out.println();
        System.out.println("-- scenario 2: custom SecurityFilterChain bean added --");
        Optional<String> password2 = startUp(new ApplicationContext(true, true));
        System.out.println("credential required for every request: " + password2.isPresent());
    }
}
```

How to run: `java DefaultSecurityLevel3.java`

Scenario 1 (no custom bean) generates and prints a fresh password every run, exactly like Boot's real startup log; scenario 2 (custom bean present) never even reaches the password-generation code at all — `startUp` returns early with `Optional.empty()`, printing the "skipped" message instead, confirming that the default's entire mechanism, not just its password requirement, is bypassed the moment a custom `SecurityFilterChain` bean exists anywhere in the application.

## 6. Walkthrough

Trace `startUp(new ApplicationContext(true, false))` from Level 3, scenario 1.

1. `startUp` first checks `context.securityStarterOnClasspath()`, which is `true`, so the early-return branch for "no starter present" is skipped.
2. Next it checks `context.customFilterChainBeanDefined()`, which is `false` for this scenario, so the "custom bean found, default skipped" branch is also skipped.
3. Control reaches the final block: `UUID.randomUUID().toString()` generates a fresh, random password string, assigned to `generatedPassword` — this value would be entirely different on the very next run of the program, since nothing seeds or persists it.
4. The method prints the blank line, the `"Using generated security password: ..."` line embedding the fresh UUID, another blank line, and the production warning — reproducing Boot's actual console output verbatim in wording and structure.
5. `startUp` returns `Optional.of(generatedPassword)`, and back in `main`, `password1.isPresent()` is `true`, printed as `"credential required for every request: true"` — signaling that, for this scenario, every subsequent request in the running application would need to present exactly this password (paired with username `"user"`) to be authenticated.
6. In scenario 2, step 2's check instead finds `customFilterChainBeanDefined()` to be `true`, so `startUp` returns immediately from that branch, printing the "skipped" message and returning `Optional.empty()` — the password-generation code in step 3 never executes at all for this run.

```
scenario 1 (no custom bean):  starter present -> no custom bean -> generate + log password -> Optional.of(password)
scenario 2 (custom bean set):  starter present -> custom bean FOUND -> default skipped entirely -> Optional.empty()
```

## 7. Gotchas & takeaways

> **Gotcha:** the generated default password changes on every single application restart and is never written anywhere durable — restarting the application (even without changing any code) invalidates whatever password was printed on the previous run, which is a common point of confusion when a developer tries to reuse a password copied from an earlier terminal session.

- Spring Boot's default security auto-configuration (require auth everywhere, generated password, form login, CSRF enabled) applies only when the security starter is present *and* no custom `SecurityFilterChain` bean has been defined anywhere in the application.
- The default is all-or-nothing: defining even one custom `SecurityFilterChain` bean, for even a single narrow path, disables the *entire* Boot default — there is no way to keep part of it while customizing the rest.
- The generated password is explicitly meant for brief local development use only, is regenerated on every restart, and is never suitable for any environment beyond a developer's own machine during initial setup.
- Seeing every endpoint suddenly require login immediately after adding `spring-boot-starter-security` to a project is the intended, secure-by-default behavior — the expected next step is always to define an explicit `SecurityFilterChain` bean matching the application's real requirements, not to search for a way to "turn off" this default in place.
