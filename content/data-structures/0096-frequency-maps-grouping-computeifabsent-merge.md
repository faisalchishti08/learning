---
card: data-structures
gi: 96
slug: frequency-maps-grouping-computeifabsent-merge
title: Frequency maps & grouping (computeIfAbsent / merge)
---

## 1. What it is

A **frequency map** counts how many times each distinct value appears in a collection — `Map<T, Integer>` mapping each value to its count. **Grouping** collects related items together under a shared key — `Map<K, List<V>>` mapping each key to the list of items that share it. `computeIfAbsent` and `merge` are `Map` methods that make both patterns concise, replacing a manual "check if present, then initialize or update" block.

## 2. Why & when

These two patterns — counting and grouping — cover a huge share of everyday data-processing tasks: word frequency, counting occurrences for a "majority element" problem, grouping words by their first letter, or grouping objects by a category field. `computeIfAbsent`/`merge` remove the boilerplate `if (!map.containsKey(key)) map.put(key, ...)` dance, and are also measurably less error-prone.

## 3. Core concept

**The old way — manual presence-checking.** Without these methods, building a frequency map requires: `if (map.containsKey(key)) map.put(key, map.get(key) + 1); else map.put(key, 1);` — two map lookups in the common case, and easy to get subtly wrong (like using `get` before confirming the key exists, risking a `NullPointerException` on auto-unboxing).

**`merge(key, value, remappingFunction)`.** If `key` is absent, it is inserted with `value` directly. If `key` is present, its current value and the new `value` are combined via `remappingFunction`, and the result replaces the old value. For counting: `map.merge(key, 1, Integer::sum)` — either insert `1` (first occurrence) or add `1` to the existing count, in one call.

**`computeIfAbsent(key, mappingFunction)`.** If `key` is absent, `mappingFunction` is called to produce a new value, which is inserted and returned. If `key` is present, its existing value is returned directly, and `mappingFunction` is never called. For grouping: `map.computeIfAbsent(key, k -> new ArrayList<>()).add(item)` — either creates a fresh list for a new key, or reuses the existing list, then appends in either case.

**Why these are correct and not just shorter.** Both methods do their check-then-act as a single map operation, avoiding the redundant double-lookup (and, in concurrent maps, a potential race condition) that a manual `containsKey` + `get`/`put` sequence would have.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two patterns side by side: merge combining a new value with an existing one to build a frequency count, and computeIfAbsent creating a list on first use then appending to it for grouping">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#79c0ff">merge: map.merge(key, 1, Integer::sum)</text>
    <text x="20" y="40" fill="#e6edf3">key absent -&gt; insert 1 directly</text>
    <text x="20" y="60" fill="#e6edf3">key present (count=3) -&gt; combine: sum(3, 1) = 4 -&gt; replace</text>

    <text x="340" y="16" fill="#f0883e">computeIfAbsent: map.computeIfAbsent(key, k -&gt; new ArrayList&lt;&gt;())</text>
    <text x="340" y="40" fill="#e6edf3">key absent -&gt; create new empty list, insert, return it</text>
    <text x="340" y="60" fill="#e6edf3">key present -&gt; return the EXISTING list (mappingFunction never called)</text>
    <text x="340" y="85" fill="#f0883e">.add(item) always runs on whichever list was returned</text>
  </g>
</svg>

`merge` combines a new value with any existing one via a function you provide; `computeIfAbsent` lazily creates a value only the first time a key is seen, then hands back whatever is there (new or existing) either way.

## 5. Runnable example

