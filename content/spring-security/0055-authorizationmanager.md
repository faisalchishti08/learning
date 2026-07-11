---
card: spring-security
gi: 55
slug: authorizationmanager
title: "AuthorizationManager"
---

## 1. What it is

`AuthorizationManager<T>` is the modern, unified interface (`AuthorizationDecision check(Supplier<Authentication>, T object)`) behind every authorization decision in current Spring Security — both URL-based (`AuthorizationFilter` calling it with an `HttpServletRequest`) and method-based (`@PreAuthorize`'s AOP interceptor calling it with a method invocation) — replacing the older, more complex `AccessDecisionManager`/`AccessDecisionVoter` machinery (covered later in this section as legacy) with a single, simpler contract returning one `AuthorizationDecision` per check.

```java
public interface AuthorizationManager<T> {
    AuthorizationDecision check(Supplier<Authentication> authentication, T object);
}

public class AuthorizationDecision {
    private final boolean granted;
    public AuthorizationDecision(boolean granted) { this.granted = granted; }
    public boolean isGranted() { return granted; }
}
```

## 2. Why & when

The older `AccessDecisionManager` design required combining multiple independent `AccessDecisionVoter`s (each returning grant/deny/abstain) via a configurable strategy (affirmative, unanimous, consensus) — flexible, but complex to reason about and rarely needed in its full generality by most applications. `AuthorizationManager` simplifies this to the single, common case: one object making one yes/no decision, given the current `Authentication` and whatever is being checked (a request, a method invocation) — every built-in authorization mechanism (`AuthorityAuthorizationManager` for role checks, `WebExpressionAuthorizationManager` for SpEL expressions, `AuthenticatedAuthorizationManager` for the plain "is logged in" check) implements this one interface, and they compose via simple delegation (`AuthorizationManagers.allOf`/`anyOf`) rather than the older voter-strategy machinery.

Reach for understanding `AuthorizationManager` directly when:

- Writing a genuinely custom authorization rule beyond what `hasRole`/`hasAuthority`/a SpEL expression can express — implementing this one interface directly is the modern equivalent of what a custom `AccessDecisionVoter` used to require, with meaningfully less ceremony.
- Understanding what actually backs `authorizeHttpRequests`'s fluent DSL (the next card) or `@PreAuthorize`'s SpEL expressions — both ultimately compile down to constructing and registering `AuthorizationManager` instances.
- Migrating legacy code still using `AccessDecisionVoter`/`AccessDecisionManager` — recognizing that a custom voter's logic maps onto a single custom `AuthorizationManager` implementation is the key insight for a clean migration.

## 3. Core concept

```
 AuthorizationFilter (or the method-security AOP interceptor) calls:
   authorizationManager.check(() -> currentAuthentication, requestOrMethodInvocation)

 the returned AuthorizationDecision:
   isGranted() == true   -> access ALLOWED, request/method proceeds
   isGranted() == false  -> AccessDeniedException thrown

 BUILT-IN implementations, each handling ONE kind of check:
   AuthorityAuthorizationManager       -- "does the principal have this specific authority/role?"
   AuthenticatedAuthorizationManager   -- "is there a genuinely authenticated (non-anonymous) principal at all?"
   WebExpressionAuthorizationManager   -- "does this SpEL expression evaluate to true?"

 COMPOSING multiple managers:
   AuthorizationManagers.allOf(...)  -- ALL must grant
   AuthorizationManagers.anyOf(...)  -- ANY ONE granting is sufficient
```

One interface, one method, one boolean-shaped decision — every authorization check in modern Spring Security reduces to this.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AuthorizationFilter calls check on an AuthorizationManager passing the current Authentication supplier and the object being checked such as a request the manager returns an AuthorizationDecision that is either granted allowing access to proceed or denied throwing an AccessDeniedException">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthorizationFilter</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.check(auth, request)</text>

  <rect x="220" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="310" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AuthorizationManager</text>
  <text x="310" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; AuthorizationDecision</text>

  <rect x="455" y="20" width="160" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="535" y="45" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">granted -&gt; proceed</text>

  <rect x="455" y="115" width="160" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="535" y="140" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">denied -&gt; AccessDeniedException</text>

  <defs><marker id="a55" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="88" x2="220" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a55)"/>
  <line x1="400" y1="80" x2="455" y2="45" stroke="#8b949e" stroke-width="1" marker-end="url(#a55)"/>
  <line x1="400" y1="95" x2="455" y2="132" stroke="#8b949e" stroke-width="1" marker-end="url(#a55)"/>
</svg>

One check, one decision, one of two outcomes — no voter counting, no strategy configuration.

## 5. Runnable example

The scenario: implement the core interface and two built-in-style managers, then compose them with `allOf`/`anyOf`-style logic, then write a genuinely custom manager expressing a rule no built-in one covers.

### Level 1 — Basic

The core interface and a minimal role-checking implementation.

