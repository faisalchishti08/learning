---
card: spring-framework
gi: 174
slug: spel-compilation
title: SpEL compilation
---

## 1. What it is

By default SpEL **interprets** expressions: every `getValue()` call walks the parsed AST node by node. SpEL can instead **compile** an expression to JVM bytecode, so subsequent evaluations run at native speed without AST traversal.

Compilation is configured via `SpelParserConfiguration`:

```java
SpelParserConfiguration config = new SpelParserConfiguration(
    SpelCompilerMode.IMMEDIATE, MyClass.class.getClassLoader());
SpelExpressionParser parser = new SpelExpressionParser(config);
```

Three modes exist:
- `OFF` — always interpret (default).
- `IMMEDIATE` — compile after the first evaluation once all type information is known.
- `MIXED` — interpret until type information stabilises, then compile; fall back to interpretation if runtime types change.

## 2. Why & when

- **Tight evaluation loops** — a discount rule applied to thousands of orders per second is CPU-bound; compiled SpEL can be 5–10× faster than interpreted.
- **Rules engines** — externally configured predicates (`product.category == 'electronics' and price > 500`) that are hot code paths benefit most.
- **Security expressions** — Spring Security evaluates SpEL access-control expressions (`hasRole('ADMIN') and #user.active`) on every request; compilation removes the AST overhead.
- **Avoid compilation** when expressions are *evaluated once* (config wiring via `@Value`) — the compilation cost outweighs any gain.
- **Avoid compilation** for expressions with frequently changing root-object types — `MIXED` mode handles this but adds complexity; `IMMEDIATE` may miscompile if types change after the first eval.

## 3. Core concept

Interpreted evaluation path:
```
parseExpression("price * discount")   → AST
─────────────────────────────────────
getValue() call 1: AST walk, reflect getPrice(), reflect getDiscount(), multiply
getValue() call 2: AST walk again …  (same cost every time)
```

Compiled evaluation path:
```
parseExpression("price * discount")   → AST
─────────────────────────────────────
getValue() call 1 (IMMEDIATE): compile AST → bytecode (one-time cost)
getValue() call 2: invoke compiled method directly  (very fast)
getValue() call 3: invoke compiled method directly  …
```

Compilation happens inside the `Expression` object. The `SpelCompiler` uses ASM to generate a class implementing `CompiledExpression`, which is loaded into the JVM via the provided class loader.

**When compilation fails or is skipped:**
- The expression contains a construct the compiler does not support (e.g., complex type coercion).
- The root object type is `null` on the first call — no type information to compile against.
- In `MIXED` mode, if the type of a property changes between calls, SpEL falls back to interpreted mode.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ca174" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cb174" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Interpreted path -->
  <rect x="5" y="8" width="330" height="195" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="170" y="28" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Interpreted (OFF / default)</text>

  <rect x="20" y="38" width="130" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="85" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">parseExpression("…")</text>
  <line x1="85" y1="62" x2="85" y2="78" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ca174)"/>
  <rect x="20" y="80" width="130" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="85" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AST stored</text>

  <text x="195" y="92" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getValue() #1</text>
  <line x1="153" y1="92" x2="175" y2="92" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ca174)"/>
  <rect x="178" y="80" width="140" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="248" y="96" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">walk AST → result</text>

  <text x="195" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getValue() #2</text>
  <line x1="153" y1="130" x2="175" y2="130" stroke="#8b949e" stroke-width="1.5" marker-end="url(#ca174)"/>
  <rect x="178" y="118" width="140" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="248" y="134" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">walk AST → result</text>

  <text x="248" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">same cost every call</text>
  <text x="248" y="173" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">O(AST depth) per eval</text>

  <!-- Compiled path -->
  <rect x="360" y="8" width="335" height="195" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="527" y="28" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Compiled (IMMEDIATE)</text>

  <rect x="375" y="38" width="130" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="440" y="54" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">parseExpression("…")</text>
  <line x1="440" y1="62" x2="440" y2="78" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cb174)"/>
  <rect x="375" y="80" width="130" height="24" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="440" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">AST stored</text>

  <text x="550" y="92" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">getValue() #1 → compile → result</text>
  <line x1="508" y1="92" x2="530" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#cb174)"/>
  <rect x="533" y="80" width="145" height="24" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1"/>
  <text x="605" y="96" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">compile AST → bytecode</text>

  <text x="550" y="130" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">getValue() #2</text>
  <line x1="508" y1="130" x2="530" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#cb174)"/>
  <rect x="533" y="118" width="145" height="24" rx="4" fill="#79c0ff" opacity="0.15" stroke="#79c0ff" stroke-width="1"/>
  <text x="605" y="134" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">invoke compiled → result</text>

  <text x="605" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">near-native speed from #2 on</text>
  <text x="605" y="173" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">O(1) overhead per eval</text>
