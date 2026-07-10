---
card: java
gi: 921
slug: method-inlining
title: Method inlining
---

## 1. What it is

Method inlining is a JIT compiler optimization that replaces a call to a small, frequently-invoked method with a direct copy of that method's own compiled code at the call site — eliminating the overhead of the call itself (setting up a new [stack frame](0913-jvm-stacks-stack-frames.md), jumping to the method's code, jumping back) and, just as importantly, opening the door to *further* optimizations that only become possible once the caller and callee's code are merged into one contiguous block the optimizer can analyze together. The [C2 compiler](0919-jit-compilation-c1-client-c2-server.md) decides which calls to inline based on the method's size, how "hot" the call site is, and — critically — how confident it can be about which actual method implementation will run at that call site, informed by the type-profiling data gathered during [tiered compilation](0920-tiered-compilation.md)'s earlier stages.

## 2. Why & when

Inlining matters enormously for idiomatic, well-encapsulated Java code, which tends to be built from many small methods (getters, setters, tiny helper methods, one-line delegating calls) — without inlining, each of these would carry real per-call overhead that, multiplied across millions of invocations in a hot loop, would add up to significant, unnecessary cost. Inlining is also the enabling optimization behind much of the JIT compiler's other work: once a getter's body is inlined directly into its caller, the surrounding code can often be further optimized (e.g., proving a value never escapes, enabling [escape analysis and scalar replacement](0922-escape-analysis-scalar-replacement.md)) in ways that wouldn't be possible while the getter remained a genuinely separate call. Understanding inlining explains why writing small, well-named helper methods for clarity generally doesn't cost real performance in hot Java code (contrary to older, pre-JIT-era intuitions from other languages) — the compiler frequently inlines them away entirely, and why virtual/polymorphic call sites (where the actual implementation called can vary) are harder to inline confidently than simple, monomorphic ones, a topic worth understanding for genuinely performance-critical code.

## 3. Core concept

```java
class Point {
    private final int x, y;
    Point(int x, int y) { this.x = x; this.y = y; }
    int getX() { return x; } // tiny, frequently-called -- a prime inlining candidate
    int getY() { return y; }
}

int distanceSquared(Point p1, Point p2) {
    int dx = p1.getX() - p2.getX(); // once hot, the JIT can inline getX() directly here
    int dy = p1.getY() - p2.getY();
    return dx * dx + dy * dy;
}
// After inlining, the compiled code for distanceSquared effectively becomes as if
// getX()/getY() had been written inline by hand -- with NO actual method-call overhead
// remaining, and the resulting merged code open to further optimization.
```

The source code retains its clean, encapsulated structure (private fields, accessor methods); the JIT compiler is what collapses that structure away at the machine-code level, once it's confident doing so is safe and beneficial.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before inlining, a call site jumps out to a separate getX method and back; after inlining, the getX method's own logic is copied directly into the caller's compiled code, with no call/return overhead remaining">
  <text x="160" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Before inlining</text>
  <rect x="20" y="35" width="260" height="35" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="150" y="57" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">caller: ... call getX() ... use result ...</text>
  <rect x="60" y="90" width="180" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="110" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">separate getX() frame, jump + return</text>
  <line x1="150" y1="70" x2="150" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a49)"/>

  <text x="480" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">After inlining</text>
  <rect x="360" y="45" width="260" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="490" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">caller: ... [getX's logic COPIED IN] ...</text>
  <text x="490" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">no call, no separate frame, no jump</text>
  <defs><marker id="a49" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Inlining physically merges the callee's compiled logic into the caller, eliminating call overhead and opening the merged code up to further, cross-method optimization.*

## 5. Runnable example

Scenario: measuring inlining's real performance impact via getter-heavy code, growing from a baseline demonstrating small-method overhead essentially disappears once hot, to deliberately preventing inlining to make its cost visible, to a polymorphic call-site case showing why virtual dispatch complicates inlining.

### Level 1 — Basic

```java
public class TrivialGettersGetInlined {
    static class Point {
        private final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        int getX() { return x; }
        int getY() { return y; }
    }

    static long distanceSquared(Point a, Point b) {
        int dx = a.getX() - b.getX();
        int dy = a.getY() - b.getY();
        return (long) dx * dx + (long) dy * dy;
    }

    public static void main(String[] args) {
        Point[] points = new Point[1000];
        for (int i = 0; i < points.length; i++) points[i] = new Point(i, i * 2);

        long start = System.nanoTime();
        long total = 0;
        for (int iter = 0; iter < 50_000; iter++) {
            for (int i = 0; i < points.length - 1; i++) {
                total += distanceSquared(points[i], points[i + 1]); // millions of getX()/getY() calls
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total=" + total + ", elapsed=" + elapsedMs + "ms");
        System.out.println("(after warm-up, getX()/getY() calls have essentially ZERO overhead -- inlined away)");
    }
}
```

