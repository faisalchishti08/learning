---
card: spring-framework
gi: 179
slug: runtimehintsregistrar
title: RuntimeHintsRegistrar
---

## 1. What it is

`RuntimeHintsRegistrar` is a Spring AOT interface you implement to register runtime hints programmatically. During `spring-boot:process-aot`, Spring discovers every registered implementation and calls `registerHints(RuntimeHints, ClassLoader)`, giving you full access to the `RuntimeHints` API.

```java
public class MyHintsRegistrar implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        hints.reflection().registerType(MyService.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.resources().registerPattern("config/default-rules.json");
    }
}
```

The registrar is activated either via `@ImportRuntimeHints(MyHintsRegistrar.class)` on a configuration class, or by listing the fully qualified class name in `META-INF/spring/aot.factories` under the key `org.springframework.aot.hint.RuntimeHintsRegistrar`.

## 2. Why & when

- **Dynamic class loading** — your code calls `Class.forName(name)` or `Constructor.newInstance()` on classes whose names come from config or database; list those classes in reflection hints so native-image includes them.
- **Third-party libraries without native support** — libraries that use reflection internally (old JAXB providers, Apache Commons BeanUtils, legacy ORM tools) need hints you supply because the library itself doesn't provide them.
- **Custom proxy patterns** — hand-rolled JDK proxies or CGLIB usage outside Spring AOP need explicit proxy hints.
- **Classpath resources** — templates, JSON schemas, XSD files loaded via `getResourceAsStream()` must be declared.
- **Prefer `@RegisterReflectionForBinding`** (next topic) for the common case of registering a DTO/record for Jackson — it's a one-liner and handles the common member categories automatically.
- **Prefer AOT test verification** over guessing: run `RuntimeHintsPredicates` tests in JVM mode to assert that your registrar covers the required access patterns before building native.

## 3. Core concept

Discovery mechanisms — two ways to register a `RuntimeHintsRegistrar`:

**Via annotation (preferred):**
```java
@ImportRuntimeHints(MyHintsRegistrar.class)
@Configuration   // or @SpringBootApplication, or any @Component
class AppConfig { }
```

**Via `aot.factories` (library authors, no Spring context dependency):**
```
# META-INF/spring/aot.factories
org.springframework.aot.hint.RuntimeHintsRegistrar=\
  com.example.MyHintsRegistrar
```

Both are collected by the AOT engine and invoked in sequence. A registrar can register hints across all four hint types in a single `registerHints` call.

**Execution context:**

`registerHints` is called during the AOT build step — not at JVM startup and not at native runtime. It runs in a JVM process that has access to your full classpath, so `classLoader.loadClass()` and `ClassUtils.resolveClassName()` work correctly.

**Relationship to generated output:**

```
AOT engine invokes registerHints()
        │
        ▼
RuntimeHints object (in-memory)
        │
        ▼ serialised by AOT engine
reflect-config.json / resource-config.json / …
        │
        ▼ read by native-image
native binary includes hinted elements
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="rha" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rhb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Registration paths -->
  <rect x="5" y="10" width="180" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="29" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@ImportRuntimeHints(MyReg.class)</text>

  <rect x="5" y="50" width="180" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="65" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">META-INF/spring/aot.factories</text>
  <text x="95" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">key=RuntimeHintsRegistrar</text>

  <rect x="5" y="90" width="180" height="30" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring AOT built-in processors</text>
  <text x="95" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(auto, covers standard beans)</text>

  <!-- AOT engine box -->
  <rect x="230" y="40" width="150" height="70" rx="6" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="2"/>
  <text x="305" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">AOT engine</text>
  <text x="305" y="85" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">process-aot phase</text>
  <text x="305" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">calls registerHints()</text>

  <line x1="187" y1="25"  x2="228" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rha)"/>
  <line x1="187" y1="65"  x2="228" y2="72" stroke="#8b949e" stroke-width="1.5" marker-end="url(#rha)" opacity="0.6"/>
  <line x1="187" y1="105" x2="228" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#rha)" opacity="0.6"/>

  <!-- RuntimeHints object -->
  <rect x="430" y="40" width="140" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="62" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">RuntimeHints</text>
  <text x="500" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.reflection()</text>
  <text x="500" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.resources()</text>
  <text x="500" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.proxies() / .serialization()</text>
  <line x1="382" y1="75" x2="428" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rha)"/>

  <!-- Output -->
  <rect x="595" y="10"  width="100" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="645" y="24" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">reflect-config.json</text>
  <rect x="595" y="37"  width="100" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="645" y="51" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">resource-config.json</text>
  <rect x="595" y="64"  width="100" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="645" y="78" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">proxy-config.json</text>
  <rect x="595" y="91"  width="100" height="20" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="645" y="105" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">serialization-config.json</text>
  <line x1="572" y1="75" x2="592" y2="55" stroke="#6db33f" stroke-width="1.2" marker-end="url(#rha)" opacity="0.7"/>
  <line x1="572" y1="75" x2="592" y2="75" stroke="#6db33f" stroke-width="1.2" marker-end="url(#rha)" opacity="0.7"/>
  <line x1="572" y1="75" x2="592" y2="100" stroke="#6db33f" stroke-width="1.2" marker-end="url(#rha)" opacity="0.7"/>

  <text x="350" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">All registrars share one RuntimeHints instance — order of registration does not matter.</text>
  <text x="350" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Registrars run at build time only; they are NOT invoked at JVM or native runtime.</text>
</svg>

`RuntimeHintsRegistrar` implementations are discovered at AOT build time, invoked once to populate a shared `RuntimeHints` object, which is serialised to JSON config files consumed by `native-image`.

## 5. Runnable example

The scenario is a **plugin registry** service that loads plugin implementations reflectively by class name — growing from a simple registrar to a full Spring Boot integration.

### Level 1 — Basic

Implement `RuntimeHintsRegistrar` and call it manually to verify it works, without a Spring context.

```java
// RhintsRegistrarBasic.java
import org.springframework.aot.hint.*;

