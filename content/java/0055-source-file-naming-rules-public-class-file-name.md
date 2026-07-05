---
card: java
gi: 55
slug: source-file-naming-rules-public-class-file-name
title: Source file naming rules (public class = file name)
---

## 1. What it is

Java enforces a strict rule: **a source file's name must match the name of the public class it contains**. The file extension is always `.java`.

```java
// File MUST be named: PaymentService.java
public class PaymentService {   // public → file name must match
    ...
}
```

One file can contain multiple classes, but **at most one can be `public`** — and the file must be named after that public class. All other classes in the file are package-private (no modifier).

## 2. Why & when

The naming rule exists so:
- **`javac` can find source files on demand.** When class `A` references class `B`, the compiler looks for `B.java` in the source path without needing to scan all files. The file name IS the class name.
- **The JVM can locate `.class` files on the classpath.** `ClassLoader.loadClass("com.example.PaymentService")` looks for `PaymentService.class` in the `com/example/` directory — it never needs to scan.
- **One class per file is a convention** that makes large codebases navigable: you know exactly which file to open when you need a class.

Violations are compile errors — `javac` will refuse to compile a file whose name doesn't match its public class.

## 3. Core concept

```bash
# Rules:
# 1. File name = public class name (case-sensitive, including capitalisation)
# 2. Extension = .java
# 3. At most ONE public class per file
# 4. Multiple non-public (package-private) classes allowed in one file

# Good examples:
PaymentService.java       → contains: public class PaymentService
OrderRepository.java      → contains: public interface OrderRepository
UserEvent.java            → contains: public record UserEvent(String id) {}
HttpStatus.java           → contains: public enum HttpStatus { OK, NOT_FOUND }

# Multiple classes in one file (valid):
# File: OrderUtils.java
public class OrderUtils { }          # public — file name must match
class OrderValidator { }             # package-private — fine
class OrderFormatter { }             # package-private — fine

# Compile error:
# File: Foo.java contains: public class Bar { }
# → error: class Bar is public, should be declared in a file named Bar.java

# Inner classes (nested inside a class) don't affect the file name:
# File: PaymentService.java
public class PaymentService {
    public enum Status { PENDING, PAID }     // nested — OK, still in PaymentService.java
    public record PaymentResult(String id) { } // nested — OK
    private static class Helper { }          // nested — OK
}

# Single-file source programs (JDK 11+):
# java Hello.java → filename doesn't need to match for single-file launch
# But for javac, the rule still applies.
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Source file naming: file name must match public class name; multiple package-private classes allowed in one file">
  <rect x="8" y="8" width="684" height="179" rx="8" fill="#0d1117"/>

  <!-- Valid: single public class -->
  <rect x="20" y="20" width="195" height="150" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="117" y="38" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">PaymentService.java</text>
  <text x="30" y="57" fill="#6db33f" font-size="9" font-family="monospace">public class PaymentService</text>
  <text x="30" y="70" fill="#8b949e" font-size="8" font-family="monospace">{ ... }</text>
  <text x="117" y="98" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">✓ VALID: file name = public class</text>

  <!-- Valid: public + package-private -->
  <rect x="227" y="20" width="215" height="150" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="38" fill="#6db33f" font-size="9" text-anchor="middle" font-family="monospace">OrderUtils.java</text>
  <text x="240" y="57" fill="#6db33f" font-size="9" font-family="monospace">public class OrderUtils { }</text>
  <text x="240" y="72" fill="#8b949e" font-size="9" font-family="monospace">class OrderValidator { }</text>
  <text x="240" y="86" fill="#8b949e" font-size="9" font-family="monospace">class OrderFormatter { }</text>
  <text x="335" y="110" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">✓ VALID: one public + many pkg-private</text>
  <text x="335" y="123" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">Validator/Formatter not importable</text>
  <text x="335" y="136" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">from outside the package</text>

  <!-- Invalid: wrong file name -->
  <rect x="455" y="20" width="220" height="150" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="565" y="38" fill="#8b949e" font-size="9" text-anchor="middle" font-family="monospace">Foo.java</text>
  <text x="468" y="57" fill="#79c0ff" font-size="9" font-family="monospace">public class Bar { }</text>
  <text x="468" y="76" fill="#e6edf3" font-size="7" font-family="monospace">// Foo ≠ Bar</text>
  <rect x="458" y="95" width="208" height="50" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="562" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">error: class Bar is public,</text>
  <text x="562" y="125" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">should be declared in a file</text>
  <text x="562" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">named Bar.java</text>
  <text x="565" y="160" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">✗ COMPILE ERROR</text>
</svg>

One public class per file; the file name must match exactly (case-sensitive). Multiple package-private classes can share a file.

## 5. Runnable example

Scenario: an order processing system showing how file naming rules interact with class organisation — one public class per file, package-private helpers co-located, and nested types inside the public class.

### Level 1 — Basic

```java
// FileNamingBasic.java — demonstrates naming rules via reflection
public class FileNamingBasic {

