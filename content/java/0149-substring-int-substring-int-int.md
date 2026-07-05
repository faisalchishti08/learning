---
card: java
gi: 149
slug: substring-int-substring-int-int
title: substring(int) / substring(int,int)
---

## 1. What it is

`substring(int beginIndex)` returns a new string containing everything from `beginIndex` (inclusive) to the end of the original string. `substring(int beginIndex, int endIndex)` returns a new string from `beginIndex` (inclusive) to `endIndex` (**exclusive**) — the character at `endIndex` itself is *not* included. Both throw `StringIndexOutOfBoundsException` if the indices are out of the valid range.

```java
String word = "hello world";
System.out.println(word.substring(6));     // "world" — index 6 to the end
System.out.println(word.substring(0, 5));  // "hello" — index 0 up to (not including) index 5
System.out.println(word.substring(6, 11)); // "world" — same result, explicit end
```

The length of the result from `substring(begin, end)` is always exactly `end - begin` — a useful sanity check when reasoning about substring boundaries, since the "exclusive end" rule is the single most common source of off-by-one mistakes with this method.

## 2. Why & when

`substring` is the standard tool for **extracting a known portion** of a string:

- **Fixed-position parsing** — pulling a specific field out of a fixed-width record (e.g., characters 10-15 are always the zip code).
- **Trimming a known prefix or suffix** — removing a fixed-length header, tag, or extension once its length is known.
- **Splitting around a delimiter's position** — often combined with `indexOf` (covered next) to find *where* to cut, then `substring` to actually extract the piece before or after that position.

For splitting a string into many pieces around a repeated delimiter, `split(String regex)` (covered later in this section) is usually more convenient than chaining several manual `substring`/`indexOf` calls yourself.

## 3. Core concept

```java
public class SubstringDemo {
    public static void main(String[] args) {
        String filename = "report_2024.pdf";

        int dotIndex = filename.lastIndexOf('.');
        String name = filename.substring(0, dotIndex);       // "report_2024"
        String extension = filename.substring(dotIndex + 1);  // "pdf" — start AFTER the dot

        System.out.println("Name: " + name);
        System.out.println("Extension: " + extension);
    }
}
```

`substring(0, dotIndex)` extracts everything before the dot (the dot's own index is the exclusive end, so it's not included in `name`). `substring(dotIndex + 1)` starts one position *after* the dot, deliberately skipping the dot character itself, and runs to the end of the string.

## 4. Diagram

<svg viewBox="0 0 700 155" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Substring diagram: the string report underscore 2024 dot pdf, showing substring(0, dotIndex) extracting everything before the dot, and substring(dotIndex+1) extracting everything after it, with the dot character itself excluded from both pieces.">
  <rect x="8" y="8" width="684" height="139" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"report_2024.pdf" — dotIndex = 12</text>

  <rect x="60" y="40" width="330" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="225" y="59" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">report_2024</text>
  <text x="225" y="82" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">substring(0, 12)</text>

  <rect x="390" y="40" width="30" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="405" y="59" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">.</text>
  <text x="405" y="82" fill="#f85149" font-size="7.5" text-anchor="middle" font-family="sans-serif">index 12 (excluded, skipped)</text>

  <rect x="420" y="40" width="90" height="28" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="465" y="59" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">pdf</text>
  <text x="465" y="82" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">substring(13)</text>

  <text x="350" y="115" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">The end index in substring(begin, end) is EXCLUSIVE — index 12 (the dot) belongs to neither piece.</text>
  <text x="350" y="130" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">substring(13) starts right after it, correctly skipping the dot itself.</text>
</svg>

The dot at index 12 is deliberately excluded from both extracted pieces — `end` is exclusive, and the second call starts at `dotIndex + 1`.

## 5. Runnable example

Scenario: parsing a simple `"key=value"` configuration line — starting with a basic split around the `=` sign, then adding trimming of surrounding whitespace, then hardening it to handle lines with no `=` sign or multiple `=` signs correctly.

### Level 1 — Basic

```java
public class ConfigLineBasic {
    public static void main(String[] args) {
        String line = "username=alice";

        int equalsIndex = line.indexOf('=');
        String key = line.substring(0, equalsIndex);
        String value = line.substring(equalsIndex + 1);

        System.out.println("Key: [" + key + "], Value: [" + value + "]");
    }
}
```

**How to run:** `java ConfigLineBasic.java`

`equalsIndex` locates the `=` at index 8. `substring(0, 8)` extracts `"username"` (indices 0-7, the `=` at index 8 excluded). `substring(9)` starts right after the `=` and extracts `"alice"` to the end.

### Level 2 — Intermediate

Same config parsing, now handling lines with **surrounding whitespace** around the key and value, trimming each piece after extraction.

