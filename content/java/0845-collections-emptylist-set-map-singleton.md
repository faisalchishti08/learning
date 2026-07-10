---
card: java
gi: 845
slug: collections-emptylist-set-map-singleton
title: Collections.emptyList/Set/Map & singleton*
---

## 1. What it is

`Collections.emptyList()`, `emptySet()`, and `emptyMap()` return an **immutable, shared singleton instance** representing a permanently empty collection of the requested type — calling `Collections.emptyList()` a thousand times returns the exact same object reference every single time, with zero allocation cost after the very first call. `Collections.singletonList(value)`, `singleton(value)`, and `singletonMap(key, value)` similarly return an immutable collection holding exactly one element, optimized specifically for that one-element case — smaller and faster than constructing a full general-purpose collection just to hold a single value.

## 2. Why & when

Returning `null` from a method that conceptually "returns a collection" forces every caller to null-check before iterating or calling any method on the result — a common source of `NullPointerException` when a caller forgets. Returning `Collections.emptyList()` instead gives callers a perfectly safe, iterable, zero-element collection to work with directly, no null-check required, and because it's a cached singleton, there's no meaningful cost to returning it every time instead of `null`. `Collections.singletonX(...)` methods matter for the specific, surprisingly common case of "exactly one value, wrapped as a collection" — passing a single value to an API expecting a `Collection`, or returning "just this one match" from a lookup — where constructing a full `ArrayList`/`HashSet` would be needlessly heavyweight for holding just one element.

## 3. Core concept

```java
// Instead of returning null for "no results", return the shared empty singleton:
List<String> noResults = Collections.emptyList();
System.out.println(noResults.size()); // 0 -- safe to call directly, no null-check needed

// Confirm it really is a cached, shared singleton -- not a fresh allocation each time:
System.out.println(Collections.emptyList() == Collections.emptyList()); // true

// A single value, wrapped as an immutable one-element collection:
List<String> justOne = Collections.singletonList("only-value");
Map<String, Integer> oneEntry = Collections.singletonMap("key", 42);

try {
    justOne.add("another"); // throws -- singletonList is immutable, just like emptyList
} catch (UnsupportedOperationException e) {
    System.out.println("singleton collections are immutable too");
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Collections.emptyList always returns the same cached singleton object; Collections.singletonList creates a lightweight, immutable one-element wrapper instead of a full general-purpose list">
  <rect x="40" y="30" width="260" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Collections.emptyList()</text>
  <text x="170" y="72" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">same cached instance every call</text>

  <rect x="340" y="30" width="260" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="470" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Collections.singletonList(x)</text>
  <text x="470" y="72" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">lightweight one-element wrapper</text>

  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Both avoid returning null and avoid the overhead of a general-purpose collection for these two common special cases</text>
</svg>

*Two targeted, immutable shortcuts: a shared empty singleton, and a lightweight one-element wrapper.*

## 5. Runnable example

Scenario: a lookup service returning zero, one, or many results, growing from replacing null returns with `emptyList`, to using `singletonList`/`singletonMap` for the exactly-one-result case, to confirming the singleton-sharing behavior actually avoids allocation.

### Level 1 — Basic

```java
import java.util.*;

public class LookupServiceBasic {
    static Map<String, String> database = Map.of("alice", "Engineering", "bob", "Sales");

    static List<String> findDepartment(String name) {
        String department = database.get(name);
        if (department == null) {
            return Collections.emptyList(); // instead of returning null
        }
        return Collections.singletonList(department);
    }

    public static void main(String[] args) {
        List<String> aliceResult = findDepartment("alice");
        List<String> unknownResult = findDepartment("zack");

        System.out.println("alice's department(s): " + aliceResult);
        System.out.println("zack's department(s): " + unknownResult);
        System.out.println("safe to check size directly, no null-check needed: " + unknownResult.size());
    }
}
```

**How to run:** `java LookupServiceBasic.java` (JDK 17+).

Expected output:
```
alice's department(s): [Engineering]
zack's department(s): []
safe to check size directly, no null-check needed: 0
```

`findDepartment("zack")` returns an empty (but never `null`) list — callers can safely call `.size()`, iterate with a for-each loop, or call `.isEmpty()` without ever needing a preceding null-check.

### Level 2 — Intermediate

```java
import java.util.*;

public class SingletonImmutability {
    public static void main(String[] args) {
        List<String> singleValue = Collections.singletonList("only-value");
        Map<String, Integer> singleEntry = Collections.singletonMap("key", 42);
        Set<String> singleSetElement = Collections.singleton("unique-item");

        System.out.println("singleton list: " + singleValue);
        System.out.println("singleton map: " + singleEntry);
        System.out.println("singleton set: " + singleSetElement);

        try {
            singleValue.add("second-value");
        } catch (UnsupportedOperationException e) {
            System.out.println("caught: singletonList rejects mutation, just like emptyList");
        }

        try {
            singleEntry.put("anotherKey", 99);
        } catch (UnsupportedOperationException e) {
            System.out.println("caught: singletonMap rejects mutation too");
        }
    }
}
```

**How to run:** `java SingletonImmutability.java`.

Expected output:
```
singleton list: [only-value]
singleton map: {key=42}
singleton set: [unique-item]
caught: singletonList rejects mutation, just like emptyList
caught: singletonMap rejects mutation too
```

The real-world concern added: confirming that `singletonList`/`singletonMap`/`singleton` are **immutable**, exactly like the `emptyX` family — they're not meant as a "starter" collection to grow later, only as a fixed, one-element (or one-entry) wrapper for exactly the value(s) supplied at construction.

### Level 3 — Advanced

```java
import java.util.*;

