---
card: spring-framework
gi: 178
slug: runtime-hints-reflection-resources-serialization-proxies
title: "Runtime hints (reflection, resources, serialization, proxies)"
---

## 1. What it is

A **runtime hint** is metadata that tells the GraalVM `native-image` tool "this class / method / resource / interface will be needed at runtime even though static analysis cannot see the usage." Without a hint the native binary omits the element; accessing it at runtime throws `ClassNotFoundException`, `NoSuchMethodException`, or a proxy-generation failure.

Spring's `RuntimeHints` API (package `org.springframework.aot.hint`) is the central place to register all four categories:

```java
RuntimeHints hints = new RuntimeHints();

hints.reflection()    // reflective class/method/field access
hints.resources()     // classpath resource files
hints.serialization() // Java serialization (ObjectOutputStream)
hints.proxies()       // JDK dynamic proxy interface lists
```

## 2. Why & when

- **Reflection hints** — any code that calls `Class.forName()`, `getDeclaredMethod()`, `newInstance()`, or uses frameworks that do (Jackson, Hibernate, Spring Data) needs reflection hints for the types involved.
- **Resource hints** — files loaded with `ClassLoader.getResourceAsStream()` or `@PropertySource` must be listed; `native-image` only includes resources explicitly declared.
- **Serialization hints** — any class passed through `ObjectOutputStream` / `ObjectInputStream` needs a serialization hint; Java serialization uses reflection internally.
- **Proxy hints** — `Proxy.newProxyInstance(loader, new Class[]{MyInterface.class}, handler)` needs a proxy hint registering the interface list; native image pre-generates the proxy class.

You do NOT need hints for:
- Classes visible via direct method calls in reachable code (static analysis covers them).
- Spring `@Component` / `@Service` beans — Spring AOT generates their hints automatically.
- `@Value` injection of `String`/`int`/standard types.

## 3. Core concept

The `RuntimeHints` object is a collector. Hints registered into it are serialised to `reflect-config.json`, `resource-config.json`, `serialization-config.json`, and `proxy-config.json` under `META-INF/native-image/` during the AOT build step.

| Hint type | API | Config file produced |
|---|---|---|
| Reflection | `hints.reflection().registerType(T.class, …)` | `reflect-config.json` |
| Resources | `hints.resources().registerPattern("path/**")` | `resource-config.json` |
| Serialization | `hints.serialization().registerType(T.class)` | `serialization-config.json` |
| JDK proxy | `hints.proxies().registerJdkProxy(If1.class, If2.class)` | `proxy-config.json` |

`MemberCategory` controls what is registered for reflection:

| `MemberCategory` | What it enables |
|---|---|
| `INVOKE_PUBLIC_CONSTRUCTORS` | `Constructor.newInstance()` on public constructors |
| `INVOKE_DECLARED_CONSTRUCTORS` | same for private/package constructors |
| `INVOKE_PUBLIC_METHODS` | calling public instance/static methods |
| `INVOKE_DECLARED_METHODS` | calling private/package methods |
| `PUBLIC_FIELDS` | reading/writing public fields |
| `DECLARED_FIELDS` | reading/writing private/package fields |

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ra178" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- RuntimeHints central box -->
  <rect x="260" y="80" width="180" height="50" rx="6" fill="#6db33f" opacity="0.25" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="100" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">RuntimeHints</text>
  <text x="350" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">central hint collector</text>

  <!-- Input sources (left) -->
  <rect x="10" y="10" width="200" height="22" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="110" y="25" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">RuntimeHintsRegistrar (manual)</text>
  <line x1="212" y1="21" x2="258" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <rect x="10" y="40" width="200" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="110" y="55" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Spring AOT processors (auto)</text>
  <line x1="212" y1="51" x2="258" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <rect x="10" y="70" width="200" height="22" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@RegisterReflectionForBinding</text>
  <line x1="212" y1="81" x2="258" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <!-- Output files (right) -->
  <rect x="490" y="5"  width="200" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="590" y="20" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">reflect-config.json</text>
  <line x1="442" y1="92" x2="488" y2="16" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <rect x="490" y="35" width="200" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="590" y="50" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">resource-config.json</text>
  <line x1="442" y1="97" x2="488" y2="46" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <rect x="490" y="65" width="200" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="590" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">serialization-config.json</text>
  <line x1="442" y1="102" x2="488" y2="76" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <rect x="490" y="95" width="200" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="590" y="110" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">proxy-config.json</text>
  <line x1="442" y1="107" x2="488" y2="106" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ra178)" opacity="0.7"/>

  <!-- native-image at bottom -->
  <rect x="250" y="160" width="200" height="30" rx="6" fill="#6db33f" opacity="0.35" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="179" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">native-image tool</text>
  <line x1="350" y1="132" x2="350" y2="158" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ra178)"/>
  <line x1="590" y1="119" x2="400" y2="160" stroke="#6db33f" stroke-width="1.2" marker-end="url(#ra178)" opacity="0.5"/>
