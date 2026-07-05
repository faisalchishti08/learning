---
card: java
gi: 54
slug: wildcard-imports-import-java-util
title: Wildcard imports (import java.util.*)
---

## 1. What it is

A **wildcard import** uses `*` to import all public types from a package in one statement:

```java
import java.util.*;    // imports List, ArrayList, Map, HashMap, Set, ... all public types
```

This is equivalent to writing individual imports for every class in `java.util` that you actually use — but it imports the *name* of every type at once, so you can reference any of them without further imports.

## 2. Why & when

**When wildcard imports are reasonable:**
- Personal scripts and small utilities where import management is a distraction.
- When you use many types from one package (5+ classes from `java.util`).
- Codebases that follow Google Style Guide (which allows wildcards).

**When to prefer explicit single-type imports:**
- Library and framework code — wildcards make it unclear which types are actually used.
- Code under review — reviewers can't tell at a glance what's actually imported.
- Oracle/Sun coding convention and most major style guides recommend explicit imports.
- IDEs (IntelliJ, Eclipse) will automatically expand wildcards on demand.

The key practical consideration: **wildcards do not cause performance overhead** at compile or runtime. The choice is purely about code clarity.

## 3. Core concept

```java
// Wildcard form
import java.util.*;         // all of java.util
import java.util.stream.*;  // all of java.util.stream (different package!)
import java.io.*;

// Equivalent to writing individually (for whatever you use):
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
// ... etc.

// What wildcards DON'T cover:
// 1. Sub-packages — import java.util.* does NOT cover java.util.stream
// 2. Static members — import java.util.* does NOT import Collections.sort()
//    (need: import static java.util.Collections.sort;)

// Name collision with wildcard:
import java.util.*;
import java.sql.*;
// Both have 'Date' — compiler reports an error when you write 'Date d = ...'
// Fix: be explicit:
import java.util.Date;      // takes priority over sql.Date
// java.sql.Date sqlDate = new java.sql.Date(0);  // FQCN for the other one

// Priority order (when wildcards are involved):
// 1. Explicit single-type import
// 2. Same-package classes (no import)
// 3. java.lang.*
// 4. Wildcard imports (lowest)
// If two wildcards produce the same name → compile error on usage
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Wildcard import covers all types in java.util but not sub-packages like java.util.stream">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>

  <!-- java.util package -->
  <rect x="20" y="20" width="290" height="155" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">java.util (import java.util.*)</text>
  <text x="35" y="58"  fill="#6db33f" font-size="9" font-family="monospace">✓ List</text>
  <text x="35" y="72"  fill="#6db33f" font-size="9" font-family="monospace">✓ ArrayList</text>
  <text x="35" y="86"  fill="#6db33f" font-size="9" font-family="monospace">✓ Map, HashMap</text>
  <text x="35" y="100" fill="#6db33f" font-size="9" font-family="monospace">✓ Set, HashSet</text>
  <text x="35" y="114" fill="#6db33f" font-size="9" font-family="monospace">✓ Date</text>
  <text x="35" y="128" fill="#6db33f" font-size="9" font-family="monospace">✓ Optional</text>
  <text x="35" y="142" fill="#6db33f" font-size="9" font-family="monospace">✓ Collections</text>
  <text x="35" y="158" fill="#6db33f" font-size="9" font-family="monospace">✓ Scanner  ...120+ types</text>

  <!-- java.util.stream — NOT covered -->
  <rect x="330" y="20" width="250" height="80" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="455" y="38" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">java.util.stream (separate package)</text>
  <text x="345" y="56" fill="#8b949e" font-size="9" font-family="monospace">✗ Stream     ← needs own import</text>
  <text x="345" y="70" fill="#8b949e" font-size="9" font-family="monospace">✗ Collectors ← needs own import</text>
  <text x="345" y="84" fill="#8b949e" font-size="9" font-family="monospace">✗ IntStream  ← needs own import</text>

  <!-- java.util.function — NOT covered -->
  <rect x="330" y="112" width="250" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="455" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">java.util.function</text>
  <text x="345" y="148" fill="#8b949e" font-size="9" font-family="monospace">✗ Function, Predicate, Consumer</text>
  <text x="345" y="161" fill="#8b949e" font-size="9" font-family="monospace">✗ Supplier, BiFunction ...</text>

  <!-- Not covered label -->
  <text x="595" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✗ = NOT covered by import java.util.*</text>
</svg>

`import java.util.*` covers only the `java.util` package itself — not sub-packages like `java.util.stream` or `java.util.function`. Each sub-package needs its own import.

## 5. Runnable example

Scenario: a student grade tracking system that makes heavy use of `java.util` collections — showing wildcard imports, their limits, and the name-collision scenario.

### Level 1 — Basic

```java
// WildcardBasic.java — wildcard import covering many java.util types
import java.util.*;

