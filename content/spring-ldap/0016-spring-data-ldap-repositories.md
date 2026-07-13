---
card: spring-ldap
gi: 16
slug: spring-data-ldap-repositories
title: "Spring Data LDAP repositories"
---

## 1. What it is

Spring Data LDAP layers the familiar Spring Data repository abstraction — the same `CrudRepository`/`LdapRepository` pattern used across Spring Data JPA, MongoDB, and others — on top of ODM-annotated entry classes (card 0014). Declaring an interface extending `LdapRepository<Person, Name>` gives an application `save`, `findAll`, `findById`, `delete`, and derived query methods (`findByUid`, `findBySurname`) for free, generated at startup, with zero hand-written implementation code.

## 2. Why & when

Even with ODM's `LdapTemplate.find*` methods (card 0015) removing the need for manual mappers, an application with several entry types still ends up writing a small, repetitive service class per type — one method to save, one to find by ID, one to find by some common attribute — largely boilerplate that looks nearly identical across types. Spring Data LDAP exists to remove that remaining boilerplate too, generating the implementation of a declared repository interface automatically, exactly the way Spring Data does for other stores, so a directory-backed entry type gets the same low-ceremony repository experience as a database-backed JPA entity.

Reach for a Spring Data LDAP repository when:

- An application already uses Spring Data patterns elsewhere (JPA, MongoDB) and wants LDAP-backed entries to feel consistent with the rest of the codebase.
- The access patterns for an entry type are simple CRUD plus a handful of attribute-based lookups — exactly what derived query methods handle well.
- Reducing repetitive save/find/delete boilerplate across several ODM entry types is worth the (very small) additional layer of framework convention over directly using `LdapTemplate`.

For unusual queries that don't fit the derived-method-name convention, a repository can still fall back to a custom method implemented with `LdapTemplate` directly, or plain `LdapTemplate` usage remains available alongside repositories in the same application.

## 3. Core concept

Think of a Spring Data LDAP repository like ordering a custom-printed form from a print shop: you specify the form's fields and a few standard fill-in-the-blank query types by name (`findByUid`, `findBySurnameStartingWith`) using the shop's naming convention, and the shop prints and hands you a fully working form (a generated repository implementation) — you never had to typeset it by hand. The repository interface is pure declaration; Spring Data LDAP generates a concrete class implementing it at application startup, deriving each method's LDAP query from its name.

```java
public interface PersonRepository extends LdapRepository<Person, Name> {
    Person findByUid(String uid);
    List<Person> findBySurname(String surname);
    List<Person> findByDepartmentNumberAndSurnameStartingWith(String dept, String prefix);
}
```

Enabling this requires one annotation on a configuration class:

```java
@Configuration
@EnableLdapRepositories(basePackages = "com.example.repository")
public class LdapRepositoryConfig { }
```

Once enabled, `PersonRepository` can be `@Autowired` anywhere and used immediately — `personRepository.save(person)`, `personRepository.findByUid("jsmith")` — with the actual `LdapTemplate` calls happening entirely inside the generated implementation.

## 4. Diagram

<svg viewBox="0 0 660 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A declared repository interface is implemented automatically at startup, translating method names into LdapTemplate calls against ODM-annotated entries">
  <rect x="20" y="30" width="200" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">interface PersonRepository</text>
  <text x="120" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">findByUid(String)</text>

  <rect x="280" y="30" width="180" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">generated impl</text>
  <text x="370" y="72" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(at startup)</text>

  <rect x="510" y="30" width="130" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="575" y="60" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">LdapTemplate</text>

  <line x1="220" y1="60" x2="275" y2="60" stroke="#3fb950" stroke-width="2" marker-end="url(#l1)"/>
  <line x1="460" y1="60" x2="505" y2="60" stroke="#3fb950" stroke-width="2" marker-end="url(#l2)"/>

  <defs>
    <marker id="l1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="l2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Only the interface is written; the implementation, backed by `LdapTemplate`, is generated automatically.

