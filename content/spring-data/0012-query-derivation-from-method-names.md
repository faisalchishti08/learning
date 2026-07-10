---
card: spring-data
gi: 12
slug: query-derivation-from-method-names
title: "Query derivation from method names"
---

## 1. What it is

Query derivation is the mechanism, referenced throughout this section, by which Spring Data turns a repository method's *name* into a real query — no annotation, no query string, no implementation body. `findByLastNameAndFirstName`, `findByAgeGreaterThan`, `findByEmailContainingIgnoreCase`, `countByStatus` — each of these method names is parsed by Spring Data's `PartTree` parser into a structured description of properties to match, comparison operators to use, and an aggregate/action to perform, which is then translated into a real query against whatever store the repository targets.

```java
public interface CustomerRepository extends JpaRepository<Customer, Long> {
    List<Customer> findByLastNameAndFirstName(String lastName, String firstName);
    List<Customer> findByAgeGreaterThanEqual(int minAge);
    long countByStatus(String status);
    boolean existsByEmail(String email);
}
```

## 2. Why & when

Every card in this section has used derived queries without fully explaining the naming rules behind them — this card is where those rules get made explicit. Query derivation exists because a huge fraction of real-world queries are simple property comparisons (`WHERE lastName = ?`, `WHERE age >= ?`, `WHERE email LIKE '%?%'`) that don't need the expressiveness of hand-written SQL or JPQL — encoding them directly in the method name keeps the query, its parameters, and its intent all visible in one place, with no separate query string to keep in sync with the method signature.

Understanding the naming rules matters specifically when:

- You're writing a new finder method and want Spring Data to generate it automatically rather than reaching for `@Query` — knowing the supported keywords (`And`, `Or`, `Between`, `LessThan`, `IsNull`, `Containing`, `OrderBy`, and more) tells you what's actually expressible this way.
- You're debugging a startup failure about an unresolvable property or an invalid query derivation — these errors happen precisely because a method name doesn't match any real entity property, or uses a keyword combination `PartTree` can't parse; understanding the naming grammar makes these errors immediately diagnosable.
- You're deciding whether a query is simple enough for derivation or complex enough to need `@Query` — as a rule of thumb, once a method name accumulates more than two or three conditions, or needs a join, subquery, or custom projection, `@Query` becomes more readable than an increasingly long derived method name.

## 3. Core concept

```
 Method name structure:  <verb><By><Property1><Op1?><And/Or><Property2><Op2?>...

 VERBS (what kind of query):
   findBy / getBy / queryBy / readBy   -- SELECT, returns entities
   countBy                              -- SELECT COUNT(*)
   existsBy                             -- SELECT ... exists check, returns boolean
   deleteBy / removeBy                  -- DELETE

 PROPERTIES: must match a real property on the entity (including nested,
   via "OrderAddressCity" for order.address.city)

 COMBINING: And, Or  -- e.g. findByLastNameAndFirstName

 COMPARISON KEYWORDS (appended after a property):
   (none)            -- equals               GreaterThan / LessThan / Between
   IsNull / IsNotNull                          Like / NotLike / Containing / StartingWith / EndingWith
   In / NotIn                                  True / False
   IgnoreCase (modifier, e.g. ContainingIgnoreCase)

 RESULT MODIFIERS:
   OrderBy<Property><Asc/Desc>          -- e.g. findByStatusOrderByCreatedAtDesc
   First<N> / Top<N>                    -- e.g. findTop5ByStatusOrderByCreatedAtDesc
```

`PartTree` parses this structure at repository-proxy-creation time (startup), not on every call — an invalid method name fails fast, before the application even finishes starting.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A derived method name is parsed into verb, properties, operators, and combinators, then translated into a real query">
  <rect x="10" y="20" width="620" height="45" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">findByLastNameAndAgeGreaterThanOrderByLastNameAsc</text>

  <rect x="10" y="100" width="140" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="80" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">verb: findBy</text>

  <rect x="165" y="100" width="150" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="240" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">lastName = ?, age &gt; ?</text>

  <rect x="330" y="100" width="140" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="400" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">combined with AND</text>

  <rect x="485" y="100" width="145" height="45" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="557" y="127" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">ORDER BY lastName ASC</text>

  <line x1="320" y1="65" x2="320" y2="95" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every segment of the method name maps to one piece of the generated query's structure.

