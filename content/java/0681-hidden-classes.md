---
card: java
gi: 681
slug: hidden-classes
title: Hidden classes
---

## 1. What it is

**Hidden classes** (JEP 371), delivered in **Java 15**, are classes that cannot be used directly by other classes' bytecode and are intended to be created and used dynamically at runtime — typically by frameworks that generate classes on the fly (bytecode-generating libraries, dynamic proxies, lambda implementations) rather than by application code loaded normally through the classpath. They're created via `Lookup.defineHiddenClass(...)` (a new method on `java.lang.invoke.MethodHandles.Lookup`), and unlike ordinary classes, a hidden class has no publicly discoverable name that other code can look up by name, is not registered in any classloader's list of named classes, and — crucially — can be **unloaded independently and much earlier** than a normal class, even while its defining classloader is still alive.

## 2. Why & when

Frameworks like those implementing dynamic proxies, lambda expressions (internally, `invokedynamic`-based lambdas), and various bytecode-manipulation libraries have long needed to generate throwaway classes at runtime — a class created just to serve one specific call site or one specific dynamically-constructed behavior, never meant to be looked up by name from anywhere else. Before hidden classes, the common workaround was `Unsafe::defineAnonymousClass`, an internal, unsupported API that happened to provide roughly the right semantics but was never meant for general use and carried the baggage of any `sun.misc.Unsafe` API — undocumented behavior, no compatibility guarantees, and eventual removal risk. Hidden classes exist to give framework authors a **proper, supported, standard API** with the same core benefit — the ability to generate, use, and discard classes rapidly, freeing metaspace sooner than normal classes would allow — without depending on internal JDK implementation details. You'd reach for hidden classes only if you're building a framework or library that dynamically generates bytecode at runtime (a proxy generator, an ORM building dynamic accessor classes, an OR-mapping or DI container); ordinary application code essentially never calls `defineHiddenClass` directly.

## 3. Core concept

```java
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodHandles.Lookup;

byte[] classBytes = /* ...compiled bytecode for some class, generated at runtime... */;

Lookup lookup = MethodHandles.lookup();
Class<?> hiddenClass = lookup
    .defineHiddenClass(classBytes, true /* initialize */)
    .lookupClass();

// hiddenClass has no discoverable name other code can look up:
// Class.forName("com.example.ThatClass") will NOT find it.
```

The resulting `Class` object works like any other for reflection and invocation *if you already hold a reference to it*, but no other code can find it by name — it simply isn't registered anywhere lookup-by-name would search.

## 4. Diagram

<svg viewBox="0 0 620 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An ordinary class is registered by name in a classloader and discoverable; a hidden class is defined but not registered by name, and can be unloaded independently">
  <rect x="20" y="30" width="260" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="150" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Ordinary class</text>
  <rect x="40" y="70" width="220" height="34" rx="5" fill="#161b22" stroke="#79c0ff"/>
  <text x="150" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">registered by name in ClassLoader</text>
  <text x="150" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Class.forName("com.example.Foo")</text>
  <text x="150" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">finds it — discoverable by name</text>

  <rect x="330" y="30" width="270" height="160" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="465" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Hidden class</text>
  <rect x="350" y="70" width="230" height="34" rx="5" fill="#161b22" stroke="#8b949e"/>
  <text x="465" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">defined, NOT registered by name</text>
  <text x="465" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">only usable via the Class reference</text>
  <text x="465" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">you already hold; unloads independently</text>
</svg>

Both are real, loaded classes at runtime — the difference is discoverability by name and independent unloading.

## 5. Runnable example

Scenario: a minimal dynamic-class factory — first generating and using one hidden class via reflection-visible bytecode, then generating several distinct hidden classes in a loop to show they don't collide despite sharing a "name," then showing hidden classes are unreachable via `Class.forName` even though instances of them work normally.

### Level 1 — Basic

