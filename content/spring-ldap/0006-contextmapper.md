---
card: spring-ldap
gi: 6
slug: contextmapper
title: "ContextMapper"
---

## 1. What it is

`ContextMapper<T>` is a sibling callback to `AttributesMapper` (card 0005), but instead of receiving just the entry's `Attributes`, it receives the full `DirContextOperations` (or raw `Object` context) representing the entry — which includes both its attributes **and** its distinguished name. It's used with `LdapTemplate` the same way: called once per matching entry during a `search` or `lookup`, converting each raw directory context into a domain object of type `T`.

## 2. Why & when

`AttributesMapper` is enough when a domain object can be built purely from attribute values. But sometimes the DN itself carries meaningful information the domain object needs — an entry's exact position in the tree, a component of the DN used as an identifier, or the need to later modify the very entry that was just read (which requires its DN). `ContextMapper` exists for exactly this: it hands the mapper everything about the entry, DN included, not just its attribute bag.

Reach for `ContextMapper` when:

- The mapped domain object needs to know its own DN — for instance, storing it so the object can later be passed back to `LdapTemplate.modifyAttributes()` or `unbind()` without re-searching for it.
- Working with `DirContextAdapter`, Spring LDAP's convenience implementation of `DirContextOperations`, which offers friendlier attribute-access methods (`getStringAttribute`, `getStringAttributes`) than raw `Attributes`.
- Building or modifying entries where round-tripping the same context object (read it, mutate it, write it back) is more natural than manually reconstructing attributes from scratch.

If the DN is never needed by the mapped object, `AttributesMapper` is simpler and communicates that fact more directly to future readers of the code.

## 3. Core concept

If `AttributesMapper` is a clerk who only ever sees the filled-out form's contents, `ContextMapper` is a clerk who also sees the folder the form came in — the label on the folder (the DN) plus the form inside it (the attributes). For most simple read scenarios that extra folder label doesn't matter. But the moment you need to know exactly where in the filing cabinet this form lives — so you can, say, go back and update it later — you need the clerk who saw the whole folder, not just its contents.

```java
ContextMapper<User> userMapper = ctx -> {
    DirContextOperations context = (DirContextOperations) ctx;
    User u = new User();
    u.setDn(context.getDn().toString());          // only ContextMapper exposes this
    u.setUid(context.getStringAttribute("uid"));
    u.setEmail(context.getStringAttribute("mail"));
    return u;
};
```

`DirContextOperations` (typically backed by `DirContextAdapter`) offers typed convenience accessors like `getStringAttribute` and `getStringAttributes` (for multi-valued attributes), removing much of the manual casting `AttributesMapper` code needs.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ContextMapper receives the full context, DN and attributes together, unlike AttributesMapper which only sees attributes">
  <rect x="20" y="30" width="180" height="140" rx="8" fill="none" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="110" y="20" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DirContextOperations</text>
  <rect x="40" y="50" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="74" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DN</text>
  <rect x="40" y="105" width="140" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="133" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Attributes</text>

  <rect x="280" y="70" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ContextMapper</text>

  <rect x="490" y="70" width="130" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="555" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">T (with DN)</text>

  <line x1="200" y1="100" x2="275" y2="100" stroke="#3fb950" stroke-width="2" marker-end="url(#f1)"/>
  <line x1="430" y1="100" x2="485" y2="100" stroke="#3fb950" stroke-width="2" marker-end="url(#f2)"/>

  <defs>
    <marker id="f1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="f2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Unlike `AttributesMapper`, `ContextMapper` receives both the DN and the attributes, so the mapped object can retain the entry's exact location.

## 5. Runnable example

The scenario: read a user entry and keep its DN so the same object can be used later to modify it — starting with a bare `ContextMapper`, then a round-trip read-modify-write, and finally a safe version that handles a concurrently-deleted entry.

### Level 1 — Basic

```java
// UserWithDn.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.ContextMapper;
import org.springframework.ldap.core.DirContextOperations;

import java.util.List;

public class UserWithDn {
    record User(String dn, String uid, String email) {}

    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        ContextMapper<User> mapper = ctx -> {
            DirContextOperations c = (DirContextOperations) ctx;
            return new User(c.getDn().toString(), c.getStringAttribute("uid"), c.getStringAttribute("mail"));
        };

        List<User> users = template.search("ou=people", "(uid=jsmith)", mapper);
        users.forEach(System.out::println);
    }
}
```

**How to run:** run against a seeded directory. Expected output: `User[dn=uid=jsmith,ou=people, uid=jsmith, email=jsmith@example.com]` — note the DN is present, something `AttributesMapper` never provides.

### Level 2 — Intermediate

Having the DN lets the same entry be re-fetched as a mutable `DirContextOperations` and updated in place — a common read-modify-write pattern.

