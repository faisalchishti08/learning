---
card: java
gi: 237
slug: shallow-vs-deep-clone
title: Shallow vs deep clone
---

## 1. What it is

A shallow clone copies an object's fields as-is: primitives are duplicated by value, but any reference field (an array, another object, a collection) is copied as a *reference*, meaning the original and the clone end up pointing to the exact same underlying data. A deep clone goes further, recursively duplicating every reference field's target too, so the original and the clone share absolutely nothing mutable — they are fully, genuinely independent.

```java
class Wallet implements Cloneable {
    double[] balances;
    Wallet(double[] balances) { this.balances = balances; }

    @Override
    public Wallet clone() {
        try {
            return (Wallet) super.clone(); // SHALLOW: balances reference is shared, not duplicated
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);
        }
    }
}
```

`super.clone()` alone always produces a shallow copy — this `Wallet.clone()` gives you a new `Wallet` object, but `original.balances` and `clone.balances` are still the *same* array; changing one changes the other, which is rarely the behaviour anyone actually wants from "cloning."

## 2. Why & when

The distinction matters anywhere an object holds mutable reference fields and code assumes a clone is safe to modify independently of the original.

- **Shallow copies are fast but risky** — they are cheap (no recursive copying work) and are perfectly fine when every field is either a primitive or an immutable reference (like `String`), since there is nothing mutable to accidentally share.
- **Deep copies are safer but costlier** — they guarantee true independence, which matters whenever the clone will be mutated and the original must remain untouched (a "snapshot" or "quote" scenario, as the previous topic's `Cart` example showed), at the cost of extra work to recursively copy every nested mutable structure.
- **Nested objects need their own deep copies too** — if a field is itself an object with its own mutable reference fields, a truly deep clone must call that field's own deep-copy logic recursively, not just duplicate the outer array or list — a shallow "fix" at only one level can still leave deeper mutable state shared.

Choose a shallow clone when a class's fields are all primitives or immutable; choose (or build) a deep clone whenever any field is a mutable reference type and true independence between original and copy is required — getting this choice wrong is a very common, quietly destructive bug (Level 3 below demonstrates exactly this).

## 3. Core concept

```java
class Address {
    String city;
    Address(String city) { this.city = city; }
    Address deepCopy() { return new Address(this.city); } // Address's own deep-copy helper
}

class Person implements Cloneable {
    String name;
    Address address; // a mutable reference field, itself needing deep copy

    Person(String name, Address address) { this.name = name; this.address = address; }

    @Override
    public Person clone() {
        try {
            Person copy = (Person) super.clone();  // shallow: address reference still shared here
            copy.address = address.deepCopy();      // now genuinely deep: address itself duplicated
            return copy;
        } catch (CloneNotSupportedException e) {
            throw new AssertionError(e);
        }
    }
}
```

`Person.clone()` demonstrates the full deep-copy pattern: `super.clone()` handles the shallow part (duplicating `name`, which is fine since `String` is immutable), and then `copy.address = address.deepCopy()` explicitly replaces the shared `Address` reference with a genuinely new, independent `Address` object — this pattern (shallow copy, then manually deep-copy each mutable reference field) generalizes to classes with any number of such fields.

## 4. Diagram

<svg viewBox="0 0 600 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Shallow clone leaves reference fields pointing to the same shared object, deep clone recursively duplicates every mutable reference field so nothing is shared">
  <rect x="8" y="8" width="584" height="194" rx="8" fill="#0d1117"/>

  <text x="150" y="28" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Shallow clone</text>
  <rect x="40" y="35" width="100" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="55" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">original</text>
  <rect x="180" y="35" width="100" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="230" y="55" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">clone</text>
  <line x1="90" y1="65" x2="150" y2="95" stroke="#f85149" stroke-width="1.5"/>
  <line x1="230" y1="65" x2="150" y2="95" stroke="#f85149" stroke-width="1.5"/>
  <rect x="110" y="98" width="80" height="28" rx="6" fill="#1c2430" stroke="#f85149" stroke-width="2"/>
  <text x="150" y="117" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">shared data</text>

  <text x="450" y="28" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Deep clone</text>
  <rect x="360" y="35" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="405" y="55" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">original</text>
  <rect x="360" y="98" width="90" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="405" y="117" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">own data copy</text>
  <line x1="405" y1="65" x2="405" y2="98" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="490" y="35" width="90" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="55" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">clone</text>
  <rect x="490" y="98" width="90" height="28" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="117" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">own data copy</text>
  <line x1="535" y1="65" x2="535" y2="98" stroke="#8b949e" stroke-width="1.5"/>

  <text x="300" y="175" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Shallow: both objects point to the same mutable data underneath.</text>
  <text x="300" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Deep: each object has its own fully independent copy of that data.</text>
</svg>

Shallow cloning shares nested mutable data; deep cloning duplicates it so nothing is shared.

## 5. Runnable example

Scenario: a `Team` object holding a roster of `Player` objects, evolved from a shallow clone (that silently shares the roster) into a deep clone that truly isolates a copied team from the original.

### Level 1 — Basic

```java
import java.util.ArrayList;
import java.util.List;

public class ShallowDeepBasic {
    static class Player {
        String name;
        Player(String name) { this.name = name; }
    }

    static class Team implements Cloneable {
        List<Player> roster;
        Team(List<Player> roster) { this.roster = roster; }

        @Override
        public Team clone() {
            try {
                return (Team) super.clone(); // shallow: roster list reference is shared
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    public static void main(String[] args) {
        Team original = new Team(new ArrayList<>(List.of(new Player("Sam"))));
        Team copy = original.clone();
        System.out.println(original.roster == copy.roster); // true — SAME list object
    }
}
```

**How to run:** `java ShallowDeepBasic.java`

`original.roster == copy.roster` is `true`, meaning both `Team` objects, despite being distinct, share the exact same underlying `List<Player>` — a shallow clone here has not truly separated the two teams' rosters at all.

### Level 2 — Intermediate

Same `Team`, now demonstrating the concrete consequence of that shared roster: adding a player to the clone's roster unexpectedly also affects the original.

```java
import java.util.ArrayList;
import java.util.List;

public class ShallowDeepIntermediate {
    static class Player {
        String name;
        Player(String name) { this.name = name; }
    }

    static class Team implements Cloneable {
        List<Player> roster;
        Team(List<Player> roster) { this.roster = roster; }

        @Override
        public Team clone() {
            try {
                return (Team) super.clone();
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    public static void main(String[] args) {
        Team original = new Team(new ArrayList<>(List.of(new Player("Sam"))));
        Team copy = original.clone();

        copy.roster.add(new Player("Jordan")); // mutate the clone's roster...

        System.out.println(original.roster.size()); // 2! the original was affected too
    }
}
```

**How to run:** `java ShallowDeepIntermediate.java`

Adding `"Jordan"` to `copy.roster` unexpectedly grows `original.roster` to size `2` as well, because both fields reference the exact same `ArrayList` instance — this is the shallow-clone pitfall causing real, observable data corruption between two objects that should have been independent.

### Level 3 — Advanced

Same `Team`, now with a genuine deep clone: a new `ArrayList` is built, and each `Player` inside it is itself duplicated (not shared), fully isolating the copy from the original at every level.

```java
import java.util.ArrayList;
import java.util.List;

public class ShallowDeepAdvanced {
    static class Player implements Cloneable {
        String name;
        Player(String name) { this.name = name; }

        @Override
        public Player clone() {
            try {
                return (Player) super.clone(); // fine here: name is an immutable String
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    static class Team implements Cloneable {
        List<Player> roster;
        Team(List<Player> roster) { this.roster = roster; }

        @Override
        public Team clone() {
            try {
                Team copy = (Team) super.clone();
                copy.roster = new ArrayList<>();          // brand-new list, not shared
                for (Player p : roster) {
                    copy.roster.add(p.clone());             // deep-copy each Player too
                }
                return copy;
            } catch (CloneNotSupportedException e) {
                throw new AssertionError(e);
            }
        }
    }

    public static void main(String[] args) {
        Team original = new Team(new ArrayList<>(List.of(new Player("Sam"))));
        Team copy = original.clone();

        copy.roster.add(new Player("Jordan"));    // mutate the clone's roster
        copy.roster.get(0).name = "Samuel";        // even mutate a shared-looking Player's field

        System.out.println("Original size: " + original.roster.size()); // 1 — unaffected
        System.out.println("Original player 0: " + original.roster.get(0).name); // "Sam" — unaffected
        System.out.println("Copy size: " + copy.roster.size());          // 2
        System.out.println("Copy player 0: " + copy.roster.get(0).name);  // "Samuel"
    }
}
```

**How to run:** `java ShallowDeepAdvanced.java`

`copy.roster = new ArrayList<>()` followed by copying each `p.clone()` individually means `original.roster` and `copy.roster` are two entirely separate `ArrayList` instances, each containing its own separate `Player` objects — mutating the clone's list, or even a field on one of the clone's `Player` objects, has zero effect on the original team or its players.

## 6. Walkthrough

Trace `main` in `ShallowDeepAdvanced` from construction through the final prints.

**Constructing `original`.** A `Team` is built with a new `ArrayList` containing one `Player("Sam")`. Call this list `L1` and this player `P1`.

**`original.clone()`.** `super.clone()` performs the shallow copy first: the new `Team` object's `roster` field temporarily points to `L1` (same list as `original`). Immediately after, `copy.roster = new ArrayList<>()` replaces it with a brand-new, empty list — call it `L2` — completely disconnecting `copy.roster` from `L1`. The `for` loop then iterates over `original.roster` (still `L1`, containing just `P1`), calling `P1.clone()`, which (via `Player`'s own `super.clone()`) produces a new `Player` object, `P2`, with `name = "Sam"` copied by value (since `String` is immutable, sharing the reference is harmless). `P2` is added to `L2`. The method returns `copy`, whose `roster` is `L2 = [P2]`.

