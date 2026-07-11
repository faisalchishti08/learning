---
card: spring-security
gi: 32
slug: run-as-authentication-replacement
title: "Run-as authentication replacement"
---

## 1. What it is

Run-as is a legacy mechanism where, for the duration of a single secured method call, Spring Security temporarily *replaces* the current `Authentication` in `SecurityContextHolder` with a different one carrying an additional, elevated, short-lived authority (conventionally prefixed `ROLE_RUN_AS_`), then restores the original `Authentication` once the method call returns — letting that one method (and anything it internally calls) act with temporarily elevated privilege, without the caller's own authorities ever actually changing.

```java
// conceptual: what a RunAsManager does around a secured method invocation
Authentication original = SecurityContextHolder.getContext().getAuthentication();
Authentication runAs = new RunAsUserToken("key", original.getPrincipal(), original.getCredentials(),
        addRunAsAuthority(original.getAuthorities()), original.getClass());
SecurityContextHolder.getContext().setAuthentication(runAs); // TEMPORARY replacement
try {
    return secureMethod.invoke(); // runs WITH the elevated authority
} finally {
    SecurityContextHolder.getContext().setAuthentication(original); // ALWAYS restored afterward
}
```

## 2. Why & when

Some operations need to internally call another component that requires a permission the *original caller* should never be granted directly — a reporting service that a regular user is allowed to invoke, but which internally needs to call a data-access layer requiring an elevated, internal-only authority the calling user should never hold in general. Run-as solves this narrow case by granting the elevated authority only for the duration of that one specific call chain, and only implicitly (the caller is never actually granted the elevated role; it exists only inside `SecurityContextHolder` for the scope of the call). In modern Spring Security applications, this same problem is far more commonly solved by using `@EnableMethodSecurity`'s finer-grained checks combined with a genuinely separate internal service/component boundary, or a manually scoped call to a privileged operation — run-as itself is rarely reached for in new code, but understanding it explains a still-encountered legacy pattern.

Reach for understanding run-as (largely historical) when:

- Encountering `RunAsManager`, `RunAsUserToken`, or a `ROLE_RUN_AS_*` authority in an older codebase, and needing to understand what temporarily elevated the calling context's permissions for one specific call.
- Explaining why a method appears to succeed with a permission the calling user's own token doesn't actually list — run-as is one possible (if unlikely, in modern code) explanation, alongside method security's AOP-based invocation always being worth double-checking first.
- For new code, prefer explicit internal service boundaries, a system-level service account genuinely granted the elevated permission and invoked deliberately, or simply restructuring the authorization checks so no temporary elevation is needed at all — run-as's implicit, temporary privilege escalation is harder to audit than an explicit, dedicated internal caller.

## 3. Core concept

```
 BEFORE the secured method call:
   SecurityContextHolder holds: Authentication(principal=bob, authorities=[ROLE_USER])

 RunAsManager.buildRunAs(...) is invoked (typically configured per-method via metadata):
   SecurityContextHolder REPLACED with: RunAsUserToken(principal=bob, authorities=[ROLE_USER, ROLE_RUN_AS_REPORT_INTERNAL])

 DURING the method call (and anything it calls internally):
   any authorization check for ROLE_RUN_AS_REPORT_INTERNAL now SUCCEEDS

 AFTER the method call returns (success OR exception):
   SecurityContextHolder RESTORED to the ORIGINAL: Authentication(principal=bob, authorities=[ROLE_USER])
   bob's OWN authorities were NEVER actually changed -- the elevation existed ONLY inside this one call's scope
```

The elevation is temporary, scoped, and automatically reverted — bob's real, persistent set of authorities never changes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before a secured method call the SecurityContext holds bob's normal authorities during the call it is temporarily replaced with a RunAsUserToken carrying an additional elevated authority after the call returns the original context is restored unchanged">
  <rect x="15" y="70" width="170" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="90" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">BEFORE: bob</text>
  <text x="100" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">[ROLE_USER]</text>

  <rect x="235" y="20" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="42" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">DURING method call:</text>
  <text x="335" y="55" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">RunAsUserToken</text>
  <text x="335" y="68" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">[ROLE_USER, ROLE_RUN_AS_*]</text>

  <rect x="480" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="90" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">AFTER: bob</text>
  <text x="555" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">[ROLE_USER] (restored)</text>

  <defs><marker id="a32" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="185" y1="88" x2="235" y2="60" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a32)"/>
  <line x1="435" y1="60" x2="480" y2="88" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a32)"/>
</svg>

The elevated authority exists only in the shaded middle box — before and after, bob's context is identical.

## 5. Runnable example