## 5. Runnable example

The scenario: a `PersonRepository` for the `Person` entry from card 0014, starting with basic CRUD, then a derived query method, and finally a custom method for a query too specific for name-derivation alone.

### Level 1 — Basic

```java
// PersonRepository.java
import org.springframework.data.ldap.repository.LdapRepository;
import javax.naming.Name;

public interface PersonRepository extends LdapRepository<Person, Name> {
}
```

```java
// RepoConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.data.ldap.repository.config.EnableLdapRepositories;

@Configuration
@EnableLdapRepositories(basePackages = "com.example")
public class RepoConfig { }
```

```java
// BasicRepoDemo.java
import org.springframework.ldap.support.LdapNameBuilder;

public class BasicRepoDemo {
    private final PersonRepository repo;

    public BasicRepoDemo(PersonRepository repo) {
        this.repo = repo;
    }

    public void run() {
        Person p = new Person();
        p.setDn(LdapNameBuilder.newInstance("ou=people").add("uid", "newperson").build());
        p.setUid("newperson");
        p.setCommonName("New Person");
        p.setSurname("Person");
        p.setEmail("newperson@example.com");

        repo.save(p); // generated implementation calls the ODM equivalent of bind/update

        long count = repo.count();
        System.out.println("Total people: " + count);
    }
}
```

**How to run:** run within a Spring context with `RepoConfig` active, connecting to a writable directory. Expected output: `Total people: N` reflecting the entry just saved plus any pre-existing ones — `save`, `count`, and the rest of `LdapRepository`'s base methods are available with zero implementation code written.

### Level 2 — Intermediate

Derived query methods let a repository interface declare a lookup purely by method name — Spring Data LDAP parses the method name and builds the equivalent `LdapQuery` automatically.

```java
// PersonRepositoryWithQueries.java
import org.springframework.data.ldap.repository.LdapRepository;
import javax.naming.Name;
import java.util.List;

public interface PersonRepositoryWithQueries extends LdapRepository<Person, Name> {
    Person findByUid(String uid);
    List<Person> findBySurnameStartingWith(String prefix);
}
```

**How to run:** call `repo.findByUid("jsmith")` — expect the single matching `Person`, equivalent to card 0015's `findOne` but with zero query-building code written. Call `repo.findBySurnameStartingWith("Sm")` — expect every `Person` whose surname starts with `Sm`, the method name alone (`findBySurnameStartingWith`) telling Spring Data LDAP to build a substring filter on `sn`.

### Level 3 — Advanced

Not every real query fits neatly into method-name derivation — a query needing custom scoping, sorting, or pagination (card 0012) benefits from an explicit implementation. Repositories support this via a custom fragment interface backed by a hand-written implementation class that still plugs into the same repository.

```java
// PersonRepositoryCustom.java
import java.util.List;

public interface PersonRepositoryCustom {
    List<Person> findActiveInDepartmentPaged(String departmentNumber, int pageSize);
}
```

```java
// PersonRepositoryCustomImpl.java
import org.springframework.ldap.core.LdapTemplate;
import org.springframework.ldap.control.PagedResultsDirContextProcessor;
import static org.springframework.ldap.query.LdapQueryBuilder.query;

import java.util.List;

public class PersonRepositoryCustomImpl implements PersonRepositoryCustom {
    private final LdapTemplate template; // injected directly for the custom, non-derivable query

    public PersonRepositoryCustomImpl(LdapTemplate template) {
        this.template = template;
    }

    @Override
    public List<Person> findActiveInDepartmentPaged(String departmentNumber, int pageSize) {
        var ldapQuery = query()
            .base("ou=people")
            .where("departmentNumber").is(departmentNumber)
            .and("employeeStatus").is("active");

        PagedResultsDirContextProcessor pager = new PagedResultsDirContextProcessor(pageSize);
        return template.find(ldapQuery, Person.class); // first page only, illustrating the custom hook
    }
}
```

