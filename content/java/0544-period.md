---
card: java
gi: 544
slug: period
title: Period
---

## 1. What it is

`Period` represents a calendar-based amount of time in years, months, and days — "1 month," "2 years and 3 months," "10 days" — as opposed to `Duration` (see [[duration]]), which measures a fixed, exact number of seconds. The key distinction: a `Period` of "1 month" means "the same day next month," regardless of whether that month has 28, 29, 30, or 31 days — its actual length in elapsed time varies depending on which dates it's applied to.

## 2. Why & when

Use `Period` whenever you're thinking in genuinely calendar terms — a subscription that renews "monthly" (on the same day-of-month each time), an employee's tenure in "years and months," an age calculation, a warranty that lasts "2 years." Because `Period` operates on `LocalDate` and understands calendar rules (varying month lengths, leap years), it correctly handles "add one month to January 31st" or "how many full years between these two birthdates" in ways that a fixed-second `Duration` fundamentally cannot express.

## 3. Core concept

```java
import java.time.*;

Period oneMonth = Period.ofMonths(1);
Period combined = Period.of(1, 2, 15); // 1 year, 2 months, 15 days

LocalDate start = LocalDate.of(2026, 1, 31);
LocalDate later = start.plus(oneMonth); // 2026-02-28 -- clamped, since Feb has no 31st

LocalDate birthDate = LocalDate.of(1990, 6, 15);
LocalDate today = LocalDate.of(2026, 7, 9);
Period age = Period.between(birthDate, today); // years, months, days between the two dates
System.out.println(age.getYears() + " years, " + age.getMonths() + " months");
```

`Period` is built with `of*` factory methods or measured between two `LocalDate`s with `Period.between(...)`, and — unlike `Duration` — always respects calendar rules like variable month lengths.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Period measures calendar-based time in years, months, and days, respecting variable month lengths">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="150" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2026-01-31</text>
  <text x="270" y="42" fill="#8b949e" font-size="10" font-family="sans-serif">.plus(Period.ofMonths(1))</text>
  <line x1="190" y1="37" x2="390" y2="37" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowPE)"/>
  <rect x="400" y="20" width="150" height="35" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="475" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2026-02-28</text>
  <text x="20" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">"1 month" clamps to Feb's actual last day -- calendar-aware, unlike a fixed-second Duration.</text>
  <defs><marker id="arrowPE" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Period.ofMonths(1)` applied to January 31st correctly clamps to February's last actual day — calendar semantics, not a fixed elapsed-time span.

## 5. Runnable example

Scenario: calculating a person's exact age and tracking a subscription's monthly renewal dates — evolved from basic `Period` construction and application, through computing age in years/months/days, to a version handling subscription renewals across varying month lengths correctly.

### Level 1 — Basic

```java
import java.time.*;

public class PeriodBasic {
    public static void main(String[] args) {
        LocalDate subscriptionStart = LocalDate.of(2026, 1, 15);
        Period oneMonth = Period.ofMonths(1);

        LocalDate firstRenewal = subscriptionStart.plus(oneMonth);
        LocalDate secondRenewal = firstRenewal.plus(oneMonth);

        System.out.println("Start: " + subscriptionStart);
        System.out.println("First renewal: " + firstRenewal);
        System.out.println("Second renewal: " + secondRenewal);
    }
}
```

**How to run:** `java PeriodBasic.java`

Expected output:
```
Start: 2026-01-15
First renewal: 2026-02-15
Second renewal: 2026-03-15
```

`Period.ofMonths(1)` applied via `.plus(...)` repeatedly advances the date by exactly one calendar month each time — since the `15`th exists in every month here, the day-of-month stays consistent across renewals, `15th` of each successive month.

### Level 2 — Intermediate

```java
import java.time.*;

public class PeriodBetween {
    public static void main(String[] args) {
        LocalDate birthDate = LocalDate.of(1990, 6, 15);
        LocalDate today = LocalDate.of(2026, 7, 9);

        Period age = Period.between(birthDate, today);

        System.out.println("Birth date: " + birthDate);
        System.out.println("Today: " + today);
        System.out.println("Age: " + age.getYears() + " years, " + age.getMonths() + " months, " + age.getDays() + " days");
    }
}
```

**How to run:** `java PeriodBetween.java`

Expected output:
```
Birth date: 1990-06-15
Today: 2026-07-09
Age: 36 years, 0 months, 24 days
```

The real-world concern this adds: `Period.between(birthDate, today)` computes a genuinely calendar-aware breakdown — from June 15, 1990 to July 9, 2026 is `36` full years (since June 15, 2026 has already passed relative to today), then counting forward from June 15, 2026: `0` additional full months (since it's not yet August 15) plus `24` days (from June 15 to July 9). This kind of "years, months, and days" breakdown is exactly what `Period` provides but `Duration` (a flat count of seconds) cannot express directly.

### Level 3 — Advanced

```java
import java.time.*;

