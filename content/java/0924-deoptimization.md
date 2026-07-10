---
card: java
gi: 924
slug: deoptimization
title: Deoptimization
---

## 1. What it is

Deoptimization is the JVM's safety net for undoing a speculative optimization once the assumption it relied on turns out to be wrong: the compiler falls back from running optimized, compiled native code to running the [interpreter](0918-bytecode-interpretation.md) again for that method, reconstructing the interpreter's full, correct state (every local variable, the current execution point) from whatever the compiled code's equivalent state was at the moment the assumption broke. Many of C2's most powerful optimizations — [method inlining](0921-method-inlining.md) based on an observed-but-not-guaranteed type at a call site, [escape analysis](0922-escape-analysis-scalar-replacement.md)'s aggressive assumptions, branch predictions based on profiling data — are inherently *speculative*: correct and beneficial for the overwhelmingly common case actually observed so far, but not something the compiler can prove will hold universally forever. Deoptimization is what makes taking that speculative risk safe: if reality ever diverges from the assumption (a new subclass shows up at a previously-monomorphic call site, for instance), the JVM detects it and gracefully falls back, rather than producing incorrect results or crashing.

## 2. Why & when

Understanding deoptimization explains why the JIT compiler is willing to make aggressive, profile-informed bets that pure, provably-safe static analysis alone could never justify — since any such bet always has a safe escape hatch if it turns out to be wrong. This directly matters for reasoning about a specific, sometimes-surprising performance phenomenon: code that runs very fast for a long stretch (because it's running well-optimized compiled code, speculatively specialized for the behavior observed so far) can suddenly slow down noticeably at some later point, if something happens that invalidates one of the compiler's earlier assumptions — a previously-unseen subclass finally gets passed to a hot, monomorphic call site, for example. Recognizing this pattern — a sudden performance dip well after a program has already warmed up — as a likely deoptimization event, rather than an unrelated mystery, is a genuinely useful diagnostic skill; JVM flags like `-XX:+PrintCompilation` (whose output includes deoptimization events) and `-XX:+TraceDeoptimization` make this directly observable rather than something you have to merely infer.

## 3. Core concept

```java
interface Shape { double area(); }
class Circle implements Shape { public double area() { return 3.14; } }
class Square implements Shape { public double area() { return 4.0; } }

double sumAreas(Shape[] shapes) {
    double total = 0;
    for (Shape s : shapes) total += s.area(); // if ONLY Circles ever appear here, JIT may speculatively
    return total;                              // inline Circle.area() directly, betting that stays true
}
// If a Square LATER appears at this same call site (after the speculative, Circle-only-optimized
// version is already running), the JVM detects the assumption broke, DEOPTIMIZES this method
// back to the interpreter (or a less-specialized compiled version), and recompiles more generally --
// this time correctly accounting for BOTH Circle and Square, going forward.
```

The speculative bet ("this call site only ever sees `Circle`") is exactly what let the compiler produce faster code than a fully general, defensive version would allow — deoptimization is the mechanism that makes betting on that assumption safe.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A method runs fast as speculatively-optimized compiled code while its assumption holds; the assumption breaks, triggering deoptimization back to the interpreter, followed by recompilation with a more general, correct assumption">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Fast: speculative compiled code</text>

  <rect x="240" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="330" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Assumption BREAKS</text>

  <rect x="460" y="20" width="160" height="40" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Deoptimize -&gt; interpreter</text>

  <rect x="240" y="100" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="125" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Recompile -- MORE GENERAL</text>

  <line x1="200" y1="40" x2="236" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a51)"/>
  <line x1="420" y1="40" x2="456" y2="40" stroke="#8b949e" stroke-width="2" marker-end="url(#a51)"/>
  <line x1="540" y1="60" x2="380" y2="98" stroke="#8b949e" stroke-width="2" marker-end="url(#a51)"/>

  <text x="330" y="160" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">The new compiled version correctly handles what was actually observed, going forward.</text>
  <defs><marker id="a51" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A broken assumption triggers a safe fallback to the interpreter and prompts recompilation with a corrected, more general assumption — never incorrect results, just a temporary performance dip.*

## 5. Runnable example

Scenario: deliberately triggering deoptimization by introducing a previously-unseen type at a long-monomorphic call site, growing from a baseline showing fast, speculatively-optimized performance, to introducing the type change and observing the resulting slowdown, to using deoptimization tracing flags to confirm the event directly.

### Level 1 — Basic

