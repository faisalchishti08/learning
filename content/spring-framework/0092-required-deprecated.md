---
card: spring-framework
gi: 92
slug: required-deprecated
title: "@Required (deprecated)"
---

## 1. What it is

`@Required` was a Spring annotation placed on **setter methods** to declare that the property must be set at configuration time. If Spring could not inject a value for an `@Required` setter, it threw a `BeanInitializationException` at startup — a fail-fast guard against missing configuration.

As of Spring 5.1, `@Required` is **deprecated**. It is still functional in Spring 6 for backwards compatibility but should not be used in new code.

## 2. Why & when

Before constructor injection became the idiomatic Spring style, many Spring apps used setter injection. `@Required` existed to make setter injection almost as safe as constructor injection: if you forgot to wire a property, Spring would crash at startup rather than silently leaving `null` fields that cause `NullPointerException`s in production.

It is only relevant today if you:

- Are reading or maintaining a pre-2018 codebase that used `@Required`.
- Need to understand why a legacy app throws `BeanInitializationException` on startup.

Modern replacement: constructor injection (with `@Autowired` on the constructor, or implicit single-constructor injection). The compiler enforces required dependencies because a constructor parameter can't be `null` without explicit effort.

## 3. Core concept

`@Required` worked through a `BeanPostProcessor` called `RequiredAnnotationBeanPostProcessor`. It was registered automatically when you used `<context:annotation-config/>` or `@Configuration` with annotation processing.

The lifecycle:
1. Spring sets bean properties via setter injection.
2. `RequiredAnnotationBeanPostProcessor.postProcessAfterInstantiation` checks every method annotated with `@Required` on the bean.
3. If any `@Required` setter was not called (no matching bean or value was configured), a `BeanInitializationException` is thrown.

The bean never entered service — fail-fast, never silent-null.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <rect x="10" y="70" width="160" height="54" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="97" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Bean instantiated</text>
  <text x="90" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">constructor called</text>

  <rect x="270" y="70" width="175" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="357" y="94" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">RequiredAnnotation</text>
  <text x="357" y="110" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">BeanPostProcessor</text>

  <rect x="530" y="40" width="155" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="607" y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">All setters called</text>
  <text x="607" y="76" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">bean enters service</text>

  <rect x="530" y="110" width="155" height="44" rx="8" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="607" y="132" fill="#ff7b72" font-size="12" text-anchor="middle" font-family="sans-serif">Missing setter</text>
  <text x="607" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">BeanInitializationException</text>

  <line x1="172" y1="97" x2="267" y2="97" stroke="#6db33f" stroke-width="2" marker-end="url(#a92)"/>
  <line x1="447" y1="85" x2="527" y2="62" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a92)"/>
  <line x1="447" y1="110" x2="527" y2="132" stroke="#ff7b72" stroke-width="1.5" marker-end="url(#c92)"/>
  <defs>
    <marker id="a92" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="c92" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Required checked after setter injection — throws on missing required setter</text>
</svg>

The post-processor validates after setter injection; missing required setters cause a startup failure.

## 5. Runnable example

### Level 1 — Basic

The original `@Required` setter-injection pattern, so you can see what it looked like.

```java
// RequiredDemo.java
import org.springframework.beans.factory.annotation.Required;
import org.springframework.context.annotation.*;

class EmailService {
    private String smtpHost;
    private int port;

    @Required
    public void setSmtpHost(String h) { this.smtpHost = h; }

    @Required
    public void setPort(int p) { this.port = p; }

    public void send(String msg) {
        System.out.println("Sending via " + smtpHost + ":" + port + " — " + msg);
    }
}

@Configuration
class EmailCfg {
    @Bean
    public EmailService emailService() {
        var svc = new EmailService();
        svc.setSmtpHost("smtp.example.com");
        svc.setPort(587);
        return svc;
    }
}

public class RequiredDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EmailCfg.class);
        ctx.getBean(EmailService.class).send("Hello!");
        ctx.close();
    }
}
```

How to run: `java RequiredDemo.java`

Both required setters are called in the `@Bean` method — startup succeeds. The pattern shows the old style: annotate setters, wire them in config.

### Level 2 — Intermediate

Demonstrate what failure looks like: remove one required setter call and observe the startup exception.

