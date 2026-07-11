---
card: spring-security
gi: 10
slug: grantedauthority
title: "GrantedAuthority"
---

## 1. What it is

`GrantedAuthority` is the single-method interface (`getAuthority()`, returning a `String`) representing one permission a user has been granted, held as a `Collection<? extends GrantedAuthority>` on every `Authentication` object — by loose convention, role-style authorities are prefixed `ROLE_` (`ROLE_ADMIN`, `ROLE_USER`) while finer-grained permission-style authorities are typically unprefixed (`orders:read`, `orders:write`), and Spring Security's `hasRole("ADMIN")` authorization check is itself just a convenience wrapper that automatically checks for `hasAuthority("ROLE_ADMIN")` underneath, prepending the `ROLE_` prefix so calling code doesn't need to type it repeatedly.

```java
Collection<GrantedAuthority> authorities = List.of(
    new SimpleGrantedAuthority("ROLE_ADMIN"),
    new SimpleGrantedAuthority("orders:write")
);
```

```java
http.authorizeHttpRequests(auth -> auth
    .requestMatchers("/admin/**").hasRole("ADMIN")        // checks for "ROLE_ADMIN" -- the prefix is IMPLICIT
    .requestMatchers("/orders/**").hasAuthority("orders:write")); // checks the EXACT string, no prefix magic
```

## 2. Why & when

Authorization decisions (from the very first card in this series) need something concrete to check against — `GrantedAuthority` is that concrete unit: a plain string, wrapped in a minimal interface, representing one specific thing a user is permitted to do. Keeping it deliberately simple (just a string) rather than a rich, structured permission object is what makes it flexible enough to represent both coarse-grained roles (`ROLE_ADMIN`, an all-or-nothing designation) and fine-grained permissions (`orders:write`, a specific capability) using the exact same underlying mechanism, with the `ROLE_` prefix convention (and `hasRole`'s automatic prefixing) existing purely as an ergonomic convenience layered on top of this one simple, uniform string-based model.

Reach for understanding `GrantedAuthority` directly when:

- Designing an authorization model for an application — deciding between coarse-grained roles (`ROLE_ADMIN`), fine-grained permissions (`orders:write`), or (commonly, in more sophisticated applications) a combination of both, is a direct design decision about what strings to grant as authorities.
- Debugging an authorization check that unexpectedly fails — confirming exactly which authority strings a given `Authentication` actually holds, and whether `hasRole` versus `hasAuthority` is being used correctly (the `ROLE_` prefix mismatch is an extremely common source of subtle authorization bugs) is usually the fastest path to the actual problem.
- Populating authorities during authentication — whether hardcoded, loaded from a database, or derived from an external identity provider's claims (an OAuth2/OIDC scope or role claim, covered in later cards), understanding that these all ultimately just populate a `Collection<GrantedAuthority>` of plain strings clarifies how diverse authority sources all feed into the same uniform authorization mechanism.

## 3. Core concept

```
 GrantedAuthority: ONE method, getAuthority() -> String

 by CONVENTION (not enforced by the type system):
   "ROLE_ADMIN", "ROLE_USER"          -- role-style, prefixed with ROLE_
   "orders:read", "orders:write"      -- permission-style, unprefixed, finer-grained

 hasRole("ADMIN")     is EXACTLY EQUIVALENT to    hasAuthority("ROLE_ADMIN")
   (hasRole silently PREPENDS "ROLE_" -- a common source of confusion/bugs if the prefix is
    ALSO manually included: hasRole("ROLE_ADMIN") checks for "ROLE_ROLE_ADMIN", which never matches)

 hasAuthority("orders:write")   checks the EXACT string, with NO automatic prefixing at all
```

Both `hasRole` and `hasAuthority` ultimately check the same underlying `Collection<GrantedAuthority>` — they differ only in whether the `ROLE_` prefix is added automatically.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Authentication object holds a collection of GrantedAuthority strings and both hasRole with automatic prefixing and hasAuthority with exact string matching check against this same underlying collection">
  <rect x="220" y="20" width="200" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">authorities collection</text>
  <text x="320" y="56" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">[ROLE_ADMIN, orders:write]</text>

  <rect x="30" y="110" width="220" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="140" y="128" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">hasRole("ADMIN")</text>
  <text x="140" y="142" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">checks "ROLE_ADMIN"</text>

  <rect x="390" y="110" width="220" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="500" y="128" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">hasAuthority("orders:write")</text>
  <text x="500" y="142" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">exact match, no prefix</text>

  <defs><marker id="a10" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="200" y1="66" x2="140" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a10)"/>
  <line x1="380" y1="66" x2="500" y2="110" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a10)"/>
