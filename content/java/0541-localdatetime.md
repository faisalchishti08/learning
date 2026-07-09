---
card: java
gi: 541
slug: localdatetime
title: LocalDateTime
---

## 1. What it is

`LocalDateTime` combines `LocalDate` and `LocalTime` into a single value representing a date *and* a time-of-day, still with no timezone attached — "2026-07-09 at 14:30" but not tied to any particular timezone's interpretation of that moment. It's immutable like the rest of `java.time`, and it's built by combining a `LocalDate` and `LocalTime`, or constructed and manipulated directly with its own `of(...)`, `plus*`, and `minus*` methods.

## 2. Why & when

`LocalDateTime` is the right choice when you need both a date and a time together, but timezone genuinely doesn't matter for the use case — scheduling a local event that always happens at the same wall-clock time regardless of timezone conversions, timestamps in a system that only ever runs in one timezone, or representing "when" something is meant to happen from a purely calendar-and-clock perspective. The moment you need to reason about *when this actually happens in UTC*, or compare times across different timezones, `LocalDateTime` is the wrong tool — that's what `ZonedDateTime` or `Instant` (see [[instant]]) are for.

## 3. Core concept

```java
import java.time.*;

LocalDateTime now = LocalDateTime.now();
LocalDateTime specific = LocalDateTime.of(2026, 7, 9, 14, 30); // year, month, day, hour, minute
LocalDateTime combined = LocalDate.of(2026, 7, 9).atTime(LocalTime.of(14, 30)); // same result, built from parts

LocalDateTime later = specific.plusHours(3).plusDays(1); // chained, each returns a new instance

LocalDate justTheDate = specific.toLocalDate(); // 2026-07-09
LocalTime justTheTime = specific.toLocalTime(); // 14:30
```

`LocalDateTime` can be constructed directly with `of(...)`, or assembled by combining a `LocalDate` and `LocalTime` via `atTime(...)`/`atDate(...)` — and can be decomposed back into its `LocalDate`/`LocalTime` parts when only one component is needed.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LocalDateTime combines a LocalDate and a LocalTime into one value, with no timezone attached">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="140" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2026-07-09</text>
  <text x="200" y="42" fill="#8b949e" font-size="14" font-family="sans-serif">+</text>
  <rect x="220" y="20" width="100" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="270" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">14:30</text>
  <text x="360" y="42" fill="#8b949e" font-size="14" font-family="sans-serif">=</text>
  <rect x="390" y="20" width="220" height="35" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="500" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2026-07-09T14:30</text>
  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Still no timezone -- represents a "wall clock" date+time, not a globally unambiguous instant.</text>
</svg>

`LocalDate` and `LocalTime` combine into one `LocalDateTime`, printed in ISO-8601's `T`-separated format — still carrying no timezone information.

## 5. Runnable example

Scenario: scheduling a recurring local event and computing reminder times — evolved from basic construction and combination, through date/time arithmetic across a day boundary, to a version comparing two `LocalDateTime` values and computing the duration between them.

### Level 1 — Basic

```java
import java.time.*;

public class LocalDateTimeBasic {
    public static void main(String[] args) {
        LocalDateTime meetingTime = LocalDateTime.of(2026, 7, 9, 14, 30);

        System.out.println("Meeting scheduled: " + meetingTime);
        System.out.println("Date part: " + meetingTime.toLocalDate());
        System.out.println("Time part: " + meetingTime.toLocalTime());
    }
}
```

**How to run:** `java LocalDateTimeBasic.java`

Expected output:
```
Meeting scheduled: 2026-07-09T14:30
Date part: 2026-07-09
Time part: 14:30
```

`LocalDateTime.of(2026, 7, 9, 14, 30)` constructs a combined date-and-time value directly. `.toLocalDate()` and `.toLocalTime()` decompose it back into its separate `LocalDate` and `LocalTime` components — useful when only one part is needed downstream, without losing the combined value itself.

### Level 2 — Intermediate

```java
import java.time.*;

public class LocalDateTimeArithmetic {
    public static void main(String[] args) {
        LocalDateTime meetingTime = LocalDateTime.of(2026, 7, 9, 23, 0); // 11 PM

        // Adding hours that cross midnight -- the DATE automatically rolls forward too.
        LocalDateTime reminderTime = meetingTime.minusHours(1); // 1 hour before
        LocalDateTime followUpTime = meetingTime.plusHours(2);  // 2 hours after, crosses into next day

        System.out.println("Meeting: " + meetingTime);
        System.out.println("Reminder (1hr before): " + reminderTime);
        System.out.println("Follow-up (2hr after): " + followUpTime);
    }
}
```

**How to run:** `java LocalDateTimeArithmetic.java`

Expected output:
```
Meeting: 2026-07-09T23:00
Reminder (1hr before): 2026-07-09T22:00
Follow-up (2hr after): 2026-07-10T01:00
```

