---
card: leetcode-patterns
gi: 594
slug: design-in-memory-file-system
title: Design In-Memory File System
---

## 1. What it is

Design a `FileSystem` class modeling a simplified in-memory file system. `ls(path)` returns a sorted list of contents: if `path` is a file, a one-element list with just its name; if a directory, a sorted list of its immediate children's names. `mkdir(path)` creates all missing directories along `path`. `addContentToFile(filePath, content)` creates the file (and any missing parent directories) if it does not exist, then appends `content` to it. `readContentFromFile(filePath)` returns the file's full stored content. Example: `mkdir("/a/b/c")`, `addContentToFile("/a/b/c/d", "hello")`, `ls("/")` → `["a"]`, `readContentFromFile("/a/b/c/d")` → `"hello"`.

## 2. Why & when

A file system is naturally a **tree**: directories are internal nodes with named children, files are leaf nodes holding content. Recognize this signal whenever a problem involves hierarchical paths (`/a/b/c`) with operations that create, list, or read nodes along that hierarchy — the natural structure is a tree of nodes, each holding a `HashMap<name, childNode>` for its children (giving O(1) lookup by name at each level) plus a flag or content field distinguishing a file from a directory.

## 3. Core concept

**Key idea:** each node in the tree is either a directory (holding a `TreeMap<String, Node>` of named children, kept sorted for `ls`) or a file (holding a `String content`). Every path operation starts at a shared `root` node and walks the path's components one directory level at a time, creating missing directories as needed (for `mkdir` and `addContentToFile`) or simply traversing (for `ls` and `readContentFromFile`).

**Steps:**
1. **Parse a path:** split `"/a/b/c"` on `"/"`, discarding empty segments (the leading `/` produces one), giving `["a", "b", "c"]`.
2. `mkdir(path)`: starting at `root`, for each component, look it up in the current node's children map; if missing, create a new directory node and insert it; move into it. Repeat for every component.
3. `addContentToFile(filePath, content)`: walk to the parent directory of the file (all components except the last), creating missing directories along the way, exactly like `mkdir`. At the last component, if the child does not exist, create a new file node with empty content. Append `content` to that file node's stored content.
4. `readContentFromFile(filePath)`: walk to the file node (all components), then return its stored content directly.
5. `ls(path)`: walk to the node at `path`. If it is a file, return a single-element list of just its own name (the last path component). If it is a directory, return a sorted list of its children's names (a `TreeMap`'s keys are already sorted).

**Why the same "walk, creating missing directories" logic is shared by `mkdir` and `addContentToFile`:** both operations need every intermediate directory along the path to exist before they can do their final step (stopping at the last directory, or creating a file). Factoring this shared walk into one helper avoids duplicating the creation logic and keeps both methods correct in the same way.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A tree of directory and file nodes; each directory holds a sorted map of named children">
  <g font-family="sans-serif" font-size="12">
    <rect x="300" y="20" width="80" height="35" rx="4" fill="#161b22" stroke="#3fb950"/><text x="340" y="42" fill="#e6edf3" text-anchor="middle" font-size="11">/ (root)</text>
    <rect x="300" y="80" width="80" height="35" rx="4" fill="#161b22" stroke="#3fb950"/><text x="340" y="102" fill="#e6edf3" text-anchor="middle" font-size="11">a (dir)</text>
    <line x1="340" y1="55" x2="340" y2="80" stroke="#8b949e"/>
    <rect x="300" y="140" width="80" height="35" rx="4" fill="#161b22" stroke="#3fb950"/><text x="340" y="162" fill="#e6edf3" text-anchor="middle" font-size="11">b (dir)</text>
    <line x1="340" y1="115" x2="340" y2="140" stroke="#8b949e"/>
    <rect x="450" y="140" width="90" height="35" rx="4" fill="#161b22" stroke="#f0883e"/><text x="495" y="162" fill="#e6edf3" text-anchor="middle" font-size="11">d (file: "hello")</text>
    <line x1="380" y1="157" x2="450" y2="157" stroke="#8b949e"/>
  </g>
</svg>

Each directory node's children map is walked one segment at a time — a file node is a leaf that stops the walk and holds content instead of further children.

## 5. Runnable example

**Level 1 — Brute force.** Store every full path string directly in a `HashMap<String, String>` (path to content), and reconstruct directory listings by string-matching prefixes on every `ls` call. Works, but `ls` becomes O(all paths) per call, and there is no real tree structure to reason about.

