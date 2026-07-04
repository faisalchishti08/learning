---
card: spring-framework
gi: 210
slug: aop-proxies-jdk-dynamic-vs-cglib
title: AOP proxies (JDK dynamic vs CGLIB)
---

## 1. What it is

Spring AOP creates proxies to intercept method calls. It has two proxy strategies:

- **JDK dynamic proxy** — Java's built-in proxy mechanism (`java.lang.reflect.Proxy`). Works only when the target bean implements at least one interface. The proxy implements the same interface(s).
- **CGLIB proxy** — Code Generation Library. Creates a runtime-generated *subclass* of the target class. Works even when the target has no interface.

Spring Boot 2.0+ defaults to CGLIB for all Spring-managed beans. You can override per configuration.

## 2. Why & when

Choosing the wrong proxy type causes subtle runtime errors:

- JDK proxy → casting to the implementing class (not the interface) throws `ClassCastException`.
- CGLIB proxy → `final` methods or `final` classes cannot be subclassed → those methods silently bypass the proxy.

Understand the trade-offs:
| | JDK Dynamic | CGLIB |
|---|---|---|
| Requires interface | Yes | No |
| Proxies `final` methods | No | No (subclass cannot override final) |
| Startup cost | Slightly faster | Slightly slower (byte generation) |
| Default since Spring Boot 2 | No | **Yes** |

Use JDK proxy when your beans implement interfaces and you want to type beans as the interface everywhere. Use CGLIB (the default) when your beans are concrete classes without interfaces.

## 3. Core concept

JDK proxy uses Java's built-in `InvocationHandler`. Every method call on the proxy interface goes to `InvocationHandler.invoke(proxy, method, args)`, which runs the advice chain and then calls the real method via reflection.

CGLIB generates a subclass at runtime. The subclass overrides every non-final, non-private method with an interceptor that runs the advice chain. The subclass delegates to the parent (`super.method(args)`) for the actual work.

Analogy: JDK proxy is like a receptionist who receives calls via a shared phone number (interface) and forwards them. CGLIB is like a stand-in actor who looks exactly like the original (subclass) and can perform all the same scenes — except those marked "only the original can do this" (final methods).

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- JDK proxy path -->
  <rect x="15" y="20" width="290" height="170" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="43" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">JDK Dynamic Proxy</text>
  <text x="160" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Target must implement interface</text>

  <rect x="30"  y="70" width="80" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="70"  y="91" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MyService</text>
  <text x="70"  y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements</text>

  <rect x="125" y="70" width="80" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="165" y="93" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">IMyService</text>

  <rect x="220" y="70" width="75" height="35" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="258" y="88" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Proxy</text>
  <text x="258" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">impl IMyService</text>

  <line x1="110" y1="87" x2="125" y2="87" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="220" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Proxy.invoke() → advice chain</text>
  <text x="220" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ target.method() via reflection</text>

  <!-- CGLIB proxy path -->
  <rect x="335" y="20" width="290" height="170" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="43" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif" font-weight="bold">CGLIB Proxy (default)</text>
  <text x="480" y="60" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Subclasses target class directly</text>

  <rect x="350" y="70" width="85" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="393" y="91" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MyService</text>
  <text x="393" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(original)</text>

  <rect x="460" y="70" width="115" height="35" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="518" y="88" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">MyService$$CGLIB</text>
  <text x="518" y="100" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">extends MyService</text>

  <line x1="435" y1="87" x2="460" y2="87" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a2)"/>
  <text x="480" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">override all non-final methods</text>
  <text x="480" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ advice chain → super.method()</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

JDK proxy implements the interface; CGLIB subclasses the class. Both intercept method calls — their differences lie in what constraints they impose.

## 5. Runnable example

Scenario: a **notification sender** — first seeing the default CGLIB proxy, then switching to JDK proxy via an interface, then demonstrating the `final` method limitation.

### Level 1 — Basic

Default Spring Boot behaviour: CGLIB proxy for a concrete class.

```java
// ProxyTypeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy   // proxyTargetClass defaults to true in Spring Boot → CGLIB
@ComponentScan
public class ProxyTypeDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyTypeDemo.class);
        NotificationSender sender = ctx.getBean(NotificationSender.class);

        System.out.println("Proxy class: " + sender.getClass().getName());
        System.out.println("Is CGLIB:    " + AopUtils.isCglibProxy(sender));
        System.out.println("Is JDK:      " + AopUtils.isJdkDynamicProxy(sender));

        sender.send("Hello");
        ctx.close();
    }
}

@Service
class NotificationSender {
    public void send(String message) {
        System.out.println("Sending: " + message);
    }
}

@Aspect
@Component
class LogAspect {
    @Before("execution(* NotificationSender.*(..))")
    public void log(org.aspectj.lang.JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().getName());
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. ProxyTypeDemo.java`

Prints `Is CGLIB: true` — the default. The proxy class name contains `$$SpringCGLIB$$`.

---

### Level 2 — Intermediate

Switch to JDK dynamic proxy by adding an interface and setting `proxyTargetClass = false`.