public class PeriodMonthEndHandling {
    public static void main(String[] args) {
        // A subscription starting on the 31st -- a genuine edge case for monthly renewals.
        LocalDate start = LocalDate.of(2026, 1, 31);
        Period oneMonth = Period.ofMonths(1);

        LocalDate current = start;
        System.out.println("Start: " + current);
        for (int i = 0; i < 4; i++) {
            current = current.plus(oneMonth);
            System.out.println("Renewal " + (i + 1) + ": " + current);
        }
    }
}
```

**How to run:** `java PeriodMonthEndHandling.java`

Expected output:
```
Start: 2026-01-31
Renewal 1: 2026-02-28
Renewal 2: 2026-03-28
Renewal 3: 2026-04-28
Renewal 4: 2026-05-28
```

This exposes a real subtlety with repeated month-based `Period` arithmetic starting near month-end: `2026-01-31` plus one month clamps to `2026-02-28` (February's actual last day). But applying `Period.ofMonths(1)` *again* to `2026-02-28` does **not** "remember" the original `31st` — it simply advances by one month from `28`, landing on `2026-03-28`, not `2026-03-31`. This is a well-known, easy-to-miss subtlety: once a clamp happens, subsequent additions continue from the *clamped* day, not the original intended day, so a subscription starting on the 31st permanently drifts to the 28th after its first February renewal.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `start` is `2026-01-31`, `oneMonth` is `Period.ofMonths(1)`. `current` is initialized to `start`.

The loop's first iteration: `current.plus(oneMonth)` computes `2026-01-31` plus one month. The target month is February 2026, which has `28` days (not a leap year). Since day `31` doesn't exist in February, the result clamps to February's last valid day: `2026-02-28`. `current` is reassigned to this clamped value. Printed as `"Renewal 1: 2026-02-28"`.

The second iteration: `current.plus(oneMonth)` now operates on `2026-02-28` (the *clamped* value from the previous step, not the original `31`). The target month is March 2026, which has `31` days. Since `current`'s day-of-month is now `28` (not `31`, because that information was lost in the previous clamp), the result is simply `2026-03-28` — March does have a `28`th day, so no clamping is needed this time, but the date "forgot" it was ever supposed to represent the `31st`. `current` becomes `2026-03-28`. Printed as `"Renewal 2: 2026-03-28"`.

The third iteration: `current.plus(oneMonth)` operates on `2026-03-28`. April has `30` days, so `28` is valid, no clamping needed: `2026-04-28`. Printed as `"Renewal 3: 2026-04-28"`.

```
start = 2026-01-31

+1 month: target Feb (28 days), day 31 invalid -> CLAMP to 2026-02-28
+1 month: target Mar (31 days), day 28 (from clamped value) valid -> 2026-03-28  (permanently drifted from "31")
+1 month: target Apr (30 days), day 28 valid -> 2026-04-28
+1 month: target May (31 days), day 28 valid -> 2026-05-28
```

The fourth iteration continues the same pattern: `2026-04-28` plus one month lands on `2026-05-28` (May has `31` days, so `28` is valid, no clamping needed, but the date remains permanently at the `28th` rather than ever returning to the `31st`). Printed as `"Renewal 4: 2026-05-28"`. This demonstrates that a single clamping event early in a chain of repeated `Period` additions has a lasting effect on every subsequent date in the sequence, even in months that would have otherwise comfortably accommodated the original day.

## 7. Gotchas & takeaways

> Repeated `Period` additions do **not** remember an original day-of-month once a clamp has occurred — each `.plus(period)` call only ever looks at the *current* date's day-of-month, with no memory of what day the sequence originally started on. A subscription or recurring schedule starting near month-end (the 29th, 30th, or 31st) will permanently drift to an earlier day after its first clamping event, as demonstrated in Level 3. If exact day-of-month preservation matters, explicit logic (re-deriving the target day from the *original* start date each time, rather than chaining `.plus(...)` repeatedly from the previous result) is needed instead.

- `Period` represents a calendar-based time span (years, months, days), respecting variable month lengths and leap years — distinct from `Duration`'s fixed-second time spans.
- `Period.between(start, end)` computes a calendar-aware breakdown into years, months, and days — the natural tool for age calculations and similar "how long ago" questions phrased in calendar terms.
- `LocalDate.plus(period)` applies month/year addition with automatic day-of-month clamping when the target month is shorter than the original day requires.
- Chaining repeated `Period` additions from a previous result (rather than always re-deriving from the original date) can cause permanent day-of-month drift once a single clamping event occurs.
- For recurring schedules anchored to a specific day-of-month (like "the 31st of every month"), consider re-computing each occurrence from the original anchor date rather than repeatedly adding to the last computed date, to avoid the drift demonstrated in Level 3.
