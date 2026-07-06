---
card: java
gi: 286
slug: java-util-calendar-legacy
title: java.util.Calendar (legacy)
---

## 1. What it is

`java.util.Calendar` is an abstract class (its common concrete implementation is `GregorianCalendar`) introduced to address `Date`'s deprecated date-component methods, providing calendar-aware field access and arithmetic: getting or setting the year, month, day, hour, and so on, plus adding or subtracting calendar units (like "add 3 months"). Like `Date`, it predates `java.time` and is now considered legacy, but it remains common in code written before Java 8.

```java
import java.util.Calendar;

public class CalendarDemo {
    public static void main(String[] args) {
        Calendar cal = Calendar.getInstance(); // factory method — returns a Calendar set to the current moment

        int year = cal.get(Calendar.YEAR);
        int month = cal.get(Calendar.MONTH); // ZERO-BASED: January is 0, not 1!
        int day = cal.get(Calendar.DAY_OF_MONTH);

        System.out.println("Year: " + year + ", Month (0-based): " + month + ", Day: " + day);

        cal.add(Calendar.DAY_OF_MONTH, 7); // move the calendar forward by 7 days
        System.out.println("One week later: " + cal.getTime()); // getTime() converts back to a Date
    }
}
```

`Calendar.getInstance()` is the standard factory method for obtaining a `Calendar` (never call a constructor directly, since `Calendar` is abstract and implementations vary by locale/timezone); `cal.get(Calendar.MONTH)` returns the month as a *zero-based* value (January is `0`, December is `11`) — a notoriously common source of off-by-one bugs in code using this API; `cal.add(...)` performs calendar-aware arithmetic, correctly handling month/year rollovers.

## 2. Why & when

`Calendar` exists to solve real problems `Date` had — genuine calendar-field access and calendar-aware arithmetic — but its own design introduces new pitfalls that understanding this topic will help you recognize and avoid.

- **Calendar-field access and manipulation** — `Calendar` lets you get or set individual components (year, month, day, hour, minute, second) and perform calendar-aware arithmetic (`add`, `roll`) that correctly handles things like month-end rollovers (adding a day to January 31st correctly produces February 1st, accounting for how many days each month actually has).
- **Locale and time zone awareness** — `Calendar.getInstance()` can be given a specific `Locale` or `TimeZone`, letting calendar calculations correctly respect regional calendar conventions and time zone offsets, something `Date` alone never provided.
- **Still mutable, and still legacy** — `Calendar` inherited `Date`'s core design philosophy of mutable state (calling `.add(...)` or `.set(...)` modifies the `Calendar` object in place), so it carries forward the same sharing/defensive-copying concerns as `Date`, and like `Date`, it has been effectively superseded by `java.time`'s much cleaner, immutable design.

Recognize `Calendar` when reading or maintaining pre-Java-8 code that needs calendar-field access or date arithmetic, being especially careful about the zero-based month indexing pitfall; for any new code, use `java.time.LocalDate`/`LocalDateTime` (which use intuitive, one-based months) and their `plusDays`/`plusMonths`/etc. methods instead, which are immutable and considerably clearer to use correctly.

## 3. Core concept

```java
import java.util.Calendar;

public class CalendarCore {
    public static void main(String[] args) {
        Calendar cal = Calendar.getInstance();
        cal.set(2024, Calendar.DECEMBER, 31); // using the Calendar.DECEMBER constant avoids the zero-based pitfall

        cal.add(Calendar.DAY_OF_MONTH, 1); // add one day, crossing into a new year and month

        System.out.println("Year: " + cal.get(Calendar.YEAR));                    // 2025
        System.out.println("Month (0-based): " + cal.get(Calendar.MONTH));         // 0 (January)
        System.out.println("Day: " + cal.get(Calendar.DAY_OF_MONTH));               // 1
    }
}
```

Using named constants like `Calendar.DECEMBER` (rather than the raw number `11`) when *setting* a month makes the zero-based indexing explicit and self-documenting; `cal.add(Calendar.DAY_OF_MONTH, 1)` correctly rolls December 31st, 2024 over into January 1st, 2025 — properly handling both the month and year rollover automatically, which is exactly the calendar-aware arithmetic `Calendar` was designed to provide over manually manipulating a raw millisecond count.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calendar getInstance returns a mutable calendar object, get and set access individual fields with month being notoriously zero based, add performs calendar aware arithmetic correctly handling month and year rollovers">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="220" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="150" y="42" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">Calendar.getInstance()</text>

  <rect x="330" y="20" width="230" height="35" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="445" y="42" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">cal.get(Calendar.MONTH) — 0-based!</text>

  <rect x="150" y="80" width="300" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="102" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">cal.add(field, amount) — handles rollovers</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Correct calendar arithmetic, but zero-based months are a notorious, well-documented pitfall.</text>
