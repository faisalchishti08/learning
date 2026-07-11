---
card: spring-security
gi: 58
slug: authorities-roles-hasrole-hasauthority-hasanyrole
title: "Authorities & roles (hasRole, hasAuthority, hasAnyRole)"
---

## 1. What it is

`GrantedAuthority` is the single interface (one method, `getAuthority()`, returning a plain string) backing every permission check in Spring Security — "roles" are not a separate concept at all, merely a *convention*: `hasRole("ADMIN")` is sugar that automatically checks for the authority string `"ROLE_ADMIN"` (prepending the `ROLE_` prefix behind the scenes), while `hasAuthority("SCOPE_orders:write")` checks for that exact string with no prefix manipulation at all. `hasAnyRole("ADMIN", "MANAGER")` and `hasAnyAuthority(...)` extend both to an OR-combination of several acceptable values.

```java
http.authorizeHttpRequests(auth -> auth
        .requestMatchers("/admin/**").hasRole("ADMIN")                       // checks for "ROLE_ADMIN" authority
        .requestMatchers("/reports/**").hasAnyRole("ADMIN", "MANAGER")        // checks "ROLE_ADMIN" OR "ROLE_MANAGER"
        .requestMatchers("/api/orders").hasAuthority("SCOPE_orders:read")     // checks exact string, NO prefix added
);
```

## 2. Why & when