</svg>

Hints flow into `RuntimeHints` from multiple sources, serialise to JSON config files, and are fed into `native-image` to control what is included in the binary.

## 5. Runnable example

The scenario is a **document processing service** that uses reflection to load document parsers by class name, loads templates from resources, serialises results, and creates JDK proxies — all four hint categories in one growing example.

### Level 1 — Basic

Using the `RuntimeHints` API directly — register reflection and resource hints, then verify them programmatically.

```java
// RuntimeHintsBasic.java
import org.springframework.aot.hint.*;
import java.lang.reflect.*;

interface DocumentParser {
    String parse(String content);
}

class JsonParser implements DocumentParser {
    public String parse(String content) { return "JSON: " + content; }
}

class XmlParser implements DocumentParser {
    public String parse(String content) { return "XML: " + content; }
}

public class RuntimeHintsBasic {
    public static void main(String[] args) throws Exception {
        var hints = new RuntimeHints();

        // Reflection hint: both parser implementations need reflective instantiation
        hints.reflection().registerType(JsonParser.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.reflection().registerType(XmlParser.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);

        // Resource hint: template file loaded via ClassLoader
        hints.resources().registerPattern("templates/report.html");
        hints.resources().registerPattern("parsers/*.properties");

        // Serialization hint: result object passed through ObjectOutputStream
        hints.serialization().registerType(TypeReference.of("java.lang.String"));

        // Proxy hint: JDK proxy implementing DocumentParser
        hints.proxies().registerJdkProxy(DocumentParser.class);

        // Verify: introspect the registered hints
        System.out.println("=== Reflection hints ===");
        hints.reflection().typeHints().forEach(th ->
            System.out.println("  " + th.getType().getName() + " → " + th.getMemberCategories()));

        System.out.println("=== Resource patterns ===");
        hints.resources().resourcePatternHints().forEach(rh ->
            rh.getIncludes().forEach(p -> System.out.println("  " + p.toRegex())));

        // Demonstrate that the reflection actually works (in JVM mode)
        Class<?> cls = Class.forName("JsonParser");
        DocumentParser parser = (DocumentParser) cls.getDeclaredConstructor().newInstance();
        System.out.println(parser.parse("{\"key\":\"value\"}"));

        // JDK proxy
        Object proxy = Proxy.newProxyInstance(
            RuntimeHintsBasic.class.getClassLoader(),
            new Class[]{DocumentParser.class},
            (p, m, a) -> "Proxy handled: " + m.getName());
        System.out.println(proxy.toString());
    }
}
```

How to run: `java RuntimeHintsBasic.java`

`hints.reflection().registerType(JsonParser.class, MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS, ...)` tells `native-image` to include `JsonParser`'s constructor and methods in the binary. Without this hint in native mode, `cls.getDeclaredConstructor().newInstance()` would throw `ClassNotFoundException`. In JVM mode everything works regardless — hints are only consulted by `native-image` at build time.

### Level 2 — Intermediate

Integrate hints with a `RuntimeHintsRegistrar` used during the Spring AOT phase; verify with `RuntimeHintsPredicates`.

