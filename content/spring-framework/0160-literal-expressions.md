---
card: spring-framework
gi: 160
slug: literal-expressions
title: "Literal expressions"
---

## 1. What it is

SpEL literal expressions produce constant values directly from the expression string: strings (single-quoted), integers, longs, hexadecimal integers, real numbers (float/double/BigDecimal with `f`, `d`, suffix), booleans, and `null`. No context or root object is needed.

```java
ExpressionParser parser = new SpelExpressionParser();
parser.parseExpression("'Hello World'").getValue(String.class);  // Hello World
parser.parseExpression("42").getValue(Integer.class);            // 42
parser.parseExpression("true").getValue(Boolean.class);          // true
parser.parseExpression("null").getValue();                       // null
```

## 2. Why & when

- **`@Value` defaults** — `@Value("#{null}")` injects `null`; `@Value("#{3.14d}")` injects a `double`.
- **Configuration constants** — embed computed constants in YAML-driven bean setup without a Java constant class.
- **Test expectations** — SpEL-based assertion frameworks evaluate literal expectations inline.
- **Mixed expressions** — literals compose with operators: `"Price: " + product.price` concatenates a string literal with a navigated property.

## 3. Core concept

Literal types in SpEL:

| Type | Syntax | Java type |
|---|---|---|
| String | `'text'` | `String` |
| Integer | `42` | `Integer` |
| Long | `42L` | `Long` |
| Hex integer | `0x2A` | `Integer` |
| Float | `3.14f` | `Float` |
| Double | `3.14` or `3.14d` | `Double` |
| BigDecimal | `3.14e2` (scientific) | `Double` (not BigDecimal) |
| Boolean | `true`, `false` | `Boolean` |
| Null | `null` | `null` |

String literals use **single quotes** only. A literal single-quote inside a string is escaped as two single quotes: `'it''s'` → `it's`. Double-quoted strings are NOT supported by SpEL.

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="15" width="320" height="140" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="36" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">SpEL Literal Expressions</text>
  <line x1="20" y1="44" x2="320" y2="44" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="170" y="59"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">'Hello World'  →  String "Hello World"</text>
  <text x="170" y="73"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">42             →  Integer 42</text>
  <text x="170" y="87"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">42L            →  Long 42</text>
  <text x="170" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">0xFF           →  Integer 255</text>
  <text x="170" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">3.14f          →  Float  3.14</text>
  <text x="170" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">3.14 / 3.14d   →  Double 3.14</text>
  <text x="170" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">true / false / null</text>

  <rect x="375" y="15" width="315" height="140" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="532" y="36" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Usage in Spring annotations</text>
  <line x1="385" y1="44" x2="682" y2="44" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="532" y="59"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Value("#{null}")       → null</text>
  <text x="532" y="73"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Value("#{true}")       → Boolean.TRUE</text>
  <text x="532" y="87"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Value("#{3.14d}")      → 3.14 double</text>
  <text x="532" y="101" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Value("#{'cfg' + env}") → "cfg" + env value</text>
  <text x="532" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Value("#{0xFF}")       → 255</text>
  <text x="532" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">'it''s a fact'  → "it's a fact"</text>
  <text x="532" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(escaped single-quote: '' inside '')</text>
</svg>

SpEL literal types map directly to their Java counterparts; string literals use single quotes exclusively.

## 5. Runnable example

### Level 1 — Basic

Evaluate all literal types standalone.

```java
// SpelLiteralsBasic.java
import org.springframework.expression.spel.standard.*;

public class SpelLiteralsBasic {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        System.out.println(p.parseExpression("'Hello SpEL'").getValue());      // Hello SpEL
        System.out.println(p.parseExpression("'it''s fun'").getValue());       // it's fun
        System.out.println(p.parseExpression("42").getValue());                // 42
        System.out.println(p.parseExpression("42L").getValue());               // 42 (Long)
        System.out.println(p.parseExpression("0xFF").getValue());              // 255
        System.out.println(p.parseExpression("3.14f").getValue());             // 3.14 (Float)
        System.out.println(p.parseExpression("3.14").getValue());              // 3.14 (Double)
        System.out.println(p.parseExpression("3.14d").getValue());             // 3.14 (Double)
        System.out.println(p.parseExpression("true").getValue());              // true
        System.out.println(p.parseExpression("false").getValue());             // false
        System.out.println(p.parseExpression("null").getValue());              // null

        // getValueType without evaluating
        System.out.println(p.parseExpression("'text'").getValueType());        // class java.lang.String
        System.out.println(p.parseExpression("42").getValueType());            // class java.lang.Integer
        System.out.println(p.parseExpression("3.14").getValueType());          // class java.lang.Double
    }
}
```

How to run: `java SpelLiteralsBasic.java`

`getValueType()` returns the inferred Java type without evaluation side effects. `42L` produces a `Long`, not an `Integer`. `0xFF` evaluates to `255` as `Integer`.

### Level 2 — Intermediate

Literal expressions combined with operators and type coercion.

