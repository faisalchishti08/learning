---
card: java
gi: 773
slug: flexible-constructor-bodies-2nd-preview
title: Flexible constructor bodies (2nd preview)
---

## 1. What it is

**Java 23** (JEP 482) is the **second preview** of [statements before `super(...)`](0761-statements-before-super-preview.md), continuing from its first preview round in Java 22. The core capability is unchanged: a constructor may contain statements before its explicit `super(...)`/`this(...)` call, as long as those statements don't reference the instance under construction. This round refines the edge cases, most notably around **inner classes**: an inner class constructor's prologue may now reference its **enclosing instance** (e.g. `Outer.this`), because the enclosing instance already fully exists — it is not the object currently being constructed — even though earlier wording had been stricter than necessary about anything resembling an implicit `this`.

## 2. Why & when

The first preview nailed the main case — validating arguments and precomputing values before `super(...)` — but inner classes exposed a gap: an inner class always implicitly captures a reference to its enclosing instance, and the first preview's rules were conservative enough to treat that captured reference as off-limits in the prologue too, even though the enclosing instance is a completely separate, already-fully-constructed object with nothing to do with the safety guarantee the rule exists to protect. That's an unnecessary restriction for a common pattern: an inner class constructor that wants to validate an argument *against the enclosing instance's state* before calling `super(...)` — for example, checking that an index is within the bounds of the enclosing collection. This round's refinement fixes exactly that: the enclosing instance is now usable in the prologue, while the instance actually under construction remains just as off-limits as before.

## 3. Core concept

```java
class Roster {
    private final String[] names;

    Roster(String[] names) { this.names = names; }

    class Slot {
        private final int index;

        Slot(int index) {
            // Prologue: references the ENCLOSING Roster instance, which
            // already fully exists — legal even before super()/this() below.
            if (index < 0 || index >= Roster.this.names.length) {
                throw new IndexOutOfBoundsException("bad index: " + index);
            }
            super();
            this.index = index;
        }
    }
}
```

`Roster.this.names` reads the already-constructed enclosing `Roster`'s field — legal in the prologue, unlike reading anything on the `Slot` instance itself.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An inner class constructor prologue may reference the already-existing enclosing instance, but still may not reference the instance currently under construction">
  <rect x="20" y="20" width="260" height="60" rx="8" fill="#0f1620" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="45" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Outer.this (enclosing instance)</text>
  <text x="150" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">already fully constructed — OK in prologue</text>

  <rect x="360" y="20" width="260" height="60" rx="8" fill="#0f1620" stroke="#f85149"/>
  <text x="490" y="45" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">this (instance under construction)</text>
  <text x="490" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">still forbidden before super()/this()</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Second preview: only the "already exists" object may be touched early</text>
</svg>

*The safety rule stays the same — only what counts as "the instance under construction" is clarified for inner classes.*

## 5. Runnable example

Scenario: an inner `Slot` class that must validate its index against the enclosing `Roster`'s size before construction, growing from a workaround into the second preview's direct enclosing-instance access.

### Level 1 — Basic

```java
public class RosterWorkaround {
    static class Roster {
        private final String[] names;

        Roster(String[] names) { this.names = names; }

        static int validate(String[] names, int index) {
            if (index < 0 || index >= names.length) {
                throw new IndexOutOfBoundsException("bad index: " + index);
            }
            return index;
        }

        class Slot {
            private final int index;

            Slot(int index) {
                // Workaround: validate via a static helper, passing the
                // enclosing array explicitly, since Outer.this wasn't usable.
                this.index = validate(names, index);
            }
        }
    }

    public static void main(String[] args) {
        Roster roster = new Roster(new String[] {"Ada", "Grace"});
        Roster.Slot slot = roster.new Slot(1);
        System.out.println("valid slot: " + slot.index);
    }
}
```

**How to run:** `java RosterWorkaround.java` (JDK 22+; this workaround pattern works on any JDK).

`validate` is a static helper taking the enclosing array as an explicit parameter — a workaround needed because the constructor body couldn't yet reference the enclosing instance before construction of `Slot` completed.

### Level 2 — Intermediate

```java
public class RosterSecondPreview {
    static class Roster {
        private final String[] names;

        Roster(String[] names) { this.names = names; }

        class Slot {
            private final int index;

            Slot(int index) {
                // Prologue directly reads the enclosing Roster's field —
                // legal under the second preview's refined rule.
                if (index < 0 || index >= Roster.this.names.length) {
                    throw new IndexOutOfBoundsException("bad index: " + index);
                }
                super();
                this.index = index;
            }
        }
    }

    public static void main(String[] args) {
        Roster roster = new Roster(new String[] {"Ada", "Grace"});
        Roster.Slot slot = roster.new Slot(1);
        System.out.println("valid slot: " + slot.index);

        try {
            roster.new Slot(5);
        } catch (IndexOutOfBoundsException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** `java --enable-preview --source 23 RosterSecondPreview.java`.

The real-world concern added: `Slot`'s constructor validates directly against `Roster.this.names.length` — the enclosing instance's own field — with no static helper and no extra parameter, because the enclosing `Roster` is already fully constructed by the time any `Slot` is created inside it.

### Level 3 — Advanced

```java
public class RosterAdvanced {
    static class Roster {
        private final String[] names;
        private int slotsCreated = 0;

