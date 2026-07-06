---
card: java
gi: 256
slug: nested-class-compilation-class-files
title: Nested class compilation ($ class files)
---

## 1. What it is

Every nested class — static nested, inner, local, or anonymous — compiles down to its own separate `.class` file, named using the enclosing class's name, a dollar sign (`$`), and the nested class's name (or a number, for anonymous classes). The Java Virtual Machine has no built-in concept of "nesting" at all; nesting is purely a source-code and compiler-level construct that gets flattened into ordinary, independent class files joined only by naming convention and, for inner classes, a hidden reference field.

```java
class Car {
    static class EngineSpec { }        // compiles to: Car$EngineSpec.class
    class Wheel { }                     // compiles to: Car$Wheel.class
}

public class CompilationDemo {
    public static void main(String[] args) {
        // After compiling, `ls` in this directory would show:
        // CompilationDemo.class, Car.class, Car$EngineSpec.class, Car$Wheel.class
        System.out.println("Check the compiled .class files to see this in action");
    }
}
```

`Car.EngineSpec` and `Car.Wheel`, written together inside one source file, `Car.java`, compile into two *additional*, entirely separate class files: `Car$EngineSpec.class` and `Car$Wheel.class`, alongside `Car.class` itself — nesting exists in the source code you write, but the compiled bytecode treats each nested class as its own independent unit.

## 2. Why & when

Understanding this compilation detail matters mainly for reading compiled output, debugging, and understanding a few real, occasionally surprising consequences of how nesting is implemented.

- **Explains file listings and stack traces** — seeing a class named `Outer$Inner` in a directory listing, a stack trace, or a `getClass().getName()` call is not a bug or a strange naming scheme; it is exactly how the compiler represents nested classes at the bytecode level, and recognizing the `$` immediately tells you "this is a nested class."
- **Reveals why inner classes need a hidden reference** — since the JVM has no native concept of "this inner instance belongs to that outer instance," the compiler must generate a hidden synthetic field (commonly seen as `this$0` in decompiled bytecode) inside every non-static inner class's compiled form, holding the reference to its enclosing instance — this is the actual mechanism behind everything the inner-class topics described.
- **Explains anonymous class naming** — since anonymous classes have no name in the source, the compiler assigns them a number instead: the first anonymous class in `Car.java` becomes `Car$1.class`, the second becomes `Car$2.class`, and so on, in the order they appear in the source file.

You don't need to think about this compilation detail for everyday coding, but it becomes directly relevant when reading stack traces (`Outer$Inner` names), inspecting compiled artifacts, working with reflection or serialization (which can be sensitive to a nested class's exact compiled name and any hidden enclosing-instance reference), or debugging why an inner class instance is unexpectedly keeping its enclosing instance from being garbage collected.

## 3. Core concept

```java
class Building {
    class Room { } // non-static inner class
}

// Conceptually, after compilation, Room's bytecode behaves roughly like this equivalent,
// hand-written class (this is illustrative, not literal generated source):
class Building_Room_Equivalent {
    Building this$0; // hidden synthetic field: the enclosing Building instance
    Building_Room_Equivalent(Building outer) { this.this$0 = outer; }
}
```

The compiler-generated `this$0` field is exactly what makes `Outer.this` (covered in an earlier topic) work: writing `Building.this` inside `Room`'s source code compiles down to reading this hidden `this$0` field — the syntax you write is source-level sugar over a plain, ordinary field reference that exists in the compiled bytecode.

## 4. Diagram

<svg viewBox="0 0 600 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One source file with nested classes compiles into multiple separate dollar sign named class files, an inner class file additionally contains a hidden field referencing its enclosing instance">
  <rect x="8" y="8" width="584" height="174" rx="8" fill="#0d1117"/>

  <rect x="40" y="20" width="200" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">Car.java (one file)</text>

  <line x1="240" y1="40" x2="290" y2="40" stroke="#8b949e" stroke-width="1.5"/>
  <text x="265" y="30" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">compiles to</text>

  <rect x="300" y="20" width="140" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="370" y="40" fill="#6db33f" font-size="8" text-anchor="middle" font-family="monospace">Car.class</text>

  <rect x="300" y="60" width="140" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="80" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">Car$EngineSpec.class</text>

  <rect x="300" y="100" width="140" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="118" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="monospace">Car$Wheel.class</text>
  <text x="370" y="132" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">has hidden this$0 field</text>

  <text x="300" y="165" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Nesting is a source-level concept only — the JVM sees independent, separately named class files.</text>