</svg>

`Calendar` provides calendar-aware arithmetic, but its zero-based month indexing is a widely-known source of bugs.

## 5. Runnable example

Scenario: a small booking system computing dates using `Calendar`, evolved from basic field access into arithmetic across month/year boundaries, then hardened with an explicit demonstration of the zero-based month pitfall and how to guard against it.

### Level 1 — Basic

```java
import java.util.Calendar;

public class CalendarBasic {
    public static void main(String[] args) {
        Calendar cal = Calendar.getInstance();
        cal.set(2024, Calendar.JUNE, 15); // June 15, 2024 — using the named constant, not a raw '5'

        System.out.println("Year: " + cal.get(Calendar.YEAR));
        System.out.println("Month (0-based): " + cal.get(Calendar.MONTH)); // 5, since JUNE == 5
        System.out.println("Day: " + cal.get(Calendar.DAY_OF_MONTH));
    }
}
```

**How to run:** `java CalendarBasic.java`

`Calendar.JUNE` is the constant `5` (zero-based: January is `0`, so June, the sixth month, is index `5`) — using the named constant instead of a raw number avoids needing to remember this offset manually.

### Level 2 — Intermediate

Same booking idea, now performing date arithmetic that crosses a month boundary, demonstrating `Calendar`'s correct handling of varying month lengths.

```java
import java.util.Calendar;

public class CalendarIntermediate {
    static Calendar addBusinessDays(Calendar start, int days) {
        Calendar result = (Calendar) start.clone(); // Calendar supports clone() -- avoids mutating the original
        result.add(Calendar.DAY_OF_MONTH, days);
        return result;
    }

    public static void main(String[] args) {
        Calendar bookingDate = Calendar.getInstance();
        bookingDate.set(2024, Calendar.JANUARY, 28); // Jan 28, 2024 (a leap year)

        Calendar checkOut = addBusinessDays(bookingDate, 5); // crosses into February

        System.out.println("Booking: " + (bookingDate.get(Calendar.MONTH) + 1) + "/" + bookingDate.get(Calendar.DAY_OF_MONTH));
        System.out.println("Checkout: " + (checkOut.get(Calendar.MONTH) + 1) + "/" + checkOut.get(Calendar.DAY_OF_MONTH));
    }
}
```

**How to run:** `java CalendarIntermediate.java`

`(Calendar) start.clone()` creates an independent copy before mutating it with `.add(...)`, since `Calendar` is mutable and modifying it directly would corrupt the original `bookingDate` (exactly the same defensive-copying concern that applied to `Date`); note the `+ 1` when printing months, converting back from the zero-based internal representation to the familiar one-based form for display.

### Level 3 — Advanced

Same booking system, now demonstrating the zero-based month pitfall as a real, concrete bug: constructing a date using a raw numeric month value (forgetting the zero-based offset) versus the correct, named-constant approach — side by side, showing exactly how the mistake manifests.

```java
import java.util.Calendar;

public class CalendarAdvanced {
    public static void main(String[] args) {
        // BUGGY: using raw "12" intending December, but Calendar.set treats 12 as month index 12 (a 13th month!)
        Calendar buggy = Calendar.getInstance();
        buggy.set(2024, 12, 25); // intended: December 25 -- but 12 is actually the 13th zero-indexed month!

        // CORRECT: using the named constant, which is exactly 11 for December
        Calendar correct = Calendar.getInstance();
        correct.set(2024, Calendar.DECEMBER, 25);

        System.out.println("Buggy result -> Year: " + buggy.get(Calendar.YEAR)
            + ", Month(0-based): " + buggy.get(Calendar.MONTH)
            + ", Day: " + buggy.get(Calendar.DAY_OF_MONTH));

        System.out.println("Correct result -> Year: " + correct.get(Calendar.YEAR)
            + ", Month(0-based): " + correct.get(Calendar.MONTH)
            + ", Day: " + correct.get(Calendar.DAY_OF_MONTH));
    }
}
```

