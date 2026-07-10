---
card: java
gi: 1006
slug: composite
title: Composite
---

## 1. What it is

The **Composite** pattern composes objects into tree structures to represent part-whole hierarchies, letting client code treat an individual object and a group of objects **through the same interface**. A file (a "leaf") and a folder full of files and other folders (a "composite") both expose the same operations — like `getSize()` — so calling code can ask a single file or an entire folder tree for its size without caring which one it's actually holding.

## 2. Why & when

Without Composite, code that processes a mix of individual items and groups of items needs to constantly check "is this a single thing or a collection?" and branch accordingly — that branching multiplies at every level of nesting a hierarchy can have. Composite exists to let a leaf and a container share one interface, so a container can implement its own version of an operation (like `getSize()`) by simply asking each of its children — leaf or container — for their own size and summing them, recursively, with no special-casing needed anywhere in the client code.

Reach for Composite whenever your data is naturally tree-shaped — file systems, UI component hierarchies (a panel containing buttons and other panels), organizational charts — and you want to run the same operation uniformly across a single item or an entire subtree. It's unnecessary for flat, non-hierarchical collections; a plain list and a loop cover that case without needing a shared leaf/composite interface.

## 3. Core concept

```
interface FileSystemNode { long getSize(); }

// Leaf: a single file
class File implements FileSystemNode {
    private final long size;
    File(long size) { this.size = size; }
    public long getSize() { return size; }
}

// Composite: a folder holding a MIX of files and other folders
class Folder implements FileSystemNode {
    private final java.util.List<FileSystemNode> children = new java.util.ArrayList<>();
    void add(FileSystemNode node) { children.add(node); }

    public long getSize() {
        long total = 0;
        for (FileSystemNode child : children) {
            total += child.getSize(); // works whether child is a File OR another Folder
        }
        return total;
    }
}

Folder root = new Folder();
root.add(new File(100));
Folder subfolder = new Folder();
subfolder.add(new File(50));
root.add(subfolder); // a Folder can contain another Folder
System.out.println(root.getSize()); // 150 -- no special-casing needed anywhere
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Folder tree with File leaves and nested Folder composites, each node exposing the same getSize method">
  <rect x="260" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Folder (root)</text>

  <rect x="100" y="100" width="100" height="36" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="150" y="123" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">File (100)</text>

  <rect x="260" y="100" width="120" height="36" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="123" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Folder (sub)</text>

  <rect x="450" y="160" width="100" height="36" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="500" y="183" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">File (50)</text>

  <line x1="280" y1="60" x2="170" y2="100" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="320" y1="60" x2="320" y2="100" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="340" y1="136" x2="490" y2="160" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every node — leaf `File` or composite `Folder` — implements the same `FileSystemNode` interface, so `getSize()` recurses uniformly through the whole tree.

## 5. Runnable example

Scenario: a file-system size calculator, evolving from type-checking, special-cased code into a uniform composite tree that handles arbitrarily deep nesting with no special-casing at all.

### Level 1 — Basic

```java
// File: CompositeBasic.java
import java.util.ArrayList;
import java.util.List;

class File {
    private final long size;
    File(long size) { this.size = size; }
    long getSize() { return size; }
}

class Folder {
    private final List<File> files = new ArrayList<>();
    void add(File file) { files.add(file); }
    long getSize() {
        long total = 0;
        for (File f : files) total += f.getSize();
        return total;
    }
}

public class CompositeBasic {
    public static void main(String[] args) {
        Folder root = new Folder();
        root.add(new File(100));
        root.add(new File(200));
        System.out.println("root size: " + root.getSize());
    }
}
```

**How to run:** save as `CompositeBasic.java`, then `javac CompositeBasic.java && java CompositeBasic` (JDK 17+).

Expected output:
```
root size: 300
```

This `Folder` can only hold `File` objects directly — there's no way for a folder to contain another folder, so any real file-system hierarchy (which nests arbitrarily) can't be represented at all yet.

### Level 2 — Intermediate

```java
// File: CompositeIntermediate.java
import java.util.ArrayList;
import java.util.List;

interface FileSystemNode {
    long getSize();
}

class File implements FileSystemNode {
    private final long size;
    File(long size) { this.size = size; }
    public long getSize() { return size; }
}

class Folder implements FileSystemNode {
    private final List<FileSystemNode> children = new ArrayList<>();
    void add(FileSystemNode node) { children.add(node); }

    public long getSize() {
        long total = 0;
        for (FileSystemNode child : children) {
            total += child.getSize(); // works uniformly for a File OR a nested Folder
        }
        return total;
    }
}

public class CompositeIntermediate {
    public static void main(String[] args) {
        Folder root = new Folder();
        root.add(new File(100));

        Folder subfolder = new Folder();
        subfolder.add(new File(50));
        subfolder.add(new File(25));
        root.add(subfolder); // a Folder inside a Folder -- now possible

        System.out.println("root size: " + root.getSize());
    }
}
```

**How to run:** save as `CompositeIntermediate.java`, then `javac CompositeIntermediate.java && java CompositeIntermediate` (JDK 17+).

Expected output:
```
root size: 175
```

The real-world concern added: `Folder` and `File` both implement `FileSystemNode`, so a `Folder` can hold a mix of files and other folders. `getSize()` recurses naturally into nested folders with no special-casing — the same loop body handles both leaf and composite children.

### Level 3 — Advanced

```java
// File: CompositeAdvanced.java
import java.util.ArrayList;
import java.util.List;

