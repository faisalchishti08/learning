---
card: spring-boot
gi: 27
slug: ant-ivy-support
title: Ant + Ivy support
---

## 1. What it is

**Apache Ant** is a build tool predating Maven and Gradle — it uses XML `build.xml` files and explicit task definitions (`<javac>`, `<jar>`, `<copy>`). There is no lifecycle, no convention, and no built-in dependency resolution.

**Apache Ivy** is a dependency management system that plugs into Ant, adding Maven Central repository resolution and an `ivy.xml` dependency descriptor file. Together, Ant + Ivy provides Maven-level dependency management to Ant projects.

Spring Boot offers **limited support** for Ant + Ivy projects through:
- An `ivy.xml` example that imports the `spring-boot-dependencies` BOM.
- A `spring-boot-antlib` module that provides Ant tasks for packaging fat JARs and building images.

**This is not the recommended path.** The Spring Boot documentation explicitly recommends Maven or Gradle. Ant + Ivy support exists for projects that cannot migrate away from Ant — a legacy constraint, not a preferred architecture.

## 2. Why & when

**When you'd use this:**
- You're maintaining a large legacy Java project built with Ant that predates Maven.
- Migrating to Maven or Gradle is not feasible short-term (organisational constraint, complex build scripts).
- You want to add Spring Boot functionality to this legacy system incrementally.

**Why Ant + Ivy is uncommon for new Spring Boot work:**
- No lifecycle conventions — every build task must be written manually.
- No plugin ecosystem comparable to Maven or Gradle.
- No Spring Initializr support — you start from scratch.
- The community and documentation for Spring Boot with Ant is thin.

For any new project, use Maven or Gradle. The only valid reason to choose Ant is if you're constrained by an existing build infrastructure.

## 3. Core concept

**`ivy.xml` for Spring Boot dependency management:**

```xml
<ivy-module version="2.0">
  <info organisation="com.example" module="myapp"/>

  <configurations>
    <conf name="compile" visibility="public"/>
    <conf name="runtime" extends="compile" visibility="public"/>
    <conf name="testCompile" extends="compile" visibility="private"/>
  </configurations>

  <dependencies>
    <!-- Import Spring Boot BOM -->
    <dependency org="org.springframework.boot"
                name="spring-boot-dependencies"
                rev="3.3.4"
                conf="compile->default" transitive="false"/>
    <!-- Add starters (rev will be resolved from the BOM) -->
    <dependency org="org.springframework.boot"
                name="spring-boot-starter-web"
                rev="latest.integration"
                conf="compile->default"/>
  </dependencies>
</ivy-module>
```

**`build.xml` with `spring-boot-antlib`:**

```xml
<project xmlns:sb="antlib:org.springframework.boot.ant">
  <taskdef resource="org/springframework/boot/ant/antlib.xml"
           uri="antlib:org.springframework.boot.ant"
           classpathref="spring-boot-antlib.classpath"/>

  <target name="package">
    <sb:exejar destfile="target/myapp.jar" classes="target/classes">
      <sb:lib>
        <fileset dir="lib" includes="*.jar"/>
      </sb:lib>
    </sb:exejar>
  </target>
</project>
```

The `<sb:exejar>` task builds a fat JAR with the Spring Boot launcher, similar to `spring-boot:repackage` in Maven or `bootJar` in Gradle.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Ant Ivy Spring Boot build flow showing ivy.xml resolving dependencies, ant build.xml compiling and packaging with spring-boot-antlib">
  <!-- ivy.xml -->
  <rect x="20" y="80" width="140" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="90" y="104" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">ivy.xml</text>
  <text x="90" y="120" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">deps + BOM import</text>
  <text x="90" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(Ivy resolver)</text>

  <line x1="160" y1="110" x2="200" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#antArr)"/>
  <text x="179" y="103" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolve</text>

  <!-- ivy resolves -->
  <rect x="200" y="60" width="160" height="100" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="280" y="84" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Ivy Resolver</text>
  <text x="280" y="104" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">downloads JARs</text>
  <text x="280" y="118" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">from Maven Central</text>
  <text x="280" y="134" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">into local cache</text>

  <line x1="360" y1="110" x2="400" y2="110" stroke="#8b949e" stroke-width="1.5" marker-end="url(#antArr2)"/>

  <!-- build.xml -->
  <rect x="400" y="60" width="160" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="84" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">build.xml</text>
  <text x="480" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;javac&gt; compile</text>
  <text x="480" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;sb:exejar&gt; package</text>
  <text x="480" y="134" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">spring-boot-antlib</text>

  <line x1="560" y1="110" x2="600" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#antArr3)"/>

  <!-- Output -->
  <rect x="600" y="88" width="48" height="44" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="624" y="108" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">fat</text>
  <text x="624" y="120" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">JAR</text>

  <defs>
    <marker id="antArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="antArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="antArr3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Ant + Ivy: Ivy resolves dependencies, Ant compiles, `spring-boot-antlib` packages the fat JAR.

