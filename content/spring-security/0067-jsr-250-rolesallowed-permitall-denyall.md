---
card: spring-security
gi: 67
slug: jsr-250-rolesallowed-permitall-denyall
title: "JSR-250 (@RolesAllowed, @PermitAll, @DenyAll)"
---

## 1. What it is

JSR-250 is the Java standard (not Spring-specific) defining a small set of common security annotations — `@RolesAllowed({"ADMIN", "MANAGER"})`, `@PermitAll`, `@DenyAll` — that Spring Security supports as an interoperability option for applications wanting standard, vendor-neutral annotations rather than Spring-specific ones, requiring `@EnableMethodSecurity(jsr250Enabled = true)` to activate, since — like `@Secured` from the previous card — it is not part of the default-enabled set.

```java
@RolesAllowed({"ADMIN", "MANAGER"}) // implicit OR, JUST LIKE @Secured -- no SpEL, no parameter access
public Report generateReport() { ... }

@PermitAll // equivalent to @PreAuthorize("permitAll()")
public String getPublicInfo() { ... }

@DenyAll // equivalent to @PreAuthorize("denyAll()") -- effectively unreachable, useful during incident response
public void temporarilyDisabledFeature() { ... }

@EnableMethodSecurity(jsr250Enabled = true)
```

## 2. Why & when

JSR-250 exists as a Java EE-wide standard, meaning code written against it is, in principle, portable across any Java EE/Jakarta EE-compliant application server's security implementation, not tied specifically to Spring Security — a genuine advantage for a library or module intended to run in multiple different containers without a hard dependency on Spring Security's own annotation set. In practice, most applications using Spring Security exclusively have no portability requirement to satisfy and gain nothing from JSR-250 over `@PreAuthorize`, which — exactly like `@Secured` — JSR-250's `@RolesAllowed` is a strict subset of in expressive power, lacking any SpEL support, parameter access, or `and`/`or` composition.

Reach for JSR-250 annotations when:

- Building a library or module explicitly intended to remain portable across different Jakarta EE-compliant security implementations, not committed exclusively to Spring Security.
- Migrating an existing Java EE application that already used JSR-250 annotations into Spring Security, where recognizing they're directly supported (rather than requiring an immediate rewrite to Spring-specific annotations) eases the transition.
- `@DenyAll` specifically as a quick, unmissable way to temporarily and completely disable a specific method during an incident, a maintenance window, or while a bug is being fixed — its single-purpose bluntness (no expression to misconfigure) can be a genuine feature in that narrow situation.
- For everything else, prefer `@PreAuthorize`/`@PostAuthorize` in new, Spring-Security-committed code, for the same reasons `@Secured` is generally superseded — the standard's portability benefit rarely outweighs the loss of SpEL expressiveness in practice.

## 3. Core concept

```
 @RolesAllowed({"ADMIN", "MANAGER"})
   -- checks: does the caller have ROLE_ADMIN OR ROLE_MANAGER?  (IMPLICIT OR, identical shape to @Secured)
   -- NO SpEL, NO method-parameter access, NO and/or composition

 @PermitAll   ==  @PreAuthorize("permitAll()")   -- ALWAYS allowed, unconditionally
 @DenyAll     ==  @PreAuthorize("denyAll()")     -- ALWAYS denied, unconditionally (method NEVER runs)

 ENABLING (separate from BOTH the default AND from securedEnabled):
   @EnableMethodSecurity(jsr250Enabled = true)
```

Structurally identical to `@Secured` in what it can express — a different vendor-neutral spelling for the same limited capability, plus two additional unconditional shortcuts.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RolesAllowed with a list of roles expresses an implicit OR check identical in capability to Secured PermitAll and DenyAll are unconditional shortcuts always allowing or always denying regardless of any authentication all three require the jsr250Enabled flag to activate">
  <rect x="15" y="15" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="105" y="33" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@RolesAllowed({...})</text>
  <text x="105" y="46" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">implicit OR, like @Secured</text>

  <rect x="230" y="15" width="180" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="320" y="33" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">@PermitAll</text>
  <text x="320" y="46" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ALWAYS allowed</text>

  <rect x="445" y="15" width="180" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="535" y="33" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@DenyAll</text>
  <text x="535" y="46" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">ALWAYS denied</text>

  <rect x="130" y="90" width="380" height="42" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="320" y="115" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@EnableMethodSecurity(jsr250Enabled = true)</text>

  <defs><marker id="a67" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="105" y1="57" x2="270" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#a67)"/>
  <line x1="320" y1="57" x2="320" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#a67)"/>
  <line x1="535" y1="57" x2="370" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#a67)"/>
