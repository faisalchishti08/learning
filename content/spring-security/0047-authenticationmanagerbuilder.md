---
card: spring-security
gi: 47
slug: authenticationmanagerbuilder
title: "AuthenticationManagerBuilder"
---

## 1. What it is

`AuthenticationManagerBuilder` is the builder API for assembling an `AuthenticationManager` (typically a `ProviderManager` under the hood) from one or more `AuthenticationProvider`s or `UserDetailsService`s, historically the standard way to wire authentication inside an overridden `configure(AuthenticationManagerBuilder)` method on `WebSecurityConfigurerAdapter` (now removed, per the earlier migration card) — in modern Spring Security, most applications instead simply declare `UserDetailsService`/`PasswordEncoder`/`AuthenticationProvider` as independent `@Bean` methods, letting auto-configuration assemble the `AuthenticationManager` automatically, with `AuthenticationManagerBuilder` reserved for cases needing explicit, multi-provider control.

```java
@Bean
public AuthenticationManager authenticationManager(
        AuthenticationConfiguration config) throws Exception {
    return config.getAuthenticationManager(); // the MODERN way to obtain the auto-assembled AuthenticationManager
}

// the OLDER, explicit builder style, still valid for multi-provider scenarios:
@Bean
public AuthenticationManager customAuthenticationManager(HttpSecurity http, UserDetailsService uds, PasswordEncoder encoder) throws Exception {
    AuthenticationManagerBuilder builder = http.getSharedObject(AuthenticationManagerBuilder.class);
    builder.userDetailsService(uds).passwordEncoder(encoder);
    builder.authenticationProvider(customLdapAuthenticationProvider());
    return builder.build();
}
```

## 2. Why & when

A single `UserDetailsService` and `PasswordEncoder` pair is enough for most applications, and Spring Boot's auto-configuration handles assembling the resulting `AuthenticationManager` automatically without any explicit builder code at all — but some applications genuinely need *multiple* `AuthenticationProvider`s tried in sequence (a primary database-backed provider, falling back to an LDAP provider for federated accounts, falling back again to a pre-authentication provider for internal service calls), and `AuthenticationManagerBuilder` is the explicit API for assembling exactly that multi-provider `ProviderManager` when auto-configuration's single-provider assumption doesn't fit.

Reach for `AuthenticationManagerBuilder` explicitly when:

- More than one `AuthenticationProvider` needs to be tried, in a specific order, for a single authentication attempt — auto-configuration handles the common single-provider case, but an explicit multi-provider chain needs to be assembled deliberately.
- Migrating legacy code that still overrides `configure(AuthenticationManagerBuilder auth)` on a (now-removed) `WebSecurityConfigurerAdapter` subclass — understanding the builder's API directly clarifies what the equivalent modern `@Bean`-based configuration should look like.
- For the common, single-provider case, prefer simply declaring `UserDetailsService` and `PasswordEncoder` as independent beans and letting `AuthenticationConfiguration.getAuthenticationManager()` (or Boot's own auto-configuration) assemble things automatically — reaching for the builder unnecessarily adds complexity a simpler bean-based setup wouldn't need.

## 3. Core concept

```
 AuthenticationManagerBuilder.build() PRODUCES a ProviderManager holding an ORDERED LIST of AuthenticationProviders:

   builder.userDetailsService(uds).passwordEncoder(encoder)
     -- CONVENIENCE method: internally constructs a DaoAuthenticationProvider wrapping uds+encoder,
        and adds IT to the list

   builder.authenticationProvider(customProvider)
     -- adds an ADDITIONAL provider DIRECTLY to the same list

   final ProviderManager tries EACH registered provider, IN ORDER, for a given authentication attempt
     -- the FIRST provider whose supports(authenticationType) returns true, and which doesn't throw,
        determines the result
```

The builder is purely an assembly convenience — the resulting `ProviderManager` behaves exactly like one manually constructed with the same provider list.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AuthenticationManagerBuilder assembles an ordered list of authentication providers a DaoAuthenticationProvider built from userDetailsService and passwordEncoder plus any additional providers added directly the resulting ProviderManager tries each provider in order for every authentication attempt">
  <rect x="15" y="20" width="220" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="125" y="38" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">.userDetailsService(uds)</text>
  <text x="125" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.passwordEncoder(encoder)</text>

  <rect x="15" y="70" width="220" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="125" y="91" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">.authenticationProvider(ldapProvider)</text>

  <rect x="15" y="114" width="220" height="34" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="125" y="135" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">.authenticationProvider(preAuthProvider)</text>

  <rect x="330" y="55" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="405" y="75" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">.build()</text>

  <rect x="510" y="55" width="115" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="567" y="75" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">ProviderManager</text>
  <text x="567" y="88" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">tries in order</text>

  <defs><marker id="a47" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="235" y1="40" x2="330" y2="70" stroke="#8b949e" stroke-width="1" marker-end="url(#a47)"/>
  <line x1="235" y1="87" x2="330" y2="78" stroke="#8b949e" stroke-width="1" marker-end="url(#a47)"/>
  <line x1="235" y1="131" x2="330" y2="86" stroke="#8b949e" stroke-width="1" marker-end="url(#a47)"/>
  <line x1="480" y1="78" x2="510" y2="78" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a47)"/>
