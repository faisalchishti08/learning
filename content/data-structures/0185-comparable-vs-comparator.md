---
card: data-structures
gi: 185
slug: comparable-vs-comparator
title: Comparable vs Comparator
---

## 1. What it is

`Comparable<T>` is an interface a class implements to define its own single, **natural** ordering (`compareTo`). `Comparator<T>` is a separate interface for defining an ordering **externally**, without touching the class being compared — and you can define as many different `Comparator`s as you need for the same type.

## 2. Why & when

Use `Comparable` when a type has one obvious, intrinsic ordering that almost every caller would want — `Integer` compares by numeric value, `String` compares lexicographically. Use `Comparator` when you need an ordering that is situational, that the class does not (or cannot) define itself, or when you need multiple different orderings for the same type — sorting `Employee` objects by name in one place and by salary in another.

## 3. Core concept

**The single-method contracts.** `Comparable<T>`: one method, `int compareTo(T other)`, implemented **inside** the class being compared. `Comparator<T>`: one method, `int compare(T a, T b)`, implemented **outside** the class, as a separate object.

**The return-value convention, shared by both.** A negative number means the first argument sorts before the second; zero means they are equal for ordering purposes; a positive number means the first argument sorts after the second. `Collections.sort`, `TreeMap`, `TreeSet`, and `PriorityQueue` all rely on this exact convention.

**Why a class can only have one `Comparable` ordering but unlimited `Comparator`s.** `compareTo` is a method on the class itself — a class only has one implementation of any given method. `Comparator` objects are separate, so you can define `Comparator.comparing(Employee::getSalary)` in one place and `Comparator.comparing(Employee::getName)` in another, and pass whichever one fits the current sorting need, without modifying `Employee` at all.

**Sorting with each.** `Collections.sort(list)` (no second argument) uses the elements' natural `Comparable` ordering — the list's elements must implement `Comparable`, or this throws a `ClassCastException`. `Collections.sort(list, comparator)` (or `list.sort(comparator)`) uses the supplied `Comparator` instead, overriding or supplying an ordering regardless of whether the elements implement `Comparable`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Comparable defined inside a class as its one natural ordering, versus multiple external Comparator objects providing different orderings for the same class">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <rect x="40" y="20" width="200" height="80" fill="#161b22" stroke="#79c0ff"/>
    <text x="140" y="40" text-anchor="middle">class Employee implements Comparable</text>
    <text x="140" y="60" text-anchor="middle" font-size="9">compareTo(other) -&gt; by id</text>
    <text x="140" y="80" text-anchor="middle" font-size="9">(one, built-in, natural ordering)</text>

    <rect x="330" y="10" width="260" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="460" y="30" text-anchor="middle" font-size="9">Comparator.comparing(Employee::getSalary)</text>
    <rect x="330" y="50" width="260" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="460" y="70" text-anchor="middle" font-size="9">Comparator.comparing(Employee::getName)</text>
    <rect x="330" y="90" width="260" height="30" fill="#0d1117" stroke="#f0883e"/>
    <text x="460" y="110" text-anchor="middle" font-size="9">Comparator.comparing(Employee::getHireDate)</text>
    <text x="460" y="140" text-anchor="middle" font-size="9" fill="#8b949e">unlimited external orderings, no class changes needed</text>
  </g>
</svg>

One `Comparable` ordering lives inside the class; any number of `Comparator` orderings live outside it.

## 5. Runnable example

