---
card: java
gi: 652
slug: compact-number-formatting-numberformat-getcompactnumberinsta
title: Compact Number Formatting (NumberFormat.getCompactNumberInstance)
---

## 1. What it is

**Compact number formatting**, added in **Java 12** via `NumberFormat.getCompactNumberInstance(Locale, NumberFormat.Style)`, formats large numbers into short, human-friendly forms like `1K`, `2.5M`, or `3B` instead of printing every digit. It takes a `Locale` (so `1000` becomes `1K` in English but a locale-appropriate equivalent elsewhere) and a `Style` — either `SHORT` (`1K`) or `LONG` (`1 thousand`). This is the same style of formatting you see throughout social media and analytics dashboards ("12.3K likes", "1.2M views"), now available as a standard JDK API instead of something every project reimplements by hand.

## 2. Why & when

Displaying raw numbers like `1500000` in a UI is hard to read at a glance; developers have long hand-rolled logic to divide by 1000/1000000/1000000000 and append `K`/`M`/`B` suffixes — logic that's easy to get subtly wrong (rounding, locale differences, pluralization in "long" form) and tedious to internationalize properly. `getCompactNumberInstance()` handles all of this correctly per-locale using CLDR (Unicode's locale data), the same source Java already uses for currency and date formatting. Reach for it whenever you're displaying counts, views, followers, or any large number in a dashboard, notification badge, or summary UI where full precision doesn't matter and shortness helps readability — and use full `NumberFormat` when exact values matter, like financial totals.

## 3. Core concept

```java
NumberFormat shortFmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.SHORT);
System.out.println(shortFmt.format(1000));       // "1K"
System.out.println(shortFmt.format(1_500_000));  // "2M"  (rounds by default)

NumberFormat longFmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.LONG);
System.out.println(longFmt.format(1000));        // "1 thousand"

shortFmt.setMaximumFractionDigits(1);
System.out.println(shortFmt.format(1_500_000));  // "1.5M" (with a fraction digit allowed)
```

By default, compact formatters round to the nearest whole compact unit (no decimal places); call `setMaximumFractionDigits(n)` if you want fractional precision like `1.5M`.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Raw numbers formatted into compact SHORT and LONG forms">
  <text x="20" y="30" fill="#8b949e" font-size="11" font-family="monospace">raw value</text>
  <text x="220" y="30" fill="#79c0ff" font-size="11" font-family="monospace">SHORT style</text>
  <text x="400" y="30" fill="#6db33f" font-size="11" font-family="monospace">LONG style</text>

  <line x1="10" y1="40" x2="590" y2="40" stroke="#8b949e" stroke-width="1"/>

  <text x="20" y="65" fill="#e6edf3" font-size="11" font-family="monospace">1,000</text>
  <text x="220" y="65" fill="#e6edf3" font-size="11" font-family="monospace">1K</text>
  <text x="400" y="65" fill="#e6edf3" font-size="11" font-family="monospace">1 thousand</text>

  <text x="20" y="90" fill="#e6edf3" font-size="11" font-family="monospace">1,500,000</text>
  <text x="220" y="90" fill="#e6edf3" font-size="11" font-family="monospace">2M (rounded)</text>
  <text x="400" y="90" fill="#e6edf3" font-size="11" font-family="monospace">2 million</text>

  <text x="20" y="115" fill="#e6edf3" font-size="11" font-family="monospace">3,200,000,000</text>
  <text x="220" y="115" fill="#e6edf3" font-size="11" font-family="monospace">3B</text>
  <text x="400" y="115" fill="#e6edf3" font-size="11" font-family="monospace">3 billion</text>

  <text x="20" y="145" fill="#8b949e" font-size="9" font-family="sans-serif">Locale-aware: uses CLDR data, so suffixes/wording vary by Locale.</text>
</svg>

`SHORT` favors compactness (`1K`, `2M`), `LONG` favors readability (`1 thousand`, `2 million`) — both driven by locale-specific CLDR patterns.

## 5. Runnable example

Scenario: formatting a social-media-style "view count" display — first a basic short-form formatter, then adding fractional precision and long form, then a full locale-aware badge renderer that adapts to different locales and handles edge cases like negative and zero values.

### Level 1 — Basic

```java
// File: CompactBasic.java
import java.text.NumberFormat;
import java.util.Locale;

public class CompactBasic {
    public static void main(String[] args) {
        NumberFormat fmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.SHORT);

        System.out.println(fmt.format(950));
        System.out.println(fmt.format(1000));
        System.out.println(fmt.format(12300));
        System.out.println(fmt.format(1500000));
    }
}
```

**How to run:** `java CompactBasic.java`

Expected output:
```
950
1K
12K
2M
```

