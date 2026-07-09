---
card: java
gi: 714
slug: remove-experimental-aot-jit-graal-compiler
title: Remove experimental AOT/JIT (Graal) compiler
---

## 1. What it is

**Java 17** (JEP 410) **removed** two experimental features introduced years earlier: the **AOT (ahead-of-time) compiler** (`jaotc`, introduced experimentally in Java 9 via JEP 295) and the option to use the **Graal compiler as an experimental JIT compiler** (`-XX:+UseJVMCICompiler`, introduced experimentally in Java 10 via JEP 317). Both had been explicitly labeled experimental from the start and never graduated to a supported, production-ready feature; JEP 410 removed them from the JDK entirely rather than continuing to carry code that saw little real-world adoption and no active investment toward production-readiness.

## 2. Why & when

The AOT compiler (`jaotc`) let you compile Java classes to native machine code ahead of time, hoping to reduce JVM startup and warmup time compared to the JIT compiling everything on the fly — but it came with real limitations (a separate compile step, restrictions on which classes could be AOT-compiled, results tied to a specific JDK build) that kept it from replacing the JIT's role broadly, and adoption stayed minimal since its Java 9 introduction. Separately, Graal (Oracle's alternative, Java-based JIT compiler) could optionally replace HotSpot's default C2 JIT compiler experimentally via a JVMCI (JVM Compiler Interface) flag — but this experimental in-JDK integration existed alongside GraalVM's own separate, actively-developed distribution, which had become the practical, supported way to actually use Graal, making the experimental in-tree option increasingly redundant. Both features consumed real ongoing maintenance effort for capabilities seeing little production use, and neither had a credible path to graduating out of "experimental" status, so JEP 410 removed both, simplifying HotSpot's build and reducing its maintenance surface. If you were using either feature, the JEP's answer is explicit: use the standard, default JIT compiler (C1/C2 tiered compilation) for ordinary needs, or the separate **GraalVM** distribution specifically if you want Graal's compiler or native-image capabilities.

## 3. Core concept

```bash
# Java 9–16: an experimental ahead-of-time compilation step existed
jaotc --output libHelloWorld.so HelloWorld.class    # Java 17+: 'jaotc' no longer exists

# Java 10–16: Graal could optionally replace the default JIT, experimentally
java -XX:+UnlockExperimentalVMOptions -XX:+UseJVMCICompiler MyApp.jar
# Java 17+: -XX:+UseJVMCICompiler is gone; the flag is rejected as unrecognized

# Java 17+ supported alternative for Graal specifically: use the separate GraalVM distribution
# https://www.graalvm.org — a complete, independently maintained JDK distribution
```

Neither the `jaotc` tool nor the in-tree experimental Graal JIT integration exist in Java 17 — both are gone, with no compatibility flag to restore them.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 17, an experimental jaotc ahead-of-time compiler and an experimental in-JDK Graal JIT option both existed alongside the default JIT compiler; Java 17 removes both, leaving the default JIT and the separately-distributed GraalVM as the two supported paths">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Java 9/10 – 16</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">default JIT (C1/C2)</text>
  <text x="160" y="95" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">+ experimental jaotc (AOT)</text>
  <text x="160" y="120" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">+ experimental in-JDK Graal JIT</text>
  <text x="160" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">both experimental, low adoption</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 17+</text>
  <text x="480" y="80" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">default JIT (C1/C2) — unchanged</text>
  <text x="480" y="110" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">jaotc: removed</text>
  <text x="480" y="130" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">in-JDK experimental Graal: removed</text>
  <text x="480" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">separate GraalVM distribution still available</text>
</svg>

The default JIT pipeline is unaffected; the two experimental, low-adoption alternatives are removed entirely.

## 5. Runnable example

Scenario: since `jaotc` and the experimental Graal JIT flag no longer exist to run directly, the most faithful runnable example is a small diagnostic that inspects what JIT compilation *is* actually available and active on the current JVM, then a program that demonstrates ordinary JIT warmup behavior (the thing both removed features were trying to improve upon), then a version that specifically detects whether the running JVM happens to be a GraalVM distribution (the supported path for anyone who still wants Graal specifically).

