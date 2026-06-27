---
card: spring-boot
gi: 26
slug: gradle-dependency-management-plugin
title: Gradle dependency management plugin
---

## 1. What it is

The **`io.spring.dependency-management`** plugin is a Gradle plugin that brings Maven-style BOM (Bill of Materials) support to Gradle. Without it, Gradle has no native concept of "import a BOM and let it govern versions." With it applied, you can do in `build.gradle.kts`:

```kotlin
plugins {
    id("io.spring.dependency-management") version "1.1.6"
}
```

And then add dependencies without versions:

```kotlin
dependencies {
    implementation("org.springframework.boot:spring-boot-starter-web")  // version from BOM
}
```

The plugin imports the Spring Boot BOM automatically when `org.springframework.boot` plugin is also applied. The two plugins are always used together in Spring Boot Gradle projects.

**Note:** Gradle 5.x+ has *native BOM support* via `platform()`. The Spring dependency-management plugin predates this and uses a different mechanism, but both achieve version pinning without specifying versions.

## 2. Why & when

**The problem without the plugin:** Gradle's default version conflict resolution is "take the highest version." If your project depends on Library A (which wants Jackson 2.14) and Library B (which wants Jackson 2.17), Gradle picks 2.17 automatically — which may break Library A. There is no mechanism to *mandate* "use exactly the version the BOM says."

**What the plugin does:**
1. Imports `spring-boot-dependencies` BOM into Gradle's dependency resolution engine.
2. When a dependency with no version is declared, the plugin provides the BOM-managed version.
3. Overriding a version is still possible by specifying it explicitly.

**When to use it:**
- Every Spring Boot Gradle project (always apply it alongside `org.springframework.boot`).
- Any non-Spring Boot Gradle project where you want to import an external BOM for version management.

**Alternative: Gradle native BOM platform:**
```kotlin
// Native Gradle approach (Gradle 5.0+) — an alternative to the plugin
dependencies {
    implementation(platform("org.springframework.boot:spring-boot-dependencies:3.3.4"))
    implementation("org.springframework.boot:spring-boot-starter-web")
}
```
The plugin approach is still more common in Spring Boot projects; both work correctly.

## 3. Core concept

The plugin adds a `dependencyManagement` DSL block to your `build.gradle.kts`:

```kotlin
dependencyManagement {
    imports {
        mavenBom("org.springframework.boot:spring-boot-dependencies:3.3.4")
    }
}
```

When `org.springframework.boot` plugin is applied, it calls this automatically — you don't need to write the `dependencyManagement` block yourself. You would only write it explicitly if you want to add additional BOMs or override specific versions:

```kotlin
dependencyManagement {
    imports {
        mavenBom("org.springframework.boot:spring-boot-dependencies:3.3.4")
        mavenBom("org.springframework.cloud:spring-cloud-dependencies:2023.0.3")
    }
    dependencies {
        // Override a single version managed by the BOM
        dependency("com.fasterxml.jackson.core:jackson-databind:2.18.0")
    }
}
```

**Version override methods:**

| Method | Effect |
|---|---|
| `extra["jackson-bom.version"] = "2.18.0"` | Override via BOM property (recommended) |
| Explicit version in `dependencies {}` | Override single artifact |
| `dependencyManagement { dependencies { ... } }` | Override within the DSL |

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring dependency management plugin flow importing BOM and resolving versions for declared Gradle dependencies">
  <!-- Plugin box -->
  <rect x="20" y="60" width="220" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="130" y="84" fill="#6db33f" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">io.spring.dependency-management</text>
  <rect x="36" y="94" width="188" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="130" y="113" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">imports spring-boot-dependencies BOM</text>
  <text x="130" y="144" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">resolves version on lookup</text>

  <line x1="240" y1="110" x2="280" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#dmArr)"/>

  <!-- BOM -->
  <rect x="280" y="40" width="200" height="140" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="380" y="64" fill="#79c0ff" font-size="11" font-weight="bold" text-anchor="middle" font-family="sans-serif">spring-boot-dependencies</text>
  <text x="380" y="80" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BOM 3.3.4</text>
  <rect x="296" y="88" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="380" y="103" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">starter-web: 3.3.4</text>
  <rect x="296" y="114" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="380" y="129" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">jackson-databind: 2.17.2</text>
  <rect x="296" y="140" width="168" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="380" y="155" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">… 400+ entries</text>

  <line x1="480" y1="110" x2="520" y2="110" stroke="#79c0ff" stroke-width="2" marker-end="url(#dmArr2)"/>

  <!-- Resolved deps -->
  <rect x="520" y="60" width="120" height="100" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="580" y="84" fill="#6db33f" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Your declared</text>
  <text x="580" y="100" fill="#6db33f" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">dependencies</text>
  <text x="580" y="122" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">starter-web</text>
  <text x="580" y="136" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(no version)</text>
  <text x="580" y="152" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">→ 3.3.4</text>

  <defs>
    <marker id="dmArr"  markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="dmArr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The plugin hooks into Gradle's dependency resolution: when a version is missing, it consults the imported BOM and provides it.

