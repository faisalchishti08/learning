---
card: spring-security
gi: 66
slug: secured-legacy
title: "@Secured (legacy)"
---

## 1. What it is

`@Secured` is the older, simpler method-security annotation predating `@PreAuthorize`, accepting a plain list of required authority strings with implicit OR semantics — `@Secured("ROLE_ADMIN")`, or `@Secured({"ROLE_ADMIN", "ROLE_MANAGER"})` to accept either — with no SpEL expression support at all, meaning no access to method parameters, no `hasRole`/`hasAuthority` function calls, and no way to express `and`/`or` combinations beyond the implicit "any listed authority is sufficient" behavior.

```java
@Secured("ROLE_ADMIN")
public void deleteAccount(Long accountId) { ... }

@Secured({"ROLE_ADMIN", "ROLE_MANAGER"}) // implicitly OR'd: EITHER role is sufficient
public Report generateReport() { ... }

// requires its OWN enabling annotation, separate from @EnableMethodSecurity's defaults:
@EnableMethodSecurity(securedEnabled = true)
```

## 2. Why & when

`@Secured` predates SpEL-based expression support in Spring Security method security entirely — it offers only the most basic capability, a fixed list of acceptable authority strings, with no way to reference method parameters, no boolean composition beyond implicit OR, and no equivalent to `@PostAuthorize`'s return-value access at all. `@PreAuthorize` was introduced specifically to supersede it with full SpEL expressiveness, and modern Spring Security applications have essentially no reason to reach for `@Secured` in new code — it survives primarily in older codebases and is disabled by default under `@EnableMethodSecurity`, requiring the explicit `securedEnabled = true` flag to activate at all.

Reach for understanding `@Secured` when:

- Maintaining or migrating legacy code that still uses it — recognizing that `@Secured("ROLE_ADMIN")` translates directly and exactly to `@PreAuthorize("hasRole('ADMIN')")` is the simple, mechanical migration path.
- Understanding why a `@Secured`-annotated method appears to have no effect at all in a modern Spring Boot application — the most common cause is simply that `securedEnabled` was never set to `true`, since it isn't part of `@EnableMethodSecurity`'s default configuration (unlike `@PreAuthorize`/`@PostAuthorize`, which are enabled by default).
- Never reach for `@Secured` in new code — `@PreAuthorize` covers every capability `@Secured` offers, plus everything SpEL expressions add on top, with no meaningful downside to preferring it exclusively.

## 3. Core concept

```
 @Secured({"ROLE_ADMIN", "ROLE_MANAGER"})
   -- checks: does the caller have ROLE_ADMIN OR ROLE_MANAGER? (IMPLICIT OR, no other option)
   -- NO access to method parameters, NO SpEL functions, NO and/or composition beyond this implicit OR

 EXACT modern equivalent:
   @PreAuthorize("hasRole('ADMIN') or hasRole('MANAGER')")
   -- SAME check, PLUS the full expressive power of SpEL if ever needed later

 ENABLING:
   @EnableMethodSecurity(securedEnabled = true)   -- @Secured is OFF by default, must be explicitly turned on
   (@PreAuthorize/@PostAuthorize are ON by default under @EnableMethodSecurity, no extra flag needed)
```

`@Secured` is a strict subset of what `@PreAuthorize` can express — never the other way around.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Secured with a list of role strings expresses only an implicit OR check with no access to method parameters or SpEL functions PreAuthorize covers the identical check plus the full expressive power of SpEL expressions Secured is a strict subset of what PreAuthorize can do">
  <rect x="15" y="50" width="230" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="130" y="72" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Secured({&quot;ROLE_ADMIN&quot;,&quot;ROLE_MANAGER&quot;})</text>
  <text x="130" y="85" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">implicit OR only, no SpEL</text>

  <rect x="395" y="30" width="230" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="52" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PreAuthorize("hasRole('ADMIN')</text>
  <text x="510" y="65" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">or hasRole('MANAGER')")</text>
  <text x="510" y="82" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">SAME check, PLUS full SpEL:</text>
  <text x="510" y="95" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">parameters, and/or, returnObject</text>

  <defs><marker id="a66" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="245" y1="75" x2="395" y2="75" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a66)"/>
</svg>

Everything the left box can do, the right box can also do — plus considerably more.

## 5. Runnable example

The scenario: implement `@Secured`'s implicit-OR check faithfully, then implement the exact `@PreAuthorize` equivalent alongside it and prove they produce identical results, then demonstrate a case `@Secured` genuinely cannot express at all, motivating the migration.

