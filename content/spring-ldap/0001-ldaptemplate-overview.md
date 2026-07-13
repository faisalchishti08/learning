---
card: spring-ldap
gi: 1
slug: ldaptemplate-overview
title: "LdapTemplate overview"
---

## 1. What it is

`LdapTemplate` is Spring LDAP's central helper class for talking to a directory server. It plays the same role for LDAP that `JdbcTemplate` plays for relational databases: it owns the low-level, error-prone plumbing (opening a connection, running the operation, closing the connection, translating checked exceptions) so application code can focus on what it actually wants — search for an entry, read some attributes, add a record — instead of how to manage a `javax.naming.directory.DirContext` safely.

## 2. Why & when

Talking to LDAP directly through Java's built-in JNDI API (`DirContext`, `NamingEnumeration`, and friends) is verbose and unforgiving. Every operation needs a context obtained and released, every failure throws a checked `NamingException` that must be caught and translated, and resource leaks are easy to introduce if a context isn't closed on every exit path, including exception paths. `LdapTemplate` exists because this ceremony is identical across almost every LDAP operation an application performs, so Spring extracts it once, the same way it does for JDBC and other resource-based APIs.

Reach for `LdapTemplate` whenever an application needs to:

- Look up user or group entries for authentication or authorization (checking a user's directory record before granting access).
- Search a corporate directory for people, groups, or organizational units matching some criteria.
- Synchronize directory data with an application's own database (reading LDAP entries and mapping them into domain objects).
- Add, modify, or remove directory entries, such as provisioning a new user account when someone joins a team.

If an application only reads LDAP occasionally through a single hardcoded query, raw JNDI is technically possible — but as soon as there is more than one operation, or any need for testability, `LdapTemplate` pays for itself immediately.

## 3. Core concept

Think of `LdapTemplate` as a translator standing between the application and a very particular, very literal foreign bureaucrat (the LDAP server via JNDI). The bureaucrat only understands rigid forms (`DirContext` calls) and only responds through equally rigid channels (`NamingEnumeration`, `Attributes`). Talking to the bureaucrat directly means learning the forms yourself, always remembering to formally end the meeting (`context.close()`) — even if the meeting went badly (an exception was thrown). The translator handles all of that: you ask a plain question ("find the entry for uid=jsmith"), and the translator fills out the form, has the conversation, closes the meeting properly regardless of outcome, and hands you back a clean, plain-language answer.

Structurally, `LdapTemplate` follows Spring's well-known **template method pattern**:

1. It obtains a `DirContext` from a configured `ContextSource` (card 0002).
2. It performs the requested operation (a search, a bind, a modify).
3. It converts any raw entries into whatever shape the caller asked for, using a callback such as an `AttributesMapper` (card 0005) or `ContextMapper` (card 0006).
4. It releases the context — always, even if step 2 or 3 threw an exception.
5. It translates any `javax.naming.NamingException` into Spring's unchecked `org.springframework.ldap.NamingException` hierarchy, so callers aren't forced to catch checked exceptions everywhere.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application code calls LdapTemplate, which obtains a context from ContextSource, talks to the LDAP server, and always releases the context">
  <rect x="20" y="90" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="115" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Application</text>
  <text x="90" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">code</text>

  <rect x="230" y="90" width="160" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="115" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">LdapTemplate</text>
  <text x="310" y="133" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">open / call / close</text>

  <rect x="460" y="20" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ContextSource</text>
  <text x="550" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hands out DirContext</text>

  <rect x="460" y="160" width="180" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="550" y="185" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">LDAP server</text>
  <text x="550" y="202" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(JNDI / DirContext)</text>

  <line x1="160" y1="120" x2="225" y2="120" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="192" y="110" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">search()</text>

  <line x1="390" y1="105" x2="455" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>
  <text x="430" y="75" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">1. get context</text>

  <line x1="390" y1="135" x2="455" y2="180" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a3)"/>
  <text x="430" y="165" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">2. run op</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`LdapTemplate` sits between plain application code and the raw JNDI/`DirContext` conversation, always closing the context regardless of outcome.

## 5. Runnable example

