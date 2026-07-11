---
card: spring-security
gi: 17
slug: java-config-enablewebsecurity
title: "Java config (@EnableWebSecurity)"
---

## 1. What it is

`@EnableWebSecurity` is the annotation placed on a `@Configuration` class that turns on Spring Security's web-layer support — it imports the infrastructure that builds the servlet `Filter` chain from any `SecurityFilterChain` beans defined in the application context, and wires that chain into the servlet container via `DelegatingFilterProxy` (from the filters card, three cards back). With Spring Boot, the security auto-configuration already applies a default configuration if no custom one is present, so `@EnableWebSecurity` is mostly needed explicitly once an application defines its own `SecurityFilterChain` bean(s), to make the intent to fully customize security configuration clear.

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth.anyRequest().authenticated());
        return http.build();
    }
}
```

## 2. Why & when

Spring Boot's auto-configuration provides a reasonable security default out of the box (every endpoint requires authentication, a generated password is printed to the console) purely so a freshly created project isn't accidentally left wide open — but almost every real application needs to customize this: some paths should be public, others should require specific roles, and the authentication mechanism itself (form login, OAuth2, a custom filter) needs explicit configuration. `@EnableWebSecurity`, combined with one or more `SecurityFilterChain` beans, is how that customization is declared — the moment a `SecurityFilterChain` bean is defined, Spring Boot's default auto-configured chain steps aside entirely in favor of the beans the application provides.

Reach for `@EnableWebSecurity` (and a custom `SecurityFilterChain` bean) when:

- The application needs anything beyond the Boot default — public endpoints, role-based access rules, a non-default login mechanism, CORS configuration, or CSRF customization.
- Migrating from the legacy `WebSecurityConfigurerAdapter` class-based style (a later card in this section) to the modern, composable bean-based style.
- Defining more than one independent `SecurityFilterChain`, each applying to a different subset of request paths (also a later card) — each chain is still declared inside an `@EnableWebSecurity`-annotated configuration class.

## 3. Core concept

```
 @Configuration
 @EnableWebSecurity                         -- turns on web security infrastructure
 class SecurityConfig {

     @Bean
     SecurityFilterChain filterChain(HttpSecurity http) {
         ...configure http...
         return http.build();               -- THIS bean IS the actual filter chain, built from the HttpSecurity DSL
     }
 }

 Spring Boot auto-configuration:
   IF an application defines its OWN SecurityFilterChain bean(s)  -->  Boot's default chain steps ASIDE entirely
   IF NOT                                                          -->  Boot's default chain applies (require auth on everything)
```

`@EnableWebSecurity` itself doesn't configure any specific security rule — it activates the machinery that turns `SecurityFilterChain` beans into an actual, running filter chain.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An EnableWebSecurity annotated configuration class defines a SecurityFilterChain bean built from the HttpSecurity DSL Spring Security wires this chain into the servlet container replacing Spring Boot's default auto configured security entirely">
  <rect x="20" y="60" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="82" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@EnableWebSecurity</text>
  <text x="110" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@Configuration class</text>
  <text x="110" y="108" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">defines SecurityFilterChain bean</text>

  <rect x="250" y="60" width="150" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="325" y="82" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">HttpSecurity DSL</text>
  <text x="325" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.authorizeHttpRequests</text>
  <text x="325" y="108" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.formLogin, etc.</text>

  <rect x="450" y="60" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="82" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">built SecurityFilterChain</text>
  <text x="535" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">wired into servlet container</text>
  <text x="535" y="108" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">(replaces Boot default)</text>

  <defs><marker id="a17" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="90" x2="250" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a17)"/>
  <line x1="400" y1="90" x2="450" y2="90" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a17)"/>
</svg>

`@EnableWebSecurity` is the switch that lets a `SecurityFilterChain` bean, built via the `HttpSecurity` DSL, take over from Boot's default.

## 5. Runnable example

The scenario: model Spring Boot's default-versus-custom security decision directly — a registry that checks whether a "custom filter chain bean" has been defined, and picks the default chain only if not. Start with the plain default-chain behavior, then add a custom chain that overrides it, then add multiple rules inside the custom chain's configuration to show a realistic authorization setup.

### Level 1 — Basic

Model Spring Boot's default security behavior: with no custom configuration present, every request requires authentication.

```java
import java.util.*;

