---
card: spring-framework
gi: 215
slug: combining-pointcut-expressions
title: Combining pointcut expressions
---

## 1. What it is

Pointcut expressions can be combined using logical operators to create precise selectors:
- `&&` — both expressions must match (AND).
- `||` — at least one expression must match (OR).
- `!` — the expression must NOT match (NOT).

You can combine inline expressions, named pointcut references, or both. Combining lets you build complex matchers from simple, single-responsibility rules without bloating individual expressions.

```java
@Before("serviceLayer() && !readOnlyOps()")
public void auditWrites(JoinPoint jp) { ... }
```

## 2. Why & when

A single `execution` expression often over-matches or under-matches. Common combination patterns:

- **Narrow scope**: `execution(* svc.*.*(..)) && @annotation(Transactional)` — transactional service methods only.
- **Exclude a subset**: `serviceLayer() && !execution(* *Service.find*(..))` — all service ops except reads.
- **Include two disjoint sets**: `execution(* OrderService.*(..)) || execution(* PaymentService.*(..))` — either service.
- **Environment guards**: `execution(* *.*(..)) && !within(com.example.test.*)` — exclude test classes.

Use `&&` to add constraints; use `||` to union disjoint sets; use `!` to carve out exceptions.

## 3. Core concept

Think of each pointcut as a lens filter on a camera. `&&` stacks filters (must pass all), `||` means "either filter works", `!` inverts the filter. You combine simple, named, single-purpose filters to get exactly the join points you want.

Operator precedence (highest to lowest): `!` > `&&` > `||`. Parentheses override this order. Spring normalises the expression at startup and evaluates it efficiently — combined expressions are no slower than monolithic ones at runtime.

Inline expressions in `@Before("…")` can use `&&`, `||`, `!` directly:

```java
@Before("execution(* OrderService.*(..)) && !execution(* OrderService.cancel(..))")
```

Or combine named references:

```java
@Before("orderOps() && !cancelOp()")
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Sets -->
  <!-- serviceLayer circle -->
  <ellipse cx="200" cy="110" rx="150" ry="65" fill="#79c0ff" opacity="0.13" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="200" y="85" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">serviceLayer()</text>

  <!-- transactional circle -->
  <ellipse cx="320" cy="110" rx="150" ry="65" fill="#6db33f" opacity="0.12" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="85" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">@annotation(Transactional)</text>

  <!-- Intersection label -->
  <text x="260" y="113" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">serviceLayer()</text>
  <text x="260" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&amp;&amp; @annotation</text>
  <text x="260" y="143" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">(Transactional)</text>

  <!-- Operator labels -->
  <text x="75" y="145" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">service but not</text>
  <text x="75" y="158" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional</text>

  <text x="490" y="145" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Transactional but</text>
  <text x="490" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">not service layer</text>
</svg>

`&&` selects the intersection (both conditions true). `!serviceLayer()` excludes the left circle; `||` would unite both circles.

## 5. Runnable example

Scenario: a **report API service** — first combining with `&&` to narrow, then with `||` to union, then with `!` to exclude and composing all three.

### Level 1 — Basic

`&&` to narrow: only `@Cached` methods inside `ReportService`.

```java
// CombinePointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Cached {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class CombinePointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CombinePointcutDemo.class);
        var svc = ctx.getBean(ReportService.class);
        System.out.println("=== generate (no @Cached) ===");
        svc.generate("Q1");    // service method, no @Cached
        System.out.println("=== fetch (@Cached) ===");
        svc.fetch("summary");  // service method with @Cached
        ctx.close();
    }
}

@Service
class ReportService {
    public void generate(String period) { System.out.println("generate: " + period); }
    @Cached
    public String fetch(String key) {
        System.out.println("fetch: " + key);
        return "data";
    }
}

@Aspect
@Component
class CacheMonitorAspect {
    // AND: must be in ReportService AND carry @Cached
    @Before("execution(* ReportService.*(..)) && @annotation(Cached)")
    public void onCached(JoinPoint jp) {
        System.out.println("[&&] Cached method intercepted: " + jp.getSignature().getName());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. CombinePointcutDemo.java`

Only `fetch` (which has `@Cached`) is intercepted. `generate` is a service method but lacks `@Cached` — the `&&` prevents it matching.

---

### Level 2 — Intermediate

`||` to union two disjoint services; `!` to exclude a specific method.

```java
// CombinePointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class CombinePointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CombinePointcutDemo.class);
        ctx.getBean(ReportService.class).generate("Q1");
        ctx.getBean(ExportService.class).exportCsv("Q1");
        ctx.getBean(ExportService.class).exportRaw("Q1");   // excluded by !
        ctx.close();
    }
}

@Service
class ReportService {
    public void generate(String p) { System.out.println("Report.generate: " + p); }
}

@Service
class ExportService {
    public void exportCsv(String p) { System.out.println("Export.csv: " + p); }
    public void exportRaw(String p) { System.out.println("Export.raw: " + p); }
}

