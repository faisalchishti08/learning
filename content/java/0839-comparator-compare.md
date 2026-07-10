---
card: java
gi: 839
slug: comparator-compare
title: Comparator & compare
---

## 1. What it is

`Comparator<T>` is a functional interface (a single abstract method, `compare(T a, T b)`, with the same negative/zero/positive contract as [`Comparable.compareTo`](0838-comparable-compareto.md)) representing an **external** ordering — one that's supplied separately from the type being compared, rather than baked into the type itself. Because it's a functional interface, a `Comparator` can be written as a lambda expression or a method reference, passed directly to `list.sort(comparator)`, `Collections.sort(list, comparator)`, or a `TreeMap`/`TreeSet` constructor, without requiring any change to the class being compared at all — including classes you don't own and can't modify.

## 2. Why & when

`Comparable` only ever lets a type declare one natural ordering, baked permanently into its `compareTo` implementation — but real-world sorting needs are rarely that singular: a list of `Employee` objects might need to be sorted by name in one report, by hire date in another, and by salary (descending) in a third, all from the exact same underlying data. `Comparator` supplies the ordering from *outside* the type, so as many different orderings as needed can coexist, chosen per call site, without touching the `Employee` class at all. It's also the only option for sorting a type that doesn't implement `Comparable` (including built-in or third-party classes you can't modify) or for cases needing a **different** order than a type's own natural one (e.g., sorting `String`s in reverse order, or case-insensitively, without changing `String` itself, which of course isn't even possible).

## 3. Core concept

```java
List<String> names = new ArrayList<>(List.of("charlie", "Alice", "bob"));

// A Comparator supplied externally -- no change to String itself needed:
names.sort(String.CASE_INSENSITIVE_ORDER);
System.out.println(names); // [Alice, bob, charlie] -- case-insensitive alphabetical

// As a lambda, for a custom ordering String doesn't provide natively:
names.sort((a, b) -> Integer.compare(a.length(), b.length())); // shortest name first
System.out.println(names); // [bob, Alice, charlie] or similar, by length
```

`Comparator.compare(a, b)` follows the identical sign convention as `compareTo`: negative means `a` sorts before `b`, zero means they're equal for ordering purposes, positive means `a` sorts after `b` — the two interfaces are deliberately parallel, differing only in whether the ordering logic lives inside the type (`Comparable`) or is supplied from outside it (`Comparator`).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same Employee objects can be sorted by different Comparators supplied per call site, without the Employee class itself defining any single fixed ordering">
  <rect x="240" y="15" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="40" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">List&lt;Employee&gt;</text>

  <line x1="280" y1="55" x2="140" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a839)"/>
  <line x1="320" y1="55" x2="320" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a839)"/>
  <line x1="360" y1="55" x2="500" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a839)"/>

  <rect x="40" y="100" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="140" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sort by name (report A)</text>

  <rect x="220" y="100" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sort by salary (report B)</text>

  <rect x="400" y="100" width="200" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="500" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">sort by hire date (report C)</text>
</svg>

*The same data, three different orderings — each supplied externally as a `Comparator`, with no change to the `Employee` class.*

## 5. Runnable example

Scenario: generating different sorted reports from the same list of employees, growing from a single external comparator, to multiple reusable named comparators, to demonstrating sort stability's role in producing predictable, repeatable multi-criteria reports.

### Level 1 — Basic

```java
import java.util.*;

public class ReportsBasic {
    record Employee(String name, int salary) {}

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Charlie", 75000), new Employee("Alice", 82000), new Employee("Bob", 68000)
        ));

        // Employee has no natural ordering (it's not Comparable) -- a Comparator is required.
        employees.sort((a, b) -> Integer.compare(a.salary(), b.salary()));
        System.out.println("sorted by salary: " + employees);
    }
}
```

**How to run:** `java ReportsBasic.java` (JDK 17+).

Expected output:
```
sorted by salary: [Employee[name=Bob, salary=68000], Employee[name=Charlie, salary=75000], Employee[name=Alice, salary=82000]]
```

Since `Employee` (a record here) doesn't implement `Comparable`, calling `employees.sort(null)` would throw `ClassCastException` at runtime — the lambda comparator supplies the ordering externally, entirely independent of the `Employee` type's own definition.

### Level 2 — Intermediate

```java
import java.util.*;

public class ReportsMultipleOrderings {
    record Employee(String name, int salary) {}

    // Named, reusable comparators -- one per report, all operating on the SAME Employee type.
    static final Comparator<Employee> BY_NAME = (a, b) -> a.name().compareTo(b.name());
    static final Comparator<Employee> BY_SALARY_DESC = (a, b) -> Integer.compare(b.salary(), a.salary());

    public static void main(String[] args) {
        List<Employee> employees = List.of(
            new Employee("Charlie", 75000), new Employee("Alice", 82000), new Employee("Bob", 68000)
        );

        List<Employee> reportA = new ArrayList<>(employees);
        reportA.sort(BY_NAME);
        System.out.println("report A (alphabetical): " + reportA);

        List<Employee> reportB = new ArrayList<>(employees);
        reportB.sort(BY_SALARY_DESC);
        System.out.println("report B (highest salary first): " + reportB);
    }
}
```

**How to run:** `java ReportsMultipleOrderings.java`.

Expected output:
```
report A (alphabetical): [Employee[name=Alice, salary=82000], Employee[name=Bob, salary=68000], Employee[name=Charlie, salary=75000]]
report B (highest salary first): [Employee[name=Charlie, salary=75000], Employee[name=Alice, salary=82000], Employee[name=Bob, salary=68000]]
```

