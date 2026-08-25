# Java Date and Time (java.time)

## Overview

Java 8 introduced `java.time` (JSR-310, based on Joda-Time) to replace the broken `java.util.Date` and `java.util.Calendar`. All core classes are **immutable** and **thread-safe**. Operations return new instances; originals are never modified.

---

## 1. Legacy Problems

### What was wrong with `java.util.Date`

```java
// LEGACY — do not use in new code
import java.util.Date;
import java.util.Calendar;
import java.text.SimpleDateFormat;

Date d = new Date(); // mutable — anyone can call d.setTime(...)

// Month is 0-indexed! January = 0, December = 11
Calendar cal = Calendar.getInstance();
cal.set(2024, 0, 15); // January 15 — not month 1!

// SimpleDateFormat is NOT thread-safe
SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd");
// Sharing this across threads → data corruption without synchronization

// Date represents both a date AND an instant — conflated concepts
// Date.getYear() returns year - 1900 (!)
// Date.getMonth() returns 0-11 (!)
```

**What this does:** shows every trap in the legacy API. Month 0-indexing caused production bugs for decades. Mutability made `Date` objects unsafe to share. `SimpleDateFormat` required `ThreadLocal` wrappers to use in web servers.

---

### Why java.time was introduced

```
java.util.Date problems:
  ┌──────────────────────────────────────────────────────┐
  │  Mutable        → not thread-safe, defensive copies  │
  │  Month 0-based  → off-by-one bugs everywhere         │
  │  Conflated      → Date = date + time + timezone mess │
  │  Deprecated     → getYear(), getMonth() deprecated   │
  │  SimpleDateFormat → not thread-safe                  │
  └──────────────────────────────────────────────────────┘

java.time (Java 8+):
  ┌──────────────────────────────────────────────────────┐
  │  Immutable      → thread-safe by design              │
  │  Month 1-based  → January = 1 (Month enum too)       │
  │  Separated      → distinct types for each use case   │
  │  Full API       → no deprecated methods              │
  │  DateTimeFormatter → thread-safe                     │
  └──────────────────────────────────────────────────────┘
```

---

## 2. Core Classes Overview

### Visual Diagram

```
                   Does it include?
              ┌──────────┬──────────┬──────────┐
              │   Date   │   Time   │ Timezone │
  ┌───────────┼──────────┼──────────┼──────────┤
  │LocalDate  │    ✓     │    ✗     │    ✗     │
  │LocalTime  │    ✗     │    ✓     │    ✗     │
  │LocalDateTime│  ✓     │    ✓     │    ✗     │
  │ZonedDateTime│  ✓     │    ✓     │    ✓     │
  │OffsetDateTime│ ✓     │    ✓     │  offset  │
  │Instant    │ epoch ns │          │  UTC     │
  └───────────┴──────────┴──────────┴──────────┘

When to use each:
  LocalDate       → birth dates, deadlines, holidays (no time needed)
  LocalTime       → business hours, alarm time (no date needed)
  LocalDateTime   → log entries, event scheduling (local context)
  ZonedDateTime   → displaying time to users in their timezone
  OffsetDateTime  → storing/serializing timestamps (DB, JSON, REST)
  Instant         → machine timestamps, elapsed time, benchmarking
```

---

### Quick creation examples for each

```java
import java.time.*;

LocalDate       ld  = LocalDate.of(2024, 1, 15);     // 2024-01-15
LocalTime       lt  = LocalTime.of(14, 30, 0);       // 14:30:00
LocalDateTime   ldt = LocalDateTime.of(2024, 1, 15, 14, 30);
ZonedDateTime   zdt = ZonedDateTime.now(ZoneId.of("America/New_York"));
OffsetDateTime  odt = OffsetDateTime.now(ZoneOffset.UTC);
Instant         ins = Instant.now();                  // 2024-01-15T14:30:00Z
```

**What this does:** all six core types in one place. Note months are 1-based throughout `java.time`.

