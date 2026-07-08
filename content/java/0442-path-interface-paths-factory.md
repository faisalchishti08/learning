---
card: java
gi: 442
slug: path-interface-paths-factory
title: Path interface & Paths factory
---

## 1. What it is

`Path`, part of the `java.nio.file` package added in Java 7 (as part of "NIO.2"), represents a file system path — a sequence of directory names ending, usually, in a file or directory name — as a rich, structured object rather than just a `String`. `Paths.get(...)` (or, on newer JDKs, `Path.of(...)`) is the factory method that builds one. Unlike the older `java.io.File`, `Path` provides genuine path *manipulation*: combining paths (`resolve`), computing relative paths between two locations (`relativize`), and cleaning up redundant segments (`normalize`) — all without touching the actual file system.

## 2. Why & when

`java.io.File` (from Java 1.0) mixes path representation with file-system operations in one class, and many of its methods return unhelpful `boolean` failure indicators instead of exceptions with useful detail. `Path`, introduced alongside the broader `java.nio.file` API, separates the concerns cleanly: `Path` is purely about the *path itself* — its components, how to combine or compare it with another path — while actual file-system operations (reading, writing, copying) live in the `Files` utility class (covered in the next two tutorials).

You reach for `Path`/`Paths` any time you're building or manipulating file-system locations programmatically — constructing a path from configurable pieces, figuring out where one file sits relative to another, or cleaning up a path assembled from user input that might contain redundant `.`/`..` segments — all without necessarily touching the disk at all.

## 3. Core concept

```java
import java.nio.file.*;

Path path = Paths.get("/home/alice/documents/report.txt");

path.getFileName();   // "report.txt" -- just the last component
path.getParent();     // "/home/alice/documents"
path.getRoot();       // "/"
path.getNameCount();  // 4 -- number of path components after the root
path.getName(1);      // "alice" -- the component at index 1 (0-based, root excluded)
```

`Path` objects are purely structural — none of these methods touch the file system, ask whether the file exists, or read anything from disk. They operate entirely on the string-like structure of the path itself.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Path is broken into a root and a sequence of named components, each accessible by index, with the last component being the file name and everything before it the parent">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">/home/alice/documents/report.txt</text>

  <rect x="30" y="45" width="50" height="30" fill="#1c2430" stroke="#e6edf3"/><text x="55" y="65" fill="#e6edf3" font-size="9" text-anchor="middle">root /</text>
  <rect x="90" y="45" width="80" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="130" y="65" fill="#79c0ff" font-size="9" text-anchor="middle">home [0]</text>
  <rect x="180" y="45" width="80" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="220" y="65" fill="#79c0ff" font-size="9" text-anchor="middle">alice [1]</text>
  <rect x="270" y="45" width="110" height="30" fill="#1c2430" stroke="#79c0ff"/><text x="325" y="65" fill="#79c0ff" font-size="9" text-anchor="middle">documents [2]</text>
  <rect x="390" y="45" width="130" height="30" fill="#1c2430" stroke="#6db33f"/><text x="455" y="65" fill="#6db33f" font-size="9" text-anchor="middle">report.txt [3]</text>

  <text x="325" y="105" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">getFileName() = last component; getParent() = everything before it; getName(i) = component at index i</text>
</svg>

A `Path` decomposes into a root plus an indexable sequence of named components.

## 5. Runnable example

Scenario: working with a small file-organization tool's location logic — the same paths, evolved from basic component inspection, through combining and comparing paths, to cleaning up a path with redundant segments and iterating its normalized components.

### Level 1 — Basic

```java
import java.nio.file.*;

public class PathBasics {
    public static void main(String[] args) {
        Path path = Paths.get("/home/alice/documents/report.txt");

        System.out.println("Full path: " + path);
        System.out.println("File name: " + path.getFileName());
        System.out.println("Parent: " + path.getParent());
        System.out.println("Root: " + path.getRoot());
        System.out.println("Name count: " + path.getNameCount());
        System.out.println("Name at index 1: " + path.getName(1));
    }
}
```

**How to run:** `java PathBasics.java`

`Paths.get(...)` parses the string into a structured `Path`, and each accessor pulls out a specific piece — the file name, parent directory, root, or a specific indexed component — all without ever checking whether this path actually exists on disk.

### Level 2 — Intermediate