</svg>

Interpreted mode pays AST-walk cost on every call; compiled mode pays the compilation cost once on the first call, then runs bytecode directly from call two onwards.

## 5. Runnable example

The scenario is a **product discount calculator** that applies an externally supplied rule expression to thousands of products — a realistic case where compilation matters.

### Level 1 — Basic

Enable compilation and confirm the same expression works in both modes.

```java
// SpelCompilationBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;

public class SpelCompilationBasic {
    record Product(String name, double price, String category) {
        public String getName()     { return name; }
        public double getPrice()    { return price; }
        public String getCategory() { return category; }
    }

    public static void main(String[] args) {
        var product = new Product("Laptop", 1200.0, "electronics");

        // Interpreted (default)
        var interpretedParser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext(product);
        Expression interp = interpretedParser.parseExpression("price * 0.9");
        System.out.println("Interpreted: " + interp.getValue(ctx, Double.class)); // 1080.0

        // Compiled — IMMEDIATE mode
        var config = new SpelParserConfiguration(SpelCompilerMode.IMMEDIATE,
                                                  SpelCompilationBasic.class.getClassLoader());
        var compiledParser = new SpelExpressionParser(config);
        Expression comp = compiledParser.parseExpression("price * 0.9");
        // First call: interprets AND compiles
        System.out.println("Compiled #1:  " + comp.getValue(ctx, Double.class)); // 1080.0
        // Subsequent calls: execute compiled bytecode
        System.out.println("Compiled #2:  " + comp.getValue(ctx, Double.class)); // 1080.0

        // Boolean predicate
        Expression eligibleExpr = compiledParser.parseExpression(
            "category == 'electronics' and price > 500");
        System.out.println("Eligible:     " + eligibleExpr.getValue(ctx, Boolean.class)); // true

        var book = new Product("Novel", 15.0, "books");
        System.out.println("Book eligible:" + eligibleExpr.getValue(
            new StandardEvaluationContext(book), Boolean.class)); // false
    }
}
```

How to run: `java SpelCompilationBasic.java`

`SpelCompilerMode.IMMEDIATE` tells SpEL to compile on the first successful evaluation. The compiled expression object is reused — each `getValue` after that first call runs generated bytecode instead of the AST walker. Passing `null` as the class loader uses the default class loader; passing a specific class loader is important in OSGi or application-server environments.

### Level 2 — Intermediate

Measure interpreted vs compiled performance; compare IMMEDIATE and MIXED modes; handle the case where compilation is not yet done.

