---
card: java
gi: 959
slug: local-records
title: Local records
---

## 1. What it is

A local record is a record declared directly inside a method body (or a constructor, or any other block), scoped only to that block, exactly like a local class or local variable — `record Pair(int a, int b) {}` written inside a method is a local record, usable only within that method (or nested blocks within it), and invisible outside it. Introduced alongside local classes and interfaces as part of Java 16's broader effort to let local type declarations be as expressive as top-level ones, local records get every feature a top-level record does: auto-generated accessors, `equals`/`hashCode`/`toString`, a canonical constructor, and the ability to implement interfaces — the only difference is scope, not capability.

## 2. Why & when

Local records solve a specific, common pain point: needing a small, throwaway, multi-value grouping *inside* a single method — perhaps to hold an intermediate computation's several related results, or to group values before sorting or filtering a stream — without wanting to pollute the enclosing class (or a whole separate file) with a tiny type that's only ever meaningful within that one method's logic. Before local records, this need was usually met with a private nested class (verbose, requiring manual `equals`/`hashCode`/`toString` if those were needed), an array or `Object[]` (losing all type safety and readability), or an unwieldy `Map.Entry`-style pair type repurposed awkwardly for more than two values. A local record is the right choice whenever the grouping is genuinely local in scope and purpose — if the same shape of data needs to be shared or returned across multiple methods or classes, a top-level (or nested, non-local) record is almost always the better choice, since a local record's very restrictively narrow scope becomes a liability rather than a feature the moment more than one method needs it.

## 3. Core concept

```
public List<String> topScorers(List<Student> students) {
    record ScoredStudent(String name, int score) {}   // LOCAL record -- scoped to this method only

    return students.stream()
        .map(s -> new ScoredStudent(s.name(), s.computeScore()))
        .sorted(Comparator.comparingInt(ScoredStudent::score).reversed())
        .limit(3)
        .map(ScoredStudent::name)
        .toList();
}
// ScoredStudent does not exist, and cannot be referenced, anywhere outside this method.
```

The local record exists purely to make an intermediate pipeline step (pairing a name with a computed score, for sorting purposes) readable and type-safe, without introducing a type that needs to be maintained, documented, or considered relevant anywhere beyond this one method's implementation.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A local record declared and used entirely within one method's body, contrasted with a top-level record visible throughout the whole class or package" >
  <rect x="20" y="20" width="280" height="110" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="38" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">method topScorers() { ... }</text>
  <rect x="40" y="50" width="240" height="60" fill="none" stroke="#6db33f" stroke-dasharray="3"/>
  <text x="160" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">record ScoredStudent(...)</text>
  <text x="160" y="86" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">used ONLY inside this block</text>
  <text x="160" y="100" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">invisible outside it</text>

  <rect x="360" y="20" width="260" height="110" fill="#1c2430" stroke="#f0883e"/>
  <text x="490" y="38" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Top-level record</text>
  <text x="490" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">visible to the whole</text>
  <text x="490" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">class / package / project</text>
  <text x="490" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">appropriate when shared</text>
  <text x="490" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">across multiple methods</text>
</svg>

*A local record's scope is deliberately narrow — exactly one method's body — while a top-level record is visible wherever its enclosing type is.*

## 5. Runnable example

Scenario: process a list of raw scores into a ranked report, evolving from a basic local record grouping two values, to a realistic streaming pipeline using it for intermediate computation, to a more advanced case with a local record that itself uses a compact constructor for validation, entirely self-contained within one method.

### Level 1 — Basic

```java
import java.util.*;

public class LocalRecordBasic {
    static void printPairs(int[] as, int[] bs) {
        record Pair(int a, int b) {} // LOCAL record -- exists only inside printPairs

        for (int i = 0; i < as.length; i++) {
            Pair p = new Pair(as[i], bs[i]);
            System.out.println(p);
        }
    }

    public static void main(String[] args) {
        printPairs(new int[]{1, 2, 3}, new int[]{10, 20, 30});
    }
}
```

**How to run:** `java LocalRecordBasic.java` (JDK 17+).

Expected output:
```
LocalRecordBasic$1Pair[a=1, b=10]
LocalRecordBasic$1Pair[a=2, b=20]
LocalRecordBasic$1Pair[a=3, b=30]
```

