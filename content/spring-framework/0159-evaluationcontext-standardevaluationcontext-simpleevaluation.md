---
card: spring-framework
gi: 159
slug: evaluationcontext-standardevaluationcontext-simpleevaluation
title: "EvaluationContext (StandardEvaluationContext / SimpleEvaluationContext)"
---

## 1. What it is

`EvaluationContext` provides the runtime environment for SpEL expression evaluation. It resolves property access, method calls, variable lookups, and type references. Spring ships two implementations:

- **`StandardEvaluationContext`** — full-featured: supports method calls, bean references (`@myBean`), type access (`T()`), constructors, reflection, and custom functions. Used by default in Spring's annotation processing.
- **`SimpleEvaluationContext`** — intentionally restricted: allows property access and simple operators only. No type access, no constructors, no reflection on arbitrary types. Use for untrusted or user-supplied expressions.

```java
// Trusted internal expression: full context
StandardEvaluationContext full = new StandardEvaluationContext(rootObject);
full.setVariable("multiplier", 3);

// Untrusted user expression: restricted context
SimpleEvaluationContext safe = SimpleEvaluationContext
    .forReadOnlyDataBinding()
    .withRootObject(order)
    .build();
```

## 2. Why & when

- **`StandardEvaluationContext`** — use in framework internals, `@Value` resolution, Spring Security, Spring Data. All SpEL features available.
- **`SimpleEvaluationContext`** — use when expressions come from user input (e.g., configurable filter rules, report column expressions, template fields). Prevents arbitrary code execution via `T(Runtime).exec(...)` attacks.
- **Custom functions** — register a static method as a function via `ctx.registerFunction("myFunc", method)` → callable as `#myFunc(arg)` in expressions.
- **Bean resolver** — `ctx.setBeanResolver(beanFactory)` enables `@myBean` references in expressions.
- **Root object** — set once per context or passed to `getValue(rootObject)` per call; the root object is the implicit subject of unqualified property access.

## 3. Core concept

Capabilities by context type:

| Feature | `StandardEvaluationContext` | `SimpleEvaluationContext` |
|---|---|---|
| Property read | Yes | Yes |
| Property write | Yes | configurable |
| Method calls | Yes | No |
| Type access `T(...)` | Yes | No |
| Constructor `new T(...)` | Yes | No |
| Bean references `@bean` | Yes (with resolver) | No |
| Custom functions `#fn()` | Yes | No |
| Safe use with untrusted input | **No** | **Yes** |

`SimpleEvaluationContext` builders:

| Builder method | Allows |
|---|---|
| `forReadOnlyDataBinding()` | property reads only |
| `forReadWriteDataBinding()` | property reads and writes |

Both can be augmented with `.withConversionService()`, `.withInstanceMethods()`, `.withRootObject()`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- StandardEvaluationContext -->
  <rect x="10" y="15" width="310" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="165" y="38" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">StandardEvaluationContext</text>
  <line x1="20" y1="47" x2="310" y2="47" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="165" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setRootObject(obj)</text>
  <text x="165" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setVariable("x", value) → #x</text>
  <text x="165" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">registerFunction("fn", method) → #fn()</text>
  <text x="165" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setBeanResolver(factory) → @myBean</text>
  <text x="165" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setTypeLocator(...) → T(Foo)</text>
  <text x="165" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setPropertyAccessors([...])</text>
  <text x="165" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">setTypeConverter(...)</text>
  <text x="165" y="162" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">⚠ Do NOT use with untrusted input</text>

  <!-- SimpleEvaluationContext -->
  <rect x="375" y="15" width="310" height="155" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="530" y="38" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">SimpleEvaluationContext</text>
  <line x1="385" y1="47" x2="675" y2="47" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="530" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">forReadOnlyDataBinding()  (builder)</text>
  <text x="530" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">forReadWriteDataBinding() (builder)</text>
  <text x="530" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.withRootObject(obj)</text>
  <text x="530" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.withConversionService(cs)</text>
  <text x="530" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.withInstanceMethods()  (safe methods)</text>
  <text x="530" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.build()</text>
  <text x="530" y="148" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">No T(), no new, no @bean</text>
  <text x="530" y="162" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ Safe for user-supplied expressions</text>
</svg>

`StandardEvaluationContext` is full-featured for trusted code; `SimpleEvaluationContext` is sandboxed for user-supplied expressions.

## 5. Runnable example

### Level 1 — Basic

`StandardEvaluationContext` with root object, variable, and custom function.

