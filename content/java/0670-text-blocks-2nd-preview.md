---
card: java
gi: 670
slug: text-blocks-2nd-preview
title: Text blocks (2nd preview)
---

## 1. What it is

Java 14's **second preview** of text blocks (JEP 368) refined the feature first previewed in Java 13 (see [Text blocks (preview)](0658-text-blocks-preview.md)) by adding **two new escape sequences** specifically useful inside `"""`-delimited blocks: `\<line-break>` (a backslash immediately followed by a newline) suppresses that line break entirely, letting you wrap a long line in your source code without inserting an actual newline into the resulting string value; and `\s` inserts a single literal space character that the compiler's automatic trailing-whitespace stripping will **not** remove. Both escapes solve real friction points reported during the Java 13 preview: without `\`, there was no way to break a text block's *source* line across multiple lines without also breaking the *string value*; without `\s`, intentional trailing spaces (meaningful in some formats) were silently stripped by the block's automatic indentation/whitespace handling.

## 2. Why & when

Text blocks automatically strip trailing whitespace from each line (to avoid invisible, hard-to-spot trailing spaces sneaking into source-controlled code) — but this is a problem if you actually *need* trailing spaces to be part of the string value, such as fixed-width text formats or certain markup/protocol payloads. `\s` gives you an explicit, visible way to say "this space is intentional, keep it" right at the point it matters, rather than working around the stripping with `+"  "` concatenation after the block. Separately, `\<line-break>` addresses pure source-formatting: sometimes you want to keep a single logical line of text under some column-width limit in your source file without actually splitting that line's *content* — the line-continuation escape lets the source wrap while the resulting string stays single-line. Reach for `\s` whenever a text block's content genuinely needs trailing spaces preserved, and reach for `\<line-break>` when you want to keep a text block's source readable within your file's line-length conventions without changing what string it produces.

## 3. Core concept

```java
// \s preserves an intentional trailing space that would otherwise be stripped
String padded = """
    Name:  Ada\s
    Role:  Engineer\s
    """;
// Each line keeps its trailing space, thanks to \s — without it,
// the text block's automatic trailing-whitespace stripping would remove it.

// \<line-break> suppresses a newline in the SOURCE without adding one to the VALUE
String longLine = """
    This is one long logical line of text that we want to \
    keep readable in the source file without actually \
    inserting newlines into the resulting string value.""";
