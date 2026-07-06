---
card: java
gi: 291
slug: java-util-bitset
title: java.util.BitSet
---

## 1. What it is

`java.util.BitSet` is a growable vector of bits, where each bit is either `true` (set) or `false` (clear). It behaves like an array of booleans but is stored far more compactly (packed as bits rather than one byte-or-more per element) and offers fast bulk operations: AND, OR, XOR, and NOT across entire sets of bits at once.

```java
import java.util.BitSet;

public class BitSetDemo {
    public static void main(String[] args) {
        BitSet bits = new BitSet();
        bits.set(2);
        bits.set(5);
        bits.set(7);

        System.out.println(bits);              // {2, 5, 7}
        System.out.println(bits.get(5));        // true
        System.out.println(bits.cardinality()); // 3 (number of set bits)
    }
}
```

`set(index)` turns a bit on, `get(index)` reads it, and `cardinality()` counts how many bits are currently `true` — `BitSet` grows automatically as higher indices are set.

## 2. Why & when

`BitSet` exists for problems that are naturally expressed as "which of these N things are true," especially when N is large and most operations are bulk set operations rather than one-at-a-time lookups.

- **Compact flag storage** — tracking membership or state across thousands or millions of indices (e.g. "which of these 1,000,000 user IDs have logged in today") uses far less memory than a `boolean[]` or a `HashSet<Integer>`.
- **Fast set algebra** — `and`, `or`, `xor`, `andNot` operate on whole words of bits at a time internally, making set intersection/union/difference over large ranges much faster than looping element by element.
- **Classic algorithms** — sieve-of-Eratosthenes-style prime sieves, bitmap indexes, and visited-node tracking in graph algorithms are natural fits.

Use `BitSet` when you need to represent a large, dense range of true/false flags and want to perform bulk boolean operations across them; use a `HashSet<Integer>` instead if the "true" indices are sparse relative to the range (a `HashSet` only pays for what's actually in it, whereas `BitSet`'s cost scales with the highest index set, not the count of true bits).

## 3. Core concept

```java
import java.util.BitSet;

public class BitSetCore {
    public static void main(String[] args) {
        BitSet evens = new BitSet();
        BitSet primes = new BitSet();
        for (int i = 0; i <= 10; i += 2) evens.set(i);
        for (int i : new int[]{2, 3, 5, 7}) primes.set(i);

        BitSet evenPrimes = (BitSet) evens.clone();
        evenPrimes.and(primes); // keep only bits set in BOTH

        System.out.println("Evens: " + evens);
        System.out.println("Primes: " + primes);
        System.out.println("Even primes: " + evenPrimes);
    }
}
```

`and` performs a bitwise intersection in place, so `evenPrimes` ends up containing only the indices that were set in both `evens` and `primes` — here, just `{2}`, since 2 is the only even prime — which is exactly why `clone()` is used first, to avoid destroying the original `evens` set.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two bit sets are combined with AND to produce a bit set containing only the positions set in both">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="10" font-family="sans-serif">index:  0 1 2 3 4 5 6 7 8 9 10</text>
  <text x="20" y="55" fill="#e6edf3" font-size="10" font-family="monospace">evens:  1 0 1 0 1 0 1 0 1 0 1</text>
  <text x="20" y="80" fill="#e6edf3" font-size="10" font-family="monospace">primes: 0 0 1 1 0 1 0 1 0 0 0</text>
  <line x1="20" y1="90" x2="300" y2="90" stroke="#8b949e" stroke-width="1"/>
  <text x="20" y="108" fill="#6db33f" font-size="10" font-family="monospace">AND:    0 0 1 0 0 0 0 0 0 0 0</text>
  <text x="300" y="108" fill="#79c0ff" font-size="11" font-family="sans-serif">-&gt; only index 2 is set in both</text>
</svg>

`and` keeps a bit set only where both operands had it set; every other position becomes (or stays) clear.

## 5. Runnable example

Scenario: a prime-number sieve, evolved from a basic Sieve of Eratosthenes into one that reports statistics and then combines results with another `BitSet` using set algebra.

### Level 1 — Basic

```java
import java.util.BitSet;

public class BitSetBasic {
    public static void main(String[] args) {
        int limit = 30;
        BitSet composite = new BitSet(limit + 1);

        for (int i = 2; i * i <= limit; i++) {
            if (!composite.get(i)) {
                for (int multiple = i * i; multiple <= limit; multiple += i) {
                    composite.set(multiple);
                }
            }
        }

        System.out.print("Primes up to " + limit + ": ");
        for (int i = 2; i <= limit; i++) {
            if (!composite.get(i)) System.out.print(i + " ");
        }
        System.out.println();
    }
}
```

**How to run:** `java BitSetBasic.java`

A classic Sieve of Eratosthenes: `composite` marks every number known to be non-prime; any index never marked by the time the loop finishes is prime.

### Level 2 — Intermediate

Same sieve, now reporting how many primes were found and the memory-relevant `cardinality()` at each stage.

```java
import java.util.BitSet;

public class BitSetIntermediate {
    public static void main(String[] args) {
        int limit = 100;
        BitSet composite = new BitSet(limit + 1);

        for (int i = 2; i * i <= limit; i++) {
            if (!composite.get(i)) {
                for (int multiple = i * i; multiple <= limit; multiple += i) {
                    composite.set(multiple);
                }
            }
        }

        int primeCount = (limit - 1) - composite.cardinality(); // exclude 0,1 from range size
        System.out.println("Composite numbers marked: " + composite.cardinality());
        System.out.println("Primes found up to " + limit + ": " + primeCount);
    }
}
```

