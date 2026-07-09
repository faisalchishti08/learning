---
card: java
gi: 590
slug: list-of-set-of-map-of-map-ofentries
title: List.of / Set.of / Map.of / Map.ofEntries
---

## 1. What it is

Java 9 added static factory methods — `List.of(...)`, `Set.of(...)`, `Map.of(...)`, and `Map.ofEntries(...)` — that build genuinely **immutable** collections in a single expression, with no builder, no `Collections.unmodifiableList(...)` wrapping step, and no mutable intermediate collection ever created. `List.of("a", "b", "c")` returns a fixed-size, unmodifiable `List<String>` directly.

## 2. Why & when

Before Java 9, creating a small immutable collection required either verbose, multi-step code (`new ArrayList<>(Arrays.asList(...))` wrapped in `Collections.unmodifiableList(...)`) or accepting a collection that was merely *conventionally* treated as read-only without actually being enforced as such. `Arrays.asList(...)` came close but wasn't a true fix — it produces a fixed-*size* list (no add/remove) that still permits `set(index, value)`, an easy-to-miss gap. `List.of`/`Set.of`/`Map.of` close this gap directly: every mutating method (`add`, `remove`, `set`, `put`, `clear`) throws `UnsupportedOperationException` unconditionally, there's no way to accidentally get a mutable reference to the same backing data, and the resulting collections also reject `null` elements outright (throwing `NullPointerException` immediately at construction, rather than silently accepting a `null` that causes a confusing failure somewhere else later). Reach for these factories any time you need a fixed, small, truly-immutable collection — constants, default values, test fixtures, or any data that should never change after creation.

## 3. Core concept

```java
List<String> names = List.of("Ann", "Bo", "Cy");
Set<Integer> primes = Set.of(2, 3, 5, 7);
Map<String, Integer> scores = Map.of("Ann", 90, "Bo", 85); // convenient up to 10 key-value pairs

Map<String, Integer> manyScores = Map.ofEntries( // for more than 10 pairs, or when built dynamically
    Map.entry("Ann", 90),
    Map.entry("Bo", 85),
    Map.entry("Cy", 78)
);

names.add("Deb"); // throws UnsupportedOperationException — truly immutable, not just "fixed size"
```

`Map.of` has overloads for 0 through 10 key-value pairs, passed as alternating key/value arguments; beyond 10 pairs (or when the pairs are computed rather than literal), `Map.ofEntries(Map.entry(k1, v1), ...)` is the general-purpose form.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="List.of/Set.of/Map.of return genuinely immutable collections that reject every mutating operation">
  <rect x="20" y="20" width="280" height="45" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="47" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">List.of("a","b","c")</text>

  <rect x="320" y="20" width="300" height="45" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="470" y="40" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">.add(x) / .set(i,x) / .remove(x)</text>
  <text x="470" y="56" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">-&gt; UnsupportedOperationException</text>

  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">Contrast: Arrays.asList("a","b","c") permits .set(i, x) — fixed SIZE, but not fully immutable.</text>
  <text x="20" y="120" fill="#8b949e" font-size="10" font-family="sans-serif">List.of blocks EVERY mutation, including .set — genuinely immutable, not just fixed-size.</text>
</svg>

Every mutating method throws, unconditionally — there is no partial-mutability loophole the way `Arrays.asList` has.

## 5. Runnable example

Scenario: defining a small, fixed configuration for a game's difficulty levels — starting with a plain immutable list of level names, then a set of "boss" levels and a map of level-to-enemy-count, then combining all three into a single immutable configuration object built once and shared safely across the program.

### Level 1 — Basic

```java
import java.util.*;

public class ImmutableBasic {
    public static void main(String[] args) {
        List<String> levels = List.of("Forest", "Cave", "Castle", "Volcano");
        System.out.println(levels);

        try {
            levels.add("Sky Fortress");
        } catch (UnsupportedOperationException e) {
            System.out.println("Cannot add: list is immutable");
        }
    }
}
```

**How to run:** `java ImmutableBasic.java`

