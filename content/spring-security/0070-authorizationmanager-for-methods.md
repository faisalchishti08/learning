---
card: spring-security
gi: 70
slug: authorizationmanager-for-methods
title: "AuthorizationManager for methods"
---

## 1. What it is

`@PreAuthorize`/`@PostAuthorize`/`@PreFilter`/`@PostFilter` are themselves implemented on top of `AuthorizationManager<MethodInvocation>` (the same core interface from the earlier `AuthorizationManager` card, parameterized this time with a method invocation instead of a request) — `PreAuthorizeAuthorizationManager` parses the annotation's SpEL string once and evaluates it per invocation, and applications can bypass the annotations entirely, registering a custom `AuthorizationManager<MethodInvocation>` directly against an `AuthorizationManagerBeforeMethodInterceptor`/`AuthorizationManagerAfterMethodInterceptor` for method-matching patterns annotations can't express as cleanly (a whole package, a naming convention, an interface implementation).

```java
@Bean
static Advisor packageBasedAuthorization() {
    AuthorizationManager<MethodInvocation> manager = (authentication, invocation) ->
            new AuthorizationDecision(authentication.get().getAuthorities().stream()
                    .anyMatch(a -> a.getAuthority().equals("ROLE_INTERNAL_SERVICE")));

    return AuthorizationManagerBeforeMethodInterceptor.pointcut(
            AopUtils.expressionPointcut("execution(* com.example.internal..*(..))"), manager);
}
```

## 2. Why & when

Annotation-based method security requires annotating each protected method individually — perfectly reasonable for most applications, but occasionally exactly the wrong granularity: securing every method across an entire package by a naming or package convention (everything under `com.example.internal`), or applying one blanket rule to every method on classes implementing a particular interface, would mean either annotating dozens of methods identically (repetitive, easy to miss one) or reaching for AOP pointcut expressions directly, registering a custom `AuthorizationManager<MethodInvocation>` against a pointcut matching by pattern rather than by individual annotation.

Reach for a direct, pointcut-based `AuthorizationManager<MethodInvocation>` registration when:

- Securing an entire package, module, or set of classes matching a naming convention uniformly, without needing to annotate every individual method.
- The rule genuinely depends on reflective information about the method itself (its name, its declaring class, its parameter types) rather than anything expressible cleanly as a per-method SpEL expression.
- For the common case of protecting individual, specifically-chosen methods, the `@PreAuthorize`/`@PostAuthorize` annotations remain the more direct, readable, and conventional choice — reach for a raw `AuthorizationManager<MethodInvocation>` registration specifically for the pattern-based cases annotations don't fit well.

## 3. Core concept

```
 @PreAuthorize("hasRole('ADMIN')") on a method
   COMPILES DOWN TO, internally:
     PreAuthorizeAuthorizationManager, parsing "hasRole('ADMIN')" ONCE,
     registered against an AOP pointcut matching JUST that ONE annotated method

 a DIRECT, pointcut-based registration instead:
   AuthorizationManager<MethodInvocation> manager = (authentication, invocation) -> { ... custom logic ... };
   registered against a POINTCUT EXPRESSION matching potentially MANY methods at once
     (a whole package: "execution(* com.example.internal..*(..))")
     (a naming convention: methods starting with "admin")
     (an interface: implementations of a specific interface)

 BOTH approaches ultimately produce the SAME kind of AOP-intercepted, AuthorizationManager-backed enforcement --
   differing only in HOW BROADLY they match methods (one annotation at a time, vs. a pattern matching many at once)
```

