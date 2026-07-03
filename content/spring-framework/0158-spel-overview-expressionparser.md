---
card: spring-framework
gi: 158
slug: spel-overview-expressionparser
title: "SpEL overview & ExpressionParser"
---

## 1. What it is

Spring Expression Language (SpEL) is a powerful expression language that supports querying and manipulating an object graph at runtime. `ExpressionParser` parses a SpEL expression string into an `Expression` object, which can then be evaluated against a context. SpEL is used inside Spring configuration annotations (`@Value`, `@ConditionalOnExpression`), Spring Security (`@PreAuthorize`), and Spring Data (`@Query`).

```java
ExpressionParser parser = new SpelExpressionParser();
Expression expr = parser.parseExpression("'Hello, ' + name.toUpperCase()");
String result = expr.getValue(context, String.class);
```

## 2. Why & when

- **`@Value` expressions** — `@Value("#{systemProperties['user.home']}")` reads a JVM system property; `@Value("#{config.timeout * 1000}")` computes a derived value.
- **Dynamic configuration** — evaluate expressions built from runtime data without compiling new code.
- **Object graph navigation** — `order.customer.address.city` traverses nested properties safely.
- **Collection projections and selections** — filter or transform lists inline: `members.?[age > 18]`, `members.![name]`.
- **Security annotations** — `@PreAuthorize("hasRole('ADMIN') and #order.owner == authentication.name")`.

## 3. Core concept

Key SpEL constructs:

| Expression type | Syntax | Example |
|---|---|---|
| Property access | `.property` | `'hello'.bytes` |
| Method call | `.method(args)` | `'hello'.toUpperCase()` |
| Arithmetic | `+`, `-`, `*`, `/`, `%`, `^` | `2 ^ 10` |
| Comparison | `==`, `!=`, `<`, `>`, `<=`, `>=`, `instanceof` | `age >= 18` |
| Logical | `and`, `or`, `not`, `!` | `active and verified` |
| Conditional | `condition ? a : b` | `age >= 18 ? 'adult' : 'minor'` |
| Elvis | `a ?: b` | `name ?: 'Anonymous'` |
| Safe navigation | `?.` | `order?.customer?.name` |
| Collection filter | `.?[predicate]` | `list.?[price > 10]` |
| Collection project | `.![field]` | `list.![name]` |
| Bean reference | `@beanName` | `@myService.doWork()` |
| Type reference | `T(FQN)` | `T(Math).PI` |
| Constructor | `new FQN(args)` | `new java.util.Date()` |

`SpelExpressionParser` is thread-safe. `Expression` objects are also thread-safe and can be cached. Evaluation via `getValue(context)` or `getValue(rootObject, resultType)`.

## 4. Diagram

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg">
  <!-- Expression string -->
  <rect x="10" y="25" width="170" height="35" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="95" y="40" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Expression string</text>
  <text x="95" y="53" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-family="monospace">"members.?[age &gt; 18].![name]"</text>

  <!-- SpelExpressionParser -->
  <rect x="230" y="18" width="160" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="310" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">SpelExpressionParser</text>
  <text x="310" y="52" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">parseExpression(str)</text>
  <text x="310" y="62" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">→ Expression (AST)</text>

  <!-- Expression -->
  <rect x="440" y="18" width="130" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="505" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Expression</text>
  <text x="505" y="52" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getValue(ctx)</text>
  <text x="505" y="62" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">setValue(ctx, val)</text>

  <!-- EvaluationContext -->
  <rect x="10" y="95" width="245" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="132" y="115" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">EvaluationContext</text>
  <text x="132" y="130" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">root object (the "it" of navigation)</text>
  <text x="132" y="143" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">variables: setVariable("x", value)</text>
  <text x="132" y="156" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">functions, bean resolver</text>

  <!-- Result -->
  <rect x="580" y="18"  width="112" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="636" y="38" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Result value</text>
  <text x="636" y="52" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">List&lt;String&gt;</text>
  <text x="636" y="63" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">["Alice", "Bob"]</text>

  <defs>
    <marker id="a158" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="182" y1="42" x2="227" y2="42" stroke="#6db33f" stroke-width="2" marker-end="url(#a158)"/>
  <line x1="402" y1="42" x2="437" y2="42" stroke="#6db33f" stroke-width="2" marker-end="url(#a158)"/>
  <line x1="572" y1="42" x2="577" y2="42" stroke="#6db33f" stroke-width="2" marker-end="url(#a158)"/>
  <!-- Context feeds into Expression eval -->
  <line x1="257" y1="120" x2="505" y2="70" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="5,3" marker-end="url(#a158)"/>

  <text x="350" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">SpelExpressionParser is thread-safe; Expression is compiled to AST once, evaluated many times</text>
