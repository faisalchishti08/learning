---
card: java
gi: 175
slug: arrays-of-objects-default-null
title: Arrays of objects (default null)
---

## 1. What it is

When you create an array of a **reference type** (any class, like `String`, or a custom class), `new Type[n]` allocates `n` slots, but each slot is filled with the default value for a reference — **`null`** — not an actual object. This differs from arrays of **primitives** (`int[]`, `double[]`, `boolean[]`), where slots default to `0`, `0.0`, or `false` respectively; a reference-type array's slots start out empty, pointing at nothing.

```java
String[] names = new String[3];
System.out.println(names[0]); // null — not an empty string ""
System.out.println(names.length); // 3 — the array itself exists, fully allocated

names[0] = "Ann"; // now slot 0 holds an actual object reference
System.out.println(names[0]); // Ann
```

The array `names` itself is a real, non-null object of length 3 the moment it's created — it's the **elements inside it** that start out `null` until explicitly assigned.

## 2. Why & when

This default matters any time an array is created before all its data is known, which is extremely common:

- **Building up a collection incrementally** — allocate `new Object[100]` upfront, then fill slots one at a time as data becomes available (e.g. as rows are read from a file).
- **Sparse data** — an array where only some positions ever get a real value, and the rest are meant to represent "nothing here" using `null`.
- **Avoiding `NullPointerException`** — calling a method on an unassigned slot (`names[1].length()` when `names[1]` is still `null`) throws `NullPointerException`, one of the single most common runtime errors in Java; knowing that object-array slots default to `null` (not to some harmless empty marker) is essential to avoiding this.

You need to be conscious of this default whenever you allocate an object array with `new Type[n]` and don't immediately fill every slot in the same statement — any slot you haven't gotten to yet is a landmine of `null` waiting to throw if touched.

## 3. Core concept

```java
public class NullDefaultDemo {
    public static void main(String[] args) {
        String[] words = new String[4];
        int[] numbers = new int[4];

        System.out.println(java.util.Arrays.toString(words));   // [null, null, null, null]
        System.out.println(java.util.Arrays.toString(numbers)); // [0, 0, 0, 0]

        words[1] = "hello";
        System.out.println(words[1].length()); // 5 — safe, words[1] is a real String now

        try {
            System.out.println(words[2].length()); // words[2] is still null!
        } catch (NullPointerException e) {
            System.out.println("Caught: cannot call length() on a null slot");
        }
    }
}
```

`words[2]` was never assigned, so it holds `null`; calling `.length()` on it — a method call on "nothing" — throws `NullPointerException` immediately, distinct from `numbers[2]`, which safely defaults to `0` because `int` is a primitive with no concept of "null."

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An array of four String reference slots, all shown as null except slot 1 which points to an actual String object hello, contrasted with an int array whose slots default to zero">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <text x="300" y="24" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">String[] words = new String[4];   (reference type: default is null)</text>

  <rect x="60" y="40" width="70" height="34" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="95" y="62" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">null</text>
  <rect x="140" y="40" width="70" height="34" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="175" y="62" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">→"hello"</text>
  <rect x="220" y="40" width="70" height="34" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="255" y="62" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">null</text>
  <rect x="300" y="40" width="70" height="34" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="335" y="62" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">null</text>

  <text x="300" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">int[] numbers = new int[4];   (primitive type: default is 0, never null)</text>
  <rect x="140" y="110" width="50" height="28" fill="#1c2430" stroke="#6db33f"/><text x="165" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">0</text>
  <rect x="190" y="110" width="50" height="28" fill="#1c2430" stroke="#6db33f"/><text x="215" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">0</text>
  <rect x="240" y="110" width="50" height="28" fill="#1c2430" stroke="#6db33f"/><text x="265" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">0</text>
  <rect x="290" y="110" width="50" height="28" fill="#1c2430" stroke="#6db33f"/><text x="315" y="129" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">0</text>
</svg>

Reference-type slots default to `null`; primitive slots default to `0`/`false` — never `null`.

## 5. Runnable example

Scenario: building a small roster of `Employee` objects, filled in over time as data arrives — starting with basic allocation showing the `null` default, then extending to progressively fill the roster, then hardening into a report method that safely skips any still-`null` (unfilled) slots.

### Level 1 — Basic

```java
public class RosterBasic {
    static class Employee {
        String name;
        Employee(String name) { this.name = name; }
    }

    public static void main(String[] args) {
        Employee[] roster = new Employee[3];

        for (int i = 0; i < roster.length; i++) {
            System.out.println("Slot " + i + ": " + roster[i]); // prints "null" for every slot
        }
    }
}
```

**How to run:** `java RosterBasic.java`

