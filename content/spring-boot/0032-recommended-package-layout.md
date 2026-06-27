---
card: spring-boot
gi: 32
slug: recommended-package-layout
title: Recommended package layout
---

## 1. What it is

**Recommended package layout** is the conventional way Spring Boot projects organise their Java source files into directories (packages). Instead of grouping by layer across the whole app (all controllers together, all services together), Spring Boot documentation recommends a **feature-first or domain-first layout** — all the code for one concept lives in one place.

The standard baseline looks like:

```
com.example.myapp
├── MyAppApplication.java        ← main class at the root
├── customer/
│   ├── CustomerController.java
│   ├── CustomerService.java
│   └── Customer.java
└── order/
    ├── OrderController.java
    ├── OrderService.java
    └── Order.java
```

The main application class sits at the **root** of the base package, with feature sub-packages beneath it.

## 2. Why & when

Spring Boot's component scan starts from the package of `@SpringBootApplication` and scans **downward**. If your classes live in sibling or parent packages, Spring won't find them and your beans won't be registered.

This convention matters because:

- **Scan just works** — no need to declare scan paths; everything is under the root package.
- **Cohesion** — all code for a feature is in one folder; easy to delete or move a feature.
- **Avoids the default package** — the default package (no package declaration) is scanned too broadly and can cause classloading collisions.

Use this layout from day one. Retrofitting package structure in a large project is painful.

## 3. Core concept

Think of it like a filing cabinet. A **layer-first** cabinet has drawers labelled "Controllers", "Services", "Repositories" — every customer file, order file, and product file gets split across drawers. A **feature-first** cabinet has drawers labelled "Customer", "Order", "Product" — everything about orders is in one drawer.

Spring Boot prefers feature-first because:

1. `@SpringBootApplication` on the root class enables `@ComponentScan` on that **package and all sub-packages**.
2. Classes annotated with `@Component`, `@Service`, `@Controller`, `@Repository`, etc. are discovered automatically by that scan.
3. Any class **outside** the root package must be explicitly registered — this breaks the "convention over configuration" promise.

Two rules worth memorising:
- **Root package** = the package containing `@SpringBootApplication`.
- **Sub-packages** = everything else; Spring auto-scans them.

## 4. Diagram

<svg viewBox="0 0 660 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot recommended package layout showing root package with feature sub-packages">
  <!-- Root package box -->
  <rect x="20" y="20" width="620" height="240" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="40" y="46" fill="#6db33f" font-size="13" font-family="monospace" font-weight="bold">com.example.myapp  (root — @SpringBootApplication lives here)</text>

  <!-- Main class -->
  <rect x="40" y="56" width="240" height="34" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="56" y="78" fill="#e6edf3" font-size="12" font-family="monospace">MyAppApplication.java</text>

  <!-- customer sub-package -->
  <rect x="40" y="106" width="240" height="130" rx="6" fill="#1a2332" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="56" y="124" fill="#79c0ff" font-size="12" font-family="monospace">customer/</text>
  <text x="72" y="148" fill="#8b949e" font-size="11" font-family="monospace">CustomerController.java</text>
  <text x="72" y="168" fill="#8b949e" font-size="11" font-family="monospace">CustomerService.java</text>
  <text x="72" y="188" fill="#8b949e" font-size="11" font-family="monospace">CustomerRepository.java</text>
  <text x="72" y="208" fill="#8b949e" font-size="11" font-family="monospace">Customer.java</text>

  <!-- order sub-package -->
  <rect x="310" y="106" width="240" height="130" rx="6" fill="#1a2332" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="326" y="124" fill="#79c0ff" font-size="12" font-family="monospace">order/</text>
  <text x="342" y="148" fill="#8b949e" font-size="11" font-family="monospace">OrderController.java</text>
  <text x="342" y="168" fill="#8b949e" font-size="11" font-family="monospace">OrderService.java</text>
  <text x="342" y="188" fill="#8b949e" font-size="11" font-family="monospace">OrderRepository.java</text>
  <text x="342" y="208" fill="#8b949e" font-size="11" font-family="monospace">Order.java</text>

  <!-- scan arrow -->
  <text x="580" y="130" fill="#6db33f" font-size="11" font-family="sans-serif" text-anchor="middle">auto-</text>
  <text x="580" y="146" fill="#6db33f" font-size="11" font-family="sans-serif" text-anchor="middle">scanned</text>
  <text x="580" y="162" fill="#6db33f" font-size="22" font-family="sans-serif" text-anchor="middle">↓</text>
