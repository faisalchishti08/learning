---
card: java
gi: 354
slug: multiple-bounds-t-extends-a-b
title: Multiple bounds (T extends A & B)
---

## 1. What it is

Multiple bounds let a single type parameter require more than one capability at once, using `&` to join them: `<T extends A & B>` means "T must be a subtype of both A and B." At most one of the bounds may be a class (and if there is one, it must come first); any number of the remaining bounds must be interfaces — this mirrors Java's own single-inheritance-of-class, multiple-inheritance-of-interface rule for ordinary classes.

```java
public class MultipleBoundsDemo {
    interface Named { String getName(); }

    static <T extends Comparable<T> & Named> T maxByNameLength(T a, T b) {
        return a.getName().length() >= b.getName().length() ? a : b;
    }

    record Person(String getName_, int age) implements Comparable<Person>, Named {
        public String getName() { return getName_; }
        public int compareTo(Person other) { return Integer.compare(age, other.age); }
    }

    public static void main(String[] args) {
        Person alice = new Person("Alice", 30);
        Person bo = new Person("Bo", 25);
        System.out.println(maxByNameLength(alice, bo).getName());
    }
}
```

`<T extends Comparable<T> & Named>` requires `T` to satisfy *both* interfaces simultaneously — `maxByNameLength` can call both `compareTo` (unused here, but available) and `getName()` on values of type `T`, something neither bound alone would allow.

## 2. Why & when

Some generic algorithms genuinely need more than one capability from their type parameter — sorting by a custom criterion while also requiring the elements be nameable, or requiring both numeric behavior and natural ordering. A single bound only grants one set of methods; multiple bounds let the type system express "needs both," checked entirely at compile time.

- **Combining orthogonal capabilities** — a type that must be both `Comparable` (orderable) and `Serializable` (persistable), or both a `Number` and `Comparable<T>` (as with the earlier `range` example), when a generic algorithm genuinely needs both.
- **Requiring a specific class's behavior plus an additional interface contract** — `<T extends AbstractHandler & Cancellable>`, when the algorithm needs both the base class's shared implementation and a specific additional capability described by an interface.
- **Expressing precise generic contracts** — rather than casting or relying on runtime `instanceof` checks, multiple bounds let the compiler verify upfront that any type used will support everything the method's body actually calls.

The single-class-first rule exists because Java classes support only single inheritance — if two classes were both allowed as bounds, there'd be no consistent way to determine "is T a subtype of both," since a type can only extend one class; interfaces, supporting multiple inheritance, have no such restriction and can be freely combined.

## 3. Core concept

```java
public class MultipleBoundsCore {
    interface Taggable { String getTag(); }

    static <T extends Number & Taggable> void report(T value) {
        System.out.println("[" + value.getTag() + "] value = " + value.doubleValue());
    }

    static class TaggedScore extends Number implements Taggable {
        private final double score;
        private final String tag;
        TaggedScore(double score, String tag) { this.score = score; this.tag = tag; }
        public String getTag() { return tag; }
        public int intValue() { return (int) score; }
        public long longValue() { return (long) score; }
        public float floatValue() { return (float) score; }
        public double doubleValue() { return score; }
    }

    public static void main(String[] args) {
        report(new TaggedScore(87.5, "quiz-1"));
    }
}
```

**How to run:** `java MultipleBoundsCore.java`

`report`'s type parameter requires *both* `Number`'s `doubleValue()` and `Taggable`'s `getTag()` — `TaggedScore` was written specifically to satisfy both bounds (extending `Number`, implementing `Taggable`), letting it be passed to `report` at all.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a type parameter bounded by both a class and interfaces must satisfy every bound simultaneously, with at most one class allowed and it must come first">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">&lt;T extends Number &amp; Comparable&lt;T&gt; &amp; Taggable&gt;</text>
  <rect x="20" y="45" width="160" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="100" y="65" fill="#6db33f" font-size="9" text-anchor="middle">Number (class, first)</text>
  <rect x="200" y="45" width="180" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="290" y="65" fill="#79c0ff" font-size="9" text-anchor="middle">Comparable&lt;T&gt; (interface)</text>
  <rect x="400" y="45" width="160" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="65" fill="#79c0ff" font-size="9" text-anchor="middle">Taggable (interface)</text>
  <text x="20" y="105" fill="#8b949e" font-size="9">T must satisfy ALL THREE bounds at once -- exactly one class allowed, any number of interfaces.</text>
</svg>

## 5. Runnable example

Scenario: a small leaderboard ranking utility, evolved from one requiring only comparability, into one also requiring a display-name capability via a second bound, into a production-style ranker combining three bounds to sort, display, and validate entries all through the type system.

### Level 1 — Basic

```java
import java.util.List;
import java.util.Collections;

public class LeaderboardBasic {
    static <T extends Comparable<T>> T topEntry(List<T> entries) { // single bound only
        return Collections.max(entries);
    }

    public static void main(String[] args) {
        System.out.println("Top score: " + topEntry(List.of(72, 95, 61)));
    }
}
```

**How to run:** `java LeaderboardBasic.java`

`topEntry` can only compare entries — it has no way to display anything more meaningful than the raw value itself, since `Comparable<T>` alone doesn't guarantee any kind of name or label is available.

### Level 2 — Intermediate

