---
card: java
gi: 692
slug: day-period-support-in-datetimeformatter
title: Day Period support in DateTimeFormatter
---

## 1. What it is

**Java 16** added support for the **"B" pattern letter** in `DateTimeFormatter` (JEP-less small enhancement, part of JSR 310 date-time API evolution), which formats a time using a locale-aware **flexible day period** — phrases like "in the morning," "at night," "noon," or "midnight" — instead of, or alongside, the traditional fixed AM/PM markers produced by the "a" pattern letter. Many locales (and the Unicode CLDR data Java's date-time formatting draws on) don't naturally split a day into just two halves the way the English AM/PM convention does; some languages have several named periods (early morning, morning, afternoon, evening, night) with locale-specific boundary times, and "B" surfaces that richer distinction.

## 2. Why & when

Software that displays times to end users often wants to phrase them naturally in the reader's language and cultural convention — and "9:00 AM" translated literally into some locales produces something that reads as stiff or simply wrong compared to how a native speaker of that language would naturally describe that time of day. CLDR (the Unicode Common Locale Data Repository) already encoded these richer, locale-specific day-period phrases and their time boundaries; before Java 16, `DateTimeFormatter` had no direct pattern letter to access that data — you were limited to AM/PM regardless of locale. The "B" pattern letter exposes CLDR's flexible day-period data directly through the standard formatting API. Reach for it whenever you're formatting a time for end-user display (as opposed to machine-readable timestamps, which should use ISO-8601 or similar unambiguous formats) and want the display to read naturally in the target locale, especially in an internationalized application supporting multiple locales.

## 3. Core concept

```java
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

LocalTime time = LocalTime.of(7, 30);

DateTimeFormatter withAmPm = DateTimeFormatter.ofPattern("h:mm a", Locale.US);
System.out.println(time.format(withAmPm)); // 7:30 AM

DateTimeFormatter withDayPeriod = DateTimeFormatter.ofPattern("h:mm B", Locale.US);
System.out.println(time.format(withDayPeriod)); // 7:30 in the morning
```

The underlying `LocalTime` value is identical in both cases — only the formatting pattern differs, producing either the traditional two-way AM/PM split or CLDR's richer, locale-aware day-period phrase.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Pattern letter a produces AM or PM; pattern letter B produces a locale-aware flexible day period phrase such as in the morning or at night">
  <rect x="20" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Pattern "a" (AM/PM)</text>
  <text x="160" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">7:30 AM</text>
  <text x="160" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">2:00 PM</text>
  <text x="160" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">always exactly 2 fixed periods</text>

  <rect x="340" y="20" width="280" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Pattern "B" (day period)</text>
  <text x="480" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">7:30 in the morning</text>
  <text x="480" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">2:00 in the afternoon</text>
  <text x="480" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">locale-defined, can be more than 2 periods</text>
</svg>

The same instant in time can be described with a coarse two-way split or a richer, culturally natural set of named periods.

## 5. Runnable example

Scenario: a small "time of day" display utility — first comparing AM/PM against day-period formatting for a handful of times, then iterating across a full day to see every distinct day-period phrase CLDR defines for a locale, then building a small greeting generator that reacts to the day period rather than to raw hour values.

### Level 1 — Basic

```java
// File: DayPeriodBasic.java
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

public class DayPeriodBasic {
    public static void main(String[] args) {
        DateTimeFormatter amPm = DateTimeFormatter.ofPattern("h:mm a", Locale.US);
        DateTimeFormatter dayPeriod = DateTimeFormatter.ofPattern("h:mm B", Locale.US);

        LocalTime[] times = {
                LocalTime.of(7, 30), LocalTime.of(13, 0),
                LocalTime.of(20, 15), LocalTime.of(0, 0)
        };

        for (LocalTime t : times) {
            System.out.println(t.format(amPm) + "  |  " + t.format(dayPeriod));
        }
    }
}
```

**How to run:** `java DayPeriodBasic.java`

Expected output:
```
7:30 AM  |  7:30 in the morning
1:00 PM  |  1:00 in the afternoon
8:15 PM  |  8:15 in the evening
12:00 AM  |  12:00 midnight
```

### Level 2 — Intermediate

```java
// File: DayPeriodSurvey.java
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashSet;
import java.util.Locale;
import java.util.Set;

public class DayPeriodSurvey {
    public static void main(String[] args) {
        DateTimeFormatter dayPeriod = DateTimeFormatter.ofPattern("B", Locale.US);
        Set<String> distinctPeriods = new LinkedHashSet<>();

        for (int hour = 0; hour < 24; hour++) {
            LocalTime t = LocalTime.of(hour, 0);
            distinctPeriods.add(t.format(dayPeriod));
        }

        System.out.println("Distinct day periods across 24 hours, in order of first appearance:");
        distinctPeriods.forEach(p -> System.out.println("  " + p));
    }
}
```

**How to run:** `java DayPeriodSurvey.java`

Expected output (using the `en_US` CLDR day-period boundaries; sampling on the hour catches both instantaneous periods, `midnight` at exactly 00:00 and `noon` at exactly 12:00, alongside the broader ranged periods):
```
Distinct day periods across 24 hours, in order of first appearance:
  midnight
  at night
  in the morning
  noon
  in the afternoon
  in the evening
```

### Level 3 — Advanced

```java
// File: GreetingByDayPeriod.java
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.util.Locale;

public class GreetingByDayPeriod {
    static String greetingFor(LocalTime time) {
        DateTimeFormatter dayPeriod = DateTimeFormatter.ofPattern("B", Locale.US);
        String period = time.format(dayPeriod);

        return switch (period) {
            case "in the morning" -> "Good morning!";
            case "in the afternoon" -> "Good afternoon!";
            case "in the evening" -> "Good evening!";
            case "at night", "midnight" -> "Working late, or just up early?";
            default -> "Hello!";
        };
    }

    public static void main(String[] args) {
        DateTimeFormatter display = DateTimeFormatter.ofPattern("h:mm B", Locale.US);
        LocalTime[] times = {
                LocalTime.of(6, 45), LocalTime.of(12, 30),
                LocalTime.of(18, 0), LocalTime.of(23, 45), LocalTime.of(3, 0)
        };

        for (LocalTime t : times) {
            System.out.println(t.format(display) + " -> " + greetingFor(t));
        }
    }
}
```

**How to run:** `java GreetingByDayPeriod.java`

Expected output:
```
6:45 in the morning -> Good morning!
12:30 in the afternoon -> Good afternoon!
6:00 in the evening -> Good evening!
11:45 at night -> Working late, or just up early?
3:00 at night -> Working late, or just up early?
```

Level 3 uses the day-period *string itself* as a dispatch key inside a `switch` expression, producing a context-appropriate greeting — a natural use case, since "morning," "afternoon," and "evening" map far more directly onto conversational greetings than a raw hour number or an AM/PM flag would.

## 6. Walkthrough

1. `greetingFor(time)` first formats `time` using the pattern `"B"` (day period only, no hour/minute) under `Locale.US`, producing one of CLDR's English day-period phrases: `"in the morning"`, `"in the afternoon"`, `"in the evening"`, `"at night"`, `"noon"`, or `"midnight"` depending on which time-of-day bucket `time` falls into according to `en_US`'s CLDR boundary data.
2. That resulting `period` string is then used as the subject of a `switch` expression, where each `case` matches one of the known day-period phrases and returns a distinct greeting; the `"at night", "midnight"` case shows a `switch` arm matching **multiple** labels with one comma-separated case, both mapping to the same result.
3. In `main`, `display` is a separate `DateTimeFormatter` combining `"h:mm B"` — hour, minute, and the day period together — used purely for readable console output alongside each greeting.
4. For `LocalTime.of(6, 45)` (6:45 AM), the day period resolves to `"in the morning"`, triggering the `"Good morning!"` case.
5. For `LocalTime.of(12, 30)` (12:30 PM), the period resolves to `"in the afternoon"` (CLDR's `en_US` boundary places early afternoon starting around noon), triggering `"Good afternoon!"`.
6. For `LocalTime.of(18, 0)` (6:00 PM), the period resolves to `"in the evening"`, triggering `"Good evening!"`.
7. For `LocalTime.of(23, 45)` (11:45 PM) and `LocalTime.of(3, 0)` (3:00 AM), both resolve to `"at night"` under `en_US`'s CLDR data (night spans across midnight, covering both late evening and early morning hours before the "morning" period proper begins), so both trigger the same `"Working late, or just up early?"` case — illustrating that a day period can span across the midnight boundary rather than resetting exactly at `00:00`.
8. Each iteration in `main`'s loop prints the formatted time-with-day-period string alongside the greeting `greetingFor` returned, giving a readable, line-by-line demonstration of how five different times of day map to five (with one repeated) natural-language greetings.

```
LocalTime ──format("B")──► day-period phrase (locale-defined boundaries)
                                    │
                         switch(period) { case "in the morning" -> ...; ... }
                                    │
                              context-appropriate greeting
```

## 7. Gotchas & takeaways

> The exact set of day-period phrases and their time boundaries are **defined by CLDR data for each locale**, not by a fixed, universal rule — `"noon"`/`"midnight"` may or may not appear as distinct periods depending on locale and JDK/CLDR version, and boundary times (where "morning" ends and "afternoon" begins) can shift between CLDR data updates bundled with different JDK releases. Don't hard-code an exhaustive `switch` over day-period strings without a `default` case, since the exact set of possible values isn't a fixed, documented contract you can rely on staying identical forever.

- The `"a"` pattern letter (AM/PM) remains available and unaffected — `"B"` is an additional, alternative pattern letter, not a replacement.
- Because day-period phrases and boundaries are locale-dependent, always pass an explicit `Locale` to `DateTimeFormatter.ofPattern(pattern, locale)` rather than relying on the JVM's default locale, especially in code whose output will be compared against fixed expected strings (as in automated tests).
- `"B"` is intended for **human-facing display**, not machine-parseable output — never format a timestamp with `"B"` for logs, APIs, or anything meant to be parsed back programmatically; use ISO-8601 (`DateTimeFormatter.ISO_LOCAL_TIME` or similar) for those.
- Combining `"B"` with hour/minute patterns (e.g. `"h:mm B"`) produces a natural, readable display string in one call, without manually computing which day-period bucket a given time falls into.
- If your target locale's day-period set turns out to only have two values in practice (effectively behaving like AM/PM), that's expected — CLDR's day-period richness varies significantly by locale, and some locales genuinely don't distinguish more finely than a rough morning/evening split.
