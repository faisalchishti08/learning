---
card: java
gi: 451
slug: file-attributes-basicfileattributes-posixfilepermissions
title: File attributes (BasicFileAttributes, PosixFilePermissions)
---

## 1. What it is

`Files.readAttributes(path, BasicFileAttributes.class)`, added in Java 7, retrieves a bundle of a file's metadata — size, creation time, last-modified time, and whether it's a regular file, directory, or symbolic link — in one efficient call, rather than several separate method calls each potentially hitting the file system again. On POSIX-compliant systems (Linux, macOS), `PosixFilePermissions` additionally provides access to the classic Unix permission model — read/write/execute for owner, group, and others — as a typed `Set<PosixFilePermission>`, convertible to and from the familiar `"rwxr-xr-x"`-style string notation.

## 2. Why & when

Before `BasicFileAttributes`, retrieving several pieces of metadata about a file meant several separate calls (`file.length()`, `file.lastModified()`, `file.isDirectory()`, and so on via `java.io.File`), each of which could independently hit the file system — inefficient, and prone to inconsistency if the file changed between calls. `readAttributes` retrieves everything in a single, atomic snapshot. Similarly, before `PosixFilePermissions`, working with Unix-style permissions from Java meant manipulating numeric octal modes by hand or shelling out to `chmod` — error-prone and unreadable. `PosixFilePermissions` gives a typed, readable `Set<PosixFilePermission>` representation instead, with clean conversion to and from the standard `rwx`-style string notation.

You reach for `BasicFileAttributes` any time you need multiple pieces of a file's metadata at once — a file browser displaying size and modification date, a backup tool deciding what's changed since last run, or diagnostic tooling. `PosixFilePermissions` is for anything that needs to read or set Unix-style file permissions programmatically — a deployment script marking a file executable, a security tool auditing permissions, or a program deliberately restricting access to a sensitive file it created.

## 3. Core concept

```java
import java.nio.file.*;
import java.nio.file.attribute.*;

BasicFileAttributes attrs = Files.readAttributes(path, BasicFileAttributes.class);
attrs.size();                // in bytes
attrs.isDirectory();
attrs.isRegularFile();
attrs.lastModifiedTime();     // a FileTime, not a raw long

// POSIX-only (Linux, macOS -- not Windows):
Set<PosixFilePermission> perms = Files.getPosixFilePermissions(path);
String readable = PosixFilePermissions.toString(perms);          // e.g. "rw-r--r--"
Set<PosixFilePermission> parsed = PosixFilePermissions.fromString("r--------");
Files.setPosixFilePermissions(path, parsed);                       // actually changes the file's permissions
```

`readAttributes` returns a single object bundling everything together, rather than requiring one round-trip per piece of metadata — an important efficiency and consistency detail for anything inspecting many files.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BasicFileAttributes bundles size, timestamps, and file-type flags into one object retrieved in a single call; PosixFilePermissions represents owner, group, and others read/write/execute permissions as a typed set">
  <rect x="8" y="8" width="624" height="134" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="260" height="90" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="160" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">BasicFileAttributes</text>
  <text x="160" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">size(), isDirectory(), isRegularFile()</text>
  <text x="160" y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">creationTime(), lastModifiedTime()</text>
  <text x="160" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-- all in ONE call</text>

  <rect x="340" y="30" width="270" height="90" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">PosixFilePermissions</text>
  <text x="475" y="68" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Set&lt;PosixFilePermission&gt;</text>
  <text x="475" y="84" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">toString()/fromString(): "rwxr-xr-x"</text>
  <text x="475" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-- Linux/macOS only</text>
</svg>

`BasicFileAttributes` bundles common metadata efficiently; `PosixFilePermissions` handles the Unix permission model specifically.

## 5. Runnable example

Scenario: inspecting and adjusting a file's metadata and access permissions — the same file, evolved from reading its basic attributes, through reading its current POSIX permissions in readable form, to actually restricting a file to read-only and observing the effect firsthand.

### Level 1 — Basic

```java
import java.nio.file.*;
import java.nio.file.attribute.*;

public class AttributesBasic {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("attrs-demo", ".txt");
        Files.write(file, "some content".getBytes());

        BasicFileAttributes attrs = Files.readAttributes(file, BasicFileAttributes.class);

        System.out.println("Size: " + attrs.size() + " bytes");
        System.out.println("Is regular file: " + attrs.isRegularFile());
        System.out.println("Is directory: " + attrs.isDirectory());
        System.out.println("Is symbolic link: " + attrs.isSymbolicLink());
        System.out.println("Last modified time is present: " + (attrs.lastModifiedTime() != null));

        Files.delete(file);
    }
}
```

**How to run:** `java AttributesBasic.java`

One `Files.readAttributes` call retrieves size, file-type flags, and timestamps together — compare this to needing several separate `java.io.File` method calls, each potentially a fresh round-trip to the file system.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.nio.file.attribute.*;
import java.util.Set;

public class PosixPermissionsRead {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("posix-demo", ".txt");

