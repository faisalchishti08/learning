---
card: java
gi: 432
slug: serviceloader-java-util-serviceloader
title: ServiceLoader (java.util.ServiceLoader)
---

## 1. What it is

`ServiceLoader<S>`, added in Java 6, discovers and loads implementations of an interface (a "service") at runtime, without the calling code ever needing to know the concrete implementation class names at compile time. It works by scanning the classpath for `META-INF/services/<fully-qualified-interface-name>` files — each a plain text file listing one implementation class name per line — and instantiating each one on demand via `ServiceLoader.load(SomeInterface.class)`. This is the exact mechanism that made JDBC 4.0's auto driver loading (covered earlier in this series) possible.

## 2. Why & when

Without `ServiceLoader`, a plugin-style architecture means the core application has to hardcode a reference to every possible implementation class — `new CreditCardProcessor()`, `new PayPalProcessor()` — which defeats the entire point of a plugin system: new implementations can't be added without modifying and recompiling the core application itself. `ServiceLoader` decouples this completely: the core application only knows about the *interface*; each implementation declares itself independently via a `META-INF/services` file, and can be added, removed, or swapped simply by changing what's on the classpath, with zero changes to the application's own code.

This is the standard mechanism behind JDBC drivers (as covered earlier), logging framework bindings (SLF4J-style provider discovery), and any plugin architecture where third parties need to contribute implementations without access to the core application's source code. You reach for it whenever your application needs to support pluggable implementations of some interface, discovered dynamically rather than hardcoded.

## 3. Core concept

```java
import java.util.ServiceLoader;

// The application only knows about the interface -- never a specific implementation class:
ServiceLoader<PaymentProcessor> loader = ServiceLoader.load(PaymentProcessor.class);

for (PaymentProcessor processor : loader) {
    // one iteration per implementation declared in a META-INF/services/PaymentProcessor
    // file found anywhere on the classpath
    System.out.println(processor.process(49.99));
}
```

Because `META-INF/services` files are packaging-level resources — something a single, standalone `.java` file can't ship alongside itself — the runnable examples below build the plugin directory structure (compiled provider classes plus a real `META-INF/services` file) at runtime, in a temporary directory, to demonstrate genuine `ServiceLoader` discovery end to end.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ServiceLoader scans the classpath for a META-INF/services file named after the interface, reads the implementation class names listed inside it, and instantiates each one without the application ever referencing those class names directly">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="120" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Application code</text>
  <rect x="30" y="90" width="180" height="40" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="120" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ServiceLoader.load(Interface.class)</text>

  <rect x="290" y="60" width="300" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="440" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">META-INF/services/Interface (text file)</text>
  <text x="440" y="45" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lists implementation class names, one per line</text>

  <line x1="210" y1="110" x2="285" y2="80" stroke="#8b949e" marker-end="url(asl1)"/>
  <line x1="210" y1="50" x2="285" y2="70" stroke="#8b949e" marker-end="url(asl1)"/>
  <text x="440" y="130" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Any JAR on the classpath can contribute one of these files, adding a new implementation.</text>
  <defs><marker id="asl1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The application asks for "implementations of this interface"; the classpath, not the application's code, decides which ones exist.

## 5. Runnable example

Scenario: a payment-processing plugin system — the same interface, evolved from hardcoded selection of a single known implementation, through genuine `ServiceLoader`-based discovery of one plugin compiled and registered at runtime, to multiple plugins discovered together and a demonstration of `reload()` picking up a newly-added one.

### Level 1 — Basic

```java
public class PaymentHardcoded {
    interface PaymentProcessor {
        String process(double amount);
    }

    static class CreditCardProcessor implements PaymentProcessor {
        public String process(double amount) { return "Charged $" + amount + " to credit card"; }
    }

    public static void main(String[] args) {
        // The caller must know the EXACT implementation class name at compile time -- no flexibility
        PaymentProcessor processor = new CreditCardProcessor();
        System.out.println(processor.process(49.99));
    }
}
```

**How to run:** `java PaymentHardcoded.java`

This works, but `main` has to hardcode `new CreditCardProcessor()` — adding a new payment method means modifying this exact line and recompiling the application, which is the core problem `ServiceLoader` solves.

### Level 2 — Intermediate