</svg>

Three annotations, all requiring the same explicit opt-in flag — none active without it.

## 5. Runnable example

The scenario: implement `@RolesAllowed`'s implicit-OR check (identical in shape to `@Secured`'s from the previous card), then implement `@PermitAll`/`@DenyAll`'s unconditional behavior, then demonstrate the `jsr250Enabled` opt-in gate explicitly, mirroring how the annotation has no effect at all without it.

### Level 1 — Basic

`@RolesAllowed`-style implicit-OR checking, structurally identical to the previous card's `@Secured` model.

```java
import java.util.*;

public class Jsr250Level1 {
    record Authentication(Set<String> authorities) {}

    // models @RolesAllowed({"ADMIN", "MANAGER"})
    static boolean rolesAllowedCheck(Authentication auth, String... roles) {
        for (String role : roles) {
            if (auth.authorities().contains("ROLE_" + role)) return true; // implicit OR, note the "ROLE_" prefix IS applied here
        }
        return false;
    }

    public static void main(String[] args) {
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));

        System.out.println("manager: " + rolesAllowedCheck(manager, "ADMIN", "MANAGER"));
        System.out.println("regular user: " + rolesAllowedCheck(regularUser, "ADMIN", "MANAGER"));
    }
}
```

How to run: `java Jsr250Level1.java`

`rolesAllowedCheck` mirrors `@Secured`'s implicit-OR logic exactly, prepending `"ROLE_"` to each listed role name before checking — the manager passes via `"ROLE_MANAGER"`, while the regular user matches neither listed role and is denied.

### Level 2 — Intermediate

Add `@PermitAll` and `@DenyAll`'s unconditional behavior, confirming neither depends on the caller's authentication at all.

```java
import java.util.*;

public class Jsr250Level2 {
    record Authentication(Set<String> authorities) {}

    // models @PermitAll -- @PreAuthorize("permitAll()")
    static boolean permitAllCheck(Authentication auth) { return true; } // NEVER even looks at "auth"

    // models @DenyAll -- @PreAuthorize("denyAll()")
    static boolean denyAllCheck(Authentication auth) { return false; } // NEVER even looks at "auth"

    public static void main(String[] args) {
        Authentication anonymous = new Authentication(Set.of());
        Authentication superAdmin = new Authentication(Set.of("ROLE_ADMIN", "ROLE_SUPER_ADMIN"));

        System.out.println("permitAll, anonymous caller: " + permitAllCheck(anonymous));
        System.out.println("permitAll, super admin caller: " + permitAllCheck(superAdmin));
        System.out.println("denyAll, anonymous caller: " + denyAllCheck(anonymous));
        System.out.println("denyAll, super admin caller: " + denyAllCheck(superAdmin)
                + "  (even the SUPER ADMIN is denied -- denyAll is TRULY unconditional)");
    }
}
```

How to run: `java Jsr250Level2.java`

Both `permitAllCheck` and `denyAllCheck` ignore their `auth` parameter entirely — even the most privileged caller imaginable (`superAdmin`) is denied by `denyAllCheck`, since the check never inspects any authority at all, demonstrating exactly why `@DenyAll` is useful for genuinely and unconditionally taking a feature offline regardless of who's asking.

### Level 3 — Advanced

Demonstrate the `jsr250Enabled` opt-in gate explicitly, showing an `@RolesAllowed`-equivalent check having literally no effect when the flag is off, exactly mirroring the real annotation's requirement.

```java
import java.util.*;

public class Jsr250Level3 {
    record Authentication(Set<String> authorities) {}
    record MethodSecurityConfig(boolean jsr250Enabled) {}

    static boolean rolesAllowedCheck(Authentication auth, String... roles) {
        for (String role : roles) {
            if (auth.authorities().contains("ROLE_" + role)) return true;
        }
        return false;
    }

    // models the AOP interceptor's OWN gate: does it even CONSULT the @RolesAllowed annotation at all?
    static String invokeMethod(MethodSecurityConfig config, Authentication auth, boolean methodHasRolesAllowed, String... requiredRoles) {
        if (methodHasRolesAllowed && !config.jsr250Enabled()) {
            // the annotation is PRESENT on the method, but jsr250 support is NOT enabled --
            // Spring Security's interceptor simply DOES NOT RECOGNIZE this annotation at all, and skips it entirely
            return "method runs UNPROTECTED (annotation present, but jsr250Enabled=false -- SILENTLY IGNORED)";
        }
        if (methodHasRolesAllowed && !rolesAllowedCheck(auth, requiredRoles)) {
            return "DENIED (jsr250Enabled=true, and check failed)";
        }
        return "method runs, PROTECTED correctly";
    }

    public static void main(String[] args) {
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));

        MethodSecurityConfig jsr250Off = new MethodSecurityConfig(false);
        MethodSecurityConfig jsr250On = new MethodSecurityConfig(true);

        System.out.println("jsr250Enabled=false: " + invokeMethod(jsr250Off, regularUser, true, "ADMIN"));
        System.out.println("jsr250Enabled=true:  " + invokeMethod(jsr250On, regularUser, true, "ADMIN"));
    }
}
```

