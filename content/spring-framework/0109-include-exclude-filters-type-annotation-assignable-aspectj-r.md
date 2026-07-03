---
card: spring-framework
gi: 109
slug: include-exclude-filters-type-annotation-assignable-aspectj-r
title: Include/exclude filters (type, annotation, assignable, aspectj, regex, custom)
---

## 1. What it is

`@ComponentScan`'s `includeFilters` and `excludeFilters` control which classes the scanner admits or rejects. Each filter is a `@ComponentScan.Filter` with a `type` that picks the matching strategy and a `classes` or `pattern` that defines the criterion.

Spring ships six filter types:

| `FilterType` | Matches on |
|---|---|
| `ANNOTATION` | Class has a specific annotation |
| `ASSIGNABLE_TYPE` | Class is or extends/implements a type |
| `ASPECTJ` | Class matches an AspectJ type pattern |
| `REGEX` | Full class name matches a regex |
| `CUSTOM` | User-supplied `TypeFilter` implementation |

## 2. Why & when

The default scan picks up every `@Component`-annotated class. Filters let you:

- **Include** only a subset without annotating every class (e.g., include all classes in a specific sub-package using `REGEX`).
- **Exclude** infrastructure/test/internal classes that should not be beans.
- **Select by interface** (`ASSIGNABLE_TYPE`) — any class implementing `HealthCheck` becomes a bean.
- **Custom logic** — combine conditions the built-in filters can't express.

## 3. Core concept

`@ComponentScan.Filter` anatomy:

```java
@ComponentScan.Filter(
    type  = FilterType.ANNOTATION,   // how to match
    classes = MyAnnotation.class     // what to match
)
```

- **`includeFilters`** — scanner checks these AFTER the default scan; a class matching any include filter is admitted. When `useDefaultFilters = false`, only classes matching include filters are admitted (no `@Component` requirement).
- **`excludeFilters`** — applied AFTER inclusion; a class matching any exclude filter is removed regardless of include rules.

Order of evaluation: default filter (or include filter) → exclude filter → register.

For `CUSTOM` filters, implement `org.springframework.core.type.filter.TypeFilter`:
```java
boolean match(MetadataReader reader, MetadataReaderFactory factory)
```
`MetadataReader` gives you class metadata, annotations, and class hierarchy info — without loading the class into the JVM.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Classpath -->
  <rect x="10" y="60" width="145" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="82" y="82" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Classpath classes</text>
  <text x="82" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Service A</text>
  <text x="82" y="113" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Component B</text>
  <text x="82" y="127" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Internal C</text>

  <!-- Include filter -->
  <rect x="240" y="40" width="155" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="317" y="63" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">includeFilters ✓</text>

  <!-- Exclude filter -->
  <rect x="240" y="100" width="155" height="40" rx="7" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="317" y="123" fill="#ff7b72" font-size="11" text-anchor="middle" font-family="sans-serif">excludeFilters ✗</text>

  <!-- Context -->
  <rect x="490" y="60" width="200" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="590" y="82" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Registered beans</text>
  <text x="590" y="99" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">A ✓ (included)</text>
  <text x="590" y="113" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">B ✓ (default)</text>
  <text x="590" y="127" fill="#ff7b72" font-size="10" text-anchor="middle" font-family="sans-serif">C ✗ (excluded)</text>

  <line x1="157" y1="90" x2="237" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a109)"/>
  <line x1="157" y1="100" x2="237" y2="120" stroke="#ff7b72" stroke-width="1.5" marker-end="url(#c109)"/>
  <line x1="397" y1="80" x2="487" y2="90" stroke="#79c0ff" stroke-width="2" marker-end="url(#b109)"/>
  <defs>
    <marker id="a109" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b109" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c109" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">include admits → exclude rejects → remainder becomes beans</text>
</svg>

Include and exclude filters gate which classpath classes enter the Spring context.

## 5. Runnable example

### Level 1 — Basic

Use `ANNOTATION` and `ASSIGNABLE_TYPE` filters to include and exclude specific classes.

