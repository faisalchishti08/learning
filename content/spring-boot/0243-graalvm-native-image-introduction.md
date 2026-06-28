---
card: spring-boot
gi: 243
slug: graalvm-native-image-introduction
title: GraalVM Native Image introduction
---

## 1. What it is

GraalVM Native Image compiles a Java application ahead-of-time (AOT) into a standalone native executable. Instead of starting a JVM at runtime, the executable contains only the reachable code paths, a minimal runtime, and pre-initialised heap state. Spring Boot 3 provides first-class Native Image support via the `spring-aot-maven-plugin` and buildpack integration.

## 2. Why & when

Standard JVM startup takes 2-8 seconds for a typical Spring Boot app and consumes 100-300 MB of RAM. A native executable starts in 50-100 milliseconds and uses 50-80% less memory — critical for serverless functions, CLIs, sidecar containers, and any workload that scales to zero and back frequently. The trade-off is longer build time (1-5 minutes) and a more constrained programming model.

## 3. Core concept

Native Image works by tracing all reachable code from the entry point at **build time**. Everything not reachable is excluded from the binary. This creates two challenges for Spring:

- **Reflection** — Spring uses reflection heavily. At build time, the AOT engine generates `RuntimeHints` registering all reflectively-accessed types.
- **Dynamic proxies and class generation** — replaced by AOT-generated static code.

Spring Boot's AOT processing runs during `spring-boot:process-aot` (Maven) or `bootBuildImage` with `BP_NATIVE_IMAGE=true`. It:
1. Instantiates the `ApplicationContext` at build time to discover beans.
2. Generates optimised source code and resource hints.
3. Passes hints to the `native-image` compiler.

The resulting binary links everything — JDK classes, Spring, your code — into a single file.

## 4. Diagram

<svg viewBox="0 0 640 290" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="290" fill="#1c2430" rx="10"/>
  <!-- Build time -->
  <rect x="20" y="30" width="280" height="200" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="160" y="58" text-anchor="middle" fill="#8b949e">Build Time</text>
  <rect x="35" y="70" width="250" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="93" text-anchor="middle" fill="#e6edf3" font-size="12">Spring AOT engine</text>
  <rect x="35" y="113" width="250" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="160" y="136" text-anchor="middle" fill="#e6edf3" font-size="12">generated source + hints</text>
  <rect x="35" y="156" width="250" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="179" text-anchor="middle" fill="#6db33f" font-size="12">native-image compiler</text>
  <text x="160" y="215" text-anchor="middle" fill="#8b949e" font-size="11">(1-5 min build time)</text>
  <!-- Arrow -->
  <line x1="302" y1="150" x2="328" y2="150" stroke="#6db33f" stroke-width="2" marker-end="url(#ag)"/>
  <!-- Runtime -->
  <rect x="330" y="30" width="290" height="200" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="475" y="58" text-anchor="middle" fill="#6db33f">Runtime (native executable)</text>
  <rect x="345" y="70" width="260" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="91" text-anchor="middle" fill="#6db33f" font-size="12">startup: 50-100 ms  ✓</text>
  <text x="475" y="107" text-anchor="middle" fill="#8b949e" font-size="11">(vs. 2-8 s for JVM)</text>
  <rect x="345" y="118" width="260" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="139" text-anchor="middle" fill="#6db33f" font-size="12">memory: 50-80% less  ✓</text>
  <rect x="345" y="166" width="260" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="475" y="181" text-anchor="middle" fill="#8b949e" font-size="12">No JVM needed at runtime</text>
  <text x="475" y="197" text-anchor="middle" fill="#8b949e" font-size="11">single self-contained binary</text>
  <!-- Constraints note -->
  <rect x="330" y="240" width="290" height="35" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="475" y="262" text-anchor="middle" fill="#79c0ff" font-size="11">Trade-off: longer build, constrained reflection</text>
  <defs>
    <marker id="ag" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_AOT compilation at build time produces a binary with instant startup and minimal memory — no JVM at runtime._

## 5. Runnable example

