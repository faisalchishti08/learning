---
card: spring-security
gi: 74
slug: acl-model-acl-sid-permission-aclservice
title: "ACL model (Acl, Sid, Permission, AclService)"
---

## 1. What it is

The ACL module's concrete model is `Sid` (Security Identity — either a `PrincipalSid` for a specific user, or a `GrantedAuthoritySid` for a role, letting a grant apply to an entire role at once), `Permission` (a bitmask-backed value, with `BasePermission.READ`/`WRITE`/`CREATE`/`DELETE`/`ADMINISTRATION` as the built-in constants), `Acl`/`MutableAcl` (the ordered list of access control entries for one specific object, each entry pairing a `Sid` with a `Permission` and a granted/denied flag), and `AclService`/`MutableAclService` (the interface for reading and persisting `Acl`s against the underlying database schema, typically PostgreSQL/MySQL tables Spring Security provides a standard DDL script for).

```java
ObjectIdentity objectIdentity = new ObjectIdentityImpl(Document.class, documentId);
MutableAcl acl = mutableAclService.createAcl(objectIdentity);

acl.insertAce(acl.getEntries().size(), BasePermission.READ, new PrincipalSid("alice"), true);
acl.insertAce(acl.getEntries().size(), BasePermission.WRITE, new GrantedAuthoritySid("ROLE_EDITOR"), true);

mutableAclService.updateAcl(acl); // PERSISTS the accumulated entries to the underlying ACL tables
```

## 2. Why & when

Each piece of this model addresses a distinct requirement the previous card's simplified example glossed over: `Sid` needs to represent *either* a specific individual *or* an entire role uniformly, since real grants are commonly made to both ("alice specifically" and "anyone with `ROLE_EDITOR`"); `Permission`'s bitmask representation allows efficient combination and storage of multiple simultaneous permission bits per entry; `Acl`'s ordered entry list means entry *order* matters — the first matching entry for a given `Sid` typically wins, allowing an explicit `DENY` entry to override an otherwise-applicable `GRANT` from a broader role-based entry positioned later; and `AclService` abstracts the actual persistence mechanism (typically the standard relational schema, though pluggable) behind a clean read/write interface.

Reach for understanding the full model when:

- Granting permission to an entire role at once (`GrantedAuthoritySid`) rather than enumerating every individual member of that role separately — a common, more maintainable pattern than granting to each `PrincipalSid` individually.
- Combining multiple permission bits efficiently — `Permission`'s bitmask design lets a single stored value represent several simultaneously-granted permissions without needing a separate row per permission type.
- Understanding entry order's significance — an explicit denial entry positioned *before* a broader role-based grant entry for the same `Sid` (or an overlapping one) can override it, making entry ordering a meaningful, deliberate design decision, not an incidental detail.
- `AclService` (read-only) versus `MutableAclService` (adds create/update/delete) — application code performing only permission *checks* needs just the former; code actually managing grants (an admin UI for sharing settings) needs the latter.

## 3. Core concept

```
 Sid (Security Identity):
   PrincipalSid("alice")           -- a SPECIFIC individual
   GrantedAuthoritySid("ROLE_EDITOR") -- an ENTIRE role, granted ONCE, applying to every member

 Permission: a BITMASK value
   BasePermission.READ = 1, WRITE = 2, CREATE = 4, DELETE = 8, ADMINISTRATION = 16
   (combining bits lets ONE stored value represent MULTIPLE simultaneously-granted permissions)

 Acl (for ONE specific object instance): an ORDERED list of AccessControlEntry, each pairing:
   (Sid, Permission, granted-or-denied boolean)
   ENTRY ORDER MATTERS: the FIRST entry matching a given Sid+Permission combination typically decides the outcome

 AclService.readAclById(objectIdentity)       -- READ an object's Acl
 MutableAclService.updateAcl(mutableAcl)      -- PERSIST changes back to the underlying schema
```

Four pieces, each solving one specific representational problem the simplified previous card's model glossed over.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An Acl for one document holds an ordered list of access control entries the first entry denies WRITE to a specific principal the second entry grants WRITE to an entire role via a GrantedAuthoritySid because the deny entry is checked first for that principal it overrides the broader role based grant that would otherwise apply">
  <rect x="15" y="15" width="600" height="150" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="32" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Acl for Document #42 -- ORDERED entries</text>

  <rect x="40" y="50" width="270" height="46" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="175" y="70" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">entry 1: PrincipalSid("bob"),</text>
  <text x="175" y="83" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">WRITE, DENIED</text>

  <rect x="330" y="50" width="270" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="465" y="70" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">entry 2: GrantedAuthoritySid</text>
  <text x="465" y="83" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">("ROLE_EDITOR"), WRITE, GRANTED</text>

  <rect x="180" y="115" width="280" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="320" y="140" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">bob (a ROLE_EDITOR member): DENIED, entry 1 wins</text>

  <defs><marker id="a74" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="175" y1="96" x2="270" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a74)"/>
  <line x1="465" y1="96" x2="370" y2="115" stroke="#8b949e" stroke-width="1" marker-end="url(#a74)"/>
</svg>

