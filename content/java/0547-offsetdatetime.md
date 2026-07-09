---
card: java
gi: 547
slug: offsetdatetime
title: OffsetDateTime
---

## 1. What it is

`OffsetDateTime` combines a `LocalDateTime` with a `ZoneOffset` — a date, a time, and a fixed UTC offset, but critically, **no** named region and **no** daylight-saving rules. It sits between `LocalDateTime` (no offset at all) and `ZonedDateTime` (a full named region with DST rules): `OffsetDateTime` knows "this local time is exactly 5 hours behind UTC," but has no idea *which region* that offset came from or whether that offset might change on a different date.

## 2. Why & when

`OffsetDateTime` is the right choice when you need an unambiguous point in time (like `Instant`) but *also* want to preserve the original local date/time values it was expressed in — common for APIs, database columns, and serialized formats where a timestamp comes with an explicit offset (`"2026-07-09T14:00:00+02:00"`) but no meaningful named region is available or needed. It's less commonly used directly in application logic than `Instant` or `ZonedDateTime`, but it shows up constantly at API/serialization boundaries, since many systems (including much of SQL's `TIMESTAMP WITH TIME ZONE`) store exactly this: local values plus a fixed offset, with no region information retained.

## 3. Core concept

```java
import java.time.*;

OffsetDateTime event = OffsetDateTime.of(2026, 7, 9, 14, 30, 0, 0, ZoneOffset.of("+02:00"));

Instant asInstant = event.toInstant(); // convert to a universal point -- offset is applied, then discarded
LocalDateTime asLocal = event.toLocalDateTime(); // strip the offset, keep just the local values

OffsetDateTime parsed = OffsetDateTime.parse("2026-07-09T14:30:00+02:00"); // typical API timestamp format

System.out.println(event); // 2026-07-09T14:30+02:00
```

`OffsetDateTime` carries local date-time values plus a fixed offset, with no concept of a named region or that offset ever changing — a simpler cousin of `ZonedDateTime`.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="OffsetDateTime combines local date-time values with a fixed offset, with no named region or DST awareness">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="600" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="320" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="monospace">2026-07-09T14:30+02:00  (no region name, just a fixed offset)</text>
  <text x="20" y="80" fill="#8b949e" font-size="10" font-family="sans-serif">Compare: ZonedDateTime = local + NAMED ZONE (rules-aware, DST-aware)</text>
  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">         OffsetDateTime = local + FIXED OFFSET (no rules, no DST awareness)</text>
</svg>

`OffsetDateTime` sits between `LocalDateTime` and `ZonedDateTime`: it has a fixed offset (unlike `LocalDateTime`) but no region or DST rules (unlike `ZonedDateTime`).

## 5. Runnable example

Scenario: parsing and processing API timestamps that arrive with explicit offsets but no named region — evolved from basic construction and conversion, through parsing typical API-style timestamp strings, to a version demonstrating why `OffsetDateTime` cannot correctly perform date arithmetic across a DST boundary the way `ZonedDateTime` can.

### Level 1 — Basic

```java
import java.time.*;

public class OffsetDateTimeBasic {
    public static void main(String[] args) {
        OffsetDateTime event = OffsetDateTime.of(2026, 7, 9, 14, 30, 0, 0, ZoneOffset.of("+02:00"));

        System.out.println("Event: " + event);
        System.out.println("Offset: " + event.getOffset());
        System.out.println("As Instant: " + event.toInstant());
    }
}
```

**How to run:** `java OffsetDateTimeBasic.java`

Expected output:
```
Event: 2026-07-09T14:30+02:00
Offset: +02:00
As Instant: 2026-07-09T12:30:00Z
```

`OffsetDateTime.of(...)` combines local date-time values with a fixed offset, `+02:00`. `.toInstant()` converts this into a universal `Instant` by subtracting the offset from the local time: `14:30` minus `2` hours is `12:30` UTC — this conversion is exact and unambiguous, since a fixed offset (unlike a named zone) requires no rule lookup at all.

