---
card: java
gi: 991
slug: solid-liskov-substitution
title: SOLID — Liskov Substitution
---

## 1. What it is

The **Liskov Substitution Principle (LSP)**, named after Barbara Liskov, says: if `S` is a subtype of `T`, then objects of type `T` should be replaceable with objects of type `S` **without altering the correctness of the program**. In plain terms — if your code works with a `Bird`, it must keep working, unmodified, when handed any subclass of `Bird`. A subclass shouldn't quietly weaken guarantees (throwing where the parent didn't, returning wildly different results) or strengthen requirements (demanding extra preconditions) that the caller wasn't written to expect.

## 2. Why & when

Inheritance is a promise: "wherever a `T` is expected, I behave like a `T`." When a subclass breaks that promise — the classic example is a `Square extends Rectangle` that overrides `setWidth` to also change the height — any code written against `Rectangle`'s contract (`setWidth` changes only the width) silently produces wrong answers the moment a `Square` is substituted in. These bugs are nasty because they don't fail at the call site that violates the contract; they fail somewhere far away, in code that trusted the parent type's documented behavior.

LSP matters whenever you're about to extend a class rather than compose with it. Ask: does this subclass honor every guarantee the parent makes (return types, thrown exceptions, side effects, invariants), or does it need to say "except in this case"? If it's the latter, inheritance is the wrong tool — composition or a shared interface with narrower guarantees usually fits better.

## 3. Core concept

```
// Violates LSP: Square silently breaks Rectangle's contract
class Rectangle {
    protected int width, height;
    void setWidth(int w) { width = w; }
    void setHeight(int h) { height = h; }
    int area() { return width * height; }
}
class Square extends Rectangle {
    @Override void setWidth(int w) { width = w; height = w; }   // surprise: also changes height
    @Override void setHeight(int h) { width = h; height = h; }  // surprise: also changes width
}

// Code written against Rectangle assumes setWidth leaves height alone:
Rectangle r = new Square(...);
r.setWidth(5);
r.setHeight(10);
// caller expects area() == 50, but a Square forces area() == 100 -- LSP violated
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Code calling setWidth then setHeight on a Rectangle reference gets a correct area, but the same calls on a substituted Square silently break the expected result">
  <rect x="40" y="30" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="150" y="50" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Rectangle r = new Rectangle();</text>
  <text x="150" y="68" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">setWidth(5); setHeight(10);</text>

  <rect x="40" y="110" width="220" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="130" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Rectangle r = new Square();</text>
  <text x="150" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">setWidth(5); setHeight(10);</text>

  <rect x="380" y="30" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="60" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">area() == 50 (correct)</text>

  <rect x="380" y="110" width="200" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="480" y="140" fill="#f0883e" font-size="13" text-anchor="middle" font-family="sans-serif">area() == 100 (surprise!)</text>

  <line x1="260" y1="55" x2="375" y2="55" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="260" y1="135" x2="375" y2="135" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Identical calls through the same `Rectangle`-typed reference produce different, surprising results depending on the concrete subtype — the substitution isn't safe.

## 5. Runnable example

Scenario: a shape hierarchy used by billing code that assumes setting width and height independently gives a predictable area — evolving from the classic broken `Square extends Rectangle` into a design where substitution is genuinely safe.

### Level 1 — Basic

```java
// File: LspBasic.java
class Rectangle {
    protected int width, height;
    void setWidth(int w) { width = w; }
    void setHeight(int h) { height = h; }
    int area() { return width * height; }
}

class Square extends Rectangle {
    @Override void setWidth(int w) { width = w; height = w; }
    @Override void setHeight(int h) { width = h; height = h; }
}

public class LspBasic {
    static int resizeAndMeasure(Rectangle r) {
        r.setWidth(5);
        r.setHeight(10);
        return r.area();
    }

    public static void main(String[] args) {
        System.out.println("Rectangle: " + resizeAndMeasure(new Rectangle()));
        System.out.println("Square:    " + resizeAndMeasure(new Square()));
    }
}
```

**How to run:** save as `LspBasic.java`, then `javac LspBasic.java && java LspBasic` (JDK 17+).

Expected output:
```
Rectangle: 50
Square:    100
```

`resizeAndMeasure` was written trusting the `Rectangle` contract (width and height are independent), but a `Square` silently violates it — same code, same reference type, different and surprising answer.

### Level 2 — Intermediate

```java
// File: LspIntermediate.java
// Fix: don't model Square as a Rectangle subclass at all. Use a common
// interface that only promises what every shape can actually guarantee.
interface Shape {
    int area();
}

class Rectangle implements Shape {
    private final int width, height;
    Rectangle(int width, int height) { this.width = width; this.height = height; }
    public int area() { return width * height; }
}

class Square implements Shape {
    private final int side;
    Square(int side) { this.side = side; }
    public int area() { return side * side; }
}

public class LspIntermediate {
    static int totalArea(Shape... shapes) {
        int total = 0;
        for (Shape s : shapes) total += s.area();
        return total;
    }

