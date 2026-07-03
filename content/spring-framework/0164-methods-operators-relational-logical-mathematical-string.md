---
card: spring-framework
gi: 164
slug: methods-operators-relational-logical-mathematical-string
title: "Methods & operators (relational, logical, mathematical, string)"
---

## 1. What it is

SpEL supports calling instance methods via dot notation, and provides a full set of operators: arithmetic (`+`, `-`, `*`, `/`, `%`, `^`), relational (`==`, `!=`, `<`, `>`, `<=`, `>=`, `instanceof`, `matches`), logical (`and`, `or`, `not`, `!`), and string concatenation (`+`). Symbolic and alphabetic forms are both valid for relational and logical operators.

```java
parser.parseExpression("'hello'.toUpperCase()").getValue();        // HELLO
parser.parseExpression("'hello'.contains('ell')").getValue();     // true
parser.parseExpression("3 > 2 and 5 != 4").getValue();            // true
parser.parseExpression("'abc' matches '[a-z]+'").getValue();       // true
parser.parseExpression("2 ^ 10").getValue();                       // 1024
```

## 2. Why & when

- **`@PreAuthorize` conditions** — `"hasRole('ADMIN') and #order.total < 10000"` combines logical and relational operators.
- **Dynamic filtering** — `list.?[name.startsWith('A') and active]` filters with method calls and logical operators.
- **`@ConditionalOnExpression`** — `"'${env}' == 'prod' and #{config.enabled}"` gates bean registration.
- **Regex matching** — `email matches '[\\w.]+@[\\w]+\\.[a-z]{2,}'` validates format inline.
- **Mathematical configuration** — `timeout * 1000 + offset` computes derived millisecond values.

## 3. Core concept

**Arithmetic operators:**

| Op | Meaning | Notes |
|---|---|---|
| `+` | add / concatenate | works on `String` too |
| `-` | subtract | |
| `*` | multiply | |
| `/` | divide | integer division if both int |
| `%` | modulo | |
| `^` | power | `2^8` = 256 |

**Relational operators (symbolic and alphabetic aliases):**

| Symbolic | Alphabetic | Meaning |
|---|---|---|
| `==` | `eq` | equals |
| `!=` | `ne` | not equals |
| `<` | `lt` | less than |
| `>` | `gt` | greater than |
| `<=` | `le` | less or equal |
| `>=` | `ge` | greater or equal |
| — | `instanceof` | type check |
| — | `matches` | regex match |
| — | `between` | `x between {1,5}` ≡ `1 <= x <= 5` |

**Logical operators:**

| Symbolic | Alphabetic |
|---|---|
| `&&` | `and` |
| `\|\|` | `or` |
| `!` | `not` |

Alphabetic forms are preferred in XML config to avoid escaping `<`, `>`, `&&`.

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="15" width="155" height="135" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="87" y="34"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Arithmetic</text>
  <line x1="18" y1="42" x2="157" y2="42" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="87" y="56"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+  -  *  /  %  ^</text>
  <text x="87" y="70"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">2 ^ 8  → 256</text>
  <text x="87" y="84"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">10 / 3 → 3 (int)</text>
  <text x="87" y="98"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">10 / 3d → 3.33</text>
  <text x="87" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">'a'+'b' → "ab"</text>
  <text x="87" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">4 % 3  → 1</text>

  <rect x="185" y="15" width="170" height="135" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="270" y="34"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Relational</text>
  <line x1="193" y1="42" x2="347" y2="42" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="270" y="56"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">== / eq    != / ne</text>
  <text x="270" y="70"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt; / lt    &gt; / gt</text>
  <text x="270" y="84"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;= / le   &gt;= / ge</text>
  <text x="270" y="98"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">instanceof</text>
  <text x="270" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">matches (regex)</text>
  <text x="270" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">between {lo, hi}</text>

  <rect x="375" y="15" width="160" height="135" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="455" y="34"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Logical</text>
  <line x1="383" y1="42" x2="527" y2="42" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="455" y="56"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&amp;&amp; / and</text>
  <text x="455" y="70"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">|| / or</text>
  <text x="455" y="84"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">! / not</text>
  <text x="455" y="98"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">short-circuit: and/or</text>
  <text x="455" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a and b → false if a=false</text>
  <text x="455" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(b not evaluated)</text>

  <rect x="555" y="15" width="137" height="135" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="623" y="34"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Methods</text>
  <line x1="563" y1="42" x2="684" y2="42" stroke="#79c0ff" stroke-width="1" opacity="0.4"/>
  <text x="623" y="56"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">'hi'.length()</text>
  <text x="623" y="70"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">'hi'.contains('h')</text>
  <text x="623" y="84"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">list.size()</text>
  <text x="623" y="98"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">list.isEmpty()</text>
  <text x="623" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">map.containsKey('k')</text>
  <text x="623" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">name.toUpperCase()</text>
