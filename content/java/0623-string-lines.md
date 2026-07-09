---
card: java
gi: 623
slug: string-lines
title: String.lines()
---

## 1. What it is

`String.lines()` is a Java 11 method that splits a string into a **`Stream<String>` of lines**, where line terminators are `\n` (line feed), `\r` (carriage return), or `\r\n` (CR+LF). It is the streaming counterpart to `String.split("\\R")` but returns a lazily-evaluated `Stream` instead of an eagerly-allocated array. The stream does not include the line terminator characters themselves — each emitted string is the content between terminators, or the final content after the last terminator. An empty string produces a stream with one element (the empty string), and a string ending with a line terminator does not produce a trailing empty element.

## 2. Why & when

Processing text line by line is one of the most common programming tasks — reading logs, parsing CSV, processing configuration files, analysing prose. Before Java 11, converting a multi-line string into lines required either `String.split("\\n")` (which creates an array eagerly and does not handle `\r\n` or `\r` uniformly) or a `BufferedReader` wrapping a `StringReader`. `lines()` provides a concise, lazy, Unicode-line-break-aware alternative that integrates directly with the Stream API: you can `filter`, `map`, `collect`, or `forEach` without materialising an intermediate array. Use it whenever you have a multi-line string and want to process its lines with stream operations.

## 3. Core concept

```java
String text = "apple\nbanana\r\ncherry\rorange";

text.lines()   // Stream<String>: ["apple", "banana", "cherry", "orange"]
    .map(String::toUpperCase)
    .forEach(System.out::println);
// Prints: APPLE BANANA CHERRY ORANGE

// Edge cases:
"".lines().count();          // 1 (the empty string itself)
"a\nb\n".lines().count();  // 2 ("a", "b") — no trailing empty string
```

The method recognises `\n`, `\r`, and `\r\n` as line terminators, conforming to the definition in `java.io.BufferedReader.readLine()`. The stream is sequential and lazily evaluated.

## 4. Diagram

<svg viewBox="0 0 580 140" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="String.lines() splits a multi-line string into a Stream of lines">
  <rect x="10" y="10" width="560" height="120" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="160" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="100" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"a\nb\r\nc\n"</text>
  <text x="100" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">raw string</text>

  <text x="190" y="47" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="210" y="25" width="100" height="40" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="260" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">.lines()</text>
  <text x="260" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">split</text>

  <text x="320" y="47" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="340" y="15" width="220" height="60" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="450" y="34" fill="#3fb950" font-size="9" text-anchor="middle" font-family="monospace">Stream&lt;String&gt;</text>
  <text x="450" y="48" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">["a", "b", "c"]</text>
  <text x="450" y="62" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">terminators removed</text>

  <text x="20" y="90" fill="#8b949e" font-size="9" font-family="sans-serif">Line terminators: \\n  |  \\r  |  \\r\\n</text>
  <text x="20" y="108" fill="#8b949e" font-size="9" font-family="sans-serif">No trailing empty line for strings ending with terminator</text>
  <text x="340" y="108" fill="#f85149" font-size="9" font-family="sans-serif">"".lines().count() == 1  (the empty string)</text>
</svg>

`lines()` converts a flat multi-line string into a lazily-evaluated stream of individual line strings, ready for stream processing.

## 5. Runnable example

Scenario: processing a server log file stored as a multi-line string — starting with basic line extraction, extending to filtering and transformation, and finally handling edge cases with different line endings and empty inputs.

### Level 1 — Basic

```java
// File: LinesDemo.java
public class LinesDemo {
    public static void main(String[] args) {
        String log = "INFO: Server started\nDEBUG: Loading config\nINFO: Listening on port 8080\nERROR: Connection timeout";

        System.out.println("All log lines:");
        log.lines().forEach(line -> System.out.println("  " + line));

        System.out.println("\nLine count: " + log.lines().count());
    }
}
```

**How to run:** `java LinesDemo.java`

Expected output:
```
All log lines:
  INFO: Server started
  DEBUG: Loading config
  INFO: Listening on port 8080
  ERROR: Connection timeout

Line count: 4
```