    public static void main(String[] args) {
        System.out.println(totalArea(new Rectangle(5, 10), new Square(4)));
    }
}
```

**How to run:** save as `LspIntermediate.java`, then `javac LspIntermediate.java && java LspIntermediate` (JDK 17+).

Expected output:
```
66
```

The real-world concern added: `Square` no longer inherits from `Rectangle`, so it can't inherit a mutable `setWidth`/`setHeight` contract it can't honor. Both shapes are immutable and only promise `area()` — a guarantee both can keep perfectly.

### Level 3 — Advanced

```java
// File: LspAdvanced.java
import java.util.List;

interface Shape {
    int area();
}

record Rectangle(int width, int height) implements Shape {
    Rectangle {
        if (width < 0 || height < 0) throw new IllegalArgumentException("dimensions must be non-negative");
    }
    public int area() { return width * height; }
}

record Square(int side) implements Shape {
    Square {
        if (side < 0) throw new IllegalArgumentException("side must be non-negative");
    }
    public int area() { return side * side; }
}

// A resizable variant that returns a NEW shape rather than mutating in place --
// this preserves substitutability because "resize" never has hidden side effects
// that differ by concrete type; every implementation just returns a fresh Shape.
interface ResizableShape extends Shape {
    ResizableShape scaledBy(double factor);
}

record ResizableRectangle(int width, int height) implements ResizableShape {
    public int area() { return width * height; }
    public ResizableShape scaledBy(double factor) {
        return new ResizableRectangle((int) (width * factor), (int) (height * factor));
    }
}

record ResizableSquare(int side) implements ResizableShape {
    public int area() { return side * side; }
    public ResizableShape scaledBy(double factor) {
        return new ResizableSquare((int) (side * factor));
    }
}

public class LspAdvanced {
    static int totalArea(List<Shape> shapes) {
        return shapes.stream().mapToInt(Shape::area).sum();
    }

    static ResizableShape doubleSize(ResizableShape shape) {
        return shape.scaledBy(2.0); // works identically for ANY ResizableShape, no surprises
    }

    public static void main(String[] args) {
        System.out.println(totalArea(List.of(new Rectangle(5, 10), new Square(4))));

        ResizableShape rect = doubleSize(new ResizableRectangle(5, 10));
        ResizableShape sq = doubleSize(new ResizableSquare(4));
        System.out.println("rect area after doubling: " + rect.area());
        System.out.println("square area after doubling: " + sq.area());
    }
}
```

**How to run:** save as `LspAdvanced.java`, then `javac LspAdvanced.java && java LspAdvanced` (JDK 17+).

Expected output:
```
66
rect area after doubling: 200
square area after doubling: 64
```

The production-flavored hard case: `ResizableShape.scaledBy` returns a brand-new shape rather than mutating fields, which is the key design move — it means `doubleSize` can treat every `ResizableShape` identically with zero risk of one implementation having hidden side effects (like the original `Square.setWidth` mutating height) that another doesn't.

## 6. Walkthrough

Tracing `doubleSize(new ResizableSquare(4))` in `LspAdvanced.main`:

1. `new ResizableSquare(4)` constructs a square-shaped record with `side = 4`.
2. `doubleSize(shape)` receives it through the `ResizableShape` parameter type — the method has no idea, and doesn't need to know, whether it's a rectangle or a square.
3. Inside `doubleSize`, `shape.scaledBy(2.0)` dispatches to `ResizableSquare.scaledBy`, which computes `(int) (4 * 2.0) = 8` and returns a **new** `ResizableSquare(8)` — the original instance passed in is untouched.
4. `doubleSize` returns that new `ResizableSquare(8)` up to `main`, which assigns it to `sq`.
5. `sq.area()` calls `ResizableSquare.area()` on the new instance: `8 * 8 = 64`, printed as `"square area after doubling: 64"`.
6. Compare with `rect`: `doubleSize(new ResizableRectangle(5, 10))` scales both dimensions to `10` and `20`, giving `area() == 200`. Both calls went through the exact same `doubleSize` method with the exact same substitution-safe contract — no branch, no type check, no surprise.

## 7. Gotchas & takeaways

> **Gotcha:** LSP violations are usually invisible at the point of inheritance — `Square extends Rectangle` compiles fine and even looks elegant ("a square *is* a rectangle," mathematically). The break only shows up later, in code that trusted the parent's contract and got a subtype that quietly didn't honor it.

- LSP: a subtype must be substitutable for its supertype without breaking the caller's expectations — same return types, no new thrown exceptions, no stronger preconditions, no different side effects.
- "IS-A" in the real world (a square is a rectangle) doesn't automatically mean "IS-A" in code if the supertype's contract includes mutable behavior the subtype can't honor.
- Preferring immutable data (records) with methods that return new instances instead of mutating shared state sidesteps a large class of LSP violations.
- When a subclass needs to override a method just to say "not for me" (throwing `UnsupportedOperationException`, weakening a guarantee), that's a strong signal inheritance is the wrong relationship — reach for [composition over inheritance](0995-composition-over-inheritance.md) instead.
- LSP is what makes [SOLID — Open/Closed](0990-solid-open-closed.md) safe in practice: OCP says "extend via new subtypes," and LSP is the rule that keeps those new subtypes trustworthy substitutes.