```java
// UpdateDepartment.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.DirContextOperations;

public class UpdateDepartment {
    private final LdapTemplate template;

    public UpdateDepartment(LdapTemplate template) {
        this.template = template;
    }

    public void moveToDepartment(String dn, String newDepartment) {
        // lookupContext fetches the entry as a mutable DirContextOperations, DN included.
        DirContextOperations context = template.lookupContext(dn);
        context.setAttributeValue("departmentNumber", newDepartment);
        template.modifyAttributes(context); // writes only the changed attribute back
    }
}
```

**How to run:** call `moveToDepartment("uid=jsmith,ou=people", "5200")`, then look up `jsmith`'s `departmentNumber` again. Expected result: it now reads `5200` — the read-modify-write round trip used the DN obtained via `ContextMapper`-style access (`lookupContext` is the equivalent single-entry form) to know exactly which entry to write back to.

### Level 3 — Advanced

Between the initial read and the write-back, another process or administrator could have deleted the entry — a real race condition in any system where multiple actors can modify the same directory. Production code needs to handle that gracefully rather than throwing an unhandled exception mid-operation.

```java
// SafeDepartmentUpdate.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.DirContextOperations;
import org.springframework.ldap.NameNotFoundException;

public class SafeDepartmentUpdate {
    private final LdapTemplate template;

    public SafeDepartmentUpdate(LdapTemplate template) {
        this.template = template;
    }

    public boolean moveToDepartment(String dn, String newDepartment) {
        try {
            DirContextOperations context = template.lookupContext(dn);
            context.setAttributeValue("departmentNumber", newDepartment);
            template.modifyAttributes(context);
            return true;
        } catch (NameNotFoundException e) {
            // Entry was deleted between some earlier read and this write attempt.
            System.err.println("Entry no longer exists, skipping update: " + dn);
            return false;
        }
    }
}
```

**How to run:** delete the `jsmith` entry from the directory, then call `moveToDepartment("uid=jsmith,ou=people", "5200")`. Expected result: `lookupContext` throws `NameNotFoundException` because the entry is gone, the `catch` block logs a clear message and returns `false` instead of an unhandled exception propagating up, and the caller can decide how to react (retry, alert, ignore) based on that boolean.

## 6. Walkthrough

Tracing `moveToDepartment` on an entry that still exists, in execution order:

1. `template.lookupContext(dn)` performs a direct lookup (card 0004) at the given DN, returning a `DirContextOperations` — this object holds both the DN and the entry's current attributes, and tracks any changes made to it.
2. `context.setAttributeValue("departmentNumber", newDepartment)` doesn't write to the directory yet — it records the change locally on the `DirContextOperations` object, marking `departmentNumber` as modified.
3. `template.modifyAttributes(context)` inspects what actually changed on the context object and sends only that delta (a `ModificationItem` for `departmentNumber`, card 0008) to the directory server — not a full rewrite of the entry.
4. The server applies the modification to the entry at that DN and confirms success; `modifyAttributes` returns normally.
5. If instead the entry no longer exists (Level 3's scenario), step 1's `lookupContext` itself fails immediately — the DN can't be resolved to any entry — throwing `NameNotFoundException` before any modification is even attempted, which the caller catches and turns into a `false` return value.

```
moveToDepartment(dn, "5200")
  -> lookupContext(dn)              [fetch, DN + attrs]
       exists?  -> DirContextOperations, tracks changes
       missing? -> NameNotFoundException -> caught -> return false
  -> setAttributeValue("departmentNumber","5200")   [local change, tracked]
  -> modifyAttributes(context)      [sends only the diff]
  -> return true
```

## 7. Gotchas & takeaways

> `modifyAttributes(context)` only sends attributes that were actually changed on the `DirContextOperations` object since it was fetched — it does not blindly overwrite the entire entry. This is a meaningful safety property: two different processes reading and modifying *different* attributes on the same entry, then calling `modifyAttributes`, won't clobber each other's unrelated changes, as long as neither reads a stale copy of the specific attribute the other is changing.

- Use `ContextMapper` (or the single-entry `lookupContext`) whenever the entry's DN is needed for anything beyond the immediate read — most commonly, a later modify or delete.
- `DirContextOperations` (usually `DirContextAdapter` under the hood) provides typed convenience accessors (`getStringAttribute`, `getStringAttributes`) that are more ergonomic than raw `Attributes` casting.
- The read-modify-write pattern (`lookupContext` → mutate → `modifyAttributes`) is the idiomatic way to update an existing entry in Spring LDAP, rather than manually building `ModificationItem` arrays by hand for simple cases.
- Always handle `NameNotFoundException` around a read-modify-write sequence in any system where entries can be deleted or renamed concurrently by another process or administrator.
- Prefer `AttributesMapper` when the DN genuinely isn't needed — reaching for `ContextMapper` by default, even when the DN is never used, adds a layer of indirection (`DirContextOperations` casting) without any corresponding benefit.