Two entries could both apply to bob — but the first one checked, positioned earlier, decides the outcome.

## 5. Runnable example

The scenario: implement `Sid`, `Permission`, and ordered `Acl` entries faithfully, then demonstrate a specific-principal denial overriding a broader role-based grant purely through entry ordering, then combine multiple permission bits in one entry via a bitmask.

### Level 1 — Basic

`Sid` as either a principal or a role, and a minimal ordered ACL evaluation.

```java
import java.util.*;

public class AclModelLevel1 {
    interface Sid {}
    record PrincipalSid(String username) implements Sid {}
    record GrantedAuthoritySid(String role) implements Sid {}

    record AccessControlEntry(Sid sid, String permission, boolean granted) {}

    static boolean sidApplies(Sid entrySid, String username, Set<String> userRoles) {
        if (entrySid instanceof PrincipalSid p) return p.username().equals(username);
        if (entrySid instanceof GrantedAuthoritySid g) return userRoles.contains(g.role());
        return false;
    }

    // evaluates an ORDERED list of entries -- the FIRST one that APPLIES to this user decides the outcome
    static boolean checkAcl(List<AccessControlEntry> acl, String username, Set<String> userRoles, String permission) {
        for (AccessControlEntry entry : acl) {
            if (entry.permission().equals(permission) && sidApplies(entry.sid(), username, userRoles)) {
                return entry.granted(); // FIRST applicable entry wins -- stop here
            }
        }
        return false; // no applicable entry at all -- deny by default
    }

    public static void main(String[] args) {
        List<AccessControlEntry> acl = List.of(
                new AccessControlEntry(new PrincipalSid("alice"), "READ", true)
        );

        System.out.println("alice READ: " + checkAcl(acl, "alice", Set.of(), "READ"));
        System.out.println("bob READ (no entry at all): " + checkAcl(acl, "bob", Set.of(), "READ"));
    }
}
```

How to run: `java AclModelLevel1.java`

`checkAcl` iterates the entry list looking for the first one whose `Sid` applies to the caller and whose permission matches — alice's explicit `PrincipalSid` entry grants her `READ`, while bob, having no applicable entry at all, is denied by the default fall-through.

### Level 2 — Intermediate

Demonstrate a specific-principal denial entry overriding a broader role-based grant, purely through entry ordering.

```java
import java.util.*;

public class AclModelLevel2 {
    interface Sid {}
    record PrincipalSid(String username) implements Sid {}
    record GrantedAuthoritySid(String role) implements Sid {}
    record AccessControlEntry(Sid sid, String permission, boolean granted) {}

    static boolean sidApplies(Sid entrySid, String username, Set<String> userRoles) {
        if (entrySid instanceof PrincipalSid p) return p.username().equals(username);
        if (entrySid instanceof GrantedAuthoritySid g) return userRoles.contains(g.role());
        return false;
    }

    static boolean checkAcl(List<AccessControlEntry> acl, String username, Set<String> userRoles, String permission) {
        for (AccessControlEntry entry : acl) {
            if (entry.permission().equals(permission) && sidApplies(entry.sid(), username, userRoles)) return entry.granted();
        }
        return false;
    }

    public static void main(String[] args) {
        // entry 1 (checked FIRST): bob is SPECIFICALLY denied WRITE
        // entry 2 (checked SECOND): anyone with ROLE_EDITOR is GRANTED WRITE -- bob happens to BE a ROLE_EDITOR
        List<AccessControlEntry> aclDenyFirst = List.of(
                new AccessControlEntry(new PrincipalSid("bob"), "WRITE", false),
                new AccessControlEntry(new GrantedAuthoritySid("ROLE_EDITOR"), "WRITE", true)
        );

        // the SAME two entries, but REORDERED -- the role grant is checked FIRST this time
        List<AccessControlEntry> aclGrantFirst = List.of(
                new AccessControlEntry(new GrantedAuthoritySid("ROLE_EDITOR"), "WRITE", true),
                new AccessControlEntry(new PrincipalSid("bob"), "WRITE", false)
        );

        Set<String> bobRoles = Set.of("ROLE_EDITOR");

        System.out.println("deny-first order, bob WRITE: " + checkAcl(aclDenyFirst, "bob", bobRoles, "WRITE"));
        System.out.println("grant-first order, bob WRITE: " + checkAcl(aclGrantFirst, "bob", bobRoles, "WRITE"));
    }
}
```

How to run: `java AclModelLevel2.java`

With the deny entry listed first, bob is correctly denied despite being a `ROLE_EDITOR` member, since his specific denial entry is checked before the broader role grant; with the *identical two entries reordered*, the role-based grant is checked first and wins instead — the exact same underlying grants produce opposite outcomes purely based on entry order, exactly mirroring the real ACL model's first-match-wins evaluation.

### Level 3 — Advanced

Add bitmask-based `Permission` combination, letting one entry represent multiple simultaneously-granted permissions, and confirm bitwise checks work correctly.

