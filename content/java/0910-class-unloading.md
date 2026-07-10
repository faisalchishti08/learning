---
card: java
gi: 910
slug: class-unloading
title: Class unloading
---

## 1. What it is

Class unloading is the garbage collector reclaiming the memory used by a class (and its associated metadata, stored in the [method area / metaspace](0912-method-area-metaspace.md)) once that class is no longer reachable. The condition for this is stricter than for ordinary object garbage collection: a class can only be unloaded when its defining `ClassLoader` instance itself becomes unreachable — which in turn requires that no live object is an instance of that class, no `Class` object for it is still referenced anywhere (including via reflection), and the class loader instance itself isn't referenced by anything still alive. In practice, this means unloading is a **class-loader-granularity** operation: an entire loader and every class it defined are collected together, as a unit, never one class at a time from a loader that's still otherwise in use.

## 2. Why & when

Understanding class unloading matters directly for anything built around dynamic or custom class loading — plugin systems, hot-reloading tools, application servers hosting multiple deployed applications — since it explains exactly when the memory used by an "unloaded" plugin or a "redeployed" application actually gets reclaimed (and, just as importantly, when it *doesn't*, if some lingering reference accidentally keeps the whole loader alive). This is also the root cause of the historically notorious "classloader leak" problem in application servers: if *anything* — a thread that was started by application code and never stopped, a static reference held by a JDK-level singleton, a listener registered with a long-lived framework object and never unregistered — keeps a reference back to a class (or its loader) from a supposedly "undeployed" application, the entire loader, and every class and static field it holds, remains permanently unreclaimable, even though the application is logically gone. Recognizing this pattern — and understanding it takes an entire loader graph becoming unreachable, not just individual classes — is essential when diagnosing memory growth in long-running, dynamically-reloading systems.

## 3. Core concept

```java
ClassLoader loader = new URLClassLoader(urls, parent);
Class<?> pluginClass = loader.loadClass("PluginImpl");
Object instance = pluginClass.getDeclaredConstructor().newInstance();

// To make the loader (and PluginImpl) eligible for unloading, EVERYTHING referencing them
// must be dropped:
instance = null;      // drop the instance
pluginClass = null;    // drop the Class reference
loader = null;         // drop the loader reference itself
System.gc();           // request collection -- ONLY NOW can the loader and PluginImpl be reclaimed
```

Every one of these references must be released — an instance still alive, a `Class` object still referenced (even without any instances), or the loader variable itself still holding a reference all independently prevent unloading.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A class loader and the classes it defined can only be unloaded together as a unit, once no live instance, no referenced Class object, and no reference to the loader itself remain reachable from any GC root">
  <rect x="220" y="20" width="200" height="40" rx="8" fill="#1c2430" stroke="#f85149"/>
  <text x="320" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GC roots (still reachable?)</text>

  <rect x="60" y="90" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="135" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">any live instance?</text>
  <rect x="245" y="90" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">any Class ref held?</text>
  <rect x="430" y="90" width="150" height="35" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="505" y="112" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">loader itself referenced?</text>

  <line x1="320" y1="60" x2="135" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a40)"/>
  <line x1="320" y1="60" x2="320" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a40)"/>
  <line x1="320" y1="60" x2="505" y2="88" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a40)"/>

  <rect x="180" y="150" width="280" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="170" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ALL three answered "no" -&gt; loader + classes unloadable</text>
  <defs><marker id="a40" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Any single lingering reference — an instance, a `Class` object, or the loader itself — keeps the entire loader and every class it defined alive; all three conditions must clear together.*

## 5. Runnable example

Scenario: loading and attempting to unload a dynamically-loaded plugin class, growing from a version that fails to unload due to a lingering instance reference, to correctly clearing all references and confirming unloading via a `WeakReference` on the loader, to demonstrating the classic "leak via an external reference" pattern that prevents unloading in a realistic way.

### Level 1 — Basic

```java
import java.net.*;
import java.lang.ref.*;

public class LingeringInstancePreventsUnload {
    public static void main(String[] args) throws Exception {
        URL classesDir = LingeringInstancePreventsUnload.class.getProtectionDomain().getCodeSource().getLocation();
        URLClassLoader loader = new URLClassLoader(new URL[]{classesDir}, null);

        Class<?> pluginClass = loader.loadClass("UnloadablePlugin");
        Object instance = pluginClass.getDeclaredConstructor().newInstance(); // KEPT alive deliberately

        WeakReference<ClassLoader> loaderRef = new WeakReference<>(loader);
        loader = null; // drop the LOCAL variable, but `instance` still implicitly references its own Class/loader

        System.gc();
        Thread.sleep(200);

        System.out.println("loader still reachable? " + (loaderRef.get() != null));
        System.out.println("(true -- 'instance' is still alive, and every object implicitly keeps");
        System.out.println(" its own Class, and hence its defining loader, reachable)");

        System.out.println(instance); // keep `instance` alive until here, to make the point concrete
    }
}

class UnloadablePlugin {
    public String toString() { return "UnloadablePlugin instance"; }
}
```

