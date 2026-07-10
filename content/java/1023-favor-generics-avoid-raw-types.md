---
card: java
gi: 1023
slug: favor-generics-avoid-raw-types
title: Favor generics & avoid raw types
---

## 1. What it is

A **raw type** is a generic class or interface used without its type parameter — `List` instead of `List<String>`. Java allows this purely for backward compatibility with code written before generics existed (Java 5), but it throws away all the type-checking generics exist to provide: a raw `List` will accept and return `Object`, meaning the compiler can't catch a type mismatch at the point it's introduced — instead, the program compiles fine and blows up later, at an unrelated line, with a `ClassCastException` when the wrong-typed element is finally read back out and cast.

## 2. Why & when

Using a raw type means the compiler stops checking what goes into the collection — you can add a `String` and an `Integer` to the same raw `List` without a single warning, and the resulting `ClassCastException` won't surface until code much later tries to read an element back out and cast it to the type it *expected*, by which point the actual bug (the wrong insertion) is far removed from the error and much harder to trace. Generics move that same check to compile time, at the exact point the mismatched type is added, with a clear compiler error instead of a runtime crash somewhere else entirely.

Always favor a parameterized type (`List<String>`) over its raw equivalent (`List`) — there's essentially never a good reason to use a raw type in new code; even `List<Object>` (which explicitly says "any object is allowed here, and I mean it") is safer and more honest than a bare raw `List`, since it still requires an explicit, visible opt-in rather than compiling silently. The only place raw types show up unavoidably is interacting with pre-generics legacy code, and even there, the recommended approach is to isolate the raw-type interaction to the smallest possible surface.

## 3. Core concept

```
import java.util.ArrayList;
import java.util.List;

// Raw type: the compiler allows ANY object in, and gives no warning about it
List names = new ArrayList();
names.add("Ana");
names.add(42); // compiles fine! Nothing catches this obviously wrong insertion.
String first = (String) names.get(0); // works
String second = (String) names.get(1); // ClassCastException -- but only discovered HERE, at read time

// Generic (parameterized) type: the compiler enforces type safety AT THE INSERTION POINT
List<String> safeNames = new ArrayList<>();
safeNames.add("Ana");
safeNames.add(42); // COMPILE ERROR right here -- caught immediately, at the actual mistake
String safeFirst = safeNames.get(0); // no cast needed at all -- the compiler already knows the type
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A raw List accepting a mismatched Integer silently, with the error only surfacing later as a ClassCastException at an unrelated read site, versus a generic List catching the mismatch immediately at the point of insertion">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Raw type: error surfaces LATE</text>
  <rect x="30" y="40" width="230" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="145" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">names.add(42) -- compiles fine</text>
  <rect x="30" y="90" width="230" height="30" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="110" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">(String) names.get(1) -- CRASH, far away</text>
  <line x1="145" y1="70" x2="145" y2="90" stroke="#f0883e" stroke-dasharray="4" marker-end="url(#a)"/>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Generic type: error caught IMMEDIATELY</text>
  <rect x="380" y="65" width="230" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="85" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">safeNames.add(42) -- COMPILE ERROR here</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A raw type's mismatch surfaces as a runtime crash far from where the bad data entered; a generic type's compiler error points directly at the mistake.

## 5. Runnable example

Scenario: a registry storing names, evolving from a raw-type collection that hides a type mismatch until runtime into a fully generic design that catches the same mistake at compile time.

### Level 1 — Basic

```java
// File: RawTypesBasic.java
import java.util.ArrayList;
import java.util.List;

public class RawTypesBasic {
    @SuppressWarnings({"rawtypes", "unchecked"})
    public static void main(String[] args) {
        List names = new ArrayList(); // raw type -- no compile-time type checking at all
        names.add("Ana");
        names.add("Ben");
        names.add(42); // a clearly wrong insertion, but the compiler says nothing

        for (Object obj : names) {
            String name = (String) obj; // crashes on the THIRD element, far from where "42" was added
            System.out.println("Name: " + name);
        }
    }
}
```

**How to run:** save as `RawTypesBasic.java`, then `javac RawTypesBasic.java && java RawTypesBasic` (JDK 17+).

Expected output:
```
Name: Ana
Name: Ben
Exception in thread "main" java.lang.ClassCastException: class java.lang.Integer cannot be cast to class java.lang.String
	at RawTypesBasic.main(RawTypesBasic.java:14)
```

The mistake (`names.add(42)`) happened on one line, but the failure surfaces on a completely different line, in a different part of the code, during the loop — the raw type gave the compiler no way to catch the actual mistake where it occurred.

### Level 2 — Intermediate

```java
// File: RawTypesIntermediate.java
import java.util.ArrayList;
import java.util.List;

public class RawTypesIntermediate {
    public static void main(String[] args) {
        List<String> names = new ArrayList<>(); // parameterized -- fully type-checked
        names.add("Ana");
        names.add("Ben");
        // names.add(42); // uncommenting this line would be a COMPILE ERROR, right here

        for (String name : names) { // no cast needed at all -- the compiler already knows the type
            System.out.println("Name: " + name);
        }
    }
}
```

**How to run:** save as `RawTypesIntermediate.java`, then `javac RawTypesIntermediate.java && java RawTypesIntermediate` (JDK 17+).

Expected output:
```
Name: Ana
Name: Ben
```

The real-world concern added: `List<String>` guarantees every element is genuinely a `String` — the loop needs no cast, and any attempt to insert a mismatched type is caught immediately, at the exact line of the mistake, before the program ever runs.

### Level 3 — Advanced

```java
// File: RawTypesAdvanced.java
import java.util.ArrayList;
import java.util.List;

