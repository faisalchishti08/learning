---
card: spring-boot
gi: 85
slug: profiles-overview
title: Profiles overview
---

## 1. What it is

A **Spring profile** is a named configuration context that you can activate at runtime to switch between different sets of beans and properties. Think of it as a "mode" for your application: `dev`, `test`, `staging`, `prod`, etc.

When a profile is active:
- Beans annotated with `@Profile("name")` are registered.
- Profile-specific properties files (`application-name.properties`) are loaded on top of the default `application.properties`.

When a profile is **not** active, beans declared with that profile are simply absent from the application context.

Spring Boot extends Spring Framework's profile support with auto-loading of profile-specific configuration files and a richer set of ways to activate profiles.

## 2. Why & when

Without profiles you end up with one of two bad options: one config file full of `if-else` branches, or separate build artifacts per environment. Profiles let you keep **one codebase** while letting each environment differ in a controlled, explicit way.

Use profiles when:
- You need a different database URL in `dev` vs. `prod`.
- You want a mock email service locally but a real SMTP server in production.
- You need integration tests (`@SpringBootTest`) to run against an in-memory H2 database while production uses PostgreSQL.
- You want to enable a monitoring bean only in cloud deployments.

The key insight is that profiles drive both **what beans exist** and **what property values those beans receive**.

## 3. Core concept

Every bean and property source in Spring Boot exists in one of three profile-states:

| State | Meaning |
|---|---|
| No profile annotation | Always registered (profile-independent) |
| `@Profile("p")` | Registered only when profile `p` is active |
| `@Profile("!p")` | Registered only when profile `p` is **not** active |

Spring keeps a set of **active profiles** (from environment variables, JVM args, or code) and a set of **default profiles** (used when nothing else is active, defaults to just the profile named `"default"`). Every bean registration or property source load is evaluated against those sets.

Property layering:
```
application.properties          ← always loaded (base)
application-dev.properties      ← loaded when "dev" is active (overrides base)
application-prod.properties     ← loaded when "prod" is active (overrides base)
```

Multiple profiles can be active simultaneously. If both `dev` and `cloud` are active, both `application-dev.properties` and `application-cloud.properties` are loaded. When keys collide, last-loaded wins (controlled by profile order in `spring.profiles.active`).

## 4. Diagram

<svg viewBox="0 0 680 290" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring profile layering: base properties always load, profile-specific files overlay on top, and only matching profile beans register">
  <!-- Background -->
  <rect x="8" y="8" width="664" height="274" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="34" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Profile Layering at Startup</text>

  <!-- Base layer -->
  <rect x="40" y="52" width="280" height="44" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="180" y="71" fill="#8b949e" font-size="11" text-anchor="middle" font-family="monospace">application.properties</text>
  <text x="180" y="87" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">always loaded (base values)</text>

  <!-- Profile-specific layer -->
  <rect x="40" y="110" width="280" height="44" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="180" y="129" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">application-prod.properties</text>
  <text x="180" y="145" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">loaded when "prod" active — overrides base</text>

  <!-- Arrow between layers -->
  <line x1="180" y1="97" x2="180" y2="108" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="3 2"/>

  <!-- Right side: bean selection -->
  <rect x="380" y="52" width="270" height="80" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="515" y="72" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">Bean registration</text>
  <text x="515" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">@Bean  → always</text>
  <text x="515" y="106" fill="#6db33f" font-size="10" text-anchor="middle" font-family="monospace">@Profile("prod") → only in prod</text>
  <text x="515" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="monospace">@Profile("!prod") → skip in prod</text>

  <!-- Active profiles box -->
  <rect x="40" y="185" width="610" height="44" rx="7" fill="#0d1117" stroke="#f0883e" stroke-width="1.5"/>
  <text x="80" y="204" fill="#8b949e" font-size="10" font-family="monospace">Active profiles:</text>
  <text x="200" y="204" fill="#f0883e" font-size="11" font-family="monospace" font-weight="bold">spring.profiles.active=prod,cloud</text>
  <text x="200" y="220" fill="#e6edf3" font-size="10" font-family="sans-serif">Both application-prod.properties and application-cloud.properties are loaded</text>

  <!-- Label arrows -->
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <line x1="323" y1="75" x2="378" y2="90" stroke="#8b949e" stroke-width="1" marker-end="url(#arr)"/>
</svg>

