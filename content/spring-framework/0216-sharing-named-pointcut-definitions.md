---
card: spring-framework
gi: 216
slug: sharing-named-pointcut-definitions
title: Sharing named pointcut definitions
---

## 1. What it is

A named `@Pointcut` method declared in one `@Aspect` class can be referenced from a *different* `@Aspect` class using its fully-qualified name: `"ClassName.pointcutMethod()"`. This lets a team define a **pointcut library** — a single `@Aspect` class containing only `@Pointcut` declarations — and have multiple aspect classes reuse those definitions without duplication.

```java
// In PointcutLibrary.java
@Aspect @Component
public class PointcutLibrary {
    @Pointcut("execution(* com.example.service..*(..))")
    public void serviceLayer() {}
}

// In LoggingAspect.java
@Aspect @Component
public class LoggingAspect {
    @Before("PointcutLibrary.serviceLayer()")  // cross-class reference
    public void log(JoinPoint jp) { ... }
}
```

## 2. Why & when

In a multi-team project, pointcut expressions for common layers (service layer, repository layer, controller layer) should be defined once and reused. Without cross-aspect sharing:

- Each aspect redeclares the same `execution(* com.example.service.*.*(..))` string.
- Package renames require updating every aspect.
- There is no single authoritative definition to review.

With a pointcut library:
- One file defines all structural pointcuts.
- All advice references them by name.
- A package rename is a one-line change in the library.

Use this pattern in any codebase where multiple aspects target the same layers.

## 3. Core concept

Think of the pointcut library as a shared address book. Each aspect is a department; instead of each department keeping its own copy of everyone's contact details, they all look up the shared book. The address book contains only contact data (pointcut expressions), not actions (advice).

Visibility rules:
- `public` — accessible from any aspect class.
- `package-private` — accessible from aspect classes in the same package.
- `private` — accessible only within the same aspect class (no sharing).

The reference syntax in advice annotations: `"ClassName.methodName()"`. If the pointcut is in the same package as the referencing aspect, the unqualified class name works. Across packages, use the fully-qualified class name: `"com.example.aop.PointcutLibrary.serviceLayer()"`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Pointcut Library -->
  <rect x="15" y="30" width="230" height="150" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="130" y="52" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">PointcutLibrary</text>
  <text x="130" y="66" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Aspect @Component</text>

  <rect x="28" y="77" width="200" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="128" y="96" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">public void serviceLayer(){}</text>

  <rect x="28" y="115" width="200" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="128" y="134" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">public void repoLayer(){}</text>

  <rect x="28" y="152" width="200" height="22" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="128" y="166" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">public void writeOps(){}</text>

  <!-- Arrows to using aspects -->
  <line x1="245" y1="92" x2="310" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="245" y1="130" x2="310" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="245" y1="163" x2="310" y2="185" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>

  <!-- LoggingAspect -->
  <rect x="310" y="50" width="170" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="70" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">LoggingAspect</text>
  <text x="395" y="87" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Before("PointcutLibrary.serviceLayer()")</text>

  <!-- AuditAspect -->
  <rect x="310" y="108" width="170" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="128" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">AuditAspect</text>
  <text x="395" y="145" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">@Around("PointcutLibrary.writeOps()")</text>

  <!-- MetricsAspect -->
  <rect x="310" y="163" width="170" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="395" y="182" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MetricsAspect</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

One `PointcutLibrary` defines expressions; many aspect classes reference them by name.

## 5. Runnable example

Scenario: a **blogging platform** with three aspects (logging, security, metrics) that all target the same service layer — defined once in a pointcut library.

### Level 1 — Basic

One aspect referencing a named pointcut from another aspect class.

```java
// SharedPointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SharedPointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SharedPointcutDemo.class);
        ctx.getBean(PostService.class).publish("Hello World");
        ctx.close();
    }
}

@Service
class PostService {
    public void publish(String title) { System.out.println("Published: " + title); }
}

// Pointcut library — only pointcuts, no advice
@Aspect
@Component
class AppPointcuts {
    @Pointcut("execution(* PostService.*(..))")
    public void postOps() {}
}

// Consuming aspect — references AppPointcuts.postOps()
@Aspect
@Component
class LoggingAspect {
    @Before("AppPointcuts.postOps()")
    public void log(JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().getName());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. SharedPointcutDemo.java`

`LoggingAspect` references `AppPointcuts.postOps()` — a cross-class pointcut reference. Changing `AppPointcuts.postOps()` updates the behaviour of `LoggingAspect` automatically.

---

### Level 2 — Intermediate

Multiple aspects reusing the same library. Each aspect handles one concern; the library owns the structural rules.

```java
// SharedPointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME) @Target(ElementType.METHOD)
@interface Secured {}

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SharedPointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SharedPointcutDemo.class);
        var svc = ctx.getBean(PostService.class);
        System.out.println("--- publish ---");
        svc.publish("Article");
        System.out.println("--- delete (secured) ---");
        svc.delete(1L);
        ctx.close();
    }
}

@Service
class PostService {
    public void publish(String title) { System.out.println("Published: " + title); }
    @Secured
    public void delete(long id) { System.out.println("Deleted: " + id); }
}

@Aspect
@Component
class AppPointcuts {
    @Pointcut("execution(* PostService.*(..))")
    public void postOps() {}

    @Pointcut("@annotation(Secured)")
    public void securedOps() {}

    // Composed: secured post operations
    @Pointcut("postOps() && securedOps()")
    public void securedPostOps() {}
}

@Aspect
@Component
class LoggingAspect {
    @Before("AppPointcuts.postOps()")
    public void log(JoinPoint jp) {
        System.out.println("[LOG]      " + jp.getSignature().getName());
    }
}

@Aspect
@Component
class SecurityAspect {
    @Before("AppPointcuts.securedPostOps()")
    public void checkAuth(JoinPoint jp) {
        System.out.println("[SECURITY] Checking auth for: " + jp.getSignature().getName());
    }
}
```

