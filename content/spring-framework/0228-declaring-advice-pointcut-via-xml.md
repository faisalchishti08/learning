---
card: spring-framework
gi: 228
slug: declaring-advice-pointcut-via-xml
title: Declaring advice/pointcut via XML
---

## 1. What it is

Within `<aop:config>` you can declare named reusable pointcuts with `<aop:pointcut>` and attach advice to them with `<aop:before>`, `<aop:after>`, `<aop:after-returning>`, `<aop:after-throwing>`, and `<aop:around>`. Each element lives inside `<aop:aspect ref="beanId">` and maps to a method on the backing bean.

```xml
<aop:config>
  <aop:pointcut id="serviceOps"
    expression="execution(* com.example.service.*.*(..))"/>

  <aop:aspect ref="auditBean">
    <aop:before pointcut-ref="serviceOps" method="logCall"/>
    <aop:after-returning pointcut-ref="serviceOps" method="cacheResult" returning="retVal"/>
    <aop:around pointcut-ref="serviceOps" method="time"/>
  </aop:aspect>
</aop:config>
```

## 2. Why & when

Use XML advice/pointcut declarations when:
- Working in an existing XML-configured codebase.
- The cross-cutting concern is a configuration choice (not a logic choice) — e.g., "log all service calls in prod but not dev" by including/excluding the XML file.
- Your team has restricted annotation use and prefers externalised wiring.

XML is more verbose than `@AspectJ` but makes the cross-cutting configuration visible in one place without scanning source code.

## 3. Core concept

Each XML advice element maps to one backing method:

| XML element | Backing method signature |
|-------------|--------------------------|
| `<aop:before>` | `void method(JoinPoint jp)` or `void method(type arg)` when using `arg-names` |
| `<aop:after>` | `void method(JoinPoint jp)` |
| `<aop:after-returning>` | `void method(JoinPoint jp, ReturnType retVal)` when `returning="retVal"` |
| `<aop:after-throwing>` | `void method(JoinPoint jp, ExceptionType ex)` when `throwing="ex"` |
| `<aop:around>` | `Object method(ProceedingJoinPoint pjp) throws Throwable` |

`<aop:pointcut>` elements placed directly inside `<aop:config>` are global — any aspect in that config can reference them via `pointcut-ref`. Pointcuts placed inside `<aop:aspect>` are local to that aspect.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg">
  <!-- aop:config outer box -->
  <rect x="10" y="10" width="440" height="185" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="220" y="32" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">&lt;aop:config&gt;</text>

  <!-- Global pointcut -->
  <rect x="22" y="42" width="415" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="229" y="60" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">&lt;aop:pointcut id="svcOps" expression="execution(* *.*(..))"/&gt;</text>

  <!-- aop:aspect -->
  <rect x="22" y="78" width="415" height="110" rx="6" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="229" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">&lt;aop:aspect ref="auditBean"&gt;</text>

  <rect x="34" y="105" width="390" height="22" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="229" y="120" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">&lt;aop:before   pointcut-ref="svcOps" method="logCall"/&gt;</text>

  <rect x="34" y="131" width="390" height="22" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="229" y="146" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">&lt;aop:after-returning  returning="r"  method="cache"/&gt;</text>

  <rect x="34" y="157" width="390" height="22" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="229" y="172" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">&lt;aop:around                          method="time"/&gt;</text>

  <!-- Arrow to bean -->
  <line x1="452" y1="105" x2="490" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="471" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ref</text>

  <!-- Bean box -->
  <rect x="490" y="65" width="135" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="558" y="87" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">auditBean</text>
  <text x="558" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">logCall()</text>
  <text x="558" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">cache(retVal)</text>
  <text x="558" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">time(pjp)</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><polygon points="0 0,8 3,0 6" fill="#6db33f"/></marker>
  </defs>
</svg>

Global `<aop:pointcut>` shared by multiple advice elements; each element delegates to one method on the backing bean.

## 5. Runnable example

Scenario: an **order service** wired entirely via XML — first a named pointcut + `<aop:before>`, then full advice palette, then `<aop:around>` with argument binding.

### Level 1 — Basic

Single named pointcut + `<aop:before>`.