### Level 1 — Basic

`@Secured`-style implicit-OR checking against a fixed list of acceptable authorities.

```java
import java.util.*;

public class SecuredLegacyLevel1 {
    record Authentication(Set<String> authorities) {}

    // models @Secured({"ROLE_ADMIN", "ROLE_MANAGER"})
    static boolean securedCheck(Authentication auth, String... requiredAuthorities) {
        for (String required : requiredAuthorities) {
            if (auth.authorities().contains(required)) return true; // ANY match is sufficient -- implicit OR
        }
        return false;
    }

    public static void main(String[] args) {
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));

        System.out.println("manager: " + securedCheck(manager, "ROLE_ADMIN", "ROLE_MANAGER"));
        System.out.println("regular user: " + securedCheck(regularUser, "ROLE_ADMIN", "ROLE_MANAGER"));
    }
}
```

How to run: `java SecuredLegacyLevel1.java`

`securedCheck` returns `true` the moment it finds *any* of the listed required authorities present — the manager matches on `"ROLE_MANAGER"`, while the regular user matches none of the listed authorities and is denied.

### Level 2 — Intermediate

Implement the exact modern `@PreAuthorize` equivalent alongside the legacy check and confirm both produce identical results for every input.

```java
import java.util.*;

public class SecuredLegacyLevel2 {
    record Authentication(Set<String> authorities) {}

    static boolean securedCheck(Authentication auth, String... requiredAuthorities) {
        for (String required : requiredAuthorities) {
            if (auth.authorities().contains(required)) return true;
        }
        return false;
    }

    // models: @PreAuthorize("hasRole('ADMIN') or hasRole('MANAGER')")
    static boolean preAuthorizeEquivalent(Authentication auth) {
        return auth.authorities().contains("ROLE_ADMIN") || auth.authorities().contains("ROLE_MANAGER");
    }

    public static void main(String[] args) {
        List<Authentication> testCases = List.of(
                new Authentication(Set.of("ROLE_ADMIN")),
                new Authentication(Set.of("ROLE_MANAGER")),
                new Authentication(Set.of("ROLE_USER")),
                new Authentication(Set.of("ROLE_ADMIN", "ROLE_USER"))
        );

        for (Authentication auth : testCases) {
            boolean legacy = securedCheck(auth, "ROLE_ADMIN", "ROLE_MANAGER");
            boolean modern = preAuthorizeEquivalent(auth);
            System.out.println(auth.authorities() + " -- legacy: " + legacy + ", modern: " + modern + ", MATCH? " + (legacy == modern));
        }
    }
}
```

How to run: `java SecuredLegacyLevel2.java`

Every single test case produces `MATCH? true` — the legacy `@Secured`-style check and its modern `@PreAuthorize` equivalent agree on every input, confirming the migration is behavior-preserving for this class of simple, role-based-OR check.

### Level 3 — Advanced

Demonstrate a genuine requirement `@Secured` cannot express at all — checking a method parameter against the caller's own identity — motivating why `@PreAuthorize`'s full SpEL support is necessary beyond this simple migration case.

```java
import java.util.*;

public class SecuredLegacyLevel3 {
    record Authentication(String principalId, Set<String> authorities) {}

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    // @Secured CANNOT express this at all -- it has NO ACCESS to method parameters whatsoever;
    // the best @Secured could do is require SOME fixed role, with NO WAY to also compare "#accountId" against the caller
    static boolean securedStyleCheck_INCOMPLETE(Authentication auth) {
        // @Secured("ROLE_USER") -- ANY user passes this, regardless of WHICH account they're trying to access!
        return auth.authorities().contains("ROLE_USER");
    }

    // @PreAuthorize CAN express the FULL, CORRECT requirement, referencing the method's OWN parameter
    static boolean preAuthorizeStyleCheck_CORRECT(Authentication auth, long accountId) {
        // @PreAuthorize("#accountId == authentication.principal.id or hasRole('ADMIN')")
        boolean ownsIt = accountId == Long.parseLong(auth.principalId());
        boolean isAdmin = auth.authorities().contains("ROLE_ADMIN");
        return ownsIt || isAdmin;
    }

    public static void main(String[] args) {
        Authentication bob = new Authentication("2", Set.of("ROLE_USER"));

        System.out.println("@Secured-style check, bob accessing ANY account (parameter IGNORED): "
                + securedStyleCheck_INCOMPLETE(bob) + " (WRONG -- would allow bob to access ANY account!)");

        System.out.println("@PreAuthorize-style check, bob accessing HIS OWN account (2): "
                + preAuthorizeStyleCheck_CORRECT(bob, 2L));
        System.out.println("@PreAuthorize-style check, bob accessing SOMEONE ELSE'S account (5): "
                + preAuthorizeStyleCheck_CORRECT(bob, 5L) + " (correctly denied)");
    }
}
```