## 5. Runnable example

The scenario: an `Employee` search repository, evolving from basic property matching, to comparison operators combined with `And`/`Or`, to a full set of advanced keywords (`Containing`, `OrderBy`, `Top`, `IgnoreCase`) working together on one realistic search method.

### Level 1 — Basic

Declare `findByDepartment` and `findByDepartmentAndActive` — the simplest equality and `And`-combined derivations.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class QueryDerivationLevel1 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String department;
        private boolean active;
        protected Employee() {}
        public Employee(String name, String department, boolean active) {
            this.name = name; this.department = department; this.active = active;
        }
        public String getName() { return name; }
        public String getDepartment() { return department; }
        public boolean isActive() { return active; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        List<Employee> findByDepartment(String department);
        List<Employee> findByDepartmentAndActive(String department, boolean active);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryDerivationLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:qd1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Ada", "Engineering", true));
        repo.save(new Employee("Grace", "Engineering", false));
        repo.save(new Employee("Katherine", "Research", true));

        List<Employee> engineering = repo.findByDepartment("Engineering");
        List<Employee> activeEngineering = repo.findByDepartmentAndActive("Engineering", true);

        System.out.println("Engineering dept = " + engineering.size());
        System.out.println("active Engineering = " + activeEngineering.size());

        if (engineering.size() != 2) throw new AssertionError("Expected 2 Engineering employees");
        if (activeEngineering.size() != 1) throw new AssertionError("Expected 1 active Engineering employee");
        System.out.println("Simple equality and And-combined derivation both worked -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java QueryDerivationLevel1.java` on JDK 17+.

`findByDepartment(String department)` parses as `WHERE department = ?1`. `findByDepartmentAndActive(String department, boolean active)` parses as `WHERE department = ?1 AND active = ?2` — the method's parameters are bound to the query's placeholders strictly in the order they appear in both the method name and the parameter list.

### Level 2 — Intermediate

Use comparison keywords (`GreaterThan`, `Between`) and `Or` combination, and add `OrderBy` for deterministic result ordering.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class QueryDerivationLevel2 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private int yearsOfService;
        protected Employee() {}
        public Employee(String name, int yearsOfService) { this.name = name; this.yearsOfService = yearsOfService; }
        public String getName() { return name; }
        public int getYearsOfService() { return yearsOfService; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        List<Employee> findByYearsOfServiceGreaterThanEqual(int minYears);
        List<Employee> findByYearsOfServiceBetween(int min, int max);
        List<Employee> findByNameOrYearsOfServiceGreaterThan(String name, int minYears);
        List<Employee> findAllByOrderByYearsOfServiceDesc();
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryDerivationLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:qd2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Ada", 12));
        repo.save(new Employee("Grace", 3));
        repo.save(new Employee("Katherine", 8));
        repo.save(new Employee("Margaret", 20));

        List<Employee> veterans = repo.findByYearsOfServiceGreaterThanEqual(10);
        List<Employee> midCareer = repo.findByYearsOfServiceBetween(5, 15);
        List<Employee> nameOrVeteran = repo.findByNameOrYearsOfServiceGreaterThan("Grace", 15);
        List<Employee> byYearsDesc = repo.findAllByOrderByYearsOfServiceDesc();

        System.out.println("veterans (>=10y) = " + veterans.size());
        System.out.println("mid-career (5-15y) = " + midCareer.size());
        System.out.println("named Grace OR >15y = " + nameOrVeteran.size());
        System.out.println("all ordered by years desc = " + byYearsDesc.stream().map(Employee::getYearsOfService).toList());

        if (veterans.size() != 2) throw new AssertionError("Expected 2 employees with >=10 years");
        if (midCareer.size() != 2) throw new AssertionError("Expected 2 employees with 5-15 years");
        if (nameOrVeteran.size() != 2) throw new AssertionError("Expected Grace + Margaret (>15y)");
        if (!byYearsDesc.get(0).getName().equals("Margaret")) throw new AssertionError("Expected Margaret (20y) first");

        System.out.println("GreaterThanEqual, Between, Or, and OrderBy all derived correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java QueryDerivationLevel2.java`.

`findByYearsOfServiceBetween(int min, int max)` parses as `WHERE yearsOfService BETWEEN ?1 AND ?2`. `findByNameOrYearsOfServiceGreaterThan(String name, int minYears)` parses as `WHERE name = ?1 OR yearsOfService > ?2` — matching `Grace` (by name) and `Margaret` (20 years, greater than 15), even though neither condition alone would match both. `findAllByOrderByYearsOfServiceDesc()` has no `By`-clause conditions at all (just `findAllBy` followed directly by `OrderBy`), retrieving every row sorted descending by years of service.

### Level 3 — Advanced

Combine `Containing`, `IgnoreCase`, `Top`, and `OrderBy` in one realistic search method — the kind of derived query a real search-box feature would use — alongside `existsBy` and `countBy` for cheap existence and aggregate checks.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class QueryDerivationLevel3 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private String department;
        private int yearsOfService;
        protected Employee() {}
        public Employee(String name, String department, int yearsOfService) {
            this.name = name; this.department = department; this.yearsOfService = yearsOfService;
        }
        public String getName() { return name; }
        public String getDepartment() { return department; }
        public int getYearsOfService() { return yearsOfService; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        // A realistic "search box" query: case-insensitive substring match on name,
        // top 3 results, most senior first.
        List<Employee> findTop3ByNameContainingIgnoreCaseOrderByYearsOfServiceDesc(String namePart);

        boolean existsByDepartmentAndYearsOfServiceGreaterThan(String department, int minYears);
        long countByDepartment(String department);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(QueryDerivationLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:qd3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Ada Lovelace", "Engineering", 12));
        repo.save(new Employee("Grace Hopper", "Engineering", 25));
        repo.save(new Employee("Katherine Johnson", "Research", 30));
        repo.save(new Employee("Margaret Hamilton", "Engineering", 15));
        repo.save(new Employee("ADA Byron", "Research", 5)); // case-differing name, contains "ada"

        List<Employee> topAdaMatches = repo.findTop3ByNameContainingIgnoreCaseOrderByYearsOfServiceDesc("ada");
        System.out.println("top matches for 'ada' (case-insensitive) = "
            + topAdaMatches.stream().map(Employee::getName).toList());

        boolean hasVeteranEngineer = repo.existsByDepartmentAndYearsOfServiceGreaterThan("Engineering", 20);
        long engineeringCount = repo.countByDepartment("Engineering");

        System.out.println("has a veteran (>20y) engineer? " + hasVeteranEngineer);
        System.out.println("Engineering headcount = " + engineeringCount);

        if (topAdaMatches.size() != 2) throw new AssertionError("Expected 2 matches for 'ada' (Ada Lovelace, ADA Byron)");
        if (!topAdaMatches.get(0).getName().equals("Ada Lovelace"))
            throw new AssertionError("Expected the more senior 'Ada' match first (12y > 5y)");
        if (!hasVeteranEngineer) throw new AssertionError("Expected Grace Hopper (25y, Engineering) to satisfy this");
        if (engineeringCount != 3) throw new AssertionError("Expected 3 Engineering employees");

        System.out.println("Containing + IgnoreCase + Top + OrderBy + existsBy + countBy all derived correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java QueryDerivationLevel3.java`.

`findTop3ByNameContainingIgnoreCaseOrderByYearsOfServiceDesc(String namePart)` parses as: limit to 3 results (`Top3`), where `name` contains `namePart` case-insensitively (`ContainingIgnoreCase`, translating to something like `LOWER(name) LIKE LOWER('%' || ?1 || '%')`), ordered by `yearsOfService` descending. Both `"Ada Lovelace"` and `"ADA Byron"` match `"ada"` despite the case difference, and `"Ada Lovelace"` (12 years) sorts before `"ADA Byron"` (5 years) per the descending order. `existsByDepartmentAndYearsOfServiceGreaterThan` returns a `boolean` from an efficient existence check rather than materializing matching rows, and `countByDepartment` returns a `long` from a `COUNT` query — both avoiding the cost of fetching full entities when only a boolean or a number is actually needed.

## 6. Walkthrough

Trace how `findTop3ByNameContainingIgnoreCaseOrderByYearsOfServiceDesc` gets built and executed.

1. **Startup — `PartTree` parsing**: when the `EmployeeRepository` proxy is generated, Spring Data's `PartTree` parser tokenizes the method name into segments: `Top3` (a limiting modifier), `By` (the boundary marking where conditions begin), `NameContainingIgnoreCase` (one condition: property `name`, operator `Containing`, modifier `IgnoreCase`), `OrderByYearsOfServiceDesc` (a sort instruction).
2. **Property validation**: for each recognized property token (`name`, `yearsOfService`), `PartTree` checks it exists on the `Employee` entity's metadata — if a property name didn't match (a typo, for instance), this step is where the startup failure would occur, before the application finishes booting.
3. **Query template generation**: Spring Data JPA translates the parsed structure into a JPQL query template equivalent to `SELECT e FROM Employee e WHERE LOWER(e.name) LIKE LOWER(CONCAT('%', ?1, '%')) ORDER BY e.yearsOfService DESC`, with a `LIMIT 3` (or the JPA equivalent, `setMaxResults(3)`) applied from the `Top3` modifier — this template is built once, at startup, and reused for every call.
4. **Call time**: `repo.findTop3ByNameContainingIgnoreCaseOrderByYearsOfServiceDesc("ada")` binds `"ada"` as the query's parameter and executes the pre-built template against H2.
5. **Database execution**: H2 evaluates the case-insensitive `LIKE` condition against all 5 employees, finds 2 matches (`"Ada Lovelace"`, `"ADA Byron"`), sorts them by `yearsOfService` descending (12 before 5), and returns at most 3 rows (here, exactly 2, since fewer than 3 matched).
6. **Result mapping**: Hibernate maps the returned rows into `Employee` entity instances, assembled into a `List<Employee>` — the method's declared return type.
7. **Verification**: the program checks the match count, confirms the more senior "Ada" match sorts first, then separately exercises `existsByDepartmentAndYearsOfServiceGreaterThan` (confirming a boolean-returning existence check) and `countByDepartment` (confirming a long-returning aggregate), printing `PASS` only if every derived query behaved exactly as its method name specified.

```
 findTop3ByNameContainingIgnoreCaseOrderByYearsOfServiceDesc("ada")
        |
        v
 PartTree (parsed at startup): Top3 | name CONTAINING IGNORE_CASE | ORDER BY yearsOfService DESC
        |
        v
 JPQL: SELECT e FROM Employee e
       WHERE LOWER(e.name) LIKE LOWER('%ada%')
       ORDER BY e.yearsOfService DESC   (LIMIT 3)
        |
        v
 2 matches: Ada Lovelace (12y), ADA Byron (5y) -- in that order
```

## 7. Gotchas & takeaways

> **Gotcha:** a derived method name that references a property Spring Data can't resolve — a typo, or a property that genuinely doesn't exist on the entity — fails at *application startup*, with an error naming the exact method and the unresolvable property, not at the first call to that method. This is a deliberate design choice (fail fast, before the application even finishes booting) but can be surprising if you expect the error to surface only when the broken method is actually invoked.

- Query derivation parses a method name into a structured query at repository-proxy-creation time (startup), using the `PartTree` parser — the same mechanism underlies every derived-query example used throughout this section.
- The supported keyword vocabulary — comparison operators (`GreaterThan`, `Between`, `Like`, `In`, `IsNull`), combinators (`And`, `Or`), modifiers (`IgnoreCase`), and result-shaping (`OrderBy`, `Top`/`First`) — covers the large majority of everyday query needs without writing a single line of query syntax.
- `existsBy` and `countBy` return `boolean`/`long` respectively from efficient existence/count queries, avoiding the cost of fetching and mapping full entities when only a yes/no or a number is actually needed.
- Once a query needs a join, a subquery, a custom projection, or simply accumulates enough conditions that the method name becomes hard to read, `@Query` (with a hand-written JPQL or native SQL string) is the more maintainable choice — query derivation is a tool for the common, simple case, not a replacement for every possible query.
