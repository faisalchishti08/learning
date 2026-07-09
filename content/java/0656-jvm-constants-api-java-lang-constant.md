---
card: java
gi: 656
slug: jvm-constants-api-java-lang-constant
title: JVM Constants API (java.lang.constant)
---

## 1. What it is

The **JVM Constants API**, added in **Java 12** (JEP 334) as the `java.lang.constant` package, gives programs a standard way to describe the "nominal" (symbolic, not-yet-resolved) form of loadable class-file constants — things like class references, method types, and method handles — without actually loading or resolving them. Its core types are `ClassDesc` (a symbolic description of a class, like `"java.lang.String"`), `MethodTypeDesc` (a symbolic method signature), and `MethodHandleDesc` (a symbolic method/field reference), all implementing the marker interface `ConstantDesc`. This is primarily a **tooling-and-bytecode-generation API** — it matters most to authors of bytecode generators, compilers, and libraries that manipulate class files (like ASM, or frameworks generating dynamic proxies), not to typical application code.

## 2. Why & when

Before this API, tools that generated or manipulated bytecode (compilers, bytecode libraries, `invokedynamic`-based frameworks) had no standard, JDK-provided way to represent "a reference to a class/method/field that hasn't been resolved yet" — each tool invented its own representation, or was forced to resolve things eagerly (actually loading classes) just to describe them symbolically. `java.lang.constant` gives a single, standard, serializable-friendly vocabulary for these symbolic references that the JDK itself now uses internally (for example, in the `invokedynamic`-based string concatenation machinery and record bootstrap methods added around the same era). You'd reach for this API directly only if you're writing a bytecode generator, an annotation processor that needs to describe class-file constants, or a framework building dynamic call sites — most application developers will never call these classes directly, but they benefit indirectly from more consistent tooling built on top of them.

## 3. Core concept

```java
import java.lang.constant.ClassDesc;
import java.lang.constant.MethodTypeDesc;

// A symbolic description of java.lang.String — no class loading happens here.
ClassDesc stringDesc = ClassDesc.of("java.lang", "String");

// A symbolic method signature: (int, String) -> boolean
MethodTypeDesc mtd = MethodTypeDesc.of(
    ClassDesc.of("boolean"),                 // not quite right for primitives, illustrative
    ClassDesc.of("int"), stringDesc
);

System.out.println(stringDesc.displayName()); // "String"
System.out.println(stringDesc.descriptorString()); // "Ljava/lang/String;"
```

`ClassDesc` and friends carry a class-file-level *descriptor string* (like `"Ljava/lang/String;"`) that a bytecode generator can emit directly into a `.class` file's constant pool — describing the reference symbolically, resolved lazily only when the generated code actually runs.

## 4. Diagram

<svg viewBox="0 0 620 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A symbolic ClassDesc describes java.lang.String without loading it; resolution to the actual Class happens later, only when needed">
  <rect x="10" y="20" width="270" height="140" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="145" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Symbolic (java.lang.constant)</text>
  <text x="25" y="70" fill="#e6edf3" font-size="10" font-family="monospace">ClassDesc.of(</text>
  <text x="25" y="85" fill="#e6edf3" font-size="10" font-family="monospace">  "java.lang", "String")</text>
  <text x="25" y="110" fill="#8b949e" font-size="9" font-family="sans-serif">Just a descriptor string:</text>
  <text x="25" y="125" fill="#8b949e" font-size="9" font-family="monospace">"Ljava/lang/String;"</text>
  <text x="25" y="145" fill="#8b949e" font-size="9" font-family="sans-serif">No class loading occurs.</text>

  <line x1="280" y1="90" x2="330" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#r1)"/>
  <text x="305" y="80" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">resolve</text>

  <rect x="340" y="20" width="270" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="475" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Resolved (java.lang.reflect)</text>
  <text x="355" y="70" fill="#e6edf3" font-size="10" font-family="monospace">classDesc.resolveConstantDesc(</text>
  <text x="355" y="85" fill="#e6edf3" font-size="10" font-family="monospace">  MethodHandles.lookup())</text>
  <text x="355" y="110" fill="#8b949e" font-size="9" font-family="sans-serif">→ actual java.lang.Class</text>
  <text x="355" y="125" fill="#8b949e" font-size="9" font-family="monospace">object for String.class</text>
  <text x="355" y="145" fill="#8b949e" font-size="9" font-family="sans-serif">Only NOW is String loaded.</text>

  <defs><marker id="r1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker></defs>
</svg>

A `ClassDesc` is a lightweight, purely symbolic description; only calling `resolveConstantDesc(...)` actually triggers class loading and resolution.

