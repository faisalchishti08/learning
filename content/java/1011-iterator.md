---
card: java
gi: 1011
slug: iterator
title: Iterator
---

## 1. What it is

The **Iterator** pattern provides a way to access the elements of a collection **sequentially**, one at a time, without exposing how that collection is actually stored internally (an array, a linked list, a tree). The consuming code only knows two things: "is there a next element?" and "give me the next element" — it never needs to know whether it's walking an `ArrayList`'s backing array or chasing pointers through a linked list. Java's own `for (Item item : collection)` loop is built directly on this pattern via the `Iterable`/`Iterator` interfaces.

## 2. Why & when

If consuming code had to know a collection's internal structure to traverse it — indexing into an array, following `next` pointers through a linked list, walking a tree recursively — every piece of code that iterates would be coupled to that specific internal representation, and switching the collection's implementation later would break every caller. Iterator exists to hide that internal structure behind a small, uniform interface (`hasNext()` / `next()`), so consuming code stays identical regardless of what's actually being iterated over, and even custom, non-collection-like sequences (a range of numbers, a stream of file lines) can be iterated the exact same way.

Reach for Iterator when you're building your own custom collection or sequence and want it to work with Java's `for-each` loop and standard traversal idioms, or when you need multiple independent traversals of the same collection happening concurrently (each `Iterator` tracks its own position). It's unnecessary for a simple array or list you're only ever going to loop over directly with an index — Java's built-in collections already implement `Iterable` for you.

## 3. Core concept

```
interface MyIterator<T> { boolean hasNext(); T next(); }
interface MyIterable<T> { MyIterator<T> createIterator(); }

class NameCollection implements MyIterable<String> {
    private final String[] names;
    NameCollection(String[] names) { this.names = names; }

    public MyIterator<String> createIterator() {
        return new MyIterator<>() {
            private int index = 0;
            public boolean hasNext() { return index < names.length; }
            public String next() { return names[index++]; }
        };
    }
}

NameCollection names = new NameCollection(new String[]{"Ana", "Ben"});
MyIterator<String> it = names.createIterator();
while (it.hasNext()) {
    System.out.println(it.next()); // consumer never touches the underlying array directly
}
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Consumer code repeatedly calling hasNext and next on an Iterator, which internally tracks a position into the underlying array without exposing that array to the consumer">
  <rect x="30" y="50" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Consumer</text>

  <rect x="230" y="50" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="300" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Iterator</text>

  <rect x="450" y="50" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4"/>
  <text x="525" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">names[] (hidden)</text>

  <line x1="150" y1="70" x2="230" y2="70" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="190" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">hasNext()/next()</text>
  <line x1="370" y1="70" x2="450" y2="70" stroke="#79c0ff" stroke-dasharray="4" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The consumer only ever calls `hasNext()`/`next()`; the underlying array (or any other storage) stays entirely hidden inside the iterator.

## 5. Runnable example

Scenario: a custom playlist collection, evolving from directly exposing its internal array into a proper `Iterable`/`Iterator` implementation that works with Java's `for-each` loop.

### Level 1 — Basic

```java
// File: IteratorBasic.java
class Playlist {
    private final String[] songs;
    Playlist(String[] songs) { this.songs = songs; }
    String[] getSongs() { return songs; } // exposes the internal array directly
}

public class IteratorBasic {
    public static void main(String[] args) {
        Playlist playlist = new Playlist(new String[]{"Song A", "Song B", "Song C"});

        // Consumer must know it's an array and use an index -- tightly coupled
        // to Playlist's internal storage choice.
        String[] songs = playlist.getSongs();
        for (int i = 0; i < songs.length; i++) {
            System.out.println(songs[i]);
        }
    }
}
```

**How to run:** save as `IteratorBasic.java`, then `javac IteratorBasic.java && java IteratorBasic` (JDK 17+).

Expected output:
```
Song A
Song B
Song C
```

`getSongs()` leaks the internal array directly — a caller could even mutate it (`songs[0] = "Hacked"`), and if `Playlist` later switches to storing songs in a `LinkedList` instead of an array, every caller using index-based access breaks.

### Level 2 — Intermediate

```java
// File: IteratorIntermediate.java
import java.util.Iterator;

class Playlist implements Iterable<String> {
    private final String[] songs;
    Playlist(String[] songs) { this.songs = songs; }

    public Iterator<String> iterator() {
        return new Iterator<>() {
            private int index = 0;
            public boolean hasNext() { return index < songs.length; }
            public String next() { return songs[index++]; }
        };
    }
}

public class IteratorIntermediate {
    public static void main(String[] args) {
        Playlist playlist = new Playlist(new String[]{"Song A", "Song B", "Song C"});

        // The consumer just uses a plain for-each loop -- no index, no array exposed.
        for (String song : playlist) {
            System.out.println(song);
        }
    }
}
```

**How to run:** save as `IteratorIntermediate.java`, then `javac IteratorIntermediate.java && java IteratorIntermediate` (JDK 17+).

Expected output:
```
Song A
Song B
Song C
```

The real-world concern added: `Playlist` implements Java's standard `Iterable<String>`, so it works with the built-in `for-each` loop. The consumer never sees the internal `String[]` at all — `Playlist` could switch to a `LinkedList` internally and no consuming code would need to change.

### Level 3 — Advanced

```java
// File: IteratorAdvanced.java
import java.util.Iterator;
import java.util.NoSuchElementException;

