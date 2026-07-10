---
card: java
gi: 1036
slug: maven-dependencies-scopes
title: Maven dependencies & scopes
---

## 1. What it is

A Maven **dependency** is a library your project needs, declared in `pom.xml` by its coordinates (`groupId`, `artifactId`, `version`) — Maven downloads it (and, transitively, whatever *that* library itself depends on) from a repository automatically. A dependency's **scope** controls *when* it's available: on the compile classpath, the test classpath, or neither at runtime in the final package — the most common scopes being `compile` (the default: needed everywhere, bundled into the final artifact), `test` (only needed for compiling and running tests — never bundled into the shipped application), `provided` (needed to compile against, but supplied by the runtime environment rather than bundled), and `runtime` (not needed to compile against, only needed when the application actually runs).

## 2. Why & when

Bundling every dependency with `compile` scope regardless of when it's actually needed would ship test-only libraries (JUnit, Mockito) inside the production JAR, bloating it with code that will never run in production and, worse, potentially introducing security-relevant dependencies into a deployed artifact that has no business being there. Scopes exist to draw this line precisely: `test`-scoped dependencies are on the classpath only while compiling and running tests, `provided`-scoped dependencies (like a servlet API supplied by an application server) are visible at compile time but deliberately excluded from the final package since the environment already provides them, and `runtime`-scoped dependencies (like a JDBC driver, used only via reflection at runtime and never referenced directly in your source code) skip compile-time visibility entirely.

Use the default `compile` scope for anything your production code directly imports and needs both to compile and to run. Use `test` scope for testing frameworks and test-only utilities (JUnit, Mockito, AssertJ) that must never ship in the production artifact. Use `provided` when the target deployment environment already supplies a dependency (a container-provided servlet API). Use `runtime` for dependencies needed only when the application executes, not referenced directly in your source code (many JDBC drivers, loaded by class name at runtime).

## 3. Core concept

```xml
<dependencies>
    <!-- compile (default): needed to compile AND run, bundled into the final artifact -->
    <dependency>
        <groupId>com.fasterxml.jackson.core</groupId>
        <artifactId>jackson-databind</artifactId>
        <version>2.17.0</version>
    </dependency>

    <!-- test: only on the classpath for compiling/running tests -- NEVER shipped -->
    <dependency>
        <groupId>org.junit.jupiter</groupId>
        <artifactId>junit-jupiter</artifactId>
        <version>5.10.2</version>
        <scope>test</scope>
    </dependency>

    <!-- runtime: needed when the app RUNS, not referenced directly in source code -->
    <dependency>
        <groupId>com.h2database</groupId>
        <artifactId>h2</artifactId>
        <version>2.2.224</version>
        <scope>runtime</scope>
    </dependency>

    <!-- provided: needed to COMPILE against, but supplied by the deployment
         environment itself -- deliberately excluded from the final artifact -->
    <dependency>
        <groupId>jakarta.servlet</groupId>
        <artifactId>jakarta.servlet-api</artifactId>
        <version>6.0.0</version>
        <scope>provided</scope>
    </dependency>
</dependencies>
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Four dependency scopes shown against compile-time and runtime classpath availability, and whether each is bundled into the final packaged artifact">
  <rect x="10" y="10" width="620" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="150" y="30" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">compile-time</text>
  <text x="470" y="30" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">runtime / bundled?</text>

  <rect x="10" y="50" width="620" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="60" y="70" fill="#e6edf3" font-size="9" font-family="sans-serif">compile</text>
  <text x="470" y="70" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">yes -- yes, bundled</text>

  <rect x="10" y="90" width="620" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="60" y="110" fill="#e6edf3" font-size="9" font-family="sans-serif">test</text>
  <text x="470" y="110" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">test-only -- NEVER bundled</text>

  <rect x="10" y="130" width="620" height="30" rx="4" fill="#1c2430" stroke="#f0883e"/>
  <text x="60" y="150" fill="#e6edf3" font-size="9" font-family="sans-serif">provided</text>
  <text x="470" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">yes -- NOT bundled (env supplies it)</text>

  <rect x="10" y="170" width="620" height="20" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="60" y="185" fill="#e6edf3" font-size="8" font-family="sans-serif">runtime -- no compile-time visibility, yes bundled</text>
</svg>

Each scope draws a different boundary between "visible while compiling," "visible while running," and "bundled into the shipped artifact."

## 5. Runnable example

Scenario: a small application using Jackson for JSON, JUnit for tests, and an H2 database driver, evolving from an undifferentiated dependency list into properly scoped dependencies.

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
    <dependencies>
        <!-- Everything left at the DEFAULT compile scope -- including test-only
             libraries, which means they'd be bundled into the shipped artifact. -->
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.17.0</version>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.2</version>
        </dependency>
    </dependencies>
</project>
```