**How to run:** compile all classes, then `java LingeringInstancePreventsUnload` (JDK 17+).

Expected output:
```
loader still reachable? true
(true -- 'instance' is still alive, and every object implicitly keeps
 its own Class, and hence its defining loader, reachable)
UnloadablePlugin instance
```

Even though the local `loader` variable was set to `null`, `instance` — an object whose class was defined by that loader — implicitly keeps its own `Class` object reachable (every object holds an internal reference to its class), and every `Class` object implicitly keeps its defining loader reachable — so the loader remains unreclaimable as long as `instance` is alive.

### Level 2 — Intermediate

```java
import java.net.*;
import java.lang.ref.*;

public class ProperlyClearingAllReferences {
    public static void main(String[] args) throws Exception {
        URL classesDir = ProperlyClearingAllReferences.class.getProtectionDomain().getCodeSource().getLocation();
        URLClassLoader loader = new URLClassLoader(new URL[]{classesDir}, null);

        Class<?> pluginClass = loader.loadClass("UnloadablePlugin2");
        Object instance = pluginClass.getDeclaredConstructor().newInstance();
        System.out.println("created: " + instance);

        WeakReference<ClassLoader> loaderRef = new WeakReference<>(loader);

        // Clear EVERY reference: the instance, the Class reference, AND the loader variable itself.
        instance = null;
        pluginClass = null;
        loader = null;

        System.gc();
        Thread.sleep(200);

        System.out.println("loader still reachable after clearing everything? " + (loaderRef.get() != null));
        System.out.println("(false, typically -- with NOTHING referencing the instance, the Class, or the");
        System.out.println(" loader itself, the whole loader graph becomes eligible for collection)");
    }
}

class UnloadablePlugin2 {
    public String toString() { return "UnloadablePlugin2 instance"; }
}
```

**How to run:** compile, then `java ProperlyClearingAllReferences`.

Expected output (`System.gc()` is best-effort, but reliably sufficient for this simple, small-heap demonstration):
```
created: UnloadablePlugin2 instance
loader still reachable after clearing everything? false
(false, typically -- with NOTHING referencing the instance, the Class, or the
 loader itself, the whole loader graph becomes eligible for collection)
```

The real-world concern added: this time, every single reference — the instance, the `Class` reference, and the loader variable itself — is explicitly cleared before requesting garbage collection, satisfying all three conditions simultaneously, so the loader (and `UnloadablePlugin2` along with it) genuinely becomes eligible for reclamation.

### Level 3 — Advanced

```java
import java.net.*;
import java.lang.ref.*;
import java.util.*;

public class ExternalReferenceLeakPattern {
    // Simulates a long-lived, "framework-level" registry that a plugin might carelessly
    // register a callback with -- and forget to unregister on shutdown.
    static List<Runnable> globalCallbackRegistry = new ArrayList<>();

    public static void main(String[] args) throws Exception {
        URL classesDir = ExternalReferenceLeakPattern.class.getProtectionDomain().getCodeSource().getLocation();
        URLClassLoader loader = new URLClassLoader(new URL[]{classesDir}, null);

        Class<?> pluginClass = loader.loadClass("LeakyPlugin");
        Object instance = pluginClass.getDeclaredConstructor().newInstance();

        // THE LEAK: registering a lambda/method reference tied to the plugin instance
        // into a registry that OUTLIVES the plugin's own intended lifecycle.
        Runnable callback = (Runnable) instance; // LeakyPlugin implements Runnable
        globalCallbackRegistry.add(callback); // <-- forgot to ever remove this on "unload"

        WeakReference<ClassLoader> loaderRef = new WeakReference<>(loader);

        // "Properly" clear everything WE directly hold...
        instance = null;
        pluginClass = null;
        loader = null;
        callback = null; // ...but the REGISTRY still holds its own reference!

        System.gc();
        Thread.sleep(200);

        System.out.println("loader still reachable, despite clearing our own references? " + (loaderRef.get() != null));
        System.out.println("(true -- globalCallbackRegistry, a completely unrelated long-lived object,");
        System.out.println(" still transitively references the plugin instance, its Class, and its loader --");
        System.out.println(" a classic classloader leak, caused by a forgotten unregister call)");

        // The fix: actually remove it from the registry before dropping our own references.
        globalCallbackRegistry.clear();
        System.gc();
        Thread.sleep(200);
        System.out.println("loader reachable after clearing the registry too? " + (loaderRef.get() != null));
    }
}

class LeakyPlugin implements Runnable {
    public void run() { System.out.println("LeakyPlugin running"); }
}
```