## 5. Runnable example

```java
// File: DependencyManagementPluginDemo.java
// Compares native Gradle BOM platform vs the Spring dependency-management plugin.
// Run: java DependencyManagementPluginDemo.java

public class DependencyManagementPluginDemo {

    public static void main(String[] args) {
        System.out.println("=== Two ways to import a BOM in Gradle ===\n");

        System.out.println("--- Option 1: io.spring.dependency-management plugin ---");
        System.out.println("""
            // build.gradle.kts
            plugins {
                id("org.springframework.boot") version "3.3.4"
                id("io.spring.dependency-management") version "1.1.6"  // BOM support
                java
            }

            // BOM imported AUTOMATICALLY by spring boot plugin.
            // Optionally add more BOMs or overrides:
            dependencyManagement {
                imports {
                    mavenBom("org.springframework.cloud:spring-cloud-dependencies:2023.0.3")
                }
            }

            dependencies {
                implementation("org.springframework.boot:spring-boot-starter-web")  // no version
                implementation("org.springframework.cloud:spring-cloud-starter-openfeign") // no version
            }
            """);

        System.out.println("--- Option 2: Gradle native platform (no plugin) ---");
        System.out.println("""
            // build.gradle.kts
            plugins {
                id("org.springframework.boot") version "3.3.4"
                // NO dependency-management plugin
                java
            }

            dependencies {
                // Explicitly import BOM using Gradle's native 'platform()':
                implementation(platform("org.springframework.boot:spring-boot-dependencies:3.3.4"))
                implementation(platform("org.springframework.cloud:spring-cloud-dependencies:2023.0.3"))

                implementation("org.springframework.boot:spring-boot-starter-web")  // no version
                implementation("org.springframework.cloud:spring-cloud-starter-openfeign") // no version
            }
            """);

        System.out.println("=== Key differences ===");
        var diffs = new String[][]{
            {"Version override syntax",
                "extra[\"jackson-bom.version\"] = \"2.18.0\"",
                "strictly(\"2.18.0\") on the dependency"},
            {"DSL style",
                "dependencyManagement { imports { mavenBom(...) } }",
                "implementation(platform(...))"},
            {"Auto-import Spring BOM",
                "yes, via org.springframework.boot plugin",
                "no, must explicitly call platform()"},
            {"Spring Boot support",
                "official recommended way",
                "works, but requires adding platform() in dependencies"}
        };
        System.out.printf("  %-28s %-40s %s%n", "Aspect", "Plugin approach", "Native platform");
        System.out.println("  " + "-".repeat(90));
        for (var d : diffs) {
            System.out.printf("  %-28s %-40s %s%n", d[0], d[1], d[2]);
        }
    }
}
```

**How to run:** `java DependencyManagementPluginDemo.java` (JDK 17+, no dependencies needed).

## 6. Walkthrough

- **Option 1** — the traditional Spring Boot Gradle approach. The `org.springframework.boot` plugin automatically imports `spring-boot-dependencies` BOM via the `io.spring.dependency-management` plugin when both are applied. The `dependencyManagement` block is used only to add *additional* BOMs (like Spring Cloud) or to override specific versions.
- **Option 2** — Gradle's native `platform()` mechanism (available since Gradle 5.0). It's more idiomatic Gradle but requires writing `platform(...)` in the `dependencies` block rather than a separate `dependencyManagement` section. For Spring Boot projects, you'd also lose the auto-import — you must call `platform("org.springframework.boot:spring-boot-dependencies:3.3.4")` yourself.
- **Version override in Option 1** — `extra["jackson-bom.version"] = "2.18.0"` sets a Gradle extra property that the dependency-management plugin reads (mirroring the BOM's own property names from the Spring Boot docs).
- **Version override in Option 2** — Gradle `strictly()` constraint: `implementation("com.fasterxml.jackson.core:jackson-databind") { version { strictly("2.18.0") } }`. `strictly` means "this version exactly, reject anything else."

## 7. Gotchas & takeaways

> **The `io.spring.dependency-management` plugin version is independent from the Spring Boot version.** Plugin `1.1.6` works with any Spring Boot 3.x release. Don't try to match the plugin version to the Spring Boot version — they have separate release cycles.

> **Don't mix both approaches in the same project.** Applying `io.spring.dependency-management` and also calling `platform()` for the same BOM can cause double-import and confusing version resolution. Pick one pattern and stick with it.

- Apply `io.spring.dependency-management` alongside `org.springframework.boot` — both are needed.
- The Spring Boot BOM is imported automatically when both plugins are applied; no `dependencyManagement` block needed unless adding extra BOMs.
- Override a single version with `extra["property-name"] = "version"` or an explicit version in `dependencies {}`.
- Gradle native `platform()` is a valid alternative; both approaches produce the same resolved dependency graph.
- `./gradlew dependencies --configuration runtimeClasspath` shows the full resolved tree to diagnose conflicts.
