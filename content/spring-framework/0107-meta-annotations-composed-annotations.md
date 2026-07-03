---
card: spring-framework
gi: 107
slug: meta-annotations-composed-annotations
title: Meta-annotations & composed annotations
---

## 1. What it is

A **meta-annotation** is an annotation applied to another annotation. Spring treats most of its own annotations as meta-annotations, so you can create **composed annotations** — your own shorthand annotations that combine and configure multiple Spring annotations in one.

Example: `@RestController` is a composed annotation that is itself annotated with `@Controller` and `@ResponseBody`. When Spring sees `@RestController`, it acts as if it saw both.

## 2. Why & when

Real projects repeat the same annotation combinations everywhere:

```java
@Controller
@ResponseBody
public class UserApi { ... }   // repeated on 40 controllers
```

A composed annotation extracts that repetition:

```java
@RestController
public class UserApi { ... }   // one annotation = two behaviours
```

Write composed annotations when:
- You use the same 2–3 Spring annotations together on every class in a category.
- You want to add project-specific defaults (e.g., always include `@Transactional(rollbackFor = Exception.class)`).
- You want a domain-meaningful name: `@DomainService` instead of `@Service @Transactional`.

## 3. Core concept

Spring's annotation processing uses `AnnotationUtils` and `MergedAnnotations` to traverse the annotation hierarchy. When Spring inspects a class for `@Component`, it doesn't just look for the literal `@Component` annotation — it looks for `@Component` or any annotation that is *itself* annotated with `@Component` (recursively).

This is called **annotation composition** or **meta-annotation inheritance**. Rules:

1. Any annotation annotated with `@Component` (directly or transitively) causes the class to be treated as a Spring component.
2. Attributes from composed annotations can **override** meta-annotation defaults using `@AliasFor`.
3. Spring reads the merged annotation from the outermost annotation first — outer attributes take precedence over meta-annotation defaults.

`@AliasFor` lets you expose a meta-annotation's attribute under a different name on your composed annotation, giving callers a clean API.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <!-- Base annotations -->
  <rect x="10"  y="20" width="140" height="36" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80"  y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Component</text>

  <rect x="165" y="20" width="140" height="36" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="235" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Transactional</text>

  <rect x="320" y="20" width="140" height="36" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="390" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Validated</text>

  <!-- Composed annotation -->
  <rect x="200" y="120" width="190" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="295" y="142" fill="#79c0ff" font-size="13" text-anchor="middle" font-family="sans-serif">@DomainService</text>
  <text x="295" y="157" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">composed annotation</text>

  <!-- Lines from bases to composed -->
  <line x1="80"  y1="56" x2="240" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a107)"/>
  <line x1="235" y1="56" x2="270" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#b107)"/>
  <line x1="390" y1="56" x2="340" y2="118" stroke="#8b949e" stroke-width="1.5" marker-end="url(#b107)"/>

  <!-- Target class -->
  <rect x="200" y="195" width="190" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="214" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@DomainService class</text>
  <line x1="295" y1="164" x2="295" y2="193" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#c107)"/>

  <defs>
    <marker id="a107" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b107" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="c107" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="30" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">meta-annotations applied to @DomainService</text>
</svg>

`@DomainService` composes three Spring annotations; the target class needs only one annotation instead of three.

## 5. Runnable example

### Level 1 — Basic

Create `@DomainService` that acts as both `@Service` and sets a custom bean name prefix — one annotation on each business class instead of two.

```java
// MetaBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

// Composed annotation: @Service + @Scope("singleton") packaged as @DomainService
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Service         // meta-annotation — Spring sees @Component transitively
@Documented
@interface DomainService {}

@DomainService   // acts as @Service → auto-registered bean
class PaymentService {
    public String pay(double amount) { return "Paid $" + amount; }
}

@DomainService
class ShippingService {
    public String ship(String address) { return "Shipped to " + address; }
}

@Controller
class CheckoutController {
    @Autowired private PaymentService payments;
    @Autowired private ShippingService shipping;

    public String checkout(double amount, String address) {
        return payments.pay(amount) + " | " + shipping.ship(address);
    }
}

@Configuration
@ComponentScan
class MetaCfg {}

public class MetaBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MetaCfg.class);
        var ctrl = ctx.getBean(CheckoutController.class);
        System.out.println(ctrl.checkout(99.99, "123 Main St"));
        // Confirm both classes are registered as Spring beans
        System.out.println("paymentService: " + ctx.containsBean("paymentService"));
        System.out.println("shippingService: " + ctx.containsBean("shippingService"));
        ctx.close();
    }
}
```

How to run: `java MetaBasic.java`

`@DomainService` meta-annotated with `@Service` causes Spring to register `PaymentService` and `ShippingService` via component scanning. The annotation hierarchy: `@DomainService` → `@Service` → `@Component`.

### Level 2 — Intermediate

Use `@AliasFor` to let the composed annotation expose the meta-annotation's `value` attribute under a cleaner name.

