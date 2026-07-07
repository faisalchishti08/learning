---
card: java
gi: 369
slug: enums-with-methods
title: Enums with methods
---

## 1. What it is

Because an enum is a real class under the hood, it can declare ordinary **instance methods**, exactly like any other class — methods that use `this`, read the enum's fields, and are called on a specific constant (`Status.NOT_FOUND.isError()`). This is distinct from just having fields: methods let a constant *compute* something, not just store it, and every constant automatically shares the same method implementations unless it overrides them (covered separately under constant-specific method bodies).

## 2. Why & when

Once an enum has fields (mass and radius for a planet, a numeric code and phrase for an HTTP status), it's natural to also want behaviour derived from those fields — a planet's surface gravity, whether a status code represents an error, how many days are left in the week from a given day. Writing that logic as a method directly on the enum keeps computed behaviour next to the data it depends on, rather than scattering `if`/`switch` logic across unrelated utility classes that all need to stay in sync with the enum's definition.

This is the natural next step after adding fields: fields answer "what data does this constant carry?", methods answer "what can this constant *do* with that data?". You reach for enum methods whenever you find yourself writing a `switch` statement elsewhere in the code that dispatches purely on which enum constant you have — that logic almost always belongs inside the enum itself instead.

## 3. Core concept

```java
public class StatusMethodDemo {
    enum Status {
        OK(200), NOT_FOUND(404), SERVER_ERROR(500);

        private final int code;
        Status(int code) { this.code = code; }

        boolean isError() { // an instance method using this constant's own field
            return code >= 400;
        }
    }

    public static void main(String[] args) {
        for (Status s : Status.values()) {
            System.out.println(s + ": isError=" + s.isError());
        }
    }
}
```

**How to run:** `java StatusMethodDemo.java`

`isError()` is an ordinary instance method: it reads `code`, the field belonging to whichever constant it's called on. `OK.isError()` evaluates `200 >= 400` (false); `NOT_FOUND.isError()` evaluates `404 >= 400` (true); `SERVER_ERROR.isError()` evaluates `500 >= 400` (true) — the same method body, applied to each constant's own data.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="one shared method body reads each constant's own field value, producing a different result per constant it is called on">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="580" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="53" fill="#6db33f" font-size="11" text-anchor="middle">boolean isError() { return code >= 400; }  -- one shared method body</text>

  <rect x="30" y="85" width="170" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="115" y="105" fill="#79c0ff" font-size="10" text-anchor="middle">OK.isError()</text>
  <text x="115" y="120" fill="#8b949e" font-size="9" text-anchor="middle">code=200 -&gt; false</text>

  <rect x="235" y="85" width="170" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="105" fill="#79c0ff" font-size="10" text-anchor="middle">NOT_FOUND.isError()</text>
  <text x="320" y="120" fill="#8b949e" font-size="9" text-anchor="middle">code=404 -&gt; true</text>

  <rect x="440" y="85" width="170" height="45" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="525" y="105" fill="#79c0ff" font-size="10" text-anchor="middle">SERVER_ERROR.isError()</text>
  <text x="525" y="120" fill="#8b949e" font-size="9" text-anchor="middle">code=500 -&gt; true</text>
</svg>

## 5. Runnable example

Scenario: computing the next day of the week, evolved from external switch-based logic living outside the enum, through the logic moving inside as a method using `ordinal()` and `values()`, to a version that also handles a "is it the weekend" business rule cleanly.

### Level 1 — Basic

```java
public class DayExternalLogic {
    enum Day { MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY }

    // logic lives OUTSIDE the enum, disconnected from the type it operates on
    static Day nextDay(Day d) {
        Day[] all = Day.values();
        return all[(d.ordinal() + 1) % all.length];
    }

    public static void main(String[] args) {
        System.out.println(nextDay(Day.FRIDAY));
        System.out.println(nextDay(Day.SUNDAY)); // wraps back to MONDAY
    }
}
```

**How to run:** `java DayExternalLogic.java`

The "next day" logic works, but it's a free-floating static method — nothing ties it to `Day` except that it happens to take one as a parameter; anyone extending or reusing `Day` in another file has to remember this helper exists elsewhere.

### Level 2 — Intermediate

```java
public class DayEnumMethod {
    enum Day {
        MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY;

        Day next() { // logic now lives directly on the type it belongs to
            Day[] all = values();
            return all[(ordinal() + 1) % all.length];
        }
    }

    public static void main(String[] args) {
        System.out.println(Day.FRIDAY.next());
        System.out.println(Day.SUNDAY.next());
    }
}
```