Expected output:
```
[Forest, Cave, Castle, Volcano]
Cannot add: list is immutable
```

`List.of(...)` returns a genuinely immutable list. Calling `.add("Sky Fortress")` on it throws `UnsupportedOperationException`, caught by the `catch` block, which prints `"Cannot add: list is immutable"` — the list itself is never modified, since the mutation is rejected before it can take effect.

### Level 2 — Intermediate

```java
import java.util.*;

public class ImmutableCollections {
    public static void main(String[] args) {
        List<String> levels = List.of("Forest", "Cave", "Castle", "Volcano");
        Set<String> bossLevels = Set.of("Castle", "Volcano");
        Map<String, Integer> enemyCounts = Map.of("Forest", 5, "Cave", 8, "Castle", 12, "Volcano", 20);

        for (String level : levels) {
            String bossTag = bossLevels.contains(level) ? " (BOSS LEVEL)" : "";
            System.out.println(level + ": " + enemyCounts.get(level) + " enemies" + bossTag);
        }
    }
}
```

**How to run:** `java ImmutableCollections.java`

Expected output:
```
Forest: 5 enemies
Cave: 8 enemies
Castle: 12 enemies (BOSS LEVEL)
Volcano: 20 enemies (BOSS LEVEL)
```

The real-world concern this adds: **three different immutable collection types working together** — a `List` for ordering, a `Set` for fast membership checks (`bossLevels.contains(level)`), and a `Map` for key-based lookups (`enemyCounts.get(level)`) — all built with the same `of(...)` factory pattern, all genuinely immutable, and all safely shareable across a program with zero risk of one part of the code accidentally mutating data another part relies on staying fixed.

### Level 3 — Advanced

```java
import java.util.*;

public class GameConfig {
    record LevelConfig(List<String> levelOrder, Set<String> bossLevels, Map<String, Integer> enemyCounts) {
        static GameConfig.LevelConfig standard() {
            return new LevelConfig(
                List.of("Forest", "Cave", "Castle", "Volcano", "Sky Fortress"),
                Set.of("Castle", "Volcano", "Sky Fortress"),
                Map.ofEntries( // more than 10 pairs would need this form; used here for clarity/extensibility
                    Map.entry("Forest", 5),
                    Map.entry("Cave", 8),
                    Map.entry("Castle", 12),
                    Map.entry("Volcano", 20),
                    Map.entry("Sky Fortress", 35)
                )
            );
        }
    }

    public static void main(String[] args) {
        LevelConfig config = LevelConfig.standard();

        int totalEnemies = 0;
        for (String level : config.levelOrder()) {
            totalEnemies += config.enemyCounts().get(level);
        }

        System.out.println("Levels: " + config.levelOrder().size());
        System.out.println("Boss levels: " + config.bossLevels().size());
        System.out.println("Total enemies across all levels: " + totalEnemies);

        // Prove the whole config is safe to hand to untrusted code: nothing can mutate it.
        try {
            config.enemyCounts().put("Forest", 999);
        } catch (UnsupportedOperationException e) {
            System.out.println("Config tampering blocked: enemyCounts is immutable");
        }
    }
}
```

**How to run:** `java GameConfig.java`

Expected output:
```
Levels: 5
Boss levels: 3
Total enemies across all levels: 80
Config tampering blocked: enemyCounts is immutable
```

