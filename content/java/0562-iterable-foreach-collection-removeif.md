---
card: java
gi: 562
slug: iterable-foreach-collection-removeif
title: Iterable.forEach() / Collection.removeIf()
---

## 1. What it is

Java 8 added two default methods that cover the two most common loop-and-mutate patterns: `Iterable.forEach(action)` runs a lambda once per element (an internal-iteration replacement for the classic `for` loop), and `Collection.removeIf(predicate)` removes every element matching a predicate in one call, safely, without the caller manually driving an `Iterator`.

## 2. Why & when

Two patterns were extremely common and easy to get subtly wrong before Java 8. First, iterating just to call something on each element (`for (String s : list) { System.out.println(s); }`) — `forEach` expresses the same thing as one expression, and can be handed a method reference directly (`list.forEach(System.out::println)`). Second, removing elements while iterating — doing this with a plain `for-each` loop throws `ConcurrentModificationException`, forcing you to use an explicit `Iterator` and call `iterator.remove()`. `removeIf(predicate)` does that internally and correctly, so you never write the iterator dance yourself. Use `forEach` for simple side-effecting iteration, and `removeIf` any time you'd otherwise write "remove every element where...".

## 3. Core concept

```java
List<Integer> numbers = new ArrayList<>(List.of(1, 2, 3, 4, 5, 6));

numbers.forEach(n -> System.out.println("Value: " + n));

numbers.removeIf(n -> n % 2 == 0); // removes all even numbers in place
System.out.println(numbers); // [1, 3, 5]
```

`forEach` is defined on `Iterable` (so it works on any `List`, `Set`, etc., but not on `Map` directly — `Map` has its own `forEach(BiConsumer)` taking key and value). `removeIf` is defined on `Collection` and returns `boolean` — `true` if any element was actually removed.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="removeIf scans a collection and deletes every element matching the predicate in one safe pass">
  <text x="20" y="25" fill="#8b949e" font-size="11" font-family="sans-serif">before: [1, 2, 3, 4, 5, 6]</text>
  <g font-family="monospace" font-size="13">
    <rect x="20" y="35" width="34" height="30" fill="#1c2430" stroke="#e6edf3"/><text x="37" y="55" fill="#e6edf3" text-anchor="middle">1</text>
    <rect x="60" y="35" width="34" height="30" fill="#1c2430" stroke="#f85149"/><text x="77" y="55" fill="#f85149" text-anchor="middle">2</text>
    <rect x="100" y="35" width="34" height="30" fill="#1c2430" stroke="#e6edf3"/><text x="117" y="55" fill="#e6edf3" text-anchor="middle">3</text>
    <rect x="140" y="35" width="34" height="30" fill="#1c2430" stroke="#f85149"/><text x="157" y="55" fill="#f85149" text-anchor="middle">4</text>
    <rect x="180" y="35" width="34" height="30" fill="#1c2430" stroke="#e6edf3"/><text x="197" y="55" fill="#e6edf3" text-anchor="middle">5</text>
    <rect x="220" y="35" width="34" height="30" fill="#1c2430" stroke="#f85149"/><text x="237" y="55" fill="#f85149" text-anchor="middle">6</text>
  </g>
  <text x="260" y="55" fill="#8b949e" font-size="10" font-family="sans-serif">(red = matches n % 2 == 0, marked for removal)</text>

  <text x="20" y="100" fill="#8b949e" font-size="11" font-family="sans-serif">after removeIf(n -&gt; n % 2 == 0):</text>
  <g font-family="monospace" font-size="13">
    <rect x="20" y="110" width="34" height="30" fill="#1c2430" stroke="#6db33f"/><text x="37" y="130" fill="#6db33f" text-anchor="middle">1</text>
    <rect x="60" y="110" width="34" height="30" fill="#1c2430" stroke="#6db33f"/><text x="77" y="130" fill="#6db33f" text-anchor="middle">3</text>
    <rect x="100" y="110" width="34" height="30" fill="#1c2430" stroke="#6db33f"/><text x="117" y="130" fill="#6db33f" text-anchor="middle">5</text>
  </g>
</svg>

removeIf deletes every matching element in one call — no manual Iterator, no ConcurrentModificationException.

## 5. Runnable example

Scenario: managing a task list — starting with printing tasks via `forEach`, then removing completed tasks with `removeIf`, then building a cleanup routine that logs each removal as it happens using `forEach` and `removeIf` together with a counter.

### Level 1 — Basic

```java
import java.util.*;

public class TaskListBasic {
    public static void main(String[] args) {
        List<String> tasks = List.of("Write report", "Review PR", "Deploy release");
        tasks.forEach(task -> System.out.println("- " + task));
    }
}
```

**How to run:** `java TaskListBasic.java`

Expected output:
```
- Write report
- Review PR
- Deploy release
```

`tasks.forEach(task -> System.out.println("- " + task))` performs **internal iteration**: the `List` implementation itself drives the loop and calls the lambda once per element, in encounter order for an ordered collection like `List`. This is functionally identical to a `for-each` loop but reads as a single expression, and composes cleanly with method references (`tasks.forEach(System.out::println)` would work too, minus the `"- "` prefix).

### Level 2 — Intermediate

