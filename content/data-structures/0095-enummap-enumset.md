---
card: data-structures
gi: 95
slug: enummap-enumset
title: EnumMap & EnumSet
---

## 1. What it is

`EnumMap` and `EnumSet` are specialized `Map` and `Set` implementations built specifically for `enum` keys/elements. Instead of hashing, they exploit the fact that every enum constant has a fixed, known **ordinal** (its position in the declaration, `0, 1, 2, ...`) to store entries directly in a compact array indexed by that ordinal.

## 2. Why & when

Use `EnumMap`/`EnumSet` whenever the keys or elements are an `enum` type — they are faster and use far less memory than `HashMap`/`HashSet` for this exact case, because there is no hash computation, no bucket array, and no collision handling needed at all. They also iterate in the enum's natural declaration order automatically, which is usually the order you want anyway (like `MONDAY` before `TUESDAY`).

## 3. Core concept

**What backs each.** `EnumMap` is backed by a plain array, sized to the number of constants in the enum type, indexed directly by each key's `ordinal()`. `EnumSet` is backed by a bitmask (a single `long` for enums with 64 or fewer constants, or an array of `long`s for larger ones) — each bit represents whether that ordinal's constant is present.

**Why this is faster than hashing.** Since an enum constant's ordinal is already a small, dense, known integer, there is nothing to hash — `array[key.ordinal()]` is a direct O(1) array access, with none of `HashMap`'s hash-computation or collision-resolution overhead. A bitmask-backed `EnumSet` makes set operations (union, intersection) extremely fast too, since they reduce to a handful of bitwise operations (`OR`, `AND`) on the underlying `long`s.

**Iteration order.** Both iterate in the enum's natural (declaration) order, always — this is a guarantee, not an incidental detail, unlike `HashMap`'s unspecified order. This is usually exactly the order you want for a fixed, meaningful set of categories (days of the week, states of a state machine, HTTP methods).

**When to choose them.** Choose `EnumMap`/`EnumSet` whenever the key/element type is an `enum` — there is essentially no downside versus `HashMap`/`HashSet` for that case, only upside (speed, memory, guaranteed order).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An EnumMap backed by a flat array indexed directly by each enum constant's ordinal, contrasted with a HashMap that would need to hash the same keys">
  <g font-family="sans-serif" font-size="11">
    <text x="20" y="16" fill="#8b949e">enum Day { MONDAY(0), TUESDAY(1), WEDNESDAY(2) }</text>
    <rect x="20" y="30" width="80" height="26" fill="#0d1117" stroke="#f0883e"/><text x="60" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">"open"</text>
    <rect x="100" y="30" width="80" height="26" fill="#0d1117" stroke="#f0883e"/><text x="140" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">"open"</text>
    <rect x="180" y="30" width="80" height="26" fill="#0d1117" stroke="#f0883e"/><text x="220" y="47" fill="#e6edf3" text-anchor="middle" font-size="8">"closed"</text>
    <text x="60" y="70" fill="#8b949e" text-anchor="middle" font-size="8">index 0</text>
    <text x="140" y="70" fill="#8b949e" text-anchor="middle" font-size="8">index 1</text>
    <text x="220" y="70" fill="#8b949e" text-anchor="middle" font-size="8">index 2</text>
    <text x="140" y="100" fill="#79c0ff" text-anchor="middle" font-size="9">array[day.ordinal()] -- direct access, no hashing at all</text>
  </g>
</svg>

Each enum constant's fixed ordinal is used as a direct array index — `EnumMap`'s entire lookup is one array access, with no hashing step.

## 5. Runnable example