</svg>

One source file with nested classes compiles into several independent `$`-named class files.

## 5. Runnable example

Scenario: a small program with a static nested class, an inner class, and an anonymous class, evolved so you can compile it and directly observe the resulting `.class` file names — grounding this topic in something you can verify yourself, not just read about.

### Level 1 — Basic

```java
public class CompilationBasic {
    static class Helper { // static nested class
        void assist() { System.out.println("Helping!"); }
    }

    public static void main(String[] args) {
        new Helper().assist();
    }
}
```

**How to run:** `java CompilationBasic.java` (or, to see the compiled files: `javac CompilationBasic.java && ls CompilationBasic*.class`)

After compiling with `javac`, running `ls` shows two files: `CompilationBasic.class` and `CompilationBasic$Helper.class` — one `.class` file for the top-level class, and a second, separate one for the nested `Helper` class, joined only by the shared `CompilationBasic$` prefix in the filename.

### Level 2 — Intermediate

Same program, now with a non-static inner class added alongside the static nested class, demonstrating that both kinds of nesting produce separate `$`-named files, but only the inner class's compiled form carries a hidden enclosing-instance reference.

```java
public class CompilationIntermediate {
    static class Helper { // static nested — no hidden enclosing reference
        void assist() { System.out.println("Static helper assisting"); }
    }

    class Assistant { // non-static inner — DOES have a hidden reference to the enclosing instance
        void assist() { System.out.println("Inner assistant for: " + CompilationIntermediate.this); }
    }

    public static void main(String[] args) {
        new Helper().assist();

        CompilationIntermediate outer = new CompilationIntermediate();
        CompilationIntermediate.Assistant inner = outer.new Assistant();
        inner.assist();
    }
}
```

**How to run:** `javac CompilationIntermediate.java && ls CompilationIntermediate*.class && java CompilationIntermediate`

Compiling produces `CompilationIntermediate.class`, `CompilationIntermediate$Helper.class`, and `CompilationIntermediate$Assistant.class` — three separate files; `Assistant`'s compiled form additionally contains the hidden `this$0` field (holding the enclosing `CompilationIntermediate` instance), which is exactly what lets `CompilationIntermediate.this` inside `Assistant.assist()` resolve correctly at runtime.

### Level 3 — Advanced

Same program, now adding an anonymous class, demonstrating the numeric naming convention (`Outer$1`, `Outer$2`, ...) the compiler uses when no name exists in the source to draw from.

```java
public class CompilationAdvanced {
    interface Task { void run(); }

    static class Helper { void assist() { System.out.println("Static helper"); } }
    class Assistant { void assist() { System.out.println("Inner assistant"); } }

    public static void main(String[] args) {
        new Helper().assist();

        CompilationAdvanced outer = new CompilationAdvanced();
        outer.new Assistant().assist();

        Task first = new Task() {              // this becomes CompilationAdvanced$1.class
            @Override public void run() { System.out.println("First anonymous task"); }
        };
        Task second = new Task() {              // this becomes CompilationAdvanced$2.class
            @Override public void run() { System.out.println("Second anonymous task"); }
        };

        first.run();
        second.run();
    }
}
```

**How to run:** `javac CompilationAdvanced.java && ls CompilationAdvanced*.class && java CompilationAdvanced`

Compiling produces five files: `CompilationAdvanced.class`, `CompilationAdvanced$Helper.class`, `CompilationAdvanced$Assistant.class`, `CompilationAdvanced$1.class` (the first anonymous `Task`), and `CompilationAdvanced$2.class` (the second) — the numbering is assigned strictly in the order the anonymous classes appear in the source file, which is why `first`'s anonymous class becomes `$1` and `second`'s becomes `$2`.

