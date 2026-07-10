---
card: spring-framework
gi: 453
slug: the-aop-schema
title: "The aop schema"
---

## 1. What it is

The `aop` namespace (`xmlns:aop="http://www.springframework.org/schema/aop"`) is the XML equivalent of `@Aspect`/`@Pointcut`/`@Before`/`@Around`-style annotations: `<aop:config>`, `<aop:aspect>`, `<aop:pointcut>`, and advice elements (`<aop:before>`, `<aop:after>`, `<aop:around>`, `<aop:after-returning>`, `<aop:after-throwing>`) let you declare cross-cutting behavior — logging, security checks, transaction-like wrapping — entirely in XML, pointing at plain POJO methods as the advice logic instead of annotated classes.

```xml
<aop:config>
    <aop:aspect ref="loggingAspect">
        <aop:pointcut id="serviceMethods"
            expression="execution(* com.example.service.*.*(..))"/>
        <aop:before pointcut-ref="serviceMethods" method="logBefore"/>
    </aop:aspect>
</aop:config>
```

## 2. Why & when

Before `@Aspect` and `@EnableAspectJAutoProxy` became the default way to write aspects, all AOP configuration in Spring was XML — a plain Java class with a `logBefore(JoinPoint jp)` method became an aspect purely by being *referenced* from an `<aop:aspect>` block, with no annotations on the class at all. That separation of "plain class" from "aspect wiring" is still the reason to reach for the `aop` schema today.

Use the `aop` schema specifically when:

- You're maintaining a legacy XML-configured Spring application where aspects are already wired this way, and need to add, modify, or trace a pointcut or piece of advice.
- You want to apply AOP behavior to classes you can't or don't want to annotate — third-party classes, generated code, or code you want to keep framework-agnostic — since the pointcut and advice wiring live entirely outside the advised class.
- You're configuring proxy behavior declaratively alongside other XML bean definitions in a codebase that is XML-first by convention, keeping all wiring in one place rather than split across XML and annotations.

For new code, `@Aspect` classes with `@EnableAspectJAutoProxy` are almost always simpler and more discoverable — the `aop` schema mainly exists to support and explain configuration that predates that style.

## 3. Core concept

```
 <aop:config>
     |
     v
 <aop:aspect ref="loggingAspect">  -- points at a plain, unannotated bean
     |
     +-- <aop:pointcut expression="execution(...)"/>   -- WHERE the advice applies
     |
     +-- <aop:before method="logBefore" .../>          -- WHEN + WHAT method runs
     +-- <aop:around method="wrapCall" .../>
     +-- <aop:after-throwing method="logError" .../>

 At context-refresh time:
   Spring finds every bean matching each pointcut's expression
        |
        v
   wraps that bean in a JDK dynamic proxy (or CGLIB proxy)
        |
        v
   calls into "loggingAspect"'s named methods around the real call
```

The `ref` attribute is what turns an ordinary bean into an aspect — nothing about the referenced class itself is special.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="aop:config wires a pointcut expression and advice methods from a plain bean around matching target beans via a proxy">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">loggingAspect bean</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">plain POJO, no annotations</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;aop:aspect&gt; wiring</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">pointcut + advice methods</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Proxy factory</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">at context refresh</text>

  <rect x="240" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService bean</text>
  <text x="330" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">matches pointcut expression</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="550" y1="70" x2="330" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The proxy factory reads the aspect wiring and the pointcut expression, then wraps every bean whose method calls match — here, `OrderService`.

## 5. Runnable example

The scenario: a plain `OrderService` bean whose `placeOrder` method should be logged before and after each call, and have exceptions logged too — all configured purely in XML against an unannotated logging class.

### Level 1 — Basic

Wire a single `<aop:before>` advice around one method, using `<aop:config>`/`<aop:aspect>`/`<aop:pointcut>` and a plain Java logging bean.

