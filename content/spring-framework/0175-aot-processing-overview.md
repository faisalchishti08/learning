---
card: spring-framework
gi: 175
slug: aot-processing-overview
title: AOT processing overview
---

## 1. What it is

**AOT (Ahead-of-Time) processing** is a build-time step introduced in Spring Framework 6 / Spring Boot 3. Instead of discovering beans, resolving conditions, and configuring proxies at startup via reflection and classpath scanning, the AOT engine does that work *once* at build time and writes out Java source code that replaces the dynamic work at runtime.

The build-time step produces:
- **`*__BeanDefinitions.java`** — programmatic `BeanDefinition` registration code (no `@ComponentScan` at runtime).
- **Generated proxy classes** — CGLIB and JDK proxy subclasses generated as source files.
- **Native image metadata** — `reflect-config.json`, `resource-config.json`, `proxy-config.json`, `serialization-config.json` under `META-INF/native-image/`.

At runtime, Spring detects the pre-generated sources and skips the expensive reflective startup path.

## 2. Why & when

- **Native images** — GraalVM `native-image` cannot use most runtime reflection. AOT generates static code that avoids reflection entirely, making native compilation possible.
- **Faster JVM startup** — even on a regular JVM the AOT path avoids classpath scanning and condition evaluation, trimming startup time.
- **Build-time validation** — missing beans, bad configurations, and missing reflection hints surface at build time rather than first request in production.
- **Not needed** if you run a traditional JVM with no startup time constraints and no native image target — the regular dynamic path still works perfectly.

## 3. Core concept

The AOT process runs via the Spring Boot Maven/Gradle plugin with a special "AOT mode" context:

```
./mvnw spring-boot:process-aot          (Maven)
./gradlew processAot                    (Gradle)
```

The engine:
1. Starts an `ApplicationContext` in **AOT mode** (beans are analysed but not fully started).
2. Runs `BeanFactoryInitializationAotProcessor` and `BeanRegistrationAotProcessor` implementations against every `BeanDefinition`.
3. Each processor either generates source code or contributes hints.
4. The generated sources are placed in `target/spring-aot/main/sources/` and compiled alongside your app.
5. At runtime, `SpringApplication` checks for the generated `ApplicationContextInitializer` and uses it instead of scanning.

| Phase | What happens | Where |
|---|---|---|
| Build time | AOT engine analyses beans, generates code & hints | `target/spring-aot/` |
| Compile time | Generated sources compiled into the JAR | Part of the build |
| Runtime (JVM) | Spring uses pre-generated initializer, skips scan | Fast startup |
| Runtime (native) | `native-image` uses hints to include required classes | No reflection at all |

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="aota" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="aotb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Build time box -->
  <rect x="5" y="5" width="330" height="210" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="170" y="25" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Build Time</text>

  <rect x="20" y="35" width="130" height="24" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1"/>
  <text x="85" y="51" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Your source code</text>

  <line x1="85" y1="60" x2="85" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aota)"/>
  <rect x="20" y="77" width="130" height="24" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1"/>
  <text x="85" y="93" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">spring-boot:process-aot</text>

  <line x1="85" y1="102" x2="85" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aota)"/>
  <rect x="20" y="118" width="130" height="24" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="85" y="134" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">AOT engine analyses ctx</text>

  <rect x="185" y="50" width="135" height="60" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="252" y="67" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Generated output:</text>
  <text x="252" y="80" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">*__BeanDefinitions.java</text>
  <text x="252" y="93" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">reflect-config.json</text>
  <text x="252" y="106" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">resource-config.json</text>
  <line x1="153" y1="130" x2="183" y2="80" stroke="#6db33f" stroke-width="1.2" marker-end="url(#aota)" opacity="0.6"/>

  <rect x="20" y="155" width="295" height="24" rx="4" fill="#6db33f" opacity="0.15" stroke="#6db33f" stroke-width="1"/>
  <text x="167" y="171" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">compile source + generated sources into JAR / native image</text>

  <line x1="252" y1="112" x2="252" y2="153" stroke="#6db33f" stroke-width="1.2" marker-end="url(#aota)" opacity="0.6"/>

  <!-- Runtime box -->
  <rect x="360" y="5" width="335" height="210" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="527" y="25" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Runtime</text>

  <rect x="375" y="35" width="145" height="70" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="447" y="52" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JVM path</text>
  <text x="447" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">AOT initializer skips scan</text>
  <text x="447" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">uses generated bean defs</text>
  <text x="447" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fast startup, no @Scan</text>

  <rect x="535" y="35" width="145" height="70" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="607" y="52" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Native image path</text>
  <text x="607" y="66" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no JVM, no reflection</text>
  <text x="607" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">hints → code included</text>
  <text x="607" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ms startup, low memory</text>

  <text x="527" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Both use the same generated AOT output.</text>
  <text x="527" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Spring detects pre-generated initializer on classpath</text>
  <text x="527" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">and activates AOT mode automatically.</text>
