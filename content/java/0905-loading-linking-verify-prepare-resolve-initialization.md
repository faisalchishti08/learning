---
card: java
gi: 905
slug: loading-linking-verify-prepare-resolve-initialization
title: Loading, linking (verify/prepare/resolve), initialization
---

## 1. What it is

Before any class's code can run, the JVM takes it through three broad phases, each with its own well-defined sub-steps. **Loading** reads the class's bytecode (from a `.class` file, a JAR, or elsewhere) and constructs an in-memory representation of it. **Linking** has three parts: **verification** (checking the bytecode is structurally valid and doesn't violate the JVM's safety rules, so it never accidentally causes memory corruption or type confusion), **preparation** (allocating storage for the class's static fields and setting them to their default zero-equivalent values — `0`, `false`, `null` — not their programmer-specified initial values yet), and **resolution** (converting symbolic references in the bytecode, like `"java/lang/String"`, into actual, direct references to the real loaded classes and members, which the JVM is allowed to do lazily, the first time each reference is actually used). **Initialization** is the final phase: running the class's static initializer blocks and assigning the actual programmer-specified values to static fields, in source-code order — this is when the class becomes fully ready for real use.

## 2. Why & when

Understanding this pipeline matters because it explains several behaviors that otherwise look mysterious: why a static field can briefly be seen at its default value (`0`) before its real initializer runs (during a narrow window between preparation and initialization, in circular-initialization scenarios); why symbolic references can fail lazily, at first actual use, with a `NoClassDefFoundError` or similar, rather than immediately when a class is loaded (resolution is lazy); and why the exact moment a class "runs its static block" is a well-defined, specifiable event (initialization), not just "whenever the JVM feels like it" (see [class initialization triggers & order](0909-class-initialization-triggers-order.md) for exactly which actions trigger it). This pipeline is also the reason class loading failures show up as distinct exception types depending on which phase failed — a `ClassNotFoundException` (can't even locate the bytecode, during loading), a `VerifyError` (bytecode is structurally invalid, during linking), or an `ExceptionInInitializerError` (a static initializer itself threw, during initialization) — which is genuinely useful for diagnosing exactly where in the pipeline something went wrong.

## 3. Core concept

```java
class Config {
    static int maxRetries = computeDefault(); // ASSIGNED during INITIALIZATION, not preparation
    static { System.out.println("Config's static initializer running"); } // also part of initialization

    static int computeDefault() { return 5; }
}
// LOADING: JVM reads Config.class bytecode into memory
// LINKING - verify: bytecode is structurally valid
// LINKING - prepare: maxRetries allocated, temporarily = 0 (the int default), NOT 5 yet
// LINKING - resolve: symbolic refs (lazily, e.g. on first real use of another class from this bytecode)
// INITIALIZATION: static block runs, maxRetries actually becomes 5
```

Between preparation and initialization, `maxRetries` technically exists with the value `0` — a detail that matters specifically in circular class-initialization scenarios, covered concretely below.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The class lifecycle pipeline: loading reads bytecode, linking verifies prepares and resolves, initialization runs static blocks and assigns real static field values">
  <rect x="10" y="60" width="110" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="65" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Loading</text>

  <rect x="150" y="20" width="330" height="130" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="315" y="35" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Linking</text>
  <rect x="165" y="50" width="90" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="210" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Verify</text>
  <rect x="270" y="50" width="90" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="315" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Prepare</text>
  <rect x="375" y="50" width="90" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="420" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Resolve (lazy)</text>
  <text x="315" y="105" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">static fields = 0/null/false here</text>

  <rect x="520" y="60" width="110" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="575" y="90" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Initialization</text>

  <line x1="120" y1="85" x2="148" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a35)"/>
  <line x1="480" y1="85" x2="518" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a35)"/>
  <text x="575" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">real values assigned, static blocks run</text>
  <defs><marker id="a35" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Loading, linking (verify/prepare/resolve), and initialization run in this order for every class — resolution alone is allowed to happen lazily, on demand.*

## 5. Runnable example

Scenario: observing the class lifecycle directly through a static initializer, growing from a simple demonstration of when initialization fires, to exposing the default-value window between preparation and initialization via circular class references, to a version that deliberately triggers each of the distinct lifecycle-related error types.

