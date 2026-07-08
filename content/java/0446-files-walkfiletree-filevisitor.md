---
card: java
gi: 446
slug: files-walkfiletree-filevisitor
title: Files.walkFileTree & FileVisitor
---

## 1. What it is

`Files.walkFileTree(start, visitor)`, added in Java 7, recursively walks a directory tree, invoking callback methods on a `FileVisitor` at each meaningful point: `preVisitDirectory` (before entering a directory), `visitFile` (for each regular file), `visitFileFailed` (when a file couldn't be accessed), and `postVisitDirectory` (after all of a directory's contents have been processed). `SimpleFileVisitor<Path>` provides no-op default implementations of all four, so you only override the ones you actually need. Each callback returns a `FileVisitResult` — `CONTINUE`, `SKIP_SUBTREE` (don't descend into this directory), `SKIP_SIBLINGS`, or `TERMINATE` — controlling how the walk proceeds.

## 2. Why & when

`Files.walk` (a `Stream`-based tree traversal, covered in the `Files` utility class tutorial) is convenient for simple cases, but it doesn't give you fine-grained control over the walk itself — you can't easily say "don't descend into this particular subdirectory" mid-traversal, or "run this cleanup exactly once, after all of a directory's children are done." `walkFileTree`'s callback-based `FileVisitor` interface gives you exactly that control: pruning specific subtrees, reacting differently to files versus directories, handling access failures gracefully, and running logic at the precise moment a directory's contents are fully processed (crucial for correct recursive deletion, since a directory must be empty before it can be removed).

You reach for `walkFileTree` whenever a directory traversal needs more control than a simple stream can offer — skipping specific subdirectories (build artifacts, `.git`, `node_modules`-style folders), computing something that depends on knowing when a directory's children are all done, or implementing robust recursive delete/copy operations.

## 3. Core concept

```java
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;

Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
    @Override
    public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
        return FileVisitResult.CONTINUE; // or SKIP_SUBTREE to prune this directory entirely
    }

    @Override
    public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
        // called once per regular file
        return FileVisitResult.CONTINUE;
    }

    @Override
    public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
        // called AFTER every child of "dir" has already been visited -- safe place to, e.g., delete "dir" itself
        return FileVisitResult.CONTINUE;
    }
});
```

The four callbacks together give a complete picture of the walk's progress: `preVisitDirectory`/`postVisitDirectory` bracket each directory's processing, while `visitFile`/`visitFileFailed` handle its actual file contents.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="walkFileTree visits preVisitDirectory before entering a folder, visitFile for each file inside it, and postVisitDirectory only after every child has been processed, making it safe to delete an empty directory at that point">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">preVisitDirectory</text>
  <rect x="220" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="295" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">visitFile (each entry)</text>
  <rect x="410" y="30" width="150" height="34" rx="6" fill="#1c2430" stroke="#f85149"/><text x="485" y="52" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">postVisitDirectory</text>

  <line x1="180" y1="47" x2="215" y2="47" stroke="#8b949e" marker-end="url(awt1)"/>
  <line x1="370" y1="47" x2="405" y2="47" stroke="#8b949e" marker-end="url(awt1)"/>

  <text x="320" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">postVisitDirectory only fires after ALL of a directory's children (files and subdirectories) are done.</text>
  <text x="320" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">This ordering is exactly what safe recursive deletion needs.</text>
</svg>

The pre/post-directory bracketing is what makes safe, correctly-ordered recursive operations possible.

## 5. Runnable example

Scenario: inspecting and eventually cleaning up a small project directory tree — the same tree, evolved from computing a total file size across the whole tree, through skipping a specific subdirectory entirely, to a full recursive delete that removes files and then their now-empty parent directories, in the correct order.

### Level 1 — Basic

```java
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;

public class WalkTreeSize {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("project");
        Files.write(root.resolve("a.txt"), "12345".getBytes());       // 5 bytes
        Files.createDirectory(root.resolve("sub"));
        Files.write(root.resolve("sub/b.txt"), "1234567890".getBytes()); // 10 bytes

        long[] totalSize = {0}; // array trick to mutate a value from inside the anonymous visitor

        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                totalSize[0] += attrs.size();
                System.out.println("Visited: " + root.relativize(file) + " (" + attrs.size() + " bytes)");
                return FileVisitResult.CONTINUE;
            }
        });

        System.out.println("Total size: " + totalSize[0] + " bytes");

        Files.delete(root.resolve("a.txt"));
        Files.delete(root.resolve("sub/b.txt"));
        Files.delete(root.resolve("sub"));
        Files.delete(root);
    }
}
```

**How to run:** `java WalkTreeSize.java`

`SimpleFileVisitor` provides no-op defaults for everything, so only `visitFile` needs overriding here — it's called once per regular file anywhere in the tree, accumulating each file's size from the already-provided `BasicFileAttributes`, avoiding a separate call to look up size information. (Note: the order files are visited in is determined by the underlying file system, not guaranteed by the API — the total is order-independent regardless.)

### Level 2 — Intermediate

```java
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;

public class WalkTreeSkip {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("project");
        Files.write(root.resolve("main.txt"), "source".getBytes());
        Files.createDirectory(root.resolve("build"));
        Files.write(root.resolve("build/output.class"), "compiled junk".getBytes());
        Files.createDirectory(root.resolve("src"));
        Files.write(root.resolve("src/Main.java"), "public class Main {}".getBytes());

        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult preVisitDirectory(Path dir, BasicFileAttributes attrs) {
                if (dir.getFileName().toString().equals("build")) {
                    System.out.println("Skipping directory: " + root.relativize(dir));
                    return FileVisitResult.SKIP_SUBTREE; // don't descend into "build" at all
                }
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) {
                System.out.println("Visited file: " + root.relativize(file));
                return FileVisitResult.CONTINUE;
            }
        });

        Files.walk(root).sorted(java.util.Comparator.reverseOrder()).forEach(p -> {
            try { Files.delete(p); } catch (Exception e) { throw new RuntimeException(e); }
        });
    }
}
```

**How to run:** `java WalkTreeSkip.java`

Returning `FileVisitResult.SKIP_SUBTREE` from `preVisitDirectory` prunes that entire directory from the walk — `build/output.class` is never visited at all, since the walk never even enters `build`, saving both time and unnecessary processing for directories you know in advance you don't care about.

### Level 3 — Advanced

```java
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.io.IOException;

public class WalkTreeDelete {
    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("to-delete");
        Files.write(root.resolve("a.txt"), "data".getBytes());
        Files.createDirectory(root.resolve("sub"));
        Files.write(root.resolve("sub/b.txt"), "more data".getBytes());

        Files.walkFileTree(root, new SimpleFileVisitor<Path>() {
            @Override
            public FileVisitResult visitFile(Path file, BasicFileAttributes attrs) throws IOException {
                Files.delete(file); // delete files as they're visited
                System.out.println("Deleted file: " + root.relativize(file));
                return FileVisitResult.CONTINUE;
            }

            @Override
            public FileVisitResult visitFileFailed(Path file, IOException exc) {
                System.out.println("Failed to visit: " + file + " (" + exc.getMessage() + ")");
                return FileVisitResult.CONTINUE; // keep going even if one file couldn't be visited
            }

            @Override
            public FileVisitResult postVisitDirectory(Path dir, IOException exc) throws IOException {
                // Runs AFTER all of a directory's children have been visited -- safe to delete it now, since it's empty
                Files.delete(dir);
                System.out.println("Deleted directory: " + root.relativize(dir));
                return FileVisitResult.CONTINUE;
            }
        });

        System.out.println("Root still exists? " + Files.exists(root));
    }
}
```

**How to run:** `java WalkTreeDelete.java`

`postVisitDirectory` is guaranteed to fire only **after** every file and subdirectory inside `dir` has already been processed — that guarantee is precisely what makes it safe to call `Files.delete(dir)` right there, since `Files.delete` requires a directory to be empty. `visitFileFailed` provides a graceful fallback if any individual file can't be accessed, letting the overall walk continue rather than aborting entirely.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example, creating `root` with one file (`a.txt`) and one subdirectory (`sub`) containing another file (`sub/b.txt`). `Files.walkFileTree(root, ...)` begins the traversal.

The walk first enters `root`, then descends into `sub` (directories are entered before their siblings are guaranteed to be fully processed — the exact order between `a.txt` and `sub` isn't fixed by the API, but the file-then-directory dependency *within* `sub` is). `visitFile` fires for `sub/b.txt`: `Files.delete(file)` removes it immediately, printing `"Deleted file: sub/b.txt"`.

Since `sub`'s only child (`b.txt`) has now been visited and deleted, `postVisitDirectory` fires for `sub` itself: at this point `sub` is empty (its one file is gone), so `Files.delete(dir)` succeeds, printing `"Deleted directory: sub"`.

The walk then processes `root`'s other entry, `a.txt`: `visitFile` fires, deleting it and printing `"Deleted file: a.txt"`.

Finally, with both of `root`'s children (`sub` and `a.txt`) fully processed and removed, `postVisitDirectory` fires for `root` itself: it's now empty, so `Files.delete(dir)` succeeds, printing `"Deleted directory: "` (an empty string, since `root.relativize(root)` produces an empty path — `root` relative to itself is nothing).

`Files.exists(root)` after the walk correctly reports `false`, confirming the entire tree — files and directories alike — was removed in a safe, dependency-correct order.

Expected output:
```
Deleted file: sub/b.txt
Deleted directory: sub
Deleted file: a.txt
Deleted directory: 
Root still exists? false
```

## 7. Gotchas & takeaways

> The order in which sibling files and directories are visited is **not guaranteed** by `Files.walkFileTree` — it depends on whatever order the underlying file system happens to return directory entries in. Never write code that assumes a specific visitation order among siblings; only the *parent-after-all-children* guarantee (via `postVisitDirectory`) is something you can safely rely on.

- `SimpleFileVisitor<Path>` provides no-op defaults for all four `FileVisitor` callbacks — override only the ones your traversal actually needs.
- `preVisitDirectory` returning `FileVisitResult.SKIP_SUBTREE` prunes an entire directory (and everything inside it) from the walk — useful for deliberately skipping known-irrelevant subdirectories.
- `postVisitDirectory` is guaranteed to run only after every file and subdirectory inside that directory has already been processed — the key guarantee that makes safe recursive deletion (and similar "roll up results from children" logic) possible.
- `visitFileFailed` lets the walk continue gracefully past a file that couldn't be accessed (permissions, a broken symbolic link, etc.), rather than aborting the whole traversal.
- For simpler cases that don't need this level of control, the `Stream`-based `Files.walk` is usually more concise — reach for `walkFileTree` specifically when you need pruning, ordered pre/post-directory hooks, or fine-grained failure handling.
