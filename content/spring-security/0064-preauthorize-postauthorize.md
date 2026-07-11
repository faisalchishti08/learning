---
card: spring-security
gi: 64
slug: preauthorize-postauthorize
title: "@PreAuthorize / @PostAuthorize"
---

## 1. What it is

`@PreAuthorize` and `@PostAuthorize` are the method-level annotations (enabled by `@EnableMethodSecurity`, from earlier in this card set) carrying a SpEL expression evaluated before or after the annotated method runs — the expression has access to the method's own parameters by name (`#accountId`), the current `authentication` object, and (for `@PostAuthorize` specifically) `returnObject`, the value the method actually returned, letting an authorization decision depend on data that only exists after the method body has executed.

```java
@PreAuthorize("#accountId == authentication.principal.id or hasRole('ADMIN')")
public Account getAccount(Long accountId) { ... }

@PostAuthorize("returnObject.ownerId == authentication.principal.id or returnObject.classification == 'PUBLIC'")
public Document findDocumentById(Long documentId) { ... }
```

## 2. Why & when

Many authorization rules genuinely depend on data that isn't available until the method has actually run — whether a loaded `Document`'s owner matches the caller, or whether its classification permits public viewing — and `@PreAuthorize` alone cannot express these, since it only has access to the method's *input* parameters, before any data has been fetched. `@PostAuthorize` fills exactly this gap, at the cost of the method body always running first (even for a request that will ultimately be denied) and, in the case of denial, the already-computed return value being discarded rather than delivered to the caller — a trade-off worth making specifically when the decision genuinely cannot be made any earlier.

Reach for `@PreAuthorize` when:

- The authorization decision can be made entirely from the method's own input parameters and the current authentication — an owner-ID comparison against a passed-in argument, a role check, or a combination via `and`/`or`.
- Avoiding unnecessary work is a priority — since `@PreAuthorize` runs before the method body, a denied call never executes any of the method's actual logic (a database query, an expensive computation), unlike `@PostAuthorize`.

Reach for `@PostAuthorize` when:

- The decision genuinely depends on data only available *after* the method runs — checking a loaded entity's own owner field, its classification, or any other property that doesn't exist until it's been fetched or computed.
- Understanding clearly that the method body *will* execute even for an ultimately-denied call — this is an acceptable trade-off only when the method's own side effects (if any) are safe to have occurred regardless of the final authorization outcome, or when the method is read-only (as in the `findDocumentById` example above).

## 3. Core concept

```
 @PreAuthorize("expression"):
   1. evaluate "expression" using: method's OWN PARAMETERS (#paramName), authentication, hasRole/hasAuthority
   2. TRUE  -> method body RUNS NORMALLY
      FALSE -> AccessDeniedException thrown IMMEDIATELY -- method body NEVER RUNS AT ALL

 @PostAuthorize("expression"):
   1. method body RUNS FIRST, UNCONDITIONALLY, producing a return value
   2. evaluate "expression" using: EVERYTHING @PreAuthorize has, PLUS returnObject (the JUST-COMPUTED result)
   3. TRUE  -> the return value IS delivered to the caller
      FALSE -> AccessDeniedException thrown -- the ALREADY-COMPUTED return value is DISCARDED, never delivered
```

`@PreAuthorize` can prevent the method from ever running; `@PostAuthorize` can only prevent its result from ever being seen.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="PreAuthorize evaluates its expression before the method body runs denying immediately without ever executing the method PostAuthorize lets the method body run first unconditionally then evaluates its expression against the return value discarding that value entirely if the check fails">
  <rect x="15" y="20" width="280" height="60" rx="9" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="155" y="40" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PreAuthorize</text>
  <text x="155" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">check FIRST -&gt; denied means</text>
  <text x="155" y="66" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">method body NEVER RUNS</text>

  <rect x="345" y="20" width="280" height="60" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="1.3"/>
  <text x="485" y="40" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">@PostAuthorize</text>
  <text x="485" y="53" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">method body runs FIRST, then</text>
  <text x="485" y="66" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">checks -- denied DISCARDS the result</text>

  <rect x="180" y="115" width="280" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="135" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">AccessDeniedException on failure,</text>
  <text x="320" y="148" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">either way</text>

  <defs><marker id="a64" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="155" y1="80" x2="270" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a64)"/>
  <line x1="485" y1="80" x2="370" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a64)"/>
</svg>

Both end in the same exception on denial — but only `@PostAuthorize` has already done the work by the time it happens.

## 5. Runnable example

The scenario: implement both annotation-style checks faithfully, using a method-invocation model, then demonstrate `@PostAuthorize`'s "runs first, discards after" behavior concretely by instrumenting the method body with a visible side effect, then combine both on the same object graph for a realistic account-and-document access scenario.

