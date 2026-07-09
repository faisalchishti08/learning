---
card: java
gi: 549
slug: parsing-formatting
title: Parsing & formatting
---

## 1. What it is

Parsing and formatting are the two directions of converting between `java.time` values and text, and this topic covers the practical details beyond basic `DateTimeFormatter` usage (see [[datetimeformatter]]): handling parse failures gracefully, working with locale-sensitive formats (month names, date orderings that vary by region), and building formatters robust enough for real-world, occasionally-malformed input — a common need whenever dates arrive from user input, external files, or third-party APIs rather than from your own well-behaved code.

## 2. Why & when

Real-world date/time text is messy: users type dates in whatever format is habitual to them, files are exported in inconsistent formats, and different locales format the same date completely differently (`"July 9, 2026"` in English versus `"9 juillet 2026"` in French). Parsing this reliably means handling malformed input without crashing the whole program, and formatting output correctly for the audience reading it. `DateTimeParseException` is the specific exception thrown by failed parsing, and catching it deliberately — rather than letting it propagate as an unhandled crash — is essential for any code processing external date input.

## 3. Core concept

```java
import java.time.*;
import java.time.format.*;
import java.util.*;

DateTimeFormatter usFormat = DateTimeFormatter.ofPattern("MM/dd/yyyy");

try {
    LocalDate date = LocalDate.parse("13/45/2026", usFormat); // invalid month AND day
} catch (DateTimeParseException e) {
    System.out.println("Parse failed: " + e.getMessage());
}

// Locale-aware formatting -- the same date, in different languages/conventions
LocalDate date = LocalDate.of(2026, 7, 9);
DateTimeFormatter frenchFormat = DateTimeFormatter.ofPattern("d MMMM yyyy", Locale.FRENCH);
System.out.println(date.format(frenchFormat)); // "9 juillet 2026"
```

`DateTimeParseException` signals malformed input at the moment of parsing; `DateTimeFormatter.ofPattern(pattern, locale)` produces locale-appropriate month/day names and formatting conventions.

## 4. Diagram

<svg viewBox="0 0 640 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="parsing malformed text throws DateTimeParseException; different locales format the same date differently">
  <rect x="8" y="8" width="624" height="114" rx="8" fill="#0d1117"/>
  <rect x="20" y="20" width="180" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="110" y="40" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">"13/45/2026" -&gt; parse</text>
  <text x="230" y="40" fill="#f85149" font-size="10" font-family="sans-serif">throws DateTimeParseException</text>

  <rect x="20" y="70" width="180" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="110" y="90" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">2026-07-09 + Locale.US</text>
  <text x="290" y="90" fill="#6db33f" font-size="10" font-family="sans-serif">"July 9, 2026"</text>
  <rect x="380" y="70" width="230" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="495" y="90" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">2026-07-09 + Locale.FRENCH -&gt; "9 juillet 2026"</text>
</svg>

Malformed input throws a specific, catchable exception; the same underlying date formats differently depending on the target locale.

## 5. Runnable example

Scenario: importing dates from a user-submitted CSV file with inconsistent, occasionally malformed formatting — evolved from basic parse-failure handling, through locale-aware formatting for an international audience, to a version that tries multiple known formats before giving up on a genuinely malformed entry.

### Level 1 — Basic

```java
import java.time.*;
import java.time.format.*;

public class ParseFailureBasic {
    public static void main(String[] args) {
        DateTimeFormatter format = DateTimeFormatter.ofPattern("MM/dd/yyyy");
        String[] inputs = {"07/09/2026", "13/45/2026", "not-a-date"};

        for (String input : inputs) {
            try {
                LocalDate date = LocalDate.parse(input, format);
                System.out.println(input + " -> " + date);
            } catch (DateTimeParseException e) {
                System.out.println(input + " -> FAILED: invalid date format");
            }
        }
    }
}
```

**How to run:** `java ParseFailureBasic.java`

Expected output:
```
07/09/2026 -> 2026-07-09
13/45/2026 -> FAILED: invalid date format
not-a-date -> FAILED: invalid date format
```

