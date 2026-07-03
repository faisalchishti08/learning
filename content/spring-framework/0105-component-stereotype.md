---
card: spring-framework
gi: 105
slug: component-stereotype
title: "@Component stereotype"
---

## 1. What it is

`@Component` is Spring's generic stereotype annotation that marks a class as a **Spring-managed bean**. When component scanning is active, Spring automatically discovers `@Component`-annotated classes, creates instances, and registers them in the application context — no XML or `@Bean` method required.

It is the base annotation from which all other stereotypes (`@Service`, `@Repository`, `@Controller`) are derived.

## 2. Why & when

Before stereotypes and component scanning, every bean had to be declared manually in XML or a `@Configuration` class. `@Component` + `@ComponentScan` automates discovery: annotate a class, and Spring finds it.

Use `@Component` when the class doesn't fit a more specific role:
- Utility helpers (formatters, parsers, converters).
- Cross-cutting infrastructure beans not specific to data, service, or web layers.
- Framework extension points.

For classes with clear roles, prefer the specific stereotypes: `@Service` for business logic, `@Repository` for data access, `@Controller` for web controllers — they carry the same registration behaviour but communicate intent.

## 3. Core concept

`@Component` tells the component scanner to instantiate the class and register it with a generated or specified bean name. The default name is the class name with the first letter lowercased: `PaymentHelper` → `"paymentHelper"`.

You can specify a name: `@Component("myHelper")`.

`@Component` itself is a `@Target(TYPE)` annotation — it goes on the class, not on methods or fields. It only works if a `@ComponentScan` is active (or `<context:component-scan>` in XML) pointing at the package containing the class.

Spring uses `ClassPathBeanDefinitionScanner` to scan the classpath for classes annotated with `@Component` (or annotations meta-annotated with `@Component`). Each discovered class becomes a `BeanDefinition` in the factory.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Source class -->
  <rect x="10" y="60" width="160" height="64" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="84" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Component</text>
  <text x="90" y="100" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">MyHelper.java</text>
  <text x="90" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">on classpath</text>

  <!-- Scanner -->
  <rect x="265" y="60" width="175" height="64" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="352" y="84" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@ComponentScan</text>
  <text x="352" y="100" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ClassPathBean</text>
  <text x="352" y="114" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">DefinitionScanner</text>

  <!-- Context -->
  <rect x="535" y="60" width="150" height="64" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="610" y="84" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">AppContext</text>
  <text x="610" y="100" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">bean: myHelper</text>
  <text x="610" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">singleton, managed</text>

  <line x1="172" y1="92" x2="262" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#a105)"/>
  <line x1="442" y1="92" x2="532" y2="92" stroke="#79c0ff" stroke-width="2" marker-end="url(#b105)"/>
  <defs>
    <marker id="a105" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b105" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="165" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@ComponentScan finds @Component classes → registers BeanDefinitions → context manages instances</text>
</svg>

`@ComponentScan` drives the scanner that auto-discovers `@Component` classes and registers them.

## 5. Runnable example

### Level 1 — Basic

A simple `@Component` helper discovered and injected without any `@Bean` declaration.

```java
// ComponentBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component
class TextFormatter {
    public String format(String text) {
        return "[" + text.trim().toUpperCase() + "]";
    }
}

@Service
class ReportService {
    @Autowired
    private TextFormatter formatter;

    public void print(String raw) {
        System.out.println(formatter.format(raw));
    }
}

@Configuration
@ComponentScan   // scans the current package by default
class AppCfg {}

public class ComponentBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        ctx.getBean(ReportService.class).print("  hello world  ");
        // Verify bean name
        System.out.println("Bean name: " + ctx.getBeanNamesForType(TextFormatter.class)[0]);
        ctx.close();
    }
}
```

How to run: `java ComponentBasic.java`

`TextFormatter` is found by the scanner, registered as `"textFormatter"` (class name, first letter lower-cased), and injected into `ReportService`. No XML or `@Bean` method needed.

### Level 2 — Intermediate

Custom bean name, multiple `@Component` classes, and showing the default singleton scope.

```java
// ComponentNamed.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component("csvFormatter")       // explicit bean name
class CsvFormatterHelper {
    public String format(Object... values) {
        return String.join(",", java.util.Arrays.stream(values)
            .map(Object::toString).toArray(String[]::new));
    }
}

@Component   // default name: "jsonFormatterHelper"
class JsonFormatterHelper {
    public String format(String key, Object value) {
        return "{\"" + key + "\":\"" + value + "\"}";
    }
}

@Service
class ExportService {
    @Autowired private CsvFormatterHelper  csvFmt;
    @Autowired private JsonFormatterHelper jsonFmt;

    public void export() {
        System.out.println("CSV:  " + csvFmt.format("Alice", 30, "Engineering"));
        System.out.println("JSON: " + jsonFmt.format("name", "Alice"));
    }
}

@Service
class AuditService {
    @Autowired private CsvFormatterHelper csvFmt;   // same singleton injected

    public void audit(Object... data) {
        System.out.println("AUDIT: " + csvFmt.format(data));
        System.out.println("Same instance? " + (csvFmt.hashCode()));
    }
}

@Configuration
@ComponentScan
class NamedCfg {}

public class ComponentNamed {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(NamedCfg.class);
        var export = ctx.getBean(ExportService.class);
        var audit  = ctx.getBean(AuditService.class);
        export.export();
        audit.audit("Bob", 25, "Marketing");
        // Both services share the same CsvFormatterHelper singleton
        System.out.println("Singleton? " +
            (ctx.getBean(CsvFormatterHelper.class) == ctx.getBean(CsvFormatterHelper.class)));
        ctx.close();
    }
}
```

