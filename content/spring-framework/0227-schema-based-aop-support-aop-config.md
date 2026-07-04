---
card: spring-framework
gi: 227
slug: schema-based-aop-support-aop-config
title: "Schema-based AOP support (<aop:config>)"
---

## 1. What it is

Spring's schema-based AOP lets you configure aspects, pointcuts, and advice in XML rather than Java annotations. The `<aop:config>` namespace element is the root container for this configuration. Inside it you declare `<aop:aspect>`, `<aop:pointcut>`, and advice elements (`<aop:before>`, `<aop:after>`, `<aop:around>`, etc.).

The aspect's actual behaviour is still written in a plain Java class — but the class does NOT need `@Aspect`. The XML wires the methods to their pointcuts.

```xml
<aop:config>
  <aop:aspect ref="loggingBean">
    <aop:before pointcut="execution(* com.example.service.*.*(..))"
                method="logBefore"/>
  </aop:aspect>
</aop:config>
```

## 2. Why & when

Schema-based AOP is the legacy approach pre-dating `@AspectJ` annotations (introduced in Spring 2.0). You encounter it in:
- Legacy enterprise applications that haven't migrated to annotations.
- Teams that prefer keeping all wiring in XML for visibility.
- Environments where modifying Java source code is restricted.

For new code, `@AspectJ`-style annotations are the recommended approach. But understanding XML AOP is necessary to maintain or migrate existing codebases.

## 3. Core concept

Schema-based AOP is functionally identical to `@AspectJ` — it uses the same underlying proxy engine. The difference is purely in how the configuration is expressed:

| Annotation | XML equivalent |
|-----------|----------------|
| `@Aspect` | `<aop:aspect ref="bean">` |
| `@Pointcut` | `<aop:pointcut id="…" expression="…"/>` |
| `@Before("pc()")` | `<aop:before pointcut-ref="pc" method="…"/>` |
| `@After` | `<aop:after …/>` |
| `@AfterReturning` | `<aop:after-returning returning="…" …/>` |
| `@AfterThrowing` | `<aop:after-throwing throwing="…" …/>` |
| `@Around` | `<aop:around …/>` |

The Java class backing an `<aop:aspect>` is a plain bean — no special annotations needed. The XML wires its methods to points in the call chain.

## 4. Diagram

<svg viewBox="0 0 640 205" xmlns="http://www.w3.org/2000/svg">
  <!-- XML config box -->
  <rect x="15" y="20" width="260" height="170" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="145" y="42" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">applicationContext.xml</text>

  <rect x="25" y="50" width="240" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="145" y="69" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">&lt;aop:config&gt;</text>

  <rect x="35" y="88" width="220" height="25" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="145" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">  &lt;aop:pointcut id="svc" …/&gt;</text>

  <rect x="35" y="119" width="220" height="25" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="145" y="135" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">  &lt;aop:aspect ref="logBean"&gt;</text>

  <rect x="45" y="150" width="200" height="25" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="145" y="166" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">    &lt;aop:before method="log"/&gt;</text>

  <!-- Arrow -->
  <line x1="275" y1="110" x2="335" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="305" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wires to</text>

  <!-- Java class box -->
  <rect x="335" y="65" width="270" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="87" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">LoggingBean (plain Java)</text>
  <text x="470" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">// no @Aspect annotation needed</text>
  <rect x="350" y="112" width="240" height="28" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="470" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">public void log(JoinPoint jp) { … }</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
  </defs>
</svg>

XML declares the wiring; Java implements the behaviour. No `@Aspect` annotation needed on the Java class.

## 5. Runnable example

Scenario: a **billing service** configured with XML AOP — first a basic `<aop:before>`, then a shared pointcut + multiple advice, then `<aop:around>` for timing.

### Level 1 — Basic

`<aop:before>` in XML wires a plain method to a pointcut.

```java
// SchemAopDemo.java
import org.springframework.context.support.*;
import org.aspectj.lang.JoinPoint;

public class SchemaAopDemo {
    public static void main(String[] args) {
        var ctx = new ClassPathXmlApplicationContext("schema-aop.xml");
        ctx.getBean("billingService", BillingService.class).charge(99.0);
        ctx.close();
    }
}

class BillingService {
    public void charge(double amount) {
        System.out.println("Charged $" + amount);
    }
}

class LoggingBean {
    // Plain method — no @Aspect, no @Before
    public void logBefore(JoinPoint jp) {
        System.out.println("[LOG] " + jp.getSignature().getName()
            + " args=" + java.util.Arrays.toString(jp.getArgs()));
    }
}
```