**How to run:** `java DayEnumMethod.java`

Moving `next()` inside the enum makes it discoverable and impossible to lose track of: anyone with a `Day` value can call `.next()` directly, and the method automatically works correctly no matter how many days are declared, since it derives everything from `values()` and `ordinal()` rather than a hardcoded count.

### Level 3 — Advanced

```java
public class DayEnumBusinessLogic {
    enum Day {
        MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY;

        Day next() {
            Day[] all = values();
            return all[(ordinal() + 1) % all.length];
        }

        boolean isWeekend() {
            return this == SATURDAY || this == SUNDAY;
        }

        Day nextWorkday() { // combines next() and isWeekend() to express a real business rule
            Day candidate = next();
            while (candidate.isWeekend()) {
                candidate = candidate.next();
            }
            return candidate;
        }
    }

    public static void main(String[] args) {
        for (Day d : Day.values()) {
            System.out.println(d + " -> next workday: " + d.nextWorkday());
        }
    }
}
```

**How to run:** `java DayEnumBusinessLogic.java`

`nextWorkday()` builds directly on the two simpler methods, `next()` and `isWeekend()`, composing them into a real business rule ("skip forward past any weekend days") entirely within the enum itself — no external caller needs to know how weekends are defined or how wraparound works.

## 6. Walkthrough

Execution starts in `main`. The loop `for (Day d : Day.values())` iterates all seven constants in declaration order. Trace the interesting case, `d = FRIDAY`.

`FRIDAY.nextWorkday()` runs. `candidate = next()` is called on `FRIDAY`: inside `next()`, `values()` returns the full seven-element array, `ordinal()` on `FRIDAY` is `4`, so `(4 + 1) % 7 = 5`, and `all[5]` is `SATURDAY`. `candidate` is now `SATURDAY`.

The `while (candidate.isWeekend())` loop checks: `SATURDAY.isWeekend()` evaluates `this == SATURDAY || this == SUNDAY`, which is `true` (first branch matches). So the loop body runs: `candidate = candidate.next()`. Inside, `SATURDAY.ordinal()` is `5`, `(5 + 1) % 7 = 6`, `all[6]` is `SUNDAY`. `candidate` is now `SUNDAY`.

The loop condition is checked again: `SUNDAY.isWeekend()` is also `true`. The loop body runs again: `candidate = candidate.next()`. `SUNDAY.ordinal()` is `6`, `(6 + 1) % 7 = 0`, `all[0]` is `MONDAY`. `candidate` is now `MONDAY`.

The loop condition is checked once more: `MONDAY.isWeekend()` is `false` (neither branch of the `||` matches). The `while` loop exits, and `nextWorkday()` returns `MONDAY`.

Back in `main`, this prints `FRIDAY -> next workday: MONDAY` — correctly skipping over both `SATURDAY` and `SUNDAY` in one call, built entirely from composing the two smaller methods.

Expected output (all seven lines; the interesting ones are FRIDAY, SATURDAY, and SUNDAY):
```
MONDAY -> next workday: TUESDAY
TUESDAY -> next workday: WEDNESDAY
WEDNESDAY -> next workday: THURSDAY
THURSDAY -> next workday: FRIDAY
FRIDAY -> next workday: MONDAY
SATURDAY -> next workday: MONDAY
SUNDAY -> next workday: MONDAY
```

## 7. Gotchas & takeaways

> `this == SATURDAY` inside an enum's own method body is comparing the current constant against another constant of the same type — this only works because enum constants are singletons (see [[enum-constants]]); it would be unsafe with almost any other kind of value.

- Enums are real classes, so they can declare ordinary instance methods that read `this`'s fields and are shared across every constant unless individually overridden.
- Moving logic that dispatches on "which constant do I have" into the enum itself (as a method) keeps that logic discoverable and co-located with the data it depends on, instead of scattered across external switch statements or utility classes.
- `values()` and `ordinal()` used together (as in `next()`) let a method work correctly regardless of how many constants exist, avoiding hardcoded counts that would break if constants are added or removed.
- Composing simple enum methods (`next()`, `isWeekend()`) into a more complex one (`nextWorkday()`) mirrors ordinary object-oriented method composition — enums are not a special, restricted feature, just classes with a fixed set of instances.
- Keep enum methods focused on logic that is intrinsic to the constant itself; behaviour that depends heavily on external context (a database, a network call) usually belongs in a separate service class that *takes* an enum as a parameter, not inside the enum.
