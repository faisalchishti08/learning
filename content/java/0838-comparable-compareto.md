---
card: java
gi: 838
slug: comparable-compareto
title: Comparable & compareTo
---

## 1. What it is

`Comparable<T>` is a single-method interface a class implements to define its own **natural ordering** — the default "sorted order" for that type. Its one method, `compareTo(T other)`, returns a negative number if `this` should sort before `other`, zero if they're considered equal for ordering purposes, and a positive number if `this` should sort after `other`. Any class implementing `Comparable` can be sorted with `Collections.sort(list)` or `list.sort(null)` without any external comparator, used directly as keys in a [`TreeMap`](0825-treemap-red-black-tree.md)/[`TreeSet`](0819-treeset.md) without a supplied `Comparator`, and compared with `<`-style semantics via its return value's sign.

## 2. Why & when

Many types have one obvious, dominant ordering — numbers order numerically, strings order lexicographically, dates order chronologically — and it would be tedious to require an external `Comparator` every single time such a type needs sorting. `Comparable` lets a type declare that ordering once, as part of its own definition, so every piece of code that sorts a list of that type gets sensible behavior "for free," without needing to know or supply the details. Implement `Comparable` on a custom class specifically when there genuinely *is* one obvious, canonical ordering that most callers would expect by default — a `Money` amount by its numeric value, an `Event` by its timestamp. When a type has multiple *equally valid* orderings depending on context (a `Person` sorted by name in one screen, by age in another), a supplied [`Comparator`](0839-comparator-compare.md) is the better tool, since `Comparable` only ever lets a type declare a single ordering.

## 3. Core concept

```java
public class Money implements Comparable<Money> {
    final int cents;
    Money(int cents) { this.cents = cents; }

    @Override
    public int compareTo(Money other) {
        return Integer.compare(this.cents, other.cents); // negative, zero, or positive
    }
}

List<Money> prices = new ArrayList<>(List.of(new Money(500), new Money(150), new Money(300)));
Collections.sort(prices); // works directly -- no Comparator needed, since Money is Comparable
```

`Integer.compare(a, b)` is the idiomatic way to implement a numeric `compareTo` — it correctly returns negative/zero/positive without the classic overflow bug that a naive `return a - b` can introduce for values near `Integer.MIN_VALUE`/`MAX_VALUE`.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="compareTo's return value sign determines relative order: negative means this comes first, zero means equal for ordering, positive means this comes after">
  <g font-family="sans-serif">
    <rect x="40" y="30" width="160" height="45" rx="6" fill="#1c2430" stroke="#3fb950"/>
    <text x="120" y="57" fill="#3fb950" font-size="12" text-anchor="middle">negative</text>
    <text x="120" y="100" fill="#8b949e" font-size="10" text-anchor="middle">this sorts BEFORE other</text>

    <rect x="240" y="30" width="160" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
    <text x="320" y="57" fill="#79c0ff" font-size="12" text-anchor="middle">zero</text>
    <text x="320" y="100" fill="#8b949e" font-size="10" text-anchor="middle">equal for ordering purposes</text>

    <rect x="440" y="30" width="160" height="45" rx="6" fill="#1c2430" stroke="#f0883e"/>
    <text x="520" y="57" fill="#f0883e" font-size="12" text-anchor="middle">positive</text>
    <text x="520" y="100" fill="#8b949e" font-size="10" text-anchor="middle">this sorts AFTER other</text>
  </g>
</svg>

*`compareTo`'s return value sign — not its magnitude — is what determines relative order.*

## 5. Runnable example

Scenario: sorting a list of employees, growing from basic single-field natural ordering, to a multi-field tie-breaking implementation, to demonstrating (and fixing) a subtle contract violation that silently corrupts sorting.

### Level 1 — Basic

