---
card: spring-framework
gi: 131
slug: activating-a-profile-spring-profiles-active
title: "Activating a profile (spring.profiles.active)"
---

## 1. What it is

Profile activation is the mechanism that tells Spring which profiles should be considered active at runtime — determining which `@Profile`-gated beans are registered. There are five standard activation mechanisms, ordered from lowest to highest priority: default value, `@ActiveProfiles` (test), programmatic API, `spring.profiles.active` property, and JVM system property.

```
-Dspring.profiles.active=prod,eu
```
or
```java
ctx.getEnvironment().setActiveProfiles("prod", "eu");
```

## 2. Why & when

Profile activation is the runtime switch that makes `@Profile` beans useful. You need to understand activation to:

- Deploy the same JAR to dev, staging, and prod environments with different beans active.
- Run tests with a `"test"` profile that activates mocked services.
- Enable feature flags by activating a feature profile.
- Override the active profile in CI/CD pipelines via environment variables.

## 3. Core concept

The five activation mechanisms (lowest to highest priority):

| Mechanism | Example | Use case |
|---|---|---|
| Default profile (fallback) | `ctx.getEnvironment().setDefaultProfiles("dev")` | No explicit activation → dev mode |
| `@ActiveProfiles` (test) | `@ActiveProfiles("test")` on test class | Per-test profile |
| Programmatic API | `ctx.getEnvironment().setActiveProfiles("staging")` | Framework / bootstrap code |
| `spring.profiles.active` property | In `application.properties` | File-based config |
| JVM system property (`-D`) | `-Dspring.profiles.active=prod` | Container / deployment scripts |
| OS environment variable | `SPRING_PROFILES_ACTIVE=prod` | Docker / Kubernetes |

When multiple profiles are active, they are evaluated with OR semantics for `@Profile({"a","b"})` expressions and AND semantics for compound expressions like `@Profile("a & b")`.

`spring.profiles.include` (Spring Boot) lets you add profiles on top of the active set without replacing them — useful for activating a "common" profile always alongside the environment profile.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Activation sources (stacked) -->
  <rect x="10" y="28" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="110" y="47" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">1. default profile (lowest prio)</text>

  <rect x="10" y="65" width="200" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="84" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">2. @ActiveProfiles (test-only)</text>

  <rect x="10" y="102" width="200" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="121" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">3. programmatic setActiveProfiles()</text>

  <rect x="10" y="139" width="200" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="158" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">4. spring.profiles.active / -D</text>

  <!-- Arrow -->
  <line x1="212" y1="100" x2="295" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a131)"/>
  <defs>
    <marker id="a131" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b131" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Profile evaluation -->
  <rect x="297" y="60" width="200" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="397" y="82" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Active set: ["prod","eu"]</text>
  <text x="397" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">evaluate @Profile expressions</text>
  <text x="397" y="118" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Profile("prod") → true</text>
  <text x="397" y="132" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@Profile("dev")  → false</text>

  <!-- Beans -->
  <rect x="583" y="68" width="110" height="65" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="638" y="91" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Registered</text>
  <text x="638" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">prod beans ✓</text>
  <text x="638" y="124" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">dev beans ✗</text>

  <line x1="499" y1="100" x2="580" y2="100" stroke="#79c0ff" stroke-width="2" marker-end="url(#b131)"/>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">All activation mechanisms populate the same active profile set — highest-priority source wins</text>
</svg>

All activation mechanisms write to the same active profile set; the set is then evaluated against each `@Profile` expression during registration.

## 5. Runnable example

### Level 1 — Basic

Activate a profile programmatically and via a system property; observe which bean is registered.

```java
// ProfileActivateBasic.java
import org.springframework.context.annotation.*;

interface Logger { void log(String msg); }
class ConsoleLogger  implements Logger { public void log(String m) { System.out.println("[CONSOLE] " + m); } }
class FileLogger     implements Logger { public void log(String m) { System.out.println("[FILE]    " + m); } }

@Configuration
class LogCfg {
    @Bean @Profile("file")      public Logger fileLogger()    { return new FileLogger();    }
    @Bean @Profile("!file")     public Logger consoleLogger() { return new ConsoleLogger();  }
}

public class ProfileActivateBasic {
    static void run(String label, Runnable setup) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        setup.run();
        ctx.register(LogCfg.class);
        ctx.refresh();
        ctx.getBean(Logger.class).log("hello world");
        System.out.println("Active: " + java.util.Arrays.toString(
            ctx.getEnvironment().getActiveProfiles()));
        ctx.close();
        System.out.println();
    }

    public static void main(String[] args) {
        // No profile active → !file matches → ConsoleLogger
        run("no profile", () -> {});

        // Programmatic activation
        run("file profile (programmatic)", () ->
            System.setProperty("spring.profiles.active", "file"));

        // Via system property
        System.clearProperty("spring.profiles.active");
    }
}
```

