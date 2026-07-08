---
card: java
gi: 427
slug: navigableset-interface
title: NavigableSet interface
---

## 1. What it is

`NavigableSet<E>`, added in Java 6 and implemented by `TreeSet`, extends `SortedSet` with the same "closest neighbor" navigation `NavigableMap` provides for maps: `floor(e)` (largest element ≤ `e`), `ceiling(e)` (smallest element ≥ `e`), `lower(e)` (largest element strictly < `e`), `higher(e)` (smallest element strictly > `e`), plus `headSet`/`tailSet`/`subSet` range views, `descendingSet()`/`descendingIterator()` for reverse order, and `pollFirst()`/`pollLast()` to atomically remove and return the smallest/largest element.

## 2. Why & when

A plain `SortedSet` gives you sorted iteration and `first()`/`last()`, but nothing for "what's the closest element to this value?" — a common need whenever a set of sorted values represents discrete points you need to navigate around, rather than just enumerate. `NavigableSet` fills that gap with logarithmic-time neighbor lookups, backed by `TreeSet`'s underlying red-black tree.

You reach for `NavigableSet` for scheduling problems (find the next available time slot at or after a requested time), for building simple range-based lookups (find the closest threshold value at or below a measurement), or for maintaining any sorted collection of discrete values where "nearest neighbor" queries matter — meeting time slots, milestone markers, or a set of valid discrete sizes/tiers.

## 3. Core concept

```java
import java.util.*;

NavigableSet<Integer> availableSlots = new TreeSet<>(Set.of(900, 930, 1000, 1030, 1100)); // minutes past midnight

availableSlots.floor(1015);    // 1000 -- largest slot <= 1015
availableSlots.ceiling(1015);  // 1030 -- smallest slot >= 1015
availableSlots.lower(1000);    // 930  -- largest slot STRICTLY less than 1000
availableSlots.higher(1000);   // 1030 -- smallest slot STRICTLY greater than 1000

availableSlots.first();        // 900
availableSlots.last();         // 1100
```

Exactly the same `floor`/`ceiling` (inclusive) versus `lower`/`higher` (strictly excludes an exact match) distinction as `NavigableMap` — the two interfaces share the same navigational vocabulary, just for keys-with-values versus standalone elements.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Given a requested time, floor and ceiling look inclusively at or around it on a sorted set of available slots; lower and higher always look strictly past an exact match">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <line x1="40" y1="80" x2="600" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <circle cx="150" cy="80" r="5" fill="#6db33f"/><text x="150" y="65" fill="#6db33f" font-size="10" text-anchor="middle">9:00</text>
  <circle cx="300" cy="80" r="5" fill="#e6edf3"/><text x="300" y="65" fill="#e6edf3" font-size="10" text-anchor="middle">10:00</text>
  <circle cx="450" cy="80" r="5" fill="#79c0ff"/><text x="450" y="65" fill="#79c0ff" font-size="10" text-anchor="middle">10:30</text>

  <text x="380" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">requested 10:15 -&gt;</text>
  <text x="300" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">floor(10:15)=10:00</text>
  <text x="450" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ceiling(10:15)=10:30</text>
  <text x="320" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">10:15 isn't in the set, so floor/ceiling straddle it -- lower/higher would behave identically here.</text>
</svg>

Neighbor lookups find the closest actual elements to a requested value, whether or not that exact value exists in the set.

## 5. Runnable example

Scenario: a meeting-room scheduling system with a fixed set of bookable time slots — the same slot set, evolved from finding the nearest available slot to a requested time, through range views for reporting a day's remaining slots, to processing slots in reverse (latest-first) and removing them as they're booked.

### Level 1 — Basic

```java
import java.util.*;

public class MeetingSlotLookup {
    public static void main(String[] args) {
        NavigableSet<Integer> slots = new TreeSet<>(Set.of(900, 930, 1000, 1030, 1100)); // minutes past midnight

        int requested = 1015;
        System.out.println("Requested: " + requested);
        System.out.println("Nearest slot at or before: " + slots.floor(requested));
        System.out.println("Nearest slot at or after: " + slots.ceiling(requested));
        System.out.println("Slot strictly before 1000: " + slots.lower(1000));
        System.out.println("Slot strictly after 1000: " + slots.higher(1000));
    }
}
```

**How to run:** `java MeetingSlotLookup.java`

`floor`/`ceiling` find the nearest bookable slot at or around a requested time in logarithmic time — a natural fit for "here's what the user asked for; here's the closest actual option" scheduling logic.

