---
card: java
gi: 285
slug: java-util-date-legacy
title: java.util.Date (legacy)
---

## 1. What it is

`java.util.Date` was Java's original class for representing a specific point in time, internally storing a single `long` value: milliseconds since the epoch (the same reference point `System.currentTimeMillis()` uses). Introduced in Java 1.0, it's now considered legacy — largely superseded by the much better-designed `java.time` package (introduced in Java 8) — but it remains common in older codebases and some APIs that predate the modern replacement.

```java
import java.util.Date;

public class DateDemo {
    public static void main(String[] args) {
        Date now = new Date(); // captures the CURRENT moment at construction time
        System.out.println("Now: " + now);

        Date specificTime = new Date(0); // epoch itself: midnight, January 1, 1970 UTC
        System.out.println("Epoch: " + specificTime);

        System.out.println("Now is after epoch: " + now.after(specificTime));
    }
}
```

`new Date()` captures the current instant at the moment of construction; `new Date(0)` constructs a `Date` representing exactly the epoch reference point; `.after(...)` and the equivalent `.before(...)` compare two `Date` instances chronologically — `Date`'s default `toString()` output includes a full date, time, and time zone, though its exact format is fixed and not easily customized without a separate formatting class.

## 2. Why & when

Understanding `Date` matters primarily for reading and maintaining older Java code, and for recognizing the specific design problems that motivated the modern `java.time` package's very different approach.

- **Historically the only option** — before Java 8, `Date` (often combined with `Calendar`, the next topic) was the standard way to represent and manipulate dates and times in Java, so any codebase predating 2014 likely uses it extensively.
- **Mutable, which is a significant design flaw** — a `Date` object's internal time value can be changed after construction via `setTime(long)`, meaning a `Date` passed to a method or stored in a shared field could be silently modified by any code holding a reference to it — this mutability is widely considered one of `java.util.Date`'s most serious design mistakes, since it makes `Date` instances unsafe to share without defensive copying.
- **Confusing, largely deprecated API surface** — many of `Date`'s original methods (like `getYear()`, `getMonth()`, `getDate()` for day-of-month) were deprecated as early as Java 1.1 in favor of `Calendar`, leaving `Date` itself with a genuinely awkward, partially-deprecated method set that's easy to misuse.

Recognize `Date` when reading legacy code or working with older libraries and APIs that still expose it, but for any new code, strongly prefer `java.time.Instant` (for a point in time), `java.time.LocalDate`/`LocalDateTime` (for calendar dates and date-times without time zone concerns), or `java.time.ZonedDateTime` (when time zones matter) — all part of the modern, immutable, far better-designed `java.time` package.

## 3. Core concept

```java
import java.util.Date;

public class DateCore {
    public static void main(String[] args) {
        Date event = new Date();
        long eventMillis = event.getTime(); // extract the raw millisecond value

        Date recreated = new Date(eventMillis); // reconstruct an equal Date from that raw value

        System.out.println(event.equals(recreated)); // true — same millisecond value
    }
}
```

`getTime()` extracts the raw `long` millisecond value a `Date` wraps internally, and passing that same value to `new Date(millis)` reconstructs an equal `Date` object — this demonstrates that a `Date`'s entire identity is really just this one `long` value, exactly parallel to what `System.currentTimeMillis()` returns directly, without any object wrapper at all.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Date object wraps a single mutable long millisecond value, its setTime method can change that value after construction, making Date instances unsafe to share without defensive copying">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="150" y="20" width="300" height="50" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="300" y="42" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Date object</text>
  <text x="300" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">wraps ONE mutable long (millis since epoch)</text>

  <line x1="300" y1="70" x2="300" y2="90" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="150" y="95" width="300" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="117" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">setTime(newMillis) — CAN change it after construction</text>

  <text x="300" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mutability is Date's most significant, widely-criticized design flaw.</text>
</svg>

`Date` wraps a single mutable `long` value, changeable after construction — a significant, well-documented design flaw.

## 5. Runnable example

