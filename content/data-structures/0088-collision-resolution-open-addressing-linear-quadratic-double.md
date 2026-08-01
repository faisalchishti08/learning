---
card: data-structures
gi: 88
slug: collision-resolution-open-addressing-linear-quadratic-double
title: 'Collision resolution: open addressing (linear/quadratic/double)'
---

## 1. What it is

**Open addressing** resolves hash collisions differently from chaining: instead of letting a bucket hold multiple entries, every entry gets its own slot, and a colliding key **probes** — checks a sequence of other slots — until it finds an empty one. There is no per-bucket list; the entire table is one flat array, and every key lives directly inside it.

## 2. Why & when

Open addressing avoids chaining's extra memory overhead (no linked-list nodes per bucket) and tends to have better cache locality, since probing stays within one contiguous array instead of following pointers. It is the strategy behind hash tables in many other languages (Python's `dict`, for example), and is the right choice when memory overhead or cache performance matters more than simplicity.

## 3. Core concept

**Linear probing.** On a collision at slot `i`, try `i+1`, `i+2`, `i+3`, ... (wrapping around) until an empty slot is found. Simple, but prone to **clustering**: once several keys land near each other, the cluster tends to grow, since any new key probing into that region has to walk past the whole cluster.

**Quadratic probing.** On a collision at slot `i`, try `i+1²`, `i+2²`, `i+3²`, ... — spreading probes out faster than linear probing, reducing (but not eliminating) clustering.

**Double hashing.** Use a *second* hash function to determine the probe step size itself: try `i`, `i + step`, `i + 2*step`, ... where `step = hash2(key)`. Since the step size varies per key, two keys that collide at the same initial slot are very unlikely to follow the same probe sequence afterward — this gives the best distribution of the three strategies.

**Deletion needs a tombstone.** Simply clearing a slot to "empty" on delete would break future lookups: a later key that originally probed past the deleted slot (because it was occupied at the time) would now stop searching too early, at the newly-emptied slot, and incorrectly report "not found." The fix is a **tombstone** marker — a special "deleted, but keep probing past me" state, distinct from both "empty" and "occupied."

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ten slot array where key B collides with key A at slot 3, then linear probing moves it to slot 4, and quadratic probing would instead try slot 4 then slot 7">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">array of 6 slots; key B hashes to slot 2 (same as key A, already there)</text>
    <rect x="20" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="40" y="47" fill="#8b949e" text-anchor="middle" font-size="8">0</text>
    <rect x="60" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="80" y="47" fill="#8b949e" text-anchor="middle" font-size="8">1</text>
    <rect x="100" y="30" width="40" height="26" fill="#0d1117" stroke="#f0883e"/><text x="120" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">A</text>
    <rect x="140" y="30" width="40" height="26" fill="#0d1117" stroke="#79c0ff"/><text x="160" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">B?</text>
    <rect x="180" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="200" y="47" fill="#8b949e" text-anchor="middle" font-size="8">4</text>
    <rect x="220" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="240" y="47" fill="#8b949e" text-anchor="middle" font-size="8">5</text>
    <text x="160" y="20" fill="#79c0ff" text-anchor="middle" font-size="8">linear probe: slot 2 taken -&gt; try slot 3 -&gt; empty, place B here</text>
    <text x="120" y="90" fill="#8b949e">quadratic would instead try slot 2+1=3, then 2+4=6 if 3 were also taken</text>
    <text x="120" y="115" fill="#8b949e">double hashing tries 2 + k*step(B), a different sequence per key</text>
  </g>
</svg>

Key `B` collides with `A` at slot `2`; each probing strategy defines a different sequence of alternate slots to try until an empty one is found.

## 5. Runnable example

