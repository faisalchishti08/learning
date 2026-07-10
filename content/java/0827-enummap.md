---
card: java
gi: 827
slug: enummap
title: EnumMap
---

## 1. What it is

`EnumMap<K extends Enum<K>, V>` is a specialized `Map` implementation whose keys must all belong to a single enum type. Internally, it's backed by a plain **array** indexed directly by each key's ordinal position (`Enum.ordinal()`) — not a hash table at all. This makes every operation (`put`, `get`, `containsKey`) a direct array-index access, faster and more memory-compact than an equivalent `HashMap<SomeEnum, V>`. Like [`EnumSet`](0820-enumset.md), it's created with a constructor that takes the enum's `Class` object, and it always iterates in the enum constants' natural declaration order, automatically — no comparator needed.

## 2. Why & when

Whenever a map's key type is a fixed, known-in-advance enum — a day-of-week schedule, a state-machine's per-state configuration, an HTTP-method-to-handler table — `EnumMap` is a strict upgrade over `HashMap<SomeEnum, V>` for the same reason `EnumSet` improves on `HashSet<SomeEnum>`: same `Map` interface and semantics, but backed by direct array indexing instead of hashing, so there's no hash computation, no bucket traversal, and no risk of collision-driven performance degradation at all. It also guarantees enum-declaration-order iteration automatically, which is exactly the order most "per-enum-value configuration" use cases want to display or process in anyway. Reach for `EnumMap<E, V>` by default whenever `E` is an enum — there's essentially no reason to prefer `HashMap<E, V>` for this specific case.

## 3. Core concept

```java
enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

EnumMap<Day, String> schedule = new EnumMap<>(Day.class);
schedule.put(Day.MONDAY, "Team standup");
schedule.put(Day.WEDNESDAY, "Sprint review");
schedule.put(Day.FRIDAY, "Retro");

schedule.get(Day.WEDNESDAY); // "Sprint review" -- a direct array lookup at Day.WEDNESDAY.ordinal()

for (Map.Entry<Day, String> entry : schedule.entrySet()) {
    System.out.println(entry.getKey() + ": " + entry.getValue());
}
// always prints in MONDAY, TUESDAY, ..., SUNDAY order -- the enum's declaration order --
// regardless of the order entries were inserted
```

`schedule.get(Day.WEDNESDAY)` computes `Day.WEDNESDAY.ordinal()` (which is `2`) and reads that array slot directly — no hashing, no bucket search, just an index computation and an array read.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An EnumMap is backed by an array indexed directly by each enum constant's ordinal position">
  <g font-family="sans-serif">
    <text x="320" y="25" fill="#8b949e" font-size="11" text-anchor="middle">EnumMap&lt;Day, String&gt; internal array, indexed by ordinal()</text>

    <rect x="40" y="45" width="80" height="45" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="80" y="63" fill="#8b949e" font-size="9" text-anchor="middle">[0] MON</text>
    <text x="80" y="80" fill="#e6edf3" font-size="9" text-anchor="middle">standup</text>

    <rect x="120" y="45" width="80" height="45" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
    <text x="160" y="63" fill="#8b949e" font-size="9" text-anchor="middle">[1] TUE</text>
    <text x="160" y="80" fill="#8b949e" font-size="9" text-anchor="middle">(none)</text>

    <rect x="200" y="45" width="80" height="45" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="240" y="63" fill="#8b949e" font-size="9" text-anchor="middle">[2] WED</text>
    <text x="240" y="80" fill="#e6edf3" font-size="9" text-anchor="middle">review</text>

    <rect x="280" y="45" width="80" height="45" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
    <text x="320" y="63" fill="#8b949e" font-size="9" text-anchor="middle">[3] THU</text>
    <text x="320" y="80" fill="#8b949e" font-size="9" text-anchor="middle">(none)</text>

    <rect x="360" y="45" width="80" height="45" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
    <text x="400" y="63" fill="#8b949e" font-size="9" text-anchor="middle">[4] FRI</text>
    <text x="400" y="80" fill="#e6edf3" font-size="9" text-anchor="middle">retro</text>
  </g>
  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">get(WEDNESDAY) computes ordinal() = 2 and reads that array slot directly — no hashing needed</text>
