---
card: spring-framework
gi: 229
slug: advisors
title: Advisors
---

## 1. What it is

An **advisor** is a Spring AOP concept that bundles one piece of advice (what to do) with one pointcut (where to apply it) into a single reusable object. The primary interface is `org.springframework.aop.Advisor`, with the most common subtype being `PointcutAdvisor`.

```java
@Bean
public DefaultPointcutAdvisor securityAdvisor() {
    NameMatchMethodPointcut pc = new NameMatchMethodPointcut();
    pc.setMappedNames("charge", "refund");
    return new DefaultPointcutAdvisor(pc, new SecurityInterceptor());
}
```

Advisors surface prominently in the `<aop:advisor>` XML element, Spring's `ProxyFactoryBean`, and programmatic proxy creation.

## 2. Why & when

Advisors appear in three contexts:

1. **XML AOP** — `<aop:advisor>` element is the legacy way to wire a single `Advice` object (often a `TransactionInterceptor` or custom `MethodInterceptor`) to a pointcut without declaring a full aspect class.
2. **Programmatic AOP** — when constructing proxies manually with `ProxyFactory` or `ProxyFactoryBean`, you add `Advisor` instances to the proxy rather than adding raw `Advice`.
3. **Framework internals** — Spring's `@Transactional`, `@Cacheable`, and `@Async` are all implemented internally as `Advisor` beans. Understanding advisors lets you inspect, order, and debug them.

## 3. Core concept

The `Advisor` interface has one method: `getAdvice()`. The `PointcutAdvisor` subinterface adds `getPointcut()`. Together they answer: "where should this advice run?"

Key types:

| Type | Purpose |
|------|---------|
| `DefaultPointcutAdvisor` | Wraps any `Pointcut` + any `Advice` |
| `NameMatchMethodPointcutAdvisor` | Matches by method name pattern |
| `RegexpMethodPointcutAdvisor` | Matches by regular expression |
| `StaticMethodMatcherPointcutAdvisor` | Abstract base for compile-time static matching |
| `AspectJExpressionPointcutAdvisor` | Wraps an AspectJ expression string |

`@AspectJ`-style `@Aspect` classes internally produce `AspectJPointcutAdvisor` instances — one per advice method. You can see them all via `((Advised) proxy).getAdvisors()`.

## 4. Diagram

<svg viewBox="0 0 640 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Advisor box -->
  <rect x="15" y="20" width="220" height="150" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="125" y="42" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Advisor</text>
  <line x1="25" y1="50" x2="225" y2="50" stroke="#8b949e" stroke-width="0.5"/>

  <rect x="30" y="60" width="190" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="125" y="78" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Pointcut</text>
  <text x="125" y="93" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">where to apply</text>

  <rect x="30" y="110" width="190" height="40" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="125" y="128" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Advice</text>
  <text x="125" y="143" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">what to do</text>

  <!-- Arrow to Proxy -->
  <line x1="237" y1="95" x2="295" y2="95" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="266" y="88" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">added to</text>

  <!-- Proxy box -->
  <rect x="295" y="50" width="160" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="375" y="72" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Proxy</text>
  <text x="375" y="91" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Advisor chain</text>
  <text x="375" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">[Advisor1]</text>
  <text x="375" y="121" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">[Advisor2]</text>

  <!-- Arrow to Target -->
  <line x1="457" y1="95" x2="510" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>

  <!-- Target box -->
  <rect x="510" y="65" width="115" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="568" y="90" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Target bean</text>
  <text x="568" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">real method</text>

  <defs>
    <marker id="a"  markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#79c0ff"/></marker>
  </defs>
</svg>

An advisor bundles pointcut + advice. Multiple advisors are held in a chain inside the proxy, evaluated in order for each method call.

## 5. Runnable example

Scenario: a **payment service** — first using `DefaultPointcutAdvisor` programmatically, then `<aop:advisor>` in XML, then inspecting the advisor chain at runtime.

### Level 1 — Basic

`ProxyFactory` + `DefaultPointcutAdvisor` — no `@Aspect`, no XML.