The scenario: look up a single employee's email address by their username in a directory, starting with the simplest possible search and growing it to handle missing entries and multiple directory servers safely.

### Level 1 — Basic

```java
// EmployeeLookup.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.AttributesMapper;

import javax.naming.directory.Attributes;
import java.util.List;

public class EmployeeLookup {
    public static void main(String[] args) throws Exception {
        LdapContextSource contextSource = new LdapContextSource();
        contextSource.setUrl("ldap://localhost:389");
        contextSource.setBase("dc=example,dc=com");
        contextSource.setUserDn("cn=admin,dc=example,dc=com");
        contextSource.setPassword("adminpass");
        contextSource.afterPropertiesSet();

        LdapTemplate ldapTemplate = new LdapTemplate(contextSource);

        List<String> emails = ldapTemplate.search(
            "ou=people",
            "(uid=jsmith)",
            (AttributesMapper<String>) attrs -> {
                Attributes a = (Attributes) attrs;
                return (String) a.get("mail").get();
            }
        );

        System.out.println("Emails found: " + emails);
    }
}
```

**How to run:** requires a running LDAP server (e.g. `docker run -p 389:389 osixia/openldap`) seeded with a `uid=jsmith` entry under `ou=people,dc=example,dc=com` that has a `mail` attribute. Compile with the Spring LDAP jars on the classpath and run `java EmployeeLookup.java`. Expected output: `Emails found: [jsmith@example.com]`.

### Level 2 — Intermediate

Real directories don't guarantee a match exists, and `attrs.get("mail")` on an entry without a `mail` attribute throws a `NullPointerException`. The template also shouldn't be rebuilt on every call — it's meant to be a long-lived, thread-safe singleton.

```java
// EmployeeLookupService.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;

import javax.naming.directory.Attributes;
import java.util.List;
import java.util.Optional;

public class EmployeeLookupService {
    private final LdapTemplate ldapTemplate; // built once, reused for the service's lifetime

    public EmployeeLookupService(LdapTemplate ldapTemplate) {
        this.ldapTemplate = ldapTemplate;
    }

    public Optional<String> findEmail(String uid) {
        List<String> results = ldapTemplate.search(
            "ou=people",
            "(uid=" + uid + ")",
            (AttributesMapper<String>) attrs -> {
                Attributes a = (Attributes) attrs;
                Object mailAttr = a.get("mail") == null ? null : a.get("mail").get();
                return mailAttr == null ? null : mailAttr.toString();
            }
        );
        return results.stream().filter(e -> e != null).findFirst();
    }
}
```

**How to run:** construct `EmployeeLookupService` once with a shared `LdapTemplate`, then call `findEmail("jsmith")` and `findEmail("nosuchuser")`. Expected output: `Optional[jsmith@example.com]` for the first call and `Optional.empty` for the second — no exception thrown either way.

### Level 3 — Advanced

Production directories are frequently unreachable for short periods (network blips, server restarts), and building the filter string by concatenation (as above) is an LDAP injection risk if `uid` ever comes from user input. This level adds a parameterized filter and graceful handling of a down directory.

```java
// SafeEmployeeLookupService.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.AttributesMapper;
import org.springframework.ldap.filter.EqualsFilter;
import org.springframework.ldap.CommunicationException;

import javax.naming.directory.Attributes;
import java.util.List;
import java.util.Optional;

public class SafeEmployeeLookupService {
    private final LdapTemplate ldapTemplate;

    public SafeEmployeeLookupService(LdapTemplate ldapTemplate) {
        this.ldapTemplate = ldapTemplate;
    }

    public Optional<String> findEmail(String uid) {
        // EqualsFilter escapes special characters in `uid` automatically —
        // safe even if uid originated from an HTTP request parameter.
        EqualsFilter filter = new EqualsFilter("uid", uid);

        try {
            List<String> results = ldapTemplate.search(
                "ou=people",
                filter.encode(),
                (AttributesMapper<String>) attrs -> {
                    Attributes a = (Attributes) attrs;
                    return a.get("mail") == null ? null : a.get("mail").get().toString();
                }
            );
            return results.stream().filter(e -> e != null).findFirst();
        } catch (CommunicationException e) {
            // Directory unreachable: fail safe rather than crash the caller.
            System.err.println("LDAP directory unreachable: " + e.getMessage());
            return Optional.empty();
        }
    }
}
```

