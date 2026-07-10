---
card: java
gi: 846
slug: collections-min-max-frequency-disjoint
title: Collections.min / max / frequency / disjoint
---

## 1. What it is

`Collections` provides several small algorithmic utilities that answer common questions about a `Collection` without requiring manual iteration code: `Collections.min(collection)`/`max(collection)` (find the smallest/largest element, by natural ordering or a supplied `Comparator`), `Collections.frequency(collection, element)` (count how many times a specific element appears, using `equals()`), and `Collections.disjoint(collection1, collection2)` (check whether two collections share **no** common elements at all, returning `true` if they're completely disjoint). Each is a straightforward O(n) (or O(n*m) for `disjoint` in the worst case) linear operation, but supplied so common code doesn't need to hand-write the equivalent loop.

## 2. Why & when

These methods exist purely for convenience and correctness — finding a minimum or maximum, counting occurrences, or checking for any overlap between two collections are each a handful of lines to write by hand, and hand-written versions are an easy place for off-by-one or edge-case bugs (empty collection handling, tie-breaking) to creep in. Reach for `Collections.min`/`max` instead of manually looping when a single min/max value (not a full sort) is all that's needed — it communicates intent more clearly and avoids sorting overhead. `Collections.frequency` is the direct way to answer "how many duplicates of X are in this collection," which `Collection.contains` alone can't tell you (it only answers "at least one"). `Collections.disjoint` answers a genuinely common question — "do these two sets of things overlap at all" — efficiently and without constructing an intermediate intersection collection just to check if it's empty.

## 3. Core concept

```java
List<Integer> scores = List.of(72, 91, 60, 85, 78, 91);

Collections.min(scores); // 60
Collections.max(scores); // 91
Collections.frequency(scores, 91); // 2 -- appears twice

List<Integer> teamA = List.of(1, 2, 3);
List<Integer> teamB = List.of(4, 5, 6);
List<Integer> teamC = List.of(3, 7, 8);

Collections.disjoint(teamA, teamB); // true -- no shared elements at all
Collections.disjoint(teamA, teamC); // false -- both contain 3
```

`Collections.disjoint` short-circuits as soon as it finds any single common element — it never needs to compute the full intersection, just detect whether one exists at all.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Collections.disjoint returns true when two collections share no elements at all, and false the moment even one shared element is found">
  <g font-family="sans-serif">
    <circle cx="180" cy="90" r="60" fill="#1c2430" stroke="#3fb950" stroke-width="1.5" opacity="0.7"/>
    <text x="180" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">teamA {1,2,3}</text>
    <circle cx="320" cy="90" r="60" fill="#1c2430" stroke="#3fb950" stroke-width="1.5" opacity="0.7"/>
    <text x="320" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">teamB {4,5,6}</text>
    <text x="250" y="150" fill="#3fb950" font-size="10" text-anchor="middle">disjoint(A,B) = true — no overlap</text>
  </g>

  <g font-family="sans-serif">
    <circle cx="470" cy="90" r="60" fill="#1c2430" stroke="#f85149" stroke-width="1.5" opacity="0.7"/>
    <text x="450" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">A {1,2,3}</text>
    <circle cx="530" cy="90" r="60" fill="#1c2430" stroke="#f85149" stroke-width="1.5" opacity="0.7"/>
    <text x="555" y="90" fill="#e6edf3" font-size="10" text-anchor="middle">C {3,7,8}</text>
    <text x="500" y="150" fill="#f85149" font-size="10" text-anchor="middle">disjoint(A,C) = false — share "3"</text>
  </g>
</svg>

*`disjoint` returns `true` for zero overlap, `false` the instant even one shared element is confirmed.*

## 5. Runnable example

Scenario: analyzing a dataset of exam scores and comparing two class rosters, growing from basic min/max/frequency queries, to custom-comparator min/max, to a genuine disjoint-set check between overlapping and non-overlapping rosters.

### Level 1 — Basic

```java
import java.util.*;

public class ScoreAnalysisBasic {
    public static void main(String[] args) {
        List<Integer> scores = List.of(72, 91, 60, 85, 78, 91);

        System.out.println("lowest score: " + Collections.min(scores));
        System.out.println("highest score: " + Collections.max(scores));
        System.out.println("how many scored 91: " + Collections.frequency(scores, 91));
        System.out.println("how many scored 100 (none did): " + Collections.frequency(scores, 100));
    }
}
```

**How to run:** `java ScoreAnalysisBasic.java` (JDK 17+).

Expected output:
```
lowest score: 60
highest score: 91
how many scored 91: 2
how many scored 100 (none did): 0
```

`Collections.min`/`max` scan the collection once, tracking the running minimum/maximum — no full sort is performed, since only the extreme value is needed, not the complete order.

### Level 2 — Intermediate

```java
import java.util.*;

public class ScoreAnalysisCustomComparator {
    record Student(String name, int score) {}

    public static void main(String[] args) {
        List<Student> students = List.of(
            new Student("Alice", 91), new Student("Bob", 60), new Student("Charlie", 91)
        );

        // min/max accept a Comparator for non-Comparable types or non-default orderings.
        Student topScorer = Collections.max(students, Comparator.comparingInt(Student::score));
        Student bottomScorer = Collections.min(students, Comparator.comparingInt(Student::score));

        System.out.println("top scorer: " + topScorer.name() + " (" + topScorer.score() + ")");
        System.out.println("bottom scorer: " + bottomScorer.name() + " (" + bottomScorer.score() + ")");

        // Collections.frequency uses equals() -- works for records, which generate equals() automatically.
        List<Student> roster = List.of(
            new Student("Alice", 91), new Student("Alice", 91), new Student("Bob", 60)
        );
        System.out.println("count of Alice(91) entries: " + Collections.frequency(roster, new Student("Alice", 91)));
    }
}
```

**How to run:** `java ScoreAnalysisCustomComparator.java`.

Expected output:
```
top scorer: Alice (91) (or Charlie, since both tie at 91 -- max returns the FIRST maximal element encountered)
bottom scorer: Bob (60)
count of Alice(91) entries: 2
```

The real-world concern added: `Collections.max`/`min` accepting an explicit `Comparator` for a type (`Student`) that isn't itself `Comparable` — and `Collections.frequency` correctly using `equals()` (here, a record's auto-generated field-based equality) to count matching entries, working just as well for custom types as for primitives/strings.

