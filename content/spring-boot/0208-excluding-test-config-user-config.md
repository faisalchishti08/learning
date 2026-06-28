---
card: spring-boot
gi: 208
slug: excluding-test-config-user-config
title: Excluding test config & user config
---

## 1. What it is

By default, `@SpringBootTest` loads everything: all `@Configuration` classes found by component scanning, all auto-configurations, and all user-defined beans. Sometimes tests need a **narrower context** — they want to exclude noisy beans, override specific configurations, or prevent certain auto-configurations from running. Spring Boot provides `@SpringBootTest(excludeAutoConfiguration = ...)`, `@EnableAutoConfiguration(exclude = ...)`, `spring.autoconfigure.exclude`, and the `@Profile` mechanism to control what gets loaded.

## 2. Why & when

Exclude configurations when:
- A test boots up slowly because of a heavy auto-configuration (e.g., full JPA stack) that the test doesn't need.
- A `@Configuration` class fires a side effect (sends email, calls external API) that you can't mock.
- You have a dev-only `@Configuration` (e.g., `DevDataLoader`) that should not run in tests.
- A second `@SpringBootApplication` class in a test module causes ambiguous context detection.

The goal is to **keep tests fast and deterministic** by eliminating irrelevant infrastructure.

## 3. Core concept

**Exclude auto-configuration via annotation:**
```java
@SpringBootTest(excludeAutoConfiguration = {
    SecurityAutoConfiguration.class,
    DataSourceAutoConfiguration.class
})
class NoSecurityNoDbTest { ... }
```

**Exclude via `application-test.properties`:**
```properties
spring.autoconfigure.exclude=\
  org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration
```

**Exclude a user-written `@Configuration`:**
```java
// Problematic config (always sending emails on startup):
@Configuration
@Profile("!test")   // exclude when test profile is active
public class EmailStartupNotifier { ... }
```

**Prevent a test helper from being picked up by the main scan:**
```java
// Test-only @Configuration in src/test/java — must NOT be at root package:
@TestConfiguration           // marks it as test-only, not imported by default
public class MockEmailConfig {
    @Bean EmailService email() { return Mockito.mock(EmailService.class); }
}
```

Note: `@TestConfiguration` does not replace existing beans by default. For that, combine with `@MockitoBean`.

## 4. Diagram

<svg viewBox="0 0 680 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Default @SpringBootTest loads all config; exclusion mechanism filters out specific AutoConfigurations or user @Configuration classes before context is built">
  <!-- All config available -->
  <rect x="10" y="25" width="195" height="160" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="107" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">All Available Config</text>
  <text x="107" y="62" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">SecurityAutoConfiguration</text>
  <text x="107" y="76" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">DataSourceAutoConfiguration</text>
  <text x="107" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">JpaAutoConfiguration</text>
  <text x="107" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">EmailStartupNotifier</text>
  <text x="107" y="118" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">CacheAutoConfiguration</text>
  <text x="107" y="132" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">YourServiceConfig</text>
  <text x="107" y="146" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">ActuatorAutoConfiguration</text>

  <!-- Filter -->
  <rect x="220" y="70" width="145" height="65" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="292" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Exclusion Filter</text>
  <text x="292" y="108" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">excludeAutoConfiguration</text>
  <text x="292" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Profile("!test")</text>
  <text x="292" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">spring.autoconfigure.exclude</text>

  <!-- Lines in -->
  <line x1="207" y1="104" x2="218" y2="104" stroke="#6db33f" stroke-width="1.5" marker-end="url(#eca)"/>

  <!-- Excluded (red X) -->
  <rect x="220" y="150" width="145" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="292" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✗ Excluded: Security, DataSource, Email</text>

  <!-- Context result -->
  <rect x="380" y="30" width="290" height="155" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="525" y="53" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Narrowed Test Context</text>
  <text x="525" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ CacheAutoConfiguration</text>
  <text x="525" y="90" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ YourServiceConfig</text>
  <text x="525" y="107" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ ActuatorAutoConfiguration</text>
  <text x="525" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✗ SecurityAutoConfiguration</text>
  <text x="525" y="143" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✗ DataSourceAutoConfiguration</text>
  <text x="525" y="158" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">✗ EmailStartupNotifier</text>

  <line x1="367" y1="102" x2="378" y2="102" stroke="#6db33f" stroke-width="2" marker-end="url(#ecb)"/>

  <defs>
    <marker id="eca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ecb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The exclusion filter removes specified auto-configurations and profile-excluded beans before the context is built, resulting in a leaner, faster test context.

