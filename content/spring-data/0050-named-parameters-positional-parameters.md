---
card: spring-data
gi: 50
slug: named-parameters-positional-parameters
title: "Named parameters & positional parameters"
---

## 1. What it is

This card focuses specifically on the mechanics and tradeoffs of `@Query`'s two parameter-binding styles: positional (`?1`, `?2`, matching method parameters strictly by declaration order) and named (`:paramName`, matching by name via `@Param`, order-independent). Both were used in passing throughout earlier cards; this card examines exactly how each resolves, what happens when a query reuses the same parameter multiple times, and why named binding is generally the safer default for anything beyond a single-parameter query.

```java
@Query("select o from Order o where o.minTotal <= :total and o.maxTotal >= :total") // reused
List<Order> findMatchingRange(@Param("total") double total);

@Query("select o from Order o where o.status = ?1 and o.total > ?2") // positional
List<Order> findByStatusAndMinTotal(String status, double minTotal);
```

## 2. Why & when

Positional parameters are concise for simple, single- or few-parameter queries, but they're fragile: reordering a method's parameters (a natural refactor) silently breaks a positional-parameter query, since Java's compiler has no way to verify `?1`/`?2` still line up correctly with the method signature — the mismatch only surfaces at runtime, often as a confusing type-mismatch or wrong-data bug, not a clear error. Named parameters remove this entire class of bug, and additionally allow a single parameter to be referenced multiple times in one query without repeating it in the method signature.

Choose between the two specifically based on:

- **Positional** (`?1`, `?2`) for very short, simple queries with one or two parameters where the binding is obviously unambiguous — acceptable, though named remains the safer default even here.
- **Named** (`:paramName` with `@Param`) for anything with more than one or two parameters, or whenever the same value needs to appear more than once in the query — order-independence and reuse are both named-only capabilities.
- Named parameters as the default choice for any query you expect to be maintained or refactored later — the resilience to parameter reordering is worth the minor extra verbosity of `@Param` annotations.

## 3. Core concept

```
 POSITIONAL:
   @Query("select o from Order o where o.status = ?1 and o.total > ?2")
   List<Order> find(String status, double minTotal);
        |
   ?1 -> FIRST method parameter (status), by declaration order
   ?2 -> SECOND method parameter (minTotal), by declaration order
        |
   REORDERING the method's parameters SILENTLY breaks the binding --
   no compile-time or even reliable runtime check catches this

 NAMED:
   @Query("select o from Order o where o.status = :status and o.total > :minTotal")
   List<Order> find(@Param("status") String status, @Param("minTotal") double minTotal);
        |
   :status  -> matched by NAME to the @Param("status") parameter
   :minTotal -> matched by NAME to the @Param("minTotal") parameter
        |
   PARAMETER ORDER in the method signature DOES NOT MATTER
   THE SAME NAME CAN BE REFERENCED MULTIPLE TIMES in the query string
```

Named binding decouples the query string's parameter references from the method signature's declaration order entirely — the two can evolve independently as long as the names stay consistent.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.v3.org/2000/svg" role="img" aria-label="Positional parameters are matched by declaration order and break silently on reordering; named parameters are matched by name and stay resilient">
  <rect x="10" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="150" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">?1, ?2 (positional)</text>
  <text x="150" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">breaks SILENTLY if params reorder</text>

  <rect x="350" y="20" width="280" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">:status, :minTotal (named)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resilient to reordering, reusable</text>
</svg>

Named parameters trade a small amount of extra verbosity for real resilience against a common refactoring hazard.

## 5. Runnable example

The scenario: an order search, evolving from demonstrating positional parameters' fragility under reordering, to the same query fixed with named parameters, to a query reusing one named parameter twice — a capability positional binding cannot offer at all.

### Level 1 — Basic

Show a positional-parameter query breaking silently after its method's parameters are reordered — a realistic refactor gone wrong.

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

import java.util.List;

