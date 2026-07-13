---
card: spring-ldap
gi: 5
slug: attributesmapper
title: "AttributesMapper"
---

## 1. What it is

`AttributesMapper<T>` is a callback interface used with `LdapTemplate` to convert one directory entry's raw `javax.naming.directory.Attributes` into a plain Java object of type `T`. It has a single method, `mapFromAttributes(Attributes attrs)`, and `LdapTemplate` invokes it once per matching entry during a `search` or `lookup`, collecting the results into the final `List<T>` (or single `T`) that gets handed back to calling code.

## 2. Why & when

Raw LDAP `Attributes` is a low-level, unstructured collection of name/value pairs, awkward to work with directly throughout application code (`attrs.get("mail").get()`, cast, null-check, repeat for every attribute, everywhere the entry is used). `AttributesMapper` exists to put that unpacking logic in exactly one place per entry type, so the rest of the application deals with clean domain objects (a `User` with typed fields) instead of repeating attribute-extraction code at every call site.

Use `AttributesMapper` when:

- Mapping a directory entry into a simple, flat domain object built entirely from its own attributes (a `User` record built from `uid`, `cn`, `mail`).
- The mapping doesn't need the entry's own DN or any binding/naming context — just its attribute values.

For cases needing the entry's DN as part of the mapped object, `ContextMapper` (card 0006) is the better fit — `AttributesMapper` only ever sees the attributes, never the DN.

## 3. Core concept

Think of an `AttributesMapper` as a form-processing clerk who receives one filled-out application form (`Attributes`) per person and fills in one line of an output ledger from it (the mapped domain object). The clerk doesn't care how many forms come in — one, ten, a thousand — the same fixed procedure runs for every single form, and `LdapTemplate` is the one responsible for gathering every form (every matching entry) and handing them to the clerk one at a time, then compiling the clerk's outputs into the final ledger (the `List<T>`).

```java
AttributesMapper<User> userMapper = attrs -> {
    User u = new User();
    u.setUid((String) attrs.get("uid").get());
    u.setEmail((String) attrs.get("mail").get());
    return u;
};
```

Because it's a functional interface, `AttributesMapper` is almost always written as a lambda, as above, rather than a named class — the mapping logic is usually short enough that a separate class would just add ceremony.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LdapTemplate calls the AttributesMapper once per matching entry, collecting the mapped results into a List">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Raw entries</text>
  <text x="90" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Attributes x N</text>

  <rect x="250" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">AttributesMapper</text>
  <text x="325" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">called once per entry</text>

  <rect x="480" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">List&lt;T&gt;</text>
  <text x="550" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">mapped domain objs</text>

  <line x1="160" y1="110" x2="245" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#e1)"/>
  <line x1="400" y1="110" x2="475" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#e2)"/>

  <defs>
    <marker id="e1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="e2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Each matching entry's `Attributes` passes through the same mapper once, and the results accumulate into one `List<T>`.

## 5. Runnable example

The scenario: mapping directory entries into a simple `User` object, starting with the two required fields, then adding defensive handling for optional attributes, and finally mapping multi-valued attributes correctly.

### Level 1 — Basic

```java
// UserMapperBasic.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.core.AttributesMapper;

import javax.naming.directory.Attributes;
import java.util.List;

public class UserMapperBasic {
    record User(String uid, String email) {}

    public static void main(String[] args) throws Exception {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        AttributesMapper<User> mapper = attrs -> new User(
            (String) attrs.get("uid").get(),
            (String) attrs.get("mail").get()
        );

        List<User> users = template.search("ou=people", "(objectClass=inetOrgPerson)", mapper);
        users.forEach(System.out::println);
    }
}
```

**How to run:** run against a directory with several `inetOrgPerson` entries under `ou=people`, each with `uid` and `mail`. Expected output: one line per matching entry, e.g. `User[uid=jsmith, email=jsmith@example.com]`.

### Level 2 — Intermediate

Not every real entry has every attribute populated — a user without a `mail` attribute set makes `attrs.get("mail")` return `null`, and calling `.get()` on that throws a `NullPointerException`, crashing the whole search over one incomplete entry.

```java
// UserMapperSafe.java
import javax.naming.directory.Attribute;
import javax.naming.directory.Attributes;
import org.springframework.ldap.core.AttributesMapper;

public class UserMapperSafe {
    record User(String uid, String email) {}

    static String attrOrNull(Attributes attrs, String name) throws javax.naming.NamingException {
        Attribute attr = attrs.get(name);
        return attr == null ? null : (String) attr.get();
    }

    public static final AttributesMapper<User> MAPPER = attrs -> new User(
        attrOrNull(attrs, "uid"),
        attrOrNull(attrs, "mail")
    );
}
```