## 5. Runnable example

```java
// ExcludingConfigDemo.java — simulates configuration exclusion in @SpringBootTest
// How to run: java ExcludingConfigDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: use excludeAutoConfiguration, @Profile, or spring.autoconfigure.exclude

import java.util.*;
import java.util.function.Predicate;

public class ExcludingConfigDemo {

    // Simulates @Configuration classes (auto and user)
    record ConfigClass(String name, String type, String[] requiredProfiles, boolean isAutoConfig) {}

    // Simulates the context builder
    static class TestContextBuilder {
        private final List<ConfigClass> allConfigs;
        private final Set<String>       excludedByAnnotation = new HashSet<>();
        private final Set<String>       excludedByProperty   = new HashSet<>();
        private String activeProfile = "test";

        TestContextBuilder(List<ConfigClass> allConfigs) { this.allConfigs = allConfigs; }

        TestContextBuilder excludeAutoConfig(String... names) {
            excludedByAnnotation.addAll(Arrays.asList(names));
            return this;
        }

        TestContextBuilder excludeViaProperty(String... names) {
            excludedByProperty.addAll(Arrays.asList(names));
            return this;
        }

        TestContextBuilder withProfile(String profile) {
            this.activeProfile = profile;
            return this;
        }

        void build(String testName) {
            System.out.println("\n=== " + testName + " (profile=" + activeProfile + ") ===");
            List<String> loaded  = new ArrayList<>();
            List<String> skipped = new ArrayList<>();

            for (ConfigClass c : allConfigs) {
                // Check exclusions
                if (excludedByAnnotation.contains(c.name())) {
                    skipped.add(c.name() + " [excluded by excludeAutoConfiguration]");
                    continue;
                }
                if (excludedByProperty.contains(c.name())) {
                    skipped.add(c.name() + " [excluded by spring.autoconfigure.exclude]");
                    continue;
                }
                // Check profile condition (simplified: "!test" means not active in test profile)
                boolean profileOk = Arrays.stream(c.requiredProfiles()).allMatch(p -> {
                    if (p.startsWith("!")) return !activeProfile.equals(p.substring(1));
                    return activeProfile.equals(p) || p.isEmpty();
                });
                if (!profileOk) {
                    skipped.add(c.name() + " [@Profile condition not met]");
                    continue;
                }
                loaded.add(c.name() + " [" + c.type() + "]");
            }

            System.out.println("  Loaded (" + loaded.size() + "):");
            loaded.forEach(s -> System.out.println("    ✓ " + s));
            System.out.println("  Skipped (" + skipped.size() + "):");
            skipped.forEach(s -> System.out.println("    ✗ " + s));
        }
    }

    static final List<ConfigClass> ALL_CONFIGS = List.of(
        new ConfigClass("SecurityAutoConfiguration",     "AutoConfig", new String[]{}, true),
        new ConfigClass("DataSourceAutoConfiguration",   "AutoConfig", new String[]{}, true),
        new ConfigClass("JpaAutoConfiguration",          "AutoConfig", new String[]{}, true),
        new ConfigClass("CacheAutoConfiguration",        "AutoConfig", new String[]{}, true),
        new ConfigClass("ActuatorAutoConfiguration",     "AutoConfig", new String[]{}, true),
        new ConfigClass("EmailStartupNotifier",          "UserConfig", new String[]{"!test"}, false),
        new ConfigClass("DevDataLoader",                 "UserConfig", new String[]{"dev"}, false),
        new ConfigClass("OrderServiceConfig",            "UserConfig", new String[]{}, false),
        new ConfigClass("MockEmailConfig",               "TestConfig", new String[]{"test"}, false)
    );

    public static void main(String[] args) {
        System.out.println("=== Excluding Test Config & User Config Demo ===");

        // Test 1: default (load everything)
        new TestContextBuilder(ALL_CONFIGS).withProfile("test").build(
            "Default @SpringBootTest (no exclusions)");

        // Test 2: exclude security and datasource via annotation
        new TestContextBuilder(ALL_CONFIGS)
            .excludeAutoConfig("SecurityAutoConfiguration", "DataSourceAutoConfiguration", "JpaAutoConfiguration")
            .withProfile("test")
            .build("@SpringBootTest(excludeAutoConfiguration={Security,DataSource,Jpa})");

        // Test 3: exclude via property
        new TestContextBuilder(ALL_CONFIGS)
            .excludeViaProperty("SecurityAutoConfiguration")
            .withProfile("test")
            .build("spring.autoconfigure.exclude=SecurityAutoConfiguration (in properties)");

        // Test 4: profile-based exclusion
        new TestContextBuilder(ALL_CONFIGS)
            .withProfile("test")
            .build("@ActiveProfiles(\"test\") — EmailStartupNotifier @Profile(\"!test\") excluded");

        System.out.println("\n--- Real annotation patterns ---");
        System.out.println("""
// Exclude via test annotation:
@SpringBootTest(excludeAutoConfiguration = {
    SecurityAutoConfiguration.class,
    DataSourceAutoConfiguration.class
})

// Exclude via property (application-test.properties):
spring.autoconfigure.exclude=\\
  org.springframework.boot.autoconfigure.security.servlet.SecurityAutoConfiguration

// Exclude user config via profile:
@Configuration
@Profile("!test")
public class EmailStartupNotifier { ... }

// @TestConfiguration: test-only, not imported by default scan:
@TestConfiguration
public class MockEmailConfig {
    @Bean EmailService email() { return mock(EmailService.class); }
}""");
    }
}
```

