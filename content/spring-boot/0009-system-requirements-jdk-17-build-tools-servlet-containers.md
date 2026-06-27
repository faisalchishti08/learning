---
card: spring-boot
gi: 9
slug: system-requirements-jdk-17-build-tools-servlet-containers
title: System requirements (JDK 17+, build tools, servlet containers)
---

## 1. What it is

Spring Boot 3.x has specific minimum version requirements for the Java runtime, build tools, and (when used) servlet containers. Meeting these requirements is a prerequisite before writing any code.

**Spring Boot 3.x requirements:**

| Component | Minimum version | Recommended |
|---|---|---|
| Java (JDK) | 17 | 21 (LTS) |
| Maven | 3.6.3 | 3.9.x |
| Gradle | 7.6.1 | 8.x |
| Tomcat (embedded) | 10.1 | (auto-managed by Boot) |
| Jetty (embedded) | 12.0 | (auto-managed by Boot) |
| Undertow | 2.3 | (auto-managed by Boot) |

**Key break from Spring Boot 2.x:** Spring Boot 3.x requires Java 17 minimum (Spring Boot 2.x supported Java 8+). This is because Spring Framework 6.x (which Boot 3.x is built on) uses Java 17 features and requires it.

## 2. Why & when

Understanding system requirements matters at three points:

1. **Project creation** — verify the JDK on your machine and CI server before generating a project from start.spring.io.
2. **Team onboarding** — new developers need the same JDK version to avoid "works on my machine" issues.
3. **Migration** — upgrading from Spring Boot 2.x to 3.x requires a JDK upgrade if you're still on Java 8 or 11.

**Why Java 17 minimum?**
- Spring Framework 6 uses Java 17 language features internally (records, sealed classes, pattern matching).
- Jakarta EE 9+ APIs (which Spring Boot 3.x targets) ship as `jakarta.*` packages — incompatible with Java EE's `javax.*` — and their implementations require Java 17.
- Java 17 is an LTS release with long-term security and performance support.

**Why not just Java 21?** Java 17 is the *minimum*. You can — and should — use Java 21 (the next LTS after 17) for new projects. Spring Boot 3.3+ officially supports Java 21 and its virtual threads via Project Loom.

## 3. Core concept

**JDK vs JRE:** You need the **JDK** (Java Development Kit) to compile and package Spring Boot applications. The JRE (Java Runtime Environment) is sufficient only for running a pre-built JAR. In production containers, you typically install only the JRE to reduce image size (e.g., `eclipse-temurin:21-jre`).

**Build tool role:** Maven or Gradle does four things for a Spring Boot project:
1. Downloads dependency JARs from Maven Central.
2. Compiles your source code against those JARs.
3. Runs tests.
4. Packages the fat JAR (via `spring-boot-maven-plugin` or `spring-boot-gradle-plugin`).

You don't need both — pick one. The project structure (`src/main/java`, `src/test/java`, etc.) is identical; only the build file differs.

**`jakarta.*` namespace (important):** Spring Boot 3.x targets Jakarta EE 10. If you see a `javax.servlet`, `javax.persistence`, or `javax.validation` import in old code, it must become `jakarta.servlet`, `jakarta.persistence`, `jakarta.validation` in Spring Boot 3.x. This is the most common migration surprise.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Dependency chain showing JDK 17 underpins Spring Framework 6 which underpins Spring Boot 3">
  <!-- Column: Spring Boot 2.x -->
  <rect x="20" y="20" width="290" height="200" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="165" y="46" fill="#8b949e" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot 2.x</text>

  <rect x="36" y="60" width="258" height="32" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="81" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Java 8 / 11 / 17 supported</text>

  <rect x="36" y="100" width="258" height="32" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="121" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Framework 5.x</text>

  <rect x="36" y="140" width="258" height="32" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="161" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">javax.* (Java EE) namespaces</text>

  <rect x="36" y="180" width="258" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="199" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Tomcat 9, Jetty 11</text>

  <!-- Column: Spring Boot 3.x -->
  <rect x="350" y="20" width="290" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="46" fill="#6db33f" font-size="13" font-weight="bold" text-anchor="middle" font-family="sans-serif">Spring Boot 3.x</text>

  <rect x="366" y="60" width="258" height="32" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="81" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Java 17+ required (21 recommended)</text>

  <rect x="366" y="100" width="258" height="32" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="121" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Framework 6.x</text>

  <rect x="366" y="140" width="258" height="32" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="495" y="161" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">jakarta.* (Jakarta EE 10) namespaces</text>

  <rect x="366" y="180" width="258" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="199" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Tomcat 10.1, Jetty 12</text>
</svg>

Spring Boot 3.x is a clean break: Java 17+, Spring 6, and `jakarta.*` — not backward-compatible with Boot 2.x at the classpath level.

