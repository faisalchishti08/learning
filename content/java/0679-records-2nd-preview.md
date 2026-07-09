---
card: java
gi: 679
slug: records-2nd-preview
title: Records (2nd preview)
---

## 1. What it is

**Records**, first previewed in Java 14, returned for a **second preview** in **Java 15** (JEP 384) with refinements based on developer feedback. A record is a compact way to declare an immutable data carrier: `record Point(int x, int y) {}` automatically gives you a canonical constructor, private final fields, public accessor methods (`x()`, `y()`, not `getX()`), plus `equals`, `hashCode`, and `toString` implementations derived from the record's components — all without writing any of that boilerplate by hand. The second preview refined details such as local records (records declared inside a method body) and clarified interactions with sealed types and annotations, ahead of standardization in Java 16.

## 2. Why & when

Plain Java classes meant for holding a handful of immutable fields have long required a large amount of repetitive, error-prone boilerplate: a constructor, getters, `equals`/`hashCode` that must stay consistent with the fields, and a `toString` for debugging — four to five separate pieces of code that all have to be kept in sync whenever a field is added or removed. Records exist because that boilerplate is pure ceremony with no design decisions in it — for a "plain data holder" type, the compiler can derive all of it mechanically from the component list. Reach for a record whenever you're modeling a simple, immutable aggregate of values — a `Point`, a `Range`, a `UserId`, a DTO returned from a service call, a key type for a `Map` — where you want value-based equality and don't need mutable state or a complex inheritance hierarchy (records cannot extend another class, since they implicitly extend `Record`, though they can implement interfaces).

## 3. Core concept

```java
// Ordinary class: this is what a record replaces
final class PointClassic {
    private final int x, y;
    PointClassic(int x, int y) { this.x = x; this.y = y; }
    int x() { return x; }
    int y() { return y; }
    @Override public boolean equals(Object o) { /* ...compare x, y... */ return false; }
    @Override public int hashCode() { /* ...combine x, y... */ return 0; }
    @Override public String toString() { return "PointClassic[x=" + x + ", y=" + y + "]"; }
}

// Java 15 preview — requires --enable-preview --release 15
record Point(int x, int y) {}
```

The single-line `record Point(int x, int y) {}` declaration generates everything the hand-written `PointClassic` class had to spell out explicitly.

## 4. Diagram

<svg viewBox="0 0 620 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A single record declaration expands into fields, accessors, constructor, equals, hashCode, and toString">
  <rect x="20" y="70" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="95" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">record Point(int x, int y)</text>
  <text x="110" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">one line of source</text>

  <line x1="200" y1="100" x2="240" y2="100" stroke="#79c0ff" stroke-width="2" marker-end="url(#a)"/>

  <rect x="250" y="15" width="350" height="170" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="35" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">compiler-generated members</text>
  <text x="270" y="58" fill="#e6edf3" font-size="10" font-family="monospace">private final int x, y;</text>
  <text x="270" y="78" fill="#e6edf3" font-size="10" font-family="monospace">Point(int x, int y) { ... }</text>
  <text x="270" y="98" fill="#e6edf3" font-size="10" font-family="monospace">int x() { return x; }</text>
  <text x="270" y="118" fill="#e6edf3" font-size="10" font-family="monospace">int y() { return y; }</text>
  <text x="270" y="138" fill="#e6edf3" font-size="10" font-family="monospace">equals(Object o) { ... }</text>
  <text x="270" y="158" fill="#e6edf3" font-size="10" font-family="monospace">hashCode() / toString()</text>

  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

One record header expands into fields, a constructor, accessors, and value-based `equals`/`hashCode`/`toString`.

## 5. Runnable example

Scenario: modeling a `Range` of integers — first as a plain record, then adding validation via a compact canonical constructor, then using a **local record** (the Java 15 second-preview refinement) declared inside a method to group intermediate results, plus a custom method added to the record body.

### Level 1 — Basic

```java
// File: RangeBasic.java
// compile & run with: --enable-preview --release 15
public class RangeBasic {
    record Range(int low, int high) {}

    public static void main(String[] args) {
        Range r = new Range(1, 10);
        System.out.println(r);
        System.out.println("low=" + r.low() + " high=" + r.high());
        System.out.println("Equal to Range(1,10)? " + r.equals(new Range(1, 10)));
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 RangeBasic.java
java --enable-preview RangeBasic
```

Expected output:
```
Range[low=1, high=10]
low=1 high=10
Equal to Range(1,10)? true
```

### Level 2 — Intermediate

```java
// File: RangeValidated.java
// compile & run with: --enable-preview --release 15
public class RangeValidated {
    record Range(int low, int high) {
        // Compact canonical constructor: no parameter list repeated,
        // runs before the (implicit) field assignments.
        Range {
            if (low > high) {
                throw new IllegalArgumentException("low (" + low + ") must be <= high (" + high + ")");
            }
        }

        int length() {
            return high - low;
        }
    }

    public static void main(String[] args) {
        Range valid = new Range(1, 10);
        System.out.println("Valid range: " + valid + ", length=" + valid.length());

        try {
            new Range(10, 1);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected invalid range: " + e.getMessage());
        }
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 RangeValidated.java
java --enable-preview RangeValidated
```

Expected output:
```
Valid range: Range[low=1, high=10], length=9
Rejected invalid range: low (10) must be <= high (1)
```

The **compact canonical constructor** (`Range { ... }` with no parameter list) is the key addition: it runs validation logic before the compiler's implicit `this.low = low; this.high = high;` assignments, letting the record enforce an invariant without having to re-declare the full parameter list or manually write the field assignments.

