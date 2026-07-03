---
card: spring-framework
gi: 108
slug: componentscan-component-scanning
title: "@ComponentScan & component scanning"
---

## 1. What it is

`@ComponentScan` tells Spring **where to look** for classes annotated with `@Component` and its stereotypes (`@Service`, `@Repository`, `@Controller`) and auto-registers them as beans. Without it, you must declare every bean manually as a `@Bean` method. With it, Spring discovers beans automatically by scanning the classpath.

## 2. Why & when

In any non-trivial application, declaring every bean in `@Configuration` classes doesn't scale. Component scanning is the standard automation:

- Zero boilerplate for most beans — annotate with a stereotype, scanning does the rest.
- Consistent discovery across teams — a new `@Service` class in the right package is registered without touching any config file.
- `@ComponentScan` is active implicitly in Spring Boot via `@SpringBootApplication` — you almost never write it explicitly in Boot. In plain Spring, you need it.

Configure it when you need to:
- Scan specific packages rather than the default (config class's own package).
- Exclude infrastructure or test classes from the scan.
- Include only certain annotation types.

## 3. Core concept

`@ComponentScan` attributes:

| Attribute | Purpose |
|---|---|
| `basePackages` | Package strings to scan: `basePackages = "com.example.service"` |
| `basePackageClasses` | Type-safe alternative: `basePackageClasses = AppMarker.class` |
| `includeFilters` | Scan *only* classes matching these filters |
| `excludeFilters` | Skip classes matching these filters |
| `lazyInit` | Make all discovered beans lazy by default |
| `useDefaultFilters` | Scan for `@Component` and stereotypes (default `true`); set `false` with `includeFilters` for custom scan |

Default scan base: the package of the class annotated with `@ComponentScan`. If your config class is in `com.example`, Spring scans `com.example` and all sub-packages.

Internally, `ClassPathBeanDefinitionScanner` walks the classpath for `.class` files in the specified packages, checks for `@Component` or composed stereotypes, and registers matching classes as `BeanDefinition`s.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Config -->
  <rect x="10" y="75" width="165" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="92" y="98" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@ComponentScan</text>
  <text x="92" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">basePackages=…</text>

  <!-- Classpath packages -->
  <rect x="260" y="30" width="165" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="342" y="51" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">com.example.service</text>

  <rect x="260" y="80" width="165" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="342" y="101" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">com.example.repo</text>

  <rect x="260" y="130" width="165" height="34" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="342" y="151" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">com.example.web</text>

  <!-- Result -->
  <rect x="525" y="75" width="165" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="98" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">BeanDefinitions</text>
  <text x="607" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">auto-registered</text>

  <line x1="177" y1="102" x2="257" y2="47" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a108)"/>
  <line x1="177" y1="102" x2="257" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a108)"/>
  <line x1="177" y1="102" x2="257" y2="147" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a108)"/>
  <line x1="427" y1="97" x2="522" y2="97" stroke="#79c0ff" stroke-width="2" marker-end="url(#b108)"/>
  <defs>
    <marker id="a108" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b108" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Scanner walks specified packages → finds @Component classes → registers BeanDefinitions</text>
</svg>

`@ComponentScan` drives the scanner across configured packages; each matched class becomes a managed bean.

## 5. Runnable example

### Level 1 — Basic

Default scan (current package) discovers all `@Component` classes automatically.

```java
// ScanBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Repository
class ItemRepository {
    public String find(int id) { return "Item#" + id; }
}

@Service
class ItemService {
    @Autowired private ItemRepository repo;
    public String get(int id) { return repo.find(id); }
}

@Configuration
@ComponentScan   // scans the package containing AppConfig (same file here)
class AppConfig {}

public class ScanBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        System.out.println(ctx.getBean(ItemService.class).get(7));
        System.out.println("Total beans: " + ctx.getBeanDefinitionCount());
        ctx.close();
    }
}
```

How to run: `java ScanBasic.java`

`@ComponentScan` on `AppConfig` scans the same package. Both `ItemRepository` and `ItemService` are found and wired without any `@Bean` declaration.

### Level 2 — Intermediate

Specify multiple base packages and exclude a class via `excludeFilters`.

```java
// ScanFiltered.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service class UserService     { public String greet() { return "Hello from UserService"; } }
@Service class ProductService  { public String greet() { return "Hello from ProductService"; } }

// This one will be EXCLUDED from scan
@Service class InternalService { public String greet() { return "I should not be registered!"; } }

@Configuration
@ComponentScan(
    basePackageClasses = ScanFiltered.class,          // type-safe base package
    excludeFilters = @ComponentScan.Filter(
        type = org.springframework.context.annotation.FilterType.ASSIGNABLE_TYPE,
        classes = InternalService.class
    )
)
class FilteredCfg {}

public class ScanFiltered {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FilteredCfg.class);

        System.out.println("UserService:    " + ctx.getBean(UserService.class).greet());
        System.out.println("ProductService: " + ctx.getBean(ProductService.class).greet());

        boolean hasInternal = ctx.containsBean("internalService");
        System.out.println("InternalService registered: " + hasInternal);   // false

        ctx.close();
    }
}
```