The real-world concern this adds: since `LocalDateTime` combines date and time, arithmetic that crosses midnight correctly rolls the **date** forward or backward too — `meetingTime.plusHours(2)` starting at `23:00` on July 9th correctly produces `01:00` on July 10th, not an invalid `25:00` or a same-day wraparound. This automatic date-rollover is exactly the kind of edge case `LocalTime` alone (see [[localtime]]) cannot handle, since it has no date component to roll over into.

### Level 3 — Advanced

```java
import java.time.*;
import java.time.temporal.ChronoUnit;

public class LocalDateTimeDuration {
    public static void main(String[] args) {
        LocalDateTime eventStart = LocalDateTime.of(2026, 7, 9, 18, 0);
        LocalDateTime eventEnd = LocalDateTime.of(2026, 7, 10, 2, 30); // crosses midnight

        boolean crossesMidnight = !eventStart.toLocalDate().equals(eventEnd.toLocalDate());
        System.out.println("Event crosses midnight: " + crossesMidnight);

        long totalMinutes = ChronoUnit.MINUTES.between(eventStart, eventEnd);
        long hours = totalMinutes / 60;
        long minutes = totalMinutes % 60;
        System.out.println("Event duration: " + hours + "h " + minutes + "m");

        boolean isBefore = eventStart.isBefore(eventEnd);
        System.out.println("Start is before end: " + isBefore);
    }
}
```

**How to run:** `java LocalDateTimeDuration.java`

Expected output:
```
Event crosses midnight: true
Event duration: 8h 30m
Start is before end: true
```

This computes the actual **duration** between two `LocalDateTime` values that span across a date boundary — `ChronoUnit.MINUTES.between(eventStart, eventEnd)` correctly accounts for the full elapsed time (`18:00` on the 9th to `02:30` on the 10th is `8` hours and `30` minutes total, i.e. `510` minutes), automatically handling the day rollover internally rather than requiring any manual date-boundary math from the caller.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `eventStart` is `2026-07-09T18:00`, `eventEnd` is `2026-07-10T02:30` — a genuine, deliberate crossing of the midnight boundary between two different calendar dates.

`eventStart.toLocalDate().equals(eventEnd.toLocalDate())` compares just the date portions: `2026-07-09` versus `2026-07-10` — these are different dates, so `.equals(...)` returns `false`, and `!false = true` — `crossesMidnight` is `true`, printed accordingly.

`ChronoUnit.MINUTES.between(eventStart, eventEnd)` computes the total elapsed minutes between the two full date-time values. Internally, this considers both the date and time components together as one continuous timeline — from `18:00` on July 9th to midnight is `6` hours (`360` minutes), and from midnight to `02:30` on July 10th is another `2.5` hours (`150` minutes), for a total of `360 + 150 = 510` minutes. `totalMinutes` is `510`.

`hours = totalMinutes / 60` computes `510 / 60 = 8` (integer division). `minutes = totalMinutes % 60` computes `510 % 60 = 30`. Printed together as `"Event duration: 8h 30m"`.

```
eventStart = 2026-07-09T18:00
eventEnd   = 2026-07-10T02:30

18:00 (Jul 9) -> midnight (Jul 10):  6h 00m = 360 minutes
midnight (Jul 10) -> 02:30 (Jul 10): 2h 30m = 150 minutes
total: 360 + 150 = 510 minutes = 8h 30m
```

`eventStart.isBefore(eventEnd)` compares the two `LocalDateTime` values as a whole (both date and time together): since `2026-07-09T18:00` chronologically precedes `2026-07-10T02:30`, this returns `true`, printed as `"Start is before end: true"` — `LocalDateTime`'s comparison methods naturally account for both the date and time components together, correctly handling cross-date comparisons without any special-case logic needed from the caller.

## 7. Gotchas & takeaways

> `LocalDateTime`, like `LocalDate` and `LocalTime`, carries **no timezone information whatsoever** — two `LocalDateTime` values with the identical date and time represent the same "wall clock" reading, but could correspond to entirely different actual moments if interpreted in different timezones. Never use `LocalDateTime` alone to compare or schedule events across different timezones; for that, `ZonedDateTime` (which pairs a `LocalDateTime` with a specific `ZoneId`) or `Instant` (a genuine, timezone-independent point in time) is the correct tool.

- `LocalDateTime` combines a `LocalDate` and `LocalTime` into one value, still with no timezone attached — immutable, like the rest of `java.time`.
- `atTime(...)`/`atDate(...)` combine a `LocalDate`/`LocalTime` into a `LocalDateTime`; `.toLocalDate()`/`.toLocalTime()` decompose one back into its parts.
- Date-and-time arithmetic (`plusHours`, `minusDays`, ...) correctly rolls the date component forward or backward whenever the time component crosses a midnight boundary.
- `ChronoUnit.between(start, end)` computes the full elapsed duration between two `LocalDateTime` values in a chosen unit (minutes, hours, days), automatically handling any date-boundary crossings internally.
- `LocalDateTime` is unsuitable for representing an unambiguous, timezone-independent moment — for that, use `ZonedDateTime` (a `LocalDateTime` plus a specific zone) or `Instant` (see [[instant]]).