Scenario: a small event-logging utility using `Date`, evolved from basic timestamping into demonstrating the mutability pitfall directly, then hardened with the defensive-copying workaround needed to use `Date` safely.

### Level 1 — Basic

```java
import java.util.Date;

public class DateBasic {
    public static void main(String[] args) {
        Date eventTime = new Date();
        System.out.println("Event logged at: " + eventTime);
        System.out.println("As raw millis: " + eventTime.getTime());
    }
}
```

**How to run:** `java DateBasic.java`

`new Date()` captures the current moment; printing it shows a full, fixed-format date-time string, and `getTime()` reveals the underlying raw millisecond value it actually wraps.

### Level 2 — Intermediate

Same idea, now demonstrating the mutability pitfall directly: a `Date` stored in one object is unexpectedly modified through a reference held elsewhere, corrupting data that should have been independent.

```java
import java.util.Date;

public class DateIntermediate {
    static class LogEntry {
        String message;
        Date timestamp;
        LogEntry(String message, Date timestamp) {
            this.message = message;
            this.timestamp = timestamp; // stores the SAME Date reference, not a copy!
        }
    }

    public static void main(String[] args) {
        Date sharedDate = new Date();
        LogEntry entry = new LogEntry("System started", sharedDate);

        System.out.println("Original entry timestamp: " + entry.timestamp);

        sharedDate.setTime(0); // mutating the SAME object entry.timestamp also references!

        System.out.println("Entry timestamp AFTER external mutation: " + entry.timestamp); // corrupted!
    }
}
```

**How to run:** `java DateIntermediate.java`

`entry.timestamp` and `sharedDate` are the *same* `Date` object (the constructor stored the reference directly, without copying), so calling `sharedDate.setTime(0)` — code entirely outside `LogEntry`'s control — silently corrupts `entry.timestamp` too, changing it to represent the epoch instead of the originally logged time; this is precisely the kind of bug `Date`'s mutability makes possible.

### Level 3 — Advanced

Same logging system, now fixed with defensive copying — storing and returning a fresh `Date` copy rather than the original reference — demonstrating the standard (if verbose) workaround required to use `Date` safely in shared or long-lived contexts.

```java
import java.util.Date;

public class DateAdvanced {
    static class SafeLogEntry {
        String message;
        private final Date timestamp;

        SafeLogEntry(String message, Date timestamp) {
            this.message = message;
            this.timestamp = new Date(timestamp.getTime()); // DEFENSIVE COPY on the way in
        }

        Date getTimestamp() {
            return new Date(timestamp.getTime()); // DEFENSIVE COPY on the way out too
        }
    }

    public static void main(String[] args) {
        Date sharedDate = new Date();
        SafeLogEntry entry = new SafeLogEntry("System started", sharedDate);

        System.out.println("Original entry timestamp: " + entry.getTimestamp());

        sharedDate.setTime(0); // mutating the ORIGINAL Date the caller still holds

        System.out.println("Entry timestamp AFTER external mutation: " + entry.getTimestamp()); // UNCHANGED, safe!

        // Even mutating the value returned by getTimestamp() cannot affect the entry's internal state:
        Date retrieved = entry.getTimestamp();
        retrieved.setTime(12345);
        System.out.println("Entry timestamp after mutating a RETRIEVED copy: " + entry.getTimestamp()); // still unchanged
    }
}
```

**How to run:** `java DateAdvanced.java`

`SafeLogEntry`'s constructor makes a defensive copy (`new Date(timestamp.getTime())`) instead of storing the caller's original `Date` reference directly, and `getTimestamp()` similarly returns a *fresh copy* rather than the internal field itself — both defensive copies ensure that neither mutating the original `sharedDate` externally, nor mutating a `Date` object retrieved via `getTimestamp()`, can ever affect `SafeLogEntry`'s own internal state.

## 6. Walkthrough

Trace `main` in `DateAdvanced` step by step.

**`Date sharedDate = new Date()`.** Captures the current time, say (hypothetically) representing millisecond value `M`.

