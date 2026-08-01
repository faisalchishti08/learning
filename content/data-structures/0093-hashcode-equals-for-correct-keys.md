---
card: data-structures
gi: 93
slug: hashcode-equals-for-correct-keys
title: hashCode/equals for correct keys
---

## 1. What it is

For a custom object to work correctly as a `HashMap` key or `HashSet` element, it must override both `hashCode()` and `equals()`, and the two must agree with each other under Java's contract: **if two objects are `equals()`, they must have the same `hashCode()`.** Without this, a hash table cannot reliably find a key it already stored.

## 2. Why & when

This is one of the most common real bugs in Java code: a class overrides `equals()` (so two logically identical objects compare equal) but forgets `hashCode()` (which still uses the default identity-based hash) — the class now silently breaks as a hash table key, since two "equal" instances can land in different buckets and never be found as duplicates of each other.

## 3. Core concept

**The contract, precisely.** 1) If `a.equals(b)` is `true`, then `a.hashCode() == b.hashCode()` must also be `true` — this direction is mandatory. 2) The reverse is *not* required: two objects can have the same `hashCode()` without being `equals()` (that is just a collision, handled normally by the bucket's chain or tree). 3) `hashCode()` must be consistent — calling it multiple times on an unchanged object must return the same value.

**Why a hash table depends on this exactly.** A hash table's `get(key)` first computes `key.hashCode()` to find the bucket, then walks that bucket calling `equals()` against each entry to find the actual match. If a key's `hashCode()` doesn't match what was used when it was originally inserted (because two "equal" objects hashed differently), `get` looks in the *wrong bucket entirely* and never even reaches the `equals()` check — the lookup fails even though a logically identical key was inserted.

**How to implement both correctly.** Use the same set of fields in both methods — every field `equals()` compares should also feed into `hashCode()`. Java 7+ makes this easy with `Objects.hash(field1, field2, ...)` for `hashCode()`, and `Objects.equals(a, b)` (null-safe) inside `equals()`. In modern Java, a `record` generates both correctly and automatically from its components.

**Mutable keys are dangerous.** If a key's fields (the ones used in `hashCode()`) change after it is inserted into a `HashMap`, its hash code changes too — but the map still stores it in the *old* bucket. A later lookup with an equal key now computes the *new* hash, looks in the wrong bucket, and fails to find the entry, even though it is still physically present in the map. Prefer immutable keys.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two Point objects with equal x and y fields, one overriding only equals and getting a different hashCode landing in a different bucket, the other overriding both correctly and landing in the same bucket">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#f0883e">BROKEN: equals() overridden, hashCode() NOT -- two equal Points, different buckets</text>
    <rect x="20" y="30" width="100" height="26" fill="#0d1117" stroke="#f0883e"/><text x="70" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">Point(1,2) #A</text>
    <text x="70" y="70" fill="#8b949e" text-anchor="middle" font-size="8">identity hashCode -&gt; bucket 3</text>
    <rect x="220" y="30" width="100" height="26" fill="#0d1117" stroke="#f0883e"/><text x="270" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">Point(1,2) #B</text>
    <text x="270" y="70" fill="#8b949e" text-anchor="middle" font-size="8">identity hashCode -&gt; bucket 9</text>
    <text x="170" y="95" fill="#f0883e" text-anchor="middle" font-size="9">map.get(#B) never finds #A -- wrong bucket, equals() never even checked</text>

    <text x="20" y="130" fill="#79c0ff">FIXED: both overridden consistently -- same fields -&gt; same bucket</text>
    <rect x="20" y="145" width="100" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="70" y="162" fill="#e6edf3" text-anchor="middle" font-size="8">Point(1,2) #A</text>
    <rect x="220" y="145" width="100" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="270" y="162" fill="#e6edf3" text-anchor="middle" font-size="8">Point(1,2) #B</text>
    <text x="170" y="185" fill="#79c0ff" text-anchor="middle" font-size="9">both hash to bucket 5 -&gt; equals() check succeeds -&gt; found</text>
  </g>
</svg>

Overriding `equals()` without `hashCode()` puts logically identical objects in different buckets, so lookups fail even when a matching key exists.

## 5. Runnable example

```java
// HashCodeEqualsForKeys.java
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

public class HashCodeEqualsForKeys {

    // BROKEN: overrides equals() but NOT hashCode() -- inherits Object's identity-based hash.
    static class BrokenPoint {
        int x, y;
        BrokenPoint(int x, int y) { this.x = x; this.y = y; }
        @Override public boolean equals(Object o) {
            return o instanceof BrokenPoint p && p.x == x && p.y == y;
        }
        // hashCode() NOT overridden -- violates the contract
    }

    static void basicLevel() {
        Map<BrokenPoint, String> map = new HashMap<>();
        map.put(new BrokenPoint(1, 2), "origin-ish");
        String result = map.get(new BrokenPoint(1, 2)); // a DIFFERENT, but equals()-equal, instance
        System.out.println("basic: BrokenPoint lookup with an equal-but-different instance -> " + result + " (expected non-null, got wrong result)");
    }

    // FIXED: overrides both, consistently, using the same fields.
    static class FixedPoint {
        int x, y;
        FixedPoint(int x, int y) { this.x = x; this.y = y; }
        @Override public boolean equals(Object o) {
            return o instanceof FixedPoint p && p.x == x && p.y == y;
        }
        @Override public int hashCode() { return Objects.hash(x, y); } // same fields as equals()
    }

    static void intermediateLevel() {
        Map<FixedPoint, String> map = new HashMap<>();
        map.put(new FixedPoint(1, 2), "origin-ish");
        String result = map.get(new FixedPoint(1, 2)); // a different instance, same field values
        System.out.println("intermediate: FixedPoint lookup with an equal-but-different instance -> " + result);

        Set<FixedPoint> set = new HashSet<>();
        set.add(new FixedPoint(3, 4));
        set.add(new FixedPoint(3, 4)); // logically a duplicate
        System.out.println("intermediate: HashSet correctly treats these as one entry, size -> " + set.size());
    }

    // Advanced: a record gets both correctly for free, AND the danger of a mutable key.
    record RecordPoint(int x, int y) {} // equals()/hashCode() auto-generated from components, correctly paired

    static void advancedLevel() {
        Map<RecordPoint, String> recordMap = new HashMap<>();
        recordMap.put(new RecordPoint(5, 6), "auto-correct");
        System.out.println("advanced: record key lookup -> " + recordMap.get(new RecordPoint(5, 6)));

        // mutable key danger: FixedPoint's fields are mutable, so changing them after insertion breaks lookup.
        Map<FixedPoint, String> mutableKeyMap = new HashMap<>();
        FixedPoint key = new FixedPoint(7, 8);
        mutableKeyMap.put(key, "before mutation"); // stored in the bucket for hashCode of (7, 8)
        key.x = 999; // mutates the key AFTER insertion -- its hashCode() now differs from what was used at insert time
        System.out.println("advanced: lookup with the SAME reference after mutation -> " + mutableKeyMap.get(key)
            + " (fails -- get() recomputes the hash from the CURRENT, mutated fields, landing in the wrong bucket)");
        System.out.println("advanced: the entry is still in the map, unreachable -> size is still " + mutableKeyMap.size());
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `HashCodeEqualsForKeys.java`, then run `java HashCodeEqualsForKeys.java`.

## 6. Walkthrough

1. `basicLevel()` inserts a `BrokenPoint(1, 2)`, then looks it up with a *different* `BrokenPoint(1, 2)` instance. Since `hashCode()` was never overridden, both instances get different identity-based hash codes, so the lookup checks the wrong bucket entirely and returns `null` — even though `equals()` would have correctly said the two points are equal, had the map ever compared them.
2. `intermediateLevel()`'s `FixedPoint` overrides both methods using the same fields (`x`, `y`). The lookup with a different-but-equal instance now succeeds, since both instances hash identically and land in the same bucket, where `equals()` correctly matches them. The `HashSet` example confirms two field-identical `FixedPoint`s are treated as one logical entry.
3. `advancedLevel()` shows a `record` getting this right automatically — `RecordPoint`'s auto-generated `equals()`/`hashCode()` are always consistent by construction, since both derive from the exact same component list. It then demonstrates the mutable-key danger: `key` is inserted while `x = 7`, landing in the bucket for `hashCode(7, 8)`. Mutating `key.x` to `999` does not move the entry — the map has no way to know a field changed. Even looking it up with that *exact same object reference* fails, because `get()` always recomputes the hash fresh from the object's current fields (`999, 8`), and searches the bucket for that hash, not the bucket the entry actually lives in. The entry is still physically present in the map (`size()` is unchanged), just permanently unreachable through normal lookup.

## 7. Gotchas & takeaways

> Gotcha: never use a mutable field in `hashCode()` for an object that will be used as a `HashMap` key or `HashSet` element while it might change — if you must, remove the object from the collection before mutating it, and re-add it afterward, so it gets rehashed into its correct new bucket.

- The contract is one-directional: `equals()` true implies same `hashCode()`; same `hashCode()` does not imply `equals()` true (that is just a normal collision).
- Override both together, using the exact same set of fields, or use a `record` to get both generated correctly.
- Never mutate a field that `hashCode()` depends on while the object is stored as a key or set element — the entry becomes unfindable by an equal instance.
- Related concepts: [equals/hashCode contract](0014-equals-hashcode-contract.md), [Hash functions & desirable properties](0085-hash-functions-desirable-properties.md).
