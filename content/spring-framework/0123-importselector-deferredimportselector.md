---
card: spring-framework
gi: 123
slug: importselector-deferredimportselector
title: "ImportSelector / DeferredImportSelector"
---

## 1. What it is

`ImportSelector` is an interface Spring calls when processing an `@Import` annotation. Instead of naming a concrete class to import, you name an `ImportSelector` implementation. Spring calls `selectImports()` on it, and the selector returns an array of class names to import — enabling **dynamic** configuration selection at context-creation time.

`DeferredImportSelector` extends `ImportSelector`. Its imports are processed **after** all regular `@Configuration` classes — crucial for auto-configuration that should yield to user-defined beans.

```java
@Configuration
@Import(FeatureSelector.class)
class AppConfig {}

class FeatureSelector implements ImportSelector {
    @Override
    public String[] selectImports(AnnotationMetadata meta) {
        return new String[]{ FastCacheConfig.class.getName() };
    }
}
```

## 2. Why & when

- **Spring Boot auto-configuration** — `AutoConfigurationImportSelector` is a `DeferredImportSelector` that reads `META-INF/spring/org.springframework.boot.autoconfigure.EnableAutoConfiguration` and imports the listed configs. Every `@EnableAutoConfiguration` (included in `@SpringBootApplication`) triggers this.
- **Feature selectors** — select which implementation config to import based on environment, classpath, or annotation attributes.
- **`@Enable*` annotations** — `@EnableCaching`, `@EnableAsync`, `@EnableWebMvc` all use `ImportSelector` to pull in the correct infrastructure config dynamically.
- **Conditional multi-config** — when you have N possible configurations and want to select one or more based on runtime metadata without a hard-coded `@Import` list.

## 3. Core concept

`ImportSelector`:

```java
public interface ImportSelector {
    String[] selectImports(AnnotationMetadata importingClassMetadata);
    // Optional: Predicate<String> getExclusionFilter()
}
```

`importingClassMetadata` is the metadata of the class bearing the `@Import`. Use it to read annotation attributes (e.g., what `@EnableFeature(mode = Mode.FAST)` declared).

`DeferredImportSelector`:

```java
public interface DeferredImportSelector extends ImportSelector {
    // Optional: Group for ordering and deduplication
    @Nullable Class<? extends Group> getImportGroup();
}
```

Processing order:

1. All regular `@Configuration` classes processed (including `@Import` of configs and plain `ImportSelector`).
2. `DeferredImportSelector` results processed last — their imports see the full bean definition registry from step 1, enabling `@ConditionalOnMissingBean` to work correctly.

`Group` (inner interface of `DeferredImportSelector`): allows multiple `DeferredImportSelector` instances to be merged and sorted together — used by Spring Boot to order auto-configurations.

## 4. Diagram

<svg viewBox="0 0 700 205" xmlns="http://www.w3.org/2000/svg">
  <!-- @Import(Selector) -->
  <rect x="10" y="60" width="175" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="83" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Import(Selector)</text>
  <text x="97" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">on @Configuration</text>
  <text x="97" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ImportSelector</text>
  <text x="97" y="135" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ immediate processing</text>
  <text x="97" y="148" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DeferredImportSelector</text>
  <text x="97" y="161" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">→ after all @Config classes</text>

  <!-- selectImports() -->
  <rect x="270" y="60" width="180" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="83" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">selectImports()</text>
  <text x="360" y="103" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads annotation metadata</text>
  <text x="360" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads environment</text>
  <text x="360" y="137" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">returns class names[ ]</text>

  <!-- Line -->
  <line x1="187" y1="105" x2="267" y2="105" stroke="#6db33f" stroke-width="2" marker-end="url(#a123)"/>
  <defs>
    <marker id="a123" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b123" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Imported configs -->
  <rect x="532" y="50" width="160" height="115" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="612" y="73" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Dynamically</text>
  <text x="612" y="88" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">imported configs</text>
  <text x="612" y="108" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">CacheConfig</text>
  <text x="612" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SecurityConfig</text>
  <text x="612" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">or nothing</text>
  <text x="612" y="157" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">based on metadata</text>

  <line x1="452" y1="105" x2="529" y2="105" stroke="#79c0ff" stroke-width="2" marker-end="url(#b123)"/>
  <text x="350" y="193" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">selectImports() returns class names → Spring processes those as if directly @Imported</text>
