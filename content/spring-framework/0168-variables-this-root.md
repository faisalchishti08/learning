---
card: spring-framework
gi: 168
slug: variables-this-root
title: "Variables (#this, #root)"
---

## 1. What it is

SpEL expressions can reference named variables using the `#variableName` syntax. Variables are set on the `EvaluationContext` via `ctx.setVariable("name", value)` and read as `#name` in expressions. Two built-in variables are always available: `#root` refers to the root object set on the context; `#this` refers to the current object under evaluation — specifically the current element when iterating inside `.?[]`, `.^[]`, `.$[]`, or `.![]`.

```java
ctx.setVariable("threshold", 100);
ctx.setVariable("label", "WARN");

parser.parseExpression("#threshold * 2").getValue(ctx);          // 200
parser.parseExpression("price > #threshold").getValue(ctx);     // true/false
parser.parseExpression("list.?[#this > #threshold]").getValue(ctx); // filtered
```

## 2. Why & when

- **Parameterised expressions** — pass runtime values into a reusable expression string without embedding literals.
- **`#this` in collection operations** — the only way to reference the current element inside `.?[]` and `.![]` when the element is a scalar (not an object).
- **`#root` for back-reference** — access the root object from inside a nested expression where the active object has shifted to a property or collection element.
- **Security expressions** — `#authentication.name`, `#id`, `#command` in Spring Security SpEL — these are pre-registered variables injected by the security framework.

## 3. Core concept

| Variable | Availability | Meaning |
|---|---|---|
| `#name` | anywhere | value registered with `ctx.setVariable("name", v)` |
| `#root` | anywhere | the root object of the context |
| `#this` | inside `.?[]`, `.^[]`, `.$[]`, `.![]` | the current collection element |
| `#systemProperties` | Spring `@Value` context | `System.getProperties()` map |
| `#systemEnvironment` | Spring `@Value` context | `System.getenv()` map |

Variables are scoped to the `EvaluationContext` instance — not to any individual expression. Setting a variable on a shared context affects all expressions evaluated against it. Create per-request contexts to isolate state.

`#root` is rarely needed when the root object is the implicit subject. It becomes useful when navigating into a property makes the nested object the active subject, and you need to refer back to the root.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg">
  <!-- EvaluationContext -->
  <rect x="10" y="20" width="250" height="145" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="135" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">StandardEvaluationContext</text>
  <line x1="18" y1="50" x2="252" y2="50" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="135" y="65"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rootObject = Order@{...}  ← #root</text>
  <text x="135" y="80"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">variables:</text>
  <text x="135" y="94"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">  "threshold" → 100</text>
  <text x="135" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">  "label"     → "WARN"</text>
  <text x="135" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">  "idx"       → 2</text>
  <text x="135" y="140" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">scoped to this context instance</text>
  <text x="135" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">NOT thread-safe if mutated</text>

  <!-- Expression usage -->
  <rect x="310" y="20" width="270" height="145" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="445" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Expression usage</text>
  <line x1="318" y1="50" x2="572" y2="50" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="445" y="65"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">#threshold          → 100</text>
  <text x="445" y="79"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">price > #threshold  → Boolean</text>
  <text x="445" y="93"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">items[#idx]         → items[2]</text>
  <text x="445" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">#root.status        → root object field</text>
  <text x="445" y="121" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">list.?[#this > 10]  → filter scalars</text>
  <text x="445" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">list.![#this * 2]   → project scalars</text>
  <text x="445" y="152" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">#this = current element in iteration</text>
</svg>

`#name` reads named variables; `#root` is the context root; `#this` is the current iteration element.

## 5. Runnable example

### Level 1 — Basic

Set and read named variables; use `#this` in scalar collection operations.

