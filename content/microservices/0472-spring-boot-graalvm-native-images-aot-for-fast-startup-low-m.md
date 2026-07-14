---
card: microservices
gi: 472
slug: spring-boot-graalvm-native-images-aot-for-fast-startup-low-m
title: "Spring Boot GraalVM native images (AOT) for fast startup / low memory"
---

## 1. What it is

A **GraalVM native image** compiles a Spring Boot application **ahead-of-time (AOT)** into a standalone, platform-specific executable — not bytecode run by a JVM, but actual machine code, with the classes it needs, a minimal runtime, and static analysis of reachable code baked in at build time. The result starts in milliseconds instead of seconds and uses a fraction of the memory a traditional JVM process needs, at the cost of a much longer build step and some runtime flexibility the JVM normally provides.

## 2. Why & when

You reach for native images specifically when startup time and memory footprint are the dominant constraints, which is common in certain microservice deployment shapes but not all:

- **Serverless / function-as-a-service platforms bill and constrain by cold-start time.** A JVM application can take seconds to start (class loading, JIT warm-up); a native image often starts in tens of milliseconds — the difference between a function that feels instant and one that visibly lags on its first invocation.
- **High-density container scheduling wants minimal memory per instance.** A traditional JVM microservice might need several hundred megabytes of heap just to run comfortably; a native image can run in a fraction of that, letting a cluster pack more instances onto the same hardware.
- **Fast scale-up matters for handling traffic spikes.** An orchestrator scaling out new Pods to absorb a burst of load benefits enormously from instances that are ready to serve traffic in milliseconds rather than seconds — native images shrink that reaction window dramatically.
- **You do NOT reach for this by default for every service.** Native image builds are significantly slower than a normal JAR build, some dynamic JVM features (certain reflection-heavy libraries, some agent-based tooling) need extra configuration or don't work at all, and the memory/startup gains matter far less for a long-running service that's rarely restarted — reserve native images for services where startup latency or footprint is genuinely the bottleneck.

## 3. Core concept

Think of the difference between an interpreter translating a book aloud, sentence by sentence, as you listen (the JVM interpreting/JIT-compiling bytecode as it runs) versus reading a book that's already been fully translated into your language before you ever opened it (a native image, compiled entirely ahead of time). The pre-translated book is instantly readable from page one; the live interpreter needs a moment to get going and translates as it goes, but can adapt more flexibly to unexpected material.

Concretely:

1. **Spring's AOT engine analyzes your application at build time** — determining which beans will actually be created, which classes are actually reachable, resolving as much of Spring's usual runtime reflection and proxying as it can, ahead of time rather than at startup.
2. **GraalVM's `native-image` tool compiles the application, its dependencies, and a minimal runtime into one native executable**, performing aggressive static analysis to include only what's reachably used — code paths the analysis can't prove are needed get excluded, unless explicitly configured otherwise.
3. **The resulting binary runs with no separate JVM process** — it's a standalone executable for the target OS/architecture, with the class-loading and JIT-warm-up phases of a normal JVM start-up eliminated entirely, since everything was already resolved at build time.
4. **Some genuinely dynamic behavior (arbitrary runtime reflection, dynamic class loading) needs explicit hints** provided at build time, because the ahead-of-time analysis can't always discover code paths that are only decided at runtime.
5. **The tradeoff is build time for run time** — a native-image build commonly takes several minutes (versus seconds for a normal JAR build), in exchange for the resulting binary starting and running dramatically faster and leaner.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A JVM build produces bytecode started by a JVM process with warm-up time; a native-image build produces a standalone executable that starts instantly" >
  <rect x="20" y="30" width="280" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">traditional JAR</text>
  <text x="160" y="72" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JVM starts -&gt; class loading -&gt; JIT warm-up</text>
  <text x="160" y="88" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">startup: ~1-3 seconds, more memory</text>

  <rect x="360" y="30" width="280" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="500" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GraalVM native image</text>
  <text x="500" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">everything resolved at BUILD time</text>
  <text x="500" y="88" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">startup: ~10s of ms, far less memory</text>

  <text x="330" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the cost is moved from every run (JVM startup) to one build (native-image compile)</text>

</svg>

Native-image compilation trades a much longer build for a dramatically faster, leaner runtime start, since resolution work happens once at build time instead of on every process start.

## 5. Runnable example

A real `native-image` build requires the GraalVM toolchain and isn't reproducible in a plain `java File.java` demo — but the core tradeoff it embodies (resolving work once, ahead of time, versus resolving it repeatedly, every run) is directly demonstrable in plain Java. We start with a basic simulation of "resolve at every startup" versus "resolve once, reuse," extend it to model reachability analysis excluding unused code, then handle the hard case: a genuinely dynamic code path that ahead-of-time analysis can't discover without an explicit hint.

### Level 1 — Basic

