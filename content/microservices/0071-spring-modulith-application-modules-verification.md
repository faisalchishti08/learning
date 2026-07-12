---
card: microservices
gi: 71
slug: spring-modulith-application-modules-verification
title: "Spring Modulith application modules & verification"
---

## 1. What it is

`ApplicationModules` is Spring Modulith's API for detecting and describing a Spring Boot application's module structure by scanning its packages, and `ApplicationModules.of(Application.class).verify()` is the call that runs its structural checks — the same checks conceptually shown in [Spring Modulith for modular monoliths as a stepping stone](0070-spring-modulith-for-modular-monoliths-as-a-stepping-stone.md) — and throws an exception (in a test, failing the build) if any module violates its boundary rules. This tutorial goes one level deeper: how the module model is actually detected from package structure, and how `verify()` is typically wired into a test so violations are caught automatically, on every build, rather than relying on manual review.

## 2. Why & when

Documentation describing intended module boundaries drifts from reality the moment nobody is watching — a deadline-pressed developer adds one import that reaches into another module's internal package, the code compiles fine, and the violation ships. `ApplicationModules.verify()` closes that gap by making the boundary check part of the automated test suite: a single JUnit test, run on every build, that fails loudly the moment any module boundary is crossed. Use it in any Spring Boot project structured as a modular monolith, from the very first commit that introduces more than one top-level module package — retrofitting boundary discipline onto a codebase that has already accumulated years of undetected violations is a much larger undertaking.

## 3. Core concept

`ApplicationModules.of(...)` scans the classpath once, builds a model of every top-level package under the main application class as a module, and `.verify()` runs a fixed set of structural rules against that model — no manual configuration needed for the common case.

```
@SpringBootApplication
class ShopApplication { }

// in a test:
ApplicationModules modules = ApplicationModules.of(ShopApplication.class);
modules.verify();   // throws if any module boundary is violated
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ApplicationModules scans the package tree under the main application class, builds a module model, and verify checks it against structural rules, throwing on violation">
  <rect x="20" y="20" width="150" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Package tree</text>
  <text x="95" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">orders/, shipping/...</text>

  <rect x="220" y="20" width="180" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">ApplicationModules.of(...)</text>
  <text x="310" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">builds the module model</text>

  <rect x="450" y="20" width="150" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="525" y="42" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">.verify()</text>
  <text x="525" y="58" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">runs structural rules</text>

  <line x1="170" y1="45" x2="220" y2="45" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="400" y1="45" x2="450" y2="45" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="220" y="120" width="200" height="60" rx="5" fill="#1c2430" stroke="#e6edf3" stroke-width="1.2"/>
  <text x="320" y="145" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">violation found</text>
  <text x="320" y="163" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">throws Violations exception -&gt; test fails</text>
  <line x1="525" y1="70" x2="320" y2="120" stroke="#79c0ff" stroke-width="1.5" stroke-dasharray="4,3"/>
</svg>

The scan builds a model once; verify checks it against fixed rules and throws on the first build where a violation exists.

## 5. Runnable example

Scenario: build a simplified stand-in for `ApplicationModules` that scans a declared package structure to detect modules automatically, first with basic scanning, then wired into a JUnit-style test method that fails on a violation, then extended to report *every* violation found (not just the first), matching how a real verification report lists all problems at once.

### Level 1 — Basic

```java
// File: ScanModules.java -- simulate scanning a package tree to detect
// modules: any package directly under the application's root package
// becomes one module. This is what ApplicationModules.of(...) does for real.
import java.util.*;

public class ScanModules {
    record ClassInfo(String fullyQualifiedPackage, String simpleName) {}

    static Set<String> detectModules(String rootPackage, List<ClassInfo> classes) {
        Set<String> modules = new TreeSet<>();
        for (ClassInfo c : classes) {
            String remainder = c.fullyQualifiedPackage().substring(rootPackage.length() + 1);
            String moduleName = remainder.split("\\.")[0]; // first segment under the root = module name
            modules.add(moduleName);
        }
        return modules;
    }

