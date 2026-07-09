---
card: java
gi: 525
slug: ordered-vs-unordered-streams
title: Ordered vs unordered streams
---

## 1. What it is

An **ordered** stream has a defined *encounter order* — the sequence in which elements would be processed matches a meaningful order from the source, such as a `List`'s index order or a sorted `TreeSet`'s natural order. An **unordered** stream has no such guarantee — sources like `HashSet` or `HashMap` have no defined iteration order to preserve, so streams built from them are unordered from the start. Calling `.unordered()` on any stream explicitly tells the stream machinery that encounter order doesn't matter for this pipeline, even if the source was originally ordered.

## 2. Why & when

Encounter order affects which operations produce deterministic results and how efficiently a stream can run in parallel. Operations like `findFirst()`, `limit()`, `skip()`, and `sorted()` (with no comparator, relying on natural order) rely on encounter order to know what "first" or "the next N" even means — on an ordered stream, they behave predictably; on an unordered stream, "first" just means "whichever the implementation happens to produce first," which usually isn't useful to depend on. Explicitly marking a stream `.unordered()` when order genuinely doesn't matter to your computation can let a parallel stream run faster, since the runtime no longer needs to coordinate results back into a specific sequence.

## 3. Core concept

```java
import java.util.*;
import java.util.stream.*;

List<Integer> orderedSource = List.of(3, 1, 4, 1, 5); // has encounter order
Set<Integer> unorderedSource = new HashSet<>(orderedSource); // no defined encounter order

orderedSource.stream().findFirst();   // deterministic -- always 3
unorderedSource.stream().findFirst(); // "first" per HashSet's internal order, not meaningful

orderedSource.stream()
        .unordered() // explicitly say order doesn't matter for this pipeline
        .parallel()
        .forEach(System.out::println); // may print in any order, potentially faster
```

An ordered stream's operations behave predictably with respect to the source's sequence; explicitly marking a stream unordered relaxes that guarantee, which can enable more efficient parallel execution.

## 4. Diagram

<svg viewBox="0 0 640 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="an ordered stream preserves encounter order from its source; an unordered stream makes no such promise">
  <rect x="8" y="8" width="624" height="124" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">List.of(3,1,4).stream():</text>
  <rect x="220" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="240" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">3</text>
  <rect x="265" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="285" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">1</text>
  <rect x="310" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="330" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">4</text>
  <text x="410" y="34" fill="#6db33f" font-size="10" font-family="sans-serif">order guaranteed: 3, 1, 4</text>

  <text x="20" y="80" fill="#8b949e" font-size="11" font-family="sans-serif">new HashSet&lt;&gt;(...).stream():</text>
  <rect x="220" y="65" width="40" height="28" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/><text x="240" y="84" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">?</text>
  <rect x="265" y="65" width="40" height="28" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/><text x="285" y="84" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">?</text>
  <rect x="310" y="65" width="40" height="28" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/><text x="330" y="84" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">?</text>
  <text x="410" y="84" fill="#f85149" font-size="10" font-family="sans-serif">order not guaranteed</text>
  <text x="20" y="125" fill="#8b949e" font-size="10" font-family="sans-serif">List preserves index order; HashSet has no defined iteration order to preserve.</text>
</svg>

`List`-backed streams preserve a predictable sequence; `HashSet`-backed streams provide no such guarantee from the start.

## 5. Runnable example

Scenario: processing a queue of print jobs where order sometimes matters and sometimes doesn't — evolved from demonstrating deterministic ordered behavior, through showing unordered behavior from a `HashSet` source, to a version explicitly marking a pipeline unordered to enable faster parallel processing where order genuinely doesn't matter.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class OrderedBasic {
    public static void main(String[] args) {
        List<String> printQueue = List.of("job-A", "job-B", "job-C", "job-D");

        Optional<String> firstJob = printQueue.stream().findFirst();
        System.out.println("First job (deterministic): " + firstJob.orElse("none"));

        List<String> firstTwo = printQueue.stream().limit(2).toList();
        System.out.println("First two jobs (deterministic): " + firstTwo);
    }
}
```

**How to run:** `java OrderedBasic.java`

Expected output:
```
First job (deterministic): job-A
First two jobs (deterministic): [job-A, job-B]
```

`printQueue` is a `List`, which has a well-defined encounter order matching its index order. `.findFirst()` and `.limit(2)` both behave predictably and repeatably — every run of this program produces the exact same result, since `List` preserves the order jobs were added in.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class UnorderedSource {
    public static void main(String[] args) {
        Set<String> jobSet = new HashSet<>(List.of("job-A", "job-B", "job-C", "job-D"));

        // HashSet has no defined iteration order -- "first" here is implementation-dependent,
        // not something this code should rely on for correctness.
        Optional<String> firstJob = jobSet.stream().findFirst();
        System.out.println("First job from HashSet (order not guaranteed): " + firstJob.orElse("none"));

        System.out.println("What IS guaranteed: all four jobs are present.");
        System.out.println("Contains job-A: " + jobSet.contains("job-A"));
        System.out.println("Contains job-D: " + jobSet.contains("job-D"));
    }
}
```

**How to run:** `java UnorderedSource.java`

