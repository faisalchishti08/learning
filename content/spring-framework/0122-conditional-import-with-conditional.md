---
card: spring-framework
gi: 122
slug: conditional-import-with-conditional
title: "Conditional import with @Conditional"
---

## 1. What it is

`@Conditional` lets a `@Bean` method or a whole `@Configuration` class be registered only when a custom condition holds at context-creation time. The annotation takes a `Condition` implementation that Spring evaluates before processing the annotated element. If the `Condition` returns `false`, the bean or config is silently skipped.

```java
@Bean
@Conditional(OnProductionCondition.class)
public MetricsExporter metricsExporter() { ... }
```

Spring also ships ready-made condition annotations (via `spring-boot-autoconfigure`):
`@ConditionalOnProperty`, `@ConditionalOnMissingBean`, `@ConditionalOnClass`, etc. — these are all `@Conditional` wrappers.

## 2. Why & when

- **Profile-like gating without `@Profile`** — enable a bean only when a system property, environment variable, or class is present.
- **Auto-configuration** — Spring Boot conditionally registers infrastructure beans so user-provided beans win.
- **Feature flags** — activate experimental features based on config state.
- **`@Profile` is itself `@Conditional`** — `@Profile("prod")` is equivalent to `@Conditional(ProfileCondition.class)`.

## 3. Core concept

The `Condition` interface:

```java
@FunctionalInterface
public interface Condition {
    boolean matches(ConditionContext context, AnnotatedTypeMetadata metadata);
}
```

`ConditionContext` provides access to:
- `BeanFactory` / `BeanDefinitionRegistry` — inspect what's already registered.
- `Environment` — read properties, active profiles.
- `ResourceLoader` — check file/classpath resources.
- `ClassLoader` — check if a class is present.

Evaluation order:
1. `@Configuration` class-level `@Conditional` — if `false`, the entire class (all its `@Bean` methods) is skipped.
2. `@Bean` method-level `@Conditional` — individual method skipped if `false`.

Conditions are evaluated **before** bean instantiation — at `BeanDefinition` registration time.

`@ConditionOnX` annotations from Spring Boot are all composed from `@Conditional` plus a `SpringBootCondition` subclass. The pattern is fully reusable: wrap `@Conditional(MyCondition.class)` in your own meta-annotation to create custom `@EnableIfX` annotations.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Condition check -->
  <rect x="10" y="55" width="175" height="95" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="78" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Conditional</text>
  <text x="97" y="96" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Condition.matches()</text>
  <text x="97" y="114" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ConditionContext:</text>
  <text x="97" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">env / factory / loader</text>
  <text x="97" y="144" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">AnnotatedTypeMetadata</text>

  <!-- True path -->
  <rect x="275" y="25" width="150" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="48" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">true → register bean</text>
  <text x="350" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanDefinition added</text>

  <!-- False path -->
  <rect x="275" y="130" width="150" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="350" y="153" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">false → skip silently</text>
  <text x="350" y="167" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">no BeanDefinition</text>

  <line x1="187" y1="90" x2="272" y2="48" stroke="#6db33f" stroke-width="2" marker-end="url(#a122)"/>
  <line x1="187" y1="120" x2="272" y2="153" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b122)"/>
  <defs>
    <marker id="a122" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b122" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Context -->
  <rect x="510" y="55" width="180" height="95" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="600" y="78" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ConditionContext</text>
  <text x="600" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">env.getProperty("key")</text>
  <text x="600" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">loader.loadClass("Cls")</text>
  <text x="600" y="131" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">factory.containsBean("b")</text>

  <line x1="427" y1="103" x2="507" y2="103" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c122)"/>
  <defs><marker id="c122" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>

  <text x="350" y="192" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Condition.matches() gates BeanDefinition registration — evaluated before instantiation</text>
</svg>

`@Conditional` intercepts before registration; `true` adds the definition, `false` silently drops it.

## 5. Runnable example

### Level 1 — Basic

Custom `Condition` that checks a system property — register an alert service only when `app.alerts=true`.

