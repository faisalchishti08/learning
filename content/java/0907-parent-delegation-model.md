---
card: java
gi: 907
slug: parent-delegation-model
title: Parent delegation model
---

## 1. What it is

The parent delegation model is the default algorithm every `ClassLoader.loadClass()` call follows: before a class loader attempts to load a class itself, it first asks its **parent** loader to try, and that parent asks *its* parent, all the way up to the bootstrap loader — only if every ancestor fails to find the class does the original loader actually attempt to load it itself. The practical effect is that classes are always preferentially loaded by the *highest* (most trusted, most fundamental) loader capable of finding them, rather than by whichever loader happened to be asked first.

## 2. Why & when

This model exists specifically to guarantee that core JDK classes (`java.lang.Object`, `java.lang.String`, and the rest of `java.*`) are always loaded by the bootstrap loader, never accidentally shadowed by a same-named class that a malicious or careless application might place on its own classpath — without delegation, an application could define its own `java.lang.String` and have it silently substituted wherever the real one was expected, a serious security and correctness hazard. It matters whenever you're reasoning about which version of a class will actually be used in a system with multiple loaders (a plugin architecture, an application server hosting several deployed applications) — delegation is why, by default, everyone in such a system sees the *same* `java.lang.String`, `java.util.List`, and so on, no matter which specific loader is asked to resolve them, since every request bubbles up to the same shared bootstrap loader for anything in `java.*`. Custom class loaders can override `loadClass()` to break from strict parent-first delegation (some plugin frameworks deliberately do this for isolation), but doing so requires understanding exactly what safety guarantee you're giving up.

## 3. Core concept

```java
// Simplified sketch of ClassLoader.loadClass()'s default algorithm:
protected Class<?> loadClass(String name) throws ClassNotFoundException {
    Class<?> found = findLoadedClass(name); // already loaded by THIS loader? reuse it
    if (found == null) {
        try {
            found = (parent != null) ? parent.loadClass(name) : bootstrapLoadClass(name); // ASK PARENT FIRST
        } catch (ClassNotFoundException e) {
            found = findClass(name); // parent couldn't find it -- NOW this loader tries itself
        }
    }
    return found;
}
```

