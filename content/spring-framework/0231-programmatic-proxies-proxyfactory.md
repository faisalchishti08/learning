---
card: spring-framework
gi: 231
slug: programmatic-proxies-proxyfactory
title: Programmatic proxies (ProxyFactory)
---

## 1. What it is

`ProxyFactory` is Spring AOP's low-level API for building proxies in plain Java — no application context, no annotations, no XML. You instantiate it with a target object, add advisors or interceptors, and call `getProxy()` to receive a proxy that delegates to the target while running the advice chain.

```java
ProxyFactory pf = new ProxyFactory(myService);
pf.addAdvice(new LoggingInterceptor());
MyService proxy = (MyService) pf.getProxy();
```

`ProxyFactoryBean` is the Spring bean-definition equivalent — it exposes `ProxyFactory` configuration as bean properties for use in XML or `@Bean` methods.

## 2. Why & when

Use `ProxyFactory` when:

- Writing **library or framework code** that must not depend on an application context being present.
- **Unit-testing aspects** — create a proxy in a `@Test` method without starting a Spring context.
- **Selective proxying** — you need a proxy for one object, not every bean of that type in a context.
- **Fine-grained control** — force JDK vs CGLIB, add interfaces, freeze the proxy after configuration.

Avoid it in normal application code where `@AspectJ` + `@EnableAspectJAutoProxy` handles everything automatically.

## 3. Core concept

`ProxyFactory` holds:

| Field | What it stores |
|-------|---------------|
| `target` | The real object to delegate to |
| `interfaces` | Interfaces the proxy should implement |
| `advisors` | `List<Advisor>` — each pairs pointcut + advice |
| `proxyTargetClass` | `true` = force CGLIB; `false` = JDK if interface available |
| `frozen` | `true` = lock after first `getProxy()` call |

Calling `getProxy()` triggers `DefaultAopProxyFactory.createAopProxy()` which chooses JDK or CGLIB based on the target class and the `proxyTargetClass` flag, then creates the proxy.

`addAdvice(advice)` wraps the advice in a `DefaultPointcutAdvisor` with `Pointcut.TRUE` (matches all methods). `addAdvisor(advisor)` gives you a specific pointcut.

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
    <marker id="arr2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>

  <!-- ProxyFactory -->
  <rect x="10" y="20" width="200" height="150" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="44" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif" font-weight="bold">ProxyFactory</text>
  <line x1="20" y1="52" x2="200" y2="52" stroke="#8b949e" stroke-width="0.5"/>
  <text x="110" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">target = MyService</text>
  <text x="110" y="86" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">interfaces = [IMyService]</text>
  <text x="110" y="102" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">advisors = [a1, a2]</text>
  <text x="110" y="118" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">proxyTargetClass = false</text>
  <text x="110" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">getProxy()</text>
  <text x="110" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ JDK or CGLIB proxy</text>

  <!-- Arrow to factory -->
  <line x1="212" y1="95" x2="270" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="241" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">creates</text>

  <!-- DefaultAopProxyFactory -->
  <rect x="270" y="60" width="170" height="70" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="355" y="84" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DefaultAopProxyFactory</text>
  <text x="355" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">has interface? → JDK</text>
  <text x="355" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">proxyTargetClass=true → CGLIB</text>

  <!-- Arrow to proxy -->
  <line x1="442" y1="95" x2="500" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Proxy -->
  <rect x="500" y="50" width="165" height="120" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="583" y="72" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Proxy</text>
  <line x1="510" y1="80" x2="655" y2="80" stroke="#8b949e" stroke-width="0.5"/>
  <text x="583" y="97" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">advisor chain: a1 → a2</text>
  <text x="583" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">target delegate</text>
  <text x="583" y="130" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">implements IMyService</text>
  <text x="583" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(Advised) castable</text>
</svg>

`ProxyFactory` decides proxy type, chains advisors, and produces a castable `Advised` proxy.

## 5. Runnable example

Scenario: a **`OrderService`** for placing orders — progressively adding interceptors, interface proxying, and runtime proxy manipulation.

### Level 1 — Basic

Minimal `ProxyFactory` with a single around-advice interceptor, no interface.

