---
card: spring-data
gi: 51
slug: param
title: "@Param"
---

## 1. What it is

`@Param` is the annotation that links a repository method parameter to a named binding marker (`:paramName`) in a `@Query` string — this card focuses specifically on the annotation itself: its one attribute (the name), the alternative of relying on the `-parameters` compiler flag instead of `@Param` entirely, and how `@Param` interacts with collection-typed parameters used in `IN` clauses.

```java
@Query("select c from Customer c where c.email = :email")
Optional<Customer> findByEmailParam(@Param("email") String email);
```

## 2. Why & when

The previous card established *why* named parameters are generally safer than positional ones — `@Param` is the mechanism that makes named binding possible at all when a method's actual parameter names aren't preserved in the compiled bytecode by default (Java historically erased parameter names unless compiled with a specific flag). Understanding `@Param` specifically — including the modern alternative of compiling with `-parameters` to skip it — clarifies exactly how named binding is wired up and what a codebase's build configuration needs to support it.

Understanding `@Param` matters specifically when:

- You're writing any `@Query` with named parameters — `@Param`'s string argument is what Spring Data actually matches against `:paramName` in the query, and it must match exactly (case-sensitive).
- You're deciding whether to rely on the `-parameters` javac flag (letting Spring Data infer parameter names directly from reflection, no `@Param` needed) versus always explicitly annotating — a real build-configuration and coding-convention decision.
- You're passing a `Collection` as a query parameter for an `IN` clause — `@Param`-annotated collection parameters bind directly, with Spring Data handling the collection-to-`IN`-list translation automatically.

## 3. Core concept

```
 @Param("paramName") on a method parameter
        |
        v
 links that parameter to :paramName in the @Query string,
 REGARDLESS of the parameter's position in the method signature

 @Param's string value MUST match the query's :marker name EXACTLY (case-sensitive)
        |
        v
 ALTERNATIVE: compile with the -parameters javac flag
   -- the compiler preserves actual parameter names in the .class file
   -- Spring Data can then infer names WITHOUT @Param annotations at all:
        @Query("select c from Customer c where c.email = :email")
        Optional<Customer> findByEmail(String email);  // NO @Param -- name inferred as "email"
   -- Spring Boot's default Maven/Gradle setup often already includes -parameters
```

`@Param` is the explicit, always-reliable choice; `-parameters` is a build-configuration convenience that removes the need for it, provided the compiler flag is genuinely active.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Param explicitly names a parameter for binding, or the -parameters compiler flag lets Spring Data infer the name automatically">
  <rect x="10" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Param("email") String email</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">explicit, always works</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">String email  (no @Param)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">requires -parameters at compile time</text>
</svg>

Two paths to the same named-binding outcome, one explicit and always reliable, one implicit and build-configuration-dependent.

## 5. Runnable example

The scenario: an employee lookup, evolving from basic `@Param` usage, to binding a `Collection` parameter for an `IN` clause, to confirming `@Param`'s name must match the query's binding marker exactly by observing a mismatch failure.

### Level 1 — Basic

Use `@Param` to bind a named query parameter, confirming the explicit annotation-based approach.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;