`"07/09/2026"` parses successfully, since it's a well-formed date matching the `"MM/dd/yyyy"` pattern. `"13/45/2026"` structurally matches the pattern's shape (three numbers separated by slashes) but has an invalid month (`13`) and day (`45`) — `DateTimeParseException` is thrown and caught. `"not-a-date"` doesn't match the pattern's shape at all, throwing the same exception type for a different underlying reason — both are handled identically by the `catch` block.

### Level 2 — Intermediate

```java
import java.time.*;
import java.time.format.*;
import java.util.*;

public class LocaleFormatting {
    public static void main(String[] args) {
        LocalDate date = LocalDate.of(2026, 7, 9);

        DateTimeFormatter usFormat = DateTimeFormatter.ofPattern("MMMM d, yyyy", Locale.US);
        DateTimeFormatter frenchFormat = DateTimeFormatter.ofPattern("d MMMM yyyy", Locale.FRENCH);
        DateTimeFormatter germanFormat = DateTimeFormatter.ofPattern("d. MMMM yyyy", Locale.GERMAN);

        System.out.println("US: " + date.format(usFormat));
        System.out.println("French: " + date.format(frenchFormat));
        System.out.println("German: " + date.format(germanFormat));
    }
}
```

**How to run:** `java LocaleFormatting.java`

Expected output:
```
US: July 9, 2026
French: 9 juillet 2026
German: 9. Juli 2026
```

The real-world concern this adds: the *same* `LocalDate` formatted for three different audiences. `Locale.US`, `Locale.FRENCH`, and `Locale.GERMAN` each supply their own month-name translations (`July`/`juillet`/`Juli`) to the formatter, which the pattern's `MMMM` token consumes automatically — the pattern structure stays the same, but the actual rendered text adapts entirely to the specified locale.

### Level 3 — Advanced

```java
import java.time.*;
import java.time.format.*;
import java.util.*;

public class MultiFormatParsing {
    // Try several known input formats, in order, before giving up.
    static final List<DateTimeFormatter> KNOWN_FORMATS = List.of(
            DateTimeFormatter.ofPattern("yyyy-MM-dd"),
            DateTimeFormatter.ofPattern("MM/dd/yyyy"),
            DateTimeFormatter.ofPattern("dd-MMM-yyyy", Locale.US)
    );

    static Optional<LocalDate> tryParse(String input) {
        for (DateTimeFormatter formatter : KNOWN_FORMATS) {
            try {
                return Optional.of(LocalDate.parse(input, formatter));
            } catch (DateTimeParseException e) {
                // this format didn't match -- try the next one
            }
        }
        return Optional.empty(); // none of the known formats matched
    }

    public static void main(String[] args) {
        String[] inputs = {"2026-07-09", "07/09/2026", "09-Jul-2026", "totally-invalid"};

        for (String input : inputs) {
            Optional<LocalDate> result = tryParse(input);
            System.out.println(input + " -> " + result.map(LocalDate::toString).orElse("UNPARSEABLE"));
        }
    }
}
```

**How to run:** `java MultiFormatParsing.java`

Expected output:
```
2026-07-09 -> 2026-07-09
07/09/2026 -> 2026-07-09
09-Jul-2026 -> 2026-07-09
totally-invalid -> UNPARSEABLE
```

This handles realistic, inconsistently-formatted input by trying **multiple known formats** in sequence: `tryParse(...)` attempts each formatter in `KNOWN_FORMATS` in order, catching and swallowing `DateTimeParseException` between attempts, only truly giving up (returning `Optional.empty()`) once every known format has failed. All three valid, differently-formatted date strings successfully parse to the same underlying `LocalDate` (`2026-07-09`), while `"totally-invalid"` exhausts every format attempt and correctly resolves to `Optional.empty()`, reported as `"UNPARSEABLE"`.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `inputs` holds four strings, three valid (in different formats) and one genuinely unparseable.

