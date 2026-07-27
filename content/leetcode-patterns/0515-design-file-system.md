---
card: leetcode-patterns
gi: 515
slug: design-file-system
title: Design File System
---

## 1. What it is

Design a file system supporting `createPath(path, value)` (creates a new path with the given value, failing if the parent path does not already exist or the path itself already exists) and `get(path)` (returns the value at a path, or `-1` if it does not exist). Paths look like `"/a"`, `"/a/b"`, using `/` as a separator. Example: `createPath("/a", 1)` → `true`; `createPath("/a/b", 2)` → `true`; `get("/a/b")` → `2`; `createPath("/c/d", 5)` → `false` (parent `/c` does not exist).

## 2. Why & when

A file system's directory structure is naturally a tree where each edge is a path segment (not a single character) — a trie where each "character" is an entire segment between slashes, rather than one letter. This is the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family applied with a coarser alphabet: segments instead of characters. Constraints: up to 10,000 calls total, path segments made of lowercase letters.

## 3. Core concept

**Key idea:** use a `Map<String, TrieNode>` for children instead of a fixed array, since path segments are arbitrary strings, not single characters. Each node stores a `value` (or a sentinel indicating "no value set here yet"). `createPath` splits the path by `/`, walks down segment by segment, and requires that every segment except the last already exists (the parent must be present) while the last segment must **not** already exist.

**Steps:**
1. Split `path` by `/` into segments (the leading empty string before the first `/` is discarded).
2. Walk from the root through every segment except the last, using the existing `children` map — if any of these intermediate segments is missing, the parent path does not exist, so return `false`.
3. Check the last segment: if it already exists as a child, the path already exists, so return `false`.
4. Otherwise, create a new node for the last segment, store `value` there, and return `true`.
5. `get(path)`: split by `/`, walk every segment; if any is missing, return `-1`; otherwise return the final node's stored value.

**Why the parent-must-exist rule maps naturally to "no missing intermediate node":** a valid file path can only be created if its containing directory already exists — walking segment by segment and failing as soon as an intermediate node is missing directly encodes "you cannot create `/a/b/c` before `/a/b` exists," without any extra bookkeeping.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A trie where each edge is a whole path segment rather than a single character">
  <g font-family="sans-serif" font-size="13">
    <circle cx="350" cy="20" r="15" fill="#161b22" stroke="#79c0ff"/>
    <text x="350" y="25" fill="#e6edf3" text-anchor="middle" font-size="10">root</text>
    <line x1="350" y1="35" x2="350" y2="65" stroke="#8b949e"/>
    <text x="365" y="55" fill="#8b949e" font-size="11">"a"</text>
    <circle cx="350" cy="80" r="15" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="85" fill="#e6edf3" text-anchor="middle" font-size="10">value=1</text>
    <line x1="350" y1="95" x2="350" y2="125" stroke="#8b949e"/>
    <text x="365" y="115" fill="#8b949e" font-size="11">"b"</text>
    <circle cx="350" cy="140" r="15" fill="#161b22" stroke="#3fb950"/>
    <text x="350" y="145" fill="#e6edf3" text-anchor="middle" font-size="10">value=2</text>
  </g>
</svg>

`createPath("/c/d", 5)` fails because no `"c"` child exists under the root — the parent segment is missing.

## 5. Runnable example

```java
// FileSystem.java
import java.util.*;

public class FileSystem {

    static class TrieNode {
        Map<String, TrieNode> children = new HashMap<>();
        int value = -1;
    }

    private final TrieNode root = new TrieNode();

    public boolean createPath(String path, int value) {
        String[] segments = path.split("/");
        TrieNode node = root;

        // walk every segment except the last; the parent must already exist
        for (int i = 1; i < segments.length - 1; i++) {
            node = node.children.get(segments[i]);
            if (node == null) return false;
        }

        String last = segments[segments.length - 1];
        if (node.children.containsKey(last)) return false; // path already exists

        TrieNode newNode = new TrieNode();
        newNode.value = value;
        node.children.put(last, newNode);
        return true;
    }

    public int get(String path) {
        String[] segments = path.split("/");
        TrieNode node = root;
        for (int i = 1; i < segments.length; i++) {
            node = node.children.get(segments[i]);
            if (node == null) return -1;
        }
        return node.value;
    }

    public static void main(String[] args) {
        FileSystem fs = new FileSystem();
        System.out.println(fs.createPath("/a", 1));      // true
        System.out.println(fs.createPath("/a/b", 2));    // true
        System.out.println(fs.get("/a/b"));              // 2
        System.out.println(fs.createPath("/c/d", 5));    // false (parent /c missing)
        System.out.println(fs.createPath("/a", 3));      // false (already exists)
        System.out.println(fs.get("/c"));                // -1
    }
}
```

**How to run:** save as `FileSystem.java`, then run `java FileSystem.java`.

## 6. Walkthrough

Trace `createPath("/c/d", 5)`. Segments after splitting `"/c/d"` by `/`: `["", "c", "d"]` (the leading empty string is discarded by the loop starting at index 1).

| step | node | check | result |
|---|---|---|---|
| walk segment "c" (index 1, not the last) | root | `root.children.get("c")` | `null` — parent "c" does not exist |

Since the intermediate segment "c" is missing, the method returns `false` immediately, without ever checking the last segment "d".

## 7. Gotchas & takeaways

> Gotcha: using a fixed-size `children[26]` array (as in a character-based trie) does not work here, since path segments are whole strings, not single characters — a `Map<String, TrieNode>` is required instead.

- This is a trie where each edge represents a full path segment, not a single character — the same tree-of-prefixes idea from [Implement Trie](0508-implement-trie-prefix-tree.md), generalized to a coarser unit.
- `createPath` must check that every segment up to the second-to-last already exists, and that the last segment does not yet exist.
- Time: O(path segment count) per `createPath` or `get` call, independent of how many other paths exist.
