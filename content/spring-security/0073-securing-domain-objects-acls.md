---
card: spring-security
gi: 73
slug: securing-domain-objects-acls
title: "Securing domain objects (ACLs)"
---

## 1. What it is

Spring Security's ACL (Access Control List) module addresses per-object, per-recipient permissions at scale — not "can any user with `ROLE_USER` view *some* document" (a role check), but "can *this specific user* perform *this specific action* on *this specific document instance*," where the answer can differ independently for every single object and every single user, and needs to be efficiently queryable across potentially millions of objects and users, backed by a dedicated relational schema rather than expressed inline in code.

```java
@PreAuthorize("hasPermission(#documentId, 'com.example.Document', 'READ')")
public Document getDocument(Long documentId) { ... }

// the actual per-object, per-user grant lives in the ACL database tables, managed separately:
aclService.createAcl(new ObjectIdentityImpl(Document.class, documentId));
MutableAcl acl = (MutableAcl) aclService.readAclById(objectIdentity);
acl.insertAce(acl.getEntries().size(), BasePermission.READ, new PrincipalSid("alice"), true);
aclService.updateAcl(acl);
```

## 2. Why & when

The `hasPermission`/ownership-comparison patterns from earlier `@PreAuthorize` cards work well when access can be derived from a simple rule (an owner-ID field, a department match), but genuinely fine-grained, per-object, per-recipient access — a specific document shared with three specific colleagues, a specific folder where one user has read-only access while another has full edit rights, entirely independent of any role or ownership pattern — needs a scalable way to store and query "who can do what to this specific instance" without hand-rolling a custom permissions table and query logic for every domain object type that needs it. Spring Security's ACL module provides exactly this: a generic, reusable schema and API for object-level permission grants, at the cost of real setup complexity and a dedicated database schema most applications never actually need.

Reach for the ACL module when:

- Individual object instances (not just object *types* or classes of objects) need independently configurable permissions per specific recipient — a genuinely per-document, per-user sharing model, similar to a file-sharing or collaborative-document application.
- The number of distinct object/recipient permission combinations is large enough that a generic, indexed, purpose-built schema meaningfully outperforms and outscales a hand-rolled equivalent.
- Never reach for ACLs when a simpler pattern suffices — an owner-ID comparison (from the earlier `@PreAuthorize`/`@PostAuthorize` card), a role-based check, or even a straightforward custom join table specific to one domain object type, are all considerably less setup and maintenance overhead for applications that don't genuinely need the ACL module's full generality.

## 3. Core concept

```
 the CORE QUESTION ACLs answer:
   "can PRINCIPAL X perform PERMISSION Y on this SPECIFIC INSTANCE of DOMAIN OBJECT Z?"

 NOT expressible efficiently as a simple rule, because:
   - the answer varies per SPECIFIC INSTANCE (not just per object TYPE)
   - the answer varies per SPECIFIC PRINCIPAL (not just per ROLE)
   - grants need to be independently ADDED/REMOVED at runtime, per object/principal PAIR

 ACL's ANSWER: a DEDICATED, GENERIC schema (covered in depth in the next card) storing exactly this --
   one row per (object instance, principal or authority, specific permission, granted/denied) combination,
   queried via hasPermission(...) inside a normal @PreAuthorize expression
```

A genuinely different shape of question from "does this role satisfy this rule" — this is "does this specific grant exist for this specific pair."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three documents each have independent per user permission grants document 1 grants alice read access document 2 grants bob write access and alice read access document 3 grants nobody any access these grants are stored in a dedicated ACL schema and queried via hasPermission rather than derived from any role or ownership rule">
  <rect x="15" y="15" width="180" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="35" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Document 1</text>
  <text x="105" y="48" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">alice: READ</text>

  <rect x="15" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="90" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Document 2</text>
  <text x="105" y="103" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">bob: WRITE</text>
  <text x="105" y="116" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">alice: READ</text>

  <rect x="15" y="140" width="180" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="161" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Document 3: (no grants)</text>

  <rect x="400" y="60" width="220" height="60" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="83" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">hasPermission(#docId, 'READ')</text>
  <text x="510" y="96" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">queries the ACL schema directly</text>

  <defs><marker id="a73" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="35" x2="400" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#a73)"/>
  <line x1="195" y1="100" x2="400" y2="95" stroke="#8b949e" stroke-width="1" marker-end="url(#a73)"/>
  <line x1="195" y1="157" x2="400" y2="110" stroke="#8b949e" stroke-width="1" marker-end="url(#a73)"/>
</svg>

Three documents, each with an entirely independent permission story — not derivable from any single role or ownership rule.

## 5. Runnable example

