---
card: spring-boot
gi: 8
slug: spring-boot-vs-spring-framework
title: Spring Boot vs Spring Framework
---

## 1. What it is

**Spring Framework** is the core IoC (Inversion of Control) container and application framework — the engine. It provides dependency injection, AOP (Aspect-Oriented Programming), data access abstractions, transaction management, and web MVC. It is the foundation everything else is built on.

**Spring Boot** is an opinionated starter kit built on top of Spring Framework. It adds auto-configuration, starter dependencies, an embedded server, production-ready features (Actuator), and the Spring Boot Maven/Gradle plugin. It does not replace Spring Framework; it makes Spring Framework easier to use.

Analogy: Spring Framework is like a professional kitchen (ovens, knives, stations, refrigerators). Spring Boot is the catering service that comes in, sets the kitchen up in the right configuration for you, stocks it with compatible ingredients, and hands you the keys — you still cook with the same kitchen.

| Aspect | Spring Framework | Spring Boot |
|---|---|---|
| Core feature | IoC container, AOP, MVC | Auto-configuration, starters, embedded server |
| Config style | Explicit (`@Bean`, XML) | Convention + property file |
| Standalone? | No (needs a container or explicit wiring) | Yes (`java -jar app.jar`) |
| Dependency management | Manual (you specify all versions) | Managed (BOM pins versions) |
| First release | 2002 | 2014 |

## 2. Why & when

**Use Spring Boot** (the vast majority of new projects):
- Starting a new REST API, web app, batch job, or event consumer.
- You want a working, deployable service in under 10 minutes.
- You want managed dependency versions and automatic infrastructure wiring.

**Know Spring Framework** (always necessary, even with Spring Boot):
- Every Spring Boot app is a Spring Framework app at runtime.
- When auto-configuration doesn't meet your needs, you write Spring Framework `@Configuration` classes to override it.
- Understanding `ApplicationContext`, `BeanFactory`, `@Transactional`, `PlatformTransactionManager` requires Spring Framework knowledge.
- Writing custom starters or integrating third-party libraries with Spring Boot requires Spring Framework internals.

You don't choose one over the other — you use Spring Boot (the starter) which runs on Spring Framework (the engine). Choosing "just Spring Framework" today means manually doing what Spring Boot does for free.

## 3. Core concept

The relationship is layered:

```
Your Application Code
        ↕
Spring Boot Auto-Configuration
  (starter POMs, @SpringBootApplication, embedded server, Actuator)
        ↕
Spring Framework
  (ApplicationContext, BeanFactory, @Bean, @Transactional, Spring MVC,
   Spring Data, Spring Security, Spring AOP, ...)
        ↕
JVM / Java Standard Library
```

`@SpringBootApplication` is the bridge between layers. It expands to:

- `@SpringBootConfiguration` — a specialisation of `@Configuration` (Spring Framework).
- `@EnableAutoConfiguration` — Spring Boot's trigger to load and apply auto-configuration classes.
- `@ComponentScan` — Spring Framework's mechanism to find `@Component` classes in your package.

Auto-configuration classes are themselves Spring Framework `@Configuration` classes with `@Conditional*` guards. When a condition passes, the `@Bean` methods in the auto-config class run and their results enter the Spring Framework `ApplicationContext` like any other bean.

Everything you know about Spring Framework — `@Autowired`, `@Transactional`, `@Value`, `RestTemplate`, `JpaRepository`, `@Aspect` — still applies in a Spring Boot app. Spring Boot just removes the need to set up the infrastructure those features run on.

## 4. Diagram

<svg viewBox="0 0 660 300" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Layered diagram showing Spring Boot sitting on top of Spring Framework which sits on the JVM">
  <!-- JVM layer -->
  <rect x="40" y="240" width="580" height="44" rx="7" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="267" fill="#8b949e" font-size="13" text-anchor="middle" font-family="sans-serif">JVM + Java Standard Library</text>

  <!-- Spring Framework layer -->
  <rect x="40" y="168" width="580" height="64" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="330" y="190" fill="#79c0ff" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Framework</text>
  <text x="330" y="210" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ApplicationContext · BeanFactory · @Bean · Spring MVC · @Transactional · AOP · Spring Data · Spring Security</text>
  <text x="330" y="226" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">IoC container + core abstractions (since 2002)</text>

  <!-- Spring Boot layer -->
  <rect x="40" y="92" width="580" height="68" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="330" y="114" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot</text>
  <text x="330" y="134" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Auto-Configuration · Starter POMs · Embedded Server · Actuator · Spring Boot Plugin</text>
  <text x="330" y="152" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Opinionated starter layer — wires Spring Framework automatically (since 2014)</text>

  <!-- Your app layer -->
  <rect x="40" y="20" width="580" height="64" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2" stroke-dasharray="6,3"/>
  <text x="330" y="42" fill="#e6edf3" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Your Application Code</text>
  <text x="330" y="62" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@RestController · @Service · @Repository · business logic · domain model</text>
  <text x="330" y="78" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Uses both layers — Spring Framework APIs + Spring Boot conventions</text>
</svg>

Your code sits atop Spring Boot which sits atop Spring Framework — the deeper you go, the more fundamental the layer, and the less you need to touch it directly.

## 5. Runnable example

