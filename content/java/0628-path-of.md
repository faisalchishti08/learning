---
card: java
gi: 628
slug: path-of
title: Path.of()
---

## 1. What it is

`Path.of(String first, String... more)` is a Java 11 static factory method that creates a `Path` instance from one or more path segments. It is functionally identical to `Paths.get(String first, String... more)` — the method it replaces. The difference is purely cosmetic: `Path.of()` reads more naturally (you create a `Path` by calling `Path.of(...)`) and follows the convention established by `List.of()`, `Set.of()`, and `Map.of()` (the static factory methods added in Java 9). `Paths.get()` still works and is not deprecated, but `Path.of()` is the preferred API for new code.

## 2. Why & when

For over a decade, Java developers created `Path` objects with `Paths.get(...)` — a method on a different class (`Paths`) from the type it returned (`Path`). This was a known API design wart: `Paths` is a utility class with exactly one method, and discovery was poor (new developers typed `Path.` in their IDE and found no constructor or factory method). `Path.of()` fixes this by placing the factory method directly on the `Path` interface (as a static method, added via the interface evolution allowed since Java 8). Use `Path.of()` in all new Java 11+ code; `Paths.get()` remains for backward compatibility but offers no advantage.

## 3. Core concept

```java
// Java 11+ (preferred):
Path p1 = Path.of("/home/user/docs/file.txt");
Path p2 = Path.of("/home", "user", "docs", "file.txt");
Path p3 = Path.of("/home/user/docs", "file.txt");

// Pre-Java 11 (still works but discouraged for new code):
Path p4 = Paths.get("/home/user/docs/file.txt");
Path p5 = Paths.get("/home", "user", "docs", "file.txt");

// Both produce identical Path objects:
System.out.println(p1.equals(p4));  // true
```

`Path.of()` delegates directly to `Paths.get()` internally — the behaviour is bytecode-identical. The change is purely a readability and discoverability improvement.

## 4. Diagram

<svg viewBox="0 0 560 130" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Path.of() is the modern factory method replacing Paths.get()">
  <rect x="10" y="10" width="540" height="110" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="240" height="45" rx="4" fill="#0d1117" stroke="#f85149"/>
  <text x="140" y="44" fill="#f85149" font-size="11" text-anchor="middle" font-family="monospace">Paths.get("a", "b", "c")</text>
  <text x="140" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Pre-Java 11 (still works, not deprecated)</text>

  <text x="275" y="50" fill="#8b949e" font-size="16" font-family="monospace" text-anchor="middle">→</text>

  <rect x="295" y="25" width="240" height="45" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="415" y="44" fill="#3fb950" font-size="11" text-anchor="middle" font-family="monospace">Path.of("a", "b", "c")</text>
  <text x="415" y="60" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Java 11+ (preferred — factory on Path itself)</text>

  <text x="20" y="95" fill="#8b949e" font-size="9" font-family="sans-serif">Path.of() delegates to Paths.get() — identical behaviour, better discoverability</text>
  <text x="20" y="113" fill="#3fb950" font-size="9" font-family="sans-serif">Follows the List.of() / Set.of() / Map.of() convention for static factory methods</text>
</svg>

`Path.of()` is a pure rename: same behaviour, better API design, following the `List.of()` convention.

## 5. Runnable example

Scenario: building a file-system navigation utility that constructs paths from segments — starting with basic path creation, extending to path manipulation, and finally handling cross-platform path concerns.

### Level 1 — Basic

```java
// File: PathOfDemo.java
import java.nio.file.*;

public class PathOfDemo {
    public static void main(String[] args) {
        // Single string
        Path p1 = Path.of("/home/user/docs/readme.txt");
        System.out.println("Single string: " + p1);

        // Varargs segments (OS joins them with correct separator)
        Path p2 = Path.of("home", "user", "docs", "readme.txt");
        System.out.println("Varargs:       " + p2);

        // Mix of directory and file
        Path p3 = Path.of("/home/user/docs", "readme.txt");
        System.out.println("Mix:           " + p3);

        // All produce the same normalised path
        Path normalised = Path.of("/home/user/docs/readme.txt");
        System.out.println("\nAll equal? " +
            (p1.equals(normalised) && p2.toAbsolutePath().equals(normalised.toAbsolutePath()) ?
             "Yes (modulo absolute/relative)" : "No"));
    }
}
```

