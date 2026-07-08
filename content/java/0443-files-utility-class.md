---
card: java
gi: 443
slug: files-utility-class
title: Files utility class
---

## 1. What it is

`Files`, part of `java.nio.file` added alongside `Path` in Java 7, is a utility class packed with `static` methods for actually **doing** things with the file system: reading and writing whole files (`readAllBytes`, `write`), checking properties (`exists`, `isRegularFile`, `size`), creating directories (`createDirectories`), listing directory contents (`list`), and opening streaming readers/writers (`newBufferedReader`/`newBufferedWriter`). Where `Path` (the previous tutorial) is purely about representing a location, `Files` is where the actual file-system operations live.

## 2. Why & when

`java.io.File` bundled a smaller, less capable set of file operations directly onto the path-representing object itself, and many of its methods returned an unhelpful `boolean` on failure rather than a specific exception explaining *why* something failed. `Files` (paired with `Path`) fixes both problems: a much richer set of operations, and methods that throw specific, informative exceptions (`NoSuchFileException`, `FileAlreadyExistsException`, and so on) when something goes wrong, rather than a bare `false`.

You reach for `Files` any time you need to actually touch the file system — reading a configuration file's contents, writing output, checking whether a directory exists before creating it, listing what's inside a directory, or streaming through a large file's lines without loading the whole thing into memory at once.

## 3. Core concept

```java
import java.nio.file.*;
import java.util.*;

Path file = Paths.get("data.txt");

Files.exists(file);                    // boolean check, no exception either way
byte[] bytes = Files.readAllBytes(file);          // whole-file read, as raw bytes
List<String> lines = Files.readAllLines(file, java.nio.charset.StandardCharsets.UTF_8); // whole-file read, as lines
Files.write(file, "new content".getBytes());      // whole-file write (overwrites by default)

Files.createDirectories(Paths.get("a/b/c"));      // creates ALL missing intermediate directories
```

`Files`' whole-file methods (`readAllBytes`, `readAllLines`, `write`) are convenient for small-to-moderate files; for anything large, `newBufferedReader`/`newBufferedWriter` (shown in the advanced example below) stream through content without holding it all in memory.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Path represents a location structurally; Files performs actual file-system operations against that location, such as reading, writing, checking existence, and creating directories">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="55" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Path (a location)</text>

  <rect x="330" y="30" width="280" height="90" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="470" y="50" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Files (operations against that location)</text>
  <text x="470" y="70" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">exists, readAllBytes, write,</text>
  <text x="470" y="86" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">createDirectories, list, size, ...</text>

  <line x1="210" y1="50" x2="325" y2="60" stroke="#8b949e" marker-end="url(afl1)"/>
  <defs><marker id="afl1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`Path` says where; `Files` does the actual reading, writing, and inspecting.

## 5. Runnable example

Scenario: a small project-scaffolding tool — the same file operations, evolved from basic whole-file reading and writing, through creating a directory structure and listing its contents, to streaming a log file line by line and inspecting its attributes.

### Level 1 — Basic

```java
import java.nio.file.*;
import java.util.*;

public class FilesBasic {
    public static void main(String[] args) throws Exception {
        Path tempFile = Files.createTempFile("demo", ".txt");

        Files.write(tempFile, "Hello, Files API!\nSecond line.".getBytes()); // Java 7's original write() overload
        byte[] rawBytes = Files.readAllBytes(tempFile);
        System.out.println("Read back:\n" + new String(rawBytes));

        List<String> lines = Files.readAllLines(tempFile, java.nio.charset.StandardCharsets.UTF_8);
        System.out.println("Line count: " + lines.size());

        Files.delete(tempFile);
        System.out.println("Deleted. Still exists? " + Files.exists(tempFile));
    }
}
```

**How to run:** `java FilesBasic.java`

`Files.write` and `Files.readAllBytes` handle a whole file's content as a single `byte[]`; `readAllLines` splits it into a `List<String>` instead. `Files.exists` after `Files.delete` confirms the deletion actually took effect.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.util.stream.*;