```java
// FiltersBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

@interface InternalOnly {}   // mark classes that should NOT be beans

@Service class PublicService   { public String role() { return "PublicService";   } }
@Service class HelperService   { public String role() { return "HelperService";   } }

@Service @InternalOnly
class InfraService { public String role() { return "InfraService (should be excluded)"; } }

@Configuration
@ComponentScan(
    basePackageClasses = FiltersBasic.class,
    excludeFilters = @ComponentScan.Filter(
        type   = FilterType.ANNOTATION,
        classes = InternalOnly.class      // exclude any class annotated @InternalOnly
    )
)
class FiltersCfg {}

public class FiltersBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FiltersCfg.class);
        System.out.println("PublicService:  " + ctx.containsBean("publicService"));
        System.out.println("HelperService:  " + ctx.containsBean("helperService"));
        System.out.println("InfraService:   " + ctx.containsBean("infraService"));   // false
        ctx.close();
    }
}
```

How to run: `java FiltersBasic.java`

`@InternalOnly` on `InfraService` triggers the exclude filter — it is never registered despite having `@Service`. The public and helper services are registered normally.

### Level 2 — Intermediate

Use `ASSIGNABLE_TYPE` to include all `HealthCheck` implementors without requiring them to have `@Component`, and `REGEX` to exclude test classes.

```java
// FiltersAssignableRegex.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// All implementations of HealthCheck should be beans — no @Component needed
interface HealthCheck {
    String check();
}

class DatabaseHealthCheck implements HealthCheck {
    public String check() { return "DB: OK"; }
}

class CacheHealthCheck implements HealthCheck {
    public String check() { return "Cache: OK"; }
}

// This looks like a test class — regex will exclude it
class DatabaseHealthCheckTest implements HealthCheck {
    public String check() { return "DB: TEST (should not run in prod)"; }
}

@Service
class MonitoringService {
    @org.springframework.beans.factory.annotation.Autowired
    private java.util.List<HealthCheck> checks;

    public void runAll() {
        System.out.println("Running " + checks.size() + " health checks:");
        checks.forEach(c -> System.out.println("  " + c.check()));
    }
}

@Configuration
@ComponentScan(
    basePackageClasses = FiltersAssignableRegex.class,
    useDefaultFilters  = true,
    includeFilters = @ComponentScan.Filter(
        type    = FilterType.ASSIGNABLE_TYPE,
        classes = HealthCheck.class          // include all HealthCheck implementors
    ),
    excludeFilters = @ComponentScan.Filter(
        type    = FilterType.REGEX,
        pattern = ".*Test"                   // exclude classes whose name ends in Test
    )
)
class AssignableCfg {}

public class FiltersAssignableRegex {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AssignableCfg.class);
        System.out.println("dbHealthCheck:   " + ctx.containsBean("databaseHealthCheck"));
        System.out.println("cacheCheck:      " + ctx.containsBean("cacheHealthCheck"));
        System.out.println("testCheck:       " + ctx.containsBean("databaseHealthCheckTest")); // false
        ctx.getBean(MonitoringService.class).runAll();
        ctx.close();
    }
}
```

How to run: `java FiltersAssignableRegex.java`

`ASSIGNABLE_TYPE = HealthCheck.class` includes all implementors without requiring `@Component`. `REGEX = ".*Test"` excludes any class whose fully qualified name ends in `Test`, so `DatabaseHealthCheckTest` is removed.

### Level 3 — Advanced

Implement a `CUSTOM` `TypeFilter` that includes only classes with a Javadoc-style comment marker (checked via annotation), combining with other filters in a production-flavoured monitoring setup.