```java
// XmlAdviceDemo.java
import org.springframework.context.support.*;
import org.aspectj.lang.JoinPoint;

public class XmlAdviceDemo {
    public static void main(String[] args) {
        var ctx = new ClassPathXmlApplicationContext("xml-advice.xml");
        ctx.getBean("orderService", OrderService.class).placeOrder("ORD-1", 49.0);
        ctx.close();
    }
}

class OrderService {
    public String placeOrder(String id, double amount) {
        System.out.println("Order placed: " + id + " $" + amount);
        return "OK";
    }
}

class AuditBean {
    public void logCall(JoinPoint jp) {
        System.out.println("[AUDIT] " + jp.getSignature().getName()
            + " args=" + java.util.Arrays.toString(jp.getArgs()));
    }
}
```

`xml-advice.xml`:
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

  <bean id="orderService" class="OrderService"/>
  <bean id="auditBean"    class="AuditBean"/>

  <aop:config>
    <!-- Named pointcut — global to this aop:config -->
    <aop:pointcut id="orderOps" expression="execution(* OrderService.*(..))"/>

    <aop:aspect ref="auditBean">
      <aop:before pointcut-ref="orderOps" method="logCall"/>
    </aop:aspect>
  </aop:config>
</beans>
```

How to run: `java -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:. XmlAdviceDemo.java`

`logCall` fires before `placeOrder`. Named pointcut `orderOps` can be reused by any other aspect in this `<aop:config>`.

---

### Level 2 — Intermediate

Full advice palette: `<aop:before>`, `<aop:after-returning>`, `<aop:after-throwing>`, `<aop:after>`.

```java
// XmlAdviceDemo.java
import org.springframework.context.support.*;
import org.aspectj.lang.JoinPoint;

public class XmlAdviceDemo {
    public static void main(String[] args) {
        var ctx = new ClassPathXmlApplicationContext("xml-advice.xml");
        var svc = ctx.getBean("orderService", OrderService.class);
        svc.placeOrder("ORD-1", 99.0);
        try { svc.placeOrder("ORD-BAD", -5.0); }
        catch (IllegalArgumentException e) { System.out.println("Caught: " + e.getMessage()); }
        ctx.close();
    }
}

class OrderService {
    public String placeOrder(String id, double amount) {
        if (amount < 0) throw new IllegalArgumentException("Negative amount: " + amount);
        System.out.println("Order placed: " + id + " $" + amount);
        return "CONFIRMED";
    }
}

class LifecycleBean {
    public void before(JoinPoint jp) {
        System.out.println("[BEFORE] " + jp.getSignature().getName());
    }
    public void afterReturning(JoinPoint jp, Object result) {
        System.out.println("[AFTER-RETURNING] result=" + result);
    }
    public void afterThrowing(JoinPoint jp, Exception ex) {
        System.out.println("[AFTER-THROWING] " + ex.getMessage());
    }
    public void afterFinally(JoinPoint jp) {
        System.out.println("[AFTER/FINALLY] " + jp.getSignature().getName());
    }
}
```

`xml-advice.xml`:
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
         http://www.springframework.org/schema/beans
         https://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/aop
         https://www.springframework.org/schema/aop/spring-aop.xsd">

  <bean id="orderService"   class="OrderService"/>
  <bean id="lifecycleBean"  class="LifecycleBean"/>

  <aop:config>
    <aop:pointcut id="orderOps" expression="execution(* OrderService.*(..))"/>

    <aop:aspect ref="lifecycleBean">
      <aop:before          pointcut-ref="orderOps" method="before"/>
      <aop:after-returning pointcut-ref="orderOps" method="afterReturning" returning="result"/>
      <aop:after-throwing  pointcut-ref="orderOps" method="afterThrowing"  throwing="ex"/>
      <aop:after           pointcut-ref="orderOps" method="afterFinally"/>
    </aop:aspect>
  </aop:config>
</beans>
```

How to run: same classpath

`returning="result"` binds the return value to `afterReturning(JoinPoint, Object result)`. `throwing="ex"` binds to `afterThrowing(JoinPoint, Exception ex)`.

---

### Level 3 — Advanced

`<aop:around>` with argument binding using `arg-names`.

