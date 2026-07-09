---
card: java
gi: 488
slug: files-lines-bufferedreader-lines
title: Files.lines() / BufferedReader.lines()
---

## 1. What it is

`Files.lines(path)` opens a text file and returns a `Stream<String>` where each element is one line of the file, read **lazily** — lines are pulled from disk as the stream is consumed, not all loaded into memory upfront. `BufferedReader.lines()` does the same thing starting from an already-open `BufferedReader` rather than a `Path`. Both implement `AutoCloseable`-backed streams: the underlying file handle must be closed when you're done, typically with try-with-resources.

## 2. Why & when

Reading a file line by line used to mean a `while ((line = reader.readLine()) != null)` loop with manual accumulation. `Files.lines`/`BufferedReader.lines` let you treat the file's lines as a stream instead — filterable, mappable, collectible with the same operations used everywhere else in the Streams API. The laziness matters most for large files: `Files.readAllLines(path)` loads the *entire* file into a `List<String>` in memory first, while `Files.lines(path)` reads and processes one line at a time, so a multi-gigabyte log file can be scanned without ever holding it all in memory at once.

You reach for `Files.lines` when processing a file from a `Path` directly (the common case), and `BufferedReader.lines()` when you already have a `Reader` open — for example, one wrapping an `InputStream` from a network connection or a resource on the classpath, rather than a plain file on disk.

## 3. Core concept

```java
import java.io.*;
import java.nio.file.*;
import java.util.stream.*;

// Files.lines -- from a Path, lazy, must be closed
try (Stream<String> lines = Files.lines(Path.of("data.txt"))) {
    long count = lines.filter(line -> !line.isBlank()).count();
}

// BufferedReader.lines -- from an already-open Reader
try (BufferedReader reader = new BufferedReader(new FileReader("data.txt"))) {
    reader.lines().forEach(System.out::println);
}
```

Both return a lazily-populated `Stream<String>` backed by an open resource — the try-with-resources block ensures that resource is released once the stream is done being used.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Files.lines reads a file lazily, one line at a time, as the stream is consumed">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="45" width="110" height="60" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="85" y="70" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">data.txt</text>
  <text x="85" y="88" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(on disk)</text>
  <line x1="140" y1="75" x2="220" y2="75" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrowL)"/>
  <text x="180" y="65" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">1 line at a time</text>
  <rect x="230" y="45" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="305" y="70" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Stream&lt;String&gt;</text>
  <text x="305" y="88" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(lazy, pull-based)</text>
  <line x1="380" y1="75" x2="460" y2="75" stroke="#8b949e" stroke-width="2" marker-end="url(#arrowL)"/>
  <rect x="470" y="45" width="140" height="60" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="75" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">filter/map/collect</text>
  <defs><marker id="arrowL" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">The whole file is never fully loaded at once -- lines flow through as the pipeline pulls them.</text>
</svg>

Lines are read from disk on demand as the stream pipeline pulls them, not loaded all at once.

## 5. Runnable example

Scenario: scanning a server access log for error lines — evolved from a basic filtered count using `Files.lines`, through extracting structured fields with `map`, to a version that safely handles the resource lifecycle and reports partial failures without leaking the file handle.

### Level 1 — Basic

```java
import java.io.*;
import java.nio.file.*;
import java.util.stream.*;

public class LinesBasic {
    public static void main(String[] args) throws IOException {
        Path logFile = Files.createTempFile("access", ".log");
        Files.writeString(logFile, """
                200 GET /home
                500 GET /checkout
                200 GET /cart
                404 GET /missing
                500 GET /payment
                """);

        try (Stream<String> lines = Files.lines(logFile)) {
            long errorCount = lines.filter(line -> line.startsWith("500")).count();
            System.out.println("Server errors: " + errorCount);
        }

        Files.deleteIfExists(logFile);
    }
}
```

**How to run:** `java LinesBasic.java`

Expected output:
```
Server errors: 2
```

`Files.lines(logFile)` opens the file and lazily exposes each line as a stream element. The try-with-resources block ensures the file is closed automatically once the block exits. `.filter(line -> line.startsWith("500"))` keeps only the two `"500 ..."` lines, and `.count()` reports `2`.

### Level 2 — Intermediate

```java
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class LinesExtractPaths {
    public static void main(String[] args) throws IOException {
        Path logFile = Files.createTempFile("access", ".log");
        Files.writeString(logFile, """
                200 GET /home
                500 GET /checkout
                200 GET /cart
                404 GET /missing
                500 GET /payment
                """);

        try (Stream<String> lines = Files.lines(logFile)) {
            List<String> failingPaths = lines
                    .filter(line -> line.startsWith("500"))
                    .map(line -> line.split(" ")[2]) // extract the path field
                    .toList();
            System.out.println("Failing paths: " + failingPaths);
        }

        Files.deleteIfExists(logFile);
    }
}
```

**How to run:** `java LinesExtractPaths.java`

Expected output:
```
Failing paths: [/checkout, /payment]
```

The real-world concern this adds: instead of just counting matching lines, each `500` line is now parsed to pull out a specific field (the request path), turning raw text lines into structured data via `.map(...)` — the kind of line-by-line extraction that's common when scanning logs for actionable detail rather than just totals.