```java
// SpelVariablesBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

public class SpelVariablesBasic {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        // Set variables
        ctx.setVariable("max", 50);
        ctx.setVariable("label", "ALERT");
        ctx.setVariable("multiplier", 3.0);

        // Read variables
        System.out.println(parser.parseExpression("#max").getValue(ctx));                     // 50
        System.out.println(parser.parseExpression("#label.toLowerCase()").getValue(ctx));    // alert
        System.out.println(parser.parseExpression("10 * #multiplier").getValue(ctx));        // 30.0
        System.out.println(parser.parseExpression("#max > 40 ? 'high' : 'low'").getValue(ctx)); // high

        // #this in scalar list operations
        List<Integer> nums = List.of(5, 15, 25, 35, 45);
        ctx.setRootObject(nums);
        System.out.println(parser.parseExpression("?[#this > #max]").getValue(ctx, List.class)); // []
        ctx.setVariable("max", 20);
        System.out.println(parser.parseExpression("?[#this > #max]").getValue(ctx, List.class)); // [25, 35, 45]
        System.out.println(parser.parseExpression("![#this * #multiplier]").getValue(ctx, List.class)); // [15.0, 45.0, 75.0, 105.0, 135.0]

        // #root
        ctx.setVariable("max", 10);
        System.out.println(parser.parseExpression("#root.size()").getValue(ctx)); // 5 (root is the list)
    }
}
```

How to run: `java SpelVariablesBasic.java`

`#this` refers to each element in `?[]` and `![]`. Updating a variable on the shared context (`ctx.setVariable("max", 20)`) affects all subsequent evaluations on the same context instance.

### Level 2 — Intermediate

`#root` for back-reference; `#this` vs root property; variable as index; chained collection with `#this`.

```java
// SpelVariablesIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Product {
    public String name;
    public double price;
    public String category;
    public boolean available;

    Product(String name, double price, String category, boolean available) {
        this.name = name; this.price = price;
        this.category = category; this.available = available;
    }
    public String getName()      { return name; }
    public double getPrice()     { return price; }
    public String getCategory()  { return category; }
    public boolean isAvailable() { return available; }
}

public class SpelVariablesIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        ctx.setVariable("minPrice", 10.0);
        ctx.setVariable("targetCat", "electronics");
        ctx.setVariable("taxRate", 0.08);
        ctx.setVariable("pickIdx", 1);

        List<Product> products = List.of(
            new Product("Phone",   599.0, "electronics", true),
            new Product("Shirt",     29.0, "clothing",    true),
            new Product("Laptop",  1200.0, "electronics", false),
            new Product("Book",       8.0, "education",   true));
        ctx.setRootObject(products);

        // Filter: available AND price > #minPrice AND category == #targetCat
        System.out.println(parser.parseExpression(
            "?[available and price > #minPrice and category == #targetCat]")
            .getValue(ctx, List.class));
        // → [Phone]

        // Project: name + " ($" + (price * (1 + #taxRate)) + ")"
        System.out.println(parser.parseExpression(
            "![name + ' ($' + price * (1 + #taxRate) + ')']").getValue(ctx, List.class));

        // #this on object element
        System.out.println(parser.parseExpression(
            "?[#this.category == #targetCat].![name]").getValue(ctx, List.class));
        // → [Phone, Laptop]

        // Variable as list index
        System.out.println(parser.parseExpression(
            "[#pickIdx].name").getValue(ctx));  // Shirt (index 1)

        // #root back-reference inside nested navigation
        // In a non-list root, #root == root; useful when object is the root
        var singleCtx = new StandardEvaluationContext();
        singleCtx.setRootObject(products.get(0));  // Phone
        singleCtx.setVariable("globalMin", 100.0);
        System.out.println(parser.parseExpression(
            "price > #globalMin and #root.available").getValue(singleCtx)); // true
    }
}
```

How to run: `java SpelVariablesIntermediate.java`

`#this.category` in `?[#this.category == #targetCat]` is equivalent to `.category` — `#this` explicitly names the current element, useful for clarity. `#root.available` uses `#root` to refer to the singleton root object (`Product Phone`).

### Level 3 — Advanced

