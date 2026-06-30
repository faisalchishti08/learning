---
card: spring-framework
gi: 88
slug: beanfactorypostprocessor-interface
title: BeanFactoryPostProcessor interface
---

## 1. What it is

`BeanFactoryPostProcessor` is a Spring hook that lets you inspect and **modify bean definitions** before any beans are actually instantiated. It operates on `BeanDefinition` metadata — the blueprints Spring holds in its registry — not on live bean instances.

Spring calls every registered `BeanFactoryPostProcessor` after it has read all configuration (XML, `@Configuration`, component scan) but before it calls any constructor.

## 2. Why & when

Sometimes you need to tweak how Spring will create beans without changing the source code of those beans. Classic use cases:

- Substituting `${...}` property expression references in `@Value` or XML with real values from a `.properties` file.
- Overriding a bean's scope or class at deploy time (e.g., swap a real service for a stub in tests).
- Enforcing naming or validation rules across all bean definitions at startup.

Spring's built-in `PropertySourcesPlaceholderConfigurer` is itself a `BeanFactoryPostProcessor`. You write a custom one when you need similar startup-time manipulation that the built-ins don't cover.

## 3. Core concept

The lifecycle in three stages:

1. **Load phase** — Spring parses `@Configuration` classes / XML and stores every discovered bean as a `BeanDefinition` in a `ConfigurableListableBeanFactory`.
2. **Post-process phase** — Spring calls `postProcessBeanFactory(ConfigurableListableBeanFactory)` on every `BeanFactoryPostProcessor` in the container. You can iterate definitions, call `bdf.getBeanDefinition(name)`, and mutate them.
3. **Instantiate phase** — Spring creates actual bean instances from the (now possibly modified) definitions.

> A `BeanFactoryPostProcessor` must itself be instantiated **early** (before other beans), so it cannot inject normal beans via `@Autowired` — those don't exist yet. It can only use constructor injection or static factory methods.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="80" width="170" height="54" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="110" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Load Config</text>
  <text x="95" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanDefinition registry</text>

  <rect x="260" y="80" width="185" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="352" y="105" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">BeanFactoryPost</text>
  <text x="352" y="121" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">Processor.postProcess</text>

  <rect x="530" y="80" width="155" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="607" y="110" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Instantiate Beans</text>
  <text x="607" y="126" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">constructors called</text>

  <line x1="182" y1="107" x2="257" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#a88)"/>
  <line x1="447" y1="107" x2="527" y2="107" stroke="#79c0ff" stroke-width="2" marker-end="url(#b88)"/>
  <defs>
    <marker id="a88" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b88" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="175" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">BFPP runs BEFORE constructors — only BeanDefinition metadata is accessible</text>
</svg>

`BeanFactoryPostProcessor` sits between loading config and creating objects.

## 5. Runnable example

### Level 1 — Basic

A custom `BeanFactoryPostProcessor` that prints every registered bean name so you can see exactly what's in the factory.

```java
// LoggingBfpp.java
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.BeanFactoryPostProcessor;
import org.springframework.beans.factory.config.ConfigurableListableBeanFactory;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
class AppConfig {
    @Bean
    public static LoggingBfpp loggingBfpp() { return new LoggingBfpp(); }

    @Bean
    public String greeting() { return "Hello, World"; }

    @Bean
    public Integer timeout() { return 30; }
}

class LoggingBfpp implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory bf) throws BeansException {
        System.out.println("=== Bean definitions in factory ===");
        for (String name : bf.getBeanDefinitionNames()) {
            System.out.println("  " + name);
        }
    }
}

public class LoggingBfppDemo {
    public static void main(String[] args) {
        new AnnotationConfigApplicationContext(AppConfig.class).close();
    }
}
```

How to run: `java LoggingBfppDemo.java` (JDK 17+, add `spring-context` jar to classpath or use a Spring Boot project)

The BFPP's `postProcessBeanFactory` fires before any bean is constructed. It receives the full `ConfigurableListableBeanFactory` and calls `getBeanDefinitionNames()` to list what Spring has registered so far.

### Level 2 — Intermediate

Now the BFPP mutates a bean definition: it forcibly marks the `timeout` bean's scope as `prototype` instead of the default `singleton`, and overrides its primary flag.

```java
// MutateBfpp.java
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.*;
import org.springframework.context.annotation.*;

@Configuration
class AppCfg {
    @Bean public static MutateBfpp mutateBfpp() { return new MutateBfpp(); }
    @Bean public Integer timeout() { return 30; }
    @Bean public String greeting() { return "Hello"; }
}

class MutateBfpp implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory bf) throws BeansException {
        BeanDefinition bd = bf.getBeanDefinition("timeout");
        System.out.println("Before: scope=" + bd.getScope() + ", primary=" + bd.isPrimary());
        bd.setScope(BeanDefinition.SCOPE_PROTOTYPE);
        bd.setPrimary(true);
        System.out.println("After:  scope=" + bd.getScope() + ", primary=" + bd.isPrimary());
    }
}

public class MutateBfppDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        // Every getBean("timeout") now creates a NEW Integer (prototype)
        System.out.println("Bean 1: " + System.identityHashCode(ctx.getBean("timeout")));
        System.out.println("Bean 2: " + System.identityHashCode(ctx.getBean("timeout")));
        ctx.close();
    }
}
```