```java
// File: HiddenClassBasic.java
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;

public class HiddenClassBasic {
    public static void main(String[] args) throws Throwable {
        // A tiny class, hand-assembled as bytecode-equivalent Java source
        // compiled ahead of time to bytes for this demo via the classfile
        // already produced by javac for a nested helper class.
        byte[] classBytes = HiddenClassBasic.class
                .getResourceAsStream("HiddenClassBasic$Greeter.class")
                .readAllBytes();

        MethodHandles.Lookup lookup = MethodHandles.lookup();
        Class<?> hiddenClass = lookup.defineHiddenClass(classBytes, true).lookupClass();

        Object instance = hiddenClass.getDeclaredConstructor().newInstance();
        Method greet = hiddenClass.getMethod("greet");
        System.out.println(greet.invoke(instance));
        System.out.println("Hidden class name: " + hiddenClass.getName());
    }

    // Compiled by javac into HiddenClassBasic$Greeter.class, then loaded
    // above as a hidden class purely to demonstrate the API.
    public static class Greeter {
        public String greet() { return "Hello from a hidden class!"; }
    }
}
```

**How to run:**
```
java HiddenClassBasic.java
```

Expected output (the exact hidden-class name suffix is JVM-generated and will vary):
```
Hello from a hidden class!
Hidden class name: HiddenClassBasic$Greeter/0x0000000800c01000
```

### Level 2 — Intermediate

```java
// File: HiddenClassMultiple.java
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;

public class HiddenClassMultiple {
    public static void main(String[] args) throws Throwable {
        byte[] classBytes = HiddenClassMultiple.class
                .getResourceAsStream("HiddenClassMultiple$Greeter.class")
                .readAllBytes();

        MethodHandles.Lookup lookup = MethodHandles.lookup();

        // Define the SAME class bytes as hidden classes multiple times —
        // each call produces a distinct, independent Class object.
        for (int i = 0; i < 3; i++) {
            Class<?> hiddenClass = lookup.defineHiddenClass(classBytes, true).lookupClass();
            Object instance = hiddenClass.getDeclaredConstructor().newInstance();
            Method greet = hiddenClass.getMethod("greet");
            System.out.println("Instance " + i + ": " + greet.invoke(instance)
                    + " [" + hiddenClass.getName() + "]");
        }
    }

    public static class Greeter {
        public String greet() { return "Hi!"; }
    }
}
```

**How to run:**
```
java HiddenClassMultiple.java
```

Expected output (each hidden class gets a distinct generated name suffix):
```
Instance 0: Hi! [HiddenClassMultiple$Greeter/0x0000000800c01000]
Instance 1: Hi! [HiddenClassMultiple$Greeter/0x0000000800c01800]
Instance 2: Hi! [HiddenClassMultiple$Greeter/0x0000000800c02000]
```

Each call to `defineHiddenClass` with the *same* class bytes produces a genuinely **distinct** `Class` object — unlike normal class loading (where loading the same named class twice from the same classloader would either fail or return the cached one), hidden classes are designed for exactly this repeated, throwaway-generation use case, which is what frameworks generating many one-off dynamic classes rely on.

### Level 3 — Advanced

```java
// File: HiddenClassUnreachable.java
import java.lang.invoke.MethodHandles;
import java.lang.reflect.Method;

public class HiddenClassUnreachable {
    public static void main(String[] args) throws Throwable {
        byte[] classBytes = HiddenClassUnreachable.class
                .getResourceAsStream("HiddenClassUnreachable$Greeter.class")
                .readAllBytes();

        MethodHandles.Lookup lookup = MethodHandles.lookup();
        Class<?> hiddenClass = lookup.defineHiddenClass(classBytes, true).lookupClass();

        // The hidden class works fine when you already have the Class reference:
        Object instance = hiddenClass.getDeclaredConstructor().newInstance();
        Method greet = hiddenClass.getMethod("greet");
        System.out.println("Direct use works: " + greet.invoke(instance));

        // Class.forName with the same binary name finds the ORDINARY compiled
        // Greeter class (loaded normally from the classpath) — a completely
        // different Class object from our hidden one, proving the hidden
        // class itself was never registered under that name.
        String binaryName = "HiddenClassUnreachable$Greeter";
        Class<?> foundByName = Class.forName(binaryName);
        System.out.println("Class.forName found: " + foundByName.getName());
        System.out.println("Hidden class object: " + hiddenClass.getName());
        System.out.println("Same Class object? " + (foundByName == hiddenClass));
        System.out.println("isHidden(): " + hiddenClass.isHidden());
    }

    public static class Greeter {
        public String greet() { return "Reachable only via the Class reference."; }
    }
}
```

**How to run:**
```
java HiddenClassUnreachable.java
```