```java
// AdvisorDemo.java
import org.springframework.aop.framework.*;
import org.springframework.aop.support.*;
import org.aopalliance.intercept.*;

public class AdvisorDemo {
    public static void main(String[] args) throws Throwable {
        // Target
        PaymentService target = new PaymentService();

        // Pointcut — match all methods named "charge"
        NameMatchMethodPointcut pc = new NameMatchMethodPointcut();
        pc.setMappedName("charge");

        // Advice — MethodInterceptor (= around advice)
        MethodInterceptor advice = invocation -> {
            System.out.println("[ADVISOR] before " + invocation.getMethod().getName());
            Object r = invocation.proceed();
            System.out.println("[ADVISOR] after  " + invocation.getMethod().getName());
            return r;
        };

        // Advisor = pointcut + advice
        DefaultPointcutAdvisor advisor = new DefaultPointcutAdvisor(pc, advice);

        // Build proxy
        ProxyFactory pf = new ProxyFactory(target);
        pf.addAdvisor(advisor);
        PaymentService proxy = (PaymentService) pf.getProxy();

        proxy.charge(100.0);  // [ADVISOR] fires
        proxy.refund(50.0);   // no advice — "refund" not in pointcut
    }
}

class PaymentService {
    public void charge(double amount) { System.out.println("Charged $" + amount); }
    public void refund(double amount) { System.out.println("Refunded $" + amount); }
}
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aopalliance.jar:. AdvisorDemo.java`

`NameMatchMethodPointcut` restricts the advice to `charge` only. `refund` is called but no advisor intercepts it.

---

### Level 2 — Intermediate

`<aop:advisor>` in XML — wire a standalone `Advice` bean to a pointcut without a full aspect class.

```java
// AdvisorDemo.java
import org.springframework.context.support.*;
import org.aopalliance.intercept.*;
import org.springframework.stereotype.*;

public class AdvisorDemo {
    public static void main(String[] args) throws Throwable {
        var ctx = new ClassPathXmlApplicationContext("advisor.xml");
        PaymentService svc = ctx.getBean("paymentService", PaymentService.class);
        svc.charge(200.0);
        svc.refund(75.0);
        ctx.close();
    }
}

class PaymentService {
    public void charge(double amount) { System.out.println("Charged $" + amount); }
    public void refund(double amount) { System.out.println("Refunded $" + amount); }
}

// Plain MethodInterceptor — implements Advice without @Aspect
class AuditInterceptor implements MethodInterceptor {
    public Object invoke(MethodInvocation inv) throws Throwable {
        System.out.println("[AUDIT] " + inv.getMethod().getName()
            + " args=" + java.util.Arrays.toString(inv.getArguments()));
        Object r = inv.proceed();
        System.out.println("[AUDIT] done");
        return r;
    }
}
```

`advisor.xml`:
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

  <bean id="paymentService"  class="PaymentService"/>
  <bean id="auditInterceptor" class="AuditInterceptor"/>

  <aop:config>
    <aop:pointcut id="paymentOps" expression="execution(* PaymentService.*(..))"/>
    <!-- aop:advisor wires a raw Advice bean to a pointcut — no aspect class needed -->
    <aop:advisor advice-ref="auditInterceptor" pointcut-ref="paymentOps"/>
  </aop:config>
</beans>
```

How to run: same classpath + XML on classpath

`<aop:advisor>` is simpler than `<aop:aspect>` when you already have a `MethodInterceptor` bean. No Java class needs `@Aspect`.

---

### Level 3 — Advanced

Inspect the advisor chain at runtime via `((Advised) proxy).getAdvisors()` and understand how Spring's own `@Transactional` advisor appears there.

```java
// AdvisorDemo.java
import org.springframework.context.annotation.*;
import org.springframework.aop.framework.*;
import org.springframework.aop.support.*;
import org.springframework.transaction.annotation.*;
import org.springframework.stereotype.*;
import org.aopalliance.intercept.*;

@Configuration
@EnableAspectJAutoProxy
@EnableTransactionManagement
@ComponentScan
public class AdvisorDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvisorDemo.class);
        PaymentService proxy = ctx.getBean(PaymentService.class);

        // Print all advisors on the proxy
        Advised advised = (Advised) proxy;
        System.out.println("=== Advisors on PaymentService proxy ===");
        for (var advisor : advised.getAdvisors()) {
            System.out.println("  " + advisor.getClass().getSimpleName()
                + " → " + advisor.getAdvice().getClass().getSimpleName());
        }

        proxy.charge(300.0);
        ctx.close();
    }

    @Bean
    public org.springframework.transaction.PlatformTransactionManager transactionManager(
            javax.sql.DataSource ds) {
        return new org.springframework.jdbc.datasource.DataSourceTransactionManager(ds);
    }

    @Bean
    public javax.sql.DataSource dataSource() {
        return new org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseBuilder()
            .setType(org.springframework.jdbc.datasource.embedded.EmbeddedDatabaseType.H2)
            .build();
    }
}