</svg>

SpEL compiles expression strings to ASTs once; evaluation is fast and thread-safe.

## 5. Runnable example

### Level 1 — Basic

Parse and evaluate simple SpEL expressions without a context.

```java
// SpelBasic.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;

public class SpelBasic {
    public static void main(String[] args) {
        ExpressionParser parser = new SpelExpressionParser();

        // Literal and arithmetic
        System.out.println(parser.parseExpression("2 + 3 * 4").getValue());          // 14
        System.out.println(parser.parseExpression("2 ^ 10").getValue());              // 1024
        System.out.println(parser.parseExpression("'hello'.toUpperCase()").getValue()); // HELLO
        System.out.println(parser.parseExpression("'hello'.bytes.length").getValue()); // 5

        // Comparison and logical
        System.out.println(parser.parseExpression("3 > 2 and 1 != 2").getValue());    // true
        System.out.println(parser.parseExpression("'abc' instanceof T(String)").getValue()); // true

        // Conditional and Elvis
        System.out.println(parser.parseExpression("5 > 3 ? 'yes' : 'no'").getValue()); // yes
        System.out.println(parser.parseExpression("null ?: 'default'").getValue());    // default
        System.out.println(parser.parseExpression("'provided' ?: 'default'").getValue()); // provided

        // Type access
        System.out.println(parser.parseExpression("T(Math).PI").getValue());           // 3.14...
        System.out.println(parser.parseExpression("T(Integer).MAX_VALUE").getValue()); // 2147483647

        // List literal
        System.out.println(parser.parseExpression("{1, 2, 3, 4}").getValue());         // [1, 2, 3, 4]
    }
}
```

How to run: `java SpelBasic.java` (requires `spring-expression` on classpath)

`parseExpression(str).getValue()` without a context evaluates against no root object. String method calls like `'hello'.bytes` access the underlying `String` object's `bytes` field. `T(ClassName)` gives access to static members.

### Level 2 — Intermediate

`StandardEvaluationContext` with root object and variables; object graph navigation; safe navigation.

```java
// SpelIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Address { public String city; public String zip;
    Address(String city, String zip) { this.city = city; this.zip = zip; } }
class Customer { public String name; public int age; public Address address;
    Customer(String name, int age, Address address) {
        this.name = name; this.age = age; this.address = address; } }
class Order {
    public String id;
    public Customer customer;
    public List<String> items;
    public double total;
    Order(String id, Customer c, List<String> items, double total) {
        this.id = id; this.customer = c; this.items = items; this.total = total; }
}

public class SpelIntermediate {
    public static void main(String[] args) {
        ExpressionParser parser = new SpelExpressionParser();
        StandardEvaluationContext ctx = new StandardEvaluationContext();

        Order order = new Order(
            "ORD-001",
            new Customer("Alice", 30, new Address("Boston", "02101")),
            List.of("Widget", "Gadget", "Doohickey"),
            249.99);

        ctx.setRootObject(order);
        ctx.setVariable("discount", 0.10);

        // Object graph navigation
        System.out.println(parser.parseExpression("id").getValue(ctx));
        System.out.println(parser.parseExpression("customer.name").getValue(ctx));
        System.out.println(parser.parseExpression("customer.address.city").getValue(ctx));

        // Method calls on the root object
        System.out.println(parser.parseExpression("items.size()").getValue(ctx));
        System.out.println(parser.parseExpression("items[1]").getValue(ctx)); // Gadget

        // Variables
        System.out.println(parser.parseExpression("total * (1 - #discount)").getValue(ctx, Double.class));

        // Safe navigation — no NPE if customer is null
        ctx.setRootObject(new Order("ORD-002", null, List.of(), 0));
        System.out.println(parser.parseExpression("customer?.name").getValue(ctx)); // null, not NPE

        // Collection operations
        List<Customer> members = List.of(
            new Customer("Bob", 16, null),
            new Customer("Alice", 25, null),
            new Customer("Charlie", 40, null));
        ctx.setRootObject(members);
        // filter: members where age >= 18
        System.out.println(parser.parseExpression("?[age >= 18]").getValue(ctx, List.class));
        // project: extract names
        System.out.println(parser.parseExpression("![name]").getValue(ctx, List.class));
    }
}
```

How to run: `java SpelIntermediate.java`

`ctx.setRootObject(order)` makes `order` the implicit `this` of expression evaluation. `#discount` refers to the variable registered with `setVariable`. `?.` (safe navigation) returns `null` instead of throwing `NullPointerException` when a path segment is null.

