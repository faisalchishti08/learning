---
card: java
gi: 663
slug: filesystems-newfilesystem-additions
title: FileSystems.newFileSystem additions
---

## 1. What it is

**Java 13** added new overloads to `java.nio.file.FileSystems.newFileSystem()` — specifically `newFileSystem(Path, Map<String,?>)` and `newFileSystem(Path, Map<String,?>, ClassLoader)` — that let you open a filesystem (like the ZIP filesystem provider) directly from a `Path` without needing to first construct a `URI` with a `jar:` scheme. Before Java 13, opening a ZIP or JAR file as a browsable filesystem typically meant `FileSystems.newFileSystem(URI.create("jar:" + path.toUri()), env)` — a slightly awkward URI-construction dance. The new `Path`-based overloads let you write `FileSystems.newFileSystem(path, env)` directly, with the JDK inferring the appropriate provider from the path (its file extension or content), and they're friendlier to use with `Path`s obtained from anywhere, not just the default filesystem.

## 2. Why & when

Treating a ZIP or JAR file as its own miniature filesystem — so you can navigate its internal directory structure and read/write entries using ordinary `Path`/`Files` APIs instead of the low-level `ZipInputStream`/`ZipEntry` API — is a genuinely useful technique for tools that need to inspect or modify archive contents (build tools, packaging utilities, config-in-a-JAR readers). The pre-Java-13 URI-based API to do this was clunky boilerplate that most developers had to look up every time: converting a `Path` to a `URI`, prepending `"jar:"`, and passing that through. The `Path`-based overloads remove that ceremony entirely. Reach for `FileSystems.newFileSystem(Path, Map)` whenever you need to read or manipulate the contents of a ZIP/JAR archive using the familiar `Path`/`Files` API rather than stream-based ZIP APIs — it's particularly convenient for walking an archive's directory tree with `Files.walk` or copying files in and out with `Files.copy`.

## 3. Core concept

```java
import java.nio.file.*;
import java.util.Map;

Path zipPath = Path.of("archive.zip");

// Old style (pre-Java 13): had to build a jar: URI manually
try (FileSystem fs = FileSystems.newFileSystem(
        URI.create("jar:" + zipPath.toUri()), Map.of())) {
    // ...
}

// Java 13+: pass the Path directly
try (FileSystem fs = FileSystems.newFileSystem(zipPath, Map.of())) {
    Path root = fs.getPath("/");
    Files.walk(root).forEach(System.out::println);
}
```

Once opened, the returned `FileSystem` behaves like any other — `fs.getPath(...)`, `Files.walk`, `Files.newInputStream`, `Files.copy`, and friends all work against paths *inside* the archive, transparently reading and writing its internal ZIP structure.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A ZIP file on disk opened as its own FileSystem, exposing internal entries as navigable Paths">
  <rect x="10" y="20" width="180" height="130" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">archive.zip (on disk)</text>
  <text x="25" y="65" fill="#8b949e" font-size="9" font-family="monospace">[binary ZIP bytes]</text>

  <line x1="190" y1="85" x2="240" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#fs1)"/>
  <text x="215" y="75" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">newFileSystem(path, env)</text>

  <rect x="250" y="20" width="340" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="420" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">FileSystem view (navigable)</text>
  <text x="265" y="65" fill="#e6edf3" font-size="10" font-family="monospace">/ (root)</text>
  <text x="280" y="82" fill="#e6edf3" font-size="10" font-family="monospace">├── META-INF/</text>
  <text x="295" y="99" fill="#e6edf3" font-size="10" font-family="monospace">│    └── MANIFEST.MF</text>
  <text x="280" y="116" fill="#e6edf3" font-size="10" font-family="monospace">├── com/example/App.class</text>
  <text x="280" y="133" fill="#e6edf3" font-size="10" font-family="monospace">└── config.properties</text>

  <defs><marker id="fs1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

Instead of a stream of ZIP entries, you get a genuine `FileSystem` you can walk, query, and write to with the standard `Path`/`Files` API.

## 5. Runnable example

Scenario: creating a ZIP archive and then inspecting/modifying it as a filesystem — first opening it directly by `Path` and listing contents, then adding and reading back a file inside the archive, then a small utility that copies specific entries out of one archive into another using nothing but `Path`/`Files` calls.

### Level 1 — Basic

