---
card: java
gi: 909
slug: class-initialization-triggers-order
title: Class initialization triggers & order
---

## 1. What it is

The JVM Specification defines a precise, exhaustive list of actions that trigger a class's initialization (running its static initializers and assigning real values to static fields) — and, just as importantly, an equally precise list of actions that do *not*. The main triggers are: creating a new instance of the class (`new`), calling one of its static methods, reading or writing one of its static fields (with an important exception for `static final` compile-time constants), and reflectively loading it with `Class.forName(name)` using the default (`initialize = true`) overload. A class's superclass is always initialized before the class itself; interfaces the class implements are only initialized if they themselves declare default methods or static fields that need it — merely implementing an interface does not, by itself, trigger the interface's initialization.

## 2. Why & when

Precisely knowing what does and doesn't trigger initialization matters for two practical reasons: performance (avoiding accidentally forcing an expensive class to initialize earlier than actually necessary — for instance, via a needlessly-early `Class.forName` call) and correctness (understanding *why* a particular static block did or didn't run yet at a given point in a program, especially in code with static initializers that have observable side effects like logging, registering with a service, or opening a resource). A particularly common surprise is that referencing a `static final` field whose value is a **compile-time constant** (a `static final int`, `String`, or other primitive/String literal known at compile time) does *not* trigger the declaring class's initialization at all — the compiler simply inlines the constant's value directly into the calling code's bytecode, meaning the referenced class might never even be loaded if that's the only thing ever used from it. This is exactly the kind of detail worth knowing before you rely on a class's static block running "because some code references one of its fields."

## 3. Core concept

```java
class Loud {
    static { System.out.println("Loud initializing"); }
    static final int COMPILE_TIME_CONSTANT = 42; // inlined at COMPILE time -- does NOT trigger initialization
    static int runtimeComputed = computeSomething(); // requires REAL initialization to get a value
    static int computeSomething() { return 99; }
}

int a = Loud.COMPILE_TIME_CONSTANT; // "Loud initializing" does NOT print -- value 42 is inlined directly
int b = Loud.runtimeComputed;        // "Loud initializing" DOES print -- this genuinely requires initialization
```

The compiler can tell these two cases apart because `COMPILE_TIME_CONSTANT`'s value is fully determined at compile time (a literal), while `runtimeComputed`'s value depends on running actual code (`computeSomething()`), which can only happen through real initialization.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two ways of referencing a class's static field: referencing a compile-time constant is inlined by the compiler and does not trigger initialization, while referencing a field requiring runtime computation does trigger it">
  <rect x="20" y="20" width="270" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="155" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">int a = Loud.COMPILE_TIME_CONSTANT;</text>

  <rect x="20" y="80" width="270" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="155" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">compiler inlines: int a = 42;</text>
  <text x="155" y="130" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Loud is NEVER even loaded for this</text>

  <rect x="350" y="20" width="270" height="40" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="485" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">int b = Loud.runtimeComputed;</text>

  <rect x="350" y="80" width="270" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="485" y="102" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">requires real GETSTATIC bytecode</text>
  <text x="485" y="130" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Loud IS initialized to compute this</text>

  <line x1="155" y1="60" x2="155" y2="78" stroke="#8b949e" stroke-width="2" marker-end="url(#a39)"/>
  <line x1="485" y1="60" x2="485" y2="78" stroke="#8b949e" stroke-width="2" marker-end="url(#a39)"/>
  <defs><marker id="a39" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A compile-time constant is inlined and never requires touching the declaring class at all; anything requiring a real value lookup triggers genuine initialization.*

## 5. Runnable example

Scenario: observing exactly which actions trigger initialization, growing from confirming the compile-time-constant exception directly, to demonstrating that implementing an interface (without static fields) doesn't trigger the interface's initialization, to a comprehensive check of the full trigger list including reflection and subclass access to inherited static members.

### Level 1 — Basic

