---
card: spring-framework
gi: 111
slug: naming-autodetected-components-beannamegenerator
title: Naming autodetected components (BeanNameGenerator)
---

## 1. What it is

When `@ComponentScan` discovers a class, it needs a bean name. Spring uses a **`BeanNameGenerator`** to derive that name. The default strategy (`AnnotationBeanNameGenerator`) produces the class name with the first letter lower-cased: `OrderService` → `"orderService"`. You can override the strategy globally or per-scan with a custom `BeanNameGenerator`.

## 2. Why & when

The default naming works for most single-module applications. Customise the strategy when:

- **Multiple packages** define classes with the same simple name — default naming collides.
- **Convention** — your team requires a prefix (`"myapp.orderService"`) or suffix (`"orderServiceBean"`).
- **Multi-module apps** — two modules each have a `UserService`; a FQN-based generator avoids conflicts.
- **Legacy integration** — you're wiring Spring into an existing name registry with different conventions.

Spring 6.1+ ships `FullyQualifiedAnnotationBeanNameGenerator` out of the box; for older projects or custom schemes, implement `BeanNameGenerator`.

## 3. Core concept

`BeanNameGenerator` is a single-method interface:

```java
String generateBeanName(BeanDefinition definition, BeanDefinitionRegistry registry);
```

`definition` gives you the class name, annotations, and all scan metadata. `registry` lets you check for name conflicts.

Built-in generators:

| Generator | Strategy |
|---|---|
| `AnnotationBeanNameGenerator` (default) | Stereotype's `value()` attribute; else simple class name, first-letter lower-cased |
| `FullyQualifiedAnnotationBeanNameGenerator` | Fully qualified class name (`com.example.OrderService`) |
| Custom | Whatever logic you implement |

Register a custom generator on `@ComponentScan`:
```java
@ComponentScan(nameGenerator = MyGenerator.class)
```
or pass it to `ClassPathBeanDefinitionScanner`:
```java
scanner.setBeanNameGenerator(new MyGenerator());
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Class -->
  <rect x="10" y="65" width="155" height="54" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="88" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">OrderService.class</text>
  <text x="87" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Service("orders")</text>

  <!-- Generator -->
  <rect x="265" y="65" width="175" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="352" y="88" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">BeanNameGenerator</text>
  <text x="352" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">generateBeanName(bd, reg)</text>

  <!-- Outcomes -->
  <rect x="530" y="30" width="160" height="36" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="610" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">"orders" (value attr)</text>

  <rect x="530" y="80" width="160" height="36" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="610" y="102" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">"orderService" (default)</text>

  <rect x="530" y="130" width="160" height="36" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="610" y="150" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">"com.ex.OrderService" (FQN)</text>

  <line x1="167" y1="92" x2="262" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#a111)"/>
  <line x1="442" y1="78" x2="527" y2="48" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a111)"/>
  <line x1="442" y1="92" x2="527" y2="98" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b111)"/>
  <line x1="442" y1="105" x2="527" y2="148" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c111)"/>
  <defs>
    <marker id="a111" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b111" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c111" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <text x="350" y="168" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Generator picks name from annotation value, class name, or FQN depending on strategy</text>
</svg>

The `BeanNameGenerator` converts a `BeanDefinition` into a string name for the registry.

## 5. Runnable example

### Level 1 — Basic

Default naming: stereotype `value()` attribute overrides the class-name-derived name.

```java
// NamingBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service                      // name = "paymentService" (class name, lower-cased first letter)
class PaymentService {}

@Service("billing")           // name = "billing" (explicit value attribute)
class BillingService {}

@Repository("orders.repo")    // name = "orders.repo" (arbitrary string)
class OrderRepository {}

@Configuration
@ComponentScan(basePackageClasses = NamingBasic.class)
class NamingCfg {}

public class NamingBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(NamingCfg.class);
        System.out.println("paymentService:  " + ctx.containsBean("paymentService"));
        System.out.println("billing:         " + ctx.containsBean("billing"));
        System.out.println("orders.repo:     " + ctx.containsBean("orders.repo"));
        // Actual class-name-based name for billing is NOT registered
        System.out.println("billingService:  " + ctx.containsBean("billingService")); // false
        ctx.close();
    }
}
```

How to run: `java NamingBasic.java`

When a stereotype's `value()` is set, that string becomes the bean name. The class-name-derived name (`billingService`) is NOT also registered — the value completely replaces it.

### Level 2 — Intermediate

Use `FullyQualifiedAnnotationBeanNameGenerator` to avoid name collisions between modules that each define a class with the same simple name.

```java
// NamingFqn.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// Simulates two "module" classes with the same simple name (different packages in real code)
@Service class UserService  { public String module() { return "module-a"; } }

// In a real multi-module project you'd have:
// com.example.modulea.UserService
// com.example.moduleb.UserService
// Default naming would collide — FQN naming avoids it

@Configuration
@ComponentScan(
    basePackageClasses = NamingFqn.class,
    nameGenerator = FullyQualifiedAnnotationBeanNameGenerator.class
)
class FqnCfg {}

