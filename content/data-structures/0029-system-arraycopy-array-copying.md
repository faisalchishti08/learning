---
card: data-structures
gi: 29
slug: system-arraycopy-array-copying
title: System.arraycopy & array copying
---

## 1. What it is

`System.arraycopy(src, srcPos, dest, destPos, length)` is a low-level, native method that copies a range of elements from one array into another (or into a different position within the same array). It is the building block every higher-level copy method — `Arrays.copyOf`, `clone()`, `ArrayList`'s internal resize — is implemented on top of.

## 2. Why & when

Use `System.arraycopy` directly when you need precise control over source and destination positions and lengths, or maximum performance in a tight loop — it runs as a JVM intrinsic, typically far faster than a manual `for` loop copying element by element. Use `Arrays.copyOf`/`copyOfRange` (built on top of it) when you just want "give me a new array with this content," since they are more concise for that common case.

## 3. Core concept

**The five arguments, in order.** `System.arraycopy(src, srcPos, dest, destPos, length)`: copy `length` elements starting at index `srcPos` in `src`, writing them starting at index `destPos` in `dest`. Both `src` and `dest` must already exist — `arraycopy` never allocates a new array itself, unlike `Arrays.copyOf`.

**Why it is fast: it is a native, block-level operation.** Rather than looping in Java bytecode, `arraycopy` is implemented natively (often compiling to a single memory-block-move instruction), so it avoids per-element loop overhead and JVM bounds-checking on every iteration.

**It safely handles overlapping ranges within the same array.** Copying a range to an overlapping destination *within the same array* (e.g., shifting elements right to make room for an insertion) is handled correctly — `arraycopy` behaves as if it copied the source range to a temporary area first, so overlapping source and destination never corrupts data, unlike a naive forward-copying loop would in some overlap cases.

**Copying is always shallow.** For an array of objects, `arraycopy` copies the references, not the objects they point to — both the source and destination arrays end up referencing the exact same underlying objects.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="System.arraycopy moving three elements from one position in a source array to a different position in a destination array">
  <g font-family="sans-serif" font-size="11">
    <text x="160" y="18" fill="#8b949e" text-anchor="middle">src (srcPos=1, length=3)</text>
    <rect x="30" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="50" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">a</text>
    <rect x="70" y="30" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="90" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">b</text>
    <rect x="110" y="30" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="130" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">c</text>
    <rect x="150" y="30" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="170" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">d</text>
    <rect x="190" y="30" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="210" y="47" fill="#e6edf3" text-anchor="middle" font-size="9">e</text>

    <text x="450" y="18" fill="#8b949e" text-anchor="middle">dest (destPos=2, length=3)</text>
    <rect x="380" y="90" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="400" y="107" fill="#e6edf3" text-anchor="middle" font-size="9">x</text>
    <rect x="420" y="90" width="40" height="26" fill="#161b22" stroke="#8b949e"/><text x="440" y="107" fill="#e6edf3" text-anchor="middle" font-size="9">x</text>
    <rect x="460" y="90" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="480" y="107" fill="#e6edf3" text-anchor="middle" font-size="9">b</text>
    <rect x="500" y="90" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="520" y="107" fill="#e6edf3" text-anchor="middle" font-size="9">c</text>
    <rect x="540" y="90" width="40" height="26" fill="#0d1117" stroke="#3fb950"/><text x="560" y="107" fill="#e6edf3" text-anchor="middle" font-size="9">d</text>

    <line x1="130" y1="60" x2="480" y2="86" stroke="#79c0ff" stroke-dasharray="3,3"/>
    <text x="320" y="150" fill="#79c0ff" text-anchor="middle">arraycopy(src, 1, dest, 2, 3) -- moves b,c,d into dest starting at index 2</text>
  </g>
</svg>

Three elements starting at `src[1]` land at `dest[2]`. The positions and length are fully independent of the surrounding array contents.

## 5. Runnable example

```java
// SystemArraycopyExample.java
import java.util.Arrays;

public class SystemArraycopyExample {

    // Basic: copy a range from one array into a different, pre-existing array.
    static void basicLevel() {
        char[] src = {'a', 'b', 'c', 'd', 'e'};
        char[] dest = {'x', 'x', 'x', 'x', 'x'};
        System.arraycopy(src, 1, dest, 2, 3); // copy 'b','c','d' into dest starting at index 2
        System.out.println("basic: dest after copy -> " + new String(dest));
    }

    // Intermediate: copying within the SAME array, with overlapping source and destination ranges.
    static void intermediateLevel() {
        int[] arr = {1, 2, 3, 4, 5, 0, 0};
        // shift elements at indices 0..4 right by 2, to open a gap for insertion at the front
        System.arraycopy(arr, 0, arr, 2, 5);
        arr[0] = 100;
        arr[1] = 200;
        System.out.println("intermediate: shifted in place -> " + Arrays.toString(arr));
    }

    // Advanced: arraycopy is shallow -- copied object-array slots still reference the SAME objects.
    static void advancedLevel() {
        StringBuilder sb = new StringBuilder("shared");
        StringBuilder[] src = {sb, new StringBuilder("unique")};
        StringBuilder[] dest = new StringBuilder[2];
        System.arraycopy(src, 0, dest, 0, 2);

        dest[0].append("-mutated"); // mutates the object, which src[0] also points to
        System.out.println("advanced: src[0] after mutating dest[0] -> " + src[0]);
        System.out.println("advanced: same object? -> " + (src[0] == dest[0]));
    }

    public static void main(String[] args) {
        basicLevel();
        intermediateLevel();
        advancedLevel();
    }
}
```

**How to run:** save as `SystemArraycopyExample.java`, then run `java SystemArraycopyExample.java`.

## 6. Walkthrough

1. `basicLevel()` copies 3 characters (`'b','c','d'`, starting at `src[1]`) into `dest`, landing them at indices 2, 3, and 4 — `dest` becomes `"xxbcd"`, while `src` is untouched (it is only the source, never modified).
2. `intermediateLevel()` copies from `arr` back into `arr` itself, at an overlapping destination 2 slots to the right. `arraycopy` correctly reads the whole source range before writing, so `{1,2,3,4,5}` correctly ends up at indices `2..6`, without the earlier writes corrupting later reads.
3. Setting `arr[0]` and `arr[1]` afterward fills the "opened" gap at the front — this is the same underlying technique `insertAt` used in [Insert / delete shifting cost](0019-insert-delete-shifting-cost.md), now shown using the real JDK method instead of a manual loop.
4. `advancedLevel()` copies an array of `StringBuilder` references. Because the copy is shallow, `dest[0]` and `src[0]` end up pointing at the *same* `StringBuilder` object — mutating through `dest[0]` is visible through `src[0]`, and `src[0] == dest[0]` prints `true`.

## 7. Gotchas & takeaways

> Gotcha: `System.arraycopy` never allocates a destination array — both `src` and `dest` must already exist with enough room, or it throws `ArrayIndexOutOfBoundsException`. If you need a brand-new array of the right size, use `Arrays.copyOf` instead, which allocates for you before delegating to `arraycopy` internally.

- `System.arraycopy` is the fast, native primitive that copies a range between two existing arrays (or within the same array), and every higher-level copy utility is built on it.
- It correctly handles overlapping source/destination ranges within the same array, unlike a naive forward-copying loop.
- The copy is always shallow — for object arrays, both arrays end up referencing the same underlying objects.
- Related concepts: [Arrays utility class](0028-arrays-utility-class-sort-fill-copyof-binarysearch.md) (built on top of `arraycopy`), [Insert / delete shifting cost](0019-insert-delete-shifting-cost.md).
