---
card: spring-security
gi: 72
slug: meta-annotations-for-method-security
title: "Meta-annotations for method security"
---

## 1. What it is

A meta-annotation is a custom annotation whose own definition is annotated with `@PreAuthorize` (or `@PostAuthorize`, `@Secured`, and so on), letting a specific, recurring authorization rule be given its own short, descriptive name — `@IsAdmin` instead of repeating `@PreAuthorize("hasRole('ADMIN')")` on every method needing it — with Spring Security fully honoring the meta-annotation exactly as if the underlying `@PreAuthorize` had been written out directly on each usage site.

```java
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
@PreAuthorize("hasRole('ADMIN')")
public @interface IsAdmin {}

@IsAdmin // reads FAR more clearly than @PreAuthorize("hasRole('ADMIN')") repeated everywhere
public void deleteAccount(Long accountId) { ... }

@IsAdmin
public void banUser(Long userId) { ... }
```

## 2. Why & when

Repeating an identical, sometimes lengthy `@PreAuthorize` SpEL expression across many methods is both verbose and a maintenance liability — if the underlying rule ever needs to change (adding an additional role that should also qualify, tightening or loosening a condition), every single repeated occurrence needs to be found and updated consistently, and a missed occurrence silently leaves stale, inconsistent behavior behind. A meta-annotation collapses this to one canonical definition: change the expression once, on the meta-annotation itself, and every usage site picks up the change automatically, while simultaneously making each usage site read as a clear, self-documenting statement of intent (`@IsAdmin`) rather than an implementation detail (the specific SpEL string) repeated everywhere it's needed.

Reach for a meta-annotation when:

- The identical (or nearly identical) `@PreAuthorize`/`@PostAuthorize` expression is used across three or more methods — the repetition itself is the signal that a meta-annotation would reduce both verbosity and future maintenance risk.
- A rule's *name* carries more meaning to a reader than its underlying implementation detail — `@IsAccountOwner` communicates intent far more directly than `@PreAuthorize("#accountId == authentication.principal.id")` repeated at every call site.
- Combining a meta-annotation with parameters (via `@AliasFor`, allowing the meta-annotation itself to accept a value substituted into the underlying expression) for cases needing a customizable, but still centrally-defined, rule shape.

## 3. Core concept

```
 define a META-ANNOTATION ONCE:
   @PreAuthorize("hasRole('ADMIN')")
   public @interface IsAdmin {}

 USE it everywhere the rule applies:
   @IsAdmin
   public void deleteAccount(...) { ... }

   @IsAdmin
   public void banUser(...) { ... }

 Spring Security's method-security infrastructure RECOGNIZES the meta-annotation
   and applies the UNDERLYING @PreAuthorize expression EXACTLY as if it had been written directly

 CHANGING the rule LATER:
   edit ONLY the meta-annotation's own @PreAuthorize expression
   EVERY usage site (deleteAccount, banUser, ...) picks up the change AUTOMATICALLY, with NO other edits needed
```

One canonical definition, many self-documenting usage sites — a change in one place propagates everywhere automatically.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A meta annotation named IsAdmin is defined once carrying a PreAuthorize expression checking hasRole ADMIN multiple methods across the codebase are annotated simply with IsAdmin each one automatically inheriting the underlying expression a future change to the meta annotation's definition propagates to every usage site without any further edits">
  <rect x="15" y="55" width="200" height="60" rx="9" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="115" y="78" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@interface IsAdmin</text>
  <text x="115" y="91" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@PreAuthorize("hasRole('ADMIN')")</text>
  <text x="115" y="104" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">defined ONCE</text>

  <rect x="290" y="15" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="365" y="36" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@IsAdmin deleteAccount</text>

  <rect x="290" y="60" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="365" y="81" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@IsAdmin banUser</text>

  <rect x="290" y="105" width="150" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="365" y="126" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@IsAdmin resetPassword</text>

  <defs><marker id="a72" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="215" y1="70" x2="290" y2="32" stroke="#8b949e" stroke-width="1" marker-end="url(#a72)"/>
  <line x1="215" y1="80" x2="290" y2="77" stroke="#8b949e" stroke-width="1" marker-end="url(#a72)"/>
  <line x1="215" y1="95" x2="290" y2="122" stroke="#8b949e" stroke-width="1" marker-end="url(#a72)"/>
</svg>

One definition, many usage sites — a single edit to the box on the left updates every arrow's destination automatically.

## 5. Runnable example

The scenario: model meta-annotation resolution directly (recognizing a custom annotation and delegating to its underlying rule), then demonstrate the maintenance benefit concretely by changing the underlying rule once and observing every usage site update automatically, then add a parameterized meta-annotation for a slightly more advanced case.

