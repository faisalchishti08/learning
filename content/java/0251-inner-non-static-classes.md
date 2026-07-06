---
card: java
gi: 251
slug: inner-non-static-classes
title: Inner (non-static) classes
---

## 1. What it is

An inner class is a nested class declared *without* the `static` keyword. Unlike a static nested class, every instance of an inner class is implicitly tied to exactly one instance of its enclosing class, and can freely access that enclosing instance's fields and methods directly — creating an inner class instance requires an enclosing instance to exist first, using the syntax `outerInstance.new InnerClass(...)`.

```java
class BankAccount {
    private double balance;
    BankAccount(double balance) { this.balance = balance; }

    class TransactionHistory { // non-static inner class — implicitly tied to one BankAccount instance
        void printBalance() {
            System.out.println("Balance for this account: " + balance); // accesses the ENCLOSING instance's field directly
        }
    }
}

public class InnerClassDemo {
    public static void main(String[] args) {
        BankAccount account = new BankAccount(500.0);
        BankAccount.TransactionHistory history = account.new TransactionHistory(); // requires an enclosing instance
        history.printBalance(); // "Balance for this account: 500.0"
    }
}
```

`TransactionHistory` reads `balance` directly, with no qualification at all, even though `balance` is a field of the *enclosing* `BankAccount` class, not of `TransactionHistory` itself — this works only because every `TransactionHistory` instance is implicitly bound to one specific `BankAccount` instance, created via `account.new TransactionHistory()`.

## 2. Why & when

Inner classes exist for situations where a nested helper class genuinely needs ongoing access to its enclosing instance's state, tying the two together for as long as the inner instance exists.

- **Direct access to enclosing state** — an inner class can read and even modify the enclosing instance's fields directly, without needing them passed in explicitly, which is convenient when the inner class exists specifically to work closely with that state.
- **Modeling a "belongs to exactly one" relationship** — a `TransactionHistory` conceptually only makes sense in the context of one specific `BankAccount`; an inner class enforces this at the language level, since every instance must be created through (and is permanently bound to) exactly one enclosing instance.
- **Historical use in event handling and iterators** — before lambdas, inner classes were the primary way to implement callback-style interfaces (like an `Iterator` for a custom collection) that needed access to the enclosing collection's internal state — `Iterator` implementations nested inside collection classes remain a common, idiomatic use of inner classes today.

Reach for a non-static inner class specifically when the nested class's behaviour is meaningless without access to a particular enclosing instance's state — if the nested class could function perfectly well on its own data, with no need to reach back into an enclosing instance, a static nested class (the previous topic) is simpler and should be preferred instead.

## 3. Core concept

```java
class Playlist {
    private java.util.List<String> songs = new java.util.ArrayList<>();

    void add(String song) { songs.add(song); }

    class PlaylistIterator { // inner class: needs access to the enclosing Playlist's songs list
        int position = 0;

        boolean hasNext() { return position < songs.size(); } // reads the ENCLOSING instance's songs field
        String next() { return songs.get(position++); }
    }

    PlaylistIterator iterator() { return new PlaylistIterator(); } // created FROM WITHIN an instance method
}
```

`PlaylistIterator` reads `songs` directly, with no explicit reference to any `Playlist` object — because it is an inner class, every instance carries an implicit reference back to whichever `Playlist` created it; `iterator()` (an instance method on `Playlist`) can create a `PlaylistIterator` with the simple `new PlaylistIterator()` syntax, since it is already running in the context of a specific `Playlist` instance (`this`).

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Every inner class instance carries an implicit reference to the exact enclosing instance that created it, allowing direct access to that instances fields, unlike a static nested class">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="60" y="30" width="200" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="50" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">BankAccount instance</text>
  <text x="160" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">balance = 500.0</text>

  <line x1="260" y1="55" x2="340" y2="55" stroke="#f85149" stroke-width="1.5"/>
  <text x="300" y="45" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">implicit ref</text>

  <rect x="340" y="30" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">TransactionHistory instance</text>
  <text x="440" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">printBalance() reads balance directly</text>

  <text x="300" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Created via account.new TransactionHistory() — permanently bound to that one BankAccount.</text>
</svg>

Every inner class instance holds an implicit link to the specific enclosing instance that created it.

## 5. Runnable example

