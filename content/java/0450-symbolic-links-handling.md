---
card: java
gi: 450
slug: symbolic-links-handling
title: Symbolic links handling
---

## 1. What it is

Java 7's `java.nio.file` API added first-class support for symbolic links — a file system entry that points to another location rather than containing data itself. `Files.createSymbolicLink(link, target)` creates one; `Files.readSymbolicLink(link)` returns the `Path` it points to; `Files.isSymbolicLink(path)` checks whether a given path *is* a link (as opposed to a regular file or directory). Critically, many `Files` methods accept an optional `LinkOption.NOFOLLOW_LINKS` argument, letting you choose whether an operation should follow a link to its target or examine the link itself.

## 2. Why & when

Symbolic links are a fundamental Unix (and, differently, Windows) file system feature — a shortcut-like entry that lets one location "stand in" for another. Before Java 7's `nio.file` API, `java.io.File` had essentially no awareness of symbolic links as a distinct concept: most operations transparently followed them, with no way to ask "is this specific path a link, or the real thing?" `Files`/`Path` fixed this by making link-awareness explicit and controllable — you can choose, per operation, whether to follow a link or examine it directly.

You reach for this whenever your code needs to work correctly in the presence of symbolic links — deployment tooling that manages "current version" symlinks pointing at versioned directories, file management utilities that need to detect and handle links specially (rather than accidentally following them into unintended locations), or diagnostic tools that need to report whether something is a link versus real data.

## 3. Core concept

```java
import java.nio.file.*;

Files.createSymbolicLink(link, target); // "link" now points AT "target"

Path pointsTo = Files.readSymbolicLink(link); // where does "link" point?

Files.isSymbolicLink(link);   // true -- this path IS a link
Files.isSymbolicLink(target); // false -- this is the real thing

Files.exists(link);                              // follows the link -- reports on the TARGET's existence
Files.exists(link, LinkOption.NOFOLLOW_LINKS);    // does NOT follow -- reports on the LINK itself
```

Most `Files` methods, by default, transparently follow symbolic links — exactly as most command-line tools do. `LinkOption.NOFOLLOW_LINKS` is the escape hatch when you specifically need to examine the link entry itself, rather than whatever it happens to point at.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Files.exists on a symbolic link normally follows it and reports on the target's existence; with NOFOLLOW_LINKS it instead reports on whether the link entry itself exists, regardless of whether its target does">
  <rect x="8" y="8" width="624" height="144" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">link (a shortcut)</text>
  <rect x="250" y="30" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-dasharray="4,3"/><text x="320" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">target (may be gone)</text>
  <line x1="170" y1="47" x2="245" y2="47" stroke="#8b949e" marker-end="url(asy1)"/>

  <text x="20" y="100" fill="#8b949e" font-size="10" font-family="sans-serif">exists(link)                  -&gt; follows to target -- false if target is gone (a "broken" link)</text>
  <text x="20" y="125" fill="#8b949e" font-size="10" font-family="sans-serif">exists(link, NOFOLLOW_LINKS)   -&gt; checks the link entry itself -- true even if target is gone</text>
  <defs><marker id="asy1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

A "broken" link is a link whose target no longer exists — the link entry itself is still there; only what it points to has vanished.

## 5. Runnable example

Scenario: a small file-shortcut mechanism — the same link, evolved from basic creation and reading, through distinguishing a link from its target using `NOFOLLOW_LINKS`, to correctly detecting and handling a "broken" link whose target has been deleted.

### Level 1 — Basic

```java
import java.nio.file.*;

public class SymlinkBasic {
    public static void main(String[] args) throws Exception {
        Path target = Files.createTempFile("real-file", ".txt");
        Files.write(target, "real content".getBytes());

        Path link = target.resolveSibling("shortcut.txt");
        Files.createSymbolicLink(link, target);

        System.out.println("Link points to: " + Files.readSymbolicLink(link));
        System.out.println("Reading through the link: " + new String(Files.readAllBytes(link)));

        Files.delete(link);
        Files.delete(target);
    }
}
```

**How to run:** `java SymlinkBasic.java`

`Files.createSymbolicLink(link, target)` creates a link that points at `target`; `Files.readSymbolicLink(link)` reports exactly where it points. `Files.readAllBytes(link)` transparently follows the link and reads the real file's content, exactly as if `link` were the real file itself.

### Level 2 — Intermediate

```java
import java.nio.file.*;

public class SymlinkVsTarget {
    public static void main(String[] args) throws Exception {
        Path target = Files.createTempFile("real-file2", ".txt");
        Files.write(target, "data".getBytes());
        Path link = target.resolveSibling("shortcut2.txt");
        Files.createSymbolicLink(link, target);

        System.out.println("Is 'link' a symbolic link? " + Files.isSymbolicLink(link));
        System.out.println("Is 'target' a symbolic link? " + Files.isSymbolicLink(target));

        // exists() by default FOLLOWS symlinks -- it reports on whatever the link points to
        System.out.println("link exists (follows link): " + Files.exists(link));
        // NOFOLLOW_LINKS checks the LINK ITSELF, without following it to its target
        System.out.println("link exists (NOFOLLOW_LINKS): " + Files.exists(link, LinkOption.NOFOLLOW_LINKS));

        Files.delete(link);
        Files.delete(target);
    }
}
```