**How to run:** run a search over entries where some lack `mail`. Expected result: every entry maps successfully — those missing `mail` produce `User[uid=..., email=null]` instead of the whole search throwing a `NullPointerException` partway through and losing every result, including the ones that mapped fine.

### Level 3 — Advanced

Group membership entries commonly store multiple values in one attribute (e.g. `member` holding several DNs). Mapping only the first value silently drops data; production code needs to correctly extract every value from a multi-valued attribute.

```java
// GroupMapperMultiValued.java
import javax.naming.directory.Attribute;
import javax.naming.directory.Attributes;
import javax.naming.NamingEnumeration;
import org.springframework.ldap.core.AttributesMapper;

import java.util.ArrayList;
import java.util.List;

public class GroupMapperMultiValued {
    record Group(String cn, List<String> memberDns) {}

    public static final AttributesMapper<Group> MAPPER = attrs -> {
        String cn = (String) attrs.get("cn").get();
        List<String> members = new ArrayList<>();

        Attribute memberAttr = attrs.get("member");
        if (memberAttr != null) {
            NamingEnumeration<?> values = memberAttr.getAll(); // iterate ALL values, not just the first
            while (values.hasMore()) {
                members.add((String) values.next());
            }
        }
        return new Group(cn, members);
    };
}
```

**How to run:** search for a group entry (e.g. `(cn=engineering)`) that has multiple `member` values. Expected output: a `Group` whose `memberDns` list contains every member DN — commonly a mistake here is calling `.get()` (which returns only the first value of a multi-valued attribute), silently losing every member after the first; `.getAll()` iterated to completion avoids that.

## 6. Walkthrough

Tracing a `search` using `GroupMapperMultiValued.MAPPER` against a group with three members, in execution order:

1. `template.search("ou=groups", "(cn=engineering)", MAPPER)` sends the filtered search to the directory.
2. The server returns one matching entry for `cn=engineering`, whose `member` attribute internally holds three DN values.
3. `LdapTemplate` invokes the mapper once, passing this entry's `Attributes`.
4. `attrs.get("cn").get()` extracts the single-valued `cn` attribute's one value directly.
5. `attrs.get("member")` retrieves the multi-valued `member` attribute as an `Attribute` object — at this point no individual values have been read yet.
6. `memberAttr.getAll()` returns a `NamingEnumeration` over all three stored values; the `while (values.hasMore())` loop pulls each one out in turn and appends it to the `members` list.
7. The mapper returns a fully-populated `Group("engineering", [dn1, dn2, dn3])`.
8. `LdapTemplate` collects this one mapped `Group` into the returned `List<Group>` (a list of one element, since only one group entry matched the filter).

```
search("ou=groups", "(cn=engineering)", MAPPER)
  -> 1 matching entry, member attr holds [dn1, dn2, dn3]
  -> mapper: cn = "engineering"
  -> mapper: member.getAll() -> iterate -> [dn1, dn2, dn3]
  -> Group("engineering", [dn1, dn2, dn3])
  -> List<Group> = [ that one Group ]
```

## 7. Gotchas & takeaways

> Calling `.get()` on a multi-valued `Attribute` silently returns only its *first* value — no exception, no warning. This is a common, easy-to-miss bug: a group mapped this way looks correct in testing with a single-member test group, then silently drops members the moment a real group has more than one. Always use `.getAll()` (or `.size()` plus indexed access) for any attribute that can legitimately hold more than one value.

- `AttributesMapper` never sees the entry's own DN — only its attributes; use `ContextMapper` (card 0006) if the DN itself needs to be part of the mapped object.
- Any attribute that might be absent on a real entry needs a null check before calling `.get()` — don't assume every entry has every attribute your mapper expects.
- Multi-valued attributes (group membership, multiple phone numbers, multiple email aliases) require iterating with `.getAll()`, not a single `.get()` call.
- Because it's a functional interface, `AttributesMapper` lambdas are cheap to define inline for one-off mappings, but extracting a shared `static final` mapper (as in Level 2 and 3) avoids duplicating mapping logic across every call site that needs the same entry type.
- Exceptions thrown inside a mapper (a `NamingException` from a malformed attribute, for instance) propagate up through `LdapTemplate` and abort the entire search — one bad entry can fail an otherwise-successful search unless the mapper defensively handles missing or malformed attributes itself.