### Level 1 — Basic

```java
public class BasicInitializationTiming {
    static class Config {
        static {
            System.out.println("Config class initializing NOW");
        }
        static int maxRetries = 5;
    }

    public static void main(String[] args) {
        System.out.println("main started -- Config has NOT been initialized yet");
        System.out.println("about to access Config.maxRetries...");
        int retries = Config.maxRetries; // THIS triggers Config's initialization
        System.out.println("Config.maxRetries = " + retries);
    }
}
```

**How to run:** `java BasicInitializationTiming.java` (JDK 17+).

Expected output:
```
main started -- Config has NOT been initialized yet
about to access Config.maxRetries...
Config class initializing NOW
Config.maxRetries = 5
```

`Config`'s static initializer runs precisely at the moment its static field is first genuinely accessed (`Config.maxRetries`), not when `BasicInitializationTiming` itself starts — loading and linking of `Config` may have already happened by then, but initialization is deferred until first real use.

### Level 2 — Intermediate

```java
public class CircularInitializationDefaultWindow {
    static class A {
        static int value = B.getValueFromA(); // triggers B's initialization DURING A's own initialization
        static int getValueFromB() { return 100; }
    }
    static class B {
        static int value = A.getValueFromB(); // A is still MID-initialization here -- sees A's DEFAULT value
        static int getValueFromA() { return 200; }
    }

    public static void main(String[] args) {
        System.out.println("A.value = " + A.value);
        System.out.println("B.value = " + B.value + " (expected 0 -- A.getValueFromB WAS available, but A.value itself");
        System.out.println("was still in its PREPARATION-phase default when B's initializer ran and read it indirectly)");
    }
}
```

**How to run:** `java CircularInitializationDefaultWindow.java`.

Expected output:
```
A.value = 200
B.value = 0 (expected 0 -- A.getValueFromB WAS available, but A.value itself
was still in its PREPARATION-phase default when B's initializer ran and read it indirectly)
```

The real-world concern added: `A`'s initialization triggers `B`'s initialization (via `B.getValueFromA()`), and `B`'s initializer, in turn, calls back into `A` (`A.getValueFromB()`) — but at that exact moment, `A` is still mid-initialization (its own `value` field assignment hasn't completed yet), so any attempt to read `A.value` directly during this window would see its preparation-phase default (`0`), not its true final value (`200`) — a subtle, well-defined consequence of the JVM's circular-initialization handling (each class initializes at most once, and re-entrant initialization requests during an in-progress initialization simply proceed without re-running it, seeing whatever state exists at that moment).

### Level 3 — Advanced

```java
public class LifecyclePhaseErrors {
    static class BadStaticInit {
        static int value = 10 / 0; // throws ArithmeticException DURING initialization
    }

    public static void main(String[] args) {
        // Demonstrates ExceptionInInitializerError: a failure specifically during the
        // INITIALIZATION phase (running static field initializers / static blocks).
        try {
            int v = BadStaticInit.value;
            System.out.println("unreachable: " + v);
        } catch (ExceptionInInitializerError e) {
            System.out.println("caught ExceptionInInitializerError, cause: " + e.getCause());
        }

        // Once a class's initialization has FAILED, the JVM marks it as erroneous --
        // ANY subsequent attempt to use it throws NoClassDefFoundError, WITHOUT re-attempting
        // initialization (initialization is guaranteed to be attempted AT MOST ONCE per class).
        try {
            int v2 = BadStaticInit.value; // second attempt -- does NOT re-run the static initializer
            System.out.println("unreachable: " + v2);
        } catch (NoClassDefFoundError e) {
            System.out.println("caught NoClassDefFoundError on second attempt: " + e.getMessage());
        }

        // A ClassNotFoundException, by contrast, happens during LOADING -- the bytecode
        // itself can't be located at all. Simulated here via reflection with a bogus name.
        try {
            Class.forName("com.example.DoesNotExist");
        } catch (ClassNotFoundException e) {
            System.out.println("caught ClassNotFoundException (a LOADING-phase failure): " + e.getMessage());
        }
    }
}
```

