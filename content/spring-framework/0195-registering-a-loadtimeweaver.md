---
card: spring-framework
gi: 195
slug: registering-a-loadtimeweaver
title: "Registering a LoadTimeWeaver"
---

## 1. What it is

A `LoadTimeWeaver` (LTW) is Spring's infrastructure for applying AspectJ aspects to classes as they are loaded by the JVM classloader, without compile-time weaving. Activating LTW requires adding a JVM agent (`-javaagent:spring-instrument.jar`) and registering the weaver in Spring.

```java
// Annotation-based activation
@Configuration
@EnableLoadTimeWeaving(aspectjWeaving = AspectJWeaving.AUTODETECT)
public class AppConfig { }
```

```xml
<!-- XML equivalent -->
<context:load-time-weaver />
```

Once registered, Spring uses the `LoadTimeWeaver` internally for:
- **JPA providers** (Hibernate, EclipseLink) that require `InstrumentationLoadTimeWeaver` for lazy loading and bytecode enhancement.
- **Full AspectJ LTW** — aspects that cannot be expressed with Spring AOP proxies (e.g., aspects on `new` constructor calls or non-Spring-managed objects).

## 2. Why & when

- **JPA with EclipseLink** — EclipseLink requires class instrumentation for LAZY loading; registers `ClassTransformer` on the LTW.
- **Full AspectJ** — aspects that require actual bytecode weaving (call/execution join points on non-Spring beans, field access, etc.).
- **`@Configurable`** — Spring's `@Configurable` annotation uses LTW to inject dependencies into objects created with `new` (not managed by Spring).
- **Don't use** if Spring AOP proxies are sufficient — proxies cover most use cases (method interception on Spring-managed beans) without any JVM agent.
- **Don't confuse with compile-time weaving** — LTW wires aspects at load time; compile-time weaving wires them during `javac` (via AspectJ compiler).

## 3. Core concept

Java classloaders can be instrumented with `java.lang.instrument.ClassFileTransformer`. Spring's `InstrumentationLoadTimeWeaver` hooks into this mechanism via `java.lang.instrument.Instrumentation` (available only when a JVM agent is attached).

**LTW setup chain:**

1. JVM starts with `-javaagent:spring-instrument.jar` — this attaches `InstrumentationSavingAgent` which stores the `Instrumentation` instance.
2. `@EnableLoadTimeWeaving` / `<context:load-time-weaver/>` in Spring config — Spring detects the stored `Instrumentation` and creates an `InstrumentationLoadTimeWeaver`.
3. Any component implementing `LoadTimeWeaverAware` receives the weaver via `setLoadTimeWeaver(LoadTimeWeaver)`.
4. When a class is loaded, the JVM calls all registered `ClassFileTransformer`s — AspectJ's transformer matches join points and rewrites bytecode inline.

**`AspectJWeaving` modes on `@EnableLoadTimeWeaving`:**

| Mode | Behaviour |
|---|---|
| `AUTODETECT` | Enable if `META-INF/aop.xml` is on classpath |
| `ENABLED` | Always enable AspectJ weaving |
| `DISABLED` | Register weaver infrastructure but don't weave AspectJ aspects |

**Environment-specific implementations:**