The scenario: model a simplified ACL store — per-object, per-principal permission grants — and a `hasPermission`-style check function, then demonstrate genuinely independent per-instance grants across multiple documents, then add revocation, proving grants can be added and removed at runtime independently per object/principal pair.

### Level 1 — Basic

A minimal ACL store: a map from (object, principal) pairs to a set of granted permissions.

```java
import java.util.*;

public class DomainObjectAclLevel1 {
    record ObjectIdentity(String type, long id) {}
    record AclKey(ObjectIdentity object, String principal) {}

    static Map<AclKey, Set<String>> aclGrants = new HashMap<>();

    static void grant(ObjectIdentity object, String principal, String permission) {
        aclGrants.computeIfAbsent(new AclKey(object, principal), k -> new HashSet<>()).add(permission);
    }

    static boolean hasPermission(ObjectIdentity object, String principal, String permission) {
        return aclGrants.getOrDefault(new AclKey(object, principal), Set.of()).contains(permission);
    }

    public static void main(String[] args) {
        ObjectIdentity document1 = new ObjectIdentity("Document", 1L);

        grant(document1, "alice", "READ");

        System.out.println("alice can READ document 1: " + hasPermission(document1, "alice", "READ"));
        System.out.println("alice can WRITE document 1 (never granted): " + hasPermission(document1, "alice", "WRITE"));
        System.out.println("bob can READ document 1 (never granted to bob): " + hasPermission(document1, "bob", "READ"));
    }
}
```

How to run: `java DomainObjectAclLevel1.java`

`grant` records exactly one specific `(object, principal, permission)` combination; `hasPermission` only returns `true` for combinations that were explicitly granted — alice's `READ` grant on document 1 doesn't extend to `WRITE` on the same document, nor does it extend to bob at all, demonstrating the fully independent, per-instance, per-principal nature of ACL grants.

### Level 2 — Intermediate

Demonstrate genuinely independent grants across multiple document instances, proving the same principal can have entirely different permissions on different objects.

```java
import java.util.*;

public class DomainObjectAclLevel2 {
    record ObjectIdentity(String type, long id) {}
    record AclKey(ObjectIdentity object, String principal) {}

    static Map<AclKey, Set<String>> aclGrants = new HashMap<>();

    static void grant(ObjectIdentity object, String principal, String permission) {
        aclGrants.computeIfAbsent(new AclKey(object, principal), k -> new HashSet<>()).add(permission);
    }

    static boolean hasPermission(ObjectIdentity object, String principal, String permission) {
        return aclGrants.getOrDefault(new AclKey(object, principal), Set.of()).contains(permission);
    }

    public static void main(String[] args) {
        ObjectIdentity document1 = new ObjectIdentity("Document", 1L);
        ObjectIdentity document2 = new ObjectIdentity("Document", 2L);
        ObjectIdentity document3 = new ObjectIdentity("Document", 3L);

        grant(document1, "alice", "READ");
        grant(document2, "alice", "READ");
        grant(document2, "alice", "WRITE"); // alice has BOTH read and write on document 2 specifically
        // document3: NO grants for alice at all

        for (ObjectIdentity doc : List.of(document1, document2, document3)) {
            System.out.println(doc + " -- alice: READ=" + hasPermission(doc, "alice", "READ")
                    + ", WRITE=" + hasPermission(doc, "alice", "WRITE"));
        }
    }
}
```

How to run: `java DomainObjectAclLevel2.java`

alice has read-only access to document 1, both read and write access to document 2, and no access at all to document 3 — three genuinely different permission profiles for the identical principal, entirely independent of any role or ownership rule, and each fully attributable to explicit, per-instance grants recorded individually.

### Level 3 — Advanced

Add revocation and confirm grants can be added and removed at runtime independently, without affecting any other object/principal combination.

```java
import java.util.*;

public class DomainObjectAclLevel3 {
    record ObjectIdentity(String type, long id) {}
    record AclKey(ObjectIdentity object, String principal) {}

    static Map<AclKey, Set<String>> aclGrants = new HashMap<>();

    static void grant(ObjectIdentity object, String principal, String permission) {
        aclGrants.computeIfAbsent(new AclKey(object, principal), k -> new HashSet<>()).add(permission);
    }

    static void revoke(ObjectIdentity object, String principal, String permission) {
        Set<String> permissions = aclGrants.get(new AclKey(object, principal));
        if (permissions != null) permissions.remove(permission);
    }

    static boolean hasPermission(ObjectIdentity object, String principal, String permission) {
        return aclGrants.getOrDefault(new AclKey(object, principal), Set.of()).contains(permission);
    }

    public static void main(String[] args) {
        ObjectIdentity sharedDoc = new ObjectIdentity("Document", 42L);

        grant(sharedDoc, "alice", "READ");
        grant(sharedDoc, "alice", "WRITE");
        grant(sharedDoc, "bob", "READ");

        System.out.println("before revocation -- alice WRITE: " + hasPermission(sharedDoc, "alice", "WRITE")
                + ", bob READ: " + hasPermission(sharedDoc, "bob", "READ"));

        revoke(sharedDoc, "alice", "WRITE"); // revoke ONLY alice's WRITE grant, on THIS specific document

        System.out.println("after revoking alice's WRITE:");
        System.out.println("  alice WRITE: " + hasPermission(sharedDoc, "alice", "WRITE") + " (revoked)");
        System.out.println("  alice READ: " + hasPermission(sharedDoc, "alice", "READ") + " (UNAFFECTED -- different permission)");
        System.out.println("  bob READ: " + hasPermission(sharedDoc, "bob", "READ") + " (UNAFFECTED -- different principal)");
    }
}
```