**How to run:** `java CalendarAdvanced.java`

Passing `12` directly to `set(2024, 12, 25)` doesn't throw an error — `Calendar` interprets month index `12` as one past December (index `11`), silently rolling over into January of the *following* year (`2025`) instead of December of the intended year; `Calendar.DECEMBER` (the correct constant, equal to `11`) produces the intended date exactly — this side-by-side comparison demonstrates precisely why relying on raw numeric month values is a well-documented, real bug pattern with this API.

## 6. Walkthrough

Trace both `set(...)` calls in `CalendarAdvanced.main` and their resulting field values.

**`buggy.set(2024, 12, 25)`.** `Calendar.set(year, month, day)` treats `month` as zero-based internally. Passing `12` means "the 13th month" (since `0` is January through `11` is December) — `Calendar` handles this by rolling over: month `12` becomes January (`0`) of the *next* year. So `buggy` actually ends up representing January 25, **2025**, not December 25, 2024 as likely intended.

**`correct.set(2024, Calendar.DECEMBER, 25)`.** `Calendar.DECEMBER` evaluates to `11` (the correct zero-based index for December, the twelfth month). `correct` ends up representing December 25, 2024, exactly as intended.

**Printing `buggy`'s fields.** `buggy.get(Calendar.YEAR)` is `2025` (rolled over). `buggy.get(Calendar.MONTH)` is `0` (January, zero-based). `buggy.get(Calendar.DAY_OF_MONTH)` is `25`.

**Printing `correct`'s fields.** `correct.get(Calendar.YEAR)` is `2024` (as intended). `correct.get(Calendar.MONTH)` is `11` (December, zero-based). `correct.get(Calendar.DAY_OF_MONTH)` is `25`.

```
buggy.set(2024, 12, 25):
  month index 12 is "one past December" -> rolls over -> January (0) of year 2025
  -> Year=2025, Month=0, Day=25  (WRONG: intended December 2024, got January 2025)

correct.set(2024, Calendar.DECEMBER, 25):
  Calendar.DECEMBER = 11 (correct zero-based index)
  -> Year=2024, Month=11, Day=25  (CORRECT: December 2024, as intended)
```

**Final output.**
```
Buggy result -> Year: 2025, Month(0-based): 0, Day: 25
Correct result -> Year: 2024, Month(0-based): 11, Day: 25
```
This demonstrates concretely why passing a raw numeric month value to `Calendar.set` is a genuine, easy-to-make mistake: `12`, which looks like it should mean "December" to anyone thinking in ordinary one-based months, actually silently produces a date in an entirely different year, with no exception or warning of any kind.

## 7. Gotchas & takeaways

> **`Calendar`'s month field is zero-based (January is `0`, December is `11`), and passing an out-of-range value like `12` does not throw an exception — it silently rolls over into the next year's January instead**, exactly as `CalendarAdvanced` demonstrated. Always use the named constants (`Calendar.JANUARY` through `Calendar.DECEMBER`) rather than raw numeric literals when setting or comparing month values, to make the zero-based indexing explicit and avoid this well-documented, easy-to-make mistake.

> **Like `Date`, `Calendar` is mutable, so sharing a `Calendar` reference (rather than cloning it, as `addBusinessDays` did) risks the same kind of silent data corruption bug the `Date` topic demonstrated** — always `clone()` (or otherwise defensively copy) a `Calendar` before performing arithmetic on it if the original must remain unmodified elsewhere.

- `java.util.Calendar` (typically obtained via `Calendar.getInstance()`) provides calendar-field access (`get`/`set`) and calendar-aware arithmetic (`add`), correctly handling month/year rollovers that raw millisecond manipulation would not.
- `Calendar`'s month field is zero-based (January is `0`), a notorious, well-documented source of off-by-one bugs — always use the named month constants rather than raw numbers.
- `Calendar` is mutable, exactly like `Date`, requiring the same defensive-copying discipline (via `clone()`) when sharing or storing instances that must not be unexpectedly modified elsewhere.
- Modern code should prefer `java.time.LocalDate`/`LocalDateTime` (with intuitive one-based months and immutable, `plusDays`/`plusMonths`-style arithmetic) over `Calendar` entirely for any new development.