The simplest usage: `lines()` splits on `\n` and returns a `Stream<String>` that can be consumed with `forEach` or counted with `count()`. Note that a stream can only be consumed once — calling `log.lines()` twice creates two independent streams.

### Level 2 — Intermediate

```java
// File: LogProcessor.java
import java.util.*;
import java.util.stream.*;

public class LogProcessor {
    public static void main(String[] args) {
        // Simulated log with mixed line endings (Unix, Windows, old Mac)
        String log = """
            INFO: Server started
            DEBUG: Loading config
            INFO: Listening on port 8080
            ERROR: Connection timeout
            WARN: Memory usage at 85%
            INFO: Health check passed
            ERROR: Disk space low
            """;

        // Filter: only errors and warnings
        System.out.println("=== Errors and Warnings ===");
        log.lines()
            .filter(line -> line.startsWith("ERROR") || line.startsWith("WARN"))
            .forEach(System.out::println);

        // Count by severity
        System.out.println("\n=== Severity Counts ===");
        Map<String, Long> counts = log.lines()
            .filter(line -> !line.isBlank())
            .map(line -> line.split(":")[0])
            .collect(Collectors.groupingBy(
                severity -> severity,
                Collectors.counting()
            ));
        counts.forEach((severity, count) ->
            System.out.printf("  %-6s: %d%n", severity, count));

        // Extract just the messages (after the colon)
        System.out.println("\n=== Messages Only ===");
        log.lines()
            .filter(line -> !line.isBlank())
            .map(line -> line.substring(line.indexOf(":") + 2))
            .forEach(msg -> System.out.println("  " + msg));
    }
}
```

**How to run:** `java LogProcessor.java`

Expected output:
```
=== Errors and Warnings ===
ERROR: Connection timeout
WARN: Memory usage at 85%
ERROR: Disk space low

=== Severity Counts ===
  INFO  : 3
  DEBUG : 1
  ERROR : 2
  WARN  : 1

=== Messages Only ===
  Server started
  Loading config
  Listening on port 8080
  Connection timeout
  Memory usage at 85%
  Health check passed
  Disk space low
```

The real-world concern: log processing pipelines. `lines()` + `filter` + `map` + `collect` forms a complete ETL pipeline in a single chain — no intermediate arrays, no manual loops. The `filter(line -> !line.isBlank())` guards against blank lines that might appear in real log files.

### Level 3 — Advanced

```java
// File: LinesEdgeCases.java
import java.util.*;
import java.util.stream.*;

public class LinesEdgeCases {
    public static void main(String[] args) {
        System.out.println("=== Edge case: empty string ===\n");

        String empty = "";
        System.out.println("empty.lines().count(): " + empty.lines().count());
        empty.lines().forEach(s -> System.out.println("  line: '" + s + "'"));

        System.out.println("\n=== Edge case: blank lines in content ===\n");

        String withBlanks = "first\n\nthird\n\n\nfifth";
        System.out.println("Total lines: " + withBlanks.lines().count());
        withBlanks.lines().forEach(s ->
            System.out.println("  '" + s + "'  (blank=" + s.isBlank() + ")"));

        System.out.println("\n=== Edge case: mixed line endings (\\n, \\r\\n, \\r) ===\n");

        // Simulating a file with mixed line endings
        String mixed = "line1\nline2\r\nline3\rline4\n";
        System.out.println("Mixed-endings line count: " + mixed.lines().count());
        mixed.lines().forEach(System.out::println);
        // Note: no trailing empty element for the final \n

        System.out.println("\n=== Practical: CSV-like parsing with lines() ===\n");

        String csvData = """
            name,age,city
            Alice,30,London
            Bob,25,Paris
            Charlie,35,Berlin
            """;

        // Skip header, parse records
        List<String[]> records = csvData.lines()
            .filter(line -> !line.isBlank())
            .skip(1)  // skip header
            .map(line -> line.split(","))
            .collect(Collectors.toList());

        System.out.println("Parsed records:");
        for (String[] fields : records) {
            System.out.printf("  %-10s %3s  %-10s%n", fields[0], fields[1], fields[2]);
        }

        System.out.println("\n=== Stream reuse warning ===\n");
        // A stream from lines() can only be consumed once
        Stream<String> lines = csvData.lines();
        System.out.println("First consumption: " + lines.count() + " lines");
        try {
            lines.count();  // Stream already consumed — throws IllegalStateException
        } catch (IllegalStateException e) {
            System.out.println("Second consumption: IllegalStateException (stream already operated upon or closed)");
        }
    }
}
```