```java
// File: AotVsJitStartup.java -- models the CORE tradeoff: work done on
// EVERY startup (JIT-style) versus work done ONCE ahead of time and
// reused on every startup (AOT-style, like a native image).
public class AotVsJitStartup {
    // Simulates expensive startup work (scanning classes, resolving beans).
    static long simulateExpensiveResolution() {
        long start = System.nanoTime();
        long sum = 0;
        for (int i = 0; i < 5_000_000; i++) sum += i; // stand-in for real startup work
        return (System.nanoTime() - start) / 1_000_000; // ms
    }

    public static void main(String[] args) {
        System.out.println("--- JIT-style: resolution work repeated on EVERY simulated startup ---");
        for (int run = 1; run <= 3; run++) {
            long ms = simulateExpensiveResolution();
            System.out.println("[jit-style] startup " + run + ": resolution took " + ms + "ms (redone every time)");
        }

        System.out.println();
        System.out.println("--- AOT-style: resolution work done ONCE, result reused every startup ---");
        long resolvedOnce = simulateExpensiveResolution(); // done once, "at build time"
        for (int run = 1; run <= 3; run++) {
            System.out.println("[aot-style] startup " + run + ": using pre-resolved result (" + resolvedOnce + "ms of work already paid for)");
        }
    }
}
```

How to run: `java AotVsJitStartup.java`

`simulateExpensiveResolution` stands in for the class-scanning and bean-resolution work a JVM does on every application start. The JIT-style loop calls it fresh on every simulated startup; the AOT-style section calls it exactly once, outside the per-startup loop, modeling how a native image pays that cost a single time at build, then every actual run simply reuses the already-resolved result.

### Level 2 — Intermediate

```java
// File: ReachabilityAnalysis.java -- the SAME resolve-once idea, now
// EXTENDED to model REACHABILITY ANALYSIS: a native-image build only
// includes code that's PROVABLY reachable from the application's entry
// point, excluding unused code paths -- unlike a JVM, which keeps every
// class on the classpath loadable, used or not.
import java.util.*;

public class ReachabilityAnalysis {
    static Map<String, List<String>> callGraph = Map.of(
        "main", List.of("OrderService", "InventoryService"),
        "OrderService", List.of("PaymentClient"),
        "InventoryService", List.of(),
        "PaymentClient", List.of(),
        "UnusedLegacyReportGenerator", List.of("UnusedPdfLibrary") // never called from main
    );

    static Set<String> computeReachable(String entryPoint) {
        Set<String> reachable = new LinkedHashSet<>();
        Deque<String> toVisit = new ArrayDeque<>();
        toVisit.push(entryPoint);
        while (!toVisit.isEmpty()) {
            String current = toVisit.pop();
            if (reachable.add(current)) {
                for (String callee : callGraph.getOrDefault(current, List.of())) {
                    toVisit.push(callee);
                }
            }
        }
        return reachable;
    }

    public static void main(String[] args) {
        Set<String> reachable = computeReachable("main");
        System.out.println("[native-image analysis] reachable from main: " + reachable);

        for (String clazz : callGraph.keySet()) {
            if (!reachable.contains(clazz)) {
                System.out.println("[native-image analysis] EXCLUDED (unreachable, not compiled in): " + clazz);
            }
        }
    }
}
```

How to run: `java ReachabilityAnalysis.java`

`computeReachable` performs a graph traversal starting at `"main"`, following `callGraph` edges to discover every class actually reachable from the application's entry point. `UnusedLegacyReportGenerator` and `UnusedPdfLibrary` are never reached by this traversal — they exist in `callGraph` (like classes sitting on a classpath) but are never called from `main`, mirroring how a native image's static analysis excludes genuinely unreachable code from the final compiled binary, shrinking both its size and its startup work.

### Level 3 — Advanced

```java
// File: ReflectionHintProblem.java -- the SAME reachability analysis, now
// handling the PRODUCTION-FLAVORED hard case: a class that's only invoked
// through REFLECTION, using a class name built dynamically at RUNTIME
// (e.g. from a configuration string). Static reachability analysis
// CANNOT discover this call, because the class name doesn't appear
// literally anywhere in the call graph -- it must be explicitly
// registered as a "hint," or the native image will fail at runtime with
// a ClassNotFoundException that never happens on a normal JVM.
import java.util.*;

public class ReflectionHintProblem {
    static Map<String, List<String>> callGraph = Map.of(
        "main", List.of("ConfigDrivenHandlerLoader"),
        "ConfigDrivenHandlerLoader", List.of() // loads a handler class BY NAME at runtime, not statically
    );

    static Set<String> computeReachable(String entryPoint) {
        Set<String> reachable = new LinkedHashSet<>();
        Deque<String> toVisit = new ArrayDeque<>();
        toVisit.push(entryPoint);
        while (!toVisit.isEmpty()) {
            String current = toVisit.pop();
            if (reachable.add(current)) {
                for (String callee : callGraph.getOrDefault(current, List.of())) {
                    toVisit.push(callee);
                }
            }
        }
        return reachable;
    }

    // Simulates loading a class purely by a runtime-computed name string, via reflection.
    static boolean tryLoadReflectively(String className, Set<String> compiledIntoImage) {
        if (!compiledIntoImage.contains(className)) {
            System.out.println("[runtime] FAILED: Class.forName(\"" + className
                    + "\") -- ClassNotFoundException, because static analysis never discovered this reflective call");
            return false;
        }
        System.out.println("[runtime] loaded " + className + " reflectively -- succeeded");
        return true;
    }

    public static void main(String[] args) {
        Set<String> staticallyReachable = computeReachable("main");
        System.out.println("[native-image analysis] statically reachable: " + staticallyReachable);

        // At RUNTIME, config decides to load "PdfExportHandler" by name -- statically invisible.
        String configDrivenClassName = "PdfExportHandler";
        System.out.println();
        System.out.println("--- without a reflection hint ---");
        tryLoadReflectively(configDrivenClassName, staticallyReachable);

        // The fix: explicitly register the class as reachable via a reflection hint,
        // exactly like adding it to a real reflect-config.json for native-image.
        System.out.println();
        System.out.println("--- with an explicit reflection hint registered ---");
        Set<String> withHint = new LinkedHashSet<>(staticallyReachable);
        withHint.add(configDrivenClassName);
        System.out.println("[build config] reflection hint registered for: " + configDrivenClassName);
        tryLoadReflectively(configDrivenClassName, withHint);
    }
}
```

