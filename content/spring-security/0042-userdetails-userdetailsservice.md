---
card: spring-security
gi: 42
slug: userdetails-userdetailsservice
title: "UserDetails & UserDetailsService"
---

## 1. What it is

`UserDetails` is the interface representing everything Spring Security needs to know about a stored user for authentication purposes — username, hashed password, granted authorities, and four account-state flags (`isAccountNonExpired`, `isAccountNonLocked`, `isCredentialsNonExpired`, `isEnabled`) — and `UserDetailsService` is the single-method interface (`loadUserByUsername(username)`) that fetches one, from wherever an application actually stores its users (an in-memory map, a relational database, an LDAP directory, an external API).

```java
public interface UserDetails extends Serializable {
    String getUsername();
    String getPassword();
    Collection<? extends GrantedAuthority> getAuthorities();
    boolean isAccountNonExpired();
    boolean isAccountNonLocked();
    boolean isCredentialsNonExpired();
    boolean isEnabled();
}

public interface UserDetailsService {
    UserDetails loadUserByUsername(String username) throws UsernameNotFoundException;
}
```

## 2. Why & when

`DaoAuthenticationProvider` needs a uniform way to ask "what does the stored record for this username look like" without caring at all whether that record lives in a `HashMap`, a SQL table, or a call to an external directory service — `UserDetailsService` is exactly that seam: implement its one method against whatever storage an application actually uses, and every other piece of Spring Security's authentication machinery (the provider, the four account-state checks, authority-based authorization) works identically regardless of the underlying storage technology. `UserDetails` itself is deliberately minimal and storage-agnostic — most applications wrap their own richer domain `User` entity (with an email, a display name, a created-at timestamp) in a small adapter class implementing `UserDetails`, rather than making their actual domain model implement the interface directly.

Reach for a custom `UserDetailsService` when:

- Building any real authentication setup beyond a quick in-memory prototype — a custom `UserDetailsService` backed by a JPA repository (or equivalent) is the standard way most applications connect their own user table into Spring Security.
- The application's own `User` entity carries additional fields (email, profile data) beyond what `UserDetails` requires — writing a thin adapter class implementing `UserDetails` and wrapping the real entity keeps the domain model clean while still satisfying the interface's contract.
- Understanding why a "correct password, but account still rejected" scenario happens — `DaoAuthenticationProvider` checks all four `UserDetails` boolean flags *in addition to* the password match, and any one of them returning `false` (an expired account, a locked account, expired credentials, a disabled account) causes rejection even with a perfectly matching password.

## 3. Core concept

```
 DaoAuthenticationProvider.authenticate(unverified):
   1. UserDetails stored = userDetailsService.loadUserByUsername(unverified.getName())
        -- throws UsernameNotFoundException if no such user exists at all
   2. passwordEncoder.matches(unverified.getCredentials(), stored.getPassword())
        -- MUST be true to proceed
   3. stored.isAccountNonExpired()      -- MUST be true (else: AccountExpiredException)
      stored.isAccountNonLocked()       -- MUST be true (else: LockedException)
      stored.isCredentialsNonExpired()  -- MUST be true (else: CredentialsExpiredException)
      stored.isEnabled()                -- MUST be true (else: DisabledException)
   4. IF ALL checks pass: build a VERIFIED Authentication carrying stored.getAuthorities()
```

Password correctness alone is necessary but not sufficient — every one of the four account-state flags is an independent, equally-enforced gate.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="UserDetailsService loads a UserDetails object for the submitted username DaoAuthenticationProvider then checks the password AND all four account state flags account non expired account non locked credentials non expired and enabled with any single failure rejecting authentication despite a correct password">
  <rect x="15" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">loadUserByUsername</text>
  <text x="90" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; UserDetails</text>

  <rect x="215" y="20" width="170" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="300" y="41" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">password matches?</text>

  <rect x="215" y="63" width="170" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="300" y="84" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">accountNonExpired?</text>

  <rect x="215" y="106" width="170" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="300" y="127" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">accountNonLocked?</text>

  <rect x="215" y="149" width="170" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="300" y="170" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">enabled?</text>

  <rect x="460" y="85" width="160" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="112" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">ALL true -&gt; authenticated</text>

  <defs><marker id="a42" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="93" x2="215" y2="37" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="165" y1="93" x2="215" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="165" y1="93" x2="215" y2="123" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="165" y1="93" x2="215" y2="166" stroke="#8b949e" stroke-width="1" marker-end="url(#a42)"/>
  <line x1="385" y1="108" x2="460" y2="108" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a42)"/>