interface FileSystemNode {
    long getSize();
    void print(String indent);
}

class File implements FileSystemNode {
    private final String name;
    private final long size;
    File(String name, long size) { this.name = name; this.size = size; }
    public long getSize() { return size; }
    public void print(String indent) {
        System.out.println(indent + "- " + name + " (" + size + " bytes)");
    }
}

class Folder implements FileSystemNode {
    private final String name;
    private final List<FileSystemNode> children = new ArrayList<>();
    Folder(String name) { this.name = name; }
    void add(FileSystemNode node) { children.add(node); }

    public long getSize() {
        long total = 0;
        for (FileSystemNode child : children) total += child.getSize();
        return total;
    }

    public void print(String indent) {
        System.out.println(indent + "+ " + name + "/ (" + getSize() + " bytes total)");
        for (FileSystemNode child : children) {
            child.print(indent + "  "); // recurse -- works uniformly for File or Folder
        }
    }
}

public class CompositeAdvanced {
    public static void main(String[] args) {
        Folder root = new Folder("root");
        root.add(new File("readme.txt", 100));

        Folder src = new Folder("src");
        src.add(new File("Main.java", 500));
        src.add(new File("Utils.java", 300));

        Folder docs = new Folder("docs");
        docs.add(new File("guide.md", 200));
        src.add(docs); // a Folder nested inside another Folder, arbitrarily deep

        root.add(src);

        root.print("");
        System.out.println("TOTAL: " + root.getSize());
    }
}
```

**How to run:** save as `CompositeAdvanced.java`, then `javac CompositeAdvanced.java && java CompositeAdvanced` (JDK 17+).

Expected output:
```
+ root/ (1100 bytes total)
  - readme.txt (100 bytes)
  + src/ (1000 bytes total)
    - Main.java (500 bytes)
    - Utils.java (300 bytes)
    + docs/ (200 bytes total)
      - guide.md (200 bytes)
TOTAL: 1100
```

The production-flavored hard case: `docs` is nested three levels deep (`root` → `src` → `docs` → `guide.md`), and both `getSize()` and `print()` handle this arbitrary depth correctly with the exact same recursive logic used for one level of nesting — no code anywhere needed to change to support deeper trees.

## 6. Walkthrough

Tracing `root.print("")` in `CompositeAdvanced.main`:

1. `root.print("")` runs `Folder.print`: it first calls `getSize()` on itself to print the header line, then prints `"+ root/ (1100 bytes total)"`.
2. It loops over `root`'s children: `readme.txt` (a `File`) and `src` (a `Folder`). For `readme.txt`, `child.print("  ")` dispatches to `File.print`, printing `"  - readme.txt (100 bytes)"`.
3. For `src`, `child.print("  ")` dispatches to `Folder.print` again (recursion) — it computes its own `getSize()` (`500 + 300 + 200 = 1000`) and prints `"  + src/ (1000 bytes total)"`.
4. Inside that recursive call, `src`'s own loop runs over its children: `Main.java` and `Utils.java` print as leaf files with two extra levels of indent, then `docs` (a nested `Folder`) triggers *another* level of recursion.
5. Inside `docs.print`, its `getSize()` is `200` (just `guide.md`), so it prints `"+ docs/ (200 bytes total)"` at four spaces of indent, then loops over its one child, `guide.md`, printing it as a leaf at six spaces of indent.
6. As the recursive calls unwind back up, `root.getSize()` (called separately, in `main`, after `print` returns) recomputes the same total from scratch by walking the tree again: `readme.txt` (100) + `src`'s total (500 + 300 + `docs`'s total of 200 = 1000) = `1100`, printed as `"TOTAL: 1100"` — matching the header line that was printed for `root` at the very top.

## 7. Gotchas & takeaways

> **Gotcha:** a naive `getSize()` recomputes the total by walking the whole subtree every time it's called — as seen here, `root.print` calls `getSize()` internally at every folder level, and `main` calls `root.getSize()` again separately afterward, redoing the same traversal. For large or frequently-queried trees, caching the computed size (invalidated when children change) avoids repeated full-tree walks.

- Composite lets a leaf (`File`) and a container of leaves/containers (`Folder`) share one interface, so client code treats a single item and an entire subtree identically.
- The composite's implementation of each operation typically just delegates to each child and combines the results — recursion handles arbitrary nesting depth for free.
- It's the natural fit for genuinely tree-shaped data: file systems, UI widget hierarchies, org charts, expression trees.
- Don't reach for Composite for flat, non-hierarchical collections — a plain `List` and a loop is simpler when there's no part-whole nesting to represent.
- Recomputing an aggregate value (like total size) on every call can get expensive for large trees queried often; caching with invalidation is the usual fix once that becomes a measured problem.
- Composite is frequently combined with [Iterator](1011-iterator.md) to traverse the tree without exposing its internal structure to client code.
