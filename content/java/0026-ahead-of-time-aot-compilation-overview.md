---
card: java
gi: 26
slug: ahead-of-time-aot-compilation-overview
title: Ahead-Of-Time (AOT) compilation overview
---

## 1. What it is

**Ahead-Of-Time (AOT) compilation** translates Java bytecode into native machine code *before* the program runs. The output is a platform-specific binary — no JVM required at runtime. GraalVM Native Image is the primary AOT compiler for Java; the JDK also includes experimental AOT support via `jaotc` (Java 9–16) and the newer JEP 483 Class Data Sharing (CDS) with AOT methods (Java 24+).

AOT is the opposite of JIT: JIT compiles during execution guided by runtime profile data; AOT compiles at build time with static analysis.

## 2. Why & when

AOT suits serverless, CLI tools, and microservice containers — anywhere startup time and memory footprint matter more than peak throughput:

| Concern | JIT | AOT (Native Image) |
|---------|-----|--------------------|
| Startup | 100 ms–5 s (warm-up) | 5–50 ms |
| Peak throughput | Higher (profile-guided) | Lower (no runtime profiling) |
| Memory RSS | 50–200 MB JVM overhead | 10–30 MB |
| Image size | JRE + JAR (~150 MB) | single binary (~30–80 MB) |
| Dynamic class loading | Supported | Limited (closed world) |
| Reflection | Supported | Requires config metadata |

Use AOT when: AWS Lambda cold starts must be < 1 s; CLI tools ship as single binaries; container images must be minimal.

Use JIT when: long-running services need peak throughput; application uses extensive reflection/dynamic proxies.

## 3. Core concept

GraalVM Native Image build process:

```
Java source → javac → .class (bytecode)
                          │
                    native-image tool
                          │
              ┌───────────┴───────────────┐
              │  Static reachability analysis │
              │  (closed-world assumption)    │
              │  ─ which classes are used?    │
              │  ─ which methods reachable?   │
              └───────────┬───────────────┘
                          │
              ┌───────────┴───────────────┐
              │  Compile reachable code to  │
              │  native machine code (x86,  │
              │  ARM, etc.) via LLVM/Graal   │
              └───────────┬───────────────┘
                          │
                    native binary
              (includes substrate VM — a tiny
               runtime for GC, thread mgmt)
```

**Closed World Assumption (CWA):** Native Image must know at build time every class, method, and field that will ever be used. Dynamic features — reflection, `Class.forName`, JNI, proxies, serialisation — require explicit **reachability metadata** (JSON config files listing what's needed dynamically).

**Substrate VM:** The native binary still includes a minimal runtime (Substrate VM) for GC (Serial GC by default, G1 for enterprise), thread management, and signal handling. This is why native images are not truly bare-metal; they are ~20–80 MB rather than 1 MB.

**Tracing agent:** `java -agentlib:native-image-agent=config-output-dir=META-INF/native-image` runs the app with a tracing agent that auto-generates the reflection/proxy/resource config files. Run your full test suite with the agent to capture all dynamic accesses.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="AOT compilation pipeline: bytecode to native binary vs JIT path">
  <rect x="10" y="10" width="660" height="200" rx="8" fill="#0d1117"/>

  <!-- JIT path (top) -->
  <text x="30" y="38" fill="#8b949e" font-size="10" font-family="sans-serif">JIT path (runtime):</text>
  <rect x="30" y="46" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="65" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.class</text>
  <line x1="110" y1="61" x2="145" y2="61" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a1)"/>
  <rect x="145" y="46" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="185" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JVM + JIT</text>
  <line x1="225" y1="61" x2="260" y2="61" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a2)"/>
  <rect x="260" y="46" width="80" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="300" y="65" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">native ops</text>
  <text x="185" y="95" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">startup: 100ms–5s · peak perf: high</text>

  <!-- AOT path (bottom) -->
  <text x="30" y="125" fill="#6db33f" font-size="10" font-family="sans-serif">AOT path (build time):</text>
  <rect x="30" y="133" width="80" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="70" y="152" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.class</text>
  <line x1="110" y1="148" x2="145" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a3)"/>
  <rect x="145" y="133" width="100" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="195" y="152" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">native-image</text>
  <line x1="245" y1="148" x2="280" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a3)"/>
  <rect x="280" y="133" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="325" y="152" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">native binary</text>
  <line x1="370" y1="148" x2="405" y2="148" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a3)"/>
  <rect x="405" y="133" width="90" height="30" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="450" y="152" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">run directly</text>
  <text x="300" y="182" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">startup: &lt;50ms · memory: low · no JVM needed</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#8b949e" stroke-width="1.5"/></marker>
    <marker id="a2" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#79c0ff" stroke-width="1.5"/></marker>
    <marker id="a3" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto"><path d="M0,0 L8,3 L0,6" fill="none" stroke="#6db33f" stroke-width="1.5"/></marker>
  </defs>
