---
card: spring-boot
gi: 31
slug: locating-the-main-application-class
title: Locating the main application class
---

## 1. What it is

The **main application class** is the entry point of a Spring Boot application — the class annotated with `@SpringBootApplication` that contains the `public static void main(String[] args)` method. Its location in the project's package hierarchy determines:

1. **Component scan root** — which packages Spring searches for `@Component`, `@Service`, `@Controller`, etc.
2. **Auto-configuration context** — where Spring Boot applies its auto-configuration.
3. **Maven/Gradle main class detection** — the `spring-boot-maven-plugin` and Gradle plugin scan for a class with a `main` method to set as the `Main-Class` manifest attribute.

**Best practice:** place the main class in the **root package** of your application — the parent of all other packages you own.

```
src/main/java/
└── com/example/orderservice/        ← main class lives here
    ├── OrderServiceApplication.java  ← @SpringBootApplication
    ├── controller/
    │   └── OrderController.java
    ├── service/
    │   └── OrderService.java
    └── repository/
        └── OrderRepository.java
```

Naming convention: `{AppName}Application.java` — e.g., `OrderServiceApplication`, `PaymentServiceApplication`. The Spring Initializr generates the file with this name automatically.

## 2. Why & when

**Why location matters for component scanning:**
- `@ComponentScan` (included in `@SpringBootApplication`) scans the annotated class's package and all sub-packages.
- If the main class is at `com.example.orderservice`, every class in `com.example.orderservice.*` is discovered automatically.
- If the main class is placed too deep (e.g., `com.example.orderservice.config.App`), classes in sibling packages like `com.example.orderservice.controller` are missed.

**Why location matters for the build plugin:**
- The Maven and Gradle Spring Boot plugins look for a single class with a `public static void main` to declare as `Start-Class` in the fat JAR's manifest.
- If there are multiple classes with `main` methods, you must configure the plugin explicitly: `<configuration><mainClass>com.example.App</mainClass></configuration>`.

Know this when:
- Creating a new project — the Initializr puts the main class in the right place automatically; don't move it.
- Adding a second module — each Spring Boot module needs its own main class in its own root package.
- Diagnosing `@Component` classes that aren't being picked up — check that they're in a sub-package of the main class's package.

## 3. Core concept

The `@SpringBootApplication` annotation combines:
- `@ComponentScan` — default root is the package of the annotated class.
- `@EnableAutoConfiguration` — scans the classpath for auto-config, not the package tree.
- `@SpringBootConfiguration` — marks this class as a configuration source.

**Naming conventions:**
- Main class: `{ProjectName}Application` (e.g., `MyServiceApplication`)
- Package: reversed domain + project name (e.g., `com.acme.orders`)
- File path matches package: `src/main/java/com/acme/orders/MyServiceApplication.java`

**Multi-module projects:** each executable module has its own main class in its own root package. Shared library modules typically have no main class and no `@SpringBootApplication`.

**Explicit main class in Maven:**
```xml
<plugin>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-maven-plugin</artifactId>
  <configuration>
    <mainClass>com.example.myapp.Application</mainClass>
  </configuration>
</plugin>
```

**Explicit main class in Gradle:**
```kotlin
springBoot {
    mainClass.set("com.example.myapp.Application")
}
```

## 4. Diagram

<svg viewBox="0 0 660 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Project package structure showing main class at the root of the application packages with controllers services and repositories beneath it">
  <!-- File system tree -->
  <text x="40" y="30" fill="#6db33f" font-size="12" font-weight="bold" font-family="monospace">src/main/java/</text>
  <text x="40" y="52" fill="#e6edf3" font-size="11" font-family="monospace">└── com/example/orders/</text>

  <!-- Main class highlight -->
  <rect x="38" y="60" width="400" height="28" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="60" y="78" fill="#6db33f" font-size="11" font-family="monospace">    ├── OrdersApplication.java</text>
  <text x="380" y="78" fill="#6db33f" font-size="10" font-family="sans-serif">← @SpringBootApplication</text>

  <text x="40" y="108" fill="#e6edf3" font-size="11" font-family="monospace">    ├── controller/</text>
  <text x="40" y="126" fill="#8b949e" font-size="11" font-family="monospace">    │   └── OrderController.java</text>
  <text x="400" y="126" fill="#8b949e" font-size="10" font-family="sans-serif">← scanned ✓</text>
  <text x="40" y="144" fill="#e6edf3" font-size="11" font-family="monospace">    ├── service/</text>
  <text x="40" y="162" fill="#8b949e" font-size="11" font-family="monospace">    │   └── OrderService.java</text>
  <text x="400" y="162" fill="#8b949e" font-size="10" font-family="sans-serif">← scanned ✓</text>
  <text x="40" y="180" fill="#e6edf3" font-size="11" font-family="monospace">    └── repository/</text>
  <text x="40" y="198" fill="#8b949e" font-size="11" font-family="monospace">        └── OrderRepository.java</text>
  <text x="400" y="198" fill="#8b949e" font-size="10" font-family="sans-serif">← scanned ✓</text>

  <!-- Scan range indicator -->
  <rect x="528" y="58" width="112" height="174" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="584" y="98" fill="#6db33f" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">@Component</text>
  <text x="584" y="112" fill="#6db33f" font-size="10" font-weight="bold" text-anchor="middle" font-family="sans-serif">Scan</text>
  <text x="584" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">covers</text>
  <text x="584" y="146" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">com.example</text>
  <text x="584" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">.orders</text>
  <text x="584" y="176" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">and all</text>
  <text x="584" y="190" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">sub-packages</text>