```java
import org.aspectj.lang.JoinPoint;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;

public class AopSchemaLevel1 {

    public static class LoggingAspect {
        public void logBefore(JoinPoint jp) {
            System.out.println("[before] calling " + jp.getSignature().toShortString());
        }
    }

    public static class OrderService {
        public String placeOrder(String item) {
            return "order placed: " + item;
        }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:aop="http://www.springframework.org/schema/aop"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/aop
                       https://www.springframework.org/schema/aop/spring-aop.xsd">

                <bean id="loggingAspect" class="AopSchemaLevel1$LoggingAspect"/>
                <bean id="orderService" class="AopSchemaLevel1$OrderService"/>

                <aop:config>
                    <aop:aspect ref="loggingAspect">
                        <aop:pointcut id="orderMethods"
                            expression="execution(* AopSchemaLevel1.OrderService.*(..))"/>
                        <aop:before pointcut-ref="orderMethods" method="logBefore"/>
                    </aop:aspect>
                </aop:config>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        OrderService service = ctx.getBean(OrderService.class);
        String result = service.placeOrder("widget");
        System.out.println("result = " + result);

        if (!result.equals("order placed: widget"))
            throw new AssertionError("Unexpected result from placeOrder");
        System.out.println("aop:before advice ran before the real method -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context`, `spring-aop`, and `aspectjweaver` on the classpath, then `java AopSchemaLevel1.java` on JDK 17+.

`<aop:pointcut expression="execution(...)">` uses AspectJ pointcut syntax to match every method on `OrderService`. `<aop:before>` says: before any matching method runs, call `loggingAspect.logBefore(JoinPoint)` first. At startup Spring detects that `orderService` matches the pointcut and wraps it in a proxy; the `service` variable in `main` is that proxy, not the raw object, which is why the `[before]` log line appears before `result` is computed.

### Level 2 — Intermediate

Add `<aop:after-throwing>` for error logging and `<aop:around>` for timing, showing how multiple advice types combine around the same pointcut — the real-world shape of a logging-and-monitoring aspect.

```java
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.ProceedingJoinPoint;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;

public class AopSchemaLevel2 {

    public static class LoggingAspect {
        public void logBefore(JoinPoint jp) {
            System.out.println("[before] " + jp.getSignature().toShortString());
        }
        public void logError(JoinPoint jp, Throwable ex) {
            System.out.println("[error] " + jp.getSignature().toShortString() + " threw " + ex.getClass().getSimpleName());
        }
        public Object timeCall(ProceedingJoinPoint pjp) throws Throwable {
            long start = System.nanoTime();
            try {
                return pjp.proceed();
            } finally {
                long micros = (System.nanoTime() - start) / 1000;
                System.out.println("[timing] " + pjp.getSignature().toShortString() + " took " + micros + "us");
            }
        }
    }

    public static class OrderService {
        public String placeOrder(String item) {
            if (item == null) throw new IllegalArgumentException("item cannot be null");
            return "order placed: " + item;
        }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:aop="http://www.springframework.org/schema/aop"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/aop
                       https://www.springframework.org/schema/aop/spring-aop.xsd">

                <bean id="loggingAspect" class="AopSchemaLevel2$LoggingAspect"/>
                <bean id="orderService" class="AopSchemaLevel2$OrderService"/>

                <aop:config>
                    <aop:aspect ref="loggingAspect">
                        <aop:pointcut id="orderMethods"
                            expression="execution(* AopSchemaLevel2.OrderService.*(..))"/>
                        <aop:before pointcut-ref="orderMethods" method="logBefore"/>
                        <aop:after-throwing pointcut-ref="orderMethods" method="logError" throwing="ex"/>
                        <aop:around pointcut-ref="orderMethods" method="timeCall"/>
                    </aop:aspect>
                </aop:config>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        OrderService service = ctx.getBean(OrderService.class);
        System.out.println(service.placeOrder("widget"));

        try {
            service.placeOrder(null);
            throw new AssertionError("Expected IllegalArgumentException to propagate");
        } catch (IllegalArgumentException expected) {
            System.out.println("Exception propagated after aop:after-throwing ran -- PASS");
        }
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java AopSchemaLevel2.java`.