The real-world concern added: two independently-named, reusable `Comparator` constants applied to **copies** of the same source list, producing two genuinely different orderings of identical underlying data — exactly the multi-report scenario `Comparable`'s single fixed ordering couldn't support without an external comparator.

### Level 3 — Advanced

```java
import java.util.*;

public class SortStabilityDemo {
    record Employee(String name, String department, int salary) {}

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Alice", "Engineering", 90000),
            new Employee("Bob", "Sales", 90000),
            new Employee("Charlie", "Engineering", 85000),
            new Employee("Dave", "Sales", 85000)
        ));

        // Sort by salary only -- ties (equal salaries) keep their ORIGINAL relative order (stable sort).
        List<Employee> bySalaryOnly = new ArrayList<>(employees);
        bySalaryOnly.sort((a, b) -> Integer.compare(b.salary(), a.salary()));
        System.out.println("sorted by salary desc (stable -- ties keep original order):");
        bySalaryOnly.forEach(e -> System.out.println("  " + e.name() + " (" + e.department() + ", $" + e.salary() + ")"));

        // Sorting TWICE, in sequence, leverages stability to achieve a multi-level sort manually:
        // first by department (the SECONDARY key), then by salary desc (the PRIMARY key) --
        // because the second sort is stable, department order survives WITHIN each salary tier.
        List<Employee> multiLevel = new ArrayList<>(employees);
        multiLevel.sort((a, b) -> a.department().compareTo(b.department())); // secondary key sorted first
        multiLevel.sort((a, b) -> Integer.compare(b.salary(), a.salary()));   // primary key sorted second, stably

        System.out.println("multi-level (salary desc, then department for ties):");
        multiLevel.forEach(e -> System.out.println("  " + e.name() + " (" + e.department() + ", $" + e.salary() + ")"));
    }
}
```

**How to run:** `java SortStabilityDemo.java`.

Expected output:
```
sorted by salary desc (stable -- ties keep original order):
  Alice (Engineering, $90000)
  Bob (Sales, $90000)
  Charlie (Engineering, $85000)
  Dave (Sales, $85000)
multi-level (salary desc, then department for ties):
  Alice (Engineering, $90000)
  Bob (Sales, $90000)
  Charlie (Engineering, $85000)
  Dave (Sales, $85000)
```

This adds the production-flavored hard case: relying on `List.sort`'s **stability guarantee** (equal elements, by the comparator's judgment, retain their relative input order) to perform a manual two-key sort by sorting twice — first by the secondary key (department), then by the primary key (salary). Because the second sort is stable, elements that tie on salary retain whatever relative order the *first* sort (by department) had already established, correctly producing a "salary descending, department ascending within each salary tier" result without writing a single combined comparator.

## 6. Walkthrough

Tracing `SortStabilityDemo.main`'s `multiLevel` construction:

1. `multiLevel` starts as a copy of the original list: `Alice(Eng,90k), Bob(Sales,90k), Charlie(Eng,85k), Dave(Sales,85k)`.
2. `multiLevel.sort((a, b) -> a.department().compareTo(b.department()))` sorts purely by department name alphabetically: `Engineering` before `Sales`. Since `Alice` and `Charlie` are both `Engineering`, and `Bob` and `Dave` are both `Sales`, the result is `Alice, Charlie, Bob, Dave` — with `Alice` before `Charlie` (both Engineering) and `Bob` before `Dave` (both Sales), preserving each pair's original relative order from before this sort, since a comparison purely by department doesn't distinguish between employees in the *same* department, and Java's sort implementation is guaranteed stable.
3. `multiLevel.sort((a, b) -> Integer.compare(b.salary(), a.salary()))` then sorts the **already department-sorted** list by salary, descending. `Alice` (90k) and `Bob` (90k) tie for highest salary; `Charlie` (85k) and `Dave` (85k) tie for lower salary. Because this second sort is stable, and the list entering this sort was `Alice, Charlie, Bob, Dave`, the two salary-90k employees (`Alice`, `Bob`) retain their *relative* order from before this sort — but critically, that relative order was `Alice` before `Bob` only because `Alice` (Engineering) happened to come before `Bob` (Sales) in the department-sorted intermediate list.
4. The final result groups by salary first (90k tier, then 85k tier), and within each tier, orders by department (`Engineering` before `Sales`) — exactly the desired "primary key salary, secondary key department" outcome, achieved purely by sorting twice in the correct order (secondary key first, primary key last) and relying on stability to preserve the secondary ordering within primary-key ties.

## 7. Gotchas & takeaways

> **Gotcha:** the two-sorts-in-sequence technique for multi-level sorting **only** works correctly if the sorts are applied in reverse priority order — secondary key first, primary key last — and only because Java's `List.sort`/`Collections.sort` are guaranteed **stable**. Sorting in the opposite order (primary key first, secondary key second) would destroy the primary ordering entirely, since the second sort would freely reorder elements based purely on the secondary key, with no memory of the primary key's prior arrangement.

- `Comparator<T>` is a functional interface supplying an ordering externally, independent of whether `T` implements [`Comparable`](0838-comparable-compareto.md) at all.
- The same underlying data can be sorted multiple different ways by supplying different `Comparator`s at each call site — no changes to the type being sorted are ever needed.
- Java's sort implementations (`List.sort`, `Collections.sort`) are guaranteed **stable**: elements considered equal by the comparator retain their original relative order.
- Sort stability enables a manual multi-key sort by sorting repeatedly, secondary keys first and the primary key last — each subsequent stable sort preserves the finer-grained ordering established by the sorts before it.
- Prefer named, reusable `Comparator` constants (or the fluent builders covered in [`Comparator.comparing`/`thenComparing`](0840-comparator-comparing-thencomparing-reversed-nullsfirst.md)) over ad-hoc inline lambdas when the same ordering logic is used in more than one place.