| Environment | Implementation |
|---|---|
| Standard JVM with `-javaagent` | `InstrumentationLoadTimeWeaver` |
| Tomcat (special classloader) | `TomcatLoadTimeWeaver` |
| GlassFish / JBoss | Container-specific weaver |
| Tests (fallback) | `ReflectiveLoadTimeWeaver` (limited) |

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ltwa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- JVM startup -->
  <rect x="5" y="10" width="150" height="45" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="28" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM Startup</text>
  <text x="80" y="42" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">-javaagent:spring-instrument.jar</text>
  <text x="80" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">→ stores Instrumentation</text>

  <!-- Spring context -->
  <rect x="5" y="70" width="150" height="45" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="88" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif" font-weight="bold">@EnableLoadTimeWeaving</text>
  <text x="80" y="102" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">creates InstrumentationLTW</text>
  <text x="80" y="112" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">injects into LTW-Aware beans</text>
  <line x1="80" y1="57" x2="80" y2="68" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ltwa)"/>

  <!-- ClassTransformer -->
  <rect x="200" y="40" width="160" height="80" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="280" y="58" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif" font-weight="bold">ClassFileTransformer</text>
  <text x="280" y="72" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">AspectJ: match join points</text>
  <text x="280" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">JPA: bytecode enhancement</text>
  <text x="280" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Configurable injection</text>
  <text x="280" y="110" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">rewrites class bytes at load time</text>
  <line x1="157" y1="92" x2="198" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ltwa)"/>

  <!-- Classloader -->
  <rect x="415" y="40" width="140" height="80" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="485" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif" font-weight="bold">JVM Classloader</text>
  <text x="485" y="72" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">loads class bytes</text>
  <text x="485" y="85" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">→ calls each transformer</text>
  <text x="485" y="98" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">→ uses woven bytes</text>
  <line x1="362" y1="80" x2="412" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ltwa)"/>

  <!-- Result -->
  <rect x="570" y="55" width="125" height="50" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="632" y="73" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Loaded class has</text>
  <text x="632" y="85" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">aspect code woven in</text>
  <text x="632" y="97" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">(no source change needed)</text>
  <line x1="557" y1="80" x2="568" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ltwa)"/>

  <!-- aop.xml note -->
  <rect x="200" y="140" width="160" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="280" y="157" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">META-INF/aop.xml</text>
  <text x="280" y="169" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">declares which aspects to weave</text>
</svg>

The JVM agent captures `Instrumentation`; Spring registers `ClassFileTransformer`s on it; every loaded class runs through the transformer chain, receiving woven bytecode.

## 5. Runnable example

Scenario: **performance monitoring system** — an AspectJ aspect logs method execution times; LTW injects the advice without compile-time weaving or proxy limitations.

### Level 1 — Basic

`LoadTimeWeaverAware` interface — how a bean receives the weaver; infrastructure check.

```java
// LtwBasic.java
import org.springframework.context.annotation.*;
import org.springframework.instrument.classloading.*;

// Simulate what @EnableLoadTimeWeaving provides
@Configuration
class LtwConfig {
    @Bean
    LoadTimeWeaver loadTimeWeaver() {
        // ReflectiveLoadTimeWeaver works without -javaagent; limited to reflection-based instrumentation
        return new ReflectiveLoadTimeWeaver();
    }
}

// A component that receives the LTW (like JPA providers do)
@org.springframework.context.annotation.Component
class LtwAwareComponent implements org.springframework.context.weaving.LoadTimeWeaverAware {
    private LoadTimeWeaver weaver;

    @Override
    public void setLoadTimeWeaver(LoadTimeWeaver weaver) {
        this.weaver = weaver;
        System.out.println("[LTW] Received weaver: " + weaver.getClass().getSimpleName());
        System.out.println("[LTW] Instrumentation classloader: "
            + weaver.getInstrumentableClassLoader().getClass().getSimpleName());
        System.out.println("[LTW] Throwaway classloader type: "
            + weaver.getThrowawayClassLoader().getClass().getSimpleName());
    }

    public void describe() {
        System.out.println("[LTW] Active weaver: " + weaver);
    }
}

public class LtwBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LtwConfig.class);
        ctx.getBean(LtwAwareComponent.class).describe();
        ctx.close();
    }
}
```

How to run: `java LtwBasic.java`

