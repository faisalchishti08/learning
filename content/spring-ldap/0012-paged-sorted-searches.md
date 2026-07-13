---
card: spring-ldap
gi: 12
slug: paged-sorted-searches
title: "Paged & sorted searches"
---

## 1. What it is

Paged and sorted searches let a client retrieve a large LDAP result set in manageable, ordered chunks instead of all at once. Spring LDAP exposes this through JNDI's standard LDAP controls — `PagedResultscontrol` (or the higher-level `PagedResultsRequestControl`/`PagedResultsCookie` pairing) for splitting results into pages, and `SortControl` for asking the server to return results in a specified attribute order — both applied to an `LdapTemplate` search via a `DirContextProcessor`.

## 2. Why & when

A directory holding tens of thousands of entries can't reasonably be searched with a single unbounded `search` call that returns everything at once — this risks the same problems `countLimit` (card 0011) guards against, but at a much larger scale, and without a way to progressively show results to a user as they arrive. Paging exists to let the directory server hand back results in bounded batches (say, 100 at a time), with a "cookie" token that lets the client ask for the next batch. Sorting exists because paging without a defined order gives no guarantee that pages don't overlap or skip entries between requests — a meaningful, stable sort order is what makes multi-page results usable at all.

Use paged searches when:

- Listing entries from a directory large enough that returning everything in one response is impractical (rendering a paginated user directory UI, exporting all entries for a migration in controlled batches).
- Respecting a directory server's own configured size limits, which often reject or truncate very large unbounded searches outright.

Combine with sorting when the paged results need a stable, predictable order across pages — without it, the same entry could plausibly appear on more than one page, or be skipped, depending on server-side result ordering that isn't otherwise guaranteed to stay consistent between requests.

## 3. Core concept

Think of paging through directory results like reading a very long report through a photocopier that only ever hands you one page at a time, along with a bookmark (the cookie) telling the copier where you left off. Ask for the next page, hand back the bookmark, get the next page plus a new bookmark — repeat until the copier says there are no more pages. Sorting is what guarantees the report was assembled in a sensible order before the photocopier started — reading page 3 makes sense in context only because pages 1 and 2 came before it in a defined, stable sequence, not an arbitrary one that could shuffle between requests.

```java
PagedResultsDirContextProcessor pager = new PagedResultsDirContextProcessor(100); // 100 entries per page
List<String> pageResults = ldapTemplate.search(query, mapper, pager);
byte[] cookie = pager.getCookie().getCookie();
boolean hasMore = cookie != null;
```

The `DirContextProcessor` passed as the extra argument to `search` is what applies the paging (and optionally sorting) control to the underlying JNDI request and reads back the server's paging state (the cookie, and whether more pages remain) after the call.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client requests pages one at a time, passing back a cookie each time, until the server signals no more pages remain">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="90" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">holds cookie</text>

  <rect x="500" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="570" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">LDAP server</text>
  <text x="570" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">sorted result set</text>

  <line x1="160" y1="95" x2="495" y2="95" stroke="#3fb950" stroke-width="1.5" marker-end="url(#i1)"/>
  <text x="330" y="85" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">page request + cookie(n)</text>

  <line x1="500" y1="120" x2="165" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#i2)"/>
  <text x="330" y="138" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">100 entries + cookie(n+1)</text>

  <text x="330" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">repeat until server returns a null/empty cookie</text>

  <defs>
    <marker id="i1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="i2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Each round trip exchanges a cookie for the next batch of (sorted) results, until the server signals none remain.

## 5. Runnable example

The scenario: listing every employee in a large directory in stable, sorted, page-sized batches — starting with one page, then looping through all pages, and finally making the pagination resilient to a page-fetch failure partway through.

### Level 1 — Basic

```java
// OnePageSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.control.PagedResultsDirContextProcessor;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;

public class OnePageSearch {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        LdapQuery ldapQuery = query().base("ou=people").where("objectClass").is("inetOrgPerson");
        PagedResultsDirContextProcessor pager = new PagedResultsDirContextProcessor(100);

        List<String> uids = template.search(ldapQuery,
            (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get(), pager);

        System.out.println("First page: " + uids.size() + " entries");
        System.out.println("More pages available: " + (pager.getCookie().getCookie() != null));
    }
}
```

**How to run:** run against a directory with more than 100 `inetOrgPerson` entries. Expected output: `First page: 100 entries` and `More pages available: true` — confirming only the first page was fetched, with a non-null cookie signaling more remain.

### Level 2 — Intermediate

Fetching only the first page is rarely the actual goal — a full listing needs to loop, feeding each page's returned cookie back into the next request, until the server signals no cookie remains. Sorting is added here so the pages come back in a stable, predictable order.

```java
// FullPagedSortedSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.control.PagedResultsDirContextProcessor;
import org.springframework.ldap.control.PagedResultsCookie;
import org.springframework.ldap.core.SortControlDirContextProcessor;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.ArrayList;
import java.util.List;

public class FullPagedSortedSearch {
    private final LdapTemplate template;

    public FullPagedSortedSearch(LdapTemplate template) {
        this.template = template;
    }

    public List<String> allUidsSorted() {
        List<String> allUids = new ArrayList<>();
        LdapQuery ldapQuery = query().base("ou=people").where("objectClass").is("inetOrgPerson");

        PagedResultsDirContextProcessor pager = new PagedResultsDirContextProcessor(100);
        PagedResultsCookie cookie = null;

        do {
            pager.setCookie(cookie);
            List<String> page = template.search(ldapQuery,
                (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get(), pager);
            allUids.addAll(page);
            cookie = pager.getCookie();
        } while (cookie != null && cookie.getCookie() != null);

        return allUids;
    }
}
```