```java
public class MonomorphicBaseline {
    interface Shape { double area(); }
    static class Circle implements Shape {
        double r;
        Circle(double r) { this.r = r; }
        public double area() { return Math.PI * r * r; }
    }

    static double sumAreas(Shape[] shapes) {
        double total = 0;
        for (Shape s : shapes) total += s.area();
        return total;
    }

    public static void main(String[] args) {
        Shape[] shapes = new Shape[10_000];
        for (int i = 0; i < shapes.length; i++) shapes[i] = new Circle(i % 10 + 1);

        long start = System.nanoTime();
        double total = 0;
        for (int i = 0; i < 100_000; i++) total += sumAreas(shapes); // ONLY Circle, consistently, for a long time
        long elapsedMs = (System.nanoTime() - start) / 1_000_000;
        System.out.println("total=" + total + ", elapsed=" + elapsedMs + "ms (Circle-only, fully optimized)");
    }
}
```

**How to run:** `java MonomorphicBaseline.java` (JDK 17+).

Expected output shape (fast, reflecting well-optimized, speculatively-monomorphic compiled code):
```
total=..., elapsed=95ms (Circle-only, fully optimized)
```

With `sumAreas`'s call site seeing only `Circle` for the entire, substantial run, the JIT compiler can speculatively specialize its compiled code heavily around that single observed type, achieving strong performance.

### Level 2 — Intermediate

```java
public class IntroducingASurprise {
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
        for (Shape s : shapes) total += s.area();
        return total;
    }

    public static void main(String[] args) {
        Shape[] shapes = new Shape[10_000];
        for (int i = 0; i < shapes.length; i++) shapes[i] = new Circle(i % 10 + 1);

        long start1 = System.nanoTime();
        double total = 0;
        for (int i = 0; i < 100_000; i++) total += sumAreas(shapes); // long stretch of Circle-only
        long elapsed1 = (System.nanoTime() - start1) / 1_000_000;
        System.out.println("phase 1 (Circle-only): " + elapsed1 + "ms");

        shapes[5000] = new Square(3.0); // introduce a Square -- something the speculative version never saw

        long start2 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) total += sumAreas(shapes); // NOW mixed -- assumption breaks
        long elapsed2 = (System.nanoTime() - start2) / 1_000_000;
        System.out.println("phase 2 (Circle+Square, right after the surprise): " + elapsed2 + "ms (likely slower, at least initially)");
        System.out.println("total=" + total);
    }
}
```

**How to run:** `java IntroducingASurprise.java` (JDK 17+).

