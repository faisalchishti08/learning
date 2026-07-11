---
card: spring-security
gi: 68
slug: method-security-spel-expressions
title: "Method security SpEL expressions"
---

## 1. What it is

Method security's SpEL expressions are evaluated against a root object exposing several built-in variables and functions — `authentication` (the current `Authentication`), `principal` (shorthand for `authentication.principal`), method parameters accessible by name via `#paramName` (requires compiling with `-parameters`, or an explicit `@P("paramName")` annotation), `hasRole(...)`/`hasAuthority(...)`/`hasPermission(...)` functions, and — critically — references to any Spring bean via `@beanName.method(...)` syntax, letting an expression call into arbitrary application logic as part of its evaluation.

```java
@PreAuthorize("#userId == authentication.principal.id or hasRole('ADMIN')")
public User getUser(Long userId) { ... }

@PreAuthorize("@accountSecurity.isOwner(#accountId, authentication.name)") // delegates to a custom @Component bean
public Account getAccount(Long accountId) { ... }

@Component("accountSecurity")
class AccountSecurityService {
    public boolean isOwner(Long accountId, String username) { /* real business logic here */ return true; }
}
```

## 2. Why & when

The built-in expression vocabulary (`hasRole`, `hasAuthority`, parameter references, `authentication`) covers the majority of authorization rules directly and concisely as a single expression string, but some rules genuinely need real application logic — a database lookup to check ownership, a call to an external permission service, multi-step business logic that would be unreasonably awkward to express as inline SpEL — and the `@beanName.method(...)` syntax is the escape hatch making this possible without abandoning the declarative annotation style entirely: the expression itself stays a simple, readable one-liner, delegating any actual complexity to a plain, independently testable Spring bean.

Reach for each expression capability specifically when:

