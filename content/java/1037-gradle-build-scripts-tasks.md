---
card: java
gi: 1037
slug: gradle-build-scripts-tasks
title: Gradle build scripts & tasks
---

## 1. What it is

Gradle is a build tool, like Maven, but instead of a fixed XML lifecycle it uses a **build script** (`build.gradle`, written in Groovy, or `build.gradle.kts`, written in Kotlin) that declares a graph of **tasks** — units of work like `compileJava`, `test`, or `jar` — each of which can declare dependencies on other tasks, forming a directed graph Gradle executes in the correct order. Running `gradle build` doesn't follow a fixed phase sequence the way Maven does; it resolves which tasks `build` depends on (directly and transitively) and runs exactly those, skipping any task whose inputs haven't changed since the last run — Gradle's **incremental build** and up-to-date checking.

## 2. Why & when

Maven's fixed lifecycle is easy to reason about but inflexible — customizing exactly what happens (adding a genuinely custom step that isn't just "run at this predefined phase") means writing a full plugin. Gradle's task graph is more flexible: a build script can define an entirely custom task with its own logic, wire it to depend on or be depended upon by any other task, and Gradle's build language (a real programming language, not XML) lets you express conditional logic directly in the build itself. Gradle's other headline advantage is speed on incremental builds: because Gradle tracks each task's declared inputs and outputs, a second build that changes only one source file re-runs only the tasks whose inputs actually changed, skipping everything already up to date — this matters far more on large, frequently-rebuilt projects than on small ones.

Reach for Gradle when a project's build has genuinely custom steps beyond what Maven's fixed lifecycle and plugin configuration comfortably express, or when incremental-build speed on a large codebase matters enough to justify learning Gradle's task-graph model. Maven's fixed lifecycle remains simpler to reason about for straightforward projects that just need "compile, test, package" — see [Maven lifecycle & POM](1035-maven-lifecycle-pom.md) for that model.

## 3. Core concept

```groovy
// File: build.gradle
plugins {
    id 'java'
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

test {
    useJUnitPlatform()
}

// A CUSTOM task, something Maven's fixed lifecycle has no equivalent for
// without writing a full plugin -- defined directly in the build script.
tasks.register('printProjectInfo') {
    doLast {
        println "Building ${project.name} version ${project.version}"
    }
}

// Wiring: make the custom task run automatically whenever 'build' runs
tasks.named('build') {
    dependsOn 'printProjectInfo'
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The build task depending on test, which depends on compileJava, plus a custom printProjectInfo task also wired as a dependency of build, forming a task graph Gradle resolves and executes in order">
  <rect x="30" y="70" width="130" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">compileJava</text>

  <rect x="220" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="265" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">test</text>

  <rect x="380" y="70" width="90" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="425" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">build</text>

  <rect x="380" y="20" width="160" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="460" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">printProjectInfo (custom)</text>

  <line x1="160" y1="90" x2="220" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="310" y1="90" x2="380" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="460" y1="54" x2="435" y2="70" stroke="#f0883e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`build` depends on `test`, which depends on `compileJava` — plus a custom task wired into the same graph.

## 5. Runnable example

Scenario: a simple Java project's build script, evolving from a bare Gradle setup into one with a custom task wired into the standard build graph.

### Level 1 — Basic

```groovy
// File: build.gradle
plugins {
    id 'java'
}

repositories {
    mavenCentral()
}

group = 'com.example'
version = '1.0.0'
```

```java
// File: src/main/java/com/example/App.java
package com.example;

public class App {
    public static void main(String[] args) {
        System.out.println("Hello from Gradle!");
    }
}
```

**How to run:** save both files in the shown structure (with a `settings.gradle` containing `rootProject.name = 'my-app'`), then run `gradle build` from the project root (or `./gradlew build` if using the Gradle wrapper).

Expected output (relevant excerpt):
```
> Task :compileJava
> Task :processResources NO-SOURCE
> Task :classes
> Task :jar
> Task :assemble
> Task :test NO-SOURCE
> Task :check
> Task :build

BUILD SUCCESSFUL
```

The `java` plugin alone provides the standard `compileJava`, `test`, `jar`, and `build` tasks with their dependency wiring already set up — but there's no custom logic yet beyond what the plugin provides by default.

### Level 2 — Intermediate

```groovy
// File: build.gradle
plugins {
    id 'java'
}

repositories {
    mavenCentral()
}

group = 'com.example'
version = '1.0.0'

dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

test {
    useJUnitPlatform() // required for Gradle's test task to recognize JUnit 5
}
```

```java
// File: src/test/java/com/example/AppTest.java
package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertTrue;

public class AppTest {
    @Test
    void placeholderTest() {
        assertTrue(true);
    }
}
```

**How to run:** run `gradle test` from the project root.

Expected output (relevant excerpt):
```
> Task :compileJava
> Task :compileTestJava
> Task :test

BUILD SUCCESSFUL
```

The real-world concern added: `gradle test` resolved that `test` depends on `compileTestJava`, which itself depends on `compileJava` — Gradle ran exactly those tasks, in the correct order, without needing an explicit phase sequence to be declared anywhere; it derived the order purely from the task dependency graph.

### Level 3 — Advanced

```groovy
// File: build.gradle
plugins {
    id 'java'
}