```java
// ConditionalBasic.java
import org.springframework.context.annotation.*;
import org.springframework.core.type.AnnotatedTypeMetadata;

// Condition: register only when system property app.alerts=true
class AlertsEnabledCondition implements Condition {
    @Override
    public boolean matches(ConditionContext ctx, AnnotatedTypeMetadata meta) {
        String value = ctx.getEnvironment().getProperty("app.alerts");
        boolean enabled = "true".equalsIgnoreCase(value);
        System.out.println("[Condition] app.alerts=" + value + " → " + enabled);
        return enabled;
    }
}

class AlertService {
    public void alert(String msg) { System.out.println("[ALERT] " + msg); }
}

@Configuration
class CondCfg {
    @Bean
    @Conditional(AlertsEnabledCondition.class)
    public AlertService alertService() {
        System.out.println("[Bean] creating AlertService");
        return new AlertService();
    }

    @Bean
    public String appName() { return "MyApp"; }
}

public class ConditionalBasic {
    public static void main(String[] args) {
        System.out.println("=== Without property (skipped) ===");
        var ctx1 = new AnnotationConfigApplicationContext(CondCfg.class);
        System.out.println("alertService present: " + ctx1.containsBean("alertService"));
        ctx1.close();

        System.out.println("\n=== With app.alerts=true (registered) ===");
        System.setProperty("app.alerts", "true");
        var ctx2 = new AnnotationConfigApplicationContext(CondCfg.class);
        System.out.println("alertService present: " + ctx2.containsBean("alertService"));
        ctx2.getBean(AlertService.class).alert("disk 95%");
        ctx2.close();
        System.clearProperty("app.alerts");
    }
}
```

How to run: `java ConditionalBasic.java`

Without the property, the condition returns `false` and `AlertService` is never registered. With `app.alerts=true`, it is registered and functional.

### Level 2 — Intermediate

Class-level `@Conditional` on a whole `@Configuration` class, plus multiple conditions combined with `@ConditionAnd`.

```java
// ConditionalConfig.java
import org.springframework.context.annotation.*;
import org.springframework.core.type.AnnotatedTypeMetadata;

// Condition 1: checks environment property
class EnvCondition implements Condition {
    @Override
    public boolean matches(ConditionContext ctx, AnnotatedTypeMetadata meta) {
        String env = ctx.getEnvironment().getProperty("app.env", "dev");
        System.out.println("[EnvCondition] env=" + env);
        return "prod".equals(env) || "staging".equals(env);
    }
}

// Condition 2: checks if another bean is already registered
class NoBeanCondition implements Condition {
    @Override
    public boolean matches(ConditionContext ctx, AnnotatedTypeMetadata meta) {
        boolean absent = !ctx.getBeanFactory().containsBeanDefinition("customMonitor");
        System.out.println("[NoBeanCondition] customMonitor absent=" + absent);
        return absent;
    }
}

class DefaultMonitor {
    DefaultMonitor() { System.out.println("[DefaultMonitor] created"); }
    public void monitor() { System.out.println("[DefaultMonitor] monitoring"); }
}

class CustomMonitor {
    CustomMonitor() { System.out.println("[CustomMonitor] created"); }
    public void monitor() { System.out.println("[CustomMonitor] monitoring (override)"); }
}

// Entire config skipped if not in prod/staging
@Configuration
@Conditional(EnvCondition.class)
class ProductionConfig {
    @Bean
    @Conditional(NoBeanCondition.class)   // registered only if no customMonitor exists
    public DefaultMonitor defaultMonitor() { return new DefaultMonitor(); }
}

// Always active — user might provide customMonitor here
@Configuration
class AppCfg {
    @Bean
    public String info() { return "App running"; }
    // Uncomment below to provide a customMonitor that blocks DefaultMonitor:
    // @Bean public CustomMonitor customMonitor() { return new CustomMonitor(); }
}

public class ConditionalConfig {
    public static void main(String[] args) {
        System.out.println("=== dev (ProductionConfig skipped) ===");
        var ctx1 = new AnnotationConfigApplicationContext(AppCfg.class, ProductionConfig.class);
        System.out.println("defaultMonitor: " + ctx1.containsBean("defaultMonitor"));
        ctx1.close();

        System.out.println("\n=== prod (ProductionConfig active) ===");
        System.setProperty("app.env", "prod");
        var ctx2 = new AnnotationConfigApplicationContext(AppCfg.class, ProductionConfig.class);
        System.out.println("defaultMonitor: " + ctx2.containsBean("defaultMonitor"));
        if (ctx2.containsBean("defaultMonitor"))
            ctx2.getBean(DefaultMonitor.class).monitor();
        ctx2.close();
        System.clearProperty("app.env");
    }
}
```

How to run: `java ConditionalConfig.java`

In dev mode, `EnvCondition` returns `false` → entire `ProductionConfig` is skipped. In prod mode, `ProductionConfig` is active and `NoBeanCondition` registers `DefaultMonitor` because `customMonitor` isn't present.

### Level 3 — Advanced

Custom `@EnableIf*` meta-annotation that composes `@Conditional` + condition logic for a feature-flag pattern.

