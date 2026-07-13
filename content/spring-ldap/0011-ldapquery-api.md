---
card: spring-ldap
gi: 11
slug: ldapquery-api
title: "LdapQuery API"
---

## 1. What it is

`LdapQuery` is the object produced by `LdapQueryBuilder` (card 0010) that bundles together everything a search needs in one place: the base DN, the search scope (how deep into the tree to look), the filter, and optionally which attributes to return and how many results to allow. Passing an `LdapQuery` to `LdapTemplate.search(query, mapper)` replaces the older style of passing base, filter, and search-controls arguments separately, and is the modern, recommended way to call `search` in Spring LDAP.

## 2. Why & when

Before `LdapQuery` existed, calling `LdapTemplate.search` with anything beyond a plain base-and-filter required constructing a raw `javax.naming.directory.SearchControls` object — setting the scope, size limit, and returned attributes as individual mutable fields on a somewhat awkward JNDI class — and passing it alongside separate base and filter arguments. `LdapQuery` exists to consolidate all of that into one fluently-built, immutable-feeling object, matching the same base-plus-filter mental model developers already use, while still exposing the scope and attribute-selection controls that real applications need.

Use the full `LdapQuery` API (beyond the basic filter-building shown in card 0010) when:

- The search needs to be scoped narrower or wider than the default (searching only immediate children versus the entire subtree).
- Only specific attributes are needed back from a search, and returning every attribute on every entry is unnecessary network and processing overhead.
- The search should be capped at a certain number of results, to avoid an unexpectedly broad filter returning an enormous result set.

## 3. Core concept

Think of `LdapQuery` as filling out one comprehensive request form for a librarian, rather than shouting several separate instructions across the room. The form has a section for "which section of the library to search" (scope), "what criteria to match" (filter), "which specific facts about each matching book to report back" (attribute selection), and "how many results is too many" (a count limit) — the librarian reads the whole form once and executes exactly what's asked, rather than juggling several loose, separately-passed instructions that could get out of sync with each other.

```java
import static org.springframework.ldap.query.LdapQueryBuilder.query;
import static org.springframework.ldap.query.SearchScope.ONELEVEL;

LdapQuery ldapQuery = query()
    .base("ou=people")
    .searchScope(ONELEVEL)          // only direct children of ou=people, not the whole subtree
    .attributes("uid", "mail")      // only fetch these two attributes, not every one
    .where("objectClass").is("inetOrgPerson");
```

The three standard LDAP search scopes, all selectable via `.searchScope(...)`:

- **`OBJECT`** — the base DN itself only, not its children (equivalent to a `lookup`, card 0004).
- **`ONELEVEL`** — immediate children of the base only, not grandchildren.
- **`SUBTREE`** — the base and every descendant at any depth (the default if not specified).

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three search scopes: OBJECT matches only the base entry, ONELEVEL matches immediate children, SUBTREE matches every descendant">
  <text x="110" y="20" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OBJECT</text>
  <circle cx="110" cy="60" r="14" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="80" cy="110" r="12" fill="#1c2430" stroke="#8b949e"/>
  <circle cx="140" cy="110" r="12" fill="#1c2430" stroke="#8b949e"/>

  <text x="320" y="20" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ONELEVEL</text>
  <circle cx="320" cy="60" r="14" fill="#1c2430" stroke="#8b949e"/>
  <circle cx="280" cy="110" r="12" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="360" cy="110" r="12" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="280" cy="155" r="10" fill="#1c2430" stroke="#8b949e"/>

  <text x="530" y="20" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">SUBTREE</text>
  <circle cx="530" cy="60" r="14" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="490" cy="110" r="12" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="570" cy="110" r="12" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <circle cx="490" cy="155" r="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
</svg>

Green nodes are matched by each scope: `OBJECT` matches only the base itself; `ONELEVEL` matches direct children; `SUBTREE` matches everything beneath the base.

## 5. Runnable example

The scenario: searching for department members with progressively more precise control over scope, returned attributes, and result size.

### Level 1 — Basic

```java
// SubtreeSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;

public class SubtreeSearch {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        LdapQuery ldapQuery = query()
            .base("ou=people")
            .where("objectClass").is("inetOrgPerson");

        List<String> uids = template.search(ldapQuery,
            (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get());

        System.out.println("All people (default SUBTREE scope): " + uids);
    }
}
```

**How to run:** run against a directory with `ou=people` containing nested organizational units, each with their own entries. Expected output: every matching `uid` at any depth under `ou=people`, since the default scope is `SUBTREE`.

### Level 2 — Intermediate

Returning every attribute on every entry when only `uid` and `mail` are actually used wastes bandwidth and processing, especially for entries with large binary attributes (like a `jpegPhoto`). Restricting both scope and returned attributes narrows the search to exactly what's needed.

```java
// ScopedAttributeLimitedSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;
import static org.springframework.ldap.query.SearchScope.ONELEVEL;

import javax.naming.directory.Attributes;
import java.util.List;

public class ScopedAttributeLimitedSearch {
    private final LdapTemplate template;

    public ScopedAttributeLimitedSearch(LdapTemplate template) {
        this.template = template;
    }

    public List<String> directPeopleEmails() {
        LdapQuery ldapQuery = query()
            .base("ou=people")
            .searchScope(ONELEVEL)          // only direct entries in ou=people, not nested OUs
            .attributes("uid", "mail")       // skip every other attribute, including large ones
            .where("objectClass").is("inetOrgPerson");

        return template.search(ldapQuery, (AttributesMapper<String>) attrs -> {
            Attributes a = (Attributes) attrs;
            return a.get("uid").get() + ": " + (a.get("mail") != null ? a.get("mail").get() : "no email");
        });
    }
}
```