    public static void main(String[] args) {
        String root = "com.example.shop";
        List<ClassInfo> classes = List.of(
            new ClassInfo("com.example.shop.orders", "OrderService"),
            new ClassInfo("com.example.shop.orders.internal", "OrderRepository"),
            new ClassInfo("com.example.shop.shipping", "ShippingService")
        );
        System.out.println("Detected modules: " + detectModules(root, classes));
    }
}
```

**How to run:** `javac ScanModules.java && java ScanModules` (JDK 17+).

Expected output:
```
Detected modules: [orders, shipping]
```

`com.example.shop.orders.internal` still counts as the `orders` module — only the *first* segment after the root package names the module, matching how the real library treats nested packages as still belonging to their parent module.

### Level 2 — Intermediate

```java
// File: VerifyAsTest.java -- wire the (simulated) module model and
// verification into something shaped like a JUnit test: verify() throws
// on the first violation, and the "test" fails with that exception.
import java.util.*;

public class VerifyAsTest {
    enum Visibility { PUBLIC, INTERNAL }
    record ModuleClass(String module, String className, Visibility visibility) {}
    record Dependency(String fromClass, String toClass) {}

    static class Violations extends RuntimeException {
        Violations(String message) { super(message); }
    }

    static void verify(List<ModuleClass> classes, List<Dependency> dependencies) {
        Map<String, ModuleClass> byName = new HashMap<>();
        for (ModuleClass c : classes) byName.put(c.className(), c);
        for (Dependency d : dependencies) {
            ModuleClass from = byName.get(d.fromClass());
            ModuleClass to = byName.get(d.toClass());
            if (!from.module().equals(to.module()) && to.visibility() == Visibility.INTERNAL) {
                throw new Violations(from.className() + " must not depend on internal type " + to.className());
            }
        }
    }

    // shaped like a JUnit @Test method
    static void verifiesModuleStructure() {
        List<ModuleClass> classes = List.of(
            new ModuleClass("orders", "OrderService", Visibility.PUBLIC),
            new ModuleClass("orders", "OrderRepository", Visibility.INTERNAL),
            new ModuleClass("shipping", "ShippingService", Visibility.PUBLIC)
        );
        List<Dependency> deps = List.of(new Dependency("ShippingService", "OrderRepository"));
        verify(classes, deps); // would be: ApplicationModules.of(ShopApplication.class).verify();
    }

    public static void main(String[] args) {
        try {
            verifiesModuleStructure();
            System.out.println("TEST PASSED");
        } catch (Violations v) {
            System.out.println("TEST FAILED: " + v.getMessage());
        }
    }
}
```

**How to run:** `javac VerifyAsTest.java && java VerifyAsTest` (JDK 17+).

Expected output:
```
TEST FAILED: ShippingService must not depend on internal type OrderRepository
```

### Level 3 — Advanced

```java
// File: ReportAllViolations.java -- a real verification report lists
// EVERY violation found, not just the first -- so a developer can fix
// them all at once instead of hitting them one at a time across
// multiple build attempts.
import java.util.*;

public class ReportAllViolations {
    enum Visibility { PUBLIC, INTERNAL }
    record ModuleClass(String module, String className, Visibility visibility) {}
    record Dependency(String fromClass, String toClass) {}

    static class Violations extends RuntimeException {
        List<String> messages;
        Violations(List<String> messages) {
            super(messages.size() + " module violation(s) found");
            this.messages = messages;
        }
    }

    static void verify(List<ModuleClass> classes, List<Dependency> dependencies) {
        Map<String, ModuleClass> byName = new HashMap<>();
        for (ModuleClass c : classes) byName.put(c.className(), c);

        List<String> messages = new ArrayList<>();
        for (Dependency d : dependencies) {
            ModuleClass from = byName.get(d.fromClass());
            ModuleClass to = byName.get(d.toClass());
            if (!from.module().equals(to.module()) && to.visibility() == Visibility.INTERNAL) {
                messages.add(from.className() + " -> " + to.className() + " (internal to " + to.module() + ")");
            }
        }
        if (!messages.isEmpty()) throw new Violations(messages);
    }

    static void verifiesModuleStructure() {
        List<ModuleClass> classes = List.of(
            new ModuleClass("orders", "OrderService", Visibility.PUBLIC),
            new ModuleClass("orders", "OrderRepository", Visibility.INTERNAL),
            new ModuleClass("shipping", "ShippingService", Visibility.PUBLIC),
            new ModuleClass("shipping", "ShipmentRepository", Visibility.INTERNAL),
            new ModuleClass("billing", "BillingService", Visibility.PUBLIC)
        );
        List<Dependency> deps = List.of(
            new Dependency("ShippingService", "OrderRepository"),   // violation 1
            new Dependency("BillingService", "ShipmentRepository"), // violation 2
            new Dependency("BillingService", "OrderService")        // fine: OrderService is PUBLIC
        );
        verify(classes, deps);
    }

