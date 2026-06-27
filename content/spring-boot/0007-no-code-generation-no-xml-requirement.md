---
card: spring-boot
gi: 7
slug: no-code-generation-no-xml-requirement
title: No code generation & no XML requirement
---

## 1. What it is

Spring Boot applications require **no XML configuration files** and produce **no generated source code**. Everything is expressed in plain Java using annotations, and the framework wires the pieces together at runtime through reflection and auto-configuration — not at build time through code generators.

This stands in contrast to:
- **Spring legacy approach** — required `applicationContext.xml`, `web.xml`, `spring-security.xml`, `persistence.xml`, etc.
- **Jakarta EE / J2EE** — required deployment descriptors and often vendor-specific XML.
- **Code-generation frameworks (e.g., older MyBatis generators, jOOQ codegen)** — generate `.java` files that you commit to source control.

With Spring Boot: one `@SpringBootApplication` annotation, standard Java, and `application.properties`. That's the entire configuration surface.

## 2. Why & when

**XML configuration problems:**
- Not type-safe — typos in `<bean id="myService">` cause runtime failures, not compile errors.
- Not IDE-friendly — refactoring a class name means hunting XML files for string references that the IDE won't update.
- Not readable — a 500-line XML file describing bean wiring is harder to understand than 50 lines of `@Configuration` Java.
- Not refactorable — moving a class breaks XML references silently.

**Code generation problems:**
- Generated files pollute version control with noise.
- Re-generation overwrites hand edits.
- Build pipelines become fragile (generate step must happen before compile step).

"No XML, no code generation" means: **the source of truth is your Java source code**, in exactly the files you see in your editor. The IDE can navigate it, refactor it, and check it at compile time.

## 3. Core concept

Spring Boot's approach is **annotation-driven configuration**:

| Old XML way | Modern Spring Boot way |
|---|---|
| `<bean id="orderService" class="com.example.OrderServiceImpl"/>` | `@Service class OrderServiceImpl {}` |
| `<context:component-scan base-package="com.example"/>` | `@SpringBootApplication` (includes `@ComponentScan`) |
| `<tx:annotation-driven/>` | `@EnableTransactionManagement` (included via auto-config) |
| `<bean id="dataSource" class="...DriverManagerDataSource">` | `spring.datasource.url=jdbc:...` in `application.properties` |
| `<import resource="security-config.xml"/>` | `@Configuration class SecurityConfig {}` |

The mechanism:
1. `@Component`, `@Service`, `@Repository`, `@Controller` — mark classes for automatic detection and bean registration.
2. `@Autowired` / constructor injection — expresses dependencies in Java; the IDE tracks them.
3. `@Configuration` + `@Bean` — explicit bean factories in Java instead of XML `<bean>` tags.
4. `application.properties` / `.yml` — externalised string/number/boolean settings only; no structure or wiring.