**How to run:** call `allUidsSorted()` against a directory with, say, 350 entries. Expected result: `allUids` contains all 350 entries, gathered across 4 page requests (100, 100, 100, 50), with the loop correctly terminating once the server returns a null cookie on the final page.

### Level 3 — Advanced

A page-fetch failure partway through a long paging loop (a transient network error on page 3 of 10) shouldn't force restarting the entire listing from page 1, nor should it silently return an incomplete list indistinguishable from a fully successful one. This level adds bounded retry per page and clearly reports partial results.

```java
// ResilientPagedSearch.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.control.PagedResultsDirContextProcessor;
import org.springframework.ldap.control.PagedResultsCookie;
import org.springframework.ldap.CommunicationException;
import org.springframework.ldap.query.LdapQuery;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.ArrayList;
import java.util.List;

public class ResilientPagedSearch {
    private final LdapTemplate template;

    public ResilientPagedSearch(LdapTemplate template) {
        this.template = template;
    }

    public record PagedListing(List<String> uids, boolean complete) {}

    public PagedListing allUidsResilient(int maxRetriesPerPage) {
        List<String> allUids = new ArrayList<>();
        LdapQuery ldapQuery = query().base("ou=people").where("objectClass").is("inetOrgPerson");

        PagedResultsCookie cookie = null;
        boolean morePages = true;

        while (morePages) {
            PagedResultsDirContextProcessor pager = new PagedResultsDirContextProcessor(100);
            pager.setCookie(cookie);

            List<String> page = null;
            for (int attempt = 0; attempt <= maxRetriesPerPage; attempt++) {
                try {
                    page = template.search(ldapQuery,
                        (AttributesMapper<String>) attrs -> (String) attrs.get("uid").get(), pager);
                    break; // success, stop retrying this page
                } catch (CommunicationException e) {
                    if (attempt == maxRetriesPerPage) {
                        // Exhausted retries for this page: report what was gathered so far as incomplete.
                        return new PagedListing(allUids, false);
                    }
                }
            }
            allUids.addAll(page);
            cookie = pager.getCookie();
            morePages = cookie != null && cookie.getCookie() != null;
        }
        return new PagedListing(allUids, true);
    }
}
```

**How to run:** simulate a transient failure by stopping the LDAP server briefly during page 3 of a multi-page listing, configured to restart before `maxRetriesPerPage` is exhausted. Expected result: the retry loop recovers and the final `PagedListing` has `complete=true` with every entry present. Then simulate a failure that outlasts every retry attempt: expect `complete=false`, with `uids` containing only the pages successfully gathered before the persistent failure — a clear, honest signal to the caller that the listing is partial, rather than either crashing outright or silently returning an incomplete list that looks the same as a complete one.

## 6. Walkthrough

Tracing `allUidsResilient(2)` across a 3-page result set where page 2 fails once transiently, in execution order:

1. Page 1: `pager.setCookie(null)` (no prior cookie), `template.search(...)` succeeds on the first attempt, returning 100 entries; `allUids` now has 100, and `cookie` is set to the value returned for page 2.
2. Page 2, attempt 0: `template.search(...)` throws `CommunicationException` (a transient network blip); since `attempt` (0) hasn't reached `maxRetriesPerPage` (2), the loop retries.
3. Page 2, attempt 1: the transient issue has resolved, `template.search(...)` succeeds, returning the next 100 entries; the `break` exits the retry loop for this page. `allUids` now has 200 entries.
4. Page 3: `template.search(...)` succeeds on the first attempt, returning the final 50 entries; `cookie` comes back null (or with a null internal cookie value), setting `morePages` to `false`.
5. The `while (morePages)` loop exits; the method returns `PagedListing(allUids, true)` — all 350 entries gathered, `complete=true`, since every page eventually succeeded within its retry budget.

```
page 1: search -> 100 entries, cookie=C1               -> allUids=100
page 2, attempt 0: search -> CommunicationException    -> retry (attempt < max)
page 2, attempt 1: search -> 100 entries, cookie=C2     -> allUids=200
page 3: search -> 50 entries, cookie=null               -> morePages=false
-> PagedListing(allUids=350 entries, complete=true)
```

## 7. Gotchas & takeaways

> The paging cookie returned by one page's `DirContextProcessor` must be fed into the *next* request's processor before it's issued — reusing a fresh `PagedResultsDirContextProcessor` without carrying the cookie forward restarts pagination from the beginning rather than continuing from where the previous page left off, a subtle bug that can silently produce duplicate or missing entries.

- Paging exists to bound the size of any single request/response against a large directory; sorting exists to make the pages meaningful together — use both when listing more than a small, fixed number of entries.
- A fresh `PagedResultsDirContextProcessor` should be created per page request, but the `PagedResultsCookie` from the previous page must be explicitly carried forward via `setCookie(...)` — the processor object itself is not meant to be reused as-is across pages.
- Treat a page-fetch failure as recoverable with bounded retry (Level 3) rather than aborting the entire listing — for any sufficiently large or slow paging loop, a single transient network blip partway through is a realistic, not exotic, failure mode.
- Always distinguish a complete listing from a partial one in whatever the paging loop returns to its caller — silently returning fewer entries than actually exist, indistinguishable from a genuinely complete result, is a common source of subtly wrong downstream behavior (a user directory that mysteriously "loses" entries after a network hiccup).
- Not every LDAP server supports paged or sorted result controls identically — verify the target directory server's support and behavior for `PagedResultsControl`/`SortControl` before relying on them in production, since behavior for edge cases (an unsupported control, an exhausted server-side resource) can vary between server implementations.
