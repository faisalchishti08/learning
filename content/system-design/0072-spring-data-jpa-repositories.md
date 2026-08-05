---
card: system-design
gi: 72
slug: spring-data-jpa-repositories
title: "Spring Data JPA & repositories"
---

## 1. What it is

**Spring Data JPA** lets you define a data-access layer by writing a Java interface — a **repository** — and having Spring generate a working implementation for it at startup. Methods like `save`, `findById`, and `deleteById` come for free from a base interface; custom queries can often be declared just by naming a method correctly (`findByEmail`), with no SQL written at all.

## 2. Why & when

Writing a Data Access Object (DAO) by hand for every entity means repeating the same boilerplate — open a connection, write SQL, map result rows to objects, close the connection — for every single table. Spring Data JPA removes nearly all of that boilerplate: you declare *what* data access you need as an interface method signature, and Spring generates the implementation using JPA (the Java Persistence API) and Hibernate underneath. Use it for any Spring application backed by a relational database; it is the standard default in the Spring ecosystem.

## 3. Core concept

**Extending a base repository interface:**

```java
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email); // no implementation needed
    List<User> findByLastNameOrderByFirstNameAsc(String lastName);
}
```

`JpaRepository<User, Long>` already provides `save`, `findById`, `findAll`, `deleteById`, and more, all backed by real SQL that Spring Data JPA generates and executes via Hibernate.

**Derived query methods:** `findByEmail(String email)` needs no implementation, no `@Query` annotation, and no SQL — Spring parses the method *name* itself (`findBy` + `Email`) and generates a query equivalent to `SELECT * FROM users WHERE email = ?`. More complex names like `findByLastNameOrderByFirstNameAsc` are parsed the same way, generating a query with both a `WHERE` and an `ORDER BY` clause.

**`@Query` for anything the naming convention cannot express:** for queries too complex for a derived method name (multi-table joins with custom conditions, aggregates), `@Query("SELECT u FROM User u WHERE u.age > :minAge")` lets you write JPQL (or native SQL) directly, still returned as typed Java objects.

**How the interface becomes a real bean:** at startup, Spring scans for interfaces extending `JpaRepository` and generates a dynamic proxy implementing every method — both the inherited base methods and your derived query methods — then registers that proxy as a Spring bean, ready to `@Autowired` into a service.

## 4. Diagram

```
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
}
              |
              | at Spring Boot startup: scanned, PROXY generated
              v
   UserRepository bean (a dynamically generated implementation)
              |
   userRepository.findByEmail("a@x.com")
              |
              v
   Spring Data JPA parses the method NAME "findByEmail"
              |
              v
   generates: SELECT u FROM User u WHERE u.email = ?1
              |
              v
   Hibernate executes it, maps the result row(s) back to a User object
```
*Caption: the interface is never manually implemented; Spring generates a working proxy from its method signatures at startup.*

## 5. Runnable example

### Artifact: a minimal Java sketch modeling how derived query methods are parsed and executed

```java
import java.util.*;
import java.util.function.Predicate;

public class SpringDataJpaSim {

    record User(Long id, String email, String lastName, String firstName) {}

    // Simulates Hibernate/JDBC underneath the generated repository proxy.
    static final List<User> table = new ArrayList<>();

    // Simulates what Spring Data JPA generates for a method NAME like "findByEmail".
    static Optional<User> findByField(Predicate<User> matcher) {
        return table.stream().filter(matcher).findFirst();
    }

    static List<User> findAllByField(Predicate<User> matcher, Comparator<User> order) {
        return table.stream().filter(matcher).sorted(order).toList();
    }

    // The "repository interface" methods, implemented here directly to show what the
    // generated proxy would actually do for each method name.
    static Optional<User> findByEmail(String email) {
        return findByField(u -> u.email().equals(email)); // parsed from "findBy" + "Email"
    }

    static List<User> findByLastNameOrderByFirstNameAsc(String lastName) {
        return findAllByField(
            u -> u.lastName().equals(lastName), // parsed from "findBy" + "LastName"
            Comparator.comparing(User::firstName) // parsed from "OrderBy" + "FirstName" + "Asc"
        );
    }

    public static void main(String[] args) {
        table.add(new User(1L, "amy@x.com", "Chen", "Amy"));
        table.add(new User(2L, "bob@x.com", "Chen", "Zack"));
        table.add(new User(3L, "cid@x.com", "Diaz", "Cid"));

        System.out.println("findByEmail(\"bob@x.com\"): " + findByEmail("bob@x.com"));
        System.out.println("findByEmail(\"missing@x.com\"): " + findByEmail("missing@x.com"));

        System.out.println("findByLastNameOrderByFirstNameAsc(\"Chen\"):");
        for (User u : findByLastNameOrderByFirstNameAsc("Chen")) {
            System.out.println("  " + u.firstName() + " " + u.lastName());
        }
    }
}
```

**How to run:** save as `SpringDataJpaSim.java`, run `java SpringDataJpaSim.java` (JDK 17+). A real Spring Boot app needs the `spring-boot-starter-data-jpa` dependency and an `@Entity`-annotated `User` class; the repository interface itself needs no implementation code at all.

## 6. Walkthrough

1. `findByEmail("bob@x.com")` filters `table` for a matching `email`, returning `Optional[User[id=2, ...]]` — mirroring the SQL `SELECT * FROM users WHERE email = 'bob@x.com'` that Spring Data JPA would generate from the method name alone.
2. `findByEmail("missing@x.com")` finds nothing and returns an empty `Optional` — mirroring a real repository's `findByEmail` returning `Optional.empty()` when no row matches, rather than throwing an exception.
3. `findByLastNameOrderByFirstNameAsc("Chen")` filters for `lastName equals "Chen"` (matching both Amy and Zack Chen) and sorts the results by `firstName` ascending — mirroring `SELECT * FROM users WHERE last_name = 'Chen' ORDER BY first_name ASC`.
4. The printed output shows `Amy Chen` before `Zack Chen`, confirming the derived sort order was applied correctly, exactly as it would be parsed from the two-part method name suffix `OrderByFirstNameAsc`.

## 7. Gotchas & takeaways

> **Gotcha:** derived query method names must exactly match your entity's field names (`findByLastName` requires a field literally named `lastName`); a typo or a renamed field breaks the method at application startup, not silently at runtime — Spring validates every repository method's name against the entity when the application context loads.

- Spring Data JPA eliminates boilerplate DAO code by generating a repository's implementation from an interface's method signatures at startup.
- Simple filtering and sorting can be expressed entirely through method naming conventions; anything more complex should use `@Query` with JPQL or native SQL.
- Related concepts: [Query planning & the N+1 problem](0067-query-planning-the-n-1-problem.md) (a common pitfall when a repository's derived methods trigger lazy-loaded associations in a loop), [@Transactional & declarative transaction management](0073-transactional-declarative-transaction-management.md) (how repository writes are wrapped in a transaction).
