---
card: spring-framework
gi: 214
slug: supported-pointcut-designators-execution-within-this-target
title: "Supported pointcut designators (execution, within, this, target, args, @annotation, etc.)"
---

## 1. What it is

A **pointcut designator (PCD)** is a keyword in a pointcut expression that specifies *what kind of thing* to match. Spring AOP supports a defined subset of AspectJ's full PCD vocabulary:

| Designator | Matches |
|-----------|---------|
| `execution` | Method execution join points (the primary PCD) |
| `within` | Methods inside a specific type or package |
| `this` | Bean proxy is an instance of a given type |
| `target` | Target object (the real bean) is an instance of a given type |
| `args` | Method arguments match given types |
| `@target` | Target class carries a given annotation |
| `@within` | Target class (or superclass) carries a given annotation |
| `@annotation` | The method carries a given annotation |
| `@args` | The runtime type of arguments carries a given annotation |
| `bean` | Spring-specific: matches by bean name pattern (Spring AOP only) |

## 2. Why & when

`execution` handles 80% of cases. The others add precision or express intent better:

- `@annotation(Transactional)` — match only `@Transactional` methods.
- `within(com.example.service.*)` — all methods in the service package, regardless of class.
- `bean(orderService)` — match a specific named bean (useful for infrastructure beans).
- `args(String, ..)` — match methods whose first argument is a `String`.

Combining designators with `&&` narrows scope; `||` widens it; `!` excludes.

## 3. Core concept

Think of each designator as a different type of filter on a surveillance camera: `execution` filters by "which action is happening", `@annotation` filters by "is the action marked with this badge", `within` filters by "which building is it happening in", `args` filters by "who/what is involved."

**`execution` pattern syntax:**
```
execution(modifiers? return-type declaring-type? method-name(params) throws?)
execution(public * com.example.service.*.*(..))
          modifier  return  declaring-type  method-name params
```
- `*` = any single token.
- `..` = any number of packages (in type patterns) or any parameters (in param patterns).
- `+` = type and all its subtypes (`AccountService+` = `AccountService` and its subclasses).

## 4. Diagram

<svg viewBox="0 0 640 215" xmlns="http://www.w3.org/2000/svg">
  <!-- Method call target -->
  <rect x="15" y="80" width="130" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="80" y="104" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="80" y="120" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Transactional</text>
  <text x="80" y="134" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">void place(String id)</text>

  <!-- Designator filters (right column) -->
  <rect x="220" y="20" width="180" height="30" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="310" y="39" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">execution(* OrderService.place(..))</text>

  <rect x="220" y="58" width="180" height="30" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="310" y="77" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">within(com.example.service.*)</text>

  <rect x="220" y="96" width="180" height="30" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="310" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@annotation(Transactional)</text>

  <rect x="220" y="134" width="180" height="30" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="310" y="153" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">args(String)</text>

  <rect x="220" y="172" width="180" height="30" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="310" y="191" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">bean(orderService)</text>

  <!-- Lines from method -->
  <line x1="145" y1="100" x2="220" y2="35" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>
  <line x1="145" y1="105" x2="220" y2="73" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>
  <line x1="145" y1="110" x2="220" y2="111" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="3 2"/>
  <line x1="145" y1="115" x2="220" y2="149" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>
  <line x1="145" y1="120" x2="220" y2="187" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2"/>

  <!-- All match label -->
  <rect x="430" y="96" width="185" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="523" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">all five match this method</text>
  <line x1="400" y1="111" x2="430" y2="111" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

All five designators match `@Transactional void OrderService.place(String id)` called through the Spring proxy.

## 5. Runnable example

Scenario: a **product catalogue service** — first using `execution`, then combining `@annotation` + `within`, then a complete tour of all major designators.

### Level 1 — Basic

`execution` — the fundamental PCD.

```java
// PcdDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PcdDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PcdDemo.class);
        var svc = ctx.getBean(ProductService.class);
        svc.findById(1L);
        svc.save("Widget");
        svc.deleteAll();
        ctx.close();
    }
}

@Service
class ProductService {
    public String findById(long id)    { System.out.println("find " + id); return "P-"+id; }
    public void   save(String name)    { System.out.println("save " + name); }
    public void   deleteAll()          { System.out.println("deleteAll"); }
    private void  helper()             { /* private: never intercepted */ }
}

@Aspect
@Component
class LogAspect {
    // execution: public methods of ProductService, any return type, any params
    @Before("execution(public * ProductService.*(..))")
    public void log(JoinPoint jp) {
        System.out.println("[EXEC] " + jp.getSignature().toShortString());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. PcdDemo.java`

All three public methods are intercepted. `private void helper()` is never intercepted (proxy cannot override private methods).

---

### Level 2 — Intermediate

Combine `@annotation` (match annotated methods) and `within` (limit to a package scope).

```java
// PcdDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Logged {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PcdDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PcdDemo.class);
        var svc = ctx.getBean(ProductService.class);
        System.out.println("--- @Logged method ---");
        svc.findById(42L);    // @Logged → aspect fires
        System.out.println("--- not @Logged method ---");
        svc.save("Gadget");   // no @Logged → aspect does NOT fire
        ctx.close();
    }
}

@Service
class ProductService {
    @Logged
    public String findById(long id)  { System.out.println("find " + id); return "P-"+id; }
    public void   save(String name)  { System.out.println("save " + name); }
}

@Aspect
@Component
class LogAspect {
    // @annotation: method must have @Logged
    @Before("@annotation(Logged)")
    public void onLogged(JoinPoint jp) {
        System.out.println("[@annotation] " + jp.getSignature().getName());
    }

    // within: any method in a class whose name starts with Product
    @Before("within(Product*)")
    public void onWithin(JoinPoint jp) {
        System.out.println("[within] " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath

`@annotation(Logged)` fires only for `findById`. `within(Product*)` fires for all methods of `ProductService`. On `findById` both fire; on `save` only `within` fires.

---

### Level 3 — Advanced

Full tour: `execution`, `args`, `@target`, `@annotation`, `target`, `bean` — each used in a named pointcut, then composed.

```java
// PcdDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target({ElementType.TYPE, ElementType.METHOD})
@interface Monitored {}

