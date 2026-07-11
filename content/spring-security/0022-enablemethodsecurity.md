---
card: spring-security
gi: 22
slug: enablemethodsecurity
title: "@EnableMethodSecurity"
---

## 1. What it is

`@EnableMethodSecurity` is the annotation (on a `@Configuration` class) that turns on method-level authorization, letting individual Spring-managed bean methods declare their own access rules directly via `@PreAuthorize`, `@PostAuthorize`, `@PreFilter`, and `@PostFilter`, checked via an AOP proxy wrapped around the bean, independently of any URL-based rule in a `SecurityFilterChain`. It is the modern replacement for the older `@EnableGlobalMethodSecurity`, and defaults to enabling only `@PreAuthorize`/`@PostAuthorize` (`@Secured` and JSR-250 annotations like `@RolesAllowed` require explicitly opting in).

```java
@Configuration
@EnableMethodSecurity
public class MethodSecurityConfig {}

@Service
class AccountService {
    @PreAuthorize("hasRole('ADMIN')")
    public void deleteAccount(Long accountId) { /* ... */ }

    @PreAuthorize("#accountId == authentication.principal.id or hasRole('ADMIN')")
    public Account getAccount(Long accountId) { /* ... */ }
}
```

## 2. Why & when

URL-based authorization (`authorizeHttpRequests`) checks access at the boundary of the web layer, based purely on the request path — but many real access rules genuinely depend on the *data* involved, not just the URL: "a user may view their own account, or any account if they're an admin" cannot be expressed as a URL pattern at all, since the same `/accounts/{id}` path needs a different decision per `id` and per caller. Method security moves the authorization check to exactly the method where that decision can be made with full context (the method's actual arguments, and often its return value), and — because it's enforced via AOP on the bean itself — the same protection applies no matter how the method is invoked: from a REST controller, a scheduled job, or another service, not just from one specific URL.

Reach for `@EnableMethodSecurity` and its annotations when:

- An access rule depends on the specific data being accessed, not merely the URL — comparing the caller's identity against the resource's owner, checking a specific field of the argument or return value.
- The same protected operation must be reachable through multiple entry points (a REST endpoint, a message listener, an internal scheduled task) and the authorization rule needs to apply uniformly regardless of caller, rather than being duplicated at each entry point's URL-based configuration.
- `@PreAuthorize` for checking access *before* a method runs (most common, cheapest — avoids doing work that will be rejected); `@PostAuthorize` for when the decision genuinely requires the method's return value (checking a loaded entity's owner field after loading it); `@PreFilter`/`@PostFilter` for filtering a collection argument or return value down to only the elements the caller may see.

## 3. Core concept

```
 @EnableMethodSecurity   -- wraps annotated beans in an AOP proxy

 caller invokes service.deleteAccount(accountId)
        |
        v
 AOP proxy intercepts the call BEFORE the real method body runs
        |
        v
 @PreAuthorize("hasRole('ADMIN')") expression evaluated
   against the CURRENT Authentication (from SecurityContextHolder)
        |
        +-- expression TRUE  -> real method body actually runs
        +-- expression FALSE -> AccessDeniedException thrown, method body NEVER runs
```

The check happens at the method boundary itself, using a SpEL expression that has access to the method's own arguments (`#accountId`) and the current `Authentication`.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A caller invokes a service method wrapped in an AOP proxy the proxy evaluates a PreAuthorize SpEL expression against the current Authentication before the real method body runs if the expression is true the method body executes otherwise an AccessDeniedException is thrown and the method body never runs">
  <rect x="15" y="65" width="130" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="80" y="92" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">caller invokes</text>

  <rect x="190" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="280" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AOP proxy</text>
  <text x="280" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">@PreAuthorize check</text>

  <rect x="460" y="15" width="160" height="42" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="540" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">real method body runs</text>

  <rect x="460" y="125" width="160" height="42" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="540" y="150" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AccessDeniedException</text>

  <defs><marker id="a22" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="145" y1="88" x2="190" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a22)"/>
  <line x1="370" y1="78" x2="460" y2="36" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a22)"/>
  <text x="400" y="55" fill="#8b949e" font-size="6.5" font-family="sans-serif">TRUE</text>
  <line x1="370" y1="98" x2="460" y2="140" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a22)"/>
  <text x="400" y="120" fill="#8b949e" font-size="6.5" font-family="sans-serif">FALSE</text>
</svg>

The proxy's decision happens strictly *before* the real method executes — a denied call never runs a single line of the actual business logic.