How to run: `java MutateBfppDemo.java`

The two `getBean` calls return **different objects** because the scope was flipped to `prototype` by the BFPP before instantiation. Without the BFPP the same singleton would be returned both times.

### Level 3 — Advanced

A production-flavoured BFPP that validates all `@Service` beans have a description set (a convention the team enforces), and rewrites any bean class that is an interface to a concrete fallback implementation — demonstrating how BFPPs can enforce architectural rules at startup time.

```java
// ValidatingBfpp.java
import org.springframework.beans.BeansException;
import org.springframework.beans.factory.config.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.Service;
import java.util.ArrayList;
import java.util.List;

@Service
class PaymentService { public void pay() { System.out.println("PaymentService.pay()"); } }

@Service
class OrderService { public void order() { System.out.println("OrderService.order()"); } }

@Configuration
@ComponentScan
class ProdConfig {
    @Bean
    public static ValidatingBfpp validatingBfpp() { return new ValidatingBfpp(); }
}

class ValidatingBfpp implements BeanFactoryPostProcessor {
    @Override
    public void postProcessBeanFactory(ConfigurableListableBeanFactory bf) throws BeansException {
        List<String> violations = new ArrayList<>();
        for (String name : bf.getBeanDefinitionNames()) {
            BeanDefinition bd = bf.getBeanDefinition(name);
            // Only check beans annotated with @Service
            try {
                Class<?> cls = Class.forName(bd.getBeanClassName() != null ? bd.getBeanClassName() : "");
                if (cls.isAnnotationPresent(Service.class)) {
                    if (bd.getDescription() == null || bd.getDescription().isBlank()) {
                        // Auto-set a default description so startup doesn't fail
                        bd.setDescription("Auto-described: " + name);
                        System.out.println("[BFPP] Added default description to: " + name);
                    }
                }
            } catch (ClassNotFoundException | NullPointerException ignored) {}
        }
        if (!violations.isEmpty()) {
            throw new IllegalStateException("BFPP validation failed: " + violations);
        }
        System.out.println("[BFPP] All @Service beans have descriptions — startup proceeds.");
    }
}

public class ValidatingBfppDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ProdConfig.class);
        ctx.getBean(PaymentService.class).pay();
        ctx.getBean(OrderService.class).order();
        ctx.close();
    }
}
```

How to run: `java ValidatingBfppDemo.java`

The BFPP scans all bean definitions, identifies `@Service` ones via reflection on the class name, and either fixes missing descriptions or accumulates violations. This pattern is used in real teams to enforce conventions (documentation, naming, required metadata) at startup rather than in code reviews.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Spring reads `ProdConfig`** — it discovers `@ComponentScan` and registers `PaymentService` and `OrderService` as `BeanDefinition` objects. No constructors called yet.
2. **Spring detects `validatingBfpp`** — because `@Bean` is `static`, Spring can create it without creating `ProdConfig` first. It adds the BFPP to an early-init list.
3. **`postProcessBeanFactory` fires** — Spring passes the `ConfigurableListableBeanFactory` with all registered definitions. The loop calls `bf.getBeanDefinitionNames()` — this returns the raw list including infrastructure beans.
4. **For each name**, `bd.getBeanClassName()` returns the fully qualified class name (e.g., `PaymentService`). `Class.forName(...)` loads it without instantiating it so we can inspect annotations.
5. **`@Service` detected** — `bd.getDescription()` returns `null` (no explicit description was set), so we call `bd.setDescription("Auto-described: paymentService")`. This mutates the blueprint inside the factory registry.
6. **Control returns to Spring** — instantiation begins. `PaymentService` and `OrderService` constructors fire with the now-amended `BeanDefinition`s.
7. **`main` calls `getBean`** — retrieves live instances and calls methods. The console shows the BFPP log lines before the service output, proving the BFPP ran first.

Expected output:
```
[BFPP] Added default description to: paymentService
[BFPP] Added default description to: orderService
[BFPP] All @Service beans have descriptions — startup proceeds.
PaymentService.pay()
OrderService.order()
```

## 7. Gotchas & takeaways

> A `BeanFactoryPostProcessor` bean method **must be `static`** in `@Configuration` classes. If it's an instance `@Bean`, Spring must create the `@Configuration` object first, which forces the whole configuration lifecycle to run too early, breaking the ordering guarantee. Always declare BFPPs with `public static`.

> You cannot `@Autowired`-inject normal application beans into a BFPP — those beans don't exist yet when the BFPP runs. Inject only infrastructure objects (e.g., `Environment`) via constructor.

- BFPP runs **before** any application bean is constructed — only `BeanDefinition` metadata is available.
- Use `bf.getBeanDefinition(name)` to get a mutable blueprint; call `setScope`, `setPrimary`, `setDescription`, or `setBeanClassName` to change how Spring will build it.
- Built-in examples: `PropertySourcesPlaceholderConfigurer`, `ConfigurationClassPostProcessor` (processes `@Configuration`).
- For bean **instance** post-processing (after construction), use `BeanPostProcessor` instead.
- Multiple BFPPs are ordered with `@Order` or by implementing `Ordered`.