**`new SafeLogEntry("System started", sharedDate)`.** Inside the constructor, `new Date(timestamp.getTime())` reads `sharedDate.getTime()` (which is `M`) and constructs a **brand-new** `Date` object with that same value, storing this new object (not `sharedDate` itself) in the `timestamp` field. From this point on, `entry.timestamp` and `sharedDate` are two entirely separate objects that merely happen to currently represent the same moment in time.

**`entry.getTimestamp()` (first call).** Returns yet another fresh `Date` copy, constructed from `entry.timestamp.getTime()` (still `M`). Printed: shows the time corresponding to `M`.

**`sharedDate.setTime(0)`.** Mutates `sharedDate` (the original object the caller still holds) to represent the epoch. This has **no effect whatsoever** on `entry.timestamp`, since that field was always a separate, independently-constructed `Date` object.

**`entry.getTimestamp()` (second call).** Still returns a fresh copy based on `entry.timestamp.getTime()`, which is still `M` (unaffected by the mutation to `sharedDate`). Printed: shows the same, correct original time — proving the defensive copy successfully protected the entry's internal state.

**`Date retrieved = entry.getTimestamp()`.** Another fresh copy, call it `R`, constructed from `entry.timestamp.getTime()` (`M`).

**`retrieved.setTime(12345)`.** Mutates `R` (the retrieved copy) to represent millisecond value `12345`. Since `R` is a separate object from `entry.timestamp`, this mutation affects only `R` itself.

**`entry.getTimestamp()` (third call).** Yet another fresh copy from `entry.timestamp.getTime()`, still `M` — completely unaffected by whatever happened to the previously retrieved (and now mutated) copy `R`.

```
sharedDate = new Date() -> represents millis M
SafeLogEntry constructor: timestamp = new Date(M) -- a SEPARATE object from sharedDate, same value

getTimestamp() #1 -> new Date(M) -- shows time for M

sharedDate.setTime(0) -- mutates ONLY sharedDate, entry.timestamp untouched (separate object)

getTimestamp() #2 -> new Date(M) -- STILL shows time for M, unaffected

retrieved = getTimestamp() -> new Date(M), call it R
retrieved.setTime(12345) -- mutates ONLY R, entry.timestamp untouched (separate object)

getTimestamp() #3 -> new Date(M) -- STILL shows time for M, unaffected
```

**Final output** (exact date/time text depends on when the program is actually run, but the key point is all three prints show the *same, original* time):
```
Original entry timestamp: <some date/time representing M>
Entry timestamp AFTER external mutation: <the SAME date/time representing M, unchanged>
Entry timestamp after mutating a RETRIEVED copy: <the SAME date/time representing M, unchanged>
```

## 7. Gotchas & takeaways

> **`java.util.Date` is mutable — its internal time value can be changed after construction via `setTime(long)` — making it unsafe to store or return a shared reference to a `Date` object without defensive copying, exactly as `DateIntermediate` demonstrated with a real, silent data-corruption bug.** Any class storing a `Date` (as a field, in a collection, or returned from a getter) should defensively copy it both on the way in and on the way out, unless it can absolutely guarantee no other code will ever mutate the shared instance.

> **For any new code, strongly prefer `java.time.Instant`, `LocalDate`, `LocalDateTime`, or `ZonedDateTime` over `java.util.Date`** — the entire `java.time` package (introduced in Java 8) was deliberately designed to be immutable, eliminating this whole category of mutability bugs entirely, along with providing a much richer, clearer API for date/time arithmetic, formatting, and time zone handling that `Date` never had.

- `java.util.Date` represents a point in time as a single, internally mutable `long` millisecond value (milliseconds since the epoch), the same reference point `System.currentTimeMillis()` uses.
- `Date` is mutable via `setTime(long)`, meaning shared or stored `Date` references can be silently modified by any code holding them — a well-documented, significant design flaw.
- Defensive copying (`new Date(original.getTime())`) both when storing a `Date` and when returning one is the standard, if verbose, workaround for using `Date` safely in shared contexts.
- Modern Java code should use the immutable `java.time` package (`Instant`, `LocalDate`, `LocalDateTime`, `ZonedDateTime`) instead of `Date` for any new development.