</svg>

Four gates, all independent, all enforced together — a single failing flag denies authentication regardless of the others.

## 5. Runnable example

The scenario: implement `UserDetailsService` against an in-memory user store, wrapping a richer domain entity, then wire in `DaoAuthenticationProvider`-style enforcement of all four account-state flags, then show each individual flag causing rejection despite a correct password.

### Level 1 — Basic

A domain `User` entity, a thin `UserDetails` adapter wrapping it, and a minimal `UserDetailsService`.

```java
import java.util.*;

public class UserDetailsLevel1 {
    // the application's OWN, richer domain entity -- NOT itself a UserDetails implementation
    record DomainUser(String username, String email, String hashedPassword, Set<String> roles) {}

    interface UserDetails {
        String getUsername();
        String getPassword();
        Set<String> getAuthorities();
    }

    // a THIN adapter, wrapping the domain entity to satisfy UserDetails' contract
    static class UserDetailsAdapter implements UserDetails {
        private final DomainUser domainUser;
        UserDetailsAdapter(DomainUser domainUser) { this.domainUser = domainUser; }
        public String getUsername() { return domainUser.username(); }
        public String getPassword() { return domainUser.hashedPassword(); }
        public Set<String> getAuthorities() { return domainUser.roles(); }
    }

    interface UserDetailsService { UserDetails loadUserByUsername(String username); }

    static Map<String, DomainUser> userTable = Map.of(
            "alice", new DomainUser("alice", "alice@example.com", "hashed-hunter2", Set.of("ROLE_USER"))
    );

    static UserDetailsService userDetailsService = username -> {
        DomainUser found = userTable.get(username);
        if (found == null) throw new NoSuchElementException("no such user: " + username);
        return new UserDetailsAdapter(found);
    };

    public static void main(String[] args) {
        UserDetails loaded = userDetailsService.loadUserByUsername("alice");
        System.out.println("username: " + loaded.getUsername());
        System.out.println("authorities: " + loaded.getAuthorities());
    }
}
```

How to run: `java UserDetailsLevel1.java`

`UserDetailsAdapter` never duplicates any of `DomainUser`'s data — it simply delegates each `UserDetails` method to the wrapped entity's own fields, keeping the domain model's actual shape (which might have an email, a bio, timestamps) entirely separate from Spring Security's minimal, storage-agnostic contract.

### Level 2 — Intermediate

Add the four account-state flags to the adapter and enforce all of them, alongside the password check, in a `DaoAuthenticationProvider`-style flow.