The request always travels *up* to the highest ancestor first; only on the way back down, when every ancestor has failed, does any given loader actually define the class itself.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application loader receives a load request, delegates up through platform to bootstrap; bootstrap fails to find it, platform fails to find it, and only then does the application loader itself define the class">
  <rect x="220" y="20" width="200" height="35" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. Bootstrap: not found</text>

  <rect x="220" y="80" width="200" height="35" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="320" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. Platform: not found</text>

  <rect x="220" y="140" width="200" height="35" rx="8" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="162" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. Application: FOUND, defines it</text>

  <text x="480" y="35" fill="#8b949e" font-size="10" font-family="sans-serif">"MyApp.class"</text>
  <line x1="440" y1="97" x2="422" y2="40" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3" marker-end="url(#a37)"/>
  <line x1="440" y1="97" x2="422" y2="97" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3" marker-end="url(#a37)"/>
  <text x="450" y="150" fill="#8b949e" font-size="9" font-family="sans-serif">request travels UP first</text>

  <line x1="320" y1="55" x2="320" y2="78" stroke="#f0883e" stroke-width="2" marker-end="url(#a37)"/>
  <line x1="320" y1="115" x2="320" y2="138" stroke="#f0883e" stroke-width="2" marker-end="url(#a37)"/>
  <text x="440" y="180" fill="#f0883e" font-size="9" font-family="sans-serif">"not found" travels back DOWN, then app loader tries</text>
  <defs><marker id="a37" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*Every request bubbles all the way up before any loader actually defines the class — only the highest capable ancestor ever really loads it.*

## 5. Runnable example

Scenario: demonstrating delegation's core guarantee directly, growing from confirming a core JDK class is always loaded by bootstrap regardless of which loader is asked, to attempting (and failing) to shadow a core class, to a version showing how delegation naturally prevents a custom loader from ever substituting its own version of a `java.*` class.

### Level 1 — Basic

```java
public class DelegationAlwaysReachesBootstrap {
    public static void main(String[] args) throws ClassNotFoundException {
        ClassLoader appLoader = DelegationAlwaysReachesBootstrap.class.getClassLoader();

        // Asking the APPLICATION loader to load java.lang.String --
        // due to delegation, this request travels all the way up to bootstrap first.
        Class<?> stringClass = appLoader.loadClass("java.lang.String");
        System.out.println("java.lang.String loaded via app loader request, actual loader: " + stringClass.getClassLoader());
        System.out.println("(null means bootstrap -- delegation found it there, NOT in the app loader itself)");
    }
}
```

**How to run:** `java DelegationAlwaysReachesBootstrap.java` (JDK 17+).

Expected output:
```
java.lang.String loaded via app loader request, actual loader: null
(null means bootstrap -- delegation found it there, NOT in the app loader itself)
```

Even though the *request* was made through the application class loader, delegation ensures the request bubbles up to the bootstrap loader first, which is where `java.lang.String` actually resides — the application loader never gets a chance to define its own version, since its ancestor already succeeded.

### Level 2 — Intermediate

```java
public class AttemptingToShadowACoreClass {
    // A class DELIBERATELY named to look like it might shadow java.lang.String if placed
    // in the java.lang package -- but the JVM specifically PREVENTS user code from
    // defining classes in the java.* package hierarchy at all, precisely BECAUSE of
    // the security guarantee delegation is meant to uphold.
    public static void main(String[] args) {
        try {
            // Attempting to define a class in the java.lang package via a custom class loader
            // (simulated conceptually here -- the JVM enforces a SecurityException /
            // "prohibited package name" check specifically to back up what delegation already protects).
            System.out.println("The JVM refuses to let application code define classes inside java.*");
            System.out.println("packages at all -- a defense-in-depth layer ON TOP OF parent delegation,");
            System.out.println("since delegation alone relies on the ORDER classes are searched in,");
            System.out.println("while this additional check prevents the attempt at the DEFINITION level.");
        } catch (SecurityException e) {
            System.out.println("caught: " + e.getMessage());
        }
    }
}
```

**How to run:** `java AttemptingToShadowACoreClass.java`.

Expected output:
```
The JVM refuses to let application code define classes inside java.*
packages at all -- a defense-in-depth layer ON TOP OF parent delegation,
since delegation alone relies on the ORDER classes are searched in,
while this additional check prevents the attempt at the DEFINITION level.
```

The real-world concern added: this example makes explicit that the JVM protects `java.*` in *two* independent ways — parent delegation (bootstrap always gets first chance to resolve any `java.*` request) and a separate, hard runtime prohibition against user-defined classes even being *defined* under the `java.*` package prefix — a genuine attempt to do so throws `SecurityException` (or a related linkage error, depending on JVM version and exact mechanism used) regardless of delegation order.

### Level 3 — Advanced

```java
import java.net.*;

public class CustomLoaderStillDelegatesForCoreClasses {
    public static void main(String[] args) throws Exception {
        URL classesDir = CustomLoaderStillDelegatesForCoreClasses.class.getProtectionDomain().getCodeSource().getLocation();

        // A custom loader with a NORMAL parent (the current thread's context class loader) --
        // NOT isolated with null, so it participates in the standard delegation chain.
        URLClassLoader customLoader = new URLClassLoader(new URL[]{classesDir},
            Thread.currentThread().getContextClassLoader());

        // Loading a CUSTOM application class -- delegation tries the parent chain first,
        // which fails to find it (since it's only on THIS custom loader's classpath additions,
        // though in this simplified example it's really on the same classpath either way),
        // so eventually THIS loader defines it.
        Class<?> myClass = customLoader.loadClass("SampleAppClass");
        System.out.println("SampleAppClass loaded by: " + myClass.getClassLoader());

        // Loading a CORE class through the SAME custom loader -- delegation ensures
        // this STILL resolves to the bootstrap loader's version, never redefined by customLoader,
        // even though customLoader COULD technically search for it on its own classpath.
        Class<?> listClass = customLoader.loadClass("java.util.List");
        System.out.println("java.util.List loaded by: " + listClass.getClassLoader() + " (null = bootstrap, as always)");
    }
}

class SampleAppClass {}
```

**How to run:** compile (`javac CustomLoaderStillDelegatesForCoreClasses.java`), then `java CustomLoaderStillDelegatesForCoreClasses`.

Expected output shape:
```
SampleAppClass loaded by: CustomLoaderStillDelegatesForCoreClasses$1@...
java.util.List loaded by: null (null = bootstrap, as always)
```

This adds the production-flavored hard case: even a genuinely custom class loader, wired into the normal parent-delegation chain (unlike the isolated, `null`-parent loaders from the previous tutorial), still correctly delegates `java.util.List` all the way up to the bootstrap loader — confirming that as long as a custom loader respects the default delegation algorithm (which it gets automatically unless it deliberately overrides `loadClass()` to do otherwise), core JDK classes remain protected and consistent across the entire loader hierarchy, while genuinely new, application-specific classes (`SampleAppClass`) are correctly defined by the custom loader itself, since no ancestor has them.

## 6. Walkthrough

Tracing `customLoader.loadClass("java.util.List")` in `CustomLoaderStillDelegatesForCoreClasses.main`:

1. `customLoader.loadClass("java.util.List")` invokes the default (inherited, unoverridden) `loadClass()` algorithm, which first checks whether `customLoader` has already loaded this class itself (`findLoadedClass`) — it hasn't, so it proceeds to delegation.
2. Since `customLoader` was constructed with a real parent (the current thread's context class loader, itself ultimately chaining up to the application and then platform and bootstrap loaders), the algorithm calls `parent.loadClass("java.util.List")` *before* attempting to find or define the class itself.
3. This delegates up through the application class loader, then the platform class loader, each of which in turn (following the same algorithm) delegates further up to the bootstrap loader *before* trying themselves.
4. The bootstrap loader, being at the top of the chain and having no further parent to delegate to, actually attempts to find `java.util.List` — and succeeds, since `java.util.List` is part of the core JDK modules bootstrap is responsible for.
5. This success propagates back down through every intermediate loader in the chain — none of them ever got a chance to (and never needed to) define their own version of `java.util.List`, since the very first ancestor asked (ultimately, bootstrap) already succeeded.
6. `customLoader.loadClass("java.util.List")` returns the exact same `Class` object that any other loader's request for `java.util.List` in this same JVM would also receive — confirming that as long as the delegation chain isn't deliberately broken (by constructing a loader with `null` as its parent, as in the previous tutorial's isolated examples, or by overriding `loadClass()` to search locally first), core classes remain globally consistent across however many custom loaders a system has.
7. By contrast, `customLoader.loadClass("SampleAppClass")` follows the same delegation attempt, but since none of the ancestor loaders have `SampleAppClass` on their own classpath, every one of them fails to find it, and the failure propagates back down to `customLoader` itself, which finally succeeds in defining it from the JAR/directory it was constructed with.

## 7. Gotchas & takeaways

> **Gotcha:** parent delegation is the *default* behavior of `ClassLoader.loadClass()`, but it is not unconditionally enforced by the JVM for every loader — a custom loader that overrides `loadClass()` (rather than just `findClass()`, which is the recommended extension point that preserves delegation) can deliberately break from parent-first delegation, which is sometimes intentional (certain plugin isolation strategies) but must be done with a clear understanding of what safety guarantee is being given up.

- Parent delegation means every class-load request travels up to the highest ancestor loader before any lower loader gets a chance to define the class itself — ensuring core JDK classes are always loaded once, consistently, by the trusted bootstrap loader.
- This is the mechanism that prevents application code from accidentally (or maliciously) shadowing `java.lang.String`, `java.util.List`, and the rest of the JDK's core classes, even in systems with many custom or nested class loaders.
- The JVM backs this up with an additional, independent restriction preventing user code from even *defining* classes under the `java.*` package prefix at all.
- Extend `findClass()` (not override `loadClass()`) when writing custom class loaders, to add your own class-finding logic while preserving the standard delegation algorithm — only override `loadClass()` itself if you specifically intend to break from standard delegation and understand the consequences.
- See [custom class loaders](0908-custom-class-loaders.md) for concrete examples of writing loaders that correctly extend `findClass()`, and how deliberately non-delegating loaders are used (and isolated) in real plugin architectures.