</svg>

*Each enum constant's ordinal is a direct array index — `EnumMap` never hashes or traverses buckets.*

## 5. Runnable example

Scenario: a weekly team schedule keyed by day of week, growing from basic per-day lookup to a state-machine-style transition table for an order-processing workflow, to a compact configuration table demonstrating the performance and ordering guarantees together.

### Level 1 — Basic

```java
import java.util.*;

public class ScheduleBasic {
    enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

    public static void main(String[] args) {
        EnumMap<Day, String> schedule = new EnumMap<>(Day.class);
        schedule.put(Day.FRIDAY, "Retro");     // inserted out of week order
        schedule.put(Day.MONDAY, "Standup");
        schedule.put(Day.WEDNESDAY, "Sprint review");

        for (Map.Entry<Day, String> entry : schedule.entrySet()) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }
    }
}
```

**How to run:** `java ScheduleBasic.java` (JDK 17+).

Expected output:
```
MONDAY: Standup
WEDNESDAY: Sprint review
FRIDAY: Retro
```

Even though `"Retro"` (Friday) was inserted first, iteration always follows the enum's declaration order — Monday, then Wednesday, then Friday — never the insertion order.

### Level 2 — Intermediate

```java
import java.util.*;
import java.util.function.*;

public class OrderStateTransitions {
    enum OrderState { PLACED, PAID, SHIPPED, DELIVERED, CANCELLED }

    public static void main(String[] args) {
        // Each state maps to the set of states it can legally transition to.
        EnumMap<OrderState, EnumSet<OrderState>> transitions = new EnumMap<>(OrderState.class);
        transitions.put(OrderState.PLACED, EnumSet.of(OrderState.PAID, OrderState.CANCELLED));
        transitions.put(OrderState.PAID, EnumSet.of(OrderState.SHIPPED, OrderState.CANCELLED));
        transitions.put(OrderState.SHIPPED, EnumSet.of(OrderState.DELIVERED));
        transitions.put(OrderState.DELIVERED, EnumSet.noneOf(OrderState.class)); // terminal state
        transitions.put(OrderState.CANCELLED, EnumSet.noneOf(OrderState.class)); // terminal state

        BiPredicate<OrderState, OrderState> canTransition =
            (from, to) -> transitions.getOrDefault(from, EnumSet.noneOf(OrderState.class)).contains(to);

        System.out.println("PLACED -> PAID allowed? " + canTransition.test(OrderState.PLACED, OrderState.PAID));
        System.out.println("PLACED -> DELIVERED allowed? " + canTransition.test(OrderState.PLACED, OrderState.DELIVERED));
        System.out.println("DELIVERED -> CANCELLED allowed? " + canTransition.test(OrderState.DELIVERED, OrderState.CANCELLED));
    }
}
```

**How to run:** `java OrderStateTransitions.java`.

Expected output:
```
PLACED -> PAID allowed? true
PLACED -> DELIVERED allowed? false
DELIVERED -> CANCELLED allowed? false
```

The real-world concern added: pairing `EnumMap` with [`EnumSet`](0820-enumset.md) values to build a compact, fast state-machine transition table — each state's valid next-states are looked up via one array index (`EnumMap`) into a bitmask membership test (`EnumSet`), avoiding hash computation at every layer of the check.

### Level 3 — Advanced