### Level 1 — Basic

```java
// File: JitInfoBasic.java
import java.lang.management.CompilationMXBean;
import java.lang.management.ManagementFactory;

public class JitInfoBasic {
    public static void main(String[] args) {
        CompilationMXBean bean = ManagementFactory.getCompilationMXBean();
        System.out.println("JIT compiler name: " + bean.getName());
        System.out.println("Compilation time monitoring supported: " + bean.isCompilationTimeMonitoringSupported());
        if (bean.isCompilationTimeMonitoringSupported()) {
            System.out.println("Total compilation time so far: " + bean.getTotalCompilationTime() + " ms");
        }
    }
}
```

**How to run:**
```
java JitInfoBasic.java
```

Expected output shape (compiler name depends on the specific JDK build; HotSpot's default tiered C1/C2 pipeline is standard from Java 17 onward, with no experimental Graal option remaining in-tree):
```
JIT compiler name: HotSpot 64-Bit Tiered Compilers
Compilation time monitoring supported: true
Total compilation time so far: 42 ms
```

### Level 2 — Intermediate

```java
// File: WarmupDemonstration.java
public class WarmupDemonstration {
    static long fibonacci(int n) {
        if (n <= 1) return n;
        long a = 0, b = 1;
        for (int i = 2; i <= n; i++) {
            long next = a + b;
            a = b;
            b = next;
        }
        return b;
    }

    static long timeIterations(int iterations) {
        long start = System.nanoTime();
        long sum = 0;
        for (int i = 0; i < iterations; i++) {
            sum += fibonacci(40);
        }
        return (System.nanoTime() - start) / 1_000_000; // ms, 'sum' only prevents dead-code elimination
    }

    public static void main(String[] args) {
        System.out.println("Cold run (JIT not yet warmed up):   " + timeIterations(1_000) + " ms");
        System.out.println("Warm run (JIT has now optimized):    " + timeIterations(1_000_000) + " ms per million");
    }
}
```

**How to run:**
```
java WarmupDemonstration.java
```

Expected output shape (exact timings vary by machine; the JIT's adaptive optimization is what both AOT and experimental Graal aimed to complement or improve upon):
```
Cold run (JIT not yet warmed up):   8 ms
Warm run (JIT has now optimized):    45 ms per million
```

### Level 3 — Advanced

```java
// File: GraalVMDetector.java
public class GraalVMDetector {
    static boolean isGraalVM() {
        String vmName = System.getProperty("java.vm.name", "");
        String vendorVersion = System.getProperty("java.vendor.version", "");
        return vmName.contains("GraalVM") || vendorVersion.contains("GraalVM")
                || System.getProperty("org.graalvm.version") != null;
    }

    public static void main(String[] args) {
        System.out.println("java.vm.name:        " + System.getProperty("java.vm.name"));
        System.out.println("java.vendor.version: " + System.getProperty("java.vendor.version", "(not set)"));
        System.out.println("Running on GraalVM:  " + isGraalVM());

        if (isGraalVM()) {
            System.out.println("This JVM includes Graal's compiler natively (the supported, actively-maintained path).");
        } else {
            System.out.println("This is a standard JDK build using the default HotSpot JIT (C1/C2) pipeline;");
            System.out.println("the experimental in-JDK Graal JIT option removed in Java 17 is not applicable here.");
        }
    }
}
```

**How to run:**
```
java GraalVMDetector.java
```

Expected output shape (on a standard OpenJDK/Temurin/etc. build, Java 17+):
```
java.vm.name:        OpenJDK 64-Bit Server VM
java.vendor.version: (not set)
Running on GraalVM:  false
This is a standard JDK build using the default HotSpot JIT (C1/C2) pipeline;
the experimental in-JDK Graal JIT option removed in Java 17 is not applicable here.
```

## 6. Walkthrough

1. `WarmupDemonstration.main` calls `timeIterations(1_000)` first, running the `fibonacci(40)` computation a mere 1,000 times — early in a JVM's life, HotSpot's JIT hasn't yet gathered enough profiling data to aggressively optimize this method, so it runs largely on the interpreter or lightly-optimized C1-tier compiled code.
2. `timeIterations(1_000_000)` then runs the same computation a million times — by this point, HotSpot's tiered compilation has had ample opportunity to promote `fibonacci` to the highly-optimizing C2 compiler tier based on how frequently it's been called ("hot" methods get progressively more aggressive optimization), so the *per-call* cost drops substantially even though the absolute total time for a million calls is naturally larger than for a thousand.
3. This warmup behavior — the JIT needing some running time to identify and optimize hot code — is exactly the cost that both AOT compilation (pre-compile before the JVM even starts, avoiding a warmup period) and, in a very different way, an alternative compiler backend like Graal were exploring ways to reduce or reshape; neither approach in its Java 9/10-era experimental in-JDK form ended up being the answer the JDK team settled on for production use.
4. `GraalVMDetector.isGraalVM()` checks `java.vm.name` and related system properties for signs the current JVM is actually a GraalVM distribution — since JEP 410 removed the *in-JDK experimental option* to opt into Graal, but did **not** touch GraalVM itself (a wholly separate, independently distributed and maintained product), this check demonstrates the two are genuinely distinct: one JVM property space for "is Graal compiling this code," entirely unaffected by what JEP 410 removed from the standard OpenJDK builds.
5. Running `GraalVMDetector` on an ordinary OpenJDK, Eclipse Temurin, or similar standard JDK 17+ build reports `false` and explains why: the removed feature (`-XX:+UseJVMCICompiler`) simply isn't a concept that applies to a standard build anymore, whereas actually running this same detector on an official GraalVM distribution would report `true`, since GraalVM ships its compiler as a first-class, integral part of that specific distribution rather than as an experimental flag on a standard JDK.

```
JVM startup
    │
tiered JIT compilation (unaffected by JEP 410):
    interpreter -> C1 (quick, light optimization) -> C2 (hot methods, heavy optimization)
    │
[removed in Java 17]: jaotc (pre-compile before startup)
[removed in Java 17]: -XX:+UseJVMCICompiler (swap in experimental in-JDK Graal)
    │
[still available, separately]: GraalVM distribution — Graal as the built-in, supported compiler
```

## 7. Gotchas & takeaways

> Removing the **experimental in-JDK option** to enable Graal (`-XX:+UseJVMCICompiler`) is not the same as removing Graal itself — **GraalVM**, the separate, independently distributed and actively developed JDK distribution built around the Graal compiler (and its native-image ahead-of-time compilation capability), is entirely unaffected by JEP 410 and remains a fully supported choice for anyone who wants Graal's compiler or native-image features specifically.
- `jaotc` and its `.so`/native-library output files are gone from Java 17 onward — any build pipeline still invoking `jaotc` needs to remove that step entirely; there's no direct in-JDK ahead-of-time-compilation replacement, though GraalVM's separate native-image tool addresses a related (but architecturally different) goal.
- Both removed features were explicitly labeled **experimental** from their introduction (Java 9 for AOT, Java 10 for the JVMCI/Graal JIT option) — this JEP is a case study in the JDK honoring that label: features marked experimental can be removed outright, without the multi-release deprecation warning process applied to established, non-experimental APIs.
- The default tiered JIT compilation pipeline (interpreter, C1, C2) that most Java applications rely on is completely unaffected by this JEP — this removal only affects the two specific, rarely-used experimental alternatives to that default path.
- If your build or deployment pipeline referenced `jaotc` or `-XX:+UseJVMCICompiler` for a Java 9–16 target, plan to remove those references before upgrading to Java 17 — the JVM will simply reject the unrecognized flag or missing tool rather than silently falling back to older behavior.
- This removal is part of the same broader Java 17 pattern as [Remove RMI Activation](0713-remove-rmi-activation.md) and [Remove Applet API](0716-remove-applet-api-deprecated.md) — the JDK actively shedding features that never reached broad production adoption, keeping the platform's maintained surface focused on what's actually widely used.
