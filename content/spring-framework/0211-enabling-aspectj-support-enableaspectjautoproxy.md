---
card: spring-framework
gi: 211
slug: enabling-aspectj-support-enableaspectjautoproxy
title: "Enabling @AspectJ support (@EnableAspectJAutoProxy)"
---

## 1. What it is

`@EnableAspectJAutoProxy` is a Spring configuration annotation that activates the `@AspectJ`-style AOP support. It registers `AnnotationAwareAspectJAutoProxyCreator` as a `BeanPostProcessor` in the application context, which scans all beans for `@Aspect` classes and automatically creates proxies for beans that match any declared pointcut.

Without `@EnableAspectJAutoProxy`, having `@Aspect` beans in the context does nothing — they sit there as ordinary beans and their advice never fires.

## 2. Why & when

Spring AOP is opt-in. You explicitly enable it by:
- Adding `@EnableAspectJAutoProxy` to a `@Configuration` class, or
- Using Spring Boot, which auto-enables it via `spring-boot-starter-aop`.

You need to understand this to:
- Enable AOP in plain Spring Framework applications (without Spring Boot).
- Control the proxy strategy (`proxyTargetClass = true/false`).
- Expose the proxy via `exposeProxy = true` for self-invocation workarounds.

You usually set this once per application context. Multiple `@EnableAspectJAutoProxy` declarations are harmless but redundant.

## 3. Core concept

Think of `@EnableAspectJAutoProxy` as flipping a switch in the application context factory. Before the switch: beans are created and returned as-is. After the switch: the factory additionally runs every created bean through `AnnotationAwareAspectJAutoProxyCreator`, which checks each bean against all registered `@Aspect` pointcuts and wraps matching beans in proxies.

Two important attributes:

```java
@EnableAspectJAutoProxy(
    proxyTargetClass = true,  // CGLIB (true) or JDK dynamic proxy (false, requires interface)
    exposeProxy = true         // store proxy in AopContext.currentProxy() for self-invocation
)
```

`exposeProxy = true` is the clean solution for the self-invocation proxy bypass: inside a bean method, you can call `((MyService) AopContext.currentProxy()).anotherMethod()` to go through the proxy instead of `this`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg">
  <!-- Without @EnableAspectJAutoProxy -->
  <rect x="15" y="20" width="270" height="150" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5 3"/>
  <text x="150" y="42" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Without @EnableAspectJAutoProxy</text>
  <rect x="35" y="60" width="100" height="40" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="85" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@Aspect bean</text>
  <text x="85" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(inert)</text>
  <rect x="155" y="60" width="110" height="40" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="210" y="83" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Service bean</text>
  <text x="210" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(raw, no proxy)</text>
  <text x="150" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">advice never fires</text>

  <!-- With @EnableAspectJAutoProxy -->
  <rect x="315" y="20" width="310" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="470" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">With @EnableAspectJAutoProxy</text>

  <rect x="330" y="60" width="100" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="380" y="83" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Aspect bean</text>
  <text x="380" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(active)</text>

  <line x1="430" y1="80" x2="455" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="443" y="73" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wraps</text>

  <rect x="455" y="58" width="110" height="52" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="79" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">AOP Proxy</text>
  <text x="510" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wraps Service</text>
  <text x="510" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">advice fires</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

Without the annotation, `@Aspect` beans are passive. The annotation activates the post-processor that wires them into proxies.

## 5. Runnable example

Scenario: a **request validator** — first showing that AOP is silent without `@EnableAspectJAutoProxy`, then enabling it, then using `exposeProxy = true` for clean self-invocation.

### Level 1 — Basic

Without `@EnableAspectJAutoProxy`: the `@Aspect` bean exists but its advice never fires.

```java
// EnableAopDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.annotation.*;

@Configuration
// @EnableAspectJAutoProxy  ← intentionally absent
@ComponentScan
public class EnableAopDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EnableAopDemo.class);
        ctx.getBean(RequestValidator.class).validate("input-1");
        System.out.println("Notice: no [ASPECT] output — AOP is not enabled");
        ctx.close();
    }
}

@org.springframework.stereotype.Service
class RequestValidator {
    public void validate(String input) {
        System.out.println("Validating: " + input);
    }
}

@Aspect
@org.springframework.stereotype.Component
class ValidationAspect {
    @Before("execution(* RequestValidator.*(..))")
    public void before() {
        System.out.println("[ASPECT] Before validate");
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. EnableAopDemo.java`

`[ASPECT]` never appears. `ValidationAspect` is a bean in the context, but no post-processor reads its `@Aspect` annotation and creates proxies.

---

### Level 2 — Intermediate

Add `@EnableAspectJAutoProxy` — the aspect fires.

```java
// EnableAopDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy   // ← the switch
@ComponentScan
public class EnableAopDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EnableAopDemo.class);
        var validator = ctx.getBean(RequestValidator.class);
        validator.validate("form-data");
        validator.validate("api-call");
        ctx.close();
    }
}

@org.springframework.stereotype.Service
class RequestValidator {
    public void validate(String input) {
        System.out.println("Validating: " + input);
    }
}

@Aspect
@org.springframework.stereotype.Component
class ValidationAspect {
    @Before("execution(* RequestValidator.validate(..))")
    public void before(JoinPoint jp) {
        System.out.println("[ASPECT] Intercepted: " + jp.getArgs()[0]);
    }
}
```

