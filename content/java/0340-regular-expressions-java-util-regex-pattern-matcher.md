---
card: java
gi: 340
slug: regular-expressions-java-util-regex-pattern-matcher
title: Regular expressions (java.util.regex: Pattern, Matcher)
---

## 1. What it is

`java.util.regex.Pattern` compiles a regular expression string into a reusable object describing a text pattern, and `java.util.regex.Matcher` applies a compiled `Pattern` against a specific piece of input text, letting you test whether it matches, find all occurrences, or extract captured groups. Compiling the pattern once via `Pattern.compile(regex)` and reusing it across many inputs is significantly more efficient than repeatedly parsing the same regex string.

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RegexDemo {
    public static void main(String[] args) {
        Pattern pattern = Pattern.compile("\\d+");
        Matcher matcher = pattern.matcher("Order #4521 shipped, 3 items");
        while (matcher.find()) {
            System.out.println("Found number: " + matcher.group());
        }
    }
}
```

`pattern.matcher(text)` creates a `Matcher` bound to that specific input, and `matcher.find()` searches forward from wherever the previous match ended, letting a single `while` loop visit every match in the text.

## 2. Why & when

Regular expressions describe a family of text patterns in a compact, standard notation, letting code validate, search, or extract structured pieces of text without writing manual character-by-character parsing logic — but they trade readability and precision for power, so they're best reserved for genuinely pattern-shaped text problems.

- **Validating input format** — checking that a string looks like an email address, a phone number, or a specific ID format before accepting it.
- **Searching and extracting substrings** — pulling all numbers, dates, or tagged values out of a larger block of text, using capturing groups to isolate the parts you actually need.
- **Search-and-replace with patterns** — `String.replaceAll(regex, replacement)` and `Matcher.replaceAll(replacement)` apply a pattern-based substitution across text, far more flexible than a literal find-and-replace.

Regular expressions are notoriously easy to get subtly wrong — greedy vs. reluctant quantifiers, unescaped special characters, and patterns that technically match unintended input are common pitfalls — so testing a regex against a range of realistic and edge-case inputs matters more than it might for more straightforward code.

## 3. Core concept

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class RegexCore {
    public static void main(String[] args) {
        Pattern pattern = Pattern.compile("(\\w+)@(\\w+\\.\\w+)"); // capturing groups
        Matcher matcher = pattern.matcher("Contact: ada@example.com or grace@test.org");
        while (matcher.find()) {
            System.out.println("Full match: " + matcher.group(0));
            System.out.println("  Username: " + matcher.group(1));
            System.out.println("  Domain: " + matcher.group(2));
        }
    }
}
```

**How to run:** `java RegexCore.java`

Parentheses in the pattern define capturing groups: `group(0)` is always the whole match, while `group(1)`, `group(2)`, etc. return just the text matched by each corresponding parenthesized subpattern, letting you extract structured pieces without manual string splitting.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a compiled Pattern applied to text via a Matcher finds successive matches, with parenthesized groups extracting sub-parts of each match">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="180" height="35" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="52" fill="#79c0ff" font-size="10" text-anchor="middle">Pattern.compile(regex)</text>

  <text x="215" y="52" fill="#8b949e" font-size="12">→ .matcher(text) →</text>

  <rect x="360" y="30" width="220" height="35" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="52" fill="#6db33f" font-size="10" text-anchor="middle">Matcher (bound to input text)</text>

  <text x="20" y="100" fill="#8b949e" font-size="10">find() locates the next match; group(0) = whole match, group(n) = nth captured subpattern</text>
</svg>

## 5. Runnable example

Scenario: a log-line parser extracting timestamps and severity levels, evolved from a basic single-pattern match, into one using named groups to extract structured fields, into a production-style parser that validates every line and reports malformed ones distinctly.

### Level 1 — Basic

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class LogParserBasic {
    public static void main(String[] args) {
        String line = "2024-01-15 ERROR Connection refused";
        Pattern pattern = Pattern.compile("\\d{4}-\\d{2}-\\d{2}");
        Matcher matcher = pattern.matcher(line);
        if (matcher.find()) {
            System.out.println("Found date: " + matcher.group());
        }
    }
}
```

**How to run:** `java LogParserBasic.java`

This extracts just the date substring using `find()` and `group()`, but ignores everything else in the line — the severity level and message aren't captured at all, so this is only a first step toward genuinely parsing the log format.

### Level 2 — Intermediate

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class LogParserIntermediate {
    public static void main(String[] args) {
        String[] lines = {
                "2024-01-15 ERROR Connection refused",
                "2024-01-16 INFO Server started"
        };
        Pattern pattern = Pattern.compile("(?<date>\\d{4}-\\d{2}-\\d{2}) (?<level>\\w+) (?<message>.+)");
        for (String line : lines) {
            Matcher matcher = pattern.matcher(line);
            if (matcher.matches()) { // matches() requires the WHOLE string to match
                System.out.println("Date: " + matcher.group("date")
                        + ", Level: " + matcher.group("level")
                        + ", Message: " + matcher.group("message"));
            }
        }
    }
}
```

