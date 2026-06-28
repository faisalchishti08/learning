---
card: spring-boot
gi: 250
slug: known-limitations-of-native-images
title: Known limitations of native images
---

## 1. What it is

GraalVM native images offer fast startup and low memory, but they impose hard constraints compared to the JVM. These are not bugs — they follow directly from the **closed-world assumption**: everything the binary can do must be known at compile time.

The major limitations fall into five categories:

1. **No runtime bytecode generation** — no CGLIB, no ByteBuddy, no `Proxy.newProxyInstance` for interfaces not pre-registered.
2. **Reflection is limited** — only reflection registered via hints works; `Class.forName` on unregistered classes returns `null`.
3. **No dynamic class loading** — `URLClassLoader`, `ClassLoader.loadClass` on classes not in the image fail.
4. **Serialisation is hint-based** — Java serialisation requires explicit `serialization-config.json` entries.
5. **Build-time condition resolution** — `@ConditionalOn*` beans are locked at build time; runtime environment differences don't re-evaluate them.

## 2. Why & when

Understanding limitations matters when deciding *whether* to go native and *how* to adapt code that won't work. Not every Spring Boot application is a good native-image candidate today:

- Apps with many third-party libraries that haven't published GraalVM metadata may need extensive manual hint writing.
- Apps that load plugins or user-provided code at runtime (scripting engines, OSGi) cannot use native images.
- Apps that rely heavily on Groovy/Kotlin scripting, dynamic AOP pointcuts, or hot-reloading (DevTools) need to remain JVM-only.

Good candidates: REST APIs, microservices, CLI tools, event processors — stateless, limited reflection, well-known dependencies.

## 3. Core concept

The closed-world assumption is like **writing a book** vs. **having a conversation**. A JVM app is a conversation: you can ask questions (reflection) and receive answers at runtime. A native image is a printed book: everything must be written before printing; you cannot add pages at runtime.

Key limitation mechanics:

| Feature | JVM | Native image |
|---|---|---|
| CGLIB subclass proxies | Works (bytecode generated at runtime) | Fails (no runtime codegen) — Spring uses interface proxies or pre-generated proxy classes |
| `Class.forName("Foo")` | Works | Returns null unless `Foo` is in reflect-config.json |
| `new URLClassLoader(...)` | Works | Fails — classpath is sealed at build time |
| Lambda serialisation | Works | Needs serialization-config.json hint |
| `Proxy.newProxyInstance` | Works for any interface | Only works for interfaces in proxy-config.json |
| Dynamic AOP (CGLIB) | Works | Replaced by AOT-generated proxy classes |

Spring 6.x / Spring Boot 3.x has already addressed most framework-internal uses of these features; the remaining friction is in your code and third-party libraries.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JVM vs native image capability comparison showing what works and what doesn't">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Headers -->
  <text x="175" y="30" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM</text>
  <text x="490" y="30" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Native Image</text>

  <!-- Row items -->
  <text x="5" y="60" fill="#8b949e" font-size="10" font-family="sans-serif">CGLIB proxies</text>
  <rect x="140" y="46" width="70" height="22" rx="4" fill="#238636"/>
  <text x="175" y="62" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Works</text>
  <rect x="455" y="46" width="70" height="22" rx="4" fill="#8b1a1a"/>
  <text x="490" y="62" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Fails</text>

  <text x="5" y="95" fill="#8b949e" font-size="10" font-family="sans-serif">Class.forName</text>
  <rect x="140" y="81" width="70" height="22" rx="4" fill="#238636"/>
  <text x="175" y="97" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Works</text>
  <rect x="455" y="81" width="70" height="22" rx="4" fill="#9a6700"/>
  <text x="490" y="97" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Hint needed</text>

  <text x="5" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">URLClassLoader</text>
  <rect x="140" y="116" width="70" height="22" rx="4" fill="#238636"/>
  <text x="175" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Works</text>
  <rect x="455" y="116" width="70" height="22" rx="4" fill="#8b1a1a"/>
  <text x="490" y="132" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Fails</text>

  <text x="5" y="165" fill="#8b949e" font-size="10" font-family="sans-serif">Dynamic AOP</text>
  <rect x="140" y="151" width="70" height="22" rx="4" fill="#238636"/>
  <text x="175" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Works</text>
  <rect x="455" y="151" width="70" height="22" rx="4" fill="#9a6700"/>
  <text x="490" y="167" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Pre-generated</text>

  <text x="5" y="200" fill="#8b949e" font-size="10" font-family="sans-serif">@Conditional eval</text>
  <rect x="140" y="186" width="70" height="22" rx="4" fill="#238636"/>
  <text x="175" y="202" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Runtime</text>
  <rect x="455" y="186" width="70" height="22" rx="4" fill="#9a6700"/>
  <text x="490" y="202" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Build-time only</text>

  <!-- Legend -->
  <rect x="220" y="240" width="14" height="14" rx="2" fill="#238636"/>
  <text x="238" y="252" fill="#8b949e" font-size="9" font-family="sans-serif">Works</text>
  <rect x="290" y="240" width="14" height="14" rx="2" fill="#9a6700"/>
  <text x="308" y="252" fill="#8b949e" font-size="9" font-family="sans-serif">Works with hints / adaptation</text>
  <rect x="450" y="240" width="14" height="14" rx="2" fill="#8b1a1a"/>
  <text x="468" y="252" fill="#8b949e" font-size="9" font-family="sans-serif">Fails — no workaround</text>
</svg>

Red = hard limit; amber = works with hints or Spring's pre-generated proxies; green = no change needed.

## 5. Runnable example

