---
card: java
gi: 513
slug: groupingby
title: groupingBy()
---

## 1. What it is

`Collectors.groupingBy(classifier)` collects a stream into a `Map<K, List<T>>`, where `classifier` is a function that computes each element's grouping key, and every element with the same key ends up together in that key's `List`. It's the streams equivalent of a manual loop building a `HashMap<K, List<T>>` with `computeIfAbsent(key, k -> new ArrayList<>()).add(element)` — done as a single, declarative collector call.

## 2. Why & when

Grouping data by some derived property is one of the most common data-processing needs: orders by customer, employees by department, log entries by severity, students by grade. `groupingBy` expresses this directly: give it a function that says "what group does this element belong to?" and it handles building the `Map`, creating new group lists as needed, and appending elements to the right group — all in one pass over the source stream.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

record Employee(String name, String department) {}

List<Employee> employees = List.of(
        new Employee("Alice", "Engineering"),
        new Employee("Bob", "Sales"),
        new Employee("Carol", "Engineering")
);

Map<String, List<Employee>> byDepartment = employees.stream()
        .collect(Collectors.groupingBy(Employee::department));
// {Engineering=[Alice, Carol], Sales=[Bob]}
```

Every distinct value the classifier function produces becomes a key in the resulting `Map`, with a `List` of all elements that mapped to that key.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="groupingBy sorts elements into buckets keyed by a classifier function's result">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="70" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="55" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Alice</text>
  <rect x="100" y="20" width="70" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="135" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Bob</text>
  <rect x="180" y="20" width="70" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="215" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Carol</text>
  <text x="130" y="65" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">groupingBy(department)</text>
  <line x1="130" y1="50" x2="130" y2="80" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowGB)"/>
  <rect x="20" y="85" width="180" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="110" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Engineering</text><text x="110" y="123" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[Alice, Carol]</text>
  <rect x="220" y="85" width="140" height="50" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="290" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Sales</text><text x="290" y="123" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">[Bob]</text>
  <defs><marker id="arrowGB" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Elements sharing the same classifier result land in the same group — `"Engineering"` collects both `Alice` and `Carol`.

## 5. Runnable example

Scenario: organizing a batch of support tickets by their status — evolved from a plain single-key grouping, through grouping by a derived (computed, not stored) key, to a version that groups by multiple criteria at once using a composite key.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class GroupingByBasic {
    record Ticket(String id, String status) {}

    public static void main(String[] args) {
        List<Ticket> tickets = List.of(
                new Ticket("T1", "open"),
                new Ticket("T2", "closed"),
                new Ticket("T3", "open"),
                new Ticket("T4", "in-progress")
        );

        Map<String, List<Ticket>> byStatus = tickets.stream()
                .collect(Collectors.groupingBy(Ticket::status));

        new TreeMap<>(byStatus).forEach((status, group) ->
                System.out.println(status + ": " + group.size() + " ticket(s)"));
    }
}
```

**How to run:** `java GroupingByBasic.java`

Expected output:
```
closed: 1 ticket(s)
in-progress: 1 ticket(s)
open: 2 ticket(s)
```

`Collectors.groupingBy(Ticket::status)` sorts the four tickets into three groups by their `status` field — `"open"` gets both `T1` and `T3`, while `"closed"` and `"in-progress"` each get one.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class GroupingByDerivedKey {
    record Ticket(String id, int ageInDays) {}

    public static void main(String[] args) {
        List<Ticket> tickets = List.of(
                new Ticket("T1", 2),
                new Ticket("T2", 15),
                new Ticket("T3", 4),
                new Ticket("T4", 45)
        );

        // Group by a COMPUTED urgency bucket -- not a stored field, but derived from ageInDays.
        Map<String, List<Ticket>> byUrgency = tickets.stream()
                .collect(Collectors.groupingBy(t -> {
                    if (t.ageInDays() > 30) return "critical";
                    if (t.ageInDays() > 7) return "stale";
                    return "fresh";
                }));

        new TreeMap<>(byUrgency).forEach((bucket, group) ->
                System.out.println(bucket + ": " + group.stream().map(Ticket::id).toList()));
    }
}
```

**How to run:** `java GroupingByDerivedKey.java`

Expected output:
```
critical: [T4]
fresh: [T1, T3]
stale: [T2]
```

The real-world concern this adds: the grouping key isn't always a stored field — here it's *computed* on the fly from `ageInDays` via an inline lambda that classifies each ticket into `"fresh"`, `"stale"`, or `"critical"`. `groupingBy` doesn't care whether the classifier reads a field directly or computes something more elaborate; it just needs a function from element to key.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class GroupingByComposite {
    record Ticket(String id, String team, String status) {}
    record TeamStatus(String team, String status) {}

    public static void main(String[] args) {
        List<Ticket> tickets = List.of(
                new Ticket("T1", "backend", "open"),
                new Ticket("T2", "backend", "closed"),
                new Ticket("T3", "frontend", "open"),
                new Ticket("T4", "backend", "open"),
                new Ticket("T5", "frontend", "closed")
        );

        // Group by a COMPOSITE key: both team and status together.
        Map<TeamStatus, List<Ticket>> byTeamAndStatus = tickets.stream()
                .collect(Collectors.groupingBy(t -> new TeamStatus(t.team(), t.status())));

        byTeamAndStatus.entrySet().stream()
                .sorted(Comparator.comparing((Map.Entry<TeamStatus, List<Ticket>> e) -> e.getKey().team())
                        .thenComparing(e -> e.getKey().status()))
                .forEach(e -> System.out.println(e.getKey().team() + "/" + e.getKey().status() + ": " + e.getValue().size()));
    }
}
```