Every authority is fundamentally just a string, but two very different *conventions* commonly layer meaning on top of that string: coarse-grained "roles" a user *is* (admin, manager, regular user — conventionally prefixed `ROLE_`) versus fine-grained "scopes" or "permissions" a token or session *has* (`orders:read`, `SCOPE_orders:write` — no prefix convention, since these aren't roles at all). `hasRole` exists purely as a readability convenience for the first convention, automatically adding the `ROLE_` prefix so application code can write `hasRole("ADMIN")` instead of `hasAuthority("ROLE_ADMIN")` — but this convenience becomes a footgun the moment it's applied to an authority that was never meant to carry that prefix.

Reach for each specifically when:

- `hasRole("ADMIN")` for coarse-grained, role-based access control, where the underlying authority genuinely follows the `ROLE_` convention (as most `UserDetailsService` implementations naturally produce).
- `hasAuthority("SCOPE_orders:write")` (or any exact-string authority with no `ROLE_` prefix, like OAuth2 scopes) — `hasRole` would incorrectly search for `"ROLE_SCOPE_orders:write"`, which will never exist, silently denying access to every request.
- `hasAnyRole(...)`/`hasAnyAuthority(...)` when several distinct roles or authorities should all satisfy the same access rule — an OR relationship, not requiring all of them simultaneously.

## 3. Core concept

```
 GrantedAuthority is JUST a string -- Spring Security itself has NO built-in concept of "role" vs "authority"

 hasRole("ADMIN")           ==  hasAuthority("ROLE_ADMIN")     -- hasRole ADDS the "ROLE_" prefix AUTOMATICALLY
 hasAnyRole("ADMIN","MGR")  ==  hasAnyAuthority("ROLE_ADMIN", "ROLE_MGR")

 hasAuthority("SCOPE_orders:write")  -- checks EXACTLY this string, NO prefix added, NO prefix assumed

 COMMON MISTAKE:
   hasRole("SCOPE_orders:write")
     -> ACTUALLY checks for "ROLE_SCOPE_orders:write"  (note the DOUBLE, nonsensical prefixing)
     -> this authority will NEVER exist -- access is ALWAYS denied, silently and confusingly
```

`hasRole` is purely a naming convenience layered on top of `hasAuthority` — it has no independent meaning beyond automatically prepending one specific string prefix.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="hasRole ADMIN and hasAuthority ROLE underscore ADMIN check the exact same underlying authority string hasRole is purely a convenience that automatically adds the ROLE underscore prefix while hasAuthority checks whatever exact string is given with no prefix manipulation at all">
  <rect x="15" y="20" width="230" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="130" y="45" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">hasRole(&quot;ADMIN&quot;)</text>

  <rect x="15" y="105" width="230" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="130" y="130" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">hasAuthority(&quot;ROLE_ADMIN&quot;)</text>

  <rect x="380" y="60" width="230" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">checks authority string</text>
  <text x="495" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">&quot;ROLE_ADMIN&quot; -- IDENTICAL check</text>

  <defs><marker id="a58" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="245" y1="41" x2="380" y2="75" stroke="#8b949e" stroke-width="1" marker-end="url(#a58)"/>
  <text x="290" y="55" fill="#8b949e" font-size="6.5" font-family="sans-serif">adds ROLE_ prefix</text>
  <line x1="245" y1="126" x2="380" y2="93" stroke="#8b949e" stroke-width="1" marker-end="url(#a58)"/>
  <text x="290" y="115" fill="#8b949e" font-size="6.5" font-family="sans-serif">no prefix added</text>
</svg>

Two different-looking calls, converging on the exact same underlying string comparison.

## 5. Runnable example

The scenario: implement both `hasRole` and `hasAuthority` faithfully (including the prefix-adding behavior), then trigger the double-prefix mistake explicitly to make its consequence concrete, then add `hasAnyRole` for a multi-role OR check.

### Level 1 — Basic

Faithful implementations of both check styles, demonstrating they converge on the identical underlying comparison.

```java
import java.util.*;
import java.util.function.Predicate;

public class RolesAuthoritiesLevel1 {
    record Authentication(Set<String> authorities) {}

    static Predicate<Authentication> hasAuthority(String exactAuthority) {
        return auth -> auth.authorities().contains(exactAuthority); // NO prefix manipulation, EVER
    }

    static Predicate<Authentication> hasRole(String roleName) {
        return hasAuthority("ROLE_" + roleName); // PURELY a convenience wrapper around hasAuthority
    }

    public static void main(String[] args) {
        Authentication admin = new Authentication(Set.of("ROLE_ADMIN"));

        System.out.println("hasRole(\"ADMIN\'): " + hasRole("ADMIN").test(admin));
        System.out.println("hasAuthority(\"ROLE_ADMIN\"): " + hasAuthority("ROLE_ADMIN").test(admin));
        System.out.println("both checks are equivalent: "
                + (hasRole("ADMIN").test(admin) == hasAuthority("ROLE_ADMIN").test(admin)));
    }
}
```

How to run: `java RolesAuthoritiesLevel1.java`

`hasRole` is implemented purely by delegating to `hasAuthority` with the `"ROLE_"` prefix already concatenated on — both calls against the identical `admin` authentication produce the identical `true` result, confirming they are genuinely the same underlying check expressed two different ways.

### Level 2 — Intermediate

Trigger the double-prefix mistake explicitly: applying `hasRole` to an authority that was never meant to carry the `ROLE_` prefix.

```java
import java.util.*;
import java.util.function.Predicate;

public class RolesAuthoritiesLevel2 {
    record Authentication(Set<String> authorities) {}

    static Predicate<Authentication> hasAuthority(String exactAuthority) {
        return auth -> auth.authorities().contains(exactAuthority);
    }

    static Predicate<Authentication> hasRole(String roleName) {
        return hasAuthority("ROLE_" + roleName);
    }

    public static void main(String[] args) {
        // an OAuth2-style client carrying a SCOPE authority -- NEVER meant to have "ROLE_" prepended
        Authentication apiClient = new Authentication(Set.of("SCOPE_orders:write"));

        boolean correctCheck = hasAuthority("SCOPE_orders:write").test(apiClient);
        System.out.println("CORRECT: hasAuthority(\"SCOPE_orders:write\") -> " + correctCheck);

        // the MISTAKE: calling hasRole on a scope string
        boolean mistakenCheck = hasRole("SCOPE_orders:write").test(apiClient);
        System.out.println("MISTAKE: hasRole(\"SCOPE_orders:write\") -> " + mistakenCheck
                + "  (actually checked for authority \"ROLE_SCOPE_orders:write\", which does NOT exist)");
    }
}
```

How to run: `java RolesAuthoritiesLevel2.java`

`hasAuthority("SCOPE_orders:write")` correctly finds the matching authority and returns `true`; `hasRole("SCOPE_orders:write")` instead searches for `"ROLE_SCOPE_orders:write"` (the double-prefixed, nonsensical string), which the client's authority set does not and will never contain, so it incorrectly returns `false` — this is the exact class of silent, confusing authorization bug that results from applying `hasRole`'s convenience to an authority that was never meant to carry the `ROLE_` prefix.

### Level 3 — Advanced

Add `hasAnyRole` for a multi-role OR check, and combine it with `hasAuthority` in one realistic access policy mixing coarse-grained roles and fine-grained scopes.

```java
import java.util.*;
import java.util.function.Predicate;

public class RolesAuthoritiesLevel3 {
    record Authentication(Set<String> authorities) {}

    static Predicate<Authentication> hasAuthority(String exactAuthority) {
        return auth -> auth.authorities().contains(exactAuthority);
    }

    static Predicate<Authentication> hasRole(String roleName) {
        return hasAuthority("ROLE_" + roleName);
    }

    static Predicate<Authentication> hasAnyRole(String... roleNames) {
        return auth -> Arrays.stream(roleNames).anyMatch(role -> hasRole(role).test(auth));
    }

    public static void main(String[] args) {
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));
        Authentication apiClientWithScope = new Authentication(Set.of("SCOPE_reports:read"));

        Predicate<Authentication> canViewReports = auth ->
                hasAnyRole("ADMIN", "MANAGER").test(auth) || hasAuthority("SCOPE_reports:read").test(auth);

        System.out.println("manager can view reports (via ROLE_MANAGER): " + canViewReports.test(manager));
        System.out.println("regular user can view reports: " + canViewReports.test(regularUser));
        System.out.println("API client can view reports (via SCOPE_reports:read): " + canViewReports.test(apiClientWithScope));
    }
}
```

How to run: `java RolesAuthoritiesLevel3.java`

`canViewReports` combines `hasAnyRole("ADMIN", "MANAGER")` (satisfied by either coarse-grained role) with `hasAuthority("SCOPE_reports:read")` (satisfied by the fine-grained scope, entirely independent of any role) — the manager and the API client both gain access through two completely different authority checks, while the regular user, matching neither condition, is correctly denied.

## 6. Walkthrough

Trace `canViewReports.test(manager)` from Level 3.

1. `canViewReports` evaluates its `||` expression left to right: `hasAnyRole("ADMIN", "MANAGER").test(manager)` runs first.
2. Inside `hasAnyRole`, `Arrays.stream(roleNames).anyMatch(role -> hasRole(role).test(auth))` iterates `["ADMIN", "MANAGER"]`; the first element, `"ADMIN"`, is checked via `hasRole("ADMIN").test(manager)`, which delegates to `hasAuthority("ROLE_ADMIN").test(manager)`, checking whether `manager.authorities()` (which is `{"ROLE_MANAGER"}`) contains `"ROLE_ADMIN"` — it does not, so this returns `false`.
3. `anyMatch` continues to the second element, `"MANAGER"`: `hasRole("MANAGER").test(manager)` delegates to `hasAuthority("ROLE_MANAGER").test(manager)`, checking whether `{"ROLE_MANAGER"}` contains `"ROLE_MANAGER"` — it does, so this returns `true`.
4. Because `anyMatch` found a `true` result on this second element, `hasAnyRole("ADMIN", "MANAGER").test(manager)` returns `true` overall — Java's short-circuit evaluation of `||` in `canViewReports` means `hasAuthority("SCOPE_reports:read").test(manager)` is never even evaluated, since the left-hand side of the `||` already determined the outcome.
5. `canViewReports.test(manager)` returns `true`, printed as `"manager can view reports (via ROLE_MANAGER): true"` — the manager's access was granted entirely through the role-based path, with the scope-based check playing no role in this particular decision.

```
canViewReports.test(manager):
  hasAnyRole("ADMIN", "MANAGER").test(manager):
    check "ROLE_ADMIN"   -> manager's authorities {ROLE_MANAGER} does NOT contain it -> false
    check "ROLE_MANAGER" -> manager's authorities {ROLE_MANAGER} DOES contain it     -> true
    -> anyMatch found true -> hasAnyRole returns true
  -> || short-circuits -> hasAuthority("SCOPE_reports:read") NEVER evaluated
  -> canViewReports returns true
```

## 7. Gotchas & takeaways

> **Gotcha:** the double-prefix mistake from Level 2 is especially dangerous precisely because it fails *silently* — there's no exception, no error, no warning; the check simply always returns `false`, denying access to every single request, which can look identical to "this feature is correctly locked down" until someone with the expected role reports being unable to access something they clearly should be able to.

- `GrantedAuthority` is fundamentally just a string — "role" versus "authority"/"scope" is purely a naming convention Spring Security's convenience methods build on top of, not a distinct underlying mechanism.
- `hasRole("X")` is exact sugar for `hasAuthority("ROLE_X")` — applying it to an authority that was never meant to carry the `ROLE_` prefix (an OAuth2 scope, a custom permission string) silently and permanently denies access, since the double-prefixed string will never match anything real.
- `hasAnyRole`/`hasAnyAuthority` express an OR relationship across several acceptable values — any one matching is sufficient, and Java's short-circuit evaluation means later conditions in a combined expression aren't necessarily even evaluated once an earlier one is satisfied.
- When in doubt about whether a given authority string follows the `ROLE_` convention, `hasAuthority` with the exact, explicit string is always safe — it never performs any implicit prefix manipulation, unlike `hasRole`.