```java
// ConditionalFeatureFlag.java
import org.springframework.context.annotation.*;
import org.springframework.core.type.AnnotatedTypeMetadata;
import java.lang.annotation.*;
import java.util.*;

// Generic condition that reads a property name from the annotation metadata
class PropertyEnabledCondition implements Condition {
    @Override
    public boolean matches(ConditionContext ctx, AnnotatedTypeMetadata meta) {
        Map<String, Object> attrs = meta.getAnnotationAttributes(EnableIfProperty.class.getName());
        if (attrs == null) return false;
        String property = (String) attrs.get("property");
        String havingValue = (String) attrs.get("havingValue");
        String actual = ctx.getEnvironment().getProperty(property, "");
        boolean match = havingValue.equals(actual);
        System.out.printf("[PropertyEnabledCondition] %s=%s (expected=%s) → %s%n",
            property, actual, havingValue, match);
        return match;
    }
}

// Custom meta-annotation — activates a config when a property has the right value
@Target({ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Conditional(PropertyEnabledCondition.class)
@interface EnableIfProperty {
    String property();
    String havingValue();
}

// Feature A: enabled when feature.search=enabled
@Configuration
@EnableIfProperty(property = "feature.search", havingValue = "enabled")
class SearchConfig {
    @Bean SearchService searchService() { return new SearchService(); }
}

// Feature B: enabled when feature.recommendations=enabled
@Configuration
@EnableIfProperty(property = "feature.recommendations", havingValue = "enabled")
class RecommendationConfig {
    @Bean RecommendationEngine engine() { return new RecommendationEngine(); }
}

class SearchService {
    public String search(String q) { return "[Search] results for: " + q; }
}

class RecommendationEngine {
    public String recommend(String user) { return "[Recs] items for: " + user; }
}

@Configuration
@Import({SearchConfig.class, RecommendationConfig.class})
class RootConfig {}

public class ConditionalFeatureFlag {
    static void run(String label, Properties props) {
        System.out.println("\n=== " + label + " ===");
        props.forEach((k, v) -> System.setProperty((String)k, (String)v));
        var ctx = new AnnotationConfigApplicationContext(RootConfig.class);
        System.out.println("searchService:     " + ctx.containsBean("searchService"));
        System.out.println("recommendationEngine: " + ctx.containsBean("engine"));
        if (ctx.containsBean("searchService"))
            System.out.println(ctx.getBean(SearchService.class).search("spring"));
        if (ctx.containsBean("engine"))
            System.out.println(ctx.getBean(RecommendationEngine.class).recommend("alice"));
        ctx.close();
        props.keySet().forEach(k -> System.clearProperty((String)k));
    }

    public static void main(String[] args) {
        run("no features", new Properties());

        Properties p1 = new Properties();
        p1.put("feature.search", "enabled");
        run("search only", p1);

        Properties p2 = new Properties();
        p2.put("feature.search", "enabled");
        p2.put("feature.recommendations", "enabled");
        run("both features", p2);
    }
}
```

How to run: `java ConditionalFeatureFlag.java`

`@EnableIfProperty` is a custom meta-annotation built on `@Conditional`. Applying it to `@Configuration` classes makes those classes active only when the specified property has the expected value — a clean feature-flag pattern.

## 6. Walkthrough

Execution for Level 3 "both features" run:

1. **`AnnotationConfigApplicationContext(RootConfig.class)` created** — `@Import({SearchConfig.class, RecommendationConfig.class})` adds both to the processing queue.
2. **`SearchConfig` evaluated** — `@EnableIfProperty(property="feature.search", havingValue="enabled")` → `PropertyEnabledCondition.matches()` → reads `feature.search=enabled` → `true` → process `SearchConfig`.
3. **`searchService()` registered** — `new SearchService()`.
4. **`RecommendationConfig` evaluated** — `feature.recommendations=enabled` → `true` → process.
5. **`engine()` registered** — `new RecommendationEngine()`.
6. **`searchService` and `engine` both present** → both operate normally.

Expected output for "both features":
```
[PropertyEnabledCondition] feature.search=enabled (expected=enabled) → true
[PropertyEnabledCondition] feature.recommendations=enabled (expected=enabled) → true
searchService:     true
recommendationEngine: true
[Search] results for: spring
[Recs] items for: alice
```

## 7. Gotchas & takeaways

> `@Conditional` is evaluated at `BeanDefinition` registration time, not at context refresh or bean instantiation. This means the condition's `ConditionContext.getBeanFactory()` may not yet have all beans registered — only those processed before the current class. Do not rely on `containsBeanDefinition` returning `true` for beans declared later in the processing order.

> `Condition` implementations must have a **public no-arg constructor**. Spring instantiates them via reflection. Using lambda syntax (`@Conditional(ctx -> ...)`) is not supported — you must implement the interface in a named class.

- `@Conditional` on a class applies to the whole config (including its `@Bean` methods). `@Conditional` on a `@Bean` method applies to just that method.
- Spring Boot's `@ConditionalOnMissingBean` is the most commonly needed pattern: register a default bean unless the user has provided their own.
- Multiple `@Conditional` annotations on the same element are ANDed — all conditions must pass.
- `@Profile("prod")` is exactly `@Conditional(ProfileCondition.class)` — understanding `@Conditional` lets you see through all `@ConditionalOn*` annotations.