---

## 3. LocalDate

### Creation

```java
LocalDate today   = LocalDate.now();                    // system clock
LocalDate specific = LocalDate.of(2024, 3, 15);         // March 15 2024
LocalDate fromEnum = LocalDate.of(2024, Month.MARCH, 15); // same, safer
LocalDate parsed  = LocalDate.parse("2024-03-15");      // ISO-8601 default
LocalDate fromDay = LocalDate.ofYearDay(2024, 100);     // 100th day of 2024
```

**What this does:** multiple factory methods — `now()` for current date, `of()` for explicit construction, `parse()` for string input, `ofYearDay()` for ordinal dates.

---

### Manipulation — immutable, returns new instance

```java
LocalDate date = LocalDate.of(2024, 3, 15);

LocalDate nextWeek     = date.plusDays(7);         // 2024-03-22
LocalDate lastMonth    = date.minusMonths(1);      // 2024-02-15
LocalDate nextYear     = date.plusYears(1);        // 2025-03-15
LocalDate firstOfMonth = date.withDayOfMonth(1);  // 2024-03-01
LocalDate inJune       = date.withMonth(6);        // 2024-06-15
LocalDate in2020       = date.withYear(2020);      // 2020-03-15
```

**What this does:** `plus*`/`minus*` for relative changes, `with*` for absolute replacement. Original `date` is unchanged — all return new `LocalDate` instances.

---

### Comparison

```java
LocalDate a = LocalDate.of(2024, 1, 1);
LocalDate b = LocalDate.of(2024, 6, 15);

System.out.println(a.isBefore(b));  // true
System.out.println(a.isAfter(b));   // false
System.out.println(a.isEqual(b));   // false
System.out.println(a.compareTo(b)); // negative (a before b)
System.out.println(a.equals(b));    // false (value equality)
```

**What this does:** `isBefore/isAfter/isEqual` are readable business-logic comparisons. `compareTo` integrates with sort. `equals` checks full value equality.

---

### Getters and info methods

```java
LocalDate date = LocalDate.of(2024, 3, 15);

System.out.println(date.getYear());            // 2024
System.out.println(date.getMonth());           // MARCH (enum)
System.out.println(date.getMonthValue());      // 3 (int, 1-based)
System.out.println(date.getDayOfMonth());      // 15
System.out.println(date.getDayOfWeek());       // FRIDAY (enum)
System.out.println(date.getDayOfYear());       // 75 (75th day of 2024)
System.out.println(date.lengthOfMonth());      // 31
System.out.println(date.lengthOfYear());       // 366 (2024 is leap year)
System.out.println(date.isLeapYear());         // true
```

**What this does:** `getMonth()` returns the `Month` enum (never a raw int). `getMonthValue()` gives 1-based int. `getDayOfWeek()` returns `DayOfWeek` enum — no more `Calendar.DAY_OF_WEEK` constants.

> ⚠️ **Pitfall:** `getMonthValue()` returns 1–12. This is different from legacy `Calendar.get(Calendar.MONTH)` which returned 0–11. Never subtract 1 with `java.time`.

---

### Dry Run — date manipulation chain

```java
LocalDate start = LocalDate.of(2024, 1, 31);
LocalDate result = start.plusMonths(1).plusDays(1);
```

| Step | Operation | Result | Note |
|---|---|---|---|
| Start | — | `2024-01-31` | |
| `plusMonths(1)` | Jan 31 + 1 month | `2024-02-29` | Feb 2024 has 29 days (leap year) — clamped |
| `plusDays(1)` | Feb 29 + 1 day | `2024-03-01` | |

> ⚠️ **Pitfall:** `plusMonths` clamps to valid day. `LocalDate.of(2024,1,31).plusMonths(1)` → Feb 29, not Feb 31. Order of operations matters.

---

## 4. LocalTime and LocalDateTime

### LocalTime creation and manipulation