interface Findable { Object findById(long id); }

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PcdDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PcdDemo.class);
        var svc = ctx.getBean(ProductService.class);
        System.out.println("=== findById (long) ===");
        svc.findById(1L);
        System.out.println("=== save (String) ===");
        svc.save("Bolt");
        System.out.println("=== beanNameOp ===");
        svc.deleteAll();
        ctx.close();
    }
}

@Monitored
@Service
class ProductService implements Findable {
    public Object findById(long id)  { System.out.println("find " + id); return "P-"+id; }
    public void   save(String name)  { System.out.println("save " + name); }
    public void   deleteAll()        { System.out.println("deleteAll"); }
}

@Aspect
@Component
class PcdTourAspect {
    // execution: standard method pattern
    @Pointcut("execution(* ProductService.*(..))")
    public void allOps() {}

    // args: first argument must be long
    @Pointcut("args(long,..)")
    public void longFirstArg() {}

    // @target: the target class bears @Monitored
    @Pointcut("@target(Monitored)")
    public void monitoredClass() {}

    // @annotation: the method bears @Monitored (none do — shows empty match)
    @Pointcut("@annotation(Monitored)")
    public void monitoredMethod() {}

    // target: the real object implements Findable
    @Pointcut("target(Findable)")
    public void findableTarget() {}

    // bean: specific bean name
    @Pointcut("bean(productService)")
    public void namedBean() {}

    // --- advice methods ---
    @Before("allOps() && longFirstArg()")
    public void onLongArg(JoinPoint jp) {
        System.out.println("[args(long)] " + jp.getSignature().getName());
    }

    @Before("monitoredClass()")
    public void onMonitoredClass(JoinPoint jp) {
        System.out.println("[@target(@Monitored)] " + jp.getSignature().getName());
    }

    @Before("findableTarget() && longFirstArg()")
    public void onFindable(JoinPoint jp) {
        System.out.println("[target(Findable)&&args(long)] " + jp.getSignature().getName());
    }

    @Before("namedBean()")
    public void onBean(JoinPoint jp) {
        System.out.println("[bean(productService)] " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

Each `@Before` fires for a different subset of calls. `findById(1L)` fires `args(long)`, `@target`, `target(Findable)`, and `bean`. `save("Bolt")` fires `@target` and `bean` (but not `args(long)` or `target(Findable)&&args(long)`). This shows how combining designators narrows scope.

## 6. Walkthrough

**Startup — pointcut compilation:**
Each `@Pointcut` expression is compiled into an `AspectJExpressionPointcut` by parsing the expression string with AspectJ's `PatternParser`. For `args(long,..)`, the parser generates a type-matching rule that checks if the first method parameter is assignable from `long` (or `Long`).

**Call to `svc.findById(1L)` — advice chain evaluation:**
1. Proxy intercepts `findById(1L)`.
2. For each registered pointcut, Spring evaluates: does this method at this join point match?
   - `allOps()` → `execution(* ProductService.*(..))` → yes.
   - `longFirstArg()` → `args(long,..)` → yes (`long id` matches).
   - `monitoredClass()` → `@target(Monitored)` → yes (`ProductService` has `@Monitored`).
   - `findableTarget()` → `target(Findable)` → yes (`ProductService` implements `Findable`).
   - `namedBean()` → `bean(productService)` → yes.
3. Matching advice runs in `@Order` sequence (default: unspecified order for same aspect).

**`this` vs `target` distinction:**
- `this` matches the *proxy* type — useful when the proxy implements additional interfaces via `@DeclareParents`.
- `target` matches the *real bean* type — used in 99% of cases where you want to match the actual class.
- For Spring CGLIB proxy: `this` == `target` == `ProductService` (CGLIB subclass IS-A `ProductService`).
- For JDK proxy: `this` is the proxy (which implements `Findable`), `target` is `ProductService`.

**Expected output excerpt:**
```
=== findById (long) ===
[args(long)] findById
[@target(@Monitored)] findById
[target(Findable)&&args(long)] findById
[bean(productService)] findById
find 1
```

## 7. Gotchas & takeaways

> **`within` matches at the class level, not the method level.** `within(com.example.service.*)` matches ANY method inside any class in that package — including methods you didn't intend to intercept. Combine with `execution` to add method-level precision.

> **`bean(pattern)` is Spring AOP–specific, not standard AspectJ.** If you ever migrate to full AspectJ with compile-time weaving, `bean` expressions will fail to compile. Use it only when you specifically need bean-name–based matching.

- `@annotation(AnnotationType)` is the cleanest opt-in mechanism — methods self-declare they want the advice by carrying the annotation.
- `@target` vs `@within`: `@target` checks the runtime class of the target bean; `@within` also matches subclasses whose superclass carries the annotation.
- `execution` pattern with `..` in the package part: `execution(* com.example..*.*(..))` matches all methods in `com.example` and any subpackage — use carefully.
- `args` type patterns use static types, not runtime types — `args(Object)` will match even if the actual argument is a `String`.
- Omitting `execution` in favour of just `within` or `args` alone can lead to infinite recursion if the pointcut accidentally matches infrastructure beans; always test pointcuts with unit tests before deploying.