```java
// RuntimeHintsIntermediate.java
import org.springframework.aot.hint.*;
import org.springframework.aot.hint.predicate.*;
import java.util.*;

// Domain objects (need serialization + reflection hints for Jackson)
record Order(String id, String product, double amount) {}
record OrderResult(String orderId, String status, String message) {}

// Custom hints registrar
class DocumentServiceHints implements org.springframework.aot.hint.RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Reflection: Order fields + constructor (for Jackson deserialization)
        hints.reflection().registerType(Order.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.PUBLIC_FIELDS,
            MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.reflection().registerType(OrderResult.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.PUBLIC_FIELDS,
            MemberCategory.INVOKE_PUBLIC_METHODS);

        // Resources: config files loaded at runtime
        hints.resources().registerPattern("orders/schema.json");
        hints.resources().registerPattern("templates/order-*.html");

        // Serialization: cached results stored in session
        hints.serialization().registerType(Order.class);
        hints.serialization().registerType(OrderResult.class);
    }
}

public class RuntimeHintsIntermediate {
    public static void main(String[] args) {
        var hints = new RuntimeHints();
        new DocumentServiceHints().registerHints(hints, RuntimeHintsIntermediate.class.getClassLoader());

        // Verify using RuntimeHintsPredicates
        var predicates = RuntimeHintsPredicates.reflection();

        boolean orderCtorOk = predicates
            .onConstructor(Order.class.getDeclaredConstructors()[0])
            .test(hints);
        System.out.println("Order constructor hinted: " + orderCtorOk);  // true

        boolean resultCtorOk = predicates
            .onConstructor(OrderResult.class.getDeclaredConstructors()[0])
            .test(hints);
        System.out.println("OrderResult constructor hinted: " + resultCtorOk); // true

        // Resource patterns registered
        System.out.println("Resource patterns:");
        hints.resources().resourcePatternHints()
             .flatMap(rh -> rh.getIncludes().stream())
             .forEach(p -> System.out.println("  " + p.toRegex()));

        // Serialization types
        System.out.println("Serialization types:");
        hints.serialization().javaSerializationHints()
             .forEach(sh -> System.out.println("  " + sh.getType().getName()));
    }
}
```

How to run: `java RuntimeHintsIntermediate.java`

`RuntimeHintsPredicates.reflection().onConstructor(...).test(hints)` returns `true` only if the constructor has been registered with a category that allows invocation. Use this in `@SpringBootTest` with `RuntimeHintsPredicates` to assert that your registrar covers all needed access patterns — this is the standard way to write native-compatibility tests without actually building a native image.

### Level 3 — Advanced

A Spring Boot service with a custom `RuntimeHintsRegistrar` covering all four hint types; verification in a Spring AOT test.

```java
// RuntimeHintsAdvanced.java — Spring Boot service + hints registrar
import org.springframework.aot.hint.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.reflect.*;
import java.util.*;

interface Processor<T> { T process(String input); }

class OrderProcessor implements Processor<String> {
    public String process(String input) { return "ORDER:" + input.toUpperCase(); }
}

class InvoiceProcessor implements Processor<String> {
    public String process(String input) { return "INVOICE:" + input.toUpperCase(); }
}

// Hint registrar: covers reflection + proxy + resource + serialization
class ProcessorHintsRegistrar implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        // Reflection: both processor impls need reflective construction
        for (Class<?> cls : List.of(OrderProcessor.class, InvoiceProcessor.class)) {
            hints.reflection().registerType(cls,
                MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
                MemberCategory.INVOKE_PUBLIC_METHODS);
        }
        // Proxy: JDK proxy implementing Processor
        hints.proxies().registerJdkProxy(Processor.class);
        // Resources: processor config files
        hints.resources().registerPattern("processors/*.json");
        // Serialization: processing result cached to disk
        hints.serialization().registerType(TypeReference.of("java.lang.String"));
    }
}

@Service
class ProcessingService {
    // Loaded dynamically by name from config (requires reflection hint)
    private final Map<String, Processor<String>> registry = new LinkedHashMap<>();

    @Autowired
    ProcessingService() throws Exception {
        for (String cls : List.of("OrderProcessor", "InvoiceProcessor")) {
            // This reflective call requires a reflection hint in native mode
            @SuppressWarnings("unchecked")
            Processor<String> p = (Processor<String>)
                Class.forName(cls).getDeclaredConstructor().newInstance();
            registry.put(cls, p);
        }
    }

    public String process(String type, String input) {
        return registry.getOrDefault(type,
            s -> "UNKNOWN:" + s).process(input);
    }
}

@ImportRuntimeHints(ProcessorHintsRegistrar.class)  // registers hints during AOT
@SpringBootApplication
public class RuntimeHintsAdvanced {
    public static void main(String[] args) {
        var ctx = SpringApplication.run(RuntimeHintsAdvanced.class, args);
        var svc = ctx.getBean(ProcessingService.class);
        System.out.println(svc.process("OrderProcessor",   "ord-001"));
        System.out.println(svc.process("InvoiceProcessor", "inv-007"));
        SpringApplication.exit(ctx);
    }
}
```