**How to run:** `java GroupingByComposite.java`

Expected output:
```
backend/closed: 1
backend/open: 2
frontend/closed: 1
frontend/open: 1
```

This groups by a **composite key** — a `TeamStatus` record combining both `team` and `status` — rather than a single field. Because `TeamStatus` is a `record`, its auto-generated `equals()`/`hashCode()` make two tickets with the same team *and* the same status land in the same group; `"backend"` tickets with `"open"` status (`T1` and `T4`) group together, distinct from `"backend"`/`"closed"` (`T2` alone), even though they share the same `team`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Five tickets are defined across two teams and two statuses.

`tickets.stream().collect(Collectors.groupingBy(t -> new TeamStatus(t.team(), t.status())))` processes each ticket, computing a composite `TeamStatus` key. For `T1` (`backend`, `open`): key is `TeamStatus("backend", "open")`, no existing group, a new list is created and `T1` added.

For `T2` (`backend`, `closed`): key is `TeamStatus("backend", "closed")` — a *different* key from `T1`'s, since the `status` differs even though `team` matches. New group created, `T2` added.

For `T3` (`frontend`, `open`): key is `TeamStatus("frontend", "open")`, new group, `T3` added.

For `T4` (`backend`, `open`): key is `TeamStatus("backend", "open")` — this exactly matches `T1`'s key (both fields equal, and since `TeamStatus` is a record, `equals()` compares all fields), so `T4` joins `T1`'s existing group rather than creating a new one.

For `T5` (`frontend`, `closed`): key is `TeamStatus("frontend", "closed")`, new group, `T5` added.

```
T1 (backend, open)   -> key TeamStatus(backend,open)   -> new group [T1]
T2 (backend, closed) -> key TeamStatus(backend,closed) -> new group [T2]
T3 (frontend, open)  -> key TeamStatus(frontend,open)  -> new group [T3]
T4 (backend, open)   -> key TeamStatus(backend,open)   -> MATCHES T1's key -> group becomes [T1, T4]
T5 (frontend,closed) -> key TeamStatus(frontend,closed)-> new group [T5]

Final: {(backend,open)=[T1,T4], (backend,closed)=[T2], (frontend,open)=[T3], (frontend,closed)=[T5]}
```

Four distinct `TeamStatus` keys result from five tickets, since `T1` and `T4` share a key. The subsequent `.sorted(...)` on the entry set orders the four groups first by `team` then by `status`, and the `forEach` prints each group's size: `backend/closed: 1`, `backend/open: 2` (containing both `T1` and `T4`), `frontend/closed: 1`, `frontend/open: 1`.

## 7. Gotchas & takeaways

> Using a mutable object as a composite grouping key is dangerous — if the key's fields change after it's used as a `Map` key, lookups and future groupings can behave inconsistently, since `hashCode()` may no longer match where the entry was actually stored. `record` types are naturally safe here since they're immutable by design, which is exactly why `TeamStatus` in Level 3 is implemented as a record rather than a mutable class.

- `Collectors.groupingBy(classifier)` sorts stream elements into a `Map<K, List<T>>`, one list per distinct key the classifier produces.
- The classifier can be a simple field reference or an arbitrary computed function — `groupingBy` only needs *a* function from element to key, however that key is derived.
- A composite key (combining multiple fields, often via a small `record`) groups by the combination of those fields together, not each field independently.
- The default `Map` implementation is unspecified (commonly `HashMap`), so iteration order isn't guaranteed — sort or wrap in a `TreeMap` when a specific display order matters.
- Always use an immutable type (like a `record`) for composite keys, since a `Map`'s correctness depends on keys not changing after insertion.