```java
import java.util.*;

public class EmployeeBasic {
    static class Employee implements Comparable<Employee> {
        final String name;
        final int age;
        Employee(String name, int age) { this.name = name; this.age = age; }

        @Override
        public int compareTo(Employee other) {
            return Integer.compare(this.age, other.age); // natural ordering: by age, ascending
        }

        @Override public String toString() { return name + "(" + age + ")"; }
    }

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Charlie", 35), new Employee("Alice", 28), new Employee("Bob", 42)
        ));

        Collections.sort(employees); // works directly -- Employee IS Comparable
        System.out.println("sorted by age: " + employees);
    }
}
```

**How to run:** `java EmployeeBasic.java` (JDK 17+).

Expected output:
```
sorted by age: [Alice(28), Charlie(35), Bob(42)]
```

`Collections.sort(employees)` requires no external comparator argument at all — it works purely because `Employee` declares its natural ordering via `Comparable`.

### Level 2 — Intermediate

```java
import java.util.*;

public class EmployeeTieBreaking {
    static class Employee implements Comparable<Employee> {
        final String name;
        final int age;
        Employee(String name, int age) { this.name = name; this.age = age; }

        @Override
        public int compareTo(Employee other) {
            int ageComparison = Integer.compare(this.age, other.age);
            if (ageComparison != 0) return ageComparison; // primary key: age
            return this.name.compareTo(other.name);        // tie-breaker: name, alphabetically
        }

        @Override public String toString() { return name + "(" + age + ")"; }
    }

    public static void main(String[] args) {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Dave", 30), new Employee("Alice", 30), new Employee("Bob", 25)
        ));

        Collections.sort(employees);
        System.out.println("sorted by age, then name for ties: " + employees);
    }
}
```

**How to run:** `java EmployeeTieBreaking.java`.

Expected output:
```
sorted by age, then name for ties: [Bob(25), Alice(30), Dave(30)]
```

The real-world concern added: two employees sharing the same age (30) need a deterministic, stable tie-breaking rule — `compareTo` first compares by `age`, and only when that comparison is exactly `0` (a genuine tie) does it fall through to comparing by `name`, correctly ordering `Alice` before `Dave`.

### Level 3 — Advanced

```java
import java.util.*;

public class BrokenComparableDemo {
    static class BuggyMoney implements Comparable<BuggyMoney> {
        final int cents;
        BuggyMoney(int cents) { this.cents = cents; }

        @Override
        public int compareTo(BuggyMoney other) {
            return this.cents - other.cents; // BUGGY: can overflow for extreme values
        }

        @Override public String toString() { return "$" + (cents / 100.0); }
    }

    static class FixedMoney implements Comparable<FixedMoney> {
        final int cents;
        FixedMoney(int cents) { this.cents = cents; }

        @Override
        public int compareTo(FixedMoney other) {
            return Integer.compare(this.cents, other.cents); // FIXED: never overflows
        }

        @Override public String toString() { return "$" + (cents / 100.0); }
    }

    public static void main(String[] args) {
        List<BuggyMoney> buggyPrices = new ArrayList<>(List.of(
            new BuggyMoney(Integer.MAX_VALUE - 100), new BuggyMoney(Integer.MIN_VALUE + 100), new BuggyMoney(0)
        ));
        Collections.sort(buggyPrices);
        System.out.println("buggy sort result (subtraction can overflow near INT boundaries): " + buggyPrices);

        List<FixedMoney> fixedPrices = new ArrayList<>(List.of(
            new FixedMoney(Integer.MAX_VALUE - 100), new FixedMoney(Integer.MIN_VALUE + 100), new FixedMoney(0)
        ));
        Collections.sort(fixedPrices);
        System.out.println("fixed sort result (Integer.compare never overflows): " + fixedPrices);
    }
}
```

**How to run:** `java BrokenComparableDemo.java`. The buggy version's exact incorrect ordering can vary by JVM/sort algorithm internals since it depends on undefined behavior from overflow, but it is **not reliably guaranteed to sort correctly** — while the fixed version always produces the mathematically correct order, every time.

