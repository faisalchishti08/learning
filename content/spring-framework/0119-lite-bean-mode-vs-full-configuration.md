---
card: spring-framework
gi: 119
slug: lite-bean-mode-vs-full-configuration
title: "Lite @Bean mode (in @Component) vs full @Configuration"
---

## 1. What it is

Spring supports two modes for `@Bean` methods:

- **Full mode** — `@Bean` methods are inside a `@Configuration`-annotated class. Spring wraps the class in a CGLIB subclass. Inter-bean method calls (`serviceA()` calling `serviceB()`) go through the proxy and return the cached singleton.
- **Lite mode** — `@Bean` methods are inside a `@Component` class (or any class that is *not* `@Configuration`). No CGLIB wrapping. Inter-bean method calls are plain Java calls — each call constructs a new object.

The difference is invisible to callers; only internal method-call behaviour changes.

## 2. Why & when

**Use full `@Configuration`** when:
- Config methods call each other to express bean dependencies (`new ServiceA(serviceB())`).
- You need singleton guarantees on shared infrastructure (connection pools, caches).
- CGLIB is acceptable on the classpath.

**Use lite mode** when:
- You want to avoid CGLIB overhead (startup time, classpath dependency, Graal native image constraints).
- Config methods do **not** call each other — each `@Bean` method is self-contained or uses parameter injection for all dependencies.
- You're writing a library or Spring Boot auto-configuration where CGLIB may not be desired.

Spring Boot's auto-configuration classes often use `@Configuration(proxyBeanMethods = false)` — the same as lite mode — for this reason.

## 3. Core concept

Full mode:

```java
@Configuration          // CGLIB subclasses this class
class FullConfig {
    @Bean A a() { return new A(b()); } // b() → singleton via CGLIB
    @Bean B b() { return new B(); }
}
```

Lite mode:

```java
@Component              // NOT subclassed — plain Java
class LiteConfig {
    @Bean A a() { return new A(b()); } // b() → creates NEW B each time!
    @Bean B b() { return new B(); }
}
```

In lite mode, `a()` calling `b()` creates a second `B` that is NOT the Spring-managed bean. If `A` and the context both need the `B` bean, they get different objects — a common bug.

**Safe pattern for lite mode**: use parameter injection for all inter-bean references.

```java
@Component
class LiteConfig {
    @Bean A a(B b) { return new A(b); }  // b injected by Spring — correct singleton
    @Bean B b()    { return new B(); }
}
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <!-- Full mode -->
  <rect x="10" y="30" width="215" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="117" y="52" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Full mode @Configuration</text>
  <text x="117" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">CGLIB subclass active</text>
  <text x="117" y="88" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">a() calls b() → proxy → singleton B</text>
  <text x="117" y="106" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">✓ shared singleton guaranteed</text>

  <!-- Lite mode -->
  <rect x="10" y="135" width="215" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="117" y="157" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Lite mode @Component</text>
  <text x="117" y="175" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no CGLIB — plain Java calls</text>
  <text x="117" y="192" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">a() calls b() → new B() each time</text>

  <!-- Registry -->
  <rect x="320" y="60" width="170" height="95" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="405" y="83" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Bean Registry</text>
  <text x="405" y="103" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">full: a→A(B1)  b→B1</text>
  <text x="405" y="120" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">lite: a→A(B2)  b→B1</text>
  <text x="405" y="137" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">   (B2 ≠ B1 — extra object!)</text>

  <line x1="227" y1="75" x2="317" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a119)"/>
  <line x1="227" y1="165" x2="317" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b119)"/>
  <defs>
    <marker id="a119" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b119" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Fix note -->
  <rect x="510" y="130" width="180" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="600" y="152" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Lite fix: use</text>
  <text x="600" y="167" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">param injection</text>
  <line x1="490" y1="165" x2="508" y2="160" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a119)"/>

  <text x="350" y="200" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">In lite mode, inter-@Bean calls create extra objects — fix with parameter injection</text>
</svg>

Full mode guarantees singleton; lite mode requires parameter injection to avoid stray instances.

## 5. Runnable example

### Level 1 — Basic

Compare full and lite mode side by side: count instances to prove the difference.

```java
// LiteVsFullBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

class Connection {
    private static int count = 0;
    private final int id;
    Connection() { this.id = ++count; System.out.println("[Connection] #" + id + " created"); }
    public int id() { return id; }
}

// ---- FULL MODE ----
@Configuration
class FullCfg {
    @Bean public Connection connection() { return new Connection(); }

