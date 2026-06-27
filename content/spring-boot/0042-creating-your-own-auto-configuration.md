---
card: spring-boot
gi: 42
slug: creating-your-own-auto-configuration
title: Creating your own auto-configuration
---

## 1. What it is

**Creating your own auto-configuration** means writing a `@AutoConfiguration` class (Spring Boot 2.7+) or a `@Configuration` class registered in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` so that Spring Boot discovers and applies it automatically when your JAR is on the classpath.

Auto-configurations you write work identically to Spring Boot's built-in ones: they define `@Bean` methods guarded by `@Conditional` annotations, and Spring Boot applies them after processing user configuration.

Typical use cases:
- Publishing a shared library used by multiple Spring Boot apps in your organisation.
- Building a reusable Spring Boot starter (open-source or internal).
- Writing a plugin that auto-wires itself into any Spring Boot app that includes your JAR.

## 2. Why & when

Without auto-configuration, every consumer of your library must manually add `@Import(YourLibraryConfig.class)` or copy-paste bean definitions. Auto-configuration moves that burden to you (the library author) and gives consumers a zero-configuration integration.

Write your own auto-configuration when:
- Your library provides a service that most consumers will want to use with sensible defaults.
- You want to respect user overrides without forcing consumers to annotate anything.
- You're building a starter module (next tutorial).

Do not auto-configure things that are highly app-specific or where sensible defaults don't exist.

## 3. Core concept

An auto-configuration class is just a `@Configuration` class that Spring Boot discovers through the `AutoConfiguration.imports` file. The pattern to follow:

1. Write a class annotated `@AutoConfiguration` (or `@Configuration` in older versions).
2. Add `@ConditionalOnClass` to guard against missing dependencies.
3. Add `@ConditionalOnMissingBean` on `@Bean` methods so users can override.
4. Add the class name to `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`.
5. Package everything in a JAR (the "autoconfigure" module).

The rule of thumb:
- `@AutoConfiguration` (class level): "apply this whole config only if X class is on the classpath."
- `@ConditionalOnMissingBean` (method level): "provide this bean only if no other bean of this type exists."

Combined, these two annotations make auto-configuration non-invasive: it works silently when present and backs off when the user customises anything.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Custom auto-configuration JAR structure and discovery flow">
  <!-- JAR structure -->
  <rect x="20" y="20" width="280" height="220" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="160" y="46" fill="#6db33f" font-size="12" font-family="monospace" font-weight="bold" text-anchor="middle">my-lib-autoconfigure.jar</text>

  <rect x="36" y="58" width="248" height="44" rx="5" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="77" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">com.mylib.MyLibAutoConfiguration</text>
  <text x="160" y="94" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@AutoConfiguration + @ConditionalOnClass</text>

  <rect x="36" y="112" width="248" height="44" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="130" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">MyLibService.java</text>
  <text x="160" y="147" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">@Bean @ConditionalOnMissingBean</text>

  <rect x="36" y="166" width="248" height="58" rx="5" fill="#1a2332" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="183" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">META-INF/spring/</text>
  <text x="160" y="199" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">AutoConfiguration.imports</text>
  <text x="160" y="215" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">com.mylib.MyLibAutoConfiguration</text>

  <!-- Arrow -->
  <line x1="302" y1="140" x2="360" y2="140" stroke="#6db33f" stroke-width="2" marker-end="url(#y1)"/>
  <text x="332" y="130" fill="#6db33f" font-size="10" font-family="sans-serif" text-anchor="middle">auto-</text>
  <text x="332" y="144" fill="#6db33f" font-size="10" font-family="sans-serif" text-anchor="middle">discovers</text>

  <!-- Consumer app -->
  <rect x="362" y="60" width="270" height="160" rx="8" fill="#16202e" stroke="#6db33f" stroke-width="1.5"/>
  <text x="497" y="84" fill="#6db33f" font-size="12" font-family="monospace" text-anchor="middle">Consumer App</text>
  <text x="497" y="108" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">pom.xml adds my-lib-autoconfigure</text>
  <text x="497" y="132" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">No extra annotation needed</text>
  <text x="497" y="156" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">myLibService bean → injected</text>
  <text x="497" y="180" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">override: define own MyLibService</text>
  <text x="497" y="196" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">→ auto-config backs off</text>

  <defs>
    <marker id="y1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

The auto-configuration JAR is self-contained; any app that includes it gets the `myLibService` bean for free, with the ability to override.

## 5. Runnable example

```java
// CustomAutoConfigDemo.java
// How to run: java CustomAutoConfigDemo.java  (JDK 17+)
// Simulates writing and applying a custom auto-configuration class
// including the AutoConfiguration.imports registration and override mechanism.

import java.lang.annotation.*;
import java.util.*;

// ── simulated annotations ─────────────────────────────────────────
@Retention(RetentionPolicy.RUNTIME) @interface AutoConfiguration {}
@Retention(RetentionPolicy.RUNTIME) @interface ConditionalOnClass { String value(); }
@Retention(RetentionPolicy.RUNTIME) @interface ConditionalOnMissingBean {}
@Retention(RetentionPolicy.RUNTIME) @interface Bean {}

