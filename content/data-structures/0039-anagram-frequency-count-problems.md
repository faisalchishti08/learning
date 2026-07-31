---
card: data-structures
gi: 39
slug: anagram-frequency-count-problems
title: Anagram & frequency-count problems
---

## 1. What it is

Two strings are **anagrams** if one can be rearranged into the other — they contain exactly the same characters, with exactly the same counts, just in a different order (`"listen"` and `"silent"`). A **frequency count** (also called a character histogram) tracks how many times each character appears in a string, usually with an array (for a known, small alphabet like lowercase letters) or a `HashMap` (for a larger or unknown character set).

## 2. Why & when

Frequency counting is the standard tool for any problem about a string's character *composition* rather than its order — anagram checks, "first non-repeating character," or "can this string be rearranged into a palindrome?" It replaces sorting-based comparison (O(n log n)) with a linear O(n) pass, at the cost of O(k) extra space for an alphabet of size `k`.

## 3. Core concept

**Two ways to check for an anagram.** Sort both strings and compare — if the sorted character sequences match, they are anagrams. This is simple but costs O(n log n) per string. The frequency-count approach counts each character's occurrences in both strings and compares the counts — O(n) total, faster for large inputs.

**Why counting works: an anagram has an identical character multiset.** "Same characters, same counts, any order" is exactly what a frequency count captures directly — it discards order entirely and keeps only the count per character, which is precisely the property that defines an anagram.

**Array vs `HashMap` for counting.** For a fixed, small alphabet (lowercase English letters, 26 possible characters), a `int[26]` array indexed by `c - 'a'` is faster and simpler than a `HashMap<Character, Integer>`. For an unknown or large character set (Unicode text), a `HashMap` is necessary, since you cannot size a fixed array to cover every possible character.

**The "count up, count down" trick for a single-pass anagram check.** Increment a shared frequency array for characters in the first string, decrement for characters in the second string. If the strings are anagrams, every count returns to exactly zero; any nonzero count reveals a mismatch.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A frequency array being incremented by characters of one string and decremented by characters of another, ending at all zeros if they are anagrams">
  <g font-family="sans-serif" font-size="11">
    <text x="320" y="16" fill="#8b949e" text-anchor="middle">"listen" (count up) vs "silent" (count down)</text>
    <rect x="60" y="30" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="80" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">e:0</text>
    <rect x="100" y="30" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="120" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">i:0</text>
    <rect x="140" y="30" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="160" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">l:0</text>
    <rect x="180" y="30" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="200" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">n:0</text>
    <rect x="220" y="30" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="240" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">s:0</text>
    <rect x="260" y="30" width="40" height="26" fill="#161b22" stroke="#3fb950"/><text x="280" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">t:0</text>
    <text x="320" y="90" fill="#79c0ff" text-anchor="middle">all six counts return to exactly 0 -&gt; the two strings ARE anagrams</text>
  </g>
</svg>

Incrementing for one string and decrementing for the other lands every count back at zero exactly when the two strings share the same character multiset.

## 5. Runnable example

```java
// AnagramFrequencyCount.java
import java.util.HashMap;
import java.util.Map;

public class AnagramFrequencyCount {

    // Basic: fixed-size array frequency count for lowercase-letter-only anagrams.
    static boolean isAnagram(String a, String b) {
        if (a.length() != b.length()) return false; // different lengths can never be anagrams
        int[] counts = new int[26];
        for (int i = 0; i < a.length(); i++) counts[a.charAt(i) - 'a']++; // count up for a
        for (int i = 0; i < b.length(); i++) counts[b.charAt(i) - 'a']--; // count down for b
        for (int count : counts) {
            if (count != 0) return false; // a leftover nonzero count means a mismatch
        }
        return true;
    }

    static void basicLevel() {
        System.out.println("basic: \"listen\" vs \"silent\" -> " + isAnagram("listen", "silent"));
        System.out.println("basic: \"hello\" vs \"world\" -> " + isAnagram("hello", "world"));
    }

    // Intermediate: HashMap-based frequency count for arbitrary Unicode text.
    static Map<Character, Integer> frequencyMap(String s) {
        Map<Character, Integer> freq = new HashMap<>();
        for (char c : s.toCharArray()) {
            freq.merge(c, 1, Integer::sum); // increment existing count, or start at 1
        }
        return freq;
    }

    static void intermediateLevel() {
        Map<Character, Integer> freq = frequencyMap("mississippi");
        System.out.println("intermediate: frequency map -> " + freq);
    }

    // Advanced: group a list of words into anagram groups, using each word's sorted form as a key.
    static Map<String, java.util.List<String>> groupAnagrams(String[] words) {
        Map<String, java.util.List<String>> groups = new HashMap<>();
        for (String word : words) {
            char[] chars = word.toCharArray();
            java.util.Arrays.sort(chars);
            String key = new String(chars); // anagrams share the same sorted form
            groups.computeIfAbsent(key, k -> new java.util.ArrayList<>()).add(word);
        }
        return groups;
    }

    static void advancedLevel() {
        String[] words = {"eat", "tea", "tan", "ate", "nat", "bat"};
        Map<String, java.util.List<String>> groups = groupAnagrams(words);
        System.out.println("advanced: anagram groups -> " + groups.values());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `AnagramFrequencyCount.java`, then run `java AnagramFrequencyCount.java`.

## 6. Walkthrough

1. `basicLevel()`'s `isAnagram("listen", "silent")` first checks lengths match (both 6). It increments `counts` for every character of `"listen"`, then decrements for every character of `"silent"` — since both strings share the same letters with the same counts, every slot in `counts` ends at exactly `0`, so the function returns `true`.
2. `isAnagram("hello", "world")` also has matching lengths (5), but their letter counts differ (`"hello"` has two `'l'`s, `"world"` has none) — at least one slot in `counts` ends nonzero, so the function correctly returns `false`.
3. `intermediateLevel()`'s `frequencyMap("mississippi")` builds a `HashMap` counting each character: `{m=1, i=4, s=4, p=2}` — `merge(c, 1, Integer::sum)` either inserts a fresh count of `1` for a new character, or adds `1` to an existing count.
4. `advancedLevel()`'s `groupAnagrams` sorts each word's characters to build a canonical key — `"eat"`, `"tea"`, and `"ate"` all sort to `"aet"`, so they land in the same group, while `"bat"` sorts to `"abt"` and forms its own group.
5. The final grouped output collects `["eat","tea","ate"]`, `["tan","nat"]`, and `["bat"]` as three separate anagram groups, keyed internally by each group's shared sorted form.

## 7. Gotchas & takeaways

> Gotcha: `c - 'a'` as an array index only works correctly for lowercase English letters — running it on uppercase letters, digits, or any Unicode character outside `'a'`-`'z'` produces a negative or out-of-range index, throwing `ArrayIndexOutOfBoundsException`. Normalize case first (`toLowerCase()`), or switch to a `HashMap` for unrestricted input.

- Frequency counting captures a string's character composition, independent of order — exactly what defines an anagram.
- A fixed-size array (`int[26]`) is faster for a known small alphabet; a `HashMap` is required for arbitrary or large character sets.
- The count-up/count-down trick checks two strings for an anagram relationship in a single O(n) pass, without sorting.
- Related concepts: [equals() & hashCode() contract](0014-equals-hashcode-contract.md) (why sorted strings work as HashMap keys for grouping), [Palindrome checking](0040-palindrome-checking.md).
