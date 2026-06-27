---
card: spring-boot
gi: 36
slug: enableautoconfiguration
title: "@EnableAutoConfiguration"
---

## 1. What it is

`@EnableAutoConfiguration` is the Spring Boot annotation that tells the framework to automatically configure the Spring application context based on the JARs on the classpath. If `spring-webmvc` is on the classpath, Spring Boot assumes you are building a web app and configures a `DispatcherServlet`; if `spring-data-jpa` is there, it configures a `JPA EntityManagerFactory` — all without a single explicit bean definition.

In practice you almost never write `@EnableAutoConfiguration` directly. `@SpringBootApplication` is a composed annotation that includes it:

```java
@SpringBootApplication   // shorthand for @Configuration + @ComponentScan + @EnableAutoConfiguration
public class MyApp {
    public static void main(String[] args) {
        SpringApplication.run(MyApp.class, args);
    }
}
```

## 2. Why & when

Before Spring Boot you configured every bean by hand: `DataSource`, `EntityManagerFactory`, `TransactionManager`, `DispatcherServlet`, `ViewResolver`, and dozens more. A typical enterprise Spring project had thousands of lines of XML or Java config doing nothing interesting — just plumbing.

`@EnableAutoConfiguration` exists to eliminate that boilerplate by codifying community best-practice defaults into reusable auto-configuration classes. You get a working stack by adding JARs, not by writing configuration.

Use it (via `@SpringBootApplication`) on every Spring Boot main class. Override individual parts with your own `@Bean` definitions wherever you disagree with the default.

## 3. Core concept

Think of auto-configuration as a smart assistant who checks what tools you brought to the workshop and sets up a sensible workbench. If you brought a welding torch, the assistant lays out welding gear; if you brought paintbrushes, it lays out paint. You can rearrange anything afterwards, but the default layout is sensible for the tools you own.

The mechanism:

1. `@EnableAutoConfiguration` activates a special `AutoConfigurationImportSelector`.
2. That selector reads `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports` (Spring Boot 2.7+) from every JAR on the classpath.
3. Each listed class is a `@Configuration` class with `@Conditional` guards.
4. Spring evaluates each guard: if the condition passes (e.g. the class `DataSource` exists on the classpath), the configuration is applied; if not, it is skipped.
5. Auto-configurations run **after** user `@Configuration` classes, so your beans always take precedence.

## 4. Diagram

<svg viewBox="0 0 660 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@EnableAutoConfiguration reading AutoConfiguration.imports and conditionally applying configs">
  <!-- Left: annotation -->
  <rect x="20" y="90" width="190" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="115" y="116" fill="#6db33f" font-size="12" font-family="monospace" text-anchor="middle">@SpringBootApp</text>
  <text x="115" y="136" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">↳ @EnableAutoConfig</text>

  <!-- Selector -->
  <rect x="240" y="90" width="180" height="60" rx="8" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="116" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">AutoConfiguration</text>
  <text x="330" y="134" fill="#79c0ff" font-size="11" font-family="monospace" text-anchor="middle">ImportSelector</text>

  <!-- Imports file -->
  <rect x="450" y="30" width="190" height="50" rx="6" fill="#1a2332" stroke="#8b949e" stroke-width="1"/>
  <text x="545" y="52" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">META-INF/spring/</text>
  <text x="545" y="68" fill="#8b949e" font-size="10" font-family="monospace" text-anchor="middle">AutoConfiguration.imports</text>

  <!-- Conditional configs -->
  <rect x="450" y="100" width="190" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="545" y="125" fill="#6db33f" font-size="11" font-family="monospace" text-anchor="middle">DataSourceAutoConfig ✅</text>

  <rect x="450" y="150" width="190" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="545" y="175" fill="#8b949e" font-size="11" font-family="monospace" text-anchor="middle">MongoAutoConfig ❌ skip</text>

  <!-- Bean pool -->
  <rect x="450" y="205" width="190" height="40" rx="6" fill="#16202e" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="230" fill="#e6edf3" font-size="11" font-family="monospace" text-anchor="middle">dataSource bean → context</text>

  <!-- Arrows -->
  <line x1="210" y1="120" x2="238" y2="120" stroke="#6db33f" stroke-width="2" marker-end="url(#e1)"/>
  <line x1="420" y1="110" x2="448" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#e1)"/>
  <line x1="420" y1="55" x2="448" y2="55" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="4,3"/>
  <line x1="545" y1="80" x2="545" y2="98" stroke="#8b949e" stroke-width="1.2" marker-end="url(#e1)"/>
  <line x1="545" y1="140" x2="545" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#e1)"/>
  <line x1="545" y1="190" x2="545" y2="203" stroke="#6db33f" stroke-width="1.5" marker-end="url(#e1)"/>

  <defs>
    <marker id="e1" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

`@EnableAutoConfiguration` triggers the selector, which reads the imports file and conditionally applies only the configurations whose classpath conditions pass.