`schema-aop.xml` (place on classpath):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xsi:schemaLocation="
         http://www.springframework.org/schema/beans
         https://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/aop
         https://www.springframework.org/schema/aop/spring-aop.xsd">

  <bean id="billingService" class="BillingService"/>
  <bean id="loggingBean"    class="LoggingBean"/>

  <aop:config>
    <aop:aspect ref="loggingBean">
      <aop:before
        pointcut="execution(* BillingService.*(..))"
        method="logBefore"/>
    </aop:aspect>
  </aop:config>

</beans>
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. SchemaAopDemo.java`

`logBefore` fires before `charge(99.0)`. `LoggingBean` has no Spring AOP annotations — it is a plain Java class wired by XML.

---

### Level 2 — Intermediate

Shared `<aop:pointcut>` referenced by multiple advice elements.

```java
// SchemaAopDemo.java
import org.springframework.context.support.*;
import org.aspectj.lang.*;

public class SchemaAopDemo {
    public static void main(String[] args) {
        var ctx = new ClassPathXmlApplicationContext("schema-aop.xml");
        var svc = ctx.getBean("billingService", BillingService.class);
        svc.charge(50.0);
        try { svc.refund(-10.0); } catch (Exception e) {
            System.out.println("Caller: " + e.getMessage());
        }
        ctx.close();
    }
}

class BillingService {
    public void charge(double amount) { System.out.println("Charged $" + amount); }
    public void refund(double amount) {
        if (amount < 0) throw new IllegalArgumentException("Negative refund");
        System.out.println("Refunded $" + amount);
    }
}

class AuditBean {
    public void before(JoinPoint jp) {
        System.out.println("[AUDIT before] " + jp.getSignature().getName());
    }
    public void afterReturn(JoinPoint jp) {
        System.out.println("[AUDIT after-returning] " + jp.getSignature().getName());
    }
    public void afterThrow(JoinPoint jp, Exception ex) {
        System.out.println("[AUDIT after-throwing] " + jp.getSignature().getName()
            + ": " + ex.getMessage());
    }
    public void afterFinally(JoinPoint jp) {
        System.out.println("[AUDIT after/finally] " + jp.getSignature().getName());
    }
}
```

`schema-aop.xml`:
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
         http://www.springframework.org/schema/beans
         https://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/aop
         https://www.springframework.org/schema/aop/spring-aop.xsd">

  <bean id="billingService" class="BillingService"/>
  <bean id="auditBean"      class="AuditBean"/>

  <aop:config>
    <!-- Shared pointcut -->
    <aop:pointcut id="billing" expression="execution(* BillingService.*(..))"/>

    <aop:aspect ref="auditBean">
      <aop:before        pointcut-ref="billing" method="before"/>
      <aop:after-returning pointcut-ref="billing" method="afterReturn"/>
      <aop:after-throwing  pointcut-ref="billing" method="afterThrow" throwing="ex"/>
      <aop:after           pointcut-ref="billing" method="afterFinally"/>
    </aop:aspect>
  </aop:config>
</beans>
```

How to run: same classpath

`pointcut-ref="billing"` references the shared `<aop:pointcut>`. All four advice elements fire at appropriate moments for `charge` and `refund`.

---

### Level 3 — Advanced

`<aop:around>` for per-method timing, plus `<aop:declare-parents>` (XML equivalent of `@DeclareParents`).