**KEY INSIGHT:** representing the file system as an actual tree — one node per path component, not one entry per full path — makes each operation proportional only to the path's own depth, and `ls` naturally reads directly off a node's already-sorted children map.

**Level 2 — Optimal.** Tree of `Node` objects, each a `TreeMap<String, Node>` (directory) or a content string (file), walked one path component at a time.

**Level 3 — Hardened.** Correctly distinguishes a file node from a directory node in `ls` (returning the file's own name, not its non-existent children), and correctly appends (not overwrites) on repeated `addContentToFile` calls to the same file.

```java
// FileSystem.java
import java.util.*;

public class FileSystem {

    static class Node {
        boolean isFile = false;
        String content = "";
        TreeMap<String, Node> children = new TreeMap<>();
    }

    private final Node root = new Node();

    private List<String> splitPath(String path) {
        List<String> parts = new ArrayList<>();
        for (String p : path.split("/")) {
            if (!p.isEmpty()) parts.add(p);
        }
        return parts;
    }

    private Node walkOrCreateDirs(List<String> parts) {
        Node cur = root;
        for (String part : parts) {
            cur = cur.children.computeIfAbsent(part, k -> new Node());
        }
        return cur;
    }

    public List<String> ls(String path) {
        List<String> parts = splitPath(path);
        Node cur = walkOrCreateDirs(parts); // walk to the target node
        if (cur.isFile) {
            return Collections.singletonList(parts.get(parts.size() - 1));
        }
        return new ArrayList<>(cur.children.keySet());
    }

    public void mkdir(String path) {
        walkOrCreateDirs(splitPath(path));
    }

    public void addContentToFile(String filePath, String content) {
        List<String> parts = splitPath(filePath);
        String fileName = parts.remove(parts.size() - 1);
        Node parent = walkOrCreateDirs(parts);
        Node file = parent.children.computeIfAbsent(fileName, k -> new Node());
        file.isFile = true;
        file.content += content;
    }

    public String readContentFromFile(String filePath) {
        List<String> parts = splitPath(filePath);
        Node cur = walkOrCreateDirs(parts);
        return cur.content;
    }

    public static void main(String[] args) {
        FileSystem fs = new FileSystem();
        fs.mkdir("/a/b/c");
        fs.addContentToFile("/a/b/c/d", "hello");
        System.out.println(fs.ls("/"));                       // [a]
        System.out.println(fs.readContentFromFile("/a/b/c/d")); // hello
        System.out.println(fs.ls("/a/b/c"));                   // [d]
    }
}
```

**How to run:** save as `FileSystem.java`, then run `java FileSystem.java`.

## 6. Walkthrough

Trace `mkdir("/a/b/c")`, `addContentToFile("/a/b/c/d", "hello")`, `ls("/")`:

1. `mkdir("/a/b/c")`: `splitPath` gives `["a","b","c"]`. Starting at `root`, `computeIfAbsent("a", ...)` creates a new directory node for `a`; move into it. Repeat for `b`, then `c`. Tree: `root -> a -> b -> c`.
2. `addContentToFile("/a/b/c/d", "hello")`: `parts = ["a","b","c","d"]`; pop `fileName = "d"`, leaving `["a","b","c"]`. Walk to that directory (already exists from step 1, so `computeIfAbsent` just returns the existing nodes). At `c`, `computeIfAbsent("d", ...)` creates a new node for `d`; mark it `isFile=true`; append `"hello"` to its content.
3. `ls("/")`: `parts = []`. Walk with an empty list returns `root` itself. `root.isFile` is `false`, so return `root.children.keySet()` — a `TreeMap`, sorted — which is `["a"]`.

## 7. Gotchas & takeaways

> Gotcha: using `file.content = content` (overwrite) instead of `file.content += content` (append) in `addContentToFile` breaks the second and later calls to the same file — the problem specifies content is appended across multiple calls, not replaced.

- Signal: hierarchical, path-based create/list/read operations are a tree-of-named-children signal — model each path segment as one level of the tree, not each full path as a flat map key.
- A `TreeMap` for each directory's children keeps `ls` O(children count) with no extra sorting step, since keys are always maintained in sorted order.
- Related problems: Design HashMap / Design HashSet (a simpler, single-level version of "build a lookup structure from scratch"), Design Browser History (a different, linear rather than tree-shaped, navigation structure).