```java
import java.util.List;
import java.util.Collections;

public class LeaderboardIntermediate {
    interface Named { String getDisplayName(); }

    static <T extends Comparable<T> & Named> void announceTop(List<T> entries) {
        T top = Collections.max(entries);
        System.out.println("Top entry: " + top.getDisplayName());
    }

    record PlayerScore(String name, int score) implements Comparable<PlayerScore>, Named {
        public int compareTo(PlayerScore other) { return Integer.compare(score, other.score); }
        public String getDisplayName() { return name + " (" + score + ")"; }
    }

    public static void main(String[] args) {
        announceTop(List.of(
                new PlayerScore("Ada", 72),
                new PlayerScore("Grace", 95),
                new PlayerScore("Alan", 61)));
    }
}
```

**How to run:** `java LeaderboardIntermediate.java`

Adding the `Named` bound alongside `Comparable<T>` lets `announceTop` call `getDisplayName()` on whichever entry `Collections.max` determines is the top one — both bounds are genuinely needed: `Comparable` for finding the max, `Named` for displaying it meaningfully.

### Level 3 — Advanced

```java
import java.util.List;
import java.util.Collections;

public class LeaderboardAdvanced {
    interface Named { String getDisplayName(); }
    interface Validatable { boolean isValid(); }

    static <T extends Comparable<T> & Named & Validatable> void announceTop(List<T> entries) {
        List<T> validEntries = entries.stream().filter(Validatable::isValid).toList();
        if (validEntries.isEmpty()) {
            System.out.println("No valid entries to rank.");
            return;
        }
        T top = Collections.max(validEntries);
        System.out.println("Top valid entry: " + top.getDisplayName());
    }

    record PlayerScore(String name, int score) implements Comparable<PlayerScore>, Named, Validatable {
        public int compareTo(PlayerScore other) { return Integer.compare(score, other.score); }
        public String getDisplayName() { return name + " (" + score + ")"; }
        public boolean isValid() { return score >= 0; } // negative scores are considered invalid data
    }

    public static void main(String[] args) {
        announceTop(List.of(
                new PlayerScore("Ada", 72),
                new PlayerScore("Grace", 95),
                new PlayerScore("Alan", -10))); // invalid, should be excluded from ranking
    }
}
```

**How to run:** `java LeaderboardAdvanced.java`

A third bound, `Validatable`, is added so `announceTop` can filter out invalid entries (`Alan`'s corrupted, negative score) *before* ranking, demonstrating three independent capabilities — comparison, display, and validation — all required simultaneously from the same type parameter, each contributing exactly the one method the algorithm actually calls.

## 6. Walkthrough

Execution starts in `main`, which builds a list of three `PlayerScore` records — `Ada` (72), `Grace` (95), `Alan` (-10) — and calls `announceTop` on it.

Inside `announceTop`, the compiler has already verified, at the call site, that `PlayerScore` satisfies all three bounds: it implements `Comparable<PlayerScore>`, `Named`, and `Validatable`.

`entries.stream().filter(Validatable::isValid).toList()` processes each entry: `Ada.isValid()` checks `72 >= 0` (true, kept); `Grace.isValid()` checks `95 >= 0` (true, kept); `Alan.isValid()` checks `-10 >= 0` (false, excluded). `validEntries` now contains only `Ada` and `Grace`.

`validEntries.isEmpty()` is `false` (two entries remain), so the early-return branch is skipped. `Collections.max(validEntries)` uses each `PlayerScore`'s `compareTo` method (comparing by `score`) to find the largest: comparing `Ada` (72) and `Grace` (95), `Grace`'s `score` is higher, so `Collections.max` returns the `Grace` record.

`top.getDisplayName()` is called on that `Grace` record, returning `"Grace (95)"`. `main` prints `Top valid entry: Grace (95)` — notably, `Alan`'s corrupted `-10` score was never even considered during the max computation, since it was filtered out before `Collections.max` ever ran.

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="entries are filtered by validity first, removing the corrupted negative score, then the max is found among only the valid remaining entries, and its display name is shown">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">entries = [Ada(72), Grace(95), Alan(-10)]</text>
  <text x="20" y="55" fill="#f85149" font-size="10">filter(isValid): Ada kept, Grace kept, Alan(-10) EXCLUDED -&gt; validEntries = [Ada(72), Grace(95)]</text>
  <text x="20" y="80" fill="#79c0ff" font-size="10">Collections.max(validEntries) via compareTo(score) -&gt; Grace(95) wins</text>
  <text x="20" y="105" fill="#6db33f" font-size="10">top.getDisplayName() -&gt; "Grace (95)" -&gt; printed</text>
</svg>

## 7. Gotchas & takeaways

> If a class bound is used, it must be listed *first* in the `&`-joined list (`<T extends SomeClass & SomeInterface>`, never the reverse order) — and only one class may appear at all, since Java classes support only single inheritance, unlike interfaces.

- Join multiple bounds with `&`: `<T extends A & B & C>` requires `T` to satisfy every listed bound simultaneously.
- At most one bound may be a concrete class, and if present, it must come first; any number of interface bounds may follow.
- Each bound unlocks that specific type's methods — the generic code can call methods from *any* of the combined bounds, not just the first one listed.
- Multiple bounds are checked entirely at compile time — they don't change runtime behavior, only which types are permitted to be used for that type parameter.
- Prefer combining bounds only when a generic algorithm genuinely needs multiple distinct capabilities — an overly long list of bounds may be a sign the design would be clearer expressed with a dedicated interface that itself extends the needed capabilities, rather than repeating the same multi-bound combination at every use site.