    // These are nested classes (inside FileNamingBasic) — not affected by file naming rule
    static class NestedHelper {
        static String help() { return "I'm nested, file name doesn't concern me."; }
    }

    enum Status { PENDING, COMPLETE, FAILED }

    record Result(String id, Status status) {}

    public static void main(String[] args) {
        System.out.println("=== File naming rules demo ===\n");

        // Show own FQCN and simple name
        Class<?> cls = FileNamingBasic.class;
        System.out.println("FQCN:        " + cls.getName());
        System.out.println("Simple name: " + cls.getSimpleName());
        System.out.println("Package:     " + cls.getPackageName());

        System.out.println("\nNested types (don't affect file name):");
        for (Class<?> nested : cls.getDeclaredClasses()) {
            System.out.println("  " + nested.getSimpleName() + " → " + nested.getName());
        }

        // Demonstrate the rule
        System.out.println("\n[ File naming rules ]");
        System.out.println("  public class Foo { }  → must be in Foo.java");
        System.out.println("  public interface Bar  → must be in Bar.java");
        System.out.println("  public enum Status    → must be in Status.java");
        System.out.println("  public record Point   → must be in Point.java");
        System.out.println("  class Helper { }      → can be in any .java file (pkg-private)");

        System.out.println("\n[ This file: FileNamingBasic.java ]");
        System.out.println("  public class FileNamingBasic  ← MUST match file name");
        System.out.println("  static class NestedHelper     ← nested: file name irrelevant");
        System.out.println("  enum Status                   ← nested: file name irrelevant");
        System.out.println("  record Result                 ← nested: file name irrelevant");

        System.out.println("\nUsing nested types:");
        System.out.println("  " + NestedHelper.help());
        Result r = new Result("ORD-001", Status.COMPLETE);
        System.out.println("  " + r);
    }
}
```

**How to run:** `java FileNamingBasic.java`

Nested types (`NestedHelper`, `Status`, `Result`) live inside `FileNamingBasic` and inherit its file. Their FQCNs use the `$` separator: `FileNamingBasic$NestedHelper`, `FileNamingBasic$Status`. The file naming rule only applies to top-level classes.

### Level 2 — Intermediate

Same order processing scenario: compile multiple classes (one public, two package-private) that share a single `.java` file — demonstrating what's accessible and what's hidden.

```java
// OrderUtils.java — one public class + two package-private classes in one file
// This file is named OrderUtils.java because OrderUtils is the public class.
// The other two classes (Validator, Formatter) cannot be imported from other packages.

// Package-private helper 1 (not accessible outside this package)
class OrderValidator {
    static void validate(String orderId, double amount) {
        if (orderId == null || orderId.isBlank())
            throw new IllegalArgumentException("orderId must not be blank");
        if (amount <= 0)
            throw new IllegalArgumentException("amount must be positive");
    }
}

// Package-private helper 2
class OrderFormatter {
    static String format(String orderId, String customer, double amount) {
        return String.format("Order[%s] for %s: £%.2f", orderId, customer, amount);
    }
}

// Public class — must match file name
public class OrderUtils {
    public static String processOrder(String orderId, String customer, double amount) {
        OrderValidator.validate(orderId, amount);    // same-file, same-package → visible
        return OrderFormatter.format(orderId, customer, amount);
    }