**How to run:** `java LifecyclePhaseErrors.java`.

Expected output:
```
caught ExceptionInInitializerError, cause: java.lang.ArithmeticException: / by zero
caught NoClassDefFoundError on second attempt: Could not initialize class LifecyclePhaseErrors$BadStaticInit
caught ClassNotFoundException (a LOADING-phase failure): com.example.DoesNotExist
```

This adds the production-flavored hard case: three distinct exception types, each corresponding to a failure in a *different* lifecycle phase — `ClassNotFoundException` from a failed **loading** attempt (the bytecode simply isn't found), `ExceptionInInitializerError` from a failure during the actual **initialization** phase (a static initializer threw), and `NoClassDefFoundError` on any *subsequent* attempt to use a class whose initialization has already failed once — since the JVM specification guarantees a class's initialization is attempted at most once, a prior failure permanently marks the class as unusable for the remainder of that JVM's run, without ever re-attempting the failed static block.

## 6. Walkthrough

Tracing `LifecyclePhaseErrors.main`'s first two `try` blocks:

1. `int v = BadStaticInit.value;` is the first genuine access to `BadStaticInit`, triggering its full lifecycle: loading (reading its bytecode), linking (verifying it, preparing `value` to its default `0`), and finally initialization — running the static field initializer `value = 10 / 0`.
2. That expression throws `ArithmeticException` during initialization. Per the JVM specification, any exception thrown during a class's static initialization (other than `Error` and its subclasses directly) is wrapped in an `ExceptionInInitializerError` and propagated to whoever triggered the initialization — here, that's `main`'s own attempted access.
3. `main`'s first `catch (ExceptionInInitializerError e)` block catches this and prints the wrapped cause, confirming the underlying `ArithmeticException`.
4. Crucially, `BadStaticInit`'s initialization is now permanently recorded by the JVM as having **failed** — the class enters an "erroneous" state.
5. The second `int v2 = BadStaticInit.value;` attempt does not get a fresh chance to re-run the static initializer (which might, in some hypothetical retry scenario, behave differently) — instead, because the class is already marked erroneous, the JVM immediately throws `NoClassDefFoundError` without attempting initialization again at all.
6. This is caught by the second `catch` block, confirming that a class's initialization failure is final and permanent for the remainder of that JVM process's lifetime — there is no way to "retry" a class's static initialization once it has failed.
7. The third block demonstrates a completely different lifecycle phase's failure: `Class.forName("com.example.DoesNotExist")` fails at the **loading** phase, since the JVM can't even locate bytecode for a class with that name — this produces the checked `ClassNotFoundException`, distinct in both timing and exception type from the two initialization-related failures above.

## 7. Gotchas & takeaways

> **Gotcha:** a class's static initialization is guaranteed to happen **at most once**, and a failed initialization permanently poisons the class for the remainder of the JVM's lifetime — every subsequent access throws `NoClassDefFoundError`, never re-attempting the static block, even if whatever caused the original failure (a missing config file, a transient resource) would no longer be a problem on a later attempt.

- Loading reads bytecode into memory; linking verifies it, prepares static fields to their default zero-equivalent values, and (lazily) resolves symbolic references; initialization runs static initializers and assigns real static field values, in source order.
- Between preparation and initialization, and during any circular initialization dependency, a static field can be observed at its default value even though its "real" initializer exists in the source — a subtle, specification-guaranteed behavior worth knowing when debugging surprising `0`/`null`/`false` values from classes with circular static dependencies.
- Distinct exception/error types map to distinct lifecycle phases: `ClassNotFoundException` (loading), `VerifyError` (linking/verification), `ExceptionInInitializerError` (initialization) — useful for diagnosing exactly where a class-loading-related failure actually occurred.
- A class's initialization is attempted at most once per JVM run; a failure permanently marks it erroneous, and all future access attempts fail fast with `NoClassDefFoundError` rather than retrying.
- See [class initialization triggers & order](0909-class-initialization-triggers-order.md) for the precise list of actions that actually trigger a class's initialization (as opposed to merely its loading or linking), which is a distinct and commonly-misunderstood question in its own right.