How to run: `java DomainObjectAclLevel3.java`

Revoking alice's `WRITE` grant on `sharedDoc` leaves her `READ` grant on the *same* document completely intact, and leaves bob's `READ` grant on the *same* document equally untouched — revocation is scoped precisely to the one `(object, principal, permission)` triple it targets, exactly as fine-grained as the ACL model's grants themselves.

## 6. Walkthrough

Trace the sequence of calls in Level 3's `main`, focusing on the state of `aclGrants` before and after `revoke`.

1. Three `grant` calls populate `aclGrants` with two entries: the key `AclKey(sharedDoc, "alice")` maps to `{"READ", "WRITE"}` (from the first two grants), and the key `AclKey(sharedDoc, "bob")` maps to `{"READ"}` (from the third grant).
2. `hasPermission(sharedDoc, "alice", "WRITE")` looks up `AclKey(sharedDoc, "alice")`, finds `{"READ", "WRITE"}`, and checks `.contains("WRITE")` — `true`; `hasPermission(sharedDoc, "bob", "READ")` similarly finds `{"READ"}` and confirms `.contains("READ")` — also `true`. Both are printed as expected before any revocation.
3. `revoke(sharedDoc, "alice", "WRITE")` runs: `aclGrants.get(new AclKey(sharedDoc, "alice"))` retrieves the *same* mutable set object, `{"READ", "WRITE"}`, and `permissions.remove("WRITE")` mutates it in place, leaving it as `{"READ"}` — critically, this is the identical `Set` object referenced by `aclGrants`'s entry for alice, so the mutation is immediately reflected in any subsequent lookup.
4. `hasPermission(sharedDoc, "alice", "WRITE")` now finds `AclKey(sharedDoc, "alice")` mapping to `{"READ"}` (post-revocation) and checks `.contains("WRITE")` — this is now `false`.
5. `hasPermission(sharedDoc, "alice", "READ")` looks up the *same* now-modified set, `{"READ"}`, and checks `.contains("READ")` — still `true`, since only `"WRITE"` was removed, not `"READ"`; `hasPermission(sharedDoc, "bob", "READ")` looks up an entirely separate key, `AclKey(sharedDoc, "bob")`, whose set `{"READ"}` was never touched by the `revoke` call at all (which only targeted alice's key) — also still `true`.

```
before revoke:  AclKey(sharedDoc,"alice") -> {READ, WRITE}     AclKey(sharedDoc,"bob") -> {READ}
revoke(sharedDoc, "alice", "WRITE"):        removes "WRITE" from alice's set ONLY
after revoke:   AclKey(sharedDoc,"alice") -> {READ}            AclKey(sharedDoc,"bob") -> {READ}  (untouched)
```

## 7. Gotchas & takeaways

> **Gotcha:** the ACL module's fine-grained, per-instance permission model carries genuine storage and query overhead proportional to the number of distinct object/principal/permission combinations an application actually needs — for applications where access can instead be derived from a simple, computable rule (ownership, role, department match), introducing the full ACL schema and API is disproportionate complexity; reserve it specifically for cases where permissions are genuinely, independently assigned per object instance and per recipient, not derivable from any simpler rule.

- Spring Security's ACL module addresses per-object, per-recipient permission grants — a fundamentally different, more granular question than the role- or ownership-based rules `@PreAuthorize` alone typically expresses.
- Grants are recorded per specific `(object instance, principal, permission)` combination, entirely independent of any role or ownership pattern, and independently addable or revocable at runtime without affecting any other combination.
- `hasPermission(...)` inside a `@PreAuthorize` expression is the typical way an ACL-backed permission check is invoked from application code, delegating to a configured `PermissionEvaluator` backed by the ACL schema.
- Reach for the ACL module only when access genuinely varies per specific object instance and per specific recipient in a way no simpler, computable rule can express — the next card covers the concrete schema (`Acl`, `Sid`, `Permission`, `AclService`) backing this model.