```java
// EvaluationContextBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.lang.reflect.*;

class Product {
    public String name;
    public double price;
    public int stock;

    Product(String name, double price, int stock) {
        this.name = name; this.price = price; this.stock = stock;
    }
    public String getName()  { return name; }
    public double getPrice() { return price; }
    public int getStock()    { return stock; }
}

public class EvaluationContextBasic {
    public static double applyDiscount(double price, double pct) {
        return price * (1.0 - pct);
    }

    public static void main(String[] args) throws NoSuchMethodException {
        ExpressionParser parser = new SpelExpressionParser();
        StandardEvaluationContext ctx = new StandardEvaluationContext();

        Product p = new Product("Widget", 100.0, 50);
        ctx.setRootObject(p);

        // Root object property access
        System.out.println(parser.parseExpression("name").getValue(ctx));        // Widget
        System.out.println(parser.parseExpression("price * 1.15").getValue(ctx)); // 115.0

        // Variable
        ctx.setVariable("vatRate", 0.20);
        System.out.println(parser.parseExpression("price * (1 + #vatRate)").getValue(ctx, Double.class)); // 120.0

        // Custom function
        Method m = EvaluationContextBasic.class.getDeclaredMethod("applyDiscount", double.class, double.class);
        ctx.registerFunction("discount", m);
        System.out.println(parser.parseExpression("#discount(price, 0.10)").getValue(ctx, Double.class)); // 90.0

        // Type access
        System.out.println(parser.parseExpression("T(Math).max(price, 50)").getValue(ctx, Double.class)); // 100.0
    }
}
```

How to run: `java EvaluationContextBasic.java`

`setRootObject(p)` makes `name` resolve to `p.getName()`. `setVariable("vatRate", 0.20)` introduces `#vatRate`. `registerFunction("discount", m)` exposes the static method as `#discount(...)`.

### Level 2 — Intermediate

`SimpleEvaluationContext` for user-supplied filter expressions; blocked dangerous expressions.

```java
// EvaluationContextSimple.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;
import java.util.stream.*;

class ReportRow {
    public String region;
    public double revenue;
    public int headcount;

    ReportRow(String region, double revenue, int headcount) {
        this.region = region; this.revenue = revenue; this.headcount = headcount;
    }
    public String getRegion()    { return region; }
    public double getRevenue()   { return revenue; }
    public int getHeadcount()    { return headcount; }
}

public class EvaluationContextSimple {
    static ExpressionParser parser = new SpelExpressionParser();

    // Evaluate a user-supplied filter expression against each row safely
    static List<ReportRow> filter(List<ReportRow> rows, String userFilter) {
        SimpleEvaluationContext ctx = SimpleEvaluationContext
            .forReadOnlyDataBinding()
            .withInstanceMethods()  // allow built-in instance methods like String.startsWith
            .build();

        Expression expr = parser.parseExpression(userFilter);
        return rows.stream()
            .filter(row -> {
                try {
                    return Boolean.TRUE.equals(expr.getValue(ctx, row, Boolean.class));
                } catch (EvaluationException ex) {
                    System.err.println("Filter eval error: " + ex.getMessage());
                    return false;
                }
            })
            .collect(Collectors.toList());
    }

    public static void main(String[] args) {
        List<ReportRow> rows = List.of(
            new ReportRow("EMEA", 500_000, 80),
            new ReportRow("APAC", 300_000, 50),
            new ReportRow("AMER", 750_000, 120));

        // Safe user filter
        var high = filter(rows, "revenue > 400000");
        high.forEach(r -> System.out.println(r.getRegion() + ": " + r.getRevenue()));

        // Another safe filter
        var emea = filter(rows, "region == 'EMEA'");
        emea.forEach(r -> System.out.println("Filtered: " + r.getRegion()));

        // Demonstrate that dangerous expressions are blocked
        System.out.println("\n=== Blocked expression ===");
        try {
            // T(Runtime) is not resolvable in SimpleEvaluationContext
            filter(rows, "T(Runtime).getRuntime().exec('ls')");
            System.out.println("Should not reach here");
        } catch (EvaluationException | SpelEvaluationException e) {
            System.out.println("Blocked: " + e.getMessage());
        } catch (Exception e) {
            System.out.println("Blocked: " + e.getClass().getSimpleName() + " - " + e.getMessage());
        }
    }
}
```

How to run: `java EvaluationContextSimple.java`

`SimpleEvaluationContext.forReadOnlyDataBinding()` restricts evaluation to safe property reads. `T(Runtime)` fails with an `EvaluationException` because type access is not available. Each `getValue(ctx, row, Boolean.class)` call passes `row` as the root object per-element.

### Level 3 — Advanced

`StandardEvaluationContext` with `BeanResolver`; write via `setValue`; `PropertyAccessor` for custom object types.

