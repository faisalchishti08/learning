---
card: spring-ldap
gi: 10
slug: filters-ldapquerybuilder-hardcoded-encoded-filters
title: "Filters (LdapQueryBuilder, hardcoded & encoded filters)"
---

## 1. What it is

An LDAP filter is the query expression that decides which entries a `search` matches, written in the standard LDAP filter syntax (e.g. `(&(objectClass=inetOrgPerson)(uid=jsmith))`). Spring LDAP offers three ways to produce one: writing the raw filter string by hand (a **hardcoded filter**), building it safely with escaping via classes like `EqualsFilter` (an **encoded filter**), or composing it fluently and safely with the modern **`LdapQueryBuilder`**, which is the recommended approach for new code and also lets `LdapTemplate` handle the base DN, scope, and filter together in one expression.

## 2. Why & when

LDAP filter syntax has its own special characters (`(`, `)`, `*`, `\`, and the null character) that must be escaped when they appear inside a value rather than as filter syntax — get this wrong, and a value containing `*` unintentionally turns into a wildcard, or a value containing `)` can prematurely close a filter clause and let an attacker inject additional filter logic (an LDAP injection, directly analogous to SQL injection). Hardcoded filter strings put this escaping burden entirely on the developer, one string-concatenation site at a time. `LdapQueryBuilder` exists to remove that burden: it builds correct, properly-escaped filters fluently, and bundles the search base and scope into the same expression `LdapTemplate.search(query, mapper)` consumes directly.

Use a **hardcoded filter string** only for filters built entirely from fixed, non-user-controlled literals (e.g. `"(objectClass=inetOrgPerson)"` with no interpolated values at all).

Use **`EqualsFilter`/`LdapQueryBuilder`** whenever any part of the filter is built from a variable — user input, a value read from another system, anything not a hardcoded literal in the source code.

## 3. Core concept

Think of a hardcoded filter string as writing a legal document by hand, one clause at a time, and being personally responsible for correctly escaping every quotation mark yourself — miss one, and the document's meaning can shift in ways you didn't intend, or a malicious party supplying part of the text could smuggle in their own clause. `LdapQueryBuilder` is like using a legal-document generator that takes each fact as a separate, clearly-labeled field, and always produces a document with valid, correctly escaped clauses, regardless of what characters appear in any individual field's value.

```java
import static org.springframework.ldap.query.LdapQueryBuilder.query;

LdapQuery ldapQuery = query()
    .base("ou=people")
    .where("objectClass").is("inetOrgPerson")
    .and("uid").is(uid); // uid is safely escaped regardless of its content

List<User> users = ldapTemplate.search(ldapQuery, userMapper);
```

`LdapQueryBuilder`'s fluent methods — `.where(attr).is(value)`, `.like(pattern)`, `.gte(value)`, `.and(...)`, `.or(...)` — each correspond to a standard LDAP filter construct (equality, substring, greater-than-or-equal, AND, OR) and escape their value arguments automatically.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three approaches to filters: hardcoded string with manual escaping risk, EqualsFilter with automatic escaping, and LdapQueryBuilder combining base, scope, and filter fluently">
  <rect x="10" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="110" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Hardcoded string</text>
  <text x="110" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">manual escaping, risky</text>

  <rect x="230" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">EqualsFilter</text>
  <text x="330" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">auto-escaped, single term</text>

  <rect x="450" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">LdapQueryBuilder</text>
  <text x="550" y="72" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fluent, base+scope+filter</text>

  <line x1="110" y1="90" x2="330" y2="150" stroke="#8b949e" stroke-width="1"/>
  <line x1="330" y1="90" x2="330" y2="150" stroke="#8b949e" stroke-width="1"/>
  <line x1="550" y1="90" x2="330" y2="150" stroke="#8b949e" stroke-width="1"/>
  <rect x="230" y="150" width="200" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="330" y="172" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ldapTemplate.search(...)</text>
</svg>

All three approaches ultimately feed `LdapTemplate.search`, but only the latter two are safe when any filter component comes from a variable.

## 5. Runnable example

The scenario: searching for active employees by department, starting with a hardcoded filter, then parameterizing it safely with `LdapQueryBuilder`, and finally composing a multi-condition query with pagination-friendly scoping.

### Level 1 — Basic

```java
// HardcodedFilterSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.AttributesMapper;

import java.util.List;

public class HardcodedFilterSearch {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        // Safe ONLY because both values here are fixed literals, never user input.
        List<String> uids = template.search(
            "ou=people",
            "(&(objectClass=inetOrgPerson)(departmentNumber=4120))",
            (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get()
        );

        System.out.println("Department 4120 members: " + uids);
    }
}
```

**How to run:** run against a seeded directory with several `inetOrgPerson` entries, some with `departmentNumber=4120`. Expected output: `Department 4120 members: [jsmith, adavis]` (or whichever uids match).

### Level 2 — Intermediate

Making the department number a parameter — as any real search endpoint would need — means it could come from user input. Building it into the filter with string concatenation reopens the injection risk from card 0009; `LdapQueryBuilder` closes it.

```java
// SafeParameterizedSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;

public class SafeParameterizedSearch {
    private final LdapTemplate template;