</svg>

SpEL provides full arithmetic, relational, logical, and string operators; methods are called via dot notation.

## 5. Runnable example

### Level 1 — Basic

All operator types demonstrated standalone.

```java
// SpelOperatorsBasic.java
import org.springframework.expression.spel.standard.*;

public class SpelOperatorsBasic {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        // Arithmetic
        System.out.println(p.parseExpression("3 + 4 * 2").getValue());        // 11
        System.out.println(p.parseExpression("(3 + 4) * 2").getValue());      // 14
        System.out.println(p.parseExpression("2 ^ 10").getValue());            // 1024
        System.out.println(p.parseExpression("17 % 5").getValue());            // 2
        System.out.println(p.parseExpression("10.0 / 3").getValue());          // 3.3333...
        System.out.println(p.parseExpression("-7 + 3").getValue());            // -4

        // String concatenation
        System.out.println(p.parseExpression("'Hello' + ', ' + 'World!'").getValue()); // Hello, World!

        // Relational
        System.out.println(p.parseExpression("5 > 3").getValue());             // true
        System.out.println(p.parseExpression("5 gt 3").getValue());            // true (alphabetic)
        System.out.println(p.parseExpression("3 == 3").getValue());            // true
        System.out.println(p.parseExpression("3 eq 3").getValue());            // true
        System.out.println(p.parseExpression("'abc' == 'abc'").getValue());    // true (equals())

        // instanceof and matches
        System.out.println(p.parseExpression("42 instanceof T(Integer)").getValue());    // true
        System.out.println(p.parseExpression("'hello@mail.com' matches '.+@.+\\\\..+'").getValue()); // true
        System.out.println(p.parseExpression("'123' matches '[0-9]+'").getValue());      // true

        // between
        System.out.println(p.parseExpression("5 between {1, 10}").getValue()); // true
        System.out.println(p.parseExpression("0 between {1, 10}").getValue()); // false

        // Logical
        System.out.println(p.parseExpression("true and false").getValue());    // false
        System.out.println(p.parseExpression("true or false").getValue());     // true
        System.out.println(p.parseExpression("not true").getValue());          // false
        System.out.println(p.parseExpression("!false").getValue());            // true
    }
}
```

How to run: `java SpelOperatorsBasic.java`

`matches` uses Java regex syntax. Backslashes need double-escaping in Java string literals: `"'str' matches '[a-z]\\\\d+'"`. `between {lo, hi}` is equivalent to `lo <= x and x <= hi` and requires an inline list.

### Level 2 — Intermediate

Operators on root-object properties; method calls in filters; combining in selection.

```java
// SpelOperatorsIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;

class Employee {
    public String name;
    public String department;
    public double salary;
    public boolean active;
    public int yearsExp;

    Employee(String name, String dept, double salary, boolean active, int yearsExp) {
        this.name = name; this.department = dept; this.salary = salary;
        this.active = active; this.yearsExp = yearsExp;
    }
    public String getName()     { return name; }
    public String getDepartment(){ return department; }
    public double getSalary()   { return salary; }
    public boolean isActive()   { return active; }
    public int getYearsExp()    { return yearsExp; }
}

public class SpelOperatorsIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();
        ctx.setVariable("minSalary", 70_000.0);
        ctx.setVariable("prefix", "A");

        List<Employee> employees = List.of(
            new Employee("Alice",   "eng",   95_000, true,  8),
            new Employee("Bob",     "mktg",  65_000, true,  3),
            new Employee("Charlie", "eng",   82_000, false, 5),
            new Employee("Anna",    "hr",    72_000, true,  6));
        ctx.setRootObject(employees);

        // Filter: active AND salary > #minSalary
        System.out.println(parser.parseExpression(
            "?[active and salary > #minSalary]").getValue(ctx, List.class));
        // → [Alice, Anna]

        // Filter: name starts with prefix AND in eng dept
        System.out.println(parser.parseExpression(
            "?[name.startsWith(#prefix) and department eq 'eng']").getValue(ctx, List.class));
        // → [Alice]

        // Filter: yearsExp between {5, 10}
        System.out.println(parser.parseExpression(
            "?[yearsExp between {5, 10}]").getValue(ctx, List.class));
        // → [Alice, Charlie, Anna]

        // Project: compute bonus = salary * 0.1 for active employees
        System.out.println(parser.parseExpression(
            "?[active].![salary * 0.10]").getValue(ctx, List.class));
        // → [9500.0, 6500.0, 7200.0]

        // Regex: filter names matching pattern
        System.out.println(parser.parseExpression(
            "?[name matches '[A-C].*']").getValue(ctx, List.class));
        // → [Alice, Bob, Charlie, Anna... filtered by A or B or C start]
    }
}
```

How to run: `java SpelOperatorsIntermediate.java`