## 5. Runnable example

```java
// File: SystemCheck.java
// Verifies your system meets Spring Boot 3.x requirements.
// Run: java SystemCheck.java

public class SystemCheck {

    public static void main(String[] args) {
        System.out.println("=== Spring Boot 3.x System Requirements Check ===\n");

        // Check Java version
        String javaVersion = System.getProperty("java.version");
        int major = Integer.parseInt(javaVersion.split("[.\\-]")[0]);
        boolean javaOk = major >= 17;
        System.out.printf("[%s] Java version: %s (need 17+)%n",
            javaOk ? "OK" : "FAIL", javaVersion);

        // Recommend 21 (LTS)
        if (javaOk && major < 21) {
            System.out.println("     Tip: Java 21 (LTS) is recommended for new projects.");
        }

        // Check for jakarta namespace (simulated)
        boolean jakartaAvailable;
        try {
            Class.forName("jakarta.servlet.http.HttpServlet");
            jakartaAvailable = true;
        } catch (ClassNotFoundException e) {
            jakartaAvailable = false;
        }
        // jakarta.servlet not on plain JDK classpath — that's expected
        System.out.printf("[INFO] jakarta.servlet on classpath: %s%n",
            jakartaAvailable ? "yes" : "no (add spring-boot-starter-web to a project)");

        // Check runtime info
        System.out.println();
        System.out.println("Runtime details:");
        System.out.println("  java.vendor  = " + System.getProperty("java.vendor"));
        System.out.println("  java.home    = " + System.getProperty("java.home"));
        System.out.println("  os.name      = " + System.getProperty("os.name"));
        System.out.println("  os.arch      = " + System.getProperty("os.arch"));

        System.out.println();
        System.out.println(javaOk
            ? "System meets Spring Boot 3.x Java requirement."
            : "UPGRADE REQUIRED: install JDK 17 or later.");
    }
}
```

**How to run:** `java SystemCheck.java` (JDK 17+, no dependencies needed).

Sample output on JDK 21:
```
=== Spring Boot 3.x System Requirements Check ===

[OK  ] Java version: 21.0.4 (need 17+)
[INFO] jakarta.servlet on classpath: no (add spring-boot-starter-web to a project)

Runtime details:
  java.vendor  = Eclipse Adoptium
  java.home    = /Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
  os.name      = Mac OS X
  os.arch      = aarch64

System meets Spring Boot 3.x Java requirement.
```

## 6. Walkthrough

- **`System.getProperty("java.version")`** — returns the JVM version string, e.g., `"21.0.4"` or `"17.0.12"`. We split on `.` or `-` (to handle strings like `"17.0.12"` and version strings like `"21-ea"`) and parse the major version number as an integer.
- **`major >= 17`** — the hard requirement for Spring Boot 3.x. If this check fails, `mvn spring-boot:run` will itself fail with a version mismatch error.
- **`Class.forName("jakarta.servlet.http.HttpServlet")`** — checks whether the Jakarta Servlet API is on the classpath. On a bare JDK it won't be; in a Spring Boot project with `spring-boot-starter-web` it will be. The demo shows the expected "no" result.
- **`System.getProperty("java.vendor")`** — reveals which JDK distribution you're running. Common choices are Eclipse Temurin (recommended), Amazon Corretto, Microsoft OpenJDK, and Oracle JDK. Spring Boot works with any of them.
- **`os.arch`** — relevant for ARM64 Macs (`aarch64`) and Apple Silicon Docker builds; JDK 17+ has stable `aarch64` support.

## 7. Gotchas & takeaways

> **`javax.*` to `jakarta.*` is a hard breaking change.** Every `import javax.servlet.*`, `import javax.persistence.*`, `import javax.validation.*` in your code must become `import jakarta.*` when migrating to Spring Boot 3.x. Many IDEs can do this automatically; IntelliJ IDEA has a dedicated migration assistant.

> **The build tool version matters for the plugin.** The `spring-boot-maven-plugin` 3.x requires Maven 3.6.3+. Running `mvn --version` before troubleshooting odd build failures can save time — an old Maven silently ignores plugin configuration instead of erroring.

- Spring Boot 3.x = Java 17 minimum, Spring Framework 6, Jakarta EE 10, Tomcat 10.1.
- Prefer Java 21 (LTS) for new projects — Spring Boot 3.3+ supports virtual threads via `spring.threads.virtual.enabled=true`.
- Build tool: use Maven 3.9.x or Gradle 8.x; both are managed by the Spring Boot Maven/Gradle plugin.
- `java --version` and `mvn --version` / `./gradlew --version` before blaming Spring Boot for a build error.
- For Docker: use `eclipse-temurin:21-jre-alpine` as your base image — slim, secure, officially supported.
