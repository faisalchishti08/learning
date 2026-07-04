---
card: spring-framework
gi: 230
slug: choosing-aop-declaration-style
title: Choosing AOP declaration style
---

## 1. What it is

Spring AOP offers three declaration styles: **`@AspectJ` annotations** on regular classes, **XML `<aop:config>` schema**, and **programmatic `ProxyFactory`/`ProxyFactoryBean`** wiring. All three produce the same runtime proxies; only the configuration surface differs.

```java
// @AspectJ style
@Aspect @Component
public class LogAspect {
    @Before("execution(* com.example.*.*(..))")
    public void log(JoinPoint jp) { System.out.println("Calling " + jp.getSignature()); }
}
```

Choosing the right style affects testability, IDE support, team familiarity, and how easily aspects can be packaged in shared libraries.

## 2. Why & when

| Style | Choose when |
|-------|-------------|
| `@AspectJ` | Greenfield Spring Boot apps; team knows annotations; tooling (IntelliJ, AspectJ IDEA plugin) highlights pointcuts inline |
| XML `<aop:config>` | All-XML config legacy apps; non-Java team members must read/maintain the crosscutting rules |
| Programmatic (`ProxyFactory`) | Library code that must not force `@EnableAspectJAutoProxy`; unit testing aspects in isolation; fine-grained proxy construction |

Mixing styles is legal — Spring processes all three. Avoid it unless you have a clear reason (e.g., migrating from XML to annotations incrementally).

## 3. Core concept

Spring's AOP infrastructure resolves all three styles to the same internal model:

1. **`AspectJPointcutAdvisor`** objects (one per advice method / XML `<aop:advice>` element / programmatic `addAdvisor` call).
2. A **proxy** (JDK dynamic proxy or CGLIB subclass) that intercepts calls and walks the advisor chain.

`@AspectJ` requires `@EnableAspectJAutoProxy` (or `<aop:aspectj-autoproxy/>`), which registers `AnnotationAwareAspectJAutoProxyCreator` — a `BeanPostProcessor` that scans every bean for `@Aspect` and builds advisors automatically.

XML `<aop:config>` registers the same `BeanPostProcessor` implicitly.

Programmatic `ProxyFactory` bypasses the container entirely; you build the proxy manually in code.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- @AspectJ -->
  <rect x="10" y="20" width="180" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="44" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@AspectJ annotations</text>
  <text x="100" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Aspect @Before @Around …</text>
  <text x="100" y="75" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@EnableAspectJAutoProxy</text>

  <!-- XML -->
  <rect x="10" y="100" width="180" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="124" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">XML &lt;aop:config&gt;</text>
  <text x="100" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;aop:aspect&gt; &lt;aop:before&gt; …</text>
  <text x="100" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;aop:aspectj-autoproxy/&gt;</text>

  <!-- Programmatic -->
  <rect x="260" y="60" width="180" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="84" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Programmatic</text>
  <text x="350" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ProxyFactory / ProxyFactoryBean</text>
  <text x="350" y="115" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">addAdvisor(…) / getProxy()</text>

  <!-- Arrows to shared internal model -->
  <line x1="192" y1="50" x2="440" y2="88" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr)"/>
  <line x1="192" y1="130" x2="440" y2="100" stroke="#6db33f" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#arr)"/>
  <line x1="442" y1="90" x2="500" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Shared model -->
  <rect x="500" y="55" width="185" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="593" y="80" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">AspectJPointcutAdvisor[]</text>
  <text x="593" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">↓</text>
  <text x="593" y="113" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">JDK / CGLIB proxy</text>
  <text x="593" y="128" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same runtime behaviour</text>
</svg>

All three styles converge on the same advisor-chain + proxy model at runtime.

## 5. Runnable example

Scenario: a **`GreetingService`** that logs entry — wired first with `@AspectJ`, then XML, then `ProxyFactory` directly.

### Level 1 — Basic

`@AspectJ` on a `@Component` aspect — the most common Spring Boot approach.