```java
// EnumMapEnumSetDemo.java
import java.util.EnumMap;
import java.util.EnumSet;
import java.util.Map;
import java.util.Set;

public class EnumMapEnumSetDemo {

    enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

    // Basic: EnumMap keyed by Day, iterating automatically in declaration order.
    static void basicLevel() {
        Map<Day, String> schedule = new EnumMap<>(Day.class);
        schedule.put(Day.WEDNESDAY, "team sync");
        schedule.put(Day.MONDAY, "planning");
        schedule.put(Day.FRIDAY, "demo");

        System.out.println("basic: EnumMap iteration order (always declaration order, not insertion order) -> " + schedule);
    }

    // Intermediate: EnumSet for a fixed set of flags, plus fast set operations via bitmask semantics.
    static void intermediateLevel() {
        Set<Day> weekend = EnumSet.of(Day.SATURDAY, Day.SUNDAY);
        Set<Day> weekdays = EnumSet.complementOf((EnumSet<Day>) weekend); // everything NOT in weekend

        System.out.println("intermediate: weekend -> " + weekend);
        System.out.println("intermediate: weekdays (complement) -> " + weekdays);

        Set<Day> meetingDays = EnumSet.of(Day.MONDAY, Day.WEDNESDAY, Day.FRIDAY);
        Set<Day> overlap = EnumSet.copyOf(meetingDays);
        overlap.retainAll(weekdays); // intersection -- fast bitwise AND under the hood
        System.out.println("intermediate: meeting days that are also weekdays -> " + overlap);
    }

    // Advanced: a realistic task -- a simple state machine using EnumMap<State, EnumSet<State>> for allowed transitions.
    enum OrderState { PENDING, PAID, SHIPPED, DELIVERED, CANCELLED }

    static Map<OrderState, Set<OrderState>> buildTransitionTable() {
        Map<OrderState, Set<OrderState>> transitions = new EnumMap<>(OrderState.class);
        transitions.put(OrderState.PENDING, EnumSet.of(OrderState.PAID, OrderState.CANCELLED));
        transitions.put(OrderState.PAID, EnumSet.of(OrderState.SHIPPED, OrderState.CANCELLED));
        transitions.put(OrderState.SHIPPED, EnumSet.of(OrderState.DELIVERED));
        transitions.put(OrderState.DELIVERED, EnumSet.noneOf(OrderState.class)); // terminal state
        transitions.put(OrderState.CANCELLED, EnumSet.noneOf(OrderState.class)); // terminal state
        return transitions;
    }

    static boolean canTransition(Map<OrderState, Set<OrderState>> table, OrderState from, OrderState to) {
        return table.getOrDefault(from, Set.of()).contains(to);
    }

    static void advancedLevel() {
        Map<OrderState, Set<OrderState>> table = buildTransitionTable();
        System.out.println("advanced: PENDING -> PAID allowed -> " + canTransition(table, OrderState.PENDING, OrderState.PAID));
        System.out.println("advanced: PENDING -> DELIVERED allowed -> " + canTransition(table, OrderState.PENDING, OrderState.DELIVERED));
        System.out.println("advanced: DELIVERED -> anything allowed -> " + canTransition(table, OrderState.DELIVERED, OrderState.CANCELLED));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `EnumMapEnumSetDemo.java`, then run `java EnumMapEnumSetDemo.java`.

## 6. Walkthrough

1. `basicLevel()` inserts entries in the order `WEDNESDAY, MONDAY, FRIDAY`, but printing the map gives `MONDAY, WEDNESDAY, FRIDAY` — declaration order, always, regardless of insertion order. This is `EnumMap`'s array-by-ordinal layout showing through directly.
2. `intermediateLevel()` builds `weekend = {SATURDAY, SUNDAY}`, then `EnumSet.complementOf` computes every constant *not* in that set — internally, a bitwise NOT (then masked to valid ordinals) on the underlying bitmask. `retainAll` (intersection) between `meetingDays` and `weekdays` reduces to a bitwise AND, giving `{MONDAY, WEDNESDAY, FRIDAY}` (none of the meeting days happen to be a weekend day here, so the full set survives).
3. `advancedLevel()` builds a state-transition table using `EnumMap<OrderState, Set<OrderState>>`, where each value is itself an `EnumSet` of allowed next states. `canTransition` is a single array lookup plus a bitmask containment check — `PENDING -> PAID` is allowed (in the set), `PENDING -> DELIVERED` is not, and `DELIVERED` (a terminal state) allows no further transitions at all.

## 7. Gotchas & takeaways

> Gotcha: `EnumMap`/`EnumSet` only work for a single, specific `enum` type per instance — you cannot mix keys from two different enum types in one `EnumMap`, and the constructor requires the enum's `.class` token (`new EnumMap<>(Day.class)`) so it knows how many ordinals to size the backing array for.

- `EnumMap` and `EnumSet` use each constant's fixed `ordinal()` as a direct array/bitmask index — no hashing, no collisions, no wasted buckets.
- They always iterate in the enum's declaration order, which is a guarantee, not an accident.
- Set operations (`retainAll`, `complementOf`, union) reduce to fast bitwise operations on the underlying bitmask.
- Prefer them over `HashMap`/`HashSet` any time the key or element type is an `enum`.
- Related concepts: [HashMap internals (buckets, treeify at 8)](0091-hashmap-internals-buckets-treeify-at-8.md), [HashSet & LinkedHashMap ordering](0092-hashset-linkedhashmap-ordering.md).