**How to run:** `java PathOfDemo.java`

Expected output (on macOS/Linux):
```
Single string: /home/user/docs/readme.txt
Varargs:       home/user/docs/readme.txt
Mix:           /home/user/docs/readme.txt

All equal? Yes (modulo absolute/relative)
```

The simplest usage: `Path.of()` with a single string creates an absolute or relative path; with multiple segments, it joins them using the platform's path separator.

### Level 2 — Intermediate

```java
// File: PathManipulation.java
import java.nio.file.*;

public class PathManipulation {
    public static void main(String[] args) {
        // Build a path and navigate it
        Path project = Path.of("myapp", "src", "main", "java", "App.java");

        System.out.println("Full path:        " + project);
        System.out.println("File name:        " + project.getFileName());
        System.out.println("Parent:           " + project.getParent());
        System.out.println("Root:             " + project.getRoot());
        System.out.println("Name count:       " + project.getNameCount());

        // Enumerate name elements
        System.out.println("\nName elements:");
        for (int i = 0; i < project.getNameCount(); i++) {
            System.out.println("  [" + i + "] " + project.getName(i));
        }

        // Resolve sibling
        Path sibling = project.resolveSibling("Test.java");
        System.out.println("\nSibling (Test.java): " + sibling);

        // Subpath
        Path sub = project.subpath(0, 3);  // myapp/src/main
        System.out.println("Subpath [0,3):    " + sub);

        // Resolve against a different root
        Path config = Path.of("config").resolve("app.properties");
        System.out.println("Resolved config:  " + config);
    }
}
```

**How to run:** `java PathManipulation.java`

Expected output (on macOS/Linux):
```
Full path:        myapp/src/main/java/App.java
File name:        App.java
Parent:           myapp/src/main/java
Root:             null
Name count:       5

Name elements:
  [0] myapp
  [1] src
  [2] main
  [3] java
  [4] App.java

Sibling (Test.java): myapp/src/main/java/Test.java
Subpath [0,3):    myapp/src/main
Resolved config:  config/app.properties
```

The real-world concern: path manipulation. Once you have a `Path` object (via `Path.of()`), you can extract file names, navigate to parent directories, resolve siblings, and extract subpaths — all without string manipulation or platform-dependent separator handling.

### Level 3 — Advanced

```java
// File: PathOfAdvanced.java
import java.nio.file.*;

public class PathOfAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Cross-platform awareness ===\n");

        // Path.of() uses the platform's default file system
        Path p = Path.of("docs", "report.txt");
        System.out.println("Platform:       " + System.getProperty("os.name"));
        System.out.println("Path toString:  " + p.toString());
        System.out.println("Separator used: " + p.getFileSystem().getSeparator());

        // On macOS/Linux: docs/report.txt
        // On Windows:    docs\report.txt

        System.out.println("\n=== Absolute vs relative ===\n");

        Path relative = Path.of("data", "config.json");
        Path absolute = relative.toAbsolutePath();
        System.out.println("Relative:  " + relative);
        System.out.println("Absolute:  " + absolute);
        System.out.println("Is absolute: " + relative.isAbsolute());

        System.out.println("\n=== Normalisation ===\n");

        Path messy = Path.of("docs", "..", "docs", ".", "report.txt");
        System.out.println("Before normalise: " + messy);
        System.out.println("After normalise:  " + messy.normalize());

        System.out.println("\n=== Path.of() vs Paths.get() — proof of equivalence ===\n");

        Path a = Path.of("x", "y", "z");
        Path b = Paths.get("x", "y", "z");
        System.out.println("Path.of()  = " + a);
        System.out.println("Paths.get() = " + b);
        System.out.println("Equal: " + a.equals(b));
        System.out.println("Same class: " + (a.getClass() == b.getClass()));

        System.out.println("\n=== Real-world: constructing a log file path ===\n");

        String logDir = "logs";
        String date = "2026-07-09";
        String appName = "myapp";
        Path logPath = Path.of(logDir, date, appName + ".log");
        System.out.println("Log path: " + logPath);

        // Ensure parent directory exists
        Path parent = logPath.getParent();
        System.out.println("Parent: " + parent);
        System.out.println("(In real code, call Files.createDirectories(parent) here)");
    }
}
```