</svg>

JIT: `.class` → JVM interprets/compiles at runtime. AOT: `.class` → `native-image` at build time → native binary runs directly.

## 5. Runnable example

Scenario: a program that detects whether it is running as a GraalVM native image or under a standard JVM — and reports key platform differences.

### Level 1 — Basic

```java
// AotDetector.java
public class AotDetector {
    public static void main(String[] args) {
        // GraalVM sets this property to "true" in native images
        boolean isNative = Boolean.getBoolean("com.oracle.graalvm.isaot");

        System.out.println("=== AOT vs JIT Runtime Detection ===\n");
        System.out.println("Running as native image : " + isNative);
        System.out.println("Java home               : " + System.getProperty("java.home"));
        System.out.println("VM name                 : " + System.getProperty("java.vm.name"));
        System.out.println("VM vendor               : " + System.getProperty("java.vm.vendor"));

        if (isNative) {
            System.out.println("\nRunning as GraalVM Native Image:");
            System.out.println("  - No JIT compiler present");
            System.out.println("  - Substrate VM handles GC & threads");
            System.out.println("  - All code was compiled at build time");
        } else {
            System.out.println("\nRunning on JVM (JIT mode):");
            System.out.println("  - HotSpot JIT will compile hot methods");
            System.out.println("  - Dynamic class loading supported");
            System.out.println("  - Reflection works without config files");
        }
    }
}
```

**How to run:** `java AotDetector.java`

When compiled with GraalVM Native Image (`native-image AotDetector`) and executed, `com.oracle.graalvm.isaot` is `true`. On a regular JVM it's `false`.

### Level 2 — Intermediate

Same detector grown to benchmark startup-time proxy: measures the JVM process start time from `main()` entry — showing what's already "free" before your code runs in native vs JIT mode.

```java
// StartupBench.java
import java.lang.management.*;
import java.util.*;

public class StartupBench {
    public static void main(String[] args) {
        long mainStartMs = System.currentTimeMillis();

        RuntimeMXBean rtBean = ManagementFactory.getRuntimeMXBean();
        long jvmStartMs = rtBean.getStartTime();
        long uptimeMs   = rtBean.getUptime();

        System.out.println("=== Startup Time Analysis ===\n");
        System.out.printf("JVM start time  : %d ms (epoch)%n", jvmStartMs);
        System.out.printf("JVM uptime at main(): %d ms%n", uptimeMs);
        System.out.printf("Wall time to main(): ~%d ms%n", mainStartMs - jvmStartMs);

        System.out.println("\nVM flags that affect startup:");
        List<String> flags = rtBean.getInputArguments();
        if (flags.isEmpty()) {
            System.out.println("  (none — default settings)");
        } else {
            flags.forEach(f -> System.out.println("  " + f));
        }

        System.out.println("\nTip: compare with a native image:");
        System.out.println("  JVM:    ~100-500 ms to main()");
        System.out.println("  Native: ~5-20 ms to main()");
        System.out.println("\nFlags that speed JVM startup:");
        System.out.println("  -XX:TieredStopAtLevel=1  (only C1, no C2 — faster but lower peak)");
        System.out.println("  -XX:+UseSerialGC         (simpler GC, faster init)");
        System.out.println("  -Xshare:on               (class data sharing, preloaded class cache)");
    }
}
```

**How to run:** `java StartupBench.java`

`RuntimeMXBean.getUptime()` when called near the top of `main()` gives the JVM initialisation overhead. A native-compiled equivalent would report < 20 ms; a JVM with CDS enabled reports 50–150 ms.

### Level 3 — Advanced

Same scenario grown to simulate the AOT reachability metadata problem: show why reflection breaks in native images and how to write the config file that fixes it.

