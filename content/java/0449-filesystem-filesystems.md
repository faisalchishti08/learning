---
card: java
gi: 449
slug: filesystem-filesystems
title: FileSystem & FileSystems
---

## 1. What it is

`FileSystem` (an interface) represents an entire file-system-like storage — most commonly the actual, local file system of the machine you're running on, but not necessarily. `FileSystems` (the factory class) provides `getDefault()` for the ordinary local file system, and `newFileSystem(uri, env)` for connecting to *other* kinds of file-system-like providers — most notably the built-in ZIP/JAR file system provider, which lets you treat a `.zip` or `.jar` file as its own self-contained, navigable file system, complete with its own `Path` objects, directories, and read/write operations.

## 2. Why & when

Before this abstraction, working with the contents of a ZIP or JAR file meant using a completely different API (`java.util.zip.ZipFile`/`ZipEntry`) with its own, unrelated method names and patterns — you couldn't reuse the same `Path`/`Files` code you'd write for ordinary disk files. `FileSystem`'s pluggable design means the ZIP file system provider (bundled with the JDK) exposes a ZIP archive's contents through the *exact same* `Path`/`Files` API used for real disk files — `Files.write`, `Files.walk`, `Files.copy` all work identically, whether the underlying storage is your actual disk or the inside of a `.zip` archive.

You reach for `FileSystems.newFileSystem` with the ZIP provider whenever you need to read from or write into a ZIP/JAR archive's contents using ordinary `Path`/`Files` code — packaging build outputs, inspecting or modifying a JAR's contents, or building a simple archive-based storage format — without learning a separate, ZIP-specific API.

## 3. Core concept

```java
import java.nio.file.*;
import java.net.URI;
import java.util.Map;

FileSystem defaultFs = FileSystems.getDefault(); // the ordinary local disk file system

// Open (or create) a ZIP file as its OWN FileSystem
URI zipUri = URI.create("jar:" + Paths.get("archive.zip").toUri());
try (FileSystem zipFs = FileSystems.newFileSystem(zipUri, Map.of("create", "true"))) {
    Path entry = zipFs.getPath("/hello.txt");
    Files.write(entry, "content".getBytes()); // ordinary Files API, but writing INSIDE the zip
}
```

Everything you already know about `Path` and `Files` still applies — `zipFs.getPath(...)` produces a `Path` rooted in the archive's own internal structure, and standard `Files` methods operate on it exactly as they would on a real disk path.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="FileSystems.getDefault gives the local disk's FileSystem; FileSystems.newFileSystem can instead open a ZIP archive as its own FileSystem, and the same Path and Files API works identically against either one">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="220" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="140" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">FileSystems.getDefault()</text>
  <rect x="30" y="90" width="220" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="140" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">FileSystems.newFileSystem("jar:...")</text>

  <rect x="400" y="60" width="200" height="40" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="500" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">SAME Path / Files API</text>

  <line x1="250" y1="50" x2="395" y2="75" stroke="#8b949e" marker-end="url(afs1)"/>
  <line x1="250" y1="110" x2="395" y2="90" stroke="#8b949e" marker-end="url(afs1)"/>
  <defs><marker id="afs1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Two entirely different kinds of storage, driven through one identical `Path`/`Files` programming interface.

## 5. Runnable example

Scenario: packaging and reading files inside a ZIP archive as if it were an ordinary directory — the same archive, evolved from inspecting the ordinary default file system, through creating a brand-new ZIP archive and writing a file into it, to walking the archive's full contents and extracting a file back out to the real disk.

### Level 1 — Basic

```java
import java.nio.file.*;

public class FileSystemDefault {
    public static void main(String[] args) {
        FileSystem fs = FileSystems.getDefault();

        System.out.println("Separator: \"" + fs.getSeparator() + "\"");
        System.out.println("Is open? " + fs.isOpen());
        System.out.println("Is read-only? " + fs.isReadOnly());

        System.out.println("Root directories:");
        for (Path root : fs.getRootDirectories()) {
            System.out.println("  " + root);
        }
    }
}
```

**How to run:** `java FileSystemDefault.java`