### Level 2 — Intermediate

```java
import java.time.*;

public class OffsetDateTimeParsing {
    public static void main(String[] args) {
        // Typical API/JSON timestamp formats -- explicit offset, no named region.
        OffsetDateTime fromApi1 = OffsetDateTime.parse("2026-07-09T14:30:00+02:00");
        OffsetDateTime fromApi2 = OffsetDateTime.parse("2026-07-09T09:30:00-03:00");

        System.out.println("API timestamp 1: " + fromApi1);
        System.out.println("API timestamp 2: " + fromApi2);

        // Both represent the SAME instant, despite different local values and offsets.
        boolean sameInstant = fromApi1.toInstant().equals(fromApi2.toInstant());
        System.out.println("Same instant: " + sameInstant);
    }
}
```

**How to run:** `java OffsetDateTimeParsing.java`

Expected output:
```
API timestamp 1: 2026-07-09T14:30+02:00
API timestamp 2: 2026-07-09T09:30-03:00
Same instant: true
```

The real-world concern this adds: parsing timestamps directly from typical API/JSON payloads, which commonly include an explicit numeric offset rather than a named region — `OffsetDateTime.parse(...)` handles this format directly. `14:30+02:00` and `09:30-03:00` represent local times with different offsets, but converting both to UTC (`14:30 - 2:00 = 12:30`, `09:30 + 3:00 = 12:30`) reveals they describe the exact same underlying instant.

### Level 3 — Advanced

```java
import java.time.*;

public class OffsetDateTimeVsZonedArithmetic {
    public static void main(String[] args) {
        // OffsetDateTime: a FIXED offset, captured once, that does NOT know about DST rules.
        OffsetDateTime offsetBased = OffsetDateTime.of(2026, 3, 1, 10, 0, 0, 0, ZoneOffset.of("-05:00"));

        // ZonedDateTime: a NAMED zone that DOES know DST rules for America/New_York.
        ZonedDateTime zoneBased = ZonedDateTime.of(2026, 3, 1, 10, 0, 0, 0, ZoneId.of("America/New_York"));

        // Add 10 days to each -- this crosses the March 8, 2026 DST transition.
        OffsetDateTime offsetPlus10Days = offsetBased.plusDays(10);
        ZonedDateTime zonePlus10Days = zoneBased.plusDays(10);

        System.out.println("OffsetDateTime + 10 days: " + offsetPlus10Days); // offset STAYS -05:00 -- WRONG for this date
        System.out.println("ZonedDateTime + 10 days:   " + zonePlus10Days);  // offset CORRECTLY becomes -04:00

        boolean offsetsDiffer = !offsetPlus10Days.getOffset().equals(zonePlus10Days.getOffset());
        System.out.println("Offsets now differ: " + offsetsDiffer);
    }
}
```

**How to run:** `java OffsetDateTimeVsZonedArithmetic.java`

Expected output:
```
OffsetDateTime + 10 days: 2026-03-11T10:00-05:00
ZonedDateTime + 10 days:   2026-03-11T10:00-04:00[America/New_York]
Offsets now differ: true
```

This demonstrates `OffsetDateTime`'s fundamental limitation: its offset is **fixed** and never automatically updates, even when arithmetic crosses a genuine DST transition. `offsetBased.plusDays(10)` starts at March 1st (`-05:00`, EST) and lands on March 11th — but since March 8th's DST transition already occurred by then, the *correct* offset for March 11th in New York is `-04:00` (EDT), not `-05:00`. `OffsetDateTime` has no way to know this, since it carries no region information at all — it simply keeps the same offset, silently producing a date-time value whose offset no longer matches what the *same local clock in New York* would actually show. `ZonedDateTime`, by contrast, correctly detects the transition: date-based additions like `plusDays` preserve the local wall-clock time (`10:00` stays `10:00`), while the offset is re-derived from the zone's rules for the new date, correctly updating to `-04:00`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `offsetBased` is `2026-03-01T10:00-05:00` — a fixed offset of `-05:00`, matching New York's winter (EST) offset at the time of construction. `zoneBased` is `2026-03-01T10:00` in the named zone `America/New_York`, which at this same starting date also resolves to `-05:00`.