public class NamingFqn {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FqnCfg.class);

        System.out.println("All bean names (FQN strategy):");
        for (String name : ctx.getBeanDefinitionNames()) {
            if (!name.contains("."))  // skip Spring internals
                System.out.println("  " + name);
            else if (name.startsWith("Naming") || name.startsWith("User"))
                System.out.println("  " + name);
        }

        // Get by FQN — the simple name "userService" is NOT registered
        System.out.println("\nSimple name works? " + ctx.containsBean("userService"));   // false
        // FQN name works
        String fqn = UserService.class.getName();
        System.out.println("FQN registered: " + ctx.containsBean(fqn));
        System.out.println("Module: " + ctx.getBean(UserService.class).module());
        ctx.close();
    }
}
```

How to run: `java NamingFqn.java`

`FullyQualifiedAnnotationBeanNameGenerator` uses the full class name (`com.example.UserService`) instead of `userService`. This eliminates collisions when two modules define a class with the same short name — each gets a unique FQN key in the registry.

### Level 3 — Advanced

Implement a custom `BeanNameGenerator` that adds a module prefix derived from the class's package, then conflict-checks against the registry.

```java
// NamingCustom.java
import org.springframework.beans.factory.config.BeanDefinition;
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.concurrent.atomic.AtomicInteger;

// Custom generator: prefix.ClassName (e.g., "payments.PaymentService")
class PrefixedBeanNameGenerator implements BeanNameGenerator {
    @Override
    public String generateBeanName(BeanDefinition definition,
                                   BeanDefinitionRegistry registry) {
        String className = definition.getBeanClassName();
        if (className == null) return "unknown-" + System.nanoTime();

        // Extract simple class name
        String simple = className.contains(".")
            ? className.substring(className.lastIndexOf('.') + 1)
            : className;

        // Derive a prefix from the last segment of the package
        String pkg = className.contains(".")
            ? className.substring(0, className.lastIndexOf('.'))
            : "root";
        String prefix = pkg.contains(".")
            ? pkg.substring(pkg.lastIndexOf('.') + 1)
            : pkg;

        String base = prefix + "." + simple;

        // Conflict resolution: append counter if name already taken
        String candidate = base;
        int counter = 1;
        while (registry.containsBeanDefinition(candidate)) {
            candidate = base + "#" + counter++;
        }
        System.out.println("[Generator] " + className + " → \"" + candidate + "\"");
        return candidate;
    }
}

// These classes exist in the same "package" here; in real apps they'd be in sub-packages
@Service class PaymentService { public String run() { return "PaymentService.run()"; } }
@Repository class PaymentRepository { public String find() { return "PaymentRepository.find()"; } }
@Service class NotificationService { public String notify() { return "NotificationService.notify()"; } }

@Configuration
@ComponentScan(
    basePackageClasses = NamingCustom.class,
    nameGenerator = PrefixedBeanNameGenerator.class
)
class CustomNameCfg {}

public class NamingCustom {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CustomNameCfg.class);

        System.out.println("\nRegistered beans (custom prefix naming):");
        for (String name : ctx.getBeanDefinitionNames()) {
            if (name.contains(".") && !name.startsWith("org."))
                System.out.println("  " + name);
        }

        // Access by generated name
        boolean found = ctx.containsBean("paymentService");   // default name — false
        System.out.println("\nDefault 'paymentService': " + found);

        // The custom name includes the package prefix segment
        ctx.close();
    }
}
```

How to run: `java NamingCustom.java`

`PrefixedBeanNameGenerator` derives a `packageSegment.ClassName` name for each bean. The conflict loop appends `#1`, `#2`, etc. if a name is already taken. The log shows exactly which name each class received.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **`AnnotationConfigApplicationContext` created** — scanner starts, using `PrefixedBeanNameGenerator`.
2. **Scanner finds `PaymentService.class`** — calls `generateBeanName(bd, registry)`. `className = "PaymentService"` (no package segment in a single-file context, so `prefix = "root"`). `candidate = "root.PaymentService"`. Registry is empty — no conflict. Registered as `"root.PaymentService"`.
3. **Same for `PaymentRepository`** → `"root.PaymentRepository"`.
4. **Same for `NotificationService`** → `"root.NotificationService"`.
5. **`ctx.containsBean("paymentService")`** — `false`. The default name was never used.
6. **Custom names printed** — shows `root.PaymentService`, `root.PaymentRepository`, etc.

Expected output (abbreviated):
```
[Generator] PaymentService → "root.PaymentService"
[Generator] PaymentRepository → "root.PaymentRepository"
[Generator] NotificationService → "root.NotificationService"
...
Registered beans (custom prefix naming):
  root.PaymentService
  root.PaymentRepository
  root.NotificationService
Default 'paymentService': false
```

## 7. Gotchas & takeaways

> When using a custom or FQN `BeanNameGenerator`, `@Autowired` by type still works — Spring resolves by type first, not name. But `ctx.getBean("beanName")` and `@Qualifier("beanName")` must use the generated name, not the intuitive short name. This can surprise developers who rely on the simple-name convention.

> Setting `nameGenerator` on `@ComponentScan` affects only beans found by that scan. `@Bean` methods in `@Configuration` classes keep their method-name-derived names regardless.

- Default `AnnotationBeanNameGenerator`: class name, first letter lower-cased. Annotation `value()` overrides it completely.
- `FullyQualifiedAnnotationBeanNameGenerator` (Spring 5.2+): use it in multi-module apps to prevent collision — it's one config change on the root `@ComponentScan`.
- Custom generators receive the `BeanDefinitionRegistry` — use `registry.containsBeanDefinition(name)` before returning a name to detect conflicts.
- The `nameGenerator` must have a no-arg constructor (Spring instantiates it via reflection).
- In Spring Boot, the `@SpringBootApplication` top-level `@ComponentScan` uses `AnnotationBeanNameGenerator`; override it by adding an explicit `@ComponentScan(nameGenerator = ...)` to your main class.
