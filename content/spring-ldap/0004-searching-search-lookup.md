---
card: spring-ldap
gi: 4
slug: searching-search-lookup
title: "Searching (search, lookup)"
---

## 1. What it is

`LdapTemplate` offers two distinct ways to read entries from a directory: **`search`**, which queries a subtree using a filter and can return zero, one, or many matching entries, and **`lookup`**, which fetches exactly one entry directly by its known distinguished name (DN) with no filter evaluation needed at all. They map to two different real-world questions: "find entries matching this criteria" versus "get this one specific entry I already know the address of."

## 2. Why & when

These two operations exist because they solve fundamentally different problems and the directory server can serve them very differently under the hood. A `search` has to walk (part of) the directory tree and evaluate a filter against each candidate entry — inherently more work, and its cost grows with how much of the tree it has to consider. A `lookup` goes straight to one known DN, the LDAP equivalent of a primary-key fetch — it's a direct read with no filter evaluation and no scanning.

Use **`search`** when:

- Finding entries by some attribute value you know but whose DN you don't (find the user whose `uid` is `jsmith`).
- Listing multiple entries matching a criterion (all members of a group, all users in a department).
- The DN of the target entry isn't already known.

Use **`lookup`** when:

- The exact DN is already known (perhaps stored from an earlier search, or configured directly), and you just need that one entry's current attributes.
- Performance matters and a direct fetch is available instead of an unnecessary filtered scan.

## 3. Core concept

Think of a `search` like asking a librarian "find me every book whose author is Jane Austen" — the librarian has to check candidates against your criteria, whether that means scanning a card catalog or an indexed database. A `lookup` is like walking directly to shelf B-14 because you already wrote down exactly where the book you want lives — no searching required, just a direct retrieval.

Both operations return their data through the same callback mechanism as `LdapTemplate`'s other reads:

- **`search(base, filter, mapper)`** — evaluates `filter` against every entry at or under `base` (scope-dependent), calling `mapper` for each match, returning a `List` of whatever the mapper produces.
- **`lookup(dn)`** — fetches the single entry at `dn` directly; without a mapper it returns the raw `Attributes` (or a bound object), and with a mapper (`lookup(dn, mapper)`) it returns one mapped result, throwing `NameNotFoundException` if nothing exists at that DN.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Search scans a subtree evaluating a filter against candidates; lookup goes directly to one known DN">
  <text x="150" y="25" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">search(base, filter)</text>
  <rect x="60" y="40" width="180" height="150" rx="6" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <circle cx="150" cy="70" r="16" fill="#1c2430" stroke="#79c0ff"/>
  <circle cx="100" cy="110" r="16" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="200" cy="110" r="16" fill="#1c2430" stroke="#8b949e"/>
  <circle cx="100" cy="160" r="16" fill="#1c2430" stroke="#8b949e"/>
  <circle cx="200" cy="160" r="16" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="150" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">green = matches filter</text>

  <text x="480" y="25" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">lookup(dn)</text>
  <rect x="400" y="40" width="180" height="150" rx="6" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <circle cx="490" cy="70" r="16" fill="#1c2430" stroke="#8b949e"/>
  <line x1="490" y1="86" x2="490" y2="130" stroke="#79c0ff" stroke-width="2" marker-end="url(#d1)"/>
  <circle cx="490" cy="150" r="16" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="490" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">direct fetch, no scan</text>

  <defs>
    <marker id="d1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`search` evaluates a filter against candidates across a subtree; `lookup` goes straight to one already-known entry.

## 5. Runnable example

The scenario: retrieve a user's department, starting with a `search` by username, then adding a `lookup` fast-path once the DN is already known, and finally combining both in a caching layer that avoids repeated searches.

### Level 1 — Basic

```java
// FindDepartment.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.AttributesMapper;

import javax.naming.directory.Attributes;
import java.util.List;

public class FindDepartment {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        List<String> departments = template.search(
            "ou=people",
            "(uid=jsmith)",
            (AttributesMapper<String>) attrs ->
                (String) ((Attributes) attrs).get("departmentNumber").get()
        );

        System.out.println("Department: " + departments);
    }
}
```

**How to run:** run against a seeded directory with `uid=jsmith` under `ou=people,dc=example,dc=com` carrying a `departmentNumber` attribute. Expected output: `Department: [4120]`.

### Level 2 — Intermediate

If the DN is already known from an earlier search or a stored reference, a `search` re-scans the subtree unnecessarily — `lookup` fetches the exact entry directly.

```java
// LookupDepartment.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;

import javax.naming.directory.Attributes;
import javax.naming.Name;
import org.springframework.ldap.support.LdapNameBuilder;

public class LookupDepartment {
    private final LdapTemplate template;

    public LookupDepartment(LdapTemplate template) {
        this.template = template;
    }

    public String departmentByDn(String uid) {
        Name dn = LdapNameBuilder.newInstance("ou=people")
            .add("uid", uid)
            .build();

        // Direct fetch by DN — no filter evaluation, no subtree scan.
        return template.lookup(dn, (AttributesMapper<String>) attrs ->
            (String) ((Attributes) attrs).get("departmentNumber").get());
    }
}
```

