---
card: spring-boot
gi: 90
slug: profile-on-beans
title: "@Profile on beans"
---

## 1. What it is

The **`@Profile`** annotation (from `org.springframework.context.annotation`) controls whether a Spring bean is registered in the application context based on which profiles are currently active. You place it on:

- A `@Component`-annotated class (including `@Service`, `@Repository`, `@Controller`).
- A `@Bean` factory method inside a `@Configuration` class.
- A `@Configuration` class itself (the entire class and all its `@Bean` methods are skipped if the profile doesn't match).

The annotation accepts a profile expression, which can be:
- A simple name: `@Profile("prod")` — matches when `prod` is active.
- A negation: `@Profile("!prod")` — matches when `prod` is NOT active.
- A Spring Expression Language (SpEL) compound expression: `@Profile("prod & cloud")` — matches when both are active.
- An OR expression: `@Profile({"prod", "staging"})` — matches when `prod` OR `staging` is active.

When a bean's profile condition is false, the bean does not exist in the context — attempting to inject it throws `NoSuchBeanDefinitionException` unless another bean satisfies the dependency.

## 2. Why & when

`@Profile` is the complement to profile-specific property files. Property files change *values* (URL, password, pool size); `@Profile` changes *which beans exist* (swap an entire implementation, toggle a feature).

Typical uses:
- **Swap data sources** — `H2DataSource` in dev, `PostgresDataSource` in prod, both implementing `DataSource`.
- **Mock services in tests** — `MockEmailService` annotated `@Profile("test")` replaces `SmtpEmailService` so tests never send real emails.
- **Feature flags** — `FeatureXController` annotated `@Profile("feature-x")` is absent until the feature profile is activated.
- **Dev-only tools** — `@Profile("!prod")` on a `DataSeeder` bean that populates the database with test data on startup.
- **Conditional configuration classes** — annotate an entire `@Configuration` class to include/exclude a whole group of beans at once.

## 3. Core concept

`@Profile` is implemented as a specialisation of `@Conditional`. Internally, Spring checks `ProfileCondition.matches()` against the `Environment.getActiveProfiles()` set for every candidate bean definition.

Profile expression rules:
```
@Profile("a")        → a ∈ active
@Profile("!a")       → a ∉ active
@Profile("a & b")    → a ∈ active AND b ∈ active   (Spring 4+)
@Profile("a | b")    → a ∈ active OR  b ∈ active   (Spring 4+)
@Profile({"a","b"})  → a ∈ active OR  b ∈ active   (array = OR shorthand)
```

When `@Profile` is on a `@Configuration` class, the condition applies to the whole class. `@Bean` methods inside a non-matching configuration class are never evaluated. You can also place `@Profile` on individual `@Bean` methods inside a configuration class — useful when most beans in the class are universal but one or two are profile-specific.

## 4. Diagram

<svg viewBox="0 0 680 310" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Bean registration with @Profile: dev profile registers H2DataSource and DataSeeder; prod registers PostgresDataSource only; neither registers beans from the other profile">
  <rect x="8" y="8" width="664" height="294" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Profile — Bean Registration by Active Profile</text>

  <!-- Beans column headers -->
  <text x="180" y="58" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Bean / class</text>
  <text x="390" y="58" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Active: dev</text>
  <text x="550" y="58" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Active: prod</text>

  <!-- Row 1 -->
  <rect x="20" y="66" width="300" height="36" rx="5" fill="#1c2430" stroke="#30363d" stroke-width="1"/>
  <text x="180" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">@Component (no @Profile)</text>
  <text x="180" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">MetricsBean</text>
  <text x="390" y="86" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">✓</text>
  <text x="550" y="86" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">✓</text>

  <!-- Row 2 -->
  <rect x="20" y="110" width="300" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="180" y="124" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@Profile("dev") H2DataSource</text>
  <text x="180" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements DataSource</text>
  <text x="390" y="130" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">✓</text>
  <text x="550" y="130" fill="#f85149" font-size="14" text-anchor="middle" font-family="sans-serif">✗</text>

  <!-- Row 3 -->
  <rect x="20" y="154" width="300" height="36" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="180" y="168" fill="#f0883e" font-size="10" text-anchor="middle" font-family="monospace">@Profile("prod") PostgresDataSource</text>
  <text x="180" y="182" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">implements DataSource</text>
  <text x="390" y="174" fill="#f85149" font-size="14" text-anchor="middle" font-family="sans-serif">✗</text>
  <text x="550" y="174" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">✓</text>

  <!-- Row 4 -->
  <rect x="20" y="198" width="300" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="180" y="212" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">@Profile("!prod") DataSeeder</text>
  <text x="180" y="226" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">seeds DB on startup</text>
  <text x="390" y="218" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">✓</text>
  <text x="550" y="218" fill="#f85149" font-size="14" text-anchor="middle" font-family="sans-serif">✗</text>

  <!-- Row 5 -->
  <rect x="20" y="242" width="300" height="36" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="180" y="256" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">@Profile({"prod","staging"})</text>
  <text x="180" y="270" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AuditLogger (prod OR staging)</text>
  <text x="390" y="262" fill="#f85149" font-size="14" text-anchor="middle" font-family="sans-serif">✗</text>
  <text x="550" y="262" fill="#6db33f" font-size="14" text-anchor="middle" font-family="sans-serif">✓</text>
</svg>

A single interface (`DataSource`) has two implementations; exactly one is active per environment based on `@Profile`.

## 5. Runnable example

```java
// ProfileOnBeans.java — run: java ProfileOnBeans.java  (JDK 17+)
// Simulates @Profile bean selection with two DataSource implementations,
// a dev-only DataSeeder, and an OR-profile AuditLogger.

import java.util.*;

public class ProfileOnBeans {

    // ── Interfaces ───────────────────────────────────────────────────────────

    interface DataSource { String url(); }
    interface EmailService { String send(String to, String body); }

    // ── Implementations (imagine @Profile annotations on each) ───────────────

    // @Profile("dev")
    static class H2DataSource implements DataSource {
        public String url() { return "jdbc:h2:mem:devdb"; }
    }

    // @Profile("prod")
    static class PostgresDataSource implements DataSource {
        public String url() { return "jdbc:postgresql://prod.example.com/app"; }
    }

    // @Profile("test")
    static class MockEmailService implements EmailService {
        public String send(String to, String body) {
            return "[MOCK] Would send to " + to + ": " + body;
        }
    }

    // @Profile("!test")
    static class SmtpEmailService implements EmailService {
        public String send(String to, String body) {
            return "[SMTP] Sending to " + to + ": " + body;
        }
    }

    // @Profile("!prod")  — dev-only bean
    static class DataSeeder {
        void seed() { System.out.println("DataSeeder: seeding dev data..."); }
    }

    // @Profile({"prod","staging"})  — OR condition
    static class AuditLogger {
        void log(String event) { System.out.println("AUDIT: " + event); }
    }

    // ── Simulated context ────────────────────────────────────────────────────

    static void run(List<String> active) {
        System.out.println("─── Active profiles: " + active + " ───");

        // DataSource: exactly one of these two beans is created
        DataSource ds = active.contains("prod")
                ? new PostgresDataSource()
                : new H2DataSource();
        System.out.println("DataSource URL: " + ds.url());

        // EmailService: Mock in test, real otherwise
        EmailService email = active.contains("test")
                ? new MockEmailService()
                : new SmtpEmailService();
        System.out.println(email.send("alice@example.com", "Hello"));

        // DataSeeder: only when prod is NOT active
        if (!active.contains("prod")) new DataSeeder().seed();

        // AuditLogger: prod OR staging
        if (active.contains("prod") || active.contains("staging"))
            new AuditLogger().log("application started");

        System.out.println();
    }

    public static void main(String[] args) {
        run(List.of("dev"));
        run(List.of("prod"));
        run(List.of("test"));
        run(List.of("staging"));
    }
}
```

**How to run:** `java ProfileOnBeans.java`

## 6. Walkthrough

- `H2DataSource` and `PostgresDataSource` both implement `DataSource`. In real Spring Boot you'd annotate them `@Profile("dev")` and `@Profile("prod")` respectively; Spring would register exactly one. The simulation uses an inline ternary to represent that choice.
- `MockEmailService` vs. `SmtpEmailService` — the test profile pattern. In integration tests annotated `@ActiveProfiles("test")`, only the mock is registered, so real SMTP calls never happen.
- `DataSeeder` uses `@Profile("!prod")`. The `!` negation means "active in any profile that is not prod" — no need to list `dev`, `test`, `staging` explicitly. When a new environment profile is added later, `!prod` continues to work correctly.
- `AuditLogger` with `@Profile({"prod","staging"})` — the array form is an OR expression. You want audit logging in staging (for QA review) and in production, but not in dev where the noise would be distracting.
- **No bean for the wrong profile.** In `run(List.of("test"))`, neither `DataSeeder` nor `AuditLogger` is created. In real Spring Boot, attempting to inject either would throw `NoSuchBeanDefinitionException` unless the injection point is `@Autowired(required = false)` or wrapped in `Optional<T>`.

## 7. Gotchas & takeaways

> **`@Profile` on a `@Configuration` class applies to every `@Bean` method inside it.** If the class-level profile doesn't match, none of its beans register — not even beans that have no `@Profile` annotation of their own. This is often surprising when a configuration class mixes universal and profile-specific beans. Split them if necessary.

> **Two `@Profile` beans implementing the same interface in the same active profile creates an ambiguous autowiring conflict.** Spring does not automatically pick one — it throws `NoUniqueBeanDefinitionException`. Annotate one with `@Primary`, or use `@Qualifier` at the injection point.

- Use `@Profile` to swap implementations (DataSource, EmailService, cache) between environments; use profile-specific property files to swap values (URLs, credentials) — both tools, different jobs.
- `@Profile("!prod")` is usually better than listing every non-prod profile by name — it stays correct when new profiles are added.
- `@Profile({"a","b"})` is OR; `@Profile("a & b")` (SpEL, Spring 4+) is AND — know the difference.
- `@ActiveProfiles` on a test class is the standard way to activate a profile for `@SpringBootTest`; it triggers `@Profile` evaluation the same way as runtime activation.
- When a profile-conditional bean is missing and its injection point is mandatory, the error is `NoSuchBeanDefinitionException` at startup — not at the point of use.
