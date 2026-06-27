---
card: spring-boot
gi: 16
slug: the-springbootapplication-annotation
title: The @SpringBootApplication annotation
---

## 1. What it is

`@SpringBootApplication` is a single convenience annotation that composes three distinct Spring annotations:

```java
@SpringBootConfiguration   // = @Configuration: this class declares beans
@EnableAutoConfiguration   // triggers Spring Boot's auto-configuration
@ComponentScan             // scans the package (and sub-packages) for @Component classes
public @interface SpringBootApplication { ... }
```

Placing `@SpringBootApplication` on your main class activates all three effects at once. It is the equivalent of writing all three annotations explicitly — which you're free to do if you need fine-grained control over any of them.

## 2. Why & when

Without `@SpringBootApplication`, you'd need three separate annotations on your main class:

```java
@SpringBootConfiguration
@EnableAutoConfiguration
@ComponentScan(basePackages = "com.example")
public class App { ... }
```

That's not wrong — it's just verbose for the common case. `@SpringBootApplication` exists to reduce that to one line for the 99% case.

Know when each component matters:
- **`@SpringBootConfiguration`** — needed so the class can declare `@Bean` methods. You rarely need to think about it explicitly.
- **`@EnableAutoConfiguration`** — the heart of Spring Boot. Remove it and auto-configuration stops; embedded Tomcat won't start, no DataSource is created, nothing is wired automatically.
- **`@ComponentScan`** — without it, Spring won't discover your `@Service`, `@Repository`, or `@Controller` classes. By default it scans the package of the annotated class and all sub-packages.

## 3. Core concept

The scanning behaviour is the most important thing to understand:

**`@ComponentScan` scans from the annotated class's package downward.** If your `App` class is in `com.example`, scanning covers `com.example.*` — all sub-packages. If `App` is in the default package (no `package` statement), scanning covers the entire classpath — extremely slow and likely to pick up third-party internals. **Always put your main class in a named base package.**

`@SpringBootApplication` attributes let you customise each composed annotation:

```java
@SpringBootApplication(
    exclude = { DataSourceAutoConfiguration.class },  // skip auto-config
    scanBasePackages = { "com.example.api", "com.example.core" }  // explicit scan roots
)
```

Common attributes:

| Attribute | Controls | Default |
|---|---|---|
| `exclude` | Auto-configuration classes to skip | none |
| `excludeName` | Same, by class name string | none |
| `scanBasePackages` | Which packages to scan | annotated class's package |
| `scanBasePackageClasses` | Scan packages of these classes (type-safe alternative to `scanBasePackages`) | none |

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="image" aria-label="@SpringBootApplication decomposed into its three component annotations and what each one activates">
  <!-- Central annotation box -->
  <rect x="220" y="20" width="220" height="44" rx="8" fill="#6db33f" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="47" fill="#1c2430" font-size="14" font-weight="bold" text-anchor="middle" font-family="sans-serif">@SpringBootApplication</text>

  <!-- Lines to three children -->
  <line x1="110" y1="100" x2="330" y2="64" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="330" y1="100" x2="330" y2="64" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="550" y1="100" x2="330" y2="64" stroke="#8b949e" stroke-width="1.5"/>

  <!-- @SpringBootConfiguration -->
  <rect x="20" y="100" width="180" height="56" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="122" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">@SpringBootConfiguration</text>
  <text x="110" y="142" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">= @Configuration</text>
  <text x="110" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">class can declare @Bean methods</text>

  <!-- @EnableAutoConfiguration -->
  <rect x="220" y="100" width="220" height="56" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="122" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">@EnableAutoConfiguration</text>
  <text x="330" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">triggers auto-config scan</text>
  <text x="330" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the engine of Spring Boot</text>

  <!-- @ComponentScan -->
  <rect x="460" y="100" width="180" height="56" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="122" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">@ComponentScan</text>
  <text x="550" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">finds @Component classes</text>
  <text x="550" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scans annotated package + children</text>

  <!-- Effect boxes -->
  <rect x="20" y="180" width="180" height="44" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="198" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">App.class can have:</text>
  <text x="110" y="214" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Bean DataSource() {...}</text>

  <rect x="220" y="180" width="220" height="44" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="198" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Tomcat starts, JPA wires,</text>
  <text x="330" y="214" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Jackson configured…</text>

  <rect x="460" y="180" width="180" height="44" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="550" y="198" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Service, @Repository,</text>
  <text x="550" y="214" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Controller auto-detected</text>
</svg>

One annotation composes three; `@EnableAutoConfiguration` is the distinctly Spring Boot piece — the other two exist in Spring Framework too.

## 5. Runnable example