How to run: `java ReflectionHintProblem.java`

`configDrivenClassName` is a string that, in a real application, might come from a database row or a config file read at runtime — it never appears as a literal edge in `callGraph`, so `computeReachable` (modeling native-image's static analysis) never discovers `"PdfExportHandler"` as reachable. The first `tryLoadReflectively` call fails because `staticallyReachable` doesn't contain that name. The second call succeeds only after `withHint` explicitly adds it — modeling a real `reflect-config.json` hint file telling `native-image` "compile this class in, even though you can't prove it's reachable on your own."

## 6. Walkthrough

Trace `ReflectionHintProblem.main` in order. **First**, `computeReachable("main")` runs its graph traversal: `main` calls `ConfigDrivenHandlerLoader`, which (in `callGraph`) has no further statically-declared callees — the traversal ends there, so `staticallyReachable` contains exactly `{main, ConfigDrivenHandlerLoader}`.

**Next**, `configDrivenClassName` is set to `"PdfExportHandler"`, representing a class name that will only be known at actual runtime — perhaps read from a configuration property — with no static reference to it anywhere in the code's call graph.

**Then**, the "without a reflection hint" section calls `tryLoadReflectively("PdfExportHandler", staticallyReachable)`. The check `!compiledIntoImage.contains(className)` is `true`, since `staticallyReachable` never included this name, so the method prints the failure message and returns `false` — modeling exactly what happens when a real native image, missing a reflection hint, hits `Class.forName` for a class the build excluded.

**After that**, the "with an explicit reflection hint" section builds `withHint` as a copy of `staticallyReachable` plus the missing class name added explicitly — modeling a developer adding an entry to a `reflect-config.json` file (or an equivalent `@RegisterReflectionForBinding` hint in Spring's AOT support) to tell the build "include this even though you can't prove it's reachable."

**Finally**, `tryLoadReflectively("PdfExportHandler", withHint)` runs the same check again, but this time `withHint.contains(className)` is `true`, so the success branch runs and prints confirmation — the exact same reflective load that failed a moment ago now succeeds, purely because of the explicit hint, with no other code changed.

```
[native-image analysis] statically reachable: [main, ConfigDrivenHandlerLoader]

--- without a reflection hint ---
[runtime] FAILED: Class.forName("PdfExportHandler") -- ClassNotFoundException, because static analysis never discovered this reflective call

--- with an explicit reflection hint registered ---
[build config] reflection hint registered for: PdfExportHandler
[runtime] loaded PdfExportHandler reflectively -- succeeded
```

## 7. Gotchas & takeaways

> A `ClassNotFoundException` (or a missing-bean error) that appears only in a native image build, and never on a normal JVM run of the exact same code, is the signature symptom of a reflective or dynamic code path the ahead-of-time analysis couldn't discover — the fix is almost always registering an explicit hint, not a code bug.
- Spring Boot's own AOT processing generates many of these hints automatically for framework-managed beans and proxies — the gap you need to close by hand is mostly your *own* application's reflective or dynamic code, plus any third-party library that isn't already native-image aware.
- Native-image build time is a real cost, often minutes rather than seconds — factor that into CI pipeline duration if you adopt this broadly, and consider whether every service in a fleet actually benefits enough to justify it.
- The startup and memory gains matter most for short-lived or frequently-restarted workloads (serverless functions, rapidly autoscaled Pods); a long-running, rarely-restarted service sees far less relative benefit from paying the native-image build cost.
- Test a native-image build in CI the same way you'd test any other build target — reflection and dynamic-class-loading gaps are easy to miss locally and only surface once the compiled binary actually runs.
- This pairs naturally with [layered JARs](0469-spring-boot-layered-jars-for-efficient-images.md) and [Cloud Native Buildpacks](0470-spring-boot-cloud-native-buildpacks-bootbuildimage.md) in the broader packaging picture — native image is one more packaging option in the same toolkit, chosen specifically when startup time and memory footprint are the dominant deployment concern.
