---
card: java
gi: 906
slug: classloader-hierarchy-bootstrap-platform-application
title: ClassLoader hierarchy (bootstrap/platform/application)
---

## 1. What it is

Every class in a running JVM is loaded by some specific `ClassLoader`, and by default these loaders form a hierarchy of three built-in levels. The **bootstrap class loader** (implemented in native code, not itself a Java object) loads the core of the JDK itself — `java.lang.Object`, `java.lang.String`, and the rest of the `java.*` platform modules. The **platform class loader** (formerly called the "extension" class loader before Java 9's module system) loads certain platform-provided modules that aren't part of the absolute core. The **application class loader** (also called the "system" class loader) loads your own application's classes — everything on the classpath or module path you specify when running `java`. Each loader (other than bootstrap) has a designated **parent**, forming a chain: application → platform → bootstrap.

## 2. Why & when

This hierarchy exists to establish a trust and consistency boundary: core JDK classes must always come from the trusted bootstrap loader, never accidentally shadowed by a same-named class an application happens to define, and the [parent delegation model](0907-parent-delegation-model.md) (covered in depth in the next tutorial) is the mechanism that enforces this by always asking a parent loader first before a child loader tries to load a class itself. Understanding which loader loaded a given class matters when debugging `ClassNotFoundException`/`NoClassDefFoundError` issues (is the class actually on the classpath the application loader searches?), when working with reflection or dynamic class loading (which loader should load a plugin class?), and when reasoning about class identity — the JVM considers two classes with the *same fully-qualified name* to be genuinely different types if they were loaded by different class loaders, a fact that explains certain surprising `ClassCastException`s in systems (like application servers or plugin frameworks) that use multiple custom loaders.

## 3. Core concept

```java
ClassLoader appLoader = MyClass.class.getClassLoader();       // typically the application class loader
ClassLoader platformLoader = appLoader.getParent();             // its parent: the platform class loader
ClassLoader bootstrapLoader = platformLoader.getParent();        // its parent: null -- bootstrap has no Java-visible parent

System.out.println(String.class.getClassLoader()); // null -- String is loaded by the bootstrap loader
System.out.println(MyClass.class.getClassLoader()); // e.g. jdk.internal.loader.ClassLoaders$AppClassLoader
```

`getClassLoader()` returning `null` specifically signals "loaded by the bootstrap loader" — since the bootstrap loader isn't itself represented as a normal Java `ClassLoader` object, there's no non-null reference to return.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Three-level class loader hierarchy: application class loader has platform class loader as parent, which has the bootstrap class loader as its parent">
  <rect x="220" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="45" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Bootstrap (native, core java.*)</text>

  <rect x="220" y="90" width="200" height="40" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Platform (some JDK modules)</text>

  <rect x="220" y="150" width="200" height="30" fill="none"/>

  <rect x="220" y="150" width="0" height="0"/>
  <rect x="220" y="150" width="200" height="30" rx="8" fill="none"/>

  <rect x="20" y="150" width="200" height="30" fill="none"/>
  <rect x="220" y="150" width="200" height="30" fill="none"/>

  <rect x="220" y="150" width="200" height="0" fill="none"/>

  <rect x="220" y="150" width="200" height="30" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="170" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Application (your classpath)</text>

  <line x1="320" y1="60" x2="320" y2="88" stroke="#8b949e" stroke-width="2" marker-end="url(#a36)"/>
  <line x1="320" y1="130" x2="320" y2="148" stroke="#8b949e" stroke-width="2" marker-end="url(#a36)"/>
  <text x="320" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">parent</text>
  <text x="320" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">parent</text>
  <defs><marker id="a36" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Application's parent is platform; platform's parent is bootstrap — arrows point from child to parent, the direction delegation requests travel.*

## 5. Runnable example

Scenario: inspecting which loader loaded various classes and walking the hierarchy, growing from a basic inspection, to demonstrating that identically-named classes loaded by different loaders are distinct types, to a version showing the hierarchy's role in a simple plugin-style scenario using a custom loader (introduced fully in [custom class loaders](0908-custom-class-loaders.md)).

### Level 1 — Basic

```java
public class InspectingTheHierarchy {
    public static void main(String[] args) {
        System.out.println("String's loader: " + String.class.getClassLoader() + " (null = bootstrap)");

        ClassLoader appLoader = InspectingTheHierarchy.class.getClassLoader();
        System.out.println("this class's loader: " + appLoader);

        ClassLoader current = appLoader;
        int level = 0;
        while (current != null) {
            System.out.println("  level " + level + ": " + current);
            current = current.getParent();
            level++;
        }
        System.out.println("  level " + level + ": null (bootstrap -- has no Java-visible parent)");
    }
}
```

**How to run:** `java InspectingTheHierarchy.java` (JDK 17+).

Expected output shape (exact loader class names are JDK-implementation-specific but the structure is stable):
```
String's loader: null (null = bootstrap)
this class's loader: jdk.internal.loader.ClassLoaders$AppClassLoader@...
  level 0: jdk.internal.loader.ClassLoaders$AppClassLoader@...
  level 1: jdk.internal.loader.ClassLoaders$PlatformClassLoader@...
  level 2: null (bootstrap -- has no Java-visible parent)
```

Walking `getParent()` repeatedly traces the full chain: this application class → the application class loader → the platform class loader → `null`, representing the bootstrap loader.

### Level 2 — Intermediate

```java
import java.net.*;

public class SameNameDifferentLoadersDistinctTypes {
    public static void main(String[] args) throws Exception {
        // Two SEPARATE URLClassLoaders, each pointed at the SAME directory of compiled classes --
        // loading the SAME class name through each produces two DISTINCT Class objects.
        URL classesDir = InspectingTheHierarchyHelperLocation.class.getProtectionDomain().getCodeSource().getLocation();

        URLClassLoader loaderA = new URLClassLoader(new URL[]{classesDir}, null); // null parent -- isolated
        URLClassLoader loaderB = new URLClassLoader(new URL[]{classesDir}, null); // a SEPARATE isolated loader

        Class<?> classFromA = loaderA.loadClass("HelperClass");
        Class<?> classFromB = loaderB.loadClass("HelperClass");

        System.out.println("same class NAME? " + classFromA.getName().equals(classFromB.getName()));
        System.out.println("same Class OBJECT (same type)? " + (classFromA == classFromB));
        System.out.println("classFromA's loader: " + classFromA.getClassLoader());
        System.out.println("classFromB's loader: " + classFromB.getClassLoader());
    }
}

class InspectingTheHierarchyHelperLocation {}

class HelperClass {
    public String identify() { return "I am HelperClass, loaded by " + getClass().getClassLoader(); }
}
```

**How to run:** compile all classes (`javac SameNameDifferentLoadersDistinctTypes.java`), then `java SameNameDifferentLoadersDistinctTypes` (JDK 17+).

Expected output shape (loader identity hash codes differ, confirming genuinely separate loader instances and thus separate types):
```
same class NAME? true
same Class OBJECT (same type)? false
classFromA's loader: HelperClass$1@1b6d3586
classFromB's loader: HelperClass$1@4554617c
```

The real-world concern added: loading the exact same bytecode (`HelperClass`) through two *different* `ClassLoader` instances produces two entirely distinct `Class` objects — even though they share the same fully-qualified name and identical bytecode, the JVM treats them as unrelated types; an instance created via `classFromA` cannot be cast to `classFromB`, and vice versa, which is exactly the mechanism (and occasional pitfall) behind class-loader isolation in plugin systems and application servers.

### Level 3 — Advanced

```java
import java.net.*;
import java.lang.reflect.*;

public class ClassCastAcrossLoaders {
    public static void main(String[] args) throws Exception {
        URL classesDir = ClassCastAcrossLoaders.class.getProtectionDomain().getCodeSource().getLocation();

        URLClassLoader pluginLoaderA = new URLClassLoader(new URL[]{classesDir}, null);
        URLClassLoader pluginLoaderB = new URLClassLoader(new URL[]{classesDir}, null);

        Class<?> pluginClassA = pluginLoaderA.loadClass("PluginImpl");
        Class<?> pluginClassB = pluginLoaderB.loadClass("PluginImpl");

        Object instanceA = pluginClassA.getDeclaredConstructor().newInstance();
        Object instanceB = pluginClassB.getDeclaredConstructor().newInstance();

        // Calling a method via REFLECTION works fine regardless of which loader created the instance --
        // reflection doesn't require static type compatibility.
        Method run = pluginClassA.getMethod("run");
        System.out.println("via reflection on instanceA: " + run.invoke(instanceA));

        Method runB = pluginClassB.getMethod("run");
        System.out.println("via reflection on instanceB: " + runB.invoke(instanceB));

        // But a DIRECT cast between the two loaders' versions of "the same" class fails --
        // this is exactly the ClassCastException that multi-loader systems must design around.
        try {
            @SuppressWarnings("unchecked")
            Object castAttempt = pluginClassB.cast(instanceA); // instanceA is a PluginImpl from LOADER A, not B
            System.out.println("unreachable");
        } catch (ClassCastException e) {
            System.out.println("ClassCastException across loaders: " + e.getMessage());
        }
    }
}

interface Plugin { String run(); }

class PluginImpl implements Plugin {
    public String run() { return "PluginImpl running, loaded by " + getClass().getClassLoader(); }
}
```

**How to run:** compile, then `java ClassCastAcrossLoaders`.

Expected output shape:
```
via reflection on instanceA: PluginImpl running, loaded by ...
via reflection on instanceB: PluginImpl running, loaded by ...
ClassCastException across loaders: class PluginImpl cannot be cast to class PluginImpl (PluginImpl is in unnamed module of loader ... @...; PluginImpl is in unnamed module of loader ... @...)
```

This adds the production-flavored hard case: a `ClassCastException` between two `Class` objects that print the *identical* fully-qualified name (`PluginImpl`) — the JVM's error message itself clarifies they're actually different classes because they came from different loader instances. This is the exact scenario that plugin architectures and application servers must design around: reflection-based invocation works across loader boundaries (since it doesn't require static type compatibility, only matching method signatures at the reflective level), but direct casts and `instanceof` checks against a type loaded by a *different* loader than the one performing the check will fail, even for what looks like "the same class."

## 6. Walkthrough

Tracing why `pluginClassB.cast(instanceA)` throws in `ClassCastAcrossLoaders.main`:

1. `pluginLoaderA.loadClass("PluginImpl")` and `pluginLoaderB.loadClass("PluginImpl")` each independently read the exact same `PluginImpl.class` bytecode from disk, but because each loader was constructed with `null` as its parent (deliberately isolating it from the normal delegation chain, and from each other), neither delegates the load to any shared parent — each loader defines its own, entirely separate `Class` object for `PluginImpl`.
2. `instanceA` is an object whose *actual runtime class* is "the `PluginImpl` defined by `pluginLoaderA`" — a distinct JVM-level type from "the `PluginImpl` defined by `pluginLoaderB`," despite having the same source code and the same printed name.
3. Reflective invocation (`run.invoke(instanceA)`) works because `Method.invoke` only needs the target object to actually have a method matching the reflected `Method` object's signature at the bytecode level — it doesn't perform a static, compile-time-style type check against a *specific* `Class` object's identity, so it succeeds regardless of which loader's version of `PluginImpl` is involved.
4. `pluginClassB.cast(instanceA)`, however, explicitly asks: "is `instanceA` an instance of *this specific* `Class` object (`pluginClassB`, the `PluginImpl` defined by loader B)?" Since `instanceA`'s actual runtime type is loader A's `PluginImpl`, not loader B's, the answer is no — even though both are named `PluginImpl` and have identical bytecode, the JVM's notion of type identity is tied to `(fully-qualified name, defining class loader)` as a pair, not the name alone.
5. This throws `ClassCastException`, and the JVM's own exception message goes out of its way to disambiguate the two same-named classes by describing their respective loaders — precisely because this exact "same name, different loader, different type" confusion is common enough that the JVM authors added that clarifying detail to the default error message.
6. This is exactly why systems that intentionally use multiple, isolated class loaders (OSGi, many application-server plugin systems, hot-reloading frameworks) must carefully design their public interfaces to be loaded by a *shared* ancestor loader (so all plugins agree on a common type for casting and `instanceof` purposes), while allowing plugin-specific implementation classes to be loaded by isolated, per-plugin loaders — which is exactly the `Plugin` interface's role in this example, versus `PluginImpl`'s isolated loading.

## 7. Gotchas & takeaways

> **Gotcha:** a `ClassCastException` (or a puzzling `instanceof` check that unexpectedly returns `false`) between two variables that both appear to hold "the same class" by name is a strong signal to check whether they were loaded by different class loaders — this is one of the most common and confusing categories of bugs in systems that use custom or multiple class loaders, precisely because the class names printed in stack traces and `toString()` output look identical.

- The default hierarchy is bootstrap (core `java.*`, native, `getClassLoader()` returns `null`) → platform (`getParent()` from application) → application (your classpath, the typical default loader for your own code).
- The JVM's notion of "the same class" is `(fully-qualified name, defining class loader)`, not just the name — two same-named classes loaded by different loaders are entirely distinct, incompatible types.
- Reflective method invocation works across loader boundaries since it doesn't require static type compatibility; direct casts and `instanceof` checks do require it and will fail across loaders even for identical bytecode.
- `getClassLoader()` returning `null` specifically indicates the bootstrap loader — it's not itself a normal `ClassLoader` object with a Java-visible parent chain.
- See [the parent delegation model](0907-parent-delegation-model.md) for the mechanism that normally keeps core JDK classes from ever being shadowed by application code, and [custom class loaders](0908-custom-class-loaders.md) for how and why real systems intentionally construct isolated loader hierarchies like the ones shown above.
