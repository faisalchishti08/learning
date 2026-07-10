---
card: java
gi: 988
slug: serviceloader-spi
title: ServiceLoader & SPI
---

## 1. What it is

The Service Provider Interface (SPI) pattern separates an API (an interface your code depends on) from its implementations (concrete classes providing that behavior), letting new implementations be added — even by entirely separate JARs, compiled independently, with no shared code beyond the interface itself — without any change to the code that consumes the interface. `java.util.ServiceLoader` is the JDK's built-in mechanism for discovering these implementations at runtime: a provider JAR declares which implementation(s) it offers by listing their fully-qualified class names in a plain text file at `META-INF/services/<fully-qualified-interface-name>`, and `ServiceLoader.load(SomeInterface.class)` scans the classpath (or, for a module-based application, the module graph) for all such declarations, returning an iterable of instances — one per discovered implementation — without the calling code ever needing to know, in advance, how many implementations exist or what their class names are.

## 2. Why & when

This mechanism is exactly what lets the JDK itself remain pluggable in places where genuinely different, independently-developed implementations of a standard interface need to coexist: `java.sql.Driver` implementations (different JDBC database drivers, each shipped as a separate JAR, all discoverable via the exact same `ServiceLoader` mechanism without the JDBC API itself needing to know about any specific database vendor), different `java.nio.file.spi.FileSystemProvider` implementations, and — a very common modern use — different logging backend implementations behind a common logging facade (SLF4J's binding mechanism works on a closely related principle). You reach for `ServiceLoader` and the SPI pattern specifically when you're building a library or framework that needs to support genuinely pluggable, independently-developed extensions — a plugin architecture, a multi-backend abstraction (different storage backends, different notification channels), or any scenario where you want new implementations addable purely by adding a new JAR to the classpath, with zero changes to the consuming application's own code required.

## 3. Core concept

```
// The API (an interface), defined once, shared by everyone:
public interface PaymentProcessor {
    String process(double amount);
}

// Provider JAR #1 declares its implementation via a text file at:
// META-INF/services/PaymentProcessor
//   containing exactly ONE line: com.example.StripeProcessor

// Provider JAR #2 (a totally SEPARATE, independently-compiled JAR) declares its own:
// META-INF/services/PaymentProcessor
//   containing: com.example.PayPalProcessor

// Consuming code -- knows NOTHING about StripeProcessor or PayPalProcessor by name:
ServiceLoader<PaymentProcessor> loader = ServiceLoader.load(PaymentProcessor.class);
for (PaymentProcessor processor : loader) {
    System.out.println(processor.process(99.99));
}
// -> discovers and instantiates BOTH implementations, purely from whatever
//    provider JARs happen to be present on the classpath at runtime
```

Neither the consuming code nor the `PaymentProcessor` interface itself ever references `StripeProcessor` or `PayPalProcessor` by name — `ServiceLoader` discovers them purely by scanning `META-INF/services` files across whatever JARs happen to be present, meaning adding or removing a payment provider is purely a matter of adding or removing that provider's JAR from the classpath.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two independently-compiled provider JARs each declaring their PaymentProcessor implementation via a META-INF/services file, discovered together by ServiceLoader without the consuming code knowing either implementation's name in advance" >
  <rect x="20" y="20" width="180" height="50" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="40" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Provider JAR 1</text>
  <text x="110" y="58" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">META-INF/services/... -&gt; StripeProcessor</text>

  <rect x="20" y="90" width="180" height="50" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="110" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Provider JAR 2</text>
  <text x="110" y="128" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">META-INF/services/... -&gt; PayPalProcessor</text>

  <rect x="280" y="55" width="140" height="50" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="75" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">ServiceLoader</text>
  <text x="350" y="93" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">scans classpath, discovers BOTH</text>

  <rect x="480" y="55" width="140" height="50" fill="#1c2430" stroke="#f0883e"/>
  <text x="550" y="75" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">Consuming code</text>
  <text x="550" y="93" fill="#f0883e" font-size="8" text-anchor="middle" font-family="sans-serif">never names either class</text>

  <line x1="200" y1="45" x2="280" y2="70" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="200" y1="115" x2="280" y2="90" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="420" y1="80" x2="480" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*Each provider JAR independently declares its implementation; ServiceLoader discovers all of them together without the consuming code ever naming a specific implementation.*

## 5. Runnable example

Scenario: build a small pluggable notification system using the SPI pattern, evolving from a basic single-implementation setup, to a realistic multi-implementation scenario processing through every discovered provider, to a more advanced case demonstrating adding a brand-new provider without touching any existing code at all.

### Level 1 — Basic

```java
// File: NotificationSender.java
public interface NotificationSender {
    void send(String message);
}
```

```java
// File: EmailSender.java
public class EmailSender implements NotificationSender {
    public void send(String message) {
        System.out.println("[Email] " + message);
    }
}
```

```
File: META-INF/services/NotificationSender
(a plain text file containing exactly one line:)
EmailSender
```

```java
// File: SpiBasic.java
import java.util.ServiceLoader;

public class SpiBasic {
    public static void main(String[] args) {
        ServiceLoader<NotificationSender> loader = ServiceLoader.load(NotificationSender.class);
        for (NotificationSender sender : loader) {
            sender.send("Order shipped!");
        }
    }
}
```

**How to run:** place the files in this layout: `NotificationSender.java`, `EmailSender.java`, `SpiBasic.java` in the current directory, and `META-INF/services/NotificationSender` as shown above; then `javac *.java && java -cp . SpiBasic` (JDK 17+).

Expected output:
```
[Email] Order shipped!
```

`SpiBasic.java` never mentions `EmailSender` by name anywhere in its own source code — `ServiceLoader.load(NotificationSender.class)` discovers `EmailSender` purely by reading the `META-INF/services/NotificationSender` file, which declares it as an implementation of that interface, and instantiates it automatically.

### Level 2 — Intermediate

```java
// File: SmsSender.java
public class SmsSender implements NotificationSender {
    public void send(String message) {
        System.out.println("[SMS] " + message);
    }
}
```

```
File: META-INF/services/NotificationSender
(now updated to list BOTH implementations, one per line:)
EmailSender
SmsSender
```

```java
// File: SpiMultiple.java
import java.util.ServiceLoader;

public class SpiMultiple {
    public static void main(String[] args) {
        ServiceLoader<NotificationSender> loader = ServiceLoader.load(NotificationSender.class);
        int count = 0;
        for (NotificationSender sender : loader) {
            sender.send("Payment received!");
            count++;
        }
        System.out.println("total providers discovered: " + count);
    }
}
```

**How to run:** add `SmsSender.java`, update `META-INF/services/NotificationSender` to list both classes, then `javac *.java && java -cp . SpiMultiple` (JDK 17+).

Expected output:
```
[Email] Payment received!
[SMS] Payment received!
total providers discovered: 2
```

The real-world concern added: adding `SmsSender` as a second implementation and listing it in the same `META-INF/services` file lets `SpiMultiple` discover and use *both* providers automatically, iterating over each one in turn — the consuming code (`SpiMultiple.java`) required zero changes at all to accommodate the new provider; only the service-declaration file and the new implementation class needed to be added.

### Level 3 — Advanced

```java
// File: PushNotificationSender.java
// A THIRD provider, added entirely SEPARATELY -- demonstrating that no existing
// file (SpiMultiple.java, EmailSender.java, SmsSender.java) needs to change at all
// to add this new capability; only this new class and an updated service file.
public class PushNotificationSender implements NotificationSender {
    public void send(String message) {
        System.out.println("[Push] " + message);
    }
}
```

```
File: META-INF/services/NotificationSender
(updated once more, now listing all THREE implementations:)
EmailSender
SmsSender
PushNotificationSender
```

```java
// File: SpiExtensible.java
import java.util.ServiceLoader;

public class SpiExtensible {
    public static void main(String[] args) {
        ServiceLoader<NotificationSender> loader = ServiceLoader.load(NotificationSender.class);

        // Using ServiceLoader.Provider (Java 9+) to inspect each provider's
        // actual TYPE before instantiating it, e.g. for logging or filtering.
        for (ServiceLoader.Provider<NotificationSender> provider : loader.stream().toList()) {
            System.out.println("discovered provider type: " + provider.type().getSimpleName());
            NotificationSender sender = provider.get(); // instantiate lazily, only when actually needed
            sender.send("System maintenance scheduled.");
        }
    }
}
```

**How to run:** add `PushNotificationSender.java`, update the service file to list all three classes, then `javac *.java && java -cp . SpiExtensible` (JDK 17+).

Expected output:
```
discovered provider type: EmailSender
[Email] System maintenance scheduled.
discovered provider type: SmsSender
[SMS] System maintenance scheduled.
discovered provider type: PushNotificationSender
[Push] System maintenance scheduled.
```

The production-flavored hard case: `loader.stream()` (Java 9+) returns a stream of `ServiceLoader.Provider` objects, letting you inspect each provider's declared *type* (`provider.type()`) before deciding whether to actually instantiate it (`provider.get()`) — useful for scenarios where instantiating every single discovered provider eagerly would be wasteful or where you want to log or filter providers before committing to using them; critically, adding `PushNotificationSender` as a third provider required touching *only* its own new file and the service-declaration file, with `SpiExtensible.java` itself completely unchanged from a version that only knew about two providers, demonstrating the core promise of the SPI pattern: consuming code is written once and needs no modification as new, independently-developed providers are added over time.

## 6. Walkthrough

Tracing `ServiceLoader.load(NotificationSender.class)` and its subsequent iteration end to end in `SpiExtensible.main`:

1. `ServiceLoader.load(NotificationSender.class)` does not immediately scan anything — it returns a lazy `ServiceLoader` instance that will perform its classpath/module scan only when actually iterated or streamed, deferring the (potentially nontrivial) discovery work until it's genuinely needed.
2. `loader.stream()` triggers the actual discovery process: `ServiceLoader` scans every JAR and directory on the classpath (or every readable module, in a modular application) looking for files at the path `META-INF/services/NotificationSender` — in this example, all the relevant classes and the service-declaration file live together in one location, so this scan finds the single service file listing all three provider class names, one per line.
3. For each declared class name found (`EmailSender`, `SmsSender`, `PushNotificationSender`, in the order they appear in the file), `ServiceLoader` creates a `ServiceLoader.Provider` object wrapping that class — critically, at this point, the actual provider *instance* has not necessarily been created yet; only its type information is available.
4. The `for` loop iterates over these three `Provider` objects in turn; for the first one, `provider.type().getSimpleName()` returns `"EmailSender"` without needing to construct an actual `EmailSender` instance at all — this is printed first.
5. `provider.get()` then actually instantiates `EmailSender` (calling its no-argument constructor, which every SPI provider implementation must have), returning a genuine `NotificationSender` instance, on which `send("System maintenance scheduled.")` is called, printing `"[Email] System maintenance scheduled."`.
6. This exact process — print the type, lazily instantiate via `get()`, call `send` — repeats for `SmsSender` and then `PushNotificationSender`, in the same order they appeared in the service-declaration file, producing the three pairs of "discovered provider type" and actual-send output lines shown above; the entire sequence was driven purely by what the `META-INF/services/NotificationSender` file listed, with `SpiExtensible.java`'s own source code never once referencing any of the three concrete class names directly.

## 7. Gotchas & takeaways

> **Gotcha:** every class listed in a `META-INF/services` file must have a public, no-argument constructor — `ServiceLoader` has no way to supply constructor arguments during its automatic discovery-and-instantiation process, so a provider class requiring configuration at construction time typically needs to either read that configuration from a well-known location itself (a system property, a configuration file) inside its own no-arg constructor, or expose a separate initialization method the consuming code calls after obtaining the instance from `ServiceLoader`.

- The SPI pattern separates an API (an interface) from its implementations, letting new implementations be added via entirely separate, independently-compiled JARs, with no change to the code consuming the interface.
- `META-INF/services/<fully-qualified-interface-name>` is a plain text file, one implementation class name per line, that a provider JAR uses to declare which implementation(s) it offers.
- `ServiceLoader.load(SomeInterface.class)` scans the classpath (or module graph) for these declaration files and discovers every declared implementation, without the consuming code ever needing to reference a specific implementation class by name.
- This mechanism underlies JDBC driver discovery, pluggable file system providers, and various logging-facade binding mechanisms within the JDK itself, and is the standard, idiomatic way to build a plugin architecture in Java.
- `ServiceLoader.Provider` (Java 9+) and `loader.stream()` let you inspect a discovered provider's type before committing to instantiate it, useful for logging, filtering, or lazy instantiation.
- Every SPI provider implementation must have a public no-argument constructor, since `ServiceLoader` has no mechanism for supplying constructor arguments during automatic discovery.
- See [dynamic proxies (java.lang.reflect.Proxy)](0985-dynamic-proxies-java-lang-reflect-proxy.md) and [annotation processing (APT)](0986-annotation-processing-apt.md) for other mechanisms frameworks commonly combine with SPI-based plugin discovery.