    @Bean public String fullA() { return "A uses conn#" + connection().id(); }  // CGLIB → singleton
    @Bean public String fullB() { return "B uses conn#" + connection().id(); }  // same singleton
}

// ---- LITE MODE ----
@Component
class LiteCfg {
    @Bean public Connection liteConn() { return new Connection(); }

    @Bean public String liteA() { return "A uses conn#" + liteConn().id(); }   // plain call → new instance
    @Bean public String liteB() { return "B uses conn#" + liteConn().id(); }   // another new instance
}

public class LiteVsFullBasic {
    public static void main(String[] args) {
        Connection.count = 0;
        System.out.println("=== Full @Configuration ===");
        var full = new AnnotationConfigApplicationContext(FullCfg.class);
        System.out.println(full.getBean("fullA", String.class));
        System.out.println(full.getBean("fullB", String.class));
        System.out.println("Total Connection instances (full): " + Connection.count);  // 1
        full.close();

        Connection.count = 0;
        System.out.println("\n=== Lite @Component ===");
        var lite = new AnnotationConfigApplicationContext(LiteCfg.class);
        System.out.println(lite.getBean("liteA", String.class));
        System.out.println(lite.getBean("liteB", String.class));
        System.out.println("Total Connection instances (lite): " + Connection.count);  // 3 (!!)
        lite.close();
    }
}
```

How to run: `java LiteVsFullBasic.java`

Full mode: `Connection` is created once. Lite mode: `liteConn()` is a plain Java call — each invocation in `liteA()` and `liteB()` creates a new `Connection`, plus the one Spring itself calls to register `liteConn`. Total: 3 instances in lite mode vs 1 in full mode.

### Level 2 — Intermediate

Fix the lite-mode problem using parameter injection — show the count drops to 1.

```java
// LiteFixedParams.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

class Pool {
    private static int count = 0;
    final int id;
    Pool() { this.id = ++count; System.out.println("[Pool] #" + id + " created"); }
}

// Broken lite mode — method calls
@Component
class BrokenLiteCfg {
    @Bean public Pool pool() { return new Pool(); }
    @Bean public String repoA() { return "A→pool#" + pool().id; }   // new Pool each time!
    @Bean public String repoB() { return "B→pool#" + pool().id; }   // another new Pool!
}

// Fixed lite mode — parameter injection
@Component
class FixedLiteCfg {
    @Bean public Pool fixedPool() { return new Pool(); }
    @Bean public String fixedRepoA(Pool p) { return "A→pool#" + p.id; }   // p = singleton
    @Bean public String fixedRepoB(Pool p) { return "B→pool#" + p.id; }   // same singleton
}

public class LiteFixedParams {
    public static void main(String[] args) {
        Pool.count = 0;
        System.out.println("=== BROKEN lite mode ===");
        var broken = new AnnotationConfigApplicationContext(BrokenLiteCfg.class);
        System.out.println(broken.getBean("repoA", String.class));
        System.out.println(broken.getBean("repoB", String.class));
        System.out.println("Pool instances (broken): " + Pool.count);  // > 1
        broken.close();

        Pool.count = 0;
        System.out.println("\n=== FIXED lite mode (param injection) ===");
        var fixed = new AnnotationConfigApplicationContext(FixedLiteCfg.class);
        System.out.println(fixed.getBean("fixedRepoA", String.class));
        System.out.println(fixed.getBean("fixedRepoB", String.class));
        System.out.println("Pool instances (fixed): " + Pool.count);  // 1
        fixed.close();
    }
}
```

How to run: `java LiteFixedParams.java`

Broken lite: multiple `Pool` instances. Fixed lite with parameter injection: one `Pool` singleton. The fix is using `Pool p` as a method parameter instead of calling `pool()` directly.

### Level 3 — Advanced

Real-world scenario: a library config class using lite mode (`@Component`) with `@Bean` methods that correctly use parameter injection — demonstrating the idiomatic pattern for Spring Boot auto-configurations.

```java
// LiteAutoConfig.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// Simulates an auto-configuration shipped by a library (no CGLIB dependency)
@Component  // Not @Configuration — lite mode intentionally
class MetricsAutoConfiguration {
    // Each @Bean method takes its dependencies as parameters — no inter-method calls
    @Bean
    public MetricsRegistry metricsRegistry() {
        System.out.println("[AutoConfig] creating MetricsRegistry");
        return new MetricsRegistry();
    }