```java
// File: ZipFsBasic.java
import java.nio.file.*;
import java.util.Map;

public class ZipFsBasic {
    public static void main(String[] args) throws Exception {
        Path zipPath = Path.of("demo.zip");
        Files.deleteIfExists(zipPath);

        // Create a new zip filesystem (env map with "create" makes a fresh archive)
        try (FileSystem fs = FileSystems.newFileSystem(zipPath, Map.of("create", "true"))) {
            Path hello = fs.getPath("/hello.txt");
            Files.writeString(hello, "Hello from inside a zip!");
        }

        // Reopen it (no "create") and list what's inside, using the Path-based overload
        try (FileSystem fs = FileSystems.newFileSystem(zipPath, Map.of())) {
            Files.walk(fs.getPath("/")).forEach(System.out::println);
        }
    }
}
```

**How to run:** `java ZipFsBasic.java` (creates `demo.zip` in the current directory).

Expected output:
```
/
/hello.txt
```

### Level 2 — Intermediate

```java
// File: ZipFsReadWrite.java
import java.nio.file.*;
import java.util.Map;

public class ZipFsReadWrite {
    public static void main(String[] args) throws Exception {
        Path zipPath = Path.of("config-bundle.zip");
        Files.deleteIfExists(zipPath);

        try (FileSystem fs = FileSystems.newFileSystem(zipPath, Map.of("create", "true"))) {
            Files.createDirectory(fs.getPath("/config"));
            Files.writeString(fs.getPath("/config/app.properties"), "env=production\ndebug=false\n");
            Files.writeString(fs.getPath("/config/logging.properties"), "level=INFO\n");
        }

        // Reopen and read a specific entry directly, plus modify one in place.
        try (FileSystem fs = FileSystems.newFileSystem(zipPath, Map.of())) {
            String appConfig = Files.readString(fs.getPath("/config/app.properties"));
            System.out.println("app.properties contains:\n" + appConfig);

            // Modify an entry in place — the archive on disk is updated when the fs closes.
            Files.writeString(fs.getPath("/config/logging.properties"), "level=DEBUG\n");
        }

        try (FileSystem fs = FileSystems.newFileSystem(zipPath, Map.of())) {
            System.out.println("logging.properties now: "
                + Files.readString(fs.getPath("/config/logging.properties")));
        }
    }
}
```

**How to run:** `java ZipFsReadWrite.java`

Expected output:
```
app.properties contains:
env=production
debug=false

logging.properties now: level=DEBUG
```

Writing to a path inside an already-open ZIP filesystem modifies the entry in place, and the change is persisted to the underlying `.zip` file on disk once that `FileSystem` is closed — no manual re-zipping logic needed.

### Level 3 — Advanced

```java
// File: ZipFsSelectiveCopy.java
import java.nio.file.*;
import java.util.Map;
import java.util.stream.Stream;

public class ZipFsSelectiveCopy {
    static void copyMatching(Path sourceZip, Path destZip, String suffix) throws Exception {
        Files.deleteIfExists(destZip);
        try (FileSystem src = FileSystems.newFileSystem(sourceZip, Map.of());
             FileSystem dst = FileSystems.newFileSystem(destZip, Map.of("create", "true"))) {

            try (Stream<Path> walk = Files.walk(src.getPath("/"))) {
                walk.filter(p -> p.toString().endsWith(suffix)).forEach(entry -> {
                    try {
                        Path target = dst.getPath(entry.toString());
                        if (target.getParent() != null) {
                            Files.createDirectories(target.getParent());
                        }
                        Files.copy(entry, target, StandardCopyOption.REPLACE_EXISTING);
                        System.out.println("Copied: " + entry);
                    } catch (Exception e) {
                        throw new RuntimeException(e);
                    }
                });
            }
        }
    }

    public static void main(String[] args) throws Exception {
        Path source = Path.of("source-bundle.zip");
        Files.deleteIfExists(source);
        try (FileSystem fs = FileSystems.newFileSystem(source, Map.of("create", "true"))) {
            Files.createDirectory(fs.getPath("/data"));
            Files.writeString(fs.getPath("/data/report.txt"), "quarterly numbers");
            Files.writeString(fs.getPath("/data/notes.md"), "# notes");
            Files.writeString(fs.getPath("/data/settings.json"), "{}");
        }

        copyMatching(source, Path.of("txt-only.zip"), ".txt");

        try (FileSystem fs = FileSystems.newFileSystem(Path.of("txt-only.zip"), Map.of())) {
            System.out.println("\nContents of txt-only.zip:");
            Files.walk(fs.getPath("/")).forEach(System.out::println);
        }
    }
}
```

**How to run:** `java ZipFsSelectiveCopy.java`