## 5. Runnable example

```java
// File: AntIvyDemo.java
// Compares build tool approaches; Ant/Ivy is the legacy path.
// Run: java AntIvyDemo.java

import java.util.*;

public class AntIvyDemo {

    record BuildTool(String name, String config, String depManagement, String packaging,
                     String startNew, String legacySupport) {}

    public static void main(String[] args) {
        var tools = List.of(
            new BuildTool("Maven",
                "pom.xml (XML)",
                "spring-boot-starter-parent or BOM import — automatic",
                "spring-boot-maven-plugin (mvn package)",
                "★★★★★ Recommended",
                "★★★★★ Full support"),
            new BuildTool("Gradle",
                "build.gradle.kts (Kotlin DSL)",
                "io.spring.dependency-management plugin — semi-automatic",
                "spring-boot-gradle-plugin (bootJar)",
                "★★★★★ Recommended",
                "★★★★★ Full support"),
            new BuildTool("Ant + Ivy",
                "build.xml + ivy.xml (XML, verbose)",
                "ivy.xml BOM import — manual, limited",
                "spring-boot-antlib (sb:exejar task)",
                "★ Not recommended for new projects",
                "★★ Minimal, maintenance-only")
        );

        System.out.println("=== Build Tool Comparison for Spring Boot ===\n");
        for (var tool : tools) {
            System.out.println("Tool              : " + tool.name());
            System.out.println("Config file       : " + tool.config());
            System.out.println("Dep. management   : " + tool.depManagement());
            System.out.println("Packaging         : " + tool.packaging());
            System.out.println("New project       : " + tool.startNew());
            System.out.println("Legacy support    : " + tool.legacySupport());
            System.out.println();
        }

        System.out.println("=== When Ant/Ivy makes sense ===");
        System.out.println("  1. Existing large Ant build too costly to migrate immediately.");
        System.out.println("  2. Organisation has locked-down Ant-based CI infrastructure.");
        System.out.println("  3. Adding Spring Boot to one module of a large Ant project.");
        System.out.println();
        System.out.println("In all other cases: choose Maven or Gradle.");
    }
}
```

**How to run:** `java AntIvyDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Build Tool Comparison for Spring Boot ===

Tool              : Maven
Config file       : pom.xml (XML)
Dep. management   : spring-boot-starter-parent or BOM import — automatic
Packaging         : spring-boot-maven-plugin (mvn package)
New project       : ★★★★★ Recommended
Legacy support    : ★★★★★ Full support
...
```

## 6. Walkthrough

- **`BuildTool` record** — immutable data holder. Records in Java 16+ auto-generate the constructor, getters, `equals`, `hashCode`, and `toString`. Using `var tool : tools` with the enhanced for-loop reads idiomatically without repeating the type name.
- **Star ratings** — a concise way to communicate recommendation weight. Maven and Gradle both get five stars; Ant gets one for new projects because the Spring documentation and community strongly discourages it.
- **The three "when it makes sense" points** — based on the actual migration scenarios where Ant/Ivy is justified. These guide readers who inherit Ant projects to make an informed decision rather than reflexively migrating everything.

## 7. Gotchas & takeaways

> **`spring-boot-antlib` is bundled inside `spring-boot-tools`, not a separate download.** To use `<sb:exejar>`, you need `spring-boot-antlib-3.x.x.jar` on the Ant taskdef classpath. Retrieve it from Maven Central separately since Ivy doesn't automatically resolve antlib JARs for Ant tasks.

> **Ant has no lifecycle.** There is no equivalent of `mvn package` — you must manually chain targets: `<target depends="compile,test,package">`. Forget a dependency in the chain and your "build" silently uses stale class files.

- Ant + Ivy support is real but minimal. Use it only when you can't migrate to Maven or Gradle.
- `spring-boot-antlib` provides `<sb:exejar>` for fat JAR creation — the only Spring Boot-specific Ant task.
- `ivy.xml` can import the `spring-boot-dependencies` BOM for version management, but the integration is less automated than Maven or Gradle.
- For any new project or green-field work within a legacy Ant codebase, create the new modules in Maven or Gradle and integrate them into the Ant build via artifact dependencies rather than mixing build tools.
- Migration path: Ant → Maven is straightforward using `mvn archetype:generate` for the structure and copying Ant's dependency list to Maven dependencies.