`LoadTimeWeaverAware` is the Spring callback interface; Spring calls `setLoadTimeWeaver` after constructing the bean. `ReflectiveLoadTimeWeaver` works without a JVM agent and without classpath AspectJ — it provides the infrastructure without actual bytecode transformation. JPA providers (Hibernate's `HibernateJpaVendorAdapter`) call `setLoadTimeWeaver` on the `LocalContainerEntityManagerFactoryBean` to register class transformers.

### Level 2 — Intermediate

`InstrumentationLoadTimeWeaver` check and registering a custom `ClassFileTransformer`.

```java
// LtwIntermediate.java
import org.springframework.context.annotation.*;
import org.springframework.instrument.classloading.*;
import org.springframework.instrument.classloading.InstrumentationLoadTimeWeaver;
import java.lang.instrument.ClassFileTransformer;
import java.security.ProtectionDomain;

@Configuration
class LtwIntermConfig {
    @Bean
    LoadTimeWeaver loadTimeWeaver() {
        // In production: use InstrumentationLoadTimeWeaver (requires -javaagent)
        // Here: fall back to ReflectiveLoadTimeWeaver for demo
        if (InstrumentationLoadTimeWeaver.isInstrumentationAvailable()) {
            System.out.println("[Config] Using InstrumentationLoadTimeWeaver");
            return new InstrumentationLoadTimeWeaver();
        }
        System.out.println("[Config] Instrumentation not available; using ReflectiveLoadTimeWeaver");
        return new ReflectiveLoadTimeWeaver();
    }
}

// Custom transformer — logs every class being loaded
class LoggingClassTransformer implements ClassFileTransformer {
    @Override
    public byte[] transform(ClassLoader loader, String className,
                            Class<?> classBeingRedefined,
                            ProtectionDomain domain, byte[] classfileBuffer) {
        if (className != null && className.startsWith("com/example")) {
            System.out.println("[Transformer] Loading class: " + className.replace('/', '.'));
        }
        return null; // null = no transformation; return classfileBuffer to pass through unchanged
    }
}

@org.springframework.context.annotation.Component
class WeaveSetup implements org.springframework.context.weaving.LoadTimeWeaverAware {
    @Override
    public void setLoadTimeWeaver(LoadTimeWeaver ltw) {
        System.out.println("[WeaveSetup] Registering transformer on " + ltw.getClass().getSimpleName());
        ltw.addTransformer(new LoggingClassTransformer());
        System.out.println("[WeaveSetup] Transformer registered.");
    }
}

public class LtwIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LtwIntermConfig.class);
        System.out.println("Context started. Transformer is active.");
        ctx.close();
    }
}
```

How to run: `java LtwIntermediate.java` (without `-javaagent` → `ReflectiveLoadTimeWeaver`); add `-javaagent:spring-instrument.jar` to get `InstrumentationLoadTimeWeaver`.

`ltw.addTransformer(transformer)` registers the `ClassFileTransformer` on the JVM instrumentation. Transformers receive raw bytecode as a `byte[]`; returning `null` means "no change". Returning a modified `byte[]` replaces the class definition. The `InstrumentationLoadTimeWeaver.isInstrumentationAvailable()` static check lets you fall back gracefully.

### Level 3 — Advanced

Full `@EnableLoadTimeWeaving` + `META-INF/aop.xml` for AspectJ LTW with `@Aspect`.

```java
// LtwAdvanced.java
// Requires: spring-aspects.jar + aspectjweaver.jar on classpath
// Requires: -javaagent:spring-instrument.jar JVM arg
// Requires: META-INF/aop.xml (see below)
import org.springframework.context.annotation.*;
import org.springframework.context.weaving.*;

@Configuration
@EnableLoadTimeWeaving(aspectjWeaving = EnableLoadTimeWeaving.AspectJWeaving.AUTODETECT)
@ComponentScan
class LtwAdvancedConfig { }

// This @Aspect will be applied at load time — NOT via Spring proxy
// Works on ANY object, including those created with new Foo()
@org.aspectj.lang.annotation.Aspect
@org.springframework.stereotype.Component
class TimingAspect {
    @org.aspectj.lang.annotation.Around("execution(* com.example..*Service.*(..))")
    public Object time(org.aspectj.lang.ProceedingJoinPoint pjp) throws Throwable {
        long start = System.nanoTime();
        Object result = pjp.proceed();
        long ms = (System.nanoTime() - start) / 1_000_000;
        System.out.printf("[Timing] %s.%s took %d ms%n",
            pjp.getTarget().getClass().getSimpleName(),
            pjp.getSignature().getName(), ms);
        return result;
    }
}

@org.springframework.stereotype.Service
class ReportService {
    public String generate(String id) {
        // Simulated work
        return "Report[" + id + "]";
    }
}

// META-INF/aop.xml (must be on classpath):
// <aspectj>
//   <weaver options="-verbose">
//     <include within="com.example..*"/>
//   </weaver>
//   <aspects>
//     <aspect name="com.example.TimingAspect"/>
//   </aspects>
// </aspectj>

public class LtwAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LtwAdvancedConfig.class);
        var svc = ctx.getBean(ReportService.class);
        svc.generate("RPT-001");
        ctx.close();
    }
}
```

How to run: `java -javaagent:spring-instrument.jar LtwAdvanced.java` (with `spring-instrument.jar`, `spring-aspects.jar`, and `aspectjweaver.jar` on classpath).

`@EnableLoadTimeWeaving(aspectjWeaving=AUTODETECT)` — Spring checks for `META-INF/aop.xml`; if found, activates AspectJ LTW. `aop.xml` tells the AspectJ weaver which packages to instrument and which aspects to apply. The `TimingAspect` now applies to ALL `*Service` method calls, including objects not managed by Spring.

## 6. Walkthrough

Tracing `svc.generate("RPT-001")` with LTW active:

**Step 1 — At JVM startup:** `-javaagent:spring-instrument.jar` registers `InstrumentationSavingAgent`, which stores `java.lang.instrument.Instrumentation`.

**Step 2 — Spring context refresh:**
- `@EnableLoadTimeWeaving` creates `InstrumentationLoadTimeWeaver`.
- Registers AspectJ's `ClassPreProcessorAgentAdapter` (from `aspectjweaver.jar`) as a `ClassFileTransformer` via `ltw.addTransformer(...)`.
- AspectJ reads `META-INF/aop.xml` and compiles the aspect matching rules.

**Step 3 — `ReportService` class is loaded by JVM:**
- JVM calls each `ClassFileTransformer`.
- AspectJ transformer matches `execution(* *Service.*(..))`.
- Rewrites `ReportService.generate()` bytecode to include `around` advice (call `TimingAspect.time()`).
- Classloader installs the woven bytecode — `ReportService.class` in the JVM now has the advice inline.

**Step 4 — `svc.generate("RPT-001")` called:**
- No proxy — the woven bytecode calls `TimingAspect.time(pjp)` directly.
- `time()` records start time, calls `pjp.proceed()` (original `generate()`), measures elapsed, prints `[Timing] ReportService.generate took N ms`.

**Key difference from Spring AOP proxies:** LTW aspects apply at the bytecode level — `new ReportService()` (not Spring-managed) would ALSO be timed. Spring AOP proxies only intercept calls going through the Spring proxy wrapper.

## 7. Gotchas & takeaways

> **Without `-javaagent:spring-instrument.jar`, `InstrumentationLoadTimeWeaver` cannot register transformers.** The only way to add class transformers is through `Instrumentation`, which requires a JVM agent at startup. There is no runtime workaround. `ReflectiveLoadTimeWeaver` is a fallback but only supports transformers through special classloader APIs — it won't give you AspectJ weaving.

> **`@EnableLoadTimeWeaving` does NOT start weaving automatically.** It registers the infrastructure. Actual weaving requires either `META-INF/aop.xml` on the classpath (for AspectJ) or a JPA provider registering its `ClassTransformer` via `LoadTimeWeaverAware`.

- **Spring Boot:** Spring Boot applications do not need manual LTW setup for JPA — providers like Hibernate use `ByteBuddyProxies` or build-time enhancement. Only add LTW if you need full AspectJ `@Configurable` or call-site interception.
- **`@Configurable`:** enables dependency injection into objects created with `new` (e.g., JPA entities). Requires `@EnableLoadTimeWeaving` + `spring-aspects.jar`. Aspect `AnnotationBeanConfigurerAspect` injects `@Autowired` fields into the non-Spring-managed objects.
- **aop.xml `<include within="..."/>` scope:** be conservative — including all packages increases startup time because every loaded class is inspected. Match only the packages that actually use aspects.
- **Testing:** use `@SpringJUnitConfig` with `@EnableLoadTimeWeaving` + `spring-instrument.jar` on the test JVM agent classpath. Alternatively, use compile-time weaving (AspectJ compiler) for tests — faster and doesn't require agent.