</svg>

AOT moves Spring's reflection-heavy startup work to build time; at runtime, pre-generated code runs instead of dynamic scanning.

## 5. Runnable example

The scenario is a **user management service** in a Spring application — growing from a plain Spring context to AOT-style programmatic registration that mirrors what the AOT engine generates.

### Level 1 — Basic

Standard Spring context with annotation-based scanning — the baseline that AOT optimises.

```java
// AotOverviewBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service
class UserService {
    public String greet(String name) { return "Hello, " + name + "!"; }
}

@Service
class AuditService {
    public void log(String msg) { System.out.println("[AUDIT] " + msg); }
}

@Configuration
@ComponentScan   // runtime scanning — the dynamic path AOT replaces
class AppConfig { }

public class AotOverviewBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);

        UserService  users  = ctx.getBean(UserService.class);
        AuditService audit  = ctx.getBean(AuditService.class);

        String greeting = users.greet("Alice");
        System.out.println(greeting);       // Hello, Alice!
        audit.log("Greeted Alice");         // [AUDIT] Greeted Alice

        // In a standard JVM run Spring did classpath scanning, reflection,
        // condition evaluation — all at startup for every bean found.
        System.out.println("Context started with " +
            ctx.getBeanDefinitionCount() + " bean definitions");

        ctx.close();
    }
}
```

How to run: `java AotOverviewBasic.java`

`@ComponentScan` triggers classpath scanning: Spring finds `UserService` and `AuditService` via reflection, reads their annotations, builds `BeanDefinition` objects, and wires the context. Every restart repeats this work. AOT replaces it with generated code that does the same registration without scanning.

### Level 2 — Intermediate

Programmatic bean registration — the same context as Level 1, but registered the way AOT-generated code does it.

```java
// AotOverviewIntermediate.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.support.*;
import org.springframework.stereotype.*;

// Same beans — NOT annotated with @Service (AOT generates code to register them)
class UserServiceAot {
    public String greet(String name) { return "Hello, " + name + "!"; }
}

class AuditServiceAot {
    public void log(String msg) { System.out.println("[AUDIT] " + msg); }
}

public class AotOverviewIntermediate {
    public static void main(String[] args) {
        // AOT-generated code produces something like this:
        // - no @ComponentScan
        // - no reflection to find beans
        // - explicit RootBeanDefinition registrations
        var factory = new DefaultListableBeanFactory();

        // Register UserService programmatically (what AOT emits)
        var userBd = new RootBeanDefinition(UserServiceAot.class);
        userBd.setInstanceSupplier(UserServiceAot::new);  // supplier — no reflection
        factory.registerBeanDefinition("userService", userBd);

        // Register AuditService programmatically
        var auditBd = new RootBeanDefinition(AuditServiceAot.class);
        auditBd.setInstanceSupplier(AuditServiceAot::new);
        factory.registerBeanDefinition("auditService", auditBd);

        // Use the factory
        var ctx = new GenericApplicationContext(factory);
        ctx.refresh();

        UserServiceAot  users  = factory.getBean(UserServiceAot.class);
        AuditServiceAot audit  = factory.getBean(AuditServiceAot.class);

        String greeting = users.greet("Alice");
        System.out.println(greeting);
        audit.log("Greeted Alice");

        System.out.println("Beans registered: " + factory.getBeanDefinitionCount());
        ctx.close();
    }
}
```

How to run: `java AotOverviewIntermediate.java`

`RootBeanDefinition` + `setInstanceSupplier(UserServiceAot::new)` is exactly the pattern AOT-generated `*__BeanDefinitions.java` files use. The supplier is a method reference — the JVM can call it directly without reflection. Classpath scanning is absent; no annotations are read at runtime.

### Level 3 — Advanced

A Spring Boot-style app wired for AOT processing — `pom.xml` configuration for the AOT plugin, `@SpringBootApplication`, and the Maven command that triggers AOT source generation.

