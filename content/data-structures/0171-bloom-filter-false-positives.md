---
card: data-structures
gi: 171
slug: bloom-filter-false-positives
title: Bloom filter (false positives)
---

## 1. What it is

A **Bloom filter** is a compact structure that answers "have I possibly seen this item before?" using far less memory than storing the items themselves. It trades perfect accuracy for space: it can say "definitely not seen" with total certainty, but "possibly seen" can occasionally be wrong — a **false positive**. It never produces a false negative.

## 2. Why & when

Use a Bloom filter when you need a fast, memory-cheap pre-check before an expensive lookup — checking if a URL might be malicious before querying a database, checking if a username might already be taken before hitting the main table, or checking if a cache might contain a key before a disk read. Storing a hash set of a billion items can take gigabytes; a Bloom filter for the same billion items, at a reasonable false-positive rate, can take a fraction of that.

## 3. Core concept

**The shape.** A bit array of size `m`, all initialized to `0`, plus `k` independent hash functions. There is no way to recover the original items from the filter — it only ever answers yes/no.

**Adding an item.** Run the item through all `k` hash functions, each producing an index into the bit array (`index = hash_i(item) % m`), and set every one of those `k` bits to `1`.

**Checking an item.** Run the same `k` hash functions on the query item. If **any** of the resulting `k` bits is still `0`, the item was **definitely never added** — a `0` bit could only exist if no add operation ever touched it. If **all** `k` bits are `1`, the item was **probably added** — but those bits could have all been set to `1` by *other* items' hashes coincidentally overlapping, which is exactly what causes a false positive.

**Why false positives happen but false negatives cannot.** Adding never clears a bit, only sets it. So once an item's bits are all `1` after it is added, they stay `1` forever (ignoring deletion, which basic Bloom filters do not support) — a real member always checks out as "possibly present." But other items sharing those same bit positions can make a *never-added* item's bits all coincidentally read as `1` too — that is the false positive.

**The tradeoff knobs.** More bits (`m`) per item and more hash functions (`k`) reduce the false-positive rate, at the cost of more memory and more hashing work per operation. There is a well-known formula to pick `m` and `k` for a target false-positive rate given the expected number of items — but the intuition (bigger filter, more hashes, both up to a point, means fewer false positives) is what matters most.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A bit array where adding two items sets several bits, and checking a third unrelated item happens to find all its bits already set by coincidence">
  <g font-family="sans-serif" font-size="10" fill="#e6edf3">
    <text x="10" y="20">bit array (m=16):</text>
    <g transform="translate(10,30)">
      <rect x="0" y="0" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="15" y="16" text-anchor="middle">0</text>
      <rect x="30" y="0" width="30" height="24" fill="#3fb950" fill-opacity="0.3" stroke="#3fb950"/><text x="45" y="16" text-anchor="middle">1</text>
      <rect x="60" y="0" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="75" y="16" text-anchor="middle">0</text>
      <rect x="90" y="0" width="30" height="24" fill="#3fb950" fill-opacity="0.3" stroke="#3fb950"/><text x="105" y="16" text-anchor="middle">1</text>
      <rect x="120" y="0" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="135" y="16" text-anchor="middle">0</text>
      <rect x="150" y="0" width="30" height="24" fill="#f0883e" fill-opacity="0.3" stroke="#f0883e"/><text x="165" y="16" text-anchor="middle">1</text>
      <rect x="180" y="0" width="30" height="24" fill="#0d1117" stroke="#8b949e"/><text x="195" y="16" text-anchor="middle">0</text>
      <rect x="210" y="0" width="30" height="24" fill="#3fb950" fill-opacity="0.3" stroke="#3fb950"/><text x="225" y="16" text-anchor="middle">1</text>
    </g>
    <text x="10" y="85" font-size="9" fill="#3fb950">green bits: set by "apple" (indices 1, 3, 7)</text>
    <text x="10" y="100" font-size="9" fill="#f0883e">orange bit: set by "banana" (index 5, plus others not shown)</text>
    <text x="10" y="130" font-size="9" fill="#e6edf3">check("grape"): hashes to indices 1, 3, 5 -- ALL already 1 (by coincidence)</text>
    <text x="10" y="145" font-size="9" fill="#e6edf3">-&gt; false positive: "grape" reported as possibly present, though never added</text>
  </g>
</svg>

Every added item only sets bits; a lucky coincidence of overlapping bits produces a false positive.

## 5. Runnable example