**How to run:** call `directPeopleEmails()` on the same directory as Level 1. Expected result: only entries directly under `ou=people` are returned — any entries nested inside a sub-organizational-unit (like `ou=contractors,ou=people`) are excluded, since `ONELEVEL` doesn't descend further, and each mapped result only reflects the two requested attributes.

### Level 3 — Advanced

An overly broad or accidentally unbounded filter against a very large directory can return far more results than the application intended to handle, risking memory pressure or an unresponsive UI listing thousands of rows. This level caps the result count and handles the case where the size limit is actually hit, so the caller knows the result is a partial (truncated) view.

```java
// BoundedSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.query.LdapQuery;
import org.springframework.ldap.SizeLimitExceededException;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;
import java.util.ArrayList;

public class BoundedSearch {
    private final LdapTemplate template;

    public BoundedSearch(LdapTemplate template) {
        this.template = template;
    }

    public record BoundedResult(List<String> uids, boolean truncated) {}

    public BoundedResult searchPeopleBySurname(String surnamePrefix, int maxResults) {
        LdapQuery ldapQuery = query()
            .base("ou=people")
            .countLimit(maxResults)          // ask the server to cap the result count
            .attributes("uid")
            .where("sn").like(surnamePrefix + "*");

        try {
            List<String> uids = template.search(ldapQuery,
                (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get());
            return new BoundedResult(uids, false);
        } catch (SizeLimitExceededException e) {
            // Server enforced the limit and stopped partway through — report what was gathered as truncated.
            return new BoundedResult(new ArrayList<>(), true);
        }
    }
}
```

**How to run:** call `searchPeopleBySurname("S", 5)` against a directory with more than five surnames starting with `S`. Expected result: depending on server behavior, either exactly 5 results are returned with `truncated=false` (some servers silently cap rather than throw), or a `SizeLimitExceededException` is thrown once the limit is hit, caught here and reported as `truncated=true` with an empty list — either way, the caller is never left waiting on or silently handed an unexpectedly enormous result set.

## 6. Walkthrough

Tracing `searchPeopleBySurname("S", 5)` against a directory where 12 people have surnames starting with `S`, in execution order (assuming the server enforces the limit by throwing):

1. `query().base("ou=people").countLimit(5).attributes("uid").where("sn").like("S*")` builds an `LdapQuery` carrying the base, a result-count cap of 5, a restricted attribute list, and a substring filter.
2. `template.search(ldapQuery, mapper)` translates this into a JNDI search with an equivalent `SearchControls` object internally, including its count limit set to 5.
3. The LDAP server begins streaming matching entries back; once it has returned the 5th match and finds there would be more, it stops and signals that the size limit was hit rather than silently returning only 5 with no indication more existed.
4. Spring LDAP translates the underlying JNDI `SizeLimitExceededException` into its own unchecked equivalent, which propagates out of `template.search(...)`.
5. The `catch (SizeLimitExceededException e)` block in `searchPeopleBySurname` catches this, and returns a `BoundedResult` with an empty list and `truncated=true` — deliberately not returning the partial 5 results already seen, since some driver/server combinations don't reliably expose partial results alongside the exception, and treating "truncated" uniformly as "don't trust what came back" is simpler and safer than case-by-case partial-result handling.
6. The caller receives a `BoundedResult` and can react appropriately — showing the user "more than 5 matches, please refine your search" rather than either hanging on an enormous result set or silently showing an incomplete list without explanation.

```
searchPeopleBySurname("S", 5), 12 real matches exist
  query: base=ou=people, countLimit=5, filter=(sn=S*), attrs=[uid]
  server streams matches, hits the 5th, more exist -> SizeLimitExceededException
  caught -> BoundedResult(uids=[], truncated=true)
```

## 7. Gotchas & takeaways

> Exact `SizeLimitExceededException` behavior (whether partial results are exposed alongside the exception, or the exception replaces them entirely) can vary by underlying LDAP driver and server. Don't rely on partial results being reliably present when a size limit is hit — treat the exception primarily as a signal that the query needs refining or the limit needs revisiting, not as a source of a guaranteed-complete partial list.

- `.searchScope(...)` (`OBJECT`, `ONELEVEL`, `SUBTREE`) controls how far into the tree a search descends — defaulting to `SUBTREE` is convenient but can be more expensive than necessary when the target entries are known to live at a specific, shallower level.
- `.attributes(...)` restricts which attributes come back from the server — a meaningful optimization when entries carry large or numerous attributes the caller doesn't need for a particular search.
- `.countLimit(...)` caps how many results the server will return, protecting the application from an unexpectedly broad filter returning far more entries than intended.
- `LdapQuery` replaces the older pattern of manually constructing a `SearchControls` object alongside separate base and filter arguments — new code should build searches through `LdapQueryBuilder`/`LdapQuery` rather than the older, more verbose JNDI-level API.
- Always give users of a search feature a clear, honest signal when results were truncated by a limit — silently returning a partial list indistinguishable from a genuinely complete one can mislead whoever consumes the result into believing they've seen everything that matches.