```java
LocalTime t1 = LocalTime.now();
LocalTime t2 = LocalTime.of(14, 30);          // 14:30:00
LocalTime t3 = LocalTime.of(14, 30, 45);      // 14:30:45
LocalTime t4 = LocalTime.of(14, 30, 45, 123_000_000); // with nanos
LocalTime t5 = LocalTime.parse("14:30:45");

LocalTime later   = t2.plusHours(3);          // 17:30
LocalTime earlier = t2.minusMinutes(15);      // 14:15
LocalTime atNoon  = t2.withHour(12);          // 12:30

System.out.println(t2.getHour());   // 14
System.out.println(t2.getMinute()); // 30
System.out.println(t2.getSecond()); // 0
```

**What this does:** same immutable pattern as `LocalDate`. `LocalTime.MIDNIGHT` (00:00) and `LocalTime.NOON` (12:00) are constants.

---

### Truncation

```java
LocalTime precise = LocalTime.of(14, 30, 45, 123_456_789);

LocalTime toMinute = precise.truncatedTo(ChronoUnit.MINUTES);  // 14:30:00
LocalTime toHour   = precise.truncatedTo(ChronoUnit.HOURS);    // 14:00:00
LocalTime toSecond = precise.truncatedTo(ChronoUnit.SECONDS);  // 14:30:45
```

**What this does:** `truncatedTo` zeroes out all fields smaller than the given unit. Useful when comparing times ignoring sub-second precision or when normalizing for scheduling.

---

### LocalDateTime — creation and combining

```java
// Direct construction
LocalDateTime ldt1 = LocalDateTime.of(2024, 3, 15, 14, 30);
LocalDateTime ldt2 = LocalDateTime.of(2024, Month.MARCH, 15, 14, 30, 0);
LocalDateTime ldt3 = LocalDateTime.parse("2024-03-15T14:30:00");

// Combining LocalDate + LocalTime
LocalDate  date = LocalDate.of(2024, 3, 15);
LocalTime  time = LocalTime.of(14, 30);

LocalDateTime combined1 = LocalDateTime.of(date, time);
LocalDateTime combined2 = date.atTime(time);          // same result
LocalDateTime combined3 = date.atTime(14, 30);        // inline
LocalDateTime combined4 = time.atDate(date);          // from time side

// Extracting back
LocalDate  extractedDate = ldt1.toLocalDate(); // 2024-03-15
LocalTime  extractedTime = ldt1.toLocalTime(); // 14:30
```

**What this does:** `atTime` and `atDate` are the canonical way to combine parts. `toLocalDate()` / `toLocalTime()` extract them back.

---

## 5. ZonedDateTime and ZoneId

### ZoneId — identifying timezones

```java
ZoneId newYork  = ZoneId.of("America/New_York");
ZoneId london   = ZoneId.of("Europe/London");
ZoneId tokyo    = ZoneId.of("Asia/Tokyo");
ZoneId utc      = ZoneId.of("UTC");
ZoneId system   = ZoneId.systemDefault(); // JVM's configured timezone

// List all available zone IDs (600+)
ZoneId.getAvailableZoneIds().stream()
    .sorted()
    .limit(5)
    .forEach(System.out::println);
// Africa/Abidjan, Africa/Accra, ...
```

**What this does:** always use region-based IDs like `"America/New_York"` rather than offsets like `"EST"` — abbreviations are ambiguous and don't account for DST automatically.

---

### Creating ZonedDateTime

```java
ZoneId nyZone = ZoneId.of("America/New_York");

// Current time in a specific zone
ZonedDateTime nowNY = ZonedDateTime.now(nyZone);

// Specific moment in a zone
ZonedDateTime zdt = ZonedDateTime.of(2024, 3, 15, 14, 30, 0, 0, nyZone);

// From LocalDateTime + ZoneId (local time interpreted in that zone)
LocalDateTime ldt = LocalDateTime.of(2024, 3, 15, 14, 30);
ZonedDateTime zdtFromLocal = ldt.atZone(nyZone);

System.out.println(zdtFromLocal);
// 2024-03-15T14:30-04:00[America/New_York]
//   ↑ date   ↑ time  ↑ offset  ↑ zone name
```

