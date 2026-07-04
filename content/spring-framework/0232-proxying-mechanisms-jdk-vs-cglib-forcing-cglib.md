---
card: spring-framework
gi: 232
slug: proxying-mechanisms-jdk-vs-cglib-forcing-cglib
title: Proxying mechanisms (JDK vs CGLIB) & forcing CGLIB
---

## 1. What it is

Spring AOP uses two proxy strategies at runtime: **JDK dynamic proxies** and **CGLIB subclass proxies**. JDK proxies implement a Java interface and intercept calls through `java.lang.reflect.Proxy`. CGLIB generates a bytecode subclass of the target class at runtime and overrides methods. Spring Boot 2.x+ defaults to CGLIB for all Spring-managed beans; Spring Framework without Boot defaults to JDK when an interface is present.

```java
// Force CGLIB even when interface exists:
@EnableAspectJAutoProxy(proxyTargetClass = true)
```

The choice determines what types you can inject, how `final` methods behave, and what tools like Mockito must do to mock your beans.

## 2. Why & when

| Dimension | JDK proxy | CGLIB |
|-----------|-----------|-------|
| Requires interface | Yes — target must implement at least one | No — works on concrete classes |
| `final` methods | Handled (interface method cannot be final) | Silently bypassed — no advice fires |
| `final` classes | Cannot proxy | Cannot proxy (cannot subclass) |
| Performance | Reflection per call | Byte-code; slightly faster (modern JVMs close the gap) |
| Injection by concrete type | Fails — proxy only implements interface | Works — proxy IS a subclass |
| Spring Boot default | Not default | **Default since Boot 2.x** |

Force CGLIB when: you inject by concrete class (common with Spring Boot auto-configuration), or your team forgets to code to interfaces.

## 3. Core concept

`DefaultAopProxyFactory.createAopProxy()` runs this decision tree:

1. Is `proxyTargetClass = true`? → CGLIB (unless target is an interface or a `@FunctionalInterface`).
2. Does the target class implement at least one non-Spring-internal interface? → JDK.
3. Otherwise → CGLIB.

CGLIB generates a subclass named something like `OrderService$$SpringCGLIB$$0` with one override per non-final, non-static, non-private method. Each override calls the CGLIB `MethodInterceptor` callback which routes to Spring's `CglibAopProxy.DynamicAdvisedInterceptor`.

JDK proxies implement all declared interfaces and route through `JdkDynamicAopProxy.invoke()`.

Both eventually call `ReflectiveMethodInvocation.proceed()` to walk the advisor chain.

## 4. Diagram

<svg viewBox="0 0 700 250" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Decision -->
  <rect x="220" y="20" width="260" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="44" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">DefaultAopProxyFactory</text>
  <text x="350" y="62" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">proxyTargetClass? / has interface?</text>

  <!-- JDK branch -->
  <line x1="280" y1="82" x2="160" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="185" y="115" fill="#79c0ff" font-size="9" font-family="sans-serif">has interface &amp;&amp; !proxyTargetClass</text>

  <rect x="30" y="130" width="230" height="90" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="152" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">JDK Dynamic Proxy</text>
  <text x="145" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements declared interfaces</text>
  <text x="145" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">JdkDynamicAopProxy.invoke()</text>
  <text x="145" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inject by interface type only</text>
  <text x="145" y="215" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">cannot proxy final methods</text>

  <!-- CGLIB branch -->
  <line x1="420" y1="82" x2="540" y2="130" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="520" y="115" fill="#6db33f" font-size="9" font-family="sans-serif">proxyTargetClass=true or no interface</text>

  <rect x="440" y="130" width="240" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="560" y="152" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">CGLIB Subclass Proxy</text>
  <text x="560" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends target class</text>
  <text x="560" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">DynamicAdvisedInterceptor</text>
  <text x="560" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">inject by concrete type ✓</text>
  <text x="560" y="215" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">final methods silently bypassed</text>
</svg>

Spring picks JDK or CGLIB at bean creation time. Boot 2.x+ defaults to CGLIB for all beans.

## 5. Runnable example

Scenario: an **`InventoryService`** — first using the default mechanism (JDK when interface present), then forcing CGLIB, then demonstrating what happens with `final` methods.

### Level 1 — Basic

Default JDK proxy when an interface is declared; inject and verify proxy type.

```java
// ProxyMechanismDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAspectJAutoProxy          // default: proxyTargetClass = false → JDK when interface present
@ComponentScan
public class ProxyMechanismDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyMechanismDemo.class);
        IInventoryService svc = ctx.getBean(IInventoryService.class);

        System.out.println("Proxy class: " + svc.getClass().getName());
        System.out.println("Is JDK proxy? " + java.lang.reflect.Proxy.isProxyClass(svc.getClass()));
        System.out.println("Implements interface? " + (svc instanceof IInventoryService));

        svc.reserve("WIDGET-A", 10);
        ctx.close();
    }
}

interface IInventoryService {
    void reserve(String sku, int qty);
}

@Component
class InventoryService implements IInventoryService {
    public void reserve(String sku, int qty) {
        System.out.println("Reserved " + qty + " × " + sku);
    }
}

@Aspect @Component
class AuditAspect {
    @Before("execution(* IInventoryService.*(..))")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().toShortString());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. ProxyMechanismDemo.java`

Output shows `$Proxy0` (or similar) — a JDK dynamic proxy. `Proxy.isProxyClass()` returns `true`. The proxy only implements `IInventoryService`; injecting by `InventoryService` concrete type would fail with `BeanNotOfRequiredTypeException`.

---

### Level 2 — Intermediate

Force **CGLIB** with `proxyTargetClass = true` — inject by concrete type.

