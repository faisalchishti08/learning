---
card: java
gi: 245
slug: implementing-multiple-interfaces
title: Implementing multiple interfaces
---

## 1. What it is

A single Java class can implement any number of interfaces at once, listing each one separated by commas after `implements`. This is Java's answer to "multiple inheritance of type" — a class can be treated as any of the interfaces it implements, satisfying several independent contracts simultaneously, even though it can still extend only one superclass.

```java
interface Swimmer { void swim(); }
interface Runner { void run(); }
interface Flyer { void fly(); }

class Duck implements Swimmer, Runner, Flyer { // three interfaces, one class
    @Override public void swim() { System.out.println("Paddling"); }
    @Override public void run() { System.out.println("Waddling"); }
    @Override public void fly() { System.out.println("Flying short distances"); }
}
```

`Duck` implements three entirely separate interfaces at once, each contributing one method — a `Duck` object can be passed anywhere a `Swimmer`, a `Runner`, or a `Flyer` is expected, satisfying all three contracts simultaneously with a single class.

## 2. Why & when

Implementing multiple interfaces models real-world objects and components that genuinely have several independent capabilities, none of which imply or require the others.

- **Modeling naturally multi-capable things** — a `Duck` really can swim, run, and fly; forcing this into a single-inheritance class hierarchy (say, `Duck extends SwimmingAnimal`) would arbitrarily prioritize one capability as "the" identity and struggle to add the others cleanly.
- **Composing standard library contracts** — a custom class might need to be `Comparable` (for sorting), `Serializable` (for persistence), and implement an application-specific interface, all at once; each of these is completely independent of the others, and Java lets a class satisfy all three simultaneously.
- **Enabling flexible, capability-based APIs** — code that accepts a `Comparable<T>` parameter, for example, works with *any* class implementing that interface, regardless of what else that class also happens to implement — multiple interfaces let a class opt into as many such APIs as make sense.

Implement multiple interfaces whenever a class genuinely has multiple, independent capabilities that other code might want to depend on separately — the moment you find yourself wanting a class to be usable in three unrelated contexts, each requiring a different contract, multiple interfaces are usually the right tool.

## 3. Core concept

```java
interface Comparable2<T> { int compareVal(T other); }
interface Printable { void print(); }

class Task implements Comparable2<Task>, Printable {
    String name;
    int priority;
    Task(String name, int priority) { this.name = name; this.priority = priority; }

    @Override
    public int compareVal(Task other) { return Integer.compare(this.priority, other.priority); }

    @Override
    public void print() { System.out.println("[" + priority + "] " + name); }
}
```

`Task` implements both `Comparable2<Task>` and `Printable`; nothing about being comparable requires being printable or vice versa — they are two independent facets of the same class, and a method that only cares about comparison (say, a generic sort routine) never needs to know or care that `Task` also happens to be printable.

## 4. Diagram

<svg viewBox="0 0 600 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One class implements three independent interfaces at once, the class can be treated as any one of them depending on what the calling code needs">
  <rect x="8" y="8" width="584" height="154" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Swimmer</text>

  <rect x="230" y="20" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Runner</text>

  <rect x="420" y="20" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="490" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">interface Flyer</text>

  <line x1="110" y1="50" x2="260" y2="95" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="300" y1="50" x2="290" y2="95" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="490" y1="50" x2="320" y2="95" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="200" y="100" width="200" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="122" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">class Duck implements all three</text>

  <text x="300" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">One class can satisfy any number of independent interface contracts simultaneously.</text>
</svg>

One class can implement several unrelated interfaces at once, satisfying every contract simultaneously.

## 5. Runnable example

Scenario: a media-file class that needs to be sortable, printable, and playable at the same time, evolved from implementing one interface into implementing three, then used generically in ways that only care about one capability at a time.

### Level 1 — Basic

```java
public class MultipleInterfacesBasic {
    interface Playable { void play(); }

    static class Song implements Playable {
        String title;
        Song(String title) { this.title = title; }
        @Override public void play() { System.out.println("Playing: " + title); }
    }

    public static void main(String[] args) {
        Song s = new Song("Nocturne");
        s.play();
    }
}
```

**How to run:** `java MultipleInterfacesBasic.java`

`Song` implements a single interface for now — this is the starting point before adding more capabilities.

### Level 2 — Intermediate

Same `Song`, now implementing a second interface, `Comparable2<Song>`, so a list of songs can be sorted by duration — demonstrating a class taking on a second, independent capability.

```java
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class MultipleInterfacesIntermediate {
    interface Playable { void play(); }
    interface Comparable2<T> { int compareVal(T other); }

    static class Song implements Playable, Comparable2<Song> {
        String title;
        int durationSeconds;
        Song(String title, int durationSeconds) {
            this.title = title;
            this.durationSeconds = durationSeconds;
        }
        @Override public void play() { System.out.println("Playing: " + title); }
        @Override public int compareVal(Song other) {
            return Integer.compare(this.durationSeconds, other.durationSeconds);
        }
    }

    public static void main(String[] args) {
        List<Song> songs = new ArrayList<>(List.of(
            new Song("Nocturne", 240),
            new Song("Short Interlude", 60),
            new Song("Epic Finale", 400)
        ));

        songs.sort((a, b) -> a.compareVal(b)); // uses the Comparable2 capability
        for (Song s : songs) s.play();          // uses the Playable capability
    }
}
```

**How to run:** `java MultipleInterfacesIntermediate.java`

