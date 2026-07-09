---
card: java
gi: 550
slug: temporaladjusters
title: TemporalAdjusters
---

## 1. What it is

`TemporalAdjusters` is a utility class providing ready-made adjustment strategies for date values — "the first day of this month," "the next Monday," "the last day of the year," "the third Wednesday of this month." Each adjuster is applied through `LocalDate.with(adjuster)`, and the class also supports writing entirely custom adjustment logic via `TemporalAdjusters.ofDateAdjuster(...)` for rules the built-in set doesn't cover.

## 2. Why & when

Computing "the next Friday" or "the last day of this month" by hand means writing repetitive, easy-to-get-wrong logic involving month lengths, day-of-week arithmetic, and leap years. `TemporalAdjusters` provides these as pre-built, well-tested strategies — `firstDayOfMonth()`, `lastDayOfMonth()`, `next(DayOfWeek)`, `nextOrSame(DayOfWeek)`, `dayOfWeekInMonth(ordinal, dayOfWeek)`, and several more — turning a whole class of fiddly calendar math into a single, readable method call.

## 3. Core concept

```java
import java.time.*;
import java.time.temporal.*;

LocalDate today = LocalDate.of(2026, 7, 9); // a Thursday

LocalDate firstOfMonth = today.with(TemporalAdjusters.firstDayOfMonth()); // 2026-07-01
LocalDate lastOfMonth = today.with(TemporalAdjusters.lastDayOfMonth());   // 2026-07-31
LocalDate nextMonday = today.with(TemporalAdjusters.next(DayOfWeek.MONDAY)); // 2026-07-13
LocalDate lastFridayOfMonth = today.with(TemporalAdjusters.lastInMonth(DayOfWeek.FRIDAY)); // 2026-07-31
```

`date.with(adjuster)` applies the adjustment strategy, returning a new `LocalDate` (or other temporal type) computed according to that specific rule — the calendar math is entirely handled internally by the adjuster.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="TemporalAdjusters compute a new date according to a named rule, applied via LocalDate.with">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">2026-07-09</text>
  <text x="270" y="40" fill="#8b949e" font-size="10" font-family="sans-serif">.with(next(MONDAY))</text>
  <line x1="190" y1="35" x2="360" y2="35" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowTA)"/>
  <rect x="370" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="445" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">2026-07-13</text>
  <text x="20" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">The next Monday after a Thursday, correctly computed without manual day-of-week arithmetic.</text>
  <defs><marker id="arrowTA" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`next(DayOfWeek.MONDAY)` computes the correct target date, handling the day-of-week arithmetic internally.

## 5. Runnable example

Scenario: computing key dates for a monthly billing and reporting system — evolved from basic built-in adjusters, through combining several adjusters for a reporting schedule, to a version writing a custom adjuster for a business rule the built-in set doesn't directly cover.

### Level 1 — Basic

```java
import java.time.*;
import java.time.temporal.*;

public class TemporalAdjustersBasic {
    public static void main(String[] args) {
        LocalDate today = LocalDate.of(2026, 7, 9);

        LocalDate firstOfMonth = today.with(TemporalAdjusters.firstDayOfMonth());
        LocalDate lastOfMonth = today.with(TemporalAdjusters.lastDayOfMonth());
        LocalDate firstOfNextMonth = today.with(TemporalAdjusters.firstDayOfNextMonth());

        System.out.println("Today: " + today);
        System.out.println("First of month: " + firstOfMonth);
        System.out.println("Last of month: " + lastOfMonth);
        System.out.println("First of next month: " + firstOfNextMonth);
    }
}
```

**How to run:** `java TemporalAdjustersBasic.java`

Expected output:
```
Today: 2026-07-09
First of month: 2026-07-01
Last of month: 2026-07-31
First of next month: 2026-08-01
```

Each adjuster computes a related date from `today` without any manual day-counting: `firstDayOfMonth()` and `lastDayOfMonth()` correctly find July's boundaries (`31` days), and `firstDayOfNextMonth()` correctly rolls into August — all handled by the adjuster's internal logic, not by the caller working out month lengths by hand.

