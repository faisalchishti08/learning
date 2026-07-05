---
card: java
gi: 51
slug: packages-the-package-statement
title: Packages & the package statement
---

## 1. What it is

A **package** is a named group of related classes and interfaces — Java's namespace mechanism. The `package` statement at the top of a source file declares which package the class belongs to:

```java
package com.example.payments;    // must be the FIRST statement in the file

public class PaymentService { }  // FQCN: com.example.payments.PaymentService
```

A package has a **fully qualified class name (FQCN)**: `com.example.payments.PaymentService`. This name must be globally unique across all JARs on the classpath.

## 2. Why & when

Packages solve three problems:
1. **Name collisions** — two libraries can each have a class named `Logger` as long as they're in different packages (`org.slf4j.Logger` vs `java.util.logging.Logger`).
2. **Organisation** — packages group related classes together, mirroring the domain model (`com.bank.accounts`, `com.bank.payments`).
3. **Access control** — `package-private` (no modifier) members are visible only within the same package, enabling encapsulation at the package level.

Convention: use **reverse domain name** as the root (`com.yourcompany.project.module`). JDK classes use `java.*` and `javax.*`; third-party libraries use their domain.

## 3. Core concept

```java
// File: src/com/example/payments/PaymentService.java
package com.example.payments;   // FIRST statement; directory must match

import com.example.accounts.Account;  // import a class from another package

public class PaymentService {

    public void process(Account account, double amount) {
        // package-private helper (visible only within com.example.payments)
        Validator.validate(amount);
        // ...
    }
}

// File: src/com/example/payments/Validator.java
package com.example.payments;   // same package as PaymentService

class Validator {               // no 'public' = package-private
    static void validate(double amount) { ... }
}
```

Directory structure must mirror package:
```
src/
  com/
    example/
      payments/
        PaymentService.java     ← package com.example.payments;
        Validator.java
      accounts/
        Account.java            ← package com.example.accounts;
```

Compile and run:
```bash
# Compile with source root
javac -d out/ src/com/example/payments/PaymentService.java

# Run using FQCN
java -cp out/ com.example.payments.PaymentService
```

Unnamed (default) package — for small scripts only:
```java
// No package statement → class is in the "unnamed" package
// Cannot be imported from named packages
// Fine for single-file scripts, bad for libraries
public class Hello { }
```

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Package directory tree showing com.example.payments and com.example.accounts with their classes">
  <rect x="8" y="8" width="684" height="194" rx="8" fill="#0d1117"/>

  <!-- Directory tree on left -->
  <rect x="20" y="20" width="240" height="170" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="140" y="40" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Source directory</text>
  <text x="35"  y="58"  fill="#6db33f" font-size="9" font-family="monospace">src/</text>
  <text x="50"  y="72"  fill="#8b949e" font-size="9" font-family="monospace">com/</text>
  <text x="65"  y="86"  fill="#8b949e" font-size="9" font-family="monospace">example/</text>
  <text x="80"  y="100" fill="#79c0ff" font-size="9" font-family="monospace">payments/</text>
  <text x="95"  y="113" fill="#e6edf3" font-size="9" font-family="monospace">PaymentService.java</text>
  <text x="95"  y="126" fill="#e6edf3" font-size="9" font-family="monospace">Validator.java</text>
  <text x="80"  y="143" fill="#79c0ff" font-size="9" font-family="monospace">accounts/</text>
  <text x="95"  y="156" fill="#e6edf3" font-size="9" font-family="monospace">Account.java</text>
  <text x="80"  y="173" fill="#8b949e" font-size="9" font-family="monospace">util/</text>
  <text x="95"  y="186" fill="#8b949e" font-size="9" font-family="monospace">DateHelper.java</text>

  <!-- FQCNs on right -->
  <rect x="280" y="20" width="400" height="170" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="480" y="40" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Fully Qualified Class Names</text>

  <rect x="295" y="52"  width="370" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="295" y="58" fill="#8b949e" font-size="7" font-family="sans-serif">package com.example.payments;</text>
  <text x="295" y="74" fill="#6db33f" font-size="9" font-family="monospace">com.example.payments.PaymentService</text>

  <rect x="295" y="90"  width="370" height="30" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1"/>
  <text x="295" y="96" fill="#8b949e" font-size="7" font-family="sans-serif">package com.example.payments; (package-private)</text>
  <text x="295" y="112" fill="#8b949e" font-size="9" font-family="monospace">com.example.payments.Validator (no public)</text>

  <rect x="295" y="128" width="370" height="30" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="134" fill="#8b949e" font-size="7" font-family="sans-serif">package com.example.accounts;</text>
  <text x="295" y="150" fill="#6db33f" font-size="9" font-family="monospace">com.example.accounts.Account</text>

  <rect x="295" y="166" width="370" height="18" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="295" y="178" fill="#8b949e" font-size="8" font-family="monospace">com.example.util.DateHelper</text>
