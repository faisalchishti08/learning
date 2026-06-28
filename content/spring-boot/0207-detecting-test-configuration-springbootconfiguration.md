---
card: spring-boot
gi: 207
slug: detecting-test-configuration-springbootconfiguration
title: Detecting test configuration (@SpringBootConfiguration)
---

## 1. What it is

When you annotate a test with `@SpringBootTest`, Spring Boot needs to find the **root configuration class** to load the application context. It does this by scanning upward through the test's package hierarchy looking for a class annotated with `@SpringBootApplication` (which is meta-annotated with `@SpringBootConfiguration`). This is called **test configuration detection**, and it means tests automatically use your application's real configuration without any explicit `classes` attribute.

## 2. Why & when

Understanding configuration detection matters when:
- Your test package structure differs from your main source packages.
- You have multiple `@SpringBootApplication` classes (unusual but possible in modular projects).
- A test is failing to load with "Unable to find a @SpringBootConfiguration" — the detection failed.
- You want to use a custom test configuration class instead of the main application class.

When the scan works, you never need to specify `@SpringBootTest(classes = MyApp.class)` — Spring Boot finds it automatically.

## 3. Core concept

**Detection algorithm:** Spring Boot walks up from the test class's package, looking for a class with `@SpringBootConfiguration` (directly or via meta-annotation like `@SpringBootApplication`):

```
com.example.order.service.OrderServiceTest
 → scan com.example.order.service → not found
 → scan com.example.order → not found
 → scan com.example → found: com.example.Application (@SpringBootApplication)
```

**Standard project layout (works automatically):**
```
src/main/java/com/example/Application.java    ← @SpringBootApplication
src/test/java/com/example/order/OrderTest.java ← @SpringBootTest (auto-detects Application)
```

**Problem case (test in different package root):**
```
src/main/java/com/example/Application.java
src/test/java/org/myteam/order/OrderTest.java  ← scan fails — can't reach com.example
```
Fix: `@SpringBootTest(classes = Application.class)`.

**Explicit configuration:**
```java
@SpringBootTest(classes = {Application.class, TestConfig.class})
class OrderIT { ... }
```

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@SpringBootTest scans upward from test package through parent packages until it finds a class annotated with @SpringBootConfiguration">
  <!-- Test class -->
  <rect x="10" y="155" width="230" height="38" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="125" y="172" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">com.example.order.service</text>
  <text x="125" y="186" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">OrderServiceTest.java (@SpringBootTest)</text>

  <!-- Arrow up -->
  <line x1="125" y1="153" x2="125" y2="125" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#dca)"/>
  <text x="140" y="143" fill="#8b949e" font-size="8" font-family="sans-serif">scan ↑ not found</text>

  <rect x="10" y="88" width="230" height="32" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="125" y="102" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">com.example.order</text>
  <text x="125" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(no @SpringBootConfiguration)</text>

  <line x1="125" y1="86" x2="125" y2="58" stroke="#6db33f" stroke-width="1.5" stroke-dasharray="4,2" marker-end="url(#dca)"/>
  <text x="140" y="75" fill="#8b949e" font-size="8" font-family="sans-serif">scan ↑ not found</text>

  <!-- Found -->
  <rect x="10" y="20" width="230" height="36" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="125" y="37" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">com.example</text>
  <text x="125" y="50" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Application.java @SpringBootApplication ✓ FOUND</text>

  <!-- Context load -->
  <line x1="242" y1="38" x2="320" y2="38" stroke="#6db33f" stroke-width="2" marker-end="url(#dcb)"/>
  <rect x="325" y="20" width="340" height="160" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="44" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">ApplicationContext loaded</text>
  <text x="495" y="62" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">all beans from Application.java</text>
  <text x="495" y="80" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ @ComponentScan result</text>
  <text x="495" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ AutoConfigurations</text>
  <text x="495" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ application.properties</text>
  <text x="495" y="132" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">If detection fails:</text>
  <text x="495" y="148" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">@SpringBootTest(classes=Application.class)</text>
  <text x="495" y="164" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">or put test in same pkg hierarchy</text>

  <defs>
    <marker id="dca" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="dcb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Spring Boot walks up the package tree from the test class until it finds `@SpringBootConfiguration`; tests must be within the same package hierarchy as the main application.

## 5. Runnable example

