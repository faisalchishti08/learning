---
card: java
gi: 593
slug: stream-ofnullable
title: Stream.ofNullable
---

## 1. What it is

`Stream.ofNullable` is a Java 9 static factory method on the `Stream` interface that returns a stream containing either a single element (if the argument is non-null) or an empty stream (if the argument is `null`). It wraps the common pattern "if the value is present, stream it; otherwise, stream nothing" into a single, readable call that avoids conditional logic scattered throughout stream pipelines.

## 2. Why & when

Before Java 9, converting a potentially-null value into a stream element required a conditional: `value == null ? Stream.empty() : Stream.of(value)`. This ternary pattern appeared everywhere — in `flatMap` lambdas, in helper methods, in collectors — and each occurrence was a small readability drag and a missed opportunity for the compiler or JIT to recognize the idiom. `Stream.ofNullable` captures this pattern as a single method call, making the intent obvious ("stream this value if it exists") and allowing stream pipelines to handle nullable data without breaking into imperative conditionals. The method is especially useful in `flatMap` chains (where each element may or may not produce a sub-stream) and when integrating with legacy APIs that return nullable references.

## 3. Core concept

```java
String present = "hello";
String absent  = null;

Stream.ofNullable(present).forEach(System.out::println); // prints "hello"
Stream.ofNullable(absent).forEach(System.out::println);  // prints nothing
```

`Stream.ofNullable(x)` is equivalent to `x == null ? Stream.empty() : Stream.of(x)`. It returns a `Stream<T>` — never `null` itself — so it can always be chained with further stream operations without a null check on the resulting stream object.

## 4. Diagram

<svg viewBox="0 0 520 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Stream.ofNullable branches on null vs non-null input">
  <rect x="20" y="10" width="480" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="60" y="30" width="180" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="150" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">Stream.ofNullable(x)</text>

  <line x1="150" y1="70" x2="100" y2="90" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="150" y1="70" x2="250" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <text x="85" y="82" fill="#8b949e" font-size="9" font-family="sans-serif">x == null</text>
  <text x="245" y="82" fill="#8b949e" font-size="9" font-family="sans-serif">x != null</text>

  <rect x="30" y="95" width="140" height="30" rx="4" fill="#f85149" stroke="#f85149"/>
  <text x="100" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Stream.empty()</text>

  <rect x="210" y="95" width="140" height="30" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="280" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">Stream.of(x)</text>
</svg>

Single branching point at the method entry — null yields emptiness, non-null yields a one-element stream.

## 5. Runnable example

Scenario: a system that resolves user IDs to display names by consulting a lookup map, where not every ID is guaranteed to have a mapping — starting with basic null-to-empty conversion, extending to a `flatMap` pipeline that filters out missing entries, and finally handling production edge cases with nested nullable structures.

### Level 1 — Basic

```java
// File: OfNullableDemo.java
import java.util.stream.Stream;

public class OfNullableDemo {
    public static void main(String[] args) {
        String name = "Alice";
        String missing = null;

        System.out.println("=== name (non-null) ===");
        Stream.ofNullable(name).forEach(n -> System.out.println("  Found: " + n));

        System.out.println("=== missing (null) ===");
        Stream.ofNullable(missing).forEach(n -> System.out.println("  Found: " + n));
        System.out.println("  (no output — stream was empty)");
    }
}
```

**How to run:** `java OfNullableDemo.java`

Expected output:
```
=== name (non-null) ===
  Found: Alice
=== missing (null) ===
  (no output — stream was empty)
```

The simplest usage: wrap a single nullable value in a stream. `Stream.ofNullable("Alice")` produces a one-element stream; `Stream.ofNullable(null)` produces an empty stream, which `.forEach` silently skips.

### Level 2 — Intermediate

