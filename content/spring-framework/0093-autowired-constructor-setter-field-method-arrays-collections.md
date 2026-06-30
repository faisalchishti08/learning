---
card: spring-framework
gi: 93
slug: autowired-constructor-setter-field-method-arrays-collections
title: "@Autowired (constructor, setter, field, method, arrays/collections)"
---

## 1. What it is

`@Autowired` is Spring's core annotation for **dependency injection**. Place it on a constructor, setter method, arbitrary method, or field, and Spring resolves the matching bean(s) from the context and injects them automatically. It also handles arrays, `List`, `Set`, and `Map` to inject **all beans of a given type** at once.

## 2. Why & when

Without `@Autowired` you must manually wire every dependency in `@Bean` methods or XML — tedious and error-prone at scale. `@Autowired` lets Spring take over the wiring:

- **Constructor injection** (recommended) — dependencies come in at construction time; the bean is always fully initialised and fields can be `final`.
- **Setter injection** — useful for optional dependencies or when you need to allow re-injection after construction (rare).
- **Field injection** — quick to write but makes testing harder (can't inject via constructor in unit tests) and hides the dependency graph.
- **Arbitrary method injection** — rarely needed; Spring calls any method annotated with `@Autowired` after construction.
- **Arrays / collections** — inject every registered bean of a type for fan-out patterns (plugin architectures, validators, event handlers).

## 3. Core concept

Spring's `AutowiredAnnotationBeanPostProcessor` scans each bean for `@Autowired` annotations and resolves the injection points:

1. **By type** — finds all beans matching the parameter/field type.
2. **By qualifier** — if multiple beans match, uses `@Qualifier` or the parameter name as a tiebreaker.
3. **For collections** — injects *all* matching beans, ordered by `@Order` or `Ordered`.

The single rule: for **required** injection (default) Spring throws `NoSuchBeanDefinitionException` if no matching bean is found. Use `@Autowired(required = false)` or `Optional<T>` for optional deps.

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg">
  <!-- Spring Context -->
  <rect x="10" y="30" width="145" height="200" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="82" y="52" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Context</text>
  <text x="82" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ServiceA</text>
  <text x="82" y="92" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ServiceB</text>
  <text x="82" y="112" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RepoImpl</text>
  <text x="82" y="132" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ValidatorA</text>
  <text x="82" y="152" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ValidatorB</text>

  <!-- Target Bean -->
  <rect x="280" y="30" width="200" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="380" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">MyBean</text>
  <text x="380" y="76" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired constructor(ServiceA)</text>
  <text x="380" y="96" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired setServiceB(…)</text>
  <text x="380" y="116" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired RepoImpl repo</text>
  <text x="380" y="136" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired List&lt;Validator&gt;</text>
  <text x="380" y="156" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired Validator[]</text>
  <text x="380" y="176" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Autowired Map&lt;String,Svc&gt;</text>

  <!-- Arrows -->
  <line x1="157" y1="72" x2="277" y2="72" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a93)"/>
  <line x1="157" y1="92" x2="277" y2="96" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a93)"/>
  <line x1="157" y1="112" x2="277" y2="116" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a93)"/>
  <line x1="157" y1="132" x2="277" y2="136" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a93)"/>
  <line x1="157" y1="152" x2="277" y2="155" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a93)"/>
  <defs>
    <marker id="a93" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="248" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Autowired works on constructor · setter · field · method · array/collection</text>
</svg>

Spring resolves matching beans from the context and injects them at every `@Autowired` injection point.

## 5. Runnable example

### Level 1 — Basic

Constructor injection (the recommended form): one service depends on a repository.

```java
// AutowiredBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Repository
class UserRepo {
    public String find(int id) { return "User#" + id; }
}

@Service
class UserService {
    private final UserRepo repo;

    // Single constructor — @Autowired optional here (Spring 4.3+), shown for clarity
    @Autowired
    public UserService(UserRepo repo) { this.repo = repo; }

    public void printUser(int id) { System.out.println(repo.find(id)); }
}

@Configuration
@ComponentScan
class AppCfg {}

public class AutowiredBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        ctx.getBean(UserService.class).printUser(42);
        ctx.close();
    }
}
```

How to run: `java AutowiredBasic.java`

Spring finds `UserRepo` via component scan, then injects it into `UserService`'s constructor. The field is `final` — immutable after construction.

### Level 2 — Intermediate

All four injection styles on a single bean, plus setter injection for an optional dependency.

```java
// AutowiredStyles.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Repository
class ProductRepo {
    public String find(int id) { return "Product#" + id; }
}

@Service
class AuditService {
    public void log(String msg) { System.out.println("[AUDIT] " + msg); }
}

@Component
class CacheService {
    public String get(String k) { return "cached:" + k; }
}

@Service
class ProductService {
    // 1. Constructor injection (preferred — final field)
    private final ProductRepo repo;
    @Autowired
    public ProductService(ProductRepo repo) { this.repo = repo; }

    // 2. Setter injection (useful when optional)
    private AuditService audit;
    @Autowired
    public void setAudit(AuditService a) { this.audit = a; }

    // 3. Field injection (quick but harder to unit-test)
    @Autowired
    private CacheService cache;

    // 4. Arbitrary method injection (called by Spring after construction)
    private String configuredRegion;
    @Autowired
    public void configure(CacheService cacheService) {
        // Could do additional setup here
        this.configuredRegion = "EU";
        System.out.println("configure() called by Spring — region set to " + configuredRegion);
    }

    public void get(int id) {
        audit.log("get " + id);
        String cached = cache.get(String.valueOf(id));
        System.out.println(cached.startsWith("cached") ? cached : repo.find(id));
    }
}

@Configuration
@ComponentScan
class StylesCfg {}

public class AutowiredStyles {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(StylesCfg.class);
        ctx.getBean(ProductService.class).get(7);
        ctx.close();
    }
}
```