### Level 3 — Advanced

```java
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;

public class LinesRobustScan {
    record LogEntry(int status, String path) {}

    static Optional<LogEntry> parse(String line) {
        String[] parts = line.split(" ");
        if (parts.length < 3) return Optional.empty(); // malformed line -- skip, don't crash
        try {
            return Optional.of(new LogEntry(Integer.parseInt(parts[0]), parts[2]));
        } catch (NumberFormatException e) {
            return Optional.empty();
        }
    }

    public static void main(String[] args) throws IOException {
        Path logFile = Files.createTempFile("access", ".log");
        Files.writeString(logFile, """
                200 GET /home
                500 GET /checkout
                garbled line here
                404 GET /missing
                500 GET /payment
                """);

        Map<Boolean, List<LogEntry>> partitioned;
        try (Stream<String> lines = Files.lines(logFile)) {
            partitioned = lines
                    .map(LinesRobustScan::parse)
                    .flatMap(Optional::stream) // drop malformed lines silently
                    .collect(Collectors.partitioningBy(entry -> entry.status() >= 500));
        }

        System.out.println("Server errors: " + partitioned.get(true).size());
        System.out.println("Other entries: " + partitioned.get(false).size());

        Files.deleteIfExists(logFile);
    }
}
```

**How to run:** `java LinesRobustScan.java`

Expected output:
```
Server errors: 2
Other entries: 2
```

This adds resilience: real log files can contain malformed lines (here, `"garbled line here"`), so `parse` returns `Optional<LogEntry>` instead of throwing, and `flatMap(Optional::stream)` drops any line that failed to parse — three good outcomes (`200`, `500`, `500`) plus one good `404` line survive, while the garbled fifth line is silently skipped rather than crashing the whole scan. `Collectors.partitioningBy` then splits valid entries into server-errors versus everything else in one pass.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. A temp log file is created with five lines, one of which (`"garbled line here"`) is intentionally malformed.

`Files.lines(logFile)` opens the file lazily inside the try-with-resources block. `.map(LinesRobustScan::parse)` runs `parse` on each line as it's pulled: for `"200 GET /home"`, `parts` is `["200", "GET", "/home"]` (length 3, OK), `Integer.parseInt("200")` succeeds, producing `Optional.of(LogEntry(200, "/home"))`. Same successful path for `"500 GET /checkout"` -> `Optional.of(LogEntry(500, "/checkout"))`.

For `"garbled line here"`, `parts` is `["garbled", "line", "here"]` — length is `3`, so the length check passes, but `Integer.parseInt("garbled")` throws `NumberFormatException`, caught and turned into `Optional.empty()`.

For `"404 GET /missing"` and `"500 GET /payment"`, parsing succeeds the same way as the first two lines.

`.flatMap(Optional::stream)` converts each `Optional<LogEntry>` into either a one-element stream (present) or a zero-element stream (empty, via `Stream.empty()`-equivalent behavior of `Optional::stream`), flattening them all into a single stream of just the four successfully-parsed `LogEntry` values — the malformed line contributes nothing and never appears again downstream.

```
"200 GET /home"      -> parse -> LogEntry(200,/home)     -> kept
"500 GET /checkout"  -> parse -> LogEntry(500,/checkout) -> kept
"garbled line here"  -> parse -> Optional.empty()        -> dropped by flatMap
"404 GET /missing"   -> parse -> LogEntry(404,/missing)  -> kept
"500 GET /payment"   -> parse -> LogEntry(500,/payment)  -> kept
```

`Collectors.partitioningBy(entry -> entry.status() >= 500)` then splits the four surviving entries into two lists keyed by `true`/`false`: `LogEntry(500,/checkout)` and `LogEntry(500,/payment)` go to `true` (status `>= 500`); `LogEntry(200,/home)` and `LogEntry(404,/missing)` go to `false`. `partitioned.get(true).size()` is `2`, printed as `"Server errors: 2"`; `partitioned.get(false).size()` is `2`, printed as `"Other entries: 2"`.

## 7. Gotchas & takeaways

> `Files.lines(path)` **must** be closed — it holds an open file handle for as long as the stream is alive. Forgetting the try-with-resources block (or an equivalent explicit `.close()`) leaks file descriptors, which can eventually exhaust the operating system's limit if the code runs repeatedly (e.g. in a loop or a long-running service).

- `Files.lines(path)` and `BufferedReader.lines()` both expose a file's lines as a lazy `Stream<String>`, reading incrementally rather than loading everything into memory.
- Always wrap the stream in try-with-resources (or otherwise guarantee `.close()`) since it holds an open OS-level file resource.
- Prefer `Files.lines` for large files where `Files.readAllLines` (which returns a fully materialized `List<String>`) would use too much memory.
- Malformed input lines are common in real files — parsing into `Optional<T>` and using `flatMap(Optional::stream)` is a clean way to skip bad lines without crashing the whole pipeline.
- `BufferedReader.lines()` is the right choice when the data doesn't come from a plain file `Path` but from some other already-open `Reader` (a socket, a classpath resource, etc.).