### Level 2 — Intermediate

```java
import java.util.*;

public class MeetingSlotRanges {
    public static void main(String[] args) {
        NavigableSet<Integer> slots = new TreeSet<>(Set.of(900, 930, 1000, 1030, 1100, 1130, 1200));

        System.out.println("Morning slots (before noon, exclusive of 1200): " + slots.headSet(1200, false));
        System.out.println("Afternoon-and-noon slots (1200 inclusive): " + slots.tailSet(1200, true));
        System.out.println("Mid-morning slots [1000, 1100]: " + slots.subSet(1000, true, 1100, true));
    }
}
```

**How to run:** `java MeetingSlotRanges.java`

`headSet`/`tailSet`/`subSet` return live sorted views of a range, with the same explicit inclusive/exclusive boundary flags as `NavigableMap` — useful for reporting "everything before/after/between" without manually filtering the whole set.

### Level 3 — Advanced

```java
import java.util.*;

public class MeetingSlotBooking {
    public static void main(String[] args) {
        NavigableSet<Integer> slots = new TreeSet<>(Set.of(900, 930, 1000, 1030, 1100));

        System.out.println("Available slots, latest first:");
        for (int slot : slots.descendingSet()) {
            System.out.println("  " + slot);
        }

        System.out.println("\nBooking the two latest available slots:");
        Integer firstBooked = slots.pollLast();  // removes and returns the LATEST slot
        Integer secondBooked = slots.pollLast();
        System.out.println("Booked: " + firstBooked + " and " + secondBooked);

        System.out.println("Remaining available slots: " + slots);
    }
}
```

**How to run:** `java MeetingSlotBooking.java`

`descendingSet()` gives a reverse-order view (latest slot first) without copying anything, and `pollLast()` atomically removes and returns the single latest remaining slot — calling it twice in a row books the two latest slots one at a time, correctly reflecting each removal before the next call.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `slots` is a `TreeSet<Integer>` containing `{900, 930, 1000, 1030, 1100}` — `TreeSet` keeps these sorted internally regardless of the `Set.of(...)` construction order.

`slots.descendingSet()` returns a view iterating in reverse sorted order — backed by the same tree, just traversed backward. The `for` loop prints `1100`, then `1030`, then `1000`, then `930`, then `900`.

`slots.pollLast()` is then called on the **original** set. This finds the largest element (`1100`), removes it from `slots`, and returns it — `firstBooked` becomes `1100`. Since `1100` was just removed, `slots` is now `{900, 930, 1000, 1030}`.

`slots.pollLast()` is called again: now the largest remaining element is `1030`, which is removed and returned — `secondBooked` becomes `1030`. `slots` is now `{900, 930, 1000}`.

`"Booked: " + firstBooked + " and " + secondBooked` prints `"Booked: 1100 and 1030"` — note this correctly reflects that the *second* `pollLast()` call operated on the set *after* the first one's removal had already taken effect, not on some cached snapshot from before either removal.

Finally, `slots` (now containing only the three unbooked slots) is printed as the remaining availability.

Expected output:
```
Available slots, latest first:
  1100
  1030
  1000
  930
  900

Booking the two latest available slots:
Booked: 1100 and 1030
Remaining available slots: [900, 930, 1000]
```

## 7. Gotchas & takeaways

> Calling `pollLast()` (or `pollFirst()`) **twice in a row** operates on the set's state *after* the first call's removal — this is exactly what you want for "book the two latest slots one at a time," but it's easy to mistakenly assume both calls see the same "before" snapshot. Each poll call sees the set as it currently stands, including any changes made by earlier polls in the same sequence.

- `floor`/`ceiling` include an exact match at the target value; `lower`/`higher` always look strictly past it — identical semantics to `NavigableMap`'s key-based equivalents.
- `headSet`/`tailSet`/`subSet` return live views with explicit inclusive/exclusive boundary flags, just like `NavigableMap`'s range views — always specify boundaries deliberately.
- `descendingSet()`/`descendingIterator()` give reverse-order access without copying or re-sorting, since they're backed by the same underlying tree traversed in the opposite direction.
- `pollFirst()`/`pollLast()` atomically remove and return the smallest/largest element — ideal for "take the next item in priority order out of the pool," such as booking the latest available slot.
- `NavigableSet` and `NavigableMap` share the same navigational vocabulary (`floor`, `ceiling`, `lower`, `higher`, range views, descending views) — learning one makes the other immediately familiar.
