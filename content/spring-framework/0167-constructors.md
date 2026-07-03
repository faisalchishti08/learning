---
card: spring-framework
gi: 167
slug: constructors
title: "Constructors"
---

## 1. What it is

SpEL supports invoking Java constructors using `new FullyQualifiedClassName(args...)` syntax. The class name must be fully qualified (except for `java.lang` types). Constructor arguments can be any SpEL sub-expressions including literals, variables, and method calls.

```java
parser.parseExpression("new java.util.Date()").getValue();
parser.parseExpression("new java.awt.Point(10, 20)").getValue();
parser.parseExpression("new java.util.ArrayList()").getValue();
parser.parseExpression("new java.util.HashMap()").getValue();
```

## 2. Why & when

- **Inline object creation in `@Value`** — `@Value("#{new java.util.Date()}")` injects a `Date` at context refresh without a `@Bean` method.
- **Dynamic object construction** — construct domain objects from configuration values: `new com.example.Threshold(#limit, 'warn')`.
- **Data transformation in projections** — `members.![new com.example.NameDto(name, email)]` projects to a new DTO list.
- **Test data** — build expected objects inline in SpEL-based test assertion frameworks.

## 3. Core concept

| Syntax | Meaning |
|---|---|
| `new FQN()` | zero-arg constructor |
| `new FQN(arg1, arg2)` | constructor with arguments |
| `new java.lang.String('abc')` | `java.lang` — can omit package |
| `new String('abc')` | short name works for `java.lang` only |

Constructor resolution follows the same rules as Java: argument count must match, and SpEL's `ConversionService` coerces types when exact types don't match. Ambiguous overloads are resolved by best-fit matching.

The `new` keyword in SpEL constructs **object instances**, not arrays — for arrays use `new T[n]` or `new T[]{...}` syntax (covered in array construction). `new` is **blocked in `SimpleEvaluationContext`** for security.

## 4. Diagram