```java
import javax.tools.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class PaymentServiceLoader {

    public interface PaymentProcessor {
        String process(double amount);
    }

    public static void main(String[] args) throws Exception {
        // Set up a plugin directory at runtime: a real compiled provider class + a real
        // META-INF/services file, exactly what a plugin JAR would contain.
        Path pluginDir = Files.createTempDirectory("plugin-demo");

        String providerSource =
            "public class PayPalProcessor implements PaymentServiceLoader.PaymentProcessor {\n" +
            "    public String process(double amount) { return \"Paid $\" + amount + \" via PayPal\"; }\n" +
            "}\n";
        Path providerFile = pluginDir.resolve("PayPalProcessor.java");
        Files.writeString(providerFile, providerSource);

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        // Compile the provider AGAINST the classpath that already has PaymentServiceLoader (for its nested interface)
        String classpath = System.getProperty("java.class.path");
        int result = compiler.run(null, null, null, "-cp", classpath, "-d", pluginDir.toString(), providerFile.toString());
        System.out.println("Provider compiled: " + (result == 0));

        Path servicesDir = pluginDir.resolve("META-INF/services");
        Files.createDirectories(servicesDir);
        Files.writeString(servicesDir.resolve("PaymentServiceLoader$PaymentProcessor"), "PayPalProcessor\n");

        URLClassLoader pluginLoader = new URLClassLoader(new URL[]{pluginDir.toUri().toURL()},
            PaymentServiceLoader.class.getClassLoader());

        ServiceLoader<PaymentProcessor> loader = ServiceLoader.load(PaymentProcessor.class, pluginLoader);
        for (PaymentProcessor processor : loader) {
            System.out.println("Discovered provider: " + processor.getClass().getSimpleName());
            System.out.println(processor.process(25.00));
        }
    }
}
```

**How to run:** `java PaymentServiceLoader.java`

The application's `main` method never mentions `PayPalProcessor` by name anywhere — it only knows about `PaymentProcessor`. The provider class and its registration file (`META-INF/services/PaymentServiceLoader$PaymentProcessor`) are built entirely at runtime here (standing in for what a real plugin JAR would ship pre-built), then `ServiceLoader.load` discovers and instantiates it purely by scanning that file.

### Level 3 — Advanced

```java
import javax.tools.*;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.util.*;

public class PaymentMultipleProviders {

    public interface PaymentProcessor {
        String process(double amount);
    }

    public static void main(String[] args) throws Exception {
        Path pluginDir = Files.createTempDirectory("plugin-demo-multi");

        String paypalSource =
            "public class PayPalProcessor implements PaymentMultipleProviders.PaymentProcessor {\n" +
            "    public String process(double amount) { return \"Paid $\" + amount + \" via PayPal\"; }\n" +
            "}\n";
        String stripeSource =
            "public class StripeProcessor implements PaymentMultipleProviders.PaymentProcessor {\n" +
            "    public String process(double amount) { return \"Charged $\" + amount + \" via Stripe\"; }\n" +
            "}\n";

        Files.writeString(pluginDir.resolve("PayPalProcessor.java"), paypalSource);
        Files.writeString(pluginDir.resolve("StripeProcessor.java"), stripeSource);

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        String classpath = System.getProperty("java.class.path");
        int result = compiler.run(null, null, null, "-cp", classpath, "-d", pluginDir.toString(),
            pluginDir.resolve("PayPalProcessor.java").toString(),
            pluginDir.resolve("StripeProcessor.java").toString());
        System.out.println("Providers compiled: " + (result == 0));

        Path servicesDir = pluginDir.resolve("META-INF/services");
        Files.createDirectories(servicesDir);
        Files.writeString(servicesDir.resolve("PaymentMultipleProviders$PaymentProcessor"),
            "PayPalProcessor\nStripeProcessor\n");

        URLClassLoader pluginLoader = new URLClassLoader(new URL[]{pluginDir.toUri().toURL()},
            PaymentMultipleProviders.class.getClassLoader());

        ServiceLoader<PaymentProcessor> loader = ServiceLoader.load(PaymentProcessor.class, pluginLoader);

        System.out.println("Broadcasting a $10 charge attempt to ALL registered processors:");
        for (PaymentProcessor processor : loader) {
            System.out.println("  " + processor.getClass().getSimpleName() + ": " + processor.process(10.00));
        }

        // Add a THIRD provider after the fact, then reload() to pick it up
        String squareSource =
            "public class SquareProcessor implements PaymentMultipleProviders.PaymentProcessor {\n" +
            "    public String process(double amount) { return \"Charged $\" + amount + \" via Square\"; }\n" +
            "}\n";
        Files.writeString(pluginDir.resolve("SquareProcessor.java"), squareSource);
        compiler.run(null, null, null, "-cp", classpath, "-d", pluginDir.toString(),
            pluginDir.resolve("SquareProcessor.java").toString());
        Files.writeString(servicesDir.resolve("PaymentMultipleProviders$PaymentProcessor"),
            "PayPalProcessor\nStripeProcessor\nSquareProcessor\n");

        loader.reload(); // forget cached providers, re-scan the services configuration
        System.out.println("\nAfter adding SquareProcessor and calling reload():");
        for (PaymentProcessor processor : loader) {
            System.out.println("  " + processor.getClass().getSimpleName() + ": " + processor.process(10.00));
        }
    }
}
```