How to run: `java ScanFiltered.java`

`basePackageClasses` uses the class literal for a refactor-safe package reference. `excludeFilters` with `ASSIGNABLE_TYPE` skips `InternalService` — it's never registered.

### Level 3 — Advanced

Multiple `@ComponentScan` definitions (via `@ComponentScans`), custom include filter scanning only `@Repository` classes in one package and `@Service` in another, plus lazy initialisation.

```java
// ScanAdvanced.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.Arrays;

// Simulating "packages" via nested types in one file (real apps use real packages)
@Repository class OrderRepo    { public String load() { return "OrderRepo.load()"; } }
@Repository class ProductRepo  { public String load() { return "ProductRepo.load()"; } }
@Service class OrderService    {
    @Autowired OrderRepo repo;
    public String run() { return "OrderService → " + repo.load(); }
}
@Service class ProductService  {
    @Autowired ProductRepo repo;
    public String run() { return "ProductService → " + repo.load(); }
}
@Component class UtilityHelper { public String help() { return "UtilityHelper.help()"; } }

@Configuration
@ComponentScans({
    @ComponentScan(
        basePackageClasses = ScanAdvanced.class,
        // Only pick up @Repository beans in this scan
        useDefaultFilters = false,
        includeFilters = @ComponentScan.Filter(
            type = FilterType.ANNOTATION,
            classes = Repository.class
        )
    ),
    @ComponentScan(
        basePackageClasses = ScanAdvanced.class,
        // Only pick up @Service beans in this scan; lazy init all of them
        useDefaultFilters = false,
        lazyInit = true,
        includeFilters = @ComponentScan.Filter(
            type = FilterType.ANNOTATION,
            classes = Service.class
        )
    )
    // Note: @Component / UtilityHelper is NOT covered by either scan
})
class AdvScanCfg {}

public class ScanAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvScanCfg.class);

        // Services are lazy — not yet instantiated
        System.out.println("Context ready. Services are lazy.");

        // Accessing a service triggers lazy init
        System.out.println(ctx.getBean(OrderService.class).run());
        System.out.println(ctx.getBean(ProductService.class).run());

        // UtilityHelper was not in any scan
        System.out.println("UtilityHelper registered: " + ctx.containsBean("utilityHelper"));

        // Print all registered bean names
        System.out.println("All beans: " + Arrays.toString(ctx.getBeanDefinitionNames()));
        ctx.close();
    }
}
```

How to run: `java ScanAdvanced.java`

`@ComponentScans` stacks two scans with different `includeFilters`. The first picks up only `@Repository` classes; the second picks up only `@Service` classes with lazy initialisation. `UtilityHelper` (`@Component`) is excluded from both scans and therefore never registered.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context created from `AdvScanCfg`** — triggers two scans.
2. **Scan 1 (repositories, eager)** — `useDefaultFilters = false`, `includeFilters = @Repository`. Finds `OrderRepo`, `ProductRepo`. Registers as eager singletons.
3. **Scan 2 (services, lazy)** — `useDefaultFilters = false`, `includeFilters = @Service`, `lazyInit = true`. Finds `OrderService`, `ProductService`. Registers as lazy singletons — BeanDefinitions exist, but no instances created.
4. **`"Context ready."` printed** — only `OrderRepo` and `ProductRepo` have been instantiated so far.
5. **`ctx.getBean(OrderService.class)`** — first access; lazy trigger fires; `OrderService` constructed; `@Autowired OrderRepo repo` resolved (already exists); `run()` called.
6. **`ctx.getBean(ProductService.class)`** — same pattern; `ProductService` constructed lazily.
7. **`ctx.containsBean("utilityHelper")`** — `false` — `UtilityHelper` was not covered by either scan.
8. **`getBeanDefinitionNames()`** — shows `orderRepo`, `productRepo`, `orderService`, `productService` (plus Spring infrastructure beans), but not `utilityHelper`.

Expected output:
```
Context ready. Services are lazy.
OrderService → OrderRepo.load()
ProductService → ProductRepo.load()
UtilityHelper registered: false
All beans: [advScanCfg, orderRepo, productRepo, orderService, productService, ...]
```

## 7. Gotchas & takeaways

> If `@ComponentScan` is placed on a class inside `com.example.config` but your `@Service` classes are in `com.example.service` (a different sub-package), they **will** be found — sub-packages are included by default. But if they're in `com.other` (outside the tree), they'll be missed silently.

> Setting `useDefaultFilters = false` without any `includeFilters` results in an empty scan — zero beans discovered. Always pair `useDefaultFilters = false` with at least one `includeFilter`.

- `basePackageClasses` is the refactor-safe way to specify a package — rename the class and the scan base renames with it. A common pattern: place a marker interface `package-info.java` or empty `package-info` class in each sub-package.
- `lazyInit = true` is a scan-level switch; it makes *all* beans found in that scan lazy. Individual beans can still override with `@Lazy(false)`.
- `@ComponentScan` without arguments scans the annotating class's own package — placing the config class in a root package ensures full coverage.
- Component scanning is O(n) in classpath size; for very large classpaths, explicit `basePackages` is faster than scanning everything.
