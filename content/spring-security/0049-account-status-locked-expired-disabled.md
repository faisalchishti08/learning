---
card: spring-security
gi: 49
slug: account-status-locked-expired-disabled
title: "Account status (locked, expired, disabled)"
---

## 1. What it is

Account status covers the three distinct, independently-meaningful `UserDetails` flags beyond credential correctness that `DaoAuthenticationProvider` enforces — `isAccountNonLocked()` (a security response to suspicious activity, like repeated failed login attempts), `isAccountNonExpired()` (the account's own validity window has ended, common for temporary contractor or trial accounts), and `isEnabled()` (an administrative on/off switch, used for suspensions or deactivated accounts) — each producing a distinct `AccountStatusException` subtype (`LockedException`, `AccountExpiredException`, `DisabledException`) so the specific reason for rejection is precisely identifiable internally, even while the client-facing response typically stays generic.

```java
public class MyUserDetails implements UserDetails {
    private final boolean locked;
    private final LocalDate accountExpiryDate;
    private final boolean enabled;

    public boolean isAccountNonLocked() { return !locked; }
    public boolean isAccountNonExpired() { return LocalDate.now().isBefore(accountExpiryDate); }
    public boolean isEnabled() { return enabled; }
    // isCredentialsNonExpired() covered separately -- a different concern (password age, not account validity)
}
```

## 2. Why & when

These three states answer three genuinely different business questions that a simple "can this password authenticate" check cannot express: locking answers "has this account shown signs of a security problem" (and is typically reversible once the concern is addressed — a fixed number of failed attempts, an administrator unlocking it); expiry answers "was this account only ever meant to be valid for a bounded time" (a contractor's access ending on a fixed date, a trial account's evaluation period); and enabled/disabled answers "has an administrator deliberately turned this account off" (a suspended account, a former employee's deactivated login). Keeping these as three separate, independently-checkable flags — rather than a single generic "is this account okay" boolean — lets an application (and its support/security teams) reason about, log, and resolve each condition according to its own distinct cause and remedy.

Reach for each specifically when:

- `isAccountNonLocked()` for temporary, automated security responses — a failed-login-attempt counter (paired with the earlier account-lockout concept from the username/password authentication card) that locks after N failures and unlocks after a cooldown period or administrator action.
- `isAccountNonExpired()` for accounts with an inherent, known validity window — a contractor's access tied to a contract end date, a trial subscription's evaluation period — where the account should stop working automatically once that date passes, without requiring any active administrative intervention.
- `isEnabled()` for deliberate, administrator-driven account state — suspending a user under investigation, deactivating a departed employee's account — a manual on/off switch rather than an automatic, time- or attempt-based condition.

## 3. Core concept

```
 LOCKED    -- typically AUTOMATIC, in response to suspicious activity (repeated failed logins)
              typically REVERSIBLE (cooldown expires, or an administrator explicitly unlocks it)
              throws: LockedException

 EXPIRED   -- typically tied to a KNOWN, PRE-DETERMINED validity window (a contract end date)
              becomes true AUTOMATICALLY once that date passes, with NO discrete "expiry event" needed
              throws: AccountExpiredException

 DISABLED  -- typically a DELIBERATE administrative action (a manual suspend/deactivate toggle)
              stays disabled until an administrator EXPLICITLY re-enables it
              throws: DisabledException

 all THREE are checked by DaoAuthenticationProvider ALONGSIDE the password check --
   any ONE being false denies authentication, REGARDLESS of password correctness
```

Three different causes, three different typical remedies, three different exception types — deliberately kept distinct rather than merged into one generic "account not okay" signal.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three independent account status conditions locked expired and disabled each with a different typical cause and remedy locked is an automatic reversible security response expired is tied to a known validity window and disabled is a deliberate administrative toggle all three are checked alongside password correctness">
  <rect x="15" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="105" y="40" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">LOCKED</text>
  <text x="105" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">automatic, reversible</text>

  <rect x="230" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="40" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">EXPIRED</text>
  <text x="320" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">known validity window</text>

  <rect x="445" y="20" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="535" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">DISABLED</text>
  <text x="535" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">deliberate admin toggle</text>

  <rect x="200" y="115" width="240" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="320" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">DaoAuthenticationProvider</text>
  <text x="320" y="148" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">checks ALL, alongside password</text>

  <defs><marker id="a49" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="105" y1="66" x2="270" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a49)"/>
  <line x1="320" y1="66" x2="320" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a49)"/>
  <line x1="535" y1="66" x2="370" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a49)"/>
</svg>

Three separate causes converge on the same enforcement point, but each retains its own distinct meaning and remedy.

## 5. Runnable example

The scenario: implement all three checks with realistic underlying logic (a failed-attempt counter for locking, a date comparison for expiry, a boolean flag for disabled), then run a scenario touching all three independently, then add automatic unlock-after-cooldown for the locked case, distinguishing it from expiry's one-way nature.