### Level 3 — Advanced

```java
// File: RangeReport.java
// compile & run with: --enable-preview --release 15
import java.util.List;

public class RangeReport {
    record Range(int low, int high) {
        Range {
            if (low > high) throw new IllegalArgumentException("low must be <= high");
        }
        int length() { return high - low; }
        boolean contains(int value) { return value >= low && value <= high; }
    }

    static String summarize(List<Range> ranges, int probe) {
        // Local record (Java 15 2nd-preview refinement): declared right
        // inside the method that needs it, scoped to this computation only.
        record Match(Range range, boolean hit) {}

        List<Match> matches = ranges.stream()
                .map(r -> new Match(r, r.contains(probe)))
                .toList();

        StringBuilder sb = new StringBuilder("Probe " + probe + ":\n");
        for (Match m : matches) {
            sb.append("  ").append(m.range()).append(" -> ")
              .append(m.hit() ? "HIT" : "miss").append("\n");
        }
        return sb.toString();
    }

    public static void main(String[] args) {
        List<Range> ranges = List.of(new Range(1, 5), new Range(4, 8), new Range(10, 20));
        System.out.print(summarize(ranges, 4));
        System.out.print(summarize(ranges, 15));
    }
}
```

**How to run:**
```
javac --enable-preview --release 15 RangeReport.java
java --enable-preview RangeReport
```

Expected output:
```
Probe 4:
  Range[low=1, high=5] -> HIT
  Range[low=4, high=8] -> HIT
  Range[low=10, high=20] -> miss

Probe 15:
  Range[low=1, high=5] -> miss
  Range[low=4, high=8] -> miss
  Range[low=10, high=20] -> HIT
```

Level 3's `Match` record is declared **locally inside `summarize`** — this is exactly the second-preview refinement Java 15 added: records nested inside a method body, scoped only to that method, useful for bundling an intermediate pair of values (here, a `Range` plus whether it matched a probe value) without polluting the enclosing class with a type only that one method cares about.

## 6. Walkthrough

1. `main` builds a `List<Range>` of three ranges and calls `summarize` twice, once per probe value (`4`, then `15`).
2. Inside `summarize`, the first statement declares `record Match(Range range, boolean hit) {}` — a **local record**. This declaration is only visible within `summarize`'s body; it behaves exactly like a top-level record (implicit fields, accessors, `equals`/`hashCode`/`toString`) but its scope is deliberately narrow.
3. `ranges.stream().map(r -> new Match(r, r.contains(probe))).toList()` transforms each `Range` into a `Match`, calling the `contains(int value)` method defined in `Range`'s body (`value >= low && value <= high`) to determine `hit`.
4. Before any of this runs for a `Range` constructed via `new Range(low, high)`, the **compact canonical constructor** `Range { if (low > high) throw ... }` executes first — checking the invariant on the raw constructor arguments before the compiler's implicit field assignment (`this.low = low; this.high = high;`) takes place. If the check fails, an exception is thrown and no `Range` instance is ever created.
5. Back in `summarize`, the resulting `List<Match>` is iterated, and for each `Match` the code appends a line to a `StringBuilder`: the range's default `toString()` (`Range[low=1, high=5]`, generated by the compiler from the component list), an arrow, then `"HIT"` or `"miss"` depending on `m.hit()`.
6. `summarize` returns the accumulated `String`, and `main` prints it via `System.out.print`.
7. For probe `4`: `Range[1,5]` contains 4 (within `1..5`), `Range[4,8]` contains 4 (boundary-inclusive since `contains` uses `>=`/`<=`), and `Range[10,20]` does not — producing two hits and one miss, matching the expected output.
8. For probe `15`: only `Range[10,20]` contains it, producing one hit and two misses.

```
summarize(ranges, probe)
   │
   ▼
local record Match(Range, boolean)  ← scoped to this method only
   │
ranges.stream().map(r -> new Match(r, r.contains(probe))).toList()
   │
   ▼
for each Match: append "<range> -> HIT/miss"
```

## 7. Gotchas & takeaways

> Records were a **preview feature through Java 14 and 15** — this second preview refined behavior (notably local records and interactions with annotations/sealed types) but still required `--enable-preview` to compile and run; records did not become permanent, standard syntax until Java 16. Code written against the Java 15 preview could differ subtly from the finalized Java 16 semantics.

- The **compact canonical constructor** (`Range { ... }`, no parameter list) is for validation/normalization only — you cannot assign to the implicit fields yourself inside it in a way that bypasses the auto-generated assignments; you can only reassign the constructor *parameters* before the implicit `this.field = param` lines run.
- Records are implicitly `final` and cannot extend another class (they implicitly extend `java.lang.Record`), though they can implement interfaces — pairing well with [sealed classes (preview)](0678-sealed-classes-preview.md) to model closed sets of data variants.
- A record's generated `equals`/`hashCode` compare **all** components — if a record holds a mutable field (e.g. an array or a mutable list), two "equal" records can appear to change equality later if that mutable field is mutated, since records don't force deep immutability of their component types.
- Local records (this preview's refinement) are implicitly `static` — like local classes and interfaces, they cannot capture an enclosing instance, keeping their semantics simple even though they're declared inside a method body.
- The default `toString()` format (`Range[low=1, high=10]`) is convenient for debugging but is not a stable, guaranteed serialization format — don't parse it back or rely on its exact text across JDK versions.