### Level 3 — Advanced

```java
import java.util.*;

public class RosterOverlapCheck {
    public static void main(String[] args) {
        Set<String> teamA = new HashSet<>(Set.of("alice", "bob", "carol"));
        Set<String> teamB = new HashSet<>(Set.of("dave", "erin", "frank"));
        Set<String> teamC = new HashSet<>(Set.of("carol", "grace", "henry"));

        System.out.println("teamA and teamB disjoint (no shared members)? " + Collections.disjoint(teamA, teamB));
        System.out.println("teamA and teamC disjoint? " + Collections.disjoint(teamA, teamC));

        // A practical use: validating that a NEW team roster doesn't accidentally reuse existing members.
        Set<String> proposedTeamD = new HashSet<>(Set.of("ivan", "julia", "bob")); // "bob" is already on teamA!

        boolean noConflictWithA = Collections.disjoint(proposedTeamD, teamA);
        boolean noConflictWithB = Collections.disjoint(proposedTeamD, teamB);
        boolean noConflictWithC = Collections.disjoint(proposedTeamD, teamC);

        System.out.println("proposed team D has no conflicts with A: " + noConflictWithA);
        System.out.println("proposed team D has no conflicts with B: " + noConflictWithB);
        System.out.println("proposed team D has no conflicts with C: " + noConflictWithC);

        if (!noConflictWithA) {
            Set<String> overlap = new HashSet<>(proposedTeamD);
            overlap.retainAll(teamA); // find exactly WHICH members overlap, once we know disjoint() said false
            System.out.println("overlapping members with team A: " + overlap);
        }
    }
}
```

