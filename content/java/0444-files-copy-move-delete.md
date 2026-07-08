---
card: java
gi: 444
slug: files-copy-move-delete
title: Files.copy / move / delete
---

## 1. What it is

`Files.copy(source, target, options...)`, `Files.move(source, target, options...)`, and `Files.delete(path)` (plus its safer sibling `Files.deleteIfExists(path)`) are the `Files` utility class's operations for actually rearranging files on disk. Each accepts optional `CopyOption` flags — most commonly `StandardCopyOption.REPLACE_EXISTING`, which permits overwriting an existing file at the destination (without it, both `copy` and `move` throw `FileAlreadyExistsException` if the target already exists).

## 2. Why & when

These operations are the fundamentals of any file-management task — backing up a file, replacing a configuration with a new version, cleaning up temporary files — and their default behavior is deliberately conservative: refusing to silently overwrite an existing file unless you explicitly opt in with `REPLACE_EXISTING`. This default protects against a common and costly class of bug (accidentally clobbering existing data) while still making the overwrite path a single, explicit flag away when you genuinely want it.

You reach for `Files.copy`/`move`/`delete` any time your program needs to manage files directly rather than just read or write their content — implementing a backup routine, a file-based cache with rotation, staging-then-promoting a new version of a file, or cleaning up after a temporary operation.

## 3. Core concept

```java
import java.nio.file.*;

Files.copy(source, target);                                         // fails if target already exists
Files.copy(source, target, StandardCopyOption.REPLACE_EXISTING);     // allows overwriting

Files.move(source, target);                                         // fails if target already exists; source is REMOVED
Files.move(source, target, StandardCopyOption.REPLACE_EXISTING);     // allows overwriting; source is REMOVED

Files.delete(path);            // throws NoSuchFileException if path doesn't exist
Files.deleteIfExists(path);    // returns false (no exception) if path doesn't exist
```

The key distinction between `copy` and `move`: `copy` leaves the source file in place, producing two independent copies; `move` removes the source, leaving only the destination — genuinely relocating the file rather than duplicating it.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Files.copy leaves the source in place and creates an independent copy at the destination; Files.move removes the source, relocating the file to the destination">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#6db33f" font-size="11" font-family="sans-serif">Files.copy(source, target): source REMAINS, target is a new independent copy</text>
  <rect x="30" y="38" width="140" height="30" fill="#1c2430" stroke="#6db33f"/><text x="100" y="58" fill="#6db33f" font-size="9" text-anchor="middle">source (still here)</text>
  <rect x="220" y="38" width="140" height="30" fill="#1c2430" stroke="#6db33f"/><text x="290" y="58" fill="#6db33f" font-size="9" text-anchor="middle">target (new copy)</text>
  <line x1="170" y1="53" x2="215" y2="53" stroke="#6db33f" marker-end="url(afc1)"/>

  <text x="20" y="105" fill="#f85149" font-size="11" font-family="sans-serif">Files.move(source, target): source is REMOVED, target is the SAME file relocated</text>
  <rect x="30" y="117" width="140" height="30" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="100" y="137" fill="#8b949e" font-size="9" text-anchor="middle">source (gone)</text>
  <rect x="220" y="117" width="140" height="30" fill="#1c2430" stroke="#f85149"/><text x="290" y="137" fill="#f85149" font-size="9" text-anchor="middle">target (relocated)</text>
  <line x1="170" y1="132" x2="215" y2="132" stroke="#f85149" marker-end="url(afc2)"/>

  <defs><marker id="afc1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker><marker id="afc2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker></defs>
</svg>

`copy` duplicates; `move` relocates — the source's fate after the operation is the defining difference.

## 5. Runnable example

Scenario: a small backup utility for a project directory — the same backup task, evolved from a basic single-file copy, through safely replacing an existing "live" file via a staged move, to recursively backing up (and later cleaning up) an entire directory tree.

### Level 1 — Basic

