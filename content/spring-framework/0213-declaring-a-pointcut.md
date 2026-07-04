---
card: spring-framework
gi: 213
slug: declaring-a-pointcut
title: Declaring a pointcut
---

## 1. What it is

A **pointcut** is a predicate expression that selects a set of join points (method executions) where advice should run. In Spring AOP you declare pointcuts using the `@Pointcut` annotation on a method with an empty body — that method acts as a named reference the advice annotations can cite.

```java
@Pointcut("execution(* com.example.service.*.*(..))")
public void serviceLayer() {} // the method name is the pointcut name
```

Advice then refers to it: `@Before("serviceLayer()")`. Named pointcuts make complex expressions reusable across multiple advice methods and across aspect classes.

## 2. Why & when

Without named pointcuts:
- Every advice annotation repeats the same `execution(…)` string inline.
- Updating the expression means touching every advice annotation.
- The expression's *intent* is not communicated.

With named pointcuts:
- One definition, many references.
- The method name documents intent: `serviceLayer()`, `publicControllerMethods()`, `databaseOperations()`.
- Pointcuts can be combined with `&&`, `||`, `!` at the reference site.

Declare a named `@Pointcut` whenever a pointcut expression is used more than once, or whenever the expression is complex enough to deserve a name.

## 3. Core concept

Think of a pointcut as a filter rule with a name. `serviceLayer()` means "all public methods in the service package." The `@Before("serviceLayer()")` advice says "run this code whenever `serviceLayer()` matches." Multiple advice methods can share the same filter.

Pointcut declarations follow these rules:
- The annotated method must have `void` return type and empty body.
- Access modifier (public/private/protected) controls visibility from other aspect classes.
- The method name becomes the pointcut's identifier.
- The `@Pointcut` expression string is the actual selector.

A pointcut can reference other named pointcuts:
```java
@Pointcut("serviceLayer() && !adminMethods()")
public void userServiceLayer() {}
```

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Pointcut declaration -->
  <rect x="15" y="30" width="280" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Pointcut declaration</text>
  <rect x="30" y="62" width="250" height="40" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="155" y="79" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">@Pointcut("execution(* svc.*(..))")</text>
  <text x="155" y="95" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">public void serviceLayer() {}</text>

  <rect x="30" y="112" width="250" height="36" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="155" y="129" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">@Pointcut("serviceLayer() &amp;&amp; @annotation(Timed)")</text>
  <text x="155" y="143" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">public void timedServiceOps() {}</text>

  <!-- Arrow -->
  <line x1="295" y1="100" x2="350" y2="100" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="323" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">used by</text>

  <!-- Advice references -->
  <rect x="350" y="30" width="270" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="485" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Advice using pointcut</text>
  <rect x="365" y="62" width="240" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="485" y="79" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@Before("serviceLayer()")</text>
  <text x="485" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">void logBefore(JoinPoint jp) { ... }</text>

  <rect x="365" y="107" width="240" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="485" y="122" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@Around("timedServiceOps()")</text>
  <text x="485" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Object time(PJP pjp) { ... }</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Named pointcuts act as reusable, composable building blocks that advice methods reference by name.

## 5. Runnable example

Scenario: an **order processing system** — first inline pointcut, then named pointcut, then composed and shared pointcuts.

### Level 1 — Basic

Inline pointcut: the expression is written directly in the `@Before` annotation.

```java
// PointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PointcutDemo.class);
        ctx.getBean(OrderService.class).place("ORD-1");
        ctx.getBean(OrderService.class).cancel("ORD-1");
        ctx.close();
    }
}

@Service
class OrderService {
    public void place(String id) { System.out.println("Order placed: " + id); }
    public void cancel(String id) { System.out.println("Order cancelled: " + id); }
}

@Aspect
@Component
class LogAspect {
    // Inline pointcut — expression repeated in each advice
    @Before("execution(* OrderService.place(..))")
    public void beforePlace(JoinPoint jp) {
        System.out.println("[LOG] place() called with: " + jp.getArgs()[0]);
    }

    @Before("execution(* OrderService.cancel(..))")
    public void beforeCancel(JoinPoint jp) {
        System.out.println("[LOG] cancel() called with: " + jp.getArgs()[0]);
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. PointcutDemo.java`

Works, but both `@Before` annotations repeat similar expressions. Change the package and you edit two places.

---

### Level 2 — Intermediate

Named pointcut: declare once, reference from multiple advice methods.

```java
// PointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PointcutDemo.class);
        var svc = ctx.getBean(OrderService.class);
        svc.place("ORD-1");
        svc.cancel("ORD-1");
        svc.ship("ORD-1");
        ctx.close();
    }
}

@Service
class OrderService {
    public void place(String id)  { System.out.println("Placed: " + id); }
    public void cancel(String id) { System.out.println("Cancelled: " + id); }
    public void ship(String id)   { System.out.println("Shipped: " + id); }
}

@Aspect
@Component
class OrderAspect {
    // Named pointcut — declared once
    @Pointcut("execution(* OrderService.*(..))")
    public void orderOps() {}

    // Multiple advice methods reference the same pointcut
    @Before("orderOps()")
    public void logEntry(JoinPoint jp) {
        System.out.println("[ENTRY] " + jp.getSignature().getName() + " " + jp.getArgs()[0]);
    }

    @After("orderOps()")
    public void logExit(JoinPoint jp) {
        System.out.println("[EXIT]  " + jp.getSignature().getName());
    }
}
```