**How to run:** call `findEmail("jsmith*)(uid=*")` — a string engineered to look like an LDAP filter injection attempt — against `SafeEmployeeLookupService`. Because `EqualsFilter` escapes the special characters, the search treats it as one literal (and non-matching) `uid` value rather than letting it corrupt the filter, and correctly returns `Optional.empty` instead of exposing directory contents. Then stop the LDAP server and repeat the call: expect a caught `CommunicationException` and a logged message instead of an uncaught exception crashing the caller.

## 6. Walkthrough

Tracing `findEmail("jsmith")` through `SafeEmployeeLookupService`, in execution order:

1. `new EqualsFilter("uid", uid)` builds a filter object representing `(uid=jsmith)`; if `uid` contained special LDAP filter characters (like `*`, `(`, `)`), `filter.encode()` would escape them so they can't alter the filter's meaning.
2. `ldapTemplate.search("ou=people", filter.encode(), mapper)` is called. Internally, `LdapTemplate` asks the configured `ContextSource` for a `DirContext` — a live, authenticated connection to the LDAP server.
3. The template issues the actual JNDI search operation against the directory, scoped to the `ou=people` subtree, using the encoded filter string.
4. The LDAP server evaluates the filter against its entries and returns any matches as a stream of raw `SearchResult` objects, each carrying an `Attributes` collection (the entry's fields, like `uid`, `mail`, `cn`).
5. For every matching entry, `LdapTemplate` invokes the `AttributesMapper` callback, passing in that entry's `Attributes`. The callback pulls out just the `mail` value (or `null` if absent) and returns it — this is where raw directory data becomes a plain Java value the rest of the application can use.
6. Once all matching entries are processed, `LdapTemplate` releases the `DirContext` back to the `ContextSource` — this happens in a `finally`-equivalent path internally, so it happens whether the search succeeded or one of the mapper calls threw an exception.
7. Back in `findEmail`, the list of mapped values (nulls and all) is filtered down to the first non-null entry and wrapped in an `Optional`.
8. If step 2 instead failed at the network level (director down), a `CommunicationException` — Spring LDAP's unchecked translation of the underlying `javax.naming.CommunicationException` — propagates up to the `catch` block, which logs it and returns `Optional.empty()` instead of letting the exception escape to the caller.

```
findEmail("jsmith")
   -> EqualsFilter("uid","jsmith").encode() => "(uid=jsmith)"
   -> LdapTemplate.search(base, filter, mapper)
        -> ContextSource.getContext()          [1: obtain]
        -> DirContext.search(...)              [2: query LDAP server]
        -> for each SearchResult: mapper.mapFromAttributes(attrs)
        -> release DirContext                  [3: always happens]
   -> List<String> -> first non-null -> Optional<String>
```

## 7. Gotchas & takeaways

> Building an LDAP filter string with plain concatenation (`"(uid=" + uid + ")"`) is vulnerable to **LDAP injection** if `uid` ever comes from user input — a value like `*)(uid=*` can widen the search to match every entry in the subtree. Always build filters with `EqualsFilter` or the broader `LdapQueryBuilder` (card 0011), which escape special characters automatically.

- `LdapTemplate` should be constructed once (typically as a Spring bean) and reused; it's thread-safe and cheap to call repeatedly.
- It automatically converts checked `javax.naming.NamingException` into Spring's unchecked `org.springframework.ldap.NamingException` hierarchy — no `try/catch` boilerplate is needed for every call.
- Context acquisition and release are always paired, even on exceptions raised inside a mapper callback — application code never has to remember to close a `DirContext` manually.
- A directory being briefly unreachable is a normal operating condition in production, not an edge case — catch `CommunicationException` (or a broader `org.springframework.ldap.NamingException`) at the boundary where a failed lookup has a sane fallback.
- Prefer `EqualsFilter`/`LdapQueryBuilder` over manual string concatenation for any filter built from external input.
