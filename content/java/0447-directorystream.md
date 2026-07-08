---
card: java
gi: 447
slug: directorystream
title: DirectoryStream
---

## 1. What it is

`DirectoryStream<Path>`, obtained via `Files.newDirectoryStream(dir)` (or the overloads accepting a glob pattern or a custom filter), lets you iterate a directory's **immediate** entries — one level deep, not recursive — as `Path` objects. It implements `Iterable<Path>`, so a `for-each` loop works directly on it, and it also implements `Closeable`, since it holds an open directory handle that must be released, making it a natural fit for try-with-resources.

## 2. Why & when

`java.io.File.list()` (the pre-Java-7 way to list a directory) returns a full `String[]` array of every entry's name, all loaded at once — for a directory with an enormous number of entries, this means holding every single name in memory simultaneously before you can even start processing them. `DirectoryStream` instead provides entries lazily, one at a time, as the iteration proceeds, without ever materializing the complete list up front — better for directories that might be very large. It also supports filtering *during* the listing itself (a glob pattern, or a custom `Filter<Path>`), rather than listing everything and filtering afterward.

You reach for `DirectoryStream` any time you need to enumerate a directory's immediate contents — listing files matching a pattern, processing entries one at a time without holding them all in memory, or filtering based on custom logic beyond what a simple glob pattern can express.

## 3. Core concept

```java
import java.nio.file.*;

// All entries, one level deep, lazily provided
try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir)) {
    for (Path entry : stream) {
        System.out.println(entry.getFileName());
    }
}

// Filtered by a glob pattern
try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.txt")) {
    for (Path entry : stream) { /* only .txt files */ }
}

// Filtered by custom logic
DirectoryStream.Filter<Path> customFilter = entry -> Files.size(entry) > 1000;
try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, customFilter)) {
    for (Path entry : stream) { /* only entries matching customFilter.accept(entry) */ }
}
```

`DirectoryStream` only ever yields the directory's **direct** children — no recursion into subdirectories. For recursive traversal, use `Files.walk` or `Files.walkFileTree` (covered in the previous tutorial).

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DirectoryStream lazily yields a directory's immediate entries one at a time, optionally filtered by a glob pattern or custom filter, without ever holding a full list of every entry in memory at once">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="140" height="80" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">directory</text>
  <text x="100" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a.txt</text>
  <text x="100" y="82" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">b.png</text>
  <text x="100" y="96" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">c.txt</text>

  <rect x="250" y="45" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="325" y="67" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">optional filter/glob</text>
  <line x1="170" y1="70" x2="245" y2="62" stroke="#8b949e" marker-end="url(ads1)"/>

  <rect x="460" y="45" width="150" height="34" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="535" y="67" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">yielded one at a time</text>
  <line x1="400" y1="62" x2="455" y2="62" stroke="#8b949e" marker-end="url(ads1)"/>

  <defs><marker id="ads1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Entries flow through an optional filter and are handed to the caller lazily, one at a time, never all at once.

## 5. Runnable example

Scenario: listing files in a mixed-content directory — the same directory, evolved from a basic unfiltered listing, through a glob-pattern filter matching a file extension, to a custom filter combining multiple conditions a simple glob can't express.

### Level 1 — Basic

```java
import java.nio.file.*;

public class DirStreamBasic {
    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("listing-demo");
        Files.write(dir.resolve("report.txt"), "data".getBytes());
        Files.write(dir.resolve("image.png"), "fake png".getBytes());
        Files.write(dir.resolve("notes.txt"), "notes".getBytes());

        System.out.println("All entries:");
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir)) {
            for (Path entry : stream) {
                System.out.println("  " + entry.getFileName());
            }
        }

        Files.walk(dir).sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
            try { Files.delete(p); } catch (Exception e) { throw new RuntimeException(e); }
        });
    }
}
```

**How to run:** `java DirStreamBasic.java`

`Files.newDirectoryStream(dir)` with no filter argument yields every immediate entry in `dir` — all three files show up, regardless of extension. (Entry order reflects whatever the underlying file system returns, which is not guaranteed by the API to follow any particular ordering.)

### Level 2 — Intermediate

