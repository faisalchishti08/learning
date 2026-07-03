---
card: spring-framework
gi: 120
slug: proxybeanmethods-attribute
title: "proxyBeanMethods attribute"
---

## 1. What it is

`@Configuration(proxyBeanMethods = false)` is the official Spring switch that opts a `@Configuration` class out of CGLIB subclassing. When `true` (the default), Spring wraps the config class in a CGLIB proxy so that inter-`@Bean` method calls return singletons. When `false`, no proxy is created — the class behaves exactly like `@Component` in lite mode.

```java
@Configuration(proxyBeanMethods = false)  // no CGLIB — lite mode
class LightweightConfig { ... }
```

## 2. Why & when

Set `proxyBeanMethods = false` when:

- **GraalVM native images** — CGLIB proxies are hard to AOT-compile; Spring Boot 3 auto-configurations default to `false` for this reason.
- **Startup performance** — skipping CGLIB proxy generation shaves startup time in large apps with many config classes.
- **No inter-`@Bean` method calls** — if all dependencies flow via parameters, the CGLIB overhead is pure waste.
- **Library / auto-configuration** — your config class is consumed by user apps; you don't want to impose a CGLIB dependency.

Keep `proxyBeanMethods = true` (the default) when:
- Config methods call each other and you want the singleton guarantee.
- You haven't thought about it yet — the default is safe.

## 3. Core concept

The attribute maps directly to `AbstractBeanDefinition.methodOverrides` — when `proxyBeanMethods = true`, Spring registers `MethodOverride` entries for every `@Bean` method, and the CGLIB subclass overrides those methods to intercept calls. When `false`, no overrides are registered, so no CGLIB subclass is generated.

Startup sequence comparison:

| Step | `proxyBeanMethods = true` | `proxyBeanMethods = false` |
|---|---|---|
| Config class detected | yes | yes |
| CGLIB subclass generated | yes (at startup) | no |
| Inter-`@Bean` call | → singleton from registry | → new Java object |
| Parameter injection | works | works (preferred) |
| Graal native | problematic | compatible |

The rest of the `@Configuration` processing — `@Import`, `@ComponentScan`, `@Bean` registration — is identical in both modes.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- proxyBeanMethods=true -->
  <rect x="10" y="30" width="200" height="75" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">proxyBeanMethods=true</text>
  <text x="110" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">CGLIB subclass generated</text>
  <text x="110" y="86" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">a() → b() → singleton</text>
  <text x="110" y="100" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ safe inter-bean calls</text>

  <!-- proxyBeanMethods=false -->
  <rect x="10" y="120" width="200" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="142" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">proxyBeanMethods=false</text>
  <text x="110" y="160" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no CGLIB — plain class</text>
  <text x="110" y="176" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">use param injection</text>

  <!-- ConfigClassPostProcessor -->
  <rect x="295" y="50" width="190" height="100" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="390" y="75" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">ConfigClassPostProcessor</text>
  <text x="390" y="95" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads proxyBeanMethods flag</text>
  <text x="390" y="115" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">true → enhanceConfigClasses()</text>
  <text x="390" y="132" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">false → skip enhancement</text>

  <line x1="212" y1="68" x2="292" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a120)"/>
  <line x1="212" y1="152" x2="292" y2="130" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b120)"/>
  <defs>
    <marker id="a120" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b120" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Outcome -->
  <rect x="548" y="65" width="142" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="619" y="87" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Result</text>
  <text x="619" y="105" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">true → $$SpringCGLIB</text>
  <text x="619" y="121" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">false → plain class</text>
  <line x1="487" y1="100" x2="545" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c120)"/>
  <defs><marker id="c120" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>

  <text x="350" y="192" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Flag read by ConfigurationClassPostProcessor — determines whether CGLIB enhancement runs</text>
</svg>

`proxyBeanMethods` tells `ConfigurationClassPostProcessor` whether to CGLIB-enhance the config class.

## 5. Runnable example

### Level 1 — Basic

Side-by-side comparison: `true` vs `false` on the same config structure, counting instances.

