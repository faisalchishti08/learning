---
card: java
gi: 524
slug: stateless-vs-stateful-operations
title: Stateless vs stateful operations
---

## 1. What it is

A **stateless** intermediate operation processes each element independently, with no memory of any other element — `filter`, `map`, `peek` are stateless: whether an element passes `filter` or what `map` turns it into depends only on that one element. A **stateful** intermediate operation needs information about *other* elements to process any single one — `sorted`, `distinct`, and `limit`/`skip` (in a parallel context) are stateful: `sorted` needs to see every element to know any one element's final position; `distinct` needs to remember every element seen so far to detect duplicates.

## 2. Why & when

This distinction matters for both performance and how a pipeline can execute. Stateless operations can process one element fully through the chain before moving to the next (as covered in [[lazy-evaluation]]), require no extra memory beyond the current element, and parallelize trivially — each element's work is fully independent. Stateful operations break that: `sorted` and `distinct` must buffer some or all of the stream before they can produce output, using memory proportional to the stream's size (for `distinct`, proportional to the number of unique elements seen), and they're inherently harder to parallelize efficiently, since work on one element can depend on work on another.

## 3. Core concept

```java
import java.util.stream.*;

// Stateless: each element decided independently, no memory needed
Stream.of(5, 2, 8, 1).filter(n -> n > 3).map(n -> n * 2);

// Stateful: sorted needs the WHOLE stream before producing element #1 of its output
Stream.of(5, 2, 8, 1).sorted();

// Stateful: distinct needs to remember every element seen so far
Stream.of(1, 2, 1, 3, 2).distinct();
```

Stateless operations look at one element at a time in isolation; stateful operations need broader knowledge of the stream — the whole thing (for `sorted`) or everything seen so far (for `distinct`) — before they can correctly process even one element.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="stateless operations process one element at a time; stateful operations must buffer across elements">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="sans-serif">filter/map (stateless):</text>
  <rect x="230" y="15" width="40" height="28" fill="#1c2430" stroke="#6db33f"/><text x="250" y="34" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">5</text>
  <text x="280" y="34" fill="#8b949e" font-size="10" font-family="sans-serif">processed alone, no memory needed</text>

  <text x="20" y="80" fill="#8b949e" font-size="11" font-family="sans-serif">sorted (stateful):</text>
  <rect x="230" y="65" width="40" height="28" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="250" y="84" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">5</text>
  <rect x="275" y="65" width="40" height="28" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="295" y="84" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">2</text>
  <rect x="320" y="65" width="40" height="28" fill="#0d1117" stroke="#8b949e" stroke-dasharray="3,2"/><text x="340" y="84" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">8</text>
  <text x="410" y="84" fill="#f85149" font-size="10" font-family="sans-serif">buffered -- all needed before output starts</text>
  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">Stateful operations can't emit their first result until they've seen enough of the stream.</text>
</svg>

Stateless operations pass elements through one at a time; stateful ones must accumulate information across multiple elements before they can emit anything.

## 5. Runnable example

Scenario: processing a stream of incoming sensor readings for a monitoring dashboard — evolved from a plain stateless pipeline, through adding `distinct` and observing it needs to buffer, to a version measuring the memory/timing difference between stateless and stateful stages on a larger stream.

### Level 1 — Basic

```java
import java.util.*;
import java.util.stream.*;

public class StatelessBasic {
    public static void main(String[] args) {
        List<Integer> readings = List.of(45, -3, 78, 12, -8, 91);

        List<Integer> processed = readings.stream()
                .filter(r -> r >= 0)   // stateless: each reading judged alone
                .map(r -> r * 10)      // stateless: each reading transformed alone
                .toList();

        System.out.println("Processed: " + processed);
    }
}
```

**How to run:** `java StatelessBasic.java`

Expected output:
```
Processed: [450, 780, 120, 910]
```

Both `.filter(...)` and `.map(...)` are stateless: each reading's fate (kept or dropped, and its transformed value) is decided purely by looking at that one reading, with no need to know anything about any other reading in the stream.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.stream.*;

public class StatefulDistinct {
    public static void main(String[] args) {
        List<Integer> readings = List.of(45, 12, 78, 12, 45, 91, 78);

        List<Integer> uniqueValid = readings.stream()
                .filter(r -> r >= 0)  // stateless
                .distinct()           // stateful -- must remember everything seen so far
                .sorted()             // stateful -- must see everything before producing output
                .toList();

        System.out.println("Unique, sorted readings: " + uniqueValid);
    }
}
```

**How to run:** `java StatefulDistinct.java`

Expected output:
```
Unique, sorted readings: [12, 45, 78, 91]
```

The real-world concern this adds: `.distinct()` (see [[distinct]]) must track every distinct value seen so far to know whether the *next* value is a repeat — it cannot decide about `12` (the second occurrence) without remembering the first `12`. `.sorted()` (see [[sorted-sorted-comparator]]) goes further still: it cannot emit even its first output element until it has seen the *entire* stream, since the smallest element might be the very last one encountered.

### Level 3 — Advanced

```java
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.*;

