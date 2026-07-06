---
card: java
gi: 227
slug: covariant-return-types-1-5
title: Covariant return types (1.5)
---

## 1. What it is

A **covariant return type**, introduced in Java 5, allows an overriding method to declare a **more specific (subtype) return type** than the method it overrides, instead of requiring an identical return type. This means an override can promise to return something more precise than its superclass's version, as long as that return type is itself a subtype of the original — giving callers of the subclass extra type information without breaking the overriding relationship.

```java
class Animal {
    Animal reproduce() { // returns the general type, Animal
        return new Animal();
    }
}

class Dog extends Animal {
    @Override
    Dog reproduce() { // covariant return: Dog is a SUBTYPE of Animal — this IS a valid override
        return new Dog();
    }
}

Dog puppy = new Dog().reproduce(); // no cast needed! reproduce() on a Dog already returns a Dog
```

`Dog.reproduce()` returns `Dog`, not `Animal` — this is a completely valid override specifically because `Dog` is a subtype of `Animal`, the return type declared by the method it's overriding; without covariant return types (as in versions of Java before 5.0, or in languages lacking this feature), `Dog.reproduce()` would have been forced to declare `Animal reproduce()` and callers would need an explicit downcast to get a `Dog` back out.

## 2. Why & when

Covariant return types exist to let overrides be more precise and useful than the strict "identical signature" rule would otherwise allow, without breaking the substitutability guarantee that overriding depends on:

- **More useful, precise APIs** — a subclass method that's guaranteed to always produce a more specific type can advertise that fact directly in its return type, sparing every caller from needing to downcast the result themselves.
- **Common in "clone" or "copy" style methods** — a method like `copy()` on a subclass often naturally wants to return that same subclass type, rather than the generic supertype, so further chained calls can use the subclass-specific type immediately.
- **Still fully substitutable** — because `Dog` genuinely *is* an `Animal`, any code that only expects `Animal reproduce()` (calling it through an `Animal`-typed reference) still works completely correctly — it just receives a `Dog`, which is perfectly acceptable wherever an `Animal` was expected.

You use covariant return types whenever an override can *guarantee* it always produces a more specific subtype than what the superclass method promises — this is common and encouraged wherever it naturally applies, since it improves the precision of a subclass's API at no cost to correctness or substitutability.

## 3. Core concept

```java
class Shape {
    Shape copy() {
        return new Shape();
    }
}

class Circle extends Shape {
    double radius;
    Circle(double radius) { this.radius = radius; }

    @Override
    Circle copy() { // covariant: Circle is a subtype of Shape
        return new Circle(this.radius);
    }
}

Circle original = new Circle(5);
Circle duplicate = original.copy(); // no cast needed — copy() on a Circle already returns a Circle
System.out.println(duplicate.radius); // 5.0 — direct access, no downcast required
```

`original.copy()` returns a `Circle` directly, so `duplicate.radius` is immediately accessible with no cast — if `Circle.copy()` had instead been forced to return the plain `Shape` type (without covariant returns), accessing `.radius` on the result would have required an explicit `(Circle)` downcast first, adding unnecessary boilerplate for something the method's implementation already guarantees.

## 4. Diagram

<svg viewBox="0 0 600 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Shape's copy method returning the general Shape type contrasted with Circle's overriding copy method returning the more specific Circle type directly, letting callers access Circle specific members immediately with no downcast required">
  <rect x="8" y="8" width="584" height="134" rx="8" fill="#0d1117"/>

  <rect x="30" y="30" width="230" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">Shape.copy() -&gt; Shape</text>

  <rect x="330" y="30" width="230" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="445" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">Circle.copy() -&gt; Circle</text>

  <text x="300" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Circle IS-A Shape, so returning Circle is a valid, MORE PRECISE override.</text>
  <text x="300" y="125" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Callers of Circle.copy() get a Circle directly — no downcast needed.</text>
</svg>

A covariant return type lets an override promise a more specific, subtype result than its superclass version.

## 5. Runnable example

Scenario: a small document-management system with a "duplicate" operation — starting with a basic covariant override, then extending with chained method calls benefiting directly from the more specific return type, then hardening into a case comparing covariant returns against the pre-Java-5 alternative to show the concrete difference.

### Level 1 — Basic

```java
public class CovariantBasic {
    static class Document {
        String title;
        Document(String title) { this.title = title; }

        Document duplicate() {
            return new Document(title + " (copy)");
        }
    }

    static class SpreadSheet extends Document {
        int rowCount;
        SpreadSheet(String title, int rowCount) {
            super(title);
            this.rowCount = rowCount;
        }

        @Override
        SpreadSheet duplicate() { // covariant: SpreadSheet is a subtype of Document
            return new SpreadSheet(title + " (copy)", rowCount);
        }
    }

    public static void main(String[] args) {
        SpreadSheet original = new SpreadSheet("Budget", 50);
        SpreadSheet copy = original.duplicate(); // no cast needed

        System.out.println(copy.title + ", rows=" + copy.rowCount);
    }
}
```

**How to run:** `java CovariantBasic.java`

`original.duplicate()` returns `SpreadSheet` directly (thanks to the covariant override), so `copy.rowCount` is immediately accessible — no explicit downcast was needed anywhere in `main`, since the compiler already knows `duplicate()` on a `SpreadSheet` produces another `SpreadSheet`.

### Level 2 — Intermediate

Same idea, now chaining a call directly onto the result of `duplicate()`, which is only possible without an intermediate cast because of the covariant return type.