// The resulting string has NO line breaks at all — just one continuous line.
```

`\s` is specifically an *escape for a single space character* (equivalent to ` `), distinct from the general-purpose trailing-whitespace-stripping rule; `\<line-break>` is specifically about *suppressing* a line break that would otherwise appear in the string, purely a source-formatting convenience.

## 4. Diagram

<svg viewBox="0 0 620 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two new escapes in the second text block preview: backslash-newline suppresses a line break in the value, and backslash-s preserves a trailing space that would otherwise be stripped">
  <rect x="10" y="15" width="290" height="150" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="155" y="37" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">\ (line continuation)</text>
  <text x="25" y="65" fill="#e6edf3" font-size="9" font-family="monospace">"""</text>
  <text x="25" y="80" fill="#e6edf3" font-size="9" font-family="monospace">Line one continues \</text>
  <text x="25" y="95" fill="#e6edf3" font-size="9" font-family="monospace">right here on line two.</text>
  <text x="25" y="110" fill="#e6edf3" font-size="9" font-family="monospace">"""</text>
  <text x="25" y="135" fill="#79c0ff" font-size="9" font-family="sans-serif">Value: "Line one continues</text>
  <text x="25" y="150" fill="#79c0ff" font-size="9" font-family="sans-serif">right here on line two."</text>
  <text x="25" y="165" fill="#8b949e" font-size="8" font-family="sans-serif">(no newline in the actual string)</text>

  <rect x="320" y="15" width="290" height="150" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="37" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">\s (preserved space)</text>
  <text x="335" y="65" fill="#e6edf3" font-size="9" font-family="monospace">"""</text>
  <text x="335" y="80" fill="#e6edf3" font-size="9" font-family="monospace">Name:  Ada\s</text>
  <text x="335" y="95" fill="#e6edf3" font-size="9" font-family="monospace">"""</text>
  <text x="335" y="120" fill="#6db33f" font-size="9" font-family="sans-serif">Value: "Name:  Ada "</text>
  <text x="335" y="135" fill="#8b949e" font-size="8" font-family="sans-serif">(trailing space kept —</text>
  <text x="335" y="150" fill="#8b949e" font-size="8" font-family="sans-serif">without \s it would be stripped)</text>
</svg>

`\` at end-of-line removes a newline from the value; `\s` inserts (and protects) a single space that would otherwise be trimmed.

## 5. Runnable example

Scenario: generating a fixed-width report line where trailing spaces matter for alignment, and separately wrapping a long descriptive string across multiple source lines without it becoming multi-line in the actual value — first showing the trailing-space-stripping problem `\s` solves, then the line-continuation use of `\`, then combining both in a small report-generator.

### Level 1 — Basic

```java
// File: TrailingSpaceProblem.java
public class TrailingSpaceProblem {
    public static void main(String[] args) {
        String withoutEscape = """
            Name:  Ada   
            Role:  Engineer   
            """;
        String withEscape = """
            Name:  Ada\s\s\s
            Role:  Engineer\s\s\s
            """;

        System.out.println("Without \\s, line length: " + withoutEscape.lines().findFirst().get().length());
        System.out.println("With \\s, line length:    " + withEscape.lines().findFirst().get().length());
    }
}
```

**How to run:** requires the preview flag since this is a Java 14 second-preview feature:
```
javac --release 14 --enable-preview TrailingSpaceProblem.java
java --enable-preview TrailingSpaceProblem
```
(On modern JDKs 15+, text blocks and these escapes are permanent and no flags are needed.)

Expected output:
```
Without \s, line length: 10
With \s, line length:    13
```

The first block's source had trailing spaces after `"Ada"` too, but the compiler's automatic whitespace stripping removed them — `"Name:  Ada"` is 10 characters. The second block used `\s\s\s` (three escaped spaces) which survive stripping, making `"Name:  Ada   "` 13 characters — exactly the 3 extra trailing spaces preserved.

### Level 2 — Intermediate

```java
// File: LineContinuation.java
public class LineContinuation {
    public static void main(String[] args) {
        String wrapped = """
            This describes a configuration option that has a fairly long \
            explanation, wrapped across multiple source lines purely for \
            source readability, but the resulting string is one single line.""";

        String notWrapped = """
            This is a genuinely
            multi-line string
            with real line breaks.""";

        System.out.println("Wrapped value has " + wrapped.lines().count() + " line(s):");
        System.out.println(wrapped);
        System.out.println();
        System.out.println("Not-wrapped value has " + notWrapped.lines().count() + " line(s):");
        System.out.println(notWrapped);
    }
}
```

**How to run:** `javac --release 14 --enable-preview LineContinuation.java && java --enable-preview LineContinuation`

Expected output:
```
Wrapped value has 1 line(s):
This describes a configuration option that has a fairly long explanation, wrapped across multiple source lines purely for source readability, but the resulting string is one single line.

Not-wrapped value has 3 line(s):
This is a genuinely
multi-line string
with real line breaks.
```

The `\` at the end of each source line in `wrapped` suppressed that line's newline from the resulting string entirely — three source lines collapsed into one logical value line — while `notWrapped`, using plain newlines with no `\` escape, kept all three lines as real line breaks in the resulting string.

### Level 3 — Advanced

```java
// File: FixedWidthReport.java
import java.util.List;

public class FixedWidthReport {
    record Row(String name, String role, int yearsExperience) {}

    static String formatRow(Row r) {
        // Pad name and role to fixed widths using \s to protect trailing spaces,
        // and use \ line-continuation to keep the format template readable in source
        // without injecting unwanted newlines into the final per-row string.
        String namePadded = String.format("%-12s", r.name());
        String rolePadded = String.format("%-15s", r.role());
        return """
            %s\
            %s\
            %d yrs""".formatted(namePadded, rolePadded, r.yearsExperience());
    }