`<aop:around>` wraps the entire call — `timeCall` must call `pjp.proceed()` itself to let the real method run, which is what lets it measure elapsed time around it. `<aop:after-throwing throwing="ex">` binds the thrown exception to the advice method's `ex` parameter by name, and runs only when the advised method throws — note the exception still propagates to the caller afterward; advice observes it, it doesn't swallow it unless written to.

### Level 3 — Advanced

Introduce a second aspect with explicit ordering (`<aop:aspect order="...">`), a narrower pointcut using an `&&` combination, and an `<aop:after-returning>` that inspects the actual return value — the shape of a production setup where a security aspect must run before a logging aspect on the same join point.

```java
import org.aspectj.lang.JoinPoint;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

public class AopSchemaLevel3 {

    public static final List<String> CALL_ORDER = new ArrayList<>();

    public static class SecurityAspect {
        public void checkAccess(JoinPoint jp) {
            CALL_ORDER.add("security-check");
            System.out.println("[security] authorized call to " + jp.getSignature().toShortString());
        }
    }

    public static class LoggingAspect {
        public void logBefore(JoinPoint jp) {
            CALL_ORDER.add("log-before");
            System.out.println("[before] " + jp.getSignature().toShortString());
        }
        public void logResult(JoinPoint jp, Object result) {
            CALL_ORDER.add("log-result");
            System.out.println("[after-returning] " + jp.getSignature().toShortString() + " -> " + result);
        }
    }

    public static class OrderService {
        public String placeOrder(String item, int quantity) {
            return "order placed: " + quantity + "x " + item;
        }
        public String cancelOrder(String orderId) {
            return "order cancelled: " + orderId;
        }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:aop="http://www.springframework.org/schema/aop"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/aop
                       https://www.springframework.org/schema/aop/spring-aop.xsd">

                <bean id="securityAspect" class="AopSchemaLevel3$SecurityAspect"/>
                <bean id="loggingAspect" class="AopSchemaLevel3$LoggingAspect"/>
                <bean id="orderService" class="AopSchemaLevel3$OrderService"/>

                <aop:config>
                    <aop:aspect ref="securityAspect" order="1">
                        <aop:pointcut id="placeOrderOnly"
                            expression="execution(* AopSchemaLevel3.OrderService.placeOrder(..)) &amp;&amp; args(item, quantity)"/>
                        <aop:before pointcut-ref="placeOrderOnly" method="checkAccess"/>
                    </aop:aspect>
                    <aop:aspect ref="loggingAspect" order="2">
                        <aop:pointcut id="allOrderMethods"
                            expression="execution(* AopSchemaLevel3.OrderService.*(..))"/>
                        <aop:before pointcut-ref="allOrderMethods" method="logBefore"/>
                        <aop:after-returning pointcut-ref="allOrderMethods" method="logResult" returning="result"/>
                    </aop:aspect>
                </aop:config>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        OrderService service = ctx.getBean(OrderService.class);
        String placed = service.placeOrder("widget", 3);
        System.out.println("placed = " + placed);

        List<String> forPlaceOrder = new ArrayList<>(CALL_ORDER);
        System.out.println("call order for placeOrder = " + forPlaceOrder);

        if (!forPlaceOrder.equals(List.of("security-check", "log-before", "log-result")))
            throw new AssertionError("Expected security to run before logging: " + forPlaceOrder);

        CALL_ORDER.clear();
        service.cancelOrder("ORD-1");
        List<String> forCancel = new ArrayList<>(CALL_ORDER);
        System.out.println("call order for cancelOrder (no security pointcut match) = " + forCancel);
        if (!forCancel.equals(List.of("log-before", "log-result")))
            throw new AssertionError("Expected only logging advice on cancelOrder: " + forCancel);

        System.out.println("aop:order + narrowed pointcut + after-returning -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java AopSchemaLevel3.java`.

