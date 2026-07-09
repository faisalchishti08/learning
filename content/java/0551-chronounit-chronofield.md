---
card: java
gi: 551
slug: chronounit-chronofield
title: ChronoUnit & ChronoField
---

## 1. What it is

`ChronoUnit` is an enum of standard time units — `DAYS`, `HOURS`, `MONTHS`, `YEARS`, and many others — used primarily with `.between(start, end)` to measure elapsed time in a specific unit, and with `.plus`/`.minus` style operations that take a unit as a parameter. `ChronoField` is an enum of standard calendar/time *fields* — `DAY_OF_WEEK`, `MONTH_OF_YEAR`, `HOUR_OF_DAY`, and others — used to extract or set a specific component of a temporal value via `.get(field)` or `.with(field, value)`. The distinction: `ChronoUnit` measures a *span* between two points; `ChronoField` accesses a *component* of one point.

## 2. Why & when

These two enums provide a generic, uniform way to work with time units and fields across every `java.time` type, rather than needing type-specific methods for every possible measurement or extraction. `ChronoUnit.between(...)` works the same way whether you're measuring days between two `LocalDate`s or minutes between two `Instant`s — one consistent API. `ChronoField` similarly lets you extract "the day of the week" or "the hour of the day" generically, useful especially when writing code that needs to work across multiple different temporal types without type-specific branching.

## 3. Core concept

```java
import java.time.*;
import java.time.temporal.*;

LocalDate start = LocalDate.of(2026, 1, 1);
LocalDate end = LocalDate.of(2026, 12, 31);

long daysBetween = ChronoUnit.DAYS.between(start, end);   // 364
long monthsBetween = ChronoUnit.MONTHS.between(start, end); // 11

LocalDateTime dateTime = LocalDateTime.of(2026, 7, 9, 14, 30);
int dayOfWeek = dateTime.get(ChronoField.DAY_OF_WEEK);   // 4 (Thursday, ISO: Monday=1)
int hourOfDay = dateTime.get(ChronoField.HOUR_OF_DAY);   // 14

LocalDateTime adjusted = dateTime.with(ChronoField.HOUR_OF_DAY, 9); // change just the hour to 9
```

`ChronoUnit.between(a, b)` measures elapsed time in a chosen unit; `temporal.get(field)`/`.with(field, value)` extract or set a specific component of a single temporal value.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ChronoUnit measures the span between two points; ChronoField accesses a component of one point">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="95" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">2026-01-01</text>
  <text x="270" y="40" fill="#8b949e" font-size="10" font-family="sans-serif">ChronoUnit.DAYS.between</text>
  <line x1="160" y1="35" x2="380" y2="35" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arrowCU)"/>
  <rect x="390" y="20" width="130" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="455" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">2026-12-31</text>
  <text x="20" y="65" fill="#6db33f" font-size="10" font-family="sans-serif">-&gt; 364 days (a SPAN between two points)</text>

  <rect x="30" y="90" width="200" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="130" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">.get(ChronoField.HOUR_OF_DAY)</text>
  <text x="20" y="105" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif"></text>
  <text x="260" y="110" fill="#6db33f" font-size="10" font-family="sans-serif">-&gt; 14 (a COMPONENT of one point)</text>
  <defs><marker id="arrowCU" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`ChronoUnit` measures the gap between two temporal values; `ChronoField` reads or writes one specific component of a single temporal value.

## 5. Runnable example

Scenario: building a report that measures project timelines and extracts calendar components for scheduling logic — evolved from basic `ChronoUnit.between` usage, through `ChronoField` extraction for a scheduling rule, to a version combining both in a single, generic reporting function that works across multiple temporal types.

### Level 1 — Basic

```java
import java.time.*;
import java.time.temporal.*;

public class ChronoUnitBasic {
    public static void main(String[] args) {
        LocalDate projectStart = LocalDate.of(2026, 1, 15);
        LocalDate projectEnd = LocalDate.of(2026, 6, 30);

        long totalDays = ChronoUnit.DAYS.between(projectStart, projectEnd);
        long totalWeeks = ChronoUnit.WEEKS.between(projectStart, projectEnd);
        long totalMonths = ChronoUnit.MONTHS.between(projectStart, projectEnd);

        System.out.println("Total days: " + totalDays);
        System.out.println("Total weeks: " + totalWeeks);
        System.out.println("Total months: " + totalMonths);
    }
}
```

