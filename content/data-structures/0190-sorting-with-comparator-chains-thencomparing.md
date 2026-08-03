---
card: data-structures
gi: 190
slug: sorting-with-comparator-chains-thencomparing
title: Sorting with Comparator chains (thenComparing)
---

## 1. What it is

`Comparator` chaining is a fluent, method-chaining style (`Comparator.comparing(...).thenComparing(...).reversed()`) for building multi-key sort orders — "sort by department first, then by salary within each department, descending" — without writing a manual `if/else` comparison method.

## 2. Why & when

Multi-key sorting comes up constantly: sort a leaderboard by score, then by name for ties; sort log entries by date, then by severity. Hand-writing this comparison logic with nested `if` statements is verbose and error-prone (easy to get a tie-break backward, or forget one). `Comparator`'s builder methods — `comparing`, `thenComparing`, `reversed`, `nullsFirst`/`nullsLast` — express the same logic declaratively, in the order the keys should be considered.

## 3. Core concept

**The building blocks.**
- `Comparator.comparing(keyExtractor)`: builds a comparator from a function that extracts a `Comparable` key from each element (e.g. `Employee::getSalary`).
- `Comparator.comparing(keyExtractor, keyComparator)`: same, but with an explicit `Comparator` for the extracted key, for keys that are not naturally `Comparable` or need custom ordering.
- `.thenComparing(keyExtractor)`: chained onto an existing comparator, this only takes effect when the primary comparator considers two elements **equal** (`compare` returns `0`) — it breaks ties, and does not override the primary ordering.
- `.reversed()`: flips the sense of whatever comparator it is called on, without needing to rewrite the underlying logic.
- `Comparator.nullsFirst(comparator)` / `Comparator.nullsLast(comparator)`: wraps a comparator to handle `null` elements gracefully, sorting them to one end instead of throwing `NullPointerException`.

**Why `thenComparing` only applies on ties.** This is the entire point of multi-key sorting: the first key is decisive whenever it differs between two elements. The second key exists purely to resolve the ambiguous case where the first key does not distinguish them. A chain can have any number of `thenComparing` calls, each only ever consulted if every earlier key in the chain tied.

**Primitive-specialized variants avoid boxing overhead.** `Comparator.comparingInt(...)`, `comparingLong(...)`, `comparingDouble(...)` extract a primitive directly (instead of a boxed `Integer`/`Long`/`Double`), avoiding unnecessary autoboxing during the sort — a minor performance detail, but idiomatic Java for numeric keys.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A comparator chain deciding order by department first, falling through to salary only when departments tie">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">Comparator.comparing(Employee::department).thenComparing(Employee::salary)</text>

    <text x="10" y="60">compare(A, B):</text>
    <rect x="120" y="45" width="160" height="30" fill="#161b22" stroke="#79c0ff"/>
    <text x="200" y="65" text-anchor="middle" font-size="9">department differs?</text>

    <line x1="200" y1="75" x2="120" y2="110" stroke="#79c0ff"/>
    <text x="60" y="130" font-size="9" fill="#3fb950">yes -&gt; done, department decides</text>

    <line x1="200" y1="75" x2="280" y2="110" stroke="#79c0ff"/>
    <text x="220" y="130" font-size="9" fill="#f0883e">no (tie) -&gt; fall through to thenComparing(salary)</text>

    <rect x="220" y="140" width="160" height="30" fill="#161b22" stroke="#f0883e"/>
    <text x="300" y="160" text-anchor="middle" font-size="9">salary decides the tie</text>
  </g>
</svg>

Each `thenComparing` step only runs when every earlier key produced a tie.

## 5. Runnable example