### Level 1 — Basic

Three independently-computed status checks, each derived from different underlying state.

```java
import java.time.LocalDate;
import java.util.*;

public class AccountStatusLevel1 {
    record Account(String username, int failedAttempts, LocalDate accessExpiryDate, boolean administratorDisabled) {}

    static boolean isAccountNonLocked(Account acc) { return acc.failedAttempts() < 3; }
    static boolean isAccountNonExpired(Account acc) { return LocalDate.now().isBefore(acc.accessExpiryDate()); }
    static boolean isEnabled(Account acc) { return !acc.administratorDisabled(); }

    public static void main(String[] args) {
        Account healthy = new Account("alice", 0, LocalDate.now().plusYears(1), false);
        Account lockedOut = new Account("bob", 3, LocalDate.now().plusYears(1), false);
        Account expiredContract = new Account("contractor1", 0, LocalDate.now().minusDays(1), false);
        Account suspended = new Account("carol", 0, LocalDate.now().plusYears(1), true);

        for (Account acc : List.of(healthy, lockedOut, expiredContract, suspended)) {
            System.out.println(acc.username() + ": nonLocked=" + isAccountNonLocked(acc)
                    + ", nonExpired=" + isAccountNonExpired(acc) + ", enabled=" + isEnabled(acc));
        }
    }
}
```

How to run: `java AccountStatusLevel1.java`

Each account demonstrates exactly one failing condition (or none): bob has 3 failed attempts, tripping `isAccountNonLocked`; the contractor's `accessExpiryDate` is in the past, tripping `isAccountNonExpired`; carol has `administratorDisabled = true`, tripping `isEnabled` — each flag is computed entirely independently of the others.

### Level 2 — Intermediate

Wire all three checks into a full authentication flow, throwing the correct, distinct exception type for each failure.

```java
import java.time.LocalDate;
import java.util.*;

public class AccountStatusLevel2 {
    record Account(String username, String password, int failedAttempts, LocalDate accessExpiryDate, boolean administratorDisabled) {}

    static class LockedException extends RuntimeException { LockedException(String m) { super(m); } }
    static class AccountExpiredException extends RuntimeException { AccountExpiredException(String m) { super(m); } }
    static class DisabledException extends RuntimeException { DisabledException(String m) { super(m); } }
    static class BadCredentialsException extends RuntimeException { BadCredentialsException() { super("Bad credentials"); } }

    static void authenticate(Account acc, String rawPassword) {
        if (acc.failedAttempts() >= 3) throw new LockedException("account locked after " + acc.failedAttempts() + " failed attempts");
        if (!LocalDate.now().isBefore(acc.accessExpiryDate())) throw new AccountExpiredException("account expired on " + acc.accessExpiryDate());
        if (acc.administratorDisabled()) throw new DisabledException("account disabled by an administrator");
        if (!("hashed-" + rawPassword).equals(acc.password())) throw new BadCredentialsException();
        System.out.println(acc.username() + ": authenticated successfully");
    }

    public static void main(String[] args) {
        Account lockedOut = new Account("bob", "hashed-correctpass", 3, LocalDate.now().plusYears(1), false);
        try {
            authenticate(lockedOut, "correctpass"); // CORRECT password -- but locked BEFORE the password is even checked
        } catch (RuntimeException ex) {
            System.out.println("bob: " + ex.getClass().getSimpleName() + " -- " + ex.getMessage());
        }
    }
}
```

How to run: `java AccountStatusLevel2.java`

Even with the *correct* password supplied, bob's account is rejected by the `LockedException` check, which runs *before* the password comparison — the exception's specific type (`LockedException`, not the generic `BadCredentialsException`) is preserved internally for logging and support purposes, even though a client-facing response would typically still present a generic message.

### Level 3 — Advanced

Add automatic unlock-after-cooldown for the locked case, contrasting its time-based *reversibility* with expiry's genuinely one-way nature (an expired account never automatically becomes valid again without deliberate administrative action to extend the expiry date).