**How to run:** `java SymlinkVsTarget.java`

`Files.isSymbolicLink` correctly distinguishes `link` (a symbolic link) from `target` (an ordinary file) — with both entries currently valid, `Files.exists` reports `true` whether or not it follows the link, since the target genuinely exists either way.

### Level 3 — Advanced

```java
import java.nio.file.*;

public class SymlinkBroken {
    public static void main(String[] args) throws Exception {
        Path target = Files.createTempFile("real-file3", ".txt");
        Path link = target.resolveSibling("shortcut3.txt");
        Files.createSymbolicLink(link, target);

        System.out.println("Before deleting target:");
        System.out.println("  exists (follows link): " + Files.exists(link));
        System.out.println("  exists (NOFOLLOW_LINKS): " + Files.exists(link, LinkOption.NOFOLLOW_LINKS));

        Files.delete(target); // delete the REAL file -- the link itself is untouched, but now dangles

        System.out.println("After deleting target (link is now BROKEN):");
        System.out.println("  exists (follows link): " + Files.exists(link));
        System.out.println("  exists (NOFOLLOW_LINKS): " + Files.exists(link, LinkOption.NOFOLLOW_LINKS));
        System.out.println("  isSymbolicLink still true? " + Files.isSymbolicLink(link));

        Files.delete(link); // deleting the link itself always works, broken or not
        System.out.println("Link deleted successfully.");
    }
}
```

**How to run:** `java SymlinkBroken.java`

After `target` is deleted, `link` becomes a **broken** (or "dangling") symbolic link — it still exists as a file system entry, but points at nothing. `Files.exists(link)` (which follows the link) now correctly reports `false`, since the thing it points *to* is gone — while `Files.exists(link, LinkOption.NOFOLLOW_LINKS)` still reports `true`, since the link entry *itself* is still perfectly intact on disk.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `target` is created as an empty temporary file, and `link` is created as a symbolic link pointing at it.

The first pair of `exists` checks, before any deletion: `Files.exists(link)` follows the link to `target`, finds it present, and returns `true`. `Files.exists(link, LinkOption.NOFOLLOW_LINKS)` checks the link entry itself (without following it), and also returns `true`, since the link entry genuinely exists on disk. At this point, both checks agree, since the link is intact and points at something real.

`Files.delete(target)` removes the *real* file — but crucially, this doesn't touch `link` at all; `link` still exists as a file system entry, it just now points at a location that no longer contains anything.

The second pair of `exists` checks, after deletion: `Files.exists(link)` follows the link, tries to find `target`, discovers it's gone, and correctly returns `false` — from this method's perspective, "does this path exist" means "does the thing it ultimately resolves to exist," and the answer is now no. `Files.exists(link, LinkOption.NOFOLLOW_LINKS)`, however, checks only whether *the link entry itself* is present on disk — completely independent of whether its target exists — and still returns `true`, since the link hasn't been removed. `Files.isSymbolicLink(link)` likewise still returns `true`: the entry is still a symbolic link, regardless of whether following it leads anywhere.

Finally, `Files.delete(link)` removes the link entry itself — this succeeds regardless of whether the link was broken, since deleting a symbolic link only ever removes the link, never anything it might (or might not) point to.

Expected output (the exact temporary file paths will vary each run):
```
Before deleting target:
  exists (follows link): true
  exists (NOFOLLOW_LINKS): true
After deleting target (link is now BROKEN):
  exists (follows link): false
  exists (NOFOLLOW_LINKS): true
  isSymbolicLink still true? true
Link deleted successfully.
```

## 7. Gotchas & takeaways

> A "broken" symbolic link (one whose target no longer exists) is **not** the same as a link that doesn't exist. `Files.exists(brokenLink)` returns `false` (since it follows the link and finds nothing there), but `Files.isSymbolicLink(brokenLink)` still returns `true`, and `Files.delete(brokenLink)` still works — the link entry itself is perfectly real and present; only what it *points to* is gone. Code that checks `Files.exists` and concludes "there's nothing here to clean up" can leave broken links behind indefinitely.

- `Files.createSymbolicLink(link, target)` creates a link; `Files.readSymbolicLink(link)` reports what it points to; `Files.isSymbolicLink(path)` checks whether a path is itself a link.
- By default, most `Files` methods (`exists`, `readAllBytes`, and others) transparently follow symbolic links to their target — passing `LinkOption.NOFOLLOW_LINKS` makes the method examine the link entry itself instead.
- A broken link (target deleted or moved) still exists as a link entry on disk, even though following it fails — `exists()` without `NOFOLLOW_LINKS` will report `false` for such a link, which can mask the fact that a stray link entry is still sitting there.
- Deleting a symbolic link (`Files.delete(link)`) only ever removes the link itself, never the file or directory it points to (and works fine even if that target no longer exists).
- Be deliberate about whether your code should follow links or examine them directly — the wrong default for a given operation (accidentally following a link into an unintended location, or failing to detect a broken link) is a real and sometimes security-relevant class of bug.
