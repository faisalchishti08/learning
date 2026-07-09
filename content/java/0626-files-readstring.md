---
card: java
gi: 626
slug: files-readstring
title: Files.readString()
---

## 1. What it is

`Files.readString(Path)` is a Java 11 method that reads the **entire contents of a file into a single `String`** in one call. It is the modern replacement for the verbose pre-Java 11 pattern of `new String(Files.readAllBytes(path), charset)`. The method uses UTF-8 as the default charset (a significant improvement over the older `Files.readAllLines` and `BufferedReader` approaches which defaulted to the platform's native charset). An overload `Files.readString(Path, Charset)` allows specifying an explicit charset. The method throws `IOException` on I/O errors and `OutOfMemoryError` if the file is too large to fit in memory.

## 2. Why & when

Reading an entire file into a `String` is one of the most common I/O operations: loading configuration files, reading JSON/XML payloads, processing small-to-medium text files, or fetching cached data. Before Java 11, the simplest correct one-liner was `new String(Files.readAllBytes(path), StandardCharsets.UTF_8)` — which is verbose, easy to forget the charset on, and requires two method calls. `Files.readString()` makes the intent crystal clear and defaults to UTF-8, which is the correct default for the modern web and almost all text formats. Use it for files up to a few megabytes; for larger files, use streaming (`BufferedReader.lines()`) to avoid loading the entire content into memory.

## 3. Core concept

```java
Path path = Path.of("config.json");

// Java 11+: read entire file to String
String content = Files.readString(path);

// With explicit charset
String latin1Content = Files.readString(path, StandardCharsets.ISO_8859_1);

// Before Java 11 (the old way):
String oldWay = new String(Files.readAllBytes(path), StandardCharsets.UTF_8);
```

The method opens the file, reads all bytes, decodes them into characters using the specified (or default UTF-8) charset, and closes the file — all in one call. It is a convenience method that eliminates boilerplate and reduces the risk of charset-related bugs.

## 4. Diagram

<svg viewBox="0 0 540 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Files.readString reads entire file content into a String in one call">
  <rect x="10" y="10" width="520" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="100" height="40" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="70" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">📄 file.txt</text>
  <text x="70" y="57" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">on disk</text>

  <text x="135" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="155" y="20" width="180" height="50" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="245" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Files.readString(path)</text>
  <text x="245" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">reads all bytes → UTF-8 decode → String</text>

  <text x="350" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="370" y="25" width="150" height="40" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="445" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">"Hello\nWorld"</text>
  <text x="445" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">in-memory String</text>

  <text x="20" y="100" fill="#8b949e" font-size="9" font-family="sans-serif">Default charset: UTF-8  |  Override: readString(path, charset)</text>
  <text x="20" y="118" fill="#f85149" font-size="9" font-family="sans-serif">Throws: IOException (I/O error), OutOfMemoryError (file too large), SecurityException (no read access)</text>
  <text x="390" y="118" fill="#3fb950" font-size="9" font-family="sans-serif">Introduced in Java 11</text>
</svg>

`Files.readString()` collapses open-read-decode-close into a single method call, with UTF-8 as the sensible default.

## 5. Runnable example

Scenario: building a simple configuration loader that reads a JSON config file, processes its contents, and handles errors — starting with basic file reading, extending to robust error handling, and finally handling charset detection and large-file safety.

### Level 1 — Basic

```java
// File: ReadStringDemo.java
import java.io.*;
import java.nio.file.*;

public class ReadStringDemo {
    public static void main(String[] args) throws IOException {
        // First, create a sample file to read
        Path file = Path.of("sample.txt");
        Files.writeString(file, "Hello, Java 11!\nThis is line two.\nAnd line three.");

        // Read it back in one call
        String content = Files.readString(file);

        System.out.println("File contents (" + content.lines().count() + " lines):");
        System.out.println(content);

        // Clean up
        Files.deleteIfExists(file);
    }
}
```

**How to run:** `java ReadStringDemo.java`

Expected output:
```
File contents (3 lines):
Hello, Java 11!
This is line two.
And line three.
```

The simplest usage: `Files.readString(path)` reads the entire file into a `String` with a single call. No `BufferedReader`, no `StringBuilder`, no charset specification needed.

### Level 2 — Intermediate

```java
// File: ConfigLoader.java
import java.io.*;
import java.nio.file.*;

public class ConfigLoader {
    public static void main(String[] args) {
        // Create a config file
        Path configPath = Path.of("app.config");
        try {
            Files.writeString(configPath, """
                # Application Configuration
                app.name=LearningHub
                app.version=11.0
                app.debug=true
                db.host=localhost
                db.port=5432
                """);
        } catch (IOException e) {
            System.out.println("Failed to create config: " + e.getMessage());
            return;
        }

        // Load and parse the config
        try {
            String raw = Files.readString(configPath);
            System.out.println("=== Raw config ===");
            System.out.println(raw);

            System.out.println("=== Parsed values ===");
            raw.lines()
                .filter(line -> !line.isBlank() && !line.startsWith("#"))
                .forEach(line -> {
                    String[] parts = line.split("=", 2);
                    System.out.printf("  %-15s → %s%n", parts[0], parts[1]);
                });

        } catch (NoSuchFileException e) {
            System.out.println("Config file not found: " + configPath);
        } catch (IOException e) {
            System.out.println("Error reading config: " + e.getMessage());
        } finally {
            // Clean up
            try { Files.deleteIfExists(configPath); } catch (IOException ignored) {}
        }
    }
}
```

**How to run:** `java ConfigLoader.java`

Expected output:
```
=== Raw config ===
# Application Configuration
app.name=LearningHub
app.version=11.0
app.debug=true
db.host=localhost
db.port=5432

=== Parsed values ===
  app.name        → LearningHub
  app.version     → 11.0
  app.debug       → true
  db.host         → localhost
  db.port         → 5432
```

The real-world concern: configuration loading. The example creates a config file, reads it with `Files.readString()`, then processes the content line-by-line using `lines()`. Specific exception handling (`NoSuchFileException`, `IOException`) makes the loader robust. The `finally` block cleans up the temporary file.

### Level 3 — Advanced

```java
// File: ReadStringAdvanced.java
import java.io.*;
import java.nio.charset.*;
import java.nio.file.*;

public class ReadStringAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Charset handling ===\n");

        // Write a file with ISO-8859-1 encoding (Latin-1)
        Path latin1File = Path.of("latin1.txt");
        try {
            // German umlauts in Latin-1
            String german = "M\u00fcnchen \u00dcber \u00c4pfel";
            Files.writeString(latin1File, german, StandardCharsets.ISO_8859_1);
            System.out.println("Written (ISO-8859-1): " + german);

            // Read back with wrong charset — garbled
            String wrong = Files.readString(latin1File, StandardCharsets.UTF_8);
            System.out.println("Read as UTF-8 (WRONG):  " + wrong);

            // Read back with correct charset
            String correct = Files.readString(latin1File, StandardCharsets.ISO_8859_1);
            System.out.println("Read as ISO-8859-1:     " + correct);

        } catch (IOException e) {
            System.out.println("Error: " + e.getMessage());
        }

        System.out.println("\n=== File-not-found handling ===\n");

        Path missing = Path.of("does_not_exist.txt");
        try {
            Files.readString(missing);
        } catch (NoSuchFileException e) {
            System.out.println("Handled: file not found — " + missing);
        } catch (IOException e) {
            System.out.println("Other I/O error: " + e.getMessage());
        }

        System.out.println("\n=== Large-file awareness ===\n");

        // Write a moderately large file
        Path largeFile = Path.of("large.txt");
        try {
            // Create a 100 KB file
            String line = "This is a line of text that will be repeated.\n";
            Files.writeString(largeFile, line.repeat(2000));  // ~100 KB
            long size = Files.size(largeFile);
            System.out.println("File size: " + size + " bytes");

            // Read it back
            String content = Files.readString(largeFile);
            System.out.println("Lines read: " + content.lines().count());
            System.out.println("First line: " + content.lines().findFirst().orElse("none"));
        } catch (IOException e) {
            System.out.println("Error: " + e.getMessage());
        }

        // Clean up all files
        try {
            Files.deleteIfExists(latin1File);
            Files.deleteIfExists(largeFile);
        } catch (IOException ignored) {}
    }
}
```

**How to run:** `java ReadStringAdvanced.java`

Expected output:
```
=== Charset handling ===

Written (ISO-8859-1): München Über Äpfel
Read as UTF-8 (WRONG):  MÃ¼nchen Ãœber Ã„pfel
Read as ISO-8859-1:     München Über Äpfel

=== File-not-found handling ===

Handled: file not found — does_not_exist.txt

=== Large-file awareness ===

File size: ... bytes
Lines read: 2000
First line: This is a line of text that will be repeated.
```

The production-flavoured hard cases: (1) **Charset mismatches** — reading a Latin-1 file as UTF-8 produces garbled text (mojibake). Always know your file's encoding. `readString()` defaults to UTF-8; use the `Charset` overload for other encodings. (2) **Missing files** — `readString()` throws `NoSuchFileException` (a subclass of `IOException`) when the file doesn't exist. Handle it specifically for user-friendly error messages. (3) **Large files** — `readString()` loads the entire file into memory. For multi-megabyte files, consider `Files.newBufferedReader(path)` and process line-by-line instead.

## 6. Walkthrough

Tracing `String content = Files.readString(Path.of("sample.txt"))`:

1. `Path.of("sample.txt")` creates a `Path` object representing the file `sample.txt` in the current working directory. This is a lightweight object — no I/O yet.

2. `Files.readString(path)` is called. Internally, it calls `Files.readAllBytes(path)` which opens a `FileInputStream` (or uses NIO channels) for the file.

3. The JVM reads all bytes from the file into a `byte[]` array. The file size is queried first to allocate a correctly-sized array. If the file is empty, an empty byte array is returned.

4. The bytes are decoded using the specified charset (default: `StandardCharsets.UTF_8`). The `String` constructor `new String(bytes, charset)` is called. If the bytes are not valid UTF-8, a `MalformedInputException` (subclass of `IOException` for reading) may be thrown.

5. The file stream is closed (via try-with-resources internally). The resulting `String` is returned to the caller.

6. The caller now has the full file content as a `String` in memory. No further I/O is performed.

The entire process is synchronous and blocking — the calling thread waits until all bytes are read and decoded. For non-blocking or reactive applications, use `AsynchronousFileChannel` or reactive streams instead.

## 7. Gotchas & takeaways

> `readString()` loads the **entire file into heap memory at once**. For a 1 GB file, this will likely throw `OutOfMemoryError`. Always check file size before calling `readString()` on untrusted input: `if (Files.size(path) > MAX_SIZE) { /* stream instead */ }`. The method is ideal for configuration files, small data files, and test resources — not for logs or data pipelines.

- `readString()` defaults to **UTF-8**, which is the correct default for virtually all modern text formats (JSON, XML, YAML, HTML, source code). This is a deliberate improvement over older Java APIs that defaulted to the platform charset.
- The method throws `NoSuchFileException` (a subclass of `IOException`) when the file doesn't exist, enabling precise error handling without string-matching on exception messages.
- `readString()` is a convenience wrapper around `readAllBytes()` + `new String(bytes, charset)`. There is no performance difference from doing it manually; the benefit is readability and reduced bug surface (forgetting the charset is impossible).
- For empty files, `readString()` returns `""` (empty string), not `null`. There is no ambiguity — an empty file and a file with content are distinguished by `isEmpty()` on the result.