```java
// ProxyBeanMethodsBasic.java
import org.springframework.context.annotation.*;

class Worker {
    static int instances = 0;
    final int id;
    Worker() { this.id = ++instances; System.out.println("[Worker] #" + id + " created"); }
    public String work() { return "Worker#" + id; }
}

@Configuration(proxyBeanMethods = true)   // default — CGLIB
class ProxyOn {
    @Bean public Worker worker() { return new Worker(); }
    @Bean public String taskA() { return "taskA uses " + worker().work(); }  // → singleton
    @Bean public String taskB() { return "taskB uses " + worker().work(); }  // → same singleton
}

@Configuration(proxyBeanMethods = false)  // lite mode — no CGLIB
class ProxyOff {
    @Bean public Worker worker2() { return new Worker(); }
    @Bean public String task2A() { return "task2A uses " + worker2().work(); }  // → new Worker!
    @Bean public String task2B() { return "task2B uses " + worker2().work(); }  // → new Worker!
}

public class ProxyBeanMethodsBasic {
    public static void main(String[] args) {
        Worker.instances = 0;
        System.out.println("=== proxyBeanMethods=true ===");
        var on = new AnnotationConfigApplicationContext(ProxyOn.class);
        System.out.println(on.getBean("taskA", String.class));
        System.out.println(on.getBean("taskB", String.class));
        System.out.println("Worker instances: " + Worker.instances);   // 1
        // Config class is CGLIB subclass:
        System.out.println("Config class: " + on.getBean(ProxyOn.class).getClass().getSimpleName());
        on.close();

        Worker.instances = 0;
        System.out.println("\n=== proxyBeanMethods=false ===");
        var off = new AnnotationConfigApplicationContext(ProxyOff.class);
        System.out.println(off.getBean("task2A", String.class));
        System.out.println(off.getBean("task2B", String.class));
        System.out.println("Worker instances: " + Worker.instances);   // 3
        System.out.println("Config class: " + off.getBean(ProxyOff.class).getClass().getSimpleName());
        off.close();
    }
}
```

How to run: `java ProxyBeanMethodsBasic.java`

`true` → config class name contains `$$SpringCGLIB$$`, one `Worker` instance. `false` → plain `ProxyOff` class name, three `Worker` instances (one per call).

### Level 2 — Intermediate

`proxyBeanMethods = false` used correctly with parameter injection — safe singleton sharing.

```java
// ProxyBeanMethodsFixed.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;

class Cache {
    static int instances = 0;
    final int id;
    Cache() { this.id = ++instances; System.out.println("[Cache] #" + id + " created"); }
    public String get(String k) { return "[cache#" + id + "] " + k; }
    public void put(String k, String v) { System.out.println("[cache#" + id + "] put " + k + "=" + v); }
}

// proxyBeanMethods=false — no CGLIB, no inter-method calls, only params
@Configuration(proxyBeanMethods = false)
class SafeConfig {
    @Bean public Cache cache() { return new Cache(); }

    @Bean public UserService userService(Cache c) {
        return new UserService(c);           // c injected by Spring — singleton
    }

    @Bean public ProductService productService(Cache c) {
        return new ProductService(c);        // same c singleton
    }

    @Bean public ShoppingCart cart(UserService us, ProductService ps) {
        return new ShoppingCart(us, ps);
    }
}

class UserService {
    final Cache cache;
    UserService(Cache c) { this.cache = c; }
    public String getUser(int id) {
        String v = cache.get("u:" + id);
        return "User:" + id + " via " + v;
    }
}

class ProductService {
    final Cache cache;
    ProductService(Cache c) { this.cache = c; }
    public void cacheProduct(int id, String name) { cache.put("p:" + id, name); }
    public String getProduct(int id) { return cache.get("p:" + id); }
}

class ShoppingCart {
    final UserService us; final ProductService ps;
    ShoppingCart(UserService u, ProductService p) { this.us = u; this.ps = p; }
    public void addToCart(int userId, int productId) {
        System.out.println(us.getUser(userId) + " added " + ps.getProduct(productId));
    }
}

public class ProxyBeanMethodsFixed {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(SafeConfig.class);
        var cart = ctx.getBean(ShoppingCart.class);

        ctx.getBean(ProductService.class).cacheProduct(5, "Widget");
        cart.addToCart(42, 5);

        System.out.println("Cache instances: " + Cache.instances);  // 1
        ctx.close();
    }
}
```

How to run: `java ProxyBeanMethodsFixed.java`

Despite `proxyBeanMethods = false`, only one `Cache` is created — because all dependencies flow through parameters, not direct method calls.

### Level 3 — Advanced

Measure startup difference: many config classes with `true` vs `false`, illustrating the performance motivation.

