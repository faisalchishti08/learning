---
card: java
gi: 1022
slug: prefer-enums-enumset
title: Prefer enums & EnumSet
---

## 1. What it is

Before `enum` existed, Java code represented a fixed set of named constants using plain `int` values (the "int enum pattern": `public static final int RED = 0;`). This has no type safety at all — a method expecting a color constant will happily accept any `int`, including one that means nothing. Java's `enum` type replaces this entirely: it's a genuine class, each constant is a real, type-checked object, and it comes with `EnumSet` and `EnumMap` — collection implementations specifically optimized for enum keys, internally backed by bit vectors instead of hash tables, making them both faster and more memory-efficient than the generic alternatives.

## 2. Why & when

The `int` constant pattern compiles away all meaning: `applyColor(3)` type-checks whether `3` means "RED," "BLUE," or an entirely unrelated status code from a different group of constants — the compiler can't help, because to the compiler it's just an `int`. `enum` fixes this at the type level: a method parameter typed `Color` can only ever receive an actual `Color` constant, never a stray integer, and an IDE can autocomplete the valid values. On top of that, when you need a *set* of enum values (a set of active `Day` values, a set of enabled `Permission` flags), `EnumSet` is dramatically more efficient than a general-purpose `HashSet<T>` — internally, it represents membership as bits in a single `long` (or an array of `long`s for larger enums), making operations like `contains`, `add`, and set unions extremely fast.

Reach for `enum` any time you have a genuinely fixed, known-at-compile-time set of related constants — the classic sign is a group of `int` or `String` constants that are always used together and represent mutually exclusive options. Reach for `EnumSet`/`EnumMap` specifically whenever the keys or set elements are enum constants — there's essentially no reason to use a generic `HashSet<SomeEnum>` instead, since `EnumSet` is a strict improvement in both speed and memory for that exact case.

## 3. Core concept

```
// The old int-constant pattern: no type safety, easy to pass the wrong "kind" of constant
public static final int COLOR_RED = 0;
public static final int COLOR_BLUE = 1;
public static final int STATUS_ACTIVE = 0; // uh oh -- same value as COLOR_RED, compiler won't catch a mix-up

void applyColor(int color) { /* accepts ANY int, including STATUS_ACTIVE by mistake */ }

// The enum replacement: genuinely type-safe, self-documenting, IDE-completable
enum Color { RED, BLUE, GREEN }
void applyColor(Color color) { /* can ONLY ever receive an actual Color constant */ }

// EnumSet: a set of enum values, backed by an efficient bit vector internally
enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }
java.util.EnumSet<Day> weekend = java.util.EnumSet.of(Day.SAT, Day.SUN);
System.out.println(weekend.contains(Day.SAT)); // fast bitwise check, not a hash lookup
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An int constant COLOR_RED being indistinguishable from an unrelated int constant STATUS_ACTIVE at the type level, versus an enum Color constant that can never be confused with an unrelated type">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">int constants: no type safety</text>
  <rect x="30" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="85" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">COLOR_RED = 0</text>
  <rect x="160" y="40" width="130" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="225" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">STATUS_ACTIVE = 0</text>
  <text x="155" y="100" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">both are just "0" -- indistinguishable to the compiler</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">enum: real, distinct types</text>
  <rect x="380" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="435" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Color.RED</text>
  <rect x="510" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="61" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Status.ACTIVE</text>
  <text x="500" y="100" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">different types -- compiler rejects any mix-up</text>
</svg>

Plain `int` constants collapse to indistinguishable numbers; `enum` constants remain genuinely distinct, type-checked values.

## 5. Runnable example

Scenario: a scheduling system tracking active days of the week, evolving from the unsafe int-constant pattern into `enum` with `EnumSet` for efficient set operations.

### Level 1 — Basic

```java
// File: EnumBasic.java
public class EnumBasic {
    static final int MON = 0, TUE = 1, WED = 2, THU = 3, FRI = 4, SAT = 5, SUN = 6;
    static final int STATUS_INACTIVE = 0; // same value as MON -- nothing distinguishes them

    static boolean isWeekend(int day) {
        return day == SAT || day == SUN;
    }

    public static void main(String[] args) {
        System.out.println("is SAT weekend? " + isWeekend(SAT));
        // Nothing stops this nonsensical call from compiling and running:
        System.out.println("is STATUS_INACTIVE weekend? " + isWeekend(STATUS_INACTIVE));
    }
}
```

**How to run:** save as `EnumBasic.java`, then `javac EnumBasic.java && java EnumBasic` (JDK 17+).

Expected output:
```
is SAT weekend? true
is STATUS_INACTIVE weekend? true
```

`isWeekend(STATUS_INACTIVE)` compiles and runs without any warning, silently returning a nonsensical answer — `STATUS_INACTIVE` and `MON` are both just the integer `0`, and the compiler has no way to know they represent completely unrelated concepts.

### Level 2 — Intermediate

```java
// File: EnumIntermediate.java
enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

public class EnumIntermediate {
    static boolean isWeekend(Day day) {
        return day == Day.SAT || day == Day.SUN;
    }

    public static void main(String[] args) {
        System.out.println("is SAT weekend? " + isWeekend(Day.SAT));
        System.out.println("is MON weekend? " + isWeekend(Day.MON));
        // isWeekend(someUnrelatedEnum) simply would not compile -- type safety enforced.
    }
}
```

**How to run:** save as `EnumIntermediate.java`, then `javac EnumIntermediate.java && java EnumIntermediate` (JDK 17+).

Expected output:
```
is SAT weekend? true
is MON weekend? false
```

The real-world concern added: `isWeekend` can only ever be called with an actual `Day` constant — any attempt to pass an unrelated type, or a stray integer, is a compile error, not a silent runtime mistake.

### Level 3 — Advanced

```java
// File: EnumAdvanced.java
import java.util.EnumSet;
import java.util.HashSet;
import java.util.Set;

enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }

public class EnumAdvanced {
    public static void main(String[] args) {
        // EnumSet: backed internally by a bit vector -- extremely fast and compact
        // for a set of enum constants, compared to a general-purpose HashSet.
        EnumSet<Day> weekend = EnumSet.of(Day.SAT, Day.SUN);
        EnumSet<Day> weekdays = EnumSet.complementOf(weekend); // "all Day values NOT in weekend"

        System.out.println("weekend: " + weekend);
        System.out.println("weekdays: " + weekdays);
        System.out.println("is WED a weekday? " + weekdays.contains(Day.WED));

        // A schedule using a HashSet<Day> would work functionally identically here,
        // but EnumSet uses a single long as its entire backing storage for up to 64
        // enum constants, versus HashSet's per-element hash-table nodes.
        Set<Day> genericWeekend = new HashSet<>(Set.of(Day.SAT, Day.SUN));
        System.out.println("functionally equal: " + weekend.equals(genericWeekend));

        // EnumSet also supports fast bulk operations reflecting set algebra directly:
        EnumSet<Day> midweek = EnumSet.range(Day.TUE, Day.THU);
        System.out.println("midweek: " + midweek);
    }
}
```

**How to run:** save as `EnumAdvanced.java`, then `javac EnumAdvanced.java && java EnumAdvanced` (JDK 17+).

Expected output:
```
weekend: [SAT, SUN]
weekdays: [MON, TUE, WED, THU, FRI]
is WED a weekday? true
functionally equal: true
midweek: [TUE, WED, THU]
```

The production-flavored hard case: `EnumSet.complementOf` and `EnumSet.range` demonstrate set-algebra operations that read naturally and execute efficiently because `EnumSet` knows the complete, fixed universe of possible values (every `Day` constant) at compile time — a `HashSet<Day>` can express the same *result* but has no way to offer operations like `complementOf` that rely on knowing the full enum universe.

## 6. Walkthrough

Tracing `EnumSet.complementOf(weekend)` in `EnumAdvanced.main`:

1. `EnumSet.of(Day.SAT, Day.SUN)` constructs `weekend` — internally, `EnumSet` represents this as a bit pattern where the bits corresponding to `Day.SAT`'s and `Day.SUN`'s ordinal positions (5 and 6, since `Day`'s constants are declared `MON, TUE, WED, THU, FRI, SAT, SUN` in that order, ordinals `0` through `6`) are set to `1`, and all others are `0`.
2. `EnumSet.complementOf(weekend)` needs to know the complete universe of possible `Day` values to compute "everything not in `weekend`" — it inspects `weekend`'s enum type (`Day.class`, discoverable since `weekend` is non-empty) and produces a new `EnumSet` whose bit pattern is the bitwise complement of `weekend`'s: every bit that was `0` becomes `1` and vice versa, restricted to the seven valid `Day` positions.
3. The result, `weekdays`, has bits set for `MON, TUE, WED, THU, FRI` (ordinals `0` through `4`) and clear for `SAT, SUN` — when printed, `EnumSet`'s `toString()` lists its members in their natural declaration order: `[MON, TUE, WED, THU, FRI]`.
4. `weekdays.contains(Day.WED)` checks whether the bit at `Day.WED`'s ordinal position (`2`) is set — it is, from step 3 — so this returns `true`, printed as `"is WED a weekday? true"`.
5. `weekend.equals(genericWeekend)` compares a bit-vector-backed `EnumSet` against a hash-table-backed `HashSet` containing the same logical elements — `Set.equals` is defined purely in terms of "same elements, regardless of underlying implementation," so this returns `true` despite the two sets having completely different internal representations.
6. `EnumSet.range(Day.TUE, Day.THU)` constructs a set covering every `Day` constant whose ordinal falls between `Day.TUE`'s (`1`) and `Day.THU`'s (`3`) inclusive — `TUE, WED, THU` — printed as `"midweek: [TUE, WED, THU]"`, another operation only possible because `EnumSet` knows the enum's fixed, ordered universe of constants.

## 7. Gotchas & takeaways

> **Gotcha:** `EnumSet` (and `EnumMap`) require knowing the enum type up front to determine the universe of possible bits — an empty `EnumSet` created via the generic `EnumSet.noneOf(Day.class)` works fine, but a truly type-erased, "figure out the enum type from context" empty set isn't possible; you always specify the enum class explicitly for an empty set.

- The old `int`-constant pattern offers zero type safety — the compiler can't distinguish one group of related constants from another, or from an arbitrary integer.
- `enum` constants are genuine, distinct types — a method parameter typed to an enum can only ever receive an actual constant of that enum, caught at compile time.
- `EnumSet` and `EnumMap` are specialized, bit-vector-backed collection implementations for enum keys/elements — functionally interchangeable with `HashSet`/`HashMap` from the caller's perspective, but faster and far more memory-efficient.
- `EnumSet` supports set-algebra operations (`complementOf`, `range`) that rely on knowing the enum's complete, ordered universe of constants — operations a generic `HashSet` has no equivalent for.
- Enum constants can also carry their own fields, methods, and even constant-specific method bodies, making them far more expressive than a bare integer or string label ever could be.
- Don't reach for `int` or `String` constants to represent a fixed, known set of related values in new code — `enum` is essentially strictly better for this purpose in modern Java.