How to run: `java RuntimeHintsAdvanced.java` (JVM); for native: `./mvnw -Pnative native:compile && ./target/app`

`@ImportRuntimeHints(ProcessorHintsRegistrar.class)` on `@SpringBootApplication` causes Spring AOT to invoke `ProcessorHintsRegistrar.registerHints(...)` during `spring-boot:process-aot`, which populates `reflect-config.json` with `OrderProcessor` and `InvoiceProcessor`. Without this, the `Class.forName("OrderProcessor").getDeclaredConstructor().newInstance()` call in `ProcessingService` would fail at native-image runtime.

## 6. Walkthrough

Tracing `ProcessingService` initialisation in the Level 3 app:

**Step 1 — AOT phase (`spring-boot:process-aot`):**
- `@ImportRuntimeHints(ProcessorHintsRegistrar.class)` is discovered on `RuntimeHintsAdvanced`.
- Spring AOT calls `new ProcessorHintsRegistrar().registerHints(hints, classLoader)`.
- Inside `registerHints`:
  - `hints.reflection().registerType(OrderProcessor.class, INVOKE_PUBLIC_CONSTRUCTORS, INVOKE_PUBLIC_METHODS)` → entry added for `OrderProcessor` in the reflection registry.
  - Same for `InvoiceProcessor`.
  - `hints.proxies().registerJdkProxy(Processor.class)` → entry in proxy registry.
  - `hints.resources().registerPattern("processors/*.json")` → pattern in resource registry.
- At end of AOT phase, the registries serialise to:
  - `reflect-config.json`: `[{"name":"OrderProcessor","allPublicConstructors":true,"allPublicMethods":true}, ...]`
  - `proxy-config.json`: `[{"interfaces":["Processor"]}]`
  - `resource-config.json`: `[{"pattern":"\\Qprocessors/\\E.*\\.json"}]`

**Step 2 — Native image build:**
- `native-image` reads `reflect-config.json`; `OrderProcessor` and `InvoiceProcessor` are included with their constructors and methods in the binary's reflection metadata.
- Without these entries the classes would be excluded entirely.

**Step 3 — Native runtime:**
- `ProcessingService()` constructor runs.
- `Class.forName("OrderProcessor")` — succeeds because the class is included in the binary.
- `.getDeclaredConstructor()` — succeeds because `INVOKE_PUBLIC_CONSTRUCTORS` was registered.
- `.newInstance()` — succeeds; `new OrderProcessor()` constructed reflectively.
- Registry populated; service ready.

**Request: `svc.process("OrderProcessor", "ord-001")`:**
```
registry.get("OrderProcessor") → OrderProcessor instance
.process("ord-001") → "ORDER:ORD-001"
```

## 7. Gotchas & takeaways

> **Hints are only consulted at `native-image` build time.** On the JVM, reflection works regardless of what hints are registered. A service that passes all JVM tests can still fail in native mode if hints are missing. Always run `./mvnw -Pnative native:test` or use `RuntimeHintsPredicates` in unit tests to verify hints cover all dynamic access paths.

> **`MemberCategory.DECLARED_FIELDS` vs `PUBLIC_FIELDS`** — Jackson uses `PUBLIC_FIELDS` to map public fields directly. If you have private fields serialised via getters, you need `INVOKE_PUBLIC_METHODS` for the getters, not `DECLARED_FIELDS`. Registering unnecessary categories increases binary size.

- Register the most restrictive `MemberCategory` set that satisfies the actual access pattern — overly broad hints increase native binary size.
- `hints.reflection().registerType(TypeReference.of("com.example.Foo"))` works even when `Foo` is not on the AOT-phase classpath — use `TypeReference.of(String)` for classes that exist only at runtime.
- `hints.resources().registerPattern("META-INF/services/**")` is needed for `java.util.ServiceLoader` usage — Spring Boot registers this automatically for standard Spring SPI, but custom `ServiceLoader` usages need manual hints.
- Use `@SpringBootTest(properties = "spring.aot.enabled=true")` with `RuntimeHintsPredicates` to write tests that fail at JVM time (cheap) instead of native-image build time (expensive).
