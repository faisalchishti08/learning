---
card: java
gi: 162
slug: intern
title: intern()
---

## 1. What it is

`String.intern()` returns the canonical representative for a string's content from the JVM's string pool: if a string with identical content already exists in the pool, `intern()` returns a reference to *that* existing object; otherwise, it adds the calling string to the pool and returns a reference to it. This was introduced briefly in the string-pool topic — here we look at it directly as its own method.

```java
String heap = new String("cat"); // NOT pooled — a distinct heap object
String pooled = "cat";           // pooled automatically, since it's a literal

System.out.println(heap == pooled);           // false — different objects
System.out.println(heap.intern() == pooled);  // true  — intern() returns the SAME pooled object
```

Calling `intern()` never changes the string's *content* — `"cat".intern()` still equals `"cat"` — it only ever affects which specific object reference you end up holding, and whether that object is now shared with the pool.

## 2. Why & when

`intern()` is a deliberate, manual opt-in to pooling for strings that weren't automatically pooled (typically ones built at runtime rather than written as literals):

- **Deduplicating many repeated runtime-built strings** — if a program parses a large dataset containing millions of repeated values (e.g., a "status" column with only a handful of distinct strings appearing millions of times), interning each parsed value ensures only one object exists per distinct value, dramatically reducing memory use compared to keeping millions of separate, duplicate `String` objects.
- **Enabling `==` comparisons deliberately** — in rare, performance-sensitive code where object-identity comparison (`==`) is intentionally used as a fast substitute for `.equals()`, every candidate string must first be interned, or the comparison becomes unreliable.

For ordinary application code, `intern()` is rarely needed — `.equals()` for comparison and normal, unpooled strings for everyday text handling are almost always sufficient. `intern()` earns its keep specifically in memory-constrained, high-volume parsing scenarios.

## 3. Core concept

```java
public class InternDemo {
    public static void main(String[] args) {
        String[] rawValues = { new String("ACTIVE"), new String("INACTIVE"), new String("ACTIVE") };

        for (String raw : rawValues) {
            String interned = raw.intern();
            System.out.println(raw + " -> interned identity hash: " + System.identityHashCode(interned));
        }
    }
}
```

Even though `rawValues[0]` and `rawValues[2]` are two entirely separate `new String("ACTIVE")` heap objects with identical content, calling `.intern()` on each returns the *very same* pooled object both times — printing the same identity hash code for both, despite `raw` itself being different objects.

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Intern diagram: two separately-created heap strings with identical content ACTIVE both call intern, and both calls return a reference to the same single pooled object, deduplicating what were previously two separate objects into one shared one." >
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Two separate heap objects, both interned to the SAME pooled object</text>

  <rect x="60" y="45" width="140" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="130" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">heap #1 "ACTIVE"</text>

  <rect x="60" y="95" width="140" height="30" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5" stroke-dasharray="3,2"/>
  <text x="130" y="115" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">heap #2 "ACTIVE"</text>

  <path d="M 200 60 L 420 70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <path d="M 200 110 L 420 80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="300" y="55" fill="#6db33f" font-size="8" font-family="sans-serif">.intern()</text>
  <text x="300" y="130" fill="#6db33f" font-size="8" font-family="sans-serif">.intern()</text>

  <rect x="420" y="60" width="160" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="500" y="80" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">POOL: "ACTIVE" (one)</text>

  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Before interning: two distinct objects. After: both references point to one shared, deduplicated object.</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

`intern()` collapses any number of content-identical heap strings down to references to one shared pooled object.

## 5. Runnable example

Scenario: parsing a very large log file where a "log level" field (e.g., "INFO", "WARN", "ERROR") repeats millions of times but only has a handful of distinct values — starting with a basic simulation of parsing without interning, then adding interning to deduplicate the repeated values, then hardening it into a small reusable cache that demonstrates the memory-saving effect directly by counting distinct object identities.

### Level 1 — Basic

```java
public class LogParseBasic {
    public static void main(String[] args) {
        String[] rawLevels = {
            new String("INFO"), new String("WARN"), new String("INFO"),
            new String("ERROR"), new String("INFO"), new String("WARN")
        };

        int distinctObjects = 0;
        for (int i = 0; i < rawLevels.length; i++) {
            boolean isNewObject = true;
            for (int j = 0; j < i; j++) {
                if (rawLevels[i] == rawLevels[j]) {
                    isNewObject = false;
                    break;
                }
            }
            if (isNewObject) distinctObjects++;
        }
        System.out.println("Distinct String OBJECTS (by identity): " + distinctObjects + " out of " + rawLevels.length);
    }
}
```

**How to run:** `java LogParseBasic.java`

Every entry in `rawLevels` was built with `new String(...)`, so *none* of them share identity with each other, even though only 3 distinct pieces of text (`"INFO"`, `"WARN"`, `"ERROR"`) actually appear — the identity-based count reports `6` distinct objects out of `6` total, meaning zero deduplication is happening despite the repeated content.

### Level 2 — Intermediate

Same log levels, now **interning** each one as it's "parsed," so repeated values collapse down to shared objects.

```java
public class LogParseIntermediate {
    public static void main(String[] args) {
        String[] rawLevels = {
            new String("INFO"), new String("WARN"), new String("INFO"),
            new String("ERROR"), new String("INFO"), new String("WARN")
        };

        String[] internedLevels = new String[rawLevels.length];
        for (int i = 0; i < rawLevels.length; i++) {
            internedLevels[i] = rawLevels[i].intern();
        }

        int distinctObjects = 0;
        for (int i = 0; i < internedLevels.length; i++) {
            boolean isNewObject = true;
            for (int j = 0; j < i; j++) {
                if (internedLevels[i] == internedLevels[j]) {
                    isNewObject = false;
                    break;
                }
            }
            if (isNewObject) distinctObjects++;
        }
        System.out.println("Distinct String OBJECTS after interning: " + distinctObjects + " out of " + internedLevels.length);
    }
}
```

