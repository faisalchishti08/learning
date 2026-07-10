---
card: spring-data
gi: 18
slug: sort-typedsort-sort-typedsort
title: "Sort & TypedSort"
---

## 1. What it is

`Sort` is the class used throughout this section to express ordering — `Sort.by("lastName")`, `Sort.by("age").descending()`, or a multi-property `Sort.by("lastName").ascending().and(Sort.by("firstName"))`. `Sort.TypedSort<T>`, obtained via `Sort.sort(Customer.class)`, is a type-safe variant that lets you build the same kind of `Sort` using method references instead of raw property-name strings — catching a misspelled property name at compile time instead of at repository-proxy-creation time (or, worse, silently at query time for stores that don't validate property names as strictly).

```java
Sort byLastName = Sort.by("lastName");                     // string-based -- typo-prone
Sort byLastNameTyped = Sort.sort(Customer.class)             // TypedSort -- compiler-checked
    .by(Customer::getLastName).ascending();
```

## 2. Why & when

`Sort.by("lastName")` works, but nothing stops you from writing `Sort.by("lastNaem")` — a typo that, depending on the store and Spring Data version, might fail at query time with a moderately clear error, or might simply produce unexpected results. `TypedSort` closes that gap by requiring an actual method reference (`Customer::getLastName`), which the Java compiler itself verifies exists — a property-name error becomes a compile error instead of a runtime one.

Reach for `TypedSort` specifically when:

- You're building `Sort` instances dynamically in application code (not just passing a fixed string once) and want the same compile-time safety for sort properties that method references already give you elsewhere in modern Java code.
- You're refactoring an entity — renaming a field — and want the compiler to catch every place that field's name was used for sorting, the same way it catches every other reference to a renamed field.
- You're building a reusable sort-building utility or a generic search/filter component and want it to be robust against property renames without needing a runtime test suite to catch the breakage.

For a one-off, fixed sort expression, plain `Sort.by("propertyName")` remains perfectly fine — `TypedSort` earns its keep specifically where the extra compile-time safety matters enough to justify its slightly more verbose syntax.

## 3. Core concept

```
 Sort.by("lastName")                       -- string-based
 Sort.by("lastName").ascending()
 Sort.by("lastName").descending()
 Sort.by("lastName").and(Sort.by("firstName"))   -- multi-property, combined via .and(...)

 Sort.TypedSort<T>  (via Sort.sort(Customer.class)):
 Sort.sort(Customer.class).by(Customer::getLastName).ascending()
        |
        v
 PropertyNameDetectionInterceptor extracts the property name "lastName"
 from the METHOD REFERENCE by generating a proxy and recording which
 getter was invoked -- producing the SAME Sort object as the string-based
 version, just derived from a compiler-checked source
```

`TypedSort` doesn't change what `Sort` fundamentally is or how it's used by a repository method — it only changes how the property name string inside that `Sort` gets constructed, trading a small amount of extra ceremony for compile-time property-name safety.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Both Sort.by(string) and TypedSort produce the same underlying Sort object, but TypedSort derives the property name from a checked method reference">
  <rect x="10" y="20" width="270" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Sort.by("lastNaem")</text>
  <text x="145" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">typo compiles fine -- fails later</text>

  <rect x="350" y="20" width="280" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="490" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Sort.sort(Customer.class).by(Customer::getLastNaem)</text>
  <text x="490" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">COMPILE ERROR -- caught immediately</text>

  <rect x="150" y="110" width="340" height="35" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="320" y="132" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">Both, when correct, produce the identical Sort object</text>
</svg>

The same underlying `Sort`, reached by two different paths — one string-based and typo-prone, one method-reference-based and compiler-checked.

## 5. Runnable example

The scenario: an `Employee` search, evolving from string-based multi-property `Sort`, to the equivalent built via `TypedSort`, to a direct proof that both paths produce genuinely equal, interchangeable `Sort` objects.

### Level 1 — Basic

Build a multi-property `Sort` the traditional string-based way and apply it to a query.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class TypedSortLevel1 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String department;
        private String lastName;
        protected Employee() {}
        public Employee(String department, String lastName) { this.department = department; this.lastName = lastName; }
        public String getDepartment() { return department; }
        public String getLastName() { return lastName; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        List<Employee> findAll(Sort sort);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(TypedSortLevel1.class,
            "--spring.datasource.url=jdbc:h2:mem:typedsort1",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Engineering", "Hopper"));
        repo.save(new Employee("Research", "Lovelace"));
        repo.save(new Employee("Engineering", "Byron"));

        Sort sort = Sort.by("department").ascending().and(Sort.by("lastName").ascending());
        List<Employee> sorted = repo.findAll(sort);

        System.out.println("sorted (dept, lastName): " + sorted.stream()
            .map(e -> e.getDepartment() + "/" + e.getLastName()).toList());

        if (!sorted.get(0).getLastName().equals("Byron"))
            throw new AssertionError("Expected Byron (Engineering) before Hopper (Engineering) alphabetically");
        System.out.println("String-based multi-property Sort worked -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-boot-starter-data-jpa` and `com.h2database:h2` on the classpath, then `java TypedSortLevel1.java` on JDK 17+.

`Sort.by("department").ascending().and(Sort.by("lastName").ascending())` combines two orderings — first by department, then by last name within each department — both property names supplied as raw strings, with no compile-time verification that `"department"` and `"lastName"` genuinely exist on `Employee`.

### Level 2 — Intermediate

Build the identical ordering using `Sort.TypedSort<Employee>` and method references instead of strings.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class TypedSortLevel2 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String department;
        private String lastName;
        protected Employee() {}
        public Employee(String department, String lastName) { this.department = department; this.lastName = lastName; }
        public String getDepartment() { return department; }
        public String getLastName() { return lastName; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        List<Employee> findAll(Sort sort);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(TypedSortLevel2.class,
            "--spring.datasource.url=jdbc:h2:mem:typedsort2",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Engineering", "Hopper"));
        repo.save(new Employee("Research", "Lovelace"));
        repo.save(new Employee("Engineering", "Byron"));

        // TypedSort -- method references instead of raw strings, checked by the compiler.
        Sort.TypedSort<Employee> typed = Sort.sort(Employee.class);
        Sort sort = typed.by(Employee::getDepartment).ascending()
            .and(typed.by(Employee::getLastName).ascending());

        List<Employee> sorted = repo.findAll(sort);

        System.out.println("sorted (dept, lastName) via TypedSort: " + sorted.stream()
            .map(e -> e.getDepartment() + "/" + e.getLastName()).toList());

        if (!sorted.get(0).getLastName().equals("Byron"))
            throw new AssertionError("Expected Byron (Engineering) before Hopper (Engineering) alphabetically");
        System.out.println("TypedSort produced the same ordering, with method-reference safety -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java TypedSortLevel2.java`.

`Sort.sort(Employee.class)` returns a `TypedSort<Employee>` — calling `.by(Employee::getDepartment)` internally generates a proxy `Employee` instance and records which getter method was invoked, extracting `"department"` as the property name via that interception, rather than requiring it to be typed out as a string. If `Employee::getDepartment` were renamed and this call site weren't updated, the code simply wouldn't compile — impossible with the string-based version from Level 1.

### Level 3 — Advanced

Directly prove both approaches produce genuinely equal `Sort` objects (not just visually similar ordering behavior), and combine `TypedSort` with a derived-query method's `Sort` parameter, showing the two features composing naturally.

```java
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

@SpringBootApplication
public class TypedSortLevel3 {

    @Entity
    public static class Employee {
        @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
        private Long id;
        private String department;
        private String lastName;
        private int salary;
        protected Employee() {}
        public Employee(String department, String lastName, int salary) {
            this.department = department; this.lastName = lastName; this.salary = salary;
        }
        public String getDepartment() { return department; }
        public String getLastName() { return lastName; }
        public int getSalary() { return salary; }
    }

    public interface EmployeeRepository extends JpaRepository<Employee, Long> {
        List<Employee> findByDepartment(String department, Sort sort);
    }

    public static void main(String[] args) {
        ConfigurableApplicationContext ctx = SpringApplication.run(TypedSortLevel3.class,
            "--spring.datasource.url=jdbc:h2:mem:typedsort3",
            "--spring.jpa.hibernate.ddl-auto=create-drop");

        EmployeeRepository repo = ctx.getBean(EmployeeRepository.class);
        repo.save(new Employee("Engineering", "Hopper", 95000));
        repo.save(new Employee("Engineering", "Byron", 88000));
        repo.save(new Employee("Engineering", "Lovelace", 102000));

        // Step 1: prove equality between string-based and TypedSort-based Sort objects.
        Sort stringBased = Sort.by(Sort.Direction.DESC, "salary");
        Sort typedBased = Sort.sort(Employee.class).by(Employee::getSalary).descending();

        System.out.println("stringBased = " + stringBased);
        System.out.println("typedBased  = " + typedBased);
        System.out.println("are they .equals()? " + stringBased.equals(typedBased));

        // Step 2: use the TypedSort-derived Sort in a real derived-query call.
        List<Employee> engineeringBySalaryDesc = repo.findByDepartment("Engineering", typedBased);
        System.out.println("Engineering by salary desc: " + engineeringBySalaryDesc.stream()
            .map(e -> e.getLastName() + "=" + e.getSalary()).toList());

        if (!stringBased.equals(typedBased))
            throw new AssertionError("Expected the string-based and TypedSort-based Sort objects to be equal");
        if (!engineeringBySalaryDesc.get(0).getLastName().equals("Lovelace"))
            throw new AssertionError("Expected the highest-paid engineer (Lovelace) first");

        System.out.println("String-based and TypedSort-based Sort objects are genuinely equal, and both work in queries -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java TypedSortLevel3.java`.

`Sort.by(Sort.Direction.DESC, "salary")` and `Sort.sort(Employee.class).by(Employee::getSalary).descending()` are constructed through entirely different code paths — one from a raw string, one from a method reference resolved via proxy interception — yet `stringBased.equals(typedBased)` evaluates `true`, because both ultimately produce a `Sort` instance wrapping the identical `Order` (property name `"salary"`, direction `DESC`). The `TypedSort`-derived `Sort` is then passed into `findByDepartment`'s regular `Sort` parameter exactly like any other `Sort` instance — `TypedSort` is a *construction* mechanism, not a different kind of `Sort` at the type level.

## 6. Walkthrough

Trace how `Sort.sort(Employee.class).by(Employee::getSalary)` resolves the property name.

1. **`Sort.sort(Employee.class)`** creates a `TypedSort<Employee>` instance — internally, this prepares a dynamic proxy generation mechanism keyed to the `Employee` class, but does no actual sorting work yet.
2. **`.by(Employee::getSalary)`** is called with a method reference. Internally, `TypedSort` generates a CGLIB (or similar) proxy instance of `Employee` and invokes the supplied function (`Employee::getSalary`) against that proxy.
3. **Interception**: because the proxy overrides every method, calling `getSalary()` on it doesn't return a real salary value — it's intercepted, and the proxy records that the `getSalary` method was the one invoked, then derives the corresponding property name, `"salary"` (following JavaBean getter-to-property-name conventions), from that method's name.
4. **`Sort` construction**: with the property name `"salary"` now resolved, `TypedSort` builds a regular `Sort` object wrapping an `Order` for `"salary"` — from this point on, it's indistinguishable from a `Sort` built any other way.
5. **`.descending()`** sets that `Order`'s direction to `DESC`, exactly as it would on a string-based `Sort`.
6. **`stringBased.equals(typedBased)`**: `Sort`'s `equals()` implementation compares the underlying list of `Order` objects (property name + direction) — since both `Sort` instances wrap an identical single `Order("salary", DESC)`, they compare equal, regardless of which construction path produced them.
7. **`repo.findByDepartment("Engineering", typedBased)`**: the repository proxy treats `typedBased` exactly like any other `Sort` argument — it has no awareness that this particular `Sort` was built via method reference rather than a raw string — producing `WHERE department = ?1 ORDER BY salary DESC`, correctly listing `Lovelace` (102000) first.

```
 Sort.sort(Employee.class).by(Employee::getSalary)
        |
        v
 generates a PROXY Employee, invokes getSalary() on it
        |
        v
 proxy records: "getSalary was called" -> derives property name "salary"
        |
        v
 builds a normal Sort(Order("salary", ...))  -- identical in every way to a string-based Sort
```

## 7. Gotchas & takeaways

> **Gotcha:** `TypedSort`'s property-name extraction relies on generating a working proxy and actually invoking the method reference against it — this means the referenced getter must be a genuine, simple property accessor (following JavaBean naming and doing nothing but returning a field) for the interception to correctly derive the property name. A getter with custom logic beyond a plain field return can produce incorrect or failed resolution, since the proxy can't meaningfully execute arbitrary logic during interception.

- `TypedSort` and string-based `Sort.by(...)` produce genuinely equal `Sort` objects when they describe the same property and direction — `TypedSort` is purely a safer *construction* mechanism, not a distinct kind of sort at the type level, and the two are fully interchangeable everywhere a `Sort` is expected.
- The main benefit of `TypedSort` is catching a property-name typo or a renamed field at compile time — a real, if modest, safety improvement over a raw string that only reveals a problem at startup or query time.
- `TypedSort`-derived `Sort` objects compose with everything else `Sort` supports — `.and(...)` for multi-property ordering, `.ascending()`/`.descending()` for direction, and passing directly into any `Sort`-accepting repository method parameter.
- For a one-off, rarely-changed sort expression, the extra verbosity of `TypedSort` may not be worth it — it earns its keep most clearly in reusable sort-building code or during active refactoring, where the compile-time safety has genuine, repeated value.