How to run: same as Level 1

`orderOps()` is declared once. Both `@Before` and `@After` reference it. Rename the package or change the expression in one place and all advice is updated.

---

### Level 3 — Advanced

Compose pointcuts with `&&` and `||`, and expose the named pointcut to a second aspect class.

```java
// PointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Auditable {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class PointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PointcutDemo.class);
        var svc = ctx.getBean(OrderService.class);
        System.out.println("--- place (Auditable) ---");
        svc.place("ORD-1");
        System.out.println("--- cancel (not Auditable) ---");
        svc.cancel("ORD-1");
        System.out.println("--- ship (Auditable) ---");
        svc.ship("ORD-1");
        ctx.close();
    }
}

@Service
class OrderService {
    @Auditable public void place(String id)  { System.out.println("Placed: " + id); }
                public void cancel(String id) { System.out.println("Cancelled: " + id); }
    @Auditable public void ship(String id)   { System.out.println("Shipped: " + id); }
}

@Aspect
@Component
class PointcutLibrary {
    // Base pointcut: all OrderService methods
    @Pointcut("execution(* OrderService.*(..))")
    public void orderOps() {}

    // Refinement: only @Auditable methods
    @Pointcut("orderOps() && @annotation(Auditable)")
    public void auditableOrderOps() {}

    // Exclusion: order ops that are NOT cancel
    @Pointcut("orderOps() && !execution(* OrderService.cancel(..))")
    public void nonCancelOrderOps() {}
}

@Aspect
@Component
class AuditAspect {
    // Cross-aspect reference: fully-qualified pointcut from PointcutLibrary
    @Before("PointcutLibrary.auditableOrderOps()")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] @Auditable method: " + jp.getSignature().getName());
    }
}

@Aspect
@Component
class MetricsAspect {
    @Before("PointcutLibrary.nonCancelOrderOps()")
    public void metric(JoinPoint jp) {
        System.out.println("[METRIC] Non-cancel op: " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

`PointcutLibrary` is a pure-pointcut aspect (no advice). `auditableOrderOps()` composes `orderOps()` with `@annotation(Auditable)`. `AuditAspect` and `MetricsAspect` reference `PointcutLibrary`'s pointcuts using the fully-qualified class prefix.

## 6. Walkthrough

**Pointcut resolution at startup:**
1. `AnnotationAwareAspectJAutoProxyCreator` reads all `@Aspect` beans.
2. For `PointcutLibrary`, it finds three `@Pointcut` methods: `orderOps`, `auditableOrderOps`, `nonCancelOrderOps`.
3. It registers them in an `AspectJExpressionPointcut` registry keyed by `"PointcutLibrary.orderOps"`, etc.

**Composition evaluation for `auditableOrderOps()`:**
- `orderOps() && @annotation(Auditable)` is parsed.
- `orderOps()` resolves to `execution(* OrderService.*(..))`.
- `@annotation(Auditable)` checks if the method has the `@Auditable` annotation.
- The composed expression is: match `OrderService.*` AND method has `@Auditable`.
- `place` → matches both → yes. `cancel` → matches `OrderService.*` but no `@Auditable` → no. `ship` → yes.

**Cross-aspect pointcut reference:**
- `AuditAspect.audit` uses `"PointcutLibrary.auditableOrderOps()"`.
- Spring resolves `PointcutLibrary` as a class name, looks up `auditableOrderOps` method in its `@Aspect` instance, and uses its compiled `@Pointcut` expression.

**Call flow for `svc.place("ORD-1")`:**
1. Proxy intercepts `place`.
2. Advice chain: `AuditAspect.audit` (matches `auditableOrderOps()`) → `MetricsAspect.metric` (matches `nonCancelOrderOps()`) → real `place("ORD-1")`.
3. Returns.

**Expected output:**
```
--- place (Auditable) ---
[AUDIT] @Auditable method: place
[METRIC] Non-cancel op: place
Placed: ORD-1
--- cancel (not Auditable) ---
Cancelled: ORD-1
--- ship (Auditable) ---
[AUDIT] @Auditable method: ship
[METRIC] Non-cancel op: ship
Shipped: ORD-1
```

## 7. Gotchas & takeaways

> **`@Pointcut` method must have an empty body.** The body is never called — the method name is just a symbol. If you add code to the body, Spring silently ignores it (the proxy does not call the method; it reads its annotation).

> **Cross-aspect pointcut reference requires the fully-qualified class name.** `"PointcutLibrary.auditableOrderOps()"` — not just `"auditableOrderOps()"`. Without the class prefix, Spring cannot resolve the reference and throws `IllegalArgumentException`.

- Private `@Pointcut` methods are accessible only within the same aspect class. Use `public` to share across aspects.
- Pointcut expressions are compiled once at startup, not re-evaluated on each invocation — they are very fast at runtime.
- Avoid very broad expressions like `execution(* *(..))` — they match everything including Spring internals and cause unexpected advice on infrastructure beans.
- A good naming convention: `verbNounLayer()` — e.g., `writeServiceLayer()`, `readRepositoryLayer()`, `publicControllerEndpoints()`.