**What this does:** `ldt.atZone(zone)` interprets the local date-time as-is in that timezone. The offset `-04:00` is automatically determined (EDT in March after DST spring-forward).

---

### Converting between zones

```java
ZonedDateTime nyTime = ZonedDateTime.of(2024, 6, 15, 9, 0, 0, 0,
    ZoneId.of("America/New_York")); // 9 AM New York

// Convert: same instant, different representation
ZonedDateTime londonTime = nyTime.withZoneSameInstant(ZoneId.of("Europe/London"));
ZonedDateTime tokyoTime  = nyTime.withZoneSameInstant(ZoneId.of("Asia/Tokyo"));

System.out.println(nyTime.toLocalTime());     // 09:00
System.out.println(londonTime.toLocalTime()); // 14:00 (UTC+1 in summer)
System.out.println(tokyoTime.toLocalTime());  // 22:00 (UTC+9)
```

**What this does:** `withZoneSameInstant` converts to the same moment in time expressed in a different timezone. The wall-clock time changes; the underlying instant does not.

---

### DST handling

```java
ZoneId nyZone = ZoneId.of("America/New_York");

// Day before US spring-forward (DST starts March 10 2024 at 2:00 AM)
ZonedDateTime before = ZonedDateTime.of(2024, 3, 9, 10, 0, 0, 0, nyZone);
ZonedDateTime after  = before.plusDays(1);

System.out.println(before); // 2024-03-09T10:00-05:00[America/New_York] (EST)
System.out.println(after);  // 2024-03-10T10:00-04:00[America/New_York] (EDT)
// same 10:00 wall clock, but offset changed automatically
```

**What this does:** `ZonedDateTime` handles DST transitions automatically. Adding one day keeps the same wall-clock time (10:00) but shifts the offset from `-05:00` to `-04:00`.

> ⚠️ **Pitfall:** `withZoneSameLocal` changes the zone label but keeps the wall-clock time, potentially changing the instant. `withZoneSameInstant` keeps the instant. Know which you need.

---

## 6. Duration and Period

### Duration — time-based (hours, minutes, seconds, nanos)

```java
Duration d1 = Duration.ofHours(2);
Duration d2 = Duration.ofMinutes(90);
Duration d3 = Duration.ofSeconds(3600);
Duration d4 = Duration.parse("PT1H30M"); // ISO-8601 duration

LocalTime start = LocalTime.of(9, 0);
LocalTime end   = LocalTime.of(17, 30);
Duration workDay = Duration.between(start, end); // 8h 30m

System.out.println(workDay.toHours());   // 8
System.out.println(workDay.toMinutes()); // 510
System.out.println(workDay.toSeconds()); // 30600

// Works with Instant and LocalDateTime too
Instant t1 = Instant.parse("2024-03-15T09:00:00Z");
Instant t2 = Instant.parse("2024-03-15T17:30:00Z");
Duration elapsed = Duration.between(t1, t2);
System.out.println(elapsed.toMinutesPart()); // 30  [Java 9+]
System.out.println(elapsed.toHoursPart());   //  8  [Java 9+]
```

**What this does:** `Duration` measures time-based amounts. `between()` takes any two `Temporal` objects of compatible types. `toHoursPart()` [Java 9+] gives just the hours component (not total hours).

---

### Period — date-based (years, months, days)

```java
Period p1 = Period.ofYears(1);
Period p2 = Period.ofMonths(6);
Period p3 = Period.of(1, 6, 15); // 1 year 6 months 15 days

LocalDate start = LocalDate.of(2020, 3, 15);
LocalDate end   = LocalDate.of(2024, 6, 20);
Period age = Period.between(start, end);

System.out.println(age.getYears());  // 4
System.out.println(age.getMonths()); // 3
System.out.println(age.getDays());   // 5
System.out.println(age);             // P4Y3M5D
```