**How to run:** `java TrivialGettersGetInlined.java` (JDK 17+).

Expected output shape (machine-dependent, but notably fast given the enormous number of logical getter calls involved):
```
total=..., elapsed=95ms
(after warm-up, getX()/getY() calls have essentially ZERO overhead -- inlined away)
```

Despite calling `getX()`/`getY()` many millions of times through the nested loops, the JIT compiler inlines these trivial accessor methods directly into `distanceSquared`'s compiled code once it's identified as hot, making the encapsulated, "clean code" style essentially free at runtime.

### Level 2 — Intermediate

```java
public class ForcingNoInlineComparison {
    static class Point {
        private final int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
        int getX() { return x; }
        int getY() { return y; }
    }

    static long distanceSquared(Point a, Point b) {
        int dx = a.getX() - b.getX();
        int dy = a.getY() - b.getY();
        return (long) dx * dx + (long) dy * dy;
    }

    public static void main(String[] args) {
        Point[] points = new Point[1000];
        for (int i = 0; i < points.length; i++) points[i] = new Point(i, i * 2);

        long start = System.nanoTime();
        long total = 0;
        for (int iter = 0; iter < 50_000; iter++) {
            for (int i = 0; i < points.length - 1; i++) {
                total += distanceSquared(points[i], points[i + 1]);
            }
        }
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total=" + total + ", elapsed=" + elapsedMs + "ms");
    }
}
```