// A generic class of your own, demonstrating a bounded type parameter --
// only types that are Comparable to themselves are allowed, enforced at compile time.
class SortedRegistry<T extends Comparable<T>> {
    private final List<T> items = new ArrayList<>();

    void add(T item) {
        int insertionPoint = 0;
        while (insertionPoint < items.size() && items.get(insertionPoint).compareTo(item) < 0) {
            insertionPoint++;
        }
        items.add(insertionPoint, item); // keeps items sorted at all times
    }

    List<T> getAll() { return List.copyOf(items); }
}

public class RawTypesAdvanced {
    public static void main(String[] args) {
        SortedRegistry<String> names = new SortedRegistry<>();
        names.add("Charlie");
        names.add("Alice");
        names.add("Bob");
        System.out.println("sorted names: " + names.getAll());

        SortedRegistry<Integer> scores = new SortedRegistry<>();
        scores.add(85);
        scores.add(42);
        scores.add(99);
        System.out.println("sorted scores: " + scores.getAll());

        // SortedRegistry<Object> would NOT compile -- Object doesn't implement
        // Comparable<Object>, so the bound T extends Comparable<T> rejects it
        // at the exact point of instantiation, not somewhere deep inside add().
    }
}
```

**How to run:** save as `RawTypesAdvanced.java`, then `javac RawTypesAdvanced.java && java RawTypesAdvanced` (JDK 17+).

Expected output:
```
sorted names: [Alice, Bob, Charlie]
sorted scores: [42, 85, 99]
```

The production-flavored hard case: `SortedRegistry<T extends Comparable<T>>` is a *bounded* type parameter — it doesn't just say "some type T," it says "some type T that can be compared to itself," letting `add`'s implementation safely call `.compareTo` on `T` values without any cast, and rejecting at compile time any attempt to use a type (like a plain `Object`) that doesn't support that comparison at all.

## 6. Walkthrough

Tracing `names.add("Alice")` (the second insertion) in `RawTypesAdvanced.main`:

1. `names` is a `SortedRegistry<String>` that already contains `["Charlie"]` after the first `add` call.
2. `names.add("Alice")` runs `SortedRegistry.add` with `item = "Alice"`. `insertionPoint` starts at `0`.
3. The `while` loop checks `insertionPoint < items.size()` (`0 < 1`, true) and `items.get(0).compareTo(item) < 0` — this calls `"Charlie".compareTo("Alice")`, which returns a positive number (since `"Charlie"` comes after `"Alice"` alphabetically), so `< 0` is `false` — the loop condition as a whole is `false`, and the loop body never executes.
4. `items.add(0, "Alice")` inserts `"Alice"` at index `0`, pushing `"Charlie"` to index `1`. `items` is now `["Alice", "Charlie"]`.
5. The third call, `names.add("Bob")`, repeats this process: `insertionPoint` starts at `0`; `items.get(0).compareTo("Bob")` is `"Alice".compareTo("Bob")`, which is negative (`"Alice"` comes before `"Bob"`), so `< 0` is `true` — the loop continues, incrementing `insertionPoint` to `1`. Now `items.get(1).compareTo("Bob")` is `"Charlie".compareTo("Bob")`, positive, so `< 0` is `false` — the loop stops at `insertionPoint = 1`.
6. `items.add(1, "Bob")` inserts `"Bob"` at index `1`, giving the final order `["Alice", "Bob", "Charlie"]` — printed by `names.getAll()` as `"sorted names: [Alice, Bob, Charlie]"`. Every `.compareTo` call in this whole trace was made without any cast, because the bound `T extends Comparable<T>` guarantees at compile time that every `T` genuinely supports `.compareTo`.

## 7. Gotchas & takeaways

> **Gotcha:** a raw type isn't just "less safe" — using one also disables generics checking for *every other* generic usage in the same expression, sometimes producing confusing "unchecked call" warnings on lines that look otherwise correct. The fix is almost always to add the missing type parameter, not to suppress the warning.

- A raw type (`List` instead of `List<String>`) throws away compile-time type checking entirely, deferring type mismatches to a runtime `ClassCastException` at a potentially unrelated line far from the actual mistake.
- Always favor a parameterized type over its raw equivalent — even `List<Object>` (an explicit, visible "anything goes here") is safer than a raw `List`.
- Bounded type parameters (`<T extends Comparable<T>>`) let a generic class rely on specific capabilities of its type parameter (like `.compareTo`) while still rejecting, at compile time, any type that doesn't provide them.
- Raw types exist purely for backward compatibility with pre-Java-5 code — there's essentially no reason to introduce one in new code.
- The `@SuppressWarnings` annotation should be reserved for the rare, deliberate cases where a raw-type or unchecked interaction with legacy code is genuinely unavoidable — and even then, scoped as narrowly as possible, not applied broadly to silence warnings you haven't actually investigated.
- This same "catch the mistake as early and as close to its source as possible" philosophy underlies most of Java's type-system features — generics simply extend it to container and parameterized types.