**How to run:** `java PathOfAdvanced.java`

Expected output (on macOS/Linux):
```
=== Cross-platform awareness ===

Platform:       Mac OS X
Path toString:  docs/report.txt
Separator used: /

=== Absolute vs relative ===

Relative:  data/config.json
Absolute:  /Users/.../Learning/data/config.json
Is absolute: false

=== Normalisation ===

Before normalise: docs/../docs/./report.txt
After normalise:  docs/report.txt

=== Path.of() vs Paths.get() — proof of equivalence ===

Path.of()   = x/y/z
Paths.get() = x/y/z
Equal: true
Same class: true

=== Real-world: constructing a log file path ===

Log path: logs/2026-07-09/myapp.log
Parent: logs/2026-07-09
(In real code, call Files.createDirectories(parent) here)
```

The production-flavoured hard cases: (1) **Cross-platform** — `Path.of()` uses the platform's default file system, so separators differ between macOS/Linux (`/`) and Windows (`\`). Never hard-code separators; let `Path` handle them. (2) **Normalisation** — `Path.normalize()` resolves `.` and `..` segments without accessing the file system (purely lexical). (3) **Creating parent directories** — `Path.of()` does NOT create directories; use `Files.createDirectories(path.getParent())` before writing files.

## 6. Walkthrough

Tracing `Path logPath = Path.of("logs", "2026-07-09", "myapp.log")`:

1. The static method `Path.of(String first, String... more)` is called with `first = "logs"` and `more = ["2026-07-09", "myapp.log"]`.

2. Internally, `Path.of()` delegates to `Paths.get(first, more)` — the existing implementation. It calls `FileSystems.getDefault().getPath(first, more)`.

3. The default `FileSystem` (typically `UnixFileSystem` on macOS/Linux or `WindowsFileSystem` on Windows) constructs a `Path` object by joining the segments with the platform separator. On macOS: `"logs/2026-07-09/myapp.log"`. On Windows: `"logs\2026-07-09\myapp.log"`.

4. The resulting `Path` object is returned. No I/O has occurred — the file does not need to exist. `Path` is a purely representational object (a fancy string wrapper with useful methods).

5. The caller now has a `Path` representing the log file location. To actually create the file, `Files.writeString(logPath, content)` would be called, which would throw `NoSuchFileException` if `logs/2026-07-09/` doesn't exist.

## 7. Gotchas & takeaways

> `Path.of()` is **not a replacement for `Paths.get()` with different behaviour** — it is the same method, moved to the `Path` interface for better API design. There is zero behavioural difference. The two can be used interchangeably, even in the same codebase.

- `Path.of()` was added in Java 11 alongside `Files.readString()` and `Files.writeString()` as part of the same effort to modernise the `java.nio.file` API with sensible defaults and better discoverability.
- `Path.of()` follows the convention of `List.of()`, `Set.of()`, `Map.of()` — static factory methods on the interface they create. This pattern makes APIs self-discovering: typing `Path.` in an IDE shows the factory method.
- For new code, prefer `Path.of()`. For code that must compile on Java 8–10, use `Paths.get()`. Both produce identical `Path` objects.
- `Path.of()` does not validate that the path exists or is valid — it is purely a string construction. Use `Files.exists(path)` to check existence and `Files.createDirectories(path.getParent())` to ensure the parent directory exists before writing.
- The method accepts an arbitrary number of varargs segments. Empty strings and null segments are not allowed (they cause runtime exceptions).