```java
// ProxyMechanismDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAspectJAutoProxy(proxyTargetClass = true)   // ← force CGLIB
@ComponentScan
public class ProxyMechanismDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyMechanismDemo.class);

        // Can now inject by concrete type — CGLIB proxy is a subclass
        InventoryService svc = ctx.getBean(InventoryService.class);
        System.out.println("Proxy class:  " + svc.getClass().getName());
        System.out.println("Is JDK proxy? " + java.lang.reflect.Proxy.isProxyClass(svc.getClass()));
        System.out.println("Is subclass?  " + (svc instanceof InventoryService));

        svc.reserve("GADGET-B", 5);
        ctx.close();
    }
}

interface IInventoryService { void reserve(String sku, int qty); }

@Component
class InventoryService implements IInventoryService {
    public void reserve(String sku, int qty) {
        System.out.println("Reserved " + qty + " × " + sku);
    }
}

@Aspect @Component
class AuditAspect {
    @Before("execution(* IInventoryService.*(..))")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath

Class name now contains `$$SpringCGLIB$$0`. `svc instanceof InventoryService` is `true`. This is the Spring Boot default — you can `@Autowired InventoryService svc` directly without a dedicated interface.

---

### Level 3 — Advanced

Demonstrate that **`final` methods are silently bypassed** by CGLIB, and how to detect which methods are unproxied.

```java
// ProxyMechanismDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;
import java.lang.reflect.*;

@Configuration
@EnableAspectJAutoProxy(proxyTargetClass = true)
@ComponentScan
public class ProxyMechanismDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyMechanismDemo.class);
        InventoryService svc = ctx.getBean(InventoryService.class);

        System.out.println("=== Calling reserve (non-final) ===");
        svc.reserve("PART-C", 3);          // advice FIRES

        System.out.println("\n=== Calling replenish (final) ===");
        svc.replenish("PART-C", 100);      // advice DOES NOT fire — CGLIB cannot override final

        System.out.println("\n=== Listing final methods (unproxied) ===");
        for (Method m : InventoryService.class.getDeclaredMethods()) {
            if (Modifier.isFinal(m.getModifiers()))
                System.out.println("  FINAL (unproxied): " + m.getName());
        }

        ctx.close();
    }
}

@Component
class InventoryService {
    public void reserve(String sku, int qty) {
        System.out.println("Reserved " + qty + " × " + sku);
    }
    public final void replenish(String sku, int qty) {   // final — CGLIB cannot override
        System.out.println("Replenished " + qty + " × " + sku);
    }
}

@Aspect @Component
class AuditAspect {
    @Before("execution(* InventoryService.*(..))")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath

`reserve` fires the audit aspect. `replenish` (marked `final`) does not — CGLIB generates the subclass but cannot override `final`. No exception is thrown; advice is silently skipped. The reflection loop at the end identifies all such methods before deploying to production.

## 6. Walkthrough

**Proxy creation (at context startup):**

1. `AnnotationConfigApplicationContext` creates `InventoryService` as a raw bean.
2. `AnnotationAwareAspectJAutoProxyCreator` (the `BeanPostProcessor`) fires `postProcessAfterInitialization`.
3. It checks: should this bean be proxied? The `AuditAspect`'s pointcut matches `InventoryService` methods → yes.
4. It calls `DefaultAopProxyFactory.createAopProxy(config)`:
   - `proxyTargetClass=false` + `InventoryService implements IInventoryService` → **JDK proxy** (Level 1).
   - `proxyTargetClass=true` → **CGLIB** (Levels 2, 3).
5. The proxy replaces the raw bean in the context.

**Per-call flow for `svc.reserve("PART-C", 3)` (CGLIB, Level 3):**

```
caller → CGLIB proxy.reserve("PART-C", 3)
  → DynamicAdvisedInterceptor.intercept()
    → ReflectiveMethodInvocation.proceed()
      → AuditAspect.audit()         [prints "[AUDIT] reserve(..)"]
        → InventoryService.reserve() [prints "Reserved 3 × PART-C"]
      ← returns
    ← returns
  ← returns
← caller
```

**Per-call flow for `svc.replenish("PART-C", 100)` (CGLIB, `final`):**

```
caller → CGLIB proxy.replenish("PART-C", 100)
  CGLIB CANNOT override final → calls InventoryService.replenish() DIRECTLY
  No proxy intercept path → no advisor chain → no advice
```

No exception, no logging — silently passes through. This is a common production bug.

## 7. Gotchas & takeaways

> **`final` methods are CGLIB's silent trap.** CGLIB generates a subclass but cannot override `final`. Advice is silently skipped — no warning at startup or at call time. Audit your service classes for `final` methods if you rely on CGLIB-based AOP (e.g., `@Transactional`, `@Cacheable`).

> **Injecting by concrete type with JDK proxy fails at runtime, not compile time.** The compiler sees an `Object` reference; the `ClassCastException` or `BeanNotOfRequiredTypeException` only surfaces when Spring tries to inject the proxy. Add `proxyTargetClass = true` or code to an interface.

> **Spring Boot sets `spring.aop.proxy-target-class=true` by default.** This forces CGLIB globally. If you want JDK proxies, set it to `false` in `application.properties` — but then all injection must be by interface.

- JDK proxy: implement interface, fast, cannot be injected by concrete type.
- CGLIB: subclass generation, allows concrete-type injection, silently skips `final` methods.
- `((Advised) proxy).isProxyTargetClass()` tells you which mechanism was used at runtime.
- `Proxy.isProxyClass(obj.getClass())` distinguishes JDK proxies from CGLIB proxies.
- `final` classes cannot be proxied by either mechanism — Spring throws `AopConfigException` at startup.