```java
import java.util.*;

public class HttpMethodDispatchTable {
    enum HttpMethod { GET, POST, PUT, PATCH, DELETE }

    interface Handler { String handle(String path); }

    public static void main(String[] args) {
        EnumMap<HttpMethod, Handler> dispatchTable = new EnumMap<>(HttpMethod.class);
        dispatchTable.put(HttpMethod.GET, path -> "reading " + path);
        dispatchTable.put(HttpMethod.POST, path -> "creating at " + path);
        dispatchTable.put(HttpMethod.DELETE, path -> "removing " + path);
        // PUT and PATCH deliberately left unregistered, to demonstrate the missing-handler case.

        for (HttpMethod method : HttpMethod.values()) {
            Handler handler = dispatchTable.get(method);
            String result = (handler != null) ? handler.handle("/users/42") : "405 Method Not Allowed";
            System.out.println(method + " /users/42 -> " + result);
        }
    }
}
```

**How to run:** `java HttpMethodDispatchTable.java`.

Expected output:
```
GET /users/42 -> reading /users/42
POST /users/42 -> creating at /users/42
PUT /users/42 -> 405 Method Not Allowed
PATCH /users/42 -> 405 Method Not Allowed
DELETE /users/42 -> removing /users/42
```

This adds the production-flavored hard case: a genuine dispatch table mapping each `HttpMethod` enum value to a handler function, iterated in declaration order via `HttpMethod.values()`, with a graceful fallback (`405 Method Not Allowed`) for methods that were never registered — `dispatchTable.get(method)` returns `null` for `PUT`/`PATCH` exactly like a `HashMap` would for a missing key, since `EnumMap` still fully honors the `Map` contract despite its specialized array-backed internals.

## 6. Walkthrough

Tracing `HttpMethodDispatchTable.main`:

1. `dispatchTable` is populated with handlers for `GET`, `POST`, and `DELETE` only — each `put` call computes the enum constant's ordinal (`GET.ordinal()` = 0, `POST.ordinal()` = 1, `DELETE.ordinal()` = 4) and stores the handler directly at that array index.
2. `HttpMethod.values()` returns all five constants in declaration order: `GET, POST, PUT, PATCH, DELETE`.
3. The `for` loop iterates that array in order, calling `dispatchTable.get(method)` for each — a direct array read at the method's ordinal index.
4. For `GET`, `POST`, and `DELETE`, this returns the registered lambda; calling `handler.handle("/users/42")` invokes it, producing the method-specific message.
5. For `PUT` and `PATCH`, the corresponding array slots were never written to, so `get` returns `null` — the ternary expression detects this and substitutes the `"405 Method Not Allowed"` fallback string instead of attempting to call a handler that doesn't exist, avoiding a `NullPointerException`.
6. All five results print in the loop's iteration order, which — because it's driven by `HttpMethod.values()` rather than the dispatch table's own iteration — matches the enum's declaration order regardless of which methods actually have registered handlers.

## 7. Gotchas & takeaways

> **Gotcha:** `EnumMap`'s array-backed storage is sized to the enum type's **total number of constants**, regardless of how many entries are actually populated — a `EnumMap<HttpMethod, Handler>` always allocates space for all five `HttpMethod` values internally, even if only two are ever `put`. This is rarely a practical concern (enum types are typically small), but it means `EnumMap`'s memory footprint scales with the enum's *size*, not the map's *entry count* — the opposite of `HashMap`'s bucket-array growth behavior.

- `EnumMap<K, V>` stores entries in an array indexed by each key's `ordinal()`, giving faster, more memory-compact operations than `HashMap<K, V>` for enum keys.
- Iteration always follows the enum's declaration order automatically — no comparator or explicit ordering needed.
- It fully implements the standard `Map` contract (`get` on a missing key returns `null`, `containsKey`, `entrySet`, etc.) despite its specialized internal representation.
- Pairing `EnumMap` with [`EnumSet`](0820-enumset.md) values is a natural, efficient way to express per-enum-value configuration or transition tables.
- Reach for `EnumMap<E, V>` by default whenever `E` is an enum type and a `Map<E, V>` is needed — there's essentially no downside relative to `HashMap<E, V>` for this specific case.
