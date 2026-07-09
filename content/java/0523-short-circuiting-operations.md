---
card: java
gi: 523
slug: short-circuiting-operations
title: Short-circuiting operations
---

## 1. What it is

A **short-circuiting operation** is one that can stop processing a stream before examining every element, because it already has enough information to produce its final answer. `limit(n)` is a short-circuiting *intermediate* operation (it stops once `n` elements have passed through). `findFirst()`, `findAny()`, `anyMatch()`, `allMatch()`, and `noneMatch()` are short-circuiting *terminal* operations — each can, in principle, stop scanning as soon as the outcome is determined, rather than always visiting every remaining element.

## 2. Why & when

Combined with lazy evaluation (see [[lazy-evaluation]]), short-circuiting is what makes certain stream computations dramatically cheaper than a naive full scan — and, critically, what makes infinite streams (`Stream.iterate`, `Stream.generate`) practically usable at all. Recognizing which operations are short-circuiting matters for two reasons: performance (searching a huge dataset for "does any element match?" can stop at the first hit instead of scanning everything), and correctness (relying on a non-short-circuiting side effect, like `peek`, to run for *every* element is unsafe once a short-circuiting operation is anywhere in the pipeline).

## 3. Core concept

```java
import java.util.stream.*;

// Short-circuiting: stops as soon as ANY match is found
boolean hasNegative = Stream.of(5, 3, -1, 8, 2).anyMatch(n -> n < 0); // stops at -1, never sees 8, 2

// Short-circuiting: stops once 3 elements are taken, regardless of source size
Stream.iterate(1, n -> n + 1).limit(3).forEach(System.out::println); // 1 2 3, source never asked for more

// NOT short-circuiting: every element must be visited to guarantee the total is complete
long total = Stream.of(1, 2, 3, 4).count(); // must account for all elements (though count() has its own optimizations)
```

Short-circuiting operations can produce a correct final answer without visiting every element; non-short-circuiting operations (like `map`, `sorted`, `collect`, `reduce` without a matching condition) fundamentally need to see everything.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a short-circuiting operation stops scanning once its answer is determined, skipping remaining elements">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="52" y="50" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">5</text>
  <rect x="85" y="30" width="45" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="107" y="50" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">3</text>
  <rect x="140" y="30" width="45" height="30" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/><text x="162" y="50" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">-1</text>
  <rect x="195" y="30" width="45" height="30" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="217" y="50" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">8</text>
  <rect x="250" y="30" width="45" height="30" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="272" y="50" fill="#8b949e" font-size="12" text-anchor="middle" font-family="monospace">2</text>
  <text x="160" y="90" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">anyMatch(n &lt; 0) finds -1 and stops -- 8 and 2 are never examined.</text>
</svg>

`-1` satisfies the predicate; `anyMatch` returns `true` immediately, and the elements after it are never visited at all.

## 5. Runnable example

Scenario: searching a stream of transaction records for suspicious activity — evolved from a plain short-circuiting search, through measuring how many elements are actually visited to prove the short-circuit, to a version comparing short-circuiting against a non-short-circuiting alternative on the same data.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class ShortCircuitBasic {
    record Transaction(String id, double amount) {}

    public static void main(String[] args) {
        List<Transaction> transactions = List.of(
                new Transaction("T1", 50.0),
                new Transaction("T2", 75.0),
                new Transaction("T3", 15000.0), // suspicious -- large amount
                new Transaction("T4", 120.0)
        );

        boolean hasSuspicious = transactions.stream()
                .anyMatch(t -> t.amount() > 10000);

        System.out.println("Has suspicious transaction: " + hasSuspicious);
    }
}
```

**How to run:** `java ShortCircuitBasic.java`

Expected output:
```
Has suspicious transaction: true
```

`.anyMatch(t -> t.amount() > 10000)` scans the transactions in order and stops the moment it finds `T3` ($15,000), which satisfies the condition — it doesn't need to check `T4` at all to know the overall answer is `true`.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;

public class ShortCircuitMeasured {
    record Transaction(String id, double amount) {}

    public static void main(String[] args) {
        List<Transaction> transactions = List.of(
                new Transaction("T1", 50.0),
                new Transaction("T2", 75.0),
                new Transaction("T3", 15000.0),
                new Transaction("T4", 120.0),
                new Transaction("T5", 90.0)
        );

        AtomicInteger examined = new AtomicInteger(0);

        boolean hasSuspicious = transactions.stream()
                .peek(t -> examined.incrementAndGet())
                .anyMatch(t -> t.amount() > 10000);

        System.out.println("Has suspicious: " + hasSuspicious);
        System.out.println("Transactions examined: " + examined.get() + " out of " + transactions.size());
    }
}
```

**How to run:** `java ShortCircuitMeasured.java`

Expected output:
```
Has suspicious: true
Transactions examined: 3 out of 5
```

The real-world concern this adds: proving the short-circuit actually happens, using a `peek`-based counter (see [[peek]]). Out of five transactions, only `3` are examined (`T1`, `T2`, `T3`) before `anyMatch` finds its answer at `T3` and stops — `T4` and `T5` are never even looked at, which matters for performance if checking each transaction were an expensive operation (a database call, an external fraud-check API).

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.*;