```java
public class CompileTimeConstantException {
    static class Loud {
        static { System.out.println("Loud's static block ran"); }
        static final int CONSTANT = 42;       // compile-time constant -- inlined, no initialization needed
        static int computed = computeIt();     // requires real initialization
        static int computeIt() { return 99; }
    }

    public static void main(String[] args) {
        System.out.println("about to read Loud.CONSTANT...");
        int a = Loud.CONSTANT; // does NOT print "Loud's static block ran"
        System.out.println("read CONSTANT = " + a + " -- notice no static block output above");

        System.out.println("about to read Loud.computed...");
        int b = Loud.computed; // THIS triggers initialization
        System.out.println("read computed = " + b);
    }
}
```

**How to run:** `java CompileTimeConstantException.java` (JDK 17+).

Expected output:
```
about to read Loud.CONSTANT...
read CONSTANT = 42 -- notice no static block output above
about to read Loud.computed...
Loud's static block ran
read computed = 99
```

`Loud`'s static block only runs when `Loud.computed` is accessed, confirming that referencing `Loud.CONSTANT` (a compile-time constant) genuinely does not trigger initialization — the value `42` is baked directly into the calling bytecode at compile time.

### Level 2 — Intermediate

```java
public class InterfaceInitializationNuance {
    interface PlainInterface {
        void doSomething(); // just an abstract method -- no static state, nothing to initialize
    }

    interface InterfaceWithStaticField {
        int VALUE = computeInterfaceValue(); // requires initialization of THIS interface
        static int computeInterfaceValue() {
            System.out.println("InterfaceWithStaticField initializing");
            return 7;
        }
    }

    static class Impl implements PlainInterface, InterfaceWithStaticField {
        public void doSomething() { System.out.println("Impl.doSomething running"); }
    }

    public static void main(String[] args) {
        System.out.println("creating an Impl instance...");
        Impl impl = new Impl(); // triggers Impl's initialization
        impl.doSomething();
        System.out.println("(notice: 'InterfaceWithStaticField initializing' did NOT print yet --");
        System.out.println(" merely IMPLEMENTING it doesn't trigger IT to initialize)");

        System.out.println("now explicitly reading InterfaceWithStaticField.VALUE...");
        int v = InterfaceWithStaticField.VALUE; // THIS triggers it
        System.out.println("VALUE = " + v);
    }
}
```

**How to run:** `java InterfaceInitializationNuance.java`.

Expected output:
```
creating an Impl instance...
Impl.doSomething running
(notice: 'InterfaceWithStaticField initializing' did NOT print yet --
 merely IMPLEMENTING it doesn't trigger IT to initialize)
now explicitly reading InterfaceWithStaticField.VALUE...
InterfaceWithStaticField initializing
VALUE = 7
```

The real-world concern added: `Impl` implementing `InterfaceWithStaticField` does **not** by itself trigger that interface's initialization when `Impl` is instantiated — an interface is only initialized when one of *its own* static fields (that requires real computation) is actually accessed directly, not merely by virtue of being implemented by some class that gets used.

### Level 3 — Advanced

```java
public class ComprehensiveTriggerCheck {
    static class Base {
        static { System.out.println("Base initializing"); }
        static int baseField = 1;
    }
    static class Derived extends Base {
        static { System.out.println("Derived initializing"); }
        static int derivedField = 2;
    }

    public static void main(String[] args) throws ClassNotFoundException {
        System.out.println("--- accessing Derived.derivedField directly ---");
        int d = Derived.derivedField; // triggers Base's init FIRST (superclass), THEN Derived's
        System.out.println("derivedField = " + d);

        System.out.println("--- Class.forName WITHOUT initialization (initialize=false) ---");
        Class.forName("ComprehensiveTriggerCheck$AnotherClass", false, ComprehensiveTriggerCheck.class.getClassLoader());
        System.out.println("(no static block output above -- loading/linking happened, but initialization did NOT)");

        System.out.println("--- Class.forName WITH initialization (the default) ---");
        Class.forName("ComprehensiveTriggerCheck$AnotherClass"); // default overload: initialize=true
    }

    static class AnotherClass {
        static { System.out.println("AnotherClass initializing"); }
    }
}
```

