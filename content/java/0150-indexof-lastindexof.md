---
card: java
gi: 150
slug: indexof-lastindexof
title: indexOf / lastIndexOf
---

## 1. What it is

`indexOf` searches a string **from the beginning** for the first occurrence of a character or substring and returns its index, or `-1` if it isn't found anywhere. `lastIndexOf` does the same search but **from the end**, returning the index of the *last* occurrence, or `-1` if none exists. Both come in overloads accepting a single `char`, a `String`, or an additional starting index to search from.

```java
String path = "/usr/local/bin/java";

System.out.println(path.indexOf('/'));       // 0  — the very first slash
System.out.println(path.lastIndexOf('/'));   // 14 — the last slash, right before "java"
System.out.println(path.indexOf("local"));   // 5  — where the substring "local" begins
System.out.println(path.indexOf("xyz"));     // -1 — not found anywhere
```

The returned index always refers to the position of the **first character** of the match — for a substring search, `indexOf("local")` returns where `"local"` *starts*, not where it ends.

## 2. Why & when

`indexOf`/`lastIndexOf` answer "where is this?" and are the foundation for many other string operations:

- **Locating a delimiter's position** before extracting pieces with `substring` (as seen in the previous topic).
- **Checking whether a string contains something**, by testing `indexOf(...) >= 0` (equivalent to, and historically predating, the more direct `contains(...)` method).
- **Finding the last occurrence of a repeated character**, such as the last `/` in a file path (everything after it is the filename) or the last `.` in a filename (everything after it is the extension).
- **Searching from a specific starting point** using the overload that accepts a `fromIndex`, useful for finding every occurrence of a substring one at a time in a loop.

Always check the result against `-1` before using it as a `substring` boundary or array index — treating a "not found" `-1` as if it were a real position is one of the most common string-processing bugs.

## 3. Core concept

```java
public class IndexOfDemo {
    public static void main(String[] args) {
        String csv = "apple,banana,cherry,date";

        // Find every comma position by repeatedly searching from just after the last one found
        int index = csv.indexOf(',');
        while (index >= 0) {
            System.out.println("Comma at index: " + index);
            index = csv.indexOf(',', index + 1); // search starting one position past this comma
        }
    }
}
```

The loop repeatedly calls `indexOf(',', index + 1)`, each time searching only the remainder of the string *after* the previously found comma — this is the standard pattern for finding every occurrence of something, not just the first.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="IndexOf and lastIndexOf diagram: the string usr local bin java showing indexOf finding the first slash at index 0 and lastIndexOf finding the last slash at index 14, right before the filename java.">
  <rect x="8" y="8" width="684" height="134" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"/usr/local/bin/java" — indexOf('/') vs lastIndexOf('/')</text>

  <rect x="30" y="45" width="20" height="26" rx="3" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="40" y="63" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">/</text>
  <rect x="50" y="45" width="380" height="26" rx="3" fill="#1c2430" stroke="#8b949e"/>
  <text x="240" y="63" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">usr/local/bin</text>
  <rect x="430" y="45" width="20" height="26" rx="3" fill="#1c2430" stroke="#f85149" stroke-width="2.5"/>
  <text x="440" y="63" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">/</text>
  <rect x="450" y="45" width="60" height="26" rx="3" fill="#1c2430" stroke="#79c0ff"/>
  <text x="480" y="63" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">java</text>

  <text x="40" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">indexOf('/') = 0</text>
  <text x="440" y="90" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">lastIndexOf('/') = 14</text>

  <text x="350" y="120" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">indexOf scans from the start; lastIndexOf scans from the end — both return -1 if nothing matches.</text>
</svg>

`indexOf` finds the first slash (index 0); `lastIndexOf` finds the last one (index 14), which conveniently marks where the filename begins.

## 5. Runnable example

Scenario: extracting the filename and extension from a full file path — starting with a basic use of `lastIndexOf` to isolate the filename, then adding extension extraction, then hardening it against paths with no directory separator or no extension at all.

### Level 1 — Basic

```java
public class PathParseBasic {
    public static void main(String[] args) {
        String path = "/usr/local/bin/report.pdf";

        int lastSlash = path.lastIndexOf('/');
        String filename = path.substring(lastSlash + 1);

        System.out.println("Filename: " + filename);
    }
}
```

**How to run:** `java PathParseBasic.java`

`lastIndexOf('/')` finds the final slash at index 14 (right before `"report.pdf"`). `substring(lastSlash + 1)` starts one position after that slash, correctly excluding it, and runs to the end, extracting `"report.pdf"`.

### Level 2 — Intermediate

Same path parsing, now also splitting the filename into its **base name and extension**, using `lastIndexOf('.')` the same way `lastIndexOf('/')` was used above — the same pattern applied to a second delimiter.

