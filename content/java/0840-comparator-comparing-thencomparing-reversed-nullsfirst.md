---
card: java
gi: 840
slug: comparator-comparing-thencomparing-reversed-nullsfirst
title: Comparator.comparing / thenComparing / reversed / nullsFirst
---

## 1. What it is

Since Java 8, `Comparator` provides a family of static and default methods that build complex orderings **declaratively**, without hand-writing comparison logic: `Comparator.comparing(keyExtractor)` builds a comparator from a function that extracts a sortable key from each element; `.thenComparing(...)` chains a tie-breaking comparator onto an existing one; `.reversed()` flips any comparator's direction; and `Comparator.nullsFirst(comparator)`/`nullsLast(comparator)` wrap a comparator to handle `null` elements gracefully, sorting them to one end instead of throwing `NullPointerException`. These compose fluently into a single expression that reads like a specification: "sort by department, then by salary descending, then by name, treating a missing manager as sorting last."

## 2. Why & when

The multi-sort-in-sequence technique — sorting repeatedly, secondary keys first, relying on stability — works, but it's verbose, easy to get the order backward, and doesn't read as a single coherent statement of intent. The fluent `Comparator` builder methods replace that entirely: `Comparator.comparing(Employee::department).thenComparing(Employee::salary, Comparator.reverseOrder()).thenComparing(Employee::name)` expresses the exact same three-level sort as one readable chain, in the natural primary-to-tertiary order (not the reversed order the manual multi-sort technique required). Reach for these builders any time a sort needs more than one criterion, needs to reverse direction, or needs to handle `null` values in the data gracefully — which is to say, for most non-trivial real-world sorting.

## 3. Core concept

```java
record Employee(String name, String department, Integer managerId, int salary) {}

Comparator<Employee> ordering = Comparator
    .comparing(Employee::department)                                    // primary key
    .thenComparing(Employee::salary, Comparator.reverseOrder())          // secondary key, descending
    .thenComparing(Employee::name);                                      // tertiary key, tie-breaker

employees.sort(ordering); // one readable chain, no manual multi-pass sorting needed
```

Each `.thenComparing(...)` call only ever gets consulted when every comparator **before** it in the chain returned exactly `0` (a tie) — this is the fluent equivalent of the manual "check age, only if equal check name" logic from [`Comparable`](0838-comparable-compareto.md)'s multi-field example, but composed declaratively instead of written as nested `if` statements.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A chained comparator tries the primary key first, only consulting each subsequent key when every prior key resulted in a tie">
  <g font-family="sans-serif">
    <rect x="40" y="20" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="120" y="45" fill="#e6edf3" font-size="10" text-anchor="middle">comparing(department)</text>

    <line x1="120" y1="60" x2="120" y2="85" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a840)"/>
    <text x="170" y="75" fill="#8b949e" font-size="9">tie?</text>

    <rect x="40" y="90" width="200" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
    <text x="140" y="115" fill="#e6edf3" font-size="10" text-anchor="middle">thenComparing(salary, reversed)</text>

    <line x1="140" y1="130" x2="140" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a840)"/>
    <text x="190" y="145" fill="#8b949e" font-size="9">tie?</text>

    <rect x="40" y="160" width="160" height="30" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
    <text x="120" y="180" fill="#e6edf3" font-size="10" text-anchor="middle">thenComparing(name)</text>
  </g>
  <text x="420" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">Each subsequent key is only</text>
  <text x="420" y="118" fill="#8b949e" font-size="10" font-family="sans-serif">consulted if every prior key</text>
  <text x="420" y="136" fill="#8b949e" font-size="10" font-family="sans-serif">tied (returned exactly 0)</text>

  <defs><marker id="a840" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Each `.thenComparing(...)` only fires when every earlier comparator in the chain returned a tie.*

## 5. Runnable example

Scenario: sorting a realistic, messy employee roster — multiple sort keys, one field needing reversed order, and some employees with a missing (null) manager ID — growing from a single-key fluent comparator, to a full multi-key chain, to correctly handling nulls without throwing.

### Level 1 — Basic

```java
import java.util.*;

public class RosterBasic {
    record Employee(String name, String department, int salary) {}

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Charlie", "Sales", 75000),
            new Employee("Alice", "Engineering", 82000),
            new Employee("Bob", "Engineering", 68000)
        ));

        employees.sort(Comparator.comparing(Employee::department));
        System.out.println("sorted by department: " + employees);
    }
}
```

**How to run:** `java RosterBasic.java` (JDK 17+).

Expected output:
```
sorted by department: [Employee[name=Alice, department=Engineering, salary=82000], Employee[name=Bob, department=Engineering, salary=68000], Employee[name=Charlie, department=Sales, salary=75000]]
```

`Comparator.comparing(Employee::department)` builds a full `Comparator<Employee>` from just the key-extraction function — no manual `compare` method needed for this single-key case.

### Level 2 — Intermediate

```java
import java.util.*;

public class RosterMultiKey {
    record Employee(String name, String department, int salary) {}

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Charlie", "Engineering", 75000),
            new Employee("Alice", "Engineering", 82000),
            new Employee("Bob", "Sales", 82000),
            new Employee("Dave", "Sales", 68000)
        ));

        Comparator<Employee> ordering = Comparator
            .comparing(Employee::department)
            .thenComparing(Employee::salary, Comparator.reverseOrder()); // secondary key, descending

        employees.sort(ordering);
        System.out.println("sorted by department, then salary desc:");
        employees.forEach(e -> System.out.println("  " + e.name() + " (" + e.department() + ", $" + e.salary() + ")"));
    }
}
```

