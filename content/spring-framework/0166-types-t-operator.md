---
card: spring-framework
gi: 166
slug: types-t-operator
title: "Types (T operator)"
---

## 1. What it is

The `T(...)` operator in SpEL gives access to a Java type (class) as a first-class value. It resolves to a `java.lang.Class` object, enabling calls to static fields, static methods, and type comparisons without constructing an instance. The argument must be a fully qualified class name or a `java.lang` type by short name.

```java
parser.parseExpression("T(Math).PI").getValue();                // 3.14159...
parser.parseExpression("T(Math).abs(-42)").getValue();          // 42
parser.parseExpression("T(Integer).MAX_VALUE").getValue();       // 2147483647
parser.parseExpression("T(System).currentTimeMillis()").getValue(); // epoch ms
parser.parseExpression("42 instanceof T(Integer)").getValue();  // true
```

## 2. Why & when

- **Static constants** — `T(Math).PI`, `T(Integer).MAX_VALUE`, `T(TimeUnit).SECONDS` in `@Value` without a bean.
- **Static factory methods** — `T(List).of('a','b')`, `T(UUID).randomUUID()`.
- **`instanceof` type check** — `obj instanceof T(com.example.Foo)` in security expressions or filter predicates.
- **Class literal injection** — `@Value("#{T(com.example.MyEnum).class}")` injects a `Class<?>` reference.
- **Enum values** — `T(com.example.Status).ACTIVE` accesses an enum constant as a SpEL value.

## 3. Core concept

`T(FQN)` evaluates to the `Class` object. From there, SpEL can:

| Access type | Syntax | Example |
|---|---|---|
| Static field | `T(Cls).FIELD` | `T(Integer).MAX_VALUE` |
| Static method | `T(Cls).method(args)` | `T(Math).abs(-5)` |
| Class object | `T(Cls)` itself | used with `instanceof` |
| Enum constant | `T(Pkg.Enum).CONST` | `T(java.time.DayOfWeek).MONDAY` |
| Class name | `T(Cls).class.name` | `T(String).class.name` |

Short names that work without full qualification: `T(String)`, `T(Integer)`, `T(Boolean)`, `T(Long)`, `T(Double)`, `T(Float)`, `T(Short)`, `T(Byte)`, `T(Character)`, `T(Math)`, `T(System)` — all classes from `java.lang`.

All others need the full package: `T(java.util.UUID)`, `T(com.example.MyEnum)`.

## 4. Diagram

<svg viewBox="0 0 700 165" xmlns="http://www.w3.org/2000/svg">
  <!-- T() box -->
  <rect x="220" y="25" width="260" height="115" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="2.5"/>
  <text x="350" y="48" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">T(FullyQualifiedName)</text>
  <line x1="228" y1="57" x2="472" y2="57" stroke="#6db33f" stroke-width="1" opacity="0.4"/>
  <text x="350" y="72"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolves to java.lang.Class object</text>
  <text x="350" y="86"  fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">T(Math).PI           → static field</text>
  <text x="350" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">T(Math).abs(-5)      → static method</text>
  <text x="350" y="114" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">x instanceof T(Foo)  → type check</text>
  <text x="350" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">T(Enum).CONST        → enum value</text>

  <!-- java.lang shortcut -->
  <rect x="10" y="50" width="185" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="102" y="70"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">java.lang short names</text>
  <text x="102" y="84"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">T(String) T(Integer)</text>
  <text x="102" y="98"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">T(Math) T(System) T(Long)...</text>

  <!-- FQN required -->
  <rect x="508" y="50" width="185" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="600" y="70"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">FQN required</text>
  <text x="600" y="84"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">T(java.util.UUID)</text>
  <text x="600" y="98"  fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">T(com.example.MyEnum)</text>

  <defs>
    <marker id="a166" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="197" y1="80" x2="217" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a166)"/>
  <line x1="483" y1="80" x2="505" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a166)"/>

  <text x="350" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">T() is BLOCKED in SimpleEvaluationContext — never use it for user-supplied expressions</text>
</svg>

`T()` grants access to static members and type objects; `java.lang` types need no package; all others need FQN.

## 5. Runnable example

### Level 1 — Basic

Static fields, static methods, and `instanceof` via `T()`.