public class ShortCircuitVsFull {
    record Transaction(String id, double amount) {}

    public static void main(String[] args) {
        List<Transaction> transactions = List.of(
                new Transaction("T1", 50.0),
                new Transaction("T2", 75.0),
                new Transaction("T3", 15000.0),
                new Transaction("T4", 120.0),
                new Transaction("T5", 90.0)
        );

        // Short-circuiting: anyMatch stops at the first hit.
        AtomicInteger shortCircuitExamined = new AtomicInteger(0);
        boolean anyFound = transactions.stream()
                .peek(t -> shortCircuitExamined.incrementAndGet())
                .anyMatch(t -> t.amount() > 10000);

        // NOT short-circuiting: filter + count must examine every element, since it needs the TOTAL count.
        AtomicInteger fullScanExamined = new AtomicInteger(0);
        long suspiciousCount = transactions.stream()
                .peek(t -> fullScanExamined.incrementAndGet())
                .filter(t -> t.amount() > 10000)
                .count();

        System.out.println("anyMatch examined: " + shortCircuitExamined.get() + " (found=" + anyFound + ")");
        System.out.println("filter+count examined: " + fullScanExamined.get() + " (count=" + suspiciousCount + ")");
    }
}
```

**How to run:** `java ShortCircuitVsFull.java`

Expected output:
```
anyMatch examined: 3 (found=true)
filter+count examined: 5 (count=1)
```

This directly contrasts the two behaviors on identical data: `.anyMatch(...)` only needs to know "does at least one exist?" so it stops at the first match, examining `3` of `5` transactions. `.filter(...).count()`, by contrast, needs to know the *total* number of matches, which fundamentally requires examining every single element — it cannot short-circuit, since a later element could always be another match that needs counting, examining all `5` transactions even though the actual matching count (`1`) is smaller than the number examined.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Five transactions are defined, with only `T3` ($15,000) exceeding the $10,000 threshold.

For the first computation, `transactions.stream().peek(t -> shortCircuitExamined.incrementAndGet()).anyMatch(t -> t.amount() > 10000)` begins pulling elements one at a time, since `anyMatch` is short-circuiting. It pulls `T1`: `peek` increments `shortCircuitExamined` to `1`; `anyMatch`'s predicate checks `50.0 > 10000`, `false` — not yet found, continue. It pulls `T2`: counter becomes `2`; `75.0 > 10000` is `false` — continue. It pulls `T3`: counter becomes `3`; `15000.0 > 10000` is `true` — a match is found, `anyMatch` can now return `true` immediately, and the pipeline stops. `T4` and `T5` are never pulled at all.

For the second computation, `transactions.stream().peek(t -> fullScanExamined.incrementAndGet()).filter(t -> t.amount() > 10000).count()` also processes elements one at a time, but `.count()` is **not** short-circuiting: even after `T3` is found to match at the third element, the pipeline must continue to `T4` and `T5` to confirm they either do or don't also match, since the final count needs to be accurate. All five elements are pulled: `T1` (counter `1`, filtered out), `T2` (counter `2`, filtered out), `T3` (counter `3`, matches, kept), `T4` (counter `4`, filtered out), `T5` (counter `5`, filtered out).

```
anyMatch path:        T1(1,no) -> T2(2,no) -> T3(3,YES) -> STOP (T4, T5 never pulled)
filter+count path:    T1(1,no) -> T2(2,no) -> T3(3,match) -> T4(4,no) -> T5(5,no) -> count=1
```

`shortCircuitExamined.get()` is `3`, `anyFound` is `true`, printed as `"anyMatch examined: 3 (found=true)"`. `fullScanExamined.get()` is `5`, `suspiciousCount` is `1` (only `T3` matched), printed as `"filter+count examined: 5 (count=1)"` — a direct, measured demonstration that `anyMatch` short-circuits while `filter().count()` fundamentally cannot.

## 7. Gotchas & takeaways

> Whether an operation short-circuits depends on what question it's answering, not on which methods happen to appear in the pipeline. `anyMatch`/`findFirst`/`limit` can stop early because their questions ("does one exist?", "give me one", "give me N") can be answered without full information. `count`, `collect`, `reduce`, and `sorted` generally cannot, because their questions ("how many total?", "give me everything transformed", "combine everything", "give me the full order") inherently require seeing every element (or, for `sorted`, at least buffering everything before producing output).

- Short-circuiting operations can stop processing a stream before visiting every element, because their answer is already determined.
- `limit(n)` is a short-circuiting intermediate operation; `findFirst`, `findAny`, `anyMatch`, `allMatch`, `noneMatch` are short-circuiting terminal operations.
- Short-circuiting combined with laziness is what makes infinite streams practically usable — without it, a terminal operation on an infinite source would never complete.
- `count()`, `collect()`, `reduce()` (without a matching short-circuit condition), and `sorted()` are not short-circuiting — they need to process the whole stream to produce a correct result.
- Relying on a side effect (like `peek`) to run for every single element is unsafe whenever a short-circuiting operation appears anywhere in the same pipeline, since some elements may never be visited at all.
