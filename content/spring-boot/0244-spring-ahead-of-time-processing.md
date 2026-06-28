---
card: spring-boot
gi: 244
slug: spring-ahead-of-time-processing
title: Spring Ahead-of-Time processing
---

## 1. What it is

**Ahead-of-Time (AOT) processing** is a compilation phase Spring performs *before* your application runs — typically at build time. It analyses the Spring application context, resolves beans, and generates plain Java source code (and resource hints) that replaces most of the reflection-heavy work Spring normally does at startup.

Without AOT, Spring uses reflection, classpath scanning, and dynamic proxy generation every time the JVM boots. With AOT, all that analysis is done once during the build; the generated code is compiled into bytecode, so the JVM can run it without runtime reflection.

Spring Boot 3.x introduced first-class AOT support (`spring-boot-starter-parent` exposes the `native` profile that drives it). The same AOT pipeline that produces native-ready artifacts also speeds up JVM launches.

## 2. Why & when

Use AOT when:

- You want to compile to a **GraalVM native image** (AOT is mandatory — native images forbid most runtime reflection).
- You want **faster JVM startup** and lower memory usage (generated code eliminates repeated classpath scanning).
- You need reproducible, statically-analysable application graphs for security reviews.

AOT has a cost: conditional beans (`@ConditionalOn*`) are evaluated once at build time instead of at runtime, so environment-specific conditions must be known before the build. That tradeoff is covered in the "Conditions & native limitations" tutorial.

## 3. Core concept

Think of a theatre rehearsal vs. a live performance. With **JIT** (just-in-time, the normal JVM mode), the cast improvises every night based on who shows up — powerful but slow to warm up. With **AOT**, you rehearse exhaustively beforehand; during the performance every actor knows their lines cold — startup is instant.

Spring's AOT pipeline has three steps:

1. **Context analysis** — `SpringApplicationAotProcessor` boots the application in a special "AOT mode", resolves the full bean graph, and inspects every `BeanDefinition`.
2. **Code generation** — For each bean, Spring generates a `BeanDefinitionRegistrar` class (plain Java, no reflection). Proxy classes are generated and compiled. Resource and reflection hints are written to `META-INF/native-image/`.
3. **Compilation** — Generated sources are compiled alongside your own code. The resulting jar (or native image) includes the generated registrars instead of the BeanFactory's runtime scanning logic.

Key artifacts produced:
- `target/spring-aot/main/sources/` — generated Java source files
- `target/spring-aot/main/resources/META-INF/native-image/` — reflection/resource/serialization config JSONs

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AOT processing pipeline from source to native or JVM artifact">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- boxes -->
  <rect x="10" y="90" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="75" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Your Source</text>
  <text x="75" y="127" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">+ Spring deps</text>

  <rect x="200" y="70" width="150" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="275" y="95" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">AOT Processor</text>
  <text x="275" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Resolves beans</text>
  <text x="275" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Generates code</text>
  <text x="275" y="145" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Writes hints</text>

  <rect x="420" y="50" width="130" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="70" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Generated Java</text>
  <text x="485" y="87" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Registrar classes</text>

  <rect x="420" y="120" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="485" y="140" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">native-image</text>
  <text x="485" y="157" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Hints JSONs</text>

  <rect x="570" y="85" width="100" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="620" y="105" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Native</text>
  <text x="620" y="122" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Binary</text>

  <!-- arrows -->
  <line x1="140" y1="115" x2="198" y2="115" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="350" y1="95" x2="418" y2="80" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="350" y1="135" x2="418" y2="145" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="550" y1="75" x2="568" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>
  <line x1="550" y1="145" x2="568" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#arr)"/>

  <text x="340" y="250" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Build time (Maven/Gradle AOT phase) → native binary runs without JVM reflection</text>
</svg>

AOT runs at build time; the resulting artifacts replace runtime reflection with precomputed Java code.

## 5. Runnable example

