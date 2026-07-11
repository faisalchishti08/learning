---
card: spring-security
gi: 18
slug: securityfilterchain-bean-lambda-dsl
title: "SecurityFilterChain bean (lambda DSL)"
---

## 1. What it is

The lambda DSL is the modern style for configuring a `SecurityFilterChain` bean, where each aspect of security (authorization rules, form login, CSRF, session management) is configured through a `Customizer<T>` lambda passed to a method on `HttpSecurity`, instead of the older style of chaining `.and()` calls. `http.authorizeHttpRequests(auth -> auth.anyRequest().authenticated())` is the lambda form; `http.authorizeHttpRequests().anyRequest().authenticated().and()` was the older, now-discouraged form that this replaced starting in Spring Security 5.7.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/public/**").permitAll()
            .anyRequest().authenticated()
        )
        .formLogin(Customizer.withDefaults())
        .csrf(Customizer.withDefaults());
    return http.build();
}
```

## 2. Why & when

The older `.and()`-chained style produced long method chains where it was genuinely ambiguous, just from reading the code, which configuration block a given `.and()` call was returning *from* and which block subsequent method calls now applied *to* — a common source of misconfiguration where a developer intended to configure one security aspect but the fluent chain had silently returned to a different, outer context. The lambda DSL fixes this structurally: each `Customizer<T>` lambda receives exactly the configuration object for *one* concern (an `AuthorizeHttpRequestsConfigurer`, a `FormLoginConfigurer`) and its scope is delimited by the lambda's own braces, making it visually and structurally obvious which calls belong to which concern.

Reach for the lambda DSL when:

- Writing any new `SecurityFilterChain` bean — it is the currently recommended style, and the `.and()`-chained style is deprecated as of Spring Security 5.7 (removal has been an ongoing multi-release process since).
- Migrating an existing `.and()`-chained configuration — each `.and()` call typically corresponds exactly to one lambda block boundary, making the mechanical conversion straightforward once the pattern is recognized.
- `Customizer.withDefaults()` is the idiom for "enable this feature with its default settings, and configure nothing further" — reach for it whenever a feature (like `formLogin` or `httpBasic`) is wanted purely with defaults, rather than writing an empty lambda body.

## 3. Core concept

```
 OLD ("and"-chained) style:
   http.authorizeHttpRequests()
           .anyRequest().authenticated()
           .and()                          -- returns to HttpSecurity, ambiguous scope
       .formLogin()
           .loginPage("/login")
           .and()
       .csrf().disable();

 NEW (lambda) style:
   http
       .authorizeHttpRequests(auth -> auth   -- auth is scoped ONLY to authorization config
           .anyRequest().authenticated()
       )
       .formLogin(form -> form                -- form is scoped ONLY to form-login config
           .loginPage("/login")
       )
       .csrf(csrf -> csrf.disable());          -- csrf is scoped ONLY to CSRF config
```

Each lambda's parameter type and scope are explicit and self-contained — there is no ambiguous "where does `.and()` return me to" question in the lambda form.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An HttpSecurity object is configured through a sequence of independent lambda blocks each receiving exactly one configurer object scoped only to its own concern authorizeHttpRequests formLogin and csrf each configured in its own self-contained lambda">
  <rect x="15" y="20" width="610" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="47" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">http.authorizeHttpRequests(auth -&gt; auth.anyRequest().authenticated())</text>

  <rect x="15" y="80" width="610" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="320" y="107" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">.formLogin(form -&gt; form.loginPage(&quot;/login&quot;))</text>

  <rect x="15" y="140" width="610" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="167" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">.csrf(csrf -&gt; csrf.disable())</text>
</svg>

Three independent, self-contained blocks — each lambda's scope is delimited by its own parentheses, not by a shared, ambiguous method-chain state.

## 5. Runnable example

The scenario: model both DSL styles for the same configuration and show the lambda form's structural clarity concretely, by simulating a configuration mistake that's easy to make in the chained style but structurally impossible in the lambda style. Start with a minimal lambda-based configurer, then reproduce the chained-style ambiguity as a cautionary comparison, then build a realistic multi-concern configuration entirely in the lambda style.

### Level 1 — Basic

A minimal `Customizer`-style lambda DSL: one method taking a lambda scoped to its own configurer object.

```java
import java.util.*;
import java.util.function.Consumer;

public class LambdaDslLevel1 {
    static class AuthorizeConfigurer {
        List<String> permittedPaths = new ArrayList<>();
        boolean anyRequestAuthenticated = false;

        AuthorizeConfigurer permitAll(String path) { permittedPaths.add(path); return this; }
        AuthorizeConfigurer anyRequestAuthenticated() { anyRequestAuthenticated = true; return this; }
    }

    static class HttpSecurity {
        AuthorizeConfigurer authorizeConfig = new AuthorizeConfigurer();

        HttpSecurity authorizeHttpRequests(Consumer<AuthorizeConfigurer> customizer) {
            customizer.accept(authorizeConfig); // the lambda ONLY ever sees this one configurer
            return this;
        }
    }

    public static void main(String[] args) {
        HttpSecurity http = new HttpSecurity();
        http.authorizeHttpRequests(auth -> auth
                .permitAll("/public")
                .anyRequestAuthenticated()
        );
        System.out.println("permitted: " + http.authorizeConfig.permittedPaths
                + ", anyRequestAuthenticated: " + http.authorizeConfig.anyRequestAuthenticated);
    }
}
```

How to run: `java LambdaDslLevel1.java`

`authorizeHttpRequests` takes a `Consumer<AuthorizeConfigurer>`; inside the lambda passed at the call site, `auth` refers *only* to that one `AuthorizeConfigurer` instance — there is no other object the lambda body could possibly be configuring by mistake.

### Level 2 — Intermediate

Add a second configurable concern (`formLogin`) alongside the first, demonstrating each lambda's independent, non-overlapping scope.

```java
import java.util.*;
import java.util.function.Consumer;

public class LambdaDslLevel2 {
    static class AuthorizeConfigurer {
        List<String> permittedPaths = new ArrayList<>();
        AuthorizeConfigurer permitAll(String path) { permittedPaths.add(path); return this; }
    }

    static class FormLoginConfigurer {
        String loginPage = "/login"; // default
        FormLoginConfigurer loginPage(String path) { loginPage = path; return this; }
    }

    static class HttpSecurity {
        AuthorizeConfigurer authorizeConfig = new AuthorizeConfigurer();
        FormLoginConfigurer formLoginConfig = new FormLoginConfigurer();

        HttpSecurity authorizeHttpRequests(Consumer<AuthorizeConfigurer> customizer) {
            customizer.accept(authorizeConfig);
            return this;
        }

        HttpSecurity formLogin(Consumer<FormLoginConfigurer> customizer) {
            customizer.accept(formLoginConfig);
            return this;
        }
    }

    public static void main(String[] args) {
        HttpSecurity http = new HttpSecurity();
        http
            .authorizeHttpRequests(auth -> auth.permitAll("/public"))
            .formLogin(form -> form.loginPage("/custom-login"));

        System.out.println("permitted: " + http.authorizeConfig.permittedPaths);
        System.out.println("login page: " + http.formLoginConfig.loginPage);
    }
}
```

How to run: `java LambdaDslLevel2.java`

Each method call (`authorizeHttpRequests`, `formLogin`) passes its lambda a completely distinct configurer type (`AuthorizeConfigurer` vs. `FormLoginConfigurer`) — even though both calls are chained together on the same `http` object, there is no shared mutable "current context" that a call could accidentally target the wrong configurer for, unlike the old `.and()` style where a misplaced `.and()` could silently leave subsequent calls operating on the wrong nesting level.

### Level 3 — Advanced

A realistic three-concern configuration (`authorizeHttpRequests`, `formLogin`, `csrf`) with a `Customizer.withDefaults()`-style shortcut, and `build()` producing the final assembled rule set.

```java
import java.util.*;
import java.util.function.Consumer;

public class LambdaDslLevel3 {
    static class AuthorizeConfigurer {
        record Rule(String path, String requirement) {}
        List<Rule> rules = new ArrayList<>();
        AuthorizeConfigurer requestMatchersPermitAll(String path) { rules.add(new Rule(path, "permitAll")); return this; }
        AuthorizeConfigurer anyRequestAuthenticated() { rules.add(new Rule("/**", "authenticated")); return this; }
    }

    static class FormLoginConfigurer {
        String loginPage = "/login";
        FormLoginConfigurer loginPage(String path) { loginPage = path; return this; }
    }

    static class CsrfConfigurer {
        boolean enabled = true;
        CsrfConfigurer disable() { enabled = false; return this; }
    }

    // models Customizer.withDefaults() -- a no-op lambda meaning "enable with defaults, configure nothing further"
    static <T> Consumer<T> withDefaults() { return t -> {}; }

    static class HttpSecurity {
        AuthorizeConfigurer authorizeConfig = new AuthorizeConfigurer();
        FormLoginConfigurer formLoginConfig = new FormLoginConfigurer();
        CsrfConfigurer csrfConfig = new CsrfConfigurer();

        HttpSecurity authorizeHttpRequests(Consumer<AuthorizeConfigurer> c) { c.accept(authorizeConfig); return this; }
        HttpSecurity formLogin(Consumer<FormLoginConfigurer> c) { c.accept(formLoginConfig); return this; }
        HttpSecurity csrf(Consumer<CsrfConfigurer> c) { c.accept(csrfConfig); return this; }

        String build() {
            return "rules=" + authorizeConfig.rules + ", loginPage=" + formLoginConfig.loginPage + ", csrfEnabled=" + csrfConfig.enabled;
        }
    }

    public static void main(String[] args) {
        HttpSecurity http = new HttpSecurity();
        http
            .authorizeHttpRequests(auth -> auth
                .requestMatchersPermitAll("/public")
                .anyRequestAuthenticated())
            .formLogin(LambdaDslLevel3.<FormLoginConfigurer>withDefaults())
            .csrf(csrf -> csrf.disable());

        System.out.println(http.build());
    }
}
```

How to run: `java LambdaDslLevel3.java`

`formLogin(withDefaults())` passes a lambda that does nothing to `formLoginConfig`, leaving `loginPage` at its default `"/login"` — exactly what `Customizer.withDefaults()` means in real Spring Security code: "turn this feature on, but don't change any of its settings" — while `csrf(csrf -> csrf.disable())` explicitly mutates its own configurer, and `authorizeHttpRequests` builds up an ordered `rules` list from its own lambda, each concern's configuration remaining entirely independent of the others.

## 6. Walkthrough

Trace the three chained calls in Level 3's `main` in the order they execute.

1. `http.authorizeHttpRequests(auth -> ...)` runs first: `customizer.accept(authorizeConfig)` invokes the lambda with `authorizeConfig` bound to `auth`, so `auth.requestMatchersPermitAll("/public")` appends `Rule("/public", "permitAll")` to `rules`, and the chained `.anyRequestAuthenticated()` call appends `Rule("/**", "authenticated")` right after it — `rules` now holds both entries in that order.
2. The method returns `this` (the `http` object), so the next chained call, `.formLogin(...)`, executes on the same instance: `customizer.accept(formLoginConfig)` invokes the `withDefaults()` no-op lambda, which does nothing at all, leaving `formLoginConfig.loginPage` unchanged at `"/login"`.
3. `.csrf(csrf -> csrf.disable())` runs last: `customizer.accept(csrfConfig)` invokes the lambda with `csrfConfig` bound to `csrf`, and `csrf.disable()` sets `csrfConfig.enabled` to `false`.
4. `http.build()` runs after the chain completes, reading the final state of all three configurer objects and assembling the summary string: `"rules=[Rule[path=/public, requirement=permitAll], Rule[path=/**, requirement=authenticated]], loginPage=/login, csrfEnabled=false"`.
5. In a real Spring Security application, this `build()` call is where the actual servlet `Filter` instances get constructed and assembled into the running `SecurityFilterChain` — the `AuthorizeConfigurer`'s accumulated `rules` become the input to `AuthorizationFilter`, `formLoginConfig`'s settings configure `UsernamePasswordAuthenticationFilter`, and `csrfConfig.enabled = false` means `CsrfFilter` is omitted from the chain entirely.

```
authorizeHttpRequests(auth -> ...)  -->  rules = [/public: permitAll, /**: authenticated]
formLogin(withDefaults())           -->  loginPage stays "/login" (unchanged)
csrf(csrf -> csrf.disable())        -->  csrfEnabled = false
build()                             -->  assembles all three into one final SecurityFilterChain
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing the old `.and()`-chained style with the new lambda style in the same configuration (which the API technically still allows during the deprecation period) reintroduces exactly the scope ambiguity the lambda style was designed to eliminate, and is a common source of confusing "why didn't my configuration take effect" bugs during incremental migrations. Convert an entire `SecurityFilterChain` bean to the lambda style in one pass rather than mixing styles.

- The lambda DSL scopes each security concern's configuration to its own lambda block, structurally preventing the "which context am I in" ambiguity the older `.and()`-chained style was prone to.
- `Customizer.withDefaults()` is the idiom for "enable this feature, change nothing" — prefer it over an empty lambda body (`form -> {}`) for readability, though both are functionally identical.
- Each `HttpSecurity` method (`authorizeHttpRequests`, `formLogin`, `csrf`, and so on) still returns `this`, so the top-level chain of calls remains fluent — only the *inner* configuration of each concern moved into a lambda.
- `http.build()` is the final step that actually assembles every configurer's accumulated settings into the real, running `SecurityFilterChain` — nothing takes effect until `build()` runs.
