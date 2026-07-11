---
card: spring-security
gi: 23
slug: migrating-from-websecurityconfigureradapter-deprecated
title: "Migrating from WebSecurityConfigurerAdapter (deprecated)"
---

## 1. What it is

`WebSecurityConfigurerAdapter` was the class-based configuration style used before Spring Security 5.7, where an application extended it and overrode `configure(HttpSecurity)` (and optionally `configure(AuthenticationManagerBuilder)` and `configure(WebSecurity)`) to define security rules; it is now deprecated (and, as of Spring Security 6/Spring Boot 3, fully removed), replaced entirely by declaring `SecurityFilterChain` and `WebSecurityCustomizer` beans directly, with no base class to extend.

```java
// OLD (deprecated, removed in Spring Security 6): extend a base class, override configure()
@Configuration
public class OldSecurityConfig extends WebSecurityConfigurerAdapter {
    @Override
    protected void configure(HttpSecurity http) throws Exception {
        http.authorizeRequests()
                .antMatchers("/public/**").permitAll()
                .anyRequest().authenticated()
            .and()
            .formLogin();
    }
}

// NEW: declare a SecurityFilterChain bean, no inheritance at all
@Configuration
@EnableWebSecurity
public class NewSecurityConfig {
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(auth -> auth
                    .requestMatchers("/public/**").permitAll()
                    .anyRequest().authenticated())
            .formLogin(Customizer.withDefaults());
        return http.build();
    }
}
```

## 2. Why & when

Extending a single base class and overriding its `configure` methods forces every application into one specific inheritance hierarchy, makes composing multiple independent security configurations awkward (a subclass can only override each `configure` method once), and ties configuration to Spring's older, less flexible bean-override-based extension model. The component-based approach — plain `@Bean` methods producing `SecurityFilterChain` and `WebSecurityCustomizer` instances, with no shared base class — fits Spring's broader, general move away from inheritance-based configuration toward composition: multiple independent chains (the earlier "multiple filter chains" card) simply become multiple `@Bean` methods, something `WebSecurityConfigurerAdapter`'s single-`configure`-override model could not express nearly as cleanly.

Reach for the migration when:

- Upgrading to Spring Security 6.x or Spring Boot 3.x, where `WebSecurityConfigurerAdapter` no longer exists at all — this migration is mandatory, not optional, for any such upgrade.
- Maintaining an older codebase that still extends the adapter — even without an immediate framework upgrade, migrating early avoids a larger, more disruptive change bundled together with an eventual major-version upgrade.
- The specific mechanical mapping to know: `configure(HttpSecurity)`'s body becomes the body of a `SecurityFilterChain` bean method (ending in `return http.build();`); `configure(WebSecurity)`'s body becomes a `WebSecurityCustomizer` bean; `configure(AuthenticationManagerBuilder)`'s body is typically replaced by defining `UserDetailsService` and `PasswordEncoder` as their own beans instead.

## 3. Core concept

```
 OLD: class-based, override configure()
   class Config extends WebSecurityConfigurerAdapter {
       configure(HttpSecurity http)              -> becomes a SecurityFilterChain @Bean method
       configure(WebSecurity web)                -> becomes a WebSecurityCustomizer @Bean method
       configure(AuthenticationManagerBuilder b)  -> becomes UserDetailsService / PasswordEncoder @Bean methods
   }

 NEW: bean-based, no inheritance
   @Bean SecurityFilterChain filterChain(HttpSecurity http) { ...; return http.build(); }
   @Bean WebSecurityCustomizer webSecurityCustomizer() { return web -> web.ignoring()...; }
   @Bean UserDetailsService userDetailsService() { ... }
   @Bean PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }
```

Each overridden method in the old style maps to exactly one `@Bean` method in the new style — the mechanical transformation is largely a matter of "unwrap the method body, add a `@Bean` annotation, return the built object."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single WebSecurityConfigurerAdapter subclass with three overridden configure methods is migrated into three independent bean methods a SecurityFilterChain bean a WebSecurityCustomizer bean and UserDetailsService and PasswordEncoder beans with no shared base class connecting them">
  <rect x="15" y="55" width="220" height="90" rx="9" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="125" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">extends WebSecurityConfigurerAdapter</text>
  <text x="125" y="92" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">configure(HttpSecurity)</text>
  <text x="125" y="105" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">configure(WebSecurity)</text>
  <text x="125" y="118" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">configure(AuthManagerBuilder)</text>
  <text x="125" y="135" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(DEPRECATED / REMOVED)</text>

  <rect x="380" y="15" width="230" height="34" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="495" y="36" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Bean SecurityFilterChain</text>

  <rect x="380" y="60" width="230" height="34" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="495" y="81" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Bean WebSecurityCustomizer</text>

  <rect x="380" y="105" width="230" height="34" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="495" y="126" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Bean UserDetailsService</text>

  <rect x="380" y="150" width="230" height="34" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="495" y="171" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Bean PasswordEncoder</text>

  <defs><marker id="a23" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="235" y1="80" x2="380" y2="32" stroke="#8b949e" stroke-width="1" marker-end="url(#a23)"/>
  <line x1="235" y1="95" x2="380" y2="77" stroke="#8b949e" stroke-width="1" marker-end="url(#a23)"/>
  <line x1="235" y1="115" x2="380" y2="122" stroke="#8b949e" stroke-width="1" marker-end="url(#a23)"/>
  <line x1="235" y1="115" x2="380" y2="167" stroke="#8b949e" stroke-width="1" marker-end="url(#a23)"/>
