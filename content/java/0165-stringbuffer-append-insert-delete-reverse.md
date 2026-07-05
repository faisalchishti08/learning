---
card: java
gi: 165
slug: stringbuffer-append-insert-delete-reverse
title: StringBuffer append/insert/delete/reverse
---

## 1. What it is

`StringBuffer` provides a core set of mutating methods that modify its internal character sequence in place: `append(...)` adds content to the end, `insert(int offset, ...)` inserts content at a specific position (shifting everything after it to the right), `delete(int start, int end)` removes a range of characters (`end` exclusive, like `substring`), and `reverse()` flips the entire sequence's order. All of these return the *same* `StringBuffer` object (`this`), which is what enables method chaining.

```java
StringBuffer sb = new StringBuffer("Hello World");

sb.insert(5, ",");           // "Hello, World" — inserted at index 5, everything after shifts right
sb.append("!");               // "Hello, World!" — added to the end
sb.delete(0, 6);               // "World!" — removes indices 0 through 5 (6 exclusive)
sb.reverse();                   // "!dlroW" — entire sequence reversed in place

System.out.println(sb);
```

Each method call mutates `sb` directly and also returns `sb` itself, so calls can be chained: `sb.append("a").append("b").insert(0, "c")` reads left to right as a sequence of in-place mutations, each acting on the buffer's state as left by the previous call.

## 2. Why & when

These four methods cover the vast majority of what incremental, mutable text building needs to do:

- **`append`** — the single most common operation, used for building output piece by piece in a loop, exactly as seen in the earlier `StringBuffer` overview.
- **`insert`** — adding content at a specific known position, without needing to manually split the buffer into "before" and "after" pieces yourself.
- **`delete`** — removing an unwanted range of characters, such as trimming a trailing separator that was added one time too many by a loop.
- **`reverse`** — flipping the entire sequence, useful for certain algorithms (palindrome checks, digit-reversal) directly on a mutable buffer rather than manually swapping indices in a `char[]`.

Because all of these mutate in place and return `this`, they compose naturally through chaining — a sequence of edits reads as one fluent expression, rather than requiring a new variable for each intermediate step the way equivalent `String` operations would.

## 3. Core concept

```java
public class BufferMethodsDemo {
    public static void main(String[] args) {
        StringBuffer sb = new StringBuffer();

        sb.append("Item A").append(", ").append("Item B").append(", ").append("Item C");
        System.out.println(sb); // "Item A, Item B, Item C"

        sb.delete(sb.length() - 2, sb.length()); // remove the trailing ", Item C"... actually just the last 2 chars
        // careful: this only removes the LAST 2 characters, not a whole trailing item — see the runnable example

        sb.insert(0, "[").append("]");
        System.out.println(sb);
    }
}
```

`sb.length()` is queried live, right before the `delete` call, so `sb.length() - 2` always refers to "2 characters before the current end," regardless of how much content has accumulated so far — this is a common, useful pattern precisely because `StringBuffer`'s length changes as you build it.

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="StringBuffer methods diagram: starting from Hello World, insert adds a comma at index 5 shifting later characters right, append adds an exclamation mark at the end, delete removes the first six characters, and reverse flips the remaining characters end to end." >
  <rect x="8" y="8" width="684" height="149" rx="8" fill="#0d1117"/>
  <text x="350" y="22" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">"Hello World" -&gt; insert(5,",") -&gt; append("!") -&gt; delete(0,6) -&gt; reverse()</text>

  <rect x="30" y="40" width="140" height="24" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="100" y="56" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="monospace">"Hello World"</text>

  <rect x="190" y="40" width="150" height="24" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="56" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="monospace">"Hello, World"</text>

  <rect x="360" y="40" width="150" height="24" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="435" y="56" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="monospace">"Hello, World!"</text>

  <rect x="530" y="40" width="110" height="24" rx="4" fill="#1c2430" stroke="#f85149"/>
  <text x="585" y="56" fill="#f85149" font-size="8.5" text-anchor="middle" font-family="monospace">"World!"</text>

  <rect x="270" y="90" width="110" height="24" rx="4" fill="#1c2430" stroke="#e6edf3" stroke-width="2"/>
  <text x="325" y="106" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="monospace">"!dlroW"</text>

  <path d="M 585 64 L 460 88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="480" y="80" fill="#8b949e" font-size="7.5" font-family="sans-serif">reverse()</text>

  <text x="350" y="135" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">Each step mutates the SAME buffer object in place — no new object is created at any stage.</text>
</svg>

Four operations, each mutating one continuously-evolving buffer object, chained left to right.

## 5. Runnable example

Scenario: building a comma-separated list from a collection of items, correctly handling the "trailing separator" problem — starting with a basic version that has the classic trailing-comma bug, then fixing it with `delete`, then hardening it into a reusable, reversible list-builder that also demonstrates `insert` for adding a prefix after the fact.

### Level 1 — Basic (the trailing-comma bug, shown deliberately)

```java
public class ListBuildBuggy {
    public static void main(String[] args) {
        String[] items = { "apple", "banana", "cherry" };
        StringBuffer sb = new StringBuffer();

        for (String item : items) {
            sb.append(item).append(", "); // adds a trailing ", " even after the LAST item
        }

        System.out.println("[" + sb + "]"); // "[apple, banana, cherry, ]" — unwanted trailing ", "
    }
}
```

**How to run:** `java ListBuildBuggy.java`

Every iteration appends `", "` after each item, including the last one — there's no way for the loop, written this way, to know it's on the final iteration and skip the separator, so the buffer ends with an unwanted trailing `", "`.

### Level 2 — Intermediate (fixed with `delete`)

Same list building, now using `delete` after the loop to remove exactly the trailing separator's length, rather than trying to avoid adding it in the first place.

