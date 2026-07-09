---
card: java
gi: 731
slug: linux-risc-v-port
title: Linux/RISC-V port
---

## 1. What it is

**Java 19** (JEP 422) adds **Linux/RISC-V** as an officially supported JDK build and runtime platform. RISC-V is an open, royalty-free instruction set architecture (as opposed to proprietary ISAs like x86 or licensed ones like ARM), and by Java 19 it had grown from a mostly academic and embedded-systems architecture into a real target for servers, single-board computers, and increasingly capable general-purpose hardware. This JEP is a **porting effort**, not a language or library feature: it means the OpenJDK build system, the HotSpot JVM's interpreter and JIT compilers, and the full standard library all now compile and run correctly on 64-bit RISC-V Linux systems — a Java program that already runs correctly on x86-64 or ARM64 Linux now also runs, unmodified, on RISC-V Linux, because the *platform*, not the *program*, is what changed.

## 2. Why & when

Every new CPU architecture the JDK supports expands where the exact same Java bytecode can run without recompilation — this is the core promise of "write once, run anywhere" extended to a genuinely new class of hardware. RISC-V's growth was driven by its open specification: unlike licensing an existing architecture, chip designers can implement RISC-V without royalty payments and can extend the base instruction set for specialized workloads, which made it attractive for everything from low-power embedded boards to, increasingly, general-purpose Linux servers and development boards aimed at a broader audience. As RISC-V hardware became something real developers might actually deploy to or develop on, having Java run natively on it — rather than requiring emulation or cross-compilation workarounds — became a meaningful gap to close. This JEP matters directly to almost no *application* code: a typical Java or Spring Boot developer's source code, build scripts, and dependencies are entirely unaffected. It matters to anyone choosing deployment hardware, building embedded or edge systems on RISC-V boards, or working on the JDK itself. The practical takeaway for application developers is reassurance, not a new API: if your organization evaluates RISC-V hardware for a new class of deployment, Java is a viable, first-class option there starting with this port, with no code changes required.

## 3. Core concept

```java
// Ordinary Java code — completely unaware of and unaffected by which CPU
// architecture the JVM happens to be running on.
public class WhereAmIRunning {
    public static void main(String[] args) {
        System.out.println("os.arch:  " + System.getProperty("os.arch"));
        System.out.println("os.name:  " + System.getProperty("os.name"));
        System.out.println("java.vm.name: " + System.getProperty("java.vm.name"));
    }
}
```

On x86-64 Linux this might print `os.arch: amd64`; on the exact same JDK build for RISC-V, running the exact same unmodified `.class` file, it prints `os.arch: riscv64` — the application source code, and even the compiled bytecode, are identical.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same compiled Java bytecode runs unmodified on any platform the JDK supports; Java 19 adds Linux on RISC-V as a new supported platform alongside existing x86 and ARM targets">
  <rect x="240" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="50" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">MyApp.class (bytecode)</text>

  <line x1="270" y1="70" x2="130" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a10)"/>
  <line x1="320" y1="70" x2="320" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a10)"/>
  <line x1="370" y1="70" x2="510" y2="120" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a10)"/>

  <rect x="40" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="130" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JVM on x86-64 Linux</text>

  <rect x="230" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="150" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JVM on ARM64 Linux</text>

  <rect x="420" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#3fb950"/>
  <text x="510" y="150" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">JVM on RISC-V Linux (new, Java 19)</text>

  <defs><marker id="a10" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

The compiled `.class` file never changes; only the JVM binary underneath it is built for a different CPU architecture.

## 5. Runnable example

Scenario: a small diagnostic program useful when preparing to deploy Java software to unfamiliar or new hardware targets like RISC-V. It grows from basic platform inspection, to checking JVM feature availability that can vary across newer ports (like which garbage collectors are present), to a self-contained portability smoke test verifying core language features work identically regardless of the underlying architecture — reasonable due diligence before shipping to a new class of hardware.

### Level 1 — Basic

```java
// File: PlatformInfoBasic.java
public class PlatformInfoBasic {
    public static void main(String[] args) {
        System.out.println("Architecture (os.arch): " + System.getProperty("os.arch"));
        System.out.println("Operating system: " + System.getProperty("os.name") + " " + System.getProperty("os.version"));
        System.out.println("JVM name: " + System.getProperty("java.vm.name"));
        System.out.println("JVM version: " + System.getProperty("java.vm.version"));
        System.out.println("Available processors: " + Runtime.getRuntime().availableProcessors());
    }
}
```

