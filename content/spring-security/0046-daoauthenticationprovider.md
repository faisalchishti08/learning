---
card: spring-security
gi: 46
slug: daoauthenticationprovider
title: "DaoAuthenticationProvider"
---

## 1. What it is

`DaoAuthenticationProvider` is Spring Security's built-in `AuthenticationProvider` implementing the standard username/password check: it loads a `UserDetails` via a configured `UserDetailsService`, verifies the submitted password against the stored hash using a configured `PasswordEncoder`, runs pre- and post-authentication account-state checks (the four `UserDetails` flags, via `DefaultPreAuthenticationChecks` and `DefaultPostAuthenticationChecks`), and — deliberately — normalizes a missing user and a wrong password into the *identical* exception type and message, to avoid leaking which case actually occurred.

```java
@Bean
public AuthenticationProvider daoAuthenticationProvider(UserDetailsService uds, PasswordEncoder encoder) {
    DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
    provider.setUserDetailsService(uds);
    provider.setPasswordEncoder(encoder);
    provider.setHideUserNotFoundExceptions(true); // the DEFAULT -- deliberately masks "no such user"
    return provider;
}
```

## 2. Why & when

Every card in this section's "Authentication" group — `UserDetails`/`UserDetailsService`, the various `PasswordEncoder` implementations, `DelegatingPasswordEncoder`, `UserDetailsPasswordService` — exists specifically to be consumed by `DaoAuthenticationProvider`; it is the concrete class that ties all of those individually-covered pieces together into one working, standard authentication flow. Understanding it directly clarifies the *exact* order operations happen in (load, pre-check, verify password, post-check, upgrade) and explains a specific, easy-to-miss security property: by default, attempting to log in as a username that doesn't exist at all produces the exact same `BadCredentialsException` (same type, same message) as attempting to log in with a wrong password for a username that *does* exist — deliberately preventing an attacker from using error-message differences to enumerate valid usernames.

Reach for understanding (or explicitly configuring) `DaoAuthenticationProvider` when:

- Wiring up any username/password-based authentication mechanism (form login, HTTP Basic) — it is very likely the concrete `AuthenticationProvider` doing the actual work underneath, registered automatically by Spring Boot's auto-configuration whenever a `UserDetailsService` bean is present.
- Debugging the exact order account-state checks run in relative to the password check — pre-checks (`isAccountNonExpired`, `isAccountNonLocked`) run *before* the password is verified, while `isCredentialsNonExpired` and `isEnabled` (post-checks) run *after* — a subtle but sometimes relevant distinction for custom `UserDetailsChecker` implementations.
- Explicitly setting `setHideUserNotFoundExceptions(false)` only in narrow, well-understood scenarios (some internal admin tooling where username enumeration isn't a meaningful risk) — leaving it at its default `true` is correct for essentially every public-facing login.

## 3. Core concept

```
 DaoAuthenticationProvider.authenticate(unverified):
   1. UserDetails user = retrieveUser(username)
        -- CALLS userDetailsService.loadUserByUsername(username)
        -- IF UsernameNotFoundException is thrown AND hideUserNotFoundExceptions=true (default):
             re-thrown as a GENERIC BadCredentialsException instead (masks "no such user")
   2. preAuthenticationChecks.check(user)
        -- isAccountNonExpired(), isAccountNonLocked()  -- checked BEFORE the password
   3. passwordEncoder.matches(rawPassword, user.getPassword())
        -- IF false: throw BadCredentialsException (the SAME exception type as step 1's masked case)
   4. postAuthenticationChecks.check(user)
        -- isCredentialsNonExpired(), isEnabled()  -- checked AFTER the password
   5. IF passwordEncoder.upgradeEncoding(user.getPassword()): upgrade (via UserDetailsPasswordService, if registered)
   6. return a NEW, verified Authentication carrying user.getAuthorities()
```

A missing user and a wrong password both terminate in the identical `BadCredentialsException` — by design, not by accident.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DaoAuthenticationProvider loads the user runs pre authentication checks verifies the password runs post authentication checks and finally checks for a password upgrade a missing user and an incorrect password both funnel into the identical BadCredentialsException by design">
  <rect x="15" y="20" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="90" y="41" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">retrieveUser</text>

  <rect x="15" y="63" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="90" y="84" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">preAuthenticationChecks</text>

  <rect x="15" y="106" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="90" y="127" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">password matches?</text>

  <rect x="15" y="149" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="90" y="170" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">postAuthenticationChecks</text>

  <rect x="440" y="60" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="530" y="86" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BadCredentialsException</text>

  <rect x="440" y="140" width="180" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="530" y="166" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">verified Authentication</text>

  <defs><marker id="a46" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="37" x2="440" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a46)"/>
  <line x1="165" y1="123" x2="440" y2="82" stroke="#8b949e" stroke-width="1" marker-end="url(#a46)"/>
  <line x1="165" y1="166" x2="440" y2="160" stroke="#8b949e" stroke-width="1" marker-end="url(#a46)"/>
</svg>

Two very different failure causes (missing user, wrong password), both routed into the identical exception box on the right.