Numbers below 1000 print as-is (there's no compact unit smaller than "thousand"); `1500000` rounds to `2M` because the default formatter allows zero fraction digits.

### Level 2 — Intermediate

```java
// File: CompactPrecise.java
import java.text.NumberFormat;
import java.util.Locale;

public class CompactPrecise {
    public static void main(String[] args) {
        NumberFormat shortFmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.SHORT);
        shortFmt.setMaximumFractionDigits(1);

        NumberFormat longFmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.LONG);
        longFmt.setMaximumFractionDigits(1);

        long[] values = {1500, 1_500_000, 3_200_000_000L};
        for (long v : values) {
            System.out.println(v + " -> short: " + shortFmt.format(v) + ", long: " + longFmt.format(v));
        }
    }
}
```

**How to run:** `java CompactPrecise.java`

Expected output:
```
1500 -> short: 1.5K, long: 1.5 thousand
1500000 -> short: 1.5M, long: 1.5 million
3200000000 -> short: 3.2B, long: 3.2 billion
```

Allowing one fraction digit turns lossy rounding (`2M`) into more informative output (`1.5M`) while keeping the number short — a common tradeoff for dashboards.

### Level 3 — Advanced

```java
// File: CompactBadge.java
import java.text.NumberFormat;
import java.util.Locale;

public class CompactBadge {
    static String viewBadge(long views) {
        if (views < 0) {
            throw new IllegalArgumentException("view count cannot be negative: " + views);
        }
        if (views == 0) {
            return "No views yet";
        }
        NumberFormat fmt = NumberFormat.getCompactNumberInstance(Locale.US, NumberFormat.Style.SHORT);
        fmt.setMaximumFractionDigits(1);
        return fmt.format(views) + (views == 1 ? " view" : " views");
    }

    public static void main(String[] args) {
        long[] counts = {0, 1, 42, 999, 1000, 1_234_567, 999_999_999};
        for (long c : counts) {
            System.out.println(c + " -> " + viewBadge(c));
        }

        NumberFormat german = NumberFormat.getCompactNumberInstance(Locale.GERMANY, NumberFormat.Style.SHORT);
        german.setMaximumFractionDigits(1);
        System.out.println("1.5M in de_DE -> " + german.format(1_500_000));

        try {
            viewBadge(-5);
        } catch (IllegalArgumentException e) {
            System.out.println("Rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java CompactBadge.java`

Expected output (German locale output may render with a comma decimal separator depending on JDK data version):
```
0 -> No views yet
1 -> 1 view
42 -> 42 views
999 -> 999 views
1000 -> 1K views
1234567 -> 1.2M views
999999999 -> 1B views
1.5M in de_DE -> 1,5 Mio.
Rejected: view count cannot be negative: -5
```

Level 3 wraps compact formatting in a small `viewBadge` helper handling edge cases (zero, singular "1 view", negative rejection) that a raw formatter call doesn't handle, and shows the same `1_500_000` value rendering differently under `Locale.GERMANY` — proving the formatting is genuinely locale-driven, not just English suffixes bolted on.

## 6. Walkthrough

1. `main` calls `viewBadge(1_234_567)` (partway through the loop). Inside, `views < 0` is `false` and `views == 0` is `false`, so execution falls through to build a `NumberFormat` via `getCompactNumberInstance(Locale.US, Style.SHORT)`.
2. `fmt.setMaximumFractionDigits(1)` configures the formatter to allow **one** digit after the decimal point in the compact form, instead of the default zero.
3. `fmt.format(1_234_567)` runs: internally the formatter picks the largest compact unit at or below the value's magnitude — here "million" (`10^6`) — divides `1,234,567` by `1,000,000` to get `1.234567`, then rounds to the configured 1 fraction digit, producing `1.2`, and appends the locale's short suffix for millions, `"M"`, yielding the string `"1.2M"`.
4. Back in `viewBadge`, `views == 1` is `false` (it's `1234567`), so the ternary appends `" views"` (plural), producing the final string `"1.2M views"`.
5. `System.out.println` prints `"1234567 -> 1.2M views"`.
6. Later, `main` builds a **separate** formatter for `Locale.GERMANY` and formats the same raw value `1_500_000`. The formatter again picks the "million" compact unit, computes `1.5`, but this time uses **German locale rules**: the decimal separator is a comma (not a period) and the suffix pattern for millions in German CLDR data is `"Mio."` rather than `"M"` — so the same numeric magnitude renders as `"1,5 Mio."`, demonstrating that the suffix, decimal separator, and unit wording are all pulled from locale data, not hardcoded English abbreviations.
7. Finally, `viewBadge(-5)` is called inside a `try` block: the very first check, `views < 0`, is `true`, so it immediately `throw`s `IllegalArgumentException` with a descriptive message — no formatter is ever constructed for invalid input — and the `catch` in `main` prints the rejection.

```
1234567 ──► getCompactNumberInstance(US, SHORT) ──► divide by 10^6 ──► 1.234567
       ──► round to 1 fraction digit ──► 1.2 ──► append suffix "M" ──► "1.2M"
       ──► viewBadge appends " views" ──► "1.2M views"
```

## 7. Gotchas & takeaways

> The **default** compact formatter (before calling `setMaximumFractionDigits`) rounds to **zero** fraction digits, so `1,500,000` becomes `"2M"`, not `"1.5M"` — a common surprise. If your UI needs one decimal of precision (the norm for view/follower counts), always call `setMaximumFractionDigits(1)` explicitly.

- `Style.SHORT` gives compact suffixes (`1K`, `1M`, `1B`); `Style.LONG` gives full words (`1 thousand`, `1 million`, `1 billion`).
- Formatting is locale-aware via CLDR — don't assume `"K"`/`"M"`/`"B"` suffixes apply to every locale.
- Numbers below the smallest compact unit (below 1000 in most locales) print unchanged, with no suffix.
- Always set `setMaximumFractionDigits` explicitly if you need fractional precision like `1.5M` rather than the default rounded `2M`.
- Use plain `NumberFormat.getNumberInstance()` (not compact) when exact values matter, such as financial amounts — compact formatting is lossy by design.