How to run: `java Jsr250Level3.java`

With `jsr250Enabled = false`, the method annotated `@RolesAllowed("ADMIN")` runs completely unprotected — the interceptor doesn't recognize the annotation at all, silently ignoring it rather than throwing any error; with `jsr250Enabled = true`, the identical annotated method is correctly protected, and the regular user (lacking `ROLE_ADMIN`) is denied — the exact same annotation on the exact same method producing opposite real-world security outcomes purely based on this one configuration flag.

## 6. Walkthrough

Trace `invokeMethod(jsr250Off, regularUser, true, "ADMIN")` from Level 3.

1. `invokeMethod` first checks `methodHasRolesAllowed && !config.jsr250Enabled()` — `methodHasRolesAllowed` is `true` (this method is indeed annotated), and `!config.jsr250Enabled()` evaluates `!false`, i.e. `true` (since `jsr250Off.jsr250Enabled()` is `false`) — the overall condition is `true && true`, i.e. `true`.
2. Because this first condition is `true`, the method returns immediately: `"method runs UNPROTECTED (annotation present, but jsr250Enabled=false -- SILENTLY IGNORED)"` — critically, `rolesAllowedCheck` is never even called in this branch, meaning `regularUser`'s lack of `ROLE_ADMIN` is entirely irrelevant to this outcome.
3. This models exactly what happens in a real Spring Security application: if `jsr250Enabled` is never set to `true`, the AOP interceptor responsible for enforcing method security simply has no registered handling for the `@RolesAllowed` annotation at all — it isn't that the check runs and passes; the check is never consulted in the first place, and the method executes as if the annotation weren't there.
4. Compare this with `invokeMethod(jsr250On, regularUser, true, "ADMIN")`: here `!config.jsr250Enabled()` evaluates `!true`, i.e. `false`, so the first condition (`true && false`) is `false`, and control proceeds to the second check, `methodHasRolesAllowed && !rolesAllowedCheck(auth, requiredRoles)` — this time `rolesAllowedCheck` genuinely runs, finds `regularUser` lacks `"ROLE_ADMIN"`, returns `false`, and `!false` is `true`, so the overall second condition is `true`, correctly returning `"DENIED (jsr250Enabled=true, and check failed)"`.

```
jsr250Enabled=false: annotation PRESENT but NOT RECOGNIZED -> check NEVER RUNS -> method runs unprotected
jsr250Enabled=true:  annotation PRESENT and RECOGNIZED    -> check RUNS -> regularUser lacks ROLE_ADMIN -> DENIED
```

## 7. Gotchas & takeaways

> **Gotcha:** because `@RolesAllowed` (like `@Secured`) requires its own explicit enabling flag, a codebase that enables `@PreAuthorize` (the default) but adds a `@RolesAllowed`-annotated method without also setting `jsr250Enabled = true` ends up with that specific method completely unprotected, silently — exactly as Level 3 demonstrates — with no error, warning, or exception anywhere indicating the annotation was never actually active.

- JSR-250's `@RolesAllowed` is structurally identical in capability to `@Secured` — a fixed, implicit-OR list of required roles, with no SpEL support, no method-parameter access, and no `and`/`or` composition.
- `@PermitAll` and `@DenyAll` provide unconditional shortcuts, useful respectively for genuinely public endpoints and for quickly, unmistakably taking a specific method entirely offline.
- All three JSR-250 annotations require the explicit `jsr250Enabled = true` flag on `@EnableMethodSecurity` — like `@Secured`'s `securedEnabled` flag, this is not part of the default-enabled set alongside `@PreAuthorize`/`@PostAuthorize`.
- For applications committed exclusively to Spring Security with no cross-container portability requirement, `@PreAuthorize`/`@PostAuthorize` cover everything JSR-250 offers plus full SpEL expressiveness, making them the generally preferred choice for new code.