        Set<PosixFilePermission> perms = Files.getPosixFilePermissions(file);
        String permString = PosixFilePermissions.toString(perms); // human-readable, like "rw-r--r--"
        System.out.println("Default permissions: " + permString);

        System.out.println("Owner can read: " + perms.contains(PosixFilePermission.OWNER_READ));
        System.out.println("Owner can write: " + perms.contains(PosixFilePermission.OWNER_WRITE));
        System.out.println("Others can write: " + perms.contains(PosixFilePermission.OTHERS_WRITE));

        Files.delete(file);
    }
}
```

**How to run:** `java PosixPermissionsRead.java`

`Files.getPosixFilePermissions` returns a typed `Set<PosixFilePermission>` — checking a specific permission is a simple `.contains(...)` call, and `PosixFilePermissions.toString` converts the whole set into the familiar `"rwx"`-style notation for display.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.nio.file.attribute.*;
import java.util.Set;

public class PosixPermissionsSet {
    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("posix-demo2", ".txt");
        Files.write(file, "original".getBytes());

        System.out.println("Before: " + PosixFilePermissions.toString(Files.getPosixFilePermissions(file)));

        // Make the file READ-ONLY for its owner (and nobody else) by removing OWNER_WRITE
        Set<PosixFilePermission> readOnly = PosixFilePermissions.fromString("r--------");
        Files.setPosixFilePermissions(file, readOnly);

        System.out.println("After: " + PosixFilePermissions.toString(Files.getPosixFilePermissions(file)));

        try {
            Files.write(file, "modified".getBytes());
            System.out.println("Write succeeded (unexpected!)");
        } catch (java.io.IOException e) {
            System.out.println("Write failed as expected: " + e.getClass().getSimpleName());
        }

        // Restore write permission so we can clean up
        Files.setPosixFilePermissions(file, PosixFilePermissions.fromString("rw-------"));
        Files.delete(file);
    }
}
```

**How to run:** `java PosixPermissionsSet.java`

`Files.setPosixFilePermissions` genuinely changes the file's access permissions on disk — after removing write access, an actual `Files.write` attempt fails with `AccessDeniedException`, confirming the permission change took real effect rather than just updating some in-memory representation.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. A temporary file is created and written with `"original"`. `Files.getPosixFilePermissions(file)` retrieves its current permissions — freshly created temp files typically default to owner-only read/write (`"rw-------"`), printed as `"Before: rw-------"`.

`PosixFilePermissions.fromString("r--------")` parses that string into a `Set<PosixFilePermission>` containing only `OWNER_READ` — no write, no execute, for owner, group, or others. `Files.setPosixFilePermissions(file, readOnly)` applies this set to the actual file on disk, replacing whatever permissions it had before. Reading them back and converting to a string confirms the change: `"After: r--------"`.

`Files.write(file, "modified".getBytes())` is then attempted inside a `try` block. Because the file's permissions no longer include `OWNER_WRITE`, the underlying operating system refuses the write — this surfaces in Java as `AccessDeniedException` (a subclass of `IOException`), caught and printed as `"Write failed as expected: AccessDeniedException"`. The write genuinely did not happen; the file's content on disk remains `"original"`.

Finally, `Files.setPosixFilePermissions(file, PosixFilePermissions.fromString("rw-------"))` restores write access, specifically so the subsequent `Files.delete(file)` call (which, on most systems, doesn't strictly require write permission on the file itself, but this restores a clean, expected state regardless) completes without any lingering permission complications.

Expected output:
```
Before: rw-------
After: r--------
Write failed as expected: AccessDeniedException
```

## 7. Gotchas & takeaways

> `PosixFilePermissions` and the whole POSIX permission model only apply on **POSIX-compliant file systems** (Linux, macOS, and similar Unix-like systems) — attempting to use `Files.getPosixFilePermissions`/`setPosixFilePermissions` on a Windows NTFS volume throws `UnsupportedOperationException`, since Windows uses an entirely different (ACL-based) permission model. Code intended to run cross-platform must check `FileSystems.getDefault().supportedFileAttributeViews().contains("posix")` (or otherwise branch by platform) before relying on this API.

- `Files.readAttributes(path, BasicFileAttributes.class)` retrieves size, timestamps, and file-type flags in one efficient, consistent snapshot, rather than multiple separate calls.
- `PosixFilePermissions.toString`/`fromString` convert between a typed `Set<PosixFilePermission>` and the familiar `"rwxr-xr-x"`-style notation.
- `Files.setPosixFilePermissions` genuinely changes a file's on-disk permissions — subsequent operations that violate those permissions (like writing to a read-only file) will actually fail at the operating-system level, surfaced as `AccessDeniedException`.
- The POSIX permission API is platform-specific; it's unavailable (and throws `UnsupportedOperationException`) on non-POSIX file systems like Windows NTFS.
- Reading attributes in one bundled call (rather than several separate ones) is both more efficient and more consistent, since all the values reflect the exact same point in time rather than potentially-differing snapshots from separate calls.
