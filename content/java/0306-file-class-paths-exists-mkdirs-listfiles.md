---
card: java
gi: 306
slug: file-class-paths-exists-mkdirs-listfiles
title: File class (paths, exists, mkdirs, listFiles)
---

## 1. What it is

`java.io.File` represents an abstract path to a file or directory — it does **not** represent the file's actual content, only its location and metadata (whether it exists, its size, whether it's a directory, its parent, and so on). It also provides operations to query and manipulate the filesystem: checking existence, creating directories, listing directory contents, and deleting.

```java
import java.io.File;

public class FileDemo {
    public static void main(String[] args) {
        File file = new File("example.txt");
        System.out.println("Exists: " + file.exists());
        System.out.println("Absolute path: " + file.getAbsolutePath());
        System.out.println("Is directory: " + file.isDirectory());
    }
}
```

`new File("example.txt")` creates a `File` object representing that path — this line performs **no** filesystem I/O at all; it's purely an in-memory representation of a path, and the file it names may or may not actually exist.

## 2. Why & when

Before `java.nio.file.Path`/`Files` arrived in Java 7, `File` was the only way to represent and manipulate filesystem paths — checking whether something exists, creating directories, listing a directory's contents, or deleting files.

- **Path representation** — `File` wraps a path string with convenience methods (`getName`, `getParent`, `getAbsolutePath`) for decomposing and normalizing it.
- **Filesystem queries** — `exists()`, `isFile()`, `isDirectory()`, `length()`, `lastModified()` let code inspect the filesystem without opening a stream.
- **Directory operations** — `mkdir()`/`mkdirs()` create directories (the latter also creating any missing parent directories); `listFiles()` enumerates a directory's contents.
- **Still widely used** — many older APIs (and `FileInputStream`/`FileOutputStream`'s constructors) accept a `File`, so it remains relevant even though newer code often prefers `java.nio.file.Path`.

For new code, `java.nio.file.Path` and `java.nio.file.Files` (covered separately) offer a richer, more consistent API — better exception handling (specific exceptions instead of `File`'s frequent silent `false`/`null` returns), symbolic link support, and more. `File` remains perfectly usable and is still what you'll see constructing `FileInputStream`/`FileOutputStream`/`FileReader`/`FileWriter`.

## 3. Core concept

```java
import java.io.File;

public class FileCore {
    public static void main(String[] args) {
        File dir = new File("output/reports");
        boolean created = dir.mkdirs(); // creates "output" AND "output/reports" if missing
        System.out.println("Created: " + created);
        System.out.println("Exists now: " + dir.exists());

        File[] contents = new File("output").listFiles();
        System.out.println("Entries in 'output': " + (contents == null ? 0 : contents.length));
    }
}
```

`mkdirs()` (plural) creates the entire directory chain, including any missing intermediate directories (here, `output` itself if it didn't already exist), unlike `mkdir()` (singular), which fails if the immediate parent doesn't already exist.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A File object represents a path which may or may not exist on the actual filesystem, exists checks reality">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="240" height="50" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="monospace">new File(path)</text>
  <text x="150" y="95" fill="#8b949e" font-size="9" text-anchor="middle">in-memory only, no I/O yet</text>

  <line x1="270" y1="55" x2="330" y2="55" stroke="#3fb950" stroke-width="2" marker-end="url(#f1)"/>
  <text x="300" y="45" fill="#3fb950" font-size="9" text-anchor="middle">exists()</text>

  <rect x="335" y="30" width="230" height="50" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="450" y="58" fill="#e6edf3" font-size="11" text-anchor="middle">real filesystem</text>
  <text x="450" y="95" fill="#8b949e" font-size="9" text-anchor="middle">may or may not have this path</text>
  <defs>
    <marker id="f1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

Constructing a `File` is free and does not touch disk; every query method (`exists`, `listFiles`, etc.) is the point where real filesystem I/O happens.

## 5. Runnable example

Scenario: a small directory-organizing utility, evolved from a basic existence check into a directory creator, then into a recursive directory-size calculator that walks a tree of files.

### Level 1 — Basic

```java
import java.io.File;

public class FileBasic {
    public static void main(String[] args) {
        File file = new File("myfile.txt");

        if (!file.exists()) {
            System.out.println(file.getName() + " does not exist yet.");
        } else {
            System.out.println(file.getName() + " exists, size: " + file.length() + " bytes");
        }
    }
}
```

**How to run:** `java FileBasic.java`

Checks whether a named file exists before deciding what to report — the most basic use of `File` as a filesystem query object.

### Level 2 — Intermediate

Same idea, now creating a nested output directory structure and writing a file into it, demonstrating `mkdirs()` and combining `File` with `FileWriter`.

```java
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class FileIntermediate {
    public static void main(String[] args) throws IOException {
        File dir = new File("output/2026/07");
        boolean created = dir.mkdirs();
        System.out.println("Directory created: " + created + " (" + dir.getAbsolutePath() + ")");

        File reportFile = new File(dir, "report.txt"); // File(parent, childName) constructor
        try (FileWriter writer = new FileWriter(reportFile)) {
            writer.write("Monthly report contents");
        }

        System.out.println("Report exists: " + reportFile.exists() + ", size: " + reportFile.length());
    }
}
```

**How to run:** `java FileIntermediate.java`

`new File(dir, "report.txt")` builds a path by joining a parent `File` and a child name, correctly inserting the platform's path separator — cleaner and more portable than manually concatenating strings with `/` or `\`.

### Level 3 — Advanced

Same directory tree, now with a recursive method that walks an entire directory structure and sums the total size of all files within it, handling both files and nested subdirectories.

```java
import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

public class FileAdvanced {
    static long totalSize(File fileOrDir) {
        if (fileOrDir.isFile()) {
            return fileOrDir.length();
        }
        long total = 0;
        File[] children = fileOrDir.listFiles();
        if (children != null) {
            for (File child : children) {
                total += totalSize(child); // recurse into subdirectories
            }
        }
        return total;
    }

    public static void main(String[] args) throws IOException {
        File root = new File("output/2026/07");
        root.mkdirs();

        try (FileWriter w1 = new FileWriter(new File(root, "report.txt"))) {
            w1.write("Report contents here.");
        }
        File subDir = new File(root, "archive");
        subDir.mkdirs();
        try (FileWriter w2 = new FileWriter(new File(subDir, "old-report.txt"))) {
            w2.write("Old report, shorter.");
        }

        long size = totalSize(new File("output"));
        System.out.println("Total size under 'output': " + size + " bytes");
    }
}
```

**How to run:** `java FileAdvanced.java`

`totalSize` checks `isFile()` first — if true, it's a leaf, and `length()` gives its byte size directly; otherwise it's a directory, and `listFiles()` returns its immediate children (files and subdirectories alike), each recursively passed back into `totalSize`, so nested subdirectories (like `archive`) are correctly walked and included in the total.

## 6. Walkthrough

Trace `totalSize(new File("output"))` in `FileAdvanced.main` step by step.

**Initial call, `fileOrDir = "output"`.** `isFile()` is `false` (it's a directory), so the method proceeds to the directory branch. `listFiles()` returns the immediate children of `output` — in this tree, that's just `"output/2026"` (a directory).

**Recursing into `"output/2026"`.** Again a directory; `listFiles()` returns `["output/2026/07"]`.

**Recursing into `"output/2026/07"`.** Again a directory; `listFiles()` returns two entries: `"output/2026/07/report.txt"` (a file) and `"output/2026/07/archive"` (a directory) — the order returned by `listFiles()` is not guaranteed, but both are visited.

**Visiting `"report.txt"`.** `isFile()` is `true`, so `totalSize` returns `report.txt.length()` directly — the byte length of `"Report contents here."`, which is 22 bytes.

**Visiting `"archive"`.** A directory; `listFiles()` returns `["output/2026/07/archive/old-report.txt"]`.

**Visiting `"old-report.txt"`.** `isFile()` is `true`; returns its length — the byte length of `"Old report, shorter."`, which is 20 bytes.

**Unwinding the recursion.** `archive`'s total is `20` (just its one file). `"07"`'s total is `22` (report.txt) `+ 20` (from archive) `= 42`. `"2026"`'s total is `42` (passed straight up, since it has only the one child directory). `"output"`'s total is `42` (passed straight up as well).

```
output/
  2026/
    07/
      report.txt        (22 bytes)
      archive/
        old-report.txt  (20 bytes)

totalSize("output")
  -> totalSize("2026") -> totalSize("07")
       -> totalSize("report.txt") = 22           (isFile: base case)
       -> totalSize("archive") -> totalSize("old-report.txt") = 20   (isFile: base case)
       -> 07's total = 22 + 20 = 42
  -> 2026's total = 42
-> output's total = 42
```

**Output:**
```
Total size under 'output': 42 bytes
```

## 7. Gotchas & takeaways

> `listFiles()` returns `null` (not an empty array) if the `File` isn't actually a directory, or if an I/O error occurs while listing it (e.g. a permissions problem) — code that calls `.length` on the result without a null check, as a naive version of `totalSize` might, will throw `NullPointerException`. The example above guards this explicitly with `if (children != null)`.

> Most `File` methods report failure by returning `false` or `null` rather than throwing an exception — `mkdirs()` returning `false` could mean the directory already existed, or that creation genuinely failed due to a permissions problem; `File` alone can't tell you which. `java.nio.file.Files`'s methods generally throw specific exceptions instead, giving clearer diagnostics.

- `File` represents a path (which may or may not exist), not the file's content — constructing one performs no I/O.
- `exists()`, `isFile()`, `isDirectory()`, `length()` query the real filesystem at the moment they're called.
- `mkdirs()` creates the full directory chain including missing parents; `mkdir()` only creates the final directory and fails if its parent is missing.
- `listFiles()` returns `null` (not an empty array) when the target isn't a directory or listing fails — always null-check before iterating.