```java
// AotOverviewAdvanced.java — Spring Boot app; run the AOT processor first
// pom.xml must include spring-boot-maven-plugin 3.x
// Command: ./mvnw spring-boot:process-aot  (generates target/spring-aot/main/sources/)
// Then build: ./mvnw package -DskipTests
// Run: java -jar target/app.jar
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;

@Service
class GreetingService {
    public String greet(String name) { return "Hello from AOT, " + name + "!"; }
}

@RestController
class GreetingController {
    private final GreetingService svc;
    GreetingController(GreetingService svc) { this.svc = svc; }

    @GetMapping("/greet/{name}")
    public String greet(@PathVariable String name) { return svc.greet(name); }
}

@SpringBootApplication
public class AotOverviewAdvanced {
    public static void main(String[] args) {
        SpringApplication.run(AotOverviewAdvanced.class, args);
        // After spring-boot:process-aot, Spring generates:
        //   target/spring-aot/main/sources/
        //     GreetingController__BeanDefinitions.java
        //     GreetingService__BeanDefinitions.java
        //     AotOverviewAdvanced__BeanDefinitions.java
        //   target/spring-aot/main/resources/
        //     META-INF/native-image/reflect-config.json
        //     META-INF/native-image/resource-config.json
    }
}
```

How to run: `./mvnw spring-boot:process-aot` then `./mvnw package` then `java -jar target/app.jar`

When AOT-processed, Spring Boot detects the pre-generated `ApplicationContextInitializer` subclass on the classpath and calls it instead of performing `@ComponentScan`. The effect is the same context but with startup time reduced because no scanning or condition evaluation happens at runtime. On a native image build (`-Pnative native:compile`), the generated hints ensure `GreetingService` and `GreetingController` are included in the image without needing reflection.

## 6. Walkthrough

Tracing what happens when `spring-boot:process-aot` runs against the Level 3 app:

**Step 1 — Plugin starts the AOT process:**
The Spring Boot Maven plugin creates a special AOT-mode application context. It loads bean definitions from `@SpringBootApplication` but does NOT fully start the app — servers don't bind ports.

**Step 2 — `BeanFactoryInitializationAotProcessor` runs:**
Spring's built-in processor walks every `BeanDefinition` registered in the context:
- `GreetingService` — generates `GreetingService__BeanDefinitions.java`
- `GreetingController` — generates `GreetingController__BeanDefinitions.java`
- Internal Spring beans — each gets a `__BeanDefinitions` source file

**Step 3 — Generated source (simplified):**
```java
// GreetingService__BeanDefinitions.java (generated — do not edit)
public class GreetingService__BeanDefinitions {
    public static BeanDefinitionHolder getGreetingServiceBeanDefinition() {
        var bd = new RootBeanDefinition(GreetingService.class);
        bd.setInstanceSupplier(GreetingService::new);
        return new BeanDefinitionHolder(bd, "greetingService");
    }
}
```

**Step 4 — Hint collection:**
Processors inspect what each bean uses at runtime (Jackson for JSON, JPA for Hibernate, etc.) and emit entries into `reflect-config.json`.

**Step 5 — Compile time:**
The build includes the generated sources in the compilation classpath. The final JAR contains both your code and the generated `__BeanDefinitions` classes.

**Step 6 — Runtime:**
`SpringApplication.run()` finds an `AotApplicationContextInitializer` on the classpath. It calls `register()` on each generated `__BeanDefinitions` class instead of running `@ComponentScan`. Startup skips reflection entirely for registered beans.

## 7. Gotchas & takeaways

> **AOT evaluates `@Conditional` annotations at build time, not runtime.** `@ConditionalOnProperty("feature.enabled")` is evaluated against the *build environment*. If the property is absent at build time, the bean is excluded from generated code — even if the property is present at runtime. Set AOT-time properties explicitly via `spring.aot.enabled=true` and test-time properties via environment variables during the `process-aot` phase.

> **AOT-generated sources are in `target/spring-aot/` — version-control your `pom.xml` or `build.gradle` changes, not the generated files.** The generated sources regenerate on every AOT build and must not be manually edited.

- Run `./mvnw spring-boot:test-process-aot` + AOT test execution to catch hint gaps before production.
- Third-party libraries need their own Spring AOT support or manual `RuntimeHintsRegistrar`. Check `spring.io/projects/spring-native` for ecosystem compatibility status.
- AOT mode is activated at runtime when `spring.aot.enabled=true` (set automatically in native images) or `SpringApplication.setDefaultProperties(Map.of("spring.aot.enabled","true"))`.
- The generated `ApplicationContextInitializer` is idempotent — it can be called multiple times safely.
