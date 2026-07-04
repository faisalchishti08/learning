---
card: spring-framework
gi: 234
slug: using-aspectj-with-spring-ltw-load-time-weaving
title: Using AspectJ with Spring (LTW — load-time weaving)
---

## 1. What it is

**Load-time weaving (LTW)** is a technique where AspectJ modifies class bytecode as the JVM loads classes, rather than at compile time or through proxies at runtime. Unlike Spring's default proxy-based AOP, LTW can intercept:

- `private` methods
- `static` methods
- `new` object creation (constructor interception)
- `final` methods and classes
- **Self-invocations** (calls through `this`) — the most important advantage over proxy AOP

LTW requires a **Java agent** (`-javaagent:spring-instrument.jar` or AspectJ's `aspectjweaver.jar` as agent) which installs a custom `ClassLoader` that transforms bytecode at load time.

```java
// aop.xml activates LTW:
// <!DOCTYPE aspectj PUBLIC "-//AspectJ//DTD//EN" "...">
// <aspectj><weaver ...><include within="com.example..*"/></weaver></aspectj>
```

## 2. Why & when

Use LTW when proxy-based AOP cannot reach the join point you need:

| Scenario | Proxy AOP | LTW |
|----------|-----------|-----|
| Public method on a Spring bean | ✓ | ✓ |
| Private method | ✗ | ✓ |
| Static method | ✗ | ✓ |
| `final` method | ✗ | ✓ |
| Self-invocation | ✗ | ✓ |
| Non-Spring-managed object (`new Foo()`) | ✗ | ✓ |
| Domain object interception | ✗ | ✓ |

LTW is heavier: requires JVM agent startup flag, `META-INF/aop.xml` configuration, and debugging is harder because there is no proxy object to inspect. Use it when proxy limitations are actually blocking you, not as a default.

## 3. Core concept

The LTW pipeline:

1. **AspectJ Weaver agent** (`-javaagent:aspectjweaver.jar`) installs a `WeavingURLClassLoader` that intercepts every class load.
2. **`META-INF/aop.xml`** tells the weaver which aspects to apply and which classes to weave.
3. Spring activates this via `@EnableLoadTimeWeaving` or `<context:load-time-weaver/>`, which registers a `LoadTimeWeavingConfigurer`.
4. At class load time the weaver rewrites bytecode to inline the advice directly into the class — no proxy, no `MethodInterceptor` chain.
5. The resulting class has advice baked in: calling `target.privateHelper()` or `this.foo()` triggers the advice because the call site itself is instrumented.

Key configuration:
- `META-INF/aop.xml` — names the aspect classes and the packages to weave.
- Spring's `@EnableLoadTimeWeaving(aspectjWeaving = ENABLED)` — bridges Spring context with the AspectJ weaver.
- `@Configurable` — allows Spring dependency injection into `new`-created objects (requires LTW).

## 4. Diagram

<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- JVM ClassLoader -->
  <rect x="10" y="80" width="130" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="100" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JVM ClassLoader</text>
  <text x="75" y="116" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">loads .class bytes</text>

  <line x1="142" y1="105" x2="195" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Weaver -->
  <rect x="195" y="60" width="200" height="90" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="295" y="84" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">AspectJ Weaver Agent</text>
  <text x="295" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">reads META-INF/aop.xml</text>
  <text x="295" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">rewrites bytecode inline</text>
  <text x="295" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">-javaagent:aspectjweaver.jar</text>

  <line x1="397" y1="105" x2="450" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Woven class -->
  <rect x="450" y="70" width="240" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="94" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Woven Class Bytecode</text>
  <text x="570" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">advice inlined at every join point</text>
  <text x="570" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">private / static / final — all covered</text>

  <!-- aop.xml -->
  <rect x="215" y="175" width="160" height="40" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="295" y="192" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">META-INF/aop.xml</text>
  <text x="295" y="207" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">which aspects, which classes</text>
  <line x1="295" y1="173" x2="295" y2="152" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,2"/>
</svg>

LTW rewrites bytecode at class-load time. Advice is baked in — no proxy, no self-invocation gap.

## 5. Runnable example

Scenario: a **`ReportingService`** — first using LTW to intercept a private method (impossible with proxy AOP), then adding `@Configurable` to inject into `new`-created objects.

### Level 1 — Basic

LTW setup: aspect intercepts a `private` method called inside `ReportingService`.

```java
// LTWDemo.java  (needs: -javaagent:aspectjweaver.jar)
import org.springframework.context.annotation.*;
import org.springframework.context.weaving.*;
import org.springframework.stereotype.*;

@Configuration
@EnableLoadTimeWeaving(aspectjWeaving = EnableLoadTimeWeaving.AspectJWeaving.ENABLED)
@ComponentScan
public class LTWDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LTWDemo.class);
        ctx.getBean(ReportingService.class).generateReport("Q1");
        ctx.close();
    }
}

@Component
class ReportingService {
    public void generateReport(String quarter) {
        System.out.println("[Report] generating " + quarter);
        buildData(quarter);   // self-invoke of private method — LTW CAN intercept
    }

    private void buildData(String quarter) {
        System.out.println("[Report] building data for " + quarter);
    }
}
```

`META-INF/aop.xml` (on classpath):
```xml
<!DOCTYPE aspectj PUBLIC
  "-//AspectJ//DTD//EN"
  "https://www.eclipse.org/aspectj/dtd/aspectj.dtd">
<aspectj>
  <weaver options="-verbose">
    <include within="com.example..*"/>
    <include within="ReportingService"/>
  </weaver>
  <aspects>
    <aspect name="PrivateCallAspect"/>
  </aspects>
</aspectj>
```

Aspect class (must be compiled/on classpath):
```java
// PrivateCallAspect.java
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;

@Aspect
public class PrivateCallAspect {
    @Before("execution(private * ReportingService.*(..))")
    public void beforePrivate(JoinPoint jp) {
        System.out.println("[LTW-ASPECT] private method: " + jp.getSignature().toShortString());
    }
}
```

How to run: `java -javaagent:aspectjweaver.jar -cp spring-context.jar:spring-aop.jar:aspectjweaver.jar:spring-instrument.jar:. LTWDemo.java`

Output includes `[LTW-ASPECT] private method: buildData(String)` — proof that LTW intercepted the `private` method and the self-invocation path. Proxy-based AOP cannot do either.

---

### Level 2 — Intermediate

Extend the same scenario to **`static` method interception** — another LTW-only capability.

```java
// LTWDemo.java
import org.springframework.context.annotation.*;
import org.springframework.context.weaving.*;
import org.springframework.stereotype.*;

@Configuration
@EnableLoadTimeWeaving(aspectjWeaving = EnableLoadTimeWeaving.AspectJWeaving.ENABLED)
@ComponentScan
public class LTWDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LTWDemo.class);
        ctx.getBean(ReportingService.class).generateReport("Q2");
        ctx.close();
    }
}

@Component
class ReportingService {
    public void generateReport(String quarter) {
        System.out.println("[Report] generating " + quarter);
        buildData(quarter);
        String fmt = formatOutput(quarter);   // static call
        System.out.println("[Report] final: " + fmt);
    }

    private void buildData(String quarter) {
        System.out.println("[Report] building data for " + quarter);
    }

    static String formatOutput(String quarter) {
        return "REPORT-" + quarter.toUpperCase();
    }
}
```

Updated aspect:
```java
// PrivateCallAspect.java
import org.aspectj.lang.annotation.*;
import org.aspectj.lang.*;

@Aspect
public class PrivateCallAspect {
    @Before("execution(private * ReportingService.*(..))")
    public void beforePrivate(JoinPoint jp) {
        System.out.println("[LTW] private: " + jp.getSignature().toShortString());
    }

    @Before("execution(static * ReportingService.*(..))")
    public void beforeStatic(JoinPoint jp) {
        System.out.println("[LTW] static:  " + jp.getSignature().toShortString());
    }
}
```

How to run: same as Level 1

Both `[LTW] private: buildData(String)` and `[LTW] static: formatOutput(String)` appear in the output. Spring's proxy AOP cannot reach either.

---

### Level 3 — Advanced

**`@Configurable`** — inject Spring beans into objects created with `new` outside the container. LTW patches the constructor to call Spring's `AspectJAfterConstruction` advisor.

```java
// LTWDemo.java
import org.springframework.context.annotation.*;
import org.springframework.context.weaving.*;
import org.springframework.beans.factory.annotation.*;

@Configuration
@EnableLoadTimeWeaving(aspectjWeaving = EnableLoadTimeWeaving.AspectJWeaving.ENABLED)
@EnableSpringConfigured           // activates @Configurable support
@ComponentScan
public class LTWDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LTWDemo.class);

        // Created with 'new' — NOT fetched from context
        Report report = new Report("Q3");
        report.print();           // Spring-injected formatter is available

        ctx.close();
    }
}

@org.springframework.beans.factory.annotation.Configurable
class Report {
    @Autowired
    private ReportFormatter formatter;   // injected by Spring via LTW

    private final String quarter;

    Report(String quarter) {
        this.quarter = quarter;
    }

    public void print() {
        System.out.println(formatter.format(quarter));
    }
}

@org.springframework.stereotype.Component
class ReportFormatter {
    public String format(String q) { return "=== REPORT " + q.toUpperCase() + " ==="; }
}
```

`aop.xml` addition:
```xml
<aspects>
  <aspect name="org.springframework.beans.factory.aspectj.AnnotationBeanConfigurerAspect"/>
</aspects>
```

How to run: `java -javaagent:aspectjweaver.jar -cp spring-context.jar:spring-aspects.jar:spring-beans.jar:spring-aop.jar:aspectjweaver.jar:. LTWDemo.java`

`new Report("Q3")` is created outside the Spring container, yet `Report.formatter` is wired because LTW patches the constructor to call Spring's bean-configurer aspect. The output is `=== REPORT Q3 ===`. This is essential for domain-driven design where domain objects must carry Spring-managed services.

## 6. Walkthrough

**JVM startup (all levels):**

1. `-javaagent:aspectjweaver.jar` installs the AspectJ transformer before any app class loads.
2. The transformer reads `META-INF/aop.xml` from the classpath at startup.
3. `<include within="ReportingService"/>` tells the weaver to watch for this class.

**Class load of `ReportingService`:**

```
ClassLoader.loadClass("ReportingService")
  → AspectJ transformer intercepts raw bytes
  → reads PrivateCallAspect pointcuts:
      execution(private * ReportingService.*(..))
      execution(static * ReportingService.*(..))
  → rewrites ReportingService.class bytecode:
      buildData() {
        PrivateCallAspect.beforePrivate(thisJoinPoint);  ← inlined
        // ... original body
      }
      static formatOutput() {
        PrivateCallAspect.beforeStatic(thisJoinPoint);   ← inlined
        // ... original body
      }
  → returns modified bytes to JVM
```

**Per-call flow for `generateReport("Q1")` (Level 1):**

```
generateReport("Q1")
  prints "[Report] generating Q1"
  → buildData("Q1")   ← now woven — advice baked in
      PrivateCallAspect.beforePrivate() fires
      prints "[LTW-ASPECT] private method: buildData(String)"
      prints "[Report] building data for Q1"
```

No proxy is involved. The woven class IS the real class — calling `this.buildData()` goes through the woven bytecode, so advice fires.

**Level 3 — `@Configurable` path:**

```
new Report("Q3")
  → Report.<init>("Q3") called
  → LTW-woven constructor runs:
      AnnotationBeanConfigurerAspect.configureBean(this)
        → Spring ApplicationContext.autowireBean(report)
           injects report.formatter = ReportFormatter bean
  ← returns wired Report instance
```

## 7. Gotchas & takeaways

> **LTW requires `-javaagent` at JVM startup.** Forgetting it means `aop.xml` is silently ignored — no aspects fire, no error. Always add a startup check (e.g., print `PrivateCallAspect.class.getClassLoader().getClass()`) to confirm the weaving ClassLoader is active.

> **`@Configurable` injection is not available until the Spring `ApplicationContext` is fully started.** If you call `new Report(...)` during `@Bean` construction — before the context is up — the injection will fail silently or throw. Wait until the context is running before instantiating `@Configurable` objects.

> **`aop.xml` `<include within="..."/>` is required.** Without it the weaver touches every class on the classpath — including JDK internals — which causes `VerifyError` or extreme startup slowness.

- LTW advantages over proxy AOP: `private`, `static`, `final`, self-invocation, non-Spring objects.
- LTW disadvantages: agent setup, harder debugging (no proxy object), `aop.xml` maintenance.
- Spring's `@EnableLoadTimeWeaving` bridges Spring DI with the AspectJ weaver.
- In Spring Boot, LTW can be enabled via `spring.aop.aspectj-weaving=ENABLED` property (Boot 3+).
- Use LTW for domain object injection (`@Configurable`) or `@Transactional` on `private` methods — not as a default replacement for proxy AOP.