```java
// ProxyFactoryDemo.java
import org.springframework.aop.framework.*;
import org.aopalliance.intercept.*;

public class ProxyFactoryDemo {
    public static void main(String[] args) throws Throwable {
        OrderService target = new OrderService();

        ProxyFactory pf = new ProxyFactory(target);
        // addAdvice wraps advice in DefaultPointcutAdvisor(Pointcut.TRUE, advice)
        pf.addAdvice((MethodInterceptor) invocation -> {
            System.out.println("[INTERCEPT] before " + invocation.getMethod().getName());
            Object result = invocation.proceed();
            System.out.println("[INTERCEPT] after  " + invocation.getMethod().getName());
            return result;
        });

        OrderService proxy = (OrderService) pf.getProxy();
        proxy.placeOrder("ORD-001");
    }
}

class OrderService {
    public void placeOrder(String orderId) {
        System.out.println("Order placed: " + orderId);
    }
    public void cancelOrder(String orderId) {
        System.out.println("Order cancelled: " + orderId);
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aopalliance.jar:. ProxyFactoryDemo.java`

`pf.addAdvice(interceptor)` applies the interceptor to every method (`Pointcut.TRUE`). Both `placeOrder` and `cancelOrder` would be intercepted. The proxy type is CGLIB because `OrderService` has no interface.

---

### Level 2 — Intermediate

Add an **interface** so JDK proxying is used, and apply a **pointcut** to intercept only `placeOrder`.

```java
// ProxyFactoryDemo.java
import org.springframework.aop.framework.*;
import org.springframework.aop.support.*;
import org.aopalliance.intercept.*;

public class ProxyFactoryDemo {
    public static void main(String[] args) throws Throwable {
        OrderServiceImpl target = new OrderServiceImpl();

        NameMatchMethodPointcut pc = new NameMatchMethodPointcut();
        pc.setMappedName("placeOrder");         // only placeOrder intercepted

        MethodInterceptor advice = inv -> {
            System.out.println("[AUDIT] placing order: args="
                + java.util.Arrays.toString(inv.getArguments()));
            Object r = inv.proceed();
            System.out.println("[AUDIT] order placed successfully");
            return r;
        };

        ProxyFactory pf = new ProxyFactory(target);
        pf.setInterfaces(IOrderService.class);   // force JDK proxy
        pf.addAdvisor(new DefaultPointcutAdvisor(pc, advice));

        IOrderService proxy = (IOrderService) pf.getProxy();
        proxy.placeOrder("ORD-002");             // intercepted
        proxy.cancelOrder("ORD-002");            // NOT intercepted
    }
}

interface IOrderService {
    void placeOrder(String orderId);
    void cancelOrder(String orderId);
}

class OrderServiceImpl implements IOrderService {
    public void placeOrder(String orderId)  { System.out.println("Order placed: " + orderId); }
    public void cancelOrder(String orderId) { System.out.println("Order cancelled: " + orderId); }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aopalliance.jar:. ProxyFactoryDemo.java`

`pf.setInterfaces(IOrderService.class)` makes `ProxyFactory` emit a JDK dynamic proxy implementing `IOrderService`. The `NameMatchMethodPointcut` restricts interception to `placeOrder` only — `cancelOrder` passes through without advice.

---

### Level 3 — Advanced

**`ProxyFactoryBean`** in a Spring context, plus runtime advisor inspection and adding advice after creation with `freeze(false)`.

```java
// ProxyFactoryDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.springframework.aop.support.*;
import org.aopalliance.intercept.*;

@Configuration
public class ProxyFactoryDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyFactoryDemo.class);
        IOrderService proxy = ctx.getBean("orderProxy", IOrderService.class);

        System.out.println("=== Before call ===");
        printAdvisors(proxy);

        proxy.placeOrder("ORD-003");

        // Dynamically add advice at runtime (proxy must not be frozen)
        Advised advised = (Advised) proxy;
        advised.addAdvice((MethodInterceptor) inv -> {
            System.out.println("[RUNTIME-ADDED] " + inv.getMethod().getName());
            return inv.proceed();
        });

        System.out.println("\n=== After adding runtime advice ===");
        printAdvisors(proxy);
        proxy.placeOrder("ORD-004");

        ctx.close();
    }

    static void printAdvisors(Object proxy) {
        Advised advised = (Advised) proxy;
        for (var a : advised.getAdvisors())
            System.out.println("  Advisor: " + a.getAdvice().getClass().getSimpleName());
    }

    @Bean
    public IOrderService orderProxy() {
        ProxyFactory pf = new ProxyFactory(new OrderServiceImpl());
        pf.setInterfaces(IOrderService.class);
        pf.setFrozen(false);   // allow runtime modification
        pf.addAdvice((MethodInterceptor) inv -> {
            System.out.println("[LOG] " + inv.getMethod().getName());
            return inv.proceed();
        });
        return (IOrderService) pf.getProxy();
    }
}

interface IOrderService {
    void placeOrder(String orderId);
    void cancelOrder(String orderId);
}

class OrderServiceImpl implements IOrderService {
    public void placeOrder(String orderId)  { System.out.println("Order placed: " + orderId); }
    public void cancelOrder(String orderId) { System.out.println("Order cancelled: " + orderId); }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aopalliance.jar:. ProxyFactoryDemo.java`