</svg>

Package names mirror the directory structure. `javac` uses the source root; `java` uses the classpath root. The FQCN uniquely identifies a class across all JARs.

## 5. Runnable example

Scenario: a payment processing system with an `accounts` package and a `payments` package — demonstrating package declarations, cross-package imports, and package-private access control.

### Level 1 — Basic

```java
// PackagesBasic.java — single file showing package concepts programmatically
public class PackagesBasic {
    public static void main(String[] args) {
        System.out.println("=== Package system demo ===\n");

        // Every class has a package (or the unnamed package)
        Class<?>[] classes = {
            String.class,
            java.util.List.class,
            java.util.logging.Logger.class,
            org.w3c.dom.Document.class,      // xml package (standard JDK)
            PackagesBasic.class,
        };

        for (Class<?> c : classes) {
            System.out.printf("FQCN:    %-45s%n", c.getName());
            System.out.printf("Package: %-45s%n", c.getPackageName());
            System.out.printf("Simple:  %-45s%n%n", c.getSimpleName());
        }

        System.out.println("[ Package naming conventions ]");
        System.out.println("  java.*        → JDK standard library");
        System.out.println("  javax.*       → JDK extension API");
        System.out.println("  org.w3c.*     → W3C XML standards");
        System.out.println("  com.example.* → your company/project");
        System.out.println("  (none)        → unnamed package (scripts only)");
    }
}
```

**How to run:** `java PackagesBasic.java`

`Class.getName()` returns the FQCN. `Class.getPackageName()` returns just the package. `Class.getSimpleName()` returns just the class name. Two classes with the same simple name can coexist if their packages differ — e.g., `java.util.logging.Logger` vs `org.slf4j.Logger`.

### Level 2 — Intermediate

Same payment system: create two packages in temp directories, compile, and run to observe cross-package access and package-private visibility.

```java
// PackageDemo.java — compile and run multi-package code at runtime
import javax.tools.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class PackageDemo {

    static final String ACCOUNT_SOURCE =
        "package com.example.accounts;\n" +
        "public class Account {\n" +
        "    private final String id;\n" +
        "    private double balance;\n" +
        "    public Account(String id, double balance) { this.id = id; this.balance = balance; }\n" +
        "    public String getId()        { return id; }\n" +
        "    public double getBalance()   { return balance; }\n" +
        "    public void credit(double a) { balance += a; }\n" +
        "    @Override public String toString() {\n" +
        "        return String.format(\"Account[%s, %.2f]\", id, balance); }\n" +
        "}\n";

    static final String VALIDATOR_SOURCE =
        "package com.example.payments;\n" +
        "// package-private: not accessible from other packages\n" +
        "class Validator {\n" +
        "    static void validate(double amount) {\n" +
        "        if (amount <= 0) throw new IllegalArgumentException(\"Amount must be positive: \" + amount);\n" +
        "        if (amount > 1_000_000) throw new IllegalArgumentException(\"Amount too large: \" + amount);\n" +
        "    }\n" +
        "}\n";

    static final String PAYMENT_SOURCE =
        "package com.example.payments;\n" +
        "import com.example.accounts.Account;\n" +
        "public class PaymentService {\n" +
        "    public String pay(Account from, Account to, double amount) {\n" +
        "        Validator.validate(amount);  // OK — same package\n" +
        "        from.credit(-amount);\n" +
        "        to.credit(amount);\n" +
        "        return String.format(\"Paid %.2f: %s → %s\", amount, from.getId(), to.getId());\n" +
        "    }\n" +
        "}\n";

    static final String MAIN_SOURCE =
        "import com.example.accounts.Account;\n" +
        "import com.example.payments.PaymentService;\n" +
        "// import com.example.payments.Validator;  // ERROR: package-private\n" +
        "public class Main {\n" +
        "    public static void main(String[] a) {\n" +
        "        Account alice = new Account(\"A001\", 1000.0);\n" +
        "        Account bob   = new Account(\"B001\", 500.0);\n" +
        "        PaymentService svc = new PaymentService();\n" +
        "        System.out.println(svc.pay(alice, bob, 250.0));\n" +
        "        System.out.println(alice);\n" +
        "        System.out.println(bob);\n" +
        "    }\n" +
        "}\n";

    public static void main(String[] args) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) { System.err.println("JDK required"); return; }

        Path work   = Files.createTempDirectory("pkg-demo");
        Path srcDir = Files.createDirectories(work.resolve("src"));
        Path outDir = Files.createDirectories(work.resolve("out"));

        // Write source files in the correct directory structure
        Path accDir = Files.createDirectories(srcDir.resolve("com/example/accounts"));
        Path payDir = Files.createDirectories(srcDir.resolve("com/example/payments"));

        Files.writeString(accDir.resolve("Account.java"),       ACCOUNT_SOURCE);
        Files.writeString(payDir.resolve("Validator.java"),     VALIDATOR_SOURCE);
        Files.writeString(payDir.resolve("PaymentService.java"),PAYMENT_SOURCE);
        Files.writeString(srcDir.resolve("Main.java"),          MAIN_SOURCE);
        System.out.println("=== Multi-package compilation ===\n");
        System.out.println("Source tree:");
        Files.walk(srcDir).filter(f -> f.toString().endsWith(".java"))
            .forEach(f -> System.out.println("  " + srcDir.relativize(f)));

        // Compile all sources at once
        List<String> compileArgs = new ArrayList<>(List.of("-d", outDir.toString()));
        Files.walk(srcDir).filter(f -> f.toString().endsWith(".java"))
            .forEach(f -> compileArgs.add(f.toString()));
        int rc = compiler.run(null, null, null, compileArgs.toArray(new String[0]));
        System.out.println("\nCompilation: " + (rc == 0 ? "SUCCESS" : "FAILED"));

        // Show class files
        System.out.println("\nGenerated class files:");
        Files.walk(outDir).filter(f -> f.toString().endsWith(".class"))
            .forEach(f -> System.out.println("  " + outDir.relativize(f)));

        // Run
        System.out.println("\nRunning Main:");
        Process p = new ProcessBuilder("java", "-cp", outDir.toString(), "Main")
            .redirectErrorStream(true).start();
        System.out.println(new String(p.getInputStream().readAllBytes()).indent(2));
        p.waitFor();

        Files.walk(work).sorted(Comparator.reverseOrder()).forEach(f -> f.toFile().delete());
        System.out.println("Cleaned up.");
    }
}
```