## 5. Runnable example

The scenario: model `@PreAuthorize`-style expression checking with a proxy wrapping a real service, then add an owner-comparison rule that depends on the method's own argument, then add a `@PostAuthorize`-style check that depends on the *return value*, the case where a `@PreAuthorize` check alone isn't enough.

### Level 1 — Basic

A proxy wrapping a service method, checking a role-based expression before invoking the real method.

```java
import java.util.*;
import java.util.function.Supplier;

public class MethodSecurityLevel1 {
    record Authentication(String principal, Set<String> roles) {}
    static Authentication currentUser; // models SecurityContextHolder.getContext().getAuthentication()

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }

    static class AccountService {
        void deleteAccountReal(Long accountId) { System.out.println("account " + accountId + " deleted"); }

        // models the AOP proxy's @PreAuthorize("hasRole('ADMIN')") check
        void deleteAccount(Long accountId) {
            if (!currentUser.roles().contains("ROLE_ADMIN")) {
                throw new AccessDeniedException("hasRole('ADMIN') evaluated to false for " + currentUser.principal());
            }
            deleteAccountReal(accountId);
        }
    }

    public static void main(String[] args) {
        AccountService service = new AccountService();

        currentUser = new Authentication("bob", Set.of("ROLE_USER"));
        try {
            service.deleteAccount(42L);
        } catch (AccessDeniedException ex) {
            System.out.println("denied: " + ex.getMessage());
        }

        currentUser = new Authentication("alice", Set.of("ROLE_ADMIN"));
        service.deleteAccount(42L);
    }
}
```

How to run: `java MethodSecurityLevel1.java`

`deleteAccount` checks `currentUser.roles()` before ever calling `deleteAccountReal`; for bob (`ROLE_USER` only) it throws without the real body running at all, while for alice (`ROLE_ADMIN`) the check passes and `deleteAccountReal` actually executes and prints its confirmation.

### Level 2 — Intermediate

Add an owner-comparison expression that reads the method's own argument, modeling `@PreAuthorize("#accountId == authentication.principal.id or hasRole('ADMIN')")`.

```java
import java.util.*;

public class MethodSecurityLevel2 {
    record Authentication(String principalId, Set<String> roles) {}
    static Authentication currentUser;

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }
    record Account(long id, String ownerName, double balance) {}

    static class AccountService {
        Map<Long, Account> accounts = Map.of(
                1L, new Account(1L, "alice", 500.0),
                2L, new Account(2L, "bob", 250.0)
        );

        Account getAccountReal(long accountId) { return accounts.get(accountId); }

        // models @PreAuthorize("#accountId == authentication.principal.id or hasRole('ADMIN')")
        Account getAccount(long accountId) {
            boolean ownsAccount = String.valueOf(accountId).equals(currentUser.principalId());
            boolean isAdmin = currentUser.roles().contains("ROLE_ADMIN");
            if (!ownsAccount && !isAdmin) {
                throw new AccessDeniedException("principal " + currentUser.principalId() + " may not access account " + accountId);
            }
            return getAccountReal(accountId);
        }
    }

    public static void main(String[] args) {
        AccountService service = new AccountService();

        currentUser = new Authentication("1", Set.of("ROLE_USER")); // "owns" account 1
        System.out.println("own account: " + service.getAccount(1L));

        try {
            service.getAccount(2L); // does NOT own account 2, not an admin
        } catch (AccessDeniedException ex) {
            System.out.println("denied: " + ex.getMessage());
        }

        currentUser = new Authentication("99", Set.of("ROLE_ADMIN")); // admin, owns neither
        System.out.println("admin viewing account 2: " + service.getAccount(2L));
    }
}
```

How to run: `java MethodSecurityLevel2.java`

`getAccount`'s check depends on *both* the method's own `accountId` argument and the caller's identity — the same method call succeeds or fails purely based on the relationship between the two, exactly the kind of data-dependent rule a URL pattern alone could never express.

### Level 3 — Advanced

Add a `@PostAuthorize`-style check that depends on the loaded entity's return value — the case where the decision genuinely cannot be made until after the method body has already run.