```java
import java.util.*;

public class TaskListCleanup {
    record Task(String name, boolean completed) {}

    public static void main(String[] args) {
        List<Task> tasks = new ArrayList<>(List.of(
            new Task("Write report", true),
            new Task("Review PR", false),
            new Task("Deploy release", true),
            new Task("Fix bug", false)
        ));

        boolean anyRemoved = tasks.removeIf(Task::completed);

        System.out.println("Any removed: " + anyRemoved);
        tasks.forEach(t -> System.out.println("- " + t.name()));
    }
}
```

**How to run:** `java TaskListCleanup.java`

Expected output:
```
Any removed: true
- Review PR
- Fix bug
```

The real-world concern this adds: **safely mutating** a list while conceptually "iterating" it — removing every completed task in one call. `tasks.removeIf(Task::completed)` internally uses an `Iterator` and calls `iterator.remove()` for each matching element, avoiding the `ConcurrentModificationException` that a plain `for-each` loop combined with `list.remove(...)` would throw. The `boolean` return value reports whether the list actually changed, useful for deciding whether to log or take further action.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public class TaskListAudit {
    record Task(String name, boolean completed) {}

    static int removeAndLog(List<Task> tasks, String reason) {
        AtomicInteger removedCount = new AtomicInteger(0);

        // First, report what's about to be removed (forEach can't remove safely itself).
        tasks.stream()
             .filter(Task::completed)
             .forEach(t -> System.out.println("Removing '" + t.name() + "' (" + reason + ")"));

        tasks.removeIf(t -> {
            boolean shouldRemove = t.completed();
            if (shouldRemove) removedCount.incrementAndGet();
            return shouldRemove;
        });

        return removedCount.get();
    }

    public static void main(String[] args) {
        List<Task> tasks = new ArrayList<>(List.of(
            new Task("Write report", true),
            new Task("Review PR", false),
            new Task("Deploy release", true),
            new Task("Fix bug", false)
        ));

        int removed = removeAndLog(tasks, "end of sprint cleanup");

        System.out.println("Removed " + removed + " task(s).");
        System.out.println("Remaining:");
        tasks.forEach(t -> System.out.println("- " + t.name()));
    }
}
```

**How to run:** `java TaskListAudit.java`

Expected output:
```
Removing 'Write report' (end of sprint cleanup)
Removing 'Deploy release' (end of sprint cleanup)
Removed 2 task(s).
Remaining:
- Review PR
- Fix bug
```

This handles the production-flavoured concern of **auditing a bulk removal** — logging exactly what will be deleted and counting how many were removed, which `removeIf`'s plain `boolean` return doesn't give you on its own. Because the predicate lambda passed to `removeIf` runs once per matching element and can have side effects, an `AtomicInteger` counter is incremented inside it to track the exact count, avoiding a separate pass just to count.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `tasks` holds four `Task` records: two completed (`Write report`, `Deploy release`), two not (`Review PR`, `Fix bug`).

`removeAndLog(tasks, "end of sprint cleanup")` is called. Inside, `removedCount` starts at `0`. The stream pipeline `tasks.stream().filter(Task::completed).forEach(...)` runs first, purely for logging: it filters to the two completed tasks and prints a "Removing..." line for each, in encounter order — `Write report`, then `Deploy release`. This pass does **not** modify `tasks` at all; it only reads.

Next, `tasks.removeIf(t -> {...})` runs. For each element in `tasks`, the lambda is evaluated:

```
t=Write report (completed=true)  -> shouldRemove=true  -> removedCount: 0->1 -> return true  (removed)
t=Review PR    (completed=false) -> shouldRemove=false  -> removedCount stays 1 -> return false (kept)
t=Deploy release (completed=true)-> shouldRemove=true   -> removedCount: 1->2 -> return true  (removed)
t=Fix bug      (completed=false) -> shouldRemove=false  -> removedCount stays 2 -> return false (kept)
```

`removeIf` internally uses an `Iterator` over `tasks` and calls `iterator.remove()` immediately whenever the predicate returns `true`, so `Write report` and `Deploy release` are excised from the underlying `ArrayList` in place, leaving `tasks = [Review PR, Fix bug]`.

`removeAndLog` returns `removedCount.get()`, which is `2`. Back in `main`, `removed` is `2`, so `"Removed 2 task(s)."` is printed. Finally, `tasks.forEach(...)` iterates the now-shrunk list and prints the two survivors: `Review PR` and `Fix bug`.

## 7. Gotchas & takeaways

> Calling `list.remove(element)` or `list.add(element)` **inside** a `forEach` lambda (or inside a plain `for-each` loop) throws `ConcurrentModificationException` — `forEach` is for read-only side effects (printing, logging, accumulating into a *separate* structure), not for mutating the collection being iterated. If you need to remove elements, use `removeIf`; if you need to transform elements in place, use `List.replaceAll(...)` instead.

- `forEach` performs internal iteration and guarantees encounter order for ordered sources (`List`); for unordered sources (`HashSet`), the order is unspecified, same as a regular loop over that collection would be.
- `removeIf` returns `true` if the collection was modified (at least one element removed), `false` otherwise — useful for conditional follow-up logic without a separate size comparison.
- `removeIf`'s predicate can have side effects (as in the Level 3 example), but keep them read-only with respect to the collection being modified — mutating `tasks` from inside the predicate itself would still risk `ConcurrentModificationException`.
- `Map` does not implement `Iterable<Entry>` directly, so it has its own `forEach(BiConsumer<K, V>)` taking key and value separately, rather than the single-argument `Iterable.forEach`.
- For transforming (not removing) every element in place, use `List.replaceAll(UnaryOperator)` — conceptually the `List` sibling of `Map.replaceAll`.
