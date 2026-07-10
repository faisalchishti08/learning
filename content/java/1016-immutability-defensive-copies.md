---
card: java
gi: 1016
slug: immutability-defensive-copies
title: Immutability & defensive copies
---

## 1. What it is

An **immutable** object's state can't change after construction — every field is `final`, set once, and never reassigned. But immutability isn't automatic just because a field is `final`: if a `final` field holds a *reference* to a mutable object (a `Date`, a `List`, an array), the referenced object's internal state can still be changed by anyone holding that same reference, even though the field itself never gets reassigned. A **defensive copy** closes this gap: instead of storing (or handing out) the caller's exact mutable object, the class stores (or hands out) its own independent copy, so no outside code can reach in and mutate what the immutable object relies on.

## 2. Why & when

`final` alone guarantees the *reference* can't be reassigned, not that the *object it points to* can't be mutated. A class that stores a `Date` parameter directly in a `final` field, or returns that same `Date` reference from a getter, is only pretending to be immutable — whoever passed in the `Date`, or whoever received it from the getter, can still call `.setTime(...)` on it and silently corrupt the "immutable" object's state from outside. Defensive copying at both the constructor (copy what comes in) and the getter (copy what goes out) is what actually closes this loophole.

Apply defensive copying whenever an immutable class's constructor accepts, or a getter returns, a reference to a genuinely mutable type. Skip it for genuinely immutable types (`String`, boxed primitives, other properly-immutable classes, or unmodifiable collections created via `List.copyOf`) — copying an object that can't be mutated in the first place is pure waste.

## 3. Core concept

```
import java.util.Date;

class Event {
    private final Date start; // final field... but Date itself is MUTABLE

    Event(Date start) {
        this.start = new Date(start.getTime()); // defensive copy IN: don't trust the caller's reference
    }

    Date getStart() {
        return new Date(start.getTime()); // defensive copy OUT: don't hand out the real internal reference
    }
}

Date original = new Date();
Event event = new Event(original);
original.setTime(0); // mutating the CALLER's Date...
System.out.println(event.getStart().equals(original)); // ...doesn't touch event's own copy -- false
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Without defensive copying, Event stores the caller's exact Date reference, so mutating the caller's Date corrupts Event's internal state; with defensive copying, Event holds its own independent copy">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Without defensive copy</text>
  <rect x="40" y="40" width="120" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="100" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">caller's Date</text>
  <rect x="220" y="40" width="120" height="40" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="280" y="65" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Event.start</text>
  <text x="190" y="65" fill="#f0883e" font-size="14" text-anchor="middle" font-family="sans-serif">==</text>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">With defensive copy</text>
  <rect x="400" y="100" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="460" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">caller's Date</text>
  <rect x="560" y="100" width="60" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="590" y="125" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">copy</text>
</svg>

Without a defensive copy, `Event`'s "immutable" state is really just the caller's own mutable object in disguise.

## 5. Runnable example

Scenario: an `Event` class storing a start time, evolving from a fake immutability that leaks mutable state into a properly defensive design that's actually immutable end to end.

### Level 1 — Basic

```java
// File: DefensiveCopyBasic.java
import java.util.Date;

class Event {
    private final Date start; // final reference, but Date is mutable

    Event(Date start) {
        this.start = start; // stores the CALLER's exact reference -- no copy
    }

    Date getStart() {
        return start; // hands out the REAL internal reference -- no copy
    }
}

public class DefensiveCopyBasic {
    public static void main(String[] args) {
        Date original = new Date(1_700_000_000_000L);
        Event event = new Event(original);

        original.setTime(0); // mutating the caller's Date...

        System.out.println("event's start: " + event.getStart().getTime());
    }
}
```

**How to run:** save as `DefensiveCopyBasic.java`, then `javac DefensiveCopyBasic.java && java DefensiveCopyBasic` (JDK 17+).

Expected output:
```
event's start: 0
```

`event`'s "immutable" start time silently changed to `0` — even though `Event` never explicitly mutated anything — because `original` and `event.start` are the exact same `Date` object, and mutating one mutates both.

### Level 2 — Intermediate

```java
// File: DefensiveCopyIntermediate.java
import java.util.Date;

class Event {
    private final Date start;

    Event(Date start) {
        this.start = new Date(start.getTime()); // defensive copy IN
    }

    Date getStart() {
        return start; // still leaking the real reference OUT -- half-fixed
    }
}

public class DefensiveCopyIntermediate {
    public static void main(String[] args) {
        Date original = new Date(1_700_000_000_000L);
        Event event = new Event(original);

        original.setTime(0); // mutating the caller's Date...
        System.out.println("event's start after mutating input: " + event.getStart().getTime());

        event.getStart().setTime(0); // ...but the GETTER's returned reference is still real
        System.out.println("event's start after mutating getter's result: " + event.getStart().getTime());
    }
}
```

**How to run:** save as `DefensiveCopyIntermediate.java`, then `javac DefensiveCopyIntermediate.java && java DefensiveCopyIntermediate` (JDK 17+).

Expected output:
```
event's start after mutating input: 1700000000000
event's start after mutating getter's result: 0
```

The real-world concern added: copying on the way *in* (the constructor) fixed one half of the leak — `original.setTime(0)` no longer affects `event`. But `getStart()` still returns the actual internal `Date` object, so any caller of `getStart()` can mutate `event`'s real internal state through the returned reference.

### Level 3 — Advanced

```java
// File: DefensiveCopyAdvanced.java
import java.util.Date;