```java
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.*;

public class AccountStatusLevel3 {
    record Account(String username, int failedAttempts, LocalDateTime lockedAt, LocalDate accessExpiryDate) {}

    static final int COOLDOWN_MINUTES = 30;

    // LOCKED is TIME-REVERSIBLE: once the cooldown has passed, the account is automatically unlocked again
    static boolean isAccountNonLocked(Account acc, LocalDateTime now) {
        if (acc.failedAttempts() < 3) return true; // never locked in the first place
        return acc.lockedAt().plusMinutes(COOLDOWN_MINUTES).isBefore(now); // cooldown has ELAPSED -- auto-unlocked
    }

    // EXPIRED is NOT time-reversible in the same way -- it only ever gets WORSE (more expired) as time passes,
    // never automatically becomes valid again without an administrator extending accessExpiryDate itself
    static boolean isAccountNonExpired(Account acc, LocalDate today) {
        return today.isBefore(acc.accessExpiryDate());
    }

    public static void main(String[] args) {
        LocalDateTime lockTime = LocalDateTime.of(2024, 1, 1, 12, 0);
        Account lockedAccount = new Account("bob", 3, lockTime, LocalDate.of(2030, 1, 1));

        LocalDateTime tenMinutesLater = lockTime.plusMinutes(10);
        LocalDateTime fortyMinutesLater = lockTime.plusMinutes(40);

        System.out.println("10 min after lock: nonLocked=" + isAccountNonLocked(lockedAccount, tenMinutesLater));
        System.out.println("40 min after lock: nonLocked=" + isAccountNonLocked(lockedAccount, fortyMinutesLater)
                + " (cooldown elapsed -- AUTOMATICALLY unlocked, no admin action needed)");

        Account expiredContractor = new Account("contractor1", 0, null, LocalDate.of(2020, 1, 1));
        System.out.println();
        System.out.println("contractor, checked in 2020: nonExpired=" + isAccountNonExpired(expiredContractor, LocalDate.of(2019, 12, 31)));
        System.out.println("contractor, checked in 2025: nonExpired=" + isAccountNonExpired(expiredContractor, LocalDate.of(2025, 1, 1))
                + " (STILL expired -- more time passing NEVER un-expires it, unlike locking's cooldown)");
    }
}
```

How to run: `java AccountStatusLevel3.java`

The locked account automatically becomes `nonLocked=true` again once 30 minutes have elapsed since the lock, purely through the passage of time, requiring no administrator action; the expired contractor's account, checked at two different points both *after* its expiry date, remains expired in both cases — time passing only ever moves further away from validity for an expired account, never back toward it, a fundamentally different temporal relationship than locking's cooldown-based reversibility.

## 6. Walkthrough

Trace `isAccountNonLocked(lockedAccount, fortyMinutesLater)` from Level 3.

1. `acc.failedAttempts()` is `3`, so `acc.failedAttempts() < 3` evaluates to `false` — the method does not take the early "never locked" return and proceeds to the cooldown calculation.
2. `acc.lockedAt().plusMinutes(COOLDOWN_MINUTES)` computes `lockTime.plusMinutes(30)`, i.e. `2024-01-01T12:30`, representing the exact moment the cooldown period ends.
3. `.isBefore(now)` checks whether this cooldown-end time (`12:30`) is before `now`, which for this call is `fortyMinutesLater` (`2024-01-01T12:40`) — since `12:30` is indeed before `12:40`, this returns `true`.
4. The method returns `true`, meaning the account is considered non-locked (i.e., unlocked) at this point in time — purely as a function of how much time has elapsed since `lockedAt`, with no separate "unlock" action having been recorded anywhere.
5. Contrast this with the call using `tenMinutesLater` (`12:10`): `acc.lockedAt().plusMinutes(30)` is still `12:30`, and `12:30.isBefore(12:10)` is `false` — at only 10 minutes past the lock, the cooldown has not yet elapsed, so the account remains locked; the *only* difference between the two calls is the `now` value passed in, demonstrating that lock status is a pure, recomputable function of elapsed time rather than a persisted "is locked" flag that would need an explicit unlock write to change.

```
lockedAt = 12:00, COOLDOWN_MINUTES = 30 -> cooldown ends at 12:30

now = 12:10 (10 min later): 12:30.isBefore(12:10) = false -> STILL LOCKED
now = 12:40 (40 min later): 12:30.isBefore(12:40) = true  -> AUTOMATICALLY UNLOCKED (cooldown elapsed)
```

## 7. Gotchas & takeaways

> **Gotcha:** implementing `isAccountNonLocked` as a persisted boolean flag that's set to `true` once and never re-evaluated (rather than a live, recomputed function of elapsed time since the lock event) requires a separate scheduled job or explicit administrator action to ever unlock an account again — losing the "automatic unlock after cooldown" behavior that makes time-based lockout a genuinely self-healing security measure rather than a permanent, unintentional lockout.

- Locked, expired, and disabled represent three genuinely distinct conditions with different typical causes and remedies — locking is usually automatic and time-reversible, expiry is tied to a known validity window and does not self-heal, and disabled status is a deliberate, manual administrative toggle.
- All three are checked by `DaoAuthenticationProvider` independently of, and in addition to, password correctness — a correct password never overrides any one of these failing.
- Implementing locked status as a live computation over elapsed time (rather than a static, persisted flag) provides automatic cooldown-based unlocking with no separate administrative or scheduled action required.
- Preserving the specific exception type (`LockedException` vs. `AccountExpiredException` vs. `DisabledException`) internally — even while presenting a generic message to the end client — is valuable for logging, support diagnostics, and security monitoring, without compromising the username-enumeration protections discussed in the `DaoAuthenticationProvider` card.