    public static void main(String[] args) {
        System.out.println("=== Multi-class single-file demo ===\n");

        try {
            System.out.println(processOrder("ORD-001", "Alice", 299.99));
            System.out.println(processOrder("ORD-002", "Bob",   150.00));

            // This will fail validation:
            processOrder("", "Carol", 100.00);
        } catch (IllegalArgumentException e) {
            System.out.println("Validation error: " + e.getMessage());
        }

        System.out.println("\n[ Class file output from javac OrderUtils.java ]");
        System.out.println("  OrderUtils.class       ← public class");
        System.out.println("  OrderValidator.class   ← package-private (separate .class file)");
        System.out.println("  OrderFormatter.class   ← package-private (separate .class file)");
        System.out.println("  Each class gets its own .class file, regardless of sharing a .java file");

        System.out.println("\n[ Access from other packages ]");
        System.out.println("  OrderUtils.processOrder(...)  ← OK (public)");
        System.out.println("  new OrderValidator()          ← COMPILE ERROR (package-private)");
        System.out.println("  new OrderFormatter()          ← COMPILE ERROR (package-private)");
    }
}
```

**How to run:** `java OrderUtils.java`

Each class in the file compiles to its own `.class` file: `OrderUtils.class`, `OrderValidator.class`, `OrderFormatter.class`. Even though `OrderValidator` and `OrderFormatter` share `OrderUtils.java`, they are independent classes at the bytecode level — just invisible to other packages.

### Level 3 — Advanced

Same order system grown to demonstrate the complete file naming contract in context: multiple files, cross-file imports, and how `ClassLoader.loadClass()` at runtime relies on the naming convention.

```java
// FileNamingAdvanced.java — inspect ClassLoader and file naming at runtime
import java.net.*;
import java.nio.file.*;
import java.lang.reflect.*;