```java
// MetaAlias.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.AliasFor;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

// @InfraComponent composes @Component but exposes 'name' instead of 'value'
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Component    // meta-annotation
@interface InfraComponent {
    @AliasFor(annotation = Component.class, attribute = "value")
    String name() default "";   // maps to @Component's 'value' (= bean name)
}

@InfraComponent(name = "emailGateway")
class EmailGateway {
    public void send(String to, String msg) {
        System.out.println("[EMAIL→" + to + "] " + msg);
    }
}

@InfraComponent(name = "smsGateway")
class SmsGateway {
    public void send(String to, String msg) {
        System.out.println("[SMS→" + to + "] " + msg);
    }
}

@Service
class NotificationService {
    @Autowired private EmailGateway email;
    @Autowired private SmsGateway   sms;

    public void notifyAll(String user, String msg) {
        email.send(user + "@example.com", msg);
        sms.send("+1555" + user.length() + "000", msg);
    }
}

@Configuration
@ComponentScan
class AliasCfg {}

public class MetaAlias {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AliasCfg.class);
        ctx.getBean(NotificationService.class).notifyAll("alice", "Order shipped");
        System.out.println("emailGateway bean: " + ctx.containsBean("emailGateway"));
        System.out.println("smsGateway bean:   " + ctx.containsBean("smsGateway"));
        ctx.close();
    }
}
```

How to run: `java MetaAlias.java`

`@AliasFor(annotation = Component.class, attribute = "value")` maps `@InfraComponent(name = "emailGateway")` to `@Component("emailGateway")`. Spring registers the bean with the specified name.

### Level 3 — Advanced

A fully composed `@ApiController` annotation that combines `@RestController` + `@RequestMapping` prefix + `@Validated`, demonstrating how multiple attributes from different meta-annotations are unified.

```java
// MetaComposed.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.AliasFor;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import java.lang.annotation.*;

// Composed: @RestController + @RequestMapping with a configurable path prefix
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@Documented
@RestController   // itself composed of @Controller + @ResponseBody
@RequestMapping   // adds routing support
@interface ApiController {
    // Expose @RequestMapping's 'value' attribute as 'path' on our annotation
    @AliasFor(annotation = RequestMapping.class, attribute = "value")
    String[] path() default {};
}

// Standalone simulated service (no Spring MVC needed to demonstrate composition)
@Service
class ProductService {
    public String find(int id) { return "Product#" + id; }
}

// Annotation fully composed — no extra annotations needed on the controller
@ApiController(path = "/api/v1/products")
class ProductController {
    @Autowired private ProductService svc;

    // Verify composition: check what annotations Spring sees on this class
    public void printAnnotations() {
        var annotations = ProductController.class.getAnnotations();
        System.out.println("Direct annotations on ProductController:");
        for (var a : annotations) System.out.println("  " + a.annotationType().getSimpleName());

        // Spring's MergedAnnotations sees the full hierarchy
        var merged = org.springframework.core.annotation.MergedAnnotations
            .from(ProductController.class,
                  org.springframework.core.annotation.MergedAnnotations.SearchStrategy.TYPE_HIERARCHY);
        System.out.println("\nSpring merged annotation hierarchy includes:");
        merged.stream()
              .map(ma -> ma.getType().getSimpleName())
              .distinct()
              .sorted()
              .forEach(n -> System.out.println("  " + n));

        System.out.println("\n@RequestMapping path: " +
            merged.get(RequestMapping.class).getString("value"));
    }
}

@Configuration
@ComponentScan
class ComposedCfg {}

public class MetaComposed {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ComposedCfg.class);
        ctx.getBean(ProductController.class).printAnnotations();
        ctx.close();
    }
}
```

How to run: `java MetaComposed.java`

`ProductController` only has `@ApiController(path="/api/v1/products")` on it. Spring's `MergedAnnotations` resolves the full hierarchy: `ApiController` → `RestController` → `Controller` → `Component`, plus `ResponseBody` and `RequestMapping`. The `path` attribute alias resolves correctly to `@RequestMapping`'s `value`.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context scans `ComposedCfg`** — `ProductController` has `@ApiController`. Spring's scanner checks: "is this class (transitively) annotated with `@Component`?" It traverses `@ApiController` → `@RestController` → `@Controller` → `@Component`. Yes → register as bean.
2. **`ProductService` registered** — direct `@Service` → `@Component`.
3. **`ProductController` autowired** — `@Autowired ProductService svc` resolved to `productService` bean.
4. **`printAnnotations()` called** — direct reflection (`getAnnotations()`) shows only the literal `@ApiController`. Spring's `MergedAnnotations.from(...)` with `TYPE_HIERARCHY` walks the meta-annotation tree, collecting all composed annotations transitively.
5. **`merged.get(RequestMapping.class).getString("value")`** — even though `@RequestMapping` is on `@ApiController`, not directly on `ProductController`, Spring resolves the `path` → `value` alias and returns `"/api/v1/products"`.

Expected output:
```
Direct annotations on ProductController:
  ApiController

Spring merged annotation hierarchy includes:
  ApiController
  Component
  Controller
  Documented
  RequestMapping
  ResponseBody
  RestController
  Target
  ...

@RequestMapping path: /api/v1/products
```

## 7. Gotchas & takeaways

> `@AliasFor` only works when Spring processes the annotation via `MergedAnnotations` or `AnnotationUtils`. Raw Java reflection (`getAnnotation(RequestMapping.class)`) on a class annotated with `@ApiController` will return `null` — the meta-annotation is invisible to standard Java reflection.

> Composed annotations must set `@Retention(RetentionPolicy.RUNTIME)` — annotations that don't survive to runtime can't be read by Spring.

- All standard Spring annotations are designed to be used as meta-annotations — `@Service`, `@Transactional`, `@RequestMapping`, `@Qualifier`, etc.
- Keep composed annotations in a shared module / package so all teams use the same project-wide conventions.
- `@AliasFor` binds an attribute in your annotation to an attribute in the meta-annotation — useful for exposing a clean API while keeping internal Spring mechanics hidden.
- Test your composed annotations by checking `MergedAnnotations.from(MyClass.class)` — it's the same API Spring uses internally.
