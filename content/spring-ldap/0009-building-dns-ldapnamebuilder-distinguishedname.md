---
card: spring-ldap
gi: 9
slug: building-dns-ldapnamebuilder-distinguishedname
title: "Building DNs (LdapNameBuilder / DistinguishedName)"
---

## 1. What it is

A distinguished name (DN) is an LDAP entry's full address in the directory tree, made up of an ordered sequence of relative components (like `uid=jsmith,ou=people,dc=example,dc=com`). `LdapNameBuilder` is Spring LDAP's fluent, safe way to construct these programmatically, component by component, instead of concatenating strings by hand. It replaces the older `DistinguishedName` class from earlier Spring LDAP versions, which served the same purpose but with a slightly clunkier API.

## 2. Why & when

DNs look like simple strings, but they have real structural rules: components must be correctly escaped if they contain special characters (`,`, `+`, `"`, `\`, `<`, `>`, `;`, leading/trailing spaces), and the order of components matters — the most specific component comes first, the root of the tree comes last. Building a DN with plain string concatenation (`"uid=" + userInput + ",ou=people"`) is both a correctness risk (a `uid` value containing a comma silently breaks the structure) and, if `userInput` is attacker-controlled, an injection risk. `LdapNameBuilder` exists to build DNs correctly and safely, handling escaping and structure so calling code doesn't have to reimplement DN syntax rules.

Use `LdapNameBuilder` when:

- Constructing a DN from one or more dynamic values (a `uid`, an `ou` name) rather than a fixed, hardcoded string.
- Any of those dynamic values could plausibly contain characters with special meaning in DN syntax.
- Building DNs relative to a base that's already configured elsewhere (composing rather than duplicating the base).

## 3. Core concept

Think of a DN as a full postal address, read from the most specific part to the least specific — apartment number, then street, then city, then country — the reverse of how most people write addresses, but exactly how a DN is written: `uid=jsmith` (the apartment) comes before `ou=people` (the street) which comes before `dc=example,dc=com` (the country). `LdapNameBuilder` is like an address-formatting service that takes each part as a separate, clearly-labeled input and correctly assembles them into a valid address string, properly quoting or escaping any part that contains something unusual (a street name with a comma in it, for a real-world analogy).

```java
Name dn = LdapNameBuilder.newInstance("dc=example,dc=com")
    .add("ou", "people")
    .add("uid", "jsmith")
    .build();
// dn.toString() == "uid=jsmith,ou=people,dc=example,dc=com"
```

Components are added in root-to-leaf order via `.add(...)` calls, and `LdapNameBuilder` assembles them into the correct leaf-to-root DN string internally — callers don't need to remember to reverse the order themselves.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LdapNameBuilder assembles ordered components into a correctly formatted, escaped distinguished name">
  <rect x="20" y="30" width="590" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="60" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">.add("ou","people").add("uid","jsmith")</text>

  <line x1="315" y1="80" x2="315" y2="115" stroke="#3fb950" stroke-width="2" marker-end="url(#h1)"/>

  <rect x="20" y="120" width="590" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="150" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="monospace">uid=jsmith,ou=people,dc=example,dc=com</text>

  <defs>
    <marker id="h1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Components added root-to-leaf are assembled into the correct leaf-to-root DN string, with escaping handled automatically.

## 5. Runnable example

The scenario: building a DN for a user lookup, starting with a fixed base, then handling a `uid` value containing a special character, and finally building nested organizational-unit DNs dynamically for a multi-department directory.

### Level 1 — Basic

```java
// BuildBasicDn.java
import org.springframework.ldap.support.LdapNameBuilder;
import javax.naming.Name;

public class BuildBasicDn {
    public static void main(String[] args) {
        Name dn = LdapNameBuilder.newInstance("dc=example,dc=com")
            .add("ou", "people")
            .add("uid", "jsmith")
            .build();

        System.out.println("DN: " + dn);
    }
}
```

**How to run:** run with the Spring LDAP jars on the classpath: `java BuildBasicDn.java`. Expected output: `DN: uid=jsmith,ou=people,dc=example,dc=com`.

### Level 2 — Intermediate

A `uid` (or any component value) containing a comma — say, a display name used as a naming attribute, `"Smith, Jane"` — would corrupt a hand-concatenated DN string by introducing an unintended extra component boundary. `LdapNameBuilder` escapes it automatically.

```java
// BuildDnWithSpecialChars.java
import org.springframework.ldap.support.LdapNameBuilder;
import javax.naming.Name;

public class BuildDnWithSpecialChars {
    public static void main(String[] args) {
        String riskyCn = "Smith, Jane"; // contains a comma, a DN-structural character

        Name dn = LdapNameBuilder.newInstance("dc=example,dc=com")
            .add("ou", "people")
            .add("cn", riskyCn)
            .build();

        System.out.println("DN: " + dn);
        System.out.println("Component count: " + dn.size()); // should be 4, not 5
    }
}
```

**How to run:** run this program. Expected output: `DN: cn=Smith\, Jane,ou=people,dc=example,dc=com` (the comma is backslash-escaped within the `cn` value) and `Component count: 4` — proving the comma was correctly treated as part of the value, not as a component separator, unlike what naive string concatenation (`"cn=" + riskyCn + ",ou=people..."`) would have produced.

### Level 3 — Advanced

A directory organized by department needs DNs built dynamically from a variable-depth path (e.g. `ou=engineering,ou=departments`) followed by the actual entry. This level builds such nested DNs from a list of path segments plus a leaf component, validating segment values along the way.

```java
// NestedOuDnBuilder.java
import org.springframework.ldap.support.LdapNameBuilder;
import javax.naming.Name;
import java.util.List;

public class NestedOuDnBuilder {

    public static Name buildUserDn(String base, List<String> departmentPath, String uid) {
        LdapNameBuilder builder = LdapNameBuilder.newInstance(base);
        builder.add("ou", "departments");

        for (String segment : departmentPath) {
            if (segment == null || segment.isBlank()) {
                throw new IllegalArgumentException("Department path segment cannot be blank");
            }
            builder.add("ou", segment);
        }
        builder.add("uid", uid);
        return builder.build();
    }

    public static void main(String[] args) {
        Name dn = buildUserDn("dc=example,dc=com", List.of("engineering", "platform"), "jsmith");
        System.out.println("DN: " + dn);
    }
}
```

**How to run:** run `main`. Expected output: `DN: uid=jsmith,ou=platform,ou=engineering,ou=departments,dc=example,dc=com` — a four-level nested path built entirely from a `List<String>` plus the base and leaf component, with each `ou` segment individually escaped by `LdapNameBuilder` if it ever contained special characters. Calling `buildUserDn("dc=example,dc=com", List.of(""), "jsmith")` throws `IllegalArgumentException` for the blank segment before any DN is even attempted, catching a configuration mistake early rather than producing a malformed or misleading DN.

## 6. Walkthrough

Tracing `buildUserDn("dc=example,dc=com", List.of("engineering","platform"), "jsmith")`, in execution order:

1. `LdapNameBuilder.newInstance("dc=example,dc=com")` starts a builder anchored at the given base — nothing else has been added yet.
2. `.add("ou", "departments")` appends the first fixed structural component; internally the builder tracks this as the next-most-specific component relative to the base.
3. The loop iterates `departmentPath` in order (`"engineering"`, then `"platform"`), calling `.add("ou", segment)` for each — each call both validates the segment isn't blank and appends it, progressively narrowing the DN one organizational level at a time.
4. `.add("uid", "jsmith")` appends the final, most specific (leaf) component.
5. `.build()` assembles all the added components into a single `Name` object, internally reversing the accumulation order so the resulting DN reads most-specific-first (`uid=...` first) as DN syntax requires, even though components were *added* least-specific-to-most-specific in the code.
6. `dn.toString()` (invoked implicitly by string concatenation in `System.out.println`) renders the final DN string, with any component value needing escaping (as in Level 2) handled automatically at this stage.

```
add("ou","departments") -> add("ou","engineering") -> add("ou","platform") -> add("uid","jsmith")
   (accumulated root-to-leaf internally)
build() -> reverse to leaf-to-root DN string:
   "uid=jsmith,ou=platform,ou=engineering,ou=departments,dc=example,dc=com"
```

## 7. Gotchas & takeaways

> Building a DN with plain string concatenation is both a correctness bug waiting to happen and a potential injection vector — any dynamic value that ends up as a DN component (a `uid`, a department name, anything not a hardcoded literal) should go through `LdapNameBuilder.add(...)`, never through `"attr=" + value + ",..."` string building.

- Components are added in root-to-leaf (base-to-specific) order via repeated `.add(...)` calls; `LdapNameBuilder` handles reversing this internally to produce a correctly-ordered DN string.
- Special characters in a component value (`,`, `+`, `"`, `\`, leading/trailing spaces, and others) are automatically escaped — this is the main correctness and safety benefit over manual string concatenation.
- `LdapNameBuilder` is the modern replacement for the older `DistinguishedName` class; new code should prefer it, though `DistinguishedName` still appears in older Spring LDAP codebases.
- Validate dynamic path segments (as in Level 3) before adding them if blank or malformed segments would otherwise silently produce a DN that resolves to an unintended location in the tree.
- The resulting `Name` object (not just a raw `String`) is what `LdapTemplate` methods like `bind`, `lookup`, and `modifyAttributes` expect — building a `Name` directly, rather than a string later parsed into one, avoids an unnecessary round trip through string parsing.