</svg>

`ImportSelector.selectImports()` returns class names; Spring imports them dynamically at config-processing time.

## 5. Runnable example

### Level 1 — Basic

`ImportSelector` that reads an annotation attribute to choose a configuration.

```java
// ImportSelectorBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.AnnotationAttributes;
import org.springframework.core.type.*;
import java.lang.annotation.*;

// Two cache implementations
@Configuration
class LocalCacheConfig {
    @Bean public String cacheType() { return "local"; }
    @Bean public CacheManager localCacheManager() { return new CacheManager("local"); }
}

@Configuration
class RemoteCacheConfig {
    @Bean public String cacheType() { return "remote"; }
    @Bean public CacheManager remoteCacheManager() { return new CacheManager("remote"); }
}

class CacheManager {
    final String type;
    CacheManager(String t) { this.type = t; System.out.println("[CacheManager] type=" + t); }
    public String get(String k) { return "[" + type + "] " + k; }
}

// Selector reads @EnableCache(type=...) attribute
class CacheImportSelector implements ImportSelector {
    @Override
    public String[] selectImports(AnnotationMetadata meta) {
        AnnotationAttributes attrs = AnnotationAttributes.fromMap(
            meta.getAnnotationAttributes(EnableCache.class.getName()));
        String type = attrs == null ? "local" : attrs.getString("type");
        System.out.println("[Selector] cache type requested: " + type);
        return "remote".equals(type)
            ? new String[]{RemoteCacheConfig.class.getName()}
            : new String[]{LocalCacheConfig.class.getName()};
    }
}

@Target(ElementType.TYPE) @Retention(RetentionPolicy.RUNTIME)
@Import(CacheImportSelector.class)
@interface EnableCache { String type() default "local"; }

@Configuration @EnableCache(type = "remote")
class AppConfig {}

public class ImportSelectorBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        System.out.println("cacheType: " + ctx.getBean("cacheType", String.class));
        System.out.println("get user: " + ctx.getBean(CacheManager.class).get("user:1"));
        System.out.println("local config present: " + ctx.containsBean("localCacheManager"));
        System.out.println("remote config present: " + ctx.containsBean("remoteCacheManager"));
        ctx.close();
    }
}
```

How to run: `java ImportSelectorBasic.java`

`@EnableCache(type = "remote")` triggers `CacheImportSelector`. The selector reads `"remote"` from the annotation metadata and returns `RemoteCacheConfig.class.getName()`. Spring processes that config — `LocalCacheConfig` is never registered.

### Level 2 — Intermediate

`DeferredImportSelector` that yields to user-defined beans (simulates `@ConditionalOnMissingBean`).