```java
// File: FrameworkVsBootDemo.java
// Shows the conceptual difference: Framework = explicit wiring, Boot = convention wiring.
// Run: java FrameworkVsBootDemo.java

public class FrameworkVsBootDemo {

    // ---- Spring Framework style: you wire everything explicitly ----
    static class EmailService {
        private final String smtpHost;
        EmailService(String smtpHost) { this.smtpHost = smtpHost; }
        String send(String to, String msg) {
            return "Sent '" + msg + "' to " + to + " via " + smtpHost;
        }
    }

    static class NotificationService {
        private final EmailService email;
        NotificationService(EmailService email) { this.email = email; }
        String notify(String user) {
            return email.send(user, "Welcome!");
        }
    }

    // Simulates a Spring Framework @Configuration class —
    // developer manually declares and wires every bean
    static NotificationService springFrameworkStyle() {
        System.out.println("[Spring Framework] Developer wires beans manually:");
        String smtpHost = System.getenv().getOrDefault("SMTP_HOST", "smtp.example.com");
        var emailSvc = new EmailService(smtpHost);
        System.out.println("  new EmailService(\"" + smtpHost + "\")");
        var notifSvc = new NotificationService(emailSvc);
        System.out.println("  new NotificationService(emailSvc)");
        return notifSvc;
    }

    // Simulates Spring Boot auto-configuration —
    // framework reads properties and wires EmailService automatically
    static NotificationService springBootStyle() {
        System.out.println("[Spring Boot] Auto-configuration reads convention + properties:");
        String smtpHost = System.getenv().getOrDefault("SMTP_HOST", "smtp.example.com");
        // Auto-config detects 'EmailService' needed, reads 'spring.mail.host' convention
        System.out.println("  @ConditionalOnClass(EmailService) → true");
        System.out.println("  @ConditionalOnProperty(spring.mail.host) → " + smtpHost);
        System.out.println("  Auto-registered: EmailService, NotificationService");
        return new NotificationService(new EmailService(smtpHost));
    }

    public static void main(String[] args) {
        System.out.println("=== Same result, different effort ===\n");

        var frameworkResult = springFrameworkStyle();
        System.out.println("Result: " + frameworkResult.notify("alice@example.com"));

        System.out.println();

        var bootResult = springBootStyle();
        System.out.println("Result: " + bootResult.notify("alice@example.com"));

        System.out.println();
        System.out.println("Both produce identical behaviour.");
        System.out.println("Spring Boot just removed the manual wiring code.");
    }
}
```

**How to run:** `java FrameworkVsBootDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Same result, different effort ===

[Spring Framework] Developer wires beans manually:
  new EmailService("smtp.example.com")
  new NotificationService(emailSvc)
Result: Sent 'Welcome!' to alice@example.com via smtp.example.com

[Spring Boot] Auto-configuration reads convention + properties:
  @ConditionalOnClass(EmailService) → true
  @ConditionalOnProperty(spring.mail.host) → smtp.example.com
  Auto-registered: EmailService, NotificationService
Result: Sent 'Welcome!' to alice@example.com via smtp.example.com

Both produce identical behaviour.
Spring Boot just removed the manual wiring code.
```

## 6. Walkthrough

- **`EmailService` and `NotificationService`** — plain Java classes with constructor injection, no framework annotations. This is valid in both Spring Framework and Spring Boot worlds; the framework wires them regardless of how they're written.
- **`springFrameworkStyle()`** — mimics a hand-written `@Bean` method in a `@Configuration` class. The developer explicitly instantiates `EmailService` with the SMTP host and passes it to `NotificationService`. In a real Spring Framework app without Boot, you write this for every infrastructure service.
- **`springBootStyle()`** — shows the auto-configuration checks Spring Boot would run. If `EmailService` is on the classpath and `spring.mail.host` is set, Boot auto-creates an `EmailService` bean; `NotificationService`'s `@Autowired` constructor gets it injected without any user `@Bean` method.
- **`System.getenv().getOrDefault`** — reads from environment variables (the highest priority override in Spring Boot), falling back to a default. Same precedence model as Spring Boot's property resolution.
- **Same output, different code path** — the application behaviour is identical. The difference is how much infrastructure code the developer writes.

## 7. Gotchas & takeaways

> **"Spring" is not one thing.** Saying "I use Spring" is ambiguous. Spring Framework (the core), Spring Boot (the starter), Spring Data, Spring Security, Spring Cloud, Spring Batch are all separate projects maintained under the Spring umbrella. They work together, but each has its own version and release cycle.

> **Spring Boot version = Spring Framework version (approximately).** Spring Boot 3.x requires Spring Framework 6.x. Spring Boot 2.x ran on Spring Framework 5.x. You don't choose the Spring Framework version separately — it's managed by the Spring Boot BOM.

- Spring Framework is the foundation: IoC, AOP, MVC, Data, Security. You always use it.
- Spring Boot is the starter: auto-config, starters, embedded server. Use it for every new project.
- `@SpringBootApplication = @Configuration + @EnableAutoConfiguration + @ComponentScan` — three Spring Framework annotations composed into one Spring Boot convenience annotation.
- Knowing Spring Framework internals makes you better at Spring Boot: you understand what Boot is doing for you, and you can override it when needed.
- When diagnosing a Spring Boot problem, the answer is almost always in Spring Framework's `ApplicationContext` — Boot just set it up.
