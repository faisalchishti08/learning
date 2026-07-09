---
card: java
gi: 539
slug: localdate
title: LocalDate
---

## 1. What it is

`LocalDate` represents a date without a time-of-day or timezone — just a year, month, and day, like "2026-07-09" or "a birthday." It's part of `java.time`, the modern date/time API introduced in Java 8 to replace the notoriously error-prone, mutable `java.util.Date` and `java.util.Calendar`. `LocalDate` instances are **immutable**: every operation that "changes" a date (adding days, changing the month) returns a brand-new `LocalDate`, leaving the original untouched.

## 2. Why & when

You reach for `LocalDate` whenever time-of-day and timezone genuinely don't matter — birthdays, anniversaries, due dates, holidays, "the date this invoice was issued." Modeling these as `LocalDate` rather than a full timestamp avoids an entire category of bugs where a date accidentally shifts by a day due to timezone conversion (a classic `java.util.Date` pitfall). Its immutability also eliminates a different class of bug: accidentally mutating a shared date object that other code still expects to be unchanged.

## 3. Core concept

```java
import java.time.*;

LocalDate today = LocalDate.now();               // the current date, from the system clock
LocalDate specific = LocalDate.of(2026, 7, 9);    // year, month (1-12), day
LocalDate parsed = LocalDate.parse("2026-12-25"); // ISO-8601 format by default

LocalDate nextWeek = today.plusDays(7);   // returns a NEW LocalDate -- today is unchanged
LocalDate lastMonth = today.minusMonths(1);

boolean isAfter = nextWeek.isAfter(today); // true
```

Every arithmetic or modification method (`plusDays`, `minusMonths`, `withYear`, ...) returns a new `LocalDate` instance rather than mutating the one it was called on — a direct consequence of `LocalDate` being immutable.

## 4. Diagram

<svg viewBox="0 0 640 120" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LocalDate operations return a new immutable instance rather than mutating the original">
  <rect x="8" y="8" width="624" height="104" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="110" y="55" fill="#6db33f" font-size="12" text-anchor="middle" font-family="monospace">2026-07-09</text>
  <text x="270" y="45" fill="#8b949e" font-size="11" font-family="sans-serif">.plusDays(7)</text>
  <line x1="190" y1="55" x2="330" y2="55" stroke="#8b949e" stroke-width="2" marker-end="url(#arrowLD)"/>
  <rect x="340" y="30" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="420" y="55" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2026-07-16</text>
  <text x="20" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">The original 2026-07-09 instance is completely unchanged -- a NEW LocalDate is returned.</text>
  <defs><marker id="arrowLD" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`plusDays(7)` produces a brand-new `LocalDate` seven days later — the original instance remains exactly `2026-07-09`.

## 5. Runnable example

Scenario: computing subscription renewal dates for a billing system — evolved from basic date arithmetic, through comparing and validating dates, to a version handling real calendar edge cases like month-end overflow and leap years.

### Level 1 — Basic

```java
import java.time.*;

public class LocalDateBasic {
    public static void main(String[] args) {
        LocalDate subscriptionStart = LocalDate.of(2026, 1, 15);
        LocalDate renewalDate = subscriptionStart.plusMonths(1);

        System.out.println("Subscription started: " + subscriptionStart);
        System.out.println("Renews on: " + renewalDate);
        System.out.println("Original unchanged: " + subscriptionStart);
    }
}
```

**How to run:** `java LocalDateBasic.java`

Expected output:
```
Subscription started: 2026-01-15
Renews on: 2026-02-15
Original unchanged: 2026-01-15
```

`subscriptionStart.plusMonths(1)` computes a date one month later, returning a brand-new `LocalDate` (`2026-02-15`) without modifying `subscriptionStart` itself — printing `subscriptionStart` again afterward confirms it's still `2026-01-15`, exactly as it was before `plusMonths` was called.

### Level 2 — Intermediate

```java
import java.time.*;

public class LocalDateComparison {
    public static void main(String[] args) {
        LocalDate subscriptionStart = LocalDate.of(2026, 1, 15);
        LocalDate today = LocalDate.of(2026, 3, 1); // simulating "today" for a reproducible example

        LocalDate renewalDate = subscriptionStart.plusMonths(1);

        boolean isOverdue = today.isAfter(renewalDate);
        boolean isExactlyRenewalDay = today.isEqual(renewalDate);

        System.out.println("Renewal was due: " + renewalDate);
        System.out.println("Today: " + today);
        System.out.println("Is overdue: " + isOverdue);
        System.out.println("Is exactly renewal day: " + isExactlyRenewalDay);
    }
}
```

**How to run:** `java LocalDateComparison.java`

Expected output:
```
Renewal was due: 2026-02-15
Today: 2026-03-01
Is overdue: true
Is exactly renewal day: false
```

The real-world concern this adds: comparing dates to determine business logic like overdue status. `today.isAfter(renewalDate)` checks whether `2026-03-01` comes after `2026-02-15` chronologically — it does, so the subscription is overdue. `isEqual(...)` checks for an exact date match, which `isAfter`/`isBefore` don't cover (a date isn't "after" itself).

### Level 3 — Advanced

