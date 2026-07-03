---
card: spring-framework
gi: 176
slug: aot-vs-jit
title: AOT vs JIT
---

## 1. What it is

**JIT (Just-in-Time)** and **AOT (Ahead-of-Time)** describe *when* compilation happens:

- **JIT** — the JVM starts with bytecode and compiles hot code paths to native machine code *during* the run, optimising based on observed runtime behaviour. The JVM C2 compiler is Java's traditional JIT.
- **AOT** — code is compiled to native machine code *before* the program runs. For Java, GraalVM `native-image` does this: it analyses the entire application at build time and produces a standalone native binary.

In the Spring context, "AOT" also refers to Spring's build-time processing (generating `__BeanDefinitions` sources), which feeds into native image compilation but also helps JVM startup speed.

## 2. Why & when

| Concern | JIT (JVM) | AOT (native) |
|---|---|---|
| Cold start | seconds (JVM boot + JIT warm-up) | milliseconds (already compiled) |
| Memory footprint | higher (JVM + JIT buffers + metaspace) | lower (no JVM overhead) |
| Peak throughput | higher (JIT optimises hotspots) | lower (static compilation, less profiling) |
| Dynamic features | full (reflection, dynamic proxies, runtime class generation) | limited (needs hints; some are impossible) |
| Docker image size | larger (JRE included) | smaller (just the native binary) |
| Debugging / profiling | excellent JVM tooling | limited (some tools support native, but less mature) |

**Choose JIT when:** long-running services (compute-heavy APIs, batch workers) where JIT's adaptive optimisation maximises throughput over hours.

**Choose AOT/native when:** serverless functions, short-lived CLI tools, or containers where cold-start latency and memory density are more important than peak throughput.

## 3. Core concept

**JIT compilation lifecycle:**
1. Source → Java bytecode (compiled by `javac` at build time).
2. JVM loads bytecode; interpreter starts running it immediately.
3. JVM profiler identifies hot methods (called >10k times by default).
4. C2 JIT compiler compiles those hot methods to optimised native code (inlining, loop unrolling, escape analysis…).
5. App runs at near-native speed after warm-up (typically 1–30 seconds of traffic).

**AOT compilation lifecycle:**
1. Source → Java bytecode (as usual).
2. `native-image` tool performs **static reachability analysis** from `main()`: follows every method call, includes all reachable classes.
3. Compiles all reachable bytecode to native machine code at build time (takes minutes).
4. Produces a standalone native binary — no JVM needed at runtime.
5. Binary starts in milliseconds; no warm-up.

**The trade-off:** JIT can inline across call sites it observed *in this run* (adaptive), while AOT's optimisations are fixed at build time (conservative). A long-lived JVM service optimised by its own production traffic often outperforms an equivalent native binary after warm-up.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="ja176" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="aa176" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- JIT timeline -->
  <rect x="5" y="5" width="330" height="220" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="170" y="24" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">JIT Compilation Path</text>

  <rect x="20" y="32" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.2"/>
  <text x="85" y="46" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Source → javac → .class</text>

  <line x1="85" y1="53" x2="85" y2="67" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ja176)"/>
  <rect x="20" y="68" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.2"/>
  <text x="85" y="82" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JVM loads bytecode</text>

  <line x1="85" y1="89" x2="85" y2="103" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ja176)"/>
  <rect x="20" y="104" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.2"/>
  <text x="85" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Interpreter runs bytecode</text>

  <line x1="85" y1="125" x2="85" y2="139" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ja176)"/>
  <rect x="20" y="140" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.3"/>
  <text x="85" y="154" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">C2 JIT: hot path → native</text>

  <line x1="85" y1="161" x2="85" y2="175" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ja176)"/>
  <rect x="20" y="176" width="130" height="20" rx="3" fill="#79c0ff" opacity="0.2"/>
  <text x="85" y="190" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Near-native after warm-up</text>

  <text x="190" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Build time:</text>
  <text x="190" y="92" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">seconds</text>
  <text x="190" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Cold start:</text>
  <text x="190" y="132" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">1–10 s</text>
  <text x="190" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Peak throughput:</text>
  <text x="190" y="172" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">highest</text>
  <text x="190" y="195" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Dynamic features:</text>
  <text x="190" y="207" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">full</text>

  <!-- AOT timeline -->
  <rect x="360" y="5" width="335" height="220" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="527" y="24" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">AOT / Native Image Path</text>

  <rect x="375" y="32" width="145" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="447" y="46" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Source → javac → .class</text>

  <line x1="447" y1="53" x2="447" y2="67" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aa176)"/>
  <rect x="375" y="68" width="145" height="20" rx="3" fill="#6db33f" opacity="0.3"/>
  <text x="447" y="82" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">native-image (build: minutes)</text>

  <line x1="447" y1="89" x2="447" y2="103" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aa176)"/>
  <rect x="375" y="104" width="145" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="447" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Standalone native binary</text>

  <line x1="447" y1="125" x2="447" y2="139" stroke="#6db33f" stroke-width="1.5" marker-end="url(#aa176)"/>
  <rect x="375" y="140" width="145" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="447" y="154" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Instant start (no JVM)</text>

  <rect x="375" y="176" width="145" height="20" rx="3" fill="#6db33f" opacity="0.2"/>
  <text x="447" y="190" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Fixed throughput, low memory</text>

  <text x="557" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Build time:</text>
  <text x="557" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">minutes</text>
  <text x="557" y="120" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Cold start:</text>
  <text x="557" y="132" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">&lt; 100 ms</text>
  <text x="557" y="160" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Peak throughput:</text>
  <text x="557" y="172" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">lower (static)</text>
  <text x="557" y="195" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Dynamic features:</text>
  <text x="557" y="207" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">limited (hints required)</text>