```java
// ChooseStyleDemo.java
import org.springframework.context.annotation.*;
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;
import org.springframework.stereotype.*;

@Configuration
@EnableAspectJAutoProxy
@ComponentScan
public class ChooseStyleDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ChooseStyleDemo.class);
        ctx.getBean(GreetingService.class).greet("Alice");
        ctx.close();
    }
}

@Component
class GreetingService {
    public String greet(String name) {
        System.out.println("Hello, " + name + "!");
        return "Hello, " + name + "!";
    }
}

@Aspect
@Component
class EntryLogger {
    @Before("execution(* GreetingService.greet(..))")
    public void before(JoinPoint jp) {
        System.out.println("[LOG] entering " + jp.getSignature().toShortString()
            + " args=" + java.util.Arrays.toString(jp.getArgs()));
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. ChooseStyleDemo.java`

`@EnableAspectJAutoProxy` activates the `BeanPostProcessor` that detects `EntryLogger` (annotated `@Aspect`), extracts its `@Before` method, and wraps `GreetingService` in a CGLIB proxy. Output: `[LOG] entering greet(String) args=[Alice]` → `Hello, Alice!`.

---

### Level 2 — Intermediate

Same logging in **XML `<aop:config>`** — no `@Aspect` annotation on the advice class.

```java
// ChooseStyleDemo.java
import org.springframework.context.support.*;

public class ChooseStyleDemo {
    public static void main(String[] args) {
        var ctx = new ClassPathXmlApplicationContext("choose-style.xml");
        GreetingService svc = ctx.getBean("greetingService", GreetingService.class);
        svc.greet("Bob");
        ctx.close();
    }
}

class GreetingService {
    public String greet(String name) {
        System.out.println("Hello, " + name + "!");
        return "Hello, " + name + "!";
    }
}

class EntryLogger {                          // plain POJO — no @Aspect needed
    public void before(org.aspectj.lang.JoinPoint jp) {
        System.out.println("[LOG-XML] entering " + jp.getSignature().toShortString());
    }
}
```

`choose-style.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
         http://www.springframework.org/schema/beans
         https://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/aop
         https://www.springframework.org/schema/aop/spring-aop.xsd">

  <bean id="greetingService" class="GreetingService"/>
  <bean id="entryLogger"     class="EntryLogger"/>

  <aop:config>
    <aop:aspect id="logAspect" ref="entryLogger">
      <aop:before method="before"
                  pointcut="execution(* GreetingService.greet(..))"/>
    </aop:aspect>
  </aop:config>
</beans>
```

How to run: same classpath + XML on classpath

`EntryLogger` is a plain bean with no Spring AOP annotations. The XML wires `before()` as before-advice explicitly. This is the legacy approach but useful when the POJO must remain framework-agnostic.

---

### Level 3 — Advanced

**Programmatic `ProxyFactory`** — no container, no XML, no annotations — direct advisor construction. Adds ordering demonstration.

```java
// ChooseStyleDemo.java
import org.springframework.aop.framework.*;
import org.springframework.aop.support.*;
import org.springframework.aop.*;
import org.aopalliance.intercept.*;

public class ChooseStyleDemo {
    public static void main(String[] args) {
        GreetingService target = new GreetingService();

        // Advisor 1 — entry log (order = first)
        NameMatchMethodPointcut pc1 = new NameMatchMethodPointcut();
        pc1.setMappedName("greet");
        MethodInterceptor log = inv -> {
            System.out.println("[LOG-PROG] entering " + inv.getMethod().getName()
                + " args=" + java.util.Arrays.toString(inv.getArguments()));
            return inv.proceed();
        };
        DefaultPointcutAdvisor a1 = new DefaultPointcutAdvisor(pc1, log);

        // Advisor 2 — timing (order = second)
        NameMatchMethodPointcut pc2 = new NameMatchMethodPointcut();
        pc2.setMappedName("greet");
        MethodInterceptor timer = inv -> {
            long t = System.nanoTime();
            Object r = inv.proceed();
            System.out.printf("[TIMER] greet took %d µs%n", (System.nanoTime() - t) / 1_000);
            return r;
        };
        DefaultPointcutAdvisor a2 = new DefaultPointcutAdvisor(pc2, timer);

        ProxyFactory pf = new ProxyFactory(target);
        pf.addAdvisor(a1);   // a1 is outer (runs first)
        pf.addAdvisor(a2);   // a2 is inner (runs second)
        GreetingService proxy = (GreetingService) pf.getProxy();

        proxy.greet("Carol");

        // Inspect what was built
        System.out.println("\n--- Advisor chain ---");
        for (var adv : ((Advised) proxy).getAdvisors())
            System.out.println("  " + adv.getAdvice().getClass().getSimpleName());
    }
}

class GreetingService {
    public String greet(String name) {
        System.out.println("Hello, " + name + "!");
        return "Hello, " + name + "!";
    }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aopalliance.jar:. ChooseStyleDemo.java`