```java
// DeferredSelectorIntermediate.java
import org.springframework.context.annotation.*;
import org.springframework.core.type.*;
import java.lang.annotation.*;

// Default implementation shipped by a "library"
@Configuration
class DefaultSecurityConfig {
    @Bean
    public SecurityProvider defaultSecurity() {
        System.out.println("[DefaultSecurity] creating default SecurityProvider");
        return new DefaultSecurityProvider();
    }
}

interface SecurityProvider { String authenticate(String user); }

class DefaultSecurityProvider implements SecurityProvider {
    public String authenticate(String u) { return "[Default] authenticated " + u; }
}

class CustomSecurityProvider implements SecurityProvider {
    public String authenticate(String u) { return "[Custom] authenticated " + u; }
}

// DeferredImportSelector: runs after all user @Configuration classes
// Registers default only if the user hasn't defined a SecurityProvider
class SecurityAutoSelector implements DeferredImportSelector {
    @Override
    public String[] selectImports(AnnotationMetadata meta) {
        System.out.println("[SecurityAutoSelector] deferred processing");
        return new String[]{DefaultSecurityConfig.class.getName()};
    }
}

// Library annotation
@Target(ElementType.TYPE) @Retention(RetentionPolicy.RUNTIME)
@Import(SecurityAutoSelector.class)
@interface EnableSecurity {}

// === Scenario A: no user customization — default is used ===
@Configuration @EnableSecurity
class ScenarioA {}

// === Scenario B: user provides their own — conflict arises ===
@Configuration @EnableSecurity
class ScenarioB {
    // User's own bean — note: this creates a conflict since both register the SAME bean name
    // In real auto-config, @ConditionalOnMissingBean prevents this
    @Bean("userSecurity")
    public SecurityProvider customSecurity() {
        System.out.println("[ScenarioB] user-defined CustomSecurityProvider");
        return new CustomSecurityProvider();
    }
}

public class DeferredSelectorIntermediate {
    public static void main(String[] args) {
        System.out.println("=== Scenario A: default security ===");
        var ctxA = new AnnotationConfigApplicationContext(ScenarioA.class);
        System.out.println(ctxA.getBean(SecurityProvider.class).authenticate("alice"));
        ctxA.close();

        System.out.println("\n=== Scenario B: user + default ===");
        var ctxB = new AnnotationConfigApplicationContext(ScenarioB.class);
        // Both exist — user's under "userSecurity", default under "defaultSecurity"
        System.out.println("defaultSecurity: " + ctxB.containsBean("defaultSecurity"));
        System.out.println("userSecurity: " + ctxB.containsBean("userSecurity"));
        System.out.println(ctxB.getBean("userSecurity", SecurityProvider.class).authenticate("bob"));
        ctxB.close();
    }
}
```

How to run: `java DeferredSelectorIntermediate.java`

`SecurityAutoSelector` is a `DeferredImportSelector` — its `DefaultSecurityConfig` is registered after `ScenarioB`'s user config. In a real Spring Boot scenario, `@ConditionalOnMissingBean` would prevent `defaultSecurity` from registering when a user bean already exists; here we show the deferred ordering without the conditional.

### Level 3 — Advanced

Full `DeferredImportSelector` with `Group` for ordering and annotation-driven multi-module selection.

```java
// DeferredSelectorAdvanced.java
import org.springframework.context.annotation.*;
import org.springframework.core.type.*;
import org.springframework.core.annotation.AnnotationAttributes;
import java.lang.annotation.*;
import java.util.*;

// Three feature configs
@Configuration class PaymentConfig {
    @Bean String paymentModule() { System.out.println("[Payment] loaded"); return "payment"; }
}
@Configuration class ShippingConfig {
    @Bean String shippingModule() { System.out.println("[Shipping] loaded"); return "shipping"; }
}
@Configuration class NotificationConfig {
    @Bean String notificationModule() { System.out.println("[Notification] loaded"); return "notification"; }
}

// Annotation that lists desired modules
@Target(ElementType.TYPE) @Retention(RetentionPolicy.RUNTIME)
@Import(ModuleSelector.class)
@interface EnableModules { String[] value() default {}; }

// Deferred selector with group — orders multiple selectors together
class ModuleSelector implements DeferredImportSelector {
    private static final Map<String, String> MODULE_MAP = Map.of(
        "payment",      PaymentConfig.class.getName(),
        "shipping",     ShippingConfig.class.getName(),
        "notification", NotificationConfig.class.getName()
    );

    @Override
    public String[] selectImports(AnnotationMetadata meta) {
        AnnotationAttributes attrs = AnnotationAttributes.fromMap(
            meta.getAnnotationAttributes(EnableModules.class.getName()));
        String[] modules = attrs == null ? new String[0] : attrs.getStringArray("value");
        System.out.println("[ModuleSelector] enabled modules: " + Arrays.toString(modules));
        return Arrays.stream(modules)
            .map(m -> MODULE_MAP.getOrDefault(m, ""))
            .filter(s -> !s.isEmpty())
            .toArray(String[]::new);
    }

    @Override
    public Class<? extends Group> getImportGroup() {
        return ModuleGroup.class;
    }

    static class ModuleGroup implements DeferredImportSelector.Group {
        private final List<Entry> entries = new ArrayList<>();

        @Override
        public void process(AnnotationMetadata meta, DeferredImportSelector selector) {
            String[] imports = selector.selectImports(meta);
            for (String name : imports) entries.add(new Entry(meta, name));
        }

        @Override
        public Iterable<Entry> selectImports() {
            // Sort alphabetically for deterministic order
            entries.sort(Comparator.comparing(Entry::getImportClassName));
            System.out.println("[ModuleGroup] ordering " + entries.size() + " imports");
            return entries;
        }
    }
}

// App enables specific modules
@Configuration
@EnableModules({"payment", "notification"})
class AppCfg {}

public class DeferredSelectorAdvanced {
    public static void main(String[] args) {
        System.out.println("=== Loading app with payment + notification modules ===");
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);

        System.out.println("\n=== Active modules ===");
        System.out.println("payment:      " + ctx.containsBean("paymentModule"));
        System.out.println("shipping:     " + ctx.containsBean("shippingModule"));
        System.out.println("notification: " + ctx.containsBean("notificationModule"));

        System.out.println("\n=== Module values ===");
        System.out.println(ctx.getBean("paymentModule", String.class));
        System.out.println(ctx.getBean("notificationModule", String.class));
        ctx.close();
    }
}
```