**How to run:** `java PackageDemo.java`

`Validator` is package-private — its class file is compiled but it's invisible to `Main`. Only `PaymentService` (in the same package) can use it. This is exactly why package-private exists: it hides implementation helpers from clients while keeping them accessible to collaborating classes.

### Level 3 — Advanced

Same system grown to use **sealed packages** (Java 17+ sealed classes) and demonstrate that package layout directly controls access, showing the full interplay between packages and access modifiers.

```java
// PackageAccessControl.java — access modifier matrix across packages
public class PackageAccessControl {

    // Simulate four access levels with inner classes
    public static class PublicMember {
        public    static String pub()       { return "public";         }
        protected static String prot()      { return "protected";      }
        /* pkg-priv */ static String pkg()  { return "package-private"; }
        private   static String priv()      { return "private";        }

        static void showAll() {
            System.out.println("Within same class: ALL accessible");
            System.out.println("  public:          " + pub());
            System.out.println("  protected:       " + prot());
            System.out.println("  package-private: " + pkg());
            System.out.println("  private:         " + priv());
        }
    }

    // Subclass in the SAME package
    static class SamePackageSub extends PublicMember {
        static void show() {
            System.out.println("\nSame-package subclass: public, protected, package-private accessible");
            System.out.println("  public:          " + pub());
            System.out.println("  protected:       " + prot());
            System.out.println("  package-private: " + pkg()); // OK — same package
            // priv() — compile error: private not accessible
        }
    }

    public static void main(String[] args) {
        System.out.println("=== Java access modifier matrix ===\n");

        System.out.println("Access modifier visibility:");
        System.out.printf("  %-20s %-12s %-12s %-12s %-12s%n",
            "Modifier", "Same class", "Same pkg", "Subclass", "Anywhere");
        System.out.printf("  %-20s %-12s %-12s %-12s %-12s%n",
            "--------", "----------", "--------", "--------", "-------");
        System.out.printf("  %-20s %-12s %-12s %-12s %-12s%n",
            "private",         "✓", "✗", "✗", "✗");
        System.out.printf("  %-20s %-12s %-12s %-12s %-12s%n",
            "(package-private)","✓", "✓", "✗*","✗");
        System.out.printf("  %-20s %-12s %-12s %-12s %-12s%n",
            "protected",       "✓", "✓", "✓", "✗");
        System.out.printf("  %-20s %-12s %-12s %-12s %-12s%n",
            "public",          "✓", "✓", "✓", "✓");
        System.out.println("  (* package-private IS visible to subclasses in the same package)");

        System.out.println();
        PublicMember.showAll();
        SamePackageSub.show();

        System.out.println("\n[ Package as encapsulation boundary ]");
        System.out.println("  com.example.payments:");
        System.out.println("    PaymentService (public)  ← API for clients");
        System.out.println("    Validator (pkg-private)  ← hidden from clients");
        System.out.println("    PaymentDao (pkg-private) ← hidden from clients");
        System.out.println();
        System.out.println("  Benefits:");
        System.out.println("    - Clients only see PaymentService");
        System.out.println("    - You can refactor Validator/PaymentDao freely");
        System.out.println("    - No leaking implementation details");

        System.out.println("\n[ Package naming — reverse domain convention ]");
        System.out.println("  com.google.guava.collect  (com.google owns google.com)");
        System.out.println("  org.apache.commons.lang3  (org.apache is Apache Software Foundation)");
        System.out.println("  io.spring.framework.*     (io.spring = spring.io reversed)");
        System.out.println("  com.yourcompany.product.module.submodule");
    }
}
```