**How to run:** `java PaymentMultipleProviders.java`

With two providers listed in the `META-INF/services` file, the `for` loop over `loader` visits **both** — a broadcast pattern where the application calls every registered implementation without knowing in advance how many there are. Adding a third provider's `.class` file and appending its name to the services file, then calling `loader.reload()`, makes the *same* `ServiceLoader` instance pick up the new provider — without `reload()`, it would keep using its already-cached list from the first scan.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. Two provider source files (`PayPalProcessor`, `StripeProcessor`) are written to a temporary `pluginDir` and compiled with the system compiler against the current classpath (so they can resolve `PaymentMultipleProviders.PaymentProcessor`, the shared interface). `Providers compiled: true` confirms success.

A `META-INF/services/PaymentMultipleProviders$PaymentProcessor` file is written inside `pluginDir`, listing both class names, one per line — this is the file `ServiceLoader` will scan. `URLClassLoader pluginLoader` is created pointing at `pluginDir`, with the *current* class loader as its parent (so it can still resolve the shared `PaymentProcessor` interface type, defined in the currently-running `PaymentMultipleProviders` class).

`ServiceLoader.load(PaymentProcessor.class, pluginLoader)` creates a loader that will search `pluginLoader`'s classpath (which includes `pluginDir`) for the relevant `META-INF/services` file. The first `for` loop over `loader` triggers the actual scan: it reads the services file, finds two class names, and instantiates each one (`Class.forName(...).getDeclaredConstructor().newInstance()` internally) via `pluginLoader`. Both `PayPalProcessor` and `StripeProcessor` are printed, each processing a `$10.00` charge according to its own logic.

Next, a third provider (`SquareProcessor`) is compiled into the same `pluginDir`, and the `META-INF/services` file is **overwritten** to list all three class names. `loader.reload()` is called — this discards `ServiceLoader`'s internal cache of already-instantiated providers, forcing the *next* iteration to re-scan the (now-updated) services file from scratch. The second `for` loop over the same `loader` object therefore sees all three providers, printing `PayPalProcessor`, `StripeProcessor`, and now also `SquareProcessor`.

Expected output:
```
Providers compiled: true
Broadcasting a $10 charge attempt to ALL registered processors:
  PayPalProcessor: Paid $10.0 via PayPal
  StripeProcessor: Charged $10.0 via Stripe

After adding SquareProcessor and calling reload():
  PayPalProcessor: Paid $10.0 via PayPal
  StripeProcessor: Charged $10.0 via Stripe
  SquareProcessor: Charged $10.0 via Square
```

## 7. Gotchas & takeaways

> A `ServiceLoader` instance **caches** the providers it has already instantiated after the first iteration — simply iterating it again does **not** pick up newly-added providers on the classpath, even if the underlying `META-INF/services` file has changed since. You must explicitly call `reload()` to force a fresh scan, exactly as the Level 3 example demonstrates; forgetting this is a common source of "why isn't my new plugin showing up" confusion.

- `ServiceLoader.load(SomeInterface.class)` discovers implementations by scanning the classpath for `META-INF/services/<fully-qualified-interface-name>` files, each listing implementation class names, one per line.
- The calling application only ever references the interface — never a specific implementation class name — which is what makes this a genuine plugin mechanism rather than hardcoded polymorphism.
- Providers must have a public no-argument constructor, since `ServiceLoader` instantiates them via reflection.
- `reload()` clears the internal cache and forces the next iteration to re-scan the classpath — necessary if providers might be added or removed after the `ServiceLoader` was first created.
- This exact mechanism underlies JDBC 4.0's auto driver loading (covered earlier in this series) — a JDBC driver JAR's `META-INF/services/java.sql.Driver` file is discovered and loaded by `DriverManager` using precisely this API.