**How to run:** `java BitSetIntermediate.java`

`composite.cardinality()` counts how many numbers in `[0, limit]` got marked as composite; subtracting that from the size of the range (excluding 0 and 1, which are neither prime nor counted as composite here) gives the prime count without a second scanning loop.

### Level 3 — Advanced

Same sieve, now computing primes up to two different limits and finding the primes common to both ranges (trivially all of the smaller range) versus primes exclusive to the larger range, using `BitSet` set algebra instead of manual comparison loops.

```java
import java.util.BitSet;

public class BitSetAdvanced {
    static BitSet sieve(int limit) {
        BitSet composite = new BitSet(limit + 1);
        for (int i = 2; i * i <= limit; i++) {
            if (!composite.get(i)) {
                for (int multiple = i * i; multiple <= limit; multiple += i) {
                    composite.set(multiple);
                }
            }
        }
        BitSet primes = new BitSet(limit + 1);
        for (int i = 2; i <= limit; i++) {
            if (!composite.get(i)) primes.set(i);
        }
        return primes;
    }

    public static void main(String[] args) {
        BitSet primesTo50 = sieve(50);
        BitSet primesTo100 = sieve(100);

        BitSet onlyInLarger = (BitSet) primesTo100.clone();
        onlyInLarger.andNot(primesTo50); // remove everything also present up to 50

        System.out.println("Primes up to 50: " + primesTo50.cardinality());
        System.out.println("Primes up to 100: " + primesTo100.cardinality());
        System.out.println("Primes strictly between 50 and 100: " + onlyInLarger);
    }
}
```

**How to run:** `java BitSetAdvanced.java`

`sieve` now returns a clean `BitSet` of primes rather than of composites, making the result directly usable for set algebra; `andNot` computes "in `primesTo100` but not in `primesTo50`" in one bulk operation, which is exactly the set of primes strictly greater than 50 and at most 100 — no manual index comparison needed.

## 6. Walkthrough

Trace `BitSetAdvanced.main` step by step.

**`sieve(50)`.** Runs the sieve algorithm up to 50: `composite` marks every non-prime in `[0, 50]`, then a second pass builds `primes`, setting bit `i` for every `i` in `[2, 50]` not marked composite — this includes 2, 3, 5, 7, 11, ..., 47. Returned as `primesTo50`.

**`sieve(100)`.** Same process, independently, up to 100 — produces `primesTo100`, a superset containing everything `primesTo50` has plus the additional primes between 51 and 100 (53, 59, 61, ..., 97).

**`onlyInLarger = (BitSet) primesTo100.clone()`.** A full, independent copy of `primesTo100`'s bits — mutating `onlyInLarger` next will not affect `primesTo100`.

**`onlyInLarger.andNot(primesTo50)`.** For every bit set in `onlyInLarger`, this clears it if the corresponding bit is *also* set in `primesTo50`. Since every prime up to 50 is, by construction, also present in `primesTo100` (and therefore in `onlyInLarger` before this call), this operation removes exactly those, leaving only the primes strictly greater than 50.

**Final prints.** `primesTo50.cardinality()` is 15 (the count of primes up to 50). `primesTo100.cardinality()` is 25 (the count of primes up to 100). `onlyInLarger` now prints as the set `{53, 59, 61, 67, 71, 73, 79, 83, 89, 97}` — 10 elements, which is consistent with `25 - 15 = 10`.

```
primesTo50:  {2,3,5,7,11,...,47}              (15 bits set)
primesTo100: {2,3,5,7,11,...,47,53,...,97}    (25 bits set)

onlyInLarger = clone(primesTo100)
onlyInLarger.andNot(primesTo50)  -- clear every bit also in primesTo50
           = {53,59,61,67,71,73,79,83,89,97}  (10 bits set)
```

**Output:**
```
Primes up to 50: 15
Primes up to 100: 25
Primes strictly between 50 and 100: {53, 59, 61, 67, 71, 73, 79, 83, 89, 97}
```

## 7. Gotchas & takeaways

> `and`, `or`, `xor`, and `andNot` all **mutate the `BitSet` they're called on** — they are not pure functions that return a new set. If you need to keep the original untouched (as `onlyInLarger` needed to preserve `primesTo100`), clone it first, exactly as shown above.

> `BitSet`'s memory cost scales with the **highest index ever set**, not with the number of `true` bits. `bitSet.set(1_000_000)` allocates internal storage covering the whole range up to a million, even if that's the only bit ever set — for sparse data, a `HashSet<Integer>` is far cheaper.

- `BitSet` packs boolean flags into bits, giving compact storage and fast bulk boolean operations (`and`, `or`, `xor`, `andNot`) compared to a `boolean[]` or `HashSet<Integer>`.
- `set`, `get`, `clear`, and `cardinality` are the everyday single-bit and counting operations.
- Bulk operations mutate the receiver in place — clone a `BitSet` first if you need to preserve the original.
- Best suited to dense ranges of flags (sieves, visited-node tracking, bitmap indexes); prefer a hash-based set for sparse data over a large range.