**How to run:** `java PackageAccessControl.java`

The access modifier table summarises exactly which combinations are legal. Package-private is the **default** when you write no modifier — it's the "friend-package" access level, tighter than `protected` (which allows cross-package subclass access).

## 6. Walkthrough

Execution trace in `PackageDemo.main`:

**Source layout.** `Account.java` lives at `src/com/example/accounts/Account.java`. The directory path `com/example/accounts` mirrors the package `com.example.accounts`. This is a compiler convention: when you pass `-sourcepath src/` to `javac`, it looks for `com.example.accounts.Account` at `src/com/example/accounts/Account.java`.

**Compilation.** `javac -d out/ src/**/*.java` compiles all four source files. Output: `.class` files under `out/` in matching subdirectories. `Validator.class` goes to `out/com/example/payments/Validator.class`.

**Package-private enforcement.** If `Main.java` had tried `import com.example.payments.Validator`, `javac` would emit: `error: Validator is not public in com.example.payments; cannot be accessed from outside package`. The access check happens at **compile time** — not at runtime.

**Cross-package import in `PaymentService`.** `import com.example.accounts.Account` resolves `Account` to `com.example.accounts.Account`. At compile time, `javac` reads `Account.class` from the `-d out/` output (already compiled). At runtime, `ClassLoader.loadClass("com.example.accounts.Account")` finds it in `out/com/example/accounts/Account.class`.

**Running `Main`.** `java -cp out/ Main` — the unnamed class `Main` is in the default package. The JVM loads it, resolves `com.example.accounts.Account` and `com.example.payments.PaymentService` from `out/`. The call `svc.pay(alice, bob, 250.0)` goes to `PaymentService.pay` which internally calls `Validator.validate(250.0)` — legal because they share the `com.example.payments` package.

**State change trace:**
```
alice = Account[A001, 1000.00]
bob   = Account[B001,  500.00]
→ PaymentService.pay(alice, bob, 250.0)
  → Validator.validate(250.0)  OK
  → alice.credit(-250.0) → alice.balance = 750.00
  → bob.credit(250.0)   → bob.balance   = 750.00
  → returns "Paid 250.00: A001 → B001"
→ System.out.println: Account[A001, 750.00]
→ System.out.println: Account[B001, 750.00]
```

## 7. Gotchas & takeaways

> **The `package` statement must be the first non-comment line.** Even a blank line before `package` causes a compile error: `class is public, should be declared in a file named...` (or similar). Comments (`//` and `/* */`) are allowed before `package`.

> **Directory structure must match the package.** `package com.example.payments` in a file stored at `src/com/other/payments/PaymentService.java` causes a compile error: `class PaymentService is public, should be declared in a file named PaymentService.java`. Compilers enforce the directory/package correspondence.

- Unnamed package (no `package` statement) — valid for scripts and small demos; cannot be imported by named packages.
- One public class per file, and the filename must match the public class name.
- `getClass().getPackageName()` — reads a class's package at runtime.
- Package-private is the default (no modifier). It's stricter than `protected` — `protected` allows subclasses from other packages; package-private does not.
- `java.lang` is automatically imported in every Java file — `String`, `Integer`, `System`, etc. don't need explicit imports.