The scenario: model a run-as-style temporary authority elevation around a single method call, including guaranteed restoration even on failure, then use it to let an outer, lower-privileged call succeed at an inner, higher-privileged check, then contrast it directly with the modern preferred alternative (a dedicated internal service call) to show why run-as is rarely reached for today.

### Level 1 — Basic

A minimal run-as wrapper: temporarily add an authority, run a supplier, always restore afterward.

```java
import java.util.*;
import java.util.function.Supplier;

public class RunAsLevel1 {
    static Set<String> currentAuthorities = new HashSet<>(Set.of("ROLE_USER")); // models SecurityContextHolder

    static <T> T runAs(String temporaryAuthority, Supplier<T> action) {
        Set<String> original = new HashSet<>(currentAuthorities); // SNAPSHOT before elevation
        try {
            currentAuthorities.add(temporaryAuthority);
            return action.get();
        } finally {
            currentAuthorities = original; // ALWAYS restored, even if action.get() threw
        }
    }

    public static void main(String[] args) {
        System.out.println("before: " + currentAuthorities);

        String result = runAs("ROLE_RUN_AS_REPORT_INTERNAL", () -> {
            System.out.println("  during call: " + currentAuthorities);
            return "report generated";
        });

        System.out.println("result: " + result);
        System.out.println("after: " + currentAuthorities);
    }
}
```

How to run: `java RunAsLevel1.java`

Inside the lambda passed to `runAs`, `currentAuthorities` includes the temporary `"ROLE_RUN_AS_REPORT_INTERNAL"` entry; once `runAs` returns, `currentAuthorities` is back to its original, pre-elevation value — the `finally` block guarantees this restoration runs regardless of how the action completes.

### Level 2 — Intermediate

Use the temporary elevation to let an outer, lower-privileged operation succeed at calling an inner, higher-privileged check, and confirm restoration even when the inner call throws.

```java
import java.util.*;
import java.util.function.Supplier;

public class RunAsLevel2 {
    static Set<String> currentAuthorities = new HashSet<>(Set.of("ROLE_USER"));

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }

    static <T> T runAs(String temporaryAuthority, Supplier<T> action) {
        Set<String> original = new HashSet<>(currentAuthorities);
        try {
            currentAuthorities.add(temporaryAuthority);
            return action.get();
        } finally {
            currentAuthorities = original;
        }
    }

    // an INTERNAL operation requiring an authority regular users should never hold directly
    static String internalDataAccess() {
        if (!currentAuthorities.contains("ROLE_RUN_AS_REPORT_INTERNAL")) {
            throw new AccessDeniedException("internalDataAccess requires ROLE_RUN_AS_REPORT_INTERNAL");
        }
        return "internal data retrieved";
    }

    // the PUBLIC-FACING operation bob is actually allowed to call
    static String generateReport() {
        return runAs("ROLE_RUN_AS_REPORT_INTERNAL", RunAsLevel2::internalDataAccess);
    }

    public static void main(String[] args) {
        System.out.println("bob calling generateReport(): " + generateReport());

        try {
            internalDataAccess(); // bob calling the INTERNAL method DIRECTLY, with no run-as wrapper active
        } catch (AccessDeniedException ex) {
            System.out.println("bob calling internalDataAccess() directly: " + ex.getMessage());
        }

        System.out.println("bob's authorities after everything: " + currentAuthorities);
    }
}
```

How to run: `java RunAsLevel2.java`