```java
import java.nio.file.*;

public class BackupCopyBasic {
    public static void main(String[] args) throws Exception {
        Path original = Files.createTempFile("data", ".txt");
        Files.write(original, "important data".getBytes());

        Path backup = original.resolveSibling("data-backup.txt");
        Files.copy(original, backup); // copies content; both files now exist independently

        System.out.println("Original exists: " + Files.exists(original));
        System.out.println("Backup exists: " + Files.exists(backup));
        System.out.println("Backup content: " + new String(Files.readAllBytes(backup)));

        Files.delete(original);
        Files.delete(backup);
    }
}
```

**How to run:** `java BackupCopyBasic.java`

`Files.copy` creates an independent copy at `backup` while leaving `original` untouched — both files exist simultaneously afterward, each with their own copy of the same content.

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.nio.file.StandardCopyOption;

public class BackupMoveReplace {
    public static void main(String[] args) throws Exception {
        Path staging = Files.createTempFile("staging", ".txt");
        Files.write(staging, "version 2".getBytes());

        Path live = staging.resolveSibling("live-config.txt");
        Files.write(live, "version 1 (old)".getBytes()); // an existing "live" file already present

        try {
            Files.move(staging, live); // fails: destination already exists, no overwrite allowed by default
        } catch (java.nio.file.FileAlreadyExistsException e) {
            System.out.println("Move failed as expected: " + e.getClass().getSimpleName());
        }

        Files.move(staging, live, StandardCopyOption.REPLACE_EXISTING); // now explicitly allow overwrite
        System.out.println("Live content after move: " + new String(Files.readAllBytes(live)));
        System.out.println("Staging still exists? " + Files.exists(staging)); // move REMOVES the source

        Files.delete(live);
    }
}
```

**How to run:** `java BackupMoveReplace.java`

The first `Files.move` attempt fails with `FileAlreadyExistsException`, since `live` already exists and no overwrite was authorized. Adding `StandardCopyOption.REPLACE_EXISTING` lets the second attempt succeed — `staging`'s content replaces `live`'s, and `staging` itself no longer exists afterward, since `move` (unlike `copy`) removes the source.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.io.IOException;
import java.util.Comparator;
import java.util.stream.Stream;

public class BackupRotation {
    public static void main(String[] args) throws Exception {
        Path projectDir = Files.createTempDirectory("project");
        Files.write(projectDir.resolve("main.txt"), "source code".getBytes());
        Files.createDirectory(projectDir.resolve("assets"));
        Files.write(projectDir.resolve("assets/logo.txt"), "logo data".getBytes());

        Path backupDir = projectDir.resolveSibling("project-backup");

        // Recursively copy the whole directory tree, since Files.copy alone only copies ONE file/directory entry
        try (Stream<Path> paths = Files.walk(projectDir)) {
            for (Path source : (Iterable<Path>) paths::iterator) {
                Path target = backupDir.resolve(projectDir.relativize(source));
                if (Files.isDirectory(source)) {
                    Files.createDirectories(target);
                } else {
                    Files.copy(source, target);
                }
            }
        }

        System.out.println("Backed up main.txt exists: " + Files.exists(backupDir.resolve("main.txt")));
        System.out.println("Backed up assets/logo.txt exists: " + Files.exists(backupDir.resolve("assets/logo.txt")));

        // deleteIfExists is safe to call even if the path is already gone; delete() would throw
        Path neverExisted = projectDir.resolve("does-not-exist.txt");
        boolean actuallyDeleted = Files.deleteIfExists(neverExisted);
        System.out.println("Attempted delete of nonexistent file, actually deleted: " + actuallyDeleted);

        // Clean up: a directory must be EMPTY before Files.delete can remove it,
        // so walk it in REVERSE (deepest entries first) to delete files before their parent directories.
        for (Path dir : new Path[]{projectDir, backupDir}) {
            try (Stream<Path> paths = Files.walk(dir)) {
                paths.sorted(Comparator.reverseOrder()).forEach(p -> {
                    try { Files.delete(p); } catch (IOException e) { throw new RuntimeException(e); }
                });
            }
        }
        System.out.println("Cleanup complete. Project dir exists: " + Files.exists(projectDir));
    }
}
```

