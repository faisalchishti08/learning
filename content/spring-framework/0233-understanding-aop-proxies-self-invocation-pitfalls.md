---
card: spring-framework
gi: 233
slug: understanding-aop-proxies-self-invocation-pitfalls
title: Understanding AOP proxies & self-invocation pitfalls
---

## 1. What it is

Spring AOP works by wrapping beans in a proxy. Every incoming call from outside the bean travels through the proxy — triggering any matching advice. But when a method inside the bean calls another method on the **same object** (`this.someMethod()`), that call goes **directly** to the target, bypassing the proxy entirely. No proxy intercept means no advice fires — even if a matching pointcut exists.

```java
@Service
public class OrderService {
    public void placeOrder() {
        this.sendConfirmation();   // DOES NOT trigger @Transactional on sendConfirmation
    }

    @Transactional
    public void sendConfirmation() { /* ... */ }
}
```

This is called the **self-invocation problem** and is the most common Spring AOP surprise in production.

## 2. Why & when

The problem occurs any time you annotate a method with `@Transactional`, `@Cacheable`, `@Async`, `@Retryable`, or any custom `@Aspect` advice — and then call that method from another method in the same class.

It matters most for:

- `@Transactional` inner calls — the transaction does not start; data changes may commit without isolation.
- `@Cacheable` inner calls — the cache is never consulted; results are never stored.
- `@Async` inner calls — the call runs synchronously on the calling thread.

The reason is fundamental to proxy-based AOP: the proxy holds a reference to the raw target object. When the target object calls `this.foo()`, it calls through the raw reference, not through the proxy.

## 3. Core concept

```
External caller → Proxy → Target.placeOrder()
                             ↓
                         this.sendConfirmation()   ← raw this, bypasses proxy
                             ↓
                         Target.sendConfirmation()  ← no advice fires
```

Three solutions exist:

1. **Refactor** — move `sendConfirmation` into a separate Spring bean and inject it.
2. **Self-inject** — inject the bean into itself (Spring supports this since 4.3 with `@Lazy`).
3. **`AopContext.currentProxy()`** — retrieve the proxy programmatically and call through it.

All three force the call to route through the proxy. Solution 1 is cleanest; solution 3 is useful for legacy code but couples the class to Spring AOP infrastructure.

## 4. Diagram

<svg viewBox="0 0 720 260" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="red" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#f85149"/>
    </marker>
    <marker id="blue" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- Caller -->
  <rect x="10" y="90" width="90" height="40" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="55" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">External Caller</text>

  <!-- Arrow caller → proxy -->
  <line x1="102" y1="110" x2="178" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Proxy -->
  <rect x="178" y="70" width="130" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="243" y="95" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Proxy</text>
  <text x="243" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">advice fires ✓</text>
  <text x="243" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ placeOrder()</text>
  <text x="243" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wraps raw target</text>

  <!-- Arrow proxy → target.placeOrder -->
  <line x1="310" y1="110" x2="380" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Target -->
  <rect x="380" y="40" width="200" height="175" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="64" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Target (raw this)</text>
  <line x1="390" y1="72" x2="570" y2="72" stroke="#8b949e" stroke-width="0.5"/>
  <text x="480" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">placeOrder() {</text>
  <text x="480" y="110" fill="#f85149" font-size="10" text-anchor="middle" font-family="monospace">  this.sendConfirmation();</text>
  <text x="480" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">}</text>
  <line x1="390" y1="138" x2="570" y2="138" stroke="#8b949e" stroke-width="0.5"/>
  <text x="480" y="158" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">@Transactional</text>
  <text x="480" y="175" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">sendConfirmation() {}</text>

  <!-- Self-invocation arrow (red = bad) -->
  <path d="M480 128 Q520 175 480 185" stroke="#f85149" stroke-width="1.5" fill="none" marker-end="url(#red)"/>
  <text x="570" y="165" fill="#f85149" font-size="9" font-family="sans-serif">self-invoke</text>
  <text x="570" y="178" fill="#f85149" font-size="9" font-family="sans-serif">(no proxy!)</text>
  <text x="570" y="191" fill="#f85149" font-size="9" font-family="sans-serif">advice SKIPPED</text>
</svg>

External calls route through the proxy (advice fires). Internal `this.` calls bypass the proxy — advice is silently skipped.

## 5. Runnable example

Scenario: an **`OrderService`** where `placeOrder()` internally calls `sendConfirmation()` — first showing the bug, then fixing with self-injection, then with `AopContext.currentProxy()`.

### Level 1 — Basic

The bug: `@Transactional` on `sendConfirmation()` does not fire when called from `placeOrder()`.

```java
// SelfInvocationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SelfInvocationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SelfInvocationDemo.class);
        OrderService svc = ctx.getBean(OrderService.class);
        svc.placeOrder("ORD-001");
        ctx.close();
    }
}

@Service
class OrderService {
    public void placeOrder(String orderId) {
        System.out.println("[placeOrder] starting for " + orderId);
        // BUG: calls this.sendConfirmation() — bypasses proxy, @Audited does not fire
        this.sendConfirmation(orderId);
        System.out.println("[placeOrder] done");
    }

    @Audited                      // custom annotation
    public void sendConfirmation(String orderId) {
        System.out.println("[sendConfirmation] email sent for " + orderId);
    }
}

@interface Audited {}

@Aspect @Component
class AuditAspect {
    @Before("@annotation(Audited)")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().toShortString() + " called");
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. SelfInvocationDemo.java`

Output: `[placeOrder] starting …` → `[sendConfirmation] email sent …` — but **`[AUDIT]` never prints**. The aspect on `sendConfirmation` is silently skipped because `this.sendConfirmation()` bypasses the proxy.