    @Bean
    public RequestTimer requestTimer(MetricsRegistry registry) {
        System.out.println("[AutoConfig] creating RequestTimer");
        return new RequestTimer(registry);
    }

    @Bean
    public ErrorCounter errorCounter(MetricsRegistry registry) {
        System.out.println("[AutoConfig] creating ErrorCounter");
        return new ErrorCounter(registry);
    }
}

class MetricsRegistry {
    private static int instances = 0;
    final int id;
    MetricsRegistry() { this.id = ++instances; }
    public void record(String metric, double value) {
        System.out.println("[Registry#" + id + "] " + metric + "=" + value);
    }
}

class RequestTimer {
    private final MetricsRegistry registry;
    RequestTimer(MetricsRegistry r) { this.registry = r; }
    public void time(String op, double ms) { registry.record("timer." + op, ms); }
}

class ErrorCounter {
    private final MetricsRegistry registry;
    ErrorCounter(MetricsRegistry r) { this.registry = r; }
    public void count(String error) { registry.record("error." + error, 1.0); }
}

// Application-level config uses the auto-config via import
@Configuration
@Import(MetricsAutoConfiguration.class)
class AppConfig {}

public class LiteAutoConfig {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);

        ctx.getBean(RequestTimer.class).time("checkout", 42.3);
        ctx.getBean(ErrorCounter.class).count("timeout");

        // Verify single MetricsRegistry
        var r1 = ctx.getBean(RequestTimer.class);
        var r2 = ctx.getBean(ErrorCounter.class);
        System.out.println("MetricsRegistry instances: " + MetricsRegistry.instances);  // 1
        ctx.close();
    }
}
```

How to run: `java LiteAutoConfig.java`

`MetricsAutoConfiguration` uses lite mode but parameter injection — so only one `MetricsRegistry` is created. `RequestTimer` and `ErrorCounter` both receive the same singleton registry.

## 6. Walkthrough

Execution for Level 3:

1. **`AnnotationConfigApplicationContext(AppConfig.class)` created** — `@Import(MetricsAutoConfiguration.class)` adds `MetricsAutoConfiguration` to processing. It's a `@Component`, not `@Configuration` — no CGLIB wrapping.
2. **`metricsRegistry()` called by Spring** — returns `new MetricsRegistry()`. Registered as `"metricsRegistry"`.
3. **`requestTimer(MetricsRegistry registry)` called** — Spring resolves the `MetricsRegistry` param from the context (the singleton from step 2). `new RequestTimer(registry)` created.
4. **`errorCounter(MetricsRegistry registry)` called** — same `MetricsRegistry` singleton injected.
5. **`RequestTimer.time("checkout", 42.3)`** → `registry.record("timer.checkout", 42.3)` → `[Registry#1] timer.checkout=42.3`.
6. **`ErrorCounter.count("timeout")`** → `registry.record("error.timeout", 1.0)` → `[Registry#1] error.timeout=1.0`.
7. **`MetricsRegistry.instances`** → `1` — one registry shared by both `RequestTimer` and `ErrorCounter`.

Expected output:
```
[AutoConfig] creating MetricsRegistry
[AutoConfig] creating RequestTimer
[AutoConfig] creating ErrorCounter
[Registry#1] timer.checkout=42.3
[Registry#1] error.timeout=1.0
MetricsRegistry instances: 1
```

## 7. Gotchas & takeaways

> The lite-mode bug is **silent** — Spring does not warn you if you call `@Bean` methods from other `@Bean` methods in a `@Component`. You get multiple instances without any error. The only way to detect it is by counting instances or inspecting identity with `==`.

> `@Configuration(proxyBeanMethods = false)` is the official "lite mode" toggle. It opts out of CGLIB while keeping the `@Configuration` stereotype (and its implications for `ConfigurationClassPostProcessor`). The effect is the same as using `@Component` — plain Java method calls.

- Rule of thumb: in any config class that is NOT CGLIB-proxied, always use method parameters for inter-bean dependencies, never direct method calls.
- Lite mode starts faster (no CGLIB proxy generation at startup) — relevant in Spring Boot apps with many auto-configurations.
- Native image (GraalVM) compilation requires lite mode because CGLIB proxies cannot be easily ahead-of-time compiled. Spring 6 / Spring Boot 3 auto-configs default to `proxyBeanMethods = false` for this reason.
- You can detect mode at runtime: `ctx.getBean(YourCfg.class).getClass().getName()` — if it contains `$$SpringCGLIB$$`, it's full mode.
