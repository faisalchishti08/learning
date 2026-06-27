---
card: spring-boot
gi: 35
slug: component-scanning-rules
title: Component scanning rules
---

## 1. What it is

**Component scanning** is Spring's mechanism for automatically detecting and registering beans without requiring explicit bean definitions. When the Spring container starts, it scans a set of packages looking for classes annotated with stereotype annotations. Any class it finds gets registered as a bean.

The stereotype annotations Spring recognises by default:

| Annotation | Intended role |
|---|---|
| `@Component` | Generic bean |
| `@Service` | Business logic layer |
| `@Repository` | Data access layer |
| `@Controller` / `@RestController` | Web layer |
| `@Configuration` | Configuration class |

All of these are meta-annotated with `@Component`, so the scanner treats them identically — the distinction is purely semantic/documentary.

## 2. Why & when

Without component scanning you would have to register every bean manually in XML or `@Configuration` classes. For a small app that is fine; for a large app with hundreds of beans it becomes unmanageable.

Component scanning gives you:
- **Zero-boilerplate registration** — add the annotation, bean appears automatically.
- **Convention over configuration** — the default scan base covers the whole project if you follow the standard package layout.
- **Consistent discovery** — the rules are uniform; no need to remember which file registers which class.

Understand the rules because when scanning goes wrong (bean not found, bean registered twice, wrong bean injected) the rules are what you debug against.

## 3. Core concept

Think of component scanning as a librarian walking the shelves. The librarian starts at a **base package** (the shelf section), opens every book (`.class` file), reads its cover (annotations), and cards any book with the right stamp (`@Component` or derivative). Cards go into a single catalogue (the application context).

The rules that govern this walk:

1. **Scan base** — defaults to the package of the `@SpringBootApplication` class and all sub-packages.
2. **Include filters** — by default, anything with a `@Component`-derived annotation is included.
3. **Exclude filters** — classes matching an exclude filter are skipped even if they have `@Component`.
4. **Scope** — each scanned bean gets `singleton` scope by default; override with `@Scope("prototype")` etc.
5. **Naming** — the bean name defaults to the camel-case class name (`CustomerService` → `customerService`); override with `@Component("myName")`.
6. **Ordering** — scan order is filesystem/JVM order; don't rely on it for bean creation order. Use `@DependsOn` if order matters.

Custom scan bases and filters are set on `@ComponentScan`:

```java
@ComponentScan(
    basePackages = "com.example",
    includeFilters = @Filter(type = FilterType.ANNOTATION, classes = MyCustomAnnotation.class),
    excludeFilters = @Filter(type = FilterType.ASSIGNABLE_TYPE, classes = DevOnlyBean.class)
)
```

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Component scanning walking packages and registering annotated classes into the context">
  <!-- Package tree on left -->
  <rect x="20" y="20" width="240" height="240" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="44" fill="#8b949e" font-size="12" font-family="monospace" text-anchor="middle">com.example.myapp/</text>

  <rect x="36" y="56" width="210" height="28" rx="5" fill="#6db33f" fill-opacity="0.15" stroke="#6db33f" stroke-width="1"/>
  <text x="50" y="75" fill="#6db33f" font-size="11" font-family="monospace">@Service CustomerService ✅</text>

  <rect x="36" y="92" width="210" height="28" rx="5" fill="#6db33f" fill-opacity="0.15" stroke="#6db33f" stroke-width="1"/>
  <text x="50" y="111" fill="#6db33f" font-size="11" font-family="monospace">@Repository CustomerRepo ✅</text>

  <rect x="36" y="128" width="210" height="28" rx="5" fill="#6db33f" fill-opacity="0.15" stroke="#6db33f" stroke-width="1"/>
  <text x="50" y="147" fill="#6db33f" font-size="11" font-family="monospace">@RestController OrderCtrl ✅</text>

  <rect x="36" y="164" width="210" height="28" rx="5" fill="#2d3748" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="50" y="183" fill="#8b949e" font-size="11" font-family="monospace">PlainJavaClass ❌ (no ann.)</text>

  <rect x="36" y="200" width="210" height="28" rx="5" fill="#3d2020" stroke="#f85149" stroke-width="1"/>
  <text x="50" y="219" fill="#f85149" font-size="11" font-family="monospace">@Service ExcludedBean ⛔</text>
  <text x="50" y="234" fill="#8b949e" font-size="10" font-family="monospace">  (matched excludeFilter)</text>

  <!-- Arrow -->
  <line x1="260" y1="140" x2="340" y2="140" stroke="#6db33f" stroke-width="2.5" marker-end="url(#scan)"/>
  <text x="300" y="130" fill="#6db33f" font-size="11" font-family="sans-serif" text-anchor="middle">scan</text>

  <!-- Context box on right -->
  <rect x="340" y="60" width="290" height="160" rx="8" fill="#16202e" stroke="#6db33f" stroke-width="2"/>
  <text x="485" y="84" fill="#6db33f" font-size="12" font-family="sans-serif" font-weight="bold" text-anchor="middle">Application Context</text>
  <text x="360" y="110" fill="#e6edf3" font-size="11" font-family="monospace">customerService  (singleton)</text>
  <text x="360" y="132" fill="#e6edf3" font-size="11" font-family="monospace">customerRepo     (singleton)</text>
  <text x="360" y="154" fill="#e6edf3" font-size="11" font-family="monospace">orderCtrl        (singleton)</text>
  <text x="360" y="196" fill="#8b949e" font-size="10" font-family="sans-serif">3 beans registered; 2 skipped</text>

  <defs>
    <marker id="scan" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto">
      <path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

The scanner walks every class in the base package tree, applies include/exclude filters, and registers matching classes as beans.

## 5. Runnable example

