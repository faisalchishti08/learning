---
card: java
gi: 1035
slug: maven-lifecycle-pom
title: Maven lifecycle & POM
---

## 1. What it is

Maven builds a Java project by running a fixed sequence of named **phases** — the **default lifecycle** — where each phase does one job and every phase before it must complete first: `validate` → `compile` → `test` → `package` → `verify` → `install` → `deploy`. Running `mvn package` doesn't run *only* the package phase; it runs every phase from the start of the lifecycle up through `package`, in order. The **POM** (`pom.xml`, Project Object Model) is the XML file describing the project: its coordinates (group, artifact, version), its dependencies, and any plugin configuration that hooks additional behavior into specific lifecycle phases.

## 2. Why & when

Without a standardized lifecycle, every project would need its own bespoke build script defining "first compile, then run tests, then package" from scratch, and every developer moving between projects would need to relearn each one's specific build steps. Maven's fixed phase sequence means `mvn test` always means the same thing across every Maven project ever built — compile the code, then run the tests — and `mvn install` always means "do all of that, then also install the built artifact into the local repository for other local projects to depend on." The POM is what customizes *what happens* at each of those fixed phases (which dependencies are on the classpath, which plugin runs during `package`) without changing the phase sequence itself.

Understand the lifecycle phase order whenever you need to reason about *what actually ran* for a given Maven command — `mvn test` runs `compile` and `test` but never reaches `package`, so no JAR file is produced; `mvn package` runs `test` along the way (tests fail the build by default if `package` is reached with failing tests). Reach for the POM's `<dependencies>` and `<build><plugins>` sections to add libraries and additional build behavior (like the JaCoCo coverage plugin from [test coverage (JaCoCo)](1033-test-coverage-jacoco.md)) without needing to alter the underlying phase sequence at all.

## 3. Core concept

```xml
<!-- A minimal pom.xml -->
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>

    <!-- Coordinates: uniquely identify THIS project -->
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <packaging>jar</packaging>

    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>

    <dependencies>
        <!-- listed here, available on the classpath from `compile` onward -->
    </dependencies>
</project>
```

```
mvn validate  -- checks the project is correct and all necessary information is available
mvn compile   -- compiles the main source code (runs validate first)
mvn test      -- runs unit tests using a testing framework (runs compile first)
mvn package   -- packages compiled code into a JAR/WAR (runs test first)
mvn verify    -- runs checks on the results of integration tests
mvn install   -- installs the package into the local repository (~/.m2)
mvn deploy    -- copies the final package to a remote repository for sharing
```

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Maven default lifecycle phases in sequence: validate, compile, test, package, verify, install, deploy, with running package implying every earlier phase already ran">
  <rect x="10" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="50" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">validate</text>
  <rect x="100" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="140" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">compile</text>
  <rect x="190" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="230" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">test</text>
  <rect x="280" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">package</text>
  <rect x="370" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="410" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">verify</text>
  <rect x="460" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="500" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">install</text>
  <rect x="550" y="60" width="80" height="34" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="590" y="81" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">deploy</text>

  <line x1="90" y1="77" x2="100" y2="77" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="180" y1="77" x2="190" y2="77" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="270" y1="77" x2="280" y2="77" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="360" y1="77" x2="370" y2="77" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="450" y1="77" x2="460" y2="77" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="540" y1="77" x2="550" y2="77" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="320" y="30" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">`mvn package` runs everything up to and including this phase</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Running any phase implicitly runs every phase before it in the sequence.

## 5. Runnable example

Scenario: a simple Java application built with Maven, evolving from a bare, minimal POM into one that shows exactly what runs at each lifecycle phase, and how phases build on each other.

### Level 1 — Basic

```xml
<!-- File: pom.xml -->
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
</project>
```

```java
// File: src/main/java/com/example/App.java
package com.example;

public class App {
    public static void main(String[] args) {
        System.out.println("Hello from the packaged app!");
    }
}
```

**How to run:** save both files in the shown directory structure, then run `mvn compile` from the project root.

Expected output (relevant excerpt):
```
[INFO] --- compiler:...:compile (default-compile) ---
[INFO] Compiling 1 source file
[INFO] BUILD SUCCESS
```

`mvn compile` ran the `validate` and `compile` phases (implicitly running `validate` first, since it precedes `compile` in the lifecycle) — but no tests ran, and no JAR was produced, since neither the `test` nor `package` phase was reached.

### Level 2 — Intermediate

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

```xml
<!-- File: pom.xml (adds the test dependency and packaging plugin needed for JUnit 5) -->
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
            </plugin>
        </plugins>
    </build>
</project>
```

**How to run:** run `mvn package` from the project root.

