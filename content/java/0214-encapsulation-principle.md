---
card: java
gi: 214
slug: encapsulation-principle
title: Encapsulation principle
---

## 1. What it is

**Encapsulation** is the practice of bundling an object's data together with the methods that operate on it, while hiding the data's internal representation behind a controlled interface — typically by making fields `private` and exposing only the specific, validated operations a class chooses to make public. It's the combination of everything covered so far in this series (fields, `private`, constructors, methods) applied deliberately, as a design principle rather than just a mechanical rule.

```java
class BankAccount {
    private double balance; // hidden — no outside code can set this directly

    BankAccount(double initialBalance) {
        if (initialBalance < 0) throw new IllegalArgumentException("Cannot start negative");
        this.balance = initialBalance;
    }

    void withdraw(double amount) { // the ONLY way to reduce balance — always validated
        if (amount > balance) throw new IllegalStateException("Insufficient funds");
        balance -= amount;
    }

    double getBalance() { // controlled, read-only access
        return balance;
    }
}
```

`balance` can never be set to an invalid value from outside `BankAccount`, because it's `private` — every change must go through `withdraw` (or a corresponding `deposit`, not shown), both of which can enforce whatever rules the class needs, guaranteeing `balance` always stays in a valid, consistent state.

## 2. Why & when

Encapsulation exists to protect an object's internal consistency and to decouple a class's external behaviour from its internal implementation details:

- **Guaranteed invariants** — by controlling every way a field can change, a class can guarantee properties about its own state (a balance never goes negative, a list never exceeds a capacity) that would be impossible to enforce if outside code could modify fields directly.
- **Freedom to change implementation later** — as long as a class's public methods keep behaving the same way, its internal fields, data structures, and algorithms can be completely rewritten without breaking any code that only ever used the public interface.
- **Reduced coupling** — other code depends only on a class's public contract (its method signatures and their documented behaviour), not on how that contract happens to be implemented internally, which makes large codebases far easier to change safely over time.

You apply encapsulation as a design discipline in essentially every class you write: default to `private` fields, expose only the operations genuinely needed by other code, and validate every state change at the single point (constructors and methods) where it's allowed to happen.

## 3. Core concept

```java
class Thermostat {
    private double targetTemp;
    private static final double MIN_TEMP = 10.0;
    private static final double MAX_TEMP = 32.0;

    Thermostat(double initialTemp) {
        setTargetTemp(initialTemp); // even the constructor goes through the SAME validation
    }

    void setTargetTemp(double temp) { // the single, controlled point of change
        if (temp < MIN_TEMP || temp > MAX_TEMP) {
            throw new IllegalArgumentException("Temperature out of range: " + temp);
        }
        targetTemp = temp;
    }

    double getTargetTemp() {
        return targetTemp;
    }
}
```

Even the constructor routes through `setTargetTemp` rather than assigning `targetTemp` directly — this ensures the *exact same* validation logic applies whether the temperature is set at construction time or changed later, with no risk of the two code paths drifting apart or one accidentally skipping a check the other enforces.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A private field completely hidden inside a class boundary, reachable only through a small set of public validated methods, with the constructor itself also routing through that same single validation point rather than bypassing it">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>

  <rect x="200" y="20" width="200" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class Thermostat</text>
  <text x="300" y="65" fill="#f85149" font-size="9" text-anchor="middle" font-family="monospace">private targetTemp 🔒</text>
  <line x1="240" y1="75" x2="360" y2="75" stroke="#8b949e" stroke-width="1"/>
  <text x="300" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">setTargetTemp(t) — validates</text>
  <text x="300" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="monospace">getTargetTemp()</text>

  <line x1="120" y1="75" x2="200" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#en)"/>
  <text x="80" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">constructor AND</text>
  <text x="80" y="80" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">outside code</text>
  <text x="80" y="95" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">both go through here</text>

  <defs><marker id="en" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

Both the constructor and any later change route through the same single, validating entry point.

## 5. Runnable example

Scenario: a small `Playlist` class managing a bounded set of songs — starting with basic encapsulated state, then extending with a method enforcing a capacity limit consistently, then hardening into a class demonstrating exactly how encapsulation prevents an invalid state that direct field access would have allowed.

### Level 1 — Basic

```java
public class PlaylistBasic {
    static class Playlist {
        private java.util.List<String> songs = new java.util.ArrayList<>();

        void addSong(String title) {
            songs.add(title);
        }

        java.util.List<String> getSongs() {
            return new java.util.ArrayList<>(songs); // returns a COPY — outside code can't mutate our internal list
        }
    }

    public static void main(String[] args) {
        Playlist p = new Playlist();
        p.addSong("Song A");
        p.addSong("Song B");

        System.out.println(p.getSongs());
    }
}
```

**How to run:** `java PlaylistBasic.java`

`getSongs()` returns a **copy** of the internal list, not the internal list itself — this means outside code that receives the result and calls `.add(...)` or `.remove(...)` on it modifies only its own copy, never `Playlist`'s actual internal state, which is a subtle but important part of encapsulation beyond just marking fields `private`.

### Level 2 — Intermediate

Same playlist, now enforcing a maximum capacity consistently through the single `addSong` method.

```java
public class PlaylistIntermediate {
    static class Playlist {
        private static final int MAX_SONGS = 3;
        private java.util.List<String> songs = new java.util.ArrayList<>();

        void addSong(String title) {
            if (songs.size() >= MAX_SONGS) {
                throw new IllegalStateException("Playlist is full (max " + MAX_SONGS + " songs)");
            }
            songs.add(title);
        }

        java.util.List<String> getSongs() {
            return new java.util.ArrayList<>(songs);
        }
    }

    public static void main(String[] args) {
        Playlist p = new Playlist();
        p.addSong("Song A");
        p.addSong("Song B");
        p.addSong("Song C");

        try {
            p.addSong("Song D"); // exceeds MAX_SONGS
        } catch (IllegalStateException e) {
            System.out.println("Rejected: " + e.getMessage());
        }

        System.out.println(p.getSongs());
    }
}
```