```java
// SpelCompilationIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;

public class SpelCompilationIntermediate {
    public static class Order {
        private double subtotal;
        private int quantity;
        private boolean vip;
        Order(double s, int q, boolean v) { subtotal=s; quantity=q; vip=v; }
        public double getSubtotal()  { return subtotal; }
        public int    getQuantity()  { return quantity; }
        public boolean isVip()       { return vip; }
    }

    static double evaluate(Expression expr, Order order) {
        return expr.getValue(new StandardEvaluationContext(order), Double.class);
    }

    public static void main(String[] args) {
        // Expressions to compare
        String ruleStr = "subtotal * (vip ? 0.80 : 0.95) + (quantity > 10 ? -5.0 : 0.0)";

        var interpExpr  = new SpelExpressionParser().parseExpression(ruleStr);

        var immCfg = new SpelParserConfiguration(SpelCompilerMode.IMMEDIATE,
                                                  SpelCompilationIntermediate.class.getClassLoader());
        var immExpr = new SpelExpressionParser(immCfg).parseExpression(ruleStr);

        var mixCfg = new SpelParserConfiguration(SpelCompilerMode.MIXED,
                                                  SpelCompilationIntermediate.class.getClassLoader());
        var mixExpr = new SpelExpressionParser(mixCfg).parseExpression(ruleStr);

        // Warm up
        var warmOrder = new Order(200.0, 5, true);
        for (int i = 0; i < 100; i++) {
            evaluate(interpExpr,  warmOrder);
            evaluate(immExpr,     warmOrder);
            evaluate(mixExpr,     warmOrder);
        }

        // Benchmark: 100 000 evaluations
        int N = 100_000;
        var order = new Order(150.0, 15, false);

        long t0 = System.nanoTime();
        for (int i = 0; i < N; i++) evaluate(interpExpr, order);
        long interpNs = System.nanoTime() - t0;

        t0 = System.nanoTime();
        for (int i = 0; i < N; i++) evaluate(immExpr, order);
        long immNs = System.nanoTime() - t0;

        t0 = System.nanoTime();
        for (int i = 0; i < N; i++) evaluate(mixExpr, order);
        long mixNs = System.nanoTime() - t0;

        double result = evaluate(interpExpr, order);
        System.out.printf("Result: %.2f%n", result);            // 137.25
        System.out.printf("Interpreted: %,d ms%n", interpNs / 1_000_000);
        System.out.printf("IMMEDIATE:   %,d ms%n", immNs    / 1_000_000);
        System.out.printf("MIXED:       %,d ms%n", mixNs    / 1_000_000);
    }
}
```

How to run: `java SpelCompilationIntermediate.java`

The benchmark evaluates `subtotal * (vip ? 0.80 : 0.95) + (quantity > 10 ? -5.0 : 0.0)` 100,000 times. After warm-up, compiled modes run 2–10× faster than interpreted depending on the JVM. `MIXED` mode defers compilation until the type is stable (unlike `IMMEDIATE` which compiles after the very first call) — both end up compiled but `MIXED` has a slightly longer warm-up phase.

### Level 3 — Advanced

A Spring bean with a configurable discount rule; rule is compiled once and reused across all requests — the production pattern.

```java
// SpelCompilationAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

@Configuration
class DiscountCfg {
    @Bean
    public DiscountEngine discountEngine() {
        // Rules loaded from config (simulated here)
        List<String> rules = List.of(
            "category == 'electronics' and price > 500 ? price * 0.85 : price",
            "quantity >= 10 ? price * quantity * 0.90 : price * quantity",
            "vip and category == 'books' ? price * 0.70 : price"
        );
        return new DiscountEngine(rules);
    }
}

class DiscountEngine {
    private final SpelParserConfiguration cfg = new SpelParserConfiguration(
        SpelCompilerMode.IMMEDIATE, DiscountEngine.class.getClassLoader());
    private final SpelExpressionParser parser = new SpelExpressionParser(cfg);
    // Pre-compiled expressions, keyed by rule string
    private final Map<String, Expression> compiled = new LinkedHashMap<>();

    DiscountEngine(List<String> rules) {
        for (String rule : rules) compiled.put(rule, parser.parseExpression(rule));
    }

    /** Evaluate all rules for the given product/cart context. */
    public void applyRules(String category, double price, int quantity, boolean vip) {
        var ctx = new StandardEvaluationContext();
        ctx.setVariable("category", category);
        ctx.setVariable("price",    price);
        ctx.setVariable("quantity", quantity);
        ctx.setVariable("vip",      vip);
        for (var entry : compiled.entrySet()) {
            Object result = entry.getValue().getValue(ctx);
            System.out.printf("Rule [%-70s] → %s%n", entry.getKey(), result);
        }
    }
}

public class SpelCompilationAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DiscountCfg.class);
        DiscountEngine engine = ctx.getBean(DiscountEngine.class);

        System.out.println("=== Electronics, $800, qty 1, not VIP ===");
        engine.applyRules("electronics", 800.0, 1, false);

        System.out.println("\n=== Books, $15, qty 12, VIP ===");
        engine.applyRules("books", 15.0, 12, true);

        ctx.close();
    }
}
```