@Service
class PaymentService {
    @Transactional
    public void charge(double amount) { System.out.println("Charged $" + amount); }
}

@org.aspectj.lang.annotation.Aspect
@Component
class TimingAspect {
    @org.aspectj.lang.annotation.Around("execution(* PaymentService.*(..))")
    public Object time(org.aspectj.lang.ProceedingJoinPoint pjp) throws Throwable {
        System.out.println("[TIMING] enter");
        Object r = pjp.proceed();
        System.out.println("[TIMING] exit");
        return r;
    }
}
```

How to run: `java -cp spring-context.jar:spring-tx.jar:spring-jdbc.jar:h2.jar:spring-aop.jar:aspectjweaver.jar:. AdvisorDemo.java`

`((Advised) proxy).getAdvisors()` shows both the `AspectJPointcutAdvisor` (from `TimingAspect`) and the `BeanFactoryTransactionAttributeSourceAdvisor` (from `@Transactional`). This is how you debug unexpected advice or ordering issues in production.

## 6. Walkthrough

**`ProxyFactory` mechanics (Level 1):**
1. `new ProxyFactory(target)` creates a factory targeting `PaymentService`.
2. `pf.addAdvisor(advisor)` registers the `DefaultPointcutAdvisor`.
3. `pf.getProxy()` — Spring decides between JDK proxy (if interfaces) and CGLIB (concrete class). `PaymentService` has no interface → CGLIB.
4. For every method call on the proxy, Spring evaluates each advisor's pointcut against the method. `NameMatchMethodPointcut("charge")` matches `charge`, not `refund`.
5. For matching advisors, the advice chain fires.

**`<aop:advisor>` mechanics (Level 2):**
- `<aop:advisor advice-ref="auditInterceptor" pointcut-ref="paymentOps"/>` creates an `AspectJExpressionPointcutAdvisor` whose `getAdvice()` returns the `auditInterceptor` bean.
- Identical to what `@Aspect` produces internally — just configured via XML.

**Advisor chain inspection (Level 3):**
- `((Advised) proxy).getAdvisors()` returns a defensive copy of the advisor list.
- Each `AspectJPointcutAdvisor` wraps one advice method from one `@Aspect` class.
- `BeanFactoryTransactionAttributeSourceAdvisor` is Spring's built-in advisor for `@Transactional`.
- Advisor ordering: `@Order(n)` on `@Aspect` classes → lower = earlier in the list.

## 7. Gotchas & takeaways

> **`<aop:advisor>` and `<aop:aspect>` are not the same.** `<aop:advisor>` wires a raw `Advice` bean (any `MethodInterceptor`, `MethodBeforeAdvice`, etc.) directly. `<aop:aspect>` wraps a POJO and converts its methods into advice. Use `<aop:advisor>` when you already have a ready `MethodInterceptor`; use `<aop:aspect>` when your logic lives in plain methods.

> **Programmatic proxy inspection is the best debugging tool.** When an aspect is not firing or fires in the wrong order, cast the proxy to `Advised` and print `getAdvisors()`. This shows exactly which advisors are active and in what order.

- `DefaultPointcutAdvisor` defaults to `Pointcut.TRUE` when no pointcut is provided — matches every method. Always supply a specific pointcut.
- `NameMatchMethodPointcut` matches by simple method name (no signature). For overloaded methods, use `AspectJExpressionPointcutAdvisor` with an `execution` pattern.
- Spring's own `@Transactional`, `@Cacheable`, `@Async`, and `@Retryable` (from Spring Retry) are all advisors. They appear in the advisor chain alongside your custom advisors.
- `RegexpMethodPointcutAdvisor` accepts a Java regex applied to the fully qualified method name (`com.example.service.OrderService.charge`). Useful for legacy codebases where you cannot add `@annotation` markers.
