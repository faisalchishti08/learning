---
card: java
gi: 540
slug: localtime
title: LocalTime
---

## 1. What it is

`LocalTime` represents a time-of-day without a date or timezone — just hours, minutes, seconds, and nanoseconds, like "14:30" or "9:15:00 AM." It's the time-only counterpart to `LocalDate`: immutable, part of `java.time`, and every modification method returns a new instance rather than mutating the original.

## 2. Why & when

Use `LocalTime` whenever you need to represent a time-of-day independent of any specific date — a store's daily opening time, a recurring meeting's start time, "the alarm goes off at 7:00 AM every day." Because it carries no date, `LocalTime` is naturally suited for recurring or schedule-like values where the date is irrelevant or determined separately. It has no timezone either, so like `LocalDate`, it's meant for "wall clock" concepts, not for representing an exact, unambiguous instant in universal time (that's what `Instant`, see [[instant]], is for).

## 3. Core concept

```java
import java.time.*;

LocalTime now = LocalTime.now();                 // current time from the system clock
LocalTime specific = LocalTime.of(14, 30);        // hour, minute (24-hour clock)
LocalTime withSeconds = LocalTime.of(9, 15, 30);  // hour, minute, second
LocalTime parsed = LocalTime.parse("18:45:00");

LocalTime later = specific.plusHours(2);   // 16:30 -- a NEW LocalTime
boolean isBefore = specific.isBefore(later); // true
```

`LocalTime` values compose the same way `LocalDate` does: construct with `of(...)` or `parse(...)`, transform with `plus*`/`minus*` methods that each return a fresh instance.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LocalTime represents a time-of-day with no date or timezone attached">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="130" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="95" y="55" fill="#6db33f" font-size="14" text-anchor="middle" font-family="monospace">14:30:00</text>
  <text x="220" y="45" fill="#8b949e" font-size="10" font-family="sans-serif">no date, no timezone -- just a time-of-day</text>
  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Compare with LocalDate (date only) and LocalDateTime (both combined).</text>
</svg>

`LocalTime` isolates just the time-of-day component — hour, minute, second, nanosecond — with nothing else attached.

## 5. Runnable example

Scenario: modeling a store's daily business hours and checking whether it's currently open — evolved from basic time construction and comparison, through wraparound-safe range checking, to a version handling a store that stays open past midnight.

### Level 1 — Basic

```java
import java.time.*;

public class LocalTimeBasic {
    public static void main(String[] args) {
        LocalTime openTime = LocalTime.of(9, 0);
        LocalTime closeTime = LocalTime.of(17, 30);

        System.out.println("Store opens: " + openTime);
        System.out.println("Store closes: " + closeTime);

        LocalTime lunchStart = openTime.plusHours(3).plusMinutes(30);
        System.out.println("Lunch break starts: " + lunchStart);
    }
}
```

**How to run:** `java LocalTimeBasic.java`

Expected output:
```
Store opens: 09:00
Store closes: 17:30
Lunch break starts: 12:30
```

`LocalTime.of(9, 0)` and `LocalTime.of(17, 30)` construct plain times with no date attached. `openTime.plusHours(3).plusMinutes(30)` chains two additions: `9:00` plus `3` hours is `12:00`, plus `30` minutes is `12:30` — each `plus*` call returns a new `LocalTime`, chained fluently.

### Level 2 — Intermediate

```java
import java.time.*;

public class LocalTimeRangeCheck {
    static boolean isOpen(LocalTime current, LocalTime open, LocalTime close) {
        return !current.isBefore(open) && current.isBefore(close);
    }

    public static void main(String[] args) {
        LocalTime openTime = LocalTime.of(9, 0);
        LocalTime closeTime = LocalTime.of(17, 30);

        LocalTime checkTime1 = LocalTime.of(14, 0);  // during business hours
        LocalTime checkTime2 = LocalTime.of(8, 30);   // before opening
        LocalTime checkTime3 = LocalTime.of(17, 30);  // exactly at closing

        System.out.println("14:00 -- open: " + isOpen(checkTime1, openTime, closeTime));
        System.out.println("08:30 -- open: " + isOpen(checkTime2, openTime, closeTime));
        System.out.println("17:30 -- open: " + isOpen(checkTime3, openTime, closeTime));
    }
}
```

**How to run:** `java LocalTimeRangeCheck.java`

Expected output:
```
14:00 -- open: true
08:30 -- open: false
17:30 -- open: false
```

The real-world concern this adds: a genuine open/closed check needs both bounds. `!current.isBefore(open) && current.isBefore(close)` treats the opening time as inclusive (`14:00` and even exactly `09:00` would count as open) and the closing time as exclusive (`17:30` itself counts as *closed*, matching how most real business-hours logic treats the closing boundary) — `14:00` falls cleanly inside, `08:30` is before opening, and `17:30` fails the strict `isBefore(close)` check since it equals the boundary rather than preceding it.

### Level 3 — Advanced

