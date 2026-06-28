---
card: spring-boot
gi: 245
slug: spring-boot-starter-parent-native-profile
title: spring-boot-starter-parent native profile
---

## 1. What it is

`spring-boot-starter-parent` is the Maven parent POM that most Spring Boot projects inherit. Starting with Spring Boot 3.0, it ships a built-in Maven **profile named `native`** that wires together all the plugins and phases needed to produce a GraalVM native image — or an AOT-optimised JVM jar — with a single command.

Activating the profile (`-Pnative`) does four things automatically:

1. Runs `spring-boot:process-aot` during the `generate-sources` phase.
2. Configures the `native-maven-plugin` (from GraalVM) to compile the native image during `package`.
3. Sets correct flags so `spring-boot:build-image` calls Buildpacks in native mode.
4. Wires test AOT (`spring-boot:process-test-aot`) into the `generate-test-sources` phase.

For Gradle projects, the `org.springframework.boot` plugin plus `org.graalvm.buildtools.native` cover the same ground — the `native` profile is a Maven-specific convenience.

## 2. Why & when

Without the native profile you would have to manually:
- Declare and configure `native-maven-plugin` with correct `<buildArgs>`.
- Add execution bindings for AOT processing to the `generate-sources` lifecycle.
- Ensure AOT-generated sources land on the compile classpath.
- Configure the Buildpacks plugin to use the Paketo native image builder.

The native profile encodes those best practices so you don't repeat the boilerplate. Use it whenever you want a native image build and your project already extends `spring-boot-starter-parent`.

Skip it if you use `spring-boot-dependencies` BOM (no `<parent>`) — there you must replicate the plugin config manually, or use the Gradle equivalent.

## 3. Core concept

A Maven **profile** is a named set of POM overrides that activate on demand. Think of it as a feature flag for your build: the base POM stays clean, and `-Pnative` flips a switch that grafts additional plugins and configuration on top.

`spring-boot-starter-parent` defines the `native` profile roughly like this (simplified):

```xml
<profile>
  <id>native</id>
  <build>
    <pluginManagement>
      <!-- pins native-maven-plugin version -->
    </pluginManagement>
    <plugins>
      <plugin>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-maven-plugin</artifactId>
        <executions>
          <execution>
            <id>process-aot</id>
            <goals><goal>process-aot</goal></goals>
          </execution>
        </executions>
      </plugin>
      <plugin>
        <groupId>org.graalvm.buildtools</groupId>
        <artifactId>native-maven-plugin</artifactId>
        <executions>
          <execution>
            <id>add-reachability-metadata</id>
            <goals><goal>add-reachability-metadata</goal></goals>
          </execution>
          <execution>
            <id>build-native</id>
            <goals><goal>compile-no-fork</goal></goals>
            <phase>package</phase>
          </execution>
        </executions>
      </plugin>
    </plugins>
  </build>
</profile>
```

When you run `mvn -Pnative package`, Maven activates this profile, and the build sequence becomes: compile → process-aot → compile-generated → package → compile-native-image.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Maven lifecycle phases activated by the native profile">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Phase boxes -->
  <rect x="10" y="95" width="90" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="55" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">compile</text>
  <text x="55" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">your classes</text>

  <rect x="130" y="75" width="120" height="64" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="190" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">process-aot</text>
  <text x="190" y="113" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">generate-sources</text>
  <text x="190" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ AOT sources</text>

  <rect x="280" y="95" width="110" height="44" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="335" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">compile</text>
  <text x="335" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">AOT classes</text>

  <rect x="420" y="75" width="110" height="64" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="475" y="97" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">package</text>
  <text x="475" y="113" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">compile-no-fork</text>
  <text x="475" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">native-maven-plugin</text>

  <rect x="560" y="95" width="110" height="44" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="615" y="113" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">native binary</text>
  <text x="615" y="129" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">target/appname</text>

  <!-- arrows -->
  <line x1="100" y1="117" x2="128" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="250" y1="117" x2="278" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="390" y1="117" x2="418" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="530" y1="117" x2="558" y2="117" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- profile label -->
  <rect x="120" y="168" width="420" height="24" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="330" y="185" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">-Pnative activates these extra phases (blue/green)</text>