```java
// EvaluationContextAdvanced.java
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import org.springframework.beans.factory.*;
import java.util.*;

// A simple dynamic map-backed object
class DynamicRecord {
    private final Map<String, Object> data = new HashMap<>();
    public void set(String key, Object value) { data.put(key, value); }
    public Object get(String key)             { return data.get(key); }
    public Map<String, Object> getData()      { return data; }
}

// Custom PropertyAccessor for DynamicRecord
class DynamicRecordAccessor implements PropertyAccessor {
    @Override
    public Class<?>[] getSpecificTargetClasses() { return new Class[]{DynamicRecord.class}; }

    @Override
    public boolean canRead(EvaluationContext ctx, Object target, String name) {
        return target instanceof DynamicRecord;
    }

    @Override
    public TypedValue read(EvaluationContext ctx, Object target, String name) {
        return new TypedValue(((DynamicRecord) target).get(name));
    }

    @Override
    public boolean canWrite(EvaluationContext ctx, Object target, String name) {
        return target instanceof DynamicRecord;
    }

    @Override
    public void write(EvaluationContext ctx, Object target, String name, Object newValue) {
        ((DynamicRecord) target).set(name, newValue);
    }
}

@Configuration
class AppBeans {
    @Bean("config")
    public Map<String, Object> configBean() {
        Map<String, Object> m = new HashMap<>();
        m.put("maxRetries", 5);
        m.put("timeout", 30_000L);
        return m;
    }
}

public class EvaluationContextAdvanced {
    public static void main(String[] args) {
        // Setup Spring context for bean resolver
        var appCtx = new AnnotationConfigApplicationContext(AppBeans.class);

        ExpressionParser parser = new SpelExpressionParser();
        StandardEvaluationContext ctx = new StandardEvaluationContext();

        // Bean resolver — enables @config in expressions
        ctx.setBeanResolver((evalCtx, beanName) -> appCtx.getBean(beanName));

        // Custom PropertyAccessor for DynamicRecord
        ctx.addPropertyAccessor(new DynamicRecordAccessor());

        DynamicRecord record = new DynamicRecord();
        record.set("userId", 42);
        record.set("role", "admin");
        ctx.setRootObject(record);

        // Read via custom accessor
        System.out.println("userId: " + parser.parseExpression("userId").getValue(ctx));     // 42
        System.out.println("role: "   + parser.parseExpression("role").getValue(ctx));       // admin

        // Write via custom accessor
        parser.parseExpression("email").setValue(ctx, "admin@example.com");
        System.out.println("email: " + record.get("email")); // admin@example.com

        // Bean resolver
        @SuppressWarnings("unchecked")
        var configMap = (Map<String, Object>) parser.parseExpression("@config").getValue(ctx);
        System.out.println("@config.maxRetries: " + configMap.get("maxRetries")); // 5

        // Combined: read from bean
        ctx.setVariable("timeout", 10_000L);
        System.out.println(parser.parseExpression("@config['timeout'] > #timeout").getValue(ctx)); // true (30000 > 10000)

        appCtx.close();
    }
}
```

How to run: `java EvaluationContextAdvanced.java`

`DynamicRecordAccessor` implements `PropertyAccessor` to enable SpEL property access on a `Map`-backed type without requiring JavaBeans getters. `ctx.setBeanResolver(...)` enables `@config` syntax to look up Spring beans by name from the `ApplicationContext`.

## 6. Walkthrough

Execution trace for `parser.parseExpression("@config['timeout'] > #timeout").getValue(ctx)` in Level 3:

1. AST root: `ComparisonOperator(>)` with two children.
2. Left child: `Indexer(['timeout'])` on `BeanReference(@config)`.
3. `BeanReference` invokes `ctx.getBeanResolver().resolve(ctx, "config")` → returns the `Map` bean.
4. `Indexer` calls `map.get("timeout")` → `30000L`.
5. Right child: `VariableReference(#timeout)` → `ctx.lookupVariable("timeout")` → `10000L`.
6. `30000L > 10000L` → `true`.

## 7. Gotchas & takeaways

> **Never use `StandardEvaluationContext` with user-supplied expressions in a web-facing endpoint.** SpEL via `T(Runtime).getRuntime().exec(...)`, `T(ProcessBuilder)`, or `T(System).exit(0)` can execute arbitrary system commands. Always use `SimpleEvaluationContext` for any expression string that originates outside trusted code.

> `StandardEvaluationContext` is NOT thread-safe when mutated (adding variables, changing root object). Create one per request/thread or use `getValue(rootObject)` overloads that pass the root object per-call on a shared, immutable context.

- `PropertyAccessor.getSpecificTargetClasses()` returning `null` means the accessor is tried for ALL types — register it last to avoid interfering with built-in accessors. Return the specific class array to limit scope.
- Variables set via `setVariable` are scoped to the `EvaluationContext` instance, not the expression. Two expressions evaluated on the same context share variables, which can cause subtle bugs in multi-threaded scenarios.
- `SimpleEvaluationContext.withInstanceMethods()` enables calling methods defined on the actual root object or target class — it does NOT enable arbitrary `T(ClassName)` method calls.
- When Spring evaluates `@Value("#{...}")` annotations, it uses a pre-configured `StandardEvaluationContext` with `#systemProperties`, `#systemEnvironment`, and a `BeanFactoryResolver` already registered. You get bean references and system properties for free.