```java
// ProxyTypeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

interface Sender {
    void send(String message);
}

@Configuration
@EnableAspectJAutoProxy(proxyTargetClass = false)  // force JDK proxy
@ComponentScan
public class ProxyTypeDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyTypeDemo.class);
        Sender sender = ctx.getBean(Sender.class); // must use interface type

        System.out.println("Proxy class: " + sender.getClass().getName());
        System.out.println("Is JDK:      " + AopUtils.isJdkDynamicProxy(sender));

        sender.send("Hello via JDK proxy");

        // Attempting to cast to the implementing class throws ClassCastException
        try {
            NotificationSender raw = (NotificationSender) sender;
        } catch (ClassCastException e) {
            System.out.println("Expected: " + e.getMessage());
        }
        ctx.close();
    }
}

@Service
class NotificationSender implements Sender {
    public void send(String message) {
        System.out.println("Sending: " + message);
    }
}

@Aspect
@Component
class LogAspect {
    @Before("execution(* Sender.*(..))")
    public void log(JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

`proxyTargetClass = false` tells Spring to use JDK dynamic proxy. `ctx.getBean(Sender.class)` works (interface type). Casting to `NotificationSender` throws `ClassCastException` — the proxy only implements `Sender`, not the class.

---

### Level 3 — Advanced

Show CGLIB limitation: `final` methods are not intercepted, and a `final` class cannot be proxied at all.

```java
// ProxyTypeDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import org.springframework.aop.framework.*;
import org.aspectj.lang.*;
import org.aspectj.lang.annotation.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class ProxyTypeDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProxyTypeDemo.class);
        NotificationSender sender = ctx.getBean(NotificationSender.class);

        System.out.println("--- non-final method (intercepted) ---");
        sender.send("Hello");           // @Before fires

        System.out.println("--- final method (NOT intercepted) ---");
        sender.sendFinal("Hello");      // @Before does NOT fire — CGLIB cannot override final
        ctx.close();
    }
}

@Service
class NotificationSender {
    public void send(String message) {
        System.out.println("Sending: " + message);
    }

    public final void sendFinal(String message) {
        System.out.println("Final send: " + message);
    }
}

@Aspect
@Component
class LogAspect {
    @Before("execution(* NotificationSender.*(..))")
    public void log(JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().getName());
    }
}
```

How to run: same classpath

`send("Hello")` prints `[LOG]` first. `sendFinal("Hello")` does NOT print `[LOG]` — CGLIB generated a subclass that could not override `final void sendFinal()`, so calls to it pass straight to the target without going through the advice chain. No error, no warning — silent bypass.

## 6. Walkthrough

**JDK proxy creation path (Level 2):**
1. `AnnotationAwareAspectJAutoProxyCreator` detects `proxyTargetClass = false`.
2. It checks that `NotificationSender` implements at least one interface (`Sender`).
3. Calls `java.lang.reflect.Proxy.newProxyInstance(classLoader, new Class[]{Sender.class}, invocationHandler)`.
4. The returned proxy object is a class like `com.sun.proxy.$Proxy12` implementing `Sender`.
5. `invocationHandler.invoke(proxy, method, args)` receives every call, runs the advice chain, then calls `method.invoke(target, args)` on the real `NotificationSender`.

**CGLIB proxy creation path (Level 1):**
1. `AnnotationAwareAspectJAutoProxyCreator` uses CGLIB (default).
2. CGLIB's `Enhancer.create()` generates a subclass like `NotificationSender$$SpringCGLIB$$0`.
3. Each public non-final method in the subclass contains: run interceptors → if no interceptor skips, call `super.send(args)`.
4. The context registers the CGLIB instance under bean name `"notificationSender"`.

**`final` method bypass (Level 3):**
CGLIB generates bytecode for the subclass. Java's language rules forbid overriding `final` methods. The CGLIB-generated subclass simply inherits `sendFinal()` from the parent *without* any interceptor wrapper. When the proxy's `sendFinal()` is called, it executes the inherited parent method directly — the advice chain is never entered.

**State: bean type after proxying:**
```
Without advice: ctx.getBean(NotificationSender.class).getClass() == NotificationSender.class
With CGLIB AOP: ctx.getBean(NotificationSender.class).getClass() == NotificationSender$$SpringCGLIB$$0.class
With JDK AOP:   ctx.getBean(Sender.class).getClass()             == $Proxy12.class
```

## 7. Gotchas & takeaways

> **Never cast a JDK-proxied bean to its implementing class.** If you ask Spring for `ctx.getBean(NotificationSender.class)` and it gave you a JDK proxy, the cast fails with `ClassCastException`. Always type the variable as the interface.

> **`@Autowired NotificationSender sender` fails with JDK proxy** if Spring detects the bean is a proxy implementing `Sender` but you declared the field as `NotificationSender`. Switch to `@Autowired Sender sender` or use CGLIB (the default).

- Spring Boot's default is `proxyTargetClass = true` (CGLIB) — this is why Spring Boot apps work without interfaces on service classes.
- Both proxy types silently skip `private` methods — no error, no interception.
- `AopUtils.isAopProxy(bean)`, `AopUtils.isCglibProxy(bean)`, `AopUtils.isJdkDynamicProxy(bean)` are your diagnostic tools in tests.
- To get the underlying target from a proxy: `AopProxyUtils.ultimateTargetClass(proxy)` or `((Advised) proxy).getTargetSource().getTarget()`.
- If you need a Spring bean to also be castable to its class type (not just interface), use CGLIB (the default). If you need strict interface-only typing, use JDK proxy.