Pre-registered Spring variables (`#systemProperties`, `#systemEnvironment`); per-expression variable isolation; mutable variable update.

```java
// SpelVariablesAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

@Configuration
class VarCfg {
    @Bean("settings")
    public Map<String, Object> settings() {
        return Map.of("debug", false, "maxConnections", 10);
    }
}

@org.springframework.stereotype.Component
class EnvAware {
    // Spring pre-registers #systemProperties and #systemEnvironment in @Value context
    @Value("#{systemProperties['java.vendor']}")
    private String javaVendor;

    @Value("#{systemEnvironment['HOME'] ?: '/tmp'}")
    private String homeDir;

    @Value("#{systemProperties['os.name']}")
    private String osName;

    public String getJavaVendor() { return javaVendor; }
    public String getHomeDir()    { return homeDir; }
    public String getOsName()     { return osName; }
}

public class SpelVariablesAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(VarCfg.class, EnvAware.class);
        var env = ctx.getBean(EnvAware.class);

        System.out.println("javaVendor: " + env.getJavaVendor());
        System.out.println("homeDir:    " + env.getHomeDir());
        System.out.println("osName:     " + env.getOsName());

        // Manual per-evaluation variable isolation
        var parser = new SpelExpressionParser();
        Expression priceExpr = parser.parseExpression("price * (1 + #vat)");

        double[] prices = {10.0, 25.0, 50.0};
        double[] vatRates = {0.05, 0.10, 0.20};

        for (int i = 0; i < prices.length; i++) {
            var evalCtx = new StandardEvaluationContext();
            evalCtx.setVariable("price", prices[i]);
            evalCtx.setVariable("vat", vatRates[i]);
            // Root object needed for expression to resolve "price" as variable
            System.out.printf("price=%.0f vat=%.0f%% → total=%.2f%n",
                prices[i], vatRates[i]*100,
                parser.parseExpression("#price * (1 + #vat)").getValue(evalCtx, Double.class));
        }

        ctx.close();
    }
}
```

How to run: `java SpelVariablesAdvanced.java`

`#systemProperties['java.vendor']` and `#systemEnvironment['HOME']` are pre-registered by Spring when processing `@Value` annotations — they map to `System.getProperties()` and `System.getenv()`. Creating a fresh `StandardEvaluationContext` per evaluation isolates variables between calls — important for concurrent use.

## 6. Walkthrough

Execution for `"?[#this > #max]"` on list `[5, 15, 25, 35, 45]` with `#max = 20`:

1. `Selection` iterates the list.
2. Element `5`: `#this = 5`, `5 > 20` → false → excluded.
3. Element `15`: `#this = 15`, `15 > 20` → false → excluded.
4. Element `25`: `#this = 25`, `25 > 20` → true → included.
5. Element `35`: `#this = 35`, `35 > 20` → true → included.
6. Element `45`: `#this = 45`, `45 > 20` → true → included.
7. Result: `[25, 35, 45]`.

## 7. Gotchas & takeaways

> `StandardEvaluationContext` is **not thread-safe** when mutated (calling `setVariable`, `setRootObject`). For concurrent scenarios, create a fresh context per thread or per evaluation. Cache the compiled `Expression` objects — they are thread-safe — but not the context.

> Inside `.?[]`, `.![]`, `.^[]`, and `.$[]`, the active object shifts to each element. To access the root during iteration, use `#root` explicitly. Without `#root`, a property reference like `status` resolves against the current element, not the original root.

- Variables set via `ctx.setVariable("name", value)` shadow Java properties of the same name on the root object. If the root has a property `max` and you set `#max` as a variable, `max` (without `#`) resolves to the property, but `#max` resolves to the variable.
- Spring Security pre-registers several variables in its SpEL context: `#authentication` (the `Authentication` object), `#principal`, `#oauth2`, and method argument names (via `#argName` in `@PreAuthorize`).
- `#this` is `null` when evaluating a scalar expression at the top level (not inside a collection operator). Only collection iteration sets `#this` to meaningful values.