No reflection on XML; no apt/annotation processor generating `.java` files; just your code running.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side comparison of XML-heavy Spring config vs annotation-driven Spring Boot config">
  <!-- Left: XML era -->
  <rect x="20" y="20" width="300" height="200" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="170" y="46" fill="#8b949e" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring (XML era)</text>

  <rect x="36" y="56" width="268" height="148" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="52" y="76" fill="#8b949e" font-size="10" font-family="monospace">&lt;?xml version="1.0"?&gt;</text>
  <text x="52" y="92" fill="#8b949e" font-size="10" font-family="monospace">&lt;beans xmlns="..."&gt;</text>
  <text x="52" y="108" fill="#8b949e" font-size="10" font-family="monospace">  &lt;bean id="ds"</text>
  <text x="52" y="124" fill="#8b949e" font-size="10" font-family="monospace">    class="Hikari..."&gt;</text>
  <text x="52" y="140" fill="#8b949e" font-size="10" font-family="monospace">    &lt;property name="url"</text>
  <text x="52" y="156" fill="#8b949e" font-size="10" font-family="monospace">      value="${db.url}"/&gt;</text>
  <text x="52" y="172" fill="#8b949e" font-size="10" font-family="monospace">  &lt;/bean&gt;</text>
  <text x="52" y="188" fill="#8b949e" font-size="10" font-family="monospace">&lt;/beans&gt;</text>

  <!-- Right: Spring Boot -->
  <rect x="360" y="20" width="300" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="46" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot (annotation)</text>

  <rect x="376" y="56" width="268" height="148" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="392" y="76" fill="#6db33f" font-size="10" font-family="monospace">// application.properties</text>
  <text x="392" y="92" fill="#e6edf3" font-size="10" font-family="monospace">spring.datasource.url=jdbc:...</text>
  <text x="392" y="116" fill="#6db33f" font-size="10" font-family="monospace">// Java — type-safe, IDE-navigable</text>
  <text x="392" y="132" fill="#79c0ff" font-size="10" font-family="monospace">@SpringBootApplication</text>
  <text x="392" y="148" fill="#e6edf3" font-size="10" font-family="monospace">public class App {</text>
  <text x="392" y="164" fill="#e6edf3" font-size="10" font-family="monospace">  public static void main(...) {</text>
  <text x="392" y="180" fill="#e6edf3" font-size="10" font-family="monospace">    SpringApplication.run(...);</text>
  <text x="392" y="196" fill="#e6edf3" font-size="10" font-family="monospace">  }</text>
</svg>

XML wires beans in strings the compiler can't check; Spring Boot wires them in Java the compiler and IDE both understand.

## 5. Runnable example

```java
// File: NoXmlDemo.java
// Shows annotation-driven wiring vs XML-style manual wiring — all pure Java.
// Run: java NoXmlDemo.java

import java.lang.annotation.*;
import java.util.*;

public class NoXmlDemo {

    // ---- Simulate @Service annotation ----
    @Retention(RetentionPolicy.RUNTIME)
    @interface Service {}

    // ---- Simulate @Autowired constructor injection ----
    @Retention(RetentionPolicy.RUNTIME)
    @interface Autowired {}

    // ---- Business classes (like real Spring components) ----
    @Service
    static class UserRepository {
        List<String> findAll() {
            return List.of("Alice", "Bob", "Carol");
        }
    }

    @Service
    static class UserService {
        private final UserRepository repo;

        @Autowired
        UserService(UserRepository repo) {      // dependency declared in Java, not XML
            this.repo = repo;
        }

        List<String> listUsers() {
            return repo.findAll();
        }
    }

    // ---- Minimal "container" that wires by annotation (no XML) ----
    static class AnnotationContainer {
        private final Map<Class<?>, Object> beans = new HashMap<>();

        <T> void register(Class<T> type, T instance) {
            beans.put(type, instance);
            System.out.println("[Container] Registered: " + type.getSimpleName());
        }

        @SuppressWarnings("unchecked")
        <T> T get(Class<T> type) {
            return (T) beans.get(type);
        }
    }

    public static void main(String[] args) throws Exception {
        System.out.println("=== No XML — wiring via Java ===\n");

        var container = new AnnotationContainer();

        // Auto-detect @Service classes and wire constructor dependencies
        var repo    = new UserRepository();
        var service = new UserService(repo);   // inject via constructor — type-safe

        container.register(UserRepository.class, repo);
        container.register(UserService.class, service);

        System.out.println();
        System.out.println("=== Using wired service ===");
        var users = container.get(UserService.class).listUsers();
        users.forEach(u -> System.out.println("  - " + u));

        System.out.println();
        System.out.println("Refactor UserRepository → rename to UserRepo?");
        System.out.println("  Java: IDE updates all references. 0 runtime surprises.");
        System.out.println("  XML:  Rename class, forget XML string → NullPointerException at startup.");
    }
}
```

**How to run:** `java NoXmlDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== No XML — wiring via Java ===

[Container] Registered: UserRepository
[Container] Registered: UserService

=== Using wired service ===
  - Alice
  - Bob
  - Carol

Refactor UserRepository → rename to UserRepo?
  Java: IDE updates all references. 0 runtime surprises.
  XML:  Rename class, forget XML string → NullPointerException at startup.
```

## 6. Walkthrough

- **`@Service` and `@Autowired` custom annotations** — we simulate Spring's own. In production Spring Boot, these are the real annotations from `org.springframework.stereotype` and `org.springframework.beans.factory.annotation`.
- **Constructor injection in `UserService`** — the dependency on `UserRepository` is declared as a constructor parameter. Java enforces it at compile time; if you forget to provide one, the code won't compile. XML `<ref bean="userRepository"/>` gives a runtime `BeanCreationException` instead.
- **`AnnotationContainer.register`** — mimics Spring's `ApplicationContext`. Real Spring finds `@Service` classes through classpath scanning triggered by `@ComponentScan` (included in `@SpringBootApplication`), then uses reflection to detect `@Autowired` constructors and satisfy them.
- **Refactoring comment** — this is the core practical benefit: type references are first-class Java. IDE rename refactoring works across the entire codebase. No XML files holding string references that become stale.

## 7. Gotchas & takeaways

> **You can still use XML if you need to.** Spring Boot doesn't forbid XML; it just doesn't require it. Legacy apps migrating to Spring Boot can use `@ImportResource("classpath:legacy-beans.xml")` to incrementally move XML bean definitions to Java.

> **Annotation noise is a real cost.** Annotation-driven configuration is not free: `@Service`, `@Repository`, `@Controller`, `@Autowired`, `@Value`, `@Transactional` — these annotations scatter configuration concerns through your domain classes. For strict clean-architecture purists who want domain objects with zero framework annotations, `@Configuration` + explicit `@Bean` methods in a separate config class is the answer.

- No XML = type-safe, IDE-navigable, refactor-safe configuration.
- No code generation = the JAR you debug is built from exactly the source you see — no surprise generated files.
- `@Component` / `@Service` / `@Repository` / `@Controller` mark classes for auto-registration.
- Constructor injection is preferred over `@Autowired` field injection: it's testable without a Spring container and makes dependencies explicit.
- If you inherit XML config, use `@ImportResource` to keep it; gradually migrate to `@Configuration` as you touch those areas.
