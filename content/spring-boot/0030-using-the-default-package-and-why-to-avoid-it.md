---
card: spring-boot
gi: 30
slug: using-the-default-package-and-why-to-avoid-it
title: Using the 'default' package (and why to avoid it)
---

## 1. What it is

The **default package** is what Java uses when a class has no `package` statement at the top of the file. For example:

```java
// No package statement — this is in the DEFAULT package
public class HelloApp { ... }
```

vs a named package:

```java
package com.example.myapp;  // properly declared package
public class HelloApp { ... }
```

In Spring Boot, placing your main class (the one annotated with `@SpringBootApplication`) in the default package causes `@ComponentScan` to scan *all* classes in *all* JARs on the classpath — including third-party JARs, the Spring framework itself, and every library dependency.

Spring Boot's documentation explicitly warns against using the default package: "We recommend that you follow Java's recommended package naming conventions and use a reversed domain name (for example, `com.example.myproject`)."

## 2. Why & when

**Why it's a problem:**
- `@ComponentScan` with no base package defaults to scanning from the class's package. In the default package, every class on the classpath is technically in or under this "package."
- Spring Boot will attempt to process every class in every JAR as a potential Spring bean or configuration class. This causes extremely slow startup, potential `BeanDefinitionStoreException` errors, and unexpected beans appearing in your context.
- Auto-configuration classes in `spring-boot-autoconfigure.jar` may be detected as regular `@Configuration` classes and applied twice, causing duplicate bean errors.

**When this comes up:**
- Quick prototypes without proper package setup.
- Students following tutorials that omit the package declaration.
- Refactoring that accidentally removes the package statement.

**The fix is always the same:** add a proper `package` declaration to your main class and all other classes. Spend 30 seconds now to avoid cryptic startup failures.

## 3. Core concept

`@SpringBootApplication` includes `@ComponentScan`. By default, `@ComponentScan` scans:
- The exact package the annotated class is in.
- All sub-packages of that package.

In a named package `com.example.myapp`:
- Scans: `com.example.myapp`, `com.example.myapp.controller`, `com.example.myapp.service`, etc.
- Ignores: `org.springframework.*`, `com.fasterxml.*`, your Tomcat JARs — because they're not under `com.example.myapp`.

In the default package (no package):
- Scans from the root — which means *everything*.
- Includes `org.springframework.boot.autoconfigure.web.WebMvcAutoConfiguration` and hundreds of other classes that happen to be on the classpath.

The recommended package structure:

```
com/
└── example/
    └── myapp/
        ├── MyApp.java            ← @SpringBootApplication here
        ├── controller/
        │   └── OrderController.java
        ├── service/
        │   └── OrderService.java
        └── repository/
            └── OrderRepository.java
```

Your `@SpringBootApplication` class should be at the **root of your application's package tree** — not deeper. If it's at `com.example.myapp.App`, the scan covers `com.example.myapp`. Moving it to `com.example.App` would miss `com.example.myapp.*`.

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Side-by-side comparison of default package scan (scans everything) vs named package scan (scans only your code)">
  <!-- Left: bad — default package -->
  <rect x="20" y="20" width="290" height="200" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="165" y="46" fill="#8b949e" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Default package — avoid</text>

  <rect x="36" y="58" width="258" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="77" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@ComponentScan scans ALL classes</text>

  <rect x="36" y="94" width="258" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="109" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ your App.java (intended)</text>
  <rect x="36" y="118" width="258" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ org.springframework.boot.autoconfigure.*</text>
  <rect x="36" y="142" width="258" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ com.fasterxml.jackson.*</text>
  <rect x="36" y="166" width="258" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="165" y="181" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ org.apache.tomcat.*</text>
  <text x="165" y="208" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ slow startup, errors, unexpected beans</text>

  <!-- Right: good — named package -->
  <rect x="350" y="20" width="290" height="200" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="46" fill="#6db33f" font-size="12" font-weight="bold" text-anchor="middle" font-family="sans-serif">Named package — correct</text>

  <rect x="366" y="58" width="258" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@ComponentScan(com.example.myapp)**</text>

  <rect x="366" y="94" width="258" height="20" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="109" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ com.example.myapp.App</text>
  <rect x="366" y="118" width="258" height="20" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ com.example.myapp.controller.*</text>
  <rect x="366" y="142" width="258" height="20" rx="3" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="495" y="157" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">✓ com.example.myapp.service.*</text>
  <rect x="366" y="166" width="258" height="20" rx="3" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="495" y="181" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">— org.springframework.* (ignored)</text>
  <text x="495" y="208" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">→ fast startup, only your beans</text>
</svg>

Named package limits `@ComponentScan` to your code only. Default package forces a full-classpath scan.

## 5. Runnable example