</svg>

Both check methods query the same underlying string collection — only the prefix-handling behavior differs between them.

## 5. Runnable example

The scenario: model both `hasRole`-style (auto-prefixed) and `hasAuthority`-style (exact-match) checks against a shared authorities collection, then deliberately reproduce the classic double-prefix bug to make it concrete. Start with basic authority checking, then add the two distinct check styles side by side, then add the common mistake of manually including the `ROLE_` prefix with `hasRole`, showing exactly how and why it silently fails.

### Level 1 — Basic

A plain collection of authority strings, checked directly.

```java
import java.util.*;

public class GrantedAuthorityLevel1 {
    public static void main(String[] args) {
        Set<String> authorities = Set.of("ROLE_ADMIN", "orders:write");

        System.out.println("has 'ROLE_ADMIN'? " + authorities.contains("ROLE_ADMIN"));
        System.out.println("has 'orders:write'? " + authorities.contains("orders:write"));
        System.out.println("has 'ROLE_USER'? " + authorities.contains("ROLE_USER"));
    }
}
```

How to run: `java GrantedAuthorityLevel1.java`

`GrantedAuthority`, stripped to its essentials, is just a set of strings checked for membership — this is the entire underlying mechanism `hasRole`/`hasAuthority` build their more convenient syntax on top of.

### Level 2 — Intermediate

Add the two distinct check styles — `hasRole` (auto-prefixing) and `hasAuthority` (exact match) — implemented explicitly to show exactly what each one does underneath.

```java
import java.util.*;

public class GrantedAuthorityLevel2 {
    static boolean hasRole(Set<String> authorities, String role) {
        return authorities.contains("ROLE_" + role); // AUTOMATICALLY prepends ROLE_
    }

    static boolean hasAuthority(Set<String> authorities, String authority) {
        return authorities.contains(authority); // EXACT match, no prefixing at all
    }

    public static void main(String[] args) {
        Set<String> authorities = Set.of("ROLE_ADMIN", "orders:write");

        System.out.println("hasRole(\"ADMIN\") -- checks 'ROLE_ADMIN': " + hasRole(authorities, "ADMIN"));
        System.out.println("hasAuthority(\"orders:write\") -- checks EXACT string: " + hasAuthority(authorities, "orders:write"));
        System.out.println("hasAuthority(\"ADMIN\") -- checks 'ADMIN' with NO prefix, does NOT match 'ROLE_ADMIN': " + hasAuthority(authorities, "ADMIN"));
    }
}
```

How to run: `java GrantedAuthorityLevel2.java`

