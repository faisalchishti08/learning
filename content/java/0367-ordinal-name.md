---
card: java
gi: 367
slug: ordinal-name
title: ordinal() & name()
---

## 1. What it is

Every enum constant automatically has two final methods it can never override: `name()`, which returns the exact identifier text you wrote in the source code (`"MONDAY"` for `Day.MONDAY`), and `ordinal()`, which returns its zero-based position in the enum's declaration order (`0` for the first constant, `1` for the second, and so on). Both are inherited from `java.lang.Enum`, the implicit superclass of every enum you write, and neither can be changed or reassigned by you.

## 2. Why & when

`name()` is the reliable, stable textual identity of a constant — it's what `valueOf()` matches against, and what `toString()` returns by default (though `toString()` can be overridden, `name()` never can be). Use `name()` when you specifically need the exact declared identifier as text, such as serializing to a format that must round-trip through `valueOf()` later.

`ordinal()` reflects nothing more than **declaration order** — it has no inherent business meaning. It exists mainly to support internal machinery like `EnumSet` and `EnumMap`, and for use with `compareTo()` (enums are `Comparable` by declaration order automatically). It is a trap when misused for business logic: if a constant is inserted, removed, or reordered in the source file, every ordinal downstream of that change silently shifts, potentially corrupting any external data (a database column, a serialized file) that stored an ordinal expecting it to mean something stable.

The practical rule: use `name()` (or `valueOf()`) for anything that needs to survive code changes or cross a persistence boundary; treat `ordinal()` as an internal implementation detail, useful for in-memory comparisons within a single run, never for storage.

## 3. Core concept

```java
public class OrdinalNameDemo {
    enum Priority { LOW, MEDIUM, HIGH, CRITICAL }

    public static void main(String[] args) {
        for (Priority p : Priority.values()) {
            System.out.println(p.name() + " -> ordinal " + p.ordinal());
        }
        System.out.println(Priority.LOW.compareTo(Priority.HIGH)); // negative: LOW comes before HIGH
    }
}
```

**How to run:** `java OrdinalNameDemo.java`

`p.name()` prints the literal declared identifier (`"LOW"`, `"MEDIUM"`, ...); `p.ordinal()` prints its position (`0`, `1`, `2`, `3`). `Priority.LOW.compareTo(Priority.HIGH)` returns a negative number because `LOW`'s ordinal (0) is less than `HIGH`'s ordinal (2) — enum comparison is purely declaration-order-based.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each enum constant has a stable name from its source identifier and an ordinal from its declaration position, which shifts if constants are reordered">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="50" fill="#79c0ff" font-size="10" text-anchor="middle">LOW</text>
  <text x="95" y="65" fill="#8b949e" font-size="9" text-anchor="middle">ordinal 0</text>

  <rect x="175" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="240" y="50" fill="#79c0ff" font-size="10" text-anchor="middle">MEDIUM</text>
  <text x="240" y="65" fill="#8b949e" font-size="9" text-anchor="middle">ordinal 1</text>

  <rect x="320" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="385" y="50" fill="#79c0ff" font-size="10" text-anchor="middle">HIGH</text>
  <text x="385" y="65" fill="#8b949e" font-size="9" text-anchor="middle">ordinal 2</text>

  <rect x="465" y="30" width="130" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="530" y="50" fill="#79c0ff" font-size="10" text-anchor="middle">CRITICAL</text>
  <text x="530" y="65" fill="#8b949e" font-size="9" text-anchor="middle">ordinal 3</text>

  <text x="20" y="110" fill="#e6edf3" font-size="10">name() = the fixed source identifier -- never changes, safe to persist.</text>
  <text x="20" y="132" fill="#f85149" font-size="10">ordinal() = position in this list -- shifts if you insert/remove/reorder a constant. Unsafe to persist.</text>
</svg>

## 5. Runnable example

Scenario: storing a task's priority, evolved from a naive version that persists the ordinal directly, through the moment reordering the enum silently corrupts old data, to a version that persists `name()` instead and is immune to reordering.

### Level 1 — Basic

```java
public class PriorityOrdinalBasic {
    enum Priority { LOW, MEDIUM, HIGH } // ordinals: LOW=0, MEDIUM=1, HIGH=2

    static int toStorage(Priority p) {
        return p.ordinal(); // "convenient" -- just an int
    }

    static Priority fromStorage(int stored) {
        return Priority.values()[stored]; // look up by position
    }

    public static void main(String[] args) {
        int stored = toStorage(Priority.HIGH); // stores 2
        System.out.println("Stored as: " + stored);
        System.out.println("Restored: " + fromStorage(stored));
    }
}
```

**How to run:** `java PriorityOrdinalBasic.java`