</svg>

One subclass with three overridden methods becomes four independent beans, with no inheritance relationship at all.

## 5. Runnable example

The scenario: model both the old inheritance-based structure and the new bean-based structure for the *same* configuration, and confirm they produce identical resulting rules — proving the migration is behavior-preserving. Start with a minimal old-style config and its mechanical new-style equivalent, then add the `WebSecurity`/ignoring migration, then add the `AuthenticationManagerBuilder` migration to standalone `UserDetailsService`/`PasswordEncoder` beans.

### Level 1 — Basic

The old `configure(HttpSecurity)` override modeled as a method body, and its mechanical bean-based equivalent, both producing the same rule set.

```java
import java.util.*;

public class MigrationLevel1 {
    record Rule(String pathPrefix, String requirement) {}

    // OLD STYLE: modeled as what configure(HttpSecurity) used to build
    static List<Rule> oldStyleConfigure() {
        List<Rule> rules = new ArrayList<>();
        rules.add(new Rule("/public", "permitAll"));
        rules.add(new Rule("/**", "authenticated"));
        return rules;
    }

    // NEW STYLE: the body of a SecurityFilterChain @Bean method
    static List<Rule> securityFilterChainBean() {
        List<Rule> rules = new ArrayList<>();
        rules.add(new Rule("/public", "permitAll"));
        rules.add(new Rule("/**", "authenticated"));
        return rules; // in real code: http.build() would return the assembled SecurityFilterChain here
    }

    public static void main(String[] args) {
        System.out.println("old style rules: " + oldStyleConfigure());
        System.out.println("new style rules: " + securityFilterChainBean());
        System.out.println("identical? " + oldStyleConfigure().equals(securityFilterChainBean()));
    }
}
```

How to run: `java MigrationLevel1.java`

The two methods produce byte-for-byte identical `Rule` lists — the migration from overriding `configure(HttpSecurity)` to writing a `SecurityFilterChain` `@Bean` method is, at this level, a purely mechanical transformation with no behavioral change at all.

### Level 2 — Intermediate

Add the `configure(WebSecurity)` override and its `WebSecurityCustomizer` bean equivalent, migrating the "ignoring static resources" configuration.

```java
import java.util.*;

public class MigrationLevel2 {
    record Rule(String pathPrefix, String requirement) {}

    static class OldStyleConfig {
        List<Rule> httpRules = List.of(new Rule("/public", "permitAll"), new Rule("/**", "authenticated"));
        List<String> ignoredPaths = List.of("/css/**", "/js/**"); // was: configure(WebSecurity web) { web.ignoring()... }
    }

    // NEW STYLE: two INDEPENDENT beans, no shared class at all
    static List<Rule> securityFilterChainBean() {
        return List.of(new Rule("/public", "permitAll"), new Rule("/**", "authenticated"));
    }

    static List<String> webSecurityCustomizerBean() {
        return List.of("/css/**", "/js/**");
    }

    public static void main(String[] args) {
        OldStyleConfig old = new OldStyleConfig();
        System.out.println("old: httpRules=" + old.httpRules + ", ignoredPaths=" + old.ignoredPaths);
        System.out.println("new: filterChain=" + securityFilterChainBean() + ", customizer=" + webSecurityCustomizerBean());
    }
}
```

How to run: `java MigrationLevel2.java`

`OldStyleConfig` bundles both concerns as fields on one object (mirroring two overridden methods on one subclass), while the new style produces them from two entirely independent, unrelated methods — there is no object holding both; each is simply its own `@Bean`, matching real Spring configuration where `filterChain(...)` and `webSecurityCustomizer()` are two separate `@Bean`-annotated methods in the same `@Configuration` class with no other relationship.

### Level 3 — Advanced

Add the `configure(AuthenticationManagerBuilder)` migration — moving user-store and password-encoding setup out of an overridden method and into standalone `UserDetailsService`/`PasswordEncoder` beans, the most involved part of a typical real migration.