```java
// SchemaAopDemo.java
import org.springframework.context.support.*;
import org.aspectj.lang.*;

public class SchemaAopDemo {
    public static void main(String[] args) throws InterruptedException {
        var ctx = new ClassPathXmlApplicationContext("schema-aop.xml");
        var svc = ctx.getBean("billingService", BillingService.class);
        svc.charge(100.0);

        // DeclareParents: BillingService now implements Trackable
        Trackable t = (Trackable) svc;
        System.out.println("Calls tracked: " + t.getCallCount());
        ctx.close();
    }
}

interface Trackable {
    int getCallCount();
    void increment();
}

class DefaultTrackable implements Trackable {
    private int count = 0;
    public int  getCallCount() { return count; }
    public void increment()    { count++; }
}

class BillingService {
    public void charge(double amount) throws InterruptedException {
        Thread.sleep(100);
        System.out.println("Charged $" + amount);
    }
}

class TimingBean {
    public Object time(ProceedingJoinPoint pjp) throws Throwable {
        long t0 = System.currentTimeMillis();
        Object result = pjp.proceed();
        System.out.printf("[TIME] %s = %d ms%n",
            pjp.getSignature().getName(), System.currentTimeMillis() - t0);
        return result;
    }
    public void count(Trackable t) { t.increment(); }
}
```

`schema-aop.xml`:
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
         http://www.springframework.org/schema/beans
         https://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/aop
         https://www.springframework.org/schema/aop/spring-aop.xsd">

  <bean id="billingService" class="BillingService"/>
  <bean id="timingBean"     class="TimingBean"/>

  <aop:config>
    <aop:pointcut id="billing" expression="execution(* BillingService.*(..))"/>

    <aop:aspect ref="timingBean">
      <aop:around pointcut-ref="billing" method="time"/>
      <aop:before pointcut="execution(* BillingService.*(..)) and this(t)"
                  method="count" arg-names="t"/>
      <aop:declare-parents
          types-matching="BillingService+"
          implement-interface="Trackable"
          default-impl="DefaultTrackable"/>
    </aop:aspect>
  </aop:config>
</beans>
```

How to run: same classpath + XML file on classpath

`<aop:around method="time"/>` wraps `charge` for timing. `<aop:declare-parents>` introduces `Trackable`. The `<aop:before>` uses `this(t)` to bind the proxy as `Trackable` and increment the counter.

## 6. Walkthrough

**XML parsing at startup:**
1. `ClassPathXmlApplicationContext` reads `schema-aop.xml`.
2. The `aop:` namespace handler (`AopNamespaceHandler`) parses `<aop:config>`.
3. For each `<aop:aspect>`, it creates `AspectJPointcutAdvisor` instances referencing the named bean's methods.
4. For each `<aop:pointcut>`, it compiles the `execution(…)` expression.
5. These advisors are registered in the context alongside the regular bean definitions.

**Proxy creation for `billingService`:**
- `AnnotationAwareAspectJAutoProxyCreator` sees advisors that match `BillingService`.
- Creates a CGLIB proxy wrapping `BillingService` with all advisors in the chain.
- `<aop:declare-parents>` causes `Trackable` to be added as an additional interface on the proxy.

**`svc.charge(100.0)` execution:**
1. Proxy intercepts `charge`.
2. `TimingBean.time()` (`@Around`) enters, records `t0`.
3. `TimingBean.count()` (`@Before`) fires — `t.increment()` → counter = 1.
4. Real `BillingService.charge(100.0)` runs.
5. `TimingBean.time()` exits, prints elapsed.

**Cast to `Trackable`:**
- `(Trackable) svc` succeeds (proxy implements it via declare-parents).
- `t.getCallCount()` returns 1.

## 7. Gotchas & takeaways

> **XML AOP and `@AspectJ` annotations can coexist.** Both are processed by the same `AnnotationAwareAspectJAutoProxyCreator`. Having both in the same application context is valid but confusing — pick one style per aspect.

> **XML AOP does not require `@EnableAspectJAutoProxy`.** The `<aop:config>` element registers the auto-proxy creator automatically when the XML is loaded.

- XML AOP is verbose compared to annotations — the same pointcut must be typed as a string attribute value and cannot benefit from IDE autocompletion for method signatures.
- The `and`, `or`, `not` keywords in XML AOP replace `&&`, `||`, `!` (XML entity issues) — `expression="execution(* *.*(..)) and @annotation(Logged)"`.
- `<aop:declare-parents>` is the XML equivalent of `@DeclareParents` — same semantics, same proxy mechanism.
- Migration path: add `@Aspect` to the backing Java class and move the `@Pointcut`/`@Before` annotations in, then remove the XML configuration.