```java
import java.util.*;

public class MethodSecurityLevel3 {
    record Authentication(String principalId, Set<String> roles) {}
    static Authentication currentUser;

    static class AccessDeniedException extends RuntimeException {
        AccessDeniedException(String msg) { super(msg); }
    }
    record Document(long id, String ownerId, String classification) {}

    static class DocumentService {
        Map<Long, Document> documents = Map.of(
                10L, new Document(10L, "1", "PUBLIC"),
                11L, new Document(11L, "2", "CONFIDENTIAL")
        );

        Document findByIdReal(long documentId) { return documents.get(documentId); }

        // models @PostAuthorize("returnObject.ownerId == authentication.principal.id or returnObject.classification == 'PUBLIC'")
        Document findById(long documentId) {
            Document result = findByIdReal(documentId); // the REAL body runs FIRST -- unavoidable, since the check needs its output
            boolean isOwner = result.ownerId().equals(currentUser.principalId());
            boolean isPublic = result.classification().equals("PUBLIC");
            if (!isOwner && !isPublic) {
                throw new AccessDeniedException("document " + documentId + " (" + result.classification()
                        + ") not visible to principal " + currentUser.principalId());
            }
            return result;
        }
    }

    public static void main(String[] args) {
        DocumentService service = new DocumentService();

        currentUser = new Authentication("5", Set.of("ROLE_USER")); // not the owner of either document

        System.out.println("public doc: " + service.findById(10L)); // classification=PUBLIC -> visible to anyone

        try {
            service.findById(11L); // CONFIDENTIAL, and principal 5 is not the owner (owner is "2")
        } catch (AccessDeniedException ex) {
            System.out.println("denied: " + ex.getMessage());
        }
    }
}
```

How to run: `java MethodSecurityLevel3.java`

`findById`'s authorization check reads `result.classification()` and `result.ownerId()` — fields only available *after* `findByIdReal` has already loaded the document — which is exactly why `@PostAuthorize` (checked after the method body runs, throwing away the result on denial) exists as a distinct annotation from `@PreAuthorize` (checked before, using only the method's input arguments).

## 6. Walkthrough

Trace `service.findById(11L)` from Level 3, given `currentUser = Authentication("5", {ROLE_USER})`.

1. `findById(11L)` is called; its first line, `Document result = findByIdReal(11L)`, runs *unconditionally* — there is no authorization gate before this line, since the check that follows needs `result`'s own fields to evaluate.
2. `findByIdReal(11L)` looks up `documents.get(11L)`, returning `new Document(11L, "2", "CONFIDENTIAL")` — this is assigned to `result`.
3. `isOwner` is computed as `result.ownerId().equals(currentUser.principalId())`, i.e. `"2".equals("5")`, which is `false`.
4. `isPublic` is computed as `result.classification().equals("PUBLIC")`, i.e. `"CONFIDENTIAL".equals("PUBLIC")`, which is also `false`.
5. Since both `isOwner` and `isPublic` are `false`, the `if (!isOwner && !isPublic)` condition is `true`, so `findById` throws `AccessDeniedException`, and the caller in `main` catches it and prints the denial message — note that `findByIdReal` had *already fully executed* by this point; the document was loaded from the map and then discarded, its data never actually returned to the caller.
6. Compare this with the first call, `findById(10L)`: `result.classification()` is `"PUBLIC"`, so `isPublic` is `true` regardless of `isOwner`, and the method returns `result` normally — the document object *is* returned to the caller in this case.

```
findById(10L): load document -> classification=PUBLIC -> isPublic=true -> ALLOWED, result returned
findById(11L): load document -> classification=CONFIDENTIAL, owner="2" != "5" -> DENIED, result discarded
```

## 7. Gotchas & takeaways

> **Gotcha:** `@PreAuthorize`/`@PostAuthorize`/etc. are enforced via a Spring AOP proxy, which means calling an annotated method *from within the same class* (a self-invocation, bypassing the proxy) silently skips the check entirely — this is a well-known Spring AOP limitation, not specific to method security, but it is a particularly dangerous place for it to bite, since the method appears protected in the source code while actually being unprotected for internal calls.

- `@EnableMethodSecurity` enables data-aware authorization checks directly on service methods, independent of and complementary to URL-based `authorizeHttpRequests` rules.
- `@PreAuthorize` runs before the method body and can reference the method's own arguments (`#argName`); `@PostAuthorize` runs after and can additionally reference `returnObject`, at the cost of having already executed the method body even on eventual denial.
- `@PreFilter`/`@PostFilter` apply the same idea to collection-shaped arguments or return values, filtering out individual elements the caller may not see rather than allowing or denying the whole call.
- Because enforcement relies on an AOP proxy around the bean, self-invocation (a method calling another `@PreAuthorize`-annotated method on `this` rather than through the injected proxy) bypasses the check — refactor such calls to go through a separate bean, or the injected proxy, if self-invocation is unavoidable.