```java
import java.util.*;

public class UserDetailsLevel2 {
    record DomainUser(String username, String hashedPassword, Set<String> roles,
                       boolean accountExpired, boolean accountLocked, boolean credentialsExpired, boolean disabled) {}

    interface UserDetails {
        String getUsername(); String getPassword(); Set<String> getAuthorities();
        boolean isAccountNonExpired(); boolean isAccountNonLocked(); boolean isCredentialsNonExpired(); boolean isEnabled();
    }

    static class UserDetailsAdapter implements UserDetails {
        private final DomainUser u;
        UserDetailsAdapter(DomainUser u) { this.u = u; }
        public String getUsername() { return u.username(); }
        public String getPassword() { return u.hashedPassword(); }
        public Set<String> getAuthorities() { return u.roles(); }
        public boolean isAccountNonExpired() { return !u.accountExpired(); }
        public boolean isAccountNonLocked() { return !u.accountLocked(); }
        public boolean isCredentialsNonExpired() { return !u.credentialsExpired(); }
        public boolean isEnabled() { return !u.disabled(); }
    }

    static Map<String, DomainUser> userTable = new HashMap<>();

    static class AuthenticationException extends RuntimeException { AuthenticationException(String m) { super(m); } }

    static String authenticate(String username, String rawPassword) {
        DomainUser found = userTable.get(username);
        if (found == null) throw new AuthenticationException("no such user");
        UserDetails details = new UserDetailsAdapter(found);

        if (!("hashed-" + rawPassword).equals(details.getPassword())) throw new AuthenticationException("bad credentials");
        if (!details.isAccountNonExpired()) throw new AuthenticationException("account expired");
        if (!details.isAccountNonLocked()) throw new AuthenticationException("account locked");
        if (!details.isCredentialsNonExpired()) throw new AuthenticationException("credentials expired");
        if (!details.isEnabled()) throw new AuthenticationException("account disabled");

        return "authenticated as " + details.getUsername() + " with " + details.getAuthorities();
    }

    public static void main(String[] args) {
        userTable.put("alice", new DomainUser("alice", "hashed-hunter2", Set.of("ROLE_USER"), false, false, false, false));

        System.out.println(authenticate("alice", "hunter2"));
    }
}
```

How to run: `java UserDetailsLevel2.java`

With all four flags `false` (meaning nothing is expired, locked, or disabled), `isAccountNonExpired()` and friends all return `true`, and alice's correct password lets her through every check — the method returns the success message.

### Level 3 — Advanced

Demonstrate each of the four flags independently causing rejection despite an otherwise-correct password, proving each gate is checked and enforced separately.

```java
import java.util.*;

public class UserDetailsLevel3 {
    record DomainUser(String username, String hashedPassword, Set<String> roles,
                       boolean accountExpired, boolean accountLocked, boolean credentialsExpired, boolean disabled) {}

    interface UserDetails {
        String getUsername(); String getPassword(); Set<String> getAuthorities();
        boolean isAccountNonExpired(); boolean isAccountNonLocked(); boolean isCredentialsNonExpired(); boolean isEnabled();
    }

    static class UserDetailsAdapter implements UserDetails {
        private final DomainUser u;
        UserDetailsAdapter(DomainUser u) { this.u = u; }
        public String getUsername() { return u.username(); }
        public String getPassword() { return u.hashedPassword(); }
        public Set<String> getAuthorities() { return u.roles(); }
        public boolean isAccountNonExpired() { return !u.accountExpired(); }
        public boolean isAccountNonLocked() { return !u.accountLocked(); }
        public boolean isCredentialsNonExpired() { return !u.credentialsExpired(); }
        public boolean isEnabled() { return !u.disabled(); }
    }

    static String authenticate(DomainUser found, String rawPassword) {
        UserDetails details = new UserDetailsAdapter(found);
        if (!("hashed-" + rawPassword).equals(details.getPassword())) return "REJECTED: bad credentials";
        if (!details.isAccountNonExpired()) return "REJECTED: account expired";
        if (!details.isAccountNonLocked()) return "REJECTED: account locked";
        if (!details.isCredentialsNonExpired()) return "REJECTED: credentials expired (password needs reset)";
        if (!details.isEnabled()) return "REJECTED: account disabled";
        return "ACCEPTED: authenticated as " + details.getUsername();
    }

    public static void main(String[] args) {
        String correctPassword = "hunter2";

        DomainUser expiredAccount = new DomainUser("u1", "hashed-hunter2", Set.of(), true, false, false, false);
        DomainUser lockedAccount = new DomainUser("u2", "hashed-hunter2", Set.of(), false, true, false, false);
        DomainUser expiredCreds = new DomainUser("u3", "hashed-hunter2", Set.of(), false, false, true, false);
        DomainUser disabledAccount = new DomainUser("u4", "hashed-hunter2", Set.of(), false, false, false, true);
        DomainUser healthyAccount = new DomainUser("u5", "hashed-hunter2", Set.of(), false, false, false, false);

        for (DomainUser u : List.of(expiredAccount, lockedAccount, expiredCreds, disabledAccount, healthyAccount)) {
            System.out.println(u.username() + " (correct password): " + authenticate(u, correctPassword));
        }
    }
}
```