public class WildcardBasic {
    public static void main(String[] args) {
        System.out.println("=== Wildcard import demo ===\n");

        // All these types come from java.util — single wildcard import covers all
        List<String> students = new ArrayList<>(List.of("Alice", "Bob", "Carol", "Dave"));
        Map<String, Integer> grades = new HashMap<>();
        grades.put("Alice", 92);
        grades.put("Bob",   78);
        grades.put("Carol", 88);
        grades.put("Dave",  95);

        Set<String> honour = new TreeSet<>();
        for (var entry : grades.entrySet()) {
            if (entry.getValue() >= 90) honour.add(entry.getKey());
        }

        Optional<String> topStudent = grades.entrySet().stream()
            .max(Map.Entry.comparingByValue())
            .map(Map.Entry::getKey);

        Collections.sort(students);
        System.out.println("Students (sorted): " + students);
        System.out.println("Grades: " + grades);
        System.out.println("Honour roll: " + honour);
        System.out.println("Top student: " + topStudent.orElse("none"));

        // Scanner — also from java.util
        System.out.println("\njava.util.Scanner: also covered by import java.util.*");

        // Show which types we used — all from java.util
        System.out.println("\n[ All from java.util.* in this file: ]");
        System.out.println("  List, ArrayList, Map, HashMap, Set, TreeSet,");
        System.out.println("  Optional, Collections, Map.Entry");
        System.out.println("  (Scanner, Random, Properties, Date, ... also available)");
    }
}
```

**How to run:** `java WildcardBasic.java`

One `import java.util.*` makes `List`, `ArrayList`, `Map`, `HashMap`, `Set`, `TreeSet`, `Optional`, `Collections`, and every other type in `java.util` available by short name. When you use this many types from one package, a wildcard is pragmatic.

### Level 2 — Intermediate

Same grade-tracking scenario extended to show what happens when two wildcard imports produce the same class name, and how to resolve it.

```java
// WildcardCollision.java — wildcard collision: java.util.Date vs java.sql.Date
import java.util.*;   // includes java.util.Date
import java.sql.*;    // includes java.sql.Date, java.sql.Connection, ...
// Now 'Date' is ambiguous: which package?

public class WildcardCollision {
    public static void main(String[] args) {
        System.out.println("=== Wildcard collision demo ===\n");

        // java.util.Date — must use FQCN because 'Date' is ambiguous
        java.util.Date utilDate = new java.util.Date();
        System.out.println("java.util.Date:  " + utilDate);

        // java.sql.Date
        java.sql.Date sqlDate = new java.sql.Date(utilDate.getTime());
        System.out.println("java.sql.Date:   " + sqlDate);

        // Other java.sql types — no collision, short name fine:
        System.out.println("\nNon-colliding java.sql types (short name works):");
        System.out.println("  java.sql.Types.VARCHAR = " + java.sql.Types.VARCHAR);

        // java.util types with no collision:
        List<String> list = new ArrayList<>(List.of("a","b","c"));
        Map<String,Integer> map = new HashMap<>();
        System.out.println("java.util.List: " + list);

        System.out.println("\n[ Resolution strategies for wildcard collision ]");
        System.out.println("Strategy A: use FQCN for both (shown above)");
        System.out.println("Strategy B: add explicit import for one (it wins over wildcards):");
        System.out.println("  import java.util.Date; // takes priority over java.sql.*");
        System.out.println("  Date d = new Date();   // = java.util.Date");
        System.out.println("  java.sql.Date sd = ...; // FQCN for the other");
        System.out.println("Strategy C: avoid java.util.Date — use java.time.* instead");

        System.out.println("\n[ Compiler error you'd get without resolution ]");
        System.out.println("  error: reference to Date is ambiguous");
        System.out.println("  both class java.util.Date in java.util");
        System.out.println("  and class java.sql.Date in java.sql match");
    }
}
```

**How to run:** `java WildcardCollision.java`

When `import java.util.*` and `import java.sql.*` are both present, writing `Date d = ...` produces a compile error: "reference to Date is ambiguous". Resolution: use FQCNs, or add an explicit `import java.util.Date` (which takes priority over any wildcard).

### Level 3 — Advanced

Same grade system grown to use `java.util.*`, `java.util.stream.*`, and `java.util.function.*` together — showing the three related-but-separate packages and demonstrating that each requires its own wildcard import.

```java
// WildcardSubPackages.java — java.util.*, java.util.stream.*, java.util.function.*
import java.util.*;
import java.util.stream.*;   // Stream, Collectors, IntStream — NOT in java.util.*
import java.util.function.*; // Function, Predicate, Comparator — NOT in java.util.*

public class WildcardSubPackages {

    record Student(String name, int grade, String subject) {}