**How to run:** `java -XX:CompileCommand=dontinline,ForcingNoInlineComparison$Point::getX -XX:CompileCommand=dontinline,ForcingNoInlineComparison$Point::getY ForcingNoInlineComparison.java` (JDK 17+; this flag explicitly forbids the JIT from inlining these two specific methods, letting their true, un-inlined call overhead show through for comparison against Level 1's result).

Expected output shape (typically slower than the freely-inlined version in Level 1, since real call overhead is now paid on every single invocation):
```
total=..., elapsed=210ms
```

The real-world concern added: forcibly disabling inlining for `getX`/`getY` specifically, via `-XX:CompileCommand=dontinline`, makes their true per-call overhead visible — the resulting elapsed time is measurably worse than the freely-optimized version, directly demonstrating inlining's real contribution to making small, well-encapsulated methods essentially free in practice.

### Level 3 — Advanced

```java
public class PolymorphicCallSiteChallenge {
    interface Shape { double area(); }
    static class Circle implements Shape {
        double r;
        Circle(double r) { this.r = r; }
        public double area() { return Math.PI * r * r; }
    }
    static class Square implements Shape {
        double side;
        Square(double side) { this.side = side; }
        public double area() { return side * side; }
    }

    static double sumAreas(Shape[] shapes) {
        double total = 0;
        for (Shape s : shapes) total += s.area(); // POLYMORPHIC call site -- which area() runs varies per element
        return total;
    }

    public static void main(String[] args) {
        // MONOMORPHIC case: every element is the SAME concrete type -- easiest to inline confidently
        Shape[] allCircles = new Shape[10_000];
        for (int i = 0; i < allCircles.length; i++) allCircles[i] = new Circle(i % 10 + 1);

        // MEGAMORPHIC-leaning case: alternating between TWO concrete types at the SAME call site --
        // harder for the JIT to inline with full confidence, since it must handle both possibilities
        Shape[] mixed = new Shape[10_000];
        for (int i = 0; i < mixed.length; i++) {
            mixed[i] = (i % 2 == 0) ? new Circle(i % 10 + 1) : new Square(i % 10 + 1);
        }

        long start1 = System.nanoTime();
        double total1 = 0;
        for (int i = 0; i < 5000; i++) total1 += sumAreas(allCircles);
        long elapsed1 = (System.nanoTime() - start1) / 1_000_000;

        long start2 = System.nanoTime();
        double total2 = 0;
        for (int i = 0; i < 5000; i++) total2 += sumAreas(mixed);
        long elapsed2 = (System.nanoTime() - start2) / 1_000_000;

        System.out.println("monomorphic (all Circle) call site: " + elapsed1 + "ms");
        System.out.println("polymorphic (mixed Circle/Square) call site: " + elapsed2 + "ms (often somewhat slower)");
    }
}
```

**How to run:** `java PolymorphicCallSiteChallenge.java` (JDK 17+).

Expected output shape (the mixed-type version is often somewhat slower, reflecting the harder inlining/dispatch problem, though the exact gap depends heavily on JVM version and machine):
```
monomorphic (all Circle) call site: 48ms
polymorphic (mixed Circle/Square) call site: 72ms (often somewhat slower)
```

This adds the production-flavored hard case: comparing a **monomorphic** call site (every array element is the same concrete `Circle` type, so the JIT can confidently inline `Circle.area()` directly and speculatively assume that type going forward, informed by the type profile from tiered compilation) against a call site alternating between two concrete types (`Circle` and `Square`) — the JIT can still often optimize this reasonably well (e.g., via a small inline cache checking for one of a couple of expected types), but it's a fundamentally harder inlining problem than the monomorphic case, since no single inlined implementation is correct for every call; understanding this distinction is valuable for genuinely performance-critical hot paths where call-site type diversity could be a real, measurable cost.

## 6. Walkthrough

Reasoning through why the monomorphic call site tends to outperform the polymorphic one:

1. In the `allCircles` array, every single element passed to `sumAreas`'s `s.area()` call site is actually a `Circle` at runtime — the type-profiling data gathered during tiered compilation's C1 stages observes this consistently, giving C2 strong confidence that inlining `Circle.area()`'s specific implementation directly at this call site (with a cheap guard checking the actual type still matches, in case that ever changes) will be correct essentially every time.
2. With that confidence, C2 can inline `Circle.area()`'s body (`Math.PI * r * r`) directly into `sumAreas`'s compiled code, eliminating virtual dispatch overhead (looking up which implementation to call based on the object's actual type) entirely for the common case, and opening the merged code to further optimization.
3. In the `mixed` array, the same call site alternates between `Circle.area()` and `Square.area()` — the type profile now shows genuine diversity at this one call site, so there's no single implementation the JIT can confidently inline as "the" answer; it typically falls back to a slightly more expensive strategy, such as an inline cache that checks the actual type and dispatches to one of a couple of specifically-anticipated implementations, or in the worst case, a full virtual method table lookup if the diversity is too great to specialize for efficiently.
4. This additional per-call type-checking/dispatch overhead, multiplied across the many millions of calls in this benchmark's loops, is what typically shows up as the polymorphic version's somewhat slower measured time — a direct, practical consequence of how much harder confident inlining becomes once a call site genuinely sees more than one implementation in practice.
5. It's worth noting this effect is usually far smaller than one might expect from purely theoretical reasoning — modern JIT compilers handle even moderate polymorphism (2-3 implementations at one call site) quite well via inline caching techniques; the effect becomes much more pronounced with a large number of genuinely different implementations hit unpredictably at the same call site ("megamorphic" call sites), which is a more specialized concern than most everyday code needs to worry about.

## 7. Gotchas & takeaways

> **Gotcha:** inlining decisions, thresholds, and the exact mechanisms for handling polymorphic call sites are JIT-implementation details that can vary meaningfully across JVM versions and vendors — never hard-code assumptions about exactly what will or won't be inlined into production logic; if a specific hot path's performance genuinely matters, measure it directly (with proper warm-up) rather than reasoning from a fixed mental model of inlining rules that may not hold on a different JVM version.

- Method inlining replaces a call to a small, hot method with a direct copy of its compiled logic at the call site, eliminating call overhead and enabling further optimizations on the merged code.
- This is exactly why writing small, well-encapsulated helper methods, getters, and setters generally costs no real performance in hot Java code — the JIT compiler routinely inlines them away once they're identified as worth optimizing.
- Confident inlining is easiest at monomorphic call sites (consistently one actual implementation observed) and progressively harder as a call site sees more genuine implementation diversity (polymorphic, and especially megamorphic, call sites).
- Type-profiling data gathered during [tiered compilation](0920-tiered-compilation.md)'s C1 stages is exactly what informs C2's inlining confidence — this is one of the concrete mechanisms by which the intermediate profiling levels pay for themselves.
- See [escape analysis & scalar replacement](0922-escape-analysis-scalar-replacement.md) for one of the most powerful further optimizations that inlining directly enables, by merging caller and callee code into one analyzable unit.