        Roster(String[] names) { this.names = names; }

        class Slot {
            private final int index;
            private final String label;

            Slot(int index) {
                if (index < 0 || index >= Roster.this.names.length) {
                    throw new IndexOutOfBoundsException("bad index: " + index);
                }
                String computedLabel = Roster.this.names[index] + "#" + index;
                super();
                this.index = index;
                this.label = computedLabel;
                Roster.this.slotsCreated++; // safe: after super(), Slot exists
            }
        }
    }

    public static void main(String[] args) {
        Roster roster = new Roster(new String[] {"Ada", "Grace", "Linus"});
        Roster.Slot a = roster.new Slot(0);
        Roster.Slot b = roster.new Slot(2);
        System.out.println(a.label + ", " + b.label);
        System.out.println("slots created: " + roster.slotsCreated);

        try {
            roster.new Slot(9);
        } catch (IndexOutOfBoundsException e) {
            System.out.println("rejected: " + e.getMessage());
        }
        System.out.println("slots created after failure: " + roster.slotsCreated);
    }
}
```

**How to run:** `java --enable-preview --source 23 RosterAdvanced.java`.

This adds the production-flavored hard case: the prologue not only **reads** the enclosing instance (`Roster.this.names[index]`) to compute a derived value, but the constructor **after** `super()` also **mutates** the enclosing instance (`Roster.this.slotsCreated++`) — legal because by that point `super()` has completed and `this` (the `Slot`) safely exists, showing the boundary precisely: enclosing-instance reads are fine even early, but any statement touching the `Slot` itself still must come after `super()`.

## 6. Walkthrough

Tracing `RosterAdvanced.main`'s failing call, `roster.new Slot(9)`:

1. `Slot`'s constructor begins running with `index = 9` and its implicit captured reference to the enclosing `roster` instance already set (inner class instances capture their enclosing instance as part of object creation, before the constructor body runs).
2. The prologue check `index < 0 || index >= Roster.this.names.length` evaluates `Roster.this.names.length`, which is `3` — since `9 >= 3`, the condition is true, and `IndexOutOfBoundsException` is thrown immediately, **before** `super()` and before any `Slot` field is set.
3. Because the exception is thrown before `super()`, no `Slot` object is ever fully constructed, and critically `Roster.this.slotsCreated` is **never incremented** for this failed attempt — the increment statement lives after `super()`, which is never reached.
4. `main`'s `catch` block catches the exception and prints the rejection message; the subsequent `System.out.println("slots created after failure: ...")` shows the counter unchanged from the two earlier successful creations.

For a successful call, `roster.new Slot(0)`:
1. The bounds check passes (`0` is a valid index into a 3-element array).
2. `computedLabel = Roster.this.names[0] + "#" + 0` reads the enclosing `Roster`'s array to compute `"Ada#0"` — this is a prologue statement, but it only reads the already-existing `Roster`, never the not-yet-constructed `Slot`, so it's legal.
3. `super()` runs (the implicit `Object` constructor), after which `this.index` and `this.label` are set on the now-permitted-to-touch `Slot` instance.
4. `Roster.this.slotsCreated++` runs last, safely mutating the enclosing instance now that `Slot` itself is fully initialized.

Expected output:
```
Ada#0, Linus#2
slots created: 2
rejected: bad index: 9
slots created after failure: 2
```

## 7. Gotchas & takeaways

> **Gotcha:** the relaxation applies only to the **enclosing** instance, never to the instance actually under construction. `this.index` or any read of a `Slot` field is still illegal before `super()` — only `Roster.this` (a different, already-complete object) gained early access. Confusing "the enclosing instance" with "the instance under construction" is an easy mistake when skimming code that uses both `this` and `Outer.this` near each other.

- Second preview in Java 23 (JEP 482), continuing from Java 22's [first preview](0761-statements-before-super-preview.md) — still requires `--enable-preview`.
- New in this round: an inner class constructor's prologue may reference its already-existing **enclosing instance** (`Outer.this`), even before `super()`/`this()`.
- The core safety guarantee is unchanged: the instance actually being constructed remains completely inaccessible until after `super()`/`this()` completes.
- This removes the last common workaround for inner classes — passing enclosing state through an extra static-helper parameter purely to validate before construction.
- Still a preview feature — expect further refinement before this and the original prologue relaxation are finalized together.