**How to run:** save as `pom.xml`, then run `mvn dependency:tree` from the project root.

Expected output (relevant excerpt):
```
[INFO] com.example:my-app:jar:1.0.0
[INFO] +- com.fasterxml.jackson.core:jackson-databind:jar:2.17.0:compile
[INFO] \- org.junit.jupiter:junit-jupiter:jar:5.10.2:compile
```

Both `jackson-databind` (genuinely needed in production) and `junit-jupiter` (only needed for testing) show the same `compile` scope — meaning JUnit's classes would end up bundled into the final shipped JAR unnecessarily.

### Level 2 — Intermediate

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
    <dependencies>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.17.0</version>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.2</version>
            <scope>test</scope> <!-- correctly scoped: test classpath only -->
        </dependency>
    </dependencies>
</project>
```

**How to run:** run `mvn dependency:tree` from the project root.

Expected output (relevant excerpt):
```
[INFO] com.example:my-app:jar:1.0.0
[INFO] +- com.fasterxml.jackson.core:jackson-databind:jar:2.17.0:compile
[INFO] \- org.junit.jupiter:junit-jupiter:jar:5.10.2:test
```

The real-world concern added: `junit-jupiter` is now correctly `test`-scoped — it's available while compiling and running tests, but excluded from the final packaged JAR entirely, keeping the shipped artifact free of test-only code.

### Level 3 — Advanced

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
    <dependencies>
        <dependency>
            <groupId>com.fasterxml.jackson.core</groupId>
            <artifactId>jackson-databind</artifactId>
            <version>2.17.0</version>
        </dependency>
        <dependency>
            <groupId>org.junit.jupiter</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>5.10.2</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.mockito</groupId>
            <artifactId>mockito-core</artifactId>
            <version>5.11.0</version>
            <scope>test</scope>
        </dependency>
        <!-- runtime: loaded by class name via JDBC's driver-manager mechanism,
             never imported directly in application source code -->
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <version>2.2.224</version>
            <scope>runtime</scope>
        </dependency>
    </dependencies>
</project>
```

