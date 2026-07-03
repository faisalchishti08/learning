---
card: spring-framework
gi: 117
slug: bean-description-description
title: "Bean description (@Description)"
---

## 1. What it is

`@Description` is a Spring annotation that attaches a human-readable string to a `BeanDefinition`. It is the `@Bean` / component equivalent of a Javadoc comment — except it is available at runtime through `BeanDefinition.getDescription()` and surfaced in management tooling (JMX MBeans, Actuator `/beans` endpoint).

```java
@Bean
@Description("Primary DataSource backed by HikariCP; poolSize=20; failover to replica on timeout")
public DataSource primaryDataSource() { ... }
```

## 2. Why & when

Use `@Description` for beans that appear in operational dashboards or JMX consoles where a textual description aids operators:

- Infrastructure beans (data sources, caches, thread pools) that show up in Spring Boot Actuator's `/actuator/beans` output.
- Library beans that need to document their purpose for downstream teams.
- Any bean whose role is not obvious from its type name — operations teams reading JMX should understand what each bean does.

In tests, querying `BeanDefinition.getDescription()` is a lightweight way to assert that the expected bean is registered with the right metadata.

## 3. Core concept

`@Description` lives in `org.springframework.context.annotation`. It has a single attribute `value` — the description string.

Where it works:

- On a `@Bean` method (most common).
- On a `@Component`-annotated class (including `@Service`, `@Repository`, etc.).
- On a `@Configuration` class itself.

How the description propagates:

1. `ConfigurationClassPostProcessor` (for `@Bean` methods) or `ClassPathBeanDefinitionScanner` (for component-scanned classes) reads `@Description` via the annotation metadata.
2. The string is stored in `AbstractBeanDefinition.description`.
3. Spring Boot Actuator's `BeansEndpoint` includes descriptions in its JSON output for each bean.
4. JMX exposure via `MBeanExporter` surfaced through `BeanDefinition.getDescription()`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Annotation -->
  <rect x="10" y="55" width="205" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="112" y="78" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Description("...")</text>
  <text x="112" y="96" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">on @Bean method</text>
  <text x="112" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">or @Component class</text>
  <text x="112" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">value = "human-readable text"</text>

  <!-- Arrow -->
  <line x1="217" y1="95" x2="300" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#a117)"/>
  <defs>
    <marker id="a117" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b117" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- BeanDefinition -->
  <rect x="302" y="55" width="190" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="397" y="78" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">BeanDefinition</text>
  <text x="397" y="96" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">description = "..."</text>
  <text x="397" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">getDescription() → string</text>

  <!-- Arrow -->
  <line x1="494" y1="95" x2="575" y2="95" stroke="#79c0ff" stroke-width="2" marker-end="url(#b117)"/>

  <!-- Consumers -->
  <rect x="577" y="40" width="115" height="115" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="634" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Actuator</text>
  <text x="634" y="82" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">/actuator/beans</text>
  <text x="634" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JMX</text>
  <text x="634" y="122" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">MBean description</text>
  <text x="634" y="145" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Tests</text>

  <text x="350" y="172" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Description string flows from annotation → BeanDefinition → management tooling</text>
</svg>

`@Description` stores a string in the `BeanDefinition`; Actuator, JMX, and tests read it at runtime.

## 5. Runnable example

### Level 1 — Basic

Apply `@Description` to a `@Bean` method and read it back from the `BeanDefinition`.

```java
// DescriptionBasic.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;

class PaymentGateway {
    public String charge(double amount) {
        return "Charged $" + amount + " via gateway";
    }
}

@Configuration
class DescCfg {
    @Bean
    @Description("Stripe payment gateway integration; retry 3x on timeout; production credentials from vault")
    public PaymentGateway paymentGateway() {
        return new PaymentGateway();
    }
}

public class DescriptionBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DescCfg.class);

        var factory = (DefaultListableBeanFactory) ctx.getBeanFactory();
        var bd = factory.getBeanDefinition("paymentGateway");
        System.out.println("Bean description:");
        System.out.println("  " + bd.getDescription());

        // Use the bean
        System.out.println(ctx.getBean(PaymentGateway.class).charge(99.99));
        ctx.close();
    }
}
```

How to run: `java DescriptionBasic.java`

`bd.getDescription()` returns the exact string from `@Description`. The bean itself works normally — the description is purely informational metadata on the definition.

### Level 2 — Intermediate

`@Description` on component-scanned classes, and listing descriptions for all registered beans.

```java
// DescriptionComponents.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service
@Description("User account CRUD — delegates to JPA repository; enforces uniqueness constraint")
class UserAccountService {
    public String create(String name) { return "created:" + name; }
}

@Repository
@Description("In-memory order store; not persistent; for unit-testing only")
class OrderRepository {
    public String find(int id) { return "order#" + id; }
}

@Component
// No @Description — description will be null
class HealthChecker {
    public boolean check() { return true; }
}

@Configuration
@ComponentScan(basePackageClasses = DescriptionComponents.class)
class CompDescCfg {}

public class DescriptionComponents {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CompDescCfg.class);
        var factory = (DefaultListableBeanFactory) ctx.getBeanFactory();

        System.out.println("=== Bean descriptions ===");
        for (String name : ctx.getBeanDefinitionNames()) {
            var bd = factory.getBeanDefinition(name);
            if (bd.getDescription() != null) {
                System.out.println("[" + name + "] " + bd.getDescription());
            }
        }

        System.out.println("\n=== No description ===");
        var hcBd = factory.getBeanDefinition("healthChecker");
        System.out.println("healthChecker.description: " + hcBd.getDescription());
        ctx.close();
    }
}
```