### Level 2 — Intermediate

```java
import java.time.*;
import java.time.temporal.*;

public class TemporalAdjustersScheduling {
    public static void main(String[] args) {
        LocalDate today = LocalDate.of(2026, 7, 9); // a Thursday

        // Reporting schedule: reports run every Monday, and a summary runs on the last Friday of each month.
        LocalDate nextMonday = today.with(TemporalAdjusters.next(DayOfWeek.MONDAY));
        LocalDate nextOrSameMonday = today.with(TemporalAdjusters.nextOrSame(DayOfWeek.MONDAY));
        LocalDate lastFridayOfMonth = today.with(TemporalAdjusters.lastInMonth(DayOfWeek.FRIDAY));

        System.out.println("Today: " + today + " (" + today.getDayOfWeek() + ")");
        System.out.println("Next Monday: " + nextMonday);
        System.out.println("Next-or-same Monday: " + nextOrSameMonday);
        System.out.println("Last Friday of the month: " + lastFridayOfMonth);
    }
}
```

**How to run:** `java TemporalAdjustersScheduling.java`

Expected output:
```
Today: 2026-07-09 (THURSDAY)
Next Monday: 2026-07-13
Next-or-same Monday: 2026-07-13
Last Friday of the month: 2026-07-31
```

The real-world concern this adds: `next(DayOfWeek.MONDAY)` and `nextOrSame(DayOfWeek.MONDAY)` behave identically here (`13th`), since today (Thursday) isn't itself a Monday — the distinction only matters when the starting date *is already* the target day-of-week (`next` would skip forward a full week, `nextOrSame` would return the starting date itself unchanged). `lastInMonth(DayOfWeek.FRIDAY)` correctly identifies July 31, 2026 as the month's final Friday, requiring no manual reasoning about which day-of-week the month happens to end on.

### Level 3 — Advanced

```java
import java.time.*;
import java.time.temporal.*;

public class TemporalAdjustersCustom {
    // Custom rule: the next business day (skipping weekends) after a given date.
    static TemporalAdjuster nextBusinessDay() {
        return TemporalAdjusters.ofDateAdjuster(date -> {
            LocalDate next = date.plusDays(1);
            while (next.getDayOfWeek() == DayOfWeek.SATURDAY || next.getDayOfWeek() == DayOfWeek.SUNDAY) {
                next = next.plusDays(1);
            }
            return next;
        });
    }

    public static void main(String[] args) {
        LocalDate friday = LocalDate.of(2026, 7, 10);   // a Friday
        LocalDate saturday = LocalDate.of(2026, 7, 11);  // a Saturday
        LocalDate wednesday = LocalDate.of(2026, 7, 8);  // a Wednesday

        System.out.println("Friday (" + friday.getDayOfWeek() + ") -> next business day: " + friday.with(nextBusinessDay()));
        System.out.println("Saturday (" + saturday.getDayOfWeek() + ") -> next business day: " + saturday.with(nextBusinessDay()));
        System.out.println("Wednesday (" + wednesday.getDayOfWeek() + ") -> next business day: " + wednesday.with(nextBusinessDay()));
    }
}
```

**How to run:** `java TemporalAdjustersCustom.java`

Expected output:
```
Friday (FRIDAY) -> next business day: 2026-07-13
Saturday (SATURDAY) -> next business day: 2026-07-13
Wednesday (WEDNESDAY) -> next business day: 2026-07-09
```

This writes a **custom** adjuster using `TemporalAdjusters.ofDateAdjuster(...)`, since "the next business day, skipping weekends" isn't among the built-in strategies. The lambda takes the current `LocalDate`, advances by one day, and loops while that day falls on a weekend, effectively skipping over `Saturday`/`Sunday` entirely. Starting from Friday, July 10th, the next business day correctly skips the weekend and lands on Monday, July 13th — the same result whether starting from Friday itself or from Saturday, since both need to skip past the same weekend.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `friday`, `saturday`, and `wednesday` are three specific dates for testing the custom adjuster.