```java
// ComparableVsComparator.java
import java.util.*;

public class ComparableVsComparator {

    record Employee(String name, int salary, String department) {}

    // Basic: a class implementing Comparable for its one natural ordering (by name).
    static class Person implements Comparable<Person> {
        String name;
        int age;

        Person(String name, int age) { this.name = name; this.age = age; }

        @Override
        public int compareTo(Person other) {
            return this.name.compareTo(other.name); // natural order: alphabetical by name
        }

        @Override
        public String toString() { return name + "(" + age + ")"; }
    }

    static void basicLevel() {
        List<Person> people = new ArrayList<>(List.of(
            new Person("Charlie", 35), new Person("Alice", 28), new Person("Bob", 42)));
        Collections.sort(people); // uses Comparable's compareTo -- natural order by name

        System.out.println("basic: sorted by natural order (name) -> " + people);
    }

    // Intermediate: Comparator objects providing alternative orderings without modifying the Employee record.
    static void intermediateLevel() {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Dana", 90000, "Engineering"),
            new Employee("Amir", 75000, "Sales"),
            new Employee("Bo", 95000, "Engineering")));

        employees.sort(Comparator.comparing(Employee::salary));
        System.out.println("intermediate: sorted by salary -> " + employees);

        employees.sort(Comparator.comparing(Employee::name));
        System.out.println("intermediate: sorted by name -> " + employees);
    }

    // Advanced: chaining Comparators with thenComparing for multi-key sorting, and reversed() for descending order.
    static void advancedLevel() {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Dana", 90000, "Engineering"),
            new Employee("Amir", 90000, "Sales"),
            new Employee("Bo", 95000, "Engineering")));

        employees.sort(
            Comparator.comparing(Employee::salary).reversed()
                .thenComparing(Employee::name));

        System.out.println("advanced: sorted by salary desc, then name asc -> " + employees);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ComparableVsComparator.java`

## 6. Walkthrough

`Person` implements `Comparable<Person>`, defining `compareTo` to compare by `name`. Calling `Collections.sort(people)` with no second argument uses this natural ordering directly — Java calls each pair's `compareTo` internally during the sort, producing `[Alice(28), Bob(42), Charlie(35)]`.

`Employee` is a plain record with **no** `Comparable` implementation. To sort it, you must supply a `Comparator` explicitly. `Comparator.comparing(Employee::salary)` builds a comparator that extracts each employee's salary and compares those numbers — sorting produces ascending salary order. Calling `employees.sort(Comparator.comparing(Employee::name))` right after re-sorts the **same list** by a completely different key, with zero changes to the `Employee` type itself.

For chained sorting: `Comparator.comparing(Employee::salary).reversed().thenComparing(Employee::name)` builds a single comparator that first compares by salary in **descending** order (via `.reversed()`), and only when two employees have the **same** salary, falls back to comparing by name in ascending order (via `.thenComparing`). This is why `Amir` (salary `90000`) and `Dana` (salary `90000`) both come after `Bo` (salary `95000`, sorted first), but between themselves, `Amir` comes before `Dana` alphabetically.

**Complexity.** Building a `Comparator` chain (`comparing`, `reversed`, `thenComparing`) is `O(1)` — it just wraps function references. The sort itself is `O(n log n)`, same as any comparison-based sort, regardless of whether the comparison logic comes from `Comparable` or an external `Comparator`.

## 7. Gotchas & takeaways

> A `compareTo` (or `compare`) implementation must be **consistent**: if `a.compareTo(b) < 0`, then `b.compareTo(a)` must be `> 0`, and if two elements compare as equal, sorting them in either order must be acceptable. An inconsistent comparator can cause `Collections.sort` or a `TreeMap`/`TreeSet` to behave unpredictably or throw `IllegalArgumentException: Comparison method violates its general contract!`.

- It is a strong convention (though not enforced by the compiler) that `compareTo` returning `0` should agree with `equals` returning `true` for the same pair — violating this ("inconsistent with equals") can cause surprising behavior in sorted collections like `TreeSet`, where equality for storage purposes is determined by `compareTo`, not `equals`.
- Prefer the `Comparator.comparing(...)`, `.reversed()`, `.thenComparing(...)` builder chain over hand-writing comparison logic — it is shorter, less error-prone, and self-documenting about which fields matter and in what order.
- Implement `Comparable` on a class only when there is truly one obvious natural ordering everyone would expect; if the ordering is context-dependent, prefer external `Comparator`s instead of forcing an arbitrary "natural" choice into the class.