@SpringBootApplication
public class ParamBindingLevel1 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private double total;
        protected Order() {}
        public Order(String status, double total) { this.status = status; this.total = total; }
        public String getStatus() { return status; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // Positional query written expecting (status, minTotal) order --
        // but the METHOD SIGNATURE below was refactored to (minTotal, status) --
        // a realistic "reordered during cleanup" mistake.
        @Query("select o from Order o where o.status = ?1 and o.total > ?2")
        List<Order> findMismatched(double minTotal, String status); // ARGS SWAPPED vs. the query's expectation
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ParamBindingLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:parambind1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("shipped", 100.0));
        repo.save(new Order("pending", 50.0));

        boolean threwTypeError = false;
        try {
            // Calling with (50.0, "shipped") -- but ?1 in the query expects a STRING (status),
            // and here we're passing a double FIRST -- a type mismatch.
            repo.findMismatched(50.0, "shipped");
        } catch (Exception expected) {
            threwTypeError = true;
            System.out.println("failed as expected due to positional mismatch: " + expected.getClass().getSimpleName());
        }

        if (!threwTypeError) throw new AssertionError("Expected a type mismatch failure from the mismatched positional binding");
        System.out.println("Positional parameters broke silently-until-runtime after a parameter reorder -- PASS (bug demonstrated)");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java ParamBindingLevel1.java` on JDK 17+.

The query string `?1`/`?2` expects `(status: String, minTotal: double)`, but the method signature was refactored to `findMismatched(double minTotal, String status)` — a `double` first, a `String` second — the exact opposite order. This compiles perfectly fine (Java has no way to check query-string parameter order against method-parameter order) and fails only when Hibernate attempts to bind a `double` value where the query expects a `String`, producing a runtime type-mismatch failure — exactly the "silent until runtime" hazard positional binding carries.

### Level 2 — Intermediate

Fix the same query using named parameters, and confirm the method's parameter *order* genuinely no longer matters.

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

@SpringBootApplication
public class ParamBindingLevel2 {

    @Entity
    public static class Order {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String status;
        private double total;
        protected Order() {}
        public Order(String status, double total) { this.status = status; this.total = total; }
        public double getTotal() { return total; }
    }

    public interface OrderRepository extends JpaRepository<Order, Long> {
        // NAMED parameters -- the method signature's parameter ORDER is irrelevant now.
        @Query("select o from Order o where o.status = :status and o.total > :minTotal")
        List<Order> findByNamedParams(@Param("minTotal") double minTotal, @Param("status") String status);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ParamBindingLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:parambind2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        OrderRepository repo = ctx.getBean(OrderRepository.class);
        repo.save(new Order("shipped", 100.0));
        repo.save(new Order("shipped", 30.0));
        repo.save(new Order("pending", 200.0));

        // Method signature has (minTotal, status) order, but @Param names resolve it correctly regardless.
        List<Order> result = repo.findByNamedParams(50.0, "shipped");
        System.out.println("result = " + result.stream().map(Order::getTotal).toList());

        if (result.size() != 1 || result.get(0).getTotal() != 100.0)
            throw new AssertionError("Expected exactly the shipped order over 50.0");
        System.out.println("Named parameters correctly resolved despite the method's own parameter order -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java ParamBindingLevel2.java`.

`@Param("minTotal")` and `@Param("status")` are matched against `:minTotal`/`:status` in the query string purely by name — even though the method signature declares `minTotal` (a `double`) before `status` (a `String`), the exact reverse of a "natural" reading order, the binding is correct because named resolution never looks at position at all. This is the concrete fix for exactly the fragility Level 1 demonstrated.

### Level 3 — Advanced

Write a query that references the *same* named parameter twice, a capability positional binding has no clean equivalent for (it would require passing the same value twice as separate method arguments).

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