</svg>

Main class at `com.example.orders` → scan covers everything beneath it, nothing outside it.

## 5. Runnable example

```java
// File: MainClassLocationDemo.java
// Shows how the main class location determines scan scope and manifest Start-Class.
// Run: java MainClassLocationDemo.java

import java.util.*;

public class MainClassLocationDemo {

    record ProjectStructure(String mainClass, String scanBase,
                            List<String> discoveredBeans, boolean allBeansCovered) {}

    static ProjectStructure simulate(String mainClass, List<String> projectClasses) {
        // Derive scan base from the main class's package
        int lastDot = mainClass.lastIndexOf('.');
        String scanBase = lastDot > 0 ? mainClass.substring(0, lastDot) : "";

        // Simulate component scan: only classes in the scan base package
        List<String> discovered = scanBase.isEmpty()
            ? new ArrayList<>(projectClasses)
            : projectClasses.stream()
                .filter(c -> c.startsWith(scanBase + "."))
                .toList();

        boolean allCovered = discovered.containsAll(projectClasses);
        return new ProjectStructure(mainClass, scanBase, discovered, allCovered);
    }

    public static void main(String[] args) {
        var projectClasses = List.of(
            "com.example.orders.controller.OrderController",
            "com.example.orders.service.OrderService",
            "com.example.orders.repository.OrderRepository"
        );

        System.out.println("=== Scenario A: Main class at correct root ===");
        var good = simulate("com.example.orders.OrdersApplication", projectClasses);
        System.out.println("Main class : " + good.mainClass());
        System.out.println("Scan base  : " + good.scanBase());
        System.out.println("Discovered : " + good.discoveredBeans());
        System.out.println("All found  : " + good.allBeansCovered());

        System.out.println();
        System.out.println("=== Scenario B: Main class buried too deep ===");
        var bad = simulate("com.example.orders.config.Application", projectClasses);
        System.out.println("Main class : " + bad.mainClass());
        System.out.println("Scan base  : " + bad.scanBase());
        System.out.println("Discovered : " + bad.discoveredBeans());
        System.out.println("All found  : " + bad.allBeansCovered() + " ← PROBLEM: beans are missing!");

        System.out.println();
        System.out.println("=== Fix for Scenario B ===");
        System.out.println("Option 1: Move main class to com.example.orders.Application");
        System.out.println("Option 2: @SpringBootApplication(scanBasePackages = {\"com.example.orders\"})");
    }
}
```

**How to run:** `java MainClassLocationDemo.java` (JDK 17+, no dependencies needed).

Expected output:
```
=== Scenario A: Main class at correct root ===
Main class : com.example.orders.OrdersApplication
Scan base  : com.example.orders
Discovered : [com.example.orders.controller.OrderController, ...]
All found  : true

=== Scenario B: Main class buried too deep ===
Main class : com.example.orders.config.Application
Scan base  : com.example.orders.config
Discovered : []
All found  : false ← PROBLEM: beans are missing!

=== Fix for Scenario B ===
Option 1: Move main class to com.example.orders.Application
Option 2: @SpringBootApplication(scanBasePackages = {"com.example.orders"})
```

## 6. Walkthrough

- **`simulate(mainClass, projectClasses)`** — extracts the package from the fully qualified main class name (everything before the last dot), then filters the project class list to those starting with that package. This mirrors Spring's `ClassPathScanningCandidateComponentProvider`.
- **Scenario A** — the main class is at `com.example.orders.OrdersApplication`. Its package is `com.example.orders`. All three project classes start with `com.example.orders.`, so all are discovered.
- **Scenario B** — the main class is at `com.example.orders.config.Application`. Its package is `com.example.orders.config`. None of the project classes are in that package or below it, so zero beans are discovered. The application starts but no controllers, services, or repositories are registered — a confusing but common bug.
- **Fix options** — moving the main class is the clean solution. Using `scanBasePackages` is valid but adds noise. Both correct the scan root.

## 7. Gotchas & takeaways

> **Multiple `main` methods cause plugin detection failures.** If your project has test classes or utility classes with `main` methods, the Maven/Gradle Spring Boot plugin may fail to detect which one is the application entry point. Resolve by specifying `<mainClass>` in the plugin configuration, or by ensuring only the `*Application.java` class has a `main` method.

> **`@SpringBootApplication` does not have to be on the main-method class.** While it almost always is, you can split them: have one class with `@SpringBootApplication` (setting the scan root) and another with the `main` method that calls `SpringApplication.run(AnnotatedClass.class, args)`. This is unusual but valid — useful for test scenarios where you want a different component scan root.

- Main class at the root package: discovered by the plugin, correct scan scope — always the right choice.
- Naming convention: `{AppName}Application` in package `com.{company}.{app}`.
- `@SpringBootApplication(scanBasePackages = {"..."})` overrides the default scan if the main class must live somewhere non-ideal.
- Only one class with `main` in the project keeps plugin auto-detection reliable.
- The Initializr always generates the main class in the correct location — trust it.
