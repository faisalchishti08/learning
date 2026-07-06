---
card: java
gi: 294
slug: hashtable
title: Hashtable
---

## 1. What it is

`Hashtable` is a legacy, synchronized implementation of a key-value map, present since Java 1.0 — before `Map`, `HashMap`, and the Collections Framework existed. Like `Vector`, it was retrofitted to implement `Map` when the Collections Framework arrived, but every one of its methods remains `synchronized`, and unlike `HashMap`, it **rejects `null`** for both keys and values.

```java
import java.util.Hashtable;

public class HashtableDemo {
    public static void main(String[] args) {
        Hashtable<String, Integer> ages = new Hashtable<>();
        ages.put("Alice", 30);
        ages.put("Bob", 25);

        System.out.println(ages.get("Alice"));
        System.out.println(ages.containsKey("Bob"));
        // ages.put(null, 1); // would throw NullPointerException
    }
}
```

`put`/`get`/`containsKey` behave like their `HashMap` counterparts, but every call is synchronized, and attempting `ages.put(null, 1)` or `ages.put("x", null)` throws `NullPointerException` immediately — a deliberate design choice `HashMap` later relaxed.

## 2. Why & when

`Hashtable` was Java's original hash-based map, written under the same early assumptions as `Vector`: that thread safety should be baked into the collection itself via per-method synchronization, and that `null` values were error-prone enough to forbid outright.