```java
public class ListBuildFixed {
    public static void main(String[] args) {
        String[] items = { "apple", "banana", "cherry" };
        StringBuffer sb = new StringBuffer();

        for (String item : items) {
            sb.append(item).append(", ");
        }

        if (sb.length() > 0) {
            sb.delete(sb.length() - 2, sb.length()); // remove the trailing ", " — exactly 2 characters
        }

        System.out.println("[" + sb + "]"); // "[apple, banana, cherry]"
    }
}
```

**How to run:** `java ListBuildFixed.java`

After the loop finishes, `sb` holds `"apple, banana, cherry, "` (with the unwanted trailing separator). `sb.delete(sb.length() - 2, sb.length())` removes exactly the last 2 characters (the `", "`), using `sb.length()` queried *after* the loop, so it correctly reflects the buffer's final size regardless of how many items there were. The `if (sb.length() > 0)` guard avoids attempting to delete from an empty buffer if `items` had been empty.

### Level 3 — Advanced

Same list builder, now packaged as a reusable method that also **prefixes** the finished list with a label using `insert(0, ...)` (adding content at the very start, after the list itself is already built) and offers a `reverse()`-based option to display the list in reverse order — demonstrating all four core mutating methods together in one coherent utility.

```java
public class ListBuildAdvanced {

    static StringBuffer buildList(String[] items, boolean reversed) {
        StringBuffer sb = new StringBuffer();
        for (String item : items) {
            sb.append(item).append(", ");
        }
        if (sb.length() > 0) {
            sb.delete(sb.length() - 2, sb.length());
        }
        if (reversed) {
            sb.reverse(); // reverses the CHARACTERS, e.g. "apple, banana" -> "ananab ,elppa"
        }
        return sb;
    }

    public static void main(String[] args) {
        String[] items = { "apple", "banana", "cherry" };

        StringBuffer forward = buildList(items, false);
        forward.insert(0, "Items: "); // add a label at the very start, AFTER the list content was already built
        System.out.println(forward);

        StringBuffer backward = buildList(items, true);
        System.out.println("Character-reversed: " + backward);
    }
}
```

**How to run:** `java ListBuildAdvanced.java`

`buildList` returns the fully-assembled `StringBuffer` (after `append`ing every item and `delete`-ing the trailing separator, and optionally `reverse`-ing it), and `main` then calls `.insert(0, "Items: ")` on the *already complete* list — this demonstrates that `insert` works just as well after a buffer is "done" as it does during construction, shifting the entire existing content to the right to make room for the new text at position `0`. Note carefully that `reverse()` reverses the raw **character** sequence, not the *order of items* — `"apple, banana, cherry"` reversed character-by-character produces `"yrrehc ,ananab ,elppa"`, not `"cherry, banana, apple"`; reversing item order (as opposed to character order) would require a different approach entirely, such as building the list from the array traversed backward.

## 6. Walkthrough

Trace `buildList(items, false)` followed by `.insert(0, "Items: ")`:

**Building.** The loop appends `"apple"`, then `", "`, then `"banana"`, then `", "`, then `"cherry"`, then `", "` — after the loop, `sb` holds `"apple, banana, cherry, "` (24 characters).

**Trimming.** `sb.length()` is `24`. `sb.delete(22, 24)` removes the last 2 characters (the final `", "`), leaving `sb = "apple, banana, cherry"` (22 characters).

**No reversal.** `reversed` is `false`, so `sb.reverse()` is never called; `sb` is returned as-is.

**Inserting the label.** Back in `main`, `forward.insert(0, "Items: ")` inserts the 7-character text `"Items: "` at position `0` — every existing character shifts right by 7 positions to make room. The buffer becomes `"Items: apple, banana, cherry"`.

```
build: append each item + ", " -> "apple, banana, cherry, " (24 chars)
delete(22, 24) -> removes trailing ", " -> "apple, banana, cherry" (22 chars)
reversed=false -> no reverse() call
insert(0, "Items: ") -> "Items: apple, banana, cherry"  (all 22 chars shifted right by 7)
```

**Final output.** `System.out.println(forward)` prints `"Items: apple, banana, cherry"`. For the separate `backward` buffer (built with `reversed = true`), the trimmed `"apple, banana, cherry"` is reversed character-by-character before being returned, printing `"Character-reversed: yrrehc ,ananab ,elppa"` — the individual words are scrambled backward along with everything else, since `reverse()` has no concept of "words" or "items," only raw character positions.

## 7. Gotchas & takeaways

> **`reverse()` reverses the entire character sequence, with no awareness of words, items, or any other higher-level structure** — reversing `"apple, banana, cherry"` produces gibberish-looking scrambled text, not `"cherry, banana, apple"`. If you need to reverse the *order of items* in a delimited list, that requires iterating and rebuilding, not a single `reverse()` call.

> **`delete(start, end)`'s `end` index is exclusive, exactly like `String.substring`** — and both `start`/`end` must be valid relative to the buffer's *current* length at the moment `delete` is called, which is why querying `sb.length()` live (immediately before the `delete` call) is the standard, correct way to remove a known-length trailing suffix, rather than hardcoding a length that might not match if the buffer's content changes.

- `append`, `insert`, `delete`, and `reverse` all mutate the same `StringBuffer` object in place and return that same object, enabling method chaining.
- `insert(offset, ...)` shifts all existing content at and after `offset` to the right to make room; it works on a buffer at any stage, not just during initial construction.
- `delete(start, end)` removes a range with an exclusive `end`, mirroring `substring`'s convention — querying `sb.length()` immediately beforehand is the standard way to target "the last N characters."
- `reverse()` operates purely on character order with no higher-level structural awareness — reversing item order in a delimited list needs a different, explicit approach.