```java
public class ConfigLineIntermediate {
    public static void main(String[] args) {
        String[] lines = { "username=alice", "  port  =  8080  ", "debug = true" };

        for (String line : lines) {
            int equalsIndex = line.indexOf('=');
            String key = line.substring(0, equalsIndex).trim();
            String value = line.substring(equalsIndex + 1).trim();
            System.out.println("Key: [" + key + "], Value: [" + value + "]");
        }
    }
}
```

**How to run:** `java ConfigLineIntermediate.java`

`substring` extracts the raw pieces first (which may still contain leading/trailing spaces), and `.trim()` is chained onto each result to clean it up afterward — `substring` itself has no concept of whitespace; it operates purely on index positions, so trimming is a deliberate, separate step applied to its output.

### Level 3 — Advanced

Same config parser, now defensively handling a line with **no `=` sign at all** (where `indexOf` returns `-1`, and calling `substring` with a negative index would throw) and a line with **multiple `=` signs** (splitting only on the first one, so the value itself may legitimately contain `=`).

```java
public class ConfigLineAdvanced {

    record ConfigEntry(String key, String value) {}

    static ConfigEntry parseLine(String line) {
        int equalsIndex = line.indexOf('=');
        if (equalsIndex < 0) {
            throw new IllegalArgumentException("Malformed config line (no '='): " + line);
        }
        String key = line.substring(0, equalsIndex).trim();
        String value = line.substring(equalsIndex + 1).trim(); // everything after the FIRST '=', including any later ones
        return new ConfigEntry(key, value);
    }

    public static void main(String[] args) {
        String[] lines = { "username=alice", "url=http://example.com?a=1&b=2", "not_valid_line" };

        for (String line : lines) {
            try {
                ConfigEntry entry = parseLine(line);
                System.out.println("Key: [" + entry.key() + "], Value: [" + entry.value() + "]");
            } catch (IllegalArgumentException e) {
                System.out.println("Skipping: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java ConfigLineAdvanced.java`

The guard clause `if (equalsIndex < 0)` catches the "no `=` found" case *before* attempting `substring(0, -1)`, which would otherwise throw a confusing `StringIndexOutOfBoundsException` rather than a clear, deliberate error message. Because `indexOf('=')` finds only the **first** occurrence, `line.substring(equalsIndex + 1)` for the URL example correctly keeps every character after that first `=`, including the later `=` signs inside the query string — `value` becomes `"http://example.com?a=1&b=2"` intact.

## 6. Walkthrough

Trace `parseLine("url=http://example.com?a=1&b=2")`:

**Finding the split point.** `line.indexOf('=')` scans left to right and returns `3` — the position of the *first* `=`, right after `"url"`. It does not know or care that there are more `=` characters later in the string.

**Extracting the key.** `line.substring(0, 3)` returns `"url"` (indices 0, 1, 2 — index 3 itself, the `=`, is excluded because the end index is exclusive). `.trim()` has no effect here since there's no surrounding whitespace.

**Extracting the value.** `line.substring(4)` starts at index 4 (one past the first `=`) and runs to the very end of the string, producing `"http://example.com?a=1&b=2"` — including both later `=` signs, since `substring` from index 4 onward has no idea those characters are also `=` signs; it just copies everything from that position forward.

```
line = "url=http://example.com?a=1&b=2"
indexOf('=') -> 3 (first '=' only)
substring(0,3) -> "url"                                (key)
substring(4)   -> "http://example.com?a=1&b=2"          (value, includes later '=' signs)
```

**Final output.** The three lines produce: `Key: [username], Value: [alice]`; `Key: [url], Value: [http://example.com?a=1&b=2]`; and for `"not_valid_line"`, `indexOf('=')` returns `-1`, the guard clause throws, and the `catch` block prints `Skipping: Malformed config line (no '='): not_valid_line`.

## 7. Gotchas & takeaways

> **`substring(begin, end)`'s `end` index is exclusive — the character at `end` is never included in the result.** The length of the extracted piece is always exactly `end - begin`; if your extracted substring is one character short (or long), this is almost always the cause.

> **Calling `substring` with a negative index (commonly from an unchecked `indexOf` result of `-1`) throws `StringIndexOutOfBoundsException`** — always check that `indexOf`'s result is `>= 0` before using it as a `substring` boundary, exactly as the guard clause in Level 3 does.

- `substring(begin)` extracts from `begin` to the end; `substring(begin, end)` extracts from `begin` up to (but not including) `end`.
- The extracted substring's length always equals `end - begin` for the two-argument form — a handy way to double-check your indices.
- `indexOf` combined with `substring` is the classic pattern for splitting a string into a "before" and "after" piece around a single delimiter occurrence.
- Always verify an index obtained from `indexOf` is non-negative before feeding it into `substring`, since `-1` (not found) produces an invalid index and throws.