## 5. Runnable example

Scenario: describing a class and a method signature symbolically without loading anything, then resolving those descriptions into real reflective objects, then building a small "descriptor catalog" that records symbolic descriptions of several types and resolves them lazily only when actually requested — mirroring how a bytecode generator defers resolution.

### Level 1 — Basic

```java
// File: ConstDescBasic.java
import java.lang.constant.ClassDesc;

public class ConstDescBasic {
    public static void main(String[] args) {
        ClassDesc stringDesc = ClassDesc.of("java.lang", "String");
        ClassDesc listDesc = ClassDesc.of("java.util", "List");

        System.out.println("Display name: " + stringDesc.displayName());
        System.out.println("Descriptor:   " + stringDesc.descriptorString());
        System.out.println("Package:      " + stringDesc.packageName());

        System.out.println();
        System.out.println("Display name: " + listDesc.displayName());
        System.out.println("Descriptor:   " + listDesc.descriptorString());
    }
}
```

**How to run:** `java ConstDescBasic.java`

Expected output:
```
Display name: String
Descriptor:   Ljava/lang/String;
Package:      java.lang

Display name: List
Descriptor:   Ljava/util/List;
```

Note that at no point does this program actually load `java.lang.String` or `java.util.List` as classes for resolution purposes — it only manipulates their symbolic descriptions as strings.

### Level 2 — Intermediate

```java
// File: ConstDescResolve.java
import java.lang.constant.ClassDesc;
import java.lang.invoke.MethodHandles;

public class ConstDescResolve {
    public static void main(String[] args) throws ReflectiveOperationException {
        ClassDesc stringDesc = ClassDesc.of("java.lang", "String");
        ClassDesc mathDesc = ClassDesc.of("java.lang", "Math");

        System.out.println("Before resolving, we only have descriptors:");
        System.out.println("  " + stringDesc.descriptorString());
        System.out.println("  " + mathDesc.descriptorString());

        MethodHandles.Lookup lookup = MethodHandles.lookup();
        Class<?> resolvedString = (Class<?>) stringDesc.resolveConstantDesc(lookup);
        Class<?> resolvedMath = (Class<?>) mathDesc.resolveConstantDesc(lookup);

        System.out.println("\nAfter resolving, we have real Class objects:");
        System.out.println("  " + resolvedString + " (isInstance check: "
            + resolvedString.isInstance("hi") + ")");
        System.out.println("  " + resolvedMath);
    }
}
```

**How to run:** `java ConstDescResolve.java`

Expected output:
```
Before resolving, we only have descriptors:
  Ljava/lang/String;
  Ljava/lang/Math;

After resolving, we have real Class objects:
  class java.lang.String (isInstance check: true)
  class java.lang.Math
```

`resolveConstantDesc(lookup)` is the step that turns a purely symbolic `ClassDesc` into an actual `java.lang.Class` object — this is where real class loading/linking happens, deferred until this explicit call.

### Level 3 — Advanced

```java
// File: DescriptorCatalog.java
import java.lang.constant.ClassDesc;
import java.lang.invoke.MethodHandles;
import java.util.LinkedHashMap;
import java.util.Map;

public class DescriptorCatalog {
    // Holds symbolic descriptions; resolves lazily, only on demand, and caches the result.
    static class Catalog {
        private final Map<String, ClassDesc> descriptors = new LinkedHashMap<>();
        private final Map<String, Class<?>> resolvedCache = new LinkedHashMap<>();
        private final MethodHandles.Lookup lookup = MethodHandles.lookup();

        void register(String key, String packageName, String simpleName) {
            descriptors.put(key, ClassDesc.of(packageName, simpleName));
        }

        Class<?> resolve(String key) throws ReflectiveOperationException {
            if (resolvedCache.containsKey(key)) {
                System.out.println("  (cache hit for " + key + ")");
                return resolvedCache.get(key);
            }
            ClassDesc desc = descriptors.get(key);
            if (desc == null) {
                throw new IllegalArgumentException("Unknown key: " + key);
            }
            System.out.println("  (resolving " + desc.descriptorString() + " for the first time)");
            Class<?> resolved = (Class<?>) desc.resolveConstantDesc(lookup);
            resolvedCache.put(key, resolved);
            return resolved;
        }
    }

    public static void main(String[] args) throws ReflectiveOperationException {
        Catalog catalog = new Catalog();
        catalog.register("str", "java.lang", "String");
        catalog.register("list", "java.util", "ArrayList");

        System.out.println("Registered symbolically — nothing resolved yet.");

        System.out.println("Requesting 'str':");
        Class<?> c1 = catalog.resolve("str");
        System.out.println("  got " + c1.getSimpleName());

        System.out.println("Requesting 'str' again:");
        Class<?> c2 = catalog.resolve("str");
        System.out.println("  got " + c2.getSimpleName() + " (same object: " + (c1 == c2) + ")");

        System.out.println("Requesting 'list':");
        Class<?> c3 = catalog.resolve("list");
        System.out.println("  got " + c3.getSimpleName());
    }
}
```

