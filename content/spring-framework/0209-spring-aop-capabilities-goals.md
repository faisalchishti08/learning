---
card: spring-framework
gi: 209
slug: spring-aop-capabilities-goals
title: Spring AOP capabilities & goals
---

## 1. What it is

**Spring AOP** is a proxy-based, runtime-weaving AOP implementation that is intentionally *not* a full AspectJ replacement. Its goals are pragmatic: solve the 80% of AOP use cases (logging, transactions, security, caching) with minimal friction inside a Spring application context, without requiring a special compiler or Java agent.

Spring AOP supports the **@AspectJ annotation style** (same syntax as full AspectJ) but executes advice through plain Java proxies — no bytecode manipulation. This makes it simpler, portable, and fully compatible with standard Java tooling.

## 2. Why & when

Understanding Spring AOP's boundaries prevents two common mistakes:
1. Expecting it to intercept field access, constructor calls, or static methods — it can't (proxy-only, method-execution join points only).
2. Reaching for full AspectJ when Spring AOP would suffice — unnecessary complexity.

Use Spring AOP when:
- You need method-level interception on Spring-managed beans.
- The codebase already uses Spring and you want zero extra dependencies.
- You want `@Transactional`, `@Cacheable`, `@PreAuthorize` to work (all use Spring AOP internally).

Switch to full AspectJ when:
- You need to intercept field access, constructor execution, or `static` method calls.
- You need aspects on objects not managed by Spring (domain objects created with `new`).
- You need compile-time or load-time weaving for performance.

## 3. Core concept

Spring AOP's design philosophy: "enough AOP to solve practical enterprise problems, no more."

Key capabilities and limitations:

| Capability | Spring AOP | Full AspectJ |
|------------|-----------|--------------|
| Method execution join points | Yes | Yes |
| Field get/set join points | **No** | Yes |
| Constructor execution | **No** | Yes |
| Static method interception | **No** | Yes |
| Objects not managed by Spring | **No** | Yes |
| Weaving mechanism | Runtime proxy | Compile-time or load-time |
| Extra tooling required | None | AspectJ compiler or agent |
| @AspectJ annotation syntax | Yes | Yes |

The same `@Aspect`, `@Pointcut`, `@Before`, `@Around` annotations work identically in both — meaning you can start with Spring AOP and migrate to AspectJ later by adding the compiler without changing annotation code.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Spring AOP circle -->
  <ellipse cx="230" cy="115" rx="175" ry="75" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="230" y="90" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">Spring AOP</text>
  <text x="230" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">method execution join points</text>
  <text x="230" y="126" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Spring-managed beans only</text>
  <text x="230" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">runtime proxies</text>
  <text x="230" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">covers 80% of enterprise AOP needs</text>

  <!-- Full AspectJ outer ring (dashed) -->
  <ellipse cx="400" cy="115" rx="210" ry="82" fill="none" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="6 3"/>
  <text x="540" y="68" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Full AspectJ adds:</text>
  <text x="545" y="86" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">field/constructor/static</text>
  <text x="545" y="101" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">non-Spring objects</text>
  <text x="545" y="116" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">compile/load-time weaving</text>
</svg>

Spring AOP is a purposeful subset of full AspectJ. Most Spring applications never need to leave the inner circle.

## 5. Runnable example

Scenario: a **cache warming service** — demonstrating Spring AOP capabilities (method interception), then hitting a limitation (inner class new-instance bypass), then correctly understanding the scope.

### Level 1 — Basic

Spring AOP capability: intercept any public method on a Spring bean.

```java
// SpringAopCapDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SpringAopCapDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpringAopCapDemo.class);
        ctx.getBean(CacheService.class).load("users");
        ctx.getBean(CacheService.class).evict("users");
        ctx.close();
    }
}

@Service
class CacheService {
    public void load(String key) {
        System.out.println("Cache load: " + key);
    }
    public void evict(String key) {
        System.out.println("Cache evict: " + key);
    }
}

@Aspect
@Component
class MonitorAspect {
    @Before("execution(* CacheService.*(..))")
    public void monitor(org.aspectj.lang.JoinPoint jp) {
        System.out.println("[MONITOR] " + jp.getSignature().toShortString());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. SpringAopCapDemo.java`

Both `load` and `evict` are intercepted because they are public methods called through the Spring proxy. This covers the typical use case.

---

### Level 2 — Intermediate

Capability boundary: demonstrate that Spring AOP intercepts on Spring-managed beans but NOT on objects created with `new`.