Expected output (the hidden class's generated name suffix will vary):
```
Direct use works: Reachable only via the Class reference.
Class.forName found: HiddenClassUnreachable$Greeter
Hidden class object: HiddenClassUnreachable$Greeter/0x00000070001b9c00
Same Class object? false
isHidden(): true
```

Level 3 proves the defining characteristic empirically: `Class.forName` with the exact binary name resolves to the **ordinary**, normally-loaded `Greeter` class (registered in the classloader the usual way) — a completely different `Class` object from `hiddenClass`, as `Same Class object? false` confirms. The hidden class itself, despite being fully usable via the reference we already hold, was never registered under any name that `Class.forName` — or any other by-name lookup — could find. `Class.isHidden()` (added alongside this feature) lets code check this property directly.

## 6. Walkthrough

1. `main` reads the compiled bytecode for the nested `Greeter` class from the classpath via `getResourceAsStream(...).readAllBytes()` — in a real framework this byte array would instead come from an in-memory bytecode generator (e.g. ASM or a similar bytecode library), not a file; reading precompiled bytes here is a stand-in to keep the example self-contained and runnable with plain `javac`/`java`.
2. `MethodHandles.lookup()` obtains a `Lookup` object representing the current class's access rights — this is the caller-sensitive "who is asking" context the JVM uses to decide what the resulting hidden class is allowed to access.
3. `lookup.defineHiddenClass(classBytes, true)` defines a brand-new class from those bytes. The `true` argument requests immediate initialization (running static initializers right away, similar to `Class.forName(name, true, loader)`). The returned `Lookup` object (not the same as the input) has full access privileges to the newly hidden class; `.lookupClass()` extracts the actual `Class<?>` object.
4. `hiddenClass.getDeclaredConstructor().newInstance()` and `hiddenClass.getMethod("greet")` then use ordinary reflection to construct an instance and invoke a method — from this point on, a hidden class behaves exactly like any other loaded class *as long as you already have a reference to its `Class` object*.
5. The call `Class.forName("HiddenClassUnreachable$Greeter")` succeeds — but it resolves to the **ordinary** `Greeter` nested class, loaded the normal way from the classpath, not to `hiddenClass`. Comparing the two with `==` returns `false`, which is the crux of the feature: even though a class with that exact "name" was just defined via `defineHiddenClass` and is actively in use, no by-name lookup path in the JVM can ever return *that* hidden `Class` object, because hidden classes are intentionally excluded from a classloader's normal name-to-class registry.
6. `hiddenClass.isHidden()` returns `true`, confirming via the API (added by this JEP) that this particular `Class` object is indeed a hidden class rather than an ordinary one — useful for framework code or diagnostics that need to distinguish the two.
7. In Level 2, calling `defineHiddenClass` three times with identical `classBytes` produces three genuinely distinct `Class` objects (visible via their distinct generated names, each with a unique numeric suffix) — this is what makes hidden classes suitable for high-churn dynamic-class-generation scenarios: no naming collision, no need to invent artificially unique class names per generated class, and each one can be garbage-collected independently once nothing references it anymore.

```
compiled bytecode (byte[])
        │
        ▼
Lookup.defineHiddenClass(bytes, initialize)
        │
        ▼
Class<?> hiddenClass ── usable directly (reflection, invocation)
        │
        ▼
Class.forName(sameName) ──► returns the ORDINARY Greeter class (different object)
```

## 7. Gotchas & takeaways

> A hidden class's "name" (the string returned by `getName()`, like `HiddenClassBasic$Greeter/0x0000000800c01000`) includes a JVM-generated suffix and is **not** a name you can pass back into `Class.forName` or any other by-name lookup API — it's purely a human-readable label for debugging/toString purposes, not a real lookup key.

- Hidden classes exist primarily for **framework and library authors** generating bytecode dynamically — proxy generators, ORMs, DI containers, lambda-metafactory-style infrastructure — not for typical application code.
- They are the standard, supported replacement for the internal `sun.misc.Unsafe::defineAnonymousClass`, which frameworks had relied on for years despite it never being a public, guaranteed API.
- Because hidden classes aren't registered by name, they can be **garbage-collected independently and potentially much sooner** than ordinary classes defined by the same classloader — valuable when a framework generates large numbers of short-lived dynamic classes and doesn't want metaspace to grow unbounded.
- `Lookup.defineHiddenClass` requires you to already have appropriate `Lookup` access — you cannot define a hidden class into an arbitrary, unrelated class's access context from outside.
- `Class.isHidden()` is the supported way to check whether a given `Class` object is hidden; don't rely on parsing the generated name string to detect this.
