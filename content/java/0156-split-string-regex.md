---
card: java
gi: 156
slug: split-string-regex
title: split(String regex)
---

## 1. What it is

`String.split(String regex)` breaks a string into an array of substrings, using the given **regular expression** as the delimiter pattern — every place the pattern matches becomes a cut point, and the pieces between cuts become the array elements. Unlike `replace`, `split`'s argument genuinely is a regular expression, not literal text, so regex-special characters (`.`, `|`, `+`, and others) need escaping if you mean them literally.

```java
String csv = "apple,banana,cherry";
String[] parts = csv.split(",");
// parts = { "apple", "banana", "cherry" }

String messy = "one   two    three"; // multiple spaces between words
String[] words = messy.split("\\s+"); // "\\s+" means "one or more whitespace characters"
// words = { "one", "two", "three" }
```

`split(",")` works here because a comma has no special meaning in regex, so it's matched literally — but splitting on a genuinely special character (like `.`) requires escaping it (`split("\\.")`) or it will match every single character instead of just literal dots.

## 2. Why & when

`split` is the standard tool for breaking a string into multiple pieces around a repeated or variable delimiter:

- **Parsing delimited data** — CSV lines, path segments, key-value pairs separated by a known character.
- **Tokenizing on flexible whitespace** — `split("\\s+")` handles any amount of spacing (single space, multiple spaces, tabs) uniformly, which manual `indexOf`/`substring` logic would need much more code to replicate.
- **Splitting on any of several delimiters** — a regex like `split("[,;]")` splits on either a comma or a semicolon, something a single literal `replace`/`substring` approach can't express directly.

For a single, fixed, non-regex delimiter with simple, predictable structure, `substring`/`indexOf` (as used in earlier topics) can sometimes be clearer — but for anything involving repetition, alternation, or genuinely variable-width separators, `split` and its regex power are the right tool.

## 3. Core concept

```java
import java.util.Arrays;

public class SplitDemo {
    public static void main(String[] args) {
        String line = "Alice,30,Engineer";
        String[] fields = line.split(",");

        System.out.println("Fields: " + Arrays.toString(fields));
        System.out.println("Name: " + fields[0]);
        System.out.println("Age: " + fields[1]);
        System.out.println("Job: " + fields[2]);
    }
}
```

`line.split(",")` breaks the string at every comma, producing an array of exactly the pieces between the commas — `fields[0]` is everything before the first comma, `fields[1]` is between the two commas, and `fields[2]` is everything after the second comma, matching the three CSV columns exactly.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Split diagram: the string Alice comma 30 comma Engineer is split at each comma into a three-element array containing Alice, 30, and Engineer, with the commas themselves consumed and not present in any array element.">
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Alice,30,Engineer".split(",") -&gt; ["Alice", "30", "Engineer"]</text>

  <rect x="60" y="45" width="100" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Alice"</text>
  <rect x="165" y="45" width="20" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="175" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">,</text>
  <rect x="190" y="45" width="60" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="220" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"30"</text>
  <rect x="255" y="45" width="20" height="28" rx="4" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="265" y="64" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">,</text>
  <rect x="280" y="45" width="130" height="28" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="64" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">"Engineer"</text>

  <text x="110" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fields[0]</text>
  <text x="175" y="88" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">consumed</text>
  <text x="220" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fields[1]</text>
  <text x="265" y="88" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">consumed</text>
  <text x="345" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">fields[2]</text>

  <text x="350" y="120" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">The delimiter itself never appears in any resulting array element — only the text between delimiters does.</text>
</svg>

Every comma acts as a cut point; the resulting array holds only the text between the cuts, with the delimiters themselves discarded.

## 5. Runnable example

Scenario: parsing a CSV line representing a person's record — starting with a basic comma split, then handling flexible whitespace around the delimiter, then hardening the parser against an unexpected number of fields and against `split`'s trailing-empty-string quirk.

### Level 1 — Basic

```java
import java.util.Arrays;

public class CsvParseBasic {
    public static void main(String[] args) {
        String line = "Alice,30,Engineer";
        String[] fields = line.split(",");

        System.out.println(Arrays.toString(fields));
    }
}
```

**How to run:** `java CsvParseBasic.java`

`split(",")` cuts the string at every comma, producing exactly `["Alice", "30", "Engineer"]` — a straightforward three-element array, since the input has exactly two commas separating three fields.

### Level 2 — Intermediate

Same CSV parsing, now handling lines with **inconsistent spacing** around the commas (`"Alice, 30 , Engineer"`), combining a split on a comma with optional surrounding whitespace directly in the regex, then trimming each resulting field to remove anything the regex didn't already consume.

```java
import java.util.Arrays;

public class CsvParseIntermediate {
    public static void main(String[] args) {
        String[] lines = { "Alice,30,Engineer", "Bob , 25,  Designer", "Carol,  40 ,Manager" };

        for (String line : lines) {
            String[] rawFields = line.split("\\s*,\\s*"); // comma with optional whitespace on either side
            for (int i = 0; i < rawFields.length; i++) {
                rawFields[i] = rawFields[i].trim(); // catches any whitespace the regex's boundaries didn't cover
            }
            System.out.println(Arrays.toString(rawFields));
        }
    }
}
```