// ── the library's service ─────────────────────────────────────────
class GreetingService {
    private final String greeting;
    GreetingService(String greeting) { this.greeting = greeting; }
    String greet(String name) { return greeting + ", " + name + "!"; }
    @Override public String toString() { return "GreetingService(greeting='" + greeting + "')"; }
}

// ── the auto-configuration class (lives in my-lib-autoconfigure.jar) ─
@AutoConfiguration
@ConditionalOnClass("com.example.GreetingService")   // guard: class on classpath
class GreetingAutoConfiguration {
    @Bean
    @ConditionalOnMissingBean                        // back off if user provides own bean
    public GreetingService greetingService() {
        return new GreetingService("Hello");         // sensible default
    }
}

// ── minimal context that applies auto-configurations ──────────────
public class CustomAutoConfigDemo {

    static Map<String, Object> context = new LinkedHashMap<>();
    static Set<String> simulatedClasspath = Set.of("com.example.GreetingService");

    public static void main(String[] args) throws Exception {
        System.out.println("=== Scenario A: no user override (auto-config applies) ===");
        context.clear();
        applyAutoConfig(GreetingAutoConfiguration.class);
        printContext();

        System.out.println("\n=== Scenario B: user provides own GreetingService ===");
        context.clear();
        // User registers a custom bean BEFORE auto-config runs
        context.put("greetingService", new GreetingService("Greetings"));
        System.out.println("User registered: greetingService → " + context.get("greetingService"));
        applyAutoConfig(GreetingAutoConfiguration.class);
        printContext();
    }

    static void applyAutoConfig(Class<?> cfg) throws Exception {
        // Check @ConditionalOnClass
        if (cfg.isAnnotationPresent(ConditionalOnClass.class)) {
            String required = cfg.getAnnotation(ConditionalOnClass.class).value();
            if (!simulatedClasspath.contains(required)) {
                System.out.println("Auto-config skipped: " + required + " not on classpath.");
                return;
            }
        }
        // Process @Bean methods
        for (var method : cfg.getDeclaredMethods()) {
            if (!method.isAnnotationPresent(Bean.class)) continue;
            String beanName = method.getName();
            if (method.isAnnotationPresent(ConditionalOnMissingBean.class)
                    && context.containsKey(beanName)) {
                System.out.println("Auto-config @ConditionalOnMissingBean: '"
                    + beanName + "' already exists → backing off");
                continue;
            }
            Object bean = method.invoke(cfg.getDeclaredConstructor().newInstance());
            context.put(beanName, bean);
            System.out.println("Auto-config registered '" + beanName + "' → " + bean);
        }
    }

    static void printContext() {
        System.out.println("Context: " + context);
    }
}
```

**How to run:** `java CustomAutoConfigDemo.java`

Expected output:
```
=== Scenario A: no user override (auto-config applies) ===
Auto-config registered 'greetingService' → GreetingService(greeting='Hello')
Context: {greetingService=GreetingService(greeting='Hello')}

=== Scenario B: user provides own GreetingService ===
User registered: greetingService → GreetingService(greeting='Greetings')
Auto-config @ConditionalOnMissingBean: 'greetingService' already exists → backing off
Context: {greetingService=GreetingService(greeting='Greetings')}
```

## 6. Walkthrough

- `GreetingAutoConfiguration` is the auto-configuration class. In a real project it goes in a separate `*-autoconfigure` Maven/Gradle module.
- `@ConditionalOnClass("com.example.GreetingService")` is the class-level guard. If the library classes aren't on the classpath, the whole config is skipped.
- `@ConditionalOnMissingBean` on the `greetingService` method lets user apps override the default by defining their own `GreetingService` bean.
- Scenario A: context is empty → auto-config registers `GreetingService("Hello")`.
- Scenario B: user pre-registers `GreetingService("Greetings")` → `@ConditionalOnMissingBean` detects it, backs off, and the user's version is used.
- In a real Spring Boot project, the class name `GreetingAutoConfiguration` would appear in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` for automatic discovery.

## 7. Gotchas & takeaways

> Auto-configuration classes must **not** be in a package that is component-scanned by the consuming application. Put them in the library module's own package under `org.springframework.boot.autoconfigure` or a dedicated `com.mylib.autoconfigure` package. If the class is scanned, it runs as a regular `@Configuration` and the ordering guarantees of auto-configuration no longer apply.

> Always add `@ConditionalOnMissingBean` to every `@Bean` method in an auto-configuration. Forgetting it makes your bean impossible to override without an `exclude` — breaking the consumer's ability to customise your library.

- Use `@AutoConfiguration` (Spring Boot 2.7+) instead of plain `@Configuration` for auto-configuration classes; it carries `@Configuration` plus markers that trigger proper ordering support.
- Register the class in `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` — one fully qualified name per line.
- Keep auto-configurations focused: one auto-configuration class per concern (data source, security, messaging).
- Use `spring-boot-autoconfigure-processor` (annotation processor) to validate imports file at build time.
- Test with `ApplicationContextRunner` (Spring Boot test utility) to assert which beans are registered under various conditions without starting a full application.