**How to run:** `java LogParserIntermediate.java`

Named groups (`(?<name>...)`) make the pattern self-documenting and let `matcher.group("date")` read fields by name instead of a fragile positional index, and `matches()` (requiring the *entire* string to conform to the pattern, unlike `find()`) ensures the whole line is well-formed, not just some substring of it.

### Level 3 — Advanced

```java
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.ArrayList;
import java.util.List;

public class LogParserAdvanced {
    record LogEntry(String date, String level, String message) {}

    public static void main(String[] args) {
        String[] lines = {
                "2024-01-15 ERROR Connection refused",
                "not a valid log line at all",
                "2024-01-16 INFO Server started"
        };

        Pattern pattern = Pattern.compile("(?<date>\\d{4}-\\d{2}-\\d{2}) (?<level>ERROR|WARN|INFO|DEBUG) (?<message>.+)");
        List<LogEntry> parsed = new ArrayList<>();
        List<String> malformed = new ArrayList<>();

        for (String line : lines) {
            Matcher matcher = pattern.matcher(line);
            if (matcher.matches()) {
                parsed.add(new LogEntry(matcher.group("date"), matcher.group("level"), matcher.group("message")));
            } else {
                malformed.add(line);
            }
        }

        System.out.println("Parsed " + parsed.size() + " entries:");
        parsed.forEach(e -> System.out.println("  " + e));
        System.out.println("Malformed lines (" + malformed.size() + "): " + malformed);
    }
}
```

**How to run:** `java LogParserAdvanced.java`

Restricting the `level` group to a specific alternation (`ERROR|WARN|INFO|DEBUG`) rejects lines with an unrecognized severity level as malformed rather than accepting arbitrary text there, and lines that fail to match at all are collected separately instead of silently skipped, giving a complete, accountable picture of what was and wasn't successfully parsed.

## 6. Walkthrough

Execution starts in `main`, which compiles the pattern once (reused for every line) and iterates the three `lines`, applying `pattern.matcher(line)` and `matcher.matches()` to each.

**First line — `"2024-01-15 ERROR Connection refused"`:** `matches()` requires the compiled pattern to account for the *entire* string. The `date` group consumes `"2024-01-15"`, a literal space follows, `level` matches `"ERROR"` (one of the allowed alternatives), another literal space follows, and `message` (`.+`, matching one or more of any character) consumes the rest, `"Connection refused"`. Since the whole string is accounted for, `matches()` returns `true`, and a `LogEntry("2024-01-15", "ERROR", "Connection refused")` is added to `parsed`.

**Second line — `"not a valid log line at all"`:** this string doesn't begin with anything matching `\d{4}-\d{2}-\d{2}`, so no possible way of aligning the pattern against the whole string succeeds; `matches()` returns `false`, and the line is added to `malformed` instead.

**Third line — `"2024-01-16 INFO Server started"`:** the same successful pattern as the first line applies, extracting `date="2024-01-16"`, `level="INFO"`, `message="Server started"`, added to `parsed`.

After the loop, `main` prints the count and contents of `parsed` (two entries, using the `LogEntry` record's automatically generated `toString()`), followed by the count and contents of `malformed` (the one unparseable line).

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="each line is tested against the full pattern via matches; successful lines are decomposed into named groups and collected, failing lines are collected as malformed">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#6db33f" font-size="10">"2024-01-15 ERROR Connection refused" -&gt; matches() true -&gt; LogEntry(date, ERROR, message)</text>
  <text x="20" y="55" fill="#f85149" font-size="10">"not a valid log line at all" -&gt; matches() false (no date prefix) -&gt; added to malformed</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">"2024-01-16 INFO Server started" -&gt; matches() true -&gt; LogEntry(date, INFO, message)</text>
  <text x="20" y="115" fill="#8b949e" font-size="10">Result: parsed = [2 entries], malformed = [1 line]</text>
</svg>

## 7. Gotchas & takeaways

> `matcher.matches()` requires the *entire* input to conform to the pattern, while `matcher.find()` only requires *some substring* to match — using `find()` when you meant `matches()` (or vice versa) is one of the most common regex bugs in Java, silently accepting or rejecting the wrong things.

- Compile a `Pattern` once (`Pattern.compile`) and reuse it across many inputs — recompiling the same regex string repeatedly wastes real work.
- Named groups (`(?<name>...)`) make patterns and extraction code far more maintainable than relying on positional group indices, especially as patterns grow complex.
- `find()` searches for the next match anywhere in the remaining text (call repeatedly in a loop to find all matches); `matches()` checks that the whole string conforms to the pattern in one shot.
- Restricting an alternation (like a fixed set of allowed values: `ERROR|WARN|INFO|DEBUG`) rather than a loose wildcard (`\w+`) lets a pattern reject genuinely invalid input instead of silently accepting anything.
- Regex special characters (`.`, `*`, `+`, `(`, `)`, `\`, and others) must be escaped when they should be treated literally — a common source of subtle bugs when a pattern is built from user-supplied or otherwise dynamic text.