</svg>

JIT trades slow cold start for maximum long-run throughput; AOT/native trades build-time minutes for sub-100ms cold starts and lower memory.

## 5. Runnable example

The scenario is a **greeting service** deployed two ways: as a JVM app (JIT) and as a native-style binary (AOT). The same logic; different compilation strategies.

### Level 1 — Basic

A simple Spring service running on the JVM — the JIT baseline. Startup time is measured.

```java
// AotVsJitBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service
class GreetService {
    public String greet(String name) {
        return "Hello, " + name + "! (JVM / JIT)";
    }
}

@Configuration
@ComponentScan
class JitConfig { }

public class AotVsJitBasic {
    public static void main(String[] args) {
        long t0 = System.currentTimeMillis();
        var ctx = new AnnotationConfigApplicationContext(JitConfig.class);
        long startMs = System.currentTimeMillis() - t0;

        GreetService svc = ctx.getBean(GreetService.class);
        System.out.println(svc.greet("Alice"));
        System.out.printf("Context startup: %d ms (JVM path — classpath scan + reflection)%n", startMs);

        // Simulate a hot loop: JIT will compile greet() after ~10k calls
        long hot0 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) svc.greet("Bob");
        long hotNs = System.nanoTime() - hot0;
        System.out.printf("100k greet() calls: %d ms%n", hotNs / 1_000_000);

        ctx.close();
    }
}
```

How to run: `java AotVsJitBasic.java`

The first `System.currentTimeMillis()` gap shows JVM startup + Spring context init time including classpath scanning. The `100k` loop triggers the JIT: C2 will detect that `greet()` is hot, inline the string concatenation, and compile it to optimised native code. After a few thousand iterations, the native code runs much faster than the first few interpreted calls.

### Level 2 — Intermediate

Compare interpreted (cold) vs JIT-compiled (warm) throughput; then show what AOT-style registration removes from startup.

```java
// AotVsJitIntermediate.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.support.*;
import org.springframework.stereotype.*;

class GreetServiceAot {
    // No Spring annotations — registered programmatically (like AOT generates)
    public String greet(String name) { return "Hello, " + name + "! (AOT-style)"; }
}

public class AotVsJitIntermediate {
    public static void main(String[] args) {
        // --- JVM path: AnnotationConfigApplicationContext with scan ---
        long t0 = System.currentTimeMillis();
        var scanCtx = new org.springframework.context.annotation.AnnotationConfigApplicationContext();
        scanCtx.register(GreetServiceAot.class);
        scanCtx.refresh();
        long jvmStartMs = System.currentTimeMillis() - t0;

        // --- AOT-style path: programmatic registration (no scan) ---
        t0 = System.currentTimeMillis();
        var factory = new DefaultListableBeanFactory();
        var bd = new RootBeanDefinition(GreetServiceAot.class);
        bd.setInstanceSupplier(GreetServiceAot::new);
        factory.registerBeanDefinition("greetService", bd);
        var aotCtx = new GenericApplicationContext(factory);
        aotCtx.refresh();
        long aotStartMs = System.currentTimeMillis() - t0;

        System.out.printf("Scan-based start:  %d ms%n", jvmStartMs);
        System.out.printf("AOT-style start:   %d ms%n", aotStartMs);
        System.out.println("Result: " +
            aotCtx.getBean(GreetServiceAot.class).greet("Alice"));

        // Throughput comparison: interpreted (first N calls) vs warm (later calls)
        var svc = aotCtx.getBean(GreetServiceAot.class);
        long cold0 = System.nanoTime();
        for (int i = 0; i < 1_000; i++) svc.greet("cold");
        long coldNs = (System.nanoTime() - cold0) / 1_000;

        long warm0 = System.nanoTime();
        for (int i = 0; i < 100_000; i++) svc.greet("warm"); // JIT compiles during this
        for (int i = 0; i < 100_000; i++) svc.greet("warm"); // fully JIT-compiled
        long hotNs = (System.nanoTime() - warm0) / 200_000;  // per-call ns

        System.out.printf("Cold (interpreted):  ~%d ns/call%n", coldNs);
        System.out.printf("Warm (JIT compiled): ~%d ns/call%n", hotNs);

        scanCtx.close(); aotCtx.close();
    }
}
```