```java
// SpelLiteralsIntermediate.java
import org.springframework.expression.spel.standard.*;

public class SpelLiteralsIntermediate {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        // String concatenation with literal
        System.out.println(p.parseExpression("'Hello, ' + 'World!'").getValue()); // Hello, World!

        // Arithmetic with numeric literals
        System.out.println(p.parseExpression("2 + 3 * 4").getValue());          // 14
        System.out.println(p.parseExpression("10 / 4").getValue());              // 2 (integer division)
        System.out.println(p.parseExpression("10 / 4.0").getValue());            // 2.5 (double division)
        System.out.println(p.parseExpression("10 % 3").getValue());              // 1
        System.out.println(p.parseExpression("2 ^ 8").getValue());               // 256

        // Coerce getValue to specific type
        System.out.println(p.parseExpression("'42'").getValue(Integer.class));   // 42 (string → int)
        System.out.println(p.parseExpression("42").getValue(String.class));      // "42" (int → string)
        System.out.println(p.parseExpression("42").getValue(Long.class));        // 42 (int → long)
        System.out.println(p.parseExpression("42").getValue(Double.class));      // 42.0 (int → double)

        // Hex and float interaction
        System.out.println(p.parseExpression("0x0A + 0x0B").getValue());         // 21
        System.out.println(p.parseExpression("3.14f + 0.01f").getValue());       // 3.15 (approx)
    }
}
```

How to run: `java SpelLiteralsIntermediate.java`

`10 / 4` performs integer division; promote to double with `4.0`. `getValue(Integer.class)` triggers `ConversionService`-backed coercion — `"42"` string parses to `42` Integer.

### Level 3 — Advanced

Literals in `@Value`; literal composition in bean configuration; `getExpressionString` round-trip.

```java
// SpelLiteralsAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;

@Configuration
class LiteralBeanCfg {
    @Bean
    String appVersion() { return "2.5.0"; }
}

@org.springframework.stereotype.Component
class AppSettings {
    @Value("#{null}")
    private String overrideKey;

    @Value("#{true}")
    private boolean debugEnabled;

    @Value("#{3.14d}")
    private double pi;

    @Value("#{42}")
    private int defaultPageSize;

    @Value("#{'v' + '2' + '.0'}")
    private String apiVersion;

    public String getOverrideKey()  { return overrideKey; }
    public boolean isDebugEnabled() { return debugEnabled; }
    public double getPi()           { return pi; }
    public int getDefaultPageSize() { return defaultPageSize; }
    public String getApiVersion()   { return apiVersion; }
}

public class SpelLiteralsAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LiteralBeanCfg.class, AppSettings.class);
        var settings = ctx.getBean(AppSettings.class);

        System.out.println("overrideKey:     " + settings.getOverrideKey());    // null
        System.out.println("debugEnabled:    " + settings.isDebugEnabled());    // true
        System.out.println("pi:              " + settings.getPi());             // 3.14
        System.out.println("defaultPageSize: " + settings.getDefaultPageSize()); // 42
        System.out.println("apiVersion:      " + settings.getApiVersion());     // v2.0

        // Expression round-trip
        ExpressionParser parser = new SpelExpressionParser();
        Expression e = parser.parseExpression("'Hello' + ' ' + 'World'");
        System.out.println("source:  " + e.getExpressionString()); // 'Hello' + ' ' + 'World'
        System.out.println("result:  " + e.getValue());             // Hello World

        ctx.close();
    }
}
```

How to run: `java SpelLiteralsAdvanced.java`

`@Value("#{null}")` injects a literal `null` — distinct from `@Value("${missing.key:}")` which injects an empty string. `#{'v' + '2' + '.0'}` concatenates three string literals at application startup. `getExpressionString()` returns the original source text, useful for logging and debugging.

## 6. Walkthrough

Execution for `p.parseExpression("10 / 4.0").getValue()` in Level 2:

1. `SpelExpressionParser` lexes tokens: `10` (INT), `/` (OP), `4.0` (REAL).
2. AST: `OpDivide(IntLiteral(10), RealLiteral(4.0))`.
3. `getValue()`: evaluates `IntLiteral(10)` → `Integer(10)`; evaluates `RealLiteral(4.0)` → `Double(4.0)`.
4. `OpDivide` coerces `Integer(10)` to `Double(10.0)` (widening) before division.
5. `10.0 / 4.0` = `2.5` → returned as `Double`.

## 7. Gotchas & takeaways

> SpEL uses **single quotes** for string literals. `"hello"` is not a string literal — it is parsed as an identifier, which causes an `EvaluationException` when no property named `hello` exists. Always use `'hello'`.

> `null` in SpEL is a literal, not an identifier. `null == null` evaluates to `true`. Navigation on `null` (e.g., `null.length()`) throws `EvaluationException` unless safe navigation `?.` is used.

- `42` is always `Integer`; use `42L` for `Long`. If a property expects `Long`, SpEL's type coercion via `ConversionService` converts `Integer` → `Long` automatically when `getValue(Long.class)` is used.
- Hex literals (`0xFF`) parse as `Integer`. There is no hex `Long` literal syntax in SpEL.
- Scientific notation like `1.5e3` evaluates to `1500.0` as `Double`, not `BigDecimal`. For precise decimal arithmetic in configuration, inject the value as a `String` and convert explicitly in the bean.