```java
// PersonRepository.java — extended to combine derived methods AND the custom fragment
public interface PersonRepository extends LdapRepository<Person, Name>, PersonRepositoryCustom {
    Person findByUid(String uid);
}
```

**How to run:** with `PersonRepositoryCustomImpl` registered as a Spring bean named `personRepositoryCustomImpl` (matching Spring Data's naming convention for custom fragments — the repository interface name plus `Impl`), calling `repo.findActiveInDepartmentPaged("4120", 50)` and `repo.findByUid("jsmith")` both work through the *same* `repo` object — one derived automatically, one backed by explicit `LdapTemplate` code — demonstrating that custom and derived methods coexist on a single repository interface.

## 6. Walkthrough

Tracing `repo.findByUid("jsmith")` on `PersonRepository`, in execution order:

1. At application startup, `@EnableLdapRepositories` scans the configured base package, finds the `PersonRepository` interface, and generates a proxy implementation for it — this happens once, before any repository method is ever called.
2. Part of that generation involves parsing each declared method name; `findByUid(String uid)` is recognized as a derived query on the `uid` property, and an equivalent `LdapQuery` (as if hand-built via `LdapQueryBuilder`, card 0010) is prepared for it.
3. At runtime, calling `repo.findByUid("jsmith")` invokes the generated proxy method, which constructs the actual query (filtering on `uid=jsmith`) and delegates to the underlying `LdapTemplate`'s ODM-aware `findOne` (card 0015).
4. `LdapTemplate` performs the search exactly as described in earlier cards — obtaining a context from the configured `ContextSource`, running the JNDI search, mapping the one matching entry into a `Person` via its ODM annotations.
5. The mapped `Person` object is returned directly from `repo.findByUid(...)`, indistinguishable from what a hand-written service method would have produced, but with none of the query-building or mapping code written explicitly anywhere in `PersonRepository` or its (nonexistent, for this method) implementation.

```
startup: @EnableLdapRepositories scans -> finds PersonRepository -> generates proxy impl
         (parses "findByUid" -> derives query on 'uid' property)

runtime: repo.findByUid("jsmith")
   -> generated proxy builds LdapQuery(uid=jsmith)
   -> delegates to LdapTemplate.findOne(query, Person.class)   [as in card 0015]
   -> returns mapped Person
```

## 7. Gotchas & takeaways

> Custom repository fragment implementations must follow Spring Data's naming convention exactly — the implementation class name must be the repository interface's name plus `Impl` (here, `PersonRepositoryCustomImpl` implementing `PersonRepositoryCustom`, combined into `PersonRepository`) — or Spring Data silently fails to wire it in, and calling the custom method throws a "no property found" or similar startup/method-resolution error that can be confusing to trace back to a simple naming mismatch.

- Derived query methods are parsed from the method name at startup — a typo in a property name (`findBySurmane` instead of `findBySurname`) fails fast at application startup with a clear error, rather than compiling silently and failing at runtime.
- Repositories are built on top of the same ODM annotations (card 0014) used by `LdapTemplate.find*` (card 0015) — there's no separate mapping concept to learn, only a different, more declarative way to invoke the same underlying mapping.
- For queries too complex or specific for name derivation, a custom fragment interface plus implementation (Level 3) lets hand-written `LdapTemplate` code coexist on the same repository as fully derived methods.
- `@EnableLdapRepositories` needs to scan the correct base package containing the repository interfaces — an interface outside the scanned package is silently not picked up, with no repository bean created for it and a startup failure only when something tries to autowire it.
- Choosing between plain `LdapTemplate`, ODM's `find*` methods, and full Spring Data repositories is a spectrum of decreasing boilerplate and increasing convention — pick based on how much of an application's LDAP access fits the simple CRUD-plus-derived-query mold versus needing bespoke query logic.
