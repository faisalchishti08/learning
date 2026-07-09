---
card: java
gi: 561
slug: map-default-methods-getordefault-putifabsent-computeifabsent
title: Map default methods (getOrDefault, putIfAbsent, computeIfAbsent, computeIfPresent, compute, merge, forEach, replaceAll)
---

## 1. What it is

Java 8 added a batch of default methods directly on the `Map` interface — `getOrDefault`, `putIfAbsent`, `computeIfAbsent`, `computeIfPresent`, `compute`, `merge`, `forEach`, and `replaceAll` — that express common "check, then act" patterns as a single atomic-looking call, instead of the classic `containsKey`/`get`/`put` combinations everyone hand-wrote before.

## 2. Why & when

Before Java 8, a very common pattern was: "get the value for this key, or a default if it's missing," or "add this key only if it isn't already there," or "build a list for this key if one doesn't exist yet, then add to it." Each of these took two or three map calls and manual null-checking, e.g. `if (!map.containsKey(k)) map.put(k, new ArrayList<>()); map.get(k).add(v);` — verbose, and on a `ConcurrentHashMap`, actually *not* atomic when written that way (a race between the check and the put). The new default methods express the same intent in one call, and on `ConcurrentHashMap` specifically, several of them (`computeIfAbsent`, `merge`, etc.) are implemented atomically. Reach for these any time you'd otherwise write a `containsKey`-then-`get`-or-`put` pair.

## 3. Core concept

```java
Map<String, Integer> counts = new HashMap<>();

counts.getOrDefault("x", 0);                       // 0, no exception, no mutation
counts.putIfAbsent("x", 1);                         // inserts 1 only if "x" absent
counts.computeIfAbsent("y", k -> 0);                // inserts 0 for "y" if absent, returns it
counts.merge("x", 1, Integer::sum);                 // "x" -> old value + 1 (or 1 if absent)
counts.computeIfPresent("x", (k, v) -> v * 10);      // updates "x" only if present
counts.forEach((k, v) -> System.out.println(k + "=" + v));
counts.replaceAll((k, v) -> v + 100);                // transforms every value in place
```

Each method targets a specific "is the key there or not" branch so callers stop writing that branch by hand.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Map default methods each encode a specific present/absent decision">
  <rect x="10" y="10" width="300" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="160" y="35" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">putIfAbsent(k, v)</text>
  <text x="320" y="35" fill="#8b949e" font-size="10" font-family="sans-serif">only writes if key is ABSENT</text>

  <rect x="10" y="60" width="300" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">computeIfPresent(k, f)</text>
  <text x="320" y="85" fill="#8b949e" font-size="10" font-family="sans-serif">only writes if key is PRESENT</text>

  <rect x="10" y="110" width="300" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="160" y="135" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace">computeIfAbsent(k, f)</text>
  <text x="320" y="135" fill="#8b949e" font-size="10" font-family="sans-serif">computes &amp; writes only if ABSENT</text>

  <rect x="10" y="160" width="300" height="40" rx="6" fill="#1c2430" stroke="#d2a8ff"/>
  <text x="160" y="185" fill="#d2a8ff" font-size="11" text-anchor="middle" font-family="monospace">merge(k, v, f)</text>
  <text x="320" y="185" fill="#8b949e" font-size="10" font-family="sans-serif">writes v if ABSENT, else f(old, v)</text>
</svg>

Each method is named for exactly the present/absent branch it handles — pick the one matching your intent.

## 5. Runnable example

Scenario: counting word frequencies and grouping words by their first letter from a stream of text — starting with a basic frequency counter, then adding a grouped index built with `computeIfAbsent`, then combining both into a single-pass word-analysis report using several default methods together.

### Level 1 — Basic

