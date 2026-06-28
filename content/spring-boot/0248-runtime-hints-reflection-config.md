---
card: spring-boot
gi: 248
slug: runtime-hints-reflection-config
title: Runtime hints & reflection config
---

## 1. What it is

**Runtime hints** are metadata registered at build time to tell GraalVM's `native-image` about code that is used *dynamically* — through reflection, resource loading, serialisation, or JNI — that the static analyser cannot see on its own.

Spring provides two ways to supply hints:

1. **`RuntimeHintsRegistrar`** — a Java interface you implement and register via `@ImportRuntimeHints`. Spring's AOT phase calls it to collect hints programmatically.
2. **`META-INF/native-image/*.json` files** — raw GraalVM configuration files (`reflect-config.json`, `resource-config.json`, `serialization-config.json`, `proxy-config.json`, `jni-config.json`). Spring AOT generates these automatically for its own beans; you add your own when needed.

Without correct hints, code that works on the JVM silently fails in a native image: `Class.forName(...)` returns `null`, `getDeclaredMethods()` returns an empty array, or resources return `null` streams.

## 2. Why & when

GraalVM native images use a **closed-world assumption**: only code reachable from `main()` at build time is included. Reflection, resource loading, and dynamic proxies punch holes in this assumption — the analyser can't follow `Class.forName("com.example.Foo")` at build time.

You need runtime hints when:

- You use reflection (custom serialisers, `Class.forName`, `getDeclaredFields`).
- You load classpath resources with `ClassLoader.getResourceAsStream`.
- You use JDK dynamic proxies (`java.lang.reflect.Proxy`).
- You deserialise objects (Java serialisation or Kryo).
- A dependency does any of the above and hasn't shipped its own hints.

Spring Boot ships hints for its own auto-configurations; you write hints for your own dynamic code or for third-party libraries that haven't added native support yet.

## 3. Core concept

Think of runtime hints as a **shopping list** you hand the compiler before the store closes. The compiler (native-image) can only pack items on the list; anything you forgot is gone. Your job during AOT is to make that list complete.

The hint API surface:

| Hint type | API | JSON file |
|---|---|---|
| Reflection | `hints.reflection().registerType(Foo.class, ...)` | `reflect-config.json` |
| Resources | `hints.resources().registerPattern("templates/*.html")` | `resource-config.json` |
| Dynamic proxies | `hints.proxies().registerJdkProxy(Iface.class)` | `proxy-config.json` |
| Serialisation | `hints.serialization().registerType(Dto.class)` | `serialization-config.json` |
| JNI | `hints.jni().registerType(NativeClass.class)` | `jni-config.json` |

Hints are additive: Spring AOT generates a base set, your `RuntimeHintsRegistrar` adds more, and any JSON files in `META-INF/native-image/` merge in as well.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Runtime hints flow from registrar to native-image configuration files">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Sources of hints -->
  <rect x="10" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="55" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Boot AOT</text>

  <rect x="10" y="90" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="85" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Your RuntimeHints</text>
  <text x="85" y="128" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Registrar</text>

  <rect x="10" y="150" width="150" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="85" y="170" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Library hints</text>
  <text x="85" y="183" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GraalVM metadata repo</text>

  <!-- Merge box -->
  <rect x="210" y="90" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="280" y="110" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">AOT Processor</text>
  <text x="280" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">merges all hints</text>

  <!-- JSON files -->
  <rect x="400" y="50" width="140" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reflect-config.json</text>

  <rect x="400" y="92" width="140" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="112" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">resource-config.json</text>

  <rect x="400" y="134" width="140" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="470" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">proxy-config.json</text>

  <!-- native-image -->
  <rect x="590" y="90" width="100" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="640" y="110" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">native-image</text>
  <text x="640" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">uses all JSONs</text>

  <!-- arrows -->
  <line x1="160" y1="50" x2="208" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="160" y1="115" x2="208" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="160" y1="170" x2="208" y2="125" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="350" y1="100" x2="398" y2="70" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="350" y1="115" x2="398" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="350" y1="128" x2="398" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="540" y1="115" x2="588" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
</svg>

All hint sources merge during the AOT phase; the resulting JSON files feed `native-image` at compile time.

## 5. Runnable example