---

### Level 2 — Intermediate

Fix with **self-injection** — `OrderService` injects itself lazily, routing the call through the proxy.

```java
// SelfInvocationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class SelfInvocationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SelfInvocationDemo.class);
        OrderService svc = ctx.getBean(OrderService.class);
        svc.placeOrder("ORD-002");
        ctx.close();
    }
}

@Service
class OrderService {
    @Lazy @Autowired
    private OrderService self;         // inject the proxy of THIS bean

    public void placeOrder(String orderId) {
        System.out.println("[placeOrder] starting for " + orderId);
        // FIX: call via the proxy reference — advice fires
        self.sendConfirmation(orderId);
        System.out.println("[placeOrder] done");
    }

    @Audited
    public void sendConfirmation(String orderId) {
        System.out.println("[sendConfirmation] email sent for " + orderId);
    }
}

@interface Audited {}

@Aspect @Component
class AuditAspect {
    @Before("@annotation(Audited)")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().toShortString() + " called");
    }
}
```

How to run: same classpath

Now output includes `[AUDIT] sendConfirmation(..) called` — the advice fires. `@Lazy` is required to break the circular dependency that would occur if `OrderService` tried to inject itself eagerly.

---

### Level 3 — Advanced

Fix with **`AopContext.currentProxy()`** — no self-injection required, but exposes the Spring AOP API. Also shows introspection of the proxy vs target.

```java
// SelfInvocationDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAspectJAutoProxy(exposeProxy = true)   // ← required for AopContext to work
@ComponentScan
public class SelfInvocationDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SelfInvocationDemo.class);
        OrderService svc = ctx.getBean(OrderService.class);

        System.out.println("Bean is proxy? " + AopUtils.isAopProxy(svc));
        System.out.println("Bean class: " + svc.getClass().getSimpleName());

        svc.placeOrder("ORD-003");
        ctx.close();
    }
}

@Service
class OrderService {
    public void placeOrder(String orderId) {
        System.out.println("[placeOrder] starting for " + orderId);
        // FIX via AopContext — retrieves current proxy from ThreadLocal
        ((OrderService) AopContext.currentProxy()).sendConfirmation(orderId);
        System.out.println("[placeOrder] done");
    }

    @Audited
    public void sendConfirmation(String orderId) {
        System.out.println("[sendConfirmation] email sent for " + orderId);
    }
}

@interface Audited {}

@Aspect @Component
class AuditAspect {
    @Before("@annotation(Audited)")
    public void audit(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().toShortString() + " called");
    }
}
```

How to run: same classpath + `spring-context.jar`

`exposeProxy = true` stores the current proxy in a `ThreadLocal` on each call. `AopContext.currentProxy()` retrieves it. Casting to `OrderService` and calling `sendConfirmation` now goes through the proxy. The advice fires. This approach is less invasive for legacy code where adding a new bean or self-injection would break a lot of existing code.

## 6. Walkthrough

**Level 1 — Bug path:**

```
External caller
  → Proxy.placeOrder("ORD-001")         [AuditAspect runs? → @Audited not on placeOrder → NO]
    → AopInterceptorChain exhausted
      → Target.placeOrder("ORD-001")    [prints "[placeOrder] starting"]
        → this.sendConfirmation("ORD-001")  ← raw 'this', not proxy
          → Target.sendConfirmation()   [prints "[sendConfirmation] email sent"]
          NO advice fires — proxy was bypassed
```

**Level 2 — Self-inject fix path:**

```
External caller
  → Proxy.placeOrder("ORD-002")
    → Target.placeOrder("ORD-002")
      → self.sendConfirmation("ORD-002")   ← self IS the proxy
        → Proxy.sendConfirmation("ORD-002")
          → AuditAspect.audit()  [prints "[AUDIT] sendConfirmation(..)"]
            → Target.sendConfirmation("ORD-002")  [prints "[sendConfirmation] email sent"]
```

**Level 3 — AopContext fix path:**

```
External caller
  → Proxy.placeOrder("ORD-003")          [exposeProxy=true → proxy stored in ThreadLocal]
    → Target.placeOrder("ORD-003")
      → AopContext.currentProxy()         [reads ThreadLocal → returns Proxy ref]
      → cast to OrderService
      → Proxy.sendConfirmation("ORD-003") [routes through proxy → advice fires]
        → AuditAspect.audit()  [prints "[AUDIT]"]
          → Target.sendConfirmation("ORD-003") [prints "[sendConfirmation]"]
```

## 7. Gotchas & takeaways

> **This is the single most common AOP bug in Spring production apps.** `@Transactional` or `@Cacheable` on a private helper method that's called internally will silently not work. The fix is always "route through the proxy", not a Spring bug.

> **`exposeProxy = true` has a small performance cost** — a `ThreadLocal` write and read on every proxied method call. Acceptable for most apps, but avoid it in hot paths. Prefer the self-inject approach.

> **`private` methods are NEVER proxied** regardless of proxy type. `@Transactional` on a private method is always ignored. No exception, no warning.

- Self-invocation through `this` bypasses the proxy; the fix is always "call through the proxy".
- Cleanest fix: move the called method to a separate `@Component` and inject it.
- `@Lazy @Autowired private MyService self` works for self-injection; `@Lazy` breaks the circular dependency.
- `AopContext.currentProxy()` requires `@EnableAspectJAutoProxy(exposeProxy = true)`; throws `IllegalStateException` if called in a non-proxied context.
- `AopUtils.isAopProxy(bean)` tests if an object is a Spring proxy; `AopUtils.getTargetClass(bean)` gives the original class.