**How to run:** `java ComprehensiveTriggerCheck.java`.

Expected output:
```
--- accessing Derived.derivedField directly ---
Base initializing
Derived initializing
derivedField = 2
--- Class.forName WITHOUT initialization (initialize=false) ---
(no static block output above -- loading/linking happened, but initialization did NOT)
--- Class.forName WITH initialization (the default) ---
AnotherClass initializing
```

This adds the production-flavored hard case: confirming three distinct, precise trigger rules in one program — accessing `Derived.derivedField` initializes `Base` **first** (superclasses always initialize before their subclasses), the three-argument `Class.forName(name, false, loader)` overload explicitly loads and links a class *without* triggering initialization (useful when you specifically want to inspect a class's metadata via reflection without running its potentially expensive or side-effecting static block), while the single-argument `Class.forName(name)` convenience overload defaults to `initialize=true` and does trigger it.

## 6. Walkthrough

Tracing the first section of `ComprehensiveTriggerCheck.main`:

1. `int d = Derived.derivedField;` is a static field access that requires a real runtime value (not a compile-time constant, since `derivedField = 2` is a plain assignment, not declared `final` with a literal), so it triggers `Derived`'s initialization.
2. Per the JVM Specification, before any class is initialized, its **superclass** must be initialized first (unless the superclass is already initialized, or is `Object`, which needs no user-level initialization) — so before `Derived`'s own static block can run, `Base`'s initialization is triggered first.
3. `Base`'s static block runs, printing `"Base initializing"`, and `Base.baseField` is assigned its real value (`1`).
4. Only after `Base`'s initialization completes does `Derived`'s own initialization proceed: its static block runs, printing `"Derived initializing"`, and `Derived.derivedField` is assigned its real value (`2`).
5. The expression `Derived.derivedField` then evaluates to `2`, which is printed.
6. In the second section, `Class.forName("...AnotherClass", false, ...)` explicitly requests loading and linking (making the class's metadata available for reflection) *without* triggering initialization — this is precisely why no `"AnotherClass initializing"` message appears at this point, even though the class is now loaded and linked in memory.
7. In the third section, `Class.forName("...AnotherClass")` (the single-argument convenience overload) is called — this overload always initializes the class it loads, and since `AnotherClass` was already loaded and linked (but not yet initialized) from the previous call, this call completes that class's lifecycle by actually running its static block, producing the final `"AnotherClass initializing"` output.

## 7. Gotchas & takeaways

> **Gotcha:** referencing a `static final` field whose value is a compile-time constant does not trigger the declaring class's initialization *and* is inlined directly into the calling code at compile time — meaning if you later change that constant's value and recompile only the declaring class (without recompiling every class that references it), the classes that reference it will keep using the *old*, stale inlined value until they too are recompiled. This is a well-known, historically significant Java gotcha around compile-time constants and incremental compilation.

- Initialization triggers: creating an instance (`new`), invoking a static method, accessing a static field that requires real computation (not a compile-time constant), and `Class.forName` with `initialize=true` (the default single-argument overload).
- Referencing a `static final` compile-time constant (a literal-valued primitive or `String`) does **not** trigger initialization — the compiler inlines the value directly, and the declaring class may never even be loaded as a result.
- A superclass is always initialized before its subclass; an interface is only initialized when one of its own static fields requiring real computation is directly accessed, not merely by being implemented.
- `Class.forName(name, false, loader)` explicitly loads and links without initializing — useful for reflection-only inspection where running the class's static block would be wasteful or have unwanted side effects.
- See [loading, linking, initialization](0905-loading-linking-verify-prepare-resolve-initialization.md) for the broader lifecycle these triggers fit into, and [class unloading](0910-class-unloading.md) for what eventually reverses this process once a class is no longer needed.