## 5. Runnable example

```java
// EnableAutoConfigDemo.java
// How to run: java EnableAutoConfigDemo.java  (JDK 17+)
// Simulates how @EnableAutoConfiguration decides which configs to apply
// by checking classpath conditions — no Spring on classpath needed.

import java.util.*;

public class EnableAutoConfigDemo {

    // Simulated "classpath" — JARs present in this hypothetical app
    static final Set<String> CLASSPATH = Set.of(
        "spring-webmvc",
        "spring-data-jpa",
        "HikariCP"
        // note: "spring-data-mongodb" is NOT present
    );

    record AutoConfig(String name, String requiredClass, String beanCreated) {}

    public static void main(String[] args) {
        // META-INF/spring/AutoConfiguration.imports (simulated)
        List<AutoConfig> candidates = List.of(
            new AutoConfig("DataSourceAutoConfiguration",
                "HikariCP",            "dataSource (HikariDataSource)"),
            new AutoConfig("JpaRepositoriesAutoConfiguration",
                "spring-data-jpa",     "entityManagerFactory, transactionManager"),
            new AutoConfig("DispatcherServletAutoConfiguration",
                "spring-webmvc",       "dispatcherServlet"),
            new AutoConfig("MongoAutoConfiguration",
                "spring-data-mongodb", "mongoClient")   // NOT on classpath → skipped
        );

        System.out.println("=== @EnableAutoConfiguration simulation ===");
        System.out.println("Classpath: " + CLASSPATH);
        System.out.println();

        List<String> registeredBeans = new ArrayList<>();

        for (AutoConfig cfg : candidates) {
            boolean conditionPasses = CLASSPATH.contains(cfg.requiredClass());
            if (conditionPasses) {
                registeredBeans.add(cfg.beanCreated());
                System.out.println("✅ APPLIED  " + cfg.name());
                System.out.println("   → registered: " + cfg.beanCreated());
            } else {
                System.out.println("❌ SKIPPED  " + cfg.name()
                    + " ('" + cfg.requiredClass() + "' not on classpath)");
            }
        }

        System.out.println("\n=== Auto-configured beans in context ===");
        registeredBeans.forEach(b -> System.out.println("  " + b));
    }
}
```

**How to run:** `java EnableAutoConfigDemo.java`

Expected output:
```
=== @EnableAutoConfiguration simulation ===
Classpath: [HikariCP, spring-webmvc, spring-data-jpa]

✅ APPLIED  DataSourceAutoConfiguration
   → registered: dataSource (HikariDataSource)
✅ APPLIED  JpaRepositoriesAutoConfiguration
   → registered: entityManagerFactory, transactionManager
✅ APPLIED  DispatcherServletAutoConfiguration
   → registered: dispatcherServlet
❌ SKIPPED  MongoAutoConfiguration ('spring-data-mongodb' not on classpath)

=== Auto-configured beans in context ===
  dataSource (HikariDataSource)
  entityManagerFactory, transactionManager
  dispatcherServlet
```

## 6. Walkthrough

- `CLASSPATH` represents the JARs present; real Spring Boot inspects actual class presence via `ClassUtils.isPresent(...)`.
- Each `AutoConfig` record maps to a real auto-configuration class that lives in `spring-boot-autoconfigure.jar`.
- The `conditionPasses` check simulates `@ConditionalOnClass`; if the required class is missing, the entire configuration is skipped — silently.
- `MongoAutoConfiguration` is skipped because `spring-data-mongodb` is not in the simulated classpath — exactly how it works in a project without the Mongo starter.
- `registeredBeans` collects what ends up in the context. In a real app these beans are available for `@Autowired` injection as soon as the context is refreshed.
- Auto-configurations run **after** user config; if you define your own `DataSource` bean, `DataSourceAutoConfiguration` backs off via `@ConditionalOnMissingBean(DataSource.class)`.

## 7. Gotchas & takeaways

> Adding a starter JAR to your `pom.xml` / `build.gradle` but forgetting to check which auto-configurations it activates can result in unwanted beans being registered — a common cause of "unexpected bean already in context" errors when two starters configure the same thing.

> `@EnableAutoConfiguration` must be on a class in a **root package** (or have correct base package set) so it processes after user beans. If your main class is in a sub-package and component scanning misses it, auto-configuration may apply before your overrides are known.

- `@SpringBootApplication` = `@Configuration` + `@ComponentScan` + `@EnableAutoConfiguration` — use the composite form.
- Auto-configuration is driven by classpath presence; remove a JAR to disable its auto-configuration.
- Use `spring.autoconfigure.exclude` in `application.properties` or the `exclude` attribute of `@EnableAutoConfiguration` to opt out of specific auto-configs.
- Run with `--debug` to see the condition evaluation report (which configs applied and why).
- User `@Bean` definitions always win over auto-configured ones thanks to `@ConditionalOnMissingBean`.