```java
import java.time.*;

public class LocalTimeOvernightRange {
    // A range check that correctly handles a range crossing midnight (e.g. a nightclub open 22:00-02:00).
    static boolean isOpen(LocalTime current, LocalTime open, LocalTime close) {
        if (open.isBefore(close)) {
            // Normal same-day range, e.g. 09:00 to 17:30.
            return !current.isBefore(open) && current.isBefore(close);
        } else {
            // Overnight range, e.g. 22:00 to 02:00 -- "open" means AFTER open OR BEFORE close.
            return !current.isBefore(open) || current.isBefore(close);
        }
    }

    public static void main(String[] args) {
        LocalTime openTime = LocalTime.of(22, 0);  // 10 PM
        LocalTime closeTime = LocalTime.of(2, 0);   // 2 AM the next day

        LocalTime lateNight = LocalTime.of(23, 30);  // 11:30 PM -- should be open
        LocalTime earlyMorning = LocalTime.of(1, 0); // 1:00 AM -- should be open (still "yesterday's" session)
        LocalTime midday = LocalTime.of(12, 0);       // noon -- should be closed
        LocalTime rightAtClose = LocalTime.of(2, 0);   // exactly closing time -- should be closed

        System.out.println("23:30 -- open: " + isOpen(lateNight, openTime, closeTime));
        System.out.println("01:00 -- open: " + isOpen(earlyMorning, openTime, closeTime));
        System.out.println("12:00 -- open: " + isOpen(midday, openTime, closeTime));
        System.out.println("02:00 -- open: " + isOpen(rightAtClose, openTime, closeTime));
    }
}
```

**How to run:** `java LocalTimeOvernightRange.java`

Expected output:
```
23:30 -- open: true
01:00 -- open: true
12:00 -- open: false
02:00 -- open: false
```

This handles a genuine edge case `LocalTime` alone doesn't solve automatically: a business open **overnight**, crossing midnight (`22:00` to `02:00`). Since `LocalTime` has no notion of "the next day," a naive `!current.isBefore(open) && current.isBefore(close)` check would incorrectly treat `22:00` to `02:00` as an *empty* range (since `open` is numerically *after* `close` on the 24-hour clock). The fix detects this case (`open.isBefore(close)` being `false` signals an overnight range) and switches to an OR-based check instead: "open" means either after the opening time *or* before the closing time, correctly capturing both `23:30` (after open) and `01:00` (before close, on the following calendar day) as open.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `openTime` is `22:00`, `closeTime` is `02:00` — an overnight range.

`isOpen(lateNight, openTime, closeTime)` is called with `lateNight = 23:30`. Inside `isOpen`, `open.isBefore(close)` checks `22:00.isBefore(02:00)` — numerically, `22:00` (as a time-of-day) is *not* before `02:00` on the same clock face, so this is `false`, meaning the overnight branch runs: `!current.isBefore(open) || current.isBefore(close)`. `current.isBefore(open)` is `23:30.isBefore(22:00)`, which is `false` (since `23:30` comes after `22:00`), so `!false = true`. Since the left side of the `||` is already `true`, the whole expression short-circuits to `true` — `23:30` is correctly identified as open (it's after the `22:00` opening time).

`isOpen(earlyMorning, openTime, closeTime)` is called with `earlyMorning = 01:00`. The overnight branch runs again: `current.isBefore(open)` is `01:00.isBefore(22:00)`, which is `true` (since `01:00` is numerically earlier in the day than `22:00`), so `!true = false`. The left side of `||` is `false`, so the right side is evaluated: `current.isBefore(close)` is `01:00.isBefore(02:00)`, which is `true`. The overall `||` is `true` — `01:00` is correctly identified as open (it's before the `02:00` closing time, understood as the *next* day's early hours).

`isOpen(midday, openTime, closeTime)` is called with `midday = 12:00`. `!current.isBefore(open)` is `!(12:00.isBefore(22:00))` = `!true` = `false`. `current.isBefore(close)` is `12:00.isBefore(02:00)` = `false` (noon is not before 2 AM on the same 24-hour clock face). Both sides of the `||` are `false`, so the overall result is `false` — correctly closed.

```
open=22:00, close=02:00 (overnight range, since open > close numerically)

23:30: !isBefore(22:00) -> true                          -> OR short-circuits -> OPEN
01:00: !isBefore(22:00) -> false, then isBefore(02:00) -> true -> OPEN
12:00: !isBefore(22:00) -> false, then isBefore(02:00) -> false -> CLOSED
02:00: !isBefore(22:00) -> false, then isBefore(02:00) -> false (02:00 is NOT before itself) -> CLOSED
```

`isOpen(rightAtClose, openTime, closeTime)` with `rightAtClose = 02:00`: `!current.isBefore(open)` is `!(02:00.isBefore(22:00))` = `!true` = `false`. `current.isBefore(close)` is `02:00.isBefore(02:00)`, which is `false` (a time is never before itself). Both sides `false`, overall `false` — correctly closed, treating the closing boundary as exclusive just like the same-day case did.

## 7. Gotchas & takeaways

> `LocalTime` has no concept of "the next day" — comparing two `LocalTime` values only ever considers their position within a single 24-hour cycle, never which calendar day they might conceptually belong to. A naive range check that works fine for same-day hours (`09:00` to `17:30`) silently breaks for any range that crosses midnight, as demonstrated in Level 3 — always special-case overnight ranges explicitly when working with `LocalTime` alone.

- `LocalTime` represents a time-of-day (hour, minute, second, nanosecond) with no date or timezone attached, immutable like all of `java.time`.
- `plus*`/`minus*` methods (`plusHours`, `plusMinutes`, ...) return a new `LocalTime` instance, chainable fluently.
- A same-day range check (open before close) works with a straightforward `!isBefore(open) && isBefore(close)` pattern.
- An overnight range (open numerically after close, like `22:00` to `02:00`) requires switching to an OR-based check, since the simple AND-based logic would incorrectly treat the range as empty.
- For representing a genuine point in time (unambiguous across timezones, suitable for logging or precise measurement), use `Instant` (see [[instant]]) instead — `LocalTime` is strictly for "wall clock" time-of-day concepts.