**How to run:** `java BackupRotation.java`

`Files.copy` only ever copies **one** file or creates **one** directory — there's no built-in "copy this whole tree" operation, so `Files.walk` is used to visit every entry and copy or recreate each one individually. Cleanup similarly must delete deepest entries first (`Files.delete` refuses to remove a non-empty directory), which `Comparator.reverseOrder()` on the walked, naturally-parent-first stream achieves by reversing it to child-first.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `projectDir` is created with one file (`main.txt`) and one subdirectory (`assets`) containing another file (`logo.txt`).

The backup loop calls `Files.walk(projectDir)`, which lazily streams every path under `projectDir` (including `projectDir` itself, first). For each `source` path, `projectDir.relativize(source)` computes its path *relative* to `projectDir` — so `main.txt` relativizes to `main.txt`, and `assets/logo.txt` relativizes to `assets/logo.txt`. `backupDir.resolve(...)` then combines that relative path with the backup location, producing the correct destination path for each entry. If `source` is a directory, `Files.createDirectories(target)` recreates that directory structure in the backup; otherwise, `Files.copy(source, target)` copies the file's content. This correctly walks and reproduces the whole tree: `projectDir` itself, `main.txt`, `assets`, and `assets/logo.txt`.

After the walk, both `backupDir.resolve("main.txt")` and `backupDir.resolve("assets/logo.txt")` exist, confirmed by `Files.exists`.

`Files.deleteIfExists(neverExisted)` is called on a path that was never created — since the file genuinely doesn't exist, `deleteIfExists` returns `false` rather than throwing, unlike plain `Files.delete`, which would throw `NoSuchFileException` here.

The cleanup loop processes `projectDir` and `backupDir` in turn. For each, `Files.walk(dir)` produces a stream naturally ordered parent-before-children (since a directory is visited before its own contents); `.sorted(Comparator.reverseOrder())` reverses this, so the *deepest* entries (like `assets/logo.txt`) come first, and each directory's own entry comes only after everything inside it has already been processed. This ordering matters because `Files.delete` on a directory requires it to be **empty** first — deleting children before their parent directory is the only order that works.

Expected output:
```
Backed up main.txt exists: true
Backed up assets/logo.txt exists: true
Attempted delete of nonexistent file, actually deleted: false
Cleanup complete. Project dir exists: false
```

## 7. Gotchas & takeaways

> `Files.delete` throws `DirectoryNotEmptyException` if you try to delete a directory that still contains anything — there is no built-in "delete this directory and everything inside it" method. Recursive deletion (as the cleanup loop above demonstrates) requires walking the tree and deleting the deepest entries first; getting the order backward (parent before children) causes the whole operation to fail partway through.

- `Files.copy` leaves the source in place, producing an independent copy; `Files.move` removes the source, relocating the file.
- Both `copy` and `move` throw `FileAlreadyExistsException` if the destination already exists, unless `StandardCopyOption.REPLACE_EXISTING` is passed explicitly — a deliberate, safe-by-default design.
- `Files.delete` throws `NoSuchFileException` if the target doesn't exist; `Files.deleteIfExists` instead returns `false` in that case, without throwing — use whichever matches whether a missing file is an error condition or an expected possibility in your code.
- Neither `copy` nor `delete` operates recursively on directory trees by itself — copying or deleting a whole tree requires walking it (`Files.walk`) and processing each entry individually, in the correct order (parent-first for creation/copying, child-first for deletion).
- `Comparator.reverseOrder()` applied to a naturally parent-first `Files.walk` stream is a simple, reliable way to get the deepest-first ordering that recursive deletion requires.