### Level 1 — Basic

Model `@PreAuthorize`'s before-the-call check, denying without ever invoking the underlying method.

```java
import java.util.*;
import java.util.function.Function;

public class PreAuthorizeLevel1 {
    record Authentication(String principalId, Set<String> roles) {}
    static Authentication currentUser;

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }

    static Map<Long, String> accounts = Map.of(1L, "alice's account data", 2L, "bob's account data");

    // models: @PreAuthorize("#accountId == authentication.principal.id or hasRole('ADMIN')")
    static String getAccount(long accountId) {
        boolean ownsIt = accountId == Long.parseLong(currentUser.principalId());
        boolean isAdmin = currentUser.roles().contains("ROLE_ADMIN");
        if (!ownsIt && !isAdmin) throw new AccessDeniedException("cannot access account " + accountId);

        System.out.println("  (method body executing: fetching account " + accountId + ")");
        return accounts.get(accountId);
    }

    public static void main(String[] args) {
        currentUser = new Authentication("1", Set.of("ROLE_USER"));

        System.out.println("own account: " + getAccount(1L));

        try {
            getAccount(2L); // NOT owned, NOT admin
        } catch (AccessDeniedException ex) {
            System.out.println("denied: " + ex.getMessage() + " (note: method body NEVER printed for this call)");
        }
    }
}
```

How to run: `java PreAuthorizeLevel1.java`

The denied call to `getAccount(2L)` never reaches (or prints) the `"method body executing"` line at all — the `AccessDeniedException` is thrown before that point in the method, confirming `@PreAuthorize`'s check genuinely prevents the method body from running, not merely its result from being returned.

### Level 2 — Intermediate

Model `@PostAuthorize`'s after-the-call check, instrumenting the method to prove it runs *before* the authorization decision, even for a call that ultimately gets denied.

```java
import java.util.*;

public class PreAuthorizeLevel2 {
    record Authentication(String principalId, Set<String> roles) {}
    static Authentication currentUser;

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }
    record Document(long id, String ownerId, String classification) {}

    static Map<Long, Document> documents = Map.of(
            10L, new Document(10L, "1", "PUBLIC"),
            11L, new Document(11L, "2", "CONFIDENTIAL")
    );

    // models: @PostAuthorize("returnObject.ownerId == authentication.principal.id or returnObject.classification == 'PUBLIC'")
    static Document findDocumentById(long documentId) {
        Document result = documents.get(documentId); // the METHOD BODY -- runs UNCONDITIONALLY, first
        System.out.println("  (method body executed: loaded document " + documentId + " with classification "
                + result.classification() + ")");

        boolean isOwner = result.ownerId().equals(currentUser.principalId());
        boolean isPublic = result.classification().equals("PUBLIC");
        if (!isOwner && !isPublic) throw new AccessDeniedException("document " + documentId + " not visible to this principal");
        return result;
    }

    public static void main(String[] args) {
        currentUser = new Authentication("5", Set.of("ROLE_USER")); // owns NEITHER document

        System.out.println("public doc: " + findDocumentById(10L));

        try {
            findDocumentById(11L); // CONFIDENTIAL, not owned -- the load STILL happens (see the printed line above the exception)
        } catch (AccessDeniedException ex) {
            System.out.println("denied: " + ex.getMessage());
        }
    }
}
```

How to run: `java PreAuthorizeLevel2.java`

For the *denied* call to `findDocumentById(11L)`, the `"method body executed"` line still prints — proving the document was genuinely loaded, its classification genuinely computed, *before* the authorization check ran and ultimately discarded the result; contrast this with Level 1, where the equivalent line for a denied call never printed at all.

### Level 3 — Advanced

Combine both annotations on related methods in one realistic account-and-document scenario, and add a case where `@PreAuthorize` alone would have been insufficient, motivating `@PostAuthorize`'s necessity concretely.