**How to run:** `java RosterOverlapCheck.java`.

Expected output:
```
teamA and teamB disjoint (no shared members)? true
teamA and teamC disjoint? false
proposed team D has no conflicts with A: false
proposed team D has no conflicts with B: true
proposed team D has no conflicts with C: true
overlapping members with team A: [bob]
```

This adds the production-flavored hard case: using `Collections.disjoint` as a fast **pre-check** before doing the more expensive work of computing an actual intersection — `disjoint` only needs to find *one* shared element to return `false` and stop, whereas `retainAll` (used afterward, only once we know there *is* an overlap) must compute the complete intersection. This two-step pattern (`disjoint` as a cheap gate, `retainAll` only when needed to find specifics) avoids unnecessary intersection computation for the common case where two collections turn out to have no overlap at all.

## 6. Walkthrough

Tracing `RosterOverlapCheck.main`:

1. `Collections.disjoint(teamA, teamB)` iterates the smaller of the two collections (an internal optimization detail — the implementation picks whichever collection is likely cheaper to iterate) and checks, for each element, whether the *other* collection contains it. Since `teamA` (`alice, bob, carol`) and `teamB` (`dave, erin, frank`) share nothing, every check comes back negative, and after exhausting all elements without finding a match, `disjoint` returns `true`.
2. `Collections.disjoint(teamA, teamC)` performs the same check, but `teamC` contains `"carol"`, which is also in `teamA`. The moment this shared element is found (regardless of which collection's elements are being iterated), `disjoint` returns `false` immediately — it doesn't need to check any remaining elements once one match is confirmed.
3. `proposedTeamD` (`ivan, julia, bob`) is checked for conflicts against all three existing teams. Against `teamA`, `"bob"` is a shared member, so `disjoint` returns `false`, meaning `noConflictWithA` is `false`. Against `teamB` and `teamC`, no shared members exist, so both checks return `true`.
4. Since `noConflictWithA` is `false` (there is a conflict), the code proceeds to actually compute the overlap: `overlap = new HashSet<>(proposedTeamD)` copies `proposedTeamD` defensively, then `overlap.retainAll(teamA)` keeps only the elements also present in `teamA` — this full intersection computation only happens because the cheaper `disjoint` check already confirmed it would find something, avoiding the extra work in the (more common, in a well-organized system) case where teams don't overlap at all.
5. The final printed `overlap` set correctly contains just `["bob"]`, the single member appearing in both `proposedTeamD` and `teamA`.

## 7. Gotchas & takeaways

> **Gotcha:** `Collections.min`/`max` throw `NoSuchElementException` if the supplied collection is empty — always check `isEmpty()` first, or otherwise guarantee non-emptiness, before calling either on data whose size isn't already known to be at least one.

- `Collections.min`/`max` find the smallest/largest element via a single linear scan — cheaper than a full sort when only the extreme value is needed, and both accept an optional `Comparator` for non-`Comparable` types or custom orderings.
- `Collections.frequency` counts occurrences of a specific element using `equals()` — the direct way to answer "how many duplicates," which `contains` alone cannot.
- `Collections.disjoint` checks for **any** overlap between two collections, short-circuiting as soon as one shared element is found — cheaper than computing a full intersection just to check if it's empty.
- Use `disjoint` as a fast pre-check gate, and only compute an actual intersection (via `retainAll` on a defensive copy) when the specific overlapping elements are actually needed.
- All of these methods throw `NoSuchElementException` (`min`/`max`) or behave predictably on empty input (`frequency` returns `0`, `disjoint` on an empty collection returns `true`) — know which applies before calling them on data of uncertain size.