How to run: `java AotVsJitIntermediate.java`

The AOT-style registration uses `setInstanceSupplier(GreetServiceAot::new)` — a method reference the JVM can call directly without reflection, reducing startup work. The throughput comparison shows the per-call cost dropping as JIT kicks in: the first 1,000 calls are interpreted; after ~10,000+ calls the C2 JIT has compiled `greet()` to native code and per-call overhead drops dramatically.

### Level 3 — Advanced

A Spring Boot app configured for both JVM and native profiles — the same code targets both compilation strategies.

```java
// AotVsJitAdvanced.java — Spring Boot app; run as JVM or native
// JVM:    ./mvnw spring-boot:run
// Native: ./mvnw -Pnative native:compile && ./target/app
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;

@Service
class ProductService {
    public String describe(String id) {
        return "Product " + id + " [image:native=" +
            (System.getProperty("org.graalvm.nativeimage.imagecode") != null) + "]";
    }
}

@RestController
class ProductController {
    private final ProductService svc;
    ProductController(ProductService svc) { this.svc = svc; }

    @GetMapping("/product/{id}")
    public String product(@PathVariable String id) { return svc.describe(id); }
}

@SpringBootApplication
public class AotVsJitAdvanced {
    public static void main(String[] args) {
        long t0 = System.currentTimeMillis();
        var app = SpringApplication.run(AotVsJitAdvanced.class, args);
        long startMs = System.currentTimeMillis() - t0;
        // JVM start: ~1-3s; native start: ~50-150ms
        System.out.printf("Started in %d ms%n", startMs);
    }
}
```

How to run (JVM): `./mvnw spring-boot:run` — startup ~1–3 s

How to run (native): `./mvnw -Pnative native:compile && ./target/aot-vs-jit` — startup <150 ms

`System.getProperty("org.graalvm.nativeimage.imagecode")` is non-null inside a native image, so the `describe` method can report which path it's running on. The same source file targets both modes; the Spring Boot AOT plugin handles generating the bean definitions and reflection hints transparently.

## 6. Walkthrough

Tracing request `GET /product/42` on **JVM** vs **native**:

**JVM path (with JIT):**

1. **App startup (1–3s):** JVM starts, Spring scans `@SpringBootApplication`, finds `ProductService` and `ProductController` via reflection, creates `BeanDefinition` objects, wires the context.
2. **First request arrives:** Tomcat receives `GET /product/42`, dispatches to `DispatcherServlet`.
3. **Interpreted execution (first ~100 requests):** `ProductController.product("42")` is called as interpreted bytecode; JVM records call counts.
4. **JIT kicks in (~1,000 calls):** C2 identifies `product()` as hot, inlines `svc.describe()`, optimises string concatenation, emits native machine code.
5. **Warm throughput:** subsequent calls execute the compiled native code — sub-microsecond per request.

**Native path (with AOT):**

1. **Build (minutes):** `native-image` analyses all reachable code, `__BeanDefinitions` sources are included, reflect-config included, produces binary `./target/app`.
2. **App startup (<150ms):** binary runs (no JVM boot), Spring calls the pre-generated `ApplicationContextInitializer` (no scanning), beans are instantiated directly via supplier references.
3. **First request arrives:** same Tomcat/DispatcherServlet path.
4. **Execution from request 1:** already compiled native code — first request is as fast as the millionth on JVM.
5. **No warm-up curve:** throughput is flat from the start (at a lower ceiling than peak-JIT).

```
        Throughput
           ▲
    peak ─ │          ....JIT (warm)
           │         /
           │        /
  native ─ │───────────────────── AOT native (flat from start)
           │      /
           │...../ JIT (cold)
           └──────────────────────▶ Time / Requests
```

The crossing point where JIT surpasses native in throughput varies by workload — typically a few minutes of steady traffic for a compute-intensive service.

## 7. Gotchas & takeaways

> **Native image build time is not deploy time.** `native-image` takes minutes — this is a build-step, run in CI, not at runtime. The resulting binary deploys in milliseconds. Factor CI time into your pipeline planning.

> **"AOT is always faster" is wrong.** AOT is faster to *start*. A JVM that has run for 10 minutes with JIT enabled may serve requests faster than the equivalent native binary, because JIT can apply profile-guided optimisations the static compiler cannot.

- Use native/AOT for: Lambda, serverless, CLI tools, containers scaled to zero (where cold start is billed).
- Use JVM/JIT for: long-running APIs, batch jobs, data pipelines — where warm peak throughput matters more than start time.
- Spring Boot 3's AOT plugin is transparent — the same codebase targets both modes. Switch with a Maven profile (`-Pnative`).
- Memory savings from native are significant in Kubernetes: a Spring Boot service at 50MB native vs 200MB JVM can triple pod density on the same node.
- JVM `GraalVM Community Edition` supports native compilation; production use warrants `GraalVM Enterprise` for better optimisation.