**How to run:** `java DescriptorCatalog.java`

Expected output:
```
Registered symbolically — nothing resolved yet.
Requesting 'str':
  (resolving Ljava/lang/String; for the first time)
  got String
Requesting 'str' again:
  (cache hit for str)
  got String (same object: true)
Requesting 'list':
  (resolving Ljava/util/ArrayList; for the first time)
  got ArrayList
```

Level 3 mirrors how a real bytecode-generation tool would use `java.lang.constant`: register many symbolic descriptions cheaply upfront (no class loading cost), then resolve each one lazily only when actually needed, caching the result — deferred, on-demand resolution is exactly the design goal this API exists to support.

## 6. Walkthrough

1. `main` creates a `Catalog` and calls `register("str", "java.lang", "String")`, which internally calls `ClassDesc.of("java.lang", "String")` and stores the resulting symbolic `ClassDesc` in the `descriptors` map under the key `"str"`. No class loading happens here — `ClassDesc.of` just builds a descriptor string internally.
2. The same happens for `"list"` → `java.util.ArrayList`. After both `register` calls, `"Registered symbolically — nothing resolved yet."` prints — accurately, since neither `String` nor `ArrayList` has been touched as an actual `Class` object yet.
3. `catalog.resolve("str")` runs. `resolvedCache.containsKey("str")` is `false` (first request), so execution proceeds to look up the stored `ClassDesc` for `"str"`, print the "resolving for the first time" message, and call `desc.resolveConstantDesc(lookup)`.
4. `resolveConstantDesc` is where the actual work happens: it takes the symbolic descriptor `Ljava/lang/String;` and, using the supplied `MethodHandles.Lookup` for resolution context and access checking, loads/links the real `java.lang.String` class and returns its `Class<?>` object. This result is cast and stored in `resolvedCache` under `"str"` before being returned.
5. Back in `main`, `c1.getSimpleName()` prints `"String"`, confirming resolution succeeded.
6. `catalog.resolve("str")` is called a **second** time. Now `resolvedCache.containsKey("str")` is `true`, so the method takes the early-return branch, prints `"(cache hit for str)"`, and returns the cached `Class` object directly — no second resolution occurs.
7. `c1 == c2` evaluates `true` because `Class` objects for a given class in a given class loader are singletons, and here we're returning the exact same cached reference besides.
8. `catalog.resolve("list")` follows the same first-time path as step 3–5, resolving `java.util.ArrayList` symbolically-to-concretely for the first time and printing `"got ArrayList"`.

```
register("str", ...) ──► ClassDesc stored (symbolic, no loading)
resolve("str") 1st call ──► cache miss ──► resolveConstantDesc(lookup) ──► loads String.class ──► cached
resolve("str") 2nd call ──► cache hit ──► returns cached Class, no reload
```

## 7. Gotchas & takeaways

> `java.lang.constant` types describe **class-file-level** constants (the kind that live in a `.class` file's constant pool) — they are not a general-purpose "lazy class loading" utility for application code. Most application developers will never construct a `ClassDesc` directly; you'll encounter this API mainly if you're writing bytecode generators, working with `invokedynamic`-based frameworks, or reading JDK internals (like the `StringConcatFactory` bootstrap methods that use it).

- `ClassDesc`, `MethodTypeDesc`, and `MethodHandleDesc` are purely symbolic — building one never triggers class loading.
- Resolution (actually loading/linking a class, or looking up a method/field) happens only when you explicitly call `resolveConstantDesc(MethodHandles.Lookup)`.
- The `descriptorString()` format matches JVM class-file constant-pool descriptor syntax (`Ljava/lang/String;`, `I` for `int`, `(Ljava/lang/String;)Z` for a method signature), which is why this API is most relevant to bytecode-level tooling.
- Deferred, on-demand resolution (as in the Level 3 catalog) is the entire point — it lets tools describe large numbers of symbolic references cheaply and only pay the resolution cost for the ones actually used.
- This API works together with `Constable` (an interface some JDK types implement to describe themselves symbolically) and is part of the broader infrastructure for compile-time-constant folding and `invokedynamic` call-site bootstrapping in the JDK.