```java
// SpringAopCapDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SpringAopCapDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpringAopCapDemo.class);

        // Managed bean — proxy exists, aspect fires
        CacheService managed = ctx.getBean(CacheService.class);
        System.out.println("--- managed bean ---");
        managed.load("config");

        // Unmanaged object — no proxy, aspect NEVER fires
        CacheService raw = new CacheService();
        System.out.println("--- unmanaged (new) ---");
        raw.load("config"); // no [MONITOR] output
        ctx.close();
    }
}

@Service
class CacheService {
    public void load(String key) {
        System.out.println("Cache load: " + key);
    }
}

@Aspect
@Component
class MonitorAspect {
    @Before("execution(* CacheService.*(..))")
    public void monitor(JoinPoint jp) {
        System.out.println("[MONITOR] " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath

`managed.load("config")` prints `[MONITOR]` because `managed` is the proxy. `raw.load("config")` prints nothing from the aspect — `raw` is a plain Java object, not Spring-managed, not proxied.

---

### Level 3 — Advanced

Demonstrate that Spring AOP cannot intercept `static` method calls or field reads — and show the correct workaround (instance method delegation).

```java
// SpringAopCapDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SpringAopCapDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SpringAopCapDemo.class);
        var svc = ctx.getBean(CacheService.class);

        System.out.println("--- static call (NOT intercepted) ---");
        CacheService.clearAll(); // static method: proxy cannot intercept this

        System.out.println("--- instance method (intercepted) ---");
        svc.clear("users"); // instance method: proxy intercepts

        System.out.println("--- field read (NOT intercepted) ---");
        System.out.println("maxSize field: " + svc.maxSize); // direct field: no proxy
        ctx.close();
    }
}

@Service
class CacheService {
    public int maxSize = 1000; // public field (bad practice, but Spring AOP cannot intercept reads)

    // Spring AOP CANNOT intercept this — static method
    public static void clearAll() {
        System.out.println("Static: cleared all caches");
    }

    // Spring AOP CAN intercept this — instance method via proxy
    public void clear(String key) {
        System.out.println("Instance: cleared " + key);
        CacheService.clearAll(); // static call inside — also NOT intercepted
    }
}

@Aspect
@Component
class MonitorAspect {
    // This pointcut tries to match all CacheService methods including static — but static won't fire
    @Before("execution(* CacheService.*(..))")
    public void monitor(JoinPoint jp) {
        System.out.println("[MONITOR] " + jp.getSignature().toShortString());
    }
}
```

How to run: same classpath

`[MONITOR]` appears only for `svc.clear("users")`. The static call and the field read are invisible to the proxy. This is a fundamental boundary of Spring AOP's proxy mechanism.

## 6. Walkthrough

**Why static methods are not interceptable (Level 3):**

Spring AOP wraps beans in a proxy using CGLIB (subclassing) or JDK dynamic proxies (interface). In both cases, the proxy *overrides instance methods*. Static methods belong to the class itself, not to an instance — they cannot be overridden. When `CacheService.clearAll()` is called, it goes directly to the class, bypassing any proxy.

**Why `new CacheService()` bypasses aspects (Level 2):**

A proxy is created by Spring's `BeanPostProcessor` infrastructure — this only runs for beans created by the Spring container. `new CacheService()` is plain Java allocation: no container involvement, no post-processing, no proxy. The real `CacheService` instance is returned, and its methods have no advice wired.

**The full capability/limitation loop:**
1. Spring scans and creates `CacheService` bean.
2. `AnnotationAwareAspectJAutoProxyCreator` wraps it in a CGLIB proxy.
3. The proxy overrides `load()`, `evict()`, `clear()` — all public instance methods.
4. The proxy does NOT override `clearAll()` (static) or intercept `maxSize` field access.
5. Any caller that obtains the bean via `ctx.getBean()` or `@Autowired` gets the proxy.
6. Any caller that does `new CacheService()` gets the raw target — no proxy.

**Spring's own AOP use:**
`@Transactional`, `@Cacheable`, and `@PreAuthorize` all work via exactly this mechanism. They are `@Aspect` classes registered by Spring Boot auto-configuration, weaving into your beans at startup. This is why they fail silently on self-invocations and on non-Spring objects.

## 7. Gotchas & takeaways

> **`@Transactional` on `private` methods silently does nothing.** Spring AOP cannot proxy private methods. The `@Transactional` annotation is read by Spring, but the proxy cannot override a private method — the transaction never starts. Always put `@Transactional` on `public` methods.

> **Spring AOP is not full AspectJ — but it uses AspectJ's annotation syntax.** The annotations (`@Aspect`, `@Before`, etc.) come from the `aspectjweaver.jar` but the *execution engine* is Spring's proxy-based runtime, not the AspectJ bytecode weaver. They look the same, but the limitations differ.

- Spring AOP join point model: **method execution only**. No field access, no constructors, no static methods.
- Objects must be Spring-managed (obtained from context or `@Autowired`) for AOP to apply.
- Spring AOP is zero-overhead for non-matched methods — the proxy only intercepts methods that match at least one pointcut.
- For Spring Boot apps, Spring AOP is available by default — no extra dependencies beyond `spring-boot-starter`.
- Full AspectJ requires either the AspectJ compiler (`ajc`) or the AspectJ load-time weaving agent (`-javaagent:aspectjweaver.jar`) — a significant toolchain change.