**How to run:** `java ChronoUnitBasic.java`

Expected output:
```
Total days: 166
Total weeks: 23
Total months: 5
```

`ChronoUnit.DAYS.between(...)`, `.WEEKS.between(...)`, and `.MONTHS.between(...)` all measure the same underlying gap between `projectStart` and `projectEnd`, just expressed in different units — `166` days, which is `23` complete weeks (with a small remainder, since `ChronoUnit.WEEKS` reports only *complete* weeks), and `5` complete months.

### Level 2 — Intermediate

```java
import java.time.*;
import java.time.temporal.*;

public class ChronoFieldBasic {
    public static void main(String[] args) {
        LocalDateTime meetingTime = LocalDateTime.of(2026, 7, 9, 14, 30);

        int dayOfWeek = meetingTime.get(ChronoField.DAY_OF_WEEK); // ISO: Monday=1 ... Sunday=7
        int hourOfDay = meetingTime.get(ChronoField.HOUR_OF_DAY);
        int dayOfMonth = meetingTime.get(ChronoField.DAY_OF_MONTH);

        System.out.println("Day of week (ISO, Mon=1): " + dayOfWeek);
        System.out.println("Hour of day: " + hourOfDay);
        System.out.println("Day of month: " + dayOfMonth);

        boolean isBusinessHours = hourOfDay >= 9 && hourOfDay < 17;
        boolean isWeekday = dayOfWeek >= 1 && dayOfWeek <= 5;
        System.out.println("Scheduled during business hours on a weekday: " + (isBusinessHours && isWeekday));
    }
}
```

**How to run:** `java ChronoFieldBasic.java`

Expected output:
```
Day of week (ISO, Mon=1): 4
Hour of day: 14
Day of month: 9
Scheduled during business hours on a weekday: true
```

