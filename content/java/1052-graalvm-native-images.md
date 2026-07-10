---
card: java
gi: 1052
slug: graalvm-native-images
title: GraalVM native images
---

## 1. What it is

A GraalVM **native image** compiles a Java application **ahead-of-time** into a standalone, platform-specific executable binary — no JVM, no bytecode interpretation, no just-in-time compilation at runtime. The tradeoff is fundamental: normal Java relies on the JVM analyzing the *running* program to decide what to load and optimize; ahead-of-time compilation must instead figure out, at *build time*, everything the program could possibly need, including every class ever reached via reflection, dynamic proxies, or JNI — anything the native-image build tool can't discover through static analysis needs to be explicitly declared in a configuration file, or it simply won't exist in the compiled binary at all.

## 2. Why & when

A normal JVM application has real startup cost — class loading, bytecode verification, JIT warmup before reaching peak performance — that's irrelevant for a long-running server processing millions of requests over hours, but genuinely painful for a short-lived process (a CLI tool, a serverless function that must respond within a cold-start budget measured in milliseconds). A native image eliminates nearly all of that startup cost: the binary starts running actual optimized machine code immediately, with startup times often measured in milliseconds rather than the JVM's typical hundreds of milliseconds to seconds — at the cost of needing to identify everything the program could possibly use *before* compilation, since there's no running JVM left afterward to load a class it didn't already know about.

Reach for a native image specifically when startup time and memory footprint genuinely matter more than peak throughput — serverless functions, CLI tools, containers that scale up and down frequently (where JVM startup cost is paid repeatedly). Reflection-heavy frameworks and libraries (a lot of "classic" Spring or Hibernate usage, unless using their more recent native-aware variants) require careful reflection-configuration to work correctly under native-image compilation, since the build tool's static analysis can't always discover every class reached only through runtime reflection.

## 3. Core concept

```java
// A class only ever referenced through reflection -- native-image's static
// analysis has no way to discover this unless explicitly configured.
class PluginLoader {
    static Object loadPlugin(String className) throws Exception {
        Class<?> clazz = Class.forName(className); // the string is only known at RUNTIME
        return clazz.getDeclaredConstructor().newInstance();
    }
}
```

```json
// META-INF/native-image/reflect-config.json -- tells native-image ahead of
// time "this class, reachable only via reflection, must be included."
[
  {
    "name": "com.example.MyPlugin",
    "allDeclaredConstructors": true,
    "allPublicMethods": true
  }
]
```

```
# Building a native image (requires GraalVM's native-image tool installed)
$ native-image -jar myapp.jar myapp-native
$ ./myapp-native
Started in 8ms   <- versus typically hundreds of ms for a normal `java -jar`
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Normal JVM startup involving class loading, bytecode verification, and JIT warmup before reaching peak speed, versus a native image starting directly as compiled machine code with near-instant startup">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Normal JVM</text>
  <rect x="30" y="40" width="90" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="75" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">class load</text>
  <rect x="130" y="40" width="90" height="30" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="175" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">interpret</text>
  <rect x="230" y="40" width="90" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="275" y="60" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">JIT-compiled</text>

  <text x="480" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Native image</text>
  <rect x="420" y="40" width="180" height="30" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">running machine code immediately</text>

  <text x="180" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">hundreds of ms before peak speed</text>
  <text x="510" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">milliseconds to start, running at full speed</text>
</svg>

A native image skips the JVM's warmup path entirely, starting directly as already-compiled machine code.

## 5. Runnable example

Scenario: a small CLI tool, evolving from a normal JVM application into a GraalVM native image, demonstrating both the startup-time benefit and the reflection-configuration requirement.

### Level 1 — Basic

```java
// File: GreeterApp.java
public class GreeterApp {
    public static void main(String[] args) {
        String name = args.length > 0 ? args[0] : "World";
        System.out.println("Hello, " + name + "!");
    }
}
```

**How to run:** save as `GreeterApp.java`, then `javac GreeterApp.java && java GreeterApp Ana` (JDK 17+).

Expected output:
```
Hello, Ana!
```

This runs correctly as a normal JVM application — but every invocation pays JVM startup cost (class loading, initial interpretation before any JIT compilation) even for a program this trivially small, which matters little here but compounds significantly for a CLI tool invoked very frequently, or a serverless function billed partly by cold-start duration.

### Level 2 — Intermediate

```
# Building GreeterApp as a native image (requires GraalVM installed, with the
# native-image tool available -- `gu install native-image` on some distributions).
$ javac GreeterApp.java
$ native-image GreeterApp
$ ./greeterapp Ana
```

**How to run:** with GraalVM's `native-image` tool installed, compile `GreeterApp.java` normally with `javac`, then run `native-image GreeterApp` to produce a standalone executable (typically named `greeterapp` or matching the class name), then run `./greeterapp Ana` directly.

Expected output:
```
Hello, Ana!
```

The real-world concern added: `./greeterapp` is a standalone native executable — no `java` command, no JVM startup, no `-cp` classpath needed at all. Running `time ./greeterapp Ana` versus `time java GreeterApp Ana` on the same machine shows the native image starting dramatically faster, since it begins executing already-compiled machine code immediately rather than loading classes and interpreting bytecode first.

### Level 3 — Advanced

```java
// File: PluginApp.java -- uses reflection to load a class by name, a pattern
// native-image's static analysis CANNOT discover on its own.
public class PluginApp {
    public static void main(String[] args) throws Exception {
        String className = args.length > 0 ? args[0] : "Greeter";
        Class<?> clazz = Class.forName(className); // only known at RUNTIME
        Object instance = clazz.getDeclaredConstructor().newInstance();
        System.out.println(instance);
    }
}