```java
// File: LookupPipeline.java
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

public class LookupPipeline {
    public static void main(String[] args) {
        Map<String, String> userNames = Map.of(
            "U1", "Alice",
            "U2", "Bob",
            "U3", "Charlie"
        );

        List<String> idsToResolve = List.of("U1", "U2", "U99", "U3", "U42");

        List<String> resolved = idsToResolve.stream()
            .map(userNames::get)              // Map.get returns null for missing keys
            .flatMap(Stream::ofNullable)       // skip nulls — keep only present names
            .collect(Collectors.toList());

        System.out.println("Resolved names: " + resolved);
    }
}
```

**How to run:** `java LookupPipeline.java`

Expected output:
```
Resolved names: [Alice, Bob, Charlie]
```

The real-world concern added: a `flatMap` pipeline that resolves IDs against a map. `Map.get` returns `null` for missing keys ("U99" and "U42"), which would normally require an explicit null check or a `filter(Objects::nonNull)` step. `.flatMap(Stream::ofNullable)` handles this inline — each `null` from `Map.get` becomes an empty stream (contributing nothing to the output), each non-null name becomes a one-element stream that `flatMap` merges into the result. This is the canonical production pattern for `Stream.ofNullable`.

### Level 3 — Advanced

```java
// File: NestedNullableDemo.java
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class NestedNullableDemo {
    record Department(String name, String managerId) {}
    record Employee(String id, String name) {}

    public static void main(String[] args) {
        // Simulated data — some departments have no manager, some managers don't exist
        List<Department> depts = List.of(
            new Department("Engineering", "E1"),
            new Department("Marketing", null),    // no manager assigned
            new Department("Sales", "E99"),       // manager ID doesn't exist
            new Department("Support", "E3")
        );

        Map<String, Employee> employees = Map.of(
            "E1", new Employee("E1", "Alice"),
            "E2", new Employee("E2", "Bob"),
            "E3", new Employee("E3", "Charlie")
        );

        List<String> reports = depts.stream()
            .flatMap(dept -> {
                // ofNullable: if managerId is null, skip this department
                return Stream.ofNullable(dept.managerId())
                    .flatMap(mgrId -> {
                        // ofNullable: if managerId doesn't map to an employee, skip
                        return Stream.ofNullable(employees.get(mgrId));
                    })
                    .map(emp -> dept.name() + " → " + emp.name() + " (" + emp.id() + ")");
            })
            .collect(Collectors.toList());

        System.out.println("Department → Manager report:");
        reports.forEach(System.out::println);
    }
}
```

**How to run:** `java NestedNullableDemo.java`

Expected output:
```
Department → Manager report:
Engineering → Alice (E1)
Support → Charlie (E3)
```

This handles the production-flavoured case of nested nullable lookups. `Marketing` has a `null` manager ID — `Stream.ofNullable(null)` at the outer level produces an empty stream, so Marketing contributes nothing. `Sales` has a valid-looking manager ID "E99", but that ID doesn't exist in the employee map — `employees.get("E99")` returns `null`, and the inner `Stream.ofNullable(null)` again produces an empty stream, so Sales also contributes nothing. `Engineering` and `Support` both have valid IDs that resolve to real employees — each produces a one-element stream that gets mapped to the report string and collected. Two layers of `Stream.ofNullable` handle two distinct nullable points without a single explicit `if` or null check.

## 6. Walkthrough

Tracing the Level 3 example from `main` to output:

Execution begins in `NestedNullableDemo.main`. Two records are defined (`Department` and `Employee`), sample data is created (four departments, three employees), and then the stream pipeline begins.

**State before the stream**: `depts` is a list of four `Department` records. The stream pipeline is `depts.stream().flatMap(...).collect(Collectors.toList())`.

The terminal operation `.collect(Collectors.toList())` triggers consumption. The stream source (the list) begins yielding elements one at a time:

---

**Element 1**: `Department("Engineering", "E1")`

The `flatMap` lambda receives this department. `Stream.ofNullable(dept.managerId())` evaluates `dept.managerId()` → `"E1"` (non-null) → returns `Stream.of("E1")`, a one-element stream containing the string `"E1"`.