Expected output (relevant excerpt):
```
[INFO] --- compiler:...:compile (default-compile) ---
[INFO] --- surefire:...:test (default-test) ---
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
[INFO] --- jar:...:jar (default-jar) ---
[INFO] Building jar: .../target/my-app-1.0.0.jar
[INFO] BUILD SUCCESS
```

The real-world concern added: `mvn package` visibly ran `compile` (main code), then `test` (running `AppTest`, via the Surefire plugin), and finally `package` itself (producing the JAR) — demonstrating the lifecycle's guarantee that every earlier phase runs automatically before the requested one.

### Level 3 — Advanced

```xml
<!-- File: pom.xml (a failing test demonstrates that `package` genuinely depends on `test` passing) -->
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>my-app</artifactId>
    <version>1.0.0</version>
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    <dependencies>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
    <build>
        <plugins>
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>3.2.5</version>
            </plugin>
        </plugins>
    </build>
</project>
```

```java
// File: src/test/java/com/example/AppTest.java
package com.example;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;

public class AppTest {
    @Test
    void intentionallyFailingTest() {
        assertEquals(1, 2); // deliberately wrong, to observe the lifecycle stop here
    }
}
```

**How to run:** run `mvn package` from the project root.

Expected output (relevant excerpt):
```
[INFO] --- surefire:...:test (default-test) ---
[ERROR] AppTest.intentionallyFailingTest:9 expected: <1> but was: <2>
[INFO] Tests run: 1, Failures: 1, Errors: 0, Skipped: 0
[INFO] BUILD FAILURE
```

The production-flavored hard case: because `test` fails, Maven never reaches the `package` phase at all — no JAR is produced, and the build reports `BUILD FAILURE` immediately after the `test` phase, demonstrating concretely that later lifecycle phases genuinely depend on earlier ones succeeding, not just conceptually but as an enforced build behavior.

## 6. Walkthrough

Tracing `mvn package` against the Level 3 project:

1. Maven starts the default lifecycle for the `package` goal, which means running every phase up to and including `package`, in order: `validate`, `compile`, `test`, `package`.
2. `validate` runs first, confirming the project structure and `pom.xml` are well-formed — this succeeds silently (no visible output for a project this simple).
3. `compile` runs next, invoking the compiler plugin to compile `src/main/java` — since there's no `App.java` shown modified from Level 2, this succeeds (any main source compiles cleanly).
4. `test` runs next, invoking the Surefire plugin (configured in the POM's `<build><plugins>` section) to compile and run everything under `src/test/java` — `AppTest.intentionallyFailingTest` executes, and `assertEquals(1, 2)` fails, since `1` does not equal `2`.
5. Surefire reports this failure (`Tests run: 1, Failures: 1`), and because a test failed, Maven's default behavior is to **stop the build immediately** rather than proceeding — this is Maven enforcing the lifecycle dependency: `package` requires `test` to have completed *successfully*, not merely to have run.
6. The `package` phase itself — which would invoke the JAR plugin to bundle the compiled classes — is never reached at all. `mvn package`'s output ends with `BUILD FAILURE` right after the `test` phase's failure report, and no `target/my-app-1.0.0.jar` file is produced, confirming concretely that later phases in the lifecycle depend on earlier ones actually succeeding.

## 7. Gotchas & takeaways

> **Gotcha:** running `mvn test` alone never produces a packaged JAR, even if every test passes — `test` is an earlier phase than `package` in the lifecycle, and Maven only runs phases up to the one explicitly requested, never phases *after* it. A common mistake is expecting `mvn test` to also build the deployable artifact.

- Maven's default lifecycle is a fixed, ordered sequence of phases (`validate`, `compile`, `test`, `package`, `verify`, `install`, `deploy`); running any phase implicitly runs every phase before it, in order.
- The POM (`pom.xml`) declares the project's coordinates, dependencies, and plugin configuration — it customizes *what* happens at each fixed phase, without changing the phase sequence itself.
- A failing test stops the build before later phases (like `package`) run at all — this is Maven enforcing that `package`ing untested-or-failing code doesn't happen silently.
- Plugins (like Surefire for running tests, or JaCoCo for coverage — see [test coverage (JaCoCo)](1033-test-coverage-jacoco.md)) bind their own goals to specific lifecycle phases, extending what happens at that point without altering the overall phase order.
- Running `mvn install` (not just `mvn package`) is what makes a locally-built artifact available as a dependency for other projects on the same machine, via the local repository at `~/.m2`.
- See [Maven dependencies & scopes](1036-maven-dependencies-scopes.md) for how the `<dependencies>` section controls which libraries are available at which lifecycle phases (compile-time only, test-only, or both).