Annotations and direct pointcut registration are two different ways to arrive at the identical underlying enforcement mechanism.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Both an individually annotated PreAuthorize method and a pointcut matched set of methods across an entire package ultimately register with the identical AuthorizationManager backed AOP interceptor mechanism differing only in how broadly they match methods">
  <rect x="15" y="20" width="230" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="130" y="38" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">@PreAuthorize on ONE method</text>
  <text x="130" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">annotated individually</text>

  <rect x="15" y="105" width="230" height="42" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="130" y="123" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">pointcut matching a WHOLE PACKAGE</text>
  <text x="130" y="136" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">many methods, ONE registration</text>

  <rect x="380" y="60" width="230" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthorizationManager&lt;MethodInvocation&gt;</text>
  <text x="495" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">the SAME underlying mechanism</text>

  <defs><marker id="a70" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="245" y1="41" x2="380" y2="75" stroke="#8b949e" stroke-width="1" marker-end="url(#a70)"/>
  <line x1="245" y1="126" x2="380" y2="95" stroke="#8b949e" stroke-width="1" marker-end="url(#a70)"/>
</svg>

Same mechanism underneath — one matches a single annotated method, the other matches many methods by pattern.

## 5. Runnable example

The scenario: implement the shared `AuthorizationManager<MethodInvocation>` interface, register one instance mimicking an individual `@PreAuthorize` annotation, then register a second instance matching many methods by a package-style pattern, proving one manager instance protects an entire set of methods uniformly.

### Level 1 — Basic

The core interface and an instance mimicking a single `@PreAuthorize("hasRole('ADMIN')")` annotation.

```java
import java.util.*;
import java.util.function.Supplier;

public class MethodAuthManagerLevel1 {
    record Authentication(Set<String> authorities) {}
    record MethodInvocation(String className, String methodName) {}
    record AuthorizationDecision(boolean granted) {}

    interface AuthorizationManager {
        AuthorizationDecision check(Supplier<Authentication> authentication, MethodInvocation invocation);
    }

    // mimics @PreAuthorize("hasRole('ADMIN')") on ONE specific method
    static AuthorizationManager singleMethodManager = (authSupplier, invocation) ->
            new AuthorizationDecision(authSupplier.get().authorities().contains("ROLE_ADMIN"));

    public static void main(String[] args) {
        Supplier<Authentication> admin = () -> new Authentication(Set.of("ROLE_ADMIN"));
        Supplier<Authentication> regularUser = () -> new Authentication(Set.of("ROLE_USER"));

        MethodInvocation deleteAccount = new MethodInvocation("AccountService", "deleteAccount");

        System.out.println("admin calling deleteAccount: " + singleMethodManager.check(admin, deleteAccount));
        System.out.println("regular user calling deleteAccount: " + singleMethodManager.check(regularUser, deleteAccount));
    }
}
```

How to run: `java MethodAuthManagerLevel1.java`

`singleMethodManager` never even inspects `invocation` in this simplified example — it behaves exactly like a `@PreAuthorize("hasRole('ADMIN')")` annotation would for whatever one method it's registered against, checking only the current authentication's authorities.

### Level 2 — Intermediate

Register a manager matching an entire package by pattern, protecting many methods with a single manager instance.

```java
import java.util.*;
import java.util.function.Supplier;

public class MethodAuthManagerLevel2 {
    record Authentication(Set<String> authorities) {}
    record MethodInvocation(String className, String packageName, String methodName) {}
    record AuthorizationDecision(boolean granted) {}

    interface AuthorizationManager {
        AuthorizationDecision check(Supplier<Authentication> authentication, MethodInvocation invocation);
    }

    // matches an ENTIRE PACKAGE by pattern -- ONE registration protects EVERY method within it
    static boolean matchesPointcut(MethodInvocation invocation) {
        return invocation.packageName().startsWith("com.example.internal");
    }

    static AuthorizationManager packageBasedManager = (authSupplier, invocation) -> {
        if (!matchesPointcut(invocation)) return new AuthorizationDecision(true); // NOT in scope -- doesn't apply at all
        return new AuthorizationDecision(authSupplier.get().authorities().contains("ROLE_INTERNAL_SERVICE"));
    };

    public static void main(String[] args) {
        Supplier<Authentication> internalService = () -> new Authentication(Set.of("ROLE_INTERNAL_SERVICE"));
        Supplier<Authentication> regularUser = () -> new Authentication(Set.of("ROLE_USER"));

        MethodInvocation internalMethod1 = new MethodInvocation("SyncService", "com.example.internal.sync", "runSync");
        MethodInvocation internalMethod2 = new MethodInvocation("CacheService", "com.example.internal.cache", "evictAll");
        MethodInvocation publicMethod = new MethodInvocation("AccountService", "com.example.api", "getAccount");

        System.out.println("internal service calling internal method 1: " + packageBasedManager.check(internalService, internalMethod1));
        System.out.println("regular user calling internal method 2: " + packageBasedManager.check(regularUser, internalMethod2));
        System.out.println("regular user calling PUBLIC method (outside the package): " + packageBasedManager.check(regularUser, publicMethod));
    }
}
```

