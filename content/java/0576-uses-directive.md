---
card: java
gi: 576
slug: uses-directive
title: uses directive
---

## 1. What it is

The `uses` directive declares that a module **consumes** a service — an interface (or abstract class) whose concrete implementation(s) it doesn't know about at compile time, but wants to discover and use at runtime via `java.util.ServiceLoader`. `uses com.example.spi.PaymentProvider;` says "this module will look up implementations of `PaymentProvider` at runtime, from whatever's available on the module path."

## 2. Why & when

`ServiceLoader`-based service discovery — defining an interface, then letting different modules plug in different implementations, discovered dynamically rather than hard-wired with `new SomeImpl()` — long predates the module system (it's how JDBC drivers, `java.nio.file.spi.FileSystemProvider`, and countless plugin architectures work). Before modules, this relied on a text file in `META-INF/services/` naming implementation classes, read by convention. With modules, that same mechanism gets first-class, compiler-and-runtime-checked support: `uses` tells the module system "this module is a service *consumer*," and the paired `provides ... with ...` directive (covered separately) tells it "this module is a service *provider*." Declaring `uses` is what makes `ServiceLoader.load(SomeInterface.class)` actually able to find providers from other modules — without it, the module system won't wire up cross-module service discovery for that interface, by design, to keep every module's dependencies (even discovery-based ones) explicit and declared.

## 3. Core concept

```java
module app {
    uses com.example.spi.PaymentProvider; // "I will look up implementations of this at runtime"
}
```

```java
package com.myapp;
import com.example.spi.PaymentProvider;
import java.util.ServiceLoader;

for (PaymentProvider provider : ServiceLoader.load(PaymentProvider.class)) {
    System.out.println(provider.process(100));
}
```

`ServiceLoader.load(PaymentProvider.class)` scans the module graph for every module that declared `provides PaymentProvider with SomeImplementation;`, instantiates each, and returns them as an iterable — all without `app`'s code ever naming a concrete implementation class directly.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="uses declares service consumption; ServiceLoader discovers matching providers from other modules at runtime">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="monospace">module app</text>
  <text x="20" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">uses PaymentProvider;</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="50" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">module stripe.impl</text>
  <text x="240" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">provides ... with StripeProvider;</text>

  <rect x="460" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#d2a8ff"/>
  <text x="540" y="50" fill="#d2a8ff" font-size="10" text-anchor="middle" font-family="monospace">module paypal.impl</text>
  <text x="440" y="90" fill="#8b949e" font-size="10" font-family="sans-serif">provides ... with PaypalProvider;</text>

  <text x="20" y="130" fill="#8b949e" font-size="10" font-family="sans-serif">ServiceLoader.load(PaymentProvider.class) finds and instantiates BOTH implementations at runtime —</text>
  <text x="20" y="145" fill="#8b949e" font-size="10" font-family="sans-serif">app's code never names StripeProvider or PaypalProvider directly, and can gain new providers without changes.</text>
</svg>

`app` depends only on the interface; providers plug in independently, discovered at runtime.

## 5. Runnable example

Scenario: a small notification system that discovers `NotificationChannel` implementations at runtime instead of hard-coding which channels exist — starting with a `uses` declaration that finds zero providers (no implementations on the module path yet), then adding one implementation module and seeing it discovered automatically, then adding a second implementation module without touching any consumer code at all.

### Level 1 — Basic

```java
// File: notify.spi/module-info.java
module notify.spi {
    exports com.notify.spi;
}
```

```java
// File: notify.spi/com/notify/spi/NotificationChannel.java
package com.notify.spi;

public interface NotificationChannel {
    String name();
    void send(String message);
}
```

```java
// File: app/module-info.java
module app {
    requires notify.spi;
    uses com.notify.spi.NotificationChannel; // declares intent to discover implementations
}
```

```java
// File: app/com/myapp/Main.java
package com.myapp;
import com.notify.spi.NotificationChannel;
import java.util.ServiceLoader;

public class Main {
    public static void main(String[] args) {
        ServiceLoader<NotificationChannel> loader = ServiceLoader.load(NotificationChannel.class);
        int count = 0;
        for (NotificationChannel channel : loader) {
            channel.send("Hello!");
            count++;
        }
        System.out.println("Channels found: " + count);
    }
}
```

**How to run:** `javac -d out --module-source-path . $(find notify.spi app -name "*.java") && java --module-path out -m app/com.myapp.Main`

Expected output:
```
Channels found: 0
```

`ServiceLoader.load(NotificationChannel.class)` runs successfully — `uses` doesn't require any providers to actually exist, it just enables the *lookup mechanism* — but the loop body never executes, because no module on the module path has declared `provides com.notify.spi.NotificationChannel with ...` yet. This level establishes the baseline: consumption is wired up, but nothing is being provided.

### Level 2 — Intermediate

```java
// File: notify.email/module-info.java
module notify.email {
    requires notify.spi;
    provides com.notify.spi.NotificationChannel with com.notify.email.EmailChannel;
}
```

```java
// File: notify.email/com/notify/email/EmailChannel.java
package com.notify.email;
import com.notify.spi.NotificationChannel;

public class EmailChannel implements NotificationChannel {
    public String name() { return "email"; }
    public void send(String message) {
        System.out.println("[email] " + message);
    }
}
```

```java
// File: app/module-info.java — add requires notify.email so it's on the module graph
module app {
    requires notify.spi;
    requires notify.email;
    uses com.notify.spi.NotificationChannel;
}
```

**How to run:** `javac -d out --module-source-path . $(find notify.spi notify.email app -name "*.java") && java --module-path out -m app/com.myapp.Main`

Expected output:
```
[email] Hello!
Channels found: 1
```

The real-world concern this adds: `notify.email` is a completely separate module that implements the `NotificationChannel` interface and declares itself a provider via `provides ... with ...`. `app`'s `Main.java` source code is **completely unchanged** from Level 1 — the same `ServiceLoader.load(...)` call now finds and instantiates `EmailChannel` automatically, purely because `notify.email` is present on the module path and declares itself as a provider for the interface `app` declared `uses` for.

### Level 3 — Advanced

```java
// File: notify.sms/module-info.java — a SECOND, independent implementation module
module notify.sms {
    requires notify.spi;
    provides com.notify.spi.NotificationChannel with com.notify.sms.SmsChannel;
}
```

```java
// File: notify.sms/com/notify/sms/SmsChannel.java
package com.notify.sms;
import com.notify.spi.NotificationChannel;

public class SmsChannel implements NotificationChannel {
    public String name() { return "sms"; }
    public void send(String message) {
        System.out.println("[sms] " + message);
    }
}
```

```java
// File: app/module-info.java — add requires notify.sms; Main.java remains COMPLETELY unchanged
module app {
    requires notify.spi;
    requires notify.email;
    requires notify.sms;
    uses com.notify.spi.NotificationChannel;
}
```

**How to run:** `javac -d out --module-source-path . $(find notify.spi notify.email notify.sms app -name "*.java") && java --module-path out -m app/com.myapp.Main`

Expected output (provider iteration order follows `ServiceLoader`'s discovery order, typically module-path order, so this is deterministic for a fixed module path but not something application code should rely on):
```
[email] Hello!
[sms] Hello!
Channels found: 2
```

This handles the production-flavoured payoff of the whole pattern: **adding an entirely new implementation required zero changes to `Main.java`**, `app`'s consumer code — only a new provider module (`notify.sms`) and one added `requires notify.sms;` line in `app`'s own `module-info.java` (needed so the provider module is actually present in the runtime module graph at all). The `ServiceLoader.load(...)` loop automatically picks up both channels without any `if`/`else` or explicit instantiation of either implementation class.

## 6. Walkthrough

Execution starts with the compilation and launch commands in Level 3, building four modules together: `notify.spi` (the interface), `notify.email` and `notify.sms` (two independent provider implementations), and `app` (the consumer).

`javac` records, from each `module-info.java`: `app` declares `uses com.notify.spi.NotificationChannel` (consumer intent) and requires all three other modules (so they're part of the runtime module graph); `notify.email` and `notify.sms` each declare `provides com.notify.spi.NotificationChannel with <their own implementation class>` (provider intent).

At runtime, `java --module-path out -m app/com.myapp.Main` launches `Main.main`. `ServiceLoader.load(NotificationChannel.class)` is called — this doesn't eagerly instantiate anything yet; `ServiceLoader` is lazy, only locating and instantiating providers as the returned iterator is actually consumed.

```
ServiceLoader.load(NotificationChannel.class) resolution, given the module graph:

app       -> uses NotificationChannel                          (consumer)
notify.email -> provides NotificationChannel with EmailChannel  (provider #1)
notify.sms   -> provides NotificationChannel with SmsChannel    (provider #2)

-> ServiceLoader finds BOTH providers, since app requires both notify.email and notify.sms,
   making them part of the module graph the ServiceLoader searches.
```

The `for (NotificationChannel channel : loader)` loop begins iterating. On the first iteration, `ServiceLoader` instantiates the first discovered provider — `EmailChannel`, via its no-argument constructor (the standard requirement for a `ServiceLoader`-discovered implementation) — and hands it to the loop body. `channel.send("Hello!")` calls `EmailChannel.send(...)`, which prints `"[email] Hello!"`. `count` becomes `1`.

The second iteration instantiates `SmsChannel` the same way; `channel.send("Hello!")` prints `"[sms] Hello!"`; `count` becomes `2`. No further providers exist, so the loop ends. `main` prints `"Channels found: 2"`.

Crucially, at no point does `Main.java`'s source code mention `EmailChannel` or `SmsChannel` by name — it only ever references the `NotificationChannel` interface and the generic `ServiceLoader.load(...)` call. The concrete implementations are discovered entirely through the module system's own bookkeeping of which modules declared themselves providers for the interface `app` declared itself a consumer of via `uses`.

## 7. Gotchas & takeaways

> `uses` only makes `ServiceLoader.load(...)` **able** to find cross-module providers — it does not, by itself, cause any providers to exist or be loaded onto the module path. If a module declares `uses SomeInterface` but no other module on the module path declares `provides SomeInterface with ...`, `ServiceLoader.load(SomeInterface.class)` simply returns an empty iterable at runtime (as in Level 1) — this is a silent, non-error condition, so consumer code should generally handle the zero-providers case gracefully rather than assuming at least one will always be present.

- A provider implementation discovered via `ServiceLoader` **must** have a public, no-argument constructor — `ServiceLoader` has no way to pass constructor arguments, since it instantiates providers reflectively and generically.
- `requires` for a provider module (like `app requires notify.email;` in Level 2) is necessary specifically so that provider module is part of the runtime module graph at all — omitting it means `ServiceLoader` simply never sees that module's `provides` declaration, even if the provider module happens to be sitting on the module path.
- The order `ServiceLoader` returns providers in is determined by module resolution order, not by any guaranteed alphabetical or declaration order — code that cares about a specific provider "winning" should filter or prioritize explicitly (e.g., by checking `channel.name()`) rather than relying on iteration order.
- This same `uses`/`provides`/`ServiceLoader` mechanism is how the JDK's own pluggable subsystems work internally — JDBC drivers, `java.nio.file.spi.FileSystemProvider`, cryptographic algorithm providers — modules just formalize a pattern that long predates them.
- Before modules, the equivalent mechanism was a `META-INF/services/com.notify.spi.NotificationChannel` text file listing implementation class names by convention — that mechanism still works for unmodularized (classpath or automatic-module) code, and `ServiceLoader` transparently supports both the old file-based and the new module-declared forms simultaneously.