`offsetBased.plusDays(10)` performs simple calendar arithmetic on the local date-time value: March 1st plus `10` days is March 11th. Crucially, `OffsetDateTime.plusDays(...)` does **not** re-derive the offset from any rule set — it has no rule set to consult — so the offset field simply stays exactly as it was, `-05:00`, regardless of what date the arithmetic landed on. The result is `2026-03-11T10:00-05:00`.

`zoneBased.plusDays(10)` performs the equivalent calendar arithmetic, but because `zoneBased` carries a `ZoneId` (not just a fixed offset), `ZonedDateTime`'s `plusDays(...)` implementation is documented to preserve the *local wall-clock time* through date-based additions, then re-derive the correct offset from the zone's rules for the resulting date. March 11, 2026 falls after the March 8th "spring forward" transition, so `America/New_York`'s rules now say the correct offset is `-04:00` (EDT), not `-05:00`. The local hour stays `10:00` exactly as it was — `plusDays` means "the same wall-clock time, 10 calendar days later" — but the offset is correctly recalculated to `-04:00`, accurately reflecting that this particular March 11th falls within daylight saving time.

```
offsetBased = 2026-03-01T10:00-05:00 (fixed offset, no DST awareness)
  .plusDays(10): local date-time -> 2026-03-11T10:00, offset UNCHANGED -05:00 (never re-derived)
  result: 2026-03-11T10:00-05:00  <- offset is now WRONG for this date in reality

zoneBased = 2026-03-01T10:00 in America/New_York (rules-aware)
  .plusDays(10): calendar date -> March 11, THEN re-derive offset from zone rules for that date
  March 11 is after the March 8 DST transition -> correct offset is -04:00, not -05:00
  result: 2026-03-11T10:00-04:00[America/New_York]  <- local hour PRESERVED, offset correctly re-derived
```

`offsetPlus10Days.getOffset()` is `-05:00`; `zonePlus10Days.getOffset()` is `-04:00` — these differ, so `offsetsDiffer` is `true`, printed as `"Offsets now differ: true"`. This concretely demonstrates that `OffsetDateTime` arithmetic silently accumulates DST-related drift whenever it crosses a transition boundary, while `ZonedDateTime` arithmetic correctly self-corrects, precisely because only `ZonedDateTime` carries the rule set needed to detect and account for such transitions.

## 7. Gotchas & takeaways

> `OffsetDateTime`'s arithmetic methods (`plusDays`, `plusMonths`, etc.) never re-derive or validate the offset against any rule set, because `OffsetDateTime` has no rule set — the offset simply stays exactly as originally specified, potentially becoming incorrect the moment a calculation crosses a real-world DST transition. This is a fundamental, documented limitation, not a bug — `OffsetDateTime` is designed for representing a fixed offset at a point in time, not for performing calendar-aware arithmetic across regions with DST.

- `OffsetDateTime` combines local date-time values with a fixed `ZoneOffset` — no named region, no DST rules, unlike `ZonedDateTime`.
- It's most commonly encountered parsing timestamps from APIs, databases, or serialized formats that include an explicit numeric offset but no region name.
- `.toInstant()` converts an `OffsetDateTime` to a universal point in time by simply applying the fixed offset — no rule lookup needed, since the offset is already explicit.
- Arithmetic on `OffsetDateTime` (`plusDays`, etc.) never updates the offset, even when the calculation crosses a genuine DST transition — this can silently produce a date-time value that's off by the DST shift amount from what the equivalent `ZonedDateTime` arithmetic would produce.
- Prefer `ZonedDateTime` over `OffsetDateTime` whenever you need to perform date/time arithmetic that might cross a DST boundary in a specific region; reserve `OffsetDateTime` for representing already-resolved timestamps with a known, fixed offset, typically at API/serialization boundaries.
