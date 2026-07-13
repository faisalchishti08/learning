---
card: spring-ldap
gi: 15
slug: odm-with-ldaptemplate-findall-find
title: "ODM with LdapTemplate.findAll / find"
---

## 1. What it is

`LdapTemplate` offers a family of ODM-aware read methods that operate directly on `@Entry`-annotated classes (card 0014): `findByDn(dn, Class)` for a single known-DN fetch, `findOne(query, Class)` for a query expected to match exactly one entry, and `find(query, Class)` / `findAll(base, filter, Class)` for queries returning multiple mapped objects — all without a manually supplied `AttributesMapper` or `ContextMapper`, since the mapping is derived entirely from the class's own annotations.

## 2. Why & when

Once an entry type is annotated for ODM (card 0014), repeating a hand-written mapper at every call site that reads it would be redundant — the class already declares exactly how to map itself. `LdapTemplate`'s ODM-aware `find*` methods exist so that any search or lookup against an ODM-annotated type can skip the mapper argument entirely, inferring it from the target class, while still supporting the same `LdapQuery`-based filtering, scoping, and attribute selection covered in cards 0010–0011.

Use these methods when:

- Reading entries of a type already annotated with `@Entry` — reach for `findByDn` for a known DN (mirroring card 0004's `lookup`), `findOne` when a query is expected to match exactly one entry, and `find`/`findAll` for queries that may match several.
- Consistency matters across a codebase — once a type is modeled with ODM, all its reads and writes should go through the ODM-aware API rather than mixing in ad hoc `AttributesMapper` calls for the same type.

## 3. Core concept

Think of the ODM-aware `find*` methods as ordering from a restaurant using a numbered menu instead of describing the dish from scratch every time — because the `Person` "dish" (card 0014's `@Entry` class) is already fully specified on the menu, you just say "table 12, Person" (`findByDn`) or "one Person matching these criteria" (`findOne`) or "every Person matching these criteria" (`find`), and the kitchen (Spring LDAP) already knows exactly how to assemble it, without you re-explaining the recipe (a mapper) each time.

```java
// single known DN
Person p = ldapTemplate.findByDn(dn, Person.class);

// exactly one expected match
Person p2 = ldapTemplate.findOne(query().where("uid").is("jsmith"), Person.class);

// zero or more matches
List<Person> people = ldapTemplate.find(
    query().base("ou=people").where("objectClass").is("inetOrgPerson"),
    Person.class);
```

`findOne` throws `IncorrectResultSizeDataAccessException` if the query matches zero or more than one entry — it's a declaration of intent ("I expect exactly one"), not merely a convenience for taking the first result of a list.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="findByDn, findOne, and find/findAll each read ODM-annotated entries without a manually supplied mapper">
  <rect x="20" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">findByDn(dn, Class)</text>

  <rect x="240" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">findOne(query, Class)</text>

  <rect x="460" y="30" width="180" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">find(query, Class)</text>

  <line x1="110" y1="80" x2="330" y2="130" stroke="#8b949e" stroke-width="1"/>
  <line x1="330" y1="80" x2="330" y2="130" stroke="#8b949e" stroke-width="1"/>
  <line x1="550" y1="80" x2="330" y2="130" stroke="#8b949e" stroke-width="1"/>
  <rect x="240" y="130" width="180" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="330" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">annotations on the @Entry class</text>
</svg>

All three read forms derive their mapping purely from the target class's own ODM annotations — no separate mapper is ever passed in.

## 5. Runnable example

The scenario: reading `Person` entries with the ODM-aware API, starting with `findByDn` and `findOne`, then a broad `find`, and finally combining `findOne`'s strict-match guarantee with graceful handling of an unexpected duplicate.

### Level 1 — Basic

```java
// OdmFindByDn.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.support.LdapNameBuilder;

public class OdmFindByDn {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        var dn = LdapNameBuilder.newInstance("ou=people").add("uid", "jsmith").build();
        Person p = template.findByDn(dn, Person.class);

        System.out.println("Found: " + p.getCommonName() + " <" + p.getEmail() + ">");
    }
}
```

**How to run:** run against a directory with `uid=jsmith` already provisioned via card 0014's `Person` class. Expected output: `Found: Jane Smith <jsmith@example.com>` — no mapper supplied anywhere, the mapping is entirely inferred from `Person`'s own annotations.

### Level 2 — Intermediate

`findOne` expresses "exactly one match expected" directly, and `find` handles the general case of zero-or-more matches, both built from the same `LdapQueryBuilder` API used for non-ODM searches (cards 0010–0011).

```java
// OdmFindOneAndFindAll.java
import org.springframework.ldap.core.LdapTemplate;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;

public class OdmFindOneAndFindAll {
    private final LdapTemplate template;

    public OdmFindOneAndFindAll(LdapTemplate template) {
        this.template = template;
    }

    public Person findByUid(String uid) {
        return template.findOne(
            query().base("ou=people").where("uid").is(uid),
            Person.class);
    }

    public List<Person> findAllInDepartment(String departmentNumber) {
        return template.find(
            query().base("ou=people").where("departmentNumber").is(departmentNumber),
            Person.class);
    }
}
```

**How to run:** call `findByUid("jsmith")` — expect a single `Person` returned directly (not wrapped in a list). Call `findAllInDepartment("4120")` on a department with three matching people: expect a `List<Person>` of size 3, each fully populated with no manual mapper involved.

### Level 3 — Advanced

`findOne` is strict by design — if a `uid` that's supposed to be unique ever has a duplicate (a data-quality bug, or two entries created by a race condition, card 0007), it throws `IncorrectResultSizeDataAccessException` rather than silently picking one. Production code calling `findOne` needs to treat that as a real, actionable signal rather than crashing uninformatively.

```java
// SafeFindOneService.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.dao.IncorrectResultSizeDataAccessException;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.Optional;

public class SafeFindOneService {
    private final LdapTemplate template;

    public SafeFindOneService(LdapTemplate template) {
        this.template = template;
    }

    public Optional<Person> findByUidSafely(String uid) {
        try {
            Person p = template.findOne(
                query().base("ou=people").where("uid").is(uid),
                Person.class);
            return Optional.ofNullable(p);
        } catch (IncorrectResultSizeDataAccessException e) {
            // Either zero matches or, more concerning, more than one entry sharing a uid meant to be unique.
            System.err.println("Data integrity issue: uid=" + uid + " matched an unexpected number of entries — "
                + e.getMessage());
            return Optional.empty();
        }
    }
}
```

**How to run:** call `findByUidSafely("jsmith")` on a healthy directory — expect the matching `Person` wrapped in `Optional`. Then, in a test directory, deliberately create two entries both with `uid=jsmith` (bypassing normal uniqueness safeguards, to simulate a data-quality bug) and call `findByUidSafely("jsmith")` again: expect `IncorrectResultSizeDataAccessException` to be caught, a clear diagnostic logged naming the exact `uid` and the fact that the match count was unexpected, and `Optional.empty()` returned rather than the method either crashing or silently returning an arbitrary one of the two conflicting entries.

## 6. Walkthrough

Tracing `findByUidSafely("jsmith")` against a directory with a duplicate `uid=jsmith`, in execution order:

1. `template.findOne(query, Person.class)` builds the equivalent of a `search` (card 0004) scoped to `ou=people` with filter `(uid=jsmith)`.
2. The directory server returns two matching entries, since the data-quality bug has created a duplicate.
3. `findOne`'s internal contract is to require exactly one match; on finding two, it throws `IncorrectResultSizeDataAccessException` rather than silently returning either the first or an arbitrary match — this is a deliberate strictness, distinct from `find`'s general "return however many match" behavior.
4. The surrounding `catch` block in `findByUidSafely` catches this specific exception, logs a diagnostic message identifying the exact `uid` involved and noting the unexpected match count, and returns `Optional.empty()`.
5. The caller receives `Optional.empty()` — behaviorally indistinguishable, from the caller's point of view, from a genuine "no such user," but the logged diagnostic is what actually surfaces the real underlying problem (a uniqueness violation) to whoever is watching application logs, so it can be investigated and fixed at the data level.

```
findByUidSafely("jsmith"), duplicate uid exists
  findOne(query, Person.class)
     -> search matches 2 entries
     -> IncorrectResultSizeDataAccessException thrown (contract: exactly 1 expected)
     -> caught -> log diagnostic ("unexpected match count for uid=jsmith")
     -> return Optional.empty()
```

## 7. Gotchas & takeaways

> `findOne` throwing `IncorrectResultSizeDataAccessException` because a query matched more than one entry is a signal of a real data problem, not merely an awkward exception to suppress — a `uid` that's supposed to be a unique identifier having duplicates usually means something upstream (provisioning, a migration, a schema constraint that isn't actually enforced) needs fixing, and quietly picking one of the duplicates would hide that.

- `findByDn` is the ODM-aware equivalent of `lookup` (card 0004) — use it whenever the DN is already known, for the same efficiency reasons.
- `findOne` should be reserved for queries genuinely expected to match exactly one entry (a uniqueness-backed lookup by `uid` or another indexed unique attribute) — using it for a query that could legitimately match zero-or-many is a misuse of its strict contract.
- `find`/`findAll` behave like the ODM equivalent of `search` (card 0004), returning a `List` of the mapped type for however many entries match.
- None of these methods require a manually supplied mapper — the mapping comes entirely from the target class's own `@Entry`/`@Attribute`/`@Id`/`@DnAttribute` annotations (card 0014).
- Catching `IncorrectResultSizeDataAccessException` specifically around `findOne` calls, and logging the underlying data anomaly clearly, turns a confusing crash into an actionable signal that something in the directory's data needs attention.