`songs.sort((a, b) -> a.compareVal(b))` uses `Song`'s `Comparable2` capability to order the list by `durationSeconds`, while the following loop uses its entirely separate `Playable` capability to play each one — two independent facets of the same class, used in two independent operations.

### Level 3 — Advanced

Same `Song`, now implementing a third interface, `Serializable2` (a simplified illustrative stand-in), and processed by three separate utility methods, each of which only depends on exactly one of the three interfaces — demonstrating true decoupling between capabilities.

```java
import java.util.ArrayList;
import java.util.List;

public class MultipleInterfacesAdvanced {
    interface Playable { void play(); }
    interface Comparable2<T> { int compareVal(T other); }
    interface Serializable2 { String toSerialString(); }

    static class Song implements Playable, Comparable2<Song>, Serializable2 {
        String title;
        int durationSeconds;
        Song(String title, int durationSeconds) {
            this.title = title;
            this.durationSeconds = durationSeconds;
        }
        @Override public void play() { System.out.println("Playing: " + title); }
        @Override public int compareVal(Song other) {
            return Integer.compare(this.durationSeconds, other.durationSeconds);
        }
        @Override public String toSerialString() { return title + "|" + durationSeconds; }
    }

    // Each utility method depends on exactly ONE interface, not the concrete Song class
    static void playAll(List<Playable> items) {
        for (Playable p : items) p.play();
    }

    static <T> void sortAndPrint(List<T> items, java.util.Comparator<T> cmp) {
        List<T> copy = new ArrayList<>(items);
        copy.sort(cmp);
        System.out.println(copy.size() + " items sorted");
    }

    static void saveAll(List<Serializable2> items) {
        for (Serializable2 s : items) System.out.println("Saved: " + s.toSerialString());
    }

    public static void main(String[] args) {
        List<Song> songs = List.of(
            new Song("Nocturne", 240),
            new Song("Short Interlude", 60)
        );

        playAll(List.copyOf(songs));                                    // uses Playable only
        sortAndPrint(songs, (a, b) -> a.compareVal(b));                  // uses Comparable2 only
        saveAll(List.copyOf(songs));                                     // uses Serializable2 only
    }
}
```

**How to run:** `java MultipleInterfacesAdvanced.java`

`playAll`, `sortAndPrint`, and `saveAll` each accept only the specific interface type they actually need (`Playable`, a `Comparator`, and `Serializable2` respectively), never the concrete `Song` class — this means any future class implementing just the relevant interface(s) could be used with these methods too, without needing to be a `Song` at all, demonstrating the real decoupling power of implementing multiple independent interfaces.

## 6. Walkthrough

Trace `main` in `MultipleInterfacesAdvanced` through each of the three utility calls.

**`playAll(List.copyOf(songs))`.** `List.copyOf(songs)` produces a `List<Song>`, but since `Song implements Playable`, it is assignable to the parameter type `List<Playable>` (a `Song` reference can always be used wherever a `Playable` is expected). Inside `playAll`, the loop calls `p.play()` for each element: first `songs.get(0)` ("Nocturne"), printing `"Playing: Nocturne"`; then `songs.get(1)` ("Short Interlude"), printing `"Playing: Short Interlude"`. Neither `compareVal` nor `toSerialString` is ever referenced here.

**`sortAndPrint(songs, (a, b) -> a.compareVal(b))`.** A copy of `songs` is made, then sorted using the lambda comparator, which calls each pair's `compareVal` (the `Comparable2` capability) — `Integer.compare(240, 60)` when comparing "Nocturne" against "Short Interlude" returns a positive number, so "Short Interlude" (shorter) sorts first. The method prints `"2 items sorted"`. Neither `play()` nor `toSerialString()` is touched.

**`saveAll(List.copyOf(songs))`.** The loop calls `s.toSerialString()` for each song: `"Nocturne|240"` and `"Short Interlude|60"`, each printed with a `"Saved: "` prefix. Neither `play()` nor `compareVal` is touched here.

```
playAll:      Song.play() x2       -> "Playing: Nocturne", "Playing: Short Interlude"
sortAndPrint: Song.compareVal() used internally by sort -> "2 items sorted"
saveAll:      Song.toSerialString() x2 -> "Saved: Nocturne|240", "Saved: Short Interlude|60"
```

**Final output.**
```
Playing: Nocturne
Playing: Short Interlude
2 items sorted
Saved: Nocturne|240
Saved: Short Interlude|60
```
Each utility method only ever touches the one interface method relevant to its job, confirming that `Song`'s three capabilities are genuinely independent of one another.

## 7. Gotchas & takeaways

> **If two implemented interfaces declare methods with the identical signature, one implementation in the class satisfies both** — there is no conflict or ambiguity, since both interfaces are simply asking for the same method to exist. Trouble only arises with `default` methods providing *different* bodies for the same signature across two interfaces, which is covered as a special case in the interface-inheritance topics ahead.

> **Implementing many interfaces on one class is not "free" — each one is a real commitment the class must honor for its entire lifetime.** Adding interfaces indiscriminately just because a class "could" implement them can bloat its public contract and make it harder to reason about; implement an interface because calling code genuinely needs to depend on that specific capability.

- A class can implement any number of interfaces at once, each contributing an independent capability the class must fulfill.
- This is Java's mechanism for multiple inheritance of type (though not of implementation, in the classic interface model), letting one class satisfy many unrelated contracts.
- Writing utility methods that accept an interface type (rather than a concrete class) lets them work with any class implementing that interface, maximizing reuse and decoupling.
- Only implement an interface when a class genuinely needs to be usable through that specific contract — each one is a commitment, not a free addition.