Base properties are always present; active profiles add layers on top. More layers = more overrides.

## 5. Runnable example

```java
// ProfilesDemo.java  — run: java ProfilesDemo.java  (JDK 17+, no Spring needed for this demo)
// This demo simulates the profile-selection logic to show the concept clearly.

public class ProfilesDemo {

    interface DataSource {
        String url();
    }

    // Simulates an always-available bean (no profile restriction)
    static class CommonMetricsBean {
        public String status() { return "Metrics: UP"; }
    }

    // Simulates @Profile("dev") bean
    static class H2DataSource implements DataSource {
        public String url() { return "jdbc:h2:mem:devdb"; }
    }

    // Simulates @Profile("prod") bean
    static class PostgresDataSource implements DataSource {
        public String url() { return "jdbc:postgresql://db.prod.example.com/appdb"; }
    }

    // Simulates @Profile("!prod") bean — present in dev and test, absent in prod
    static class DevToolsBean {
        public String info() { return "DevTools: live-reload active"; }
    }

    public static void main(String[] args) {
        String activeProfile = args.length > 0 ? args[0] : "dev";
        System.out.println("=== Active profile: " + activeProfile + " ===");

        // Always registered
        CommonMetricsBean metrics = new CommonMetricsBean();
        System.out.println(metrics.status());

        // Profile-conditional beans
        DataSource ds = activeProfile.equals("prod")
                ? new PostgresDataSource()
                : new H2DataSource();
        System.out.println("DataSource URL : " + ds.url());

        // Only in non-prod
        if (!activeProfile.equals("prod")) {
            DevToolsBean dt = new DevToolsBean();
            System.out.println(dt.info());
        } else {
            System.out.println("DevTools: NOT active in prod");
        }

        // Simulated profile-specific properties
        String dbPoolSize = activeProfile.equals("prod") ? "20" : "2";
        System.out.println("DB pool size   : " + dbPoolSize
                + "  (from application-" + activeProfile + ".properties)");
    }
}
```

**How to run:**
```
java ProfilesDemo.java           # runs with "dev" profile
java ProfilesDemo.java prod      # runs with "prod" profile
```

## 6. Walkthrough

- `activeProfile = args.length > 0 ? args[0] : "dev"` — mimics `spring.profiles.active`. Defaults to `dev`, overridable via argument.
- `CommonMetricsBean` — no profile restriction, so always constructed. In Spring this is a plain `@Bean` or `@Component` with no `@Profile`.
- `H2DataSource` vs. `PostgresDataSource` — two implementations of `DataSource`. In real Spring Boot you'd annotate each class with `@Profile("dev")` and `@Profile("prod")` respectively, and Spring's context would register exactly one.
- `DevToolsBean` is created for any profile that is not `prod`. The `@Profile("!prod")` negation syntax lets you say "everywhere except production" without listing every other profile.
- `dbPoolSize` simulates how `application-prod.properties` might set `spring.datasource.hikari.maximum-pool-size=20` while `application-dev.properties` uses `2`. In Spring Boot these file-based overrides happen automatically.
- The final `println` shows the resolved value **and its source** — the kind of transparency you get from `spring.config.name` logging at `DEBUG` level.

## 7. Gotchas & takeaways

> **Profiles are additive, not mutually exclusive.** Nothing stops you from activating both `dev` and `prod` at the same time — Spring won't warn you. Adopt a convention (e.g. only one environment profile active) and enforce it in your CI pipeline.

> **The default profile (`"default"`) is active only when no other profile is active.** If you set `spring.profiles.active=dev`, the `"default"` profile is gone — beans annotated `@Profile("default")` will not register. Use `@Profile("!prod")` instead of `@Profile("default")` when you mean "everywhere except production."

- Profiles govern both bean registration and property file loading — they are not just a config flag.
- `application.properties` is **always** loaded; profile-specific files overlay it.
- Multiple profiles can be active at once; order matters when the same key appears in two profile files.
- Use `@Profile("!prod")` for "development-only" beans rather than listing every non-prod environment.
- The active profiles are printed at startup (`INFO o.s.b.SpringApplication - The following profiles are active: …`) — check logs early when debugging unexpected bean wiring.
