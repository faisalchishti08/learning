---
card: spring-data
gi: 173
slug: spring-data-ldap-ldaprepository-entry
title: "Spring Data LDAP (LdapRepository, @Entry)"
---

## 1. What it is

Spring Data LDAP brings the repository pattern to LDAP directories (like Active Directory or OpenLDAP) — hierarchical stores of "entries" organized by distinguished name (DN), commonly used for user accounts, groups, and organizational structure. `@Entry` maps a Java class to an LDAP object class, and `LdapRepository` gives it the familiar generated-method-name treatment.

```java
@Entry(objectClasses = {"person", "top"}, base = "ou=customers")
class Customer {
    @Id Name dn;
    @Attribute(name = "cn") String fullName;
    @Attribute(name = "mail") String email;
}
```

## 2. Why & when

LDAP is a fundamentally different shape from every store covered so far: entries are organized in a strict tree hierarchy identified by distinguished names (`cn=Amara,ou=customers,dc=example,dc=com`), not by an arbitrary key or a flat collection. Most applications touch LDAP for exactly one purpose — reading (and occasionally writing) directory entries like user accounts — rather than as a general-purpose application database.

Reach for `LdapRepository`/`@Entry` when:

- Integrating with an existing corporate directory (user accounts, group membership) rather than modeling new application data.
- The natural identifier for an entry is its distinguished name (DN) — its position in the directory tree — rather than a surrogate key.
- You want simple, derived-style lookups against directory attributes (`findByUid`, `findByMail`) without hand-writing LDAP filter syntax.

## 3. Core concept

```
 dc=example,dc=com
   ou=customers
     cn=Amara,ou=customers,dc=example,dc=com    <- an "entry", identified by its DN
       objectClass: person, top
       cn: Amara
       mail: amara@example.com

 @Entry(objectClasses = {"person","top"}, base = "ou=customers")
 class Customer {
     @Id Name dn;                    -- the entry's position in the tree
     @Attribute(name = "cn") String fullName;
 }

 interface CustomerRepository extends LdapRepository<Customer> {
     List<Customer> findByFullName(String name);  -- derived, compiles to an LDAP filter
 }
```

An entry's identity is its DN — a path through the directory tree — not an arbitrary generated key, which is the core conceptual difference from every other Spring Data module in this course.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An LDAP directory tree with a customer entry nested under an organizational unit under a domain component">
  <rect x="250" y="15" width="140" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="37" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">dc=example,dc=com</text>

  <line x1="320" y1="50" x2="320" y2="80" stroke="#8b949e" stroke-width="1.3"/>

  <rect x="250" y="80" width="140" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="320" y="102" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ou=customers</text>

  <line x1="320" y1="115" x2="320" y2="145" stroke="#8b949e" stroke-width="1.3"/>

  <rect x="200" y="145" width="240" height="35" rx="6" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="167" fill="#e6edf3" font-size="8.2" text-anchor="middle" font-family="sans-serif">cn=Amara,ou=customers,dc=example,dc=com</text>
</svg>

An LDAP entry's identity is its full path through the directory tree — the distinguished name.

## 5. Runnable example

The scenario: managing customer entries in a directory tree, evolving from a basic `@Entry`-mapped lookup by DN, to a derived-method search by attribute, to a search combining an attribute filter with the entry's position in the tree — a concern with no equivalent in a flat store.

### Level 1 — Basic

Model a bare `@Entry` lookup by distinguished name against an in-memory stand-in for a directory.

```java
import java.util.*;

public class LdapLevel1 {
    public static void main(String[] args) {
        DirectoryStore store = new DirectoryStore();
        store.save(new Customer("cn=Amara,ou=customers,dc=example,dc=com", "Amara", "amara@example.com"));

        Customer found = store.findByDn("cn=Amara,ou=customers,dc=example,dc=com");
        System.out.println("Found: " + found.fullName + " <" + found.email + ">");
    }
}

// @Entry(objectClasses = {"person", "top"}, base = "ou=customers")
class Customer {
    // @Id
    String dn; // distinguished name -- the entry's identity, not a surrogate key
    // @Attribute(name = "cn")
    String fullName;
    // @Attribute(name = "mail")
    String email;
    Customer(String dn, String fullName, String email) { this.dn = dn; this.fullName = fullName; this.email = email; }
}

// Stands in for an LDAP directory accessed through Spring Data LDAP's LdapTemplate.
class DirectoryStore {
    private final Map<String, Customer> entries = new HashMap<>();
    void save(Customer c) { entries.put(c.dn, c); }
    Customer findByDn(String dn) { return entries.get(dn); }
}
```

How to run: `java LdapLevel1.java`

`findByDn` is the LDAP equivalent of `findById` in every earlier module, except the "id" here is a hierarchical path through the directory tree — `cn=Amara,ou=customers,dc=example,dc=com` — not an arbitrary key.

### Level 2 — Intermediate

Add a derived repository method that searches by attribute value, compiling to an LDAP filter.