```java
// File: PackageScanDemo.java
// Demonstrates how ComponentScan scope is determined by the annotated class's package.
// Run: java PackageScanDemo.java

import java.util.*;

public class PackageScanDemo {

    // Simulates what Spring Boot scans given a base package
    static List<String> simulateScan(String basePackage, List<String> allClassesOnClasspath) {
        if (basePackage.isEmpty()) {
            // Default package: scan everything on classpath
            return allClassesOnClasspath;
        }
        // Named package: only classes under the base package
        return allClassesOnClasspath.stream()
            .filter(cls -> cls.startsWith(basePackage + ".") || cls.equals(basePackage))
            .toList();
    }

    public static void main(String[] args) {
        // Simulate a realistic classpath
        var classpath = List.of(
            "App",                                                    // default package class (no dot prefix)
            "com.example.myapp.App",                                  // main class
            "com.example.myapp.controller.OrderController",
            "com.example.myapp.service.OrderService",
            "com.example.myapp.repository.OrderRepository",
            "org.springframework.boot.autoconfigure.web.WebMvcAutoConfiguration",
            "org.springframework.boot.autoconfigure.data.jpa.JpaRepositoriesAutoConfiguration",
            "com.fasterxml.jackson.databind.ObjectMapper",
            "org.apache.tomcat.embed.core.TomcatEmbedded"
        );

        System.out.println("=== Scenario 1: Main class in DEFAULT package ===");
        System.out.println("package statement: (none)");
        System.out.println("@ComponentScan base: (everything)");
        System.out.println();
        var defaultScan = simulateScan("", classpath);
        System.out.println("Scanned classes (" + defaultScan.size() + "):");
        defaultScan.forEach(c -> System.out.println("  " + c));
        System.out.println("→ Spring tries to process every class on the classpath!");

        System.out.println();
        System.out.println("=== Scenario 2: Main class in 'com.example.myapp' ===");
        System.out.println("package statement: package com.example.myapp;");
        System.out.println("@ComponentScan base: com.example.myapp");
        System.out.println();
        var namedScan = simulateScan("com.example.myapp", classpath);
        System.out.println("Scanned classes (" + namedScan.size() + "):");
        namedScan.forEach(c -> System.out.println("  " + c));
        System.out.println("→ Only your application classes. Fast and clean.");
    }
}
```

**How to run:** `java PackageScanDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Scenario 1: Main class in DEFAULT package ===
Scanned classes (9):
  App
  com.example.myapp.App
  com.example.myapp.controller.OrderController
  ... (all 9 classes, including Spring and Tomcat internals)
→ Spring tries to process every class on the classpath!

=== Scenario 2: Main class in 'com.example.myapp' ===
Scanned classes (4):
  com.example.myapp.App
  com.example.myapp.controller.OrderController
  com.example.myapp.service.OrderService
  com.example.myapp.repository.OrderRepository
→ Only your application classes. Fast and clean.
```

## 6. Walkthrough

- **`simulateScan(basePackage, classpath)`** — if `basePackage` is empty (default package), return all classes. Otherwise, filter to those starting with `basePackage + "."`. This mirrors `ClassPathScanningCandidateComponentProvider`'s behaviour in Spring.
- **Default package result** — 9 classes including Spring, Jackson, and Tomcat internals. In a real application with hundreds of JARs, this would be thousands of classes.
- **Named package result** — exactly 4 classes, all your own code. Spring auto-configuration classes are still applied (they're on the classpath), but via the `AutoConfiguration.imports` mechanism, not `@ComponentScan`. This is correct behaviour.
- **The `+  "."` suffix** — ensures `com.example.myapp.something` matches but `com.example.myappother` does not. This is the standard package prefix check.

## 7. Gotchas & takeaways

> **The default package is not just "bad practice" — it breaks Spring Boot.** If your main class is in the default package, Spring Boot logs warnings at startup and may fail entirely depending on what it encounters scanning third-party JARs.

> **Your main class doesn't have to be at the top of your package tree, but it should be.** If `App.java` is in `com.example.myapp.startup`, the scan covers `com.example.myapp.startup.*` but misses `com.example.myapp.service.*`. Either place the main class in `com.example.myapp` or explicitly set `scanBasePackages = {"com.example.myapp"}` in `@SpringBootApplication`.

- Never use the default package in Spring Boot projects. Always add a `package com.example.myapp;` statement.
- The main class with `@SpringBootApplication` should be in the top-level package of your application.
- Use reversed domain name convention: `com.yourcompany.projectname`.
- `@SpringBootApplication(scanBasePackages = {"com.example.module1", "com.example.module2"})` explicitly controls the scan when a single root package isn't suitable.
- If startup is unexpectedly slow and you see thousands of `@Component` candidates logged, a missing package declaration is the first thing to check.