```java
// ComponentScanDemo.java
// How to run: java ComponentScanDemo.java  (JDK 17+)
// Simulates Spring component scanning rules: base package check,
// include filter (annotation present), exclude filter (type match).

import java.lang.annotation.*;
import java.util.*;

// ── simulated annotations ─────────────────────────────────────────
@Retention(RetentionPolicy.RUNTIME) @interface Component  { String value() default ""; }
@Retention(RetentionPolicy.RUNTIME) @interface Service    {}
@Retention(RetentionPolicy.RUNTIME) @interface Repository {}

// ── candidate classes ─────────────────────────────────────────────
@Service    class CustomerService  {}
@Repository class CustomerRepo     {}
@Service    class ExcludedService  {}   // will be excluded by filter
            class PlainJavaClass   {}   // no annotation → skipped

public class ComponentScanDemo {

    record BeanCandidate(String pkg, Class<?> cls) {}

    public static void main(String[] args) {
        String basePackage = "com.example.myapp";

        // Simulate classes "found on classpath" with their declared packages
        List<BeanCandidate> classpathClasses = List.of(
            new BeanCandidate("com.example.myapp",  CustomerService.class),
            new BeanCandidate("com.example.myapp",  CustomerRepo.class),
            new BeanCandidate("com.example.myapp",  ExcludedService.class),
            new BeanCandidate("com.example.myapp",  PlainJavaClass.class),
            new BeanCandidate("com.example.other",  String.class)   // outside base pkg
        );

        // Exclude filter: skip ExcludedService (by type)
        Set<Class<?>> excluded = Set.of(ExcludedService.class);

        Map<String, Class<?>> context = new LinkedHashMap<>();

        System.out.println("Base package: " + basePackage);
        System.out.println("Exclude filter: " + ExcludedService.class.getSimpleName());
        System.out.println("─────────────────────────────────────────────────");

        for (BeanCandidate bc : classpathClasses) {
            String verdict;

            if (!bc.pkg().startsWith(basePackage)) {
                verdict = "SKIP — outside base package";
            } else if (excluded.contains(bc.cls())) {
                verdict = "SKIP — matched excludeFilter";
            } else if (!hasComponentAnnotation(bc.cls())) {
                verdict = "SKIP — no @Component-derived annotation";
            } else {
                String beanName = toBeanName(bc.cls().getSimpleName());
                context.put(beanName, bc.cls());
                verdict = "REGISTERED as '" + beanName + "'";
            }

            System.out.printf("%-35s → %s%n", bc.cls().getSimpleName(), verdict);
        }

        System.out.println("\n=== Registered beans ===");
        context.forEach((name, cls) ->
            System.out.println("  " + name + " → " + cls.getSimpleName()));
    }

    static boolean hasComponentAnnotation(Class<?> cls) {
        return cls.isAnnotationPresent(Component.class)
            || cls.isAnnotationPresent(Service.class)
            || cls.isAnnotationPresent(Repository.class);
    }

    static String toBeanName(String className) {
        return Character.toLowerCase(className.charAt(0)) + className.substring(1);
    }
}
```

**How to run:** `java ComponentScanDemo.java`

Expected output:
```
Base package: com.example.myapp
Exclude filter: ExcludedService
─────────────────────────────────────────────────
CustomerService     → REGISTERED as 'customerService'
CustomerRepo        → REGISTERED as 'customerRepo'
ExcludedService     → SKIP — matched excludeFilter
PlainJavaClass      → SKIP — no @Component-derived annotation
String              → SKIP — outside base package

=== Registered beans ===
  customerService → CustomerService
  customerRepo → CustomerRepo
```

## 6. Walkthrough

- `basePackage = "com.example.myapp"` mirrors the root package of `@SpringBootApplication`. The `startsWith` check implements the rule that any sub-package qualifies.
- `excluded = Set.of(ExcludedService.class)` simulates `excludeFilters = @Filter(ASSIGNABLE_TYPE, ExcludedService.class)`. Even though `ExcludedService` has `@Service`, it is skipped before the annotation check.
- `hasComponentAnnotation` mimics Spring's meta-annotation traversal: in reality Spring checks if `@Service` (or any present annotation) is itself annotated with `@Component`, going up the annotation chain. The demo flattens this to a direct check for clarity.
- `toBeanName` replicates `AnnotationBeanNameGenerator`'s default: camel-case the class name. A custom name set via `@Component("myBean")` overrides this.
- The `String` from `com.example.other` is skipped by the package check — exactly what happens when a third-party library class ends up on the classpath.

## 7. Gotchas & takeaways

> `@SpringBootApplication` already includes `@ComponentScan` with the scan base set to its own package. Adding a separate bare `@ComponentScan` (no `basePackages`) on the same class **replaces** that default scan and may reset the base package — a subtle way to break scanning silently.

> Classes in the **default package** (no `package` statement) are scanned only if the scan base is explicitly set to `""`. Spring Boot discourages the default package precisely because this sweep is dangerously broad on a large classpath.

- Default bean name = lower-camel-case of the class name; override with `@Component("name")`.
- `excludeFilters` takes precedence over `includeFilters` — an excluded class is never registered, even if explicitly included.
- `@ComponentScan` can accept multiple base packages: `basePackages = {"com.example.a", "com.example.b"}`.
- Scanning is done once at startup; it does not re-scan the classpath at runtime.
- `@ComponentScan.Filter` types: `ANNOTATION`, `ASSIGNABLE_TYPE`, `ASPECTJ`, `REGEX`, `CUSTOM` — `ANNOTATION` and `ASSIGNABLE_TYPE` cover 95% of real use cases.
- Use `@SpringBootApplication(scanBasePackages = "com.example")` as a shorthand instead of a separate `@ComponentScan`.