    public static void main(String[] args) {
        System.out.println("=== Wildcard sub-packages demo ===\n");

        // Build student list
        List<Student> students = List.of(
            new Student("Alice",  92, "Maths"),
            new Student("Bob",    78, "Maths"),
            new Student("Carol",  88, "Science"),
            new Student("Dave",   95, "Science"),
            new Student("Eve",    73, "Maths"),
            new Student("Frank",  90, "Science")
        );

        // java.util.function.Predicate (from java.util.function.*)
        Predicate<Student> highAchiever = s -> s.grade() >= 90;
        Predicate<Student> mathStudent  = s -> "Maths".equals(s.subject());

        // java.util.function.Function (from java.util.function.*)
        Function<Student, String> nameOf  = Student::name;
        Function<Student, Integer> gradeOf = Student::grade;

        // java.util.stream.Collectors (from java.util.stream.*)
        Map<String, List<Student>> bySubject = students.stream()
            .collect(Collectors.groupingBy(Student::subject));

        Map<String, Double> avgBySubject = students.stream()
            .collect(Collectors.groupingBy(Student::subject,
                     Collectors.averagingInt(Student::grade)));

        List<String> honourRoll = students.stream()
            .filter(highAchiever)
            .sorted(Comparator.comparingInt(Student::grade).reversed())
            .map(nameOf)
            .collect(Collectors.toList());

        // IntStream (from java.util.stream.*)
        IntSummaryStatistics stats = students.stream()
            .mapToInt(gradeOf::apply)
            .summaryStatistics();

        System.out.println("By subject: " + bySubject.keySet());
        System.out.println("Average by subject: " + avgBySubject);
        System.out.println("Honour roll (grade≥90): " + honourRoll);
        System.out.printf("Stats: min=%d, max=%d, avg=%.1f, count=%d%n",
            stats.getMin(), stats.getMax(), stats.getAverage(), stats.getCount());

        System.out.println("\n[ Package hierarchy — each needs own wildcard ]");
        System.out.println("  java.util.*         → List, Map, Set, Optional, Collections...");
        System.out.println("  java.util.stream.*  → Stream, Collectors, IntStream...");
        System.out.println("  java.util.function.*→ Function, Predicate, Consumer, Supplier...");
        System.out.println("  java.util.concurrent.* → CompletableFuture, ExecutorService...");
        System.out.println("  (Each is a distinct package — wildcards don't recurse)");

        System.out.println("\n[ Quick reference: wildcard vs explicit ]");
        System.out.println("  Wildcard covers:  ALL public types in that exact package");
        System.out.println("  Wildcard misses:  sub-packages, static members, nested types");
        System.out.println("  No overhead:      compiler resolves at compile time only");
        System.out.println("  Conflict risk:    two wildcards with same class name → error");
    }
}
```

**How to run:** `java WildcardSubPackages.java`

`java.util.*`, `java.util.stream.*`, and `java.util.function.*` are three completely distinct packages despite the visual hierarchy. Each needs its own import. This is the most common misconception about wildcard imports.

## 6. Walkthrough

Execution trace in `WildcardSubPackages.main`:

**Import resolution.** The compiler sees three wildcard imports. When it encounters `Predicate<Student>`, it searches: (1) explicit single-type imports — none. (2) Same package (`WildcardSubPackages`'s package) — not there. (3) `java.lang.*` — not there. (4) Wildcards: found in `java.util.function.*` → `java.util.function.Predicate`. Similarly `Collectors` → `java.util.stream.Collectors`, `List` → `java.util.List`.

**`Collectors.groupingBy(Student::subject)`.** This is a static method on `java.util.stream.Collectors`. If `import java.util.stream.*` were missing, the compiler would produce: `error: cannot find symbol Collectors`. Just adding `import java.util.*` would not help — `Collectors` lives in `java.util.stream`.

**`Comparator.comparingInt(Student::grade).reversed()`.** `Comparator` is in `java.util` — covered by `import java.util.*`. `comparingInt` is a static method; `.reversed()` is an instance method on the resulting `Comparator<Student>`. No static import needed.

**`stats = students.stream().mapToInt(gradeOf::apply).summaryStatistics()`.** `mapToInt` returns an `IntStream` (from `java.util.stream.IntStream`). `summaryStatistics()` returns `IntSummaryStatistics` (also from `java.util.stream`). Both are resolved via `import java.util.stream.*`.

**No collision.** None of `java.util`, `java.util.stream`, and `java.util.function` share a type name (except edge cases like `Date` in `java.util` and `java.sql` — which are not involved here), so all three wildcards coexist without conflict.

**Bytecode.** The compiled `.class` contains `java.util.List`, `java.util.stream.Collectors`, `java.util.function.Predicate` — fully qualified. `import java.util.*` literally disappears from the bytecode.

## 7. Gotchas & takeaways

> **`import java.util.*` does NOT cover `java.util.stream` or `java.util.function`** — this is the most common wildcard misunderstanding. Sub-packages are fully independent namespaces. No Java import form (not even `import java.*.*`) imports across sub-packages.

> **Wildcards don't cause slower compilation.** A common myth: "wildcard imports slow down the compiler by searching the whole package." In practice, `javac` reads the package's class index once and resolves names in a single pass — there's no measurable difference between `import java.util.*` and explicit imports of 10 types.

- `import java.util.*` = all public types in `java.util` only.
- Sub-packages need their own imports: `java.util.stream.*`, `java.util.function.*`.
- If two wildcards produce the same name, writing that name causes a compile error — add an explicit import to resolve.
- An explicit import always wins over a wildcard for the same name.
- IDEs expand wildcards to single-type imports automatically — if your style guide requires it, just configure your formatter.