```java
// RuntimeHintsDemo.java — run with: java RuntimeHintsDemo.java
// Demonstrates writing a RuntimeHintsRegistrar and shows the equivalent
// JSON entries that Spring AOT produces in META-INF/native-image/.

import java.lang.reflect.Method;

public class RuntimeHintsDemo {

    // --- The class we need to access via reflection at runtime ---
    static class ReportGenerator {
        public String generate(String format) {
            return "Report in format: " + format;
        }
    }

    // --- Simulated hint registrar (real one implements RuntimeHintsRegistrar) ---
    // In a Spring app:
    //   @ImportRuntimeHints(MyHints.class)
    //   @SpringBootApplication
    //   public class App { ... }
    //
    //   class MyHints implements RuntimeHintsRegistrar {
    //     public void registerHints(RuntimeHints hints, ClassLoader cl) {
    //       hints.reflection()
    //            .registerType(ReportGenerator.class,
    //                MemberCategory.INVOKE_PUBLIC_METHODS);
    //       hints.resources()
    //            .registerPattern("reports/*.xml");
    //     }
    //   }

    // --- Equivalent reflect-config.json entry ---
    static final String REFLECT_JSON = """
        [
          {
            "name": "com.example.ReportGenerator",
            "methods": [
              { "name": "generate", "parameterTypes": ["java.lang.String"] }
            ]
          }
        ]
        """;

    // --- Equivalent resource-config.json entry ---
    static final String RESOURCE_JSON = """
        {
          "resources": {
            "includes": [
              { "pattern": "\\\\Qreports/\\\\E.*\\\\.xml" }
            ]
          }
        }
        """;

    public static void main(String[] args) throws Exception {
        System.out.println("=== RuntimeHints Demo ===\n");

        // Simulate what happens at native runtime after hints are correctly registered:
        // reflection access that would fail WITHOUT hints is available WITH them.
        Class<?> cls = Class.forName("RuntimeHintsDemo$ReportGenerator");
        Method m = cls.getDeclaredMethod("generate", String.class);
        Object instance = cls.getDeclaredConstructor().newInstance();
        String result = (String) m.invoke(instance, "PDF");
        System.out.println("Reflection call succeeded: " + result);

        System.out.println("\n--- reflect-config.json entry this class needs ---");
        System.out.println(REFLECT_JSON);

        System.out.println("--- resource-config.json for reports/*.xml ---");
        System.out.println(RESOURCE_JSON);

        System.out.println("--- Discovery: use the GraalVM agent to generate hints ---");
        System.out.println("  java -agentlib:native-image-agent=config-output-dir=src/main/resources/META-INF/native-image \\");
        System.out.println("       -jar myapp.jar");
        System.out.println("  # Exercise all code paths, then commit the generated JSON files.");
    }
}
```

**How to run:** `java RuntimeHintsDemo.java`

## 6. Walkthrough

- **`Class.forName(...)` + `getDeclaredMethod(...)` + `newInstance()`** — the three reflection operations most likely to fail in a native image without hints. Each must appear in `reflect-config.json` to survive native compilation.
- **`REFLECT_JSON`** — shows the exact JSON format. `"name"` is the fully qualified class name. `"methods"` lists method signatures. The `MemberCategory.INVOKE_PUBLIC_METHODS` enum in the Spring Hints API expands to all public method entries automatically.
- **`RESOURCE_JSON`** — resource patterns use regex. `\\Q...\\E` is regex "literal" quoting, so `\\Qreports/\\E.*\\.xml` matches `reports/anything.xml` without treating `/` specially.
- **GraalVM tracing agent** — the most practical way to discover missing hints: run the app with `-agentlib:native-image-agent=...`, exercise every feature (including test cases), and the agent writes complete JSON configs. Then copy them to `src/main/resources/META-INF/native-image/` and commit.
- **`@ImportRuntimeHints`** — Spring's annotation wires your `RuntimeHintsRegistrar` into the AOT phase. Spring calls `registerHints()` during `spring-boot:process-aot`, and the hints end up in the generated JSON files automatically.

## 7. Gotchas & takeaways

> **Missing hints fail silently on JVM, loudly on native.** A `NullPointerException` from `Class.forName` returning `null`, or a `MethodNotFoundException` you never saw on JVM, is almost always a missing reflection hint. Use `nativeTest` to catch these before production.

> **The GraalVM agent only records what it observes during that run.** If a code path is exercised only in production (e.g., an error handler, a rarely used API endpoint), the agent misses it. Supplement agent-generated hints with manual hints for critical paths.

- Check generated hints: `target/spring-aot/main/resources/META-INF/native-image/`.
- `MemberCategory` enum values: `INVOKE_PUBLIC_METHODS`, `DECLARED_FIELDS`, `INTROSPECT_DECLARED_CONSTRUCTORS` — pick the minimal set needed.
- Third-party hints ship via the GraalVM reachability metadata repo — add the `add-reachability-metadata` plugin goal to pull them automatically.
- Use `@Reflective` on your own classes (Spring 6.x) to register reflection hints without a registrar.
- Never delete Spring Boot's generated hint JSONs from `target/spring-aot/` — they're regenerated; if you need to override, write your own registrar or add JSON to `src/main/resources/META-INF/native-image/`.