Expected output (the exact first job may vary by JVM/run — that's the point):
```
First job from HashSet (order not guaranteed): job-D
What IS guaranteed: all four jobs are present.
Contains job-A: true
Contains job-D: true
```

The real-world concern this adds: `jobSet` is backed by `HashSet`, which has no defined iteration order at all — `.findFirst()` still returns *some* element, but which one depends on `HashSet`'s internal hashing and bucket layout, not on any meaningful sequence. Code that needs a predictable "first" job should never be built on a `HashSet` source; what a `Set` *does* reliably guarantee is membership (`.contains(...)`), not order.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.stream.*;

public class ExplicitlyUnordered {
    public static void main(String[] args) {
        List<Integer> jobIds = IntStream.rangeClosed(1, 20).boxed().toList();

        // Order genuinely doesn't matter here -- we just need to know if ANY job needs urgent attention.
        // Marking .unordered() lets the runtime skip the bookkeeping needed to preserve encounter order.
        boolean anyUrgent = jobIds.parallelStream()
                .unordered()
                .anyMatch(id -> id % 7 == 0 && id > 10);

        System.out.println("Any urgent job found: " + anyUrgent);

        // Contrast: forEachOrdered on the same parallel stream WOULD force order, undoing the benefit.
        List<Integer> collectedInOrder = jobIds.parallelStream()
                .filter(id -> id % 2 == 0)
                .toList(); // toList() collects the RESULT in encounter order regardless of parallel execution
        System.out.println("Even job IDs, collected in order: " + collectedInOrder);
    }
}
```

**How to run:** `java ExplicitlyUnordered.java`

Expected output:
```
Any urgent job found: true
Even job IDs, collected in order: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
```

This shows `.unordered()` used deliberately: `anyMatch` only needs a yes/no answer, so declaring the pipeline unordered removes any need for the parallel runtime to coordinate which thread's result "counts" as being found first — purely a performance hint here, since `anyMatch`'s *result* (`true`/`false`) doesn't depend on order regardless. The second part shows that `.toList()` still collects results in encounter order by default (even on a parallel stream, since `toList` respects the source's ordering unless `.unordered()` was applied) — `.unordered()` changes what guarantees the *pipeline* provides, not automatically every terminal operation's behavior.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `jobIds` is a `List<Integer>` of `1` through `20`, built via `IntStream.rangeClosed(1, 20).boxed().toList()` (see [[intstream-range-rangeclosed]] and [[boxed]]) — this source has a well-defined encounter order matching numeric sequence.

For the first computation, `jobIds.parallelStream().unordered().anyMatch(id -> id % 7 == 0 && id > 10)`: `.parallelStream()` creates a parallel stream (still ordered by default, inheriting `List`'s order), and `.unordered()` explicitly relaxes that guarantee for this pipeline. `.anyMatch(...)` then searches for any ID that's both a multiple of `7` and greater than `10` — among `1` through `20`, `14` (`14 % 7 == 0 && 14 > 10`) qualifies. Because the pipeline is unordered, worker threads processing different chunks of the twenty IDs in parallel can each independently check their chunk and report a match the instant they find one, with no need to verify that no *earlier* (in original order) match exists first — that coordination requirement is exactly what `.unordered()` waives. The result, `true`, is found and returned as soon as any thread locates `14` (or, in principle, `21` if the range extended further, though it doesn't here).

For the second computation, `jobIds.parallelStream().filter(id -> id % 2 == 0).toList()`: this parallel stream is *not* marked unordered, so it retains its inherited encounter order from `jobIds`. `.filter(...)` keeps only even IDs (`2, 4, 6, ..., 20`) — ten values — and even though the filtering work may be distributed and executed out of order across threads, `.toList()` (the terminal operation) reassembles the final result back into the original encounter order before returning it.

```
Pipeline 1 (unordered): parallel workers search chunks independently, first hit wins immediately
  chunk [1..7]:   no match (7 itself is not > 10)
  chunk [8..14]:  finds 14 -- reports true right away, no need to wait for other chunks
  chunk [15..20]: (may not even be checked if 14's chunk finishes first)

Pipeline 2 (ordered, default): parallel filtering, but toList() reassembles the result in order
  filtered evens found across all chunks -> reassembled: [2,4,6,8,10,12,14,16,18,20]
```

`anyUrgent` is `true`, printed as `"Any urgent job found: true"`. `collectedInOrder` is `[2, 4, 6, 8, 10, 12, 14, 16, 18, 20]`, printed in that exact numeric order — proving that even without `.unordered()`, a parallel stream's *final collected result* still respects the source's encounter order by default, since `List`-based sources are ordered unless explicitly told otherwise.

## 7. Gotchas & takeaways

> Calling `.unordered()` doesn't change *what* elements are in the stream — only whether the pipeline is permitted to process and report them out of the source's original sequence. It's purely a hint that can enable performance optimizations (especially for parallel streams using operations like `distinct`, `limit`, or `anyMatch` that would otherwise need extra coordination to respect order) — it never changes the correctness of element *presence*, only the guarantees around their *sequence*.

- An ordered stream preserves a meaningful encounter order from its source (e.g. a `List`'s index order); an unordered stream (e.g. from a `HashSet`) has no such defined sequence.
- `findFirst()`, `limit()`, `skip()`, and comparator-free `sorted()` all rely on encounter order to produce meaningful, deterministic results.
- `.unordered()` explicitly relaxes the order guarantee for a pipeline, which can let parallel execution skip coordination overhead for operations like `anyMatch`, `distinct`, or `limit`.
- A `Set`/`Map` built on hashing (`HashSet`, `HashMap`) provides no iteration order guarantee by nature — don't rely on "the first element" from such a source meaning anything specific.
- Even on an unordered-execution parallel stream, terminal operations like `.toList()`/`.collect(...)` still respect the source's original encounter order in their *final result*, unless `.unordered()` was explicitly applied to the pipeline.