```java
public class PathParseIntermediate {
    public static void main(String[] args) {
        String path = "/usr/local/bin/report.final.pdf";

        int lastSlash = path.lastIndexOf('/');
        String filename = path.substring(lastSlash + 1);

        int lastDot = filename.lastIndexOf('.');
        String baseName = filename.substring(0, lastDot);
        String extension = filename.substring(lastDot + 1);

        System.out.println("Filename: " + filename);
        System.out.println("Base name: " + baseName);
        System.out.println("Extension: " + extension);
    }
}
```

**How to run:** `java PathParseIntermediate.java`

`filename` ends up as `"report.final.pdf"`, which itself contains two dots. Using `lastIndexOf('.')` (rather than `indexOf('.')`) correctly finds the *final* dot, treating everything before it — including the earlier dot in `"report.final"` — as the base name, and only `"pdf"` as the extension. Using `indexOf` here instead would have incorrectly split it as base name `"report"` and extension `"final.pdf"`.

### Level 3 — Advanced

Same path parser, now defensively handling a path with **no directory separator** (a bare filename) and a filename with **no extension at all** — both cases where the corresponding `lastIndexOf` call returns `-1`, which must be checked before it's used as a `substring` boundary.

```java
public class PathParseAdvanced {

    record ParsedPath(String filename, String baseName, String extension) {}

    static ParsedPath parse(String path) {
        int lastSlash = path.lastIndexOf('/');
        String filename = (lastSlash < 0) ? path : path.substring(lastSlash + 1); // no slash: whole path IS the filename

        int lastDot = filename.lastIndexOf('.');
        String baseName = (lastDot < 0) ? filename : filename.substring(0, lastDot); // no dot: whole filename IS the base name
        String extension = (lastDot < 0) ? "" : filename.substring(lastDot + 1);      // no dot: no extension

        return new ParsedPath(filename, baseName, extension);
    }

    public static void main(String[] args) {
        String[] paths = { "/usr/local/bin/report.pdf", "README", "notes.txt", "/etc/hostname" };
        for (String path : paths) {
            ParsedPath p = parse(path);
            System.out.println(path + " -> filename=[" + p.filename() + "], base=[" + p.baseName() + "], ext=[" + p.extension() + "]");
        }
    }
}
```

**How to run:** `java PathParseAdvanced.java`

Both `lastSlash` and `lastDot` are checked against `< 0` before being used in a `substring` call — when `lastSlash` is `-1` (no `/` anywhere, as in `"README"`), the entire input is treated as the filename rather than attempting `substring(0)` on a miscalculated index; similarly, when `lastDot` is `-1` (no `.` anywhere), the whole filename becomes the base name and `extension` is simply an empty string, rather than crashing or producing a nonsensical result.

## 6. Walkthrough

Trace `parse("README")` (no `/`, no `.`):

**Finding the slash.** `path.lastIndexOf('/')` scans `"README"` and finds no `/` anywhere, returning `-1`. Since `lastSlash < 0`, the ternary sets `filename = path` directly — the entire string `"README"` is treated as the filename, with no `substring` call needed at all.

**Finding the dot.** `filename.lastIndexOf('.')` on `"README"` likewise finds no `.`, returning `-1`. Since `lastDot < 0`, `baseName = filename` (`"README"` again) and `extension = ""`.

```
path = "README"
lastIndexOf('/') -> -1  ->  filename = "README" (whole string, no substring call)
lastIndexOf('.') -> -1  ->  baseName = "README", extension = ""
```

**Final output.** For the four paths: `/usr/local/bin/report.pdf -> filename=[report.pdf], base=[report], ext=[pdf]`; `README -> filename=[README], base=[README], ext=[]`; `notes.txt -> filename=[notes.txt], base=[notes], ext=[txt]`; `/etc/hostname -> filename=[hostname], base=[hostname], ext=[]` (a slash exists, but no dot, so the extension is empty).

## 7. Gotchas & takeaways

> **Both `indexOf` and `lastIndexOf` return `-1`, not an exception, when nothing matches** — this is convenient (no `try`/`catch` needed) but also dangerous if the `-1` is used directly as a `substring` index without checking, since that produces either a confusing exception or, worse, a wrong result that happens not to crash.

> **`indexOf` finds the first occurrence; `lastIndexOf` finds the last — mixing them up silently produces the wrong split point for strings with multiple occurrences of the delimiter**, such as a filename with more than one dot, or a path with nested directories.

- `indexOf`/`lastIndexOf` return the index of a match, or `-1` if there is none — always check for `-1` before using the result.
- Use `lastIndexOf` when you want the *final* occurrence (file extensions, the last path segment); use `indexOf` for the *first* (as in the earlier config-line parsing example).
- The overload accepting a starting index (`indexOf(char, fromIndex)`) lets you find every occurrence of something by repeatedly searching past the last match found.
- A `-1` result is not an error on its own — it's valid information ("not found") that your code must explicitly check for and handle, typically with a different code path than a successful match.