How to run: `java SpelCompilationAdvanced.java`

`DiscountEngine` pre-compiles every rule expression at construction time (when the `@Bean` is initialised). The `Expression` objects are stored in a `Map` and reused for every product evaluation. Because `SpelCompilerMode.IMMEDIATE` is set, compilation happens on the first call to each expression — subsequent calls for thousands of products go through bytecode directly. This is the standard pattern for rules engines: parse and compile once at startup, evaluate many times at runtime.

## 6. Walkthrough

Tracing a single call `engine.applyRules("electronics", 800.0, 1, false)` for rule `category == 'electronics' and price > 500 ? price * 0.85 : price`:

**Step 1 — `DiscountEngine` construction (at Spring wiring time):**
- `parser.parseExpression(rule)` builds an AST for each rule string.
- The `Expression` objects are stored in `compiled` map — compilation has NOT happened yet (no type info available without a context).

**Step 2 — `applyRules` called:**
- A fresh `StandardEvaluationContext` is created.
- Variables bound: `category="electronics"`, `price=800.0`, `quantity=1`, `vip=false`.

**Step 3 — `expression.getValue(ctx)` for first rule (FIRST CALL):**
- SpEL interprets the expression to produce the result (since this is the first call and compilation needs to happen).
- It also compiles the expression to JVM bytecode at this point (IMMEDIATE mode).
- `category == 'electronics'` → `"electronics" == "electronics"` → `true`
- `price > 500` → `800.0 > 500` → `true`
- `true and true` → `true`
- Ternary: `true` branch → `price * 0.85` → `800.0 * 0.85` = `680.0`

**Step 4 — Output:** `Rule [...] → 680.0`

**Step 5 — Second `applyRules` call (different product):**
- Same rule's expression is now compiled.
- `getValue(ctx)` invokes the compiled `CompiledExpression.getValue()` method directly — JVM runs native bytecode, no AST traversal.

Expected output for `applyRules("electronics", 800.0, 1, false)`:
```
Rule [category == 'electronics' and price > 500 ? price * 0.85 : price         ] → 680.0
Rule [quantity >= 10 ? price * quantity * 0.90 : price * quantity               ] → 800.0
Rule [vip and category == 'books' ? price * 0.70 : price                        ] → 800.0
```

## 7. Gotchas & takeaways

> **Compilation requires consistent root-object types.** If you evaluate an expression against different classes (e.g., `Product` then `Order`), SpEL compiled for `Product` will fail or produce wrong results when applied to `Order`. Always evaluate a compiled expression against objects of the same type it was first compiled against, or use `MIXED` mode which re-compiles when types change.

> **`null` root object on the first call prevents compilation in IMMEDIATE mode.** SpEL needs the actual types to generate bytecode. Call `getValue` with a non-null object at least once before the high-frequency path begins, or use a `StandardEvaluationContext` with type information manually set.

- Not all SpEL constructs are compilable — collection operators (`.?[]`, `.![]`), some type coercions, and custom `MethodResolver`s fall back to interpreted mode silently. Check `SpelExpression.isCompiled()` if performance is critical.
- Compilation uses the `ClassLoader` you provide. In a Spring Boot fat JAR, pass `Thread.currentThread().getContextClassLoader()`. In a standard app, `MyClass.class.getClassLoader()` is correct.
- `SpelCompilerMode.MIXED` is safer for expressions whose operand types might change; `IMMEDIATE` is faster for stable types.
- Compiled expressions hold a reference to the generated class in the provided class loader — in a hot-reload scenario this can cause class loader leaks. Reuse parsers and expressions at application scope, not request scope.