`friday.with(nextBusinessDay())` applies the custom adjuster to `2026-07-10` (a Friday). Inside the adjuster's lambda, `next = date.plusDays(1)` computes `2026-07-11` (Saturday). The `while` loop checks: `next.getDayOfWeek() == SATURDAY` is `true`, so the loop body runs: `next = next.plusDays(1)` computes `2026-07-12` (Sunday). The loop checks again: `next.getDayOfWeek() == SUNDAY` is `true`, loop body runs again: `next = next.plusDays(1)` computes `2026-07-13` (Monday). The loop checks a third time: `next.getDayOfWeek()` is now `MONDAY`, neither `SATURDAY` nor `SUNDAY`, so the `while` condition is `false` and the loop exits. The adjuster returns `2026-07-13`.

`saturday.with(nextBusinessDay())` applies the adjuster to `2026-07-11` (Saturday) directly. `next = date.plusDays(1)` computes `2026-07-12` (Sunday). The loop checks: `SUNDAY`, `true`, advances to `2026-07-13` (Monday). The loop checks again: `MONDAY`, `false`, exits. Returns `2026-07-13` — the same result as starting from Friday, since both dates need to skip past the identical weekend.

```
friday (Jul 10, FRI):    +1 -> Jul 11 (SAT, skip) -> +1 -> Jul 12 (SUN, skip) -> +1 -> Jul 13 (MON, stop) -> Jul 13
saturday (Jul 11, SAT):  +1 -> Jul 12 (SUN, skip) -> +1 -> Jul 13 (MON, stop) -> Jul 13
wednesday (Jul 8, WED):  +1 -> Jul 9 (THU, stop, not a weekend day) -> Jul 9
```

`wednesday.with(nextBusinessDay())` applies the adjuster to `2026-07-08` (Wednesday). `next = date.plusDays(1)` computes `2026-07-09` (Thursday). The loop checks: `THURSDAY` is neither `SATURDAY` nor `SUNDAY`, so the condition is `false` immediately — the loop never executes its body. The adjuster returns `2026-07-09` directly, since the very next calendar day already happens to be a business day, requiring no skipping at all.

`main` prints all three results: `"Friday (FRIDAY) -> next business day: 2026-07-13"`, `"Saturday (SATURDAY) -> next business day: 2026-07-13"`, `"Wednesday (WEDNESDAY) -> next business day: 2026-07-09"` — demonstrating the custom adjuster correctly handles both the weekend-skipping case and the simple, no-skip case identically well.

## 7. Gotchas & takeaways

> `TemporalAdjusters.next(dayOfWeek)` and `nextOrSame(dayOfWeek)` (and similarly `previous`/`previousOrSame`) behave identically *except* when the starting date is already the target day-of-week — `next` always moves forward at least one full week in that case, while `nextOrSame` returns the starting date unchanged. Choosing the wrong one of this pair is a common, subtle bug source when the starting date could coincidentally already be the target day.

- `TemporalAdjusters` provides ready-made, well-tested calendar computation strategies, applied via `date.with(adjuster)`.
- Built-in adjusters cover common needs: `firstDayOfMonth()`, `lastDayOfMonth()`, `next(dayOfWeek)`, `nextOrSame(dayOfWeek)`, `lastInMonth(dayOfWeek)`, and several others.
- `next(dayOfWeek)` versus `nextOrSame(dayOfWeek)` differ specifically when the starting date already matches the target day — always double-check which behavior a given use case actually needs.
- `TemporalAdjusters.ofDateAdjuster(function)` (or the more general `TemporalAdjuster` functional interface) lets you write entirely custom adjustment logic for rules the built-in set doesn't directly provide, such as "the next business day."
- Encapsulating calendar computation logic behind a `TemporalAdjuster` keeps it reusable and testable in isolation, rather than scattering the same day-of-week/month-length arithmetic across multiple call sites.