```java
// File: NativeImageDemo.java
// How to run (standard JVM): java NativeImageDemo.java
// How to build native image: ./mvnw -Pnative native:compile
// How to run native binary:  ./target/myapp

public class NativeImageDemo {

    // Detect at runtime whether we're in a GraalVM native image
    static boolean isNativeImage() {
        try {
            // This class is only present in a native image context
            Class.forName("org.graalvm.nativeimage.ImageInfo");
            return true;
        } catch (ClassNotFoundException e) {
            return false;
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Runtime environment ===");
        System.out.println("Running as native image: " + isNativeImage());
        System.out.println("Java version: " + System.getProperty("java.version"));
        System.out.println("Available processors: " + Runtime.getRuntime().availableProcessors());
        System.out.printf("Max heap (MB): %.0f%n",
                Runtime.getRuntime().maxMemory() / 1_048_576.0);

        System.out.println("\n=== Build commands ===");
        System.out.println("# Requires GraalVM JDK 21+ with native-image installed");
        System.out.println("# Install: sdk install java 21.0.3-graal");
        System.out.println();
        System.out.println("# Maven: build native executable");
        System.out.println("./mvnw -Pnative native:compile");
        System.out.println();
        System.out.println("# Maven: build native container image via Paketo");
        System.out.println("./mvnw spring-boot:build-image -Pnative");
        System.out.println("  (uses BP_NATIVE_IMAGE=true buildpack env)");
        System.out.println();
        System.out.println("# Gradle: build native executable");
        System.out.println("./gradlew nativeCompile");

        System.out.println("\n=== Key AOT-processing hints ===");
        System.out.println("// Register a class for reflection at build time:");
        System.out.println("// @ImportRuntimeHints(MyHints.class)");
        System.out.println("// class MyHints implements RuntimeHintsRegistrar {");
        System.out.println("//   public void registerHints(RuntimeHints hints, ClassLoader cl) {");
        System.out.println("//     hints.reflection().registerType(MyDto.class,");
        System.out.println("//       MemberCategory.INVOKE_DECLARED_CONSTRUCTORS,");
        System.out.println("//       MemberCategory.INVOKE_PUBLIC_METHODS);");
        System.out.println("//   }");
        System.out.println("// }");
    }
}
```

**How to run (JVM):** `java NativeImageDemo.java` — works on any JVM and prints build commands.
**Build native:** Install GraalVM (`sdk install java 21.0.3-graal`), then `./mvnw -Pnative native:compile` in a Spring Boot project with the `native` profile.

## 6. Walkthrough

1. `isNativeImage()` — detects native vs. JVM mode by checking for `org.graalvm.nativeimage.ImageInfo`, a class present only in native images.
2. **Build pipeline** — `./mvnw -Pnative native:compile` activates the `native` Maven profile (added by Spring Initializr). It first runs `spring-boot:process-aot`, which instantiates the context at build time and generates static configuration. Then `native:compile` invokes the `native-image` binary.
3. **AOT processing** — Spring Boot's AOT engine scans `@Configuration` classes, resolves beans, and emits: generated `@Configuration` code, proxy factories, serialisation hints, and resource pattern hints.
4. **`RuntimeHintsRegistrar`** — for libraries or code that still needs reflection, you implement this interface and annotate with `@ImportRuntimeHints`. The engine feeds these hints to `native-image`.
5. **Buildpack path** — `./mvnw spring-boot:build-image -Pnative` uses `BP_NATIVE_IMAGE=true` inside the Paketo buildpack. GraalVM is provided by the buildpack — no local GraalVM install needed.

## 7. Gotchas & takeaways

> Native images do **not** support all Java features. Dynamic class loading, arbitrary reflection without hints, and serialisation of unregistered types fail at runtime. Test the native binary, not just the JVM build.

> Build time is long (1-5 minutes) and requires 4-8 GB of RAM. Native image builds are not suitable for hot-reload development — keep the JVM dev loop, build native only for CI and deployment.

> Not all third-party libraries support Native Image out-of-the-box. Check the [GraalVM Reachability Metadata Repository](https://github.com/oracle/graalvm-reachability-metadata) — Spring Boot auto-pulls hints for popular libraries.

- Start with `./mvnw -Pnative test` — runs the test suite in a native image, catching reflection issues before production.
- Use `@NativeHint` (deprecated) or `RuntimeHintsRegistrar` for custom reflection, resource, or proxy hints.
- `native-image-agent` can generate hints by tracing a JVM run: add `-agentlib:native-image-agent=config-output-dir=hints/` to a JVM test run.
- Serverless (AWS Lambda, Google Cloud Run) is the primary use case where native startup time has measurable cost impact.