- `#paramName` for referencing a method's own arguments directly — the most common building block for ownership-style checks (`#accountId == authentication.principal.id`).
- `@beanName.method(...)` whenever the check requires genuine logic beyond a simple comparison — looking something up, calling another service, applying a multi-step business rule — keeping that logic in ordinary, testable Java code rather than cramming it into an expression string.
- `hasPermission(...)` (covered in more depth by the ACL cards later in this section) specifically for domain-object-level permission checks backed by a pluggable `PermissionEvaluator`.
- Understand that `#paramName` requires either compiling with parameter name information retained (`-parameters` javac flag, Spring Boot's default) or an explicit `@P("paramName")` annotation on the parameter — without either, Spring Security cannot resolve the parameter's name at runtime, and the expression fails.

## 3. Core concept

```
 SpEL root object exposes (INSIDE any @PreAuthorize/@PostAuthorize/@PreFilter/@PostFilter expression):

   authentication              -- the current Authentication object
   principal                    -- shorthand for authentication.principal
   #paramName                   -- the method's OWN parameter, referenced by name
   returnObject                 -- (POST-annotations ONLY) the method's return value
   filterObject                 -- (FILTER annotations ONLY) the CURRENT element being filtered
   hasRole('X') / hasAuthority('X') / hasAnyRole('X','Y')  -- the SAME checks covered earlier in this section
   hasPermission(target, perm)   -- delegates to a configured PermissionEvaluator (ACL cards, later)
   @beanName.someMethod(...)     -- calls ANY method on ANY registered Spring bean named "beanName"
```

Every one of these is available inside the SAME expression string, freely combinable with `and`/`or`/`not`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A PreAuthorize expression references the accountId parameter directly and delegates to a custom accountSecurity bean's isOwner method combining a built in check with a call into real application logic all within one expression string">
  <rect x="15" y="60" width="280" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="155" y="80" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@PreAuthorize(</text>
  <text x="155" y="93" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">"@accountSecurity.isOwner(#accountId, ...)")</text>

  <rect x="360" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="425" y="45" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">#accountId (param)</text>

  <rect x="360" y="105" width="230" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="125" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@accountSecurity bean</text>
  <text x="475" y="138" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">.isOwner(...) real logic</text>

  <defs><marker id="a68" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="295" y1="72" x2="360" y2="40" stroke="#8b949e" stroke-width="1" marker-end="url(#a68)"/>
  <line x1="295" y1="95" x2="360" y2="120" stroke="#8b949e" stroke-width="1" marker-end="url(#a68)"/>
</svg>

A parameter reference and a bean reference, combined in one declarative expression that delegates real work elsewhere.

## 5. Runnable example

The scenario: implement a `#paramName`-based check first, then delegate to a custom bean method for logic too involved for inline expression syntax, then combine both styles with `hasRole` in one realistic, multi-condition rule.

### Level 1 — Basic

A `#paramName`-based ownership check, the simplest expression building block.

```java
import java.util.*;

public class MethodSecuritySpelLevel1 {
    record Authentication(String principalId, Set<String> authorities) {}

    // models: @PreAuthorize("#accountId == authentication.principal.id")
    static boolean checkExpression(long accountId, Authentication authentication) {
        return accountId == Long.parseLong(authentication.principalId());
    }

    public static void main(String[] args) {
        Authentication bob = new Authentication("2", Set.of("ROLE_USER"));

        System.out.println("bob accessing account 2 (his own): " + checkExpression(2L, bob));
        System.out.println("bob accessing account 5 (not his): " + checkExpression(5L, bob));
    }
}
```

How to run: `java MethodSecuritySpelLevel1.java`

`checkExpression` directly compares the method's own `accountId` parameter against `authentication.principalId()` — bob's request for account `2` (matching his own ID) is granted, while his request for account `5` is denied.

### Level 2 — Intermediate

Delegate to a custom bean method for logic genuinely too involved for an inline comparison — checking against a set of collaborators, not just a single owner ID.

```java
import java.util.*;

public class MethodSecuritySpelLevel2 {
    record Authentication(String principalId) {}

    // the CUSTOM bean referenced via @accountSecurity in a real @PreAuthorize expression
    static class AccountSecurityService {
        Map<Long, Set<String>> accountCollaborators = Map.of(
                1L, Set.of("5", "6"), // account 1 has TWO collaborators, either may access it
                2L, Set.of("7")
        );

        boolean isCollaborator(long accountId, String principalId) {
            return accountCollaborators.getOrDefault(accountId, Set.of()).contains(principalId);
        }
    }

    // models: @PreAuthorize("@accountSecurity.isCollaborator(#accountId, authentication.name)")
    static boolean checkExpression(long accountId, Authentication auth, AccountSecurityService accountSecurity) {
        return accountSecurity.isCollaborator(accountId, auth.principalId());
    }

    public static void main(String[] args) {
        AccountSecurityService accountSecurity = new AccountSecurityService();

        Authentication user5 = new Authentication("5");
        Authentication user7 = new Authentication("7");
        Authentication user999 = new Authentication("999");

        System.out.println("user 5 accessing account 1 (collaborator): " + checkExpression(1L, user5, accountSecurity));
        System.out.println("user 7 accessing account 1 (NOT a collaborator there): " + checkExpression(1L, user7, accountSecurity));
        System.out.println("user 999 accessing account 2: " + checkExpression(2L, user999, accountSecurity));
    }
}
```

How to run: `java MethodSecuritySpelLevel2.java`

`checkExpression` delegates entirely to `accountSecurity.isCollaborator`, which looks up a multi-member collaborator set per account — logic that would be awkward to express as an inline SpEL expression, but reads as a clean, single method call in the annotation, with the actual lookup logic living in ordinary, independently testable Java code.

### Level 3 — Advanced

Combine `#paramName`, a bean delegate, and `hasRole` in one realistic expression, mirroring a genuine multi-condition production rule.

```java
import java.util.*;

public class MethodSecuritySpelLevel3 {
    record Authentication(String principalId, Set<String> authorities) {}

    static class AccountSecurityService {
        Map<Long, Set<String>> collaborators = Map.of(1L, Set.of("5", "6"));
        boolean isCollaborator(long accountId, String principalId) {
            return collaborators.getOrDefault(accountId, Set.of()).contains(principalId);
        }
    }

    // models: @PreAuthorize("hasRole('ADMIN') or #accountId == authentication.principal.id
    //                        or @accountSecurity.isCollaborator(#accountId, authentication.name)")
    static boolean checkExpression(long accountId, Authentication auth, AccountSecurityService accountSecurity) {
        boolean isAdmin = auth.authorities().contains("ROLE_ADMIN");
        boolean ownsIt = accountId == Long.parseLong(auth.principalId());
        boolean isCollaborator = accountSecurity.isCollaborator(accountId, auth.principalId());
        return isAdmin || ownsIt || isCollaborator;
    }

    public static void main(String[] args) {
        AccountSecurityService accountSecurity = new AccountSecurityService();

        Authentication admin = new Authentication("999", Set.of("ROLE_ADMIN"));
        Authentication owner = new Authentication("1", Set.of("ROLE_USER"));
        Authentication collaborator = new Authentication("6", Set.of("ROLE_USER"));
        Authentication stranger = new Authentication("42", Set.of("ROLE_USER"));

        for (Authentication auth : List.of(admin, owner, collaborator, stranger)) {
            System.out.println(auth.principalId() + " accessing account 1: " + checkExpression(1L, auth, accountSecurity));
        }
    }
}
```

How to run: `java MethodSecuritySpelLevel3.java`

Four different callers are each granted (or denied) access to account `1` via three completely different paths: the admin via `isAdmin`, the owner (whose own ID is `"1"`, matching `accountId`) via `ownsIt`, the collaborator via `isCollaborator`, and only the stranger — matching none of the three conditions — is correctly denied.

## 6. Walkthrough

Trace `checkExpression(1L, collaborator, accountSecurity)` from Level 3, where `collaborator = Authentication("6", {ROLE_USER})`.

1. `isAdmin = auth.authorities().contains("ROLE_ADMIN")` checks `{"ROLE_USER"}` for `"ROLE_ADMIN"` — absent, so `isAdmin` is `false`.
2. `ownsIt = accountId == Long.parseLong(auth.principalId())` computes `Long.parseLong("6")`, i.e. `6L`, and compares `1L == 6L` — this is `false`, so `ownsIt` is `false`.
3. `isCollaborator = accountSecurity.isCollaborator(1L, "6")` calls into the bean method: `collaborators.getOrDefault(1L, Set.of())` retrieves `{"5", "6"}` (the collaborator set for account `1`), and `.contains("6")` checks whether this set contains `"6"` — it does, so `isCollaborator` is `true`.
4. The method returns `isAdmin || ownsIt || isCollaborator`, i.e. `false || false || true`, which is `true` — access is granted, specifically and only through the third condition, the delegated bean method call.
5. This demonstrates all three expression styles working together within one combined rule: a built-in role check, a direct parameter comparison, and a delegated call into real application logic, with the overall `or` composition meaning any single one succeeding is sufficient to grant access — exactly the flexibility SpEL-based method security is designed to provide over the more limited `@Secured`/`@RolesAllowed` annotations from the two previous cards.

```
checkExpression(accountId=1, auth=collaborator(id="6"), accountSecurity):
  isAdmin        -> authorities lack ROLE_ADMIN         -> false
  ownsIt         -> 1L == 6L                              -> false
  isCollaborator -> accountSecurity.isCollaborator(1, "6") -> collaborators[1] = {5,6}, contains "6" -> true
  -> false || false || true -> GRANTED (via the collaborator check specifically)
```

## 7. Gotchas & takeaways

> **Gotcha:** `#paramName`-style parameter references require the application to be compiled with parameter name information retained (the `-parameters` javac flag, which Spring Boot's Maven/Gradle plugins enable by default) — in an environment where this information is stripped (some minified or heavily optimized builds, certain non-standard build configurations), `#paramName` silently fails to resolve at runtime, typically producing a `SpelEvaluationException`; the `@P("paramName")` annotation on the parameter is the reliable fallback that works regardless of compiler flags.

- Method security SpEL expressions expose `authentication`, `principal`, method parameters via `#paramName`, and `returnObject`/`filterObject` (for the post/filter annotation variants), all combinable with standard boolean operators.
- `@beanName.method(...)` syntax lets an expression delegate to arbitrary Spring bean logic, keeping the annotation itself concise and readable while pushing any real complexity into ordinary, independently testable Java code.
- `#paramName` resolution depends on retained parameter name metadata at compile time (or an explicit `@P` annotation) — a detail worth confirming explicitly if a seemingly correct expression unexpectedly fails at runtime.
- Combining multiple conditions with `or`/`and` in a single expression (a role check, a parameter comparison, and a delegated bean call) is a natural and common pattern for expressing genuinely multi-path authorization rules in one declarative annotation.