Expected output shape (phase 2 often shows at least a temporary slowdown, or is measurably slower than phase 1's fully-specialized speed, reflecting the deoptimization and subsequent recompilation cost):
```
phase 1 (Circle-only): 92ms
phase 2 (Circle+Square, right after the surprise): 118ms (likely slower, at least initially)
total=...
```

The real-world concern added: introducing a single `Square` into a previously all-`Circle` array, after `sumAreas` has already been running as speculatively-optimized, `Circle`-specialized compiled code — this breaks the compiler's earlier assumption, triggering deoptimization back to less-specialized execution and eventual recompilation with a more general (correctly handling both types) assumption, visible here as phase 2's comparatively slower measured time relative to phase 1's fully-specialized baseline.

### Level 3 — Advanced

```java
public class ObservingDeoptimizationDirectly {
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
        for (Shape s : shapes) total += s.area();
        return total;
    }

    public static void main(String[] args) {
        Shape[] shapes = new Shape[10_000];
        for (int i = 0; i < shapes.length; i++) shapes[i] = new Circle(i % 10 + 1);

        double total = 0;
        for (int i = 0; i < 100_000; i++) total += sumAreas(shapes);
        System.out.println("--- about to introduce a Square, watch for deoptimization events below ---");

        shapes[5000] = new Square(3.0);

        for (int i = 0; i < 100_000; i++) total += sumAreas(shapes);
        System.out.println("total=" + total);
    }
}
```

**How to run:** `java -XX:+UnlockDiagnosticVMOptions -XX:+PrintCompilation -XX:+TraceDeoptimization ObservingDeoptimizationDirectly.java 2>&1 | grep -A2 -B2 -i "deopt\|about to introduce"` (JDK 17+; diagnostic flags and their exact availability/output format can vary across JVM versions — adjust the grep pattern as needed to find deoptimization-related log lines around the point the `Square` is introduced).

Expected output shape (illustrative — actual log format is JVM-version-specific, but a deoptimization event tied to `sumAreas` should appear shortly after the marker message):
```
--- about to introduce a Square, watch for deoptimization events below ---
Uncommon trap ... reason='class_check' action='maybe_recompile' ... ObservingDeoptimizationDirectly::sumAreas
total=...
```

This adds the production-flavored hard case: using JVM diagnostic flags to directly observe a deoptimization event ("uncommon trap") tied specifically to `sumAreas`, occurring right around the point the previously-unseen `Square` is introduced — moving from indirectly inferring deoptimization occurred (via a measured slowdown, as in Level 2) to directly confirming it via the JVM's own diagnostic logging, which explicitly names the reason (a broken type-check assumption, `class_check`, in typical output) and the action taken (`maybe_recompile`, indicating the JVM will consider generating a corrected, more general compiled version going forward).

## 6. Walkthrough

Reasoning through the sequence of events in `ObservingDeoptimizationDirectly.main`:

1. During the first loop (100,000 calls to `sumAreas` over an all-`Circle` array), the JVM's tiered compilation pipeline compiles `sumAreas` — and, informed by profiling data showing only `Circle` ever appears at the `s.area()` call site, C2 speculatively inlines `Circle.area()`'s logic directly, guarded by a cheap type check confirming the assumption still holds on each call.
2. This speculative specialization is what makes the first loop run fast — but it comes with an implicit, JVM-tracked caveat: "this optimization is only valid as long as only `Circle` ever actually appears here."
3. `shapes[5000] = new Square(3.0);` mutates the array, introducing a type the speculative compiled code was never built to handle correctly.
4. On the very next call to `sumAreas` that reaches index 5000, the compiled code's guard (the cheap type check protecting the speculative inline) detects that the object at this position is *not* a `Circle` — this triggers an "uncommon trap," the JVM's internal mechanism for handling exactly this situation: it deoptimizes, meaning it abandons the currently-executing compiled frame, reconstructs the equivalent interpreter state (the loop's current index, `total`'s current value, and so on) from what the compiled code had, and resumes execution in the interpreter from that exact point — correctly handling the `Square` via ordinary (if temporarily slower) interpreted virtual dispatch.
5. Having observed this broken assumption, the JVM updates its understanding of this call site (now recognizing it as genuinely polymorphic, seeing both `Circle` and `Square`) and, if the method continues to be called frequently, eventually recompiles it — this time without the invalidated single-type assumption, instead using a strategy that correctly and efficiently handles both known types (commonly, a small inline cache checking for either type before falling back to general dispatch).
6. The measured slowdown in phase 2 (relative to phase 1) reflects this entire sequence: some calls immediately after the `Square` introduction running the fallback interpreted path (or a less-optimized recompiled version) while the JVM works out the new, corrected compiled version — after which, if the loop continued running much longer, performance would generally stabilize again at a new (correctly general, though perhaps not quite as fast as the original overly-specific speculative version) steady state.

## 7. Gotchas & takeaways

> **Gotcha:** a program that appears to "slow down mysteriously" partway through a long run, well after any expected warm-up period, is a strong candidate for having experienced a deoptimization event — some previously-unseen condition (a new type at a call site, a branch outcome the profile didn't anticipate) invalidated one of the JIT compiler's earlier speculative assumptions. This is a genuinely useful pattern to recognize when diagnosing performance regressions that don't correlate with any code change, but instead with a change in the actual *data* the running program encounters.

- Deoptimization is the safety mechanism that lets the JIT compiler take aggressive, profile-informed speculative bets (inlining based on an observed-but-not-guaranteed type, and more) by guaranteeing a safe, correct fallback to interpreted execution if any such bet ever turns out to be wrong.
- A broken assumption triggers an "uncommon trap": the compiled frame is abandoned, equivalent interpreter state is reconstructed from it, and execution resumes correctly (if temporarily more slowly) in the interpreter, followed by likely recompilation with a corrected, more general assumption.
- This explains a specific, sometimes-surprising performance pattern: a program running noticeably faster for a long stretch, then measurably (if often temporarily) slower once some previously-unseen data condition appears — without any change to the code itself.
- `-XX:+TraceDeoptimization` (alongside `-XX:+PrintCompilation`) makes deoptimization events directly observable in JVM diagnostic output, rather than something you can only infer indirectly from timing measurements.
- See [method inlining](0921-method-inlining.md) (whose polymorphic call-site challenges are exactly the kind of assumption deoptimization protects against) and [on-stack replacement](0923-on-stack-replacement-osr.md) (a related but distinct mechanism for transitioning execution between interpreted and compiled code, in the opposite direction — from interpreted to compiled, rather than compiled back to interpreted).