**How to run:** compile, then `java ExternalReferenceLeakPattern`.

Expected output:
```
loader still reachable, despite clearing our own references? true
(true -- globalCallbackRegistry, a completely unrelated long-lived object,
 still transitively references the plugin instance, its Class, and its loader --
 a classic classloader leak, caused by a forgotten unregister call)
loader reachable after clearing the registry too? false
```

This adds the production-flavored hard case: even after diligently clearing every *local* reference to the instance, its `Class`, and the loader, the plugin's loader remains alive because a completely separate, long-lived object (`globalCallbackRegistry`, standing in for a real framework-level registry, listener list, or thread) still transitively holds a reference to the plugin instance — this is exactly the mechanism behind real-world classloader leaks in application servers and plugin systems, and the fix requires finding and removing *every* such external reference, not just the ones in the code that did the loading.

## 6. Walkthrough

Tracing why the loader remains reachable in the first half of `ExternalReferenceLeakPattern.main`:

1. `globalCallbackRegistry.add(callback)` stores a reference to `instance` (cast to `Runnable`) inside `globalCallbackRegistry`, a static field on `ExternalReferenceLeakPattern` itself — a class loaded by the *application's own* class loader, entirely independent of `loader` (the plugin's loader).
2. Because `globalCallbackRegistry` is a `static` field, it's reachable directly from a GC root (the class `ExternalReferenceLeakPattern` itself, which is always reachable as long as the application's own classes are in use) — anything the list holds is transitively reachable too.
3. Even after `instance = null; pluginClass = null; loader = null; callback = null;` clear every *local variable* that once referenced the plugin, the list itself still holds its own independent reference to the same object — local variables and collection elements are simply different references to the same underlying object, and clearing one doesn't affect the other.
4. When the garbage collector traces reachability, it finds `ExternalReferenceLeakPattern.globalCallbackRegistry` → the `Runnable` (still `instance`, the `LeakyPlugin` object) → its `Class` (`LeakyPlugin`) → its defining `ClassLoader` (the plugin's `loader`) — a complete, unbroken chain from a GC root, meaning none of these objects (including the loader) can be collected.
5. `globalCallbackRegistry.clear()` finally removes the list's own reference to the plugin instance — with this last reference gone, and every other reference already cleared, the object, its `Class`, and its loader all become genuinely unreachable.
6. The second `System.gc()` call then successfully collects the entire loader graph, and `loaderRef.get()` correctly returns `null`, confirming the leak is resolved only once *every* reference — including ones held by unrelated, long-lived framework or registry objects — has been accounted for.

## 7. Gotchas & takeaways

> **Gotcha:** a plugin/application "unload" is only ever as complete as the *weakest* remaining reference somewhere in the entire JVM — a single forgotten unregister call, an un-stopped thread, or a static field on some completely unrelated, long-lived class can single-handedly prevent an otherwise-correctly-implemented unload from ever actually reclaiming memory, and this is notoriously hard to spot without heap-dump analysis tooling specifically designed to trace reference chains back to GC roots.

- Class unloading operates at the granularity of an entire class loader — a loader and every class it defined are reclaimed together, only once nothing anywhere in the JVM still references the loader, any of its classes, or any live instance of those classes.
- Every live object implicitly keeps its own `Class` reachable, and every `Class` implicitly keeps its defining loader reachable — a single lingering instance is enough to prevent the entire loader graph from being collected.
- The classic "classloader leak" in application servers and plugin systems comes from an external, long-lived object (a registry, a listener list, an un-stopped thread) retaining a reference into a supposedly-unloaded application or plugin.
- Diagnosing these leaks typically requires heap-dump analysis tooling that can trace the actual reference chain keeping a specific loader alive, since the leaking reference is often in code entirely unrelated to (and far away from) the loading/unloading logic itself.
- See [custom class loaders](0908-custom-class-loaders.md) for how loaders are constructed and used in the first place, and the [method area / metaspace](0912-method-area-metaspace.md) tutorial for where the actual memory being reclaimed by unloading lives.