public class FilesDirectories {
    public static void main(String[] args) throws Exception {
        Path baseDir = Files.createTempDirectory("demo-project");
        Path subDir = baseDir.resolve("src/main/java"); // nested, non-existent path

        System.out.println("Exists before creation? " + Files.exists(subDir));
        Files.createDirectories(subDir); // creates ALL missing intermediate directories
        System.out.println("Exists after createDirectories? " + Files.exists(subDir));

        Files.write(baseDir.resolve("readme.txt"), "Project readme".getBytes());
        Files.write(subDir.resolve("Main.java"), "public class Main {}".getBytes());

        System.out.println("Top-level entries in baseDir:");
        try (Stream<Path> entries = Files.list(baseDir)) {
            entries.forEach(p -> System.out.println("  " + p.getFileName()));
        }
    }
}
```

**How to run:** `java FilesDirectories.java`

`Files.createDirectories` creates every missing directory along the path in one call — `src`, `src/main`, and `src/main/java` all get created together, even though none of them existed beforehand. `Files.list` returns a lazily-populated `Stream<Path>` of a directory's immediate entries — note it's wrapped in try-with-resources, since it holds an open directory handle that must be released.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.io.*;

public class FilesStreamingAttributes {
    public static void main(String[] args) throws Exception {
        Path logFile = Files.createTempFile("access-log", ".txt");

        // newBufferedWriter: stream lines out WITHOUT holding the whole file in memory
        try (BufferedWriter writer = Files.newBufferedWriter(logFile, StandardCharsets.UTF_8)) {
            for (int i = 1; i <= 3; i++) {
                writer.write("Log entry " + i);
                writer.newLine();
            }
        }

        System.out.println("File size in bytes: " + Files.size(logFile));
        System.out.println("Is regular file? " + Files.isRegularFile(logFile));
        System.out.println("Is readable? " + Files.isReadable(logFile));

        // newBufferedReader: stream lines in, one at a time
        try (BufferedReader reader = Files.newBufferedReader(logFile, StandardCharsets.UTF_8)) {
            String line;
            int count = 0;
            while ((line = reader.readLine()) != null) {
                count++;
                System.out.println("  Read: " + line);
            }
            System.out.println("Total lines streamed: " + count);
        }

        Files.delete(logFile);
    }
}
```

**How to run:** `java FilesStreamingAttributes.java`

`Files.newBufferedWriter`/`newBufferedReader` return standard `java.io` `BufferedWriter`/`BufferedReader` objects wired up to the given path — this streams content in and out a piece at a time, rather than requiring the whole file's content in memory at once as `readAllBytes`/`write` do, making it the better choice for large files.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `Files.createTempFile("access-log", ".txt")` creates a real, empty temporary file and returns its `Path`.

`Files.newBufferedWriter(logFile, StandardCharsets.UTF_8)` opens a streaming writer inside a try-with-resources block. The `for` loop runs three times, each iteration calling `writer.write("Log entry " + i)` followed by `writer.newLine()` — each of these writes goes to the file incrementally, rather than accumulating in memory as one large string first. When the try-with-resources block ends, the writer is flushed and closed automatically.

`Files.size(logFile)` reads the file's actual byte length from the file system — printed as a specific byte count. `Files.isRegularFile(logFile)` confirms it's an ordinary file (not a directory or special file), and `Files.isReadable(logFile)` confirms the current process has read permission — both return `true`.

`Files.newBufferedReader(logFile, StandardCharsets.UTF_8)` opens a streaming reader, again inside try-with-resources. The `while ((line = reader.readLine()) != null)` loop pulls one line at a time: `"Log entry 1"`, then `"Log entry 2"`, then `"Log entry 3"`, each printed with a `"  Read: "` prefix and incrementing `count`. When `readLine()` returns `null` (no more lines), the loop ends, and the final count (`3`) is printed. The reader is then closed automatically by try-with-resources.

Finally, `Files.delete(logFile)` removes the temporary file from disk.

Expected output:
```
File size in bytes: 36
Is regular file? true
Is readable? true
  Read: Log entry 1
  Read: Log entry 2
  Read: Log entry 3
Total lines streamed: 3
```

## 7. Gotchas & takeaways

> `Files.write`, `Files.readAllBytes`, and `Files.readAllLines` load or write the **entire** file's content in memory as one unit. For a genuinely large file (say, several gigabytes), this can exhaust available memory. Reach for `Files.newBufferedReader`/`newBufferedWriter` (or `Files.lines(path)`, a lazily-streamed `Stream<String>` added in Java 8) whenever file size isn't small and bounded.

- `Path` (previous tutorial) represents *where*; `Files` performs the actual operations *there* — reading, writing, checking, creating.
- Whole-file methods (`readAllBytes`, `readAllLines`, `write`) are convenient for small files but hold the entire content in memory; streaming methods (`newBufferedReader`/`newBufferedWriter`) handle arbitrarily large files a piece at a time.
- `Files.createDirectories` creates every missing intermediate directory along a path in one call — unlike the older `File.mkdir()`, which only creates the final directory and fails if its parent doesn't already exist.
- Methods like `Files.list` and `Files.walk` return a `Stream<Path>` backed by an open resource handle — always use them inside try-with-resources to ensure that handle is released.
- `Files` methods throw specific, informative exceptions (`NoSuchFileException`, `FileAlreadyExistsException`, `AccessDeniedException`, and so on) rather than the vague `boolean` failure signals common in the older `java.io.File` API.