```java
// FiltersCustom.java
import org.springframework.context.annotation.*;
import org.springframework.core.type.classreading.*;
import org.springframework.core.type.filter.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;
import java.util.*;

// Marker annotation used by the custom filter
@Target(ElementType.TYPE)
@Retention(RetentionPolicy.RUNTIME)
@interface Monitored {
    String category() default "general";
}

interface MetricCollector {
    String collect();
}

@Component @Monitored(category = "database")
class DbMetricCollector implements MetricCollector {
    public String collect() { return "db.connections=42"; }
}

@Component @Monitored(category = "cache")
class CacheMetricCollector implements MetricCollector {
    public String collect() { return "cache.hit_rate=0.87"; }
}

@Component   // NOT @Monitored — custom filter will exclude it
class UtilityMetricCollector implements MetricCollector {
    public String collect() { return "utility.noop"; }
}

// Custom TypeFilter: admits only classes annotated with @Monitored
class MonitoredFilter implements TypeFilter {
    @Override
    public boolean match(MetadataReader reader, MetadataReaderFactory factory) {
        return reader.getAnnotationMetadata()
                     .isAnnotated(Monitored.class.getName());
    }
}

@Service
class MetricsDashboard {
    @org.springframework.beans.factory.annotation.Autowired
    private List<MetricCollector> collectors;

    public void display() {
        System.out.println("Monitored metrics (" + collectors.size() + "):");
        collectors.forEach(c -> System.out.println("  " + c.collect()));
    }
}

@Configuration
@ComponentScan(
    basePackageClasses = FiltersCustom.class,
    useDefaultFilters  = true,
    excludeFilters = @ComponentScan.Filter(
        type    = FilterType.CUSTOM,
        classes = MonitoredFilter.class    // wait — this is an INclude filter used as EXclude
        // To exclude non-@Monitored MetricCollectors, we use a negating wrapper below
    )
)
class CustomFilterCfgWrong {}   // intentionally separate — see CorrectCfg below

// The correct approach: include only @Monitored MetricCollector impls via custom filter
@Configuration
@ComponentScan(
    basePackageClasses = FiltersCustom.class,
    useDefaultFilters  = true,             // still picks up @Service, @Component etc.
    excludeFilters = {
        // Exclude MetricCollector impls that are NOT @Monitored
        @ComponentScan.Filter(
            type    = FilterType.ASSIGNABLE_TYPE,
            classes = MetricCollector.class   // first exclude ALL MetricCollectors…
        )
    },
    includeFilters = {
        // …then re-include the @Monitored ones
        @ComponentScan.Filter(
            type    = FilterType.CUSTOM,
            classes = MonitoredFilter.class
        )
    }
)
class CorrectCfg {}

public class FiltersCustom {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CorrectCfg.class);
        System.out.println("DbMetric:      " + ctx.containsBean("dbMetricCollector"));      // true
        System.out.println("CacheMetric:   " + ctx.containsBean("cacheMetricCollector"));   // true
        System.out.println("UtilityMetric: " + ctx.containsBean("utilityMetricCollector")); // false
        ctx.getBean(MetricsDashboard.class).display();
        ctx.close();
    }
}
```

How to run: `java FiltersCustom.java`

The custom `MonitoredFilter` checks `@Monitored` via `MetadataReader` (no class loading). The scan excludes all `MetricCollector` implementors first, then re-includes only those that pass the custom filter — a two-step include/exclude pattern for precise control.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context created from `CorrectCfg`** — `ClassPathBeanDefinitionScanner` processes filters.
2. **Exclude filter (`ASSIGNABLE_TYPE = MetricCollector`)** — removes all classes implementing `MetricCollector` from candidate set: `DbMetricCollector`, `CacheMetricCollector`, `UtilityMetricCollector` all excluded.
3. **Include filter (`CUSTOM = MonitoredFilter`)** — scans the excluded set; for each class, calls `MonitoredFilter.match(reader, factory)`. `reader.getAnnotationMetadata().isAnnotated("@Monitored")`:
   - `DbMetricCollector` → `@Monitored` present → `match = true` → re-included.
   - `CacheMetricCollector` → `@Monitored` present → re-included.
   - `UtilityMetricCollector` → no `@Monitored` → `match = false` → stays excluded.
4. **`MetricsDashboard`** — registered via default `@Service` filter. `@Autowired List<MetricCollector>` gets `[DbMetricCollector, CacheMetricCollector]` — two beans.
5. **`display()` called** — both metrics printed.

Expected output:
```
DbMetric:      true
CacheMetric:   true
UtilityMetric: false
Monitored metrics (2):
  db.connections=42
  cache.hit_rate=0.87
```

## 7. Gotchas & takeaways

> `includeFilters` and `excludeFilters` interact: **exclude always wins** over include. A class that matches both an include filter and an exclude filter is excluded. Design your filters so they don't overlap.

> `MetadataReader` in a `CUSTOM` filter reads class bytecode metadata — it does NOT load the class. This is intentional and important for performance. Never call `Class.forName(reader.getClassMetadata().getClassName())` inside a TypeFilter — it forces class loading for every scanned file.

- `REGEX` filter matches against the **fully qualified class name**, not just the simple name. Pattern `".*Test"` matches `com.example.UserServiceTest`.
- `ASPECTJ` filter requires the AspectJ weaver on the classpath and matches AspectJ type patterns like `"com.example..*"`.
- `useDefaultFilters = false` + `includeFilters` = only the specified annotations/types are admitted — useful for strict scanning of a non-Spring codebase.
- Multiple filters of the same kind are OR'd within each category: if a class matches any include filter, it's included; if it matches any exclude filter, it's excluded.