- **Historical thread safety** — every method synchronized, so a `Hashtable` could historically be shared across threads without external locking (though, as with `Vector`, this doesn't make multi-call sequences atomic).
- **Strict null rejection** — throwing immediately on a `null` key or value catches certain bugs early (a `null` silently stored can be ambiguous — does it mean "no value" or "the value is null?").
- **Legacy API surfaces** — some very old code and a few standard-library corners still expose `Hashtable` in their signatures.

For new code, prefer `HashMap` (unsynchronized, faster, and permits one `null` key plus `null` values) for single-threaded use, or `ConcurrentHashMap` for genuine concurrent access — `ConcurrentHashMap` is dramatically more scalable than `Hashtable` because it doesn't lock the entire table for every operation, only the relevant segment.

## 3. Core concept

```java
import java.util.Hashtable;
import java.util.Enumeration;

public class HashtableCore {
    public static void main(String[] args) {
        Hashtable<String, Integer> scores = new Hashtable<>();
        scores.put("A", 90);
        scores.put("B", 85);

        Enumeration<String> keys = scores.keys(); // legacy iteration mechanism
        while (keys.hasMoreElements()) {
            String key = keys.nextElement();
            System.out.println(key + " = " + scores.get(key));
        }
    }
}
```

`keys()` returns an `Enumeration` — `Hashtable`'s original, pre-`Iterator` way of walking its entries — which still works today alongside the modern `entrySet()`/`keySet()` methods `Hashtable` also supports via `Map`.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Hashtable synchronizes the whole table for every call, ConcurrentHashMap only locks the relevant segment, allowing far more parallelism">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="250" height="90" rx="6" fill="#1c2430" stroke="#f85149"/>
  <text x="155" y="52" fill="#f85149" font-size="12" text-anchor="middle" font-family="monospace">Hashtable</text>
  <text x="155" y="72" fill="#8b949e" font-size="9" text-anchor="middle">whole-table lock per call</text>
  <text x="155" y="90" fill="#8b949e" font-size="9" text-anchor="middle">rejects null keys/values</text>

  <rect x="320" y="30" width="250" height="90" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="445" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">ConcurrentHashMap</text>
  <text x="445" y="72" fill="#8b949e" font-size="9" text-anchor="middle">fine-grained locking</text>
  <text x="445" y="90" fill="#8b949e" font-size="9" text-anchor="middle">far better concurrent throughput</text>
</svg>

Both are thread-safe maps; `ConcurrentHashMap` gets there with much less contention under load.

## 5. Runnable example

Scenario: a shared word-frequency counter, evolved from a single-threaded `Hashtable` tally into a multi-threaded counter that exposes the classic check-then-act race and fixes it with `computeIfAbsent`-style atomic updates.

### Level 1 — Basic

```java
import java.util.Hashtable;

public class HashtableBasic {
    public static void main(String[] args) {
        String[] words = {"the", "quick", "the", "fox", "the", "quick"};
        Hashtable<String, Integer> counts = new Hashtable<>();

        for (String word : words) {
            Integer current = counts.get(word);
            counts.put(word, (current == null ? 0 : current) + 1);
        }

        System.out.println(counts);
    }
}
```

**How to run:** `java HashtableBasic.java`

Single-threaded frequency counting — `get` then `put` is a manual check-then-act update, fine here because nothing else touches `counts` concurrently.

### Level 2 — Intermediate

Same word-counting idea, now with multiple threads each processing part of the word list and updating a shared `Hashtable`, revealing the race condition in the naive get-then-put pattern.

```java
import java.util.Hashtable;

public class HashtableIntermediate {
    public static void main(String[] args) throws InterruptedException {
        Hashtable<String, Integer> counts = new Hashtable<>();
        Runnable countTheWord = () -> {
            for (int i = 0; i < 10_000; i++) {
                Integer current = counts.get("the"); // read
                counts.put("the", (current == null ? 0 : current) + 1); // write
            }
        };

        Thread t1 = new Thread(countTheWord);
        Thread t2 = new Thread(countTheWord);
        t1.start();
        t2.start();
        t1.join();
        t2.join();

        System.out.println("Count for 'the': " + counts.get("the")); // often LESS than 20000!
    }
}
```

**How to run:** `java HashtableIntermediate.java`

Even though `get` and `put` are each individually synchronized, the *sequence* — read the current value, compute `+1`, write it back — is not atomic; two threads can both read the same current value before either writes back the increment, silently losing updates, so the final count is frequently less than the expected `20000`.

### Level 3 — Advanced

Same counter, now fixed using `merge`, which performs the read-compute-write as a single atomic operation under the hood, eliminating the lost-update race entirely.

```java
import java.util.Hashtable;

public class HashtableAdvanced {
    public static void main(String[] args) throws InterruptedException {
        Hashtable<String, Integer> counts = new Hashtable<>();
        Runnable countTheWord = () -> {
            for (int i = 0; i < 10_000; i++) {
                counts.merge("the", 1, Integer::sum); // atomic read-compute-write
            }
        };

        Thread t1 = new Thread(countTheWord);
        Thread t2 = new Thread(countTheWord);
        t1.start();
        t2.start();
        t1.join();
        t2.join();

        System.out.println("Count for 'the': " + counts.get("the")); // reliably exactly 20000
    }
}
```

**How to run:** `java HashtableAdvanced.java`

`merge("the", 1, Integer::sum)` atomically does the equivalent of "if absent, set to 1; if present, add 1 to the existing value" as one indivisible operation on the map — no other thread can interleave a read and write in the middle of it, so running this with two threads each incrementing 10,000 times reliably produces exactly `20000` every time, unlike the Level 2 version.

## 6. Walkthrough

Trace why Level 2 can lose updates and why Level 3 cannot, step by step.

**Level 2, a lost-update scenario.** Suppose the counter currently holds `100` for `"the"`. Thread 1 calls `counts.get("the")`, reading `100` into its local `current` variable. Before Thread 1 calls `put`, Thread 2 also calls `counts.get("the")`, *also* reading `100` (the write from Thread 1 hasn't happened yet). Both threads now independently compute `100 + 1 = 101` and both call `counts.put("the", 101)`. The map ends up at `101`, even though two increments occurred — one increment's effect was silently overwritten. This can repeat many times across 20,000 total increments, so the final count ends up noticeably below `20000`.

**Level 3, the same scenario with `merge`.** `merge("the", 1, Integer::sum)` is implemented so that the read of the current value and the write of the new value happen as one atomic unit with respect to other calls on the same key — no other thread's `merge` call can be "in between" the read and the write of another. So if the counter holds `100` and two threads call `merge` at nearly the same time, the map's internal locking (or, in `ConcurrentHashMap`'s case, its per-bucket locking) ensures they are effectively serialized for that key: one sees `100` and writes `101`; the other then sees `101` and writes `102`. No increment is ever lost.

**Why `get`-then-`put` fails but `merge` doesn't**, even though `Hashtable` synchronizes every method: `get` and `put` are two *separate* method calls, each individually atomic, but nothing prevents another thread's `get` from slipping in between this thread's `get` and its subsequent `put`. `merge`, by contrast, is **one single method call** that performs the entire read-compute-write internally, so there is no gap for another thread to interleave into.

```
Level 2 (get then put) -- gap between read and write:
  T1: get -> 100        T2: get -> 100         (both read the SAME stale value)
  T1: put(101)           T2: put(101)           (one increment is lost)

Level 3 (merge) -- no gap, entire operation is one atomic call:
  T1: merge -> reads 100, writes 101, done
  T2: merge -> reads 101, writes 102, done      (nothing lost)
```

**Output (Level 3):**
```
Count for 'the': 20000
```

## 7. Gotchas & takeaways

> `Hashtable` throws `NullPointerException` immediately on `put(null, ...)` or `put(..., null)` — a difference from `HashMap`, which permits one `null` key and any number of `null` values. Code migrated from `HashMap` to `Hashtable` (or vice versa) can break if it relied on storing `null`.

> Per-method synchronization (on both `Hashtable` and `Vector`) does not make multi-call sequences atomic. The classic "read the value, compute a new one, write it back" pattern is a race condition waiting to happen unless you use an atomic compound method (`merge`, `computeIfAbsent`, `putIfAbsent`) or your own explicit lock around the whole sequence.

- `Hashtable` is a legacy, synchronized `Map` implementation that rejects `null` keys and values.
- Prefer `HashMap` for single-threaded use and `ConcurrentHashMap` for concurrent use — both offer better performance and, for `ConcurrentHashMap`, far better scalability under contention.
- Individually-synchronized methods do not make read-then-write sequences atomic; use `merge`/`computeIfAbsent`/`putIfAbsent` for atomic compound updates.
- `Hashtable` predates `Iterator` and still supports its original `Enumeration`-based iteration via `keys()`/`elements()`, alongside the modern `Map` methods.