Expected output shape (buggy output specifically may vary or coincidentally look correct on some inputs/JVMs — that unpredictability is exactly the point):
```
buggy sort result (subtraction can overflow near INT boundaries): [$-21474836.48, $0.0, $21474835.47]
fixed sort result (Integer.compare never overflows): [$-21474835.47, $0.0, $21474836.47]
```

This adds the production-flavored hard case: the classic `return a - b` `compareTo` implementation, which looks correct and works fine for typical values, but silently breaks for values near `Integer.MIN_VALUE`/`MAX_VALUE` because the subtraction itself can overflow and wrap around to the opposite sign — violating `compareTo`'s contract without throwing any exception, and producing sorting results that are subtly, silently wrong. `Integer.compare(a, b)` (or `Long.compare`, `Double.compare` for other primitive types) never has this problem, since it's implemented specifically to avoid the overflow trap.

## 6. Walkthrough

Tracing the difference between `BuggyMoney` and `FixedMoney` during `Collections.sort`:

1. `Collections.sort` internally calls `compareTo` repeatedly between pairs of elements to determine their relative order, using whatever sorting algorithm the JDK's `List.sort`/`Collections.sort` implementation uses internally (a variant of merge sort/TimSort for objects).
2. For `BuggyMoney.compareTo`, comparing an element near `Integer.MAX_VALUE` against one near `Integer.MIN_VALUE` computes `this.cents - other.cents` — a large positive number minus a large negative number. This subtraction can overflow the 32-bit `int` range, wrapping around to an incorrect sign entirely (a mathematically positive difference can appear negative after overflow, or vice versa).
3. Because `compareTo`'s contract requires its result to correctly and consistently indicate relative order, this overflow directly violates that contract — the sort algorithm, trusting `compareTo`'s reported sign, can place elements in an incorrect relative position, and because different sort algorithms probe different pairs of elements, the exact resulting (wrong) order isn't even deterministic across different JDK versions or list sizes.
4. `FixedMoney.compareTo` instead calls `Integer.compare(this.cents, other.cents)`, which is implemented internally using conditional branches (essentially `(a < b) ? -1 : (a == b) ? 0 : 1`) rather than subtraction — this never overflows, regardless of how close `a` and `b` are to the `int` range's boundaries, so the sort always produces the mathematically correct result.
5. Printing both lists side by side shows the fixed version consistently sorted correctly (`Integer.MIN_VALUE`-adjacent value first, then zero, then `Integer.MAX_VALUE`-adjacent value), while the buggy version's result depends on the overflow's exact effect on the specific comparisons the sort algorithm happened to make.

## 7. Gotchas & takeaways

> **Gotcha:** never implement a numeric `compareTo` (or `Comparator`) using subtraction (`return a - b`) — it silently overflows for values near the primitive type's boundaries, corrupting sort order without ever throwing an exception. Always use `Integer.compare(a, b)`, `Long.compare(a, b)`, `Double.compare(a, b)`, or the equivalent for the relevant primitive type, which are implemented to avoid this trap entirely.

- `Comparable<T>`'s single method, `compareTo(T other)`, defines a type's natural ordering — negative/zero/positive indicates before/equal/after.
- Implementing `Comparable` lets a type be sorted directly (`Collections.sort`, `list.sort(null)`) and used as `TreeMap`/`TreeSet` keys without an external comparator.
- Chain multiple fields in `compareTo` by checking each in priority order, falling through to the next only when the current comparison returns exactly `0` (a genuine tie).
- Never implement a numeric comparison via subtraction — use `Integer.compare`/`Long.compare`/`Double.compare` to avoid silent overflow bugs.
- Reach for `Comparable` when a type has one obvious, canonical default ordering; use an external [`Comparator`](0839-comparator-compare.md) instead when multiple valid orderings need to coexist depending on context.