`FileSystems.getDefault()` returns the `FileSystem` representing the machine's actual local storage — `getSeparator()` reports the platform's path separator (`/` on Unix-like systems, `\` on Windows), and `getRootDirectories()` lists the file system's top-level roots.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.util.*;
import java.net.URI;

public class ZipFileSystem {
    public static void main(String[] args) throws Exception {
        Path zipPath = Files.createTempFile("archive", ".zip");
        Files.delete(zipPath); // newFileSystem with create=true needs the path to NOT already exist

        URI zipUri = URI.create("jar:" + zipPath.toUri());
        Map<String, String> env = Map.of("create", "true");

        try (FileSystem zipFs = FileSystems.newFileSystem(zipUri, env)) {
            Path entry = zipFs.getPath("/hello.txt");
            Files.write(entry, "Hello from inside a zip!".getBytes());
            System.out.println("Wrote a file INSIDE the zip archive's own file system");
        }

        System.out.println("Zip file size on disk: " + Files.size(zipPath) + " bytes");

        // Reopen (read-only this time) to prove the content genuinely persisted in the archive
        try (FileSystem zipFs = FileSystems.newFileSystem(zipUri, Map.of())) {
            Path entry = zipFs.getPath("/hello.txt");
            System.out.println("Read back: " + new String(Files.readAllBytes(entry)));
        }

        Files.delete(zipPath);
    }
}
```

**How to run:** `java ZipFileSystem.java`

`FileSystems.newFileSystem(zipUri, Map.of("create", "true"))` creates a brand-new ZIP archive and opens it as its own `FileSystem` — `zipFs.getPath("/hello.txt")` gives a `Path` *inside* that archive, and `Files.write` works exactly as it would for a real file, except the bytes actually land inside the ZIP's internal structure. Reopening the same archive afterward (without `"create"`) and reading the file back confirms the content genuinely persisted in the archive on disk.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.util.*;
import java.net.URI;
import java.util.stream.*;

public class ZipFileSystemAdvanced {
    public static void main(String[] args) throws Exception {
        Path zipPath = Files.createTempFile("archive2", ".zip");
        Files.delete(zipPath);
        URI zipUri = URI.create("jar:" + zipPath.toUri());

        try (FileSystem zipFs = FileSystems.newFileSystem(zipUri, Map.of("create", "true"))) {
            Files.createDirectory(zipFs.getPath("/docs"));
            Files.write(zipFs.getPath("/readme.txt"), "top-level readme".getBytes());
            Files.write(zipFs.getPath("/docs/guide.txt"), "user guide content".getBytes());

            System.out.println("Entries inside the zip file system:");
            try (Stream<Path> walk = Files.walk(zipFs.getPath("/"))) {
                walk.filter(Files::isRegularFile)
                    .forEach(p -> System.out.println("  " + p));
            }

            // Copy a file OUT of the zip filesystem into the DEFAULT filesystem -- crossing FileSystem providers
            Path extractedFile = Files.createTempFile("extracted-guide", ".txt");
            Files.copy(zipFs.getPath("/docs/guide.txt"), extractedFile, StandardCopyOption.REPLACE_EXISTING);
            System.out.println("Extracted content: " + new String(Files.readAllBytes(extractedFile)));
            Files.delete(extractedFile);
        }

        Files.delete(zipPath);
    }
}
```

**How to run:** `java ZipFileSystemAdvanced.java`

`Files.walk(zipFs.getPath("/"))` recursively traverses the archive's internal directory structure exactly like it would a real directory tree. `Files.copy(zipFs.getPath(...), extractedFile, ...)` copies a file from **inside** the ZIP `FileSystem` to a path on the **default** `FileSystem` — the same `Files.copy` call transparently bridges two entirely different `FileSystem` providers.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. A temporary path is chosen for the new archive, then immediately deleted (since `newFileSystem` with `"create": "true"` requires the target not to already exist), and `zipUri` is built as a `"jar:"`-prefixed URI pointing at that path.

`FileSystems.newFileSystem(zipUri, Map.of("create", "true"))` creates and opens a brand-new, empty ZIP archive as `zipFs`. `Files.createDirectory(zipFs.getPath("/docs"))` creates a `docs` directory *inside* the archive. `Files.write(zipFs.getPath("/readme.txt"), ...)` writes a top-level file, and `Files.write(zipFs.getPath("/docs/guide.txt"), ...)` writes a file inside the `docs` directory — both calls are the exact same `Files.write` you'd use for real disk files, just operating against paths rooted in the ZIP's own `FileSystem`.

`Files.walk(zipFs.getPath("/"))` starts a recursive traversal from the archive's root, visiting every entry (the root itself, `docs`, `readme.txt`, and `docs/guide.txt`). `.filter(Files::isRegularFile)` keeps only actual files (excluding directories), so the printed list shows `/readme.txt` and `/docs/guide.txt` — both files that were just written, confirmed present inside the archive's structure.

A new temporary file, `extractedFile`, is created on the **default** file system (ordinary disk). `Files.copy(zipFs.getPath("/docs/guide.txt"), extractedFile, StandardCopyOption.REPLACE_EXISTING)` copies the content of the file living inside the ZIP archive out to this ordinary disk location — a single `copy` call bridging two entirely different `FileSystem` implementations transparently. `Files.readAllBytes(extractedFile)` then confirms the content made it across correctly: `"user guide content"`.

Expected output:
```
Entries inside the zip file system:
  /readme.txt
  /docs/guide.txt
Extracted content: user guide content
```

## 7. Gotchas & takeaways

> `FileSystems.newFileSystem(uri, Map.of("create", "true"))` requires that the target ZIP file **does not already exist** — attempting to create one where a file is already present throws `FileAlreadyExistsException`. To open an *existing* ZIP file's contents (rather than create a new archive), simply omit the `"create"` option entirely (as the read-back step in Level 2 does), rather than passing `"create": "false"` or similar.

- `FileSystems.getDefault()` gives the ordinary local disk's `FileSystem`; `FileSystems.newFileSystem(uri, env)` can open entirely different kinds of file-system-like storage, most notably ZIP/JAR archives via the JDK's built-in provider.
- The exact same `Path`/`Files` API works identically regardless of which `FileSystem` a `Path` belongs to — no separate ZIP-specific methods are needed for reading, writing, or walking archive contents.
- `zipFs.getPath(...)` produces a `Path` rooted in the archive's own internal structure, distinct from — and not directly comparable to — paths from the default file system.
- `Files.copy` (and similar operations) can bridge two different `FileSystem` implementations in a single call, letting you move content between, say, the inside of a ZIP archive and ordinary disk storage transparently.
- Always close a `FileSystem` obtained via `newFileSystem` (ideally with try-with-resources) once you're done with it — for the ZIP provider, this is what actually finalizes and writes out the archive's contents to disk.
