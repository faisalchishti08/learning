---
card: spring-boot
gi: 247
slug: building-with-graalvm-native-build-tools
title: Building with GraalVM Native Build Tools
---

## 1. What it is

**GraalVM Native Build Tools** is a set of Maven and Gradle plugins published by the GraalVM team (`org.graalvm.buildtools`) that integrate the `native-image` compiler directly into your build lifecycle — without Docker, without Buildpacks.

- **Maven**: `native-maven-plugin` — adds `nativeCompile` and `nativeTest` goals.
- **Gradle**: `org.graalvm.buildtools.native` plugin — adds `nativeCompile` and `nativeTest` tasks.

Both are automatically configured by Spring Boot's `native` profile (Maven) or the Gradle plugin combination. You can also use them standalone for non-Spring projects.

The output is a **native executable** binary in `target/` (Maven) or `build/native/nativeCompile/` (Gradle) — a self-contained OS binary, not a container image.

## 2. Why & when

Choose Native Build Tools when:

- You need the native binary as a **file** (not an OCI image), e.g. to embed in a tar, RPM, or deploy via `scp`.
- You want **full control** over `native-image` arguments (memory limits, build-time initialisation classes, custom feature flags).
- You want native **test execution** (`nativeTest`) — running your JUnit tests compiled to native.
- Docker is not available in your CI environment.

Choose Buildpacks instead when you prefer a no-local-GraalVM, OCI-first workflow.

## 3. Core concept

`native-image` is GraalVM's ahead-of-time compiler. It performs a **closed-world analysis**: starting from the application's entry points, it traces all reachable code, eliminates everything unreachable, and compiles the reachable graph to machine code. The result needs no JVM at runtime.

**Native Build Tools** bridges the Maven/Gradle lifecycle and `native-image`:

1. **AOT phase** (Spring's `process-aot`) generates registrar classes and hint JSONs.
2. **Compile phase** compiles AOT-generated sources alongside your app.
3. **`nativeCompile`** goal/task invokes `native-image` with:
   - The fat-jar or exploded classpath as input.
   - Hint JSONs from `META-INF/native-image/` passed via `-H:ConfigurationFileDirectories`.
   - Any `<buildArgs>` you added in the plugin config.

The plugin also handles **reachability metadata** from the GraalVM community repository — pre-built hint JSONs for popular libraries that haven't added native support natively.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Native Build Tools pipeline: source to native binary via native-image tool">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <rect x="10" y="95" width="100" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="60" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Source +</text>
  <text x="60" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Spring deps</text>

  <rect x="140" y="75" width="130" height="64" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="205" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">process-aot</text>
  <text x="205" y="113" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Registrar .java</text>
  <text x="205" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">+ hint JSONs</text>

  <rect x="300" y="95" width="110" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="355" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">javac</text>
  <text x="355" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">all .class files</text>

  <rect x="440" y="75" width="120" height="64" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="500" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">native-image</text>
  <text x="500" y="113" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">GraalVM tool</text>
  <text x="500" y="127" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">closed-world AOT</text>

  <rect x="590" y="95" width="100" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="640" y="113" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">./myapp</text>
  <text x="640" y="129" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">native binary</text>

  <line x1="110" y1="117" x2="138" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="270" y1="117" x2="298" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="410" y1="117" x2="438" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="560" y1="117" x2="588" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GraalVM JDK must be on PATH — no Docker needed — output is a native OS binary</text>
</svg>

Native Build Tools calls `native-image` directly; GraalVM JDK on `PATH` is the only runtime prerequisite.

## 5. Runnable example

```java
// NativeBuildToolsDemo.java — run with: java NativeBuildToolsDemo.java
// Prints the Maven and Gradle configuration for Native Build Tools,
// explains key plugin options, and shows what the compiled output looks like.

public class NativeBuildToolsDemo {

    public static void main(String[] args) {
        System.out.println("=== GraalVM Native Build Tools for Spring Boot ===\n");
        printMavenConfig();
        printGradleConfig();
        printBuildArgs();
        printOutputLocations();
    }

    static void printMavenConfig() {
        System.out.println("--- Maven (pom.xml) ---");
        System.out.println("""
            <!-- Inherit spring-boot-starter-parent: native profile already configures -->
            <!-- native-maven-plugin. To customise build args, override the plugin:    -->
            <plugin>
              <groupId>org.graalvm.buildtools</groupId>
              <artifactId>native-maven-plugin</artifactId>
              <configuration>
                <imageName>myapp</imageName>
                <buildArgs>
                  <buildArg>--no-fallback</buildArg>
                  <buildArg>-H:+ReportExceptionStackTraces</buildArg>
                  <buildArg>-J-Xmx8g</buildArg>   <!-- heap for the image builder -->
                </buildArgs>
              </configuration>
            </plugin>

            <!-- Commands: -->
            <!--   mvn -Pnative package         => target/myapp         -->
            <!--   mvn -PnativeTest test         => native test run      -->
            """);
    }

    static void printGradleConfig() {
        System.out.println("--- Gradle (build.gradle) ---");
        System.out.println("""
            plugins {
              id 'org.springframework.boot'       version '3.3.0'
              id 'io.spring.dependency-management' version '1.1.4'
              id 'org.graalvm.buildtools.native'  version '0.10.2'
            }

            graalvmNative {
              binaries {
                main {
                  imageName = 'myapp'
                  buildArgs.add('--no-fallback')
                  buildArgs.add('-J-Xmx8g')
                }
              }
            }

            // ./gradlew nativeCompile  => build/native/nativeCompile/myapp
            // ./gradlew nativeTest     => run tests as native
            """);
    }

    static void printBuildArgs() {
        System.out.println("--- Key native-image flags ---");
        String[][] flags = {
            {"--no-fallback",
             "Fail if image cannot be built (don't silently fall back to JVM mode)"},
            {"-H:+ReportExceptionStackTraces",
             "Include full stack traces in native image (useful for debugging)"},
            {"--initialize-at-build-time=com.example",
             "Run static initialisers at build time (faster startup, care required)"},
            {"-J-Xmx8g",
             "Give the native-image compiler 8 GB heap (complex apps need 6-12 GB)"},
            {"--enable-preview",
             "Enable Java preview features in the native binary"},
        };
        for (var f : flags) {
            System.out.printf("  %-48s  %s%n", f[0], f[1]);
        }
    }

    static void printOutputLocations() {
        System.out.println("\n--- Output locations ---");
        System.out.println("  Maven  : target/<imageName>            (e.g. target/myapp)");
        System.out.println("  Gradle : build/native/nativeCompile/   (e.g. build/native/nativeCompile/myapp)");
        System.out.println("\n--- Run the binary ---");
        System.out.println("  ./target/myapp --server.port=9090");
        System.out.println("  # No java command, no JVM, starts in < 200 ms");
    }
}
```

**How to run:** `java NativeBuildToolsDemo.java`

## 6. Walkthrough

- **`--no-fallback`** — critical flag. Without it, if `native-image` can't resolve some dynamic code, it silently falls back to bundling a full JVM, producing a "fallback image" that defeats the purpose. `--no-fallback` makes the build fail loudly instead.
- **`-J-Xmx8g`** — passes a JVM argument to the `native-image` *compiler process itself* (not the resulting binary). The compiler is a JVM application and needs substantial heap for large apps.
- **`-H:+ReportExceptionStackTraces`** — native images strip stack traces by default for size. This flag restores them. Useful during development; remove it for production to reduce binary size.
- **`--initialize-at-build-time`** — runs specified class static initialisers during the image build rather than at runtime. Speeds startup but requires those initialisers to be safe without a running JVM context (no file access, no network).
- **Reachability metadata** — the `add-reachability-metadata` plugin goal (in Maven) fetches pre-built hint JSONs from `github.com/oracle/graalvm-reachability-metadata` for libraries like Hibernate, Jackson, and Netty, saving you from writing those hints by hand.

## 7. Gotchas & takeaways

> **Build time is the pain point.** Expect 3–10 minutes for a medium Spring Boot app. `native-image` performs whole-program analysis; it is CPU and RAM intensive. On CI, use a build cache and parallelise only at the job level — `native-image` already uses all available cores internally.

> **Architecture is locked at compile time.** A binary built on `linux/amd64` does not run on `linux/arm64`. Cross-compilation is not yet supported by GraalVM; use the Buildpacks approach with `--platform` flags on a CI agent of the target architecture.

- Install GraalVM JDK 21+ (ships `native-image` built-in; no separate `gu install` needed).
- Check GraalVM is active: `java -version` should say `GraalVM CE` or `Oracle GraalVM`.
- `mvn -Pnative -DskipNativeTests package` — skip native tests (slow) during development.
- `mvn -PnativeTest test` — run the full test suite compiled to native (catches reflection issues tests miss on JVM).
- `nativeTest` failures on native often pass on JVM — those are reflection/serialisation gaps to fix with runtime hints.