    public static void main(String[] args) {
        List<Row> rows = List.of(
            new Row("Ada", "Engineer", 8),
            new Row("Grace", "Admiral", 44),
            new Row("Alan", "Researcher", 12)
        );

        System.out.println("""
            Name        Role           Experience\s
            ----------------------------------------""");
        for (Row r : rows) {
            System.out.println(formatRow(r));
        }
    }
}
```

**How to run:** `javac --release 14 --enable-preview FixedWidthReport.java && java --enable-preview FixedWidthReport`

Expected output:
```
Name        Role           Experience 
----------------------------------------
Ada         Engineer       8 yrs
Grace       Admiral        44 yrs
Alan        Researcher     12 yrs
```

Level 3 uses `\` line-continuation inside `formatRow`'s text block to keep the three `%s`/`%s`/`%d` format placeholders on separate, readable source lines while producing one single-line formatted row per call, and uses `\s` in the header block to preserve the trailing space after `"Experience"` (perhaps needed for consistent column alignment with a tool that trims trailing whitespace elsewhere) — both escapes chosen for genuinely different, deliberate reasons in the same small program.

## 6. Walkthrough

1. `main` calls `formatRow(new Row("Ada", "Engineer", 8))` inside the loop. First, `String.format("%-12s", "Ada")` left-pads "Ada" with spaces to a total width of 12, producing `"Ada         "` (Ada plus 9 trailing spaces); `String.format("%-15s", "Engineer")` similarly produces `"Engineer       "` (Engineer plus 7 trailing spaces).
2. The text block `"""%s\%s\%d yrs"""` is evaluated. Its source spans three lines, each ending with `\` immediately before the line break — every one of those three `\<line-break>` sequences suppresses the newline that would otherwise appear in the string value at that point, meaning the block's *source* is three lines but its *value* is one continuous line: `"%s%s%d yrs"`.
3. `.formatted(namePadded, rolePadded, r.yearsExperience())` substitutes the three placeholders in order: `%s` becomes `"Ada         "`, `%s` becomes `"Engineer       "`, `%d` becomes `8`, yielding the final string `"Ada         Engineer       8 yrs"`.
4. `formatRow` returns this string, and `System.out.println(formatRow(r))` prints it as one line — critically, the internal `%s`/`%s`/`%d` boundaries produced no stray newlines, because the `\` escapes in the template's source explicitly suppressed them.
5. Before the loop even started, `main` printed the header via a separate text block: `"""Name        Role           Experience\s\n----------------------------------------"""`. Here, the `\s` immediately after `"Experience"` inserts one literal, protected space character; without it, the automatic trailing-whitespace stripping that text blocks perform on every line would have silently removed that trailing space, since it's the last character before the line ends.
6. `System.out.println` prints the header exactly as written: `"Name        Role           Experience "` (with its preserved trailing space, invisible in the terminal but present in the actual string value) followed by the dashed separator line on the next line — the two lines *are* separated by a real newline here, since there's no `\` line-continuation between them in this particular block.
7. This pattern — some newlines suppressed via `\`, others kept as real line breaks, and specific trailing spaces protected via `\s` — is exactly the fine-grained control the second preview added over the first: Java 13's preview could produce multi-line strings and strip trailing whitespace automatically, but had no way to selectively override either behavior at a specific point in the text.

```
formatRow template source (3 lines, each ending in \):
    "%s\" + "%s\" + "%d yrs"
         │        │        │
         ▼        ▼        ▼
    all 3 \-suppressed newlines removed → single-line value: "%s%s%d yrs"
         │
         ▼ .formatted(...)
    "Ada         Engineer       8 yrs"
```

## 7. Gotchas & takeaways

> This is a **second preview** in Java 14, meaning it still requires `--enable-preview`, and while `\s` and `\` line-continuation did become part of the final, permanent text-block specification in Java 15 largely unchanged, always treat preview-era code as subject to refinement until you've verified it against the specific JDK version you're targeting in production.

- `\s` inserts exactly one literal space character and is immune to the automatic trailing-whitespace stripping that every text block otherwise applies to each line.
- `\<line-break>` (a backslash directly followed by the end of a source line) removes that line break from the resulting string value — it's purely a source-formatting tool, not something that changes what the text represents once you factor it in.
- These escapes solve two genuinely different problems: `\s` is about *content* (I need this space to actually be part of the string), while `\` line-continuation is about *source layout* (I want to wrap this line in my editor without changing the string's content).
- Both escapes only make sense inside `"""`-delimited text blocks — they aren't meaningful (or even necessary) in traditional `"..."` string literals, where multi-line content and trailing-whitespace stripping aren't automatic concerns to begin with.
- If a text block's line ends with a real (non-escaped) newline, that newline is part of the string value; only an explicit trailing `\` suppresses it — it's easy to forget the `\` and end up with unwanted embedded newlines when trying to wrap long template strings.