How to run: `java MethodAuthManagerLevel2.java`

`packageBasedManager` is a single manager instance, but it correctly protects *both* `internalMethod1` and `internalMethod2` (both under `com.example.internal`), denying the regular user's attempt on the second one, while `publicMethod` (outside the matched package) is unconditionally granted, since `matchesPointcut` correctly identifies it as out of this manager's scope entirely.

### Level 3 — Advanced

Combine an annotation-equivalent (single-method) manager and a pattern-based (package-wide) manager registered together, confirming each correctly governs only its own intended scope without interfering with the other.

```java
import java.util.*;
import java.util.function.Supplier;

public class MethodAuthManagerLevel3 {
    record Authentication(Set<String> authorities) {}
    record MethodInvocation(String className, String packageName, String methodName) {}
    record AuthorizationDecision(boolean granted, String decidedBy) {}

    interface AuthorizationManager {
        AuthorizationDecision check(Supplier<Authentication> authentication, MethodInvocation invocation);
    }

    // manager 1: an ANNOTATION-EQUIVALENT, targeting ONE specific method by exact identity
    static AuthorizationManager deleteAccountManager = (authSupplier, invocation) -> {
        boolean matches = invocation.className().equals("AccountService") && invocation.methodName().equals("deleteAccount");
        if (!matches) return new AuthorizationDecision(true, "not-applicable");
        return new AuthorizationDecision(authSupplier.get().authorities().contains("ROLE_ADMIN"), "deleteAccountManager");
    };

    // manager 2: a PATTERN-BASED manager, matching an entire package
    static AuthorizationManager internalPackageManager = (authSupplier, invocation) -> {
        if (!invocation.packageName().startsWith("com.example.internal")) return new AuthorizationDecision(true, "not-applicable");
        return new AuthorizationDecision(authSupplier.get().authorities().contains("ROLE_INTERNAL_SERVICE"), "internalPackageManager");
    };

    static List<AuthorizationManager> registeredManagers = List.of(deleteAccountManager, internalPackageManager);

    // models Spring AOP's real behavior: EVERY applicable manager must agree (an ALL-OF composition)
    static AuthorizationDecision evaluateAll(Supplier<Authentication> authSupplier, MethodInvocation invocation) {
        for (AuthorizationManager manager : registeredManagers) {
            AuthorizationDecision decision = manager.check(authSupplier, invocation);
            if (!"not-applicable".equals(decision.decidedBy()) && !decision.granted()) return decision; // first APPLICABLE denial wins
        }
        return new AuthorizationDecision(true, "all-applicable-managers-granted");
    }

    public static void main(String[] args) {
        Supplier<Authentication> regularUser = () -> new Authentication(Set.of("ROLE_USER"));

        MethodInvocation deleteAccount = new MethodInvocation("AccountService", "com.example.api", "deleteAccount");
        MethodInvocation internalSync = new MethodInvocation("SyncService", "com.example.internal.sync", "runSync");
        MethodInvocation unrelatedMethod = new MethodInvocation("ReportService", "com.example.api", "getReport");

        System.out.println("regular user, deleteAccount: " + evaluateAll(regularUser, deleteAccount));
        System.out.println("regular user, internal sync: " + evaluateAll(regularUser, internalSync));
        System.out.println("regular user, unrelated method: " + evaluateAll(regularUser, unrelatedMethod));
    }
}
```