// Plugin interface loaded via reflection in production
interface Plugin {
    String execute(String input);
}

class CsvPlugin  implements Plugin { public String execute(String i) { return "CSV:"  + i; } }
class JsonPlugin implements Plugin { public String execute(String i) { return "JSON:" + i; } }
class XmlPlugin  implements Plugin { public String execute(String i) { return "XML:"  + i; } }

// The registrar — implement once, used by AOT at build time
class PluginHintsRegistrar implements RuntimeHintsRegistrar {
    // Centralises all plugin hints in one place
    static final Class<?>[] PLUGINS = {CsvPlugin.class, JsonPlugin.class, XmlPlugin.class};

    @Override
    public void registerHints(RuntimeHints hints, ClassLoader classLoader) {
        for (Class<?> plugin : PLUGINS) {
            hints.reflection().registerType(plugin,
                MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
                MemberCategory.INVOKE_PUBLIC_METHODS);
        }
        // JDK proxy for Plugin interface (used in tests with Mockito-style proxies)
        hints.proxies().registerJdkProxy(Plugin.class);
        // Config files listing available plugins
        hints.resources().registerPattern("plugins/registry.properties");
    }
}

public class RhintsRegistrarBasic {
    public static void main(String[] args) throws Exception {
        // Invoke the registrar manually (simulates what AOT engine does)
        var hints = new RuntimeHints();
        new PluginHintsRegistrar().registerHints(hints,
            RhintsRegistrarBasic.class.getClassLoader());

        // Verify reflection hints
        System.out.println("Hinted types:");
        hints.reflection().typeHints()
             .forEach(th -> System.out.println("  " + th.getType().getName()
                 + " categories=" + th.getMemberCategories()));

        // Use the reflective access (works on JVM regardless of hints)
        for (Class<?> cls : PluginHintsRegistrar.PLUGINS) {
            Plugin p = (Plugin) Class.forName(cls.getName())
                                     .getDeclaredConstructor()
                                     .newInstance();
            System.out.println(p.execute("test"));
        }
    }
}
```

How to run: `java RhintsRegistrarBasic.java`

Calling `registerHints` manually simulates what the AOT engine does. On the JVM, `Class.forName()` works regardless of whether hints are registered — hints only matter for native image compilation. The output of `typeHints()` shows exactly what will appear in `reflect-config.json` during a real AOT build.

### Level 2 — Intermediate

Multiple registrars cooperating; use `RuntimeHintsPredicates` to write assertions that catch missing hints before going to native.

```java
// RhintsRegistrarIntermediate.java
import org.springframework.aot.hint.*;
import org.springframework.aot.hint.predicate.*;
import java.util.*;

// Domain models
record User(String id, String email, String role) {}
record UserEvent(String type, User user, long timestamp) {}