`generateReport()` succeeds because it wraps `internalDataAccess()` in `runAs`, temporarily granting the required authority; calling `internalDataAccess()` directly (bypassing `generateReport`'s run-as wrapper) fails, since bob's actual, persistent authorities never include `ROLE_RUN_AS_REPORT_INTERNAL` outside that specific wrapped call.

### Level 3 — Advanced

Contrast run-as with the modern, preferred alternative: a dedicated internal service, genuinely and permanently granted the elevated authority, invoked explicitly rather than via implicit temporary elevation — showing why this alternative is easier to reason about and audit.

```java
import java.util.*;
import java.util.function.Supplier;

public class RunAsLevel3 {
    static Set<String> currentAuthorities = new HashSet<>(Set.of("ROLE_USER"));

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }

    static <T> T runAs(String temporaryAuthority, Supplier<T> action) {
        Set<String> original = new HashSet<>(currentAuthorities);
        try {
            currentAuthorities.add(temporaryAuthority);
            return action.get();
        } finally {
            currentAuthorities = original;
        }
    }

    static String internalDataAccess(Set<String> callerAuthorities) {
        if (!callerAuthorities.contains("ROLE_RUN_AS_REPORT_INTERNAL") && !callerAuthorities.contains("ROLE_INTERNAL_REPORT_SERVICE")) {
            throw new AccessDeniedException("internalDataAccess requires elevated internal authority");
        }
        return "internal data retrieved";
    }

    // OLD STYLE: run-as, implicit, temporary elevation
    static String generateReportRunAsStyle() {
        return runAs("ROLE_RUN_AS_REPORT_INTERNAL", () -> internalDataAccess(currentAuthorities));
    }

    // MODERN STYLE: a dedicated, explicitly-invoked internal service account with its OWN, permanent (but narrowly scoped) authority
    static class InternalReportService {
        static final Set<String> SERVICE_AUTHORITIES = Set.of("ROLE_INTERNAL_REPORT_SERVICE");
        String generateReport() {
            return internalDataAccess(SERVICE_AUTHORITIES); // called EXPLICITLY as its own, separate identity
        }
    }

    public static void main(String[] args) {
        System.out.println("run-as style: " + generateReportRunAsStyle());
        System.out.println("bob's authorities afterward (unchanged): " + currentAuthorities);

        InternalReportService service = new InternalReportService();
        System.out.println("modern style (explicit internal service): " + service.generateReport());
        System.out.println("bob's authorities never touched by the modern style: " + currentAuthorities);
    }
}
```

How to run: `java RunAsLevel3.java`

Both styles produce the same result (`"internal data retrieved"`), but the modern style never mutates any shared, ambient `currentAuthorities` state at all — `InternalReportService` simply carries its own fixed, permanent `SERVICE_AUTHORITIES`, invoked as its own explicit call, which is generally easier to audit (the elevated authority is visible directly on the service class, not conjured temporarily and implicitly mid-call-stack) than run-as's approach of mutating the ambient security context for the duration of a call.

## 6. Walkthrough

Trace `generateReportRunAsStyle()` from Level 3.

1. `generateReportRunAsStyle()` calls `runAs("ROLE_RUN_AS_REPORT_INTERNAL", () -> internalDataAccess(currentAuthorities))` — note the lambda captures `currentAuthorities` by reference to the *variable*, not a snapshot, so whatever `runAs` does to it before invoking the lambda is what `internalDataAccess` will actually see.
2. Inside `runAs`, `original` snapshots the current state (`{ROLE_USER}`) into a new set, then `currentAuthorities.add("ROLE_RUN_AS_REPORT_INTERNAL")` mutates the *shared* `currentAuthorities` set in place, so it now holds `{ROLE_USER, ROLE_RUN_AS_REPORT_INTERNAL}`.
3. `action.get()` runs next, invoking the lambda, which calls `internalDataAccess(currentAuthorities)` — since `currentAuthorities` now includes the temporary authority, the check `!callerAuthorities.contains("ROLE_RUN_AS_REPORT_INTERNAL")` is `false`, so no exception is thrown, and the method returns `"internal data retrieved"`.
4. Back in `runAs`, the `try` block's `return action.get()` completes with this value, and the `finally` block runs regardless, reassigning `currentAuthorities = original` — restoring it to the pre-elevation snapshot, `{ROLE_USER}`.
5. `generateReportRunAsStyle()` returns the `"internal data retrieved"` value it got from `runAs`, and the subsequent `println("bob's authorities afterward (unchanged): " + currentAuthorities)` confirms the restoration: the set printed is exactly `{ROLE_USER}`, with no trace of the temporary elevation remaining.

```
before runAs():   currentAuthorities = {ROLE_USER}
runAs adds temp:  currentAuthorities = {ROLE_USER, ROLE_RUN_AS_REPORT_INTERNAL}   <- during the wrapped call only
runAs restores:   currentAuthorities = {ROLE_USER}                                <- back to original, in finally
```

## 7. Gotchas & takeaways

> **Gotcha:** run-as's temporary elevation is scoped to the current thread's `SecurityContextHolder` for the duration of the call — if the wrapped method spawns work on a *different* thread (an async task, a new thread not propagating the security context), that other thread will not see the elevated authority at all, a common source of confusion when run-as "doesn't seem to work" for asynchronous code paths.

- Run-as temporarily replaces the current `Authentication` with one carrying an additional authority for the scope of a single method call, then unconditionally restores the original afterward, even on failure.
- The calling principal's own, persistent authorities are never actually changed — the elevation exists only inside `SecurityContextHolder` for the duration of the wrapped call.
- Modern Spring Security applications rarely reach for run-as; an explicit, dedicated internal service or component boundary with its own genuinely (and narrowly) granted authority is generally easier to audit and reason about than an implicit, temporary, ambient elevation.
- Because the elevation lives in thread-local `SecurityContextHolder` state, it does not automatically propagate to work spawned on other threads — a relevant caveat for any asynchronous or multi-threaded call chain.
