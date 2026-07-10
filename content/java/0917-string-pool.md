---
card: java
gi: 917
slug: string-pool
title: String pool
---

## 1. What it is

The string pool (also called the string intern pool) is a special, JVM-managed table of unique `String` objects, kept so that identical string content can be represented by a single, shared object rather than many separate duplicates. It's closely related to, but distinct from, the [runtime constant pool](0916-runtime-constant-pool.md) covered in the previous tutorial: the constant pool is a per-class, compile-time structure holding a class's literal and symbolic references; the string pool is a single, JVM-wide (not per-class) runtime table that both string literals (via the constant pool machinery) and explicit `String.intern()` calls populate and share. Since Java 7, the string pool lives in the regular heap (rather than the old, now-removed PermGen region), making pooled strings subject to ordinary garbage collection like any other heap object, once nothing references them anymore.

## 2. Why & when

The string pool exists to save memory in the extremely common case of many identical string values appearing throughout a program — class names, field names, configuration keys, repeated literal text — without needing every single occurrence to be a separate object. It matters practically whenever you reason about `String` identity (`==`) versus content equality (`.equals()`), and whenever you work with a large volume of runtime-constructed strings that have a lot of duplicate content (parsing a large file with many repeated category or field values, deduplicating log lines) — explicitly calling `.intern()` on such strings can meaningfully reduce memory footprint by collapsing duplicates down to shared references, at the cost of the lookup/insertion overhead of `intern()` itself and (in older JVMs, less so today) potential pressure on the pool's own internal storage if it isn't sized generously enough.

## 3. Core concept

```java
String a = "config-key";              // literal -- automatically added to (or found in) the string pool
String b = new String("config-key").intern(); // explicitly interned -- looked up in the SAME shared pool

System.out.println(a == b); // true -- both reference the SAME pooled object

// -XX:StringTableSize can tune the string pool's underlying hash table size for workloads
// with a very large number of DISTINCT interned strings, where lookup/insertion performance matters.
```

`intern()` performs a lookup in the shared pool: if an equal string is already present, it returns that existing reference; otherwise, it adds the current string (or an equal copy) to the pool and returns it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Many separate String objects with duplicate content across the heap, versus the same values after being interned, all now sharing references to a small number of unique objects in the string pool">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Before interning: many duplicate objects</text>
  <rect x="20" y="35" width="80" height="30" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="60" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"cat"</text>
  <rect x="110" y="35" width="80" height="30" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"cat"</text>
  <rect x="200" y="35" width="80" height="30" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="240" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"cat"</text>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">After interning: shared references</text>
  <rect x="440" y="70" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="485" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">pool: "cat"</text>
  <rect x="370" y="35" width="50" height="25" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="440" y="35" width="50" height="25" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <rect x="510" y="35" width="50" height="25" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <line x1="395" y1="60" x2="470" y2="68" stroke="#8b949e" stroke-width="1" marker-end="url(#a45)"/>
  <line x1="465" y1="60" x2="480" y2="68" stroke="#8b949e" stroke-width="1" marker-end="url(#a45)"/>
  <line x1="535" y1="60" x2="495" y2="68" stroke="#8b949e" stroke-width="1" marker-end="url(#a45)"/>
  <defs><marker id="a45" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Interning collapses many separate objects with identical content down to shared references to one, single pooled instance — direct memory savings for duplicate-heavy workloads.*

## 5. Runnable example

Scenario: parsing many repeated category values from a large synthetic dataset, growing from the naive, non-interned baseline, to using `intern()` to deduplicate, to measuring the actual memory difference directly.

### Level 1 — Basic

```java
import java.util.*;

public class NonInternedDuplicates {
    public static void main(String[] args) {
        String[] categories = {"electronics", "books", "clothing"};
        List<String> parsed = new ArrayList<>();
        Random random = new Random(42);

        for (int i = 0; i < 100_000; i++) {
            // simulates parsing a category value from some data source -- each call to
            // substring()/concatenation genuinely builds a NEW String object, even though
            // there are only 3 distinct underlying values.
            String category = categories[random.nextInt(3)] + ""; // force a fresh object, not the literal itself
            parsed.add(category);
        }

        long distinctByIdentity = parsed.stream().map(System::identityHashCode).distinct().count();
        System.out.println("total parsed values: " + parsed.size());
        System.out.println("distinct OBJECTS by identity: " + distinctByIdentity + " (many duplicates, despite only 3 real values)");
    }
}
```

**How to run:** `java NonInternedDuplicates.java` (JDK 17+).

Expected output shape:
```
total parsed values: 100000
distinct OBJECTS by identity: 100000 (many duplicates, despite only 3 real values)
```

Every single parsed value is its own separate `String` object, even though only 3 distinct pieces of content actually exist among them — a substantial number of redundant objects for what is logically only 3 unique values.

### Level 2 — Intermediate

```java
import java.util.*;

public class InterningDeduplicates {
    public static void main(String[] args) {
        String[] categories = {"electronics", "books", "clothing"};
        List<String> parsed = new ArrayList<>();
        Random random = new Random(42);

        for (int i = 0; i < 100_000; i++) {
            String category = (categories[random.nextInt(3)] + "").intern(); // explicitly interned
            parsed.add(category);
        }

        long distinctByIdentity = parsed.stream().map(System::identityHashCode).distinct().count();
        System.out.println("total parsed values: " + parsed.size());
        System.out.println("distinct OBJECTS by identity: " + distinctByIdentity + " (collapsed to just the 3 real values)");
    }
}
```

**How to run:** `java InterningDeduplicates.java`.