The inner `flatMap` now receives `"E1"` and evaluates its lambda: `Stream.ofNullable(employees.get("E1"))`. `employees.get("E1")` looks up the map key "E1" → returns `Employee("E1", "Alice")` (non-null) → returns `Stream.of(Employee("E1", "Alice"))`, a one-element stream containing the employee.

`.map(emp -> dept.name() + " → " + emp.name() + " (" + emp.id() + ")")` transforms this employee element into the string `"Engineering → Alice (E1)"`. This string is sent downstream to the collector.

---

**Element 2**: `Department("Marketing", null)`

`Stream.ofNullable(dept.managerId())` evaluates `dept.managerId()` → `null` → returns `Stream.empty()`. An empty stream has zero elements, so the inner `flatMap` and `.map` stages are never invoked for this department. Nothing is contributed to the collector. Marketing silently disappears from the output.

---

**Element 3**: `Department("Sales", "E99")`

`Stream.ofNullable(dept.managerId())` → `"E99"` (non-null) → `Stream.of("E99")`.

Inner `flatMap` receives `"E99"` → `Stream.ofNullable(employees.get("E99"))`. `employees.get("E99")` looks up key "E99" → no such key → `Map.get` returns `null` → `Stream.ofNullable(null)` returns `Stream.empty()`. The inner empty stream contributes nothing. Sales silently disappears from the output.

---

**Element 4**: `Department("Support", "E3")`

Same path as Element 1: manager ID "E3" is non-null → resolves to `Employee("E3", "Charlie")` → maps to `"Support → Charlie (E3)"` → collected.

---

After all four departments are processed, the collector returns a `List` containing two strings: `"Engineering → Alice (E1)"` and `"Support → Charlie (E3)"`. The `println` header and `forEach` loop produce the final output.

```
                         ┌───────────────────────────────────┐
  dept.stream()          │  flatMap(Stream.ofNullable chain)  │       collect(toList())
  ───────────────────────►│                                    │──────────────────────►
                          │                                    │
  Engineering / "E1" ─────┤  ofNullable("E1") → Stream.of("E1")│
                          │  → employees.get("E1") → Alice ────┤  "Engineering → Alice (E1)"
                          │                                    │
  Marketing / null ───────┤  ofNullable(null) → Stream.empty() │  (skipped — no output)
                          │                                    │
  Sales / "E99" ──────────┤  ofNullable("E99") → Stream.of("E99")│
                          │  → employees.get("E99") → null ────┤  (skipped — no output)
                          │  → ofNullable(null) → Stream.empty()│
                          │                                    │
  Support / "E3" ─────────┤  ofNullable("E3") → Stream.of("E3")│
                          │  → employees.get("E3") → Charlie ──┤  "Support → Charlie (E3)"
                          └───────────────────────────────────┘
```

## 7. Gotchas & takeaways

> `Stream.ofNullable` returns a `Stream`, never `null` — chaining `.map(...)` or `.filter(...)` on the result is always safe, but if you call `.findFirst()` on a stream that was `Stream.ofNullable(null)`, you get `Optional.empty()`, not `null`. This is consistent with all stream behaviour but can surprise developers who expect the null to propagate through.

- `Stream.ofNullable` is a **static method** on the `Stream` interface, not an instance method — you call it as `Stream.ofNullable(x)`, not `someStream.ofNullable(x)`.
- It is the stream-level counterpart to `Optional.ofNullable` — while `Optional.ofNullable` wraps a nullable value in a container that may or may not be present, `Stream.ofNullable` converts it into a stream of zero or one elements, which composes more naturally into stream pipelines.
- Combined with `flatMap`, it serves as a compact "skip nulls" operation: `.flatMap(Stream::ofNullable)` is often clearer than `.filter(Objects::nonNull)` because it works on the mapped value, not on the stream elements themselves.
- There is no performance cost to using `Stream.ofNullable(null)` repeatedly — `Stream.empty()` is a shared singleton, so no new stream object is allocated for the null case.
- It does not replace `Optional` — `Stream.ofNullable` is specifically for stream pipelines; for single-value null handling in non-stream code, `Optional.ofNullable` remains the appropriate tool. 