</svg>

Activating `-Pnative` inserts the AOT and native-compile phases into the standard Maven lifecycle.

## 5. Runnable example

```java
// NativeProfileDemo.java — run with: java NativeProfileDemo.java
// Shows the pom.xml snippets that the native profile wires in,
// then simulates what each phase does in sequence.

public class NativeProfileDemo {

    record Phase(String name, String plugin, String what) {}

    public static void main(String[] args) {
        System.out.println("=== Maven lifecycle with -Pnative ===\n");

        Phase[] phases = {
            new Phase("generate-sources",
                "spring-boot-maven-plugin:process-aot",
                "Boot app in AOT mode → write generated Java + hint JSONs"),
            new Phase("compile (2nd pass)",
                "maven-compiler-plugin",
                "Compile AOT-generated sources into target/classes"),
            new Phase("package",
                "native-maven-plugin:compile-no-fork",
                "GraalVM native-image tool reads classes + hints → native binary"),
        };

        for (Phase p : phases) {
            System.out.printf("[%s]%n  plugin : %s%n  action : %s%n%n",
                p.name(), p.plugin(), p.what());
        }

        System.out.println("Key pom.xml requirement:");
        System.out.println("""
            <parent>
              <groupId>org.springframework.boot</groupId>
              <artifactId>spring-boot-starter-parent</artifactId>
              <version>3.3.0</version>
            </parent>
            <!-- then just run: mvn -Pnative package -->
            """);

        System.out.println("Gradle equivalent:");
        System.out.println("""
            plugins {
              id 'org.springframework.boot' version '3.3.0'
              id 'org.graalvm.buildtools.native' version '0.10.2'
            }
            // then: ./gradlew nativeCompile
            """);
    }
}
```

**How to run:** `java NativeProfileDemo.java`

## 6. Walkthrough

- **`Phase` record** — each entry models one Maven lifecycle phase that `-Pnative` adds or augments. In a real build you see these in Maven's output as `[INFO] --- spring-boot-maven-plugin:... process-aot`.
- **`generate-sources` phase** — `process-aot` forks a child JVM, boots your Spring context in AOT mode, and dumps generated sources to `target/spring-aot/main/sources`. These don't exist in a normal (non-native) build.
- **Second compile pass** — the compiler picks up the AOT sources alongside your own classes. Maven's source-directory management (configured by the native profile) adds `target/spring-aot/main/sources` to the compile classpath automatically.
- **`package` phase with `compile-no-fork`** — `native-maven-plugin` invokes GraalVM's `native-image` tool, which reads compiled bytecode plus hint JSONs from `META-INF/native-image/` and produces a self-contained OS executable.
- **Gradle alternative** — there's no profile concept; instead the `org.graalvm.buildtools.native` Gradle plugin adds a `nativeCompile` task that does the same work.

## 7. Gotchas & takeaways

> **Inheriting `spring-boot-starter-parent` is required for the profile to exist.** If your project uses `<dependencyManagement>` with the BOM only (no `<parent>`), the `native` profile is not in your POM. You must copy the plugin configuration manually from the parent's source.

> **`-Pnative` does not automatically install GraalVM.** The `native-image` binary must be on `PATH`. Install GraalVM JDK 21+ (it ships `native-image` built-in) or use `gu install native-image` on older distributions. Alternatively, use Buildpacks (`mvn -Pnative spring-boot:build-image`) which download GraalVM inside a container.

- `mvn -Pnative package` — full native binary in `target/`.
- `mvn -Pnative spring-boot:build-image` — OCI image via Buildpacks (no local GraalVM needed).
- `mvn spring-boot:process-aot` without `-Pnative` — run AOT phase only, useful to inspect generated sources without a full native build.
- The profile does not change your runtime behaviour for JVM mode; `-Pnative` only affects the build pipeline.
- Check what the profile defines: `mvn help:effective-pom -Pnative | grep -A5 native-maven-plugin`.