public class EnableWebSecurityLevel1 {
    record Request(String path, String principal) {}

    // models the DEFAULT Spring Boot auto-configured chain: require authentication on every request
    static String defaultChain(Request request) {
        if (request.principal() == null) return "401 Unauthorized (default: everything requires auth)";
        return "200 OK, authenticated as " + request.principal();
    }

    public static void main(String[] args) {
        System.out.println(defaultChain(new Request("/", null)));
        System.out.println(defaultChain(new Request("/", "alice")));
    }
}
```

How to run: `java EnableWebSecurityLevel1.java`

With no custom configuration, `defaultChain` treats every request identically: no principal means `401`, any principal at all means `200` — this is Boot's out-of-the-box default, intentionally strict so a fresh project isn't left wide open by accident.

### Level 2 — Intermediate

Introduce a registry modeling `@EnableWebSecurity`'s bean-presence check: if a custom `SecurityFilterChain`-like bean is registered, it fully replaces the default.

```java
import java.util.*;
import java.util.function.Function;

public class EnableWebSecurityLevel2 {
    record Request(String path, String principal) {}

    static String defaultChain(Request request) {
        if (request.principal() == null) return "401 Unauthorized (default chain)";
        return "200 OK (default chain), authenticated as " + request.principal();
    }

    // models a registry of beans in the application context
    static class ApplicationContext {
        Function<Request, String> customChain = null; // null = no custom SecurityFilterChain bean defined

        String handle(Request request) {
            // @EnableWebSecurity's actual behavior: a custom bean, if present, REPLACES the default entirely
            Function<Request, String> chain = (customChain != null) ? customChain : EnableWebSecurityLevel2::defaultChain;
            return chain.apply(request);
        }
    }

    public static void main(String[] args) {
        ApplicationContext context = new ApplicationContext();
        System.out.println("no custom chain: " + context.handle(new Request("/public", null)));

        // register a custom chain: public paths need no authentication, everything else does
        context.customChain = request -> {
            if (request.path().equals("/public")) return "200 OK (public, no auth required)";
            if (request.principal() == null) return "401 Unauthorized (custom chain)";
            return "200 OK (custom chain), authenticated as " + request.principal();
        };
        System.out.println("with custom chain: " + context.handle(new Request("/public", null)));
        System.out.println("with custom chain: " + context.handle(new Request("/account", null)));
    }
}
```

How to run: `java EnableWebSecurityLevel2.java`

Before `customChain` is set, `handle` falls back to `defaultChain` and rejects the unauthenticated `/public` request; once a custom chain is registered, `/public` is explicitly carved out as needing no authentication while `/account` still requires it — the custom bean has fully replaced the default, not merely supplemented it.

### Level 3 — Advanced

Model a more realistic `HttpSecurity`-style DSL with an ordered list of path-to-rule mappings and a fallback rule, matching how `authorizeHttpRequests` actually evaluates matchers in registration order.

```java
import java.util.*;
import java.util.function.Predicate;

public class EnableWebSecurityLevel3 {
    record Request(String path, String principal, Set<String> roles) {}
    record Rule(Predicate<String> pathMatcher, String requiredRole) {} // requiredRole == null means "permitAll"

    static class SecurityFilterChain {
        private final List<Rule> rules = new ArrayList<>();

        SecurityFilterChain permitAll(String pathPrefix) {
            rules.add(new Rule(p -> p.startsWith(pathPrefix), null));
            return this;
        }

        SecurityFilterChain hasRole(String pathPrefix, String role) {
            rules.add(new Rule(p -> p.startsWith(pathPrefix), role));
            return this;
        }

        SecurityFilterChain anyRequestAuthenticated() {
            rules.add(new Rule(p -> true, "AUTHENTICATED_ONLY"));
            return this;
        }

        String handle(Request request) {
            for (Rule rule : rules) {
                if (!rule.pathMatcher().test(request.path())) continue;
                if (rule.requiredRole() == null) return "200 OK (permitAll matched " + request.path() + ")";
                if (request.principal() == null) return "401 Unauthorized";
                if (rule.requiredRole().equals("AUTHENTICATED_ONLY")) return "200 OK, authenticated as " + request.principal();
                if (!request.roles().contains(rule.requiredRole())) return "403 Forbidden, requires " + rule.requiredRole();
                return "200 OK, " + request.principal() + " has required role " + rule.requiredRole();
            }
            return "403 Forbidden (no matching rule -- deny by default)";
        }
    }