@SpringBootApplication
public class ParamAnnotationLevel1 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Employee() {}
        public Employee(String email) { this.email = email; }
        public String getEmail() { return email; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        @Query("select e from Employee e where e.email = :email")
        Optional<Employee> findByEmailParam(@Param("email") String email);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ParamAnnotationLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:paramann1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("ada@example.com"));

        Optional<Employee> found = repo.findByEmailParam("ada@example.com");
        System.out.println("found = " + found.map(Employee::getEmail).orElse("MISSING"));

        if (found.isEmpty()) throw new AssertionError("Expected to find the employee via @Param binding");
        System.out.println("@Param correctly bound the method parameter to the query's named marker -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ParamAnnotationLevel1.java` on JDK 17+.

`@Param("email")` explicitly links the `email` method parameter to `:email` in the query string — this works regardless of whether the project's build is configured with the `-parameters` compiler flag, making `@Param` the universally reliable choice.

### Level 2 — Intermediate

Bind a `Collection<String>` parameter for an `IN` clause, confirming Spring Data handles the collection-to-`IN`-list translation automatically.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Set;

@SpringBootApplication
public class ParamAnnotationLevel2 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String department;
        protected Employee() {}
        public Employee(String department) { this.department = department; }
        public String getDepartment() { return department; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        @Query("select e from Employee e where e.department in :departments")
        List<Employee> findInDepartments(@Param("departments") Set<String> departments);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ParamAnnotationLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:paramann2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Engineering"));
        repo.save(new Employee("Research"));
        repo.save(new Employee("Sales"));

        List<Employee> matched = repo.findInDepartments(Set.of("Engineering", "Research"));
        System.out.println("matched departments = " + matched.stream().map(Employee::getDepartment).toList());

        if (matched.size() != 2) throw new AssertionError("Expected 2 employees in Engineering or Research");
        System.out.println("@Param correctly bound a Set<String> for an IN clause -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java ParamAnnotationLevel2.java`.

`:departments` in the query, combined with `e.department in :departments`, accepts a `Set<String>` directly — `@Param("departments")` binds the whole collection, and Hibernate translates it into a SQL `IN (...)` clause automatically, with each collection element becoming one value in the `IN` list.

### Level 3 — Advanced

Deliberately mismatch `@Param`'s name against the query's binding marker, confirming the exact, case-sensitive matching requirement by observing the resulting startup failure.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.beans.factory.BeanCreationException;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

@SpringBootApplication
public class ParamAnnotationLevel3 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String email;
        protected Employee() {}
        public Employee(String email) { this.email = email; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        // MISMATCH: the query uses ":email", but @Param says "emailAddress" -- wrong name.
        @Query("select e from Employee e where e.email = :email")
        Employee findByMismatchedParam(@Param("emailAddress") String email);
    }

    public static void main(String[] args) {
        boolean startupFailed = false;
        try {
            ConfigurableApplicationContext ctx = SpringApplication.run(ParamAnnotationLevel3.class,
                "--spring.datasource.url=jdbc:h2:mem:paramann3",
                "--spring.jpa.hibernate.ddl-auto=create-drop");
            ctx.close(); // should not be reached
        } catch (BeanCreationException | IllegalStateException | IllegalArgumentException expected) {
            startupFailed = true;
            System.out.println("startup failed as expected due to the @Param name mismatch: " + expected.getClass().getSimpleName());
        }

        if (!startupFailed)
            throw new AssertionError("Expected startup to fail because @Param(\"emailAddress\") doesn't match \":email\" in the query");
        System.out.println("@Param's name must match the query's binding marker EXACTLY -- mismatch caught at startup -- PASS");
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ParamAnnotationLevel3.java` on JDK 17+. Expect a caught startup failure followed by `PASS` — the failure is the correct, intended outcome for this test.

`@Param("emailAddress")` doesn't match `:email` in the query string — Spring Data validates named-parameter bindings when it builds the repository proxy (during application startup, part of the same fail-fast validation this whole section has repeatedly relied on), catching this mismatch immediately rather than letting the query fail confusingly (or bind to nothing) the first time the broken method is actually called.

## 6. Walkthrough

Trace the startup failure in Level 3.

1. **`SpringApplication.run(...)` begins**, and Spring Data JPA's repository factory attempts to build a proxy for `EmployeeRepository`.
2. **Method resolution for `findByMismatchedParam`**: the factory parses the `@Query` string, `select e from Employee e where e.email = :email`, identifying `:email` as a required named parameter.
3. **Parameter metadata inspection**: it examines the method's declared parameters, finding one annotated `@Param("emailAddress")` — but the query requires a parameter named exactly `email`, not `emailAddress`.
4. **Validation fails**: Spring Data's parameter-binding validation detects this mismatch — the query references a named parameter with no corresponding method argument to supply it — and raises an exception describing the problem.
5. **Exception propagation**: this failure occurs while `EmployeeRepository`'s proxy bean is still being constructed, so it propagates up through `SpringApplication.run(...)` as a `BeanCreationException` (or a related exception type, depending on the exact Spring Data version), preventing the application from starting.
6. **`main`'s `try`/`catch`** catches this startup failure, confirming it occurred.
7. **Verification**: the program asserts a startup failure genuinely happened, printing `PASS` because — for this specific test — a hard startup failure is exactly the correct, expected outcome of the deliberate name mismatch.

```
 @Query("... where e.email = :email")     requires a parameter named "email"
        |
 @Param("emailAddress") String email       supplies a parameter named "emailAddress"
        |
        v
 NAME MISMATCH  -->  validation fails during proxy construction  -->  startup FAILS
```

## 7. Gotchas & takeaways

> **Gotcha:** `@Param`'s string value is matched case-sensitively against the query's `:marker` name — `@Param("Email")` (capital E) will not satisfy a query expecting `:email` (lowercase), even though this looks like an easy visual mismatch to miss during a quick code review. Keep parameter names consistent in casing between the annotation and the query string.

- `@Param("name")` explicitly links a method parameter to a `:name` binding marker in a `@Query` string, working reliably regardless of the project's compiler configuration.
- The `-parameters` javac compiler flag (often already active in default Spring Boot Maven/Gradle setups) lets Spring Data infer parameter names directly from reflection, removing the need for explicit `@Param` annotations — but this depends on the build genuinely compiling with that flag active.
- `@Param`-annotated `Collection`-typed parameters bind directly to an `IN` clause in the query, with Spring Data automatically translating the collection into the SQL `IN (...)` list.
- `@Param`'s name must match the query's binding marker exactly (case-sensitive) — a mismatch is caught at repository-proxy-construction time (application startup), consistent with the fail-fast validation behavior covered throughout this section's query-resolution cards.