`order="1"` on `securityAspect` and `order="2"` on `loggingAspect` guarantees the security check runs before the logging `before` advice whenever both apply to the same join point — without `order`, the relative sequence of two aspects on the same pointcut is otherwise unspecified. The `placeOrderOnly` pointcut combines `execution(...)` with `args(item, quantity)` using `&amp;&amp;` (XML-escaped `&&`), narrowing it to only `placeOrder`, which is why `cancelOrder` shows no `security-check` entry in its call order — its signature doesn't match the narrower pointcut, only the broader `allOrderMethods` one. `<aop:after-returning returning="result">` binds the real return value into the advice method's `result` parameter, letting the logging aspect print what was actually returned.

## 6. Walkthrough

Trace Level 3's `service.placeOrder("widget", 3)` call end-to-end.

1. **Context refresh**: Spring parses `<aop:config>`, finds two `<aop:aspect>` blocks referencing `securityAspect` and `loggingAspect`, and registers their pointcuts and advice methods internally as `Advisor`s.
2. **Proxy creation**: Because `orderService`'s methods match at least one pointcut expression, Spring wraps it in a proxy (JDK dynamic proxy here, since it doesn't implement an interface it would use CGLIB) at context-refresh time. `ctx.getBean(OrderService.class)` returns this proxy.
3. **Call enters the proxy**: `service.placeOrder("widget", 3)` first hits the proxy, not the real `OrderService` instance.
4. **Advisor chain resolution**: the proxy determines which advisors apply to `placeOrder(String, int)`, then orders them — `securityAspect` (order 1) before `loggingAspect` (order 2).
5. **`securityAspect.checkAccess`** runs first (its pointcut `placeOrderOnly` matches, binding `item="widget"`, `quantity=3` via `args(...)`), appending `"security-check"` to `CALL_ORDER`.
6. **`loggingAspect.logBefore`** runs next, appending `"log-before"`.
7. **Real method executes**: the underlying `OrderService.placeOrder` body runs, returning `"order placed: 3x widget"`.
8. **`loggingAspect.logResult`** runs as `after-returning`, receiving the real return value bound to `result`, appending `"log-result"`.
9. **Proxy returns** the real return value up to `main`, unchanged by the advice.
10. **Assertions** check `CALL_ORDER` equals `["security-check", "log-before", "log-result"]`, confirming both ordering and pointcut scoping worked; then the test clears the list and calls `cancelOrder`, which only matches the broader `allOrderMethods` pointcut, confirming `securityAspect` correctly did *not* fire for it.

```
 placeOrder("widget", 3) call
        |
        v
 [proxy] -- advisor chain, ordered: security(1), logging(2)
        |
        +--> securityAspect.checkAccess()      CALL_ORDER += security-check
        +--> loggingAspect.logBefore()          CALL_ORDER += log-before
        +--> [[ real OrderService.placeOrder ]] returns "order placed: 3x widget"
        +--> loggingAspect.logResult(result)    CALL_ORDER += log-result
        |
        v
 return value passed back to caller, unchanged
```

## 7. Gotchas & takeaways

> **Gotcha:** `<aop:config>` proxies work the same way `@Aspect` proxies do — self-invocation (a method calling another method on `this` within the same bean) bypasses the proxy entirely, so advice on the inner call never fires. This trips up both XML and annotation-based AOP equally; it's not specific to the `aop` schema.

- `<aop:aspect ref="...">` can point at any plain bean — the referenced class needs no annotations, interfaces, or base classes, which is what makes XML AOP usable against code you don't control.
- Advice ordering across multiple aspects on the same pointcut is unspecified unless you set `order` explicitly — always set it when the relative sequence matters (as with security-before-logging).
- `<aop:pointcut>` expressions use the same AspectJ syntax as `@Pointcut` — knowledge of one transfers directly to the other; only the surrounding wiring differs.
- When migrating legacy `aop`-schema configuration to annotations, each `<aop:aspect>` block maps to one `@Aspect` class, each `<aop:pointcut>` to a `@Pointcut` method, and each advice element to its matching annotation (`<aop:before>` → `@Before`, and so on).
