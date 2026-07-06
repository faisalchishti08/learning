---
card: java
gi: 300
slug: filereader-filewriter
title: FileReader / FileWriter
---

## 1. What it is

`FileReader` and `FileWriter` are convenience `Reader`/`Writer` subclasses for reading and writing text files using **character** streams instead of raw bytes. Internally, each is effectively an `InputStreamReader`/`OutputStreamWriter` wrapping a `FileInputStream`/`FileOutputStream`, but historically they used the platform's default character encoding rather than letting you specify one directly.

```java
import java.io.FileWriter;
import java.io.FileReader;
import java.io.IOException;

public class FileReaderWriterDemo {
    public static void main(String[] args) throws IOException {
        try (FileWriter writer = new FileWriter("note.txt")) {
            writer.write("Hello, text file!");
        }

        try (FileReader reader = new FileReader("note.txt")) {
            char[] buffer = new char[100];
            int charsRead = reader.read(buffer);
            System.out.println(new String(buffer, 0, charsRead));
        }
    }
}
```

`FileWriter.write(String)` encodes and writes the text; `FileReader.read(char[])` decodes bytes back into characters, filling the buffer and returning how many characters were actually read.

## 2. Why & when

`FileReader`/`FileWriter` exist to save you from manually wrapping `FileInputStream`/`FileOutputStream` in `InputStreamReader`/`OutputStreamWriter` for the common case of "I just want to read or write a text file." They are convenience classes layered on the more general byte-plus-encoding machinery.

- **Quick text file access** — for simple scripts or examples, `new FileReader(path)` is shorter than the fully-explicit `InputStreamReader`/`FileInputStream` combination.
- **Line-based reading** — wrapping a `FileReader` in `BufferedReader` gives `readLine()`, the standard way to process a text file one line at a time.
- **Historically encoding-implicit** — older `FileReader`/`FileWriter` constructors take no `Charset` argument at all, silently using the JVM's platform-default encoding, which is exactly the portability trap discussed for `Reader`/`Writer` in general.

Since Java 11, `FileReader` and `FileWriter` gained constructor overloads that accept an explicit `Charset`, closing much of the historical gap — prefer those overloads (`new FileReader(file, StandardCharsets.UTF_8)`) over the no-charset ones whenever portability matters, which is essentially always. For anything beyond the simplest cases, `Files.newBufferedReader(path, charset)` from `java.nio.file` is the modern, equally explicit alternative.

## 3. Core concept

```java
import java.io.FileWriter;
import java.io.FileReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class FileReaderWriterCore {
    public static void main(String[] args) throws IOException {
        try (FileWriter writer = new FileWriter("lines.txt", StandardCharsets.UTF_8)) {
            writer.write("first\nsecond\nthird");
        }

        try (BufferedReader reader = new BufferedReader(new FileReader("lines.txt", StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println("Line: " + line);
            }
        }
    }
}
```

Wrapping `FileReader` in `BufferedReader` is the standard combination for reading text files line by line; specifying `StandardCharsets.UTF_8` explicitly on both the writer and reader (Java 11+) avoids depending on the platform default.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FileReader and FileWriter are convenience classes layered over InputStreamReader and OutputStreamWriter over the raw file streams">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="20" width="240" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">FileReader / FileWriter</text>
  <text x="150" y="80" fill="#8b949e" font-size="9" text-anchor="middle">convenience wrapper for</text>
  <rect x="30" y="90" width="240" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">InputStreamReader / OutputStreamWriter</text>

  <text x="450" y="45" fill="#8b949e" font-size="9" text-anchor="middle">+ BufferedReader</text>
  <text x="450" y="60" fill="#8b949e" font-size="9" text-anchor="middle">-&gt; readLine()</text>
</svg>

`FileReader`/`FileWriter` trade a bit of explicitness for convenience; specify a `Charset` explicitly to get both.

## 5. Runnable example

Scenario: a small CSV-like notes file, evolved from a basic write-then-read into line-by-line processing, then into a version that parses each line into structured fields with error handling for malformed rows.

### Level 1 — Basic

```java
import java.io.FileWriter;
import java.io.FileReader;
import java.io.IOException;

public class FileReaderWriterBasic {
    public static void main(String[] args) throws IOException {
        try (FileWriter writer = new FileWriter("notes.csv")) {
            writer.write("Alice,30\nBob,25\n");
        }

        try (FileReader reader = new FileReader("notes.csv")) {
            char[] buffer = new char[200];
            int charsRead = reader.read(buffer);
            System.out.print(new String(buffer, 0, charsRead));
        }
    }
}
```

**How to run:** `java FileReaderWriterBasic.java`

Writes two comma-separated lines to `notes.csv` and reads the whole file back into one buffer in a single call.

### Level 2 — Intermediate

Same notes file, now processed line by line with `BufferedReader`, splitting each line on the comma to extract the name and age separately.