```java
public class CovariantIntermediate {
    static class Document {
        String title;
        Document(String title) { this.title = title; }
        Document duplicate() { return new Document(title + " (copy)"); }
    }

    static class SpreadSheet extends Document {
        int rowCount;
        SpreadSheet(String title, int rowCount) { super(title); this.rowCount = rowCount; }

        @Override
        SpreadSheet duplicate() { return new SpreadSheet(title + " (copy)", rowCount); }

        void addRow() { rowCount++; }
    }

    public static void main(String[] args) {
        SpreadSheet original = new SpreadSheet("Budget", 50);

        original.duplicate().addRow(); // chained call — only possible because duplicate() returns SpreadSheet directly
        System.out.println("Chained call succeeded (no cast needed)");
    }
}
```

**How to run:** `java CovariantIntermediate.java`

`original.duplicate().addRow()` chains directly, since `duplicate()`'s covariant return type (`SpreadSheet`, not `Document`) means the result already has `addRow()` available on it — if `duplicate()` had returned the generic `Document` type instead, this chained call would fail to compile without an explicit downcast first, since `Document` itself declares no `addRow()` method.

### Level 3 — Advanced

Same system, now comparing a covariant override directly against a non-covariant one, demonstrating precisely the extra downcast step covariant returns eliminate.

```java
public class CovariantAdvanced {
    static class Document {
        String title;
        Document(String title) { this.title = title; }
        Document duplicateGeneric() { return new Document(title + " (copy)"); } // NOT overridden by SpreadSheet
    }

    static class SpreadSheet extends Document {
        int rowCount;
        SpreadSheet(String title, int rowCount) { super(title); this.rowCount = rowCount; }

        @Override
        SpreadSheet duplicate() { return new SpreadSheet(title + " (copy)", rowCount); } // covariant override

        void addRow() { rowCount++; }
    }

    public static void main(String[] args) {
        SpreadSheet original = new SpreadSheet("Budget", 50);

        // Using the COVARIANT override: direct access, no cast
        SpreadSheet copy1 = original.duplicate();
        copy1.addRow();
        System.out.println("Covariant path: rows=" + copy1.rowCount);

        // Using a hypothetical NON-covariant method (duplicateGeneric, inherited unchanged): requires a cast
        Document genericCopy = original.duplicateGeneric(); // returns plain Document — inherited, not overridden
        if (genericCopy instanceof SpreadSheet spreadSheetCopy) { // must check and cast explicitly
            spreadSheetCopy.addRow();
            System.out.println("Non-covariant path (after explicit cast): rows=" + spreadSheetCopy.rowCount);
        }
    }
}
```

**How to run:** `java CovariantAdvanced.java`

`original.duplicate()` (the covariant override) hands back a `SpreadSheet` directly, ready for `.addRow()` immediately; `original.duplicateGeneric()` (inherited unchanged from `Document`, since `SpreadSheet` never overrides it) returns the plain `Document` type, requiring an explicit `instanceof`-guarded downcast before `.addRow()` becomes callable — the side-by-side comparison makes the practical convenience covariant returns provide directly visible.

## 6. Walkthrough

Trace both paths in `CovariantAdvanced.main`:

**Covariant path.** `original.duplicate()` — since `original`'s actual and declared type here is `SpreadSheet`, and `SpreadSheet` overrides `duplicate()` with a covariant `SpreadSheet` return type, the call directly returns a `SpreadSheet` object, assigned to `copy1` with no cast. `copy1.addRow()` immediately increments `rowCount` from `50` to `51`. Prints `"Covariant path: rows=51"`.

**Non-covariant path.** `original.duplicateGeneric()` — `SpreadSheet` never overrides this method, so it's simply inherited unchanged from `Document`, and its declared return type remains `Document`. The result, `genericCopy`, is declared `Document`, even though the actual object created inside `duplicateGeneric()`'s body is a plain `new Document(...)` (not a `SpreadSheet`, since `duplicateGeneric` was never overridden to produce one). The `instanceof SpreadSheet spreadSheetCopy` check therefore evaluates `false` — the returned object genuinely is just a `Document`, not a `SpreadSheet` — so the `if` block is skipped entirely, and no second output line prints for this path in this particular run.

```
Covariant path:
  original.duplicate() -> returns SpreadSheet directly (covariant override)
  copy1.addRow() -> rowCount 50 -> 51
  print "Covariant path: rows=51"

Non-covariant path:
  original.duplicateGeneric() -> inherited from Document, returns a plain Document object
  genericCopy instanceof SpreadSheet? false (it's genuinely just a Document)
  if-block skipped -> no output for this path
```

**Final output.** Only one line prints: `"Covariant path: rows=51"` — the non-covariant path's `if` check correctly (if perhaps surprisingly) reveals that `duplicateGeneric()`, never having been overridden, produces a plain `Document`, not a `SpreadSheet`, reinforcing that covariant returns specifically require an *actual override* with a more specific return type — simply inheriting a method unchanged does not gain any of this benefit.

## 7. Gotchas & takeaways

> **A covariant return type is still bound by all the other overriding rules — the return type must be a genuine subtype of the original, not just any unrelated type.** `Circle copy()` overriding `Shape copy()` is valid because `Circle extends Shape`; attempting to override `Shape copy()` with, say, `String copy()` (an unrelated type) is a compile error, since `String` has no subtype relationship to `Shape`.

> **Covariant returns only take effect on a genuine override — a method inherited unchanged (like `duplicateGeneric` in the advanced example) keeps its original, superclass-declared return type, with no automatic narrowing.** Only writing an explicit override with a more specific return type actually gains the covariant benefit.

- Covariant return types (Java 5+) let an overriding method declare a more specific (subtype) return type than the method it overrides.
- This eliminates the need for callers to manually downcast a result they already know, from the override's guarantee, will be a specific subtype.
- The declared covariant return type must genuinely be a subtype of the original method's return type — any other type is a compile error.
- Only an actual override gains covariant benefits; a method simply inherited unchanged keeps the original superclass's declared return type.