```java
import java.nio.file.*;

public class PathResolveRelativize {
    public static void main(String[] args) {
        Path base = Paths.get("/home/alice/documents");
        Path resolved = base.resolve("photos/vacation.jpg"); // combine base with a relative path
        System.out.println("Resolved: " + resolved);

        Path other = Paths.get("/home/alice/photos/vacation.jpg");
        Path relative = base.relativize(other); // express "other" relative to "base"
        System.out.println("Relative from documents to photos: " + relative);
    }
}
```

**How to run:** `java PathResolveRelativize.java`

`resolve` combines a base path with a relative one, as if appending a sub-path onto a directory. `relativize` does the inverse kind of work: given two absolute paths, it computes the relative path that would get you from one to the other — here, since `photos` is a sibling of `documents` rather than nested inside it, the result correctly includes a `..` to step back up first.

### Level 3 — Advanced

```java
import java.nio.file.*;

public class PathNormalizeIterate {
    public static void main(String[] args) {
        Path messy = Paths.get("/home/alice/./documents/../documents/report.txt");
        System.out.println("Messy: " + messy);

        Path clean = messy.normalize(); // resolves "." and ".." segments WITHOUT touching the filesystem
        System.out.println("Normalized: " + clean);

        System.out.println("Iterating segments of the normalized path:");
        for (Path segment : clean) {
            System.out.println("  " + segment);
        }

        System.out.println("Is absolute? " + clean.isAbsolute());
        System.out.println("As absolute (from current dir, if it weren't already): " + clean.toAbsolutePath());
    }
}
```

**How to run:** `java PathNormalizeIterate.java`

`normalize()` resolves `.` (current directory, a no-op) and `..` (step up one level) segments purely through string/structural manipulation — it never touches the file system, so it works correctly even for paths that don't actually exist yet. `Path` itself implements `Iterable<Path>`, so a `for-each` loop visits each named component in order (the root itself is excluded from this iteration).

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `messy` is built from the literal string `"/home/alice/./documents/../documents/report.txt"` — deliberately containing a redundant `.` (current directory) and a `..` (step back up) pair.

`messy.normalize()` processes the path's segments left to right: `home`, `alice`, then `.` (which contributes nothing and is simply dropped), then `documents`, then `..` (which cancels out the *previous* segment, removing `documents`), then `documents` again, then `report.txt`. After this cancellation, what remains is `home`, `alice`, `documents`, `report.txt` — printed as `"/home/alice/documents/report.txt"`, with all the redundant segments resolved away purely through path arithmetic, not by checking anything on disk.

The `for (Path segment : clean)` loop then iterates `clean`'s named components in order: `Path` implements `Iterable<Path>`, so each iteration yields one path segment as its own small `Path` object — `"home"`, `"alice"`, `"documents"`, `"report.txt"`, printed one per line. Note the root (`/`) itself is not included in this iteration; only the named components after it are.

`clean.isAbsolute()` checks whether the path starts from a filesystem root — since it began with `/`, this is `true`. `clean.toAbsolutePath()` would normally resolve a *relative* path against the current working directory to produce an absolute one; since `clean` is already absolute, this call simply returns it unchanged.

Expected output:
```
Messy: /home/alice/./documents/../documents/report.txt
Normalized: /home/alice/documents/report.txt
Iterating segments of the normalized path:
  home
  alice
  documents
  report.txt
Is absolute? true
As absolute (from current dir, if it weren't already): /home/alice/documents/report.txt
```

## 7. Gotchas & takeaways

> `normalize()` operates **purely on the path's text structure** — it does not consult the file system at all, and has no way to know about symbolic links. If any component of the path is actually a symlink pointing somewhere else, `normalize()`'s naive `..`-cancellation logic can produce a path that doesn't correspond to where the symlink chain would actually lead. For a path that must be resolved *correctly* with respect to real symlinks, use `Path.toRealPath()` instead, which does consult the file system.

- `Path` represents a file-system location as a structured object; `Paths.get(...)` (or `Path.of(...)` on newer JDKs) constructs one from a `String`.
- `Path` is purely about the path's structure — none of its methods (`resolve`, `relativize`, `normalize`, component accessors) touch the actual file system; that's the job of the `Files` utility class, covered next.
- `resolve` combines a base path with a relative one; `relativize` computes the relative path needed to get from one absolute path to another.
- `normalize()` resolves `.` and `..` segments through pure text/structural manipulation, without any awareness of symbolic links — use `toRealPath()` if symlink-aware resolution against the real file system is needed.
- `Path` implements `Iterable<Path>`, so a `for-each` loop naturally visits each named component in order, excluding the root.