class Playlist implements Iterable<String> {
    private final String[] songs;
    Playlist(String[] songs) { this.songs = songs; }

    // A FILTERING iterator: skips songs matching a predicate, entirely transparently
    // to the consumer -- it still just sees hasNext()/next().
    Iterable<String> withoutExplicit(java.util.Set<String> explicitSongs) {
        return () -> new Iterator<>() {
            private int index = 0;
            private String pending = null;

            public boolean hasNext() {
                while (pending == null && index < songs.length) {
                    String candidate = songs[index++];
                    if (!explicitSongs.contains(candidate)) {
                        pending = candidate;
                    }
                }
                return pending != null;
            }

            public String next() {
                if (!hasNext()) throw new NoSuchElementException();
                String result = pending;
                pending = null;
                return result;
            }
        };
    }
}

public class IteratorAdvanced {
    public static void main(String[] args) {
        Playlist playlist = new Playlist(new String[]{"Song A", "Explicit Track", "Song B", "Song C"});
        java.util.Set<String> explicit = java.util.Set.of("Explicit Track");

        for (String song : playlist.withoutExplicit(explicit)) {
            System.out.println(song);
        }
    }
}
```

**How to run:** save as `IteratorAdvanced.java`, then `javac IteratorAdvanced.java && java IteratorAdvanced` (JDK 17+).

Expected output:
```
Song A
Song B
Song C
```

The production-flavored hard case: `withoutExplicit` returns a custom `Iterable` whose iterator skips filtered-out elements internally — `hasNext()` has to look ahead through possibly several skipped elements to find the next valid one, buffering it in `pending`, while the consuming `for-each` loop is completely unaware that any filtering or look-ahead logic is happening at all.

## 6. Walkthrough

Tracing the `for-each` loop over `playlist.withoutExplicit(explicit)`:

1. The `for-each` loop calls `.iterator()` on the `Iterable` returned by `withoutExplicit`, getting a fresh anonymous `Iterator` with `index = 0` and `pending = null`.
2. The loop calls `hasNext()`: the `while` loop runs since `pending == null && index < 4`. It reads `songs[0]` (`"Song A"`), increments `index` to `1`. `"Song A"` isn't in `explicitSongs`, so `pending = "Song A"` and the `while` loop exits (since `pending` is no longer `null`). `hasNext()` returns `true`.
3. The loop calls `next()`: `hasNext()` is called again internally, but since `pending` is already `"Song A"` (non-null), the `while` loop inside it doesn't execute at all, and it returns `true` immediately. `next()` then saves `result = "Song A"`, resets `pending = null`, and returns `"Song A"` — printed.
4. The loop calls `hasNext()` again: this time the `while` loop reads `songs[1]` (`"Explicit Track"`), increments `index` to `2`. Since `explicitSongs.contains("Explicit Track")` is `true`, `pending` stays `null` and the `while` loop continues: it reads `songs[2]` (`"Song B"`), increments `index` to `3`, and since it's not filtered, sets `pending = "Song B"` and exits the loop. `hasNext()` returns `true`, silently having skipped `"Explicit Track"`.
5. `next()` returns `"Song B"`, printed. The same look-ahead-and-skip process repeats for `"Song C"` at `index = 3`, after which `index` reaches `4` (`songs.length`) and no more elements remain.
6. The final `hasNext()` call finds `pending == null` and `index < songs.length` is false, so the `while` loop never runs and it returns `false`, ending the `for-each` loop. The filtering — skipping `"Explicit Track"` — happened entirely inside the iterator; the consuming loop's code (`for (String song : ...) { System.out.println(song); }`) never changed at all.

## 7. Gotchas & takeaways

> **Gotcha:** a filtering or lazy iterator's `hasNext()` often needs to do real work (looking ahead, as in Level 3) rather than a trivial bounds check — calling `hasNext()` multiple times in a row without calling `next()` in between must be safe and idempotent (it shouldn't skip an extra element each time it's called), which is exactly why the `pending` field buffers the found element instead of discarding it.

- Iterator exposes a uniform `hasNext()`/`next()` interface over a collection's elements, hiding whatever internal storage structure the collection actually uses.
- Java's `for-each` loop is built directly on the `Iterable`/`Iterator` interfaces — implementing them on your own class makes it work with `for-each` for free.
- Multiple independent iterators over the same collection can each track their own position, enabling concurrent traversals without interfering with each other.
- A filtering or transforming iterator (Level 3) can do arbitrarily complex look-ahead logic inside `hasNext()`/`next()` while consuming code stays completely unaware of it.
- Don't build a custom iterator for a simple case Java's built-in collections already cover — `ArrayList`, `LinkedList`, and friends already implement `Iterable`.
- Iterator pairs naturally with [Composite](1006-composite.md): a custom iterator can hide the recursive tree-traversal logic needed to walk a composite structure, presenting client code with a flat, linear sequence instead.