class Greeter {
    @Override public String toString() { return "Hello from a reflectively-loaded Greeter!"; }
}
```

```json
// File: META-INF/native-image/reflect-config.json -- WITHOUT this file, building
// PluginApp as a native image would compile successfully but FAIL at runtime
// with a ClassNotFoundException, since native-image's static analysis has no
// way to know Class.forName("Greeter") will ever be called with that string.
[
  {
    "name": "Greeter",
    "allDeclaredConstructors": true
  }
]
```

**How to run:** with GraalVM's `native-image` tool installed, compile with `javac PluginApp.java`, place `reflect-config.json` at `META-INF/native-image/reflect-config.json` relative to the compiled classes, then build with `native-image -H:ConfigurationFileDirectories=META-INF/native-image PluginApp`, then run `./pluginapp Greeter`.

Expected output:
```
Hello from a reflectively-loaded Greeter!
```

If `reflect-config.json` were omitted entirely, this exact same source code would still compile into a native image successfully (native-image can't know in advance that `Greeter` needs to be reachable), but running `./pluginapp Greeter` would fail at runtime with `java.lang.ClassNotFoundException: Greeter` — the class simply wouldn't exist in the compiled binary at all, since nothing in the program's static structure (as opposed to its runtime string argument) ever names `Greeter` directly.

The production-flavored hard case: `Class.forName(className)` receives its target class name as a runtime string (a command-line argument here; in real applications, often a configuration value or a plugin identifier read from a file) — native-image's build-time static analysis fundamentally cannot know what string will be passed at runtime, so `reflect-config.json` is the mechanism that explicitly tells the build "include `Greeter` and its constructor in the compiled binary, even though nothing in the code's static structure directly names it."

## 6. Walkthrough

Tracing why `reflect-config.json` is necessary, by comparing what native-image's static analysis can and can't determine:

1. During the native-image build process, the tool performs a "closed-world" static analysis: starting from `PluginApp.main`, it traces every method call, field access, and class reference it can find *directly in the code* — `System.out.println`, `Class.forName`, `getDeclaredConstructor`, `newInstance` are all found this way, since they're explicit method calls in the source.
2. But `Class.forName(className)` takes a `String` variable, `className`, whose actual value (`"Greeter"`, or whatever the user passes as a command-line argument) is not known until the program actually runs — the build-time analysis has no way to evaluate what string will end up in that variable at runtime, since it depends on `args[0]`, an input only available when the program executes.
3. Without any additional configuration, native-image's analysis therefore has no reason to include `Greeter`'s class metadata, its constructor, or any reflective-invocation support for it in the compiled binary at all — from the analysis's perspective, `Greeter` is simply never referenced anywhere in the program's actual, traceable structure.
4. `reflect-config.json` closes this gap explicitly: it tells the native-image build tool, as a separate, manually-provided piece of information, "the class named `Greeter` (referenced only by string, only at runtime) needs its declared constructors preserved and reachable in the final binary" — effectively supplying the information the static analysis structurally cannot derive on its own.
5. With this configuration present during the build, native-image includes `Greeter`'s class metadata and constructor in the compiled executable, even though no line of code anywhere in `PluginApp.java` mentions `Greeter` by name directly.
6. At runtime, `./pluginapp Greeter` executes: `Class.forName("Greeter")` now succeeds (because the class genuinely exists in this binary, thanks to the configuration), `getDeclaredConstructor().newInstance()` constructs a `Greeter` instance, and `System.out.println(instance)` calls its `toString()` override, printing `"Hello from a reflectively-loaded Greeter!"` — demonstrating that the reflection-config mechanism successfully bridged the gap between what the static analysis could see and what the program actually needs at runtime.

## 7. Gotchas & takeaways

> **Gotcha:** a class that works perfectly under a normal JVM but is only reachable via reflection, dynamic proxies, JNI, or resource loading (`getResourceAsStream`) can silently fail — or simply not be found — under native-image compilation, with the build itself completing *successfully* and the failure only surfacing later, at runtime, exactly at the point that reflective call executes. GraalVM provides a tracing agent (`java -agentlib:native-image-agent=config-output-dir=...`) that can run your application under a normal JVM first, observing its actual reflective usage, and auto-generate the needed configuration files — a common and much less error-prone way to bootstrap this configuration than writing it by hand.

- A GraalVM native image compiles Java ahead-of-time into a standalone executable with no JVM, dramatically reducing startup time and memory footprint at the cost of needing complete, build-time knowledge of everything the program could reach.
- Reflection, dynamic proxies, JNI, and dynamic resource loading are the primary categories of "dynamic" behavior native-image's static analysis cannot discover on its own — each requires explicit configuration (`reflect-config.json` and similar files) to work correctly.
- The tracing agent (`-agentlib:native-image-agent`) runs your application normally under a JVM, observes its actual runtime reflective usage, and generates the configuration files automatically — far more reliable than manually guessing what needs to be declared.
- Native images suit short-lived or frequently-restarted processes (CLI tools, serverless functions, rapidly-scaling containers) where startup time and memory footprint genuinely matter more than raw peak throughput.
- Long-running server applications that stay up for hours or days often benefit more from the JVM's ability to progressively optimize based on actual runtime behavior (adaptive JIT compilation) than from a native image's fast-but-fixed ahead-of-time compilation.
- Modern frameworks increasingly ship native-image-aware variants (Spring Boot's native support via Spring AOT processing, for instance) that generate the necessary reflection configuration automatically as part of the framework's own build tooling, reducing the manual configuration burden significantly compared to hand-writing it for every reflectively-used class.
