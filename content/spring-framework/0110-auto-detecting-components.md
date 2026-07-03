---
card: spring-framework
gi: 110
slug: auto-detecting-components
title: Auto-detecting components
---

## 1. What it is

**Auto-detecting components** is the process by which Spring's `ClassPathBeanDefinitionScanner` walks the classpath, finds classes annotated with `@Component` or its stereotypes, and registers them as `BeanDefinition`s — all without any explicit bean declaration. It is the operational result of `@ComponentScan` doing its job.

This topic focuses on *what happens* during scanning: how Spring identifies candidates, what metadata it reads, and how it turns a class file into a managed bean.

## 2. Why & when

Understanding the mechanics matters when:

- You add a `@Service` class and it doesn't appear in the context — diagnosing why requires knowing how scanning works.
- You have duplicate beans unexpectedly — often caused by scanning the same package from two different `@ComponentScan` declarations.
- You're writing a library that needs to control which of its classes Spring auto-detects in consuming apps.
- You use Spring's scanning APIs programmatically (`ClassPathBeanDefinitionScanner`) in framework code.

## 3. Core concept

The scan lifecycle for each `.class` file in the target packages:

1. **MetadataReader** opens the `.class` file using ASM (no class loading), reads class name, supertype, interfaces, and annotation metadata.
2. **Filter evaluation** — default filters check for `@Component` (or any meta-annotation chain leading to `@Component`). Custom filters add/remove candidates.
3. **Candidate check** — a class passes if it's concrete (not abstract, not an interface), or is a `@Configuration` class, or explicitly allowed by a filter.
4. **`BeanDefinition` creation** — a `ScannedGenericBeanDefinition` is created with scope, lazy flags, and all annotation metadata.
5. **Naming** — a `BeanNameGenerator` assigns a name (default: class name, first letter lower-cased, or the `value` attribute of the stereotype).
6. **Post-processing** — `@Scope`, `@Lazy`, `@DependsOn`, `@Primary`, `@Role`, `@Description` annotations on the class are applied to the `BeanDefinition`.
7. **Registration** — the `BeanDefinition` is stored in the factory's registry.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Steps -->
  <rect x="10"  y="70" width="95" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="57" y="92"  fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">1. Read .class</text>
  <text x="57" y="106" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">ASM (no load)</text>

  <rect x="120" y="70" width="95" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="167" y="92"  fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">2. Filter check</text>
  <text x="167" y="106" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Component?</text>

  <rect x="230" y="70" width="95" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="277" y="92"  fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">3. Concrete?</text>
  <text x="277" y="106" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">not abstract</text>

  <rect x="340" y="70" width="105" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="392" y="92"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">4. BeanDefinition</text>
  <text x="392" y="106" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">ScannedGenericBD</text>

  <rect x="460" y="70" width="95" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="507" y="92"  fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">5. Naming</text>
  <text x="507" y="106" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">BeanNameGen</text>

  <rect x="570" y="70" width="120" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="630" y="92"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">6. Register</text>
  <text x="630" y="106" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">factory registry</text>

  <line x1="107" y1="95" x2="117" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a110)"/>
  <line x1="217" y1="95" x2="227" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a110)"/>
  <line x1="327" y1="95" x2="337" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a110)"/>
  <line x1="447" y1="95" x2="457" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a110)"/>
  <line x1="557" y1="95" x2="567" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b110)"/>
  <defs>
    <marker id="a110" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b110" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="180" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ASM bytecode scan → filter → BeanDefinition creation → naming → registry</text>
</svg>

Auto-detection is a six-step pipeline from `.class` file to registered `BeanDefinition`.

## 5. Runnable example

### Level 1 — Basic

Show what Spring auto-detects and what it skips (abstract class, interface, un-annotated class).