    public static void main(String[] args) {
        try {
            verifiesModuleStructure();
            System.out.println("TEST PASSED");
        } catch (Violations v) {
            System.out.println("TEST FAILED: " + v.getMessage());
            for (String m : v.messages) System.out.println("  - " + m);
        }
    }
}
```

**How to run:** `javac ReportAllViolations.java && java ReportAllViolations` (JDK 17+).

Expected output:
```
TEST FAILED: 2 module violation(s) found
  - ShippingService -> OrderRepository (internal to orders)
  - BillingService -> ShipmentRepository (internal to shipping)
```

## 6. Walkthrough

1. **Level 1** — `detectModules` strips the shared `rootPackage` prefix off each class's package and takes the first remaining path segment as its module name. Running it against three sample classes correctly detects two modules, `orders` and `shipping`, and confirms that `com.example.shop.orders.internal.OrderRepository` is still grouped under `orders`, not treated as its own module — matching how `ApplicationModules.of(...)` interprets nested packages in a real Spring Boot app.
2. **Level 2 — verification as a test** — `verifiesModuleStructure` is written to look like a JUnit test method (a real Spring Modulith test would call `ApplicationModules.of(ShopApplication.class).verify()` at this exact point, marked `@Test`). It calls `verify`, which throws `Violations` the instant it finds `ShippingService` depending on the `INTERNAL` `OrderRepository`. `main` wraps the call in try/catch to simulate a test runner: `verifiesModuleStructure()` throws, the catch block prints `TEST FAILED` with the violation message — in a real CI pipeline, this is exactly the signal that fails the build.
3. **Level 3 — collecting every violation before failing** — instead of throwing on the *first* bad dependency found, `verify` now accumulates every violation into a `messages` list while it walks all dependencies, and only throws (with the full list attached) after the loop completes. `verifiesModuleStructure`'s dependency list has three entries: `ShippingService -> OrderRepository` (violation, `OrderRepository` is internal to a different module), `BillingService -> ShipmentRepository` (violation, same reasoning), and `BillingService -> OrderService` (fine — `OrderService` is `PUBLIC`, so a cross-module dependency on it is exactly the intended way to use another module).
4. **Tracing the output** — `main` catches the thrown `Violations`, prints its summary message (`"2 module violation(s) found"`), then iterates `v.messages` and prints each one indented. The third dependency, on the public `OrderService`, never appears in the output at all — it was checked, found to be legitimate, and silently allowed, exactly as intended: `verify()`'s job is to catch *illegitimate* cross-module access, not to prevent all cross-module communication.
5. **Why report-all matters in practice** — if `verify` still threw on the first violation only, fixing `ShippingService -> OrderRepository`, rerunning, discovering `BillingService -> ShipmentRepository`, and rerunning again would cost a developer two separate build cycles for what is really one clean-up pass. Reporting every violation up front, as Level 3 does, lets a developer see and fix the whole picture in one pass — which is exactly how the real `ApplicationModules.verify()`'s exception message is formatted.

## 7. Gotchas & takeaways

> **Gotcha:** `verify()` only catches structural boundary violations it can see from the package layout — it cannot catch a module quietly depending on another module's *behavior* through some indirect mechanism (a shared static field, reflection, or a database table both modules happen to read). Structural verification is necessary, but it is not a substitute for genuinely designing clean module APIs.

- `ApplicationModules.of(Application.class)` scans the package tree once and builds a module model automatically — no manual module registration needed for the standard case.
- `.verify()` should be wired into a test that runs on every build (a plain JUnit `@Test` calling it is the idiomatic way), so violations are caught the moment they're introduced, not discovered much later.
- A real verification failure reports every violation found in one pass, not just the first — design any similar checking logic in your own tooling the same way, to avoid multi-cycle fix loops.
- Dependencies on another module's `PUBLIC` API are the intended, encouraged form of cross-module communication — verification exists to block reaching into `internal` packages, not to eliminate inter-module collaboration entirely.
- See [Spring Modulith domain events between modules](0072-spring-modulith-domain-events-between-modules.md) for the preferred way to let modules react to each other's state changes without even a direct public-API call.