```java
import java.util.*;

public class WordCountBasic {
    public static void main(String[] args) {
        String[] words = {"the", "cat", "sat", "on", "the", "mat", "the", "cat"};
        Map<String, Integer> counts = new HashMap<>();

        for (String word : words) {
            counts.merge(word, 1, Integer::sum);
        }

        counts.forEach((word, count) -> System.out.println(word + ": " + count));
    }
}
```

**How to run:** `java WordCountBasic.java`

Expected output (HashMap iteration order is not guaranteed; one valid order shown):
```
the: 3
cat: 2
sat: 1
on: 1
mat: 1
```

`counts.merge(word, 1, Integer::sum)` is the entire counting logic. For a word not yet in the map, `merge` inserts `1` directly (the "no old value" case never calls the function). For a word already present, `merge` calls `Integer::sum` with the old count and `1`, storing the result — so `"the"` goes `absent -> 1 -> sum(1,1)=2 -> sum(2,1)=3` across its three occurrences. `counts.forEach(...)` then prints every entry without a separate `keySet()`/`get()` loop.

### Level 2 — Intermediate

```java
import java.util.*;

public class WordGroupByLetter {
    public static void main(String[] args) {
        String[] words = {"the", "cat", "sat", "on", "the", "mat", "chair", "cup"};
        Map<Character, List<String>> byFirstLetter = new HashMap<>();

        for (String word : words) {
            char first = word.charAt(0);
            byFirstLetter.computeIfAbsent(first, k -> new ArrayList<>()).add(word);
        }

        byFirstLetter.forEach((letter, list) -> System.out.println(letter + " -> " + list));
    }
}
```

**How to run:** `java WordGroupByLetter.java`

Expected output (order not guaranteed; content shown):
```
t -> [the, the]
c -> [cat, cat, chair, cup]
s -> [sat]
o -> [on]
m -> [mat]
```

The real-world concern this adds: building a **grouped index** — a `Map<Character, List<String>>` — where each key's value is a mutable collection that must be created exactly once. `computeIfAbsent(first, k -> new ArrayList<>())` returns the existing list if `first` is already a key, or creates, stores, and returns a brand-new `ArrayList` if not — either way, `.add(word)` is called on the correct list in a single expression, with no separate `containsKey` check.

### Level 3 — Advanced

```java
import java.util.*;

public class WordAnalysisReport {
    record Stats(int totalCount, Set<Character> firstLetters) {}

    public static void main(String[] args) {
        String[] words = {"the", "cat", "sat", "on", "the", "mat", "chair", "cup", "the"};
        Map<String, Integer> counts = new HashMap<>();
        Map<Character, List<String>> byFirstLetter = new HashMap<>();

        for (String word : words) {
            counts.merge(word, 1, Integer::sum);
            byFirstLetter.computeIfAbsent(word.charAt(0), k -> new ArrayList<>()).add(word);
        }

        // Only bump the count for words seen 2+ times — leave singletons untouched.
        counts.computeIfPresent("the", (word, count) -> count >= 2 ? count : null);

        // Normalize every grouped list: replace with a de-duplicated, sorted view.
        byFirstLetter.replaceAll((letter, list) -> {
            List<String> unique = new ArrayList<>(new TreeSet<>(list));
            return unique;
        });

        System.out.println("Counts: " + new TreeMap<>(counts));
        System.out.println("Groups: " + new TreeMap<>(byFirstLetter));
        System.out.println("Unknown word count: " + counts.getOrDefault("zebra", 0));
    }
}
```

**How to run:** `java WordAnalysisReport.java`

Expected output:
```
Counts: {cat=1, chair=1, cup=1, mat=1, on=1, sat=1, the=3}
Groups: {c=[cat, chair, cup], m=[mat], o=[on], s=[sat], t=[the]}
Unknown word count: 0
```