How to run: `java ComponentNamed.java`

`@Component("csvFormatter")` overrides the default generated name. Both `ExportService` and `AuditService` receive the same `CsvFormatterHelper` singleton.

### Level 3 — Advanced

`@Component` with `@Scope("prototype")`, `@Lazy`, and showing how these interact with the component model.

```java
// ComponentScoped.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Component
@Scope("prototype")   // new instance per getBean() call
class RequestContext {
    private final long id = System.nanoTime();
    private String userId;

    public void setUserId(String uid) { this.userId = uid; }
    public void print() {
        System.out.printf("RequestContext[id=%d, user=%s]%n", id, userId);
    }
}

@Component
@Lazy   // not instantiated until first getBean() or @Autowired reference
class ExpensiveAnalyticsEngine {
    ExpensiveAnalyticsEngine() {
        System.out.println("ExpensiveAnalyticsEngine created (lazy)");
    }
    public String analyse(String event) { return "ANALYSIS:" + event; }
}

@Service
class RequestHandler {
    @Autowired private org.springframework.context.ApplicationContext ctx;
    @Autowired private ExpensiveAnalyticsEngine engine;  // triggers lazy init here

    public void handle(String userId, String event) {
        // Prototype: get a fresh RequestContext per request
        var rc = ctx.getBean(RequestContext.class);
        rc.setUserId(userId);
        rc.print();
        System.out.println(engine.analyse(event));
    }
}

@Configuration
@ComponentScan
class ScopedCfg {}

public class ComponentScoped {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ScopedCfg.class);
        // ExpensiveAnalyticsEngine is lazy — not yet created
        System.out.println("Context ready. Engine not yet created.");
        var handler = ctx.getBean(RequestHandler.class);
        // @Autowired engine reference now triggers lazy init
        handler.handle("alice", "page.view");
        handler.handle("bob",   "purchase");
        ctx.close();
    }
}
```

How to run: `java ComponentScoped.java`

`@Scope("prototype")` means each `ctx.getBean(RequestContext.class)` returns a new instance — different `nanoTime` IDs. `@Lazy` delays `ExpensiveAnalyticsEngine` creation until first use. The log shows "created (lazy)" only when `RequestHandler` is first autowired with the engine.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **`AnnotationConfigApplicationContext` created** — `@ComponentScan` triggers scanning. Finds `RequestContext`, `ExpensiveAnalyticsEngine`, `RequestHandler`.
2. **`RequestContext` BeanDefinition registered** — scope `prototype`. No instance created yet.
3. **`ExpensiveAnalyticsEngine` BeanDefinition registered** — `@Lazy` flag set. No instance created yet.
4. **`RequestHandler` instantiated** — singleton, `@Autowired ApplicationContext ctx` injected. `@Autowired ExpensiveAnalyticsEngine engine` — because it's `@Lazy`, Spring injects a proxy, not the real bean.
5. **`"Context ready."` printed** — engine still not created.
6. **`handler.handle("alice", "page.view")` called** — `engine.analyse(...)` called through the proxy → proxy triggers real `ExpensiveAnalyticsEngine` creation now → `"ExpensiveAnalyticsEngine created (lazy)"` printed.
7. **`ctx.getBean(RequestContext.class)`** — prototype scope: constructor called → new `id` from `nanoTime`. `setUserId("alice")` called. `print()` outputs `[id=X, user=alice]`.
8. **`handler.handle("bob", "purchase")`** — engine already created (singleton), not recreated. Another new `RequestContext` prototype created (different `id`).

Expected output:
```
Context ready. Engine not yet created.
ExpensiveAnalyticsEngine created (lazy)
RequestContext[id=123456789, user=alice]
ANALYSIS:page.view
RequestContext[id=987654321, user=bob]
ANALYSIS:purchase
```

## 7. Gotchas & takeaways

> `@Component` only registers a bean if `@ComponentScan` (or `<context:component-scan>`) covers the package the class is in. A `@Component` in a package outside the scan base is silently ignored. This is the most common "why isn't my bean registered?" cause.

> `@Scope("prototype")` and `@Autowired` together create a problem: the singleton bean gets one prototype instance injected at construction time and reuses it forever. To get a new prototype per call, inject `ApplicationContext` and call `ctx.getBean(...)`, or use `ObjectProvider<T>`.

- Default bean name = class name with first letter lowercased. Override with `@Component("customName")`.
- `@Component` is the root stereotype; `@Service`, `@Repository`, `@Controller` are all `@Component` meta-annotated — they register the same way.
- `@Lazy` on a singleton delays creation until the first dependency injection or explicit `getBean()` call.
- `@Component` on a class that extends `BeanPostProcessor` can cause issues — Spring instantiates BPPs very early, potentially before the rest of the context is ready.