The real-world concern this adds: extracting individual calendar/time *components* for scheduling logic. `ChronoField.DAY_OF_WEEK` returns `4` for July 9, 2026 (a Thursday, since ISO numbering starts Monday as `1`). Combining `HOUR_OF_DAY` (`14`, i.e. `2` PM) and `DAY_OF_WEEK` (`4`, a weekday) lets a scheduling check confirm this meeting falls within business hours on a weekday, entirely through generic field extraction rather than type-specific methods like `.getDayOfWeek()` (which, while more idiomatic for `LocalDateTime` specifically, doesn't generalize the same way across different temporal types).

### Level 3 — Advanced

```java
import java.time.*;
import java.time.temporal.*;

public class ChronoGenericReport {
    // Generic function: works with ANY Temporal type supporting the needed unit/field, via the common interfaces.
    static <T extends Temporal> String describeSpan(T start, T end, ChronoUnit unit) {
        long amount = unit.between(start, end);
        return amount + " " + unit.toString().toLowerCase();
    }

    public static void main(String[] args) {
        LocalDate dateStart = LocalDate.of(2026, 1, 1);
        LocalDate dateEnd = LocalDate.of(2026, 7, 9);

        LocalDateTime timeStart = LocalDateTime.of(2026, 7, 9, 9, 0);
        LocalDateTime timeEnd = LocalDateTime.of(2026, 7, 9, 17, 30);

        Instant instantStart = Instant.parse("2026-07-09T00:00:00Z");
        Instant instantEnd = Instant.parse("2026-07-09T12:45:30Z");

        // The SAME generic function, applied to three DIFFERENT temporal types.
        System.out.println("Date span: " + describeSpan(dateStart, dateEnd, ChronoUnit.DAYS));
        System.out.println("Time span: " + describeSpan(timeStart, timeEnd, ChronoUnit.MINUTES));
        System.out.println("Instant span: " + describeSpan(instantStart, instantEnd, ChronoUnit.SECONDS));
    }
}
```

**How to run:** `java ChronoGenericReport.java`

Expected output:
```
Date span: 189 days
Time span: 510 minutes
Instant span: 45930 seconds
```

This demonstrates `ChronoUnit`'s real generality: `describeSpan(...)` is written **once**, generically over `Temporal` (the common interface `LocalDate`, `LocalDateTime`, and `Instant` all implement), and works correctly regardless of which specific temporal type it's given — `ChronoUnit.DAYS.between(...)` on two `LocalDate`s, `ChronoUnit.MINUTES.between(...)` on two `LocalDateTime`s, and `ChronoUnit.SECONDS.between(...)` on two `Instant`s all flow through the exact same generic code path, since `ChronoUnit.between(...)` itself is designed to work uniformly across any compatible `Temporal` type.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Three pairs of temporal values are defined: `LocalDate`s six months apart, `LocalDateTime`s within the same day roughly `8.5` hours apart, and `Instant`s within the same day about `12.75` hours apart.

`describeSpan(dateStart, dateEnd, ChronoUnit.DAYS)` is called. Inside, `unit.between(start, end)` invokes `ChronoUnit.DAYS.between(dateStart, dateEnd)` — internally, `ChronoUnit` delegates to the specific temporal type's own supported-unit logic, computing the calendar day difference between `2026-01-01` and `2026-07-09`: `189` days (accounting for January's `31`, February's `28`, March's `31`, April's `30`, May's `31`, June's `30`, plus `9` days into July). The method returns `"189 days"`.

`describeSpan(timeStart, timeEnd, ChronoUnit.MINUTES)` is called next. `ChronoUnit.MINUTES.between(timeStart, timeEnd)` computes the minute difference between `2026-07-09T09:00` and `2026-07-09T17:30`: that's `8` hours and `30` minutes, i.e. `8 * 60 + 30 = 510` minutes. The method returns `"510 minutes"`.

`describeSpan(instantStart, instantEnd, ChronoUnit.SECONDS)` is called last. `ChronoUnit.SECONDS.between(instantStart, instantEnd)` computes the second difference between `2026-07-09T00:00:00Z` and `2026-07-09T12:45:30Z`: that's `12` hours, `45` minutes, and `30` seconds total, i.e. `12*3600 + 45*60 + 30 = 43200 + 2700 + 30 = 45930` seconds. The method returns `"45930 seconds"`.

```
describeSpan(LocalDate, LocalDate, DAYS)      -> ChronoUnit.DAYS.between(...)    -> 189 (calendar days)
describeSpan(LocalDateTime, LocalDateTime, MINUTES) -> ChronoUnit.MINUTES.between(...) -> 510 (8h30m)
describeSpan(Instant, Instant, SECONDS)        -> ChronoUnit.SECONDS.between(...) -> 45930 (12h45m30s)

Same generic function, same ChronoUnit.between(...) call pattern, three different Temporal types.
```

`main` prints all three results: `"Date span: 189 days"`, `"Time span: 510 minutes"`, `"Instant span: 45930 seconds"` — demonstrating that `ChronoUnit`'s uniform `.between(...)` contract lets a single piece of generic code correctly measure spans across entirely different `java.time` types, without any type-specific branching logic needed inside `describeSpan` itself.

## 7. Gotchas & takeaways

> Not every `ChronoUnit` is supported by every temporal type — attempting `ChronoUnit.YEARS.between(...)` on two `Instant`s (which have no inherent notion of a calendar year) throws `UnsupportedTemporalTypeException`, since `Instant` only supports time-based units (seconds, nanoseconds and coarser), not calendar-based ones. Similarly, `ChronoField.DAY_OF_WEEK` doesn't apply to a value with no date component at all. Always confirm the unit or field you're using is actually meaningful for the specific temporal type at hand.

- `ChronoUnit` (an enum: `DAYS`, `HOURS`, `MONTHS`, `YEARS`, and more) measures elapsed time between two temporal values via `.between(start, end)`.
- `ChronoField` (an enum: `DAY_OF_WEEK`, `HOUR_OF_DAY`, `MONTH_OF_YEAR`, and more) extracts or sets a specific component of one temporal value via `.get(field)`/`.with(field, value)`.
- Both provide a uniform interface across different `java.time` types, letting generic code (like `describeSpan` in Level 3) work correctly with `LocalDate`, `LocalDateTime`, `Instant`, and others without type-specific branching.
- Not every unit or field is meaningful for every temporal type — calendar-based units/fields don't apply to `Instant` (no calendar concept), and attempting to use them throws `UnsupportedTemporalTypeException`.
- `ChronoField`'s `DAY_OF_WEEK` uses ISO numbering (Monday = `1` through Sunday = `7`), distinct from some other date libraries' conventions — always verify the numbering convention when working with day-of-week values.