How to run: `java DeferredSelectorAdvanced.java`

`@EnableModules({"payment", "notification"})` triggers `ModuleSelector`. The selector reads the module names, maps them to config class names, and returns them. The `ModuleGroup` sorts imports alphabetically for deterministic ordering. `ShippingConfig` is never loaded.

## 6. Walkthrough

Execution for Level 3:

1. **`AnnotationConfigApplicationContext(AppCfg.class)` created** — `ConfigurationClassPostProcessor` finds `@Import(ModuleSelector.class)` via `@EnableModules`.
2. **`ModuleSelector` detected as `DeferredImportSelector`** — deferred for later.
3. **All `@Configuration` classes processed first** — in this example, only `AppCfg` itself.
4. **Deferred phase begins** — `ModuleGroup.process()` called with `AppCfg`'s metadata and `ModuleSelector` instance. `selectImports()` runs → reads `["payment", "notification"]` → returns `[NotificationConfig.class.getName(), PaymentConfig.class.getName()]`.
5. **`ModuleGroup.selectImports()`** — sorts entries alphabetically → `[NotificationConfig, PaymentConfig]`.
6. **`[ModuleGroup] ordering 2 imports`** printed.
7. **`NotificationConfig` processed** → `notificationModule` bean registered. Prints `[Notification] loaded`.
8. **`PaymentConfig` processed** → `paymentModule` bean registered. Prints `[Payment] loaded`.
9. **`ShippingConfig`** — never mentioned, never loaded.

Expected output:
```
=== Loading app with payment + notification modules ===
[ModuleSelector] enabled modules: [payment, notification]
[ModuleGroup] ordering 2 imports
[Notification] loaded
[Payment] loaded

=== Active modules ===
payment:      true
shipping:     false
notification: true

=== Module values ===
payment
notification
```

## 7. Gotchas & takeaways

> `ImportSelector.selectImports()` is called **before** the bean factory has finished populating — you cannot call `ctx.getBean()` inside it. Use `ConditionContext` (via `EnvironmentAware`, `BeanFactoryAware`, or `ResourceLoaderAware` on the selector) to inspect current state.

> `DeferredImportSelector` implementations run after all `@Configuration` classes have been parsed but before beans are instantiated. This is the correct moment to check for user-defined beans via `BeanDefinitionRegistry` — enabling `@ConditionalOnMissingBean` semantics.

- Return an **empty array** (`new String[0]`) from `selectImports()` to import nothing — do not return `null`.
- `selectImports()` receives the metadata of the **importing** class (the class that has `@Import`), not the selector class itself. Use it to read annotation attributes on the `@Enable*` annotation.
- `ImportBeanDefinitionRegistrar` (a sibling to `ImportSelector`) lets you register `BeanDefinition`s programmatically — more powerful but more verbose.
- Spring Boot's entire auto-configuration system is a `DeferredImportSelector` reading `META-INF/spring/...` files — understanding this interface explains how `@SpringBootApplication` pulls in hundreds of configurations lazily and conditionally.