How to run: same as Level 1

`publish` triggers only `[LOG]`. `delete` (which has `@Secured`) triggers both `[LOG]` and `[SECURITY]`. Both aspects reference the library — neither duplicates the `execution(* PostService.*(..))` expression.

---

### Level 3 — Advanced

Full library with multi-layer pointcuts (service + repository), fully-qualified cross-package reference, and three separate aspect classes.

```java
// SharedPointcutDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SharedPointcutDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SharedPointcutDemo.class);
        System.out.println("=== PostService.publish ===");
        ctx.getBean(PostService.class).publish("Tech news");
        System.out.println("=== PostRepository.save ===");
        ctx.getBean(PostRepository.class).save("Tech news");
        ctx.close();
    }
}

@Service  class PostService    { public void publish(String t) { System.out.println("Svc publish: " + t); } }
@Repository class PostRepository { public void save(String t)  { System.out.println("Repo save: " + t); } }

// ── Pointcut library ──────────────────────────────────────────────────
@Aspect
@Component
class AppPointcuts {
    @Pointcut("execution(* PostService.*(..))")
    public void serviceLayer() {}

    @Pointcut("execution(* PostRepository.*(..))")
    public void repoLayer() {}

    @Pointcut("serviceLayer() || repoLayer()")
    public void allApplicationOps() {}

    @Pointcut("serviceLayer() && !execution(* PostService.internal*(..))")
    public void publicServiceOps() {}
}

// ── Three consuming aspects ───────────────────────────────────────────
@Aspect @Component
class LoggingAspect {
    @Before("AppPointcuts.allApplicationOps()")
    public void log(JoinPoint jp) {
        System.out.println("[LOG]     " + jp.getSignature().toShortString());
    }
}

@Aspect @Component
class MetricsAspect {
    @Around("AppPointcuts.publicServiceOps()")
    public Object time(org.aspectj.lang.ProceedingJoinPoint pjp) throws Throwable {
        long t0 = System.currentTimeMillis();
        Object r = pjp.proceed();
        System.out.printf("[METRIC]  %s = %d ms%n",
            pjp.getSignature().getName(), System.currentTimeMillis() - t0);
        return r;
    }
}

@Aspect @Component
class AuditAspect {
    @After("AppPointcuts.repoLayer()")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT]   " + jp.getSignature().getName() + " completed");
    }
}
```

How to run: same classpath

`PostService.publish` fires `[LOG]` (allApplicationOps) and `[METRIC]` (publicServiceOps). `PostRepository.save` fires `[LOG]` (allApplicationOps) and `[AUDIT]` (repoLayer). Three aspects, zero duplication of structural expressions.

## 6. Walkthrough

**Pointcut resolution at startup:**
1. Spring builds a list of all `@Aspect` beans: `AppPointcuts`, `LoggingAspect`, `MetricsAspect`, `AuditAspect`.
2. For each `@Aspect`, it reads `@Pointcut` methods and compiles their expressions.
3. `AppPointcuts.allApplicationOps()` references `serviceLayer()` and `repoLayer()` — Spring resolves these by looking up `AppPointcuts.serviceLayer` and `AppPointcuts.repoLayer` in the same class.
4. `LoggingAspect.log` cites `"AppPointcuts.allApplicationOps()"` — Spring looks for class `AppPointcuts`, method `allApplicationOps`, and retrieves its compiled expression.

**Cross-aspect reference mechanics:**
- Spring uses `MethodMatcher` and `ClassFilter` compiled from the resolved expression.
- The reference resolves at startup, not at each call — no reflection overhead per invocation.
- If `AppPointcuts` is not in the context (e.g., not `@Component`), the reference fails with `IllegalArgumentException: Pointcut '…' cannot be found`.

**`publish` call flow:**
1. Proxy intercepts `PostService.publish("Tech news")`.
2. `allApplicationOps()` matches → `LoggingAspect.log` fires.
3. `publicServiceOps()` matches → `MetricsAspect.time` enters.
4. Inside `time`, `pjp.proceed()` calls real `publish`.
5. `time` records elapsed, prints `[METRIC]`.
6. `repoLayer()` does NOT match `PostService` → `AuditAspect.audit` does not fire.

**Expected output:**
```
=== PostService.publish ===
[LOG]     PostService.publish(..)
[METRIC]  publish = 0 ms
Svc publish: Tech news
=== PostRepository.save ===
[LOG]     PostRepository.save(..)
Repo save: Tech news
[AUDIT]   save completed
```

## 7. Gotchas & takeaways

> **A `private @Pointcut` cannot be referenced from another aspect class.** Spring will resolve the class but fail to access the private method, throwing `IllegalArgumentException`. Always use `public` for shared pointcuts.

> **The pointcut library class must be a Spring bean.** If `AppPointcuts` lacks `@Component` (or equivalent), Spring cannot look up its `@Pointcut` methods and all cross-aspect references fail at startup with a clear error.

- A pure pointcut library (`@Aspect @Component` with only `@Pointcut` methods and no advice) is a legitimate and useful pattern — it is not a code smell.
- Cross-package references need the fully-qualified class name: `"com.example.aop.AppPointcuts.serviceLayer()"`.
- Composition in the library (`allApplicationOps = serviceLayer() || repoLayer()`) is powerful: add a new layer to the library and all aspects that reference the composed pointcut automatically cover it.
- Keep the library's pointcuts at the structural level (packages, classes, annotations). Application-logic predicates (`args(OrderId)`) belong in the consuming aspect that needs them.