```java
// RequiredFail.java
import org.springframework.beans.factory.annotation.Required;
import org.springframework.context.annotation.*;

class ReportService {
    private String reportDir;
    private String outputFormat;

    @Required public void setReportDir(String d) { this.reportDir = d; }
    @Required public void setOutputFormat(String f) { this.outputFormat = f; }

    public void generate() {
        System.out.println("Report: " + outputFormat + " → " + reportDir);
    }
}

@Configuration
class ReportCfg {
    @Bean
    public ReportService reportService() {
        var svc = new ReportService();
        svc.setReportDir("/reports");
        // outputFormat NOT set — @Required will catch this
        return svc;
    }
}

public class RequiredFail {
    public static void main(String[] args) {
        try {
            var ctx = new AnnotationConfigApplicationContext(ReportCfg.class);
            ctx.getBean(ReportService.class).generate();
            ctx.close();
        } catch (Exception e) {
            System.out.println("Startup failed: " + e.getMessage());
        }
    }
}
```

How to run: `java RequiredFail.java`

Spring throws `BeanInitializationException: Property 'outputFormat' is required for bean 'reportService'`. This is exactly the safety guarantee `@Required` provided — crash at startup, not at runtime when `outputFormat` would have been `null`.

### Level 3 — Advanced

The modern equivalent using constructor injection — no `@Required` needed, same safety guarantee enforced by the compiler.

```java
// ConstructorInjectionDemo.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.Component;

// No @Required — constructor guarantees all deps are provided
record SmtpConfig(String host, int port) {}

@Component
class ModernEmailService {
    private final SmtpConfig smtp;
    private final String fromAddress;

    // Single constructor — Spring auto-wires without @Autowired
    public ModernEmailService(SmtpConfig smtp, String fromAddress) {
        // Null-check at construction time — no runtime NullPointerException possible
        if (smtp == null) throw new IllegalArgumentException("smtp config required");
        if (fromAddress == null || fromAddress.isBlank()) throw new IllegalArgumentException("fromAddress required");
        this.smtp = smtp;
        this.fromAddress = fromAddress;
    }

    public void send(String to, String body) {
        System.out.printf("From %s via %s:%d → %s: %s%n",
            fromAddress, smtp.host(), smtp.port(), to, body);
    }
}

@Configuration
@ComponentScan
class ModernCfg {
    @Bean SmtpConfig smtpConfig() { return new SmtpConfig("smtp.example.com", 587); }
    @Bean String fromAddress()    { return "noreply@example.com"; }
}

public class ConstructorInjectionDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ModernCfg.class);
        ctx.getBean(ModernEmailService.class).send("user@example.com", "Welcome!");
        ctx.close();
    }
}
```

How to run: `java ConstructorInjectionDemo.java`

If either `smtpConfig` or `fromAddress` bean is absent, Spring throws `NoSuchBeanDefinitionException` at startup — same fail-fast behaviour as `@Required`, but enforced by the DI framework and the constructor itself, with no deprecated annotations.

## 6. Walkthrough

Execution order for the Level 3 example (the modern replacement):

1. **`AnnotationConfigApplicationContext` created** — scans `ModernCfg`, finds `SmtpConfig` and `String` `@Bean`s plus `ModernEmailService` via `@ComponentScan`.
2. **Spring determines `ModernEmailService` needs** `SmtpConfig` and `String` — it inspects the single constructor's parameters.
3. **Dependency lookup** — Spring resolves `SmtpConfig` → `smtpConfig()` bean; `String` → `fromAddress()` bean.
4. **Constructor called** — `new ModernEmailService(smtp, "noreply@example.com")`. The two null-checks run immediately. Both pass.
5. **`send()` called** — prints the formatted message.
6. **Compare to `@Required` path** — if `smtpConfig` bean were absent, step 3 would throw `NoSuchBeanDefinitionException` (or an `UnsatisfiedDependencyException`). Same fail-fast result, no deprecated API.

Expected output:
```
From noreply@example.com via smtp.example.com:587 → user@example.com: Welcome!
```

## 7. Gotchas & takeaways

> `@Required` is deprecated since Spring 5.1. **Do not use it in new code.** Switch all setter-injected required fields to constructor injection.

> `RequiredAnnotationBeanPostProcessor` must be registered for `@Required` to work. `<context:annotation-config/>` or `@Configuration` with annotation scanning registers it automatically; raw XML without annotation config does not.

- `@Required` was a band-aid: setter injection inherently allows partial wiring; constructor injection makes incomplete wiring impossible.
- The modern idiom: single constructor + `final` fields. Spring wires it without `@Autowired` (as of Spring 4.3 with a single constructor).
- If you absolutely must use setter injection for optional dependencies, leave off `@Required` — only use it on truly mandatory setters.
- Spring Boot apps should prefer `@ConfigurationProperties` (with `@Validated`) for required configuration validation rather than either approach above.