`setFrozen(false)` leaves the proxy open for modification. After the first call, `advised.addAdvice(...)` injects a new interceptor that runs on subsequent calls. `printAdvisors()` shows the chain growing from one advisor to two. This pattern is useful in test fixtures that need to attach probes mid-test.

## 6. Walkthrough

**Entry point:** `pf.getProxy()` (all levels).

1. `ProxyFactory` calls `DefaultAopProxyFactory.createAopProxy(this)`.
2. Decision: does target implement any non-Spring interface AND `proxyTargetClass==false`? Level 2 → yes → **JDK proxy**. Level 1 → no interface → **CGLIB**.
3. For JDK: creates `java.lang.reflect.Proxy` with the listed interfaces. Every call routes through `JdkDynamicAopProxy.invoke()`.
4. For CGLIB: generates a subclass of `OrderService` at runtime. Every call routes through `CglibAopProxy`'s `MethodInterceptor` (the CGLIB sense — different from AOP Alliance's).
5. On each method call, the proxy builds a `ReflectiveMethodInvocation` and calls `proceed()`.
6. `proceed()` walks the advisor list. For each advisor, evaluates `pointcut.matches(method, targetClass)`. If true → calls `advice.invoke(invocation)`.
7. At the end of the chain, `invocation.proceed()` calls the real target method.

**State trace for Level 2 `placeOrder("ORD-002")`:**

```
caller → JDK proxy.placeOrder("ORD-002")
  → JdkDynamicAopProxy.invoke()
    → ReflectiveMethodInvocation.proceed()
      → DefaultPointcutAdvisor: pointcut matches "placeOrder"? YES
        → MethodInterceptor.invoke()
           prints "[AUDIT] placing order: args=[ORD-002]"
           → invocation.proceed()
             → OrderServiceImpl.placeOrder("ORD-002")
                prints "Order placed: ORD-002"
           ← returns void
           prints "[AUDIT] order placed successfully"
        ← returns void
      ← chain exhausted
    ← returns void
  ← returns void
← caller returns
```

For `cancelOrder("ORD-002")`: pointcut matches `placeOrder` only → chain runs but no advisor matches → target called directly.

## 7. Gotchas & takeaways

> **`pf.setFrozen(true)` (the default after first `getProxy()` call) prevents adding advisors at runtime.** Calling `addAdvice` on a frozen `Advised` proxy throws `AopConfigException`. If you need dynamic advice, set `frozen(false)` explicitly before the first `getProxy()`.

> **`ProxyFactory` does NOT register the proxy as a Spring bean.** If you call `getProxy()` outside a `@Bean` method, the proxy has no bean name and is not subject to lifecycle callbacks (`@PostConstruct`, `DisposableBean`, etc.). Use `ProxyFactoryBean` in a bean context to get lifecycle integration.

- `pf.addAdvice(x)` is shorthand for `pf.addAdvisor(new DefaultPointcutAdvisor(Pointcut.TRUE, x))` — matches every method.
- `pf.setInterfaces(...)` selects JDK proxying even if `proxyTargetClass` is `false` by default — you must declare the interfaces explicitly, or Spring infers them from the target.
- Cast any Spring-managed proxy to `Advised` to inspect or modify it: `((Advised) proxy).getAdvisors()`.
- `ProxyFactoryBean` wraps `ProxyFactory` for use as a `FactoryBean<T>` bean definition — use it in `@Bean` methods for context-managed proxies with full lifecycle.