`Pair` is declared entirely inside `printPairs` and used only within its body — the auto-generated `toString()` (note the compiler-assigned local-class-style name, `$1Pair`) confirms it behaves exactly like any other record, despite being invisible to any code outside this one method.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class LocalRecordStreamPipeline {
    record Student(String name, int correct, int total) {}

    static List<String> topScorers(List<Student> students, int topN) {
        record ScoredStudent(String name, double percentage) {} // LOCAL -- only meaningful HERE

        return students.stream()
            .map(s -> new ScoredStudent(s.name(), 100.0 * s.correct() / s.total()))
            .sorted(Comparator.comparingDouble(ScoredStudent::percentage).reversed())
            .limit(topN)
            .map(ScoredStudent::name)
            .toList();
    }

    public static void main(String[] args) {
        List<Student> students = List.of(
            new Student("Ada", 18, 20),
            new Student("Grace", 15, 20),
            new Student("Barbara", 19, 20)
        );
        System.out.println(topScorers(students, 2));
    }
}
```

**How to run:** `java LocalRecordStreamPipeline.java` (JDK 17+).

Expected output:
```
[Barbara, Ada]
```

The real-world concern added: `ScoredStudent` exists purely to carry an intermediate computed value (`percentage`) alongside the name, just long enough to sort by it — since this pairing has no meaning or use anywhere outside this one method's ranking logic, declaring it as a local record keeps the enclosing class free of a type that would otherwise need to be named, documented, and maintained as if it were part of the class's actual public design.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class LocalRecordWithValidation {
    record RawReading(String sensorId, double celsius) {}

    static Map<String, String> classifyReadings(List<RawReading> readings) {
        // Local record with its OWN compact canonical constructor -- full record
        // capability, still entirely scoped to this one method.
        record ClassifiedReading(String sensorId, String category) {
            ClassifiedReading {
                if (sensorId == null || sensorId.isBlank()) {
                    throw new IllegalArgumentException("sensorId cannot be blank");
                }
            }
        }

        return readings.stream()
            .map(r -> {
                String category = r.celsius() < 0 ? "freezing"
                                 : r.celsius() < 20 ? "cool"
                                 : r.celsius() < 30 ? "warm"
                                 : "hot";
                return new ClassifiedReading(r.sensorId(), category);
            })
            .collect(Collectors.toMap(ClassifiedReading::sensorId, ClassifiedReading::category));
    }

    public static void main(String[] args) {
        List<RawReading> readings = List.of(
            new RawReading("sensor-1", -5.0),
            new RawReading("sensor-2", 22.0),
            new RawReading("sensor-3", 35.0)
        );
        System.out.println(classifyReadings(readings));
    }
}
```

**How to run:** `java LocalRecordWithValidation.java` (JDK 17+).

Expected output:
```
{sensor-1=freezing, sensor-2=warm, sensor-3=hot}
```

The production-flavored hard case: `ClassifiedReading` is a local record with its own compact canonical constructor performing genuine validation, demonstrating that a local record loses none of a top-level record's capabilities — it can still enforce invariants, still gets auto-generated `equals`/`hashCode` (relevant here for correct behavior as a `Collectors.toMap` intermediate value), and remains entirely self-contained within `classifyReadings`, never leaking its existence to any other part of the program.

## 6. Walkthrough

Tracing `classifyReadings(readings)` end to end from `LocalRecordWithValidation.main`:

1. The method receives a list of three `RawReading` records, each pairing a sensor ID with a raw Celsius temperature — `RawReading` itself is a top-level (well, nested but non-local) record, visible throughout the class, since it represents genuinely shared input data, unlike the purely-internal `ClassifiedReading`.
2. The local record `ClassifiedReading` is declared at the top of `classifyReadings`'s body — from this point in the method onward, `ClassifiedReading` behaves exactly like any other record type, but it exists nowhere outside this method's scope.
3. The stream pipeline's `map` step processes each `RawReading` in turn: for `sensor-1` at `-5.0`°C, the ternary chain evaluates `celsius() < 0` as true, assigning `category = "freezing"`; a `new ClassifiedReading("sensor-1", "freezing")` is constructed.
4. Construction invokes `ClassifiedReading`'s compact canonical constructor, which checks `sensorId == null || sensorId.isBlank()` — since `"sensor-1"` is neither, this check passes silently, and the compiler's implicit field assignments proceed normally, producing a fully-constructed `ClassifiedReading` instance.
5. This process repeats for `sensor-2` (22.0°C, falling into the `< 30` branch, so `category = "warm"`) and `sensor-3` (35.0°C, falling through every branch to `category = "hot"`) — each producing its own validated `ClassifiedReading` instance.
6. `Collectors.toMap(ClassifiedReading::sensorId, ClassifiedReading::category)` consumes the stream of three `ClassifiedReading` instances, using each one's auto-generated `sensorId()` accessor as the resulting map's key and `category()` accessor as its value — producing the final map `{sensor-1=freezing, sensor-2=warm, sensor-3=hot}`, which is printed; throughout this entire process, `ClassifiedReading` never needed to be referenced, named, or even known about by any code outside `classifyReadings`'s own body, exactly fulfilling its purpose as a purely local, throwaway grouping type.

## 7. Gotchas & takeaways

> **Gotcha:** a local record, like a local class, can be declared inside a static or instance method, a constructor, or even a loop body or `if` block — but if declared inside a non-static context, be aware it still cannot capture and store a reference to the enclosing instance's mutable state as its own field the way a local (non-static) *class* implicitly can; local records, like all records, are implicitly static in nature and can only capture effectively-final local variables from the enclosing scope, not implicit access to `this` of the enclosing instance.

- A local record is declared inside a method (or other block) and scoped only to that block — invisible outside it — while retaining every capability a top-level record has: accessors, `equals`/`hashCode`/`toString`, a canonical constructor, and interface implementation.
- Use a local record for small, throwaway groupings needed only within one method's logic (an intermediate computation, a sort key, a grouping before a stream operation) — this avoids introducing a type into the enclosing class's public or package-level surface that no other code needs to know about.
- If the same shape of data needs to be shared across multiple methods or classes, a top-level or ordinary nested record is the better choice — a local record's narrow scope becomes a limitation, not a benefit, once more than one method needs it.
- A local record retains full validation capability via its own canonical constructor, exactly as demonstrated with `ClassifiedReading`'s compact constructor above.
- Local records are implicitly static in nature and cannot implicitly capture the enclosing instance — they can only capture effectively-final local variables from the enclosing scope, same as a lambda expression.
- See [record components & canonical constructor](0954-record-components-canonical-constructor.md) for the general record mechanics a local record fully inherits, and [record patterns / deconstruction](0960-record-patterns-deconstruction.md) for how records (local or otherwise) can be destructured directly in pattern matching.