## 5. Runnable example

The scenario: implement the full `DaoAuthenticationProvider`-style pipeline, prove a missing user and a wrong password are indistinguishable to the caller, then add the pre/post-check ordering distinction, then wire in an upgrade check as the final step, tying the whole authentication section's pieces together.

### Level 1 — Basic

The core pipeline, demonstrating the deliberate exception-masking behavior directly.

```java
import java.util.*;

public class DaoProviderLevel1 {
    record UserDetails(String username, String password, boolean enabled) {}
    static Map<String, UserDetails> userStore = Map.of("alice", new UserDetails("alice", "hashed-hunter2", true));

    static class BadCredentialsException extends RuntimeException {
        BadCredentialsException() { super("Bad credentials"); } // ALWAYS the same generic message
    }

    static UserDetails retrieveUser(String username) {
        UserDetails found = userStore.get(username);
        if (found == null) throw new BadCredentialsException(); // masked -- NOT a distinguishable "no such user"
        return found;
    }

    static void authenticate(String username, String rawPassword) {
        UserDetails user = retrieveUser(username); // throws the SAME exception if username doesn't exist
        if (!("hashed-" + rawPassword).equals(user.password())) throw new BadCredentialsException(); // SAME exception again
        System.out.println("authenticated as " + user.username());
    }

    public static void main(String[] args) {
        try { authenticate("nonexistent-user", "anything"); }
        catch (BadCredentialsException ex) { System.out.println("caught: " + ex.getMessage()); }

        try { authenticate("alice", "wrongpassword"); }
        catch (BadCredentialsException ex) { System.out.println("caught: " + ex.getMessage()); }
    }
}
```

How to run: `java DaoProviderLevel1.java`

Both `catch` blocks print the *identical* message, `"Bad credentials"` — a caller (or an attacker probing the login endpoint) receiving this response has no way to distinguish "that username doesn't exist" from "that username exists but the password was wrong," exactly the deliberate ambiguity `hideUserNotFoundExceptions` (enabled by default) provides.

### Level 2 — Intermediate

Add the pre/post-check ordering distinction: account expiry and locking are checked *before* the password; credential expiry and enabled status are checked *after*.

```java
import java.util.*;

public class DaoProviderLevel2 {
    record UserDetails(String username, String password, boolean accountExpired, boolean accountLocked,
                        boolean credentialsExpired, boolean disabled) {}

    static class AccountStatusException extends RuntimeException { AccountStatusException(String m) { super(m); } }
    static class BadCredentialsException extends RuntimeException { BadCredentialsException() { super("Bad credentials"); } }

    static void preAuthenticationChecks(UserDetails user) {
        if (user.accountExpired()) throw new AccountStatusException("account expired");
        if (user.accountLocked()) throw new AccountStatusException("account locked");
    }

    static void postAuthenticationChecks(UserDetails user) {
        if (user.credentialsExpired()) throw new AccountStatusException("credentials expired");
        if (user.disabled()) throw new AccountStatusException("account disabled");
    }

    static void authenticate(UserDetails user, String rawPassword) {
        preAuthenticationChecks(user); // BEFORE the password check
        if (!("hashed-" + rawPassword).equals(user.password())) throw new BadCredentialsException();
        postAuthenticationChecks(user); // AFTER the password check
        System.out.println("authenticated as " + user.username());
    }

    public static void main(String[] args) {
        // account is LOCKED -- rejected by the PRE-check, WITHOUT the password ever being checked at all
        UserDetails locked = new UserDetails("bob", "hashed-CORRECT-password", false, true, false, false);
        try {
            authenticate(locked, "totally-wrong-guess"); // even a WRONG guess never reaches the password check
        } catch (AccountStatusException ex) {
            System.out.println("bob (locked): " + ex.getMessage() + " (password was never even evaluated)");
        }
    }
}
```

How to run: `java DaoProviderLevel2.java`

`authenticate` calls `preAuthenticationChecks` before ever comparing passwords — bob's account being locked is detected and thrown immediately, meaning the (deliberately wrong) password guess passed in never actually gets evaluated at all, demonstrating that pre-checks short-circuit the entire rest of the flow, including the password comparison itself.

### Level 3 — Advanced

Wire in the full pipeline including a final upgrade check, tying together `UserDetails`, `PasswordEncoder`-style verification, account checks, and `UserDetailsPasswordService`-style persistence from the earlier cards in this section.

