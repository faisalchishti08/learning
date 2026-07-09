---
card: java
gi: 546
slug: zoneddatetime
title: ZonedDateTime
---

## 1. What it is

`ZonedDateTime` combines a `LocalDateTime` with a `ZoneId`, representing a specific date and time *in a specific named timezone*, with full daylight-saving awareness. It's the most complete of the `java.time` types: it knows the year, month, day, hour, minute, second, which timezone region applies, and — because it consults that zone's rules — the correct UTC offset for that exact moment, accounting for DST if applicable.

## 2. Why & when

Use `ZonedDateTime` whenever you need to represent "this specific wall-clock moment, in this specific place" — a meeting scheduled for "9 AM in Tokyo," a flight departing "at 14:30 in New York," anything where both the local time-of-day *and* the region's specific DST rules matter together. It sits between `LocalDateTime` (which has no timezone at all) and `Instant` (which has no "local" concept at all, just a universal point) — `ZonedDateTime` is what you reach for when you genuinely need both.

## 3. Core concept

```java
import java.time.*;

ZonedDateTime meeting = ZonedDateTime.of(2026, 7, 9, 14, 30, 0, 0, ZoneId.of("America/New_York"));

Instant asInstant = meeting.toInstant();          // convert to a universal point in time
LocalDateTime asLocal = meeting.toLocalDateTime(); // strip the zone, keep just the local values

ZonedDateTime inTokyo = meeting.withZoneSameInstant(ZoneId.of("Asia/Tokyo"));
// same INSTANT, but displayed in Tokyo's local time -- the clock values change, the instant doesn't

System.out.println(meeting);   // 2026-07-09T14:30-04:00[America/New_York]
System.out.println(inTokyo);   // 2026-07-10T03:30+09:00[Asia/Tokyo] -- same moment, different wall clock
```