This combines four default methods in one pass: `merge` for counting, `computeIfAbsent` for grouped-list building, `computeIfPresent` for a conditional update (that in this case leaves `"the"`'s count of 3 unchanged, since 3 >= 2), and `replaceAll` to transform every value in the grouping map in place — de-duplicating and sorting each letter's word list — exactly the kind of multi-step normalization a real word-frequency report would need.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `words` has 9 entries with `"the"` appearing three times, `"cat"` and others once each.

The main loop processes each word, calling both `counts.merge(...)` and `byFirstLetter.computeIfAbsent(...).add(...)` per word — building both maps in a single pass over the array. After the loop, `counts` holds `{the=3, cat=1, sat=1, on=1, mat=1, chair=1, cup=1}` and `byFirstLetter` holds `{t=[the,the,the], c=[cat,chair,cup], s=[sat], o=[on], m=[mat]}` (insertion order within each list, duplicates included).

`counts.computeIfPresent("the", (word, count) -> count >= 2 ? count : null)` is called next. Since `"the"` is present with count `3`, the lambda runs with `word="the"`, `count=3`. The condition `count >= 2` is `true`, so the lambda returns `count` (`3`) unchanged — `computeIfPresent` writes that value back, so `counts.get("the")` is still `3`. (Had the lambda returned `null`, `computeIfPresent` would have *removed* the key entirely — that's the documented behavior for a `null` result, useful for conditional removal in one call.)

`byFirstLetter.replaceAll((letter, list) -> {...})` iterates every entry currently in `byFirstLetter` and replaces each value with the lambda's result:

```
letter='t', list=[the,the,the] -> new TreeSet<>(list) = {the} -> new ArrayList<>({the}) = [the]
letter='c', list=[cat,chair,cup] -> TreeSet sorts+dedupes -> [cat, chair, cup]
letter='s', list=[sat] -> [sat]
letter='o', list=[on]  -> [on]
letter='m', list=[mat] -> [mat]
```

`new TreeSet<>(list)` both removes duplicates (a `Set` can't hold repeats) and sorts alphabetically (`TreeSet`'s natural ordering for `String`); wrapping it in `new ArrayList<>(...)` converts back to a `List` for the map's value type. After `replaceAll`, `byFirstLetter` holds cleaned, de-duplicated, sorted lists for every letter.

`main` prints `counts` and `byFirstLetter` wrapped in `new TreeMap<>(...)` purely for deterministic, alphabetically-ordered output (since `HashMap` iteration order isn't guaranteed) — this doesn't change the underlying data, only how it's displayed. Finally, `counts.getOrDefault("zebra", 0)` looks up a key that was never inserted; since it's absent, `getOrDefault` returns the fallback `0` directly, without throwing or mutating the map.

## 7. Gotchas & takeaways

> `computeIfAbsent`, `computeIfPresent`, `compute`, and `merge` all treat a **mapping function that returns `null` as "remove this key."** If your value-producing lambda can legitimately return `null` for reasons unrelated to "delete this entry" (e.g., a business value that happens to be `null`), these methods will silently delete the mapping instead of storing `null` — a subtle source of bugs. If you need to store an actual `null` value, use `put` directly instead.

- `getOrDefault(key, fallback)` never mutates the map — it's a pure read with a substitute value, unlike the others in this group.
- `putIfAbsent` returns the *existing* value if the key was already present (and does nothing), or `null` if it inserted the new value — check the return value if you need to know which happened.
- `computeIfAbsent` is the standard one-liner for "get-or-create a mutable collection value" (`Map<K, List<V>>`, `Map<K, Set<V>>`), and its implementation on `ConcurrentHashMap` guarantees the creation happens at most once per key even under concurrent access.
- `merge(key, value, remappingFunction)` is the standard one-liner for counters and accumulators — `counts.merge(k, 1, Integer::sum)` is the idiomatic replacement for the old `containsKey`/`get`/`put` counting dance.
- `forEach` and `replaceAll` both iterate the *live* map — `replaceAll` may only replace values (not add or remove keys), while structural modification (adding/removing keys) during either call throws `ConcurrentModificationException`, same as iterating with an `Iterator` directly.