## 6. Walkthrough

Trace what happens when `CompilationAdvanced.java` is compiled and then run.

**Compilation (`javac CompilationAdvanced.java`).** The compiler processes the single source file and emits five separate `.class` files: `CompilationAdvanced.class` (the outer class itself, containing `main`), `CompilationAdvanced$Helper.class` (the static nested class — no hidden reference field, since it needs none), `CompilationAdvanced$Assistant.class` (the inner class — includes a hidden `this$0` field of type `CompilationAdvanced`), `CompilationAdvanced$1.class` (the first anonymous `Task` implementation), and `CompilationAdvanced$2.class` (the second). Running `ls CompilationAdvanced*.class` at this point would list exactly these five files.

**Running (`java CompilationAdvanced`).** The JVM loads `CompilationAdvanced.class` and executes `main`.

**`new Helper().assist()`.** The JVM loads `CompilationAdvanced$Helper.class` (if not already loaded), constructs an instance with no enclosing reference needed, and calls `assist()`, printing `"Static helper"`.

**`outer.new Assistant().assist()`.** `outer` is constructed first (a `CompilationAdvanced` instance). `outer.new Assistant()` loads `CompilationAdvanced$Assistant.class`, constructs an instance, and — behind the scenes — passes `outer` into the hidden `this$0` field during construction. Calling `assist()` prints `"Inner assistant"`.

**`new Task() { ... }` (first).** The JVM loads `CompilationAdvanced$1.class`, instantiates it, and assigns it to `first`.

**`new Task() { ... }` (second).** The JVM loads `CompilationAdvanced$2.class`, instantiates it, and assigns it to `second`.

**`first.run()` and `second.run()`.** Each dispatches to its respective anonymous class's `run()` method, printing `"First anonymous task"` and `"Second anonymous task"` respectively.

```
javac CompilationAdvanced.java produces:
  CompilationAdvanced.class          (outer class, has main)
  CompilationAdvanced$Helper.class   (static nested, no hidden field)
  CompilationAdvanced$Assistant.class (inner class, has this$0 field)
  CompilationAdvanced$1.class        (1st anonymous Task)
  CompilationAdvanced$2.class        (2nd anonymous Task)

java CompilationAdvanced runs main():
  Helper.assist()      -> "Static helper"
  Assistant.assist()   -> "Inner assistant"
  first.run()          -> "First anonymous task"
  second.run()         -> "Second anonymous task"
```

**Final output.**
```
Static helper
Inner assistant
First anonymous task
Second anonymous task
```

## 7. Gotchas & takeaways

> **A non-static inner class instance's hidden `this$0` reference can prevent its enclosing instance from being garbage collected, for as long as the inner instance itself remains reachable** — if you register a long-lived inner class instance (say, as an event listener with an external, long-running system) and forget about this hidden reference, you can accidentally keep a large enclosing object alive far longer than intended, a subtle and real source of memory leaks in Java code that uses inner classes freely.

> **Anonymous class numbering (`Outer$1`, `Outer$2`, ...) is based purely on source order within the file, not on runtime execution order** — if the source code declared the anonymous classes in a different order than they execute, the numbers would still reflect the *source* order, since the compiler assigns them at compile time, before the program ever runs.

- Every nested class — static, inner, local, or anonymous — compiles into its own separate `.class` file, named `Outer$Name` (or `Outer$N` for anonymous classes, numbered by source order).
- The JVM has no built-in concept of nesting; it is purely a compiler-level and source-level construct, flattened into ordinary, independently loaded classes.
- Non-static inner classes carry a hidden, compiler-generated reference field (commonly seen as `this$0` in decompiled bytecode) to their enclosing instance; static nested classes do not.
- This hidden reference is what makes `Outer.this` work at the source level, but it can also unintentionally keep an enclosing instance alive longer than expected if an inner instance outlives it in some external, long-running context.