`ZonedDateTime` carries local date/time values, a `ZoneId`, and (derived from the zone's rules for that moment) the correct offset — `withZoneSameInstant(...)` re-expresses the same underlying instant through a different zone's local perspective.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ZonedDateTime combines a LocalDateTime with a ZoneId, deriving the correct offset from the zone's rules">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="150" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="95" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">2026-07-09T14:30</text>
  <text x="185" y="40" fill="#8b949e" font-size="14" font-family="sans-serif">+</text>
  <rect x="200" y="20" width="180" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="290" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">America/New_York</text>
  <text x="400" y="40" fill="#8b949e" font-size="14" font-family="sans-serif">=</text>
  <rect x="420" y="20" width="200" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="520" y="40" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">2026-07-09T14:30-04:00[...]</text>
  <text x="20" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">The offset (-04:00) is DERIVED from the zone's rules for this specific date -- not stored independently.</text>
</svg>

`ZonedDateTime` combines local date-time values with a zone, and derives the correct offset from that zone's rules for the specific date given.

## 5. Runnable example

Scenario: scheduling an international video call and displaying the correct local time for participants in different cities — evolved from basic `ZonedDateTime` construction, through converting the same moment across zones, to a version handling a scheduling conflict caused by DST transitions in different regions occurring on different dates.

### Level 1 — Basic

```java
import java.time.*;

public class ZonedDateTimeBasic {
    public static void main(String[] args) {
        ZonedDateTime meeting = ZonedDateTime.of(
                2026, 7, 9, 14, 30, 0, 0, ZoneId.of("America/New_York"));

        System.out.println("Meeting time: " + meeting);
        System.out.println("Zone: " + meeting.getZone());
        System.out.println("Offset: " + meeting.getOffset());
    }
}
```

**How to run:** `java ZonedDateTimeBasic.java`

Expected output:
```
Meeting time: 2026-07-09T14:30-04:00[America/New_York]
Zone: America/New_York
Offset: -04:00
```

`ZonedDateTime.of(...)` constructs a specific local date-time paired with a named zone. The printed representation includes all three pieces: the local date-time, the derived offset (`-04:00`, since July falls within New York's daylight saving period), and the zone name in brackets. `.getOffset()` retrieves just the numeric offset that was automatically derived from the zone's rules for this specific date.

### Level 2 — Intermediate

```java
import java.time.*;

public class ZonedDateTimeConversion {
    public static void main(String[] args) {
        ZonedDateTime meetingInNewYork = ZonedDateTime.of(
                2026, 7, 9, 14, 30, 0, 0, ZoneId.of("America/New_York"));

        ZonedDateTime sameForLondon = meetingInNewYork.withZoneSameInstant(ZoneId.of("Europe/London"));
        ZonedDateTime sameForTokyo = meetingInNewYork.withZoneSameInstant(ZoneId.of("Asia/Tokyo"));

        System.out.println("New York: " + meetingInNewYork.toLocalTime());
        System.out.println("London:   " + sameForLondon.toLocalTime());
        System.out.println("Tokyo:    " + sameForTokyo.toLocalTime());

        boolean sameInstant = meetingInNewYork.toInstant().equals(sameForLondon.toInstant());
        System.out.println("Same underlying instant: " + sameInstant);
    }
}
```

**How to run:** `java ZonedDateTimeConversion.java`

Expected output:
```
New York: 14:30
London:   19:30
Tokyo:    03:30
```
(Tokyo's date rolls forward to the next day, so the full timestamp is 2026-07-10T03:30 there)
```
Same underlying instant: true
```

The real-world concern this adds: `.withZoneSameInstant(...)` re-expresses the *same underlying moment* through a different region's local perspective — the actual instant in universal time never changes, only how it's displayed. New York's `14:30` corresponds to London's `19:30` (5 hours ahead, accounting for both zones' respective DST status in July) and Tokyo's `03:30` the *next calendar day* (Tokyo being far enough ahead that the date itself rolls over). The final check confirms all three `ZonedDateTime` values, despite showing different local times, represent the exact same `Instant`.

### Level 3 — Advanced

```java
import java.time.*;

public class ZonedDateTimeDstGap {
    public static void main(String[] args) {
        // A genuinely tricky case: a time that doesn't EXIST due to a DST "spring forward" transition.
        // In the US in 2026, clocks spring forward on March 8th at 2:00 AM -> jumps straight to 3:00 AM.
        ZonedDateTime beforeGap = ZonedDateTime.of(
                2026, 3, 8, 1, 30, 0, 0, ZoneId.of("America/New_York"));

        // 2:30 AM on March 8, 2026 in New York DOES NOT EXIST -- it's skipped by the spring-forward.
        ZonedDateTime duringGap = ZonedDateTime.of(
                2026, 3, 8, 2, 30, 0, 0, ZoneId.of("America/New_York"));

        System.out.println("Before the gap (1:30 AM): " + beforeGap);
        System.out.println("Requested 2:30 AM (doesn't exist -- gets adjusted): " + duringGap);

        // Java resolves this by shifting the invalid time FORWARD by the gap's length (1 hour here).
        boolean wasAdjusted = duringGap.getHour() != 2;
        System.out.println("Time was automatically adjusted: " + wasAdjusted);
    }
}
```

**How to run:** `java ZonedDateTimeDstGap.java`

Expected output:
```
Before the gap (1:30 AM): 2026-03-08T01:30-05:00[America/New_York]
Requested 2:30 AM (doesn't exist -- gets adjusted): 2026-03-08T03:30-04:00[America/New_York]
Time was automatically adjusted: true
```

This handles a genuinely tricky DST edge case: when clocks "spring forward," an entire hour of local time (here, `2:00 AM` to `3:00 AM` on March 8, 2026) simply **does not exist** in New York's local clock. Requesting `ZonedDateTime.of(..., 2, 30, ...)` for a moment that falls inside this gap doesn't throw an exception — instead, `java.time`'s documented behavior shifts the requested time *forward* by the length of the gap, landing on `03:30` instead of the requested (nonexistent) `02:30`, with the offset also correctly updating from `-05:00` (EST, before the transition) to `-04:00` (EDT, after it).

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `beforeGap` is constructed as `2026-03-08T01:30` in New York — a perfectly ordinary, existing local time, safely before the DST transition. Since March 8th at `01:30` is still before the spring-forward moment (which occurs at `2:00 AM` local time), New York is still on Eastern Standard Time at this point, so the offset is `-05:00`. Printed as `"2026-03-08T01:30-05:00[America/New_York]"`.

`duringGap` is constructed requesting `2026-03-08T02:30` in New York. Internally, `ZonedDateTime.of(...)` consults `America/New_York`'s DST rules for this date and discovers that the requested local time, `02:30`, falls squarely within the "spring forward" gap — the moment clocks jump from `2:00 AM` directly to `3:00 AM`, so no `2:xx AM` time exists at all on this particular date in this zone.

Java's `java.time` framework resolves this ambiguity with documented, deterministic behavior: it shifts the requested local time forward by exactly the length of the gap (one hour, in this case), producing `03:30` instead of the nonexistent `02:30`. Since `03:30` falls *after* the transition, the offset for this adjusted time is `-04:00` (EDT, the new daylight-saving offset). The full result prints as `"2026-03-08T03:30-04:00[America/New_York]"`.

```
Requested: 2026-03-08T02:30 in America/New_York

DST rule check: on March 8, 2026, clocks spring forward at 2:00 AM -> 3:00 AM instantly
  -> the entire range [2:00 AM, 3:00 AM) does not exist locally

02:30 falls inside this gap -> Java shifts it FORWARD by the gap length (1 hour)
  -> adjusted result: 03:30, with offset correctly updated to -04:00 (EDT, post-transition)
```

`duringGap.getHour()` is `3` (from the adjusted `03:30`), not the originally-requested `2` — so `duringGap.getHour() != 2` is `true`, printed as `"Time was automatically adjusted: true"`, confirming that Java silently and predictably resolved the impossible request rather than throwing an exception or producing an invalid state.

## 7. Gotchas & takeaways

> Two categories of DST edge cases exist: "spring forward" gaps (a local time that doesn't exist at all, silently shifted forward, as shown in Level 3) and "fall back" overlaps (a local time that occurs *twice*, once before and once after clocks are set back — `java.time` resolves this ambiguity by defaulting to the *earlier* of the two occurrences unless told otherwise). Both are real, documented behaviors worth being aware of whenever scheduling logic touches a DST transition boundary.

- `ZonedDateTime` combines a `LocalDateTime` with a `ZoneId`, deriving the correct UTC offset from that zone's rules for the specific date given.
- `.withZoneSameInstant(newZone)` re-expresses the same underlying moment through a different zone's local perspective — the instant stays fixed, only the displayed local values and offset change.
- `.toInstant()` extracts the universal, timezone-independent moment; `.toLocalDateTime()` extracts just the local date-time values, discarding the zone information.
- "Spring forward" DST transitions create a gap of local times that don't exist at all — `java.time` silently shifts a requested time inside this gap forward by the gap's length rather than throwing an exception.
- Always use `ZonedDateTime` (not `LocalDateTime`) when a specific real-world moment tied to a specific region genuinely matters, since only `ZonedDateTime` correctly and automatically accounts for that region's daylight-saving behavior.