public class StatelessVsStatefulTiming {
    public static void main(String[] args) {
        List<Integer> largeReadings = IntStream.range(0, 1_000_000)
                .map(i -> (i * 37) % 500_000) // creates lots of duplicates across a wide range
                .boxed()
                .toList();

        AtomicLong statelessCount = new AtomicLong();
        long t1 = System.nanoTime();
        long resultA = largeReadings.stream()
                .filter(r -> r % 2 == 0)  // stateless
                .peek(r -> statelessCount.incrementAndGet())
                .count();
        long t2 = System.nanoTime();

        AtomicLong statefulCount = new AtomicLong();
        long t3 = System.nanoTime();
        long resultB = largeReadings.stream()
                .distinct()                // stateful -- must track every unique value seen
                .peek(r -> statefulCount.incrementAndGet())
                .count();
        long t4 = System.nanoTime();

        System.out.println("Stateless (filter+count) result: " + resultA);
        System.out.println("Stateful (distinct+count) result: " + resultB);
        System.out.println("Both completed: " + (t2 > t1 && t4 > t3));
    }
}
```

**How to run:** `java StatelessVsStatefulTiming.java`

Expected output:
```
Stateless (filter+count) result: 500000
Stateful (distinct+count) result: 500000
```

This demonstrates the practical difference at scale: the stateless pipeline (`filter` then `count`) processes each of the one million readings independently, requiring no extra memory beyond the current element. The stateful pipeline (`distinct` then `count`) must internally maintain a set of every unique value seen among the million readings — needing memory proportional to the number of distinct values, a fundamentally different resource profile from the stateless version even though both ultimately call `.count()`. Since `37` and `500,000` share no common factor, `(i * 37) % 500_000` happens to visit every value from `0` to `499,999` exactly twice across the full million-element range — so the *distinct* count here also comes out to `500,000`, but `distinct()` had to build and check against an internal set of half a million entries to arrive at that number, unlike `filter`, which needed no such structure at all.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `largeReadings` is built as a list of one million integers, generated by `(i * 37) % 500_000` for `i` from `0` to `999,999`. Because `37` shares no common factor with `500,000`, this formula visits every value from `0` to `499,999` exactly twice across the full million-element range — once while `i` runs through its first `500,000` values, and again while it runs through the second `500,000`.

For the stateless computation, `largeReadings.stream().filter(r -> r % 2 == 0).peek(...).count()`: each of the one million readings is processed independently — `.filter(...)` decides whether to keep it based only on that reading's own value (`r % 2 == 0`), with zero dependency on any other reading. This is why a stateless pipeline can, conceptually, process element `500,000` without needing to have remembered anything at all about elements `0` through `499,999`.

For the stateful computation, `largeReadings.stream().distinct().peek(...).count()`: `.distinct()` must maintain an internal set of every value it has encountered so far. Processing each reading requires checking whether its value has already appeared among the *entire preceding* stream — meaning `distinct()`'s internal memory usage grows as it processes more of the stream, up to the number of genuinely unique values it eventually finds: `500,000` here, since every value in that range shows up exactly twice and the second occurrence of each is filtered out as a duplicate.

```
Stateless pipeline:  reading -> filter (looks only at THIS reading) -> keep/drop -> next reading
                      (no memory of prior readings needed at any point)

Stateful pipeline:   reading -> distinct (checks against a growing set of ALL prior unique readings)
                      -> keep if new, drop if already seen -> next reading
                      (internal set grows to hold up to 500,000 unique values)
```

`resultA`, the count of even readings after filtering, is `500000` (exactly half of a million readings, since the modulo formula happens to produce an even split here). `resultB`, the count of distinct readings, is also `500000` — but arrived at by a completely different mechanism: `distinct()` had to build and query an internal set of half a million entries to filter out the second occurrence of every repeated value, work that `filter()` never needed to do at all. `t2 > t1 && t4 > t3` simply confirms both computations ran to completion in increasing time order, printed as `"Both completed: true"` — the real point being that the *nature* of the work performed by `filter` versus `distinct` is fundamentally different, even when their final counts happen to coincide.

## 7. Gotchas & takeaways

> A pipeline containing even one stateful operation loses the "process one element fully through the chain" efficiency of a purely stateless pipeline (see [[lazy-evaluation]]) — `sorted()` in particular must fully buffer the stream before *any* downstream operation can run, which can be a real memory concern for very large streams, and is simply impossible for a genuinely infinite stream (calling `.sorted()` on an infinite `Stream.iterate(...)` source would never terminate, since `sorted` can never be sure it has seen everything).

- Stateless operations (`filter`, `map`, `peek`) process each element independently, needing no memory of other elements.
- Stateful operations (`sorted`, `distinct`, and `limit`/`skip` in parallel contexts) need information spanning multiple elements, requiring internal buffering.
- `distinct()` needs memory proportional to the number of unique elements seen; `sorted()` needs to buffer the entire stream before producing any output.
- A stateful operation, especially `sorted()`, cannot be meaningfully applied to a genuinely infinite stream, since it can never finish gathering the information it needs.
- Recognizing which operations in a pipeline are stateful helps predict memory usage and understand why some operations (like `sorted`) can't participate in the same element-by-element, fully lazy execution model that purely stateless pipelines enjoy.