**How to run:** `java LinesEdgeCases.java`

Expected output:
```
=== Edge case: empty string ===

empty.lines().count(): 1
  line: ''

=== Edge case: blank lines in content ===

Total lines: 6
  'first'  (blank=false)
  ''  (blank=true)
  'third'  (blank=false)
  ''  (blank=true)
  ''  (blank=true)
  'fifth'  (blank=false)

=== Edge case: mixed line endings (\n, \r\n, \r) ===

Mixed-endings line count: 4
line1
line2
line3
line4

=== Practical: CSV-like parsing with lines() ===

Parsed records:
  Alice       30  London    
  Bob         25  Paris     
  Charlie     35  Berlin    

=== Stream reuse warning ===

First consumption: 0 lines
Second consumption: IllegalStateException (stream already operated upon or closed)
```

The production-flavoured hard cases: (1) empty string returns a stream with one element (the empty string), which can be surprising — always filter with `!isBlank()` if you want to skip empty lines. (2) Mixed line endings (`\n`, `\r\n`, `\r`) are all handled uniformly, making `lines()` superior to manual `split("\\n")`. (3) The returned stream follows standard stream semantics: it can only be consumed once. Call `lines()` again if you need to re-process. (4) No trailing empty line — a string ending with `\n` does not produce an extra empty element at the end.

## 6. Walkthrough

Tracing the log processing example `log.lines().filter(...).map(...).collect(...)` end to end:

1. `log.lines()` is called on the multi-line string. The `lines()` method creates a `StringLinesStream` — a lazy spliterator-based stream. No lines are extracted yet; only the source is set up.

2. `.filter(line -> line.startsWith("ERROR") || line.startsWith("WARN"))` attaches a filtering predicate to the stream pipeline. Still lazy — no work is done.

3. `.map(line -> line.split(":")[0])` attaches a mapping function. Still lazy.

4. `.collect(Collectors.groupingBy(severity -> severity, Collectors.counting()))` is the **terminal operation** that triggers evaluation. Now the stream pipeline activates.

5. The collector asks the stream for elements. The spliterator advances through the string, finding line terminators and emitting substrings. Each substring is tested against the filter, transformed by the map, and accumulated into the grouping map.

6. The `HashMap<String, Long>` is populated: "INFO" → 3, "DEBUG" → 1, "ERROR" → 2, "WARN" → 1. This map is the final result.

7. `counts.forEach(...)` iterates the result map and prints the severity counts.

The key efficiency insight: `lines()` never allocates an array of all lines. The spliterator walks the original string's character array, yielding substrings on demand. For large strings (e.g. a 100 MB log file loaded as a String), this avoids duplicating the entire content in memory.

## 7. Gotchas & takeaways

> Unlike `split("\\n")`, `lines()` does **not** produce a trailing empty string when the input ends with a line terminator. `"a\nb\n".lines().count()` is `2`, not `3`. This matches `BufferedReader.readLine()` semantics but differs from `split()`, which would produce `["a", "b", ""]`.

- `lines()` handles `\n`, `\r\n`, and `\r` uniformly — you don't need to normalise line endings before processing. This makes it suitable for reading files that may have been created on different operating systems.
- The returned `Stream<String>` is sequential and lazily evaluated. No intermediate array is materialised, which saves memory for large strings.
- Like all streams, the result of `lines()` can only be consumed once. To iterate multiple times, either call `lines()` again or collect to a `List<String>` first.
- An empty string `""` produces a stream with one element (the empty string `""`), not an empty stream. If "no lines" is the desired semantics for empty input, use `.filter(Predicate.not(String::isBlank))`.
- The method delegates to `StringLatin1.lines()` or `StringUTF16.lines()` internally, both of which use a `Spliterator` that walks the underlying byte/char array directly — no regex engine is involved, making it faster than `split()`.