**What this does:** `Period` measures calendar-based amounts. Components are separate — `getYears()` does NOT include months or days. Use `ChronoUnit.DAYS.between()` for total days.

---

### Dry Run — calculate age with Period.between()

```java
LocalDate birthDate = LocalDate.of(1990, 5, 20);
LocalDate today     = LocalDate.of(2024, 3, 15);
Period age = Period.between(birthDate, today);
```

| Step | Calculation | Value |
|---|---|---|
| Years | 2024 − 1990 | 33 (birthday not yet in 2024 → 33, not 34) |
| Months | March(3) − May(5) → borrow | −2 → 10 months back from March = 10 |
| Days | 15 − 20 → borrow | −5 → days back from 15 = 23 |
| Final | | P33Y10M23D |

```java
System.out.println("Age: " + age.getYears() + " years, "
    + age.getMonths() + " months, "
    + age.getDays() + " days");
// Age: 33 years, 10 months, 23 days
```

> ⚠️ **Pitfall:** `Duration` and `Period` cannot be mixed. `Duration.between(localDate1, localDate2)` throws `UnsupportedTemporalTypeException`. Use `Period` for dates, `Duration` for times/instants.

---

### Total days between two dates

```java
LocalDate from = LocalDate.of(2024, 1, 1);
LocalDate to   = LocalDate.of(2024, 12, 31);

long totalDays = ChronoUnit.DAYS.between(from, to); // 365
long totalMonths = ChronoUnit.MONTHS.between(from, to); // 11
```

**What this does:** `ChronoUnit.DAYS.between()` gives total days as a long — unlike `Period` which splits into years/months/days components.

---

## 7. DateTimeFormatter

### Predefined formatters

```java
import java.time.format.DateTimeFormatter;

LocalDate date = LocalDate.of(2024, 3, 15);
LocalDateTime ldt = LocalDateTime.of(2024, 3, 15, 14, 30, 45);
ZonedDateTime zdt = ZonedDateTime.of(ldt, ZoneId.of("UTC"));

// ISO standard formats (thread-safe singletons)
System.out.println(DateTimeFormatter.ISO_LOCAL_DATE.format(date));
// 2024-03-15

System.out.println(DateTimeFormatter.ISO_LOCAL_DATE_TIME.format(ldt));
// 2024-03-15T14:30:45

System.out.println(DateTimeFormatter.ISO_ZONED_DATE_TIME.format(zdt));
// 2024-03-15T14:30:45Z[UTC]

System.out.println(DateTimeFormatter.ISO_INSTANT.format(zdt));
// 2024-03-15T14:30:45Z

System.out.println(DateTimeFormatter.RFC_1123_DATE_TIME.format(zdt));
// Fri, 15 Mar 2024 14:30:45 GMT
```

**What this does:** predefined formatters are static constants on `DateTimeFormatter` — always thread-safe, no instantiation needed. `ISO_INSTANT` is the standard for REST API timestamps.

---

### Custom patterns

```java
DateTimeFormatter custom1 = DateTimeFormatter.ofPattern("dd/MM/yyyy");
DateTimeFormatter custom2 = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss");
DateTimeFormatter custom3 = DateTimeFormatter.ofPattern("MMMM d, yyyy");
DateTimeFormatter custom4 = DateTimeFormatter.ofPattern("EEE, MMM d yyyy");

LocalDate date = LocalDate.of(2024, 3, 15);
LocalDateTime ldt = LocalDateTime.of(2024, 3, 15, 14, 30, 45);

System.out.println(date.format(custom1));  // 15/03/2024
System.out.println(ldt.format(custom2));   // 15/03/2024 14:30:45
System.out.println(date.format(custom3));  // March 15, 2024
System.out.println(date.format(custom4));  // Fri, Mar 15 2024
```