    public static void main(String[] args) {
        SecurityFilterChain chain = new SecurityFilterChain()
                .permitAll("/public")
                .hasRole("/admin", "ROLE_ADMIN")
                .anyRequestAuthenticated();

        System.out.println(chain.handle(new Request("/public/info", null, Set.of())));
        System.out.println(chain.handle(new Request("/admin/reports", "bob", Set.of("ROLE_USER"))));
        System.out.println(chain.handle(new Request("/admin/reports", "alice", Set.of("ROLE_ADMIN"))));
        System.out.println(chain.handle(new Request("/account", "bob", Set.of("ROLE_USER"))));
    }
}
```

How to run: `java EnableWebSecurityLevel3.java`

`rules` is checked in the exact order they were registered — `/public/info` matches the first rule and is granted immediately; `/admin/reports` matches the second rule for both bob and alice, but only alice has `ROLE_ADMIN`, so bob gets `403` while alice gets `200`; `/account` matches neither specific rule and falls to the final catch-all `anyRequestAuthenticated` rule, which only checks that a principal exists — reproducing `http.authorizeHttpRequests(auth -> auth.requestMatchers("/public/**").permitAll().requestMatchers("/admin/**").hasRole("ADMIN").anyRequest().authenticated())` rule by rule.

## 6. Walkthrough

Trace `chain.handle(new Request("/admin/reports", "bob", Set.of("ROLE_USER")))` from Level 3.

1. `handle` begins iterating `rules` in registration order: first `Rule(p -> p.startsWith("/public"), null)` — its `pathMatcher.test("/admin/reports")` returns `false`, so the loop's `continue` skips straight to the next rule.
2. Next is `Rule(p -> p.startsWith("/admin"), "ROLE_ADMIN")` — its `pathMatcher.test("/admin/reports")` returns `true`, so this rule is selected and the loop does not continue further.
3. `rule.requiredRole()` is `"ROLE_ADMIN"`, not `null`, so the `permitAll` branch is skipped; `request.principal()` is `"bob"`, not `null`, so the `401` branch is skipped too.
4. `rule.requiredRole().equals("AUTHENTICATED_ONLY")` is `false` (it's `"ROLE_ADMIN"`), so control reaches the final check: `request.roles().contains("ROLE_ADMIN")` — bob's roles are `{ROLE_USER}`, which does not contain `"ROLE_ADMIN"`, so this is `false`.
5. The method returns `"403 Forbidden, requires ROLE_ADMIN"` — bob is a known, authenticated principal (this was never a `401` case), but lacks the specific role this path requires, exactly the `AccessDeniedException` scenario from the previous card's exception-translation walkthrough.

```
request: GET /admin/reports (principal=bob, roles={ROLE_USER})
  rule 1 (/public, permitAll)        -> path mismatch, skip
  rule 2 (/admin, ROLE_ADMIN)        -> path match! principal present, but ROLE_ADMIN missing -> 403
  (rule 3 never evaluated -- rule 2 already returned)
```

## 7. Gotchas & takeaways

> **Gotcha:** rule order matters — `authorizeHttpRequests` (and this model's `rules` list) evaluates matchers top to bottom and stops at the first match, so a broad `anyRequest().authenticated()` rule placed *before* a more specific `/admin/**` rule would shadow it entirely, silently applying the wrong (too permissive or too strict) policy to admin paths. Always register the most specific path rules first and the catch-all `anyRequest()` rule last.

- `@EnableWebSecurity` itself only activates the infrastructure; the actual security policy comes entirely from `SecurityFilterChain` bean(s) built with the `HttpSecurity` DSL.
- Defining even one custom `SecurityFilterChain` bean fully replaces Spring Boot's auto-configured default chain — there's no partial merge between the two.
- Rule/matcher order inside `authorizeHttpRequests` is evaluated sequentially and short-circuits at the first match, mirroring exactly how the `rules` list is walked in the example above.
- A request matching no rule at all is denied by default (`403`), not silently allowed — "deny by default" is a deliberate security posture that should generally be preserved by ending every configuration with an explicit catch-all rule.