Two advisors stacked: `a1` wraps `a2` wraps the real method. The interceptor chain runs outermost-first. `((Advised) proxy).getAdvisors()` at the end prints them in order, confirming the chain structure.

## 6. Walkthrough

**Execution flow for `proxy.greet("Alice")` with `@AspectJ` (Level 1):**

1. `AnnotationConfigApplicationContext` starts. `@ComponentScan` finds `GreetingService` and `EntryLogger`.
2. `AnnotationAwareAspectJAutoProxyCreator` (registered by `@EnableAspectJAutoProxy`) runs as a `BeanPostProcessor` after every bean is created.
3. It finds `EntryLogger` bears `@Aspect`. It reads `@Before("execution(* GreetingService.greet(..))")` and creates an `AspectJPointcutAdvisor`.
4. When `GreetingService` bean is created, the post-processor checks: any advisor matches? Yes → wraps the bean in a **CGLIB proxy**.
5. `ctx.getBean(GreetingService.class)` returns the proxy, not the original.
6. `proxy.greet("Alice")` enters the CGLIB proxy's `intercept()` method.
7. The proxy walks the advisor chain. `AspectJExpressionPointcut.matches(Method, Class)` returns `true` for `greet`.
8. The before-advice runs: prints `[LOG] entering greet(String) args=[Alice]`.
9. The real `GreetingService.greet("Alice")` executes: prints `Hello, Alice!`.
10. Return value `"Hello, Alice!"` propagates back to the caller.

**State changes at each stage:**

```
Caller → proxy.greet("Alice")
  → CGLIB intercept()
    → AdvisorChain.invoke()
      → EntryLogger.before()     [prints log line]
      → GreetingService.greet()  [prints "Hello, Alice!", returns String]
  ← return "Hello, Alice!"
← caller receives String
```

For Level 3, the two-advisor chain nests:

```
proxy.greet()
  → a1 interceptor (LOG)
    → a2 interceptor (TIMER)
      → GreetingService.greet()  ← real call
    ← TIMER prints µs
  ← LOG returns result
```

## 7. Gotchas & takeaways

> **`@AspectJ` requires `aspectjweaver.jar` on the classpath even though Spring does not use AspectJ byte-code weaving.** Spring uses AspectJ's pointcut parser only. Forgetting the JAR causes a `NoClassDefFoundError` at startup.

> **XML `<aop:config>` and `@EnableAspectJAutoProxy` both register the same `BeanPostProcessor`.** Declaring both in one context is harmless but redundant — Spring deduplicates.

- `@AspectJ` is the recommended style for modern Spring; IDE tooling highlights matched join points inline.
- XML `<aop:config>` keeps aspects separate from Java code — good for non-developer-maintained crosscutting rules (e.g., security policies in a config file).
- Programmatic `ProxyFactory` is the right choice for library code or unit tests where you need a proxy without an application context.
- All three styles coexist. Mixing is fine when migrating; avoid long-term mixing for clarity.
- Introspect any proxy with `((Advised) proxy).getAdvisors()` regardless of which style created it.