**How to run:** `java ExcludingConfigDemo.java`

## 6. Walkthrough

- **Default context** (test 1): all 9 configurations load. `EmailStartupNotifier` with `@Profile("!test")` is excluded because the active profile is "test". `DevDataLoader` is excluded because it requires the "dev" profile. So even without explicit exclusion, profile conditions already filter some beans.
- **Exclude by annotation** (test 2): `SecurityAutoConfiguration`, `DataSourceAutoConfiguration`, and `JpaAutoConfiguration` are removed. A test that only needs services and cache now starts significantly faster.
- **Exclude via property** (test 3): same result as test 2 but configured in `application-test.properties` — useful when you can't change the test annotation (e.g., base test class in a library).
- **Profile exclusion** (test 4): `@Profile("!test")` is the idiomatic way to exclude dev-only beans like `EmailStartupNotifier` without changing any test code.

## 7. Gotchas & takeaways

> `@TestConfiguration` is **not automatically scanned**. It must be either in the test class as a static inner class, or explicitly imported with `@Import(MockEmailConfig.class)`. A `@TestConfiguration` placed in `src/test/java` at the root package IS picked up by the main scan — place it in a sub-package or use `@Import` to control loading explicitly.

> `excludeAutoConfiguration` only works for Spring Boot's managed auto-configurations (the ones in `spring.factories` or `AutoConfiguration.imports`). It cannot exclude user-written `@Configuration` classes — use `@Profile` for those.

- `spring.autoconfigure.exclude` in `application.properties` applies globally; put exclusions in `application-test.properties` to limit them to the test profile.
- Use `@ConditionalOnProperty(name = "feature.email.startup", havingValue = "true")` on non-test beans to make them opt-in rather than using `@Profile("!test")`.
- Test context caching: two tests with different `excludeAutoConfiguration` sets use different contexts. Keep exclusion sets consistent in a base class to maximize cache hits.