```java
// ComparatorChains.java
import java.util.*;

public class ComparatorChains {

    record Employee(String name, String department, int salary) {}

    // Basic: a single-key sort using Comparator.comparing.
    static void basicLevel() {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Dana", "Engineering", 90000),
            new Employee("Amir", "Sales", 75000),
            new Employee("Bo", "Engineering", 95000)));

        employees.sort(Comparator.comparing(Employee::name));
        System.out.println("basic: sorted by name -> " + employees);
    }

    // Intermediate: multi-key sort with thenComparing, breaking ties on a second field.
    static void intermediateLevel() {
        List<Employee> employees = new ArrayList<>(List.of(
            new Employee("Dana", "Engineering", 90000),
            new Employee("Amir", "Engineering", 90000), // same department AND same salary as Dana
            new Employee("Bo", "Sales", 95000)));

        employees.sort(
            Comparator.comparing(Employee::department)
                .thenComparingInt(Employee::salary)
                .thenComparing(Employee::name)); // third-level tie-break

        System.out.println("intermediate: sorted by dept, then salary, then name -> " + employees);
    }

    // Advanced: reversed() combined with thenComparing, plus nullsLast for optional fields.
    record Task(String title, Integer priority) {} // priority may be null (unset)

    static void advancedLevel() {
        List<Task> tasks = new ArrayList<>(List.of(
            new Task("Deploy", 1),
            new Task("Investigate bug", null),
            new Task("Write docs", 3),
            new Task("Fix outage", 1)));

        Comparator<Task> byPriority = Comparator.comparing(Task::priority, Comparator.nullsLast(Comparator.naturalOrder()));
        tasks.sort(byPriority.thenComparing(Task::title));

        System.out.println("advanced: sorted by priority (nulls last), then title -> " + tasks);

        tasks.sort(byPriority.reversed()); // highest priority number first, nulls now come FIRST (reversed nulls-last)
        System.out.println("advanced: reversed priority order -> " + tasks);
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java ComparatorChains.java`

## 6. Walkthrough

For the multi-key example: `Dana` and `Amir` both work in `"Engineering"` and both earn `90000`. `Comparator.comparing(Employee::department)` compares `"Engineering"` vs `"Sales"` for the full set — `Bo` (Sales) sorts after both Engineering employees. Between `Dana` and `Amir`, department comparison returns `0` (a tie), so the chain falls through to `.thenComparingInt(Employee::salary)` — but their salaries are also equal (`90000` each), another tie. The chain falls through again to `.thenComparing(Employee::name)`, which finally distinguishes them: `"Amir"` sorts before `"Dana"` alphabetically. Final order: `Amir, Dana, Bo`.

For the `nullsLast` example: `Comparator.comparing(Task::priority, Comparator.nullsLast(Comparator.naturalOrder()))` builds a comparator that extracts each task's `priority` (which may be `null`), then compares those values using natural ordering, but treats `null` as "sorts after everything else" instead of throwing `NullPointerException` (which plain `Comparator.naturalOrder()` would do on a `null` input). Sorting `[Deploy(1), Investigate bug(null), Write docs(3), Fix outage(1)]` by this chain, then by title as a tie-break, produces `[Deploy(1), Fix outage(1), Write docs(3), Investigate bug(null)]` — the two priority-`1` tasks tie-break alphabetically, and the `null`-priority task sinks to the end.

Calling `.reversed()` on the whole chain flips the **entire** comparison sense, including how `nulls` are treated — `nullsLast` becomes effectively "nulls first" under the reversal, since reversing flips every comparison outcome, including the ones that placed `null` at the end.

**Complexity.** Building a comparator chain is `O(1)` — it only wraps function references, doing no actual comparison work until the sort runs. The sort itself is `O(n log n)`, with each comparison costing `O(k)` for `k` chained keys in the worst case (when many elements tie on early keys and the chain must fall through several levels).

## 7. Gotchas & takeaways

> `thenComparing` only ever activates on a **tie** from everything before it in the chain — a common mistake is expecting a later key in the chain to somehow "average" or "combine" with an earlier key, when in fact it is purely a tie-breaker, consulted only when the earlier comparison returned exactly `0`.

- Use the primitive-specialized `thenComparingInt`/`thenComparingLong`/`thenComparingDouble` for numeric tie-breaks — cleaner than `thenComparing` with a boxed type, and avoids unnecessary autoboxing.
- `Comparator.nullsFirst`/`nullsLast` should wrap the **key comparator**, not the whole chain, when only one specific field can be `null` — wrapping the entire chain in `nullsFirst` would instead handle the case where an entire element (not just one field) is `null`.
- Order matters: `.thenComparing(a).thenComparing(b)` is not the same as `.thenComparing(b).thenComparing(a)` — list the keys in priority order, most important first, exactly as you would explain the sort rule in plain English.