### Level 1 — Basic

A minimal meta-annotation registry, resolving a custom annotation name to its underlying rule.

```java
import java.util.*;
import java.util.function.Predicate;

public class MetaAnnotationsLevel1 {
    record Authentication(Set<String> authorities) {}

    // models: @interface IsAdmin { @PreAuthorize("hasRole('ADMIN')") }
    static Map<String, Predicate<Authentication>> metaAnnotationRules = new HashMap<>();

    static void defineMetaAnnotation(String annotationName, Predicate<Authentication> underlyingRule) {
        metaAnnotationRules.put(annotationName, underlyingRule);
    }

    // models the method-security infrastructure recognizing the meta-annotation on a given method
    static boolean checkMethod(String metaAnnotationName, Authentication auth) {
        return metaAnnotationRules.get(metaAnnotationName).test(auth);
    }

    public static void main(String[] args) {
        defineMetaAnnotation("IsAdmin", auth -> auth.authorities().contains("ROLE_ADMIN"));

        Authentication admin = new Authentication(Set.of("ROLE_ADMIN"));
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));

        System.out.println("@IsAdmin on deleteAccount, admin caller: " + checkMethod("IsAdmin", admin));
        System.out.println("@IsAdmin on banUser, regular user caller: " + checkMethod("IsAdmin", regularUser));
    }
}
```

How to run: `java MetaAnnotationsLevel1.java`

`defineMetaAnnotation` registers `"IsAdmin"`'s underlying rule exactly once; `checkMethod` looks up and applies that rule for *any* method claiming to use `"IsAdmin"` — both usage sites (`deleteAccount`, `banUser`) share the identical underlying check, resolved from the single registered definition.

### Level 2 — Intermediate

Change the underlying rule once and confirm every usage site picks up the change automatically, demonstrating the core maintenance benefit.

```java
import java.util.*;
import java.util.function.Predicate;

public class MetaAnnotationsLevel2 {
    record Authentication(Set<String> authorities) {}

    static Map<String, Predicate<Authentication>> metaAnnotationRules = new HashMap<>();

    static void defineMetaAnnotation(String name, Predicate<Authentication> rule) { metaAnnotationRules.put(name, rule); }
    static boolean checkMethod(String metaAnnotationName, Authentication auth) { return metaAnnotationRules.get(metaAnnotationName).test(auth); }

    public static void main(String[] args) {
        defineMetaAnnotation("IsAdmin", auth -> auth.authorities().contains("ROLE_ADMIN"));

        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));

        System.out.println("BEFORE the rule change:");
        System.out.println("  deleteAccount (uses @IsAdmin): " + checkMethod("IsAdmin", manager));
        System.out.println("  banUser (uses @IsAdmin): " + checkMethod("IsAdmin", manager));

        // the RULE CHANGES: managers should NOW also qualify as "admin" for this purpose --
        // this is ONE edit, to the META-ANNOTATION's definition, NOT to either usage site
        defineMetaAnnotation("IsAdmin", auth -> auth.authorities().contains("ROLE_ADMIN") || auth.authorities().contains("ROLE_MANAGER"));

        System.out.println("AFTER the rule change (both usage sites updated automatically):");
        System.out.println("  deleteAccount (STILL just says @IsAdmin): " + checkMethod("IsAdmin", manager));
        System.out.println("  banUser (STILL just says @IsAdmin): " + checkMethod("IsAdmin", manager));
    }
}
```

How to run: `java MetaAnnotationsLevel2.java`

Before the rule change, a manager fails both checks (only admins qualified); after redefining `"IsAdmin"`'s underlying rule exactly once, *both* `deleteAccount` and `banUser` — neither of which was individually edited — now correctly grant the manager, since both simply reference the meta-annotation by name and inherit whatever its current definition happens to be.

### Level 3 — Advanced

Add a parameterized meta-annotation, modeling `@AliasFor`-style customization where the meta-annotation itself accepts a value substituted into the underlying expression.