```java
// NativeLimitationsDemo.java — run with: java NativeLimitationsDemo.java
// Walks through the key limitations with concrete code patterns
// and shows native-safe alternatives for each.

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class NativeLimitationsDemo {

    interface Greeter { String greet(String name); }

    public static void main(String[] args) throws Exception {
        System.out.println("=== Known Native Image Limitations & Safe Alternatives ===\n");

        limitation1_reflection();
        limitation2_dynamicProxy();
        limitation3_classLoading();
        limitation4_cglib();
    }

    // LIMITATION 1: Unregistered reflection
    static void limitation1_reflection() throws Exception {
        System.out.println("--- 1. Reflection ---");
        System.out.println("FAILS on native (class not in reflect-config.json):");
        System.out.println("  Class<?> c = Class.forName(\"com.plugin.DynamicLoader\");");
        System.out.println("  // => returns null in native image\n");

        // SAFE: register it in hints, or use direct reference
        System.out.println("SAFE: direct class reference (always reachable):");
        // Static reference — native-image traces this at build time
        Class<?> c = NativeLimitationsDemo.class;
        Method m = c.getDeclaredMethod("main", String[].class);
        System.out.println("  Reflected method (self-ref): " + m.getName() + "\n");
    }

    // LIMITATION 2: Dynamic JDK proxy for unregistered interface
    static void limitation2_dynamicProxy() {
        System.out.println("--- 2. Dynamic JDK Proxy ---");
        System.out.println("FAILS on native if Greeter not in proxy-config.json:");
        System.out.println("  Proxy.newProxyInstance(...)  // => IllegalArgumentException\n");

        // SAFE: pre-register via proxy-config.json OR use concrete class
        // In a Spring app: hints.proxies().registerJdkProxy(Greeter.class)
        // Here we show the safe concrete-class alternative:
        Greeter greeter = name -> "Hello, " + name + " (native-safe)";
        System.out.println("SAFE: lambda / concrete impl: " + greeter.greet("World") + "\n");
    }

    // LIMITATION 3: Dynamic class loading
    static void limitation3_classLoading() {
        System.out.println("--- 3. Dynamic Class Loading ---");
        System.out.println("FAILS on native:");
        System.out.println("  new URLClassLoader(new URL[]{pluginJar}).loadClass(\"Plugin\")");
        System.out.println("  // Classpath is sealed — no new classes can be loaded\n");
        System.out.println("ALTERNATIVES:");
        System.out.println("  - Use ServiceLoader (classes known at build time)");
        System.out.println("  - Keep plugin host on JVM, expose REST/gRPC interface");
        System.out.println("  - Sidecar pattern: native core + JVM plugin process\n");
    }

    // LIMITATION 4: CGLIB (affects Spring AOP, @Transactional on concrete classes)
    static void limitation4_cglib() {
        System.out.println("--- 4. CGLIB / Runtime Bytecode Generation ---");
        System.out.println("FAILS on native:");
        System.out.println("  @Transactional on a class without an interface => CGLIB subclass");
        System.out.println("  // native-image cannot generate bytecode at runtime\n");
        System.out.println("FIX: extract interface OR rely on Spring's AOT proxy generation");
        System.out.println("  Spring Boot 3.x generates CGLIB-equivalent proxy classes at");
        System.out.println("  AOT build time when it detects @Transactional on concrete beans.\n");
    }
}
```

**How to run:** `java NativeLimitationsDemo.java`

## 6. Walkthrough

- **Limitation 1 (reflection)** — `Class.forName("com.plugin.DynamicLoader")` fails silently in a native image if the class isn't in `reflect-config.json`. The safe alternative is a direct class literal (`DynamicLoader.class`) or a registered hint. The program demonstrates that self-referential reflection (`NativeLimitationsDemo.class`) always works because the class is obviously reachable.
- **Limitation 2 (dynamic proxy)** — `Proxy.newProxyInstance` only works for interfaces listed in `proxy-config.json`. The safe alternative: lambdas are compiled to static synthetic methods and are always reachable; an explicit interface implementation is also safe.
- **Limitation 3 (class loading)** — the classpath is frozen at build time. `URLClassLoader` with runtime JARs simply doesn't work. The sidecar pattern (native binary for core logic, separate JVM process for plugins) is the architectural workaround for plugin-based systems.
- **Limitation 4 (CGLIB)** — Spring Boot 3.x's AOT pipeline detects `@Transactional` on concrete classes and pre-generates the proxy class at build time (it appears in `target/spring-aot/main/sources/`). This is a Spring workaround, not a GraalVM feature; it means `@Transactional` works in native images as long as you use Spring's AOT phase.

## 7. Gotchas & takeaways

> **Fallback images are dangerous.** Without `--no-fallback`, if GraalVM can't build a true native image it silently produces a "fallback" that bundles the JVM — giving you none of the native benefits while hiding the real problem. Always pass `--no-fallback`.

> **Groovy, JRuby, Nashorn, and other dynamic language runtimes are incompatible with native images** — they generate bytecode at runtime. If your Spring Boot app embeds a scripting engine, keep it on the JVM or move scripting to a separate service.

- Check compatibility: `mvn -PnativeTest test` is the fastest definitive test before committing to native deployment.
- Spring Boot's compatibility page documents which auto-configurations are native-compatible; check it for each major dependency you add.
- Some limits are being lifted: GraalVM is evolving (Project Leyden will bring JVM-native closer together).
- Prefer interfaces over concrete classes for injected beans — helps both testability and native proxy generation.
- Use the GraalVM reachability metadata repository to skip writing hints for popular libraries (Jackson, Hibernate, etc.).