```java
import java.util.*;
import java.util.function.Supplier;

public class AuthorizationManagerLevel1 {
    record Authentication(String principal, Set<String> authorities) {}
    record AuthorizationDecision(boolean granted) {}

    interface AuthorizationManager<T> {
        AuthorizationDecision check(Supplier<Authentication> authentication, T object);
    }

    static class AuthorityAuthorizationManager implements AuthorizationManager<String> {
        private final String requiredAuthority;
        AuthorityAuthorizationManager(String requiredAuthority) { this.requiredAuthority = requiredAuthority; }
        public AuthorizationDecision check(Supplier<Authentication> authentication, String object) {
            return new AuthorizationDecision(authentication.get().authorities().contains(requiredAuthority));
        }
    }

    public static void main(String[] args) {
        AuthorizationManager<String> requiresAdmin = new AuthorityAuthorizationManager("ROLE_ADMIN");

        Supplier<Authentication> alice = () -> new Authentication("alice", Set.of("ROLE_USER"));
        Supplier<Authentication> bob = () -> new Authentication("bob", Set.of("ROLE_USER", "ROLE_ADMIN"));

        System.out.println("alice: " + requiresAdmin.check(alice, "/admin/reports"));
        System.out.println("bob: " + requiresAdmin.check(bob, "/admin/reports"));
    }
}
```

How to run: `java AuthorizationManagerLevel1.java`

`AuthorityAuthorizationManager.check` simply checks whether the supplied `Authentication`'s authorities contain the required one — alice (`ROLE_USER` only) gets a denied decision, bob (`ROLE_USER` and `ROLE_ADMIN`) gets a granted one.

### Level 2 — Intermediate

Add a second manager type and compose both with `allOf`/`anyOf`-style logic.

```java
import java.util.*;
import java.util.function.Supplier;

public class AuthorizationManagerLevel2 {
    record Authentication(String principal, Set<String> authorities, boolean fullyAuthenticated) {}
    record AuthorizationDecision(boolean granted) {}

    interface AuthorizationManager<T> { AuthorizationDecision check(Supplier<Authentication> auth, T object); }

    static class AuthorityAuthorizationManager implements AuthorizationManager<Object> {
        String required;
        AuthorityAuthorizationManager(String required) { this.required = required; }
        public AuthorizationDecision check(Supplier<Authentication> auth, Object o) {
            return new AuthorizationDecision(auth.get().authorities().contains(required));
        }
    }

    static class AuthenticatedAuthorizationManager implements AuthorizationManager<Object> {
        public AuthorizationDecision check(Supplier<Authentication> auth, Object o) {
            return new AuthorizationDecision(auth.get().fullyAuthenticated());
        }
    }

    static AuthorizationManager<Object> allOf(List<AuthorizationManager<Object>> managers) {
        return (auth, o) -> new AuthorizationDecision(managers.stream().allMatch(m -> m.check(auth, o).granted()));
    }

    static AuthorizationManager<Object> anyOf(List<AuthorizationManager<Object>> managers) {
        return (auth, o) -> new AuthorizationDecision(managers.stream().anyMatch(m -> m.check(auth, o).granted()));
    }

    public static void main(String[] args) {
        AuthorizationManager<Object> requiresAuthenticatedAdmin = allOf(List.of(
                new AuthenticatedAuthorizationManager(), new AuthorityAuthorizationManager("ROLE_ADMIN")
        ));

        Supplier<Authentication> anonymous = () -> new Authentication("anonymousUser", Set.of("ROLE_ADMIN"), false);
        Supplier<Authentication> realAdmin = () -> new Authentication("alice", Set.of("ROLE_ADMIN"), true);

        System.out.println("anonymous (somehow has ROLE_ADMIN authority but NOT authenticated): "
                + requiresAuthenticatedAdmin.check(anonymous, "resource"));
        System.out.println("real authenticated admin: " + requiresAuthenticatedAdmin.check(realAdmin, "resource"));
    }
}
```

How to run: `java AuthorizationManagerLevel2.java`

`allOf` requires every composed manager to grant — the anonymous case fails specifically because `AuthenticatedAuthorizationManager` denies it (despite having the right authority string), demonstrating that composition genuinely combines independent checks rather than any single one being sufficient on its own.

### Level 3 — Advanced

Write a genuinely custom manager expressing a rule no built-in manager covers: access granted only during business hours *and* only to users whose department matches the requested resource.