**What this does:** `ofPattern` creates a formatter from a pattern string. Common tokens: `yyyy` (4-digit year), `MM` (month), `dd` (day), `HH` (24h hour), `mm` (minutes), `ss` (seconds), `MMMM` (full month name), `EEE` (short weekday).

---

### Parsing — string to date

```java
DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd/MM/yyyy");

LocalDate parsed = LocalDate.parse("15/03/2024", fmt);
System.out.println(parsed); // 2024-03-15

// ISO default — no formatter needed
LocalDate iso = LocalDate.parse("2024-03-15");
LocalDateTime isoLdt = LocalDateTime.parse("2024-03-15T14:30:00");
```

**What this does:** `parse` is the static method on the type class. The formatter must match the input string exactly or `DateTimeParseException` is thrown.

---

### Locale-sensitive formatting

```java
DateTimeFormatter frenchFmt = DateTimeFormatter
    .ofPattern("d MMMM yyyy", Locale.FRENCH);

DateTimeFormatter germanFmt = DateTimeFormatter
    .ofPattern("d MMMM yyyy", Locale.GERMAN);

LocalDate date = LocalDate.of(2024, 3, 15);

System.out.println(date.format(frenchFmt)); // 15 mars 2024
System.out.println(date.format(germanFmt)); // 15 März 2024
```

**What this does:** `ofPattern(pattern, locale)` localizes month and day names. Essential for user-facing date display in international applications.

> ⚠️ **Pitfall:** `DateTimeFormatter.ofPattern` is thread-safe; `SimpleDateFormat` from the old API is NOT. You can safely store `DateTimeFormatter` in a static field; never do that with `SimpleDateFormat`.

> ⚠️ **Pitfall:** Month pattern `M` or `MM` formats as number; `MMM` gives abbreviated name ("Mar"); `MMMM` gives full name ("March"). Using the wrong count is a common mistake.

---

## 8. Temporal Adjusters

### Built-in adjusters from `TemporalAdjusters`

```java
import java.time.temporal.TemporalAdjusters;

LocalDate date = LocalDate.of(2024, 3, 15); // Friday

LocalDate firstOfMonth    = date.with(TemporalAdjusters.firstDayOfMonth());  // 2024-03-01
LocalDate lastOfMonth     = date.with(TemporalAdjusters.lastDayOfMonth());   // 2024-03-31
LocalDate firstOfYear     = date.with(TemporalAdjusters.firstDayOfYear());   // 2024-01-01
LocalDate lastOfYear      = date.with(TemporalAdjusters.lastDayOfYear());    // 2024-12-31
LocalDate firstOfNextMonth= date.with(TemporalAdjusters.firstDayOfNextMonth()); // 2024-04-01
LocalDate firstOfNextYear = date.with(TemporalAdjusters.firstDayOfNextYear()); // 2025-01-01

LocalDate nextMonday      = date.with(TemporalAdjusters.next(DayOfWeek.MONDAY));
// 2024-03-18 (next Monday after Friday Mar 15)

LocalDate nextOrSameMonday= date.with(TemporalAdjusters.nextOrSame(DayOfWeek.MONDAY));
// 2024-03-18 (same result here — Mar 15 is Friday not Monday)

LocalDate fridayOrSame    = date.with(TemporalAdjusters.nextOrSame(DayOfWeek.FRIDAY));
// 2024-03-15 (today is already Friday — returns same date)
```

**What this does:** `TemporalAdjusters` provides a library of common calendar calculations. `with(adjuster)` applies the adjuster and returns a new date. `next(DOW)` always goes forward at least one day; `nextOrSame(DOW)` returns today if it already matches.

---

### nth day of month — advanced built-in