How to run: `java ProfileActivateBasic.java`

Without a profile, `@Profile("!file")` matches → `ConsoleLogger`. With `spring.profiles.active=file`, `@Profile("file")` matches → `FileLogger`. The system property activates profiles globally before context creation.

### Level 2 — Intermediate

Programmatic activation with multiple profiles; show that setting profiles must happen before `refresh()`.

```java
// ProfileActivateMultiple.java
import org.springframework.context.annotation.*;
import java.util.*;

interface Mailer  { String send(String to, String msg); }
interface Storage { String save(String data);           }

class SmtpMailer     implements Mailer  { public String send(String t, String m) { return "[SMTP→"    + t + "] " + m; } }
class SandboxMailer  implements Mailer  { public String send(String t, String m) { return "[SANDBOX→" + t + "] " + m; } }
class S3Storage      implements Storage { public String save(String d) { return "[S3] " + d;     } }
class LocalStorage   implements Storage { public String save(String d) { return "[LOCAL] " + d;  } }

@Configuration
class InfraCfg {
    @Bean @Profile("prod")   public Mailer  smtpMailer()     { return new SmtpMailer();    }
    @Bean @Profile("!prod")  public Mailer  sandboxMailer()  { return new SandboxMailer(); }
    @Bean @Profile("aws")    public Storage s3Storage()      { return new S3Storage();     }
    @Bean @Profile("!aws")   public Storage localStorage()   { return new LocalStorage();  }
}

public class ProfileActivateMultiple {
    static void run(String label, String... profiles) {
        System.out.println("=== " + label + " ===");
        var ctx = new AnnotationConfigApplicationContext();
        // Must set profiles BEFORE refresh()
        ctx.getEnvironment().setActiveProfiles(profiles);
        ctx.register(InfraCfg.class);
        ctx.refresh();

        System.out.println("Active profiles: " + Arrays.toString(ctx.getEnvironment().getActiveProfiles()));
        ctx.getBean(Mailer.class).send("alice@acme.com", "Order confirmed").equals("") ; // print result
        System.out.println(ctx.getBean(Mailer.class).send("alice@acme.com", "Order confirmed"));
        System.out.println(ctx.getBean(Storage.class).save("order-data.json"));
        ctx.close();
        System.out.println();
    }

    public static void main(String[] args) {
        run("dev (no profiles)");
        run("prod only",  "prod");
        run("prod + aws", "prod", "aws");
        run("aws only",   "aws");
    }
}
```

How to run: `java ProfileActivateMultiple.java`

Orthogonal profiles `"prod"` (controls Mailer) and `"aws"` (controls Storage) compose independently. `"prod"` + `"aws"` gives production email with S3 storage.

### Level 3 — Advanced

Demonstrating all five activation mechanisms in a priority hierarchy — last activated wins.