```java
import java.time.LocalTime;
import java.util.*;
import java.util.function.Supplier;

public class AuthorizationManagerLevel3 {
    record Authentication(String principal, String department, Set<String> authorities) {}
    record AuthorizationDecision(boolean granted, String reason) {}
    record Resource(String path, String requiredDepartment) {}

    interface AuthorizationManager<T> { AuthorizationDecision check(Supplier<Authentication> auth, T object); }

    // a CUSTOM manager: combines a time-of-day rule with a department-matching rule -- no built-in manager does this
    static class BusinessHoursDepartmentAuthorizationManager implements AuthorizationManager<Resource> {
        private final LocalTime open, close;
        BusinessHoursDepartmentAuthorizationManager(LocalTime open, LocalTime close) { this.open = open; this.close = close; }

        public AuthorizationDecision check(Supplier<Authentication> authSupplier, Resource resource) {
            LocalTime now = LocalTime.now();
            if (now.isBefore(open) || now.isAfter(close)) {
                return new AuthorizationDecision(false, "outside business hours (" + open + "-" + close + ")");
            }
            Authentication auth = authSupplier.get();
            if (!auth.department().equals(resource.requiredDepartment()) && !auth.authorities().contains("ROLE_ADMIN")) {
                return new AuthorizationDecision(false, "department mismatch: " + auth.department() + " != " + resource.requiredDepartment());
            }
            return new AuthorizationDecision(true, "granted");
        }
    }

    public static void main(String[] args) {
        AuthorizationManager<Resource> manager = new BusinessHoursDepartmentAuthorizationManager(
                LocalTime.of(0, 0), LocalTime.of(23, 59) // wide-open window so this example is time-independent when run
        );

        Supplier<Authentication> financeUser = () -> new Authentication("bob", "FINANCE", Set.of("ROLE_USER"));
        Supplier<Authentication> adminUser = () -> new Authentication("alice", "ENGINEERING", Set.of("ROLE_ADMIN"));

        Resource financeReport = new Resource("/finance/reports", "FINANCE");

        System.out.println("finance user accessing finance report: " + manager.check(financeUser, financeReport));
        System.out.println("engineering admin accessing finance report: " + manager.check(adminUser, financeReport));
    }
}
```

How to run: `java AuthorizationManagerLevel3.java`

`BusinessHoursDepartmentAuthorizationManager` implements a rule combining a time check and a department check in one custom manager — the finance user accesses the finance report normally by matching department, while the engineering admin, despite a different department, is granted access anyway via the `ROLE_ADMIN` override — logic that exists nowhere as a single built-in manager, demonstrating exactly why writing a custom `AuthorizationManager` is the right tool for genuinely bespoke rules.

## 6. Walkthrough

Trace `manager.check(adminUser, financeReport)` from Level 3.

1. `check` first computes `now = LocalTime.now()` and checks `now.isBefore(open) || now.isAfter(close)` — since `open` is `00:00` and `close` is `23:59`, this condition is `false` for essentially any time the code runs, so the business-hours guard doesn't deny access here.
2. `auth = authSupplier.get()` invokes the supplier, producing `new Authentication("alice", "ENGINEERING", Set.of("ROLE_ADMIN"))`.
3. `!auth.department().equals(resource.requiredDepartment())` checks `!"ENGINEERING".equals("FINANCE")`, which is `!false`, i.e. `true` — the department genuinely does not match; but this is combined with `&&`, so the full condition also checks `!auth.authorities().contains("ROLE_ADMIN")`, which is `!true`, i.e. `false`.
4. The overall `if` condition is `true && false`, i.e. `false` — so the department-mismatch denial branch does *not* fire, specifically because alice's `ROLE_ADMIN` authority provides an override, even though her department genuinely doesn't match the resource's required department.
5. Control reaches the final line, returning `new AuthorizationDecision(true, "granted")` — alice's access succeeds, for a reason distinct from bob's (whose department directly matched): hers is granted via the administrative override built into this custom manager's logic.

```
adminUser (ENGINEERING, ROLE_ADMIN) accessing FINANCE resource:
  business hours check -> within hours -> continue
  department check: "ENGINEERING" != "FINANCE" -> true, BUT has ROLE_ADMIN -> override -> overall condition false
  -> falls through to: AuthorizationDecision(true, "granted")
```

## 7. Gotchas & takeaways

> **Gotcha:** `AuthorizationManager.check` receives a `Supplier<Authentication>`, not the `Authentication` object directly — this is deliberate, allowing the authentication to be resolved lazily only if the manager's logic actually needs it (some checks, like a pure IP-based rule, might never call `.get()` at all), but a custom manager that calls `.get()` multiple times without caching the result risks redundant work if resolving the `Authentication` is itself non-trivial.

- `AuthorizationManager<T>` is the single, unified interface behind every modern authorization decision, replacing the older, more complex `AccessDecisionManager`/voter design with one method returning one `AuthorizationDecision`.
- Built-in managers (`AuthorityAuthorizationManager`, `AuthenticatedAuthorizationManager`, `WebExpressionAuthorizationManager`) each handle one specific, common kind of check, and compose via straightforward `allOf`/`anyOf` delegation.
- Both `authorizeHttpRequests`'s fluent DSL and `@PreAuthorize`'s SpEL expressions ultimately construct and register `AuthorizationManager` instances underneath — understanding this interface clarifies what those higher-level APIs actually compile down to.
- Writing a genuinely custom `AuthorizationManager` is the modern, simpler equivalent of what a custom `AccessDecisionVoter` used to require, appropriate whenever a rule combines multiple independent conditions that no single built-in manager expresses.