```java
LocalDate date = LocalDate.of(2024, 3, 1);

// Third Monday of March 2024
LocalDate thirdMonday = date.with(
    TemporalAdjusters.dayOfWeekInMonth(3, DayOfWeek.MONDAY)
);
System.out.println(thirdMonday); // 2024-03-18

// Last Friday of March 2024
LocalDate lastFriday = date.with(
    TemporalAdjusters.lastInMonth(DayOfWeek.FRIDAY)
);
System.out.println(lastFriday); // 2024-03-29
```

**What this does:** `dayOfWeekInMonth(n, day)` finds the nth occurrence of a weekday in the month. Negative n counts from end. `lastInMonth(day)` finds the last occurrence.

---

### Custom adjuster implementation

```java
import java.time.temporal.TemporalAdjuster;
import java.time.temporal.Temporal;

// Adjuster: move to next business day (skip weekends)
TemporalAdjuster nextBusinessDay = temporal -> {
    LocalDate date = LocalDate.from(temporal);
    DayOfWeek dow = date.getDayOfWeek();
    int daysToAdd = switch (dow) {
        case FRIDAY   -> 3; // Friday + 3 = Monday
        case SATURDAY -> 2; // Saturday + 2 = Monday
        default       -> 1; // any other day + 1
    };
    return date.plusDays(daysToAdd);
};

LocalDate friday   = LocalDate.of(2024, 3, 15); // Friday
LocalDate saturday = LocalDate.of(2024, 3, 16); // Saturday
LocalDate tuesday  = LocalDate.of(2024, 3, 12); // Tuesday

System.out.println(friday.with(nextBusinessDay));   // 2024-03-18 (Monday)
System.out.println(saturday.with(nextBusinessDay)); // 2024-03-18 (Monday)
System.out.println(tuesday.with(nextBusinessDay));  // 2024-03-13 (Wednesday)
```

**What this does:** `TemporalAdjuster` is a `@FunctionalInterface` — implement it as a lambda. The lambda receives the `Temporal`, computes the new value, and returns it. Plugs cleanly into `.with()`.

---

## 9. Legacy Bridge

### The conversion map

```
java.util.Date  ←→  java.time.Instant  ←→  ZonedDateTime / LocalDateTime
java.util.Calendar  →  Instant
long (epoch ms)  →  Instant
```

---

### Date ↔ Instant

```java
import java.util.Date;
import java.time.Instant;

// Legacy Date → Instant
Date legacyDate = new Date();
Instant instant = legacyDate.toInstant();

// Instant → legacy Date (for legacy API compatibility)
Instant now = Instant.now();
Date backToDate = Date.from(now);

System.out.println(instant);    // 2024-03-15T14:30:00.000Z
System.out.println(backToDate); // Fri Mar 15 14:30:00 UTC 2024
```

**What this does:** `Date.toInstant()` and `Date.from(Instant)` are the canonical bridge methods added in Java 8 to `java.util.Date` itself.

---

### Calendar → Instant

```java
import java.util.Calendar;

Calendar cal = Calendar.getInstance();
cal.set(2024, Calendar.MARCH, 15); // still 0-indexed months in Calendar!

Instant fromCal = cal.toInstant();
```

**What this does:** `Calendar.toInstant()` also added in Java 8. Note Calendar months are still 0-indexed — this is the legacy API's problem, not `java.time`.

---

### epoch millis ↔ Instant

```java
long epochMs = System.currentTimeMillis();

Instant fromEpoch = Instant.ofEpochMilli(epochMs);
Instant fromEpochSec = Instant.ofEpochSecond(1710508200L);

long backToMs = fromEpoch.toEpochMilli();
```

**What this does:** `Instant.ofEpochMilli` is the bridge for timestamps stored as `long` (common in databases, Kafka, Redis). `toEpochMilli()` converts back.

---

### Full migration pattern