This handles the production-flavoured case of a **fully immutable configuration object** — a `record` (itself immutable by construction) whose fields are all `List.of`/`Set.of`/`Map.ofEntries`-built collections, meaning the *entire* `LevelConfig` is deeply immutable: neither the record's own fields nor the collections those fields hold can ever be reassigned or mutated after construction. This makes `GameConfig.LevelConfig.standard()` safe to share freely — pass it to any code, anywhere, including code you don't fully trust, with a compiler- and runtime-enforced guarantee that nothing can corrupt the shared configuration.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `LevelConfig.standard()` is called, which constructs a `LevelConfig` record with three immutable collections: `levelOrder` (a `List<String>` of five level names, in order), `bossLevels` (a `Set<String>` of three level names), and `enemyCounts` (a `Map<String, Integer>` built via `Map.ofEntries(...)`, since it's clearer and more extensible than the positional `Map.of(k1, v1, k2, v2, ...)` form once there are several pairs).

Back in `main`, the `for (String level : config.levelOrder())` loop iterates the five levels in their declared order: `Forest`, `Cave`, `Castle`, `Volcano`, `Sky Fortress`. For each, `config.enemyCounts().get(level)` looks up that level's enemy count and adds it to `totalEnemies`.

```
totalEnemies accumulation:

Forest         -> enemyCounts.get("Forest")       = 5   -> totalEnemies = 5
Cave           -> enemyCounts.get("Cave")         = 8   -> totalEnemies = 13
Castle         -> enemyCounts.get("Castle")       = 12  -> totalEnemies = 25
Volcano        -> enemyCounts.get("Volcano")      = 20  -> totalEnemies = 45
Sky Fortress   -> enemyCounts.get("Sky Fortress") = 35  -> totalEnemies = 80
```

After the loop, `totalEnemies` is `80`. `main` prints `config.levelOrder().size()` (`5`), `config.bossLevels().size()` (`3`), and `totalEnemies` (`80`), each on its own line.

Finally, `main` attempts `config.enemyCounts().put("Forest", 999)` inside a `try` block — an attempt to overwrite `"Forest"`'s enemy count. Because `enemyCounts` was built with `Map.ofEntries(...)`, it's genuinely immutable: `put(...)` is one of the mutating operations every `Map.of`/`Map.ofEntries`-produced map unconditionally rejects, throwing `UnsupportedOperationException` immediately, before any actual modification could occur — the map's internal state is entirely untouched. The `catch` block catches this exception and prints `"Config tampering blocked: enemyCounts is immutable"`, demonstrating that the configuration genuinely cannot be corrupted by code holding a reference to it, whether that attempted mutation was accidental or deliberate.

## 7. Gotchas & takeaways

> `List.of`, `Set.of`, and `Map.of`/`Map.ofEntries` all reject `null` elements, keys, or values — attempting `List.of("a", null, "c")` or `Map.of("key", null)` throws `NullPointerException` **immediately, at construction time**, not later when the `null` might actually be accessed. This is a deliberate design choice (unlike `ArrayList`, which permits `null` freely) and a common surprise for code migrating from mutable collections that happened to rely on storing `null`.

- `Set.of(...)` throws `IllegalArgumentException` if given duplicate elements — unlike `HashSet`, which would silently drop duplicates, `Set.of` treats a duplicate as a caller error worth failing loudly on, since the caller almost certainly didn't intend to pass the same value twice.
- The iteration order of `Set.of(...)` and `Map.of(...)` is intentionally **unspecified and may vary between JVM runs** (even within the same program execution across different calls) — this is a deliberate design choice to prevent code from accidentally depending on an iteration order the API never promised; `List.of(...)`, by contrast, always preserves the exact order elements were passed in, since ordering is `List`'s whole purpose.
- These factory methods return specific, internal implementation classes (not `ArrayList`, `HashSet`, or `HashMap`) optimized for the immutable, fixed-size case — don't assume `List.of(...).getClass()` is `ArrayList.class`, and don't rely on any behavior beyond what the `List`/`Set`/`Map` interfaces themselves guarantee.
- For converting an *existing*, potentially mutable collection into an immutable one, `List.copyOf(existingList)` (and the `Set`/`Map` equivalents, also added in Java 10) create a genuinely immutable copy — distinct from `Collections.unmodifiableList(existingList)`, which only wraps the original list and still reflects any subsequent mutation to that original, underlying list.
- `Map.of(...)`'s positional overloads only go up to 10 key-value pairs (an intentional cap to keep the overload set finite and readable) — beyond that, `Map.ofEntries(Map.entry(k, v), ...)` is the only option, and is also generally preferable stylistically once a map has more than a handful of entries, since positional key/value pairs become harder to read correctly at a glance as the list grows.