Expected output:
```
Copied: /data/report.txt

Contents of txt-only.zip:
/
/data
/data/report.txt
```

Level 3 opens **two** ZIP filesystems simultaneously — a source and a destination — and copies only `.txt`-suffixed entries between them using plain `Files.walk`, `Files.copy`, and `Files.createDirectories`, exactly as if both archives were ordinary directory trees, with no ZIP-specific API beyond the initial `newFileSystem(Path, Map)` calls.

## 6. Walkthrough

1. `main` first builds `source-bundle.zip` by opening it with `FileSystems.newFileSystem(source, Map.of("create", "true"))` — the `"create"` entry in the environment map tells the ZIP filesystem provider to create a brand-new, empty archive rather than expecting an existing one. Inside the try-with-resources block, a `/data` directory and three files are written directly into the archive via `Files.createDirectory` and `Files.writeString`.
2. When that try-with-resources block ends, the `FileSystem` closes, which flushes all the writes and finalizes `source-bundle.zip` as a valid ZIP file on disk.
3. `main` calls `copyMatching(source, Path.of("txt-only.zip"), ".txt")`. Inside, `Files.deleteIfExists(destZip)` clears any stale file from a previous run, then two filesystems are opened at once: `src` (the existing `source-bundle.zip`, opened for reading with `Map.of()` — no `"create"` needed since it already exists) and `dst` (`txt-only.zip`, opened with `"create", "true"` to start fresh).
4. `Files.walk(src.getPath("/"))` recursively streams every path inside the source archive — the root, `/data`, `/data/report.txt`, `/data/notes.md`, `/data/settings.json` — in a depth-first traversal order.
5. The `.filter(p -> p.toString().endsWith(suffix))` step keeps only paths ending in `".txt"`, which matches exactly `/data/report.txt` and excludes the root, the `/data` directory itself, and the `.md`/`.json` files.
6. For that one matching entry, `dst.getPath(entry.toString())` builds the *equivalent path string* but resolved against the **destination** filesystem — `entry.toString()` gives `"/data/report.txt"`, and `dst.getPath("/data/report.txt")` creates a `Path` object rooted in `dst`, not `src`, even though the string looks identical; `Path`s from different filesystems are not directly interchangeable, which is why this string round-trip is necessary.
7. `Files.createDirectories(target.getParent())` ensures `/data` exists inside `dst` before writing into it (ZIP filesystems, like most filesystems, need parent directories to exist before you can create a file inside them), and `Files.copy(entry, target, StandardCopyOption.REPLACE_EXISTING)` streams the actual file content from the source archive entry into the new destination archive entry — this cross-filesystem copy works because `Files.copy` operates on the generic `Path`/`Files` abstraction, unaware or uncaring that the two paths happen to live inside two different ZIP files.
8. After the walk finishes and both filesystems close (flushing `txt-only.zip` to disk), `main` reopens `txt-only.zip` fresh and walks it, printing `/`, `/data`, and `/data/report.txt` — confirming only the `.txt` file (and the directory structure needed to hold it) made it into the filtered copy.

```
source-bundle.zip: /data/report.txt, /data/notes.md, /data/settings.json
        │ Files.walk + filter(".txt")
        ▼
   /data/report.txt  ──copy──►  txt-only.zip: /data/report.txt
```

## 7. Gotchas & takeaways

> `Files.copy(entry, target, ...)` between two **different** open `FileSystem` instances (as in Level 3) works, but `entry` and `target` must each be constructed relative to their *own* filesystem — you cannot pass a `Path` from `src` directly into a method expecting a path already resolved against `dst`. This is why `copyMatching` deliberately round-trips through `entry.toString()` and `dst.getPath(...)` rather than trying to reuse `entry` directly against the destination.

- The `Path`-based `FileSystems.newFileSystem(Path, Map)` overloads (Java 13+) remove the need to manually construct a `jar:` URI — the provider is inferred from the path.
- Pass `Map.of("create", "true")` in the environment map to create a brand-new archive; omit it (or use `Map.of()`) to open an existing one.
- Always close the `FileSystem` (via try-with-resources) to ensure writes are flushed and the ZIP structure is finalized correctly on disk.
- Once open, a ZIP filesystem behaves like any other `FileSystem` — `Files.walk`, `Files.copy`, `Files.createDirectories`, and `Files.writeString`/`Files.readString` all work against paths inside it, with no ZIP-specific API needed beyond opening it.
- You can have multiple ZIP filesystems (and the default filesystem) open simultaneously, enabling cross-archive operations like the selective copy in Level 3.