```java
import java.util.*;

public class MigrationLevel3 {
    record User(String username, String hashedPassword, Set<String> roles) {}

    interface PasswordEncoder { String encode(String raw); boolean matches(String raw, String hashed); }

    static class SimplePasswordEncoder implements PasswordEncoder {
        public String encode(String raw) { return "hashed(" + raw + ")"; } // stand-in for BCrypt
        public boolean matches(String raw, String hashed) { return encode(raw).equals(hashed); }
    }

    interface UserDetailsService { User loadUserByUsername(String username); }

    // OLD STYLE, modeled: what configure(AuthenticationManagerBuilder auth) used to wire up inline
    static class OldStyleAuthConfig {
        PasswordEncoder passwordEncoder = new SimplePasswordEncoder();
        Map<String, User> userStore = new HashMap<>();

        void configure() { // models auth.inMemoryAuthentication().withUser(...)... called from configure()
            userStore.put("alice", new User("alice", passwordEncoder.encode("secret"), Set.of("ROLE_ADMIN")));
        }
    }

    // NEW STYLE: PasswordEncoder and UserDetailsService are their OWN, independent beans
    static PasswordEncoder passwordEncoderBean() { return new SimplePasswordEncoder(); }

    static UserDetailsService userDetailsServiceBean(PasswordEncoder encoder) {
        Map<String, User> userStore = new HashMap<>();
        userStore.put("alice", new User("alice", encoder.encode("secret"), Set.of("ROLE_ADMIN")));
        return username -> {
            User user = userStore.get(username);
            if (user == null) throw new NoSuchElementException("no such user: " + username);
            return user;
        };
    }

    public static void main(String[] args) {
        OldStyleAuthConfig old = new OldStyleAuthConfig();
        old.configure();
        User oldAlice = old.userStore.get("alice");
        System.out.println("old style: " + oldAlice);

        PasswordEncoder encoder = passwordEncoderBean();
        UserDetailsService uds = userDetailsServiceBean(encoder);
        User newAlice = uds.loadUserByUsername("alice");
        System.out.println("new style: " + newAlice);

        System.out.println("both authenticate 'secret' correctly? "
                + encoder.matches("secret", oldAlice.hashedPassword())
                + " and " + encoder.matches("secret", newAlice.hashedPassword()));
    }
}
```

How to run: `java MigrationLevel3.java`

`userDetailsServiceBean` takes `PasswordEncoder` as a constructor-style parameter (mirroring `@Bean` method dependency injection in real Spring code, where `userDetailsService(PasswordEncoder encoder)` simply declares the dependency as a method parameter), producing an independently testable, independently reusable bean — rather than both concerns being buried inside a single `configure(AuthenticationManagerBuilder)` override that only that one subclass could invoke.

## 6. Walkthrough

Trace the new-style path in Level 3's `main`, from bean construction through to a successful password check.

1. `passwordEncoderBean()` is called first, constructing and returning a fresh `SimplePasswordEncoder` instance, assigned to `encoder` — in real Spring code, this method's `@Bean` annotation means the container manages this instance and injects it wherever a `PasswordEncoder` is required.
2. `userDetailsServiceBean(encoder)` is called next, with the just-created `encoder` passed in — inside, it builds a `userStore` map with one entry for `"alice"`, calling `encoder.encode("secret")` to compute `"hashed(secret)"` as her stored password, and returns a lambda implementing `UserDetailsService`.
3. `uds.loadUserByUsername("alice")` is called, looking up `"alice"` in the closed-over `userStore` map (captured by the lambda), finding the entry, and returning it as `newAlice`.
4. The final `println` calls `encoder.matches("secret", oldAlice.hashedPassword())` and the equivalent for `newAlice` — `matches` re-encodes `"secret"` (producing `"hashed(secret)"` again) and compares it against the stored hash, which is equal in both cases, so both print `true`.
5. This confirms the migration is behavior-preserving: whether the `UserDetailsService` and `PasswordEncoder` setup lives inside an overridden `configure(AuthenticationManagerBuilder)` method or in two independent `@Bean` methods, the same user, with the same correctly-hashed password, is available to authenticate against.

```
old style: configure() runs inline inside the subclass, populates userStore directly
new style: passwordEncoderBean() -> userDetailsServiceBean(encoder) -> uds.loadUserByUsername("alice")
both produce a User with the SAME hashed password -> encoder.matches("secret", ...) == true for both
```

## 7. Gotchas & takeaways

> **Gotcha:** `antMatchers(...)` (used throughout the old `WebSecurityConfigurerAdapter` style) was itself deprecated and removed alongside the adapter class, in favor of `requestMatchers(...)` — a migration that touches `configure(HttpSecurity)` almost always needs both changes made together (adapter-to-bean *and* `antMatchers`-to-`requestMatchers`), not just one.

- `WebSecurityConfigurerAdapter` is fully removed in Spring Security 6 / Spring Boot 3 — this migration is mandatory for any application upgrading past that point, not merely a stylistic recommendation.
- Each overridden `configure` method maps to one independent `@Bean` method: `configure(HttpSecurity)` to a `SecurityFilterChain` bean, `configure(WebSecurity)` to a `WebSecurityCustomizer` bean, `configure(AuthenticationManagerBuilder)` to standalone `UserDetailsService`/`PasswordEncoder` beans.
- The new style has no shared base class connecting these beans — they are related only by being declared in the same `@Configuration` class (or even different ones), which is what makes composing multiple independent chains (the earlier multiple-filter-chains card) far more natural than it was under the single-subclass adapter model.
- `antMatchers`/`mvcMatchers`/`regexMatchers` were deprecated and removed alongside the adapter — `requestMatchers(...)` is the single unified replacement for all of them.