```java
// OpenAddressingHashTable.java
public class OpenAddressingHashTable {
    private static final Object TOMBSTONE = new Object(); // marks a deleted slot: keep probing past it
    private Object[] keys;
    private Object[] values;
    private int capacity;

    OpenAddressingHashTable(int capacity) {
        this.capacity = capacity;
        keys = new Object[capacity];
        values = new Object[capacity];
    }

    private int hash(Object key) { return Math.floorMod(key.hashCode(), capacity); }

    // Basic: linear probing for insert and lookup.
    void putLinear(Object key, Object value) {
        int i = hash(key);
        while (keys[i] != null && keys[i] != TOMBSTONE && !keys[i].equals(key)) {
            i = (i + 1) % capacity; // linear probe: next slot
        }
        keys[i] = key;
        values[i] = value;
    }

    Object getLinear(Object key) {
        int i = hash(key);
        int startedAt = i;
        while (keys[i] != null) {
            if (keys[i] != TOMBSTONE && keys[i].equals(key)) return values[i];
            i = (i + 1) % capacity;
            if (i == startedAt) break; // full loop, avoid infinite spin on a full table
        }
        return null;
    }

    static void basicLevel() {
        OpenAddressingHashTable table = new OpenAddressingHashTable(8);
        table.putLinear("apple", 1);
        table.putLinear("banana", 2);
        System.out.println("basic: get(\"apple\") -> " + table.getLinear("apple"));
        System.out.println("basic: get(\"banana\") -> " + table.getLinear("banana"));
    }

    // Intermediate: force a collision with a tiny capacity, watch linear probing find the next open slot.
    static void intermediateLevel() {
        OpenAddressingHashTable table = new OpenAddressingHashTable(4);
        table.putLinear("a", 1); // hashes into some slot
        table.putLinear("b", 2); // may collide, probes forward if so
        table.putLinear("c", 3); // same
        System.out.println("intermediate: all three inserted despite a small table -> "
            + table.getLinear("a") + ", " + table.getLinear("b") + ", " + table.getLinear("c"));
    }

    // Advanced: deletion with a tombstone -- confirm a later key's lookup still succeeds past a deleted slot.
    void delete(Object key) {
        int i = hash(key);
        int startedAt = i;
        while (keys[i] != null) {
            if (keys[i] != TOMBSTONE && keys[i].equals(key)) { keys[i] = TOMBSTONE; values[i] = null; return; }
            i = (i + 1) % capacity;
            if (i == startedAt) return;
        }
    }

    static void advancedLevel() {
        OpenAddressingHashTable table = new OpenAddressingHashTable(4);
        table.putLinear("x", 1);
        table.putLinear("y", 2); // suppose this collides with "x" and probes to the next slot
        table.delete("x");        // delete the FIRST key, leaving a tombstone where it was
        System.out.println("advanced: get(\"y\") after deleting \"x\" (which may be earlier in the probe sequence) -> "
            + table.getLinear("y"));
        System.out.println("advanced: without a tombstone, this lookup could incorrectly stop early and return null");
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `OpenAddressingHashTable.java`, then run `java OpenAddressingHashTable.java`.

## 6. Walkthrough

1. `basicLevel()` inserts two keys that likely land in different slots at capacity `8`; `getLinear` recomputes each key's starting slot and finds it directly, or after a short probe if a collision happened.
2. `intermediateLevel()` uses a small capacity-`4` table, making collisions likely. Whichever keys collide, `putLinear`'s `while` loop advances one slot at a time until it finds an empty (or matching) slot — every key still ends up findable afterward, just possibly not at its "natural" hashed slot.
3. `advancedLevel()` demonstrates why deletion needs a tombstone: if `"y"` originally probed past `"x"`'s slot because it was occupied, then deleting `"x"` and leaving that slot truly `null` (not a tombstone) would make `getLinear("y")`'s probe sequence stop at that now-empty slot, believing the search has run off the end of `"y"`'s cluster — incorrectly returning `null` even though `"y"` is still in the table, just further along. The tombstone (`keys[i] = TOMBSTONE`) keeps the probe sequence walking past deleted slots, so `"y"` is still found correctly.

## 7. Gotchas & takeaways

> Gotcha: forgetting the "full loop" guard (`if (i == startedAt) break`) in a lookup or insert loop causes an infinite loop if the table is completely full of non-matching, non-tombstone entries — open addressing requires the table to never actually reach 100% full in practice, which is why implementations resize well before that point.

- Open addressing stores every entry directly in the array, resolving collisions by probing to another slot instead of chaining.
- Linear probing is simple but clusters; quadratic probing spreads probes faster; double hashing (a second hash function sets the step) gives the best distribution.
- Deletion needs a tombstone marker, not a plain "empty," or later lookups that probed past the deleted slot will incorrectly stop early.
- Related concepts: [Collision resolution: separate chaining](0087-collision-resolution-separate-chaining.md), [Load factor & rehashing](0086-load-factor-rehashing.md).
