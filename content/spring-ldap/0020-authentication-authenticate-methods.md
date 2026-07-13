---
card: spring-ldap
gi: 20
slug: authentication-authenticate-methods
title: "Authentication (authenticate methods)"
---

## 1. What it is

`LdapTemplate.authenticate(...)` checks whether a given set of credentials (a search filter identifying a user, plus a password) can successfully bind to the directory, without leaving the application holding a long-lived, user-authenticated context afterward. It comes in a couple of overloads — one taking a base and filter plus password, and another taking a fully-built `LdapQuery` (card 0011) — and internally performs a search to resolve the user's DN, then attempts a bind as that DN with the supplied password, reporting only true/false success.

## 2. Why & when

Verifying a username/password pair against LDAP is a distinct operation from every other `LdapTemplate` method covered so far — it's not reading data or writing data, it's testing whether a bind succeeds, which is exactly what "checking a password" means in LDAP terms. Doing this manually (searching for the user's DN with the admin-bound template, then separately opening a brand-new `DirContext` bound as that DN and that password to see if it succeeds) is exactly the kind of repetitive, error-prone plumbing `LdapTemplate` exists to hide — `authenticate` wraps that whole sequence into one method call with a boolean result.

Use `authenticate` when:

- Implementing a login flow where users authenticate against an LDAP directory rather than an application-managed password store.
- Verifying a password for a re-authentication step (confirming a user's current password before a sensitive account change) without needing anything else from the directory for that check.

## 3. Core concept

Think of `authenticate` as a bouncer checking an ID card against both a guest list and a claimed password on the spot — the bouncer looks up which guest the presented ID (the search filter, resolving to one entry) actually refers to, then tests whether the claimed password actually opens that specific guest's account, and reports only "yes, this checks out" or "no, it doesn't" — without letting the bouncer's own credentials or the guest's temporarily-verified access persist as some ongoing session the rest of the venue can rely on afterward.

```java
boolean valid = ldapTemplate.authenticate(
    "ou=people",
    "(uid=jsmith)",
    "theClaimedPassword"
);
```

Internally, this performs (1) a search using the admin-bound context to resolve exactly which entry matches the filter and obtain its DN, then (2) a separate bind attempt using that resolved DN and the supplied password — success of that second bind is what `authenticate` reports as `true`; any failure (wrong password, or the search matching zero or more than one entry) reports `false`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="authenticate resolves a DN via search using the admin context, then attempts a separate bind as that DN with the supplied password">
  <rect x="20" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. search(filter)</text>

  <line x1="200" y1="55" x2="240" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#p1)"/>

  <rect x="250" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">resolve DN of match</text>

  <line x1="340" y1="80" x2="340" y2="115" stroke="#79c0ff" stroke-width="2" marker-end="url(#p2)"/>

  <rect x="250" y="120" width="180" height="50" rx="6" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="340" y="150" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. bind(dn, password)</text>

  <text x="340" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">success/failure of THIS bind is the returned boolean</text>

  <defs>
    <marker id="p1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="p2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`authenticate` is a search-then-bind sequence, boiled down to a single boolean outcome from the second bind.

## 5. Runnable example

The scenario: a login check, starting with the basic overload, then guarding against ambiguous matches, and finally adding a rate limit against repeated failed attempts for the same account.

### Level 1 — Basic

```java
// BasicAuthCheck.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;

public class BasicAuthCheck {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com"); // used only for the initial search step
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        boolean valid = template.authenticate("ou=people", "(uid=jsmith)", "userSecret123");
        System.out.println("Login valid: " + valid);
    }
}
```

**How to run:** run against a directory with `uid=jsmith` whose password is `userSecret123`. Expected output: `Login valid: true` for the correct password, and `Login valid: false` if run again with a wrong password.

### Level 2 — Intermediate

If the filter accidentally matches more than one entry (a data-quality issue, or a poorly chosen filter), `authenticate`'s behavior in that ambiguous case shouldn't be trusted blindly — wrapping the filter construction through `LdapQueryBuilder` and checking uniqueness explicitly beforehand makes the login check more defensible.

```java
// SafeLoginService.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

public class SafeLoginService {
    private final LdapTemplate template;

    public SafeLoginService(LdapTemplate template) {
        this.template = template;
    }

    public boolean login(String uid, String password) {
        // EqualsFilter-backed .is(...) avoids the LDAP injection risk from card 0010's filter discussion.
        LdapQuery query = query().base("ou=people").where("uid").is(uid);

        long matchCount = template.search(query, (Object obj) -> obj).size();
        if (matchCount != 1) {
            // Zero matches (no such user) or more than one (a data problem) — never proceed to authenticate().
            return false;
        }

        return template.authenticate(query, password);
    }
}
```

**How to run:** call `login("jsmith", "userSecret123")` — expect `true` when exactly one matching entry exists and the password is correct. Simulate a duplicate `uid=jsmith` (as in card 0015's duplicate scenario) and call `login("jsmith", "userSecret123")` again: expect `false` regardless of whether either duplicate's password matches, since the explicit uniqueness check short-circuits before ever attempting the underlying bind — avoiding whatever ambiguous or server-dependent behavior `authenticate` might otherwise exhibit against multiple matches.

### Level 3 — Advanced

Repeated failed login attempts against the same account are a real attack pattern (password guessing) that an LDAP-backed login flow needs to slow down, independent of whatever rate limiting the directory server itself might or might not enforce. This level adds an in-application attempt counter with a cooldown, on top of the safe uniqueness-checked authentication from Level 2.

```java
// RateLimitedLoginService.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class RateLimitedLoginService {
    private final LdapTemplate template;
    private final Map<String, FailureRecord> failures = new ConcurrentHashMap<>();
    private static final int MAX_ATTEMPTS = 5;
    private static final long COOLDOWN_SECONDS = 60;

    private record FailureRecord(int count, Instant lockedUntil) {}

    public RateLimitedLoginService(LdapTemplate template) {
        this.template = template;
    }

    public enum Result { SUCCESS, INVALID_CREDENTIALS, LOCKED_OUT }

    public Result login(String uid, String password) {
        FailureRecord record = failures.get(uid);
        if (record != null && record.lockedUntil() != null && Instant.now().isBefore(record.lockedUntil())) {
            return Result.LOCKED_OUT;
        }

        LdapQuery query = query().base("ou=people").where("uid").is(uid);
        long matchCount = template.search(query, (Object obj) -> obj).size();

        boolean success = matchCount == 1 && template.authenticate(query, password);

        if (success) {
            failures.remove(uid); // clear any prior failure history on a successful login
            return Result.SUCCESS;
        } else {
            int newCount = (record == null ? 0 : record.count()) + 1;
            Instant lockUntil = newCount >= MAX_ATTEMPTS ? Instant.now().plusSeconds(COOLDOWN_SECONDS) : null;
            failures.put(uid, new FailureRecord(newCount, lockUntil));
            return lockUntil != null ? Result.LOCKED_OUT : Result.INVALID_CREDENTIALS;
        }
    }
}
```

**How to run:** call `login("jsmith", "wrongpassword")` five times in a row — expect `INVALID_CREDENTIALS` for the first four, then `LOCKED_OUT` on the fifth (and any further attempts within 60 seconds, even with the *correct* password). After the cooldown elapses, call `login("jsmith", "userSecret123")`: expect `SUCCESS`, with the failure history cleared.

## 6. Walkthrough

Tracing the sequence of five failed logins followed by a lockout attempt with the correct password, in execution order:

1. Attempts 1–4 with the wrong password: each call finds no existing `FailureRecord` blocking it (or one below the threshold), proceeds to `template.authenticate(query, "wrongpassword")`, which internally resolves `jsmith`'s DN via search and attempts a bind with the wrong password — the bind fails, `authenticate` returns `false`, and `login` increments the stored `FailureRecord`'s count each time, returning `Result.INVALID_CREDENTIALS`.
2. Attempt 5: the `FailureRecord` count reaches `MAX_ATTEMPTS` (5) after this failed attempt, so `lockUntil` is set to 60 seconds from now, and the method returns `Result.LOCKED_OUT` — importantly, this determination happens *after* the failed authentication attempt itself completes for this 5th call, since it's the one that crosses the threshold.
3. A 6th attempt, even supplying the *correct* password: the very first check, `record.lockedUntil() != null && Instant.now().isBefore(record.lockedUntil())`, is now true, so the method returns `Result.LOCKED_OUT` immediately — critically, `template.authenticate(...)` is never even called this time, meaning the correct password never gets a chance to succeed until the cooldown expires, regardless of how correct it is.
4. Once 60 seconds have elapsed, a subsequent call finds `Instant.now().isBefore(record.lockedUntil())` is now `false`, so the lockout no longer applies, and the login proceeds to the actual `authenticate` call — with the correct password this time, it succeeds, and `failures.remove(uid)` clears the account's failure history entirely.

```
attempt 1-4 (wrong pw): authenticate() -> false -> count++ -> INVALID_CREDENTIALS
attempt 5   (wrong pw): authenticate() -> false -> count reaches MAX -> lockedUntil set -> LOCKED_OUT
attempt 6   (correct pw, still within cooldown): lockedUntil check short-circuits -> LOCKED_OUT
                                                  (authenticate() never even called)
after cooldown (correct pw): lockedUntil check passes -> authenticate() -> true -> SUCCESS, history cleared
```

## 7. Gotchas & takeaways

> `authenticate`'s underlying search-then-bind sequence means a filter matching more than one entry has behavior that shouldn't be relied on without checking — always verify the search resolves to exactly one entry before treating an `authenticate` call's result as meaningful, exactly as shown in Level 2, rather than trusting `authenticate` alone to handle ambiguous matches sensibly.

- `authenticate` is the right tool specifically for "does this password work for this user," not for reading any other data about the user — it deliberately returns only a boolean, not the entry's attributes.
- The context used to perform the initial search (resolving the filter to a DN) is the application's own configured admin/service context (card 0002), not the user being authenticated — the user's credentials are only ever used for the second, separate bind attempt.
- Application-level rate limiting (Level 3) against repeated failed attempts is worth adding independent of whatever protections the directory server itself might have, since a login flow is a natural target for password-guessing attempts and the application is well-positioned to slow that down per-account.
- Once locked out, avoid even attempting the underlying `authenticate` call — checking the lockout state first (as in Level 3) means a correct password submitted during a cooldown period still correctly results in denial, not a confusing race between "your password would have worked" and "you're locked out."
- Clear any accumulated failure history on a successful login — a lingering failure count from unrelated past attempts shouldn't count against a user indefinitely once they've successfully proven their credentials.