public class SingletonSharingProof {
    public static void main(String[] args) {
        // Prove emptyList() truly returns the SAME cached object every time -- zero allocation cost.
        List<String> empty1 = Collections.emptyList();
        List<String> empty2 = Collections.emptyList();
        System.out.println("emptyList() returns the identical object each call: " + (empty1 == empty2));

        // Same for emptySet() and emptyMap():
        System.out.println("emptySet() identical instances: " + (Collections.emptySet() == Collections.emptySet()));
        System.out.println("emptyMap() identical instances: " + (Collections.emptyMap() == Collections.emptyMap()));

        // Contrast: singletonList(x) is NOT a shared singleton per value -- each call creates a
        // NEW lightweight wrapper object, since it needs to hold a DIFFERENT specific value each time.
        List<String> single1 = Collections.singletonList("same-value");
        List<String> single2 = Collections.singletonList("same-value");
        System.out.println("singletonList(\"same-value\") returns identical objects: " + (single1 == single2));
        System.out.println("but they ARE equal by value: " + single1.equals(single2));
    }
}
```

**How to run:** `java SingletonSharingProof.java`.

Expected output:
```
emptyList() returns the identical object each call: true
emptySet() identical instances: true
emptyMap() identical instances: true
singletonList("same-value") returns identical objects: false
but they ARE equal by value: true
```

This adds the production-flavored hard case: distinguishing what's actually shared from what merely looks similar. `emptyList()`/`emptySet()`/`emptyMap()` genuinely return the **same cached object reference** every time (there's only ever one way to be empty, so one shared instance suffices for every caller), while `singletonList(value)` must construct a **new** wrapper object per call, since each call could be wrapping a different value — the "lightweight" optimization here is in the wrapper's small, specialized implementation (compared to a full `ArrayList`), not in object sharing across calls the way the empty-collection methods achieve.

## 6. Walkthrough

Tracing `SingletonSharingProof.main`:

1. `empty1 = Collections.emptyList()` and `empty2 = Collections.emptyList()` are two separate calls. Internally, `Collections.emptyList()` is implemented to simply return a reference to one `static final` empty list instance the `Collections` class holds — there's no per-call construction at all, so `empty1` and `empty2` end up referencing the exact same object, and `==` (reference equality) correctly reports `true`.
2. The same holds for `emptySet()` and `emptyMap()` — each is backed by its own single shared static instance, since "the empty set" and "the empty map" are each conceptually unique, requiring no per-call variation.
3. `single1 = Collections.singletonList("same-value")` and `single2 = Collections.singletonList("same-value")` are two separate calls, each constructing a **new** lightweight wrapper object holding the string `"same-value"` — because `singletonList` must be able to wrap *any* value passed to it, it cannot pre-allocate one shared instance the way `emptyList` can; each call needs its own wrapper around whatever value was actually supplied.
4. `single1 == single2` therefore correctly reports `false` — they are two distinct objects in memory, even though both happen to have been constructed with the identical string argument.
5. `single1.equals(single2)` reports `true`, since `List.equals` compares elements by value (using each element's own `equals` method, here `String.equals`), not by object identity — confirming that while the two singleton-list wrappers are different objects, they represent equal, interchangeable data from a value-comparison perspective.

## 7. Gotchas & takeaways

> **Gotcha:** don't assume `Collections.singletonList(x)` (or `singleton`/`singletonMap`) shares instances across calls the way `emptyList()`/`emptySet()`/`emptyMap()` do — each call to a `singletonX` method allocates a new (small) wrapper object, since it must hold whatever specific value was passed to that particular call. Only the `emptyX` family benefits from true call-independent object sharing, precisely because "empty" requires no per-call state at all.

- `Collections.emptyList()`/`emptySet()`/`emptyMap()` each return a shared, cached, immutable singleton instance — genuinely the same object reference on every call, with zero per-call allocation cost.
- Returning these instead of `null` for "no results" lets callers safely call `.size()`, `.isEmpty()`, or iterate directly, with no null-check required.
- `Collections.singletonList(x)`/`singleton(x)`/`singletonMap(k, v)` return a new, lightweight, immutable one-element (or one-entry) wrapper per call — smaller and faster to construct than a general-purpose collection, but not shared across calls the way the empty-collection family is.
- All of these are immutable — attempting to mutate any of them throws `UnsupportedOperationException`, exactly like [`Collections.unmodifiableX`](0843-collections-unmodifiable-views.md) wrappers.
- Prefer these targeted factory methods over constructing a full `ArrayList`/`HashSet`/`HashMap` for the specific zero- or one-element cases they're designed for.