**How to run:**
```
java PlatformInfoBasic.java
```

Expected output (values vary by machine; shown here for an x86-64 Linux example — the same source run on a Java 19 RISC-V build would print `riscv64` for os.arch and otherwise the same shape of output):
```
Architecture (os.arch): amd64
Operating system: Linux 6.1.0
JVM name: OpenJDK 64-Bit Server VM
JVM version: 19+36
Available processors: 8
```

### Level 2 — Intermediate

```java
// File: PlatformInfoIntermediate.java
// Adds a check of which garbage collectors are actually available on this
// JVM build — a real-world concern when validating a JDK port on new
// hardware, since not every GC implementation is necessarily available (or
// equally mature) on every platform port from day one.
import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.util.List;

public class PlatformInfoIntermediate {
    public static void main(String[] args) {
        System.out.println("Architecture (os.arch): " + System.getProperty("os.arch"));
        System.out.println("JVM name: " + System.getProperty("java.vm.name"));

        List<GarbageCollectorMXBean> collectors = ManagementFactory.getGarbageCollectorMXBeans();
        System.out.println("Garbage collectors available on this JVM:");
        for (GarbageCollectorMXBean gc : collectors) {
            System.out.println("  - " + gc.getName());
        }

        long maxHeapBytes = Runtime.getRuntime().maxMemory();
        System.out.println("Max heap: " + (maxHeapBytes / (1024 * 1024)) + " MB");
    }
}
```

**How to run:**
```
java PlatformInfoIntermediate.java
```

Expected output shape (collector names and count vary by JVM configuration and platform):
```
Architecture (os.arch): amd64
JVM name: OpenJDK 64-Bit Server VM
Garbage collectors available on this JVM:
  - G1 Young Generation
  - G1 Old Generation
Max heap: 4096 MB
```

### Level 3 — Advanced

```java
// File: PortabilitySmokeTestAdvanced.java
// A small self-contained smoke test exercising core language and runtime
// features (numeric behavior, threading, exceptions, string handling) that
// should behave IDENTICALLY across every platform the JDK supports — the
// kind of due-diligence check worth running when validating a deployment
// target on a newer or less common JDK port such as Linux/RISC-V.
import java.util.concurrent.atomic.AtomicInteger;

public class PortabilitySmokeTestAdvanced {
    static int checksPassed = 0;
    static int checksFailed = 0;

    static void check(String description, boolean condition) {
        if (condition) {
            checksPassed++;
        } else {
            checksFailed++;
            System.out.println("FAILED: " + description);
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("Running portability smoke test on: " + System.getProperty("os.arch"));

        // Numeric behavior must be identical bit-for-bit across platforms (IEEE 754, two's complement).
        check("integer overflow wraps predictably", Integer.MAX_VALUE + 1 == Integer.MIN_VALUE);
        check("double precision arithmetic", 0.1 + 0.2 != 0.3 && Math.abs(0.1 + 0.2 - 0.3) < 1e-9);
        check("long division truncates toward zero", -7L / 2L == -3L);

        // Threading must work correctly regardless of the underlying CPU's memory model quirks.
        AtomicInteger counter = new AtomicInteger(0);
        Thread[] threads = new Thread[4];
        for (int i = 0; i < threads.length; i++) {
            threads[i] = new Thread(() -> {
                for (int j = 0; j < 1000; j++) counter.incrementAndGet();
            });
            threads[i].start();
        }
        for (Thread t : threads) t.join();
        check("concurrent atomic increments are race-free", counter.get() == 4000);

        // String and Unicode handling must be architecture-independent.
        String unicode = "café 你好";
        check("string length is architecture-independent", unicode.length() == 8);

        // Exceptions must unwind correctly regardless of native stack layout differences.
        boolean caught = false;
        try {
            throw new IllegalStateException("test exception");
        } catch (IllegalStateException e) {
            caught = true;
        }
        check("exception handling works", caught);

        System.out.println("Checks passed: " + checksPassed + ", failed: " + checksFailed);
    }
}
```