```java
// FrequencyAndGrouping.java
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class FrequencyAndGrouping {

    // Basic: word frequency count using merge().
    static Map<String, Integer> wordFrequency(String[] words) {
        Map<String, Integer> counts = new HashMap<>();
        for (String word : words) {
            counts.merge(word, 1, Integer::sum); // absent -> 1; present -> old + 1
        }
        return counts;
    }

    static void basicLevel() {
        String[] words = {"a", "b", "a", "c", "b", "a"};
        System.out.println("basic: word frequency -> " + wordFrequency(words));
    }

    // Intermediate: grouping words by their first letter using computeIfAbsent().
    static Map<Character, List<String>> groupByFirstLetter(String[] words) {
        Map<Character, List<String>> groups = new HashMap<>();
        for (String word : words) {
            groups.computeIfAbsent(word.charAt(0), k -> new ArrayList<>()).add(word);
        }
        return groups;
    }

    static void intermediateLevel() {
        String[] words = {"apple", "banana", "avocado", "blueberry", "cherry"};
        System.out.println("intermediate: grouped by first letter -> " + groupByFirstLetter(words));
    }

    // Advanced: combine both -- find the most frequent word per group (first letter), using merge AND computeIfAbsent together.
    static Map<Character, String> mostFrequentPerGroup(String[] words) {
        Map<Character, Map<String, Integer>> groupedCounts = new HashMap<>();
        for (String word : words) {
            groupedCounts
                .computeIfAbsent(word.charAt(0), k -> new HashMap<>()) // one frequency map PER first letter
                .merge(word, 1, Integer::sum);                         // count within that group's map
        }

        Map<Character, String> result = new HashMap<>();
        for (Map.Entry<Character, Map<String, Integer>> entry : groupedCounts.entrySet()) {
            String best = null;
            int bestCount = -1;
            for (Map.Entry<String, Integer> wordCount : entry.getValue().entrySet()) {
                if (wordCount.getValue() > bestCount) { best = wordCount.getKey(); bestCount = wordCount.getValue(); }
            }
            result.put(entry.getKey(), best);
        }
        return result;
    }

    static void advancedLevel() {
        String[] words = {"apple", "apple", "avocado", "banana", "banana", "banana"};
        System.out.println("advanced: most frequent word per first letter -> " + mostFrequentPerGroup(words));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `FrequencyAndGrouping.java`, then run `java FrequencyAndGrouping.java`.

## 6. Walkthrough

1. `basicLevel()` processes `["a", "b", "a", "c", "b", "a"]`. Each `merge` call either inserts `1` for a brand-new word, or adds `1` to the existing count. After all six words, `"a"` has been merged three times (`1`, then `2`, then `3`), giving the final count `{a=3, b=2, c=1}`.
2. `intermediateLevel()` processes the same-shaped loop but for grouping: `computeIfAbsent('a', k -> new ArrayList<>())` creates a fresh list the first time letter `'a'` is seen (for `"apple"`), then reuses that same list for `"avocado"` — both end up together under key `'a'`.
3. `advancedLevel()` nests both patterns: `computeIfAbsent` creates a per-first-letter frequency map (a `Map<String, Integer>`) the first time each letter is seen, and `merge` then counts the specific word within that inner map. For `["apple", "apple", "avocado", "banana", "banana", "banana"]`, group `'a'` ends with `{apple=2, avocado=1}` (max: `"apple"`), and group `'b'` ends with `{banana=3}` (max: `"banana"`) — the final result is `{a=apple, b=banana}`.

## 7. Gotchas & takeaways

> Gotcha: `merge`'s remapping function is called with `(oldValue, newValue)`, and if it ever returns `null`, the key is **removed** from the map entirely — this is a deliberate feature (useful for merge-and-possibly-delete patterns), but surprising if you did not expect it; make sure your combining function never accidentally returns `null` when you meant to keep the entry.

- `merge(key, value, fn)` inserts on absence or combines via `fn` on presence — the standard one-liner for counting.
- `computeIfAbsent(key, fn)` creates a value lazily only on first use, then always returns whatever is now stored — the standard one-liner for grouping into a per-key collection.
- Both avoid the double-lookup and edge-case bugs of manual `containsKey` + `get`/`put` logic.
- Related concepts: [HashMap internals (buckets, treeify at 8)](0091-hashmap-internals-buckets-treeify-at-8.md), [hashCode/equals for correct keys](0093-hashcode-equals-for-correct-keys.md).