</svg>

Three registration calls, one assembled `ProviderManager` — the builder's entire job is producing this final ordered list.

## 5. Runnable example

The scenario: model the builder's assembly logic, then use it to construct a multi-provider chain (database-backed primary, LDAP-style fallback), then show provider ordering mattering for which one actually handles a given authentication attempt.

### Level 1 — Basic

A minimal builder accumulating providers and producing a final ordered list.

```java
import java.util.*;
import java.util.function.Function;

public class AuthManagerBuilderLevel1 {
    interface AuthenticationProvider { String authenticate(String username, String password); }

    static class AuthenticationManagerBuilder {
        List<AuthenticationProvider> providers = new ArrayList<>();

        AuthenticationManagerBuilder userDetailsService(Map<String, String> userStore) {
            // CONVENIENCE method: builds a DaoAuthenticationProvider-style provider internally
            providers.add((username, password) -> {
                String stored = userStore.get(username);
                if (stored != null && stored.equals(password)) return "authenticated as " + username + " (via userDetailsService)";
                return null; // null signals "this provider could not authenticate"
            });
            return this;
        }

        AuthenticationManagerBuilder authenticationProvider(AuthenticationProvider provider) {
            providers.add(provider);
            return this;
        }

        List<AuthenticationProvider> build() { return List.copyOf(providers); } // an immutable, final ordered list
    }

    public static void main(String[] args) {
        AuthenticationManagerBuilder builder = new AuthenticationManagerBuilder();
        builder.userDetailsService(Map.of("alice", "hunter2"));

        List<AuthenticationProvider> providerManager = builder.build();
        System.out.println("provider count: " + providerManager.size());
        System.out.println(providerManager.get(0).authenticate("alice", "hunter2"));
    }
}
```

How to run: `java AuthManagerBuilderLevel1.java`

`userDetailsService(...)` is purely a convenience that internally constructs and registers a provider closure — the final `build()` call simply returns the accumulated list, exactly mirroring how the real builder's `userDetailsService`/`passwordEncoder` methods are convenience wrappers around constructing and adding a `DaoAuthenticationProvider`.

### Level 2 — Intermediate

Add a second, LDAP-style provider, assembling a genuine multi-provider chain and trying each in order until one succeeds.

```java
import java.util.*;

public class AuthManagerBuilderLevel2 {
    interface AuthenticationProvider { String authenticate(String username, String password); }

    static class AuthenticationManagerBuilder {
        List<AuthenticationProvider> providers = new ArrayList<>();
        AuthenticationManagerBuilder userDetailsService(Map<String, String> userStore) {
            providers.add((u, p) -> {
                String stored = userStore.get(u);
                return (stored != null && stored.equals(p)) ? "authenticated as " + u + " (database)" : null;
            });
            return this;
        }
        AuthenticationManagerBuilder authenticationProvider(AuthenticationProvider provider) { providers.add(provider); return this; }
        ProviderManager build() { return new ProviderManager(providers); }
    }

    static class ProviderManager {
        List<AuthenticationProvider> providers;
        ProviderManager(List<AuthenticationProvider> providers) { this.providers = providers; }

        String authenticate(String username, String password) {
            for (AuthenticationProvider provider : providers) {
                String result = provider.authenticate(username, password);
                if (result != null) return result; // FIRST provider to succeed wins -- no further providers tried
            }
            throw new RuntimeException("no provider could authenticate " + username);
        }
    }

    static AuthenticationProvider ldapStyleProvider = (username, password) -> {
        Map<String, String> ldapDirectory = Map.of("bob", "ldap-password-123");
        String stored = ldapDirectory.get(username);
        return (stored != null && stored.equals(password)) ? "authenticated as " + username + " (LDAP)" : null;
    };

    public static void main(String[] args) {
        AuthenticationManagerBuilder builder = new AuthenticationManagerBuilder();
        builder.userDetailsService(Map.of("alice", "hunter2"));
        builder.authenticationProvider(ldapStyleProvider);

        ProviderManager manager = builder.build();
        System.out.println(manager.authenticate("alice", "hunter2")); // matched by the FIRST (database) provider
        System.out.println(manager.authenticate("bob", "ldap-password-123")); // FIRST provider fails, SECOND (LDAP) succeeds
    }
}
```

How to run: `java AuthManagerBuilderLevel2.java`

alice authenticates via the first (database) provider, since her credentials match there directly; bob's credentials don't exist in the database provider's user store at all (it returns `null`), so `authenticate`'s loop falls through to the second, LDAP-style provider, which succeeds — demonstrating genuine multi-provider fallback in the exact order the providers were registered.