// Registrar 1: user domain model hints (reflection + serialization)
class UserDomainHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.reflection().registerType(User.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS,
            MemberCategory.PUBLIC_FIELDS);
        hints.serialization().registerType(User.class);
        hints.serialization().registerType(UserEvent.class);
    }
}

// Registrar 2: audit infrastructure hints (resources + proxy)
class AuditInfraHints implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.resources().registerPattern("audit/*.sql");
        hints.resources().registerPattern("audit/schema-*.xml");
        hints.proxies().registerJdkProxy(
            java.util.function.Predicate.class);  // audit filter proxy
    }
}

public class RhintsRegistrarIntermediate {
    public static void main(String[] args) throws Exception {
        var hints = new RuntimeHints();
        var cl    = RhintsRegistrarIntermediate.class.getClassLoader();

        // Apply all registrars — all share the same RuntimeHints instance
        new UserDomainHints().registerHints(hints, cl);
        new AuditInfraHints().registerHints(hints, cl);

        // Assert using RuntimeHintsPredicates (use in @SpringBootTest in real code)
        var refl = RuntimeHintsPredicates.reflection();

        var userCtor = User.class.getDeclaredConstructors()[0];
        assert refl.onConstructor(userCtor).test(hints)
            : "User constructor not hinted!";

        var emailMethod = User.class.getMethod("email");
        assert refl.onMethod(emailMethod).test(hints)
            : "User.email() not hinted!";

        System.out.println("All predicate assertions passed.");

        // Serialization
        System.out.println("Serialization types:");
        hints.serialization().javaSerializationHints()
             .forEach(sh -> System.out.println("  " + sh.getType().getName()));

        // Resources
        System.out.println("Resource patterns:");
        hints.resources().resourcePatternHints()
             .flatMap(rh -> rh.getIncludes().stream())
             .forEach(p -> System.out.println("  " + p.toRegex()));
    }
}
```

How to run: `java RhintsRegistrarIntermediate.java`

Multiple `RuntimeHintsRegistrar` instances all write into the same shared `RuntimeHints` object. The order of registration does not matter; all hints are merged. `RuntimeHintsPredicates.reflection().onConstructor(ctor).test(hints)` returns `true` only if the constructor is registered with a category that allows invocation — use these assertions in JVM tests to catch missing hints without building a native binary.

### Level 3 — Advanced

Attach registrars to a Spring Boot application using both `@ImportRuntimeHints` and `aot.factories`; include a helper that inspects the registrar output at AOT time.

```java
// RhintsRegistrarAdvanced.java — Spring Boot, full AOT wiring
import org.springframework.aot.hint.*;
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

// --- Domain ---
record CacheEntry(String key, String value, long ttl) {}

// --- Registrar via @ImportRuntimeHints ---
class CacheHintsRegistrar implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.reflection().registerType(CacheEntry.class,
            MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS,
            MemberCategory.INVOKE_PUBLIC_METHODS);
        hints.serialization().registerType(CacheEntry.class);
        hints.resources().registerPattern("cache/eviction-rules.json");
        System.out.println("[AOT] CacheHintsRegistrar invoked");
    }
}

// --- Registrar via aot.factories (for library authors) ---
// In a real project: list this in META-INF/spring/aot.factories
// org.springframework.aot.hint.RuntimeHintsRegistrar=\
//   com.example.LibraryHintsRegistrar
class LibraryHintsRegistrar implements RuntimeHintsRegistrar {
    @Override
    public void registerHints(RuntimeHints hints, ClassLoader cl) {
        hints.resources().registerPattern("lib/defaults.properties");
        System.out.println("[AOT] LibraryHintsRegistrar invoked");
    }
}

@Service
class CacheService {
    private final Map<String, CacheEntry> store = new LinkedHashMap<>();
    public void put(String key, String value, long ttl) {
        store.put(key, new CacheEntry(key, value, ttl));
    }
    public Optional<CacheEntry> get(String key) { return Optional.ofNullable(store.get(key)); }
}