`name.startsWith(#prefix)` calls a `String` instance method inside a selection expression. `?[active and salary > #minSalary]` chains logical `and` with relational `>`. `.![]` projection can be chained directly after `.?[]` selection.

### Level 3 — Advanced

Combined expressions in `@Value`; mathematical operators for configuration; `matches` for validation.

```java
// SpelOperatorsAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;

@Configuration
class OpsCfg {
    @Bean("baseTimeout")  public int baseTimeout()  { return 5000; }
    @Bean("retryFactor")  public int retryFactor()  { return 3; }
    @Bean("appName")      public String appName()   { return "myservice"; }
}

@org.springframework.stereotype.Component
class ServiceConfig {
    // Arithmetic: total timeout = baseTimeout * retryFactor
    @Value("#{baseTimeout * retryFactor}")
    private int totalTimeout;

    // Power: max payload = 2^16
    @Value("#{T(Math).pow(2, 16)}")
    private double maxPayload;

    // Logical + relational: enable strict mode for prod
    @Value("#{systemEnvironment['ENV'] != null and systemEnvironment['ENV'] eq 'prod'}")
    private boolean strictMode;

    // Regex validation: ensure app name matches naming convention
    @Value("#{appName matches '[a-z][a-z0-9-]{2,29}'}")
    private boolean validAppName;

    // Mathematical: bandwidth limit in KB
    @Value("#{T(Math).round(maxPayload / 1024)}")
    private long bandwidthKb;

    public int getTotalTimeout()  { return totalTimeout; }
    public double getMaxPayload() { return maxPayload; }
    public boolean isStrictMode() { return strictMode; }
    public boolean isValidAppName(){ return validAppName; }
    public long getBandwidthKb()  { return bandwidthKb; }
}

public class SpelOperatorsAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OpsCfg.class, ServiceConfig.class);
        var cfg = ctx.getBean(ServiceConfig.class);

        System.out.println("totalTimeout:  " + cfg.getTotalTimeout());   // 15000
        System.out.println("maxPayload:    " + cfg.getMaxPayload());     // 65536.0
        System.out.println("strictMode:    " + cfg.isStrictMode());      // false (ENV not set)
        System.out.println("validAppName:  " + cfg.isValidAppName());    // true
        System.out.println("bandwidthKb:   " + cfg.getBandwidthKb());    // 64

        // Runtime operator demo
        var parser = new SpelExpressionParser();
        var evalCtx = new StandardEvaluationContext();
        evalCtx.setVariable("x", 15);

        // Chained: (x % 2 == 0) or (x between {10, 20})
        System.out.println(parser.parseExpression(
            "(#x % 2 == 0) or (#x between {10, 20})").getValue(evalCtx)); // true (15 in [10,20])

        // String + arithmetic mix
        System.out.println(parser.parseExpression(
            "'Score: ' + (#x * 2)").getValue(evalCtx)); // Score: 30

        ctx.close();
    }
}
```

How to run: `java SpelOperatorsAdvanced.java`

`T(Math).pow(2, 16)` calls a static method. `T(Math).round(...)` rounds a double to `long`. `systemEnvironment['ENV']` accesses the `Map<String,String>` environment variables pre-loaded in Spring's `StandardEvaluationContext`.

## 6. Walkthrough

Execution for `"?[active and salary > #minSalary]"` with `#minSalary = 70000.0`:

1. `Selection` iterates `List<Employee>`.
2. Element Alice: `active=true and salary(95000) > 70000` → `true and true` → `true` → included.
3. Element Bob: `active=true and salary(65000) > 70000` → `true and false` → `false` → excluded.
4. Element Charlie: `active=false` → `and` short-circuits → `false` → excluded (salary not evaluated).
5. Element Anna: `active=true and salary(72000) > 70000` → `true and true` → `true` → included.
6. Result: `[Alice, Anna]`.

## 7. Gotchas & takeaways

> `'abc' == 'abc'` in SpEL uses `.equals()`, not reference equality — consistent with Java semantics for `String`. This differs from how `==` works for object identity in Java code, but SpEL always delegates to `.equals()` for the `==` operator.

> `matches` requires the regex to match the **entire** string (anchored), same as `String.matches()`. `'hello world' matches 'hello'` returns `false`. Use `'hello world' matches '.*hello.*'` to match a substring.

- Alphabetic operators (`eq`, `gt`, `lt`, etc.) are preferred in XML/YAML contexts where angle brackets and ampersands need XML-escaping. In Java string literals, symbolic forms are fine.
- Short-circuit evaluation: `and` does not evaluate the right side when the left is `false`; `or` does not evaluate the right side when the left is `true`. This matters when the right side has side effects (method calls).
- The `between` operator requires an inline list `{lo, hi}` — it cannot accept variables directly as bounds. `x between {#lo, #hi}` works because inline list elements are expressions and `#lo`, `#hi` resolve to values.