```java
// SpelTypesBasic.java
import org.springframework.expression.spel.standard.*;
import java.util.*;

public class SpelTypesBasic {
    public static void main(String[] args) {
        var p = new SpelExpressionParser();

        // Static fields (java.lang — short name OK)
        System.out.println(p.parseExpression("T(Math).PI").getValue());
        System.out.println(p.parseExpression("T(Integer).MAX_VALUE").getValue());
        System.out.println(p.parseExpression("T(Integer).MIN_VALUE").getValue());
        System.out.println(p.parseExpression("T(Long).MAX_VALUE").getValue());
        System.out.println(p.parseExpression("T(Double).NaN").getValue());

        // Static methods
        System.out.println(p.parseExpression("T(Math).abs(-99)").getValue());         // 99
        System.out.println(p.parseExpression("T(Math).max(10, 20)").getValue());       // 20
        System.out.println(p.parseExpression("T(Math).sqrt(144.0)").getValue());       // 12.0
        System.out.println(p.parseExpression("T(System).currentTimeMillis()").getValue()); // epoch ms

        // FQN required for non-java.lang types
        System.out.println(p.parseExpression("T(java.util.UUID).randomUUID()").getValue());
        System.out.println(p.parseExpression("T(java.time.LocalDate).now()").getValue());

        // instanceof check
        System.out.println(p.parseExpression("42 instanceof T(Integer)").getValue());       // true
        System.out.println(p.parseExpression("'hello' instanceof T(String)").getValue());   // true
        System.out.println(p.parseExpression("42 instanceof T(Long)").getValue());           // false

        // Class object itself
        System.out.println(p.parseExpression("T(String).class.name").getValue());           // java.lang.String
        System.out.println(p.parseExpression("T(String) == T(String)").getValue());          // true
    }
}
```

How to run: `java SpelTypesBasic.java`

`T(Integer)` evaluates to `Integer.class`. `T(String) == T(String)` is `true` because the same `Class` object is returned each time. `T(java.util.UUID).randomUUID()` calls the static factory method.

### Level 2 — Intermediate

Enum access; `T()` in filter predicates; type-based conditional configuration.

```java
// SpelTypesIntermediate.java
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.time.*;
import java.util.*;

enum Priority { LOW, MEDIUM, HIGH, CRITICAL }

class Task {
    public String title;
    public Priority priority;
    public boolean done;

    Task(String title, Priority priority, boolean done) {
        this.title = title; this.priority = priority; this.done = done;
    }
    public String getTitle()      { return title; }
    public Priority getPriority() { return priority; }
    public boolean isDone()       { return done; }
}

public class SpelTypesIntermediate {
    public static void main(String[] args) {
        var parser = new SpelExpressionParser();
        var ctx = new StandardEvaluationContext();

        // Enum access via T()
        Object mon = parser.parseExpression("T(java.time.DayOfWeek).MONDAY").getValue();
        System.out.println("DayOfWeek: " + mon); // MONDAY

        // Enum ordinal comparison
        ctx.setVariable("minPriority", Priority.MEDIUM.ordinal());
        List<Task> tasks = List.of(
            new Task("Write docs", Priority.LOW,      false),
            new Task("Fix bug",    Priority.HIGH,     false),
            new Task("Deploy",     Priority.CRITICAL, false),
            new Task("Code review",Priority.MEDIUM,   true));
        ctx.setRootObject(tasks);

        // Filter: priority ordinal >= MEDIUM and not done
        System.out.println(parser.parseExpression(
            "?[!done and priority.ordinal() >= #minPriority]").getValue(ctx, List.class));

        // instanceof filter
        List<Object> mixed = new ArrayList<>(List.of("text", 42, 3.14, true, "more"));
        ctx.setRootObject(mixed);
        System.out.println(parser.parseExpression(
            "?[#this instanceof T(String)]").getValue(ctx, List.class)); // [text, more]
        System.out.println(parser.parseExpression(
            "?[#this instanceof T(Number)]").getValue(ctx, List.class)); // [42, 3.14]

        // Use T() in computed value
        var single = new StandardEvaluationContext();
        single.setVariable("items", List.of("a", "b", "c"));
        System.out.println(parser.parseExpression(
            "T(Math).min(#items.size(), 2)").getValue(single)); // 2
    }
}
```