How to run: `java SecuredLegacyLevel3.java`

`securedStyleCheck_INCOMPLETE` returns `true` for bob regardless of which account he's trying to access, since `@Secured` has no way to reference the `accountId` parameter at all — a genuinely dangerous gap if this were the *only* check applied; `preAuthorizeStyleCheck_CORRECT` correctly distinguishes bob accessing his own account (granted) from bob accessing someone else's (denied), precisely because `@PreAuthorize`'s SpEL expression can reference the method's own parameter directly, something `@Secured` structurally cannot do.

## 6. Walkthrough

Trace `preAuthorizeStyleCheck_CORRECT(bob, 5L)` from Level 3, the correctly-denied call.

1. `ownsIt = 5L == Long.parseLong(bob.principalId())` evaluates `Long.parseLong("2")`, which produces `2L`; comparing `5L == 2L` is `false`, so `ownsIt` is `false` — bob's own principal ID (`"2"`) does not match the requested `accountId` (`5`).
2. `isAdmin = bob.authorities().contains("ROLE_ADMIN")` checks bob's authorities, `{"ROLE_USER"}`, for `"ROLE_ADMIN"` — it is absent, so `isAdmin` is `false`.
3. The method returns `ownsIt || isAdmin`, i.e. `false || false`, which is `false` — the call is correctly denied, since bob neither owns account `5` nor holds an administrative override.
4. Contrast this with `securedStyleCheck_INCOMPLETE(bob)` from the same file: that method's entire body is `auth.authorities().contains("ROLE_USER")`, which is `true` for bob regardless of any `accountId` value — because `@Secured`'s expression language has no mechanism to reference a method parameter at all, *any* attempt to replicate this per-account ownership check using only `@Secured` would need to either grant blanket access to all accounts for any `ROLE_USER` holder, or push the actual ownership check into the method body itself (defeating the purpose of declarative, annotation-based authorization in the first place).
5. This concretely demonstrates why `@PreAuthorize`'s SpEL expressiveness isn't merely a convenience over `@Secured` — for authorization rules genuinely depending on the specific data involved in a call (as opposed to a caller's role alone), `@Secured` is not just less convenient, it is structurally incapable of expressing the requirement at all.

```
@Secured-equivalent check: only ever asks "does the caller have ROLE_USER?" -- accountId is INVISIBLE to it
  bob (ROLE_USER) requesting ANY account -> ALWAYS true, regardless of which account

@PreAuthorize-equivalent check: asks "does accountId match the caller's own ID, or are they an admin?"
  bob (id="2") requesting account 2 -> ownsIt=true  -> GRANTED
  bob (id="2") requesting account 5 -> ownsIt=false, isAdmin=false -> DENIED
```

## 7. Gotchas & takeaways

> **Gotcha:** `@Secured` requires its own explicit `securedEnabled = true` flag on `@EnableMethodSecurity` — unlike `@PreAuthorize`/`@PostAuthorize`, which are enabled by default — so a codebase migrating *toward* `@Secured` (or one where it was added without updating the `@EnableMethodSecurity` configuration) may find the annotation silently has no effect at all, with no error or warning indicating it was never actually activated.

- `@Secured` accepts only a fixed list of authority strings with implicit OR semantics, offering no access to method parameters, no SpEL functions, and no boolean composition beyond that single OR.
- `@Secured("X")` migrates directly and exactly to `@PreAuthorize("hasRole('X')")` (or `hasAuthority` for a non-role-prefixed string) — a simple, mechanical, behavior-preserving translation for this class of check.
- For any authorization rule depending on the specific data involved in a call — not just the caller's role — `@Secured` is structurally incapable of expressing it at all, since it has no mechanism to reference method parameters; `@PreAuthorize` is necessary for these cases.
- `@Secured` requires explicitly setting `securedEnabled = true` on `@EnableMethodSecurity`, unlike `@PreAuthorize`/`@PostAuthorize`, which are enabled by default — worth checking directly if a `@Secured`-annotated method appears to have no effect.