How to run: `java UserDetailsLevel3.java`

Every single account in this run receives the *identical* correct password, `"hunter2"` — yet only `healthyAccount` (`u5`) is accepted; each of the other four is rejected for a completely different reason, demonstrating that `DaoAuthenticationProvider`'s account-state checks are independent, mandatory gates layered on top of (never replacing) the password check.

## 6. Walkthrough

Trace `authenticate(expiredCreds, "hunter2")` from Level 3.

1. `details = new UserDetailsAdapter(expiredCreds)` wraps the domain entity; `expiredCreds` has `credentialsExpired = true` and all other boolean fields `false`.
2. `!("hashed-" + "hunter2").equals(details.getPassword())` checks `!"hashed-hunter2".equals("hashed-hunter2")`, which is `!true`, i.e. `false` — so this first guard does *not* trigger a rejection; the password is correct.
3. `!details.isAccountNonExpired()` calls `isAccountNonExpired()`, which returns `!u.accountExpired()`, i.e. `!false`, i.e. `true`; negating that for the guard gives `!true = false` — this guard also does not trigger.
4. `!details.isAccountNonLocked()` similarly evaluates to `false` — not triggered.
5. `!details.isCredentialsNonExpired()` calls `isCredentialsNonExpired()`, which returns `!u.credentialsExpired()`, i.e. `!true`, i.e. `false`; negating that for the guard gives `!false = true` — *this* guard triggers, and the method returns `"REJECTED: credentials expired (password needs reset)"` immediately, without ever reaching the `isEnabled()` check.
6. This demonstrates the checks run in a fixed sequence and stop at the *first* failing gate — even though `expiredCreds`'s password was entirely correct and her account isn't expired or locked, the credentials-expired flag alone is sufficient to deny authentication, exactly modeling a real-world "your password has expired, please reset it" scenario.

```
u1 (accountExpired=true):       password OK -> accountNonExpired FALSE -> REJECTED: account expired
u2 (accountLocked=true):        password OK, not expired -> accountNonLocked FALSE -> REJECTED: account locked
u3 (credentialsExpired=true):   password OK, not expired/locked -> credentialsNonExpired FALSE -> REJECTED: credentials expired
u4 (disabled=true):             password OK, all prior checks pass -> enabled FALSE -> REJECTED: account disabled
u5 (all flags false):           password OK, ALL checks pass -> ACCEPTED
```

## 7. Gotchas & takeaways

> **Gotcha:** a `UserDetailsService` implementation that always returns `true` for all four account-state flags (a common shortcut when first wiring up a custom implementation) silently disables all of this enforcement — a locked or disabled account in the application's *own* domain data would still successfully authenticate, since `UserDetailsAdapter` never actually reflects that domain state into the flags Spring Security checks. Always wire the adapter's flags to genuinely reflect the underlying domain entity's real state.

- `UserDetailsService`'s single method is the seam between Spring Security's authentication machinery and whatever storage technology an application actually uses — implement it once, correctly, and every other security feature works uniformly regardless of the backing store.
- `UserDetails` is deliberately minimal; wrapping a richer domain entity in a thin adapter class is the standard, recommended pattern, keeping the domain model free of framework-specific interface requirements.
- All four account-state flags are checked *in addition to* password correctness, each independently capable of denying authentication — a correct password is necessary but never sufficient on its own.
- `UsernameNotFoundException` (thrown by `loadUserByUsername` when no such user exists) and a password mismatch both ultimately produce the same generic `BadCredentialsException` to the caller, deliberately avoiding leaking "this username doesn't exist" versus "this password is wrong" as distinguishable outcomes to a potential attacker.