    public SafeParameterizedSearch(LdapTemplate template) {
        this.template = template;
    }

    public List<String> findByDepartment(String departmentNumber) {
        LdapQuery ldapQuery = query()
            .base("ou=people")
            .where("objectClass").is("inetOrgPerson")
            .and("departmentNumber").is(departmentNumber); // escaped regardless of content

        return template.search(ldapQuery,
            (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get());
    }
}
```

**How to run:** call `findByDepartment("4120")` — expect the same result as Level 1. Then call `findByDepartment("4120)(uid=*")`, an injection attempt trying to widen the filter to match every uid: expect it to correctly match **nothing** (or only an entry whose literal `departmentNumber` happens to be that exact malformed string), because `LdapQueryBuilder` escapes the value rather than interpreting it as filter syntax — unlike what string concatenation into a hardcoded-style filter would have allowed.

### Level 3 — Advanced

Real search screens combine multiple optional conditions (department, and/or active status, and/or a name substring) that shouldn't all be mandatory — a department-only search shouldn't require a name too. This level builds a query conditionally from several optional parameters.

```java
// FlexibleEmployeeSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.query.ConditionCriteria;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;

public class FlexibleEmployeeSearch {
    private final LdapTemplate template;

    public FlexibleEmployeeSearch(LdapTemplate template) {
        this.template = template;
    }

    public List<String> search(String departmentNumber, String surnamePrefix, boolean activeOnly) {
        ConditionCriteria criteria = query()
            .base("ou=people")
            .where("objectClass").is("inetOrgPerson");

        if (departmentNumber != null) {
            criteria = criteria.and("departmentNumber").is(departmentNumber);
        }
        if (surnamePrefix != null) {
            criteria = criteria.and("sn").like(surnamePrefix + "*"); // substring filter, safely built
        }
        if (activeOnly) {
            criteria = criteria.and("employeeStatus").is("active");
        }

        LdapQuery ldapQuery = (LdapQuery) criteria;
        return template.search(ldapQuery,
            (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get());
    }
}
```

**How to run:** call `search("4120", null, true)` — expect only active employees in department 4120. Call `search(null, "Sm", false)` — expect every employee (active or not, any department) whose surname starts with `Sm`. Each call assembles only the clauses relevant to the parameters actually supplied, rather than a single rigid filter requiring every field.

## 6. Walkthrough

Tracing `search("4120", null, true)`, in execution order:

1. `query().base("ou=people").where("objectClass").is("inetOrgPerson")` starts building the query, establishing the mandatory base condition every real employee entry satisfies.
2. Since `departmentNumber` is `"4120"` (non-null), `.and("departmentNumber").is("4120")` is appended, narrowing the query to that department.
3. Since `surnamePrefix` is `null`, that `if` block is skipped entirely — no name-related clause is added to the query at all.
4. Since `activeOnly` is `true`, `.and("employeeStatus").is("active")` is appended, further narrowing to active employees only.
5. The accumulated `criteria` is cast to `LdapQuery` and passed to `template.search(ldapQuery, mapper)`.
6. Internally, `LdapTemplate` extracts the base (`ou=people`), the assembled filter string (equivalent to `(&(objectClass=inetOrgPerson)(departmentNumber=4120)(employeeStatus=active))`), and the default search scope, then performs the JNDI search exactly as described in card 0001's walkthrough.
7. Each matching entry is passed to the `AttributesMapper`, extracting `uid`, and the collected `uid` values are returned as the final `List<String>`.

```
search("4120", null, true)
  base condition: objectClass=inetOrgPerson         [always included]
  departmentNumber != null -> AND departmentNumber=4120   [included]
  surnamePrefix == null    -> (sn clause skipped)         [omitted]
  activeOnly == true       -> AND employeeStatus=active   [included]
  -> effective filter: (&(objectClass=inetOrgPerson)(departmentNumber=4120)(employeeStatus=active))
```

## 7. Gotchas & takeaways

> Concatenating a variable directly into a filter string — even one that looks harmless, like a plain department number — is unsafe the moment that variable can originate from outside the application's own fixed literals. A value like `4120)(uid=*` can widen a filter to match unintended entries. Always route variable filter components through `EqualsFilter`, `.is(...)`, `.like(...)`, or another `LdapQueryBuilder` method, never through string concatenation.

- Hardcoded filter strings are only safe when every component is a fixed literal written directly in the source code — the moment any part becomes a variable, switch to `LdapQueryBuilder`.
- `LdapQueryBuilder` bundles base, scope, and filter into a single `LdapQuery` object, which `LdapTemplate.search(query, mapper)` consumes directly — no separate base-string and filter-string arguments to keep in sync.
- Conditionally building a query (Level 3) by reassigning the fluent builder's return value across `if` blocks is a clean way to support several optional search criteria without duplicating filter-construction logic for every possible combination.
- `.like("prefix*")` builds an LDAP substring filter; the `*` wildcard placement should be a literal part of the pattern string the developer controls, not something a raw, unescaped user value could introduce unexpectedly elsewhere in the filter.
- When reviewing existing code for LDAP injection risk, treat any `String` filter built with `+` concatenation from a non-literal source as a signal worth investigating, the same way string-concatenated SQL is treated as a signal for SQL injection review.