```java
import java.util.*;

public class PreAuthorizeLevel3 {
    record Authentication(String principalId, Set<String> roles) {}
    static Authentication currentUser;

    static class AccessDeniedException extends RuntimeException { AccessDeniedException(String m) { super(m); } }
    record Account(long id, String ownerId) {}
    record Document(long id, String accountId, String classification) {}

    static Map<Long, Account> accounts = Map.of(1L, new Account(1L, "5"));
    static Map<Long, Document> documents = Map.of(
            100L, new Document(100L, "1", "PRIVATE"), // belongs to account 1 (owned by principal "5")
            200L, new Document(200L, "999", "PRIVATE") // belongs to SOME OTHER account entirely
    );

    // @PreAuthorize works fine HERE: the account ID is a direct method PARAMETER
    static Account getAccount(long accountId) {
        Account acc = accounts.get(accountId);
        boolean owns = acc != null && acc.ownerId().equals(currentUser.principalId());
        if (!owns) throw new AccessDeniedException("cannot access account " + accountId);
        return acc;
    }

    // @PreAuthorize would NOT work here -- the document's OWNING ACCOUNT is only known AFTER loading it;
    // there is no method PARAMETER representing "which account owns this document" to check in advance
    static Document getDocument(long documentId) {
        Document doc = documents.get(documentId); // MUST run first -- no way to know the owning account otherwise
        Account owningAccount = accounts.get(Long.parseLong(doc.accountId()));
        boolean ownsAccount = owningAccount != null && owningAccount.ownerId().equals(currentUser.principalId());
        if (!ownsAccount) throw new AccessDeniedException("document " + documentId + "'s owning account is not yours");
        return doc;
    }

    public static void main(String[] args) {
        currentUser = new Authentication("5", Set.of("ROLE_USER"));

        System.out.println("own account: " + getAccount(1L));
        System.out.println("own document (via owned account): " + getDocument(100L));

        try {
            getDocument(200L); // belongs to an account NOT owned by principal "5"
        } catch (AccessDeniedException ex) {
            System.out.println("denied: " + ex.getMessage());
        }
    }
}
```

How to run: `java PreAuthorizeLevel3.java`

`getAccount` can check ownership purely from its `accountId` parameter, a perfect fit for `@PreAuthorize`; `getDocument` genuinely cannot know which account a document belongs to until after loading it, since that relationship isn't part of the method's input at all — this is precisely the situation motivating `@PostAuthorize`, and the denied call to `getDocument(200L)` still performs the full lookup and ownership computation before ultimately throwing.

## 6. Walkthrough

Trace `getDocument(200L)` from Level 3, the denied call.

1. `doc = documents.get(200L)` retrieves `new Document(200L, "999", "PRIVATE")` — this line runs unconditionally, since there is no earlier authorization gate in this method at all (mirroring `@PostAuthorize`'s design, where the check can only happen after this kind of data becomes available).
2. `owningAccount = accounts.get(Long.parseLong(doc.accountId()))` parses `"999"` into `999L` and looks it up in `accounts` — since `accounts` only contains an entry for key `1L`, this returns `null`.
3. `ownsAccount = owningAccount != null && owningAccount.ownerId().equals(currentUser.principalId())` evaluates `null != null`, which is `false`; because of `&&`'s short-circuit evaluation, `owningAccount.ownerId()` is never even called (which is important, since calling a method on `null` would otherwise throw a `NullPointerException`) — the overall expression is `false`.
4. `if (!ownsAccount)` evaluates `!false`, i.e. `true`, so the method throws `new AccessDeniedException("document 200's owning account is not yours")`.
5. Note that by the time this exception is thrown, the document *was* already fully loaded (step 1) and the ownership computation *was* already fully performed (steps 2–3) — exactly the `@PostAuthorize`-style trade-off: the work happens regardless of the eventual outcome, and only the final delivery of a result to the caller is what's actually prevented by the denial.

```
getDocument(200L):
  doc = documents.get(200L) -> Document(200, accountId="999", PRIVATE)   [LOADED regardless of outcome]
  owningAccount = accounts.get(999) -> null                                [account 999 doesn't exist]
  ownsAccount = (null != null) && ... -> false                            [short-circuits before NPE]
  !ownsAccount -> true -> AccessDeniedException thrown
  (the loaded "doc" object is simply discarded -- never returned to the caller)
```

## 7. Gotchas & takeaways

> **Gotcha:** relying on `@PostAuthorize` for a method with meaningful side effects (writing to a database, sending a notification, charging a payment) is dangerous specifically because the method body — and any side effects within it — runs to completion *before* the authorization check, regardless of whether the check ultimately denies the result; only the *return value* is withheld from the caller on denial, not any side effect the method already performed. Reserve `@PostAuthorize` for read-only or otherwise side-effect-free methods, and use `@PreAuthorize` for anything with real side effects whenever the check can possibly be expressed from the method's input parameters alone.

- `@PreAuthorize` checks before the method runs, using only the method's own parameters and the current authentication — a denied call never executes any of the method's logic.
- `@PostAuthorize` checks after the method has already fully run, additionally having access to `returnObject` — necessary when the decision genuinely depends on data only available after execution, but at the cost of the method body always running regardless of the outcome.
- Prefer `@PreAuthorize` whenever the check can be expressed from input parameters alone, both to avoid unnecessary work and to avoid the side-effect risk `@PostAuthorize` introduces for non-read-only methods.
- The two annotations frequently coexist on related methods within the same application — one method's ownership might be checkable from its parameters (`@PreAuthorize`), while a related method's ownership might only be discoverable after loading related data (`@PostAuthorize`).