Scenario: a custom `Playlist` class with an inner iterator, evolved from basic iteration into a working `Iterator` interface implementation, then hardened to demonstrate exactly how the implicit enclosing reference (`Outer.this`) resolves when names could otherwise be ambiguous.

### Level 1 — Basic

```java
import java.util.ArrayList;
import java.util.List;

public class InnerClassBasic {
    static class Playlist {
        List<String> songs = new ArrayList<>();
        void add(String song) { songs.add(song); }

        class PlaylistPrinter { // inner class
            void printAll() {
                for (String s : songs) System.out.println("Track: " + s); // reads enclosing songs directly
            }
        }
    }

    public static void main(String[] args) {
        Playlist playlist = new Playlist();
        playlist.add("Song A");
        playlist.add("Song B");

        Playlist.PlaylistPrinter printer = playlist.new PlaylistPrinter(); // requires an enclosing instance
        printer.printAll();
    }
}
```

**How to run:** `java InnerClassBasic.java`

`playlist.new PlaylistPrinter()` explicitly creates the inner class instance through `playlist`, binding it to that specific `Playlist`; `printAll()` then reads `songs` directly, with no need to reference `playlist` at all inside the inner class's own code.

### Level 2 — Intermediate

Same `Playlist`, now with a proper `java.util.Iterator<String>` implementation as an inner class — a very common, idiomatic real-world use — letting the playlist be used directly in a Java for-each loop via `Iterable`.

```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class InnerClassIntermediate {
    static class Playlist implements Iterable<String> {
        List<String> songs = new ArrayList<>();
        void add(String song) { songs.add(song); }

        @Override
        public Iterator<String> iterator() {
            return new PlaylistIterator(); // created from within an instance method: implicit enclosing instance
        }

        class PlaylistIterator implements Iterator<String> {
            int position = 0;
            @Override
            public boolean hasNext() { return position < songs.size(); } // reads enclosing songs
            @Override
            public String next() { return songs.get(position++); }
        }
    }

    public static void main(String[] args) {
        Playlist playlist = new Playlist();
        playlist.add("Song A");
        playlist.add("Song B");
        playlist.add("Song C");

        for (String song : playlist) { // works because Playlist implements Iterable<String>
            System.out.println("Now playing: " + song);
        }
    }
}
```

**How to run:** `java InnerClassIntermediate.java`

`Playlist.iterator()` creates a `PlaylistIterator` with plain `new PlaylistIterator()`, since it runs as an instance method on a specific `Playlist` (`this` is implicitly available); the resulting iterator reads `songs` directly from that same enclosing instance, letting the standard for-each loop iterate over `playlist`'s songs without `Playlist` needing to expose `songs` publicly at all.

### Level 3 — Advanced

Same playlist, now with a naming conflict deliberately introduced — the inner class has its own `position` field with the same name style as something in the outer class — demonstrating `Outer.this` used to disambiguate exactly which instance's member is meant.

```java
import java.util.ArrayList;
import java.util.Iterator;
import java.util.List;

public class InnerClassAdvanced {
    static class Playlist implements Iterable<String> {
        List<String> songs = new ArrayList<>();
        int position = 0; // an OUTER field, same simple name as one we'll add in the inner class

        void add(String song) { songs.add(song); }

        void markCurrentPosition(int pos) { this.position = pos; } // outer's own position tracking

        @Override
        public Iterator<String> iterator() { return new PlaylistIterator(); }

        class PlaylistIterator implements Iterator<String> {
            int position = 0; // INNER field — same name as Playlist.position, deliberately

            @Override
            public boolean hasNext() { return position < songs.size(); } // refers to the INNER position (closest scope)

            @Override
            public String next() { return songs.get(position++); }

            void syncToOuterPosition() {
                position = Playlist.this.position; // Outer.this disambiguates: the ENCLOSING Playlist's position
            }
        }
    }

    public static void main(String[] args) {
        Playlist playlist = new Playlist();
        playlist.add("Song A");
        playlist.add("Song B");
        playlist.add("Song C");
        playlist.markCurrentPosition(1); // outer's position is now 1

        Playlist.PlaylistIterator it = playlist.new PlaylistIterator();
        System.out.println("Inner position before sync: " + it.position); // 0 — inner's own field
        it.syncToOuterPosition();
        System.out.println("Inner position after sync: " + it.position);  // 1 — copied from outer via Playlist.this

        while (it.hasNext()) {
            System.out.println("Song: " + it.next()); // starts from position 1: "Song B", "Song C"
        }
    }
}
```