repositories {
    mavenCentral()
}

group = 'com.example'
version = '1.0.0'

dependencies {
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testRuntimeOnly 'org.junit.platform:junit-platform-launcher'
}

test {
    useJUnitPlatform()
}

// A custom task with NO Maven equivalent short of writing a full plugin --
// generates a version file as part of the build, using build-script logic.
tasks.register('generateVersionFile') {
    def outputFile = layout.buildDirectory.file('generated/version.txt')
    outputs.file(outputFile) // declaring outputs enables Gradle's up-to-date checking

    doLast {
        outputFile.get().asFile.parentFile.mkdirs()
        outputFile.get().asFile.text = "version=${project.version}\n"
        println "Generated version file with version ${project.version}"
    }
}

// Wire the custom task into the standard graph: 'build' now also runs this.
tasks.named('build') {
    dependsOn 'generateVersionFile'
}
```

**How to run:** run `gradle build` from the project root, then run `gradle build` again immediately afterward without changing anything.

Expected output (first run, relevant excerpt):
```
> Task :generateVersionFile
Generated version file with version 1.0.0
> Task :compileJava
> Task :test
> Task :build

BUILD SUCCESSFUL
```

Expected output (second run, with nothing changed):
```
> Task :generateVersionFile UP-TO-DATE
> Task :compileJava UP-TO-DATE
> Task :test UP-TO-DATE
> Task :build UP-TO-DATE

BUILD SUCCESSFUL
```

The production-flavored hard case: on the second run, every task shows `UP-TO-DATE` and none of their actual logic re-executes — Gradle compared each task's declared inputs and outputs against the previous run and determined nothing had changed, skipping the work entirely. This is Gradle's incremental build behavior, something Maven's phase-based model doesn't provide out of the box.

## 6. Walkthrough

Tracing `gradle build` on the second, unchanged run:

1. Gradle resolves the task graph for the `build` task: `build` depends on `generateVersionFile` (as wired) plus the standard tasks the `java` plugin already connects (`assemble`, which depends on `jar`, which depends on `classes`, which depends on `compileJava`; and `check`, which depends on `test`).
2. Before actually running `generateVersionFile`'s action, Gradle checks: does this task declare any inputs or outputs, and if so, have they changed since the last successful run? `generateVersionFile` declared `outputs.file(outputFile)` — Gradle compares the current state of that output file against a snapshot taken after the previous run.
3. Since the file already exists from the first run and nothing has changed `project.version` or any other input this task's action depends on, Gradle determines the task's outputs are still valid — it marks the task `UP-TO-DATE` and skips executing its `doLast { ... }` block entirely, meaning `"Generated version file..."` is not printed again.
4. The same up-to-date check happens for `compileJava`: Gradle compares the current `.java` source files against a snapshot from the last compilation — since nothing changed, it skips recompilation and marks the task `UP-TO-DATE`.
5. `test` similarly checks whether its inputs (compiled test classes, compiled main classes) have changed — they haven't, so it's also marked `UP-TO-DATE`, and the actual JUnit test run is skipped.
6. `build` itself, having all of its dependency tasks resolve to `UP-TO-DATE`, is also reported as `UP-TO-DATE`, and the overall build reports `BUILD SUCCESSFUL` almost instantly — none of the actual compilation, testing, or file-generation work was redone, since Gradle had cached, verifiable proof that none of it needed to be.

## 7. Gotchas & takeaways

> **Gotcha:** a custom task's up-to-date checking only works correctly if its inputs and outputs are declared accurately (`outputs.file(...)`, `inputs.files(...)`) — a task that reads or writes files Gradle doesn't know about (undeclared inputs/outputs) can either be incorrectly skipped when it should have re-run, or never benefit from the up-to-date optimization at all.

- Gradle build scripts declare a graph of tasks with explicit dependencies (`dependsOn`), rather than following Maven's fixed, predefined phase sequence.
- Custom tasks with arbitrary logic (Groovy or Kotlin code directly in the build script) are straightforward to write and wire into the standard graph — no separate plugin is required for simple custom steps.
- Gradle's incremental build compares each task's declared inputs and outputs against the previous run, skipping (`UP-TO-DATE`) any task whose relevant state hasn't changed — a major speed advantage on large, frequently-rebuilt projects.
- `useJUnitPlatform()` inside the `test` block is required for Gradle's built-in `test` task to recognize and run JUnit 5 tests; without it, JUnit 5 tests are silently skipped.
- Gradle's flexibility (a real scripting language) is also a discipline risk — build logic can become as tangled and hard-to-follow as any other codebase if custom tasks and dependency wiring aren't kept simple and well-organized.
- See [Maven lifecycle & POM](1035-maven-lifecycle-pom.md) for the alternative, fixed-lifecycle model Gradle's task graph is often compared against — Maven remains simpler to reason about for projects that don't need Gradle's flexibility or incremental-build performance.