```java
import java.util.*;
import java.util.stream.*;

public class LdapLevel2 {
    public static void main(String[] args) {
        CustomerRepository repo = new CustomerRepositoryImpl();
        repo.save(new Customer("cn=Amara,ou=customers,dc=example,dc=com", "Amara", "amara@example.com"));
        repo.save(new Customer("cn=Bilal,ou=customers,dc=example,dc=com", "Bilal", "bilal@example.com"));

        // derived -> LDAP filter: (&(objectClass=person)(mail=amara@example.com))
        List<Customer> matches = repo.findByEmail("amara@example.com");
        for (Customer c : matches) System.out.println("Matched: " + c.fullName);
    }
}

class Customer {
    String dn, fullName, email;
    Customer(String dn, String fullName, String email) { this.dn = dn; this.fullName = fullName; this.email = email; }
}

interface CustomerRepository {
    Customer save(Customer c);
    List<Customer> findByEmail(String email);
}

// Stands in for the Spring Data-generated LDAP-filter-backed implementation of an LdapRepository.
class CustomerRepositoryImpl implements CustomerRepository {
    private final Map<String, Customer> entries = new HashMap<>();
    public Customer save(Customer c) { entries.put(c.dn, c); return c; }
    public List<Customer> findByEmail(String email) {
        // Simulated LDAP filter: (&(objectClass=person)(mail=$email))
        return entries.values().stream().filter(c -> c.email.equals(email)).collect(Collectors.toList());
    }
}
```

How to run: `java LdapLevel2.java`

`findByEmail` derives to an LDAP search filter, `(&(objectClass=person)(mail=$email))` — Spring Data LDAP builds the filter syntax the same way derived methods build a Mongo filter or SQL `WHERE` clause elsewhere in this course, scoped automatically to the entry's `@Entry(base = ...)` subtree.

### Level 3 — Advanced

Search within a specific subtree of the directory *and* filter by attribute — combining structural position with content filtering, a concern unique to a hierarchical directory.

```java
import java.util.*;
import java.util.stream.*;

public class LdapLevel3 {
    public static void main(String[] args) {
        DirectoryStore store = new DirectoryStore();
        store.save(new Customer("cn=Amara,ou=customers,ou=lagos,dc=example,dc=com", "Amara", "person"));
        store.save(new Customer("cn=Bilal,ou=customers,ou=lagos,dc=example,dc=com", "Bilal", "person"));
        store.save(new Customer("cn=Chidi,ou=customers,ou=abuja,dc=example,dc=com", "Chidi", "person"));
        store.save(new Customer("cn=support-team,ou=groups,ou=lagos,dc=example,dc=com", "support-team", "group"));

        // Scoped search: only under ou=lagos, only objectClass=person -- structural AND content filter combined.
        List<Customer> lagosPeople = store.searchSubtree("ou=lagos", "person");
        for (Customer c : lagosPeople) System.out.println("Lagos person: " + c.fullName);
    }
}

class Customer {
    String dn, fullName, objectClass;
    Customer(String dn, String fullName, String objectClass) { this.dn = dn; this.fullName = fullName; this.objectClass = objectClass; }
}

class DirectoryStore {
    private final Map<String, Customer> entries = new HashMap<>();
    void save(Customer c) { entries.put(c.dn, c); }
    // Combines a subtree scope (structural: is the DN under this branch?) with an attribute filter.
    List<Customer> searchSubtree(String subtreeContains, String objectClass) {
        return entries.values().stream()
            .filter(c -> c.dn.contains(subtreeContains))
            .filter(c -> c.objectClass.equals(objectClass))
            .collect(Collectors.toList());
    }
}
```

How to run: `java LdapLevel3.java`

`searchSubtree` filters on two independent axes: the entry's *position* in the tree (is its DN under `ou=lagos`?) and its *content* (`objectClass=person`) — `support-team`, though also under `ou=lagos`, is excluded because it's a `group`, not a `person`; `Chidi` is excluded because he's under `ou=abuja`, not `ou=lagos`, even though he is a `person`.

## 6. Walkthrough

Execution starts in `main` for Level 3. Four entries are saved into the directory tree stand-in, spread across two organizational units (`ou=lagos`, `ou=abuja`) and two object classes (`person`, `group`). `store.searchSubtree("ou=lagos", "person")` runs the combined filter.

In a real LDAP search, this corresponds to setting the search base to `ou=lagos,dc=example,dc=com` (scoping *where* in the tree to search) and applying the filter `(objectClass=person)` (scoping *what* to match within that subtree) — LDAP servers are optimized to prune whole branches of the tree quickly based on the search base, before ever evaluating the attribute filter on individual entries:

```
Lagos person: Amara
Lagos person: Bilal
```

`Chidi` is excluded first, structurally — his DN never falls under `ou=lagos`, so the search base alone rules him out. `support-team` falls within the right subtree but is excluded by the `objectClass=person` filter. This two-stage narrowing — subtree first, attributes second — is the LDAP-specific reasoning that has no equivalent in a flat document or table-based store.

## 7. Gotchas & takeaways

> Gotcha: an entry's DN encodes its position in the tree — moving an entry to a different branch (e.g. reorganizing customers by region) means changing its DN, which most LDAP servers treat as a delete-and-recreate rather than a simple in-place update, unlike changing a foreign key in a relational table.

> Gotcha: `@Entry`'s `objectClasses` attribute must match exactly what the directory schema expects for that entry type — LDAP servers validate entries against their schema strictly, and a missing or extra `objectClass` value can cause writes to be rejected outright rather than silently accepted.

- LDAP entries are identified by distinguished name (DN) — a hierarchical path through the directory tree — not an arbitrary surrogate key, a genuinely different identity model from every other store in this course.
- `LdapRepository` supports the same derived-method-name pattern as other Spring Data modules, compiling to LDAP search filters instead of SQL, Mongo filters, or Cypher.
- Searches in LDAP combine a structural scope (which subtree to search) with a content filter (which attributes to match) — a two-axis search model unique to hierarchical directories.
- LDAP is typically used for existing directory integration (accounts, groups) rather than as a general-purpose application data store.