**How to run:** `java RosterMultiKey.java`.

Expected output:
```
sorted by department, then salary desc:
  Alice (Engineering, $82000)
  Charlie (Engineering, $75000)
  Bob (Sales, $82000)
  Dave (Sales, $68000)
```

The real-world concern added: a genuine two-key sort — department alphabetically, then salary descending within each department — expressed as one fluent chain in natural primary-then-secondary order, rather than the reversed-order manual multi-pass-sort technique that plain [`Comparator`](0839-comparator-compare.md) composition without these builder methods would require.

### Level 3 — Advanced

```java
import java.util.*;

public class RosterWithNulls {
    record Employee(String name, String department, Integer managerId, int salary) {}

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Charlie", "Engineering", 101, 75000),
            new Employee("Alice", "Engineering", null, 82000), // Alice has no manager (e.g. she IS the manager)
            new Employee("Bob", "Sales", 102, 82000),
            new Employee("Dave", "Sales", null, 68000)
        ));

        // Sort by managerId, with nulls sorting FIRST (unmanaged employees listed at the top),
        // then by name as a tie-breaker for equal (including both-null) managerId values.
        Comparator<Employee> ordering = Comparator
            .comparing(Employee::managerId, Comparator.nullsFirst(Comparator.naturalOrder()))
            .thenComparing(Employee::name);

        employees.sort(ordering);
        System.out.println("sorted by managerId (nulls first), then name:");
        employees.forEach(e -> System.out.println("  " + e.name() + " (manager: " + e.managerId() + ")"));
    }
}
```

**How to run:** `java RosterWithNulls.java`.

Expected output:
```
sorted by managerId (nulls first), then name:
  Alice (manager: null)
  Dave (manager: null)
  Charlie (manager: 101)
  Bob (manager: 102)
```

This adds the production-flavored hard case: real data with missing values. Without `Comparator.nullsFirst(...)`, calling `Comparator.comparing(Employee::managerId)` directly would throw `NullPointerException` the moment it tried to compare a `null` `managerId` against a non-null one — `Integer.compareTo` (which the default natural-ordering comparator would use) has no defined behavior for `null`. Wrapping the natural-ordering comparator with `Comparator.nullsFirst(...)` handles this gracefully, treating `null` as sorting before every non-null value, and the `.thenComparing(Employee::name)` tie-breaker correctly orders `Alice` before `Dave` since both share the "tied" `null` managerId.

## 6. Walkthrough

Tracing `RosterWithNulls.main`'s sort:

1. `ordering` is built as `Comparator.comparing(Employee::managerId, Comparator.nullsFirst(Comparator.naturalOrder()))` — this reads as "extract each employee's `managerId`, then compare those extracted values using a null-safe wrapper around natural (numeric) ordering," followed by `.thenComparing(Employee::name)` as the tie-breaker.
2. When the sort compares `Alice` (managerId `null`) against `Charlie` (managerId `101`), the `nullsFirst`-wrapped comparator recognizes one side is `null` and immediately returns a negative result (indicating `null` sorts first), without ever attempting `null.compareTo(101)`, which would otherwise throw `NullPointerException`.
3. When comparing `Alice` (managerId `null`) against `Dave` (managerId `null`), the `nullsFirst` wrapper recognizes both sides are `null` and returns exactly `0` — a genuine tie at the primary-key level, since neither has a "real" managerId value to differ on.
4. Because that primary comparison tied, the chain proceeds to `.thenComparing(Employee::name)`, comparing `"Alice"` against `"Dave"` alphabetically — `"Alice"` sorts first, correctly placing her before `Dave` among the two unmanaged employees.
5. `Charlie` (managerId `101`) and `Bob` (managerId `102`) are both non-null, so the `nullsFirst` wrapper delegates to the underlying `Comparator.naturalOrder()`, comparing `101` against `102` numerically — `Charlie` sorts before `Bob`. Since neither pair of comparisons among the managed employees ties on `managerId`, the name-based tie-breaker never needs to run for them.
6. The final order — `Alice`, `Dave` (both null, alphabetical), then `Charlie`, `Bob` (both non-null, numeric) — confirms the whole chain worked correctly across both the null-handling case and the normal numeric-comparison case.

## 7. Gotchas & takeaways

> **Gotcha:** `Comparator.comparing(Employee::managerId)` **without** wrapping the key comparison in `nullsFirst`/`nullsLast` throws `NullPointerException` the instant it needs to compare a `null`-valued key against anything — this failure only surfaces once the sort actually encounters a `null` in the data, which can mean code that worked fine in testing (with clean sample data) breaks in production the first time a genuinely missing value appears.

- `Comparator.comparing(keyExtractor)` builds a full comparator from a key-extraction function, avoiding hand-written `compare` method bodies for single-key sorts.
- `.thenComparing(...)` chains tie-breaking comparators, each one only consulted if every comparator before it in the chain returned exactly `0`.
- `.reversed()` (on any comparator) or `Comparator.reverseOrder()` (for natural ordering) flips sort direction without writing a separate comparator from scratch.
- `Comparator.nullsFirst(comparator)`/`nullsLast(comparator)` handle `null` values gracefully, sorting them to one end instead of throwing `NullPointerException` when the underlying comparator would otherwise fail on a `null`.
- These builder methods express multi-key, reversed, and null-tolerant sorting in the natural primary-to-tertiary reading order, replacing the more error-prone and less readable manual multi-pass-sort-relying-on-stability technique.