```java
import java.io.FileWriter;
import java.io.FileReader;
import java.io.BufferedReader;
import java.io.IOException;

public class FileReaderWriterIntermediate {
    public static void main(String[] args) throws IOException {
        try (FileWriter writer = new FileWriter("notes.csv")) {
            writer.write("Alice,30\nBob,25\nCarol,35\n");
        }

        try (BufferedReader reader = new BufferedReader(new FileReader("notes.csv"))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                System.out.println(parts[0] + " is " + parts[1] + " years old");
            }
        }
    }
}
```

**How to run:** `java FileReaderWriterIntermediate.java`

`readLine()` returns each line without its terminator; `line.split(",")` breaks `"Alice,30"` into `["Alice", "30"]`, giving structured access to each field.

### Level 3 — Advanced

Same notes file, now with an explicit UTF-8 charset (Java 11+ constructor), validation that each line has exactly two fields, and a count of how many rows were skipped as malformed.

```java
import java.io.*;
import java.nio.charset.StandardCharsets;

public class FileReaderWriterAdvanced {
    public static void main(String[] args) throws IOException {
        try (FileWriter writer = new FileWriter("notes.csv", StandardCharsets.UTF_8)) {
            writer.write("Alice,30\nBob,25\nmalformed line\nCarol,35\n");
        }

        int validCount = 0;
        int skippedCount = 0;
        try (BufferedReader reader = new BufferedReader(
                new FileReader("notes.csv", StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                String[] parts = line.split(",");
                if (parts.length != 2) {
                    System.out.println("Skipping malformed line: \"" + line + "\"");
                    skippedCount++;
                    continue;
                }
                System.out.println(parts[0] + " is " + parts[1] + " years old");
                validCount++;
            }
        }

        System.out.println("Valid rows: " + validCount + ", skipped: " + skippedCount);
    }
}
```

**How to run:** `java FileReaderWriterAdvanced.java`

The `parts.length != 2` check catches `"malformed line"` (which splits into a single-element array, since it contains no comma) before it can cause an `ArrayIndexOutOfBoundsException` on `parts[1]`, and the explicit `StandardCharsets.UTF_8` argument on both constructors (available since Java 11) guarantees the read matches the write regardless of platform defaults.

## 6. Walkthrough

Trace the reading loop in `FileReaderWriterAdvanced.main` step by step.

**File contents after writing:** `"Alice,30\nBob,25\nmalformed line\nCarol,35\n"` — four lines, one of which (the third) has no comma.

**First `readLine()`.** Returns `"Alice,30"`. `split(",")` produces `["Alice", "30"]`, length `2` — passes validation. Prints `"Alice is 30 years old"`. `validCount` becomes `1`.

**Second `readLine()`.** Returns `"Bob,25"`. Same as above: prints `"Bob is 25 years old"`, `validCount` becomes `2`.

**Third `readLine()`.** Returns `"malformed line"`. `split(",")` on a string with no comma returns the whole string as a single-element array: `["malformed line"]`, length `1` — fails the `!= 2` check. Prints `"Skipping malformed line: \"malformed line\""`, `skippedCount` becomes `1`, and `continue` skips straight to the next loop iteration without touching `parts[1]` (which doesn't exist).

**Fourth `readLine()`.** Returns `"Carol,35"`. Passes validation, prints `"Carol is 35 years old"`, `validCount` becomes `3`.

**Fifth `readLine()`.** Returns `null` (the file's trailing `\n` after `"Carol,35"` doesn't produce a spurious empty extra line — `readLine()` treats a trailing newline as simply ending the last line, not starting a new empty one). The loop ends.

**Final print.** `validCount` is `3`, `skippedCount` is `1`.

```
notes.csv:
  Alice,30           -> valid   -> "Alice is 30 years old"
  Bob,25             -> valid   -> "Bob is 25 years old"
  malformed line     -> INVALID -> skipped, skippedCount++
  Carol,35           -> valid   -> "Carol is 35 years old"

Totals: validCount=3, skippedCount=1
```

**Output:**
```
Alice is 30 years old
Bob is 25 years old
Skipping malformed line: "malformed line"
Carol is 35 years old
Valid rows: 3, skipped: 1
```

## 7. Gotchas & takeaways

> The no-charset `FileReader`/`FileWriter` constructors use the JVM's platform-default encoding, exactly like the general `Reader`/`Writer` case — this can silently corrupt non-ASCII text when code runs on a machine with a different default encoding than where it was written and tested. Since Java 11, always prefer the overloads that take an explicit `Charset` argument.

> `String.split(delimiter)` on a line with no occurrences of the delimiter returns a single-element array containing the whole line — not an empty array. Code that assumes a minimum array length without checking (as the naive Level 2 example does) will throw `ArrayIndexOutOfBoundsException` on malformed input; always validate `parts.length` before indexing when input format isn't guaranteed.

- `FileReader`/`FileWriter` are convenience wrappers over `InputStreamReader`/`OutputStreamWriter` plus the corresponding file byte streams.
- Since Java 11, both accept an explicit `Charset` argument — prefer those overloads over the platform-default ones.
- Wrap `FileReader` in `BufferedReader` for line-by-line text processing via `readLine()`.
- Always validate the structure of parsed data (like the field count after a `split`) before indexing into it, since real-world input files are rarely perfectly well-formed.