```java
import java.time.*;

public class LocalDateEdgeCases {
    public static void main(String[] args) {
        // Edge case 1: adding a month to Jan 31 -- February doesn't HAVE a 31st.
        LocalDate jan31 = LocalDate.of(2026, 1, 31);
        LocalDate plusOneMonth = jan31.plusMonths(1);
        System.out.println("Jan 31 + 1 month: " + plusOneMonth); // clamps to Feb's actual last day

        // Edge case 2: leap year handling -- Feb 29 only exists in leap years.
        LocalDate leapDay2024 = LocalDate.of(2024, 2, 29); // 2024 IS a leap year
        System.out.println("Leap day 2024 is valid: " + leapDay2024);

        boolean isLeap2026 = Year.isLeap(2026);
        System.out.println("2026 is a leap year: " + isLeap2026);

        try {
            LocalDate invalidLeapDay = LocalDate.of(2026, 2, 29); // 2026 is NOT a leap year
            System.out.println("This should not print: " + invalidLeapDay);
        } catch (DateTimeException e) {
            System.out.println("Correctly rejected invalid date: Feb 29, 2026 does not exist");
        }

        // Edge case 3: computing the number of days between two dates.
        LocalDate start = LocalDate.of(2026, 1, 1);
        LocalDate end = LocalDate.of(2026, 12, 31);
        long daysBetween = java.time.temporal.ChronoUnit.DAYS.between(start, end);
        System.out.println("Days from Jan 1 to Dec 31, 2026: " + daysBetween);
    }
}
```

**How to run:** `java LocalDateEdgeCases.java`

Expected output:
```
Jan 31 + 1 month: 2026-02-28
Leap day 2024 is valid: 2024-02-29
2026 is a leap year: false
Correctly rejected invalid date: Feb 29, 2026 does not exist
Days from Jan 1 to Dec 31, 2026: 364
```

This handles three real calendar edge cases: `jan31.plusMonths(1)` cannot produce `"2026-02-31"` (February never has 31 days), so `LocalDate` automatically **clamps** the result to February's actual last day, `28` (2026 isn't a leap year). `LocalDate.of(2026, 2, 29)` throws `DateTimeException` immediately, since Java correctly validates that `2026` isn't a leap year and `February 29` simply doesn't exist that year — a bug caught at the moment of construction rather than silently producing a wrong date. `ChronoUnit.DAYS.between(...)` correctly counts the days across the entire year, accounting for varying month lengths automatically.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `jan31` is constructed as `LocalDate.of(2026, 1, 31)` — January 31st, 2026.

`jan31.plusMonths(1)` is called. Internally, `LocalDate` computes the target month (February 2026) and then needs a day-of-month for the result. Since the *same* day-of-month, `31`, doesn't exist in February (which has at most `28` or `29` days), `LocalDate`'s documented behavior is to clamp the day down to the last valid day of the target month — February 2026 has `28` days (not a leap year), so the result becomes `2026-02-28`. This is printed as `"Jan 31 + 1 month: 2026-02-28"`.

Next, `leapDay2024` is constructed as `LocalDate.of(2024, 2, 29)`. Since `2024` genuinely is a leap year (divisible by `4`, and not a century year that would need to also be divisible by `400`), February 2024 does have a `29`th day, so this construction succeeds without error, printed as `"Leap day 2024 is valid: 2024-02-29"`.

`Year.isLeap(2026)` checks whether `2026` is a leap year: `2026` is not divisible by `4` (`2026 / 4 = 506.5`), so it returns `false`, printed as `"2026 is a leap year: false"`.

The `try` block then attempts `LocalDate.of(2026, 2, 29)` — since `2026` is not a leap year (just confirmed above), February 2026 only has `28` days, and day `29` is invalid. `LocalDate.of(...)` validates its arguments at construction time and throws `DateTimeException` immediately, rather than silently rolling over into March or producing some other unexpected date. The `catch` block prints `"Correctly rejected invalid date: Feb 29, 2026 does not exist"`.

```
jan31 = 2026-01-31
plusMonths(1): target month = February 2026 (28 days, not a leap year)
  day 31 doesn't exist in February -> CLAMPED to last valid day -> 2026-02-28

LocalDate.of(2024, 2, 29): 2024 IS a leap year -> Feb has 29 days -> valid, succeeds
LocalDate.of(2026, 2, 29): 2026 is NOT a leap year -> Feb has 28 days -> day 29 invalid -> THROWS DateTimeException
```

Finally, `ChronoUnit.DAYS.between(start, end)` computes the exact number of days between `2026-01-01` and `2026-12-31`, correctly accounting for every month's actual length across the year (including February's `28` days, since 2026 isn't a leap year) — the result is `364` (one day short of the full `365`-day year, since it counts the days *between* January 1st and December 31st, not including both endpoints as a full year span), printed as `"Days from Jan 1 to Dec 31, 2026: 364"`.

## 7. Gotchas & takeaways

> `plusMonths`/`plusYears` silently **clamp** the day-of-month when the target month doesn't have enough days (as seen with `Jan 31 + 1 month` becoming `Feb 28`, not throwing or rolling over into March) — this is well-documented, expected behavior, but easy to overlook if you assume date arithmetic always preserves the exact day number. Always consider month-length edge cases when adding months or years to a date near the end of a month.

- `LocalDate` represents a date-only value (year, month, day) with no time-of-day or timezone component, immutable like all of `java.time`.
- Every "modification" method (`plusDays`, `minusMonths`, `withYear`, ...) returns a new `LocalDate` instance — the original is never changed.
- `LocalDate.of(year, month, day)` validates its arguments at construction time, throwing `DateTimeException` for genuinely invalid dates (like February 29th in a non-leap year).
- `plusMonths`/`plusYears` clamp the resulting day-of-month to the target month's last valid day when the original day doesn't exist there (e.g. adding a month to January 31st).
- `java.time.temporal.ChronoUnit.DAYS.between(start, end)` (and other `ChronoUnit` values) correctly compute calendar-aware differences between dates, handling varying month lengths and leap years automatically.