**How to run:**
```
java PortabilitySmokeTestAdvanced.java
```

Expected output (identical pass/fail results on every JDK-supported platform, including x86-64, ARM64, and — from Java 19 onward — RISC-V64 Linux):
```
Running portability smoke test on: amd64
Checks passed: 5, failed: 0
```

## 6. Walkthrough

1. `PortabilitySmokeTestAdvanced.main` first prints `os.arch`, establishing which CPU architecture the current JVM is actually running on — this line is the only part of the program whose *output value* varies across platforms; everything that follows is a correctness check whose *result* must not vary.
2. The numeric checks (`Integer.MAX_VALUE + 1 == Integer.MIN_VALUE`, floating-point precision behavior, integer division truncation) verify that Java's specified arithmetic semantics — two's complement integer wraparound, IEEE 754 floating-point representation, truncating integer division — hold exactly, bit for bit, regardless of the CPU underneath. This is a core guarantee the Java Language Specification makes and that every JDK port, including the RISC-V one this JEP delivers, must uphold: these are not "usually true," they are specified and mechanically verifiable.
3. The threading check spawns four threads, each incrementing a shared `AtomicInteger` a thousand times, then verifies the final count is exactly `4000` — proving atomic operations remain race-free regardless of the CPU's native memory model and atomic-instruction support, which can differ significantly between architectures (RISC-V's atomic extension, x86's cache-coherency guarantees, ARM's weaker default memory ordering) even though the JVM must present the same Java Memory Model guarantees on top of all of them.
4. The Unicode string-length check verifies that `String.length()` — which counts UTF-16 code units, an entirely software-level concept — behaves identically regardless of how the underlying platform represents characters or bytes natively; a multi-byte UTF-8 native encoding on Linux doesn't leak into Java's own internal `String` representation.
5. The exception-handling check verifies that a `throw` and matching `catch` unwind the stack correctly — this exercises the JIT compiler's and interpreter's exception-table handling, a piece of the runtime that a new architecture port (like RISC-V's HotSpot interpreter and compilers) has to implement correctly for stack unwinding to behave per the JVM specification.
6. Finally, `checksPassed`/`checksFailed` are printed — on a correctly functioning JDK port, this smoke test produces the exact same `5 passed, 0 failed` result whether it's run on x86-64, ARM64, or, from Java 19 onward, RISC-V64 Linux, which is precisely the portability guarantee this JEP extends to a new class of hardware.

```
Same PortabilitySmokeTestAdvanced.class file
        |
        +----------------+----------------+
        v                v                v
  x86-64 Linux      ARM64 Linux      RISC-V64 Linux (Java 19+)
        |                |                |
        v                v                v
  5 passed, 0 failed  5 passed, 0 failed  5 passed, 0 failed
```

## 7. Gotchas & takeaways

> This JEP delivers a **platform port**, not an application-visible feature — there is no new class, method, or syntax for ordinary Java code to use. Its entire effect is that JDK builds and the HotSpot JVM now exist for Linux/RISC-V, meaning `System.getProperty("os.arch")` can now return `"riscv64"` on a real, officially supported target.
- Application developers should expect **zero source-code changes** when targeting RISC-V — the entire point of the JVM's bytecode abstraction is that portable Java code doesn't need architecture-specific branches; write ordinary, portable Java and it runs correctly on any JDK-supported platform, including this new one.
- Newer or less mature platform ports can, in practice, lag slightly behind more established ones (x86-64, ARM64) in areas like garbage collector maturity, JIT compiler optimization tiers, or certain native-interop features — the diagnostic approach in Level 2 (checking which garbage collectors are actually present) is a reasonable practical check before committing to a newer architecture for a production deployment.
- RISC-V's openness (no licensing fees, extensible instruction set) is precisely why it became a compelling enough target to warrant this JEP — the same forces that made it attractive to chip designers made it worth the OpenJDK project's engineering investment to support as a first-class platform.
- If your organization is evaluating RISC-V hardware, the practical next step is not code changes but infrastructure verification: confirming a suitable JDK distribution is available for the target RISC-V board or server, and running exactly the kind of portability smoke test shown in Level 3 as part of standard due diligence before deploying real workloads.