```java
// BEFORE: legacy pattern
public Date addBusinessDays(Date inputDate, int days) {
    Calendar cal = Calendar.getInstance();
    cal.setTime(inputDate);
    // ... messy calendar arithmetic
    return cal.getTime();
}

// AFTER: java.time pattern, legacy boundary at method signature
public Date addBusinessDays(Date inputDate, int days) {
    LocalDate date = inputDate.toInstant()
        .atZone(ZoneId.systemDefault())
        .toLocalDate();

    int added = 0;
    while (added < days) {
        date = date.plusDays(1);
        if (date.getDayOfWeek() != DayOfWeek.SATURDAY
         && date.getDayOfWeek() != DayOfWeek.SUNDAY) {
            added++;
        }
    }

    return Date.from(date.atStartOfDay(ZoneId.systemDefault()).toInstant());
}
```

**What this does:** convert `Date` → `Instant` → `LocalDate` at the entry point, do all logic in `java.time`, convert `LocalDate` → `Instant` → `Date` at the exit. The method signature stays `Date` for callers not yet migrated.

---

### Instant ↔ ZonedDateTime ↔ LocalDateTime

```java
Instant instant = Instant.parse("2024-03-15T14:30:00Z");

// Instant → ZonedDateTime (need a zone to interpret the instant as local time)
ZonedDateTime zdt = instant.atZone(ZoneId.of("America/New_York"));
// 2024-03-15T10:30-04:00[America/New_York]  (14:30 UTC = 10:30 EDT)

// ZonedDateTime → LocalDateTime (strip zone info)
LocalDateTime ldt = zdt.toLocalDateTime();
// 2024-03-15T10:30

// LocalDateTime → ZonedDateTime (attach zone)
ZonedDateTime backToZdt = ldt.atZone(ZoneId.of("America/New_York"));

// ZonedDateTime → Instant
Instant backToInstant = backToZdt.toInstant();
```

**What this does:** `Instant` is always UTC. To render it to a user you need a zone. `atZone()` bridges Instant → ZonedDateTime. Stripping to `LocalDateTime` loses timezone context permanently.

> ⚠️ **Pitfall:** `LocalDateTime → Instant` directly is not possible (no zone info). You must go through `ZonedDateTime` or `OffsetDateTime`: `ldt.atZone(zone).toInstant()`.

---

## Quick Reference

```
Creation:
  LocalDate.now() / .of(y,m,d) / .parse("2024-03-15")
  LocalTime.now() / .of(h,m,s) / .parse("14:30:00")
  LocalDateTime.of(date, time) / date.atTime(time)
  ZonedDateTime.now(zone) / ldt.atZone(zone)
  Instant.now() / .ofEpochMilli(ms) / .parse("...Z")

Manipulation (always returns new instance):
  plus/minus: Days, Weeks, Months, Years, Hours, Minutes, Seconds
  with:       withYear, withMonth, withDayOfMonth, with(adjuster)
  truncate:   truncatedTo(ChronoUnit.MINUTES)

Comparison:
  isBefore(other) / isAfter(other) / isEqual(other) / equals(other)

Duration (time-based):
  Duration.between(t1, t2)
  .toHours() / .toMinutes() / .toSeconds()
  .toHoursPart() / .toMinutesPart()  [Java 9+]

Period (date-based):
  Period.between(d1, d2)
  .getYears() / .getMonths() / .getDays()

Formatting:
  DateTimeFormatter.ISO_LOCAL_DATE / ISO_INSTANT / RFC_1123_DATE_TIME
  DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm:ss")
  date.format(formatter) / LocalDate.parse(str, formatter)

Adjusters:
  .with(TemporalAdjusters.firstDayOfMonth())
  .with(TemporalAdjusters.next(DayOfWeek.MONDAY))
  .with(TemporalAdjusters.lastDayOfYear())

Legacy bridge:
  date.toInstant()          Date → Instant
  Date.from(instant)        Instant → Date
  instant.atZone(zone)      Instant → ZonedDateTime
  zdt.toInstant()           ZonedDateTime → Instant
  Instant.ofEpochMilli(ms)  long → Instant
```