This "works" today: `HIGH`'s ordinal (`2`) round-trips back to `HIGH` correctly. But the storage format now silently depends on the exact declaration order of `Priority` never changing — a fragile, invisible assumption.

### Level 2 — Intermediate

```java
public class PriorityOrdinalBug {
    // Someone adds a new priority level ABOVE HIGH in the source file:
    enum Priority { LOW, MEDIUM, URGENT, HIGH } // ordinals shifted: HIGH is now 3, not 2!

    static Priority fromStorage(int stored) {
        return Priority.values()[stored];
    }

    public static void main(String[] args) {
        int oldStoredValue = 2; // this "2" was saved back when HIGH's ordinal WAS 2
        System.out.println("Restored: " + fromStorage(oldStoredValue)); // now silently wrong!
    }
}
```

**How to run:** `java PriorityOrdinalBug.java`

This is the bug in action: `oldStoredValue = 2` represented `HIGH` under the *old* declaration order. After `URGENT` was inserted before `HIGH`, ordinal `2` now belongs to `URGENT` instead — the old stored data is silently reinterpreted as the wrong priority, with no exception, no warning, just quietly incorrect behaviour.

### Level 3 — Advanced

```java
public class PriorityNameSafe {
    enum Priority { LOW, MEDIUM, URGENT, HIGH } // reordering no longer matters for storage

    static String toStorage(Priority p) {
        return p.name(); // store the stable identifier text, not the position
    }

    static Priority fromStorage(String stored) {
        try {
            return Priority.valueOf(stored); // look up by name, immune to reordering
        } catch (IllegalArgumentException e) {
            throw new IllegalStateException("Unknown stored priority: " + stored, e);
        }
    }

    public static void main(String[] args) {
        String stored = toStorage(Priority.HIGH); // stores "HIGH", not a position
        System.out.println("Stored as: " + stored);
        System.out.println("Restored: " + fromStorage(stored));
    }
}
```

**How to run:** `java PriorityNameSafe.java`

Switching storage to `name()`/`valueOf()` fixes the Level 2 bug at the root: the stored value is now the constant's stable textual identifier, `"HIGH"`, which resolves correctly regardless of where `HIGH` sits in the declaration order — inserting, removing, or reordering other constants can never corrupt this stored data.

## 6. Walkthrough

Execution starts in `main`. `toStorage(Priority.HIGH)` calls `p.name()` on the `HIGH` constant, which returns the literal string `"HIGH"` — this is fixed by the source code identifier and completely independent of `HIGH`'s position in the enum. `stored` is now the string `"HIGH"`, and `main` prints `Stored as: HIGH`.

`fromStorage(stored)` is called with `"HIGH"`. Inside, `Priority.valueOf("HIGH")` searches for a constant whose `name()` equals `"HIGH"` exactly; it finds `Priority.HIGH` (regardless of the fact that it's now the fourth constant declared, ordinal 3, not the third as it might have been in an earlier version of the code) and returns it directly. No `IllegalArgumentException` is thrown since the name matches. `main` prints `Restored: HIGH`.

Contrast this with the Level 2 bug: there, `fromStorage` used `Priority.values()[stored]` — a raw array index into declaration order. When `URGENT` was inserted before `HIGH`, the *value* `2` that used to mean "the constant at position 2" (`HIGH`, in the old three-constant version) now means "the constant at position 2" in the *new* four-constant version — which is `URGENT`, not `HIGH`. The old stored integer was implicitly coupled to a declaration order that changed, and nothing detected the mismatch.

Expected output (Level 3):
```
Stored as: HIGH
Restored: HIGH
```

## 7. Gotchas & takeaways

> Never persist `ordinal()` to a database, file, or any format that must survive across code changes — inserting, removing, or reordering enum constants silently shifts every ordinal after the change point, and old stored data will be reinterpreted as the wrong constant with no error raised. Persist `name()` (via `valueOf()` to read it back) instead.

- `name()` returns the exact, fixed source identifier of a constant; it is `final` and cannot be overridden, unlike `toString()`.
- `ordinal()` returns the constant's zero-based position in declaration order — meaningful only for in-memory comparisons within a single version of the code, never as a stable identifier.
- `Enum` implements `Comparable` using `ordinal()` automatically, which is why `compareTo()` on enums reflects declaration order by default.
- `EnumSet` and `EnumMap` use ordinals internally for their fast, array/bitset-based implementations — this is a safe, appropriate use of ordinal, since it never crosses a persistence boundary.
- When you need a stable, reorder-proof textual representation of an enum constant (for storage, JSON, logs meant to be machine-parsed later), always prefer `name()`/`valueOf()` over `ordinal()`.
