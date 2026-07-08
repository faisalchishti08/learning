---
card: java
gi: 445
slug: files-readalllines-readallbytes-write
title: Files.readAllLines / readAllBytes / write
---

## 1. What it is

`Files.readAllLines(path)`, `Files.readAllBytes(path)`, and `Files.write(path, data, options...)` are the whole-file convenience methods on `Files` (Java 7) for reading or writing an entire file's content in one call. `readAllLines` returns a `List<String>` (one entry per line); `readAllBytes` returns the raw `byte[]` content, encoding-agnostic; `write` accepts either a `byte[]` or an `Iterable<? extends CharSequence>` (a collection of lines), and takes optional `OpenOption` flags controlling exactly how the write behaves — most notably `StandardOpenOption.APPEND`.

## 2. Why & when

Reading or writing a whole small-to-moderate file used to mean manually wiring up a `BufferedReader`/`BufferedWriter` (or `InputStream`/`OutputStream`) and looping until end-of-file — correct, but boilerplate for the extremely common case of "just give me the file's content" or "just write this content to a file." These three methods collapse that boilerplate into single calls, at the cost of holding the entire file's content in memory at once — a reasonable tradeoff for anything not enormous.

You reach for these whenever a whole file's content genuinely needs to be in memory anyway — parsing a small configuration or data file, generating a report and writing it in one shot, or reading a file to pass its full content elsewhere. For files too large to comfortably hold in memory, the streaming alternatives (`newBufferedReader`/`newBufferedWriter`, covered in the `Files` utility class tutorial) are the better fit.

## 3. Core concept

```java
import java.nio.file.*;
import java.util.*;

Path file = Paths.get("data.csv");

Files.write(file, List.of("alice,92", "bob,78"));         // writes lines, one per element (overwrites by default)
Files.write(file, moreLines, StandardOpenOption.APPEND);   // appends instead of overwriting

List<String> lines = Files.readAllLines(file);             // whole file, split into lines
byte[] rawBytes = Files.readAllBytes(file);                 // whole file, as raw bytes (no line splitting, no charset assumed)
```

`readAllBytes` is the encoding-agnostic option — it makes no assumption about character encoding at all, simply returning whatever bytes are on disk; `readAllLines` (and the `write` overload accepting lines) assumes text and a specific `Charset` (UTF-8 by default on the no-charset-argument overloads).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Files.write without APPEND truncates and replaces a file's entire content; with APPEND, new content is added after the existing content, leaving it intact">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">Files.write(file, newLines) -- default: TRUNCATES, replaces everything</text>
  <rect x="30" y="38" width="200" height="26" fill="#1c2430" stroke="#f85149"/><text x="130" y="56" fill="#f85149" font-size="9" text-anchor="middle">old content -- GONE</text>
  <rect x="250" y="38" width="200" height="26" fill="#1c2430" stroke="#6db33f"/><text x="350" y="56" fill="#6db33f" font-size="9" text-anchor="middle">new content only</text>

  <text x="20" y="95" fill="#6db33f" font-size="11" font-family="sans-serif">Files.write(file, newLines, APPEND) -- adds after existing content</text>
  <rect x="30" y="107" width="200" height="26" fill="#1c2430" stroke="#6db33f"/><text x="130" y="125" fill="#6db33f" font-size="9" text-anchor="middle">old content -- KEPT</text>
  <rect x="230" y="107" width="150" height="26" fill="#1c2430" stroke="#79c0ff"/><text x="305" y="125" fill="#79c0ff" font-size="9" text-anchor="middle">new content appended</text>
</svg>

`StandardOpenOption.APPEND` is the difference between replacing a file's content and adding to it.

## 5. Runnable example

Scenario: maintaining a small grades CSV file — the same file, evolved from a basic write-then-read-all-lines round trip, through appending new rows without wiping existing ones, to correctly handling text encoding with `readAllBytes` and an explicit `Charset`.

### Level 1 — Basic

```java
import java.nio.file.*;
import java.util.*;

public class GradesBasic {
    public static void main(String[] args) throws Exception {
        Path gradesFile = Files.createTempFile("grades", ".csv");

        List<String> rows = List.of("alice,92", "bob,78", "carol,85");
        Files.write(gradesFile, rows); // write() has an overload that accepts an Iterable<CharSequence>, one per line

        List<String> readBack = Files.readAllLines(gradesFile);
        System.out.println("Rows read: " + readBack.size());
        for (String row : readBack) {
            String[] parts = row.split(",");
            System.out.println(parts[0] + " scored " + parts[1]);
        }

        Files.delete(gradesFile);
    }
}
```

**How to run:** `java GradesBasic.java`

`Files.write(gradesFile, rows)` writes each `String` in `rows` as its own line; `Files.readAllLines` reads the whole file back and splits it into a `List<String>` matching what was written.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.util.*;