```java
// AutoDetectBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.Arrays;

// Detected: concrete class + @Component
@Component class ConcreteBean   { public String name() { return "ConcreteBean";   } }

// Detected: concrete class + @Service (meta @Component)
@Service  class ServiceBean     { public String name() { return "ServiceBean";     } }

// NOT detected: abstract class (even with @Component, Spring rejects abstracts by default)
@Component abstract class AbstractBean { public abstract String name(); }

// NOT detected: no stereotype
class PlainClass { public String name() { return "PlainClass"; } }

// NOT detected: interface
@Component interface MarkerInterface {}

@Configuration
@ComponentScan(basePackageClasses = AutoDetectBasic.class)
class DetectCfg {}

public class AutoDetectBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DetectCfg.class);

        System.out.println("ConcreteBean:   " + ctx.containsBean("concreteBean"));    // true
        System.out.println("ServiceBean:    " + ctx.containsBean("serviceBean"));     // true
        System.out.println("AbstractBean:   " + ctx.containsBean("abstractBean"));    // false
        System.out.println("PlainClass:     " + ctx.containsBean("plainClass"));      // false
        System.out.println("MarkerInterface:" + ctx.containsBean("markerInterface")); // false

        System.out.println("\nAll component beans:");
        Arrays.stream(ctx.getBeanNamesForAnnotation(Component.class))
              .sorted()
              .forEach(n -> System.out.println("  " + n));
        ctx.close();
    }
}
```

How to run: `java AutoDetectBasic.java`

Abstract classes and interfaces with `@Component` are silently skipped. Plain classes without a stereotype are never even considered. Only concrete, annotated classes are detected.

### Level 2 — Intermediate

Use `ClassPathBeanDefinitionScanner` directly (the API that backs `@ComponentScan`) to scan programmatically and inspect what was registered.

```java
// AutoDetectProgrammatic.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service class Alpha   { public String id() { return "alpha";   } }
@Service class Beta    { public String id() { return "beta";    } }
@Repository class Gamma { public String id() { return "gamma"; } }

public class AutoDetectProgrammatic {
    public static void main(String[] args) {
        // Build a raw BeanFactory and run the scanner manually
        var factory  = new DefaultListableBeanFactory();
        var scanner  = new ClassPathBeanDefinitionScanner(factory);

        // Scan the package of this class
        int count = scanner.scan(AutoDetectProgrammatic.class.getPackageName());
        System.out.println("Scanned and registered: " + count + " bean definitions");

        // Inspect registered definitions
        for (String name : factory.getBeanDefinitionNames()) {
            var bd = factory.getBeanDefinition(name);
            System.out.printf("  %-25s scope=%-12s lazy=%s%n",
                name, bd.getScope().isEmpty() ? "singleton" : bd.getScope(), bd.isLazyInit());
        }

        // Retrieve a bean
        System.out.println("\nalpha.id() = " + factory.getBean(Alpha.class).id());
        System.out.println("gamma.id() = " + factory.getBean(Gamma.class).id());
    }
}
```

How to run: `java AutoDetectProgrammatic.java`

`ClassPathBeanDefinitionScanner` is the actual class that powers `@ComponentScan`. Calling `.scan(packageName)` returns the count of registered definitions and populates the factory. This is what Spring does internally — but exposed here for inspection.

### Level 3 — Advanced

Observe the full BeanDefinition metadata that auto-detection produces: scope, role, annotations, lazy, primary flags.