@ImportRuntimeHints(CacheHintsRegistrar.class)  // annotation-driven
@SpringBootApplication
public class RhintsRegistrarAdvanced {
    public static void main(String[] args) {
        var ctx = SpringApplication.run(RhintsRegistrarAdvanced.class, args);
        var svc = ctx.getBean(CacheService.class);
        svc.put("session-1", "user:alice", 3600L);
        svc.get("session-1").ifPresent(e ->
            System.out.println("Cached: " + e.key() + "=" + e.value()));
        SpringApplication.exit(ctx);
    }
}
```

How to run: `java RhintsRegistrarAdvanced.java` (prints `[AOT] CacheHintsRegistrar invoked` only during `process-aot`)

`@ImportRuntimeHints(CacheHintsRegistrar.class)` attaches the registrar to the Spring Boot application class. During `./mvnw spring-boot:process-aot`, the AOT engine discovers this annotation, instantiates `CacheHintsRegistrar`, and calls `registerHints`. The `System.out.println` inside will appear in the build log during the AOT phase — useful for verifying registrar execution in CI. At JVM runtime, `registerHints` is never called again.

## 6. Walkthrough

Tracing the lifecycle of `CacheHintsRegistrar` from source to native binary:

**Phase 1 — Compile time (regular `javac`):**
- `CacheHintsRegistrar.class` is compiled and packaged in the JAR.
- `@ImportRuntimeHints(CacheHintsRegistrar.class)` on `RhintsRegistrarAdvanced` is an annotation with a `Class[]` attribute — this is statically resolvable by the AOT engine.

**Phase 2 — AOT time (`./mvnw spring-boot:process-aot`):**
1. AOT engine scans all beans; finds `@ImportRuntimeHints(CacheHintsRegistrar.class)` on `RhintsRegistrarAdvanced`.
2. Instantiates `CacheHintsRegistrar` via `new CacheHintsRegistrar()`.
3. Calls `registerHints(hints, classLoader)` where `hints` is the shared `RuntimeHints` instance.
4. Inside `registerHints`:
   - `hints.reflection().registerType(CacheEntry.class, ...)` → CacheEntry added to reflection registry.
   - `hints.serialization().registerType(CacheEntry.class)` → CacheEntry added to serialization registry.
   - `hints.resources().registerPattern("cache/eviction-rules.json")` → pattern added to resource registry.
5. Registrar prints `[AOT] CacheHintsRegistrar invoked` (build log only).
6. At end of AOT phase, `hints` is serialised:
   - `reflect-config.json`: `[{"name":"CacheEntry","allPublicConstructors":true,"allPublicMethods":true}]`
   - `serialization-config.json`: `[{"name":"CacheEntry"}]`
   - `resource-config.json`: `[{"pattern":"\\Qcache/eviction-rules.json\\E"}]`

**Phase 3 — Native build (`native-image`):**
- Reads `reflect-config.json` → includes `CacheEntry` with constructor + methods.
- Reads `resource-config.json` → embeds `cache/eviction-rules.json` in the binary (if present on classpath).

**Phase 4 — Native runtime:**
- `CacheService.put("session-1", "user:alice", 3600L)` creates `new CacheEntry(...)`.
- Because `CacheEntry` was hinted, any reflective serialisation of the entry (e.g. Jackson or `ObjectOutputStream`) succeeds.
- `[AOT] CacheHintsRegistrar invoked` does NOT print — `registerHints` is never called at runtime.

## 7. Gotchas & takeaways

> **`registerHints` runs at build time only.** Any expensive operations (database lookups, HTTP calls) inside `registerHints` will run during `process-aot` in CI — keep registrars fast and side-effect-free. Never read from a running database to discover which classes need hints; instead, enumerate them statically.

> **Multiple registrars for the same class add, not overwrite, member categories.** If registrar A calls `registerType(Foo.class, INVOKE_PUBLIC_METHODS)` and registrar B calls `registerType(Foo.class, DECLARED_FIELDS)`, the final `reflect-config.json` entry for `Foo` includes both. There is no conflict — the union is used.

- A registrar registered via `META-INF/spring/aot.factories` is discovered automatically from any JAR on the classpath — library authors should use this mechanism so library users get native compatibility without manual `@ImportRuntimeHints`.
- Test your registrar in JVM mode with `RuntimeHintsPredicates`: `RuntimeHintsPredicates.reflection().onType(MyClass.class).withMemberCategories(MemberCategory.INVOKE_PUBLIC_CONSTRUCTORS).test(hints)` — returns `true` only when correctly registered.
- The `classLoader` argument to `registerHints` is useful for dynamically listing classes: `ClassUtils.resolveClassName("com.example.Foo", classLoader)` lets you register classes by string name, even types not directly referenced in your module.
- Avoid registering `Object.class` or common JDK types — GraalVM includes them by default via its JDK substitutions; explicit hints for them are redundant.