How to run: same classpath

Now `[ASPECT]` appears before each `Validating:` line. The single annotation change wired the entire AOP machinery.

---

### Level 3 — Advanced

`exposeProxy = true` + `AopContext.currentProxy()` to fix the self-invocation problem without injecting `self`.

```java
// EnableAopDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy(exposeProxy = true)  // store proxy in thread-local
@ComponentScan
public class EnableAopDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EnableAopDemo.class);
        var svc = ctx.getBean(RequestValidator.class);
        System.out.println("--- direct call (advice fires) ---");
        svc.validate("direct");

        System.out.println("--- validate calls sanitize() via this (NO advice) ---");
        svc.validateAndSanitize("raw-input");

        System.out.println("--- validate calls sanitize() via proxy (advice fires) ---");
        svc.validateWithProxy("raw-input");
        ctx.close();
    }
}

@org.springframework.stereotype.Service
class RequestValidator {
    public void validate(String input) {
        System.out.println("Validated: " + input);
    }

    public void sanitize(String input) {
        System.out.println("Sanitized: " + input);
    }

    public void validateAndSanitize(String input) {
        validate(input);
        this.sanitize(input); // self-invocation: proxy bypassed for sanitize()
    }

    public void validateWithProxy(String input) {
        validate(input);
        // Use AopContext to get the proxy — advice fires for sanitize()
        ((RequestValidator) AopContext.currentProxy()).sanitize(input);
    }
}

@Aspect
@org.springframework.stereotype.Component
class ValidationAspect {
    @Before("execution(* RequestValidator.*(..))")
    public void before(JoinPoint jp) {
        System.out.println("[ASPECT] " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

In `validateAndSanitize`, `this.sanitize(input)` bypasses the proxy — no `[ASPECT]` for `sanitize`. In `validateWithProxy`, `AopContext.currentProxy()` retrieves the proxy from a thread-local (set by `exposeProxy = true`) — `sanitize` IS intercepted.

## 6. Walkthrough

**`@EnableAspectJAutoProxy` bootstrap:**
1. Spring processes `@Configuration` class and finds `@EnableAspectJAutoProxy`.
2. This imports `AspectJAutoProxyRegistrar` which calls `AopConfigUtils.registerAspectJAnnotationAutoProxyCreatorIfNecessary(registry)`.
3. That registers `AnnotationAwareAspectJAutoProxyCreator` as a `BeanDefinition` in the context.
4. During context refresh, this `BeanPostProcessor` is instantiated early (before ordinary beans).

**Proxy creation for `RequestValidator`:**
1. `RequestValidator` bean is instantiated.
2. `AnnotationAwareAspectJAutoProxyCreator.postProcessAfterInitialization(bean, "requestValidator")` is called.
3. It scans all `@Aspect` beans — finds `ValidationAspect`.
4. Evaluates `execution(* RequestValidator.*(..))` against `RequestValidator` — matches.
5. Creates a CGLIB proxy subclassing `RequestValidator`, wrapping `validate`, `sanitize`, `validateAndSanitize`, `validateWithProxy`.
6. Returns the proxy to the context.

**`exposeProxy = true` thread-local mechanism:**
- When `svc.validateWithProxy("raw-input")` is called on the proxy, before invoking the real method, the proxy stores itself in `AopContext.currentProxy()` — a `ThreadLocal<Object>`.
- Inside `validateWithProxy`, `AopContext.currentProxy()` reads the thread-local → returns the proxy.
- Casting to `RequestValidator` succeeds (CGLIB proxy is a subclass).
- `sanitize()` is called on the proxy → advice chain runs.

**Expected output:**
```
--- direct call (advice fires) ---
[ASPECT] validate
Validated: direct
--- validate calls sanitize() via this (NO advice) ---
[ASPECT] validateAndSanitize
[ASPECT] validate
Validated: raw-input
Sanitized: raw-input          ← no [ASPECT] for sanitize
--- validate calls sanitize() via proxy (advice fires) ---
[ASPECT] validateWithProxy
[ASPECT] validate
Validated: raw-input
[ASPECT] sanitize             ← advice fires via proxy
Sanitized: raw-input
```

## 7. Gotchas & takeaways

> **Spring Boot auto-enables AOP.** `spring-boot-starter-aop` (or any starter that depends on it) adds `@EnableAspectJAutoProxy` automatically. Adding it again in your `@Configuration` is harmless but redundant.

> **`exposeProxy = true` has a performance cost.** Storing the proxy in a `ThreadLocal` on every proxied method call adds overhead. Use it only where self-invocation is genuinely required, not as a blanket setting.

- The annotation can appear on any `@Configuration` class, but putting it on the root application configuration class makes it easiest to find.
- `proxyTargetClass = true` (CGLIB) is the default when `@EnableAspectJAutoProxy` is added without arguments in Spring Boot; `proxyTargetClass = false` forces JDK dynamic proxies.
- In an XML-configured Spring application, the equivalent is `<aop:aspectj-autoproxy/>` in the XML.
- `AnnotationAwareAspectJAutoProxyCreator` also processes `@Transactional`, `@Cacheable`, and `@PreAuthorize` — it is the single post-processor behind all of Spring's annotation-driven AOP features.