For `input = "2026-07-09"`, `tryParse(...)` is called. Inside, the `for` loop tries the first formatter, `"yyyy-MM-dd"`: `LocalDate.parse("2026-07-09", formatter)` succeeds immediately, since the input exactly matches this pattern. `tryParse` returns `Optional.of(LocalDate.of(2026, 7, 9))` right away, without even attempting the remaining two formatters.

For `input = "07/09/2026"`, `tryParse(...)` tries the first formatter, `"yyyy-MM-dd"`: parsing `"07/09/2026"` against this pattern fails (the slashes and field order don't match `yyyy-MM-dd`'s expected shape), throwing `DateTimeParseException`, caught and silently ignored by the loop. The loop then tries the second formatter, `"MM/dd/yyyy"`: this matches the input's shape exactly, `LocalDate.parse("07/09/2026", formatter)` succeeds, returning `Optional.of(LocalDate.of(2026, 7, 9))` — the same underlying date as the first input, just expressed in a different textual format.

For `input = "09-Jul-2026"`, the first two formatters both fail to match (different separators and field orders), each throwing and having their exception caught. The third formatter, `"dd-MMM-yyyy"` with `Locale.US` (needed so `"Jul"` is recognized as an English month abbreviation), successfully matches, returning `Optional.of(LocalDate.of(2026, 7, 9))`.

```
"2026-07-09"  -> try "yyyy-MM-dd": MATCHES -> return LocalDate(2026,7,9)

"07/09/2026"  -> try "yyyy-MM-dd": FAILS (caught)
              -> try "MM/dd/yyyy": MATCHES -> return LocalDate(2026,7,9)

"09-Jul-2026" -> try "yyyy-MM-dd": FAILS (caught)
              -> try "MM/dd/yyyy": FAILS (caught)
              -> try "dd-MMM-yyyy": MATCHES -> return LocalDate(2026,7,9)

"totally-invalid" -> try all THREE formatters: ALL FAIL (each caught)
                   -> loop exhausted -> return Optional.empty()
```

For `input = "totally-invalid"`, all three formatters in `KNOWN_FORMATS` are attempted in sequence, and every single one throws `DateTimeParseException` (the input doesn't structurally resemble any of the three expected date shapes at all) — each exception is caught and the loop moves on, until the `for` loop exhausts every formatter with no success. `tryParse` falls through to `return Optional.empty()`.

Back in `main`, `result.map(LocalDate::toString).orElse("UNPARSEABLE")` is evaluated for each input: for the three successful parses, `.map(LocalDate::toString)` converts the present `LocalDate` to its ISO string form, and `.orElse(...)` is never reached. For the failed parse, `result` is `Optional.empty()`, so `.map(...)` has nothing to transform and stays empty, and `.orElse("UNPARSEABLE")` supplies the fallback string, printed as `"totally-invalid -> UNPARSEABLE"`.

## 7. Gotchas & takeaways

> Catching and silently ignoring `DateTimeParseException` inside a loop (as `tryParse` does between format attempts) is appropriate specifically because *failure to match one format* isn't itself an error — it's expected, normal control flow when trying several possible formats. But make sure the final `catch`-and-give-up point (returning `Optional.empty()` here) still surfaces the ultimate failure clearly to the caller — silently swallowing *every* parse failure with no signal at all would hide genuinely malformed data from view.

- `DateTimeParseException` is thrown when text doesn't match the expected format during parsing — always catch it explicitly when processing external, potentially-malformed date input.
- `DateTimeFormatter.ofPattern(pattern, locale)` produces locale-appropriate month names and formatting conventions, while the pattern structure itself stays consistent.
- Trying multiple known formats in sequence (catching and moving past each failed attempt) is a practical, defensive pattern for parsing dates from inconsistently-formatted real-world sources.
- Wrapping the final result in `Optional<LocalDate>` (rather than throwing all the way up, or returning `null`) gives callers a clean, safe way to handle "none of the known formats matched" without an unguarded exception or a `null`-check.
- Always test date parsing against genuinely malformed input (not just correctly-formatted examples) before deploying code that processes external date data — the failure mode matters as much as the success path.