**`copy.roster.add(new Player("Jordan"))`.** A new `Player`, `P3`, is created and added to `L2`. `L2` is now `[P2, P3]`. `L1` (still referenced only by `original.roster`) is completely untouched — it remains `[P1]`.

**`copy.roster.get(0).name = "Samuel"`.** `copy.roster.get(0)` retrieves `P2` from `L2`. Its `name` field is reassigned from `"Sam"` to `"Samuel"`. `P1` (a separate object, referenced only through `L1`) is entirely unaffected — its `name` remains `"Sam"`.

**Printing the results.** `original.roster.size()` reads `L1`'s size: `1`. `original.roster.get(0).name` reads `P1.name`: `"Sam"`. `copy.roster.size()` reads `L2`'s size: `2`. `copy.roster.get(0).name` reads `P2.name`: `"Samuel"`.

```
original.roster (L1) = [P1("Sam")]           <- never touched again
copy.clone():
  copy.roster = new L2 (empty)
  L2.add(P1.clone() = P2("Sam"))              -> L2 = [P2("Sam")]

copy.roster.add(P3("Jordan"))                 -> L2 = [P2("Sam"), P3("Jordan")]
copy.roster.get(0).name = "Samuel"            -> P2.name becomes "Samuel" (P1 untouched)

original: size=1, player0="Sam"     (L1 = [P1("Sam")], unaffected throughout)
copy:     size=2, player0="Samuel"  (L2 = [P2("Samuel"), P3("Jordan")])
```