**How to run:** `java CsvParseIntermediate.java`

The regex `"\\s*,\\s*"` matches a comma optionally surrounded by any amount of whitespace (`\s*` means "zero or more whitespace characters") on either side, so `" 30 , "` around a comma is consumed as part of the delimiter itself — an additional `.trim()` per field is still applied afterward as a defensive backstop, in case a field has leading/trailing whitespace not directly adjacent to a comma (such as at the very start or end of the whole line).

### Level 3 — Advanced

Same CSV parser, now validating the **expected field count** and defending against `split`'s well-known trailing-empty-string quirk: by default, `split` **removes trailing empty strings** from the result, which can silently shrink the array below the expected length if the line ends with the delimiter.

```java
import java.util.Arrays;

public class CsvParseAdvanced {

    record Person(String name, int age, String job) {}

    static Person parseLine(String line) {
        // split with a negative limit disables the "remove trailing empty strings" behavior
        String[] fields = line.split("\\s*,\\s*", -1);

        if (fields.length != 3) {
            throw new IllegalArgumentException("Expected 3 fields, got " + fields.length + " in: " + line);
        }

        String name = fields[0].trim();
        int age = Integer.parseInt(fields[1].trim());
        String job = fields[2].trim();
        return new Person(name, age, job);
    }

    public static void main(String[] args) {
        String[] lines = { "Alice,30,Engineer", "Bob,25,", "Carol,40" };

        for (String line : lines) {
            try {
                Person p = parseLine(line);
                System.out.println(p);
            } catch (Exception e) {
                System.out.println("Failed to parse [" + line + "]: " + e.getMessage());
            }
        }
    }
}
```

**How to run:** `java CsvParseAdvanced.java`

`line.split("\\s*,\\s*", -1)` uses the two-argument overload with a **negative limit**, which tells `split` to keep trailing empty strings in the result instead of silently discarding them — without this, `"Bob,25,"` (a genuinely blank third field, perhaps a missing job title) would split into only `["Bob", "25"]` (the trailing empty piece dropped), miscounting as 2 fields instead of the expected 3, and incorrectly triggering the "wrong field count" error for data that's actually valid, just incomplete in one column.

## 6. Walkthrough

Trace `parseLine("Bob,25,")` (note the trailing comma, meaning an intentionally blank job field):

**Splitting.** `"Bob,25,".split("\\s*,\\s*", -1)` finds two comma delimiters. With the negative limit, the result keeps every piece including any trailing empty one: `["Bob", "25", ""]` — three elements, the last being an empty string, correctly representing the blank job field.

**Field count check.** `fields.length` is `3`, matching the expected count, so no exception is thrown.

**Extracting fields.** `fields[0].trim()` gives `"Bob"`. `Integer.parseInt(fields[1].trim())` parses `"25"` to `25`. `fields[2].trim()` gives `""` (trimming an already-empty string just returns another empty string).

```
"Bob,25,".split("\\s*,\\s*", -1) -> ["Bob", "25", ""]   (trailing empty KEPT because of -1 limit)
fields.length == 3 -> OK, proceed
name = "Bob", age = 25, job = ""
-> Person[name=Bob, age=25, job=]
```

**Contrast without the limit.** If `split("\\s*,\\s*")` had been called with no second argument (the default behavior), the same input would produce only `["Bob", "25"]` — the trailing empty string silently removed — `fields.length` would be `2`, and the guard clause would incorrectly throw `"Expected 3 fields, got 2"` for what is actually valid (if incomplete) data.

**Final output.** For the three lines: `"Alice,30,Engineer"` parses cleanly to `Person[name=Alice, age=30, job=Engineer]`; `"Bob,25,"` parses to `Person[name=Bob, age=25, job=]` (as traced, thanks to the `-1` limit); and `"Carol,40"` has only one comma, producing a 2-element array regardless of the limit argument, correctly triggering `Failed to parse [Carol,40]: Expected 3 fields, got 2`.

## 7. Gotchas & takeaways

> **`split`'s argument is a genuine regular expression, not literal text** — splitting on a regex-special character (`.`, `|`, `+`, `*`, and others) without escaping it produces unexpected results, since the character is interpreted as a pattern instruction rather than matched literally. Use `Pattern.quote(...)` or an escaped literal (`"\\."`) when the delimiter itself is regex-special.

> **By default, `split` silently discards trailing empty strings from the result** — a line ending in the delimiter (like a CSV row with a blank final field) can produce an array shorter than expected. Use the two-argument overload with a **negative limit** (`split(regex, -1)`) to preserve trailing empty strings when that matters for correctly validating field counts.

- `split(regex)` breaks a string into an array around every match of the given regular expression; the delimiter matches themselves are consumed and don't appear in the result.
- A regex like `"\\s*,\\s*"` elegantly handles a delimiter with optional surrounding whitespace in one step, avoiding the need for a separate trim pass on every field (though trimming defensively afterward is still common practice).
- Always validate the resulting array's length before indexing into it, since malformed input can produce fewer (or more) fields than expected.
- Remember the trailing-empty-string quirk: pass a negative limit as the second argument to `split` whenever a blank trailing field is meaningful and must not be silently dropped.