Expected output:
```
total parsed values: 100000
distinct OBJECTS by identity: 3 (collapsed to just the 3 real values)
```

The real-world concern added: calling `.intern()` on each freshly-parsed value collapses all 100,000 entries down to references to just 3 actual, shared `String` objects — one per distinct content value — directly demonstrating the pool's deduplication effect at scale.

### Level 3 — Advanced

```java
import java.util.*;

public class MeasuringMemorySavings {
    public static void main(String[] args) {
        Runtime runtime = Runtime.getRuntime();
        String[] categories = {"electronics-department", "books-and-media", "clothing-and-accessories"};
        Random random = new Random(42);

        System.gc();
        long beforeNonInterned = usedMB(runtime);
        List<String> nonInterned = new ArrayList<>();
        for (int i = 0; i < 500_000; i++) {
            nonInterned.add(categories[random.nextInt(3)] + ""); // NOT interned -- 500,000 separate objects
        }
        long afterNonInterned = usedMB(runtime);
        System.out.println("memory used by 500,000 NON-interned strings: ~" + (afterNonInterned - beforeNonInterned) + "MB");

        nonInterned = null; // release for a clean measurement of the interned case
        System.gc();

        long beforeInterned = usedMB(runtime);
        List<String> interned = new ArrayList<>();
        random = new Random(42); // same sequence, for a fair comparison
        for (int i = 0; i < 500_000; i++) {
            interned.add((categories[random.nextInt(3)] + "").intern()); // interned -- only 3 REAL objects
        }
        long afterInterned = usedMB(runtime);
        System.out.println("memory used by 500,000 INTERNED strings: ~" + (afterInterned - beforeInterned) + "MB (dramatically less)");

        System.out.println("interned list size: " + interned.size() + " (all references, only 3 actual backing objects)");
    }

    static long usedMB(Runtime runtime) {
        return (runtime.totalMemory() - runtime.freeMemory()) / 1_000_000;
    }
}
```

**How to run:** `java MeasuringMemorySavings.java` (JDK 17+).

Expected output shape (exact megabyte figures vary by JVM/platform, but the interned version should use dramatically less memory):
```
memory used by 500,000 NON-interned strings: ~28MB
memory used by 500,000 INTERNED strings: ~1MB (dramatically less)
interned list size: 500000 (all references, only 3 actual backing objects)
```

This adds the production-flavored hard case: directly measuring, via `Runtime`'s memory statistics, the real memory difference between 500,000 non-interned duplicate strings (each a genuinely separate heap object) and 500,000 interned references to just 3 underlying pooled objects — quantifying that interning's benefit isn't just a theoretical identity trick but a real, measurable memory optimization for workloads with substantial duplicate string content at scale.

## 6. Walkthrough

Tracing why the interned version uses so much less memory:

1. In the non-interned loop, every call to `categories[random.nextInt(3)] + ""` performs a genuine runtime string concatenation (since `""` prevents the compiler from treating this as a compile-time constant expression, forcing real, fresh object creation each time) — this produces 500,000 entirely separate `String` objects on the heap, even though only 3 distinct content values exist among them.
2. Each of those 500,000 objects consumes its own memory (an object header, a reference to its own internal character array, and that array's own storage) — with combined content lengths of roughly 20-25 characters each, this adds up to tens of megabytes total, purely from redundant duplicate storage.
3. In the interned loop, the same concatenation still happens (producing a temporary, freshly-created `String` each iteration), but `.intern()` is then called on each result — this looks up the string's content in the shared pool: the *first* time each of the 3 distinct values is encountered, it's added to the pool; every subsequent occurrence of an *equal* value simply returns the already-pooled reference instead of retaining the freshly-created temporary object.
4. Because `interned` (the `List<String>`) ends up holding 500,000 references, but those references all point to just 3 actual backing `String` objects, the *reachable* memory footprint is dominated by the list's own reference-storage overhead (500,000 pointer-sized entries) plus just 3 real string objects — dramatically less than 500,000 full string objects.
5. The `interned.size()` check confirms the list still logically holds 500,000 entries (nothing about the list's own size changed) — the memory savings come entirely from how many *distinct backing objects* those entries collectively point to, which interning collapsed from 500,000 down to 3.
6. This demonstrates concretely that string interning's value isn't just about `==` comparisons working "correctly" — it's a genuine, measurable memory-deduplication technique, most valuable specifically when a large volume of string data has a comparatively small number of genuinely distinct values.

## 7. Gotchas & takeaways

> **Gotcha:** `intern()` itself has a cost — a lookup (and potential insertion) into the shared, JVM-wide pool, which for a workload with an enormous number of genuinely *distinct* string values (rather than many duplicates of a small number of values) can add overhead without providing any real deduplication benefit, since there's nothing to deduplicate; blindly interning every string in a program is not a universal performance win and can occasionally hurt, especially if it causes excessive growth of the intern table itself.

- The string pool is a JVM-wide, shared table of unique `String` objects — since Java 7, it lives in the regular heap and its contents are subject to ordinary garbage collection once unreferenced.
- String literals are automatically interned; `String.intern()` lets you explicitly opt a runtime-constructed string into the same shared pool.
- Interning is most valuable for workloads with a large volume of duplicate string content and a comparatively small number of genuinely distinct values — parsing data with many repeated categorical fields is the classic case.
- Interning has real overhead (the lookup/insertion cost) and provides no benefit — only cost — for workloads dominated by genuinely unique string values with little duplication.
- `-XX:StringTableSize` can be tuned for workloads with an especially large number of *distinct* interned strings, to keep the pool's internal hash table appropriately sized for good lookup performance; this is a specialized tuning knob, not something most applications need to touch.