```java
// AutoDetectMetadata.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.config.*;
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component
@Scope("prototype")
@Lazy
@Primary
@Description("The main order processor for the fulfillment pipeline")
class OrderProcessor {
    @Autowired private NotificationSender sender;

    public void process(int orderId) {
        System.out.println("[OrderProcessor] processing order " + orderId);
        sender.notify("Order " + orderId + " processed");
    }
}

@Component
@Scope("singleton")
class NotificationSender {
    public void notify(String msg) { System.out.println("[Notifier] " + msg); }
}

@Configuration
@ComponentScan(basePackageClasses = AutoDetectMetadata.class)
class MetaCfg {}

public class AutoDetectMetadata {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MetaCfg.class);

        // Inspect the BeanDefinition metadata Spring created during scanning
        var bdf = (DefaultListableBeanFactory) ctx.getBeanFactory();

        System.out.println("=== OrderProcessor BeanDefinition ===");
        var bd = bdf.getBeanDefinition("orderProcessor");
        System.out.println("scope:       " + bd.getScope());
        System.out.println("lazy:        " + bd.isLazyInit());
        System.out.println("primary:     " + bd.isPrimary());
        System.out.println("description: " + bd.getDescription());
        System.out.println("class:       " + bd.getBeanClassName());

        System.out.println("\n=== NotificationSender BeanDefinition ===");
        var bd2 = bdf.getBeanDefinition("notificationSender");
        System.out.println("scope:       " + (bd2.getScope().isEmpty() ? "singleton" : bd2.getScope()));
        System.out.println("lazy:        " + bd2.isLazyInit());

        // Retrieve prototype — every getBean call creates a new instance
        System.out.println("\nCreating prototype instances:");
        var p1 = ctx.getBean(OrderProcessor.class);
        var p2 = ctx.getBean(OrderProcessor.class);
        System.out.println("Same instance? " + (p1 == p2));   // false — prototype
        p1.process(101);

        ctx.close();
    }
}
```

How to run: `java AutoDetectMetadata.java`

`@Scope`, `@Lazy`, `@Primary`, and `@Description` are all read from the class file during scanning and baked into the `BeanDefinition` at that point. Inspecting `bd` shows exactly what the scanner captured.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **`AnnotationConfigApplicationContext` created** — triggers `ClassPathBeanDefinitionScanner.scan(...)`.
2. **Scanner opens `OrderProcessor.class`** (via ASM, no JVM class loading). Reads:
   - Annotation `@Component` → candidate.
   - Annotation `@Scope("prototype")` → scope attribute.
   - Annotation `@Lazy` → lazyInit = true.
   - Annotation `@Primary` → primary = true.
   - Annotation `@Description(...)` → description string.
3. **`ScannedGenericBeanDefinition` created** for `OrderProcessor` with all captured metadata.
4. **Same for `NotificationSender`** — scope = `""` (treated as singleton), lazy = false.
5. **Both BeanDefinitions registered** in the factory registry.
6. **BeanDefinition inspection** in `main` — prints the raw metadata values captured in step 2-4.
7. **Two `ctx.getBean(OrderProcessor.class)` calls** — scope is `prototype`, so both calls construct a new `OrderProcessor`. Same `NotificationSender` singleton injected into both.
8. **`p1 == p2`** → `false` (different prototype instances).
9. **`p1.process(101)`** — prints the processing log via the shared `NotificationSender`.

Expected output:
```
=== OrderProcessor BeanDefinition ===
scope:       prototype
lazy:        true
primary:     true
description: The main order processor for the fulfillment pipeline
class:       OrderProcessor

=== NotificationSender BeanDefinition ===
scope:       singleton
lazy:        false

Creating prototype instances:
Same instance? false
[OrderProcessor] processing order 101
[Notifier] Order 101 processed
```

## 7. Gotchas & takeaways

> Spring uses **ASM bytecode reading**, not `Class.forName()`, during scanning. This means a class file in the scan path does NOT get loaded into the JVM unless it passes all filters and gets registered. This is critical for large classpaths — you don't pay for loading unused classes.

> If a `@Component` class is in the scan path but is abstract, Spring silently skips it. No warning, no exception. This surprises developers who expect Spring to register an abstract base class and use a subclass — it won't; annotate the concrete subclass instead.

- Auto-detection respects `@Scope`, `@Lazy`, `@Primary`, `@DependsOn`, `@Description`, and `@Role` — these are captured at scan time and stored in the `BeanDefinition`.
- Scanning a package twice (e.g., from two `@ComponentScan` on two `@Configuration` classes) may register duplicate beans — Spring detects and merges exact duplicates but warns on conflicts.
- The scanner produces `ScannedGenericBeanDefinition` objects; beans declared via `@Bean` methods produce `ConfigurationClassBeanDefinition` objects — both are `BeanDefinition`s but carry slightly different metadata.
- Use `ctx.getBeanDefinitionNames()` and `ctx.getBeanDefinition(name)` to inspect what was auto-detected when debugging registration issues.