public class FileNamingAdvanced {
    public static void main(String[] args) throws Exception {
        System.out.println("=== File naming + ClassLoader demo ===\n");

        // 1. Show how ClassLoader resolves names to file paths
        ClassLoader cl = FileNamingAdvanced.class.getClassLoader();
        System.out.println("ClassLoader: " + cl.getClass().getSimpleName());

        // For a class com.example.PaymentService, the ClassLoader looks for:
        //   <classpath>/com/example/PaymentService.class
        // The file NAME is derived directly from the CLASS NAME

        // 2. Show the resource path for standard JDK classes
        String[] classesToCheck = {
            "java.lang.String",
            "java.util.ArrayList",
            "java.util.stream.Collectors",
            "java.time.LocalDate",
        };
        System.out.println("Class → resource path (how ClassLoader finds .class files):");
        for (String fqcn : classesToCheck) {
            String resourcePath = fqcn.replace('.', '/') + ".class";
            System.out.printf("  %-35s → %s%n", fqcn, resourcePath);
        }

        // 3. Demonstrate with a runtime-compiled class
        System.out.println("\n[ Runtime compilation — naming matters ]");
        javax.tools.JavaCompiler compiler = javax.tools.ToolProvider.getSystemJavaCompiler();
        if (compiler != null) {
            Path tmp = Files.createTempDirectory("naming-demo");

            // Source: class name must match file name
            String source = "public class RuntimeWidget { public String hello() { return \"Hi!\"; } }";
            Path src = tmp.resolve("RuntimeWidget.java");  // file name = class name
            Files.writeString(src, source);

            int rc = compiler.run(null, null, null, src.toString());
            System.out.println("Compile: " + (rc == 0 ? "SUCCESS" : "FAIL"));

            if (rc == 0) {
                try (URLClassLoader loader = new URLClassLoader(new URL[]{tmp.toUri().toURL()})) {
                    Class<?> cls = loader.loadClass("RuntimeWidget");
                    // ClassLoader looked for RuntimeWidget.class (name convention!)
                    Object obj = cls.getDeclaredConstructor().newInstance();
                    Method m   = cls.getMethod("hello");
                    System.out.println("Result: " + m.invoke(obj));
                    System.out.println("ClassLoader found: " + cls.getName() + ".class");
                    System.out.println("  via: " + tmp.resolve("RuntimeWidget.class"));
                }
            }

            Files.walk(tmp).sorted(java.util.Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
            System.out.println("Cleaned up.");
        }

        // 4. Naming conventions summary
        System.out.println("\n[ Java naming convention cheat sheet ]");
        System.out.println("  Class    PascalCase    OrderService, HttpClient, ThreadPool");
        System.out.println("  File     <ClassName>.java  must match public class exactly");
        System.out.println("  Package  lowercase    com.example.orders, org.apache.commons");
        System.out.println("  Method   camelCase    processOrder(), getUserById()");
        System.out.println("  Field    camelCase    orderCount, maxRetries");
        System.out.println("  Constant UPPER_SNAKE  MAX_RETRIES, DEFAULT_TIMEOUT_MS");
        System.out.println("  Enum     PascalCase   HttpStatus, DayOfWeek");
        System.out.println("  Record   PascalCase   Point, Transaction, UserEvent");
    }
}
```

**How to run:** `java FileNamingAdvanced.java`

`ClassLoader.loadClass("RuntimeWidget")` constructs the path `RuntimeWidget.class` from the class name. This is why the source file must be named `RuntimeWidget.java` — `javac` outputs `RuntimeWidget.class` and the ClassLoader searches for exactly that filename.

## 6. Walkthrough

Execution trace in `FileNamingAdvanced.main`:

**ClassLoader resolution.** For `ClassLoader.loadClass("java.util.ArrayList")`, the JVM converts the class name to a resource path: `java/util/ArrayList.class`. It searches each classpath entry for that exact path. The naming convention ensures `ArrayList.class` is always found in the `java/util/` directory — no scanning required.

**Runtime compilation.** `Files.writeString(src, source)` writes `"public class RuntimeWidget { ... }"` to `tmp/RuntimeWidget.java`. The file name `RuntimeWidget.java` matches the public class name `RuntimeWidget`. `compiler.run(...)` compiles it to `tmp/RuntimeWidget.class`.

**URLClassLoader.loadClass("RuntimeWidget").** The ClassLoader appends `.class` to the class name: `RuntimeWidget.class`. It searches the URL `tmp/` → finds `tmp/RuntimeWidget.class` → loads it. If the file were named `Widget.class` (mismatch), `loadClass("RuntimeWidget")` would throw `ClassNotFoundException`.

**What happens with a wrong file name.** If you write `public class Bar { }` in `Foo.java` and run `javac Foo.java`, `javac` immediately emits: `Foo.java:1: error: class Bar is public, should be declared in a file named Bar.java`. This is checked before any bytecode is generated.

**Per-class .class files.** `OrderUtils.java` (from Level 2) produces three `.class` files: `OrderUtils.class`, `OrderValidator.class`, `OrderFormatter.class`. `javac` always produces one `.class` file per top-level class, regardless of source file grouping. Nested/inner classes produce `Outer$Inner.class`.

## 7. Gotchas & takeaways

> **Case sensitivity matters — especially on macOS and Linux.** On macOS (HFS+ default), `paymentservice.java` and `PaymentService.java` may refer to the same file on disk, but `javac` requires the case to match exactly. Linux (case-sensitive filesystem) would treat them as different files. Always name your file exactly as the class, including capitalisation.

> **A file can have multiple top-level classes if only one is `public`.** This is valid Java but discouraged: IDEs and humans expect one class per file. The only common exception is small helper classes tightly coupled to a single public class (e.g., a package-private `OrderValidator` helper inside `OrderUtils.java`).

- `public class Foo` → file must be `Foo.java` (case-sensitive, no exceptions).
- `public interface`, `public enum`, `public record`, `public @interface` → same rule.
- Package-private (no modifier) classes → can live in any `.java` file in the same package.
- Nested classes (`static class Inner`) → live inside the outer class's file; named `Outer$Inner.class`.
- One `.class` file per top-level class, even if they share a `.java` source file.
- The `single-file source` launch (`java Foo.java`) relaxes the javac rule but the class name still comes from the source, not the file name.