@Aspect
@Component
class UnionAspect {
    @Pointcut("execution(* ReportService.*(..))")
    public void reports() {}

    @Pointcut("execution(* ExportService.*(..))")
    public void exports() {}

    @Pointcut("execution(* ExportService.exportRaw(..))")
    public void rawExport() {}

    // OR union of both services, minus exportRaw
    @Before("(reports() || exports()) && !rawExport()")
    public void monitor(JoinPoint jp) {
        System.out.println("[|| && !] " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath

`generate` (ReportService) and `exportCsv` (ExportService) are intercepted via `||`. `exportRaw` is excluded by `!rawExport()`.

---

### Level 3 — Advanced

Full composition: named pointcuts combined into layered expressions, with `within` for a package guard and an arg-type filter.

```java
// CombinePointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class CombinePointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CombinePointcutDemo.class);
        var report = ctx.getBean(ReportService.class);
        var export = ctx.getBean(ExportService.class);

        System.out.println("=== report.generate(String) ===");
        report.generate("Q1");               // service + String arg → fires all matching
        System.out.println("=== report.count() ===");
        report.count();                      // service + no String arg → fires some
        System.out.println("=== export.exportCsv(String) ===");
        export.exportCsv("Q1");              // exports + String arg → fires
        ctx.close();
    }
}

@Service
class ReportService {
    public void generate(String period) { System.out.println("generate: " + period); }
    public long count() { System.out.println("count"); return 42L; }
}

@Service
class ExportService {
    public void exportCsv(String period) { System.out.println("exportCsv: " + period); }
}

@Aspect
@Component
class ComposedAspect {
    @Pointcut("execution(* ReportService.*(..))")
    public void reports() {}

    @Pointcut("execution(* ExportService.*(..))")
    public void exports() {}

    @Pointcut("args(String,..)")
    public void stringFirstArg() {}

    @Pointcut("!execution(* *.count(..))")
    public void notCount() {}

    // Union of both services, only when String arg present, excluding count()
    @Before("(reports() || exports()) && stringFirstArg() && notCount()")
    public void preciselyCombined(JoinPoint jp) {
        System.out.println("[composed] " + jp.getSignature().toShortString());
    }

    // Separately: all service methods, including count
    @Before("reports() || exports()")
    public void allOps(JoinPoint jp) {
        System.out.println("[all ops] " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

`generate("Q1")` matches both `[composed]` (String arg, not count, in services) and `[all ops]`. `count()` matches `[all ops]` but NOT `[composed]` (no String arg, and excluded by `!count()`). `exportCsv("Q1")` matches both.

## 6. Walkthrough

**Expression evaluation at runtime (Level 3, `report.generate("Q1")`):**

1. Proxy intercepts `ReportService.generate("Q1")`.
2. Spring evaluates `(reports() || exports()) && stringFirstArg() && notCount()`:
   - `reports()` → `execution(* ReportService.*(..))` → yes.
   - `|| exports()` → short-circuits to yes (OR already satisfied).
   - `&& stringFirstArg()` → `args(String,..)` → is first arg a String? yes.
   - `&& notCount()` → `!execution(* *.count(..))` → is this NOT `count()`? yes.
   - Combined: true → `[composed]` advice fires.
3. Spring evaluates `reports() || exports()`:
   - `reports()` → yes → true → `[all ops]` advice fires.

**Short-circuit evaluation:**
Spring evaluates `&&` left to right and stops as soon as a false operand is found. For `||`, it stops at the first true. This means the order of sub-expressions affects how many checks are performed. Put cheap checks (class-level `within`) before expensive ones (runtime `args` type checks).

**`!` precedence:**
`!rawExport() && exports()` is `(!rawExport()) && exports()`, not `!(rawExport() && exports())`. Parentheses are required to change grouping: `!(rawExport() && exports())`.

**Expected output (Level 3):**
```
=== report.generate(String) ===
[composed] ReportService.generate(..)
[all ops] generate
generate: Q1
=== report.count() ===
[all ops] count
count
=== export.exportCsv(String) ===
[composed] ExportService.exportCsv(..)
[all ops] exportCsv
exportCsv: Q1
```

## 7. Gotchas & takeaways

> **`&&` in XML Spring config must be written `&amp;&amp;`** (XML entity escaping). In `@Pointcut` annotation strings in Java, `&&` works as-is.

> **Too many `||` unions can create unexpectedly broad pointcuts.** A pointcut like `execution(* *.*(..)) || @annotation(X)` matches almost everything — the first clause overwhelms the specificity of the second. Review combined pointcuts carefully in tests.

- Build pointcuts bottom-up: small, single-responsibility named pointcuts → combine into larger expressions. Don't write one giant expression.
- `!` is useful for "all service methods except reads": `serviceLayer() && !readOps()`.
- Named pointcuts can be composed in a "library" aspect class that has no advice — only `@Pointcut` declarations — then other aspects reference them.
- Test combined pointcuts with a unit test that creates a `AspectJExpressionPointcut` and calls `.matches(method, targetClass)` — verifies the expression before deploying.