`hasRole(authorities, "ADMIN")` correctly returns `true` (it checks `"ROLE_ADMIN"`, which is present); `hasAuthority(authorities, "ADMIN")` incorrectly (from a naive caller's perspective) returns `false`, because it checks the exact, unprefixed string `"ADMIN"`, which was never granted — only `"ROLE_ADMIN"` was — demonstrating precisely why `hasRole` and `hasAuthority` are not interchangeable and must be used with the correct corresponding string format.

### Level 3 — Advanced

Add the classic double-prefix mistake: manually including `"ROLE_"` when calling `hasRole`, and show exactly why it silently fails rather than throwing an obvious error.

```java
import java.util.*;

public class GrantedAuthorityLevel3 {
    static boolean hasRole(Set<String> authorities, String role) {
        return authorities.contains("ROLE_" + role);
    }

    public static void main(String[] args) {
        Set<String> authorities = Set.of("ROLE_ADMIN");

        // CORRECT usage -- pass just "ADMIN", let hasRole add the prefix
        System.out.println("hasRole(\"ADMIN\") -- CORRECT: " + hasRole(authorities, "ADMIN"));

        // COMMON MISTAKE -- manually including "ROLE_" AS WELL, causing DOUBLE prefixing
        System.out.println("hasRole(\"ROLE_ADMIN\") -- checks for 'ROLE_ROLE_ADMIN': " + hasRole(authorities, "ROLE_ADMIN"));

        // demonstrate WHY it fails: what string is ACTUALLY being checked in the mistaken call
        String actuallyChecked = "ROLE_" + "ROLE_ADMIN";
        System.out.println("the mistaken call actually checks for: '" + actuallyChecked + "'");
        System.out.println("is that string present in authorities? " + authorities.contains(actuallyChecked));
    }
}
```

How to run: `java GrantedAuthorityLevel3.java`

`hasRole(authorities, "ROLE_ADMIN")` returns `false`, not because the user lacks the admin role (they clearly have `"ROLE_ADMIN"`), but because the mistaken call causes `hasRole` to check for the string `"ROLE_ROLE_ADMIN"` (the `ROLE_` prefix applied twice), which was never granted to anyone — this failure produces no exception and no obvious error message, just a silent, incorrect access denial, making it a particularly easy and common mistake to introduce and hard to immediately diagnose without knowing to check for exactly this double-prefixing pattern.

## 6. Walkthrough

Trace the mistaken `hasRole(authorities, "ROLE_ADMIN")` call in Level 3.

1. `hasRole(authorities, "ROLE_ADMIN")` is called with the (mistaken) argument `"ROLE_ADMIN"` — the caller likely intended to express "check for the ADMIN role" but incorrectly included the `ROLE_` prefix themselves, perhaps out of habit from writing `SimpleGrantedAuthority("ROLE_ADMIN")` elsewhere in the same codebase.
2. Inside `hasRole`, the expression `"ROLE_" + role` evaluates with `role = "ROLE_ADMIN"`, producing the concatenated string `"ROLE_" + "ROLE_ADMIN" = "ROLE_ROLE_ADMIN"`.
3. `authorities.contains("ROLE_ROLE_ADMIN")` checks the set `{"ROLE_ADMIN"}` for membership of `"ROLE_ROLE_ADMIN"` — these two strings are different (`"ROLE_ADMIN"` versus `"ROLE_ROLE_ADMIN"`), so `contains` correctly (from `Set.contains`'s own perspective) returns `false`.
4. `hasRole` returns `false`, exactly as any legitimate "the user genuinely lacks this role" case would also return `false` — there is no distinguishing signal anywhere in this return value indicating the *reason* was a double-prefix bug rather than a genuine permission gap, which is precisely why this class of mistake is so easy to introduce and so tedious to debug without specifically knowing to check for it.
5. The explicit demonstration lines confirm this directly: `actuallyChecked` is built the same way `hasRole` builds its internal check string, printed out for visibility, and `authorities.contains(actuallyChecked)` confirms it's `false` — making the otherwise-invisible cause of the failure fully visible for debugging purposes.

```
hasRole(authorities, "ROLE_ADMIN")  [MISTAKEN call -- caller included the prefix themselves]
  internally computes: "ROLE_" + "ROLE_ADMIN" = "ROLE_ROLE_ADMIN"
  authorities.contains("ROLE_ROLE_ADMIN") -> authorities is {"ROLE_ADMIN"} -> NOT present -> false

hasRole returns false -- INDISTINGUISHABLE, from the return value alone, from a GENUINE lack of permission
```

## 7. Gotchas & takeaways

> **Gotcha:** as demonstrated concretely above, calling `hasRole("ROLE_ADMIN")` when the user genuinely has the `"ROLE_ADMIN"` authority silently and incorrectly denies access, because `hasRole` always prepends its own `"ROLE_"` prefix — the correct call is `hasRole("ADMIN")` (no prefix), while `hasAuthority("ROLE_ADMIN")` (the full, exact string, no auto-prefixing) is the correct way to check the same underlying authority using the exact-match method instead. Mixing up which of the two methods expects a prefix is one of the single most common Spring Security authorization bugs in practice.

- `GrantedAuthority` is deliberately minimal — a plain string wrapped in a one-method interface — which is what makes it flexible enough to represent both coarse role-style and fine-grained permission-style authorities using one uniform mechanism.
- The `ROLE_` prefix convention is exactly that: a convention, not something enforced by the `GrantedAuthority` type itself — it exists purely so `hasRole(...)` can offer a slightly more ergonomic calling syntax that doesn't require typing the prefix out repeatedly.
- `hasRole("ADMIN")` and `hasAuthority("ROLE_ADMIN")` are exactly equivalent, checking the identical underlying string — the double-prefix bug (calling `hasRole("ROLE_ADMIN")`) is the single most common practical mistake stemming from not fully internalizing this equivalence.
- When debugging an authorization failure, explicitly checking both which check method was used (`hasRole` vs. `hasAuthority`) and what the *actual*, fully-resolved string being checked was (accounting for `hasRole`'s automatic prefixing) is often the fastest path to finding a subtle, silent authorization bug like this one.