```java
import java.util.*;
import java.util.function.BiPredicate;

public class MetaAnnotationsLevel3 {
    record Authentication(Set<String> authorities) {}

    // models: @interface HasRole { String value(); @PreAuthorize("hasRole(#root.this.value())") }
    // -- a PARAMETERIZED meta-annotation: the SAME underlying shape, but with a VALUE supplied per usage site
    static BiPredicate<Authentication, String> hasRoleMetaAnnotation =
            (auth, requiredRole) -> auth.authorities().contains("ROLE_" + requiredRole);

    // usage sites supply THEIR OWN value, but share the SAME underlying rule SHAPE
    static boolean deleteAccountCheck(Authentication auth) { return hasRoleMetaAnnotation.test(auth, "ADMIN"); } // @HasRole("ADMIN")
    static boolean generateReportCheck(Authentication auth) { return hasRoleMetaAnnotation.test(auth, "MANAGER"); } // @HasRole("MANAGER")
    static boolean viewDashboardCheck(Authentication auth) { return hasRoleMetaAnnotation.test(auth, "USER"); } // @HasRole("USER")

    public static void main(String[] args) {
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));

        System.out.println("manager calling deleteAccount (@HasRole(\"ADMIN\")): " + deleteAccountCheck(manager));
        System.out.println("manager calling generateReport (@HasRole(\"MANAGER\")): " + generateReportCheck(manager));
        System.out.println("manager calling viewDashboard (@HasRole(\"USER\")): " + viewDashboardCheck(manager)
                + " (manager does NOT directly have ROLE_USER -- no hierarchy applied in this simplified model)");
    }
}
```

How to run: `java MetaAnnotationsLevel3.java`

All three usage sites share the identical underlying `hasRoleMetaAnnotation` shape, but each supplies its own required-role value (`"ADMIN"`, `"MANAGER"`, `"USER"`) — exactly mirroring how a parameterized meta-annotation like `@HasRole("ADMIN")` lets multiple usage sites reuse one common annotation *definition* while still expressing genuinely different, per-site requirements.

## 6. Walkthrough

Trace `checkMethod("IsAdmin", manager)` from Level 2, called *after* the rule redefinition.

1. `checkMethod` looks up `metaAnnotationRules.get("IsAdmin")` — since `defineMetaAnnotation("IsAdmin", ...)` was called a second time with a new lambda, the map's value for the key `"IsAdmin"` has been *replaced* with this newer rule: `auth -> auth.authorities().contains("ROLE_ADMIN") || auth.authorities().contains("ROLE_MANAGER")`.
2. `.test(manager)` invokes this newer rule with `manager`, whose authorities are `{"ROLE_MANAGER"}`.
3. `auth.authorities().contains("ROLE_ADMIN")` checks `{"ROLE_MANAGER"}` for `"ROLE_ADMIN"` — absent, so this is `false`.
4. `auth.authorities().contains("ROLE_MANAGER")` checks the same set for `"ROLE_MANAGER"` — present, so this is `true`.
5. `false || true` evaluates to `true` — `checkMethod` returns `true`, correctly granting the manager, purely because the *definition* associated with the key `"IsAdmin"` changed; critically, neither `checkMethod("IsAdmin", manager)` call site in `main` (representing `deleteAccount` and `banUser`) needed any edit at all to reflect this — they simply look up whatever rule is currently registered under that name at the moment they're invoked.

```
BEFORE redefinition: metaAnnotationRules["IsAdmin"] = (auth) -> authorities.contains("ROLE_ADMIN")
  checkMethod("IsAdmin", manager) -> manager lacks ROLE_ADMIN -> false

--- defineMetaAnnotation("IsAdmin", NEW rule) -- ONE edit, to the definition only ---

AFTER redefinition: metaAnnotationRules["IsAdmin"] = (auth) -> ROLE_ADMIN OR ROLE_MANAGER
  checkMethod("IsAdmin", manager) -> manager HAS ROLE_MANAGER -> true
  (BOTH deleteAccount's and banUser's calls to checkMethod("IsAdmin", ...) automatically reflect this, unedited)
```

## 7. Gotchas & takeaways

> **Gotcha:** a meta-annotation's underlying expression is resolved once, at the meta-annotation's own definition site — a common mistake is expecting a meta-annotation to somehow reference or parameterize itself using the *annotated method's own* parameters directly (the way a directly-applied `@PreAuthorize("#accountId == ...")` naturally can) without additional plumbing (`@AliasFor`-style value substitution) to actually wire a usage-site-specific value into the shared expression — a plain, non-parameterized meta-annotation can only express a fixed rule, identical at every usage site.

- A meta-annotation collapses a repeated `@PreAuthorize`/`@PostAuthorize`/`@Secured` expression into one canonical, named definition, making every usage site both more concise and self-documenting.
- Changing the underlying rule requires editing only the meta-annotation's own definition — every usage site automatically picks up the change, eliminating the maintenance risk of updating a repeated expression consistently across many call sites.
- Parameterized meta-annotations (via `@AliasFor`) let multiple usage sites share one common rule *shape* while each still supplying its own specific value, useful when the underlying check is structurally identical but the exact required role or condition legitimately differs per usage.
- Reach for a meta-annotation once an identical or near-identical expression starts appearing across three or more methods — the repetition itself is the practical signal that consolidating into a named, centrally-defined annotation is worthwhile.