**How to run:** `java LogParseIntermediate.java`

`rawLevels[i].intern()` is called on every parsed value before it's stored — now `internedLevels` reports only `3` distinct objects (`"INFO"`, `"WARN"`, `"ERROR"`, each shared across their repeated occurrences) out of the same `6` total entries, exactly matching the number of genuinely distinct pieces of text, rather than the number of separately-allocated heap objects.

### Level 3 — Advanced

Same idea, now demonstrating the memory-saving effect at a larger, more realistic scale — simulating a million-line log file where interning turns what would be a million separate heap allocations into just a handful of shared objects, and reporting the actual identity-based savings.

```java
import java.util.HashMap;
import java.util.Map;

public class LogParseAdvanced {

    static int countDistinctObjects(String[] values) {
        Map<String, Boolean> seenByIdentity = new HashMap<>(); // used only to track already-seen VALUES, not identity
        int distinct = 0;
        java.util.IdentityHashMap<String, Boolean> seenIdentities = new java.util.IdentityHashMap<>();
        for (String v : values) {
            if (!seenIdentities.containsKey(v)) {
                seenIdentities.put(v, true);
                distinct++;
            }
        }
        return distinct;
    }

    public static void main(String[] args) {
        String[] levelPool = { "INFO", "WARN", "ERROR", "DEBUG" };
        int totalLines = 1_000_000;

        String[] withoutIntern = new String[totalLines];
        String[] withIntern = new String[totalLines];

        for (int i = 0; i < totalLines; i++) {
            String level = levelPool[i % levelPool.length];
            withoutIntern[i] = new String(level);       // simulate parsing: always a fresh object
            withIntern[i] = new String(level).intern();  // simulate parsing, then deduplicate via intern()
        }

        System.out.println("Total lines: " + totalLines);
        System.out.println("Distinct objects WITHOUT intern(): " + countDistinctObjects(withoutIntern));
        System.out.println("Distinct objects WITH intern():    " + countDistinctObjects(withIntern));
    }
}
```

**How to run:** `java LogParseAdvanced.java`

`java.util.IdentityHashMap` is used specifically because it compares keys by **reference identity** (`==`), not `.equals()` content — this makes it the correct tool to count genuinely distinct *objects*, as opposed to a regular `HashMap`, which would collapse all content-equal strings together regardless of interning. `withoutIntern` simulates parsing where every line creates a brand-new, un-interned `String`, so `countDistinctObjects` reports the full `1,000,000` (every object is unique by identity, despite only 4 distinct pieces of text). `withIntern` calls `.intern()` immediately after constructing each value, so repeated values collapse onto the same pooled objects, and `countDistinctObjects` reports just `4` — matching `levelPool.length` exactly.

## 6. Walkthrough

Trace what happens for the first few iterations of the `withIntern` loop in `LogParseAdvanced` (`levelPool.length = 4`):

**i = 0.** `level = levelPool[0] = "INFO"`. `new String("INFO")` creates a fresh heap object with content `"INFO"`. `.intern()` checks the pool: no `"INFO"` is there yet (assuming it wasn't already interned from being used as a literal elsewhere), so this heap object itself becomes the pool's canonical `"INFO"`, and `withIntern[0]` references it.

**i = 4.** `level = levelPool[0] = "INFO"` again (since `4 % 4 == 0`). `new String("INFO")` creates *another* fresh heap object with the same content. `.intern()` checks the pool: this time, `"INFO"` **is** already there (from step `i = 0`) — so `intern()` discards the newly-created heap object's identity and returns a reference to the *original* pooled `"INFO"` instead. `withIntern[4]` ends up referencing the exact same object as `withIntern[0]`.

```
i=0: new String("INFO") -> heap object A -> intern(): pool empty for "INFO" -> A becomes pooled -> withIntern[0] = A
i=4: new String("INFO") -> heap object B (different object!) -> intern(): pool already has "INFO" (=A) -> return A -> withIntern[4] = A
result: withIntern[0] == withIntern[4]  (both reference A, object B is discarded/eligible for GC)
```

**Final output.** `countDistinctObjects(withoutIntern)` reports `1000000` (every one of the million parsed values is a separate, never-deduplicated heap object). `countDistinctObjects(withIntern)` reports `4` — exactly `levelPool.length` — since every one of the million values collapses onto one of only four pooled objects, regardless of how many times each log level actually appeared.

## 7. Gotchas & takeaways

> **`intern()` does not change a string's content — it only affects which object reference you get back, and whether the pool now shares it.** `"cat".intern().equals("cat")` is trivially `true`, exactly as it would be without interning; the *behavior* changes only for `==` comparisons and for how many distinct objects exist in memory.

> **Interning has a cost too — the pool itself consumes memory and lookup time — so blanket-interning every string in ordinary application code is not a free optimization.** It earns its keep specifically for high-volume, high-repetition scenarios (parsing large datasets with few distinct values); for typical, moderate string usage, the pool's own overhead can outweigh any savings.

- `intern()` returns the pool's canonical object for a given string's content, adding it to the pool if not already present.
- It's a deliberate, manual way to deduplicate strings built at runtime (via `new String(...)`, concatenation, or parsing), which aren't automatically pooled the way literals are.
- Use it specifically for high-volume data with a small number of distinct repeated values — the classic case being a "category" or "status" style field parsed millions of times.
- Never rely on `==` for correctness unless you can guarantee every candidate string has been interned — `.equals()` remains the universally correct way to compare string content regardless of pooling.
