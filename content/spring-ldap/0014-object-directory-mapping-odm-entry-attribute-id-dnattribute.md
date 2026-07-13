---
card: spring-ldap
gi: 14
slug: object-directory-mapping-odm-entry-attribute-id-dnattribute
title: "Object-Directory Mapping (ODM) — @Entry, @Attribute, @Id, @DnAttribute"
---

## 1. What it is

Object-Directory Mapping (ODM) is Spring LDAP's declarative alternative to writing `AttributesMapper`/`ContextMapper` callbacks by hand (cards 0005–0006). Instead of manually pulling each attribute out of `Attributes`, you annotate a plain Java class with `@Entry` (declaring which object classes it represents) and annotate its fields with `@Id` (the entry's DN, as a `Name`), `@Attribute` (a mapped LDAP attribute), and `@DnAttribute` (a field that's both a DN component and, optionally, a regular attribute) — and `LdapTemplate` reads and writes instances of that class directly, generating the mapping automatically.

## 2. Why & when

Hand-written mappers work fine, but they mean writing (and keeping in sync) a small chunk of boilerplate for every entry type an application deals with — one lambda pulling out `uid`, another pulling out `mail`, repeated with minor variations across every domain type. ODM exists to eliminate that repetition: describe the shape of the mapping once, declaratively, on the domain class itself, and let Spring LDAP generate the equivalent of a hand-written `ContextMapper` automatically, for both reading and writing.

Reach for ODM when:

- A domain class maps fairly directly and consistently to one entry type (a `Person` class mapping to `inetOrgPerson` entries) with a small, stable set of attributes.
- Both reading and writing the same entry type are needed, and a single annotated class can serve both directions instead of maintaining a mapper and separate bind/modify logic.
- Reducing per-entry-type boilerplate across an application with several distinct entry types is worth the small amount of annotation-driven "magic" compared to fully explicit mapper code.

Hand-written mappers remain a better fit for unusual or highly conditional mapping logic (computed fields, complex multi-attribute derivations) that don't fit ODM's straightforward field-to-attribute model cleanly.

## 3. Core concept

Think of ODM like a shipping label template: instead of writing out a new label by hand for every single package (a hand-written mapper per entry type), you fill in a standard template once — this field is the recipient's name, this one's the street address, this one's the postal code — and the shipping system (Spring LDAP) automatically produces correctly formatted labels (mapped objects) for every package that matches the template, and can just as easily read an incoming label back into the same structured fields.

```java
import org.springframework.ldap.odm.annotations.*;
import javax.naming.Name;

@Entry(objectClasses = {"inetOrgPerson", "organizationalPerson", "person", "top"})
public class Person {

    @Id
    private Name dn;

    @Attribute(name = "uid")
    @DnAttribute(value = "uid", index = 0)
    private String uid;

    @Attribute(name = "cn")
    private String commonName;

    @Attribute(name = "sn")
    private String surname;

    @Attribute(name = "mail")
    private String email;

    // getters and setters omitted
}
```

- **`@Entry(objectClasses = {...})`** declares which LDAP object classes a bound instance of this class must satisfy — used both when reading (to help build the right search filter) and writing (to populate the `objectClass` attribute automatically).
- **`@Id`** marks the field holding the entry's DN, always typed as `javax.naming.Name`.
- **`@Attribute(name = "...")`** maps a field to a specific LDAP attribute by name.
- **`@DnAttribute`** marks a field that is also (or only) derived from a component of the DN itself, with `index` controlling its position when the DN is constructed for a new entry.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An annotated Person class maps directly to and from an LDAP entry's DN and attributes without a hand-written mapper">
  <rect x="20" y="30" width="230" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="135" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Entry class Person</text>
  <text x="135" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Id Name dn</text>
  <text x="135" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Attribute uid</text>
  <text x="135" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Attribute commonName</text>
  <text x="135" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Attribute email</text>

  <rect x="390" y="30" width="230" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="505" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">LDAP entry</text>
  <text x="505" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">dn: uid=jsmith,ou=people</text>
  <text x="505" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">uid: jsmith</text>
  <text x="505" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">cn: Jane Smith</text>
  <text x="505" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">mail: jsmith@example.com</text>

  <line x1="250" y1="80" x2="385" y2="80" stroke="#3fb950" stroke-width="2" marker-end="url(#k1)"/>
  <text x="315" y="70" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">write</text>
  <line x1="385" y1="130" x2="250" y2="130" stroke="#79c0ff" stroke-width="2" marker-end="url(#k2)"/>
  <text x="315" y="150" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">read</text>

  <defs>
    <marker id="k1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="k2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Annotations on the class describe the mapping in both directions — no separate mapper needed for reading versus writing.

## 5. Runnable example

The scenario: mapping a `Person` entry with ODM, starting with basic read/write, then adding a multi-valued attribute field, and finally handling a field whose DN component and attribute value must stay consistent under an update.

### Level 1 — Basic

```java
// Person.java
import org.springframework.ldap.odm.annotations.*;
import javax.naming.Name;

@Entry(objectClasses = {"inetOrgPerson", "organizationalPerson", "person", "top"})
public class Person {
    @Id
    private Name dn;

    @Attribute(name = "uid")
    @DnAttribute(value = "uid", index = 0)
    private String uid;

    @Attribute(name = "cn")
    private String commonName;

    @Attribute(name = "sn")
    private String surname;

    @Attribute(name = "mail")
    private String email;

    public Name getDn() { return dn; }
    public void setDn(Name dn) { this.dn = dn; }
    public String getUid() { return uid; }
    public void setUid(String uid) { this.uid = uid; }
    public String getCommonName() { return commonName; }
    public void setCommonName(String commonName) { this.commonName = commonName; }
    public String getSurname() { return surname; }
    public void setSurname(String surname) { this.surname = surname; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
}
```

```java
// OdmBasicDemo.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.core.support.LdapContextSource;
import org.springframework.ldap.support.LdapNameBuilder;

public class OdmBasicDemo {
    public static void main(String[] args) {
        LdapContextSource cs = new LdapContextSource();
        cs.setUrl("ldap://localhost:389");
        cs.setBase("dc=example,dc=com");
        cs.setUserDn("cn=admin,dc=example,dc=com");
        cs.setPassword("adminpass");
        cs.afterPropertiesSet();

        LdapTemplate template = new LdapTemplate(cs);

        Person p = new Person();
        p.setDn(LdapNameBuilder.newInstance("ou=people").add("uid", "jsmith").build());
        p.setUid("jsmith");
        p.setCommonName("Jane Smith");
        p.setSurname("Smith");
        p.setEmail("jsmith@example.com");

        template.create(p); // ODM equivalent of bind — objectClasses come from @Entry automatically

        Person fetched = template.findByDn(p.getDn(), Person.class);
        System.out.println("Fetched: " + fetched.getEmail());
    }
}
```

**How to run:** run against a writable directory. Expected output: `Fetched: jsmith@example.com` — the entry was created via `template.create(p)` (no manual `Attributes`/`objectClass` construction needed, unlike card 0007's raw `bind`) and read back via `findByDn`, both operating on the same annotated `Person` class.

### Level 2 — Intermediate

Real `inetOrgPerson` entries often carry multi-valued attributes, like several telephone numbers. ODM maps these directly to array or `List` fields.

```java
// PersonWithPhones.java (excerpt — extends the Level 1 class with one more field)
import org.springframework.ldap.odm.annotations.Attribute;

public class PersonWithPhones extends Person {
    @Attribute(name = "telephoneNumber")
    private String[] telephoneNumbers; // multi-valued attribute maps directly to an array field

    public String[] getTelephoneNumbers() { return telephoneNumbers; }
    public void setTelephoneNumbers(String[] telephoneNumbers) { this.telephoneNumbers = telephoneNumbers; }
}
```

**How to run:** set `telephoneNumbers` to `new String[]{"+1-555-0100", "+1-555-0101"}` before calling `template.create(...)`, then fetch it back with `template.findByDn(dn, PersonWithPhones.class)`. Expected result: `getTelephoneNumbers()` returns both values as a `String[]` of length 2 — ODM handles the multi-valued mapping automatically in both directions, unlike the manual `.getAll()` iteration a hand-written `AttributesMapper` would need (card 0005).

### Level 3 — Advanced

`uid` is both the naming attribute (part of the DN, via `@DnAttribute`) and a regular attribute value. Changing it after creation means the DN itself must change (a rename), not a simple attribute modification — attempting to just set a new `uid` value and calling `update` without renaming leaves the DN and the `uid` attribute inconsistent.

```java
// RenamePerson.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.support.LdapNameBuilder;
import javax.naming.Name;

public class RenamePerson {
    private final LdapTemplate template;

    public RenamePerson(LdapTemplate template) {
        this.template = template;
    }

    public void renameUid(Name currentDn, String newUid) {
        Person person = template.findByDn(currentDn, Person.class);

        Name newDn = LdapNameBuilder.newInstance("ou=people").add("uid", newUid).build();

        // ODM's update() cannot move an entry to a new DN by itself — an explicit rename is required
        // whenever the naming attribute (uid, via @DnAttribute) itself changes.
        template.rename(currentDn, newDn);

        person.setDn(newDn);
        person.setUid(newUid); // keep the in-memory object's attribute value consistent with its new DN
        template.update(person);
    }
}
```

**How to run:** call `renameUid(oldDn, "jsmith2")` on an existing `jsmith` entry. Expected result: the entry now exists at the new DN `uid=jsmith2,ou=people`, with its `uid` attribute also correctly reading `jsmith2` — both the DN and the `uid` attribute stay consistent because the rename and the attribute update were both performed explicitly, rather than assuming `update()` alone would relocate the entry.

## 6. Walkthrough

Tracing `renameUid(oldDn, "jsmith2")`, in execution order:

1. `template.findByDn(currentDn, Person.class)` reads the existing entry, populating a `Person` object whose `dn` and `uid` fields both still reflect the old value, `jsmith`.
2. `LdapNameBuilder` (card 0009) builds the new target DN, `uid=jsmith2,ou=people`.
3. `template.rename(currentDn, newDn)` sends an LDAP modify-DN operation to the server, physically relocating the entry from the old DN to the new one — this is a distinct LDAP operation from an attribute modification (card 0008), and it's the only way to change an entry's naming attribute.
4. After the rename, the entry now exists at `newDn`, but its `uid` attribute value (a regular attribute, separate from the DN itself in the underlying data even though `@DnAttribute` links them conceptually) may not have been automatically updated by the rename alone, depending on server behavior — the in-memory `person` object is updated explicitly to be sure.
5. `person.setDn(newDn)` and `person.setUid("jsmith2")` bring the in-memory object back in sync with the new reality.
6. `template.update(person)` writes any attribute-level changes (here, ensuring `uid` matches) to the entry now sitting at `newDn`.

```
renameUid(oldDn, "jsmith2")
  findByDn(oldDn) -> Person{dn=oldDn, uid="jsmith", ...}
  rename(oldDn, newDn)              [LDAP modify-DN: entry physically moves]
  person.setDn(newDn); person.setUid("jsmith2")   [keep object in sync]
  update(person)                    [ensure uid attribute matches new DN]
```

## 7. Gotchas & takeaways

> Renaming an entry whose naming attribute is mapped via `@DnAttribute` requires an explicit `rename()` call — `update()` alone does not relocate an entry to a new DN, even if the in-memory object's `@DnAttribute`-annotated field has changed. Skipping the explicit rename leaves the object pointing at a DN that either doesn't reflect the intended change or, worse, silently updates the wrong entry.

- ODM eliminates the need for hand-written `AttributesMapper`/`ContextMapper` callbacks for straightforward entry types, at the cost of some annotation-driven implicit behavior that's worth understanding, not just trusting blindly.
- `@Entry(objectClasses = {...})` should list every object class the entry actually needs, matching the schema's requirements (card 0007's `ObjectClassViolationException` risk applies here too if a required attribute has no corresponding mapped field with a value).
- Multi-valued LDAP attributes map cleanly to array or `List`-typed fields — no manual `.getAll()` iteration needed, unlike a hand-written `AttributesMapper`.
- A field marked `@DnAttribute` is both part of the DN and, typically, a regular attribute — changing its value on an existing entry requires an explicit `rename()`, not just an `update()`.
- ODM is a good fit for simple, table-like entry types; for entries needing complex conditional or computed mapping logic, a hand-written `ContextMapper` (card 0006) may stay clearer and more maintainable than forcing the shape into ODM's annotation model.