```java
// ProxyBeanMethodsPerf.java
import org.springframework.context.annotation.*;
import java.util.*;

// Simulate 5 infrastructure config classes
@Configuration(proxyBeanMethods = true)
class InfraCfg1 { @Bean String b1() { return "b1"; } @Bean String b1b(){ return "b1b"+ b1();} }
@Configuration(proxyBeanMethods = true)
class InfraCfg2 { @Bean String b2() { return "b2"; } @Bean String b2b(){ return "b2b"+ b2();} }
@Configuration(proxyBeanMethods = true)
class InfraCfg3 { @Bean String b3() { return "b3"; } @Bean String b3b(){ return "b3b"+ b3();} }

// Same classes with proxyBeanMethods=false
@Configuration(proxyBeanMethods = false)
class LiteCfg1 { @Bean String c1() { return "c1"; } @Bean String c1b(String c1){ return "c1b"+c1;} }
@Configuration(proxyBeanMethods = false)
class LiteCfg2 { @Bean String c2() { return "c2"; } @Bean String c2b(String c2){ return "c2b"+c2;} }
@Configuration(proxyBeanMethods = false)
class LiteCfg3 { @Bean String c3() { return "c3"; } @Bean String c3b(String c3){ return "c3b"+c3;} }

@Configuration
@Import({InfraCfg1.class, InfraCfg2.class, InfraCfg3.class})
class WithProxy {}

@Configuration
@Import({LiteCfg1.class, LiteCfg2.class, LiteCfg3.class})
class WithoutProxy {}

public class ProxyBeanMethodsPerf {
    public static void main(String[] args) {
        // Warm up JVM
        new AnnotationConfigApplicationContext(WithProxy.class).close();
        new AnnotationConfigApplicationContext(WithoutProxy.class).close();

        int runs = 5;
        long totalProxy = 0, totalLite = 0;
        for (int i = 0; i < runs; i++) {
            long t0 = System.nanoTime();
            new AnnotationConfigApplicationContext(WithProxy.class).close();
            totalProxy += System.nanoTime() - t0;

            long t1 = System.nanoTime();
            new AnnotationConfigApplicationContext(WithoutProxy.class).close();
            totalLite += System.nanoTime() - t1;
        }

        System.out.printf("proxyBeanMethods=true  avg: %.2f ms%n", totalProxy / runs / 1_000_000.0);
        System.out.printf("proxyBeanMethods=false avg: %.2f ms%n", totalLite  / runs / 1_000_000.0);
        System.out.println("(difference grows with more config classes in production apps)");

        // Verify config class identity
        var proxyCtx = new AnnotationConfigApplicationContext(WithProxy.class);
        var liteCtx  = new AnnotationConfigApplicationContext(WithoutProxy.class);
        System.out.println("\nWithProxy InfraCfg1: " + proxyCtx.getBean(InfraCfg1.class).getClass().getSimpleName());
        System.out.println("WithoutProxy LiteCfg1: " + liteCtx.getBean(LiteCfg1.class).getClass().getSimpleName());
        proxyCtx.close(); liteCtx.close();
    }
}
```

How to run: `java ProxyBeanMethodsPerf.java`

The timing shows `proxyBeanMethods=false` is faster. The class-name printout confirms the proxy vs plain class difference.

## 6. Walkthrough

Execution for Level 1 `true` path:

1. **`AnnotationConfigApplicationContext(ProxyOn.class)` created** — `ConfigurationClassPostProcessor` detects `@Configuration(proxyBeanMethods = true)` (the default).
2. **CGLIB enhancement** — `ProxyOn` is subclassed as `ProxyOn$$SpringCGLIB$$0`. The `worker()` method is overridden to check the bean registry.
3. **`worker()` called by Spring** to create the `worker` bean → `new Worker()` (Worker#1).
4. **`taskA()` called** — calls `worker()` on the CGLIB proxy → registry check → returns Worker#1.
5. **`taskB()` called** — same proxy intercept → same Worker#1.
6. Total Worker instances: **1**.

Execution for `false` path:

1. **`ConfigurationClassPostProcessor` reads `proxyBeanMethods = false`** — skips CGLIB enhancement. `ProxyOff` class used as-is.
2. **`worker2()` called by Spring** → Worker#1 registered as `worker2` bean.
3. **`task2A()` called** — calls `worker2()` as a plain Java method → `new Worker()` = Worker#2. NOT the bean in the registry.
4. **`task2B()` called** — same plain Java call → `new Worker()` = Worker#3.
5. Total Worker instances: **3** (one in registry, two discarded).

## 7. Gotchas & takeaways

> When `proxyBeanMethods = false`, the method return value for inter-method calls is a fresh Java object, NOT the bean in the context. This is the only behavioural difference — everything else (lifecycle, `@Scope`, `@Import`, `@Autowired`) works identically.

> Spring Boot auto-configuration starter classes use `proxyBeanMethods = false` by default since Spring Boot 2.2. If you copy a `@Configuration` class from the internet that uses method calls between `@Bean` methods, adding `proxyBeanMethods = false` will silently break it.

- `@Configuration` without the attribute = `proxyBeanMethods = true` = CGLIB proxy = safe inter-bean calls.
- `@Configuration(proxyBeanMethods = false)` = lite mode = no CGLIB = use param injection.
- `@Component` is always lite mode — same as `proxyBeanMethods = false`.
- The class cannot be `final` with `proxyBeanMethods = true` (CGLIB needs to subclass it).
- Spring Framework 5.2+ introduced `proxyBeanMethods`; before that, all `@Configuration` classes were always proxied.