**How to run:** `java InnerClassAdvanced.java`

Inside `PlaylistIterator`, an unqualified `position` always refers to the *inner* class's own field (the closest enclosing scope wins by default), while `Playlist.this.position` explicitly reaches past the inner class to the *specific enclosing `Playlist` instance's* `position` field — `Outer.this` is the general syntax for this disambiguation, needed whenever an inner class's own member would otherwise shadow a same-named member on the enclosing instance.

## 6. Walkthrough

Trace `main` in `InnerClassAdvanced` step by step.

**Building `playlist` and adding three songs.** `songs` becomes `["Song A", "Song B", "Song C"]`. `playlist.position` (the outer field) starts at `0`.

**`playlist.markCurrentPosition(1)`.** Sets `playlist.position` (the outer field) to `1`.

**`playlist.new PlaylistIterator()`.** Creates a `PlaylistIterator` bound to `playlist`. Its own `position` field (the inner one) is initialized to `0`, entirely separate from `playlist.position` (which is `1`).

**`it.position` (first print).** Refers to the inner class's own `position` field: `0`. Prints `"Inner position before sync: 0"`.

**`it.syncToOuterPosition()`.** Executes `position = Playlist.this.position;` — the left-hand `position` (unqualified) refers to the inner field being assigned; the right-hand `Playlist.this.position` explicitly reaches the *enclosing* `Playlist` instance's `position`, which is `1`. So the inner `position` field is set to `1`.

**`it.position` (second print).** Now `1`, reflecting the sync. Prints `"Inner position after sync: 1"`.

**The `while (it.hasNext())` loop.** `hasNext()` checks `position < songs.size()`: `1 < 3` is `true`. `it.next()` returns `songs.get(1)` (`"Song B"`) and increments `position` to `2`. Prints `"Song: Song B"`. Loop again: `hasNext()` checks `2 < 3` — `true`. `next()` returns `songs.get(2)` (`"Song C"`), increments `position` to `3`. Prints `"Song: Song C"`. Loop again: `hasNext()` checks `3 < 3` — `false`. Loop ends.

```
playlist.songs = ["Song A", "Song B", "Song C"]
playlist.position (outer) = 0 -> markCurrentPosition(1) -> outer.position = 1

new PlaylistIterator(): inner.position = 0 (separate field, unrelated to outer.position so far)

it.position (before sync) -> 0 (inner's own field)
syncToOuterPosition(): inner.position = Playlist.this.position (=1) -> inner.position becomes 1
it.position (after sync) -> 1

while(hasNext): position=1 < 3 -> next() -> songs[1]="Song B", position becomes 2
while(hasNext): position=2 < 3 -> next() -> songs[2]="Song C", position becomes 3
while(hasNext): position=3 < 3 -> false -> loop ends
```

**Final output.**
```
Inner position before sync: 0
Inner position after sync: 1
Song: Song B
Song: Song C
```

## 7. Gotchas & takeaways

> **An inner class instance cannot exist without an enclosing instance, and holds an implicit reference to it for its entire lifetime** — this means an inner class instance can inadvertently keep its enclosing instance alive (preventing garbage collection) for as long as the inner instance itself is reachable, which matters for memory management in long-lived inner class instances (like listeners registered with an external system).

> **When an inner class field or method shares a name with one on the enclosing class, the inner class's own member is used by default (it "shadows" the outer one) — use `Outer.this.member` to explicitly reach the enclosing instance's version.** This is the exact mechanism `syncToOuterPosition` relied on; forgetting this rule is a common source of confusion when refactoring code that introduces a naming collision between an inner class and its enclosing class.

- A non-static inner class instance is always tied to exactly one enclosing instance, created via `outerInstance.new InnerClass(...)` (or plain `new InnerClass()` from within an enclosing instance method).
- It can access the enclosing instance's fields and methods directly, without qualification, unlike a static nested class.
- `Outer.this` explicitly refers to the specific enclosing instance, needed to disambiguate when an inner class's own member shadows one with the same name on the enclosing class.
- Prefer a static nested class unless the nested class's behaviour genuinely depends on ongoing access to a specific enclosing instance's state.