How to run: `java SpelTypesIntermediate.java`

`T(com.example.Priority)` — since `Priority` is not in `java.lang`, you'd use the FQN. The example uses a top-level class accessible without package for simplicity. `priority.ordinal()` calls the instance `ordinal()` method on an enum field. `#this instanceof T(String)` checks element type in a filter.

### Level 3 — Advanced

`@Value` with `T()` for static constants and factory methods; class comparison; `T()` in `@ConditionalOnExpression`.

```java
// SpelTypesAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.expression.*;
import org.springframework.expression.spel.standard.*;
import org.springframework.expression.spel.support.*;
import java.util.*;
import java.util.concurrent.*;

@Configuration
class TypesCfg {}

@org.springframework.stereotype.Component
class AppConstants {
    @Value("#{T(Integer).MAX_VALUE}")
    private int maxInt;

    @Value("#{T(Math).PI}")
    private double pi;

    @Value("#{T(java.util.concurrent.TimeUnit).SECONDS.toMillis(30)}")
    private long thirtySeconds;

    @Value("#{T(java.util.UUID).randomUUID().toString()}")
    private String instanceId;

    @Value("#{T(System).getProperty('java.version')}")
    private String javaVersion;

    public int getMaxInt()          { return maxInt; }
    public double getPi()           { return pi; }
    public long getThirtySeconds()  { return thirtySeconds; }
    public String getInstanceId()   { return instanceId; }
    public String getJavaVersion()  { return javaVersion; }
}

public class SpelTypesAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(TypesCfg.class, AppConstants.class);
        var consts = ctx.getBean(AppConstants.class);

        System.out.println("maxInt:        " + consts.getMaxInt());
        System.out.println("pi:            " + consts.getPi());
        System.out.println("30s in ms:     " + consts.getThirtySeconds()); // 30000
        System.out.println("instanceId:    " + consts.getInstanceId());
        System.out.println("javaVersion:   " + consts.getJavaVersion());

        // Runtime type comparison
        var parser = new SpelExpressionParser();
        var evalCtx = new StandardEvaluationContext();
        evalCtx.setVariable("obj", "hello");
        System.out.println(parser.parseExpression(
            "#obj.class == T(String)").getValue(evalCtx)); // true
        System.out.println(parser.parseExpression(
            "T(String).isAssignableFrom(#obj.class)").getValue(evalCtx)); // true

        ctx.close();
    }
}
```

How to run: `java SpelTypesAdvanced.java`

`T(java.util.concurrent.TimeUnit).SECONDS.toMillis(30)` chains enum constant access with an instance method call. `T(System).getProperty('java.version')` calls `System.getProperty` as a static method. `T(String).isAssignableFrom(#obj.class)` calls a static method from `Class` itself.

## 6. Walkthrough

Execution for `"T(Math).max(10, 20)"`:

1. `T(Math)` — `TypeLocator.findType("Math")` → checks `java.lang` short-name list → returns `Math.class`.
2. `.max(10, 20)` — `MethodResolver` finds `Math.max(int, int)` via reflection.
3. Static method invoked: `Math.max(10, 20)` → `20`.
4. Result: `Integer(20)`.

## 7. Gotchas & takeaways

> `T()` is **blocked in `SimpleEvaluationContext`**. Any user-supplied expression containing `T(Runtime)` or `T(ProcessBuilder)` could execute system commands. Always sandbox user expressions with `SimpleEvaluationContext`, which rejects type access entirely.

> Only `java.lang.*` types can use short names in `T()`. `T(Date)` fails — use `T(java.util.Date)`. `T(List)` fails — use `T(java.util.List)`. Forgetting the package is a common source of `EvaluationException: Type cannot be found 'Date'`.

- `T(SomeEnum).CONST` works for accessing enum constants. To get the ordinal: `T(SomeEnum).CONST.ordinal()`. To compare by name: `enumField.name() == 'ACTIVE'` (avoids needing `T()` for the comparison).
- `T()` returns the same `Class` instance on every evaluation because the JVM interns class objects. `T(String) == T(String)` is `true` even with `==` (reference equality), not just `.equals()`.
- Calling `T(System).exit(0)` in a SpEL expression terminates the JVM. This is the primary reason `T()` must be blocked in any context that accepts externally-supplied expression strings.