```java
// SpringBootConfigurationDetectionDemo.java — simulates package scanning for @SpringBootConfiguration
// How to run: java SpringBootConfigurationDetectionDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: scan is automatic when test is under the @SpringBootApplication package

import java.util.*;

public class SpringBootConfigurationDetectionDemo {

    // Represents a class in the package tree
    record ClassInfo(String packageName, String className, boolean hasSpringBootConfiguration) {}

    // Simulates Spring Boot's upward package scan
    static Optional<ClassInfo> detectConfiguration(String testPackage, List<ClassInfo> allClasses) {
        String pkg = testPackage;
        while (!pkg.isEmpty()) {
            final String currentPkg = pkg;
            Optional<ClassInfo> found = allClasses.stream()
                .filter(c -> c.packageName().equals(currentPkg))
                .filter(ClassInfo::hasSpringBootConfiguration)
                .findFirst();
            if (found.isPresent()) return found;

            // Walk up: com.example.order → com.example → com → ""
            int lastDot = pkg.lastIndexOf('.');
            pkg = lastDot > 0 ? pkg.substring(0, lastDot) : "";
        }
        return Optional.empty();
    }

    static void simulateScan(String testClass, String testPkg, List<ClassInfo> classes) {
        System.out.println("\nTest: " + testClass);
        System.out.println("Package: " + testPkg);
        System.out.println("Scanning upward...");

        String pkg = testPkg;
        while (!pkg.isEmpty()) {
            boolean found = classes.stream()
                .anyMatch(c -> c.packageName().equals(pkg) && c.hasSpringBootConfiguration());
            System.out.printf("  %s %-45s %s%n",
                found ? "✓" : "→", pkg,
                found ? "FOUND @SpringBootConfiguration" : "(scanning parent...)");
            if (found) break;
            int dot = pkg.lastIndexOf('.');
            pkg = dot > 0 ? pkg.substring(0, dot) : "";
            if (pkg.isEmpty()) {
                System.out.println("  ✗ NOT FOUND — detection failed!");
            }
        }
    }

    public static void main(String[] args) {
        System.out.println("=== @SpringBootConfiguration Detection Demo ===\n");

        // Typical Spring Boot project layout
        List<ClassInfo> projectClasses = List.of(
            new ClassInfo("com.example", "Application", true),         // @SpringBootApplication
            new ClassInfo("com.example.order", "OrderService", false),
            new ClassInfo("com.example.order.service", "OrderRepository", false),
            new ClassInfo("com.example.payment", "PaymentService", false)
        );

        // Case 1: test in sub-package — works
        System.out.println("=== Case 1: Test in sub-package (normal case) ===");
        simulateScan("OrderServiceTest", "com.example.order.service", projectClasses);

        // Case 2: test at root package — works
        System.out.println("\n=== Case 2: Test at root package ===");
        simulateScan("ApplicationTest", "com.example", projectClasses);

        // Case 3: test in wrong package root — fails
        System.out.println("\n=== Case 3: Test in different root package (problem!) ===");
        simulateScan("OrderServiceTest", "org.myteam.order", projectClasses);
        System.out.println("  Fix: @SpringBootTest(classes = Application.class)");

        // Fix demonstration: explicit classes attribute
        System.out.println("\n=== Fix: explicit classes attribute ===");
        System.out.println("@SpringBootTest(classes = {Application.class, TestDatabaseConfig.class})");
        System.out.println("  → bypasses package scan");
        System.out.println("  → loads Application + TestDatabaseConfig");

        // Case 4: multiple @SpringBootApplication classes (unusual)
        System.out.println("\n=== Case 4: Ambiguous — multiple @SpringBootConfiguration ===");
        List<ClassInfo> ambiguous = List.of(
            new ClassInfo("com.example", "Application", true),
            new ClassInfo("com.example", "TestApplication", true)  // second one
        );
        // Detection finds the first alphabetically (actual Spring Boot picks first found — undefined order)
        System.out.println("  Two @SpringBootConfiguration in same package — ambiguous!");
        System.out.println("  Spring Boot may throw: 'Found multiple @SpringBootConfiguration classes'");
        System.out.println("  Fix: use @SpringBootTest(classes = Application.class) to be explicit");

        // Summary
        System.out.println("\n--- Detection rules ---");
        System.out.println("1. Test class must be in same package tree as @SpringBootApplication");
        System.out.println("2. Scan goes UP the package hierarchy only (never sideways)");
        System.out.println("3. @SpringBootApplication is meta-annotated with @SpringBootConfiguration");
        System.out.println("4. Explicit: @SpringBootTest(classes=App.class) bypasses scan");
        System.out.println("5. Only one @SpringBootConfiguration allowed per scan (or use explicit)");
    }
}
```

**How to run:** `java SpringBootConfigurationDetectionDemo.java`

## 6. Walkthrough

- **Case 1 (normal)**: `com.example.order.service` → `com.example.order` → `com.example` (found `Application.java`). This is the standard layout and works with zero configuration.
- **Case 2 (root package)**: test is at `com.example` — found immediately. Fine for small projects where all tests live at the application package level.
- **Case 3 (wrong root)**: `org.myteam.order` → `org.myteam` → `org` → `` (empty, failed). The test's package hierarchy never crosses `com.example`, so the scan fails. The error is `IllegalStateException: Unable to find a @SpringBootConfiguration`.
- **Case 4 (ambiguous)**: two `@SpringBootConfiguration` classes in the same package — Spring Boot throws an error unless you use explicit `classes`. This is rare but can happen in test-specific main configurations.
- The "detection rules" summary is the practical reference for troubleshooting.

## 7. Gotchas & takeaways

> The most common "Unable to find a @SpringBootConfiguration" error occurs when test classes are placed in a **different root package** than the main application, or when the test module has no `@SpringBootApplication` in its `src/main/java` at all. Fix by either moving tests or using `classes = MyApp.class`.

> `@SpringBootTest` only finds **one** `@SpringBootConfiguration`. If you have a test utility module that declares its own `@SpringBootApplication`, tests in that module will load the wrong context. Use `@SpringBootTest(classes = RealApp.class)` explicitly.

- `@SpringBootConfiguration` is the bare-bones version of `@SpringBootApplication` without `@EnableAutoConfiguration` — useful when you need component scanning but not auto-configuration.
- In multi-module Maven/Gradle projects, each module that runs `@SpringBootTest` must have a class reachable by upward scan.
- The `@ContextConfiguration` Spring Test annotation still works and predates `@SpringBootTest` — but `@SpringBootTest` is preferred for Spring Boot apps.
- Check detected configuration: set `logging.level.org.springframework.boot.test=DEBUG` to see which class was found.
