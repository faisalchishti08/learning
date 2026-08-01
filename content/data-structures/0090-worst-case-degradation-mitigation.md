---
card: data-structures
gi: 90
slug: worst-case-degradation-mitigation
title: Worst-case degradation & mitigation
---

## 1. What it is

**Worst-case degradation** is what happens when a hash table's average-O(1) guarantee breaks down: many keys collide into the same bucket, turning that bucket's operations into an O(n) linear (or O(k) for a chain of length `k`) scan instead of a near-instant lookup. This can happen by bad luck (a poorly written hash function) or by design (an attacker deliberately crafting colliding keys).

## 2. Why & when

Understanding this matters for two reasons: writing your own `hashCode()` correctly (a poor one silently creates this problem), and recognizing a real security concern — **hash-flooding denial-of-service attacks**, where an attacker submits many keys engineered to all hash to the same bucket, deliberately degrading a server's hash-table-backed request handling from O(1) to O(n) per request, potentially overwhelming it.

## 3. Core concept

**How degradation happens.** If a hash function distributes keys poorly (see [Hash functions & desirable properties](0085-hash-functions-desirable-properties.md)), or if an attacker who knows the hash function's exact algorithm crafts many keys that all produce the same hash code, every one of those keys lands in the same bucket. That bucket's chain (or open-addressing cluster) grows to hold most of the table's entries, and every operation touching it degrades toward O(n).