`new Employee[3]` allocates 3 slots, all defaulting to `null` since `Employee` is a reference type — printing a `null` reference with `+` string concatenation prints the literal text `"null"`, not an error, since `String.valueOf(null)` handles this case gracefully.

### Level 2 — Intermediate

Same roster, now progressively filled as employees are hired, leaving some slots still `null` because not all positions are filled yet.

```java
public class RosterIntermediate {
    static class Employee {
        String name;
        Employee(String name) { this.name = name; }
    }

    public static void main(String[] args) {
        Employee[] roster = new Employee[4];

        roster[0] = new Employee("Ann");
        roster[2] = new Employee("Bo"); // slots 1 and 3 remain null — not yet hired

        for (int i = 0; i < roster.length; i++) {
            if (roster[i] != null) {
                System.out.println("Slot " + i + ": " + roster[i].name);
            } else {
                System.out.println("Slot " + i + ": (vacant)");
            }
        }
    }
}
```

**How to run:** `java RosterIntermediate.java`

`if (roster[i] != null)` guards every access to `.name` — without this check, `roster[1].name` would throw `NullPointerException` the moment the loop reached the still-unfilled slot 1.

### Level 3 — Advanced

Same roster, now with a reporting method that both counts vacancies and safely computes something (average name length) only across the filled slots, ignoring `null` entries entirely.

```java
public class RosterAdvanced {
    static class Employee {
        String name;
        Employee(String name) { this.name = name; }
    }

    static void reportRoster(Employee[] roster) {
        int filled = 0;
        int totalNameLength = 0;
        for (Employee e : roster) {
            if (e != null) {
                filled++;
                totalNameLength += e.name.length();
            }
        }
        int vacant = roster.length - filled;
        System.out.println(filled + " filled, " + vacant + " vacant");
        if (filled > 0) {
            System.out.println("Average name length: " + ((double) totalNameLength / filled));
        } else {
            System.out.println("No employees to average");
        }
    }

    public static void main(String[] args) {
        Employee[] roster = new Employee[5];
        roster[1] = new Employee("Ann");
        roster[3] = new Employee("Bartholomew");

        reportRoster(roster);
    }
}
```

**How to run:** `java RosterAdvanced.java`

The for-each loop's `if (e != null)` filters out every unfilled slot before touching `e.name`, and `filled` (not `roster.length`) is used as the divisor for the average — correctly excluding vacant slots from both the count and the calculation rather than treating them as zero-length names.

## 6. Walkthrough

Trace `reportRoster(roster)` for `roster = [null, Employee("Ann"), null, Employee("Bartholomew"), null]`:

**Index 0.** `e` is `null` — the `if` guard skips it entirely; `filled` and `totalNameLength` stay at `0`.

**Index 1.** `e` is `Employee("Ann")`, not `null`. `filled` becomes `1`. `e.name.length()` is `3` (`"Ann"`). `totalNameLength` becomes `3`.

**Index 2.** `e` is `null` — skipped again.

**Index 3.** `e` is `Employee("Bartholomew")`. `filled` becomes `2`. `e.name.length()` is `11`. `totalNameLength` becomes `3 + 11 = 14`.

**Index 4.** `e` is `null` — skipped.

**After the loop.** `filled = 2`, `vacant = roster.length - filled = 5 - 2 = 3`. Prints `"2 filled, 3 vacant"`. Since `filled > 0`, prints `"Average name length: 7.0"` (`14.0 / 2`).

```
index:   0     1        2     3              4
value: null  "Ann"    null  "Bartholomew"   null
filled count: 2   totalNameLength: 3 + 11 = 14
vacant = 5 - 2 = 3
average = 14 / 2 = 7.0
```

## 7. Gotchas & takeaways

> **`new Type[n]` for a reference type does not create `n` objects — it creates `n` empty slots, each holding `null`.** Calling any method on an unassigned slot (`roster[i].name` before `roster[i]` is assigned) throws `NullPointerException`. This is different from `new int[n]`, whose slots are immediately usable `0` values with no risk of this exception.

> **Always guard with `if (element != null)` before calling methods on elements of a freshly-allocated or partially-filled object array**, unless you are certain every slot has already been assigned. Skipping this check is one of the most common sources of `NullPointerException` in real Java code.

- Object-array slots default to `null`; primitive-array slots default to `0`, `0.0`, or `false` — never `null`.
- The array itself is a real, non-null object of the requested length the instant it's created, even before any element is assigned.
- Calling a method on a `null` element throws `NullPointerException`; always check `!= null` first when a slot might be unfilled.
- When aggregating over a possibly-sparse object array (counts, sums, averages), skip `null` entries explicitly rather than assuming every slot holds real data.