```java
// XmlAdviceDemo.java
import org.springframework.context.support.*;
import org.aspectj.lang.*;

public class XmlAdviceDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new ClassPathXmlApplicationContext("xml-advice.xml");
        var svc = ctx.getBean("orderService", OrderService.class);
        svc.placeOrder("ORD-VIP", 500.0);
        svc.placeOrder("ORD-STD", 10.0);
        ctx.close();
    }
}

class OrderService {
    public String placeOrder(String id, double amount) throws InterruptedException {
        Thread.sleep(50);
        System.out.println("Order: " + id + " $" + amount);
        return "OK";
    }
}

class TimingBean {
    // args(id, amount) must match arg-names attribute in XML
    public Object timeAndEnrich(ProceedingJoinPoint pjp, String id, double amount) throws Throwable {
        long t0 = System.currentTimeMillis();
        System.out.printf("[AROUND/enter] id=%s amount=%.2f%n", id, amount);
        // Modify argument: VIP orders get 10% discount
        Object result = amount >= 100
            ? pjp.proceed(new Object[]{id, amount * 0.9})
            : pjp.proceed();
        long elapsed = System.currentTimeMillis() - t0;
        System.out.printf("[AROUND/exit]  elapsed=%dms result=%s%n", elapsed, result);
        return result;
    }
}
```

`xml-advice.xml`:
```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:aop="http://www.springframework.org/schema/aop"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="
         http://www.springframework.org/schema/beans
         https://www.springframework.org/schema/beans/spring-beans.xsd
         http://www.springframework.org/schema/aop
         https://www.springframework.org/schema/aop/spring-aop.xsd">

  <bean id="orderService" class="OrderService"/>
  <bean id="timingBean"   class="TimingBean"/>

  <aop:config>
    <aop:pointcut id="orderOps"
      expression="execution(* OrderService.placeOrder(String, double)) and args(id, amount)"/>

    <aop:aspect ref="timingBean">
      <aop:around pointcut-ref="orderOps" method="timeAndEnrich" arg-names="id,amount"/>
    </aop:aspect>
  </aop:config>
</beans>
```

How to run: same classpath + XML on classpath

`arg-names="id,amount"` tells Spring which parameters on `timeAndEnrich` correspond to the `args(id, amount)` binding in the pointcut. `pjp.proceed(new Object[]{id, amount * 0.9})` passes modified arguments for VIP orders.

## 6. Walkthrough

**Startup — XML parsing:**
1. `ClassPathXmlApplicationContext` parses `xml-advice.xml`.
2. `AopNamespaceHandler` processes `<aop:config>`.
3. `<aop:pointcut id="orderOps" …/>` compiles the AspectJ expression and registers it by id.
4. `<aop:around … arg-names="id,amount"/>` creates an `AspectJAroundAdvice` adapter that maps `id` and `amount` to method parameters via reflection.
5. An `AspectJPointcutAdvisor` wraps the advice + pointcut and is registered in the context.

**Proxy creation for `orderService`:**
- `AnnotationAwareAspectJAutoProxyCreator` finds the advisor matches `OrderService`.
- Wraps `orderService` in a CGLIB proxy.

**`svc.placeOrder("ORD-VIP", 500.0)` (Level 3):**
1. Proxy intercepts `placeOrder`.
2. `TimingBean.timeAndEnrich(pjp, "ORD-VIP", 500.0)` enters; `t0` recorded.
3. `amount >= 100` → `pjp.proceed({"ORD-VIP", 450.0})` — discount applied.
4. Real `placeOrder("ORD-VIP", 450.0)` runs.
5. Returns `"OK"`.
6. `timeAndEnrich` prints elapsed + result.

**`svc.placeOrder("ORD-STD", 10.0):`**
- `amount < 100` → `pjp.proceed()` with original args; no modification.

## 7. Gotchas & takeaways

> **`arg-names` is required when Spring cannot deduce parameter names from debug info.** If the compiled class lacks `-parameters` flag (Java 8+) or `-g` debug flag, Spring falls back to `arg-names` in the XML to perform the binding. Omitting it causes `IllegalArgumentException: error at ::0 can't find referenced pointcut`.

> **Global vs local `<aop:pointcut>`.** A `<aop:pointcut>` inside `<aop:config>` directly (not nested under `<aop:aspect>`) is global — any aspect can reference it via `pointcut-ref`. A pointcut inside `<aop:aspect>` is local to that aspect only.

- XML advice ordering within one `<aop:aspect>` is determined by declaration order in the file. For cross-aspect ordering, add an `order` attribute to `<aop:aspect order="1">`.
- The `and`/`or`/`not` keywords replace `&&`/`||`/`!` in XML to avoid entity escaping issues.
- The `method` attribute value must match an accessible (public) method name on the backing bean. Overloaded methods need unique names — Spring cannot distinguish overloads at XML configuration time.