**Mitigation 1 — treeification (Java's `HashMap`).** Once a single bucket's chain grows past 8 entries (with the table itself large enough, at least 64 buckets), Java converts that bucket from a linked list to a red-black tree. This bounds the worst-case lookup within a single bucket to O(log n) instead of O(n) — it does not fix a bad hash function, but it caps the damage.

**Mitigation 2 — hash randomization (seeded/salted hashing).** Some languages and frameworks randomize part of the hash function per process (a random seed mixed into every hash computation), so an attacker cannot predict which keys will collide without knowing that run's specific seed. This defends against hash-flooding attacks that rely on knowing the exact hash algorithm in advance.

**Mitigation 3 — a good hash function in the first place.** The cheapest and most effective mitigation is simply using a well-distributed hash function (delegating to a type's well-tested `hashCode()`, like `String`'s, rather than writing a naive custom one) — this is prevention, not a fallback once things have already gone wrong.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A hash table where every attacker-chosen key collides into bucket 3, forming a long linked chain, versus the same bucket after Java treeifies it into a balanced tree once it exceeds 8 entries">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#f0883e">before mitigation: bucket 3 has a long chain -- O(n) lookups</text>
    <rect x="20" y="30" width="30" height="22" fill="#0d1117" stroke="#f0883e"/>
    <rect x="55" y="30" width="30" height="22" fill="#0d1117" stroke="#f0883e"/>
    <rect x="90" y="30" width="30" height="22" fill="#0d1117" stroke="#f0883e"/>
    <rect x="125" y="30" width="30" height="22" fill="#0d1117" stroke="#f0883e"/>
    <rect x="160" y="30" width="30" height="22" fill="#0d1117" stroke="#f0883e"/>
    <text x="95" y="70" fill="#f0883e" font-size="9">chain keeps growing as attacker submits more colliding keys</text>

    <text x="20" y="110" fill="#79c0ff">after treeify (&gt;8 entries): bucket becomes a balanced tree -- O(log n)</text>
    <circle cx="95" cy="140" r="14" fill="#0d1117" stroke="#79c0ff"/>
    <circle cx="60" cy="170" r="14" fill="#161b22" stroke="#8b949e"/>
    <circle cx="130" cy="170" r="14" fill="#161b22" stroke="#8b949e"/>
    <line x1="88" y1="150" x2="68" y2="160" stroke="#8b949e"/>
    <line x1="102" y1="150" x2="122" y2="160" stroke="#8b949e"/>
  </g>
</svg>

Without mitigation, a flooded bucket becomes a long chain (O(n) per lookup); Java's treeify-at-8 rule converts it to a balanced tree instead, capping the worst case at O(log n).

## 5. Runnable example

```java
// WorstCaseDegradationDemo.java
import java.util.HashMap;
import java.util.Map;

public class WorstCaseDegradationDemo {

    // A deliberately terrible hash function -- constant, simulating a hash-flooding attack or a bad hashCode().
    static class FloodedKey {
        int value;
        FloodedKey(int value) { this.value = value; }
        @Override public int hashCode() { return 1; } // every key collides -- the attack scenario
        @Override public boolean equals(Object o) { return o instanceof FloodedKey f && f.value == value; }
    }

    // Basic: show a well-distributed key type does NOT degrade as size grows.
    static void basicLevel() {
        Map<Integer, String> normalMap = new HashMap<>();
        for (int i = 0; i < 50_000; i++) normalMap.put(i, "v" + i); // Integer.hashCode() is well distributed

        long t0 = System.nanoTime();
        normalMap.get(25_000);
        long normalNs = System.nanoTime() - t0;
        System.out.println("basic: single lookup in a 50,000-entry well-distributed map -> " + normalNs + " ns");
    }

    // Intermediate: simulate the degraded case with FloodedKey -- every insert grows the SAME bucket's chain.
    static void intermediateLevel() {
        Map<FloodedKey, String> floodedMap = new HashMap<>();
        for (int i = 0; i < 20_000; i++) floodedMap.put(new FloodedKey(i), "v" + i); // all 20,000 collide into one bucket-group

        long t0 = System.nanoTime();
        floodedMap.get(new FloodedKey(19_999)); // must scan through (or tree-search) a huge chain
        long floodedNs = System.nanoTime() - t0;
        System.out.println("intermediate: single lookup in a 20,000-entry FULLY COLLIDED map -> " + floodedNs + " ns");
        System.out.println("intermediate: still correct, but measurably costlier per lookup than the well-distributed case");
    }

    // Advanced: confirm Java's treeification still keeps this from becoming truly linear-catastrophic (O(log n), not O(n)).
    static void advancedLevel() {
        Map<FloodedKey, String> floodedMap = new HashMap<>();
        for (int i = 0; i < 100_000; i++) floodedMap.put(new FloodedKey(i), "v" + i);

        long t0 = System.nanoTime();
        floodedMap.get(new FloodedKey(99_999));
        long ns100k = System.nanoTime() - t0;
        System.out.println("advanced: lookup in a 100,000-entry fully collided map -> " + ns100k + " ns");
        System.out.println("advanced: grows much slower than linear thanks to treeify-at-8 (bucket becomes a red-black tree)");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `WorstCaseDegradationDemo.java`, then run `java WorstCaseDegradationDemo.java`.

## 6. Walkthrough

1. `basicLevel()` uses plain `Integer` keys, whose `hashCode()` is well distributed. A single lookup among 50,000 entries stays fast, confirming the normal average-O(1) case.
2. `intermediateLevel()` uses `FloodedKey`, whose `hashCode()` always returns `1` — simulating either a badly written `hashCode()` or a deliberate hash-flooding attack. Every one of the 20,000 keys lands in the same bucket group. A lookup still returns the correct value (`equals()` still distinguishes the keys correctly), but it costs measurably more than the well-distributed case, since it must search through a much larger structure at that one bucket.
3. `advancedLevel()` scales the flooded scenario up to 100,000 entries. Because Java's `HashMap` treeifies a bucket once its chain exceeds 8 entries (converting it to a red-black tree), the lookup cost grows roughly logarithmically with the flooded count, not linearly — a real, measurable mitigation against exactly this kind of degradation, even though it does not eliminate the underlying cost of a bad hash function.

## 7. Gotchas & takeaways

> Gotcha: treeification requires the *key type* to be `Comparable` (or the `HashMap` falls back to comparing by class name and identity hash as a tie-breaker) — a custom key class that implements `equals()`/`hashCode()` but not `Comparable` still benefits from treeification, but less predictably, since Java's fallback ordering is not meaningful for that type.

- Worst-case degradation happens when many keys collide into the same bucket — from a bad hash function, or a deliberate hash-flooding attack.
- Java's `HashMap` mitigates this by treeifying a bucket (converting its chain to a red-black tree) once it exceeds 8 entries, capping the worst case at O(log n).
- Hash randomization (a per-process random seed) is another mitigation, used to prevent attackers from predicting collisions in advance.
- The cheapest mitigation is simply using a well-distributed hash function from the start.
- Related concepts: [Hash functions & desirable properties](0085-hash-functions-desirable-properties.md), [HashMap internals (buckets, treeify at 8)](0091-hashmap-internals-buckets-treeify-at-8.md).