How to run: `java DescriptionComponents.java`

Component-scanned beans with `@Description` show their descriptions; `healthChecker` without `@Description` returns `null` for `getDescription()`.

### Level 3 — Advanced

A diagnostic utility that aggregates all described beans and outputs a formatted bean manifest — simulating what Actuator does internally.

```java
// DescriptionManifest.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

// Infrastructure beans with descriptions
@Configuration
class InfraConfig {
    @Bean
    @Description("HikariCP connection pool; 20 connections; timeout 30s; auto-reconnect")
    public String dataSource() { return "HikariDataSource[size=20]"; }

    @Bean
    @Description("Redis cache layer; TTL=300s; cluster mode; serialization=JSON")
    public String cacheManager() { return "RedissonCacheManager"; }

    @Bean
    @Description("Async task executor; corePool=5; maxPool=20; queue=100; keepAlive=60s")
    public String taskExecutor() { return "ThreadPoolTaskExecutor[core=5,max=20]"; }
}

@Service
@Description("Order processing pipeline; validates → reserves inventory → charges → fulfills")
class OrderPipeline {
    public String process(int id) { return "Processed order " + id; }
}

@Service
// No description — internal implementation detail
class InternalEventBus {
    public void publish(String event) {}
}

@Configuration
@ComponentScan(basePackageClasses = DescriptionManifest.class)
@Import(InfraConfig.class)
class ManifestCfg {}

public class DescriptionManifest {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ManifestCfg.class);
        var factory = (DefaultListableBeanFactory) ctx.getBeanFactory();

        // Build manifest: name → description for all described beans
        var manifest = new TreeMap<String, String>();
        for (String name : ctx.getBeanDefinitionNames()) {
            var bd = factory.getBeanDefinition(name);
            if (bd.getDescription() != null && !bd.getDescription().isBlank()) {
                manifest.put(name, bd.getDescription());
            }
        }

        System.out.println("=== Bean Manifest ===");
        System.out.printf("%-20s  %s%n", "Bean Name", "Description");
        System.out.println("-".repeat(80));
        manifest.forEach((name, desc) ->
            System.out.printf("%-20s  %s%n", name, desc));

        System.out.println("\nTotal described beans: " + manifest.size());
        System.out.println("Total registered beans: " + ctx.getBeanDefinitionCount());

        // Use one of the beans
        System.out.println("\n" + ctx.getBean(OrderPipeline.class).process(42));
        ctx.close();
    }
}
```

How to run: `java DescriptionManifest.java`

The manifest shows all beans with descriptions sorted alphabetically. Infrastructure beans and `OrderPipeline` appear; `InternalEventBus` (no description) and Spring internals do not.

## 6. Walkthrough

Execution order for Level 3:

1. **`AnnotationConfigApplicationContext(ManifestCfg.class)` created** — `@Import(InfraConfig.class)` adds `InfraConfig` to the processing set. `@ComponentScan` discovers `OrderPipeline` and `InternalEventBus`.
2. **`ConfigurationClassPostProcessor` processes `InfraConfig`** — reads `@Description` from each `@Bean` method and stores it in the `AbstractBeanDefinition.description` field.
3. **Component scanner processes `OrderPipeline`** — reads `@Description` from class-level annotation and stores it in the `ScannedGenericBeanDefinition`.
4. **`InternalEventBus`** — no `@Description`, so `bd.getDescription() == null`.
5. **Manifest built** — iterates all definition names, selects those with non-null descriptions, sorts into `TreeMap`.
6. **Table printed** — shows `cacheManager`, `dataSource`, `orderPipeline`, `taskExecutor` with their descriptions.
7. **`OrderPipeline.process(42)`** → `"Processed order 42"`.

Expected output (abbreviated):
```
=== Bean Manifest ===
Bean Name             Description
--------------------------------------------------------------------------------
cacheManager          Redis cache layer; TTL=300s; cluster mode; serialization=JSON
dataSource            HikariCP connection pool; 20 connections; timeout 30s; auto-reconnect
orderPipeline         Order processing pipeline; validates → reserves...
taskExecutor          Async task executor; corePool=5; maxPool=20...

Total described beans: 4
Total registered beans: 9

Processed order 42
```

## 7. Gotchas & takeaways

> `@Description` is **not inherited** — if a subclass of a `@Service` class extends it without repeating `@Description`, the subclass bean has no description. The annotation lives on the declaring class or method, not propagated through hierarchy.

> The description has no effect on bean wiring, scope, lifecycle, or proxy behavior. It is purely informational metadata. Changing or removing it never changes runtime behavior.

- For `@Bean` methods, `@Description` must be on the method, not the class — one per method.
- For component-scanned beans, `@Description` goes on the class.
- Spring Boot Actuator exposes descriptions in `/actuator/beans` → `"beans"` → `"<beanName>"` → `"description"` (when non-null).
- In JMX via `AnnotationMBeanExporter`, bean descriptions appear in JConsole's MBean description field.
- Use it as lightweight runbook-in-code: include the SLA, failover policy, and config parameters that ops teams need — it shows up in Actuator without any extra tooling.