```java
// File: src/main/java/com/example/App.java
package com.example;

public class App {
    public static void main(String[] args) throws Exception {
        // Loaded purely BY NAME at runtime -- App.java never has an `import
        // org.h2...` statement anywhere, which is exactly why `runtime` scope
        // (not `compile`) is the correct, precise choice for the H2 driver.
        Class.forName("org.h2.Driver");
        System.out.println("H2 driver loaded successfully at runtime");
    }
}
```

**How to run:** save both files in the shown structure, then run `mvn compile` (to confirm `App.java` compiles without ever referencing H2 directly) followed by `mvn dependency:tree`.

Expected output (relevant excerpt from `dependency:tree`):
```
[INFO] com.example:my-app:jar:1.0.0
[INFO] +- com.fasterxml.jackson.core:jackson-databind:jar:2.17.0:compile
[INFO] +- org.junit.jupiter:junit-jupiter:jar:5.10.2:test
[INFO] +- org.mockito:mockito-core:jar:5.11.0:test
[INFO] \- com.h2database:h2:jar:2.2.224:runtime
```

The production-flavored hard case: `App.java`'s source code compiles cleanly with **zero** direct references to the H2 driver classes (it's loaded purely by class name via `Class.forName`), yet the driver must still be present on the classpath when the application actually *runs* — exactly the scenario `runtime` scope exists for: no compile-time visibility needed, but required at execution time.

## 6. Walkthrough

Tracing what happens across `mvn compile` followed by `mvn test` for the Level 3 project:

1. `mvn compile` runs the `compile` phase, which builds the classpath from every dependency whose scope makes it visible at compile time: `compile`-scoped `jackson-databind` and — notably — `provided`-scoped dependencies would also appear here (though none are declared in this example). `test`-scoped (`junit-jupiter`, `mockito-core`) and `runtime`-scoped (`h2`) dependencies are **not** on this classpath.
2. `App.java` compiles successfully despite never importing anything from `org.h2` — because the source code never references H2 classes directly (only `Class.forName("org.h2.Driver")`, a runtime string lookup), the compiler never needed H2 on its classpath at all, confirming `runtime` scope was the correct choice rather than `compile`.
3. `mvn test` runs `compile` first (as always, per the lifecycle), then builds the **test** classpath — this one includes everything from the compile classpath *plus* every `test`-scoped dependency: `junit-jupiter` and `mockito-core` become available, letting test classes import and use them freely.
4. If `App`'s `main` method were actually executed (say, via `mvn exec:java` or by running the packaged JAR), the **runtime** classpath would be assembled: `compile`-scoped and `runtime`-scoped dependencies both appear (`jackson-databind` and `h2`), but `test`-scoped dependencies do not — `junit-jupiter` and `mockito-core` are absent from a real running instance of the application, exactly as intended.
5. `Class.forName("org.h2.Driver")` executes at this point, using ordinary Java reflection to look up the `org.h2.Driver` class by its fully-qualified name on the current classpath — since `h2` is present on the runtime classpath (from step 4), this lookup succeeds, printing `"H2 driver loaded successfully at runtime"`.
6. Had `h2` mistakenly been left at `test` scope instead of `runtime`, this exact `Class.forName` call would throw a `ClassNotFoundException` the moment the application actually ran outside of a test context — a very common real-world Maven configuration mistake that only surfaces at runtime, precisely because compilation alone (which never needed H2 visible) would have succeeded regardless.

## 7. Gotchas & takeaways

> **Gotcha:** a dependency declared with `provided` scope is visible at compile time but deliberately excluded from the packaged artifact — if the actual deployment environment doesn't genuinely supply that dependency (a common mistake when moving from an application-server deployment model to a standalone one), the application will fail at runtime with a `ClassNotFoundException`, even though it compiled and packaged without any errors.

- `compile` (the default) is available everywhere and bundled into the final artifact — the right choice for anything production code directly imports and needs to both compile and run.
- `test` scope is available only for compiling and running tests, and is **never** bundled into the shipped artifact — the right choice for JUnit, Mockito, AssertJ, and any test-only utility.
- `provided` scope is visible at compile time but excluded from the final package, since the target deployment environment is expected to supply it — a mismatch between this assumption and the actual environment is a common source of runtime `ClassNotFoundException`s.
- `runtime` scope has no compile-time visibility at all, but is bundled and available when the application executes — the right choice for dependencies loaded by name (many JDBC drivers) rather than referenced directly in source code.
- `mvn dependency:tree` is the direct way to inspect exactly which scope each dependency (including transitive ones pulled in indirectly) actually has in your project.
- See [Maven lifecycle & POM](1035-maven-lifecycle-pom.md) for how these scoped classpaths map onto the specific lifecycle phases (`compile`, `test`, `package`) that build and consume them.