```java
// BloomFilter.java
import java.util.*;

public class BloomFilter {

    // Basic: a Bloom filter using two simple hash functions derived from Java's hashCode.
    static class SimpleBloomFilter {
        boolean[] bits;
        int size;
        int hashCount;

        SimpleBloomFilter(int size, int hashCount) {
            this.size = size;
            this.hashCount = hashCount;
            bits = new boolean[size];
        }

        int[] hashesFor(String item) {
            int[] result = new int[hashCount];
            int h1 = item.hashCode();
            int h2 = Integer.reverse(h1) ^ 0x5bd1e995; // a second, cheap independent-ish hash
            for (int i = 0; i < hashCount; i++) {
                int combined = h1 + i * h2;
                result[i] = Math.floorMod(combined, size);
            }
            return result;
        }

        void add(String item) {
            for (int index : hashesFor(item)) bits[index] = true;
        }

        boolean mightContain(String item) {
            for (int index : hashesFor(item)) {
                if (!bits[index]) return false; // definitely not present
            }
            return true; // possibly present
        }
    }

    static void basicLevel() {
        SimpleBloomFilter filter = new SimpleBloomFilter(1000, 3);
        filter.add("apple");
        filter.add("banana");

        System.out.println("basic: mightContain(\"apple\") -> " + filter.mightContain("apple"));
        System.out.println("basic: mightContain(\"cherry\") -> " + filter.mightContain("cherry"));
    }

    // Intermediate: measure the observed false-positive rate empirically against a real HashSet.
    static void intermediateLevel() {
        SimpleBloomFilter filter = new SimpleBloomFilter(10_000, 5);
        Set<String> added = new HashSet<>();
        for (int i = 0; i < 1000; i++) {
            String item = "item-" + i;
            filter.add(item);
            added.add(item);
        }

        int falsePositives = 0;
        int trials = 5000;
        for (int i = 1000; i < 1000 + trials; i++) {
            String item = "item-" + i; // never added
            if (filter.mightContain(item)) falsePositives++;
        }
        System.out.printf("intermediate: observed false-positive rate -> %.2f%%%n", 100.0 * falsePositives / trials);
    }

    // Advanced: compare filter size vs false-positive rate, showing the space/accuracy tradeoff directly.
    static double measureFalsePositiveRate(int bits, int hashCount, int itemsAdded, int trials) {
        SimpleBloomFilter filter = new SimpleBloomFilter(bits, hashCount);
        for (int i = 0; i < itemsAdded; i++) filter.add("member-" + i);

        int falsePositives = 0;
        for (int i = itemsAdded; i < itemsAdded + trials; i++) {
            if (filter.mightContain("member-" + i)) falsePositives++;
        }
        return 100.0 * falsePositives / trials;
    }

    static void advancedLevel() {
        System.out.printf("advanced: small filter (2000 bits) rate -> %.2f%%%n", measureFalsePositiveRate(2000, 3, 1000, 5000));
        System.out.printf("advanced: large filter (20000 bits) rate -> %.2f%%%n", measureFalsePositiveRate(20000, 3, 1000, 5000));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

How to run: `java BloomFilter.java`

## 6. Walkthrough

Create a filter with `size = 1000` bits and `hashCount = 3`. Call `add("apple")`: compute 3 indices from `"apple"`'s hash combinations, and set those 3 bits to `true`. Call `add("banana")`: compute 3 different (probably) indices, set those to `true` too.

Check `mightContain("apple")`: recompute the same 3 indices used during `add("apple")` — since hashing is deterministic, they are identical. All 3 bits are `true` (set during the earlier `add`), so return `true` — correctly "possibly present," and in fact genuinely present.

Check `mightContain("cherry")`, an item never added: compute its 3 indices. If even one of those 3 bits happens to still be `false` (never touched by any `add` call), return `false` immediately — a guaranteed-correct "definitely not present." Only if all 3 land on bits that some other add operation happened to set (by coincidence) does the filter incorrectly answer `true`.

The `intermediateLevel` experiment adds 1000 real items, then checks 5000 different never-added items, counting how often the filter incorrectly says "possibly present." Comparing a small filter (2000 bits) against a large filter (20000 bits) for the same 1000 items in `advancedLevel` shows the false-positive rate drop sharply as the bit array grows relative to the number of items stored.

**Complexity.** Add: `O(k)` for `k` hash functions. Check: `O(k)`. Space: `O(m)` bits, independent of the size of the items themselves — a filter for URLs of any length still only needs `m` bits total.

## 7. Gotchas & takeaways

> A standard Bloom filter cannot support deletion. Clearing a bit to remove one item can un-set a bit that another item's membership also depends on, silently turning that other item into a false negative — which breaks the filter's core guarantee. A **counting Bloom filter** (using small counters instead of single bits) is the fix if deletion is required.

- Always follow up a Bloom filter "possibly present" answer with the real, authoritative check (the database query, the disk read) — the filter is a fast pre-filter to skip expensive lookups for definite non-members, never a replacement for the real check.
- More hash functions is not always better: too many `k` relative to `m` sets so many bits that the filter saturates toward all-`1`s, which *increases* the false-positive rate. The optimal `k` is roughly `(m/n) * ln(2)` for `n` expected items.
- For counting distinct items instead of membership, look at [HyperLogLog](0176-hyperloglog-for-cardinality-estimation.md) — a related but different probabilistic structure solving a different question.
