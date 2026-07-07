---
card: java
gi: 373
slug: enummap
title: EnumMap
---

## 1. What it is

`EnumMap` is a specialised `Map` implementation, in `java.util`, whose keys must all be constants of a single enum type. Like [[enumset]], it exploits the fact that an enum has a small, fixed, known-in-advance set of possible values: internally, it stores its values in a plain array indexed by each key's `ordinal()`, instead of the hash table a `HashMap` would use. You create one with `new EnumMap<>(SomeEnum.class)`, passing the enum's `Class` object so the map knows which enum type — and therefore which array size — to use.

## 2. Why & when

A `HashMap<Day, String>` works, but every `put` and `get` computes a hash code, potentially walks a collision chain, and iterates in an unspecified order. `EnumMap` sidesteps all of that: since the complete set of possible keys is known up front (the enum's constants), it just allocates one array slot per constant and indexes directly by ordinal — `put` and `get` become simple array writes and reads, and iteration always proceeds in the enum's natural declaration order.

Reach for `EnumMap` whenever you need to associate data with each (or some) constant of an enum — mapping a `DayOfWeek` to a schedule, a `LogLevel` to a colour, a `Status` to a handler function. It's a strict upgrade over `HashMap<SomeEnum, V>` in the common case: faster, more memory-efficient, and predictably ordered, with no code-level cost beyond passing the enum's `Class` to the constructor.

## 3. Core concept

```java
import java.util.EnumMap;
import java.util.Map;

public class EnumMapDemo {
    enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

    public static void main(String[] args) {
        Map<Day, String> schedule = new EnumMap<>(Day.class); // must supply the enum's Class
        schedule.put(Day.MONDAY, "Team standup");
        schedule.put(Day.WEDNESDAY, "Code review");
        schedule.put(Day.FRIDAY, "Retro");

        for (Map.Entry<Day, String> entry : schedule.entrySet()) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }
    }
}
```

**How to run:** `java EnumMapDemo.java`

`new EnumMap<>(Day.class)` creates a map sized for exactly `Day`'s seven constants. Even though entries were inserted out of declaration order (`MONDAY`, `WEDNESDAY`, `FRIDAY` — skipping `TUESDAY`, `THURSDAY`), iterating `entrySet()` always visits them in declaration order: `MONDAY`, then `WEDNESDAY`, then `FRIDAY`.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="EnumMap stores values in an array indexed by key ordinal, so each key maps directly to a fixed array slot instead of a hash bucket">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="11">Internal array, indexed by ordinal (0..6):</text>

  <rect x="30" y="45" width="80" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="70" y="62" fill="#6db33f" font-size="9" text-anchor="middle">MON [0]</text>
  <text x="70" y="76" fill="#8b949e" font-size="8" text-anchor="middle">"standup"</text>

  <rect x="120" y="45" width="80" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="62" fill="#8b949e" font-size="9" text-anchor="middle">TUE [1]</text>
  <text x="160" y="76" fill="#8b949e" font-size="8" text-anchor="middle">(empty)</text>

  <rect x="210" y="45" width="80" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="250" y="62" fill="#6db33f" font-size="9" text-anchor="middle">WED [2]</text>
  <text x="250" y="76" fill="#8b949e" font-size="8" text-anchor="middle">"review"</text>

  <rect x="300" y="45" width="80" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="340" y="62" fill="#8b949e" font-size="9" text-anchor="middle">THU [3]</text>
  <text x="340" y="76" fill="#8b949e" font-size="8" text-anchor="middle">(empty)</text>

  <rect x="390" y="45" width="80" height="40" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="430" y="62" fill="#6db33f" font-size="9" text-anchor="middle">FRI [4]</text>
  <text x="430" y="76" fill="#8b949e" font-size="8" text-anchor="middle">"retro"</text>

  <text x="20" y="120" fill="#8b949e" font-size="10">put(MONDAY, ...) writes directly to array index 0 -- no hashing, no bucket search.</text>
  <text x="20" y="142" fill="#8b949e" font-size="10">Iteration always walks the array front-to-back, so entries appear in declaration order.</text>
</svg>

## 5. Runnable example

Scenario: mapping HTTP status codes to handler descriptions, evolved from a `HashMap`-based version, through the `EnumMap` equivalent, to a version that uses `EnumMap`'s ordered iteration and `getOrDefault` to build a complete, gap-filled report.

### Level 1 — Basic

```java
import java.util.HashMap;
import java.util.Map;

public class HandlersHashMap {
    enum Status { OK, NOT_FOUND, SERVER_ERROR }

    public static void main(String[] args) {
        Map<Status, String> handlers = new HashMap<>();
        handlers.put(Status.OK, "serveContent()");
        handlers.put(Status.SERVER_ERROR, "logAndAlert()");

        System.out.println(handlers.get(Status.OK));
        System.out.println(handlers.get(Status.NOT_FOUND)); // not present -- returns null
    }
}
```

**How to run:** `java HandlersHashMap.java`

Works, but `HashMap<Status, String>`'s iteration order is unspecified, and its internal hashing machinery is unnecessary overhead when the entire key universe is only three known constants.

### Level 2 — Intermediate

```java
import java.util.EnumMap;
import java.util.Map;

public class HandlersEnumMap {
    enum Status { OK, NOT_FOUND, SERVER_ERROR }

    public static void main(String[] args) {
        Map<Status, String> handlers = new EnumMap<>(Status.class);
        handlers.put(Status.OK, "serveContent()");
        handlers.put(Status.SERVER_ERROR, "logAndAlert()");

        System.out.println(handlers.get(Status.OK));
        System.out.println(handlers.get(Status.NOT_FOUND)); // still absent -- still null
    }
}
```

**How to run:** `java HandlersEnumMap.java`

Identical behaviour and API to the `HashMap` version — `EnumMap` is a drop-in replacement wherever the key type is a specific enum — but internally backed by an array indexed on ordinal, faster and using less memory for this exact shape of data.

### Level 3 — Advanced

```java
import java.util.EnumMap;
import java.util.Map;

public class HandlersReport {
    enum Status { OK, NOT_FOUND, SERVER_ERROR }

    public static void main(String[] args) {
        EnumMap<Status, String> handlers = new EnumMap<>(Status.class);
        handlers.put(Status.OK, "serveContent()");
        handlers.put(Status.SERVER_ERROR, "logAndAlert()");
        // NOT_FOUND deliberately left unmapped -- simulating a missing handler

        for (Status status : Status.values()) { // walk EVERY constant, not just mapped ones
            String handler = handlers.getOrDefault(status, "<no handler registered>");
            System.out.println(status + " -> " + handler);
        }

        System.out.println("Fully covered? " + handlers.keySet().containsAll(
                EnumMap.class.isInstance(handlers) ? java.util.EnumSet.allOf(Status.class) : null));
    }
}
```

**How to run:** `java HandlersReport.java`

Looping over `Status.values()` — every possible constant — rather than `handlers.entrySet()` — only the ones actually mapped — turns this into a completeness report: it surfaces `NOT_FOUND` explicitly as `<no handler registered>` instead of silently skipping it, which is exactly the kind of gap-detection you want when an `EnumMap` is meant to cover every constant of its key type.

## 6. Walkthrough

Execution starts in `main`. `handlers` is created as an empty `EnumMap<Status, String>`. Two `put` calls populate array slots for `OK` (ordinal 0) and `SERVER_ERROR` (ordinal 2); the slot for `NOT_FOUND` (ordinal 1) is left empty.

The loop `for (Status status : Status.values())` iterates all three constants in declaration order: `OK`, `NOT_FOUND`, `SERVER_ERROR` — this comes from the enum itself, not from `handlers`, so every constant is visited regardless of whether it has a mapped value.

For `OK`: `handlers.getOrDefault(OK, "<no handler registered>")` finds a value at that slot (`"serveContent()"`) and returns it directly, ignoring the default. This prints `OK -> serveContent()`.

For `NOT_FOUND`: `getOrDefault` finds the slot empty (no value was ever `put` there) and returns the supplied default string instead. This prints `NOT_FOUND -> <no handler registered>` — surfacing the gap explicitly, rather than the loop silently skipping this constant the way iterating `handlers.entrySet()` alone would have.

For `SERVER_ERROR`: `getOrDefault` finds `"logAndAlert()"` at that slot and returns it, printing `SERVER_ERROR -> logAndAlert()`.

Expected output:
```
OK -> serveContent()
NOT_FOUND -> <no handler registered>
SERVER_ERROR -> logAndAlert()
Fully covered? false
```

(The final `containsAll` check compares only the two actually-mapped keys against all three real constants, correctly reporting `false` since `NOT_FOUND` was never mapped.)

## 7. Gotchas & takeaways

> `EnumMap`'s constructor always requires the enum's `Class` object (`new EnumMap<>(Status.class)`), even though Java usually infers generic type parameters automatically — this is because the map needs to know the concrete enum type at construction time to size its internal array, information erasure would otherwise discard.

- `EnumMap` keys must all belong to one specific enum type; you cannot mix keys from two different enums in the same map.
- Internally, values are stored in an array indexed by key `ordinal()`, making `put`/`get` fast, direct array operations instead of hash lookups.
- Iteration order always follows the enum's declaration order, regardless of insertion order — a guarantee `HashMap` does not provide.
- Looping over `SomeEnum.values()` and using `getOrDefault` on an `EnumMap` is a common, idiomatic pattern for surfacing every constant, including ones that were never explicitly mapped.
- Prefer `EnumMap<SomeEnum, V>` over `HashMap<SomeEnum, V>` by default — it's a near-drop-in replacement with better performance and predictable ordering, at the minor cost of passing the enum's `Class` to the constructor.