public class GradesAppend {
    public static void main(String[] args) throws Exception {
        Path gradesFile = Files.createTempFile("grades", ".csv");
        Files.write(gradesFile, List.of("alice,92", "bob,78"));

        // Without APPEND, write() TRUNCATES the file by default -- this would wipe out the existing rows.
        Files.write(gradesFile, List.of("dave,60"), StandardOpenOption.APPEND);

        List<String> allRows = Files.readAllLines(gradesFile);
        System.out.println("Total rows after append: " + allRows.size());
        allRows.forEach(System.out::println);

        Files.delete(gradesFile);
    }
}
```

**How to run:** `java GradesAppend.java`

`StandardOpenOption.APPEND` changes the second `write` call's behavior entirely — instead of truncating and replacing the file's content (the default), the new line is added after the existing ones, preserving `alice` and `bob`'s rows.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.nio.charset.StandardCharsets;

public class GradesEncodingBinary {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("grades-intl", ".csv");

        String content = "nãme,score\nclémentine,95"; // contains non-ASCII characters (ã, é)
        Files.write(file, content.getBytes(StandardCharsets.UTF_8));

        // Reading back with the SAME charset it was written in: correct
        String correct = new String(Files.readAllBytes(file), StandardCharsets.UTF_8);
        System.out.println("Read with UTF-8 (correct): " + correct.replace("\n", " | "));

        // Reading back with the WRONG charset: silently produces garbled (mojibake) text, no exception thrown
        String garbled = new String(Files.readAllBytes(file), StandardCharsets.ISO_8859_1);
        System.out.println("Read with ISO-8859-1 (wrong): " + garbled.replace("\n", " | "));

        Files.delete(file);
    }
}
```

**How to run:** `java GradesEncodingBinary.java`

`Files.readAllBytes` returns raw bytes with no encoding assumption at all — decoding correctly is entirely the caller's responsibility. Using the *same* charset (`UTF_8`) the file was written in reproduces the original text exactly; using a *different* one (`ISO_8859_1`) silently produces garbled but non-crashing output — a real and common source of subtle text-encoding bugs.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `content` is a two-line `String` containing accented, non-ASCII characters (`ã`, `é`). `Files.write(file, content.getBytes(StandardCharsets.UTF_8))` first converts the `String` into raw bytes using UTF-8 encoding (where each accented character becomes a specific multi-byte sequence), then writes those exact bytes to disk.

`Files.readAllBytes(file)` reads those same raw bytes back, with no interpretation at all — it's simply a `byte[]`. `new String(bytes, StandardCharsets.UTF_8)` decodes those bytes back into a `String`, using the *same* encoding scheme they were written with — so each multi-byte UTF-8 sequence is correctly reassembled into its original character, reproducing `"nãme,score\nclémentine,95"` exactly. This is printed (with the newline replaced by `" | "` for single-line display) as the "correct" result.

`new String(bytes, StandardCharsets.ISO_8859_1)` takes the exact same raw bytes but decodes them using a *different* encoding scheme — ISO-8859-1 interprets every single byte as exactly one character, regardless of whether it was originally part of a multi-byte UTF-8 sequence. Since `ã` and `é` were encoded as multi-byte UTF-8 sequences, ISO-8859-1 misinterprets each of those bytes individually, producing garbled but still-valid-looking text (`"mojibake"`) — critically, this **does not throw an exception**; it just silently produces the wrong content, which is precisely why encoding mismatches are such an insidious class of bug.

Expected output:
```
Read with UTF-8 (correct): nãme,score | clémentine,95
Read with ISO-8859-1 (wrong): nÃ£me,score | clÃ©mentine,95
```

## 7. Gotchas & takeaways

> Reading a file with the **wrong character encoding never throws an exception** — it silently produces garbled text (often called "mojibake"), which can go unnoticed until someone spots oddly-corrupted characters in output much later. Always be deliberate and explicit about which `Charset` a file was written in, and use that exact same `Charset` when reading it back — don't rely on whatever the platform's default charset happens to be, since that can vary between machines and silently produce different (wrong) results.

- `readAllBytes` returns raw, encoding-agnostic bytes; `readAllLines` and the line-based `write` overload assume text and a specific `Charset` (UTF-8 by default on the no-charset overloads).
- `write` **truncates and replaces** a file's content by default — pass `StandardOpenOption.APPEND` explicitly to add to existing content instead.
- These whole-file methods hold the entire file's content in memory — fine for small-to-moderate files, but not appropriate for anything approaching available memory limits.
- A text-encoding mismatch between how a file was written and how it's read back produces silently wrong (garbled) output, never an exception — this makes explicit, consistent `Charset` usage across write and read paths essential.
- For files too large to comfortably hold in memory at once, use the streaming alternatives (`Files.newBufferedReader`/`newBufferedWriter`, or `Files.lines` for a lazy `Stream<String>`) instead of these whole-file methods.