@SpringBootApplication
public class ParamBindingLevel3 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String name;
        private int minSalaryBand;
        private int maxSalaryBand;
        protected Employee() {}
        public Employee(String name, int minSalaryBand, int maxSalaryBand) {
            this.name = name; this.minSalaryBand = minSalaryBand; this.maxSalaryBand = maxSalaryBand;
        }
        public String getName() { return name; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        // A single named parameter, ":targetSalary", referenced TWICE in the same query --
        // impossible to express as cleanly with positional parameters (would need ?1 AND ?1,
        // which some JPA providers reject, or duplicating the argument in the method call).
        @Query("select e from Employee e where e.minSalaryBand <= :targetSalary and e.maxSalaryBand >= :targetSalary")
        List<Employee> findEmployeesForSalaryBand(@Param("targetSalary") int targetSalary);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(ParamBindingLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:parambind3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Ada", 50000, 70000));
        repo.save(new Employee("Grace", 60000, 90000));
        repo.save(new Employee("Katherine", 80000, 100000));

        List<Employee> matches = repo.findEmployeesForSalaryBand(65000);
        System.out.println("employees whose band covers 65000: " + matches.stream().map(Employee::getName).toList());

        if (matches.size() != 2) throw new AssertionError("Expected Ada (50-70k) and Grace (60-90k) to both cover 65000");
        System.out.println("A single named parameter was reused twice in one query -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java ParamBindingLevel3.java`.

`:targetSalary` appears twice in the query string, but the method has only *one* parameter, `targetSalary` — a single value the caller passes once, checked against both `minSalaryBand` and `maxSalaryBand` in the query. `65000` falls within Ada's `50000–70000` band and Grace's `60000–90000` band, but not Katherine's `80000–100000` band, so exactly 2 employees match.

## 6. Walkthrough

Trace `repo.findEmployeesForSalaryBand(65000)`.

1. **Call**: `findEmployeesForSalaryBand(65000)` is invoked with a single `int` argument.
2. **Parameter resolution**: Spring Data JPA's query-parameter binding sees the declared query has two occurrences of `:targetSalary`, and the method has one `@Param("targetSalary")`-annotated parameter — it binds the single supplied value, `65000`, to *both* occurrences of `:targetSalary` in the resulting JPQL query.
3. **Query execution**: the generated query becomes, conceptually, `WHERE e.minSalaryBand <= 65000 AND e.maxSalaryBand >= 65000`, evaluated against all three seeded employees.
4. **Row-by-row evaluation**: Ada (50000–70000) satisfies both conditions (50000 ≤ 65000 and 70000 ≥ 65000); Grace (60000–90000) satisfies both (60000 ≤ 65000 and 90000 ≥ 65000); Katherine (80000–100000) fails the first condition (80000 ≤ 65000 is false).
5. **Result**: exactly 2 employees — Ada and Grace — match, returned as a `List<Employee>`.
6. **Verification**: the program checks the result count and confirms it matches the expected pair, proving the single named parameter correctly bound to both occurrences in the query.

```
 findEmployeesForSalaryBand(65000)
        |
        v
 single value 65000 bound to BOTH ":targetSalary" occurrences
        |
        v
 WHERE minSalaryBand <= 65000 AND maxSalaryBand >= 65000
        |
        v
 Ada (50-70k): true AND true  -> MATCH
 Grace (60-90k): true AND true -> MATCH
 Katherine (80-100k): FALSE AND true -> no match
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing positional and named parameters within the *same* query string is not portable/reliable across all JPA providers and is generally rejected or discouraged — pick one style per query and stay consistent, rather than combining `?1` and `:paramName` in the same `@Query` string.

- Positional parameters (`?1`, `?2`) bind strictly by method-parameter declaration order — concise for trivial queries, but silently fragile against a common refactor: reordering the method's own parameters breaks the binding with no compile-time warning.
- Named parameters (`:paramName` with `@Param`) bind by name, making the query string's parameter references completely independent of the method signature's declaration order — the safer default for any query beyond the simplest single-parameter case.
- A single named parameter can be referenced multiple times within one query string, letting one method argument satisfy multiple conditions — positional binding has no clean equivalent for this.
- When in doubt, default to named parameters — the small extra verbosity of `@Param` annotations buys real resilience against exactly the kind of silent, hard-to-diagnose bug positional parameters can introduce during routine refactoring.