class Event {
    private final Date start;
    private final Date end;

    Event(Date start, Date end) {
        if (start.after(end)) {
            throw new IllegalArgumentException("start must be before end");
        }
        // Defensive copies IN, taken AFTER validation but BEFORE storing --
        // validating the caller's original objects, then storing independent copies.
        this.start = new Date(start.getTime());
        this.end = new Date(end.getTime());
    }

    Date getStart() { return new Date(start.getTime()); } // defensive copy OUT
    Date getEnd() { return new Date(end.getTime()); }     // defensive copy OUT

    long durationMillis() { return end.getTime() - start.getTime(); }
}

public class DefensiveCopyAdvanced {
    public static void main(String[] args) {
        Date start = new Date(1_700_000_000_000L);
        Date end = new Date(1_700_003_600_000L); // one hour later
        Event event = new Event(start, end);

        // Attempt to corrupt the event from every angle: mutate the original
        // inputs AND mutate whatever the getters hand back.
        start.setTime(0);
        end.setTime(0);
        event.getStart().setTime(999);
        event.getEnd().setTime(999);

        System.out.println("duration still correct: " + (event.durationMillis() == 3_600_000L));
        System.out.println("start still correct: " + (event.getStart().getTime() == 1_700_000_000_000L));
    }
}
```

**How to run:** save as `DefensiveCopyAdvanced.java`, then `javac DefensiveCopyAdvanced.java && java DefensiveCopyAdvanced` (JDK 17+).

Expected output:
```
duration still correct: true
start still correct: true
```

The production-flavored hard case: `Event` defensively copies on **both** the way in (constructor) and the way out (getters), and validates its invariant (`start` before `end`) using the caller's original objects before making its own independent copies — no combination of mutating the original inputs or mutating the getters' return values can corrupt `event`'s actual internal state.

## 6. Walkthrough

Tracing the sequence of mutation attempts in `DefensiveCopyAdvanced.main`:

1. `new Event(start, end)` runs the constructor: `start.after(end)` checks the caller's original `Date` objects directly, confirming `1_700_000_000_000L` is before `1_700_003_600_000L` — the validation passes.
2. `this.start = new Date(start.getTime())` and `this.end = new Date(end.getTime())` create **brand-new** `Date` objects holding the same millisecond values, but as entirely separate objects from the caller's `start` and `end` variables.
3. `start.setTime(0)` mutates the caller's original `start` variable — but `event`'s internal `this.start` field is a different object entirely (from step 2), so it's completely unaffected. Same for `end.setTime(0)`.
4. `event.getStart().setTime(999)` calls `getStart()`, which returns `new Date(start.getTime())` — a **freshly created** `Date` object, a copy of `event`'s internal `start`. Calling `.setTime(999)` on *that* temporary copy mutates only the temporary object, which is immediately discarded (never stored anywhere) — `event`'s real internal `start` field is untouched. Same for `event.getEnd().setTime(999)`.
5. `event.durationMillis()` computes `end.getTime() - start.getTime()` using `event`'s own internal, never-mutated fields: `1_700_003_600_000L - 1_700_000_000_000L = 3_600_000L`, matching the expected one-hour duration — printed as `"duration still correct: true"`.
6. `event.getStart().getTime()` returns a fresh copy's value, `1_700_000_000_000L`, matching the original construction value exactly — printed as `"start still correct: true"`. Every single attempt to corrupt `event` from outside failed, because none of them ever touched the actual objects `event` relies on internally.

## 7. Gotchas & takeaways

> **Gotcha:** defensive copies must be taken with the actual mutable type's copy constructor or equivalent (`new Date(start.getTime())`), not a shallow reference assignment (`this.start = start`) that only *looks* like a copy. And validation logic that checks an invariant should run against the caller's original objects *before* copying (or against the copies, consistently) — checking one and storing the other can reintroduce a subtle time-of-check-to-time-of-use gap if the caller mutates between the check and the copy on another thread.

- `final` prevents a field's *reference* from being reassigned; it says nothing about whether the object that reference points to can be mutated.
- A defensive copy on the way **in** (constructor) protects against the caller mutating the object after handing it over; a defensive copy on the way **out** (getters) protects against callers mutating the class's internal state through a returned reference.
- Only copy genuinely mutable types — copying an already-immutable object (`String`, `Integer`, an unmodifiable list) wastes time and allocation for no safety benefit.
- Prefer inherently immutable types where possible (`java.time.Instant` instead of `java.util.Date`, `List.copyOf(...)` instead of a raw mutable `List`) — they eliminate the need for defensive copying entirely, since there's nothing to protect against.
- Records automatically apply this discipline for their accessor methods only if you write it yourself in a compact canonical constructor — records do not automatically defensively copy mutable component types, so this remains something to handle explicitly even with records.
- This principle underlies why properly immutable objects are inherently thread-safe: with no mutable state reachable from outside, there's nothing for concurrent threads to race over.