**Final output.**
```
Original size: 1
Original player 0: Sam
Copy size: 2
Copy player 0: Samuel
```
This confirms full independence: mutations to the clone's roster list, and even to a field deep inside one of the clone's `Player` objects, leave the original `Team` and its `Player` completely unaffected.

## 7. Gotchas & takeaways

> **A "deep enough" clone depends entirely on what your class actually contains** — `Player.clone()` only needed a shallow `super.clone()` because its only field, `name`, is an immutable `String`; had `Player` instead held a mutable field (say, a `List<String> nicknames`), its `clone()` would itself need to deep-copy that field too. Deep cloning is recursive in principle: go exactly as deep as there is mutable, shared state to protect.

> **Collections like `ArrayList` do not implement a deep-copying `clone()` themselves** — `new ArrayList<>(original)` (the copy constructor) or `original.clone()` on an `ArrayList` both copy the list structure itself, but every element inside is still copied by reference; if the elements are mutable, they must be cloned individually, exactly as the loop in `Team.clone()` does.

- A shallow clone copies primitives by value but reference fields by reference, leaving the original and the clone sharing the same underlying mutable data.
- A deep clone recursively duplicates every mutable reference field (and, transitively, whatever they reference), so the original and the clone share nothing mutable.
- Immutable fields (like `String`) never need deep copying — sharing a reference to immutable data is always safe, since it can never change out from under either object.
- Deciding shallow versus deep is a per-field, per-class judgment call: copy only as deeply as there is mutable state that must not be shared between the original and its clone.