How to run: `java AutowiredStyles.java`

Spring calls the constructor first, then the `@Autowired` setter, then the `@Autowired` arbitrary method, then injects the `@Autowired` field — all before the bean enters service.

### Level 3 — Advanced

Inject all validators as a `List<Validator>`, an array, and a `Map<String, Validator>` (keyed by bean name) to build a plugin-style validation pipeline.

```java
// AutowiredCollections.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.*;
import java.util.*;

interface Validator {
    boolean validate(String input);
    String name();
}

@Component @Order(1)
class NotBlankValidator implements Validator {
    public boolean validate(String v) { return v != null && !v.isBlank(); }
    public String name() { return "NotBlank"; }
}

@Component @Order(2)
class LengthValidator implements Validator {
    public boolean validate(String v) { return v != null && v.length() <= 50; }
    public String name() { return "Length<=50"; }
}

@Component @Order(3)
class EmailValidator implements Validator {
    public boolean validate(String v) { return v != null && v.contains("@"); }
    public String name() { return "EmailFormat"; }
}

@Service
class ValidationService {
    // All Validator beans — ordered by @Order
    @Autowired private List<Validator> validatorList;

    // Same beans as an array
    @Autowired private Validator[] validatorArray;

    // Bean-name → bean (useful for selecting by name at runtime)
    @Autowired private Map<String, Validator> validatorMap;

    public boolean validate(String input) {
        System.out.println("\n--- Validating: \"" + input + "\" ---");
        System.out.println("Via List (" + validatorList.size() + " validators):");
        boolean ok = true;
        for (var v : validatorList) {
            boolean pass = v.validate(input);
            System.out.printf("  %s: %s%n", v.name(), pass ? "PASS" : "FAIL");
            if (!pass) ok = false;
        }
        System.out.println("Map keys: " + validatorMap.keySet());
        return ok;
    }
}

@Configuration
@ComponentScan
class CollCfg {}

public class AutowiredCollections {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CollCfg.class);
        var svc = ctx.getBean(ValidationService.class);
        svc.validate("user@example.com");
        svc.validate("");
        svc.validate("not-an-email");
        ctx.close();
    }
}
```

How to run: `java AutowiredCollections.java`

Spring collects all `Validator` beans into the list (ordered by `@Order`), the same beans into the array, and wraps them in a `Map<String, Validator>` where the key is the bean name (e.g., `"notBlankValidator"`).

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Component scan** — Spring finds `NotBlankValidator`, `LengthValidator`, `EmailValidator`, and `ValidationService`.
2. **Validators instantiated first** — they have no dependencies, so Spring creates them in order of discovery (the exact order is registration order, then sorted by `@Order` for injection).
3. **`ValidationService` instantiated** — `AutowiredAnnotationBeanPostProcessor` inspects it and finds three `@Autowired` fields.
4. **`validatorList` resolved** — Spring collects all beans assignable to `Validator`, sorts them by `@Order` (1→2→3), and wraps them in an `ArrayList`. Injected.
5. **`validatorArray` resolved** — same set, same order, wrapped as `Validator[]`. Injected.
6. **`validatorMap` resolved** — Spring builds a `LinkedHashMap<String, Validator>` with bean names as keys: `{"notBlankValidator": …, "lengthValidator": …, "emailValidator": …}`. Injected.
7. **`validate("user@example.com")`** — iterates `validatorList`, calls each in `@Order` order. All pass.
8. **`validate("")`** — `NotBlankValidator` fails (`isBlank()` → true); `LengthValidator` passes; `EmailValidator` fails.

Expected output (abbreviated):
```
--- Validating: "user@example.com" ---
Via List (3 validators):
  NotBlank: PASS
  Length<=50: PASS
  EmailFormat: PASS
Map keys: [notBlankValidator, lengthValidator, emailValidator]

--- Validating: "" ---
  NotBlank: FAIL
  Length<=50: PASS
  EmailFormat: FAIL
```

## 7. Gotchas & takeaways

> Prefer **constructor injection** for required dependencies and **`@Autowired(required = false)`** or `Optional<T>` for optional ones. Field injection (`@Autowired` on a private field) makes unit testing painful because you can't supply dependencies without a Spring context or reflection.

> When injecting a `List<T>` or `T[]`, Spring injects **all beans** of type `T`. If you want just one, use a plain `@Autowired T field` and resolve ambiguity with `@Qualifier` or `@Primary`.

- `@Autowired` on a **constructor** with a single constructor is implicit since Spring 4.3 — no annotation needed.
- Injection order in collections follows `@Order`, `Ordered`, or `PriorityOrdered`; use these to control pipeline sequence.
- `Map<String, T>` injection gives you both the bean and its name — useful for dynamic dispatch by name at runtime.
- `@Autowired` is processed by `AutowiredAnnotationBeanPostProcessor`; it must be registered, which happens automatically with `@Configuration` + component scanning.
- Never mix constructor and field injection for the same dependency — pick one style per bean.