```java
// File: AnnotationDecomposer.java
// Demonstrates what @SpringBootApplication expands to, using reflection on its meta-annotations.
// Run: java AnnotationDecomposer.java
// Note: spring-boot JARs not on classpath — simulates the decomposition conceptually.

import java.lang.annotation.*;
import java.util.*;

public class AnnotationDecomposer {

    // Simulate the three component annotations
    @Retention(RetentionPolicy.RUNTIME) @interface Configuration {}
    @Retention(RetentionPolicy.RUNTIME) @interface EnableAutoConfiguration {
        Class<?>[] exclude() default {};
    }
    @Retention(RetentionPolicy.RUNTIME) @interface ComponentScan {
        String[] basePackages() default {};
    }

    // Simulate @SpringBootApplication as a composed annotation
    @Retention(RetentionPolicy.RUNTIME)
    @Configuration
    @EnableAutoConfiguration
    @ComponentScan
    @interface SpringBootApplication {
        Class<?>[] exclude() default {};
        String[] scanBasePackages() default {};
    }

    // A minimal main class using the composed annotation
    @SpringBootApplication(
        exclude = {},                                // no auto-config to skip
        scanBasePackages = {"com.example"}          // explicit scan root
    )
    static class App {
        public static void main(String[] args) {
            System.out.println("Bootstrapping...");
        }
    }

    public static void main(String[] args) {
        System.out.println("@SpringBootApplication on App class decomposes to:");
        System.out.println();

        var sba = App.class.getAnnotation(SpringBootApplication.class);
        System.out.println("Direct: @SpringBootApplication");
        System.out.println("  exclude         = " + Arrays.toString(sba.exclude()));
        System.out.println("  scanBasePackages = " + Arrays.toString(sba.scanBasePackages()));
        System.out.println();

        System.out.println("Meta-annotations (what @SpringBootApplication is annotated with):");
        for (var ann : SpringBootApplication.class.getAnnotations()) {
            String name = ann.annotationType().getSimpleName();
            if (!name.equals("Retention") && !name.equals("Target")) {
                System.out.println("  @" + name);
            }
        }

        System.out.println();
        System.out.println("Effect summary:");
        System.out.println("  @Configuration         → App can declare @Bean methods");
        System.out.println("  @EnableAutoConfiguration → auto-config fires on classpath detection");
        System.out.println("  @ComponentScan          → scans com.example.** for @Component classes");
    }
}
```

**How to run:** `java AnnotationDecomposer.java` (JDK 17+, no dependencies needed).

Expected output:
```
@SpringBootApplication on App class decomposes to:

Direct: @SpringBootApplication
  exclude          = []
  scanBasePackages = [com.example]

Meta-annotations (what @SpringBootApplication is annotated with):
  @Configuration
  @EnableAutoConfiguration
  @ComponentScan

Effect summary:
  @Configuration          → App can declare @Bean methods
  @EnableAutoConfiguration → auto-config fires on classpath detection
  @ComponentScan           → scans com.example.** for @Component classes
```

## 6. Walkthrough

- **`@Retention(RetentionPolicy.RUNTIME)`** — annotations only exist at runtime if this is set. Without it, `getAnnotation(...)` returns null. Spring Boot's own annotations all have `RUNTIME` retention for exactly this reason — Spring reads them via reflection when the JVM starts.
- **`@interface SpringBootApplication`** — declares a custom composed annotation. Spring's `@SpringBootApplication` works identically: it's an `@interface` annotated with `@Configuration`, `@EnableAutoConfiguration`, and `@ComponentScan`.
- **`App.class.getAnnotation(SpringBootApplication.class)`** — retrieves the annotation instance from the class object. From it we can read the attribute values (`exclude`, `scanBasePackages`).
- **`SpringBootApplication.class.getAnnotations()`** — reads the meta-annotations on the annotation type itself. This reveals the three composed annotations.
- **Filter out `Retention` and `Target`** — every annotation automatically carries these two meta-annotations; filtering them keeps the output clean.

## 7. Gotchas & takeaways

> **Put your main class in the top-level package of your application.** If `App` is in `com.example.demo`, component scanning covers `com.example.demo` and all sub-packages. If you later move a service to `com.example.common`, it's outside the scan root and won't be found. Either move the main class up one level or use `scanBasePackages = {"com.example"}`.

> **`@SpringBootApplication` should appear exactly once.** Using it on multiple classes in the same application causes multiple component scans and multiple `@EnableAutoConfiguration` triggers — unexpected beans appear, and startup is slower. One main class, one `@SpringBootApplication`.

- `@SpringBootApplication = @SpringBootConfiguration + @EnableAutoConfiguration + @ComponentScan`.
- `@EnableAutoConfiguration` is the uniquely Spring Boot part; the other two are Spring Framework annotations.
- Default scan root = the package containing the annotated class. Always use a named base package.
- Use `exclude = DataSourceAutoConfiguration.class` to skip specific auto-configurations without touching `application.properties`.
- You can replace `@SpringBootApplication` with the three explicit annotations if you need separate control over each.