```java
// AotDemo.java  — run with: java AotDemo.java  (JDK 17+)
// Simulates what Spring AOT generates: a registrar that creates beans
// without reflection, using direct constructor calls instead.

import java.util.HashMap;
import java.util.Map;
import java.util.function.Supplier;

public class AotDemo {

    // Simulated bean registry (normally this is Spring's BeanFactory)
    static final Map<String, Supplier<Object>> REGISTRY = new HashMap<>();

    // ---- What AOT generates: plain code, zero reflection ----
    static {
        // Instead of: context.getBean("greetingService") using reflection,
        // AOT generates code like this for each bean:
        REGISTRY.put("greetingService", GreetingService::new);
        REGISTRY.put("appRunner", () -> new AppRunner(
            (GreetingService) REGISTRY.get("greetingService").get()
        ));
    }

    // Bean classes (in a real app these would be @Component/@Service)
    static class GreetingService {
        String greet(String name) { return "Hello, " + name + " (no reflection used)"; }
    }

    static class AppRunner {
        private final GreetingService svc;
        AppRunner(GreetingService svc) { this.svc = svc; }
        void run() { System.out.println(svc.greet("AOT World")); }
    }

    public static void main(String[] args) {
        System.out.println("=== AOT-style startup: wiring beans from generated registry ===");
        long start = System.nanoTime();

        // Resolve and run — no Class.forName, no getDeclaredConstructors
        AppRunner runner = (AppRunner) REGISTRY.get("appRunner").get();
        runner.run();

        long ms = (System.nanoTime() - start) / 1_000_000;
        System.out.println("Wired and ran in " + ms + " ms (no reflection overhead)");
    }
}
```

**How to run:** `java AotDemo.java`

## 6. Walkthrough

- **Static initialiser block** — represents the code Spring AOT *generates* for your application. It runs once at class-load time, wiring beans via direct constructor calls (`GreetingService::new`), not `Class.forName`.
- **`REGISTRY.put("greetingService", GreetingService::new)`** — the generated registrar stores a `Supplier<Object>`. In real AOT output this is a `BeanDefinitionRegistrar` class compiled into the jar.
- **`REGISTRY.get("appRunner").get()`** — dependency injection without reflection: `AppRunner` receives the already-constructed `GreetingService`. Spring's real AOT does exactly this — the generated code calls `new AppRunner(greetingService)` instead of using `AutowiredAnnotationBeanPostProcessor`.
- **Timing** — in a real Spring Boot app, AOT startup is 30–60 % faster than the equivalent reflection-based startup because the entire `BeanDefinitionReader` / classpath-scan / proxy-creation cycle is replaced by a single method call to the generated registrar.

## 7. Gotchas & takeaways

> **Conditions are locked at build time.** `@ConditionalOnProperty`, `@ConditionalOnMissingBean`, etc. are evaluated during the AOT phase. If a property only exists at runtime (e.g., injected by a secret manager), the condition may resolve incorrectly and the wrong bean set gets compiled in. Use environment variables set *before* the build, or design conditions that are deterministic at build time.

> **Generated sources are not for editing.** The `target/spring-aot/` directory is regenerated on every build. Put runtime hints in `@ImportRuntimeHints` classes or in `RuntimeHintsRegistrar` implementations, not by modifying generated files.

- AOT turns Spring's dynamic reflection-heavy wiring into static generated Java — required for GraalVM native images, beneficial for JVM startup too.
- Trigger it with `mvn spring-boot:process-aot` or `gradle processAot`, or automatically via the `native` profile.
- Inspect `target/spring-aot/main/sources/` to understand what Spring thinks your context looks like — mismatches reveal misconfigured beans.
- Libraries that use reflection internally need `RuntimeHintsRegistrar` registrations; Spring Boot ships these for its own auto-configurations already.
- AOT and JIT are not mutually exclusive for JVM mode: the AOT-compiled jar still JIT-compiles hot paths, it just starts without the reflection bootstrap cost.