How to run: `java MethodAuthManagerLevel3.java`

`deleteAccount` is denied by `deleteAccountManager` specifically (the regular user lacks `ROLE_ADMIN`); `internalSync` is denied by `internalPackageManager` specifically (lacking `ROLE_INTERNAL_SERVICE`); `unrelatedMethod` matches neither manager's scope at all, so both report `"not-applicable"` and the call is granted by default — demonstrating that multiple registered managers, each with their own distinct matching scope, coexist correctly without interfering with methods outside their respective concerns.

## 6. Walkthrough

Trace `evaluateAll(regularUser, unrelatedMethod)` from Level 3.

1. The `for` loop begins with `deleteAccountManager`: `invocation.className().equals("AccountService") && invocation.methodName().equals("deleteAccount")` checks `unrelatedMethod`'s fields — `"ReportService".equals("AccountService")` is `false`, so `matches` is `false`, and the manager returns `new AuthorizationDecision(true, "not-applicable")`.
2. Back in `evaluateAll`, the condition `!"not-applicable".equals(decision.decidedBy()) && !decision.granted()` checks this returned decision: `!"not-applicable".equals("not-applicable")` is `!true`, i.e. `false` — the overall condition is `false && ...`, which short-circuits to `false` without even evaluating `!decision.granted()` — so this manager's result does *not* trigger an early return.
3. The loop continues to `internalPackageManager`: `invocation.packageName().startsWith("com.example.internal")` checks `"com.example.api".startsWith("com.example.internal")` — this is `false`, so the manager again returns `new AuthorizationDecision(true, "not-applicable")`, and the same logic in step 2 applies again, not triggering an early return.
4. The `for` loop completes without either manager ever producing an applicable denial, so `evaluateAll` reaches its final line, returning `new AuthorizationDecision(true, "all-applicable-managers-granted")` — the call is granted, correctly, since neither registered manager's matching scope actually covers this particular method at all.
5. This demonstrates the "not-applicable" sentinel doing real work: without distinguishing "this manager doesn't apply here" from "this manager applies and grants," a manager returning `granted=true` purely because it doesn't match anything could be misleadingly indistinguishable from a manager that genuinely evaluated the request and found it acceptable — the distinction matters for correctly reasoning about which manager, if any, actually made a substantive decision for a given call.

```
unrelatedMethod (ReportService.getReport, package com.example.api):
  deleteAccountManager:      className mismatch -> "not-applicable" -> skipped, no early return
  internalPackageManager:    package mismatch    -> "not-applicable" -> skipped, no early return
  loop completes with no applicable denial -> GRANTED ("all-applicable-managers-granted")
```

## 7. Gotchas & takeaways

> **Gotcha:** when multiple `AuthorizationManager<MethodInvocation>` registrations have overlapping matching scopes (two pointcuts both matching the same method), the effective combined behavior depends on how they're composed (all must grant, versus any one being sufficient) — this composition detail is easy to overlook when registering several pattern-based managers independently, and worth testing explicitly for any method genuinely falling under more than one registration's scope.

- `@PreAuthorize` and friends are themselves implemented on top of `AuthorizationManager<MethodInvocation>`, registered against an AOP pointcut matching exactly the one annotated method.
- Registering a custom `AuthorizationManager<MethodInvocation>` directly, against a broader pointcut expression, is the right tool for securing an entire package, module, or naming-convention-matched set of methods uniformly, without annotating each one individually.
- A manager instance covering a broad pointcut should clearly distinguish "this method is outside my scope, defer entirely" from "this method is in my scope, and I'm granting it" — conflating the two makes composing multiple managers correctly much harder to reason about.
- For individually-chosen, specific methods, the `@PreAuthorize`/`@PostAuthorize` annotations remain the more direct and conventional choice — reach for raw `AuthorizationManager<MethodInvocation>` registration specifically for pattern-based, many-methods-at-once scenarios.