**How to run:** call `departmentByDn("jsmith")`. Expected output: `4120`, the same result as Level 1's search, but fetched as a direct read against the known DN `uid=jsmith,ou=people,dc=example,dc=com` rather than a filtered scan.

### Level 3 — Advanced

Real applications look up the same user's department repeatedly across many requests. Combining a cached DN (found once via `search`) with subsequent `lookup` calls, and handling the case where the entry has since been deleted, avoids repeated scanning while staying correct.

```java
// CachedDepartmentService.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.NameNotFoundException;

import javax.naming.directory.Attributes;
import javax.naming.Name;
import org.springframework.ldap.support.LdapNameBuilder;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Optional;

public class CachedDepartmentService {
    private final LdapTemplate template;
    private final Map<String, Name> dnCache = new ConcurrentHashMap<>();

    public CachedDepartmentService(LdapTemplate template) {
        this.template = template;
    }

    public Optional<String> departmentFor(String uid) {
        Name dn = dnCache.computeIfAbsent(uid, u ->
            LdapNameBuilder.newInstance("ou=people").add("uid", u).build());

        try {
            String dept = template.lookup(dn, (AttributesMapper<String>) attrs ->
                (String) ((Attributes) attrs).get("departmentNumber").get());
            return Optional.ofNullable(dept);
        } catch (NameNotFoundException e) {
            // Cached DN no longer exists (entry deleted, or uid never really existed) — evict and report absent.
            dnCache.remove(uid);
            return Optional.empty();
        }
    }
}
```

**How to run:** call `departmentFor("jsmith")` twice — both calls use `lookup` against the cached DN rather than re-running a filtered search. Then delete the `jsmith` entry from the directory and call `departmentFor("jsmith")` again: expect `NameNotFoundException` to be caught internally, the stale DN evicted from `dnCache`, and `Optional.empty()` returned instead of an uncaught exception propagating to the caller.

## 6. Walkthrough

Tracing `departmentFor("jsmith")` on a cache miss followed by a cache hit, in execution order:

1. First call: `dnCache.computeIfAbsent("jsmith", ...)` finds no cached entry, so it builds `uid=jsmith,ou=people` via `LdapNameBuilder` (card 0009) and stores it in the cache.
2. `template.lookup(dn, mapper)` sends a direct LDAP lookup for that exact DN — the directory server resolves it in effectively one step, no subtree evaluation needed.
3. The server returns the entry's attributes; the `AttributesMapper` extracts `departmentNumber`, which is wrapped in an `Optional` and returned.
4. Second call, same `uid`: `computeIfAbsent` finds the DN already cached, skipping DN construction entirely, and goes straight to `template.lookup` again — no `search` was ever needed after the first population.
5. If the entry has since been deleted and a `lookup` is attempted against its now-stale cached DN, the directory server reports no such entry, and `LdapTemplate` translates the underlying JNDI exception into `org.springframework.ldap.NameNotFoundException`.
6. The `catch` block removes the stale DN from `dnCache` (so a future call rebuilds it fresh — perhaps because a new entry now legitimately exists under the same `uid`) and returns `Optional.empty()`.

```
departmentFor("jsmith")
  cache miss -> build DN -> lookup(dn) -> attrs -> departmentNumber -> cache DN, return value
  cache hit  -> lookup(dn) directly -> attrs -> departmentNumber -> return value
  entry deleted -> lookup(dn) -> NameNotFoundException -> evict cached DN -> return empty
```

## 7. Gotchas & takeaways

> A cached DN can go stale if the underlying entry is renamed, moved, or deleted — always be prepared to catch `NameNotFoundException` on a `lookup` against a previously-cached DN, and treat it as a signal to evict and, if appropriate, re-resolve rather than as an unexpected failure.

- Use `search` when the DN isn't already known; use `lookup` when it is — conflating the two by always searching is a common, avoidable source of unnecessary directory load.
- `lookup` without a mapper returns raw `Attributes`; providing a mapper (as shown here) returns the mapped domain value directly, keeping calling code free of low-level `Attributes` handling.
- Caching resolved DNs (Level 3) is a reasonable optimization for frequently-accessed entries, but the cache must be invalidated on `NameNotFoundException`, since directory entries can move or disappear independently of the application's cache.
- `search` results come back as a `List`, even when exactly one match is expected — calling code should not assume a single-element list without checking, since a broad filter can unexpectedly match more than one entry.
- Prefer the most specific operation available for the situation: a direct `lookup` is both cheaper and clearer in intent than a `search` scoped so narrowly it can only ever return one result.