```java
import java.nio.file.*;

public class DirStreamGlob {
    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("listing-demo");
        Files.write(dir.resolve("report.txt"), "data".getBytes());
        Files.write(dir.resolve("image.png"), "fake png".getBytes());
        Files.write(dir.resolve("notes.txt"), "notes".getBytes());

        System.out.println("Only *.txt entries:");
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, "*.txt")) {
            for (Path entry : stream) {
                System.out.println("  " + entry.getFileName());
            }
        }

        Files.walk(dir).sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
            try { Files.delete(p); } catch (Exception e) { throw new RuntimeException(e); }
        });
    }
}
```

**How to run:** `java DirStreamGlob.java`

The `"*.txt"` glob argument filters *during* the listing — `image.png` is skipped entirely, without ever being handed to your code at all, rather than being listed and then discarded afterward.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.io.IOException;

public class DirStreamCustomFilter {
    public static void main(String[] args) throws Exception {
        Path dir = Files.createTempDirectory("listing-demo");
        Files.write(dir.resolve("small.txt"), "hi".getBytes());               // 2 bytes
        Files.write(dir.resolve("large.txt"), "this is a much longer file".getBytes()); // 26 bytes
        Files.write(dir.resolve("large.png"), "also a long fake image file".getBytes()); // not .txt

        // Custom filter: files larger than 10 bytes AND ending in ".txt" -- logic beyond what a simple glob can express
        DirectoryStream.Filter<Path> largeTextFiles = entry ->
            entry.toString().endsWith(".txt") && Files.size(entry) > 10;

        System.out.println("Large .txt files:");
        try (DirectoryStream<Path> stream = Files.newDirectoryStream(dir, largeTextFiles)) {
            for (Path entry : stream) {
                System.out.println("  " + entry.getFileName() + " (" + Files.size(entry) + " bytes)");
            }
        }

        Files.walk(dir).sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
            try { Files.delete(p); } catch (IOException e) { throw new RuntimeException(e); }
        });
    }
}
```

**How to run:** `java DirStreamCustomFilter.java`

`DirectoryStream.Filter<Path>` is a functional interface with one method, `accept(Path entry)` — a lambda expressing "ends with `.txt` **and** is larger than 10 bytes" combines two conditions a glob pattern alone couldn't express. Of the three files, only `large.txt` satisfies both: `small.txt` is too small, and `large.png` doesn't match the extension.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Three files are created: `small.txt` (2 bytes), `large.txt` (26 bytes), and `large.png` (also long, but a different extension).

`largeTextFiles` is defined as a lambda implementing `DirectoryStream.Filter<Path>` — its single method, `accept(Path entry)`, is what `Files.newDirectoryStream(dir, largeTextFiles)` will call once per directory entry to decide whether that entry should be yielded.

`Files.newDirectoryStream(dir, largeTextFiles)` opens the directory and, as the `for-each` loop iterates, evaluates `accept` on each entry in turn. For `small.txt`: `entry.toString().endsWith(".txt")` is `true`, but `Files.size(entry) > 10` is `false` (it's only 2 bytes) — the overall condition (`&&`) is `false`, so `small.txt` is filtered out and never yielded to the loop body. For `large.png`: `entry.toString().endsWith(".txt")` is `false` immediately — short-circuiting the `&&`, so `Files.size` isn't even checked — filtered out. For `large.txt`: both conditions are `true` (`.txt` extension, and its size of 26 bytes exceeds 10) — this entry passes the filter and is yielded to the loop, which prints `"  large.txt (26 bytes)"`.

Expected output:
```
Large .txt files:
  large.txt (26 bytes)
```

## 7. Gotchas & takeaways

> `DirectoryStream` only yields a directory's **immediate** entries — it never recurses into subdirectories, even if one of the entries happens to be a directory itself. If you need to walk an entire tree, use `Files.walk` or `Files.walkFileTree` (the previous tutorial) instead; using `DirectoryStream` where recursive traversal was actually needed is a common mistake that silently produces an incomplete listing.

- `DirectoryStream<Path>` lazily provides a directory's immediate entries, one at a time, without loading the complete list into memory up front.
- It implements both `Iterable<Path>` (for a natural `for-each` loop) and `Closeable` (since it holds an open directory handle) — always use it inside try-with-resources.
- `Files.newDirectoryStream(dir, globPattern)` filters entries by a glob pattern *during* the listing, more efficient than listing everything and filtering afterward.
- `Files.newDirectoryStream(dir, filter)` accepts a custom `DirectoryStream.Filter<Path>` — a functional interface — for filtering logic beyond what a simple glob pattern can express.
- It never traverses recursively — only the directory's direct children are yielded, regardless of whether any of them are themselves directories.