```java
// ProfileActivatePriority.java
import org.springframework.context.annotation.*;
import org.springframework.core.env.*;
import java.util.*;

@Configuration
class PriorityCfg {
    // Beans gated on profile names that encode their source
    @Bean @Profile("from-default")      String defaultActivated()      { return "default-profile";    }
    @Bean @Profile("from-api")          String apiActivated()          { return "programmatic-api";   }
    @Bean @Profile("from-sysprop")      String syspropActivated()      { return "system-property";    }
    @Bean @Profile("from-envvar")       String envvarActivated()       { return "env-variable";       }
    @Bean @Profile("always")            String alwaysPresent()         { return "always-active";      }
}

public class ProfileActivatePriority {
    public static void main(String[] args) {
        // Demonstrate programmatic API activation
        System.out.println("=== Programmatic API ===");
        var ctx1 = new AnnotationConfigApplicationContext();
        ctx1.getEnvironment().setDefaultProfiles("from-default");   // fallback
        ctx1.getEnvironment().setActiveProfiles("from-api");         // explicit: overrides default
        ctx1.register(PriorityCfg.class);
        ctx1.refresh();

        System.out.println("Active profiles: " +
            Arrays.toString(ctx1.getEnvironment().getActiveProfiles()));
        System.out.println("Default profiles: " +
            Arrays.toString(ctx1.getEnvironment().getDefaultProfiles()));
        System.out.println("from-default present: " + ctx1.containsBean("defaultActivated"));
        System.out.println("from-api present:     " + ctx1.containsBean("apiActivated"));
        ctx1.close();

        // Demonstrate system property override
        System.out.println("\n=== System property ===");
        System.setProperty("spring.profiles.active", "from-sysprop");
        var ctx2 = new AnnotationConfigApplicationContext();
        ctx2.getEnvironment().setActiveProfiles("from-api");  // this is superseded by sysprop
        ctx2.register(PriorityCfg.class);
        ctx2.refresh();

        System.out.println("Active profiles: " +
            Arrays.toString(ctx2.getEnvironment().getActiveProfiles()));
        System.out.println("from-api present:     " + ctx2.containsBean("apiActivated"));
        System.out.println("from-sysprop present: " + ctx2.containsBean("syspropActivated"));
        ctx2.close();
        System.clearProperty("spring.profiles.active");

        // Multiple active profiles at once
        System.out.println("\n=== Multiple profiles (always + prod) ===");
        var ctx3 = new AnnotationConfigApplicationContext();
        ctx3.getEnvironment().setActiveProfiles("always", "from-api");
        ctx3.register(PriorityCfg.class);
        ctx3.refresh();
        System.out.println("Active: " + Arrays.toString(ctx3.getEnvironment().getActiveProfiles()));
        System.out.println("alwaysPresent:    " + ctx3.containsBean("alwaysPresent"));
        System.out.println("apiActivated:     " + ctx3.containsBean("apiActivated"));
        System.out.println("defaultActivated: " + ctx3.containsBean("defaultActivated"));
        ctx3.close();
    }
}
```

How to run: `java ProfileActivatePriority.java`

The system property `spring.profiles.active` is read by `StandardEnvironment` and takes precedence over `setActiveProfiles()` called in code — because the property is registered as a high-priority `PropertySource`. When `setActiveProfiles()` is called AND the system property is set, the system property wins (it's evaluated at `refresh()` time by the property-source chain).

## 6. Walkthrough

Execution for Level 3 "System property" run:

1. **`System.setProperty("spring.profiles.active", "from-sysprop")`** — places `"from-sysprop"` in JVM system properties.
2. **`ctx.getEnvironment().setActiveProfiles("from-api")`** — sets programmatic active profile to `"from-api"`.
3. **`ctx.refresh()`** — `StandardEnvironment` initialises. It reads `spring.profiles.active` from system properties (high-priority `PropertySource`) and activates `"from-sysprop"`, overriding the programmatic value.
4. **`getActiveProfiles()`** → `["from-sysprop"]`.
5. **`from-api present`** → `false`. **`from-sysprop present`** → `true`.

Expected output:
```
=== System property ===
Active profiles: [from-sysprop]
from-api present:     false
from-sysprop present: true
```

## 7. Gotchas & takeaways

> `setActiveProfiles()` must be called **before** `ctx.refresh()`. After refresh, beans are already instantiated. Profile activation after refresh has no effect on bean registration.

> When `spring.profiles.active` is set as a system property, it overrides `setActiveProfiles()` programmatic calls. This surprises developers who set a profile in code and wonder why it's being ignored — check system properties first.

- `setDefaultProfiles()` sets the fallback profile(s) used when NO profile is explicitly activated. Setting any active profile causes the default to be ignored.
- `spring.profiles.active` and `spring.profiles.include` (Spring Boot) can be set in `application.properties`, environment variables, or system properties.
- The OS environment variable equivalent is `SPRING_PROFILES_ACTIVE` (uppercase, underscores — Spring converts it to the dot-notation property).
- `@ActiveProfiles` on a test class is the cleanest way to activate a profile in unit/integration tests — it integrates with Spring TestContext Framework.