```java
// AotReflectionDemo.java
import java.lang.reflect.*;
import java.util.*;

public class AotReflectionDemo {

    // These classes would not be detected by native-image static analysis
    // unless explicitly listed in reflect-config.json
    record Employee(String name, int salary) {}
    record Product(String sku, double price) {}

    public static void main(String[] args) throws Exception {
        System.out.println("=== AOT Reflection Problem & Solution ===\n");

        List<Class<?>> dynamicClasses = List.of(Employee.class, Product.class);

        System.out.println("[ Dynamic reflection — works on JVM, fails in native without config ]");
        for (Class<?> cls : dynamicClasses) {
            System.out.println("\nClass: " + cls.getSimpleName());
            for (RecordComponent rc : cls.getRecordComponents()) {
                Object instance = cls.getDeclaredConstructors()[0]
                    .newInstance(rc.getType() == String.class ? "test" : 42);
                System.out.printf("  component: %-10s  accessor result: %s%n",
                    rc.getName(), rc.getAccessor().invoke(instance));
            }
        }

        // Generate the reflect-config.json that GraalVM needs
        System.out.println("\n\n[ Generated reflect-config.json for native-image ]");
        System.out.println("Place this file at: src/main/resources/META-INF/native-image/reflect-config.json\n");
        System.out.println("[");
        for (int i = 0; i < dynamicClasses.size(); i++) {
            Class<?> cls = dynamicClasses.get(i);
            System.out.println("  {");
            System.out.println("    \"name\": \"" + cls.getName() + "\",");
            System.out.println("    \"allDeclaredConstructors\": true,");
            System.out.println("    \"allDeclaredMethods\": true,");
            System.out.println("    \"allDeclaredFields\": true");
            System.out.print("  }");
            System.out.println(i < dynamicClasses.size()-1 ? "," : "");
        }
        System.out.println("]");

        System.out.println("\n[ Alternatively — use the tracing agent ]");
        System.out.println("java -agentlib:native-image-agent=config-output-dir=META-INF/native-image \\");
        System.out.println("     -jar app.jar");
        System.out.println("# run all code paths, then native-image uses generated config");
    }
}
```

**How to run:** `java AotReflectionDemo.java`

This shows how reflection usage must be declared in `reflect-config.json` for GraalVM Native Image. Frameworks like Spring Boot 3+ ship with GraalVM hints built in via `@RegisterReflectionForBinding` and AOT processing at build time.

## 6. Walkthrough

Execution in `AotReflectionDemo.main`:

1. **`dynamicClasses`** — a list of `Class<?>` objects. At runtime on a JVM, `cls.getDeclaredConstructors()`, `cls.getRecordComponents()`, and `rc.getAccessor().invoke()` all work without any configuration — the JVM has a full reflective model.

2. **Native Image failure mode** — when `native-image` analyses `AotReflectionDemo.class`, it sees `cls.getDeclaredConstructors()` called on a variable, not a literal class name. Static analysis cannot determine which classes might be in `dynamicClasses`. Without config, those classes are excluded from the native binary → `NoSuchMethodException` at runtime.

3. **`reflect-config.json`** generation — the printed JSON tells Native Image: "include these classes in the native binary with all constructors, methods, and fields available for reflection". The `allDeclared*` flags maximise coverage; production configs narrow to exactly what's needed.

4. **Tracing agent** — the recommended production approach. The agent monitors a full JVM run and captures every reflective access, generating `reflect-config.json`, `proxy-config.json`, `resource-config.json`, and `jni-config.json` automatically.

5. **Spring Boot 3 AOT** — runs an AOT processing phase during `mvn package` that analyses `@Component` classes and pre-generates config files + proxy classes, so the resulting native image has correct reflection metadata without a tracing agent.

## 7. Gotchas & takeaways

> **`native-image` takes 3–10 minutes to build and requires GraalVM.** It is not part of OpenJDK. Install GraalVM CE or use the `graalvm-community` Maven plugin. The long build time is a build-server concern, not a developer-inner-loop concern.

> **Dynamic class loading is incompatible with AOT.** If your code calls `Class.forName(someVariable)`, or uses OSGI, or loads plugins at runtime — native image is either impossible or requires significant refactoring.

- AOT (GraalVM Native Image): native binary, ~5–50 ms startup, ~10–30 MB RSS, no JIT warmup.
- Reflection/proxies/serialisation require explicit metadata (JSON config or tracing agent).
- Spring Boot 3+ has first-class AOT support via `spring-boot:process-aot` and `spring-aot-maven-plugin`.
- JDK's Class Data Sharing (CDS/AppCDS) is a lighter alternative: not full AOT, but pre-parses class bytecode to cut JVM startup by 30–50%.
- AOT peak throughput is typically 10–30% lower than JIT because AOT cannot use runtime profiling for speculative optimisations.