### Level 3 — Advanced

`SpelParserConfiguration` with null-safe and auto-grow modes; expression compilation; write values via `setValue`.

```java
// SpelAdvanced.java
import org.springframework.expression.*;
import org.springframework.expression.spel.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Config {
    public Map<String, Object> settings = new HashMap<>();
    public List<String> tags = new ArrayList<>();
    public String description;

    public Map<String, Object> getSettings() { return settings; }
    public List<String> getTags()            { return tags; }
    public String getDescription()           { return description; }
    public void setDescription(String v)     { this.description = v; }
}

public class SpelAdvanced {
    public static void main(String[] args) {
        // Auto-grow null references and collections
        SpelParserConfiguration config = new SpelParserConfiguration(
            SpelCompilerMode.OFF,   // or IMMEDIATE/MIXED for compiled expressions
            SpelAdvanced.class.getClassLoader());
        ExpressionParser parser = new SpelExpressionParser(config);

        StandardEvaluationContext ctx = new StandardEvaluationContext();
        Config cfg = new Config();
        ctx.setRootObject(cfg);

        // Write via setValue
        parser.parseExpression("description").setValue(ctx, "My Config");
        System.out.println("description: " + cfg.getDescription()); // My Config

        // Map write
        parser.parseExpression("settings['timeout']").setValue(ctx, 30);
        parser.parseExpression("settings['retries']").setValue(ctx, 3);
        System.out.println("settings: " + cfg.getSettings()); // {timeout=30, retries=3}

        // List append / index
        parser.parseExpression("tags").setValue(ctx, new ArrayList<>(List.of("prod", "v2")));
        System.out.println("tags[0]: " + parser.parseExpression("tags[0]").getValue(ctx)); // prod

        // Type coercion — expression returns int, getValue forces String
        ExpressionParser p2 = new SpelExpressionParser();
        StandardEvaluationContext ctx2 = new StandardEvaluationContext();
        ctx2.setRootObject(Map.of("x", 42, "y", 8));
        System.out.println(p2.parseExpression("x + y").getValue(ctx2, String.class)); // "50"

        // getExpressionString — recover source text
        Expression e = p2.parseExpression("x * 2");
        System.out.println("source: " + e.getExpressionString()); // x * 2

        // getValueType — type inference before evaluation
        System.out.println("type: " + p2.parseExpression("'hello'").getValueType()); // class java.lang.String
    }
}
```

How to run: `java SpelAdvanced.java`

`setValue(ctx, value)` writes back through the same property path used for reading — `settings['timeout']` calls `settings.put("timeout", value)`. `SpelCompilerMode.IMMEDIATE` compiles the expression to bytecode on first evaluation for repeated high-throughput use. `getValueType()` returns the result type without evaluating the expression side effects.

## 6. Walkthrough

Execution trace for `parser.parseExpression("?[age >= 18]").getValue(ctx, List.class)` in Level 2:

1. `SpelExpressionParser` lexes and parses `"?[age >= 18]"` → AST with `SelectionFirst` node and predicate `age >= 18`.
2. `getValue(ctx, List.class)` invokes the AST against `ctx.rootObject` (the `List<Customer>`).
3. `SelectionFirst` iterates each element; for each `Customer`, evaluates `age >= 18` with the element as the current context object.
4. Bob (age 16): `false` → excluded. Alice (25): `true` → included. Charlie (40): `true` → included.
5. Result: `[Alice, Charlie]` as `List<Customer>`, coerced to `List.class`.

## 7. Gotchas & takeaways

> SpEL resolves property names via JavaBeans conventions — `name` resolves to `getName()`. Fields without getters are NOT accessible by default. Use `StandardEvaluationContext.setTypeLocator` or declare public fields if you need direct field access.

> `parseExpression` is thread-safe and cheap. `Expression.getValue` evaluation is thread-safe when used with independent `EvaluationContext` instances per thread. Never share a mutable `EvaluationContext` across threads.

- `?[predicate]` returns all matching elements; `^[predicate]` returns the first match; `$[predicate]` returns the last match. `![projection]` projects over all elements.
- `T(com.example.Foo)` references must use the fully qualified class name. Short names are not resolved unless a type locator is configured.
- In `@Value("#{...}")`, the root object is the Spring `Environment`; `@beanName` references are resolved via the `ApplicationContext`. Variables like `#systemProperties` are pre-registered.
- Compiled SpEL (`SpelCompilerMode.IMMEDIATE`) is up to 100x faster for expressions evaluated millions of times, but compilation only succeeds when all types are known at first evaluation. Use `MIXED` mode to fall back gracefully to interpreted mode when compilation fails.