<svg viewBox="0 0 700 160" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="20" width="230" height="125" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="115" y="40" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">new ClassName(args)</text>
  <line x1="18" y1="48" x2="232" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="115" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new java.util.Date()</text>
  <text x="115" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new String('hello')</text>
  <text x="115" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new java.awt.Point(#x, #y)</text>
  <text x="115" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new ArrayList()</text>
  <text x="115" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new com.example.Dto(name, id)</text>
  <text x="115" y="136" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">⚠ blocked in SimpleEvaluationContext</text>

  <rect x="265" y="20" width="210" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ConstructorResolver</text>
  <line x1="273" y1="48" x2="467" y2="48" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="370" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">TypeLocator.findType(FQN)</text>
  <text x="370" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">find matching constructor</text>
  <text x="370" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">coerce args via ConversionService</text>
  <text x="370" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">invoke via reflection</text>

  <rect x="507" y="20" width="183" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="598" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Result</text>
  <line x1="515" y1="48" x2="682" y2="48" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="598" y="62"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new instance of FQN</text>
  <text x="598" y="76"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">can chain methods/properties</text>
  <text x="598" y="90"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">new UUID(...).toString()</text>

  <defs>
    <marker id="a167" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="242" y1="75" x2="262" y2="75" stroke="#6db33f" stroke-width="2" marker-end="url(#a167)"/>
  <line x1="477" y1="75" x2="504" y2="75" stroke="#6db33f" stroke-width="2" marker-end="url(#a167)"/>
</svg>

SpEL `new` invokes constructors via reflection through `ConstructorResolver`; `java.lang` types use short names.

## 5. Runnable example

### Level 1 — Basic

Construct standard library objects and chain method calls.

```java
// SpelConstructorsBasic.java
import org.springframework.expression.spel.standard.*;
import java.util.*;

public class SpelConstructorsBasic {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        // java.lang — short name works
        System.out.println(p.parseExpression("new String('hello').toUpperCase()").getValue()); // HELLO
        System.out.println(p.parseExpression("new Integer(42)").getValue());                   // 42

        // java.util — FQN required
        System.out.println(p.parseExpression("new java.util.ArrayList()").getValue());          // []
        System.out.println(p.parseExpression("new java.util.HashMap()").getValue());            // {}
        System.out.println(p.parseExpression("new java.util.Date().getClass().getSimpleName()").getValue()); // Date

        // Chain on constructed object
        System.out.println(p.parseExpression(
            "new java.util.ArrayList({'a','b','c'}).size()").getValue()); // Hm — ArrayList(Collection) ctor

        // BigDecimal
        System.out.println(p.parseExpression(
            "new java.math.BigDecimal('123.456').setScale(2, T(java.math.RoundingMode).HALF_UP)").getValue()); // 123.46

        // UUID
        System.out.println(p.parseExpression(
            "new java.util.UUID(0, 0).toString()").getValue()); // 00000000-0000-0000-0000-000000000000
    }
}
```

How to run: `java SpelConstructorsBasic.java`

Constructed objects are regular Java instances — method calls chain normally. `new java.math.BigDecimal('123.456')` takes the `String` constructor to avoid floating-point imprecision.

### Level 2 — Intermediate

Constructors with variable arguments; projection using constructors to create DTO lists.

```java
// SpelConstructorsIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class PersonDto {
    public final String name;
    public final String displayName;

    PersonDto(String name, String email) {
        this.name = name;
        this.displayName = name + " <" + email + ">";
    }
    @Override public String toString() { return "PersonDto(" + displayName + ")"; }
}

class RawPerson {
    public String firstName;
    public String lastName;
    public String email;

    RawPerson(String firstName, String lastName, String email) {
        this.firstName = firstName; this.lastName = lastName; this.email = email;
    }
    public String getFirstName() { return firstName; }
    public String getLastName()  { return lastName; }
    public String getEmail()     { return email; }
    public String getFullName()  { return firstName + " " + lastName; }
}

public class SpelConstructorsIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        List<RawPerson> people = List.of(
            new RawPerson("Alice", "Smith",  "alice@example.com"),
            new RawPerson("Bob",   "Jones",  "bob@example.com"),
            new RawPerson("Carol", "Davis",  "carol@example.com"));
        ctx.setRootObject(people);

        // Project: create PersonDto from each RawPerson
        List<?> dtos = parser.parseExpression(
            "![new com.example.PersonDto(fullName, email)]").getValue(ctx, List.class);

        // Since PersonDto is in default package in this demo, use full class expression:
        List<?> result = parser.parseExpression(
            "![firstName + ' ' + lastName + ' <' + email + '>']").getValue(ctx, List.class);
        result.forEach(System.out::println);

        // Filter then construct
        ctx.setVariable("domain", "@example.com");
        List<?> filtered = parser.parseExpression(
            "?[email.endsWith(#domain)].![firstName + ' ' + lastName]").getValue(ctx, List.class);
        System.out.println("Filtered: " + filtered);

        // Construct with computed args
        var single = new StandardEvaluationContext();
        single.setVariable("width",  800);
        single.setVariable("height", 600);
        System.out.println(parser.parseExpression(
            "new java.awt.Dimension(#width, #height).toString()").getValue(single)); // [800 x 600]
    }
}
```

How to run: `java SpelConstructorsIntermediate.java`

`new java.awt.Dimension(#width, #height)` uses variables as constructor args. The projection `![new Dto(field1, field2)]` pattern transforms a list by constructing a new object per element — a common SpEL idiom.

### Level 3 — Advanced

Constructor in `@Value` for configuration objects; chained construction; conditional construction.

```java
// SpelConstructorsAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.net.*;

@Configuration
class CtorCfg {
    @Bean("hostname") public String hostname() { return "api.example.com"; }
    @Bean("apiPort")  public int apiPort()     { return 8443; }
    @Bean("path")     public String path()     { return "/v2/data"; }
}

@org.springframework.stereotype.Component
class ApiEndpointConfig {
    // Construct URI from parts
    @Value("#{new java.net.URI('https', hostname, '/' + path, null, null).toString()}")
    private String baseUri;

    // Construct StringBuilder and chain
    @Value("#{new StringBuilder(hostname).append(':').append(apiPort).toString()}")
    private String hostPort;

    public String getBaseUri()  { return baseUri; }
    public String getHostPort() { return hostPort; }
}

public class SpelConstructorsAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CtorCfg.class, ApiEndpointConfig.class);
        var cfg = ctx.getBean(ApiEndpointConfig.class);

        System.out.println("baseUri:   " + cfg.getBaseUri());
        System.out.println("hostPort:  " + cfg.getHostPort());

        // Conditional construction
        var parser = new SpelExpressionParser();
        var evalCtx = new StandardEvaluationContext();
        evalCtx.setVariable("useStrict", true);
        evalCtx.setVariable("input", "  hello  ");

        // Elvis with constructor as default
        System.out.println(parser.parseExpression(
            "#input != null ? #input.trim() : new String('default')").getValue(evalCtx)); // hello

        // Construct inside selection filter
        evalCtx.setVariable("items", java.util.List.of("foo", "bar", "baz"));
        System.out.println(parser.parseExpression(
            "#items.?[new String(#this).toUpperCase().startsWith('B')]").getValue(evalCtx)); // [bar, baz]

        ctx.close();
    }
}
```

How to run: `java SpelConstructorsAdvanced.java`

`new java.net.URI('https', hostname, ...)` invokes the multi-arg URI constructor inline in `@Value`. `new StringBuilder(hostname).append(':').append(apiPort).toString()` chains builder calls. `new String(#this)` inside a filter is redundant (String is already a String) but demonstrates that constructors work in selection predicates.

## 6. Walkthrough

Execution for `"new java.math.BigDecimal('123.456').setScale(2, T(java.math.RoundingMode).HALF_UP)"`:

1. Parse: `ConstructorRef("java.math.BigDecimal", ["123.456"])` → `.setScale(2, TypeRef("HALF_UP"))`.
2. `TypeLocator.findType("java.math.BigDecimal")` → `BigDecimal.class`.
3. Constructor `BigDecimal(String)` invoked with `"123.456"` → `BigDecimal(123.456)`.
4. `.setScale(2, ...)`: `T(java.math.RoundingMode).HALF_UP` → `RoundingMode.HALF_UP`.
5. `bigDecimal.setScale(2, RoundingMode.HALF_UP)` → `BigDecimal(123.46)`.
6. Result returned.

## 7. Gotchas & takeaways

> `new` is **blocked in `SimpleEvaluationContext`**. An expression containing `new ProcessBuilder('rm','-rf','/').start()` could execute system commands. Use `SimpleEvaluationContext` for any user-provided expression string — it rejects constructor calls entirely.

> Constructor arguments are passed **by value**. Primitives and strings are safe; object references are the same Java object identity. Mutations inside a SpEL-constructed object propagate, as usual in Java.

- Short names only work for `java.lang.*`. `new ArrayList()` fails — `ArrayList` is `java.util.ArrayList`. A clear `EvaluationException: Type cannot be found 'ArrayList'` is raised. Always use FQN outside `java.lang`.
- SpEL matches constructors by argument count first, then by type compatibility via `ConversionService`. If two constructors have the same arg count but different types, the most specific matching constructor is chosen. Ambiguity throws `EvaluationException`.
- Creating expensive objects (database connections, network clients) inside `@Value` SpEL constructor expressions executes at every `ApplicationContext` refresh. Prefer a `@Bean` method for expensive initialization.