```java
import java.util.*;

public class DaoProviderLevel3 {
    record UserDetails(String username, String password, int costFactor, boolean enabled) {}

    static Map<String, UserDetails> userStore = new HashMap<>();
    static final int CURRENT_COST_FACTOR = 12;

    static class BadCredentialsException extends RuntimeException { BadCredentialsException() { super("Bad credentials"); } }
    static class DisabledException extends RuntimeException { DisabledException() { super("Account disabled"); } }

    static boolean passwordMatches(String raw, UserDetails user) {
        return ("hashed-" + raw).equals(user.password()); // a real (if simplified) comparison, not a hard-coded stand-in
    }
    static boolean upgradeEncoding(UserDetails user) { return user.costFactor() < CURRENT_COST_FACTOR; }

    static void persistUpgrade(String username, String rawPassword) {
        UserDetails existing = userStore.get(username);
        userStore.put(username, new UserDetails(username, existing.password(), CURRENT_COST_FACTOR, existing.enabled()));
        System.out.println("  (upgraded " + username + " from cost=" + existing.costFactor() + " to cost=" + CURRENT_COST_FACTOR + ")");
    }

    static String authenticate(String username, String rawPassword) {
        UserDetails user = userStore.get(username);
        if (user == null) throw new BadCredentialsException(); // masked, same as a wrong password below

        if (!passwordMatches(rawPassword, user)) throw new BadCredentialsException();

        if (!user.enabled()) throw new DisabledException(); // POST-check, runs after password verification

        if (upgradeEncoding(user)) persistUpgrade(username, rawPassword);

        return "200 OK, authenticated as " + username;
    }

    public static void main(String[] args) {
        userStore.put("carol", new UserDetails("carol", "hashed-p@ssw0rd", 8, true)); // OLD cost factor

        System.out.println(authenticate("carol", "p@ssw0rd"));
        System.out.println("carol's stored cost factor now: " + userStore.get("carol").costFactor());

        System.out.println(authenticate("carol", "p@ssw0rd")); // second login: ALREADY upgraded, no further change
        System.out.println("carol's stored cost factor still: " + userStore.get("carol").costFactor());
    }
}
```

How to run: `java DaoProviderLevel3.java`

carol's first login verifies her password, passes the enabled-status post-check, and finds `upgradeEncoding` true (her stored `costFactor` is `8`), triggering `persistUpgrade`; her second login, using the identical password, now finds `upgradeEncoding` false (her `costFactor` is already `12`), so no further upgrade happens — the whole pipeline (load, verify, check, upgrade) runs correctly for both calls, with the upgrade step only actually firing once.

## 6. Walkthrough

Trace `authenticate("carol", "p@ssw0rd")` for carol's *first* login in Level 3.

1. `user = userStore.get("carol")` retrieves `UserDetails("carol", "hashed-p@ssw0rd", 8, true)` — non-null, so the `BadCredentialsException` guard for a missing user is skipped.
2. `passwordMatches("p@ssw0rd", user)` evaluates `("hashed-" + "p@ssw0rd").equals(user.password())`, i.e. `"hashed-p@ssw0rd".equals("hashed-p@ssw0rd")`, which is `true`; since the call returns `true`, the `if (!passwordMatches(...))` guard does not throw.
3. `!user.enabled()` evaluates `!true`, i.e. `false` — the `DisabledException` guard is skipped, since carol's account is enabled.
4. `upgradeEncoding(user)` checks `user.costFactor() < CURRENT_COST_FACTOR`, i.e. `8 < 12`, which is `true` — this triggers a call to `persistUpgrade("carol", "p@ssw0rd")`.
5. Inside `persistUpgrade`, `existing = userStore.get("carol")` retrieves the same record fetched in step 1; `userStore.put("carol", new UserDetails("carol", existing.password(), 12, existing.enabled()))` replaces carol's entry with an identical password but an updated `costFactor` of `12`, and a confirmation message is printed.
6. Back in `authenticate`, the method returns `"200 OK, authenticated as carol"` — this return value is identical regardless of whether the upgrade branch fired, since the upgrade is an opportunistic *side effect* of a successful authentication, never a condition for it.

```
authenticate("carol", "p@ssw0rd") [first call]:
  user found, not null            -> no BadCredentialsException
  password matches                -> no BadCredentialsException
  account enabled                 -> no DisabledException
  upgradeEncoding: 8 < 12 = true  -> persistUpgrade() -> costFactor now 12
  -> returns "200 OK, authenticated as carol"
```

## 7. Gotchas & takeaways

> **Gotcha:** setting `setHideUserNotFoundExceptions(false)` reveals, via a distinguishable exception type/message, whether a submitted username exists at all — this is a genuine username-enumeration vulnerability for any public-facing login form, letting an attacker efficiently build a list of valid accounts to target with further attacks (credential stuffing, targeted phishing). Leave this at its secure default (`true`) unless there is a specific, well-understood reason not to.

- `DaoAuthenticationProvider` is the concrete class tying together `UserDetailsService`, `PasswordEncoder`, account-state checks, and `UserDetailsPasswordService` into Spring Security's standard username/password authentication flow.
- Pre-authentication checks (account expiry, account locked) run *before* the password is verified; post-authentication checks (credentials expired, disabled) run *after* — a distinction relevant when reasoning about exactly what state is checked at what point in the flow.
- A missing username and an incorrect password are deliberately normalized into the identical `BadCredentialsException`, preventing an attacker from using response differences to enumerate valid usernames.
- The password-upgrade check (via `upgradeEncoding` and, if registered, `UserDetailsPasswordService`) is the final step of a successful authentication, running as an opportunistic side effect rather than a condition of the authentication succeeding.