</svg>

`@SpringBootApplication` on the root class triggers a scan of all sub-packages automatically; no extra configuration needed.

## 5. Runnable example

```java
// PackageLayoutDemo.java
// How to run: java PackageLayoutDemo.java  (JDK 17+)
// Simulates how Spring Boot discovers beans by checking package hierarchy.

public class PackageLayoutDemo {

    // Simulated annotation constants
    static final String ROOT_PKG    = "com.example.myapp";
    static final String CUSTOMER_PKG= "com.example.myapp.customer";
    static final String ORDER_PKG   = "com.example.myapp.order";
    static final String OUTSIDE_PKG = "com.example.other";      // NOT under root

    public static void main(String[] args) {
        System.out.println("=== Spring Boot Package Layout Demo ===\n");

        String[] packages = {ROOT_PKG, CUSTOMER_PKG, ORDER_PKG, OUTSIDE_PKG};
        String[] classNames = {
            "MyAppApplication",
            "CustomerController",
            "OrderService",
            "ThirdPartyUtil"
        };

        System.out.println("Root scan base: " + ROOT_PKG);
        System.out.println("--------------------------------------------");

        for (int i = 0; i < packages.length; i++) {
            boolean discovered = packages[i].startsWith(ROOT_PKG);
            System.out.printf("%-40s → %s%n",
                packages[i] + "." + classNames[i],
                discovered ? "✅ discovered by @ComponentScan"
                           : "❌ NOT found — outside root package");
        }

        System.out.println();
        System.out.println("Tip: keep @SpringBootApplication in the ROOT package,");
        System.out.println("     not in a sub-package, or beans in sibling packages are missed.");
    }
}
```

**How to run:** `java PackageLayoutDemo.java`

Expected output:
```
=== Spring Boot Package Layout Demo ===

Root scan base: com.example.myapp
--------------------------------------------
com.example.myapp.MyAppApplication          → ✅ discovered by @ComponentScan
com.example.myapp.customer.CustomerController → ✅ discovered by @ComponentScan
com.example.myapp.order.OrderService         → ✅ discovered by @ComponentScan
com.example.other.ThirdPartyUtil             → ❌ NOT found — outside root package
```

## 6. Walkthrough

- `ROOT_PKG` represents where `@SpringBootApplication` lives. Spring uses this as the scan base.
- `packages[i].startsWith(ROOT_PKG)` simulates the real Spring scan rule: a class is eligible if its package starts with the root package string.
- `CUSTOMER_PKG` and `ORDER_PKG` both start with `com.example.myapp`, so they are found.
- `OUTSIDE_PKG = "com.example.other"` does **not** start with the root package — Spring ignores it unless you add an explicit `@ComponentScan(basePackages = ...)`.
- The tip at the end captures the single most common mistake: putting `@SpringBootApplication` inside a sub-package (e.g. `com.example.myapp.config`) which then misses beans in sibling packages.

## 7. Gotchas & takeaways

> Putting `@SpringBootApplication` in a sub-package instead of the root is the most common layout mistake. Classes in sibling packages silently fail to register as beans, giving cryptic `NoSuchBeanDefinitionException` errors at runtime.

> Avoid the **default package** (no `package` declaration). Spring scans it too eagerly and it can pull in classes from every JAR on the classpath, causing unpredictable collisions.

- Root package = the package of `@SpringBootApplication`; everything must be **under** it.
- Feature-first sub-packages (customer/, order/) keep related code together and are easier to refactor.
- Layer-first layouts (controllers/, services/) work but scatter a feature's files across directories.
- If you must scan an external package, add `@ComponentScan(basePackages = {"com.example.myapp", "com.other"})`.
- Keep `@SpringBootApplication` on a class named `*Application` in the root package — IDEs and tools expect this convention.