**How to run:** `java PlaylistIntermediate.java`

Because `songs` is `private` and the *only* way to add to it is through `addSong`, the `MAX_SONGS` limit is guaranteed to be enforced consistently — there is no code path anywhere that could add a fourth song while bypassing this check, since direct access to `songs` from outside `Playlist` simply isn't possible.

### Level 3 — Advanced

Same playlist, now demonstrating concretely what would go wrong *without* encapsulation, by contrasting the safe version against a hypothetical unencapsulated one that exposes the list directly.

```java
import java.util.ArrayList;
import java.util.List;

public class PlaylistAdvanced {

    // WITHOUT encapsulation — demonstrates the risk directly
    static class UnsafePlaylist {
        List<String> songs = new ArrayList<>(); // public field — no protection at all
    }

    // WITH encapsulation — the correct approach
    static class SafePlaylist {
        private static final int MAX_SONGS = 3;
        private List<String> songs = new ArrayList<>();

        void addSong(String title) {
            if (songs.size() >= MAX_SONGS) {
                throw new IllegalStateException("Playlist is full");
            }
            songs.add(title);
        }

        List<String> getSongs() {
            return new ArrayList<>(songs);
        }
    }

    public static void main(String[] args) {
        UnsafePlaylist unsafe = new UnsafePlaylist();
        unsafe.songs.add("A"); unsafe.songs.add("B");
        unsafe.songs.add("C"); unsafe.songs.add("D"); // no limit enforced at all — direct field access bypasses everything
        System.out.println("Unsafe playlist size: " + unsafe.songs.size()); // 4 — the "limit" was never real

        SafePlaylist safe = new SafePlaylist();
        safe.addSong("A"); safe.addSong("B"); safe.addSong("C");
        try {
            safe.addSong("D");
        } catch (IllegalStateException e) {
            System.out.println("Safe playlist correctly rejected: " + e.getMessage());
        }
        System.out.println("Safe playlist size: " + safe.getSongs().size()); // 3 — the limit actually held
    }
}
```

**How to run:** `java PlaylistAdvanced.java`

`UnsafePlaylist` exposes `songs` as a plain public field with no controlling method at all — nothing stops outside code from adding a fourth song directly, since there's no single point where a limit could be enforced; `SafePlaylist`, by contrast, makes `songs` `private` and routes every addition through `addSong`, so its capacity limit is a genuine, unbreakable guarantee rather than a suggestion that outside code could simply ignore.

## 6. Walkthrough

Trace both playlists in `PlaylistAdvanced.main`:

**`UnsafePlaylist`.** `unsafe.songs.add("A")` directly mutates the public `songs` list — no validation exists anywhere to intercept this. The same happens for `"B"`, `"C"`, and `"D"` — all four adds succeed unconditionally, since there is no method standing between outside code and the list itself. `unsafe.songs.size()` reads `4`.

**`SafePlaylist`.** `safe.addSong("A")` checks `songs.size() (0) >= MAX_SONGS (3)` — false, so `"A"` is added; `songs.size()` becomes `1`. Same for `"B"` (`size` becomes `2`) and `"C"` (`size` becomes `3`). `safe.addSong("D")` checks `songs.size() (3) >= MAX_SONGS (3)` — true this time, so the guard fires, throwing `IllegalStateException("Playlist is full")` *before* `"D"` is ever added.

```
UnsafePlaylist: songs.add() called directly 4 times, no check anywhere -> size = 4 (limit never enforced)

SafePlaylist: addSong() called 4 times
  "A": size 0 >= 3? no -> add -> size 1
  "B": size 1 >= 3? no -> add -> size 2
  "C": size 2 >= 3? no -> add -> size 3
  "D": size 3 >= 3? YES -> throw, never added -> size stays 3
```

**Final output.** `"Unsafe playlist size: 4"`, then `"Safe playlist correctly rejected: Playlist is full"`, then `"Safe playlist size: 3"` — the side-by-side comparison makes the practical value of encapsulation directly visible: one class's stated limit is real and enforced; the other's is purely aspirational, since nothing actually protects it.

## 7. Gotchas & takeaways

> **Making a field `private` alone is not sufficient encapsulation if a getter simply hands back a direct reference to a mutable internal object.** `return songs;` (without copying) would let outside code call `.add(...)` on the *actual* internal list through the returned reference, silently bypassing every check inside `addSong` — this is exactly why `getSongs()` in the examples above returns a defensive copy instead.

> **Encapsulation is a design discipline, not just a syntax rule — simply marking every field `private` accomplishes nothing if every field also has an unrestricted, unvalidated setter.** The real value comes from thoughtfully deciding which operations should be allowed, and enforcing whatever invariants matter at those specific, deliberate points of control.

- Encapsulation means hiding internal data behind a controlled, validated interface, typically via `private` fields and public methods.
- It guarantees invariants (like a size limit or a non-negative balance) that direct, unrestricted field access would make impossible to enforce.
- A getter that returns a direct reference to an internal mutable object can silently undermine encapsulation — return a defensive copy when the internal object could otherwise be mutated externally.
- Route every path that changes state (including constructors) through the same validating logic, so no code path can accidentally bypass a rule enforced elsewhere.