### Level 3 — Advanced

Demonstrate provider *order* mattering directly: the same two providers, registered in reversed order, change which provider's identity is reported for a user whose credentials happen to be valid against both.

```java
import java.util.*;

public class AuthManagerBuilderLevel3 {
    interface AuthenticationProvider { String authenticate(String username, String password); }

    static class ProviderManager {
        List<AuthenticationProvider> providers;
        ProviderManager(List<AuthenticationProvider> providers) { this.providers = providers; }
        String authenticate(String username, String password) {
            for (AuthenticationProvider provider : providers) {
                String result = provider.authenticate(username, password);
                if (result != null) return result;
            }
            throw new RuntimeException("no provider could authenticate " + username);
        }
    }

    // deliberately: a user "shared" who happens to have MATCHING credentials registered in BOTH stores
    static AuthenticationProvider databaseProvider = (u, p) ->
            (u.equals("shared") && p.equals("samepass")) ? "authenticated as shared (DATABASE provider)" : null;

    static AuthenticationProvider ldapProvider = (u, p) ->
            (u.equals("shared") && p.equals("samepass")) ? "authenticated as shared (LDAP provider)" : null;

    public static void main(String[] args) {
        ProviderManager databaseFirst = new ProviderManager(List.of(databaseProvider, ldapProvider));
        ProviderManager ldapFirst = new ProviderManager(List.of(ldapProvider, databaseProvider));

        System.out.println("database-first order: " + databaseFirst.authenticate("shared", "samepass"));
        System.out.println("LDAP-first order:      " + ldapFirst.authenticate("shared", "samepass"));
    }
}
```

How to run: `java AuthManagerBuilderLevel3.java`

The identical credentials, checked against the identical two providers, produce a *different* reported result purely based on registration order — `databaseFirst` reports the database provider's identity string since it's tried first and succeeds immediately, while `ldapFirst` reports the LDAP provider's instead, since *it* is now first in line; this matters in practice whenever different providers might attach different authorities or metadata to an otherwise similarly-named principal.

## 6. Walkthrough

Trace `ldapFirst.authenticate("shared", "samepass")` from Level 3.

1. `ldapFirst.providers` is `[ldapProvider, databaseProvider]` — note the order, reversed relative to `databaseFirst`.
2. `authenticate`'s `for` loop begins with the first element, `ldapProvider`: it calls `ldapProvider.authenticate("shared", "samepass")`, which checks `u.equals("shared") && p.equals("samepass")` — both conditions are `true`, so it returns `"authenticated as shared (LDAP provider)"`, a non-null value.
3. Because `result` is non-null, the `if (result != null) return result;` line fires immediately, returning this string directly from `authenticate` — the loop never proceeds to check `databaseProvider` at all, even though it *would* have also matched these exact same credentials had it been reached.
4. Compare this with `databaseFirst`, whose `providers` list is `[databaseProvider, ldapProvider]` — its loop instead reaches `databaseProvider` first, which matches identically and returns its own `"...(DATABASE provider)"` string, again short-circuiting before `ldapProvider` is ever consulted.
5. This confirms the entire behavioral difference between the two `ProviderManager` instances stems purely from list ordering — nothing about the credentials, the providers' internal logic, or anything else changed between the two calls, only which provider happened to be checked *first*.

```
ldapFirst.providers    = [ldapProvider, databaseProvider]
  authenticate("shared", "samepass"):
    try ldapProvider     -> matches -> return "...(LDAP provider)" immediately, databaseProvider NEVER checked

databaseFirst.providers = [databaseProvider, ldapProvider]
  authenticate("shared", "samepass"):
    try databaseProvider -> matches -> return "...(DATABASE provider)" immediately, ldapProvider NEVER checked
```

## 7. Gotchas & takeaways

> **Gotcha:** when two registered providers could both plausibly authenticate the same username (a genuine risk if, say, both a local database and an external LDAP directory happen to contain accounts with the same username), registration order silently determines which provider's identity, authorities, and any provider-specific metadata "win" — this is worth deliberately considering and testing for, not left to incidental registration order.

- `AuthenticationManagerBuilder` assembles an ordered list of `AuthenticationProvider`s into a `ProviderManager`; its convenience methods (`userDetailsService`, `passwordEncoder`) simply construct and register a `DaoAuthenticationProvider` internally.
- Most applications with a single `UserDetailsService`/`PasswordEncoder` pair never need to touch this builder directly — Spring Boot's auto-configuration assembles the equivalent single-provider `AuthenticationManager` automatically from independently declared beans.
- Reach for the builder explicitly when a genuine multi-provider chain is needed — providers are tried in registration order, and the first one to successfully authenticate (without throwing, and returning a non-null/verified result) wins, with no further providers consulted.
- Provider registration order is a meaningful, behavior-affecting decision whenever more than one registered provider could plausibly handle the same authentication attempt — test this ordering deliberately rather than leaving it to chance.