```java
import java.util.*;

public class AclModelLevel3 {
    interface Sid {}
    record PrincipalSid(String username) implements Sid {}
    record GrantedAuthoritySid(String role) implements Sid {}

    // models BasePermission's bitmask constants
    static final int READ = 1;
    static final int WRITE = 2;
    static final int CREATE = 4;
    static final int DELETE = 8;
    static final int ADMINISTRATION = 16;

    record AccessControlEntry(Sid sid, int permissionMask, boolean granted) {}

    static boolean sidApplies(Sid entrySid, String username, Set<String> userRoles) {
        if (entrySid instanceof PrincipalSid p) return p.username().equals(username);
        if (entrySid instanceof GrantedAuthoritySid g) return userRoles.contains(g.role());
        return false;
    }

    // checks whether ONE SPECIFIC permission bit is set within the entry's COMBINED mask
    static boolean maskIncludes(int entryMask, int specificPermission) {
        return (entryMask & specificPermission) == specificPermission;
    }

    static boolean checkAcl(List<AccessControlEntry> acl, String username, Set<String> userRoles, int permission) {
        for (AccessControlEntry entry : acl) {
            if (maskIncludes(entry.permissionMask(), permission) && sidApplies(entry.sid(), username, userRoles)) {
                return entry.granted();
            }
        }
        return false;
    }

    public static void main(String[] args) {
        // ONE entry grants alice BOTH READ and WRITE simultaneously, via a COMBINED bitmask
        int readAndWrite = READ | WRITE; // bitwise OR: combines bit 1 and bit 2 into the value 3
        List<AccessControlEntry> acl = List.of(
                new AccessControlEntry(new PrincipalSid("alice"), readAndWrite, true)
        );

        System.out.println("alice READ (bit included in combined mask): " + checkAcl(acl, "alice", Set.of(), READ));
        System.out.println("alice WRITE (bit included in combined mask): " + checkAcl(acl, "alice", Set.of(), WRITE));
        System.out.println("alice DELETE (bit NOT included): " + checkAcl(acl, "alice", Set.of(), DELETE));
    }
}
```

How to run: `java AclModelLevel3.java`

`readAndWrite` combines `READ` (bit value `1`) and `WRITE` (bit value `2`) into a single stored value, `3`, via bitwise OR; `maskIncludes` then checks whether a specific permission's bit is present within that combined value using bitwise AND — alice's single entry correctly grants both `READ` and `WRITE` checks, since both bits are present in her combined mask, while `DELETE` (bit value `8`, not included in `3`) correctly fails.

## 6. Walkthrough

Trace `checkAcl(acl, "alice", Set.of(), WRITE)` from Level 3, where `acl`'s single entry has `permissionMask = 3` (i.e., `READ | WRITE`).

1. The `for` loop checks the single entry in `acl`: `maskIncludes(3, WRITE)` is called, where `WRITE` is `2`.
2. Inside `maskIncludes`, `entryMask & specificPermission` computes `3 & 2` — in binary, `3` is `011` and `2` is `010`; the bitwise AND of these is `010`, which is `2` in decimal.
3. `(entryMask & specificPermission) == specificPermission` checks `2 == 2`, which is `true` — so `maskIncludes` returns `true`, confirming the `WRITE` bit is indeed present within the combined mask `3`.
4. Back in `checkAcl`, since `maskIncludes` returned `true`, the method next checks `sidApplies(entry.sid(), "alice", Set.of())` — the entry's `sid` is `PrincipalSid("alice")`, and `p.username().equals("alice")` is `true`, so `sidApplies` also returns `true`.
5. Both conditions of the `if` statement are satisfied, so `checkAcl` returns `entry.granted()`, which is `true` — alice's `WRITE` check succeeds, correctly derived from the single combined bitmask entry without needing any separate, dedicated `WRITE`-only entry to exist at all.

```
entry.permissionMask = 3 (binary 011 = READ|WRITE combined)
checking WRITE (binary 010, decimal 2):
  3 & 2 = 010 (decimal 2)
  2 == 2 -> true -> maskIncludes returns true
  sidApplies("alice") -> true
  -> checkAcl returns entry.granted() = true
```

## 7. Gotchas & takeaways

> **Gotcha:** entry order within an `Acl` is meaningful and must be managed deliberately — `insertAce`'s position parameter determines exactly where a new entry is placed in the evaluated sequence, and inserting a broad role-based grant *before* a more specific principal-level denial (rather than after it) silently allows the broader grant to win instead of the intended, more specific denial, exactly as Level 2's reordered example demonstrates.

- `Sid` uniformly represents either a specific principal or an entire granted authority (role), letting a single ACL entry apply to one individual or to every member of a role at once.
- `Permission`'s bitmask design allows one stored entry to represent multiple simultaneously-granted permissions efficiently, checked via bitwise AND against the specific permission being queried.
- `Acl` entries are evaluated in order, with the first entry applicable to a given `Sid` and permission typically determining the outcome — entry order is a deliberate, meaningful design decision, not an incidental implementation detail, and is exactly how a specific-principal denial can override a broader role-based grant.
- `AclService`/`MutableAclService` abstract the underlying persistence (typically Spring Security's standard relational ACL schema) behind a clean read (`readAclById`) and write (`createAcl`/`updateAcl`) interface, letting application code manage grants without directly manipulating the underlying tables.
